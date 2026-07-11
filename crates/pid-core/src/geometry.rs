use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::preprocess::SplitMix64;
use crate::stats::finite_mean;

#[derive(Debug, Clone)]
pub struct DistanceConcentrationConfig {
    pub metric: Metric,
}

impl Default for DistanceConcentrationConfig {
    fn default() -> Self {
        Self {
            metric: Metric::Chebyshev,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct DistanceConcentrationStats {
    /// Count of pairwise distances (n*(n-1)/2).
    pub pairwise_count: u64,
    pub pairwise_min: f64,
    pub pairwise_max: f64,
    pub pairwise_mean: f64,
    pub pairwise_std: f64,
    /// Coefficient of variation (unitless), evaluated before rescaling the moments so it remains
    /// informative even when the individually rounded mean or standard deviation is subnormal.
    pub pairwise_cv: f64,

    /// Per-point nearest-neighbor distance summary.
    pub nn_min: f64,
    pub nn_max: f64,
    pub nn_mean: f64,
    pub nn_std: f64,
    pub nn_cv: f64,

    /// Ratio of mean nearest-neighbor distance to mean pairwise distance.
    /// The ratio is evaluated before restoring either distance scale, avoiding subnormal
    /// underflow in this dimensionless summary.
    ///
    /// In high dimension with distance concentration (Beyer et al. 1999-type conditions —
    /// a diagnostic tendency, not an unconditional theorem), this ratio tends to approach 1.
    pub nn_over_pairwise_mean: f64,
}

#[derive(Clone, Copy, Debug)]
struct RunningMoments {
    n: u64,
    scale: f64,
    mean: f64,
    m2: f64,
}

impl RunningMoments {
    fn new() -> Self {
        Self {
            n: 0,
            scale: 0.0,
            mean: 0.0,
            m2: 0.0,
        }
    }

    fn update(&mut self, x: f64) -> bool {
        if !x.is_finite() {
            return false;
        }
        let Some(next_n) = self.n.checked_add(1) else {
            return false;
        };
        let magnitude = x.abs();
        if magnitude > self.scale {
            let ratio = if self.scale == 0.0 {
                0.0
            } else {
                self.scale / magnitude
            };
            self.mean *= ratio;
            self.m2 *= ratio * ratio;
            self.scale = magnitude;
        }
        let scaled = if self.scale == 0.0 {
            0.0
        } else {
            x / self.scale
        };
        let delta = scaled - self.mean;
        let next_mean = self.mean + delta / (next_n as f64);
        let delta2 = scaled - next_mean;
        let next_m2 = self.m2 + delta * delta2;
        if !next_mean.is_finite() || !next_m2.is_finite() {
            return false;
        }
        self.n = next_n;
        self.mean = next_mean;
        self.m2 = next_m2;
        true
    }

    fn mean(&self) -> f64 {
        self.scale * self.mean
    }

    fn std_population(&self) -> f64 {
        if self.n == 0 {
            return f64::NAN;
        }
        self.scale * (self.m2 / (self.n as f64)).sqrt()
    }

    fn cv_population(&self) -> f64 {
        if self.n == 0 || self.mean <= 0.0 || self.m2 < 0.0 {
            return f64::NAN;
        }
        (self.m2 / self.n as f64).sqrt() / self.mean
    }

    fn standard_error_of_mean(&self, context: &'static str) -> PidResult<Option<f64>> {
        if self.n == 0 {
            return Err(PidError::NumericalInstability { context });
        }
        if self.n == 1 {
            return Ok(None);
        }
        // Observations are scaled into [-1, 1], so Welford's aggregate roundoff grows with the
        // number of bounded updates. In raw units this tolerance scales by `self.scale²`.
        let negative_roundoff_tolerance = 64.0 * f64::EPSILON * self.n as f64;
        if !self.m2.is_finite() || self.m2 < -negative_roundoff_tolerance {
            return Err(PidError::NumericalInstability { context });
        }
        let scaled_standard_error =
            (self.m2.max(0.0) / (self.n - 1) as f64).sqrt() / (self.n as f64).sqrt();
        let standard_error = self.scale * scaled_standard_error;
        if standard_error.is_finite() {
            Ok(Some(standard_error))
        } else {
            Err(PidError::NumericalInstability { context })
        }
    }

    fn mean_ratio(&self, denominator: &Self) -> f64 {
        if self.scale <= 0.0
            || self.mean <= 0.0
            || denominator.scale <= 0.0
            || denominator.mean <= 0.0
        {
            return f64::NAN;
        }
        (self.scale / denominator.scale) * (self.mean / denominator.mean)
    }
}

/// Distance concentration diagnostics for kNN validity checks.
///
/// This function computes simple, robust proxies that indicate whether distances are
/// becoming “nearly equal” (a common failure mode for kNN methods in high dimension):
/// - coefficient of variation of all pairwise distances (`pairwise_cv = std/mean`)
/// - ratio of mean nearest-neighbor distance to mean pairwise distance (`nn_over_pairwise_mean`)
///
/// Notes:
/// - This is a **diagnostic**, not a guarantee.
/// - Non-finite inputs (NaN/Inf) are rejected.
/// - Some duplicate points are allowed (the minimum distance can be 0), but the nearest-neighbor
///   summary is rejected if every point has a zero-distance duplicate. Jitter changes the
///   estimated distribution: use it only under an explicit observation-noise model or in a
///   reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or
///   mixed-support method.
/// - This implementation is brute-force O(n²) and intended for Experiment-0-scale diagnostics.
pub fn distance_concentration_stats(
    x: MatRef<'_>,
    cfg: &DistanceConcentrationConfig,
) -> PidResult<DistanceConcentrationStats> {
    let n = x.nrows();
    let d = x.ncols();
    if n < 2 || d == 0 {
        return Err(PidError::InvalidConfig {
            context: "distance_concentration_stats",
            message: "x must have at least 2 rows and 1 column",
        });
    }

    let mut pair_stats = RunningMoments::new();
    let mut pair_min = f64::INFINITY;
    let mut pair_max = 0.0f64;

    let mut nn = vec![f64::INFINITY; n];

    for i in 0..n {
        let xi = x.row(i);
        for j in (i + 1)..n {
            let dist = cfg.metric.distance(xi, x.row(j));
            if !dist.is_finite() || dist < 0.0 {
                return Err(PidError::NumericalInstability {
                    context: "distance_concentration_stats: non-finite or negative distance",
                });
            }
            if dist < pair_min {
                pair_min = dist;
            }
            if dist > pair_max {
                pair_max = dist;
            }
            if !pair_stats.update(dist) {
                return Err(PidError::NumericalInstability {
                    context: "distance_concentration_stats: pairwise moments overflow",
                });
            }

            if dist < nn[i] {
                nn[i] = dist;
            }
            if dist < nn[j] {
                nn[j] = dist;
            }
        }
    }

    let pairwise_mean = pair_stats.mean();
    if !pairwise_mean.is_finite() || pairwise_mean <= 0.0 {
        return Err(PidError::NumericalInstability {
            context: "distance_concentration_stats: non-positive mean distance (degenerate data)",
        });
    }
    let pairwise_std = pair_stats.std_population();
    // Keep the unitless ratio in scaled coordinates. Rescaling the two moments first can round a
    // representable coefficient of variation to zero for subnormal distances.
    let pairwise_cv = pair_stats.cv_population();
    if !pairwise_std.is_finite() || !pairwise_cv.is_finite() {
        return Err(PidError::NumericalInstability {
            context: "distance_concentration_stats: non-finite pairwise summary",
        });
    }

    let mut nn_stats = RunningMoments::new();
    let mut nn_min = f64::INFINITY;
    let mut nn_max = 0.0f64;
    for &dnn in &nn {
        if !dnn.is_finite() || dnn < 0.0 {
            return Err(PidError::NumericalInstability {
                context:
                    "distance_concentration_stats: non-finite or negative nearest-neighbor distance",
            });
        }
        if dnn < nn_min {
            nn_min = dnn;
        }
        if dnn > nn_max {
            nn_max = dnn;
        }
        if !nn_stats.update(dnn) {
            return Err(PidError::NumericalInstability {
                context: "distance_concentration_stats: nearest-neighbor moments overflow",
            });
        }
    }

    let nn_mean = nn_stats.mean();
    if !nn_mean.is_finite() || nn_mean <= 0.0 {
        return Err(PidError::NumericalInstability {
            context: "distance_concentration_stats: non-positive nearest-neighbor mean distance (degenerate data)",
        });
    }
    let nn_std = nn_stats.std_population();
    let nn_cv = nn_stats.cv_population();
    let nn_over_pairwise_mean = nn_stats.mean_ratio(&pair_stats);
    if !nn_std.is_finite() || !nn_cv.is_finite() || !nn_over_pairwise_mean.is_finite() {
        return Err(PidError::NumericalInstability {
            context: "distance_concentration_stats: non-finite nearest-neighbor summary",
        });
    }

    Ok(DistanceConcentrationStats {
        pairwise_count: pair_stats.n,
        pairwise_min: pair_min,
        pairwise_max: pair_max,
        pairwise_mean,
        pairwise_std,
        pairwise_cv,
        nn_min,
        nn_max,
        nn_mean,
        nn_std,
        nn_cv,
        nn_over_pairwise_mean,
    })
}

#[derive(Debug, Clone)]
pub struct IntrinsicDimConfig {
    /// Number of nearest neighbors to use for the Levina–Bickel MLE-style estimator.
    ///
    /// Requirements: `k >= 3` (the MacKay–Ghahramani `k-2` normalisation needs it) and `n > k`.
    pub k: usize,
    pub metric: Metric,
}

impl Default for IntrinsicDimConfig {
    fn default() -> Self {
        Self {
            k: 10,
            metric: Metric::Chebyshev,
        }
    }
}

/// Estimate intrinsic dimension using a nearest-neighbor MLE-style estimator (Levina–Bickel).
///
/// This is a **diagnostic**, not a guarantee: it is useful for deciding whether kNN-based MI/PID
/// is even plausible at a given operating point.
///
/// For each sample `i`, let `T_j(i)` be the distance from `x_i` to its `j`-th nearest neighbor
/// (excluding itself) under `cfg.metric`, and let `k = cfg.k`. The pointwise estimate is:
///
/// `m_i = ( (1/(k-2)) * Σ_{j=1..k-1} ln( T_k(i) / T_j(i) ) )^{-1}`
///
/// and the returned estimate is the mean of `m_i` over all samples.
///
/// The `1/(k-2)` normalisation is the MacKay–Ghahramani bias correction ("Comments on 'Maximum
/// Likelihood Estimation of Intrinsic Dimension'", 2005): under Levina–Bickel's own Poisson
/// approximation, `Σ_{j<k} ln(T_k/T_j) ~ Gamma(k-1, m)`, so the original `(k-1)/Σ` pointwise
/// estimator has mean `m·(k-1)/(k-2)` (+12.5% bias at the default `k = 10`); dividing by `k-2`
/// makes each `m_i` unbiased. This matches standard implementations (e.g. scikit-dimension).
///
/// Notes:
/// - Duplicate points (zero distances) make the estimator ill-posed. Jitter changes the estimated
///   distribution: use it only under an explicit observation-noise model or in a reported
///   noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support
///   method.
/// - This implementation is brute-force O(n²) and intended for Experiment-0-scale diagnostics.
pub fn intrinsic_dimension_levina_bickel(
    x: MatRef<'_>,
    cfg: &IntrinsicDimConfig,
) -> PidResult<f64> {
    let n = x.nrows();
    let d = x.ncols();
    if n == 0 || d == 0 {
        return Err(PidError::InvalidConfig {
            context: "intrinsic_dimension_levina_bickel",
            message: "x must be non-empty (n,d >= 1)",
        });
    }

    let k = cfg.k;
    if k < 3 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let kth = k - 1;
    let mut scratch = Vec::with_capacity(n.saturating_sub(1));
    let mut local_estimates = Vec::with_capacity(n);
    for i in 0..n {
        scratch.clear();
        let xi = x.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            // `checked_distance` turns a NaN distance (e.g. an off-hyperboloid point under
            // `Metric::HyperbolicLorentz`) into an explicit error, matching `symmetric_distances`
            // and `sampled_four_point_delta_summary`. With the plain `distance`, `total_cmp`
            // would sort NaN as the largest value, so it would silently never enter the kNN and a
            // plausible-looking intrinsic dimension would be returned for invalid input.
            scratch.push(cfg.metric.checked_distance(
                xi,
                x.row(j),
                "intrinsic_dimension_levina_bickel: distance",
            )?);
        }

        scratch.select_nth_unstable_by(kth, |a, b| a.total_cmp(b));
        // The k smallest distances are in scratch[..k] (unordered).
        scratch[..k].sort_by(|a, b| a.total_cmp(b));
        let tk = scratch[kth];
        if tk <= 0.0 || !tk.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "intrinsic_dimension_levina_bickel: kNN radius is non-positive; duplicates require a discrete/quantized/mixed-support method unless jitter is an explicit observation-noise model or reported noise-scale sensitivity analysis",
            });
        }

