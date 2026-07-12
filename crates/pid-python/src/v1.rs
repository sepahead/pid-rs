//! Stable Python surface for pid-rs 1.0.
//!
//! The default wheel deliberately exposes only empirical categorical estimators, explicitly
//! fitted quantization, conditional report-first Euclidean KSG, and diagnostics. Research and
//! pre-1.0 compatibility functions are registered only under the default-off
//! `python-experimental` feature.

use std::mem::size_of;
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use numpy::ndarray::Array2;
use numpy::{Element, IntoPyArray, PyArray2, PyReadonlyArray2};
use pid_core::diagnostics::{
    continuous_input_diagnostics_with_budget_and_cancellation as core_continuous_input_diagnostics_with_budget_and_cancellation,
    distance_concentration_stats_with_budget_and_cancellation,
    intrinsic_dimension_report_with_cancellation as core_intrinsic_dimension_report_with_cancellation,
    ContinuousInputDiagnostics, DistanceConcentrationConfig, DistanceConcentrationStats,
    DistanceQuantiles, IntrinsicDimConfig, NeighborShellDiagnostics,
};
use pid_core::stable::categorical::{
    discrete_sxpid2_averaged_with_budget_and_cancellation,
    discrete_sxpid3_averaged_with_budget_and_cancellation,
    discrete_sxpid_n_averaged_with_budget_and_cancellation, DiscreteInputEncoding,
    DiscreteSxPid2Result, DiscreteSxPid3Result, DiscreteSxPidNResult, EmpiricalPmfDiagnostics,
    SxAtom as CoreSxAtom,
};
use pid_core::stable::continuous::{
    ksg_mi_report_with_budget_and_cancellation, KsgConfig, KsgCountQuantiles,
    KsgLocalDiagnosticsSummary, KsgNeighborBackend, KsgProvenance, KsgValueQuantiles,
};
use pid_core::stable::imin::{
    imin_pid2_with_budget_and_cancellation, IminPid2Result as CoreIminPid2Result,
};
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2_with_budget_and_cancellation,
    EqualWidthQuantizer as CoreEqualWidthQuantizer, OutOfRangePolicy as CoreOutOfRangePolicy,
    QuantizationReport as CoreQuantizationReport, QuantizerConfig as CoreQuantizerConfig,
};
use pid_core::{
    CancellationToken as CoreCancellationToken, DiscreteMatRef, MatRef, Metric,
    PidError as CorePidError, ResourceBudget as CoreResourceBudget,
};
use pyo3::create_exception;
use pyo3::exceptions::PyException;
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyModule, PySequence, PyTuple};

#[cfg(feature = "python-experimental")]
#[path = "lib.rs"]
mod legacy;

create_exception!(
    pid_core_rs,
    PidRsError,
    PyException,
    "Base exception for structured pid-rs failures."
);
create_exception!(
    pid_core_rs,
    PidInputError,
    PidRsError,
    "Invalid shape, value, scientific contract, or configuration."
);
create_exception!(
    pid_core_rs,
    PidResourceError,
    PidRsError,
    "A declared memory, pairwise-distance, or operation budget was exceeded."
);
create_exception!(
    pid_core_rs,
    PidNumericalError,
    PidRsError,
    "The estimator rejected numerically ambiguous or unstable geometry."
);
create_exception!(
    pid_core_rs,
    PidUnsupportedError,
    PidRsError,
    "The requested scientific model is outside the stable surface."
);
create_exception!(
    pid_core_rs,
    PidCancelledError,
    PidRsError,
    "The computation was cooperatively cancelled before completion."
);

const DEFAULT_MAX_BYTES: u64 = 1 << 30;
const DEFAULT_MAX_PAIRWISE_DISTANCES: u64 = 50_000_000;
const DEFAULT_MAX_OPERATIONS_HINT: u128 = 10_000_000_000;
const DEFAULT_MAX_THREADS: usize = 1;

#[pyclass(
    name = "ResourceBudget",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyResourceBudget {
    #[pyo3(get)]
    max_bytes: u64,
    #[pyo3(get)]
    max_pairwise_distances: u64,
    #[pyo3(get)]
    max_operations_hint: u128,
    #[pyo3(get)]
    max_threads: usize,
}

impl Default for PyResourceBudget {
    fn default() -> Self {
        Self {
            max_bytes: DEFAULT_MAX_BYTES,
            max_pairwise_distances: DEFAULT_MAX_PAIRWISE_DISTANCES,
            max_operations_hint: DEFAULT_MAX_OPERATIONS_HINT,
            max_threads: DEFAULT_MAX_THREADS,
        }
    }
}

#[pymethods]
impl PyResourceBudget {
    #[new]
    #[pyo3(signature = (
        max_bytes=DEFAULT_MAX_BYTES,
        max_pairwise_distances=DEFAULT_MAX_PAIRWISE_DISTANCES,
        max_operations_hint=DEFAULT_MAX_OPERATIONS_HINT,
        max_threads=DEFAULT_MAX_THREADS
    ))]
    fn new(
        py: Python<'_>,
        max_bytes: u64,
        max_pairwise_distances: u64,
        max_operations_hint: u128,
        max_threads: usize,
    ) -> PyResult<Self> {
        if max_bytes == 0
            || max_pairwise_distances == 0
            || max_operations_hint == 0
            || max_threads == 0
        {
            return Err(input_error(
                py,
                "invalid_resource_budget",
                "resource-budget limits must all be positive",
                [],
            ));
        }
        Ok(Self {
            max_bytes,
            max_pairwise_distances,
            max_operations_hint,
            max_threads,
        })
    }

    fn __repr__(&self) -> String {
        format!(
            "ResourceBudget(max_bytes={}, max_pairwise_distances={}, max_operations_hint={}, max_threads={})",
            self.max_bytes,
            self.max_pairwise_distances,
            self.max_operations_hint,
            self.max_threads
        )
    }
}

impl From<CoreResourceBudget> for PyResourceBudget {
    fn from(value: CoreResourceBudget) -> Self {
        Self {
            max_bytes: value.max_bytes,
            max_pairwise_distances: value.max_pairwise_distances,
            max_operations_hint: value.max_operations_hint,
            max_threads: value.max_threads,
        }
    }
}

impl PyResourceBudget {
    fn as_core(&self) -> CoreResourceBudget {
        let mut budget = CoreResourceBudget::default();
        budget.max_bytes = self.max_bytes;
        budget.max_pairwise_distances = self.max_pairwise_distances;
        budget.max_operations_hint = self.max_operations_hint;
        budget.max_threads = self.max_threads;
        budget
    }
}

#[pyclass(
    name = "ResourceEstimate",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyResourceEstimate {
    #[pyo3(get)]
    estimated_bytes: u128,
    #[pyo3(get)]
    pairwise_distances: u128,
    #[pyo3(get)]
    operations_hint: u128,
}

impl From<pid_core::ResourceEstimate> for PyResourceEstimate {
    fn from(value: pid_core::ResourceEstimate) -> Self {
        Self {
            estimated_bytes: value.estimated_bytes,
            pairwise_distances: value.pairwise_distances,
            operations_hint: value.operations_hint,
        }
    }
}

fn annotate_error(
    py: Python<'_>,
    error: PyErr,
    code: &str,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    let value = error.value(py);
    let _ = value.setattr("code", code);
    let mapping = PyDict::new(py);
    for (key, value) in fields {
        let _ = mapping.set_item(key, value);
    }
    let _ = value.setattr("fields", mapping);
    error
}

fn input_error(
    py: Python<'_>,
    code: &str,
    message: impl Into<String>,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    annotate_error(
        py,
        PyErr::new::<PidInputError, _>(message.into()),
        code,
        fields,
    )
}

fn resource_error(
    py: Python<'_>,
    code: &str,
    message: impl Into<String>,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    annotate_error(
        py,
        PyErr::new::<PidResourceError, _>(message.into()),
        code,
        fields,
    )
}

fn numerical_error(
    py: Python<'_>,
    code: &str,
    message: impl Into<String>,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    annotate_error(
        py,
        PyErr::new::<PidNumericalError, _>(message.into()),
        code,
        fields,
    )
}

fn unsupported_error(
    py: Python<'_>,
    code: &str,
    message: impl Into<String>,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    annotate_error(
        py,
        PyErr::new::<PidUnsupportedError, _>(message.into()),
        code,
        fields,
    )
}

fn cancelled_error(
    py: Python<'_>,
    code: &str,
    message: impl Into<String>,
    fields: impl IntoIterator<Item = (String, String)>,
) -> PyErr {
    annotate_error(
        py,
        PyErr::new::<PidCancelledError, _>(message.into()),
        code,
        fields,
    )
}

fn core_error(py: Python<'_>, error: CorePidError) -> PyErr {
    let message = error.to_string();
    let debug = format!("{error:?}");
    match error {
        CorePidError::ShapeMismatch {
            context,
            expected_len,
            actual_len,
        } => input_error(
            py,
            "shape_mismatch",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("expected_len".to_owned(), expected_len.to_string()),
                ("actual_len".to_owned(), actual_len.to_string()),
            ],
        ),
        CorePidError::InvalidConfig {
            context,
            message: detail,
        } => input_error(
            py,
            "invalid_config",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("detail".to_owned(), detail.to_owned()),
            ],
        ),
        CorePidError::RowCountMismatch {
            context,
            left_rows,
            right_rows,
        } => input_error(
            py,
            "row_count_mismatch",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("left_rows".to_owned(), left_rows.to_string()),
                ("right_rows".to_owned(), right_rows.to_string()),
            ],
        ),
        CorePidError::SourceDimensionMismatch {
            context,
            left_cols,
            right_cols,
        } => input_error(
            py,
            "source_dimension_mismatch",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("left_cols".to_owned(), left_cols.to_string()),
                ("right_cols".to_owned(), right_cols.to_string()),
            ],
        ),
        CorePidError::InvalidK { k, n_samples } => input_error(
            py,
            "invalid_k",
            message,
            [
                ("k".to_owned(), k.to_string()),
                ("n_samples".to_owned(), n_samples.to_string()),
            ],
        ),
        CorePidError::NonFiniteInput { context } => input_error(
            py,
            "non_finite_input",
            message,
            [("context".to_owned(), context.to_owned())],
        ),
        CorePidError::SupportContractRequired { context } => input_error(
            py,
            "support_contract_required",
            message,
            [("context".to_owned(), context.to_owned())],
        ),
        CorePidError::UnsupportedSupportContract { context, contract } => unsupported_error(
            py,
            "unsupported_support_contract",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("contract".to_owned(), contract.to_string()),
            ],
        ),
        CorePidError::ObservedContinuousSampleIncompatibility {
            context,
            input_index,
            coordinate,
            unique_values,
            n_samples,
            max_multiplicity,
        } => input_error(
            py,
            "observed_continuous_sample_incompatibility",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("input_index".to_owned(), input_index.to_string()),
                (
                    "coordinate".to_owned(),
                    coordinate.map_or_else(|| "none".to_owned(), |value| value.to_string()),
                ),
                ("unique_values".to_owned(), unique_values.to_string()),
                ("n_samples".to_owned(), n_samples.to_string()),
                ("max_multiplicity".to_owned(), max_multiplicity.to_string()),
            ],
        ),
        CorePidError::NumericalInstability { context } => numerical_error(
            py,
            "numerical_instability",
            message,
            [("context".to_owned(), context.to_owned())],
        ),
        CorePidError::ResourceLimitExceeded {
            operation,
            resource,
            requested,
            limit,
        } => resource_error(
            py,
            "resource_limit_exceeded",
            message,
            [
                ("operation".to_owned(), operation.to_owned()),
                ("resource".to_owned(), resource.to_owned()),
                ("requested".to_owned(), requested.to_string()),
                ("limit".to_owned(), limit.to_string()),
            ],
        ),
        CorePidError::AllocationFailed {
            operation,
            requested_bytes,
        } => resource_error(
            py,
            "allocation_failed",
            message,
            [
                ("operation".to_owned(), operation.to_owned()),
                ("requested_bytes".to_owned(), requested_bytes.to_string()),
            ],
        ),
        CorePidError::SizeOverflow { operation } => resource_error(
            py,
            "size_overflow",
            message,
            [("operation".to_owned(), operation.to_owned())],
        ),
        CorePidError::QuantizerOutOfRange {
            column,
            value,
            training_min,
            training_max,
        } => input_error(
            py,
            "quantizer_out_of_range",
            message,
            [
                ("column".to_owned(), column.to_string()),
                ("value".to_owned(), value.to_string()),
                ("training_min".to_owned(), training_min.to_string()),
                ("training_max".to_owned(), training_max.to_string()),
            ],
        ),
        CorePidError::SampleCountPrecisionExceeded {
            operation,
            sample_count,
            maximum_exact_sample_count,
        } => resource_error(
            py,
            "sample_count_precision_exceeded",
            message,
            [
                ("operation".to_owned(), operation.to_owned()),
                ("sample_count".to_owned(), sample_count.to_string()),
                (
                    "maximum_exact_sample_count".to_owned(),
                    maximum_exact_sample_count.to_string(),
                ),
            ],
        ),
        CorePidError::ParallelExecutionFailed { operation } => numerical_error(
            py,
            "parallel_execution_failed",
            message,
            [("operation".to_owned(), operation.to_owned())],
        ),
        CorePidError::Cancelled {
            operation,
            completed_units,
            total_units,
        } => cancelled_error(
            py,
            "cancelled",
            message,
            [
                ("operation".to_owned(), operation.to_owned()),
                ("completed_units".to_owned(), completed_units.to_string()),
                ("total_units".to_owned(), total_units.to_string()),
            ],
        ),
        CorePidError::AmbiguousKthNeighborShell {
            context,
            query_index,
            k,
            radius,
            interior_count,
            boundary_count,
        } => numerical_error(
            py,
            "ambiguous_kth_neighbor_shell",
            message,
            [
                ("context".to_owned(), context.to_owned()),
                ("query_index".to_owned(), query_index.to_string()),
                ("k".to_owned(), k.to_string()),
                ("radius".to_owned(), radius.to_string()),
                ("interior_count".to_owned(), interior_count.to_string()),
                ("boundary_count".to_owned(), boundary_count.to_string()),
            ],
        ),
        CorePidError::NotImplemented { feature } => unsupported_error(
            py,
            "not_implemented",
            message,
            [("feature".to_owned(), feature.to_owned())],
        ),
        #[allow(unreachable_patterns)]
        _ => unsupported_error(
            py,
            "pid_core_error",
            message,
            [("rust_error".to_owned(), debug)],
        ),
    }
}

