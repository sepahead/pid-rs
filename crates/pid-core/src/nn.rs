use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;

/// Convert a raw kNN radius `eps_raw` into a radius suitable for *inclusive* neighbor counting.
///
/// KSG-style estimators require strict-inequality semantics (`distance < eps_raw`). Many kNN
/// backends provide only inclusive radius queries (`<= eps`). To recover strict semantics, we
/// return an `eps_strict` that is guaranteed to be strictly smaller than `eps_raw` (in floating
/// point terms). Counting neighbors with `distance <= eps_strict` is then equivalent to
/// `distance < eps_raw` for floating-point distances.
#[inline]
pub(crate) fn strict_radius(eps: f64, tie_epsilon: f64) -> f64 {
    if !eps.is_finite() || eps <= 0.0 {
        return 0.0;
    }
    let mut out = if tie_epsilon > 0.0 {
        (eps - tie_epsilon).max(0.0)
    } else {
        eps
    };
    if out == eps {
        out = next_down_pos(eps);
    }
    out
}

#[inline]
fn next_down_pos(x: f64) -> f64 {
    debug_assert!(x.is_finite());
    debug_assert!(x >= 0.0);
    if x == 0.0 {
        return 0.0;
    }
    f64::from_bits(x.to_bits() - 1)
}

/// Brute-force kNN radius in a joint space composed of multiple blocks, using a reusable scratch
/// buffer for distances.
///
/// This is identical to `kth_neighbor_distance_joint_max`, but avoids allocating a fresh `Vec<f64>`
/// for every query. Callers should pass a `scratch` with capacity `n-1` for best performance.
pub fn kth_neighbor_distance_joint_max_with_scratch(
    blocks: &[MatRef<'_>],
    i: usize,
    k: usize,
    metric: Metric,
    scratch: &mut Vec<f64>,
) -> PidResult<f64> {
    if blocks.is_empty() {
        return Err(PidError::NotImplemented {
            feature: "kth_neighbor_distance_joint_max_with_scratch with empty blocks",
        });
    }

    let n = blocks[0].nrows();
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }
    for b in blocks.iter().skip(1) {
        if b.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "kth_neighbor_distance_joint_max_with_scratch",
                left_rows: n,
                right_rows: b.nrows(),
            });
        }
    }

    scratch.clear();
    scratch.reserve(n.saturating_sub(1));

    for j in 0..n {
        if i == j {
            continue;
        }
        let mut dist = 0.0f64;
        for b in blocks {
            dist = dist.max(metric.checked_distance(
                b.row(i),
                b.row(j),
                "kth_neighbor_distance_joint_max_with_scratch: block distance",
            )?);
        }
        scratch.push(dist);
    }

    let kth = k - 1;
    scratch.select_nth_unstable_by(kth, |a, b| a.total_cmp(b));
    Ok(scratch[kth])
}

/// Count neighbors of sample `i` within radius `eps` in a single space.
///
/// This uses inclusive counting (`<= eps`). For KSG-style strict-inequality semantics, pass
/// `eps = strict_radius(eps_raw, tie_epsilon)`.
pub fn count_neighbors_within(
    m: MatRef<'_>,
    i: usize,
    eps: f64,
    metric: Metric,
) -> PidResult<usize> {
    let n = m.nrows();
    let mi = m.row(i);
    let mut count = 0usize;
    for j in 0..n {
        if i == j {
            continue;
        }
        if metric.checked_distance(mi, m.row(j), "count_neighbors_within: distance")? <= eps {
            count += 1;
        }
    }
    Ok(count)
}

#[cfg(test)]
mod tests {
    use super::strict_radius;

    #[test]
    fn strict_radius_is_strict_when_possible() {
        let eps = 1.0;

        // With tie_epsilon=0, we still ensure strictness via next-down.
        let r = strict_radius(eps, 0.0);
        assert!(r.is_finite());
        assert!(r > 0.0);
        assert!(r < eps);

        // With a small tie epsilon, subtracting should already be strict.
        let r = strict_radius(eps, 1e-12);
        assert!(r.is_finite());
        assert!(r > 0.0);
        assert!(r < eps);
    }

    #[test]
    fn strict_radius_handles_degenerate_and_non_finite_inputs() {
        assert_eq!(strict_radius(0.0, 1e-12), 0.0);
        assert_eq!(strict_radius(-1.0, 1e-12), 0.0);
        assert_eq!(strict_radius(f64::NAN, 1e-12), 0.0);
        assert_eq!(strict_radius(f64::INFINITY, 1e-12), 0.0);
    }

    #[test]
    fn strict_radius_can_be_zero_if_tie_epsilon_is_large() {
        let eps = 1e-9;
        let r = strict_radius(eps, 1e-3);
        assert_eq!(r, 0.0);
    }
}
