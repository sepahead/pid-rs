use numpy::{PyReadonlyArray2, PyUntypedArrayMethods};
use pid_core::{
    average_degree_of_redundancy, average_degree_of_vulnerability, co_information_pairwise,
    discrete_pid2, discrete_pid3, discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n,
    distance_concentration_stats, gromov_hyperbolicity, intrinsic_dimension_levina_bickel,
    isx_redundancy, ksg_mi, ksg_mi_concat_xy, pid2_isx, pid3_isx, quantized_sxpid2,
    quantized_sxpid3, quantized_sxpid_n, DiscreteMatRef, DistanceConcentrationConfig,
    HashProjector, HyperbolicityConfig, IntrinsicDimConfig, IsxConfig, IsxMethod, KsgConfig,
    MatRef, Metric, NegativeHandling, PcaProjector, Pid2Config, Pid3Config, PlsProjector,
    Standardizer,
};
use pyo3::prelude::*;
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
        "hyperbolic" | "lorentz" => Ok(Metric::HyperbolicLorentz),
        _ => Err(pyo3::exceptions::PyValueError::new_err(format!(
            "Unknown metric: '{}'. Valid metrics are: 'chebyshev' (aliases: 'linf', 'max'), \
             'hyperbolic' (alias: 'lorentz', experimental MI-only)",
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
) -> PyResult<KsgConfig> {
    Ok(KsgConfig {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        negative_handling: parse_negative_handling(negative_handling)?,
    })
}

fn make_isx_config(k: usize, metric: &str, tie_epsilon: f64, method: &str) -> PyResult<IsxConfig> {
    Ok(IsxConfig {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
        method: parse_isx_method(method)?,
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
        | E::InvalidK { .. }
        | E::NonFiniteInput { .. } => pyo3::exceptions::PyValueError::new_err(msg),
        // Estimator could not produce a result on otherwise-valid input → RuntimeError.
        E::NumericalInstability { .. } => pyo3::exceptions::PyRuntimeError::new_err(msg),
        E::NotImplemented { .. } => pyo3::exceptions::PyNotImplementedError::new_err(msg),
    }
}

/// Compute KSG Mutual Information.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
#[pyo3(signature = (x, y, k=3, metric="chebyshev", tie_epsilon=0.0, negative_handling="clamp_to_zero"))]
fn compute_mi(
    x: PyReadonlyArray2<f64>,
    y: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
    negative_handling: &str,
) -> PyResult<f64> {
    let x_mat = array_to_matref(&x)?;
    let y_mat = array_to_matref(&y)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, negative_handling)?;

    ksg_mi(x_mat, y_mat, &cfg).map_err(pid_err)
}

/// Compute continuous I_sx_intersect redundancy.
#[pyfunction]
#[pyo3(signature = (s1, s2, target, k=3, method="ehrlich_ksg", metric="chebyshev", tie_epsilon=0.0))]
fn compute_redundancy(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    method: &str,
    metric: &str,
    tie_epsilon: f64,
) -> PyResult<f64> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_isx_config(k, metric, tie_epsilon, method)?;

    isx_redundancy(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)
}

/// Co-information I(S1;T) + I(S2;T) - I(S1,S2;T), in nats.
///
/// The MI terms are always computed unclamped (the core forces `NegativeHandling::Allow`):
/// clamping a term before the subtraction would silently break the identity. There is
/// deliberately no `negative_handling` parameter here — it would be a no-op.
#[pyfunction]
#[pyo3(signature = (s1, s2, target, k=3, metric="chebyshev", tie_epsilon=0.0))]
fn compute_co_information(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
) -> PyResult<f64> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, "allow")?;

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
#[pyo3(signature = (s1, s2, target, k=3, method="ehrlich_ksg", metric="chebyshev", tie_epsilon=0.0))]
fn compute_pid2(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    method: &str,
    metric: &str,
    tie_epsilon: f64,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = Pid2Config {
        ksg: make_ksg_config(k, metric, tie_epsilon, "allow")?,
        isx: make_isx_config(k, metric, tie_epsilon, method)?,
    };
    let out = pid2_isx(s1_mat, s2_mat, t_mat, &cfg).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert("redundancy".to_string(), out.redundancy);
    map.insert("unique_s1".to_string(), out.unique_s1);
    map.insert("unique_s2".to_string(), out.unique_s2);
    map.insert("synergy".to_string(), out.synergy);
    Ok(map)
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
#[pyo3(signature = (s1, s2, target, k=3, metric="chebyshev", tie_epsilon=0.0))]
fn compute_invariants(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = make_ksg_config(k, metric, tie_epsilon, "allow")?;
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

/// Estimate Gromov delta-hyperbolicity via 4-point sampling.
#[pyfunction]
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

    gromov_hyperbolicity(x_mat, &cfg).map_err(pid_err)
}

/// Compute distance concentration statistics.
/// Returns a dict with summary statistics including:
/// - pairwise min/max/mean/std/cv
/// - nearest-neighbor mean/cv and nn_over_pairwise_mean
#[pyfunction]
#[pyo3(signature = (x, metric="chebyshev"))]
fn distance_stats(x: PyReadonlyArray2<f64>, metric: &str) -> PyResult<BTreeMap<String, f64>> {
    let x_mat = array_to_matref(&x)?;
    let metric_enum = parse_metric(metric)?;

    let cfg = DistanceConcentrationConfig {
        metric: metric_enum,
    };

    let stats = distance_concentration_stats(x_mat, &cfg).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    map.insert("pairwise_count".to_string(), stats.pairwise_count as f64);
    map.insert("pairwise_min".to_string(), stats.pairwise_min);
    map.insert("pairwise_max".to_string(), stats.pairwise_max);
    map.insert("pairwise_mean".to_string(), stats.pairwise_mean);
    map.insert("pairwise_std".to_string(), stats.pairwise_std);
    map.insert("pairwise_cv".to_string(), stats.pairwise_cv);
    map.insert("nn_min".to_string(), stats.nn_min);
    map.insert("nn_max".to_string(), stats.nn_max);
    map.insert("nn_mean".to_string(), stats.nn_mean);
    map.insert("nn_cv".to_string(), stats.nn_cv);
    map.insert(
        "nn_over_pairwise_mean".to_string(),
        stats.nn_over_pairwise_mean,
    );
    Ok(map)
}

/// Compute the continuous 3-source `I^sx_∩` PID (18 atoms via Möbius inversion on the
/// redundancy lattice; Ehrlich et al. 2024 kNN estimator — not the discrete SxPID of
/// `compute_discrete_sxpid3`).
///
/// Keys are the antichain's source-subset bitmasks in the same `"[1, 6]"` list format used by
/// the discrete PID functions (bit `i` set ⇔ source `i+1` in the subset; e.g. `"[1, 2, 4]"` is
/// the bottom node `{{1},{2},{3}}` and `"[7]"` is the top node `{{1,2,3}}`).
#[pyfunction]
#[pyo3(signature = (s1, s2, s3, target, k=3, metric="chebyshev", tie_epsilon=0.0))]
#[allow(clippy::too_many_arguments)]
fn compute_pid3(
    s1: PyReadonlyArray2<f64>,
    s2: PyReadonlyArray2<f64>,
    s3: PyReadonlyArray2<f64>,
    target: PyReadonlyArray2<f64>,
    k: usize,
    metric: &str,
    tie_epsilon: f64,
) -> PyResult<BTreeMap<String, f64>> {
    let s1_mat = array_to_matref(&s1)?;
    let s2_mat = array_to_matref(&s2)?;
    let s3_mat = array_to_matref(&s3)?;
    let t_mat = array_to_matref(&target)?;
    let cfg = Pid3Config {
        k,
        metric: parse_metric(metric)?,
        tie_epsilon,
    };
    let out = pid3_isx(s1_mat, s2_mat, s3_mat, t_mat, &cfg).map_err(pid_err)?;

    let mut map = BTreeMap::new();
    for atom in &out.atoms {
        // Bitmask-list key (e.g. "[1, 6]"), matching the discrete PID functions — NOT the
        // struct's Debug output, which leaks internal zero-padding and is not a stable contract.
        map.insert(format!("{:?}", atom.antichain.sets()), atom.value);
    }
    Ok(map)
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

/// Fit PLS (Partial Least Squares) supervised dimensionality reduction and project X.
///
/// Projects high-dimensional X onto directions maximally correlated with target Y.
/// Unlike PCA, PLS uses label information to find the task-relevant subspace.
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
    let (projected, _pls) = PlsProjector::fit_transform(x_mat, y_mat, out_dim).map_err(pid_err)?;

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
    m.add_function(wrap_pyfunction!(compute_mi, m)?)?;
    m.add_function(wrap_pyfunction!(compute_redundancy, m)?)?;
    m.add_function(wrap_pyfunction!(compute_co_information, m)?)?;
    m.add_function(wrap_pyfunction!(compute_pid2, m)?)?;
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
    m.add_function(wrap_pyfunction!(estimate_intrinsic_dimension, m)?)?;
    m.add_function(wrap_pyfunction!(estimate_gromov_delta, m)?)?;
    m.add_function(wrap_pyfunction!(distance_stats, m)?)?;
    m.add_function(wrap_pyfunction!(pls_transform, m)?)?;
    m.add_function(wrap_pyfunction!(standardize, m)?)?;
    m.add_function(wrap_pyfunction!(pca_transform, m)?)?;
    m.add_function(wrap_pyfunction!(hash_project, m)?)?;
    Ok(())
}
