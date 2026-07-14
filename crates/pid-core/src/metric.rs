use crate::error::{PidError, PidResult};
#[cfg(feature = "experimental-hyperbolic")]
use crate::hyperbolic::HyperbolicCurvature;
use crate::resource::{CancellationProgress, CancellationToken};
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Metric {
    /// Chebyshev / L∞ distance: max_i |a_i - b_i|
    Chebyshev,
    /// Hyperbolic geodesic distance in the Lorentz (hyperboloid) model.
    ///
    /// Expects each row vector to represent a point `x ∈ R^{d+1}` on the hyperboloid with
    /// Minkowski norm `⟨x,x⟩_L = -1` and `x0 > 0`. Distance is:
    ///
    /// At [`HyperbolicCurvature::NegativeOne`], `d(x,y) = arcosh( -⟨x,y⟩_L )`.
    ///
    /// Among MI estimators, this is accepted only by the provenance-carrying, **standalone
    /// pairwise-MI-only** [`crate::stable::continuous::ksg_mi_report`] research path. Geometry diagnostics and
    /// [`Metric::distance`] also accept it; scalar/local KSG, concatenated-variable Shannon
    /// invariants, and shared-exclusions `I^sx_∩` reject it.
    #[cfg(feature = "experimental-hyperbolic")]
    HyperbolicLorentz {
        /// Explicit curvature scale forming part of the geometric estimand.
        curvature: HyperbolicCurvature,
    },
}

impl Metric {
    /// Compute the distance between equal-length coordinate vectors.
    ///
    /// # Errors
    ///
    /// Returns a structured error for mismatched dimensions, non-finite input, an invalid or
    /// unverifiable Lorentz point, or a non-finite computed distance. Failure is never encoded as
    /// `NaN`.
    pub fn distance(&self, a: &[f64], b: &[f64]) -> PidResult<f64> {
        self.distance_with_context(a, b, "Metric::distance")
    }

    fn distance_with_context(&self, a: &[f64], b: &[f64], context: &'static str) -> PidResult<f64> {
        match self {
            Metric::Chebyshev => chebyshev(a, b, context),
            #[cfg(feature = "experimental-hyperbolic")]
            Metric::HyperbolicLorentz { curvature } => {
                crate::hyperbolic::hyperbolic_distance_lorentz_with_context(
                    a, b, *curvature, context,
                )
            }
        }
    }

    #[inline]
    #[cfg_attr(
        not(any(
            feature = "experimental-continuous",
            feature = "experimental-heuristics"
        )),
        allow(dead_code)
    )]
    pub(crate) fn checked_distance(
        &self,
        a: &[f64],
        b: &[f64],
        context: &'static str,
    ) -> PidResult<f64> {
        self.distance_with_context(a, b, context)
    }

    #[inline]
    pub(crate) fn checked_distance_with_cancellation(
        &self,
        a: &[f64],
        b: &[f64],
        context: &'static str,
        cancellation_progress: CancellationProgress,
        cancellation: &CancellationToken,
    ) -> PidResult<f64> {
        match self {
            Metric::Chebyshev => {
                chebyshev_with_cancellation(a, b, context, cancellation_progress, cancellation)
            }
            #[cfg(feature = "experimental-hyperbolic")]
            Metric::HyperbolicLorentz { curvature } => {
                crate::hyperbolic::hyperbolic_distance_lorentz_with_context_and_cancellation(
                    a,
                    b,
                    *curvature,
                    context,
                    cancellation_progress,
                    cancellation,
                )
            }
        }
    }
}

#[inline]
pub(crate) fn chebyshev(a: &[f64], b: &[f64], context: &'static str) -> PidResult<f64> {
    if a.len() != b.len() {
        return Err(PidError::ShapeMismatch {
            context,
            expected_len: a.len(),
            actual_len: b.len(),
        });
    }
    let mut max_abs = 0.0;
    for (&ai, &bi) in a.iter().zip(b.iter()) {
        if !(ai.is_finite() && bi.is_finite()) {
            return Err(PidError::NonFiniteInput { context });
        }
        let d = (ai - bi).abs();
        if !d.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        if d > max_abs {
            max_abs = d;
        }
    }
    Ok(max_abs)
}

