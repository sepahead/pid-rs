//! Experimental Rust types for a possible future schema 3 scientific-outcome contract.
//!
//! This project-defined module does not add a PID measure or estimator. Schema 2 remains the
//! active run-log wire format. No event, reader, replay path, sidecar, CLI path, or migration uses
//! these types.
//!
//! Constructors enforce the documented structural rules. Public encoders compute the supported
//! matrix and split identities. Other content identities are caller-supplied. The module does not
//! read external artifacts, consult a trusted method catalog, or prove scientific claims. Direct
//! Serde deserialization is not a bounded run-log reader.
//!
//! Method catalog: software.scientific-outcome-contract-foundation

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use anyhow::Result;
use serde::de::{IgnoredAny, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use super::{canonical_json_hash_v2_with_limits, to_hex, EstimatorIdentity, JsonF64, RunLogLimits};

const CONTRACT_REVISION: u32 = 1;
const MAX_IDENTIFIER_BYTES: usize = 256;
const MAX_EXPLANATION_BYTES: usize = 4 * 1024;
const MAX_EVIDENCE_ITEMS: usize = 1_024;
const MAX_DATA_IDENTITIES: usize = 8;
const MAX_SPLIT_IDENTITIES: usize = 4_096;
const MAX_NAMED_VALUES: usize = 256;
const MAX_TRANSFORMS: usize = 16;
const MAX_REQUEST_OUTCOMES: usize = 65_536;
const MAX_SUPPORT_SETS: usize = (1usize << MAX_DATA_IDENTITIES) - 1;
const F64_MATRIX_IDENTITY_DOMAIN: &[u8] = b"pid-rs/matrix/row-major-f64-bits-le/v1\0";
const U64_MATRIX_IDENTITY_DOMAIN: &[u8] = b"pid-rs/matrix/row-major-u64-le/v1\0";
const SPLIT_MEMBERSHIP_IDENTITY_DOMAIN: &[u8] = b"pid-rs/split-membership/ordered-u64-le/v1\0";

struct BoundedVec<T, const MAX: usize>(Vec<T>);

impl<T, const MAX: usize> BoundedVec<T, MAX> {
    fn into_vec(self) -> Vec<T> {
        self.0
    }
}

struct BoundedVecVisitor<T, const MAX: usize>(std::marker::PhantomData<T>);

impl<'de, T, const MAX: usize> Visitor<'de> for BoundedVecVisitor<T, MAX>
where
    T: Deserialize<'de>,
{
    type Value = BoundedVec<T, MAX>;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "an array with at most {MAX} items")
    }

    fn visit_seq<A>(self, mut sequence: A) -> std::result::Result<Self::Value, A::Error>
    where
        A: SeqAccess<'de>,
    {
        if sequence.size_hint().is_some_and(|hint| hint > MAX) {
            return Err(serde::de::Error::custom(format!(
                "array exceeds {MAX} items"
            )));
        }
        let mut values = Vec::with_capacity(sequence.size_hint().unwrap_or(0).min(MAX));
        while values.len() < MAX {
            let Some(value) = sequence.next_element()? else {
                return Ok(BoundedVec(values));
            };
            values.push(value);
        }
        if sequence.next_element::<IgnoredAny>()?.is_some() {
            return Err(serde::de::Error::custom(format!(
                "array exceeds {MAX} items"
            )));
        }
        Ok(BoundedVec(values))
    }
}

impl<'de, T, const MAX: usize> Deserialize<'de> for BoundedVec<T, MAX>
where
    T: Deserialize<'de>,
{
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_seq(BoundedVecVisitor(std::marker::PhantomData))
    }
}

/// Hash function for a possible future schema 3 scientific identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificHashAlgorithm {
    /// SHA-256.
    Sha256,
}

/// Exact byte contract for a possible future schema 3 scientific hash.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificHashRevision {
    /// The existing lossless canonical JSON v2 contract.
    CanonicalJsonV2,
    /// Raw UTF-8 bytes with no normalization.
    RawUtf8V1,
    /// The row-major binary64 matrix contract implemented in this module.
    RowMajorF64BitsLeV1,
    /// The row-major unsigned 64-bit matrix contract implemented in this module.
    RowMajorU64LeV1,
    /// The ordered unsigned 64-bit split-membership contract implemented in this module.
    SplitMembershipU64LeV1,
}

/// A checked hash identity for a possible future schema.
///
/// This type is separate from the schema 2 [`super::HashIdentity`]. A typed schema 2 hash field
/// cannot use a [`ScientificHashRevision`].
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificHashIdentity {
    algorithm: ScientificHashAlgorithm,
    revision: ScientificHashRevision,
    digest: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificHashIdentityWire {
    algorithm: ScientificHashAlgorithm,
    revision: ScientificHashRevision,
    digest: String,
}

impl ScientificHashIdentity {
    pub fn sha256(revision: ScientificHashRevision, digest: impl Into<String>) -> Result<Self> {
        let digest = digest.into();
        if digest.len() != 64
            || !digest
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            anyhow::bail!("scientific SHA-256 digest must be 64 lowercase hexadecimal characters");
        }
        Ok(Self {
            algorithm: ScientificHashAlgorithm::Sha256,
            revision,
            digest,
        })
    }

    pub fn algorithm(&self) -> ScientificHashAlgorithm {
        self.algorithm
    }

    pub fn revision(&self) -> ScientificHashRevision {
        self.revision
    }

    pub fn digest(&self) -> &str {
        &self.digest
    }

    fn validate(&self) -> Result<()> {
        Self::sha256(self.revision, self.digest.clone()).map(|_| ())
    }
}

impl<'de> Deserialize<'de> for ScientificHashIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificHashIdentityWire::deserialize(deserializer)?;
        if wire.algorithm != ScientificHashAlgorithm::Sha256 {
            return Err(serde::de::Error::custom(
                "unsupported scientific hash algorithm",
            ));
        }
        Self::sha256(wire.revision, wire.digest).map_err(serde::de::Error::custom)
    }
}

fn canonical_scientific_identity<T: Serialize>(value: &T) -> Result<ScientificHashIdentity> {
    let limits = RunLogLimits {
        max_file_bytes: 64 * 1024 * 1024,
        max_line_bytes: 64 * 1024 * 1024,
        max_array_len: MAX_REQUEST_OUTCOMES,
        ..RunLogLimits::default()
    };
    ScientificHashIdentity::sha256(
        ScientificHashRevision::CanonicalJsonV2,
        canonical_json_hash_v2_with_limits(value, limits)?,
    )
}

/// A matrix hash and the shape recorded with that hash.
///
/// A public encoder computes the hash and shape together. Private fields prevent direct field
/// mutation. Deserialization checks the record structure, but it cannot recompute the hash without
/// the original matrix values.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificMatrixIdentity {
    content_hash: ScientificHashIdentity,
    rows: u64,
    columns: u64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificMatrixIdentityWire {
    content_hash: ScientificHashIdentity,
    rows: u64,
    columns: u64,
}

impl ScientificMatrixIdentity {
    fn new(content_hash: ScientificHashIdentity, rows: u64, columns: u64) -> Result<Self> {
        content_hash.validate()?;
        if !matches!(
            content_hash.revision(),
            ScientificHashRevision::RowMajorF64BitsLeV1 | ScientificHashRevision::RowMajorU64LeV1
        ) {
            anyhow::bail!("scientific matrix identity needs a matrix hash revision");
        }
        if rows == 0 || columns == 0 {
            anyhow::bail!("scientific matrix rows and columns must be positive");
        }
        Ok(Self {
            content_hash,
            rows,
            columns,
        })
    }

    /// Return the matrix content hash.
    pub fn content_hash(&self) -> &ScientificHashIdentity {
        &self.content_hash
    }

    /// Return the encoded row count.
    pub fn rows(&self) -> u64 {
        self.rows
    }

    /// Return the encoded column count.
    pub fn columns(&self) -> u64 {
        self.columns
    }
}

impl<'de> Deserialize<'de> for ScientificMatrixIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificMatrixIdentityWire::deserialize(deserializer)?;
        Self::new(wire.content_hash, wire.rows, wire.columns).map_err(serde::de::Error::custom)
    }
}

/// An ordered-membership hash and the counts recorded with that hash.
///
/// A public encoder computes the hash and counts together. Private fields prevent direct field
/// mutation. Deserialization checks the record structure, but it cannot recompute the hash without
/// the original member list.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificMembershipIdentity {
    content_hash: ScientificHashIdentity,
    member_count: u64,
    unique_member_count: u64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificMembershipIdentityWire {
    content_hash: ScientificHashIdentity,
    member_count: u64,
    unique_member_count: u64,
}

impl ScientificMembershipIdentity {
    fn new(
        content_hash: ScientificHashIdentity,
        member_count: u64,
        unique_member_count: u64,
    ) -> Result<Self> {
        content_hash.validate()?;
        if content_hash.revision() != ScientificHashRevision::SplitMembershipU64LeV1 {
            anyhow::bail!("scientific membership identity needs its exact hash revision");
        }
        if member_count == 0 {
            anyhow::bail!("scientific membership count must be positive");
        }
        if unique_member_count == 0 || unique_member_count > member_count {
            anyhow::bail!("scientific unique-member count is inconsistent");
        }
        Ok(Self {
            content_hash,
            member_count,
            unique_member_count,
        })
    }

    /// Return the ordered-membership content hash.
    pub fn content_hash(&self) -> &ScientificHashIdentity {
        &self.content_hash
    }

    /// Return the encoded member count.
    pub fn member_count(&self) -> u64 {
        self.member_count
    }

    /// Return the number of distinct member identifiers.
    pub fn unique_member_count(&self) -> u64 {
        self.unique_member_count
    }
}

impl<'de> Deserialize<'de> for ScientificMembershipIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificMembershipIdentityWire::deserialize(deserializer)?;
        Self::new(
            wire.content_hash,
            wire.member_count,
            wire.unique_member_count,
        )
        .map_err(serde::de::Error::custom)
    }
}

fn validate_matrix_shape(rows: u64, columns: u64, value_count: usize) -> Result<()> {
    if rows == 0 || columns == 0 {
        anyhow::bail!("scientific matrix rows and columns must be positive");
    }
    let expected = u128::from(rows) * u128::from(columns);
    if expected != value_count as u128 {
        anyhow::bail!("scientific matrix shape does not match its value count");
    }
    Ok(())
}

/// Compute the v1 identity for a row-major binary64 matrix.
///
/// The SHA-256 preimage is the domain tag `pid-rs/matrix/row-major-f64-bits-le/v1\0`, the row and
/// column counts as little-endian `u128` values, and each `f64::to_bits()` value as a
/// little-endian `u64`. The function keeps signed zero and each NaN bit pattern distinct.
///
/// # Errors
///
/// Returns an error if a dimension is zero or the shape does not match `values`.
pub fn scientific_f64_matrix_identity_v1(
    rows: u64,
    columns: u64,
    values: &[f64],
) -> Result<ScientificMatrixIdentity> {
    validate_matrix_shape(rows, columns, values.len())?;
    let mut digest = Sha256::new();
    digest.update(F64_MATRIX_IDENTITY_DOMAIN);
    digest.update(u128::from(rows).to_le_bytes());
    digest.update(u128::from(columns).to_le_bytes());
    for value in values {
        digest.update(value.to_bits().to_le_bytes());
    }
    ScientificMatrixIdentity::new(
        ScientificHashIdentity::sha256(
            ScientificHashRevision::RowMajorF64BitsLeV1,
            to_hex(&digest.finalize()),
        )?,
        rows,
        columns,
    )
}

/// Compute the v1 identity for a row-major unsigned 64-bit matrix.
///
/// The SHA-256 preimage is the domain tag `pid-rs/matrix/row-major-u64-le/v1\0`, the row and column
/// counts as little-endian `u128` values, and each value as a little-endian `u64`.
///
/// # Errors
///
/// Returns an error if a dimension is zero or the shape does not match `values`.
pub fn scientific_u64_matrix_identity_v1(
    rows: u64,
    columns: u64,
    values: &[u64],
) -> Result<ScientificMatrixIdentity> {
    validate_matrix_shape(rows, columns, values.len())?;
    let mut digest = Sha256::new();
    digest.update(U64_MATRIX_IDENTITY_DOMAIN);
    digest.update(u128::from(rows).to_le_bytes());
    digest.update(u128::from(columns).to_le_bytes());
    for value in values {
        digest.update(value.to_le_bytes());
    }
    ScientificMatrixIdentity::new(
        ScientificHashIdentity::sha256(
            ScientificHashRevision::RowMajorU64LeV1,
            to_hex(&digest.finalize()),
        )?,
        rows,
        columns,
    )
}

/// Compute the v1 identity for an ordered list of split or resample members.
///
/// The SHA-256 preimage is the domain tag `pid-rs/split-membership/ordered-u64-le/v1\0`, the member
/// count as a little-endian `u128`, and each member as a little-endian `u64`. Order and repeated
/// members are significant.
///
/// # Errors
///
/// Returns an error if `members` is empty or its length cannot fit in `u64`.
pub fn scientific_split_membership_identity_v1(
    members: &[u64],
) -> Result<ScientificMembershipIdentity> {
    if members.is_empty() {
        anyhow::bail!("scientific split membership must be nonempty");
    }
    let mut digest = Sha256::new();
    digest.update(SPLIT_MEMBERSHIP_IDENTITY_DOMAIN);
    digest.update((members.len() as u128).to_le_bytes());
    for member in members {
        digest.update(member.to_le_bytes());
    }
    let member_count = u64::try_from(members.len())
        .map_err(|_| anyhow::anyhow!("scientific split membership exceeds u64"))?;
    let unique_member_count = u64::try_from(members.iter().copied().collect::<BTreeSet<_>>().len())
        .map_err(|_| anyhow::anyhow!("scientific unique split membership exceeds u64"))?;
    ScientificMembershipIdentity::new(
        ScientificHashIdentity::sha256(
            ScientificHashRevision::SplitMembershipU64LeV1,
            to_hex(&digest.finalize()),
        )?,
        member_count,
        unique_member_count,
    )
}

fn validate_machine_text(field: &'static str, value: &str) -> Result<()> {
    if value.is_empty() || value.trim() != value {
        anyhow::bail!("{field} must be nonempty and have no surrounding whitespace");
    }
    if value.len() > MAX_IDENTIFIER_BYTES {
        anyhow::bail!("{field} exceeds {MAX_IDENTIFIER_BYTES} UTF-8 bytes");
    }
    if !value.bytes().all(|byte| {
        byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-' | b'/' | b':')
    }) {
        anyhow::bail!("{field} contains a character outside the machine-text vocabulary");
    }
    Ok(())
}

fn validate_explanation(field: &'static str, value: &str) -> Result<()> {
    if value.is_empty() || value.trim() != value {
        anyhow::bail!("{field} must be nonempty and have no surrounding whitespace");
    }
    if value.len() > MAX_EXPLANATION_BYTES {
        anyhow::bail!("{field} exceeds {MAX_EXPLANATION_BYTES} UTF-8 bytes");
    }
    if value.chars().any(char::is_control) {
        anyhow::bail!("{field} must not contain control characters");
    }
    Ok(())
}

fn validate_estimator_identity(identity: &EstimatorIdentity) -> Result<()> {
    validate_machine_text("estimator family", &identity.family)?;
    validate_machine_text("definition revision", &identity.definition_revision)?;
    validate_machine_text("estimator revision", &identity.estimator_revision)
}

/// A schema name, schema revision, and digest in one record.
///
/// The type checks the record structure. It does not recompute the digest, authenticate bytes, or
/// prove that the named schema was applied correctly.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct VersionedContentIdentity {
    schema: String,
    revision: String,
    content_hash: ScientificHashIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct VersionedContentIdentityWire {
    schema: String,
    revision: String,
    content_hash: ScientificHashIdentity,
}

impl VersionedContentIdentity {
    pub fn new(
        schema: impl Into<String>,
        revision: impl Into<String>,
        content_hash: ScientificHashIdentity,
    ) -> Result<Self> {
        let schema = schema.into();
        let revision = revision.into();
        validate_machine_text("content schema", &schema)?;
        validate_machine_text("content schema revision", &revision)?;
        content_hash.validate()?;
        Ok(Self {
            schema,
            revision,
            content_hash,
        })
    }

    pub fn schema(&self) -> &str {
        &self.schema
    }

    pub fn revision(&self) -> &str {
        &self.revision
    }

    pub fn content_hash(&self) -> &ScientificHashIdentity {
        &self.content_hash
    }
}

impl<'de> Deserialize<'de> for VersionedContentIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = VersionedContentIdentityWire::deserialize(deserializer)?;
        Self::new(wire.schema, wire.revision, wire.content_hash).map_err(serde::de::Error::custom)
    }
}

/// Checked lowercase machine code for a reason or warning.
///
/// Each dot-separated part starts with a lowercase ASCII letter. Later characters can also be
/// digits or underscores. Use a namespace for a new code. An adapter can keep an existing
/// one-part code so that it does not change the source value.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(transparent)]
pub struct ScientificReasonCode(String);

impl ScientificReasonCode {
    pub fn new(value: impl Into<String>) -> Result<Self> {
        let value = value.into();
        if value.len() > MAX_IDENTIFIER_BYTES {
            anyhow::bail!("scientific reason code exceeds {MAX_IDENTIFIER_BYTES} bytes");
        }
        let segments = value.split('.').collect::<Vec<_>>();
        if segments.iter().any(|segment| {
            let mut bytes = segment.bytes();
            !bytes.next().is_some_and(|byte| byte.is_ascii_lowercase())
                || !bytes
                    .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
        }) {
            anyhow::bail!("scientific reason code must contain checked lowercase parts");
        }
        Ok(Self(value))
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl<'de> Deserialize<'de> for ScientificReasonCode {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        Self::new(String::deserialize(deserializer)?).map_err(serde::de::Error::custom)
    }
}

/// Coded reason with bounded explanatory text.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificReason {
    code: ScientificReasonCode,
    explanation: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificReasonWire {
    code: ScientificReasonCode,
    explanation: String,
}

impl ScientificReason {
    pub fn new(code: ScientificReasonCode, explanation: impl Into<String>) -> Result<Self> {
        let explanation = explanation.into();
        validate_explanation("scientific reason explanation", &explanation)?;
        Ok(Self { code, explanation })
    }

    pub fn code(&self) -> &ScientificReasonCode {
        &self.code
    }

    pub fn explanation(&self) -> &str {
        &self.explanation
    }
}

impl<'de> Deserialize<'de> for ScientificReason {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificReasonWire::deserialize(deserializer)?;
        Self::new(wire.code, wire.explanation).map_err(serde::de::Error::custom)
    }
}

/// Warning that changes how a numerical result can be used or interpreted.
///
/// Advisory diagnostics that do not affect the result or its use stay in the estimator report.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificWarning {
    code: ScientificReasonCode,
    explanation: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificWarningWire {
    code: ScientificReasonCode,
    explanation: String,
}

