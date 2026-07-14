//! Pipeline functions that compose PLS projection, PID decomposition, and bootstrap
//! uncertainty quantification.
//!
//! These are convenience entry points for the common VLA analysis workflow:
//!
//! 1. `pls_project_then_pid3` — fit PLS on high-dimensional embeddings, project into a
//!    low-dimensional task-relevant subspace, then run the continuous 3-source I^sx_∩ PID
//!    ([`pid3_isx`]; NOT the discrete SxPID of the `sxpid` module).
//!
//! The former with-replacement continuous PID3 bootstrap was removed in the 0.9 review surface
//! while shaping the proposed 1.0 boundary because duplicated observations violate the estimator's
//! continuous-sample conditions and raw percentiles were not calibrated confidence intervals.

use crate::bootstrap::{
    BlockResamplingAlgorithmRevision, BlockResamplingProvenance, BootstrapConfig,
    CancellationToken, StatisticCallbackDeclaration,
};
use crate::concat_horiz;
use crate::discrete_pid::same_sample_quantized_imin_pid3;
use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use crate::pid2::{
    pid2_isx_with_budget, pid2_resource_estimate_for_threads, Pid2Config, Pid2Result,
};
use crate::pid3::{
    pid3_isx, pid3_isx_with_budget, pid3_resource_estimate_for_threads, Antichain3, Pid3Config,
    Pid3Result,
};
use crate::pls::PlsProjector;
use crate::preprocess::SplitMix64;
use crate::resource::{ResourceBudget, ResourceEstimate};
use crate::stats::{finite_mean, finite_mean_std_population, finite_mean_std_sample};
use crate::sxpid::quantized_sxpid2;

fn try_vec_with_capacity<T>(capacity: usize, context: &'static str) -> PidResult<Vec<T>> {
    try_vec_with_capacity_budget(capacity, context, ResourceBudget::default())
}

fn try_vec_with_capacity_budget<T>(
    capacity: usize,
    context: &'static str,
    budget: ResourceBudget,
) -> PidResult<Vec<T>> {
    crate::resource::try_vec_with_capacity(context, capacity, budget)
}

fn checked_add_resource(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_add(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_mul_resource(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_len(operation: &'static str, left: usize, right: usize) -> PidResult<usize> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
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
#[derive(Debug)]
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
#[cfg(any())]
pub struct Pid3BootstrapAtom {
    /// The antichain identifying this atom on the PID lattice.
    pub antichain: Antichain3,
    /// Point estimate on the original (un-resampled) data.
    pub point_estimate: f64,
    /// Mean of the with-replacement resampling distribution.
    pub resample_mean: f64,
    /// Sample standard deviation of the resampling distribution; not a generally calibrated kNN
    /// standard error.
    pub resample_standard_deviation: f64,
    /// Lower raw resampling percentile; not a generally calibrated kNN confidence bound.
    pub percentile_lower: f64,
    /// Upper raw resampling percentile; not a generally calibrated kNN confidence bound.
    pub percentile_upper: f64,
}

/// Legacy result of the deprecated [`bootstrap_pid3`].
#[derive(Debug)]
#[cfg(any())]
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
/// This is a with-replacement moving-block bootstrap. Repeated blocks duplicate rows, so observed
/// continuous-sample incompatibility is rejected before shell estimation. Independently, a sample
/// with unique rows may still have an ambiguous positive k-th-neighbor boundary. Even resamples
/// that happen to remain finite do not provide a generally reliable KSG uncertainty guarantee. Prefer
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
/// decomposition is not complete and finite,
/// [`PidError::ObservedContinuousSampleIncompatibility`] when exact ties violate ideal
/// continuous-sample conditions, and [`PidError::AmbiguousKthNeighborShell`] for a separate
/// positive boundary tie.
#[cfg(any())]
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
    // index (alpha >= 2 panics) or inverted raw percentiles (alpha in (1,2)). Reject up front.
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
    let worker_heap_bytes = (n as u128)
        .checked_mul((dv as u128) + (dl as u128) + (dd as u128) + (da as u128))
        .and_then(|elements| elements.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: "bootstrap_pid3",
        })?;
    let per_resample: Vec<PidResult<Vec<f64>>> = crate::par::slice_map_index_ordered(
        &resample_indices,
        ResourceBudget::default(),
        worker_heap_bytes,
        |indices| {
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
            let mut values = try_vec_with_capacity_budget(
                result.atoms.len(),
                "bootstrap_pid3 resample atoms",
                ResourceBudget::default(),
            )?;
            values.extend(result.atoms.iter().map(|atom| atom.value));
            if values.len() != n_atoms || values.iter().any(|value| !value.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context: "bootstrap_pid3 resample",
                });
            }
            Ok(values)
        },
    )?;

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
                resample_mean: mean,
                resample_standard_deviation: se,
                percentile_lower: values[lo_idx],
                percentile_upper: values[hi_idx],
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
///   The permutation APIs retain every transform failure and withhold the tail fraction, so they
///   never select a transformation-dependent subset.
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
#[non_exhaustive]
pub enum PermutationScheme {
    /// Independent full-row Fisher–Yates shuffle (exchangeable/i.i.d. rows only).
    FullShuffle,
    /// Fisher–Yates shuffle of fixed, contiguous blocks, preserving within-block order.
    ///
    /// Requires `block_size >= 1`, `n % block_size == 0`, and at least two blocks.
    /// Draws are sampled with replacement and are uniform over the permutations of the
    /// `n / block_size` block labels, including the identity. The add-one result is a
    /// Monte Carlo permutation p-value under exchangeability of the whole blocks,
    /// provided every transform evaluates successfully and finitely (otherwise the report
    /// retains the failures and has no tail fraction). Choosing a block size does not itself make
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
#[non_exhaustive]
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

/// Declared exchangeability/stationarity assumption defining a permutation or surrogate null.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum PermutationNullAssumption {
    /// Individual rows are exchangeable under the null.
    ExchangeableRows,
    /// Fixed contiguous blocks of the recorded size are exchangeable under the null.
    ExchangeableBlocks { block_size: usize },
    /// The aligned multivariate series is stationary enough for circular shifts to be meaningful.
    WeaklyStationarySeries { minimum_shift: usize },
}

/// Calibration claim supported by the selected transformation family.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum PermutationCalibration {
    /// Add-one Monte Carlo p-value under the declared exchangeability null.
    MonteCarloPValue,
    /// Restricted circular-shift tail fraction; a surrogate score, not an exact p-value.
    ApproximateSurrogateScore,
}

/// Predeclared multiple-testing family identity and size.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub struct PermutationFamily {
    /// Caller-assigned stable identifier shared by all hypotheses in the family.
    pub id: u64,
    /// Total number of hypotheses declared before observing their outcomes.
    pub size: usize,
}

impl PermutationFamily {
    /// Construct a nonempty predeclared family.
    pub fn new(id: u64, size: usize) -> PidResult<Self> {
        if size == 0 {
            return Err(PidError::InvalidConfig {
                context: "PermutationFamily::new",
                message: "family size must be positive",
            });
        }
        Ok(Self { id, size })
    }

    fn standalone(size: usize) -> Self {
        debug_assert!(size > 0);
        Self { id: 0, size }
    }

    fn validate(self, context: &'static str) -> PidResult<()> {
        if self.size == 0 {
            Err(PidError::InvalidConfig {
                context,
                message: "permutation family size must be positive",
            })
        } else {
            Ok(())
        }
    }
}

/// Versioned, typed permutation/surrogate null specification and provenance.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum PermutationAlgorithmRevision {
    SeededRowTransformV1,
}

/// Versioned, typed permutation/surrogate null specification and provenance.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub struct PermutationNull {
    pub scheme: PermutationScheme,
    pub assumption: PermutationNullAssumption,
    pub calibration: PermutationCalibration,
    pub tail: PermutationTail,
    pub seed: u64,
    pub algorithm_revision: PermutationAlgorithmRevision,
    pub family: PermutationFamily,
}

impl PermutationNull {
    /// Construct the null specification implied by `scheme`, with explicit family provenance.
    pub fn new(
        scheme: PermutationScheme,
        tail: PermutationTail,
        seed: u64,
        family: PermutationFamily,
    ) -> PidResult<Self> {
        family.validate("PermutationNull::new")?;
        let (assumption, calibration) = match scheme {
            PermutationScheme::FullShuffle => (
                PermutationNullAssumption::ExchangeableRows,
                PermutationCalibration::MonteCarloPValue,
            ),
            PermutationScheme::BlockShuffle { block_size } => (
                PermutationNullAssumption::ExchangeableBlocks { block_size },
                PermutationCalibration::MonteCarloPValue,
            ),
            PermutationScheme::CircularShift { min_shift } => (
                PermutationNullAssumption::WeaklyStationarySeries {
                    minimum_shift: min_shift,
                },
                PermutationCalibration::ApproximateSurrogateScore,
            ),
        };
        Ok(Self {
            scheme,
            assumption,
            calibration,
            tail,
            seed,
            algorithm_revision: PermutationAlgorithmRevision::SeededRowTransformV1,
            family,
        })
    }
}

/// Status of one requested permutation/surrogate transform.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub enum PermutationReplicateStatus {
    /// Transform produced the declared finite statistic vector.
    Complete { statistics: Vec<f64> },
    /// Transform failed; the exact structured reason is retained.
    Failed { error: PidError },
}

/// Indexed outcome for one requested permutation/surrogate transform.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct PermutationReplicateOutcome {
    pub replicate_index: usize,
    pub status: PermutationReplicateStatus,
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
            if !n.is_multiple_of(block_size) {
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
    budget: ResourceBudget,
) -> PidResult<Vec<usize>> {
    match scheme {
        PermutationScheme::FullShuffle => {
            let mut perm = try_vec_with_capacity_budget(n, context, budget)?;
            perm.extend(0..n);
            for i in (1..n).rev() {
                let j = uniform_index(rng, i + 1);
                perm.swap(i, j);
            }
            Ok(perm)
        }
        PermutationScheme::BlockShuffle { block_size } => {
            let n_blocks = n / block_size; // validated: exact division and >= 2
            let mut blocks = try_vec_with_capacity_budget(n_blocks, context, budget)?;
            blocks.extend(0..n_blocks);
            for i in (1..n_blocks).rev() {
                let j = uniform_index(rng, i + 1);
                blocks.swap(i, j);
            }

            let mut perm = try_vec_with_capacity_budget(n, context, budget)?;
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
            let mut perm = try_vec_with_capacity_budget(n, context, budget)?;
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
    /// [`PermutationPid3Result::null`]. `None` means at least one requested transform failed; the
    /// individual reasons are retained in [`PermutationPid3Result::replicates`].
    pub tail_fraction: Option<f64>,
    /// Number of complete, finite permutations in the null distribution. A tail fraction is
    /// present only when this equals the requested count. For [`PermutationScheme::CircularShift`],
    /// it is an approximate surrogate score rather than an exact p-value.
    pub n_valid: usize,
}

/// Result of [`permutation_pid3`].
#[derive(Debug)]
pub struct PermutationPid3Result {
    /// Complete observed result, including experimental/support/dimension/warning metadata.
    pub point_estimate: Pid3Result,
    pub atoms: Vec<PermutationPid3Atom>,
    /// Every requested transform, including structured failures, in deterministic order.
    pub replicates: Vec<PermutationReplicateOutcome>,
    /// Number of transforms requested. See per-atom `n_valid` and [`Self::replicates`] for
    /// completeness.
    pub n_perm: usize,
    pub source_shuffled: usize,
    /// Typed null assumptions, calibration, seed/revision, and family definition.
    pub null: PermutationNull,
}

/// Estimate retained atom distributions and one simultaneously materialized three-source
/// permutation and the repeated continuous PID3 estimator work.
pub fn permutation_pid3_resource_estimate(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    cfg: &Pid3Config,
    n_perm: usize,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "permutation_pid3";
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
            context: OPERATION,
            left_rows: n,
            right_rows,
        });
    }
    if n_perm == 0 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "n_perm must be > 0",
        });
    }
    let source_columns = [v.ncols(), l.ncols(), d.ncols()]
        .into_iter()
        .try_fold(0_u128, |sum, columns| {
            checked_add_resource(OPERATION, sum, columns as u128)
        })?;
    let n = n as u128;
    let atom_count = 18_u128;
    let bytes = [
        checked_mul_resource(
            OPERATION,
            checked_mul_resource(OPERATION, 2, n)?,
            std::mem::size_of::<usize>() as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            checked_mul_resource(OPERATION, n, source_columns)?,
            std::mem::size_of::<f64>() as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            n_perm as u128,
            std::mem::size_of::<PermutationReplicateOutcome>() as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            checked_mul_resource(OPERATION, atom_count, n_perm as u128)?,
            std::mem::size_of::<f64>() as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            atom_count,
            std::mem::size_of::<PermutationPid3Atom>() as u128,
        )?,
    ]
    .into_iter()
    .try_fold(0_u128, |sum, value| {
        checked_add_resource(OPERATION, sum, value)
    })?;
    let work_per_permutation = checked_add_resource(
        OPERATION,
        n,
        checked_mul_resource(OPERATION, n, source_columns)?,
    )?;
    let estimator = pid3_resource_estimate_for_threads(v, l, d, a, cfg, max_threads)?;
    let estimator_calls = (n_perm as u128)
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: checked_add_resource(OPERATION, bytes, estimator.estimated_bytes)?,
        pairwise_distances: checked_mul_resource(
            OPERATION,
            estimator_calls,
            estimator.pairwise_distances,
        )?,
        operations_hint: checked_add_resource(
            OPERATION,
            checked_mul_resource(OPERATION, n_perm as u128, work_per_permutation)?,
            checked_mul_resource(OPERATION, estimator_calls, estimator.operations_hint)?,
        )?,
    })
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
/// A tail fraction is reported only if every requested permutation produces a complete, finite
/// PID decomposition; otherwise all failure reasons are retained in the returned report.
///
/// # Errors
///
/// Returns an error for invalid inputs or configuration, if the requested null distribution
/// cannot be reserved safely, or if the observed PID cannot be computed completely and finitely.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, seed, tail, and budget are scientific provenance"
)]
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
    permutation_pid3_with_budget(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        seed,
        ResourceBudget::default(),
    )
}

