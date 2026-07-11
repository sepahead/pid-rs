use crate::error::{PidError, PidResult};
use crate::kdtree::{concat_row_into, kdtree_applicable, KdTree};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
use crate::par::map_index_ordered;
use crate::stats::{compensated_sum, digamma, digamma_int_table};
use crate::support::{
    continuous_input_diagnostics, continuous_joint_shell_diagnostics,
    validate_observed_sample_conditions, validate_support_contract, ContinuousInputDiagnostics,
    NeighborShellDiagnostics, SupportContract,
};

const LORENTZ_CURVATURE: f64 = -1.0;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NegativeHandling {
    /// Return the signed finite-sample estimate without a presentation transform.
    Allow,
    /// Floor the final standalone estimate at zero as an explicit presentation transform.
    ///
    /// Do not use this for MI terms that enter algebraic identities or inference procedures.
    ClampToZero,
}

#[derive(Clone, Copy)]
struct DistPair {
    joint: f64,
    dx: f64,
    dy: f64,
}

/// Neighbor-search backend selection. `Auto` engages the exact Chebyshev
/// kd-tree (see `kdtree.rs`) when it is applicable and profitable; the other
/// variants exist so tests can force each path and assert bit-identical
/// results.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[cfg_attr(not(test), allow(dead_code))] // Brute/KdTree are test-only forcing knobs
pub(crate) enum NnBackend {
    Auto,
    Brute,
    KdTree,
}

impl NnBackend {
    #[inline]
    fn use_tree(self, metric: Metric, n: usize, joint_dims: usize) -> bool {
        match self {
            NnBackend::Brute => false,
            NnBackend::KdTree => matches!(metric, Metric::Chebyshev) && joint_dims > 0,
            NnBackend::Auto => kdtree_applicable(metric, n, joint_dims),
        }
    }
}

#[derive(Debug, Clone)]
pub struct KsgConfig {
    /// Number of nearest neighbors (excluding self).
    ///
    /// KSG requires `n > k >= 1`.
    pub k: usize,
    /// Distance metric. For KSG, the standard choice is Chebyshev / L∞.
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Exact floating-point strict inequality is implemented with the predecessor of the raw kNN
    /// radius. Subtracting a material epsilon would exclude legitimate distances and estimate a
    /// different, eroded-neighborhood functional, so nonzero values are rejected.
    pub tie_epsilon: f64,
    /// Handling of small negative MI estimates due to finite-sample noise. The default is
    /// [`NegativeHandling::Allow`]; clamping is an explicit presentation-only opt-in.
    pub negative_handling: NegativeHandling,
    /// Population-support assertion for this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. For ordinary
    /// Euclidean KSG, the caller must assert [`SupportContract::AssumeAbsolutelyContinuous`] for
    /// every marginal and joint law used by the call. This assertion is not inferred or proved
    /// from the sample. [`SupportContract::AssumeSmoothManifold`] asserts continuous marginal and
    /// joint densities relative to the relevant manifold/product-manifold measures and finite MI;
    /// it is accepted only with the explicitly experimental hyperbolic metric.
    pub support_contract: SupportContract,
}

impl Default for KsgConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl KsgConfig {
    /// Construct the ordinary Chebyshev configuration with an explicit caller assertion that all
    /// required marginal and joint laws are full-dimensional and absolutely continuous.
    pub fn assume_absolutely_continuous() -> Self {
        Self {
            support_contract: SupportContract::AssumeAbsolutelyContinuous,
            ..Self::default()
        }
    }

    /// Construct the standalone experimental manifold-KSG configuration.
    ///
    /// This selects Lorentz distance at curvature `-1` and records the manifold support assertion;
    /// it does not establish statistical consistency for manifold or hyperbolic KSG. This
    /// configuration is accepted only by [`ksg_mi_report`], which requires training provenance and
    /// preserves experimental warnings; scalar/local-term entry points reject it.
    pub fn experimental_smooth_hyperbolic_manifold() -> Self {
        Self {
            metric: Metric::HyperbolicLorentz,
            support_contract: SupportContract::AssumeSmoothManifold,
            ..Self::default()
        }
    }
}