impl ScientificWarning {
    pub fn new(code: ScientificReasonCode, explanation: impl Into<String>) -> Result<Self> {
        let explanation = explanation.into();
        validate_explanation("scientific warning explanation", &explanation)?;
        Ok(Self { code, explanation })
    }

    pub fn code(&self) -> &ScientificReasonCode {
        &self.code
    }

    pub fn explanation(&self) -> &str {
        &self.explanation
    }
}

impl<'de> Deserialize<'de> for ScientificWarning {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificWarningWire::deserialize(deserializer)?;
        Self::new(wire.code, wire.explanation).map_err(serde::de::Error::custom)
    }
}

/// Availability of a scientific artifact in one calculation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificArtifactStatus {
    /// The artifact exists and has an identity.
    Available,
    /// The workflow did not produce the artifact.
    NotProduced,
    /// The artifact does not apply to this calculation.
    NotApplicable,
}

/// An available artifact identity or an explicit reason for its absence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
#[non_exhaustive]
pub enum ScientificArtifactIdentity {
    /// The artifact exists.
    Available { identity: VersionedContentIdentity },
    /// The workflow did not produce the artifact.
    NotProduced { reason: ScientificReason },
    /// The artifact does not apply.
    NotApplicable { reason: ScientificReason },
}

impl ScientificArtifactIdentity {
    pub fn available(identity: VersionedContentIdentity) -> Self {
        Self::Available { identity }
    }

    pub fn not_produced(reason: ScientificReason) -> Self {
        Self::NotProduced { reason }
    }

    pub fn not_applicable(reason: ScientificReason) -> Self {
        Self::NotApplicable { reason }
    }

    pub fn status(&self) -> ScientificArtifactStatus {
        match self {
            Self::Available { .. } => ScientificArtifactStatus::Available,
            Self::NotProduced { .. } => ScientificArtifactStatus::NotProduced,
            Self::NotApplicable { .. } => ScientificArtifactStatus::NotApplicable,
        }
    }

    pub fn identity(&self) -> Option<&VersionedContentIdentity> {
        match self {
            Self::Available { identity } => Some(identity),
            Self::NotProduced { .. } | Self::NotApplicable { .. } => None,
        }
    }

    pub fn reason(&self) -> Option<&ScientificReason> {
        match self {
            Self::Available { .. } => None,
            Self::NotProduced { reason } | Self::NotApplicable { reason } => Some(reason),
        }
    }
}

/// Origin of a method or quantity definition.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificMethodOrigin {
    /// A cited paper defines the method or quantity.
    PaperDefined,
    /// The project composes or adapts cited published definitions.
    PaperDerived,
    /// pid-rs defines the software contract, diagnostic, or workflow.
    ProjectDefined,
}

/// Population regime of the estimand.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificEstimandRegime {
    /// An empirical probability-mass-function estimand.
    EmpiricalPmf,
    /// A continuous estimand under explicit population-support conditions.
    ConditionalContinuous,
    /// A method-specific regime that a versioned contract defines.
    ContractDefined,
}

/// API and review maturity of the implementation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificApiMaturity {
    /// The method is on the stable scientific API.
    Stable,
    /// The method is on an experimental API.
    Experimental,
    /// The method is available only for research.
    ResearchOnly,
    /// No local implementation exposes an API for this request.
    NotApplicable,
}

/// Completeness of the requested scientific result.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificCompleteness {
    /// The implementation can produce the complete requested result.
    Complete,
    /// The implementation produces only a named diagnostic subset.
    IncompleteDiagnostic,
    /// No local implementation exists, so implementation completeness does not apply.
    NotApplicable,
}

/// Availability of an implementation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificAvailability {
    /// Local code implements the requested method in the declared regime.
    LocalImplementation,
    /// A separately maintained reference implementation exists, but pid-rs has no local code.
    ExternalReferenceCode,
    /// No local or external implementation supports the requested method.
    NoImplementation,
}

/// Separate method classifications and a recorded method-catalog entry identity.
///
/// The constructor checks that the catalog-entry schema name agrees with `catalog_id`. It does not
/// load a trusted catalog or verify the classification or digest. A consumer must compare this
/// value with a trusted catalog snapshot.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificMethodIdentity {
    catalog_id: String,
    origin: ScientificMethodOrigin,
    estimand_regime: ScientificEstimandRegime,
    api_maturity: ScientificApiMaturity,
    completeness: ScientificCompleteness,
    availability: ScientificAvailability,
    catalog_entry: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificMethodIdentityWire {
    catalog_id: String,
    origin: ScientificMethodOrigin,
    estimand_regime: ScientificEstimandRegime,
    api_maturity: ScientificApiMaturity,
    completeness: ScientificCompleteness,
    availability: ScientificAvailability,
    catalog_entry: VersionedContentIdentity,
}

/// Checked inputs for [`ScientificMethodIdentity::new`].
#[derive(Debug)]
pub struct ScientificMethodIdentityInputs {
    /// Identifier of the bound method-catalog entry.
    pub catalog_id: String,
    /// Origin of the scientific definition.
    pub origin: ScientificMethodOrigin,
    /// Population regime of the estimand.
    pub estimand_regime: ScientificEstimandRegime,
    /// Maturity of the local API.
    pub api_maturity: ScientificApiMaturity,
    /// Completeness of the local result.
    pub completeness: ScientificCompleteness,
    /// Location or absence of an implementation.
    pub availability: ScientificAvailability,
    /// Content identity for the method-catalog entry.
    pub catalog_entry: VersionedContentIdentity,
}

impl ScientificMethodIdentity {
    /// Construct a method identity and check that its axes agree.
    ///
    /// # Errors
    ///
    /// Returns an error for invalid identifiers, a catalog-entry schema mismatch, or incompatible
    /// local API, completeness, and implementation-availability states.
    pub fn new(inputs: ScientificMethodIdentityInputs) -> Result<Self> {
        let ScientificMethodIdentityInputs {
            catalog_id,
            origin,
            estimand_regime,
            api_maturity,
            completeness,
            availability,
            catalog_entry,
        } = inputs;
        validate_machine_text("method catalog ID", &catalog_id)?;
        let expected_schema = format!("pid-rs/method-catalog-entry/{catalog_id}");
        if catalog_entry.schema() != expected_schema {
            anyhow::bail!("method catalog entry schema does not match its catalog ID");
        }
        match availability {
            ScientificAvailability::LocalImplementation => {
                if api_maturity == ScientificApiMaturity::NotApplicable
                    || completeness == ScientificCompleteness::NotApplicable
                {
                    anyhow::bail!("local methods need applicable API and completeness axes");
                }
            }
            ScientificAvailability::ExternalReferenceCode
            | ScientificAvailability::NoImplementation => {
                if api_maturity != ScientificApiMaturity::NotApplicable
                    || completeness != ScientificCompleteness::NotApplicable
                {
                    anyhow::bail!(
                        "methods without local code need not-applicable local API and completeness axes"
                    );
                }
            }
        }
        Ok(Self {
            catalog_id,
            origin,
            estimand_regime,
            api_maturity,
            completeness,
            availability,
            catalog_entry,
        })
    }

    pub fn catalog_id(&self) -> &str {
        &self.catalog_id
    }

    pub fn origin(&self) -> ScientificMethodOrigin {
        self.origin
    }

    pub fn estimand_regime(&self) -> ScientificEstimandRegime {
        self.estimand_regime
    }

    pub fn api_maturity(&self) -> ScientificApiMaturity {
        self.api_maturity
    }

    pub fn completeness(&self) -> ScientificCompleteness {
        self.completeness
    }

    pub fn availability(&self) -> ScientificAvailability {
        self.availability
    }

    pub fn catalog_entry(&self) -> &VersionedContentIdentity {
        &self.catalog_entry
    }
}

impl<'de> Deserialize<'de> for ScientificMethodIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificMethodIdentityWire::deserialize(deserializer)?;
        Self::new(ScientificMethodIdentityInputs {
            catalog_id: wire.catalog_id,
            origin: wire.origin,
            estimand_regime: wire.estimand_regime,
            api_maturity: wire.api_maturity,
            completeness: wire.completeness,
            availability: wire.availability,
            catalog_entry: wire.catalog_entry,
        })
        .map_err(serde::de::Error::custom)
    }
}

/// Available estimator identity or an explicit reason that no estimator is available.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
#[non_exhaustive]
pub enum ScientificEstimatorIdentity {
    /// A finite-sample estimator is available.
    Available { identity: EstimatorIdentity },
    /// No estimator is available for this request.
    Unavailable { reason: ScientificReason },
}

impl ScientificEstimatorIdentity {
    pub fn available(identity: EstimatorIdentity) -> Result<Self> {
        validate_estimator_identity(&identity)?;
        Ok(Self::Available { identity })
    }

    pub fn unavailable(reason: ScientificReason) -> Self {
        Self::Unavailable { reason }
    }

    pub fn identity(&self) -> Option<&EstimatorIdentity> {
        match self {
            Self::Available { identity } => Some(identity),
            Self::Unavailable { .. } => None,
        }
    }

    pub fn reason(&self) -> Option<&ScientificReason> {
        match self {
            Self::Available { .. } => None,
            Self::Unavailable { reason } => Some(reason),
        }
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificEstimatorIdentityWire {
    Available { identity: EstimatorIdentity },
    Unavailable { reason: ScientificReason },
}

impl<'de> Deserialize<'de> for ScientificEstimatorIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificEstimatorIdentityWire::deserialize(deserializer)? {
            ScientificEstimatorIdentityWire::Available { identity } => {
                Self::available(identity).map_err(serde::de::Error::custom)
            }
            ScientificEstimatorIdentityWire::Unavailable { reason } => {
                Ok(Self::unavailable(reason))
            }
        }
    }
}

/// Unit of one named output quantity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificUnit {
    /// Natural-log information units.
    Nats,
}

/// Definition of one named value in a logical outcome.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificQuantityDefinition {
    key: String,
    unit: ScientificUnit,
    origin: ScientificMethodOrigin,
    definition: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificQuantityDefinitionWire {
    key: String,
    unit: ScientificUnit,
    origin: ScientificMethodOrigin,
    definition: VersionedContentIdentity,
}

impl ScientificQuantityDefinition {
    pub fn new(
        key: impl Into<String>,
        unit: ScientificUnit,
        origin: ScientificMethodOrigin,
        definition: VersionedContentIdentity,
    ) -> Result<Self> {
        let key = key.into();
        validate_machine_text("scientific quantity key", &key)?;
        Ok(Self {
            key,
            unit,
            origin,
            definition,
        })
    }

    pub fn key(&self) -> &str {
        &self.key
    }

    pub fn unit(&self) -> ScientificUnit {
        self.unit
    }

    pub fn origin(&self) -> ScientificMethodOrigin {
        self.origin
    }

    pub fn definition(&self) -> &VersionedContentIdentity {
        &self.definition
    }
}

impl<'de> Deserialize<'de> for ScientificQuantityDefinition {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificQuantityDefinitionWire::deserialize(deserializer)?;
        Self::new(wire.key, wire.unit, wire.origin, wire.definition)
            .map_err(serde::de::Error::custom)
    }
}

/// Declared set and definitions of the named values in one logical outcome.
///
/// Completeness is relative to this caller-supplied declaration. A consumer needs a trusted method
/// contract to decide whether this declaration contains every quantity for a specific method.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificOutputSchema {
    schema_id: String,
    revision: String,
    quantities: Vec<ScientificQuantityDefinition>,
    identity: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificOutputSchemaWire {
    schema_id: String,
    revision: String,
    quantities: BoundedVec<ScientificQuantityDefinition, MAX_NAMED_VALUES>,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificOutputSchemaPreimage<'a> {
    domain: &'static str,
    schema_id: &'a str,
    revision: &'a str,
    quantities: &'a [ScientificQuantityDefinition],
}

impl ScientificOutputSchema {
    /// Construct a declared output schema and compute its identity.
    ///
    /// # Errors
    ///
    /// Returns an error for invalid identifiers, an empty or oversized quantity list, duplicate
    /// keys, or a canonical-hash resource failure.
    pub fn new(
        schema_id: impl Into<String>,
        revision: impl Into<String>,
        mut quantities: Vec<ScientificQuantityDefinition>,
    ) -> Result<Self> {
        let schema_id = schema_id.into();
        let revision = revision.into();
        validate_machine_text("scientific output schema ID", &schema_id)?;
        validate_machine_text("scientific output schema revision", &revision)?;
        if quantities.is_empty() || quantities.len() > MAX_NAMED_VALUES {
            anyhow::bail!("scientific output schema needs 1..={MAX_NAMED_VALUES} quantities");
        }
        quantities.sort_by(|left, right| left.key.cmp(&right.key));
        if quantities.windows(2).any(|pair| pair[0].key == pair[1].key) {
            anyhow::bail!("scientific output quantity keys must be unique");
        }
        let preimage = ScientificOutputSchemaPreimage {
            domain: "pid-rs/scientific-output-schema/v1",
            schema_id: &schema_id,
            revision: &revision,
            quantities: &quantities,
        };
        let identity = VersionedContentIdentity::new(
            schema_id.clone(),
            revision.clone(),
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            schema_id,
            revision,
            quantities,
            identity,
        })
    }

    pub fn schema_id(&self) -> &str {
        &self.schema_id
    }

    pub fn revision(&self) -> &str {
        &self.revision
    }

    pub fn quantities(&self) -> &[ScientificQuantityDefinition] {
        &self.quantities
    }

    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }

    fn matches_values(&self, values: &ScientificValueSet) -> bool {
        self.quantities
            .iter()
            .map(|quantity| quantity.key.as_str())
            .eq(values.as_map().keys().map(String::as_str))
    }
}

impl<'de> Deserialize<'de> for ScientificOutputSchema {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificOutputSchemaWire::deserialize(deserializer)?;
        let expected = wire.identity;
        let schema = Self::new(wire.schema_id, wire.revision, wire.quantities.into_vec())
            .map_err(serde::de::Error::custom)?;
        if schema.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific output schema identity does not match its canonical preimage",
            ));
        }
        Ok(schema)
    }
}

/// One nonzero coefficient and output key in a linear scientific invariant.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificLinearTerm {
    key: String,
    coefficient: f64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificLinearTermWire {
    key: String,
    coefficient: JsonF64,
}

impl ScientificLinearTerm {
    /// Construct one checked linear term.
    pub fn new(key: impl Into<String>, coefficient: f64) -> Result<Self> {
        let key = key.into();
        validate_machine_text("scientific invariant quantity key", &key)?;
        if !coefficient.is_finite() || coefficient == 0.0 {
            anyhow::bail!("scientific invariant coefficient must be finite and nonzero");
        }
        Ok(Self { key, coefficient })
    }

    /// Return the quantity key.
    pub fn key(&self) -> &str {
        &self.key
    }

    /// Return the coefficient.
    pub fn coefficient(&self) -> f64 {
        self.coefficient
    }
}

impl<'de> Deserialize<'de> for ScientificLinearTerm {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificLinearTermWire::deserialize(deserializer)?;
        Self::new(wire.key, wire.coefficient.0).map_err(serde::de::Error::custom)
    }
}

/// One equation of the form `sum(coefficient * value) = 0`.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificLinearInvariant {
    invariant_id: String,
    terms: Vec<ScientificLinearTerm>,
    absolute_tolerance: f64,
    relative_tolerance: f64,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificLinearInvariantWire {
    invariant_id: String,
    terms: BoundedVec<ScientificLinearTerm, MAX_NAMED_VALUES>,
    absolute_tolerance: JsonF64,
    relative_tolerance: JsonF64,
}

impl ScientificLinearInvariant {
    /// Construct one checked scale-aware linear invariant.
    ///
    /// # Errors
    ///
    /// Returns an error for an invalid identifier, duplicate or invalid terms, or a negative or
    /// non-finite tolerance.
    pub fn new(
        invariant_id: impl Into<String>,
        mut terms: Vec<ScientificLinearTerm>,
        absolute_tolerance: f64,
        relative_tolerance: f64,
    ) -> Result<Self> {
        let invariant_id = invariant_id.into();
        validate_machine_text("scientific invariant ID", &invariant_id)?;
        if terms.len() < 2 || terms.len() > MAX_NAMED_VALUES {
            anyhow::bail!("scientific linear invariant needs 2..={MAX_NAMED_VALUES} terms");
        }
        terms.sort_by(|left, right| left.key.cmp(&right.key));
        if terms.windows(2).any(|pair| pair[0].key == pair[1].key) {
            anyhow::bail!("scientific invariant term keys must be unique");
        }
        if !absolute_tolerance.is_finite()
            || absolute_tolerance < 0.0
            || !relative_tolerance.is_finite()
            || relative_tolerance < 0.0
        {
            anyhow::bail!("scientific invariant tolerances must be finite and nonnegative");
        }
        Ok(Self {
            invariant_id,
            terms,
            absolute_tolerance,
            relative_tolerance,
        })
    }

    /// Return the invariant ID.
    pub fn invariant_id(&self) -> &str {
        &self.invariant_id
    }

    /// Return the canonical linear terms.
    pub fn terms(&self) -> &[ScientificLinearTerm] {
        &self.terms
    }

    /// Return the absolute residual tolerance.
    pub fn absolute_tolerance(&self) -> f64 {
        self.absolute_tolerance
    }

    /// Return the relative scale tolerance.
    pub fn relative_tolerance(&self) -> f64 {
        self.relative_tolerance
    }

    fn validate_schema(&self, schema: &ScientificOutputSchema) -> Result<()> {
        for term in &self.terms {
            if schema
                .quantities
                .binary_search_by(|quantity| quantity.key.as_str().cmp(&term.key))
                .is_err()
            {
                anyhow::bail!("scientific invariant names a key outside the output schema");
            }
        }
        Ok(())
    }

    fn validate_values(&self, values: &ScientificValueSet) -> Result<()> {
        let mut contributions = Vec::with_capacity(self.terms.len());
        for term in &self.terms {
            let value = values
                .as_map()
                .get(&term.key)
                .ok_or_else(|| anyhow::anyhow!("scientific invariant value is absent"))?;
            let contribution = term.coefficient * value;
            if !contribution.is_finite() {
                anyhow::bail!(
                    "scientific invariant {} has a nonfinite linear contribution",
                    self.invariant_id
                );
            }
            contributions.push(contribution);
        }
        let max_magnitude = contributions
            .iter()
            .map(|value| value.abs())
            .fold(0.0_f64, f64::max);
        if max_magnitude == 0.0 {
            return Ok(());
        }
        let residual = neumaier_sum(
            contributions
                .iter()
                .map(|contribution| contribution / max_magnitude),
        );
        let scale = neumaier_sum(
            contributions
                .iter()
                .map(|contribution| contribution.abs() / max_magnitude),
        );
        let tolerance = self.absolute_tolerance / max_magnitude + self.relative_tolerance * scale;
        if residual.abs() > tolerance {
            anyhow::bail!(
                "scientific output violates linear invariant {}",
                self.invariant_id
            );
        }
        Ok(())
    }
}

fn neumaier_sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        correction += if sum.abs() >= value.abs() {
            (sum - next) + value
        } else {
            (value - next) + sum
        };
        sum = next;
    }
    sum + correction
}

