use std::cmp::Ordering;

use rug::float::Round;
use rug::ops::{AddAssignRound, MulAssignRound};
use rug::{Float, Integer, Rational};
use serde::Serialize;

use crate::error::CertError;
use crate::exact::LogExpression;

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Dyadic {
    significand: Integer,
    exponent2: i32,
}

#[derive(Clone, Debug)]
pub(crate) struct Enclosure {
    pub(crate) lower: Dyadic,
    pub(crate) upper: Dyadic,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub(crate) struct DyadicOutput {
    pub(crate) significand: String,
    pub(crate) exponent2: i32,
}

impl Dyadic {
    fn from_float(value: &Float) -> Result<Self, CertError> {
        let (mut significand, mut exponent2) = value.to_integer_exp().ok_or_else(|| {
            CertError::internal("MPFR returned a non-finite authoritative endpoint")
        })?;
        if significand == 0 {
            return Ok(Self {
                significand,
                exponent2: 0,
            });
        }
        while significand.is_even() {
            significand >>= 1;
            exponent2 = exponent2.checked_add(1).ok_or_else(|| {
                CertError::internal("dyadic exponent overflow during normalization")
            })?;
        }
        Ok(Self {
            significand,
            exponent2,
        })
    }

    fn from_rational_dyadic(value: &Rational) -> Result<Self, CertError> {
        let mut denominator = value.denom().clone();
        let mut denominator_power = 0i32;
        while denominator > 1 && denominator.is_even() {
            denominator >>= 1;
            denominator_power = denominator_power
                .checked_add(1)
                .ok_or_else(|| CertError::internal("dyadic denominator exponent overflow"))?;
        }
        if denominator != 1 {
            return Err(CertError::internal(
                "authoritative endpoint is not an exact dyadic rational",
            ));
        }
        let mut result = Self {
            significand: value.numer().clone(),
            exponent2: -denominator_power,
        };
        if result.significand == 0 {
            result.exponent2 = 0;
        } else {
            while result.significand.is_even() {
                result.significand >>= 1;
                result.exponent2 = result.exponent2.checked_add(1).ok_or_else(|| {
                    CertError::internal("dyadic exponent overflow during normalization")
                })?;
            }
        }
        Ok(result)
    }

    pub(crate) fn to_rational(&self) -> Rational {
        if self.exponent2 >= 0 {
            let numerator = self.significand.clone() << self.exponent2.unsigned_abs();
            Rational::from(numerator)
        } else {
            let denominator = Integer::from(1) << self.exponent2.unsigned_abs();
            Rational::from((self.significand.clone(), denominator))
        }
    }

    pub(crate) fn output(&self) -> DyadicOutput {
        DyadicOutput {
            significand: self.significand.to_string(),
            exponent2: self.exponent2,
        }
    }
}

impl Enclosure {
    pub(crate) fn exact_zero() -> Self {
        let zero = Dyadic {
            significand: Integer::from(0),
            exponent2: 0,
        };
        Self {
            lower: zero.clone(),
            upper: zero,
        }
    }

    pub(crate) fn validate(&self) -> Result<(), CertError> {
        if self.lower.to_rational() > self.upper.to_rational() {
            return Err(CertError::internal(
                "authoritative interval has lower endpoint above upper endpoint",
            ));
        }
        Ok(())
    }

    pub(crate) fn width(&self) -> Rational {
        self.upper.to_rational() - self.lower.to_rational()
    }

    pub(crate) fn intersect(&self, other: &Self) -> Result<Self, CertError> {
        let self_lower = self.lower.to_rational();
        let other_lower = other.lower.to_rational();
        let self_upper = self.upper.to_rational();
        let other_upper = other.upper.to_rational();
        let lower = if self_lower >= other_lower {
            self_lower
        } else {
            other_lower
        };
        let upper = if self_upper <= other_upper {
            self_upper
        } else {
            other_upper
        };
        if lower > upper {
            return Err(CertError::internal(
                "successive directed-rounding intervals have an empty intersection",
            ));
        }
        let result = Self {
            lower: Dyadic::from_rational_dyadic(&lower)?,
            upper: Dyadic::from_rational_dyadic(&upper)?,
        };
        result.validate()?;
        Ok(result)
    }

    pub(crate) fn overlaps(&self, other: &Self) -> bool {
        self.lower.to_rational() <= other.upper.to_rational()
            && other.lower.to_rational() <= self.upper.to_rational()
    }

    pub(crate) fn exact_subtract(left: &Self, right: &Self) -> Result<Self, CertError> {
        let lower = left.lower.to_rational() - right.upper.to_rational();
        let upper = left.upper.to_rational() - right.lower.to_rational();
        let result = Self {
            lower: Dyadic::from_rational_dyadic(&lower)?,
            upper: Dyadic::from_rational_dyadic(&upper)?,
        };
        result.validate()?;
        Ok(result)
    }

    pub(crate) fn sign(&self, symbolic_zero: bool) -> &'static str {
        if symbolic_zero {
            "certified_exact_zero"
        } else if self.lower.to_rational() > 0 {
            "certified_positive"
        } else if self.upper.to_rational() < 0 {
            "certified_negative"
        } else {
            "unresolved_sign"
        }
    }
}