/// Owned, structurally checked caller-declared provenance attached to a [`KsgMiReport`].
///
/// Provenance describes operations and assumptions that cannot be reconstructed from the numeric
/// sample. Both required descriptions must contain at least one non-whitespace character. An
/// embedding-training description is optional for ordinary Chebyshev KSG, but is required by
/// [`ksg_mi_report`] for the experimental Lorentz-hyperbolic path.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct KsgProvenance {
    preprocessing_description: String,
    observation_model_description: String,
    embedding_training_provenance: Option<String>,
}

impl KsgProvenance {
    /// Construct owned caller-declared provenance, checking only that required text is nonempty.
    pub fn new(
        preprocessing_description: impl Into<String>,
        observation_model_description: impl Into<String>,
        embedding_training_provenance: Option<String>,
    ) -> PidResult<Self> {
        let preprocessing_description = preprocessing_description.into();
        if preprocessing_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "preprocessing_description must be nonempty",
            });
        }
        let observation_model_description = observation_model_description.into();
        if observation_model_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "observation_model_description must be nonempty",
            });
        }
        if embedding_training_provenance
            .as_deref()
            .is_some_and(|description| description.trim().is_empty())
        {
            return Err(PidError::InvalidConfig {
                context: "KsgProvenance::new",
                message: "embedding_training_provenance must be nonempty when provided",
            });
        }
        Ok(Self {
            preprocessing_description,
            observation_model_description,
            embedding_training_provenance,
        })
    }

    pub fn preprocessing_description(&self) -> &str {
        &self.preprocessing_description
    }

    pub fn observation_model_description(&self) -> &str {
        &self.observation_model_description
    }

    pub fn embedding_training_provenance(&self) -> Option<&str> {
        self.embedding_training_provenance.as_deref()
    }
}

/// Scientific maturity of the estimator represented by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum KsgMethodStatus {
    /// Ordinary Chebyshev KSG under the explicitly declared, restricted support contract.
    RestrictedDomain,
    /// A research path without the same estimator-level validation claim.
    Experimental,
}

/// Geometry model recorded by a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum KsgGeometryModel {
    /// Ambient-coordinate product neighborhoods using the Chebyshev (L-infinity) metric.
    AmbientChebyshev,
    /// Unit-curvature Lorentz hyperboloid model.
    LorentzHyperboloid,
}

/// A deterministic, machine-readable warning attached to a [`KsgMiReport`].
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum KsgReportWarning {
    /// Sample diagnostics are one-way checks, not proofs of population support.
    SampleDiagnosticsCannotProveSupport,
    /// At least one independently selected marginal k-th-neighbor shell is degenerate or
    /// ambiguous, even though the joint shells used by the returned estimate passed validation.
    MarginalNeighborShellPathology,
    /// This crate has no consistency theorem for its manifold/hyperbolic KSG path.
    HyperbolicConsistencyNotEstablished,
}

impl KsgReportWarning {
    /// Stable explanatory text for this warning.
    pub const fn message(self) -> &'static str {
        match self {
            Self::SampleDiagnosticsCannotProveSupport => {
                "sample diagnostics can identify observations incompatible with ideal estimator conditions, but cannot determine the cause or prove population continuity, a common reference measure, or finite mutual information"
            }
            Self::MarginalNeighborShellPathology => {
                "an independently selected marginal k-th-neighbor shell has zero radius or an ambiguous positive boundary"
            }
            Self::HyperbolicConsistencyNotEstablished => {
                "hyperbolic/manifold KSG is experimental and this implementation lacks a statistical consistency theorem"
            }
        }
    }
}