        let mut s = 0.0f64;
        for &tj in &scratch[..kth] {
            if tj <= 0.0 || !tj.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "intrinsic_dimension_levina_bickel: neighbor distance is non-positive; duplicates require a discrete/quantized/mixed-support method unless jitter is an explicit observation-noise model or reported noise-scale sensitivity analysis",
                });
            }
            s += stable_log_ratio(tk, tj);
        }

        // MacKay–Ghahramani correction: normalise by k-2 (= kth-1), not k-1 (see doc comment).
        let denom = s / ((kth - 1) as f64);
        if denom <= 0.0 || !denom.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "intrinsic_dimension_levina_bickel: non-positive mean log distance ratio",
            });
        }

        local_estimates.push(1.0 / denom);
    }

    finite_mean(
        &local_estimates,
        "intrinsic_dimension_levina_bickel: mean local estimate overflow",
    )
}

/// Evaluate `ln(upper / lower)` for finite `upper >= lower > 0` without overflowing the ratio or
/// losing an adjacent-float separation when the two logarithms round to the same value.
fn stable_log_ratio(upper: f64, lower: f64) -> f64 {
    debug_assert!(upper.is_finite() && lower.is_finite());
    debug_assert!(upper >= lower && lower > 0.0);
    let relative_difference = (upper - lower) / lower;
    if relative_difference.is_finite() && relative_difference <= 0.5 {
        relative_difference.ln_1p()
    } else {
        upper.ln() - lower.ln()
    }
}

