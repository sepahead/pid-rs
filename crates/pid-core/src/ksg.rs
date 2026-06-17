use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::strict_radius;
use crate::stats::{digamma, digamma_int_table};

/// Map the per-point KSG local-MI computation over `0..n`, collecting results in
/// index order. With the `parallel` feature this runs data-parallel over the points
/// (each point is independent and allocates its own scratch); without it, serially.
///
/// Because results are collected **in index order** and the closure body is
/// identical in both paths, the parallel result is bit-for-bit identical to the
/// serial one — the `parallel` feature is a throughput optimization, not a change of
/// estimator (validated by re-running the estimator test suite under the feature).
#[cfg(feature = "parallel")]
fn map_local_terms<F>(n: usize, f: F) -> PidResult<Vec<f64>>
where
    F: Fn(usize) -> PidResult<f64> + Sync + Send,
{
    use rayon::prelude::*;
    (0..n).into_par_iter().map(f).collect()
}

#[cfg(not(feature = "parallel"))]
fn map_local_terms<F>(n: usize, f: F) -> PidResult<Vec<f64>>
where
    F: Fn(usize) -> PidResult<f64>,
{
    (0..n).map(f).collect()
}

#[derive(Debug, Clone, Copy)]
pub enum NegativeHandling {
    Allow,
    ClampToZero,
}

#[derive(Clone, Copy)]
struct DistPair {
    joint: f64,
    dx: f64,
    dy: f64,
}

#[derive(Debug, Clone)]
pub struct KsgConfig {
    /// Number of nearest neighbors (excluding self).
    ///
    /// KSG requires `n > k >= 1`.
    pub k: usize,
    /// Distance metric. For KSG, the standard choice is Chebyshev / L∞.
    pub metric: Metric,
    /// Tie handling for strict-inequality counting.
    ///
    /// Many kNN backends only support inclusive ball queries (`<= eps`). To implement the KSG-1
    /// strict inequality (`< eps_raw`) robustly, we convert the raw kNN radius `eps_raw` into a
    /// strict radius `eps = strict_radius(eps_raw, tie_epsilon)` which is guaranteed to be
    /// strictly smaller than `eps_raw` (in floating-point terms), then count neighbors using
    /// `<= eps`.
    pub tie_epsilon: f64,
    /// Handling of small negative MI estimates due to finite-sample noise.
    pub negative_handling: NegativeHandling,
}

impl Default for KsgConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            negative_handling: NegativeHandling::ClampToZero,
        }
    }
}

/// KSG mutual information estimator (Algorithm 1 style).
///
/// - Uses a kNN search in joint space (X,Y) with the configured metric (default: L∞).
/// - Uses strict-inequality semantics for marginal counts (`< eps_raw`) via `strict_radius` + `<=`.
/// - Returns MI in nats (natural log).
///
/// This is a brute-force O(n²) reference implementation intended for correctness first.
///
/// # Assumptions / failure modes
/// - **i.i.d. samples:** KSG assumes independent samples from a fixed distribution. For time-series
///   data (VLA trajectories), autocorrelation can seriously bias estimates unless you subsample or
///   otherwise account for dependence.
/// - **Continuous support:** duplicates/quantization can collapse the kNN radius to 0 and trigger
///   `PidError::NumericalInstability`. Add small jitter (explicitly, seeded) only as a last resort
///   and re-validate in Experiment 0.
/// - **High dimension:** kNN distances concentrate with large ambient/intrinsic dimension; the
///   estimator can become unstable or dominated by finite-sample noise.
/// - **Strong dependence:** even at low dimension, near-deterministic relationships (very large
///   true MI) can require prohibitive sample sizes for kNN MI (see Gao, Ver Steeg, Galstyan 2015).
/// - **Clamping:** by default `KsgConfig` clamps small negative estimates to 0. This is a reporting
///   choice, not a mathematical property of the estimator; use `NegativeHandling::Allow` when you
///   need unbiased cancellation in algebraic identities.
pub fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    let local = ksg_local_mi_terms(x, y, cfg)?;
    let mi = local.iter().sum::<f64>() / (local.len() as f64);
    Ok(match cfg.negative_handling {
        NegativeHandling::Allow => mi,
        NegativeHandling::ClampToZero => mi.max(0.0),
    })
}

/// Returns the per-sample local MI contributions whose average equals the KSG MI estimate.
///
/// local_i = ψ(k) + ψ(n) - ψ(n_x(i)+1) - ψ(n_y(i)+1)
///
/// This is useful for building shared-exclusions estimators based on pointwise terms.
pub fn ksg_local_mi_terms(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<Vec<f64>> {
    if x.nrows() != y.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "ksg_local_mi_terms",
            left_rows: x.nrows(),
            right_rows: y.nrows(),
        });
    }
    if x.ncols() == 0 || y.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms",
            message: "x and y must have at least 1 column",
        });
    }
    if !cfg.tie_epsilon.is_finite() || cfg.tie_epsilon < 0.0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms",
            message: "tie_epsilon must be finite and >= 0",
        });
    }
    let n = x.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    map_local_terms(n, |i| {
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
        let eps = scratch[kth].joint;
        // Strict inequality for marginal counts.
        let eps = strict_radius(eps, cfg.tie_epsilon);
        if eps == 0.0 {
            return Err(PidError::NumericalInstability {
                context:
                    "ksg_local_mi_terms: kNN radius is non-positive; add jitter to break duplicates",
            });
        }

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
    if !cfg.tie_epsilon.is_finite() || cfg.tie_epsilon < 0.0 {
        return Err(PidError::InvalidConfig {
            context: "ksg_local_mi_terms_xblocks",
            message: "tie_epsilon must be finite and >= 0",
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

    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    map_local_terms(n, |i| {
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
        let eps = strict_radius(scratch[kth].joint, cfg.tie_epsilon);
        if eps == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "ksg_local_mi_terms_xblocks: kNN radius is non-positive; add jitter to break duplicates",
            });
        }

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
    let mi = local.iter().sum::<f64>() / (local.len() as f64);
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

        let mut x = Vec::with_capacity(n * d1);
        let mut y = Vec::with_capacity(n * d2);
        let mut t = Vec::with_capacity(n * dt);
        for i in 0..n {
            for j in 0..d1 {
                x.push((i as f64) * 0.1 + (j as f64) * 0.01);
            }
            for j in 0..d2 {
                y.push((i as f64) * 0.2 - (j as f64) * 0.03);
            }
            t.push((i as f64) * 0.15);
        }

        let x = MatRef::new(&x, n, d1).unwrap();
        let y = MatRef::new(&y, n, d2).unwrap();
        let t = MatRef::new(&t, n, dt).unwrap();
        let cfg = KsgConfig::default();

        let mi_blocks = ksg_mi_concat_xy(x, y, t, &cfg).unwrap();
        let xy = concat_horiz(x, y).unwrap();
        let mi_explicit = ksg_mi(xy.as_ref(), t, &cfg).unwrap();

        assert!(
            (mi_blocks - mi_explicit).abs() < 1e-12,
            "mi_blocks={mi_blocks} mi_explicit={mi_explicit}"
        );
    }
}