/// KSG estimate with scoped support, geometry, sample diagnostics, and caller provenance.
///
/// All information values are in nats. The sample diagnostics can identify observations
/// incompatible with ideal estimator conditions, but cannot determine their cause or prove
/// absolute continuity, smooth-manifold support, a common reference measure, or finite population
/// mutual information. In particular,
/// [`KsgMethodStatus::Experimental`] for Lorentz geometry records that this crate does not have a
/// consistency theorem for hyperbolic/manifold KSG.
///
/// The diagnostic set is intentionally non-exhaustive: it does not estimate intrinsic dimension,
/// distance concentration, temporal dependence, k/n sensitivity, or finite-sample bias. Use the
/// crate's geometry diagnostics and an explicitly reported k/sample-size sensitivity analysis as
/// separate checks.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct KsgMiReport {
    pub estimate_nats: f64,
    pub n_samples: usize,
    pub k: usize,
    pub metric: Metric,
    pub negative_handling: NegativeHandling,
    pub support_contract: SupportContract,
    pub method_status: KsgMethodStatus,
    pub provenance: KsgProvenance,
    pub x_diagnostics: ContinuousInputDiagnostics,
    pub y_diagnostics: ContinuousInputDiagnostics,
    pub joint_shells: NeighborShellDiagnostics,
    pub geometry_model: KsgGeometryModel,
    /// Sectional curvature for a geometric model, or `None` for ambient Chebyshev geometry.
    pub curvature: Option<f64>,
    /// `d` inferred from a Lorentz row of width `d + 1`; not an estimated intrinsic dimension.
    pub x_hyperbolic_dimension: Option<usize>,
    /// `d` inferred from a Lorentz row of width `d + 1`; not an estimated intrinsic dimension.
    pub y_hyperbolic_dimension: Option<usize>,
    /// Warnings in a stable order: support limitation, observed marginal pathology, then
    /// hyperbolic-theory limitation when applicable.
    pub warnings: Vec<KsgReportWarning>,
}

/// Estimate KSG mutual information and return scoped interpretation metadata and diagnostics.
///
/// The scalar [`ksg_mi`] API remains available for callers that deliberately do not need a
/// structured report. This reporting path additionally computes independent marginal and joint
/// shell diagnostics and therefore performs more distance evaluations.
pub fn ksg_mi_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<KsgMiReport> {
    // Preserve shape/config/support error precedence before the report-only provenance gate.
    validate_ksg_pair_structure("ksg_mi_report", x, y, cfg)?;
    if cfg.metric == Metric::HyperbolicLorentz
        && provenance.embedding_training_provenance().is_none()
    {
        return Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        });
    }

    let estimate_nats = ksg_mi_for_report(x, y, cfg)?;
    let x_diagnostics = continuous_input_diagnostics(x, cfg.k, cfg.metric)?;
    let y_diagnostics = continuous_input_diagnostics(y, cfg.k, cfg.metric)?;
    let joint_shells = continuous_joint_shell_diagnostics(&[x, y], cfg.k, cfg.metric)?;

    let mut warnings = Vec::with_capacity(3);
    warnings.push(KsgReportWarning::SampleDiagnosticsCannotProveSupport);
    if has_shell_pathology(x_diagnostics.marginal_shells)
        || has_shell_pathology(y_diagnostics.marginal_shells)
    {
        warnings.push(KsgReportWarning::MarginalNeighborShellPathology);
    }

    let (method_status, geometry_model, curvature, x_hyperbolic_dimension, y_hyperbolic_dimension) =
        match cfg.metric {
            Metric::Chebyshev => (
                KsgMethodStatus::RestrictedDomain,
                KsgGeometryModel::AmbientChebyshev,
                None,
                None,
                None,
            ),
            Metric::HyperbolicLorentz => {
                warnings.push(KsgReportWarning::HyperbolicConsistencyNotEstablished);
                (
                    KsgMethodStatus::Experimental,
                    KsgGeometryModel::LorentzHyperboloid,
                    Some(LORENTZ_CURVATURE),
                    Some(x.ncols() - 1),
                    Some(y.ncols() - 1),
                )
            }
        };

    Ok(KsgMiReport {
        estimate_nats,
        n_samples: x.nrows(),
        k: cfg.k,
        metric: cfg.metric,
        negative_handling: cfg.negative_handling,
        support_contract: cfg.support_contract,
        method_status,
        provenance: provenance.clone(),
        x_diagnostics,
        y_diagnostics,
        joint_shells,
        geometry_model,
        curvature,
        x_hyperbolic_dimension,
        y_hyperbolic_dimension,
        warnings,
    })
}

fn has_shell_pathology(diagnostics: NeighborShellDiagnostics) -> bool {
    diagnostics.zero_radius_queries > 0 || diagnostics.ambiguous_positive_shell_queries > 0
}