impl<'de> Deserialize<'de> for ScientificLinearInvariant {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificLinearInvariantWire::deserialize(deserializer)?;
        Self::new(
            wire.invariant_id,
            wire.terms.into_vec(),
            wire.absolute_tolerance.0,
            wire.relative_tolerance.0,
        )
        .map_err(serde::de::Error::custom)
    }
}

#[derive(Debug, Clone, PartialEq)]
enum ScientificInvariantState {
    NotApplicable {
        reason: ScientificReason,
    },
    Linear {
        invariants: Vec<ScientificLinearInvariant>,
    },
}

/// Numerical-coherence policy for a declared output schema.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct ScientificInvariantContract {
    state: ScientificInvariantState,
}

impl ScientificInvariantContract {
    /// Record that this layer has no applicable linear invariant.
    pub fn not_applicable(reason: ScientificReason) -> Self {
        Self {
            state: ScientificInvariantState::NotApplicable { reason },
        }
    }

    /// Construct a non-empty set of checked linear invariants.
    ///
    /// # Errors
    ///
    /// Returns an error if the set is empty, is too large, or repeats an invariant ID.
    pub fn linear(mut invariants: Vec<ScientificLinearInvariant>) -> Result<Self> {
        if invariants.is_empty() || invariants.len() > MAX_NAMED_VALUES {
            anyhow::bail!("scientific invariant contract needs 1..={MAX_NAMED_VALUES} equations");
        }
        invariants.sort_by(|left, right| left.invariant_id.cmp(&right.invariant_id));
        if invariants
            .windows(2)
            .any(|pair| pair[0].invariant_id == pair[1].invariant_id)
        {
            anyhow::bail!("scientific invariant IDs must be unique");
        }
        Ok(Self {
            state: ScientificInvariantState::Linear { invariants },
        })
    }

    /// Return the linear invariants, or an empty slice when none apply.
    pub fn linear_invariants(&self) -> &[ScientificLinearInvariant] {
        match &self.state {
            ScientificInvariantState::NotApplicable { .. } => &[],
            ScientificInvariantState::Linear { invariants } => invariants,
        }
    }

    /// Return the reason when no invariant applies.
    pub fn reason(&self) -> Option<&ScientificReason> {
        match &self.state {
            ScientificInvariantState::NotApplicable { reason } => Some(reason),
            ScientificInvariantState::Linear { .. } => None,
        }
    }

    fn validate_schema(&self, schema: &ScientificOutputSchema) -> Result<()> {
        for invariant in self.linear_invariants() {
            invariant.validate_schema(schema)?;
        }
        Ok(())
    }

    fn validate_values(&self, values: &ScientificValueSet) -> Result<()> {
        for invariant in self.linear_invariants() {
            invariant.validate_values(values)?;
        }
        Ok(())
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificInvariantSerialize<'a> {
    NotApplicable {
        reason: &'a ScientificReason,
    },
    Linear {
        invariants: &'a [ScientificLinearInvariant],
    },
}

impl Serialize for ScientificInvariantContract {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match &self.state {
            ScientificInvariantState::NotApplicable { reason } => {
                ScientificInvariantSerialize::NotApplicable { reason }
            }
            ScientificInvariantState::Linear { invariants } => {
                ScientificInvariantSerialize::Linear { invariants }
            }
        }
        .serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificInvariantDeserialize {
    NotApplicable {
        reason: ScientificReason,
    },
    Linear {
        invariants: BoundedVec<ScientificLinearInvariant, MAX_NAMED_VALUES>,
    },
}

impl<'de> Deserialize<'de> for ScientificInvariantContract {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificInvariantDeserialize::deserialize(deserializer)? {
            ScientificInvariantDeserialize::NotApplicable { reason } => {
                Ok(Self::not_applicable(reason))
            }
            ScientificInvariantDeserialize::Linear { invariants } => {
                Self::linear(invariants.into_vec()).map_err(serde::de::Error::custom)
            }
        }
    }
}

/// One variable role and identifier in a frozen logical request.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificRequestVariable {
    role: InformationVariableRole,
    variable_id: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificRequestVariableWire {
    role: InformationVariableRole,
    variable_id: String,
}

impl ScientificRequestVariable {
    /// Construct one checked request variable.
    pub fn new(role: InformationVariableRole, variable_id: impl Into<String>) -> Result<Self> {
        let variable_id = variable_id.into();
        validate_machine_text("scientific request variable ID", &variable_id)?;
        Ok(Self { role, variable_id })
    }

    /// Return the variable role.
    pub fn role(&self) -> InformationVariableRole {
        self.role
    }

    /// Return the variable identifier.
    pub fn variable_id(&self) -> &str {
        &self.variable_id
    }
}

impl<'de> Deserialize<'de> for ScientificRequestVariable {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificRequestVariableWire::deserialize(deserializer)?;
        Self::new(wire.role, wire.variable_id).map_err(serde::de::Error::custom)
    }
}

/// Candidate outcome ID, activation state, and frozen analysis-plan identity.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificRequestEntry {
    outcome_id: String,
    requested: bool,
    analysis_plan: VersionedContentIdentity,
}

/// Checked inputs for [`ScientificRequestEntry::new`].
#[derive(Debug)]
pub struct ScientificRequestEntryInputs {
    /// The logical outcome ID.
    pub outcome_id: String,
    /// Whether the run activated this candidate calculation.
    pub requested: bool,
    /// The complete frozen analysis-plan identity.
    pub analysis_plan: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificRequestEntryWire {
    outcome_id: String,
    requested: bool,
    analysis_plan: VersionedContentIdentity,
}

impl ScientificRequestEntry {
    /// Construct one checked request entry.
    pub fn new(inputs: ScientificRequestEntryInputs) -> Result<Self> {
        let outcome_id = inputs.outcome_id;
        validate_machine_text("scientific request outcome ID", &outcome_id)?;
        if !inputs
            .analysis_plan
            .schema()
            .starts_with("pid-rs/scientific-analysis-plan/")
        {
            anyhow::bail!("request entry needs a scientific analysis-plan identity");
        }
        Ok(Self {
            outcome_id,
            requested: inputs.requested,
            analysis_plan: inputs.analysis_plan,
        })
    }

    /// Return the logical outcome ID.
    pub fn outcome_id(&self) -> &str {
        &self.outcome_id
    }

    /// Return whether the run activated this candidate calculation.
    pub fn requested(&self) -> bool {
        self.requested
    }

    /// Return the complete frozen analysis-plan identity.
    pub fn analysis_plan(&self) -> &VersionedContentIdentity {
        &self.analysis_plan
    }
}

impl<'de> Deserialize<'de> for ScientificRequestEntry {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificRequestEntryWire::deserialize(deserializer)?;
        Self::new(ScientificRequestEntryInputs {
            outcome_id: wire.outcome_id,
            requested: wire.requested,
            analysis_plan: wire.analysis_plan,
        })
        .map_err(serde::de::Error::custom)
    }
}

/// Frozen set of logical outcomes that a run or screen must account for.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificRequestLedger {
    contract_revision: u32,
    ledger_id: String,
    sampling_frame: VersionedContentIdentity,
    entries: Vec<ScientificRequestEntry>,
    identity: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificRequestLedgerWire {
    contract_revision: u32,
    ledger_id: String,
    sampling_frame: VersionedContentIdentity,
    entries: BoundedVec<ScientificRequestEntry, MAX_REQUEST_OUTCOMES>,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificRequestLedgerPreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    ledger_id: &'a str,
    sampling_frame: &'a VersionedContentIdentity,
    entries: &'a [ScientificRequestEntry],
}

impl ScientificRequestLedger {
    pub fn new(
        ledger_id: impl Into<String>,
        sampling_frame: VersionedContentIdentity,
        mut entries: Vec<ScientificRequestEntry>,
    ) -> Result<Self> {
        let ledger_id = ledger_id.into();
        validate_machine_text("scientific request ledger ID", &ledger_id)?;
        if entries.is_empty() || entries.len() > MAX_REQUEST_OUTCOMES {
            anyhow::bail!("scientific request ledger needs 1..={MAX_REQUEST_OUTCOMES} outcome IDs");
        }
        entries.sort_by(|left, right| left.outcome_id.cmp(&right.outcome_id));
        if entries
            .windows(2)
            .any(|pair| pair[0].outcome_id == pair[1].outcome_id)
        {
            anyhow::bail!("expected scientific outcome IDs must be unique");
        }
        let preimage = ScientificRequestLedgerPreimage {
            domain: "pid-rs/scientific-request-ledger/v1",
            contract_revision: CONTRACT_REVISION,
            ledger_id: &ledger_id,
            sampling_frame: &sampling_frame,
            entries: &entries,
        };
        let identity = VersionedContentIdentity::new(
            format!("pid-rs/scientific-request-ledger/{ledger_id}"),
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            ledger_id,
            sampling_frame,
            entries,
            identity,
        })
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn ledger_id(&self) -> &str {
        &self.ledger_id
    }

    pub fn sampling_frame(&self) -> &VersionedContentIdentity {
        &self.sampling_frame
    }

    /// Return the canonical request entries.
    pub fn entries(&self) -> &[ScientificRequestEntry] {
        &self.entries
    }

    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }

    /// Return the entry for one logical outcome ID.
    pub fn entry(&self, outcome_id: &str) -> Option<&ScientificRequestEntry> {
        self.entries
            .binary_search_by(|entry| entry.outcome_id.as_str().cmp(outcome_id))
            .ok()
            .map(|index| &self.entries[index])
    }
}

impl<'de> Deserialize<'de> for ScientificRequestLedger {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificRequestLedgerWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific request ledger revision",
            ));
        }
        let expected = wire.identity;
        let ledger = Self::new(wire.ledger_id, wire.sampling_frame, wire.entries.into_vec())
            .map_err(serde::de::Error::custom)?;
        if ledger.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific request ledger identity does not match its canonical preimage",
            ));
        }
        Ok(ledger)
    }
}

/// Role of one estimator input matrix.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
#[non_exhaustive]
pub enum InformationVariableRole {
    /// A source variable at the given zero-based index.
    Source { index: u32 },
    /// The single target variable.
    Target,
}

#[derive(Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
enum InformationVariableRoleWire {
    Source(InformationSourceRoleWire),
    Target(InformationTargetRoleWire),
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InformationSourceRoleWire {
    index: u32,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InformationTargetRoleWire {}

impl<'de> Deserialize<'de> for InformationVariableRole {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match InformationVariableRoleWire::deserialize(deserializer)? {
            InformationVariableRoleWire::Source(wire) => Ok(Self::Source { index: wire.index }),
            InformationVariableRoleWire::Target(_) => Ok(Self::Target),
        }
    }
}

/// A declared estimator-input identity and optional upstream artifact identity.
///
/// Use [`scientific_f64_matrix_identity_v1`] or [`scientific_u64_matrix_identity_v1`] to compute a
/// supported value hash from matrix values. This constructor checks the identity record. It does
/// not read an external artifact or recompute a caller-supplied digest.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificDataIdentity {
    role: InformationVariableRole,
    variable_id: String,
    matrix: ScientificMatrixIdentity,
    row_membership: ScientificMembershipIdentity,
    source_artifact: ScientificArtifactIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificDataIdentityWire {
    role: InformationVariableRole,
    variable_id: String,
    matrix: ScientificMatrixIdentity,
    row_membership: ScientificMembershipIdentity,
    source_artifact: ScientificArtifactIdentity,
}

impl ScientificDataIdentity {
    pub fn new(
        role: InformationVariableRole,
        variable_id: impl Into<String>,
        matrix: ScientificMatrixIdentity,
        row_membership: ScientificMembershipIdentity,
        source_artifact: ScientificArtifactIdentity,
    ) -> Result<Self> {
        let variable_id = variable_id.into();
        validate_machine_text("scientific variable ID", &variable_id)?;
        if matrix.rows() != row_membership.member_count() {
            anyhow::bail!("scientific matrix rows must match ordered row membership");
        }
        Ok(Self {
            role,
            variable_id,
            matrix,
            row_membership,
            source_artifact,
        })
    }

    pub fn role(&self) -> InformationVariableRole {
        self.role
    }

    pub fn variable_id(&self) -> &str {
        &self.variable_id
    }

    pub fn value_hash(&self) -> &ScientificHashIdentity {
        self.matrix.content_hash()
    }

    /// Return the typed matrix identity, including its encoded shape.
    pub fn matrix_identity(&self) -> &ScientificMatrixIdentity {
        &self.matrix
    }

    pub fn row_membership_hash(&self) -> &ScientificHashIdentity {
        self.row_membership.content_hash()
    }

    /// Return the typed ordered-membership identity, including its encoded count.
    pub fn row_membership_identity(&self) -> &ScientificMembershipIdentity {
        &self.row_membership
    }

    pub fn rows(&self) -> u64 {
        self.matrix.rows()
    }

    pub fn columns(&self) -> u64 {
        self.matrix.columns()
    }

    pub fn source_artifact(&self) -> &ScientificArtifactIdentity {
        &self.source_artifact
    }
}

impl<'de> Deserialize<'de> for ScientificDataIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificDataIdentityWire::deserialize(deserializer)?;
        Self::new(
            wire.role,
            wire.variable_id,
            wire.matrix,
            wire.row_membership,
            wire.source_artifact,
        )
        .map_err(serde::de::Error::custom)
    }
}

/// Kind of one applied data transform.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificTransformKind {
    /// Unsupervised or supervised preprocessing.
    Preprocessing,
    /// An explicit observation-model transform.
    ObservationModel,
    /// A split, permutation, bootstrap, or other resampling transform.
    Resampling,
}

/// Whether an applied transform used a fitted state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificTransformFitStatus {
    /// The transform did not fit state from sample rows.
    Stateless,
    /// The transform used a state fitted on the recorded data and split.
    Fitted,
}

/// Variable access used to fit transform state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificFitAccess {
    /// The fit used source variables and did not access the target.
    UnsupervisedSources,
    /// The fit used both source variables and the target.
    SupervisedSourcesAndTarget,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ScientificTransformFitState {
    Stateless,
    Fitted {
        state: VersionedContentIdentity,
        access: ScientificFitAccess,
        fit_data: Vec<ScientificDataIdentity>,
        fit_split: String,
    },
}

/// Fit-state provenance for one applied aggregate transform.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub struct ScientificTransformFit {
    state: ScientificTransformFitState,
}

impl ScientificTransformFit {
    /// Record a transform that did not fit state from sample rows.
    pub fn stateless() -> Self {
        Self {
            state: ScientificTransformFitState::Stateless,
        }
    }

    /// Record a fitted-state identity, the declared fit data, and the fit split.
    pub fn fitted(
        state: VersionedContentIdentity,
        access: ScientificFitAccess,
        mut fit_data: Vec<ScientificDataIdentity>,
        fit_split: impl Into<String>,
    ) -> Result<Self> {
        let fit_split = fit_split.into();
        validate_machine_text("scientific transform fit split", &fit_split)?;
        canonicalize_fit_data(&mut fit_data, access)?;
        Ok(Self {
            state: ScientificTransformFitState::Fitted {
                state,
                access,
                fit_data,
                fit_split,
            },
        })
    }

    /// Return whether this transform used fitted state.
    pub fn status(&self) -> ScientificTransformFitStatus {
        match self.state {
            ScientificTransformFitState::Stateless => ScientificTransformFitStatus::Stateless,
            ScientificTransformFitState::Fitted { .. } => ScientificTransformFitStatus::Fitted,
        }
    }

    /// Return the fitted-state identity, if one exists.
    pub fn fitted_state(&self) -> Option<&VersionedContentIdentity> {
        match &self.state {
            ScientificTransformFitState::Stateless => None,
            ScientificTransformFitState::Fitted { state, .. } => Some(state),
        }
    }

    /// Return the source/target access policy for a fitted state.
    pub fn access(&self) -> Option<ScientificFitAccess> {
        match &self.state {
            ScientificTransformFitState::Stateless => None,
            ScientificTransformFitState::Fitted { access, .. } => Some(*access),
        }
    }

    /// Return the declared data identities used to fit the state.
    pub fn fit_data(&self) -> Option<&[ScientificDataIdentity]> {
        match &self.state {
            ScientificTransformFitState::Stateless => None,
            ScientificTransformFitState::Fitted { fit_data, .. } => Some(fit_data),
        }
    }

    /// Return the split used to fit the state.
    pub fn fit_split(&self) -> Option<&str> {
        match &self.state {
            ScientificTransformFitState::Stateless => None,
            ScientificTransformFitState::Fitted { fit_split, .. } => Some(fit_split),
        }
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificTransformFitSerialize<'a> {
    Stateless,
    Fitted {
        state: &'a VersionedContentIdentity,
        access: ScientificFitAccess,
        fit_data: &'a [ScientificDataIdentity],
        fit_split: &'a str,
    },
}

impl Serialize for ScientificTransformFit {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match &self.state {
            ScientificTransformFitState::Stateless => ScientificTransformFitSerialize::Stateless,
            ScientificTransformFitState::Fitted {
                state,
                access,
                fit_data,
                fit_split,
            } => ScientificTransformFitSerialize::Fitted {
                state,
                access: *access,
                fit_data,
                fit_split,
            },
        }
        .serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificTransformFitDeserialize {
    Stateless,
    Fitted {
        state: VersionedContentIdentity,
        access: ScientificFitAccess,
        fit_data: BoundedVec<ScientificDataIdentity, MAX_DATA_IDENTITIES>,
        fit_split: String,
    },
}

impl<'de> Deserialize<'de> for ScientificTransformFit {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificTransformFitDeserialize::deserialize(deserializer)? {
            ScientificTransformFitDeserialize::Stateless => Ok(Self::stateless()),
            ScientificTransformFitDeserialize::Fitted {
                state,
                access,
                fit_data,
                fit_split,
            } => Self::fitted(state, access, fit_data.into_vec(), fit_split)
                .map_err(serde::de::Error::custom),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ScientificTransformFitPlanState {
    Stateless,
    Fitted {
        access: ScientificFitAccess,
        fit_split: String,
    },
}

/// Planned fit policy for one transform step.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub struct ScientificTransformFitPlan {
    state: ScientificTransformFitPlanState,
}

impl ScientificTransformFitPlan {
    /// Plan a transform that does not fit state from sample rows.
    pub fn stateless() -> Self {
        Self {
            state: ScientificTransformFitPlanState::Stateless,
        }
    }

    /// Plan a fitted transform with an explicit access policy and split.
    pub fn fitted(access: ScientificFitAccess, fit_split: impl Into<String>) -> Result<Self> {
        let fit_split = fit_split.into();
        validate_machine_text("scientific planned transform fit split", &fit_split)?;
        Ok(Self {
            state: ScientificTransformFitPlanState::Fitted { access, fit_split },
        })
    }

    /// Return whether the planned transform is fitted.
    pub fn status(&self) -> ScientificTransformFitStatus {
        match self.state {
            ScientificTransformFitPlanState::Stateless => ScientificTransformFitStatus::Stateless,
            ScientificTransformFitPlanState::Fitted { .. } => ScientificTransformFitStatus::Fitted,
        }
    }

