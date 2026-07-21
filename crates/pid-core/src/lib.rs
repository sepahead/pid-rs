#![doc = include_str!("../README.md")]
//!
//! ---
//!
//! `pid-core`: continuous mutual information + shared-exclusions PID (`I^sx_∩`) estimators.
//!
//! # Method provenance labels
//!
//! Source modules use the same labels as the repository method catalog:
//! **PAPER-DEFINED** for a direct implementation of a published method, **PAPER-DERIVED** for an
//! adaptation or composition of published methods, and **PROJECT-DEFINED** for software,
//! diagnostics, or workflow design specified by pid-rs. **EXTERNAL REFERENCE CODE** marks
//! separately maintained comparison software, and **NO IMPLEMENTATION** records an explicit
//! negative capability. These are provenance statements, not claims of new mathematical results.
//! See the repository `METHODS.md` for code paths, feature gates, primary papers, and claim
//! boundaries.
//!
//! The following project-defined infrastructure supports the estimators but is not itself a
//! statistical method:
//!
//! - bounded symmetric-distance storage and deterministic distance evaluation;
//!   Method catalog: diagnostics.distance-matrix
//! - typed estimate identities, warnings, assumptions, and provenance-bearing reports;
//!   Method catalog: software.estimate-report-contracts
//! - resource preflight and cooperative cancellation contracts;
//!   Method catalog: software.resource-cancellation-contracts
//! - typed software identity that keeps API-signature, source, selected-build, forensic-reference,
//!   and explicit non-attestation domains separate.
//!
//! This crate implements:
//! - KSG mutual information (Kraskov et al. 2004) for continuous variables
//! - Wibral-group shared-exclusions redundancy `I^sx_∩(S1,S2;T)` (Makkeh et al. 2021)
//! - Continuous shared-exclusions estimator (Ehrlich et al. 2024)
//! - Experimental 2-source continuous PID atoms derived from MI + `I^sx_∩`, plus incomplete and
//!   separately research-gated full 3-source diagnostics
//! - A hierarchical "fast→slow" screening path for many-source settings
//!
//! # Units
//! All information quantities are reported in **nats** (natural logarithm).
//!
//! # Scientific contract
//! The mathematical object of interest is `I^sx_∩` and its derived PID atoms. Estimators are
//! finite-sample algorithms with failure modes; do not interpret results without first reviewing
//! relevant diagnostics and analytic-reference checks on synthetic systems with known information
//! quantities (see the `exp0` diagnostic binary and the project README).
//!
//! # Estimator cautions (read before using on VLA embeddings)
//! - kNN estimators assume i.i.d. samples; trajectories violate this unless you subsample.
//! - High ambient/intrinsic dimension can collapse kNN geometry (distance concentration).
//! - Strong dependence (near-deterministic mappings) can require prohibitive samples even at low
//!   dimension.
//! - Exact deterministic continuous maps have singular joint laws and infinite mutual information,
//!   outside the finite-MI KSG/PID domain. An explicit observation-noise model defines a different
//!   finite-MI distribution; otherwise use a suitable discrete/mixed estimator.
//! - Relative source units and preprocessing are part of the continuous `I^sx_∩` estimand because
//!   they define how source neighborhoods are compared. Record them and do not pool atoms across
//!   schemes.
//! - Two-source continuous `I^sx_∩` requires equal ambient source dimensions. This is necessary
//!   for comparable small-ball scaling, but does not prove equal intrinsic dimensions or compatible
//!   reference measures.
//! - Full continuous PID3 necessarily mixes singleton and pair-source ambient dimensions and is
//!   absent unless the compile-time `research-mixed-dimension-pid3` feature is enabled. Its runtime
//!   acknowledgement then permits only research reference reproduction with unresolved-theory
//!   status; it is never part of the default stable surface.
//! - `I^sx_∩` (and PID atoms) are **not guaranteed non-negative** under all desiderata; negative
//!   values are possible and must be representable.
#![forbid(unsafe_code)]