fn run_owned_worker_with_signal_cancellation<T, F>(
    py: Python<'_>,
    operation: &'static str,
    work: F,
) -> PyResult<T>
where
    T: Send + 'static,
    F: FnOnce(&CoreCancellationToken) -> Result<T, CorePidError> + Send + 'static,
{
    const SIGNAL_POLL_INTERVAL: Duration = Duration::from_millis(10);

    py.check_signals()?;
    let cancellation = Arc::new(CoreCancellationToken::new());
    let worker_cancellation = Arc::clone(&cancellation);
    let worker = thread::Builder::new()
        .spawn(move || work(worker_cancellation.as_ref()))
        .map_err(|error| {
            resource_error(
                py,
                "worker_spawn_failed",
                format!("{operation}: could not start an owned Rust worker: {error}"),
                [("operation".to_owned(), operation.to_owned())],
            )
        })?;

    let mut signal_error = None;
    while !worker.is_finished() {
        py.detach(|| thread::park_timeout(SIGNAL_POLL_INTERVAL));
        if signal_error.is_none() {
            if let Err(error) = py.check_signals() {
                cancellation.cancel();
                signal_error = Some(error);
            }
        }
    }

    // Joining is mandatory even after SIGINT: returning while a worker continues would only hide
    // the computation and retain its owned buffers. The join itself runs without the GIL.
    let worker_result = py.detach(|| worker.join()).map_err(|_| {
        numerical_error(
            py,
            "worker_panicked",
            format!("{operation}: owned Rust worker panicked"),
            [("operation".to_owned(), operation.to_owned())],
        )
    })?;
    if let Some(error) = signal_error {
        return Err(error);
    }
    py.check_signals()?;
    worker_result.map_err(|error| core_error(py, error))
}

fn effective_budget(budget: Option<&PyResourceBudget>) -> PyResourceBudget {
    budget.cloned().unwrap_or_default()
}

impl PyResourceBudget {
    fn check_limit(
        &self,
        py: Python<'_>,
        operation: &str,
        resource: &'static str,
        requested: u128,
        limit: u128,
    ) -> PyResult<()> {
        if requested > limit {
            return Err(resource_error(
                py,
                "resource_limit_exceeded",
                format!(
                    "{operation}: resource limit exceeded for {resource} (requested {requested}, limit {limit})"
                ),
                [
                    ("operation".to_owned(), operation.to_owned()),
                    ("resource".to_owned(), resource.to_owned()),
                    ("requested".to_owned(), requested.to_string()),
                    ("limit".to_owned(), limit.to_string()),
                ],
            ));
        }
        Ok(())
    }

    fn check_bytes(
        &self,
        py: Python<'_>,
        operation: &str,
        elements: usize,
        element_bytes: usize,
    ) -> PyResult<()> {
        let requested = (elements as u128)
            .checked_mul(element_bytes as u128)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    format!("{operation}: byte estimate overflow"),
                    [("operation".to_owned(), operation.to_owned())],
                )
            })?;
        self.check_limit(
            py,
            operation,
            "bytes",
            requested,
            u128::from(self.max_bytes),
        )
    }

    fn check_wrapper_peak_bytes(
        &self,
        py: Python<'_>,
        operation: &str,
        requested: u128,
    ) -> PyResult<()> {
        self.check_limit(
            py,
            operation,
            "bytes",
            requested,
            u128::from(self.max_bytes),
        )
    }

    fn check_estimate_with_retained(
        &self,
        py: Python<'_>,
        operation: &str,
        retained_bytes: u128,
        wrapper_operations: u128,
        estimate: pid_core::ResourceEstimate,
    ) -> PyResult<()> {
        let requested_bytes = retained_bytes
            .checked_add(estimate.estimated_bytes)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    format!("{operation}: aggregate byte estimate overflow"),
                    [("operation".to_owned(), operation.to_owned())],
                )
            })?;
        let requested_operations = wrapper_operations
            .checked_add(estimate.operations_hint)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    format!("{operation}: aggregate operation estimate overflow"),
                    [("operation".to_owned(), operation.to_owned())],
                )
            })?;
        self.check_limit(
            py,
            operation,
            "bytes",
            requested_bytes,
            u128::from(self.max_bytes),
        )?;
        self.check_limit(
            py,
            operation,
            "pairwise_distances",
            estimate.pairwise_distances,
            u128::from(self.max_pairwise_distances),
        )?;
        self.check_limit(
            py,
            operation,
            "operations_hint",
            requested_operations,
            self.max_operations_hint,
        )
    }

    fn core_after_wrapper_cost(
        &self,
        py: Python<'_>,
        operation: &str,
        retained_bytes: u128,
        wrapper_operations: u128,
    ) -> PyResult<CoreResourceBudget> {
        self.check_wrapper_peak_bytes(py, operation, retained_bytes)?;
        self.check_limit(
            py,
            operation,
            "operations_hint",
            wrapper_operations,
            self.max_operations_hint,
        )?;

        let remaining_bytes = u128::from(self.max_bytes) - retained_bytes;
        if remaining_bytes == 0 {
            return Err(resource_error(
                py,
                "resource_limit_exceeded",
                format!("{operation}: no byte budget remains for the core computation"),
                [
                    ("operation".to_owned(), operation.to_owned()),
                    ("resource".to_owned(), "bytes".to_owned()),
                    (
                        "requested".to_owned(),
                        retained_bytes.saturating_add(1).to_string(),
                    ),
                    ("limit".to_owned(), self.max_bytes.to_string()),
                ],
            ));
        }
        let remaining_operations = self.max_operations_hint - wrapper_operations;
        if remaining_operations == 0 {
            return Err(resource_error(
                py,
                "resource_limit_exceeded",
                format!("{operation}: no operation budget remains for the core computation"),
                [
                    ("operation".to_owned(), operation.to_owned()),
                    ("resource".to_owned(), "operations_hint".to_owned()),
                    (
                        "requested".to_owned(),
                        wrapper_operations.saturating_add(1).to_string(),
                    ),
                    ("limit".to_owned(), self.max_operations_hint.to_string()),
                ],
            ));
        }

        CoreResourceBudget::new(
            remaining_bytes as u64,
            self.max_pairwise_distances,
            remaining_operations,
            self.max_threads,
        )
        .map_err(|error| core_error(py, error))
    }
}

struct OwnedF64Matrix {
    data: Vec<f64>,
    nrows: usize,
    ncols: usize,
}

impl OwnedF64Matrix {
    fn as_ref(&self) -> Result<MatRef<'_>, CorePidError> {
        MatRef::new(&self.data, self.nrows, self.ncols)
    }
}

struct OwnedI64Matrix {
    data: Vec<i64>,
    nrows: usize,
    ncols: usize,
}

struct EncodedDiscreteMatrix {
    data: Vec<usize>,
    nrows: usize,
    ncols: usize,
}

impl EncodedDiscreteMatrix {
    fn as_ref(&self) -> Result<DiscreteMatRef<'_>, CorePidError> {
        DiscreteMatRef::new(&self.data, self.nrows, self.ncols)
    }
}

fn checked_shape(py: Python<'_>, operation: &str, nrows: usize, ncols: usize) -> PyResult<usize> {
    if nrows == 0 || ncols == 0 {
        return Err(input_error(
            py,
            "empty_matrix",
            format!("{operation}: arrays must have at least one row and one column"),
            [
                ("nrows".to_owned(), nrows.to_string()),
                ("ncols".to_owned(), ncols.to_string()),
            ],
        ));
    }
    nrows.checked_mul(ncols).ok_or_else(|| {
        input_error(
            py,
            "shape_overflow",
            format!("{operation}: matrix shape product overflows usize"),
            [
                ("nrows".to_owned(), nrows.to_string()),
                ("ncols".to_owned(), ncols.to_string()),
            ],
        )
    })
}

fn array_element_count<T: Element>(
    py: Python<'_>,
    array: &PyReadonlyArray2<'_, T>,
    operation: &str,
) -> PyResult<usize> {
    let view = array.as_array();
    let [nrows, ncols]: [usize; 2] = view
        .shape()
        .try_into()
        .map_err(|_| input_error(py, "invalid_rank", "expected a two-dimensional array", []))?;
    checked_shape(py, operation, nrows, ncols)
}

fn aggregate_elements(py: Python<'_>, operation: &str, lengths: &[usize]) -> PyResult<usize> {
    lengths.iter().try_fold(0usize, |total, &length| {
        total.checked_add(length).ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                format!("{operation}: aggregate input length overflow"),
                [("operation".to_owned(), operation.to_owned())],
            )
        })
    })
}

fn allocation_bytes(
    py: Python<'_>,
    operation: &str,
    elements: usize,
    element_bytes: usize,
) -> PyResult<u128> {
    (elements as u128)
        .checked_mul(element_bytes as u128)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                format!("{operation}: aggregate byte estimate overflow"),
                [("operation".to_owned(), operation.to_owned())],
            )
        })
}

fn try_string_copy(py: Python<'_>, operation: &str, value: &str) -> PyResult<String> {
    let mut output = String::new();
    output.try_reserve_exact(value.len()).map_err(|_| {
        resource_error(
            py,
            "allocation_failed",
            format!("{operation}: string allocation failed"),
            [
                ("operation".to_owned(), operation.to_owned()),
                ("requested_bytes".to_owned(), value.len().to_string()),
            ],
        )
    })?;
    output.push_str(value);
    Ok(output)
}

fn preflight_aggregate_copies(
    py: Python<'_>,
    operation: &str,
    budget: &PyResourceBudget,
    lengths: &[usize],
    element_bytes: usize,
) -> PyResult<(usize, u128)> {
    let elements = aggregate_elements(py, operation, lengths)?;
    let bytes = allocation_bytes(py, operation, elements, element_bytes)?;
    budget.check_wrapper_peak_bytes(py, operation, bytes)?;
    Ok((elements, bytes))
}

fn copy_f64_matrix(
    py: Python<'_>,
    array: &PyReadonlyArray2<'_, f64>,
    operation: &str,
    budget: &PyResourceBudget,
) -> PyResult<OwnedF64Matrix> {
    let view = array.as_array();
    let [nrows, ncols]: [usize; 2] = view
        .shape()
        .try_into()
        .map_err(|_| input_error(py, "invalid_rank", "expected a two-dimensional array", []))?;
    let len = checked_shape(py, operation, nrows, ncols)?;
    budget.check_bytes(py, operation, len, size_of::<f64>())?;
    let mut data = Vec::new();
    data.try_reserve_exact(len).map_err(|_| {
        resource_error(
            py,
            "allocation_failed",
            format!("{operation}: could not reserve Rust-owned input buffer"),
            [("requested_elements".to_owned(), len.to_string())],
        )
    })?;
    let mut copied = 0usize;
    for row in 0..nrows {
        for column in 0..ncols {
            if copied.is_multiple_of(4096) {
                py.check_signals()?;
            }
            let value = view[(row, column)];
            if !value.is_finite() {
                return Err(input_error(
                    py,
                    "non_finite_input",
                    format!("{operation}: input contains NaN or infinity"),
                    [
                        ("row".to_owned(), row.to_string()),
                        ("column".to_owned(), column.to_string()),
                    ],
                ));
            }
            data.push(value);
            copied += 1;
        }
    }
    Ok(OwnedF64Matrix { data, nrows, ncols })
}

fn copy_i64_matrix(
    py: Python<'_>,
    array: &PyReadonlyArray2<'_, i64>,
    operation: &str,
    budget: &PyResourceBudget,
) -> PyResult<OwnedI64Matrix> {
    let view = array.as_array();
    let [nrows, ncols]: [usize; 2] = view
        .shape()
        .try_into()
        .map_err(|_| input_error(py, "invalid_rank", "expected a two-dimensional array", []))?;
    let len = checked_shape(py, operation, nrows, ncols)?;
    budget.check_bytes(py, operation, len, size_of::<i64>())?;
    let mut data = Vec::new();
    data.try_reserve_exact(len).map_err(|_| {
        resource_error(
            py,
            "allocation_failed",
            format!("{operation}: could not reserve Rust-owned categorical input buffer"),
            [("requested_elements".to_owned(), len.to_string())],
        )
    })?;
    let mut copied = 0usize;
    for row in 0..nrows {
        for column in 0..ncols {
            if copied.is_multiple_of(4096) {
                py.check_signals()?;
            }
            data.push(view[(row, column)]);
            copied += 1;
        }
    }
    Ok(OwnedI64Matrix { data, nrows, ncols })
}

fn encode_discrete(
    input: &OwnedI64Matrix,
    operation: &'static str,
    cancellation: &CoreCancellationToken,
) -> Result<EncodedDiscreteMatrix, CorePidError> {
    let requested_unique_bytes = (input.data.len() as u128) * size_of::<i64>() as u128;
    let mut unique_labels = Vec::new();
    unique_labels
        .try_reserve_exact(input.data.len())
        .map_err(|_| CorePidError::AllocationFailed {
            operation,
            requested_bytes: requested_unique_bytes,
        })?;
    check_wrapper_cancellation(cancellation, operation, 0, input.data.len())?;
    for (index, &label) in input.data.iter().enumerate() {
        if index.is_multiple_of(1024) {
            check_wrapper_cancellation(cancellation, operation, index, input.data.len())?;
        }
        unique_labels.push(label);
    }
    cancellable_i64_heapsort(&mut unique_labels, operation, cancellation)?;
    if !unique_labels.is_empty() {
        let mut write = 1usize;
        for read in 1..unique_labels.len() {
            if read.is_multiple_of(1024) {
                check_wrapper_cancellation(cancellation, operation, read, unique_labels.len())?;
            }
            if unique_labels[read] != unique_labels[write - 1] {
                unique_labels[write] = unique_labels[read];
                write += 1;
            }
        }
        unique_labels.truncate(write);
    }

    let requested_output_bytes = (input.data.len() as u128) * size_of::<usize>() as u128;
    let mut data = Vec::new();
    data.try_reserve_exact(input.data.len())
        .map_err(|_| CorePidError::AllocationFailed {
            operation,
            requested_bytes: requested_output_bytes,
        })?;
    for (index, &label) in input.data.iter().enumerate() {
        if index.is_multiple_of(1024) {
            check_wrapper_cancellation(cancellation, operation, index, input.data.len())?;
        }
        let code = unique_labels
            .binary_search(&label)
            .map_err(|_| CorePidError::NumericalInstability { context: operation })?;
        data.push(code);
    }
    Ok(EncodedDiscreteMatrix {
        data,
        nrows: input.nrows,
        ncols: input.ncols,
    })
}

