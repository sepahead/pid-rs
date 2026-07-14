"""Typed 0.9 review API proposed for 1.0; no 1.x compatibility promise is made."""

from types import ModuleType
from typing import Final, Self, Sequence, final

import numpy as np
import numpy.typing as npt

_FloatMatrix = npt.NDArray[np.float64]
_IntMatrix = npt.NDArray[np.int64]

__version__: str
SCIENTIFIC_SCOPE: Final[str]
__all__ = [
    "__version__",
    "SCIENTIFIC_SCOPE",
    "PidRsError",
    "PidInputError",
    "PidResourceError",
    "PidNumericalError",
    "PidUnsupportedError",
    "PidCancelledError",
    "ResourceBudget",
    "ResourceEstimate",
    "DistanceQuantiles",
    "NeighborShellDiagnostics",
    "CoordinateCardinality",
    "ContinuousInputReport",
    "DistanceConcentrationReport",
    "IntrinsicDimensionReport",
    "ValueQuantiles",
    "CountQuantiles",
    "KsgLocalDiagnostics",
    "AssumptionLedgerEntry",
    "EstimandIdentity",
    "Provenance",
    "MiReport",
    "SxAtom",
    "EmpiricalPmfDiagnostics",
    "SxPid2Result",
    "Antichain",
    "AntichainAtom",
    "SxPidLatticeResult",
    "IminPid2Result",
    "QuantizationReport",
    "QuantizedData",
    "EqualWidthQuantizer",
    "QuantizedSxPid2Result",
    "compute_mi_report",
    "compute_categorical_sxpid2",
    "compute_categorical_sxpid3",
    "compute_categorical_sxpid",
    "compute_categorical_imin_pid2",
    "compute_fitted_quantized_sxpid2",
    "diagnose_continuous_input",
    "distance_concentration_report",
    "intrinsic_dimension_report",
    "stable",
    "diagnostics",
]


class PidRsError(Exception):
    code: str
    fields: dict[str, str]


class PidInputError(PidRsError): ...
class PidResourceError(PidRsError): ...
class PidNumericalError(PidRsError): ...
class PidUnsupportedError(PidRsError): ...
class PidCancelledError(PidRsError): ...


@final
class ResourceBudget:
    @property
    def max_bytes(self) -> int: ...
    @property
    def max_pairwise_distances(self) -> int: ...
    @property
    def max_operations_hint(self) -> int: ...
    @property
    def max_threads(self) -> int: ...
    def __new__(
        cls,
        max_bytes: int = ...,
        max_pairwise_distances: int = ...,
        max_operations_hint: int = ...,
        max_threads: int = ...,
    ) -> Self: ...


@final
class ResourceEstimate:
    estimated_bytes: int
    pairwise_distances: int
    operations_hint: int


@final
class DistanceQuantiles:
    min: float
    p10: float
    median: float
    p90: float
    p99: float
    max: float


@final
class NeighborShellDiagnostics:
    query_count: int
    zero_radius_queries: int
    ambiguous_positive_shell_queries: int
    kth_radius: DistanceQuantiles


@final
class CoordinateCardinality:
    coordinate: int
    unique_values: int
    tied_groups: int
    repeated_observations: int
    max_multiplicity: int
    minimum_positive_spacing: float | None
    maximum_positive_spacing: float | None
    unrepresentable_positive_spacings: int


@final
class ContinuousInputReport:
    n_samples: int
    ambient_dimension: int
    unique_rows: int
    tied_row_groups: int
    repeated_rows: int
    max_row_multiplicity: int
    coordinates: tuple[CoordinateCardinality, ...]
    marginal_shells: NeighborShellDiagnostics
    status: str
    warnings: list[str]


@final
class DistanceConcentrationReport:
    n_samples: int
    ambient_dimension: int
    metric: str
    pairwise_count: int
    pairwise_min: float
    pairwise_max: float
    pairwise_mean: float
    pairwise_std: float
    pairwise_cv: float
    nn_min: float
    nn_max: float
    nn_mean: float
    nn_std: float
    nn_cv: float
    nn_over_pairwise_mean: float
    warnings: list[str]


@final
class IntrinsicDimensionReport:
    estimate: float
    n_samples: int
    ambient_dimension: int
    k: int
    metric: str
    status: str
    warnings: list[str]


@final
class ValueQuantiles:
    min: float
    p10: float
    median: float
    p90: float
    p99: float
    max: float


@final
class CountQuantiles:
    min: int
    p10: int
    median: int
    p90: int
    p99: int
    max: int


@final
class KsgLocalDiagnostics:
    joint_radius: ValueQuantiles
    x_marginal_count: CountQuantiles
    y_marginal_count: CountQuantiles
    local_mi_nats: ValueQuantiles


@final
class AssumptionLedgerEntry:
    assumption: str
    state: str
    note: str


