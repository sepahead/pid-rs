//! Default-off Python compatibility wrappers for research and pre-1.0 APIs.
//!
//! # Method provenance and availability
//!
//! **PROJECT-DEFINED BINDING INVENTORY.** `register_legacy` defines the exact callable, class, and
//! policy-attribute surface under `pid_core_rs.experimental.migration`. The prefix is part of the
//! scientific status boundary; importing a wrapper does not promote its wrapped Rust method.
//!
//! Method catalog: software.python-experimental-migration-bindings
//!
//! **PAPER-DERIVED RESEARCH COMPOSITION.** `compute_invariants` combines raw KSG mutual
//! information, raw pairwise co-information, and the published target-based average redundancy
//! and vulnerability formulas. It is a Python-only research composition, not the categorical
//! invariant family and not an independent estimator theorem.
//!
//! Method catalog: shannon-invariants.continuous-ksg-composition

use numpy::{PyReadonlyArray2, PyUntypedArrayMethods};
use pid_core::diagnostics::{
    average_degree_of_redundancy, average_degree_of_vulnerability,
    continuous_input_diagnostics as core_continuous_input_diagnostics,
    distance_concentration_stats, intrinsic_dimension_levina_bickel,
    sampled_four_point_delta_summary as core_four_point_delta_summary, ContinuousInputDiagnostics,
    DistanceConcentrationConfig, HyperbolicityConfig, IntrinsicDimConfig, NeighborShellDiagnostics,
};
use pid_core::experimental::continuous::raw_scalars::{
    co_information_pairwise, isx_redundancy, ksg_mi, ksg_mi_concat_xy,
};
use pid_core::experimental::continuous::{
    incomplete_pid3_report as pid3_isx_partial_report, pid2_isx, pid2_isx_report, IsxConfig,
    IsxMethod, Pid2Config, Pid2MethodStatus, Pid2Provenance, Pid2ReportWarning, Pid3Config,
    Pid3Provenance,
};
use pid_core::experimental::hyperbolic::{
    hyperbolic_continuous_input_diagnostics, hyperbolic_distance_concentration_stats,
    hyperbolic_intrinsic_dimension_levina_bickel, hyperbolic_ksg_mi_report,
    hyperbolic_sampled_four_point_delta_summary, HyperbolicCurvature,
    HyperbolicDistanceConcentrationConfig, HyperbolicFourPointConfig, HyperbolicIntrinsicDimConfig,
    HyperbolicKsgConfig, HyperbolicKsgReportWarning, HyperbolicMetric,
};
use pid_core::experimental::mixed_dimension_pid3::{pid3_isx_report, Pid3MethodStatus};
use pid_core::experimental::pipelines::{
    exploratory_same_sample_quantized_imin_pid2 as discrete_pid2,
    exploratory_same_sample_quantized_imin_pid3 as discrete_pid3,
    exploratory_same_sample_quantized_sxpid2 as core_quantized_sxpid2,
    exploratory_same_sample_quantized_sxpid3 as core_quantized_sxpid3,
    exploratory_same_sample_quantized_sxpid_n as core_quantized_sxpid_n,
    PlsProjector as CorePlsProjector,
};
use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n, DiscreteSxPid2Result, SxAveragedAtom,
};
use pid_core::stable::continuous::{
    ksg_mi_report, KsgConfig, KsgGeometryModel, KsgMethodStatus, KsgProvenance, KsgReportWarning,
    NegativeHandling, SupportContract,
};
use pid_core::stable::preprocessing::{
    ConstantColumnPolicy, HashProjector, PcaProjector, Standardizer,
};
use pid_core::{DiscreteMatRef, MatRef, Metric, DEFAULT_MAX_BYTES, DEFAULT_MAX_OPERATIONS_HINT};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList, PySequence};
use std::collections::BTreeMap;
use std::mem::size_of;

const MIGRATION_MAX_SOURCES: usize = 4;
const MIGRATION_MAX_CONFIG_TOKEN_BYTES: usize = 64;
const MIGRATION_MAX_PROVENANCE_BYTES: usize = 16 * 1024;

fn migration_size_overflow(operation: &'static str) -> PyErr {
    pid_err(pid_core::PidError::SizeOverflow { operation })
}

fn checked_product(operation: &'static str, left: usize, right: usize) -> PyResult<usize> {
    left.checked_mul(right)
        .ok_or_else(|| migration_size_overflow(operation))
}

fn checked_u128_mul(operation: &'static str, left: u128, right: u128) -> PyResult<u128> {
    left.checked_mul(right)
        .ok_or_else(|| migration_size_overflow(operation))
}

fn checked_u128_add(operation: &'static str, left: u128, right: u128) -> PyResult<u128> {
    left.checked_add(right)
        .ok_or_else(|| migration_size_overflow(operation))
}

fn check_migration_resources(
    operation: &'static str,
    estimated_bytes: u128,
    operations_hint: u128,
) -> PyResult<()> {
    if estimated_bytes > u128::from(DEFAULT_MAX_BYTES) {
        return Err(pid_err(pid_core::PidError::ResourceLimitExceeded {
            operation,
            resource: "bytes",
            requested: estimated_bytes,
            limit: u128::from(DEFAULT_MAX_BYTES),
        }));
    }
    if operations_hint > DEFAULT_MAX_OPERATIONS_HINT {
        return Err(pid_err(pid_core::PidError::ResourceLimitExceeded {
            operation,
            resource: "operations_hint",
            requested: operations_hint,
            limit: DEFAULT_MAX_OPERATIONS_HINT,
        }));
    }
    Ok(())
}

fn try_vec_with_capacity<T>(operation: &'static str, capacity: usize) -> PyResult<Vec<T>> {
    let requested_bytes = checked_u128_mul(operation, capacity as u128, size_of::<T>() as u128)?;
    check_migration_resources(operation, requested_bytes, capacity as u128)?;
    let mut values = Vec::new();
    values.try_reserve_exact(capacity).map_err(|_| {
        pid_err(pid_core::PidError::AllocationFailed {
            operation,
            requested_bytes,
        })
    })?;
    Ok(values)
}

fn validate_config_token(field: &'static str, value: &str) -> PyResult<()> {
    if value.len() > MIGRATION_MAX_CONFIG_TOKEN_BYTES {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "{field} must be at most {MIGRATION_MAX_CONFIG_TOKEN_BYTES} bytes"
        )));
    }
    Ok(())
}

fn try_owned_provenance(field: &'static str, value: &str) -> PyResult<String> {
    if value.trim().is_empty() || value.len() > MIGRATION_MAX_PROVENANCE_BYTES {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "{field} must be nonempty and at most {MIGRATION_MAX_PROVENANCE_BYTES} bytes"
        )));
    }
    let mut owned = String::new();
    owned.try_reserve_exact(value.len()).map_err(|_| {
        pid_err(pid_core::PidError::AllocationFailed {
            operation: "experimental.migration provenance",
            requested_bytes: value.len() as u128,
        })
    })?;
    owned.push_str(value);
    Ok(owned)
}

fn ceil_log2(value: usize) -> u128 {
    if value <= 1 {
        1
    } else {
        (usize::BITS - (value - 1).leading_zeros()) as u128
    }
}

fn preflight_categorical_lengths(operation: &'static str, lengths: &[usize]) -> PyResult<()> {
    let total_elements = lengths.iter().try_fold(0u128, |total, &length| {
        checked_u128_add(operation, total, length as u128)
    })?;
    // Every encoded matrix remains live until the estimator call. This conservative bound also
    // retains a full sorted-label scratch buffer for every input, even though conversion is
    // sequential and only one such buffer is live at a time.
    let bytes_per_element = size_of::<usize>()
        .checked_add(size_of::<i64>())
        .ok_or_else(|| migration_size_overflow(operation))? as u128;
    let estimated_bytes = checked_u128_mul(operation, total_elements, bytes_per_element)?;
    let operations_hint = lengths.iter().try_fold(total_elements, |total, &length| {
        let per_element = checked_u128_add(
            operation,
            checked_u128_mul(operation, ceil_log2(length), 5)?,
            4,
        )?;
        checked_u128_add(
            operation,
            total,
            checked_u128_mul(operation, length as u128, per_element)?,
        )
    })?;
    check_migration_resources(operation, estimated_bytes, operations_hint)
}

fn categorical_array_len(arr: &PyReadonlyArray2<'_, i64>) -> PyResult<usize> {
    if !arr.is_c_contiguous() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Categorical array must be C-contiguous; wrap it in np.ascontiguousarray(x)",
        ));
    }
    arr.as_slice().map(|slice| slice.len()).map_err(|_| {
        pyo3::exceptions::PyValueError::new_err("Categorical array must be C-contiguous")
    })
}

fn validate_aligned_rows(operation: &'static str, rows: &[usize]) -> PyResult<()> {
    let Some(&expected) = rows.first() else {
        return Ok(());
    };
    if let Some((index, actual)) = rows
        .iter()
        .copied()
        .enumerate()
        .find(|(_, actual)| *actual != expected)
    {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "{operation}: row count mismatch at input {index}: expected {expected}, got {actual}"
        )));
    }
    Ok(())
}

/// Conservative legacy compatibility preflight retained before the Rust same-sample wrappers.
///
/// The `num_bins + 1` term models a fitted-edge vector even though the rebound Rust transform
/// materializes none. This intentionally preserves the deprecated Python rejection domain; it can
/// reject large bin counts accepted by Rust and therefore is not a transform-equivalence claim.
fn preflight_quantized_matrices(
    operation: &'static str,
    matrices: &[MatRef<'_>],
    num_bins: usize,
) -> PyResult<()> {
    if num_bins < 2 {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "num_bins must be at least 2",
        ));
    }
    let edge_width = num_bins
        .checked_add(1)
        .ok_or_else(|| migration_size_overflow(operation))?;
    let mut total_elements = 0u128;
    let mut total_edges = 0u128;
    for matrix in matrices {
        let elements = checked_product(operation, matrix.nrows(), matrix.ncols())? as u128;
        total_elements = checked_u128_add(operation, total_elements, elements)?;
        let edges = checked_u128_mul(operation, matrix.ncols() as u128, edge_width as u128)?;
        total_edges = checked_u128_add(operation, total_edges, edges)?;
    }
    let label_bytes = checked_u128_mul(operation, total_elements, size_of::<usize>() as u128)?;
    let edge_bytes = checked_u128_mul(operation, total_edges, size_of::<f64>() as u128)?;
    let estimated_bytes = checked_u128_add(operation, label_bytes, edge_bytes)?;
    let element_work = checked_u128_mul(operation, total_elements, 6)?;
    let operations_hint = checked_u128_add(operation, element_work, total_edges)?;
    check_migration_resources(operation, estimated_bytes, operations_hint)
}

fn preflight_matrix_output(operation: &'static str, nrows: usize, ncols: usize) -> PyResult<usize> {
    let elements = checked_product(operation, nrows, ncols)?;
    // The core-owned projection and the compatibility flat Vec coexist. Allocation performed by
    // Python while converting that Vec is a separate allocator boundary and remains fallible.
    let two_f64_buffers = size_of::<f64>()
        .checked_mul(2)
        .ok_or_else(|| migration_size_overflow(operation))? as u128;
    let estimated_bytes = checked_u128_mul(operation, elements as u128, two_f64_buffers)?;
    check_migration_resources(operation, estimated_bytes, elements as u128)?;
    Ok(elements)
}