#[cfg(feature = "experimental-pipelines")]
mod bootstrap;
#[cfg(feature = "experimental-continuous")]
mod ci;
mod discrete_pid;
mod distance_matrix;
mod error;
mod geometry;
#[cfg(feature = "experimental-hierarchy")]
mod hierarchy;
#[cfg(feature = "experimental-hyperbolic")]
mod hyperbolic;
mod identity;
mod invariants;
#[cfg(feature = "experimental-continuous")]
mod isx;
mod kdtree;
mod ksg;
#[cfg(feature = "experimental-pipelines")]
mod logistic;
mod matrix;
mod metric;
mod nn;
mod par;
#[cfg(feature = "experimental-continuous")]
mod pid2;
#[cfg(feature = "experimental-continuous")]
mod pid3;
#[cfg(feature = "experimental-pipelines")]
mod pipeline;
#[cfg(feature = "experimental-pipelines")]
mod pls;
mod preprocess;
mod quantizer;
mod report;
mod resource;
#[cfg(feature = "experimental-pipelines")]
mod same_sample;
mod stats;
mod support;
mod sxpid;

pub use error::{PidError, PidResult};
pub use identity::{
    software_identity, AttestationStatus, BuildContext, PublicRustApiSignatureIdentity,
    PublicRustApiSignatureScope, PublicRustApiSignatureStatus, ReferenceArtifactIdentity,
    ReferenceArtifactKind, ReferenceArtifactRole, SoftwareIdentity, SourceIdentity,
    SourceUnavailableReason, WorkingTreeScope, WorkingTreeState,
};
pub use matrix::{
    concat_horiz, concat_horiz_with_budget, DiscreteMatOwned, DiscreteMatRef, MatOwned, MatRef,
};
pub use metric::Metric;
pub use resource::{
    CancellationToken, ResourceBudget, ResourceEstimate, DEFAULT_MAX_BYTES,
    DEFAULT_MAX_OPERATIONS_HINT, DEFAULT_MAX_PAIRWISE_DISTANCES,
};

/// Default 0.9 review estimator surface.
///
/// The default build deliberately contains only empirical categorical estimators, explicitly
/// fitted quantized estimands, the Williams--Beer `I_min` comparator, and report-first
/// conditional Euclidean KSG. Continuous shared exclusions and the research pipelines live under
/// the default-off `experimental` namespace.
pub mod stable {
    /// Direct shared-exclusions PID evaluation on an empirical categorical PMF.
    pub mod categorical {
        pub use crate::sxpid::{
            discrete_sxpid2, discrete_sxpid2_averaged, discrete_sxpid2_averaged_with_budget,
            discrete_sxpid2_averaged_with_budget_and_cancellation,
            discrete_sxpid2_resource_estimate, discrete_sxpid2_with_budget, discrete_sxpid3,
            discrete_sxpid3_averaged, discrete_sxpid3_averaged_with_budget,
            discrete_sxpid3_averaged_with_budget_and_cancellation,
            discrete_sxpid3_resource_estimate, discrete_sxpid3_with_budget, discrete_sxpid_n,
            discrete_sxpid_n_averaged, discrete_sxpid_n_averaged_with_budget,
            discrete_sxpid_n_averaged_with_budget_and_cancellation,
            discrete_sxpid_n_resource_estimate, discrete_sxpid_n_with_budget,
            DiscreteInputEncoding, DiscreteInputMetadata, DiscreteSxPid2Result,
            DiscreteSxPid3Result, DiscreteSxPidNResult, EmpiricalPmfDiagnostics, SxAtomAggregation,
            SxAtomContextRequirement, SxAtomCoordinateSemantics, SxAtomDecompositionMeasure,
            SxAtomEvidentialScope, SxAtomInterpretation, SxAveragedAtom,
            SxInterpretationGuardOrigin, SxPointwise2, SxPointwise3, SxPointwiseAtom, SxPointwiseN,
            SxUnsupportedInference,
        };
    }

