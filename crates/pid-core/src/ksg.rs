use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{PidError, PidResult};
#[cfg(feature = "experimental-hyperbolic")]
use crate::hyperbolic::{HyperbolicCurvature, HyperbolicMetric};
use crate::kdtree::{concat_row_into, kdtree_applicable, KdTree};
use crate::matrix::MatRef;
use crate::metric::{KernelMetric, Metric};
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
#[cfg(feature = "parallel")]
use crate::par::WORKER_STACK_BYTES;
use crate::par::{map_index_ordered, with_thread_budget};
use crate::report::{
    Assumption, AssumptionLedgerEntry, AssumptionState, EstimandIdentity, InformationUnit,
    ProvenanceHashes, ScientificStatus, WarningCode,
};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_with_capacity, CancellationProgress,
    CancellationToken, ResourceBudget, ResourceEstimate,
};
use crate::stats::{compensated_sum, digamma, digamma_int_table, ksg_local_digamma_term};
#[cfg(any(feature = "experimental-continuous", test))]
use crate::support::validate_observed_sample_conditions_with_budget;
#[cfg(feature = "experimental-hyperbolic")]
use crate::support::validate_smooth_manifold_sample_conditions_with_budget_and_cancellation;
use crate::support::{
    continuous_input_diagnostics_with_kernel_and_cancellation,
    continuous_joint_shell_diagnostics_with_kernel_and_cancellation,
    validate_observed_sample_conditions_with_budget_and_cancellation, validate_support_contract,
    BoundaryModel, ContinuousInputDiagnostics, CoordinateCardinalityDiagnostics,
    NeighborShellDiagnostics, SupportContract,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum NegativeHandling {
    /// Return the signed finite-sample estimate without a presentation transform.
    Allow,
    /// Floor the final standalone estimate at zero as an explicit presentation transform.
    ///
    /// Do not use this for MI terms that enter algebraic identities or inference procedures.
    ClampToZero,
}

#[derive(Clone, Copy)]
struct DistPair {
    joint: f64,
    dx: f64,
    dy: f64,
}

#[derive(Clone, Copy)]
struct KsgLocalDiagnostic {
    term_nats: f64,
    joint_radius: f64,
    x_count: usize,
    y_count: usize,
}

/// Neighbor-search backend selection. `Auto` engages the exact Chebyshev
/// kd-tree (see `kdtree.rs`) when it is applicable and profitable; the other
/// variants exist so tests can force each path and assert bit-identical
/// results.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(not(test), allow(dead_code))] // Brute/KdTree are test-only forcing knobs
pub(crate) enum NnBackend {
    Auto,
    Brute,
    KdTree,
}

impl NnBackend {
    #[inline]
    fn use_tree(self, metric: KernelMetric, n: usize, joint_dims: usize) -> bool {
        match self {
            NnBackend::Brute => false,
            NnBackend::KdTree => metric.is_chebyshev() && joint_dims > 0,
            NnBackend::Auto => {
                metric.is_chebyshev() && kdtree_applicable(Metric::Chebyshev, n, joint_dims)
            }
        }
    }
}

pub(crate) fn effective_thread_count(requested: usize, n_tasks: usize) -> usize {
    #[cfg(feature = "parallel")]
    let available = std::thread::available_parallelism().map_or(1, std::num::NonZero::get);
    #[cfg(not(feature = "parallel"))]
    let available = 1;
    requested.min(n_tasks).min(available).max(1)
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum KernelSupportMode {
    Stable,
    #[cfg(feature = "experimental-hyperbolic")]
    SmoothManifold,
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct KsgConfig {
    /// Number of nearest neighbors (excluding self).
    ///
    /// KSG requires `n > k >= 1`.
    pub k: usize,
    /// Distance metric. For KSG, the standard choice is Chebyshev / L∞.
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Exact floating-point strict inequality is implemented with the predecessor of the raw kNN
    /// radius. Subtracting a material epsilon would exclude legitimate distances and estimate a
    /// different, eroded-neighborhood functional, so nonzero values are rejected.
    pub tie_epsilon: f64,
    /// Handling of small negative MI estimates due to finite-sample noise. The default is
    /// [`NegativeHandling::Allow`]; clamping is an explicit presentation-only opt-in.
    pub negative_handling: NegativeHandling,
    /// Population-support assertion for this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. For ordinary
    /// Euclidean KSG, the caller must assert [`SupportContract::AssumeRegularFullDimensional`] for
    /// every marginal and joint law used by the call. This assertion is not inferred or proved
    /// from the sample. The default-off `experimental-hyperbolic` feature adds a separate smooth
    /// manifold assertion for research-only pairwise reporting.
    pub support_contract: SupportContract,
}

impl Default for KsgConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl KsgConfig {
    /// Set the nearest-neighbor count.
    pub const fn with_k(mut self, k: usize) -> Self {
        self.k = k;
        self
    }

    /// Set the distance metric.
    pub const fn with_metric(mut self, metric: Metric) -> Self {
        self.metric = metric;
        self
    }

    /// Set the reserved strict-radius compatibility value.
    ///
    /// Only exactly zero is accepted by estimator validation; this setter exists so malformed
    /// values can still be tested without relying on a semver-fragile struct literal.
    pub const fn with_tie_epsilon(mut self, tie_epsilon: f64) -> Self {
        self.tie_epsilon = tie_epsilon;
        self
    }

    /// Set the presentation policy for negative standalone estimates.
    pub const fn with_negative_handling(mut self, negative_handling: NegativeHandling) -> Self {
        self.negative_handling = negative_handling;
        self
    }

    /// Set the caller-declared population-support contract.
    pub const fn with_support_contract(mut self, support_contract: SupportContract) -> Self {
        self.support_contract = support_contract;
        self
    }

    /// Construct the ordinary Chebyshev configuration with an explicit caller assertion that all
    /// required marginal and joint laws are full-dimensional and absolutely continuous.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            support_contract: SupportContract::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

#[derive(Debug, Clone)]
struct KernelKsgConfig {
    config: KsgConfig,
    kernel_metric: KernelMetric,
    kernel_support_mode: KernelSupportMode,
}

impl KernelKsgConfig {
    fn stable(config: &KsgConfig) -> Self {
        Self {
            config: config.clone(),
            kernel_metric: config.metric.into(),
            kernel_support_mode: KernelSupportMode::Stable,
        }
    }
}

impl std::ops::Deref for KernelKsgConfig {
    type Target = KsgConfig;

    fn deref(&self) -> &Self::Target {
        &self.config
    }
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgConfig {
    /// Number of nearest neighbors (excluding self).
    pub k: usize,
    /// Lorentz-model metric and its explicit curvature.
    pub metric: HyperbolicMetric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    pub tie_epsilon: f64,
    /// Presentation handling for a negative finite-sample estimate.
    pub negative_handling: NegativeHandling,
}

#[cfg(feature = "experimental-hyperbolic")]
impl HyperbolicKsgConfig {
    /// Assert smooth densities relative to the relevant manifold volume measures and finite
    /// mutual information for every marginal and joint law required by the research estimator.
    pub const fn assume_smooth_manifold(curvature: HyperbolicCurvature) -> Self {
        Self {
            k: 3,
            metric: HyperbolicMetric::lorentz(curvature),
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
        }
    }

    /// Set the nearest-neighbor count.
    pub const fn with_k(mut self, k: usize) -> Self {
        self.k = k;
        self
    }

    /// Set the reserved strict-radius compatibility value.
    pub const fn with_tie_epsilon(mut self, tie_epsilon: f64) -> Self {
        self.tie_epsilon = tie_epsilon;
        self
    }

    /// Set the presentation policy for negative standalone estimates.
    pub const fn with_negative_handling(mut self, negative_handling: NegativeHandling) -> Self {
        self.negative_handling = negative_handling;
        self
    }

    fn kernel_config(&self) -> KernelKsgConfig {
        KernelKsgConfig {
            config: KsgConfig {
                k: self.k,
                metric: Metric::Chebyshev,
                tie_epsilon: self.tie_epsilon,
                negative_handling: self.negative_handling,
                support_contract: SupportContract::Unspecified,
            },
            kernel_metric: self.metric.kernel(),
            kernel_support_mode: KernelSupportMode::SmoothManifold,
        }
    }
}

/// Owned, structurally checked caller-declared provenance attached to a [`KsgMiReport`].
///
/// Provenance describes operations and assumptions that cannot be reconstructed from the numeric
/// sample. Both required descriptions must contain at least one non-whitespace character. An
/// embedding-training description is optional for ordinary Chebyshev KSG, but is required by
/// `hyperbolic_ksg_mi_report` for the experimental Lorentz-hyperbolic path.
#[derive(Debug, PartialEq, Eq, Serialize)]
pub struct KsgProvenance {
    preprocessing_description: String,
    observation_model_description: String,
    embedding_training_provenance: Option<String>,
    sampling_model_description: Option<String>,
    training_split_id: Option<String>,
    evaluation_split_id: Option<String>,
}

impl KsgProvenance {
    /// Construct owned caller-declared provenance, checking only that required text is nonempty.
    pub fn new(
        preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
        embedding_training_provenance: Option<&str>,
    ) -> PidResult<Self> {
        let preprocessing_description = preprocessing_description.as_ref();
        if preprocessing_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "preprocessing_description must be nonempty",
            });
        }
        let observation_model_description = observation_model_description.as_ref();
        if observation_model_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "observation_model_description must be nonempty",
            });
        }
        for value in [preprocessing_description, observation_model_description] {
            validate_optional_provenance_text(
                "KsgProvenance::new",
                "provenance field is too long",
                Some(value),
            )?;
        }
        if embedding_training_provenance.is_some_and(|description| description.trim().is_empty()) {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "embedding_training_provenance must be nonempty when provided",
            });
        }
        validate_optional_provenance_text(
            "KsgProvenance::new",
            "embedding_training_provenance is too long",
            embedding_training_provenance,
        )?;
        let preprocessing_description =
            try_provenance_string("KsgProvenance::new", preprocessing_description)?;
        let observation_model_description =
            try_provenance_string("KsgProvenance::new", observation_model_description)?;
        let embedding_training_provenance = embedding_training_provenance
            .map(|value| try_provenance_string("KsgProvenance::new", value))
            .transpose()?;
        Ok(Self {
            preprocessing_description,
            observation_model_description,
            embedding_training_provenance,
            sampling_model_description: None,
            training_split_id: None,
            evaluation_split_id: None,
        })
    }

    /// Attach the declared sampling/dependence model and train/evaluation split identities.
    pub fn with_sampling_model_and_splits(
        mut self,
        sampling_model_description: impl AsRef<str>,
        training_split_id: Option<&str>,
        evaluation_split_id: Option<&str>,
    ) -> PidResult<Self> {
        let sampling_model_description = sampling_model_description.as_ref();
        if sampling_model_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::with_sampling_model_and_splits",
                message: "sampling_model_description must be nonempty",
            });
        }
        for value in [
            Some(sampling_model_description),
            training_split_id,
            evaluation_split_id,
        ] {
            validate_optional_provenance_text(
                "KsgProvenance::with_sampling_model_and_splits",
                "provenance field is too long",
                value,
            )?;
        }
        self.sampling_model_description = Some(try_provenance_string(
            "KsgProvenance::with_sampling_model_and_splits",
            sampling_model_description,
        )?);
        self.training_split_id = training_split_id
            .map(|value| {
                try_provenance_string("KsgProvenance::with_sampling_model_and_splits", value)
            })
            .transpose()?;
        self.evaluation_split_id = evaluation_split_id
            .map(|value| {
                try_provenance_string("KsgProvenance::with_sampling_model_and_splits", value)
            })
            .transpose()?;
        Ok(self)
    }

    pub fn preprocessing_description(&self) -> &str {
        &self.preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }

    pub fn embedding_training_provenance(&self) -> Option<&str> {
        self.embedding_training_provenance.as_deref()
    }

    pub fn sampling_model_description(&self) -> Option<&str> {
        self.sampling_model_description.as_deref()
    }

    pub fn training_split_id(&self) -> Option<&str> {
        self.training_split_id.as_deref()
    }

    pub fn evaluation_split_id(&self) -> Option<&str> {
        self.evaluation_split_id.as_deref()
    }

    fn heap_bytes(&self) -> PidResult<u128> {
        [
            Some(self.preprocessing_description.as_str()),
            Some(self.observation_model_description.as_str()),
            self.embedding_training_provenance.as_deref(),
            self.sampling_model_description.as_deref(),
            self.training_split_id.as_deref(),
            self.evaluation_split_id.as_deref(),
        ]
        .into_iter()
        .flatten()
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "KsgProvenance",
                })
        })
    }

    /// Fallibly copy all owned provenance text under an aggregate resource budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        budget.check(
            "KsgProvenance report copy",
            ResourceEstimate {
                estimated_bytes: self.heap_bytes()?,
                pairwise_distances: 0,
                operations_hint: 6,
            },
        )?;
        Ok(Self {
            preprocessing_description: try_provenance_string(
                "KsgProvenance report copy",
                &self.preprocessing_description,
            )?,
            observation_model_description: try_provenance_string(
                "KsgProvenance report copy",
                &self.observation_model_description,
            )?,
            embedding_training_provenance: self
                .embedding_training_provenance
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            sampling_model_description: self
                .sampling_model_description
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            training_split_id: self
                .training_split_id
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
            evaluation_split_id: self
                .evaluation_split_id
                .as_deref()
                .map(|value| try_provenance_string("KsgProvenance report copy", value))
                .transpose()?,
        })
    }
}

