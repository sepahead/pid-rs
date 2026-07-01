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
    debug_assert_eq!(a.len(), b.len());
    debug_assert!(
        a.len() >= 2,
        "Lorentz vectors must have dimension >= 2 (time + at least one spatial dim)"
    );
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
/// 1. **Validity/coincidence gate.** `arg = -⟨x,y⟩_L` must be `>= 1`. The dot product subtracts
///    large near-equal terms (`x0·y0 − Σ xi·yi`) for nearby far-from-origin points, so the gate
///    tolerance is scaled by the magnitude of those terms (`~ε·Σ|xi·yi|`) rather than a fixed
///    `1e-12` — otherwise a *coincident* pair at large hyperbolic radius (where the cancellation
///    error exceeds `1e-12`) would spuriously return `NaN`.
/// 2. **Difference-based distance.** For valid inputs the value is computed as
///    `2·asinh( ½·√⟨x−y, x−y⟩_L )` from coordinate *differences*, using the exact identity
///    `arcosh(arg) = 2·asinh(√((arg−1)/2))` with `⟨x−y,x−y⟩_L = 2(arg−1) ≥ 0`. This avoids both the
///    catastrophic cancellation in `arg` and the precision loss of `acosh` near 1, recovering full
///    accuracy for nearby points at any radius.
///
/// Returns `NaN` if the inputs do not define a valid hyperbolic distance (`arg < 1` beyond the
/// scale-aware tolerance, i.e. genuinely off-hyperboloid input), or if any coordinate is non-finite.
#[inline]
pub fn hyperbolic_distance_lorentz(a: &[f64], b: &[f64]) -> f64 {
    debug_assert_eq!(a.len(), b.len());
    let n = a.len();
    if n < 2 {
        return f64::NAN;
    }

    // 1) Validity/coincidence gate on arg = -⟨a,b⟩_L, with a cancellation-aware tolerance.
    let mut dot = -a[0] * b[0];
    let mut mag_dot = (a[0] * b[0]).abs();
    for i in 1..n {
        dot += a[i] * b[i];
        mag_dot += (a[i] * b[i]).abs();
    }
    if !dot.is_finite() {
        return f64::NAN;
    }
    let arg = -dot;
    let tol = 8.0 * f64::EPSILON * mag_dot.max(1.0);
    if arg < 1.0 - tol {
        return f64::NAN; // genuinely off-hyperboloid / invalid input
    }

    // 2) Distance from coordinate differences: ⟨a−b, a−b⟩_L = 2(arg−1) ≥ 0 for valid points.
    let d0 = a[0] - b[0];
    let mut q = -d0 * d0;
    for i in 1..n {
        let di = a[i] - b[i];
        q += di * di;
    }
    // `q` can dip slightly below 0 by FP noise for (near-)coincident points; clamp to 0 (the true
    // distance there is 0 — this is a coincidence, not sign-hiding of an information atom).
    2.0 * (0.5 * q.max(0.0).sqrt()).asinh()
}

/// Convert a point from the Poincaré ball model (‖u‖<1) to the Lorentz model (hyperboloid).
///
/// For curvature -1:
/// - `x0 = (1 + ||u||^2) / (1 - ||u||^2)`
/// - `xi = 2 u_i / (1 - ||u||^2)`
///
/// Returns `None` if the input is not inside the unit ball or contains non-finite values.
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
    Some(out)
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
}
