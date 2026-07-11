use numpy::{PyReadonlyArray2, PyUntypedArrayMethods};
use pid_core::{
    average_degree_of_redundancy, average_degree_of_vulnerability, co_information_pairwise,
    continuous_input_diagnostics as core_continuous_input_diagnostics, discrete_pid2,
    discrete_pid3, discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n,
    distance_concentration_stats, intrinsic_dimension_levina_bickel, isx_redundancy, ksg_mi,
    ksg_mi_concat_xy, ksg_mi_report, pid2_isx, pid2_isx_report, pid3_isx_partial_report,
    pid3_isx_report, quantized_sxpid2, quantized_sxpid3, quantized_sxpid_n,
    sampled_four_point_delta_summary as core_four_point_delta_summary, ContinuousInputDiagnostics,
    DiscreteMatRef, DistanceConcentrationConfig, HashProjector, HyperbolicityConfig,
    IntrinsicDimConfig, IsxConfig, IsxMethod, KsgConfig, KsgGeometryModel, KsgMethodStatus,
    KsgProvenance, KsgReportWarning, MatRef, Metric, NegativeHandling, NeighborShellDiagnostics,
    PcaProjector, Pid2Config, Pid2MethodStatus, Pid2Provenance, Pid2ReportWarning, Pid3Config,
    Pid3MethodStatus, Pid3Provenance, PlsProjector as CorePlsProjector, Standardizer,
    SupportContract,
};
use pyo3::prelude::*;
use pyo3::types::PyDict;
use std::collections::BTreeMap;

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
    if !arr.is_c_contiguous() {
        return Err(pyo3::exceptions::PyValueError::new_err(
            "Categorical array must be C-contiguous; wrap it in np.ascontiguousarray(x)",
        ));
    }
    let slice = arr.as_slice().map_err(|_| {
        pyo3::exceptions::PyValueError::new_err("Categorical array must be C-contiguous")
    })?;
    let view = arr.as_array();
    let (nrows, ncols) = (view.shape()[0], view.shape()[1]);
    let mut codebook = BTreeMap::<i64, usize>::new();
    let mut labels = Vec::with_capacity(slice.len());
    for &label in slice {
        let next = codebook.len();
        let code = *codebook.entry(label).or_insert(next);
        labels.push(code);
    }
    Ok(OwnedDiscreteMatrix {
        labels,
        nrows,
        ncols,
    })
}

fn parse_metric(name: &str) -> PyResult<Metric> {
    match name.to_lowercase().as_str() {
        "chebyshev" | "linf" | "max" => Ok(Metric::Chebyshev),
        // Experimental research metrics (MI-only, not validated for ISX):
        "hyperbolic" | "hyperbolic_lorentz" | "lorentz" => Ok(Metric::HyperbolicLorentz),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown metric: '{}'. Valid metrics are: 'chebyshev' (aliases: 'linf', 'max'), \
             'hyperbolic_lorentz' (aliases: 'hyperbolic', 'lorentz', experimental MI-only)",
            name
        ))),
    }
}

fn parse_negative_handling(name: &str) -> PyResult<NegativeHandling> {
    match name.to_lowercase().as_str() {
        "allow" | "raw" | "none" => Ok(NegativeHandling::Allow),
        "clamp_to_zero" | "clamp" | "zero" => Ok(NegativeHandling::ClampToZero),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown negative_handling: '{}'. Valid values are: 'allow', 'clamp_to_zero'",
            name
        ))),
    }
}

fn parse_support_contract(name: &str) -> PyResult<SupportContract> {
    match name.to_lowercase().as_str() {
        "unspecified" => Ok(SupportContract::Unspecified),
        "assume_absolutely_continuous" => Ok(SupportContract::AssumeAbsolutelyContinuous),
        "assume_smooth_manifold" => Ok(SupportContract::AssumeSmoothManifold),
        "atomic_or_mixed" => Ok(SupportContract::KnownAtomicOrMixed),
        "quantized" => Ok(SupportContract::KnownQuantized),
        "singular_or_lower_dimensional" => Ok(SupportContract::KnownSingularOrLowerDimensional),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown support_contract: '{}'. Valid values are: 'unspecified', \
             'assume_absolutely_continuous', 'assume_smooth_manifold', 'atomic_or_mixed', \
             'quantized', 'singular_or_lower_dimensional'",
            name
        ))),
    }
}

