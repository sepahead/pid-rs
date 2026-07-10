//! Block bootstrap for uncertainty quantification of estimators.
//!
//! Given a vector of i.i.d. or weakly dependent samples and a statistic function,
//! block bootstrap resamples contiguous blocks (with replacement) and recomputes
//! the statistic on each resample. This yields a bootstrap distribution from which
//! standard errors and percentile confidence intervals can be derived.
//!
//! This implements the **moving-block bootstrap** (Künsch 1989): block starts are
//! drawn uniformly over all `n − block_size + 1` positions (so every sample — head,
//! interior, and tail — is reachable), and `⌈n / block_size⌉` blocks are
//! concatenated and truncated to exactly `n`. Overlapping moving blocks avoid the
//! tail-drop and grid-alignment bias of a fixed non-overlapping partition.
//!
//! [`crate::bootstrap_rows_stats`] additionally supports fixed-grid block subsampling without
//! repeated row indices for kNN diagnostics; that is the path Exp0 uses. Ties already present in
//! the original data remain possible.
//!
//! # Example
//! ```
//! use pid_core::{block_bootstrap, BootstrapConfig, BootstrapResult};
//!
//! let data: Vec<f64> = (0..200).map(|i| (i as f64) * 0.01).collect();
//! let cfg = BootstrapConfig {
//!     n_boot: 100,
//!     block_size: 20,
//!     seed: 42,
//!     alpha: 0.05,
//! };
//! let result = block_bootstrap(&data, &cfg, |samples| {
//!     samples.iter().sum::<f64>() / samples.len() as f64
//! })?;
//! assert!(result.ci_low < result.ci_high);
//! # Ok::<(), pid_core::PidError>(())
//! ```

use crate::error::{PidError, PidResult};
use crate::par::slice_map_index_ordered;
use crate::preprocess::SplitMix64;

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
pub struct BootstrapConfig {
    /// Number of bootstrap resamples attempted.
    pub n_boot: usize,
    /// Block size (number of contiguous samples per block).
    pub block_size: usize,
    /// PRNG seed for reproducibility.
    pub seed: u64,
    /// Significance level for the percentile CI (e.g. 0.05 for a 95% CI).
    pub alpha: f64,
}

impl Default for BootstrapConfig {
    fn default() -> Self {
        Self {
            n_boot: 200,
            block_size: 10,
            seed: 0,
            alpha: 0.05,
        }
    }
}

/// Result of a block bootstrap.
#[derive(Debug, Clone, PartialEq)]
pub struct BootstrapResult {
    /// Point estimate on the original data.
    pub point_estimate: f64,
    /// Mean of bootstrap distribution.
    pub boot_mean: f64,
    /// Standard error (std of bootstrap distribution).
    pub boot_se: f64,
    /// Lower percentile CI bound.
    pub ci_low: f64,
    /// Upper percentile CI bound.
    pub ci_high: f64,
    /// Number of bootstrap resamples.
    pub n_boot: usize,
    /// Number of bootstrap resamples whose statistic was finite.
    pub n_valid: usize,
    /// Block size used.
    pub block_size: usize,
}

fn validate_bootstrap_config(
    context: &'static str,
    data_len: usize,
    cfg: &BootstrapConfig,
) -> PidResult<()> {
    if data_len == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "data must not be empty",
        });
    }
    if cfg.block_size == 0 || cfg.block_size > data_len {
        return Err(PidError::InvalidConfig {
            context,
            message: "block_size must be in 1..=data.len()",
        });
    }
    if cfg.n_boot == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "n_boot must be > 0",
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

fn summarize_bootstrap(
    context: &'static str,
    point_estimate: f64,
    mut boot_stats: Vec<f64>,
    cfg: &BootstrapConfig,
) -> PidResult<BootstrapResult> {
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context });
    }

    boot_stats.retain(|x| x.is_finite());
    if boot_stats.is_empty() {
        return Err(PidError::NumericalInstability { context });
    }

    boot_stats.sort_by(f64::total_cmp);
    let n_valid = boot_stats.len();
    let boot_mean = boot_stats.iter().sum::<f64>() / n_valid as f64;
    let boot_var = boot_stats
        .iter()
        .map(|&x| (x - boot_mean).powi(2))
        .sum::<f64>()
        / n_valid as f64;
    let boot_se = boot_var.sqrt();
    if !(boot_mean.is_finite() && boot_se.is_finite()) {
        return Err(PidError::NumericalInstability { context });
    }

    let lo_idx = ((cfg.alpha / 2.0) * n_valid as f64).floor() as usize;
    let hi_idx = (((1.0 - cfg.alpha / 2.0) * n_valid as f64).ceil() as usize)
        .saturating_sub(1)
        .min(n_valid - 1);

    Ok(BootstrapResult {
        point_estimate,
        boot_mean,
        boot_se,
        ci_low: boot_stats[lo_idx],
        ci_high: boot_stats[hi_idx],
        n_boot: cfg.n_boot,
        n_valid,
        block_size: cfg.block_size,
    })
}