/// [`permutation_pid3`] under an explicit permutation-materialization budget.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, seed, tail, and budget are scientific provenance"
)]
pub fn permutation_pid3_with_budget(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    seed: u64,
    budget: ResourceBudget,
) -> PidResult<PermutationPid3Result> {
    permutation_pid3_with_tail_and_budget(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        seed,
        PermutationScheme::FullShuffle,
        PermutationTail::Upper,
        budget,
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
/// Failed/non-finite transforms are retained and make every atom tail fraction unavailable; no
/// transform-dependent successful subset is scored.
///
/// # Errors
///
/// Returns an error for an invalid source, permutation count, or scheme; if the requested null
/// distribution cannot be reserved safely; if the observed PID cannot be computed finitely; or
/// if the observed PID cannot be computed finitely.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, seed, tail, and budget are scientific provenance"
)]
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
    permutation_pid3_with_tail_and_budget(
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
        ResourceBudget::default(),
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
/// Failed/non-finite transforms are retained and make every atom tail fraction unavailable; no
/// transform-dependent successful subset is scored.
///
/// # Errors
///
/// Returns an error for an invalid source, permutation count, or scheme; if the requested null
/// distribution cannot be reserved safely; if the observed PID cannot be computed finitely; or
/// if the observed PID cannot be computed finitely.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, seed, tail, and budget are scientific provenance"
)]
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
    permutation_pid3_with_tail_and_budget(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        seed,
        scheme,
        tail,
        ResourceBudget::default(),
    )
}

/// [`permutation_pid3_with_tail`] under an explicit permutation-materialization budget.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, seed, tail, and budget are scientific provenance"
)]
pub fn permutation_pid3_with_tail_and_budget(
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
    budget: ResourceBudget,
) -> PidResult<PermutationPid3Result> {
    let null = PermutationNull::new(scheme, tail, seed, PermutationFamily::standalone(18))?;
    permutation_pid3_under_null_with_budget(v, l, d, a, pid_cfg, n_perm, source_idx, null, budget)
}

/// PID3 permutation/surrogate report under a fully typed null specification.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, source, count, and budget are scientific provenance"
)]
pub fn permutation_pid3_under_null_with_budget(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    null: PermutationNull,
    budget: ResourceBudget,
) -> PidResult<PermutationPid3Result> {
    let cancellation = CancellationToken::new();
    permutation_pid3_under_null_with_cancellation(
        v,
        l,
        d,
        a,
        pid_cfg,
        n_perm,
        source_idx,
        null,
        budget,
        &cancellation,
    )
}

/// [`permutation_pid3_under_null_with_budget`] with cooperative cancellation checks.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit matrices, null, source, count, budget, and token are scientific provenance"
)]
pub fn permutation_pid3_under_null_with_cancellation(
    v: MatRef<'_>,
    l: MatRef<'_>,
    d: MatRef<'_>,
    a: MatRef<'_>,
    pid_cfg: &Pid3Config,
    n_perm: usize,
    source_idx: usize,
    null: PermutationNull,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
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
    null.family.validate("permutation_pid3")?;
    validate_permutation_scheme("permutation_pid3", null.scheme, n)?;
    budget.check(
        "permutation_pid3",
        permutation_pid3_resource_estimate(v, l, d, a, pid_cfg, n_perm, budget.max_threads)?,
    )?;
    cancellation.check("permutation_pid3", 0, n_perm + 1)?;

    // Observed PID on real data.
    let observed = pid3_isx_with_budget(v, l, d, a, pid_cfg, budget)?;
    if observed.atoms.iter().any(|atom| !atom.value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "permutation_pid3 point estimate",
        });
    }

    let mut rng = SplitMix64::new(null.seed);
    let n_atoms = observed.atoms.len();
    let mut replicates = try_vec_with_capacity_budget::<PermutationReplicateOutcome>(
        n_perm,
        "permutation_pid3 outcomes",
        budget,
    )?;

    let dv = v.ncols();
    let dl = l.ncols();
    let dd = d.ncols();

    for replicate_index in 0..n_perm {
        cancellation.check("permutation_pid3", replicate_index + 1, n_perm + 1)?;
        let evaluation = (|| -> PidResult<Vec<f64>> {
            let perm = draw_permutation(null.scheme, n, &mut rng, "permutation_pid3", budget)?;

            let shuffle = |mat: MatRef<'_>, dim: usize| -> PidResult<MatOwned> {
                let data_len = n.checked_mul(dim).ok_or(PidError::InvalidConfig {
                    context: "permutation_pid3",
                    message: "shuffled matrix length overflow",
                })?;
                let mut data = try_vec_with_capacity_budget(data_len, "permutation_pid3", budget)?;
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
                let mut data = try_vec_with_capacity_budget(data_len, "permutation_pid3", budget)?;
                for i in 0..n {
                    data.extend_from_slice(mat.row(i));
                }
                MatOwned::new(data, n, dim)
            };

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

            complete_pid3_permutation_values(
                pid3_isx_with_budget(vp.as_ref(), lp.as_ref(), dp.as_ref(), a, pid_cfg, budget),
                n_atoms,
                budget,
            )
        })();
        let status = match evaluation {
            Err(error @ PidError::Cancelled { .. }) => return Err(error),
            Err(error) => PermutationReplicateStatus::Failed { error },
            Ok(statistics) => PermutationReplicateStatus::Complete { statistics },
        };
        replicates.push(PermutationReplicateOutcome {
            replicate_index,
            status,
        });
    }

    let n_valid = replicates
        .iter()
        .filter(|replicate| {
            matches!(
                replicate.status,
                PermutationReplicateStatus::Complete { .. }
            )
        })
        .count();
    let all_complete = n_valid == n_perm;
    let mut atoms = try_vec_with_capacity_budget(n_atoms, "permutation_pid3 summaries", budget)?;
    for (idx, atom) in observed.atoms.iter().enumerate() {
        let tail_fraction = if all_complete {
            let mut n_extreme = 0usize;
            for replicate in &replicates {
                let PermutationReplicateStatus::Complete { statistics } = &replicate.status else {
                    return Err(PidError::NumericalInstability {
                        context: "permutation_pid3 outcome coherence",
                    });
                };
                if null.tail.contains(statistics[idx], atom.value) {
                    n_extreme += 1;
                }
            }
            Some((1 + n_extreme) as f64 / (1 + n_perm) as f64)
        } else {
            None
        };
        atoms.push(PermutationPid3Atom {
            antichain: atom.antichain,
            observed: atom.value,
            tail_fraction,
            n_valid,
        });
    }

    Ok(PermutationPid3Result {
        point_estimate: observed,
        atoms,
        replicates,
        n_perm,
        source_shuffled: source_idx,
        null,
    })
}

/// Convert one permuted PID evaluation into the complete finite atom vector required for
/// permutation inference. Accepting the fallible evaluation directly makes both failure paths
/// explicit: estimator errors propagate, while malformed/non-finite successful results become a
/// numerical-instability error.
fn complete_pid3_permutation_values(
    result: PidResult<Pid3Result>,
    expected_atoms: usize,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    let result = result?;
    let mut values =
        try_vec_with_capacity_budget(expected_atoms, "permutation_pid3 values", budget)?;
    values.extend(result.atoms.iter().map(|atom| atom.value));
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
#[derive(Debug)]
#[non_exhaustive]
pub struct PlsCvResult {
    /// Every candidate and every leave-one-out fold, including structured failures.
    pub candidates: Vec<PlsCvCandidateOutcome>,
    /// Most parsimonious component count maximizing finite complete-candidate Q². `None` means no
    /// candidate completed every predeclared fold; failures remain available in `candidates`.
    pub best_components: Option<usize>,
    /// Total number of candidate components tested.
    pub max_components: usize,
}

/// Status of one held-out PLS CV fold.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub enum PlsCvFoldStatus {
    /// Fit and held-out prediction completed and contributed to PRESS.
    Complete,
    /// Fit, transform, or prediction failed; the exact reason is retained.
    Failed { error: PidError },
}

/// Outcome of one predeclared held-out row for one component candidate.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct PlsCvFoldOutcome {
    pub held_out_row: usize,
    pub status: PlsCvFoldStatus,
}

/// Completeness and Q² status for one candidate component count.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub enum PlsCvCandidateStatus {
    /// Every fold completed; Q² is finite and comparable across candidates.
    Complete { q2: f64 },
    /// One or more folds failed, so no selectively reduced Q² is reported.
    Incomplete { failed_folds: usize },
    /// All folds ran but the aggregate Q² ratio was not representable.
    Failed { error: PidError },
}

/// Full outcome for one candidate component count.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct PlsCvCandidateOutcome {
    pub components: usize,
    pub status: PlsCvCandidateStatus,
    pub folds: Vec<PlsCvFoldOutcome>,
}