fn validate_optional_provenance_text(
    context: &'static str,
    message: &'static str,
    value: Option<&str>,
) -> PidResult<()> {
    const MAX_PROVENANCE_BYTES: usize = 16 * 1024;
    if value.is_some_and(|value| value.len() > MAX_PROVENANCE_BYTES) {
        return Err(PidError::InvalidConfig { context, message });
    }
    Ok(())
}

fn try_provenance_string(context: &'static str, value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation: context,
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Scientific maturity of the estimator represented by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgMethodStatus {
    /// Ordinary Chebyshev KSG under the explicitly declared, restricted support contract.
    RestrictedDomain,
    /// A research path without the same estimator-level validation claim.
    Experimental,
}

/// Geometry model recorded by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgGeometryModel {
    /// Ambient-coordinate product neighborhoods using the Chebyshev (L-infinity) metric.
    AmbientChebyshev,
}

/// A deterministic, machine-readable warning attached to a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgReportWarning {
    /// Sample diagnostics are one-way checks, not proofs of population support.
    SampleDiagnosticsCannotProveSupport,
    /// At least one independently selected marginal k-th-neighbor shell is degenerate or
    /// ambiguous, even though the joint shells used by the returned estimate passed validation.
    MarginalNeighborShellPathology,
}

impl KsgReportWarning {
    /// Stable explanatory text for this warning.
    pub const fn message(self) -> &'static str {
        match self {
            Self::SampleDiagnosticsCannotProveSupport => {
                "sample diagnostics can identify observations incompatible with ideal estimator conditions, but cannot determine the cause or prove population continuity, a common reference measure, or finite mutual information"
            }
            Self::MarginalNeighborShellPathology => {
                "an independently selected marginal k-th-neighbor shell has zero radius or an ambiguous positive boundary"
            }
        }
    }
}

/// Empirical nearest-rank quantiles of finite local floating-point diagnostics.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgValueQuantiles {
    pub min: f64,
    pub p10: f64,
    pub median: f64,
    pub p90: f64,
    pub p99: f64,
    pub max: f64,
}

/// Empirical nearest-rank quantiles of marginal neighbor counts.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct KsgCountQuantiles {
    pub min: usize,
    pub p10: usize,
    pub median: usize,
    pub p90: usize,
    pub p99: usize,
    pub max: usize,
}

/// Local-radius, count, and pointwise-term distributions used by the returned KSG estimate.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgLocalDiagnosticsSummary {
    pub joint_radius: KsgValueQuantiles,
    pub x_marginal_count: KsgCountQuantiles,
    pub y_marginal_count: KsgCountQuantiles,
    pub local_mi_nats: KsgValueQuantiles,
}

/// Neighbor-search implementation selected before estimation.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum KsgNeighborBackend {
    BruteForce,
    ExactChebyshevKdTree,
}

/// KSG estimate with scoped support, geometry, sample diagnostics, and caller provenance.
///
/// All information values are in nats. The sample diagnostics can identify observations
/// incompatible with ideal estimator conditions, but cannot determine their cause or prove
/// absolute continuity, a common reference measure, or finite population mutual information. This
/// stable report is restricted to ambient Chebyshev geometry; the feature-gated manifold path has
/// a separate typed report.
///
/// The diagnostic set is intentionally non-exhaustive: it does not estimate intrinsic dimension,
/// distance concentration, temporal dependence, k/n sensitivity, or finite-sample bias. Use the
/// crate's geometry diagnostics and an explicitly reported k/sample-size sensitivity analysis as
/// separate checks.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgMiReport {
    /// Estimate after the requested presentation policy.
    pub estimate_nats: f64,
    /// Unclamped signed estimate. This is always retained so presentation clamping is reversible.
    pub signed_estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub negative_handling: NegativeHandling,
    pub support_contract: SupportContract,
    pub method_status: KsgMethodStatus,
    pub scientific_status: ScientificStatus,
    pub estimand: EstimandIdentity,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub provenance: KsgProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub x_diagnostics: ContinuousInputDiagnostics,
    pub y_diagnostics: ContinuousInputDiagnostics,
    pub joint_shells: NeighborShellDiagnostics,
    pub local_diagnostics: KsgLocalDiagnosticsSummary,
    pub neighbor_backend: KsgNeighborBackend,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub geometry_model: KsgGeometryModel,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub curvature: Option<()>,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub x_hyperbolic_dimension: Option<usize>,
    /// Reserved 0.9 compatibility field; ambient Chebyshev reports always contain `None`.
    pub y_hyperbolic_dimension: Option<usize>,
    /// Warnings in a stable order: support limitation, then observed marginal pathology.
    pub warnings: Vec<KsgReportWarning>,
    pub report_warnings: Vec<WarningCode>,
}

pub(crate) struct KsgReportComputation {
    pub(crate) report: KsgMiReport,
    #[cfg(feature = "experimental-continuous")]
    pub(crate) local_terms_nats: Vec<f64>,
}

/// Complete report sequence for a declared sensitivity trajectory.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct KsgTrajectoryReport {
    pub varied_parameter: &'static str,
    pub reports: Vec<KsgMiReport>,
    pub aggregate_resource_estimate: ResourceEstimate,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicSupportContract {
    /// Caller asserts smooth densities relative to the relevant manifold volume measures and
    /// finite mutual information for every marginal and joint law required by the estimate.
    AssumeSmoothManifold,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicKsgGeometryModel {
    /// Lorentz hyperboloid with the curvature recorded by the report metric.
    LorentzHyperboloid,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicKsgReportWarning {
    /// Sample diagnostics are one-way checks, not population-support proofs.
    SampleDiagnosticsCannotProveSupport,
    /// A marginal neighbor shell is degenerate or ambiguous.
    MarginalNeighborShellPathology,
    /// This crate has no consistency theorem for its manifold KSG path.
    ConsistencyNotEstablished,
}

#[cfg(feature = "experimental-hyperbolic")]
const HYPERBOLIC_KSG_WARNING_CAPACITY: usize = 3;

#[cfg(feature = "experimental-hyperbolic")]
impl HyperbolicKsgReportWarning {
    /// Explanatory text for this warning.
    pub const fn message(self) -> &'static str {
        match self {
            Self::SampleDiagnosticsCannotProveSupport => {
                KsgReportWarning::SampleDiagnosticsCannotProveSupport.message()
            }
            Self::MarginalNeighborShellPathology => {
                KsgReportWarning::MarginalNeighborShellPathology.message()
            }
            Self::ConsistencyNotEstablished => {
                "hyperbolic/manifold KSG is experimental and this implementation lacks a statistical consistency theorem"
            }
        }
    }
}

/// Feature-gated Lorentz KSG estimate with typed geometry and research status.
#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgMiReport {
    pub estimate_nats: f64,
    pub signed_estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub metric: HyperbolicMetric,
    pub negative_handling: NegativeHandling,
    pub support_contract: HyperbolicSupportContract,
    pub method_status: KsgMethodStatus,
    pub scientific_status: ScientificStatus,
    pub estimand: EstimandIdentity,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub provenance: KsgProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub x_diagnostics: ContinuousInputDiagnostics,
    pub y_diagnostics: ContinuousInputDiagnostics,
    pub joint_shells: NeighborShellDiagnostics,
    pub local_diagnostics: KsgLocalDiagnosticsSummary,
    pub neighbor_backend: KsgNeighborBackend,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub geometry_model: HyperbolicKsgGeometryModel,
    pub curvature: HyperbolicCurvature,
    /// `d` inferred from a Lorentz row of width `d + 1`.
    pub x_hyperbolic_dimension: usize,
    /// `d` inferred from a Lorentz row of width `d + 1`.
    pub y_hyperbolic_dimension: usize,
    pub warnings: Vec<HyperbolicKsgReportWarning>,
    pub report_warnings: Vec<WarningCode>,
}

