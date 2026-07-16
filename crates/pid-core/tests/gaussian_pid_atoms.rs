#![cfg(feature = "experimental-continuous")]

//! Seeded finite-sample Gaussian PID-atom regression diagnostics.
//!
//! The existing Gaussian test (`tests/ksg.rs`) only checks the KSG *mutual information*
//! estimator. This file exercises PID atoms (Red / Unq1 / Unq2 / Syn) on fixed Gaussian
//! constructions, seeds, sample sizes, and tolerances. Analytic Gaussian MI identities and a
//! separately tested paired-Monte-Carlo shared-exclusions target provide bounded regression
//! references. These checks are not proofs of estimator consistency, convergence, or generic
//! finite-sample calibration.
//!
//! The identical-source construction is singular and therefore violates the continuous
//! estimator's regular full-dimensional support contract. Its test is ignored and retained only
//! as an explicitly out-of-domain diagnostic; it is not validation evidence.
//!
//! Conventions (AGENTS.md):
//! - All quantities are in **nats** (natural log).
//! - MI terms feeding the PID identity use `NegativeHandling::Allow` (enforced inside `pid2_isx`).
//! - Negative atoms are real; we never clamp.
//! - RNG is seeded explicitly (`Rng64`).
//!
//! Expected analytic values and numerical reference targets are labelled separately below.

use pid_core::experimental::continuous::raw_scalars::{ksg_mi, ksg_mi_concat_xy};
use pid_core::experimental::continuous::{pid2_isx_with_budget, IsxConfig, Pid2Config, Pid2Result};
use pid_core::stable::continuous::{KsgConfig, NegativeHandling};
use pid_core::stable::preprocessing::{ConstantColumnPolicy, Standardizer};
use pid_core::{MatRef, ResourceBudget};

mod common;

use common::Rng64;

/// Closed-form mutual information of a bivariate Gaussian channel via correlation:
///   I(X;Y) = -1/2 ln(1 - rho^2)      [nats]
/// Standard result; see e.g. Cover & Thomas, *Elements of Information Theory*, and Kraskov et al.
/// 2004, which uses this analytic form as a numerical benchmark.
fn gaussian_mi_from_corr(rho: f64) -> f64 {
    let r2 = rho * rho;
    debug_assert!(r2 < 1.0);
    -0.5 * (1.0 - r2).ln()
}

/// KSG config used for all MI/atom estimation here. `k=3` matches the rest of the suite and the
/// `IsxConfig` default (`pid2_isx` requires the KSG and ISX `k` to agree).
fn ksg_cfg() -> KsgConfig {
    KsgConfig::assume_regular_full_dimensional()
        .with_k(3)
        .with_negative_handling(NegativeHandling::Allow)
}

fn pid2_cfg() -> Pid2Config {
    Pid2Config {
        ksg: ksg_cfg(),
        isx: IsxConfig::assume_regular_full_dimensional(), // EhrlichKsg, k=3, Chebyshev.
    }
}

fn gaussian_comparison_budget() -> ResourceBudget {
    let default = ResourceBudget::default();
    ResourceBudget::new(
        default.max_bytes,
        100_000_000,
        default.max_operations_hint,
        default.max_threads,
    )
    .unwrap()
}

/// Out-of-domain diagnostic tolerance for the singular identical-source construction (nats).
///
/// This threshold is a scoped regression value, not a literature-derived coverage, calibration,
/// or convergence guarantee.
const ATOM_TOL: f64 = 0.08;

