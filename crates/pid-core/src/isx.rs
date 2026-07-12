use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::ksg::{
    count_quantiles, effective_thread_count, hash_matrix, hash_text, value_quantiles,
    KsgCountQuantiles, KsgValueQuantiles,
};
#[cfg(feature = "experimental-heuristics")]
use crate::ksg::{
    ksg_local_mi_terms_with_budget, ksg_local_mi_terms_xblocks_with_budget, KsgConfig,
    NegativeHandling,
};
use crate::matrix::MatRef;
use crate::metric::Metric;
#[cfg(feature = "experimental-heuristics")]
use crate::nn::{count_neighbors_within, kth_neighbor_distance_joint_max_with_scratch};
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
#[cfg(feature = "parallel")]
use crate::par::WORKER_STACK_BYTES;
use crate::report::{
    Assumption, AssumptionLedgerEntry, AssumptionState, EstimandIdentity, InformationUnit,
    ProvenanceHashes, ScientificStatus, WarningCode,
};
#[cfg(feature = "experimental-heuristics")]
use crate::resource::try_vec_filled;
use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::{compensated_sum, digamma, digamma_int_table};
use crate::support::{
    validate_observed_sample_conditions_with_budget, validate_support_contract,
    CoordinateCardinalityDiagnostics, SupportContract,
};

#[derive(Clone, Copy)]
struct DistIsx2 {
    joint: f64,
    dt: f64,
    ds: f64,
    ds1: f64,
    ds2: f64,
}

#[derive(Clone, Copy)]
pub(crate) struct IsxLocalDiagnostic {
    pub(crate) term_nats: f64,
    joint_radius: f64,
    source_union_count: usize,
    target_count: usize,
    source1_count: usize,
    source2_count: usize,
    overlap_count: usize,
    source1_half_count: usize,
    source2_half_count: usize,
    overlap_half_count: usize,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum IsxMethod {
    /// Paper-faithful kNN estimator for continuous shared-exclusions redundancy from:
    /// Ehrlich et al. (2024), Phys. Rev. E 110, 014115 (arXiv:2311.06373v3).
    ///
    /// Implements the bivariate redundancy `I^sx_∩(S1,S2;T)` via the KSG-style estimator
    /// (Appendix H, Algorithms 3–6) under the L∞/Chebyshev metric:
    ///
    /// I^sx_∩ = ψ(k) + ψ(n) - ⟨ ψ(n_α(i)) + ψ(n_T(i)) ⟩_i
    ///
    /// where:
    /// - ε_i is the kNN radius in the joint (source-disjunction, target) space,
    /// - n_α(i) counts neighbors in the *source disjunction* within ε_i,
    /// - n_T(i) counts neighbors in target space within ε_i.
    ///
    /// Note: This is the default method for `IsxConfig`.
    EhrlichKsg,
    /// Experimental heuristic sketch estimator.
    ///
    /// Provided as an explicit, clearly-labelled baseline only; it should be treated as
    /// untrusted until validated against synthetic systems with known information quantities.
    #[cfg(feature = "experimental-heuristics")]
    HeuristicSketch,
    /// Approximate shared-exclusions redundancy by taking the samplewise minimum
    /// of KSG local MI terms for (S1,T) and (S2,T), then averaging.
    #[cfg(feature = "experimental-heuristics")]
    LocalMinKsg,
    /// Experimental **unweighted inclusion–exclusion heuristic** over pointwise KSG local-MI
    /// terms:
    ///
    /// r(s1,s2;t) = log( exp(i(s1;t)) + exp(i(s2;t)) - exp(i(s1,s2;t)) )
    ///
    /// **This is NOT the shared-exclusions disjunction identity.** The true forms are:
    /// - discrete (Makkeh–Gutknecht–Wibral 2021):
    ///   `i^sx = log[(p(s1)e^{i1} + p(s2)e^{i2} − p(s1,s2)e^{i12}) / (p(s1)+p(s2)−p(s1,s2))]`
    ///   (probability-weighted);
    /// - continuous limit (Ehrlich et al. 2024, Def. 2; re-derived in
    ///   `tests/sxpid_gaussian_oracle.rs`):
    ///   `i^sx = log[w1·e^{i1} + w2·e^{i2}]` with density weights
    ///   `w_a = f_{S_a}(s_a) / (f_{S1}(s1) + f_{S2}(s2))` and **no** joint term (the discrete
    ///   joint-term weight `p(s1,s2)` vanishes in the continuum).
    ///
    /// This variant sets all weights to 1 and retains a full-weight joint term, so it estimates
    /// a *different* functional and does not converge to `I^sx_∩` as estimation error → 0; its
    /// log argument can also be non-positive (surfacing as `NumericalInstability`), whereas the
    /// true `i^sx` argument `P(∪|t)/P(∪)` is always positive. Baseline/diagnostic use only.
    #[cfg(feature = "experimental-heuristics")]
    DisjunctionFromLocalMi,
}

#[derive(Debug, Clone, Serialize)]
pub struct IsxConfig {
    pub k: usize,
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Strict counts use the floating-point predecessor of the raw kNN radius. A material
    /// subtraction would erode the neighborhood and estimate a different functional.
    pub tie_epsilon: f64,
    pub method: IsxMethod,
    /// Population-support assertion for every marginal and joint law used by this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. The current
    /// continuous shared-exclusions estimators accept only
    /// [`SupportContract::AssumeRegularFullDimensional`].
    pub support_contract: SupportContract,
}

/// Caller-declared source gauges, preprocessing, sampling, and split provenance for ISX.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct IsxProvenance {
    source1_gauge_description: String,
    source2_gauge_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
    sampling_model_description: Option<String>,
    training_split_id: Option<String>,
    evaluation_split_id: Option<String>,
}

