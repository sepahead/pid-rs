//! Hyperbolic geometry helpers (Lorentz / hyperboloid model).
//!
//! This module supports **experimental MI-only** pipelines where embeddings are represented in a
//! hyperbolic space and neighborhood queries should use the **hyperbolic geodesic distance**.
//!
//! Important: this does **not** make the paper-validated shared-exclusions `I^sx_∩` estimator
//! “hyperbolic-correct” automatically. Treat hyperbolic + `I^sx_∩` as research-gated.

/// Minkowski / Lorentz bilinear form for vectors in the Lorentz model of hyperbolic space.
///
/// Convention: `⟨x,y⟩_L = -x0*y0 + Σ_{i>=1} xi*yi`.
#[inline]
pub fn lorentz_dot(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() || a.len() < 2 {
        return f64::NAN;
    }
    let mut s = -a[0] * b[0];
    for i in 1..a.len() {
        s += a[i] * b[i];
    }
    s
}

/// Geodesic distance in the Lorentz (hyperboloid) model for curvature -1.
///
/// For valid points on the hyperboloid (`⟨x,x⟩_L = -1`, `x0>0`), the distance is
/// `d(x,y) = arcosh( -⟨x,y⟩_L )`. This implementation uses two numerically robust ingredients:
///
/// 1. **Per-point validity gate.** Each input must lie on the upper unit hyperboloid. Its time
///    coordinate is checked against the stable identity `x0 = hypot(‖x_spatial‖, 1)`. Points whose
///    unit offset is too ill-conditioned to verify in `f64` are rejected instead of being silently
///    admitted.
/// 2. **Hyperbolic polar distance.** Write a point as
///    `x = (cosh(ρ), sinh(ρ) n)`, where `n` is a Euclidean unit vector. The implementation uses
///
///    `sinh²(d/2) = sinh²((ρx−ρy)/2) + sinh(ρx)sinh(ρy)‖nx−ny‖²/4`.
///
///    This avoids the catastrophic cancellation in `acosh(−⟨x,y⟩)`, the Lorentz difference
///    quadratic form, and the Poincaré-ball map for nearby points far from the origin.
///
/// Returns `NaN` if either row is off the upper unit hyperboloid, is too ill-conditioned for that
/// constraint to be verified in `f64`, or contains a non-finite coordinate.
#[inline]
pub fn hyperbolic_distance_lorentz(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() {
        return f64::NAN;
    }
    let Some(a_radius) = validated_spatial_radius(a) else {
        return f64::NAN;
    };
    let Some(b_radius) = validated_spatial_radius(b) else {
        return f64::NAN;
    };
    if a == b {
        return 0.0;
    }

    let radial_half_chord = ((a_radius.asinh() - b_radius.asinh()) * 0.5).abs().sinh();

    let angular_half_chord = if a_radius == 0.0 || b_radius == 0.0 {
        0.0
    } else {
        let mut direction_difference = 0.0_f64;
        for i in 1..a.len() {
            direction_difference = direction_difference.hypot(a[i] / a_radius - b[i] / b_radius);
        }
        // Form the geometric-mean radius before applying the (at most unit-sized) angular
        // half-chord. With subnormal radii, multiplying by 0.5 first can round a representable
        // final chord to zero before the direction difference has a chance to restore it.
        a_radius.sqrt() * b_radius.sqrt() * (0.5 * direction_difference)
    };
    let half_chord = radial_half_chord.hypot(angular_half_chord);
    if !half_chord.is_finite() || half_chord == 0.0 {
        // Distinct representable rows whose polar coordinates collapse at f64 precision cannot
        // be assigned a trustworthy distance. Fail closed instead of manufacturing a duplicate.
        return f64::NAN;
    }

    let distance = 2.0 * half_chord.asinh();
    if distance.is_finite() {
        distance
    } else {
        f64::NAN
    }
}

fn validated_spatial_radius(point: &[f64]) -> Option<f64> {
    if point.len() < 2 || !point[0].is_finite() || point[0] <= 0.0 {
        return None;
    }
    let mut spatial_norm = 0.0_f64;
    for &coordinate in &point[1..] {
        if !coordinate.is_finite() {
            return None;
        }
        spatial_norm = spatial_norm.hypot(coordinate);
    }
    let expected_time = spatial_norm.hypot(1.0);
    if !expected_time.is_finite() {
        return None;
    }
    let next_time = f64::from_bits(expected_time.to_bits() + 1);
    let ulp = next_time - expected_time;
    // The spatial norm uses one rounded `hypot` per coordinate, followed by the final unit-offset
    // `hypot`; the supplied time coordinate has also been rounded independently. Allow twice that
    // count of output ulps for conservative propagation, instead of a relative epsilon band whose
    // width can span tens of ulps and admit materially off-hyperboloid rows at large radius.
    let tolerance = 2.0 * (point.len() as f64 + 1.0) * ulp;
    let unit_offset = expected_time - spatial_norm;
    // A row is verifiable only when the represented unit offset is larger than the tolerance used
    // to admit coordinate rounding. Merely checking `expected_time > spatial_norm` is insufficient:
    // near the representability boundary, a null row `[r, r]` can otherwise fall inside the much
    // wider tolerance band and be accepted as a unit-hyperboloid point.
    if !ulp.is_finite() || ulp <= 0.0 || !tolerance.is_finite() || unit_offset <= tolerance {
        return None;
    }
    (point[0] - expected_time)
        .abs()
        .le(&tolerance)
        .then_some(spatial_norm)
}