fn check_wrapper_cancellation(
    cancellation: &CoreCancellationToken,
    operation: &'static str,
    completed_units: usize,
    total_units: usize,
) -> Result<(), CorePidError> {
    if cancellation.is_cancelled() {
        Err(CorePidError::Cancelled {
            operation,
            completed_units,
            total_units,
        })
    } else {
        Ok(())
    }
}

fn cancellable_i64_heapsort(
    values: &mut [i64],
    operation: &'static str,
    cancellation: &CoreCancellationToken,
) -> Result<(), CorePidError> {
    let len = values.len();
    check_wrapper_cancellation(cancellation, operation, 0, len)?;
    for (completed, root) in (0..(len / 2)).rev().enumerate() {
        if completed.is_multiple_of(1024) {
            check_wrapper_cancellation(cancellation, operation, completed, len)?;
        }
        cancellable_i64_sift_down(values, root, len, operation, cancellation)?;
    }
    for end in (1..len).rev() {
        if end.is_multiple_of(1024) {
            check_wrapper_cancellation(cancellation, operation, len - end, len)?;
        }
        values.swap(0, end);
        cancellable_i64_sift_down(values, 0, end, operation, cancellation)?;
    }
    check_wrapper_cancellation(cancellation, operation, len, len)
}

fn cancellable_i64_sift_down(
    values: &mut [i64],
    mut root: usize,
    end: usize,
    operation: &'static str,
    cancellation: &CoreCancellationToken,
) -> Result<(), CorePidError> {
    loop {
        let Some(left) = root.checked_mul(2).and_then(|value| value.checked_add(1)) else {
            return Err(CorePidError::SizeOverflow { operation });
        };
        if left >= end {
            return Ok(());
        }
        let right = left + 1;
        let larger = if right < end && values[right] > values[left] {
            right
        } else {
            left
        };
        if values[root] >= values[larger] {
            return Ok(());
        }
        values.swap(root, larger);
        root = larger;
        if root.is_multiple_of(1024) {
            check_wrapper_cancellation(cancellation, operation, root, end)?;
        }
    }
}

fn ceil_log2(value: usize) -> u128 {
    if value <= 1 {
        1
    } else {
        (usize::BITS - (value - 1).leading_zeros()) as u128
    }
}

fn categorical_wrapper_cost(
    py: Python<'_>,
    operation: &str,
    lengths: &[usize],
) -> PyResult<(u128, u128)> {
    let total_elements = aggregate_elements(py, operation, lengths)?;
    let input_bytes = allocation_bytes(py, operation, total_elements, size_of::<i64>())?;
    let encoding_bytes_per_element = size_of::<i64>()
        .checked_add(size_of::<usize>())
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                format!("{operation}: encoding element-size overflow"),
                [("operation".to_owned(), operation.to_owned())],
            )
        })?;
    let encoding_workspace =
        allocation_bytes(py, operation, total_elements, encoding_bytes_per_element)?;
    let peak_bytes = input_bytes.checked_add(encoding_workspace).ok_or_else(|| {
        resource_error(
            py,
            "resource_estimate_overflow",
            format!("{operation}: encoding peak-byte estimate overflow"),
            [("operation".to_owned(), operation.to_owned())],
        )
    })?;

    let operations = lengths
        .iter()
        .try_fold(total_elements as u128, |total, &length| {
            let per_element = ceil_log2(length)
                .checked_mul(5)
                .and_then(|value| value.checked_add(4))
                .ok_or_else(|| {
                    resource_error(
                        py,
                        "resource_estimate_overflow",
                        format!("{operation}: encoding operation estimate overflow"),
                        [("operation".to_owned(), operation.to_owned())],
                    )
                })?;
            (length as u128)
                .checked_mul(per_element)
                .and_then(|value| total.checked_add(value))
                .ok_or_else(|| {
                    resource_error(
                        py,
                        "resource_estimate_overflow",
                        format!("{operation}: encoding operation estimate overflow"),
                        [("operation".to_owned(), operation.to_owned())],
                    )
                })
        })?;
    Ok((peak_bytes, operations))
}

fn validate_aligned_rows(py: Python<'_>, operation: &str, rows: &[usize]) -> PyResult<()> {
    let Some(&expected) = rows.first() else {
        return Ok(());
    };
    if let Some((index, actual)) = rows
        .iter()
        .copied()
        .enumerate()
        .find(|(_, value)| *value != expected)
    {
        return Err(input_error(
            py,
            "row_count_mismatch",
            format!("{operation}: all arrays must have the same row count"),
            [
                ("input_index".to_owned(), index.to_string()),
                ("expected_rows".to_owned(), expected.to_string()),
                ("actual_rows".to_owned(), actual.to_string()),
            ],
        ));
    }
    Ok(())
}

#[pyclass(
    name = "DistanceQuantiles",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyDistanceQuantiles {
    #[pyo3(get)]
    min: f64,
    #[pyo3(get)]
    p10: f64,
    #[pyo3(get)]
    median: f64,
    #[pyo3(get)]
    p90: f64,
    #[pyo3(get)]
    p99: f64,
    #[pyo3(get)]
    max: f64,
}

impl From<DistanceQuantiles> for PyDistanceQuantiles {
    fn from(value: DistanceQuantiles) -> Self {
        Self {
            min: value.min,
            p10: value.p10,
            median: value.median,
            p90: value.p90,
            p99: value.p99,
            max: value.max,
        }
    }
}

#[pyclass(
    name = "NeighborShellDiagnostics",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyNeighborShellDiagnostics {
    #[pyo3(get)]
    query_count: usize,
    #[pyo3(get)]
    zero_radius_queries: usize,
    #[pyo3(get)]
    ambiguous_positive_shell_queries: usize,
    kth_radius: PyDistanceQuantiles,
}

#[pymethods]
impl PyNeighborShellDiagnostics {
    #[getter]
    fn kth_radius(&self) -> PyDistanceQuantiles {
        self.kth_radius.clone()
    }
}

impl From<NeighborShellDiagnostics> for PyNeighborShellDiagnostics {
    fn from(value: NeighborShellDiagnostics) -> Self {
        Self {
            query_count: value.query_count,
            zero_radius_queries: value.zero_radius_queries,
            ambiguous_positive_shell_queries: value.ambiguous_positive_shell_queries,
            kth_radius: value.kth_radius.into(),
        }
    }
}

#[pyclass(
    name = "CoordinateCardinality",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyCoordinateCardinality {
    #[pyo3(get)]
    coordinate: usize,
    #[pyo3(get)]
    unique_values: usize,
    #[pyo3(get)]
    tied_groups: usize,
    #[pyo3(get)]
    repeated_observations: usize,
    #[pyo3(get)]
    max_multiplicity: usize,
    #[pyo3(get)]
    minimum_positive_spacing: Option<f64>,
    #[pyo3(get)]
    maximum_positive_spacing: Option<f64>,
    #[pyo3(get)]
    unrepresentable_positive_spacings: usize,
}

#[pyclass(
    name = "ContinuousInputReport",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyContinuousInputReport {
    #[pyo3(get)]
    n_samples: usize,
    #[pyo3(get)]
    ambient_dimension: usize,
    #[pyo3(get)]
    unique_rows: usize,
    #[pyo3(get)]
    tied_row_groups: usize,
    #[pyo3(get)]
    repeated_rows: usize,
    #[pyo3(get)]
    max_row_multiplicity: usize,
    coordinates: Vec<PyCoordinateCardinality>,
    marginal_shells: PyNeighborShellDiagnostics,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PyContinuousInputReport {
    #[getter]
    fn coordinates(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        let mut values = Vec::new();
        values
            .try_reserve_exact(self.coordinates.len())
            .map_err(|_| {
                resource_error(
                    py,
                    "allocation_failed",
                    "coordinate tuple allocation failed",
                    [],
                )
            })?;
        for (index, value) in self.coordinates.iter().enumerate() {
            if index.is_multiple_of(1024) {
                py.check_signals()?;
            }
            values.push(Py::new(py, value.clone())?);
        }
        Ok(PyTuple::new(py, values)?.unbind())
    }

    #[getter]
    fn marginal_shells(&self) -> PyNeighborShellDiagnostics {
        self.marginal_shells.clone()
    }
}

impl PyContinuousInputReport {
    fn try_from_core(py: Python<'_>, value: ContinuousInputDiagnostics) -> PyResult<Self> {
        let mut coordinates = Vec::new();
        coordinates
            .try_reserve_exact(value.coordinates.len())
            .map_err(|_| {
                resource_error(
                    py,
                    "allocation_failed",
                    "pid-python continuous diagnostic conversion allocation failed",
                    [(
                        "requested_bytes".to_owned(),
                        ((value.coordinates.len() as u128)
                            * size_of::<PyCoordinateCardinality>() as u128)
                            .to_string(),
                    )],
                )
            })?;
        for (index, coordinate) in value.coordinates.into_iter().enumerate() {
            if index.is_multiple_of(1024) {
                py.check_signals()?;
            }
            coordinates.push(PyCoordinateCardinality {
                coordinate: coordinate.coordinate,
                unique_values: coordinate.unique_values,
                tied_groups: coordinate.tied_groups,
                repeated_observations: coordinate.repeated_observations,
                max_multiplicity: coordinate.max_multiplicity,
                minimum_positive_spacing: coordinate.minimum_positive_spacing,
                maximum_positive_spacing: coordinate.maximum_positive_spacing,
                unrepresentable_positive_spacings: coordinate.unrepresentable_positive_spacings,
            });
        }
        Ok(Self {
            n_samples: value.n_samples,
            ambient_dimension: value.ambient_dimension,
            unique_rows: value.unique_rows,
            tied_row_groups: value.tied_row_groups,
            repeated_rows: value.repeated_rows,
            max_row_multiplicity: value.max_row_multiplicity,
            coordinates,
            marginal_shells: value.marginal_shells.into(),
            status: "finite_sample_checks_reported".to_owned(),
            warnings: vec![
                "sample diagnostics can identify observed incompatibilities but cannot prove the population support model".to_owned(),
            ],
        })
    }
}

#[pyclass(
    name = "DistanceConcentrationReport",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyDistanceConcentrationReport {
    #[pyo3(get)]
    n_samples: usize,
    #[pyo3(get)]
    ambient_dimension: usize,
    #[pyo3(get)]
    metric: String,
    #[pyo3(get)]
    pairwise_count: u64,
    #[pyo3(get)]
    pairwise_min: f64,
    #[pyo3(get)]
    pairwise_max: f64,
    #[pyo3(get)]
    pairwise_mean: f64,
    #[pyo3(get)]
    pairwise_std: f64,
    #[pyo3(get)]
    pairwise_cv: f64,
    #[pyo3(get)]
    nn_min: f64,
    #[pyo3(get)]
    nn_max: f64,
    #[pyo3(get)]
    nn_mean: f64,
    #[pyo3(get)]
    nn_std: f64,
    #[pyo3(get)]
    nn_cv: f64,
    #[pyo3(get)]
    nn_over_pairwise_mean: f64,
    #[pyo3(get)]
    warnings: Vec<String>,
}

impl PyDistanceConcentrationReport {
    fn from_core(
        n_samples: usize,
        ambient_dimension: usize,
        value: DistanceConcentrationStats,
    ) -> Self {
        Self {
            n_samples,
            ambient_dimension,
            metric: "chebyshev".to_owned(),
            pairwise_count: value.pairwise_count,
            pairwise_min: value.pairwise_min,
            pairwise_max: value.pairwise_max,
            pairwise_mean: value.pairwise_mean,
            pairwise_std: value.pairwise_std,
            pairwise_cv: value.pairwise_cv,
            nn_min: value.nn_min,
            nn_max: value.nn_max,
            nn_mean: value.nn_mean,
            nn_std: value.nn_std,
            nn_cv: value.nn_cv,
            nn_over_pairwise_mean: value.nn_over_pairwise_mean,
            warnings: vec![
                "distance concentration is a finite-sample diagnostic, not proof that a kNN estimator is valid".to_owned(),
            ],
        }
    }
}

#[pyclass(
    name = "IntrinsicDimensionReport",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyIntrinsicDimensionReport {
    #[pyo3(get)]
    estimate: f64,
    #[pyo3(get)]
    n_samples: usize,
    #[pyo3(get)]
    ambient_dimension: usize,
    #[pyo3(get)]
    k: usize,
    #[pyo3(get)]
    metric: String,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pyfunction]
#[pyo3(signature = (x, k=10, *, budget=None))]
fn diagnose_continuous_input(
    py: Python<'_>,
    x: PyReadonlyArray2<'_, f64>,
    k: usize,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyContinuousInputReport> {
    let budget = effective_budget(budget.as_deref());
    let x = copy_f64_matrix(py, &x, "diagnose_continuous_input", &budget)?;
    let retained_input_bytes = allocation_bytes(
        py,
        "diagnose_continuous_input",
        x.data.len(),
        size_of::<f64>(),
    )?;
    let conversion_bytes = allocation_bytes(
        py,
        "diagnose_continuous_input",
        x.ncols,
        size_of::<PyCoordinateCardinality>(),
    )?;
    let retained_and_conversion_bytes = retained_input_bytes
        .checked_add(conversion_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "diagnose_continuous_input: conversion-byte estimate overflow",
                [],
            )
        })?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "diagnose_continuous_input",
        retained_and_conversion_bytes,
        (x.data.len() as u128)
            .checked_add(x.ncols as u128)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    "diagnose_continuous_input: wrapper operation estimate overflow",
                    [],
                )
            })?,
    )?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "diagnose_continuous_input",
        move |cancellation| {
            let matrix = x.as_ref()?;
            core_continuous_input_diagnostics_with_budget_and_cancellation(
                matrix,
                k,
                Metric::Chebyshev,
                core_budget,
                cancellation,
            )
        },
    )?;
    PyContinuousInputReport::try_from_core(py, result)
}

