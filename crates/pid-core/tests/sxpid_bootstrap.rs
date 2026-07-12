#![cfg(feature = "experimental-pipelines")]

//! Dependence-aware raw resampling-percentile diagnostics for discrete SxPID atoms.

use pid_core::experimental::pipelines::{
    bootstrap_quantized_sxpid2, exploratory_same_sample_quantized_sxpid2 as quantized_sxpid2,
    BlockLengthSelection, BootstrapConfig, ResamplingValidityDeclaration,
};
use pid_core::MatRef;

fn and_gate(reps: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>, usize) {
    let rows = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)];
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..reps {
        for &(a, b, c) in &rows {
            s1.push(a as f64);
            s2.push(b as f64);
            t.push(c as f64);
        }
    }
    (s1.clone(), s2.clone(), t.clone(), 4 * reps)
}

#[test]
fn bootstrap_sxpid2_point_estimate_and_raw_percentiles() {
    let (s1, s2, t, n) = and_gate(40); // n = 160
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = BootstrapConfig::new(
        200,
        1, // i.i.d. rows
        7,
        0.05,
        ResamplingValidityDeclaration::independent_rows(BlockLengthSelection::FixedAPriori),
    )
    .unwrap();
    let boot = bootstrap_quantized_sxpid2(s1, s2, t, 2, &cfg).unwrap();

    // Point estimate equals the direct estimator exactly.
    let direct = quantized_sxpid2(s1, s2, t, 2).unwrap();
    assert!((boot.redundancy.point_estimate - direct.red.net).abs() < 1e-12);
    assert!((boot.synergy.point_estimate - direct.syn.net).abs() < 1e-12);

    // Discrete data ⇒ every resample is valid (no NaN/instability from duplicates).
    for s in [
        &boot.redundancy,
        &boot.unique_s1,
        &boot.unique_s2,
        &boot.synergy,
    ] {
        assert_eq!(
            s.n_valid, cfg.n_boot,
            "all discrete resamples should be valid"
        );
        assert!(s.resample_standard_deviation.is_finite() && s.resample_standard_deviation >= 0.0);
        assert!(
            s.percentile_lower <= s.percentile_upper,
            "raw percentiles must be ordered"
        );
        assert!(
            s.percentile_lower <= s.resample_mean + 1e-12
                && s.resample_mean <= s.percentile_upper + 1e-12
        );
    }
    // A balanced gate resampled with replacement has nonzero spread in the redundancy atom.
    assert!(boot.redundancy.resample_standard_deviation > 0.0);
}
