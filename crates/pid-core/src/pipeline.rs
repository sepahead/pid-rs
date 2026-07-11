//! Pipeline functions that compose PLS projection, PID decomposition, and bootstrap
//! uncertainty quantification.
//!
//! These are convenience entry points for the common VLA analysis workflow:
//!
//! 1. `pls_project_then_pid3` — fit PLS on high-dimensional embeddings, project into a
//!    low-dimensional task-relevant subspace, then run the continuous 3-source I^sx_∩ PID
//!    ([`pid3_isx`]; NOT the discrete SxPID of the `sxpid` module).
//! 2. `bootstrap_pid3` — deprecated with-replacement PID3 bootstrap retained for compatibility;
//!    duplicated kNN samples make its intervals unreliable and now commonly trigger a structured
//!    ambiguous-shell error.

use crate::bootstrap::BootstrapConfig;
use crate::concat_horiz;
use crate::discrete_pid::discrete_pid3;
use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use crate::pid2::{pid2_isx, Pid2Config, Pid2Result};
use crate::pid3::{pid3_isx, Antichain3, Pid3Config, Pid3Result};
use crate::pls::PlsProjector;
use crate::preprocess::SplitMix64;
use crate::stats::{finite_mean, finite_mean_std_population, finite_mean_std_sample};
use crate::sxpid::quantized_sxpid2;

fn try_vec_with_capacity<T>(capacity: usize, context: &'static str) -> PidResult<Vec<T>> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(capacity)
        .map_err(|_| PidError::InvalidConfig {
            context,
            message: "requested resampling allocation is too large",
        })?;
    Ok(values)
}

// ── PLS → PID3 ─────────────────────────────────────────────────────────────

/// Configuration for [`pls_project_then_pid3`].
#[derive(Debug, Clone)]
pub struct PlsPid3Config {
    /// Number of PLS latent components to extract (applied to each source and target).
    pub pls_components: usize,
    /// Full PID3 estimator configuration, including its experimental mixed-lattice opt-in.
    pub pid_cfg: Pid3Config,
    /// Explicit opt-in to fitting supervised PLS and estimating PID on the same rows.
    ///
    /// This workflow is exploratory: target-adaptive fitting on the evaluation sample can make
    /// downstream atoms optimistic. For inference, fit each [`PlsProjector`] on training rows and
    /// call [`pid3_isx`] only on separately transformed evaluation rows.
    pub exploratory_allow_same_sample_fit: bool,
}

/// Output of [`pls_project_then_pid3`].
#[derive(Debug, Clone)]
pub struct PlsPid3Result {
    /// PID decomposition on the PLS-projected embeddings.
    pub pid: Pid3Result,
    /// Number of PLS components used.
    pub pls_components: usize,
    /// Input column counts for V, L, D, A before projection.
    pub input_dims: [usize; 4],
    /// Output column count after projection (= pls_components).
    pub projected_dim: usize,
}

/// Fit per-source PLS projectors (each source → A) to reduce dimensionality, then
/// run the continuous 3-source I^sx_∩ PID ([`pid3_isx`]) on the projected embeddings.
/// (This is the Ehrlich-et-al.-2024 kNN estimator — not the discrete, IDTxl-validated
/// SxPID in the `sxpid` module; the two must not be conflated when reporting atoms.)
///
/// Each of V, L, D is projected through its own PLS model fitted with A as target.
/// A is projected through a PLS fitted with the concatenated VLD as target.
/// All four projections yield `pls_components`-dimensional representations.
///
/// The three sources (V, L, D) must share the same row count `n`, and A must also have `n` rows.
///
/// # Exploratory same-sample fit
///
/// This function fits PLS on **all** provided data and therefore requires
/// [`PlsPid3Config::exploratory_allow_same_sample_fit`] to be `true`. That acknowledgement does
/// not make the output suitable for inference. For proper train/test separation, call
/// [`PlsProjector::fit`] on training data only, then [`PlsProjector::transform`] on held-out rows,
/// and finally [`pid3_isx`] on the held-out projected matrices. Hyperparameter selection must be
/// nested inside the training split as well.
pub fn pls_project_then_pid3(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    cfg: &PlsPid3Config,
) -> PidResult<PlsPid3Result> {
    let n = v.nrows();
    if l.nrows() != n || d.nrows() != n || a.nrows() != n {
        let right_rows = if l.nrows() != n {
            l.nrows()
        } else if d.nrows() != n {
            d.nrows()
        } else {
            a.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context: "pls_project_then_pid3",
            left_rows: n,
            right_rows,
        });
    }
    if !cfg.exploratory_allow_same_sample_fit {
        return Err(PidError::InvalidConfig {
            context: "pls_project_then_pid3",
            message: "same-sample supervised PLS followed by PID is exploratory; set exploratory_allow_same_sample_fit=true to acknowledge, or fit PLS on training rows and estimate PID on held-out transformed rows",
        });
    }

    // Fit a per-source PLS projector: each source S_i → A.
    // This gives each source its own low-d task-relevant representation.
    let v_proj = PlsProjector::fit(v, a, cfg.pls_components)?.transform(v)?;
    let l_proj = PlsProjector::fit(l, a, cfg.pls_components)?.transform(l)?;
    let d_proj = PlsProjector::fit(d, a, cfg.pls_components)?.transform(d)?;
    // For A, fit a PLS using the concatenated VLD as target so that the
    // projected target captures task-relevant variance from the sources.
    let vld = concat_horiz(concat_horiz(v, l)?.as_ref(), d)?;
    let a_proj = PlsProjector::fit(a, vld.as_ref(), cfg.pls_components)?.transform(a)?;

    let pid = pid3_isx(
        v_proj.as_ref(),
        l_proj.as_ref(),
        d_proj.as_ref(),
        a_proj.as_ref(),
        &cfg.pid_cfg,
    )?;

    Ok(PlsPid3Result {
        pid,
        pls_components: cfg.pls_components,
        input_dims: [v.ncols(), l.ncols(), d.ncols(), a.ncols()],
        projected_dim: cfg.pls_components,
    })
}

// ── Bootstrap PID3 ─────────────────────────────────────────────────────────

/// Legacy per-atom with-replacement resampling summary for a 3-source PID decomposition.
#[derive(Debug, Clone)]
pub struct Pid3BootstrapAtom {
    /// The antichain identifying this atom on the PID lattice.
    pub antichain: Antichain3,
    /// Point estimate on the original (un-resampled) data.
    pub point_estimate: f64,
    /// Mean of the with-replacement resampling distribution.
    pub boot_mean: f64,
    /// Sample standard deviation of the resampling distribution; not a generally calibrated kNN
    /// standard error.
    pub boot_se: f64,
    /// Lower raw resampling percentile; not a generally calibrated kNN confidence bound.
    pub ci_low: f64,
    /// Upper raw resampling percentile; not a generally calibrated kNN confidence bound.
    pub ci_high: f64,
}

/// Legacy result of the deprecated [`bootstrap_pid3`].
#[derive(Debug, Clone)]
pub struct BootstrapPid3Result {
    /// Point estimate PID result on the original data.
    pub point_estimate: Pid3Result,
    /// Legacy raw resampling summaries for each atom (same canonical order as
    /// `point_estimate.atoms`).
    pub atoms: Vec<Pid3BootstrapAtom>,
    /// Number of bootstrap resamples attempted.
    pub n_boot: usize,
    /// Number of complete finite resamples. Successful results always have `n_valid == n_boot`.
    pub n_valid: usize,
    /// Block size used.
    pub block_size: usize,
}

/// Deprecated with-replacement percentile summaries for every atom of a 3-source PID
/// decomposition.
///
/// Rows of (V, L, D, A) are resampled jointly (same block indices across all four matrices),
/// preserving any cross-variable dependence. `pid3_isx` is recomputed on each resample, and
/// raw percentiles are extracted for each of the 18 atoms.
///
/// # Deprecated for kNN inference
///
/// This is a with-replacement moving-block bootstrap. Repeated blocks duplicate rows, which can
/// make the continuous estimator's k-th-neighbor shell ambiguous; even resamples that happen to
/// remain finite do not provide a generally reliable KSG uncertainty guarantee. Prefer
/// [`bootstrap_rows_stats`] with [`RowResampleScheme::Subsample`] and report its smaller effective
/// sample size and raw quantiles as diagnostics, not calibrated confidence bounds. A failed
/// resample invalidates the summary rather than being selectively omitted.
///
/// # Errors
///
/// Returns [`PidError::RowCountMismatch`] if V, L, D, A do not share a row count, and
/// [`PidError::InvalidConfig`] if `block_size` is not in `1..n`, `n_boot < 2`, `alpha` is not in
/// the open interval `(0, 1)`, or the requested schedule/distribution cannot be reserved safely.
/// Returns [`PidError::NumericalInstability`] if the original decomposition or any resampled
/// decomposition is not complete and finite, and [`PidError::AmbiguousKthNeighborShell`] when a
/// duplicate-induced positive boundary tie makes the continuous rank formula undefined.
#[deprecated(
    since = "0.5.0",
    note = "with-replacement resampling invalidates kNN neighborhoods; use bootstrap_rows_stats with RowResampleScheme::Subsample and treat its raw m-sample quantiles as diagnostics"
)]
pub fn bootstrap_pid3(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    boot_cfg: &BootstrapConfig,
) -> PidResult<BootstrapPid3Result> {
    let n = v.nrows();
    if l.nrows() != n || d.nrows() != n || a.nrows() != n {
        let right_rows = if l.nrows() != n {
            l.nrows()
        } else if d.nrows() != n {
            d.nrows()
        } else {
            a.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context: "bootstrap_pid3",
            left_rows: n,
            right_rows,
        });
    }
    if boot_cfg.block_size == 0 || boot_cfg.block_size >= n {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_pid3",
            message: "block_size must be in 1..n",
        });
    }
    if boot_cfg.n_boot < 2 {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_pid3",
            message: "n_boot must be >= 2 to estimate bootstrap variance",
        });
    }
    // `alpha` indexes percentile bounds below; outside (0,1) it yields an out-of-range
    // index (alpha >= 2 panics) or an inverted CI (alpha in (1,2)). Reject up front.
    if !(boot_cfg.alpha > 0.0 && boot_cfg.alpha < 1.0) {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_pid3",
            message: "alpha must be in the open interval (0, 1)",
        });
    }

    // Allocate the outer schedule fallibly before running the expensive point estimator.
    let mut resample_indices =
        try_vec_with_capacity::<Vec<usize>>(boot_cfg.n_boot, "bootstrap_pid3")?;

    let dv = v.ncols();
    let dl = l.ncols();
    let dd = d.ncols();
    let da = a.ncols();

    // Point estimate on original data.
    let point_estimate = pid3_isx(v, l, d, a, pid_cfg)?;
    let n_atoms = point_estimate.atoms.len();
    if point_estimate
        .atoms
        .iter()
        .any(|atom| !atom.value.is_finite())
    {
        return Err(PidError::NumericalInstability {
            context: "bootstrap_pid3 point estimate",
        });
    }

    // Draw every resample's row-index set serially so the RNG stream is unchanged regardless of
    // whether the (expensive) `pid3_isx` evaluations later run in parallel.
    //
    // True moving-block bootstrap (Künsch 1989): block starts drawn uniformly over ALL
    // `n − block_size + 1` overlapping positions — every row is reachable, including the
    // `n % block_size` tail — with `⌈n/block_size⌉` blocks concatenated and truncated to `n`
    // rows. (`block_size` is in `1..n`, so `n_starts >= 2`.)
    let n_starts = n - boot_cfg.block_size + 1;
    let blocks_per_resample = n.div_ceil(boot_cfg.block_size);
    let mut rng = SplitMix64::new(boot_cfg.seed);
    for _ in 0..boot_cfg.n_boot {
        let mut indices = try_vec_with_capacity(n, "bootstrap_pid3")?;
        'blocks: for _ in 0..blocks_per_resample {
            let block_start = uniform_index(&mut rng, n_starts);
            for j in 0..boot_cfg.block_size {
                indices.push(block_start + j);
                if indices.len() == n {
                    break 'blocks;
                }
            }
        }
        resample_indices.push(indices);
    }

    // Evaluate PID on each resample, collected **in resample order**. Each closure reads the
    // shared (immutable) inputs and allocates its own owned resample matrices, so it is pure;
    // collecting by index and only then reducing keeps the parallel path bit-identical.
    let per_resample: Vec<PidResult<Vec<f64>>> =
        crate::par::slice_map_index_ordered(&resample_indices, |indices| {
            let resample = |mat: MatRef<'_>, dim: usize| -> PidResult<MatOwned> {
                let data_len = indices
                    .len()
                    .checked_mul(dim)
                    .ok_or(PidError::InvalidConfig {
                        context: "bootstrap_pid3",
                        message: "resampled matrix length overflow",
                    })?;
                let mut data = try_vec_with_capacity(data_len, "bootstrap_pid3")?;
                for &i in indices {
                    data.extend_from_slice(mat.row(i));
                }
                MatOwned::new(data, indices.len(), dim)
            };

            let vr = resample(v, dv)?;
            let lr = resample(l, dl)?;
            let dr = resample(d, dd)?;
            let ar = resample(a, da)?;

            let result = pid3_isx(vr.as_ref(), lr.as_ref(), dr.as_ref(), ar.as_ref(), pid_cfg)?;
            let values: Vec<f64> = result.atoms.iter().map(|atom| atom.value).collect();
            if values.len() != n_atoms || values.iter().any(|value| !value.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context: "bootstrap_pid3 resample",
                });
            }
            Ok(values)
        });

    // boot_values[atom_idx][boot_idx], filled in resample order (identical to the serial push
    // order), so all downstream summaries are bit-identical.
    let mut boot_values = try_vec_with_capacity::<Vec<f64>>(n_atoms, "bootstrap_pid3")?;
    for _ in 0..n_atoms {
        boot_values.push(try_vec_with_capacity(boot_cfg.n_boot, "bootstrap_pid3")?);
    }
    for atom_vals in per_resample {
        let atom_vals = atom_vals?;
        for (idx, &val) in atom_vals.iter().enumerate() {
            boot_values[idx].push(val);
        }
    }
    let n_valid = boot_cfg.n_boot;

    // Build per-atom bootstrap summaries.
    let alpha = boot_cfg.alpha;
    let atoms: Vec<Pid3BootstrapAtom> = point_estimate
        .atoms
        .iter()
        .enumerate()
        .map(|(idx, atom)| -> PidResult<Pid3BootstrapAtom> {
            let mut values = boot_values[idx].clone();
            debug_assert_eq!(values.len(), boot_cfg.n_boot);
            debug_assert!(values.iter().all(|value| value.is_finite()));
            values.sort_by(f64::total_cmp);
            let m = values.len();
            let (mean, se) = finite_mean_std_sample(&values, "bootstrap_pid3 summary")?;
            let lo_idx = (((alpha / 2.0) * m as f64).floor() as usize).min(m - 1);
            let hi_idx = (((1.0 - alpha / 2.0) * m as f64).ceil() as usize)
                .saturating_sub(1)
                .min(m - 1);
            Ok(Pid3BootstrapAtom {
                antichain: atom.antichain,
                point_estimate: atom.value,
                boot_mean: mean,
                boot_se: se,
                ci_low: values[lo_idx],
                ci_high: values[hi_idx],
            })
        })
        .collect::<PidResult<_>>()?;

    Ok(BootstrapPid3Result {
        point_estimate,
        atoms,
        n_boot: boot_cfg.n_boot,
        n_valid,
        block_size: boot_cfg.block_size,
    })
}

