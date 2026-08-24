//! Two-source continuous PID assembled from KSG mutual information and continuous shared
//! exclusions.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED CORE / PROJECT-DEFINED REPORT WORKFLOWS.** Ehrlich et al. define the
//! two-source atom reconstruction from KSG MI and continuous shared exclusions. The code is
//! available under `experimental-continuous`; pid-rs supplies no separate consistency theorem for
//! the finite-sample assembly of separately estimated terms. Split-sample and cross-fit reports
//! are project-defined wrappers and do not by themselves provide calibrated inference.
//!
//! Method catalog: pid.continuous-pid2

use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::exact_binary64::{
    exact_binary64_sum, EXACT_BINARY64_ADD_LIMB_VISIT_BOUND, EXACT_BINARY64_TOTAL_LIMB_VISIT_BOUND,
};
use crate::isx::{
    isx_redundancy_report_with_local_terms, isx_redundancy_with_budget,
    isx_report_resource_estimate, isx_resource_estimate_for_method, IsxConfig, IsxLocalDiagnostic,
    IsxProvenance, IsxReport,
};
use crate::ksg::{
    effective_thread_count, ksg_mi_concat_xy_with_budget, ksg_mi_report_with_local_terms,
    ksg_mi_with_budget, ksg_report_resource_estimate, ksg_resource_estimate_for_threads,
    ksg_xblocks_report_resource_estimate, ksg_xblocks_resource_estimate, KsgConfig, KsgMiReport,
    KsgProvenance, NegativeHandling,
};
use crate::matrix::{concat_horiz_with_budget, MatRef};
use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::compensated_sum;
use crate::support::{
    validate_observed_sample_conditions_with_budget, validate_support_contract, SupportContract,
};

/// Two-source continuous PID configuration.
///
/// The derived default deliberately carries unspecified KSG/ISX support contracts and therefore
/// fails closed. Use [`Pid2Config::assume_regular_full_dimensional`] only when its population-law
/// assertion is scientifically justified.
#[derive(Debug, Clone, Default)]
pub struct Pid2Config {
    pub ksg: KsgConfig,
    pub isx: IsxConfig,
}

impl Pid2Config {
    /// Construct a two-source configuration with matching explicit absolute-continuity assertions
    /// for the KSG and shared-exclusions terms.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            ksg: KsgConfig::assume_regular_full_dimensional(),
            isx: IsxConfig::assume_regular_full_dimensional(),
        }
    }
}

/// Structurally checked, caller-declared provenance for a [`Pid2Report`].
///
/// The separate source descriptions are intentional: relative source scaling and preprocessing
/// change the continuous shared-exclusions estimand. Construction checks only that every
/// description is nonempty; it cannot validate the truth or scientific adequacy of the text.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct Pid2Provenance {
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
    sampling_model_description: Option<String>,
    training_split_id: Option<String>,
    evaluation_split_id: Option<String>,
}

impl Pid2Provenance {
    pub fn new(
        source1_preprocessing_description: impl AsRef<str>,
        source2_preprocessing_description: impl AsRef<str>,
        target_preprocessing_description: impl AsRef<str>,
        observation_model_description: impl AsRef<str>,
    ) -> PidResult<Self> {
        let source1_preprocessing_description = source1_preprocessing_description.as_ref();
        let source2_preprocessing_description = source2_preprocessing_description.as_ref();
        let target_preprocessing_description = target_preprocessing_description.as_ref();
        let observation_model_description = observation_model_description.as_ref();
        for (field, description) in [
            (
                "source1_preprocessing_description",
                source1_preprocessing_description,
            ),
            (
                "source2_preprocessing_description",
                source2_preprocessing_description,
            ),
            (
                "target_preprocessing_description",
                target_preprocessing_description,
            ),
            (
                "observation_model_description",
                observation_model_description,
            ),
        ] {
            if description.trim().is_empty() || description.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "Pid2Provenance::new",
                    message: match field {
                        "source1_preprocessing_description" => {
                            "source1_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        "source2_preprocessing_description" => {
                            "source2_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        "target_preprocessing_description" => {
                            "target_preprocessing_description must be nonempty and at most 16 KiB"
                        }
                        _ => "observation_model_description must be nonempty and at most 16 KiB",
                    },
                });
            }
        }
        Ok(Self {
            source1_preprocessing_description: try_owned_text(
                "PID2 provenance",
                source1_preprocessing_description,
            )?,
            source2_preprocessing_description: try_owned_text(
                "PID2 provenance",
                source2_preprocessing_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "PID2 provenance",
                target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "PID2 provenance",
                observation_model_description,
            )?,
            sampling_model_description: None,
            training_split_id: None,
            evaluation_split_id: None,
        })
    }

    /// Attach the declared dependence model and fit/evaluation split identities.
    ///
    /// These are caller declarations. Distinct labels are required when both split identifiers
    /// are present, but labels cannot prove that the underlying row sets are disjoint.
    pub fn with_sampling_model_and_splits(
        mut self,
        sampling_model_description: impl AsRef<str>,
        training_split_id: Option<&str>,
        evaluation_split_id: Option<&str>,
    ) -> PidResult<Self> {
        let sampling_model_description = sampling_model_description.as_ref();
        validate_pid2_optional_text(
            "sampling_model_description",
            Some(sampling_model_description),
        )?;
        validate_pid2_optional_text("training_split_id", training_split_id)?;
        validate_pid2_optional_text("evaluation_split_id", evaluation_split_id)?;
        if training_split_id.is_some()
            && evaluation_split_id.is_some()
            && training_split_id == evaluation_split_id
        {
            return Err(PidError::InvalidConfig {
                context: "Pid2Provenance::with_sampling_model_and_splits",
                message: "training and evaluation split identifiers must differ",
            });
        }
        self.sampling_model_description = Some(try_owned_text(
            "PID2 sampling provenance",
            sampling_model_description,
        )?);
        self.training_split_id = training_split_id
            .map(|value| try_owned_text("PID2 training split", value))
            .transpose()?;
        self.evaluation_split_id = evaluation_split_id
            .map(|value| try_owned_text("PID2 evaluation split", value))
            .transpose()?;
        Ok(self)
    }

    pub fn source1_preprocessing_description(&self) -> &str {
        &self.source1_preprocessing_description
    }

    pub fn source2_preprocessing_description(&self) -> &str {
        &self.source2_preprocessing_description
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
            self.source1_preprocessing_description.as_str(),
            self.source2_preprocessing_description.as_str(),
            self.target_preprocessing_description.as_str(),
            self.observation_model_description.as_str(),
        ]
        .into_iter()
        .map(Some)
        .chain([
            self.sampling_model_description.as_deref(),
            self.training_split_id.as_deref(),
            self.evaluation_split_id.as_deref(),
        ])
        .flatten()
        .try_fold(0u128, |total, value| {
            total
                .checked_add(value.len() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "PID2 provenance",
                })
        })
    }

    fn try_clone_for_report(&self) -> PidResult<Self> {
        Ok(Self {
            source1_preprocessing_description: try_owned_text(
                "PID2 report provenance",
                &self.source1_preprocessing_description,
            )?,
            source2_preprocessing_description: try_owned_text(
                "PID2 report provenance",
                &self.source2_preprocessing_description,
            )?,
            target_preprocessing_description: try_owned_text(
                "PID2 report provenance",
                &self.target_preprocessing_description,
            )?,
            observation_model_description: try_owned_text(
                "PID2 report provenance",
                &self.observation_model_description,
            )?,
            sampling_model_description: self
                .sampling_model_description
                .as_deref()
                .map(|value| try_owned_text("PID2 report provenance", value))
                .transpose()?,
            training_split_id: self
                .training_split_id
                .as_deref()
                .map(|value| try_owned_text("PID2 report provenance", value))
                .transpose()?,
            evaluation_split_id: self
                .evaluation_split_id
                .as_deref()
                .map(|value| try_owned_text("PID2 report provenance", value))
                .transpose()?,
        })
    }
}