fn metric_name(metric: Metric) -> &'static str {
    match metric {
        Metric::Chebyshev => "chebyshev",
        Metric::HyperbolicLorentz => "hyperbolic_lorentz",
    }
}

fn negative_handling_name(handling: NegativeHandling) -> &'static str {
    match handling {
        NegativeHandling::Allow => "allow",
        NegativeHandling::ClampToZero => "clamp_to_zero",
    }
}

fn support_contract_name(contract: SupportContract) -> &'static str {
    match contract {
        SupportContract::Unspecified => "unspecified",
        SupportContract::AssumeAbsolutelyContinuous => "assume_absolutely_continuous",
        SupportContract::AssumeSmoothManifold => "assume_smooth_manifold",
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
        KsgGeometryModel::LorentzHyperboloid => "lorentz_hyperboloid",
        _ => "unknown",
    }
}

fn ksg_warning_code(warning: KsgReportWarning) -> &'static str {
    match warning {
        KsgReportWarning::SampleDiagnosticsCannotProveSupport => {
            "sample_diagnostics_cannot_prove_support"
        }
        KsgReportWarning::MarginalNeighborShellPathology => "marginal_neighbor_shell_pathology",
        KsgReportWarning::HyperbolicConsistencyNotEstablished => {
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
    Ok(KsgConfig {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        negative_handling: parse_negative_handling(negative_handling)?,
        support_contract: parse_support_contract(support_contract)?,
    })
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
        | E::ObservedContinuousSampleIncompatibility { .. } => {
            pyo3::exceptions::PyValueError::new_err(msg)
        }
        // Estimator could not produce a result on otherwise-valid input → RuntimeError.
        E::NumericalInstability { .. } | E::AmbiguousKthNeighborShell { .. } => {
            pyo3::exceptions::PyRuntimeError::new_err(msg)
        }
        E::NotImplemented { .. } => pyo3::exceptions::PyNotImplementedError::new_err(msg),
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
    let cfg = make_ksg_config(k, metric, tie_epsilon, negative_handling, support_contract)?;
    match ksg_mi(x_mat, y_mat, &cfg) {
        Err(pid_core::PidError::InvalidConfig {
            context: "ksg_mi",
            message: "Metric::HyperbolicLorentz is available only through ksg_mi_report, which requires embedding-training provenance and preserves experimental status/warnings",
        }) => Err(pyo3::exceptions::PyValueError::new_err(
            "hyperbolic MI is available only through compute_mi_report, which requires \
             embedding_training_provenance and preserves experimental status and warnings",
        )),
        result => result.map_err(pid_err),
    }
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
    preprocessing_description: String,
    observation_model_description: String,
    embedding_training_provenance: Option<String>,
) -> PyResult<Py<PyAny>> {
    let x_mat = array_to_matref(&x)?;
    let y_mat = array_to_matref(&y)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, negative_handling, support_contract)?;
    let provenance = KsgProvenance::new(
        preprocessing_description,
        observation_model_description,
        embedding_training_provenance,
    )
    .map_err(pid_err)?;
    let report = ksg_mi_report(x_mat, y_mat, &cfg, &provenance).map_err(pid_err)?;

    let config = PyDict::new(py);
    config.set_item("n_samples", report.n_samples)?;
    config.set_item("k", report.k)?;
    config.set_item("metric", metric_name(report.metric))?;
    config.set_item(
        "negative_handling",
        negative_handling_name(report.negative_handling),
    )?;
    config.set_item(
        "support_contract",
        support_contract_name(report.support_contract),
    )?;

    let method = PyDict::new(py);
    method.set_item("status", ksg_method_status_name(report.method_status))?;
    method.set_item(
        "geometry_model",
        ksg_geometry_model_name(report.geometry_model),
    )?;
    method.set_item("curvature", report.curvature)?;
    method.set_item("x_hyperbolic_dimension", report.x_hyperbolic_dimension)?;
    method.set_item("y_hyperbolic_dimension", report.y_hyperbolic_dimension)?;

    let provenance = PyDict::new(py);
    provenance.set_item(
        "preprocessing_description",
        report.provenance.preprocessing_description(),
    )?;
    provenance.set_item(
        "observation_model_description",
        report.provenance.observation_model_description(),
    )?;
    provenance.set_item(
        "embedding_training_provenance",
        report.provenance.embedding_training_provenance(),
    )?;

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

    let diagnostics = PyDict::new(py);
    diagnostics.set_item(
        "x",
        continuous_input_diagnostics_output(py, &report.x_diagnostics)?,
    )?;
    diagnostics.set_item(
        "y",
        continuous_input_diagnostics_output(py, &report.y_diagnostics)?,
    )?;
    diagnostics.set_item(
        "joint_shells",
        neighbor_shell_diagnostics_output(py, report.joint_shells)?,
    )?;

    let output = PyDict::new(py);
    output.set_item("estimate_nats", report.estimate_nats)?;
    output.set_item("config", config)?;
    output.set_item("method", method)?;
    output.set_item("provenance", provenance)?;
    output.set_item("warnings", warnings)?;
    output.set_item("diagnostics", diagnostics)?;
    Ok(output.into_any().unbind())
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

/// Compute a two-source continuous PID metadata report.
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
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
) -> PyResult<Py<PyAny>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let target_mat = array_to_matref(&target)?;
    let cfg = Pid2Config {
        ksg: make_ksg_config(k, metric, tie_epsilon, "allow", support_contract)?,
        isx: make_isx_config(k, metric, tie_epsilon, method, support_contract)?,
    };
    let provenance = Pid2Provenance::new(
        source1_preprocessing_description,
        source2_preprocessing_description,
        target_preprocessing_description,
        observation_model_description,
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
        average_degree_of_redundancy(&[mi_s1_t, mi_s2_t], mi_s1s2_t),
    );
    map.insert(
        "v_bar".to_string(),
        average_degree_of_vulnerability(mi_s1s2_t, &[mi_s2_t, mi_s1_t]),
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
    let coordinates = diagnostics
        .coordinates
        .iter()
        .map(|coordinate| {
            BTreeMap::from([
                ("coordinate".to_string(), coordinate.coordinate),
                ("unique_values".to_string(), coordinate.unique_values),
                ("tied_groups".to_string(), coordinate.tied_groups),
                (
                    "repeated_observations".to_string(),
                    coordinate.repeated_observations,
                ),
                ("max_multiplicity".to_string(), coordinate.max_multiplicity),
            ])
        })
        .collect::<Vec<_>>();

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
    let diagnostics =
        core_continuous_input_diagnostics(array_to_matref(&x)?, k, parse_metric(metric)?)
            .map_err(pid_err)?;
    continuous_input_diagnostics_output(py, &diagnostics)
}