impl IsxProvenance {
    pub fn new(
        source1_gauge_description: impl AsRef<str>,
        source2_gauge_description: impl AsRef<str>,
        target_preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
        sampling_model_description: impl AsRef<str>,
        training_split_id: Option<String>,
        evaluation_split_id: Option<String>,
    ) -> PidResult<Self> {
        let source1_gauge_description = source1_gauge_description.as_ref();
        let source2_gauge_description = source2_gauge_description.as_ref();
        let target_preprocessing_description = target_preprocessing_description.as_ref();
        let observation_model_description = observation_model_description.as_ref();
        let sampling_model_description = sampling_model_description.as_ref();
        for value in [
            source1_gauge_description,
            source2_gauge_description,
            target_preprocessing_description,
            observation_model_description,
            sampling_model_description,
        ] {
            if value.trim().is_empty() || value.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "IsxProvenance::new",
                    message: "provenance descriptions must be nonempty and at most 16 KiB",
                });
            }
        }
        for value in [training_split_id.as_deref(), evaluation_split_id.as_deref()]
            .into_iter()
            .flatten()
        {
            if value.is_empty() || value.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "IsxProvenance::new",
                    message: "split identifiers must be nonempty and at most 16 KiB",
                });
            }
        }
        Ok(Self {
            source1_gauge_description: try_owned_text(
                "IsxProvenance::new source1 gauge",
                source1_gauge_description,
            )?,
            source2_gauge_description: try_owned_text(
                "IsxProvenance::new source2 gauge",
                source2_gauge_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "IsxProvenance::new target preprocessing",
                target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "IsxProvenance::new observation model",
                observation_model_description,
            )?,
            sampling_model_description: Some(try_owned_text(
                "IsxProvenance::new sampling model",
                sampling_model_description,
            )?),
            training_split_id,
            evaluation_split_id,
        })
    }

    pub fn source1_gauge_description(&self) -> &str {
        &self.source1_gauge_description
    }

    pub fn source2_gauge_description(&self) -> &str {
        &self.source2_gauge_description
    }

    pub fn target_preprocessing_description(&self) -> &str {
        &self.target_preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
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
            Some(self.source1_gauge_description.as_str()),
            Some(self.source2_gauge_description.as_str()),
            Some(self.target_preprocessing_description.as_str()),
            Some(self.observation_model_description.as_str()),
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
                    operation: "ISX provenance",
                })
        })
    }

    fn try_clone_for_report(&self) -> PidResult<Self> {
        Ok(Self {
            source1_gauge_description: try_owned_text(
                "ISX report provenance",
                &self.source1_gauge_description,
            )?,
            source2_gauge_description: try_owned_text(
                "ISX report provenance",
                &self.source2_gauge_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "ISX report provenance",
                &self.target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "ISX report provenance",
                &self.observation_model_description,
            )?,
            sampling_model_description: self
                .sampling_model_description
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
            training_split_id: self
                .training_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
            evaluation_split_id: self
                .evaluation_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report provenance", value))
                .transpose()?,
        })
    }

    pub(crate) fn new_with_optional_sampling(
        source1_gauge_description: &str,
        source2_gauge_description: &str,
        target_preprocessing_description: &str,
        observation_model_description: &str,
        sampling_model_description: Option<&str>,
        training_split_id: Option<&str>,
        evaluation_split_id: Option<&str>,
    ) -> PidResult<Self> {
        let explicit_sampling = sampling_model_description.unwrap_or("sampling model undeclared");
        let mut provenance = Self::new(
            source1_gauge_description,
            source2_gauge_description,
            target_preprocessing_description,
            observation_model_description,
            explicit_sampling,
            training_split_id
                .map(|value| try_owned_text("ISX training split", value))
                .transpose()?,
            evaluation_split_id
                .map(|value| try_owned_text("ISX evaluation split", value))
                .transpose()?,
        )?;
        if sampling_model_description.is_none() {
            provenance.sampling_model_description = None;
        }
        Ok(provenance)
    }
}

fn try_owned_text(operation: &'static str, value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Multi-scale branch/overlap and local-term summary for the ISX neighborhoods actually used.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IsxLocalDiagnosticsSummary {
    pub joint_radius: KsgValueQuantiles,
    pub source_union_count: KsgCountQuantiles,
    pub target_count: KsgCountQuantiles,
    pub source1_count: KsgCountQuantiles,
    pub source2_count: KsgCountQuantiles,
    pub overlap_count: KsgCountQuantiles,
    pub overlap_half_radius_count: KsgCountQuantiles,
    pub overlap_ratio: KsgValueQuantiles,
    pub overlap_half_radius_ratio: KsgValueQuantiles,
    pub source1_scaling_slope: Option<KsgValueQuantiles>,
    pub source2_scaling_slope: Option<KsgValueQuantiles>,
    pub undefined_source1_slopes: usize,
    pub undefined_source2_slopes: usize,
    pub local_redundancy_nats: KsgValueQuantiles,
}