fn validate_pid2_optional_text(field: &'static str, value: Option<&str>) -> PidResult<()> {
    if let Some(value) = value {
        if value.trim().is_empty() || value.len() > 16 * 1024 {
            return Err(PidError::InvalidConfig {
                context: "Pid2Provenance::with_sampling_model_and_splits",
                message: match field {
                    "sampling_model_description" => {
                        "sampling_model_description must be nonempty and at most 16 KiB"
                    }
                    "training_split_id" => "training_split_id must be nonempty and at most 16 KiB",
                    _ => "evaluation_split_id must be nonempty and at most 16 KiB",
                },
            });
        }
    }
    Ok(())
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

/// Scientific maturity of the two-source continuous PID method.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Pid2MethodStatus {
    /// Cited estimator construction on a restricted declared domain, without a general estimator
    /// consistency theorem supplied by this crate.
    ExperimentalRestrictedDomain,
    /// Heuristic or alternate estimator retained only as an explicitly experimental baseline.
    ExperimentalBaseline,
}

/// Machine-readable scientific limitation attached to a [`Pid2Report`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Pid2ReportWarning {
    PopulationModelNotVerified,
    EqualAmbientDimensionOnlyNecessary,
    RelativeSourceScalingDefinesEstimand,
    GeneralConsistencyNotEstablished,
    MixedEstimatorBiasProfiles,
    /// The returned covariance describes aligned local contributions, not a calibrated sampling
    /// distribution or confidence interval.
    LocalContributionCovarianceIsNotSamplingCovariance,
    /// No generic uncertainty interval is supplied for this duplicate-sensitive kNN estimator.
    SamplingUncertaintyNotCalibrated,
    ExperimentalIsxBaseline,
}