/// Convert a numpy array to a `MatRef` borrowing its buffer.
///
/// Requires a **C-contiguous** array. `as_slice()` also accepts a Fortran-contiguous buffer and
/// hands back its column-major bytes, which `MatRef` (row-major) would then read as the
/// transpose — silently producing wrong results for any non-square input (e.g. a transposed or
/// `order="F"` array). We reject non-C-contiguous input up front with an actionable error
/// instead. Non-finite values are rejected by `MatRef::new`.
fn array_to_matref<'a>(arr: &'a PyReadonlyArray2<f64>) -> PyResult<MatRef<'a>> {
    if !arr.is_c_contiguous() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Array must be C-contiguous; wrap it in np.ascontiguousarray(x) \
             (e.g. for a transposed or order='F' array) before passing it in",
        ));
    }
    let slice = arr
        .as_slice()
        .map_err(|_| pyo3::exceptions::PyValueError::new_err("Array must be C-contiguous"))?;
    let input_bytes = checked_u128_mul(
        "experimental.migration NumPy input",
        slice.len() as u128,
        size_of::<f64>() as u128,
    )?;
    check_migration_resources(
        "experimental.migration NumPy input",
        input_bytes,
        slice.len() as u128,
    )?;
    let arr_view = arr.as_array();
    let (nrows, ncols) = (arr_view.shape()[0], arr_view.shape()[1]);

    MatRef::new(slice, nrows, ncols)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid data: {e}")))
}

struct OwnedDiscreteMatrix {
    labels: Vec<usize>,
    nrows: usize,
    ncols: usize,
}

impl OwnedDiscreteMatrix {
    fn as_ref(&self) -> PyResult<DiscreteMatRef<'_>> {
        DiscreteMatRef::new(&self.labels, self.nrows, self.ncols).map_err(pid_err)
    }
}

/// Dense-encode a signed integer NumPy matrix without imposing numeric meaning on its labels.
fn array_to_discrete(arr: &PyReadonlyArray2<i64>) -> PyResult<OwnedDiscreteMatrix> {
    let length = categorical_array_len(arr)?;
    preflight_categorical_lengths("experimental.migration categorical encoding", &[length])?;
    let slice = arr.as_slice().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err("Categorical array must be C-contiguous")
    })?;
    let view = arr.as_array();
    let (nrows, ncols) = (view.shape()[0], view.shape()[1]);
    let mut unique_labels =
        try_vec_with_capacity("experimental.migration categorical labels", slice.len())?;
    unique_labels.extend_from_slice(slice);
    unique_labels.sort_unstable();
    unique_labels.dedup();

    let mut labels =
        try_vec_with_capacity("experimental.migration categorical codes", slice.len())?;
    for &label in slice {
        let code = unique_labels.binary_search(&label).map_err(|_| {
            pyo3::exceptions::PyRuntimeError::new_err(
                "categorical encoding lost a label after deterministic sorting",
            )
        })?;
        labels.push(code);
    }
    Ok(OwnedDiscreteMatrix {
        labels,
        nrows,
        ncols,
    })
}

#[derive(Clone, Copy)]
enum MetricSelection {
    Chebyshev,
    HyperbolicLorentz,
}

#[derive(Clone, Copy)]
enum SupportContractSelection {
    Stable(SupportContract),
    SmoothManifold,
}

const PYTHON_HYPERBOLIC_METRIC: HyperbolicMetric =
    HyperbolicMetric::lorentz(HyperbolicCurvature::NegativeOne);

fn parse_metric_selection(name: &str) -> PyResult<MetricSelection> {
    validate_config_token("metric", name)?;
    match name.to_lowercase().as_str() {
        "chebyshev" | "linf" | "max" => Ok(MetricSelection::Chebyshev),
        "hyperbolic" | "hyperbolic_lorentz" | "lorentz" => Ok(MetricSelection::HyperbolicLorentz),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown metric: '{}'. Valid metrics are: 'chebyshev' (aliases: 'linf', 'max'), \
             'hyperbolic_lorentz' (aliases: 'hyperbolic', 'lorentz', experimental report and diagnostic paths)",
            name
        ))),
    }
}

fn parse_metric(name: &str) -> PyResult<Metric> {
    match parse_metric_selection(name)? {
        MetricSelection::Chebyshev => Ok(Metric::Chebyshev),
        MetricSelection::HyperbolicLorentz => Err(pyo3::exceptions::PyValueError::new_err(
            "hyperbolic metrics are available only through explicitly hyperbolic report and diagnostic paths",
        )),
    }
}

fn parse_negative_handling(name: &str) -> PyResult<NegativeHandling> {
    validate_config_token("negative_handling", name)?;
    match name.to_lowercase().as_str() {
        "allow" | "raw" | "none" => Ok(NegativeHandling::Allow),
        "clamp_to_zero" | "clamp" | "zero" => Ok(NegativeHandling::ClampToZero),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown negative_handling: '{}'. Valid values are: 'allow', 'clamp_to_zero'",
            name
        ))),
    }
}

fn parse_support_contract_selection(name: &str) -> PyResult<SupportContractSelection> {
    validate_config_token("support_contract", name)?;
    match name.to_lowercase().as_str() {
        "unspecified" => Ok(SupportContractSelection::Stable(
            SupportContract::Unspecified,
        )),
        "assume_regular_full_dimensional" => Ok(SupportContractSelection::Stable(
            SupportContract::assume_regular_full_dimensional(),
        )),
        "assume_smooth_manifold" => Ok(SupportContractSelection::SmoothManifold),
        "atomic_or_mixed" => Ok(SupportContractSelection::Stable(
            SupportContract::KnownAtomicOrMixed,
        )),
        "quantized" => Ok(SupportContractSelection::Stable(
            SupportContract::KnownQuantized,
        )),
        "singular_or_lower_dimensional" => Ok(SupportContractSelection::Stable(
            SupportContract::KnownSingularOrLowerDimensional,
        )),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown support_contract: '{}'. Valid values are: 'unspecified', \
             'assume_regular_full_dimensional', 'assume_smooth_manifold', 'atomic_or_mixed', \
             'quantized', 'singular_or_lower_dimensional'",
            name
        ))),
    }
}

fn parse_support_contract(name: &str) -> PyResult<SupportContract> {
    match parse_support_contract_selection(name)? {
        SupportContractSelection::Stable(contract) => Ok(contract),
        SupportContractSelection::SmoothManifold => Err(pyo3::exceptions::PyValueError::new_err(
            "assume_smooth_manifold is available only with an explicitly hyperbolic report",
        )),
    }
}

#[allow(clippy::too_many_arguments)]
fn validate_legacy_ksg_pair_structure(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    k: usize,
    tie_epsilon: f64,
    metric: MetricSelection,
    support_contract: SupportContractSelection,
) -> PyResult<()> {
    if x.nrows() != y.nrows() {
        return Err(pid_err(pid_core::PidError::RowCountMismatch {
            context,
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        }));
    }
    if x.ncols() == 0 || y.ncols() == 0 {
        return Err(pid_err(pid_core::PidError::InvalidConfig {
            context,
            message: "x and y must have at least 1 column",
        }));
    }
    if matches!(metric, MetricSelection::HyperbolicLorentz) && (x.ncols() < 2 || y.ncols() < 2) {
        return Err(pid_err(pid_core::PidError::InvalidConfig {
            context,
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        }));
    }
    if tie_epsilon != 0.0 {
        return Err(pid_err(pid_core::PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        }));
    }
    if k == 0 || x.nrows() <= k {
        return Err(pid_err(pid_core::PidError::InvalidK {
            k,
            n_samples: x.nrows(),
        }));
    }

    match (metric, support_contract) {
        (
            MetricSelection::Chebyshev,
            SupportContractSelection::Stable(
                SupportContract::AssumeRegularFullDimensional {
                    density_regular: true,
                    finite_information: true,
                    ..
                },
            ),
        )
        | (MetricSelection::HyperbolicLorentz, SupportContractSelection::SmoothManifold) => Ok(()),
        (_, SupportContractSelection::Stable(SupportContract::Unspecified)) => {
            Err(pid_err(pid_core::PidError::SupportContractRequired {
                context,
            }))
        }
        (_, SupportContractSelection::Stable(contract)) => {
            Err(pid_err(pid_core::PidError::UnsupportedSupportContract {
                context,
                contract,
            }))
        }
        (_, SupportContractSelection::SmoothManifold) => {
            Err(pyo3::exceptions::PyValueError::new_err(format!(
                "{context}: support contract `assume_smooth_manifold` is unsupported by this continuous estimator"
            )))
        }
    }
}

fn metric_name(metric: Metric) -> &'static str {
    match metric {
        Metric::Chebyshev => "chebyshev",
        _ => "unknown",
    }
}

fn negative_handling_name(handling: NegativeHandling) -> &'static str {
    match handling {
        NegativeHandling::Allow => "allow",
        NegativeHandling::ClampToZero => "clamp_to_zero",
        _ => "unknown",
    }
}

fn support_contract_name(contract: SupportContract) -> &'static str {
    match contract {
        SupportContract::Unspecified => "unspecified",
        SupportContract::AssumeRegularFullDimensional { .. } => "assume_regular_full_dimensional",
        SupportContract::KnownAtomicOrMixed => "atomic_or_mixed",
        SupportContract::KnownQuantized => "quantized",
        SupportContract::KnownSingularOrLowerDimensional => "singular_or_lower_dimensional",
        _ => "unknown",
    }
}

fn ksg_method_status_name(status: KsgMethodStatus) -> &'static str {
    match status {
        KsgMethodStatus::RestrictedDomain => "restricted_domain",
        KsgMethodStatus::Experimental => "experimental",
        _ => "unknown",
    }
}

fn ksg_geometry_model_name(model: KsgGeometryModel) -> &'static str {
    match model {
        KsgGeometryModel::AmbientChebyshev => "ambient_chebyshev",
        _ => "unknown",
    }
}

fn ksg_warning_code(warning: KsgReportWarning) -> &'static str {
    match warning {
        KsgReportWarning::SampleDiagnosticsCannotProveSupport => {
            "sample_diagnostics_cannot_prove_support"
        }
        KsgReportWarning::MarginalNeighborShellPathology => "marginal_neighbor_shell_pathology",
        _ => "unknown_warning",
    }
}

fn hyperbolic_ksg_warning_code(warning: HyperbolicKsgReportWarning) -> &'static str {
    match warning {
        HyperbolicKsgReportWarning::SampleDiagnosticsCannotProveSupport => {
            "sample_diagnostics_cannot_prove_support"
        }
        HyperbolicKsgReportWarning::MarginalNeighborShellPathology => {
            "marginal_neighbor_shell_pathology"
        }
        HyperbolicKsgReportWarning::ConsistencyNotEstablished => {
            "hyperbolic_consistency_not_established"
        }
        _ => "unknown_warning",
    }
}

