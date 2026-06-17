use pid_core::{
    co_information_pairwise, ksg_mi, KsgConfig, MatRef, NegativeHandling, PidError, Standardizer,
};

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

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
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

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
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
    let (x, _) = Standardizer::fit_transform(x).unwrap();
    let (y, _) = Standardizer::fit_transform(y).unwrap();

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let mi_hat = ksg_mi(x.as_ref(), y.as_ref(), &cfg).unwrap();

    let rho = 1.0 / ((1.0 + sigma_x * sigma_x) * (1.0 + sigma_y * sigma_y)).sqrt();
    let mi_true = gaussian_mi_from_corr(rho);

    assert!(mi_hat.is_finite());
    assert!(
        (mi_hat - mi_true).abs() < 0.35,
        "MI mismatch: estimated={mi_hat:.4} true={mi_true:.4} rho={rho:.4}"
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
    let (x, _) = Standardizer::fit_transform(x).unwrap();

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };

    let sigmas = [1.0, 0.3, 0.1];
    let mut last = None;
    for &sigma in &sigmas {
        let y_raw: Vec<f64> = x_raw
            .iter()
            .zip(noise.iter())
            .map(|(&xi, &ni)| xi + sigma * ni)
            .collect();

        let y = MatRef::new(&y_raw, n, 1).unwrap();
        let (y, _) = Standardizer::fit_transform(y).unwrap();

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

    let cfg = KsgConfig::default();
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
    let (s1, _) = Standardizer::fit_transform(s1).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2).unwrap();
    let (t, _) = Standardizer::fit_transform(t).unwrap();

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let ci_hat = co_information_pairwise(s1.as_ref(), s2.as_ref(), t.as_ref(), &cfg).unwrap();

    let i_s1_t = -0.5 * ((1.0 + sigma2) / (2.0 + sigma2)).ln();
    let i_s1s2_t = 0.5 * ((2.0 + sigma2) / sigma2).ln();
    let ci_true = 2.0 * i_s1_t - i_s1s2_t;

    assert!(ci_hat.is_finite());
    assert!(
        (ci_hat - ci_true).abs() < 0.45,
        "CI mismatch: estimated={ci_hat:.4} true={ci_true:.4}"
    );
}

#[test]
fn ksg_rejects_zero_column_inputs() {
    let n = 10;
    let x: Vec<f64> = Vec::new();
    let y: Vec<f64> = Vec::new();
    let x = MatRef::new(&x, n, 0).unwrap();
    let y = MatRef::new(&y, n, 0).unwrap();

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn ksg_rejects_negative_tie_epsilon() {
    let n = 20;
    let x: Vec<f64> = (0..n).map(|i| i as f64).collect();
    let y: Vec<f64> = (0..n).map(|i| (i as f64) * 0.5).collect();
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig {
        k: 3,
        tie_epsilon: -1.0,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::InvalidConfig { .. }),
        "unexpected error: {err:?}"
    );
}

#[test]
fn ksg_errors_on_duplicate_points_without_jitter() {
    // Duplicate points make the kNN radius zero, which breaks strict-inequality counting.
    let n = 30;
    let x = vec![0.0f64; n];
    let y = vec![0.0f64; n];
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();

    let cfg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..Default::default()
    };
    let err = ksg_mi(x, y, &cfg).unwrap_err();
    assert!(
        matches!(err, PidError::NumericalInstability { .. }),
        "unexpected error: {err:?}"
    );
}