impl Pid2ReportWarning {
    pub const fn message(self) -> &'static str {
        match self {
            Self::PopulationModelNotVerified => {
                "the support contract is caller-declared; sample checks cannot verify the population model or finite mutual information"
            }
            Self::EqualAmbientDimensionOnlyNecessary => {
                "equal source ambient dimensions are necessary for this construction but do not establish compatible intrinsic geometry or reference measures"
            }
            Self::RelativeSourceScalingDefinesEstimand => {
                "relative source units and preprocessing are part of the shared-exclusions estimand"
            }
            Self::GeneralConsistencyNotEstablished => {
                "the cited restricted-domain construction is not a crate-level claim of general estimator consistency"
            }
            Self::MixedEstimatorBiasProfiles => {
                "KSG mutual-information terms and the shared-exclusions redundancy estimator can have different finite-sample bias profiles"
            }
            Self::LocalContributionCovarianceIsNotSamplingCovariance => {
                "the covariance matrices summarize aligned per-observation estimator contributions and are not calibrated sampling covariance or uncertainty intervals"
            }
            Self::SamplingUncertaintyNotCalibrated => {
                "no generic bootstrap, standard error, or confidence interval is claimed for the duplicate-sensitive continuous PID estimator"
            }
            Self::ExperimentalIsxBaseline => {
                "the selected ISX method is an experimental baseline rather than the cited Ehrlich KSG construction"
            }
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct Pid2Estimate {
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    pub mi_s1s2_t: f64,
    pub redundancy_isx: f64,
}

impl Pid2Estimate {
    /// Construct the four signed estimator coordinates used by [`Pid2Result::from_estimate`].
    pub const fn new(mi_s1_t: f64, mi_s2_t: f64, mi_s1s2_t: f64, redundancy_isx: f64) -> Self {
        Self {
            mi_s1_t,
            mi_s2_t,
            mi_s1s2_t,
            redundancy_isx,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct Pid2Result {
    pub redundancy: f64,
    pub unique_s1: f64,
    pub unique_s2: f64,
    pub synergy: f64,
}

/// Conditioning state for one PID atom's defining linear combination.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Pid2ConditioningStatus {
    /// The atom is nonzero and its finite amplification factor is representable.
    Finite,
    /// Every defining term and the atom are exactly zero.
    AllTermsZero,
    /// Nonzero defining terms cancel to an exactly zero represented atom.
    ExactCancellation,
    /// The finite mathematical ratio exceeds the binary64 range.
    AmplificationExceedsF64Range,
}

/// Scale and cancellation diagnostics for one PID atom.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct Pid2AtomConditioning {
    pub atom: &'static str,
    pub value_nats: f64,
    pub absolute_constituent_sum_nats: f64,
    /// `|atom| / sum(|signed constituent terms|)`, or `None` when every term is zero.
    pub retained_fraction: Option<f64>,
    /// Reciprocal retained fraction. Absent only for exact zero or an unrepresentable ratio.
    pub amplification_factor: Option<f64>,
    pub status: Pid2ConditioningStatus,
}

/// Joint empirical covariance diagnostics from the four aligned local estimator contributions.
///
/// These matrices describe the observed local contribution vectors. They are not a theorem-backed
/// covariance estimator for the population PID atoms and must not be relabeled as standard errors
/// or confidence intervals.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub struct Pid2JointDiagnostics {
    pub constituent_order: [&'static str; 4],
    pub atom_order: [&'static str; 4],
    pub local_contribution_covariance_nats2: [[f64; 4]; 4],
    pub propagated_atom_local_covariance_nats2: [[f64; 4]; 4],
    pub atom_conditioning: [Pid2AtomConditioning; 4],
    pub interpretation: &'static str,
}

/// Complete two-source PID report with constituent estimators, diagnostics, provenance, and
/// resource accounting attached.
///
/// The three signed KSG MI coordinates and the shared-exclusions redundancy coordinate are each
/// evaluated once and retained as complete reports. Joint diagnostics summarize covariance of
/// their aligned local contributions and cancellation in the derived atoms. That covariance is a
/// descriptive finite-sample diagnostic, not calibrated sampling covariance or uncertainty.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct Pid2Report {
    pub atoms: Pid2Result,
    pub estimate_terms: Pid2Estimate,
    pub n_samples: usize,
    pub source_ambient_dimensions: [usize; 2],
    pub target_ambient_dimension: usize,
    pub supplied_ksg_config: KsgConfig,
    pub supplied_isx_config: IsxConfig,
    pub effective_negative_handling: NegativeHandling,
    pub support_contract: SupportContract,
    pub method_status: Pid2MethodStatus,
    pub provenance: Pid2Provenance,
    /// Complete report for `I(S1;T)`, evaluated once with signed terms.
    pub mi_s1_t_report: KsgMiReport,
    /// Complete report for `I(S2;T)`, evaluated once with signed terms.
    pub mi_s2_t_report: KsgMiReport,
    /// Complete report for `I((S1,S2);T)`, evaluated once on the explicit concatenation.
    pub mi_s1s2_t_report: KsgMiReport,
    /// Complete shared-exclusions neighborhood report used as the redundancy coordinate.
    pub redundancy_isx_report: IsxReport,
    pub joint_diagnostics: Pid2JointDiagnostics,
    pub warnings: Vec<Pid2ReportWarning>,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

/// One already-separated evaluation fold for [`pid2_isx_cross_fit_reports_with_budget`].
///
/// Fitting, scaling, projection, and row selection happen outside this type. The fold therefore
/// accepts only evaluation matrices plus provenance that identifies the complementary training
/// rows and this evaluation split.
pub struct Pid2CrossFitFold<'a> {
    fold_id: &'a str,
    source1: MatRef<'a>,
    source2: MatRef<'a>,
    target: MatRef<'a>,
    provenance: &'a Pid2Provenance,
}

impl<'a> Pid2CrossFitFold<'a> {
    pub fn new(
        fold_id: &'a str,
        source1: MatRef<'a>,
        source2: MatRef<'a>,
        target: MatRef<'a>,
        provenance: &'a Pid2Provenance,
    ) -> PidResult<Self> {
        validate_pid2_optional_text("evaluation_split_id", Some(fold_id))?;
        if provenance.training_split_id().is_none()
            || provenance.evaluation_split_id() != Some(fold_id)
        {
            return Err(PidError::InvalidConfig {
                context: "Pid2CrossFitFold::new",
                message: "provenance must name a training split and an evaluation_split_id equal to fold_id",
            });
        }
        Ok(Self {
            fold_id,
            source1,
            source2,
            target,
            provenance,
        })
    }

    pub fn fold_id(&self) -> &str {
        self.fold_id
    }
}

/// One complete PID2 report retained in its own fold-specific coordinate system.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct Pid2CrossFitFoldReport {
    pub fold_id: String,
    pub report: Pid2Report,
}

/// Deliberate aggregation policy for cross-fit continuous PID outputs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Pid2CrossFitAggregation {
    /// Fold-specific source gauges, radii, and local contributions are returned separately.
    FoldCoordinatesRemainSeparate,
}

/// Cross-fit envelope that intentionally does not pool incompatible neighborhood coordinates.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct Pid2CrossFitReport {
    pub folds: Vec<Pid2CrossFitFoldReport>,
    pub aggregation: Pid2CrossFitAggregation,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub warning: &'static str,
}

/// 2-source PID atoms (Red, Unq₁, Unq₂, Syn) from KSG mutual information and the `I^sx_∩`
/// redundancy. Their defining exact-real algebra satisfies
/// `Red + Unq₁ + Unq₂ + Syn = I(S1,S2;T)`. The represented-binary64 constructor exactly reduces
/// the four represented synergy operands, then admits the separately rounded atom tuple only under
/// its documented 32-position compatibility guard; this is not exact binary64 identity or an
/// estimator-validity theorem.
///
/// The redundancy term follows `cfg.isx.method`. `IsxMethod::EhrlichKsg` (the default) is the
/// cited restricted-domain construction; the crate does not claim a general consistency theorem.
/// The other methods are experimental baselines, and combining them with the KSG MI terms
/// mixes estimators with different bias profiles — interpret such atoms with care (see the `isx`
/// module docs).
///
/// Relative source units/preprocessing are part of the continuous shared-exclusions estimand;
/// record them and do not compare atoms across schemes. Exact deterministic continuous maps have
/// infinite MI and require a justified noise model or a suitable discrete/mixed estimator.
/// Both sources must also have the same ambient column count. This is a necessary small-ball
/// scaling guard, not proof that their intrinsic dimensions or reference measures are compatible.
///
/// # Example
/// ```
/// use pid_core::experimental::continuous::{pid2_isx, Pid2Config};
/// use pid_core::MatRef;
/// // T depends on both sources, so expect non-trivial synergy/redundancy.
/// let s1 = [0.13, 0.91, 0.37, 0.62, 0.04, 0.78, 0.49, 0.25];
/// let s2 = [0.84, 0.17, 0.55, 0.03, 0.69, 0.31, 0.96, 0.42];
/// let noise = [0.03, -0.02, 0.01, -0.04, 0.02, -0.01, 0.04, -0.03];
/// let t: Vec<f64> = (0..8).map(|i| s1[i] + s2[i] + noise[i]).collect();
/// let s1 = MatRef::new(&s1, 8, 1)?;
/// let s2 = MatRef::new(&s2, 8, 1)?;
/// let t = MatRef::new(&t, 8, 1)?;
/// let pid = pid2_isx(s1, s2, t, &Pid2Config::assume_regular_full_dimensional())?;
/// // A returned tuple passed the represented-coordinate compatibility guard; exact f64 equality
/// // and statistical validity do not follow.
/// let sum = pid.redundancy + pid.unique_s1 + pid.unique_s2 + pid.synergy;
/// assert!(sum.is_finite());
/// # Ok::<(), pid_core::PidError>(())
/// ```
pub fn pid2_isx(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Pid2Result> {
    pid2_isx_with_budget(s1, s2, t, cfg, ResourceBudget::default())
}

/// Compute continuous PID2 under an explicit memory, work, and thread budget.
pub fn pid2_isx_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    budget: ResourceBudget,
) -> PidResult<Pid2Result> {
    let estimate = pid2_isx_estimate_with_budget(s1, s2, t, cfg, budget)?;
    Pid2Result::from_estimate(estimate)
}

