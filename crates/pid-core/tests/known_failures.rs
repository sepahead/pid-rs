//! Permanent counterexamples for regimes that pid-rs 1.0 does not claim to solve.
//!
//! These are not expected-to-panic tests. Each test must either expose the documented pathology
//! through a diagnostic or prove that the public API fails closed before returning an estimate.

use pid_core::diagnostics::{
    distance_concentration_stats, intrinsic_dimension_report, DistanceConcentrationConfig,
    IntrinsicDimConfig,
};
#[cfg(feature = "experimental-hyperbolic")]
use pid_core::experimental::hyperbolic::{
    hyperbolic_ksg_mi_report, HyperbolicCurvature, HyperbolicKsgConfig,
};
use pid_core::stable::continuous::{ksg_mi_report, KsgConfig, KsgProvenance, SupportContract};
use pid_core::{MatRef, Metric, PidError, ResourceBudget};

fn provenance() -> KsgProvenance {
    KsgProvenance::new(
        "fixed identity preprocessing",
        "declared observation model for a known-failure fixture",
        None,
    )
    .unwrap()
}

fn lcg_uniform(state: &mut u64) -> f64 {
    *state = state
        .wrapping_mul(6_364_136_223_846_793_005)
        .wrapping_add(1_442_695_040_888_963_407);
    ((*state >> 11) as f64 + 0.5) / ((1_u64 << 53) as f64)
}