fn isx_method_name(method: IsxMethod) -> &'static str {
    match method {
        IsxMethod::EhrlichKsg => "ehrlich_ksg",
        IsxMethod::HeuristicSketch => "heuristic_sketch",
        IsxMethod::LocalMinKsg => "local_min_ksg",
        IsxMethod::DisjunctionFromLocalMi => "disjunction_from_local_mi",
        _ => "unknown",
    }
}

fn pid2_method_status_name(status: Pid2MethodStatus) -> &'static str {
    match status {
        Pid2MethodStatus::ExperimentalRestrictedDomain => "experimental_restricted_domain",
        Pid2MethodStatus::ExperimentalBaseline => "experimental_baseline",
        _ => "unknown",
    }
}

fn pid2_warning_code(warning: Pid2ReportWarning) -> &'static str {
    match warning {
        Pid2ReportWarning::PopulationModelNotVerified => "population_model_not_verified",
        Pid2ReportWarning::EqualAmbientDimensionOnlyNecessary => {
            "equal_ambient_dimension_only_necessary"
        }
        Pid2ReportWarning::RelativeSourceScalingDefinesEstimand => {
            "relative_source_scaling_defines_estimand"
        }
        Pid2ReportWarning::GeneralConsistencyNotEstablished => {
            "general_consistency_not_established"
        }
        Pid2ReportWarning::MixedEstimatorBiasProfiles => "mixed_estimator_bias_profiles",
        Pid2ReportWarning::LocalContributionCovarianceIsNotSamplingCovariance => {
            "local_contribution_covariance_is_not_sampling_covariance"
        }
        Pid2ReportWarning::SamplingUncertaintyNotCalibrated => {
            "sampling_uncertainty_not_calibrated"
        }
        Pid2ReportWarning::ExperimentalIsxBaseline => "experimental_isx_baseline",
        _ => "unknown_warning",
    }
}

fn pid3_method_status_name(status: Pid3MethodStatus) -> &'static str {
    match status {
        Pid3MethodStatus::ExperimentalMixedDimension => "experimental_mixed_dimension",
        _ => "unknown",
    }
}

fn parse_isx_method(name: &str) -> PyResult<IsxMethod> {
    validate_config_token("method", name)?;
    match name.to_lowercase().as_str() {
        "ehrlich_ksg" | "continuous" => Ok(IsxMethod::EhrlichKsg),
        "heuristic_sketch" | "sketch" => Ok(IsxMethod::HeuristicSketch),
        "local_min_ksg" | "local_min" => Ok(IsxMethod::LocalMinKsg),
        "disjunction_from_local_mi" | "disjunction" => Ok(IsxMethod::DisjunctionFromLocalMi),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown method: '{}'. Valid methods are: 'ehrlich_ksg', 'heuristic_sketch', \
             'local_min_ksg', 'disjunction_from_local_mi'",
            name
        ))),
    }
}

fn make_ksg_config(
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    negative_handling: &str,
    support_contract: &str,
) -> PyResult<KsgConfig> {
    Ok(KsgConfig::default()
        .with_k(k)
        .with_metric(parse_metric(metric)?)
        .with_tie_epsilon(tie_epsilon)
        .with_negative_handling(parse_negative_handling(negative_handling)?)
        .with_support_contract(parse_support_contract(support_contract)?))
}

fn make_isx_config(
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    method: &str,
    support_contract: &str,
) -> PyResult<IsxConfig> {
    Ok(IsxConfig {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        method: parse_isx_method(method)?,
        support_contract: parse_support_contract(support_contract)?,
    })
}

fn pid_err(e: pid_core::PidError) -> PyErr {
    use pid_core::PidError as E;
    let msg = e.to_string();
    match e {
        // Caller-supplied bad input / configuration → ValueError (consistent with the
        // contiguity and shape checks in `array_to_matref`).
        E::ShapeMismatch { .. }
        | E::InvalidConfig { .. }
        | E::RowCountMismatch { .. }
        | E::SourceDimensionMismatch { .. }
        | E::InvalidK { .. }
        | E::NonFiniteInput { .. }
        | E::SupportContractRequired { .. }
        | E::UnsupportedSupportContract { .. }
        | E::ObservedContinuousSampleIncompatibility { .. }
        | E::QuantizerOutOfRange { .. } => pyo3::exceptions::PyValueError::new_err(msg),
        E::ResourceLimitExceeded { .. }
        | E::AllocationFailed { .. }
        | E::SizeOverflow { .. }
        | E::SampleCountPrecisionExceeded { .. } => pyo3::exceptions::PyMemoryError::new_err(msg),
        // Estimator could not produce a result on otherwise-valid input → RuntimeError.
        E::NumericalInstability { .. } | E::AmbiguousKthNeighborShell { .. } => {
            pyo3::exceptions::PyRuntimeError::new_err(msg)
        }
        E::NotImplemented { .. } => pyo3::exceptions::PyNotImplementedError::new_err(msg),
        _ => pyo3::exceptions::PyRuntimeError::new_err(msg),
    }
}

/// Compute KSG mutual information.
///
/// Signed finite-sample estimates are returned by default. `negative_handling="clamp_to_zero"`
/// is an explicit presentation transform and must not be used before algebraic identities or
/// inference.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (x, y, k=3, metric="chebyshev", tie_epsilon=0.0, negative_handling="allow", support_contract="unspecified"))]
fn compute_mi(
    x: PyReadonlyArray2<f64>,
    y: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    negative_handling: &str,
    support_contract: &str,
) -> PyResult<f64> {
    let x_mat = array_to_matref(&x)?;
    let y_mat = array_to_matref(&y)?;
    let metric_selection = parse_metric_selection(metric)?;
    let negative_handling = parse_negative_handling(negative_handling)?;
    let support_contract = parse_support_contract_selection(support_contract)?;

    match (metric_selection, support_contract) {
        (MetricSelection::Chebyshev, SupportContractSelection::Stable(support_contract)) => {
            let cfg = KsgConfig::default()
                .with_k(k)
                .with_tie_epsilon(tie_epsilon)
                .with_negative_handling(negative_handling)
                .with_support_contract(support_contract);
            ksg_mi(x_mat, y_mat, &cfg).map_err(pid_err)
        }
        (MetricSelection::Chebyshev, SupportContractSelection::SmoothManifold) => {
            Err(pyo3::exceptions::PyValueError::new_err(
                "assume_smooth_manifold is available only with an explicitly hyperbolic report",
            ))
        }
        _ => {
            validate_legacy_ksg_pair_structure(
                "ksg_mi",
                x_mat,
                y_mat,
                k,
                tie_epsilon,
                metric_selection,
                support_contract,
            )?;
            Err(pyo3::exceptions::PyValueError::new_err(
                "hyperbolic MI is available only through compute_mi_report, which requires \
                 embedding_training_provenance and preserves experimental status and warnings",
            ))
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn mi_report_output(
    py: Python<'_>,
    estimate_nats: f64,
    n_samples: usize,
    k: usize,
    metric: &'static str,
    negative_handling: NegativeHandling,
    support_contract: &'static str,
    method_status: KsgMethodStatus,
    geometry_model: &'static str,
    curvature: Option<f64>,
    x_hyperbolic_dimension: Option<usize>,
    y_hyperbolic_dimension: Option<usize>,
    report_provenance: &KsgProvenance,
    warnings: Vec<BTreeMap<String, String>>,
    x_diagnostics: &ContinuousInputDiagnostics,
    y_diagnostics: &ContinuousInputDiagnostics,
    joint_shells: NeighborShellDiagnostics,
) -> PyResult<Py<PyAny>> {
    let config = PyDict::new(py);
    config.set_item("n_samples", n_samples)?;
    config.set_item("k", k)?;
    config.set_item("metric", metric)?;
    config.set_item(
        "negative_handling",
        negative_handling_name(negative_handling),
    )?;
    config.set_item("support_contract", support_contract)?;

    let method = PyDict::new(py);
    method.set_item("status", ksg_method_status_name(method_status))?;
    method.set_item("geometry_model", geometry_model)?;
    method.set_item("curvature", curvature)?;
    method.set_item("x_hyperbolic_dimension", x_hyperbolic_dimension)?;
    method.set_item("y_hyperbolic_dimension", y_hyperbolic_dimension)?;

    let provenance = PyDict::new(py);
    provenance.set_item(
        "preprocessing_description",
        report_provenance.preprocessing_description(),
    )?;
    provenance.set_item(
        "observation_model_description",
        report_provenance.observation_model_description(),
    )?;
    provenance.set_item(
        "embedding_training_provenance",
        report_provenance.embedding_training_provenance(),
    )?;

    let diagnostics = PyDict::new(py);
    diagnostics.set_item("x", continuous_input_diagnostics_output(py, x_diagnostics)?)?;
    diagnostics.set_item("y", continuous_input_diagnostics_output(py, y_diagnostics)?)?;
    diagnostics.set_item(
        "joint_shells",
        neighbor_shell_diagnostics_output(py, joint_shells)?,
    )?;

    let output = PyDict::new(py);
    output.set_item("estimate_nats", estimate_nats)?;
    output.set_item("config", config)?;
    output.set_item("method", method)?;
    output.set_item("provenance", provenance)?;
    output.set_item("warnings", warnings)?;
    output.set_item("diagnostics", diagnostics)?;
    Ok(output.into_any().unbind())
}

/// Compute KSG mutual information with interpretation-critical metadata and diagnostics.
///
/// The two provenance descriptions are required keyword-only arguments and must be nonempty.
/// Hyperbolic reports additionally require `embedding_training_provenance`. Sample diagnostics can
/// identify observations incompatible with ideal estimator conditions, but cannot determine their
/// cause or prove continuity or estimator consistency.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (x, y, k=3, metric="chebyshev", tie_epsilon=0.0, negative_handling="allow", support_contract="unspecified", *, preprocessing_description, observation_model_description, embedding_training_provenance=None))]
fn compute_mi_report(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    y: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    negative_handling: &str,
    support_contract: &str,
    preprocessing_description: &str,
    observation_model_description: &str,
    embedding_training_provenance: Option<&str>,
) -> PyResult<Py<PyAny>> {
    let x_mat = array_to_matref(&x)?;
    let y_mat = array_to_matref(&y)?;
    let metric_selection = parse_metric_selection(metric)?;
    let negative_handling = parse_negative_handling(negative_handling)?;
    let support_contract = parse_support_contract_selection(support_contract)?;
    if matches!(metric_selection, MetricSelection::Chebyshev)
        && matches!(support_contract, SupportContractSelection::SmoothManifold)
    {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "assume_smooth_manifold is available only with an explicitly hyperbolic report",
        ));
    }
    let provenance = KsgProvenance::new(
        preprocessing_description,
        observation_model_description,
        embedding_training_provenance,
    )
    .map_err(pid_err)?;

    match metric_selection {
        MetricSelection::Chebyshev => {
            let SupportContractSelection::Stable(support_contract) = support_contract else {
                validate_legacy_ksg_pair_structure(
                    "ksg_mi_report",
                    x_mat,
                    y_mat,
                    k,
                    tie_epsilon,
                    metric_selection,
                    support_contract,
                )?;
                return Err(pyo3::exceptions::PyRuntimeError::new_err(
                    "legacy KSG validation accepted an incompatible support contract",
                ));
            };
            let cfg = KsgConfig::default()
                .with_k(k)
                .with_tie_epsilon(tie_epsilon)
                .with_negative_handling(negative_handling)
                .with_support_contract(support_contract);
            let report = ksg_mi_report(x_mat, y_mat, &cfg, &provenance).map_err(pid_err)?;
            let warnings = report
                .warnings
                .iter()
                .map(|&warning| {
                    BTreeMap::from([
                        ("code".to_string(), ksg_warning_code(warning).to_string()),
                        ("message".to_string(), warning.message().to_string()),
                    ])
                })
                .collect::<Vec<_>>();
            mi_report_output(
                py,
                report.estimate_nats,
                report.n_samples,
                report.k,
                metric_name(report.metric),
                report.negative_handling,
                support_contract_name(report.support_contract),
                report.method_status,
                ksg_geometry_model_name(report.geometry_model),
                None,
                report.x_hyperbolic_dimension,
                report.y_hyperbolic_dimension,
                &report.provenance,
                warnings,
                &report.x_diagnostics,
                &report.y_diagnostics,
                report.joint_shells,
            )
        }
        MetricSelection::HyperbolicLorentz => {
            validate_legacy_ksg_pair_structure(
                "ksg_mi_report",
                x_mat,
                y_mat,
                k,
                tie_epsilon,
                metric_selection,
                support_contract,
            )?;
            let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HyperbolicCurvature::NegativeOne)
                .with_k(k)
                .with_tie_epsilon(tie_epsilon)
                .with_negative_handling(negative_handling);
            let report =
                hyperbolic_ksg_mi_report(x_mat, y_mat, &cfg, &provenance).map_err(pid_err)?;
            let warnings = report
                .warnings
                .iter()
                .map(|&warning| {
                    BTreeMap::from([
                        (
                            "code".to_string(),
                            hyperbolic_ksg_warning_code(warning).to_string(),
                        ),
                        ("message".to_string(), warning.message().to_string()),
                    ])
                })
                .collect::<Vec<_>>();
            mi_report_output(
                py,
                report.estimate_nats,
                report.n_samples,
                report.k,
                "hyperbolic_lorentz",
                report.negative_handling,
                "assume_smooth_manifold",
                report.method_status,
                "lorentz_hyperboloid",
                Some(report.curvature.sectional_curvature()),
                Some(report.x_hyperbolic_dimension),
                Some(report.y_hyperbolic_dimension),
                &report.provenance,
                warnings,
                &report.x_diagnostics,
                &report.y_diagnostics,
                report.joint_shells,
            )
        }
    }
}