    /// Return the planned access policy.
    pub fn access(&self) -> Option<ScientificFitAccess> {
        match self.state {
            ScientificTransformFitPlanState::Stateless => None,
            ScientificTransformFitPlanState::Fitted { access, .. } => Some(access),
        }
    }

    /// Return the planned fit split.
    pub fn fit_split(&self) -> Option<&str> {
        match &self.state {
            ScientificTransformFitPlanState::Stateless => None,
            ScientificTransformFitPlanState::Fitted { fit_split, .. } => Some(fit_split),
        }
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificTransformFitPlanSerialize<'a> {
    Stateless,
    Fitted {
        access: ScientificFitAccess,
        fit_split: &'a str,
    },
}

impl Serialize for ScientificTransformFitPlan {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match &self.state {
            ScientificTransformFitPlanState::Stateless => {
                ScientificTransformFitPlanSerialize::Stateless
            }
            ScientificTransformFitPlanState::Fitted { access, fit_split } => {
                ScientificTransformFitPlanSerialize::Fitted {
                    access: *access,
                    fit_split,
                }
            }
        }
        .serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificTransformFitPlanDeserialize {
    Stateless,
    Fitted {
        access: ScientificFitAccess,
        fit_split: String,
    },
}

impl<'de> Deserialize<'de> for ScientificTransformFitPlan {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificTransformFitPlanDeserialize::deserialize(deserializer)? {
            ScientificTransformFitPlanDeserialize::Stateless => Ok(Self::stateless()),
            ScientificTransformFitPlanDeserialize::Fitted { access, fit_split } => {
                Self::fitted(access, fit_split).map_err(serde::de::Error::custom)
            }
        }
    }
}

/// One ordered transform step in a frozen analysis plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificTransformPlanStep {
    step_id: String,
    kind: ScientificTransformKind,
    contract: VersionedContentIdentity,
    fit: ScientificTransformFitPlan,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificTransformPlanStepWire {
    step_id: String,
    kind: ScientificTransformKind,
    contract: VersionedContentIdentity,
    fit: ScientificTransformFitPlan,
}

impl ScientificTransformPlanStep {
    /// Construct one checked transform-plan step.
    pub fn new(
        step_id: impl Into<String>,
        kind: ScientificTransformKind,
        contract: VersionedContentIdentity,
        fit: ScientificTransformFitPlan,
    ) -> Result<Self> {
        let step_id = step_id.into();
        validate_machine_text("scientific transform plan step ID", &step_id)?;
        Ok(Self {
            step_id,
            kind,
            contract,
            fit,
        })
    }

    /// Return the step ID.
    pub fn step_id(&self) -> &str {
        &self.step_id
    }

    /// Return the transform kind.
    pub fn kind(&self) -> ScientificTransformKind {
        self.kind
    }

    /// Return the step contract.
    pub fn contract(&self) -> &VersionedContentIdentity {
        &self.contract
    }

    /// Return the planned fit policy.
    pub fn fit(&self) -> &ScientificTransformFitPlan {
        &self.fit
    }
}

impl<'de> Deserialize<'de> for ScientificTransformPlanStep {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificTransformPlanStepWire::deserialize(deserializer)?;
        Self::new(wire.step_id, wire.kind, wire.contract, wire.fit)
            .map_err(serde::de::Error::custom)
    }
}

/// Ordered transform policy in a frozen analysis plan.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificPipelinePlan {
    contract_revision: u32,
    steps: Vec<ScientificTransformPlanStep>,
    identity: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificPipelinePlanWire {
    contract_revision: u32,
    steps: BoundedVec<ScientificTransformPlanStep, MAX_TRANSFORMS>,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificPipelinePlanPreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    steps: &'a [ScientificTransformPlanStep],
}

impl ScientificPipelinePlan {
    /// Construct an ordered pipeline plan and compute its identity.
    pub fn new(steps: Vec<ScientificTransformPlanStep>) -> Result<Self> {
        if steps.len() > MAX_TRANSFORMS {
            anyhow::bail!("scientific pipeline plan exceeds {MAX_TRANSFORMS} steps");
        }
        let mut step_ids = BTreeSet::new();
        if steps
            .iter()
            .any(|step| !step_ids.insert(step.step_id.as_str()))
        {
            anyhow::bail!("scientific pipeline plan step IDs must be unique");
        }
        let preimage = ScientificPipelinePlanPreimage {
            domain: "pid-rs/scientific-pipeline-plan/v1",
            contract_revision: CONTRACT_REVISION,
            steps: &steps,
        };
        let identity = VersionedContentIdentity::new(
            "pid-rs/scientific-pipeline-plan",
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            steps,
            identity,
        })
    }

    /// Return the ordered steps.
    pub fn steps(&self) -> &[ScientificTransformPlanStep] {
        &self.steps
    }

    /// Return the complete pipeline-plan identity.
    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }

    fn matches_prefix(&self, transforms: &[ScientificTransformEdge]) -> bool {
        transforms.len() <= self.steps.len()
            && self.steps.iter().zip(transforms).all(|(planned, applied)| {
                planned.step_id == applied.step_id
                    && planned.kind == applied.kind
                    && planned.contract == applied.contract
                    && planned.fit.status() == applied.fit.status()
                    && planned.fit.access() == applied.fit.access()
                    && planned.fit.fit_split() == applied.fit.fit_split()
            })
    }
}

impl<'de> Deserialize<'de> for ScientificPipelinePlan {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificPipelinePlanWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific pipeline plan revision",
            ));
        }
        let expected = wire.identity;
        let plan = Self::new(wire.steps.into_vec()).map_err(serde::de::Error::custom)?;
        if plan.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific pipeline plan identity does not match its canonical preimage",
            ));
        }
        Ok(plan)
    }
}

/// One checked aggregate transform edge with declared input and output identities.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificTransformEdge {
    step_id: String,
    kind: ScientificTransformKind,
    contract: VersionedContentIdentity,
    fit: ScientificTransformFit,
    inputs: Vec<ScientificDataIdentity>,
    outputs: Vec<ScientificDataIdentity>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificTransformEdgeWire {
    step_id: String,
    kind: ScientificTransformKind,
    contract: VersionedContentIdentity,
    fit: ScientificTransformFit,
    inputs: BoundedVec<ScientificDataIdentity, MAX_DATA_IDENTITIES>,
    outputs: BoundedVec<ScientificDataIdentity, MAX_DATA_IDENTITIES>,
}

impl ScientificTransformEdge {
    pub fn new(
        step_id: impl Into<String>,
        kind: ScientificTransformKind,
        contract: VersionedContentIdentity,
        fit: ScientificTransformFit,
        mut inputs: Vec<ScientificDataIdentity>,
        mut outputs: Vec<ScientificDataIdentity>,
    ) -> Result<Self> {
        let step_id = step_id.into();
        validate_machine_text("scientific transform step ID", &step_id)?;
        canonicalize_data_identities(&mut inputs)?;
        canonicalize_data_identities(&mut outputs)?;
        if kind != ScientificTransformKind::Resampling
            && inputs[0].row_membership_identity() != outputs[0].row_membership_identity()
        {
            anyhow::bail!(
                "preprocessing and observation-model transforms must preserve ordered row membership"
            );
        }
        Ok(Self {
            step_id,
            kind,
            contract,
            fit,
            inputs,
            outputs,
        })
    }

    pub fn step_id(&self) -> &str {
        &self.step_id
    }

    pub fn kind(&self) -> ScientificTransformKind {
        self.kind
    }

    pub fn contract(&self) -> &VersionedContentIdentity {
        &self.contract
    }

    /// Return the fit-state provenance.
    pub fn fit(&self) -> &ScientificTransformFit {
        &self.fit
    }

    pub fn inputs(&self) -> &[ScientificDataIdentity] {
        &self.inputs
    }

    pub fn outputs(&self) -> &[ScientificDataIdentity] {
        &self.outputs
    }
}

impl<'de> Deserialize<'de> for ScientificTransformEdge {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificTransformEdgeWire::deserialize(deserializer)?;
        Self::new(
            wire.step_id,
            wire.kind,
            wire.contract,
            wire.fit,
            wire.inputs.into_vec(),
            wire.outputs.into_vec(),
        )
        .map_err(serde::de::Error::custom)
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ScientificDataSetState {
    Available { data: Vec<ScientificDataIdentity> },
    NotProduced { reason: ScientificReason },
    NotApplicable { reason: ScientificReason },
}

/// Available data identities or an explicit reason for their absence.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub struct ScientificDataSet {
    state: ScientificDataSetState,
}

impl ScientificDataSet {
    pub fn available(mut data: Vec<ScientificDataIdentity>) -> Result<Self> {
        canonicalize_data_identities(&mut data)?;
        Ok(Self {
            state: ScientificDataSetState::Available { data },
        })
    }

    pub fn not_produced(reason: ScientificReason) -> Self {
        Self {
            state: ScientificDataSetState::NotProduced { reason },
        }
    }

    pub fn not_applicable(reason: ScientificReason) -> Self {
        Self {
            state: ScientificDataSetState::NotApplicable { reason },
        }
    }

    pub fn status(&self) -> ScientificArtifactStatus {
        match self.state {
            ScientificDataSetState::Available { .. } => ScientificArtifactStatus::Available,
            ScientificDataSetState::NotProduced { .. } => ScientificArtifactStatus::NotProduced,
            ScientificDataSetState::NotApplicable { .. } => ScientificArtifactStatus::NotApplicable,
        }
    }

    pub fn data(&self) -> Option<&[ScientificDataIdentity]> {
        match &self.state {
            ScientificDataSetState::Available { data } => Some(data),
            ScientificDataSetState::NotProduced { .. }
            | ScientificDataSetState::NotApplicable { .. } => None,
        }
    }

    pub fn reason(&self) -> Option<&ScientificReason> {
        match &self.state {
            ScientificDataSetState::Available { .. } => None,
            ScientificDataSetState::NotProduced { reason }
            | ScientificDataSetState::NotApplicable { reason } => Some(reason),
        }
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificDataSetSerialize<'a> {
    Available { data: &'a [ScientificDataIdentity] },
    NotProduced { reason: &'a ScientificReason },
    NotApplicable { reason: &'a ScientificReason },
}

impl Serialize for ScientificDataSet {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match &self.state {
            ScientificDataSetState::Available { data } => {
                ScientificDataSetSerialize::Available { data }
            }
            ScientificDataSetState::NotProduced { reason } => {
                ScientificDataSetSerialize::NotProduced { reason }
            }
            ScientificDataSetState::NotApplicable { reason } => {
                ScientificDataSetSerialize::NotApplicable { reason }
            }
        }
        .serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificDataSetDeserialize {
    Available {
        data: BoundedVec<ScientificDataIdentity, MAX_DATA_IDENTITIES>,
    },
    NotProduced {
        reason: ScientificReason,
    },
    NotApplicable {
        reason: ScientificReason,
    },
}

impl<'de> Deserialize<'de> for ScientificDataSet {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificDataSetDeserialize::deserialize(deserializer)? {
            ScientificDataSetDeserialize::Available { data } => {
                Self::available(data.into_vec()).map_err(serde::de::Error::custom)
            }
            ScientificDataSetDeserialize::NotProduced { reason } => Ok(Self::not_produced(reason)),
            ScientificDataSetDeserialize::NotApplicable { reason } => {
                Ok(Self::not_applicable(reason))
            }
        }
    }
}

/// Ordered transform lineage from source data to estimator data.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificDataLineage {
    contract_revision: u32,
    source_data: ScientificDataSet,
    transforms: Vec<ScientificTransformEdge>,
    estimator_data: ScientificDataSet,
    identity: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificDataLineageWire {
    contract_revision: u32,
    source_data: ScientificDataSet,
    transforms: BoundedVec<ScientificTransformEdge, MAX_TRANSFORMS>,
    estimator_data: ScientificDataSet,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificDataLineagePreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    source_data: &'a ScientificDataSet,
    transforms: &'a [ScientificTransformEdge],
    estimator_data: &'a ScientificDataSet,
}

impl ScientificDataLineage {
    pub fn new(
        source_data: ScientificDataSet,
        transforms: Vec<ScientificTransformEdge>,
        estimator_data: ScientificDataSet,
    ) -> Result<Self> {
        if transforms.len() > MAX_TRANSFORMS {
            anyhow::bail!("scientific lineage exceeds {MAX_TRANSFORMS} transforms");
        }
        let mut step_ids = BTreeSet::new();
        if transforms
            .iter()
            .any(|step| !step_ids.insert(step.step_id.as_str()))
        {
            anyhow::bail!("scientific transform step IDs must be unique");
        }
        match (source_data.data(), estimator_data.data()) {
            (Some(source), estimator) => {
                let mut previous = source;
                for step in &transforms {
                    if step.inputs != previous {
                        anyhow::bail!(
                            "scientific transform inputs do not match the previous output"
                        );
                    }
                    previous = &step.outputs;
                }
                if estimator.is_some_and(|estimator| previous != estimator) {
                    anyhow::bail!("scientific lineage does not end at the estimator data");
                }
            }
            (None, None)
                if transforms.is_empty() && source_data.status() == estimator_data.status() => {}
            _ => anyhow::bail!(
                "scientific lineage needs available source data or matching absent endpoints"
            ),
        }
        let preimage = ScientificDataLineagePreimage {
            domain: "pid-rs/scientific-data-lineage/v1",
            contract_revision: CONTRACT_REVISION,
            source_data: &source_data,
            transforms: &transforms,
            estimator_data: &estimator_data,
        };
        let identity = VersionedContentIdentity::new(
            "pid-rs/scientific-data-lineage",
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            source_data,
            transforms,
            estimator_data,
            identity,
        })
    }

    pub fn source_data(&self) -> &ScientificDataSet {
        &self.source_data
    }

    pub fn transforms(&self) -> &[ScientificTransformEdge] {
        &self.transforms
    }

    pub fn estimator_data(&self) -> &ScientificDataSet {
        &self.estimator_data
    }

    /// Return the latest available data in the lineage.
    pub fn latest_available_data(&self) -> Option<&[ScientificDataIdentity]> {
        self.estimator_data
            .data()
            .or_else(|| self.transforms.last().map(|transform| transform.outputs()))
            .or_else(|| self.source_data.data())
    }

    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }

    /// Compute the group identity for all ordered edges of one transform kind.
    pub fn transform_group_identity(
        &self,
        kind: ScientificTransformKind,
    ) -> Result<Option<VersionedContentIdentity>> {
        transform_group_identity(kind, &self.transforms)
    }
}

#[derive(Serialize)]
struct ScientificTransformGroupPreimage<'a> {
    domain: &'static str,
    kind: ScientificTransformKind,
    transforms: Vec<&'a ScientificTransformEdge>,
}

fn transform_kind_label(kind: ScientificTransformKind) -> &'static str {
    match kind {
        ScientificTransformKind::Preprocessing => "preprocessing",
        ScientificTransformKind::ObservationModel => "observation-model",
        ScientificTransformKind::Resampling => "resampling",
    }
}

fn transform_group_identity(
    kind: ScientificTransformKind,
    transforms: &[ScientificTransformEdge],
) -> Result<Option<VersionedContentIdentity>> {
    let matching = transforms
        .iter()
        .filter(|transform| transform.kind == kind)
        .collect::<Vec<_>>();
    if matching.is_empty() {
        return Ok(None);
    }
    let preimage = ScientificTransformGroupPreimage {
        domain: "pid-rs/scientific-transform-group/v1",
        kind,
        transforms: matching,
    };
    Ok(Some(VersionedContentIdentity::new(
        format!(
            "pid-rs/scientific-transform-group/{}",
            transform_kind_label(kind)
        ),
        "1",
        canonical_scientific_identity(&preimage)?,
    )?))
}

impl<'de> Deserialize<'de> for ScientificDataLineage {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificDataLineageWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific data lineage revision",
            ));
        }
        let expected = wire.identity;
        let lineage = Self::new(
            wire.source_data,
            wire.transforms.into_vec(),
            wire.estimator_data,
        )
        .map_err(serde::de::Error::custom)?;
        if lineage.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific data lineage identity does not match its canonical preimage",
            ));
        }
        Ok(lineage)
    }
}

/// Role of one sample-membership identity.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificSplitRole {
    /// All rows in the source data set.
    FullSample,
    /// Rows used to fit a model or preprocessing state.
    Training,
    /// Rows used to select settings during development.
    Validation,
    /// Rows reserved for a final test.
    Test,
    /// Rows on which this estimator is evaluated.
    Evaluation,
    /// An ordered resample, which can contain repeated rows.
    Resample,
}

/// A declared ordered membership identity for one split or resample.
///
/// Use [`scientific_split_membership_identity_v1`] to compute a supported membership identity.
/// The constructor does not read the partition manifest or parent row ledger. It cannot prove that
/// members belong to the parent ledger, that splits are disjoint, or that splits cover the parent
/// rows.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificSplitIdentity {
    role: ScientificSplitRole,
    split_name: String,
    membership: ScientificMembershipIdentity,
    parent_row_ledger: VersionedContentIdentity,
    partition_manifest: ScientificArtifactIdentity,
    identity: VersionedContentIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificSplitIdentityWire {
    role: ScientificSplitRole,
    split_name: String,
    membership: ScientificMembershipIdentity,
    parent_row_ledger: VersionedContentIdentity,
    partition_manifest: ScientificArtifactIdentity,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificSplitPreimage<'a> {
    domain: &'static str,
    role: ScientificSplitRole,
    split_name: &'a str,
    membership: &'a ScientificMembershipIdentity,
    parent_row_ledger: &'a VersionedContentIdentity,
    partition_manifest: &'a ScientificArtifactIdentity,
}

impl ScientificSplitIdentity {
    pub fn new(
        role: ScientificSplitRole,
        split_name: impl Into<String>,
        membership: ScientificMembershipIdentity,
        parent_row_ledger: VersionedContentIdentity,
        partition_manifest: ScientificArtifactIdentity,
    ) -> Result<Self> {
        let split_name = split_name.into();
        validate_machine_text("scientific split name", &split_name)?;
        if role != ScientificSplitRole::Resample
            && membership.unique_member_count() != membership.member_count()
        {
            anyhow::bail!("only a resample split can contain repeated member identifiers");
        }
        match role {
            ScientificSplitRole::FullSample => {
                if partition_manifest.status() != ScientificArtifactStatus::NotApplicable {
                    anyhow::bail!("a full-sample split needs a not-applicable partition manifest");
                }
            }
            ScientificSplitRole::Training
            | ScientificSplitRole::Validation
            | ScientificSplitRole::Test
            | ScientificSplitRole::Evaluation
            | ScientificSplitRole::Resample => {
                if partition_manifest.status() != ScientificArtifactStatus::Available {
                    anyhow::bail!("a non-full split needs an available partition manifest");
                }
            }
        }
        let preimage = ScientificSplitPreimage {
            domain: "pid-rs/scientific-split/v1",
            role,
            split_name: &split_name,
            membership: &membership,
            parent_row_ledger: &parent_row_ledger,
            partition_manifest: &partition_manifest,
        };
        let identity = VersionedContentIdentity::new(
            format!("pid-rs/scientific-split/{split_name}"),
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            role,
            split_name,
            membership,
            parent_row_ledger,
            partition_manifest,
            identity,
        })
    }

    pub fn role(&self) -> ScientificSplitRole {
        self.role
    }

    pub fn split_name(&self) -> &str {
        &self.split_name
    }

    pub fn membership_hash(&self) -> &ScientificHashIdentity {
        self.membership.content_hash()
    }

    /// Return the typed membership identity, including its encoded count.
    pub fn membership_identity(&self) -> &ScientificMembershipIdentity {
        &self.membership
    }

    pub fn member_count(&self) -> u64 {
        self.membership.member_count()
    }

    pub fn parent_row_ledger(&self) -> &VersionedContentIdentity {
        &self.parent_row_ledger
    }

    pub fn partition_manifest(&self) -> &ScientificArtifactIdentity {
        &self.partition_manifest
    }

    /// Return the identity that covers this complete split declaration.
    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }
}

