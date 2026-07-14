use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::ksg::{value_quantiles, KsgValueQuantiles};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::{kth_neighbor_shell_counts, validate_kth_neighbor_shell};
use crate::preprocess::SplitMix64;
use crate::report::{ScientificStatus, WarningCode};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_filled, try_vec_with_capacity,
    CancellationProgress, CancellationToken, ResourceBudget, ResourceEstimate,
};
use crate::stats::finite_mean;

#[derive(Debug, Clone)]
#[non_exhaustive]
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

impl DistanceConcentrationConfig {
    pub const fn with_metric(mut self, metric: Metric) -> Self {
        self.metric = metric;
        self
    }
}

#[derive(Debug, Clone, Copy)]
#[non_exhaustive]
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
    distance_concentration_stats_with_budget(x, cfg, ResourceBudget::default())
}

/// Preflight memory and pairwise work for [`distance_concentration_stats`].
pub fn distance_concentration_resource_estimate(x: MatRef<'_>) -> PidResult<ResourceEstimate> {
    let n = x.nrows() as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "distance_concentration_stats",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: n.checked_mul(std::mem::size_of::<f64>() as u128).ok_or(
            PidError::SizeOverflow {
                operation: "distance_concentration_stats",
            },
        )?,
        pairwise_distances: pairs,
        operations_hint: pairs
            .checked_mul(
                (x.ncols() as u128)
                    .checked_add(8)
                    .ok_or(PidError::SizeOverflow {
                        operation: "distance_concentration_stats",
                    })?,
            )
            .ok_or(PidError::SizeOverflow {
                operation: "distance_concentration_stats",
            })?,
    })
}

/// Distance-concentration diagnostics with a caller-supplied resource ceiling.
pub fn distance_concentration_stats_with_budget(
    x: MatRef<'_>,
    cfg: &DistanceConcentrationConfig,
    budget: ResourceBudget,
) -> PidResult<DistanceConcentrationStats> {
    let cancellation = CancellationToken::new();
    distance_concentration_stats_with_budget_and_cancellation(x, cfg, budget, &cancellation)
}

/// Distance-concentration diagnostics with resource and cooperative-cancellation controls.
pub fn distance_concentration_stats_with_budget_and_cancellation(
    x: MatRef<'_>,
    cfg: &DistanceConcentrationConfig,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<DistanceConcentrationStats> {
    let n = x.nrows();
    let d = x.ncols();
    if n < 2 || d == 0 {
        return Err(PidError::InvalidConfig {
            context: "distance_concentration_stats",
            message: "x must have at least 2 rows and 1 column",
        });
    }
    budget.check(
        "distance_concentration_stats",
        distance_concentration_resource_estimate(x)?,
    )?;
    let total_pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "distance_concentration_stats",
        })?;
    cancellation.check("distance_concentration_stats", 0, total_pairs)?;

    let mut pair_stats = RunningMoments::new();
    let mut pair_min = f64::INFINITY;
    let mut pair_max = 0.0f64;

    let mut nn = try_vec_filled(
        "distance_concentration_stats nearest neighbors",
        n,
        f64::INFINITY,
        budget,
    )?;

    let mut completed_pairs = 0usize;
    for i in 0..n {
        let xi = x.row(i);
        for j in (i + 1)..n {
            let dist = cfg.metric.checked_distance_with_cancellation(
                xi,
                x.row(j),
                "distance_concentration_stats: pair distance",
                CancellationProgress::new(
                    "distance_concentration_stats",
                    completed_pairs,
                    total_pairs,
                ),
                cancellation,
            )?;
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
            completed_pairs += 1;
            if completed_pairs.is_multiple_of(1024) {
                cancellation.check("distance_concentration_stats", completed_pairs, total_pairs)?;
            }
        }
    }
    cancellation.check("distance_concentration_stats", completed_pairs, total_pairs)?;

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
#[non_exhaustive]
pub struct IntrinsicDimConfig {
    /// Number of nearest neighbors to use for the Levina–Bickel MLE-style estimator.
    ///
    /// Requirements: `k >= 3` (the MacKay–Ghahramani `k-2` normalisation needs it) and `n > k`.
    pub k: usize,
    pub metric: Metric,
}

/// Local and aggregate Levina--Bickel intrinsic-dimension diagnostic.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IntrinsicDimensionReport {
    pub mean: f64,
    pub local_estimates: Vec<f64>,
    pub local_estimate_quantiles: KsgValueQuantiles,
    pub kth_radius_quantiles: KsgValueQuantiles,
    pub n_samples: usize,
    pub ambient_dimension: usize,
    pub k: usize,
    pub metric: Metric,
    pub status: ScientificStatus,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub warnings: Vec<WarningCode>,
}