#[cfg(feature = "experimental-hyperbolic")]
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct HyperbolicKsgTrajectoryReport {
    pub varied_parameter: &'static str,
    pub reports: Vec<HyperbolicKsgMiReport>,
    pub aggregate_resource_estimate: ResourceEstimate,
}

/// Estimate KSG mutual information and return scoped interpretation metadata and diagnostics.
///
/// This is the canonical stable entry point. Scalar and local-term paths are available only in
/// the default-off experimental namespace because a publication-facing number must remain coupled
/// to its assumptions, provenance, diagnostics, revision identity, and resource preflight.
pub fn ksg_mi_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<KsgMiReport> {
    ksg_mi_report_with_budget(x, y, cfg, provenance, ResourceBudget::default())
}

/// Report-first KSG with an explicit memory/work/thread budget.
pub fn ksg_mi_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<KsgMiReport> {
    let cancellation = CancellationToken::new();
    ksg_mi_report_with_budget_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

/// Report-first KSG with explicit resource and cooperative-cancellation controls.
pub fn ksg_mi_report_with_budget_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgMiReport> {
    Ok(ksg_mi_report_with_local_terms_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        cancellation,
    )?
    .report)
}

#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_mi_report_with_local_terms(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<KsgReportComputation> {
    let cancellation = CancellationToken::new();
    ksg_mi_report_with_local_terms_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

pub(crate) fn ksg_mi_report_with_local_terms_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgReportComputation> {
    let kernel_config = KernelKsgConfig::stable(cfg);
    ksg_mi_report_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        provenance,
        resource_budget,
        cancellation,
    )
}

fn ksg_mi_report_with_kernel_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgReportComputation> {
    // Preserve shape/config/support error precedence before the report-only provenance gate.
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, cfg)?;
    #[cfg(feature = "experimental-hyperbolic")]
    if matches!(cfg.kernel_metric, KernelMetric::HyperbolicLorentz { .. })
        && provenance.embedding_training_provenance().is_none()
    {
        return Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        });
    }

    let effective_threads = effective_thread_count(resource_budget.max_threads, x.nrows());
    let resource_estimate = ksg_report_resource_estimate(x, y, provenance, effective_threads)?;
    resource_budget.check("ksg_mi_report", resource_estimate)?;
    cancellation.check("ksg_mi_report", 0, x.nrows())?;
    let use_tree = NnBackend::Auto.use_tree(cfg.kernel_metric, x.nrows(), x.ncols() + y.ncols());
    let local = with_thread_budget(effective_threads, || {
        ksg_local_diagnostics_backend_with_kernel_and_cancellation(
            x,
            y,
            cfg,
            NnBackend::Auto,
            resource_budget,
            cancellation,
        )
    })?;
    let signed_estimate =
        compensated_sum(local.iter().map(|value| value.term_nats)) / local.len() as f64;
    let estimate_nats = match cfg.negative_handling {
        NegativeHandling::Allow => signed_estimate,
        NegativeHandling::ClampToZero => signed_estimate.max(0.0),
    };
    #[cfg(feature = "experimental-continuous")]
    let local_terms_nats = {
        let mut terms =
            try_vec_with_capacity("ksg retained local terms", local.len(), resource_budget)?;
        terms.extend(local.iter().map(|value| value.term_nats));
        terms
    };
    let local_diagnostics =
        summarize_local_diagnostics_with_cancellation(&local, resource_budget, cancellation)?;
    let x_diagnostics = continuous_input_diagnostics_with_kernel_and_cancellation(
        x,
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;
    let y_diagnostics = continuous_input_diagnostics_with_kernel_and_cancellation(
        y,
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;
    let joint_shells = continuous_joint_shell_diagnostics_with_kernel_and_cancellation(
        &[x, y],
        cfg.k,
        cfg.kernel_metric,
        resource_budget,
        cancellation,
    )?;

    let mut warnings = try_vec_with_capacity("ksg warnings", 3, resource_budget)?;
    warnings.push(KsgReportWarning::SampleDiagnosticsCannotProveSupport);
    if has_shell_pathology(x_diagnostics.marginal_shells)
        || has_shell_pathology(y_diagnostics.marginal_shells)
    {
        warnings.push(KsgReportWarning::MarginalNeighborShellPathology);
    }

    let (method_status, x_hyperbolic_dimension, y_hyperbolic_dimension) = match cfg.kernel_metric {
        KernelMetric::Chebyshev => (KsgMethodStatus::RestrictedDomain, None, None),
        #[cfg(feature = "experimental-hyperbolic")]
        KernelMetric::HyperbolicLorentz { .. } => (
            KsgMethodStatus::Experimental,
            Some(x.ncols() - 1),
            Some(y.ncols() - 1),
        ),
    };

    let scientific_status = match method_status {
        KsgMethodStatus::RestrictedDomain => ScientificStatus::ConditionalContinuous,
        KsgMethodStatus::Experimental => ScientificStatus::ResearchOnly,
    };
    let metric_identity = match cfg.kernel_metric {
        KernelMetric::Chebyshev => "chebyshev-max-product",
        #[cfg(feature = "experimental-hyperbolic")]
        KernelMetric::HyperbolicLorentz { .. } => "lorentz-hyperboloid-curvature-minus-one",
    };
    let estimand = EstimandIdentity {
        family: "kraskov-stoegbauer-grassberger-mutual-information",
        definition_revision: "ksg1-product-small-ball-v1",
        estimator_revision: "strict-unique-shell-report-v3",
        units: InformationUnit::Nats,
        metric: metric_identity,
        source_gauge: None,
    };
    let assumption_ledger = ksg_assumption_ledger(provenance, joint_shells, resource_budget)?;
    let mut input_hashes_sha256 =
        try_vec_with_capacity("ksg report input hashes", 2, resource_budget)?;
    input_hashes_sha256.extend([
        hash_matrix_with_cancellation(x, cancellation)?,
        hash_matrix_with_cancellation(y, cancellation)?,
    ]);
    let provenance_hashes = ProvenanceHashes {
        input_hashes_sha256,
        preprocessing_hash_sha256: hash_text(provenance.preprocessing_description()),
        observation_model_hash_sha256: hash_text(provenance.observation_model_description()),
        training_split_id: provenance
            .training_split_id()
            .map(|value| try_provenance_string("ksg report split identity", value))
            .transpose()?,
        evaluation_split_id: provenance
            .evaluation_split_id()
            .map(|value| try_provenance_string("ksg report split identity", value))
            .transpose()?,
    };
    let mut report_warnings = try_vec_with_capacity("ksg report warnings", 8, resource_budget)?;
    report_warnings.push(WarningCode::DiagnosticsDoNotProvePopulationAssumptions);
    if matches!(
        cfg.support_contract,
        SupportContract::AssumeRegularFullDimensional {
            boundary: BoundaryModel::Unknown,
            ..
        }
    ) {
        report_warnings.push(WarningCode::BoundaryModelUnknown);
    }
    if provenance.sampling_model_description.is_none() {
        report_warnings.push(WarningCode::DependenceDiagnosticsNotEvaluated);
    }
    report_warnings.extend([
        WarningCode::KTrajectoryNotEvaluated,
        WarningCode::SampleSizeTrajectoryNotEvaluated,
        WarningCode::TransformationSensitivityNotEvaluated,
        WarningCode::ObservationNoiseSensitivityNotEvaluated,
    ]);
    if scientific_status == ScientificStatus::ResearchOnly {
        report_warnings.push(WarningCode::ExperimentalEstimator);
    }

    let report = KsgMiReport {
        estimate_nats,
        signed_estimate_nats: signed_estimate,
        n_samples: x.nrows(),
        k: cfg.k,
        metric: cfg.metric,
        negative_handling: cfg.negative_handling,
        support_contract: cfg.support_contract,
        method_status,
        scientific_status,
        estimand,
        assumption_ledger,
        provenance: provenance.try_clone_with_budget(resource_budget)?,
        provenance_hashes,
        x_diagnostics,
        y_diagnostics,
        joint_shells,
        local_diagnostics,
        neighbor_backend: if use_tree {
            KsgNeighborBackend::ExactChebyshevKdTree
        } else {
            KsgNeighborBackend::BruteForce
        },
        resource_estimate,
        resource_budget,
        geometry_model: KsgGeometryModel::AmbientChebyshev,
        curvature: None,
        x_hyperbolic_dimension,
        y_hyperbolic_dimension,
        warnings,
        report_warnings,
    };
    cancellation.check("ksg_mi_report", x.nrows(), x.nrows())?;
    Ok(KsgReportComputation {
        report,
        #[cfg(feature = "experimental-continuous")]
        local_terms_nats,
    })
}

/// Compute a feature-gated Lorentz-model KSG report.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<HyperbolicKsgMiReport> {
    hyperbolic_ksg_mi_report_with_budget(x, y, cfg, provenance, ResourceBudget::default())
}

/// Compute a Lorentz-model KSG report under an explicit resource budget.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
) -> PidResult<HyperbolicKsgMiReport> {
    let cancellation = CancellationToken::new();
    hyperbolic_ksg_mi_report_with_budget_and_cancellation(
        x,
        y,
        cfg,
        provenance,
        resource_budget,
        &cancellation,
    )
}