#[test]
fn atom_continuous_mixture_is_rejected_instead_of_treated_as_regular_ksg() {
    let x = [0.0, 0.13, 0.0, 0.41, 0.0, 0.79, 0.0, 1.31];
    let y = [0.07, 0.19, 0.31, 0.53, 0.83, 1.09, 1.43, 1.91];
    let x = MatRef::new(&x, x.len(), 1).unwrap();
    let y = MatRef::new(&y, y.len(), 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_support_contract(SupportContract::KnownAtomicOrMixed);

    assert!(matches!(
        ksg_mi_report(x, y, &cfg, &provenance()),
        Err(PidError::UnsupportedSupportContract {
            contract: SupportContract::KnownAtomicOrMixed,
            ..
        })
    ));
}

#[test]
fn singular_deterministic_map_is_rejected_by_declared_support() {
    let x = [0.03, 0.11, 0.29, 0.47, 0.71, 1.03, 1.41, 1.89];
    let y: Vec<f64> = x.iter().map(|value| value * value).collect();
    let x = MatRef::new(&x, x.len(), 1).unwrap();
    let y = MatRef::new(&y, y.len(), 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_support_contract(SupportContract::KnownSingularOrLowerDimensional);

    assert!(matches!(
        ksg_mi_report(x, y, &cfg, &provenance()),
        Err(PidError::UnsupportedSupportContract {
            contract: SupportContract::KnownSingularOrLowerDimensional,
            ..
        })
    ));
}

#[test]
fn positive_kth_shell_tie_is_a_known_invalid_local_estimate() {
    // At x=2 the non-self distances begin 1,1,2,2. Rank k=2 has two boundary points.
    let x = [-100.0, 0.0, 1.0, 2.0, 3.0, 4.0, 100.0];
    // Keep target separations below one so the joint Chebyshev shell is governed by x while the
    // target coordinate itself remains unique.
    let target = [0.0001, 0.0013, 0.0029, 0.0047, 0.0071, 0.0103, 0.0141];
    let x = MatRef::new(&x, x.len(), 1).unwrap();
    let target = MatRef::new(&target, target.len(), 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(2);

    assert!(matches!(
        ksg_mi_report(x, target, &cfg, &provenance()),
        Err(PidError::AmbiguousKthNeighborShell {
            k: 2,
            boundary_count: 2,
            ..
        })
    ));
}

#[test]
fn local_dimension_heterogeneity_survives_the_global_mean() {
    let mut state = 0x5eed_1234_abcd_9876;
    let mut data = Vec::with_capacity(96 * 2);
    // A nearly one-dimensional stratum.
    for index in 0..48 {
        let u = index as f64 / 47.0 + 1.0e-4 * lcg_uniform(&mut state);
        data.push(u);
        data.push(1.0e-5 * u * u + 1.0e-7 * lcg_uniform(&mut state));
    }
    // A genuinely two-dimensional stratum, spatially separated from the first.
    for _ in 0..48 {
        data.push(3.0 + lcg_uniform(&mut state));
        data.push(3.0 + lcg_uniform(&mut state));
    }
    let matrix = MatRef::new(&data, 96, 2).unwrap();
    let report = intrinsic_dimension_report(
        matrix,
        &IntrinsicDimConfig::default()
            .with_k(8)
            .with_metric(Metric::Chebyshev),
        ResourceBudget::default(),
    )
    .unwrap();

    assert!(report.mean.is_finite());
    assert!(
        report.local_estimate_quantiles.p90 > 1.35 * report.local_estimate_quantiles.p10,
        "a single mean hid too little of the constructed local-dimension spread: {:?}",
        report.local_estimate_quantiles
    );
}

#[test]
fn high_dimensional_chebyshev_distances_concentrate() {
    let (n, dimensions) = (64, 128);
    let mut state = 0xa11c_e55e_1234_5678;
    let mut data = Vec::with_capacity(n * dimensions);
    for _ in 0..n * dimensions {
        data.push(lcg_uniform(&mut state));
    }
    let matrix = MatRef::new(&data, n, dimensions).unwrap();
    let stats = distance_concentration_stats(
        matrix,
        &DistanceConcentrationConfig::default().with_metric(Metric::Chebyshev),
    )
    .unwrap();

    assert!(
        stats.pairwise_cv < 0.08,
        "pairwise CV={}",
        stats.pairwise_cv
    );
    assert!(
        stats.nn_over_pairwise_mean > 0.8,
        "nearest/pairwise mean ratio={}",
        stats.nn_over_pairwise_mean
    );
}

#[cfg(feature = "research-mixed-dimension-pid3")]
#[test]
fn mixed_dimensional_small_ball_weights_collapse_as_radius_shrinks() {
    // A one-dimensional branch has mass proportional to r, while a two-dimensional branch has
    // mass proportional to r². Treating their raw radii as one common gauge makes the normalized
    // 1-D weight converge to one, irrespective of equal finite prefactors. This is the unresolved
    // asymptotic obstruction behind research-only full continuous PID3.
    let weight_1d = |radius: f64| radius / (radius + radius * radius);
    let coarse = weight_1d(0.25);
    let fine = weight_1d(2.0_f64.powi(-20));
    assert!(fine > coarse);
    assert!(fine > 0.999_999);
}

#[cfg(feature = "experimental-continuous")]
#[test]
fn leading_order_branch_overlap_remains_an_explicit_unproved_assumption() {
    use pid_core::experimental::continuous::{isx_redundancy_report, IsxConfig, IsxProvenance};
    use pid_core::stable::continuous::{Assumption, AssumptionState};

    let n = 64;
    let mut state = 0x1234_5678_9abc_def0;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut target = Vec::with_capacity(n);
    for _ in 0..n {
        let signal = lcg_uniform(&mut state);
        s1.push(signal);
        s2.push(signal + 1.0e-3 * lcg_uniform(&mut state));
        target.push(signal + 0.05 * lcg_uniform(&mut state));
    }
    let provenance = IsxProvenance::new(
        "source 1 identity gauge",
        "source 2 identity gauge",
        "target identity preprocessing",
        "additive continuous observation model",
        "independent fixture rows",
        None,
        Some("known-failure-evaluation".to_owned()),
    )
    .unwrap();
    let report = isx_redundancy_report(
        MatRef::new(&s1, n, 1).unwrap(),
        MatRef::new(&s2, n, 1).unwrap(),
        MatRef::new(&target, n, 1).unwrap(),
        &IsxConfig::assume_regular_full_dimensional(),
        &provenance,
        ResourceBudget::default(),
    )
    .unwrap();

    assert!(report.assumption_ledger.iter().any(|entry| {
        entry.assumption == Assumption::LowerOrderBranchIntersections
            && entry.state == AssumptionState::WarningPresent
    }));
    assert!(report.local_diagnostics.overlap_ratio.p90 > 0.5);
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_nonlocal_radii_remain_research_only() {
    use pid_core::stable::continuous::{KsgMethodStatus, ScientificStatus, WarningCode};

    let n = 16;
    let mut state = 0x7788_99aa_bbcc_ddee;
    let mut x = Vec::with_capacity(n * 2);
    let mut y = Vec::with_capacity(n * 2);
    for index in 0..n {
        let u = 3.0 * index as f64 / n as f64 + 0.01 * lcg_uniform(&mut state);
        let v = 2.5 * lcg_uniform(&mut state);
        x.extend_from_slice(&[u.cosh(), u.sinh()]);
        y.extend_from_slice(&[v.cosh(), v.sinh()]);
    }
    let provenance = KsgProvenance::new(
        "fixed hyperboloid coordinates",
        "declared smooth-manifold fixture",
        Some("known deterministic embedding, not trained on evaluation rows"),
    )
    .unwrap();
    let report = hyperbolic_ksg_mi_report(
        MatRef::new(&x, n, 2).unwrap(),
        MatRef::new(&y, n, 2).unwrap(),
        &HyperbolicKsgConfig::assume_smooth_manifold(HyperbolicCurvature::NegativeOne),
        &provenance,
    )
    .unwrap();

    assert_eq!(report.method_status, KsgMethodStatus::Experimental);
    assert_eq!(report.scientific_status, ScientificStatus::ResearchOnly);
    assert!(report.local_diagnostics.joint_radius.max > 1.0);
    assert!(report
        .report_warnings
        .contains(&WarningCode::ExperimentalEstimator));
}

#[cfg(feature = "experimental-pipelines")]
#[test]
fn same_sample_pls_can_fit_independent_noise_but_not_held_out_noise() {
    use pid_core::experimental::pipelines::PlsProjector;

    fn correlation(x: &[f64], y: &[f64]) -> f64 {
        let mean_x = x.iter().sum::<f64>() / x.len() as f64;
        let mean_y = y.iter().sum::<f64>() / y.len() as f64;
        let mut xy = 0.0;
        let mut xx = 0.0;
        let mut yy = 0.0;
        for (&left, &right) in x.iter().zip(y) {
            let left = left - mean_x;
            let right = right - mean_y;
            xy += left * right;
            xx += left * left;
            yy += right * right;
        }
        xy / (xx * yy).sqrt()
    }

    let (train_n, eval_n, dimensions) = (24, 200, 80);
    let mut state = 0x55aa_33cc_77ee_11ff;
    let train_x: Vec<f64> = (0..train_n * dimensions)
        .map(|_| lcg_uniform(&mut state) - 0.5)
        .collect();
    let train_y: Vec<f64> = (0..train_n)
        .map(|_| lcg_uniform(&mut state) - 0.5)
        .collect();
    let eval_x: Vec<f64> = (0..eval_n * dimensions)
        .map(|_| lcg_uniform(&mut state) - 0.5)
        .collect();
    let eval_y: Vec<f64> = (0..eval_n).map(|_| lcg_uniform(&mut state) - 0.5).collect();
    let train_x = MatRef::new(&train_x, train_n, dimensions).unwrap();
    let train_y_matrix = MatRef::new(&train_y, train_n, 1).unwrap();
    let projector = PlsProjector::fit(train_x, train_y_matrix, 1).unwrap();
    let train_scores = projector.transform(train_x).unwrap();
    let eval_scores = projector
        .transform(MatRef::new(&eval_x, eval_n, dimensions).unwrap())
        .unwrap();
    // Matrices are column vectors; use their backing values by iterating rows.
    let train_score_values: Vec<f64> = (0..train_n)
        .map(|row| train_scores.as_ref().row(row)[0])
        .collect();
    let eval_score_values: Vec<f64> = (0..eval_n)
        .map(|row| eval_scores.as_ref().row(row)[0])
        .collect();
    let train_correlation = correlation(&train_score_values, &train_y);
    let eval_correlation = correlation(&eval_score_values, &eval_y);

    assert!(train_correlation.abs() > 0.8, "train r={train_correlation}");
    assert!(
        eval_correlation.abs() < 0.2,
        "held-out r={eval_correlation}"
    );
}

#[cfg(feature = "experimental-pipelines")]
#[test]
fn invalid_block_permutation_null_is_rejected() {
    use pid_core::experimental::pipelines::{
        permutation_rows_pvalue_with, PermutationScheme, StatisticCallbackDeclaration,
    };
    use pid_core::ResourceEstimate;

    let x = [0.0, 1.0, 2.0, 3.0, 4.0];
    let y = [1.0, 0.0, 1.0, 0.0, 1.0];
    let matrices = [
        MatRef::new(&x, x.len(), 1).unwrap(),
        MatRef::new(&y, y.len(), 1).unwrap(),
    ];
    let result = permutation_rows_pvalue_with(
        &matrices,
        0,
        31,
        7,
        PermutationScheme::BlockShuffle { block_size: 2 },
        StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
        |inputs: &[MatRef<'_>]| Ok(inputs[0].row(0)[0]),
    );

    assert!(matches!(result, Err(PidError::InvalidConfig { .. })));
}

#[cfg(feature = "experimental-pipelines")]
#[test]
fn full_row_shuffle_is_anti_conservative_for_independent_autocorrelated_series() {
    use pid_core::experimental::pipelines::{
        permutation_rows_pvalue_with, PermutationCalibration, PermutationNullAssumption,
        PermutationScheme, StatisticCallbackDeclaration,
    };
    use pid_core::ResourceEstimate;

    fn ar1(seed: u64, rho: f64, burn_in: usize, n: usize) -> Vec<f64> {
        let mut state = seed;
        let mut value = 0.0;
        let mut series = Vec::with_capacity(n);
        for index in 0..burn_in + n {
            let innovation = lcg_uniform(&mut state) - 0.5;
            value = rho.mul_add(value, innovation);
            if index >= burn_in {
                series.push(value);
            }
        }
        series
    }

    fn absolute_pearson(inputs: &[MatRef<'_>]) -> pid_core::PidResult<f64> {
        let n = inputs[0].nrows();
        let mean_x = (0..n).map(|row| inputs[0].row(row)[0]).sum::<f64>() / n as f64;
        let mean_y = (0..n).map(|row| inputs[1].row(row)[0]).sum::<f64>() / n as f64;
        let mut covariance = 0.0;
        let mut variance_x = 0.0;
        let mut variance_y = 0.0;
        for row in 0..n {
            let x = inputs[0].row(row)[0] - mean_x;
            let y = inputs[1].row(row)[0] - mean_y;
            covariance += x * y;
            variance_x += x * x;
            variance_y += y * y;
        }
        Ok((covariance / (variance_x * variance_y).sqrt()).abs())
    }

    // X and Y are independent by construction, but each is strongly autocorrelated. Full-row
    // shuffling destroys the shuffled series' dependence and therefore compares the observed
    // statistic to an invalid, much easier null. The deterministic rejection frequency is a
    // counterexample, not a general calibration estimate.
    let trials = 24usize;
    let mut false_rejections = 0usize;
    for trial in 0..trials {
        let x = ar1(0x1234_5678 + 2 * trial as u64, 0.99, 512, 96);
        let y = ar1(0x9abc_def0 + 2 * trial as u64, 0.99, 512, 96);
        let matrices = [
            MatRef::new(&x, x.len(), 1).unwrap(),
            MatRef::new(&y, y.len(), 1).unwrap(),
        ];
        let result = permutation_rows_pvalue_with(
            &matrices,
            0,
            99,
            7 + 101 * trial as u64,
            PermutationScheme::FullShuffle,
            StatisticCallbackDeclaration::scalar(ResourceEstimate::ZERO),
            absolute_pearson,
        )
        .unwrap();

        assert_eq!(
            result.null.assumption,
            PermutationNullAssumption::ExchangeableRows
        );
        assert_eq!(
            result.null.calibration,
            PermutationCalibration::MonteCarloPValue
        );
        if result.tail_fraction.unwrap() <= 0.05 {
            false_rejections += 1;
        }
    }

    assert!(
        false_rejections >= 12,
        "invalid exchangeable-row null rejected {false_rejections}/{trials} independent AR(1) pairs"
    );
}