/// Restricted-domain experimental continuous shared-exclusions report.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IsxReport {
    pub estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub source_dimensions: [usize; 2],
    pub target_dimension: usize,
    pub estimand: EstimandIdentity,
    pub scientific_status: ScientificStatus,
    pub support_contract: SupportContract,
    pub provenance: IsxProvenance,
    pub provenance_hashes: ProvenanceHashes,
    pub assumption_ledger: Vec<AssumptionLedgerEntry>,
    pub local_diagnostics: IsxLocalDiagnosticsSummary,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub warnings: Vec<WarningCode>,
}

pub(crate) struct IsxReportComputation {
    pub(crate) report: IsxReport,
    pub(crate) local: Vec<IsxLocalDiagnostic>,
}

impl Default for IsxConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            method: IsxMethod::EhrlichKsg,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl IsxConfig {
    /// Construct the paper-faithful Chebyshev configuration with an explicit caller assertion that
    /// every required marginal and joint law is full-dimensional and absolutely continuous.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            support_contract: SupportContract::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

/// Continuous shared-exclusions redundancy I^sx_∩(S1,S2;T).
///
/// This is the core Wibral-group PID quantity (Makkeh et al. 2021; Ehrlich et al. 2024).
///
/// By default (`IsxMethod::EhrlichKsg`), this uses the paper-faithful KSG-style kNN estimator
/// for continuous variables (Ehrlich et al. 2024, Appendix H).
///
/// # Units
/// Returns redundancy in **nats** (natural log).
///
/// # Important: can be negative
/// `I^sx_∩` is a well-defined functional of the joint distribution, but it is **not guaranteed
/// to be non-negative** under all desiderata (see the PID inconsistency/impossibility results
/// discussed in Makkeh et al. 2021 and Matthias et al. 2025). Do not clamp this value to 0.
///
/// # Assumptions / failure modes (estimator-level)
/// The default estimator is kNN-based and inherits the usual kNN MI pathologies:
/// - The default support contract is unspecified and fails closed. Callers must explicitly assert
///   full-dimensional absolute continuity for every marginal and joint law used by the estimator.
///   Exact coordinate ties are incompatible with ideal i.i.d., unrounded continuous-sample
///   conditions but do not identify their cause or population support; all-unique finite
///   observations do not prove the model.
/// - Assumes i.i.d. samples from a continuous distribution; trajectory autocorrelation and
///   quantization/duplicates can collapse the kNN radius or create an ambiguous positive boundary.
///   Adding jitter changes the estimated distribution and is appropriate only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis; otherwise
///   use a discrete, quantized, or mixed-support estimator.
/// - Can fail in high ambient/intrinsic dimension due to distance concentration.
/// - Can require prohibitive samples under strong dependence (very large true MI).
/// - Exact deterministic continuous maps have infinite MI and fall outside the estimator's domain.
///   An explicit observation-noise model defines a different, finite-MI distribution; otherwise
///   use a suitable discrete/mixed estimator.
/// - The two source matrices must have the same ambient column count. The small-ball
///   disjunction compares their raw neighborhood radii, whose asymptotic scaling depends on
///   dimension; unequal-dimensional source balls therefore do not share the estimator's
///   required reference scaling. Equal ambient dimensions are only a necessary guard: they do
///   **not** prove equal intrinsic dimensions, compatible reference measures, or comparable
///   neighborhood geometry.
/// - Relative source units and preprocessing define the comparison between source neighborhoods
///   and are part of the continuous `I^sx_∩` estimand. Record the full scheme and do not compare
///   or pool results across different source scalings/projections.
///
/// Other `IsxMethod` variants are included only as explicit experimental baselines / cross-checks
/// against the default estimator, and should not be trusted without validation.
pub(crate) fn isx_redundancy(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    isx_redundancy_with_budget(s1, s2, t, cfg, ResourceBudget::default())
}

pub(crate) fn isx_redundancy_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    const CONTEXT: &str = "isx_redundancy";
    validate_isx_structure(CONTEXT, s1, s2, t, cfg)?;
    validate_support_contract(CONTEXT, cfg.support_contract, cfg.metric)?;
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let estimate = isx_resource_estimate_for_method(s1, s2, t, cfg.method, threads)?;
    budget.check(CONTEXT, estimate)?;
    validate_observed_sample_conditions_with_budget(
        CONTEXT,
        cfg.support_contract,
        &[s1, s2, t],
        budget,
    )?;
    match cfg.method {
        IsxMethod::EhrlichKsg => crate::par::with_thread_budget(threads, || {
            isx_redundancy_ehrlich_ksg(s1, s2, t, cfg, budget)
        }),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::HeuristicSketch => isx_redundancy_heuristic_sketch(s1, s2, t, cfg, budget),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::LocalMinKsg => isx_redundancy_local_min_ksg(s1, s2, t, cfg, budget),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::DisjunctionFromLocalMi => {
            isx_redundancy_disjunction_from_local_mi(s1, s2, t, cfg, budget)
        }
    }
}

fn validate_isx_structure(
    context: &'static str,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<()> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: s1.nrows(),
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    if s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "inputs must have at least 1 column",
        });
    }
    if s1.ncols() != s2.ncols() {
        return Err(PidError::SourceDimensionMismatch {
            context,
            left_cols: s1.ncols(),
            right_cols: s2.ncols(),
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.k == 0 || s1.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: s1.nrows(),
        });
    }
    // The paper-faithful continuous `I^sx_∩` implementation is restricted to its documented
    // L∞/Chebyshev convention. This is metric-domain validation, not a general consistency claim.
    // Do not silently “swap the geometry” (e.g., hyperbolic distances) and still call it `I^sx_∩`.
    if cfg.method == IsxMethod::EhrlichKsg && cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message:
                "IsxMethod::EhrlichKsg is restricted to its paper-faithful Metric::Chebyshev (L∞) convention; other metrics are research-gated",
        });
    }
    Ok(())
}