/// Compute a Lorentz-model KSG report with resource and cancellation controls.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_mi_report_with_budget_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<HyperbolicKsgMiReport> {
    let kernel_config = cfg.kernel_config();
    // Preserve structural/support and provenance error precedence before resource preflight.
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    validate_hyperbolic_ksg_provenance(provenance)?;
    let resource_estimate = hyperbolic_ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(resource_budget.max_threads, x.nrows()),
    )?;
    resource_budget.check("hyperbolic_ksg_mi_report", resource_estimate)?;
    let report = ksg_mi_report_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        provenance,
        resource_budget,
        cancellation,
    )?
    .report;

    let warning_count = report
        .warnings
        .len()
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    if warning_count > HYPERBOLIC_KSG_WARNING_CAPACITY {
        return Err(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        });
    }
    let mut warnings = try_vec_with_capacity(
        "hyperbolic KSG warnings",
        HYPERBOLIC_KSG_WARNING_CAPACITY,
        resource_budget,
    )?;
    for warning in report.warnings {
        warnings.push(match warning {
            KsgReportWarning::SampleDiagnosticsCannotProveSupport => {
                HyperbolicKsgReportWarning::SampleDiagnosticsCannotProveSupport
            }
            KsgReportWarning::MarginalNeighborShellPathology => {
                HyperbolicKsgReportWarning::MarginalNeighborShellPathology
            }
        });
    }
    warnings.push(HyperbolicKsgReportWarning::ConsistencyNotEstablished);

    Ok(HyperbolicKsgMiReport {
        estimate_nats: report.estimate_nats,
        signed_estimate_nats: report.signed_estimate_nats,
        n_samples: report.n_samples,
        k: report.k,
        metric: cfg.metric,
        negative_handling: report.negative_handling,
        support_contract: HyperbolicSupportContract::AssumeSmoothManifold,
        method_status: report.method_status,
        scientific_status: report.scientific_status,
        estimand: report.estimand,
        assumption_ledger: report.assumption_ledger,
        provenance: report.provenance,
        provenance_hashes: report.provenance_hashes,
        x_diagnostics: report.x_diagnostics,
        y_diagnostics: report.y_diagnostics,
        joint_shells: report.joint_shells,
        local_diagnostics: report.local_diagnostics,
        neighbor_backend: report.neighbor_backend,
        resource_estimate,
        resource_budget: report.resource_budget,
        geometry_model: HyperbolicKsgGeometryModel::LorentzHyperboloid,
        curvature: cfg.metric.curvature,
        x_hyperbolic_dimension: x.ncols() - 1,
        y_hyperbolic_dimension: y.ncols() - 1,
        warnings,
        report_warnings: report.report_warnings,
    })
}

#[cfg(feature = "experimental-hyperbolic")]
fn validate_hyperbolic_ksg_provenance(provenance: &KsgProvenance) -> PidResult<()> {
    if provenance.embedding_training_provenance().is_none() {
        return Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        });
    }
    Ok(())
}

/// Evaluate Lorentz-model reports over a declared `k` grid.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_k_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    k_values: &[usize],
    base_config: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<HyperbolicKsgTrajectoryReport> {
    if k_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_k_trajectory",
            message: "k_values must be nonempty",
        });
    }
    for &k in k_values {
        let config = base_config.clone().with_k(k);
        let kernel_config = config.kernel_config();
        validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    }
    validate_hyperbolic_ksg_provenance(provenance)?;
    let one = hyperbolic_ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(budget.max_threads, x.nrows()),
    )?;
    let aggregate = repeat_resource_estimate("ksg_k_trajectory", one, k_values.len())?;
    budget.check("ksg_k_trajectory", aggregate)?;
    let mut reports = try_vec_with_capacity("ksg_k_trajectory", k_values.len(), budget)?;
    for &k in k_values {
        let config = base_config.clone().with_k(k);
        reports.push(hyperbolic_ksg_mi_report_with_budget(
            x, y, &config, provenance, budget,
        )?);
    }
    Ok(HyperbolicKsgTrajectoryReport {
        varied_parameter: "k",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate Lorentz-model reports on increasing row prefixes.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_sample_size_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    sample_sizes: &[usize],
    config: &HyperbolicKsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<HyperbolicKsgTrajectoryReport> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "ksg_sample_size_trajectory",
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if sample_sizes.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_sample_size_trajectory",
            message: "sample_sizes must be nonempty",
        });
    }
    let kernel_config = config.kernel_config();
    validate_ksg_pair_structure_with_kernel("ksg_mi_report", x, y, &kernel_config)?;
    for &n in sample_sizes {
        if n > x.nrows() || n <= config.k {
            return Err(PidError::InvalidK {
                k: config.k,
                n_samples: n,
            });
        }
    }
    validate_hyperbolic_ksg_provenance(provenance)?;
    let mut aggregate = ResourceEstimate::ZERO;
    for &n in sample_sizes {
        let x_len = n.checked_mul(x.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let y_len = n.checked_mul(y.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        aggregate = add_resource_estimates(
            "ksg_sample_size_trajectory",
            aggregate,
            hyperbolic_ksg_report_resource_estimate(
                x_prefix,
                y_prefix,
                provenance,
                effective_thread_count(budget.max_threads, n),
            )?,
        )?;
    }
    budget.check("ksg_sample_size_trajectory", aggregate)?;
    let mut reports =
        try_vec_with_capacity("ksg_sample_size_trajectory", sample_sizes.len(), budget)?;
    for &n in sample_sizes {
        let x_len = n * x.ncols();
        let y_len = n * y.ncols();
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        reports.push(hyperbolic_ksg_mi_report_with_budget(
            x_prefix, y_prefix, config, provenance, budget,
        )?);
    }
    Ok(HyperbolicKsgTrajectoryReport {
        varied_parameter: "sample_size",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate complete reports over a declared `k` grid without discarding diagnostics.
pub fn ksg_k_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    k_values: &[usize],
    base_config: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<KsgTrajectoryReport> {
    if k_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_k_trajectory",
            message: "k_values must be nonempty",
        });
    }
    let one = ksg_report_resource_estimate(
        x,
        y,
        provenance,
        effective_thread_count(budget.max_threads, x.nrows()),
    )?;
    let aggregate = repeat_resource_estimate("ksg_k_trajectory", one, k_values.len())?;
    budget.check("ksg_k_trajectory", aggregate)?;
    let mut reports = try_vec_with_capacity("ksg_k_trajectory", k_values.len(), budget)?;
    for &k in k_values {
        let mut config = base_config.clone();
        config.k = k;
        reports.push(ksg_mi_report_with_budget(
            x, y, &config, provenance, budget,
        )?);
    }
    Ok(KsgTrajectoryReport {
        varied_parameter: "k",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

/// Evaluate complete reports on increasing row prefixes.
///
/// Prefix trajectories are scientifically meaningful only when row ordering is independent of
/// the process being estimated (for example a fixed seeded random ordering). The ordering policy
/// belongs in provenance.
pub fn ksg_sample_size_trajectory(
    x: MatRef<'_>,
    y: MatRef<'_>,
    sample_sizes: &[usize],
    config: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<KsgTrajectoryReport> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "ksg_sample_size_trajectory",
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if sample_sizes.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "ksg_sample_size_trajectory",
            message: "sample_sizes must be nonempty",
        });
    }
    let mut aggregate = ResourceEstimate::ZERO;
    for &n in sample_sizes {
        if n > x.nrows() || n <= config.k {
            return Err(PidError::InvalidK {
                k: config.k,
                n_samples: n,
            });
        }
        let x_len = n.checked_mul(x.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let y_len = n.checked_mul(y.ncols()).ok_or(PidError::SizeOverflow {
            operation: "ksg_sample_size_trajectory",
        })?;
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        aggregate = add_resource_estimates(
            "ksg_sample_size_trajectory",
            aggregate,
            ksg_report_resource_estimate(
                x_prefix,
                y_prefix,
                provenance,
                effective_thread_count(budget.max_threads, n),
            )?,
        )?;
    }
    budget.check("ksg_sample_size_trajectory", aggregate)?;
    let mut reports =
        try_vec_with_capacity("ksg_sample_size_trajectory", sample_sizes.len(), budget)?;
    for &n in sample_sizes {
        let x_len = n * x.ncols();
        let y_len = n * y.ncols();
        let x_prefix = MatRef::new(&x.as_slice()[..x_len], n, x.ncols())?;
        let y_prefix = MatRef::new(&y.as_slice()[..y_len], n, y.ncols())?;
        reports.push(ksg_mi_report_with_budget(
            x_prefix, y_prefix, config, provenance, budget,
        )?);
    }
    Ok(KsgTrajectoryReport {
        varied_parameter: "sample_size",
        reports,
        aggregate_resource_estimate: aggregate,
    })
}

fn repeat_resource_estimate(
    operation: &'static str,
    estimate: ResourceEstimate,
    count: usize,
) -> PidResult<ResourceEstimate> {
    let count = count as u128;
    Ok(ResourceEstimate {
        // Reports run sequentially, but their owned diagnostics/provenance remain in the
        // trajectory. Multiplying the full per-report estimate is conservative and guarantees
        // retained output cannot bypass the caller's ceiling.
        estimated_bytes: estimate
            .estimated_bytes
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
        pairwise_distances: estimate
            .pairwise_distances
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
        operations_hint: estimate
            .operations_hint
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow { operation })?,
    })
}

fn add_resource_estimates(
    operation: &'static str,
    left: ResourceEstimate,
    right: ResourceEstimate,
) -> PidResult<ResourceEstimate> {
    Ok(ResourceEstimate {
        // Retained reports accumulate in the trajectory. Summing the complete per-report peaks
        // is conservative but prevents output heaps from escaping the aggregate ceiling.
        estimated_bytes: left
            .estimated_bytes
            .checked_add(right.estimated_bytes)
            .ok_or(PidError::SizeOverflow { operation })?,
        pairwise_distances: left
            .pairwise_distances
            .checked_add(right.pairwise_distances)
            .ok_or(PidError::SizeOverflow { operation })?,
        operations_hint: left
            .operations_hint
            .checked_add(right.operations_hint)
            .ok_or(PidError::SizeOverflow { operation })?,
    })
}

fn has_shell_pathology(diagnostics: NeighborShellDiagnostics) -> bool {
    diagnostics.zero_radius_queries > 0 || diagnostics.ambiguous_positive_shell_queries > 0
}

/// Worst-case pairwise-work and scratch/tree-memory estimate for report-first KSG.
pub fn ksg_resource_estimate(x: MatRef<'_>, y: MatRef<'_>) -> PidResult<ResourceEstimate> {
    ksg_resource_estimate_with_coordinate_work_factor(x, y, 1)
}

fn ksg_resource_estimate_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ksg_mi_report";
    let n = x.nrows() as u128;
    let dimensions = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })? as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let tree_build_operations = n
        .checked_mul(dimensions.max(1))
        .and_then(|value| {
            value.checked_mul(if x.nrows() <= 1 {
                1
            } else {
                (usize::BITS - (x.nrows() - 1).leading_zeros()) as u128
            })
        })
        .and_then(|value| value.checked_mul(3))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let estimator_operations = pairs
        .checked_mul(dimensions.max(1))
        .and_then(|value| value.checked_mul(coordinate_work_factor))
        .and_then(|value| value.checked_mul(6))
        .and_then(|value| value.checked_add(tree_build_operations))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    // Conservative simultaneous tree/scratch/local-diagnostic storage. The estimator does not
    // materialize an n-by-n distance matrix.
    let estimator_bytes = dimensions
        .checked_mul(4)
        .and_then(|value| value.checked_add(64))
        .and_then(|value| value.checked_mul(n))
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let x_support = crate::support::continuous_diagnostics_resource_estimate(
        &[x],
        true,
        coordinate_work_factor,
    )?;
    let y_support = crate::support::continuous_diagnostics_resource_estimate(
        &[y],
        true,
        coordinate_work_factor,
    )?;
    let joint_support = crate::support::continuous_diagnostics_resource_estimate(
        &[x, y],
        false,
        coordinate_work_factor,
    )?;
    let support_peak_bytes = x_support
        .estimated_bytes
        .max(y_support.estimated_bytes)
        .max(joint_support.estimated_bytes);
    let estimated_bytes =
        estimator_bytes
            .checked_add(support_peak_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    let pairwise_distances = pairs
        .checked_add(x_support.pairwise_distances)
        .and_then(|value| value.checked_add(y_support.pairwise_distances))
        .and_then(|value| value.checked_add(joint_support.pairwise_distances))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let operations_hint =
        estimator_operations
            .checked_add(x_support.operations_hint.checked_mul(2).ok_or(
                PidError::SizeOverflow {
                    operation: OPERATION,
                },
            )?)
            .and_then(|value| value.checked_add(y_support.operations_hint.checked_mul(2)?))
            .and_then(|value| value.checked_add(joint_support.operations_hint))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances,
        operations_hint,
    })
}