/// Run block bootstrap on a 1-D sample vector with a user-supplied statistic.
///
/// `statistic` is called with a slice of resampled values and must return a scalar.
///
/// With the `parallel` feature the per-resample `statistic` evaluations run data-parallel,
/// but the resample **index sequences are drawn serially** from the seeded RNG (so the RNG
/// stream is unchanged) and the resulting `boot_stats` vector is collected **in resample
/// order** before any reduction — so the result is bit-for-bit identical to the serial path.
///
/// # Errors
///
/// Returns [`PidError::InvalidConfig`] for empty data or an invalid bootstrap configuration.
/// Returns [`PidError::NumericalInstability`] if the original statistic is non-finite or no
/// resample produces a finite statistic.
pub fn block_bootstrap<F>(
    data: &[f64],
    cfg: &BootstrapConfig,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64]) -> f64 + Sync + Send,
{
    const CONTEXT: &str = "block_bootstrap";
    validate_bootstrap_config(CONTEXT, data.len(), cfg)?;

    let n = data.len();
    // Moving-block bootstrap: every position is a valid block start, and we draw
    // enough blocks to cover n, then truncate — so no sample is ever dropped.
    let n_starts = n - cfg.block_size + 1;
    let blocks_needed = n.div_ceil(cfg.block_size);

    // Point estimate
    let point_estimate = statistic(data);
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context: CONTEXT });
    }

    // Draw every resample's block-start sequence serially so the RNG stream is identical to
    // the serial path, regardless of whether the statistic is later evaluated in parallel.
    let mut rng = SplitMix64::new(cfg.seed);
    let starts: Vec<Vec<usize>> = (0..cfg.n_boot)
        .map(|_| {
            (0..blocks_needed)
                .map(|_| uniform_index(&mut rng, n_starts))
                .collect()
        })
        .collect();

    let build_resample = |block_starts: &[usize]| -> Vec<f64> {
        let mut resample = Vec::with_capacity(blocks_needed * cfg.block_size);
        for &start in block_starts {
            resample.extend_from_slice(&data[start..start + cfg.block_size]);
        }
        resample.truncate(n);
        resample
    };

    // Evaluate the statistic on each resample, collected in resample (index) order.
    let boot_stats = slice_map_index_ordered(&starts, |bs| statistic(&build_resample(bs)));
    summarize_bootstrap(CONTEXT, point_estimate, boot_stats, cfg)
}