#[derive(Debug, Clone)]
pub struct HyperbolicityConfig {
    /// Number of 4-point tuples to sample for the four-point-delta summary.
    pub n_samples: usize,
    pub metric: Metric,
    /// Seed for the internal deterministic PRNG used to draw distinct 4-point tuples.
    /// Sampling is fully deterministic for a fixed `(seed, n, n_samples)`: the same
    /// seed reproduces the same quadruples (no `rand` dependency, no system entropy).
    pub seed: u64,
}

/// Descriptive statistics for sampled four-point deltas.
///
/// These are Monte Carlo summaries of the finite dataset, not an estimate of the defining
/// sup-over-all-quadruples Gromov hyperbolicity constant. In particular, `max` is only the
/// largest delta among the sampled quadruples.
///
/// The normalized fields use the common `2 * delta / diameter` convention. They are `None` for
/// a zero-diameter dataset, where that ratio is undefined. `monte_carlo_standard_error` and its
/// normalized counterpart are `None` when only one quadruple was sampled because a sample
/// variance cannot then be estimated.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SampledFourPointDeltaSummary {
    /// Number of independently drawn quadruples summarized.
    pub sample_count: u64,
    /// Arithmetic mean of the sampled deltas.
    pub mean: f64,
    /// Empirical median (linearly interpolated between adjacent order statistics).
    pub median: f64,
    /// Empirical 90th percentile (linearly interpolated).
    pub p90: f64,
    /// Empirical 99th percentile (linearly interpolated).
    pub p99: f64,
    /// Largest sampled delta. This is not the supremum over all quadruples.
    pub max: f64,
    /// Standard error of `mean` under the configured with-replacement quadruple sampler.
    pub monte_carlo_standard_error: Option<f64>,
    /// Exact maximum pairwise distance in the finite dataset under `HyperbolicityConfig::metric`.
    pub diameter: f64,
    /// `2 * mean / diameter`, or `None` when `diameter == 0`.
    pub normalized_mean: Option<f64>,
    /// `2 * median / diameter`, or `None` when `diameter == 0`.
    pub normalized_median: Option<f64>,
    /// `2 * p90 / diameter`, or `None` when `diameter == 0`.
    pub normalized_p90: Option<f64>,
    /// `2 * p99 / diameter`, or `None` when `diameter == 0`.
    pub normalized_p99: Option<f64>,
    /// `2 * max / diameter`, or `None` when `diameter == 0`.
    pub normalized_max: Option<f64>,
    /// Normalized Monte Carlo standard error, when both source quantities are defined.
    pub normalized_monte_carlo_standard_error: Option<f64>,
}