/// Conservative KSG preflight including one brute-force scratch buffer per worker.
pub fn ksg_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    ksg_resource_estimate_for_threads_with_coordinate_work_factor(x, y, max_threads, 1)
}

fn ksg_resource_estimate_for_threads_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: "ksg_mi_report",
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    let mut estimate =
        ksg_resource_estimate_with_coordinate_work_factor(x, y, coordinate_work_factor)?;
    #[cfg(feature = "parallel")]
    let additional_scratch = {
        let active_threads = max_threads.min(x.nrows()).max(1) as u128;
        let scratch = active_threads
            .saturating_sub(1)
            .checked_mul(x.nrows() as u128)
            .and_then(|value| value.checked_mul(std::mem::size_of::<DistPair>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
        let stacks = active_threads
            .checked_mul(WORKER_STACK_BYTES as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
        scratch.checked_add(stacks).ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?
    };
    #[cfg(not(feature = "parallel"))]
    let additional_scratch = 0;
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(additional_scratch)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    Ok(estimate)
}

/// Full report preflight, including worker scratch and retained provenance/diagnostic output.
pub fn ksg_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    ksg_report_resource_estimate_with_coordinate_work_factor(x, y, provenance, max_threads, 1)
}

fn ksg_report_resource_estimate_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    let split_identity_bytes = provenance
        .training_split_id()
        .into_iter()
        .chain(provenance.evaluation_split_id())
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "ksg_mi_report",
                })
        })?;
    ksg_report_resource_estimate_for_provenance_bytes_with_coordinate_work_factor(
        x,
        y,
        provenance.heap_bytes()?,
        split_identity_bytes,
        max_threads,
        coordinate_work_factor,
    )
}

/// Full Lorentz-report preflight, including the typed wrapper and warning conversion.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_ksg_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let mut estimate = ksg_report_resource_estimate_with_coordinate_work_factor(
        x,
        y,
        provenance,
        max_threads,
        crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR,
    )?;
    let warning_capacity = HYPERBOLIC_KSG_WARNING_CAPACITY as u128;
    let wrapper_bytes = (std::mem::size_of::<HyperbolicKsgMiReport>() as u128)
        .checked_add(
            warning_capacity
                .checked_mul(std::mem::size_of::<HyperbolicKsgReportWarning>() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "hyperbolic_ksg_mi_report",
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(wrapper_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: "hyperbolic_ksg_mi_report",
            })?;
    estimate.operations_hint = estimate
        .operations_hint
        .checked_add(warning_capacity)
        .ok_or(PidError::SizeOverflow {
            operation: "hyperbolic_ksg_mi_report",
        })?;
    Ok(estimate)
}

fn ksg_report_resource_estimate_for_provenance_bytes_with_coordinate_work_factor(
    x: MatRef<'_>,
    y: MatRef<'_>,
    provenance_heap_bytes: u128,
    split_identity_bytes: u128,
    max_threads: usize,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    let estimate = ksg_resource_estimate_for_threads_with_coordinate_work_factor(
        x,
        y,
        max_threads,
        coordinate_work_factor,
    )?;
    let dimensions = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    add_ksg_report_retained(
        estimate,
        x.nrows(),
        dimensions,
        provenance_heap_bytes,
        split_identity_bytes,
    )
}

/// Report preflight for a source represented as several Chebyshev-concatenated blocks.
///
/// This is used by higher-level report assemblers so they can preflight a joint-variable report
/// without first allocating the explicit row-major concatenation used for the retained report.
#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_xblocks_report_resource_estimate(
    x_blocks: &[MatRef<'_>],
    y: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ksg_mi_xblocks_report";
    if x_blocks.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "x_blocks must be nonempty",
        });
    }
    let dimensions = x_blocks.iter().try_fold(y.ncols(), |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })
    })?;
    let split_identity_bytes = provenance
        .training_split_id()
        .into_iter()
        .chain(provenance.evaluation_split_id())
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })
        })?;
    add_ksg_report_retained(
        ksg_xblocks_resource_estimate(x_blocks, y, max_threads)?,
        y.nrows(),
        dimensions,
        provenance.heap_bytes()?,
        split_identity_bytes,
    )
}

