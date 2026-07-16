//! Block bootstrap for uncertainty quantification of estimators.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED RESAMPLING METHOD.** The generic with-replacement path implements the
//! moving-block bootstrap of Künsch (1989) under `experimental-pipelines`. pid-rs adds typed
//! dependence/block-length declarations, complete-replicate failure handling, deterministic
//! seeds, and resource controls. Returned spreads and percentiles describe the resampling
//! distribution; the generic API does not label them as calibrated standard errors or confidence
//! intervals.
//!
//! Method catalog: resampling.moving-block-bootstrap
//!
//! **NO IMPLEMENTATION.** No generic calibrated bootstrap confidence interval for KSG or
//! continuous PID is implemented. With-replacement duplicates can violate continuous-sample
//! conditions, and estimator-specific m-out-of-n centering/scaling is outside this API.
//!
//! Method catalog: unsupported.generic-knn-bootstrap-ci
//!
//! Given a vector of i.i.d. or weakly dependent samples and a statistic function,
//! block bootstrap resamples contiguous blocks (with replacement) and recomputes
//! the statistic on each resample. This yields a bootstrap distribution from which
//! an empirical resampling distribution can be described. The returned spread and raw
//! percentiles are not labelled as a standard error or confidence interval: those inferential
//! interpretations require statistic-specific calibration that this generic module cannot prove.
//!
//! This implements the **moving-block bootstrap** (Künsch 1989): block starts are
//! drawn uniformly over all `n − block_size + 1` positions (so every sample — head,
//! interior, and tail — is reachable), and `⌈n / block_size⌉` blocks are
//! concatenated and truncated to exactly `n`. Overlapping moving blocks avoid the
//! tail-drop and grid-alignment bias of a fixed non-overlapping partition.
//!
//! [`crate::experimental::pipelines::bootstrap_rows_stats`] additionally supports random-origin
//! circular block subsampling without repeated row indices for kNN diagnostics; that is the path
//! Exp0 uses. Ties already present in the original data remain possible.
//!
//! # Example
//! ```
//! use pid_core::{
//!     experimental::pipelines::{
//!         block_bootstrap, BlockLengthSelection, BootstrapConfig,
//!         ResamplingValidityDeclaration, StatisticCallbackDeclaration,
//!     },
//!     ResourceEstimate,
//! };
//!
//! let data: Vec<f64> = (0..200).map(|i| (i as f64) * 0.01).collect();
//! let cfg = BootstrapConfig::new(
//!     100,
//!     20,
//!     42,
//!     0.05,
//!     ResamplingValidityDeclaration::independent_rows(
//!         BlockLengthSelection::FixedAPriori,
//!     ),
//! )?;
//! let result = block_bootstrap(
//!     &data,
//!     &cfg,
//!     StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
//!     |samples| Ok(samples.iter().sum::<f64>() / samples.len() as f64),
//! )?;
//! let Some(summary) = result.summary else {
//!     return Err(pid_core::PidError::NumericalInstability {
//!         context: "block-bootstrap example: incomplete resampling distribution",
//!     });
//! };
//! assert!(summary.percentile_lower < summary.percentile_upper);
//! # Ok::<(), pid_core::PidError>(())
//! ```

use crate::error::{PidError, PidResult};
use crate::par::slice_map_index_ordered;
use crate::preprocess::SplitMix64;
pub use crate::resource::CancellationToken;
use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::finite_mean_std_sample;

/// Scientific dependence assumption attached to a resampling procedure.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum ResamplingDependence {
    /// No assumption declared. Validation rejects this sentinel before user code runs.
    Undeclared,
    /// Rows are mutually independent and exchangeable under the sampling law.
    IndependentExchangeableRows,
    /// A weakly dependent stationary series with a declared dependence scale in rows.
    WeaklyDependentStationary {
        /// Predeclared or training-only estimate of the dependence scale.
        dependence_scale_rows: usize,
    },
}

/// How the block length was selected without using the reported resampling outcomes.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum BlockLengthSelection {
    /// Fixed before inspecting the evaluation data or its resampling outcomes.
    FixedAPriori,
    /// Selected using a disjoint training sample.
    TrainingDataOnly,
    /// One member of an explicitly reported block-length sensitivity analysis.
    SensitivityAnalysis,
}

/// Explicit validity declaration required by generic resampling APIs.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub struct ResamplingValidityDeclaration {
    /// Dependence structure the caller asserts for the sampled rows.
    pub dependence: ResamplingDependence,
    /// Non-post-selective basis for the configured block length.
    pub block_length_selection: BlockLengthSelection,
}

impl ResamplingValidityDeclaration {
    /// Declare independent, exchangeable rows.
    pub const fn independent_rows(block_length_selection: BlockLengthSelection) -> Self {
        Self {
            dependence: ResamplingDependence::IndependentExchangeableRows,
            block_length_selection,
        }
    }

    /// Declare a weakly dependent stationary series and its dependence scale.
    pub fn weakly_dependent_stationary(
        dependence_scale_rows: usize,
        block_length_selection: BlockLengthSelection,
    ) -> PidResult<Self> {
        if dependence_scale_rows == 0 {
            return Err(PidError::InvalidConfig {
                context: "ResamplingValidityDeclaration::weakly_dependent_stationary",
                message: "dependence_scale_rows must be positive",
            });
        }
        Ok(Self {
            dependence: ResamplingDependence::WeaklyDependentStationary {
                dependence_scale_rows,
            },
            block_length_selection,
        })
    }

