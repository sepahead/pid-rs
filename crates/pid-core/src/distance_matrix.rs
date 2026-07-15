use crate::error::{PidError, PidResult};
#[cfg(feature = "experimental-hyperbolic")]
use crate::hyperbolic::HyperbolicMetric;
use crate::matrix::MatRef;
use crate::metric::{KernelMetric, Metric};
use crate::resource::{
    try_vec_filled, try_vec_with_capacity, CancellationProgress, CancellationToken, ResourceBudget,
    ResourceEstimate,
};

#[derive(Debug)]
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
    ///
    /// # Panics
    ///
    /// Panics if either index is outside `0..self.n()`, matching ordinary Rust indexing.
    #[inline]
    pub fn get(&self, i: usize, j: usize) -> f64 {
        assert!(i < self.n, "row index {i} outside 0..{}", self.n);
        assert!(j < self.n, "column index {j} outside 0..{}", self.n);
        if i == j {
            return 0.0;
        }
        let (a, b) = if i < j { (i, j) } else { (j, i) };
        let idx = tri_index(self.n, a, b);
        self.data[idx]
    }

    /// Return a distance when both indices are in bounds.
    pub fn checked_get(&self, i: usize, j: usize) -> Option<f64> {
        if i >= self.n || j >= self.n {
            return None;
        }
        Some(self.get(i, j))
    }

    /// Preflight a copy of this matrix's triangular backing buffer.
    pub fn try_clone_resource_estimate(&self) -> PidResult<ResourceEstimate> {
        ResourceEstimate::contiguous::<f64>(
            "SymmetricDistanceMatrix::try_clone_with_budget",
            self.data.len(),
        )
    }

    /// Fallibly copy this matrix under an explicit resource ceiling.
    ///
    /// The ordinary [`Clone`] trait is intentionally absent because triangular storage is O(n²)
    /// and an infallible copy would bypass the crate's preflight contract.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        budget.check(
            "SymmetricDistanceMatrix::try_clone_with_budget",
            self.try_clone_resource_estimate()?,
        )?;
        let mut data = try_vec_with_capacity(
            "SymmetricDistanceMatrix::try_clone_with_budget",
            self.data.len(),
            budget,
        )?;
        data.extend_from_slice(&self.data);
        Ok(Self { n: self.n, data })
    }
}

/// Compute the symmetric pairwise distance matrix for `m` under `metric`.
///
/// Storage is upper-triangular excluding the diagonal to reduce memory. Distances are non-negative.
pub fn symmetric_distances(m: MatRef<'_>, metric: Metric) -> PidResult<SymmetricDistanceMatrix> {
    symmetric_distances_with_budget(m, metric, ResourceBudget::default())
}

/// Preflight the memory and pairwise work for one triangular `f64` distance matrix.
pub fn symmetric_distance_resources(n: usize) -> PidResult<ResourceEstimate> {
    ResourceEstimate::triangular_f64("symmetric_distances", n, 1, 1)
}

/// Dimension-aware preflight for computing one triangular distance matrix.
pub fn symmetric_distance_resources_for(m: MatRef<'_>) -> PidResult<ResourceEstimate> {
    let mut estimate = symmetric_distance_resources(m.nrows())?;
    estimate.operations_hint = estimate
        .pairwise_distances
        .checked_mul(m.ncols() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: "symmetric_distances",
        })?;
    Ok(estimate)
}

/// Compute a symmetric distance matrix after enforcing an explicit resource budget.
pub fn symmetric_distances_with_budget(
    m: MatRef<'_>,
    metric: Metric,
    budget: ResourceBudget,
) -> PidResult<SymmetricDistanceMatrix> {
    let cancellation = CancellationToken::new();
    symmetric_distances_with_budget_and_cancellation(m, metric, budget, &cancellation)
}