/// Estimate intrinsic dimension using Levina-Bickel (kNN MLE).
#[pyfunction]
#[pyo3(signature = (x, k=10, metric="chebyshev"))]
fn estimate_intrinsic_dimension(x: PyReadonlyArray2<f64>, k: usize, metric: &str) -> PyResult<f64> {
    let x_mat = array_to_matref(&x)?;
    let metric_enum = parse_metric(metric)?;

    let cfg = IntrinsicDimConfig {
        k,
        metric: metric_enum,
    };

    intrinsic_dimension_levina_bickel(x_mat, &cfg).map_err(pid_err)
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
    let metric_enum = parse_metric(metric)?;

    let cfg = HyperbolicityConfig {
        n_samples,
        metric: metric_enum,
        seed,
    };

    core_four_point_delta_summary(x_mat, &cfg)
        .map(|summary| summary.mean)
        .map_err(pid_err)
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
    let cfg = HyperbolicityConfig {
        n_samples,
        metric: parse_metric(metric)?,
        seed,
    };
    let summary = core_four_point_delta_summary(x_mat, &cfg).map_err(pid_err)?;

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
    let metric_enum = parse_metric(metric)?;

    let cfg = DistanceConcentrationConfig {
        metric: metric_enum,
    };

    let stats = distance_concentration_stats(x_mat, &cfg).map_err(pid_err)?;

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
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    source3_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
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
        source1_preprocessing_description,
        source2_preprocessing_description,
        source3_preprocessing_description,
        target_preprocessing_description,
        observation_model_description,
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
    output.set_item("experimental", out.experimental)?;
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
    source1_preprocessing_description: String,
    source2_preprocessing_description: String,
    source3_preprocessing_description: String,
    target_preprocessing_description: String,
    observation_model_description: String,
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
        source1_preprocessing_description,
        source2_preprocessing_description,
        source3_preprocessing_description,
        target_preprocessing_description,
        observation_model_description,
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

/// Compute discrete 2-source PID via quantization.
///
/// Useful as a fallback when continuous kNN-based estimation fails due to
/// distance concentration (high intrinsic dimension).
#[pyfunction]
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
    let out = discrete_pid2(s1_mat, s2_mat, t_mat, num_bins).map_err(pid_err)?;

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

/// Compute discrete 3-source PID via quantization (Williams–Beer `I_min` redundancy).
///
/// The discrete counterpart to `compute_pid3`. Note this is a **different PID
/// measure** from the continuous `I^sx_∩` (a different PID measure):
/// do not pool its atoms with continuous-mode atoms. Keys are the antichain set
/// indices of each atom on the 3-source lattice.
#[pyfunction]
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
    let out = discrete_pid3(s0_mat, s1_mat, s2_mat, t_mat, num_bins).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    for atom in &out.atoms {
        map.insert(format!("{:?}", atom.antichain_sets), atom.value);
    }
    Ok(map)
}