/// Run block bootstrap on paired (x, y) samples, preserving pairing within blocks.
///
/// `statistic` receives two slices `(x_resample, y_resample)` of equal length.
///
/// # Errors
///
/// Returns [`PidError::RowCountMismatch`] if `x` and `y` have different lengths,
/// [`PidError::InvalidConfig`] for empty data or an invalid bootstrap configuration, and
/// [`PidError::NumericalInstability`] if the original statistic is non-finite or no resample
/// produces a finite statistic.
pub fn block_bootstrap_paired<F>(
    x: &[f64],
    y: &[f64],
    cfg: &BootstrapConfig,
    statistic: F,
) -> PidResult<BootstrapResult>
where
    F: Fn(&[f64], &[f64]) -> f64 + Sync + Send,
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

    let n = x.len();
    // Moving-block bootstrap (same scheme as `block_bootstrap`), applied jointly to
    // the (x, y) pair so within-block pairing is preserved.
    let n_starts = n - cfg.block_size + 1;
    let blocks_needed = n.div_ceil(cfg.block_size);

    let point_estimate = statistic(x, y);
    if !point_estimate.is_finite() {
        return Err(PidError::NumericalInstability { context: CONTEXT });
    }

    // Draw resample block-start sequences serially (RNG stream unchanged), then evaluate the
    // statistic per resample, collected in index order — bit-identical serial vs parallel.
    let mut rng = SplitMix64::new(cfg.seed);
    let starts: Vec<Vec<usize>> = (0..cfg.n_boot)
        .map(|_| {
            (0..blocks_needed)
                .map(|_| uniform_index(&mut rng, n_starts))
                .collect()
        })
        .collect();

    let boot_stats = slice_map_index_ordered(&starts, |block_starts| {
        let mut rx = Vec::with_capacity(blocks_needed * cfg.block_size);
        let mut ry = Vec::with_capacity(blocks_needed * cfg.block_size);
        for &start in block_starts {
            rx.extend_from_slice(&x[start..start + cfg.block_size]);
            ry.extend_from_slice(&y[start..start + cfg.block_size]);
        }
        rx.truncate(n);
        ry.truncate(n);
        statistic(&rx, &ry)
    });

    summarize_bootstrap(CONTEXT, point_estimate, boot_stats, cfg)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bootstrap_mean_of_uniform_has_narrow_ci() {
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
        };
        let result =
            block_bootstrap(&data, &cfg, |s| s.iter().sum::<f64>() / s.len() as f64).unwrap();

        // Mean should be ~0.5 for uniform [0,1]
        assert!(
            (result.point_estimate - 0.5).abs() < 0.1,
            "point estimate {}",
            result.point_estimate
        );
        // SE should be small
        assert!(result.boot_se < 0.05, "SE {}", result.boot_se);
        // CI should bracket the point estimate
        assert!(result.ci_low < result.point_estimate);
        assert!(result.ci_high > result.point_estimate);
    }

    #[test]
    fn bootstrap_is_deterministic_with_same_seed() {
        let data: Vec<f64> = (0..100).map(|i| i as f64 * 0.1).collect();
        let cfg = BootstrapConfig {
            n_boot: 50,
            block_size: 10,
            seed: 99,
            alpha: 0.05,
        };
        let stat = |s: &[f64]| s.iter().sum::<f64>() / s.len() as f64;
        let a = block_bootstrap(&data, &cfg, stat).unwrap();
        let b = block_bootstrap(&data, &cfg, stat).unwrap();
        assert_eq!(a, b);
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
            },
            stat,
        )
        .unwrap();
        let b = block_bootstrap(
            &data,
            &BootstrapConfig {
                n_boot: 50,
                block_size: 10,
                seed: 2,
                alpha: 0.05,
            },
            stat,
        )
        .unwrap();
        // Different seeds -> different bootstrap SE (not exactly equal)
        assert!((a.boot_se - b.boot_se).abs() > 1e-12);
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
        };
        let result = block_bootstrap_paired(&x, &y, &cfg, |rx, ry| {
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
        assert!(result.boot_se < 1e-10, "SE should be ~0 for perfect corr");
    }

    #[test]
    fn bootstrap_rejects_zero_block_size() {
        let data = vec![1.0, 2.0, 3.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 0,
            seed: 0,
            alpha: 0.05,
        };
        assert!(block_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_oversized_block() {
        let data = vec![1.0, 2.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 5,
            seed: 0,
            alpha: 0.05,
        };
        assert!(block_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_out_of_range_alpha() {
        // alpha >= 1 would make the percentile lower index reach/exceed len (OOB) or invert the
        // CI; it must be rejected up front rather than panic on an out-of-bounds index later.
        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 1.5,
        };
        assert!(block_bootstrap(&data, &cfg, |s| s[0]).is_err());
    }

    #[test]
    fn bootstrap_rejects_nonfinite_point_estimate() {
        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        assert!(block_bootstrap(&data, &cfg, |_| f64::NAN).is_err());
    }

    #[test]
    fn bootstrap_rejects_when_every_resample_is_nonfinite() {
        use std::sync::atomic::{AtomicUsize, Ordering};

        let data = vec![1.0, 2.0, 3.0, 4.0];
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        let calls = AtomicUsize::new(0);
        let result = block_bootstrap(&data, &cfg, |_| {
            if calls.fetch_add(1, Ordering::Relaxed) == 0 {
                1.0
            } else {
                f64::NAN
            }
        });
        assert!(
            result.is_err(),
            "all-nonfinite resamples must not return Ok"
        );
    }

    #[test]
    fn bootstrap_paired_rejects_mismatched_lengths() {
        let cfg = BootstrapConfig {
            n_boot: 10,
            block_size: 1,
            seed: 0,
            alpha: 0.05,
        };

        assert!(block_bootstrap_paired(&[1.0, 2.0], &[1.0], &cfg, |_, _| 0.0).is_err());
    }
}