// ── Permutation test ───────────────────────────────────────────────────────────

/// How a resampling null rearranges the selected variable's rows.
///
/// The choice decides which null hypothesis the test actually simulates:
///
/// - [`PermutationScheme::FullShuffle`] draws an independent Fisher–Yates permutation
///   per resample. This gives the usual Monte Carlo permutation test when rows are
///   **exchangeable (i.i.d.)**. On autocorrelated trajectory data it destroys the
///   shuffled variable's *own* serial dependence, so the null is easier than the data
///   and p-values can become **anti-conservative**.
/// - [`PermutationScheme::BlockShuffle`] partitions the series into fixed, equal-sized,
///   contiguous blocks and Fisher–Yates shuffles the blocks while preserving row order
///   inside each block. Block permutations are sampled with replacement and form a
///   finite transformation group, so the add-one result is a Monte Carlo permutation
///   p-value when the **whole blocks are exchangeable** under the null. It is not exact
///   when dependence remains between blocks or their positions are not exchangeable.
///   The permutation APIs reject the whole inference if any transform fails or returns
///   a non-finite statistic, so they never select a transformation-dependent subset.
/// - [`PermutationScheme::CircularShift`] rotates the variable's rows by a seeded
///   pseudorandom offset `k ∈ [min_shift, n − min_shift]`. This preserves the
///   variable's internal autocorrelation exactly (up to the single wrap seam) while
///   breaking its alignment with the other variables — a dependence-aware surrogate
///   for stationary series. Because the restricted offsets exclude the identity and do
///   not form a transformation group, the reported tail fraction is an **approximate
///   stationary-surrogate score**, not an exact randomization-test p-value. Offsets are sampled
///   with replacement, so the score's numerical floor is `1 / (n_perm + 1)`, not a
///   resolution bound derived from the number of distinct offsets.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PermutationScheme {
    /// Independent full-row Fisher–Yates shuffle (exchangeable/i.i.d. rows only).
    FullShuffle,
    /// Fisher–Yates shuffle of fixed, contiguous blocks, preserving within-block order.
    ///
    /// Requires `block_size >= 1`, `n % block_size == 0`, and at least two blocks.
    /// Draws are sampled with replacement and are uniform over the permutations of the
    /// `n / block_size` block labels, including the identity. The add-one result is a
    /// Monte Carlo permutation p-value under exchangeability of the whole blocks,
    /// provided every transform evaluates successfully and finitely (otherwise the
    /// permutation API returns an error). Choosing a block size does not itself make
    /// dependent or nonstationary blocks exchangeable.
    BlockShuffle {
        /// Number of consecutive rows in each fixed block.
        block_size: usize,
    },
    /// Circular time-shift by a seeded pseudorandom offset
    /// `k ∈ [min_shift, n − min_shift]`.
    ///
    /// Set `min_shift` to at least the data's dependence length — the same order as
    /// the block size you would give the moving-block bootstrap — so no resample is
    /// nearly aligned with the original. Requires `min_shift ≥ 1` and
    /// `n ≥ 2·min_shift + 1` (at least two distinct offsets).
    CircularShift {
        /// Minimum rotation, in rows, enforced from both ends of the series.
        min_shift: usize,
    },
}

/// Signed one-sided alternative for permutation tests.
///
/// The tail is applied to the statistic exactly as supplied: no absolute value, recentering, or
/// implicit two-sided construction is performed. For signed PID atoms, choose the direction from
/// the scientific alternative before inspecting the null distribution.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PermutationTail {
    /// Count null statistics greater than or equal to the observed statistic.
    Upper,
    /// Count null statistics less than or equal to the observed statistic.
    Lower,
}

impl PermutationTail {
    #[inline]
    fn contains(self, null_value: f64, observed: f64) -> bool {
        match self {
            Self::Upper => null_value >= observed,
            Self::Lower => null_value <= observed,
        }
    }
}

/// Validate `scheme` against the sample count `n` (once, before any resampling).
fn validate_permutation_scheme(
    context: &'static str,
    scheme: PermutationScheme,
    n: usize,
) -> PidResult<()> {
    match scheme {
        PermutationScheme::FullShuffle => {}
        PermutationScheme::BlockShuffle { block_size } => {
            if block_size == 0 {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "BlockShuffle block_size must be >= 1",
                });
            }
            if n % block_size != 0 {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "BlockShuffle requires n % block_size == 0",
                });
            }
            if n / block_size < 2 {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "BlockShuffle requires at least two blocks",
                });
            }
        }
        PermutationScheme::CircularShift { min_shift } => {
            if min_shift == 0 {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "CircularShift min_shift must be >= 1",
                });
            }
            let Some(min_rows) = min_shift.checked_mul(2).and_then(|v| v.checked_add(1)) else {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "CircularShift min_shift is too large",
                });
            };
            if n < min_rows {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "CircularShift needs n >= 2*min_shift + 1 (>= two distinct offsets)",
                });
            }
        }
    }
    Ok(())
}

/// Draw an unbiased integer from `0..upper_exclusive`.
fn uniform_index(rng: &mut SplitMix64, upper_exclusive: usize) -> usize {
    debug_assert!(upper_exclusive > 0);
    let bound = upper_exclusive as u64;
    let threshold = bound.wrapping_neg() % bound;
    loop {
        let draw = rng.next_u64();
        if draw >= threshold {
            return (draw % bound) as usize;
        }
    }
}

/// Draw one row-index rearrangement under `scheme`.
///
/// Full-row and block shuffles use rejection-sampled bounded draws, making every Fisher–Yates
/// choice exactly uniform over the seeded 64-bit generator. Circular shifts use the same bounded
/// draw for their admissible offset range.
fn draw_permutation(
    scheme: PermutationScheme,
    n: usize,
    rng: &mut SplitMix64,
    context: &'static str,
) -> PidResult<Vec<usize>> {
    match scheme {
        PermutationScheme::FullShuffle => {
            let mut perm = try_vec_with_capacity(n, context)?;
            perm.extend(0..n);
            for i in (1..n).rev() {
                let j = uniform_index(rng, i + 1);
                perm.swap(i, j);
            }
            Ok(perm)
        }
        PermutationScheme::BlockShuffle { block_size } => {
            let n_blocks = n / block_size; // validated: exact division and >= 2
            let mut blocks = try_vec_with_capacity(n_blocks, context)?;
            blocks.extend(0..n_blocks);
            for i in (1..n_blocks).rev() {
                let j = uniform_index(rng, i + 1);
                blocks.swap(i, j);
            }

            let mut perm = try_vec_with_capacity(n, context)?;
            for block in blocks {
                let start = block * block_size;
                perm.extend(start..start + block_size);
            }
            Ok(perm)
        }
        PermutationScheme::CircularShift { min_shift } => {
            let span = n - min_shift - min_shift + 1; // validated: >= 2
            let k = min_shift + uniform_index(rng, span);
            let wrap_at = n - k;
            let mut perm = try_vec_with_capacity(n, context)?;
            for i in 0..n {
                perm.push(if i >= wrap_at { i - wrap_at } else { i + k });
            }
            Ok(perm)
        }
    }
}

/// Result of a permutation test on PID atoms.
#[derive(Debug, Clone)]
pub struct PermutationPid3Atom {
    pub antichain: Antichain3,
    pub observed: f64,
    /// Signed one-sided add-one tail fraction. The comparison direction is recorded in
    /// [`PermutationPid3Result::tail`] and the null provenance in
    /// [`PermutationPid3Result::scheme`].
    pub p_value: f64,
    /// Number of complete, finite permutations in the null distribution. Successful
    /// results always have `n_valid == n_perm`; a failed or
    /// non-finite permutation invalidates the whole inference instead of being selectively
    /// omitted. For [`PermutationScheme::CircularShift`], the resulting tail fraction is
    /// an approximate surrogate score rather than an exact p-value.
    pub n_valid: usize,
}

/// Result of [`permutation_pid3`].
#[derive(Debug, Clone)]
pub struct PermutationPid3Result {
    pub atoms: Vec<PermutationPid3Atom>,
    /// Number of complete, finite permutations used for every atom. If any requested
    /// permutation fails, no result is returned.
    pub n_perm: usize,
    pub source_shuffled: usize,
    /// Resampling scheme that generated the null distribution.
    pub scheme: PermutationScheme,
    /// Signed one-sided tail used for every atom's p-value or surrogate score.
    pub tail: PermutationTail,
}

/// Upper-tail permutation test for PID atoms: shuffles rows of a single source to build a null
/// distribution, then computes signed one-sided p-values for each atom.
///
/// `source_idx` selects which source to shuffle (0=V, 1=L, 2=D). The selected scheme defines an
/// empirical null in which that source's rows or blocks are exchangeable relative to the aligned
/// joint of the other sources and target. Each observed atom is compared with its own null
/// distribution; shared-exclusions atoms are not generally expected to be zero under an
/// independent-source null.
///
/// Uses [`PermutationScheme::FullShuffle`], which assumes **exchangeable (i.i.d.) rows**;
/// use [`permutation_pid3_with`] with [`PermutationScheme::BlockShuffle`] when fixed,
/// equal-sized whole blocks are exchangeable, or [`PermutationScheme::CircularShift`]
/// for a stationary-series surrogate whose tail fraction is approximate.
/// Every requested permutation must produce a complete, finite PID decomposition.
///
/// # Errors
///
/// Returns an error for invalid inputs or configuration, if the requested null distribution
/// cannot be reserved safely, or if the observed PID or any permuted PID cannot be computed
/// completely and finitely.
#[allow(clippy::too_many_arguments)]
pub fn permutation_pid3(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    seed: u64,
) -> PidResult<PermutationPid3Result> {
    permutation_pid3_with(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        seed,
        PermutationScheme::FullShuffle,
    )
}

/// [`permutation_pid3`] with an explicit [`PermutationScheme`] and the compatibility-default
/// [`PermutationTail::Upper`] alternative.
///
/// With [`PermutationScheme::FullShuffle`] this is bit-identical to
/// [`permutation_pid3`] at the same seed. [`PermutationScheme::BlockShuffle`] preserves
/// order within fixed blocks and gives a Monte Carlo permutation p-value under
/// whole-block exchangeability when every requested transform succeeds and is finite.
/// [`PermutationScheme::CircularShift`] preserves the shuffled source's own
/// autocorrelation by rotation, but its restricted shifts are not a permutation group,
/// so the reported tail fraction is not an exact randomization-test p-value.
///
/// Every requested transform must produce a complete, finite PID decomposition. A failed
/// or non-finite transform invalidates the whole inference rather than being selectively
/// omitted from an atom's null distribution.
///
/// # Errors
///
/// Returns an error for an invalid source, permutation count, or scheme; if the requested null
/// distribution cannot be reserved safely; if the observed PID cannot be computed finitely; or
/// if any permuted PID fails or contains a non-finite atom.
#[allow(clippy::too_many_arguments)]
pub fn permutation_pid3_with(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    seed: u64,
    scheme: PermutationScheme,
) -> PidResult<PermutationPid3Result> {
    permutation_pid3_with_tail(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        seed,
        scheme,
        PermutationTail::Upper,
    )
}