/// Multi-`k` intrinsic-dimension trajectory retaining every local distribution.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IntrinsicDimensionTrajectory {
    pub reports: Vec<IntrinsicDimensionReport>,
    pub aggregate_resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

impl Default for IntrinsicDimConfig {
    fn default() -> Self {
        Self {
            k: 10,
            metric: Metric::Chebyshev,
        }
    }
}

impl IntrinsicDimConfig {
    pub const fn with_k(mut self, k: usize) -> Self {
        self.k = k;
        self
    }

    pub const fn with_metric(mut self, metric: Metric) -> Self {
        self.metric = metric;
        self
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
/// - Every positive `k`-th-neighbor shell must be unique: exactly `k - 1` points must be strictly
///   inside the radius and exactly one point must lie on its boundary. Duplicate points and
///   positive-radius boundary ties make the local estimate ill-posed. Jitter changes the estimated
///   distribution: use it only under an explicit observation-noise model or in a reported
///   noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support
///   method.
/// - This implementation is brute-force O(n²) and intended for Experiment-0-scale diagnostics.
pub fn intrinsic_dimension_levina_bickel(
    x: MatRef<'_>,
    cfg: &IntrinsicDimConfig,
) -> PidResult<f64> {
    intrinsic_dimension_report(x, cfg, ResourceBudget::default()).map(|report| report.mean)
}

/// Preflight memory and pairwise work for one intrinsic-dimension report.
pub fn intrinsic_dimension_resource_estimate(x: MatRef<'_>) -> PidResult<ResourceEstimate> {
    let n = x.nrows() as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "intrinsic_dimension_report",
        })?;
    let log_n = if x.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (x.nrows() - 1).leading_zeros()) as u128
    };
    let operations_hint = pairs
        .checked_mul(2)
        .and_then(|value| {
            value.checked_mul((x.ncols() as u128).checked_add(3)?.checked_add(log_n)?)
        })
        .and_then(|value| value.checked_add(n.checked_mul(log_n)?.checked_mul(2)?))
        .ok_or(PidError::SizeOverflow {
            operation: "intrinsic_dimension_report",
        })?;
    Ok(ResourceEstimate {
        // Scratch distances, local estimates, k-th radii, and a sorted local copy coexist.
        estimated_bytes: n
            .checked_mul(4)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "intrinsic_dimension_report",
            })?,
        pairwise_distances: pairs,
        operations_hint,
    })
}

/// Return local estimates, radius distributions, scientific warnings, and resource preflight.
pub fn intrinsic_dimension_report(
    x: MatRef<'_>,
    cfg: &IntrinsicDimConfig,
    budget: ResourceBudget,
) -> PidResult<IntrinsicDimensionReport> {
    let cancellation = CancellationToken::new();
    intrinsic_dimension_report_with_cancellation(x, cfg, budget, &cancellation)
}