fn add_ksg_report_retained(
    mut estimate: ResourceEstimate,
    n_samples: usize,
    dimensions: usize,
    provenance_heap_bytes: u128,
    split_identity_bytes: u128,
) -> PidResult<ResourceEstimate> {
    let retained_local_terms = (n_samples as u128)
        .checked_mul(std::mem::size_of::<f64>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    let retained_bytes = provenance_heap_bytes
        .checked_add(split_identity_bytes)
        .and_then(|value| value.checked_add(retained_local_terms))
        .and_then(|value| value.checked_add(std::mem::size_of::<KsgMiReport>() as u128))
        .and_then(|value| {
            value.checked_add(
                12u128.checked_mul(std::mem::size_of::<AssumptionLedgerEntry>() as u128)?,
            )
        })
        .and_then(|value| value.checked_add(2 * 32))
        .and_then(|value| {
            value.checked_add(
                (dimensions as u128)
                    .checked_mul(std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128)?,
            )
        })
        .and_then(|value| {
            value.checked_add(3u128.checked_mul(std::mem::size_of::<KsgReportWarning>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(8u128.checked_mul(std::mem::size_of::<WarningCode>() as u128)?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_mi_report",
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(retained_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_mi_report",
            })?;
    Ok(estimate)
}

fn summarize_local_diagnostics_with_cancellation(
    local: &[KsgLocalDiagnostic],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<KsgLocalDiagnosticsSummary> {
    let mut radii = try_vec_with_capacity("ksg local radius summary", local.len(), budget)?;
    let mut x_counts = try_vec_with_capacity("ksg x-count summary", local.len(), budget)?;
    let mut y_counts = try_vec_with_capacity("ksg y-count summary", local.len(), budget)?;
    let mut terms = try_vec_with_capacity("ksg local-term summary", local.len(), budget)?;
    for (index, diagnostic) in local.iter().enumerate() {
        if index.is_multiple_of(1024) {
            cancellation.check("ksg local diagnostic summary", index, local.len())?;
        }
        radii.push(diagnostic.joint_radius);
        x_counts.push(diagnostic.x_count);
        y_counts.push(diagnostic.y_count);
        terms.push(diagnostic.term_nats);
    }
    sort_unstable_by_with_cancellation(
        "ksg local radius summary",
        &mut radii,
        cancellation,
        f64::total_cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg x-count summary",
        &mut x_counts,
        cancellation,
        Ord::cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg y-count summary",
        &mut y_counts,
        cancellation,
        Ord::cmp,
    )?;
    sort_unstable_by_with_cancellation(
        "ksg local-term summary",
        &mut terms,
        cancellation,
        f64::total_cmp,
    )?;
    Ok(KsgLocalDiagnosticsSummary {
        joint_radius: value_quantiles(&radii)?,
        x_marginal_count: count_quantiles(&x_counts)?,
        y_marginal_count: count_quantiles(&y_counts)?,
        local_mi_nats: value_quantiles(&terms)?,
    })
}

fn nearest_rank_index(len: usize, percentile: u128) -> PidResult<usize> {
    if len == 0 || percentile > 100 {
        return Err(PidError::InvalidConfig {
            context: "ksg diagnostic quantiles",
            message: "quantiles require nonempty data and a percentile in 0..=100",
        });
    }
    let numerator = (len.saturating_sub(1) as u128)
        .checked_mul(percentile)
        .and_then(|value| value.checked_add(50))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg diagnostic quantiles",
        })?;
    usize::try_from(numerator / 100).map_err(|_| PidError::SizeOverflow {
        operation: "ksg diagnostic quantiles",
    })
}

pub(crate) fn value_quantiles(sorted: &[f64]) -> PidResult<KsgValueQuantiles> {
    if sorted.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "ksg local diagnostic contains a non-finite value",
        });
    }
    Ok(KsgValueQuantiles {
        min: sorted[nearest_rank_index(sorted.len(), 0)?],
        p10: sorted[nearest_rank_index(sorted.len(), 10)?],
        median: sorted[nearest_rank_index(sorted.len(), 50)?],
        p90: sorted[nearest_rank_index(sorted.len(), 90)?],
        p99: sorted[nearest_rank_index(sorted.len(), 99)?],
        max: sorted[nearest_rank_index(sorted.len(), 100)?],
    })
}

pub(crate) fn count_quantiles(sorted: &[usize]) -> PidResult<KsgCountQuantiles> {
    Ok(KsgCountQuantiles {
        min: sorted[nearest_rank_index(sorted.len(), 0)?],
        p10: sorted[nearest_rank_index(sorted.len(), 10)?],
        median: sorted[nearest_rank_index(sorted.len(), 50)?],
        p90: sorted[nearest_rank_index(sorted.len(), 90)?],
        p99: sorted[nearest_rank_index(sorted.len(), 99)?],
        max: sorted[nearest_rank_index(sorted.len(), 100)?],
    })
}

fn ksg_assumption_ledger(
    provenance: &KsgProvenance,
    joint_shells: NeighborShellDiagnostics,
    budget: ResourceBudget,
) -> PidResult<Vec<AssumptionLedgerEntry>> {
    let mut ledger = try_vec_with_capacity("ksg assumption ledger", 12, budget)?;
    let shell_state = if joint_shells.zero_radius_queries == 0
        && joint_shells.ambiguous_positive_shell_queries == 0
    {
        AssumptionState::FiniteSampleChecksPassed
    } else {
        AssumptionState::UnsupportedObservedCondition
    };
    ledger.extend([
        AssumptionLedgerEntry {
            assumption: Assumption::RegularContinuousOrManifoldLaw,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; finite samples cannot prove the population support model",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedLocalDimension,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller asserts each required marginal and joint law is locally fixed-dimensional in its own ambient space",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::RegularFiniteDensity,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; radius trajectories are still required",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FiniteMutualInformation,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; a finite estimate does not prove finite population MI",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::DeclaredSamplingDependence,
            state: if provenance.sampling_model_description.is_some() {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "dependence diagnostics are workflow-specific and not inferred here",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::UniqueKthNeighborShell,
            state: shell_state,
            note: "every joint shell used by the estimate is checked exactly",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LocalNeighborhoods,
            state: AssumptionState::NotEvaluated,
            note: "interpret the reported radius quantiles against domain scales",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::CommonBranchLeadingScale,
            state: AssumptionState::NotEvaluated,
            note: "not used by pairwise MI; required by continuous shared exclusions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LowerOrderBranchIntersections,
            state: AssumptionState::NotEvaluated,
            note: "not used by pairwise MI; required by continuous shared exclusions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedPreprocessingAndMetric,
            state: AssumptionState::AssumptionsDeclared,
            note: "the preprocessing description and metric are hashed in the report",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdequateSampleSize,
            state: AssumptionState::NotEvaluated,
            note: "run declared k and increasing-sample-size trajectories",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdaptiveTransformsFitOutsideEvaluationData,
            state: if provenance.training_split_id.is_some()
                && provenance.evaluation_split_id.is_some()
                && provenance.training_split_id != provenance.evaluation_split_id
            {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "distinct training and evaluation split identifiers are required for adaptive transforms",
        },
    ]);
    Ok(ledger)
}

#[cfg(feature = "experimental-continuous")]
pub(crate) fn hash_matrix(matrix: MatRef<'_>) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    for row in 0..matrix.nrows() {
        for value in matrix.row(row) {
            digest.update(value.to_bits().to_le_bytes());
        }
    }
    digest.finalize().into()
}

fn hash_matrix_with_cancellation(
    matrix: MatRef<'_>,
    cancellation: &CancellationToken,
) -> PidResult<[u8; 32]> {
    let total_values =
        matrix
            .nrows()
            .checked_mul(matrix.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg report input hash",
            })?;
    let mut digest = Sha256::new();
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    let mut completed_values = 0usize;
    cancellation.check("ksg report input hash", completed_values, total_values)?;
    for row in 0..matrix.nrows() {
        for value in matrix.row(row) {
            digest.update(value.to_bits().to_le_bytes());
            completed_values += 1;
            if completed_values.is_multiple_of(1024) {
                cancellation.check("ksg report input hash", completed_values, total_values)?;
            }
        }
    }
    cancellation.check("ksg report input hash", completed_values, total_values)?;
    Ok(digest.finalize().into())
}

pub(crate) fn hash_text(value: &str) -> [u8; 32] {
    Sha256::digest(value.as_bytes()).into()
}

/// KSG mutual information estimator (Algorithm 1 style).
///
/// - Uses a kNN search in joint space (X,Y). This scalar API accepts ordinary Chebyshev/L∞
///   geometry; experimental Lorentz geometry is provenance-gated through
///   `hyperbolic_ksg_mi_report`.
/// - Uses strict-inequality semantics for marginal counts (`< eps_raw`) via `strict_radius` + `<=`.
/// - Returns MI in nats (natural log).
///
/// Eligible low-dimensional Chebyshev inputs use an exact kd-tree with typically
/// sublinear pruned queries; other inputs use the brute-force scan. A kd-tree query
/// is still O(n) in the worst case, so the estimator remains O(n²) worst-case.
///
/// # Assumptions / failure modes
/// - **Declared support:** the default support contract is unspecified and fails closed. Ordinary
///   Chebyshev KSG requires a caller assertion that every marginal and joint law used here is
///   full-dimensional and absolutely continuous. Exact coordinate ties are incompatible with the
///   estimator's ideal i.i.d., unrounded continuous-sample conditions, but neither identify their
///   cause nor classify population support; all-unique finite observations do not prove the model.
/// - **i.i.d. samples:** KSG assumes independent samples from a fixed distribution. For time-series
///   data (VLA trajectories), autocorrelation can seriously bias estimates unless you subsample or
///   otherwise account for dependence.
/// - **Observed ties and geometry:** exact coordinate ties are rejected by the continuous-sample
///   preflight. Separately, an otherwise accepted sample can still produce a non-positive kNN
///   radius or multiple observations on a positive boundary; those cases trigger
///   `PidError::NumericalInstability` or `PidError::AmbiguousKthNeighborShell`, respectively.
///   Adding jitter changes the estimated distribution; use it only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis. Otherwise
///   use an estimator whose discrete, quantized, or mixed-support contract matches the data.
/// - **High dimension:** kNN distances concentrate with large ambient/intrinsic dimension; the
///   estimator can become unstable or dominated by finite-sample noise.
/// - **Strong dependence:** even at low dimension, near-deterministic relationships (very large
///   true MI) can require prohibitive sample sizes for kNN MI (see Gao, Ver Steeg, Galstyan 2015).
///   An exact deterministic map between continuous variables has infinite MI and is outside this
///   estimator's domain. An explicit observation-noise model defines a different, finite-MI
///   distribution; otherwise use a suitable discrete/mixed method.
/// - **Clamping:** `KsgConfig` returns signed estimates by default. Opting into
///   `NegativeHandling::ClampToZero` is a presentation transform, not a mathematical property of
///   the estimator, and must not be applied before algebraic identities or inference.
///
/// # Example
/// ```rust,ignore
/// use pid_core::{experimental::continuous::ksg_mi, stable::continuous::KsgConfig, MatRef};
/// // Columns are dimensions, rows are samples: scalar X and a dependent Y.
/// let x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
/// let y = [0.1, 0.9, 2.1, 2.8, 4.2, 4.9, 6.1, 7.0];
/// let x = MatRef::new(&x, 8, 1)?;
/// let y = MatRef::new(&y, 8, 1)?;
/// let mi = ksg_mi(x, y, &KsgConfig::assume_regular_full_dimensional())?; // nats
/// assert!(mi.is_finite());
/// # Ok::<(), pid_core::PidError>(())
/// ```
#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    ksg_mi_with_budget(x, y, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    validate_ksg_pair_structure("ksg_mi", x, y, cfg)?;
    let local = ksg_local_mi_terms_with_budget(x, y, cfg, budget)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

/// Returns the per-sample local MI contributions whose average is the **unclamped** KSG MI
/// estimate (i.e. [`ksg_mi`] configured with [`NegativeHandling::Allow`]).
///
/// local_i = ψ(k) + ψ(n) - ψ(n_x(i)+1) - ψ(n_y(i)+1)
///
/// If [`ksg_mi`] is explicitly configured with [`NegativeHandling::ClampToZero`], low-MI data can
/// have a local-term mean slightly below the floored value that [`ksg_mi`] reports. The default
/// [`NegativeHandling::Allow`] returns this signed mean unchanged.
///
/// This is useful for building shared-exclusions estimators based on pointwise terms.
#[cfg(feature = "experimental-continuous")]
pub(crate) fn ksg_local_mi_terms(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_with_budget(x, y, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_local_mi_terms_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    validate_ksg_pair_structure("ksg_local_mi_terms", x, y, cfg)?;
    ksg_local_mi_terms_backend_with_budget(x, y, cfg, NnBackend::Auto, budget)
}

#[cfg(any(feature = "experimental-continuous", test))]
#[cfg(test)]
pub(crate) fn ksg_local_mi_terms_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_backend_with_budget(x, y, cfg, backend, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_mi_terms_backend_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let threads = effective_thread_count(budget.max_threads, x.nrows());
    let diagnostics = with_thread_budget(threads, || {
        ksg_local_diagnostics_backend(x, y, cfg, backend, budget)
    })?;
    let mut terms = try_vec_with_capacity("ksg local MI terms", diagnostics.len(), budget)?;
    terms.extend(
        diagnostics
            .into_iter()
            .map(|diagnostic| diagnostic.term_nats),
    );
    Ok(terms)
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_diagnostics_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
    resource_budget: ResourceBudget,
) -> PidResult<Vec<KsgLocalDiagnostic>> {
    let cancellation = CancellationToken::new();
    let kernel_config = KernelKsgConfig::stable(cfg);
    ksg_local_diagnostics_backend_with_kernel_and_cancellation(
        x,
        y,
        &kernel_config,
        backend,
        resource_budget,
        &cancellation,
    )
}

fn ksg_local_diagnostics_backend_with_kernel_and_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
    backend: NnBackend,
    resource_budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<KsgLocalDiagnostic>> {
    validate_ksg_pair_structure_with_kernel("ksg_local_mi_terms", x, y, cfg)?;
    let n = x.nrows();
    let k = cfg.k;
    let joint_dims = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms",
        })?;
    let threads = effective_thread_count(resource_budget.max_threads, n);
    resource_budget.check(
        "ksg_local_mi_terms",
        ksg_resource_estimate_for_threads(x, y, threads)?,
    )?;
    match cfg.kernel_support_mode {
        KernelSupportMode::Stable => {
            validate_observed_sample_conditions_with_budget_and_cancellation(
                "ksg_local_mi_terms",
                cfg.support_contract,
                &[x, y],
                resource_budget,
                cancellation,
            )?;
        }
        #[cfg(feature = "experimental-hyperbolic")]
        KernelSupportMode::SmoothManifold => {
            validate_smooth_manifold_sample_conditions_with_budget_and_cancellation(
                "ksg_local_mi_terms",
                &[x, y],
                resource_budget,
                cancellation,
            )?;
        }
    }
    cancellation.check("ksg_local_mi_terms", 0, n)?;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n)?;

    // Typically faster exact Chebyshev kd-tree path (kdtree.rs) — identical
    // outputs to the brute scan (same distance fold, same total_cmp k-th
    // value, same inclusive counts on the strict radius). Queries remain
    // linear in the worst case. A selected tree backend never silently falls back to an
    // unbounded brute-force job: build failure is returned to the caller.
    if backend.use_tree(cfg.kernel_metric, n, joint_dims) {
        let joint =
            KdTree::build_with_budget_and_cancellation(&[x, y], resource_budget, cancellation)?;
        let tx = KdTree::build_with_budget_and_cancellation(&[x], resource_budget, cancellation)?;
        let ty = KdTree::build_with_budget_and_cancellation(&[y], resource_budget, cancellation)?;
        return map_index_ordered(n, |i| {
            cancellation.check("ksg_local_mi_terms", i, n)?;
            let mut q = try_vec_with_capacity(
                "ksg_local_mi_terms joint query",
                joint_dims,
                ResourceBudget::default(),
            )?;
            concat_row_into(&[x, y], i, &mut q);
            let eps_raw = joint.kth_distance_with_cancellation(&q, k, i as u32, cancellation)?;
            if eps_raw == 0.0 {
                return Err(PidError::NumericalInstability {
                    context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                });
            }
            let (interior_count, boundary_count) = joint
                .kth_neighbor_shell_counts_with_cancellation(&q, eps_raw, i as u32, cancellation)?;
            validate_kth_neighbor_shell(
                "ksg_local_mi_terms",
                i,
                k,
                eps_raw,
                interior_count,
                boundary_count,
            )?;
            let eps = strict_radius(eps_raw);
            let nx = tx.count_within_with_cancellation(x.row(i), eps, i as u32, cancellation)?;
            let ny = ty.count_within_with_cancellation(y.row(i), eps, i as u32, cancellation)?;
            Ok(KsgLocalDiagnostic {
                term_nats: ksg_local_digamma_term(psi_k, psi_n, psi_int[nx + 1], psi_int[ny + 1]),
                joint_radius: eps_raw,
                x_count: nx,
                y_count: ny,
            })
        });
    }

    map_index_ordered(n, |i| {
        cancellation.check("ksg_local_mi_terms", i, n)?;
        let mut scratch = try_vec_with_capacity(
            "ksg_local_mi_terms distance scratch",
            n.saturating_sub(1),
            ResourceBudget::default(),
        )?;
        let xi = x.row(i);
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let dx = cfg.kernel_metric.checked_distance_with_cancellation(
                xi,
                x.row(j),
                "ksg_local_mi_terms: x distance",
                CancellationProgress::new("ksg_local_mi_terms", i, n),
                cancellation,
            )?;
            let dy = cfg.kernel_metric.checked_distance_with_cancellation(
                yi,
                y.row(j),
                "ksg_local_mi_terms: y distance",
                CancellationProgress::new("ksg_local_mi_terms", i, n),
                cancellation,
            )?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
            if j.is_multiple_of(1024) {
                cancellation.check("ksg_local_mi_terms", i, n)?;
            }
        }

        let kth = k - 1;
        cancellation.check("ksg_local_mi_terms", i, n)?;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        cancellation.check("ksg_local_mi_terms", i, n)?;
        let eps_raw = scratch[kth].joint;
        // Strict inequality for marginal counts.
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(KsgLocalDiagnostic {
            term_nats: ksg_local_digamma_term(psi_k, psi_n, psi_int[nx + 1], psi_int[ny + 1]),
            joint_radius: eps_raw,
            x_count: nx,
            y_count: ny,
        })
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
fn validate_ksg_pair_structure(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<()> {
    let kernel_config = KernelKsgConfig::stable(cfg);
    validate_ksg_pair_structure_with_kernel(context, x, y, &kernel_config)
}

fn validate_ksg_pair_structure_with_kernel(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KernelKsgConfig,
) -> PidResult<()> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if x.ncols() == 0 || y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "x and y must have at least 1 column",
        });
    }
    #[cfg(feature = "experimental-hyperbolic")]
    if cfg.kernel_metric.is_hyperbolic() && (x.ncols() < 2 || y.ncols() < 2) {
        return Err(PidError::InvalidConfig {
            context,
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    let n = x.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    match cfg.kernel_support_mode {
        KernelSupportMode::Stable => {
            validate_support_contract(context, cfg.support_contract, cfg.metric)
        }
        #[cfg(feature = "experimental-hyperbolic")]
        KernelSupportMode::SmoothManifold => Ok(()),
    }
}

/// KSG local MI terms when the "X" variable is treated as a concatenation of multiple blocks.
///
/// With `Metric::Chebyshev`, treating the concatenation as a max-over-blocks distance is
/// equivalent to explicitly concatenating the vectors, but avoids allocating an `(n×(d1+d2+...))`
/// temporary matrix.
#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_xblocks_resource_estimate(
    x_blocks: &[MatRef<'_>],
    y: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let x_dims = x_blocks.iter().try_fold(0usize, |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })
    })?;
    let joint_dims = x_dims
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let n = y.nrows();
    let pairs = (n as u128)
        .checked_mul(n.saturating_sub(1) as u128)
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let base_bytes = (n as u128)
        .checked_mul(
            (joint_dims as u128)
                .checked_mul(4)
                .and_then(|value| value.checked_add(64))
                .ok_or(PidError::SizeOverflow {
                    operation: "ksg_local_mi_terms_xblocks",
                })?,
        )
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let log_n = if n <= 1 {
        1u128
    } else {
        (usize::BITS - (n - 1).leading_zeros()) as u128
    };
    let support_peak_bytes = (n as u128)
        .checked_mul(joint_dims as u128)
        .and_then(|value| value.checked_mul(2 * std::mem::size_of::<u64>() as u128))
        .and_then(|value| {
            value.checked_add((n as u128).checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(
                (joint_dims as u128)
                    .checked_mul(std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    #[cfg(feature = "parallel")]
    let parallel_bytes = {
        let threads = effective_thread_count(max_threads, n) as u128;
        threads
            .checked_mul(WORKER_STACK_BYTES as u128)
            .and_then(|value| {
                value.checked_add(
                    threads
                        .checked_mul(n as u128)?
                        .checked_mul(std::mem::size_of::<DistPair>() as u128)?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })?
    };
    #[cfg(not(feature = "parallel"))]
    let parallel_bytes = {
        // Thread requests are semantically inert in serial builds, but retaining the parameter
        // keeps the preflight API identical across feature sets.
        let _ = max_threads;
        0
    };
    let operations_hint = pairs
        .checked_mul(joint_dims as u128)
        .and_then(|value| value.checked_mul(6))
        .and_then(|value| {
            value.checked_add(
                (n as u128)
                    .checked_mul(joint_dims as u128)?
                    .checked_mul(log_n)?
                    .checked_mul(2)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: base_bytes
            .checked_add(parallel_bytes)
            .map(|value| value.max(support_peak_bytes))
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })?,
        pairwise_distances: pairs,
        operations_hint,
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_local_mi_terms_xblocks_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let threads = effective_thread_count(budget.max_threads, y.nrows());
    with_thread_budget(threads, || {
        ksg_local_mi_terms_xblocks_backend_with_budget(x_blocks, y, cfg, NnBackend::Auto, budget)
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
#[cfg(test)]
pub(crate) fn ksg_local_mi_terms_xblocks_backend<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_xblocks_backend_with_budget(
        x_blocks,
        y,
        cfg,
        backend,
        ResourceBudget::default(),
    )
}

#[cfg(any(feature = "experimental-continuous", test))]
fn ksg_local_mi_terms_xblocks_backend_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    backend: NnBackend,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    if x_blocks.is_empty() {
        return Err(PidError::NotImplemented {
            feature: "ksg_local_mi_terms_xblocks with empty x_blocks",
        });
    }
    if y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "y must have at least 1 column",
        });
    }
    let n = y.nrows();
    for b in x_blocks {
        if b.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "ksg_local_mi_terms_xblocks",
                left_rows: n,
                right_rows: b.nrows(),
            });
        }
        if b.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: "ksg_local_mi_terms_xblocks",
                message: "x blocks must have at least 1 column",
            });
        }
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }

    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    // The max-over-blocks distance equals true concatenation only under L∞/Chebyshev
    // (max(max_b d_b, d_y) == d over the concatenated vector). For any other metric it
    // silently computes a *different* quantity, so reject it rather than mislabel the
    // result — matching the gating in `isx_redundancy` and `pid3_isx`.
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "max-over-blocks concatenation distance is exact only for Metric::Chebyshev (L∞); other metrics are research-gated",
        });
    }
    let x_dims = x_blocks.iter().try_fold(0usize, |total, block| {
        total
            .checked_add(block.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: "ksg_local_mi_terms_xblocks",
            })
    })?;
    let joint_dims = x_dims
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    budget.check(
        "ksg_local_mi_terms_xblocks",
        ksg_xblocks_resource_estimate(x_blocks, y, budget.max_threads)?,
    )?;
    validate_support_contract(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        cfg.metric,
    )?;
    let block_count = x_blocks
        .len()
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: "ksg_local_mi_terms_xblocks",
        })?;
    let mut support_inputs = try_vec_with_capacity(
        "ksg_local_mi_terms_xblocks support inputs",
        block_count,
        budget,
    )?;
    support_inputs.extend_from_slice(x_blocks);
    support_inputs.push(y);
    validate_observed_sample_conditions_with_budget(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        &support_inputs,
        budget,
    )?;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n)?;

    // Typically faster exact tree path (see ksg_local_mi_terms_backend). The
    // metric is already gated to Chebyshev above, where max-over-blocks equals
    // the concatenated-space distance. Worst-case queries are still linear.
    if backend.use_tree(cfg.metric.into(), n, joint_dims) {
        let mut joint_blocks = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks tree blocks",
            block_count,
            budget,
        )?;
        joint_blocks.extend_from_slice(x_blocks);
        joint_blocks.push(y);
        let joint = KdTree::build_with_budget(&joint_blocks, budget)?;
        let tx = KdTree::build_with_budget(x_blocks, budget)?;
        let ty = KdTree::build_with_budget(&[y], budget)?;
        return map_index_ordered(n, |i| {
            let mut q = try_vec_with_capacity(
                "ksg_local_mi_terms_xblocks joint query",
                joint_dims,
                budget,
            )?;
            concat_row_into(&joint_blocks, i, &mut q);
            let eps_raw = joint.kth_distance(&q, k, i as u32)?;
            if eps_raw == 0.0 {
                return Err(PidError::NumericalInstability {
                        context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                    });
            }
            let (interior_count, boundary_count) =
                joint.kth_neighbor_shell_counts(&q, eps_raw, i as u32);
            validate_kth_neighbor_shell(
                "ksg_local_mi_terms_xblocks",
                i,
                k,
                eps_raw,
                interior_count,
                boundary_count,
            )?;
            let eps = strict_radius(eps_raw);
            let mut qx =
                try_vec_with_capacity("ksg_local_mi_terms_xblocks source query", x_dims, budget)?;
            concat_row_into(x_blocks, i, &mut qx);
            let nx = tx.count_within(&qx, eps, i as u32);
            let ny = ty.count_within(y.row(i), eps, i as u32);
            Ok(ksg_local_digamma_term(
                psi_k,
                psi_n,
                psi_int[nx + 1],
                psi_int[ny + 1],
            ))
        });
    }

    map_index_ordered(n, |i| {
        let mut scratch = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks distance scratch",
            n.saturating_sub(1),
            budget,
        )?;
        let mut x_rows_i = try_vec_with_capacity(
            "ksg_local_mi_terms_xblocks source rows",
            x_blocks.len(),
            budget,
        )?;
        for b in x_blocks {
            x_rows_i.push(b.row(i));
        }
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let mut dx = 0.0f64;
            for (b_idx, b) in x_blocks.iter().enumerate() {
                dx = dx.max(cfg.metric.checked_distance(
                    x_rows_i[b_idx],
                    b.row(j),
                    "ksg_local_mi_terms_xblocks: x distance",
                )?);
            }
            let dy = cfg.metric.checked_distance(
                yi,
                y.row(j),
                "ksg_local_mi_terms_xblocks: y distance",
            )?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms_xblocks",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(ksg_local_digamma_term(
            psi_k,
            psi_n,
            psi_int[nx + 1],
            psi_int[ny + 1],
        ))
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_xblocks_with_budget<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let local = ksg_local_mi_terms_xblocks_with_budget(x_blocks, y, cfg, budget)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_concat_xy(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    ksg_mi_concat_xy_with_budget(x, y, t, cfg, ResourceBudget::default())
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn ksg_mi_concat_xy_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    ksg_mi_xblocks_with_budget(&[x, y], t, cfg, budget)
}