    pub(crate) fn validate(self, context: &'static str) -> PidResult<()> {
        if self.dependence == ResamplingDependence::Undeclared {
            return Err(PidError::InvalidConfig {
                context,
                message: "a resampling dependence/validity declaration is required",
            });
        }
        if let ResamplingDependence::WeaklyDependentStationary {
            dependence_scale_rows,
        } = self.dependence
        {
            if dependence_scale_rows == 0 {
                return Err(PidError::InvalidConfig {
                    context,
                    message: "dependence_scale_rows must be positive",
                });
            }
        }
        Ok(())
    }
}

/// Declared output width and conservative resources for one statistic callback invocation.
///
/// Pipeline preflight charges the callback once for the point estimate and once per requested
/// resample/permutation. `per_call.estimated_bytes` is treated as peak scratch, while operation and
/// pairwise-distance counts are charged for every invocation.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub struct StatisticCallbackDeclaration {
    /// Number of finite scalar outputs returned by every successful invocation.
    pub output_values: usize,
    /// Conservative resource estimate for one invocation.
    pub per_call: ResourceEstimate,
}

impl StatisticCallbackDeclaration {
    /// Declare a scalar callback.
    pub const fn scalar(per_call: ResourceEstimate) -> Self {
        Self {
            output_values: 1,
            per_call,
        }
    }

    /// Declare a fixed-width vector callback.
    pub fn vector(output_values: usize, per_call: ResourceEstimate) -> PidResult<Self> {
        if output_values == 0 {
            return Err(PidError::InvalidConfig {
                context: "StatisticCallbackDeclaration::vector",
                message: "output_values must be positive",
            });
        }
        Ok(Self {
            output_values,
            per_call,
        })
    }

    pub(crate) fn validate(self, context: &'static str) -> PidResult<()> {
        if self.output_values == 0 {
            Err(PidError::InvalidConfig {
                context,
                message: "statistic callback output_values must be positive",
            })
        } else {
            Ok(())
        }
    }
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

/// Configuration for block bootstrap.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct BootstrapConfig {
    /// Number of bootstrap resamples attempted.
    pub n_boot: usize,
    /// Block size (number of contiguous samples per block), which must be smaller than the sample
    /// count so the moving-block distribution has more than one possible block.
    pub block_size: usize,
    /// PRNG seed for reproducibility.
    pub seed: u64,
    /// Two-sided tail mass for the raw percentile summary (e.g. 0.05 returns the empirical
    /// 2.5th and 97.5th percentiles; it does not assert 95% confidence coverage).
    pub alpha: f64,
    /// Explicit sampling/dependence and block-selection validity declaration.
    pub validity: ResamplingValidityDeclaration,
}

impl Default for BootstrapConfig {
    fn default() -> Self {
        Self {
            n_boot: 200,
            block_size: 10,
            seed: 0,
            alpha: 0.05,
            validity: ResamplingValidityDeclaration {
                dependence: ResamplingDependence::Undeclared,
                block_length_selection: BlockLengthSelection::FixedAPriori,
            },
        }
    }
}

impl BootstrapConfig {
    /// Construct a declared resampling configuration.
    pub fn new(
        n_boot: usize,
        block_size: usize,
        seed: u64,
        alpha: f64,
        validity: ResamplingValidityDeclaration,
    ) -> PidResult<Self> {
        validity.validate("BootstrapConfig::new")?;
        if n_boot < 2 {
            return Err(PidError::InvalidConfig {
                context: "BootstrapConfig::new",
                message: "n_boot must be at least two",
            });
        }
        if block_size == 0 {
            return Err(PidError::InvalidConfig {
                context: "BootstrapConfig::new",
                message: "block_size must be positive",
            });
        }
        if !(alpha > 0.0 && alpha < 1.0) {
            return Err(PidError::InvalidConfig {
                context: "BootstrapConfig::new",
                message: "alpha must lie in the open interval (0, 1)",
            });
        }
        Ok(Self {
            n_boot,
            block_size,
            seed,
            alpha,
            validity,
        })
    }
}

/// Complete empirical distribution summary, available only when every requested replicate
/// succeeds and is finite.
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct ResamplingDistributionSummary {
    /// Arithmetic mean of the complete resampling distribution.
    pub resample_mean: f64,
    /// Sample standard deviation of the resampling distribution. This is a descriptive spread,
    /// not a generic calibrated standard error.
    pub resample_standard_deviation: f64,
    /// Lower raw empirical percentile at `alpha / 2`.
    pub percentile_lower: f64,
    /// Upper raw empirical percentile at `1 - alpha / 2`.
    pub percentile_upper: f64,
}

/// Status of one requested scalar resampling replicate.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub enum BootstrapReplicateStatus {
    /// Callback completed with a finite scalar value.
    Complete { value: f64 },
    /// Callback failed or returned a non-finite value. The reason is retained verbatim.
    Failed { error: PidError },
}

/// Indexed outcome for one requested scalar resampling replicate.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct BootstrapReplicateOutcome {
    pub replicate_index: usize,
    pub status: BootstrapReplicateStatus,
}

/// Versioned block-resampling algorithm identifier.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub enum BlockResamplingAlgorithmRevision {
    /// Künsch moving blocks and random-origin circular no-replacement blocks.
    V1,
}