/// Compute continuous I_sx_intersect redundancy.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (s1, s2, target, k=3, method="ehrlich_ksg", metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified"))]
fn compute_redundancy(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    method: &str,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
) -> PyResult<f64> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_isx_config(k, metric, tie_epsilon, method, support_contract)?;

    isx_redundancy(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)
}

/// Co-information I(S1;T) + I(S2;T) - I(S1,S2;T), in nats.
///
/// The MI terms are always computed unclamped (the core forces `NegativeHandling::Allow`):
/// clamping a term before the subtraction would silently break the identity. There is
/// deliberately no `negative_handling` parameter here — it would be a no-op.
#[pyfunction]
#[pyo3(signature = (s1, s2, target, k=3, metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified"))]
fn compute_co_information(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
) -> PyResult<f64> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, "allow", support_contract)?;

    co_information_pairwise(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)
}

/// 2-source PID atoms (redundancy / unique_s1 / unique_s2 / synergy) from KSG MI plus the
/// continuous shared-exclusions redundancy `I^sx_∩`, in nats.
///
/// The MI terms feeding the atoms are always computed unclamped (the core forces
/// `NegativeHandling::Allow`) so that `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)` holds by
/// construction up to floating-point roundoff. There is deliberately no `negative_handling`
/// parameter here — it would be a no-op.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (s1, s2, target, k=3, method="ehrlich_ksg", metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified"))]
fn compute_pid2(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    method: &str,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = Pid2Config {
        ksg: make_ksg_config(k, metric, tie_epsilon, "allow", support_contract)?,
        isx: make_isx_config(k, metric, tie_epsilon, method, support_contract)?,
    };
    let out = pid2_isx(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert("redundancy".to_string(), out.redundancy);
    map.insert("unique_s1".to_string(), out.unique_s1);
    map.insert("unique_s2".to_string(), out.unique_s2);
    map.insert("synergy".to_string(), out.synergy);
    Ok(map)
}

/// Compute a complete two-source constituent-estimator report.
///
/// This keeps both estimator configurations, restricted/experimental method status, support and
/// dimension metadata, signed MI/redundancy terms, atoms, stable warnings, and separate
/// caller-declared preprocessing descriptions for each source and target. The provenance text is
/// checked only for nonemptiness. This is intentionally not called a full diagnostic report: ISX
/// disjunction-neighborhood counts/radii are not exposed by this surface.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (s1, s2, target, k=3, method="ehrlich_ksg", metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified", *, source1_preprocessing_description, source2_preprocessing_description, target_preprocessing_description, observation_model_description))]
fn compute_pid2_report(
    py: Python<'_>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    method: &str,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
    source1_preprocessing_description: &str,
    source2_preprocessing_description: &str,
    target_preprocessing_description: &str,
    observation_model_description: &str,
) -> PyResult<Py<PyAny>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let target_mat = array_to_matref(&target)?;
    let cfg = Pid2Config {
        ksg: make_ksg_config(k, metric, tie_epsilon, "allow", support_contract)?,
        isx: make_isx_config(k, metric, tie_epsilon, method, support_contract)?,
    };
    let provenance = Pid2Provenance::new(
        try_owned_provenance(
            "source1_preprocessing_description",
            source1_preprocessing_description,
        )?,
        try_owned_provenance(
            "source2_preprocessing_description",
            source2_preprocessing_description,
        )?,
        try_owned_provenance(
            "target_preprocessing_description",
            target_preprocessing_description,
        )?,
        try_owned_provenance(
            "observation_model_description",
            observation_model_description,
        )?,
    )
    .map_err(pid_err)?;
    let report = pid2_isx_report(s1_mat, s2_mat, target_mat, &cfg, &provenance).map_err(pid_err)?;

    let atoms = PyDict::new(py);
    atoms.set_item("redundancy", report.atoms.redundancy)?;
    atoms.set_item("unique_s1", report.atoms.unique_s1)?;
    atoms.set_item("unique_s2", report.atoms.unique_s2)?;
    atoms.set_item("synergy", report.atoms.synergy)?;

    let estimate_terms = PyDict::new(py);
    estimate_terms.set_item("mi_s1_t", report.estimate_terms.mi_s1_t)?;
    estimate_terms.set_item("mi_s2_t", report.estimate_terms.mi_s2_t)?;
    estimate_terms.set_item("mi_s1s2_t", report.estimate_terms.mi_s1s2_t)?;
    estimate_terms.set_item("redundancy_isx", report.estimate_terms.redundancy_isx)?;

    let config = PyDict::new(py);
    config.set_item("n_samples", report.n_samples)?;
    config.set_item("k", report.supplied_ksg_config.k)?;
    config.set_item("metric", metric_name(report.supplied_ksg_config.metric))?;
    config.set_item("tie_epsilon", report.supplied_ksg_config.tie_epsilon)?;
    config.set_item(
        "support_contract",
        support_contract_name(report.support_contract),
    )?;
    config.set_item(
        "supplied_ksg_negative_handling",
        negative_handling_name(report.supplied_ksg_config.negative_handling),
    )?;
    config.set_item(
        "effective_negative_handling",
        negative_handling_name(report.effective_negative_handling),
    )?;
    config.set_item(
        "isx_method",
        isx_method_name(report.supplied_isx_config.method),
    )?;
    config.set_item(
        "source_ambient_dimensions",
        report.source_ambient_dimensions,
    )?;
    config.set_item("target_ambient_dimension", report.target_ambient_dimension)?;

    let method = PyDict::new(py);
    method.set_item("status", pid2_method_status_name(report.method_status))?;

    let provenance = PyDict::new(py);
    provenance.set_item(
        "source1_preprocessing_description",
        report.provenance.source1_preprocessing_description(),
    )?;
    provenance.set_item(
        "source2_preprocessing_description",
        report.provenance.source2_preprocessing_description(),
    )?;
    provenance.set_item(
        "target_preprocessing_description",
        report.provenance.target_preprocessing_description(),
    )?;
    provenance.set_item(
        "observation_model_description",
        report.provenance.observation_model_description(),
    )?;

    let warnings = report
        .warnings
        .iter()
        .map(|&warning| {
            BTreeMap::from([
                ("code".to_string(), pid2_warning_code(warning).to_string()),
                ("message".to_string(), warning.message().to_string()),
            ])
        })
        .collect::<Vec<_>>();

    let output = PyDict::new(py);
    output.set_item("atoms", atoms)?;
    output.set_item("estimate_terms", estimate_terms)?;
    output.set_item("config", config)?;
    output.set_item("method", method)?;
    output.set_item("provenance", provenance)?;
    output.set_item("warnings", warnings)?;
    Ok(output.into_any().unbind())
}

/// Shannon-invariant screening quantities, in nats: the three MI terms, co-information,
/// and the r̄ / v̄ statistics.
///
/// Every term is computed unclamped (`NegativeHandling::Allow`) so the returned dict is
/// internally consistent: `co_information == mi_s1_t + mi_s2_t - mi_s1s2_t`, and r̄/v̄ are
/// built from the same unclamped MI values. There is deliberately no `negative_handling`
/// parameter here — mixing clamped MI terms with the identity-based quantities would make
/// the dict incoherent.
#[pyfunction]
#[pyo3(signature = (s1, s2, target, k=3, metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified"))]
fn compute_invariants(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, "allow", support_contract)?;
    let mi_s1_t = ksg_mi(s1_mat, t_mat, &cfg).map_err(pid_err)?;
    let mi_s2_t = ksg_mi(s2_mat, t_mat, &cfg).map_err(pid_err)?;
    let mi_s1s2_t = ksg_mi_concat_xy(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)?;
    let ci = co_information_pairwise(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert("mi_s1_t".to_string(), mi_s1_t);
    map.insert("mi_s2_t".to_string(), mi_s2_t);
    map.insert("mi_s1s2_t".to_string(), mi_s1s2_t);
    map.insert("co_information".to_string(), ci);
    map.insert(
        "r_bar".to_string(),
        average_degree_of_redundancy(&[mi_s1_t, mi_s2_t], mi_s1s2_t)
            .require_value("compute_invariants: r_bar is undefined or unstable")
            .map_err(pid_err)?,
    );
    map.insert(
        "v_bar".to_string(),
        average_degree_of_vulnerability(mi_s1s2_t, &[mi_s2_t, mi_s1_t])
            .require_value("compute_invariants: v_bar is undefined or unstable")
            .map_err(pid_err)?,
    );
    Ok(map)
}

