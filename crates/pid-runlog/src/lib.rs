#![doc = include_str!("../README.md")]

use anyhow::{Context, Result};
use serde::ser::{
    SerializeMap, SerializeSeq, SerializeStruct, SerializeStructVariant, SerializeTuple,
    SerializeTupleStruct, SerializeTupleVariant,
};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsStr;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, BufWriter, ErrorKind, Read, Write};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

/// Current event schema. Schema 1 remains readable through the bounded compatibility path.
pub const RUN_LOG_SCHEMA_VERSION: u32 = 2;
/// Oldest event schema accepted by the 0.9 review reader proposed for 1.0.
pub const MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION: u32 = 1;
/// Current JSON sidecar/manifest schema.
pub const RUN_LOG_SIDECAR_SCHEMA_VERSION: u32 = 2;

/// Resource limits applied before or during JSONL parsing.
///
/// The defaults are deliberately finite. Applications processing larger trusted logs can provide
/// an explicit larger value to the `*_with_limits` APIs; no path API silently disables limits.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunLogLimits {
    /// Maximum bytes in the complete JSONL file.
    pub max_file_bytes: u64,
    /// Maximum encoded bytes in one JSON line, excluding its newline.
    pub max_line_bytes: usize,
    /// Maximum number of non-empty event lines.
    pub max_events: usize,
    /// Maximum encoded bytes between the quotes of any JSON string, including object keys.
    pub max_string_bytes: usize,
    /// Maximum elements in any JSON array.
    pub max_array_len: usize,
    /// Maximum entries in any JSON object.
    pub max_object_entries: usize,
    /// Maximum combined object/array nesting depth.
    pub max_nesting_depth: usize,
}

impl Default for RunLogLimits {
    fn default() -> Self {
        Self {
            max_file_bytes: 256 * 1024 * 1024,
            max_line_bytes: 4 * 1024 * 1024,
            max_events: 1_000_000,
            max_string_bytes: 1024 * 1024,
            max_array_len: 1_000_000,
            max_object_entries: 100_000,
            max_nesting_depth: 64,
        }
    }
}

impl RunLogLimits {
    pub const fn with_max_file_bytes(mut self, value: u64) -> Self {
        self.max_file_bytes = value;
        self
    }

    pub const fn with_max_line_bytes(mut self, value: usize) -> Self {
        self.max_line_bytes = value;
        self
    }

    pub const fn with_max_events(mut self, value: usize) -> Self {
        self.max_events = value;
        self
    }

    pub const fn with_max_string_bytes(mut self, value: usize) -> Self {
        self.max_string_bytes = value;
        self
    }

    pub const fn with_max_array_len(mut self, value: usize) -> Self {
        self.max_array_len = value;
        self
    }

    pub const fn with_max_object_entries(mut self, value: usize) -> Self {
        self.max_object_entries = value;
        self
    }

    pub const fn with_max_nesting_depth(mut self, value: usize) -> Self {
        self.max_nesting_depth = value;
        self
    }

    fn validate(self) -> Result<Self> {
        if self.max_file_bytes == 0
            || self.max_line_bytes == 0
            || self.max_events == 0
            || self.max_string_bytes == 0
            || self.max_array_len == 0
            || self.max_object_entries == 0
            || self.max_nesting_depth == 0
        {
            return Err(anyhow::Error::new(RunLogError::InvalidLimits));
        }
        Ok(self)
    }
}

/// Compatibility name for callers that use a general resource-budget vocabulary.
pub type ResourceBudget = RunLogLimits;

/// Structured failures produced by the bounded reader and durable writer.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub enum RunLogError {
    ResourceLimitExceeded {
        operation: &'static str,
        requested: u128,
        limit: u128,
    },
    InvalidLimits,
    ValidationFailed {
        errors: usize,
    },
    ManifestSourceMismatch,
    SourceChangedDuringInspection,
}

impl std::fmt::Display for RunLogError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ResourceLimitExceeded {
                operation,
                requested,
                limit,
            } => write!(
                formatter,
                "{operation}: resource limit exceeded (requested {requested}, limit {limit})"
            ),
            Self::InvalidLimits => formatter.write_str("run-log limits must all be positive"),
            Self::ValidationFailed { errors } => {
                write!(
                    formatter,
                    "run-log validation failed with {errors} error(s)"
                )
            }
            Self::ManifestSourceMismatch => formatter.write_str(
                "supplied events do not match the run-log file used to construct the manifest",
            ),
            Self::SourceChangedDuringInspection => {
                formatter.write_str("run-log source changed during inspection")
            }
        }
    }
}

impl std::error::Error for RunLogError {}

trait ResourceValue {
    fn to_u128(self) -> u128;
}

impl ResourceValue for usize {
    fn to_u128(self) -> u128 {
        self as u128
    }
}

impl ResourceValue for u64 {
    fn to_u128(self) -> u128 {
        u128::from(self)
    }
}

impl ResourceValue for u128 {
    fn to_u128(self) -> u128 {
        self
    }
}

fn resource_limit(
    operation: &'static str,
    requested: impl ResourceValue,
    limit: impl ResourceValue,
) -> anyhow::Error {
    anyhow::Error::new(RunLogError::ResourceLimitExceeded {
        operation,
        requested: requested.to_u128(),
        limit: limit.to_u128(),
    })
}

pub const RUN_LOG_EVENT_TYPES: &[&str] = &[
    "run_started",
    "run_ended",
    "config_logged",
    "frame_observed",
    "embedding_captured",
    "embedding_contract",
    "sim_snapshot",
    "bridge_request",
    "bridge_response",
    "action_applied",
    "object_pose",
    "flow_gt",
    "flow_pred",
    "pid_metric",
    "pid_estimate",
    "geometry_metric",
    "evaluation_metric",
    "label_observed",
    "intervention_applied",
    "artifact_logged",
    "attribution_logged",
    "error_logged",
];

pub const RUN_LOG_SIDECARS: &[&str] = &["validation", "summary", "manifest"];

pub const RUN_LOG_VALIDATION_RULES: &[&str] = &[
    "run log is nonempty",
    "exactly one run_started event",
    "exactly one run_ended event",
    "run_started is first event",
    "run_ended is last event",
    "schema_version is within the supported range; legacy schemas emit a warning",
    "timestamps are nondecreasing",
    "steps are nondecreasing",
    "run_id is nonempty and consistent",
    "schema 2 has exactly one config_logged event before operational events",
    "config_hash values match canonical config JSON and run_started",
    "payload_hash values match canonical payload JSON",
    "bridge request_id values are nonempty and unique",
    "bridge responses refer to existing requests",
    "poses, velocities, flows, and metrics are finite",
    "artifact, embedding, contract, metric, label, and flow source names are nonempty",
    "schema-2 hashes use valid SHA-256 text and the declared lossless canonical generation",
    "artifact URI/path fields are syntactically safe and contain no literal or encoded parent traversal",
    "typed PID estimates carry valid estimator, support, split, hash, diagnostic, and warning provenance",
    "embedding contract variables have nonempty variable/source names and positive dims",
    "label values are non-null",
];

/// Deserialize a JSON number as `f64`, including serde_json's lossless-number representation.
///
/// With serde_json's `arbitrary_precision` feature, an internally tagged enum temporarily
/// buffers numbers through a private map representation. The ordinary `f64` deserializer cannot
/// consume that buffer, so event fields use this adapter while arbitrary-precision numbers inside
/// generic JSON payloads remain lossless.
#[derive(Clone, Copy)]
struct JsonF64(f64);

impl<'de> Deserialize<'de> for JsonF64 {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        struct JsonF64Visitor;

        impl<'de> serde::de::Visitor<'de> for JsonF64Visitor {
            type Value = JsonF64;

            fn expecting(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                formatter.write_str("a finite JSON number representable as f64")
            }

            fn visit_i64<E>(self, value: i64) -> std::result::Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                exact_signed_json_f64(i128::from(value))
                    .map(JsonF64)
                    .map_err(E::custom)
            }

            fn visit_i128<E>(self, value: i128) -> std::result::Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                exact_signed_json_f64(value).map(JsonF64).map_err(E::custom)
            }

            fn visit_u64<E>(self, value: u64) -> std::result::Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                exact_unsigned_json_f64(u128::from(value))
                    .map(JsonF64)
                    .map_err(E::custom)
            }

            fn visit_u128<E>(self, value: u128) -> std::result::Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                exact_unsigned_json_f64(value)
                    .map(JsonF64)
                    .map_err(E::custom)
            }

            fn visit_f64<E>(self, value: f64) -> std::result::Result<Self::Value, E>
            where
                E: serde::de::Error,
            {
                if value.is_finite() {
                    Ok(JsonF64(value))
                } else {
                    Err(E::custom("JSON number is not a finite f64"))
                }
            }

            fn visit_map<A>(self, map: A) -> std::result::Result<Self::Value, A::Error>
            where
                A: serde::de::MapAccess<'de>,
            {
                let number = serde_json::Number::deserialize(
                    serde::de::value::MapAccessDeserializer::new(map),
                )?;
                let raw = number.as_str();
                if !raw.bytes().any(|byte| matches!(byte, b'.' | b'e' | b'E')) {
                    if let Ok(value) = raw.parse::<i128>() {
                        return exact_signed_json_f64(value)
                            .map(JsonF64)
                            .map_err(serde::de::Error::custom);
                    }
                    if let Ok(value) = raw.parse::<u128>() {
                        return exact_unsigned_json_f64(value)
                            .map(JsonF64)
                            .map_err(serde::de::Error::custom);
                    }
                    return Err(serde::de::Error::custom(
                        "integer JSON number is outside the supported i128/u128 range",
                    ));
                }
                let value = number
                    .as_f64()
                    .filter(|value| value.is_finite())
                    .ok_or_else(|| {
                        serde::de::Error::custom("JSON number is not representable as a finite f64")
                    })?;
                Ok(JsonF64(value))
            }
        }

        deserializer.deserialize_any(JsonF64Visitor)
    }
}

fn integer_magnitude_is_exact_f64(value: u128) -> bool {
    if value == 0 {
        return true;
    }
    let significant_bits = u128::BITS - value.leading_zeros();
    significant_bits <= f64::MANTISSA_DIGITS
        || value.trailing_zeros() >= significant_bits - f64::MANTISSA_DIGITS
}

fn exact_signed_json_f64(value: i128) -> std::result::Result<f64, &'static str> {
    if integer_magnitude_is_exact_f64(value.unsigned_abs()) {
        Ok(value as f64)
    } else {
        Err("integer JSON number cannot be represented exactly as f64")
    }
}

fn exact_unsigned_json_f64(value: u128) -> std::result::Result<f64, &'static str> {
    if integer_magnitude_is_exact_f64(value) {
        Ok(value as f64)
    } else {
        Err("integer JSON number cannot be represented exactly as f64")
    }
}

fn deserialize_json_f64<'de, D>(deserializer: D) -> std::result::Result<f64, D::Error>
where
    D: serde::Deserializer<'de>,
{
    Ok(JsonF64::deserialize(deserializer)?.0)
}

fn deserialize_json_f64_array<'de, D, const N: usize>(
    deserializer: D,
) -> std::result::Result<[f64; N], D::Error>
where
    D: serde::Deserializer<'de>,
{
    let values = Vec::<JsonF64>::deserialize(deserializer)?;
    if values.len() != N {
        return Err(serde::de::Error::custom(format!(
            "expected an array of length {N}, got {}",
            values.len()
        )));
    }
    let values: [JsonF64; N] = values
        .try_into()
        .map_err(|_| serde::de::Error::custom("validated array length changed"))?;
    Ok(values.map(|value| value.0))
}

#[derive(Deserialize)]
struct JsonVec3(#[serde(deserialize_with = "deserialize_json_f64_array")] [f64; 3]);

fn deserialize_json_vec3s<'de, D>(deserializer: D) -> std::result::Result<Vec<[f64; 3]>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    Ok(Vec::<JsonVec3>::deserialize(deserializer)?
        .into_iter()
        .map(|value| value.0)
        .collect())
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ActorType {
    HumanGui,
    Script,
    LlmTool,
    System,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Actor {
    pub actor_type: ActorType,
    pub actor_id: String,
    pub session_id: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum RunStatus {
    Succeeded,
    Failed,
    Aborted,
}

/// Hash function used for a content identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum HashAlgorithm {
    Sha256,
}

/// Exact byte/canonicalization contract used before hashing.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum HashRevision {
    CanonicalJsonV1,
    CanonicalJsonV2,
    ReplayTraceV1,
    ReplayTraceV2,
    LogicalTraceV1,
    LogicalTraceV2,
    LogicalTraceV3,
    FileBytesV1,
}

/// A digest which cannot be detached from its algorithm and byte-contract revision.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HashIdentity {
    pub algorithm: HashAlgorithm,
    pub revision: HashRevision,
    pub digest: String,
}

impl HashIdentity {
    /// Construct a validated SHA-256 identity.
    pub fn sha256(revision: HashRevision, digest: impl Into<String>) -> Result<Self> {
        let digest = digest.into();
        if !is_sha256_hex(&digest) {
            anyhow::bail!("invalid SHA-256 digest: expected exactly 64 hexadecimal characters");
        }
        Ok(Self {
            algorithm: HashAlgorithm::Sha256,
            revision,
            digest: digest.to_ascii_lowercase(),
        })
    }

    pub fn validate(&self) -> Result<()> {
        if self.algorithm != HashAlgorithm::Sha256 || !is_sha256_hex(&self.digest) {
            anyhow::bail!("invalid SHA-256 hash identity");
        }
        Ok(())
    }
}

/// Explicit identities for every supported whole-trace digest generation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RunLogHashIdentities {
    pub replay_lossless: HashIdentity,
    pub logical_lossless: HashIdentity,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub replay_legacy: Option<HashIdentity>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub logical_legacy: Option<HashIdentity>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub logical_top_level_clock_legacy: Option<HashIdentity>,
}

/// Scientific maturity carried by a typed PID metric event.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificStatus {
    EmpiricalPmf,
    ConditionalContinuous,
    ExperimentalRestrictedDomain,
    IncompleteDiagnostic,
    ResearchOnly,
    Unsupported,
}

/// Versioned mathematical definition and finite-sample estimator identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EstimatorIdentity {
    pub family: String,
    pub definition_revision: String,
    pub estimator_revision: String,
}

/// Typed provenance which travels with a publication-facing PID metric.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PidMetricProvenance {
    pub data_hash: HashIdentity,
    pub preprocessing_hash: HashIdentity,
    pub split_ids: Vec<String>,
    pub support_contract: String,
    pub metric: String,
    pub k: Option<usize>,
    pub diagnostics: serde_json::Value,
    pub warnings: Vec<String>,
}

/// Complete typed PID metric payload for schema 2.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PidMetricReport {
    pub name: String,
    #[serde(deserialize_with = "deserialize_json_f64")]
    pub value_nats: f64,
    pub status: ScientificStatus,
    pub estimator: EstimatorIdentity,
    pub provenance: PidMetricProvenance,
}

/// Optional trusted service, transparency log, signature, DOI, or other external anchor.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalAnchor {
    pub provider: String,
    pub uri: String,
    pub anchored_hash: HashIdentity,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub signature: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Pose {
    #[serde(deserialize_with = "deserialize_json_f64_array")]
    pub position: [f64; 3],
    #[serde(deserialize_with = "deserialize_json_f64_array")]
    pub orientation_xyzw: [f64; 4],
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SimObjectSnapshot {
    pub object_id: String,
    pub pose: Pose,
    #[serde(deserialize_with = "deserialize_json_f64_array")]
    pub velocity: [f64; 3],
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EmbeddingVariableContract {
    pub variable: String,
    pub source: String,
    pub dims: Vec<usize>,
    pub artifact_uri: Option<String>,
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
#[non_exhaustive]
pub enum RunLogEvent {
    RunStarted {
        schema_version: u32,
        run_id: String,
        timestamp_ns: u64,
        config_hash: String,
        metadata: BTreeMap<String, String>,
    },
    RunEnded {
        run_id: String,
        timestamp_ns: u64,
        status: RunStatus,
        message: Option<String>,
    },
    ConfigLogged {
        timestamp_ns: u64,
        config_hash: String,
        config: serde_json::Value,
    },
    FrameObserved {
        step: u64,
        timestamp_ns: u64,
        observation_hash: Option<String>,
        metadata: BTreeMap<String, String>,
    },
    EmbeddingCaptured {
        step: u64,
        timestamp_ns: u64,
        name: String,
        dims: Vec<usize>,
        artifact_uri: Option<String>,
        sha256: Option<String>,
        metadata: BTreeMap<String, String>,
    },
    EmbeddingContract {
        timestamp_ns: u64,
        name: String,
        variables: Vec<EmbeddingVariableContract>,
        metadata: BTreeMap<String, String>,
    },
    SimSnapshot {
        step: u64,
        timestamp_ns: u64,
        objects: Vec<SimObjectSnapshot>,
        metadata: BTreeMap<String, String>,
    },
    BridgeRequest {
        step: Option<u64>,
        timestamp_ns: u64,
        request_id: String,
        actor: Actor,
        method: String,
        payload_hash: String,
        payload: serde_json::Value,
    },
    BridgeResponse {
        step: Option<u64>,
        timestamp_ns: u64,
        request_id: String,
        ok: bool,
        message: Option<String>,
        result_hash: Option<String>,
    },
    ActionApplied {
        step: u64,
        timestamp_ns: u64,
        actor: Actor,
        action_type: String,
        payload_hash: String,
        payload: serde_json::Value,
    },
    ObjectPose {
        step: u64,
        timestamp_ns: u64,
        object_id: String,
        pose: Pose,
    },
    FlowGt {
        step: u64,
        timestamp_ns: u64,
        object_id: String,
        #[serde(deserialize_with = "deserialize_json_vec3s")]
        flow: Vec<[f64; 3]>,
    },
    FlowPred {
        step: u64,
        timestamp_ns: u64,
        source: String,
        object_id: String,
        horizon_steps: u64,
        #[serde(deserialize_with = "deserialize_json_vec3s")]
        flow: Vec<[f64; 3]>,
        metadata: BTreeMap<String, String>,
    },
    PidMetric {
        step: u64,
        timestamp_ns: u64,
        name: String,
        #[serde(deserialize_with = "deserialize_json_f64")]
        value: f64,
        metadata: BTreeMap<String, String>,
    },
    /// Schema-2 publication-facing PID metric with inseparable method and provenance metadata.
    PidEstimate {
        step: u64,
        timestamp_ns: u64,
        report: PidMetricReport,
    },
    GeometryMetric {
        step: u64,
        timestamp_ns: u64,
        name: String,
        #[serde(deserialize_with = "deserialize_json_f64")]
        value: f64,
        metadata: BTreeMap<String, String>,
    },
    EvaluationMetric {
        step: u64,
        timestamp_ns: u64,
        name: String,
        #[serde(deserialize_with = "deserialize_json_f64")]
        value: f64,
        metadata: BTreeMap<String, String>,
    },
    LabelObserved {
        step: u64,
        timestamp_ns: u64,
        name: String,
        value: serde_json::Value,
        metadata: BTreeMap<String, String>,
    },
    InterventionApplied {
        step: u64,
        timestamp_ns: u64,
        actor: Actor,
        intervention_type: String,
        payload_hash: String,
        payload: serde_json::Value,
    },
    ArtifactLogged {
        timestamp_ns: u64,
        name: String,
        kind: String,
        uri: String,
        sha256: Option<String>,
        metadata: BTreeMap<String, String>,
    },
    AttributionLogged {
        timestamp_ns: u64,
        method: String,
        target_output: String,
        layer: Option<String>,
        modality: Option<String>,
        baseline: Option<String>,
        score_hash: Option<String>,
        faithfulness_check: Option<bool>,
        artifact_uri: Option<String>,
        metadata: BTreeMap<String, String>,
    },
    ErrorLogged {
        step: Option<u64>,
        timestamp_ns: u64,
        message: String,
        recoverable: bool,
    },
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunLogEventContract {
    pub event_type: String,
    pub has_step: bool,
    pub carries_payload_hash: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunLogContract {
    pub schema_version: u32,
    pub event_types: Vec<RunLogEventContract>,
    pub actor_types: Vec<String>,
    pub run_statuses: Vec<String>,
    pub sidecars: Vec<String>,
    pub validation_rules: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct PoseRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub pose: Pose,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct MetricRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub value: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct PidEstimateRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub report: PidMetricReport,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ActionRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub actor: Actor,
    pub action_type: String,
    pub payload_hash: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct EmbeddingRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub name: String,
    pub dims: Vec<usize>,
    pub artifact_uri: Option<String>,
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct EmbeddingContractRecord {
    pub timestamp_ns: u64,
    pub name: String,
    pub variables: Vec<EmbeddingVariableContract>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct BridgeRecord {
    pub step: Option<u64>,
    pub timestamp_ns: u64,
    pub request_id: String,
    pub method: String,
    pub payload_hash: Option<String>,
    pub ok: Option<bool>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct InterventionRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub actor: Actor,
    pub intervention_type: String,
    pub payload_hash: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ArtifactRecord {
    pub timestamp_ns: u64,
    pub name: String,
    pub kind: String,
    pub uri: String,
    pub sha256: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct AttributionRecord {
    pub timestamp_ns: u64,
    pub method: String,
    pub target_output: String,
    pub layer: Option<String>,
    pub modality: Option<String>,
    pub baseline: Option<String>,
    pub score_hash: Option<String>,
    pub faithfulness_check: Option<bool>,
    pub artifact_uri: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct LabelRecord {
    pub step: u64,
    pub timestamp_ns: u64,
    pub name: String,
    pub value: serde_json::Value,
}

#[derive(Debug, Clone, Default, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ReplayState {
    pub schema_version: Option<u32>,
    pub run_id: Option<String>,
    pub config_hash: Option<String>,
    pub status: Option<RunStatus>,
    pub last_step: Option<u64>,
    pub last_timestamp_ns: Option<u64>,
    pub events_seen: usize,
    /// Total JSONL bytes, including one newline per event, accepted by bounded in-memory replay.
    #[serde(default)]
    pub replay_input_bytes: u64,
    pub object_poses: BTreeMap<String, PoseRecord>,
    pub pid_metrics: BTreeMap<String, MetricRecord>,
    #[serde(default)]
    pub pid_estimates: BTreeMap<String, PidEstimateRecord>,
    pub geometry_metrics: BTreeMap<String, MetricRecord>,
    pub evaluation_metrics: BTreeMap<String, MetricRecord>,
    #[serde(default)]
    pub pid_metric_events: usize,
    #[serde(default)]
    pub geometry_metric_events: usize,
    #[serde(default)]
    pub evaluation_metric_events: usize,
    pub labels: Vec<LabelRecord>,
    pub actions: Vec<ActionRecord>,
    pub interventions: Vec<InterventionRecord>,
    pub artifacts: Vec<ArtifactRecord>,
    pub attributions: Vec<AttributionRecord>,
    pub embeddings: Vec<EmbeddingRecord>,
    pub embedding_contracts: Vec<EmbeddingContractRecord>,
    pub bridge_records: Vec<BridgeRecord>,
    pub sim_snapshots: usize,
    pub errors: Vec<String>,
    pub flow_gt_records: usize,
    pub flow_pred_records: usize,
}

fn reserve_replay_slot<T>(
    values: &mut Vec<T>,
    operation: &'static str,
    limits: RunLogLimits,
) -> Result<()> {
    let requested = values
        .len()
        .checked_add(1)
        .ok_or_else(|| resource_limit(operation, usize::MAX, limits.max_array_len))?;
    if requested > limits.max_array_len {
        return Err(resource_limit(operation, requested, limits.max_array_len));
    }
    values
        .try_reserve(1)
        .map_err(|_| resource_limit(operation, requested, limits.max_array_len))
}

fn check_replay_map_entry<K: Ord, V>(
    values: &BTreeMap<K, V>,
    key: &K,
    operation: &'static str,
    limits: RunLogLimits,
) -> Result<()> {
    if values.contains_key(key) {
        return Ok(());
    }
    let requested = values
        .len()
        .checked_add(1)
        .ok_or_else(|| resource_limit(operation, usize::MAX, limits.max_object_entries))?;
    if requested > limits.max_object_entries {
        return Err(resource_limit(
            operation,
            requested,
            limits.max_object_entries,
        ));
    }
    Ok(())
}

fn increment_replay_counter(value: &mut usize, operation: &'static str) -> Result<()> {
    *value = value
        .checked_add(1)
        .ok_or_else(|| resource_limit(operation, u128::MAX, usize::MAX))?;
    Ok(())
}

fn check_replay_counter(value: usize, operation: &'static str) -> Result<()> {
    value
        .checked_add(1)
        .ok_or_else(|| resource_limit(operation, u128::MAX, usize::MAX))?;
    Ok(())
}

fn preflight_replay_state_mutation(
    state: &mut ReplayState,
    event: &RunLogEvent,
    limits: RunLogLimits,
) -> Result<()> {
    match event {
        RunLogEvent::EmbeddingCaptured { .. } => {
            reserve_replay_slot(&mut state.embeddings, "replay embedding count", limits)
        }
        RunLogEvent::EmbeddingContract { .. } => reserve_replay_slot(
            &mut state.embedding_contracts,
            "replay embedding-contract count",
            limits,
        ),
        RunLogEvent::BridgeRequest { .. } | RunLogEvent::BridgeResponse { .. } => {
            reserve_replay_slot(
                &mut state.bridge_records,
                "replay bridge-record count",
                limits,
            )
        }
        RunLogEvent::ActionApplied { .. } => {
            reserve_replay_slot(&mut state.actions, "replay action count", limits)
        }
        RunLogEvent::ObjectPose { object_id, .. } => check_replay_map_entry(
            &state.object_poses,
            object_id,
            "replay object-pose keys",
            limits,
        ),
        RunLogEvent::PidMetric { name, .. } => {
            check_replay_counter(state.pid_metric_events, "replay PID metrics")?;
            check_replay_map_entry(&state.pid_metrics, name, "replay PID metric keys", limits)
        }
        RunLogEvent::PidEstimate { report, .. } => {
            check_replay_counter(state.pid_metric_events, "replay PID metrics")?;
            check_replay_map_entry(
                &state.pid_metrics,
                &report.name,
                "replay PID metric keys",
                limits,
            )?;
            check_replay_map_entry(
                &state.pid_estimates,
                &report.name,
                "replay typed PID estimate keys",
                limits,
            )
        }
        RunLogEvent::GeometryMetric { name, .. } => {
            check_replay_counter(state.geometry_metric_events, "replay geometry metrics")?;
            check_replay_map_entry(
                &state.geometry_metrics,
                name,
                "replay geometry metric keys",
                limits,
            )
        }
        RunLogEvent::EvaluationMetric { name, .. } => {
            check_replay_counter(state.evaluation_metric_events, "replay evaluation metrics")?;
            check_replay_map_entry(
                &state.evaluation_metrics,
                name,
                "replay evaluation metric keys",
                limits,
            )
        }
        RunLogEvent::LabelObserved { .. } => {
            reserve_replay_slot(&mut state.labels, "replay label count", limits)
        }
        RunLogEvent::InterventionApplied { .. } => reserve_replay_slot(
            &mut state.interventions,
            "replay intervention count",
            limits,
        ),
        RunLogEvent::ArtifactLogged { .. } => {
            reserve_replay_slot(&mut state.artifacts, "replay artifact count", limits)
        }
        RunLogEvent::AttributionLogged { .. } => {
            reserve_replay_slot(&mut state.attributions, "replay attribution count", limits)
        }
        RunLogEvent::ErrorLogged { .. } => {
            reserve_replay_slot(&mut state.errors, "replay error count", limits)
        }
        RunLogEvent::SimSnapshot { .. } => {
            check_replay_counter(state.sim_snapshots, "replay simulation snapshots")
        }
        RunLogEvent::FlowGt { .. } => {
            check_replay_counter(state.flow_gt_records, "replay ground-truth flows")
        }
        RunLogEvent::FlowPred { .. } => {
            check_replay_counter(state.flow_pred_records, "replay predicted flows")
        }
        RunLogEvent::RunStarted { .. }
        | RunLogEvent::RunEnded { .. }
        | RunLogEvent::ConfigLogged { .. }
        | RunLogEvent::FrameObserved { .. } => Ok(()),
    }
}

impl ReplayState {
    /// Apply one event under the default finite replay budget.
    pub fn apply(&mut self, event: &RunLogEvent) -> Result<()> {
        self.apply_with_limits(event, RunLogLimits::default())
    }

    /// Apply one event under explicit count, byte, string, and container limits.
    pub fn apply_with_limits(&mut self, event: &RunLogEvent, limits: RunLogLimits) -> Result<()> {
        let limits = limits.validate()?;
        let next_events = self.events_seen.checked_add(1).ok_or_else(|| {
            resource_limit(
                "in-memory replay event count",
                usize::MAX,
                limits.max_events,
            )
        })?;
        if next_events > limits.max_events {
            return Err(resource_limit(
                "in-memory replay event count",
                next_events,
                limits.max_events,
            ));
        }
        let encoded = validated_json_bytes_with_limits(event, limits)?;
        let encoded_len = u64::try_from(encoded.len())
            .ok()
            .and_then(|encoded_len| encoded_len.checked_add(1))
            .ok_or_else(|| {
                resource_limit("in-memory replay bytes", u128::MAX, limits.max_file_bytes)
            })?;
        drop(encoded);
        let next_bytes = self
            .replay_input_bytes
            .checked_add(encoded_len)
            .ok_or_else(|| {
                resource_limit("in-memory replay bytes", u128::MAX, limits.max_file_bytes)
            })?;
        if next_bytes > limits.max_file_bytes {
            return Err(resource_limit(
                "in-memory replay bytes",
                next_bytes,
                limits.max_file_bytes,
            ));
        }
        // Reserve/check every branch-specific destination before mutating logical replay state.
        // A returned error therefore leaves the state value unchanged (capacity growth is not
        // observable through equality or serialization).
        preflight_replay_state_mutation(self, event, limits)?;
        self.events_seen = next_events;
        self.replay_input_bytes = next_bytes;
        self.last_timestamp_ns = Some(event.timestamp_ns());
        if let Some(step) = event.step() {
            self.last_step = Some(step);
        }

        match event {
            RunLogEvent::RunStarted {
                schema_version,
                run_id,
                config_hash,
                ..
            } => {
                self.schema_version = Some(*schema_version);
                self.run_id = Some(run_id.clone());
                self.config_hash = Some(config_hash.clone());
            }
            RunLogEvent::RunEnded { status, .. } => {
                self.status = Some(status.clone());
            }
            RunLogEvent::ConfigLogged { config_hash, .. } => {
                self.config_hash = Some(config_hash.clone());
            }
            RunLogEvent::FrameObserved { .. } => {}
            RunLogEvent::EmbeddingCaptured {
                step,
                timestamp_ns,
                name,
                dims,
                artifact_uri,
                sha256,
                ..
            } => {
                reserve_replay_slot(&mut self.embeddings, "replay embedding count", limits)?;
                self.embeddings.push(EmbeddingRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    name: name.clone(),
                    dims: dims.clone(),
                    artifact_uri: artifact_uri.clone(),
                    sha256: sha256.clone(),
                });
            }
            RunLogEvent::EmbeddingContract {
                timestamp_ns,
                name,
                variables,
                ..
            } => {
                reserve_replay_slot(
                    &mut self.embedding_contracts,
                    "replay embedding-contract count",
                    limits,
                )?;
                self.embedding_contracts.push(EmbeddingContractRecord {
                    timestamp_ns: *timestamp_ns,
                    name: name.clone(),
                    variables: variables.clone(),
                });
            }
            RunLogEvent::SimSnapshot { .. } => {
                increment_replay_counter(&mut self.sim_snapshots, "replay simulation snapshots")?;
            }
            RunLogEvent::BridgeRequest {
                step,
                timestamp_ns,
                request_id,
                method,
                payload_hash,
                ..
            } => {
                reserve_replay_slot(
                    &mut self.bridge_records,
                    "replay bridge-record count",
                    limits,
                )?;
                self.bridge_records.push(BridgeRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    request_id: request_id.clone(),
                    method: method.clone(),
                    payload_hash: Some(payload_hash.clone()),
                    ok: None,
                });
            }
            RunLogEvent::BridgeResponse {
                step,
                timestamp_ns,
                request_id,
                ok,
                ..
            } => {
                reserve_replay_slot(
                    &mut self.bridge_records,
                    "replay bridge-record count",
                    limits,
                )?;
                self.bridge_records.push(BridgeRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    request_id: request_id.clone(),
                    method: "response".to_string(),
                    payload_hash: None,
                    ok: Some(*ok),
                });
            }
            RunLogEvent::ActionApplied {
                step,
                timestamp_ns,
                actor,
                action_type,
                payload_hash,
                ..
            } => {
                reserve_replay_slot(&mut self.actions, "replay action count", limits)?;
                self.actions.push(ActionRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    actor: actor.clone(),
                    action_type: action_type.clone(),
                    payload_hash: payload_hash.clone(),
                });
            }
            RunLogEvent::ObjectPose {
                step,
                timestamp_ns,
                object_id,
                pose,
            } => {
                check_replay_map_entry(
                    &self.object_poses,
                    object_id,
                    "replay object-pose keys",
                    limits,
                )?;
                self.object_poses.insert(
                    object_id.clone(),
                    PoseRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        pose: pose.clone(),
                    },
                );
            }
            RunLogEvent::FlowGt { .. } => {
                increment_replay_counter(&mut self.flow_gt_records, "replay ground-truth flows")?;
            }
            RunLogEvent::FlowPred { .. } => {
                increment_replay_counter(&mut self.flow_pred_records, "replay predicted flows")?;
            }
            RunLogEvent::PidMetric {
                step,
                timestamp_ns,
                name,
                value,
                ..
            } => {
                increment_replay_counter(&mut self.pid_metric_events, "replay PID metrics")?;
                check_replay_map_entry(&self.pid_metrics, name, "replay PID metric keys", limits)?;
                self.pid_metrics.insert(
                    name.clone(),
                    MetricRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        value: *value,
                    },
                );
            }
            RunLogEvent::PidEstimate {
                step,
                timestamp_ns,
                report,
            } => {
                increment_replay_counter(&mut self.pid_metric_events, "replay PID metrics")?;
                check_replay_map_entry(
                    &self.pid_metrics,
                    &report.name,
                    "replay PID metric keys",
                    limits,
                )?;
                self.pid_metrics.insert(
                    report.name.clone(),
                    MetricRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        value: report.value_nats,
                    },
                );
                check_replay_map_entry(
                    &self.pid_estimates,
                    &report.name,
                    "replay typed PID estimate keys",
                    limits,
                )?;
                self.pid_estimates.insert(
                    report.name.clone(),
                    PidEstimateRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        report: report.clone(),
                    },
                );
            }
            RunLogEvent::GeometryMetric {
                step,
                timestamp_ns,
                name,
                value,
                ..
            } => {
                increment_replay_counter(
                    &mut self.geometry_metric_events,
                    "replay geometry metrics",
                )?;
                check_replay_map_entry(
                    &self.geometry_metrics,
                    name,
                    "replay geometry metric keys",
                    limits,
                )?;
                self.geometry_metrics.insert(
                    name.clone(),
                    MetricRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        value: *value,
                    },
                );
            }
            RunLogEvent::EvaluationMetric {
                step,
                timestamp_ns,
                name,
                value,
                ..
            } => {
                increment_replay_counter(
                    &mut self.evaluation_metric_events,
                    "replay evaluation metrics",
                )?;
                check_replay_map_entry(
                    &self.evaluation_metrics,
                    name,
                    "replay evaluation metric keys",
                    limits,
                )?;
                self.evaluation_metrics.insert(
                    name.clone(),
                    MetricRecord {
                        step: *step,
                        timestamp_ns: *timestamp_ns,
                        value: *value,
                    },
                );
            }
            RunLogEvent::LabelObserved {
                step,
                timestamp_ns,
                name,
                value,
                ..
            } => {
                reserve_replay_slot(&mut self.labels, "replay label count", limits)?;
                self.labels.push(LabelRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    name: name.clone(),
                    value: value.clone(),
                });
            }
            RunLogEvent::InterventionApplied {
                step,
                timestamp_ns,
                actor,
                intervention_type,
                payload_hash,
                ..
            } => {
                reserve_replay_slot(&mut self.interventions, "replay intervention count", limits)?;
                self.interventions.push(InterventionRecord {
                    step: *step,
                    timestamp_ns: *timestamp_ns,
                    actor: actor.clone(),
                    intervention_type: intervention_type.clone(),
                    payload_hash: payload_hash.clone(),
                });
            }
            RunLogEvent::ArtifactLogged {
                timestamp_ns,
                name,
                kind,
                uri,
                sha256,
                ..
            } => {
                reserve_replay_slot(&mut self.artifacts, "replay artifact count", limits)?;
                self.artifacts.push(ArtifactRecord {
                    timestamp_ns: *timestamp_ns,
                    name: name.clone(),
                    kind: kind.clone(),
                    uri: uri.clone(),
                    sha256: sha256.clone(),
                });
            }
            RunLogEvent::AttributionLogged {
                timestamp_ns,
                method,
                target_output,
                layer,
                modality,
                baseline,
                score_hash,
                faithfulness_check,
                artifact_uri,
                ..
            } => {
                reserve_replay_slot(&mut self.attributions, "replay attribution count", limits)?;
                self.attributions.push(AttributionRecord {
                    timestamp_ns: *timestamp_ns,
                    method: method.clone(),
                    target_output: target_output.clone(),
                    layer: layer.clone(),
                    modality: modality.clone(),
                    baseline: baseline.clone(),
                    score_hash: score_hash.clone(),
                    faithfulness_check: *faithfulness_check,
                    artifact_uri: artifact_uri.clone(),
                });
            }
            RunLogEvent::ErrorLogged { message, .. } => {
                reserve_replay_slot(&mut self.errors, "replay error count", limits)?;
                self.errors.push(message.clone());
            }
        }
        Ok(())
    }
}