impl Default for HyperbolicityConfig {
    fn default() -> Self {
        Self {
            n_samples: 1000,
            metric: Metric::Chebyshev, // Standard metric; Euclidean would be natural for hyperbolicity but is not implemented
            seed: 42,
        }
    }
}

#[derive(Clone, Copy)]
struct ExactPairSum {
    rounded: f64,
    error: f64,
}

fn exact_pair_sum(left: f64, right: f64) -> ExactPairSum {
    let rounded = left + right;
    let right_virtual = rounded - left;
    let error = (left - (rounded - right_virtual)) + (right - right_virtual);
    ExactPairSum { rounded, error }
}

fn pair_sum_difference(left: ExactPairSum, right: ExactPairSum) -> f64 {
    let values = [left.rounded, -right.rounded, left.error, -right.error];
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        correction += if sum.abs() >= value.abs() {
            (sum - next) + value
        } else {
            (value - next) + sum
        };
        sum = next;
    }
    sum + correction
}

fn compare_pair_sums(left: ExactPairSum, right: ExactPairSum) -> std::cmp::Ordering {
    let difference = pair_sum_difference(left, right);
    if difference < 0.0 {
        std::cmp::Ordering::Less
    } else if difference > 0.0 {
        std::cmp::Ordering::Greater
    } else {
        std::cmp::Ordering::Equal
    }
}