/// Typed block-resampling provenance.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[non_exhaustive]
pub struct BlockResamplingProvenance {
    pub validity: ResamplingValidityDeclaration,
    pub block_size: usize,
    pub seed: u64,
    pub requested_replicates: usize,
    /// Algorithm revision pinned for deterministic reproduction.
    pub algorithm_revision: BlockResamplingAlgorithmRevision,
}

/// Result of a generic scalar moving-block resampling run.
#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct BootstrapResult {
    /// Point estimate on the original data.
    pub point_estimate: f64,
    /// Descriptive distribution summary. `None` if any requested replicate failed; callers must
    /// inspect [`Self::replicates`] rather than conditioning on the successful subset.
    pub summary: Option<ResamplingDistributionSummary>,
    /// Every requested replicate in deterministic index order, including structured failures.
    pub replicates: Vec<BootstrapReplicateOutcome>,
    /// Dependence, block-length, seed, and algorithm provenance.
    pub provenance: BlockResamplingProvenance,
}

fn validate_bootstrap_config(
    context: &'static str,
    data_len: usize,
    cfg: &BootstrapConfig,
) -> PidResult<()> {
    cfg.validity.validate(context)?;
    if data_len == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "data must not be empty",
        });
    }
    if cfg.block_size == 0 || cfg.block_size >= data_len {
        return Err(PidError::InvalidConfig {
            context,
            message: "block_size must be in 1..data.len()",
        });
    }
    if cfg.n_boot < 2 {
        return Err(PidError::InvalidConfig {
            context,
            message: "n_boot must be >= 2 to estimate bootstrap variance",
        });
    }
    if !(cfg.alpha > 0.0 && cfg.alpha < 1.0) {
        return Err(PidError::InvalidConfig {
            context,
            message: "alpha must be in the open interval (0, 1)",
        });
    }
    Ok(())
}

fn checked_add(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_add(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_mul(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn bootstrap_resource_estimate_impl(
    operation: &'static str,
    data_len: usize,
    cfg: &BootstrapConfig,
    simultaneous_series: usize,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
) -> PidResult<ResourceEstimate> {
    validate_bootstrap_config(operation, data_len, cfg)?;
    callback.validate(operation)?;
    if callback.output_values != 1 {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "scalar bootstrap requires callback output_values == 1",
        });
    }
    budget.validate(operation)?;
    let n = data_len as u128;
    let n_boot = cfg.n_boot as u128;
    let blocks_needed = data_len.div_ceil(cfg.block_size) as u128;
    let rounded_len = checked_mul(operation, blocks_needed, cfg.block_size as u128)?;
    let vec_header = std::mem::size_of::<Vec<usize>>() as u128;
    let usize_bytes = std::mem::size_of::<usize>() as u128;
    let result_bytes = std::mem::size_of::<PidResult<f64>>() as u128;

    let schedule_headers = checked_mul(operation, n_boot, vec_header)?;
    let schedule_payload = checked_mul(
        operation,
        checked_mul(operation, n_boot, blocks_needed)?,
        usize_bytes,
    )?;
    let ordered_results = checked_mul(operation, n_boot, result_bytes)?;
    let retained_outcomes = checked_mul(
        operation,
        n_boot,
        std::mem::size_of::<BootstrapReplicateOutcome>() as u128,
    )?;
    let retained_statistics = checked_mul(operation, n_boot, std::mem::size_of::<f64>() as u128)?;
    let one_resample = checked_mul(
        operation,
        checked_mul(operation, rounded_len, simultaneous_series as u128)?,
        std::mem::size_of::<f64>() as u128,
    )?;
    #[cfg(feature = "parallel")]
    let (worker_count, worker_stacks) = {
        let workers = cfg.n_boot.min(budget.max_threads) as u128;
        (
            workers,
            checked_mul(
                operation,
                budget.max_threads as u128,
                crate::par::WORKER_STACK_BYTES as u128,
            )?,
        )
    };
    #[cfg(not(feature = "parallel"))]
    let (worker_count, worker_stacks) = (1, 0);
    let concurrent_resamples = checked_mul(operation, worker_count, one_resample)?;
    let callback_peak_bytes =
        checked_mul(operation, worker_count, callback.per_call.estimated_bytes)?;
    let estimated_bytes = [
        schedule_headers,
        schedule_payload,
        ordered_results,
        retained_outcomes,
        retained_statistics,
        concurrent_resamples,
        worker_stacks,
        callback_peak_bytes,
    ]
    .into_iter()
    .try_fold(0_u128, |sum, bytes| checked_add(operation, sum, bytes))?;
    let draw_work = checked_mul(operation, n_boot, blocks_needed)?;
    let copy_work = checked_mul(
        operation,
        checked_mul(operation, n_boot, n)?,
        simultaneous_series as u128,
    )?;
    let callback_calls = checked_add(operation, n_boot, 1)?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: checked_mul(
            operation,
            callback_calls,
            callback.per_call.pairwise_distances,
        )?,
        operations_hint: checked_add(
            operation,
            checked_add(operation, draw_work, copy_work)?,
            checked_mul(operation, callback_calls, callback.per_call.operations_hint)?,
        )?,
    })
}