#[pyfunction]
#[pyo3(signature = (x, *, budget=None))]
fn distance_concentration_report(
    py: Python<'_>,
    x: PyReadonlyArray2<'_, f64>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyDistanceConcentrationReport> {
    let budget = effective_budget(budget.as_deref());
    let x = copy_f64_matrix(py, &x, "distance_concentration_report", &budget)?;
    let retained_bytes = allocation_bytes(
        py,
        "distance_concentration_report",
        x.data.len(),
        size_of::<f64>(),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "distance_concentration_report",
        retained_bytes,
        x.data.len() as u128,
    )?;
    let nrows = x.nrows;
    let ncols = x.ncols;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "distance_concentration_report",
        move |cancellation| {
            let matrix = x.as_ref()?;
            distance_concentration_stats_with_budget_and_cancellation(
                matrix,
                &DistanceConcentrationConfig::default().with_metric(Metric::Chebyshev),
                core_budget,
                cancellation,
            )
        },
    )?;
    Ok(PyDistanceConcentrationReport::from_core(
        nrows, ncols, result,
    ))
}

#[pyfunction]
#[pyo3(signature = (x, k=10, *, budget=None))]
fn intrinsic_dimension_report(
    py: Python<'_>,
    x: PyReadonlyArray2<'_, f64>,
    k: usize,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyIntrinsicDimensionReport> {
    let budget = effective_budget(budget.as_deref());
    let x = copy_f64_matrix(py, &x, "intrinsic_dimension_report", &budget)?;
    let retained_bytes = allocation_bytes(
        py,
        "intrinsic_dimension_report",
        x.data.len(),
        size_of::<f64>(),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "intrinsic_dimension_report",
        retained_bytes,
        x.data.len() as u128,
    )?;
    let n_samples = x.nrows;
    let ambient_dimension = x.ncols;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "intrinsic_dimension_report",
        move |cancellation| {
            let matrix = x.as_ref()?;
            core_intrinsic_dimension_report_with_cancellation(
                matrix,
                &IntrinsicDimConfig::default()
                    .with_k(k)
                    .with_metric(Metric::Chebyshev),
                core_budget,
                cancellation,
            )
        },
    )?;
    Ok(PyIntrinsicDimensionReport {
            estimate: result.mean,
            n_samples,
            ambient_dimension,
            k,
            metric: "chebyshev".to_owned(),
            status: "finite_sample_diagnostic".to_owned(),
            warnings: vec![
                "intrinsic-dimension estimates can be sensitive to k, boundaries, outliers, and heterogeneous local dimension".to_owned(),
            ],
        })
}

fn debug_code(value: &impl std::fmt::Debug) -> String {
    let source = format!("{value:?}");
    let mut code = String::with_capacity(source.len());
    for (index, character) in source.chars().enumerate() {
        if character.is_ascii_uppercase() && index != 0 {
            code.push('_');
        }
        code.push(character.to_ascii_lowercase());
    }
    code
}

#[pyclass(
    name = "ValueQuantiles",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyValueQuantiles {
    #[pyo3(get)]
    min: f64,
    #[pyo3(get)]
    p10: f64,
    #[pyo3(get)]
    median: f64,
    #[pyo3(get)]
    p90: f64,
    #[pyo3(get)]
    p99: f64,
    #[pyo3(get)]
    max: f64,
}

impl From<KsgValueQuantiles> for PyValueQuantiles {
    fn from(value: KsgValueQuantiles) -> Self {
        Self {
            min: value.min,
            p10: value.p10,
            median: value.median,
            p90: value.p90,
            p99: value.p99,
            max: value.max,
        }
    }
}

#[pyclass(
    name = "CountQuantiles",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyCountQuantiles {
    #[pyo3(get)]
    min: usize,
    #[pyo3(get)]
    p10: usize,
    #[pyo3(get)]
    median: usize,
    #[pyo3(get)]
    p90: usize,
    #[pyo3(get)]
    p99: usize,
    #[pyo3(get)]
    max: usize,
}

impl From<KsgCountQuantiles> for PyCountQuantiles {
    fn from(value: KsgCountQuantiles) -> Self {
        Self {
            min: value.min,
            p10: value.p10,
            median: value.median,
            p90: value.p90,
            p99: value.p99,
            max: value.max,
        }
    }
}

#[pyclass(
    name = "KsgLocalDiagnostics",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyKsgLocalDiagnostics {
    joint_radius: PyValueQuantiles,
    x_marginal_count: PyCountQuantiles,
    y_marginal_count: PyCountQuantiles,
    local_mi_nats: PyValueQuantiles,
}

#[pymethods]
impl PyKsgLocalDiagnostics {
    #[getter]
    fn joint_radius(&self) -> PyValueQuantiles {
        self.joint_radius.clone()
    }

    #[getter]
    fn x_marginal_count(&self) -> PyCountQuantiles {
        self.x_marginal_count.clone()
    }

    #[getter]
    fn y_marginal_count(&self) -> PyCountQuantiles {
        self.y_marginal_count.clone()
    }

    #[getter]
    fn local_mi_nats(&self) -> PyValueQuantiles {
        self.local_mi_nats.clone()
    }
}

impl From<KsgLocalDiagnosticsSummary> for PyKsgLocalDiagnostics {
    fn from(value: KsgLocalDiagnosticsSummary) -> Self {
        Self {
            joint_radius: value.joint_radius.into(),
            x_marginal_count: value.x_marginal_count.into(),
            y_marginal_count: value.y_marginal_count.into(),
            local_mi_nats: value.local_mi_nats.into(),
        }
    }
}

#[pyclass(
    name = "AssumptionLedgerEntry",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyAssumptionLedgerEntry {
    #[pyo3(get)]
    assumption: String,
    #[pyo3(get)]
    state: String,
    #[pyo3(get)]
    note: String,
}

#[pyclass(
    name = "EstimandIdentity",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyEstimandIdentity {
    #[pyo3(get)]
    family: String,
    #[pyo3(get)]
    definition_revision: String,
    #[pyo3(get)]
    estimator_revision: String,
    #[pyo3(get)]
    units: String,
    #[pyo3(get)]
    metric: String,
    #[pyo3(get)]
    source_gauge: Option<String>,
}

#[pyclass(
    name = "Provenance",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyProvenance {
    #[pyo3(get)]
    preprocessing_description: String,
    #[pyo3(get)]
    observation_model_description: String,
    #[pyo3(get)]
    dependence_model_description: String,
    #[pyo3(get)]
    input_hashes_sha256: Vec<String>,
    #[pyo3(get)]
    preprocessing_hash_sha256: String,
    #[pyo3(get)]
    observation_model_hash_sha256: String,
    #[pyo3(get)]
    training_split_id: Option<String>,
    #[pyo3(get)]
    evaluation_split_id: Option<String>,
}

#[pyclass(name = "MiReport", frozen, skip_from_py_object, module = "pid_core_rs")]
#[derive(Debug)]
struct PyMiReport {
    #[pyo3(get)]
    value_nats: f64,
    #[pyo3(get)]
    signed_value_nats: f64,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    support_assertion: String,
    #[pyo3(get)]
    n_samples: usize,
    #[pyo3(get)]
    x_dimension: usize,
    #[pyo3(get)]
    y_dimension: usize,
    #[pyo3(get)]
    k: usize,
    #[pyo3(get)]
    backend: String,
    #[pyo3(get)]
    backend_fallback_occurred: bool,
    #[pyo3(get)]
    method_status: String,
    #[pyo3(get)]
    geometry_model: String,
    #[pyo3(get)]
    estimated_pairwise_distances: u64,
    #[pyo3(get)]
    estimated_bytes: u64,
    estimand: Py<PyEstimandIdentity>,
    provenance: Py<PyProvenance>,
    assumption_ledger: Vec<Py<PyAssumptionLedgerEntry>>,
    x_diagnostics: Py<PyContinuousInputReport>,
    y_diagnostics: Py<PyContinuousInputReport>,
    joint_shells: PyNeighborShellDiagnostics,
    local_diagnostics: PyKsgLocalDiagnostics,
    resource_estimate: PyResourceEstimate,
    resource_budget: PyResourceBudget,
    #[pyo3(get)]
    warning_codes: Vec<String>,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PyMiReport {
    #[getter]
    fn estimand(&self, py: Python<'_>) -> Py<PyEstimandIdentity> {
        self.estimand.clone_ref(py)
    }

    #[getter]
    fn provenance(&self, py: Python<'_>) -> Py<PyProvenance> {
        self.provenance.clone_ref(py)
    }

    #[getter]
    fn assumption_ledger(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        Ok(PyTuple::new(
            py,
            self.assumption_ledger
                .iter()
                .map(|entry| entry.clone_ref(py)),
        )?
        .unbind())
    }

    #[getter]
    fn x_diagnostics(&self, py: Python<'_>) -> Py<PyContinuousInputReport> {
        self.x_diagnostics.clone_ref(py)
    }

    #[getter]
    fn y_diagnostics(&self, py: Python<'_>) -> Py<PyContinuousInputReport> {
        self.y_diagnostics.clone_ref(py)
    }

    #[getter]
    fn joint_shells(&self) -> PyNeighborShellDiagnostics {
        self.joint_shells.clone()
    }

    #[getter]
    fn local_diagnostics(&self) -> PyKsgLocalDiagnostics {
        self.local_diagnostics.clone()
    }

    #[getter]
    fn resource_estimate(&self) -> PyResourceEstimate {
        self.resource_estimate.clone()
    }

    #[getter]
    fn resource_budget(&self) -> PyResourceBudget {
        self.resource_budget.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "MiReport(value_nats={:.6}, signed_value_nats={:.6}, status='{}', n_samples={}, k={})",
            self.value_nats, self.signed_value_nats, self.status, self.n_samples, self.k
        )
    }
}

const REGULAR_CONTINUOUS_ASSERTION: &str = "regular_full_dimensional_absolutely_continuous";

#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (
    x,
    y,
    k=3,
    *,
    support_assertion,
    preprocessing_description,
    observation_model_description,
    dependence_model_description,
    training_split_id=None,
    evaluation_split_id=None,
    budget=None
))]
fn compute_mi_report(
    py: Python<'_>,
    x: PyReadonlyArray2<'_, f64>,
    y: PyReadonlyArray2<'_, f64>,
    k: usize,
    support_assertion: &str,
    preprocessing_description: &str,
    observation_model_description: &str,
    dependence_model_description: &str,
    training_split_id: Option<&str>,
    evaluation_split_id: Option<&str>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyMiReport> {
    if support_assertion != REGULAR_CONTINUOUS_ASSERTION {
        return Err(input_error(
            py,
            "support_contract_required",
            format!(
                "stable Euclidean KSG requires support_assertion='{REGULAR_CONTINUOUS_ASSERTION}'"
            ),
            [(
                "expected_support_assertion".to_owned(),
                REGULAR_CONTINUOUS_ASSERTION.to_owned(),
            )],
        ));
    }
    for (field, value) in [
        ("preprocessing_description", preprocessing_description),
        (
            "observation_model_description",
            observation_model_description,
        ),
        ("dependence_model_description", dependence_model_description),
    ] {
        if value.trim().is_empty() {
            return Err(input_error(
                py,
                "missing_provenance",
                format!("{field} must be nonempty"),
                [("field".to_owned(), field.to_owned())],
            ));
        }
    }
    let budget = effective_budget(budget.as_deref());
    let mut provenance_bytes = 0usize;
    for text in [
        Some(preprocessing_description),
        Some(observation_model_description),
        Some(dependence_model_description),
        training_split_id,
        evaluation_split_id,
    ]
    .into_iter()
    .flatten()
    {
        provenance_bytes = provenance_bytes.checked_add(text.len()).ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: provenance-byte estimate overflow",
                [],
            )
        })?;
    }
    budget.check_wrapper_peak_bytes(py, "compute_mi_report", provenance_bytes as u128)?;
    let core_provenance = KsgProvenance::new(
        preprocessing_description,
        observation_model_description,
        None,
    )
    .and_then(|provenance| {
        provenance.with_sampling_model_and_splits(
            dependence_model_description,
            training_split_id,
            evaluation_split_id,
        )
    })
    .map_err(|error| core_error(py, error))?;

    let x_len = array_element_count(py, &x, "compute_mi_report.x")?;
    let y_len = array_element_count(py, &y, "compute_mi_report.y")?;
    let (input_elements, retained_input_bytes) = preflight_aggregate_copies(
        py,
        "compute_mi_report",
        &budget,
        &[x_len, y_len],
        size_of::<f64>(),
    )?;
    let x = copy_f64_matrix(py, &x, "compute_mi_report.x", &budget)?;
    let y = copy_f64_matrix(py, &y, "compute_mi_report.y", &budget)?;
    validate_aligned_rows(py, "compute_mi_report", &[x.nrows, y.nrows])?;
    let diagnostic_coordinates = x.ncols.checked_add(y.ncols).ok_or_else(|| {
        resource_error(
            py,
            "resource_estimate_overflow",
            "compute_mi_report: diagnostic coordinate count overflow",
            [],
        )
    })?;
    let coordinate_conversion_bytes = allocation_bytes(
        py,
        "compute_mi_report",
        diagnostic_coordinates,
        size_of::<PyCoordinateCardinality>(),
    )?;
    let provenance_conversion_bytes =
        allocation_bytes(py, "compute_mi_report", provenance_bytes, 2)?;
    let wrapper_conversion_bytes = coordinate_conversion_bytes
        .checked_add(provenance_conversion_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: conversion-byte estimate overflow",
                [],
            )
        })?;
    let reserved_wrapper_bytes = retained_input_bytes
        .checked_add(wrapper_conversion_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: wrapper-byte estimate overflow",
                [],
            )
        })?;
    let wrapper_operations = (input_elements as u128)
        .checked_add(diagnostic_coordinates as u128)
        .and_then(|value| value.checked_add((provenance_bytes as u128).checked_mul(2)?))
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: wrapper operation estimate overflow",
                [],
            )
        })?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_mi_report",
        reserved_wrapper_bytes,
        wrapper_operations,
    )?;

    let x_dimension = x.ncols;
    let y_dimension = y.ncols;
    let n_samples = x.nrows;
    let config = KsgConfig::assume_regular_full_dimensional().with_k(k);

    let mut report =
        run_owned_worker_with_signal_cancellation(py, "compute_mi_report", move |cancellation| {
            let x_ref = x.as_ref()?;
            let y_ref = y.as_ref()?;
            ksg_mi_report_with_budget_and_cancellation(
                x_ref,
                y_ref,
                &config,
                &core_provenance,
                core_budget,
                cancellation,
            )
        })?;
    let mut warnings = Vec::new();
    warnings
        .try_reserve_exact(report.warnings.len())
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "warning-list allocation failed",
                [],
            )
        })?;
    for warning in &report.warnings {
        warnings.push(warning.message().to_owned());
    }
    let mut warning_codes = Vec::new();
    warning_codes
        .try_reserve_exact(report.report_warnings.len())
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "warning-code list allocation failed",
                [],
            )
        })?;
    for warning in &report.report_warnings {
        warning_codes.push(debug_code(warning));
    }
    let mut assumption_ledger = Vec::new();
    assumption_ledger
        .try_reserve_exact(report.assumption_ledger.len())
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "assumption ledger allocation failed",
                [],
            )
        })?;
    for entry in &report.assumption_ledger {
        assumption_ledger.push(Py::new(
            py,
            PyAssumptionLedgerEntry {
                assumption: debug_code(&entry.assumption),
                state: debug_code(&entry.state),
                note: entry.note.to_owned(),
            },
        )?);
    }
    let backend = match report.neighbor_backend {
        KsgNeighborBackend::BruteForce => "brute_force",
        KsgNeighborBackend::ExactChebyshevKdTree => "exact_chebyshev_kd_tree",
        #[allow(unreachable_patterns)]
        _ => "unknown",
    }
    .to_owned();
    let aggregate_estimated_bytes = report
        .resource_estimate
        .estimated_bytes
        .checked_add(reserved_wrapper_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: aggregate reported byte estimate overflow",
                [],
            )
        })?;
    let aggregate_operations_hint = report
        .resource_estimate
        .operations_hint
        .checked_add(wrapper_operations)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_mi_report: aggregate reported operation estimate overflow",
                [],
            )
        })?;
    let estimated_pairwise = report
        .resource_estimate
        .pairwise_distances
        .min(u64::MAX as u128) as u64;
    let estimated_bytes = aggregate_estimated_bytes.min(u64::MAX as u128) as u64;
    let aggregate_resource_estimate = PyResourceEstimate {
        estimated_bytes: aggregate_estimated_bytes,
        pairwise_distances: report.resource_estimate.pairwise_distances,
        operations_hint: aggregate_operations_hint,
    };
    let estimand = PyEstimandIdentity {
        family: report.estimand.family.to_owned(),
        definition_revision: report.estimand.definition_revision.to_owned(),
        estimator_revision: report.estimand.estimator_revision.to_owned(),
        units: debug_code(&report.estimand.units),
        metric: report.estimand.metric.to_owned(),
        source_gauge: report.estimand.source_gauge.map(str::to_owned),
    };
    let mut input_hashes_sha256 = Vec::new();
    input_hashes_sha256
        .try_reserve_exact(report.provenance_hashes.input_hashes_sha256.len())
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "provenance hash-list allocation failed",
                [],
            )
        })?;
    for hash in &report.provenance_hashes.input_hashes_sha256 {
        input_hashes_sha256.push(hex_digest(*hash));
    }
    let Some(dependence_model_description) = report.provenance.sampling_model_description() else {
        return Err(numerical_error(
            py,
            "missing_core_provenance",
            "compute_mi_report: core report omitted the declared sampling model",
            [],
        ));
    };
    let provenance = PyProvenance {
        preprocessing_description: try_string_copy(
            py,
            "compute_mi_report.preprocessing_description",
            report.provenance.preprocessing_description(),
        )?,
        observation_model_description: try_string_copy(
            py,
            "compute_mi_report.observation_model_description",
            report.provenance.observation_model_description(),
        )?,
        dependence_model_description: try_string_copy(
            py,
            "compute_mi_report.dependence_model_description",
            dependence_model_description,
        )?,
        input_hashes_sha256,
        preprocessing_hash_sha256: hex_digest(report.provenance_hashes.preprocessing_hash_sha256),
        observation_model_hash_sha256: hex_digest(
            report.provenance_hashes.observation_model_hash_sha256,
        ),
        training_split_id: report.provenance_hashes.training_split_id.take(),
        evaluation_split_id: report.provenance_hashes.evaluation_split_id.take(),
    };
    let x_diagnostics = PyContinuousInputReport::try_from_core(py, report.x_diagnostics)?;
    let y_diagnostics = PyContinuousInputReport::try_from_core(py, report.y_diagnostics)?;

    Ok(PyMiReport {
        value_nats: report.estimate_nats,
        signed_value_nats: report.signed_estimate_nats,
        status: debug_code(&report.scientific_status),
        support_assertion: REGULAR_CONTINUOUS_ASSERTION.to_owned(),
        n_samples,
        x_dimension,
        y_dimension,
        k,
        backend,
        backend_fallback_occurred: report.backend_fallback_occurred,
        method_status: debug_code(&report.method_status),
        geometry_model: debug_code(&report.geometry_model),
        estimated_pairwise_distances: estimated_pairwise,
        estimated_bytes,
        estimand: Py::new(py, estimand)?,
        provenance: Py::new(py, provenance)?,
        assumption_ledger,
        x_diagnostics: Py::new(py, x_diagnostics)?,
        y_diagnostics: Py::new(py, y_diagnostics)?,
        joint_shells: report.joint_shells.into(),
        local_diagnostics: report.local_diagnostics.into(),
        resource_estimate: aggregate_resource_estimate,
        resource_budget: budget,
        warning_codes,
        warnings,
    })
}