fn chebyshev_with_cancellation(
    a: &[f64],
    b: &[f64],
    context: &'static str,
    cancellation_progress: CancellationProgress,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    if a.len() != b.len() {
        return Err(PidError::ShapeMismatch {
            context,
            expected_len: a.len(),
            actual_len: b.len(),
        });
    }
    cancellation_progress.check(cancellation)?;
    let mut max_abs = 0.0;
    for (index, (&ai, &bi)) in a.iter().zip(b.iter()).enumerate() {
        if index.is_multiple_of(1024) {
            cancellation_progress.check(cancellation)?;
        }
        if !(ai.is_finite() && bi.is_finite()) {
            return Err(PidError::NonFiniteInput { context });
        }
        let distance = (ai - bi).abs();
        if !distance.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        if distance > max_abs {
            max_abs = distance;
        }
    }
    cancellation_progress.check(cancellation)?;
    Ok(max_abs)
}

#[cfg(test)]
mod tests {
    use super::Metric;
    use crate::error::PidError;
    #[cfg(feature = "experimental-hyperbolic")]
    use crate::hyperbolic::HyperbolicCurvature;
    #[cfg(feature = "experimental-hyperbolic")]
    use crate::resource::{CancellationProgress, CancellationToken};

    #[test]
    fn public_distance_rejects_mismatched_dimensions_without_panicking() {
        assert!(matches!(
            Metric::Chebyshev.distance(&[1.0, 2.0], &[1.0]),
            Err(PidError::ShapeMismatch { .. })
        ));
        #[cfg(feature = "experimental-hyperbolic")]
        assert!(matches!(
            Metric::HyperbolicLorentz {
                curvature: HyperbolicCurvature::NegativeOne,
            }
            .distance(&[1.0, 0.0], &[1.0]),
            Err(PidError::ShapeMismatch { .. })
        ));
    }

    #[test]
    fn public_chebyshev_distance_rejects_nonfinite_coordinates() {
        assert!(matches!(
            Metric::Chebyshev.distance(&[f64::NAN], &[0.0]),
            Err(PidError::NonFiniteInput { .. })
        ));
        assert!(matches!(
            Metric::Chebyshev.distance(&[f64::INFINITY], &[f64::INFINITY]),
            Err(PidError::NonFiniteInput { .. })
        ));
        assert!(matches!(
            Metric::Chebyshev.distance(&[-f64::MAX], &[f64::MAX]),
            Err(PidError::NumericalInstability { .. })
        ));
    }

    #[cfg(feature = "experimental-hyperbolic")]
    #[test]
    fn cancellable_hyperbolic_distance_preserves_bits_and_honors_token() {
        let metric = Metric::HyperbolicLorentz {
            curvature: HyperbolicCurvature::NegativeOne,
        };
        let radial_coordinate = 0.5_f64;
        let a = [1.0, 0.0];
        let b = [radial_coordinate.cosh(), radial_coordinate.sinh()];

        let expected = metric
            .checked_distance(&a, &b, "cancellable hyperbolic distance test")
            .unwrap();
        let running = CancellationToken::new();
        let actual = metric
            .checked_distance_with_cancellation(
                &a,
                &b,
                "cancellable hyperbolic distance test",
                CancellationProgress::new("metric cancellation test", 3, 7),
                &running,
            )
            .unwrap();
        assert_eq!(actual.to_bits(), expected.to_bits());

        let cancelled = CancellationToken::new();
        cancelled.cancel();
        assert!(matches!(
            metric.checked_distance_with_cancellation(
                &a,
                &b,
                "cancellable hyperbolic distance test",
                CancellationProgress::new("metric cancellation test", 3, 7),
                &cancelled,
            ),
            Err(PidError::Cancelled {
                operation: "metric cancellation test",
                completed_units: 3,
                total_units: 7,
            })
        ));
    }
}