fn neighbor_shell_diagnostics_output(
    py: Python<'_>,
    diagnostics: NeighborShellDiagnostics,
) -> PyResult<Py<PyAny>> {
    let radii = PyDict::new(py);
    radii.set_item("min", diagnostics.kth_radius.min)?;
    radii.set_item("p10", diagnostics.kth_radius.p10)?;
    radii.set_item("median", diagnostics.kth_radius.median)?;
    radii.set_item("p90", diagnostics.kth_radius.p90)?;
    radii.set_item("p99", diagnostics.kth_radius.p99)?;
    radii.set_item("max", diagnostics.kth_radius.max)?;

    let shells = PyDict::new(py);
    shells.set_item("query_count", diagnostics.query_count)?;
    shells.set_item("zero_radius_queries", diagnostics.zero_radius_queries)?;
    shells.set_item(
        "ambiguous_positive_shell_queries",
        diagnostics.ambiguous_positive_shell_queries,
    )?;
    shells.set_item("kth_radius", radii)?;
    Ok(shells.into_any().unbind())
}

fn continuous_input_diagnostics_output(
    py: Python<'_>,
    diagnostics: &ContinuousInputDiagnostics,
) -> PyResult<Py<PyAny>> {
    let coordinate_count = diagnostics.coordinates.len();
    let list_pointer_bytes = checked_u128_mul(
        "experimental.migration diagnostic coordinate output",
        coordinate_count as u128,
        size_of::<usize>() as u128,
    )?;
    check_migration_resources(
        "experimental.migration diagnostic coordinate output",
        list_pointer_bytes,
        checked_u128_mul(
            "experimental.migration diagnostic coordinate output",
            coordinate_count as u128,
            5,
        )?,
    )?;
    let coordinates = PyList::empty(py);
    for coordinate in &diagnostics.coordinates {
        let entry = PyDict::new(py);
        entry.set_item("coordinate", coordinate.coordinate)?;
        entry.set_item("unique_values", coordinate.unique_values)?;
        entry.set_item("tied_groups", coordinate.tied_groups)?;
        entry.set_item("repeated_observations", coordinate.repeated_observations)?;
        entry.set_item("max_multiplicity", coordinate.max_multiplicity)?;
        coordinates.append(entry)?;
    }

    let output = PyDict::new(py);
    output.set_item("n_samples", diagnostics.n_samples)?;
    output.set_item("ambient_dimension", diagnostics.ambient_dimension)?;
    output.set_item("unique_rows", diagnostics.unique_rows)?;
    output.set_item("tied_row_groups", diagnostics.tied_row_groups)?;
    output.set_item("repeated_rows", diagnostics.repeated_rows)?;
    output.set_item("max_row_multiplicity", diagnostics.max_row_multiplicity)?;
    output.set_item("coordinates", coordinates)?;
    output.set_item(
        "marginal_shells",
        neighbor_shell_diagnostics_output(py, diagnostics.marginal_shells)?,
    )?;
    Ok(output.into_any().unbind())
}

/// Inspect exact cardinalities and independently selected marginal k-th-neighbor shells.
///
/// Exact ties are incompatible with ideal i.i.d., unrounded continuous-sample conditions, but do
/// not identify their cause or population support. Their absence cannot prove population
/// continuity. This diagnostic remains available for atomic, quantized, mixed, and singular inputs
/// so callers can select an estimator with a matching estimand.
#[pyfunction]
#[pyo3(signature = (x, k=3, metric="chebyshev"))]
fn continuous_input_diagnostics(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
) -> PyResult<Py<PyAny>> {
    let x_mat = array_to_matref(&x)?;
    let diagnostics = match parse_metric_selection(metric)? {
        MetricSelection::Chebyshev => {
            core_continuous_input_diagnostics(x_mat, k, Metric::Chebyshev)
        }
        MetricSelection::HyperbolicLorentz => {
            hyperbolic_continuous_input_diagnostics(x_mat, k, PYTHON_HYPERBOLIC_METRIC)
        }
    }
    .map_err(pid_err)?;
    continuous_input_diagnostics_output(py, &diagnostics)
}

/// Estimate intrinsic dimension using Levina-Bickel (kNN MLE).
#[pyfunction]
#[pyo3(signature = (x, k=10, metric="chebyshev"))]
fn estimate_intrinsic_dimension(x: PyReadonlyArray2<f64>, k: usize, metric: &str) -> PyResult<f64> {
    let x_mat = array_to_matref(&x)?;
    match parse_metric_selection(metric)? {
        MetricSelection::Chebyshev => {
            let cfg = IntrinsicDimConfig::default()
                .with_k(k)
                .with_metric(Metric::Chebyshev);
            intrinsic_dimension_levina_bickel(x_mat, &cfg)
        }
        MetricSelection::HyperbolicLorentz => {
            let cfg = HyperbolicIntrinsicDimConfig::new(PYTHON_HYPERBOLIC_METRIC).with_k(k);
            hyperbolic_intrinsic_dimension_levina_bickel(x_mat, &cfg)
        }
    }
    .map_err(pid_err)
}

/// Deprecated compatibility helper returning only the mean sampled four-point delta.
///
/// This does not estimate the sup-defined Gromov hyperbolicity constant. New code should use
/// `sampled_four_point_delta_summary` and inspect its quantiles, sampled maximum, diameter, and
/// Monte Carlo standard error.
#[pyfunction]
#[pyo3(warn(
    message = "estimate_gromov_delta is deprecated; use sampled_four_point_delta_summary",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (x, n_samples=1000, metric="chebyshev", seed=42))]
fn estimate_gromov_delta(
    x: PyReadonlyArray2<f64>,
    n_samples: usize,
    metric: &str,
    seed: u64,
) -> PyResult<f64> {
    let x_mat = array_to_matref(&x)?;
    let summary = match parse_metric_selection(metric)? {
        MetricSelection::Chebyshev => {
            let cfg = HyperbolicityConfig::default()
                .with_n_samples(n_samples)
                .with_metric(Metric::Chebyshev)
                .with_seed(seed);
            core_four_point_delta_summary(x_mat, &cfg)
        }
        MetricSelection::HyperbolicLorentz => {
            let cfg = HyperbolicFourPointConfig::new(PYTHON_HYPERBOLIC_METRIC)
                .with_n_samples(n_samples)
                .with_seed(seed);
            hyperbolic_sampled_four_point_delta_summary(x_mat, &cfg)
        }
    }
    .map_err(pid_err)?;
    Ok(summary.mean)
}

/// Return descriptive statistics for deterministically sampled four-point deltas.
///
/// The returned `max` is the largest sampled value, not the defining supremum over all
/// quadruples. Normalized values use `2 * delta / diameter` and are `None` when the finite
/// dataset has zero diameter. The Monte Carlo standard error fields are `None` for one sample.
#[pyfunction]
#[pyo3(signature = (x, n_samples=1000, metric="chebyshev", seed=42))]
fn sampled_four_point_delta_summary(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    n_samples: usize,
    metric: &str,
    seed: u64,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    let summary = match parse_metric_selection(metric)? {
        MetricSelection::Chebyshev => {
            let cfg = HyperbolicityConfig::default()
                .with_n_samples(n_samples)
                .with_metric(Metric::Chebyshev)
                .with_seed(seed);
            core_four_point_delta_summary(x_mat, &cfg)
        }
        MetricSelection::HyperbolicLorentz => {
            let cfg = HyperbolicFourPointConfig::new(PYTHON_HYPERBOLIC_METRIC)
                .with_n_samples(n_samples)
                .with_seed(seed);
            hyperbolic_sampled_four_point_delta_summary(x_mat, &cfg)
        }
    }
    .map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert(
        "sample_count".to_string(),
        summary.sample_count.into_pyobject(py)?.into_any().unbind(),
    );
    for (name, value) in [
        ("mean", summary.mean),
        ("median", summary.median),
        ("p90", summary.p90),
        ("p99", summary.p99),
        ("max", summary.max),
        ("diameter", summary.diameter),
    ] {
        map.insert(
            name.to_string(),
            value.into_pyobject(py)?.into_any().unbind(),
        );
    }
    for (name, value) in [
        (
            "monte_carlo_standard_error",
            summary.monte_carlo_standard_error,
        ),
        ("normalized_mean", summary.normalized_mean),
        ("normalized_median", summary.normalized_median),
        ("normalized_p90", summary.normalized_p90),
        ("normalized_p99", summary.normalized_p99),
        ("normalized_max", summary.normalized_max),
        (
            "normalized_monte_carlo_standard_error",
            summary.normalized_monte_carlo_standard_error,
        ),
    ] {
        map.insert(
            name.to_string(),
            value.into_pyobject(py)?.into_any().unbind(),
        );
    }
    Ok(map)
}

/// Compute distance concentration statistics.
/// Returns a dict with summary statistics including:
/// - pairwise min/max/mean/std/cv
/// - nearest-neighbor mean/cv and nn_over_pairwise_mean
#[pyfunction]
#[pyo3(signature = (x, metric="chebyshev"))]
fn distance_stats(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    metric: &str,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    let stats = match parse_metric_selection(metric)? {
        MetricSelection::Chebyshev => {
            let cfg = DistanceConcentrationConfig::default().with_metric(Metric::Chebyshev);
            distance_concentration_stats(x_mat, &cfg)
        }
        MetricSelection::HyperbolicLorentz => {
            let cfg = HyperbolicDistanceConcentrationConfig::new(PYTHON_HYPERBOLIC_METRIC);
            hyperbolic_distance_concentration_stats(x_mat, &cfg)
        }
    }
    .map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert(
        "pairwise_count".to_string(),
        stats.pairwise_count.into_pyobject(py)?.into_any().unbind(),
    );
    for (name, value) in [
        ("pairwise_min", stats.pairwise_min),
        ("pairwise_max", stats.pairwise_max),
        ("pairwise_mean", stats.pairwise_mean),
        ("pairwise_std", stats.pairwise_std),
        ("pairwise_cv", stats.pairwise_cv),
        ("nn_min", stats.nn_min),
        ("nn_max", stats.nn_max),
        ("nn_mean", stats.nn_mean),
        ("nn_cv", stats.nn_cv),
        ("nn_over_pairwise_mean", stats.nn_over_pairwise_mean),
    ] {
        map.insert(
            name.to_string(),
            value.into_pyobject(py)?.into_any().unbind(),
        );
    }
    Ok(map)
}