/// Permutation test for PID atoms with an explicit null scheme and signed one-sided tail.
///
/// [`PermutationTail::Upper`] uses
/// `(1 + #{permutation >= observed}) / (1 + n_perm)` and is bit-identical to
/// [`permutation_pid3_with`] at the same seed and scheme. [`PermutationTail::Lower`] uses the
/// corresponding `<= observed` comparison. PID atoms can be signed; this API does not take
/// absolute values or infer a two-sided alternative.
///
/// Every requested transform must produce a complete, finite PID decomposition. A failed or
/// non-finite transform invalidates the whole inference rather than being selectively omitted
/// from an atom's null distribution.
///
/// # Errors
///
/// Returns an error for an invalid source, permutation count, or scheme; if the requested null
/// distribution cannot be reserved safely; if the observed PID cannot be computed finitely; or
/// if any permuted PID fails or contains a non-finite atom.
#[allow(clippy::too_many_arguments)]
pub fn permutation_pid3_with_tail(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    seed: u64,
    scheme: PermutationScheme,
    tail: PermutationTail,
) -> PidResult<PermutationPid3Result> {
    if source_idx > 2 {
        return Err(PidError::InvalidConfig {
            context: "permutation_pid3",
            message: "source_idx must be 0, 1, or 2",
        });
    }
    let n = v.nrows();
    if n_perm == 0 {
        return Err(PidError::InvalidConfig {
            context: "permutation_pid3",
            message: "n_perm must be > 0",
        });
    }
    validate_permutation_scheme("permutation_pid3", scheme, n)?;

    // Observed PID on real data.
    let observed = pid3_isx(v, l, d, a, pid_cfg)?;
    if observed.atoms.iter().any(|atom| !atom.value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "permutation_pid3 point estimate",
        });
    }

    let mut rng = SplitMix64::new(seed);
    let n_atoms = observed.atoms.len();
    // perm_values[atom_idx][perm_idx]
    let mut perm_values = try_vec_with_capacity::<Vec<f64>>(n_atoms, "permutation_pid3")?;
    for _ in 0..n_atoms {
        perm_values.push(try_vec_with_capacity(n_perm, "permutation_pid3")?);
    }

    let dv = v.ncols();
    let dl = l.ncols();
    let dd = d.ncols();

    for _ in 0..n_perm {
        let perm = draw_permutation(scheme, n, &mut rng, "permutation_pid3")?;

        let shuffle = |mat: MatRef<'_>, dim: usize| -> PidResult<MatOwned> {
            let data_len = n.checked_mul(dim).ok_or(PidError::InvalidConfig {
                context: "permutation_pid3",
                message: "shuffled matrix length overflow",
            })?;
            let mut data = try_vec_with_capacity(data_len, "permutation_pid3")?;
            for &i in &perm {
                data.extend_from_slice(mat.row(i));
            }
            MatOwned::new(data, n, dim)
        };

        let copy_mat = |mat: MatRef<'_>, dim: usize| -> PidResult<MatOwned> {
            let data_len = n.checked_mul(dim).ok_or(PidError::InvalidConfig {
                context: "permutation_pid3",
                message: "copied matrix length overflow",
            })?;
            let mut data = try_vec_with_capacity(data_len, "permutation_pid3")?;
            for i in 0..n {
                data.extend_from_slice(mat.row(i));
            }
            MatOwned::new(data, n, dim)
        };

        // Only shuffle the selected source; keep others and target intact.
        let vp = if source_idx == 0 {
            shuffle(v, dv)?
        } else {
            copy_mat(v, dv)?
        };
        let lp = if source_idx == 1 {
            shuffle(l, dl)?
        } else {
            copy_mat(l, dl)?
        };
        let dp = if source_idx == 2 {
            shuffle(d, dd)?
        } else {
            copy_mat(d, dd)?
        };

        let values = complete_pid3_permutation_values(
            pid3_isx(vp.as_ref(), lp.as_ref(), dp.as_ref(), a, pid_cfg),
            n_atoms,
        )?;
        for (idx, value) in values.into_iter().enumerate() {
            perm_values[idx].push(value);
        }
    }

    let atoms: Vec<PermutationPid3Atom> = observed
        .atoms
        .iter()
        .enumerate()
        .map(|(idx, atom)| {
            let vals = &perm_values[idx];
            // Report the selected signed one-sided add-one tail fraction. For FullShuffle this is
            // the usual Monte Carlo permutation p-value under the relevant exchangeability
            // assumption (rows for FullShuffle, whole blocks for BlockShuffle). For the
            // restricted CircularShift scheme it is an approximate surrogate score.
            let n_extreme = vals
                .iter()
                .filter(|&&value| tail.contains(value, atom.value))
                .count();
            let p_value = (1 + n_extreme) as f64 / (1 + n_perm) as f64;
            PermutationPid3Atom {
                antichain: atom.antichain,
                observed: atom.value,
                p_value,
                n_valid: n_perm,
            }
        })
        .collect();

    Ok(PermutationPid3Result {
        atoms,
        n_perm,
        source_shuffled: source_idx,
        scheme,
        tail,
    })
}

/// Convert one permuted PID evaluation into the complete finite atom vector required for
/// permutation inference. Accepting the fallible evaluation directly makes both failure paths
/// explicit: estimator errors propagate, while malformed/non-finite successful results become a
/// numerical-instability error.
fn complete_pid3_permutation_values(
    result: PidResult<Pid3Result>,
    expected_atoms: usize,
) -> PidResult<Vec<f64>> {
    let result = result?;
    let values: Vec<f64> = result.atoms.iter().map(|atom| atom.value).collect();
    if values.len() != expected_atoms || values.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "permutation_pid3 permutation",
        });
    }
    Ok(values)
}

// ── PLS cross-validation ───────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, Default)]
struct ScaledSquareSum {
    max_log_square: f64,
    sum_scaled: f64,
    correction: f64,
    has_nonzero: bool,
}

impl ScaledSquareSum {
    fn add_difference(&mut self, left: f64, right: f64, context: &'static str) -> PidResult<()> {
        if !left.is_finite() || !right.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        let scale = left.abs().max(right.abs());
        if scale == 0.0 {
            return Ok(());
        }
        // Form the difference in bounded coordinates. `left - right` itself can overflow even
        // though the ratio of two sums of squared differences remains representable.
        let difference_scaled = left / scale - right / scale;
        if difference_scaled == 0.0 {
            return Ok(());
        }
        let log_square = 2.0 * (difference_scaled.abs().ln() + scale.ln());
        if !log_square.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }

        if !self.has_nonzero {
            self.max_log_square = log_square;
            self.sum_scaled = 1.0;
            self.has_nonzero = true;
            return Ok(());
        }
        if log_square > self.max_log_square {
            let ratio = (self.max_log_square - log_square).exp();
            self.sum_scaled *= ratio;
            self.correction *= ratio;
            self.max_log_square = log_square;
        }
        let value = (log_square - self.max_log_square).exp();
        let next = self.sum_scaled + value;
        self.correction += if self.sum_scaled.abs() >= value.abs() {
            (self.sum_scaled - next) + value
        } else {
            (value - next) + self.sum_scaled
        };
        self.sum_scaled = next;
        if self.sum_scaled.is_finite() && self.correction.is_finite() {
            Ok(())
        } else {
            Err(PidError::NumericalInstability { context })
        }
    }

    fn ratio(self, denominator: Self) -> Option<f64> {
        if !denominator.has_nonzero {
            return None;
        }
        if !self.has_nonzero {
            return Some(0.0);
        }
        let numerator_scaled = self.sum_scaled + self.correction;
        let denominator_scaled = denominator.sum_scaled + denominator.correction;
        if !(numerator_scaled.is_finite()
            && numerator_scaled > 0.0
            && denominator_scaled.is_finite()
            && denominator_scaled > 0.0)
        {
            return None;
        }
        let log_ratio = self.max_log_square - denominator.max_log_square + numerator_scaled.ln()
            - denominator_scaled.ln();
        if !log_ratio.is_finite() || log_ratio > f64::MAX.ln() {
            return None;
        }
        let ratio = log_ratio.exp();
        ratio.is_finite().then_some(ratio)
    }
}

/// Result of PLS cross-validation for component selection.
#[derive(Debug, Clone)]
pub struct PlsCvResult {
    /// Predictive power Q² for each candidate component count.
    pub q2: Vec<f64>,
    /// Optimal number of components (maximizing Q²).
    pub best_components: usize,
    /// Total number of candidate components tested.
    pub max_components: usize,
}

/// Leave-one-out cross-validation to select the optimal number of PLS components.
///
/// For each candidate `k` in 1..=max_components, this computes Q² = 1 - PRESS/SS_total,
/// where PRESS is the sum of squared prediction errors from LOO-CV and SS_total is the
/// total sum of squares of the target.
///
/// `x` is the source matrix (n×d_x) and `y` is the target (n×d_y).
pub fn pls_cv_select_components(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_components: usize,
) -> PidResult<PlsCvResult> {
    let n = x.nrows();
    let d_x = x.ncols();
    let d_y = y.ncols();
    if y.nrows() != n {
        return Err(PidError::RowCountMismatch {
            context: "pls_cv_select_components",
            left_rows: n,
            right_rows: y.nrows(),
        });
    }
    let max_out = d_x.min(n.saturating_sub(1));
    let max_components = max_components.min(max_out);
    if max_components == 0 {
        return Err(PidError::InvalidConfig {
            context: "pls_cv_select_components",
            message: "max_components must be >= 1 after clipping",
        });
    }

    // Compute SS_total.
    let mut y_mean = vec![0.0f64; d_y];
    for (j, mean) in y_mean.iter_mut().enumerate() {
        let column: Vec<f64> = (0..n).map(|i| y.row(i)[j]).collect();
        *mean = finite_mean(&column, "pls_cv_select_components: target mean")?;
    }
    let mut ss_total = ScaledSquareSum::default();
    for i in 0..n {
        for (j, &mean) in y_mean.iter().enumerate() {
            ss_total.add_difference(
                y.row(i)[j],
                mean,
                "pls_cv_select_components: target sum of squares",
            )?;
        }
    }

    let mut q2 = Vec::with_capacity(max_components);
    for k in 1..=max_components {
        let mut press = ScaledSquareSum::default();
        let mut fold_failed = false;
        // LOO-CV: for each held-out sample, fit PLS on the rest and predict.
        for held_out in 0..n {
            // Build train set (n-1 samples).
            let train_n = n - 1;
            let mut x_train_data = Vec::with_capacity(train_n * d_x);
            let mut y_train_data = Vec::with_capacity(train_n * d_y);
            for i in 0..n {
                if i == held_out {
                    continue;
                }
                x_train_data.extend_from_slice(x.row(i));
                y_train_data.extend_from_slice(y.row(i));
            }
            let x_train =
                MatOwned::new(x_train_data, train_n, d_x).expect("train data should be finite");
            let y_train =
                MatOwned::new(y_train_data, train_n, d_y).expect("train data should be finite");

            match PlsProjector::fit(x_train.as_ref(), y_train.as_ref(), k) {
                Ok(pls) => {
                    // Predict the held-out sample with the model's OWN PLS regression
                    // (`Ŷ = (x−x̄_train)·B + ȳ_train`). This uses the training-fold
                    // target mean as the intercept — never the full-data mean — so the
                    // held-out target does not leak into its own prediction, and the
                    // `W(PᵀW)⁻¹` rotation makes it exact for any number of components.
                    let x_ho =
                        MatRef::new(x.row(held_out), 1, d_x).expect("held-out row should be valid");
                    match pls.predict(x_ho) {
                        Ok(y_hat) => {
                            let pred = y_hat.as_ref().row(0);
                            let ho_row = y.row(held_out);
                            for j in 0..d_y {
                                press.add_difference(
                                    ho_row[j],
                                    pred[j],
                                    "pls_cv_select_components: prediction error sum of squares",
                                )?;
                            }
                        }
                        Err(_) => {
                            fold_failed = true;
                            break;
                        }
                    }
                }
                Err(_) => {
                    fold_failed = true;
                    break;
                }
            }
        }
        // A single failed LOO fold (rank-deficient training split, or a non-finite prediction)
        // makes `press` NaN, so `Q²(k) = −∞` and this `k` is not selected. This is deliberate,
        // not a lost result: a component count whose leave-one-out CV is ill-posed on *any* fold
        // is not a defensible choice, and silently dropping the failed fold would break Q²
        // comparability across `k` (PRESS and SS_total would then be summed over different
        // held-out sets). If *every* `k` fails, the function errors out below.
        let q2_k = if !fold_failed {
            press
                .ratio(ss_total)
                .map(|ratio| 1.0 - ratio)
                .filter(|value| value.is_finite())
                .unwrap_or(f64::NEG_INFINITY)
        } else {
            f64::NEG_INFINITY
        };
        q2.push(q2_k);
    }

    // Select the most parsimonious k achieving the best Q². `max_by` returns the LAST
    // maximum, which biases toward more components on ties; and if every fold failed (all
    // Q² are -inf) it would silently return the largest k. Pick the first k within a small
    // tolerance of the maximum, and error out when no fold produced a finite Q².
    let best = q2.iter().copied().fold(f64::NEG_INFINITY, f64::max);
    if !best.is_finite() {
        return Err(PidError::NumericalInstability {
            context: "pls_cv_select_components: all CV folds failed (no finite Q²)",
        });
    }
    let best_idx = q2.iter().position(|&v| v >= best - 1e-9).unwrap_or(0);
    let best_components = best_idx + 1;

    Ok(PlsCvResult {
        q2,
        best_components,
        max_components,
    })
}

// ── PLS → Discrete PID3 ──────────────────────────────────────────────────────

/// Configuration for [`pls_project_then_discrete_pid3`].
#[derive(Debug, Clone)]
pub struct PlsDiscretePid3Config {
    /// Number of PLS latent components to extract.
    pub pls_components: usize,
    /// Number of equal-width bins for discrete PID.
    pub num_bins: usize,
    /// Explicit opt-in to fitting supervised PLS and estimating PID on the same rows.
    ///
    /// This workflow is exploratory; fit projectors and choose component/bin counts on training
    /// data before evaluating PID on separately transformed rows for inferential use.
    pub exploratory_allow_same_sample_fit: bool,
}