#[pyclass(name = "SxAtom", frozen, skip_from_py_object, module = "pid_core_rs")]
#[derive(Debug, Clone)]
struct PySxAtom {
    #[pyo3(get)]
    informative_nats: f64,
    #[pyo3(get)]
    misinformative_nats: f64,
    #[pyo3(get)]
    net_nats: f64,
}

#[pyclass(
    name = "EmpiricalPmfDiagnostics",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyEmpiricalPmfDiagnostics {
    #[pyo3(get)]
    sample_count: usize,
    #[pyo3(get)]
    observed_joint_states: usize,
    #[pyo3(get)]
    singleton_joint_states: usize,
    #[pyo3(get)]
    low_count_joint_states: usize,
    #[pyo3(get)]
    minimum_observed_count: usize,
    #[pyo3(get)]
    maximum_observed_count: usize,
    #[pyo3(get)]
    observed_coverage_indicator: f64,
    #[pyo3(get)]
    population_caveat: &'static str,
}

impl From<EmpiricalPmfDiagnostics> for PyEmpiricalPmfDiagnostics {
    fn from(value: EmpiricalPmfDiagnostics) -> Self {
        Self {
            sample_count: value.sample_count,
            observed_joint_states: value.observed_joint_states,
            singleton_joint_states: value.singleton_joint_states,
            low_count_joint_states: value.low_count_joint_states,
            minimum_observed_count: value.minimum_observed_count,
            maximum_observed_count: value.maximum_observed_count,
            observed_coverage_indicator: value.observed_coverage_indicator,
            population_caveat: value.population_caveat,
        }
    }
}

impl From<CoreSxAtom> for PySxAtom {
    fn from(value: CoreSxAtom) -> Self {
        Self {
            informative_nats: value.informative,
            misinformative_nats: value.misinformative,
            net_nats: value.net,
        }
    }
}

#[pyclass(
    name = "SxPid2Result",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PySxPid2Result {
    redundancy: PySxAtom,
    unique_s1: PySxAtom,
    unique_s2: PySxAtom,
    synergy: PySxAtom,
    #[pyo3(get)]
    mi_s1_t_nats: f64,
    #[pyo3(get)]
    mi_s2_t_nats: f64,
    #[pyo3(get)]
    mi_s1s2_t_nats: f64,
    #[pyo3(get)]
    input_encoding: String,
    #[pyo3(get)]
    observed_cardinalities: Vec<usize>,
    #[pyo3(get)]
    pointwise_included: bool,
    empirical_pmf: PyEmpiricalPmfDiagnostics,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PySxPid2Result {
    #[getter]
    fn redundancy(&self) -> PySxAtom {
        self.redundancy.clone()
    }

    #[getter]
    fn unique_s1(&self) -> PySxAtom {
        self.unique_s1.clone()
    }

    #[getter]
    fn unique_s2(&self) -> PySxAtom {
        self.unique_s2.clone()
    }

    #[getter]
    fn synergy(&self) -> PySxAtom {
        self.synergy.clone()
    }

    #[getter]
    fn empirical_pmf(&self) -> PyEmpiricalPmfDiagnostics {
        self.empirical_pmf.clone()
    }

    fn __repr__(&self) -> String {
        format!(
            "SxPid2Result(redundancy={:.6}, unique_s1={:.6}, unique_s2={:.6}, synergy={:.6})",
            self.redundancy.net_nats,
            self.unique_s1.net_nats,
            self.unique_s2.net_nats,
            self.synergy.net_nats
        )
    }
}

fn encoding_name(encoding: &DiscreteInputEncoding) -> String {
    match encoding {
        DiscreteInputEncoding::Categorical => "categorical".to_owned(),
        DiscreteInputEncoding::FittedEqualWidth => "fitted_equal_width".to_owned(),
        #[cfg(feature = "python-experimental")]
        DiscreteInputEncoding::EqualWidth { num_bins } => format!("equal_width:{num_bins}"),
        #[allow(unreachable_patterns)]
        _ => "unknown".to_owned(),
    }
}

impl From<DiscreteSxPid2Result> for PySxPid2Result {
    fn from(value: DiscreteSxPid2Result) -> Self {
        Self {
            redundancy: value.red.into(),
            unique_s1: value.unq1.into(),
            unique_s2: value.unq2.into(),
            synergy: value.syn.into(),
            mi_s1_t_nats: value.mi_s1_t,
            mi_s2_t_nats: value.mi_s2_t,
            mi_s1s2_t_nats: value.mi_s1s2_t,
            input_encoding: encoding_name(&value.input.encoding),
            observed_cardinalities: value.input.observed_cardinalities,
            pointwise_included: value.pointwise_included,
            empirical_pmf: value.empirical_pmf.into(),
            status: "empirical_pmf".to_owned(),
            warnings: vec![
                "this is direct evaluation on the empirical categorical PMF, not an unbiased population estimate".to_owned(),
                "pointwise atoms remain available in the Rust API; the stable Python result intentionally returns the bounded averaged report".to_owned(),
            ],
        }
    }
}

#[pyclass(
    name = "Antichain",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyAntichain {
    sets: Vec<u8>,
}

#[pymethods]
impl PyAntichain {
    #[getter]
    fn sets(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        Ok(PyTuple::new(py, self.sets.iter().copied())?.unbind())
    }

    fn __len__(&self) -> usize {
        self.sets.len()
    }

    fn __repr__(&self) -> String {
        format!("Antichain(sets={:?})", self.sets)
    }
}

#[pyclass(
    name = "AntichainAtom",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyAntichainAtom {
    antichain: PyAntichain,
    atom: PySxAtom,
}

#[pymethods]
impl PyAntichainAtom {
    #[getter]
    fn antichain(&self) -> PyAntichain {
        self.antichain.clone()
    }

    #[getter]
    fn atom(&self) -> PySxAtom {
        self.atom.clone()
    }
}

#[pyclass(
    name = "SxPidLatticeResult",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PySxPidLatticeResult {
    #[pyo3(get)]
    n_sources: usize,
    entries: Vec<PyAntichainAtom>,
    #[pyo3(get)]
    joint_mi_nats: f64,
    #[pyo3(get)]
    subset_mis_nats: Vec<f64>,
    #[pyo3(get)]
    input_encoding: String,
    #[pyo3(get)]
    observed_cardinalities: Vec<usize>,
    #[pyo3(get)]
    pointwise_included: bool,
    empirical_pmf: PyEmpiricalPmfDiagnostics,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PySxPidLatticeResult {
    #[getter]
    fn entries(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        let mut entries = Vec::new();
        entries.try_reserve_exact(self.entries.len()).map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "lattice entry tuple allocation failed",
                [],
            )
        })?;
        for entry in &self.entries {
            entries.push(Py::new(py, entry.clone())?);
        }
        Ok(PyTuple::new(py, entries)?.unbind())
    }

    #[getter]
    fn empirical_pmf(&self) -> PyEmpiricalPmfDiagnostics {
        self.empirical_pmf.clone()
    }

    fn atom(&self, py: Python<'_>, sets: &Bound<'_, PyAny>) -> PyResult<Option<PySxAtom>> {
        let sequence = sets.cast::<PySequence>().map_err(|_| {
            input_error(
                py,
                "invalid_antichain",
                "sets must be a finite sequence of source-set bitmasks",
                [],
            )
        })?;
        let length = sequence.len()?;
        let maximum_length = 1usize.checked_shl(self.n_sources as u32).unwrap_or(0);
        if length > maximum_length {
            return Err(input_error(
                py,
                "invalid_antichain",
                "sets contains more source subsets than the lattice can contain",
                [
                    ("length".to_owned(), length.to_string()),
                    ("maximum_length".to_owned(), maximum_length.to_string()),
                ],
            ));
        }
        let mut sets = Vec::new();
        sets.try_reserve_exact(length).map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "antichain query allocation failed",
                [("requested_elements".to_owned(), length.to_string())],
            )
        })?;
        for index in 0..length {
            sets.push(sequence.get_item(index)?.extract::<u8>()?);
        }
        sets.sort_unstable();
        Ok(self
            .entries
            .iter()
            .find(|entry| entry.antichain.sets == sets)
            .map(|entry| entry.atom.clone()))
    }
}

fn convert_lattice_entries(
    antichains: Vec<Vec<u8>>,
    atoms: Vec<CoreSxAtom>,
    operation: &'static str,
) -> Result<Vec<PyAntichainAtom>, CorePidError> {
    let mut entries = Vec::new();
    entries
        .try_reserve_exact(antichains.len())
        .map_err(|_| CorePidError::AllocationFailed {
            operation,
            requested_bytes: (antichains.len() as u128) * size_of::<PyAntichainAtom>() as u128,
        })?;
    for (sets, atom) in antichains.into_iter().zip(atoms) {
        entries.push(PyAntichainAtom {
            antichain: PyAntichain { sets },
            atom: atom.into(),
        });
    }
    Ok(entries)
}

impl PySxPidLatticeResult {
    fn try_from_pid3(value: DiscreteSxPid3Result) -> Result<Self, CorePidError> {
        let entries = convert_lattice_entries(
            value.antichains,
            value.atoms,
            "pid-python SxPID3 result conversion",
        )?;
        Ok(Self {
            n_sources: 3,
            entries,
            joint_mi_nats: value.mi_s0s1s2_t,
            subset_mis_nats: value.subset_mis,
            input_encoding: encoding_name(&value.input.encoding),
            observed_cardinalities: value.input.observed_cardinalities,
            pointwise_included: value.pointwise_included,
            empirical_pmf: value.empirical_pmf.into(),
            status: "empirical_pmf".to_owned(),
            warnings: vec![
                "this is direct evaluation on the empirical categorical PMF, not an unbiased population estimate".to_owned(),
            ],
        })
    }