impl<'de> Deserialize<'de> for ScientificSplitIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificSplitIdentityWire::deserialize(deserializer)?;
        let expected = wire.identity;
        let split = Self::new(
            wire.role,
            wire.split_name,
            wire.membership,
            wire.parent_row_ledger,
            wire.partition_manifest,
        )
        .map_err(serde::de::Error::custom)?;
        if split.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific split identity does not match its canonical preimage",
            ));
        }
        Ok(split)
    }
}

/// Selected estimator split or an explicit reason that no split was selected.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
#[non_exhaustive]
pub enum ScientificSplitSelection {
    /// The estimator used the named split.
    Selected { split_name: String },
    /// The workflow did not produce an estimator split.
    NotProduced { reason: ScientificReason },
    /// An estimator split does not apply to this outcome.
    NotApplicable { reason: ScientificReason },
}

impl ScientificSplitSelection {
    pub fn selected(split_name: impl Into<String>) -> Result<Self> {
        let split_name = split_name.into();
        validate_machine_text("scientific estimator split", &split_name)?;
        Ok(Self::Selected { split_name })
    }

    pub fn not_produced(reason: ScientificReason) -> Self {
        Self::NotProduced { reason }
    }

    pub fn not_applicable(reason: ScientificReason) -> Self {
        Self::NotApplicable { reason }
    }

    pub fn split_name(&self) -> Option<&str> {
        match self {
            Self::Selected { split_name } => Some(split_name),
            Self::NotProduced { .. } | Self::NotApplicable { .. } => None,
        }
    }

    pub fn status(&self) -> ScientificArtifactStatus {
        match self {
            Self::Selected { .. } => ScientificArtifactStatus::Available,
            Self::NotProduced { .. } => ScientificArtifactStatus::NotProduced,
            Self::NotApplicable { .. } => ScientificArtifactStatus::NotApplicable,
        }
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificSplitSelectionWire {
    Selected { split_name: String },
    NotProduced { reason: ScientificReason },
    NotApplicable { reason: ScientificReason },
}

impl<'de> Deserialize<'de> for ScientificSplitSelection {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificSplitSelectionWire::deserialize(deserializer)? {
            ScientificSplitSelectionWire::Selected { split_name } => {
                Self::selected(split_name).map_err(serde::de::Error::custom)
            }
            ScientificSplitSelectionWire::NotProduced { reason } => Ok(Self::not_produced(reason)),
            ScientificSplitSelectionWire::NotApplicable { reason } => {
                Ok(Self::not_applicable(reason))
            }
        }
    }
}

/// Availability of a population-support declaration.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificSupportStatus {
    /// A contract explicitly covers the named marginal and joint laws.
    Declared,
    /// The caller did not specify a population-support contract.
    Unspecified,
    /// No support contract is available for this requested method.
    Unsupported,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum ScientificSupportState {
    Declared {
        contract: VersionedContentIdentity,
        covered_variable_sets: Vec<Vec<String>>,
        application_envelope: Option<VersionedContentIdentity>,
        declaration_identity: Box<VersionedContentIdentity>,
    },
    Unspecified {
        reason: ScientificReason,
    },
    Unsupported {
        reason: ScientificReason,
    },
}

/// A typed population-support state with explicit marginal and joint coverage.
#[derive(Debug, Clone, PartialEq, Eq)]
#[non_exhaustive]
pub struct ScientificSupportIdentity {
    state: ScientificSupportState,
}

#[derive(Serialize)]
struct ScientificSupportDeclarationPreimage<'a> {
    domain: &'static str,
    contract: &'a VersionedContentIdentity,
    covered_variable_sets: &'a [Vec<String>],
    application_envelope: &'a Option<VersionedContentIdentity>,
}

impl ScientificSupportIdentity {
    pub fn declared(
        contract: VersionedContentIdentity,
        mut covered_variable_sets: Vec<Vec<String>>,
        application_envelope: Option<VersionedContentIdentity>,
    ) -> Result<Self> {
        if covered_variable_sets.is_empty() || covered_variable_sets.len() > MAX_SUPPORT_SETS {
            anyhow::bail!("support coverage needs 1..={MAX_SUPPORT_SETS} variable sets");
        }
        for variables in &mut covered_variable_sets {
            if variables.is_empty() || variables.len() > MAX_DATA_IDENTITIES {
                anyhow::bail!("each support coverage set must be nonempty and bounded");
            }
            for variable in variables.iter() {
                validate_machine_text("support variable ID", variable)?;
            }
            variables.sort();
            if variables.windows(2).any(|pair| pair[0] == pair[1]) {
                anyhow::bail!("a support coverage set must not repeat a variable");
            }
        }
        covered_variable_sets.sort();
        if covered_variable_sets
            .windows(2)
            .any(|pair| pair[0] == pair[1])
        {
            anyhow::bail!("support coverage sets must be unique");
        }
        let preimage = ScientificSupportDeclarationPreimage {
            domain: "pid-rs/scientific-support-declaration/v1",
            contract: &contract,
            covered_variable_sets: &covered_variable_sets,
            application_envelope: &application_envelope,
        };
        let declaration_identity = VersionedContentIdentity::new(
            "pid-rs/scientific-support-declaration",
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            state: ScientificSupportState::Declared {
                contract,
                covered_variable_sets,
                application_envelope,
                declaration_identity: Box::new(declaration_identity),
            },
        })
    }

    pub fn unspecified(reason: ScientificReason) -> Self {
        Self {
            state: ScientificSupportState::Unspecified { reason },
        }
    }

    pub fn unsupported(reason: ScientificReason) -> Self {
        Self {
            state: ScientificSupportState::Unsupported { reason },
        }
    }

    pub fn status(&self) -> ScientificSupportStatus {
        match self.state {
            ScientificSupportState::Declared { .. } => ScientificSupportStatus::Declared,
            ScientificSupportState::Unspecified { .. } => ScientificSupportStatus::Unspecified,
            ScientificSupportState::Unsupported { .. } => ScientificSupportStatus::Unsupported,
        }
    }

    pub fn declared_contract(&self) -> Option<&VersionedContentIdentity> {
        match &self.state {
            ScientificSupportState::Declared { contract, .. } => Some(contract),
            ScientificSupportState::Unspecified { .. }
            | ScientificSupportState::Unsupported { .. } => None,
        }
    }

    /// Return the identity that covers the contract, tuple coverage, and application envelope.
    pub fn declaration_identity(&self) -> Option<&VersionedContentIdentity> {
        match &self.state {
            ScientificSupportState::Declared {
                declaration_identity,
                ..
            } => Some(declaration_identity.as_ref()),
            ScientificSupportState::Unspecified { .. }
            | ScientificSupportState::Unsupported { .. } => None,
        }
    }

    pub fn covered_variable_sets(&self) -> &[Vec<String>] {
        match &self.state {
            ScientificSupportState::Declared {
                covered_variable_sets,
                ..
            } => covered_variable_sets,
            ScientificSupportState::Unspecified { .. }
            | ScientificSupportState::Unsupported { .. } => &[],
        }
    }

    pub fn application_envelope(&self) -> Option<&VersionedContentIdentity> {
        match &self.state {
            ScientificSupportState::Declared {
                application_envelope,
                ..
            } => application_envelope.as_ref(),
            ScientificSupportState::Unspecified { .. }
            | ScientificSupportState::Unsupported { .. } => None,
        }
    }

    pub fn reason(&self) -> Option<&ScientificReason> {
        match &self.state {
            ScientificSupportState::Declared { .. } => None,
            ScientificSupportState::Unspecified { reason }
            | ScientificSupportState::Unsupported { reason } => Some(reason),
        }
    }

    fn covers_all_nonempty_subsets(&self, variables: &[String]) -> bool {
        let ScientificSupportState::Declared {
            covered_variable_sets,
            ..
        } = &self.state
        else {
            return false;
        };
        let expected_count = (1usize << variables.len()) - 1;
        if covered_variable_sets.len() != expected_count {
            return false;
        }
        (1usize..=expected_count).all(|mask| {
            let subset = variables
                .iter()
                .enumerate()
                .filter(|(index, _)| mask & (1usize << index) != 0)
                .map(|(_, variable)| variable.clone())
                .collect::<Vec<_>>();
            covered_variable_sets.binary_search(&subset).is_ok()
        })
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificSupportSerialize<'a> {
    Declared {
        contract: &'a VersionedContentIdentity,
        covered_variable_sets: &'a [Vec<String>],
        #[serde(skip_serializing_if = "Option::is_none")]
        application_envelope: &'a Option<VersionedContentIdentity>,
        declaration_identity: &'a VersionedContentIdentity,
    },
    Unspecified {
        reason: &'a ScientificReason,
    },
    Unsupported {
        reason: &'a ScientificReason,
    },
}

impl Serialize for ScientificSupportIdentity {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        match &self.state {
            ScientificSupportState::Declared {
                contract,
                covered_variable_sets,
                application_envelope,
                declaration_identity,
            } => ScientificSupportSerialize::Declared {
                contract,
                covered_variable_sets,
                application_envelope,
                declaration_identity,
            },
            ScientificSupportState::Unspecified { reason } => {
                ScientificSupportSerialize::Unspecified { reason }
            }
            ScientificSupportState::Unsupported { reason } => {
                ScientificSupportSerialize::Unsupported { reason }
            }
        }
        .serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificSupportDeserialize {
    Declared {
        contract: VersionedContentIdentity,
        covered_variable_sets:
            BoundedVec<BoundedVec<String, MAX_DATA_IDENTITIES>, MAX_SUPPORT_SETS>,
        #[serde(default)]
        application_envelope: Option<VersionedContentIdentity>,
        declaration_identity: Box<VersionedContentIdentity>,
    },
    Unspecified {
        reason: ScientificReason,
    },
    Unsupported {
        reason: ScientificReason,
    },
}

impl<'de> Deserialize<'de> for ScientificSupportIdentity {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificSupportDeserialize::deserialize(deserializer)? {
            ScientificSupportDeserialize::Declared {
                contract,
                covered_variable_sets,
                application_envelope,
                declaration_identity,
            } => {
                let expected = *declaration_identity;
                let support = Self::declared(
                    contract,
                    covered_variable_sets
                        .into_vec()
                        .into_iter()
                        .map(BoundedVec::into_vec)
                        .collect(),
                    application_envelope,
                )
                .map_err(serde::de::Error::custom)?;
                if support.declaration_identity() != Some(&expected) {
                    return Err(serde::de::Error::custom(
                        "scientific support declaration identity does not match its canonical preimage",
                    ));
                }
                Ok(support)
            }
            ScientificSupportDeserialize::Unspecified { reason } => Ok(Self::unspecified(reason)),
            ScientificSupportDeserialize::Unsupported { reason } => Ok(Self::unsupported(reason)),
        }
    }
}

/// Verdict of one separate scientific gate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificGateVerdict {
    /// The gate passed and has at least one evidence identity.
    Passed,
    /// The gate passed only under the condition in its reason.
    Conditional,
    /// The gate was not evaluated.
    NotEvaluated,
    /// The gate did not pass and blocks the claim.
    Blocked,
    /// This gate does not apply to the declared method or outcome.
    NotApplicable,
}

/// One gate verdict, coded reason, and list of evidence identities.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificGateDecision {
    verdict: ScientificGateVerdict,
    reason: ScientificReason,
    evidence: Vec<VersionedContentIdentity>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificGateDecisionWire {
    verdict: ScientificGateVerdict,
    reason: ScientificReason,
    evidence: BoundedVec<VersionedContentIdentity, MAX_EVIDENCE_ITEMS>,
}

impl ScientificGateDecision {
    /// Construct a checked gate decision.
    ///
    /// A passed gate needs at least one unique evidence identity. A gate that does not apply must
    /// not contain evidence. This function checks the records but does not recompute their digests.
    pub fn new(
        verdict: ScientificGateVerdict,
        reason: ScientificReason,
        mut evidence: Vec<VersionedContentIdentity>,
    ) -> Result<Self> {
        if evidence.len() > MAX_EVIDENCE_ITEMS {
            anyhow::bail!("scientific gate evidence exceeds {MAX_EVIDENCE_ITEMS} items");
        }
        if verdict == ScientificGateVerdict::Passed && evidence.is_empty() {
            anyhow::bail!("a passed scientific gate needs content-addressed evidence");
        }
        if verdict == ScientificGateVerdict::NotApplicable && !evidence.is_empty() {
            anyhow::bail!("a not-applicable scientific gate must not name evidence");
        }
        evidence.sort();
        if evidence.windows(2).any(|pair| pair[0] == pair[1]) {
            anyhow::bail!("scientific gate evidence must not contain duplicates");
        }
        Ok(Self {
            verdict,
            reason,
            evidence,
        })
    }

    pub fn verdict(&self) -> ScientificGateVerdict {
        self.verdict
    }

    pub fn reason(&self) -> &ScientificReason {
        &self.reason
    }

    pub fn evidence(&self) -> &[VersionedContentIdentity] {
        &self.evidence
    }

    fn has_evidence(&self, identity: &VersionedContentIdentity) -> bool {
        self.evidence.binary_search(identity).is_ok()
    }
}

impl<'de> Deserialize<'de> for ScientificGateDecision {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificGateDecisionWire::deserialize(deserializer)?;
        Self::new(wire.verdict, wire.reason, wire.evidence.into_vec())
            .map_err(serde::de::Error::custom)
    }
}

/// Explicit decision about whether the recorded outcome can be interpreted.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct InterpretationDecision {
    allowed: bool,
    reason: ScientificReason,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct InterpretationDecisionWire {
    allowed: bool,
    reason: ScientificReason,
}

impl InterpretationDecision {
    pub fn new(allowed: bool, reason: ScientificReason) -> Self {
        Self { allowed, reason }
    }

    pub fn allowed(&self) -> bool {
        self.allowed
    }

    pub fn reason(&self) -> &ScientificReason {
        &self.reason
    }
}

impl<'de> Deserialize<'de> for InterpretationDecision {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = InterpretationDecisionWire::deserialize(deserializer)?;
        Ok(Self::new(wire.allowed, wire.reason))
    }
}

/// Four separate scientific gate decisions and one interpretation decision.
///
/// The population gate records a decision about population assumptions. The measure gate records a
/// decision about whether the mathematical quantity suits the question. The estimator gate records
/// a decision about use of the estimator in the declared regime. The application gate records a
/// decision about the stated application and sampling process.
///
/// The constructors check required evidence identities for passed gates. They do not evaluate the
/// scientific content of that evidence.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificGateSet {
    contract_revision: u32,
    population: ScientificGateDecision,
    measure: ScientificGateDecision,
    estimator: ScientificGateDecision,
    application: ScientificGateDecision,
    interpretation: InterpretationDecision,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificGateSetWire {
    contract_revision: u32,
    population: ScientificGateDecision,
    measure: ScientificGateDecision,
    estimator: ScientificGateDecision,
    application: ScientificGateDecision,
    interpretation: InterpretationDecision,
}

impl ScientificGateSet {
    /// Construct four gates and their interpretation decision.
    ///
    /// An allowed interpretation requires all four gates to pass. The decision can still deny
    /// interpretation after all four gates pass.
    pub fn new(
        population: ScientificGateDecision,
        measure: ScientificGateDecision,
        estimator: ScientificGateDecision,
        application: ScientificGateDecision,
        interpretation: InterpretationDecision,
    ) -> Result<Self> {
        let gates = Self {
            contract_revision: CONTRACT_REVISION,
            population,
            measure,
            estimator,
            application,
            interpretation,
        };
        if gates.interpretation.allowed && !gates.all_passed() {
            anyhow::bail!("interpretation requires all four scientific gates to pass");
        }
        Ok(gates)
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn population(&self) -> &ScientificGateDecision {
        &self.population
    }

    pub fn measure(&self) -> &ScientificGateDecision {
        &self.measure
    }

    pub fn estimator(&self) -> &ScientificGateDecision {
        &self.estimator
    }

    pub fn application(&self) -> &ScientificGateDecision {
        &self.application
    }

    pub fn interpretation(&self) -> &InterpretationDecision {
        &self.interpretation
    }

    pub fn all_passed(&self) -> bool {
        self.decisions()
            .iter()
            .all(|decision| decision.verdict == ScientificGateVerdict::Passed)
    }

    pub fn all_not_applicable(&self) -> bool {
        self.decisions()
            .iter()
            .all(|decision| decision.verdict == ScientificGateVerdict::NotApplicable)
    }

    fn decisions(&self) -> [&ScientificGateDecision; 4] {
        [
            &self.population,
            &self.measure,
            &self.estimator,
            &self.application,
        ]
    }

    fn has_nonpassing_reason(&self, code: &ScientificReasonCode) -> bool {
        self.decisions().iter().any(|decision| {
            matches!(
                decision.verdict,
                ScientificGateVerdict::Conditional
                    | ScientificGateVerdict::NotEvaluated
                    | ScientificGateVerdict::Blocked
            ) && decision.reason.code == *code
        })
    }
}

impl<'de> Deserialize<'de> for ScientificGateSet {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificGateSetWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific gate contract revision",
            ));
        }
        Self::new(
            wire.population,
            wire.measure,
            wire.estimator,
            wire.application,
            wire.interpretation,
        )
        .map_err(serde::de::Error::custom)
    }
}

/// Stage at which one logical calculation stopped.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificStopStage {
    /// The run did not activate this candidate outcome.
    NotRequested,
    /// The run stopped before preflight passed.
    Preflight,
    /// Preflight passed, but estimation did not complete.
    Estimation,
    /// Estimation completed.
    Complete,
}

/// Fixed application-stage facts for one logical outcome.
///
/// These facts are separate from scientific gates. `preflight_passed` does not require
/// `declared_support_compatible`. For example, a discrete estimate can pass preflight without a
/// continuous-support declaration. Estimation requires a passed preflight. A later numerical
/// failure can therefore retain `preflight_passed = true` and `estimated = false`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificStageSet {
    contract_revision: u32,
    requested: bool,
    declared_support_compatible: bool,
    preflight_passed: bool,
    estimated: bool,
    stop_stage: ScientificStopStage,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificStageSetWire {
    contract_revision: u32,
    requested: bool,
    declared_support_compatible: bool,
    preflight_passed: bool,
    estimated: bool,
    stop_stage: ScientificStopStage,
}