/// Compute only ambient-dimension-compatible continuous PID3 coordinates and atoms.
///
/// Redundancy coordinates whose branches have unequal ambient dimensions are returned with
/// `value=None`. An atom is returned with `value=None` whenever its exact Möbius expansion depends
/// on any unavailable redundancy; `unavailable_redundancies` names those dependencies using the
/// canonical bitmask-list keys. No values are imputed, so the available atoms are not a complete
/// 18-atom decomposition. Separate source/target preprocessing and observation-model provenance is
/// required and returned with the metadata; its text is checked only for nonemptiness.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (s1, s2, s3, target, k=3, metric="chebyshev", tie_epsilon=0.0, support_contract="unspecified", *, source1_preprocessing_description, source2_preprocessing_description, source3_preprocessing_description, target_preprocessing_description, observation_model_description))]
fn compute_pid3_partial(
    py: Python<'_>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    s3: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    support_contract: &str,
    source1_preprocessing_description: &str,
    source2_preprocessing_description: &str,
    source3_preprocessing_description: &str,
    target_preprocessing_description: &str,
    observation_model_description: &str,
) -> PyResult<Py<PyAny>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let s3_mat = array_to_matref(&s3)?;
    let target_mat = array_to_matref(&target)?;
    let cfg = Pid3Config {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        support_contract: parse_support_contract(support_contract)?,
        experimental_allow_mixed_dimension_lattice: false,
    };
    let provenance = Pid3Provenance::new(
        try_owned_provenance(
            "source1_preprocessing_description",
            source1_preprocessing_description,
        )?,
        try_owned_provenance(
            "source2_preprocessing_description",
            source2_preprocessing_description,
        )?,
        try_owned_provenance(
            "source3_preprocessing_description",
            source3_preprocessing_description,
        )?,
        try_owned_provenance(
            "target_preprocessing_description",
            target_preprocessing_description,
        )?,
        try_owned_provenance(
            "observation_model_description",
            observation_model_description,
        )?,
    )
    .map_err(pid_err)?;
    let report = pid3_isx_partial_report(s1_mat, s2_mat, s3_mat, target_mat, &cfg, &provenance)
        .map_err(pid_err)?;
    let out = &report.result;

    let redundancies = PyDict::new(py);
    for redundancy in &out.redundancies {
        let entry = PyDict::new(py);
        entry.set_item("value", redundancy.value)?;
        entry.set_item("branch_dimensions", &redundancy.branch_dimensions)?;
        redundancies.set_item(format!("{:?}", redundancy.antichain.sets()), entry)?;
    }

    let atoms = PyDict::new(py);
    for atom in &out.atoms {
        let entry = PyDict::new(py);
        let unavailable_redundancies = atom
            .unavailable_redundancies
            .iter()
            .map(|antichain| format!("{:?}", antichain.sets()))
            .collect::<Vec<_>>();
        entry.set_item("value", atom.value)?;
        entry.set_item("unavailable_redundancies", unavailable_redundancies)?;
        atoms.set_item(format!("{:?}", atom.antichain.sets()), entry)?;
    }

    let output = PyDict::new(py);
    output.set_item("n_samples", out.n_samples)?;
    output.set_item("k", out.k)?;
    output.set_item("metric", metric_name(out.metric))?;
    output.set_item(
        "support_contract",
        support_contract_name(out.support_contract),
    )?;
    output.set_item("source_ambient_dimensions", out.source_ambient_dimensions)?;
    output.set_item("target_ambient_dimension", out.target_ambient_dimension)?;
    output.set_item(
        "method_status",
        "ambient_dimension_compatible_but_unvalidated",
    )?;
    output.set_item("experimental", true)?;
    output.set_item("warnings", &out.warnings)?;
    let provenance = PyDict::new(py);
    provenance.set_item(
        "source1_preprocessing_description",
        report.provenance.source1_preprocessing_description(),
    )?;
    provenance.set_item(
        "source2_preprocessing_description",
        report.provenance.source2_preprocessing_description(),
    )?;
    provenance.set_item(
        "source3_preprocessing_description",
        report.provenance.source3_preprocessing_description(),
    )?;
    provenance.set_item(
        "target_preprocessing_description",
        report.provenance.target_preprocessing_description(),
    )?;
    provenance.set_item(
        "observation_model_description",
        report.provenance.observation_model_description(),
    )?;
    output.set_item("provenance", provenance)?;
    output.set_item("redundancies", redundancies)?;
    output.set_item("atoms", atoms)?;
    Ok(output.into_any().unbind())
}

/// Compute the continuous 3-source `I^sx_∩` PID (18 atoms via Möbius inversion on the
/// redundancy lattice; Ehrlich et al. 2024 kNN estimator — not the discrete SxPID of
/// `compute_discrete_sxpid3`).
///
/// The nested `redundancies` and `atoms` mappings use the antichain's source-subset bitmasks in
/// the same `"[1, 6]"` list format used by the discrete PID functions (bit `i` set ⇔ source `i+1`
/// in the subset; e.g. `"[1, 2, 4]"` is the bottom node `{{1},{2},{3}}` and `"[7]"` is the top
/// node `{{1,2,3}}`). Status, support, dimensions, and warnings remain attached to the numbers.
///
/// The full lattice necessarily compares singleton source neighborhoods with concatenated-pair
/// neighborhoods of a different ambient dimension. It is therefore disabled by default. Passing
/// `experimental_allow_mixed_dimension_lattice=True` preserves the implementation for reference
/// reproduction and explicitly labelled diagnostics; it does not validate the resulting atoms as
/// mixed-dimensional scientific estimates. Separate caller-declared preprocessing descriptions
/// for each source/target and an observation-model description are required keyword arguments;
/// they are checked only for nonemptiness and returned under `provenance`.
#[pyfunction]
#[pyo3(signature = (s1, s2, s3, target, k=3, metric="chebyshev", tie_epsilon=0.0, experimental_allow_mixed_dimension_lattice=false, support_contract="unspecified", *, source1_preprocessing_description, source2_preprocessing_description, source3_preprocessing_description, target_preprocessing_description, observation_model_description))]
#[allow(clippy::too_many_arguments)]
fn compute_pid3(
    py: Python<'_>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    s3: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    experimental_allow_mixed_dimension_lattice: bool,
    support_contract: &str,
    source1_preprocessing_description: &str,
    source2_preprocessing_description: &str,
    source3_preprocessing_description: &str,
    target_preprocessing_description: &str,
    observation_model_description: &str,
) -> PyResult<Py<PyAny>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let s3_mat = array_to_matref(&s3)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = Pid3Config {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        support_contract: parse_support_contract(support_contract)?,
        experimental_allow_mixed_dimension_lattice,
    };
    let provenance = Pid3Provenance::new(
        try_owned_provenance(
            "source1_preprocessing_description",
            source1_preprocessing_description,
        )?,
        try_owned_provenance(
            "source2_preprocessing_description",
            source2_preprocessing_description,
        )?,
        try_owned_provenance(
            "source3_preprocessing_description",
            source3_preprocessing_description,
        )?,
        try_owned_provenance(
            "target_preprocessing_description",
            target_preprocessing_description,
        )?,
        try_owned_provenance(
            "observation_model_description",
            observation_model_description,
        )?,
    )
    .map_err(pid_err)?;
    let report =
        pid3_isx_report(s1_mat, s2_mat, s3_mat, t_mat, &cfg, &provenance).map_err(pid_err)?;
    let out = &report.result;

    let redundancies = PyDict::new(py);
    for redundancy in &out.redundancies {
        redundancies.set_item(
            format!("{:?}", redundancy.antichain.sets()),
            redundancy.value,
        )?;
    }

    let atoms = PyDict::new(py);
    for atom in &out.atoms {
        // Bitmask-list key (e.g. "[1, 6]"), matching the discrete PID functions — NOT the
        // struct's Debug output, which leaks internal zero-padding and is not a stable contract.
        atoms.set_item(format!("{:?}", atom.antichain.sets()), atom.value)?;
    }

    let output = PyDict::new(py);
    output.set_item("n_samples", out.n_samples)?;
    output.set_item("k", out.k)?;
    output.set_item("metric", metric_name(out.metric))?;
    output.set_item(
        "support_contract",
        support_contract_name(out.support_contract),
    )?;
    output.set_item("source_ambient_dimensions", out.source_ambient_dimensions)?;
    output.set_item("target_ambient_dimension", out.target_ambient_dimension)?;
    output.set_item("method_status", pid3_method_status_name(out.method_status))?;
    output.set_item(
        "experimental",
        matches!(
            out.method_status,
            Pid3MethodStatus::ExperimentalMixedDimension
        ),
    )?;
    output.set_item("warnings", &out.warnings)?;
    let provenance = PyDict::new(py);
    provenance.set_item(
        "source1_preprocessing_description",
        report.provenance.source1_preprocessing_description(),
    )?;
    provenance.set_item(
        "source2_preprocessing_description",
        report.provenance.source2_preprocessing_description(),
    )?;
    provenance.set_item(
        "source3_preprocessing_description",
        report.provenance.source3_preprocessing_description(),
    )?;
    provenance.set_item(
        "target_preprocessing_description",
        report.provenance.target_preprocessing_description(),
    )?;
    provenance.set_item(
        "observation_model_description",
        report.provenance.observation_model_description(),
    )?;
    output.set_item("provenance", provenance)?;
    output.set_item("redundancies", redundancies)?;
    output.set_item("atoms", atoms)?;
    Ok(output.into_any().unbind())
}

/// Compute an exploratory same-sample, equal-width-quantized two-source Williams–Beer `I_min` PID.
///
/// This deprecated migration adapter derives per-column ranges and bins from the same evaluated
/// rows, changes the variables and estimand, consumes the Rust provenance wrapper, and returns only
/// a flat numeric dictionary. Bin assignment uses the internal exact binary64-significand route,
/// not the stable fitted-edge quantizer. It is not a discrete counterpart or validation fallback
/// for a failed continuous nearest-neighbor route, and no mapping to continuous shared exclusions
/// is claimed.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated adapter fits quantization on the evaluated sample, returns Williams-Beer I_min rather than shared exclusions, and discards num_bins-only wrapper/input/PMF provenance; it is not a KSG or Ehrlich fallback",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s1, s2, target, num_bins=10))]
fn compute_discrete_pid2(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    validate_aligned_rows(
        "compute_discrete_pid2",
        &[s1_mat.nrows(), s2_mat.nrows(), t_mat.nrows()],
    )?;
    preflight_quantized_matrices(
        "compute_discrete_pid2 quantization",
        &[s1_mat, s2_mat, t_mat],
        num_bins,
    )?;
    let out = discrete_pid2(s1_mat, s2_mat, t_mat, num_bins)
        .map_err(pid_err)?
        .into_categorical_result();

    let mut map = BTreeMap::new();
    map.insert("redundancy".to_string(), out.redundancy);
    map.insert("unique_s1".to_string(), out.unique_s1);
    map.insert("unique_s2".to_string(), out.unique_s2);
    map.insert("synergy".to_string(), out.synergy);
    map.insert("mi_s1_t".to_string(), out.mi_s1_t);
    map.insert("mi_s2_t".to_string(), out.mi_s2_t);
    map.insert("mi_s1s2_t".to_string(), out.mi_s1s2_t);
    Ok(map)
}

