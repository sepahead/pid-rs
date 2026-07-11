use crate::error::{PidError, PidResult};

/// Mean of finite values, scaled before summation so avoidable intermediate overflow does not
/// reject a representable result.
pub(crate) fn finite_mean(values: &[f64], context: &'static str) -> PidResult<f64> {
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    let mean = scale * mean_scaled;
    if mean.is_finite() {
        Ok(mean)
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

/// Population mean and standard deviation of finite values.
///
/// Both passes operate after division by `max(abs(x))`. This matters for data such as
/// `[0, f64::MAX]`: its mean and standard deviation are both finite, even though forming either
/// the raw sum or the raw variance overflows.
pub(crate) fn finite_mean_std_population(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 0, context)
}

/// Sample mean and standard deviation (Bessel-corrected, denominator `n-1`).
pub(crate) fn finite_mean_std_sample(
    values: &[f64],
    context: &'static str,
) -> PidResult<(f64, f64)> {
    finite_mean_std(values, 1, context)
}

fn finite_mean_std(values: &[f64], ddof: usize, context: &'static str) -> PidResult<(f64, f64)> {
    if values.len() <= ddof {
        return Err(PidError::InvalidConfig {
            context,
            message: "not enough values for the requested variance degrees of freedom",
        });
    }
    let (scale, mean_scaled) = scaled_mean_parts(values, context)?;
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let sum_squared_scaled = compensated_sum(values.iter().map(|value| {
        let deviation = value / scale - mean_scaled;
        deviation * deviation
    }));
    let variance_scaled = sum_squared_scaled / (values.len() - ddof) as f64;
    // For |x| <= scale, the exact population variance is <= scale^2. Permit a small floating
    // tolerance, then restore that mathematical bound so `scale * sqrt(var)` cannot spuriously
    // overflow at `f64::MAX`.
    let variance_bound = values.len() as f64 / (values.len() - ddof) as f64;
    let tolerance = 64.0 * f64::EPSILON * variance_bound;
    if !variance_scaled.is_finite()
        || variance_scaled < -tolerance
        || variance_scaled > variance_bound + tolerance
    {
        return Err(PidError::NumericalInstability { context });
    }
    let std = scale * variance_scaled.clamp(0.0, variance_bound).sqrt();
    let mean = scale * mean_scaled;
    if mean.is_finite() && std.is_finite() {
        Ok((mean, std))
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

fn scaled_mean_parts(values: &[f64], context: &'static str) -> PidResult<(f64, f64)> {
    if values.is_empty() {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one value",
        });
    }
    if values.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NonFiniteInput { context });
    }
    let scale = values
        .iter()
        .fold(0.0_f64, |current, value| current.max(value.abs()));
    if scale == 0.0 {
        return Ok((0.0, 0.0));
    }

    let raw_mean_scaled =
        compensated_sum(values.iter().map(|value| value / scale)) / values.len() as f64;
    let tolerance = 64.0 * f64::EPSILON;
    if !raw_mean_scaled.is_finite() || raw_mean_scaled.abs() > 1.0 + tolerance {
        return Err(PidError::NumericalInstability { context });
    }
    Ok((scale, raw_mean_scaled.clamp(-1.0, 1.0)))
}

/// Deterministic Neumaier compensated summation in iterator order.
///
/// Callers remain responsible for ensuring that the mathematical sum is representable. Keeping
/// this helper crate-visible lets estimators share one stable accumulation policy without exposing
/// it as part of the public API.
pub(crate) fn compensated_sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    sum + correction
}