    fn try_from_pid_n(value: DiscreteSxPidNResult) -> Result<Self, CorePidError> {
        let entries = convert_lattice_entries(
            value.antichains,
            value.atoms,
            "pid-python SxPID-N result conversion",
        )?;
        Ok(Self {
            n_sources: value.n_sources,
            entries,
            joint_mi_nats: value.joint_mi,
            subset_mis_nats: value.subset_mis,
            input_encoding: encoding_name(&value.input.encoding),
            observed_cardinalities: value.input.observed_cardinalities,
            pointwise_included: value.pointwise_included,
            empirical_pmf: value.empirical_pmf.into(),
            status: "empirical_pmf".to_owned(),
            warnings: vec![
                "this is direct evaluation on the empirical categorical PMF, not an unbiased population estimate".to_owned(),
            ],
        })
    }
}

fn encode_owned(
    py: Python<'_>,
    input: OwnedI64Matrix,
    operation: &'static str,
) -> PyResult<EncodedDiscreteMatrix> {
    run_owned_worker_with_signal_cancellation(py, operation, move |cancellation| {
        encode_discrete(&input, operation, cancellation)
    })
}

#[pyfunction]
#[pyo3(signature = (s1, s2, target, *, budget=None))]
fn compute_categorical_sxpid2(
    py: Python<'_>,
    s1: PyReadonlyArray2<'_, i64>,
    s2: PyReadonlyArray2<'_, i64>,
    target: PyReadonlyArray2<'_, i64>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PySxPid2Result> {
    let budget = effective_budget(budget.as_deref());
    let lengths = [
        array_element_count(py, &s1, "compute_categorical_sxpid2.s1")?,
        array_element_count(py, &s2, "compute_categorical_sxpid2.s2")?,
        array_element_count(py, &target, "compute_categorical_sxpid2.target")?,
    ];
    let (input_elements, _) = preflight_aggregate_copies(
        py,
        "compute_categorical_sxpid2",
        &budget,
        &lengths,
        size_of::<i64>(),
    )?;
    let (encoding_peak_bytes, wrapper_operations) =
        categorical_wrapper_cost(py, "compute_categorical_sxpid2", &lengths)?;
    budget.check_wrapper_peak_bytes(py, "compute_categorical_sxpid2", encoding_peak_bytes)?;
    let retained_encoded_bytes = allocation_bytes(
        py,
        "compute_categorical_sxpid2",
        input_elements,
        size_of::<usize>(),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_categorical_sxpid2",
        retained_encoded_bytes,
        wrapper_operations,
    )?;
    let s1 = copy_i64_matrix(py, &s1, "compute_categorical_sxpid2.s1", &budget)?;
    let s2 = copy_i64_matrix(py, &s2, "compute_categorical_sxpid2.s2", &budget)?;
    let target = copy_i64_matrix(py, &target, "compute_categorical_sxpid2.target", &budget)?;
    validate_aligned_rows(
        py,
        "compute_categorical_sxpid2",
        &[s1.nrows, s2.nrows, target.nrows],
    )?;
    let s1 = encode_owned(py, s1, "compute_categorical_sxpid2.s1")?;
    let s2 = encode_owned(py, s2, "compute_categorical_sxpid2.s2")?;
    let target = encode_owned(py, target, "compute_categorical_sxpid2.target")?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "compute_categorical_sxpid2",
        move |cancellation| {
            discrete_sxpid2_averaged_with_budget_and_cancellation(
                s1.as_ref()?,
                s2.as_ref()?,
                target.as_ref()?,
                core_budget,
                cancellation,
            )
        },
    )?;
    Ok(PySxPid2Result::from(result))
}

#[pyfunction]
#[pyo3(signature = (s0, s1, s2, target, *, budget=None))]
fn compute_categorical_sxpid3(
    py: Python<'_>,
    s0: PyReadonlyArray2<'_, i64>,
    s1: PyReadonlyArray2<'_, i64>,
    s2: PyReadonlyArray2<'_, i64>,
    target: PyReadonlyArray2<'_, i64>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PySxPidLatticeResult> {
    let budget = effective_budget(budget.as_deref());
    let lengths = [
        array_element_count(py, &s0, "compute_categorical_sxpid3.s0")?,
        array_element_count(py, &s1, "compute_categorical_sxpid3.s1")?,
        array_element_count(py, &s2, "compute_categorical_sxpid3.s2")?,
        array_element_count(py, &target, "compute_categorical_sxpid3.target")?,
    ];
    let (input_elements, _) = preflight_aggregate_copies(
        py,
        "compute_categorical_sxpid3",
        &budget,
        &lengths,
        size_of::<i64>(),
    )?;
    let (encoding_peak_bytes, wrapper_operations) =
        categorical_wrapper_cost(py, "compute_categorical_sxpid3", &lengths)?;
    budget.check_wrapper_peak_bytes(py, "compute_categorical_sxpid3", encoding_peak_bytes)?;
    let retained_encoded_bytes = allocation_bytes(
        py,
        "compute_categorical_sxpid3",
        input_elements,
        size_of::<usize>(),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_categorical_sxpid3",
        retained_encoded_bytes,
        wrapper_operations,
    )?;
    let s0 = copy_i64_matrix(py, &s0, "compute_categorical_sxpid3.s0", &budget)?;
    let s1 = copy_i64_matrix(py, &s1, "compute_categorical_sxpid3.s1", &budget)?;
    let s2 = copy_i64_matrix(py, &s2, "compute_categorical_sxpid3.s2", &budget)?;
    let target = copy_i64_matrix(py, &target, "compute_categorical_sxpid3.target", &budget)?;
    validate_aligned_rows(
        py,
        "compute_categorical_sxpid3",
        &[s0.nrows, s1.nrows, s2.nrows, target.nrows],
    )?;
    let s0 = encode_owned(py, s0, "compute_categorical_sxpid3.s0")?;
    let s1 = encode_owned(py, s1, "compute_categorical_sxpid3.s1")?;
    let s2 = encode_owned(py, s2, "compute_categorical_sxpid3.s2")?;
    let target = encode_owned(py, target, "compute_categorical_sxpid3.target")?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "compute_categorical_sxpid3",
        move |cancellation| {
            discrete_sxpid3_averaged_with_budget_and_cancellation(
                s0.as_ref()?,
                s1.as_ref()?,
                s2.as_ref()?,
                target.as_ref()?,
                core_budget,
                cancellation,
            )
        },
    )?;
    PySxPidLatticeResult::try_from_pid3(result).map_err(|error| core_error(py, error))
}

#[pyfunction]
#[pyo3(signature = (sources, target, *, budget=None))]
fn compute_categorical_sxpid(
    py: Python<'_>,
    sources: &Bound<'_, PyAny>,
    target: PyReadonlyArray2<'_, i64>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PySxPidLatticeResult> {
    let sources = sources.cast::<PySequence>().map_err(|_| {
        input_error(
            py,
            "invalid_sources",
            "sources must be a finite sequence of NumPy int64 matrices",
            [],
        )
    })?;
    let source_count = sources.len()?;
    if !(2..=4).contains(&source_count) {
        return Err(input_error(
            py,
            "unsupported_source_count",
            "compute_categorical_sxpid supports exactly two to four sources",
            [("source_count".to_owned(), source_count.to_string())],
        ));
    }
    let budget = effective_budget(budget.as_deref());
    let mut lengths = Vec::new();
    lengths.try_reserve_exact(source_count + 1).map_err(|_| {
        resource_error(
            py,
            "allocation_failed",
            "compute_categorical_sxpid: input-shape list allocation failed",
            [],
        )
    })?;
    for index in 0..source_count {
        let source = sources
            .get_item(index)?
            .extract::<PyReadonlyArray2<'_, i64>>()?;
        lengths.push(array_element_count(
            py,
            &source,
            &format!("compute_categorical_sxpid.source[{index}]"),
        )?);
    }
    lengths.push(array_element_count(
        py,
        &target,
        "compute_categorical_sxpid.target",
    )?);
    let (input_elements, _) = preflight_aggregate_copies(
        py,
        "compute_categorical_sxpid",
        &budget,
        &lengths,
        size_of::<i64>(),
    )?;
    let (encoding_peak_bytes, wrapper_operations) =
        categorical_wrapper_cost(py, "compute_categorical_sxpid", &lengths)?;
    budget.check_wrapper_peak_bytes(py, "compute_categorical_sxpid", encoding_peak_bytes)?;
    let retained_encoded_bytes = allocation_bytes(
        py,
        "compute_categorical_sxpid",
        input_elements,
        size_of::<usize>(),
    )?;
    let source_ref_bytes = allocation_bytes(
        py,
        "compute_categorical_sxpid",
        source_count,
        size_of::<DiscreteMatRef<'_>>(),
    )?;
    let retained_bytes = retained_encoded_bytes
        .checked_add(source_ref_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_categorical_sxpid: retained-byte estimate overflow",
                [],
            )
        })?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_categorical_sxpid",
        retained_bytes,
        wrapper_operations,
    )?;
    let mut owned_sources = Vec::new();
    owned_sources.try_reserve_exact(source_count).map_err(|_| {
        resource_error(py, "allocation_failed", "source-list allocation failed", [])
    })?;
    for index in 0..source_count {
        let source = sources
            .get_item(index)?
            .extract::<PyReadonlyArray2<'_, i64>>()?;
        owned_sources.push(copy_i64_matrix(
            py,
            &source,
            &format!("compute_categorical_sxpid.source[{index}]"),
            &budget,
        )?);
    }
    let target = copy_i64_matrix(py, &target, "compute_categorical_sxpid.target", &budget)?;
    let mut rows = Vec::new();
    rows.try_reserve_exact(owned_sources.len() + 1)
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "compute_categorical_sxpid: row-count list allocation failed",
                [],
            )
        })?;
    rows.extend(owned_sources.iter().map(|source| source.nrows));
    rows.push(target.nrows);
    validate_aligned_rows(py, "compute_categorical_sxpid", &rows)?;
    let mut encoded_sources = Vec::new();
    encoded_sources
        .try_reserve_exact(owned_sources.len())
        .map_err(|_| {
            resource_error(
                py,
                "allocation_failed",
                "compute_categorical_sxpid: encoded source-list allocation failed",
                [],
            )
        })?;
    for source in owned_sources {
        encoded_sources.push(encode_owned(
            py,
            source,
            "compute_categorical_sxpid.source",
        )?);
    }
    let target = encode_owned(py, target, "compute_categorical_sxpid.target")?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "compute_categorical_sxpid",
        move |cancellation| {
            let mut source_refs = Vec::new();
            source_refs
                .try_reserve_exact(encoded_sources.len())
                .map_err(|_| CorePidError::AllocationFailed {
                    operation: "compute_categorical_sxpid.source_refs",
                    requested_bytes: source_ref_bytes,
                })?;
            for source in &encoded_sources {
                source_refs.push(source.as_ref()?);
            }
            discrete_sxpid_n_averaged_with_budget_and_cancellation(
                &source_refs,
                target.as_ref()?,
                core_budget,
                cancellation,
            )
        },
    )?;
    PySxPidLatticeResult::try_from_pid_n(result).map_err(|error| core_error(py, error))
}

#[pyclass(
    name = "IminPid2Result",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyIminPid2Result {
    #[pyo3(get)]
    redundancy_nats: f64,
    #[pyo3(get)]
    unique_s1_nats: f64,
    #[pyo3(get)]
    unique_s2_nats: f64,
    #[pyo3(get)]
    synergy_nats: f64,
    #[pyo3(get)]
    mi_s1_t_nats: f64,
    #[pyo3(get)]
    mi_s2_t_nats: f64,
    #[pyo3(get)]
    mi_s1s2_t_nats: f64,
    #[pyo3(get)]
    input_encoding: String,
    #[pyo3(get)]
    observed_cardinalities: Vec<usize>,
    empirical_pmf: PyEmpiricalPmfDiagnostics,
    #[pyo3(get)]
    status: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PyIminPid2Result {
    #[getter]
    fn empirical_pmf(&self) -> PyEmpiricalPmfDiagnostics {
        self.empirical_pmf.clone()
    }
}

impl From<CoreIminPid2Result> for PyIminPid2Result {
    fn from(value: CoreIminPid2Result) -> Self {
        let caveat = value.input.population_caveat;
        Self {
            redundancy_nats: value.redundancy,
            unique_s1_nats: value.unique_s1,
            unique_s2_nats: value.unique_s2,
            synergy_nats: value.synergy,
            mi_s1_t_nats: value.mi_s1_t,
            mi_s2_t_nats: value.mi_s2_t,
            mi_s1s2_t_nats: value.mi_s1s2_t,
            input_encoding: "categorical".to_owned(),
            observed_cardinalities: value.input.observed_cardinalities,
            empirical_pmf: PyEmpiricalPmfDiagnostics {
                sample_count: value.empirical_pmf.sample_count,
                observed_joint_states: value.empirical_pmf.observed_joint_states,
                singleton_joint_states: value.empirical_pmf.singleton_joint_states,
                low_count_joint_states: value.empirical_pmf.low_count_joint_states,
                minimum_observed_count: value.empirical_pmf.minimum_observed_count,
                maximum_observed_count: value.empirical_pmf.maximum_observed_count,
                observed_coverage_indicator: value.empirical_pmf.observed_coverage_indicator,
                population_caveat: caveat,
            },
            status: "empirical_pmf_legacy_comparator".to_owned(),
            warnings: vec![
                "Williams--Beer I_min is a different redundancy measure from shared exclusions; do not pool or relabel its atoms as I^sx atoms".to_owned(),
                "this is direct evaluation on the empirical categorical PMF, not an unbiased population estimate".to_owned(),
            ],
        }
    }
}

#[pyfunction]
#[pyo3(signature = (s1, s2, target, *, budget=None))]
fn compute_categorical_imin_pid2(
    py: Python<'_>,
    s1: PyReadonlyArray2<'_, i64>,
    s2: PyReadonlyArray2<'_, i64>,
    target: PyReadonlyArray2<'_, i64>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyIminPid2Result> {
    let budget = effective_budget(budget.as_deref());
    let lengths = [
        array_element_count(py, &s1, "compute_categorical_imin_pid2.s1")?,
        array_element_count(py, &s2, "compute_categorical_imin_pid2.s2")?,
        array_element_count(py, &target, "compute_categorical_imin_pid2.target")?,
    ];
    let (input_elements, _) = preflight_aggregate_copies(
        py,
        "compute_categorical_imin_pid2",
        &budget,
        &lengths,
        size_of::<i64>(),
    )?;
    let (encoding_peak_bytes, wrapper_operations) =
        categorical_wrapper_cost(py, "compute_categorical_imin_pid2", &lengths)?;
    budget.check_wrapper_peak_bytes(py, "compute_categorical_imin_pid2", encoding_peak_bytes)?;
    let retained_encoded_bytes = allocation_bytes(
        py,
        "compute_categorical_imin_pid2",
        input_elements,
        size_of::<usize>(),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_categorical_imin_pid2",
        retained_encoded_bytes,
        wrapper_operations,
    )?;
    let s1 = copy_i64_matrix(py, &s1, "compute_categorical_imin_pid2.s1", &budget)?;
    let s2 = copy_i64_matrix(py, &s2, "compute_categorical_imin_pid2.s2", &budget)?;
    let target = copy_i64_matrix(py, &target, "compute_categorical_imin_pid2.target", &budget)?;
    validate_aligned_rows(
        py,
        "compute_categorical_imin_pid2",
        &[s1.nrows, s2.nrows, target.nrows],
    )?;
    let s1 = encode_owned(py, s1, "compute_categorical_imin_pid2.s1")?;
    let s2 = encode_owned(py, s2, "compute_categorical_imin_pid2.s2")?;
    let target = encode_owned(py, target, "compute_categorical_imin_pid2.target")?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "compute_categorical_imin_pid2",
        move |cancellation| {
            imin_pid2_with_budget_and_cancellation(
                s1.as_ref()?,
                s2.as_ref()?,
                target.as_ref()?,
                core_budget,
                cancellation,
            )
        },
    )?;
    Ok(PyIminPid2Result::from(result))
}

