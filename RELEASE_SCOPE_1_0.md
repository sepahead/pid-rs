# pid-rs 1.0 release scope

> **Scope state:** proposed 1.0 boundary for external review. The software publication
> target is 0.9.0 first. This document does not claim 1.0 publication, registry availability,
> independent acceptance, application validity, or a 1.x compatibility promise.

The machine-readable source is `release-scope-1.0.json`. The scope checker regenerates
this rendered view; the coherence job also rebuilds every compiled API profile and rejects
unlisted `pid-core` exports/modules, stable-namespace drift, feature-closure changes, snapshot
changes, schema violations, or ambiguous integration status.

Enabling a research feature changes only software availability. It does **not** promote
scientific maturity, widen support, establish calibration, or create a 1.x SemVer promise.

## Capability matrix

| ID | Public module | Cargo feature | Stability | Mathematical family / definition | Estimator revision | Support domain | Required provenance | Known failures | Rust | Python | Intended consumers | 1.x SemVer |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| pid-core.infrastructure | `crate` | — | stable | matrix, metric, error, cancellation, and resource infrastructure / `pid-core-infrastructure-v1` | `pid-core-infrastructure-v1` | typed matrices and declared resource ceilings | matrix dimensions; metric; resource budget | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow | pid_core | PidRsError; PidInputError; PidResourceError; PidNumericalError; PidUnsupportedError; PidCancelledError; ResourceBudget; ResourceEstimate | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.stable.categorical | `stable::categorical` | — | stable | empirical categorical shared-exclusions PID for 2–4 sources / `makkeh-gutknecht-wibral-2021-empirical-v1` | `direct-empirical-pmf-mobius-v1` | complete categorical source/target rows; nominal labels; 2–4 sources | source order and dimensions; target identity; row count; categorical encoding; input hash | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; source count outside 2–4; sample count above exact f64 integer range | pid_core::stable::categorical | SxAtom; EmpiricalPmfDiagnostics; SxPid2Result; Antichain; AntichainAtom; SxPidLatticeResult; compute_categorical_sxpid2; compute_categorical_sxpid3; compute_categorical_sxpid | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.stable.quantized | `stable::quantized` | — | stable | shared-exclusions PID of training-fitted equal-width categorical variables / `fitted-quantized-categorical-sxpid-v1` | `equal-width-fit-transform-plus-empirical-pmf-v1` | finite continuous training/evaluation matrices transformed by fixed fitted edges | training split identity; edges and policies; fit/evaluation occupancy; input/output hashes; source order | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; non-finite input; constant column under error policy; held-out out-of-range value | pid_core::stable::quantized | QuantizationReport; QuantizedData; EqualWidthQuantizer; QuantizedSxPid2Result; compute_fitted_quantized_sxpid2 | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.stable.imin | `stable::imin` | — | stable | Williams–Beer I_min comparator on an empirical categorical PMF / `williams-beer-2010-imin-v1` | `empirical-specific-information-minimum-v1` | complete categorical source/target rows; nominal labels | source order and dimensions; target identity; row count; categorical encoding; input hash | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; sample count above exact f64 integer range | pid_core::stable::imin | IminPid2Result; compute_categorical_imin_pid2 | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.stable.continuous | `stable::continuous` | — | stable | KSG1 mutual information with ambient Chebyshev/L-infinity product metric / `ksg1-product-small-ball-v1` | `strict-unique-shell-report-v3` | caller-asserted regular full-dimensional continuous law with finite MI and observed-sample tie/shell compatibility | ordered x/y identities; support assertion; preprocessing and observation model; sample/split identity; input hashes | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; support contract absent or unsupported; zero radius; ambiguous positive kth shell; non-finite input; numerical instability | pid_core::stable::continuous | ValueQuantiles; CountQuantiles; KsgLocalDiagnostics; AssumptionLedgerEntry; EstimandIdentity; Provenance; MiReport; compute_mi_report | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.stable.preprocessing | `stable::preprocessing` | — | stable | standardization, PCA, and fixed seeded hash projection utilities / `preprocessing-utilities-v1` | `preprocessing-safe-rust-v1` | finite matrices; transforms fitted on training rows for evidence use | fit dataset/split identity; parameters and parameter hash; input/output dimensions; transform role | invalid shape or row count; resource preflight rejection; checked size overflow; constant-column policy rejection; PCA nonconvergence | pid_core::stable::preprocessing |  | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.diagnostics.distance-matrix | `diagnostics` | — | stable | bounded exact symmetric distance matrices / `metric-distance-matrix-v1` | `upper-triangle-exact-v1` | finite matrices and supported metrics | metric; input identity; dimensions | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow | pid_core::diagnostics |  | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.diagnostics.geometry | `diagnostics` | — | stable | finite-sample intrinsic-dimension, distance-concentration, and four-point-delta diagnostics / `diagnostic-formulas-v1` | `diagnostic-safe-rust-v1` | finite sample geometry; observations are one-sided diagnostics only | metric; seed/config; input dimensions and hash; preprocessing identity | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; invalid k; degenerate all-zero distances | pid_core::diagnostics | DistanceConcentrationReport; IntrinsicDimensionReport; distance_concentration_report; intrinsic_dimension_report | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.diagnostics.invariants | `diagnostics` | — | stable | empirical categorical entropy, co-information, O-information, redundancy and vulnerability summaries / `empirical-shannon-invariants-v1` | `empirical-count-map-v1` | complete categorical rows with explicit normalization policy where applicable | variable order; row count; encoding and input identity; normalization policy | invalid shape or row count; resource preflight rejection; checked size overflow; undefined normalization | pid_core::diagnostics |  | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.diagnostics.support | `diagnostics` | — | stable | finite-sample tie, cardinality, and neighbor-shell observations / `continuous-sample-diagnostics-v1` | `exact-observation-diagnostics-v1` | finite observed matrices; never a population-support proof | metric; k; input dimensions and hash | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; invalid k; non-finite input | pid_core::diagnostics | DistanceQuantiles; NeighborShellDiagnostics; CoordinateCardinality; ContinuousInputReport; diagnose_continuous_input | standalone pid-rs callers; no downstream compatibility claimed | yes |
| pid-core.experimental.continuous.co-information | `experimental::continuous` | experimental-continuous | experimental | continuous KSG-derived co-information reports / `co-information-algebra-v1` | `ksg-derived-co-information-v1` | restricted continuous support; cancellation/bias interactions remain application-specific | all KSG support and preprocessing provenance; term identities | invalid shape or row count; resource preflight rejection; cancellation; checked size overflow; conditioning/cancellation imbalance | pid_core::experimental::continuous | experimental.migration.compute_co_information | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.continuous.isx | `experimental::continuous` | experimental-continuous | experimental | continuous shared-exclusions redundancy / `common-coordinate-radius-v1` | `strict-unique-shell-isx-v3` | restricted equal-ambient-dimension source gauges and regular support | ordered source/target identities; gauge/preprocessing descriptions; support assertion; input hashes | invalid shape or row count; resource preflight rejection; checked size overflow; source dimension mismatch; support/tie/shell incompatibility | pid_core::experimental::continuous | experimental.migration.compute_redundancy | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.continuous.shared-ksg-config | `experimental::continuous` | experimental-continuous | experimental | KSG configuration re-export shared with report-first continuous MI / `kraskov-stoegbauer-grassberger-2004-config-v1` | `ksg-chebyshev-config-v1` | caller-declared full-dimensional regular continuous laws for every required marginal and joint law | neighbor count k; metric; negative handling; support contract; resource policy | unsupported or undeclared population support; invalid neighbor count; ties incompatible with the declared observation model; resource preflight rejection | pid_core::experimental::continuous |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.continuous.pid2 | `experimental::continuous` | experimental-continuous | experimental | two-source continuous PID derived from KSG MI and continuous shared exclusions / `continuous-isx-pid2-algebra-v1` | `separate-biased-term-pid2-v1` | restricted continuous support; application validity not established | all KSG/ISX identities; fold/split provenance when applicable | invalid shape or row count; resource preflight rejection; checked size overflow; conditioning/cancellation failure | pid_core::experimental::continuous | experimental.migration.compute_pid2; experimental.migration.compute_pid2_report | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.continuous.incomplete-pid3 | `experimental::continuous` | experimental-continuous | experimental | availability diagnostics for incomplete continuous PID3 coordinates / `incomplete-pid3-availability-v1` | `equal-ambient-branch-screen-v1` | only named coordinates whose exact dependencies are available | source dimensions and order; available/missing dependency set; support and gauge provenance | invalid shape or row count; resource preflight rejection; checked size overflow; unavailable lattice dependency | pid_core::experimental::continuous | experimental.migration.compute_pid3_partial | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.raw-ksg | `experimental::continuous::raw_scalars` | experimental-continuous | research-only | raw scalar/local KSG mutual information / `kraskov-stoegbauer-grassberger-2004-v1` | `ksg-chebyshev-raw-v1` | research use only; local terms are dependent coordinate-specific contributions | caller-managed complete provenance | invalid shape or row count; resource preflight rejection; checked size overflow | pid_core::experimental::continuous::raw_scalars | experimental.migration.compute_mi | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.raw-isx | `experimental::continuous::raw_scalars` | experimental-continuous | research-only | raw continuous shared-exclusions redundancy / `ehrlich-et-al-2024-isx-intersection-v1` | `ehrlich-local-knn-raw-v1` | research use only; local terms are dependent coordinate-specific contributions | caller-managed complete provenance | invalid shape or row count; resource preflight rejection; checked size overflow | pid_core::experimental::continuous::raw_scalars | experimental.migration.compute_redundancy | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.raw-co-information | `experimental::continuous::raw_scalars` | experimental-continuous | research-only | raw co-information by KSG mutual-information inclusion/exclusion / `shannon-co-information-inclusion-exclusion-v1` | `ksg-co-information-raw-v1` | research use only; local terms are dependent coordinate-specific contributions | caller-managed complete provenance | invalid shape or row count; resource preflight rejection; checked size overflow | pid_core::experimental::continuous::raw_scalars | experimental.migration.compute_co_information | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.isx-heuristics | `experimental::isx_heuristics` | experimental-heuristics | research-only | formula-labelled heuristic baselines that do not estimate paper-defined continuous shared exclusions / `heuristic-baselines-v1` | `heuristic-baselines-v1` | exploratory comparison only | method identity; input and preprocessing identity | invalid shape or row count; resource preflight rejection; checked size overflow | pid_core::experimental::isx_heuristics |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.mixed-dimension-pid3 | `experimental::mixed_dimension_pid3` | research-mixed-dimension-pid3 | research-only | full mixed-dimensional continuous PID3 reference reproduction / `mixed-dimensional-pid3-reference-v1` | `mixed-dimensional-pid3-reference-v1` | double opt-in research reproduction; no general consistency claim | source/branch dimensions; runtime acknowledgement; support and gauge provenance | invalid shape or row count; resource preflight rejection; checked size overflow; runtime opt-in absent | pid_core::experimental::mixed_dimension_pid3 | experimental.migration.compute_pid3 | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.research.hyperbolic | `experimental::hyperbolic` | experimental-hyperbolic | research-only | Lorentz/Poincare geometry utilities and research pairwise KSG support / `hyperbolic-geometry-v1` | `lorentz-geometry-safe-rust-v1` | fixed supported curvature; no hyperbolic PID claim | curvature; embedding artifact/training identity; support assertion | invalid shape or row count; resource preflight rejection; checked size overflow; invalid manifold coordinates | pid_core::experimental::hyperbolic | experimental.migration.compute_mi_report | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.hierarchy | `experimental::hierarchy` | experimental-hierarchy | experimental | fast-to-slow exploratory hierarchy screening / `hierarchy-screening-v1` | `hierarchy-screening-v1` | exploratory screening only | selection/split identity; all estimator provenance | invalid shape or row count; resource preflight rejection; checked size overflow; selection/gate failure | pid_core::experimental::hierarchy |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.block-resampling | `experimental::pipelines` | experimental-pipelines | experimental | moving-block resampling contracts and estimators / `moving-block-bootstrap-v1` | `explicit-seed-block-bootstrap-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | block length/selection; dependence declaration; seed/RNG revision; replicate outcomes | invalid shape or row count; resource preflight rejection; checked size overflow; invalid block length; unsupported dependence declaration; failed replicate; cancellation | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.same-sample-quantization | `experimental::pipelines` | experimental-pipelines | experimental | explicitly exploratory same-sample quantization adapters / `same-sample-quantized-exploration-v1` | `equal-width-same-sample-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | bin count; source order; input hashes | invalid shape or row count; resource preflight rejection; checked size overflow; same-sample fitting is not held-out inference; invalid bin count | pid_core::experimental::pipelines | experimental.migration.compute_quantized_sxpid2; experimental.migration.compute_quantized_sxpid3; experimental.migration.compute_quantized_sxpid_n; experimental.migration.compute_discrete_pid2; experimental.migration.compute_discrete_pid3 | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.logistic-regression | `experimental::pipelines` | experimental-pipelines | experimental | L2-regularized logistic regression primitive / `penalized-logistic-regression-v1` | `newton-irls-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | regularization; convergence policy; training split | invalid shape or row count; resource preflight rejection; checked size overflow; singular or non-finite Newton system; non-convergence | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.fdr-adjustment | `experimental::pipelines` | experimental-pipelines | experimental | Benjamini-Hochberg/Yekutieli multiple-testing adjustment / `bh-by-fdr-v1` | `deterministic-sorted-pvalues-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | method; test-family identity; input p-values | invalid shape or row count; resource preflight rejection; checked size overflow; non-finite or out-of-range p-value; dependence assumptions not declared | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.quantized-sxpid-bootstrap | `experimental::pipelines` | experimental-pipelines | experimental | block-bootstrap uncertainty summary for fitted quantized SxPID2 / `quantized-sxpid2-block-bootstrap-v1` | `explicit-seed-quantized-bootstrap-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | fitted quantizers; block/dependence declaration; seed/RNG revision; replicate outcomes | invalid shape or row count; resource preflight rejection; checked size overflow; failed replicate; same-sample quantizer fitting; unsupported dependence declaration | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.row-bootstrap | `experimental::pipelines` | experimental-pipelines | experimental | callback-based row/block bootstrap procedure / `callback-row-bootstrap-v1` | `explicit-seed-row-bootstrap-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | callback identity/resource declaration; resampling scheme; seed/RNG revision; replicate outcomes | invalid shape or row count; resource preflight rejection; checked size overflow; failed callback/replicate; unsupported dependence declaration; cancellation | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.permutation-contracts | `experimental::pipelines` | experimental-pipelines | experimental | permutation-null and calibration contracts / `permutation-contracts-v1` | `explicit-seed-permutation-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | null family; exchangeability declaration; tail/calibration; seed/RNG revision | invalid shape or row count; resource preflight rejection; checked size overflow; unsupported null or exchangeability declaration; failed replicate | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.pid3-permutation | `experimental::pipelines` | experimental-pipelines | experimental | continuous PID3 permutation procedure / `pid3-permutation-null-v1` | `explicit-seed-pid3-permutation-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | PID3 configuration; null/exchangeability declaration; tail; seed/RNG revision; replicate outcomes | invalid shape or row count; resource preflight rejection; checked size overflow; research-only PID3 dependency; unsupported exchangeability; failed replicate; cancellation | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.row-permutation | `experimental::pipelines` | experimental-pipelines | experimental | callback-based row permutation procedure / `callback-row-permutation-v1` | `explicit-seed-row-permutation-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | callback identity/resource declaration; null/exchangeability declaration; tail; seed/RNG revision | invalid shape or row count; resource preflight rejection; checked size overflow; unsupported exchangeability; failed callback/replicate; cancellation | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.pls-selection-and-composition | `experimental::pipelines` | experimental-pipelines | experimental | PLS component selection and composed PID procedures / `pls-selection-composition-v1` | `deterministic-pls-cv-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | fold/split identity; target-use declaration; candidate components; selected transform | invalid shape or row count; resource preflight rejection; checked size overflow; target leakage; failed fold/candidate; cancellation | pid_core::experimental::pipelines | experimental.migration.pls_transform | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.pid2-screening | `experimental::pipelines` | experimental-pipelines | experimental | pairwise PID2 screening procedure / `pid2-pair-screen-v1` | `deterministic-pair-enumeration-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | source order; PID2 configuration; screening policy | invalid shape or row count; resource preflight rejection; checked size overflow; experimental PID2 dependency; selection leakage | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |
| pid-core.experimental.pipelines.jitter-preprocessing | `experimental::pipelines` | experimental-pipelines | experimental | explicit additive-noise preprocessing primitive / `seeded-additive-jitter-v1` | `seeded-jitter-v1` | exploratory only; requires declared dependence, exchangeability, split, and target-use assumptions | seed; noise distribution; noise scale; observation-model rationale | invalid shape or row count; resource preflight rejection; checked size overflow; changes the estimand; non-finite noise scale | pid_core::experimental::pipelines |  | standalone pid-rs callers; no downstream compatibility claimed | no |

## Exact public symbols

### `pid-core.infrastructure`

Module: `crate`. Export count: 15.

```text
CancellationToken
DEFAULT_MAX_BYTES
DEFAULT_MAX_OPERATIONS_HINT
DEFAULT_MAX_PAIRWISE_DISTANCES
DiscreteMatOwned
DiscreteMatRef
MatOwned
MatRef
Metric
PidError
PidResult
ResourceBudget
ResourceEstimate
concat_horiz
concat_horiz_with_budget
```

### `pid-core.stable.categorical`

Module: `stable::categorical`. Export count: 28.

```text
DiscreteInputEncoding
DiscreteInputMetadata
DiscreteSxPid2Result
DiscreteSxPid3Result
DiscreteSxPidNResult
EmpiricalPmfDiagnostics
SxAtom
SxPointwise2
SxPointwise3
SxPointwiseN
discrete_sxpid2
discrete_sxpid2_averaged
discrete_sxpid2_averaged_with_budget
discrete_sxpid2_averaged_with_budget_and_cancellation
discrete_sxpid2_resource_estimate
discrete_sxpid2_with_budget
discrete_sxpid3
discrete_sxpid3_averaged
discrete_sxpid3_averaged_with_budget
discrete_sxpid3_averaged_with_budget_and_cancellation
discrete_sxpid3_resource_estimate
discrete_sxpid3_with_budget
discrete_sxpid_n
discrete_sxpid_n_averaged
discrete_sxpid_n_averaged_with_budget
discrete_sxpid_n_averaged_with_budget_and_cancellation
discrete_sxpid_n_resource_estimate
discrete_sxpid_n_with_budget
```

### `pid-core.stable.quantized`

Module: `stable::quantized`. Export count: 18.

```text
EqualWidthQuantizer
FittedQuantizedSxPid2Result
FittedQuantizedSxPid3Result
FittedQuantizedSxPidNResult
OutOfRangePolicy
QuantizationReport
QuantizedData
QuantizerConfig
fitted_quantized_sxpid2
fitted_quantized_sxpid2_resource_estimate
fitted_quantized_sxpid2_with_budget
fitted_quantized_sxpid2_with_budget_and_cancellation
fitted_quantized_sxpid3
fitted_quantized_sxpid3_resource_estimate
fitted_quantized_sxpid3_with_budget
fitted_quantized_sxpid_n
fitted_quantized_sxpid_n_resource_estimate
fitted_quantized_sxpid_n_with_budget
```

### `pid-core.stable.imin`

Module: `stable::imin`. Export count: 19.

```text
IminEmpiricalPmfDiagnostics
IminInputEncoding
IminInputMetadata
IminPid2Result
IminPid3Atom
IminPid3Result
imin_pid2
imin_pid2_quantized
imin_pid2_quantized_resource_estimate
imin_pid2_quantized_with_budget
imin_pid2_resource_estimate
imin_pid2_with_budget
imin_pid2_with_budget_and_cancellation
imin_pid3
imin_pid3_quantized
imin_pid3_quantized_resource_estimate
imin_pid3_quantized_with_budget
imin_pid3_resource_estimate
imin_pid3_with_budget
```

### `pid-core.stable.continuous`

Module: `stable::continuous`. Export count: 31.

```text
Assumption
AssumptionLedgerEntry
AssumptionState
BoundaryModel
EstimandIdentity
EstimateReport
InformationUnit
KsgConfig
KsgCountQuantiles
KsgGeometryModel
KsgLocalDiagnosticsSummary
KsgMethodStatus
KsgMiReport
KsgNeighborBackend
KsgProvenance
KsgReportWarning
KsgTrajectoryReport
KsgValueQuantiles
NegativeHandling
ProvenanceHashes
ScientificStatus
SupportContract
WarningCode
ksg_k_trajectory
ksg_mi_report
ksg_mi_report_with_budget
ksg_mi_report_with_budget_and_cancellation
ksg_report_resource_estimate
ksg_resource_estimate
ksg_resource_estimate_for_threads
ksg_sample_size_trajectory
```

### `pid-core.stable.preprocessing`

Module: `stable::preprocessing`. Export count: 4.

```text
ConstantColumnPolicy
HashProjector
PcaProjector
Standardizer
```

### `pid-core.diagnostics.distance-matrix`

Module: `diagnostics`. Export count: 6.

```text
SymmetricDistanceMatrix
symmetric_distance_resources
symmetric_distance_resources_for
symmetric_distances
symmetric_distances_with_budget
symmetric_distances_with_budget_and_cancellation
```

### `pid-core.diagnostics.geometry`

Module: `diagnostics`. Export count: 20.

```text
DistanceConcentrationConfig
DistanceConcentrationStats
HyperbolicityConfig
IntrinsicDimConfig
IntrinsicDimensionReport
IntrinsicDimensionTrajectory
SampledFourPointDeltaSummary
distance_concentration_resource_estimate
distance_concentration_stats
distance_concentration_stats_with_budget
distance_concentration_stats_with_budget_and_cancellation
intrinsic_dimension_levina_bickel
intrinsic_dimension_multi_k
intrinsic_dimension_report
intrinsic_dimension_report_with_cancellation
intrinsic_dimension_resource_estimate
sampled_four_point_delta_summary
sampled_four_point_delta_summary_with_budget
sampled_four_point_delta_summary_with_budget_and_cancellation
sampled_four_point_resource_estimate
```

### `pid-core.diagnostics.invariants`

Module: `diagnostics`. Export count: 26.

```text
NormalizedInvariantPolicy
NormalizedInvariantReport
NormalizedInvariantStatus
NormalizedInvariantUnit
average_degree_of_redundancy
average_degree_of_redundancy_with_policy
average_degree_of_vulnerability
average_degree_of_vulnerability_with_policy
co_information_pairwise_discrete
co_information_pairwise_discrete_resource_estimate
co_information_pairwise_discrete_with_budget
entropy_discrete
entropy_discrete_resource_estimate
entropy_discrete_with_budget
joint_entropy_discrete
joint_entropy_discrete_resource_estimate
joint_entropy_discrete_with_budget
o_information_discrete
o_information_discrete_resource_estimate
o_information_discrete_with_budget
red_degree_discrete
red_degree_discrete_resource_estimate
red_degree_discrete_with_budget
vul_degree_discrete
vul_degree_discrete_resource_estimate
vul_degree_discrete_with_budget
```

### `pid-core.diagnostics.support`

Module: `diagnostics`. Export count: 12.

```text
ContinuousInputDiagnostics
CoordinateCardinalityDiagnostics
DistanceQuantiles
NeighborShellDiagnostics
continuous_input_diagnostics
continuous_input_diagnostics_resource_estimate
continuous_input_diagnostics_with_budget
continuous_input_diagnostics_with_budget_and_cancellation
continuous_joint_shell_diagnostics
continuous_joint_shell_diagnostics_with_budget
continuous_joint_shell_diagnostics_with_budget_and_cancellation
continuous_joint_shell_resource_estimate
```

### `pid-core.experimental.continuous.co-information`

Module: `experimental::continuous`. Export count: 13.

```text
CoInformationCancellationDiagnostics
CoInformationConditioningStatus
CoInformationReportWarning
PairwiseCoInformationReport
TripletCoInformationReport
co_information_pairwise_report
co_information_pairwise_report_resource_estimate
co_information_pairwise_report_resource_estimate_for_threads
co_information_pairwise_report_with_budget
co_information_triplet_report
co_information_triplet_report_resource_estimate
co_information_triplet_report_resource_estimate_for_threads
co_information_triplet_report_with_budget
```

### `pid-core.experimental.continuous.isx`

Module: `experimental::continuous`. Export count: 9.

```text
IsxConfig
IsxLocalDiagnosticsSummary
IsxMethod
IsxProvenance
IsxReport
isx_redundancy_report
isx_report_resource_estimate
isx_resource_estimate
isx_resource_estimate_for_threads
```

### `pid-core.experimental.continuous.shared-ksg-config`

Module: `experimental::continuous`. Export count: 1.

```text
KsgConfig
```

### `pid-core.experimental.continuous.pid2`

Module: `experimental::continuous`. Export count: 28.

```text
Pid2AtomConditioning
Pid2ConditioningStatus
Pid2Config
Pid2CrossFitAggregation
Pid2CrossFitFold
Pid2CrossFitFoldReport
Pid2CrossFitReport
Pid2Estimate
Pid2JointDiagnostics
Pid2MethodStatus
Pid2Provenance
Pid2Report
Pid2ReportWarning
Pid2Result
pid2_cross_fit_resource_estimate
pid2_isx
pid2_isx_cross_fit_reports
pid2_isx_cross_fit_reports_with_budget
pid2_isx_estimate
pid2_isx_estimate_with_budget
pid2_isx_report
pid2_isx_report_with_budget
pid2_isx_split_sample_report
pid2_isx_split_sample_report_with_budget
pid2_isx_with_budget
pid2_report_resource_estimate
pid2_resource_estimate
pid2_resource_estimate_for_threads
```

### `pid-core.experimental.continuous.incomplete-pid3`

Module: `experimental::continuous`. Export count: 14.

```text
Antichain3
IncompletePid3Atom
IncompletePid3Diagnostic
IncompletePid3Redundancy
IncompletePid3Report
IncompletePid3Status
Pid3Config
Pid3Provenance
incomplete_pid3_diagnostic
incomplete_pid3_diagnostic_with_budget
incomplete_pid3_report
incomplete_pid3_report_with_budget
incomplete_pid3_resource_estimate
incomplete_pid3_resource_estimate_for_threads
```

### `pid-core.research.raw-ksg`

Module: `experimental::continuous::raw_scalars`. Export count: 3.

```text
ksg_local_mi_terms
ksg_mi
ksg_mi_concat_xy
```

### `pid-core.research.raw-isx`

Module: `experimental::continuous::raw_scalars`. Export count: 1.

```text
isx_redundancy
```

### `pid-core.research.raw-co-information`

Module: `experimental::continuous::raw_scalars`. Export count: 8.

```text
co_information_pairwise
co_information_pairwise_resource_estimate
co_information_pairwise_resource_estimate_for_threads
co_information_pairwise_with_budget
co_information_triplet
co_information_triplet_resource_estimate
co_information_triplet_resource_estimate_for_threads
co_information_triplet_with_budget
```

### `pid-core.research.isx-heuristics`

Module: `experimental::isx_heuristics`. Export count: 3.

```text
heuristic_sketch_baseline
local_mi_minimum_baseline
unweighted_local_mi_inclusion_exclusion_baseline
```

### `pid-core.research.mixed-dimension-pid3`

Module: `experimental::mixed_dimension_pid3`. Export count: 14.

```text
Antichain3
Pid3Atom
Pid3Config
Pid3MethodStatus
Pid3Provenance
Pid3Redundancy
Pid3Report
Pid3Result
pid3_isx
pid3_isx_report
pid3_isx_report_with_budget
pid3_isx_with_budget
pid3_resource_estimate
pid3_resource_estimate_for_threads
```

### `pid-core.research.hyperbolic`

Module: `experimental::hyperbolic`. Export count: 58.

```text
ContinuousInputDiagnostics
DistanceConcentrationStats
HyperbolicCurvature
HyperbolicDistanceConcentrationConfig
HyperbolicFourPointConfig
HyperbolicIntrinsicDimConfig
HyperbolicIntrinsicDimensionReport
HyperbolicIntrinsicDimensionTrajectory
HyperbolicKsgConfig
HyperbolicKsgGeometryModel
HyperbolicKsgMiReport
HyperbolicKsgReportWarning
HyperbolicKsgTrajectoryReport
HyperbolicMetric
HyperbolicSupportContract
NeighborShellDiagnostics
SampledFourPointDeltaSummary
SymmetricDistanceMatrix
hyperbolic_continuous_input_diagnostics
hyperbolic_continuous_input_diagnostics_resource_estimate
hyperbolic_continuous_input_diagnostics_with_budget
hyperbolic_continuous_input_diagnostics_with_budget_and_cancellation
hyperbolic_continuous_joint_shell_diagnostics
hyperbolic_continuous_joint_shell_diagnostics_with_budget
hyperbolic_continuous_joint_shell_diagnostics_with_budget_and_cancellation
hyperbolic_continuous_joint_shell_resource_estimate
hyperbolic_distance_concentration_resource_estimate
hyperbolic_distance_concentration_stats
hyperbolic_distance_concentration_stats_with_budget
hyperbolic_distance_concentration_stats_with_budget_and_cancellation
hyperbolic_distance_lorentz
hyperbolic_intrinsic_dimension_levina_bickel
hyperbolic_intrinsic_dimension_multi_k
hyperbolic_intrinsic_dimension_report
hyperbolic_intrinsic_dimension_report_with_cancellation
hyperbolic_intrinsic_dimension_resource_estimate
hyperbolic_ksg_k_trajectory
hyperbolic_ksg_mi_report
hyperbolic_ksg_mi_report_with_budget
hyperbolic_ksg_mi_report_with_budget_and_cancellation
hyperbolic_ksg_report_resource_estimate
hyperbolic_ksg_sample_size_trajectory
hyperbolic_sampled_four_point_delta_summary
hyperbolic_sampled_four_point_delta_summary_with_budget
hyperbolic_sampled_four_point_delta_summary_with_budget_and_cancellation
hyperbolic_sampled_four_point_resource_estimate
hyperbolic_symmetric_distance_resources
hyperbolic_symmetric_distance_resources_for
hyperbolic_symmetric_distances
hyperbolic_symmetric_distances_with_budget
hyperbolic_symmetric_distances_with_budget_and_cancellation
lorentz_dot
lorentz_to_poincare
lorentz_to_poincare_resource_estimate
lorentz_to_poincare_with_budget
poincare_to_lorentz
poincare_to_lorentz_resource_estimate
poincare_to_lorentz_with_budget
```

### `pid-core.experimental.hierarchy`

Module: `experimental::hierarchy`. Export count: 18.

```text
HierarchicalConfig
HierarchicalPairwiseReport
HierarchicalTriplet
HierarchySelectionProvenance
HierarchySplitIdentity
PairSelection
PairwiseScreen
hierarchical_pairwise
hierarchical_pairwise_resource_estimate
hierarchical_pairwise_resource_estimate_for_threads
hierarchical_pairwise_split
hierarchical_pairwise_split_resource_estimate_for_threads
hierarchical_pairwise_split_with_budget
hierarchical_pairwise_with_budget
hierarchical_triplet
hierarchical_triplet_resource_estimate
hierarchical_triplet_resource_estimate_for_threads
hierarchical_triplet_with_budget
```

### `pid-core.experimental.pipelines.block-resampling`

Module: `experimental::pipelines`. Export count: 20.

```text
BlockLengthSelection
BlockResamplingAlgorithmRevision
BlockResamplingProvenance
BootstrapConfig
BootstrapReplicateOutcome
BootstrapReplicateStatus
BootstrapResult
CancellationToken
ResamplingDependence
ResamplingDistributionSummary
ResamplingValidityDeclaration
StatisticCallbackDeclaration
block_bootstrap
block_bootstrap_paired
block_bootstrap_paired_resource_estimate
block_bootstrap_paired_with_budget
block_bootstrap_paired_with_cancellation
block_bootstrap_resource_estimate
block_bootstrap_with_budget
block_bootstrap_with_cancellation
```

### `pid-core.experimental.pipelines.same-sample-quantization`

Module: `experimental::pipelines`. Export count: 7.

```text
ExploratorySameSampleQuantizedResult
SameSampleEqualWidthProvenance
exploratory_same_sample_quantized_imin_pid2
exploratory_same_sample_quantized_imin_pid3
exploratory_same_sample_quantized_sxpid2
exploratory_same_sample_quantized_sxpid3
exploratory_same_sample_quantized_sxpid_n
```

### `pid-core.experimental.pipelines.logistic-regression`

Module: `experimental::pipelines`. Export count: 2.

```text
LogisticRegression
LogisticRegressionConfig
```

### `pid-core.experimental.pipelines.fdr-adjustment`

Module: `experimental::pipelines`. Export count: 4.

```text
MultipleTestingAdjustment
MultipleTestingMethod
benjamini_hochberg
benjamini_yekutieli
```

### `pid-core.experimental.pipelines.quantized-sxpid-bootstrap`

Module: `experimental::pipelines`. Export count: 4.

```text
QuantizedSxPid2BootstrapResult
bootstrap_quantized_sxpid2
bootstrap_quantized_sxpid2_resource_estimate
bootstrap_quantized_sxpid2_with_budget
```

### `pid-core.experimental.pipelines.row-bootstrap`

Module: `experimental::pipelines`. Export count: 9.

```text
RowBootstrapResult
RowBootstrapStat
RowResampleOutcome
RowResampleScheme
RowResampleStatus
bootstrap_rows_stats
bootstrap_rows_stats_resource_estimate
bootstrap_rows_stats_with_budget
bootstrap_rows_stats_with_cancellation
```

### `pid-core.experimental.pipelines.permutation-contracts`

Module: `experimental::pipelines`. Export count: 9.

```text
PermutationAlgorithmRevision
PermutationCalibration
PermutationFamily
PermutationNull
PermutationNullAssumption
PermutationReplicateOutcome
PermutationReplicateStatus
PermutationScheme
PermutationTail
```

### `pid-core.experimental.pipelines.pid3-permutation`

Module: `experimental::pipelines`. Export count: 10.

```text
PermutationPid3Atom
PermutationPid3Result
permutation_pid3
permutation_pid3_resource_estimate
permutation_pid3_under_null_with_budget
permutation_pid3_under_null_with_cancellation
permutation_pid3_with
permutation_pid3_with_budget
permutation_pid3_with_tail
permutation_pid3_with_tail_and_budget
```

### `pid-core.experimental.pipelines.row-permutation`

Module: `experimental::pipelines`. Export count: 9.

```text
RowPermutationStat
permutation_rows_pvalue
permutation_rows_pvalue_resource_estimate
permutation_rows_pvalue_under_null_with_budget
permutation_rows_pvalue_under_null_with_cancellation
permutation_rows_pvalue_with
permutation_rows_pvalue_with_budget
permutation_rows_pvalue_with_tail
permutation_rows_pvalue_with_tail_and_budget
```

### `pid-core.experimental.pipelines.pls-selection-and-composition`

Module: `experimental::pipelines`. Export count: 16.

```text
PlsCvCandidateOutcome
PlsCvCandidateStatus
PlsCvFoldOutcome
PlsCvFoldStatus
PlsCvResult
PlsDiscretePid3Config
PlsDiscretePid3Result
PlsPid3Config
PlsPid3Result
PlsProjector
pls_cv_select_components
pls_cv_select_components_resource_estimate
pls_cv_select_components_with_budget
pls_cv_select_components_with_cancellation
pls_project_then_discrete_pid3
pls_project_then_pid3
```

### `pid-core.experimental.pipelines.pid2-screening`

Module: `experimental::pipelines`. Export count: 4.

```text
Pid2ScreenEntry
screen_pid2_pairs
screen_pid2_pairs_resource_estimate
screen_pid2_pairs_with_budget
```

### `pid-core.experimental.pipelines.jitter-preprocessing`

Module: `experimental::pipelines`. Export count: 1.

```text
Jitter
```

## Known stable-namespace leaks that block API freeze

These members appear only when a research feature is enabled but mutate types also
exported through stable/top-level paths. They are recorded as blockers, not approved
1.x stable API. They must move behind a research-only type or entry point before the
1.x API can freeze.

| Public path | Feature | Kind | Removed default signature | 1.x promise |
|---|---|---|---|---|
| `pid_core::Metric::HyperbolicLorentz` | `experimental-hyperbolic` | enum variant | — | no |
| `pid_core::Metric::HyperbolicLorentz::curvature: pid_core::experimental::hyperbolic::HyperbolicCurvature` | `experimental-hyperbolic` | variant field | — | no |
| `pid_core::stable::continuous::SupportContract::AssumeSmoothManifold` | `experimental-hyperbolic` | enum variant | — | no |
| `pid_core::stable::continuous::KsgConfig::experimental_smooth_hyperbolic_manifold` | `experimental-hyperbolic` | inherent method | — | no |
| `pid_core::stable::continuous::KsgGeometryModel::LorentzHyperboloid` | `experimental-hyperbolic` | enum variant | — | no |
| `pid_core::stable::continuous::KsgReportWarning::HyperbolicConsistencyNotEstablished` | `experimental-hyperbolic` | enum variant | — | no |
| `pid_core::stable::continuous::KsgMiReport::curvature: core::option::Option<pid_core::experimental::hyperbolic::HyperbolicCurvature>` | `experimental-hyperbolic` | field type mutation | pub pid_core::stable::continuous::KsgMiReport::curvature: core::option::Option<()> | no |
| `pid_core::stable::categorical::DiscreteInputEncoding::EqualWidth` | `experimental-pipelines` | enum variant | — | no |
| `pid_core::stable::categorical::DiscreteInputEncoding::EqualWidth::num_bins` | `experimental-pipelines` | variant field | — | no |
| `pid_core::stable::imin::IminInputEncoding::SameSampleEqualWidth` | `experimental-pipelines` | enum variant | — | no |
| `pid_core::stable::imin::IminInputEncoding::SameSampleEqualWidth::num_bins` | `experimental-pipelines` | variant field | — | no |

## Optional integration claims

- `crebain`: **not_claimed** — proposed 1.0 boundary under review during the 0.9 release; no qualified compatibility evidence is claimed
- `external-authority`: **not_claimed** — proposed 1.0 boundary under review during the 0.9 release; no qualified compatibility evidence is claimed
- `galadriel`: **not_claimed** — proposed 1.0 boundary under review during the 0.9 release; no qualified compatibility evidence is claimed
- `haldir`: **not_claimed** — proposed 1.0 boundary under review during the 0.9 release; no qualified compatibility evidence is claimed
- `prisoma`: **not_claimed** — proposed 1.0 boundary under review during the 0.9 release; no qualified compatibility evidence is claimed

## Acceptance blockers

- Every stable publication-facing estimator still needs a common status, identity, and provenance report contract before 1.0 qualification.
- Eleven research-feature members still mutate otherwise stable namespaces and must be isolated behind research-only types or entry points before the 1.0 API can be frozen.
- Maintainer approval must identify the exact frozen 1.0 candidate commit after 0.9 review feedback is resolved.
- An independent scientific reviewer must approve the exact frozen 1.0 candidate commit and disclose their role and conflicts.
- The exact stable Python import allowlist and serialized/CLI surfaces remain unfrozen and must be recorded before 1.0 qualification.

## Review approvals

- `maintainer`: **pending**; binding: `api_snapshot_source_commit`; reviewer: —; commit: —; evidence: —; conflicts: —; independence: —
- `independent_scientific_reviewer`: **pending**; binding: `api_snapshot_source_commit`; reviewer: —; commit: —; evidence: —; conflicts: —; independence: —

## Prohibited 1.0 claims

- Universal validity, consistency, or calibration of KSG or continuous PID.
- A finite sample or geometry diagnostic proves population absolute continuity or full-dimensional support.
- Generic calibrated confidence intervals or hypothesis tests for kNN PID.
- Automatic jitter repairs ties without changing the estimand.
- High-dimensional VLA embedding application validity.
- Shared exclusions is the uniquely correct PID measure.
- Observational information establishes causal availability, use, effect, or safety.
- Prisoma H1–H4, Galadriel field validation, Crebain adapter compatibility, or Haldir deployment compatibility.
- PID evidence grants, creates, or widens authorization.
- Internal hashes alone authenticate origin or provide a safety certificate.
- Full mixed-dimensional continuous PID3 is stable science.

## Unsupported in 1.0

- Universal calibrated uncertainty for generic kNN PID.
- Silent tie repair or automatic jitter.
- Stable full continuous PID3 across mixed-dimensional branches.
- Hyperbolic shared-exclusions PID.
- Per-sample local PID features as a stable cross-fold prediction contract.
- Safety monitoring, command authorization, or field certification.

## Compiled public-API snapshots

Snapshots were generated with the pinned tool recorded in this scope file. They are
signature evidence, not scientific-validation evidence.

| Profile | Activation | Requested features | Feature closure | Snapshot | SHA-256 |
|---|---|---|---|---|---|
| `pid-core-default` | explicit feature set |  |  | `audit/api/public-api/pid-core-default.txt` | `af8a471d3d00cc4c45434e32df430cf9904f5e4a88398e01cff32540a8f769e6` |
| `pid-core-parallel` | explicit feature set | parallel | parallel | `audit/api/public-api/pid-core-parallel.txt` | `af8a471d3d00cc4c45434e32df430cf9904f5e4a88398e01cff32540a8f769e6` |
| `pid-core-experimental-continuous` | explicit feature set | experimental-continuous | experimental-continuous | `audit/api/public-api/pid-core-experimental-continuous.txt` | `21d8f7c33527ec3b22c7aba95506317b99067238f0d2bfef35d37f7bf6100969` |
| `pid-core-experimental-hyperbolic` | explicit feature set | experimental-hyperbolic | experimental-continuous; experimental-hyperbolic | `audit/api/public-api/pid-core-experimental-hyperbolic.txt` | `6f27f1cda1e7d4a514688e3f010f8f86abc8baf244ec2a1f97a9c8002f0591db` |
| `pid-core-experimental-heuristics` | explicit feature set | experimental-heuristics | experimental-continuous; experimental-heuristics | `audit/api/public-api/pid-core-experimental-heuristics.txt` | `33d0583e5da6387e3347da2a700b442682c34d95f5fa89e21687d62f9253860d` |
| `pid-core-experimental-hierarchy` | explicit feature set | experimental-hierarchy | experimental-continuous; experimental-hierarchy | `audit/api/public-api/pid-core-experimental-hierarchy.txt` | `f9528986c689131ccae47c2df9d10acda280af0447143d891f2a3255f74b507a` |
| `pid-core-research-mixed-dimension-pid3` | explicit feature set | research-mixed-dimension-pid3 | experimental-continuous; research-mixed-dimension-pid3 | `audit/api/public-api/pid-core-research-mixed-dimension-pid3.txt` | `13c005dbde27a84c49340b1b165a39a736d3dde71abafa19e3b6694ab1e2f54f` |
| `pid-core-experimental-pipelines` | explicit feature set | experimental-pipelines | experimental-continuous; experimental-pipelines; research-mixed-dimension-pid3 | `audit/api/public-api/pid-core-experimental-pipelines.txt` | `db81cc10beab6a66578b4da47bdd60132970507df77b05a7f092aee539b66d4b` |
| `pid-core-experimental-all` | explicit feature set | experimental-all | experimental-all; experimental-continuous; experimental-heuristics; experimental-hierarchy; experimental-hyperbolic; experimental-pipelines; research-mixed-dimension-pid3 | `audit/api/public-api/pid-core-experimental-all.txt` | `c79ccacb1d80bf4e84ecd4d9bc63027733501bb24943ee0a4e51e5e089e93c35` |
| `pid-core-all-features` | `--all-features` |  | default; experimental-all; experimental-continuous; experimental-heuristics; experimental-hierarchy; experimental-hyperbolic; experimental-pipelines; parallel; research-mixed-dimension-pid3 | `audit/api/public-api/pid-core-experimental-all.txt` | `c79ccacb1d80bf4e84ecd4d9bc63027733501bb24943ee0a4e51e5e089e93c35` |