impl ScientificStageSet {
    pub fn not_requested() -> Self {
        Self {
            contract_revision: CONTRACT_REVISION,
            requested: false,
            declared_support_compatible: false,
            preflight_passed: false,
            estimated: false,
            stop_stage: ScientificStopStage::NotRequested,
        }
    }

    pub fn requested(
        declared_support_compatible: bool,
        preflight_passed: bool,
        estimated: bool,
    ) -> Result<Self> {
        if estimated && !preflight_passed {
            anyhow::bail!("an estimated outcome needs a passed preflight");
        }
        let stop_stage = if estimated {
            ScientificStopStage::Complete
        } else if preflight_passed {
            ScientificStopStage::Estimation
        } else {
            ScientificStopStage::Preflight
        };
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            requested: true,
            declared_support_compatible,
            preflight_passed,
            estimated,
            stop_stage,
        })
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn was_requested(&self) -> bool {
        self.requested
    }

    pub fn declared_support_compatible(&self) -> bool {
        self.declared_support_compatible
    }

    pub fn preflight_passed(&self) -> bool {
        self.preflight_passed
    }

    pub fn estimated(&self) -> bool {
        self.estimated
    }

    /// Return the stage at which this calculation stopped.
    pub fn stop_stage(&self) -> ScientificStopStage {
        self.stop_stage
    }

    fn is_not_requested(&self) -> bool {
        !self.requested
            && !self.declared_support_compatible
            && !self.preflight_passed
            && !self.estimated
            && self.stop_stage == ScientificStopStage::NotRequested
    }
}

impl<'de> Deserialize<'de> for ScientificStageSet {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificStageSetWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific stage contract revision",
            ));
        }
        if !wire.requested {
            let stages = Self::not_requested();
            if wire.declared_support_compatible || wire.preflight_passed || wire.estimated {
                return Err(serde::de::Error::custom(
                    "a not-requested stage set must contain only false facts",
                ));
            }
            if wire.stop_stage != ScientificStopStage::NotRequested {
                return Err(serde::de::Error::custom(
                    "a not-requested stage set needs the not-requested stop stage",
                ));
            }
            Ok(stages)
        } else {
            let stages = Self::requested(
                wire.declared_support_compatible,
                wire.preflight_passed,
                wire.estimated,
            )
            .map_err(serde::de::Error::custom)?;
            if stages.stop_stage != wire.stop_stage {
                return Err(serde::de::Error::custom(
                    "scientific stop stage does not match its stage facts",
                ));
            }
            Ok(stages)
        }
    }
}

/// A checked and deterministically ordered set of named information values.
///
/// One logical calculation can produce several values. For example, one PID2 calculation can
/// produce redundancy, two unique terms, synergy, and mutual-information terms. An adapter must
/// put all values from one logical calculation in one set. A future event-stream validator must
/// reject duplicate outcome IDs and require complete ledger coverage before it counts reports.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(transparent)]
pub struct ScientificValueSet(BTreeMap<String, f64>);

impl ScientificValueSet {
    pub fn new(mut values_nats: BTreeMap<String, f64>) -> Result<Self> {
        if values_nats.is_empty() || values_nats.len() > MAX_NAMED_VALUES {
            anyhow::bail!("scientific value set needs 1..={MAX_NAMED_VALUES} entries");
        }
        for (name, value) in &mut values_nats {
            validate_machine_text("scientific value name", name)?;
            if !value.is_finite() {
                anyhow::bail!("each produced scientific value must be finite");
            }
            if *value == 0.0 {
                *value = 0.0;
            }
        }
        Ok(Self(values_nats))
    }

    pub fn try_from_pairs<I, K>(pairs: I) -> Result<Self>
    where
        I: IntoIterator<Item = (K, f64)>,
        K: Into<String>,
    {
        let mut values = BTreeMap::new();
        for (name, value) in pairs {
            if values.len() == MAX_NAMED_VALUES {
                anyhow::bail!("scientific value set exceeds {MAX_NAMED_VALUES} entries");
            }
            let name = name.into();
            if values.insert(name.clone(), value).is_some() {
                anyhow::bail!("scientific value names must be unique: {name}");
            }
        }
        Self::new(values)
    }

    pub fn scalar(name: impl Into<String>, value_nats: f64) -> Result<Self> {
        Self::try_from_pairs([(name, value_nats)])
    }

    pub fn as_map(&self) -> &BTreeMap<String, f64> {
        &self.0
    }
}

struct ScientificValueSetVisitor;

impl<'de> Visitor<'de> for ScientificValueSetVisitor {
    type Value = ScientificValueSet;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("a nonempty bounded map of names to finite JSON numbers")
    }

    fn visit_map<A>(self, mut map: A) -> std::result::Result<Self::Value, A::Error>
    where
        A: MapAccess<'de>,
    {
        let mut values = BTreeMap::new();
        while values.len() < MAX_NAMED_VALUES {
            let Some(name) = map.next_key::<String>()? else {
                return ScientificValueSet::new(values).map_err(serde::de::Error::custom);
            };
            validate_machine_text("scientific value name", &name)
                .map_err(serde::de::Error::custom)?;
            if values.contains_key(&name) {
                return Err(serde::de::Error::custom(format!(
                    "duplicate scientific value name: {name}"
                )));
            }
            let JsonF64(value) = map.next_value::<JsonF64>()?;
            values.insert(name, value);
        }
        if map.next_key::<IgnoredAny>()?.is_some() {
            let _: IgnoredAny = map.next_value()?;
            return Err(serde::de::Error::custom(format!(
                "scientific value set exceeds {MAX_NAMED_VALUES} entries"
            )));
        }
        ScientificValueSet::new(values).map_err(serde::de::Error::custom)
    }
}

impl<'de> Deserialize<'de> for ScientificValueSet {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        deserializer.deserialize_map(ScientificValueSetVisitor)
    }
}

/// Typed computation state. Only produced states carry named values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum ScientificOutcomeStatus {
    /// The caller did not request this outcome.
    NotRequested,
    /// The calculation produced all required named values without a use warning.
    Produced,
    /// The calculation produced all required named values with one or more use warnings.
    ProducedWithWarning,
    /// The caller requested the outcome, but the calculation produced no values.
    Abstained,
}

#[derive(Debug, Clone, PartialEq)]
enum ScientificOutcomeState {
    NotRequested {
        reason: ScientificReason,
    },
    Produced {
        values_nats: ScientificValueSet,
    },
    ProducedWithWarning {
        values_nats: ScientificValueSet,
        warnings: Vec<ScientificWarning>,
    },
    Abstained {
        reason: ScientificReason,
    },
}

/// Checked tagged computation outcome.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct ScientificComputationOutcome {
    state: ScientificOutcomeState,
}

impl ScientificComputationOutcome {
    pub fn not_requested(reason: ScientificReason) -> Self {
        Self {
            state: ScientificOutcomeState::NotRequested { reason },
        }
    }

    pub fn produced(values_nats: ScientificValueSet) -> Self {
        Self {
            state: ScientificOutcomeState::Produced { values_nats },
        }
    }

    pub fn produced_scalar(name: impl Into<String>, value_nats: f64) -> Result<Self> {
        Ok(Self::produced(ScientificValueSet::scalar(
            name, value_nats,
        )?))
    }

    pub fn produced_with_warning(
        values_nats: ScientificValueSet,
        mut warnings: Vec<ScientificWarning>,
    ) -> Result<Self> {
        if warnings.is_empty() {
            anyhow::bail!("produced-with-warning needs at least one warning");
        }
        if warnings.len() > MAX_EVIDENCE_ITEMS {
            anyhow::bail!("scientific warnings exceed {MAX_EVIDENCE_ITEMS} items");
        }
        warnings.sort_by(|left, right| left.code.cmp(&right.code));
        if warnings.windows(2).any(|pair| pair[0].code == pair[1].code) {
            anyhow::bail!("scientific warning codes must be unique");
        }
        Ok(Self {
            state: ScientificOutcomeState::ProducedWithWarning {
                values_nats,
                warnings,
            },
        })
    }

    pub fn abstained(reason: ScientificReason) -> Self {
        Self {
            state: ScientificOutcomeState::Abstained { reason },
        }
    }

    pub fn status(&self) -> ScientificOutcomeStatus {
        match &self.state {
            ScientificOutcomeState::NotRequested { .. } => ScientificOutcomeStatus::NotRequested,
            ScientificOutcomeState::Produced { .. } => ScientificOutcomeStatus::Produced,
            ScientificOutcomeState::ProducedWithWarning { .. } => {
                ScientificOutcomeStatus::ProducedWithWarning
            }
            ScientificOutcomeState::Abstained { .. } => ScientificOutcomeStatus::Abstained,
        }
    }

    pub fn values_nats(&self) -> Option<&ScientificValueSet> {
        match &self.state {
            ScientificOutcomeState::Produced { values_nats }
            | ScientificOutcomeState::ProducedWithWarning { values_nats, .. } => Some(values_nats),
            ScientificOutcomeState::NotRequested { .. }
            | ScientificOutcomeState::Abstained { .. } => None,
        }
    }

    pub fn reason(&self) -> Option<&ScientificReason> {
        match &self.state {
            ScientificOutcomeState::NotRequested { reason }
            | ScientificOutcomeState::Abstained { reason } => Some(reason),
            ScientificOutcomeState::Produced { .. }
            | ScientificOutcomeState::ProducedWithWarning { .. } => None,
        }
    }

    pub fn warnings(&self) -> &[ScientificWarning] {
        match &self.state {
            ScientificOutcomeState::ProducedWithWarning { warnings, .. } => warnings,
            ScientificOutcomeState::NotRequested { .. }
            | ScientificOutcomeState::Produced { .. }
            | ScientificOutcomeState::Abstained { .. } => &[],
        }
    }
}

#[derive(Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
enum ScientificOutcomeSerialize<'a> {
    NotRequested {
        reason: &'a ScientificReason,
    },
    Produced {
        values_nats: &'a ScientificValueSet,
    },
    ProducedWithWarning {
        values_nats: &'a ScientificValueSet,
        warnings: &'a [ScientificWarning],
    },
    Abstained {
        reason: &'a ScientificReason,
    },
}

impl Serialize for ScientificComputationOutcome {
    fn serialize<S>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let wire = match &self.state {
            ScientificOutcomeState::NotRequested { reason } => {
                ScientificOutcomeSerialize::NotRequested { reason }
            }
            ScientificOutcomeState::Produced { values_nats } => {
                ScientificOutcomeSerialize::Produced { values_nats }
            }
            ScientificOutcomeState::ProducedWithWarning {
                values_nats,
                warnings,
            } => ScientificOutcomeSerialize::ProducedWithWarning {
                values_nats,
                warnings,
            },
            ScientificOutcomeState::Abstained { reason } => {
                ScientificOutcomeSerialize::Abstained { reason }
            }
        };
        wire.serialize(serializer)
    }
}

#[derive(Deserialize)]
#[serde(tag = "status", rename_all = "snake_case", deny_unknown_fields)]
enum ScientificOutcomeDeserialize {
    NotRequested {
        reason: ScientificReason,
    },
    Produced {
        values_nats: ScientificValueSet,
    },
    ProducedWithWarning {
        values_nats: ScientificValueSet,
        warnings: BoundedVec<ScientificWarning, MAX_EVIDENCE_ITEMS>,
    },
    Abstained {
        reason: ScientificReason,
    },
}

impl<'de> Deserialize<'de> for ScientificComputationOutcome {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        match ScientificOutcomeDeserialize::deserialize(deserializer)? {
            ScientificOutcomeDeserialize::NotRequested { reason } => {
                Ok(Self::not_requested(reason))
            }
            ScientificOutcomeDeserialize::Produced { values_nats } => {
                Ok(Self::produced(values_nats))
            }
            ScientificOutcomeDeserialize::ProducedWithWarning {
                values_nats,
                warnings,
            } => Self::produced_with_warning(values_nats, warnings.into_vec())
                .map_err(serde::de::Error::custom),
            ScientificOutcomeDeserialize::Abstained { reason } => Ok(Self::abstained(reason)),
        }
    }
}

/// Frozen scientific inputs and policies for one class of logical outcomes.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificAnalysisPlan {
    contract_revision: u32,
    plan_id: String,
    method: ScientificMethodIdentity,
    output_schema: ScientificOutputSchema,
    invariants: ScientificInvariantContract,
    variables: Vec<ScientificRequestVariable>,
    source_data: ScientificDataSet,
    estimator: ScientificEstimatorIdentity,
    estimator_contract: ScientificArtifactIdentity,
    analysis_scope: VersionedContentIdentity,
    pipeline: ScientificPipelinePlan,
    support: ScientificSupportIdentity,
    splits: Vec<ScientificSplitIdentity>,
    planned_split: ScientificSplitSelection,
    identity: VersionedContentIdentity,
}

/// Checked inputs for [`ScientificAnalysisPlan::new`].
#[derive(Debug)]
pub struct ScientificAnalysisPlanInputs {
    /// Stable identifier for this plan within its request ledger.
    pub plan_id: String,
    /// Method classification and catalog binding.
    pub method: ScientificMethodIdentity,
    /// Declared output schema.
    pub output_schema: ScientificOutputSchema,
    /// Numerical-coherence equations for the output schema.
    pub invariants: ScientificInvariantContract,
    /// Source variable roles and identifiers.
    pub variables: Vec<ScientificRequestVariable>,
    /// Declared source-data identities or an explicit absence state.
    pub source_data: ScientificDataSet,
    /// Estimator revision or an explicit unavailable state.
    pub estimator: ScientificEstimatorIdentity,
    /// Estimator settings contract or an explicit absence state.
    pub estimator_contract: ScientificArtifactIdentity,
    /// Declared application-defined analysis scope.
    pub analysis_scope: VersionedContentIdentity,
    /// Ordered preprocessing, observation-model, and resampling policy.
    pub pipeline: ScientificPipelinePlan,
    /// Population-support declaration and application envelope.
    pub support: ScientificSupportIdentity,
    /// Declared split identities used by the plan.
    pub splits: Vec<ScientificSplitIdentity>,
    /// Split that the estimator is planned to use.
    pub planned_split: ScientificSplitSelection,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificAnalysisPlanWire {
    contract_revision: u32,
    plan_id: String,
    method: ScientificMethodIdentity,
    output_schema: ScientificOutputSchema,
    invariants: ScientificInvariantContract,
    variables: BoundedVec<ScientificRequestVariable, MAX_DATA_IDENTITIES>,
    source_data: ScientificDataSet,
    estimator: ScientificEstimatorIdentity,
    estimator_contract: ScientificArtifactIdentity,
    analysis_scope: VersionedContentIdentity,
    pipeline: ScientificPipelinePlan,
    support: ScientificSupportIdentity,
    splits: BoundedVec<ScientificSplitIdentity, MAX_SPLIT_IDENTITIES>,
    planned_split: ScientificSplitSelection,
    identity: VersionedContentIdentity,
}

#[derive(Serialize)]
struct ScientificAnalysisPlanPreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    plan_id: &'a str,
    method: &'a ScientificMethodIdentity,
    output_schema: &'a ScientificOutputSchema,
    invariants: &'a ScientificInvariantContract,
    variables: &'a [ScientificRequestVariable],
    source_data: &'a ScientificDataSet,
    estimator: &'a ScientificEstimatorIdentity,
    estimator_contract: &'a ScientificArtifactIdentity,
    analysis_scope: &'a VersionedContentIdentity,
    pipeline: &'a ScientificPipelinePlan,
    support: &'a ScientificSupportIdentity,
    splits: &'a [ScientificSplitIdentity],
    planned_split: &'a ScientificSplitSelection,
}

impl ScientificAnalysisPlan {
    /// Construct a frozen analysis plan and compute its identity.
    ///
    /// # Errors
    ///
    /// Returns an error if the method, variables, output, estimator state, support, splits, or
    /// transform policy is internally inconsistent, or if identity computation exceeds its
    /// resource limit.
    pub fn new(mut inputs: ScientificAnalysisPlanInputs) -> Result<Self> {
        validate_machine_text("scientific analysis plan ID", &inputs.plan_id)?;
        inputs.invariants.validate_schema(&inputs.output_schema)?;
        canonicalize_request_variables(&mut inputs.variables)?;
        if let Some(source_data) = inputs.source_data.data() {
            if inputs.variables != data_request_variables(source_data) {
                anyhow::bail!("analysis-plan variables do not match its source data");
            }
        }
        let estimator_available = inputs.estimator.identity().is_some();
        if inputs.method.availability() == ScientificAvailability::NoImplementation
            && estimator_available
        {
            anyhow::bail!("a method with no implementation cannot select an estimator");
        }
        if estimator_available
            != (inputs.estimator_contract.status() == ScientificArtifactStatus::Available)
        {
            anyhow::bail!("analysis-plan estimator contract availability must match its estimator");
        }
        canonicalize_split_identities(&mut inputs.splits)?;
        validate_full_sample_split(inputs.source_data.data(), &inputs.splits)?;
        validate_support_coverage(&inputs.support, inputs.source_data.data())?;
        if estimator_available && inputs.planned_split.split_name().is_none() {
            anyhow::bail!("an analysis plan with an estimator needs a named estimator split");
        }
        if !estimator_available && inputs.planned_split.split_name().is_some() {
            anyhow::bail!("an analysis plan without an estimator cannot select an estimator split");
        }
        if let Some(planned_split) = inputs.planned_split.split_name() {
            if !inputs
                .splits
                .iter()
                .any(|split| split.split_name == planned_split)
            {
                anyhow::bail!("planned estimator split does not exist in the analysis plan");
            }
        }
        for step in inputs.pipeline.steps() {
            if let Some(fit_split) = step.fit().fit_split() {
                if !inputs
                    .splits
                    .iter()
                    .any(|split| split.split_name == fit_split)
                {
                    anyhow::bail!("planned transform fit split does not exist");
                }
            }
        }
        let preimage = ScientificAnalysisPlanPreimage {
            domain: "pid-rs/scientific-analysis-plan/v1",
            contract_revision: CONTRACT_REVISION,
            plan_id: &inputs.plan_id,
            method: &inputs.method,
            output_schema: &inputs.output_schema,
            invariants: &inputs.invariants,
            variables: &inputs.variables,
            source_data: &inputs.source_data,
            estimator: &inputs.estimator,
            estimator_contract: &inputs.estimator_contract,
            analysis_scope: &inputs.analysis_scope,
            pipeline: &inputs.pipeline,
            support: &inputs.support,
            splits: &inputs.splits,
            planned_split: &inputs.planned_split,
        };
        let identity = VersionedContentIdentity::new(
            format!("pid-rs/scientific-analysis-plan/{}", inputs.plan_id),
            "1",
            canonical_scientific_identity(&preimage)?,
        )?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            plan_id: inputs.plan_id,
            method: inputs.method,
            output_schema: inputs.output_schema,
            invariants: inputs.invariants,
            variables: inputs.variables,
            source_data: inputs.source_data,
            estimator: inputs.estimator,
            estimator_contract: inputs.estimator_contract,
            analysis_scope: inputs.analysis_scope,
            pipeline: inputs.pipeline,
            support: inputs.support,
            splits: inputs.splits,
            planned_split: inputs.planned_split,
            identity,
        })
    }

    pub fn plan_id(&self) -> &str {
        &self.plan_id
    }

    pub fn method(&self) -> &ScientificMethodIdentity {
        &self.method
    }

    pub fn output_schema(&self) -> &ScientificOutputSchema {
        &self.output_schema
    }

    pub fn invariants(&self) -> &ScientificInvariantContract {
        &self.invariants
    }

    pub fn variables(&self) -> &[ScientificRequestVariable] {
        &self.variables
    }

    pub fn source_data(&self) -> &ScientificDataSet {
        &self.source_data
    }

    pub fn estimator(&self) -> &ScientificEstimatorIdentity {
        &self.estimator
    }

    pub fn estimator_contract(&self) -> &ScientificArtifactIdentity {
        &self.estimator_contract
    }

    pub fn analysis_scope(&self) -> &VersionedContentIdentity {
        &self.analysis_scope
    }

    pub fn pipeline(&self) -> &ScientificPipelinePlan {
        &self.pipeline
    }

    pub fn support(&self) -> &ScientificSupportIdentity {
        &self.support
    }

    pub fn splits(&self) -> &[ScientificSplitIdentity] {
        &self.splits
    }

    pub fn planned_split(&self) -> &ScientificSplitSelection {
        &self.planned_split
    }

    pub fn identity(&self) -> &VersionedContentIdentity {
        &self.identity
    }
}