@final
class EstimandIdentity:
    family: str
    definition_revision: str
    estimator_revision: str
    units: str
    metric: str
    source_gauge: str | None


@final
class Provenance:
    preprocessing_description: str
    observation_model_description: str
    dependence_model_description: str
    input_hashes_sha256: list[str]
    preprocessing_hash_sha256: str
    observation_model_hash_sha256: str
    training_split_id: str | None
    evaluation_split_id: str | None


@final
class MiReport:
    value_nats: float
    signed_value_nats: float
    status: str
    support_assertion: str
    n_samples: int
    x_dimension: int
    y_dimension: int
    k: int
    backend: str
    method_status: str
    geometry_model: str
    estimated_pairwise_distances: int
    estimated_bytes: int
    estimand: EstimandIdentity
    provenance: Provenance
    assumption_ledger: tuple[AssumptionLedgerEntry, ...]
    x_diagnostics: ContinuousInputReport
    y_diagnostics: ContinuousInputReport
    joint_shells: NeighborShellDiagnostics
    local_diagnostics: KsgLocalDiagnostics
    resource_estimate: ResourceEstimate
    resource_budget: ResourceBudget
    warning_codes: list[str]
    warnings: list[str]


@final
class SxAtom:
    informative_nats: float
    misinformative_nats: float
    net_nats: float


@final
class EmpiricalPmfDiagnostics:
    sample_count: int
    observed_joint_states: int
    singleton_joint_states: int
    low_count_joint_states: int
    minimum_observed_count: int
    maximum_observed_count: int
    observed_coverage_indicator: float
    population_caveat: str


@final
class SxPid2Result:
    redundancy: SxAtom
    unique_s1: SxAtom
    unique_s2: SxAtom
    synergy: SxAtom
    mi_s1_t_nats: float
    mi_s2_t_nats: float
    mi_s1s2_t_nats: float
    input_encoding: str
    observed_cardinalities: list[int]
    pointwise_included: bool
    empirical_pmf: EmpiricalPmfDiagnostics
    status: str
    warnings: list[str]


@final
class Antichain:
    sets: tuple[int, ...]
    def __len__(self) -> int: ...


@final
class AntichainAtom:
    antichain: Antichain
    atom: SxAtom


@final
class SxPidLatticeResult:
    n_sources: int
    entries: tuple[AntichainAtom, ...]
    joint_mi_nats: float
    subset_mis_nats: list[float]
    input_encoding: str
    observed_cardinalities: list[int]
    pointwise_included: bool
    empirical_pmf: EmpiricalPmfDiagnostics
    status: str
    warnings: list[str]
    def atom(self, sets: Sequence[int]) -> SxAtom | None: ...


@final
class IminPid2Result:
    redundancy_nats: float
    unique_s1_nats: float
    unique_s2_nats: float
    synergy_nats: float
    mi_s1_t_nats: float
    mi_s2_t_nats: float
    mi_s1s2_t_nats: float
    input_encoding: str
    observed_cardinalities: list[int]
    empirical_pmf: EmpiricalPmfDiagnostics
    status: str
    warnings: list[str]


@final
class QuantizationReport:
    bin_edges: tuple[tuple[float, ...], ...]
    training_input_hash_sha256: str | None
    transform_input_hash_sha256: str
    categorical_output_hash_sha256: str
    out_of_range_policy: str
    preprocessing_description: str
    n_rows: int
    n_features: int
    num_bins: int
    nominal_joint_cardinality: int | None
    observed_joint_cardinality: int
    empty_joint_cells: int | None
    low_count_joint_cells: int
    minimum_observed_cell_count: int
    maximum_observed_cell_count: int
    estimand: str
    warnings: list[str]


@final
class QuantizedData:
    values: _IntMatrix
    report: QuantizationReport


@final
class EqualWidthQuantizer:
    @staticmethod
    def fit(
        training_data: _FloatMatrix,
        num_bins: int,
        *,
        preprocessing_description: str,
        out_of_range_policy: str = "error",
        low_count_threshold: int = 5,
        record_training_data_hash: bool = True,
        budget: ResourceBudget | None = None,
    ) -> EqualWidthQuantizer: ...
    @property
    def num_bins(self) -> int: ...
    @property
    def n_features(self) -> int: ...
    @property
    def training_input_hash_sha256(self) -> str | None: ...
    @property
    def preprocessing_description(self) -> str: ...
    @property
    def out_of_range_policy(self) -> str: ...
    @property
    def resource_budget(self) -> ResourceBudget: ...
    @property
    def edges(self) -> tuple[tuple[float, ...], ...]: ...
    def transform(
        self, data: _FloatMatrix, *, budget: ResourceBudget | None = None
    ) -> QuantizedData: ...


@final
class QuantizedSxPid2Result:
    pid: SxPid2Result
    source1_quantization: QuantizationReport
    source2_quantization: QuantizationReport
    target_quantization: QuantizationReport