/// Digamma / psi function ψ(x).
///
/// Implementation: recurrence to shift into a "large x" regime + asymptotic expansion.
///
/// Units: natural logarithm (nats).
pub(crate) fn digamma(x: f64) -> f64 {
    debug_assert!(x.is_finite());
    debug_assert!(x > 0.0);

    let mut x = x;
    let mut acc = 0.0;

    // Recurrence for small x: ψ(x) = ψ(x+1) - 1/x
    // Shifting to 8 keeps the truncated Bernoulli expansion comfortably below 1e-13 error at
    // the small integer arguments used by KSG. Stopping at 6 leaves a ~9.3e-13 bias in psi(1).
    while x < 8.0 {
        acc -= 1.0 / x;
        x += 1.0;
    }

    // Asymptotic series (Stirling-like).
    // ψ(x) ≈ ln(x) - 1/(2x) - 1/(12x²) + 1/(120x⁴) - 1/(252x⁶) + 1/(240x⁸) - 1/(132x¹⁰) + 691/(32760x¹²) - ...
    let inv = 1.0 / x;
    let inv2 = inv * inv;
    let inv4 = inv2 * inv2;
    let inv6 = inv4 * inv2;
    let inv8 = inv4 * inv4;
    let inv10 = inv8 * inv2;
    let inv12 = inv6 * inv6;

    acc + x.ln() - 0.5 * inv - (1.0 / 12.0) * inv2 + (1.0 / 120.0) * inv4 - (1.0 / 252.0) * inv6
        + (1.0 / 240.0) * inv8
        - (1.0 / 132.0) * inv10
        + (691.0 / 32760.0) * inv12
}

/// Precompute ψ(i) for integer `i` in `0..=n` (with index 0 unused).
///
/// KSG-style estimators call `digamma` many times with small positive integers
/// (`k`, `N`, and neighbor counts). This helper avoids repeated work while keeping
/// semantics identical.
pub(crate) fn digamma_int_table(n: usize) -> Vec<f64> {
    let mut out = vec![0.0f64; n.saturating_add(1)];
    for (i, v) in out.iter_mut().enumerate().skip(1) {
        *v = digamma(i as f64);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::{digamma, finite_mean, finite_mean_std_population, finite_mean_std_sample};

    const EULER_GAMMA: f64 = 0.577_215_664_901_532_9_f64;

    fn harmonic(n: usize) -> f64 {
        // H_n = sum_{k=1..n} 1/k, with H_0 = 0.
        (1..=n).map(|k| 1.0 / (k as f64)).sum()
    }

    #[test]
    fn digamma_matches_known_integer_values() {
        // ψ(1) = -γ
        let psi1 = digamma(1.0);
        assert!((psi1 + EULER_GAMMA).abs() < 1e-12, "psi(1)={psi1}");

        // ψ(n) = H_{n-1} - γ for integer n>=2
        for n in 2..=25usize {
            let psi_n = digamma(n as f64);
            let expected = harmonic(n - 1) - EULER_GAMMA;
            assert!(
                (psi_n - expected).abs() < 5e-14,
                "psi({n})={psi_n} expected={expected}"
            );
        }
    }

    #[test]
    fn digamma_recurrence_holds() {
        // ψ(x+1) = ψ(x) + 1/x
        let x = 3.7;
        let lhs = digamma(x + 1.0);
        let rhs = digamma(x) + 1.0 / x;
        assert!((lhs - rhs).abs() < 5e-13, "lhs={lhs} rhs={rhs}");
    }

    #[test]
    fn scaled_moments_keep_representable_extreme_results_finite() {
        let (mean, std) = finite_mean_std_population(&[0.0, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, f64::MAX * 0.5);
        assert_eq!(std, f64::MAX * 0.5);

        let (mean, std) =
            finite_mean_std_population(&[-f64::MAX, f64::MAX], "extreme moments").unwrap();
        assert_eq!(mean, 0.0);
        assert_eq!(std, f64::MAX);

        assert_eq!(
            finite_mean(&[f64::MAX; 4], "extreme mean").unwrap(),
            f64::MAX
        );
    }

    #[test]
    fn scaled_moments_reject_empty_or_nonfinite_input() {
        assert!(finite_mean(&[], "empty mean").is_err());
        assert!(finite_mean_std_population(&[f64::NAN], "nan moments").is_err());
        assert!(finite_mean_std_sample(&[1.0], "singleton sample").is_err());
    }
}
