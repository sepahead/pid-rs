use std::cmp::Ordering as CmpOrdering;
use std::mem::size_of;
use std::sync::atomic::{AtomicBool, Ordering};

use serde::{Deserialize, Serialize};

use crate::error::{PidError, PidResult};

/// Thread-safe cooperative cancellation flag for bounded long-running operations.
///
/// Cancellation is advisory and is observed at deterministic work-unit boundaries. A cancelled
/// call returns [`PidError::Cancelled`] and never manufactures a partial numerical result.
#[derive(Debug, Default)]
pub struct CancellationToken {
    cancelled: AtomicBool,
}

impl CancellationToken {
    /// Construct a token in the running state.
    pub const fn new() -> Self {
        Self {
            cancelled: AtomicBool::new(false),
        }
    }

    /// Request cancellation. This operation is thread-safe and idempotent.
    pub fn cancel(&self) {
        self.cancelled.store(true, Ordering::Release);
    }

    /// Whether cancellation has been requested.
    pub fn is_cancelled(&self) -> bool {
        self.cancelled.load(Ordering::Acquire)
    }

    pub(crate) fn check(
        &self,
        operation: &'static str,
        completed_units: usize,
        total_units: usize,
    ) -> PidResult<()> {
        if self.is_cancelled() {
            Err(PidError::Cancelled {
                operation,
                completed_units,
                total_units,
            })
        } else {
            Ok(())
        }
    }
}

/// Caller-visible progress to retain when cancellation is observed inside one metric distance.
///
/// A single high-dimensional distance is itself checked cooperatively, but its coordinate index is
/// not the work-unit contract of the enclosing public operation. Passing this snapshot into the
/// metric keeps [`PidError::Cancelled`] attributable to that operation and its advertised units.
#[derive(Debug, Clone, Copy)]
pub(crate) struct CancellationProgress {
    operation: &'static str,
    completed_units: usize,
    total_units: usize,
}

impl CancellationProgress {
    pub(crate) const fn new(
        operation: &'static str,
        completed_units: usize,
        total_units: usize,
    ) -> Self {
        Self {
            operation,
            completed_units,
            total_units,
        }
    }

    pub(crate) fn check(self, cancellation: &CancellationToken) -> PidResult<()> {
        cancellation.check(self.operation, self.completed_units, self.total_units)
    }
}

/// In-place max-heapsort with periodic cooperative-cancellation checks.
///
/// This is used where `slice::sort_unstable_by` would otherwise form one uninterruptible,
/// externally-sized work unit. The final ordering is identical under a total comparator; equal
/// elements may move, matching the unstable-order contract.
pub(crate) fn sort_unstable_by_with_cancellation<T, F>(
    operation: &'static str,
    values: &mut [T],
    cancellation: &CancellationToken,
    mut compare: F,
) -> PidResult<()>
where
    F: FnMut(&T, &T) -> CmpOrdering,
{
    let len = values.len();
    let log_len = if len <= 1 {
        1
    } else {
        (usize::BITS - (len - 1).leading_zeros()) as usize
    };
    let total_units = len
        .saturating_mul(log_len.saturating_add(1))
        .saturating_mul(2);
    let mut completed_units = 0usize;
    cancellation.check(operation, completed_units, total_units)?;
    if len < 2 {
        return Ok(());
    }

    for root in (0..(len / 2)).rev() {
        sift_down_with_cancellation(
            operation,
            values,
            root,
            len,
            cancellation,
            &mut completed_units,
            total_units,
            &mut compare,
        )?;
    }
    for end in (1..len).rev() {
        values.swap(0, end);
        sift_down_with_cancellation(
            operation,
            values,
            0,
            end,
            cancellation,
            &mut completed_units,
            total_units,
            &mut compare,
        )?;
    }
    cancellation.check(operation, completed_units, total_units)
}