    /// Explicitly quantized estimands. Bin fitting is part of the estimand and must use training
    /// rows only in an inferential workflow.
    pub mod quantized {
        pub use crate::quantizer::{
            EqualWidthQuantizer, OutOfRangePolicy, QuantizationReport, QuantizedData,
            QuantizerConfig,
        };
        pub use crate::sxpid::{
            fitted_quantized_sxpid2, fitted_quantized_sxpid2_resource_estimate,
            fitted_quantized_sxpid2_with_budget,
            fitted_quantized_sxpid2_with_budget_and_cancellation, fitted_quantized_sxpid3,
            fitted_quantized_sxpid3_resource_estimate, fitted_quantized_sxpid3_with_budget,
            fitted_quantized_sxpid_n, fitted_quantized_sxpid_n_resource_estimate,
            fitted_quantized_sxpid_n_with_budget, FittedQuantizedSxPid2Result,
            FittedQuantizedSxPid3Result, FittedQuantizedSxPidNResult,
        };
    }

    /// Williams--Beer `I_min` on an explicit empirical PMF.
    pub mod imin {
        pub use crate::discrete_pid::{
            imin_pid2, imin_pid2_quantized, imin_pid2_quantized_resource_estimate,
            imin_pid2_quantized_with_budget, imin_pid2_resource_estimate, imin_pid2_with_budget,
            imin_pid2_with_budget_and_cancellation, imin_pid3, imin_pid3_quantized,
            imin_pid3_quantized_resource_estimate, imin_pid3_quantized_with_budget,
            imin_pid3_resource_estimate, imin_pid3_with_budget, IminEmpiricalPmfDiagnostics,
            IminInputEncoding, IminInputMetadata, IminPid2Result, IminPid3Atom, IminPid3Result,
        };
    }

    /// Conditional, report-first Euclidean KSG mutual information.
    pub mod continuous {
        pub use crate::ksg::{
            ksg_k_trajectory, ksg_mi_report, ksg_mi_report_with_budget,
            ksg_mi_report_with_budget_and_cancellation, ksg_report_resource_estimate,
            ksg_resource_estimate, ksg_resource_estimate_for_threads, ksg_sample_size_trajectory,
            KsgConfig, KsgCountQuantiles, KsgGeometryModel, KsgLocalDiagnosticsSummary,
            KsgMethodStatus, KsgMiReport, KsgNeighborBackend, KsgProvenance, KsgReportWarning,
            KsgTrajectoryReport, KsgValueQuantiles, NegativeHandling,
        };
        pub use crate::report::{
            Assumption, AssumptionLedgerEntry, AssumptionState, EstimandIdentity, EstimateReport,
            InformationUnit, ProvenanceHashes, ScientificStatus, WarningCode,
        };
        pub use crate::support::{BoundaryModel, SupportContract};
    }

    /// Unsupervised transforms whose fitted state can be reused on held-out rows.
    pub mod preprocessing {
        pub use crate::preprocess::{
            ConstantColumnPolicy, HashProjector, PcaProjector, Standardizer,
        };
    }
}

/// General diagnostics. Their outputs are warnings and measurements, never proofs that estimator
/// assumptions hold for a population law.
pub mod diagnostics {
    pub use crate::distance_matrix::{
        symmetric_distance_resources, symmetric_distance_resources_for, symmetric_distances,
        symmetric_distances_with_budget, symmetric_distances_with_budget_and_cancellation,
        SymmetricDistanceMatrix,
    };
    pub use crate::geometry::{
        distance_concentration_resource_estimate, distance_concentration_stats,
        distance_concentration_stats_with_budget,
        distance_concentration_stats_with_budget_and_cancellation,
        intrinsic_dimension_levina_bickel, intrinsic_dimension_multi_k, intrinsic_dimension_report,
        intrinsic_dimension_report_with_cancellation, intrinsic_dimension_resource_estimate,
        sampled_four_point_delta_summary, sampled_four_point_delta_summary_with_budget,
        sampled_four_point_delta_summary_with_budget_and_cancellation,
        sampled_four_point_resource_estimate, DistanceConcentrationConfig,
        DistanceConcentrationStats, HyperbolicityConfig, IntrinsicDimConfig,
        IntrinsicDimensionReport, IntrinsicDimensionTrajectory, SampledFourPointDeltaSummary,
    };
    pub use crate::invariants::{
        average_degree_of_redundancy, average_degree_of_redundancy_with_policy,
        average_degree_of_vulnerability, average_degree_of_vulnerability_with_policy,
        co_information_pairwise_discrete, co_information_pairwise_discrete_resource_estimate,
        co_information_pairwise_discrete_with_budget, entropy_discrete,
        entropy_discrete_resource_estimate, entropy_discrete_with_budget, joint_entropy_discrete,
        joint_entropy_discrete_resource_estimate, joint_entropy_discrete_with_budget,
        o_information_discrete, o_information_discrete_resource_estimate,
        o_information_discrete_with_budget, red_degree_discrete,
        red_degree_discrete_resource_estimate, red_degree_discrete_with_budget,
        vul_degree_discrete, vul_degree_discrete_resource_estimate,
        vul_degree_discrete_with_budget, NormalizedInvariantPolicy, NormalizedInvariantReport,
        NormalizedInvariantStatus, NormalizedInvariantUnit,
    };
    pub use crate::support::{
        continuous_input_diagnostics, continuous_input_diagnostics_resource_estimate,
        continuous_input_diagnostics_with_budget,
        continuous_input_diagnostics_with_budget_and_cancellation,
        continuous_joint_shell_diagnostics, continuous_joint_shell_diagnostics_with_budget,
        continuous_joint_shell_diagnostics_with_budget_and_cancellation,
        continuous_joint_shell_resource_estimate, ContinuousInputDiagnostics,
        CoordinateCardinalityDiagnostics, DistanceQuantiles, NeighborShellDiagnostics,
    };
}