/// Return an intrinsic-dimension report with cooperative cancellation between distance work units.
pub fn intrinsic_dimension_report_with_cancellation(
    x: MatRef<'_>,
    cfg: &IntrinsicDimConfig,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<IntrinsicDimensionReport> {
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

    let resource_estimate = intrinsic_dimension_resource_estimate(x)?;
    budget.check("intrinsic_dimension_report", resource_estimate)?;
    let total_distances = n
        .checked_mul(n.saturating_sub(1))
        .ok_or(PidError::SizeOverflow {
            operation: "intrinsic_dimension_report",
        })?;
    cancellation.check("intrinsic_dimension_report", 0, total_distances)?;

    let kth = k - 1;
    let mut scratch =
        try_vec_with_capacity("intrinsic-dimension scratch", n.saturating_sub(1), budget)?;
    let mut local_estimates =
        try_vec_with_capacity("intrinsic-dimension local estimates", n, budget)?;
    let mut kth_radii = try_vec_with_capacity("intrinsic-dimension radii", n, budget)?;
    let mut completed_distances = 0usize;
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
            scratch.push(cfg.metric.checked_distance_with_cancellation(
                xi,
                x.row(j),
                "intrinsic_dimension_levina_bickel: distance",
                CancellationProgress::new(
                    "intrinsic_dimension_report",
                    completed_distances,
                    total_distances,
                ),
                cancellation,
            )?);
            completed_distances += 1;
            if completed_distances.is_multiple_of(1024) {
                cancellation.check(
                    "intrinsic_dimension_report",
                    completed_distances,
                    total_distances,
                )?;
            }
        }

        scratch.select_nth_unstable_by(kth, |a, b| a.total_cmp(b));
        // The k smallest distances are in scratch[..k] (unordered).
        scratch[..k].sort_unstable_by(|a, b| a.total_cmp(b));
        let tk = scratch[kth];
        if tk <= 0.0 || !tk.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "intrinsic_dimension_levina_bickel: kNN radius is non-positive; duplicates require a discrete/quantized/mixed-support method unless jitter is an explicit observation-noise model or reported noise-scale sensitivity analysis",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), tk);
        validate_kth_neighbor_shell(
            "intrinsic_dimension_levina_bickel",
            i,
            k,
            tk,
            interior_count,
            boundary_count,
        )?;
        kth_radii.push(tk);

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
    cancellation.check(
        "intrinsic_dimension_report",
        completed_distances,
        total_distances,
    )?;

    let mean = finite_mean(
        &local_estimates,
        "intrinsic_dimension_levina_bickel: mean local estimate overflow",
    )?;
    let mut sorted_local = try_vec_with_capacity(
        "intrinsic-dimension quantiles",
        local_estimates.len(),
        budget,
    )?;
    sorted_local.extend_from_slice(&local_estimates);
    sorted_local.sort_unstable_by(f64::total_cmp);
    kth_radii.sort_unstable_by(f64::total_cmp);
    Ok(IntrinsicDimensionReport {
        mean,
        local_estimate_quantiles: value_quantiles(&sorted_local)?,
        kth_radius_quantiles: value_quantiles(&kth_radii)?,
        local_estimates,
        n_samples: n,
        ambient_dimension: d,
        k,
        metric: cfg.metric,
        status: ScientificStatus::IncompleteDiagnostic,
        resource_estimate,
        resource_budget: budget,
        warnings: vec![WarningCode::DiagnosticsDoNotProvePopulationAssumptions],
    })
}

/// Evaluate intrinsic-dimension reports over several `k` values.
pub fn intrinsic_dimension_multi_k(
    x: MatRef<'_>,
    k_values: &[usize],
    metric: Metric,
    budget: ResourceBudget,
) -> PidResult<IntrinsicDimensionTrajectory> {
    if k_values.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "intrinsic_dimension_multi_k",
            message: "k_values must be nonempty",
        });
    }
    let one = intrinsic_dimension_resource_estimate(x)?;
    let count = k_values.len() as u128;
    let retained_plus_transient = count
        .checked_add(3)
        .and_then(|value| value.checked_mul(x.nrows() as u128))
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: "intrinsic_dimension_multi_k",
        })?;
    let retained_report_storage = count
        .checked_mul(
            (std::mem::size_of::<IntrinsicDimensionReport>() + std::mem::size_of::<WarningCode>())
                as u128,
        )
        .ok_or(PidError::SizeOverflow {
            operation: "intrinsic_dimension_multi_k",
        })?;
    let aggregate_resource_estimate = ResourceEstimate {
        estimated_bytes: retained_plus_transient
            .checked_add(retained_report_storage)
            .ok_or(PidError::SizeOverflow {
                operation: "intrinsic_dimension_multi_k",
            })?,
        pairwise_distances: one.pairwise_distances.checked_mul(count).ok_or(
            PidError::SizeOverflow {
                operation: "intrinsic_dimension_multi_k",
            },
        )?,
        operations_hint: one
            .operations_hint
            .checked_mul(count)
            .ok_or(PidError::SizeOverflow {
                operation: "intrinsic_dimension_multi_k",
            })?,
    };
    budget.check("intrinsic_dimension_multi_k", aggregate_resource_estimate)?;
    let mut reports =
        try_vec_with_capacity("intrinsic-dimension trajectory", k_values.len(), budget)?;
    for &k in k_values {
        reports.push(intrinsic_dimension_report(
            x,
            &IntrinsicDimConfig { k, metric },
            budget,
        )?);
    }
    Ok(IntrinsicDimensionTrajectory {
        reports,
        aggregate_resource_estimate,
        resource_budget: budget,
    })
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
#[non_exhaustive]
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
#[non_exhaustive]
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

impl HyperbolicityConfig {
    pub const fn with_n_samples(mut self, n_samples: usize) -> Self {
        self.n_samples = n_samples;
        self
    }