/// Compute a complete two-source PID report suitable for persistence or scientific handoff.
///
/// Provenance strings are caller declarations checked only for nonemptiness. The report preserves
/// both supplied estimator configurations and records that PID algebra always uses signed
/// (`Allow`) MI terms. It retains every constituent KSG report, the complete ISX
/// disjunction-neighborhood report, and aligned local-contribution covariance/conditioning
/// diagnostics without claiming calibrated sampling uncertainty.
pub fn pid2_isx_report(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
) -> PidResult<Pid2Report> {
    pid2_isx_report_with_budget(s1, s2, t, cfg, provenance, ResourceBudget::default())
}

/// Compute the complete PID2 report under an explicit resource budget.
pub fn pid2_isx_report_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
    budget: ResourceBudget,
) -> PidResult<Pid2Report> {
    validate_pid2_inputs(s1, s2, t, cfg)?;
    if cfg.isx.method != crate::isx::IsxMethod::EhrlichKsg {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_report",
            message: "complete PID2 reports require the cited IsxMethod::EhrlichKsg construction; heuristic scalar baselines do not have complete neighborhood reports",
        });
    }
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let component_provenance = pid2_component_provenance(provenance)?;
    let resource_estimate = pid2_report_resource_estimate_with_provenance(
        s1,
        s2,
        t,
        cfg,
        provenance,
        &component_provenance,
        threads,
    )?;
    budget.check("pid2_isx_report", resource_estimate)?;

    let ksg = cfg
        .ksg
        .clone()
        .with_negative_handling(NegativeHandling::Allow);
    let joined_sources = concat_horiz_with_budget(s1, s2, budget)?;
    let mi_s1 = ksg_mi_report_with_local_terms(s1, t, &ksg, &component_provenance.mi_s1_t, budget)?;
    let mi_s2 = ksg_mi_report_with_local_terms(s2, t, &ksg, &component_provenance.mi_s2_t, budget)?;
    let mi_s1s2 = ksg_mi_report_with_local_terms(
        joined_sources.as_ref(),
        t,
        &ksg,
        &component_provenance.mi_s1s2_t,
        budget,
    )?;
    let redundancy = isx_redundancy_report_with_local_terms(
        s1,
        s2,
        t,
        &cfg.isx,
        &component_provenance.redundancy,
        budget,
    )?;
    let estimate_terms = Pid2Estimate {
        mi_s1_t: mi_s1.report.estimate_nats,
        mi_s2_t: mi_s2.report.estimate_nats,
        mi_s1s2_t: mi_s1s2.report.estimate_nats,
        redundancy_isx: redundancy.report.estimate_nats,
    };
    let atoms = Pid2Result::from_estimate(estimate_terms)?;
    let joint_diagnostics = pid2_joint_diagnostics(
        &mi_s1.local_terms_nats,
        &mi_s2.local_terms_nats,
        &mi_s1s2.local_terms_nats,
        &redundancy.local,
        estimate_terms,
        atoms,
    )?;
    let method_status = Pid2MethodStatus::ExperimentalRestrictedDomain;
    let mut warnings = try_vec_with_capacity("PID2 report warnings", 8, budget)?;
    warnings.extend([
        Pid2ReportWarning::PopulationModelNotVerified,
        Pid2ReportWarning::EqualAmbientDimensionOnlyNecessary,
        Pid2ReportWarning::RelativeSourceScalingDefinesEstimand,
        Pid2ReportWarning::GeneralConsistencyNotEstablished,
        Pid2ReportWarning::MixedEstimatorBiasProfiles,
        Pid2ReportWarning::LocalContributionCovarianceIsNotSamplingCovariance,
        Pid2ReportWarning::SamplingUncertaintyNotCalibrated,
    ]);
    Ok(Pid2Report {
        atoms,
        estimate_terms,
        n_samples: t.nrows(),
        source_ambient_dimensions: [s1.ncols(), s2.ncols()],
        target_ambient_dimension: t.ncols(),
        supplied_ksg_config: cfg.ksg.clone(),
        supplied_isx_config: cfg.isx.clone(),
        effective_negative_handling: NegativeHandling::Allow,
        support_contract: cfg.ksg.support_contract,
        method_status,
        provenance: provenance.try_clone_for_report()?,
        mi_s1_t_report: mi_s1.report,
        mi_s2_t_report: mi_s2.report,
        mi_s1s2_t_report: mi_s1s2.report,
        redundancy_isx_report: redundancy.report,
        joint_diagnostics,
        warnings,
        resource_estimate,
        resource_budget: budget,
    })
}

/// Evaluate one pre-separated held-out split, requiring explicit train/evaluation identities.
pub fn pid2_isx_split_sample_report(
    s1_evaluation: MatRef<'_>,
    s2_evaluation: MatRef<'_>,
    target_evaluation: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
) -> PidResult<Pid2Report> {
    pid2_isx_split_sample_report_with_budget(
        s1_evaluation,
        s2_evaluation,
        target_evaluation,
        cfg,
        provenance,
        ResourceBudget::default(),
    )
}

/// Evaluate one pre-separated held-out split under an aggregate resource ceiling.
pub fn pid2_isx_split_sample_report_with_budget(
    s1_evaluation: MatRef<'_>,
    s2_evaluation: MatRef<'_>,
    target_evaluation: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
    budget: ResourceBudget,
) -> PidResult<Pid2Report> {
    if provenance.training_split_id().is_none() || provenance.evaluation_split_id().is_none() {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_split_sample_report_with_budget",
            message: "split-sample PID2 requires distinct training_split_id and evaluation_split_id provenance",
        });
    }
    pid2_isx_report_with_budget(
        s1_evaluation,
        s2_evaluation,
        target_evaluation,
        cfg,
        provenance,
        budget,
    )
}