/// Result of [`pls_project_then_discrete_pid3`].
#[derive(Debug, Clone)]
pub struct PlsDiscretePid3Result {
    pub pid: crate::discrete_pid::DiscretePid3Result,
    pub pls_components: usize,
    pub num_bins: usize,
    pub input_dims: [usize; 4],
    pub projected_dim: usize,
}

/// Fit per-source PLS projectors, project all four matrices into a low-dimensional
/// task-relevant subspace, then run discrete PID3 on the quantized projections.
///
/// This same-sample convenience is exploratory and requires
/// [`PlsDiscretePid3Config::exploratory_allow_same_sample_fit`] to be `true`: supervised PLS and
/// bin-count selection on the evaluation rows can make downstream atoms optimistic. For
/// inference, fit the projectors and choose all hyperparameters on training data, then transform
/// a separate evaluation set and call [`discrete_pid3`] there. Unlike the continuous estimator,
/// this avoids kNN distance concentration, but the result remains binning-sensitive.
pub fn pls_project_then_discrete_pid3(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    cfg: &PlsDiscretePid3Config,
) -> PidResult<PlsDiscretePid3Result> {
    let n = v.nrows();
    if l.nrows() != n || d.nrows() != n || a.nrows() != n {
        let right_rows = if l.nrows() != n {
            l.nrows()
        } else if d.nrows() != n {
            d.nrows()
        } else {
            a.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context: "pls_project_then_discrete_pid3",
            left_rows: n,
            right_rows,
        });
    }
    if !cfg.exploratory_allow_same_sample_fit {
        return Err(PidError::InvalidConfig {
            context: "pls_project_then_discrete_pid3",
            message: "same-sample supervised PLS followed by PID is exploratory; set exploratory_allow_same_sample_fit=true to acknowledge, or fit PLS and choose bins on training rows before evaluating held-out transformed rows",
        });
    }

    // Per-source PLS projectors.
    let v_proj = PlsProjector::fit(v, a, cfg.pls_components)?.transform(v)?;
    let l_proj = PlsProjector::fit(l, a, cfg.pls_components)?.transform(l)?;
    let d_proj = PlsProjector::fit(d, a, cfg.pls_components)?.transform(d)?;
    let vld = concat_horiz(concat_horiz(v, l)?.as_ref(), d)?;
    let a_proj = PlsProjector::fit(a, vld.as_ref(), cfg.pls_components)?.transform(a)?;

    let pid = discrete_pid3(
        v_proj.as_ref(),
        l_proj.as_ref(),
        d_proj.as_ref(),
        a_proj.as_ref(),
        cfg.num_bins,
    )?;

    Ok(PlsDiscretePid3Result {
        pid,
        pls_components: cfg.pls_components,
        num_bins: cfg.num_bins,
        input_dims: [v.ncols(), l.ncols(), d.ncols(), a.ncols()],
        projected_dim: cfg.pls_components,
    })
}

// ── Multi-pair PID2 screening ──────────────────────────────────────────────────

/// A single PID2 screening result for a pair of sources.
#[derive(Debug, Clone)]
pub struct Pid2ScreenEntry {
    /// Source pair indices (i, j) into the sources list.
    pub source_i: usize,
    pub source_j: usize,
    pub result: Pid2Result,
}

/// Screen all pairs of sources with PID2, returning one entry per pair.
///
/// `sources` is a slice of matrices, each n×d with the same ambient source dimension; equality is
/// a necessary continuous small-ball scaling guard, not proof of compatible intrinsic geometry.
/// `target` is the target matrix.
/// This computes PID2 for all C(n_sources, 2) pairs and sorts them by descending
/// synergy.
///
/// # Errors
///
/// Returns an error if a source is misaligned or any pair cannot be estimated. A partial
/// screening result is never returned as though it represented every requested pair.
pub fn screen_pid2_pairs(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Vec<Pid2ScreenEntry>> {
    let n = target.nrows();
    let n_src = sources.len();
    if n_src < 2 {
        return Err(PidError::InvalidConfig {
            context: "screen_pid2_pairs",
            message: "need at least two sources",
        });
    }
    let mut entries = Vec::with_capacity(n_src * (n_src.saturating_sub(1)) / 2);

    // Validate every source up front. A per-pair `continue` for source `j` could only
    // mask a row-count mismatch until the outer loop reached that index and hard-errored,
    // so the outcome was identical — validate once, then keep the pair loop clean.
    for s in sources {
        if s.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "screen_pid2_pairs",
                left_rows: n,
                right_rows: s.nrows(),
            });
        }
    }

    for i in 0..n_src {
        for j in (i + 1)..n_src {
            let result = pid2_isx(sources[i], sources[j], target, cfg)?;
            entries.push(Pid2ScreenEntry {
                source_i: i,
                source_j: j,
                result,
            });
        }
    }

    // Sort by descending synergy.
    entries.sort_by(|a, b| {
        b.result
            .synergy
            .partial_cmp(&a.result.synergy)
            .unwrap_or(std::cmp::Ordering::Equal)
    });

    Ok(entries)
}

// ── Generic row-resampling uncertainty helpers ─────────────────────────────

/// Bootstrap summary for one scalar statistic from [`bootstrap_rows_stats`].
#[derive(Debug, Clone, PartialEq)]
pub struct RowBootstrapStat {
    /// Statistic evaluated on the original (un-resampled, un-jittered) data.
    pub point_estimate: f64,
    /// Mean of the complete finite resampling distribution.
    pub boot_mean: f64,
    /// Standard deviation of the finite resample distribution. Under
    /// [`RowResampleScheme::Subsample`] this is the spread of the `m`-sample statistic, not a
    /// calibrated standard error for the `n`-row point estimate.
    pub boot_se: f64,
    /// Lower finite-resample percentile. Under [`RowResampleScheme::Subsample`] this is a raw
    /// `m`-sample diagnostic quantile, not a calibrated confidence bound for the `n`-row estimate.
    pub ci_low: f64,
    /// Upper finite-resample percentile. Under [`RowResampleScheme::Subsample`] this is a raw
    /// `m`-sample diagnostic quantile, not a calibrated confidence bound for the `n`-row estimate.
    pub ci_high: f64,
    /// Number of resamples attempted.
    pub n_attempted: usize,
    /// Number of complete finite resamples. Successful results always have
    /// `n_valid == n_attempted`; a failed draw invalidates the whole summary.
    pub n_valid: usize,
}

/// Row-resampling scheme for [`bootstrap_rows_stats`].
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum RowResampleScheme {
    /// Moving-block bootstrap (Künsch 1989) **with replacement** plus deterministic
    /// tie-breaking jitter on the resampled rows: block starts are drawn uniformly
    /// over all `n − block_size + 1` overlapping positions (every row is reachable,
    /// including the `n % block_size` tail), `⌈n/block_size⌉` blocks are concatenated
    /// and truncated to `n` rows.
    ///
    /// With-replacement resampling can create, and typically does create, duplicate rows. The KSG-family
    /// estimators in this crate intentionally reject zero kNN radii caused by
    /// duplicates (`PidError::NumericalInstability`), so `jitter_rel` should generally
    /// be > 0 for kNN statistics (each resampled element gets an additive uniform
    /// perturbation of amplitude `jitter_rel × column_std`, column std measured on
    /// the original data — the tie-breaking noise recommended by Kraskov et al.
    /// 2004 §III).
    ///
    /// **Caveat (empirically pinned by a test):** even with jitter, duplicated
    /// points distort kNN local-density statistics, shifting the bootstrap mean of
    /// KSG MI by a non-negligible amount. Naive with-replacement bootstrap is known
    /// to be unreliable for kNN information estimators; prefer
    /// [`RowResampleScheme::Subsample`] for KSG-based statistics.
    BlockBootstrapJitter {
        /// Relative jitter amplitude (e.g. `1e-9`); 0 disables jitter.
        jitter_rel: f64,
    },
    /// Fixed-grid block subsampling **without replacement**: each resample
    /// draws `subsample_len / block_size` *distinct* contiguous blocks from the fixed
    /// non-overlapping block grid, yielding a subsample with no repeated row indices and
    /// (approximately) `subsample_len` rows. Because the grid is fixed, the trailing
    /// `n % block_size` rows are never sampled by this scheme (the distinct-block
    /// guarantee is what prevents resampling from introducing duplicates).
    ///
    /// This scheme does not introduce duplicate indices, but ties already present in the original
    /// data can still collapse kNN radii. The returned percentiles are the raw distribution of the
    /// statistic at effective sample size
    /// `m = floor(subsample_len / block_size) * block_size`. At least one complete grid block must
    /// be omitted. These percentiles are **not** a calibrated confidence interval for the `n`-row
    /// estimate: m-out-of-n inference requires estimator-specific centering/scaling, and KSG bias
    /// itself can vary with `m`. Treat them as diagnostics and report the effective `m`.
    Subsample {
        /// Subsample length `m` (rows; rounded down to a multiple of `block_size`).
        subsample_len: usize,
    },
}

/// Result of [`bootstrap_rows_stats`].
#[derive(Debug, Clone, PartialEq)]
pub struct RowBootstrapResult {
    /// Per-statistic summaries, in the order returned by the statistic closure.
    pub stats: Vec<RowBootstrapStat>,
    /// Number of resamples attempted.
    pub n_boot: usize,
    /// Block size used for the block-level resampling.
    pub block_size: usize,
    /// Rows in each realized resample.
    ///
    /// This equals the original `n` for [`RowResampleScheme::BlockBootstrapJitter`]. For
    /// [`RowResampleScheme::Subsample`] it is
    /// `floor(subsample_len / block_size) * block_size`, which callers must report alongside the
    /// raw diagnostic quantiles.
    pub effective_resample_len: usize,
    /// Resampling scheme used.
    pub scheme: RowResampleScheme,
}