/// Compute a symmetric distance matrix with resource and cooperative-cancellation controls.
pub fn symmetric_distances_with_budget_and_cancellation(
    m: MatRef<'_>,
    metric: Metric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<SymmetricDistanceMatrix> {
    symmetric_distances_with_kernel_and_cancellation(
        m,
        metric.into(),
        symmetric_distance_resources_for(m)?,
        false,
        budget,
        cancellation,
    )
}

/// Compute a Lorentz-model symmetric distance matrix.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_symmetric_distances(
    m: MatRef<'_>,
    metric: HyperbolicMetric,
) -> PidResult<SymmetricDistanceMatrix> {
    hyperbolic_symmetric_distances_with_budget(m, metric, ResourceBudget::default())
}

/// Preflight one Lorentz-model triangular distance matrix.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_symmetric_distance_resources(n: usize) -> PidResult<ResourceEstimate> {
    let mut estimate = symmetric_distance_resources(n)?;
    let distance_calls =
        estimate
            .pairwise_distances
            .checked_add(n as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "symmetric_distances",
            })?;
    estimate.operations_hint = distance_calls
        .checked_mul(2)
        .and_then(|value| {
            value.checked_mul(crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR)
        })
        .ok_or(PidError::SizeOverflow {
            operation: "symmetric_distances",
        })?;
    Ok(estimate)
}

/// Dimension-aware preflight for one Lorentz-model triangular distance matrix.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_symmetric_distance_resources_for(m: MatRef<'_>) -> PidResult<ResourceEstimate> {
    let mut estimate = hyperbolic_symmetric_distance_resources(m.nrows())?;
    let distance_calls = estimate
        .pairwise_distances
        .checked_add(m.nrows() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: "symmetric_distances",
        })?;
    estimate.operations_hint = distance_calls
        .checked_mul(m.ncols().max(2) as u128)
        .and_then(|value| {
            value.checked_mul(crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR)
        })
        .ok_or(PidError::SizeOverflow {
            operation: "symmetric_distances",
        })?;
    Ok(estimate)
}

/// Compute a Lorentz-model symmetric distance matrix under an explicit resource budget.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_symmetric_distances_with_budget(
    m: MatRef<'_>,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
) -> PidResult<SymmetricDistanceMatrix> {
    let cancellation = CancellationToken::new();
    hyperbolic_symmetric_distances_with_budget_and_cancellation(m, metric, budget, &cancellation)
}

/// Compute a Lorentz-model symmetric distance matrix with resource and cancellation controls.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_symmetric_distances_with_budget_and_cancellation(
    m: MatRef<'_>,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<SymmetricDistanceMatrix> {
    crate::hyperbolic::validate_lorentz_matrix_widths("symmetric_distances", &[m])?;
    symmetric_distances_with_kernel_and_cancellation(
        m,
        metric.kernel(),
        hyperbolic_symmetric_distance_resources_for(m)?,
        true,
        budget,
        cancellation,
    )
}

