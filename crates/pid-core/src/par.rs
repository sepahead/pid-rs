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

/// Map `f` over `0..n`, collecting the results into a `Vec` **in index order**.
///
/// With the `parallel` feature this evaluates `f` data-parallel across the indices; without it,
/// serially. In both cases the returned vector is `[f(0), f(1), …, f(n-1)]` — identical
/// element-for-element — so callers that reduce in index order get bit-identical results.
///
/// The first `Err` (by the parallel scheduler's discovery, or by index order in the serial
/// path) short-circuits the collect; since the closures used here are deterministic this only
/// changes *which* identical error is surfaced, not the success-path values.
#[cfg(feature = "parallel")]
pub(crate) fn map_index_ordered<T, F>(n: usize, f: F) -> PidResult<Vec<T>>
where
    T: Send,
    F: Fn(usize) -> PidResult<T> + Sync + Send,
{
    use rayon::prelude::*;
    (0..n).into_par_iter().map(f).collect()
}

#[cfg(not(feature = "parallel"))]
pub(crate) fn map_index_ordered<T, F>(n: usize, f: F) -> PidResult<Vec<T>>
where
    F: Fn(usize) -> PidResult<T>,
{
    (0..n).map(f).collect()
}

/// Map `f` over a slice, collecting the results into a `Vec` **in index order**.
///
/// Like [`map_index_ordered`] but for an already-materialized input slice (e.g. a list of
/// pre-drawn bootstrap resample plans). With the `parallel` feature this evaluates `f`
/// data-parallel across the elements; without it, serially. The returned vector is
/// `[f(&xs[0]), …, f(&xs[len-1])]` in either case, so any downstream index-ordered reduction
/// is bit-identical between the two paths.
#[cfg(feature = "parallel")]
pub(crate) fn slice_map_index_ordered<I, R, F>(xs: &[I], f: F) -> Vec<R>
where
    I: Sync,
    R: Send,
    F: Fn(&I) -> R + Sync + Send,
{
    use rayon::prelude::*;
    xs.par_iter().map(f).collect()
}

#[cfg(not(feature = "parallel"))]
pub(crate) fn slice_map_index_ordered<I, R, F>(xs: &[I], f: F) -> Vec<R>
where
    F: Fn(&I) -> R,
{
    xs.iter().map(f).collect()
}
