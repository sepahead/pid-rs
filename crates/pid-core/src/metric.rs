use crate::error::{PidError, PidResult};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Metric {
    /// Chebyshev / L∞ distance: max_i |a_i - b_i|
    Chebyshev,
    /// Hyperbolic geodesic distance in the Lorentz (hyperboloid) model (curvature -1).
    ///
    /// Expects each row vector to represent a point `x ∈ R^{d+1}` on the hyperboloid with
    /// Minkowski norm `⟨x,x⟩_L = -1` and `x0 > 0`. Distance is:
    ///
    /// `d(x,y) = arcosh( -⟨x,y⟩_L )`
    ///
    /// This is intended for **MI-only** manifold/hyperbolic contingencies (Shannon-invariant
    /// screening). It is *not* a drop-in way to “hyperbolicize” the validated shared-exclusions
    /// `I^sx_∩` estimator.
    HyperbolicLorentz,
}

impl Metric {
    #[inline]
    pub fn distance(&self, a: &[f64], b: &[f64]) -> f64 {
        match self {
            Metric::Chebyshev => chebyshev(a, b),
            Metric::HyperbolicLorentz => crate::hyperbolic::hyperbolic_distance_lorentz(a, b),
        }
    }

    #[inline]
    pub(crate) fn checked_distance(
        &self,
        a: &[f64],
        b: &[f64],
        context: &'static str,
    ) -> PidResult<f64> {
        let d = self.distance(a, b);
        if !d.is_finite() || d < 0.0 {
            return Err(PidError::NonFiniteInput { context });
        }
        Ok(d)
    }
}

#[inline]
pub fn chebyshev(a: &[f64], b: &[f64]) -> f64 {
    debug_assert_eq!(a.len(), b.len());
    let mut max_abs = 0.0;
    for (&ai, &bi) in a.iter().zip(b.iter()) {
        let d = (ai - bi).abs();
        if d > max_abs {
            max_abs = d;
        }
    }
    max_abs
}