fn policy_name(policy: CoreOutOfRangePolicy) -> &'static str {
    match policy {
        CoreOutOfRangePolicy::Error => "error",
        CoreOutOfRangePolicy::ClampToBoundary => "clamp_to_boundary",
        #[allow(unreachable_patterns)]
        _ => "unknown",
    }
}

fn hex_digest(bytes: [u8; 32]) -> String {
    let mut text = String::with_capacity(64);
    for byte in bytes {
        use std::fmt::Write as _;
        let _ = write!(&mut text, "{byte:02x}");
    }
    text
}

#[pyclass(
    name = "QuantizationReport",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyQuantizationReport {
    bin_edges: Vec<Vec<f64>>,
    #[pyo3(get)]
    training_data_hash_sha256: Option<String>,
    #[pyo3(get)]
    transformed_data_hash_sha256: String,
    #[pyo3(get)]
    out_of_range_policy: String,
    #[pyo3(get)]
    preprocessing_description: String,
    #[pyo3(get)]
    n_rows: usize,
    #[pyo3(get)]
    n_features: usize,
    #[pyo3(get)]
    num_bins: usize,
    #[pyo3(get)]
    nominal_joint_cardinality: Option<u128>,
    #[pyo3(get)]
    observed_joint_cardinality: usize,
    #[pyo3(get)]
    empty_joint_cells: Option<u128>,
    #[pyo3(get)]
    low_count_joint_cells: usize,
    #[pyo3(get)]
    minimum_observed_cell_count: usize,
    #[pyo3(get)]
    maximum_observed_cell_count: usize,
    #[pyo3(get)]
    estimand: String,
    #[pyo3(get)]
    warnings: Vec<String>,
}

#[pymethods]
impl PyQuantizationReport {
    #[getter]
    fn bin_edges(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        nested_f64_tuple(py, &self.bin_edges)
    }
}

impl From<CoreQuantizationReport> for PyQuantizationReport {
    fn from(value: CoreQuantizationReport) -> Self {
        let mut warnings = vec![
            "quantization defines a categorical estimand and does not bypass high-dimensional cell sparsity".to_owned(),
        ];
        if value.out_of_range_policy == CoreOutOfRangePolicy::ClampToBoundary {
            warnings.push(
                "held-out values outside the fitted range are clamped to boundary bins by explicit policy".to_owned(),
            );
        }
        Self {
            bin_edges: value.bin_edges,
            training_data_hash_sha256: value.training_data_hash.map(hex_digest),
            transformed_data_hash_sha256: hex_digest(value.transformed_data_hash),
            out_of_range_policy: policy_name(value.out_of_range_policy).to_owned(),
            preprocessing_description: value.scaling_description,
            n_rows: value.n_samples,
            n_features: value.dimensions,
            num_bins: value.bins_per_dimension,
            nominal_joint_cardinality: value.nominal_joint_cardinality,
            observed_joint_cardinality: value.observed_joint_cardinality,
            empty_joint_cells: value.empty_joint_cells,
            low_count_joint_cells: value.low_count_joint_cells,
            minimum_observed_cell_count: value.minimum_observed_cell_count,
            maximum_observed_cell_count: value.maximum_observed_cell_count,
            estimand: value.estimand_statement.to_owned(),
            warnings,
        }
    }
}

fn nested_f64_tuple(py: Python<'_>, rows: &[Vec<f64>]) -> PyResult<Py<PyTuple>> {
    let mut tuples = Vec::new();
    tuples
        .try_reserve_exact(rows.len())
        .map_err(|_| resource_error(py, "allocation_failed", "tuple allocation failed", []))?;
    for row in rows {
        tuples.push(PyTuple::new(py, row.iter().copied())?.unbind());
    }
    Ok(PyTuple::new(py, tuples)?.unbind())
}

#[pyclass(name = "QuantizedData", frozen, module = "pid_core_rs")]
struct PyQuantizedData {
    values: Py<PyArray2<i64>>,
    report: Py<PyQuantizationReport>,
}

#[pymethods]
impl PyQuantizedData {
    #[getter]
    fn values(&self, py: Python<'_>) -> Py<PyArray2<i64>> {
        self.values.clone_ref(py)
    }

    #[getter]
    fn report(&self, py: Python<'_>) -> Py<PyQuantizationReport> {
        self.report.clone_ref(py)
    }
}

#[pyclass(
    name = "EqualWidthQuantizer",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug, Clone)]
struct PyEqualWidthQuantizer {
    inner: Arc<CoreEqualWidthQuantizer>,
}

#[pymethods]
impl PyEqualWidthQuantizer {
    #[staticmethod]
    #[pyo3(signature = (
        training_data,
        num_bins,
        *,
        preprocessing_description,
        out_of_range_policy="error",
        low_count_threshold=5,
        record_training_data_hash=true,
        budget=None
    ))]
    #[allow(clippy::too_many_arguments)]
    fn fit(
        py: Python<'_>,
        training_data: PyReadonlyArray2<'_, f64>,
        num_bins: usize,
        preprocessing_description: &str,
        out_of_range_policy: &str,
        low_count_threshold: usize,
        record_training_data_hash: bool,
        budget: Option<PyRef<'_, PyResourceBudget>>,
    ) -> PyResult<Self> {
        if !(2..=i64::MAX as usize).contains(&num_bins) {
            return Err(input_error(
                py,
                "invalid_bin_count",
                "num_bins must be between 2 and i64::MAX",
                [("num_bins".to_owned(), num_bins.to_string())],
            ));
        }
        let policy = match out_of_range_policy {
            "error" => CoreOutOfRangePolicy::Error,
            "clamp_to_boundary" | "clip" => CoreOutOfRangePolicy::ClampToBoundary,
            _ => {
                return Err(input_error(
                    py,
                    "invalid_out_of_range_policy",
                    "out_of_range_policy must be 'error' or 'clamp_to_boundary'",
                    [(
                        "accepted_values".to_owned(),
                        "error,clamp_to_boundary".to_owned(),
                    )],
                ));
            }
        };
        let budget = effective_budget(budget.as_deref());
        let training_elements = array_element_count(py, &training_data, "EqualWidthQuantizer.fit")?;
        let training_columns = training_data.as_array().shape()[1];
        let (_, retained_input_bytes) = preflight_aggregate_copies(
            py,
            "EqualWidthQuantizer.fit",
            &budget,
            &[training_elements],
            size_of::<f64>(),
        )?;
        let retained_config_and_input_bytes = retained_input_bytes
            .checked_add(preprocessing_description.len() as u128)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    "EqualWidthQuantizer.fit: aggregate retained-byte estimate overflow",
                    [],
                )
            })?;
        budget.check_wrapper_peak_bytes(
            py,
            "EqualWidthQuantizer.fit",
            retained_config_and_input_bytes,
        )?;
        let edges_per_column = num_bins.checked_add(1).ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "EqualWidthQuantizer.fit: edge-count estimate overflow",
                [],
            )
        })?;
        let edge_count = training_columns
            .checked_mul(edges_per_column)
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    "EqualWidthQuantizer.fit: edge-count estimate overflow",
                    [],
                )
            })?;
        let edge_bytes =
            allocation_bytes(py, "EqualWidthQuantizer.fit", edge_count, size_of::<f64>())?;
        let edge_vector_bytes = allocation_bytes(
            py,
            "EqualWidthQuantizer.fit",
            training_columns,
            size_of::<Vec<f64>>(),
        )?;
        let aggregate_fit_bytes = retained_config_and_input_bytes
            .checked_add(edge_bytes)
            .and_then(|value| value.checked_add(edge_vector_bytes))
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    "EqualWidthQuantizer.fit: aggregate byte estimate overflow",
                    [],
                )
            })?;
        let aggregate_fit_operations = (training_elements as u128)
            .checked_mul(3)
            .and_then(|value| value.checked_add(edge_count as u128))
            .and_then(|value| value.checked_add(preprocessing_description.len() as u128))
            .ok_or_else(|| {
                resource_error(
                    py,
                    "resource_estimate_overflow",
                    "EqualWidthQuantizer.fit: aggregate operation estimate overflow",
                    [],
                )
            })?;
        budget.check_limit(
            py,
            "EqualWidthQuantizer.fit",
            "bytes",
            aggregate_fit_bytes,
            u128::from(budget.max_bytes),
        )?;
        budget.check_limit(
            py,
            "EqualWidthQuantizer.fit",
            "operations_hint",
            aggregate_fit_operations,
            budget.max_operations_hint,
        )?;
        let config = CoreQuantizerConfig::new(
            policy,
            record_training_data_hash,
            low_count_threshold,
            preprocessing_description,
            budget.as_core(),
        )
        .map_err(|error| core_error(py, error))?;
        let training = copy_f64_matrix(py, &training_data, "EqualWidthQuantizer.fit", &budget)?;
        let fit_estimate = CoreEqualWidthQuantizer::fit_resource_estimate(
            training.as_ref().map_err(|error| core_error(py, error))?,
            num_bins,
        )
        .map_err(|error| core_error(py, error))?;
        budget.check_estimate_with_retained(
            py,
            "EqualWidthQuantizer.fit",
            retained_config_and_input_bytes,
            (training_elements as u128)
                .checked_add(preprocessing_description.len() as u128)
                .ok_or_else(|| {
                    resource_error(
                        py,
                        "resource_estimate_overflow",
                        "EqualWidthQuantizer.fit: wrapper operation estimate overflow",
                        [],
                    )
                })?,
            fit_estimate,
        )?;
        let result = run_owned_worker_with_signal_cancellation(
            py,
            "EqualWidthQuantizer.fit",
            move |cancellation| {
                CoreEqualWidthQuantizer::fit_with_cancellation(
                    training.as_ref()?,
                    num_bins,
                    config,
                    cancellation,
                )
            },
        )?;
        Ok(Self {
            inner: Arc::new(result),
        })
    }

    #[getter]
    fn num_bins(&self) -> usize {
        self.inner.bins()
    }

    #[getter]
    fn n_features(&self) -> usize {
        self.inner.edges().len()
    }

    #[getter]
    fn training_data_hash_sha256(&self) -> Option<String> {
        self.inner.training_data_hash().map(hex_digest)
    }

    #[getter]
    fn preprocessing_description(&self) -> &str {
        self.inner.config().scaling_description()
    }

    #[getter]
    fn out_of_range_policy(&self) -> &'static str {
        policy_name(self.inner.config().out_of_range_policy())
    }

    #[getter]
    fn resource_budget(&self) -> PyResourceBudget {
        self.inner.config().resource_budget().into()
    }

    #[getter]
    fn edges(&self, py: Python<'_>) -> PyResult<Py<PyTuple>> {
        nested_f64_tuple(py, self.inner.edges())
    }

    #[pyo3(signature = (data, *, budget=None))]
    fn transform(
        &self,
        py: Python<'_>,
        data: PyReadonlyArray2<'_, f64>,
        budget: Option<PyRef<'_, PyResourceBudget>>,
    ) -> PyResult<PyQuantizedData> {
        let budget = effective_budget(budget.as_deref());
        let input_elements = array_element_count(py, &data, "EqualWidthQuantizer.transform")?;
        let (_, retained_input_bytes) = preflight_aggregate_copies(
            py,
            "EqualWidthQuantizer.transform",
            &budget,
            &[input_elements],
            size_of::<f64>(),
        )?;
        let output_bytes = allocation_bytes(
            py,
            "EqualWidthQuantizer.transform.output",
            input_elements,
            size_of::<i64>(),
        )?;
        let retained_and_output_bytes =
            retained_input_bytes
                .checked_add(output_bytes)
                .ok_or_else(|| {
                    resource_error(
                        py,
                        "resource_estimate_overflow",
                        "EqualWidthQuantizer.transform: aggregate byte estimate overflow",
                        [],
                    )
                })?;
        budget.check_wrapper_peak_bytes(
            py,
            "EqualWidthQuantizer.transform",
            retained_and_output_bytes,
        )?;
        let wrapper_operations = (input_elements as u128).checked_mul(2).ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "EqualWidthQuantizer.transform: wrapper operation estimate overflow",
                [],
            )
        })?;
        let data = copy_f64_matrix(py, &data, "EqualWidthQuantizer.transform", &budget)?;
        let transform_estimate = self
            .inner
            .transform_resource_estimate(data.as_ref().map_err(|error| core_error(py, error))?)
            .map_err(|error| core_error(py, error))?;
        budget.check_estimate_with_retained(
            py,
            "EqualWidthQuantizer.transform",
            retained_and_output_bytes,
            wrapper_operations,
            transform_estimate,
        )?;
        let nrows = data.nrows;
        let ncols = data.ncols;
        let quantizer = self.inner.clone();
        let result = run_owned_worker_with_signal_cancellation(
            py,
            "EqualWidthQuantizer.transform",
            move |cancellation| {
                let output = quantizer
                    .transform_with_report_with_cancellation(data.as_ref()?, cancellation)?;
                let mut labels = Vec::new();
                labels
                    .try_reserve_exact(output.matrix.data().len())
                    .map_err(|_| CorePidError::AllocationFailed {
                        operation: "EqualWidthQuantizer.transform",
                        requested_bytes: (output.matrix.data().len() as u128)
                            * size_of::<i64>() as u128,
                    })?;
                for (index, &value) in output.matrix.data().iter().enumerate() {
                    if index.is_multiple_of(1024) {
                        check_wrapper_cancellation(
                            cancellation,
                            "EqualWidthQuantizer.transform",
                            index,
                            output.matrix.data().len(),
                        )?;
                    }
                    labels.push(value as i64);
                }
                Ok::<_, CorePidError>((labels, output.report))
            },
        )?;
        let (labels, report) = result;
        let values = Array2::from_shape_vec((nrows, ncols), labels).map_err(|error| {
            numerical_error(
                py,
                "output_shape_error",
                format!("could not shape quantized output: {error}"),
                [],
            )
        })?;
        Ok(PyQuantizedData {
            values: values.into_pyarray(py).unbind(),
            report: Py::new(py, PyQuantizationReport::from(report))?,
        })
    }
}