/// Joint block-level row resampling over several aligned matrices, for a
/// vector-valued statistic, under a configurable [`RowResampleScheme`].
///
/// All matrices must share the same row count `n`. Each resample draws contiguous
/// blocks of row indices (the same indices are applied to every matrix, preserving
/// cross-variable alignment), then evaluates `stat` on the resampled matrices.
/// Raw percentile bounds are computed from the finite resample statistics. They have the usual
/// percentile-bootstrap interpretation only when the selected scheme supports it; the
/// [`RowResampleScheme::Subsample`] bounds are uncalibrated `m`-sample diagnostics.
///
/// For KSG/kNN-based statistics use [`RowResampleScheme::Subsample`]; see the
/// scheme docs for why with-replacement bootstrap is problematic there.
///
/// A failed resample (statistic returns `Err`, changes output width, or returns a non-finite
/// entry) invalidates the whole summary. Selectively deleting failed draws would condition the
/// resampling distribution on estimator success and can make intervals anti-conservative.
///
/// # Errors
///
/// Returns an error if the matrices are empty or misaligned, if the configuration is invalid, if
/// the requested schedules/distributions cannot be reserved safely, or if the statistic fails
/// **on the original data** (a failed point
/// estimate makes the resampling distribution meaningless), including when any original
/// point-estimate entry is non-finite. A resample error from `stat` is propagated; a non-finite
/// resample entry or an overflowing distribution summary returns
/// [`PidError::NumericalInstability`].
pub fn bootstrap_rows_stats<F>(
    mats: &[MatRef<'_>],
    cfg: &BootstrapConfig,
    scheme: RowResampleScheme,
    stat: F,
) -> PidResult<RowBootstrapResult>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<Vec<f64>>,
{
    if mats.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "mats must not be empty",
        });
    }
    let n = mats[0].nrows();
    for m in mats {
        if m.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "bootstrap_rows_stats",
                left_rows: n,
                right_rows: m.nrows(),
            });
        }
    }
    if cfg.n_boot < 2 {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "n_boot must be >= 2 to estimate resample variance",
        });
    }
    if cfg.block_size == 0 || cfg.block_size >= n {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "block_size must be in 1..n",
        });
    }
    if !(cfg.alpha > 0.0 && cfg.alpha < 1.0) {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "alpha must be in (0, 1)",
        });
    }
    let n_blocks = n / cfg.block_size;
    // Number of distinct blocks to draw per resample, and whether to draw with
    // replacement, depend on the scheme.
    let (blocks_per_resample, with_replacement, jitter_rel) = match scheme {
        RowResampleScheme::BlockBootstrapJitter { jitter_rel } => {
            if !jitter_rel.is_finite() || jitter_rel < 0.0 {
                return Err(PidError::InvalidConfig {
                    context: "bootstrap_rows_stats",
                    message: "jitter_rel must be finite and >= 0",
                });
            }
            // True MBB: ⌈n/block_size⌉ overlapping-start blocks, truncated to n rows below.
            (n.div_ceil(cfg.block_size), true, jitter_rel)
        }
        RowResampleScheme::Subsample { subsample_len } => {
            let blocks = subsample_len / cfg.block_size;
            if blocks == 0 {
                return Err(PidError::InvalidConfig {
                    context: "bootstrap_rows_stats",
                    message: "subsample_len must be >= block_size",
                });
            }
            if blocks >= n_blocks {
                return Err(PidError::InvalidConfig {
                    context: "bootstrap_rows_stats",
                    message: "subsample_len must omit at least one complete fixed-grid block",
                });
            }
            (blocks, false, 0.0)
        }
    };

    // Preflight every resample-distribution and index schedule capacity before invoking `stat`.
    // In particular, a zero-column `MatRef` can legally carry an enormous logical row count, so
    // row-index amplification must be checked independently of matrix storage size.
    let first_boot_values = try_vec_with_capacity::<f64>(cfg.n_boot, "bootstrap_rows_stats")?;
    let index_capacity = if with_replacement {
        // Moving-block concatenation is truncated to exactly `n` rows.
        n
    } else {
        blocks_per_resample
            .checked_mul(cfg.block_size)
            .ok_or(PidError::InvalidConfig {
                context: "bootstrap_rows_stats",
                message: "resample index length overflow",
            })?
    };
    let mut starts = try_vec_with_capacity::<usize>(blocks_per_resample, "bootstrap_rows_stats")?;
    let mut indices = try_vec_with_capacity::<usize>(index_capacity, "bootstrap_rows_stats")?;
    let mut pool = if with_replacement {
        Vec::new()
    } else {
        try_vec_with_capacity::<usize>(n_blocks, "bootstrap_rows_stats")?
    };

    let point = stat(mats)?;
    if point.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "stat must return at least one value",
        });
    }
    if point.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "bootstrap_rows_stats point estimate",
        });
    }
    let n_stats = point.len();

    // Jitter alone needs a scale. Avoid both unnecessary work and manufactured overflow on the
    // no-repeated-index/no-jitter paths. Scale-normalized moments keep a constant column at
    // f64::MAX at its mathematically correct zero standard deviation instead of overflowing a
    // naive sum.
    let col_stds = if jitter_rel > 0.0 {
        mats.iter()
            .map(|m| checked_column_stds(*m))
            .collect::<PidResult<Vec<_>>>()?
    } else {
        Vec::new()
    };

    let mut rng = SplitMix64::new(cfg.seed);
    // boot_values[stat_idx][resample_idx], with every resample retained coherently.
    let mut boot_values = try_vec_with_capacity::<Vec<f64>>(n_stats, "bootstrap_rows_stats")?;
    boot_values.push(first_boot_values);
    for _ in 1..n_stats {
        boot_values.push(try_vec_with_capacity(cfg.n_boot, "bootstrap_rows_stats")?);
    }

    for _ in 0..cfg.n_boot {
        // Draw block starts per scheme.
        starts.clear();
        if with_replacement {
            // True moving-block bootstrap (Künsch 1989): starts uniform over ALL
            // n − block_size + 1 overlapping positions, so every row (including the
            // n % block_size tail) is reachable.
            let n_starts = n - cfg.block_size + 1;
            for _ in 0..blocks_per_resample {
                starts.push(uniform_index(&mut rng, n_starts));
            }
        } else {
            // Partial Fisher–Yates over the fixed non-overlapping grid [0, n_blocks):
            // distinct blocks are what guarantee no repeated row indices (see the
            // `RowResampleScheme::Subsample` doc for the tail-exclusion trade-off).
            pool.clear();
            pool.extend(0..n_blocks);
            for k in 0..blocks_per_resample {
                let j = k + uniform_index(&mut rng, n_blocks - k);
                pool.swap(k, j);
                starts.push(pool[k] * cfg.block_size);
            }
            // Keep temporal order of subsampled blocks for block-structure fidelity.
            starts.sort_unstable();
        }

        indices.clear();
        'blocks: for &block_start in &starts {
            for j in 0..cfg.block_size {
                indices.push(block_start + j);
                if with_replacement && indices.len() == n {
                    // MBB concatenation truncates to exactly n rows.
                    break 'blocks;
                }
            }
        }

        let mut owned = try_vec_with_capacity::<MatOwned>(mats.len(), "bootstrap_rows_stats")?;
        for (m_idx, m) in mats.iter().enumerate() {
            let d = m.ncols();
            let data_len = indices
                .len()
                .checked_mul(d)
                .ok_or(PidError::InvalidConfig {
                    context: "bootstrap_rows_stats",
                    message: "resampled matrix length overflow",
                })?;
            let mut data = try_vec_with_capacity(data_len, "bootstrap_rows_stats")?;
            for &i in &indices {
                data.extend_from_slice(m.row(i));
            }
            if jitter_rel > 0.0 {
                for (flat_idx, v) in data.iter_mut().enumerate() {
                    let col = flat_idx % d;
                    let scale = jitter_rel * col_stds[m_idx][col];
                    if !scale.is_finite() {
                        return Err(PidError::NumericalInstability {
                            context: "bootstrap_rows_stats jitter scale",
                        });
                    }
                    if scale > 0.0 {
                        // Uniform in [-scale, scale]: tie-breaking only, shape irrelevant.
                        let u = (rng.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
                        *v += scale * (2.0 * u - 1.0);
                    }
                }
            }
            owned.push(
                MatOwned::new(data, indices.len(), d).map_err(|error| match error {
                    PidError::NonFiniteInput { .. } => PidError::NumericalInstability {
                        context: "bootstrap_rows_stats jittered resample",
                    },
                    other => other,
                })?,
            );
        }
        let mut refs = try_vec_with_capacity::<MatRef<'_>>(owned.len(), "bootstrap_rows_stats")?;
        refs.extend(owned.iter().map(|matrix| matrix.as_ref()));
        let values = stat(&refs)?;
        if values.len() != n_stats {
            return Err(PidError::InvalidConfig {
                context: "bootstrap_rows_stats",
                message: "stat returned an inconsistent number of values",
            });
        }
        if values.iter().any(|value| !value.is_finite()) {
            return Err(PidError::NumericalInstability {
                context: "bootstrap_rows_stats resample",
            });
        }
        for (idx, value) in values.into_iter().enumerate() {
            boot_values[idx].push(value);
        }
    }

    let stats: Vec<RowBootstrapStat> = point
        .iter()
        .enumerate()
        .map(|(idx, &point_estimate)| -> PidResult<RowBootstrapStat> {
            let vals = &mut boot_values[idx];
            vals.sort_by(f64::total_cmp);
            let m = vals.len();
            debug_assert_eq!(m, cfg.n_boot);
            let (mean, se) = finite_mean_std_sample(vals, "bootstrap_rows_stats summary")?;
            let lo_idx = ((cfg.alpha / 2.0) * m as f64).floor() as usize;
            let hi_idx = (((1.0 - cfg.alpha / 2.0) * m as f64).ceil() as usize)
                .saturating_sub(1)
                .min(m - 1);
            Ok(RowBootstrapStat {
                point_estimate,
                boot_mean: mean,
                boot_se: se,
                ci_low: vals[lo_idx],
                ci_high: vals[hi_idx],
                n_attempted: cfg.n_boot,
                n_valid: m,
            })
        })
        .collect::<PidResult<_>>()?;

    Ok(RowBootstrapResult {
        stats,
        n_boot: cfg.n_boot,
        block_size: cfg.block_size,
        effective_resample_len: index_capacity,
        scheme,
    })
}

fn checked_column_stds(matrix: MatRef<'_>) -> PidResult<Vec<f64>> {
    debug_assert!(matrix.nrows() > 0);
    (0..matrix.ncols())
        .map(|column| {
            let values: Vec<f64> = (0..matrix.nrows())
                .map(|row| matrix.row(row)[column])
                .collect();
            finite_mean_std_population(&values, "bootstrap_rows_stats jitter standard deviation")
                .map(|(_, std)| std)
        })
        .collect()
}

/// Bootstrap confidence intervals for the averaged 2-source discrete SxPID (`i^sx_∩`) atoms.
#[derive(Debug, Clone, PartialEq)]
pub struct QuantizedSxPid2BootstrapResult {
    pub redundancy: RowBootstrapStat,
    pub unique_s1: RowBootstrapStat,
    pub unique_s2: RowBootstrapStat,
    pub synergy: RowBootstrapStat,
    pub n_boot: usize,
    pub block_size: usize,
}

/// Dependence-aware bootstrap confidence intervals for the averaged discrete SxPID atoms
/// ([`quantized_sxpid2`]).
///
/// Resampling uses a moving-block bootstrap **with replacement and no jitter**
/// ([`RowResampleScheme::BlockBootstrapJitter`] with `jitter_rel = 0`): unlike the kNN/KSG
/// estimators, the discrete (counting-based) SxPID is unaffected by duplicate rows, and jitter
/// would corrupt the discrete labels. Set `cfg.block_size = 1` for i.i.d. data, or a larger block
/// for autocorrelated (e.g. time-series) data. The percentile interval is the
/// `(1 − cfg.alpha)` two-sided CI of each atom over the resamples.
///
/// This mirrors the uncertainty story IDTxl provides for PID via its surrogate framework.
/// The continuous inputs are resampled first and `quantized_sxpid2` then re-fits equal-width bin
/// edges on each resample. This is a full-pipeline bootstrap; it does not hold the original
/// sample's bin edges fixed.
///
/// # Errors
///
/// Propagates [`bootstrap_rows_stats`] errors, including invalid configuration, unallocatable
/// resampling schedules/distributions, and failed or non-finite atom evaluation.
pub fn bootstrap_quantized_sxpid2(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    num_bins: usize,
    cfg: &BootstrapConfig,
) -> PidResult<QuantizedSxPid2BootstrapResult> {
    let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
        let r = quantized_sxpid2(mats[0], mats[1], mats[2], num_bins)?;
        Ok(vec![r.red.net, r.unq1.net, r.unq2.net, r.syn.net])
    };
    let res = bootstrap_rows_stats(
        &[s1, s2, t],
        cfg,
        RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
        stat,
    )?;
    let mut it = res.stats.into_iter();
    let mut next = || {
        it.next().ok_or(PidError::InvalidConfig {
            context: "bootstrap_quantized_sxpid2",
            message: "missing bootstrap statistic",
        })
    };
    Ok(QuantizedSxPid2BootstrapResult {
        redundancy: next()?,
        unique_s1: next()?,
        unique_s2: next()?,
        synergy: next()?,
        n_boot: res.n_boot,
        block_size: res.block_size,
    })
}

/// Result of [`permutation_rows_pvalue`].
#[derive(Debug, Clone, PartialEq)]
pub struct RowPermutationStat {
    /// Statistic on the original data.
    pub observed: f64,
    /// Add-one signed one-sided tail fraction. [`PermutationTail::Upper`] counts
    /// `permutation >= observed`; [`PermutationTail::Lower`] counts
    /// `permutation <= observed`.
    ///
    /// For [`PermutationScheme::FullShuffle`] this is the usual Monte Carlo permutation
    /// p-value under row exchangeability. For [`PermutationScheme::BlockShuffle`] it is
    /// a Monte Carlo permutation p-value under whole-block exchangeability. For
    /// [`PermutationScheme::CircularShift`] it is an approximate stationary-surrogate
    /// score, not an exact randomization-test p-value. Any failed or non-finite transform
    /// invalidates the whole inference, so successful results use every attempted draw.
    pub p_value: f64,
    /// Number of permutations attempted.
    pub n_attempted: usize,
    /// Number of complete, finite permutations used in the null distribution. Successful
    /// results always have `n_valid == n_attempted`.
    pub n_valid: usize,
    /// Index (into `mats`) of the matrix whose rows were shuffled.
    pub shuffled_index: usize,
    /// Resampling scheme that generated the null distribution.
    pub scheme: PermutationScheme,
    /// Signed one-sided alternative used for the tail comparison.
    pub tail: PermutationTail,
}

/// Upper-tail permutation test on a scalar statistic of several aligned matrices.
///
/// Shuffles the rows of `mats[shuffled_index]` (Fisher–Yates, seeded) while keeping
/// every other matrix fixed, re-evaluating `stat` on each permuted dataset. Under a null in which
/// the selected rows/blocks are exchangeable relative to the aligned joint of
/// all remaining matrices, the observed statistic is exchangeable with the permuted ones.
///
/// Like [`permutation_pid3`], this helper counts `permutation >= observed` and uses the add-one
/// Monte Carlo p-value `(b + 1) / (m + 1)` (Phipson & Smyth 2010). Under row exchangeability and
/// [`PermutationScheme::FullShuffle`] it is the usual nonzero permutation p-value and
/// is the convention the Experiment 0 gate relies on.
///
/// A permutation preserves each individual matrix's row multiset, but re-pairing repeated source
/// and target values can still create duplicate rows in a joint kNN space. No implicit jitter is
/// added: every requested transform must evaluate under the caller's fixed preprocessing policy,
/// and a duplicate-induced estimator failure invalidates the permutation inference.
///
/// Uses [`PermutationScheme::FullShuffle`] (exchangeable/i.i.d. rows). Use
/// [`permutation_rows_pvalue_with`] with [`PermutationScheme::BlockShuffle`] when
/// fixed, equal-sized whole blocks are exchangeable, or
/// [`PermutationScheme::CircularShift`] for a stationary-series surrogate.
///
/// # Errors
///
/// Returns an error on misaligned/empty inputs, an out-of-range `shuffled_index`,
/// `n_perm == 0`, an unallocatable row schedule or shuffled matrix, or if the statistic fails or
/// is non-finite on the original data or any permutation.
pub fn permutation_rows_pvalue<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with(
        mats,
        shuffled_index,
        n_perm,
        seed,
        PermutationScheme::FullShuffle,
        stat,
    )
}

/// [`permutation_rows_pvalue`] with an explicit [`PermutationScheme`] and the
/// compatibility-default [`PermutationTail::Upper`] alternative.
///
/// With [`PermutationScheme::FullShuffle`] this is bit-identical to
/// [`permutation_rows_pvalue`] at the same seed. With
/// [`PermutationScheme::BlockShuffle`], the equal-sized block permutations form a
/// finite group, and the add-one formula is a Monte Carlo permutation p-value under
/// exchangeability of the whole blocks. With [`PermutationScheme::CircularShift`], the
/// same formula is only an approximate stationary-surrogate tail fraction because the
/// restricted shifts do not form a transformation group and are sampled with replacement.
/// Every transform must evaluate successfully and finitely; otherwise the whole inference
/// returns an error instead of selecting a transform-dependent subset of draws.
///
/// # Errors
///
/// Returns an error on invalid inputs or scheme configuration, an unallocatable row schedule or
/// shuffled matrix, or if `stat` fails or returns a non-finite value on the observed data or any
/// permutation.
pub fn permutation_rows_pvalue_with<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with_tail(
        mats,
        shuffled_index,
        n_perm,
        seed,
        scheme,
        PermutationTail::Upper,
        stat,
    )
}

