use std::collections::BTreeMap;

use rug::{Integer, Rational};
use serde::Serialize;

use crate::digest::canonical_digest;
use crate::error::CertError;
use crate::resource::MAX_TERMS_PER_EXPRESSION;

/// A canonical exact expression of the form `sum coefficient * ln(argument)`.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub(crate) struct LogExpression {
    terms: BTreeMap<Rational, Rational>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub(crate) struct ExactRational {
    pub(crate) numerator: String,
    pub(crate) denominator: String,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub(crate) struct ExactLogTerm {
    pub(crate) coefficient: ExactRational,
    pub(crate) log_argument: ExactRational,
}

impl LogExpression {
    pub(crate) fn add_term(
        &mut self,
        coefficient: Rational,
        argument: Rational,
    ) -> Result<(), CertError> {
        if argument <= 0 {
            return Err(CertError::new(
                "nonpositive_log_argument",
                format!("exact log argument must be positive, found {argument}"),
            ));
        }
        if coefficient == 0 || argument == 1 {
            return Ok(());
        }

        if let Some(existing) = self.terms.get(&argument) {
            let mut combined = existing.clone();
            combined += coefficient;
            if combined == 0 {
                self.terms.remove(&argument);
            } else {
                self.terms.insert(argument, combined);
            }
        } else {
            if self.terms.len() >= MAX_TERMS_PER_EXPRESSION {
                return Err(CertError::new(
                    "certificate_resource_limit",
                    format!("one exact expression would exceed {MAX_TERMS_PER_EXPRESSION} terms"),
                ));
            }
            self.terms.insert(argument, coefficient);
        }
        Ok(())
    }

    pub(crate) fn add_scaled(&mut self, other: &Self, scale: i32) -> Result<(), CertError> {
        if scale == 0 {
            return Ok(());
        }
        let exact_scale = Rational::from(scale);
        for (argument, coefficient) in &other.terms {
            let mut scaled = coefficient.clone();
            scaled *= &exact_scale;
            self.add_term(scaled, argument.clone())?;
        }
        Ok(())
    }

    pub(crate) fn linear_combination(
        expressions: &[Self; 4],
        coefficients: [i32; 4],
    ) -> Result<Self, CertError> {
        let mut result = Self::default();
        for (expression, coefficient) in expressions.iter().zip(coefficients) {
            result.add_scaled(expression, coefficient)?;
        }
        Ok(result)
    }

    pub(crate) fn terms(&self) -> impl Iterator<Item = (&Rational, &Rational)> {
        self.terms.iter()
    }

    pub(crate) fn is_symbolic_zero(&self) -> bool {
        self.terms.is_empty()
    }

    pub(crate) fn len(&self) -> usize {
        self.terms.len()
    }

    pub(crate) fn estimated_canonical_terms_json_bytes(&self) -> Result<usize, CertError> {
        let mut bytes = 2usize;
        for (argument, coefficient) in &self.terms {
            bytes = bytes
                .checked_add(192)
                .and_then(|value| value.checked_add(integer_text_upper_bound(coefficient.numer())))
                .and_then(|value| value.checked_add(integer_text_upper_bound(coefficient.denom())))
                .and_then(|value| value.checked_add(integer_text_upper_bound(argument.numer())))
                .and_then(|value| value.checked_add(integer_text_upper_bound(argument.denom())))
                .ok_or_else(|| {
                    CertError::new(
                        "certificate_resource_limit",
                        "exact-expression serialization estimate overflowed",
                    )
                })?;
        }
        Ok(bytes)
    }

    pub(crate) fn canonical_terms(&self) -> Vec<ExactLogTerm> {
        self.terms
            .iter()
            .map(|(argument, coefficient)| ExactLogTerm {
                coefficient: rational_output(coefficient),
                log_argument: rational_output(argument),
            })
            .collect()
    }

    pub(crate) fn digest(&self) -> Result<String, CertError> {
        canonical_digest(&self.canonical_terms())
    }
}

fn integer_text_upper_bound(value: &Integer) -> usize {
    let magnitude_digits_upper_bound = usize::try_from(value.significant_bits())
        .unwrap_or(usize::MAX)
        .max(1);
    magnitude_digits_upper_bound.saturating_add(usize::from(value < &0))
}

pub(crate) fn rational_output(value: &Rational) -> ExactRational {
    ExactRational {
        numerator: value.numer().to_string(),
        denominator: value.denom().to_string(),
    }
}

#[cfg(test)]
mod tests {
    use rug::Rational;

    use super::LogExpression;

    #[test]
    fn add_term_should_remove_coefficients_that_cancel_exactly() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(3), Rational::from((2, 3)))
            .expect("valid term");
        expression
            .add_term(Rational::from(-3), Rational::from((2, 3)))
            .expect("valid term");

        assert!(expression.is_symbolic_zero());
    }

    #[test]
    fn add_term_should_remove_log_of_one() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(7), Rational::from(1))
            .expect("valid term");

        assert!(expression.is_symbolic_zero());
    }

    #[test]
    fn add_term_should_reject_zero_argument() {
        let mut expression = LogExpression::default();

        let error = expression
            .add_term(Rational::from(1), Rational::from(0))
            .expect_err("zero log argument must fail");

        assert_eq!(error.code(), "nonpositive_log_argument");
    }
}
