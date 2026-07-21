#![cfg(feature = "experimental-pipelines")]

//! Fixed-sample semi-analytic comparisons for continuous `I^sx_∩` redundancy on a
//! jointly-Gaussian system, plus a bounded discrete-quantization trend diagnostic.
//!
//! Under the constant-relative-precision gauge used in the cited continuous construction, the
//! chosen analytic functional for the `{{1},{2}}` redundancy has the form below when both source
//! marginals use the same refining partition:
//!
//!   i^sx_∩(t:{1},{2})  →  log[ w1·exp(i1) + w2·exp(i2) ],
//!   w_a = f_{S_a}(s_a) / (f_{S1}(s1)+f_{S2}(s2)),   i_a = pointwise MI i(s_a; t).
//!
//! The fixture satisfies that gauge choice because `S1` and `S2` have identical standard-normal
//! marginals and are already in known population-standardized coordinates. For standardized
//! jointly-Gaussian `(S_a, T)` with correlation `ρ_a`, both `i_a` and the marginal densities are
//! closed form. The pointwise integrand is therefore analytic, while its expectation is
//! approximated by paired Monte Carlo on fixed draws. The tests check finite-sample KSG agreement
//! at declared seeds, sample sizes, and tolerances; they do not claim the same limit for other
//! gauges or partitions and do not prove convergence or population-sign claims. The fixed samples
//! provide numerical evidence against a naive `Red→0` expectation in the non-degenerate
//! independent-additive regime.

use pid_core::experimental::continuous::{pid2_isx_with_budget, IsxConfig, Pid2Config};
use pid_core::experimental::pipelines::exploratory_same_sample_quantized_sxpid2 as quantized_sxpid2;
use pid_core::stable::continuous::{KsgConfig, NegativeHandling};
use pid_core::{MatRef, ResourceBudget};

mod common;
use common::Rng64;

/// Pointwise MI for a standardized bivariate Gaussian `(a,b)` with correlation `r` (nats):
///   i = -½ln(1-r²) - (r²(a²+b²) - 2 r a b) / (2(1-r²)).
fn pointwise_gaussian_mi(a: f64, b: f64, r: f64) -> f64 {
    let r2 = r * r;
    -0.5 * (1.0 - r2).ln() - (r2 * (a * a + b * b) - 2.0 * r * a * b) / (2.0 * (1.0 - r2))
}

/// Build the independent-additive Gaussian system in known population-standardized coordinates.
/// Returns `(s1, s2, t, n, rho)`.
fn additive_gaussian(
    seed: u64,
    n: usize,
    sigma: f64,
) -> (Vec<f64>, Vec<f64>, Vec<f64>, usize, f64) {
    let mut rng = Rng64::new(seed);
    let target_scale = (2.0 + sigma * sigma).sqrt();
    let (mut s1, mut s2, mut t) = (
        Vec::with_capacity(n),
        Vec::with_capacity(n),
        Vec::with_capacity(n),
    );
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let z = rng.normal();
        s1.push(a);
        s2.push(b);
        t.push((a + b + sigma * z) / target_scale);
    }
    let rho = 1.0 / target_scale;
    (s1, s2, t, n, rho)
}

/// Paired Monte Carlo estimate of continuous `I^sx_∩`: each pointwise Gaussian term is closed
/// form, while the expectation and its ordinary i.i.d. Monte Carlo standard error are evaluated
/// over this finite sample.
fn paired_mc_isx_red(s1: &[f64], s2: &[f64], t: &[f64], rho: f64) -> (f64, f64) {
    let n = s1.len();
    let mut mean = 0.0;
    let mut m2 = 0.0;
    for i in 0..n {
        let i1 = pointwise_gaussian_mi(s1[i], t[i], rho);
        let i2 = pointwise_gaussian_mi(s2[i], t[i], rho);
        // weights from standard-normal marginal densities (the 1/√(2π) constants cancel).
        let p1 = (-0.5 * s1[i] * s1[i]).exp();
        let p2 = (-0.5 * s2[i] * s2[i]).exp();
        let (w1, w2) = (p1 / (p1 + p2), p2 / (p1 + p2));
        let m = i1.max(i2);
        let value = m + (w1 * (i1 - m).exp() + w2 * (i2 - m).exp()).ln();
        let count = (i + 1) as f64;
        let delta = value - mean;
        mean += delta / count;
        m2 += delta * (value - mean);
    }
    let sample_variance = if n > 1 { m2 / (n - 1) as f64 } else { 0.0 };
    (mean, (sample_variance / n as f64).sqrt())
}

fn gaussian_comparison_budget() -> ResourceBudget {
    let default = ResourceBudget::default();
    ResourceBudget::new(
        default.max_bytes,
        250_000_000,
        default.max_operations_hint,
        default.max_threads,
    )
    .unwrap()
}