/// Compute an exploratory same-sample, equal-width-quantized three-source Williams–Beer `I_min`
/// PID.
///
/// This uses a **different PID measure** from continuous `compute_pid3`; no counterpart or mapping
/// theorem is claimed, and its atoms must not be pooled with continuous-mode atoms. This deprecated
/// migration adapter derives ranges and bins from the evaluated rows with the internal exact
/// binary64-significand rule, consumes the Rust provenance wrapper, and returns only a flat numeric
/// dictionary. Keys are the antichain set indices of each atom on the 3-source lattice. The same
/// key syntax is also used by the categorical MGW adapter, so callers must retain method identity
/// externally; dictionary shape cannot identify the functional.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated adapter fits quantization on the evaluated sample, returns Williams-Beer I_min rather than shared exclusions, and discards num_bins-only wrapper/input/PMF provenance; it is not a KSG or Ehrlich fallback",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s0, s1, s2, target, num_bins=10))]
fn compute_discrete_pid3(
    s0: PyReadonlyArray2<f64>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let s0_mat = array_to_matref(&s0)?;
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    validate_aligned_rows(
        "compute_discrete_pid3",
        &[
            s0_mat.nrows(),
            s1_mat.nrows(),
            s2_mat.nrows(),
            t_mat.nrows(),
        ],
    )?;
    preflight_quantized_matrices(
        "compute_discrete_pid3 quantization",
        &[s0_mat, s1_mat, s2_mat, t_mat],
        num_bins,
    )?;
    let out = discrete_pid3(s0_mat, s1_mat, s2_mat, t_mat, num_bins)
        .map_err(pid_err)?
        .into_categorical_result();

    let mut map = BTreeMap::new();
    for atom in &out.atoms {
        map.insert(format!("{:?}", atom.antichain_sets), atom.value);
    }
    Ok(map)
}

fn sxpid2_output(out: DiscreteSxPid2Result) -> BTreeMap<String, f64> {
    let mut map = BTreeMap::new();
    for (name, a) in [
        ("redundancy", out.red),
        ("unique_s1", out.unq1),
        ("unique_s2", out.unq2),
        ("synergy", out.syn),
    ] {
        map.insert(name.to_string(), a.net_nats());
        map.insert(format!("{name}_informative"), a.informative_nats());
        map.insert(format!("{name}_misinformative"), a.misinformative_nats());
    }
    map.insert("mi_s1_t".to_string(), out.mi_s1_t);
    map.insert("mi_s2_t".to_string(), out.mi_s2_t);
    map.insert("mi_s1s2_t".to_string(), out.mi_s1s2_t);
    map
}

fn sxpid_lattice_output(antichains: &[Vec<u8>], atoms: &[SxAveragedAtom]) -> BTreeMap<String, f64> {
    let mut map = BTreeMap::new();
    for (sets, atom) in antichains.iter().zip(atoms) {
        map.insert(format!("{sets:?}"), atom.net_nats());
    }
    map
}

/// Compute exact categorical 2-source shared-exclusions PID (`i^sx_∩`).
///
/// Inputs must be C-contiguous NumPy `int64` matrices. Numeric spacing is ignored; only equality
/// of categorical rows matters. Returns averaged atoms in nats with informative/misinformative
/// splits. This deprecated flat numeric adapter omits typed atom interpretation; the stable typed
/// API retains it. `compute_quantized_sxpid2` is only an explicitly sample-dependent transform
/// sensitivity route for finite numeric data; it is not continuous PID.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter omits typed atom interpretation; use the stable typed API, which retains it",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s1, s2, target))]
fn compute_discrete_sxpid2(
    s1: PyReadonlyArray2<i64>,
    s2: PyReadonlyArray2<i64>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let lengths = [
        categorical_array_len(&s1)?,
        categorical_array_len(&s2)?,
        categorical_array_len(&target)?,
    ];
    validate_aligned_rows(
        "compute_discrete_sxpid2",
        &[s1.shape()[0], s2.shape()[0], target.shape()[0]],
    )?;
    preflight_categorical_lengths("compute_discrete_sxpid2 encoding", &lengths)?;
    let s1 = array_to_discrete(&s1)?;
    let s2 = array_to_discrete(&s2)?;
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid2(s1.as_ref()?, s2.as_ref()?, target.as_ref()?).map_err(pid_err)?;
    Ok(sxpid2_output(out))
}

/// Equal-width-quantized 2-source categorical shared-exclusions PID for finite numeric inputs.
///
/// Per-column ranges and bins are derived from the same rows with the internal exact
/// binary64-significand rule, so this computes categorical Makkeh–Gutknecht–Wibral shared
/// exclusions for sample-dependent transformed variables, not a continuous shared-exclusions PID
/// or the stable fitted-edge transform. This deprecated flat numeric adapter consumes and discards
/// the Rust wrapper's quantization-provenance component, whose sole field is `num_bins`, and omits
/// input/PMF metadata and typed atom interpretation; the stable fitted-transform API retains its
/// own fixed-edge provenance and typed interpretation.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter discards the num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance; categorical MGW output is not continuous Ehrlich PID",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s1, s2, target, num_bins=10))]
fn compute_quantized_sxpid2(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let s1 = array_to_matref(&s1)?;
    let s2 = array_to_matref(&s2)?;
    let target = array_to_matref(&target)?;
    validate_aligned_rows(
        "compute_quantized_sxpid2",
        &[s1.nrows(), s2.nrows(), target.nrows()],
    )?;
    preflight_quantized_matrices(
        "compute_quantized_sxpid2 quantization",
        &[s1, s2, target],
        num_bins,
    )?;
    let out = core_quantized_sxpid2(s1, s2, target, num_bins)
        .map_err(pid_err)?
        .into_categorical_result();
    Ok(sxpid2_output(out))
}

/// Compute exact categorical 3-source shared-exclusions PID over the 18-antichain lattice.
///
/// This deprecated flat numeric adapter omits typed atom interpretation; the stable typed API
/// retains it.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter omits typed atom interpretation; use the stable typed API, which retains it",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s0, s1, s2, target))]
fn compute_discrete_sxpid3(
    s0: PyReadonlyArray2<i64>,
    s1: PyReadonlyArray2<i64>,
    s2: PyReadonlyArray2<i64>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let lengths = [
        categorical_array_len(&s0)?,
        categorical_array_len(&s1)?,
        categorical_array_len(&s2)?,
        categorical_array_len(&target)?,
    ];
    validate_aligned_rows(
        "compute_discrete_sxpid3",
        &[
            s0.shape()[0],
            s1.shape()[0],
            s2.shape()[0],
            target.shape()[0],
        ],
    )?;
    preflight_categorical_lengths("compute_discrete_sxpid3 encoding", &lengths)?;
    let s0 = array_to_discrete(&s0)?;
    let s1 = array_to_discrete(&s1)?;
    let s2 = array_to_discrete(&s2)?;
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid3(s0.as_ref()?, s1.as_ref()?, s2.as_ref()?, target.as_ref()?)
        .map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Equal-width-quantized 3-source categorical shared-exclusions PID for finite numeric inputs.
///
/// Per-column ranges and bins are derived from the same rows with the internal exact
/// binary64-significand rule, so this computes categorical Makkeh–Gutknecht–Wibral shared
/// exclusions for sample-dependent transformed variables, not a continuous shared-exclusions PID
/// or the stable fitted-edge transform. This deprecated flat numeric adapter consumes and discards
/// the Rust wrapper's quantization-provenance component, whose sole field is `num_bins`, and omits
/// input/PMF metadata and typed atom interpretation; the stable fitted-transform API retains its
/// own fixed-edge provenance and typed interpretation. Its antichain-key dictionary has the same
/// shape as the deprecated three-source `I_min` dictionary, so callers must retain method identity.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter discards the num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance; categorical MGW output is not continuous Ehrlich PID",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (s0, s1, s2, target, num_bins=10))]
fn compute_quantized_sxpid3(
    s0: PyReadonlyArray2<f64>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let s0 = array_to_matref(&s0)?;
    let s1 = array_to_matref(&s1)?;
    let s2 = array_to_matref(&s2)?;
    let target = array_to_matref(&target)?;
    validate_aligned_rows(
        "compute_quantized_sxpid3",
        &[s0.nrows(), s1.nrows(), s2.nrows(), target.nrows()],
    )?;
    preflight_quantized_matrices(
        "compute_quantized_sxpid3 quantization",
        &[s0, s1, s2, target],
        num_bins,
    )?;
    let out = core_quantized_sxpid3(s0, s1, s2, target, num_bins)
        .map_err(pid_err)?
        .into_categorical_result();
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Compute exact categorical shared-exclusions PID for two to four `int64` sources.
///
/// This deprecated flat numeric adapter omits typed atom interpretation; the stable typed API
/// retains it.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter omits typed atom interpretation; use the stable typed API, which retains it",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (sources, target))]
fn compute_discrete_sxpid_n(
    sources: &Bound<'_, PyAny>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let sources = sources.cast::<PySequence>().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err(
            "sources must be a finite sequence of NumPy int64 matrices",
        )
    })?;
    let source_count = sources.len()?;
    if !(2..=MIGRATION_MAX_SOURCES).contains(&source_count) {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "compute_discrete_sxpid_n supports exactly two to {MIGRATION_MAX_SOURCES} sources; got {source_count}"
        )));
    }

    let mut source_arrays =
        try_vec_with_capacity("compute_discrete_sxpid_n source extraction", source_count)?;
    for index in 0..source_count {
        source_arrays.push(
            sources
                .get_item(index)?
                .extract::<PyReadonlyArray2<'_, i64>>()?,
        );
    }

    let mut lengths = try_vec_with_capacity(
        "compute_discrete_sxpid_n shape collection",
        source_count + 1,
    )?;
    let mut rows =
        try_vec_with_capacity("compute_discrete_sxpid_n row collection", source_count + 1)?;
    for source in &source_arrays {
        lengths.push(categorical_array_len(source)?);
        rows.push(source.shape()[0]);
    }
    lengths.push(categorical_array_len(&target)?);
    rows.push(target.shape()[0]);
    validate_aligned_rows("compute_discrete_sxpid_n", &rows)?;
    preflight_categorical_lengths("compute_discrete_sxpid_n encoding", &lengths)?;

    let mut owned_sources =
        try_vec_with_capacity("compute_discrete_sxpid_n encoded sources", source_count)?;
    for source in &source_arrays {
        owned_sources.push(array_to_discrete(source)?);
    }
    let mut source_refs =
        try_vec_with_capacity("compute_discrete_sxpid_n source references", source_count)?;
    for source in &owned_sources {
        source_refs.push(source.as_ref()?);
    }
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid_n(&source_refs, target.as_ref()?).map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Equal-width-quantized categorical shared-exclusions PID for two to four finite numeric sources.
///
/// Per-column ranges and bins are derived from the same rows with the internal exact
/// binary64-significand rule, so this computes categorical Makkeh–Gutknecht–Wibral shared
/// exclusions for sample-dependent transformed variables, not a continuous shared-exclusions PID
/// or the stable fitted-edge transform. This deprecated flat numeric adapter consumes and discards
/// the Rust wrapper's quantization-provenance component, whose sole field is `num_bins`, and omits
/// input/PMF metadata and typed atom interpretation; the stable fitted-transform API retains its
/// own fixed-edge provenance and typed interpretation. At three sources its antichain-key
/// dictionary has the same shape as the deprecated `I_min` dictionary, so callers must retain
/// method identity.
#[pyfunction]
#[pyo3(warn(
    message = "this deprecated flat SxPID adapter discards the num_bins-only quantization-provenance component plus input/PMF and typed-atom provenance; categorical MGW output is not continuous Ehrlich PID",
    category = pyo3::exceptions::PyDeprecationWarning
))]
#[pyo3(signature = (sources, target, num_bins=10))]
fn compute_quantized_sxpid_n(
    sources: &Bound<'_, PyAny>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let sources = sources.cast::<PySequence>().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err(
            "sources must be a finite sequence of NumPy float64 matrices",
        )
    })?;
    let source_count = sources.len()?;
    if !(2..=MIGRATION_MAX_SOURCES).contains(&source_count) {
        return Err(pyo3::exceptions::PyValueError::new_err(format!(
            "compute_quantized_sxpid_n supports exactly two to {MIGRATION_MAX_SOURCES} sources; got {source_count}"
        )));
    }

    let mut source_arrays =
        try_vec_with_capacity("compute_quantized_sxpid_n source extraction", source_count)?;
    for index in 0..source_count {
        source_arrays.push(
            sources
                .get_item(index)?
                .extract::<PyReadonlyArray2<'_, f64>>()?,
        );
    }
    let mut matrices = try_vec_with_capacity(
        "compute_quantized_sxpid_n matrix references",
        source_count + 1,
    )?;
    for source in &source_arrays {
        matrices.push(array_to_matref(source)?);
    }
    matrices.push(array_to_matref(&target)?);
    let mut rows =
        try_vec_with_capacity("compute_quantized_sxpid_n row collection", source_count + 1)?;
    rows.extend(matrices.iter().map(MatRef::nrows));
    validate_aligned_rows("compute_quantized_sxpid_n", &rows)?;
    preflight_quantized_matrices(
        "compute_quantized_sxpid_n quantization",
        &matrices,
        num_bins,
    )?;
    let target = matrices[source_count];
    let out = core_quantized_sxpid_n(&matrices[..source_count], target, num_bins)
        .map_err(pid_err)?
        .into_categorical_result();
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