/// Evaluate complete reports on already-separated cross-fit folds without pooling coordinates.
pub fn pid2_isx_cross_fit_reports(
    folds: &[Pid2CrossFitFold<'_>],
    cfg: &Pid2Config,
) -> PidResult<Pid2CrossFitReport> {
    pid2_isx_cross_fit_reports_with_budget(folds, cfg, ResourceBudget::default())
}

/// Cross-fit report assembly under an aggregate memory/work/thread ceiling.
pub fn pid2_isx_cross_fit_reports_with_budget(
    folds: &[Pid2CrossFitFold<'_>],
    cfg: &Pid2Config,
    budget: ResourceBudget,
) -> PidResult<Pid2CrossFitReport> {
    let resource_estimate = pid2_cross_fit_resource_estimate(folds, cfg, budget.max_threads)?;
    budget.check("pid2_isx_cross_fit_reports", resource_estimate)?;
    let mut reports = try_vec_with_capacity("PID2 cross-fit reports", folds.len(), budget)?;
    for fold in folds {
        let report = pid2_isx_split_sample_report_with_budget(
            fold.source1,
            fold.source2,
            fold.target,
            cfg,
            fold.provenance,
            budget,
        )?;
        reports.push(Pid2CrossFitFoldReport {
            fold_id: try_owned_text("PID2 cross-fit fold identity", fold.fold_id)?,
            report,
        });
    }
    Ok(Pid2CrossFitReport {
        folds: reports,
        aggregation: Pid2CrossFitAggregation::FoldCoordinatesRemainSeparate,
        resource_estimate,
        resource_budget: budget,
        warning: "fold reports are not pooled: independently fitted gauges and kNN neighborhood coordinates do not define a common local-coordinate sample",
    })
}

/// Aggregate preflight for already-separated cross-fit folds.
pub fn pid2_cross_fit_resource_estimate(
    folds: &[Pid2CrossFitFold<'_>],
    cfg: &Pid2Config,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "pid2_isx_cross_fit_reports";
    if folds.len() < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "cross-fit reporting requires at least two evaluation folds",
        });
    }
    for (index, fold) in folds.iter().enumerate() {
        for other in &folds[..index] {
            if fold.fold_id == other.fold_id {
                return Err(PidError::InvalidConfig {
                    context: OPERATION,
                    message: "cross-fit fold identifiers must be unique",
                });
            }
        }
    }
    let mut aggregate = ResourceEstimate::ZERO;
    for fold in folds {
        let estimate = pid2_report_resource_estimate(
            fold.source1,
            fold.source2,
            fold.target,
            cfg,
            fold.provenance,
            max_threads,
        )?;
        aggregate.estimated_bytes = aggregate
            .estimated_bytes
            .checked_add(estimate.estimated_bytes)
            .and_then(|value| value.checked_add(fold.fold_id.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        aggregate.pairwise_distances = aggregate
            .pairwise_distances
            .checked_add(estimate.pairwise_distances)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        aggregate.operations_hint = aggregate
            .operations_hint
            .checked_add(estimate.operations_hint)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    }
    aggregate.estimated_bytes = aggregate
        .estimated_bytes
        .checked_add(std::mem::size_of::<Pid2CrossFitReport>() as u128)
        .and_then(|value| {
            value.checked_add(
                (folds.len() as u128)
                    .checked_mul(std::mem::size_of::<Pid2CrossFitFoldReport>() as u128)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.operations_hint = aggregate
        .operations_hint
        .checked_add(
            (folds.len() as u128)
                .checked_mul(folds.len().saturating_sub(1) as u128)
                .and_then(|value| value.checked_div(2))
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(aggregate)
}

struct Pid2ComponentProvenance {
    mi_s1_t: KsgProvenance,
    mi_s2_t: KsgProvenance,
    mi_s1s2_t: KsgProvenance,
    redundancy: IsxProvenance,
}

fn pid2_component_provenance(provenance: &Pid2Provenance) -> PidResult<Pid2ComponentProvenance> {
    let mi_s1_t = pid2_ksg_provenance(
        &[
            ("source1", provenance.source1_preprocessing_description()),
            ("target", provenance.target_preprocessing_description()),
        ],
        provenance,
    )?;
    let mi_s2_t = pid2_ksg_provenance(
        &[
            ("source2", provenance.source2_preprocessing_description()),
            ("target", provenance.target_preprocessing_description()),
        ],
        provenance,
    )?;
    let mi_s1s2_t = pid2_ksg_provenance(
        &[
            ("source1", provenance.source1_preprocessing_description()),
            ("source2", provenance.source2_preprocessing_description()),
            ("target", provenance.target_preprocessing_description()),
        ],
        provenance,
    )?;
    let redundancy = IsxProvenance::new_with_optional_sampling(
        provenance.source1_preprocessing_description(),
        provenance.source2_preprocessing_description(),
        provenance.target_preprocessing_description(),
        provenance.observation_model_description(),
        provenance.sampling_model_description(),
        provenance.training_split_id(),
        provenance.evaluation_split_id(),
    )?;
    Ok(Pid2ComponentProvenance {
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        redundancy,
    })
}

fn pid2_ksg_provenance(
    preprocessing: &[(&'static str, &str)],
    provenance: &Pid2Provenance,
) -> PidResult<KsgProvenance> {
    let description = labeled_description("PID2 KSG preprocessing", preprocessing)?;
    let mut result = KsgProvenance::new(
        &description,
        provenance.observation_model_description(),
        None,
    )?;
    if let Some(sampling_model) = provenance.sampling_model_description() {
        result = result.with_sampling_model_and_splits(
            sampling_model,
            provenance.training_split_id(),
            provenance.evaluation_split_id(),
        )?;
    }
    Ok(result)
}

fn labeled_description(
    operation: &'static str,
    fields: &[(&'static str, &str)],
) -> PidResult<String> {
    let capacity =
        fields
            .iter()
            .enumerate()
            .try_fold(0usize, |total, (index, (label, value))| {
                total
                    .checked_add(label.len())
                    .and_then(|sum| sum.checked_add(1))
                    .and_then(|sum| sum.checked_add(value.len()))
                    .and_then(|sum| sum.checked_add(usize::from(index + 1 < fields.len()) * 2))
                    .ok_or(PidError::SizeOverflow { operation })
            })?;
    let mut description = String::new();
    description
        .try_reserve_exact(capacity)
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: capacity as u128,
        })?;
    for (index, (label, value)) in fields.iter().enumerate() {
        if index > 0 {
            description.push_str("; ");
        }
        description.push_str(label);
        description.push('=');
        description.push_str(value);
    }
    Ok(description)
}

const PID2_CONSTITUENT_ORDER: [&str; 4] =
    ["I(S1;T)", "I(S2;T)", "I((S1,S2);T)", "Icap_sx(S1,S2;T)"];
const PID2_ATOM_ORDER: [&str; 4] = ["redundancy", "unique_s1", "unique_s2", "synergy"];
// Compatibility policy inherited by the checked constructor. This is not a derived forward-error
// bound: near zero it can accept complete relative loss. Because ordered_float_bits distinguishes
// signed zeros, expected payload +32 versus reconstructed +0 passes and +33 fails, whereas -31
// passes and -32 fails. Keep this sign-asymmetric compatibility boundary explicit and tested.
const PID2_RECONSTRUCTION_MAX_ORDERED_POSITIONS: u64 = 32;
const PID2_ATOM_TRANSFORM: [[f64; 4]; 4] = [
    [0.0, 0.0, 0.0, 1.0],
    [1.0, 0.0, 0.0, -1.0],
    [0.0, 1.0, 0.0, -1.0],
    [-1.0, -1.0, 1.0, 1.0],
];

fn pid2_joint_diagnostics(
    mi_s1: &[f64],
    mi_s2: &[f64],
    mi_s1s2: &[f64],
    redundancy: &[IsxLocalDiagnostic],
    estimate: Pid2Estimate,
    atoms: Pid2Result,
) -> PidResult<Pid2JointDiagnostics> {
    let n = mi_s1.len();
    if n < 2 || mi_s2.len() != n || mi_s1s2.len() != n || redundancy.len() != n {
        return Err(PidError::InvalidConfig {
            context: "PID2 local covariance",
            message: "aligned constituent local-term vectors must have the same length >= 2",
        });
    }
    let means = [
        compensated_sum(mi_s1.iter().copied()) / n as f64,
        compensated_sum(mi_s2.iter().copied()) / n as f64,
        compensated_sum(mi_s1s2.iter().copied()) / n as f64,
        compensated_sum(redundancy.iter().map(|value| value.term_nats)) / n as f64,
    ];
    if means.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "PID2 local covariance means",
        });
    }
    let mut covariance = [[0.0; 4]; 4];
    for row in 0..4 {
        for column in row..4 {
            let sum = compensated_sum((0..n).map(|index| {
                (pid2_local_value(row, index, mi_s1, mi_s2, mi_s1s2, redundancy) - means[row])
                    * (pid2_local_value(column, index, mi_s1, mi_s2, mi_s1s2, redundancy)
                        - means[column])
            }));
            let value = sum / (n - 1) as f64;
            if !value.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "PID2 local contribution covariance",
                });
            }
            covariance[row][column] = value;
            covariance[column][row] = value;
        }
    }
    let atom_covariance = propagate_pid2_covariance(covariance)?;
    let atom_conditioning = [
        pid2_atom_conditioning("redundancy", atoms.redundancy, &[estimate.redundancy_isx])?,
        pid2_atom_conditioning(
            "unique_s1",
            atoms.unique_s1,
            &[estimate.mi_s1_t, -estimate.redundancy_isx],
        )?,
        pid2_atom_conditioning(
            "unique_s2",
            atoms.unique_s2,
            &[estimate.mi_s2_t, -estimate.redundancy_isx],
        )?,
        pid2_atom_conditioning(
            "synergy",
            atoms.synergy,
            &[
                estimate.mi_s1s2_t,
                -estimate.mi_s1_t,
                -estimate.mi_s2_t,
                estimate.redundancy_isx,
            ],
        )?,
    ];
    Ok(Pid2JointDiagnostics {
        constituent_order: PID2_CONSTITUENT_ORDER,
        atom_order: PID2_ATOM_ORDER,
        local_contribution_covariance_nats2: covariance,
        propagated_atom_local_covariance_nats2: atom_covariance,
        atom_conditioning,
        interpretation: "empirical covariance of aligned local estimator contributions; not calibrated sampling covariance, standard errors, or confidence intervals",
    })
}

fn pid2_local_value(
    constituent: usize,
    index: usize,
    mi_s1: &[f64],
    mi_s2: &[f64],
    mi_s1s2: &[f64],
    redundancy: &[IsxLocalDiagnostic],
) -> f64 {
    match constituent {
        0 => mi_s1[index],
        1 => mi_s2[index],
        2 => mi_s1s2[index],
        _ => redundancy[index].term_nats,
    }
}

fn propagate_pid2_covariance(covariance: [[f64; 4]; 4]) -> PidResult<[[f64; 4]; 4]> {
    let mut propagated = [[0.0; 4]; 4];
    for row in 0..4 {
        for column in row..4 {
            let value = compensated_sum((0..4).flat_map(|i| {
                (0..4).map(move |j| {
                    PID2_ATOM_TRANSFORM[row][i] * covariance[i][j] * PID2_ATOM_TRANSFORM[column][j]
                })
            }));
            if !value.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "PID2 propagated local covariance",
                });
            }
            propagated[row][column] = value;
            propagated[column][row] = value;
        }
    }
    Ok(propagated)
}