/// Permutation test on a scalar statistic with an explicit null scheme and signed one-sided tail.
///
/// [`PermutationTail::Upper`] counts `permutation >= observed` and is bit-identical to
/// [`permutation_rows_pvalue_with`] at the same seed and scheme. [`PermutationTail::Lower`]
/// counts `permutation <= observed`. The statistic is used as supplied; this API does not take
/// absolute values or infer a two-sided alternative.
///
/// Every transform must evaluate successfully and finitely; otherwise the whole inference
/// returns an error instead of selecting a transform-dependent subset of draws.
///
/// # Errors
///
/// Returns an error on invalid inputs or scheme configuration, an unallocatable row schedule or
/// shuffled matrix, or if `stat` fails or returns a non-finite value on the observed data or any
/// permutation.
pub fn permutation_rows_pvalue_with_tail<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    tail: PermutationTail,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    if mats.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "mats must not be empty",
        });
    }
    let n = mats[0].nrows();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "matrices must have at least one row",
        });
    }
    for m in mats {
        if m.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "permutation_rows_pvalue",
                left_rows: n,
                right_rows: m.nrows(),
            });
        }
    }
    if shuffled_index >= mats.len() {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "shuffled_index out of range",
        });
    }
    if n_perm == 0 {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "n_perm must be > 0",
        });
    }
    validate_permutation_scheme("permutation_rows_pvalue", scheme, n)?;

    let observed = stat(mats)?;
    if !observed.is_finite() {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "observed statistic must be finite",
        });
    }

    let mut rng = SplitMix64::new(seed);
    let shuffled_dim = mats[shuffled_index].ncols();
    let mut n_extreme = 0usize;

    for _ in 0..n_perm {
        let perm = draw_permutation(scheme, n, &mut rng, "permutation_rows_pvalue")?;
        let data_len = n.checked_mul(shuffled_dim).ok_or(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "shuffled matrix length overflow",
        })?;
        let mut data = try_vec_with_capacity(data_len, "permutation_rows_pvalue")?;
        for &i in &perm {
            data.extend_from_slice(mats[shuffled_index].row(i));
        }
        let shuffled =
            MatOwned::new(data, n, shuffled_dim).map_err(|_| PidError::InvalidConfig {
                context: "permutation_rows_pvalue",
                message: "shuffled data must be finite",
            })?;
        let mut refs = try_vec_with_capacity::<MatRef<'_>>(mats.len(), "permutation_rows_pvalue")?;
        refs.extend_from_slice(mats);
        refs[shuffled_index] = shuffled.as_ref();
        let value = stat(&refs)?;
        if !value.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "permutation_rows_pvalue permutation statistic",
            });
        }
        if tail.contains(value, observed) {
            n_extreme += 1;
        }
    }

    let p_value = (1.0 + n_extreme as f64) / (1.0 + n_perm as f64);

    Ok(RowPermutationStat {
        observed,
        p_value,
        n_attempted: n_perm,
        n_valid: n_perm,
        shuffled_index,
        scheme,
        tail,
    })
}

// ── Multiple-testing correction ────────────────────────────────────────────────

/// Benjamini–Hochberg step-up false-discovery-rate adjustment.
///
/// Returns q-values aligned with the input: `q[i]` is the smallest FDR level at
/// which hypothesis `i` would be rejected — reject `{i : q[i] ≤ α}` to control the
/// FDR at `α` (Benjamini & Hochberg 1995, JRSS-B 57(1):289–300; valid under
/// independence or positive regression dependence of the p-values). Computed as
/// `q₍ᵢ₎ = min_{j ≥ i} p₍ⱼ₎ · m / j` over the ascending order statistics, clamped
/// to 1.
///
/// This is the correction genuine atom-level permutation p-values need when many atoms ×
/// sources × windows are tested at once. Apply it to the pooled family only after checking
/// the resampling assumptions and finite counts. In particular, a restricted
/// [`PermutationScheme::CircularShift`] tail fraction is an approximate surrogate score, not
/// a p-value, and must not be passed here as though it were one.
///
/// `NaN` entries (for example, hypotheses declared unavailable before correction) are
/// passed through as `NaN` but count conservatively toward the predeclared family size `m`
/// as failed, nonsignificant hypotheses. Dropping post-hoc failures from `m` would make the
/// correction anti-conservative.
///
/// # Errors
///
/// Returns an error if the input is empty or any finite entry lies outside `[0, 1]`.
pub fn benjamini_hochberg(p_values: &[f64]) -> PidResult<Vec<f64>> {
    adjust_step_up(p_values, 1.0, "benjamini_hochberg")
}

/// Benjamini–Yekutieli step-up false-discovery-rate adjustment.
///
/// This is the arbitrary-dependence counterpart to [`benjamini_hochberg`]. It applies the
/// harmonic correction `c(m) = sum_{i=1}^m 1/i`, yielding
/// `q₍ᵢ₎ = min_{j ≥ i} p₍ⱼ₎ · m · c(m) / j` (Benjamini & Yekutieli 2001,
/// *Annals of Statistics* 29(4):1165–1188). Use it when the dependence structure among a pooled
/// family of atom/source/window p-values is unknown or does not satisfy BH's independence or
/// positive-dependence conditions. The extra guarantee is conservative and can substantially
/// reduce power for large families.
///
/// `NaN` entries pass through and count toward the predeclared family size exactly as in
/// [`benjamini_hochberg`]. Restricted circular-shift surrogate scores are not p-values and must
/// not be passed to either adjustment.
///
/// # Errors
///
/// Returns an error if the input is empty or any finite entry lies outside `[0, 1]`.
pub fn benjamini_yekutieli(p_values: &[f64]) -> PidResult<Vec<f64>> {
    if p_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "benjamini_yekutieli",
            message: "p_values must not be empty",
        });
    }
    let harmonic = (1..=p_values.len())
        .map(|rank| 1.0 / rank as f64)
        .sum::<f64>();
    adjust_step_up(p_values, harmonic, "benjamini_yekutieli")
}

fn adjust_step_up(
    p_values: &[f64],
    dependence_factor: f64,
    context: &'static str,
) -> PidResult<Vec<f64>> {
    if p_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "p_values must not be empty",
        });
    }
    let mut finite: Vec<(usize, f64)> = Vec::with_capacity(p_values.len());
    for (i, &p) in p_values.iter().enumerate() {
        if p.is_nan() {
            continue;
        }
        if !(0.0..=1.0).contains(&p) {
            return Err(PidError::InvalidConfig {
                context,
                message: "every finite p-value must lie in [0, 1]",
            });
        }
        finite.push((i, p));
    }
    let mut adjusted = vec![f64::NAN; p_values.len()];
    let finite_count = finite.len();
    let m = p_values.len();
    if finite_count == 0 {
        return Ok(adjusted); // all-NaN input: nothing to adjust
    }
    finite.sort_by(|a, b| a.1.total_cmp(&b.1));
    // Step-up: walk ranks from largest to smallest carrying the running minimum.
    let mut running_min = 1.0f64;
    for rank in (1..=finite_count).rev() {
        let (orig_idx, p) = finite[rank - 1];
        let q = (p * m as f64 * dependence_factor / rank as f64)
            .min(running_min)
            .min(1.0);
        running_min = q;
        adjusted[orig_idx] = q;
    }
    Ok(adjusted)
}

// ── Tests ──────────────────────────────────────────────────────────────────

#[cfg(test)]
#[allow(deprecated)]
mod tests {
    use super::*;
    use crate::preprocess::SplitMix64;

    fn experimental_pid3_config() -> Pid3Config {
        Pid3Config {
            experimental_allow_mixed_dimension_lattice: true,
            ..Pid3Config::default()
        }
    }

    /// Helper: generate synthetic (V, L, D, A) data where V and L share signal about A,
    /// D is pure noise.
    fn make_vlda(n: usize, seed: u64) -> (MatOwned, MatOwned, MatOwned, MatOwned) {
        let mut rng = SplitMix64::new(seed);
        let mut v_data = Vec::with_capacity(n * 3);
        let mut l_data = Vec::with_capacity(n * 3);
        let mut d_data = Vec::with_capacity(n * 2);
        let mut a_data = Vec::with_capacity(n);
        for _ in 0..n {
            let signal = rng.normal();
            // V carries signal in dim 0, noise in dims 1,2
            v_data.push(signal + 0.1 * rng.normal());
            v_data.push(rng.normal());
            v_data.push(rng.normal());
            // L carries signal in dim 0, noise in dims 1,2
            l_data.push(signal + 0.1 * rng.normal());
            l_data.push(rng.normal());
            l_data.push(rng.normal());
            // D is pure noise
            d_data.push(rng.normal());
            d_data.push(rng.normal());
            // A = signal + small noise
            a_data.push(signal + 0.05 * rng.normal());
        }
        let v = MatOwned::new(v_data, n, 3).unwrap();
        let l = MatOwned::new(l_data, n, 3).unwrap();
        let d = MatOwned::new(d_data, n, 2).unwrap();
        let a = MatOwned::new(a_data, n, 1).unwrap();
        (v, l, d, a)
    }

    #[test]
    fn pls_project_then_pid3_runs_and_returns_18_atoms() {
        let (v, l, d, a) = make_vlda(60, 42);
        let cfg = PlsPid3Config {
            pls_components: 1,
            pid_cfg: experimental_pid3_config(),
            exploratory_allow_same_sample_fit: true,
        };
        let result =
            pls_project_then_pid3(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &cfg).unwrap();
        // The PID result has 18 atoms for 3 sources.
        assert_eq!(result.pid.atoms.len(), 18);
        assert_eq!(result.pls_components, 1);
        assert_eq!(result.projected_dim, 1);
        assert_eq!(result.input_dims, [3, 3, 2, 1]);
    }

    #[test]
    fn pls_project_then_pid3_requires_exploratory_same_sample_acknowledgement() {
        let (v, l, d, a) = make_vlda(20, 8);
        let cfg = PlsPid3Config {
            pls_components: 1,
            pid_cfg: experimental_pid3_config(),
            exploratory_allow_same_sample_fit: false,
        };
        let error = pls_project_then_pid3(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &cfg)
            .unwrap_err();
        assert!(matches!(
            error,
            PidError::InvalidConfig {
                context: "pls_project_then_pid3",
                ..
            }
        ));
    }

    #[test]
    fn pls_project_then_pid3_rejects_mismatched_rows() {
        let v = MatOwned::new(vec![0.0; 30], 10, 3).unwrap();
        let l = MatOwned::new(vec![0.0; 15], 5, 3).unwrap(); // Wrong row count
        let d = MatOwned::new(vec![0.0; 20], 10, 2).unwrap();
        let a = MatOwned::new(vec![0.0; 10], 10, 1).unwrap();
        let cfg = PlsPid3Config {
            pls_components: 1,
            pid_cfg: experimental_pid3_config(),
            exploratory_allow_same_sample_fit: false,
        };
        assert!(
            pls_project_then_pid3(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &cfg,).is_err()
        );
    }