// =============================================================================================
// CASE 1 — IDENTICAL sources.
//
// Construction: X ~ N(0,1), T = X + sigma*Z with Z ~ N(0,1) independent, and S1 = S2 = X.
//
// At the level of the PID functional, self-redundancy identifies all of S1's information about T
// with the information shared by the duplicate source:
//
//   I(S1;T) = I(S2;T) = I(S1,S2;T) = I(X;T).
//
// Theory (holds for I^sx_∩ and PID measures satisfying self-redundancy:
// the self-redundancy axiom of Williams & Beer 2010, arXiv:1004.2515; Makkeh et al. 2021):
//   Red  = I(X;T)
//   Unq1 = I(S1;T) - Red = 0
//   Unq2 = I(S2;T) - Red = 0
//   Syn  = I(S1,S2;T) - I(S1;T) - I(S2;T) + Red = I(X;T) - 2 I(X;T) + I(X;T) = 0.
//
// Reference MI value (closed form): rho(X,T) = 1/sqrt(1+sigma^2), so
//   I(X;T) = -1/2 ln(1 - rho^2) = 1/2 ln(1 + 1/sigma^2).
// (Equivalent Gaussian-channel form 0.5 ln(1 + 1/sigma^2).)
// =============================================================================================
#[test]
#[ignore = "out-of-domain diagnostic: S2 == S1 is singular and violates regular full-dimensional support"]
fn diagnostic_identical_sources_under_false_continuous_support_assumption() {
    let mut rng = Rng64::new(0x1DEA_71CA_u64); // explicit, deterministic seed
    let n = 4000;
    let sigma = 0.7; // Fixed diagnostic value; I(X;T) = ½ln(1+1/σ²) ≈ 0.556 nats.
    let sigma2 = sigma * sigma;

    let mut x = Vec::with_capacity(n);
    let mut s2v = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let xi = rng.normal();
        let z = rng.normal();
        x.push(xi);
        s2v.push(xi); // S2 == S1 exactly
        t.push(xi + sigma * z);
    }

    let s1 = MatRef::new(&x, n, 1).unwrap();
    let s2 = MatRef::new(&s2v, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
    let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

    // WARNING: `S2 == S1` makes the joint source singular. Calling this configuration requires a
    // knowingly false support declaration, which is why this diagnostic is ignored and cannot
    // serve as estimator-validation evidence.
    let cfg = pid2_cfg();
    let out = pid2_isx_with_budget(
        s1.as_ref(),
        s2.as_ref(),
        t.as_ref(),
        &cfg,
        gaussian_comparison_budget(),
    )
    .unwrap();

    // Reference MI from theory (NOT from the estimator):
    let rho = 1.0 / (1.0 + sigma2).sqrt();
    let i_xt = gaussian_mi_from_corr(rho); // = 0.5 ln(1 + 1/sigma^2)

    // Theory atoms:
    let red_true = i_xt;
    let unq_true = 0.0;
    let syn_true = 0.0;

    assert!(
        (out.redundancy - red_true).abs() < ATOM_TOL,
        "identical-sources Red: est={:.4} theory I(X;T)={:.4} (tol {ATOM_TOL})",
        out.redundancy,
        red_true
    );
    assert!(
        (out.unique_s1 - unq_true).abs() < ATOM_TOL,
        "identical-sources Unq1: est={:.4} theory=0 (tol {ATOM_TOL})",
        out.unique_s1
    );
    assert!(
        (out.unique_s2 - unq_true).abs() < ATOM_TOL,
        "identical-sources Unq2: est={:.4} theory=0 (tol {ATOM_TOL})",
        out.unique_s2
    );
    assert!(
        (out.synergy - syn_true).abs() < ATOM_TOL,
        "identical-sources Syn: est={:.4} theory=0 (tol {ATOM_TOL})",
        out.synergy
    );

    // Algebraic check: the PID identity must hold up to floating-point error because the same
    // estimated terms appear on both sides.
    let i_s1s2_t = ksg_mi_concat_xy(s1.as_ref(), s2.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();
    let sum_atoms = out.redundancy + out.unique_s1 + out.unique_s2 + out.synergy;
    assert!(
        (sum_atoms - i_s1s2_t).abs() < 1e-9,
        "PID identity broken: sum_atoms={sum_atoms} I(S1,S2;T)={i_s1s2_t}"
    );
}

// =============================================================================================
// CASE 2 — INDEPENDENT additive sources (synergy-dominant).
//
// Construction: S1, S2 ~ N(0,1) independent, T = S1 + S2 + sigma*Z, Z ~ N(0,1) independent.
//   Var(T) = 2 + sigma^2.
//
// Closed-form MI terms:
//   rho(S1,T) = Cov(S1,T)/(sd S1 * sd T) = 1 / sqrt(2 + sigma^2)
//     => I(S1;T) = -1/2 ln(1 - 1/(2+sigma^2)) = -1/2 ln((1+sigma^2)/(2+sigma^2)).  (= I(S2;T))
//   I(S1,S2;T) = 1/2 ln(Var(T)/sigma^2) = 1/2 ln((2+sigma^2)/sigma^2).
//
// Shared-exclusions reference for this construction (see `tests/sxpid_gaussian_oracle.rs`):
//   A previous zero-redundancy fixture target was unsupported. The proposed continuous-limit
//   expression uses the paper's constant-relative-precision gauge. This fixture satisfies its
//   common-partition assumptions because both sources have identical standard-normal marginals in
//   known population-standardized coordinates. Under that declared gauge the expression is:
//       i^sx_∩(t:{1},{2})  ->  log[ w1·exp(i1) + w2·exp(i2) ],   w_a = f_{S_a}(s_a)/(f_{S1}+f_{S2}),
//   i.e. the log of a probability-weighted average of the pointwise-MI exponentials. For
//   the fixed independent-additive Gaussian fixture at sigma=0.6, a paired Monte Carlo
//   evaluation of that analytic integrand is about 0.225 nats. The bounded comparison in
//   `tests/sxpid_gaussian_oracle.rs` finds finite-sample KSG agreement at its declared seed and
//   tolerance. Its binned diagnostic shows a compatible numerical trend; neither result proves a
//   convergence rate, gauge independence, or generic large-sample correctness.
//
//   The bounded numerical target is nonzero and below the MMI value
//   min(I(S1;T), I(S2;T)); this is not a general ordering theorem. Only the MI *terms* are
//   population closed forms:
//     I(S1;T) = I(S2;T) = -1/2 ln((1+sigma^2)/(2+sigma^2)),   I(S1,S2;T) = 1/2 ln((2+sigma^2)/sigma^2).
//   The analytic co-information is negative, and the fixed-seed estimated atoms below are
//   synergy-dominant.
// =============================================================================================
#[test]
#[ignore = "diagnostic: compares two selected sample sizes; not convergence evidence"]
fn diagnostic_independent_redundancy_at_selected_sample_sizes() {
    for &(seed, n) in &[(0xD1A6_0001_u64, 2000usize), (0xD1A6_0002, 4000)] {
        let mut rng = Rng64::new(seed);
        let sigma = 0.6;
        let sigma2 = sigma * sigma;
        let mut s1v = Vec::with_capacity(n);
        let mut s2v = Vec::with_capacity(n);
        let mut t = Vec::with_capacity(n);
        for _ in 0..n {
            let a = rng.normal();
            let b = rng.normal();
            let z = rng.normal();
            s1v.push(a);
            s2v.push(b);
            t.push(a + b + sigma * z);
        }
        let s1 = MatRef::new(&s1v, n, 1).unwrap();
        let s2 = MatRef::new(&s2v, n, 1).unwrap();
        let t = MatRef::new(&t, n, 1).unwrap();
        let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
        let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
        let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();
        let out = pid2_isx_with_budget(
            s1.as_ref(),
            s2.as_ref(),
            t.as_ref(),
            &pid2_cfg(),
            gaussian_comparison_budget(),
        )
        .unwrap();
        let rho = 1.0 / (2.0 + sigma2).sqrt();
        let i_s1_t = gaussian_mi_from_corr(rho);
        let i_s1s2_t = 0.5 * ((2.0 + sigma2) / sigma2).ln();
        eprintln!(
            "n={n:>6} Red={:.4} Unq1={:.4} Unq2={:.4} Syn={:.4} | I(S1;T)={:.4} Syn_at_Red0={:.4}",
            out.redundancy,
            out.unique_s1,
            out.unique_s2,
            out.synergy,
            i_s1_t,
            i_s1s2_t - 2.0 * i_s1_t
        );
    }
}

/// Build the independent-additive system and estimate its atoms for the fixed regression fixture.
fn independent_additive_atoms() -> (Pid2Result, f64, f64, f64, f64) {
    let mut rng = Rng64::new(0x1DEC_0DED_u64);
    let n = 4000;
    let sigma = 0.6; // Fixed fixture value; no generic kNN-validity claim is attached to it.
    let sigma2 = sigma * sigma;

    let mut s1v = Vec::with_capacity(n);
    let mut s2v = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let z = rng.normal();
        s1v.push(a);
        s2v.push(b);
        t.push(a + b + sigma * z);
    }

    let s1 = MatRef::new(&s1v, n, 1).unwrap();
    let s2 = MatRef::new(&s2v, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();
    let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
    let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
    let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

    let out = pid2_isx_with_budget(
        s1.as_ref(),
        s2.as_ref(),
        t.as_ref(),
        &pid2_cfg(),
        gaussian_comparison_budget(),
    )
    .unwrap();

    // Closed-form reference MI (theory, NOT estimator):
    let rho_s_t = 1.0 / (2.0 + sigma2).sqrt();
    let i_s1_t = gaussian_mi_from_corr(rho_s_t); // = -0.5 ln((1+sigma^2)/(2+sigma^2))
    let i_s2_t = i_s1_t; // symmetry
    let i_s1s2_t = 0.5 * ((2.0 + sigma2) / sigma2).ln();

    // Same-estimator total MI, for the exact PID identity check.
    let i_s1s2_t_hat = ksg_mi_concat_xy(s1.as_ref(), s2.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();

    (out, i_s1_t, i_s2_t, i_s1s2_t, i_s1s2_t_hat)
}

#[test]
fn seeded_independent_additive_atoms_are_synergy_dominant() {
    let (out, i_s1_t, i_s2_t, i_s1s2_t, i_s1s2_t_hat) = independent_additive_atoms();

    // The paired Monte Carlo target in tests/sxpid_gaussian_oracle.rs is about 0.225 nats for its
    // declared finite sample. Only the MI terms here are population closed forms. The expression
    // below is the synergy value obtained by setting redundancy to zero; calling it a lower bound
    // would additionally assume non-negative population redundancy, which this test does not
    // prove.
    let syn_at_zero_red = i_s1s2_t - i_s1_t - i_s2_t;
    assert!(
        syn_at_zero_red > i_s1_t,
        "zero-redundancy synergy={syn_at_zero_red:.4} must exceed I(S1;T)={i_s1_t:.4}"
    );

    // ---- Bounded finite-sample checks at the fixed seed and n ----
    //
    // 1) Synergy dominates: the estimated Syn is the strictly largest atom and clearly positive.
    assert!(
        out.synergy > out.redundancy && out.synergy > out.unique_s1 && out.synergy > out.unique_s2,
        "expected synergy-dominant estimate: Red={:.4} Unq1={:.4} Unq2={:.4} Syn={:.4}",
        out.redundancy,
        out.unique_s1,
        out.unique_s2,
        out.synergy
    );
    assert!(
        out.synergy > 0.3,
        "expected clearly-positive synergy, got {:.4}",
        out.synergy
    );

    // 2) Unique atoms are small, consistent with the paired Monte Carlo redundancy target:
    //    Unq = I(S1;T) − Red ≈ 0.28 − 0.225 ≈ 0.05.
    assert!(
        out.unique_s1.abs() < 0.2 && out.unique_s2.abs() < 0.2,
        "expected small unique atoms: Unq1={:.4} Unq2={:.4}",
        out.unique_s1,
        out.unique_s2
    );

    // 3) Estimated redundancy is strictly BELOW the Barrett-2015 MMI redundancy
    //    R_MMI = min(I(S1;T), I(S2;T)). This is a direction-of-difference check, NOT an
    //    equality claim: I^sx and MMI are different measures, and for independent additive
    //    sources the fixed-seed I^sx estimate sits below MMI's analytic value.
    let r_mmi_true = i_s1_t.min(i_s2_t);
    assert!(
        out.redundancy < r_mmi_true,
        "expected I^sx Red < MMI Red: Red={:.4} R_MMI={:.4}",
        out.redundancy,
        r_mmi_true
    );

    // 4) PID identity: exact up to floating-point error, with the same estimates on both sides.
    let sum_atoms = out.redundancy + out.unique_s1 + out.unique_s2 + out.synergy;
    assert!(
        (sum_atoms - i_s1s2_t_hat).abs() < 1e-9,
        "PID identity broken: sum_atoms={sum_atoms} I(S1,S2;T)={i_s1s2_t_hat}"
    );
}

/// Regression guard for the corrected nonzero independent-additive fixture.
///
/// Despite the historical filename, `tests/sxpid_gaussian_oracle.rs` compares a fixed-seed KSG
/// estimate with paired Monte Carlo evaluation of an analytic integrand and obtains about
/// 0.22 nats within its scoped tolerance.
/// This test checks only the corresponding direction and range at its own seed. It does not prove
/// population strict positivity, estimator consistency, or a convergence rate.
#[test]
fn seeded_independent_additive_redundancy_is_positive_and_below_single_source_mi() {
    let (out, i_s1_t, _i_s2_t, _i_s1s2_t, _) = independent_additive_atoms();
    // This fixed-seed estimate is positive and below analytic I(S1;T), consistent with the
    // separate paired Monte Carlo fixture.
    assert!(
        out.redundancy > 0.1 && out.redundancy < i_s1_t,
        "independent-additive I^sx Red should be positive and < I(S1;T): Red={:.4} I(S1;T)={:.4}",
        out.redundancy,
        i_s1_t
    );
}

// =============================================================================================
// BARRETT-2015 GAUSSIAN MMI BIVARIATE-REDUNDANCY REFERENCE.
//
// !!! IMPORTANT: MMI is a DIFFERENT redundancy measure from I^sx_∩. This is a sanity comparison,
// NOT an assertion that I^sx == MMI. !!!
//
// Barrett (2015), "Exploration of synergistic and redundant information sharing in static and
// dynamical Gaussian systems", Phys. Rev. E 91, 052802. For the broad class of jointly-Gaussian
// systems with a UNIVARIATE target, Barrett shows the Minimum Mutual Information (MMI) PID gives
// the bivariate redundancy as simply the smaller of the two single-source MIs:
//
//   R_MMI(S1,S2;T) = min( I(S1;T), I(S2;T) ).
//
// We compute the closed-form MMI redundancy for both Gaussian systems above and compare it,
// purely as a sanity reference, against the KSG single-source MI estimates. We do NOT compare it
// to the I^sx atoms.
// =============================================================================================
#[test]
fn barrett2015_gaussian_mmi_redundancy_reference_labelled_mmi_not_isx() {
    // -- System A: identical sources (I(S1;T) = I(S2;T) = I(X;T)). --
    // Barrett MMI: R_MMI = min(I(S1;T), I(S2;T)) = I(X;T).
    {
        let mut rng = Rng64::new(0xBA77_E771);
        let n = 4000;
        let sigma = 0.7;
        let sigma2 = sigma * sigma;

        let mut x = Vec::with_capacity(n);
        let mut t = Vec::with_capacity(n);
        for _ in 0..n {
            let xi = rng.normal();
            let z = rng.normal();
            x.push(xi);
            t.push(xi + sigma * z);
        }
        let s1 = MatRef::new(&x, n, 1).unwrap();
        let t = MatRef::new(&t, n, 1).unwrap();
        let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
        let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

        let i_s1_t = ksg_mi(s1.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();
        // S2 == S1, so estimate is identical up to RNG reuse; use the same series for MMI ref.
        let i_s2_t = i_s1_t;

        // Theory (Barrett 2015): R_MMI = min(I(S1;T), I(S2;T)) = I(X;T) closed form.
        let rho = 1.0 / (1.0 + sigma2).sqrt();
        let r_mmi_true = gaussian_mi_from_corr(rho);
        let r_mmi_hat = i_s1_t.min(i_s2_t);

        // Sanity comparison ONLY (MMI != I^sx).
        assert!(
            (r_mmi_hat - r_mmi_true).abs() < 0.12,
            "[MMI ref, identical] R_MMI est={r_mmi_hat:.4} theory=min(I)=I(X;T)={r_mmi_true:.4}"
        );
    }

    // -- System B: independent additive sources. --
    // Barrett MMI: R_MMI = min(I(S1;T), I(S2;T)) = I(S1;T) (symmetric).
    // NOTE: the separate paired Monte Carlo fixture gives an I^sx redundancy near 0.225 nats,
    // below the MMI value min(I(S1;T), I(S2;T)) ≈ 0.276 nats. This is a bounded numerical
    // comparison, not a general ordering theorem; MMI and I^sx are different measures.
    {
        let mut rng = Rng64::new(0xBA77_E772);
        let n = 4000;
        let sigma = 0.6;
        let sigma2 = sigma * sigma;

        let mut s1v = Vec::with_capacity(n);
        let mut s2v = Vec::with_capacity(n);
        let mut t = Vec::with_capacity(n);
        for _ in 0..n {
            let a = rng.normal();
            let b = rng.normal();
            let z = rng.normal();
            s1v.push(a);
            s2v.push(b);
            t.push(a + b + sigma * z);
        }
        let s1 = MatRef::new(&s1v, n, 1).unwrap();
        let s2 = MatRef::new(&s2v, n, 1).unwrap();
        let t = MatRef::new(&t, n, 1).unwrap();
        let (s1, _) = Standardizer::fit_transform(s1, ConstantColumnPolicy::Error).unwrap();
        let (s2, _) = Standardizer::fit_transform(s2, ConstantColumnPolicy::Error).unwrap();
        let (t, _) = Standardizer::fit_transform(t, ConstantColumnPolicy::Error).unwrap();

        let i_s1_t = ksg_mi(s1.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();
        let i_s2_t = ksg_mi(s2.as_ref(), t.as_ref(), &ksg_cfg()).unwrap();

        // Theory (Barrett 2015): R_MMI = min(I(S1;T), I(S2;T)) = -0.5 ln((1+s^2)/(2+s^2)).
        let rho_s_t = 1.0 / (2.0 + sigma2).sqrt();
        let r_mmi_true = gaussian_mi_from_corr(rho_s_t);
        let r_mmi_hat = i_s1_t.min(i_s2_t);

        assert!(
            r_mmi_true > 0.05,
            "[MMI ref] independent-additive MMI redundancy is strictly positive (theory): {r_mmi_true:.4}"
        );
        assert!(
            (r_mmi_hat - r_mmi_true).abs() < 0.12,
            "[MMI ref, independent] R_MMI est={r_mmi_hat:.4} theory=min(I)={r_mmi_true:.4}"
        );
    }
}