impl RunLogEvent {
    pub fn timestamp_ns(&self) -> u64 {
        match self {
            RunLogEvent::RunStarted { timestamp_ns, .. }
            | RunLogEvent::RunEnded { timestamp_ns, .. }
            | RunLogEvent::ConfigLogged { timestamp_ns, .. }
            | RunLogEvent::FrameObserved { timestamp_ns, .. }
            | RunLogEvent::EmbeddingCaptured { timestamp_ns, .. }
            | RunLogEvent::EmbeddingContract { timestamp_ns, .. }
            | RunLogEvent::SimSnapshot { timestamp_ns, .. }
            | RunLogEvent::BridgeRequest { timestamp_ns, .. }
            | RunLogEvent::BridgeResponse { timestamp_ns, .. }
            | RunLogEvent::ActionApplied { timestamp_ns, .. }
            | RunLogEvent::ObjectPose { timestamp_ns, .. }
            | RunLogEvent::FlowGt { timestamp_ns, .. }
            | RunLogEvent::FlowPred { timestamp_ns, .. }
            | RunLogEvent::PidMetric { timestamp_ns, .. }
            | RunLogEvent::PidEstimate { timestamp_ns, .. }
            | RunLogEvent::GeometryMetric { timestamp_ns, .. }
            | RunLogEvent::EvaluationMetric { timestamp_ns, .. }
            | RunLogEvent::LabelObserved { timestamp_ns, .. }
            | RunLogEvent::InterventionApplied { timestamp_ns, .. }
            | RunLogEvent::ArtifactLogged { timestamp_ns, .. }
            | RunLogEvent::AttributionLogged { timestamp_ns, .. }
            | RunLogEvent::ErrorLogged { timestamp_ns, .. } => *timestamp_ns,
        }
    }

    pub fn step(&self) -> Option<u64> {
        match self {
            RunLogEvent::FrameObserved { step, .. }
            | RunLogEvent::EmbeddingCaptured { step, .. }
            | RunLogEvent::SimSnapshot { step, .. }
            | RunLogEvent::ActionApplied { step, .. }
            | RunLogEvent::ObjectPose { step, .. }
            | RunLogEvent::FlowGt { step, .. }
            | RunLogEvent::FlowPred { step, .. }
            | RunLogEvent::PidMetric { step, .. }
            | RunLogEvent::PidEstimate { step, .. }
            | RunLogEvent::GeometryMetric { step, .. }
            | RunLogEvent::EvaluationMetric { step, .. }
            | RunLogEvent::LabelObserved { step, .. }
            | RunLogEvent::InterventionApplied { step, .. } => Some(*step),
            RunLogEvent::BridgeRequest { step, .. }
            | RunLogEvent::BridgeResponse { step, .. }
            | RunLogEvent::ErrorLogged { step, .. } => *step,
            RunLogEvent::RunStarted { .. }
            | RunLogEvent::RunEnded { .. }
            | RunLogEvent::ConfigLogged { .. }
            | RunLogEvent::EmbeddingContract { .. }
            | RunLogEvent::ArtifactLogged { .. }
            | RunLogEvent::AttributionLogged { .. } => None,
        }
    }
}

pub fn runlog_event_contracts() -> Vec<RunLogEventContract> {
    RUN_LOG_EVENT_TYPES
        .iter()
        .map(|event_type| RunLogEventContract {
            event_type: (*event_type).to_string(),
            has_step: matches!(
                *event_type,
                "frame_observed"
                    | "embedding_captured"
                    | "sim_snapshot"
                    | "bridge_request"
                    | "bridge_response"
                    | "action_applied"
                    | "object_pose"
                    | "flow_gt"
                    | "flow_pred"
                    | "pid_metric"
                    | "pid_estimate"
                    | "geometry_metric"
                    | "evaluation_metric"
                    | "label_observed"
                    | "intervention_applied"
                    | "error_logged"
            ),
            carries_payload_hash: matches!(
                *event_type,
                "bridge_request" | "action_applied" | "intervention_applied"
            ),
        })
        .collect()
}

