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
    /// Among MI estimators, this is accepted only by the provenance-carrying, **standalone
    /// pairwise-MI-only** [`crate::ksg_mi_report`] research path. Geometry diagnostics and
    /// [`Metric::distance`] also accept it; scalar/local KSG, concatenated-variable Shannon
    /// invariants, and shared-exclusions `I^sx_∩` reject it.
    HyperbolicLorentz,
}

impl Metric {
    /// Compute the distance between equal-length coordinate vectors.
    ///
    /// Returns `NaN` when the vector lengths differ. Estimator entry points use the
    /// crate-private checked form and turn that sentinel into [`PidError::NonFiniteInput`].
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
pub(crate) fn chebyshev(a: &[f64], b: &[f64]) -> f64 {
    if a.len() != b.len() {
        return f64::NAN;
    }
    let mut max_abs = 0.0;
    for (&ai, &bi) in a.iter().zip(b.iter()) {
        if !(ai.is_finite() && bi.is_finite()) {
            return f64::NAN;
        }
        let d = (ai - bi).abs();
        if !d.is_finite() {
            return d;
        }
        if d > max_abs {
            max_abs = d;
        }
    }
    max_abs
}

#[cfg(test)]
mod tests {
    use super::Metric;

    #[test]
    fn public_distance_rejects_mismatched_dimensions_without_panicking() {
        assert!(Metric::Chebyshev.distance(&[1.0, 2.0], &[1.0]).is_nan());
        assert!(Metric::HyperbolicLorentz
            .distance(&[1.0, 0.0], &[1.0])
            .is_nan());
    }

    #[test]
    fn public_chebyshev_distance_rejects_nonfinite_coordinates() {
        assert!(Metric::Chebyshev.distance(&[f64::NAN], &[0.0]).is_nan());
        assert!(Metric::Chebyshev
            .distance(&[f64::INFINITY], &[f64::INFINITY])
            .is_nan());
        assert!(Metric::Chebyshev
            .distance(&[-f64::MAX], &[f64::MAX])
            .is_infinite());
    }
}