#[pyclass(
    name = "QuantizedSxPid2Result",
    frozen,
    skip_from_py_object,
    module = "pid_core_rs"
)]
#[derive(Debug)]
struct PyQuantizedSxPid2Result {
    pid: Py<PySxPid2Result>,
    source1_quantization: Py<PyQuantizationReport>,
    source2_quantization: Py<PyQuantizationReport>,
    target_quantization: Py<PyQuantizationReport>,
}

#[pymethods]
impl PyQuantizedSxPid2Result {
    #[getter]
    fn pid(&self, py: Python<'_>) -> Py<PySxPid2Result> {
        self.pid.clone_ref(py)
    }

    #[getter]
    fn source1_quantization(&self, py: Python<'_>) -> Py<PyQuantizationReport> {
        self.source1_quantization.clone_ref(py)
    }

    #[getter]
    fn source2_quantization(&self, py: Python<'_>) -> Py<PyQuantizationReport> {
        self.source2_quantization.clone_ref(py)
    }

    #[getter]
    fn target_quantization(&self, py: Python<'_>) -> Py<PyQuantizationReport> {
        self.target_quantization.clone_ref(py)
    }
}

#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (
    s1,
    s2,
    target,
    s1_quantizer,
    s2_quantizer,
    target_quantizer,
    *,
    budget=None
))]
fn compute_fitted_quantized_sxpid2(
    py: Python<'_>,
    s1: PyReadonlyArray2<'_, f64>,
    s2: PyReadonlyArray2<'_, f64>,
    target: PyReadonlyArray2<'_, f64>,
    s1_quantizer: PyRef<'_, PyEqualWidthQuantizer>,
    s2_quantizer: PyRef<'_, PyEqualWidthQuantizer>,
    target_quantizer: PyRef<'_, PyEqualWidthQuantizer>,
    budget: Option<PyRef<'_, PyResourceBudget>>,
) -> PyResult<PyQuantizedSxPid2Result> {
    let budget = effective_budget(budget.as_deref());
    let lengths = [
        array_element_count(py, &s1, "compute_fitted_quantized_sxpid2.s1")?,
        array_element_count(py, &s2, "compute_fitted_quantized_sxpid2.s2")?,
        array_element_count(py, &target, "compute_fitted_quantized_sxpid2.target")?,
    ];
    let (input_elements, retained_input_bytes) = preflight_aggregate_copies(
        py,
        "compute_fitted_quantized_sxpid2",
        &budget,
        &lengths,
        size_of::<f64>(),
    )?;
    let quantized_label_bytes = allocation_bytes(
        py,
        "compute_fitted_quantized_sxpid2",
        input_elements,
        size_of::<usize>(),
    )?;
    let minimum_transform_peak = retained_input_bytes
        .checked_add(quantized_label_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_fitted_quantized_sxpid2: minimum transform-byte estimate overflow",
                [],
            )
        })?;
    budget.check_wrapper_peak_bytes(
        py,
        "compute_fitted_quantized_sxpid2",
        minimum_transform_peak,
    )?;
    let s1 = copy_f64_matrix(py, &s1, "compute_fitted_quantized_sxpid2.s1", &budget)?;
    let s2 = copy_f64_matrix(py, &s2, "compute_fitted_quantized_sxpid2.s2", &budget)?;
    let target = copy_f64_matrix(
        py,
        &target,
        "compute_fitted_quantized_sxpid2.target",
        &budget,
    )?;
    validate_aligned_rows(
        py,
        "compute_fitted_quantized_sxpid2",
        &[s1.nrows, s2.nrows, target.nrows],
    )?;
    let source1_quantizer = s1_quantizer.inner.clone();
    let source2_quantizer = s2_quantizer.inner.clone();
    let target_quantizer = target_quantizer.inner.clone();
    let transform_estimates = [
        source1_quantizer
            .transform_resource_estimate(s1.as_ref().map_err(|error| core_error(py, error))?)
            .map_err(|error| core_error(py, error))?,
        source2_quantizer
            .transform_resource_estimate(s2.as_ref().map_err(|error| core_error(py, error))?)
            .map_err(|error| core_error(py, error))?,
        target_quantizer
            .transform_resource_estimate(target.as_ref().map_err(|error| core_error(py, error))?)
            .map_err(|error| core_error(py, error))?,
    ];
    let (transform_bytes, transform_pairwise, transform_operations) = transform_estimates
        .iter()
        .try_fold(
            (0u128, 0u128, 0u128),
            |(bytes, pairwise, operations), estimate| {
                Some((
                    bytes.checked_add(estimate.estimated_bytes)?,
                    pairwise.checked_add(estimate.pairwise_distances)?,
                    operations.checked_add(estimate.operations_hint)?,
                ))
            },
        )
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_fitted_quantized_sxpid2: transform resource estimate overflow",
                [],
            )
        })?;
    let transform_peak_bytes = retained_input_bytes
        .checked_add(transform_bytes)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_fitted_quantized_sxpid2: transform byte estimate overflow",
                [],
            )
        })?;
    let wrapper_operations = (input_elements as u128)
        .checked_add(transform_operations)
        .ok_or_else(|| {
            resource_error(
                py,
                "resource_estimate_overflow",
                "compute_fitted_quantized_sxpid2: transform operation estimate overflow",
                [],
            )
        })?;
    budget.check_limit(
        py,
        "compute_fitted_quantized_sxpid2",
        "bytes",
        transform_peak_bytes,
        u128::from(budget.max_bytes),
    )?;
    budget.check_limit(
        py,
        "compute_fitted_quantized_sxpid2",
        "pairwise_distances",
        transform_pairwise,
        u128::from(budget.max_pairwise_distances),
    )?;
    let core_budget = budget.core_after_wrapper_cost(
        py,
        "compute_fitted_quantized_sxpid2",
        transform_bytes,
        wrapper_operations,
    )?;
    let result = run_owned_worker_with_signal_cancellation(
        py,
        "compute_fitted_quantized_sxpid2",
        move |cancellation| {
            let source1_quantized = source1_quantizer
                .transform_with_report_with_cancellation(s1.as_ref()?, cancellation)?;
            let source2_quantized = source2_quantizer
                .transform_with_report_with_cancellation(s2.as_ref()?, cancellation)?;
            let target_quantized = target_quantizer
                .transform_with_report_with_cancellation(target.as_ref()?, cancellation)?;
            drop(s1);
            drop(s2);
            drop(target);
            fitted_quantized_sxpid2_with_budget_and_cancellation(
                &source1_quantized,
                &source2_quantized,
                &target_quantized,
                core_budget,
                cancellation,
            )
        },
    )?;
    let [source1_quantization, source2_quantization] = result.source_quantization;
    let target_quantization = result.target_quantization;
    let mut pid = PySxPid2Result::from(result.pid);
    pid.input_encoding = "fitted_equal_width".to_owned();
    pid.status = "quantized_estimand".to_owned();
    pid.warnings.push(
        "fixed bin edges were fitted separately and are preserved in the quantization reports"
            .to_owned(),
    );
    Ok(PyQuantizedSxPid2Result {
        pid: Py::new(py, pid)?,
        source1_quantization: Py::new(py, PyQuantizationReport::from(source1_quantization))?,
        source2_quantization: Py::new(py, PyQuantizationReport::from(source2_quantization))?,
        target_quantization: Py::new(py, PyQuantizationReport::from(target_quantization))?,
    })
}

fn register_result_classes(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_class::<PyResourceBudget>()?;
    module.add_class::<PyResourceEstimate>()?;
    module.add_class::<PyDistanceQuantiles>()?;
    module.add_class::<PyNeighborShellDiagnostics>()?;
    module.add_class::<PyCoordinateCardinality>()?;
    module.add_class::<PyContinuousInputReport>()?;
    module.add_class::<PyDistanceConcentrationReport>()?;
    module.add_class::<PyIntrinsicDimensionReport>()?;
    module.add_class::<PyValueQuantiles>()?;
    module.add_class::<PyCountQuantiles>()?;
    module.add_class::<PyKsgLocalDiagnostics>()?;
    module.add_class::<PyAssumptionLedgerEntry>()?;
    module.add_class::<PyEstimandIdentity>()?;
    module.add_class::<PyProvenance>()?;
    module.add_class::<PyMiReport>()?;
    module.add_class::<PySxAtom>()?;
    module.add_class::<PyEmpiricalPmfDiagnostics>()?;
    module.add_class::<PySxPid2Result>()?;
    module.add_class::<PyAntichain>()?;
    module.add_class::<PyAntichainAtom>()?;
    module.add_class::<PySxPidLatticeResult>()?;
    module.add_class::<PyIminPid2Result>()?;
    module.add_class::<PyQuantizationReport>()?;
    module.add_class::<PyQuantizedData>()?;
    module.add_class::<PyEqualWidthQuantizer>()?;
    module.add_class::<PyQuantizedSxPid2Result>()?;
    Ok(())
}

fn register_stable_functions(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(compute_mi_report, module)?)?;
    module.add_function(wrap_pyfunction!(compute_categorical_sxpid2, module)?)?;
    module.add_function(wrap_pyfunction!(compute_categorical_sxpid3, module)?)?;
    module.add_function(wrap_pyfunction!(compute_categorical_sxpid, module)?)?;
    module.add_function(wrap_pyfunction!(compute_categorical_imin_pid2, module)?)?;
    module.add_function(wrap_pyfunction!(compute_fitted_quantized_sxpid2, module)?)?;
    Ok(())
}

fn register_diagnostic_functions(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(diagnose_continuous_input, module)?)?;
    module.add_function(wrap_pyfunction!(distance_concentration_report, module)?)?;
    module.add_function(wrap_pyfunction!(intrinsic_dimension_report, module)?)?;
    Ok(())
}

#[pymodule]
fn pid_core_rs(py: Python<'_>, module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add("__version__", env!("CARGO_PKG_VERSION"))?;
    module.add(
        "SCIENTIFIC_SCOPE",
        "stable empirical categorical and fitted-quantized PID; conditional report-first KSG",
    )?;
    module.add("PidRsError", py.get_type::<PidRsError>())?;
    module.add("PidInputError", py.get_type::<PidInputError>())?;
    module.add("PidResourceError", py.get_type::<PidResourceError>())?;
    module.add("PidNumericalError", py.get_type::<PidNumericalError>())?;
    module.add("PidUnsupportedError", py.get_type::<PidUnsupportedError>())?;
    module.add("PidCancelledError", py.get_type::<PidCancelledError>())?;
    register_result_classes(module)?;
    register_stable_functions(module)?;
    register_diagnostic_functions(module)?;

    let stable = PyModule::new(py, "pid_core_rs.stable")?;
    register_result_classes(&stable)?;
    register_stable_functions(&stable)?;
    module.add_submodule(&stable)?;

    let diagnostics = PyModule::new(py, "pid_core_rs.diagnostics")?;
    diagnostics.add_class::<PyResourceBudget>()?;
    diagnostics.add_class::<PyResourceEstimate>()?;
    diagnostics.add_class::<PyDistanceQuantiles>()?;
    diagnostics.add_class::<PyNeighborShellDiagnostics>()?;
    diagnostics.add_class::<PyCoordinateCardinality>()?;
    diagnostics.add_class::<PyContinuousInputReport>()?;
    diagnostics.add_class::<PyDistanceConcentrationReport>()?;
    diagnostics.add_class::<PyIntrinsicDimensionReport>()?;
    register_diagnostic_functions(&diagnostics)?;
    module.add_submodule(&diagnostics)?;

    let modules = py.import("sys")?.getattr("modules")?;
    modules.set_item("pid_core_rs.stable", &stable)?;
    modules.set_item("pid_core_rs.diagnostics", &diagnostics)?;

    #[cfg(feature = "python-experimental")]
    {
        let experimental = PyModule::new(py, "pid_core_rs.experimental")?;
        let migration = PyModule::new(py, "pid_core_rs.experimental.migration")?;
        legacy::register_legacy(py, &migration)?;
        experimental.add_submodule(&migration)?;
        module.add_submodule(&experimental)?;
        modules.set_item("pid_core_rs.experimental", &experimental)?;
        modules.set_item("pid_core_rs.experimental.migration", &migration)?;
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn core_cancelled_error_maps_to_typed_python_fields() {
        Python::initialize();
        Python::attach(|py| {
            let error = core_error(
                py,
                CorePidError::Cancelled {
                    operation: "test operation",
                    completed_units: 3,
                    total_units: 11,
                },
            );
            assert!(error.is_instance_of::<PidCancelledError>(py));
            let value = error.value(py);
            assert_eq!(
                value
                    .getattr("code")
                    .expect("structured error must expose code")
                    .extract::<String>()
                    .expect("code must be a string"),
                "cancelled"
            );
            let fields = value
                .getattr("fields")
                .expect("structured error must expose fields")
                .cast_into::<PyDict>()
                .expect("fields must be a dictionary");
            for (field, expected) in [
                ("operation", "test operation"),
                ("completed_units", "3"),
                ("total_units", "11"),
            ] {
                assert_eq!(
                    fields
                        .get_item(field)
                        .expect("field lookup must succeed")
                        .expect("field must be present")
                        .extract::<String>()
                        .expect("field must be a string"),
                    expected
                );
            }
        });
    }
}