/// Conservative retained/scratch estimate for [`pls_cv_select_components_with_budget`].
pub fn pls_cv_select_components_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_components: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "pls_cv_select_components";
    let n = x.nrows();
    let d_x = x.ncols();
    let d_y = y.ncols();
    if y.nrows() != n {
        return Err(PidError::RowCountMismatch {
            context: OPERATION,
            left_rows: n,
            right_rows: y.nrows(),
        });
    }
    let components = max_components.min(d_x.min(n.saturating_sub(1)));
    if components == 0 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "max_components must be >= 1 after clipping",
        });
    }
    if components > crate::pls::MAX_NALGEBRA_SOLVER_COMPONENTS {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "nalgebra_solver_components",
            requested: components as u128,
            limit: crate::pls::MAX_NALGEBRA_SOLVER_COMPONENTS as u128,
        });
    }
    let train_n = n.saturating_sub(1) as u128;
    let n = n as u128;
    let d_x = d_x as u128;
    let d_y = d_y as u128;
    let k = components as u128;
    let train_elements = checked_mul_resource(
        OPERATION,
        train_n,
        checked_add_resource(OPERATION, d_x, d_y)?,
    )?;
    let centered = train_elements;
    let metadata = checked_mul_resource(OPERATION, 3, checked_add_resource(OPERATION, d_x, d_y)?)?;
    let fitted = checked_add_resource(
        OPERATION,
        checked_mul_resource(OPERATION, 2, checked_mul_resource(OPERATION, k, d_x)?)?,
        checked_mul_resource(OPERATION, k, d_y)?,
    )?;
    let nipals_scratch = [
        checked_mul_resource(OPERATION, 3, train_n)?,
        checked_mul_resource(OPERATION, 2, d_x)?,
        d_y,
    ]
    .into_iter()
    .try_fold(0_u128, |sum, value| {
        checked_add_resource(OPERATION, sum, value)
    })?;
    let qr_scratch = checked_add_resource(
        OPERATION,
        checked_mul_resource(OPERATION, 6, checked_mul_resource(OPERATION, k, k)?)?,
        checked_mul_resource(OPERATION, d_x, k)?,
    )?;
    let retained = [
        components as u128,
        d_y,
        n,
        train_elements,
        centered,
        metadata,
        fitted,
        nipals_scratch,
        qr_scratch,
    ]
    .into_iter()
    .try_fold(0_u128, |sum, value| {
        checked_add_resource(OPERATION, sum, value)
    })?;
    let component_sum = checked_mul_resource(OPERATION, k, k + 1)? / 2;
    let per_component_iteration = checked_mul_resource(
        OPERATION,
        train_n,
        checked_mul_resource(OPERATION, 2, checked_add_resource(OPERATION, d_x, d_y)?)?,
    )?;
    let fit_work = checked_mul_resource(
        OPERATION,
        checked_mul_resource(OPERATION, n, component_sum)?,
        checked_mul_resource(OPERATION, 200, per_component_iteration)?,
    )?;
    let prediction_work = checked_mul_resource(
        OPERATION,
        checked_mul_resource(OPERATION, n, component_sum)?,
        checked_mul_resource(OPERATION, d_x, d_y.max(1))?,
    )?;
    let numeric_bytes =
        checked_mul_resource(OPERATION, retained, std::mem::size_of::<f64>() as u128)?;
    let candidate_bytes = checked_mul_resource(
        OPERATION,
        k,
        std::mem::size_of::<PlsCvCandidateOutcome>() as u128,
    )?;
    let fold_bytes = checked_mul_resource(
        OPERATION,
        checked_mul_resource(OPERATION, k, n)?,
        std::mem::size_of::<PlsCvFoldOutcome>() as u128,
    )?;
    Ok(ResourceEstimate {
        estimated_bytes: checked_add_resource(
            OPERATION,
            numeric_bytes,
            checked_add_resource(OPERATION, candidate_bytes, fold_bytes)?,
        )?,
        pairwise_distances: 0,
        operations_hint: checked_add_resource(OPERATION, fit_work, prediction_work)?,
    })
}

/// Leave-one-out cross-validation to select the optimal number of PLS components.
///
/// For each candidate `k` in 1..=max_components, this computes Q² = 1 - PRESS/SS_total,
/// where PRESS is the sum of squared prediction errors from LOO-CV and SS_total is the
/// total sum of squares of the target.
///
/// Candidate fitting is nested inside each training fold, and fold-specific latent coordinates
/// are used only to predict that fold's held-out row; they are never pooled into one kNN cloud.
/// Every fold outcome is retained. A candidate with any failed fold has no Q² value and cannot be
/// selected; if every candidate is incomplete, `best_components` is `None`.
///
/// `x` is the source matrix (n×d_x) and `y` is the target (n×d_y).
pub fn pls_cv_select_components(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_components: usize,
) -> PidResult<PlsCvResult> {
    pls_cv_select_components_with_budget(x, y, max_components, ResourceBudget::default())
}

/// [`pls_cv_select_components`] under an explicit aggregate fold/solver budget.
pub fn pls_cv_select_components_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_components: usize,
    budget: ResourceBudget,
) -> PidResult<PlsCvResult> {
    let cancellation = CancellationToken::new();
    pls_cv_select_components_with_cancellation(x, y, max_components, budget, &cancellation)
}