/// KSG mutual information estimator (Algorithm 1 style).
///
/// - Uses a kNN search in joint space (X,Y). This scalar API accepts ordinary Chebyshev/L∞
///   geometry; experimental Lorentz geometry is provenance-gated through [`ksg_mi_report`].
/// - Uses strict-inequality semantics for marginal counts (`< eps_raw`) via `strict_radius` + `<=`.
/// - Returns MI in nats (natural log).
///
/// Eligible low-dimensional Chebyshev inputs use an exact kd-tree with typically
/// sublinear pruned queries; other inputs use the brute-force scan. A kd-tree query
/// is still O(n) in the worst case, so the estimator remains O(n²) worst-case.
///
/// # Assumptions / failure modes
/// - **Declared support:** the default support contract is unspecified and fails closed. Ordinary
///   Chebyshev KSG requires a caller assertion that every marginal and joint law used here is
///   full-dimensional and absolutely continuous. Exact coordinate ties are incompatible with the
///   estimator's ideal i.i.d., unrounded continuous-sample conditions, but neither identify their
///   cause nor classify population support; all-unique finite observations do not prove the model.
/// - **i.i.d. samples:** KSG assumes independent samples from a fixed distribution. For time-series
///   data (VLA trajectories), autocorrelation can seriously bias estimates unless you subsample or
///   otherwise account for dependence.
/// - **Observed ties and geometry:** exact coordinate ties are rejected by the continuous-sample
///   preflight. Separately, an otherwise accepted sample can still produce a non-positive kNN
///   radius or multiple observations on a positive boundary; those cases trigger
///   `PidError::NumericalInstability` or `PidError::AmbiguousKthNeighborShell`, respectively.
///   Adding jitter changes the estimated distribution; use it only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis. Otherwise
///   use an estimator whose discrete, quantized, or mixed-support contract matches the data.
/// - **High dimension:** kNN distances concentrate with large ambient/intrinsic dimension; the
///   estimator can become unstable or dominated by finite-sample noise.
/// - **Strong dependence:** even at low dimension, near-deterministic relationships (very large
///   true MI) can require prohibitive sample sizes for kNN MI (see Gao, Ver Steeg, Galstyan 2015).
///   An exact deterministic map between continuous variables has infinite MI and is outside this
///   estimator's domain. An explicit observation-noise model defines a different, finite-MI
///   distribution; otherwise use a suitable discrete/mixed method.
/// - **Clamping:** `KsgConfig` returns signed estimates by default. Opting into
///   `NegativeHandling::ClampToZero` is a presentation transform, not a mathematical property of
///   the estimator, and must not be applied before algebraic identities or inference.
///
/// # Example
/// ```
/// use pid_core::{ksg_mi, KsgConfig, MatRef};
/// // Columns are dimensions, rows are samples: scalar X and a dependent Y.
/// let x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
/// let y = [0.1, 0.9, 2.1, 2.8, 4.2, 4.9, 6.1, 7.0];
/// let x = MatRef::new(&x, 8, 1)?;
/// let y = MatRef::new(&y, 8, 1)?;
/// let mi = ksg_mi(x, y, &KsgConfig::assume_absolutely_continuous())?; // nats
/// assert!(mi.is_finite());
/// # Ok::<(), pid_core::PidError>(())
/// ```
pub fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    validate_ksg_pair_structure("ksg_mi", x, y, cfg)?;
    reject_unreported_hyperbolic("ksg_mi", cfg)?;
    ksg_mi_for_report(x, y, cfg)
}