#[test]
fn ksg_isx_redundancy_matches_fixed_sample_reference_additive() {
    // Compare the continuous KSG I^sx estimate with the paired semi-analytic reference at this
    // fixed sample size and seed. The reference is positive (~0.22 nats), not zero, for
    // independent additive Gaussian sources.
    let sigma = 0.6;
    let (s1, s2, t, n, rho) = additive_gaussian(0x0AC1_E517, 4000, sigma);
    let (reference, reference_mc_se) = paired_mc_isx_red(&s1, &s2, &t, rho);

    // Fixed-seed regression checks on the paired Monte Carlo reference. These inequalities are
    // numerical observations for this sample, not a proof of population ordering.
    let i_s1_t = -0.5 * (1.0 - rho * rho).ln();
    assert!(
        reference > 0.15,
        "fixed-sample i^sx reference should exceed 0.15 nats; got {reference:.4}"
    );
    assert!(
        reference < i_s1_t,
        "fixed-sample reference {reference:.4} should be < analytic I(S1;T) {i_s1_t:.4}"
    );
    assert!(reference_mc_se < 0.02, "MC SE={reference_mc_se:.4}");

    let s1m = MatRef::new(&s1, n, 1).unwrap();
    let s2m = MatRef::new(&s2, n, 1).unwrap();
    let tm = MatRef::new(&t, n, 1).unwrap();
    let cfg = Pid2Config {
        ksg: KsgConfig::assume_regular_full_dimensional()
            .with_k(3)
            .with_negative_handling(NegativeHandling::Allow),
        isx: IsxConfig::assume_regular_full_dimensional(),
    };
    let out = pid2_isx_with_budget(s1m, s2m, tm, &cfg, gaussian_comparison_budget()).unwrap();
    eprintln!(
        "additive-Gaussian I^sx Red: KSG estimate = {:.4}, reference = {:.4}, MC SE = {:.4}, |diff| = {:.4}",
        out.redundancy,
        reference,
        reference_mc_se,
        (out.redundancy - reference).abs()
    );

    // On this fixed seed the agreement is ~0.004 nats (printed above). The 0.05 bound is a scoped
    // finite-sample regression tolerance: it leaves margin for kNN error while still excluding
    // zero, which is ~0.22 nats away. It is not a confidence interval or convergence rate.
    assert!(
        (out.redundancy - reference).abs() < 0.05,
        "KSG I^sx Red {:.4} should match the fixed-sample reference {:.4} within 0.05 nats",
        out.redundancy,
        reference
    );
}

#[test]
#[ignore = "diagnostic: KSG estimator vs fixed-sample paired Gaussian references across several sigma"]
fn multi_sigma_ksg_vs_fixed_sample_reference() {
    for &sigma in &[0.3_f64, 0.6, 1.0, 1.5] {
        let (s1, s2, t, n, rho) = additive_gaussian(0x5EED_0001, 6000, sigma);
        let (reference, reference_mc_se) = paired_mc_isx_red(&s1, &s2, &t, rho);
        let s1m = MatRef::new(&s1, n, 1).unwrap();
        let s2m = MatRef::new(&s2, n, 1).unwrap();
        let tm = MatRef::new(&t, n, 1).unwrap();
        let cfg = Pid2Config {
            ksg: KsgConfig::assume_regular_full_dimensional()
                .with_k(3)
                .with_negative_handling(NegativeHandling::Allow),
            isx: IsxConfig::assume_regular_full_dimensional(),
        };
        let out = pid2_isx_with_budget(s1m, s2m, tm, &cfg, gaussian_comparison_budget()).unwrap();
        eprintln!(
            "sigma={sigma:.1}: KSG Red={:.4}  reference={:.4}  MC SE={:.4}  |diff|={:.4}",
            out.redundancy,
            reference,
            reference_mc_se,
            (out.redundancy - reference).abs()
        );
    }
}

#[test]
#[ignore = "diagnostic: discrete i^sx moves toward the fixed-sample reference over a bounded bin range"]
fn discrete_isx_moves_toward_reference_over_bounded_bins() {
    let sigma = 0.6;
    let (s1, s2, t, n, rho) = additive_gaussian(0x0AC1_E518, 6000, sigma);
    let (reference, reference_mc_se) = paired_mc_isx_red(&s1, &s2, &t, rho);
    let s1m = MatRef::new(&s1, n, 1).unwrap();
    let s2m = MatRef::new(&s2, n, 1).unwrap();
    let tm = MatRef::new(&t, n, 1).unwrap();
    eprintln!(
        "fixed-sample continuous reference = {reference:.4} nats (MC SE {reference_mc_se:.4})"
    );
    let mut first = None;
    let mut previous = None;
    for &bins in &[6usize, 8, 10, 12, 14] {
        let r = quantized_sxpid2(s1m, s2m, tm, bins)
            .unwrap()
            .into_categorical_result();
        eprintln!(
            "  quantized_sxpid2 bins={bins:>2}: Red={:.4}",
            r.red.net_nats()
        );
        if first.is_none() {
            first = Some(r.red.net_nats());
        }
        previous = Some(r.red.net_nats());
    }
    let first = first.unwrap();
    let last = previous.unwrap();
    assert!(
        last < reference,
        "bounded trajectory does not reach reference"
    );
    assert!(
        (reference - last).abs() < (reference - first).abs(),
        "bounded trajectory must finish closer to the reference"
    );
}