/// Default-off research APIs whose software availability is not a scientific-validity claim.
#[cfg(any(
    feature = "experimental-continuous",
    feature = "experimental-hyperbolic",
    feature = "experimental-heuristics",
    feature = "experimental-hierarchy",
    feature = "research-mixed-dimension-pid3",
    feature = "experimental-pipelines"
))]
pub mod experimental {
    /// Formula-labelled heuristic baselines. These do not estimate the paper-defined continuous
    /// shared-exclusions functional and are available only with `experimental-heuristics`.
    #[cfg(feature = "experimental-heuristics")]
    pub mod isx_heuristics {
        use crate::isx::{isx_redundancy, IsxConfig, IsxMethod};
        use crate::{MatRef, PidResult};

        pub fn heuristic_sketch_baseline(
            s1: MatRef<'_>,
            s2: MatRef<'_>,
            target: MatRef<'_>,
            config: &IsxConfig,
        ) -> PidResult<f64> {
            let mut config = config.clone();
            config.method = IsxMethod::HeuristicSketch;
            isx_redundancy(s1, s2, target, &config)
        }

        pub fn local_mi_minimum_baseline(
            s1: MatRef<'_>,
            s2: MatRef<'_>,
            target: MatRef<'_>,
            config: &IsxConfig,
        ) -> PidResult<f64> {
            let mut config = config.clone();
            config.method = IsxMethod::LocalMinKsg;
            isx_redundancy(s1, s2, target, &config)
        }

        pub fn unweighted_local_mi_inclusion_exclusion_baseline(
            s1: MatRef<'_>,
            s2: MatRef<'_>,
            target: MatRef<'_>,
            config: &IsxConfig,
        ) -> PidResult<f64> {
            let mut config = config.clone();
            config.method = IsxMethod::DisjunctionFromLocalMi;
            isx_redundancy(s1, s2, target, &config)
        }
    }