fn ksg_mi_for_report(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    let local = ksg_local_mi_terms_backend(x, y, cfg, NnBackend::Auto)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

/// Returns the per-sample local MI contributions whose average is the **unclamped** KSG MI
/// estimate (i.e. [`ksg_mi`] configured with [`NegativeHandling::Allow`]).
///
/// local_i = ψ(k) + ψ(n) - ψ(n_x(i)+1) - ψ(n_y(i)+1)
///
/// If [`ksg_mi`] is explicitly configured with [`NegativeHandling::ClampToZero`], low-MI data can
/// have a local-term mean slightly below the floored value that [`ksg_mi`] reports. The default
/// [`NegativeHandling::Allow`] returns this signed mean unchanged.
///
/// This is useful for building shared-exclusions estimators based on pointwise terms.
pub fn ksg_local_mi_terms(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<Vec<f64>> {
    validate_ksg_pair_structure("ksg_local_mi_terms", x, y, cfg)?;
    reject_unreported_hyperbolic("ksg_local_mi_terms", cfg)?;
    ksg_local_mi_terms_backend(x, y, cfg, NnBackend::Auto)
}

fn reject_unreported_hyperbolic(context: &'static str, cfg: &KsgConfig) -> PidResult<()> {
    if cfg.metric == Metric::HyperbolicLorentz {
        return Err(PidError::InvalidConfig {
            context,
            message: "Metric::HyperbolicLorentz is available only through ksg_mi_report, which requires embedding-training provenance and preserves experimental status/warnings",
        });
    }
    Ok(())
}

pub(crate) fn ksg_local_mi_terms_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    validate_ksg_pair_structure("ksg_local_mi_terms", x, y, cfg)?;
    let n = x.nrows();
    let k = cfg.k;
    validate_observed_sample_conditions("ksg_local_mi_terms", cfg.support_contract, &[x, y])?;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    // Typically faster exact Chebyshev kd-tree path (kdtree.rs) — identical
    // outputs to the brute scan (same distance fold, same total_cmp k-th
    // value, same inclusive counts on the strict radius). Queries remain
    // linear in the worst case. Build failure (non-finite coordinates or
    // spans) falls through to the brute scan so the canonical
    // `checked_distance` error context is preserved.
    if backend.use_tree(cfg.metric, n, x.ncols() + y.ncols()) {
        if let (Ok(joint), Ok(tx), Ok(ty)) = (
            KdTree::build(&[x, y]),
            KdTree::build(&[x]),
            KdTree::build(&[y]),
        ) {
            return map_index_ordered(n, |i| {
                let mut q = Vec::with_capacity(x.ncols() + y.ncols());
                concat_row_into(&[x, y], i, &mut q);
                let eps_raw = joint.kth_distance(&q, k, i as u32);
                if eps_raw == 0.0 {
                    return Err(PidError::NumericalInstability {
                        context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                    });
                }
                let (interior_count, boundary_count) =
                    joint.kth_neighbor_shell_counts(&q, eps_raw, i as u32);
                validate_kth_neighbor_shell(
                    "ksg_local_mi_terms",
                    i,
                    k,
                    eps_raw,
                    interior_count,
                    boundary_count,
                )?;
                let eps = strict_radius(eps_raw);
                let nx = tx.count_within(x.row(i), eps, i as u32);
                let ny = ty.count_within(y.row(i), eps, i as u32);
                Ok(psi_k + psi_n - psi_int[nx + 1] - psi_int[ny + 1])
            });
        }
    }

    map_index_ordered(n, |i| {
        let mut scratch = Vec::with_capacity(n.saturating_sub(1));
        let xi = x.row(i);
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let dx = cfg
                .metric
                .checked_distance(xi, x.row(j), "ksg_local_mi_terms: x distance")?;
            let dy = cfg
                .metric
                .checked_distance(yi, y.row(j), "ksg_local_mi_terms: y distance")?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        // Strict inequality for marginal counts.
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(psi_k + psi_n - psi_int[nx + 1] - psi_int[ny + 1])
    })
}

fn validate_ksg_pair_structure(
    context: &'static str,
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<()> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context,
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if x.ncols() == 0 || y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "x and y must have at least 1 column",
        });
    }
    if cfg.metric == Metric::HyperbolicLorentz && (x.ncols() < 2 || y.ncols() < 2) {
        return Err(PidError::InvalidConfig {
            context,
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    let n = x.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    validate_support_contract(context, cfg.support_contract, cfg.metric)
}

/// KSG local MI terms when the "X" variable is treated as a concatenation of multiple blocks.
///
/// With `Metric::Chebyshev`, treating the concatenation as a max-over-blocks distance is
/// equivalent to explicitly concatenating the vectors, but avoids allocating an `(n×(d1+d2+...))`
/// temporary matrix.
pub(crate) fn ksg_local_mi_terms_xblocks<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_xblocks_backend(x_blocks, y, cfg, NnBackend::Auto)
}

pub(crate) fn ksg_local_mi_terms_xblocks_backend<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
    if x_blocks.is_empty() {
        return Err(PidError::NotImplemented {
            feature: "ksg_local_mi_terms_xblocks with empty x_blocks",
        });
    }
    if y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "y must have at least 1 column",
        });
    }
    let n = y.nrows();
    for b in x_blocks {
        if b.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "ksg_local_mi_terms_xblocks",
                left_rows: n,
                right_rows: b.nrows(),
            });
        }
        if b.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: "ksg_local_mi_terms_xblocks",
                message: "x blocks must have at least 1 column",
            });
        }
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }

    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    // The max-over-blocks distance equals true concatenation only under L∞/Chebyshev
    // (max(max_b d_b, d_y) == d over the concatenated vector). For any other metric it
    // silently computes a *different* quantity, so reject it rather than mislabel the
    // result — matching the gating in `isx_redundancy` and `pid3_isx`.
    if cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "max-over-blocks concatenation distance is exact only for Metric::Chebyshev (L∞); other metrics are research-gated",
        });
    }
    validate_support_contract(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        cfg.metric,
    )?;
    let mut support_inputs = Vec::new();
    support_inputs
        .try_reserve_exact(x_blocks.len().saturating_add(1))
        .map_err(|_| PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "support-input allocation failed",
        })?;
    support_inputs.extend_from_slice(x_blocks);
    support_inputs.push(y);
    validate_observed_sample_conditions(
        "ksg_local_mi_terms_xblocks",
        cfg.support_contract,
        &support_inputs,
    )?;

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    // Typically faster exact tree path (see ksg_local_mi_terms_backend). The
    // metric is already gated to Chebyshev above, where max-over-blocks equals
    // the concatenated-space distance. Worst-case queries are still linear.
    let x_dims: usize = x_blocks.iter().map(|b| b.ncols()).sum();
    if backend.use_tree(cfg.metric, n, x_dims + y.ncols()) {
        let mut joint_blocks: Vec<MatRef<'a>> = x_blocks.to_vec();
        joint_blocks.push(y);
        if let (Ok(joint), Ok(tx), Ok(ty)) = (
            KdTree::build(&joint_blocks),
            KdTree::build(x_blocks),
            KdTree::build(&[y]),
        ) {
            return map_index_ordered(n, |i| {
                let mut q = Vec::with_capacity(x_dims + y.ncols());
                concat_row_into(&joint_blocks, i, &mut q);
                let eps_raw = joint.kth_distance(&q, k, i as u32);
                if eps_raw == 0.0 {
                    return Err(PidError::NumericalInstability {
                        context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
                    });
                }
                let (interior_count, boundary_count) =
                    joint.kth_neighbor_shell_counts(&q, eps_raw, i as u32);
                validate_kth_neighbor_shell(
                    "ksg_local_mi_terms_xblocks",
                    i,
                    k,
                    eps_raw,
                    interior_count,
                    boundary_count,
                )?;
                let eps = strict_radius(eps_raw);
                let mut qx = Vec::with_capacity(x_dims);
                concat_row_into(x_blocks, i, &mut qx);
                let nx = tx.count_within(&qx, eps, i as u32);
                let ny = ty.count_within(y.row(i), eps, i as u32);
                Ok(psi_k + psi_n - psi_int[nx + 1] - psi_int[ny + 1])
            });
        }
    }

    map_index_ordered(n, |i| {
        let mut scratch = Vec::with_capacity(n.saturating_sub(1));
        let mut x_rows_i: Vec<&[f64]> = Vec::with_capacity(x_blocks.len());
        for b in x_blocks {
            x_rows_i.push(b.row(i));
        }
        let yi = y.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let mut dx = 0.0f64;
            for (b_idx, b) in x_blocks.iter().enumerate() {
                dx = dx.max(cfg.metric.checked_distance(
                    x_rows_i[b_idx],
                    b.row(j),
                    "ksg_local_mi_terms_xblocks: x distance",
                )?);
            }
            let dy = cfg.metric.checked_distance(
                yi,
                y.row(j),
                "ksg_local_mi_terms_xblocks: y distance",
            )?;
            scratch.push(DistPair {
                joint: dx.max(dy),
                dx,
                dy,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "ksg_local_mi_terms_xblocks",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        let mut nx = 0usize;
        let mut ny = 0usize;
        for d in &scratch {
            if d.dx <= eps {
                nx += 1;
            }
            if d.dy <= eps {
                ny += 1;
            }
        }

        Ok(psi_k + psi_n - psi_int[nx + 1] - psi_int[ny + 1])
    })
}

pub(crate) fn ksg_mi_xblocks<'a>(
    x_blocks: &[MatRef<'a>],
    y: MatRef<'a>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    let local = ksg_local_mi_terms_xblocks(x_blocks, y, cfg)?;
    let mi = compensated_sum(local.iter().copied()) / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

pub fn ksg_mi_concat_xy(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    ksg_mi_xblocks(&[x, y], t, cfg)
}

#[cfg(test)]
mod tests {
    use super::{ksg_mi, ksg_mi_concat_xy, KsgConfig};
    use crate::matrix::{concat_horiz, MatRef};

    #[test]
    fn concat_xy_matches_explicit_concatenation_for_chebyshev() {
        // For Chebyshev/L∞, computing distance as max-over-blocks is equivalent to explicit
        // concatenation. This test guards the allocation-avoidance optimization.
        let n = 40;
        let d1 = 3;
        let d2 = 2;
        let dt = 1;

        let mut state = 0xC011_CAFE_D15C_A11Eu64;
        let mut next = || {
            state ^= state >> 12;
            state ^= state << 25;
            state ^= state >> 27;
            (state.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        };
        let mut x = Vec::with_capacity(n * d1);
        let mut y = Vec::with_capacity(n * d2);
        let mut t = Vec::with_capacity(n * dt);
        for _ in 0..n {
            for _ in 0..d1 {
                x.push(next());
            }
            for _ in 0..d2 {
                y.push(next());
            }
            t.push(next());
        }

        let x = MatRef::new(&x, n, d1).unwrap();
        let y = MatRef::new(&y, n, d2).unwrap();
        let t = MatRef::new(&t, n, dt).unwrap();
        let cfg = KsgConfig::assume_absolutely_continuous();

        let mi_blocks = ksg_mi_concat_xy(x, y, t, &cfg).unwrap();
        let xy = concat_horiz(x, y).unwrap();
        let mi_explicit = ksg_mi(xy.as_ref(), t, &cfg).unwrap();

        assert!(
            (mi_blocks - mi_explicit).abs() < 1e-12,
            "mi_blocks={mi_blocks} mi_explicit={mi_explicit}"
        );
    }
}

#[cfg(test)]
mod kdtree_parity_tests {
    use super::*;
    use crate::error::PidError;
    use crate::matrix::MatOwned;

    struct Rng(u64);
    impl Rng {
        fn next_f64(&mut self) -> f64 {
            let mut x = self.0;
            x ^= x >> 12;
            x ^= x << 25;
            x ^= x >> 27;
            self.0 = x;
            (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1u64 << 53) as f64
        }
    }

    fn mat(rng: &mut Rng, n: usize, d: usize, quantize: bool) -> MatOwned {
        let mut data = Vec::with_capacity(n * d);
        for _ in 0..n * d {
            let v = rng.next_f64();
            data.push(if quantize {
                (v * 16.0).round() / 16.0
            } else {
                v
            });
        }
        MatOwned::new(data, n, d).unwrap()
    }

    fn cfg(k: usize) -> KsgConfig {
        KsgConfig {
            k,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::Allow,
            support_contract: crate::support::SupportContract::AssumeAbsolutelyContinuous,
        }
    }

    fn shell_error_signature(
        result: PidResult<Vec<f64>>,
    ) -> (&'static str, usize, usize, u64, usize, usize) {
        match result.unwrap_err() {
            PidError::AmbiguousKthNeighborShell {
                context,
                query_index,
                k,
                radius,
                interior_count,
                boundary_count,
            } => (
                context,
                query_index,
                k,
                radius.to_bits(),
                interior_count,
                boundary_count,
            ),
            error => panic!("expected ambiguous k-th-neighbor shell, got {error:?}"),
        }
    }

    #[test]
    fn local_mi_terms_tree_is_bit_identical_to_brute() {
        // Below and above the Auto threshold; smooth and tie-heavy data.
        for (n, dx, dy, k, quantize) in [
            (64, 1, 1, 4, false),
            (300, 1, 1, 4, false),
            (300, 2, 1, 3, true),
            (200, 3, 2, 7, true),
        ] {
            let mut rng = Rng(0x5EED ^ ((n as u64) << 16) ^ ((dx as u64) << 8) ^ k as u64);
            let x = mat(&mut rng, n, dx, quantize);
            let y = mat(&mut rng, n, dy, quantize);
            let c = cfg(k);
            let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
            let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);
            match (brute, tree) {
                (Ok(b), Ok(t)) => {
                    assert_eq!(b.len(), t.len());
                    for (i, (bb, tt)) in b.iter().zip(&t).enumerate() {
                        assert_eq!(
                            bb.to_bits(),
                            tt.to_bits(),
                            "term {i} differs (n={n} dx={dx} dy={dy} k={k} q={quantize})"
                        );
                    }
                }
                // Tie-heavy data may legitimately collapse the radius: both
                // paths must then fail identically.
                (Err(_), Err(_)) => {}
                (b, t) => panic!("backend disagreement: brute={b:?} tree={t:?}"),
            }
        }
    }

    #[test]
    fn xblocks_tree_is_bit_identical_to_brute() {
        let mut rng = Rng(0xB10C5);
        let n = 260;
        let x1 = mat(&mut rng, n, 2, false);
        let x2 = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let blocks = [x1.as_ref(), x2.as_ref()];
        let brute =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::Brute).unwrap();
        let tree =
            ksg_local_mi_terms_xblocks_backend(&blocks, y.as_ref(), &c, NnBackend::KdTree).unwrap();
        for (i, (bb, tt)) in brute.iter().zip(&tree).enumerate() {
            assert_eq!(bb.to_bits(), tt.to_bits(), "xblocks term {i} differs");
        }
    }

    #[test]
    fn positive_outer_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [0.5, 1, 1, 3], so the outer shell contains two points.
        let x = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn positive_left_shell_tie_errors_identically_on_both_backends() {
        // Every joint row is distinct. At query 0 and k=2 the positive distances are
        // [1, 1, 2], so fewer than k-1 points lie strictly inside the selected radius.
        let x = MatOwned::new(vec![0.0, 1.0, 0.3, 2.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.2, 1.0, 2.0], 4, 1).unwrap();
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_backend(
            x.as_ref(),
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms", 0, 2, 1.0f64.to_bits(), 0, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn xblocks_positive_shell_tie_errors_identically_on_both_backends() {
        let x1 = MatOwned::new(vec![0.0, 0.5, 1.0, 0.3, 3.0], 5, 1).unwrap();
        let x2 = MatOwned::new(vec![0.0, 0.25, 0.75, 0.35, 2.5], 5, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 0.4, 0.2, 1.0, 3.0], 5, 1).unwrap();
        let blocks = [x1.as_ref(), x2.as_ref()];
        let c = cfg(2);
        let brute = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::Brute,
        ));
        let tree = shell_error_signature(ksg_local_mi_terms_xblocks_backend(
            &blocks,
            y.as_ref(),
            &c,
            NnBackend::KdTree,
        ));
        let expected = ("ksg_local_mi_terms_xblocks", 0, 2, 1.0f64.to_bits(), 1, 2);

        assert_eq!([brute, tree], [expected, expected]);
    }

    #[test]
    fn duplicate_rows_error_identically_on_both_backends() {
        // All-identical rows collapse every kNN radius; both backends must
        // fail (radius guard), not silently disagree.
        let n = 150;
        let x = MatOwned::new(vec![0.25; n], n, 1).unwrap();
        let y = MatOwned::new(vec![0.75; n], n, 1).unwrap();
        let c = cfg(3);
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).is_err());
        assert!(ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).is_err());
    }

    #[test]
    fn overflowing_coordinate_span_errors_identically_on_both_backends() {
        let x = MatOwned::new(vec![-f64::MAX, f64::MAX, 0.0, 1.0], 4, 1).unwrap();
        let y = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let c = cfg(1);

        let brute = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute);
        let tree = ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree);

        assert!(brute.is_err());
        assert!(tree.is_err());
    }

    #[test]
    #[ignore = "manual benchmark: cargo test -p pid-core --release kdtree_speedup -- --ignored --nocapture"]
    fn kdtree_speedup_smoke() {
        let mut rng = Rng(0xBEEF);
        let n = 4000;
        let x = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, false);
        let c = cfg(4);
        let t0 = std::time::Instant::now();
        let brute =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::Brute).unwrap();
        let t_brute = t0.elapsed();
        let t1 = std::time::Instant::now();
        let tree =
            ksg_local_mi_terms_backend(x.as_ref(), y.as_ref(), &c, NnBackend::KdTree).unwrap();
        let t_tree = t1.elapsed();
        assert_eq!(brute.len(), tree.len());
        println!(
            "n={n}: brute {t_brute:?} vs kd-tree {t_tree:?} ({:.1}x)",
            t_brute.as_secs_f64() / t_tree.as_secs_f64()
        );
    }
}