/// Estimate the retained schedule, distribution, worker stacks, and simultaneous resample heap
/// for [`block_bootstrap_with_budget`], including the supplied callback declaration.
pub fn block_bootstrap_resource_estimate(
    data_len: usize,
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
) -> PidResult<ResourceEstimate> {
    bootstrap_resource_estimate_impl("block_bootstrap", data_len, cfg, 1, budget, callback)
}

/// Estimate the corresponding paired-resample resources for
/// [`block_bootstrap_paired_with_budget`].
pub fn block_bootstrap_paired_resource_estimate(
    data_len: usize,
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
) -> PidResult<ResourceEstimate> {
    bootstrap_resource_estimate_impl("block_bootstrap_paired", data_len, cfg, 2, budget, callback)
}

fn summarize_bootstrap(
    context: &'static str,
    point_estimate: f64,
    replicates: Vec<BootstrapReplicateOutcome>,
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
) -> PidResult<BootstrapResult> {
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context });
    }

    if replicates.len() != cfg.n_boot {
        return Err(PidError::NumericalInstability { context });
    }
    let all_complete = replicates
        .iter()
        .all(|outcome| matches!(outcome.status, BootstrapReplicateStatus::Complete { .. }));
    let summary = if all_complete {
        let mut values = try_vec_with_capacity(context, cfg.n_boot, budget)?;
        for outcome in &replicates {
            let BootstrapReplicateStatus::Complete { value } = outcome.status else {
                return Err(PidError::NumericalInstability { context });
            };
            values.push(value);
        }
        values.sort_by(f64::total_cmp);
        let (resample_mean, resample_standard_deviation) =
            finite_mean_std_sample(&values, context)?;
        let lo_idx = ((cfg.alpha / 2.0) * values.len() as f64).floor() as usize;
        let hi_idx = (((1.0 - cfg.alpha / 2.0) * values.len() as f64).ceil() as usize)
            .saturating_sub(1)
            .min(values.len() - 1);
        Some(ResamplingDistributionSummary {
            resample_mean,
            resample_standard_deviation,
            percentile_lower: values[lo_idx],
            percentile_upper: values[hi_idx],
        })
    } else {
        None
    };

    Ok(BootstrapResult {
        point_estimate,
        summary,
        replicates,
        provenance: BlockResamplingProvenance {
            validity: cfg.validity,
            block_size: cfg.block_size,
            seed: cfg.seed,
            requested_replicates: cfg.n_boot,
            algorithm_revision: BlockResamplingAlgorithmRevision::V1,
        },
    })
}

/// Run block bootstrap on a 1-D sample vector with a user-supplied statistic.
///
/// `statistic` is called with a slice of resampled values and must return a scalar. It must be a
/// deterministic, stateless function of that slice: with the `parallel` feature, different
/// resamples may be evaluated concurrently and in an unspecified execution order.
///
/// With the `parallel` feature the per-resample `statistic` evaluations run data-parallel,
/// but the resample **index sequences are drawn serially** from the seeded RNG (so the RNG
/// stream is unchanged) and the resulting outcomes are collected **in resample
/// order** before any reduction — so the result is bit-for-bit identical to the serial path.
///
/// # Errors
///
/// Returns [`PidError::InvalidConfig`] for empty data or an invalid bootstrap configuration,
/// [`PidError::ResourceLimitExceeded`] when preflight exceeds the inherited budget, and
/// [`PidError::AllocationFailed`] if a budget-approved fallible reserve cannot be satisfied.
/// Returns [`PidError::NumericalInstability`] if the original statistic is non-finite.
/// Per-replicate failures/non-finite values are retained and make `summary` unavailable.
pub fn block_bootstrap<F>(
    data: &[f64],
    cfg: &BootstrapConfig,
    callback: StatisticCallbackDeclaration,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64]) -> PidResult<f64> + Sync + Send,
{
    block_bootstrap_with_budget(data, cfg, ResourceBudget::default(), callback, statistic)
}

/// [`block_bootstrap`] with a caller-supplied aggregate resource ceiling.
///
/// The preflight includes the complete retained draw schedule, result distribution, all private
/// Rayon worker stacks, one simultaneously materialized resample per active worker, and the
/// caller-declared per-call callback resources. The library cannot verify that an opaque callback
/// declaration is conservative; under-declaration violates this API's resource contract.
pub fn block_bootstrap_with_budget<F>(
    data: &[f64],
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64]) -> PidResult<f64> + Sync + Send,
{
    let cancellation = CancellationToken::new();
    block_bootstrap_with_cancellation(data, cfg, budget, callback, &cancellation, statistic)
}

