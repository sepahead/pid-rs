//! Index-ordered parallel map helpers.
//!
//! The `parallel` (rayon) feature is a *throughput* optimization, not a change of estimator.
//! Every parallel path in this crate must be **bit-for-bit identical** to its serial path
//! (`f64::to_bits` equality), which is non-negotiable per the project conventions.
//!
//! The recipe that guarantees this:
//! 1. The mapped closure is **pure** — it reads shared `&` data and allocates its own scratch,
//!    so its result for index `i` does not depend on which thread runs it or in what order.
//! 2. Results are collected **into a `Vec` indexed by `i`** (rayon's `IndexedParallelIterator`
//!    `collect` preserves index order), so the returned vector is identical regardless of the
//!    parallel schedule.
//! 3. Any downstream reduction (e.g. a sum) is then performed over that vector in **index
//!    order** by the caller — never inside the parallel reduce — so floating-point summation
//!    order is fixed.
//!
//! With (1)+(2)+(3) the only difference between the serial and parallel paths is *who* computes
//! each independent term, never *what value* is produced or *in what order* terms are combined.

use crate::error::PidResult;
#[cfg(feature = "experimental-pipelines")]
use crate::resource::ResourceEstimate;
use crate::resource::{try_vec_with_capacity, ResourceBudget};

/// Explicit stack reservation requested for each Rayon worker created by this crate.
#[cfg(feature = "parallel")]
pub(crate) const WORKER_STACK_BYTES: usize = 2 * 1024 * 1024;