    #[test]
    fn pipeline_row_mismatch_reports_the_first_operand_that_actually_differs() {
        let v = MatOwned::new(vec![0.0; 30], 10, 3).unwrap();
        let l = MatOwned::new(vec![0.0; 30], 10, 3).unwrap();
        let d = MatOwned::new(vec![0.0; 24], 12, 2).unwrap();
        let a = MatOwned::new(vec![0.0; 10], 10, 1).unwrap();
        let continuous_cfg = PlsPid3Config {
            pls_components: 1,
            pid_cfg: experimental_pid3_config(),
            exploratory_allow_same_sample_fit: false,
        };
        let discrete_cfg = PlsDiscretePid3Config {
            pls_components: 1,
            num_bins: 2,
            exploratory_allow_same_sample_fit: false,
        };
        let bootstrap_cfg = BootstrapConfig {
            n_boot: 2,
            block_size: 2,
            seed: 0,
            alpha: 0.05,
        };

        let errors = [
            pls_project_then_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &continuous_cfg,
            )
            .unwrap_err(),
            pls_project_then_discrete_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &discrete_cfg,
            )
            .unwrap_err(),
            bootstrap_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &experimental_pid3_config(),
                &bootstrap_cfg,
            )
            .unwrap_err(),
        ];
        for error in errors {
            assert!(matches!(
                error,
                PidError::RowCountMismatch {
                    left_rows: 10,
                    right_rows: 12,
                    ..
                }
            ));
        }
    }

    #[test]
    fn bootstrap_pid3_rejects_ambiguous_shells_created_by_duplicate_blocks() {
        let (v, l, d, a) = make_vlda(80, 77);
        let pid_cfg = experimental_pid3_config();
        let boot_cfg = BootstrapConfig {
            n_boot: 20, // Small for test speed
            // Two long blocks can duplicate a row at most once per identical draw, below k=3;
            // smaller blocks can be selected four times and correctly invalidate kNN inference.
            block_size: 40,
            seed: 42,
            alpha: 0.1,
        };
        let error = bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            &boot_cfg,
        )
        .unwrap_err();
        assert!(matches!(error, PidError::AmbiguousKthNeighborShell { .. }));
    }

    #[test]
    fn bootstrap_pid3_rejects_out_of_range_alpha() {
        let (v, l, d, a) = make_vlda(40, 5);
        let pid_cfg = experimental_pid3_config();
        // alpha >= 1 previously produced an out-of-range percentile index (alpha >= 2 panicked);
        // every alpha outside the open interval (0, 1) must now be a clean Err.
        for bad_alpha in [0.0, 1.0, 2.0, -0.1] {
            let boot_cfg = BootstrapConfig {
                n_boot: 5,
                block_size: 8,
                seed: 1,
                alpha: bad_alpha,
            };
            let res = bootstrap_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &pid_cfg,
                &boot_cfg,
            );
            assert!(
                res.is_err(),
                "alpha={bad_alpha} must be rejected (require 0 < alpha < 1)"
            );
        }
    }

    #[test]
    fn bootstrap_pid3_rejects_a_full_sample_block() {
        let (v, l, d, a) = make_vlda(20, 6);
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 20,
            seed: 0,
            alpha: 0.05,
        };

        assert!(bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &experimental_pid3_config(),
            &config,
        )
        .is_err());
    }

    #[test]
    fn bootstrap_pid3_rejects_unallocatable_resample_count_without_panicking() {
        let (v, l, d, a) = make_vlda(8, 6);
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 4,
            seed: 0,
            alpha: 0.05,
        };

        let outcome = std::panic::catch_unwind(|| {
            bootstrap_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &experimental_pid3_config(),
                &config,
            )
        });

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn bootstrap_pid3_rejects_when_every_resample_fails() {
        let (v, l, d, a) = make_vlda(20, 73);
        let pid_cfg = Pid3Config {
            k: 1,
            ..experimental_pid3_config()
        };
        let boot_cfg = BootstrapConfig {
            n_boot: 4,
            block_size: 1,
            seed: 9,
            alpha: 0.05,
        };

        let result = bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            &boot_cfg,
        );
        assert!(
            result.is_err(),
            "all-invalid resamples must not return NaN CIs"
        );
    }

    #[test]
    fn bootstrap_pid3_is_deterministic() {
        let (v, l, d, a) = make_vlda(60, 123);
        let pid_cfg = experimental_pid3_config();
        let boot_cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 10,
            seed: 99,
            alpha: 0.05,
        };
        let r1 = bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            &boot_cfg,
        )
        .unwrap_err();
        let r2 = bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            &boot_cfg,
        )
        .unwrap_err();

        // Same seed reaches the same first invalid kNN shell.
        assert_eq!(r1.to_string(), r2.to_string());
    }

    #[test]
    fn bootstrap_pid3_can_reject_after_a_valid_direct_point_estimate() {
        let (v, l, d, a) = make_vlda(60, 55);
        let pid_cfg = experimental_pid3_config();
        let boot_cfg = BootstrapConfig {
            n_boot: 5,
            block_size: 10,
            seed: 0,
            alpha: 0.05,
        };
        let result = bootstrap_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            &boot_cfg,
        );

        let direct = pid3_isx(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &pid_cfg);
        assert!(direct.is_ok());
        assert!(matches!(
            result,
            Err(PidError::AmbiguousKthNeighborShell { .. })
        ));
    }

    #[test]
    fn permutation_pid3_produces_p_values() {
        let (v, l, d, a) = make_vlda(60, 42);
        let pid_cfg = experimental_pid3_config();
        let result = permutation_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            10, // Small for test speed.
            2,  // Shuffle D (noise source → p-values should be high).
            42,
        )
        .unwrap();
        assert_eq!(result.atoms.len(), 18);
        assert_eq!(result.n_perm, 10);
        assert_eq!(result.source_shuffled, 2);
        assert_eq!(result.tail, PermutationTail::Upper);
        // A successful inference uses the complete finite permutation set for every atom.
        assert!(result
            .atoms
            .iter()
            .all(|atom| atom.p_value.is_finite() && atom.n_valid == result.n_perm));
    }

    #[test]
    fn permutation_pid3_rejects_failed_and_nonfinite_transforms() {
        let failed = complete_pid3_permutation_values(
            Err(PidError::NumericalInstability {
                context: "synthetic permuted PID failure",
            }),
            1,
        );
        assert!(matches!(
            failed,
            Err(PidError::NumericalInstability {
                context: "synthetic permuted PID failure"
            })
        ));

        let antichain = Antichain3::try_from_sets(&[0b001]).unwrap();
        let nonfinite = Pid3Result {
            redundancies: Vec::new(),
            atoms: vec![crate::pid3::Pid3Atom {
                antichain,
                value: f64::NAN,
            }],
        };
        assert!(matches!(
            complete_pid3_permutation_values(Ok(nonfinite), 1),
            Err(PidError::NumericalInstability {
                context: "permutation_pid3 permutation"
            })
        ));
    }

    #[test]
    fn permutation_pid3_rejects_a_failed_transform_end_to_end() {
        // The observed (source-0, target) pairs are all distinct, but some source-0
        // permutations align equal source values with equal target values. At k=1 that
        // creates a zero joint radius and must invalidate the complete inference.
        let v = MatOwned::new(vec![0.0, 1.0, 0.0, 1.0], 4, 1).unwrap();
        let l = MatOwned::new(
            vec![
                3.837_994_630_055_094_4,
                3.120_142_197_049_379,
                -4.884_690_323_704_783,
                -4.553_090_691_658_043,
            ],
            4,
            1,
        )
        .unwrap();
        let d = MatOwned::new(
            vec![
                3.854_570_370_386_62,
                0.173_852_662_366_986_27,
                0.190_043_206_057_938,
                2.803_027_871_070_086_4,
            ],
            4,
            1,
        )
        .unwrap();
        let a = MatOwned::new(vec![0.0, 0.0, 2.0, 2.0], 4, 1).unwrap();
        let pid_cfg = Pid3Config {
            k: 1,
            ..experimental_pid3_config()
        };

        assert!(pid3_isx(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &pid_cfg).is_ok());
        assert!(permutation_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            40,
            0,
            7
        )
        .is_err());
    }

    #[test]
    fn permutation_pid3_rejects_bad_source_idx() {
        let (v, l, d, a) = make_vlda(60, 42);
        let pid_cfg = experimental_pid3_config();
        assert!(permutation_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            5,
            3, // Invalid source index.
            0
        )
        .is_err());
    }

    #[test]
    fn permutation_pid3_rejects_unallocatable_permutation_count_without_panicking() {
        let (v, l, d, a) = make_vlda(8, 42);

        let outcome = std::panic::catch_unwind(|| {
            permutation_pid3(
                v.as_ref(),
                l.as_ref(),
                d.as_ref(),
                a.as_ref(),
                &experimental_pid3_config(),
                usize::MAX,
                0,
                0,
            )
        });

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn pls_cv_selects_at_least_one_component() {
        let n = 50;
        let mut rng = SplitMix64::new(77);
        let mut x_data = Vec::with_capacity(n * 5);
        let mut y_data = Vec::with_capacity(n);
        for _ in 0..n {
            let sig = rng.normal();
            x_data.push(sig + 0.1 * rng.normal());
            for _ in 1..5 {
                x_data.push(rng.normal());
            }
            y_data.push(sig);
        }
        let x = MatRef::new(&x_data, n, 5).unwrap();
        let y = MatRef::new(&y_data, n, 1).unwrap();
        let result = pls_cv_select_components(x, y, 3).unwrap();
        assert_eq!(result.q2.len(), 3);
        assert!(result.best_components >= 1);
        assert!(result.best_components <= 3);
    }

    #[test]
    fn pls_cv_q2_is_invariant_to_uniform_extreme_target_scaling() {
        let x_data = [-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0];
        let y_data = [-2.8, -1.8, -1.2, 0.3, 0.7, 2.2, 2.7, 4.3];
        let y_huge: Vec<f64> = y_data.iter().map(|value| value * 1.0e200).collect();
        let y_tiny: Vec<f64> = y_data.iter().map(|value| value * 1.0e-200).collect();
        let x = MatRef::new(&x_data, x_data.len(), 1).unwrap();
        let y = MatRef::new(&y_data, y_data.len(), 1).unwrap();
        let huge = MatRef::new(&y_huge, y_huge.len(), 1).unwrap();
        let tiny = MatRef::new(&y_tiny, y_tiny.len(), 1).unwrap();

        let ordinary = pls_cv_select_components(x, y, 1).unwrap();
        let scaled = pls_cv_select_components(x, huge, 1).unwrap();
        let scaled_tiny = pls_cv_select_components(x, tiny, 1).unwrap();

        assert_eq!(ordinary.best_components, scaled.best_components);
        assert_eq!(ordinary.best_components, scaled_tiny.best_components);
        assert!((ordinary.q2[0] - scaled.q2[0]).abs() < 1.0e-12);
        assert!((ordinary.q2[0] - scaled_tiny.q2[0]).abs() < 1.0e-12);
    }

    #[test]
    fn pls_project_then_discrete_pid3_runs() {
        let (v, l, d, a) = make_vlda(60, 42);
        let cfg = PlsDiscretePid3Config {
            pls_components: 1,
            num_bins: 8,
            exploratory_allow_same_sample_fit: true,
        };
        let result =
            pls_project_then_discrete_pid3(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &cfg)
                .unwrap();
        assert_eq!(result.pid.atoms.len(), 18);
        assert_eq!(result.pls_components, 1);
        assert_eq!(result.num_bins, 8);
        assert_eq!(result.projected_dim, 1);
        assert_eq!(result.input_dims, [3, 3, 2, 1]);
    }

    #[test]
    fn pls_project_then_discrete_pid3_requires_same_sample_acknowledgement() {
        let (v, l, d, a) = make_vlda(20, 12);
        let cfg = PlsDiscretePid3Config {
            pls_components: 1,
            num_bins: 4,
            exploratory_allow_same_sample_fit: false,
        };
        let error =
            pls_project_then_discrete_pid3(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &cfg)
                .unwrap_err();
        assert!(matches!(
            error,
            PidError::InvalidConfig {
                context: "pls_project_then_discrete_pid3",
                ..
            }
        ));
    }

    #[test]
    fn screen_pid2_pairs_returns_all_pairs() {
        let n = 60;
        let mut rng = SplitMix64::new(42);
        let mut s0_data = Vec::with_capacity(n * 2);
        let mut s1_data = Vec::with_capacity(n * 2);
        let mut s2_data = Vec::with_capacity(n * 2);
        let mut t_data = Vec::with_capacity(n);
        for _ in 0..n {
            let sig = rng.normal();
            s0_data.push(sig + 0.1 * rng.normal());
            s0_data.push(rng.normal());
            s1_data.push(sig + 0.1 * rng.normal());
            s1_data.push(rng.normal());
            s2_data.push(rng.normal());
            s2_data.push(rng.normal());
            t_data.push(sig + 0.05 * rng.normal());
        }
        let s0 = MatOwned::new(s0_data, n, 2).unwrap();
        let s1 = MatOwned::new(s1_data, n, 2).unwrap();
        let s2 = MatOwned::new(s2_data, n, 2).unwrap();
        let t = MatOwned::new(t_data, n, 1).unwrap();
        let sources: Vec<MatRef<'_>> = vec![s0.as_ref(), s1.as_ref(), s2.as_ref()];
        let cfg = Pid2Config::default();
        let entries = screen_pid2_pairs(&sources, t.as_ref(), &cfg).unwrap();
        // 3 sources → C(3,2) = 3 pairs.
        assert_eq!(entries.len(), 3);
        // Sorted by descending synergy.
        for w in entries.windows(2) {
            assert!(w[0].result.synergy >= w[1].result.synergy);
        }
    }

    #[test]
    fn screen_pid2_pairs_propagates_invalid_config() {
        let (v, l, _, a) = make_vlda(20, 91);
        let sources = [v.as_ref(), l.as_ref()];
        let mut cfg = Pid2Config::default();
        cfg.ksg.k = 0;
        cfg.isx.k = 0;

        let result = screen_pid2_pairs(&sources, a.as_ref(), &cfg);
        assert!(
            result.is_err(),
            "invalid universal config must not become Ok([])"
        );
    }

    /// Helper: paired (x, y) columns with y = x + noise, returned as 1-col matrices.
    fn make_linear_pair(n: usize, noise: f64, seed: u64) -> (MatOwned, MatOwned) {
        let mut rng = SplitMix64::new(seed);
        let mut x_data = Vec::with_capacity(n);
        let mut y_data = Vec::with_capacity(n);
        for _ in 0..n {
            let x = rng.normal();
            x_data.push(x);
            y_data.push(x + noise * rng.normal());
        }
        (
            MatOwned::new(x_data, n, 1).unwrap(),
            MatOwned::new(y_data, n, 1).unwrap(),
        )
    }

    fn pearson_stat(mats: &[MatRef<'_>]) -> PidResult<Vec<f64>> {
        let x = mats[0];
        let y = mats[1];
        let n = x.nrows() as f64;
        let mx: f64 = (0..x.nrows()).map(|i| x.row(i)[0]).sum::<f64>() / n;
        let my: f64 = (0..y.nrows()).map(|i| y.row(i)[0]).sum::<f64>() / n;
        let mut cov = 0.0;
        let mut vx = 0.0;
        let mut vy = 0.0;
        for i in 0..x.nrows() {
            let a = x.row(i)[0] - mx;
            let b = y.row(i)[0] - my;
            cov += a * b;
            vx += a * a;
            vy += b * b;
        }
        Ok(vec![cov / (vx.sqrt() * vy.sqrt())])
    }

    #[test]
    fn bootstrap_rows_stats_is_deterministic_and_brackets_point() {
        let (x, y) = make_linear_pair(200, 0.5, 7);
        let cfg = BootstrapConfig {
            n_boot: 64,
            block_size: 1,
            seed: 11,
            alpha: 0.05,
        };
        let mats = [x.as_ref(), y.as_ref()];
        let scheme = RowResampleScheme::Subsample { subsample_len: 150 };
        let a = bootstrap_rows_stats(&mats, &cfg, scheme, pearson_stat).unwrap();
        let b = bootstrap_rows_stats(&mats, &cfg, scheme, pearson_stat).unwrap();
        assert_eq!(a, b);
        assert_eq!(a.effective_resample_len, 150);
        let s = &a.stats[0];
        assert_eq!(s.n_attempted, 64);
        assert_eq!(s.n_valid, 64);
        assert!(s.ci_low <= s.point_estimate + 0.05);
        assert!(s.ci_high >= s.point_estimate - 0.05);
        assert!(s.boot_se > 0.0 && s.boot_se < 0.2, "se={}", s.boot_se);
    }

    #[test]
    fn bootstrap_rows_stats_reports_rounded_subsample_length() {
        let (x, y) = make_linear_pair(100, 0.5, 19);
        let cfg = BootstrapConfig {
            n_boot: 2,
            block_size: 10,
            seed: 4,
            alpha: 0.05,
        };
        let result = bootstrap_rows_stats(
            &[x.as_ref(), y.as_ref()],
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 53 },
            pearson_stat,
        )
        .unwrap();

        assert_eq!(result.effective_resample_len, 50);
    }

    #[test]
    fn bootstrap_rows_stats_subsample_is_duplicate_free_for_ksg() {
        // Subsampling draws *distinct* rows, so KSG (which rejects duplicate-induced
        // zero kNN radii) succeeds with no jitter on every resample.
        let (x, y) = make_linear_pair(200, 0.5, 13);
        let ksg_cfg = crate::KsgConfig::default();
        let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
            Ok(vec![crate::ksg_mi(mats[0], mats[1], &ksg_cfg)?])
        };
        let cfg = BootstrapConfig {
            n_boot: 32,
            block_size: 1,
            seed: 3,
            alpha: 0.05,
        };
        let mats = [x.as_ref(), y.as_ref()];
        let sub = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 120 },
            stat,
        )
        .unwrap();
        assert_eq!(sub.stats[0].n_valid, 32);
        assert!(sub.stats[0].ci_low.is_finite());
        assert!(sub.stats[0].ci_high >= sub.stats[0].ci_low);
        assert!(sub.stats[0].ci_low <= sub.stats[0].point_estimate);
        assert!(sub.stats[0].ci_high >= sub.stats[0].point_estimate);
    }

    #[test]
    fn bootstrap_rows_stats_with_replacement_needs_jitter_for_ksg() {
        // With-replacement bootstrap without jitter produces duplicate rows that
        // make KSG fail on a resample; selective deletion is invalid, so the whole CI errors. A
        // tiny jitter rescues every draw. This pins the failure mode documented on the scheme.
        let (x, y) = make_linear_pair(150, 0.5, 17);
        let ksg_cfg = crate::KsgConfig::default();
        let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
            Ok(vec![crate::ksg_mi(mats[0], mats[1], &ksg_cfg)?])
        };
        let cfg = BootstrapConfig {
            n_boot: 16,
            block_size: 1,
            seed: 3,
            alpha: 0.05,
        };
        let mats = [x.as_ref(), y.as_ref()];
        let without = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
            stat,
        );
        assert!(without.is_err());

        let with = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            stat,
        )
        .unwrap();
        assert_eq!(with.stats[0].n_valid, 16);
        assert!(with.stats[0].ci_low.is_finite());
        assert!(with.stats[0].ci_high >= with.stats[0].ci_low);
    }

    #[test]
    fn bootstrap_rows_stats_rejects_bad_config() {
        let (x, y) = make_linear_pair(50, 0.5, 1);
        let mats = [x.as_ref(), y.as_ref()];
        let jit = RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 };
        let mut cfg = BootstrapConfig {
            n_boot: 0,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };
        assert!(bootstrap_rows_stats(&mats, &cfg, jit, pearson_stat).is_err());
        cfg.n_boot = 8;
        cfg.block_size = 0;
        assert!(bootstrap_rows_stats(&mats, &cfg, jit, pearson_stat).is_err());
        cfg.block_size = 50;
        assert!(bootstrap_rows_stats(&mats, &cfg, jit, pearson_stat).is_err());
        cfg.block_size = 1;
        cfg.alpha = 1.5;
        assert!(bootstrap_rows_stats(&mats, &cfg, jit, pearson_stat).is_err());
        cfg.alpha = 0.05;
        assert!(bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: -1.0 },
            pearson_stat
        )
        .is_err());
        // Subsample longer than n must be rejected.
        assert!(bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample {
                subsample_len: 1000
            },
            pearson_stat
        )
        .is_err());
        // Selecting every complete grid block is deterministic after temporal sorting and would
        // manufacture a zero-width pseudo-distribution.
        assert!(bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 50 },
            pearson_stat
        )
        .is_err());
        // Subsample shorter than block_size must be rejected.
        cfg.block_size = 10;
        assert!(bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 5 },
            pearson_stat
        )
        .is_err());
    }

    #[test]
    fn bootstrap_rows_stats_rejects_nonfinite_point_estimate() {
        let (x, y) = make_linear_pair(50, 0.5, 1);
        let mats = [x.as_ref(), y.as_ref()];
        let cfg = BootstrapConfig {
            n_boot: 8,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        let result = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 40 },
            |_| Ok(vec![f64::NAN]),
        );
        assert!(
            result.is_err(),
            "a non-finite point estimate must be rejected"
        );
    }

    #[test]
    fn bootstrap_jitter_scale_is_stable_and_skipped_when_unused() {
        let constant = MatOwned::new(vec![f64::MAX; 8], 8, 1).unwrap();
        let cfg = BootstrapConfig {
            n_boot: 4,
            block_size: 2,
            seed: 5,
            alpha: 0.1,
        };
        let jittered = bootstrap_rows_stats(
            &[constant.as_ref()],
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            |_| Ok(vec![0.0]),
        )
        .unwrap();
        assert_eq!(jittered.stats[0].n_valid, cfg.n_boot);

        // With no jitter, even a range whose variance is not representable need not have moments
        // computed merely to perform row selection without repeated indices.
        let extreme = MatOwned::new(vec![-f64::MAX, f64::MAX, -f64::MAX, f64::MAX], 4, 1).unwrap();
        let no_jitter = BootstrapConfig {
            n_boot: 3,
            block_size: 1,
            seed: 6,
            alpha: 0.1,
        };
        assert!(bootstrap_rows_stats(
            &[extreme.as_ref()],
            &no_jitter,
            RowResampleScheme::Subsample { subsample_len: 3 },
            |_| Ok(vec![0.0]),
        )
        .is_ok());
        assert!(bootstrap_rows_stats(
            &[extreme.as_ref()],
            &no_jitter,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            |_| Ok(vec![0.0]),
        )
        .is_err());
    }

    #[test]
    fn bootstrap_rows_stats_classifies_post_jitter_overflow_as_numerical_instability() {
        let extreme = MatOwned::new(vec![0.0, f64::MAX, 0.0, f64::MAX], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        let result = bootstrap_rows_stats(
            &[extreme.as_ref()],
            &config,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1.0 },
            |_| Ok(vec![0.0]),
        );

        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "bootstrap_rows_stats jittered resample"
            })
        ));
    }

    #[test]
    fn bootstrap_rows_stats_rejects_unallocatable_resample_count_without_panicking() {
        let matrix = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        let outcome = std::panic::catch_unwind(|| {
            bootstrap_rows_stats(
                &[matrix.as_ref()],
                &config,
                RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
                |_| Ok(vec![0.0]),
            )
        });

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn bootstrap_rows_stats_rejects_unallocatable_moving_block_indices_without_panicking() {
        let logical_matrix = MatRef::new(&[], usize::MAX, 0).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: usize::MAX - 1,
            seed: 0,
            alpha: 0.05,
        };

        let outcome = std::panic::catch_unwind(|| {
            bootstrap_rows_stats(
                &[logical_matrix],
                &config,
                RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
                |_| Ok(vec![0.0]),
            )
        });

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn quantized_bootstrap_inherits_unallocatable_resample_rejection_without_panicking() {
        let s1 = MatRef::new(&[0.0, 0.0, 1.0, 1.0], 4, 1).unwrap();
        let s2 = MatRef::new(&[0.0, 1.0, 0.0, 1.0], 4, 1).unwrap();
        let target = MatRef::new(&[0.0, 1.0, 1.0, 0.0], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        let outcome =
            std::panic::catch_unwind(|| bootstrap_quantized_sxpid2(s1, s2, target, 2, &config));

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn permutation_rows_pvalue_detects_signal_and_respects_null() {
        let ksg_cfg = crate::KsgConfig::default();
        let stat =
            |mats: &[MatRef<'_>]| -> PidResult<f64> { crate::ksg_mi(mats[0], mats[1], &ksg_cfg) };

        // Strong linear signal: p should be at the add-one floor 1/(M+1).
        let (x, y) = make_linear_pair(150, 0.3, 21);
        let mats = [x.as_ref(), y.as_ref()];
        let signal = permutation_rows_pvalue(&mats, 0, 99, 5, stat).unwrap();
        assert_eq!(signal.n_valid, 99);
        assert_eq!(signal.tail, PermutationTail::Upper);
        assert!(
            (signal.p_value - 1.0 / 100.0).abs() < 1e-12,
            "p={}",
            signal.p_value
        );

        // Independent pair: p should be large (deterministic for this seed; the
        // statistical claim is uniformity, this is a regression pin).
        let (x_a, _) = make_linear_pair(150, 0.3, 100);
        let (x_b, _) = make_linear_pair(150, 0.3, 200);
        let mats_null = [x_a.as_ref(), x_b.as_ref()];
        let null = permutation_rows_pvalue(&mats_null, 0, 99, 5, stat).unwrap();
        assert!(null.p_value > 0.1, "p={}", null.p_value);
    }

    #[test]
    fn permutation_rows_pvalue_is_deterministic_and_validates_input() {
        let (x, y) = make_linear_pair(80, 0.5, 33);
        let mats = [x.as_ref(), y.as_ref()];
        let stat = pearson_stat;
        let scalar = |m: &[MatRef<'_>]| -> PidResult<f64> { Ok(stat(m)?[0]) };
        let a = permutation_rows_pvalue(&mats, 0, 49, 9, scalar).unwrap();
        let b = permutation_rows_pvalue(&mats, 0, 49, 9, scalar).unwrap();
        assert_eq!(a, b);
        assert!(permutation_rows_pvalue(&mats, 2, 49, 9, scalar).is_err());
        assert!(permutation_rows_pvalue(&mats, 0, 0, 9, scalar).is_err());
        let empty: [MatRef<'_>; 0] = [];
        assert!(permutation_rows_pvalue(&empty, 0, 9, 9, scalar).is_err());
    }

    #[test]
    fn permutation_rows_rejects_unallocatable_logical_rows_without_panicking() {
        let logical_matrix = MatRef::new(&[], usize::MAX, 0).unwrap();

        let outcome = std::panic::catch_unwind(|| {
            permutation_rows_pvalue(&[logical_matrix], 0, 1, 0, |_| Ok(0.0))
        });

        assert!(matches!(outcome, Ok(Err(PidError::InvalidConfig { .. }))));
    }

    #[test]
    fn permutation_rows_pvalue_rejects_the_former_selective_16_of_40_null() {
        let x = MatOwned::new(vec![3.0, 0.0, 1.0, 2.0], 4, 1).unwrap();
        let mats = [x.as_ref()];

        // Pin the old failure exactly: with this seed, only 16 of 40 transforms passed
        // `first >= 2`, and 8 of those met the observed threshold of 3. The former
        // finite-only calculation therefore returned 9/17 instead of rejecting inference.
        let mut rng = SplitMix64::new(7);
        let mut selectively_valid = 0usize;
        let mut selectively_geq = 0usize;
        for _ in 0..40 {
            let perm = draw_permutation(
                PermutationScheme::FullShuffle,
                4,
                &mut rng,
                "selective permutation regression",
            )
            .unwrap();
            let value = x.as_ref().row(perm[0])[0];
            if value >= 2.0 {
                selectively_valid += 1;
                if value >= 3.0 {
                    selectively_geq += 1;
                }
            }
        }
        assert_eq!((selectively_valid, selectively_geq), (16, 8));
        let former_p = (1 + selectively_geq) as f64 / (1 + selectively_valid) as f64;
        assert_eq!(former_p.to_bits(), (9.0_f64 / 17.0).to_bits());

        let result = permutation_rows_pvalue(&mats, 0, 40, 7, |permuted| {
            let value = permuted[0].row(0)[0];
            if value >= 2.0 {
                Ok(value)
            } else {
                Err(PidError::NumericalInstability {
                    context: "synthetic selective permutation failure",
                })
            }
        });
        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "synthetic selective permutation failure"
            })
        ));
    }

    #[test]
    fn permutation_rows_pvalue_rejects_a_nonfinite_null_transform() {
        let x = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let mats = [x.as_ref()];
        let calls = std::cell::Cell::new(0usize);
        let result = permutation_rows_pvalue(&mats, 0, 5, 1, |_| {
            let call = calls.get();
            calls.set(call + 1);
            Ok(if call == 0 { 1.0 } else { f64::NAN })
        });

        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "permutation_rows_pvalue permutation statistic"
            })
        ));
        assert_eq!(calls.get(), 2, "observed plus the first invalid transform");
    }
}
