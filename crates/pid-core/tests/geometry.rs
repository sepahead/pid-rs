use pid_core::{
    distance_concentration_stats, gromov_hyperbolicity, intrinsic_dimension_levina_bickel,
    DistanceConcentrationConfig, HyperbolicityConfig, IntrinsicDimConfig, MatRef, Metric, PidError,
};

mod common;

use common::Rng64;

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

    let cfg = IntrinsicDimConfig {
        k: 10,
        metric: Metric::Chebyshev,
    };

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

    let cfg = DistanceConcentrationConfig {
        metric: Metric::Chebyshev,
    };
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
    let config = IntrinsicDimConfig {
        k: 3,
        metric: Metric::Chebyshev,
    };

    let estimate = intrinsic_dimension_levina_bickel(x, &config).unwrap();

    assert!(estimate.is_finite() && estimate > 0.0);
}

#[test]
fn gromov_draws_one_distinct_quadruple_when_n_is_four() {
    let data = [0.0, 1.0, 2.0, 3.0];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig {
        n_samples: 1,
        metric: Metric::Chebyshev,
        seed: 0,
    };

    let delta = gromov_hyperbolicity(x, &config).unwrap();

    assert_eq!(delta, 0.0);
}

#[test]
fn gromov_rejects_zero_requested_samples() {
    let data = [0.0, 1.0, 2.0, 3.0];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let config = HyperbolicityConfig {
        n_samples: 0,
        metric: Metric::Chebyshev,
        seed: 0,
    };

    assert!(matches!(
        gromov_hyperbolicity(x, &config),
        Err(PidError::InvalidConfig { .. })
    ));
}

#[test]
fn gromov_hyperbolicity_normalizes_pair_sums_before_cancellation() {
    // These dyadic line coordinates have two exactly equal largest pair sums, each larger than
    // f64::MAX. Their difference remains exactly zero after power-of-two normalization.
    let scale = 2.0_f64.powi(1023);
    let diameter = 1.5 * scale;
    let data = [0.0, 0.25 * diameter, 0.75 * diameter, diameter];
    let x = MatRef::new(&data, 4, 1).unwrap();
    let cfg = HyperbolicityConfig {
        n_samples: 10_000,
        metric: Metric::Chebyshev,
        seed: 42,
    };

    let delta = gromov_hyperbolicity(x, &cfg).unwrap();

    assert_eq!(delta, 0.0);
}

#[test]
fn gromov_hyperbolicity_reports_the_exact_represented_near_max_delta() {
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
    let config = HyperbolicityConfig {
        n_samples: 1,
        metric: Metric::Chebyshev,
        seed: 0,
    };

    let delta = gromov_hyperbolicity(x, &config).unwrap();

    assert_eq!(delta, 2.0_f64.powi(968));
}

#[test]
fn gromov_hyperbolicity_preserves_a_genuine_delta_below_epsilon_band() {
    let epsilon = 2.0_f64.powi(-49);
    let data = [0.0, 0.0, 0.0, 1.0, 0.0, 2.0, epsilon, 1.0];
    let x = MatRef::new(&data, 4, 2).unwrap();
    let config = HyperbolicityConfig {
        n_samples: 1,
        metric: Metric::Chebyshev,
        seed: 0,
    };

    let delta = gromov_hyperbolicity(x, &config).unwrap();

    assert_eq!(delta, 2.0_f64.powi(-50));
}