fn pid2_atom_conditioning(
    atom: &'static str,
    value_nats: f64,
    signed_terms: &[f64],
) -> PidResult<Pid2AtomConditioning> {
    let absolute_constituent_sum_nats = compensated_sum(signed_terms.iter().map(|v| v.abs()));
    if !absolute_constituent_sum_nats.is_finite() {
        return Err(PidError::NumericalInstability {
            context: "PID2 atom conditioning",
        });
    }
    if absolute_constituent_sum_nats == 0.0 {
        return Ok(Pid2AtomConditioning {
            atom,
            value_nats,
            absolute_constituent_sum_nats,
            retained_fraction: None,
            amplification_factor: None,
            status: Pid2ConditioningStatus::AllTermsZero,
        });
    }
    let retained_fraction = value_nats.abs() / absolute_constituent_sum_nats;
    if value_nats == 0.0 {
        return Ok(Pid2AtomConditioning {
            atom,
            value_nats,
            absolute_constituent_sum_nats,
            retained_fraction: Some(0.0),
            amplification_factor: None,
            status: Pid2ConditioningStatus::ExactCancellation,
        });
    }
    let amplification_factor = absolute_constituent_sum_nats / value_nats.abs();
    let (amplification_factor, status) = if amplification_factor.is_finite() {
        (Some(amplification_factor), Pid2ConditioningStatus::Finite)
    } else {
        (None, Pid2ConditioningStatus::AmplificationExceedsF64Range)
    };
    Ok(Pid2AtomConditioning {
        atom,
        value_nats,
        absolute_constituent_sum_nats,
        retained_fraction: Some(retained_fraction),
        amplification_factor,
        status,
    })
}

pub fn pid2_isx_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Pid2Estimate> {
    pid2_isx_estimate_with_budget(s1, s2, t, cfg, ResourceBudget::default())
}

/// Compute the four signed PID2 constituent estimates under an explicit resource budget.
pub fn pid2_isx_estimate_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    budget: ResourceBudget,
) -> PidResult<Pid2Estimate> {
    validate_pid2_inputs(s1, s2, t, cfg)?;
    let threads = effective_thread_count(budget.max_threads, s1.nrows());
    let resource_estimate = pid2_resource_estimate_for_threads(s1, s2, t, cfg, threads)?;
    budget.check("pid2_isx_estimate", resource_estimate)?;
    validate_observed_sample_conditions_with_budget(
        "pid2_isx_estimate",
        cfg.ksg.support_contract,
        &[s1, s2, t],
        budget,
    )?;
    pid2_isx_estimate_prevalidated(s1, s2, t, cfg, budget)
}