/// [`pls_cv_select_components_with_budget`] with cooperative checks between folds and inside PLS
/// fitting iterations.
pub fn pls_cv_select_components_with_cancellation(
    x: MatRef<'_>,
    y: MatRef<'_>,
    max_components: usize,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
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
    budget.check(
        "pls_cv_select_components",
        pls_cv_select_components_resource_estimate(x, y, max_components)?,
    )?;
    let total_folds = max_components
        .checked_mul(n)
        .ok_or(PidError::SizeOverflow {
            operation: "pls_cv_select_components",
        })?;
    cancellation.check("pls_cv_select_components", 0, total_folds)?;

    // Compute SS_total.
    let mut y_mean = crate::resource::try_vec_filled(
        "pls_cv_select_components target means",
        d_y,
        0.0f64,
        budget,
    )?;
    for (j, mean) in y_mean.iter_mut().enumerate() {
        let mut column =
            try_vec_with_capacity_budget(n, "pls_cv_select_components target column", budget)?;
        column.extend((0..n).map(|i| y.row(i)[j]));
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

    let mut candidates = try_vec_with_capacity_budget(
        max_components,
        "pls_cv_select_components candidates",
        budget,
    )?;
    for k in 1..=max_components {
        let mut press = ScaledSquareSum::default();
        let mut folds =
            try_vec_with_capacity_budget(n, "pls_cv_select_components fold outcomes", budget)?;
        // LOO-CV: for each held-out sample, fit PLS on the rest and predict.
        for held_out in 0..n {
            let completed_folds = (k - 1)
                .checked_mul(n)
                .and_then(|completed| completed.checked_add(held_out))
                .ok_or(PidError::SizeOverflow {
                    operation: "pls_cv_select_components",
                })?;
            cancellation.check("pls_cv_select_components", completed_folds, total_folds)?;
            let fold_result = (|| -> PidResult<()> {
                let train_n = n - 1;
                let x_train_len = checked_len("pls_cv_select_components", train_n, d_x)?;
                let y_train_len = checked_len("pls_cv_select_components", train_n, d_y)?;
                let mut x_train_data = try_vec_with_capacity_budget(
                    x_train_len,
                    "pls_cv_select_components training X",
                    budget,
                )?;
                let mut y_train_data = try_vec_with_capacity_budget(
                    y_train_len,
                    "pls_cv_select_components training Y",
                    budget,
                )?;
                for i in 0..n {
                    if i == held_out {
                        continue;
                    }
                    x_train_data.extend_from_slice(x.row(i));
                    y_train_data.extend_from_slice(y.row(i));
                }
                let x_train = MatOwned::new(x_train_data, train_n, d_x)?;
                let y_train = MatOwned::new(y_train_data, train_n, d_y)?;
                let pls = PlsProjector::fit_with_budget_and_cancellation(
                    x_train.as_ref(),
                    y_train.as_ref(),
                    k,
                    budget,
                    cancellation,
                )?;
                let x_ho = MatRef::new(x.row(held_out), 1, d_x)?;
                let y_hat = pls.predict_with_budget(x_ho, budget)?;
                let pred = y_hat.as_ref().row(0);
                let ho_row = y.row(held_out);
                for j in 0..d_y {
                    press.add_difference(
                        ho_row[j],
                        pred[j],
                        "pls_cv_select_components: prediction error sum of squares",
                    )?;
                }
                Ok(())
            })();
            let status = match fold_result {
                Err(error @ PidError::Cancelled { .. }) => return Err(error),
                Err(error) => PlsCvFoldStatus::Failed { error },
                Ok(()) => PlsCvFoldStatus::Complete,
            };
            folds.push(PlsCvFoldOutcome {
                held_out_row: held_out,
                status,
            });
        }
        let failed_folds = folds
            .iter()
            .filter(|fold| matches!(fold.status, PlsCvFoldStatus::Failed { .. }))
            .count();
        let status = if failed_folds > 0 {
            PlsCvCandidateStatus::Incomplete { failed_folds }
        } else {
            match press
                .ratio(ss_total)
                .map(|ratio| 1.0 - ratio)
                .filter(|value| value.is_finite())
            {
                Some(q2) => PlsCvCandidateStatus::Complete { q2 },
                None => PlsCvCandidateStatus::Failed {
                    error: PidError::NumericalInstability {
                        context: "pls_cv_select_components: Q2 aggregation",
                    },
                },
            }
        };
        candidates.push(PlsCvCandidateOutcome {
            components: k,
            status,
            folds,
        });
    }

    let best_q2 = candidates
        .iter()
        .filter_map(|candidate| match candidate.status {
            PlsCvCandidateStatus::Complete { q2 } => Some(q2),
            _ => None,
        })
        .fold(None, |best: Option<f64>, value| {
            Some(best.map_or(value, |current| current.max(value)))
        });
    let best_components = best_q2.and_then(|best| {
        candidates
            .iter()
            .find_map(|candidate| match candidate.status {
                PlsCvCandidateStatus::Complete { q2 } if q2 >= best - 1e-9 => {
                    Some(candidate.components)
                }
                _ => None,
            })
    });

    Ok(PlsCvResult {
        candidates,
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
#[derive(Debug)]
pub struct PlsDiscretePid3Result {
    pub pid: crate::discrete_pid::IminPid3Result,
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
/// a separate evaluation set, use fitted quantizers, and call stable `imin_pid3` there. Unlike the continuous estimator,
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

    let pid = same_sample_quantized_imin_pid3(
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
#[derive(Debug)]
pub struct Pid2ScreenEntry {
    /// Source pair indices (i, j) into the sources list.
    pub source_i: usize,
    pub source_j: usize,
    pub result: Pid2Result,
}

/// Estimate retained result headers plus the sequential PID2 estimator work for every pair.
pub fn screen_pid2_pairs_resource_estimate(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &Pid2Config,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "screen_pid2_pairs";
    let source_count = sources.len();
    if source_count < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "need at least two sources",
        });
    }
    let count = source_count as u128;
    let pairs = checked_mul_resource(OPERATION, count, count - 1)? / 2;
    let result_bytes = checked_mul_resource(
        OPERATION,
        pairs,
        std::mem::size_of::<Pid2ScreenEntry>() as u128,
    )?;
    let mut peak_estimator_bytes = 0_u128;
    let mut estimator_pairs = 0_u128;
    let mut estimator_operations = 0_u128;
    for i in 0..source_count {
        for j in (i + 1)..source_count {
            let estimate = pid2_resource_estimate_for_threads(
                sources[i],
                sources[j],
                target,
                cfg,
                max_threads,
            )?;
            peak_estimator_bytes = peak_estimator_bytes.max(estimate.estimated_bytes);
            estimator_pairs =
                checked_add_resource(OPERATION, estimator_pairs, estimate.pairwise_distances)?;
            estimator_operations =
                checked_add_resource(OPERATION, estimator_operations, estimate.operations_hint)?;
        }
    }
    Ok(ResourceEstimate {
        estimated_bytes: checked_add_resource(OPERATION, result_bytes, peak_estimator_bytes)?,
        pairwise_distances: estimator_pairs,
        operations_hint: checked_add_resource(OPERATION, pairs, estimator_operations)?,
    })
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
    screen_pid2_pairs_with_budget(sources, target, cfg, ResourceBudget::default())
}

/// [`screen_pid2_pairs`] under an explicit pair-enumeration/result budget.
pub fn screen_pid2_pairs_with_budget(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &Pid2Config,
    budget: ResourceBudget,
) -> PidResult<Vec<Pid2ScreenEntry>> {
    let n = target.nrows();
    let n_src = sources.len();
    if n_src < 2 {
        return Err(PidError::InvalidConfig {
            context: "screen_pid2_pairs",
            message: "need at least two sources",
        });
    }
    let pair_count = n_src
        .checked_mul(n_src - 1)
        .and_then(|count| count.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "screen_pid2_pairs",
        })?;
    budget.check(
        "screen_pid2_pairs",
        screen_pid2_pairs_resource_estimate(sources, target, cfg, budget.max_threads)?,
    )?;
    let mut entries =
        try_vec_with_capacity_budget(pair_count, "screen_pid2_pairs results", budget)?;

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
            let result = pid2_isx_with_budget(sources[i], sources[j], target, cfg, budget)?;
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

/// Complete descriptive summary for one scalar statistic from [`bootstrap_rows_stats`].
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct RowBootstrapStat {
    /// Statistic evaluated on the original (un-resampled, un-jittered) data.
    pub point_estimate: f64,
    /// Mean of the complete finite resampling distribution.
    pub resample_mean: f64,
    /// Sample standard deviation of the finite resample distribution. Under
    /// [`RowResampleScheme::Subsample`] this is the spread of the `m`-sample statistic, not a
    /// calibrated standard error for the `n`-row point estimate.
    pub resample_standard_deviation: f64,
    /// Lower finite-resample percentile. Under [`RowResampleScheme::Subsample`] this is a raw
    /// `m`-sample diagnostic quantile, not a calibrated confidence bound for the `n`-row estimate.
    pub percentile_lower: f64,
    /// Upper finite-resample percentile. Under [`RowResampleScheme::Subsample`] this is a raw
    /// `m`-sample diagnostic quantile, not a calibrated confidence bound for the `n`-row estimate.
    pub percentile_upper: f64,
    /// Number of resamples attempted.
    pub n_attempted: usize,
    /// Number of complete finite resamples. Successful results always have
    /// `n_valid == n_attempted`; a failed draw invalidates the whole summary.
    pub n_valid: usize,
}

/// Status of one vector-valued row-resampling replicate.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub enum RowResampleStatus {
    /// Callback completed with exactly the declared number of finite values.
    Complete { statistics: Vec<f64> },
    /// Callback failed, changed width, or returned a non-finite value.
    Failed { error: PidError },
}

/// Indexed row-resampling outcome retained even when another replicate fails.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct RowResampleOutcome {
    pub replicate_index: usize,
    /// Random circular grid origin for no-replacement subsampling. Moving-block bootstrap uses
    /// independently drawn overlapping starts and records `None` here.
    pub circular_block_origin: Option<usize>,
    pub status: RowResampleStatus,
}

/// Row-resampling scheme for [`bootstrap_rows_stats`].
#[derive(Debug, Clone, Copy, PartialEq)]
#[non_exhaustive]
pub enum RowResampleScheme {
    /// Moving-block bootstrap (Künsch 1989) **with replacement** plus optional deterministic
    /// observation noise on the resampled rows: block starts are drawn uniformly
    /// over all `n − block_size + 1` overlapping positions (every row is reachable,
    /// including the `n % block_size` tail), `⌈n/block_size⌉` blocks are concatenated
    /// and truncated to `n` rows.
    ///
    /// With-replacement resampling can create, and typically does create, duplicate rows. Under the
    /// absolute-continuity contract, exact ties are rejected first as
    /// [`PidError::ObservedContinuousSampleIncompatibility`]. Zero-radius numerical failures and
    /// ambiguous positive shells remain separate later geometry checks. Setting `jitter_rel > 0`
    /// adds uniform noise of amplitude
    /// `jitter_rel × column_std` to each resampled element (column std measured on the original
    /// data), thereby changing the resampled distribution. Use nonzero jitter only under an
    /// explicit observation-noise model or as a seeded, reported noise-scale sensitivity analysis;
    /// it is not a generic tie repair. Otherwise use [`RowResampleScheme::Subsample`] for KSG-based
    /// diagnostics or an estimator with the appropriate discrete, quantized, or mixed-support
    /// contract.
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
    /// Random-origin circular block subsampling **without replacement**: each resample first
    /// draws a circular origin uniformly from all rows, then draws
    /// `subsample_len / block_size` distinct blocks from the resulting non-overlapping circular
    /// grid. The rotating omitted arc makes every row reachable across replicates, while distinct
    /// block labels guarantee no repeated row index within a replicate.
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
#[derive(Debug)]
#[non_exhaustive]
pub struct RowBootstrapResult {
    /// Per-statistic summaries in callback order. `None` if any requested replicate failed; the
    /// successful subset is never summarized selectively.
    pub stats: Option<Vec<RowBootstrapStat>>,
    /// Every requested replicate in deterministic order, including structured failure reasons.
    pub replicates: Vec<RowResampleOutcome>,
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
    /// Dependence, block-length, seed, and algorithm provenance.
    pub provenance: BlockResamplingProvenance,
}

/// Estimate row-resampling schedules, retained distributions, and one materialized joint
/// resample, including the caller-declared callback resources.
pub fn bootstrap_rows_stats_resource_estimate(
    mats: &[MatRef<'_>],
    cfg: &BootstrapConfig,
    scheme: RowResampleScheme,
    callback: StatisticCallbackDeclaration,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "bootstrap_rows_stats";
    callback.validate(OPERATION)?;
    if mats.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "mats must not be empty",
        });
    }
    cfg.validity.validate(OPERATION)?;
    let n = mats[0].nrows();
    for matrix in mats {
        if matrix.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: OPERATION,
                left_rows: n,
                right_rows: matrix.nrows(),
            });
        }
    }
    if cfg.n_boot < 2 || cfg.block_size == 0 || cfg.block_size >= n {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "invalid resample count or block size",
        });
    }
    let n_blocks = n / cfg.block_size;
    let (blocks_per_resample, index_capacity, jitter) = match scheme {
        RowResampleScheme::BlockBootstrapJitter { jitter_rel } => {
            if !jitter_rel.is_finite() || jitter_rel < 0.0 {
                return Err(PidError::InvalidConfig {
                    context: OPERATION,
                    message: "jitter_rel must be finite and >= 0",
                });
            }
            (n.div_ceil(cfg.block_size), n, jitter_rel > 0.0)
        }
        RowResampleScheme::Subsample { subsample_len } => {
            let blocks = subsample_len / cfg.block_size;
            if blocks == 0 || blocks >= n_blocks {
                return Err(PidError::InvalidConfig {
                    context: OPERATION,
                    message: "subsample must retain at least one and omit at least one block",
                });
            }
            (
                blocks,
                checked_len(OPERATION, blocks, cfg.block_size)?,
                false,
            )
        }
    };
    let total_columns = mats.iter().try_fold(0_u128, |sum, matrix| {
        checked_add_resource(OPERATION, sum, matrix.ncols() as u128)
    })?;
    let maximum_columns = mats.iter().map(|matrix| matrix.ncols()).max().unwrap_or(0) as u128;
    let usize_bytes = std::mem::size_of::<usize>() as u128;
    let f64_bytes = std::mem::size_of::<f64>() as u128;
    let n_stats = callback.output_values as u128;
    let bytes = [
        checked_mul_resource(OPERATION, blocks_per_resample as u128, usize_bytes)?,
        checked_mul_resource(OPERATION, index_capacity as u128, usize_bytes)?,
        checked_mul_resource(OPERATION, n_blocks as u128, usize_bytes)?,
        checked_mul_resource(OPERATION, n_stats, std::mem::size_of::<Vec<f64>>() as u128)?,
        checked_mul_resource(
            OPERATION,
            checked_mul_resource(
                OPERATION,
                2,
                checked_mul_resource(OPERATION, n_stats, cfg.n_boot as u128)?,
            )?,
            f64_bytes,
        )?,
        checked_mul_resource(
            OPERATION,
            checked_mul_resource(OPERATION, index_capacity as u128, total_columns)?,
            f64_bytes,
        )?,
        checked_mul_resource(
            OPERATION,
            mats.len() as u128,
            (std::mem::size_of::<MatOwned>() + std::mem::size_of::<MatRef<'_>>()) as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            n_stats,
            std::mem::size_of::<RowBootstrapStat>() as u128,
        )?,
        checked_mul_resource(
            OPERATION,
            cfg.n_boot as u128,
            std::mem::size_of::<RowResampleOutcome>() as u128,
        )?,
        callback.per_call.estimated_bytes,
        if jitter {
            checked_mul_resource(OPERATION, total_columns, f64_bytes)?
        } else {
            0
        },
        if jitter {
            checked_mul_resource(OPERATION, n as u128, maximum_columns.max(1) * f64_bytes)?
        } else {
            0
        },
    ]
    .into_iter()
    .try_fold(0_u128, |sum, value| {
        checked_add_resource(OPERATION, sum, value)
    })?;
    let copy_work = checked_mul_resource(
        OPERATION,
        cfg.n_boot as u128,
        checked_mul_resource(OPERATION, index_capacity as u128, total_columns)?,
    )?;
    let draw_work =
        checked_mul_resource(OPERATION, cfg.n_boot as u128, blocks_per_resample as u128)?;
    let callback_calls = checked_add_resource(OPERATION, cfg.n_boot as u128, 1)?;
    Ok(ResourceEstimate {
        estimated_bytes: bytes,
        pairwise_distances: checked_mul_resource(
            OPERATION,
            callback_calls,
            callback.per_call.pairwise_distances,
        )?,
        operations_hint: checked_add_resource(
            OPERATION,
            checked_add_resource(OPERATION, copy_work, draw_work)?,
            checked_mul_resource(OPERATION, callback_calls, callback.per_call.operations_hint)?,
        )?,
    })
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
/// entry) is retained in [`RowBootstrapResult::replicates`] and makes `stats` unavailable.
/// Selectively deleting failed draws would condition the distribution on estimator success.
///
/// # Errors
///
/// Returns an error if the matrices are empty or misaligned, if the configuration is invalid, if
/// the requested schedules/distributions cannot be reserved safely, or if the statistic fails
/// **on the original data** (a failed point
/// estimate makes the resampling distribution meaningless), including when any original
/// point-estimate entry is non-finite. Cancellation is propagated immediately. Individual
/// resample/materialization/callback failures are retained in the returned report; only a complete
/// requested set is summarized.
pub fn bootstrap_rows_stats<F>(
    mats: &[MatRef<'_>],
    cfg: &BootstrapConfig,
    scheme: RowResampleScheme,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowBootstrapResult>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<Vec<f64>>,
{
    bootstrap_rows_stats_with_budget(mats, cfg, scheme, ResourceBudget::default(), callback, stat)
}

/// [`bootstrap_rows_stats`] under an explicit schedule/distribution/resample budget.
pub fn bootstrap_rows_stats_with_budget<F>(
    mats: &[MatRef<'_>],
    cfg: &BootstrapConfig,
    scheme: RowResampleScheme,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowBootstrapResult>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<Vec<f64>>,
{
    let cancellation = CancellationToken::new();
    bootstrap_rows_stats_with_cancellation(mats, cfg, scheme, budget, callback, &cancellation, stat)
}

/// [`bootstrap_rows_stats_with_budget`] with cooperative cancellation between replicates.
pub fn bootstrap_rows_stats_with_cancellation<F>(
    mats: &[MatRef<'_>],
    cfg: &BootstrapConfig,
    scheme: RowResampleScheme,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    cancellation: &CancellationToken,
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
    cfg.validity.validate("bootstrap_rows_stats")?;
    callback.validate("bootstrap_rows_stats")?;
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
                    message: "subsample_len must omit at least one complete circular-grid block",
                });
            }
            (blocks, false, 0.0)
        }
    };
    budget.check(
        "bootstrap_rows_stats",
        bootstrap_rows_stats_resource_estimate(mats, cfg, scheme, callback)?,
    )?;
    cancellation.check("bootstrap_rows_stats", 0, cfg.n_boot + 1)?;

    // Preflight every resample-distribution and index schedule capacity before invoking `stat`.
    // In particular, a zero-column `MatRef` can legally carry an enormous logical row count, so
    // row-index amplification must be checked independently of matrix storage size.
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
    let mut starts =
        try_vec_with_capacity_budget::<usize>(blocks_per_resample, "bootstrap_rows_stats", budget)?;
    let mut indices =
        try_vec_with_capacity_budget::<usize>(index_capacity, "bootstrap_rows_stats", budget)?;
    let mut pool = if with_replacement {
        Vec::new()
    } else {
        try_vec_with_capacity_budget::<usize>(n_blocks, "bootstrap_rows_stats", budget)?
    };

    let point = stat(mats)?;
    if point.len() != callback.output_values {
        return Err(PidError::InvalidConfig {
            context: "bootstrap_rows_stats",
            message: "stat output width does not match its callback declaration",
        });
    }
    if point.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "bootstrap_rows_stats point estimate",
        });
    }
    let n_stats = callback.output_values;

    // Jitter alone needs a scale. Avoid both unnecessary work and manufactured overflow on the
    // no-repeated-index/no-jitter paths. Scale-normalized moments keep a constant column at
    // f64::MAX at its mathematically correct zero standard deviation instead of overflowing a
    // naive sum.
    let col_stds = if jitter_rel > 0.0 {
        let mut values =
            try_vec_with_capacity_budget(mats.len(), "bootstrap_rows_stats column scales", budget)?;
        for matrix in mats {
            values.push(checked_column_stds(*matrix, budget)?);
        }
        values
    } else {
        Vec::new()
    };

    let mut rng = SplitMix64::new(cfg.seed);
    let mut replicates = try_vec_with_capacity_budget::<RowResampleOutcome>(
        cfg.n_boot,
        "bootstrap_rows_stats outcomes",
        budget,
    )?;

    for replicate_index in 0..cfg.n_boot {
        cancellation.check("bootstrap_rows_stats", replicate_index + 1, cfg.n_boot + 1)?;
        // Draw block starts per scheme.
        starts.clear();
        let mut circular_block_origin = None;
        if with_replacement {
            // True moving-block bootstrap (Künsch 1989): starts uniform over ALL
            // n − block_size + 1 overlapping positions, so every row (including the
            // n % block_size tail) is reachable.
            let n_starts = n - cfg.block_size + 1;
            for _ in 0..blocks_per_resample {
                starts.push(uniform_index(&mut rng, n_starts));
            }
        } else {
            // Randomize the circular grid origin before partial Fisher–Yates. The complete grid
            // spans `floor(n / block_size) * block_size` unique rows and leaves a rotating gap;
            // distinct selected block labels therefore cannot duplicate a row.
            let origin = uniform_index(&mut rng, n);
            circular_block_origin = Some(origin);
            pool.clear();
            pool.extend(0..n_blocks);
            for k in 0..blocks_per_resample {
                let j = k + uniform_index(&mut rng, n_blocks - k);
                pool.swap(k, j);
                starts.push(pool[k]);
            }
            // Preserve circular temporal order relative to the randomized origin.
            starts.sort_unstable();
            for block in &mut starts {
                *block = (origin + *block * cfg.block_size) % n;
            }
        }

        indices.clear();
        'blocks: for &block_start in &starts {
            for j in 0..cfg.block_size {
                let row = if with_replacement {
                    block_start + j
                } else {
                    (block_start + j) % n
                };
                indices.push(row);
                if with_replacement && indices.len() == n {
                    // MBB concatenation truncates to exactly n rows.
                    break 'blocks;
                }
            }
        }

        let evaluation = (|| -> PidResult<Vec<f64>> {
            let mut owned = try_vec_with_capacity_budget::<MatOwned>(
                mats.len(),
                "bootstrap_rows_stats",
                budget,
            )?;
            for (m_idx, m) in mats.iter().enumerate() {
                let d = m.ncols();
                let data_len = indices
                    .len()
                    .checked_mul(d)
                    .ok_or(PidError::InvalidConfig {
                        context: "bootstrap_rows_stats",
                        message: "resampled matrix length overflow",
                    })?;
                let mut data =
                    try_vec_with_capacity_budget(data_len, "bootstrap_rows_stats", budget)?;
                for &i in &indices {
                    data.extend_from_slice(m.row(i));
                }
                if jitter_rel > 0.0 {
                    for (flat_idx, value) in data.iter_mut().enumerate() {
                        let col = flat_idx % d;
                        let scale = jitter_rel * col_stds[m_idx][col];
                        if !scale.is_finite() {
                            return Err(PidError::NumericalInstability {
                                context: "bootstrap_rows_stats jitter scale",
                            });
                        }
                        if scale > 0.0 {
                            let uniform = (rng.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
                            *value += scale * (2.0 * uniform - 1.0);
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
            let mut refs = try_vec_with_capacity_budget::<MatRef<'_>>(
                owned.len(),
                "bootstrap_rows_stats",
                budget,
            )?;
            refs.extend(owned.iter().map(|matrix| matrix.as_ref()));
            stat(&refs)
        })();
        let status = match evaluation {
            Err(error @ PidError::Cancelled { .. }) => return Err(error),
            Err(error) => RowResampleStatus::Failed { error },
            Ok(statistics) if statistics.len() != n_stats => RowResampleStatus::Failed {
                error: PidError::InvalidConfig {
                    context: "bootstrap_rows_stats",
                    message: "stat output width changed across resamples",
                },
            },
            Ok(statistics) if statistics.iter().any(|value| !value.is_finite()) => {
                RowResampleStatus::Failed {
                    error: PidError::NumericalInstability {
                        context: "bootstrap_rows_stats resample",
                    },
                }
            }
            Ok(statistics) => RowResampleStatus::Complete { statistics },
        };
        replicates.push(RowResampleOutcome {
            replicate_index,
            circular_block_origin,
            status,
        });
    }

    let all_complete = replicates
        .iter()
        .all(|replicate| matches!(replicate.status, RowResampleStatus::Complete { .. }));
    let stats = if all_complete {
        let mut distributions =
            try_vec_with_capacity_budget::<Vec<f64>>(n_stats, "bootstrap_rows_stats", budget)?;
        for _ in 0..n_stats {
            distributions.push(try_vec_with_capacity_budget(
                cfg.n_boot,
                "bootstrap_rows_stats",
                budget,
            )?);
        }
        for replicate in &replicates {
            let RowResampleStatus::Complete { statistics } = &replicate.status else {
                return Err(PidError::NumericalInstability {
                    context: "bootstrap_rows_stats outcome coherence",
                });
            };
            for (statistic_index, &value) in statistics.iter().enumerate() {
                distributions[statistic_index].push(value);
            }
        }
        let mut summaries =
            try_vec_with_capacity_budget(n_stats, "bootstrap_rows_stats summaries", budget)?;
        for (statistic_index, &point_estimate) in point.iter().enumerate() {
            let values = &mut distributions[statistic_index];
            values.sort_by(f64::total_cmp);
            let (resample_mean, resample_standard_deviation) =
                finite_mean_std_sample(values, "bootstrap_rows_stats summary")?;
            let lo_idx = ((cfg.alpha / 2.0) * values.len() as f64).floor() as usize;
            let hi_idx = (((1.0 - cfg.alpha / 2.0) * values.len() as f64).ceil() as usize)
                .saturating_sub(1)
                .min(values.len() - 1);
            summaries.push(RowBootstrapStat {
                point_estimate,
                resample_mean,
                resample_standard_deviation,
                percentile_lower: values[lo_idx],
                percentile_upper: values[hi_idx],
                n_attempted: cfg.n_boot,
                n_valid: values.len(),
            });
        }
        Some(summaries)
    } else {
        None
    };

    Ok(RowBootstrapResult {
        stats,
        replicates,
        n_boot: cfg.n_boot,
        block_size: cfg.block_size,
        effective_resample_len: index_capacity,
        scheme,
        provenance: BlockResamplingProvenance {
            validity: cfg.validity,
            block_size: cfg.block_size,
            seed: cfg.seed,
            requested_replicates: cfg.n_boot,
            algorithm_revision: BlockResamplingAlgorithmRevision::V1,
        },
    })
}

fn checked_column_stds(matrix: MatRef<'_>, budget: ResourceBudget) -> PidResult<Vec<f64>> {
    debug_assert!(matrix.nrows() > 0);
    let mut deviations =
        try_vec_with_capacity_budget(matrix.ncols(), "bootstrap_rows_stats column scales", budget)?;
    for column in 0..matrix.ncols() {
        let mut values = try_vec_with_capacity_budget(
            matrix.nrows(),
            "bootstrap_rows_stats column values",
            budget,
        )?;
        values.extend((0..matrix.nrows()).map(|row| matrix.row(row)[column]));
        let (_, std) =
            finite_mean_std_population(&values, "bootstrap_rows_stats jitter standard deviation")?;
        deviations.push(std);
    }
    Ok(deviations)
}

/// Raw moving-block resampling-percentile summaries for averaged 2-source discrete SxPID atoms.
#[derive(Debug, Clone, PartialEq)]
pub struct QuantizedSxPid2BootstrapResult {
    pub redundancy: RowBootstrapStat,
    pub unique_s1: RowBootstrapStat,
    pub unique_s2: RowBootstrapStat,
    pub synergy: RowBootstrapStat,
    pub n_boot: usize,
    pub block_size: usize,
}

fn quantized_sxpid2_callback_declaration(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
) -> PidResult<StatisticCallbackDeclaration> {
    const OPERATION: &str = "bootstrap_quantized_sxpid2 callback";
    let n = s1.nrows() as u128;
    let columns = [s1.ncols(), s2.ncols(), target.ncols()]
        .into_iter()
        .try_fold(0_u128, |sum, value| {
            checked_add_resource(OPERATION, sum, value as u128)
        })?;
    // The legacy same-sample quantizer/SxPID callback uses several sorted state/count tables.
    // Charge a deliberately conservative quadratic state envelope until that experimental
    // convenience path is replaced by fitted categorical inputs with an exact estimator report.
    let state_slots = checked_mul_resource(OPERATION, n, n.max(columns).max(1))?;
    let per_call = ResourceEstimate {
        estimated_bytes: checked_mul_resource(OPERATION, state_slots, 256)?,
        pairwise_distances: 0,
        operations_hint: checked_mul_resource(OPERATION, state_slots, 32)?,
    };
    StatisticCallbackDeclaration::vector(4, per_call)
}

/// Dependence-aware raw resampling-percentile summaries for the averaged discrete SxPID atoms
/// ([`quantized_sxpid2`]).
///
/// Resampling uses a moving-block bootstrap **with replacement and no jitter**
/// ([`RowResampleScheme::BlockBootstrapJitter`] with `jitter_rel = 0`): unlike the kNN/KSG
/// estimators, the discrete (counting-based) SxPID is unaffected by duplicate rows, and jitter
/// would corrupt the discrete labels. Set `cfg.block_size = 1` for i.i.d. data, or a larger block
/// for autocorrelated (e.g. time-series) data. The output is the central
/// `(1 − cfg.alpha)` empirical percentile range of each atom over the resamples; generic coverage
/// is not claimed.
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
    bootstrap_quantized_sxpid2_with_budget(s1, s2, t, num_bins, cfg, ResourceBudget::default())
}

/// Resource estimate for [`bootstrap_quantized_sxpid2_with_budget`], excluding the opaque
/// categorical estimator's own bounded allocations.
pub fn bootstrap_quantized_sxpid2_resource_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &BootstrapConfig,
) -> PidResult<ResourceEstimate> {
    bootstrap_rows_stats_resource_estimate(
        &[s1, s2, t],
        cfg,
        RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
        quantized_sxpid2_callback_declaration(s1, s2, t)?,
    )
}