    pub const fn with_metric(mut self, metric: Metric) -> Self {
        self.metric = metric;
        self
    }

    pub const fn with_seed(mut self, seed: u64) -> Self {
        self.seed = seed;
        self
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
    sampled_four_point_delta_summary_with_budget(x, cfg, ResourceBudget::default())
}

/// Preflight memory and distance work for [`sampled_four_point_delta_summary`].
pub fn sampled_four_point_resource_estimate(
    x: MatRef<'_>,
    cfg: &HyperbolicityConfig,
) -> PidResult<ResourceEstimate> {
    let n = x.nrows() as u128;
    let d = x.ncols() as u128;
    let samples = cfg.n_samples as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "sampled_four_point_delta_summary",
        })?;
    let diameter_operations = pairs.checked_mul(d).ok_or(PidError::SizeOverflow {
        operation: "sampled_four_point_delta_summary",
    })?;
    let sample_operations = samples
        .checked_mul(6)
        .and_then(|value| value.checked_mul(d))
        .ok_or(PidError::SizeOverflow {
            operation: "sampled_four_point_delta_summary",
        })?;
    let log_samples = if cfg.n_samples <= 1 {
        1u128
    } else {
        (usize::BITS - (cfg.n_samples - 1).leading_zeros()) as u128
    };
    let validation_operations = n.checked_mul(d).ok_or(PidError::SizeOverflow {
        operation: "sampled_four_point_delta_summary",
    })?;
    let sort_operations = samples
        .checked_mul(log_samples)
        .ok_or(PidError::SizeOverflow {
            operation: "sampled_four_point_delta_summary",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: samples
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "sampled_four_point_delta_summary",
            })?,
        pairwise_distances: pairs,
        operations_hint: diameter_operations
            .checked_add(sample_operations)
            .and_then(|value| value.checked_add(validation_operations))
            .and_then(|value| value.checked_add(sort_operations))
            .ok_or(PidError::SizeOverflow {
                operation: "sampled_four_point_delta_summary",
            })?,
    })
}

/// Sampled four-point diagnostics with a caller-supplied resource ceiling.
pub fn sampled_four_point_delta_summary_with_budget(
    x: MatRef<'_>,
    cfg: &HyperbolicityConfig,
    budget: ResourceBudget,
) -> PidResult<SampledFourPointDeltaSummary> {
    let cancellation = CancellationToken::new();
    sampled_four_point_delta_summary_with_budget_and_cancellation(x, cfg, budget, &cancellation)
}

