use crate::error::{PidError, PidResult};
use crate::kdtree::{concat_row_into, kdtree_applicable, KdTree};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::strict_radius;
use crate::par::map_index_ordered;
use crate::stats::{digamma, digamma_int_table};

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
/// Eligible low-dimensional Chebyshev inputs use an exact kd-tree with typically
/// sublinear pruned queries; other inputs use the brute-force scan. A kd-tree query
/// is still O(n) in the worst case, so the estimator remains O(n²) worst-case.
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
///
/// # Example
/// ```
/// use pid_core::{ksg_mi, KsgConfig, MatRef};
/// // Columns are dimensions, rows are samples: scalar X and a dependent Y.
/// let x = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0];
/// let y = [0.1, 0.9, 2.1, 2.8, 4.2, 4.9, 6.1, 7.0];
/// let x = MatRef::new(&x, 8, 1)?;
/// let y = MatRef::new(&y, 8, 1)?;
/// let mi = ksg_mi(x, y, &KsgConfig::default())?; // nats
/// assert!(mi.is_finite() && mi >= 0.0);
/// # Ok::<(), pid_core::PidError>(())
/// ```
pub fn ksg_mi(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<f64> {
    let local = ksg_local_mi_terms(x, y, cfg)?;
    let mi = local.iter().sum::<f64>() / (local.len() as f64);
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
/// Under the default [`NegativeHandling::ClampToZero`], [`ksg_mi`] floors its result at 0, so
/// for low-MI data the mean of these terms can be slightly below the value [`ksg_mi`] reports.
///
/// This is useful for building shared-exclusions estimators based on pointwise terms.
pub fn ksg_local_mi_terms(x: MatRef<'_>, y: MatRef<'_>, cfg: &KsgConfig) -> PidResult<Vec<f64>> {
    ksg_local_mi_terms_backend(x, y, cfg, NnBackend::Auto)
}

pub(crate) fn ksg_local_mi_terms_backend(
    x: MatRef<'_>,
    y: MatRef<'_>,
    cfg: &KsgConfig,
    backend: NnBackend,
) -> PidResult<Vec<f64>> {
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
                let eps = strict_radius(joint.kth_distance(&q, k, i as u32), cfg.tie_epsilon);
                if eps == 0.0 {
                    return Err(PidError::NumericalInstability {
                        context:
                            "ksg_local_mi_terms: kNN radius is non-positive; add jitter to break duplicates",
                    });
                }
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
                let eps = strict_radius(joint.kth_distance(&q, k, i as u32), cfg.tie_epsilon);
                if eps == 0.0 {
                    return Err(PidError::NumericalInstability {
                        context:
                            "ksg_local_mi_terms_xblocks: kNN radius is non-positive; add jitter to break duplicates",
                    });
                }
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

#[cfg(test)]
mod kdtree_parity_tests {
    use super::*;
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
        let x1 = mat(&mut rng, n, 2, true);
        let x2 = mat(&mut rng, n, 1, false);
        let y = mat(&mut rng, n, 1, true);
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