/// Compute the restricted-domain paper-faithful estimator with neighborhood, scaling, overlap,
/// assumption, provenance, and resource diagnostics attached.
pub fn isx_redundancy_report(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    config: &IsxConfig,
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<IsxReport> {
    Ok(isx_redundancy_report_with_local_terms(s1, s2, target, config, provenance, budget)?.report)
}

pub(crate) fn isx_redundancy_report_with_local_terms(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    config: &IsxConfig,
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<IsxReportComputation> {
    validate_isx_structure("isx_redundancy_report", s1, s2, target, config)?;
    if config.method != IsxMethod::EhrlichKsg {
        return Err(PidError::InvalidConfig {
            context: "isx_redundancy_report",
            message: "report-first ISX is defined only for the paper-faithful EhrlichKsg method",
        });
    }
    validate_support_contract(
        "isx_redundancy_report",
        config.support_contract,
        config.metric,
    )?;
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let resource_estimate = isx_report_resource_estimate(s1, s2, target, provenance, threads)?;
    budget.check("isx_redundancy_report", resource_estimate)?;
    validate_observed_sample_conditions_with_budget(
        "isx_redundancy_report",
        config.support_contract,
        &[s1, s2, target],
        budget,
    )?;
    let local = crate::par::with_thread_budget(threads, || {
        isx_local_diagnostics(s1, s2, target, config, budget)
    })?;
    let estimate_nats =
        compensated_sum(local.iter().map(|term| term.term_nats)) / local.len() as f64;
    let local_diagnostics = summarize_isx_local(&local, budget)?;
    let assumption_ledger = isx_assumption_ledger(provenance, budget)?;
    let combined_preprocessing = combined_preprocessing_description(provenance)?;
    let mut input_hashes_sha256 = try_vec_with_capacity("ISX report input hashes", 3, budget)?;
    input_hashes_sha256.extend([hash_matrix(s1), hash_matrix(s2), hash_matrix(target)]);
    let mut warnings = try_vec_with_capacity("ISX report warnings", 7, budget)?;
    warnings.extend([
        WarningCode::DiagnosticsDoNotProvePopulationAssumptions,
        WarningCode::ExperimentalEstimator,
        WarningCode::KTrajectoryNotEvaluated,
        WarningCode::SampleSizeTrajectoryNotEvaluated,
        WarningCode::TransformationSensitivityNotEvaluated,
        WarningCode::ObservationNoiseSensitivityNotEvaluated,
    ]);
    if provenance.sampling_model_description.is_none() {
        warnings.push(WarningCode::DependenceDiagnosticsNotEvaluated);
    }
    let report = IsxReport {
        estimate_nats,
        n_samples: s1.nrows(),
        k: config.k,
        source_dimensions: [s1.ncols(), s2.ncols()],
        target_dimension: target.ncols(),
        estimand: EstimandIdentity {
            family: "ehrlich-wibral-continuous-isx",
            definition_revision: "common-coordinate-radius-v1",
            estimator_revision: "strict-unique-shell-isx-v3",
            units: InformationUnit::Nats,
            metric: "chebyshev-common-coordinate-radius",
            source_gauge: Some("caller-declared-source-gauges"),
        },
        scientific_status: ScientificStatus::ExperimentalRestrictedDomain,
        support_contract: config.support_contract,
        provenance: provenance.try_clone_for_report()?,
        provenance_hashes: ProvenanceHashes {
            input_hashes_sha256,
            preprocessing_hash_sha256: hash_text(&combined_preprocessing),
            observation_model_hash_sha256: hash_text(provenance.observation_model_description()),
            training_split_id: provenance
                .training_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report split identity", value))
                .transpose()?,
            evaluation_split_id: provenance
                .evaluation_split_id
                .as_deref()
                .map(|value| try_owned_text("ISX report split identity", value))
                .transpose()?,
        },
        assumption_ledger,
        local_diagnostics,
        resource_estimate,
        resource_budget: budget,
        warnings,
    };
    Ok(IsxReportComputation { report, local })
}

/// Conservative peak-memory and pairwise-work estimate for report-first two-source ISX.
pub fn isx_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    isx_resource_estimate_for_threads(
        s1,
        s2,
        target,
        effective_thread_count(ResourceBudget::default().max_threads, s1.nrows()),
    )
}

/// ISX preflight including one scratch buffer and explicit stack reservation per active worker.
pub fn isx_resource_estimate_for_threads(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "isx_redundancy_report";
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    if s1.nrows() != s2.nrows() || s1.nrows() != target.nrows() {
        return Err(PidError::RowCountMismatch {
            context: OPERATION,
            left_rows: s1.nrows(),
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                target.nrows()
            },
        });
    }
    let n_usize = s1.nrows();
    let n = n_usize as u128;
    let dimensions = s1
        .ncols()
        .checked_add(s2.ncols())
        .and_then(|value| value.checked_add(target.ncols()))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })? as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let digamma_bytes = n
        .checked_add(1)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let local_bytes = n
        .checked_mul(std::mem::size_of::<IsxLocalDiagnostic>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let summary_bytes = n
        .checked_mul(
            6u128
                .checked_mul(std::mem::size_of::<f64>() as u128)
                .and_then(|value| {
                    value.checked_add(6u128.checked_mul(std::mem::size_of::<usize>() as u128)?)
                })
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let active_threads = effective_thread_count(max_threads, n_usize) as u128;
    let worker_scratch = active_threads
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_mul(std::mem::size_of::<DistIsx2>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(feature = "parallel")]
    let worker_stacks = active_threads
        .checked_mul(WORKER_STACK_BYTES as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let worker_stacks = 0;
    #[cfg(feature = "parallel")]
    let ordered_map_intermediate = n
        .checked_mul(std::mem::size_of::<PidResult<IsxLocalDiagnostic>>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    #[cfg(not(feature = "parallel"))]
    let ordered_map_intermediate = 0;
    let estimator_peak = digamma_bytes
        .checked_add(local_bytes)
        .and_then(|value| value.checked_add(ordered_map_intermediate))
        .and_then(|value| value.checked_add(worker_scratch))
        .and_then(|value| value.checked_add(worker_stacks))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let summary_peak = local_bytes
        .checked_add(summary_bytes)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let support_peak = [s1, s2, target]
        .into_iter()
        .map(continuous_cardinality_estimate)
        .try_fold(ResourceEstimate::ZERO, |peak, estimate| {
            let estimate = estimate?;
            Ok::<_, PidError>(ResourceEstimate {
                estimated_bytes: peak.estimated_bytes.max(estimate.estimated_bytes),
                pairwise_distances: 0,
                operations_hint: peak
                    .operations_hint
                    .checked_add(estimate.operations_hint)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?,
            })
        })?;
    let operations_hint = pairs
        .checked_mul(2)
        .and_then(|value| value.checked_mul(dimensions.checked_add(16)?))
        .and_then(|value| value.checked_add(support_peak.operations_hint))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: estimator_peak
            .max(summary_peak)
            .max(support_peak.estimated_bytes),
        pairwise_distances: pairs,
        operations_hint,
    })
}

/// Complete ISX report preflight including retained provenance, hashes, and metadata.
pub fn isx_report_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &IsxProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "isx_redundancy_report";
    let mut estimate = isx_resource_estimate_for_threads(s1, s2, target, max_threads)?;
    let retained = provenance
        .heap_bytes()?
        .checked_mul(2)
        .and_then(|value| {
            value.checked_add(
                provenance.source1_gauge_description.len() as u128
                    + provenance.source2_gauge_description.len() as u128
                    + provenance.target_preprocessing_description.len() as u128
                    + 27,
            )
        })
        .and_then(|value| value.checked_add(std::mem::size_of::<IsxReport>() as u128))
        .and_then(|value| value.checked_add(5 * 64))
        .and_then(|value| {
            value.checked_add(
                12u128.checked_mul(std::mem::size_of::<AssumptionLedgerEntry>() as u128)?,
            )
        })
        .and_then(|value| {
            value.checked_add(7u128.checked_mul(std::mem::size_of::<WarningCode>() as u128)?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    estimate.estimated_bytes =
        estimate
            .estimated_bytes
            .checked_add(retained)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    Ok(estimate)
}

fn continuous_cardinality_estimate(input: MatRef<'_>) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "ISX support cardinalities";
    let n = input.nrows() as u128;
    let dimensions = input.ncols() as u128;
    let coordinates = n.checked_mul(dimensions).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let log_n = if input.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (input.nrows() - 1).leading_zeros()) as u128
    };
    Ok(ResourceEstimate {
        estimated_bytes: coordinates
            .checked_mul(2 * std::mem::size_of::<u64>() as u128)
            .and_then(|value| {
                value.checked_add(n.checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
            })
            .and_then(|value| {
                value.checked_add(
                    dimensions.checked_mul(
                        std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128,
                    )?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
        pairwise_distances: 0,
        operations_hint: coordinates
            .checked_mul(log_n)
            .and_then(|value| value.checked_mul(2))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?,
    })
}

fn combined_preprocessing_description(provenance: &IsxProvenance) -> PidResult<String> {
    const PREFIX_BYTES: usize = "source1=; source2=; target=".len();
    let capacity = provenance
        .source1_gauge_description
        .len()
        .checked_add(provenance.source2_gauge_description.len())
        .and_then(|value| value.checked_add(provenance.target_preprocessing_description.len()))
        .and_then(|value| value.checked_add(PREFIX_BYTES))
        .ok_or(PidError::SizeOverflow {
            operation: "ISX preprocessing provenance",
        })?;
    let mut combined = String::new();
    combined
        .try_reserve_exact(capacity)
        .map_err(|_| PidError::AllocationFailed {
            operation: "ISX preprocessing provenance",
            requested_bytes: capacity as u128,
        })?;
    combined.push_str("source1=");
    combined.push_str(&provenance.source1_gauge_description);
    combined.push_str("; source2=");
    combined.push_str(&provenance.source2_gauge_description);
    combined.push_str("; target=");
    combined.push_str(&provenance.target_preprocessing_description);
    Ok(combined)
}

pub(crate) fn isx_resource_estimate_for_method(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    method: IsxMethod,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let base = isx_resource_estimate_for_threads(s1, s2, target, max_threads)?;
    match method {
        IsxMethod::EhrlichKsg => Ok(base),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::HeuristicSketch => scale_isx_work(base, target.nrows(), 5, 5),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::LocalMinKsg => scale_isx_work(base, target.nrows(), 2, 2),
        #[cfg(feature = "experimental-heuristics")]
        IsxMethod::DisjunctionFromLocalMi => scale_isx_work(base, target.nrows(), 3, 3),
    }
}

#[cfg(feature = "experimental-heuristics")]
fn scale_isx_work(
    base: ResourceEstimate,
    n: usize,
    passes: u128,
    retained_vectors: u128,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "experimental ISX heuristic";
    let retained_bytes = (n as u128)
        .checked_mul(retained_vectors)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: base.estimated_bytes.checked_add(retained_bytes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
        pairwise_distances: base.pairwise_distances.checked_mul(passes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
        operations_hint: base.operations_hint.checked_mul(passes).ok_or(
            PidError::SizeOverflow {
                operation: OPERATION,
            },
        )?,
    })
}

fn isx_redundancy_ehrlich_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let terms = isx_local_diagnostics(s1, s2, t, cfg, budget)?;
    let sum = compensated_sum(terms.iter().map(|term| term.term_nats));
    Ok(sum / terms.len() as f64)
}

fn isx_local_diagnostics(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<IsxLocalDiagnostic>> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_ehrlich_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // This is the bivariate antichain α = {{1},{2}}; the disjunction distance in source space is:
    // d_S_disj(i,j) = min( d(S1_i,S1_j), d(S2_i,S2_j) ).
    //
    // With Chebyshev/L∞ and a shared target ball, the joint disjunction distance is:
    // d_ST_disj(i,j) = max( d(T_i,T_j), d_S_disj(i,j) ).
    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n)?;

    // Per-point local term. Each point is independent and allocates its own scratch, so the
    // closure is pure and can run data-parallel. Results are collected **in index order** and
    // reduced with the same deterministic compensated summation in both paths, so the `parallel`
    // path is bit-for-bit identical to the serial path (see `map_index_ordered`).
    let local = |i: usize| -> PidResult<IsxLocalDiagnostic> {
        let mut scratch = try_vec_with_capacity(
            "ISX per-query distance scratch",
            n.saturating_sub(1),
            budget,
        )?;
        let s1i = s1.row(i);
        let s2i = s2.row(i);
        let ti = t.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let ds1 = cfg.metric.checked_distance(
                s1i,
                s1.row(j),
                "isx_redundancy_ehrlich_ksg: s1 distance",
            )?;
            let ds2 = cfg.metric.checked_distance(
                s2i,
                s2.row(j),
                "isx_redundancy_ehrlich_ksg: s2 distance",
            )?;
            let dt = cfg.metric.checked_distance(
                ti,
                t.row(j),
                "isx_redundancy_ehrlich_ksg: target distance",
            )?;
            let ds = ds1.min(ds2);
            scratch.push(DistIsx2 {
                joint: dt.max(ds),
                dt,
                ds,
                ds1,
                ds2,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_ehrlich_ksg: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "isx_redundancy_ehrlich_ksg",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        // Counts exclude self; the estimator needs counts including self.
        let mut n_t = 1usize;
        let mut n_alpha = 1usize;
        let mut n_s1 = 0usize;
        let mut n_s2 = 0usize;
        let mut n_overlap = 0usize;
        let mut n_s1_half = 0usize;
        let mut n_s2_half = 0usize;
        let mut n_overlap_half = 0usize;
        let half_radius = eps_raw * 0.5;
        for d in &scratch {
            if d.dt <= eps {
                n_t += 1;
            }
            if d.ds <= eps {
                n_alpha += 1;
            }
            let in_s1 = d.ds1 <= eps;
            let in_s2 = d.ds2 <= eps;
            n_s1 += usize::from(in_s1);
            n_s2 += usize::from(in_s2);
            n_overlap += usize::from(in_s1 && in_s2);
            let in_s1_half = d.ds1 < half_radius;
            let in_s2_half = d.ds2 < half_radius;
            n_s1_half += usize::from(in_s1_half);
            n_s2_half += usize::from(in_s2_half);
            n_overlap_half += usize::from(in_s1_half && in_s2_half);
        }

        Ok(IsxLocalDiagnostic {
            term_nats: psi_k + psi_n - psi_int[n_alpha] - psi_int[n_t],
            joint_radius: eps_raw,
            source_union_count: n_alpha,
            target_count: n_t,
            source1_count: n_s1,
            source2_count: n_s2,
            overlap_count: n_overlap,
            source1_half_count: n_s1_half,
            source2_half_count: n_s2_half,
            overlap_half_count: n_overlap_half,
        })
    };

    crate::par::map_index_ordered(n, local)
}

fn summarize_isx_local(
    local: &[IsxLocalDiagnostic],
    budget: ResourceBudget,
) -> PidResult<IsxLocalDiagnosticsSummary> {
    let mut radii = try_vec_with_capacity("ISX radius summary", local.len(), budget)?;
    let mut source_union = try_vec_with_capacity("ISX union-count summary", local.len(), budget)?;
    let mut target = try_vec_with_capacity("ISX target-count summary", local.len(), budget)?;
    let mut source1 = try_vec_with_capacity("ISX source1-count summary", local.len(), budget)?;
    let mut source2 = try_vec_with_capacity("ISX source2-count summary", local.len(), budget)?;
    let mut overlap = try_vec_with_capacity("ISX overlap-count summary", local.len(), budget)?;
    let mut overlap_half =
        try_vec_with_capacity("ISX half-overlap-count summary", local.len(), budget)?;
    let mut overlap_ratio =
        try_vec_with_capacity("ISX overlap-ratio summary", local.len(), budget)?;
    let mut overlap_half_ratio =
        try_vec_with_capacity("ISX half-overlap-ratio summary", local.len(), budget)?;
    let mut source1_slopes =
        try_vec_with_capacity("ISX source1-slope summary", local.len(), budget)?;
    let mut source2_slopes =
        try_vec_with_capacity("ISX source2-slope summary", local.len(), budget)?;
    let mut terms = try_vec_with_capacity("ISX local-term summary", local.len(), budget)?;
    for value in local {
        radii.push(value.joint_radius);
        source_union.push(value.source_union_count);
        target.push(value.target_count);
        source1.push(value.source1_count);
        source2.push(value.source2_count);
        overlap.push(value.overlap_count);
        overlap_half.push(value.overlap_half_count);
        let union = value
            .source1_count
            .checked_add(value.source2_count)
            .and_then(|count| count.checked_sub(value.overlap_count))
            .ok_or(PidError::SizeOverflow {
                operation: "ISX overlap ratio",
            })?;
        let half_union = value
            .source1_half_count
            .checked_add(value.source2_half_count)
            .and_then(|count| count.checked_sub(value.overlap_half_count))
            .ok_or(PidError::SizeOverflow {
                operation: "ISX half-overlap ratio",
            })?;
        overlap_ratio.push(if union == 0 {
            0.0
        } else {
            value.overlap_count as f64 / union as f64
        });
        overlap_half_ratio.push(if half_union == 0 {
            0.0
        } else {
            value.overlap_half_count as f64 / half_union as f64
        });
        if let Some(slope) = scaling_slope(value.source1_count, value.source1_half_count) {
            source1_slopes.push(slope);
        }
        if let Some(slope) = scaling_slope(value.source2_count, value.source2_half_count) {
            source2_slopes.push(slope);
        }
        terms.push(value.term_nats);
    }
    for values in [
        &mut radii,
        &mut overlap_ratio,
        &mut overlap_half_ratio,
        &mut source1_slopes,
        &mut source2_slopes,
        &mut terms,
    ] {
        values.sort_unstable_by(f64::total_cmp);
    }
    for values in [
        &mut source_union,
        &mut target,
        &mut source1,
        &mut source2,
        &mut overlap,
        &mut overlap_half,
    ] {
        values.sort_unstable();
    }
    Ok(IsxLocalDiagnosticsSummary {
        joint_radius: value_quantiles(&radii)?,
        source_union_count: count_quantiles(&source_union)?,
        target_count: count_quantiles(&target)?,
        source1_count: count_quantiles(&source1)?,
        source2_count: count_quantiles(&source2)?,
        overlap_count: count_quantiles(&overlap)?,
        overlap_half_radius_count: count_quantiles(&overlap_half)?,
        overlap_ratio: value_quantiles(&overlap_ratio)?,
        overlap_half_radius_ratio: value_quantiles(&overlap_half_ratio)?,
        source1_scaling_slope: (!source1_slopes.is_empty())
            .then(|| value_quantiles(&source1_slopes))
            .transpose()?,
        source2_scaling_slope: (!source2_slopes.is_empty())
            .then(|| value_quantiles(&source2_slopes))
            .transpose()?,
        undefined_source1_slopes: local.len() - source1_slopes.len(),
        undefined_source2_slopes: local.len() - source2_slopes.len(),
        local_redundancy_nats: value_quantiles(&terms)?,
    })
}

fn scaling_slope(full_count: usize, half_count: usize) -> Option<f64> {
    (full_count > 0 && half_count > 0 && full_count >= half_count)
        .then(|| (full_count as f64 / half_count as f64).ln() / 2.0_f64.ln())
}

fn isx_assumption_ledger(
    provenance: &IsxProvenance,
    budget: ResourceBudget,
) -> PidResult<Vec<AssumptionLedgerEntry>> {
    let mut ledger = try_vec_with_capacity("ISX assumption ledger", 12, budget)?;
    let separated_splits = provenance.training_split_id.is_some()
        && provenance.evaluation_split_id.is_some()
        && provenance.training_split_id != provenance.evaluation_split_id;
    ledger.extend([
        AssumptionLedgerEntry {
            assumption: Assumption::RegularContinuousOrManifoldLaw,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; sample diagnostics cannot prove population support",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedLocalDimension,
            state: AssumptionState::WarningPresent,
            note: "equal ambient source columns do not prove equal intrinsic dimensions",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::RegularFiniteDensity,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; inspect the multi-scale branch slopes",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FiniteMutualInformation,
            state: AssumptionState::AssumptionsDeclared,
            note: "caller assertion; finite output is not proof",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::DeclaredSamplingDependence,
            state: if provenance.sampling_model_description.is_some() {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "sampling model is recorded but not verified",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::UniqueKthNeighborShell,
            state: AssumptionState::FiniteSampleChecksPassed,
            note: "every joint disjunction shell used by the estimate passed the exact check",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LocalNeighborhoods,
            state: AssumptionState::NotEvaluated,
            note: "compare radius quantiles with density, noise, and domain scales",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::CommonBranchLeadingScale,
            state: AssumptionState::WarningPresent,
            note: "branch slopes are diagnostics, not a proof of common asymptotic scaling",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::LowerOrderBranchIntersections,
            state: AssumptionState::WarningPresent,
            note: "overlap ratios are reported at full and half radii",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::FixedPreprocessingAndMetric,
            state: AssumptionState::AssumptionsDeclared,
            note: "source gauges and target preprocessing are hashed",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdequateSampleSize,
            state: AssumptionState::NotEvaluated,
            note: "run declared k and sample-size trajectories",
        },
        AssumptionLedgerEntry {
            assumption: Assumption::AdaptiveTransformsFitOutsideEvaluationData,
            state: if separated_splits {
                AssumptionState::AssumptionsDeclared
            } else {
                AssumptionState::WarningPresent
            },
            note: "distinct training and evaluation split identifiers are required",
        },
    ]);
    Ok(ledger)
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_disjunction_from_local_mi(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_disjunction_from_local_mi",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let mut i1 = ksg_local_mi_terms_with_budget(s1, t, &ksg_cfg, budget)?;
    let i2 = ksg_local_mi_terms_with_budget(s2, t, &ksg_cfg, budget)?;
    let i12 = ksg_local_mi_terms_xblocks_with_budget(&[s1, s2], t, &ksg_cfg, budget)?;

    for ((a, &b), &c) in i1.iter_mut().zip(i2.iter()).zip(i12.iter()) {
        // Compute: log(exp(a)+exp(b)-exp(c)) stably.
        let m = (*a).max(b).max(c);
        let sa = (*a - m).exp();
        let sb = (b - m).exp();
        let sc = (c - m).exp();
        let s = sa + sb - sc;
        if !s.is_finite() || s <= 0.0 {
            return Err(PidError::NumericalInstability {
                context:
                    "isx_redundancy_disjunction_from_local_mi: disjunction argument is non-positive",
            });
        }
        *a = m + s.ln();
    }

    Ok(compensated_sum(i1) / (n as f64))
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_local_min_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_local_min_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let local_s1 = ksg_local_mi_terms_with_budget(s1, t, &ksg_cfg, budget)?;
    let local_s2 = ksg_local_mi_terms_with_budget(s2, t, &ksg_cfg, budget)?;

    let red = compensated_sum(
        local_s1
            .iter()
            .zip(local_s2.iter())
            .map(|(&a, &b)| a.min(b)),
    ) / (n as f64);

    Ok(red)
}

#[cfg(feature = "experimental-heuristics")]
fn isx_redundancy_heuristic_sketch(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_heuristic_sketch",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // 1) Per-sample kNN radii in the (S1,T) and (S2,T) joint spaces. (Steps 2–3 use only
    //    these two and their samplewise min; no (S1,S2,T) joint radius enters the estimate.)
    let mut eps_s1_t = try_vec_filled("experimental ISX source1 radii", n, 0.0f64, budget)?;
    let mut eps_s2_t = try_vec_filled("experimental ISX source2 radii", n, 0.0f64, budget)?;

    let mut scratch = try_vec_with_capacity(
        "experimental ISX distance scratch",
        n.saturating_sub(1),
        budget,
    )?;
    for i in 0..n {
        let e1 =
            kth_neighbor_distance_joint_max_with_scratch(&[s1, t], i, k, cfg.metric, &mut scratch)?;
        if e1 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e1);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s1,target)",
            i,
            k,
            e1,
            interior_count,
            boundary_count,
        )?;
        eps_s1_t[i] = e1;

        let e2 =
            kth_neighbor_distance_joint_max_with_scratch(&[s2, t], i, k, cfg.metric, &mut scratch)?;
        if e2 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e2);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s2,target)",
            i,
            k,
            e2,
            interior_count,
            boundary_count,
        )?;
        eps_s2_t[i] = e2;
    }

    // 2) Count neighbors in target space within the respective radii.
    let mut n_t_s1 = try_vec_filled("experimental ISX source1 target counts", n, 0usize, budget)?;
    let mut n_t_s2 = try_vec_filled("experimental ISX source2 target counts", n, 0usize, budget)?;
    let mut n_t_shared =
        try_vec_filled("experimental ISX shared target counts", n, 0usize, budget)?;

    for i in 0..n {
        let e1_raw = eps_s1_t[i];
        let e2_raw = eps_s2_t[i];

        let e1 = strict_radius(e1_raw);
        let e2 = strict_radius(e2_raw);
        let es = strict_radius(e1_raw.min(e2_raw));

        n_t_s1[i] = count_neighbors_within(t, i, e1, cfg.metric)?;
        n_t_s2[i] = count_neighbors_within(t, i, e2, cfg.metric)?;
        n_t_shared[i] = count_neighbors_within(t, i, es, cfg.metric)?;
    }

    // 3) Experimental heuristic sketch estimator.
    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n)?;

    let avg_term = compensated_sum((0..n).map(|i| {
        let psi_shared = psi_int[n_t_shared[i] + 1];
        let psi_s1 = psi_int[n_t_s1[i] + 1];
        let psi_s2 = psi_int[n_t_s2[i] + 1];
        psi_shared - 0.5 * (psi_s1 + psi_s2)
    })) / (n as f64);

    let redundancy = psi_k + psi_n + avg_term;
    Ok(redundancy)
}