fn power_of_two_scale(value: f64) -> f64 {
    debug_assert!(value.is_finite() && value > 0.0);
    let exponent = (value.to_bits() >> 52) & 0x7ff;
    if exponent == 0 {
        f64::from_bits(1)
    } else {
        f64::from_bits(exponent << 52)
    }
}

/// Summarize four-point deltas from deterministically sampled quadruples.
///
/// The 4-point condition states that for any four points x, y, z, w:
/// (x.y)_w >= min((x.z)_w, (y.z)_w) - delta
///
/// where (x.y)_w is the Gromov product with respect to base point w:
/// (x.y)_w = 0.5 * (d(x,w) + d(y,w) - d(x,y))
///
/// Equivalently, per quadruple (ordered by sums of opposite-pair distances),
/// delta_quad = (L - M) / 2, where L is the largest sum of pairs and M is the medium sum.
///
/// The defining Gromov delta-hyperbolicity constant is the *supremum* of `delta_quad` over all
/// quadruples. This function instead reports descriptive statistics for a configured Monte Carlo
/// sample. Its `max` is therefore only a sampled lower bound on the finite dataset's supremum;
/// the mean and quantiles are distributional diagnostics, not estimators of that supremum.
///
/// The dataset diameter is computed exactly in `O(n²)` distance evaluations. Sampling remains
/// fully deterministic for a fixed configuration. Percentiles use linear interpolation between
/// adjacent empirical order statistics, and the Monte Carlo standard error uses the usual sample
/// variance of the with-replacement quadruple draws.
pub fn sampled_four_point_delta_summary(
    x: MatRef<'_>,
    cfg: &HyperbolicityConfig,
) -> PidResult<SampledFourPointDeltaSummary> {
    let n = x.nrows();
    let d = x.ncols();
    if n < 4 {
        return Err(PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "need at least 4 points to sample four-point deltas",
        });
    }
    if d == 0 {
        return Err(PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "x must have at least 1 column",
        });
    }
    if cfg.n_samples == 0 {
        return Err(PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "n_samples must be > 0",
        });
    }
    let mut deltas = Vec::new();
    deltas
        .try_reserve_exact(cfg.n_samples)
        .map_err(|_| PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "n_samples is too large to allocate the sampled-delta buffer",
        })?;

    // Sampling must not make input validity seed-dependent. In particular, a finite row that is
    // off the unit hyperboloid can otherwise be omitted from every sampled quadruple and yield a
    // plausible `Ok` diagnostic. A checked self-distance validates each row once without changing
    // the sampled estimator.
    for i in 0..n {
        cfg.metric.checked_distance(
            x.row(i),
            x.row(i),
            "sampled_four_point_delta_summary: invalid input row",
        )?;
    }

    let mut diameter = 0.0_f64;
    for i in 0..n {
        for j in (i + 1)..n {
            let distance = cfg.metric.checked_distance(
                x.row(i),
                x.row(j),
                "sampled_four_point_delta_summary: diameter distance",
            )?;
            diameter = diameter.max(distance);
        }
    }

    let mut rng = SplitMix64::new(cfg.seed ^ 0xcafe_f00d_d15e_a5e5);
    let mut delta_moments = RunningMoments::new();
    // Preserve the historical scalar API's deterministic online-mean recurrence exactly. The
    // scaled moments accumulator is kept separately for a robust Monte Carlo standard error.
    let mut mean_delta = 0.0_f64;

    for _ in 0..cfg.n_samples {
        let [i, j, k, l] = sample_four_distinct(&mut rng, n);

        let pi = x.row(i);
        let pj = x.row(j);
        let pk = x.row(k);
        let pl = x.row(l);

        // Compute the 3 pair sums
        // S1 = d(i,j) + d(k,l)
        // S2 = d(i,k) + d(j,l)
        // S3 = d(i,l) + d(j,k)
        // Use `checked_distance` so a non-finite distance (e.g. an off-hyperboloid point under
        // `Metric::HyperbolicLorentz`) becomes an explicit error rather than silently propagating
        // to `Ok(NaN)`.
        let ctx = "sampled_four_point_delta_summary: quadruple distance";
        let dij = cfg.metric.checked_distance(pi, pj, ctx)?;
        let dkl = cfg.metric.checked_distance(pk, pl, ctx)?;
        let dik = cfg.metric.checked_distance(pi, pk, ctx)?;
        let djl = cfg.metric.checked_distance(pj, pl, ctx)?;
        let dil = cfg.metric.checked_distance(pi, pl, ctx)?;
        let djk = cfg.metric.checked_distance(pj, pk, ctx)?;

        // A raw pair sum can overflow even when `(L-M)/2` is representable. Scale by an exact
        // power of two, then retain each two-term sum's roundoff residual. This reports every
        // positive difference present in the represented metric without an absolute epsilon clamp.
        let distances = [dij, dkl, dik, djl, dil, djk];
        let max_distance = distances.into_iter().fold(0.0_f64, f64::max);
        let delta_local = if max_distance == 0.0 {
            0.0
        } else {
            let distance_scale = power_of_two_scale(max_distance);
            let mut normalized = [0.0; 6];
            for (slot, distance) in normalized.iter_mut().zip(distances) {
                *slot = distance / distance_scale;
                if distance > 0.0 && *slot == 0.0 {
                    return Err(PidError::NumericalInstability {
                        context:
                            "sampled_four_point_delta_summary: distance dynamic range is not representable",
                    });
                }
            }
            let mut sums = [
                exact_pair_sum(normalized[0], normalized[1]),
                exact_pair_sum(normalized[2], normalized[3]),
                exact_pair_sum(normalized[4], normalized[5]),
            ];
            sums.sort_by(|left, right| compare_pair_sums(*right, *left));
            let difference = pair_sum_difference(sums[0], sums[1]);
            if !difference.is_finite() || difference < 0.0 {
                return Err(PidError::NumericalInstability {
                    context: "sampled_four_point_delta_summary: non-finite quadruple delta",
                });
            }
            // Choose the multiplication order so neither a subnormal normalized difference nor a
            // subnormal distance scale is halved before the other factor can restore a
            // representable raw delta.
            let delta = if distance_scale >= 2.0 {
                difference * (distance_scale * 0.5)
            } else {
                (difference * distance_scale) * 0.5
            };
            if !delta.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "sampled_four_point_delta_summary: quadruple delta overflow",
                });
            }
            delta
        };
        if !delta_moments.update(delta_local) {
            return Err(PidError::NumericalInstability {
                context: "sampled_four_point_delta_summary: delta moments overflow",
            });
        }
        mean_delta += (delta_local - mean_delta) / delta_moments.n as f64;
        if !mean_delta.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "sampled_four_point_delta_summary: mean delta overflow",
            });
        }
        deltas.push(delta_local);
    }

    if deltas.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "sampled_four_point_delta_summary",
            message: "failed to sample a valid quadruple",
        });
    }

    deltas.sort_by(f64::total_cmp);
    let mean = mean_delta;
    let median = linear_quantile(&deltas, 0.5);
    let p90 = linear_quantile(&deltas, 0.9);
    let p99 = linear_quantile(&deltas, 0.99);
    let max = *deltas.last().expect("non-empty deltas checked above");
    let monte_carlo_standard_error = delta_moments
        .standard_error_of_mean("sampled_four_point_delta_summary: invalid Monte Carlo variance")?;
    let normalized = |value| normalized_four_point_delta(value, diameter);

    Ok(SampledFourPointDeltaSummary {
        sample_count: delta_moments.n,
        mean,
        median,
        p90,
        p99,
        max,
        monte_carlo_standard_error,
        diameter,
        normalized_mean: normalized(mean),
        normalized_median: normalized(median),
        normalized_p90: normalized(p90),
        normalized_p99: normalized(p99),
        normalized_max: normalized(max),
        normalized_monte_carlo_standard_error: monte_carlo_standard_error.and_then(normalized),
    })
}

