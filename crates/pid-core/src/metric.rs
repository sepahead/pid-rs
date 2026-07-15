use crate::error::{PidError, PidResult};
use crate::resource::{CancellationProgress, CancellationToken};
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum Metric {
    /// Chebyshev / L∞ distance: max_i |a_i - b_i|
    Chebyshev,
}

impl Metric {
    /// Compute the distance between equal-length coordinate vectors.
    ///
    /// # Errors
    ///
    /// Returns a structured error for mismatched dimensions, non-finite input, or a non-finite
    /// computed distance. Failure is never encoded as `NaN`.
    pub fn distance(&self, a: &[f64], b: &[f64]) -> PidResult<f64> {
        self.distance_with_context(a, b, "Metric::distance")
    }

    fn distance_with_context(&self, a: &[f64], b: &[f64], context: &'static str) -> PidResult<f64> {
        KernelMetric::from(*self).checked_distance(a, b, context)
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
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum KernelMetric {
    Chebyshev,
    #[cfg(feature = "experimental-hyperbolic")]
    HyperbolicLorentz {
        curvature: crate::hyperbolic::HyperbolicCurvature,
    },
}

impl KernelMetric {
    pub(crate) const fn is_chebyshev(self) -> bool {
        matches!(self, Self::Chebyshev)
    }

    #[cfg(feature = "experimental-hyperbolic")]
    pub(crate) const fn is_hyperbolic(self) -> bool {
        matches!(self, Self::HyperbolicLorentz { .. })
    }

    pub(crate) const fn coordinate_work_factor(self) -> u128 {
        match self {
            Self::Chebyshev => 1,
            #[cfg(feature = "experimental-hyperbolic")]
            Self::HyperbolicLorentz { .. } => {
                crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR
            }
        }
    }

    pub(crate) fn checked_distance(
        self,
        a: &[f64],
        b: &[f64],
        context: &'static str,
    ) -> PidResult<f64> {
        match self {
            Self::Chebyshev => chebyshev(a, b, context),
            #[cfg(feature = "experimental-hyperbolic")]
            Self::HyperbolicLorentz { curvature } => {
                crate::hyperbolic::hyperbolic_distance_lorentz_with_context(
                    a, b, curvature, context,
                )
            }
        }
    }

    pub(crate) fn checked_distance_with_cancellation(
        self,
        a: &[f64],
        b: &[f64],
        context: &'static str,
        cancellation_progress: CancellationProgress,
        cancellation: &CancellationToken,
    ) -> PidResult<f64> {
        match self {
            Self::Chebyshev => {
                chebyshev_with_cancellation(a, b, context, cancellation_progress, cancellation)
            }
            #[cfg(feature = "experimental-hyperbolic")]
            Self::HyperbolicLorentz { curvature } => {
                crate::hyperbolic::hyperbolic_distance_lorentz_with_context_and_cancellation(
                    a,
                    b,
                    curvature,
                    context,
                    cancellation_progress,
                    cancellation,
                )
            }
        }
    }
}

impl From<Metric> for KernelMetric {
    fn from(metric: Metric) -> Self {
        match metric {
            Metric::Chebyshev => Self::Chebyshev,
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

    #[test]
    fn public_distance_rejects_mismatched_dimensions_without_panicking() {
        assert!(matches!(
            Metric::Chebyshev.distance(&[1.0, 2.0], &[1.0]),
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
}
