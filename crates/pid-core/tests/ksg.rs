#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::raw_scalars::{
    co_information_pairwise, ksg_local_mi_terms, ksg_mi, ksg_mi_concat_xy,
};
use pid_core::stable::continuous::{KsgConfig, NegativeHandling, SupportContract};
use pid_core::stable::preprocessing::{ConstantColumnPolicy, Standardizer};
use pid_core::{MatRef, PidError};

mod common;

use common::Rng64;

fn gaussian_mi_from_corr(rho: f64) -> f64 {
    let r2 = rho * rho;
    debug_assert!(r2 < 1.0);
    -0.5 * (1.0 - r2).ln()
}

fn gaussian_channel_mi(sigma: f64) -> f64 {
    debug_assert!(sigma.is_finite());
    debug_assert!(sigma > 0.0);
    0.5 * (1.0 + 1.0 / (sigma * sigma)).ln()
}

#[test]
fn ksg_default_preserves_signed_finite_sample_estimates() {
    assert_eq!(
        KsgConfig::default().negative_handling,
        NegativeHandling::Allow
    );
}

#[test]
fn ksg_default_fails_closed_without_a_support_assertion() {
    let x = MatRef::new(&[0.0, 0.2, 0.5, 0.9], 4, 1).unwrap();
    let y = MatRef::new(&[0.1, 0.35, 0.6, 1.1], 4, 1).unwrap();

    assert!(matches!(
        ksg_mi(x, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));
}

#[test]
fn ksg_exclusive_counts_reach_the_exact_integer_harmonic_local_term() {
    // This fixed sample is a count/arithmetic conformance witness, not evidence for a population
    // support model or estimator calibration. Every coordinate and joint row is unique, and each
    // k=2 joint shell has exactly one strict-interior and one boundary neighbor.
    let x: [f64; 8] = [7.0, 194.0, 144.0, 75.0, 61.0, 138.0, 38.0, 9.0];
    let y: [f64; 8] = [17.0, 48.0, 166.0, 120.0, 2.0, 199.0, 43.0, 93.0];
    let expected_counts = [
        (54.0, 2, 3),
        (119.0, 2, 6),
        (69.0, 2, 2),
        (69.0, 5, 2),
        (54.0, 3, 3),
        (79.0, 4, 1),
        (41.0, 4, 2),
        (66.0, 3, 3),
    ];

    for query in 0..x.len() {
        let mut joint_distances = Vec::with_capacity(x.len() - 1);
        for neighbor in 0..x.len() {
            if query != neighbor {
                let dx = (x[query] - x[neighbor]).abs();
                let dy = (y[query] - y[neighbor]).abs();
                joint_distances.push(dx.max(dy));
            }
        }
        joint_distances.sort_by(f64::total_cmp);
        let radius = joint_distances[1];
        let interior = joint_distances
            .iter()
            .filter(|&&distance| distance < radius)
            .count();
        let boundary = joint_distances
            .iter()
            .filter(|&&distance| distance == radius)
            .count();
        let nx = (0..x.len())
            .filter(|&neighbor| query != neighbor && (x[query] - x[neighbor]).abs() < radius)
            .count();
        let ny = (0..y.len())
            .filter(|&neighbor| query != neighbor && (y[query] - y[neighbor]).abs() < radius)
            .count();

        assert_eq!((interior, boundary), (1, 1), "query {query}");
        assert_eq!((radius, nx, ny), expected_counts[query], "query {query}");
    }

    let x = MatRef::new(&x, 8, 1).unwrap();
    let y = MatRef::new(&y, 8, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(2)
        .with_negative_handling(NegativeHandling::Allow);
    let terms = ksg_local_mi_terms(x, y, &config).unwrap();

    assert_eq!(terms.len(), 8);
    assert_eq!(
        terms[5].to_bits(),
        0x3fe0_4e04_e04e_04e0,
        "row 5 has exact-real target H_7 - H_4 = 107/210; pin the selected binary64 association"
    );
}

#[test]
fn ksg_rejects_every_declared_incompatible_support_type() {
    let x = MatRef::new(&[0.0, 0.2, 0.5, 0.9], 4, 1).unwrap();
    let y = MatRef::new(&[0.1, 0.35, 0.6, 1.1], 4, 1).unwrap();
    let incompatible_contracts = [
        SupportContract::KnownAtomicOrMixed,
        SupportContract::KnownQuantized,
        SupportContract::KnownSingularOrLowerDimensional,
    ];
    for support_contract in incompatible_contracts {
        let config = KsgConfig::default().with_support_contract(support_contract);
        assert!(matches!(
            ksg_mi(x, y, &config),
            Err(PidError::UnsupportedSupportContract { contract, .. })
                if contract == support_contract
        ));
    }
}

#[test]
fn ksg_mi_is_small_for_independent_uniforms() {
    let mut rng = Rng64::new(42);
    let n = 250;
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        x.push(rng.next_f64());
        y.push(rng.next_f64());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi = ksg_mi(x, y, &cfg).unwrap();

    assert!(mi.is_finite());
    assert!(mi.abs() < 0.6, "expected near-0 MI, got {mi}");
}

#[test]
fn ksg_mi_is_larger_for_noisy_copy() {
    let mut rng = Rng64::new(123);
    let n = 300;
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let xi = rng.next_f64();
        let yi = xi + 0.05 * rng.normal();
        x.push(xi);
        y.push(yi);
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi = ksg_mi(x, y, &cfg).unwrap();

    assert!(mi.is_finite());
    assert!(mi > 0.5, "expected MI > 0.5 nats, got {mi}");
}

#[test]
fn ksg_mi_matches_gaussian_correlation_approximately() {
    // Analytic MI for 1D jointly-Gaussian variables via correlation:
    // I(X;Y) = -0.5 ln(1 - rho^2)
    let mut rng = Rng64::new(2026);
    let n = 600;
    let sigma_x = 0.5;
    let sigma_y = 0.8;

    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        x.push(base + sigma_x * rng.normal());
        y.push(base + sigma_y * rng.normal());
    }

    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let (x, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();
    let (y, _) = Standardizer::fit_transform(y, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let mi_hat = ksg_mi(x.as_ref(), y.as_ref(), &cfg).unwrap();

    let rho = 1.0 / ((1.0 + sigma_x * sigma_x) * (1.0 + sigma_y * sigma_y)).sqrt();
    let mi_true = gaussian_mi_from_corr(rho);

    assert!(mi_hat.is_finite());
    // The tolerance must stay BELOW the effect size (mi_true ≈ 0.33 nats) or the check is
    // vacuous — a dead-zero estimator, a 2× scale bug, and a bits-for-nats mixup would all
    // pass at 0.35. 0.12 nats is comfortably above the KSG finite-sample error here while
    // excluding all three failure modes; the second assertion pins the zero-collapse case.
    assert!(
        (mi_hat - mi_true).abs() < 0.12,
        "MI mismatch: estimated={mi_hat:.4} true={mi_true:.4} rho={rho:.4}"
    );
    assert!(
        mi_hat > 0.5 * mi_true,
        "MI collapsed toward zero: estimated={mi_hat:.4} true={mi_true:.4}"
    );
}

#[test]
fn exp0_strong_dependence_gaussian_channel_sweep_smoke() {
    // Strong dependence (very large true MI) can break kNN MI even at low dimension.
    // This test is not asserting "perfect accuracy"; it checks:
    // - finiteness (no NaNs/Infs)
    // - broadly increasing MI as sigma shrinks
    // - rough agreement with the analytic Gaussian-channel MI at moderate MI values
    //
    // Analytic: X ~ N(0,1), Y = X + σN, N~N(0,1): I(X;Y) = 0.5 ln(1 + 1/σ²).
    let mut rng = Rng64::new(0x51A7_2026);
    let n = 800;

    let mut x_raw = Vec::with_capacity(n);
    let mut noise = Vec::with_capacity(n);
    for _ in 0..n {
        x_raw.push(rng.normal());
        noise.push(rng.normal());
    }

    let x = MatRef::new(&x_raw, n, 1).unwrap();
    let (x, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);

    let sigmas = [1.0, 0.3, 0.1];
    let mut last = None;
    for &sigma in &sigmas {
        let y_raw: Vec<f64> = x_raw
            .iter()
            .zip(noise.iter())
            .map(|(&xi, &ni)| xi + sigma * ni)
            .collect();

        let y = MatRef::new(&y_raw, n, 1).unwrap();
        let (y, _) = Standardizer::fit_transform(y, ConstantColumnPolicy::Error).unwrap();

        let mi_hat = ksg_mi(x.as_ref(), y.as_ref(), &cfg).unwrap();
        let mi_true = gaussian_channel_mi(sigma);

        assert!(mi_hat.is_finite(), "sigma={sigma} mi_hat={mi_hat}");

        if let Some(prev) = last {
            assert!(
                mi_hat >= prev - 0.25,
                "expected MI to increase as sigma shrinks: sigma={sigma} mi_hat={mi_hat} prev={prev}"
            );
        }
        last = Some(mi_hat);

        assert!(
            (mi_hat - mi_true).abs() < 1.0,
            "MI mismatch: sigma={sigma} estimated={mi_hat:.4} true={mi_true:.4}"
        );
    }
}

#[test]
fn exp0_co_information_smoke() {
    // Minimal Experiment 0-ish smoke: CI is finite.
    let mut rng = Rng64::new(999);
    let n = 250;
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        let noise = 0.01 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional();
    let ci = co_information_pairwise(s1, s2, t, &cfg).unwrap();
    assert!(ci.is_finite());
}

#[test]
fn co_information_matches_gaussian_sum_channel_approximately() {
    // S1,S2 ~ N(0,1) independent. T = S1 + S2 + N, N~N(0, sigma^2).
    //
    // Analytic:
    // I(S1;T) = -0.5 ln((1+sigma^2)/(2+sigma^2))
    // I(S1,S2;T) = 0.5 ln((2+sigma^2)/sigma^2)
    // CI = I(S1;T)+I(S2;T)-I(S1,S2;T)
    let mut rng = Rng64::new(2027);
    let n = 700;
    let sigma = 0.6;
    let sigma2 = sigma * sigma;

    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let noise = sigma * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
    let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let ci_hat = co_information_pairwise(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();

    let i_s1_t = -0.5 * ((1.0 + sigma2) / (2.0 + sigma2)).ln();
    let i_s1s2_t = 0.5 * ((2.0 + sigma2) / sigma2).ln();
    let ci_true = 2.0 * i_s1_t - i_s1s2_t;

    assert!(ci_hat.is_finite());
    // Same principle as the MI test above: tolerance below the effect size (|ci_true| ≈ 0.39
    // nats), plus an explicit bound that excludes a zero-collapsed estimator and pins the sign.
    assert!(
        (ci_hat - ci_true).abs() < 0.20,
        "CI mismatch: estimated={ci_hat:.4} true={ci_true:.4}"
    );
    assert!(
        ci_hat < 0.5 * ci_true,
        "CI collapsed toward zero (should be clearly negative): estimated={ci_hat:.4} true={ci_true:.4}"
    );
}

#[test]
fn ksg_rejects_zero_column_inputs() {
    let n = 10;
    let x: Vec<f64> = Vec::new();
    let y: Vec<f64> = Vec::new();
    let x = MatRef::new(&x, n, 0).unwrap();
    let y = MatRef::new(&y, n, 0).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn ksg_rejects_every_nonzero_or_nonfinite_tie_epsilon() {
    let n = 20;
    let x: Vec<f64> = (0..n).map(|i| i as f64).collect();
    let y: Vec<f64> = (0..n).map(|i| (i as f64) * 0.5).collect();
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    for tie_epsilon in [-1.0, 1.0e-12, f64::NAN, f64::INFINITY] {
        let cfg = KsgConfig::assume_regular_full_dimensional()
            .with_k(3)
            .with_tie_epsilon(tie_epsilon)
            .with_negative_handling(NegativeHandling::Allow);
        let err = ksg_mi(x, y, &cfg).unwrap_err();
        assert!(
            matches!(err, PidError::InvalidConfig { .. }),
            "tie_epsilon={tie_epsilon:?}: unexpected error: {err:?}"
        );
    }
}

#[test]
fn ksg_accepts_a_smallest_subnormal_positive_radius() {
    let smallest = f64::from_bits(1);
    let x = [0.0, smallest];
    let y = [0.0, smallest];
    let x = MatRef::new(&x, 2, 1).unwrap();
    let y = MatRef::new(&y, 2, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(1)
        .with_negative_handling(NegativeHandling::Allow);

    let estimate = ksg_mi(x, y, &config).unwrap();

    assert!(estimate.is_finite());
}

#[test]
fn ksg_rejects_a_positive_ambiguous_kth_neighbor_shell() {
    // All joint rows are distinct and every non-self distance is positive. At query 0 and k=2,
    // the joint distances are [0.5, 1, 1, 3], making the positive outer shell ambiguous.
    let x = [0.0, 0.5, 1.0, 0.3, 3.0];
    let y = [0.0, 0.4, 0.2, 1.0, 3.0];
    let x = MatRef::new(&x, 5, 1).unwrap();
    let y = MatRef::new(&y, 5, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(2)
        .with_negative_handling(NegativeHandling::Allow);

    let error = ksg_mi(x, y, &config).unwrap_err();

    assert!(matches!(
        error,
        PidError::AmbiguousKthNeighborShell {
            query_index: 0,
            k: 2,
            radius: 1.0,
            interior_count: 1,
            boundary_count: 2,
            ..
        }
    ));
}

#[test]
fn ksg_handles_heavily_quantized_data_cleanly() {
    // Stress test: feed heavily-quantized data so that many points coincide exactly
    // (the realistic failure mode when continuous signals are rounded to a coarse grid
    // or recorded by a low-resolution sensor). The contract is that the estimator must
    // EITHER reject a collapsed or ambiguous kNN shell with its structured error OR return a
    // finite, stable estimate — but never panic, never produce NaN/Inf, and never silently report
    // a value that pretends the data was continuous.
    //
    // We sweep quantization coarseness from very coarse (few levels → many exact ties)
    // to fairly fine (few ties). At every coarseness, both outcomes are acceptable; we
    // only forbid panics and non-finite "successes".
    let mut rng = Rng64::new(0xC0FFEE);
    let n = 200;

    let mut x_cont = Vec::with_capacity(n);
    let mut y_cont = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.normal();
        x_cont.push(base);
        y_cont.push(base + 0.3 * rng.normal());
    }

    let cfg = KsgConfig::default()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(SupportContract::KnownQuantized);

    // levels=2 is extremely coarse (data collapses onto ~2 grid points per axis →
    // heavy duplication); levels=64 is fine enough that ties are rare.
    for &levels in &[2.0f64, 3.0, 5.0, 16.0, 64.0] {
        let quantize = |v: f64| -> f64 { (v * levels).round() / levels };
        let xq: Vec<f64> = x_cont.iter().map(|&v| quantize(v)).collect();
        let yq: Vec<f64> = y_cont.iter().map(|&v| quantize(v)).collect();

        let x = MatRef::new(&xq, n, 1).unwrap();
        let y = MatRef::new(&yq, n, 1).unwrap();

        assert!(matches!(
            ksg_mi(x, y, &cfg),
            Err(PidError::UnsupportedSupportContract {
                contract: SupportContract::KnownQuantized,
                ..
            })
        ));
    }
}

#[test]
fn ksg_errors_on_duplicate_points() {
    // Duplicate points make the kNN radius zero, which breaks strict-inequality counting.
    let n = 30;
    let x = vec![0.0f64; n];
    let y = vec![0.0f64; n];
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow);
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(
            err,
            PidError::ObservedContinuousSampleIncompatibility { .. }
        ),
        "unexpected error: {err:?}"
    );
}

#[test]
fn marginal_atoms_are_rejected_even_when_joint_rows_and_shells_are_unique() {
    // Bernoulli X plus a continuously perturbed Y has eight unique joint rows and unique positive
    // k=3 joint shells. The atomic X marginal still invalidates standard continuous KSG.
    let x = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let y = [0.01, 0.08, 0.19, 0.41, 1.03, 1.11, 1.29, 1.52];
    let x = MatRef::new(&x, 8, 1).unwrap();
    let y = MatRef::new(&y, 8, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(3);

    let error = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(matches!(
        error,
        PidError::ObservedContinuousSampleIncompatibility {
            input_index: 0,
            coordinate: Some(0),
            unique_values: 2,
            max_multiplicity: 4,
            ..
        }
    ));
}

#[test]
fn public_local_and_concat_apis_cannot_bypass_support_preflight() {
    let x1_data = [0.03, 0.17, 0.31, 0.52, 0.76, 1.01, 1.29, 1.62];
    let x2_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21, 0.07];
    let y_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
    let x1 = MatRef::new(&x1_data, 8, 1).unwrap();
    let x2 = MatRef::new(&x2_data, 8, 1).unwrap();
    let y = MatRef::new(&y_data, 8, 1).unwrap();

    assert!(matches!(
        ksg_local_mi_terms(x1, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));
    assert!(matches!(
        ksg_mi_concat_xy(x1, x2, y, &KsgConfig::default()),
        Err(PidError::SupportContractRequired { .. })
    ));

    let tied_data = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let tied = MatRef::new(&tied_data, 8, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional();
    assert!(matches!(
        ksg_local_mi_terms(tied, y, &cfg),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));
    assert!(matches!(
        ksg_mi_concat_xy(tied, x2, y, &cfg),
        Err(PidError::ObservedContinuousSampleIncompatibility { .. })
    ));

    let short_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21];
    let short = MatRef::new(&short_data, 7, 1).unwrap();
    let invalid_tie_cfg = KsgConfig::assume_regular_full_dimensional().with_tie_epsilon(1.0e-6);
    assert!(matches!(
        ksg_mi_concat_xy(x1, short, y, &invalid_tie_cfg),
        Err(PidError::RowCountMismatch { .. })
    ));
}
