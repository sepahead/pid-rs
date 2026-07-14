use pid_core::diagnostics::{
    distance_concentration_stats, distance_concentration_stats_with_budget_and_cancellation,
    intrinsic_dimension_levina_bickel, intrinsic_dimension_report,
    sampled_four_point_delta_summary,
    sampled_four_point_delta_summary_with_budget_and_cancellation, DistanceConcentrationConfig,
    HyperbolicityConfig, IntrinsicDimConfig,
};
use pid_core::{CancellationToken, MatRef, Metric, PidError, ResourceBudget};

mod common;

use common::Rng64;

#[test]
fn distance_concentration_cancellation_preserves_parity_and_stops_mid_work() {
    let small_data: Vec<f64> = (0..600)
        .map(|index| (index as f64).mul_add(0.013, (index % 11) as f64 * 0.001))
        .collect();
    let small = MatRef::new(&small_data, 200, 3).unwrap();
    let config = DistanceConcentrationConfig::default();
    let baseline = distance_concentration_stats(small, &config).unwrap();
    let token = CancellationToken::new();
    let cancellable = distance_concentration_stats_with_budget_and_cancellation(
        small,
        &config,
        ResourceBudget::default(),
        &token,
    )
    .unwrap();
    assert_eq!(baseline.pairwise_count, cancellable.pairwise_count);
    for (left, right) in [
        (baseline.pairwise_min, cancellable.pairwise_min),
        (baseline.pairwise_max, cancellable.pairwise_max),
        (baseline.pairwise_mean, cancellable.pairwise_mean),
        (baseline.pairwise_std, cancellable.pairwise_std),
        (baseline.pairwise_cv, cancellable.pairwise_cv),
        (baseline.nn_min, cancellable.nn_min),
        (baseline.nn_max, cancellable.nn_max),
        (baseline.nn_mean, cancellable.nn_mean),
        (baseline.nn_std, cancellable.nn_std),
        (baseline.nn_cv, cancellable.nn_cv),
        (
            baseline.nn_over_pairwise_mean,
            cancellable.nn_over_pairwise_mean,
        ),
    ] {
        assert_eq!(left.to_bits(), right.to_bits());
    }

    let n = 3_000usize;
    let d = 32usize;
    let large_data: Vec<f64> = (0..n * d)
        .map(|index| (index as f64).mul_add(0.000_031, (index % 17) as f64 * 0.000_001))
        .collect();
    let large = MatRef::new(&large_data, n, d).unwrap();
    let token = std::sync::Arc::new(CancellationToken::new());
    let canceller = std::sync::Arc::clone(&token);
    let request = std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(5));
        canceller.cancel();
    });
    let error = distance_concentration_stats_with_budget_and_cancellation(
        large,
        &config,
        ResourceBudget::default(),
        token.as_ref(),
    )
    .unwrap_err();
    request.join().unwrap();
    assert!(matches!(
        error,
        PidError::Cancelled {
            operation: "distance_concentration_stats",
            ..
        }
    ));
}

#[test]
fn sampled_four_point_cancellation_preserves_parity_and_stops_mid_work() {
    let data = [0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 2.0, 2.0, 1.0, 0.25];
    let matrix = MatRef::new(&data, 5, 2).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(1_000)
        .with_metric(Metric::Chebyshev)
        .with_seed(0x5eed);
    let baseline = sampled_four_point_delta_summary(matrix, &config).unwrap();
    let running = CancellationToken::new();
    let cancellable = sampled_four_point_delta_summary_with_budget_and_cancellation(
        matrix,
        &config,
        ResourceBudget::default(),
        &running,
    )
    .unwrap();
    assert_eq!(baseline, cancellable);

    let cancelled = CancellationToken::new();
    cancelled.cancel();
    assert!(matches!(
        sampled_four_point_delta_summary_with_budget_and_cancellation(
            matrix,
            &config,
            ResourceBudget::default(),
            &cancelled,
        ),
        Err(PidError::Cancelled {
            operation: "sampled_four_point_delta_summary",
            completed_units: 0,
            ..
        })
    ));

    let n = 3_000usize;
    let d = 32usize;
    let large_data: Vec<f64> = (0..n * d)
        .map(|index| (index as f64).mul_add(0.000_031, (index % 17) as f64 * 0.000_001))
        .collect();
    let large = MatRef::new(&large_data, n, d).unwrap();
    let token = std::sync::Arc::new(CancellationToken::new());
    let canceller = std::sync::Arc::clone(&token);
    let request = std::thread::spawn(move || {
        std::thread::sleep(std::time::Duration::from_millis(5));
        canceller.cancel();
    });
    let error = sampled_four_point_delta_summary_with_budget_and_cancellation(
        large,
        &HyperbolicityConfig::default().with_n_samples(1),
        ResourceBudget::default(),
        token.as_ref(),
    )
    .unwrap_err();
    request.join().unwrap();
    assert!(matches!(
        error,
        PidError::Cancelled {
            operation: "sampled_four_point_delta_summary",
            ..
        }
    ));
}