fn symmetric_distances_with_kernel_and_cancellation(
    m: MatRef<'_>,
    metric: KernelMetric,
    estimate: ResourceEstimate,
    validate_metric_rows: bool,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<SymmetricDistanceMatrix> {
    const OPERATION: &str = "symmetric_distances";
    let n = m.nrows();
    budget.check(OPERATION, estimate)?;
    let len = usize::try_from(estimate.pairwise_distances).map_err(|_| PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let validation_work = if validate_metric_rows { n } else { 0 };
    let total_work = validation_work
        .checked_add(len)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let mut completed_work = 0usize;
    cancellation.check(OPERATION, completed_work, total_work)?;

    if validate_metric_rows {
        for row in 0..n {
            metric.checked_distance_with_cancellation(
                m.row(row),
                m.row(row),
                "symmetric_distances: invalid input row",
                CancellationProgress::new(OPERATION, completed_work, total_work),
                cancellation,
            )?;
            completed_work += 1;
            cancellation.check(OPERATION, completed_work, total_work)?;
        }
    }

    let mut data = try_vec_filled(OPERATION, len, 0.0f64, budget)?;
    let mut completed_pairs = 0usize;
    for i in 0..n {
        let mi = m.row(i);
        for j in (i + 1)..n {
            let dist = metric.checked_distance_with_cancellation(
                mi,
                m.row(j),
                "symmetric_distances: pairwise distance",
                CancellationProgress::new(OPERATION, completed_work, total_work),
                cancellation,
            )?;
            data[tri_index(n, i, j)] = dist;
            completed_pairs += 1;
            completed_work += 1;
            if completed_pairs.is_multiple_of(1_024) {
                cancellation.check(OPERATION, completed_work, total_work)?;
            }
        }
    }
    cancellation.check(OPERATION, completed_work, total_work)?;

    Ok(SymmetricDistanceMatrix { n, data })
}

#[inline]
fn tri_index(n: usize, i: usize, j: usize) -> usize {
    debug_assert!(i < j);
    debug_assert!(j < n);

    // Number of entries before row i in the upper triangle excluding diagonal:
    // sum_{r=0..i-1} (n - r - 1) = i*n - i*(i+1)/2.
    // Every supported Rust target has a <=64-bit usize, so the product of two usize values fits
    // in u128. Construction already proved the final triangular length fits usize; calculating
    // the intermediate in u128 avoids the otherwise possible `i*n` overflow.
    let i128 = i as u128;
    let base = i128 * n as u128 - (i128 * (i128 + 1)) / 2;
    let index = base + (j - i - 1) as u128;
    debug_assert!(index <= usize::MAX as u128);
    index as usize
}

#[cfg(test)]
mod tests {
    use super::{symmetric_distances, symmetric_distances_with_budget};
    use crate::error::PidError;
    use crate::matrix::MatRef;
    use crate::metric::Metric;
    use crate::resource::ResourceBudget;

    #[test]
    fn oversized_zero_column_matrix_returns_error_instead_of_capacity_panic() {
        // A zero-column MatRef can describe this row count without allocating an input buffer.
        // Its triangular f64 storage exceeds the addressable Vec byte capacity on 64-bit targets.
        let matrix = MatRef::new(&[], 1_600_000_000, 0).unwrap();

        assert!(symmetric_distances(matrix, Metric::Chebyshev).is_err());
    }

    #[test]
    fn dimension_work_is_included_in_preflight() {
        let data = [0.0; 6];
        let matrix = MatRef::new(&data, 2, 3).unwrap();
        let budget = ResourceBudget {
            max_operations_hint: 2,
            ..ResourceBudget::default()
        };

        assert!(symmetric_distances_with_budget(matrix, Metric::Chebyshev, budget).is_err());
    }

    #[test]
    fn actual_distance_path_rejects_triangular_bytes_before_allocation() {
        let data = [0.0; 5];
        let matrix = MatRef::new(&data, 5, 1).unwrap();
        let budget = ResourceBudget {
            max_bytes: 79,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            symmetric_distances_with_budget(matrix, Metric::Chebyshev, budget),
            Err(PidError::ResourceLimitExceeded {
                operation: "symmetric_distances",
                resource: "bytes",
                requested: 80,
                limit: 79,
            })
        ));
    }

    #[test]
    fn triangular_matrix_copy_requires_an_explicit_sufficient_budget() {
        let data = [0.0, 1.0, 3.0];
        let matrix =
            symmetric_distances(MatRef::new(&data, 3, 1).unwrap(), Metric::Chebyshev).unwrap();
        let tiny = ResourceBudget {
            max_bytes: 23,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            matrix.try_clone_with_budget(tiny),
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                requested: 24,
                limit: 23,
                ..
            })
        ));
        let copied = matrix
            .try_clone_with_budget(ResourceBudget::default())
            .unwrap();
        assert_eq!(copied.get(0, 2), matrix.get(0, 2));
    }
}