    /// Restricted-domain continuous shared exclusions and derived incomplete/PID2 diagnostics.
    #[cfg(feature = "experimental-continuous")]
    pub mod continuous {
        pub use crate::ci::{
            co_information_pairwise_report, co_information_pairwise_report_resource_estimate,
            co_information_pairwise_report_resource_estimate_for_threads,
            co_information_pairwise_report_with_budget, co_information_triplet_report,
            co_information_triplet_report_resource_estimate,
            co_information_triplet_report_resource_estimate_for_threads,
            co_information_triplet_report_with_budget, CoInformationCancellationDiagnostics,
            CoInformationConditioningStatus, CoInformationReportWarning,
            PairwiseCoInformationReport, TripletCoInformationReport,
        };
        pub use crate::isx::{
            isx_redundancy_report, isx_report_resource_estimate, isx_resource_estimate,
            isx_resource_estimate_for_threads, IsxConfig, IsxLocalDiagnosticsSummary, IsxMethod,
            IsxProvenance, IsxReport,
        };
        pub use crate::ksg::KsgConfig;
        pub use crate::pid2::{
            pid2_cross_fit_resource_estimate, pid2_isx, pid2_isx_cross_fit_reports,
            pid2_isx_cross_fit_reports_with_budget, pid2_isx_estimate,
            pid2_isx_estimate_with_budget, pid2_isx_report, pid2_isx_report_with_budget,
            pid2_isx_split_sample_report, pid2_isx_split_sample_report_with_budget,
            pid2_isx_with_budget, pid2_report_resource_estimate, pid2_resource_estimate,
            pid2_resource_estimate_for_threads, Pid2AtomConditioning, Pid2ConditioningStatus,
            Pid2Config, Pid2CrossFitAggregation, Pid2CrossFitFold, Pid2CrossFitFoldReport,
            Pid2CrossFitReport, Pid2Estimate, Pid2JointDiagnostics, Pid2MethodStatus,
            Pid2Provenance, Pid2Report, Pid2ReportWarning, Pid2Result,
        };
        pub use crate::pid3::{
            incomplete_pid3_diagnostic, incomplete_pid3_diagnostic_with_budget,
            incomplete_pid3_report, incomplete_pid3_report_with_budget,
            incomplete_pid3_resource_estimate, incomplete_pid3_resource_estimate_for_threads,
            Antichain3, IncompletePid3Atom, IncompletePid3Diagnostic, IncompletePid3Redundancy,
            IncompletePid3Report, IncompletePid3Status, Pid3Config, Pid3Provenance,
        };

        /// Unreported numeric research paths. These deliberately sit below a conspicuous name so
        /// they cannot be mistaken for the report-first publication API.
        pub mod raw_scalars {
            use crate::{MatRef, PidResult};

            pub use crate::ci::{
                co_information_pairwise, co_information_pairwise_resource_estimate,
                co_information_pairwise_resource_estimate_for_threads,
                co_information_pairwise_with_budget, co_information_triplet,
                co_information_triplet_resource_estimate,
                co_information_triplet_resource_estimate_for_threads,
                co_information_triplet_with_budget,
            };

            use crate::isx::IsxConfig;
            use crate::ksg::KsgConfig;

            pub fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, config: &KsgConfig) -> PidResult<f64> {
                crate::ksg::ksg_mi(x, y, config)
            }

            pub fn ksg_local_mi_terms(
                x: MatRef<'_>,
                y: MatRef<'_>,
                config: &KsgConfig,
            ) -> PidResult<Vec<f64>> {
                crate::ksg::ksg_local_mi_terms(x, y, config)
            }

            pub fn ksg_mi_concat_xy(
                x: MatRef<'_>,
                y: MatRef<'_>,
                target: MatRef<'_>,
                config: &KsgConfig,
            ) -> PidResult<f64> {
                crate::ksg::ksg_mi_concat_xy(x, y, target, config)
            }