#[cfg(test)]
mod tests {
    use super::{ksg_mi, ksg_mi_concat_xy, KsgConfig};
    use crate::matrix::{concat_horiz, MatRef};

    #[test]
    fn concat_xy_matches_explicit_concatenation_for_chebyshev() {
        // For Chebyshev/L∞, computing distance as max-over-blocks is equivalent to explicit
        // concatenation. This test guards the allocation-avoidance optimization.
        let n = 40;
        let d1 = 3;
        let d2 = 2;
        let dt = 1;

        let mut state = 0xC011_CAFE_D15C_A11Eu64;
        let mut next = || {
            state ^= state >> 12;
            state ^= state << 25;
            state ^= state >> 27;
            (state.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        };
        let mut x = Vec::with_capacity(n * d1);
        let mut y = Vec::with_capacity(n * d2);
        let mut t = Vec::with_capacity(n * dt);
        for _ in 0..n {
            for _ in 0..d1 {
                x.push(next());
            }
            for _ in 0..d2 {
                y.push(next());
            }
            t.push(next());
        }

        let x = MatRef::new(&x, n, d1).unwrap();
        let y = MatRef::new(&y, n, d2).unwrap();
        let t = MatRef::new(&t, n, dt).unwrap();
        let cfg = KsgConfig::assume_regular_full_dimensional();

        let mi_blocks = ksg_mi_concat_xy(x, y, t, &cfg).unwrap();
        let xy = concat_horiz(x, y).unwrap();
        let mi_explicit = ksg_mi(xy.as_ref(), t, &cfg).unwrap();

        assert!(
            (mi_blocks - mi_explicit).abs() < 1e-12,
            "mi_blocks={mi_blocks} mi_explicit={mi_explicit}"
        );
    }
}

#[cfg(test)]
mod kdtree_parity_tests {
    use super::*;
    use crate::error::PidError;
    use crate::matrix::MatOwned;