impl<'de> Deserialize<'de> for ScientificAnalysisPlan {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificAnalysisPlanWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific analysis plan revision",
            ));
        }
        let expected = wire.identity;
        let plan = Self::new(ScientificAnalysisPlanInputs {
            plan_id: wire.plan_id,
            method: wire.method,
            output_schema: wire.output_schema,
            invariants: wire.invariants,
            variables: wire.variables.into_vec(),
            source_data: wire.source_data,
            estimator: wire.estimator,
            estimator_contract: wire.estimator_contract,
            analysis_scope: wire.analysis_scope,
            pipeline: wire.pipeline,
            support: wire.support,
            splits: wire.splits.into_vec(),
            planned_split: wire.planned_split,
        })
        .map_err(serde::de::Error::custom)?;
        if plan.identity != expected {
            return Err(serde::de::Error::custom(
                "scientific analysis plan identity does not match its canonical preimage",
            ));
        }
        Ok(plan)
    }
}

/// A checked computational regime for one logical calculation.
///
/// Its identity covers every field in this record. Nested content identities remain declarations:
/// this type does not read their external bytes or recompute their digests.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificRegime {
    contract_revision: u32,
    analysis_plan: ScientificAnalysisPlan,
    method: ScientificMethodIdentity,
    estimator: ScientificEstimatorIdentity,
    output_schema: ScientificOutputSchema,
    lineage: ScientificDataLineage,
    software: VersionedContentIdentity,
    estimator_contract: ScientificArtifactIdentity,
    estimator_report: ScientificArtifactIdentity,
    analysis_scope: VersionedContentIdentity,
    preprocessing: ScientificArtifactIdentity,
    observation_model: ScientificArtifactIdentity,
    resampling: ScientificArtifactIdentity,
    support: ScientificSupportIdentity,
    splits: Vec<ScientificSplitIdentity>,
    estimator_split: ScientificSplitSelection,
    regime_identity: ScientificHashIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificRegimeWire {
    contract_revision: u32,
    analysis_plan: ScientificAnalysisPlan,
    method: ScientificMethodIdentity,
    estimator: ScientificEstimatorIdentity,
    output_schema: ScientificOutputSchema,
    lineage: ScientificDataLineage,
    software: VersionedContentIdentity,
    estimator_contract: ScientificArtifactIdentity,
    estimator_report: ScientificArtifactIdentity,
    analysis_scope: VersionedContentIdentity,
    preprocessing: ScientificArtifactIdentity,
    observation_model: ScientificArtifactIdentity,
    resampling: ScientificArtifactIdentity,
    support: ScientificSupportIdentity,
    splits: BoundedVec<ScientificSplitIdentity, MAX_SPLIT_IDENTITIES>,
    estimator_split: ScientificSplitSelection,
    regime_identity: ScientificHashIdentity,
}

#[derive(Serialize)]
struct ScientificRegimePreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    analysis_plan: &'a ScientificAnalysisPlan,
    method: &'a ScientificMethodIdentity,
    estimator: &'a ScientificEstimatorIdentity,
    output_schema: &'a ScientificOutputSchema,
    lineage: &'a ScientificDataLineage,
    software: &'a VersionedContentIdentity,
    estimator_contract: &'a ScientificArtifactIdentity,
    estimator_report: &'a ScientificArtifactIdentity,
    analysis_scope: &'a VersionedContentIdentity,
    preprocessing: &'a ScientificArtifactIdentity,
    observation_model: &'a ScientificArtifactIdentity,
    resampling: &'a ScientificArtifactIdentity,
    support: &'a ScientificSupportIdentity,
    splits: &'a [ScientificSplitIdentity],
    estimator_split: &'a ScientificSplitSelection,
}

/// Checked inputs for [`ScientificRegime::new`].
#[derive(Debug)]
pub struct ScientificRegimeInputs {
    /// The frozen analysis plan that this applied regime follows.
    pub analysis_plan: ScientificAnalysisPlan,
    /// Orthogonal method classification and method-catalog binding.
    pub method: ScientificMethodIdentity,
    /// The estimator identity or an explicit unavailable state.
    pub estimator: ScientificEstimatorIdentity,
    /// The declared definitions and keys for the named output set.
    pub output_schema: ScientificOutputSchema,
    /// The checked transform path from source data to estimator data.
    pub lineage: ScientificDataLineage,
    /// The software identity for the code that ran the calculation.
    pub software: VersionedContentIdentity,
    /// The requested estimator settings and numerical contract.
    pub estimator_contract: ScientificArtifactIdentity,
    /// The estimator report identity, including its settings and diagnostics.
    pub estimator_report: ScientificArtifactIdentity,
    /// The declared analysis scope, such as full, training, control, or uncertainty.
    pub analysis_scope: VersionedContentIdentity,
    /// The preprocessing identity or explicit absence state.
    pub preprocessing: ScientificArtifactIdentity,
    /// The observation-model identity or explicit absence state.
    pub observation_model: ScientificArtifactIdentity,
    /// The resampling identity or explicit absence state.
    pub resampling: ScientificArtifactIdentity,
    /// The population-support declaration and optional application envelope.
    pub support: ScientificSupportIdentity,
    /// The split and resample identities relevant to this calculation.
    pub splits: Vec<ScientificSplitIdentity>,
    /// The selected estimator split or an explicit absence state.
    pub estimator_split: ScientificSplitSelection,
}

impl ScientificRegime {
    /// Construct a regime and compute its canonical identity.
    ///
    /// The data must have contiguous source indexes, one target, equal row counts, and supported
    /// matrix hash revisions. The active split must exist and have the same number of rows.
    ///
    /// # Errors
    ///
    /// Returns an error if the applied regime contradicts its analysis plan, data lineage,
    /// estimator state, support declaration, split declarations, or transform artifacts.
    pub fn new(mut inputs: ScientificRegimeInputs) -> Result<Self> {
        let estimator_available = inputs.estimator.identity().is_some();
        if inputs.method.availability() == ScientificAvailability::NoImplementation
            && estimator_available
        {
            anyhow::bail!("a method with no implementation cannot select an estimator");
        }
        if inputs.method.availability() == ScientificAvailability::NoImplementation
            && (inputs.estimator_contract.status() == ScientificArtifactStatus::Available
                || inputs.estimator_report.status() == ScientificArtifactStatus::Available
                || inputs.lineage.estimator_data().status() == ScientificArtifactStatus::Available
                || inputs.estimator_split.status() == ScientificArtifactStatus::Available)
        {
            anyhow::bail!(
                "a method with no implementation cannot have estimator output artifacts or a selected split"
            );
        }
        if estimator_available
            != (inputs.estimator_contract.status() == ScientificArtifactStatus::Available)
        {
            anyhow::bail!("estimator-contract availability must match estimator selection");
        }
        if !estimator_available
            && (inputs.estimator_report.status() == ScientificArtifactStatus::Available
                || inputs.lineage.estimator_data().status() == ScientificArtifactStatus::Available
                || inputs.estimator_split.status() == ScientificArtifactStatus::Available)
        {
            anyhow::bail!(
                "a regime without a selected estimator cannot have estimator output artifacts or a selected split"
            );
        }
        canonicalize_split_identities(&mut inputs.splits)?;
        validate_full_sample_split(inputs.lineage.source_data().data(), &inputs.splits)?;
        validate_transform_fit_scopes(inputs.lineage.transforms(), &inputs.splits)?;
        validate_resampling_outputs(inputs.lineage.transforms(), &inputs.splits)?;
        validate_split_selection(
            &inputs.splits,
            &inputs.estimator_split,
            inputs.lineage.estimator_data().data(),
        )?;
        validate_support_coverage(&inputs.support, inputs.lineage.latest_available_data())?;
        validate_transform_artifact(
            ScientificTransformKind::Preprocessing,
            &inputs.preprocessing,
            inputs.lineage.transforms(),
        )?;
        validate_transform_artifact(
            ScientificTransformKind::ObservationModel,
            &inputs.observation_model,
            inputs.lineage.transforms(),
        )?;
        validate_transform_artifact(
            ScientificTransformKind::Resampling,
            &inputs.resampling,
            inputs.lineage.transforms(),
        )?;
        validate_regime_against_plan(&inputs)?;
        let preimage = ScientificRegimePreimage {
            domain: "pid-rs/scientific-regime/v1",
            contract_revision: CONTRACT_REVISION,
            analysis_plan: &inputs.analysis_plan,
            method: &inputs.method,
            estimator: &inputs.estimator,
            output_schema: &inputs.output_schema,
            lineage: &inputs.lineage,
            software: &inputs.software,
            estimator_contract: &inputs.estimator_contract,
            estimator_report: &inputs.estimator_report,
            analysis_scope: &inputs.analysis_scope,
            preprocessing: &inputs.preprocessing,
            observation_model: &inputs.observation_model,
            resampling: &inputs.resampling,
            support: &inputs.support,
            splits: &inputs.splits,
            estimator_split: &inputs.estimator_split,
        };
        let regime_identity = canonical_scientific_identity(&preimage)?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            analysis_plan: inputs.analysis_plan,
            method: inputs.method,
            estimator: inputs.estimator,
            output_schema: inputs.output_schema,
            lineage: inputs.lineage,
            software: inputs.software,
            estimator_contract: inputs.estimator_contract,
            estimator_report: inputs.estimator_report,
            analysis_scope: inputs.analysis_scope,
            preprocessing: inputs.preprocessing,
            observation_model: inputs.observation_model,
            resampling: inputs.resampling,
            support: inputs.support,
            splits: inputs.splits,
            estimator_split: inputs.estimator_split,
            regime_identity,
        })
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn analysis_plan(&self) -> &ScientificAnalysisPlan {
        &self.analysis_plan
    }

    pub fn method(&self) -> &ScientificMethodIdentity {
        &self.method
    }

    pub fn estimator(&self) -> &ScientificEstimatorIdentity {
        &self.estimator
    }

    pub fn output_schema(&self) -> &ScientificOutputSchema {
        &self.output_schema
    }

    pub fn lineage(&self) -> &ScientificDataLineage {
        &self.lineage
    }

    pub fn software(&self) -> &VersionedContentIdentity {
        &self.software
    }

    pub fn estimator_contract(&self) -> &ScientificArtifactIdentity {
        &self.estimator_contract
    }

    pub fn estimator_report(&self) -> &ScientificArtifactIdentity {
        &self.estimator_report
    }

    pub fn analysis_scope(&self) -> &VersionedContentIdentity {
        &self.analysis_scope
    }

    pub fn preprocessing(&self) -> &ScientificArtifactIdentity {
        &self.preprocessing
    }

    pub fn observation_model(&self) -> &ScientificArtifactIdentity {
        &self.observation_model
    }

    pub fn resampling(&self) -> &ScientificArtifactIdentity {
        &self.resampling
    }

    pub fn support(&self) -> &ScientificSupportIdentity {
        &self.support
    }

    pub fn splits(&self) -> &[ScientificSplitIdentity] {
        &self.splits
    }

    pub fn estimator_split(&self) -> &ScientificSplitSelection {
        &self.estimator_split
    }

    pub fn regime_identity(&self) -> &ScientificHashIdentity {
        &self.regime_identity
    }
}

impl<'de> Deserialize<'de> for ScientificRegime {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificRegimeWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific regime contract revision",
            ));
        }
        wire.regime_identity
            .validate()
            .map_err(serde::de::Error::custom)?;
        let expected = wire.regime_identity;
        let regime = Self::new(ScientificRegimeInputs {
            analysis_plan: wire.analysis_plan,
            method: wire.method,
            estimator: wire.estimator,
            output_schema: wire.output_schema,
            lineage: wire.lineage,
            software: wire.software,
            estimator_contract: wire.estimator_contract,
            estimator_report: wire.estimator_report,
            analysis_scope: wire.analysis_scope,
            preprocessing: wire.preprocessing,
            observation_model: wire.observation_model,
            resampling: wire.resampling,
            support: wire.support,
            splits: wire.splits.into_vec(),
            estimator_split: wire.estimator_split,
        })
        .map_err(serde::de::Error::custom)?;
        if regime.regime_identity != expected {
            return Err(serde::de::Error::custom(
                "scientific regime identity does not match its canonical preimage",
            ));
        }
        Ok(regime)
    }
}

fn validate_regime_against_plan(inputs: &ScientificRegimeInputs) -> Result<()> {
    let plan = &inputs.analysis_plan;
    if plan.method != inputs.method {
        anyhow::bail!("applied regime method does not match its analysis plan");
    }
    if plan.output_schema != inputs.output_schema {
        anyhow::bail!("applied output schema does not match its analysis plan");
    }
    if plan.source_data != *inputs.lineage.source_data() {
        anyhow::bail!("applied source data does not match its analysis plan");
    }
    if plan.estimator != inputs.estimator {
        anyhow::bail!("applied estimator does not match its analysis plan");
    }
    if plan.estimator_contract != inputs.estimator_contract {
        anyhow::bail!("applied estimator contract does not match its analysis plan");
    }
    if plan.analysis_scope != inputs.analysis_scope {
        anyhow::bail!("applied analysis scope does not match its analysis plan");
    }
    if plan.support != inputs.support {
        anyhow::bail!("applied support declaration does not match its analysis plan");
    }
    if plan.splits != inputs.splits {
        anyhow::bail!("applied split declarations do not match the analysis plan");
    }
    if !plan.pipeline.matches_prefix(inputs.lineage.transforms()) {
        anyhow::bail!("applied transform lineage is not a prefix of the analysis plan");
    }
    if let Some(applied_split) = inputs.estimator_split.split_name() {
        if plan.planned_split.split_name() != Some(applied_split) {
            anyhow::bail!("applied estimator split does not match the analysis plan");
        }
    }
    Ok(())
}

fn canonicalize_data_identities(data: &mut Vec<ScientificDataIdentity>) -> Result<()> {
    if data.is_empty() || data.len() > MAX_DATA_IDENTITIES {
        anyhow::bail!("scientific regime needs 1..={MAX_DATA_IDENTITIES} data identities");
    }
    data.sort_by_key(|identity| identity.role);
    let expected_rows = data[0].rows();
    let expected_membership = data[0].row_membership_identity();
    if data.iter().any(|identity| identity.rows() != expected_rows) {
        anyhow::bail!("all scientific data identities must have the same row count");
    }
    if data
        .iter()
        .any(|identity| identity.row_membership_identity() != expected_membership)
    {
        anyhow::bail!("all scientific data identities must have the same ordered row membership");
    }
    let mut variable_ids = BTreeSet::new();
    let mut source_indices = BTreeSet::new();
    let mut targets = 0usize;
    for identity in data {
        if !variable_ids.insert(identity.variable_id.as_str()) {
            anyhow::bail!("scientific variable IDs must be unique");
        }
        match identity.role {
            InformationVariableRole::Source { index } => {
                if !source_indices.insert(index) {
                    anyhow::bail!("scientific source indices must be unique");
                }
            }
            InformationVariableRole::Target => targets += 1,
        }
    }
    if targets != 1 || source_indices.is_empty() {
        anyhow::bail!("scientific data must contain at least one source and exactly one target");
    }
    let source_count = u32::try_from(source_indices.len())
        .map_err(|_| anyhow::anyhow!("scientific source count exceeds u32"))?;
    if source_indices.iter().copied().ne(0..source_count) {
        anyhow::bail!("scientific source indices must be contiguous and start at zero");
    }
    Ok(())
}

fn canonicalize_fit_data(
    data: &mut Vec<ScientificDataIdentity>,
    access: ScientificFitAccess,
) -> Result<()> {
    if access == ScientificFitAccess::SupervisedSourcesAndTarget {
        return canonicalize_data_identities(data);
    }
    if data.is_empty() || data.len() > MAX_DATA_IDENTITIES {
        anyhow::bail!("scientific fit needs 1..={MAX_DATA_IDENTITIES} data identities");
    }
    data.sort_by_key(|identity| identity.role);
    let expected_rows = data[0].rows();
    let expected_membership = data[0].row_membership_identity();
    let mut variable_ids = BTreeSet::new();
    let mut source_indices = BTreeSet::new();
    for identity in data.iter() {
        if identity.rows() != expected_rows
            || identity.row_membership_identity() != expected_membership
        {
            anyhow::bail!("all scientific fit data must use the same ordered rows");
        }
        if !variable_ids.insert(identity.variable_id.as_str()) {
            anyhow::bail!("scientific fit variable IDs must be unique");
        }
        let InformationVariableRole::Source { index } = identity.role else {
            anyhow::bail!("an unsupervised transform fit must not access the target");
        };
        if !source_indices.insert(index) {
            anyhow::bail!("scientific fit source indices must be unique");
        }
    }
    let source_count = u32::try_from(source_indices.len())
        .map_err(|_| anyhow::anyhow!("scientific fit source count exceeds u32"))?;
    if source_indices.iter().copied().ne(0..source_count) {
        anyhow::bail!("scientific fit source indices must be contiguous and start at zero");
    }
    Ok(())
}