/// [`bootstrap_quantized_sxpid2`] under an explicit row-resampling budget.
pub fn bootstrap_quantized_sxpid2_with_budget(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    num_bins: usize,
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
) -> PidResult<QuantizedSxPid2BootstrapResult> {
    let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
        let r = quantized_sxpid2(mats[0], mats[1], mats[2], num_bins)?;
        Ok(vec![r.red.net, r.unq1.net, r.unq2.net, r.syn.net])
    };
    let res = bootstrap_rows_stats_with_budget(
        &[s1, s2, t],
        cfg,
        RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
        budget,
        quantized_sxpid2_callback_declaration(s1, s2, t)?,
        stat,
    )?;
    let stats = res.stats.ok_or(PidError::NumericalInstability {
        context: "bootstrap_quantized_sxpid2: at least one replicate failed",
    })?;
    let mut it = stats.into_iter();
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
#[derive(Debug, Clone)]
#[non_exhaustive]
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
    /// score, not an exact randomization-test p-value. `None` means at least one requested
    /// transform failed; every reason is retained in [`Self::replicates`].
    pub tail_fraction: Option<f64>,
    /// Number of permutations attempted.
    pub n_attempted: usize,
    /// Number of complete, finite transforms. A tail fraction exists only when this equals
    /// `n_attempted`.
    pub n_valid: usize,
    /// Index (into `mats`) of the matrix whose rows were shuffled.
    pub shuffled_index: usize,
    /// Every requested transform in deterministic order, including failures.
    pub replicates: Vec<PermutationReplicateOutcome>,
    /// Typed null assumptions, calibration, family, seed, and revision provenance.
    pub null: PermutationNull,
}