/// Compatibility wrapper returning the mean sampled four-point delta.
///
/// This function does **not** compute the sup-defined Gromov hyperbolicity constant. Use
/// [`sampled_four_point_delta_summary`] for accurately named mean, quantile, sampled-maximum,
/// diameter-normalized, and Monte Carlo uncertainty diagnostics.
#[deprecated(
    since = "0.5.0",
    note = "use sampled_four_point_delta_summary; this returns only its sampled mean, not the Gromov supremum"
)]
pub fn gromov_hyperbolicity(x: MatRef<'_>, cfg: &HyperbolicityConfig) -> PidResult<f64> {
    sampled_four_point_delta_summary(x, cfg).map(|summary| summary.mean)
}

fn linear_quantile(sorted: &[f64], probability: f64) -> f64 {
    debug_assert!(!sorted.is_empty());
    debug_assert!((0.0..=1.0).contains(&probability));
    let rank = probability * (sorted.len() - 1) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;
    let fraction = rank - lower as f64;
    sorted[lower] + fraction * (sorted[upper] - sorted[lower])
}

fn normalized_four_point_delta(delta: f64, diameter: f64) -> Option<f64> {
    if diameter == 0.0 {
        return None;
    }
    debug_assert!(delta.is_finite() && delta >= 0.0);
    debug_assert!(diameter.is_finite() && diameter > 0.0);
    let normalized = if delta <= f64::MAX / 2.0 {
        (2.0 * delta) / diameter
    } else {
        (delta / diameter) * 2.0
    };
    debug_assert!(normalized.is_finite());
    Some(normalized)
}