/// Convert a point from the Poincaré ball model (‖u‖<1) to the Lorentz model (hyperboloid).
///
/// For curvature -1:
/// - `x0 = (1 + ||u||^2) / (1 - ||u||^2)`
/// - `xi = 2 u_i / (1 - ||u||^2)`
///
/// Returns `None` if the input is not inside the unit ball, contains non-finite values, or maps
/// beyond the range where the unit-hyperboloid constraint remains verifiable in `f64`.
pub fn poincare_to_lorentz(u: &[f64]) -> Option<Vec<f64>> {
    if u.is_empty() {
        return None;
    }
    let mut norm2 = 0.0;
    for &ui in u {
        if !ui.is_finite() {
            return None;
        }
        norm2 += ui * ui;
    }
    if norm2 >= 1.0 {
        return None;
    }
    let denom = 1.0 - norm2;
    let x0 = (1.0 + norm2) / denom;
    let scale = 2.0 / denom;
    let mut out = Vec::with_capacity(u.len() + 1);
    out.push(x0);
    for &ui in u {
        out.push(scale * ui);
    }
    // Keep the converter and distance API on the same representable domain: do not manufacture a
    // Lorentz row whose unit hyperboloid constraint is already lost at f64 precision.
    validated_spatial_radius(&out).map(|_| out)
}

#[cfg(test)]
mod tests {
    use super::{hyperbolic_distance_lorentz, lorentz_dot, poincare_to_lorentz};

    #[test]
    fn lorentz_distance_matches_known_geodesic_in_h1() {
        // In H^1 (2D Lorentz vectors), points along a geodesic can be parameterized as:
        // x(t) = (cosh t, sinh t). Distance from x(0) to x(t) equals |t|.
        let t = 0.7_f64;
        let x0 = [1.0_f64, 0.0_f64];
        let xt = [t.cosh(), t.sinh()];

        // Check hyperboloid constraint: <x,x>_L = -1
        let n0 = lorentz_dot(&x0, &x0);
        let nt = lorentz_dot(&xt, &xt);
        assert!((n0 + 1.0).abs() < 1e-12);
        assert!((nt + 1.0).abs() < 1e-12);

        let d = hyperbolic_distance_lorentz(&x0, &xt);
        assert!((d - t).abs() < 1e-12, "d={d} t={t}");
        let d_sym = hyperbolic_distance_lorentz(&xt, &x0);
        assert!((d_sym - t).abs() < 1e-12, "d_sym={d_sym} t={t}");
        let d0 = hyperbolic_distance_lorentz(&x0, &x0);
        assert!(d0.abs() < 1e-12, "d0={d0}");
    }

    #[test]
    fn coincident_far_from_origin_point_has_zero_distance_not_nan() {
        // Regression: a point at large hyperbolic radius (Poincaré ball-norm 0.99) has a
        // Lorentz-dot cancellation error that exceeds the old fixed 1e-12 snap tolerance, so the
        // previous implementation returned NaN for d(x, x). The scale-aware tolerance + the
        // difference-based formula must return exactly 0.
        let u = [0.99_f64, 0.0];
        let x = poincare_to_lorentz(&u).expect("valid poincare point");
        assert!(x[0] > 50.0, "expected a far-from-origin point, x0={}", x[0]);
        let d = hyperbolic_distance_lorentz(&x, &x);
        assert!(
            d.is_finite() && d.abs() < 1e-9,
            "d(x,x)={d} should be ~0, not NaN"
        );

        // A nearby (not identical) far point still yields a small, finite, accurate distance.
        let u2 = [0.990_000_1_f64, 0.0];
        let y = poincare_to_lorentz(&u2).unwrap();
        let d2 = hyperbolic_distance_lorentz(&x, &y);
        assert!(
            d2.is_finite() && d2 > 0.0,
            "d(x,y)={d2} should be small positive"
        );
    }

    #[test]
    fn off_hyperboloid_points_return_nan() {
        // x0 = 0 is not a valid hyperboloid point (needs x0 = sqrt(1+||xi||^2) >= 1); the gate must
        // reject it (this underlies tests/hyperbolic_mi.rs::ksg_mi_rejects_invalid_hyperbolic).
        let a = [0.0_f64, 0.1];
        let b = [0.0_f64, 0.2];
        assert!(hyperbolic_distance_lorentz(&a, &b).is_nan());

        assert!(hyperbolic_distance_lorentz(&[2.0, 0.0], &[2.0, 0.0]).is_nan());
        assert!(hyperbolic_distance_lorentz(&[-1.0, 0.0], &[-1.0, 0.0]).is_nan());
    }