#[allow(clippy::too_many_arguments)]
fn sift_down_with_cancellation<T, F>(
    operation: &'static str,
    values: &mut [T],
    mut root: usize,
    end: usize,
    cancellation: &CancellationToken,
    completed_units: &mut usize,
    total_units: usize,
    compare: &mut F,
) -> PidResult<()>
where
    F: FnMut(&T, &T) -> CmpOrdering,
{
    loop {
        *completed_units = completed_units.saturating_add(1);
        if completed_units.is_multiple_of(1024) {
            cancellation.check(operation, *completed_units, total_units)?;
        }
        let Some(left) = root.checked_mul(2).and_then(|value| value.checked_add(1)) else {
            return Err(PidError::SizeOverflow { operation });
        };
        if left >= end {
            return Ok(());
        }
        let right = left + 1;
        let mut larger = left;
        if right < end && compare(&values[left], &values[right]).is_lt() {
            larger = right;
        }
        if !compare(&values[root], &values[larger]).is_lt() {
            return Ok(());
        }
        values.swap(root, larger);
        root = larger;
    }
}

/// Default memory ceiling inherited by APIs whose caller does not supply a budget (1 GiB).
pub const DEFAULT_MAX_BYTES: u64 = 1 << 30;
/// Default ceiling on distinct unordered pairwise distances.
pub const DEFAULT_MAX_PAIRWISE_DISTANCES: u64 = 50_000_000;
/// Default coarse operation ceiling for preflight estimates.
pub const DEFAULT_MAX_OPERATIONS_HINT: u128 = 10_000_000_000;

/// Caller-controlled resource ceiling for an estimator or diagnostic.
///
/// Safe APIs either accept a budget explicitly or inherit [`Self::default`]. A budget is a
/// preflight guard, not a promise that the operating system can satisfy an allocation below the
/// ceiling; allocator failures are returned separately as [`PidError::AllocationFailed`].
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ResourceBudget {
    pub max_bytes: u64,
    pub max_pairwise_distances: u64,
    pub max_operations_hint: u128,
    pub max_threads: usize,
}

impl Default for ResourceBudget {
    fn default() -> Self {
        Self {
            max_bytes: DEFAULT_MAX_BYTES,
            max_pairwise_distances: DEFAULT_MAX_PAIRWISE_DISTANCES,
            max_operations_hint: DEFAULT_MAX_OPERATIONS_HINT,
            max_threads: std::thread::available_parallelism().map_or(1, std::num::NonZero::get),
        }
    }
}

impl ResourceBudget {
    /// Construct and validate an explicit resource ceiling.
    pub fn new(
        max_bytes: u64,
        max_pairwise_distances: u64,
        max_operations_hint: u128,
        max_threads: usize,
    ) -> PidResult<Self> {
        Self {
            max_bytes,
            max_pairwise_distances,
            max_operations_hint,
            max_threads,
        }
        .validate("ResourceBudget::new")
    }

    /// Validate that every ceiling is positive.
    pub fn validate(self, operation: &'static str) -> PidResult<Self> {
        for (resource, value) in [
            ("max_bytes", u128::from(self.max_bytes)),
            (
                "max_pairwise_distances",
                u128::from(self.max_pairwise_distances),
            ),
            ("max_operations_hint", self.max_operations_hint),
            ("max_threads", self.max_threads as u128),
        ] {
            if value == 0 {
                return Err(PidError::ResourceLimitExceeded {
                    operation,
                    resource,
                    requested: 1,
                    limit: 0,
                });
            }
        }
        Ok(self)
    }

    /// Check a deterministic preflight estimate against this budget.
    pub fn check(self, operation: &'static str, estimate: ResourceEstimate) -> PidResult<()> {
        self.validate(operation)?;
        check_limit(
            operation,
            "bytes",
            estimate.estimated_bytes,
            u128::from(self.max_bytes),
        )?;
        check_limit(
            operation,
            "pairwise_distances",
            estimate.pairwise_distances,
            u128::from(self.max_pairwise_distances),
        )?;
        check_limit(
            operation,
            "operations_hint",
            estimate.operations_hint,
            self.max_operations_hint,
        )
    }
}

/// Deterministic memory/complexity preflight attached to report-first APIs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[non_exhaustive]
pub struct ResourceEstimate {
    pub estimated_bytes: u128,
    pub pairwise_distances: u128,
    pub operations_hint: u128,
}