pub(crate) fn evaluate(
    expression: &LogExpression,
    precision_bits: u32,
) -> Result<Enclosure, CertError> {
    if expression.is_symbolic_zero() {
        return Ok(Enclosure::exact_zero());
    }

    let (mut lower_sum, lower_zero_order) = Float::with_val_round(precision_bits, 0, Round::Down);
    ensure_lower_order(lower_zero_order, "lower zero initialization")?;
    let (mut upper_sum, upper_zero_order) = Float::with_val_round(precision_bits, 0, Round::Up);
    ensure_upper_order(upper_zero_order, "upper zero initialization")?;

    for (argument, coefficient) in expression.terms() {
        let (mut log_lower, argument_lower_order) =
            Float::with_val_round(precision_bits, argument, Round::Down);
        ensure_lower_order(argument_lower_order, "lower rational conversion")?;
        let (mut log_upper, argument_upper_order) =
            Float::with_val_round(precision_bits, argument, Round::Up);
        ensure_upper_order(argument_upper_order, "upper rational conversion")?;
        if !log_lower.is_finite() || !log_upper.is_finite() || log_lower <= 0 || log_upper <= 0 {
            return Err(CertError::internal(
                "positive rational log argument became nonpositive or non-finite",
            ));
        }

        let log_lower_order = log_lower.ln_round(Round::Down);
        ensure_lower_order(log_lower_order, "lower natural logarithm")?;
        let log_upper_order = log_upper.ln_round(Round::Up);
        ensure_upper_order(log_upper_order, "upper natural logarithm")?;

        let (mut term_lower, mut term_upper) = if coefficient > &0 {
            (log_lower, log_upper)
        } else if coefficient < &0 {
            (log_upper, log_lower)
        } else {
            return Err(CertError::internal(
                "canonical expression retained a zero coefficient",
            ));
        };

        let term_lower_order = term_lower.mul_assign_round(coefficient, Round::Down);
        ensure_lower_order(term_lower_order, "lower exact-rational scaling")?;
        let term_upper_order = term_upper.mul_assign_round(coefficient, Round::Up);
        ensure_upper_order(term_upper_order, "upper exact-rational scaling")?;

        let lower_sum_order = lower_sum.add_assign_round(&term_lower, Round::Down);
        ensure_lower_order(lower_sum_order, "lower directed accumulation")?;
        let upper_sum_order = upper_sum.add_assign_round(&term_upper, Round::Up);
        ensure_upper_order(upper_sum_order, "upper directed accumulation")?;
        if !lower_sum.is_finite() || !upper_sum.is_finite() {
            return Err(CertError::internal(
                "directed accumulation produced a non-finite endpoint",
            ));
        }
    }

    let result = Enclosure {
        lower: Dyadic::from_float(&lower_sum)?,
        upper: Dyadic::from_float(&upper_sum)?,
    };
    result.validate()?;
    Ok(result)
}

fn ensure_lower_order(order: Ordering, stage: &str) -> Result<(), CertError> {
    if order == Ordering::Greater {
        return Err(CertError::internal(format!(
            "{stage} violated the downward-rounding order contract"
        )));
    }
    Ok(())
}

fn ensure_upper_order(order: Ordering, stage: &str) -> Result<(), CertError> {
    if order == Ordering::Less {
        return Err(CertError::internal(format!(
            "{stage} violated the upward-rounding order contract"
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use rug::{Integer, Rational};

    use crate::exact::LogExpression;

    use super::{evaluate, Enclosure};

    fn tiny_positive_expression() -> LogExpression {
        let denominator: Integer = Integer::from(1) << 100;
        let numerator = denominator.clone() + 1;
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(1), Rational::from((numerator, denominator)))
            .expect("valid positive log argument");
        expression
    }

    #[test]
    fn evaluate_should_keep_high_precision_interval_inside_low_precision_interval() {
        let expression = tiny_positive_expression();
        let low = evaluate(&expression, 32).expect("low-precision enclosure");
        let high = evaluate(&expression, 256).expect("high-precision enclosure");

        assert!(low.overlaps(&high));
    }

    #[test]
    fn evaluate_should_leave_tiny_positive_value_unresolved_at_low_precision() {
        let interval = evaluate(&tiny_positive_expression(), 32).expect("enclosure");

        assert_eq!(interval.sign(false), "unresolved_sign");
    }

    #[test]
    fn evaluate_should_certify_tiny_positive_value_at_high_precision() {
        let interval = evaluate(&tiny_positive_expression(), 256).expect("enclosure");

        assert_eq!(interval.sign(false), "certified_positive");
    }

    #[test]
    fn exact_subtract_should_cross_endpoints() {
        let left = Enclosure::exact_zero();
        let mut positive = LogExpression::default();
        positive
            .add_term(Rational::from(1), Rational::from(2))
            .expect("valid term");
        let right = evaluate(&positive, 64).expect("positive enclosure");

        let difference = Enclosure::exact_subtract(&left, &right).expect("subtraction enclosure");

        assert_eq!(difference.sign(false), "certified_negative");
    }

    #[test]
    fn directed_evaluation_should_contain_exact_log_reciprocal_identity() {
        let mut identity = LogExpression::default();
        identity
            .add_term(Rational::from(1), Rational::from(2))
            .expect("positive argument");
        identity
            .add_term(Rational::from(1), Rational::from((1, 2)))
            .expect("positive reciprocal argument");

        let interval = evaluate(&identity, 128).expect("identity enclosure");

        assert!(interval.lower.to_rational() <= 0);
        assert!(interval.upper.to_rational() >= 0);
    }

    #[test]
    fn directed_evaluation_should_contain_exact_log_power_identity() {
        let mut identity = LogExpression::default();
        identity
            .add_term(Rational::from(1), Rational::from(4))
            .expect("positive argument");
        identity
            .add_term(Rational::from(-2), Rational::from(2))
            .expect("positive argument");

        let interval = evaluate(&identity, 128).expect("identity enclosure");

        assert!(interval.lower.to_rational() <= 0);
        assert!(interval.upper.to_rational() >= 0);
    }
}