    #[test]
    fn nearby_far_points_do_not_collapse_to_zero_distance() {
        // Both rows satisfy x0^2-x1^2=1 in f64. Direct Lorentz-dot and difference-quadratic
        // formulas round their two large terms to equality and incorrectly produce distance 0.
        let a = [1_634_508.686_236_208_3, 1_634_508.686_235_902_4];
        let b = [1_634_672.145_277_647_3, 1_634_672.145_277_341_4];

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert!((distance - 1.0e-4).abs() < 2.0e-10, "distance={distance}");
    }

    #[test]
    fn nearby_far_points_retain_radial_distance_below_ball_precision() {
        // Exact H^1 rows for t=14.7 and t=14.699999999997999. Mapping both rows to the
        // Poincare ball loses most of this separation and used to overestimate it by about 134x.
        let a = [1.210_873_816_626_412_3e6, 1.210_873_816_625_999_5e6];
        let b = [1.210_873_816_623_990_4e6, 1.210_873_816_623_577_4e6];
        let expected = 2.000_177_801_164_682e-12;

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert!(
            (distance - expected).abs() < 5.0e-16,
            "distance={distance} expected={expected}"
        );
    }

    #[test]
    fn distinct_rows_below_ball_precision_retain_radial_distance() {
        let t0 = 15.0_f64;
        let t1 = t0 + 1.0e-11;
        let a = [t0.cosh(), t0.sinh()];
        let b = [t1.cosh(), t1.sinh()];
        assert_ne!(a, b);

        let distance = hyperbolic_distance_lorentz(&a, &b);
        let expected = (t1 - t0).abs();
        assert!((distance - expected).abs() < 5.0e-15);
    }

    #[test]
    fn per_point_gate_rejects_small_but_material_norm_error() {
        let t = 15.0_f64;
        let off = [t.cosh() + 3.0e-8, t.sinh()];
        let valid = [t.cosh(), t.sinh()];

        assert!(hyperbolic_distance_lorentz(&off, &valid).is_nan());
    }

    #[test]
    fn per_point_gate_rejects_null_rows_before_the_offset_rounds_away() {
        let null = [30_000_000.0, 30_000_000.0];
        let origin = [1.0, 0.0];
        assert_eq!(lorentz_dot(&null, &null), 0.0);

        assert!(hyperbolic_distance_lorentz(&null, &origin).is_nan());
    }

    #[test]
    fn per_point_gate_rejects_rows_many_ulps_from_the_unit_hyperboloid() {
        let off = [10_000_000.000_000_086, 10_000_000.0];
        let origin = [1.0, 0.0];
        assert_eq!(lorentz_dot(&off, &off), -1.71875);

        assert!(hyperbolic_distance_lorentz(&off, &origin).is_nan());
    }

    #[test]
    fn opposite_subnormal_directions_retain_representable_distance() {
        let smallest = f64::from_bits(1);
        let a = [1.0, smallest];
        let b = [1.0, -smallest];

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert_eq!(distance.to_bits(), 2);
    }

    #[test]
    fn overflowing_validity_scale_or_difference_returns_nan() {
        // The signed Lorentz products cancel to a finite value while the magnitude sum
        // overflows. An infinite tolerance must not admit these off-hyperboloid points.
        let a = [1e154, 1e154, 1e154];
        let b = [1e154, 1e154, 0.0];
        assert!(hyperbolic_distance_lorentz(&a, &b).is_nan());

        // Finite coordinates can also produce a non-finite difference quadratic form.
        let c = [f64::MAX, 0.0];
        let d = [-f64::MAX, 0.0];
        assert!(hyperbolic_distance_lorentz(&c, &d).is_nan());
    }

    #[test]
    fn invalid_dimensions_return_nan_without_panicking() {
        assert!(lorentz_dot(&[], &[]).is_nan());
        assert!(lorentz_dot(&[1.0, 0.0], &[1.0]).is_nan());
        assert!(hyperbolic_distance_lorentz(&[1.0, 0.0], &[1.0]).is_nan());
    }

    #[test]
    fn poincare_to_lorentz_produces_valid_hyperboloid_points() {
        let u = [0.2_f64, -0.1_f64, 0.05_f64];
        let x = poincare_to_lorentz(&u).expect("valid poincare point");
        assert_eq!(x.len(), u.len() + 1);
        assert!(x[0] > 0.0);
        let n = lorentz_dot(&x, &x);
        assert!((n + 1.0).abs() < 1e-10, "lorentz norm={n}");
    }

    #[test]
    fn poincare_converter_rejects_unverifiable_near_boundary_output() {
        // This point is mathematically inside the ball, but its Lorentz radius is so large that
        // `hypot(radius, 1)` rounds back to `radius`; the unit offset is no longer represented.
        assert!(poincare_to_lorentz(&[0.999_999_999_9]).is_none());
    }
}