/// [`block_bootstrap_with_budget`] with cooperative cancellation checks between replicates.
pub fn block_bootstrap_with_cancellation<F>(
    data: &[f64],
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    cancellation: &CancellationToken,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64]) -> PidResult<f64> + Sync + Send,
{
    const CONTEXT: &str = "block_bootstrap";
    validate_bootstrap_config(CONTEXT, data.len(), cfg)?;
    budget.check(
        CONTEXT,
        block_bootstrap_resource_estimate(data.len(), cfg, budget, callback)?,
    )?;
    cancellation.check(CONTEXT, 0, cfg.n_boot + 1)?;

    let n = data.len();
    // Moving-block bootstrap: every position is a valid block start, and we draw
    // enough blocks to cover n, then truncate — so no sample is ever dropped.
    let n_starts = n - cfg.block_size + 1;
    let blocks_needed = n.div_ceil(cfg.block_size);
    let resample_capacity =
        blocks_needed
            .checked_mul(cfg.block_size)
            .ok_or(PidError::InvalidConfig {
                context: CONTEXT,
                message: "resample length overflow",
            })?;

    // Reserve the outer plan before invoking user code so an impossible requested count is a
    // normal library error, not a `Vec` capacity panic during iterator collection.
    let mut starts = try_vec_with_capacity::<Vec<usize>>(CONTEXT, cfg.n_boot, budget)?;

    // Point estimate
    let point_estimate = statistic(data)?;
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context: CONTEXT });
    }

    // Draw every resample's block-start sequence serially so the RNG stream is identical to
    // the serial path, regardless of whether the statistic is later evaluated in parallel.
    let mut rng = SplitMix64::new(cfg.seed);
    for replicate_index in 0..cfg.n_boot {
        cancellation.check(CONTEXT, replicate_index + 1, cfg.n_boot + 1)?;
        let mut block_starts = try_vec_with_capacity(CONTEXT, blocks_needed, budget)?;
        for _ in 0..blocks_needed {
            block_starts.push(uniform_index(&mut rng, n_starts));
        }
        starts.push(block_starts);
    }

    let build_resample = |block_starts: &[usize]| -> PidResult<Vec<f64>> {
        let mut resample = try_vec_with_capacity(CONTEXT, resample_capacity, budget)?;
        for &start in block_starts {
            resample.extend_from_slice(&data[start..start + cfg.block_size]);
        }
        resample.truncate(n);
        Ok(resample)
    };

    // Evaluate the statistic on each resample, collected in resample (index) order.
    let worker_heap_bytes =
        ResourceEstimate::contiguous::<f64>(CONTEXT, resample_capacity)?.estimated_bytes;
    let evaluated = slice_map_index_ordered(&starts, budget, worker_heap_bytes, |bs| {
        cancellation.check(CONTEXT, 1, cfg.n_boot + 1)?;
        build_resample(bs).and_then(|resample| statistic(&resample))
    })?;
    let mut replicates = try_vec_with_capacity(CONTEXT, cfg.n_boot, budget)?;
    for (replicate_index, result) in evaluated.into_iter().enumerate() {
        let status = match result {
            Err(error @ PidError::Cancelled { .. }) => return Err(error),
            Ok(value) if value.is_finite() => BootstrapReplicateStatus::Complete { value },
            Ok(_) => BootstrapReplicateStatus::Failed {
                error: PidError::NumericalInstability {
                    context: "block_bootstrap replicate statistic",
                },
            },
            Err(error) => BootstrapReplicateStatus::Failed { error },
        };
        replicates.push(BootstrapReplicateOutcome {
            replicate_index,
            status,
        });
    }
    summarize_bootstrap(CONTEXT, point_estimate, replicates, cfg, budget)
}

/// Run block bootstrap on paired (x, y) samples, preserving pairing within blocks.
///
/// `statistic` receives two slices `(x_resample, y_resample)` of equal length. It must be a
/// deterministic, stateless function of those slices because parallel builds may evaluate
/// resamples concurrently and in an unspecified execution order.
///
/// # Errors
///
/// Returns [`PidError::RowCountMismatch`] if `x` and `y` have different lengths,
/// [`PidError::InvalidConfig`] for empty data or an invalid bootstrap configuration,
/// [`PidError::ResourceLimitExceeded`] / [`PidError::AllocationFailed`] for bounded allocation
/// failures, and [`PidError::NumericalInstability`] if the original statistic is non-finite.
/// Per-replicate failures/non-finite values are retained and make `summary` unavailable.
pub fn block_bootstrap_paired<F>(
    x: &[f64],
    y: &[f64],
    cfg: &BootstrapConfig,
    callback: StatisticCallbackDeclaration,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64], &[f64]) -> PidResult<f64> + Sync + Send,
{
    block_bootstrap_paired_with_budget(x, y, cfg, ResourceBudget::default(), callback, statistic)
}

/// [`block_bootstrap_paired`] with a caller-supplied aggregate resource ceiling.
pub fn block_bootstrap_paired_with_budget<F>(
    x: &[f64],
    y: &[f64],
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64], &[f64]) -> PidResult<f64> + Sync + Send,
{
    let cancellation = CancellationToken::new();
    block_bootstrap_paired_with_cancellation(x, y, cfg, budget, callback, &cancellation, statistic)
}