def compute_mi_report(
    x: _FloatMatrix,
    y: _FloatMatrix,
    k: int = 3,
    *,
    support_assertion: str,
    preprocessing_description: str,
    observation_model_description: str,
    dependence_model_description: str,
    training_split_id: str | None = None,
    evaluation_split_id: str | None = None,
    budget: ResourceBudget | None = None,
) -> MiReport: ...


def compute_categorical_sxpid2(
    s1: _IntMatrix,
    s2: _IntMatrix,
    target: _IntMatrix,
    *,
    budget: ResourceBudget | None = None,
) -> SxPid2Result: ...


def compute_categorical_sxpid3(
    s0: _IntMatrix,
    s1: _IntMatrix,
    s2: _IntMatrix,
    target: _IntMatrix,
    *,
    budget: ResourceBudget | None = None,
) -> SxPidLatticeResult: ...


def compute_categorical_sxpid(
    sources: Sequence[_IntMatrix],
    target: _IntMatrix,
    *,
    budget: ResourceBudget | None = None,
) -> SxPidLatticeResult: ...


def compute_categorical_imin_pid2(
    s1: _IntMatrix,
    s2: _IntMatrix,
    target: _IntMatrix,
    *,
    budget: ResourceBudget | None = None,
) -> IminPid2Result: ...


def compute_fitted_quantized_sxpid2(
    s1: _FloatMatrix,
    s2: _FloatMatrix,
    target: _FloatMatrix,
    s1_quantizer: EqualWidthQuantizer,
    s2_quantizer: EqualWidthQuantizer,
    target_quantizer: EqualWidthQuantizer,
    *,
    budget: ResourceBudget | None = None,
) -> QuantizedSxPid2Result: ...


def diagnose_continuous_input(
    x: _FloatMatrix, k: int = 10, *, budget: ResourceBudget | None = None
) -> ContinuousInputReport: ...


def distance_concentration_report(
    x: _FloatMatrix, *, budget: ResourceBudget | None = None
) -> DistanceConcentrationReport: ...


def intrinsic_dimension_report(
    x: _FloatMatrix, k: int = 10, *, budget: ResourceBudget | None = None
) -> IntrinsicDimensionReport: ...


# The extension registers true submodules at import time. These module protocols preserve
# autocomplete without pretending the default wheel contains an experimental namespace.
class _StableModule(ModuleType):
    def compute_mi_report(
        self,
        x: _FloatMatrix,
        y: _FloatMatrix,
        k: int = 3,
        *,
        support_assertion: str,
        preprocessing_description: str,
        observation_model_description: str,
        dependence_model_description: str,
        training_split_id: str | None = None,
        evaluation_split_id: str | None = None,
        budget: ResourceBudget | None = None,
    ) -> MiReport: ...
    def compute_categorical_sxpid2(
        self,
        s1: _IntMatrix,
        s2: _IntMatrix,
        target: _IntMatrix,
        *,
        budget: ResourceBudget | None = None,
    ) -> SxPid2Result: ...
    def compute_categorical_sxpid3(
        self,
        s0: _IntMatrix,
        s1: _IntMatrix,
        s2: _IntMatrix,
        target: _IntMatrix,
        *,
        budget: ResourceBudget | None = None,
    ) -> SxPidLatticeResult: ...
    def compute_categorical_sxpid(
        self,
        sources: Sequence[_IntMatrix],
        target: _IntMatrix,
        *,
        budget: ResourceBudget | None = None,
    ) -> SxPidLatticeResult: ...
    def compute_categorical_imin_pid2(
        self,
        s1: _IntMatrix,
        s2: _IntMatrix,
        target: _IntMatrix,
        *,
        budget: ResourceBudget | None = None,
    ) -> IminPid2Result: ...
    def compute_fitted_quantized_sxpid2(
        self,
        s1: _FloatMatrix,
        s2: _FloatMatrix,
        target: _FloatMatrix,
        s1_quantizer: EqualWidthQuantizer,
        s2_quantizer: EqualWidthQuantizer,
        target_quantizer: EqualWidthQuantizer,
        *,
        budget: ResourceBudget | None = None,
    ) -> QuantizedSxPid2Result: ...


class _DiagnosticsModule(ModuleType):
    def diagnose_continuous_input(
        self,
        x: _FloatMatrix,
        k: int = 10,
        *,
        budget: ResourceBudget | None = None,
    ) -> ContinuousInputReport: ...
    def distance_concentration_report(
        self, x: _FloatMatrix, *, budget: ResourceBudget | None = None
    ) -> DistanceConcentrationReport: ...
    def intrinsic_dimension_report(
        self,
        x: _FloatMatrix,
        k: int = 10,
        *,
        budget: ResourceBudget | None = None,
    ) -> IntrinsicDimensionReport: ...


stable: _StableModule
diagnostics: _DiagnosticsModule