/// Sampled four-point diagnostics with resource and cooperative-cancellation controls.
pub fn sampled_four_point_delta_summary_with_budget_and_cancellation(
    x: MatRef<'_>,
    cfg: &HyperbolicityConfig,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<SampledFourPointDeltaSummary> {
    const OPERATION: &str = "sampled_four_point_delta_summary";
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
    budget.check(OPERATION, sampled_four_point_resource_estimate(x, cfg)?)?;
    let diameter_distances = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let sample_distances = cfg.n_samples.checked_mul(6).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let total_work = n
        .checked_add(diameter_distances)
        .and_then(|value| value.checked_add(sample_distances))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let mut completed_work = 0usize;
    cancellation.check(OPERATION, completed_work, total_work)?;
    let mut deltas = try_vec_with_capacity(
        "sampled_four_point_delta_summary deltas",
        cfg.n_samples,
        budget,
    )?;

    // Sampling must not make input validity seed-dependent. In particular, a finite row that is
    // off the unit hyperboloid can otherwise be omitted from every sampled quadruple and yield a
    // plausible `Ok` diagnostic. A checked self-distance validates each row once without changing
    // the sampled estimator.
    for i in 0..n {
        cfg.metric.checked_distance_with_cancellation(
            x.row(i),
            x.row(i),
            "sampled_four_point_delta_summary: invalid input row",
            CancellationProgress::new(OPERATION, completed_work, total_work),
            cancellation,
        )?;
        completed_work = completed_work
            .checked_add(1)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        cancellation.check(OPERATION, completed_work, total_work)?;
    }

    let mut diameter = 0.0_f64;
    for i in 0..n {
        for j in (i + 1)..n {
            let distance = cfg.metric.checked_distance_with_cancellation(
                x.row(i),
                x.row(j),
                "sampled_four_point_delta_summary: diameter distance",
                CancellationProgress::new(OPERATION, completed_work, total_work),
                cancellation,
            )?;
            diameter = diameter.max(distance);
            completed_work = completed_work
                .checked_add(1)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
            if completed_work.is_multiple_of(1_024) {
                cancellation.check(OPERATION, completed_work, total_work)?;
            }
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
        let dij = cfg.metric.checked_distance_with_cancellation(
            pi,
            pj,
            ctx,
            CancellationProgress::new(OPERATION, completed_work, total_work),
            cancellation,
        )?;
        let dkl = cfg.metric.checked_distance_with_cancellation(
            pk,
            pl,
            ctx,
            CancellationProgress::new(OPERATION, completed_work + 1, total_work),
            cancellation,
        )?;
        let dik = cfg.metric.checked_distance_with_cancellation(
            pi,
            pk,
            ctx,
            CancellationProgress::new(OPERATION, completed_work + 2, total_work),
            cancellation,
        )?;
        let djl = cfg.metric.checked_distance_with_cancellation(
            pj,
            pl,
            ctx,
            CancellationProgress::new(OPERATION, completed_work + 3, total_work),
            cancellation,
        )?;
        let dil = cfg.metric.checked_distance_with_cancellation(
            pi,
            pl,
            ctx,
            CancellationProgress::new(OPERATION, completed_work + 4, total_work),
            cancellation,
        )?;
        let djk = cfg.metric.checked_distance_with_cancellation(
            pj,
            pk,
            ctx,
            CancellationProgress::new(OPERATION, completed_work + 5, total_work),
            cancellation,
        )?;
        completed_work = completed_work
            .checked_add(6)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        cancellation.check(OPERATION, completed_work, total_work)?;

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

    cancellation.check(OPERATION, completed_work, total_work)?;
    sort_unstable_by_with_cancellation(OPERATION, &mut deltas, cancellation, f64::total_cmp)?;
    cancellation.check(OPERATION, completed_work, total_work)?;
    let mean = mean_delta;
    let median = linear_quantile(&deltas, 0.5);
    let p90 = linear_quantile(&deltas, 0.9);
    let p99 = linear_quantile(&deltas, 0.99);
    let max = deltas
        .last()
        .copied()
        .ok_or(PidError::NumericalInstability {
            context: "sampled_four_point_delta_summary: empty sorted sample",
        })?;
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
#[cfg(any())]
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
    stable_interpolate(sorted[lower], sorted[upper], fraction)
}

fn stable_interpolate(lower: f64, upper: f64, fraction: f64) -> f64 {
    if lower == upper || fraction == 0.0 {
        return lower;
    }
    if fraction == 1.0 {
        return upper;
    }
    let difference = upper - lower;
    let interpolated = if difference.is_finite() {
        lower + fraction * difference
    } else {
        lower * (1.0 - fraction) + upper * fraction
    };
    interpolated.clamp(lower, upper)
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
        linear_quantile, sample_four_distinct, sampled_four_point_delta_summary, stable_log_ratio,
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
    fn quantile_interpolation_does_not_overflow_opposite_extremes() {
        let values = [-f64::MAX, f64::MAX];

        assert_eq!(linear_quantile(&values, 0.5), 0.0);
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
            Err(PidError::ResourceLimitExceeded { .. } | PidError::SizeOverflow { .. })
        ));
    }

    #[test]
    fn distinct_sampler_preserves_historical_seeded_quadruple() {
        let mut rng = SplitMix64::new(42 ^ 0xcafe_f00d_d15e_a5e5);

        assert_eq!(sample_four_distinct(&mut rng, 5), [2, 1, 3, 4]);
    }

    #[test]
    #[cfg(feature = "experimental-hyperbolic")]
    fn sampled_four_point_delta_prevalidates_hyperbolic_rows_that_sampling_would_omit() {
        let mut data = vec![2.0, 0.0]; // Finite, but off the unit hyperboloid.
        for rapidity in [0.0_f64, 0.2, 0.4, 0.6] {
            data.push(rapidity.cosh());
            data.push(rapidity.sinh());
        }
        let matrix = MatRef::new(&data, 5, 2).unwrap();
        let config = HyperbolicityConfig {
            n_samples: 1,
            metric: Metric::HyperbolicLorentz {
                curvature: crate::hyperbolic::HyperbolicCurvature::NegativeOne,
            },
            seed: 42,
        };

        // This seed's sole quadruple is [2,1,3,4], so the old sampled-only validation omitted row 0.
        assert!(matches!(
            sampled_four_point_delta_summary(matrix, &config),
            Err(PidError::InvalidConfig { .. })
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