/// Run a closure inside a Rayon pool capped by the report's declared thread budget.
#[cfg(feature = "parallel")]
pub(crate) fn with_thread_budget<R, F>(max_threads: usize, f: F) -> PidResult<R>
where
    R: Send,
    F: FnOnce() -> PidResult<R> + Send,
{
    if max_threads == 0 {
        return Err(crate::error::PidError::ResourceLimitExceeded {
            operation: "parallel thread pool",
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    let pool = rayon::ThreadPoolBuilder::new()
        .num_threads(max_threads)
        .stack_size(WORKER_STACK_BYTES)
        .build()
        .map_err(|_| crate::error::PidError::ParallelExecutionFailed {
            operation: "parallel thread pool",
        })?;
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| pool.install(f))).map_err(|_| {
        crate::error::PidError::ParallelExecutionFailed {
            operation: "parallel worker",
        }
    })?
}

#[cfg(not(feature = "parallel"))]
pub(crate) fn with_thread_budget<R, F>(max_threads: usize, f: F) -> PidResult<R>
where
    F: FnOnce() -> PidResult<R>,
{
    if max_threads == 0 {
        return Err(crate::error::PidError::ResourceLimitExceeded {
            operation: "serial execution",
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    f()
}

/// Map `f` over `0..n`, collecting the results into a `Vec` **in index order**.
///
/// With the `parallel` feature this evaluates `f` data-parallel across the indices; without it,
/// serially. In both cases the returned vector is `[f(0), f(1), …, f(n-1)]` — identical
/// element-for-element — so callers that reduce in index order get bit-identical results.
///
/// If multiple indices fail, both implementations return the lowest-index `Err`. The parallel
/// path first collects indexed `Result`s and then propagates errors sequentially; this makes
/// structured diagnostics deterministic rather than dependent on scheduler discovery order.
#[cfg(feature = "parallel")]
pub(crate) fn map_index_ordered<T, F>(n: usize, f: F) -> PidResult<Vec<T>>
where
    T: Send,
    F: Fn(usize) -> PidResult<T> + Sync + Send,
{
    use rayon::prelude::*;
    let mut indexed_results = try_vec_with_capacity(
        "parallel ordered map intermediate results",
        n,
        ResourceBudget::default(),
    )?;
    (0..n)
        .into_par_iter()
        .map(f)
        .collect_into_vec(&mut indexed_results);

    let mut values =
        try_vec_with_capacity("parallel ordered map results", n, ResourceBudget::default())?;
    for result in indexed_results {
        values.push(result?);
    }
    Ok(values)
}

#[cfg(not(feature = "parallel"))]
pub(crate) fn map_index_ordered<T, F>(n: usize, f: F) -> PidResult<Vec<T>>
where
    F: Fn(usize) -> PidResult<T>,
{
    let mut values =
        try_vec_with_capacity("serial ordered map results", n, ResourceBudget::default())?;
    for index in 0..n {
        values.push(f(index)?);
    }
    Ok(values)
}

/// Map `f` over a slice, collecting the results into a `Vec` **in index order**.
///
/// Like [`map_index_ordered`] but for an already-materialized input slice (e.g. a list of
/// pre-drawn bootstrap resample plans). With the `parallel` feature this evaluates `f`
/// data-parallel across the elements; without it, serially. The returned vector is
/// `[f(&xs[0]), …, f(&xs[len-1])]` in either case, so any downstream index-ordered reduction
/// is bit-identical between the two paths.
#[cfg(feature = "experimental-pipelines")]
fn slice_map_resource_estimate<R>(
    len: usize,
    _budget: ResourceBudget,
    simultaneous_worker_heap_bytes: u128,
) -> PidResult<ResourceEstimate> {
    let output_bytes = (len as u128)
        .checked_mul(std::mem::size_of::<R>() as u128)
        .ok_or(crate::error::PidError::SizeOverflow {
            operation: "ordered slice map",
        })?;
    #[cfg(feature = "parallel")]
    let stack_bytes = (_budget.max_threads as u128)
        .checked_mul(WORKER_STACK_BYTES as u128)
        .ok_or(crate::error::PidError::SizeOverflow {
            operation: "ordered slice map",
        })?;
    #[cfg(not(feature = "parallel"))]
    let stack_bytes = 0;
    let concurrent_workers: u128 = if len == 0 {
        0_u128
    } else {
        #[cfg(feature = "parallel")]
        {
            len.min(_budget.max_threads) as u128
        }
        #[cfg(not(feature = "parallel"))]
        {
            1_u128
        }
    };
    let worker_heap_bytes = concurrent_workers
        .checked_mul(simultaneous_worker_heap_bytes)
        .ok_or(crate::error::PidError::SizeOverflow {
            operation: "ordered slice map",
        })?;
    let estimated_bytes = output_bytes
        .checked_add(stack_bytes)
        .and_then(|bytes| bytes.checked_add(worker_heap_bytes))
        .ok_or(crate::error::PidError::SizeOverflow {
            operation: "ordered slice map",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: 0,
        operations_hint: len as u128,
    })
}

/// Map a materialized schedule in index order under an explicit aggregate execution budget.
///
/// `simultaneous_worker_heap_bytes` is the caller's conservative peak heap estimate for one
/// invocation of `f`. Parallel builds charge it once per concurrently active element and also
/// charge every explicitly reserved Rayon worker stack. The result allocation itself is
/// fallible. A worker panic or private-pool failure becomes a structured error.
#[cfg(all(feature = "experimental-pipelines", feature = "parallel"))]
pub(crate) fn slice_map_index_ordered<I, R, F>(
    xs: &[I],
    budget: ResourceBudget,
    simultaneous_worker_heap_bytes: u128,
    f: F,
) -> PidResult<Vec<R>>
where
    I: Sync,
    R: Send,
    F: Fn(&I) -> R + Sync + Send,
{
    use rayon::prelude::*;
    budget.check(
        "ordered slice map",
        slice_map_resource_estimate::<R>(xs.len(), budget, simultaneous_worker_heap_bytes)?,
    )?;
    let mut values = try_vec_with_capacity("ordered slice map results", xs.len(), budget)?;
    with_thread_budget(budget.max_threads, || {
        xs.par_iter().map(f).collect_into_vec(&mut values);
        Ok(())
    })?;
    Ok(values)
}

#[cfg(all(feature = "experimental-pipelines", not(feature = "parallel")))]
pub(crate) fn slice_map_index_ordered<I, R, F>(
    xs: &[I],
    budget: ResourceBudget,
    simultaneous_worker_heap_bytes: u128,
    f: F,
) -> PidResult<Vec<R>>
where
    F: Fn(&I) -> R,
{
    budget.check(
        "ordered slice map",
        slice_map_resource_estimate::<R>(xs.len(), budget, simultaneous_worker_heap_bytes)?,
    )?;
    let mut values = try_vec_with_capacity("ordered slice map results", xs.len(), budget)?;
    for value in xs {
        values.push(f(value));
    }
    Ok(values)
}

#[cfg(test)]
mod tests {
    use super::map_index_ordered;
    #[cfg(feature = "experimental-pipelines")]
    use super::slice_map_index_ordered;
    use crate::error::{PidError, PidResult};
    #[cfg(feature = "experimental-pipelines")]
    use crate::resource::ResourceBudget;

    #[test]
    fn map_index_ordered_returns_the_lowest_index_error() {
        let outcome: PidResult<Vec<usize>> = map_index_ordered(64, |index| {
            if index == 3 || index == 41 {
                Err(PidError::ShapeMismatch {
                    context: "map_index_ordered test",
                    expected_len: 0,
                    actual_len: index,
                })
            } else {
                Ok(index)
            }
        });

        assert!(matches!(
            outcome,
            Err(PidError::ShapeMismatch { actual_len: 3, .. })
        ));
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn slice_map_rejects_a_tiny_aggregate_budget_before_execution() {
        use std::sync::atomic::{AtomicBool, Ordering};

        let budget = ResourceBudget {
            max_bytes: 1,
            max_pairwise_distances: 1,
            max_operations_hint: 10,
            max_threads: 1,
        };
        let called = AtomicBool::new(false);

        let result = slice_map_index_ordered(&[1_u64, 2], budget, 0, |value| {
            called.store(true, Ordering::Relaxed);
            *value
        });

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded { .. })
        ));
        assert!(!called.load(Ordering::Relaxed));
    }
}