fn sample_four_distinct(rng: &mut SplitMix64, n: usize) -> [usize; 4] {
    let mut selected = [0usize; 4];
    for slot in 0..4 {
        let rank = uniform_index(rng, n - slot);
        let mut candidate = rank;
        // Interpret the draw as a rank among unselected indices. This fixed point preserves the
        // historical rank mapping without allocating and sorting an exclusion vector per draw.
        loop {
            let next = rank
                + selected[..slot]
                    .iter()
                    .filter(|&&index| index <= candidate)
                    .count();
            if next == candidate {
                break;
            }
            candidate = next;
        }
        debug_assert!(candidate < n);
        debug_assert!(!selected[..slot].contains(&candidate));
        selected[slot] = candidate;
    }
    selected
}

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

#[cfg(test)]
mod tests {
    use super::{
        sample_four_distinct, sampled_four_point_delta_summary, stable_log_ratio,
        HyperbolicityConfig, RunningMoments, SplitMix64,
    };
    use crate::error::PidError;
    use crate::matrix::MatRef;
    use crate::metric::Metric;

    #[test]
    fn stable_log_ratio_retains_adjacent_large_floats() {
        let upper = 1.0e300_f64;
        let lower = f64::from_bits(upper.to_bits() - 1);
        assert_eq!(upper.ln(), lower.ln());

        let ratio_log = stable_log_ratio(upper, lower);

        assert!(ratio_log.is_finite() && ratio_log > 0.0);
    }

    #[test]
    fn standard_error_is_none_for_exactly_one_sample() {
        let moments = RunningMoments {
            n: 1,
            scale: 2.0,
            mean: 0.5,
            m2: 0.0,
        };

        assert_eq!(moments.standard_error_of_mean("test").unwrap(), None);
    }

