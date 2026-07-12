use serde::Serialize;

use crate::resource::{ResourceBudget, ResourceEstimate};

/// Scientific maturity of an estimator output. This is intentionally not a Boolean validity flag.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum ScientificStatus {
    EmpiricalPmf,
    QuantizedEstimand,
    ConditionalContinuous,
    ExperimentalRestrictedDomain,
    IncompleteDiagnostic,
    ResearchOnly,
    Unsupported,
}

/// Unit in which an information quantity is reported.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum InformationUnit {
    Nats,
}

/// Versioned identity of the mathematical definition and finite-sample algorithm.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct EstimandIdentity {
    pub family: &'static str,
    pub definition_revision: &'static str,
    pub estimator_revision: &'static str,
    pub units: InformationUnit,
    pub metric: &'static str,
    pub source_gauge: Option<&'static str>,
}

/// Population or workflow obligation recorded in every continuous report.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Assumption {
    RegularContinuousOrManifoldLaw,
    FixedLocalDimension,
    RegularFiniteDensity,
    FiniteMutualInformation,
    DeclaredSamplingDependence,
    UniqueKthNeighborShell,
    LocalNeighborhoods,
    CommonBranchLeadingScale,
    LowerOrderBranchIntersections,
    FixedPreprocessingAndMetric,
    AdequateSampleSize,
    AdaptiveTransformsFitOutsideEvaluationData,
}

/// Evidence state for an assumption. Passing sample checks never upgrades an assumption to proof.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum AssumptionState {
    AssumptionsDeclared,
    FiniteSampleChecksPassed,
    WarningPresent,
    UnsupportedObservedCondition,
    NotEvaluated,
    ResearchOnly,
}

/// One machine-readable assumption-ledger row.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct AssumptionLedgerEntry {
    pub assumption: Assumption,
    pub state: AssumptionState,
    pub note: &'static str,
}

/// Stable warning codes shared by report-first APIs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum WarningCode {
    DiagnosticsDoNotProvePopulationAssumptions,
    BoundaryModelUnknown,
    DependenceDiagnosticsNotEvaluated,
    KTrajectoryNotEvaluated,
    SampleSizeTrajectoryNotEvaluated,
    TransformationSensitivityNotEvaluated,
    ObservationNoiseSensitivityNotEvaluated,
    ExperimentalEstimator,
    IncompleteDecomposition,
}

/// Content hashes and split identifiers that make a report traceable to its inputs and fitted
/// workflow state.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct ProvenanceHashes {
    pub input_hashes_sha256: Vec<[u8; 32]>,
    pub preprocessing_hash_sha256: [u8; 32],
    pub observation_model_hash_sha256: [u8; 32],
    pub training_split_id: Option<String>,
    pub evaluation_split_id: Option<String>,
}

/// Generic report envelope for new stable APIs.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct EstimateReport<T> {
    pub value: T,
    pub estimand: EstimandIdentity,
    pub status: ScientificStatus,
    pub assumptions: Vec<AssumptionLedgerEntry>,
    pub provenance: ProvenanceHashes,
    pub resources: ResourceEstimate,
    pub budget: ResourceBudget,
    pub warnings: Vec<WarningCode>,
}