fn sxpid2_output(out: pid_core::DiscreteSxPid2Result) -> BTreeMap<String, f64> {
    let mut map = BTreeMap::new();
    for (name, a) in [
        ("redundancy", out.red),
        ("unique_s1", out.unq1),
        ("unique_s2", out.unq2),
        ("synergy", out.syn),
    ] {
        map.insert(name.to_string(), a.net);
        map.insert(format!("{name}_informative"), a.informative);
        map.insert(format!("{name}_misinformative"), a.misinformative);
    }
    map.insert("mi_s1_t".to_string(), out.mi_s1_t);
    map.insert("mi_s2_t".to_string(), out.mi_s2_t);
    map.insert("mi_s1s2_t".to_string(), out.mi_s1s2_t);
    map
}

fn sxpid_lattice_output(
    antichains: &[Vec<u8>],
    atoms: &[pid_core::SxAtom],
) -> BTreeMap<String, f64> {
    let mut map = BTreeMap::new();
    for (sets, atom) in antichains.iter().zip(atoms) {
        map.insert(format!("{sets:?}"), atom.net);
    }
    map
}

/// Compute exact categorical 2-source shared-exclusions PID (`i^sx_∩`).
///
/// Inputs must be C-contiguous NumPy `int64` matrices. Numeric spacing is ignored; only equality
/// of categorical rows matters. Returns averaged atoms in nats with informative/misinformative
/// splits. Use `compute_quantized_sxpid2` for continuous `float64` measurements.
#[pyfunction]
#[pyo3(signature = (s1, s2, target))]
fn compute_discrete_sxpid2(
    s1: PyReadonlyArray2<i64>,
    s2: PyReadonlyArray2<i64>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let s1 = array_to_discrete(&s1)?;
    let s2 = array_to_discrete(&s2)?;
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid2(s1.as_ref()?, s2.as_ref()?, target.as_ref()?).map_err(pid_err)?;
    Ok(sxpid2_output(out))
}

/// Equal-width-quantized 2-source shared-exclusions PID for continuous `float64` inputs.
#[pyfunction]
#[pyo3(signature = (s1, s2, target, num_bins=10))]
fn compute_quantized_sxpid2(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let out = quantized_sxpid2(
        array_to_matref(&s1)?,
        array_to_matref(&s2)?,
        array_to_matref(&target)?,
        num_bins,
    )
    .map_err(pid_err)?;
    Ok(sxpid2_output(out))
}

