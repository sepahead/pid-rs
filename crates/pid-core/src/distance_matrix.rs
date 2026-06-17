use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;

#[derive(Debug, Clone)]
pub struct SymmetricDistanceMatrix {
    n: usize,
    /// Upper-triangular storage excluding the diagonal, length n*(n-1)/2.
    data: Vec<f64>,
}

impl SymmetricDistanceMatrix {
    pub fn n(&self) -> usize {
        self.n
    }

    /// Get the distance between samples `i` and `j`.
    #[inline]
    pub fn get(&self, i: usize, j: usize) -> f64 {
        debug_assert!(i < self.n);
        debug_assert!(j < self.n);
        if i == j {
            return 0.0;
        }
        let (a, b) = if i < j { (i, j) } else { (j, i) };
        let idx = tri_index(self.n, a, b);
        self.data[idx]
    }
}

/// Compute the symmetric pairwise distance matrix for `m` under `metric`.
///
/// Storage is upper-triangular excluding the diagonal to reduce memory. Distances are non-negative.
pub fn symmetric_distances(m: MatRef<'_>, metric: Metric) -> PidResult<SymmetricDistanceMatrix> {
    let n = m.nrows();
    let len = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|v| v.checked_div(2))
        .ok_or(PidError::InvalidConfig {
            context: "symmetric_distances",
            message: "matrix size overflow",
        })?;

    let mut data = vec![0.0f64; len];
    for i in 0..n {
        let mi = m.row(i);
        for j in (i + 1)..n {
            let dist =
                metric.checked_distance(mi, m.row(j), "symmetric_distances: pairwise distance")?;
            data[tri_index(n, i, j)] = dist;
        }
    }

    Ok(SymmetricDistanceMatrix { n, data })
}

#[inline]
fn tri_index(n: usize, i: usize, j: usize) -> usize {
    debug_assert!(i < j);
    debug_assert!(j < n);

    // Number of entries before row i in the upper triangle excluding diagonal:
    // sum_{r=0..i-1} (n - r - 1) = i*n - i*(i+1)/2.
    let base = i * n - (i * (i + 1)) / 2;
    base + (j - i - 1)
}