/// [`block_bootstrap_paired_with_budget`] with cooperative cancellation checks.
pub fn block_bootstrap_paired_with_cancellation<F>(
    x: &[f64],
    y: &[f64],
    cfg: &BootstrapConfig,
    budget: ResourceBudget,
    callback: StatisticCallbackDeclaration,
    cancellation: &CancellationToken,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64], &[f64]) -> PidResult<f64> + Sync + Send,
{
    const CONTEXT: &str = "block_bootstrap_paired";
    if x.len() != y.len() {
        return Err(PidError::RowCountMismatch {
            context: CONTEXT,
            left_rows: x.len(),
            right_rows: y.len(),
        });
    }
    validate_bootstrap_config(CONTEXT, x.len(), cfg)?;
    budget.check(
        CONTEXT,
        block_bootstrap_paired_resource_estimate(x.len(), cfg, budget, callback)?,
    )?;
    cancellation.check(CONTEXT, 0, cfg.n_boot + 1)?;

    let n = x.len();
    // Moving-block bootstrap (same scheme as `block_bootstrap`), applied jointly to
    // the (x, y) pair so within-block pairing is preserved.
    let n_starts = n - cfg.block_size + 1;
    let blocks_needed = n.div_ceil(cfg.block_size);
    let resample_capacity =
        blocks_needed
            .checked_mul(cfg.block_size)
            .ok_or(PidError::InvalidConfig {
                context: CONTEXT,
                message: "resample length overflow",
            })?;

    let mut starts = try_vec_with_capacity::<Vec<usize>>(CONTEXT, cfg.n_boot, budget)?;

    let point_estimate = statistic(x, y)?;
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context: CONTEXT });
    }

    // Draw resample block-start sequences serially (RNG stream unchanged), then evaluate the
    // statistic per resample, collected in index order — bit-identical serial vs parallel.
    let mut rng = SplitMix64::new(cfg.seed);
    for replicate_index in 0..cfg.n_boot {
        cancellation.check(CONTEXT, replicate_index + 1, cfg.n_boot + 1)?;
        let mut block_starts = try_vec_with_capacity(CONTEXT, blocks_needed, budget)?;
        for _ in 0..blocks_needed {
            block_starts.push(uniform_index(&mut rng, n_starts));
        }
        starts.push(block_starts);
    }

    let one_series_bytes =
        ResourceEstimate::contiguous::<f64>(CONTEXT, resample_capacity)?.estimated_bytes;
    let worker_heap_bytes = one_series_bytes
        .checked_mul(2)
        .ok_or(PidError::SizeOverflow { operation: CONTEXT })?;
    let evaluated = slice_map_index_ordered(
        &starts,
        budget,
        worker_heap_bytes,
        |block_starts| -> PidResult<f64> {
            cancellation.check(CONTEXT, 1, cfg.n_boot + 1)?;
            let mut rx = try_vec_with_capacity(CONTEXT, resample_capacity, budget)?;
            let mut ry = try_vec_with_capacity(CONTEXT, resample_capacity, budget)?;
            for &start in block_starts {
                rx.extend_from_slice(&x[start..start + cfg.block_size]);
                ry.extend_from_slice(&y[start..start + cfg.block_size]);
            }
            rx.truncate(n);
            ry.truncate(n);
            statistic(&rx, &ry)
        },
    )?;

    let mut replicates = try_vec_with_capacity(CONTEXT, cfg.n_boot, budget)?;
    for (replicate_index, result) in evaluated.into_iter().enumerate() {
        let status = match result {
            Err(error @ PidError::Cancelled { .. }) => return Err(error),
            Ok(value) if value.is_finite() => BootstrapReplicateStatus::Complete { value },
            Ok(_) => BootstrapReplicateStatus::Failed {
                error: PidError::NumericalInstability {
                    context: "block_bootstrap_paired replicate statistic",
                },
            },
            Err(error) => BootstrapReplicateStatus::Failed { error },
        };
        replicates.push(BootstrapReplicateOutcome {
            replicate_index,
            status,
        });
    }

    summarize_bootstrap(CONTEXT, point_estimate, replicates, cfg, budget)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    const CALLBACK: StatisticCallbackDeclaration =
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO);

    fn independent_validity() -> ResamplingValidityDeclaration {
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori)
    }

    fn run_bootstrap<F>(
        data: &[f64],
        config: &BootstrapConfig,
        statistic: F,
    ) -> PidResult<BootstrapResult>
    where
        F: Fn(&[f64]) -> f64 + Sync + Send,
    {
        block_bootstrap(data, config, CALLBACK, |values| Ok(statistic(values)))
    }

    fn run_paired<F>(
        x: &[f64],
        y: &[f64],
        config: &BootstrapConfig,
        statistic: F,
    ) -> PidResult<BootstrapResult>
    where
        F: Fn(&[f64], &[f64]) -> f64 + Sync + Send,
    {
        block_bootstrap_paired(x, y, config, CALLBACK, |left, right| {
            Ok(statistic(left, right))
        })
    }

    fn complete_values(result: &BootstrapResult) -> Vec<u64> {
        result
            .replicates
            .iter()
            .map(|outcome| match outcome.status {
                BootstrapReplicateStatus::Complete { value } => value.to_bits(),
                BootstrapReplicateStatus::Failed { .. } => panic!("unexpected failed replicate"),
            })
            .collect()
    }

    #[test]
    fn budget_rejection_precedes_user_statistic_execution() {
        let calls = AtomicUsize::new(0);
        let config = BootstrapConfig {
            n_boot: 4,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let budget = ResourceBudget {
            max_bytes: 1,
            max_pairwise_distances: 1,
            max_operations_hint: 100,
            max_threads: 1,
        };

        let result = block_bootstrap_with_budget(&[1.0, 2.0], &config, budget, CALLBACK, |_| {
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
    fn default_config_requires_an_explicit_validity_declaration() {
        let calls = AtomicUsize::new(0);
        let data = [0.0; 20];

        let result = block_bootstrap(&data, &BootstrapConfig::default(), CALLBACK, |_| {
            calls.fetch_add(1, Ordering::Relaxed);
            Ok(0.0)
        });

        assert!(matches!(result, Err(PidError::InvalidConfig { .. })));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn callback_resources_are_charged_before_execution() {
        let calls = AtomicUsize::new(0);
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let callback = StatisticCallbackDeclaration::scalar(ResourceEstimate {
            estimated_bytes: 0,
            pairwise_distances: 0,
            operations_hint: 100_000,
        });
        let budget = ResourceBudget {
            max_operations_hint: 10_000,
            max_threads: 1,
            ..ResourceBudget::default()
        };

        let result = block_bootstrap_with_budget(&[1.0, 2.0], &config, budget, callback, |_| {
            calls.fetch_add(1, Ordering::Relaxed);
            Ok(0.0)
        });

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded {
                resource: "operations_hint",
                ..
            })
        ));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn cancellation_precedes_point_statistic_execution() {
        let calls = AtomicUsize::new(0);
        let cancellation = CancellationToken::new();
        cancellation.cancel();
        let config = BootstrapConfig {
            n_boot: 2,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let result = block_bootstrap_with_cancellation(
            &[1.0, 2.0],
            &config,
            ResourceBudget::default(),
            CALLBACK,
            &cancellation,
            |_| {
                calls.fetch_add(1, Ordering::Relaxed);
                Ok(0.0)
            },
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                completed_units: 0,
                ..
            })
        ));
        assert_eq!(calls.load(Ordering::Relaxed), 0);
    }

    #[test]
    fn callback_failures_are_retained_for_every_replicate() {
        let calls = AtomicUsize::new(0);
        let config = BootstrapConfig {
            n_boot: 4,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let report = block_bootstrap(&[1.0, 2.0], &config, CALLBACK, |_| {
            let call = calls.fetch_add(1, Ordering::Relaxed);
            if call == 0 {
                Ok(0.0)
            } else {
                Err(PidError::NumericalInstability {
                    context: "synthetic callback failure",
                })
            }
        })
        .unwrap();

        assert!(report.summary.is_none());
        assert_eq!(report.replicates.len(), config.n_boot);
        assert!(report.replicates.iter().all(|replicate| matches!(
            replicate.status,
            BootstrapReplicateStatus::Failed {
                error: PidError::NumericalInstability {
                    context: "synthetic callback failure"
                }
            }
        )));
        assert_eq!(calls.load(Ordering::Relaxed), config.n_boot + 1);
    }

    #[cfg(feature = "parallel")]
    #[test]
    fn bootstrap_is_bit_identical_across_thread_budgets() {
        let data: Vec<f64> = (0..97).map(|index| (index % 19) as f64 / 8.0).collect();
        let config = BootstrapConfig {
            n_boot: 67,
            block_size: 7,
            seed: 91,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let statistic = |values: &[f64]| Ok(values.iter().sum::<f64>() / values.len() as f64);
        let baseline = block_bootstrap_with_budget(
            &data,
            &config,
            ResourceBudget {
                max_threads: 1,
                ..ResourceBudget::default()
            },
            CALLBACK,
            statistic,
        )
        .unwrap();
        let maximum = std::thread::available_parallelism().map_or(1, std::num::NonZero::get);

        for threads in [1, 2, 3, 4, maximum] {
            let actual = block_bootstrap_with_budget(
                &data,
                &config,
                ResourceBudget {
                    max_threads: threads,
                    ..ResourceBudget::default()
                },
                CALLBACK,
                statistic,
            )
            .unwrap();

            assert_eq!(actual.summary, baseline.summary, "thread budget {threads}");
            assert_eq!(
                complete_values(&actual),
                complete_values(&baseline),
                "thread budget {threads}"
            );
        }
    }

    #[test]
    fn bootstrap_mean_of_uniform_has_narrow_raw_percentile_range() {
        let n = 500;
        let data: Vec<f64> = (0..n)
            .map(|i| {
                let mut rng = SplitMix64::new(123 + i as u64);
                let u = rng.next_u64();
                // Simple transform to roughly uniform [0,1]
                (u as f64) / (u64::MAX as f64)
            })
            .collect();

        let cfg = BootstrapConfig {
            n_boot: 200,
            block_size: 25,
            seed: 42,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let result =
            run_bootstrap(&data, &cfg, |s| s.iter().sum::<f64>() / s.len() as f64).unwrap();
        let summary = result.summary.as_ref().unwrap();

        // Mean should be ~0.5 for uniform [0,1]
        assert!(
            (result.point_estimate - 0.5).abs() < 0.1,
            "point estimate {}",
            result.point_estimate
        );
        assert!(
            summary.resample_standard_deviation < 0.05,
            "spread {}",
            summary.resample_standard_deviation
        );
        assert!(summary.percentile_lower < result.point_estimate);
        assert!(summary.percentile_upper > result.point_estimate);
    }

    #[test]
    fn bootstrap_is_deterministic_with_same_seed() {
        let data: Vec<f64> = (0..100).map(|i| i as f64 * 0.1).collect();
        let cfg = BootstrapConfig {
            n_boot: 50,
            block_size: 10,
            seed: 99,
            alpha: 0.05,
            validity: independent_validity(),
        };
        let stat = |s: &[f64]| s.iter().sum::<f64>() / s.len() as f64;
        let a = run_bootstrap(&data, &cfg, stat).unwrap();
        let b = run_bootstrap(&data, &cfg, stat).unwrap();
        assert_eq!(a.summary, b.summary);
        assert_eq!(complete_values(&a), complete_values(&b));
    }

    #[test]
    fn bootstrap_different_seeds_give_different_resamples() {
        let data: Vec<f64> = (0..100).map(|i| i as f64 * 0.1).collect();
        let stat = |s: &[f64]| s.iter().sum::<f64>() / s.len() as f64;
        let a = block_bootstrap(
            &data,
            &BootstrapConfig {
                n_boot: 50,
                block_size: 10,
                seed: 1,
                alpha: 0.05,
                validity: independent_validity(),
            },
            CALLBACK,
            |values| Ok(stat(values)),
        )
        .unwrap();
        let b = block_bootstrap(
            &data,
            &BootstrapConfig {
                n_boot: 50,
                block_size: 10,
                seed: 2,
                alpha: 0.05,
                validity: independent_validity(),
            },
            CALLBACK,
            |values| Ok(stat(values)),
        )
        .unwrap();
        let a_spread = a.summary.unwrap().resample_standard_deviation;
        let b_spread = b.summary.unwrap().resample_standard_deviation;
        assert!((a_spread - b_spread).abs() > 1e-12);
    }

    #[test]
    fn bootstrap_paired_preserves_length() {
        let x: Vec<f64> = (0..100).map(|i| i as f64).collect();
        let y: Vec<f64> = x.iter().map(|&v| v * 2.0).collect();
        let cfg = BootstrapConfig {
            n_boot: 50,
            block_size: 10,
            seed: 7,
            alpha: 0.1,
            validity: independent_validity(),
        };
        let result = run_paired(&x, &y, &cfg, |rx, ry| {
            // Compute Pearson correlation
            let n = rx.len() as f64;
            let mx: f64 = rx.iter().sum::<f64>() / n;
            let my: f64 = ry.iter().sum::<f64>() / n;
            let cov: f64 = rx
                .iter()
                .zip(ry)
                .map(|(a, b)| (a - mx) * (b - my))
                .sum::<f64>()
                / n;
            let sx = (rx.iter().map(|a| (a - mx).powi(2)).sum::<f64>() / n).sqrt();
            let sy = (ry.iter().map(|b| (b - my).powi(2)).sum::<f64>() / n).sqrt();
            cov / (sx * sy)
        })
        .unwrap();
        // Perfect linear relationship -> correlation = 1
        assert!(
            (result.point_estimate - 1.0).abs() < 1e-10,
            "point estimate {}",
            result.point_estimate
        );
        assert!(
            result.summary.unwrap().resample_standard_deviation < 1e-10,
            "resampling spread should be ~0 for perfect correlation"
        );
    }

    #[test]
    fn bootstrap_rejects_zero_block_size() {
        let data = vec![1.0, 2.0, 3.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 0,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        assert!(run_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_oversized_block() {
        let data = vec![1.0, 2.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 5,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };
        assert!(run_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_full_sample_block_that_would_make_every_draw_identical() {
        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: data.len(),
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        assert!(run_bootstrap(&data, &cfg, |values| values[0]).is_err());
        assert!(run_paired(&data, &data, &cfg, |x, _| x[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_out_of_range_alpha() {
        // alpha >= 1 would make the percentile lower index reach/exceed len (OOB) or invert the
        // raw percentile range; reject before indexing.
        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 1.5,
            validity: independent_validity(),
        };
        assert!(run_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_nonfinite_point_estimate() {
        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        assert!(run_bootstrap(&data, &cfg, |_| f64::NAN).is_err());
    }

    #[test]
    fn bootstrap_rejects_when_any_resample_is_nonfinite() {
        use std::sync::atomic::{AtomicUsize, Ordering};

        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let calls = AtomicUsize::new(0);
        let result = run_bootstrap(&data, &cfg, |_| {
            if calls.fetch_add(1, Ordering::Relaxed) == 2 {
                f64::NAN
            } else {
                1.0
            }
        });
        let report = result.unwrap();
        assert!(report.summary.is_none());
        assert!(report
            .replicates
            .iter()
            .any(|replicate| matches!(replicate.status, BootstrapReplicateStatus::Failed { .. })));
    }

    #[test]
    fn bootstrap_requires_two_resamples_for_a_sample_spread() {
        let config = BootstrapConfig {
            n_boot: 1,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        assert!(run_bootstrap(&[1.0, 2.0], &config, |values| values[0]).is_err());
    }

    #[test]
    fn bootstrap_paired_rejects_mismatched_lengths() {
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        assert!(run_paired(&[1.0, 2.0], &[1.0], &cfg, |_, _| 0.0).is_err());
    }

    #[test]
    fn block_bootstrap_rejects_unallocatable_resample_count_without_panicking() {
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let outcome =
            std::panic::catch_unwind(|| run_bootstrap(&[1.0, 2.0], &config, |values| values[0]));

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }

    #[test]
    fn block_bootstrap_paired_rejects_unallocatable_resample_count_without_panicking() {
        let config = BootstrapConfig {
            n_boot: usize::MAX,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
            validity: independent_validity(),
        };

        let outcome =
            std::panic::catch_unwind(|| run_paired(&[1.0, 2.0], &[2.0, 4.0], &config, |x, _| x[0]));

        assert!(matches!(
            outcome,
            Ok(Err(PidError::ResourceLimitExceeded { .. }))
        ));
    }
}