/// Compute exact categorical 3-source shared-exclusions PID over the 18-antichain lattice.
#[pyfunction]
#[pyo3(signature = (s0, s1, s2, target))]
fn compute_discrete_sxpid3(
    s0: PyReadonlyArray2<i64>,
    s1: PyReadonlyArray2<i64>,
    s2: PyReadonlyArray2<i64>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let s0 = array_to_discrete(&s0)?;
    let s1 = array_to_discrete(&s1)?;
    let s2 = array_to_discrete(&s2)?;
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid3(s0.as_ref()?, s1.as_ref()?, s2.as_ref()?, target.as_ref()?)
        .map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Equal-width-quantized 3-source shared-exclusions PID for continuous `float64` inputs.
#[pyfunction]
#[pyo3(signature = (s0, s1, s2, target, num_bins=10))]
fn compute_quantized_sxpid3(
    s0: PyReadonlyArray2<f64>,
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let out = quantized_sxpid3(
        array_to_matref(&s0)?,
        array_to_matref(&s1)?,
        array_to_matref(&s2)?,
        array_to_matref(&target)?,
        num_bins,
    )
    .map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Compute exact categorical shared-exclusions PID for two to four `int64` sources.
#[pyfunction]
#[pyo3(signature = (sources, target))]
fn compute_discrete_sxpid_n(
    sources: Vec<PyReadonlyArray2<i64>>,
    target: PyReadonlyArray2<i64>,
) -> PyResult<BTreeMap<String, f64>> {
    let owned_sources: Vec<OwnedDiscreteMatrix> = sources
        .iter()
        .map(array_to_discrete)
        .collect::<PyResult<_>>()?;
    let source_refs: Vec<DiscreteMatRef<'_>> = owned_sources
        .iter()
        .map(OwnedDiscreteMatrix::as_ref)
        .collect::<PyResult<_>>()?;
    let target = array_to_discrete(&target)?;
    let out = discrete_sxpid_n(&source_refs, target.as_ref()?).map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

/// Equal-width-quantized shared-exclusions PID for two to four continuous sources.
#[pyfunction]
#[pyo3(signature = (sources, target, num_bins=10))]
fn compute_quantized_sxpid_n(
    sources: Vec<PyReadonlyArray2<f64>>,
    target: PyReadonlyArray2<f64>,
    num_bins: usize,
) -> PyResult<BTreeMap<String, f64>> {
    let source_refs: Vec<MatRef<'_>> = sources
        .iter()
        .map(array_to_matref)
        .collect::<PyResult<_>>()?;
    let out =
        quantized_sxpid_n(&source_refs, array_to_matref(&target)?, num_bins).map_err(pid_err)?;
    Ok(sxpid_lattice_output(&out.antichains, &out.atoms))
}

fn matrix_output(
    py: Python<'_>,
    projected: pid_core::MatOwned,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let ref_view = projected.as_ref();
    let n = ref_view.nrows();
    let d = ref_view.ncols();
    let mut flat = Vec::with_capacity(n * d);
    for i in 0..n {
        flat.extend_from_slice(ref_view.row(i));
    }

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
        let projected = self
            .inner
            .transform(array_to_matref(&x)?)
            .map_err(pid_err)?;
        matrix_output(py, projected)
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
    let (projected, _pls) =
        CorePlsProjector::fit_transform(x_mat, y_mat, out_dim).map_err(pid_err)?;
    matrix_output(py, projected)
}

/// Standardize a matrix (zero mean, unit variance per column).
#[pyfunction]
#[pyo3(signature = (x))]
fn standardize(py: Python<'_>, x: PyReadonlyArray2<f64>) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    let (projected, _std) = Standardizer::fit_transform(x_mat).map_err(pid_err)?;

    let ref_view = projected.as_ref();
    let n = ref_view.nrows();
    let d = ref_view.ncols();
    let mut flat = Vec::with_capacity(n * d);
    for i in 0..n {
        flat.extend_from_slice(ref_view.row(i));
    }

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

/// PCA dimensionality reduction.
#[pyfunction]
#[pyo3(signature = (x, out_dim))]
fn pca_transform(
    py: Python<'_>,
    x: PyReadonlyArray2<f64>,
    out_dim: usize,
) -> PyResult<BTreeMap<String, Py<PyAny>>> {
    let x_mat = array_to_matref(&x)?;
    let (projected, _pca) = PcaProjector::fit_transform(x_mat, out_dim).map_err(pid_err)?;

    let ref_view = projected.as_ref();
    let n = ref_view.nrows();
    let d = ref_view.ncols();
    let mut flat = Vec::with_capacity(n * d);
    for i in 0..n {
        flat.extend_from_slice(ref_view.row(i));
    }

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
    let proj = HashProjector::new(x_mat.ncols(), out_dim, seed).map_err(pid_err)?;
    let projected = proj.transform(x_mat).map_err(pid_err)?;

    let ref_view = projected.as_ref();
    let n = ref_view.nrows();
    let d = ref_view.ncols();
    let mut flat = Vec::with_capacity(n * d);
    for i in 0..n {
        flat.extend_from_slice(ref_view.row(i));
    }

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

#[pymodule]
fn pid_core_rs(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
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