            pub fn isx_redundancy(
                source1: MatRef<'_>,
                source2: MatRef<'_>,
                target: MatRef<'_>,
                config: &IsxConfig,
            ) -> PidResult<f64> {
                crate::isx::isx_redundancy(source1, source2, target, config)
            }
        }
    }

    /// Full mixed-dimensional continuous PID3 reference reproduction.
    #[cfg(feature = "research-mixed-dimension-pid3")]
    pub mod mixed_dimension_pid3 {
        pub use crate::pid3::{
            pid3_isx, pid3_isx_report, pid3_isx_report_with_budget, pid3_isx_with_budget,
            pid3_resource_estimate, pid3_resource_estimate_for_threads, Antichain3, Pid3Atom,
            Pid3Config, Pid3MethodStatus, Pid3Provenance, Pid3Redundancy, Pid3Report, Pid3Result,
        };
    }

    /// Manifold/hyperbolic research utilities and KSG reporting path.
    #[cfg(feature = "experimental-hyperbolic")]
    pub mod hyperbolic {
        pub use crate::distance_matrix::{
            hyperbolic_symmetric_distance_resources, hyperbolic_symmetric_distance_resources_for,
            hyperbolic_symmetric_distances, hyperbolic_symmetric_distances_with_budget,
            hyperbolic_symmetric_distances_with_budget_and_cancellation, SymmetricDistanceMatrix,
        };
        pub use crate::geometry::{
            hyperbolic_distance_concentration_resource_estimate,
            hyperbolic_distance_concentration_stats,
            hyperbolic_distance_concentration_stats_with_budget,
            hyperbolic_distance_concentration_stats_with_budget_and_cancellation,
            hyperbolic_intrinsic_dimension_levina_bickel, hyperbolic_intrinsic_dimension_multi_k,
            hyperbolic_intrinsic_dimension_report,
            hyperbolic_intrinsic_dimension_report_with_cancellation,
            hyperbolic_intrinsic_dimension_resource_estimate,
            hyperbolic_sampled_four_point_delta_summary,
            hyperbolic_sampled_four_point_delta_summary_with_budget,
            hyperbolic_sampled_four_point_delta_summary_with_budget_and_cancellation,
            hyperbolic_sampled_four_point_resource_estimate, DistanceConcentrationStats,
            HyperbolicDistanceConcentrationConfig, HyperbolicFourPointConfig,
            HyperbolicIntrinsicDimConfig, HyperbolicIntrinsicDimensionReport,
            HyperbolicIntrinsicDimensionTrajectory, SampledFourPointDeltaSummary,
        };
        pub use crate::hyperbolic::{
            hyperbolic_distance_lorentz, lorentz_dot, lorentz_to_poincare,
            lorentz_to_poincare_resource_estimate, lorentz_to_poincare_with_budget,
            poincare_to_lorentz, poincare_to_lorentz_resource_estimate,
            poincare_to_lorentz_with_budget, HyperbolicCurvature, HyperbolicMetric,
        };
        pub use crate::ksg::{
            hyperbolic_ksg_k_trajectory, hyperbolic_ksg_mi_report,
            hyperbolic_ksg_mi_report_with_budget,
            hyperbolic_ksg_mi_report_with_budget_and_cancellation,
            hyperbolic_ksg_report_resource_estimate, hyperbolic_ksg_sample_size_trajectory,
            HyperbolicKsgConfig, HyperbolicKsgGeometryModel, HyperbolicKsgMiReport,
            HyperbolicKsgReportWarning, HyperbolicKsgTrajectoryReport, HyperbolicSupportContract,
        };
        pub use crate::support::{
            hyperbolic_continuous_input_diagnostics,
            hyperbolic_continuous_input_diagnostics_resource_estimate,
            hyperbolic_continuous_input_diagnostics_with_budget,
            hyperbolic_continuous_input_diagnostics_with_budget_and_cancellation,
            hyperbolic_continuous_joint_shell_diagnostics,
            hyperbolic_continuous_joint_shell_diagnostics_with_budget,
            hyperbolic_continuous_joint_shell_diagnostics_with_budget_and_cancellation,
            hyperbolic_continuous_joint_shell_resource_estimate, ContinuousInputDiagnostics,
            NeighborShellDiagnostics,
        };
    }

    /// Exploratory hierarchy screening.
    #[cfg(feature = "experimental-hierarchy")]
    pub mod hierarchy {
        pub use crate::hierarchy::{
            hierarchical_pairwise, hierarchical_pairwise_resource_estimate,
            hierarchical_pairwise_resource_estimate_for_threads, hierarchical_pairwise_split,
            hierarchical_pairwise_split_resource_estimate_for_threads,
            hierarchical_pairwise_split_with_budget, hierarchical_pairwise_with_budget,
            hierarchical_triplet, hierarchical_triplet_resource_estimate,
            hierarchical_triplet_resource_estimate_for_threads, hierarchical_triplet_with_budget,
            HierarchicalConfig, HierarchicalPairwiseReport, HierarchicalTriplet,
            HierarchySelectionProvenance, HierarchySplitIdentity, PairSelection, PairwiseScreen,
        };
    }

    /// Target-adaptive and uncalibrated inference pipelines.
    #[cfg(feature = "experimental-pipelines")]
    pub mod pipelines {
        pub use crate::bootstrap::{
            block_bootstrap, block_bootstrap_paired, block_bootstrap_paired_resource_estimate,
            block_bootstrap_paired_with_budget, block_bootstrap_paired_with_cancellation,
            block_bootstrap_resource_estimate, block_bootstrap_with_budget,
            block_bootstrap_with_cancellation, BlockLengthSelection,
            BlockResamplingAlgorithmRevision, BlockResamplingProvenance, BootstrapConfig,
            BootstrapReplicateOutcome, BootstrapReplicateStatus, BootstrapResult,
            CancellationToken, ResamplingDependence, ResamplingDistributionSummary,
            ResamplingValidityDeclaration, StatisticCallbackDeclaration,
        };
        pub use crate::discrete_pid::{
            same_sample_quantized_imin_pid2 as exploratory_same_sample_quantized_imin_pid2,
            same_sample_quantized_imin_pid3 as exploratory_same_sample_quantized_imin_pid3,
        };
        pub use crate::logistic::{LogisticRegression, LogisticRegressionConfig};
        pub use crate::pipeline::{
            benjamini_hochberg, benjamini_yekutieli, bootstrap_quantized_sxpid2,
            bootstrap_quantized_sxpid2_resource_estimate, bootstrap_quantized_sxpid2_with_budget,
            bootstrap_rows_stats, bootstrap_rows_stats_resource_estimate,
            bootstrap_rows_stats_with_budget, bootstrap_rows_stats_with_cancellation,
            permutation_pid3, permutation_pid3_resource_estimate,
            permutation_pid3_under_null_with_budget, permutation_pid3_under_null_with_cancellation,
            permutation_pid3_with, permutation_pid3_with_budget, permutation_pid3_with_tail,
            permutation_pid3_with_tail_and_budget, permutation_rows_pvalue,
            permutation_rows_pvalue_resource_estimate,
            permutation_rows_pvalue_under_null_with_budget,
            permutation_rows_pvalue_under_null_with_cancellation, permutation_rows_pvalue_with,
            permutation_rows_pvalue_with_budget, permutation_rows_pvalue_with_tail,
            permutation_rows_pvalue_with_tail_and_budget, pls_cv_select_components,
            pls_cv_select_components_resource_estimate, pls_cv_select_components_with_budget,
            pls_cv_select_components_with_cancellation, pls_project_then_discrete_pid3,
            pls_project_then_pid3, screen_pid2_pairs, screen_pid2_pairs_resource_estimate,
            screen_pid2_pairs_with_budget, MultipleTestingAdjustment, MultipleTestingMethod,
            PermutationAlgorithmRevision, PermutationCalibration, PermutationFamily,
            PermutationNull, PermutationNullAssumption, PermutationPid3Atom, PermutationPid3Result,
            PermutationReplicateOutcome, PermutationReplicateStatus, PermutationScheme,
            PermutationTail, Pid2ScreenEntry, PlsCvCandidateOutcome, PlsCvCandidateStatus,
            PlsCvFoldOutcome, PlsCvFoldStatus, PlsCvResult, PlsDiscretePid3Config,
            PlsDiscretePid3Result, PlsPid3Config, PlsPid3Result, QuantizedSxPid2BootstrapResult,
            RowBootstrapResult, RowBootstrapStat, RowPermutationStat, RowResampleOutcome,
            RowResampleScheme, RowResampleStatus, SxAveragedAtomBootstrapInterpretation,
            SxAveragedAtomBootstrapStat, SxBootstrapEvidentialScope, SxBootstrapSummaryComponent,
            SxBootstrapSummaryScope, SxPid2BootstrapAtomSummaries, SxPid2BootstrapSummaryStatus,
        };
        pub use crate::pls::PlsProjector;
        pub use crate::preprocess::Jitter;
        pub use crate::same_sample::{
            ExploratorySameSampleQuantizedResult, SameSampleEqualWidthProvenance,
        };
        pub use crate::sxpid::{
            quantized_sxpid2 as exploratory_same_sample_quantized_sxpid2,
            quantized_sxpid3 as exploratory_same_sample_quantized_sxpid3,
            quantized_sxpid_n as exploratory_same_sample_quantized_sxpid_n,
        };
    }
}
