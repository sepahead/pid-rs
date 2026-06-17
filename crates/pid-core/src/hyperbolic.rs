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
/// For valid points on the hyperboloid (`⟨x,x⟩_L = -1`, `x0>0`), the distance is:
/// `d(x,y) = arcosh( -⟨x,y⟩_L )`.
///
/// Returns NaN if the inputs do not define a valid hyperbolic distance (e.g., if `-⟨x,y⟩ < 1`
/// by more than a tiny numerical tolerance).
#[inline]
pub fn hyperbolic_distance_lorentz(a: &[f64], b: &[f64]) -> f64 {
    let dot = lorentz_dot(a, b);
    if !dot.is_finite() {
        return f64::NAN;
    }
    let arg = -dot;
    // For valid points, arg >= 1. Allow tiny numerical violations.
    if arg < 1.0 {
        if arg > 1.0 - 1e-12 {
            return 0.0;
        }
        return f64::NAN;
    }
    arg.acosh()
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
    fn poincare_to_lorentz_produces_valid_hyperboloid_points() {
        let u = [0.2_f64, -0.1_f64, 0.05_f64];
        let x = poincare_to_lorentz(&u).expect("valid poincare point");
        assert_eq!(x.len(), u.len() + 1);
        assert!(x[0] > 0.0);
        let n = lorentz_dot(&x, &x);
        assert!((n + 1.0).abs() < 1e-10, "lorentz norm={n}");
    }
}