fn validate_pid2_inputs(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<()> {
    if s1.nrows() != s2.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "pid2_isx_estimate",
            left_rows: s1.nrows(),
            right_rows: s2.nrows(),
        });
    }
    if s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "pid2_isx_estimate",
            left_rows: s1.nrows(),
            right_rows: t.nrows(),
        });
    }
    if s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_estimate",
            message: "sources and target must each have at least 1 column",
        });
    }
    if s1.ncols() != s2.ncols() {
        return Err(PidError::SourceDimensionMismatch {
            context: "pid2_isx_estimate",
            left_cols: s1.ncols(),
            right_cols: s2.ncols(),
        });
    }
    if cfg.ksg.k == 0 || s1.nrows() <= cfg.ksg.k {
        return Err(PidError::InvalidK {
            k: cfg.ksg.k,
            n_samples: s1.nrows(),
        });
    }
    validate_pid2_config(cfg)?;
    validate_support_contract(
        "pid2_isx_estimate",
        cfg.ksg.support_contract,
        cfg.ksg.metric,
    )?;
    Ok(())
}

fn pid2_isx_estimate_prevalidated(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    budget: ResourceBudget,
) -> PidResult<Pid2Estimate> {
    // The MI terms feed algebraic identities (`Unq`/`Syn` are differences of MIs), so they must
    // not be clamped: clamping a term before a subtraction would break the identity
    // `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`. Force `Allow` regardless of the caller's config so
    // the default path is correct. Keep the signed raw atoms: negative shared-exclusions atoms can
    // be genuine, and any presentation transform must remain separate from the scientific result.
    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.ksg.clone()
    };
    let mi_s1_t = ksg_mi_with_budget(s1, t, &ksg, budget)?;
    let mi_s2_t = ksg_mi_with_budget(s2, t, &ksg, budget)?;
    let mi_s1s2_t = ksg_mi_concat_xy_with_budget(s1, s2, t, &ksg, budget)?;
    let redundancy_isx = isx_redundancy_with_budget(s1, s2, t, &cfg.isx, budget)?;

    Ok(Pid2Estimate {
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        redundancy_isx,
    })
}

/// Preflight the peak memory and aggregate pairwise work for the four PID2 constituents.
pub fn pid2_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<ResourceEstimate> {
    pid2_resource_estimate_for_threads(
        s1,
        s2,
        t,
        cfg,
        effective_thread_count(ResourceBudget::default().max_threads, s1.nrows()),
    )
}

/// PID2 preflight including one scratch buffer and explicit stack reservation per active worker.
pub fn pid2_resource_estimate_for_threads(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "pid2_isx_estimate";
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    validate_pid2_inputs(s1, s2, t, cfg)?;
    let estimates = [
        ksg_resource_estimate_for_threads(s1, t, max_threads)?,
        ksg_resource_estimate_for_threads(s2, t, max_threads)?,
        ksg_xblocks_resource_estimate(&[s1, s2], t, max_threads)?,
        isx_resource_estimate_for_method(s1, s2, t, cfg.isx.method, max_threads)?,
    ];
    let mut aggregate = ResourceEstimate::ZERO;
    for estimate in estimates {
        aggregate.estimated_bytes = aggregate.estimated_bytes.max(estimate.estimated_bytes);
        aggregate.pairwise_distances = aggregate
            .pairwise_distances
            .checked_add(estimate.pairwise_distances)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        aggregate.operations_hint = aggregate
            .operations_hint
            .checked_add(estimate.operations_hint)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    }
    // One result construction performs the four-addend synergy reduction and three identity
    // reconstructions with 2, 2, and 4 addends: 12 exact adds and four finalizations. The public
    // constituent-estimate-only call conservatively retains this fixed allowance because it shares
    // this preflight with the result-returning path.
    aggregate.operations_hint = aggregate
        .operations_hint
        .checked_add(pid2_exact_reconstruction_work())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.estimated_bytes = aggregate
        .estimated_bytes
        .checked_add(std::mem::size_of::<Pid2Estimate>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(aggregate)
}

/// Full PID2 metadata-report preflight including retained provenance and warnings.
pub fn pid2_report_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    if cfg.isx.method != crate::isx::IsxMethod::EhrlichKsg {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_report",
            message: "complete PID2 reports require the cited IsxMethod::EhrlichKsg construction; heuristic scalar baselines do not have complete neighborhood reports",
        });
    }
    let component_provenance = pid2_component_provenance(provenance)?;
    pid2_report_resource_estimate_with_provenance(
        s1,
        s2,
        t,
        cfg,
        provenance,
        &component_provenance,
        max_threads,
    )
}

fn pid2_report_resource_estimate_with_provenance(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
    provenance: &Pid2Provenance,
    component_provenance: &Pid2ComponentProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "pid2_isx_report";
    validate_pid2_inputs(s1, s2, t, cfg)?;
    let estimates = [
        ksg_report_resource_estimate(s1, t, &component_provenance.mi_s1_t, max_threads)?,
        ksg_report_resource_estimate(s2, t, &component_provenance.mi_s2_t, max_threads)?,
        ksg_xblocks_report_resource_estimate(
            &[s1, s2],
            t,
            &component_provenance.mi_s1s2_t,
            max_threads,
        )?,
        isx_report_resource_estimate(s1, s2, t, &component_provenance.redundancy, max_threads)?,
    ];
    // All constituent reports and their aligned local-term vectors coexist while covariance is
    // assembled, so sum their memory estimates rather than taking only a sequential peak.
    let mut estimate = ResourceEstimate::ZERO;
    for constituent in estimates {
        estimate.estimated_bytes = estimate
            .estimated_bytes
            .checked_add(constituent.estimated_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        estimate.pairwise_distances = estimate
            .pairwise_distances
            .checked_add(constituent.pairwise_distances)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        estimate.operations_hint = estimate
            .operations_hint
            .checked_add(constituent.operations_hint)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    }
    estimate.operations_hint = estimate
        .operations_hint
        .checked_add(pid2_exact_reconstruction_work())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let joined_elements = s1
        .ncols()
        .checked_add(s2.ncols())
        .and_then(|columns| columns.checked_mul(s1.nrows()))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let joined_bytes = (joined_elements as u128)
        .checked_mul(std::mem::size_of::<f64>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let retained = provenance
        .heap_bytes()?
        .checked_add(std::mem::size_of::<Pid2Report>() as u128)
        .and_then(|value| {
            value.checked_add(8u128.checked_mul(std::mem::size_of::<Pid2ReportWarning>() as u128)?)
        })
        .and_then(|value| value.checked_add(std::mem::size_of::<Pid2JointDiagnostics>() as u128))
        .and_then(|value| value.checked_add(joined_bytes))
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

fn pid2_exact_reconstruction_work() -> u128 {
    12 * EXACT_BINARY64_ADD_LIMB_VISIT_BOUND as u128
        + 4 * EXACT_BINARY64_TOTAL_LIMB_VISIT_BOUND as u128
}

/// Enforce the KSG/ISX parameter-consistency contract shared by every path that mixes KSG MI
/// terms with an `isx_redundancy` estimate (`pid2_isx`, `hierarchical_pairwise`): the two
/// estimators must agree on `k`, `metric`, and `tie_epsilon` or the atoms mix incompatible
/// neighbourhood geometries.
pub(crate) fn validate_ksg_isx_consistency(
    context: &'static str,
    ksg: &crate::ksg::KsgConfig,
    isx: &crate::isx::IsxConfig,
) -> PidResult<()> {
    if ksg.k != isx.k {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX k values must match",
        });
    }
    if ksg.metric != isx.metric {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX metrics must match",
        });
    }
    if ksg.metric != crate::metric::Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message: "continuous PID2 requires the cited Metric::Chebyshev (L∞) neighborhood convention; hyperbolic MI reports cannot supply concatenated/shared-exclusions PID terms",
        });
    }
    if ksg.tie_epsilon != isx.tie_epsilon {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX tie_epsilon values must match",
        });
    }
    if ksg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX tie_epsilon must both be exactly 0; strict counting uses next-down semantics",
        });
    }
    if ksg.support_contract != isx.support_contract {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX support contracts must match",
        });
    }
    if ksg.support_contract == SupportContract::Unspecified {
        // Keep this explicit here so a PID result cannot combine two identically unspecified
        // estimators and defer the failure to whichever term happens to run first.
        return Err(PidError::SupportContractRequired { context });
    }
    Ok(())
}