/// Estimate one materialized permutation plus repeated schedule/copy work and the caller-declared
/// statistic callback resources.
pub fn permutation_rows_pvalue_resource_estimate(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    callback: StatisticCallbackDeclaration,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "permutation_rows_pvalue";
    callback.validate(OPERATION)?;
    if callback.output_values != 1 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "row permutation callback must declare one output value",
        });
    }
    if mats.is_empty() || shuffled_index >= mats.len() || n_perm == 0 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "mats, shuffled_index, and n_perm must be valid",
        });
    }
    let n = mats[0].nrows();
    for matrix in mats {
        if matrix.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: OPERATION,
                left_rows: n,
                right_rows: matrix.nrows(),
            });
        }
    }
    let dimension = mats[shuffled_index].ncols() as u128;
    let n = n as u128;
    let permutation_bytes = checked_mul_resource(
        OPERATION,
        checked_mul_resource(OPERATION, 2, n)?,
        std::mem::size_of::<usize>() as u128,
    )?;
    let matrix_bytes = checked_mul_resource(
        OPERATION,
        checked_mul_resource(OPERATION, n, dimension)?,
        std::mem::size_of::<f64>() as u128,
    )?;
    let refs_bytes = checked_mul_resource(
        OPERATION,
        mats.len() as u128,
        std::mem::size_of::<MatRef<'_>>() as u128,
    )?;
    let outcome_bytes = checked_mul_resource(
        OPERATION,
        n_perm as u128,
        std::mem::size_of::<PermutationReplicateOutcome>() as u128,
    )?;
    let outcome_payload_bytes = checked_mul_resource(
        OPERATION,
        n_perm as u128,
        std::mem::size_of::<f64>() as u128,
    )?;
    let per_permutation_work =
        checked_add_resource(OPERATION, n, checked_mul_resource(OPERATION, n, dimension)?)?;
    let callback_calls = checked_add_resource(OPERATION, n_perm as u128, 1)?;
    Ok(ResourceEstimate {
        estimated_bytes: checked_add_resource(
            OPERATION,
            checked_add_resource(
                OPERATION,
                checked_add_resource(OPERATION, permutation_bytes, matrix_bytes)?,
                refs_bytes,
            )?,
            checked_add_resource(
                OPERATION,
                checked_add_resource(OPERATION, outcome_bytes, outcome_payload_bytes)?,
                callback.per_call.estimated_bytes,
            )?,
        )?,
        pairwise_distances: checked_mul_resource(
            OPERATION,
            callback_calls,
            callback.per_call.pairwise_distances,
        )?,
        operations_hint: checked_add_resource(
            OPERATION,
            checked_mul_resource(OPERATION, n_perm as u128, per_permutation_work)?,
            checked_mul_resource(OPERATION, callback_calls, callback.per_call.operations_hint)?,
        )?,
    })
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
/// A permutation preserves every individual matrix's row multiset, so the continuous-sample
/// preflight outcome is unchanged. Re-pairing can nevertheless create ambiguous positive-distance
/// shells in the joint kNN space. No implicit jitter is added: every requested transform must
/// evaluate under the caller's declared preprocessing policy. If the null requires refitting an
/// adaptive transform, that fit must occur inside `stat` for every transform; passing already
/// transformed matrices instead defines a conditional null with the transform held fixed.
///
/// Uses [`PermutationScheme::FullShuffle`] (exchangeable/i.i.d. rows). Use
/// [`permutation_rows_pvalue_with`] with [`PermutationScheme::BlockShuffle`] when
/// fixed, equal-sized whole blocks are exchangeable, or
/// [`PermutationScheme::CircularShift`] for a stationary-series surrogate.
///
/// # Errors
///
/// Returns an error on misaligned/empty inputs, an out-of-range `shuffled_index`,
/// `n_perm == 0`, an unallocatable retained schedule/report, or if the statistic fails or is
/// non-finite on the original data. Per-transform failures are retained and withhold the score.
pub fn permutation_rows_pvalue<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with_budget(
        mats,
        shuffled_index,
        n_perm,
        seed,
        ResourceBudget::default(),
        callback,
        stat,
    )
}

/// [`permutation_rows_pvalue`] under an explicit schedule/materialization budget.
pub fn permutation_rows_pvalue_with_budget<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with_tail_and_budget(
        mats,
        shuffled_index,
        n_perm,
        seed,
        PermutationScheme::FullShuffle,
        PermutationTail::Upper,
        budget,
        callback,
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
/// Every transform must evaluate successfully and finitely for a tail fraction to be available;
/// otherwise failures are retained without selecting a successful subset.
///
/// # Errors
///
/// Returns an error on invalid inputs or scheme configuration, an unallocatable row schedule or
/// shuffled report, or if `stat` fails or returns a non-finite value on the observed data.
pub fn permutation_rows_pvalue_with<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with_tail_and_budget(
        mats,
        shuffled_index,
        n_perm,
        seed,
        scheme,
        PermutationTail::Upper,
        ResourceBudget::default(),
        callback,
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
/// Every transform must evaluate successfully and finitely for a tail fraction to be available;
/// otherwise failures are retained without selecting a successful subset.
///
/// # Errors
///
/// Returns an error on invalid inputs or scheme configuration, an unallocatable row schedule or
/// shuffled report, or if `stat` fails or returns a non-finite value on the observed data.
#[expect(
    clippy::too_many_arguments,
    reason = "the compatibility wrapper keeps every component of the null procedure explicit"
)]
pub fn permutation_rows_pvalue_with_tail<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    tail: PermutationTail,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    permutation_rows_pvalue_with_tail_and_budget(
        mats,
        shuffled_index,
        n_perm,
        seed,
        scheme,
        tail,
        ResourceBudget::default(),
        callback,
        stat,
    )
}

/// [`permutation_rows_pvalue_with_tail`] under an explicit schedule/materialization budget.
#[expect(
    clippy::too_many_arguments,
    reason = "the explicit null, seed, tail, budget, and statistic define the procedure"
)]
pub fn permutation_rows_pvalue_with_tail_and_budget<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    seed: u64,
    scheme: PermutationScheme,
    tail: PermutationTail,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    let null = PermutationNull::new(scheme, tail, seed, PermutationFamily::standalone(1))?;
    permutation_rows_pvalue_under_null_with_budget(
        mats,
        shuffled_index,
        n_perm,
        null,
        budget,
        callback,
        stat,
    )
}

/// Scalar row permutation/surrogate report under a fully typed null specification.
pub fn permutation_rows_pvalue_under_null_with_budget<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    null: PermutationNull,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    stat: F,
) -> PidResult<RowPermutationStat>
where
    F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
{
    let cancellation = CancellationToken::new();
    permutation_rows_pvalue_under_null_with_cancellation(
        mats,
        shuffled_index,
        n_perm,
        null,
        budget,
        callback,
        &cancellation,
        stat,
    )
}

/// [`permutation_rows_pvalue_under_null_with_budget`] with cooperative cancellation checks.
#[expect(
    clippy::too_many_arguments,
    reason = "the aligned matrices, typed null, callback contract, budget, and token define the procedure"
)]
pub fn permutation_rows_pvalue_under_null_with_cancellation<F>(
    mats: &[MatRef<'_>],
    shuffled_index: usize,
    n_perm: usize,
    null: PermutationNull,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    cancellation: &CancellationToken,
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
    null.family.validate("permutation_rows_pvalue")?;
    validate_permutation_scheme("permutation_rows_pvalue", null.scheme, n)?;
    budget.check(
        "permutation_rows_pvalue",
        permutation_rows_pvalue_resource_estimate(mats, shuffled_index, n_perm, callback)?,
    )?;
    cancellation.check("permutation_rows_pvalue", 0, n_perm + 1)?;

    let observed = stat(mats)?;
    if !observed.is_finite() {
        return Err(PidError::InvalidConfig {
            context: "permutation_rows_pvalue",
            message: "observed statistic must be finite",
        });
    }

    let mut rng = SplitMix64::new(null.seed);
    let shuffled_dim = mats[shuffled_index].ncols();
    let mut replicates = try_vec_with_capacity_budget::<PermutationReplicateOutcome>(
        n_perm,
        "permutation_rows_pvalue outcomes",
        budget,
    )?;

    for replicate_index in 0..n_perm {
        cancellation.check("permutation_rows_pvalue", replicate_index + 1, n_perm + 1)?;
        let evaluation = (|| -> PidResult<f64> {
            let perm =
                draw_permutation(null.scheme, n, &mut rng, "permutation_rows_pvalue", budget)?;
            let data_len = n.checked_mul(shuffled_dim).ok_or(PidError::InvalidConfig {
                context: "permutation_rows_pvalue",
                message: "shuffled matrix length overflow",
            })?;
            let mut data =
                try_vec_with_capacity_budget(data_len, "permutation_rows_pvalue", budget)?;
            for &i in &perm {
                data.extend_from_slice(mats[shuffled_index].row(i));
            }
            let shuffled =
                MatOwned::new(data, n, shuffled_dim).map_err(|_| PidError::InvalidConfig {
                    context: "permutation_rows_pvalue",
                    message: "shuffled data must be finite",
                })?;
            let mut refs = try_vec_with_capacity_budget::<MatRef<'_>>(
                mats.len(),
                "permutation_rows_pvalue",
                budget,
            )?;
            refs.extend_from_slice(mats);
            refs[shuffled_index] = shuffled.as_ref();
            let value = stat(&refs)?;
            if !value.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "permutation_rows_pvalue permutation statistic",
                });
            }
            Ok(value)
        })();
        let status = match evaluation {
            Err(error @ PidError::Cancelled { .. }) => return Err(error),
            Err(error) => PermutationReplicateStatus::Failed { error },
            Ok(value) => {
                let mut statistics =
                    try_vec_with_capacity_budget(1, "permutation_rows_pvalue outcome", budget)?;
                statistics.push(value);
                PermutationReplicateStatus::Complete { statistics }
            }
        };
        replicates.push(PermutationReplicateOutcome {
            replicate_index,
            status,
        });
    }

    let n_valid = replicates
        .iter()
        .filter(|replicate| {
            matches!(
                replicate.status,
                PermutationReplicateStatus::Complete { .. }
            )
        })
        .count();
    let tail_fraction = if n_valid == n_perm {
        let mut n_extreme = 0usize;
        for replicate in &replicates {
            let PermutationReplicateStatus::Complete { statistics } = &replicate.status else {
                return Err(PidError::NumericalInstability {
                    context: "permutation_rows_pvalue outcome coherence",
                });
            };
            if null.tail.contains(statistics[0], observed) {
                n_extreme += 1;
            }
        }
        Some((1.0 + n_extreme as f64) / (1.0 + n_perm as f64))
    } else {
        None
    };

    Ok(RowPermutationStat {
        observed,
        tail_fraction,
        n_attempted: n_perm,
        n_valid,
        shuffled_index,
        replicates,
        null,
    })
}

// ── Multiple-testing correction ────────────────────────────────────────────────

/// Step-up false-discovery-rate adjustment method.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum MultipleTestingMethod {
    BenjaminiHochberg,
    BenjaminiYekutieli,
}

/// Adjusted p-values with the exact predeclared family definition retained.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct MultipleTestingAdjustment {
    pub family: PermutationFamily,
    pub method: MultipleTestingMethod,
    pub adjusted_p_values: Vec<f64>,
}

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
/// The family must be fully declared and finite. A missing/failed hypothesis is a typed upstream
/// failure, not a `NaN` p-value; decide its conservative family treatment before calling this
/// numeric adjustment.
///
/// # Errors
///
/// Returns an error if the input is empty or any entry is non-finite or outside `[0, 1]`.
pub fn benjamini_hochberg(
    p_values: &[f64],
    family: PermutationFamily,
) -> PidResult<MultipleTestingAdjustment> {
    validate_adjustment_family(p_values, family, "benjamini_hochberg")?;
    Ok(MultipleTestingAdjustment {
        family,
        method: MultipleTestingMethod::BenjaminiHochberg,
        adjusted_p_values: adjust_step_up(p_values, 1.0, "benjamini_hochberg")?,
    })
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
/// Missing/failed hypotheses must be resolved through a typed upstream family policy as in
/// [`benjamini_hochberg`]. Restricted circular-shift surrogate scores are not p-values and must
/// not be passed to either adjustment.
///
/// # Errors
///
/// Returns an error if the input is empty or any entry is non-finite or outside `[0, 1]`.
pub fn benjamini_yekutieli(
    p_values: &[f64],
    family: PermutationFamily,
) -> PidResult<MultipleTestingAdjustment> {
    validate_adjustment_family(p_values, family, "benjamini_yekutieli")?;
    if p_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "benjamini_yekutieli",
            message: "p_values must not be empty",
        });
    }
    let harmonic = (1..=p_values.len())
        .map(|rank| 1.0 / rank as f64)
        .sum::<f64>();
    Ok(MultipleTestingAdjustment {
        family,
        method: MultipleTestingMethod::BenjaminiYekutieli,
        adjusted_p_values: adjust_step_up(p_values, harmonic, "benjamini_yekutieli")?,
    })
}