    struct Rng(u64);
    impl Rng {
        fn next_f64(&mut self) -> f64 {
            let mut x = self.0;
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            self.0 = x;
            (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        }
    }

    fn mat(rng: &mut Rng, n: usize, d: usize, quantize: bool) -> MatOwned {
        let mut data = Vec::with_capacity(n * d);
        for _ in 0..n * d {
            let v = rng.next_f64();
            data.push(if quantize {
                (v * 16.0).round() / 16.0
            } else {
                v
            });
        }
        MatOwned::new(data, n, d).unwrap()
    }

    fn cfg(k: usize) -> KsgConfig {
        KsgConfig {
            k,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: crate::support::SupportContract::AssumeRegularFullDimensional {
                boundary: crate::support::BoundaryModel::Unknown,
                density_regular: true,
                finite_information: true,
            },
        }
    }

    fn shell_error_signature(
        result: PidResult<Vec<f64>>,
    ) -> (&'static str, usize, usize, u64, usize, usize) {
        match result.unwrap_err() {
            PidError::AmbiguousKthNeighborShell {
                context,
                query_index,
                k,
                radius,
                interior_count,
                boundary_count,
            } => (
                context,
                query_index,
                k,
                radius.to_bits(),
                interior_count,
                boundary_count,
            ),
            error => panic!("expected ambiguous k-th-neighbor shell, got {error:?}"),
        }
    }

    #[test]
    fn local_mi_terms_tree_is_bit_identical_to_brute() {
        // Below and above the Auto threshold; smooth and tie-heavy data.
        for (n, dx, dy, k, quantize) in [
            (64, 1, 1, 4, false),
            (300, 1, 1, 4, false),
            (300, 2, 1, 3, true),
            (200, 3, 2, 7, true),
        ] {
            let mut rng = Rng(0x5EED ^ ((n as u64) << 16) ^ ((dx as u64) << 8) ^ k as u64);
            let x = mat(&mut rng, n, dx, quantize);
            let y = mat(&mut rng, n, dy, quantize);
            let c = cfg(k);
            let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
            let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);
            match (brute, tree) {
                (Ok(b), Ok(t)) => {
                    assert_eq!(b.len(), t.len());
                    for (i, (bb, tt)) in b.iter().zip(&t).enumerate() {
                        assert_eq!(
                            bb.to_bits(),
                            tt.to_bits(),
                            "term {i} differs (n={n} dx={dx} dy={dy} k={k} q={quantize})"
                        );
                    }
                }
                // Tie-heavy data may legitimately collapse the radius: both
                // paths must then fail identically.
                (Err(_), Err(_)) => {}
                (b, t) => panic!("backend disagreement: brute={b:?} tree={t:?}"),
            }
        }
    }

    #[test]
    fn xblocks_tree_is_bit_identical_to_brute() {
        let mut rng = Rng(0xB10C5);
        let n = 260;
        let x1 = mat(&mut rng, n, 2, false);
        let x2 = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let blocks = [x1.as_ref(), x2.as_ref()];
        let brute =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::Brute).unwrap();
        let tree =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::KdTree).unwrap();
        for (i, (bb, tt)) in brute.iter().zip(&tree).enumerate() {
            assert_eq!(bb.to_bits(), tt.to_bits(), "xblocks term {i} differs");
        }
    }

    #[test]
    fn positive_outer_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [0.5, 1, 1, 3], so the outer shell contains two points.
        let x = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn positive_left_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [1, 1, 2], so fewer than k-1 points lie strictly inside the selected radius.
        let x = MatOwned::new(vec![0.0, 1.0, 0.3, 2.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.2, 1.0, 2.0], 4, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 0, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn xblocks_positive_shell_tie_errors_identically_on_both_backends() {
        let x1 = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let x2 = MatOwned::new(vec![0.0, 0.25, 0.75, 0.35, 2.5], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let blocks = [x1.as_ref(), x2.as_ref()];
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms_xblocks", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn duplicate_rows_error_identically_on_both_backends() {
        // All-identical rows collapse every kNN radius; both backends must
        // fail (radius guard), not silently disagree.
        let n = 150;
        let x = MatOwned::new(vec![0.25; n], n, 1).unwrap();
        let y = MatOwned::new(vec![0.75; n], n, 1).unwrap();
        let c = cfg(3);
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).is_err());
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).is_err());
    }

    #[test]
    fn overflowing_coordinate_span_errors_identically_on_both_backends() {
        let x = MatOwned::new(vec![-f64::MAX, f64::MAX, 0.0, 1.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let c = cfg(1);

        let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
        let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);

        assert!(brute.is_err());
        assert!(tree.is_err());
    }

    #[test]
    #[ignore = "manual benchmark: cargo test -p pid-core --release kdtree_speedup -- --ignored --nocapture"]
    fn kdtree_speedup_smoke() {
        let mut rng = Rng(0xBEEF);
        let n = 4000;
        let x = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let t0 = std::time::Instant::now();
        let brute =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).unwrap();
        let t_brute = t0.elapsed();
        let t1 = std::time::Instant::now();
        let tree =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).unwrap();
        let t_tree = t1.elapsed();
        assert_eq!(brute.len(), tree.len());
        println!(
            "n={n}: brute {t_brute:?} vs kd-tree {t_tree:?} ({:.1}x)",
            t_brute.as_secs_f64() / t_tree.as_secs_f64()
        );
    }
}