fn canonicalize_request_variables(variables: &mut Vec<ScientificRequestVariable>) -> Result<()> {
    if variables.is_empty() || variables.len() > MAX_DATA_IDENTITIES {
        anyhow::bail!("scientific request needs 1..={MAX_DATA_IDENTITIES} variables");
    }
    variables.sort_by_key(|variable| variable.role);
    let mut variable_ids = BTreeSet::new();
    let mut source_indices = BTreeSet::new();
    let mut targets = 0usize;
    for variable in variables {
        if !variable_ids.insert(variable.variable_id.as_str()) {
            anyhow::bail!("scientific request variable IDs must be unique");
        }
        match variable.role {
            InformationVariableRole::Source { index } => {
                if !source_indices.insert(index) {
                    anyhow::bail!("scientific request source indices must be unique");
                }
            }
            InformationVariableRole::Target => targets += 1,
        }
    }
    if targets != 1 || source_indices.is_empty() {
        anyhow::bail!("scientific request needs at least one source and exactly one target");
    }
    let source_count = u32::try_from(source_indices.len())
        .map_err(|_| anyhow::anyhow!("scientific request source count exceeds u32"))?;
    if source_indices.iter().copied().ne(0..source_count) {
        anyhow::bail!("scientific request source indices must be contiguous and start at zero");
    }
    Ok(())
}

fn data_request_variables(data: &[ScientificDataIdentity]) -> Vec<ScientificRequestVariable> {
    data.iter()
        .map(|identity| ScientificRequestVariable {
            role: identity.role,
            variable_id: identity.variable_id.clone(),
        })
        .collect()
}

fn canonicalize_split_identities(splits: &mut [ScientificSplitIdentity]) -> Result<()> {
    if splits.len() > MAX_SPLIT_IDENTITIES {
        anyhow::bail!("scientific regime exceeds {MAX_SPLIT_IDENTITIES} split identities");
    }
    splits.sort_by(|left, right| left.split_name.cmp(&right.split_name));
    if splits
        .windows(2)
        .any(|pair| pair[0].split_name == pair[1].split_name)
    {
        anyhow::bail!("scientific split names must be unique");
    }
    if let Some(first) = splits.first() {
        if splits
            .iter()
            .any(|split| split.parent_row_ledger != first.parent_row_ledger)
        {
            anyhow::bail!("all scientific splits must use the same parent row ledger");
        }
    }
    let manifests = splits
        .iter()
        .filter(|split| split.role != ScientificSplitRole::FullSample)
        .filter_map(|split| split.partition_manifest.identity())
        .collect::<BTreeSet<_>>();
    if manifests.len() > 1 {
        anyhow::bail!("all non-full splits must use the same partition manifest");
    }
    Ok(())
}

fn validate_full_sample_split(
    source_data: Option<&[ScientificDataIdentity]>,
    splits: &[ScientificSplitIdentity],
) -> Result<()> {
    let full_splits = splits
        .iter()
        .filter(|split| split.role == ScientificSplitRole::FullSample)
        .collect::<Vec<_>>();
    match source_data {
        Some(data) => {
            if full_splits.len() != 1 {
                anyhow::bail!("available source data needs exactly one full-sample split");
            }
            let full = full_splits[0];
            if full.membership_identity() != data[0].row_membership_identity() {
                anyhow::bail!("full-sample membership must match the source data");
            }
            if splits.iter().any(|split| {
                split.role != ScientificSplitRole::Resample
                    && split.member_count() > full.member_count()
            }) {
                anyhow::bail!("a non-resample split cannot exceed the full-sample size");
            }
        }
        None if !full_splits.is_empty() => {
            anyhow::bail!("a full-sample split needs available source data");
        }
        None => {}
    }
    Ok(())
}

fn validate_transform_fit_scopes(
    transforms: &[ScientificTransformEdge],
    splits: &[ScientificSplitIdentity],
) -> Result<()> {
    for transform in transforms {
        let Some(fit_data) = transform.fit.fit_data() else {
            continue;
        };
        let fit_split_name = transform
            .fit
            .fit_split()
            .ok_or_else(|| anyhow::anyhow!("fitted transform has no fit split"))?;
        let split = splits
            .binary_search_by(|split| split.split_name.as_str().cmp(fit_split_name))
            .ok()
            .map(|index| &splits[index])
            .ok_or_else(|| anyhow::anyhow!("scientific transform fit split does not exist"))?;
        if split.member_count() != fit_data[0].rows()
            || split.membership_identity() != fit_data[0].row_membership_identity()
        {
            anyhow::bail!("scientific transform fit data does not match its fit split");
        }
        let expected_variables = match transform.fit.access() {
            Some(ScientificFitAccess::UnsupervisedSources) => transform
                .inputs
                .iter()
                .filter(|identity| matches!(identity.role, InformationVariableRole::Source { .. }))
                .map(|identity| (identity.role, identity.variable_id.as_str()))
                .collect::<Vec<_>>(),
            Some(ScientificFitAccess::SupervisedSourcesAndTarget) => transform
                .inputs
                .iter()
                .map(|identity| (identity.role, identity.variable_id.as_str()))
                .collect::<Vec<_>>(),
            None => unreachable!("fit data exists only for a fitted transform"),
        };
        let actual_variables = fit_data
            .iter()
            .map(|identity| (identity.role, identity.variable_id.as_str()))
            .collect::<Vec<_>>();
        if actual_variables != expected_variables {
            anyhow::bail!("scientific transform fit variables do not match its application input");
        }
    }
    Ok(())
}

fn validate_resampling_outputs(
    transforms: &[ScientificTransformEdge],
    splits: &[ScientificSplitIdentity],
) -> Result<()> {
    for transform in transforms
        .iter()
        .filter(|transform| transform.kind == ScientificTransformKind::Resampling)
    {
        let output_membership = transform.outputs[0].row_membership_identity();
        if !splits
            .iter()
            .any(|split| split.membership_identity() == output_membership)
        {
            anyhow::bail!("a resampling transform output must match a declared split or resample");
        }
    }
    Ok(())
}

fn validate_split_selection(
    splits: &[ScientificSplitIdentity],
    selection: &ScientificSplitSelection,
    estimator_data: Option<&[ScientificDataIdentity]>,
) -> Result<()> {
    let Some(split_name) = selection.split_name() else {
        return Ok(());
    };
    let data = estimator_data
        .ok_or_else(|| anyhow::anyhow!("a selected estimator split needs estimator data"))?;
    let active = splits
        .binary_search_by(|split| split.split_name.as_str().cmp(split_name))
        .ok()
        .map(|index| &splits[index])
        .ok_or_else(|| anyhow::anyhow!("scientific estimator split does not exist"))?;
    if active.member_count() != data[0].rows() {
        anyhow::bail!("scientific estimator split size must match the estimator data rows");
    }
    if active.membership_identity() != data[0].row_membership_identity() {
        anyhow::bail!("scientific estimator split membership must match the estimator data");
    }
    Ok(())
}

fn validate_support_coverage(
    support: &ScientificSupportIdentity,
    estimator_data: Option<&[ScientificDataIdentity]>,
) -> Result<()> {
    match (support.status(), estimator_data) {
        (ScientificSupportStatus::Declared, Some(data)) => {
            let mut variables = data
                .iter()
                .map(|identity| identity.variable_id.clone())
                .collect::<Vec<_>>();
            variables.sort();
            if !support.covers_all_nonempty_subsets(&variables) {
                anyhow::bail!("declared support must cover every nonempty marginal and joint set");
            }
        }
        (ScientificSupportStatus::Declared, None) => {
            anyhow::bail!("declared support needs available estimator data")
        }
        (ScientificSupportStatus::Unspecified | ScientificSupportStatus::Unsupported, _) => {}
    }
    Ok(())
}

fn validate_transform_artifact(
    kind: ScientificTransformKind,
    artifact: &ScientificArtifactIdentity,
    transforms: &[ScientificTransformEdge],
) -> Result<()> {
    let expected = transform_group_identity(kind, transforms)?;
    match (artifact.identity(), expected.as_ref()) {
        (Some(identity), Some(expected)) if identity == expected => Ok(()),
        (Some(_), Some(_)) => {
            anyhow::bail!("available transform artifact does not match its lineage group")
        }
        (Some(_), None) => {
            anyhow::bail!("an available transform artifact needs at least one lineage edge")
        }
        (None, None) => Ok(()),
        (None, Some(_)) => anyhow::bail!("a lineage transform group needs an available artifact"),
    }
}

/// One logical information outcome, its declared regime, its gates, and its typed payload.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
#[non_exhaustive]
pub struct ScientificOutcomeReport {
    contract_revision: u32,
    outcome_id: String,
    request_ledger: ScientificRequestLedger,
    regime: ScientificRegime,
    gates: ScientificGateSet,
    stages: ScientificStageSet,
    outcome: ScientificComputationOutcome,
    outcome_identity: ScientificHashIdentity,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ScientificOutcomeReportWire {
    contract_revision: u32,
    outcome_id: String,
    request_ledger: ScientificRequestLedger,
    regime: ScientificRegime,
    gates: ScientificGateSet,
    stages: ScientificStageSet,
    outcome: ScientificComputationOutcome,
    outcome_identity: ScientificHashIdentity,
}

#[derive(Serialize)]
struct ScientificOutcomePreimage<'a> {
    domain: &'static str,
    contract_revision: u32,
    outcome_id: &'a str,
    request_ledger: &'a ScientificRequestLedger,
    regime: &'a ScientificRegime,
    gates: &'a ScientificGateSet,
    stages: &'a ScientificStageSet,
    outcome: &'a ScientificComputationOutcome,
}

impl ScientificOutcomeReport {
    /// Construct a report and compute its canonical outcome identity.
    ///
    /// A not-requested outcome requires four gates and all stage facts to be not applicable. A
    /// warned or abstained outcome cannot permit interpretation. An abstention reason must match a
    /// gate that is conditional, not evaluated, or blocked.
    ///
    /// # Errors
    ///
    /// Returns an error if the request, plan, values, invariants, stages, gates, evidence, or
    /// computation state contradict one another.
    pub fn new(
        outcome_id: impl Into<String>,
        request_ledger: ScientificRequestLedger,
        regime: ScientificRegime,
        gates: ScientificGateSet,
        stages: ScientificStageSet,
        outcome: ScientificComputationOutcome,
    ) -> Result<Self> {
        let outcome_id = outcome_id.into();
        validate_machine_text("scientific outcome ID", &outcome_id)?;
        let request = request_ledger.entry(&outcome_id).ok_or_else(|| {
            anyhow::anyhow!("scientific outcome ID is absent from its request ledger")
        })?;
        if request.analysis_plan != *regime.analysis_plan.identity() {
            anyhow::bail!("scientific request and applied analysis-plan identities do not match");
        }
        if regime
            .splits
            .iter()
            .any(|split| split.parent_row_ledger != request_ledger.sampling_frame)
        {
            anyhow::bail!("scientific request sampling frame does not match the split row ledger");
        }

        if let Some(values) = outcome.values_nats() {
            if !regime.output_schema.matches_values(values) {
                anyhow::bail!("scientific outcome values do not match the output schema");
            }
            regime.analysis_plan.invariants.validate_values(values)?;
        }
        if regime.estimator.identity().is_none() && outcome.values_nats().is_some() {
            anyhow::bail!("a regime without a selected estimator cannot carry numeric values");
        }
        if stages.declared_support_compatible()
            && regime.support.status() != ScientificSupportStatus::Declared
        {
            anyhow::bail!("support-compatible stage fact needs declared support");
        }
        if gates.population.verdict() == ScientificGateVerdict::Passed
            && !stages.declared_support_compatible()
        {
            anyhow::bail!("a passed population gate needs a support-compatible stage fact");
        }
        match outcome.status() {
            ScientificOutcomeStatus::NotRequested => {
                if request.requested {
                    anyhow::bail!("a requested ledger entry cannot have a not-requested outcome");
                }
                if !gates.all_not_applicable()
                    || !stages.is_not_requested()
                    || gates.interpretation.allowed
                {
                    anyhow::bail!(
                        "not-requested outcomes need not-applicable gates and stages and denied interpretation"
                    );
                }
                if regime.estimator_report.status() == ScientificArtifactStatus::Available
                    || regime.lineage.estimator_data().status()
                        == ScientificArtifactStatus::Available
                    || regime.estimator_split.status() == ScientificArtifactStatus::Available
                {
                    anyhow::bail!(
                        "a not-requested outcome cannot have estimator output artifacts or a selected split"
                    );
                }
            }
            ScientificOutcomeStatus::Produced => {
                if !request.requested {
                    anyhow::bail!("an inactive ledger entry cannot have a produced outcome");
                }
                validate_produced_stage_and_artifacts(&regime, &stages)?;
            }
            ScientificOutcomeStatus::ProducedWithWarning => {
                if !request.requested {
                    anyhow::bail!("an inactive ledger entry cannot have a warned outcome");
                }
                validate_produced_stage_and_artifacts(&regime, &stages)?;
                if gates.interpretation.allowed {
                    anyhow::bail!("produced-with-warning outcomes cannot allow interpretation");
                }
            }
            ScientificOutcomeStatus::Abstained => {
                if !request.requested {
                    anyhow::bail!("an inactive ledger entry cannot have an abstained outcome");
                }
                if !stages.was_requested() || stages.estimated() {
                    anyhow::bail!("abstained outcome has inconsistent application stage facts");
                }
                if gates.interpretation.allowed {
                    anyhow::bail!("abstained outcomes cannot allow interpretation");
                }
                let Some(reason) = outcome.reason() else {
                    anyhow::bail!("abstained outcome must retain its reason");
                };
                if !gates.has_nonpassing_reason(reason.code()) {
                    anyhow::bail!(
                        "abstention reason must match a conditional, unevaluated, or blocked gate"
                    );
                }
            }
        }
        validate_gate_evidence(&regime, &gates, &request_ledger)?;

        let preimage = ScientificOutcomePreimage {
            domain: "pid-rs/scientific-outcome/v1",
            contract_revision: CONTRACT_REVISION,
            outcome_id: &outcome_id,
            request_ledger: &request_ledger,
            regime: &regime,
            gates: &gates,
            stages: &stages,
            outcome: &outcome,
        };
        let outcome_identity = canonical_scientific_identity(&preimage)?;
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            outcome_id,
            request_ledger,
            regime,
            gates,
            stages,
            outcome,
            outcome_identity,
        })
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn outcome_id(&self) -> &str {
        &self.outcome_id
    }

    pub fn request_ledger(&self) -> &ScientificRequestLedger {
        &self.request_ledger
    }

    pub fn regime(&self) -> &ScientificRegime {
        &self.regime
    }

    pub fn gates(&self) -> &ScientificGateSet {
        &self.gates
    }

    pub fn stages(&self) -> &ScientificStageSet {
        &self.stages
    }

    pub fn outcome(&self) -> &ScientificComputationOutcome {
        &self.outcome
    }

    pub fn outcome_identity(&self) -> &ScientificHashIdentity {
        &self.outcome_identity
    }
}

impl<'de> Deserialize<'de> for ScientificOutcomeReport {
    fn deserialize<D>(deserializer: D) -> std::result::Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = ScientificOutcomeReportWire::deserialize(deserializer)?;
        if wire.contract_revision != CONTRACT_REVISION {
            return Err(serde::de::Error::custom(
                "unsupported scientific outcome contract revision",
            ));
        }
        wire.outcome_identity
            .validate()
            .map_err(serde::de::Error::custom)?;
        let expected = wire.outcome_identity;
        let report = Self::new(
            wire.outcome_id,
            wire.request_ledger,
            wire.regime,
            wire.gates,
            wire.stages,
            wire.outcome,
        )
        .map_err(serde::de::Error::custom)?;
        if report.outcome_identity != expected {
            return Err(serde::de::Error::custom(
                "scientific outcome identity does not match its canonical preimage",
            ));
        }
        Ok(report)
    }
}

fn validate_produced_stage_and_artifacts(
    regime: &ScientificRegime,
    stages: &ScientificStageSet,
) -> Result<()> {
    if !stages.was_requested() || !stages.preflight_passed() || !stages.estimated() {
        anyhow::bail!("produced outcome has inconsistent application stage facts");
    }
    if regime.lineage.estimator_data().status() != ScientificArtifactStatus::Available {
        anyhow::bail!("produced outcome needs available estimator data");
    }
    if regime.estimator_report.status() != ScientificArtifactStatus::Available {
        anyhow::bail!("produced outcome needs an available estimator report");
    }
    if regime.estimator_split.status() != ScientificArtifactStatus::Available {
        anyhow::bail!("produced outcome needs a selected estimator split");
    }
    if regime.analysis_plan.pipeline.steps().len() != regime.lineage.transforms().len() {
        anyhow::bail!("produced outcome must complete every planned transform step");
    }
    Ok(())
}

fn validate_gate_evidence(
    regime: &ScientificRegime,
    gates: &ScientificGateSet,
    request_ledger: &ScientificRequestLedger,
) -> Result<()> {
    if gates.population.verdict == ScientificGateVerdict::Passed {
        let declaration = regime
            .support
            .declaration_identity()
            .ok_or_else(|| anyhow::anyhow!("passed population gate needs declared support"))?;
        if !gates.population.has_evidence(declaration) {
            anyhow::bail!("passed population gate must cite the regime support declaration");
        }
    }
    if gates.measure.verdict == ScientificGateVerdict::Passed
        && (!gates.measure.has_evidence(regime.output_schema.identity())
            || !gates.measure.has_evidence(regime.method.catalog_entry()))
    {
        anyhow::bail!("passed measure gate must cite the output schema and method catalog entry");
    }
    if gates.estimator.verdict == ScientificGateVerdict::Passed {
        if regime.estimator.identity().is_none() {
            anyhow::bail!("passed estimator gate needs an available estimator");
        }
        let report = regime
            .estimator_report
            .identity()
            .ok_or_else(|| anyhow::anyhow!("passed estimator gate needs an estimator report"))?;
        let estimator_contract = regime
            .estimator_contract
            .identity()
            .ok_or_else(|| anyhow::anyhow!("passed estimator gate needs an estimator contract"))?;
        if !gates.estimator.has_evidence(report)
            || !gates.estimator.has_evidence(estimator_contract)
            || !gates.estimator.has_evidence(&regime.software)
            || !gates.estimator.has_evidence(regime.lineage.identity())
        {
            anyhow::bail!(
                "passed estimator gate must cite the estimator contract, report, software, and data lineage"
            );
        }
    }
    if gates.application.verdict == ScientificGateVerdict::Passed {
        let envelope = regime
            .support
            .application_envelope()
            .ok_or_else(|| anyhow::anyhow!("passed application gate needs a support envelope"))?;
        if !gates.application.has_evidence(envelope)
            || !gates.application.has_evidence(&regime.analysis_scope)
            || !gates
                .application
                .has_evidence(&request_ledger.sampling_frame)
        {
            anyhow::bail!(
                "passed application gate must cite the support envelope, analysis scope, and sampling frame"
            );
        }
        if let Some(split_name) = regime.estimator_split.split_name() {
            let split = regime
                .splits
                .iter()
                .find(|split| split.split_name == split_name)
                .ok_or_else(|| anyhow::anyhow!("applied estimator split does not exist"))?;
            if !gates.application.has_evidence(split.identity()) {
                anyhow::bail!("passed application gate must cite the applied split declaration");
            }
        }
        if let Some(resampling) = regime.resampling.identity() {
            if !gates.application.has_evidence(resampling) {
                anyhow::bail!("passed application gate must cite the resampling contract");
            }
        }
    }
    Ok(())
}