fn matrix_output(
    py: Python<'_>,
    projected: pid_core::MatOwned,
    operation: &'static str,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let ref_view = projected.as_ref();
    let n = ref_view.nrows();
    let d = ref_view.ncols();
    let elements = preflight_matrix_output(operation, n, d)?;
    if ref_view.as_slice().len() != elements {
        return Err(pyo3::exceptions::PyRuntimeError::new_err(format!(
            "{operation}: projected matrix shape disagrees with its backing buffer"
        )));
    }
    let mut flat = try_vec_with_capacity(operation, elements)?;
    flat.extend_from_slice(ref_view.as_slice());

    let mut map = BTreeMap::new();
    map.insert(
        "data".to_string(),
        flat.into_pyobject(py)?.into_any().unbind(),
    );
    map.insert(
        "nrows".to_string(),
        n.into_pyobject(py)?.into_any().unbind(),
    );
    map.insert(
        "ncols".to_string(),
        d.into_pyobject(py)?.into_any().unbind(),
    );
    Ok(map)
}

/// A fitted PLS projector that can transform held-out source rows without refitting.
///
/// Fit this object on training `X` and `Y`, then reuse `transform` for validation, test, or
/// production `X` rows. This keeps target information from the held-out split out of the fitted
/// projection.
#[pyclass(name = "PlsProjector", frozen)]
struct PyPlsProjector {
    inner: CorePlsProjector,
}

#[pymethods]
impl PyPlsProjector {
    /// Fit PLS supervised dimensionality reduction on training rows.
    #[staticmethod]
    #[pyo3(signature = (x, y, out_dim))]
    fn fit(x: PyReadonlyArray2<f64>, y: PyReadonlyArray2<f64>, out_dim: usize) -> PyResult<Self> {
        let x_mat = array_to_matref(&x)?;
        let y_mat = array_to_matref(&y)?;
        let inner = CorePlsProjector::fit(x_mat, y_mat, out_dim).map_err(pid_err)?;
        Ok(Self { inner })
    }

    /// Project arbitrary source rows with the parameters learned by `fit`.
    fn transform(
        &self,
        py: Python<'_>,
        x: PyReadonlyArray2<f64>,
    ) -> PyResult<BTreeMap<String, Py<PyAny>>> {
        let x = array_to_matref(&x)?;
        preflight_matrix_output(
            "PlsProjector.transform compatibility output",
            x.nrows(),
            self.inner.out_dim(),
        )?;
        let projected = self.inner.transform(x).map_err(pid_err)?;
        matrix_output(py, projected, "PlsProjector.transform compatibility output")
    }

    /// Number of source columns required by `transform`.
    #[getter]
    fn in_dim(&self) -> usize {
        self.inner.in_dim()
    }

    /// Number of latent components returned by `transform`.
    #[getter]
    fn out_dim(&self) -> usize {
        self.inner.out_dim()
    }

    /// Number of target columns used while fitting.
    #[getter]
    fn target_dim(&self) -> usize {
        self.inner.target_dim()
    }
}

/// Training-only compatibility wrapper that fits PLS and projects the same X rows.
///
/// Projects high-dimensional X onto directions maximally correlated with target Y.
/// Unlike PCA, PLS uses label information to find the task-relevant subspace.
/// Do not use this convenience wrapper to evaluate held-out data: fitting on all rows leaks target
/// information into the projection. Use `PlsProjector.fit(x_train, y_train, out_dim)` followed by
/// `projector.transform(x_test)` for train/test workflows.
/// Returns the projected data as a 2D numpy-compatible flat list + (nrows, ncols).
#[pyfunction]
#[pyo3(signature = (x, y, out_dim))]
fn pls_transform(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    y: PyReadonlyArray2<f64>,
    out_dim: usize,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    let y_mat = array_to_matref(&y)?;
    validate_aligned_rows("pls_transform", &[x_mat.nrows(), y_mat.nrows()])?;
    preflight_matrix_output("pls_transform compatibility output", x_mat.nrows(), out_dim)?;
    let (projected, _pls) =
        CorePlsProjector::fit_transform(x_mat, y_mat, out_dim).map_err(pid_err)?;
    matrix_output(py, projected, "pls_transform compatibility output")
}

/// Standardize a matrix (zero mean, unit variance per column).
#[pyfunction]
#[pyo3(signature = (x))]
fn standardize(py: Python<'_>, x: PyReadonlyArray2<f64>) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    preflight_matrix_output(
        "standardize compatibility output",
        x_mat.nrows(),
        x_mat.ncols(),
    )?;
    let (projected, _std) =
        Standardizer::fit_transform(x_mat, ConstantColumnPolicy::Error).map_err(pid_err)?;
    matrix_output(py, projected, "standardize compatibility output")
}

/// PCA dimensionality reduction.
#[pyfunction]
#[pyo3(signature = (x, out_dim))]
fn pca_transform(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    out_dim: usize,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    preflight_matrix_output("pca_transform compatibility output", x_mat.nrows(), out_dim)?;
    let (projected, _pca) = PcaProjector::fit_transform(x_mat, out_dim).map_err(pid_err)?;
    matrix_output(py, projected, "pca_transform compatibility output")
}

/// Hash-based (CountSketch) dimensionality reduction.
#[pyfunction]
#[pyo3(signature = (x, out_dim, seed=42))]
fn hash_project(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    out_dim: usize,
    seed: u64,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    preflight_matrix_output("hash_project compatibility output", x_mat.nrows(), out_dim)?;
    let proj = HashProjector::new(x_mat.ncols(), out_dim, seed).map_err(pid_err)?;
    let projected = proj.transform(x_mat).map_err(pid_err)?;
    matrix_output(py, projected, "hash_project compatibility output")
}

/// Register the pre-1.0 compatibility surface inside `experimental.migration`.
///
/// This file is compiled only by the default-off `python-experimental` feature; the stable module
/// is implemented in `v1.rs` and never registers these scalar/research entry points.
pub(crate) fn register_legacy(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // The method-catalog checker parses this block through its exact `Ok(())` terminator and
    // recognizes these `m.add`, `m.add_class`, and `wrap_pyfunction` forms. Keep new registrations
    // in the same flat, parser-readable structure and update the catalog inventory with them.
    m.add("RESOURCE_MAX_BYTES", DEFAULT_MAX_BYTES)?;
    m.add("RESOURCE_MAX_OPERATIONS_HINT", DEFAULT_MAX_OPERATIONS_HINT)?;
    m.add(
        "RESOURCE_POLICY",
        "fixed compatibility ceiling for Rust-owned wrapper/core work; CPython object allocation remains a separate fallible boundary",
    )?;
    m.add_class::<PyPlsProjector>()?;
    m.add_function(wrap_pyfunction!(compute_mi, m)?)?;
    m.add_function(wrap_pyfunction!(compute_mi_report, m)?)?;
    m.add_function(wrap_pyfunction!(compute_redundancy, m)?)?;
    m.add_function(wrap_pyfunction!(compute_co_information, m)?)?;
    m.add_function(wrap_pyfunction!(compute_pid2, m)?)?;
    m.add_function(wrap_pyfunction!(compute_pid2_report, m)?)?;
    m.add_function(wrap_pyfunction!(compute_pid3_partial, m)?)?;
    m.add_function(wrap_pyfunction!(compute_pid3, m)?)?;
    m.add_function(wrap_pyfunction!(compute_discrete_pid2, m)?)?;
    m.add_function(wrap_pyfunction!(compute_discrete_pid3, m)?)?;
    m.add_function(wrap_pyfunction!(compute_discrete_sxpid2, m)?)?;
    m.add_function(wrap_pyfunction!(compute_discrete_sxpid3, m)?)?;
    m.add_function(wrap_pyfunction!(compute_discrete_sxpid_n, m)?)?;
    m.add_function(wrap_pyfunction!(compute_quantized_sxpid2, m)?)?;
    m.add_function(wrap_pyfunction!(compute_quantized_sxpid3, m)?)?;
    m.add_function(wrap_pyfunction!(compute_quantized_sxpid_n, m)?)?;
    m.add_function(wrap_pyfunction!(compute_invariants, m)?)?;
    m.add_function(wrap_pyfunction!(continuous_input_diagnostics, m)?)?;
    m.add_function(wrap_pyfunction!(estimate_intrinsic_dimension, m)?)?;
    m.add_function(wrap_pyfunction!(estimate_gromov_delta, m)?)?;
    m.add_function(wrap_pyfunction!(sampled_four_point_delta_summary, m)?)?;
    m.add_function(wrap_pyfunction!(distance_stats, m)?)?;
    m.add_function(wrap_pyfunction!(pls_transform, m)?)?;
    m.add_function(wrap_pyfunction!(standardize, m)?)?;
    m.add_function(wrap_pyfunction!(pca_transform, m)?)?;
    m.add_function(wrap_pyfunction!(hash_project, m)?)?;
    Ok(())
}