impl ResourceEstimate {
    /// A zero-cost estimate for constant-space operations.
    pub const ZERO: Self = Self {
        estimated_bytes: 0,
        pairwise_distances: 0,
        operations_hint: 0,
    };

    /// Estimate triangular pair storage and pairwise work for `n` observations.
    pub fn triangular_f64(
        operation: &'static str,
        n: usize,
        simultaneous_matrices: usize,
        operations_per_pair: u128,
    ) -> PidResult<Self> {
        let n = n as u128;
        let pairs = n
            .checked_mul(n.saturating_sub(1))
            .and_then(|value| value.checked_div(2))
            .ok_or(PidError::SizeOverflow { operation })?;
        let estimated_bytes = pairs
            .checked_mul(size_of::<f64>() as u128)
            .and_then(|value| value.checked_mul(simultaneous_matrices as u128))
            .ok_or(PidError::SizeOverflow { operation })?;
        let operations_hint = pairs
            .checked_mul(operations_per_pair)
            .ok_or(PidError::SizeOverflow { operation })?;
        Ok(Self {
            estimated_bytes,
            pairwise_distances: pairs,
            operations_hint,
        })
    }

    /// Estimate a contiguous allocation of `elements` values of `T`.
    pub fn contiguous<T>(operation: &'static str, elements: usize) -> PidResult<Self> {
        let estimated_bytes = (elements as u128)
            .checked_mul(size_of::<T>() as u128)
            .ok_or(PidError::SizeOverflow { operation })?;
        Ok(Self {
            estimated_bytes,
            pairwise_distances: 0,
            operations_hint: elements as u128,
        })
    }
}

fn check_limit(
    operation: &'static str,
    resource: &'static str,
    requested: u128,
    limit: u128,
) -> PidResult<()> {
    if requested > limit {
        return Err(PidError::ResourceLimitExceeded {
            operation,
            resource,
            requested,
            limit,
        });
    }
    Ok(())
}

/// Allocate a vector capacity without invoking Rust's infallible allocation path.
pub(crate) fn try_vec_with_capacity<T>(
    operation: &'static str,
    capacity: usize,
    budget: ResourceBudget,
) -> PidResult<Vec<T>> {
    let estimate = ResourceEstimate::contiguous::<T>(operation, capacity)?;
    budget.check(operation, estimate)?;
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: estimate.estimated_bytes,
        })?;
    Ok(values)
}

/// Fallibly construct a filled vector while applying a memory budget.
pub(crate) fn try_vec_filled<T: Clone>(
    operation: &'static str,
    len: usize,
    value: T,
    budget: ResourceBudget,
) -> PidResult<Vec<T>> {
    let mut values = try_vec_with_capacity(operation, len, budget)?;
    values.resize(len, value);
    Ok(values)
}

#[cfg(test)]
mod tests {
    use super::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
    use crate::error::PidError;

    #[test]
    fn triangular_estimate_is_exact_for_four_f64_matrices() {
        let estimate = ResourceEstimate::triangular_f64("test", 5, 4, 3).unwrap();

        assert_eq!(estimate.estimated_bytes, 320);
        assert_eq!(estimate.pairwise_distances, 10);
        assert_eq!(estimate.operations_hint, 30);
    }

    #[test]
    fn budget_rejects_oversized_distance_work_before_allocation() {
        let budget = ResourceBudget {
            max_bytes: 64,
            max_pairwise_distances: 1_000,
            max_operations_hint: 1_000,
            max_threads: 1,
        };
        let estimate = ResourceEstimate::triangular_f64("test", 5, 1, 1).unwrap();

        assert!(matches!(
            budget.check("test", estimate),
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                requested: 80,
                limit: 64,
                ..
            })
        ));
    }

    #[test]
    fn fallible_capacity_obeys_budget() {
        let budget = ResourceBudget {
            max_bytes: 7,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            try_vec_with_capacity::<u64>("test", 1, budget),
            Err(PidError::ResourceLimitExceeded { .. })
        ));
    }
}
