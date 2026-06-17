use pid_core::{
    distance_concentration_stats, intrinsic_dimension_levina_bickel, DistanceConcentrationConfig,
    IntrinsicDimConfig, MatRef, Metric, PidError,
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