    #[test]
    fn standard_error_clamps_tiny_negative_roundoff_for_multiple_samples() {
        let moments = RunningMoments {
            n: 2,
            scale: 2.0,
            mean: 0.5,
            m2: -64.0 * f64::EPSILON,
        };

        assert_eq!(moments.standard_error_of_mean("test").unwrap(), Some(0.0));
    }

    #[test]
    fn standard_error_rejects_materially_negative_variance() {
        let moments = RunningMoments {
            n: 2,
            scale: 2.0,
            mean: 0.5,
            m2: -1.0e-6,
        };

        assert!(matches!(
            moments.standard_error_of_mean("test"),
            Err(PidError::NumericalInstability { context: "test" })
        ));
    }

    #[test]
    fn sampled_four_point_delta_rejects_zero_column_input() {
        let matrix = MatRef::new(&[], 4, 0).unwrap();

        assert!(matches!(
            sampled_four_point_delta_summary(matrix, &HyperbolicityConfig::default()),
            Err(PidError::InvalidConfig { .. })
        ));
    }

    #[test]
    fn sampled_four_point_delta_rejects_unallocatable_sample_count() {
        let data = [0.0, 1.0, 2.0, 3.0];
        let matrix = MatRef::new(&data, 4, 1).unwrap();
        let config = HyperbolicityConfig {
            n_samples: usize::MAX,
            metric: Metric::Chebyshev,
            seed: 42,
        };

        assert!(matches!(
            sampled_four_point_delta_summary(matrix, &config),
            Err(PidError::InvalidConfig {
                context: "sampled_four_point_delta_summary",
                message: "n_samples is too large to allocate the sampled-delta buffer",
            })
        ));
    }

    #[test]
    fn distinct_sampler_preserves_historical_seeded_quadruple() {
        let mut rng = SplitMix64::new(42 ^ 0xcafe_f00d_d15e_a5e5);

        assert_eq!(sample_four_distinct(&mut rng, 5), [2, 1, 3, 4]);
    }

    #[test]
    fn sampled_four_point_delta_prevalidates_hyperbolic_rows_that_sampling_would_omit() {
        let mut data = vec![2.0, 0.0]; // Finite, but off the unit hyperboloid.
        for rapidity in [0.0_f64, 0.2, 0.4, 0.6] {
            data.push(rapidity.cosh());
            data.push(rapidity.sinh());
        }
        let matrix = MatRef::new(&data, 5, 2).unwrap();
        let config = HyperbolicityConfig {
            n_samples: 1,
            metric: Metric::HyperbolicLorentz,
            seed: 42,
        };

        // This seed's sole quadruple is [2,1,3,4], so the old sampled-only validation omitted row 0.
        assert!(matches!(
            sampled_four_point_delta_summary(matrix, &config),
            Err(PidError::NonFiniteInput { .. })
        ));
    }

    #[test]
    fn sampled_four_point_delta_rescales_before_halving_a_subnormal_normalized_delta() {
        let diameter = 2.0_f64.powi(1023);
        let epsilon = 2.0_f64.powi(-51);
        // Frechet's L-infinity embedding of the four-point metric with distances
        // d(1,{2,3,4})=D, d(2,3)=d(2,4)=e, d(3,4)=2e. Its opposite-pair sums are
        // D+2e, D+e, D+e, hence delta=e/2. Normalizing by D makes their difference the
        // smallest positive subnormal, which must be rescaled before division by two.
        let data = [
            0.0,
            diameter,
            diameter,
            diameter,
            diameter,
            0.0,
            epsilon,
            epsilon,
            diameter,
            epsilon,
            0.0,
            2.0 * epsilon,
            diameter,
            epsilon,
            2.0 * epsilon,
            0.0,
        ];
        let matrix = MatRef::new(&data, 4, 4).unwrap();
        let config = HyperbolicityConfig {
            n_samples: 1,
            metric: Metric::Chebyshev,
            seed: 0,
        };

        let summary = sampled_four_point_delta_summary(matrix, &config).unwrap();

        assert_eq!(summary.mean, 2.0_f64.powi(-52));
        assert_eq!(summary.max, summary.mean);
        assert_eq!(summary.sample_count, 1);
        assert_eq!(summary.monte_carlo_standard_error, None);
    }
}