fn validate_adjustment_family(
    p_values: &[f64],
    family: PermutationFamily,
    context: &'static str,
) -> PidResult<()> {
    family.validate(context)?;
    if family.size != p_values.len() {
        return Err(PidError::ShapeMismatch {
            context,
            expected_len: family.size,
            actual_len: p_values.len(),
        });
    }
    Ok(())
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
    let mut finite = try_vec_with_capacity::<(usize, f64)>(p_values.len(), context)?;
    for (i, &p) in p_values.iter().enumerate() {
        if !p.is_finite() || !(0.0..=1.0).contains(&p) {
            return Err(PidError::InvalidConfig {
                context,
                message: "every p-value must be finite and lie in [0, 1]",
            });
        }
        finite.push((i, p));
    }
    let mut adjusted =
        crate::resource::try_vec_filled(context, p_values.len(), 1.0, ResourceBudget::default())?;
    let finite_count = finite.len();
    let m = p_values.len();
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
    use std::sync::atomic::{AtomicUsize, Ordering};

    fn tiny_budget() -> ResourceBudget {
        ResourceBudget {
            max_bytes: 1,
            max_pairwise_distances: 1,
            max_operations_hint: 10_000,
            max_threads: 1,
        }
    }

    fn independent_validity() -> crate::bootstrap::ResamplingValidityDeclaration {
        crate::bootstrap::ResamplingValidityDeclaration::independent_rows(
            crate::bootstrap::BlockLengthSelection::FixedAPriori,
        )
    }

    fn scalar_callback() -> StatisticCallbackDeclaration {
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO)
    }

    fn complete_q2(result: &PlsCvResult, candidate_index: usize) -> f64 {
        match result.candidates[candidate_index].status {
            PlsCvCandidateStatus::Complete { q2 } => q2,
            _ => panic!("expected complete CV candidate"),
        }
    }

    fn complete_row_values(result: &RowBootstrapResult) -> Vec<(Option<usize>, Vec<u64>)> {
        result
            .replicates
            .iter()
            .map(|replicate| {
                let RowResampleStatus::Complete { statistics } = &replicate.status else {
                    panic!("expected complete row-resampling outcome");
                };
                (
                    replicate.circular_block_origin,
                    statistics.iter().map(|value| value.to_bits()).collect(),
                )
            })
            .collect()
    }

    fn complete_permutation_values(result: &RowPermutationStat) -> Vec<Vec<u64>> {
        result
            .replicates
            .iter()
            .map(|replicate| {
                let PermutationReplicateStatus::Complete { statistics } = &replicate.status else {
                    panic!("expected complete permutation outcome");
                };
                statistics.iter().map(|value| value.to_bits()).collect()
            })
            .collect()
    }

    fn bootstrap_rows_stats<F>(
        mats: &[MatRef<'_>],
        config: &BootstrapConfig,
        scheme: RowResampleScheme,
        statistic: F,
    ) -> PidResult<RowBootstrapResult>
    where
        F: Fn(&[MatRef<'_>]) -> PidResult<Vec<f64>>,
    {
        super::bootstrap_rows_stats(mats, config, scheme, scalar_callback(), statistic)
    }

    fn bootstrap_rows_stats_with_budget<F>(
        mats: &[MatRef<'_>],
        config: &BootstrapConfig,
        scheme: RowResampleScheme,
        budget: ResourceBudget,
        statistic: F,
    ) -> PidResult<RowBootstrapResult>
    where
        F: Fn(&[MatRef<'_>]) -> PidResult<Vec<f64>>,
    {
        super::bootstrap_rows_stats_with_budget(
            mats,
            config,
            scheme,
            budget,
            scalar_callback(),
            statistic,
        )
    }

    fn permutation_rows_pvalue<F>(
        mats: &[MatRef<'_>],
        shuffled_index: usize,
        n_perm: usize,
        seed: u64,
        statistic: F,
    ) -> PidResult<RowPermutationStat>
    where
        F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
    {
        super::permutation_rows_pvalue(
            mats,
            shuffled_index,
            n_perm,
            seed,
            scalar_callback(),
            statistic,
        )
    }

    fn permutation_rows_pvalue_with_budget<F>(
        mats: &[MatRef<'_>],
        shuffled_index: usize,
        n_perm: usize,
        seed: u64,
        budget: ResourceBudget,
        statistic: F,
    ) -> PidResult<RowPermutationStat>
    where
        F: Fn(&[MatRef<'_>]) -> PidResult<f64>,
    {
        super::permutation_rows_pvalue_with_budget(
            mats,
            shuffled_index,
            n_perm,
            seed,
            budget,
            scalar_callback(),
            statistic,
        )
    }

    #[test]
    fn row_resampling_budget_rejection_precedes_statistic_execution() {
        let matrix = MatRef::new(&[0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let calls = AtomicUsize::new(0);

        let result = bootstrap_rows_stats_with_budget(
            &[matrix],
            &config,
            RowResampleScheme::Subsample { subsample_len: 2 },
            tiny_budget(),
            |_| {
                calls.fetch_add(1, Ordering::Relaxed);
                Ok(vec![0.0])
            },
        );

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded { .. })
        ));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn permutation_budget_rejection_precedes_statistic_execution() {
        let matrix = MatRef::new(&[0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let calls = AtomicUsize::new(0);

        let result = permutation_rows_pvalue_with_budget(&[matrix], 0, 2, 0, tiny_budget(), |_| {
            calls.fetch_add(1, Ordering::Relaxed);
            Ok(0.0)
        });

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded { .. })
        ));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn row_resampling_honors_a_pre_cancelled_token() {
        let matrix = MatRef::new(&[0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let cancellation = CancellationToken::new();
        cancellation.cancel();
        let calls = AtomicUsize::new(0);

        let result = super::bootstrap_rows_stats_with_cancellation(
            &[matrix],
            &config,
            RowResampleScheme::Subsample { subsample_len: 2 },
            ResourceBudget::default(),
            scalar_callback(),
            &cancellation,
            |_| {
                calls.fetch_add(1, Ordering::Relaxed);
                Ok(vec![0.0])
            },
        );

        assert!(matches!(result, Err(PidError::Cancelled { .. })));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn row_permutation_honors_a_pre_cancelled_token() {
        let matrix = MatRef::new(&[0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let cancellation = CancellationToken::new();
        cancellation.cancel();
        let calls = AtomicUsize::new(0);
        let null = PermutationNull::new(
            PermutationScheme::FullShuffle,
            PermutationTail::Upper,
            0,
            PermutationFamily::standalone(1),
        )
        .unwrap();

        let result = super::permutation_rows_pvalue_under_null_with_cancellation(
            &[matrix],
            0,
            2,
            null,
            ResourceBudget::default(),
            scalar_callback(),
            &cancellation,
            |_| {
                calls.fetch_add(1, Ordering::Relaxed);
                Ok(0.0)
            },
        );

        assert!(matches!(result, Err(PidError::Cancelled { .. })));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn pls_cv_rejects_tiny_budget_before_fold_allocation() {
        let x = MatRef::new(&[0.0, 1.0, 1.0, 2.0, 2.0, 3.0], 3, 2).unwrap();
        let y = MatRef::new(&[0.0, 1.0, 2.0], 3, 1).unwrap();

        let result = pls_cv_select_components_with_budget(x, y, 1, tiny_budget());

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded { .. })
        ));
    }

    #[test]
    fn pls_cv_honors_a_pre_cancelled_token() {
        let x = MatRef::new(&[0.0, 1.0, 1.0, 2.0, 2.0, 3.0], 3, 2).unwrap();
        let y = MatRef::new(&[0.0, 1.0, 2.0], 3, 1).unwrap();
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = pls_cv_select_components_with_cancellation(
            x,
            y,
            1,
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(result, Err(PidError::Cancelled { .. })));
    }

    #[test]
    fn pls_cv_retains_every_failed_fold_without_negative_infinity_sentinels() {
        let x = MatRef::new(&[1.0, 1.0, 1.0, 1.0], 4, 1).unwrap();
        let y = MatRef::new(&[0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();

        let report = pls_cv_select_components(x, y, 1).unwrap();

        assert_eq!(report.best_components, None);
        assert_eq!(report.candidates.len(), 1);
        assert!(matches!(
            report.candidates[0].status,
            PlsCvCandidateStatus::Incomplete { failed_folds: 4 }
        ));
        assert_eq!(report.candidates[0].folds.len(), 4);
        assert!(report.candidates[0]
            .folds
            .iter()
            .all(|fold| matches!(fold.status, PlsCvFoldStatus::Failed { .. })));
    }

    fn experimental_pid3_config() -> Pid3Config {
        Pid3Config {
            experimental_allow_mixed_dimension_lattice: true,
            ..Pid3Config::assume_regular_full_dimensional()
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

    #[cfg(any())]
    #[test]
    fn bootstrap_pid3_rejects_duplicate_blocks_as_support_violations() {
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
        assert!(matches!(
            error,
            PidError::ObservedContinuousSampleIncompatibility { .. }
        ));
    }

    #[cfg(any())]
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
                validity: independent_validity(),
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

    #[cfg(any())]
    #[test]
    fn bootstrap_pid3_rejects_a_full_sample_block() {
        let (v, l, d, a) = make_vlda(20, 6);
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 20,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
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

    #[cfg(any())]
    #[test]
    fn bootstrap_pid3_rejects_unallocatable_resample_count_without_panicking() {
        let (v, l, d, a) = make_vlda(8, 6);
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 4,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
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

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }

    #[cfg(any())]
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
            validity: independent_validity(),
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
            "all-invalid resamples must not return NaN summaries"
        );
    }

    #[cfg(any())]
    #[test]
    fn bootstrap_pid3_is_deterministic() {
        let (v, l, d, a) = make_vlda(60, 123);
        let pid_cfg = experimental_pid3_config();
        let boot_cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 10,
            seed: 99,
            alpha: 0.05,
            validity: independent_validity(),
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

    #[cfg(any())]
    #[test]
    fn bootstrap_pid3_can_reject_after_a_valid_direct_point_estimate() {
        let (v, l, d, a) = make_vlda(60, 55);
        let pid_cfg = experimental_pid3_config();
        let boot_cfg = BootstrapConfig {
            n_boot: 5,
            block_size: 10,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
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
            Err(PidError::ObservedContinuousSampleIncompatibility { .. })
        ));
    }

    #[test]
    fn permutation_pid3_produces_complete_tail_fractions() {
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
        assert_eq!(result.null.tail, PermutationTail::Upper);
        // A successful inference uses the complete finite permutation set for every atom.
        assert!(result
            .atoms
            .iter()
            .all(|atom| atom.tail_fraction.is_some_and(f64::is_finite)
                && atom.n_valid == result.n_perm));
    }

    #[test]
    fn permutation_pid3_rejects_failed_and_nonfinite_transforms() {
        let failed = complete_pid3_permutation_values(
            Err(PidError::NumericalInstability {
                context: "synthetic permuted PID failure",
            }),
            1,
            ResourceBudget::default(),
        );
        assert!(matches!(
            failed,
            Err(PidError::NumericalInstability {
                context: "synthetic permuted PID failure"
            })
        ));

        let antichain = Antichain3::try_from_sets(&[0b001]).unwrap();
        let nonfinite = Pid3Result {
            n_samples: 1,
            k: 1,
            metric: crate::metric::Metric::Chebyshev,
            support_contract: crate::support::SupportContract::assume_regular_full_dimensional(),
            source_ambient_dimensions: [1, 1, 1],
            target_ambient_dimension: 1,
            method_status: crate::pid3::Pid3MethodStatus::ExperimentalMixedDimension,
            warnings: Vec::new(),
            redundancies: Vec::new(),
            atoms: vec![crate::pid3::Pid3Atom {
                antichain,
                value: f64::NAN,
            }],
        };
        assert!(matches!(
            complete_pid3_permutation_values(Ok(nonfinite), 1, ResourceBudget::default()),
            Err(PidError::NumericalInstability {
                context: "permutation_pid3 permutation"
            })
        ));
    }

    #[test]
    fn permutation_pid3_retains_a_failed_transform_end_to_end() {
        // Every marginal value is unique and the observed PID is valid. Some source-0
        // permutations nevertheless create an ambiguous positive nearest-neighbor shell at k=1,
        // which must invalidate the complete inference.
        let v = MatOwned::new(vec![0.0, 0.2, 1.0, 3.0], 4, 1).unwrap();
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
        let a = MatOwned::new(vec![0.0, 0.4, 1.0, 3.0], 4, 1).unwrap();
        let pid_cfg = Pid3Config {
            k: 1,
            ..experimental_pid3_config()
        };

        assert!(pid3_isx(v.as_ref(), l.as_ref(), d.as_ref(), a.as_ref(), &pid_cfg).is_ok());
        let report = permutation_pid3(
            v.as_ref(),
            l.as_ref(),
            d.as_ref(),
            a.as_ref(),
            &pid_cfg,
            40,
            0,
            7,
        )
        .unwrap();
        assert!(report.atoms.iter().all(|atom| atom.tail_fraction.is_none()));
        assert!(report.replicates.iter().any(|replicate| matches!(
            replicate.status,
            PermutationReplicateStatus::Failed { .. }
        )));
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

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
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
        assert_eq!(result.candidates.len(), 3);
        assert!(matches!(result.best_components, Some(1..=3)));
        assert!(result.candidates.iter().all(|candidate| {
            candidate.folds.len() == n
                && matches!(candidate.status, PlsCvCandidateStatus::Complete { .. })
        }));
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
        assert!((complete_q2(&ordinary, 0) - complete_q2(&scaled, 0)).abs() < 1.0e-12);
        assert!((complete_q2(&ordinary, 0) - complete_q2(&scaled_tiny, 0)).abs() < 1.0e-12);
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
        let cfg = Pid2Config::assume_regular_full_dimensional();
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
        let mut cfg = Pid2Config::assume_regular_full_dimensional();
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
            validity: independent_validity(),
        };
        let mats = [x.as_ref(), y.as_ref()];
        let scheme = RowResampleScheme::Subsample { subsample_len: 150 };
        let a = bootstrap_rows_stats(&mats, &cfg, scheme, pearson_stat).unwrap();
        let b = bootstrap_rows_stats(&mats, &cfg, scheme, pearson_stat).unwrap();
        assert_eq!(a.stats, b.stats);
        assert_eq!(complete_row_values(&a), complete_row_values(&b));
        assert_eq!(a.effective_resample_len, 150);
        let origins: std::collections::BTreeSet<usize> = a
            .replicates
            .iter()
            .filter_map(|replicate| replicate.circular_block_origin)
            .collect();
        assert!(
            origins.len() > 1,
            "subsample grid origin must be randomized"
        );
        assert!(origins.iter().all(|&origin| origin < x.as_ref().nrows()));
        let s = &a.stats.as_ref().unwrap()[0];
        assert_eq!(s.n_attempted, 64);
        assert_eq!(s.n_valid, 64);
        assert!(s.percentile_lower <= s.point_estimate + 0.05);
        assert!(s.percentile_upper >= s.point_estimate - 0.05);
        assert!(
            s.resample_standard_deviation > 0.0 && s.resample_standard_deviation < 0.2,
            "spread={}",
            s.resample_standard_deviation
        );
    }

    #[test]
    fn bootstrap_rows_stats_reports_rounded_subsample_length() {
        let (x, y) = make_linear_pair(100, 0.5, 19);
        let cfg = BootstrapConfig {
            n_boot: 2,
            block_size: 10,
            seed: 4,
            alpha: 0.05,
            validity: independent_validity(),
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
        let ksg_cfg = crate::ksg::KsgConfig::assume_regular_full_dimensional();
        let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
            Ok(vec![crate::ksg::ksg_mi(mats[0], mats[1], &ksg_cfg)?])
        };
        let cfg = BootstrapConfig {
            n_boot: 32,
            block_size: 1,
            seed: 3,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let mats = [x.as_ref(), y.as_ref()];
        let sub = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::Subsample { subsample_len: 120 },
            stat,
        )
        .unwrap();
        let statistic = &sub.stats.as_ref().unwrap()[0];
        assert_eq!(statistic.n_valid, 32);
        assert!(statistic.percentile_lower.is_finite());
        assert!(statistic.percentile_upper >= statistic.percentile_lower);
        assert!(statistic.percentile_lower <= statistic.point_estimate);
        assert!(statistic.percentile_upper >= statistic.point_estimate);
    }

    #[test]
    fn bootstrap_jitter_changes_a_rejected_ksg_resample_distribution() {
        // With-replacement bootstrap without jitter produces duplicate rows that
        // make KSG fail on resamples; selective deletion is invalid, so no summary is emitted.
        // Adding noise produces finite draws from a different distribution. This test pins that
        // mechanical distinction, not scientific validity of the jittered bootstrap.
        let (x, y) = make_linear_pair(150, 0.5, 17);
        let ksg_cfg = crate::ksg::KsgConfig::assume_regular_full_dimensional();
        let stat = |mats: &[MatRef<'_>]| -> PidResult<Vec<f64>> {
            Ok(vec![crate::ksg::ksg_mi(mats[0], mats[1], &ksg_cfg)?])
        };
        let cfg = BootstrapConfig {
            n_boot: 16,
            block_size: 1,
            seed: 3,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let mats = [x.as_ref(), y.as_ref()];
        let without = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
            stat,
        )
        .unwrap();
        assert!(without.stats.is_none());
        assert!(without
            .replicates
            .iter()
            .any(|replicate| matches!(replicate.status, RowResampleStatus::Failed { .. })));

        let with = bootstrap_rows_stats(
            &mats,
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            stat,
        )
        .unwrap();
        let statistic = &with.stats.as_ref().unwrap()[0];
        assert_eq!(statistic.n_valid, 16);
        assert!(statistic.percentile_lower.is_finite());
        assert!(statistic.percentile_upper >= statistic.percentile_lower);
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
            validity: independent_validity(),
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
            validity: independent_validity(),
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
            validity: independent_validity(),
        };
        let jittered = bootstrap_rows_stats(
            &[constant.as_ref()],
            &cfg,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            |_| Ok(vec![0.0]),
        )
        .unwrap();
        assert_eq!(jittered.stats.as_ref().unwrap()[0].n_valid, cfg.n_boot);

        // With no jitter, even a range whose variance is not representable need not have moments
        // computed merely to perform row selection without repeated indices.
        let extreme = MatOwned::new(vec![-f64::MAX, f64::MAX, -f64::MAX, f64::MAX], 4, 1).unwrap();
        let no_jitter = BootstrapConfig {
            n_boot: 3,
            block_size: 1,
            seed: 6,
            alpha: 0.1,
            validity: independent_validity(),
        };
        assert!(bootstrap_rows_stats(
            &[extreme.as_ref()],
            &no_jitter,
            RowResampleScheme::Subsample { subsample_len: 3 },
            |_| Ok(vec![0.0]),
        )
        .is_ok());
        let jittered = bootstrap_rows_stats(
            &[extreme.as_ref()],
            &no_jitter,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1e-9 },
            |_| Ok(vec![0.0]),
        )
        .unwrap();
        assert!(jittered.stats.is_none());
    }

    #[test]
    fn bootstrap_rows_stats_retains_post_jitter_overflow_reasons() {
        let extreme = MatOwned::new(vec![0.0, f64::MAX, 0.0, f64::MAX], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let result = bootstrap_rows_stats(
            &[extreme.as_ref()],
            &config,
            RowResampleScheme::BlockBootstrapJitter { jitter_rel: 1.0 },
            |_| Ok(vec![0.0]),
        );

        let result = result.unwrap();
        assert!(result.stats.is_none());
        assert!(result.replicates.iter().any(|replicate| matches!(
            replicate.status,
            RowResampleStatus::Failed {
                error: PidError::NumericalInstability {
                    context: "bootstrap_rows_stats jittered resample"
                }
            }
        )));
    }

    #[test]
    fn bootstrap_rows_stats_rejects_unallocatable_resample_count_without_panicking() {
        let matrix = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let outcome = std::panic::catch_unwind(|| {
            bootstrap_rows_stats(
                &[matrix.as_ref()],
                &config,
                RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
                |_| Ok(vec![0.0]),
            )
        });

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }

    #[test]
    fn bootstrap_rows_stats_rejects_unallocatable_moving_block_indices_without_panicking() {
        let logical_matrix = MatRef::new(&[], usize::MAX, 0).unwrap();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: usize::MAX - 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let outcome = std::panic::catch_unwind(|| {
            bootstrap_rows_stats(
                &[logical_matrix],
                &config,
                RowResampleScheme::BlockBootstrapJitter { jitter_rel: 0.0 },
                |_| Ok(vec![0.0]),
            )
        });

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
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
            validity: independent_validity(),
        };

        let outcome =
            std::panic::catch_unwind(|| bootstrap_quantized_sxpid2(s1, s2, target, 2, &config));

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }

    #[test]
    fn permutation_rows_pvalue_detects_signal_and_respects_null() {
        let ksg_cfg = crate::ksg::KsgConfig::assume_regular_full_dimensional();
        let stat = |mats: &[MatRef<'_>]| -> PidResult<f64> {
            crate::ksg::ksg_mi(mats[0], mats[1], &ksg_cfg)
        };

        // Strong linear signal: p should be at the add-one floor 1/(M+1).
        let (x, y) = make_linear_pair(150, 0.3, 21);
        let mats = [x.as_ref(), y.as_ref()];
        let signal = permutation_rows_pvalue(&mats, 0, 99, 5, stat).unwrap();
        assert_eq!(signal.n_valid, 99);
        assert_eq!(signal.null.tail, PermutationTail::Upper);
        let signal_fraction = signal.tail_fraction.unwrap();
        assert!(
            (signal_fraction - 1.0 / 100.0).abs() < 1e-12,
            "p={signal_fraction}"
        );

        // Independent pair: p should be large (deterministic for this seed; the
        // statistical claim is uniformity, this is a regression pin).
        let (x_a, _) = make_linear_pair(150, 0.3, 100);
        let (x_b, _) = make_linear_pair(150, 0.3, 200);
        let mats_null = [x_a.as_ref(), x_b.as_ref()];
        let null = permutation_rows_pvalue(&mats_null, 0, 99, 5, stat).unwrap();
        let null_fraction = null.tail_fraction.unwrap();
        assert!(null_fraction > 0.1, "p={null_fraction}");
    }

    #[test]
    fn permutation_rows_pvalue_is_deterministic_and_validates_input() {
        let (x, y) = make_linear_pair(80, 0.5, 33);
        let mats = [x.as_ref(), y.as_ref()];
        let stat = pearson_stat;
        let scalar = |m: &[MatRef<'_>]| -> PidResult<f64> { Ok(stat(m)?[0]) };
        let a = permutation_rows_pvalue(&mats, 0, 49, 9, scalar).unwrap();
        let b = permutation_rows_pvalue(&mats, 0, 49, 9, scalar).unwrap();
        assert_eq!(a.tail_fraction, b.tail_fraction);
        assert_eq!(a.null, b.null);
        assert_eq!(
            complete_permutation_values(&a),
            complete_permutation_values(&b)
        );
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

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }

    #[test]
    fn permutation_rows_retains_the_former_selective_16_of_40_failures_without_scoring() {
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
                ResourceBudget::default(),
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
        })
        .unwrap();
        assert_eq!(result.n_valid, 16);
        assert!(result.tail_fraction.is_none());
        assert_eq!(result.replicates.len(), 40);
        assert_eq!(
            result
                .replicates
                .iter()
                .filter(|replicate| matches!(
                    replicate.status,
                    PermutationReplicateStatus::Failed { .. }
                ))
                .count(),
            24
        );
    }

    #[test]
    fn permutation_rows_retains_every_nonfinite_null_transform() {
        let x = MatOwned::new(vec![0.0, 1.0, 2.0, 3.0], 4, 1).unwrap();
        let mats = [x.as_ref()];
        let calls = std::cell::Cell::new(0usize);
        let result = permutation_rows_pvalue(&mats, 0, 5, 1, |_| {
            let call = calls.get();
            calls.set(call + 1);
            Ok(if call == 0 { 1.0 } else { f64::NAN })
        });

        let result = result.unwrap();
        assert!(result.tail_fraction.is_none());
        assert_eq!(result.n_valid, 0);
        assert_eq!(result.replicates.len(), 5);
        assert_eq!(calls.get(), 6, "observed plus every requested transform");
    }
}
