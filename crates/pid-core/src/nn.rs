use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;

/// Convert a positive raw kNN radius `eps_raw` into a radius suitable for *inclusive* neighbor
/// counting.
///
/// KSG-style estimators require strict-inequality semantics (`distance < eps_raw`). Many kNN
/// backends provide only inclusive radius queries (`<= eps`). To recover strict semantics, we
/// return an `eps_strict` that is guaranteed to be strictly smaller than `eps_raw` (in floating
/// point terms). Counting neighbors with `distance <= eps_strict` is then equivalent to
/// `distance < eps_raw` for floating-point distances.
#[inline]
pub(crate) fn strict_radius(eps: f64) -> f64 {
    if !eps.is_finite() || eps <= 0.0 {
        return 0.0;
    }
    next_down_pos(eps)
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

/// Count points strictly inside and exactly on a positive kNN-radius shell.
///
/// The caller supplies distances computed in the estimator's joint metric. Keeping this helper
/// independent of the distance backend lets brute-force and indexed estimators enforce the same
/// continuous-support contract.
pub(crate) fn kth_neighbor_shell_counts(
    distances: impl IntoIterator<Item = f64>,
    radius: f64,
) -> (usize, usize) {
    let mut interior_count = 0usize;
    let mut boundary_count = 0usize;
    for distance in distances {
        if distance < radius {
            interior_count += 1;
        } else if distance == radius {
            boundary_count += 1;
        }
    }
    (interior_count, boundary_count)
}

/// Reject a k-th-neighbor shell that is not uniquely defined by the empirical distances.
///
/// For a continuous sample without distance ties, the positive k-th radius has exactly `k - 1`
/// points in its strict interior and exactly one point on its boundary. Either a tie that crosses
/// the left side of rank `k` or an additional point tied on the outer boundary violates that
/// condition, so applying the continuous KSG formula would silently choose a rank convention that
/// the estimator does not define.
pub(crate) fn validate_kth_neighbor_shell(
    context: &'static str,
    query_index: usize,
    k: usize,
    radius: f64,
    interior_count: usize,
    boundary_count: usize,
) -> PidResult<()> {
    if k > 0 && interior_count == k - 1 && boundary_count == 1 {
        return Ok(());
    }
    Err(PidError::AmbiguousKthNeighborShell {
        context,
        query_index,
        k,
        radius,
        interior_count,
        boundary_count,
    })
}

/// Brute-force kNN radius in a joint space composed of multiple blocks, using a reusable scratch
/// buffer for distances.
///
/// This is identical to `kth_neighbor_distance_joint_max`, but avoids allocating a fresh `Vec<f64>`
/// for every query. Callers should pass a `scratch` with capacity `n-1` for best performance.
pub(crate) fn kth_neighbor_distance_joint_max_with_scratch(
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
/// `eps = strict_radius(eps_raw)`.
pub(crate) fn count_neighbors_within(
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
    use super::{kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell};
    use crate::error::PidError;

    #[test]
    fn strict_radius_is_strict_when_possible() {
        let eps = 1.0;

        // Exact strictness is represented by the predecessor of the raw radius.
        let r = strict_radius(eps);
        assert!(r.is_finite());
        assert!(r > 0.0);
        assert!(r < eps);

        assert_eq!(strict_radius(f64::from_bits(1)), 0.0);
    }

    #[test]
    fn strict_radius_handles_degenerate_and_non_finite_inputs() {
        assert_eq!(strict_radius(0.0), 0.0);
        assert_eq!(strict_radius(-1.0), 0.0);
        assert_eq!(strict_radius(f64::NAN), 0.0);
        assert_eq!(strict_radius(f64::INFINITY), 0.0);
    }

    #[test]
    fn kth_neighbor_shell_accepts_one_boundary_point_at_rank_k() {
        let counts = kth_neighbor_shell_counts([0.25, 0.5, 1.0, 2.0], 1.0);

        assert!(validate_kth_neighbor_shell("test", 7, 3, 1.0, counts.0, counts.1).is_ok());
    }

    #[test]
    fn kth_neighbor_shell_rejects_a_tie_crossing_rank_k() {
        let counts = kth_neighbor_shell_counts([1.0, 1.0, 2.0], 1.0);

        let error = validate_kth_neighbor_shell("test", 7, 2, 1.0, counts.0, counts.1).unwrap_err();

        assert!(matches!(
            error,
            PidError::AmbiguousKthNeighborShell {
                query_index: 7,
                k: 2,
                radius: 1.0,
                interior_count: 0,
                boundary_count: 2,
                ..
            }
        ));
    }
}