fn validate_pid2_config(cfg: &Pid2Config) -> PidResult<()> {
    validate_ksg_isx_consistency("pid2_isx_estimate", &cfg.ksg, &cfg.isx)
}

impl Pid2Result {
    /// Form a checked PID2 atom tuple from already represented MI and redundancy coordinates.
    ///
    /// Write `I1 = est.mi_s1_t`, `I2 = est.mi_s2_t`, `J = est.mi_s1s2_t`, and
    /// `R = est.redundancy_isx`. The synergy field is
    /// `RN-even(exact(J - I1 - I2 + R))`: the four represented binary64 terms are accumulated
    /// exactly and rounded once. This source-order-independent arithmetic contract does not make
    /// the represented estimator coordinates exact or establish their statistical validity.
    ///
    /// # Errors
    ///
    /// Returns [`PidError::NumericalInstability`] if an input is non-finite, an atom is non-finite,
    /// or the represented atoms cannot reconstruct all three supplied MI coordinates within the
    /// fixed inclusive 32-position ordered-binary64 guard. That guard is a project compatibility
    /// policy, not a derived forward-error or relative-accuracy bound. In particular, an expected
    /// positive subnormal with payload 32 and a reconstructed positive zero passes despite complete
    /// relative loss; payload 33 fails. Because the ordered representation distinguishes signed
    /// zero, negative payload 31 passes against positive zero while negative payload 32 fails. This
    /// checked public boundary also protects callers constructing [`Pid2Estimate`] directly.
    pub fn from_estimate(est: Pid2Estimate) -> PidResult<Self> {
        if [est.mi_s1_t, est.mi_s2_t, est.mi_s1s2_t, est.redundancy_isx]
            .iter()
            .any(|value| !value.is_finite())
        {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate input",
            });
        }
        let red = est.redundancy_isx;
        let unq1 = est.mi_s1_t - red;
        let unq2 = est.mi_s2_t - red;
        // Give the represented-input formula one symmetric binary64 meaning. Do not perturb this
        // field to compensate for rounding in the separately computed unique atoms; the identity
        // guard below fails closed when the rounded tuple cannot represent both contracts.
        let syn = exact_binary64_sum([est.mi_s1s2_t, -est.mi_s1_t, -est.mi_s2_t, red]);
        if [red, unq1, unq2, syn]
            .iter()
            .any(|value| !value.is_finite())
        {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate atoms",
            });
        }
        if !pid2_identities_match(&est, red, unq1, unq2, syn) {
            return Err(PidError::NumericalInstability {
                context:
                    "Pid2Result::from_estimate reconstructed coordinates exceed compatibility guard",
            });
        }
        Ok(Self {
            redundancy: red,
            unique_s1: unq1,
            unique_s2: unq2,
            synergy: syn,
        })
    }
}

fn pid2_identities_match(
    estimate: &Pid2Estimate,
    redundancy: f64,
    unique_s1: f64,
    unique_s2: f64,
    synergy: f64,
) -> bool {
    identity_matches(estimate.mi_s1_t, [redundancy, unique_s1])
        && identity_matches(estimate.mi_s2_t, [redundancy, unique_s2])
        && identity_matches(
            estimate.mi_s1s2_t,
            [redundancy, unique_s1, unique_s2, synergy],
        )
}

fn identity_matches<const N: usize>(expected: f64, terms: [f64; N]) -> bool {
    let reconstructed = exact_binary64_sum(terms);
    if !reconstructed.is_finite() {
        return false;
    }
    ordered_float_bits(reconstructed).abs_diff(ordered_float_bits(expected))
        <= PID2_RECONSTRUCTION_MAX_ORDERED_POSITIONS
}

fn ordered_float_bits(value: f64) -> u64 {
    const SIGN: u64 = 1 << 63;
    let bits = value.to_bits();
    if bits & SIGN == 0 {
        bits | SIGN
    } else {
        !bits
    }
}

#[cfg(test)]
mod tests {
    use super::{pid2_exact_reconstruction_work, Pid2Estimate, Pid2Result};

    #[test]
    fn exact_reconstruction_limb_visits_are_fully_charged() {
        // Synergy plus the three identity checks have 4+2+2+4 represented addends and four
        // finalizations. With 34 limbs, the conservative envelope is 12*68 + 4*136 = 1,360.
        assert_eq!(pid2_exact_reconstruction_work(), 1_360);
    }

    #[test]
    fn checked_constructor_rejects_finite_atoms_that_erase_an_mi_identity() {
        let estimate = Pid2Estimate {
            mi_s1_t: 1.0,
            mi_s2_t: 0.0,
            mi_s1s2_t: 0.0,
            redundancy_isx: 1.0e300,
        };

        assert!(Pid2Result::from_estimate(estimate).is_err());
    }
}
