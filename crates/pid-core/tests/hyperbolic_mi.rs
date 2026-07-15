#![cfg(feature = "experimental-hyperbolic")]

use pid_core::experimental::hyperbolic::{
    hyperbolic_ksg_mi_report, HyperbolicCurvature, HyperbolicKsgConfig,
};
use pid_core::stable::continuous::{KsgProvenance, NegativeHandling};
use pid_core::MatRef;

const CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;

// Deterministic 64-bit LCG for test data generation (no external deps).
fn lcg_next(state: &mut u64) -> u64 {
    // PCG-style constants (any full-period LCG is fine for deterministic tests).
    *state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
    *state
}

fn u64_to_unit_f64(x: u64) -> f64 {
    // Map to [0,1) using the top 53 bits.
    let top = x >> 11;
    (top as f64) * (1.0 / ((1u64 << 53) as f64))
}

fn sample_scalar(state: &mut u64) -> f64 {
    // Deterministic scalar in [-1, 1].
    2.0 * u64_to_unit_f64(lcg_next(state)) - 1.0
}

#[test]
fn hyperbolic_report_preserves_explicit_negative_handling() {
    // Build two independent H^1 (2D Lorentz vectors) sequences.
    // x_i = (cosh u_i, sinh u_i), y_i = (cosh v_i, sinh v_i)
    let n = 200;
    let mut sx = 0x1234_5678_9abc_def0u64;
    let mut sy = 0x0fed_cba9_8765_4321u64;

    let mut x = Vec::with_capacity(n * 2);
    let mut y = Vec::with_capacity(n * 2);
    for _ in 0..n {
        let u = sample_scalar(&mut sx);
        let v = sample_scalar(&mut sy);
        x.push(u.cosh());
        x.push(u.sinh());
        y.push(v.cosh());
        y.push(v.sinh());
    }

    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 2).unwrap();

    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(CURVATURE)
        .with_k(3)
        .with_negative_handling(NegativeHandling::ClampToZero);
    let provenance = KsgProvenance::new(
        "upper-unit-hyperboloid coordinates",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();

    let report = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap();
    assert_eq!(report.estimate_nats, report.signed_estimate_nats.max(0.0));
}

#[test]
fn ksg_mi_rejects_invalid_hyperbolic_distances() {
    let x_data = [1.0, 0.0, 1.0, 0.1, 1.0, 0.2, 1.0, 0.3, 1.0, 0.4];
    let y_data = [0.0, 0.0, 0.0, 0.1, 0.0, 0.2, 0.0, 0.3, 0.0, 0.4];
    let x = MatRef::new(&x_data, 5, 2).unwrap();
    let y = MatRef::new(&y_data, 5, 2).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(CURVATURE)
        .with_k(2)
        .with_negative_handling(NegativeHandling::Allow);

    let provenance = KsgProvenance::new(
        "upper-unit-hyperboloid coordinates",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    assert!(hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).is_err());
}