#[test]
fn intrinsic_dimension_increases_with_embedding_dimension() {
    let mut rng = Rng64::new(0xD1A7_2026);
    let n = 350usize;

    // 1D Gaussian.
    let mut x1 = Vec::with_capacity(n);
    for _ in 0..n {
        x1.push(rng.normal());
    }
    let x1 = MatRef::new(&x1, n, 1).unwrap();

    // 3D Gaussian (independent coords).
    let mut x3 = Vec::with_capacity(n * 3);
    for _ in 0..n {
        x3.push(rng.normal());
        x3.push(rng.normal());
        x3.push(rng.normal());
    }
    let x3 = MatRef::new(&x3, n, 3).unwrap();

    let cfg = IntrinsicDimConfig::default()
        .with_k(10)
        .with_metric(Metric::Chebyshev);

    let d1 = intrinsic_dimension_levina_bickel(x1, &cfg).unwrap();
    let d3 = intrinsic_dimension_levina_bickel(x3, &cfg).unwrap();

    assert!(d1.is_finite() && d1 > 0.0, "d1={d1}");
    assert!(d3.is_finite() && d3 > 0.0, "d3={d3}");
    assert!(d3 > d1 + 0.5, "expected d3>d1, got d1={d1} d3={d3}");
}

#[test]
fn intrinsic_dimension_errors_on_duplicate_points() {
    let n = 50usize;
    let x = vec![0.0f64; n];
    let x = MatRef::new(&x, n, 1).unwrap();
    let cfg = IntrinsicDimConfig::default();

    let err = intrinsic_dimension_levina_bickel(x, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::NumericalInstability { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn intrinsic_dimension_rejects_positive_tie_crossing_kth_shell() {
    // Around the middle point at x=2 the non-self distances are 1,1,2,2. For k=3 the
    // third-order radius is 2 with two boundary points, so the local order statistic is not
    // uniquely defined. Additional distant points make n > k while preserving that shell.
    let x = [-100.0, 0.0, 1.0, 2.0, 3.0, 4.0, 100.0];
    let x = MatRef::new(&x, x.len(), 1).unwrap();
    let cfg = IntrinsicDimConfig::default()
        .with_k(3)
        .with_metric(Metric::Chebyshev);

    let error = intrinsic_dimension_levina_bickel(x, &cfg).unwrap_err();

    assert!(matches!(
        error,
        PidError::AmbiguousKthNeighborShell {
            k: 3,
            boundary_count: 2,
            ..
        }
    ));
}

#[test]
fn intrinsic_dimension_rejects_k_two_tied_shell_fixture() {
    // At x=2 the non-self distances are exactly 1,1,2,2. The bias-corrected
    // Levina--Bickel/MacKay--Ghahramani estimator itself requires k >= 3, so the audit's k=2
    // fixture is rejected at configuration validation; the k=3 test above separately proves that
    // a positive tied boundary is rejected by the shell contract.
    let data = [0.0, 1.0, 2.0, 3.0, 4.0];
    let matrix = MatRef::new(&data, data.len(), 1).unwrap();
    let config = IntrinsicDimConfig::default()
        .with_k(2)
        .with_metric(Metric::Chebyshev);

    assert!(matches!(
        intrinsic_dimension_levina_bickel(matrix, &config),
        Err(PidError::InvalidK { k: 2, .. })
    ));
}

#[test]
fn intrinsic_dimension_unique_shell_matches_independent_hand_oracle() {
    // Golomb-like coordinates make every k=3 boundary unique. Compute the reference directly
    // from the published corrected local formula, independently of the crate's shell machinery:
    // m_i = (k - 2) / sum_{j=1}^{k-1} ln(T_k(i) / T_j(i)). Frozen bits run in both serial and
    // `parallel` CI configurations.
    let data = [0.0_f64, 1.0, 4.0, 10.0, 12.0, 17.0];
    let matrix = MatRef::new(&data, data.len(), 1).unwrap();
    let config = IntrinsicDimConfig::default()
        .with_k(3)
        .with_metric(Metric::Chebyshev);
    let report = intrinsic_dimension_report(matrix, &config, ResourceBudget::default()).unwrap();

    let mut oracle = Vec::with_capacity(data.len());
    for (i, value) in data.iter().enumerate() {
        let mut distances: Vec<f64> = data
            .iter()
            .enumerate()
            .filter_map(|(j, other)| (i != j).then_some((value - other).abs()))
            .collect();
        distances.sort_unstable_by(f64::total_cmp);
        let kth = distances[2];
        let log_sum: f64 = distances[..2]
            .iter()
            .map(|distance| (kth / distance).ln())
            .sum();
        oracle.push(1.0 / log_sum);
    }
    let oracle_mean = oracle.iter().sum::<f64>() / oracle.len() as f64;

    for (actual, expected) in report.local_estimates.iter().zip(&oracle) {
        assert!((actual - expected).abs() <= 2.0e-15);
    }
    assert!((report.mean - oracle_mean).abs() <= 2.0e-15);
    // CI runs this same independent oracle in both serial and `parallel` feature builds. Exact
    // transcendental last bits are intentionally not frozen across operating-system libm builds.
}

#[test]
fn distance_concentration_matches_hand_computed_example() {
    // Three points on the line: 0, 1, 3.
    //
    // Pairwise distances: {1,2,3}
    // mean = 2
    // std_pop = sqrt(((1-2)^2 + (2-2)^2 + (3-2)^2)/3) = sqrt(2/3)
    //
    // Nearest-neighbor distances per point: {1,1,2}
    // mean = 4/3
    // std_pop = sqrt(((1-4/3)^2 + (1-4/3)^2 + (2-4/3)^2)/3) = sqrt(2/9)
    let x = [0.0f64, 1.0, 3.0];
    let x = MatRef::new(&x, 3, 1).unwrap();

    let cfg = DistanceConcentrationConfig::default().with_metric(Metric::Chebyshev);
    let s = distance_concentration_stats(x, &cfg).unwrap();

    let pair_mean = 2.0;
    let pair_std = (2.0_f64 / 3.0).sqrt();
    let nn_mean = 4.0 / 3.0;
    let nn_std = (2.0_f64 / 9.0).sqrt();

    assert!(
        (s.pairwise_mean - pair_mean).abs() < 1e-12,
        "mean={}",
        s.pairwise_mean
    );
    assert!(
        (s.pairwise_std - pair_std).abs() < 1e-12,
        "std={}",
        s.pairwise_std
    );
    assert!(
        (s.pairwise_cv - (pair_std / pair_mean)).abs() < 1e-12,
        "cv={}",
        s.pairwise_cv
    );

    assert!((s.nn_mean - nn_mean).abs() < 1e-12, "nn_mean={}", s.nn_mean);
    assert!((s.nn_std - nn_std).abs() < 1e-12, "nn_std={}", s.nn_std);
    assert!(
        (s.nn_cv - (nn_std / nn_mean)).abs() < 1e-12,
        "nn_cv={}",
        s.nn_cv
    );
    assert!(
        (s.nn_over_pairwise_mean - (nn_mean / pair_mean)).abs() < 1e-12,
        "nn/mean={}",
        s.nn_over_pairwise_mean
    );
}

#[test]
fn distance_concentration_errors_on_fully_degenerate_data() {
    // All points identical => all distances 0 => mean distance 0 (degenerate).
    let x = [0.0f64; 8];
    let x = MatRef::new(&x, 4, 2).unwrap();
    let cfg = DistanceConcentrationConfig::default();

    let err = distance_concentration_stats(x, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::NumericalInstability { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn distance_concentration_handles_finite_extreme_distances() {
    let data = [0.0, f64::MAX * 0.5, f64::MAX];
    let x = MatRef::new(&data, 3, 1).unwrap();

    let stats = distance_concentration_stats(x, &DistanceConcentrationConfig::default()).unwrap();

    assert!(stats.pairwise_mean.is_finite());
    assert!(stats.pairwise_std.is_finite());
    assert!((stats.pairwise_cv - 2.0_f64.sqrt() / 4.0).abs() < 1.0e-15);
}

#[test]
fn distance_concentration_is_invariant_to_extreme_uniform_scaling() {
    fn summaries(scale: f64) -> (f64, f64, f64) {
        let data = [0.0, scale, 3.0 * scale];
        let x = MatRef::new(&data, 3, 1).unwrap();
        let stats =
            distance_concentration_stats(x, &DistanceConcentrationConfig::default()).unwrap();
        (stats.pairwise_cv, stats.nn_cv, stats.nn_over_pairwise_mean)
    }

    let baseline = summaries(1.0);
    for scale in [1.0e-200, 1.0e200] {
        let scaled = summaries(scale);
        assert!((scaled.0 - baseline.0).abs() < 1.0e-14);
        assert!((scaled.1 - baseline.1).abs() < 1.0e-14);
        assert!((scaled.2 - baseline.2).abs() < 1.0e-14);
    }
}

#[test]
fn distance_concentration_keeps_subnormal_dimensionless_summaries() {
    let smallest = f64::from_bits(1);
    let data = [0.0, smallest, 2.0 * smallest];
    let x = MatRef::new(&data, 3, 1).unwrap();

    let stats = distance_concentration_stats(x, &DistanceConcentrationConfig::default()).unwrap();

    assert!((stats.pairwise_cv - 2.0_f64.sqrt() / 4.0).abs() < 1.0e-15);
    assert!((stats.nn_over_pairwise_mean - 0.75).abs() < 1.0e-15);
}

#[test]
fn intrinsic_dimension_uses_stable_log_ratios_across_extreme_scales() {
    let data = [
        0.0, 1.0e-308, 2.0e-308, 1.0e307, 1.1e307, 1.3e307, 1.7e307, 2.5e307,
    ];
    let x = MatRef::new(&data, data.len(), 1).unwrap();
    let config = IntrinsicDimConfig::default()
        .with_k(3)
        .with_metric(Metric::Chebyshev);

    let estimate = intrinsic_dimension_levina_bickel(x, &config).unwrap();

    assert!(estimate.is_finite() && estimate > 0.0);
}

#[test]
fn sampled_four_point_delta_draws_one_distinct_quadruple_when_n_is_four() {
    let data = [0.0, 1.0, 2.0, 3.0];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(1)
        .with_metric(Metric::Chebyshev)
        .with_seed(0);

    let summary = sampled_four_point_delta_summary(x, &config).unwrap();

    assert_eq!(summary.sample_count, 1);
    assert_eq!(summary.mean, 0.0);
    assert_eq!(summary.median, 0.0);
    assert_eq!(summary.p90, 0.0);
    assert_eq!(summary.p99, 0.0);
    assert_eq!(summary.max, 0.0);
    assert_eq!(summary.monte_carlo_standard_error, None);
    assert_eq!(summary.diameter, 3.0);
    assert_eq!(summary.normalized_mean, Some(0.0));
    assert_eq!(summary.normalized_max, Some(0.0));
    assert_eq!(summary.normalized_monte_carlo_standard_error, None);
}

#[test]
fn sampled_four_point_delta_rejects_zero_requested_samples() {
    let data = [0.0, 1.0, 2.0, 3.0];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(0)
        .with_metric(Metric::Chebyshev)
        .with_seed(0);

    assert!(matches!(
        sampled_four_point_delta_summary(x, &config),
        Err(PidError::InvalidConfig { .. })
    ));
}

#[test]
fn sampled_four_point_summary_reports_deterministic_distribution_and_normalization() {
    let data = [0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 2.0, 2.0, 1.0, 0.25];
    let x = MatRef::new(&data, 5, 2).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(1_000)
        .with_metric(Metric::Chebyshev)
        .with_seed(0x5eed);

    let first = sampled_four_point_delta_summary(x, &config).unwrap();
    let second = sampled_four_point_delta_summary(x, &config).unwrap();

    assert_eq!(first, second);
    assert_eq!(first.sample_count, 1_000);
    assert_eq!(first.diameter, 2.0);
    assert!(first.mean >= 0.0);
    assert!(first.median >= 0.0);
    assert!(first.p90 >= first.median);
    assert!(first.p99 >= first.p90);
    assert!(first.max >= first.p99);
    assert!(first
        .monte_carlo_standard_error
        .is_some_and(|value| value > 0.0));
    assert_eq!(first.normalized_mean, Some(first.mean));
    assert_eq!(first.normalized_median, Some(first.median));
    assert_eq!(first.normalized_p90, Some(first.p90));
    assert_eq!(first.normalized_p99, Some(first.p99));
    assert_eq!(first.normalized_max, Some(first.max));
    assert_eq!(
        first.normalized_monte_carlo_standard_error,
        first.monte_carlo_standard_error
    );
}

#[test]
fn sampled_four_point_summary_marks_zero_diameter_normalization_undefined() {
    let data = [3.0, 3.0, 3.0, 3.0];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(2)
        .with_metric(Metric::Chebyshev)
        .with_seed(7);

    let summary = sampled_four_point_delta_summary(x, &config).unwrap();

    assert_eq!(summary.diameter, 0.0);
    assert_eq!(summary.mean, 0.0);
    assert_eq!(summary.monte_carlo_standard_error, Some(0.0));
    assert_eq!(summary.normalized_mean, None);
    assert_eq!(summary.normalized_median, None);
    assert_eq!(summary.normalized_p90, None);
    assert_eq!(summary.normalized_p99, None);
    assert_eq!(summary.normalized_max, None);
    assert_eq!(summary.normalized_monte_carlo_standard_error, None);
}

#[cfg(any())]
#[test]
fn deprecated_gromov_wrapper_returns_sampled_mean() {
    let data = [0.0, 0.0, 2.0, 0.0, 0.0, 2.0, 2.0, 2.0, 1.0, 0.25];
    let x = MatRef::new(&data, 5, 2).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(50)
        .with_metric(Metric::Chebyshev)
        .with_seed(11);

    let summary = sampled_four_point_delta_summary(x, &config).unwrap();
    let legacy = pid_core::gromov_hyperbolicity(x, &config).unwrap();

    assert_eq!(legacy, summary.mean);
}

#[test]
fn sampled_four_point_delta_normalizes_pair_sums_before_cancellation() {
    // These dyadic line coordinates have two exactly equal largest pair sums, each larger than
    // f64::MAX. Their difference remains exactly zero after power-of-two normalization.
    let scale = 2.0_f64.powi(1023);
    let diameter = 1.5 * scale;
    let data = [0.0, 0.25 * diameter, 0.75 * diameter, diameter];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let cfg = HyperbolicityConfig::default()
        .with_n_samples(10_000)
        .with_metric(Metric::Chebyshev)
        .with_seed(42);

    let summary = sampled_four_point_delta_summary(x, &cfg).unwrap();

    assert_eq!(summary.mean, 0.0);
    assert_eq!(summary.max, 0.0);
    assert_eq!(summary.monte_carlo_standard_error, Some(0.0));
    assert_eq!(summary.diameter, diameter);
    assert_eq!(summary.normalized_mean, Some(0.0));
}

#[test]
fn sampled_four_point_delta_reports_the_exact_represented_near_max_delta() {
    // The rounded Chebyshev distances for these near-MAX coordinates make the two largest pair
    // sums differ by exactly 2^-54 after power-of-two normalization. Report that represented-metric
    // delta exactly; a blanket epsilon snap would erase it, while inexact scaling overstates it.
    let data = [
        f64::from_bits(0xffbe_1a13_42b7_2ef7),
        f64::from_bits(0x7f99_d7ea_4cf4_13df),
        f64::from_bits(0x7fae_5c96_fa7d_22cf),
        f64::from_bits(0x7fd8_92b2_6887_f3f1),
    ];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(1)
        .with_metric(Metric::Chebyshev)
        .with_seed(0);

    let summary = sampled_four_point_delta_summary(x, &config).unwrap();

    assert_eq!(summary.mean, 2.0_f64.powi(968));
}

#[test]
fn sampled_four_point_delta_preserves_a_genuine_delta_below_epsilon_band() {
    let epsilon = 2.0_f64.powi(-49);
    let data = [0.0, 0.0, 0.0, 1.0, 0.0, 2.0, epsilon, 1.0];
    let x = MatRef::new(&data, 4, 2).unwrap();
    let config = HyperbolicityConfig::default()
        .with_n_samples(1)
        .with_metric(Metric::Chebyshev)
        .with_seed(0);

    let summary = sampled_four_point_delta_summary(x, &config).unwrap();

    assert_eq!(summary.mean, 2.0_f64.powi(-50));
}