pub fn runlog_contract() -> RunLogContract {
    RunLogContract {
        schema_version: RUN_LOG_SCHEMA_VERSION,
        event_types: runlog_event_contracts(),
        actor_types: ["human_gui", "script", "llm_tool", "system"]
            .into_iter()
            .map(str::to_string)
            .collect(),
        run_statuses: ["succeeded", "failed", "aborted"]
            .into_iter()
            .map(str::to_string)
            .collect(),
        sidecars: RUN_LOG_SIDECARS
            .iter()
            .map(|value| (*value).to_string())
            .collect(),
        validation_rules: RUN_LOG_VALIDATION_RULES
            .iter()
            .map(|value| (*value).to_string())
            .collect(),
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ValidationSeverity {
    Error,
    Warning,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ValidationIssue {
    pub severity: ValidationSeverity,
    pub event_index: Option<usize>,
    pub message: String,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ValidationReport {
    pub events: usize,
    pub errors: usize,
    pub warnings: usize,
    pub issues: Vec<ValidationIssue>,
}

impl ValidationReport {
    pub fn is_valid(&self) -> bool {
        self.errors == 0
    }

    fn error(&mut self, event_index: Option<usize>, message: impl Into<String>) {
        self.errors += 1;
        self.issues.push(ValidationIssue {
            severity: ValidationSeverity::Error,
            event_index,
            message: message.into(),
        });
    }

    fn warning(&mut self, event_index: Option<usize>, message: impl Into<String>) {
        self.warnings += 1;
        self.issues.push(ValidationIssue {
            severity: ValidationSeverity::Warning,
            event_index,
            message: message.into(),
        });
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunLogSummary {
    /// Sidecar schema. Missing in historical files and treated as schema 1.
    #[serde(default = "legacy_sidecar_schema_version")]
    pub sidecar_schema_version: u32,
    pub schema_version: Option<u32>,
    pub run_id: Option<String>,
    pub config_hash: Option<String>,
    pub status: Option<RunStatus>,
    pub event_count: usize,
    /// Schema-1 replay hash when the log is representable by the released finite-`f64` algorithm.
    /// This is empty when no schema-1 digest exists; it never aliases a newer hash generation.
    pub trace_hash: String,
    /// Explicit lossless replay hash. Older sidecars deserialize this field as an empty string.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub trace_hash_v2: String,
    /// Schema-1 logical trace hash, with every field named `timestamp_ns` excluded for backward
    /// compatibility. This is empty when schema-1 number normalization is impossible.
    pub logical_trace_hash: String,
    /// Explicit lossless logical hash with only top-level event clocks excluded.
    /// Older sidecars deserialize this field as an empty string.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub logical_trace_hash_v3: String,
    /// Unambiguous identities for new readers. Historical sidecars omit this field.
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hash_identities: Option<RunLogHashIdentities>,
    pub validation_errors: usize,
    pub validation_warnings: usize,
    pub last_step: Option<u64>,
    pub last_timestamp_ns: Option<u64>,
    pub actions: usize,
    pub interventions: usize,
    pub objects: usize,
    pub pid_metrics: usize,
    pub geometry_metrics: usize,
    pub evaluation_metrics: usize,
    #[serde(default)]
    pub pid_metric_events: usize,
    #[serde(default)]
    pub geometry_metric_events: usize,
    #[serde(default)]
    pub evaluation_metric_events: usize,
    pub labels: usize,
    pub embeddings: usize,
    pub embedding_contracts: usize,
    pub bridge_records: usize,
    pub sim_snapshots: usize,
    pub artifacts: usize,
    pub attributions: usize,
    pub errors: usize,
    pub flow_gt_records: usize,
    pub flow_pred_records: usize,
    pub validation_issues: Vec<ValidationIssue>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ArtifactManifestEntry {
    pub name: String,
    pub kind: String,
    pub uri: String,
    pub sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub content_hash: Option<HashIdentity>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunManifest {
    #[serde(default = "legacy_sidecar_schema_version")]
    pub sidecar_schema_version: u32,
    pub schema_version: u32,
    pub run_id: Option<String>,
    pub config_hash: Option<String>,
    /// Exact UTF-8 spelling of the filesystem path supplied during manifest construction.
    pub run_log_uri: String,
    pub run_log_sha256: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub run_log_hash: Option<HashIdentity>,
    /// Compatibility replay hash. See [`RunLogSummary::trace_hash`].
    pub trace_hash: String,
    /// Explicit lossless replay hash. Older sidecars deserialize this field as an empty string.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub trace_hash_v2: String,
    /// Compatibility logical trace hash. See [`RunLogSummary::logical_trace_hash`].
    pub logical_trace_hash: String,
    /// Explicit lossless logical hash with only top-level event clocks excluded.
    /// Older sidecars deserialize this field as an empty string.
    #[serde(default, skip_serializing_if = "String::is_empty")]
    pub logical_trace_hash_v3: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub hash_identities: Option<RunLogHashIdentities>,
    pub event_count: usize,
    pub validation_errors: usize,
    pub validation_warnings: usize,
    pub artifacts: Vec<ArtifactManifestEntry>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub external_anchors: Vec<ExternalAnchor>,
}

const fn legacy_sidecar_schema_version() -> u32 {
    1
}

impl RunManifest {
    /// Attach a syntactically validated external provenance anchor.
    pub fn add_external_anchor(&mut self, anchor: ExternalAnchor) -> Result<()> {
        self.add_external_anchor_with_limits(anchor, RunLogLimits::default())
    }

    /// Attach an anchor under explicit string and collection limits.
    pub fn add_external_anchor_with_limits(
        &mut self,
        anchor: ExternalAnchor,
        limits: RunLogLimits,
    ) -> Result<()> {
        let limits = limits.validate()?;
        let requested = self.external_anchors.len().checked_add(1).ok_or_else(|| {
            resource_limit("external anchor count", usize::MAX, limits.max_array_len)
        })?;
        if requested > limits.max_array_len {
            return Err(resource_limit(
                "external anchor count",
                requested,
                limits.max_array_len,
            ));
        }
        for (field, value) in [
            (
                "external anchor provider bytes",
                Some(anchor.provider.as_str()),
            ),
            ("external anchor URI bytes", Some(anchor.uri.as_str())),
            (
                "external anchor signature bytes",
                anchor.signature.as_deref(),
            ),
        ] {
            if let Some(value) = value {
                if value.len() > limits.max_string_bytes {
                    return Err(resource_limit(field, value.len(), limits.max_string_bytes));
                }
            }
        }
        validate_nonempty("external anchor provider", &anchor.provider)?;
        validate_artifact_location(&anchor.uri).context("invalid external anchor URI or path")?;
        anchor.anchored_hash.validate()?;
        if anchor
            .signature
            .as_deref()
            .is_some_and(|signature| signature.trim().is_empty())
        {
            anyhow::bail!("external anchor signature must not be empty when present");
        }
        self.external_anchors.try_reserve(1).map_err(|_| {
            resource_limit(
                "external anchor allocation",
                requested,
                limits.max_array_len,
            )
        })?;
        self.external_anchors.push(anchor);
        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub struct RunLogSidecarPaths {
    pub validation: PathBuf,
    pub summary: PathBuf,
    pub manifest: PathBuf,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct RunLogSidecars {
    pub validation: ValidationReport,
    pub summary: RunLogSummary,
    pub manifest: RunManifest,
}

#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct SidecarVerificationReport {
    pub checked: usize,
    pub issues: Vec<SidecarVerificationIssue>,
}

impl SidecarVerificationReport {
    pub fn is_valid(&self) -> bool {
        self.issues.is_empty()
    }

    fn issue(
        &mut self,
        sidecar: impl Into<String>,
        path: impl AsRef<Path>,
        message: impl Into<String>,
    ) {
        self.issues.push(SidecarVerificationIssue {
            sidecar: sidecar.into(),
            path: path.as_ref().display().to_string(),
            message: message.into(),
        });
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct SidecarVerificationIssue {
    pub sidecar: String,
    pub path: String,
    pub message: String,
}

struct StreamingValidationState {
    limits: RunLogLimits,
    report: ValidationReport,
    schema_version: Option<u32>,
    run_id: Option<String>,
    starts: usize,
    ends: usize,
    configs: usize,
    operational_event_seen: bool,
    last_timestamp: Option<u64>,
    last_step: Option<u64>,
    last_event_was_run_ended: bool,
    run_started_config_hash: Option<String>,
    bridge_requests: BTreeSet<String>,
    bridge_responses: BTreeSet<String>,
}

impl StreamingValidationState {
    fn new(limits: RunLogLimits) -> Self {
        Self {
            limits,
            report: ValidationReport::default(),
            schema_version: None,
            run_id: None,
            starts: 0,
            ends: 0,
            configs: 0,
            operational_event_seen: false,
            last_timestamp: None,
            last_step: None,
            last_event_was_run_ended: false,
            run_started_config_hash: None,
            bridge_requests: BTreeSet::new(),
            bridge_responses: BTreeSet::new(),
        }
    }

    fn strict_schema(&self) -> bool {
        self.schema_version.is_some_and(|version| version >= 2)
    }

    fn is_operational_event(event: &RunLogEvent) -> bool {
        !matches!(
            event,
            RunLogEvent::RunStarted { .. }
                | RunLogEvent::ConfigLogged { .. }
                | RunLogEvent::RunEnded { .. }
        )
    }

    fn push(&mut self, event: &RunLogEvent) {
        let idx = self.report.events;
        self.report.events += 1;
        self.last_event_was_run_ended = matches!(event, RunLogEvent::RunEnded { .. });
        let timestamp = event.timestamp_ns();
        if let Some(prev) = self.last_timestamp {
            if timestamp < prev {
                self.report
                    .error(Some(idx), "timestamps must be nondecreasing");
            }
        }
        self.last_timestamp = Some(timestamp);

        if let Some(step) = event.step() {
            if let Some(prev) = self.last_step {
                if step < prev {
                    self.report.error(Some(idx), "steps must be nondecreasing");
                }
            }
            self.last_step = Some(step);
        }

        if self.strict_schema() && Self::is_operational_event(event) {
            if self.configs == 0 {
                self.report.error(
                    Some(idx),
                    "schema-2 config_logged must precede operational events",
                );
            }
            self.operational_event_seen = true;
        }

        match event {
            RunLogEvent::RunStarted {
                schema_version,
                run_id: id,
                config_hash,
                ..
            } => {
                self.starts += 1;
                if idx != 0 {
                    self.report
                        .error(Some(idx), "run_started must be the first event");
                }
                self.schema_version = Some(*schema_version);
                if !(MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION..=RUN_LOG_SCHEMA_VERSION)
                    .contains(schema_version)
                {
                    self.report
                        .error(Some(idx), "unsupported run-log schema version");
                } else if *schema_version < RUN_LOG_SCHEMA_VERSION {
                    self.report.warning(
                        Some(idx),
                        "legacy run-log schema accepted through bounded compatibility reader",
                    );
                }
                if id.is_empty() {
                    self.report.error(Some(idx), "run_id must not be empty");
                }
                if config_hash.is_empty() {
                    if self.strict_schema() {
                        self.report
                            .error(Some(idx), "schema-2 run_started.config_hash is empty");
                    } else {
                        self.report.warning(Some(idx), "config_hash is empty");
                    }
                } else {
                    self.validate_hash_text(idx, "config_hash", config_hash);
                    self.run_started_config_hash = Some(config_hash.clone());
                }
                self.run_id = Some(id.clone());
            }
            RunLogEvent::RunEnded { run_id: id, .. } => {
                self.ends += 1;
                if let Some(start_id) = &self.run_id {
                    if start_id != id {
                        self.report
                            .error(Some(idx), "run_ended run_id does not match run_started");
                    }
                }
            }
            RunLogEvent::ActionApplied {
                payload_hash,
                payload,
                action_type,
                ..
            } => {
                self.validate_hash_text(idx, "payload_hash", payload_hash);
                let strict_schema = self.strict_schema();
                validate_payload_hash(
                    &mut self.report,
                    idx,
                    payload_hash,
                    payload,
                    strict_schema,
                    self.limits,
                );
                if action_type.is_empty() {
                    self.report
                        .error(Some(idx), "action_type must not be empty");
                }
            }
            RunLogEvent::InterventionApplied {
                payload_hash,
                payload,
                intervention_type,
                ..
            } => {
                self.validate_hash_text(idx, "payload_hash", payload_hash);
                let strict_schema = self.strict_schema();
                validate_payload_hash(
                    &mut self.report,
                    idx,
                    payload_hash,
                    payload,
                    strict_schema,
                    self.limits,
                );
                if intervention_type.is_empty() {
                    self.report
                        .error(Some(idx), "intervention_type must not be empty");
                }
            }
            RunLogEvent::BridgeRequest {
                request_id,
                method,
                payload_hash,
                payload,
                ..
            } => {
                self.validate_hash_text(idx, "payload_hash", payload_hash);
                let strict_schema = self.strict_schema();
                validate_payload_hash(
                    &mut self.report,
                    idx,
                    payload_hash,
                    payload,
                    strict_schema,
                    self.limits,
                );
                if request_id.is_empty() {
                    self.report
                        .error(Some(idx), "bridge request_id must not be empty");
                } else if !self.bridge_requests.insert(request_id.clone()) {
                    self.report.error(Some(idx), "duplicate bridge request_id");
                }
                if method.is_empty() {
                    self.report
                        .error(Some(idx), "bridge method must not be empty");
                }
            }
            RunLogEvent::BridgeResponse {
                request_id,
                result_hash,
                ..
            } => {
                if request_id.is_empty() {
                    self.report
                        .error(Some(idx), "bridge response request_id must not be empty");
                } else {
                    // Requests are inserted in stream order, so a response whose request_id is
                    // not yet present arrived before (or without) its request — a causality
                    // violation the end-of-stream set difference cannot catch on its own.
                    if !self.bridge_requests.contains(request_id) {
                        self.report.error(
                            Some(idx),
                            "bridge response precedes or lacks its matching request",
                        );
                    }
                    if !self.bridge_responses.insert(request_id.clone()) {
                        self.report
                            .error(Some(idx), "duplicate bridge response request_id");
                    }
                }
                if let Some(hash) = result_hash {
                    self.validate_hash_text(idx, "result_hash", hash);
                }
            }
            RunLogEvent::ObjectPose {
                object_id, pose, ..
            } => {
                if object_id.is_empty() {
                    self.report.error(Some(idx), "object_id must not be empty");
                }
                validate_pose(&mut self.report, idx, pose);
            }
            RunLogEvent::SimSnapshot { objects, .. } => {
                for object in objects {
                    if object.object_id.is_empty() {
                        self.report
                            .error(Some(idx), "snapshot object_id must not be empty");
                    }
                    validate_pose(&mut self.report, idx, &object.pose);
                    validate_vec3(&mut self.report, idx, object.velocity, "snapshot velocity");
                }
            }
            RunLogEvent::FlowGt {
                object_id, flow, ..
            } => {
                if object_id.is_empty() {
                    self.report
                        .error(Some(idx), "flow object_id must not be empty");
                }
                for vec in flow {
                    validate_vec3(&mut self.report, idx, *vec, "flow vector");
                }
            }
            RunLogEvent::FlowPred {
                source,
                object_id,
                horizon_steps,
                flow,
                ..
            } => {
                if source.is_empty() {
                    self.report
                        .error(Some(idx), "flow source must not be empty");
                }
                if object_id.is_empty() {
                    self.report
                        .error(Some(idx), "flow object_id must not be empty");
                }
                if *horizon_steps == 0 {
                    self.report
                        .error(Some(idx), "flow horizon_steps must be positive");
                }
                for vec in flow {
                    validate_vec3(&mut self.report, idx, *vec, "flow vector");
                }
            }
            RunLogEvent::PidMetric { name, value, .. }
            | RunLogEvent::GeometryMetric { name, value, .. }
            | RunLogEvent::EvaluationMetric { name, value, .. } => {
                if name.is_empty() {
                    self.report
                        .error(Some(idx), "metric name must not be empty");
                }
                if !value.is_finite() {
                    self.report.error(Some(idx), "metric value must be finite");
                }
            }
            RunLogEvent::PidEstimate { report, .. } => {
                validate_pid_metric_report(&mut self.report, idx, report);
                if !self.strict_schema() {
                    self.report.warning(
                        Some(idx),
                        "typed pid_estimate event appeared in legacy schema declaration",
                    );
                }
            }
            RunLogEvent::LabelObserved { name, value, .. } => {
                if name.is_empty() {
                    self.report.error(Some(idx), "label name must not be empty");
                }
                if value.is_null() {
                    self.report.error(Some(idx), "label value must not be null");
                }
            }
            RunLogEvent::EmbeddingCaptured {
                name,
                dims,
                artifact_uri,
                sha256,
                ..
            } => {
                if name.is_empty() {
                    self.report
                        .error(Some(idx), "embedding name must not be empty");
                }
                if dims.is_empty() || dims.contains(&0) {
                    self.report
                        .error(Some(idx), "embedding dims must be nonempty and positive");
                }
                if let Some(uri) = artifact_uri {
                    self.validate_location(idx, "embedding artifact_uri", uri);
                }
                if let Some(hash) = sha256 {
                    self.validate_hash_text(idx, "embedding sha256", hash);
                }
            }
            RunLogEvent::EmbeddingContract {
                name, variables, ..
            } => {
                validate_embedding_contract(&mut self.report, idx, name, variables);
                for variable in variables {
                    if let Some(uri) = &variable.artifact_uri {
                        self.validate_location(idx, "embedding contract artifact_uri", uri);
                    }
                    if let Some(hash) = &variable.sha256 {
                        self.validate_hash_text(idx, "embedding contract sha256", hash);
                    }
                }
            }
            RunLogEvent::ArtifactLogged {
                name, uri, sha256, ..
            } => {
                if name.is_empty() {
                    self.report
                        .error(Some(idx), "artifact name must not be empty");
                }
                self.validate_location(idx, "artifact uri", uri);
                if let Some(hash) = sha256 {
                    self.validate_hash_text(idx, "artifact sha256", hash);
                }
            }
            RunLogEvent::AttributionLogged {
                method,
                target_output,
                score_hash,
                artifact_uri,
                ..
            } => {
                if method.is_empty() {
                    self.report
                        .error(Some(idx), "attribution method must not be empty");
                }
                if target_output.is_empty() {
                    self.report
                        .error(Some(idx), "attribution target_output must not be empty");
                }
                if let Some(hash) = score_hash {
                    self.validate_hash_text(idx, "attribution score_hash", hash);
                }
                if let Some(uri) = artifact_uri {
                    self.validate_location(idx, "attribution artifact_uri", uri);
                }
            }
            RunLogEvent::ConfigLogged {
                config_hash,
                config,
                ..
            } => {
                self.configs += 1;
                if self.strict_schema() {
                    if self.configs > 1 {
                        self.report.error(
                            Some(idx),
                            "schema 2 requires exactly one config_logged event",
                        );
                    }
                    if self.operational_event_seen {
                        self.report.error(
                            Some(idx),
                            "schema-2 config_logged must precede operational events",
                        );
                    }
                }
                if config_hash.is_empty() {
                    if self.strict_schema() {
                        self.report
                            .error(Some(idx), "schema-2 config_logged.config_hash is empty");
                    } else {
                        self.report.warning(Some(idx), "config_hash is empty");
                    }
                } else {
                    self.validate_hash_text(idx, "config_hash", config_hash);
                    let strict_schema = self.strict_schema();
                    let hashes = validate_config_hash(
                        &mut self.report,
                        idx,
                        config_hash,
                        config,
                        strict_schema,
                        self.limits,
                    );
                    match (&self.run_started_config_hash, hashes) {
                        (Some(started_hash), Some(hashes))
                            if config_hash != started_hash
                                && !(hashes.matches_for_schema(started_hash, strict_schema)
                                    && hashes.matches_for_schema(config_hash, strict_schema)) =>
                        {
                            self.report.error(
                                Some(idx),
                                "config_logged config_hash does not match run_started",
                            );
                        }
                        (None, _) => self.report.error(
                            Some(idx),
                            "run_started.config_hash is empty but config_logged is present; config integrity cannot be verified",
                        ),
                        _ => {}
                    }
                }
            }
            RunLogEvent::FrameObserved {
                observation_hash, ..
            } => {
                if let Some(hash) = observation_hash {
                    self.validate_hash_text(idx, "observation_hash", hash);
                }
            }
            RunLogEvent::ErrorLogged { .. } => {}
        }
    }

    fn validate_hash_text(&mut self, idx: usize, field: &'static str, hash: &str) {
        if !is_sha256_hex(hash) {
            let message = format!("{field} must be a 64-character hexadecimal SHA-256 digest");
            if self.strict_schema() {
                self.report.error(Some(idx), message);
            } else {
                self.report
                    .warning(Some(idx), format!("legacy schema: {message}"));
            }
        }
    }

    fn validate_location(&mut self, idx: usize, field: &'static str, location: &str) {
        if let Err(error) = validate_artifact_location(location) {
            let message = format!("{field} is invalid: {error:#}");
            if self.strict_schema() {
                self.report.error(Some(idx), message);
            } else {
                self.report
                    .warning(Some(idx), format!("legacy schema: {message}"));
            }
        }
    }

    fn finish(mut self) -> ValidationReport {
        if self.report.events == 0 {
            self.report.error(None, "run log is empty");
            return self.report;
        }
        if !self.last_event_was_run_ended {
            self.report.error(None, "run_ended must be the last event");
        }
        if self.starts != 1 {
            self.report.error(
                None,
                format!(
                    "expected exactly one run_started event, got {}",
                    self.starts
                ),
            );
        }
        if self.ends != 1 {
            self.report.error(
                None,
                format!("expected exactly one run_ended event, got {}", self.ends),
            );
        }
        if self.strict_schema() && self.configs != 1 {
            self.report.error(
                None,
                format!(
                    "schema 2 requires exactly one config_logged event, got {}",
                    self.configs
                ),
            );
        }
        for request_id in self.bridge_requests.difference(&self.bridge_responses) {
            self.report.warning(
                None,
                format!("bridge request without response: {request_id}"),
            );
        }
        self.report
    }
}

pub fn validate_events(events: &[RunLogEvent]) -> Result<ValidationReport> {
    validate_events_with_limits(events, RunLogLimits::default())
}

/// Validate an already-decoded event slice under an explicit aggregate budget.
pub fn validate_events_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<ValidationReport> {
    preflight_event_slice(events, limits)?;
    let limits = limits.validate()?;
    let mut state = StreamingValidationState::new(limits);
    for event in events {
        state.push(event);
    }
    Ok(state.finish())
}

pub fn validate_events_from_path(path: impl AsRef<Path>) -> Result<ValidationReport> {
    validate_events_from_path_with_limits(path, RunLogLimits::default())
}

pub fn validate_events_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<ValidationReport> {
    Ok(inspect_path_with_limits(path, limits)?.validation)
}

pub fn summarize_events(events: &[RunLogEvent]) -> Result<RunLogSummary> {
    summarize_events_with_limits(events, RunLogLimits::default())
}

/// Summarize an already-decoded event slice under an explicit aggregate budget.
pub fn summarize_events_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<RunLogSummary> {
    let limits = limits.validate()?;
    let state = replay_events_with_limits(events, limits)?;
    let validation = validate_events_with_limits(events, limits)?;
    let mut accumulator = TraceHashAccumulator::new(limits);
    for event in events {
        accumulator.update(event)?;
    }
    summary_from_parts(&state, validation, accumulator.finish()?)
}

fn summary_from_parts(
    state: &ReplayState,
    validation: ValidationReport,
    hash_identities: RunLogHashIdentities,
) -> Result<RunLogSummary> {
    let trace_hash_v2 = hash_identities.replay_lossless.digest.clone();
    let logical_trace_hash_v3 = hash_identities.logical_lossless.digest.clone();
    let trace_hash = hash_identities
        .replay_legacy
        .as_ref()
        .map_or_else(String::new, |identity| identity.digest.clone());
    let logical_trace_hash = hash_identities
        .logical_legacy
        .as_ref()
        .map_or_else(String::new, |identity| identity.digest.clone());
    Ok(RunLogSummary {
        sidecar_schema_version: RUN_LOG_SIDECAR_SCHEMA_VERSION,
        schema_version: state.schema_version,
        run_id: state.run_id.clone(),
        config_hash: state.config_hash.clone(),
        status: state.status.clone(),
        event_count: state.events_seen,
        trace_hash,
        trace_hash_v2,
        logical_trace_hash,
        logical_trace_hash_v3,
        hash_identities: Some(hash_identities),
        validation_errors: validation.errors,
        validation_warnings: validation.warnings,
        last_step: state.last_step,
        last_timestamp_ns: state.last_timestamp_ns,
        actions: state.actions.len(),
        interventions: state.interventions.len(),
        objects: state.object_poses.len(),
        pid_metrics: state.pid_metrics.len(),
        geometry_metrics: state.geometry_metrics.len(),
        evaluation_metrics: state.evaluation_metrics.len(),
        pid_metric_events: state.pid_metric_events,
        geometry_metric_events: state.geometry_metric_events,
        evaluation_metric_events: state.evaluation_metric_events,
        labels: state.labels.len(),
        embeddings: state.embeddings.len(),
        embedding_contracts: state.embedding_contracts.len(),
        bridge_records: state.bridge_records.len(),
        sim_snapshots: state.sim_snapshots,
        artifacts: state.artifacts.len(),
        attributions: state.attributions.len(),
        errors: state.errors.len(),
        flow_gt_records: state.flow_gt_records,
        flow_pred_records: state.flow_pred_records,
        validation_issues: validation.issues,
    })
}

pub fn summarize_path(path: impl AsRef<Path>) -> Result<RunLogSummary> {
    summarize_path_with_limits(path, RunLogLimits::default())
}

pub fn summarize_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<RunLogSummary> {
    let inspection = inspect_path_with_limits(path, limits)?;
    summary_from_parts(
        &inspection.replay_state,
        inspection.validation,
        inspection.hash_identities,
    )
}

pub fn manifest_for_events(path: impl AsRef<Path>, events: &[RunLogEvent]) -> Result<RunManifest> {
    manifest_for_events_with_limits(path, events, RunLogLimits::default())
}

/// Construct a manifest after binding an already-decoded event slice to the file at `path`.
///
/// The file is inspected and hashed through one open handle. The supplied events must have the
/// same lossless ordered trace as that file; otherwise this returns
/// [`RunLogError::ManifestSourceMismatch`]. Opened-handle metadata and the path's file identity are
/// checked after the pass, but callers must still quiesce the path against changes after that
/// point-in-time check.
pub fn manifest_for_events_with_limits(
    path: impl AsRef<Path>,
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<RunManifest> {
    let path = path.as_ref();
    let limits = limits.validate()?;
    let hashed = inspect_path_with_hash(path, limits)?;
    let supplied_summary = summarize_events_with_limits(events, limits)?;
    if hashed.inspection.replay_state.events_seen != supplied_summary.event_count
        || hashed.inspection.hash_identities.replay_lossless.digest
            != supplied_summary.trace_hash_v2
    {
        return Err(anyhow::Error::new(RunLogError::ManifestSourceMismatch));
    }
    let summary = summary_from_parts(
        &hashed.inspection.replay_state,
        hashed.inspection.validation,
        hashed.inspection.hash_identities,
    )?;
    manifest_from_parts(
        path,
        &hashed.inspection.replay_state,
        summary,
        hashed.file_sha256,
        Vec::new(),
        limits,
    )
}

fn manifest_from_parts(
    path: &Path,
    state: &ReplayState,
    summary: RunLogSummary,
    run_log_sha256: String,
    external_anchors: Vec<ExternalAnchor>,
    limits: RunLogLimits,
) -> Result<RunManifest> {
    let path_text = path
        .to_str()
        .context("run-log manifest paths must be valid UTF-8")?;
    let run_log_uri =
        try_owned_runlog_text("run-log manifest URI", path_text, limits.max_string_bytes)?;
    let run_log_sha256_field = try_owned_runlog_text(
        "run-log manifest hash",
        &run_log_sha256,
        limits.max_string_bytes,
    )?;
    if state.artifacts.len() > limits.max_array_len {
        return Err(resource_limit(
            "manifest artifact count",
            state.artifacts.len(),
            limits.max_array_len,
        ));
    }
    let mut artifacts = Vec::new();
    artifacts
        .try_reserve_exact(state.artifacts.len())
        .map_err(|_| {
            resource_limit(
                "manifest artifact allocation",
                state.artifacts.len(),
                limits.max_array_len,
            )
        })?;
    for artifact in &state.artifacts {
        let sha256 = artifact
            .sha256
            .as_deref()
            .map(|value| {
                try_owned_runlog_text("manifest artifact hash", value, limits.max_string_bytes)
            })
            .transpose()?;
        let content_hash = sha256
            .as_deref()
            .map(|digest| {
                HashIdentity::sha256(
                    HashRevision::FileBytesV1,
                    try_owned_runlog_text(
                        "manifest artifact hash identity",
                        digest,
                        limits.max_string_bytes,
                    )?,
                )
            })
            .transpose()?;
        artifacts.push(ArtifactManifestEntry {
            name: try_owned_runlog_text(
                "manifest artifact name",
                &artifact.name,
                limits.max_string_bytes,
            )?,
            kind: try_owned_runlog_text(
                "manifest artifact kind",
                &artifact.kind,
                limits.max_string_bytes,
            )?,
            uri: try_owned_runlog_text(
                "manifest artifact URI",
                &artifact.uri,
                limits.max_string_bytes,
            )?,
            sha256,
            content_hash,
        });
    }
    Ok(RunManifest {
        sidecar_schema_version: RUN_LOG_SIDECAR_SCHEMA_VERSION,
        schema_version: state.schema_version.unwrap_or(RUN_LOG_SCHEMA_VERSION),
        run_id: summary.run_id,
        config_hash: summary.config_hash,
        run_log_uri,
        run_log_sha256: Some(run_log_sha256_field),
        run_log_hash: Some(HashIdentity::sha256(
            HashRevision::FileBytesV1,
            run_log_sha256,
        )?),
        trace_hash: summary.trace_hash,
        trace_hash_v2: summary.trace_hash_v2,
        logical_trace_hash: summary.logical_trace_hash,
        logical_trace_hash_v3: summary.logical_trace_hash_v3,
        hash_identities: summary.hash_identities,
        event_count: summary.event_count,
        validation_errors: summary.validation_errors,
        validation_warnings: summary.validation_warnings,
        artifacts,
        external_anchors,
    })
}

fn try_owned_runlog_text(
    operation: &'static str,
    value: &str,
    max_string_bytes: usize,
) -> Result<String> {
    if value.len() > max_string_bytes {
        return Err(resource_limit(operation, value.len(), max_string_bytes));
    }
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| resource_limit(operation, value.len(), max_string_bytes))?;
    owned.push_str(value);
    Ok(owned)
}

pub fn manifest_for_path(path: impl AsRef<Path>) -> Result<RunManifest> {
    manifest_for_path_with_limits(path, RunLogLimits::default())
}

/// Construct a point-in-time manifest from one opened run-log handle.
///
/// The opened handle's metadata and the path's file identity are checked after inspection. This
/// detects common observable changes during the pass, but same-length rewrites can evade coarse or
/// preserved modification timestamps, and another process can modify or retarget the path after the
/// final check. Callers must therefore quiesce concurrently written logs. The path must be valid
/// UTF-8 because it is recorded losslessly in [`RunManifest::run_log_uri`].
pub fn manifest_for_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<RunManifest> {
    let path = path.as_ref();
    let hashed = inspect_path_with_hash(path, limits)?;
    let inspection = hashed.inspection;
    let summary = summary_from_parts(
        &inspection.replay_state,
        inspection.validation,
        inspection.hash_identities,
    )?;
    manifest_from_parts(
        path,
        &inspection.replay_state,
        summary,
        hashed.file_sha256,
        Vec::new(),
        limits,
    )
}

pub fn manifest_for_path_with_anchors(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
    anchors: Vec<ExternalAnchor>,
) -> Result<RunManifest> {
    let path = path.as_ref();
    let hashed = inspect_path_with_hash(path, limits)?;
    let inspection = hashed.inspection;
    let summary = summary_from_parts(
        &inspection.replay_state,
        inspection.validation,
        inspection.hash_identities,
    )?;
    let mut manifest = manifest_from_parts(
        path,
        &inspection.replay_state,
        summary,
        hashed.file_sha256,
        Vec::new(),
        limits,
    )?;
    for anchor in anchors {
        manifest.add_external_anchor_with_limits(anchor, limits)?;
    }
    Ok(manifest)
}

pub fn runlog_sidecar_paths(path: impl AsRef<Path>) -> RunLogSidecarPaths {
    let path = path.as_ref();
    RunLogSidecarPaths {
        validation: sidecar_path(path, "validation"),
        summary: sidecar_path(path, "summary"),
        manifest: sidecar_path(path, "manifest"),
    }
}

pub fn sidecars_for_path(path: impl AsRef<Path>) -> Result<RunLogSidecars> {
    sidecars_for_path_with_limits(path, RunLogLimits::default())
}

pub fn sidecars_for_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<RunLogSidecars> {
    let path = path.as_ref();
    let hashed = inspect_path_with_hash(path, limits)?;
    let inspection = hashed.inspection;
    let validation = inspection.validation;
    let summary = summary_from_parts(
        &inspection.replay_state,
        validation.clone(),
        inspection.hash_identities,
    )?;
    let manifest = manifest_from_parts(
        path,
        &inspection.replay_state,
        summary.clone(),
        hashed.file_sha256,
        Vec::new(),
        limits,
    )?;
    Ok(RunLogSidecars {
        validation,
        summary,
        manifest,
    })
}

pub fn write_sidecars_for_path(path: impl AsRef<Path>) -> Result<RunLogSidecarPaths> {
    write_sidecars_for_path_with_limits(path, RunLogLimits::default())
}

pub fn write_sidecars_for_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<RunLogSidecarPaths> {
    let path = path.as_ref();
    let paths = runlog_sidecar_paths(path);
    for output in [&paths.validation, &paths.summary, &paths.manifest] {
        reject_runlog_output_alias(path, output)?;
    }
    let sidecars = sidecars_for_path_with_limits(path, limits)?;
    write_json_file_with_limits(&paths.validation, &sidecars.validation, limits)?;
    write_json_file_with_limits(&paths.summary, &sidecars.summary, limits)?;
    write_json_file_with_limits(&paths.manifest, &sidecars.manifest, limits)?;
    Ok(paths)
}

fn reject_runlog_output_alias(input: &Path, output: &Path) -> Result<()> {
    match same_file::is_same_file(input, output) {
        Ok(true) => anyhow::bail!(
            "refusing to replace run-log input {} through output alias {}",
            input.display(),
            output.display()
        ),
        Ok(false) => Ok(()),
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error).with_context(|| {
            format!(
                "failed to compare run-log input {} with output {}",
                input.display(),
                output.display()
            )
        }),
    }
}

pub fn verify_sidecars_for_path(path: impl AsRef<Path>) -> Result<SidecarVerificationReport> {
    verify_sidecars_for_path_with_limits(path, RunLogLimits::default())
}

pub fn verify_sidecars_for_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<SidecarVerificationReport> {
    let path = path.as_ref();
    let paths = runlog_sidecar_paths(path);
    let expected = sidecars_for_path_with_limits(path, limits)?;
    let mut report = SidecarVerificationReport::default();
    verify_sidecar(
        &mut report,
        "validation",
        &paths.validation,
        &expected.validation,
        limits,
    );
    verify_sidecar(
        &mut report,
        "summary",
        &paths.summary,
        &expected.summary,
        limits,
    );
    verify_sidecar(
        &mut report,
        "manifest",
        &paths.manifest,
        &expected.manifest,
        limits,
    );
    Ok(report)
}

fn verify_sidecar<T>(
    report: &mut SidecarVerificationReport,
    sidecar: &str,
    path: impl AsRef<Path>,
    expected: &T,
    limits: RunLogLimits,
) where
    T: Serialize,
{
    let path = path.as_ref();
    report.checked += 1;
    let actual = match read_json_value_with_limits(path, limits) {
        Ok(actual) => actual,
        Err(err) if err.kind() == ErrorKind::NotFound => {
            report.issue(sidecar, path, "sidecar is missing");
            return;
        }
        Err(err) => {
            report.issue(sidecar, path, format!("failed to open sidecar: {err}"));
            return;
        }
    };
    let mut expected = match serde_json::to_value(expected) {
        Ok(expected) => expected,
        Err(err) => {
            report.issue(
                sidecar,
                path,
                format!("failed to serialize expected sidecar: {err}"),
            );
            return;
        }
    };
    // Historical schema-1 sidecars predate the explicit `sidecar_schema_version` field. Only that
    // unmarked wire shape receives additive-field compatibility. An explicit version marker is a
    // current-schema assertion and must never be rewritten or stripped during verification:
    // otherwise changing `2` to `1` would create a trivial downgrade path.
    if matches!(sidecar, "summary" | "manifest") {
        if let (Some(actual), Some(expected)) = (actual.as_object(), expected.as_object_mut()) {
            if !actual.contains_key("sidecar_schema_version") {
                expected.remove("sidecar_schema_version");
                for field in [
                    "trace_hash_v2",
                    "logical_trace_hash_v3",
                    "hash_identities",
                    "run_log_hash",
                    "external_anchors",
                ] {
                    if !actual.contains_key(field) {
                        expected.remove(field);
                    }
                }
            }
        }
    }
    if actual != expected {
        report.issue(sidecar, path, "sidecar does not match current run log");
    }
}

pub fn write_json_file<T: Serialize>(path: impl AsRef<Path>, value: &T) -> Result<()> {
    write_json_file_with_limits(path, value, RunLogLimits::default())
}

pub fn write_json_file_with_limits<T: Serialize>(
    path: impl AsRef<Path>,
    value: &T,
    limits: RunLogLimits,
) -> Result<()> {
    let path = path.as_ref();
    let limits = limits.validate()?;
    // Serialize into a fallible bounded buffer before touching the destination. The subsequent
    // traversal rejects values which serde_json would otherwise represent as `null` (NaN/inf).
    let byte_limit = usize::try_from(limits.max_file_bytes).unwrap_or(usize::MAX);
    let bytes = serialize_json_with_byte_limit(value, true, byte_limit, "JSON output bytes")
        .with_context(|| format!("failed to serialize {}", path.display()))?;
    validate_finite_json(value)
        .with_context(|| format!("refusing to write non-finite JSON to {}", path.display()))?;
    preflight_json_bytes(&bytes, &limits)?;
    atomic_write_bytes(path, &bytes)
}

struct LimitedJsonBuffer {
    bytes: Vec<u8>,
    limit: usize,
    rejected_size: Option<usize>,
    allocation_failed_at: Option<usize>,
}

impl LimitedJsonBuffer {
    fn new(limit: usize) -> Self {
        Self {
            bytes: Vec::new(),
            limit,
            rejected_size: None,
            allocation_failed_at: None,
        }
    }
}

impl Write for LimitedJsonBuffer {
    fn write(&mut self, input: &[u8]) -> std::io::Result<usize> {
        let requested = self.bytes.len().checked_add(input.len()).ok_or_else(|| {
            self.rejected_size = Some(usize::MAX);
            std::io::Error::other("JSON output length overflow")
        })?;
        if requested > self.limit {
            self.rejected_size = Some(requested);
            return Err(std::io::Error::other(
                "JSON output exceeds configured limit",
            ));
        }
        self.bytes.try_reserve(input.len()).map_err(|_| {
            self.allocation_failed_at = Some(requested);
            std::io::Error::other("JSON output allocation failed")
        })?;
        self.bytes.extend_from_slice(input);
        Ok(input.len())
    }

    fn flush(&mut self) -> std::io::Result<()> {
        Ok(())
    }
}

fn serialize_json_with_byte_limit<T: Serialize>(
    value: &T,
    pretty: bool,
    limit: usize,
    operation: &'static str,
) -> Result<Vec<u8>> {
    let mut output = LimitedJsonBuffer::new(limit);
    let serialization = if pretty {
        serde_json::to_writer_pretty(&mut output, value)
    } else {
        serde_json::to_writer(&mut output, value)
    };
    if let Some(requested) = output.rejected_size {
        return Err(resource_limit(operation, requested, limit));
    }
    if let Some(requested) = output.allocation_failed_at {
        return Err(resource_limit(operation, requested, limit));
    }
    serialization.context("JSON serialization failed")?;
    Ok(output.bytes)
}

fn read_json_value_with_limits(
    path: &Path,
    limits: RunLogLimits,
) -> std::io::Result<serde_json::Value> {
    let metadata = std::fs::metadata(path)?;
    if metadata.len() > limits.max_file_bytes {
        return Err(std::io::Error::other(format!(
            "sidecar exceeds max_file_bytes ({} > {})",
            metadata.len(),
            limits.max_file_bytes
        )));
    }
    let mut file = File::open(path)?;
    let byte_limit = usize::try_from(limits.max_file_bytes).unwrap_or(usize::MAX);
    let mut output = LimitedJsonBuffer::new(byte_limit);
    let mut chunk = [0u8; 16 * 1024];
    loop {
        let read = file.read(&mut chunk)?;
        if read == 0 {
            break;
        }
        output.write_all(&chunk[..read])?;
    }
    let bytes = output.bytes;
    if bytes.len() as u128 > limits.max_file_bytes as u128 {
        return Err(std::io::Error::other("sidecar exceeds max_file_bytes"));
    }
    preflight_json_bytes(&bytes, &limits)
        .map_err(|error| std::io::Error::other(format!("sidecar JSON limit failure: {error:#}")))?;
    let value: serde_json::Value = serde_json::from_slice(&bytes)
        .map_err(|error| std::io::Error::other(format!("invalid sidecar JSON: {error}")))?;
    Ok(value)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum AtomicWritePhase {
    TempCreated,
    DataSynced,
    Renamed,
    ParentSynced,
}

static TEMP_FILE_SEQUENCE: AtomicU64 = AtomicU64::new(0);

struct TempFileCleanup {
    path: PathBuf,
    armed: bool,
}

impl Drop for TempFileCleanup {
    fn drop(&mut self) {
        if self.armed {
            let _ = std::fs::remove_file(&self.path);
        }
    }
}

fn atomic_write_bytes(path: &Path, bytes: &[u8]) -> Result<()> {
    atomic_write_bytes_with_hook(path, bytes, |_| Ok(()))
}

fn atomic_write_bytes_with_hook<F>(path: &Path, bytes: &[u8], mut hook: F) -> Result<()>
where
    F: FnMut(AtomicWritePhase) -> std::io::Result<()>,
{
    let parent = path
        .parent()
        .filter(|parent| !parent.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let file_name = path
        .file_name()
        .ok_or_else(|| anyhow::anyhow!("atomic JSON destination must have a file name"))?
        .to_string_lossy();
    let sequence = TEMP_FILE_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let temporary = parent.join(format!(
        ".{file_name}.pid-runlog-tmp-{}-{sequence}",
        std::process::id()
    ));
    let mut cleanup = TempFileCleanup {
        path: temporary.clone(),
        armed: true,
    };
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temporary)
        .with_context(|| format!("failed to create temporary file {}", temporary.display()))?;
    hook(AtomicWritePhase::TempCreated).context("atomic write interrupted after temp creation")?;
    file.write_all(bytes)
        .with_context(|| format!("failed to write temporary file {}", temporary.display()))?;
    file.flush()
        .with_context(|| format!("failed to flush temporary file {}", temporary.display()))?;
    file.sync_all()
        .with_context(|| format!("failed to fsync temporary file {}", temporary.display()))?;
    hook(AtomicWritePhase::DataSynced).context("atomic write interrupted after data sync")?;
    drop(file);
    std::fs::rename(&temporary, path).with_context(|| {
        format!(
            "failed to atomically rename {} to {}",
            temporary.display(),
            path.display()
        )
    })?;
    cleanup.armed = false;
    hook(AtomicWritePhase::Renamed).context("atomic write interrupted after rename")?;
    sync_parent_directory(parent)?;
    hook(AtomicWritePhase::ParentSynced).context("atomic write interrupted after parent sync")?;
    Ok(())
}

#[cfg(unix)]
fn sync_parent_directory(parent: &Path) -> Result<()> {
    let directory = File::open(parent)
        .with_context(|| format!("failed to open parent directory {}", parent.display()))?;
    directory
        .sync_all()
        .with_context(|| format!("failed to fsync parent directory {}", parent.display()))
}

// Windows' standard-library `File::open` cannot open directories (it does not request
// FILE_FLAG_BACKUP_SEMANTICS), and FlushFileBuffers is not a portable directory-durability
// primitive. The temporary file itself is flushed before the atomic replacement, so readers
// never observe a valid-looking truncated sidecar; a power loss immediately after replacement
// can nevertheless lose the directory entry on platforms without a supported directory fsync.
// This weaker durability boundary is explicit in the crate README and sidecar documentation.
#[cfg(not(unix))]
fn sync_parent_directory(_parent: &Path) -> Result<()> {
    Ok(())
}

fn validate_payload_hash(
    report: &mut ValidationReport,
    event_index: usize,
    payload_hash: &str,
    payload: &serde_json::Value,
    strict_schema: bool,
    limits: RunLogLimits,
) {
    match canonical_json_hashes_with_limits(payload, limits) {
        Ok(hashes) if hashes.matches_for_schema(payload_hash, strict_schema) => {}
        Ok(_) => report.error(Some(event_index), "payload_hash does not match payload"),
        Err(err) => report.error(Some(event_index), format!("payload hash failed: {err}")),
    }
}

fn validate_config_hash(
    report: &mut ValidationReport,
    event_index: usize,
    config_hash: &str,
    config: &serde_json::Value,
    strict_schema: bool,
    limits: RunLogLimits,
) -> Option<CanonicalJsonHashes> {
    match canonical_json_hashes_with_limits(config, limits) {
        Ok(hashes) => {
            if !hashes.matches_for_schema(config_hash, strict_schema) {
                report.error(Some(event_index), "config_hash does not match config");
            }
            Some(hashes)
        }
        Err(err) => {
            report.error(Some(event_index), format!("config hash failed: {err}"));
            None
        }
    }
}

fn is_sha256_hex(value: &str) -> bool {
    value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit())
}

fn validate_nonempty(field: &'static str, value: &str) -> Result<()> {
    if value.trim().is_empty() {
        anyhow::bail!("{field} must not be empty");
    }
    Ok(())
}

fn validate_artifact_location(location: &str) -> Result<()> {
    validate_nonempty("artifact URI/path", location)?;
    if location.chars().any(is_unsafe_artifact_character) {
        anyhow::bail!(
            "artifact URI/path must not contain control, format, or line-separator characters"
        );
    }
    if let Some((scheme, remainder)) = location.split_once("://") {
        let mut chars = scheme.chars();
        if !chars
            .next()
            .is_some_and(|character| character.is_ascii_alphabetic())
            || !chars.all(|character| {
                character.is_ascii_alphanumeric() || matches!(character, '+' | '-' | '.')
            })
            || remainder.trim().is_empty()
            || remainder.chars().any(char::is_whitespace)
            || remainder.contains('\\')
            || has_parent_path_segment(remainder)
        {
            anyhow::bail!("artifact URI has an invalid scheme or unsafe location");
        }
        validate_percent_encoded_uri(remainder)?;
        return Ok(());
    }
    if has_parent_path_segment(location)
        || Path::new(location)
            .components()
            .any(|component| component == Component::ParentDir)
    {
        anyhow::bail!("artifact paths must not contain parent traversal");
    }
    Ok(())
}

fn validate_percent_encoded_uri(remainder: &str) -> Result<()> {
    let bytes = remainder.as_bytes();
    let mut decoded = Vec::new();
    decoded
        .try_reserve_exact(bytes.len())
        .context("failed to allocate artifact URI percent-decoding buffer")?;
    let mut index = 0;
    let mut path_segment_start = 0usize;
    let mut in_path = true;
    while index < bytes.len() {
        let encoded = bytes[index] == b'%';
        let byte = match bytes[index] {
            delimiter @ (b'?' | b'#') if in_path => {
                if decoded[path_segment_start..] == *b".." {
                    anyhow::bail!("artifact URI must not contain encoded parent traversal");
                }
                in_path = false;
                decoded.push(delimiter);
                index += 1;
                continue;
            }
            b'/' if in_path => {
                if decoded[path_segment_start..] == *b".." {
                    anyhow::bail!("artifact URI must not contain encoded parent traversal");
                }
                decoded.push(b'/');
                path_segment_start = decoded.len();
                index += 1;
                continue;
            }
            b'%' => {
                let Some(high) = bytes.get(index + 1).and_then(|byte| hex_value(*byte)) else {
                    anyhow::bail!("artifact URI contains an invalid percent escape");
                };
                let Some(low) = bytes.get(index + 2).and_then(|byte| hex_value(*byte)) else {
                    anyhow::bail!("artifact URI contains an invalid percent escape");
                };
                index += 3;
                (high << 4) | low
            }
            byte => {
                index += 1;
                byte
            }
        };
        if in_path && encoded && (byte == b'/' || byte == b'\\') {
            anyhow::bail!("artifact URI must not contain encoded path separators");
        }
        decoded.push(byte);
    }
    if in_path && decoded[path_segment_start..] == *b".." {
        anyhow::bail!("artifact URI must not contain encoded parent traversal");
    }
    let decoded = std::str::from_utf8(&decoded)
        .context("artifact URI percent-decoding produced invalid UTF-8")?;
    if decoded
        .chars()
        .any(|character| is_unsafe_artifact_character(character) || character.is_whitespace())
    {
        anyhow::bail!(
            "artifact URI must not contain encoded control, format, or whitespace characters"
        );
    }
    Ok(())
}

fn is_unsafe_artifact_character(character: char) -> bool {
    character.is_control()
        || matches!(
            character,
            '\u{AD}'
                | '\u{600}'..='\u{605}'
                | '\u{61C}'
                | '\u{6DD}'
                | '\u{70F}'
                | '\u{890}'..='\u{891}'
                | '\u{8E2}'
                | '\u{180E}'
                | '\u{200B}'..='\u{200F}'
                | '\u{2028}'..='\u{202E}'
                | '\u{2060}'..='\u{206F}'
                | '\u{FEFF}'
                | '\u{FFF9}'..='\u{FFFB}'
                | '\u{110BD}'
                | '\u{110CD}'
                | '\u{13430}'..='\u{1343F}'
                | '\u{1BCA0}'..='\u{1BCA3}'
                | '\u{1D173}'..='\u{1D17A}'
                | '\u{E0001}'
                | '\u{E0020}'..='\u{E007F}'
        )
}

fn hex_value(byte: u8) -> Option<u8> {
    match byte {
        b'0'..=b'9' => Some(byte - b'0'),
        b'a'..=b'f' => Some(byte - b'a' + 10),
        b'A'..=b'F' => Some(byte - b'A' + 10),
        _ => None,
    }
}

fn has_parent_path_segment(location: &str) -> bool {
    location
        .split(['/', '\\'])
        .any(|component| component == "..")
}

fn validate_pid_metric_report(
    validation: &mut ValidationReport,
    event_index: usize,
    report: &PidMetricReport,
) {
    for (field, value) in [
        ("PID metric name", report.name.as_str()),
        ("estimator family", report.estimator.family.as_str()),
        (
            "definition revision",
            report.estimator.definition_revision.as_str(),
        ),
        (
            "estimator revision",
            report.estimator.estimator_revision.as_str(),
        ),
        (
            "support contract",
            report.provenance.support_contract.as_str(),
        ),
        ("metric", report.provenance.metric.as_str()),
    ] {
        if value.trim().is_empty() {
            validation.error(Some(event_index), format!("{field} must not be empty"));
        }
    }
    if !report.value_nats.is_finite() {
        validation.error(Some(event_index), "PID metric value must be finite");
    }
    if report.provenance.split_ids.is_empty()
        || report
            .provenance
            .split_ids
            .iter()
            .any(|split| split.trim().is_empty())
    {
        validation.error(
            Some(event_index),
            "PID metric split_ids must contain nonempty identifiers",
        );
    }
    if report
        .provenance
        .warnings
        .iter()
        .any(|warning| warning.trim().is_empty())
    {
        validation.error(
            Some(event_index),
            "PID metric warnings must not contain empty strings",
        );
    }
    if report.provenance.diagnostics.is_null() {
        validation.error(
            Some(event_index),
            "PID metric diagnostics must be an explicit non-null value",
        );
    }
    for (field, identity) in [
        ("PID metric data_hash", &report.provenance.data_hash),
        (
            "PID metric preprocessing_hash",
            &report.provenance.preprocessing_hash,
        ),
    ] {
        if identity.validate().is_err() {
            validation.error(
                Some(event_index),
                format!("{field} must contain a valid SHA-256 digest"),
            );
        }
    }
}

fn validate_pose(report: &mut ValidationReport, event_index: usize, pose: &Pose) {
    validate_vec3(report, event_index, pose.position, "pose position");
    for value in pose.orientation_xyzw {
        if !value.is_finite() {
            report.error(Some(event_index), "pose orientation must be finite");
        }
    }
}

fn validate_embedding_contract(
    report: &mut ValidationReport,
    event_index: usize,
    name: &str,
    variables: &[EmbeddingVariableContract],
) {
    if name.is_empty() {
        report.error(
            Some(event_index),
            "embedding contract name must not be empty",
        );
    }
    if variables.is_empty() {
        report.error(
            Some(event_index),
            "embedding contract must include at least one variable",
        );
    }
    let mut seen = BTreeSet::new();
    for variable in variables {
        if variable.variable.is_empty() {
            report.error(
                Some(event_index),
                "embedding contract variable name must not be empty",
            );
        } else if !seen.insert(variable.variable.clone()) {
            report.error(
                Some(event_index),
                format!(
                    "duplicate embedding contract variable {}",
                    variable.variable
                ),
            );
        }
        if variable.source.is_empty() {
            report.error(
                Some(event_index),
                "embedding contract source must not be empty",
            );
        }
        if variable.dims.is_empty() || variable.dims.contains(&0) {
            report.error(
                Some(event_index),
                "embedding contract dims must be nonempty and positive",
            );
        }
    }
}

fn validate_vec3(report: &mut ValidationReport, event_index: usize, value: [f64; 3], field: &str) {
    if value.iter().any(|v| !v.is_finite()) {
        report.error(Some(event_index), format!("{field} must be finite"));
    }
}

fn sidecar_path(path: &Path, suffix: &str) -> PathBuf {
    let mut file_name = path
        .file_name()
        .unwrap_or_else(|| OsStr::new("runlog"))
        .to_os_string();
    file_name.push(format!(".{suffix}.json"));
    path.with_file_name(file_name)
}

pub struct RunLogWriter<W> {
    writer: W,
    appended_bytes: u64,
    appended_events: usize,
    failed: bool,
}

impl RunLogWriter<BufWriter<File>> {
    pub fn create(path: impl AsRef<Path>) -> Result<Self> {
        let file = File::create(path.as_ref())
            .with_context(|| format!("failed to create run log {}", path.as_ref().display()))?;
        Ok(Self::new(BufWriter::new(file)))
    }

    /// Flush the in-memory buffer to the OS **and** fsync the underlying file so already-written
    /// events survive a crash/power loss. Use this for crash-safe live logging: call it after the
    /// events you must not lose (e.g. each `RunStarted`/checkpoint), accepting the I/O cost.
    ///
    /// `flush` alone only hands bytes to the kernel page cache; it does not guarantee they reach
    /// stable storage. `sync_all` flushes file *contents and metadata* (length) durably.
    pub fn sync_all(&mut self) -> Result<()> {
        self.writer
            .flush()
            .context("failed to flush run log before fsync")?;
        self.writer
            .get_ref()
            .sync_all()
            .context("failed to fsync run log to durable storage")?;
        Ok(())
    }

    /// Alias for [`RunLogWriter::sync_all`]: flush the buffer and fsync to durable storage.
    pub fn flush_durable(&mut self) -> Result<()> {
        self.sync_all()
    }
}

impl<W: Write> RunLogWriter<W> {
    pub fn new(writer: W) -> Self {
        Self {
            writer,
            appended_bytes: 0,
            appended_events: 0,
            failed: false,
        }
    }

    /// Append one event as a JSON line, guaranteeing the line can be read back.
    ///
    /// `serde_json` silently serializes non-finite `f64` (NaN/±inf) as `null`, which
    /// [`read_events`] can never parse back into the typed event — without this guard the
    /// corruption would only surface at replay/validate time, after the run is over. `append`
    /// therefore validates the typed value before serialization, then re-parses the exact line it
    /// is about to write. Callers must pre-filter or explicitly encode non-finite values.
    pub fn append(&mut self, event: &RunLogEvent) -> Result<()> {
        self.append_with_limits(event, RunLogLimits::default())
    }

    /// Append one event while enforcing all configured budgets.
    ///
    /// Event and file-byte totals cover data appended through this writer instance. A generic
    /// `writer` supplied to [`RunLogWriter::new`] may already contain bytes which this wrapper
    /// cannot discover; callers appending to pre-populated storage must account for that content
    /// separately. An underlying write error poisons the wrapper because a generic [`Write`]
    /// implementation cannot report how many bytes it committed before failing; later appends are
    /// rejected so retries cannot bypass aggregate accounting.
    pub fn append_with_limits(&mut self, event: &RunLogEvent, limits: RunLogLimits) -> Result<()> {
        if self.failed {
            anyhow::bail!("run-log writer is unusable after a previous I/O failure");
        }
        let limits = limits.validate()?;
        let next_events = self.appended_events.checked_add(1).ok_or_else(|| {
            resource_limit("run-log output event count", u128::MAX, limits.max_events)
        })?;
        if next_events > limits.max_events {
            return Err(resource_limit(
                "run-log output event count",
                next_events,
                limits.max_events,
            ));
        }
        let line = serialize_json_with_byte_limit(
            event,
            false,
            serialized_json_line_limit(limits),
            "run-log output line bytes",
        )?;
        let line_bytes = u64::try_from(line.len())
            .ok()
            .and_then(|line_bytes| line_bytes.checked_add(1))
            .ok_or_else(|| {
                resource_limit(
                    "run-log output file bytes",
                    u128::MAX,
                    limits.max_file_bytes,
                )
            })?;
        let next_bytes = self.appended_bytes.checked_add(line_bytes).ok_or_else(|| {
            resource_limit(
                "run-log output file bytes",
                u128::MAX,
                limits.max_file_bytes,
            )
        })?;
        if next_bytes > limits.max_file_bytes {
            return Err(resource_limit(
                "run-log output file bytes",
                next_bytes,
                limits.max_file_bytes,
            ));
        }
        validate_finite_json(event).context("refusing to append non-finite run-log event")?;
        preflight_json_bytes(&line, &limits)?;
        serde_json::from_slice::<RunLogEvent>(&line)
            .context("refusing to append a run-log event that cannot be read back")?;
        if let Err(error) = self.writer.write_all(&line) {
            self.failed = true;
            return Err(error).context("failed to write run-log event");
        }
        if let Err(error) = self.writer.write_all(b"\n") {
            self.failed = true;
            return Err(error).context("failed to write run-log newline");
        }
        self.appended_bytes = next_bytes;
        self.appended_events = next_events;
        Ok(())
    }

    pub fn flush(&mut self) -> Result<()> {
        self.writer.flush().context("failed to flush run log")
    }

    pub fn into_inner(self) -> W {
        self.writer
    }
}

/// Bounded streaming JSONL parser. It never allocates more than one configured line plus one
/// decoded event at a time.
pub struct RunLogEventStream<R> {
    reader: R,
    limits: RunLogLimits,
    line: Vec<u8>,
    total_bytes: u64,
    event_count: usize,
    line_number: usize,
    finished: bool,
}

impl<R: BufRead> RunLogEventStream<R> {
    pub fn new(reader: R, limits: RunLogLimits) -> Result<Self> {
        Ok(Self {
            reader,
            limits: limits.validate()?,
            line: Vec::new(),
            total_bytes: 0,
            event_count: 0,
            line_number: 0,
            finished: false,
        })
    }

    fn next_event(&mut self) -> Result<Option<RunLogEvent>> {
        loop {
            self.line.clear();
            let mut saw_bytes = false;
            loop {
                let (consumed, has_newline) = {
                    let available = self.reader.fill_buf().with_context(|| {
                        format!("failed to read run-log line {}", self.line_number + 1)
                    })?;
                    if available.is_empty() {
                        (0, false)
                    } else if let Some(position) = available.iter().position(|byte| *byte == b'\n')
                    {
                        let consumed = position + 1;
                        let requested = self.line.len().saturating_add(position);
                        if requested > self.limits.max_line_bytes {
                            return Err(resource_limit(
                                "run-log line bytes",
                                requested,
                                self.limits.max_line_bytes,
                            ));
                        }
                        self.line.try_reserve(position).map_err(|_| {
                            resource_limit(
                                "run-log line allocation",
                                requested,
                                self.limits.max_line_bytes,
                            )
                        })?;
                        self.line.extend_from_slice(&available[..position]);
                        (consumed, true)
                    } else {
                        let requested = self.line.len().saturating_add(available.len());
                        if requested > self.limits.max_line_bytes {
                            return Err(resource_limit(
                                "run-log line bytes",
                                requested,
                                self.limits.max_line_bytes,
                            ));
                        }
                        self.line.try_reserve(available.len()).map_err(|_| {
                            resource_limit(
                                "run-log line allocation",
                                requested,
                                self.limits.max_line_bytes,
                            )
                        })?;
                        self.line.extend_from_slice(available);
                        (available.len(), false)
                    }
                };

                if consumed == 0 {
                    break;
                }
                saw_bytes = true;
                let next_total =
                    self.total_bytes
                        .checked_add(consumed as u64)
                        .ok_or_else(|| {
                            resource_limit(
                                "run-log file bytes",
                                u128::MAX,
                                self.limits.max_file_bytes,
                            )
                        })?;
                if next_total > self.limits.max_file_bytes {
                    return Err(resource_limit(
                        "run-log file bytes",
                        next_total,
                        self.limits.max_file_bytes,
                    ));
                }
                self.total_bytes = next_total;
                self.reader.consume(consumed);
                if has_newline {
                    break;
                }
            }

            if !saw_bytes && self.line.is_empty() {
                self.finished = true;
                return Ok(None);
            }
            self.line_number = self.line_number.saturating_add(1);
            if self.line.last() == Some(&b'\r') {
                self.line.pop();
            }
            if self.line.iter().all(u8::is_ascii_whitespace) {
                continue;
            }
            let next_event_count = self.event_count.saturating_add(1);
            if next_event_count > self.limits.max_events {
                return Err(resource_limit(
                    "run-log event count",
                    next_event_count,
                    self.limits.max_events,
                ));
            }
            preflight_json_bytes(&self.line, &self.limits).with_context(|| {
                format!(
                    "run-log line {} violates JSON resource limits",
                    self.line_number
                )
            })?;
            let event = serde_json::from_slice(&self.line)
                .with_context(|| format!("invalid run-log event at line {}", self.line_number))?;
            self.event_count = next_event_count;
            return Ok(Some(event));
        }
    }
}

impl<R: BufRead> Iterator for RunLogEventStream<R> {
    type Item = Result<RunLogEvent>;

    fn next(&mut self) -> Option<Self::Item> {
        if self.finished {
            return None;
        }
        match self.next_event() {
            Ok(Some(event)) => Some(Ok(event)),
            Ok(None) => None,
            Err(error) => {
                self.finished = true;
                Some(Err(error))
            }
        }
    }
}

fn preflight_json_bytes(bytes: &[u8], limits: &RunLogLimits) -> Result<()> {
    #[derive(Clone, Copy)]
    struct ContainerFrame {
        kind: u8,
        separators: usize,
        has_content: bool,
    }

    let stack_capacity = limits.max_nesting_depth.min(bytes.len());
    let mut stack: Vec<ContainerFrame> = Vec::new();
    stack.try_reserve_exact(stack_capacity).map_err(|_| {
        resource_limit(
            "JSON nesting allocation",
            stack_capacity,
            limits.max_nesting_depth,
        )
    })?;
    let mut in_string = false;
    let mut escaped = false;
    let mut string_bytes = 0usize;
    for &byte in bytes {
        if in_string {
            if escaped {
                escaped = false;
                string_bytes = string_bytes.saturating_add(1);
            } else if byte == b'\\' {
                escaped = true;
                string_bytes = string_bytes.saturating_add(1);
            } else if byte == b'"' {
                in_string = false;
            } else {
                string_bytes = string_bytes.saturating_add(1);
            }
            if string_bytes > limits.max_string_bytes {
                return Err(resource_limit(
                    "JSON string bytes",
                    string_bytes,
                    limits.max_string_bytes,
                ));
            }
            continue;
        }
        match byte {
            b'"' => {
                if let Some(frame) = stack.last_mut() {
                    frame.has_content = true;
                }
                in_string = true;
                string_bytes = 0;
            }
            b'{' | b'[' => {
                if let Some(frame) = stack.last_mut() {
                    frame.has_content = true;
                }
                let depth = stack.len().checked_add(1).ok_or_else(|| {
                    resource_limit("JSON nesting depth", usize::MAX, limits.max_nesting_depth)
                })?;
                if depth > limits.max_nesting_depth {
                    return Err(resource_limit(
                        "JSON nesting depth",
                        depth,
                        limits.max_nesting_depth,
                    ));
                }
                stack.push(ContainerFrame {
                    kind: byte,
                    separators: 0,
                    has_content: false,
                });
            }
            b',' => {
                if let Some(frame) = stack.last_mut() {
                    frame.separators = frame.separators.checked_add(1).ok_or_else(|| {
                        resource_limit("JSON container length", usize::MAX, limits.max_array_len)
                    })?;
                }
            }
            b'}' | b']' => {
                if let Some(frame) = stack.pop() {
                    let entries = if frame.has_content {
                        frame.separators.checked_add(1).ok_or_else(|| {
                            resource_limit(
                                "JSON container length",
                                usize::MAX,
                                limits.max_array_len,
                            )
                        })?
                    } else {
                        0
                    };
                    let (operation, limit) = if frame.kind == b'[' {
                        ("JSON array length", limits.max_array_len)
                    } else {
                        ("JSON object entries", limits.max_object_entries)
                    };
                    if entries > limit {
                        return Err(resource_limit(operation, entries, limit));
                    }
                }
            }
            byte if !byte.is_ascii_whitespace() => {
                if let Some(frame) = stack.last_mut() {
                    frame.has_content = true;
                }
            }
            _ => {}
        }
    }
    Ok(())
}

struct TraceHashAccumulator {
    limits: RunLogLimits,
    replay_legacy: Option<Sha256>,
    replay_lossless: Sha256,
    logical_legacy: Option<Sha256>,
    logical_top_level_legacy: Option<Sha256>,
    logical_lossless: Sha256,
}

struct HashingReader<R> {
    inner: R,
    hasher: Sha256,
}

impl<R> HashingReader<R> {
    fn new(inner: R) -> Self {
        Self {
            inner,
            hasher: Sha256::new(),
        }
    }

    fn finish(self) -> String {
        to_hex(&self.hasher.finalize())
    }

    fn get_ref(&self) -> &R {
        &self.inner
    }
}

impl<R: Read> Read for HashingReader<R> {
    fn read(&mut self, buffer: &mut [u8]) -> std::io::Result<usize> {
        let bytes_read = self.inner.read(buffer)?;
        self.hasher.update(&buffer[..bytes_read]);
        Ok(bytes_read)
    }
}

impl TraceHashAccumulator {
    fn new(limits: RunLogLimits) -> Self {
        Self {
            limits,
            replay_legacy: Some(Sha256::new()),
            replay_lossless: Sha256::new(),
            logical_legacy: Some(Sha256::new()),
            logical_top_level_legacy: Some(Sha256::new()),
            logical_lossless: Sha256::new(),
        }
    }

    fn update(&mut self, event: &RunLogEvent) -> Result<()> {
        let bytes = validated_json_bytes_with_limits(event, self.limits)
            .context("failed to serialize event for lossless replay trace hash")?;
        update_length_prefixed(&mut self.replay_lossless, &bytes);

        if let Some(hasher) = &mut self.replay_legacy {
            match legacy_number_event(event)
                .and_then(|event| validated_json_bytes_with_limits(&event, self.limits))
            {
                Ok(bytes) => update_length_prefixed(hasher, &bytes),
                Err(_) => self.replay_legacy = None,
            }
        }
        update_logical_hasher(
            &mut self.logical_lossless,
            event,
            strip_top_level_wall_clock,
            true,
            false,
            self.limits,
        )?;
        if let Some(hasher) = &mut self.logical_legacy {
            if update_logical_hasher(
                hasher,
                event,
                strip_wall_clock_v1_recursive,
                false,
                true,
                self.limits,
            )
            .is_err()
            {
                self.logical_legacy = None;
            }
        }
        if let Some(hasher) = &mut self.logical_top_level_legacy {
            if update_logical_hasher(
                hasher,
                event,
                strip_top_level_wall_clock,
                true,
                true,
                self.limits,
            )
            .is_err()
            {
                self.logical_top_level_legacy = None;
            }
        }
        Ok(())
    }

    fn finish(self) -> Result<RunLogHashIdentities> {
        Ok(RunLogHashIdentities {
            replay_lossless: HashIdentity::sha256(
                HashRevision::ReplayTraceV2,
                to_hex(&self.replay_lossless.finalize()),
            )?,
            logical_lossless: HashIdentity::sha256(
                HashRevision::LogicalTraceV3,
                to_hex(&self.logical_lossless.finalize()),
            )?,
            replay_legacy: self
                .replay_legacy
                .map(|hasher| {
                    HashIdentity::sha256(HashRevision::ReplayTraceV1, to_hex(&hasher.finalize()))
                })
                .transpose()?,
            logical_legacy: self
                .logical_legacy
                .map(|hasher| {
                    HashIdentity::sha256(HashRevision::LogicalTraceV1, to_hex(&hasher.finalize()))
                })
                .transpose()?,
            logical_top_level_clock_legacy: self
                .logical_top_level_legacy
                .map(|hasher| {
                    HashIdentity::sha256(HashRevision::LogicalTraceV2, to_hex(&hasher.finalize()))
                })
                .transpose()?,
        })
    }
}

fn update_length_prefixed(hasher: &mut Sha256, bytes: &[u8]) {
    hasher.update((bytes.len() as u64).to_le_bytes());
    hasher.update(bytes);
}

fn update_logical_hasher(
    hasher: &mut Sha256,
    event: &RunLogEvent,
    strip_clock: fn(&mut serde_json::Value),
    canonicalize_keys: bool,
    legacy_numbers: bool,
    limits: RunLogLimits,
) -> Result<()> {
    if legacy_numbers && matches!(event, RunLogEvent::PidEstimate { .. }) {
        anyhow::bail!("schema-2 pid_estimate has no schema-1 logical representation");
    }
    let mut value = validated_json_value_with_limits(event, limits)?;
    if legacy_numbers {
        coerce_legacy_numbers(&mut value)?;
    }
    strip_clock(&mut value);
    if canonicalize_keys {
        canonicalize_object_keys(&mut value)?;
    }
    let bytes = serialize_canonical_json_with_limits(&value, limits)?;
    update_length_prefixed(hasher, &bytes);
    Ok(())
}

/// Result of one bounded streaming pass over a run log.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct RunLogInspection {
    pub validation: ValidationReport,
    pub replay_state: ReplayState,
    pub hash_identities: RunLogHashIdentities,
}

/// A streaming inspection whose lifecycle, causality, hashes, and typed fields all validated.
#[derive(Debug, Clone, PartialEq)]
pub struct ValidatedRunLog {
    inspection: RunLogInspection,
}

impl ValidatedRunLog {
    pub fn inspection(&self) -> &RunLogInspection {
        &self.inspection
    }

    pub fn replay_state(&self) -> &ReplayState {
        &self.inspection.replay_state
    }

    pub fn hash_identities(&self) -> &RunLogHashIdentities {
        &self.inspection.hash_identities
    }
}

pub fn inspect_event_stream<R: BufRead>(
    mut reader: R,
    limits: RunLogLimits,
) -> Result<RunLogInspection> {
    inspect_event_stream_inner(&mut reader, limits)
}

fn inspect_event_stream_inner<R: BufRead>(
    reader: &mut R,
    limits: RunLogLimits,
) -> Result<RunLogInspection> {
    let limits = limits.validate()?;
    let mut validation = StreamingValidationState::new(limits);
    let mut replay_state = ReplayState::default();
    let mut hashes = TraceHashAccumulator::new(limits);
    for event in RunLogEventStream::new(reader, limits)? {
        let event = event?;
        validation.push(&event);
        replay_state.apply_with_limits(&event, limits)?;
        hashes.update(&event)?;
    }
    Ok(RunLogInspection {
        validation: validation.finish(),
        replay_state,
        hash_identities: hashes.finish()?,
    })
}

#[derive(Debug)]
struct HashedRunLogInspection {
    inspection: RunLogInspection,
    file_sha256: String,
}

fn open_bounded_run_log(path: &Path, limits: RunLogLimits) -> Result<File> {
    let file =
        File::open(path).with_context(|| format!("failed to open run log {}", path.display()))?;
    let metadata = file
        .metadata()
        .with_context(|| format!("failed to inspect run log {}", path.display()))?;
    if metadata.len() > limits.max_file_bytes {
        return Err(resource_limit(
            "run-log file bytes",
            metadata.len(),
            limits.max_file_bytes,
        ));
    }
    Ok(file)
}

fn inspect_path_with_hash(path: &Path, limits: RunLogLimits) -> Result<HashedRunLogInspection> {
    inspect_path_with_hash_and_hook(path, limits, || Ok(()))
}

fn inspect_path_with_hash_and_hook<F>(
    path: &Path,
    limits: RunLogLimits,
    after_read: F,
) -> Result<HashedRunLogInspection>
where
    F: FnOnce() -> Result<()>,
{
    let limits = limits.validate()?;
    let file = open_bounded_run_log(path, limits)?;
    let initial_metadata = file
        .metadata()
        .with_context(|| format!("failed to inspect opened run log {}", path.display()))?;
    let initial_modified = initial_metadata.modified().ok();
    let opened_identity = same_file::Handle::from_file(
        file.try_clone()
            .with_context(|| format!("failed to clone opened run log {}", path.display()))?,
    )
    .with_context(|| format!("failed to identify opened run log {}", path.display()))?;
    let mut reader = BufReader::new(HashingReader::new(file));
    let inspection = inspect_event_stream_inner(&mut reader, limits)?;
    after_read()?;
    let hashing_reader = reader.into_inner();
    let final_metadata = hashing_reader
        .get_ref()
        .metadata()
        .with_context(|| format!("failed to re-inspect opened run log {}", path.display()))?;
    let metadata_changed = initial_metadata.len() != final_metadata.len()
        || initial_modified
            .zip(final_metadata.modified().ok())
            .is_some_and(|(initial, final_value)| initial != final_value);
    let current_identity = same_file::Handle::from_path(path).map_err(|error| {
        anyhow::Error::new(RunLogError::SourceChangedDuringInspection).context(format!(
            "failed to re-identify run-log path {}: {error}",
            path.display()
        ))
    })?;
    if metadata_changed || opened_identity != current_identity {
        return Err(anyhow::Error::new(
            RunLogError::SourceChangedDuringInspection,
        ));
    }
    let file_sha256 = hashing_reader.finish();
    Ok(HashedRunLogInspection {
        inspection,
        file_sha256,
    })
}

pub fn inspect_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<RunLogInspection> {
    let path = path.as_ref();
    let limits = limits.validate()?;
    let file = open_bounded_run_log(path, limits)?;
    inspect_event_stream(BufReader::new(file), limits)
}

pub fn inspect_path(path: impl AsRef<Path>) -> Result<RunLogInspection> {
    inspect_path_with_limits(path, RunLogLimits::default())
}

pub fn read_validated_runlog_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<ValidatedRunLog> {
    let inspection = inspect_path_with_limits(path, limits)?;
    if !inspection.validation.is_valid() {
        return Err(anyhow::Error::new(RunLogError::ValidationFailed {
            errors: inspection.validation.errors,
        }));
    }
    Ok(ValidatedRunLog { inspection })
}

pub fn read_validated_runlog_from_path(path: impl AsRef<Path>) -> Result<ValidatedRunLog> {
    read_validated_runlog_from_path_with_limits(path, RunLogLimits::default())
}

/// Result of explicitly rewriting a supported legacy stream to the current schema declaration.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct SchemaMigrationReport {
    pub from_schema: u32,
    pub to_schema: u32,
    pub events: usize,
    pub legacy_pid_metric_events: usize,
    pub warnings: Vec<String>,
}

/// Rewrite a schema-1/2 log to a new writer with current schema and content-hash revisions.
///
/// Legacy scalar `pid_metric` events are preserved rather than inventing provenance which was not
/// recorded. The report makes that limitation explicit; callers can then attach external evidence
/// or keep the migrated log out of publication-facing workflows. Migration reads one bounded event
/// at a time. It retains only the bounded prefix through the first `config_logged` event so the
/// earlier `run_started.config_hash` can be re-anchored to canonical JSON v2.
/// A legacy stream without exactly one pre-operational `config_logged` event cannot be upgraded
/// without inventing configuration evidence, so migration rejects it.
/// The supplied limits also govern every content hash and the aggregate migrated output written
/// through this function. The destination is a generic forward-only writer, so an error discovered
/// after writing begins may leave a valid prefix behind. A caller publishing to a path must stage
/// the output and atomically install it only after this function succeeds.
pub fn migrate_runlog<R: BufRead, W: Write>(
    reader: R,
    writer: W,
    limits: RunLogLimits,
) -> Result<SchemaMigrationReport> {
    let limits = limits.validate()?;
    let mut output = RunLogWriter::new(writer);
    let mut from_schema = None;
    let mut events = 0usize;
    let mut legacy_pid_metric_events = 0usize;
    let mut pending_prefix = Vec::new();
    let mut config_anchor_resolved = false;
    let mut config_logged_events = 0usize;
    for event in RunLogEventStream::new(reader, limits)? {
        let mut event = event?;
        if events == 0 && !matches!(&event, RunLogEvent::RunStarted { .. }) {
            anyhow::bail!("cannot migrate a log whose first event is not run_started");
        }
        if let RunLogEvent::RunStarted { schema_version, .. } = &mut event {
            if from_schema.is_some() {
                anyhow::bail!("cannot migrate a log with multiple run_started events");
            }
            from_schema = Some(*schema_version);
            if !(MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION..=RUN_LOG_SCHEMA_VERSION)
                .contains(schema_version)
            {
                anyhow::bail!("cannot migrate unsupported run-log schema {schema_version}");
            }
            *schema_version = RUN_LOG_SCHEMA_VERSION;
        }
        if matches!(event, RunLogEvent::ConfigLogged { .. }) {
            config_logged_events = config_logged_events.saturating_add(1);
            if config_logged_events > 1 {
                anyhow::bail!(
                    "cannot migrate a log with more than one config_logged event to schema 2"
                );
            }
        }
        if matches!(event, RunLogEvent::PidMetric { .. }) {
            legacy_pid_metric_events = legacy_pid_metric_events.saturating_add(1);
        }
        let config_anchor = rewrite_schema_two_content_hashes(&mut event, limits)?;
        if config_anchor_resolved {
            output.append_with_limits(&event, limits)?;
        } else {
            pending_prefix.try_reserve(1).map_err(|_| {
                resource_limit(
                    "schema migration prefix events",
                    pending_prefix.len().saturating_add(1),
                    limits.max_events,
                )
            })?;
            pending_prefix.push(event);
            if let Some(config_anchor) = config_anchor {
                if pending_prefix.len() != 2 {
                    anyhow::bail!(
                        "cannot migrate a log whose config_logged event does not immediately follow run_started"
                    );
                }
                if let Some(RunLogEvent::RunStarted { config_hash, .. }) = pending_prefix
                    .iter_mut()
                    .find(|event| matches!(event, RunLogEvent::RunStarted { .. }))
                {
                    *config_hash = config_anchor;
                }
                append_migration_events(&mut output, pending_prefix.drain(..), limits)?;
                config_anchor_resolved = true;
            }
        }
        events = events.saturating_add(1);
    }
    let from_schema = from_schema.context("cannot migrate a log without run_started")?;
    if !config_anchor_resolved {
        anyhow::bail!(
            "cannot migrate a log without exactly one config_logged event immediately after run_started"
        );
    }
    debug_assert!(pending_prefix.is_empty());
    output.flush()?;
    let mut warnings = Vec::new();
    if legacy_pid_metric_events != 0 {
        warnings.push(format!(
            "preserved {legacy_pid_metric_events} legacy pid_metric event(s) without inventing typed estimator provenance"
        ));
    }
    Ok(SchemaMigrationReport {
        from_schema,
        to_schema: RUN_LOG_SCHEMA_VERSION,
        events,
        legacy_pid_metric_events,
        warnings,
    })
}

fn rewrite_schema_two_content_hashes(
    event: &mut RunLogEvent,
    limits: RunLogLimits,
) -> Result<Option<String>> {
    match event {
        RunLogEvent::ConfigLogged {
            config_hash,
            config,
            ..
        } => {
            let lossless = canonical_json_hash_v2_with_limits(config, limits)?;
            *config_hash = lossless.clone();
            Ok(Some(lossless))
        }
        RunLogEvent::BridgeRequest {
            payload_hash,
            payload,
            ..
        }
        | RunLogEvent::ActionApplied {
            payload_hash,
            payload,
            ..
        }
        | RunLogEvent::InterventionApplied {
            payload_hash,
            payload,
            ..
        } => {
            *payload_hash = canonical_json_hash_v2_with_limits(payload, limits)?;
            Ok(None)
        }
        _ => Ok(None),
    }
}

fn append_migration_events<W: Write>(
    output: &mut RunLogWriter<W>,
    events: impl Iterator<Item = RunLogEvent>,
    limits: RunLogLimits,
) -> Result<()> {
    for event in events {
        output.append_with_limits(&event, limits)?;
    }
    Ok(())
}

pub fn read_events_from_path(path: impl AsRef<Path>) -> Result<Vec<RunLogEvent>> {
    read_events_from_path_with_limits(path, RunLogLimits::default())
}

pub fn read_events_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<Vec<RunLogEvent>> {
    let path = path.as_ref();
    let limits = limits.validate()?;
    let metadata = std::fs::metadata(path)
        .with_context(|| format!("failed to stat run log {}", path.display()))?;
    if metadata.len() > limits.max_file_bytes {
        return Err(resource_limit(
            "run-log file bytes",
            metadata.len(),
            limits.max_file_bytes,
        ));
    }
    let file =
        File::open(path).with_context(|| format!("failed to open run log {}", path.display()))?;
    read_events_with_limits(BufReader::new(file), limits)
}

pub fn replay_state_from_path(path: impl AsRef<Path>) -> Result<ReplayState> {
    replay_state_from_path_with_limits(path, RunLogLimits::default())
}

pub fn replay_state_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<ReplayState> {
    Ok(inspect_path_with_limits(path, limits)?.replay_state)
}

pub fn replay_trace_hash_from_path(path: impl AsRef<Path>) -> Result<String> {
    replay_trace_hash_from_path_with_limits(path, RunLogLimits::default())
}

pub fn replay_trace_hash_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<String> {
    let hashes = inspect_path_with_limits(path, limits)?.hash_identities;
    hashes
        .replay_legacy
        .map(|identity| identity.digest)
        .context("run log contains numbers unsupported by replay trace hash v1")
}

/// Lossless replay-trace hash for logs whose generic JSON payloads may contain integers outside
/// the legacy serde_json `i64`/`u64` range.
///
/// Unlike [`replay_trace_hash`], this v2 digest preserves arbitrary-precision JSON number text.
/// Use it for explicit lossless comparisons. Current summary and manifest sidecars expose the
/// result as `trace_hash_v2`; the unversioned helper retains the released schema-1 coercion.
pub fn replay_trace_hash_v2_from_path(path: impl AsRef<Path>) -> Result<String> {
    replay_trace_hash_v2_from_path_with_limits(path, RunLogLimits::default())
}

pub fn replay_trace_hash_v2_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<String> {
    Ok(inspect_path_with_limits(path, limits)?
        .hash_identities
        .replay_lossless
        .digest)
}

pub fn read_events<R: BufRead>(reader: R) -> Result<Vec<RunLogEvent>> {
    read_events_with_limits(reader, RunLogLimits::default())
}

pub fn read_events_with_limits<R: BufRead>(
    reader: R,
    limits: RunLogLimits,
) -> Result<Vec<RunLogEvent>> {
    let mut events = Vec::new();
    for event in RunLogEventStream::new(reader, limits)? {
        let event = event?;
        events.try_reserve(1).map_err(|_| {
            resource_limit(
                "run-log event allocation",
                events.len() + 1,
                limits.max_events,
            )
        })?;
        events.push(event);
    }
    Ok(events)
}

pub fn replay_events(events: &[RunLogEvent]) -> Result<ReplayState> {
    replay_events_with_limits(events, RunLogLimits::default())
}

/// Replay an already-decoded event slice under an explicit aggregate budget.
pub fn replay_events_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<ReplayState> {
    let limits = limits.validate()?;
    let mut state = ReplayState::default();
    for event in events {
        state.apply_with_limits(event, limits)?;
    }
    Ok(state)
}

fn preflight_event_slice(events: &[RunLogEvent], limits: RunLogLimits) -> Result<()> {
    let limits = limits.validate()?;
    if events.len() > limits.max_events {
        return Err(resource_limit(
            "in-memory event count",
            events.len(),
            limits.max_events,
        ));
    }
    let mut total_bytes = 0u64;
    for event in events {
        // Validation must retain semantic diagnostics for non-finite typed fields rather than
        // fail before `StreamingValidationState` can record them. serde_json's temporary `null`
        // representation is used only for resource sizing; write/hash/replay paths still reject
        // non-finite values.
        let byte_limit = serialized_json_line_limit(limits);
        let bytes = serialize_json_with_byte_limit(
            event,
            false,
            byte_limit,
            "in-memory validation event line bytes",
        )?;
        preflight_json_bytes(&bytes, &limits)?;
        let event_bytes = u64::try_from(bytes.len())
            .ok()
            .and_then(|event_bytes| event_bytes.checked_add(1))
            .ok_or_else(|| {
                resource_limit("in-memory event bytes", u128::MAX, limits.max_file_bytes)
            })?;
        total_bytes = total_bytes.checked_add(event_bytes).ok_or_else(|| {
            resource_limit("in-memory event bytes", u128::MAX, limits.max_file_bytes)
        })?;
        if total_bytes > limits.max_file_bytes {
            return Err(resource_limit(
                "in-memory event bytes",
                total_bytes,
                limits.max_file_bytes,
            ));
        }
    }
    Ok(())
}

/// Order-sensitive schema-1 content hash over the **full recorded** event sequence.
///
/// Each event's schema-defined serde JSON representation is length-prefixed before folding into
/// SHA-256, so record boundaries are unambiguous. This deliberately preserves the released byte
/// algorithm used by existing replay-hash sidecars, including serde_json's former conversion of
/// out-of-range payload integers and all decimal/exponent literals through `f64`. Generic key
/// sorting belongs to [`canonical_json_hash`], not this compatibility-sensitive trace digest.
/// Prefer [`replay_trace_hash_v2`] for lossless new hashes. Unlike a hash of the collapsed
/// [`ReplayState`], this covers intermediate records that the last-wins replay state omits. It is
/// a comparison digest for recorded content, not authentication of the log or proof that a
/// computation occurred.
///
/// # Errors
///
/// Returns an error when an event contains a non-finite float or cannot be represented as JSON.
pub fn replay_trace_hash(events: &[RunLogEvent]) -> Result<String> {
    replay_trace_hash_with_limits(events, RunLogLimits::default())
}

/// Compute the schema-1 replay-trace hash under an explicit serialization budget.
pub fn replay_trace_hash_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<String> {
    let limits = limits.validate()?;
    preflight_event_slice(events, limits)?;
    let mut hasher = Sha256::new();
    for event in events {
        let legacy_event = legacy_number_event(event)?;
        let bytes = validated_json_bytes_with_limits(&legacy_event, limits)
            .context("failed to serialize event for replay trace hash")?;
        hasher.update((bytes.len() as u64).to_le_bytes());
        hasher.update(&bytes);
    }
    Ok(to_hex(&hasher.finalize()))
}

/// Order-sensitive lossless content hash over the full recorded event sequence.
///
/// This v2 algorithm retains arbitrary-precision numbers inside generic JSON payloads. Event
/// boundaries and schema-defined field order otherwise match [`replay_trace_hash`].
///
/// # Errors
///
/// Returns an error when an event contains a non-finite float or cannot be represented as JSON.
pub fn replay_trace_hash_v2(events: &[RunLogEvent]) -> Result<String> {
    replay_trace_hash_v2_with_limits(events, RunLogLimits::default())
}

/// Compute the lossless replay-trace hash under an explicit serialization budget.
pub fn replay_trace_hash_v2_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<String> {
    let limits = limits.validate()?;
    preflight_event_slice(events, limits)?;
    let mut hasher = Sha256::new();
    for event in events {
        let bytes = validated_json_bytes_with_limits(event, limits)
            .context("failed to serialize event for lossless replay trace hash")?;
        hasher.update((bytes.len() as u64).to_le_bytes());
        hasher.update(&bytes);
    }
    Ok(to_hex(&hasher.finalize()))
}

/// Order-sensitive schema-1 content hash over the **logical** event sequence.
///
/// Unlike [`replay_trace_hash`], this digest deliberately excludes fields named `timestamp_ns`.
/// The released schema-1 algorithm removed that key recursively, including from nested payloads;
/// this function preserves those bytes so existing sidecars continue to verify. Prefer
/// [`logical_trace_hash_v3`] for new comparisons: it excludes only the event's top-level wall
/// clock, keeps identically named nested payload data covered, and preserves arbitrary-precision
/// payload numbers. The run-log's filesystem path is never part of an event and is excluded by
/// construction.
///
/// Consequence: two runs that are logically identical but differ only in their timestamps share
/// the same `logical_trace_hash`, while their [`replay_trace_hash`] values differ. This supports
/// comparison of matching recorded logical traces across different wall clocks; it does not
/// certify that the underlying computations were identical or authenticate either log.
///
/// # Errors
///
/// Returns an error when an event contains a non-finite float or cannot be represented as JSON.
pub fn logical_trace_hash(events: &[RunLogEvent]) -> Result<String> {
    logical_trace_hash_with_limits(events, RunLogLimits::default())
}

/// Compute the schema-1 logical trace hash under an explicit serialization budget.
pub fn logical_trace_hash_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<String> {
    logical_trace_hash_with(events, strip_wall_clock_v1_recursive, false, true, limits)
}

/// Corrected logical trace hash which excludes only each event's top-level `timestamp_ns`.
///
/// This v2 algorithm preserves nested payload fields named `timestamp_ns`, along with event order
/// and every other recorded field, and recursively canonicalizes object-key order. It retains the
/// released serde_json number coercion for compatibility; use [`logical_trace_hash_v3`] when
/// arbitrary-precision generic payload numbers must remain lossless. It is intentionally separate
/// from [`logical_trace_hash`] so a bug fix cannot silently invalidate schema-1 summary/manifest
/// sidecars. Like every digest in this crate, it compares recorded content; it does not
/// authenticate a log or prove that a computation occurred.
///
/// # Errors
///
/// Returns an error when an event contains a non-finite float or cannot be represented as JSON.
pub fn logical_trace_hash_v2(events: &[RunLogEvent]) -> Result<String> {
    logical_trace_hash_v2_with_limits(events, RunLogLimits::default())
}

/// Compute the corrected schema-1 logical trace hash under an explicit serialization budget.
pub fn logical_trace_hash_v2_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<String> {
    logical_trace_hash_with(events, strip_top_level_wall_clock, true, true, limits)
}

/// Lossless logical trace hash which excludes only each event's top-level `timestamp_ns`.
///
/// This v3 algorithm has the corrected wall-clock scope and canonical object-key ordering of
/// [`logical_trace_hash_v2`], while preserving arbitrary-precision numbers inside generic JSON
/// payloads. The separately retained v1/v2 functions reproduce their released number coercion for
/// existing sidecars.
///
/// # Errors
///
/// Returns an error when an event contains a non-finite float or cannot be represented as JSON.
pub fn logical_trace_hash_v3(events: &[RunLogEvent]) -> Result<String> {
    logical_trace_hash_v3_with_limits(events, RunLogLimits::default())
}

/// Compute the lossless logical trace hash under an explicit serialization budget.
pub fn logical_trace_hash_v3_with_limits(
    events: &[RunLogEvent],
    limits: RunLogLimits,
) -> Result<String> {
    logical_trace_hash_with(events, strip_top_level_wall_clock, true, false, limits)
}

fn logical_trace_hash_with(
    events: &[RunLogEvent],
    strip_clock: fn(&mut serde_json::Value),
    canonicalize_keys: bool,
    legacy_numbers: bool,
    limits: RunLogLimits,
) -> Result<String> {
    let limits = limits.validate()?;
    preflight_event_slice(events, limits)?;
    let mut hasher = Sha256::new();
    for event in events {
        if legacy_numbers && matches!(event, RunLogEvent::PidEstimate { .. }) {
            anyhow::bail!("schema-2 pid_estimate has no schema-1 logical representation");
        }
        let mut value = validated_json_value_with_limits(event, limits)
            .context("failed to serialize event for logical trace hash")?;
        if legacy_numbers {
            coerce_legacy_numbers(&mut value)
                .context("event contains a number unsupported by the schema-1 hash")?;
        }
        strip_clock(&mut value);
        if canonicalize_keys {
            canonicalize_object_keys(&mut value)?;
        }
        let bytes = serialize_canonical_json_with_limits(&value, limits)
            .context("failed to serialize logical event for trace hash")?;
        hasher.update((bytes.len() as u64).to_le_bytes());
        hasher.update(&bytes);
    }
    Ok(to_hex(&hasher.finalize()))
}

pub fn logical_trace_hash_from_path(path: impl AsRef<Path>) -> Result<String> {
    logical_trace_hash_from_path_with_limits(path, RunLogLimits::default())
}

pub fn logical_trace_hash_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<String> {
    inspect_path_with_limits(path, limits)?
        .hash_identities
        .logical_legacy
        .map(|identity| identity.digest)
        .context("run log contains numbers unsupported by logical trace hash v1")
}

pub fn logical_trace_hash_v2_from_path(path: impl AsRef<Path>) -> Result<String> {
    logical_trace_hash_v2_from_path_with_limits(path, RunLogLimits::default())
}

pub fn logical_trace_hash_v2_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<String> {
    inspect_path_with_limits(path, limits)?
        .hash_identities
        .logical_top_level_clock_legacy
        .map(|identity| identity.digest)
        .context("run log contains numbers unsupported by logical trace hash v2")
}

/// Compute [`logical_trace_hash_v3`] for a JSONL run log on disk.
pub fn logical_trace_hash_v3_from_path(path: impl AsRef<Path>) -> Result<String> {
    logical_trace_hash_v3_from_path_with_limits(path, RunLogLimits::default())
}

pub fn logical_trace_hash_v3_from_path_with_limits(
    path: impl AsRef<Path>,
    limits: RunLogLimits,
) -> Result<String> {
    Ok(inspect_path_with_limits(path, limits)?
        .hash_identities
        .logical_lossless
        .digest)
}

/// Clone an event and reproduce serde_json's pre-`arbitrary_precision` representation for its
/// generic JSON fields without disturbing the event struct's released serialization order.
fn legacy_number_event(event: &RunLogEvent) -> Result<RunLogEvent> {
    let mut event = event.clone();
    let value = match &mut event {
        RunLogEvent::ConfigLogged { config, .. } => Some(config),
        RunLogEvent::BridgeRequest { payload, .. }
        | RunLogEvent::ActionApplied { payload, .. }
        | RunLogEvent::InterventionApplied { payload, .. } => Some(payload),
        RunLogEvent::LabelObserved { value, .. } => Some(value),
        RunLogEvent::RunStarted { .. }
        | RunLogEvent::RunEnded { .. }
        | RunLogEvent::FrameObserved { .. }
        | RunLogEvent::EmbeddingCaptured { .. }
        | RunLogEvent::EmbeddingContract { .. }
        | RunLogEvent::SimSnapshot { .. }
        | RunLogEvent::BridgeResponse { .. }
        | RunLogEvent::ObjectPose { .. }
        | RunLogEvent::FlowGt { .. }
        | RunLogEvent::FlowPred { .. }
        | RunLogEvent::PidMetric { .. }
        | RunLogEvent::GeometryMetric { .. }
        | RunLogEvent::EvaluationMetric { .. }
        | RunLogEvent::ArtifactLogged { .. }
        | RunLogEvent::AttributionLogged { .. }
        | RunLogEvent::ErrorLogged { .. } => None,
        RunLogEvent::PidEstimate { .. } => {
            anyhow::bail!("schema-2 pid_estimate has no schema-1 numeric representation")
        }
    };
    if let Some(value) = value {
        coerce_legacy_numbers(value)?;
    }
    Ok(event)
}

/// Recursively reproduce serde_json's representation before `arbitrary_precision` was enabled.
/// Integer tokens fitting the signed/unsigned 64-bit variants remain integers; decimal/exponent
/// literals and out-of-range integers pass through finite `f64` formatting.
fn coerce_legacy_numbers(value: &mut serde_json::Value) -> Result<()> {
    match value {
        serde_json::Value::Array(items) => {
            for item in items {
                coerce_legacy_numbers(item)?;
            }
        }
        serde_json::Value::Object(map) => {
            for child in map.values_mut() {
                coerce_legacy_numbers(child)?;
            }
        }
        serde_json::Value::Number(number) => {
            let raw = number.as_str();
            let integer_syntax = !raw.bytes().any(|byte| matches!(byte, b'.' | b'e' | b'E'));
            let legacy = if integer_syntax && raw != "-0" {
                if raw.starts_with('-') {
                    raw.parse::<i64>().ok().map(serde_json::Number::from)
                } else {
                    raw.parse::<u64>().ok().map(serde_json::Number::from)
                }
            } else {
                None
            };
            *number = match legacy {
                Some(integer) => integer,
                None => {
                    let float = raw.parse::<f64>().with_context(|| {
                        format!("schema-1 hash cannot represent JSON number {raw}")
                    })?;
                    serde_json::Number::from_f64(float).with_context(|| {
                        format!("schema-1 hash cannot represent JSON number {raw} as finite f64")
                    })?
                }
            };
        }
        _ => {}
    }
    Ok(())
}

fn strip_top_level_wall_clock(value: &mut serde_json::Value) {
    if let serde_json::Value::Object(map) = value {
        map.remove("timestamp_ns");
    }
}

fn strip_wall_clock_v1_recursive(value: &mut serde_json::Value) {
    match value {
        serde_json::Value::Object(map) => {
            map.remove("timestamp_ns");
            for child in map.values_mut() {
                strip_wall_clock_v1_recursive(child);
            }
        }
        serde_json::Value::Array(items) => {
            for item in items {
                strip_wall_clock_v1_recursive(item);
            }
        }
        _ => {}
    }
}

/// Hash the schema-1 canonical JSON representation of a serializable value.
///
/// Object keys are sorted recursively, making the digest independent of map iteration order.
/// This unversioned function preserves the released serde_json numeric representation: integers in
/// the `i64`/`u64` range remain integers, while decimal/exponent literals and larger integers pass
/// through finite `f64` formatting. Use [`canonical_json_hash_v2`] for a lossless content address.
/// Non-finite floating-point values are rejected because JSON has no representation for them and
/// `serde_json` would otherwise serialize them as `null`, colliding with a genuine JSON null.
pub fn canonical_json_hash<T: Serialize>(value: &T) -> Result<String> {
    canonical_json_hash_with_limits(value, RunLogLimits::default())
}

/// Hash the schema-1 canonical representation under an explicit serialization budget.
pub fn canonical_json_hash_with_limits<T: Serialize>(
    value: &T,
    limits: RunLogLimits,
) -> Result<String> {
    let limits = limits.validate()?;
    let mut canonical = validated_json_value_with_limits(value, limits)?;
    coerce_legacy_numbers(&mut canonical)
        .context("value contains a number unsupported by the schema-1 canonical hash")?;
    canonicalize_object_keys(&mut canonical)?;
    Ok(sha256_hex(&serialize_canonical_json_with_limits(
        &canonical, limits,
    )?))
}

/// Hash a lossless canonical JSON representation of a serializable value.
///
/// Object keys are sorted recursively and arbitrary-precision JSON number text is retained. This
/// is the preferred content address for newly written payloads and configs. Schema-1 validation
/// accepts both this generation and [`canonical_json_hash`] because its hash fields predate an
/// explicit generation marker.
pub fn canonical_json_hash_v2<T: Serialize>(value: &T) -> Result<String> {
    canonical_json_hash_v2_with_limits(value, RunLogLimits::default())
}

/// Hash the lossless canonical representation under an explicit serialization budget.
pub fn canonical_json_hash_v2_with_limits<T: Serialize>(
    value: &T,
    limits: RunLogLimits,
) -> Result<String> {
    let limits = limits.validate()?;
    let mut canonical = validated_json_value_with_limits(value, limits)?;
    canonicalize_object_keys(&mut canonical)?;
    Ok(sha256_hex(&serialize_canonical_json_with_limits(
        &canonical, limits,
    )?))
}

/// Hash a value with the current lossless canonical JSON contract and retain its full identity.
pub fn canonical_json_hash_identity_v2<T: Serialize>(value: &T) -> Result<HashIdentity> {
    HashIdentity::sha256(
        HashRevision::CanonicalJsonV2,
        canonical_json_hash_v2(value)?,
    )
}

#[derive(Debug, Clone)]
struct CanonicalJsonHashes {
    legacy: Option<String>,
    lossless: String,
}

impl CanonicalJsonHashes {
    fn matches_for_schema(&self, candidate: &str, strict_schema: bool) -> bool {
        candidate == self.lossless || (!strict_schema && self.legacy.as_deref() == Some(candidate))
    }
}

fn canonical_json_hashes_with_limits<T: Serialize>(
    value: &T,
    limits: RunLogLimits,
) -> Result<CanonicalJsonHashes> {
    let lossless = canonical_json_hash_v2_with_limits(value, limits)?;
    // Once the lossless hash succeeds, the only additional failure mode in the legacy generation
    // is a syntactically valid JSON number outside finite f64. Such values simply have no v1 hash.
    let legacy = canonical_json_hash_with_limits(value, limits).ok();
    Ok(CanonicalJsonHashes { legacy, lossless })
}

fn validated_json_bytes_with_limits<T: Serialize>(
    value: &T,
    limits: RunLogLimits,
) -> Result<Vec<u8>> {
    let limits = limits.validate()?;
    let byte_limit = serialized_json_line_limit(limits);
    let bytes =
        serialize_json_with_byte_limit(value, false, byte_limit, "serialized JSON line bytes")?;
    validate_finite_json(value)?;
    preflight_json_bytes(&bytes, &limits)?;
    Ok(bytes)
}

fn serialized_json_line_limit(limits: RunLogLimits) -> usize {
    limits
        .max_line_bytes
        .min(usize::try_from(limits.max_file_bytes).unwrap_or(usize::MAX))
}

fn validated_json_value_with_limits<T: Serialize>(
    value: &T,
    limits: RunLogLimits,
) -> Result<serde_json::Value> {
    let bytes = validated_json_bytes_with_limits(value, limits)?;
    serde_json::from_slice(&bytes).context("failed to decode validated JSON value")
}

fn validate_finite_json<T: Serialize>(value: &T) -> Result<()> {
    value
        .serialize(FiniteJsonValidator)
        .context("value contains data that is not valid finite JSON")
}

fn serialize_canonical_json_with_limits(
    value: &serde_json::Value,
    limits: RunLogLimits,
) -> Result<Vec<u8>> {
    let byte_limit = serialized_json_line_limit(limits);
    serialize_json_with_byte_limit(value, false, byte_limit, "canonical JSON bytes")
        .context("failed to serialize canonical value for hashing")
}

fn canonicalize_object_keys(value: &mut serde_json::Value) -> Result<()> {
    match value {
        serde_json::Value::Array(items) => {
            for item in items {
                canonicalize_object_keys(item)?;
            }
        }
        serde_json::Value::Object(map) => {
            for child in map.values_mut() {
                canonicalize_object_keys(child)?;
            }

            // `serde_json::Map` is sorted unless its optional `preserve_order` feature is active.
            // Rebuilding from explicitly sorted entries keeps this function canonical either way.
            let previous = std::mem::take(map);
            let mut entries = Vec::new();
            entries.try_reserve_exact(previous.len()).map_err(|_| {
                resource_limit(
                    "canonical JSON key ordering",
                    previous.len(),
                    RunLogLimits::default().max_object_entries,
                )
            })?;
            entries.extend(previous);
            entries.sort_unstable_by(|(left, _), (right, _)| left.cmp(right));
            map.extend(entries);
        }
        _ => {}
    }
    Ok(())
}

/// A traversal-only serializer that rejects floats which JSON cannot represent.
///
/// This validation must happen before converting to `serde_json::Value`: serde_json intentionally
/// maps NaN and infinities to `null`, after which their original type cannot be recovered.
#[derive(Clone, Copy)]
struct FiniteJsonValidator;

fn non_finite_json_error() -> serde_json::Error {
    <serde_json::Error as serde::ser::Error>::custom(
        "non-finite floating-point value cannot be represented in canonical JSON",
    )
}

impl serde::Serializer for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;
    type SerializeSeq = Self;
    type SerializeTuple = Self;
    type SerializeTupleStruct = Self;
    type SerializeTupleVariant = Self;
    type SerializeMap = Self;
    type SerializeStruct = Self;
    type SerializeStructVariant = Self;

    fn serialize_bool(self, _value: bool) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_i8(self, _value: i8) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_i16(self, _value: i16) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_i32(self, _value: i32) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_i64(self, _value: i64) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_i128(self, _value: i128) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_u8(self, _value: u8) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_u16(self, _value: u16) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_u32(self, _value: u32) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_u64(self, _value: u64) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_u128(self, _value: u128) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_f32(self, value: f32) -> std::result::Result<Self::Ok, Self::Error> {
        if value.is_finite() {
            Ok(())
        } else {
            Err(non_finite_json_error())
        }
    }

    fn serialize_f64(self, value: f64) -> std::result::Result<Self::Ok, Self::Error> {
        if value.is_finite() {
            Ok(())
        } else {
            Err(non_finite_json_error())
        }
    }

    fn serialize_char(self, _value: char) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_str(self, _value: &str) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_bytes(self, _value: &[u8]) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_none(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_some<T: ?Sized + Serialize>(
        self,
        value: &T,
    ) -> std::result::Result<Self::Ok, Self::Error> {
        value.serialize(self)
    }

    fn serialize_unit(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_unit_struct(
        self,
        _name: &'static str,
    ) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_unit_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
    ) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }

    fn serialize_newtype_struct<T: ?Sized + Serialize>(
        self,
        _name: &'static str,
        value: &T,
    ) -> std::result::Result<Self::Ok, Self::Error> {
        value.serialize(self)
    }

    fn serialize_newtype_variant<T: ?Sized + Serialize>(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        value: &T,
    ) -> std::result::Result<Self::Ok, Self::Error> {
        value.serialize(self)
    }

    fn serialize_seq(
        self,
        _len: Option<usize>,
    ) -> std::result::Result<Self::SerializeSeq, Self::Error> {
        Ok(self)
    }

    fn serialize_tuple(
        self,
        _len: usize,
    ) -> std::result::Result<Self::SerializeTuple, Self::Error> {
        Ok(self)
    }

    fn serialize_tuple_struct(
        self,
        _name: &'static str,
        _len: usize,
    ) -> std::result::Result<Self::SerializeTupleStruct, Self::Error> {
        Ok(self)
    }

    fn serialize_tuple_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> std::result::Result<Self::SerializeTupleVariant, Self::Error> {
        Ok(self)
    }

    fn serialize_map(
        self,
        _len: Option<usize>,
    ) -> std::result::Result<Self::SerializeMap, Self::Error> {
        Ok(self)
    }

    fn serialize_struct(
        self,
        _name: &'static str,
        _len: usize,
    ) -> std::result::Result<Self::SerializeStruct, Self::Error> {
        Ok(self)
    }

    fn serialize_struct_variant(
        self,
        _name: &'static str,
        _variant_index: u32,
        _variant: &'static str,
        _len: usize,
    ) -> std::result::Result<Self::SerializeStructVariant, Self::Error> {
        Ok(self)
    }

    fn is_human_readable(&self) -> bool {
        true
    }
}

impl SerializeSeq for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_element<T: ?Sized + Serialize>(
        &mut self,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeTuple for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_element<T: ?Sized + Serialize>(
        &mut self,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeTupleStruct for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_field<T: ?Sized + Serialize>(
        &mut self,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeTupleVariant for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_field<T: ?Sized + Serialize>(
        &mut self,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeMap for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_key<T: ?Sized + Serialize>(
        &mut self,
        key: &T,
    ) -> std::result::Result<(), Self::Error> {
        key.serialize(*self)
    }

    fn serialize_value<T: ?Sized + Serialize>(
        &mut self,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeStruct for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_field<T: ?Sized + Serialize>(
        &mut self,
        _key: &'static str,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

impl SerializeStructVariant for FiniteJsonValidator {
    type Ok = ();
    type Error = serde_json::Error;

    fn serialize_field<T: ?Sized + Serialize>(
        &mut self,
        _key: &'static str,
        value: &T,
    ) -> std::result::Result<(), Self::Error> {
        value.serialize(*self)
    }

    fn end(self) -> std::result::Result<Self::Ok, Self::Error> {
        Ok(())
    }
}

/// Hash a file under the default finite [`RunLogLimits::max_file_bytes`] ceiling.
pub fn sha256_file(path: impl AsRef<Path>) -> Result<String> {
    sha256_file_with_limit(path, RunLogLimits::default().max_file_bytes)
}

/// Hash a file while rejecting more than `max_bytes` bytes.
///
/// The limit is checked against metadata from the opened handle and again while reading, so a
/// concurrently growing file cannot bypass the ceiling.
pub fn sha256_file_with_limit(path: impl AsRef<Path>, max_bytes: u64) -> Result<String> {
    if max_bytes == 0 {
        return Err(anyhow::Error::new(RunLogError::InvalidLimits));
    }
    let path = path.as_ref();
    let mut file =
        File::open(path).with_context(|| format!("failed to open artifact {}", path.display()))?;
    let metadata = file
        .metadata()
        .with_context(|| format!("failed to inspect artifact {}", path.display()))?;
    if metadata.len() > max_bytes {
        return Err(resource_limit(
            "artifact hash bytes",
            metadata.len(),
            max_bytes,
        ));
    }
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 8192];
    let mut total = 0u64;
    loop {
        let n = file
            .read(&mut buf)
            .with_context(|| format!("failed to read artifact {}", path.display()))?;
        if n == 0 {
            break;
        }
        total = total
            .checked_add(n as u64)
            .ok_or_else(|| resource_limit("artifact hash bytes", u128::MAX, max_bytes))?;
        if total > max_bytes {
            return Err(resource_limit("artifact hash bytes", total, max_bytes));
        }
        hasher.update(&buf[..n]);
    }
    Ok(to_hex(&hasher.finalize()))
}

pub fn sha256_hex(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    to_hex(&hasher.finalize())
}

fn to_hex(bytes: &[u8]) -> String {
    const HEX: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for &byte in bytes {
        out.push(HEX[(byte >> 4) as usize] as char);
        out.push(HEX[(byte & 0x0f) as usize] as char);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;
    use std::collections::HashMap;
    use std::io::Cursor;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn actor() -> Actor {
        Actor {
            actor_type: ActorType::Script,
            actor_id: "test".to_string(),
            session_id: Some("s1".to_string()),
        }
    }

    fn unique_temp_path(stem: &str) -> PathBuf {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        std::env::temp_dir().join(format!("pid-runlog-{stem}-{stamp}.json"))
    }

    struct PartialFailWriter {
        bytes: Vec<u8>,
        remaining: usize,
    }

    impl Write for PartialFailWriter {
        fn write(&mut self, input: &[u8]) -> std::io::Result<usize> {
            if self.remaining == 0 {
                return Err(std::io::Error::other("injected partial write failure"));
            }
            let written = input.len().min(self.remaining);
            self.bytes.extend_from_slice(&input[..written]);
            self.remaining -= written;
            Ok(written)
        }

        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }

    fn metric_event(value: f64) -> RunLogEvent {
        RunLogEvent::PidMetric {
            step: 0,
            timestamp_ns: 1,
            name: "redundancy".to_string(),
            value,
            metadata: BTreeMap::new(),
        }
    }

    fn null_label_event() -> RunLogEvent {
        RunLogEvent::LabelObserved {
            step: 0,
            timestamp_ns: 1,
            name: "optional_label".to_string(),
            value: serde_json::Value::Null,
            metadata: BTreeMap::new(),
        }
    }

    fn sample_events() -> Vec<RunLogEvent> {
        let config = json!({ "dt": 0.01, "source": "sample" });
        let config_hash = canonical_json_hash_v2(&config).unwrap();
        let step_payload = json!({ "dt": 0.01 });
        let step_payload_hash = canonical_json_hash_v2(&step_payload).unwrap();
        let artifact_hash = sha256_hex(b"sample artifact");
        vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "run-1".to_string(),
                timestamp_ns: 1,
                config_hash: config_hash.clone(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash,
                config,
            },
            RunLogEvent::ActionApplied {
                step: 0,
                timestamp_ns: 2,
                actor: actor(),
                action_type: "sim.step".to_string(),
                payload_hash: step_payload_hash.clone(),
                payload: step_payload.clone(),
            },
            RunLogEvent::EmbeddingCaptured {
                step: 0,
                timestamp_ns: 2,
                name: "V".to_string(),
                dims: vec![1, 3],
                artifact_uri: Some("artifacts/v.npy".to_string()),
                sha256: Some(artifact_hash.clone()),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::EmbeddingContract {
                timestamp_ns: 2,
                name: "vla_tuple".to_string(),
                variables: vec![EmbeddingVariableContract {
                    variable: "V".to_string(),
                    source: "V".to_string(),
                    dims: vec![1, 3],
                    artifact_uri: Some("artifacts/v.npy".to_string()),
                    sha256: Some(artifact_hash),
                }],
                metadata: BTreeMap::new(),
            },
            RunLogEvent::BridgeRequest {
                step: Some(0),
                timestamp_ns: 2,
                request_id: "req-1".to_string(),
                actor: actor(),
                method: "sim.step".to_string(),
                payload_hash: step_payload_hash,
                payload: step_payload,
            },
            RunLogEvent::BridgeResponse {
                step: Some(0),
                timestamp_ns: 2,
                request_id: "req-1".to_string(),
                ok: true,
                message: None,
                result_hash: None,
            },
            RunLogEvent::ObjectPose {
                step: 0,
                timestamp_ns: 3,
                object_id: "cube".to_string(),
                pose: Pose {
                    position: [1.0, 2.0, 3.0],
                    orientation_xyzw: [0.0, 0.0, 0.0, 1.0],
                },
            },
            RunLogEvent::PidMetric {
                step: 0,
                timestamp_ns: 4,
                name: "redundancy".to_string(),
                value: 0.25,
                metadata: BTreeMap::new(),
            },
            RunLogEvent::EvaluationMetric {
                step: 0,
                timestamp_ns: 4,
                name: "baseline.accuracy".to_string(),
                value: 0.75,
                metadata: BTreeMap::new(),
            },
            RunLogEvent::LabelObserved {
                step: 0,
                timestamp_ns: 4,
                name: "success".to_string(),
                value: json!(true),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::RunEnded {
                run_id: "run-1".to_string(),
                timestamp_ns: 5,
                status: RunStatus::Succeeded,
                message: None,
            },
        ]
    }

    #[test]
    fn jsonl_round_trip_preserves_events() {
        let events = sample_events();
        let mut writer = RunLogWriter::new(Vec::new());
        for event in &events {
            writer.append(event).unwrap();
        }
        let bytes = writer.into_inner();
        let decoded = read_events(Cursor::new(bytes)).unwrap();
        assert_eq!(decoded, events);
    }

    #[test]
    fn append_rejects_non_finite_events_before_writing() {
        let finite = RunLogEvent::PidMetric {
            step: 0,
            timestamp_ns: 1,
            name: "redundancy".to_string(),
            value: 0.25,
            metadata: BTreeMap::new(),
        };
        for bad_value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            let mut writer = RunLogWriter::new(Vec::new());
            writer.append(&finite).unwrap();
            let poisoned = RunLogEvent::PidMetric {
                step: 1,
                timestamp_ns: 2,
                name: "redundancy".to_string(),
                value: bad_value,
                metadata: BTreeMap::new(),
            };
            let err = writer.append(&poisoned).unwrap_err();
            assert!(
                format!("{err:#}").contains("non-finite"),
                "unexpected error for {bad_value}: {err:#}"
            );
            // The rejected event must not have been written: the log still parses and holds
            // exactly the one finite event.
            let bytes = writer.into_inner();
            let decoded = read_events(Cursor::new(bytes)).unwrap();
            assert_eq!(decoded, vec![finite.clone()]);
        }
    }

    #[test]
    fn append_enforces_aggregate_event_and_file_limits_before_writing() {
        let event = sample_events().remove(0);
        let encoded_bytes = serde_json::to_vec(&event).unwrap().len();

        let mut newline_limited = RunLogWriter::new(Vec::new());
        let error = newline_limited
            .append_with_limits(
                &event,
                RunLogLimits::default().with_max_file_bytes(encoded_bytes as u64),
            )
            .unwrap_err();
        assert!(format!("{error:#}").contains("output file bytes"));
        assert!(newline_limited.into_inner().is_empty());

        let encoded_line_bytes = u64::try_from(encoded_bytes + 1).unwrap();
        let mut byte_limited = RunLogWriter::new(Vec::new());
        let limits = RunLogLimits::default().with_max_file_bytes(encoded_line_bytes * 2 - 1);
        byte_limited.append_with_limits(&event, limits).unwrap();
        let first_line = byte_limited.writer.clone();
        let error = byte_limited.append_with_limits(&event, limits).unwrap_err();
        assert!(format!("{error:#}").contains("output file bytes"));
        assert_eq!(byte_limited.into_inner(), first_line);

        let mut event_limited = RunLogWriter::new(Vec::new());
        let limits = RunLogLimits::default().with_max_events(1);
        event_limited.append_with_limits(&event, limits).unwrap();
        let first_line = event_limited.writer.clone();
        let error = event_limited
            .append_with_limits(&event, limits)
            .unwrap_err();
        assert!(format!("{error:#}").contains("output event count"));
        assert_eq!(event_limited.into_inner(), first_line);
    }

    #[test]
    fn append_poisoned_after_partial_io_failure_cannot_retry() {
        let event = sample_events().remove(0);
        let mut writer = RunLogWriter::new(PartialFailWriter {
            bytes: Vec::new(),
            remaining: 5,
        });

        let error = writer.append(&event).unwrap_err();
        assert!(format!("{error:#}").contains("partial write failure"));
        let bytes_after_failure = writer.writer.bytes.clone();
        let error = writer.append(&event).unwrap_err();
        assert!(format!("{error:#}").contains("unusable after a previous I/O failure"));
        assert_eq!(writer.into_inner().bytes, bytes_after_failure);
    }

    #[test]
    fn read_events_rejects_unknown_event_fields() {
        let line = r#"{"type":"run_started","schema_version":1,"run_id":"run-1","timestamp_ns":1,"config_hash":"cfg","metadata":{},"unexpected":true}"#;
        let error = read_events(Cursor::new(format!("{line}\n"))).unwrap_err();

        assert!(
            format!("{error:#}").contains("unknown field `unexpected`"),
            "unexpected parse error: {error:#}"
        );
    }

    #[test]
    fn read_events_rejects_unknown_nested_actor_fields() {
        let line = r#"{"type":"action_applied","step":0,"timestamp_ns":1,"actor":{"actor_type":"script","actor_id":"test","session_id":null,"unexpected":true},"action_type":"step","payload_hash":"hash","payload":{}}"#;
        let error = read_events(Cursor::new(format!("{line}\n"))).unwrap_err();

        assert!(
            format!("{error:#}").contains("unknown field `unexpected`"),
            "unexpected parse error: {error:#}"
        );
    }

    #[test]
    fn replay_tracks_latest_state() {
        let events = sample_events();
        let state = replay_events(&events).unwrap();
        assert_eq!(state.run_id.as_deref(), Some("run-1"));
        assert_eq!(state.last_step, Some(0));
        assert_eq!(state.actions.len(), 1);
        assert_eq!(state.embeddings.len(), 1);
        assert_eq!(state.embedding_contracts[0].name, "vla_tuple");
        assert_eq!(state.embedding_contracts[0].variables[0].variable, "V");
        assert_eq!(state.bridge_records.len(), 2);
        assert_eq!(state.object_poses["cube"].pose.position, [1.0, 2.0, 3.0]);
        assert_eq!(state.pid_metrics["redundancy"].value, 0.25);
        assert_eq!(state.evaluation_metrics["baseline.accuracy"].value, 0.75);
        assert_eq!(state.pid_metric_events, 1);
        assert_eq!(state.geometry_metric_events, 0);
        assert_eq!(state.evaluation_metric_events, 1);
        assert_eq!(state.labels[0].name, "success");
        assert_eq!(state.labels[0].value, json!(true));
    }

    #[test]
    fn replay_counts_repeated_metric_events_separately_from_unique_names() {
        let mut events = sample_events();
        events.insert(
            events.len() - 1,
            RunLogEvent::EvaluationMetric {
                step: 0,
                timestamp_ns: 4,
                name: "baseline.accuracy".to_string(),
                value: 0.875,
                metadata: BTreeMap::new(),
            },
        );

        let state = replay_events(&events).unwrap();
        assert_eq!(state.evaluation_metrics.len(), 1);
        assert_eq!(state.evaluation_metrics["baseline.accuracy"].value, 0.875);
        assert_eq!(state.evaluation_metric_events, 2);

        let summary = summarize_events(&events).unwrap();
        assert_eq!(summary.evaluation_metrics, 1);
        assert_eq!(summary.evaluation_metric_events, 2);
    }

    #[test]
    fn validation_accepts_sample_events() {
        let report = validate_events(&sample_events()).unwrap();
        assert!(report.is_valid(), "{:?}", report.issues);
        assert_eq!(report.warnings, 0);
    }

    #[test]
    fn schema_two_requires_exactly_one_config_logged_event() {
        let mut missing = sample_events();
        assert!(matches!(
            missing.remove(1),
            RunLogEvent::ConfigLogged { .. }
        ));
        let missing_report = validate_events(&missing).unwrap();
        assert!(!missing_report.is_valid());
        assert!(missing_report.issues.iter().any(|issue| {
            issue
                .message
                .contains("requires exactly one config_logged event, got 0")
        }));
        assert!(missing_report.issues.iter().any(|issue| {
            issue
                .message
                .contains("config_logged must precede operational events")
        }));

        let mut duplicate = sample_events();
        let second_config = duplicate[1].clone();
        duplicate.insert(2, second_config);
        let duplicate_report = validate_events(&duplicate).unwrap();
        assert!(!duplicate_report.is_valid());
        assert!(duplicate_report.issues.iter().any(|issue| {
            issue
                .message
                .contains("requires exactly one config_logged event")
        }));
    }

    #[test]
    fn schema_two_rejects_config_logged_after_operational_events() {
        let mut events = sample_events();
        let mut config = events.remove(1);
        if let RunLogEvent::ConfigLogged { timestamp_ns, .. } = &mut config {
            *timestamp_ns = 4;
        } else {
            panic!("sample event layout changed");
        }
        events.insert(events.len() - 1, config);

        let report = validate_events(&events).unwrap();

        assert!(!report.is_valid());
        assert!(report.issues.iter().any(|issue| {
            issue
                .message
                .contains("config_logged must precede operational events")
        }));
    }

    #[test]
    fn schema_two_rejects_empty_config_hash_bindings() {
        let mut events = sample_events();
        if let RunLogEvent::RunStarted { config_hash, .. } = &mut events[0] {
            config_hash.clear();
        } else {
            panic!("sample event layout changed");
        }
        if let RunLogEvent::ConfigLogged { config_hash, .. } = &mut events[1] {
            config_hash.clear();
        } else {
            panic!("sample event layout changed");
        }

        let report = validate_events(&events).unwrap();

        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("run_started.config_hash is empty")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("config_logged.config_hash is empty")));
    }

    #[test]
    fn schema_one_remains_valid_without_config_logged() {
        let mut events = sample_events();
        assert!(matches!(events.remove(1), RunLogEvent::ConfigLogged { .. }));
        if let RunLogEvent::RunStarted { schema_version, .. } = &mut events[0] {
            *schema_version = MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION;
        } else {
            panic!("sample event layout changed");
        }

        let report = validate_events(&events).unwrap();

        assert!(report.is_valid(), "{:?}", report.issues);
        assert!(!report
            .issues
            .iter()
            .any(|issue| issue.message.contains("requires exactly one config_logged")));
    }

    #[test]
    fn validation_catches_bad_payload_hash() {
        let mut events = sample_events();
        if let RunLogEvent::ActionApplied { payload_hash, .. } = &mut events[2] {
            *payload_hash = "bad".to_string();
        }
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("payload_hash")));
    }

    #[test]
    fn validation_catches_bad_config_hash() {
        let config = json!({ "dt": 0.1 });
        let events = vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "run-1".to_string(),
                timestamp_ns: 1,
                config_hash: canonical_json_hash(&config).unwrap(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash: "bad".to_string(),
                config,
            },
            RunLogEvent::RunEnded {
                run_id: "run-1".to_string(),
                timestamp_ns: 2,
                status: RunStatus::Failed,
                message: None,
            },
        ];
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("config_hash")));
    }

    #[test]
    fn schema_one_accepts_mixed_legacy_and_lossless_canonical_hashes() {
        let config: serde_json::Value =
            serde_json::from_str(r#"{"rate":1E+02,"threshold":0.2500}"#).unwrap();
        let payload: serde_json::Value =
            serde_json::from_str(r#"{"command":1E+02,"gain":0.2500}"#).unwrap();
        let config_v1 = canonical_json_hash(&config).unwrap();
        let config_v2 = canonical_json_hash_v2(&config).unwrap();
        let payload_v1 = canonical_json_hash(&payload).unwrap();
        let payload_v2 = canonical_json_hash_v2(&payload).unwrap();
        assert_ne!(config_v1, config_v2);
        assert_ne!(payload_v1, payload_v2);

        for (started_hash, logged_hash, action_hash) in [
            (&config_v1, &config_v2, &payload_v1),
            (&config_v2, &config_v1, &payload_v2),
        ] {
            let events = vec![
                RunLogEvent::RunStarted {
                    schema_version: MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION,
                    run_id: "mixed-canonical-hashes".to_string(),
                    timestamp_ns: 1,
                    config_hash: started_hash.clone(),
                    metadata: BTreeMap::new(),
                },
                RunLogEvent::ConfigLogged {
                    timestamp_ns: 1,
                    config_hash: logged_hash.clone(),
                    config: config.clone(),
                },
                RunLogEvent::ActionApplied {
                    step: 0,
                    timestamp_ns: 2,
                    actor: actor(),
                    action_type: "set-gain".to_string(),
                    payload_hash: action_hash.clone(),
                    payload: payload.clone(),
                },
                RunLogEvent::RunEnded {
                    run_id: "mixed-canonical-hashes".to_string(),
                    timestamp_ns: 3,
                    status: RunStatus::Succeeded,
                    message: None,
                },
            ];

            let report = validate_events(&events).unwrap();
            assert!(report.is_valid(), "{:?}", report.issues);
        }
    }

    #[test]
    fn schema_two_rejects_legacy_canonical_hash_generation() {
        let config: serde_json::Value =
            serde_json::from_str(r#"{"rate":1E+02,"threshold":0.2500}"#).unwrap();
        let payload: serde_json::Value =
            serde_json::from_str(r#"{"command":1E+02,"gain":0.2500}"#).unwrap();
        let config_v1 = canonical_json_hash(&config).unwrap();
        let payload_v1 = canonical_json_hash(&payload).unwrap();
        let events = vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "explicit-hash-generation".to_string(),
                timestamp_ns: 1,
                config_hash: config_v1.clone(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash: config_v1,
                config,
            },
            RunLogEvent::ActionApplied {
                step: 0,
                timestamp_ns: 2,
                actor: actor(),
                action_type: "set-gain".to_string(),
                payload_hash: payload_v1,
                payload,
            },
            RunLogEvent::RunEnded {
                run_id: "explicit-hash-generation".to_string(),
                timestamp_ns: 3,
                status: RunStatus::Succeeded,
                message: None,
            },
        ];

        let report = validate_events(&events).unwrap();

        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("config_hash does not match")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("payload_hash does not match")));
    }

    #[test]
    fn validation_catches_config_hash_mismatch_with_run_started() {
        let config = json!({ "dt": 0.1 });
        let config_hash = canonical_json_hash(&config).unwrap();
        let events = vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "run-1".to_string(),
                timestamp_ns: 1,
                config_hash: "different".to_string(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash,
                config,
            },
            RunLogEvent::RunEnded {
                run_id: "run-1".to_string(),
                timestamp_ns: 2,
                status: RunStatus::Failed,
                message: None,
            },
        ];
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("does not match run_started")));
    }

    #[test]
    fn validation_catches_events_after_run_ended() {
        let mut events = sample_events();
        events.push(RunLogEvent::ErrorLogged {
            step: None,
            timestamp_ns: 6,
            message: "late event".to_string(),
            recoverable: true,
        });
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("run_ended must be the last event")));
    }

    #[test]
    fn validation_catches_bad_label() {
        let mut events = sample_events();
        if let RunLogEvent::LabelObserved { name, value, .. } = &mut events[10] {
            name.clear();
            *value = serde_json::Value::Null;
        }
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("label name")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("label value")));
    }

    #[test]
    fn validation_catches_bad_embedding_contract() {
        let mut events = sample_events();
        if let RunLogEvent::EmbeddingContract {
            name, variables, ..
        } = &mut events[4]
        {
            name.clear();
            variables.push(EmbeddingVariableContract {
                variable: "V".to_string(),
                source: "".to_string(),
                dims: vec![0],
                artifact_uri: None,
                sha256: None,
            });
        }
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("embedding contract name")));
        assert!(report.issues.iter().any(|issue| issue
            .message
            .contains("duplicate embedding contract variable")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("embedding contract dims")));
    }

    #[test]
    fn validation_catches_bad_flow_pred() {
        let mut events = sample_events();
        events.insert(
            events.len() - 1,
            RunLogEvent::FlowPred {
                step: 0,
                timestamp_ns: 4,
                source: "".to_string(),
                object_id: "".to_string(),
                horizon_steps: 0,
                flow: vec![[f64::NAN, 0.0, 0.0]],
                metadata: BTreeMap::new(),
            },
        );
        let report = validate_events(&events).unwrap();
        assert!(!report.is_valid());
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("flow source")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("horizon_steps")));
        assert!(report
            .issues
            .iter()
            .any(|issue| issue.message.contains("flow vector")));
    }

    #[test]
    fn summary_and_manifest_include_trace_hash() {
        let mut events = sample_events();
        events.insert(
            events.len() - 1,
            RunLogEvent::FlowPred {
                step: 0,
                timestamp_ns: 4,
                source: "constant_velocity_baseline".to_string(),
                object_id: "cube".to_string(),
                horizon_steps: 1,
                flow: vec![[0.1, 0.0, 0.0]],
                metadata: BTreeMap::new(),
            },
        );
        let summary = summarize_events(&events).unwrap();
        assert_eq!(summary.run_id.as_deref(), Some("run-1"));
        assert_eq!(
            summary.config_hash.as_deref(),
            Some(
                canonical_json_hash_v2(&json!({ "dt": 0.01, "source": "sample" }))
                    .unwrap()
                    .as_str()
            )
        );
        assert_eq!(summary.validation_errors, 0);
        assert_eq!(summary.evaluation_metrics, 1);
        assert_eq!(summary.evaluation_metric_events, 1);
        assert_eq!(summary.labels, 1);
        assert_eq!(summary.embedding_contracts, 1);
        assert_eq!(summary.flow_pred_records, 1);
        assert_eq!(summary.trace_hash.len(), 64);
        let state_hash = replay_trace_hash(&events).unwrap();
        assert_eq!(summary.trace_hash, state_hash);
    }

    #[test]
    fn trace_hash_distinguishes_traces_with_identical_final_state() {
        // `FrameObserved` is a no-op for `ReplayState`, so two traces differing ONLY in a
        // frame's `observation_hash` collapse to the SAME final state — yet they are different
        // traces. A hash of the collapsed state collides (and `--compare` would falsely report a
        // match); the full event-sequence trace hash must distinguish them.
        let make = |obs: &str| {
            vec![
                RunLogEvent::RunStarted {
                    schema_version: RUN_LOG_SCHEMA_VERSION,
                    run_id: "run-1".to_string(),
                    timestamp_ns: 1,
                    config_hash: "cfg".to_string(),
                    metadata: BTreeMap::new(),
                },
                RunLogEvent::FrameObserved {
                    step: 0,
                    timestamp_ns: 2,
                    observation_hash: Some(obs.to_string()),
                    metadata: BTreeMap::new(),
                },
                RunLogEvent::RunEnded {
                    run_id: "run-1".to_string(),
                    timestamp_ns: 3,
                    status: RunStatus::Succeeded,
                    message: None,
                },
            ]
        };
        let a = make("frame-aaaa");
        let b = make("frame-bbbb");
        // Precondition: the collapsed replay states are byte-identical...
        assert_eq!(
            canonical_json_hash(&replay_events(&a).unwrap()).unwrap(),
            canonical_json_hash(&replay_events(&b).unwrap()).unwrap(),
            "the two traces must collapse to the same ReplayState for this test to be meaningful"
        );
        // ...but the full-trace hashes must differ.
        assert_ne!(
            replay_trace_hash(&a).unwrap(),
            replay_trace_hash(&b).unwrap(),
            "trace hash must reflect per-event content, not just the final collapsed state"
        );
    }

    #[test]
    fn logical_trace_hash_ignores_timestamps_but_replay_hash_does_not() {
        // Two logs that are logically identical but differ ONLY in their wall-clock timestamps
        // must share the same logical_trace_hash, while the full replay_trace_hash differs.
        let base = sample_events();
        let mut shifted = base.clone();
        for event in &mut shifted {
            // Bump every event's wall clock by a constant offset; logical content is untouched.
            match event {
                RunLogEvent::RunStarted { timestamp_ns, .. }
                | RunLogEvent::RunEnded { timestamp_ns, .. }
                | RunLogEvent::ConfigLogged { timestamp_ns, .. }
                | RunLogEvent::FrameObserved { timestamp_ns, .. }
                | RunLogEvent::EmbeddingCaptured { timestamp_ns, .. }
                | RunLogEvent::EmbeddingContract { timestamp_ns, .. }
                | RunLogEvent::SimSnapshot { timestamp_ns, .. }
                | RunLogEvent::BridgeRequest { timestamp_ns, .. }
                | RunLogEvent::BridgeResponse { timestamp_ns, .. }
                | RunLogEvent::ActionApplied { timestamp_ns, .. }
                | RunLogEvent::ObjectPose { timestamp_ns, .. }
                | RunLogEvent::FlowGt { timestamp_ns, .. }
                | RunLogEvent::FlowPred { timestamp_ns, .. }
                | RunLogEvent::PidMetric { timestamp_ns, .. }
                | RunLogEvent::PidEstimate { timestamp_ns, .. }
                | RunLogEvent::GeometryMetric { timestamp_ns, .. }
                | RunLogEvent::EvaluationMetric { timestamp_ns, .. }
                | RunLogEvent::LabelObserved { timestamp_ns, .. }
                | RunLogEvent::InterventionApplied { timestamp_ns, .. }
                | RunLogEvent::ArtifactLogged { timestamp_ns, .. }
                | RunLogEvent::AttributionLogged { timestamp_ns, .. }
                | RunLogEvent::ErrorLogged { timestamp_ns, .. } => *timestamp_ns += 1_000_000,
            }
        }

        // Logical hashes match: same recorded logical trace, different wall clock.
        assert_eq!(
            logical_trace_hash(&base).unwrap(),
            logical_trace_hash(&shifted).unwrap(),
            "logical_trace_hash must ignore wall-clock timestamps"
        );
        // Full replay (wall-clock-sensitive) hashes differ.
        assert_ne!(
            replay_trace_hash(&base).unwrap(),
            replay_trace_hash(&shifted).unwrap(),
            "replay_trace_hash must reflect wall-clock timestamps"
        );

        // And the logical hash still distinguishes a genuine logical change.
        let mut logically_changed = base.clone();
        if let RunLogEvent::PidMetric { value, .. } = &mut logically_changed[8] {
            *value += 1.0;
        } else {
            panic!("expected PidMetric at index 8 of sample_events");
        }
        assert_ne!(
            logical_trace_hash(&base).unwrap(),
            logical_trace_hash(&logically_changed).unwrap(),
            "logical_trace_hash must still detect changes to logical content"
        );

        // Sidecars surface both hashes, and the logical hash agrees with the standalone fn.
        let summary = summarize_events(&base).unwrap();
        assert_eq!(
            summary.logical_trace_hash,
            logical_trace_hash(&base).unwrap()
        );
        assert_eq!(summary.logical_trace_hash.len(), 64);
        assert_ne!(summary.logical_trace_hash, summary.trace_hash);
    }

    #[test]
    fn logical_trace_hash_v2_keeps_nested_payload_timestamps_without_breaking_v1() {
        let event = RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 10,
            actor: actor(),
            action_type: "nested-clock".to_string(),
            payload_hash: "payload".to_string(),
            payload: json!({"metadata": {"timestamp_ns": 20}}),
        };

        let mut top_level_changed = event.clone();
        if let RunLogEvent::ActionApplied { timestamp_ns, .. } = &mut top_level_changed {
            *timestamp_ns = 11;
        }
        assert_eq!(
            logical_trace_hash_v2(std::slice::from_ref(&event)).unwrap(),
            logical_trace_hash_v2(std::slice::from_ref(&top_level_changed)).unwrap(),
            "the event's top-level wall clock must remain excluded"
        );

        let mut nested_changed = event.clone();
        if let RunLogEvent::ActionApplied { payload, .. } = &mut nested_changed {
            payload["metadata"]["timestamp_ns"] = json!(21);
        }
        assert_ne!(
            logical_trace_hash_v2(std::slice::from_ref(&event)).unwrap(),
            logical_trace_hash_v2(std::slice::from_ref(&nested_changed)).unwrap(),
            "a nested timestamp_ns is logical payload content and must remain covered"
        );
        assert_eq!(
            logical_trace_hash(std::slice::from_ref(&event)).unwrap(),
            logical_trace_hash(std::slice::from_ref(&nested_changed)).unwrap(),
            "the schema-1 algorithm must retain its historical recursive exclusion"
        );
    }

    #[test]
    fn logical_trace_hash_v2_canonicalizes_nested_object_keys() {
        let mut left_payload = serde_json::Map::new();
        left_payload.insert("z".to_string(), json!({"b": 2, "a": 1}));
        left_payload.insert("a".to_string(), json!(0));
        let mut right_payload = serde_json::Map::new();
        right_payload.insert("a".to_string(), json!(0));
        right_payload.insert("z".to_string(), json!({"a": 1, "b": 2}));

        let make_event = |payload| RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 1,
            actor: actor(),
            action_type: "canonical-keys".to_string(),
            payload_hash: "payload".to_string(),
            payload: serde_json::Value::Object(payload),
        };
        let left = make_event(left_payload);
        let right = make_event(right_payload);
        assert_eq!(
            logical_trace_hash_v2(&[left]).unwrap(),
            logical_trace_hash_v2(&[right]).unwrap()
        );
    }

    #[test]
    fn flush_durable_persists_events_to_disk() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("pid-runlog-fsync-{stamp}.jsonl"));
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        // fsync mid-stream (crash-safe live logging) then finish.
        writer.flush_durable().unwrap();
        writer.sync_all().unwrap();
        drop(writer);

        let decoded = read_events_from_path(&path).unwrap();
        assert_eq!(decoded, sample_events());
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn replay_trace_hash_is_stable() {
        let events = sample_events();
        let h1 = replay_trace_hash(&events).unwrap();
        let h2 = replay_trace_hash(&events).unwrap();
        assert_eq!(h1, h2);
        assert_eq!(h1.len(), 64);

        // Schema 1 defined the trace digest over each event's raw serde JSON bytes (with a
        // little-endian u64 length prefix). Generic canonical key sorting must not silently
        // invalidate existing sidecars.
        let mut legacy = Sha256::new();
        for event in &events {
            let bytes = serde_json::to_vec(event).unwrap();
            legacy.update((bytes.len() as u64).to_le_bytes());
            legacy.update(bytes);
        }
        assert_eq!(h1, to_hex(&legacy.finalize()));
    }

    #[test]
    fn replay_trace_hash_rejects_nan_instead_of_hashing_json_null() {
        let nan_event = metric_event(f64::NAN);
        let serialized = serde_json::to_value(&nan_event).unwrap();
        assert_eq!(serialized["value"], serde_json::Value::Null);

        let error = replay_trace_hash(std::slice::from_ref(&nan_event)).unwrap_err();
        assert!(replay_trace_hash_v2(std::slice::from_ref(&nan_event)).is_err());
        let null_hash = replay_trace_hash(&[null_label_event()]).unwrap();
        assert!(
            format!("{error:#}").contains("finite JSON") && null_hash.len() == 64,
            "NaN error: {error:#}; valid-null hash: {null_hash}"
        );
    }

    #[test]
    fn logical_trace_hash_rejects_nan_instead_of_hashing_json_null() {
        let nan_event = metric_event(f64::NAN);
        let serialized = serde_json::to_value(&nan_event).unwrap();
        assert_eq!(serialized["value"], serde_json::Value::Null);

        let error = logical_trace_hash(std::slice::from_ref(&nan_event)).unwrap_err();
        assert!(logical_trace_hash_v2(std::slice::from_ref(&nan_event)).is_err());
        assert!(logical_trace_hash_v3(std::slice::from_ref(&nan_event)).is_err());
        let null_hash = logical_trace_hash(&[null_label_event()]).unwrap();
        assert!(
            format!("{error:#}").contains("finite JSON") && null_hash.len() == 64,
            "NaN error: {error:#}; valid-null hash: {null_hash}"
        );
    }

    #[test]
    fn canonical_json_hash_sorts_hash_map_keys_recursively() {
        let mut first_inner = HashMap::new();
        first_inner.insert("d".to_string(), 4_u64);
        first_inner.insert("c".to_string(), 3_u64);
        let mut second_inner = HashMap::new();
        second_inner.insert("b".to_string(), 2_u64);
        second_inner.insert("a".to_string(), 1_u64);

        let mut value = HashMap::new();
        value.insert("z".to_string(), second_inner);
        value.insert("a".to_string(), first_inner);

        let canonical = br#"{"a":{"c":3,"d":4},"z":{"a":1,"b":2}}"#;
        assert_eq!(canonical_json_hash(&value).unwrap(), sha256_hex(canonical));
    }

    #[test]
    fn canonical_json_hash_versions_preserve_legacy_collision_and_lossless_integers() {
        const FIRST: &str = "12345678901234567890123456789012345678901234567890";
        const SECOND: &str = "12345678901234567890123456789012345678901234567891";
        let first: serde_json::Value =
            serde_json::from_str(&format!(r#"{{"value":{FIRST}}}"#)).unwrap();
        let second: serde_json::Value =
            serde_json::from_str(&format!(r#"{{"value":{SECOND}}}"#)).unwrap();

        assert_eq!(first["value"].to_string(), FIRST);
        assert_eq!(second["value"].to_string(), SECOND);
        assert_eq!(
            canonical_json_hash(&first).unwrap(),
            canonical_json_hash(&second).unwrap()
        );
        assert_ne!(
            canonical_json_hash_v2(&first).unwrap(),
            canonical_json_hash_v2(&second).unwrap()
        );
    }

    #[test]
    fn jsonl_round_trip_preserves_arbitrary_precision_payload_integer() {
        const INTEGER: &str = "12345678901234567890123456789012345678901234567890";
        let payload: serde_json::Value =
            serde_json::from_str(&format!(r#"{{"value":{INTEGER}}}"#)).unwrap();
        let event = RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 1,
            actor: actor(),
            action_type: "large-integer".to_string(),
            payload_hash: canonical_json_hash_v2(&payload).unwrap(),
            payload,
        };
        let mut writer = RunLogWriter::new(Vec::new());
        writer.append(&event).unwrap();
        let bytes = writer.into_inner();
        let decoded = read_events(Cursor::new(bytes.clone())).unwrap();

        assert_eq!(decoded, vec![event]);
        assert!(String::from_utf8(bytes).unwrap().contains(INTEGER));
    }

    #[test]
    fn versioned_trace_hashes_preserve_legacy_bytes_and_distinguish_lossless_integers() {
        const FIRST: &str = "12345678901234567890123456789012345678901234567890";
        const SECOND: &str = "12345678901234567890123456789012345678901234567891";
        let event = |integer: &str| RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 1,
            actor: actor(),
            action_type: "large-integer".to_string(),
            // Hold the caller-supplied hash fixed so only the payload number can distinguish traces.
            payload_hash: "same-placeholder".to_string(),
            payload: serde_json::from_str(&format!(r#"{{"value":{integer}}}"#)).unwrap(),
        };
        let first = [event(FIRST)];
        let second = [event(SECOND)];

        // These exact fixtures were computed with serde_json *without* arbitrary_precision. Pin
        // them so enabling lossless parsing can never silently invalidate schema-1 sidecars.
        assert_eq!(
            replay_trace_hash(&first).unwrap(),
            "127027cd30d787990f03b2090d101facd47984d556c58358d0313f8d0ec02284"
        );
        assert_eq!(
            logical_trace_hash(&first).unwrap(),
            "fdef66270c7a3837a3112b0ec505c3469b0d4ff4e71a5d843755881aa81d4a0d"
        );
        assert_eq!(
            logical_trace_hash_v2(&first).unwrap(),
            "fdef66270c7a3837a3112b0ec505c3469b0d4ff4e71a5d843755881aa81d4a0d"
        );

        // The released hashes reproduce the former f64 collision; explicitly versioned hashes
        // retain the arbitrary-precision payload and distinguish the adjacent integers.
        assert_eq!(
            replay_trace_hash(&first).unwrap(),
            replay_trace_hash(&second).unwrap()
        );
        assert_eq!(
            logical_trace_hash(&first).unwrap(),
            logical_trace_hash(&second).unwrap()
        );
        assert_eq!(
            logical_trace_hash_v2(&first).unwrap(),
            logical_trace_hash_v2(&second).unwrap()
        );
        assert_ne!(
            replay_trace_hash_v2(&first).unwrap(),
            replay_trace_hash_v2(&second).unwrap()
        );
        assert_ne!(
            logical_trace_hash_v3(&first).unwrap(),
            logical_trace_hash_v3(&second).unwrap()
        );
    }

    #[test]
    fn lossless_trace_hash_path_helpers_match_in_memory_hashes() {
        const INTEGER: &str = "12345678901234567890123456789012345678901234567890";
        let event = RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 1,
            actor: actor(),
            action_type: "large-integer".to_string(),
            payload_hash: "same-placeholder".to_string(),
            payload: serde_json::from_str(&format!(r#"{{"value":{INTEGER}}}"#)).unwrap(),
        };
        let path = unique_temp_path("lossless-hash-path");
        let mut writer = RunLogWriter::create(&path).unwrap();
        writer.append(&event).unwrap();
        writer.flush().unwrap();
        drop(writer);

        assert_eq!(
            replay_trace_hash_v2_from_path(&path).unwrap(),
            replay_trace_hash_v2(std::slice::from_ref(&event)).unwrap()
        );
        assert_eq!(
            logical_trace_hash_v3_from_path(&path).unwrap(),
            logical_trace_hash_v3(std::slice::from_ref(&event)).unwrap()
        );
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn legacy_hashes_normalize_decimal_and_exponent_lexemes() {
        let from_text = |payload: &str| RunLogEvent::LabelObserved {
            step: 0,
            timestamp_ns: 1,
            name: "number-lexemes".to_string(),
            value: serde_json::from_str(payload).unwrap(),
            metadata: BTreeMap::new(),
        };
        let lexical = [from_text(r#"{"value":1E+02}"#)];
        let former_representation = [from_text(r#"{"value":100.0}"#)];
        let canonical_lexical: serde_json::Value =
            serde_json::from_str(r#"{"decimal":0.2500,"value":1E+02}"#).unwrap();

        assert_eq!(
            canonical_json_hash(&lexical[0]).unwrap(),
            canonical_json_hash(&former_representation[0]).unwrap()
        );
        assert_eq!(
            canonical_json_hash(&canonical_lexical).unwrap(),
            sha256_hex(br#"{"decimal":0.25,"value":100.0}"#)
        );
        assert_ne!(
            canonical_json_hash_v2(&lexical[0]).unwrap(),
            canonical_json_hash_v2(&former_representation[0]).unwrap()
        );

        assert_eq!(
            replay_trace_hash(&lexical).unwrap(),
            replay_trace_hash(&former_representation).unwrap()
        );
        assert_eq!(
            logical_trace_hash_v2(&lexical).unwrap(),
            logical_trace_hash_v2(&former_representation).unwrap()
        );
        assert_ne!(
            replay_trace_hash_v2(&lexical).unwrap(),
            replay_trace_hash_v2(&former_representation).unwrap()
        );
        assert_ne!(
            logical_trace_hash_v3(&lexical).unwrap(),
            logical_trace_hash_v3(&former_representation).unwrap()
        );
    }

    #[test]
    fn canonical_json_hash_rejects_non_finite_floats_instead_of_hashing_null() {
        #[derive(Serialize)]
        struct Measurement {
            value: f64,
        }

        let null_hash = canonical_json_hash(&json!({"value": null})).unwrap();
        assert_eq!(null_hash.len(), 64);

        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            let error = canonical_json_hash(&Measurement { value }).unwrap_err();
            assert!(canonical_json_hash_v2(&Measurement { value }).is_err());
            assert!(
                error.to_string().contains("finite JSON"),
                "unexpected validation error: {error:#}"
            );
        }
    }

    #[test]
    fn write_json_file_does_not_create_destination_for_non_finite_value() {
        let path = unique_temp_path("nonfinite-new");
        let _ = std::fs::remove_file(&path);

        let error = write_json_file(&path, &metric_event(f64::NAN)).unwrap_err();

        assert!(format!("{error:#}").contains("non-finite"));
        assert!(!path.exists(), "invalid value created {}", path.display());
    }

    #[test]
    fn write_json_file_does_not_truncate_destination_for_non_finite_value() {
        let path = unique_temp_path("nonfinite-existing");
        std::fs::write(&path, b"sentinel").unwrap();

        let error = write_json_file(&path, &metric_event(f64::INFINITY)).unwrap_err();
        let contents = std::fs::read(&path).unwrap();
        let _ = std::fs::remove_file(&path);

        assert!(format!("{error:#}").contains("non-finite"));
        assert_eq!(contents, b"sentinel");
    }

    #[test]
    fn sidecar_types_reject_unknown_fields() {
        let mut summary =
            serde_json::to_value(summarize_events(&sample_events()).unwrap()).unwrap();
        summary
            .as_object_mut()
            .unwrap()
            .insert("unexpected".to_string(), true.into());

        let error = serde_json::from_value::<RunLogSummary>(summary).unwrap_err();

        assert!(error.to_string().contains("unknown field `unexpected`"));
    }

    #[test]
    fn runlog_contract_lists_current_schema_surface() {
        let contract = runlog_contract();
        assert_eq!(contract.schema_version, RUN_LOG_SCHEMA_VERSION);
        assert_eq!(contract.event_types.len(), RUN_LOG_EVENT_TYPES.len());
        assert!(contract
            .event_types
            .iter()
            .any(|event| event.event_type == "bridge_request"
                && event.has_step
                && event.carries_payload_hash));
        assert!(contract
            .event_types
            .iter()
            .any(|event| event.event_type == "evaluation_metric" && event.has_step));
        assert!(contract
            .event_types
            .iter()
            .any(|event| event.event_type == "label_observed" && event.has_step));
        assert!(contract
            .event_types
            .iter()
            .any(|event| event.event_type == "embedding_contract" && !event.has_step));
        assert!(contract
            .event_types
            .iter()
            .any(|event| event.event_type == "flow_pred" && event.has_step));
        assert!(contract.sidecars.contains(&"manifest".to_string()));
        assert!(contract.actor_types.contains(&"llm_tool".to_string()));
    }

    #[test]
    fn malformed_json_reports_line_number() {
        let mut writer = RunLogWriter::new(Vec::new());
        writer.append(&sample_events()[0]).unwrap();
        let mut bytes = writer.into_inner();
        bytes.extend_from_slice(b"not-json\n");
        let err = read_events(Cursor::new(bytes)).unwrap_err();
        let msg = format!("{err:#}");
        assert!(msg.contains("line 2"));
    }

    #[test]
    fn sidecar_paths_append_suffixes_to_runlog_name() {
        let paths = runlog_sidecar_paths("outputs/demo.jsonl");
        assert_eq!(
            paths.validation,
            PathBuf::from("outputs/demo.jsonl.validation.json")
        );
        assert_eq!(
            paths.summary,
            PathBuf::from("outputs/demo.jsonl.summary.json")
        );
        assert_eq!(
            paths.manifest,
            PathBuf::from("outputs/demo.jsonl.manifest.json")
        );
    }

    #[cfg(unix)]
    #[test]
    fn non_utf8_runlog_names_remain_distinct_and_manifests_fail_closed() {
        use std::os::unix::ffi::{OsStrExt, OsStringExt};

        let template = unique_temp_path("non-utf8-source");
        let parent = template.parent().unwrap();
        let base = template.file_name().unwrap().as_bytes();
        let events = sample_events();
        let state = replay_events(&events).unwrap();
        let summary = summarize_events(&events).unwrap();
        let mut paths = Vec::new();
        for invalid_byte in [0xfe, 0xff] {
            let mut name = base.to_vec();
            name.push(invalid_byte);
            let path = parent.join(std::ffi::OsString::from_vec(name.clone()));
            let sidecars = runlog_sidecar_paths(&path);
            let mut expected_validation = name;
            expected_validation.extend_from_slice(b".validation.json");
            assert_eq!(
                sidecars.validation.file_name().unwrap().as_bytes(),
                expected_validation
            );

            let error = manifest_from_parts(
                &path,
                &state,
                summary.clone(),
                sha256_hex(b"run log"),
                Vec::new(),
                RunLogLimits::default(),
            )
            .unwrap_err();
            assert!(format!("{error:#}").contains("valid UTF-8"));
            paths.push((path, sidecars));
        }

        assert_ne!(paths[0].1.validation, paths[1].1.validation);
    }

    #[cfg(unix)]
    #[test]
    fn sidecar_writes_reject_every_static_input_alias_before_mutation() {
        use std::os::unix::fs::symlink;

        for target_kind in ["validation", "summary", "manifest"] {
            let input = unique_temp_path(&format!("sidecar-input-alias-{target_kind}"));
            let outputs = runlog_sidecar_paths(&input);
            let target = match target_kind {
                "validation" => &outputs.validation,
                "summary" => &outputs.summary,
                "manifest" => &outputs.manifest,
                _ => unreachable!(),
            };
            let mut writer = RunLogWriter::create(target).unwrap();
            for event in sample_events() {
                writer.append(&event).unwrap();
            }
            writer.flush().unwrap();
            drop(writer);
            let original = std::fs::read(target).unwrap();
            symlink(target, &input).unwrap();

            let error = write_sidecars_for_path(&input).unwrap_err();

            assert!(format!("{error:#}").contains("refusing to replace run-log input"));
            assert_eq!(std::fs::read(target).unwrap(), original);
            let _ = std::fs::remove_file(&input);
            for output in [&outputs.validation, &outputs.summary, &outputs.manifest] {
                let _ = std::fs::remove_file(output);
            }
        }
    }

    #[test]
    fn write_sidecars_emits_validation_summary_and_manifest() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("pid-runlog-sidecars-{stamp}.jsonl"));
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();

        let paths = write_sidecars_for_path(&path).unwrap();
        let validation: ValidationReport =
            serde_json::from_reader(File::open(&paths.validation).unwrap()).unwrap();
        let summary: RunLogSummary =
            serde_json::from_reader(File::open(&paths.summary).unwrap()).unwrap();
        let manifest: RunManifest =
            serde_json::from_reader(File::open(&paths.manifest).unwrap()).unwrap();

        assert!(validation.is_valid(), "{:?}", validation.issues);
        assert_eq!(summary.run_id.as_deref(), Some("run-1"));
        assert_eq!(manifest.event_count, summary.event_count);
        assert_eq!(manifest.trace_hash, summary.trace_hash);
        assert_eq!(manifest.trace_hash_v2, summary.trace_hash_v2);
        assert_eq!(
            manifest.logical_trace_hash_v3,
            summary.logical_trace_hash_v3
        );
        assert_eq!(manifest.config_hash, summary.config_hash);
        assert_eq!(summary.trace_hash_v2.len(), 64);
        assert_eq!(summary.logical_trace_hash_v3.len(), 64);
        let expected_file_hash = sha256_file(&path).unwrap();
        assert_eq!(
            manifest.run_log_sha256.as_deref(),
            Some(expected_file_hash.as_str())
        );

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn path_manifest_hashes_the_same_stream_it_inspects() {
        let path = unique_temp_path("one-open-manifest");
        let events = sample_events();
        let mut writer = RunLogWriter::new(Vec::new());
        for event in &events {
            writer.append(event).unwrap();
        }
        let bytes = writer.into_inner();
        std::fs::write(&path, &bytes).unwrap();

        let hashed = inspect_path_with_hash(&path, RunLogLimits::default()).unwrap();
        let manifest = manifest_for_path(&path).unwrap();

        assert_eq!(hashed.file_sha256, sha256_hex(&bytes));
        assert_eq!(
            hashed.inspection.hash_identities.replay_lossless.digest,
            replay_trace_hash_v2(&events).unwrap()
        );
        assert_eq!(
            manifest.run_log_sha256.as_deref(),
            Some(hashed.file_sha256.as_str())
        );
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn hashed_path_inspection_rejects_a_source_changed_after_reading() {
        let path = unique_temp_path("changed-during-inspection");
        let events = sample_events();
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in &events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);

        let error = inspect_path_with_hash_and_hook(&path, RunLogLimits::default(), || {
            std::fs::write(&path, b"changed after the streaming pass")
                .context("failed to mutate run-log test source")?;
            Ok(())
        })
        .unwrap_err();

        assert_eq!(
            error.downcast_ref::<RunLogError>(),
            Some(&RunLogError::SourceChangedDuringInspection)
        );
        let _ = std::fs::remove_file(path);
    }

    #[cfg(unix)]
    #[test]
    fn hashed_path_inspection_rejects_path_retargeting_after_reading() {
        let path = unique_temp_path("retargeted-during-inspection");
        let replacement = unique_temp_path("retargeted-replacement");
        let events = sample_events();
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in &events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);
        std::fs::write(&replacement, b"replacement inode").unwrap();

        let error = inspect_path_with_hash_and_hook(&path, RunLogLimits::default(), || {
            std::fs::rename(&replacement, &path).context("failed to retarget run-log test path")?;
            Ok(())
        })
        .unwrap_err();

        assert_eq!(
            error.downcast_ref::<RunLogError>(),
            Some(&RunLogError::SourceChangedDuringInspection)
        );
        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(replacement);
    }

    #[test]
    fn manifest_for_events_rejects_events_from_a_different_source() {
        let path = unique_temp_path("manifest-source-binding");
        let events = sample_events();
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in &events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);

        let matching = manifest_for_events(&path, &events).unwrap();
        assert_eq!(matching.event_count, events.len());

        let mut different = events.clone();
        if let RunLogEvent::PidMetric { value, .. } = &mut different[8] {
            *value = 0.5;
        } else {
            panic!("sample event layout changed");
        }
        let error = manifest_for_events(&path, &different).unwrap_err();
        assert_eq!(
            error.downcast_ref::<RunLogError>(),
            Some(&RunLogError::ManifestSourceMismatch)
        );

        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn verify_sidecars_accepts_current_sidecars() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("pid-runlog-verify-sidecars-{stamp}.jsonl"));
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();

        let paths = write_sidecars_for_path(&path).unwrap();
        let report = verify_sidecars_for_path(&path).unwrap();
        assert!(report.is_valid(), "{:?}", report.issues);
        assert_eq!(report.checked, 3);

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn verify_sidecars_rejects_missing_schema_two_identity_fields() {
        let path = unique_temp_path("verify-schema-two-identities");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);

        let paths = write_sidecars_for_path(&path).unwrap();
        for (sidecar_name, sidecar_path, field) in [
            ("summary", &paths.summary, "trace_hash_v2"),
            ("summary", &paths.summary, "logical_trace_hash_v3"),
            ("summary", &paths.summary, "hash_identities"),
            ("manifest", &paths.manifest, "trace_hash_v2"),
            ("manifest", &paths.manifest, "logical_trace_hash_v3"),
            ("manifest", &paths.manifest, "hash_identities"),
            ("manifest", &paths.manifest, "run_log_hash"),
        ] {
            let original: serde_json::Value =
                serde_json::from_reader(File::open(sidecar_path).unwrap()).unwrap();
            assert_eq!(
                original["sidecar_schema_version"],
                json!(RUN_LOG_SIDECAR_SCHEMA_VERSION)
            );
            let mut stripped = original.clone();
            assert!(
                stripped.as_object_mut().unwrap().remove(field).is_some(),
                "{sidecar_name} did not contain {field}"
            );
            write_json_file(sidecar_path, &stripped).unwrap();

            let report = verify_sidecars_for_path(&path).unwrap();

            assert!(!report.is_valid(), "{sidecar_name}.{field} was forgiven");
            assert!(report
                .issues
                .iter()
                .any(|issue| issue.sidecar == sidecar_name));
            write_json_file(sidecar_path, &original).unwrap();
        }
        let restored = verify_sidecars_for_path(&path).unwrap();
        assert!(restored.is_valid(), "{:?}", restored.issues);

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn verify_sidecars_rejects_explicit_schema_downgrade() {
        let path = unique_temp_path("verify-sidecar-downgrade");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);

        let paths = write_sidecars_for_path(&path).unwrap();
        let mut downgraded: serde_json::Value =
            serde_json::from_reader(File::open(&paths.summary).unwrap()).unwrap();
        let object = downgraded.as_object_mut().unwrap();
        object.insert("sidecar_schema_version".to_string(), json!(1));
        object.remove("hash_identities");
        write_json_file(&paths.summary, &downgraded).unwrap();

        let report = verify_sidecars_for_path(&path).unwrap();

        assert!(!report.is_valid());
        assert!(report.issues.iter().any(|issue| issue.sidecar == "summary"));

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn numbers_above_finite_f64_summarize_write_and_verify_lossless_sidecars() {
        let config: serde_json::Value = serde_json::from_str(r#"{"limit":1e400}"#).unwrap();
        let payload: serde_json::Value = serde_json::from_str(r#"{"magnitude":1e400}"#).unwrap();
        assert!(canonical_json_hash(&config).is_err());
        assert!(canonical_json_hash(&payload).is_err());
        let config_hash = canonical_json_hash_v2(&config).unwrap();
        let payload_hash = canonical_json_hash_v2(&payload).unwrap();
        let events = vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "above-f64".to_string(),
                timestamp_ns: 1,
                config_hash: config_hash.clone(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash,
                config,
            },
            RunLogEvent::ActionApplied {
                step: 0,
                timestamp_ns: 2,
                actor: actor(),
                action_type: "large-number".to_string(),
                payload_hash,
                payload,
            },
            RunLogEvent::RunEnded {
                run_id: "above-f64".to_string(),
                timestamp_ns: 3,
                status: RunStatus::Succeeded,
                message: None,
            },
        ];
        let validation = validate_events(&events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        assert!(replay_trace_hash(&events).is_err());
        assert!(logical_trace_hash(&events).is_err());

        let summary = summarize_events(&events).unwrap();
        assert!(summary.trace_hash.is_empty());
        assert!(summary.logical_trace_hash.is_empty());
        assert_eq!(
            summary.trace_hash_v2,
            replay_trace_hash_v2(&events).unwrap()
        );
        assert_eq!(
            summary.logical_trace_hash_v3,
            logical_trace_hash_v3(&events).unwrap()
        );
        let identities = summary.hash_identities.as_ref().unwrap();
        assert!(identities.replay_legacy.is_none());
        assert!(identities.logical_legacy.is_none());

        let path = unique_temp_path("above-f64-sidecars");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in &events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);

        let paths = write_sidecars_for_path(&path).unwrap();
        let written_summary: RunLogSummary =
            serde_json::from_reader(File::open(&paths.summary).unwrap()).unwrap();
        let written_manifest: RunManifest =
            serde_json::from_reader(File::open(&paths.manifest).unwrap()).unwrap();
        assert_eq!(written_summary.trace_hash_v2, summary.trace_hash_v2);
        assert_eq!(
            written_manifest.logical_trace_hash_v3,
            summary.logical_trace_hash_v3
        );
        let report = verify_sidecars_for_path(&path).unwrap();
        assert!(report.is_valid(), "{:?}", report.issues);

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn verify_sidecars_accepts_unmarked_schema_one_sidecars() {
        let path = unique_temp_path("verify-old-sidecars");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();

        let paths = write_sidecars_for_path(&path).unwrap();
        for sidecar_path in [&paths.summary, &paths.manifest] {
            let mut value: serde_json::Value =
                serde_json::from_reader(File::open(sidecar_path).unwrap()).unwrap();
            let object = value.as_object_mut().unwrap();
            for field in [
                "sidecar_schema_version",
                "trace_hash_v2",
                "logical_trace_hash_v3",
                "hash_identities",
                "run_log_hash",
            ] {
                object.remove(field);
            }
            write_json_file(sidecar_path, &value).unwrap();
        }

        let old_summary: RunLogSummary =
            serde_json::from_reader(File::open(&paths.summary).unwrap()).unwrap();
        let old_manifest: RunManifest =
            serde_json::from_reader(File::open(&paths.manifest).unwrap()).unwrap();
        assert!(old_summary.trace_hash_v2.is_empty());
        assert!(old_summary.logical_trace_hash_v3.is_empty());
        assert_eq!(old_summary.sidecar_schema_version, 1);
        assert!(old_summary.hash_identities.is_none());
        assert!(old_manifest.trace_hash_v2.is_empty());
        assert!(old_manifest.logical_trace_hash_v3.is_empty());
        assert_eq!(old_manifest.sidecar_schema_version, 1);
        assert!(old_manifest.hash_identities.is_none());
        assert!(old_manifest.run_log_hash.is_none());

        let report = verify_sidecars_for_path(&path).unwrap();
        assert!(report.is_valid(), "{:?}", report.issues);
        assert_eq!(report.checked, 3);

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn verify_sidecars_reports_extra_summary_fields() {
        let stamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let path = std::env::temp_dir().join(format!("pid-runlog-stale-sidecar-{stamp}.jsonl"));
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();

        let paths = write_sidecars_for_path(&path).unwrap();
        let mut stale_summary: serde_json::Value =
            serde_json::from_reader(File::open(&paths.summary).unwrap()).unwrap();
        stale_summary
            .as_object_mut()
            .unwrap()
            .insert("stale_extra_field".to_string(), true.into());
        write_json_file(&paths.summary, &stale_summary).unwrap();

        let report = verify_sidecars_for_path(&path).unwrap();
        assert!(!report.is_valid());
        assert!(report.issues.iter().any(|issue| {
            issue.sidecar == "summary" && issue.message.contains("does not match")
        }));

        let _ = std::fs::remove_file(path);
        let _ = std::fs::remove_file(paths.validation);
        let _ = std::fs::remove_file(paths.summary);
        let _ = std::fs::remove_file(paths.manifest);
    }

    #[test]
    fn bounded_reader_rejects_a_line_before_exceeding_its_limit() {
        let input = format!("{}\n", "x".repeat(65));
        let limits = RunLogLimits {
            max_line_bytes: 64,
            ..RunLogLimits::default()
        };

        let error = read_events_with_limits(Cursor::new(input), limits).unwrap_err();

        assert!(format!("{error:#}").contains("run-log line bytes"));
    }

    #[test]
    fn bounded_reader_rejects_event_count_over_budget() {
        let input = include_bytes!("../tests/fixtures/schema_v1_minimal.jsonl");
        let limits = RunLogLimits {
            max_events: 1,
            ..RunLogLimits::default()
        };

        let error = read_events_with_limits(Cursor::new(input), limits).unwrap_err();

        assert!(format!("{error:#}").contains("event count"));
    }

    #[test]
    fn bounded_path_reader_rejects_file_size_from_metadata() {
        let path = unique_temp_path("oversized-runlog");
        let input = include_bytes!("../tests/fixtures/schema_v1_minimal.jsonl");
        std::fs::write(&path, input).unwrap();
        let limits = RunLogLimits {
            max_file_bytes: u64::try_from(input.len() - 1).unwrap(),
            ..RunLogLimits::default()
        };

        let error = inspect_path_with_limits(&path, limits).unwrap_err();

        assert!(format!("{error:#}").contains("run-log file bytes"));
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn bounded_reader_rejects_encoded_string_over_budget() {
        let line = r#"{"type":"run_started","schema_version":1,"run_id":"too-long","timestamp_ns":1,"config_hash":"","metadata":{}}"#;
        let limits = RunLogLimits {
            max_string_bytes: 7,
            ..RunLogLimits::default()
        };

        let error = read_events_with_limits(Cursor::new(line), limits).unwrap_err();

        assert!(format!("{error:#}").contains("JSON string bytes"));
    }

    #[test]
    fn bounded_reader_rejects_array_over_budget() {
        let line = r#"{"type":"config_logged","timestamp_ns":1,"config_hash":"","config":{"items":[1,2]}}"#;
        let limits = RunLogLimits {
            max_array_len: 1,
            ..RunLogLimits::default()
        };

        let error = read_events_with_limits(Cursor::new(line), limits).unwrap_err();

        assert!(format!("{error:#}").contains("JSON array length"));
    }

    #[test]
    fn bounded_reader_rejects_nesting_before_json_deserialization() {
        let line = r#"{"type":"config_logged","timestamp_ns":1,"config_hash":"","config":{"a":{"b":{"c":1}}}}"#;
        let limits = RunLogLimits {
            max_nesting_depth: 3,
            ..RunLogLimits::default()
        };

        let error = read_events_with_limits(Cursor::new(line), limits).unwrap_err();

        assert!(format!("{error:#}").contains("JSON nesting depth"));
    }

    #[test]
    fn bounded_writer_rejects_before_creating_destination() {
        let path = unique_temp_path("bounded-json-writer");
        let _ = std::fs::remove_file(&path);
        let limits = RunLogLimits::default().with_max_file_bytes(32);

        let error = write_json_file_with_limits(
            &path,
            &json!({"payload": "this value is deliberately longer than thirty-two bytes"}),
            limits,
        )
        .unwrap_err();

        assert!(format!("{error:#}").contains("JSON output bytes"));
        assert!(!path.exists());
    }

    #[test]
    fn decoded_in_memory_apis_enforce_aggregate_limits() {
        let events = sample_events();
        let limits = RunLogLimits::default().with_max_events(1);

        assert!(replay_events_with_limits(&events, limits).is_err());
        assert!(validate_events_with_limits(&events, limits).is_err());

        let tiny_hash_budget = RunLogLimits::default().with_max_file_bytes(8);
        assert!(canonical_json_hash_v2_with_limits(
            &json!({"payload": "bounded"}),
            tiny_hash_budget,
        )
        .is_err());

        let event = sample_events().remove(0);
        let compact_bytes = serde_json::to_vec(&event).unwrap().len() as u64;
        let jsonl_boundary = RunLogLimits::default().with_max_file_bytes(compact_bytes);
        let events = [event.clone()];
        assert!(replay_events_with_limits(&events, jsonl_boundary).is_err());
        assert!(validate_events_with_limits(&events, jsonl_boundary).is_err());
        assert!(summarize_events_with_limits(&events, jsonl_boundary).is_err());
        assert!(replay_trace_hash_v2_with_limits(&events, jsonl_boundary).is_err());
        assert!(logical_trace_hash_v3_with_limits(&events, jsonl_boundary).is_err());
        let mut replay = ReplayState::default();
        assert!(replay.apply_with_limits(&event, jsonl_boundary).is_err());
    }

    #[test]
    fn decoded_in_memory_apis_enforce_event_line_limit() {
        let event = sample_events().remove(0);
        let encoded_len = serde_json::to_vec(&event).unwrap().len();
        let limits = RunLogLimits::default().with_max_line_bytes(encoded_len - 1);
        let events = [event.clone()];

        let assert_line_limited = |error: anyhow::Error| {
            assert!(
                format!("{error:#}").contains("line bytes"),
                "unexpected error: {error:#}"
            );
        };
        assert_line_limited(validate_events_with_limits(&events, limits).unwrap_err());
        assert_line_limited(replay_events_with_limits(&events, limits).unwrap_err());
        let mut replay = ReplayState::default();
        assert_line_limited(replay.apply_with_limits(&event, limits).unwrap_err());
        assert_line_limited(summarize_events_with_limits(&events, limits).unwrap_err());
        assert_line_limited(replay_trace_hash_with_limits(&events, limits).unwrap_err());
        assert_line_limited(replay_trace_hash_v2_with_limits(&events, limits).unwrap_err());
        assert_line_limited(logical_trace_hash_with_limits(&events, limits).unwrap_err());
        assert_line_limited(logical_trace_hash_v2_with_limits(&events, limits).unwrap_err());
        assert_line_limited(logical_trace_hash_v3_with_limits(&events, limits).unwrap_err());
        assert_line_limited(canonical_json_hash_with_limits(&event, limits).unwrap_err());
        assert_line_limited(canonical_json_hash_v2_with_limits(&event, limits).unwrap_err());
    }

    #[test]
    fn explicit_limits_reach_validation_summary_and_every_trace_hash() {
        let default_limits = RunLogLimits::default();
        let large_text = "x".repeat(default_limits.max_string_bytes + 1);
        let limits = default_limits.with_max_string_bytes(large_text.len());
        let config = json!({"description": large_text.clone()});
        let config_hash = canonical_json_hash_v2_with_limits(&config, limits).unwrap();
        let payload = json!({"blob": large_text});
        let payload_hash = canonical_json_hash_v2_with_limits(&payload, limits).unwrap();
        let events = vec![
            RunLogEvent::RunStarted {
                schema_version: RUN_LOG_SCHEMA_VERSION,
                run_id: "raised-limits".to_string(),
                timestamp_ns: 1,
                config_hash: config_hash.clone(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash,
                config,
            },
            RunLogEvent::ActionApplied {
                step: 0,
                timestamp_ns: 2,
                actor: actor(),
                action_type: "large-payload".to_string(),
                payload_hash,
                payload,
            },
            RunLogEvent::RunEnded {
                run_id: "raised-limits".to_string(),
                timestamp_ns: 3,
                status: RunStatus::Succeeded,
                message: None,
            },
        ];

        assert!(validate_events(&events).is_err());
        assert!(validate_events_with_limits(&events, limits)
            .unwrap()
            .is_valid());
        let summary = summarize_events_with_limits(&events, limits).unwrap();
        assert_eq!(summary.event_count, events.len());
        assert_eq!(
            replay_trace_hash_with_limits(&events, limits).unwrap(),
            summary.trace_hash
        );
        assert_eq!(
            replay_trace_hash_v2_with_limits(&events, limits).unwrap(),
            summary.trace_hash_v2
        );
        assert_eq!(
            logical_trace_hash_with_limits(&events, limits).unwrap(),
            summary.logical_trace_hash
        );
        assert!(logical_trace_hash_v2_with_limits(&events, limits).is_ok());
        assert_eq!(
            logical_trace_hash_v3_with_limits(&events, limits).unwrap(),
            summary.logical_trace_hash_v3
        );

        let path = unique_temp_path("raised-limits");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in &events {
            writer.append_with_limits(event, limits).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);
        let inspection = inspect_path_with_limits(&path, limits).unwrap();
        assert_eq!(
            inspection.hash_identities.replay_lossless.digest,
            summary.trace_hash_v2
        );
        let manifest = manifest_for_events_with_limits(&path, &events, limits).unwrap();
        assert_eq!(manifest.event_count, events.len());
        let mut migrated = Vec::new();
        let report = migrate_runlog(
            Cursor::new(std::fs::read(&path).unwrap()),
            &mut migrated,
            limits,
        )
        .unwrap();
        assert_eq!(report.events, events.len());
        let migrated = read_events_with_limits(Cursor::new(migrated), limits).unwrap();
        let validation = validate_events_with_limits(&migrated, limits).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn bounded_file_hash_rejects_over_limit_and_accepts_exact_size() {
        let path = unique_temp_path("bounded-hash");
        let bytes = b"bounded artifact";
        std::fs::write(&path, bytes).unwrap();

        let error = sha256_file_with_limit(&path, bytes.len() as u64 - 1).unwrap_err();
        assert!(format!("{error:#}").contains("artifact hash bytes"));
        assert_eq!(
            sha256_file_with_limit(&path, bytes.len() as u64).unwrap(),
            sha256_hex(bytes)
        );
        assert!(sha256_file_with_limit(&path, 0).is_err());

        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn replay_state_enforces_aggregate_collection_limits() {
        let label = |step, name: &str| RunLogEvent::LabelObserved {
            step,
            timestamp_ns: step + 1,
            name: name.to_string(),
            value: json!(step),
            metadata: BTreeMap::new(),
        };
        let array_limits = RunLogLimits::default().with_max_array_len(1);
        let mut labels = ReplayState::default();
        labels
            .apply_with_limits(&label(0, "a"), array_limits)
            .unwrap();
        let labels_before_error = labels.clone();
        let error = labels
            .apply_with_limits(&label(1, "b"), array_limits)
            .unwrap_err();
        assert!(format!("{error:#}").contains("replay label count"));
        assert_eq!(labels, labels_before_error);

        let metric = |step, name: &str| RunLogEvent::GeometryMetric {
            step,
            timestamp_ns: step + 1,
            name: name.to_string(),
            value: step as f64,
            metadata: BTreeMap::new(),
        };
        // GeometryMetric has six top-level JSON fields, so a limit of six accepts each event but
        // rejects the seventh distinct retained key.
        let object_limits = RunLogLimits::default().with_max_object_entries(6);
        let mut metrics = ReplayState::default();
        for index in 0..6 {
            metrics
                .apply_with_limits(&metric(index, &format!("metric-{index}")), object_limits)
                .unwrap();
        }
        let metrics_before_error = metrics.clone();
        let error = metrics
            .apply_with_limits(&metric(6, "metric-6"), object_limits)
            .unwrap_err();
        assert!(format!("{error:#}").contains("replay geometry metric keys"));
        assert_eq!(metrics, metrics_before_error);
    }

    #[test]
    fn typed_float_rejects_lossy_integer_input() {
        for integer in [
            "9007199254740993",
            "340282366920938463463374607431768211455",
            "-170141183460469231731687303715884105727",
        ] {
            let line = format!(
                r#"{{"type":"pid_metric","step":0,"timestamp_ns":1,"name":"x","value":{integer},"metadata":{{}}}}"#
            );

            let error = read_events(Cursor::new(line)).unwrap_err();

            assert!(
                format!("{error:#}").contains("cannot be represented exactly as f64"),
                "unexpected error for {integer}: {error:#}"
            );
        }
    }

    #[test]
    fn typed_float_accepts_exact_large_integer_input() {
        for integer in [
            "9007199254740992",
            "170141183460469231731687303715884105728",
            "-170141183460469231731687303715884105728",
        ] {
            let line = format!(
                r#"{{"type":"pid_metric","step":0,"timestamp_ns":1,"name":"x","value":{integer},"metadata":{{}}}}"#
            );

            let events = read_events(Cursor::new(line)).unwrap();

            assert!(matches!(
                events.as_slice(),
                [RunLogEvent::PidMetric { value, .. }]
                    if *value == integer.parse::<f64>().unwrap()
            ));
        }
    }

    #[test]
    fn streaming_inspection_matches_in_memory_replay_and_hashes() {
        let events = sample_events();
        let mut writer = RunLogWriter::new(Vec::new());
        for event in &events {
            writer.append(event).unwrap();
        }

        let inspection =
            inspect_event_stream(Cursor::new(writer.into_inner()), RunLogLimits::default())
                .unwrap();

        assert_eq!(inspection.replay_state, replay_events(&events).unwrap());
        assert_eq!(
            inspection.hash_identities.replay_lossless.digest,
            replay_trace_hash_v2(&events).unwrap()
        );
        assert_eq!(
            inspection.hash_identities.logical_lossless.digest,
            logical_trace_hash_v3(&events).unwrap()
        );
    }

    #[test]
    fn schema_one_golden_fixture_is_bounded_and_migratable() {
        let input = include_bytes!("../tests/fixtures/schema_v1_minimal.jsonl");
        let inspection = inspect_event_stream(Cursor::new(input), RunLogLimits::default()).unwrap();
        assert!(
            inspection.validation.is_valid(),
            "{:?}",
            inspection.validation.issues
        );

        let mut migrated = Vec::new();
        let report =
            migrate_runlog(Cursor::new(input), &mut migrated, RunLogLimits::default()).unwrap();
        assert_eq!(
            migrated,
            include_bytes!("../tests/fixtures/schema_v1_migrated_v2.jsonl")
        );
        let migrated_events = read_events(Cursor::new(&migrated)).unwrap();

        assert_eq!(report.from_schema, 1);
        assert!(matches!(
            migrated_events.first(),
            Some(RunLogEvent::RunStarted { schema_version, .. })
                if *schema_version == RUN_LOG_SCHEMA_VERSION
        ));
        let validation = validate_events(&migrated_events).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
    }

    #[test]
    fn migration_rejects_schema_one_without_preoperational_config() {
        let legacy = vec![
            RunLogEvent::RunStarted {
                schema_version: MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION,
                run_id: "legacy-without-config".to_string(),
                timestamp_ns: 1,
                config_hash: String::new(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::RunEnded {
                run_id: "legacy-without-config".to_string(),
                timestamp_ns: 2,
                status: RunStatus::Succeeded,
                message: None,
            },
        ];
        let validation = validate_events(&legacy).unwrap();
        assert!(validation.is_valid(), "{:?}", validation.issues);
        let mut encoded = RunLogWriter::new(Vec::new());
        for event in &legacy {
            encoded.append(event).unwrap();
        }
        let mut migrated = Vec::new();

        let error = migrate_runlog(
            Cursor::new(encoded.into_inner()),
            &mut migrated,
            RunLogLimits::default(),
        )
        .unwrap_err();

        assert!(format!("{error:#}").contains("without exactly one config_logged event"));
        assert!(migrated.is_empty());
    }

    #[test]
    fn migration_reanchors_schema_one_config_and_payload_hashes_to_v2() {
        let config: serde_json::Value = serde_json::from_str(r#"{"rate":1E+02}"#).unwrap();
        let payload: serde_json::Value = serde_json::from_str(r#"{"gain":0.2500}"#).unwrap();
        let config_v1 = canonical_json_hash(&config).unwrap();
        let payload_v1 = canonical_json_hash(&payload).unwrap();
        assert_ne!(config_v1, canonical_json_hash_v2(&config).unwrap());
        assert_ne!(payload_v1, canonical_json_hash_v2(&payload).unwrap());
        let legacy = vec![
            RunLogEvent::RunStarted {
                schema_version: MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION,
                run_id: "migration-hashes".to_string(),
                timestamp_ns: 1,
                config_hash: config_v1.clone(),
                metadata: BTreeMap::new(),
            },
            RunLogEvent::ConfigLogged {
                timestamp_ns: 1,
                config_hash: config_v1,
                config: config.clone(),
            },
            RunLogEvent::ActionApplied {
                step: 0,
                timestamp_ns: 2,
                actor: actor(),
                action_type: "set-gain".to_string(),
                payload_hash: payload_v1,
                payload: payload.clone(),
            },
            RunLogEvent::RunEnded {
                run_id: "migration-hashes".to_string(),
                timestamp_ns: 3,
                status: RunStatus::Succeeded,
                message: None,
            },
        ];
        let mut encoded = RunLogWriter::new(Vec::new());
        for event in &legacy {
            encoded.append(event).unwrap();
        }
        let mut migrated = Vec::new();

        migrate_runlog(
            Cursor::new(encoded.into_inner()),
            &mut migrated,
            RunLogLimits::default(),
        )
        .unwrap();
        let migrated = read_events(Cursor::new(migrated)).unwrap();
        let validation = validate_events(&migrated).unwrap();

        assert!(validation.is_valid(), "{:?}", validation.issues);
        assert!(matches!(
            &migrated[0],
            RunLogEvent::RunStarted { config_hash, .. }
                if config_hash == &canonical_json_hash_v2(&config).unwrap()
        ));
        assert!(matches!(
            &migrated[2],
            RunLogEvent::ActionApplied { payload_hash, .. }
                if payload_hash == &canonical_json_hash_v2(&payload).unwrap()
        ));
    }

    #[test]
    fn schema_two_typed_pid_golden_fixture_validates_and_replays() {
        let input = include_bytes!("../tests/fixtures/schema_v2_typed_pid.jsonl");

        let inspection = inspect_event_stream(Cursor::new(input), RunLogLimits::default()).unwrap();

        assert!(
            inspection.validation.is_valid(),
            "{:?}",
            inspection.validation.issues
        );
        assert_eq!(inspection.replay_state.pid_metric_events, 1);
        assert!(inspection
            .replay_state
            .pid_estimates
            .contains_key("redundancy"));
        assert!(inspection.hash_identities.replay_legacy.is_none());
        assert!(inspection.hash_identities.logical_legacy.is_none());
        assert!(inspection
            .hash_identities
            .logical_top_level_clock_legacy
            .is_none());
    }

    #[test]
    fn schema_two_rejects_invalid_artifact_hash_and_parent_traversal() {
        let mut events = sample_events();
        events.insert(
            events.len() - 1,
            RunLogEvent::ArtifactLogged {
                timestamp_ns: 4,
                name: "escape".to_string(),
                kind: "fixture".to_string(),
                uri: "../escape.bin".to_string(),
                sha256: Some("not-a-digest".to_string()),
                metadata: BTreeMap::new(),
            },
        );

        let report = validate_events(&events).unwrap();

        assert!(report.errors >= 2, "{:?}", report.issues);
    }

    #[test]
    fn artifact_locations_reject_cross_platform_and_uri_traversal() {
        for location in [
            "../escape.bin",
            r"..\escape.bin",
            "https://example.invalid/../escape.bin",
            "https://example.invalid/%2e%2e/escape.bin",
            "https://example.invalid/.%2E/escape.bin",
            "https://example.invalid/%2e./escape.bin",
            "https://example.invalid/artifacts%2fescape.bin",
            "https://example.invalid/artifacts%5Cescape.bin",
            "https://example.invalid/artifacts/%00escape.bin",
            "https://example.invalid/artifacts/%20escape.bin",
            "https://example.invalid/artifacts/%",
            "https://example.invalid/artifacts/%2",
            "https://example.invalid/artifacts/%gg",
            "https://example.invalid/artifacts/ok?digest=%gg",
            "https://example.invalid/artifacts/ok#digest=%2",
            "https://example.invalid/artifacts/%C2%A0/escape.bin",
            "https://example.invalid/artifacts/%C2%85/escape.bin",
            "https://example.invalid/artifacts/%FF/escape.bin",
            "https://example.invalid/artifacts/ok?label=%C2%A0",
            "https://example.invalid/artifacts/ok#label=%00",
            "artifacts/evil\u{200b}name.json",
            "artifacts/evil\u{202e}name.json",
            "artifacts/evil\u{2066}name.json",
            "artifacts/evil\u{2028}name.json",
            "artifacts/evil\u{2029}name.json",
            "https://example.invalid/artifacts/%E2%80%8Bname.json",
            "https://example.invalid/artifacts/%E2%80%AEname.json",
            "https://example.invalid/artifacts/%E2%81%A6name.json",
            "https://example.invalid/artifacts/%E2%80%A8name.json",
            "https://example.invalid/artifacts/%E2%80%A9name.json",
            "https:// ",
        ] {
            assert!(
                validate_artifact_location(location).is_err(),
                "unexpectedly accepted {location:?}"
            );
        }
        for location in [
            "artifacts/estimate.json",
            r"artifacts\estimate.json",
            "https://example.invalid/artifacts/estimate.json",
            "https://example.invalid/artifacts/caf%C3%A9.json",
            "https://example.invalid/artifacts/%252e%252e.json",
            "https://example.invalid/artifacts/estimate.json?part=a%2Fb",
            "https://example.invalid/artifacts/estimate.json#percent=%25",
            "artifacts/%2e%2e.json",
        ] {
            assert!(
                validate_artifact_location(location).is_ok(),
                "unexpectedly rejected {location:?}"
            );
        }
    }

    #[test]
    fn summary_exposes_unambiguous_hash_identities() {
        let summary = summarize_events(&sample_events()).unwrap();
        let identities = summary.hash_identities.unwrap();

        assert_eq!(identities.replay_lossless.algorithm, HashAlgorithm::Sha256);
        assert_eq!(
            identities.replay_lossless.revision,
            HashRevision::ReplayTraceV2
        );
        assert_eq!(
            identities.logical_lossless.revision,
            HashRevision::LogicalTraceV3
        );
    }

    #[test]
    fn atomic_write_failure_before_rename_preserves_destination_and_cleans_temp() {
        let path = unique_temp_path("atomic-failure");
        write_json_file(&path, &json!({"generation": "old"})).unwrap();

        let error = atomic_write_bytes_with_hook(&path, br#"{"generation":"new"}"#, |phase| {
            if phase == AtomicWritePhase::DataSynced {
                Err(std::io::Error::other("injected failure"))
            } else {
                Ok(())
            }
        })
        .unwrap_err();
        let actual: serde_json::Value =
            serde_json::from_reader(File::open(&path).unwrap()).unwrap();
        let file_name = path.file_name().unwrap().to_string_lossy();
        let leaked_temp = std::fs::read_dir(path.parent().unwrap())
            .unwrap()
            .filter_map(std::result::Result::ok)
            .any(|entry| {
                entry
                    .file_name()
                    .to_string_lossy()
                    .starts_with(&format!(".{file_name}.pid-runlog-tmp-"))
            });

        assert!(format!("{error:#}").contains("injected failure"));
        assert_eq!(actual, json!({"generation": "old"}));
        assert!(!leaked_temp);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn atomic_write_failure_after_rename_leaves_complete_new_destination() {
        let path = unique_temp_path("atomic-post-rename-failure");
        write_json_file(&path, &json!({"generation": "old"})).unwrap();

        let error = atomic_write_bytes_with_hook(&path, br#"{"generation":"new"}"#, |phase| {
            if phase == AtomicWritePhase::Renamed {
                Err(std::io::Error::other("injected post-rename failure"))
            } else {
                Ok(())
            }
        })
        .unwrap_err();
        let actual: serde_json::Value =
            serde_json::from_reader(File::open(&path).unwrap()).unwrap();
        let file_name = path.file_name().unwrap().to_string_lossy();
        let leaked_temp = std::fs::read_dir(path.parent().unwrap())
            .unwrap()
            .filter_map(std::result::Result::ok)
            .any(|entry| {
                entry
                    .file_name()
                    .to_string_lossy()
                    .starts_with(&format!(".{file_name}.pid-runlog-tmp-"))
            });

        assert!(format!("{error:#}").contains("injected post-rename failure"));
        assert_eq!(actual, json!({"generation": "new"}));
        assert!(!leaked_temp);
        let _ = std::fs::remove_file(path);
    }

    #[test]
    fn manifest_accepts_a_valid_external_anchor() {
        let path = unique_temp_path("external-anchor");
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in sample_events() {
            writer.append(&event).unwrap();
        }
        writer.flush().unwrap();
        let anchor = ExternalAnchor {
            provider: "transparency-log".to_string(),
            uri: "https://example.invalid/entry/1".to_string(),
            anchored_hash: HashIdentity::sha256(HashRevision::FileBytesV1, sha256_hex(b"anchor"))
                .unwrap(),
            signature: Some("detached-signature-reference".to_string()),
        };

        let manifest =
            manifest_for_path_with_anchors(&path, RunLogLimits::default(), vec![anchor]).unwrap();

        assert_eq!(manifest.external_anchors.len(), 1);
        let _ = std::fs::remove_file(path);
    }
}
