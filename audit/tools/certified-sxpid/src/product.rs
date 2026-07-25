use rug::ops::Pow;
use rug::{Integer, Rational};
use serde::Serialize;

use crate::error::CertError;
use crate::exact::LogExpression;
use crate::resource::{
    MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT, MAX_EXACT_PRODUCT_PROJECTED_BITS_PER_EXPRESSION,
    MAX_EXACT_PRODUCT_TERMS_PER_EXPRESSION, MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS,
};

const DECISION_SOURCE: &str = "bounded_exact_rational_product_after_integer_denominator_clearing";

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum ExactProductSign {
    Negative,
    Zero,
    Positive,
}

impl ExactProductSign {
    pub(crate) fn decision(self) -> &'static str {
        match self {
            Self::Negative => "certified_negative",
            Self::Zero => "certified_exact_zero",
            Self::Positive => "certified_positive",
        }
    }
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct ExactProductEvidence {
    status: &'static str,
    decision_source: &'static str,
    decision: Option<&'static str>,
    exact_zero_witness: Option<&'static str>,
    preflight: ExactProductPreflightEvidence,
}

#[derive(Clone, Debug, Serialize)]
struct ExactProductPreflightEvidence {
    term_count: usize,
    maximum_absolute_exponent: String,
    projected_product_bits_upper_bound: String,
    within_per_expression_limits: bool,
    admitted_under_total_projected_bits_limit: bool,
}

#[derive(Clone, Debug)]
pub(crate) struct ExactProductResult {
    pub(crate) evidence: ExactProductEvidence,
    pub(crate) sign: Option<ExactProductSign>,
}

#[derive(Clone, Debug)]
struct ProductFactor {
    argument: Rational,
    exponent_is_negative: bool,
    absolute_exponent: u32,
}

#[derive(Clone, Debug)]
struct ProductPlan {
    factors: Vec<ProductFactor>,
    term_count: usize,
    maximum_absolute_exponent: Integer,
    projected_product_bits_upper_bound: Integer,
    within_per_expression_limits: bool,
}

pub(crate) fn compare_all(
    expressions: &[&LogExpression],
    total_count: &Integer,
) -> Result<Vec<ExactProductResult>, CertError> {
    if total_count <= &0 {
        return Err(CertError::internal(
            "exact-product comparison received a nonpositive total count",
        ));
    }

    let plans = expressions
        .iter()
        .map(|expression| plan(expression, total_count))
        .collect::<Result<Vec<_>, _>>()?;
    let aggregate_projected_bits = plans
        .iter()
        .filter(|plan| plan.within_per_expression_limits)
        .try_fold(0u64, |sum, plan| {
            let projected = plan
                .projected_product_bits_upper_bound
                .to_u64()
                .ok_or_else(|| {
                    CertError::internal(
                        "admissible exact-product projection is not representable as u64",
                    )
                })?;
            sum.checked_add(projected).ok_or_else(|| {
                CertError::internal("aggregate exact-product projection overflowed u64")
            })
        })?;
    let aggregate_admitted = aggregate_projected_bits <= MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS;

    plans
        .into_iter()
        .map(|plan| {
            if !plan.within_per_expression_limits {
                return Ok(unavailable_result(
                    &plan,
                    "not_compared_per_expression_preflight_limit",
                    false,
                ));
            }
            if !aggregate_admitted && !plan.factors.is_empty() {
                return Ok(unavailable_result(
                    &plan,
                    "not_compared_total_preflight_limit",
                    false,
                ));
            }
            compare_plan(plan, true)
        })
        .collect()
}

fn plan(expression: &LogExpression, total_count: &Integer) -> Result<ProductPlan, CertError> {
    let mut maximum_absolute_exponent = Integer::from(0);
    let mut projected_product_bits_upper_bound = Integer::from(0);

    for (argument, coefficient) in expression.terms() {
        let mut cleared = coefficient.clone();
        cleared *= total_count;
        if cleared.denom() != &1 {
            return Err(CertError::internal(
                "n times an averaged exact-log coefficient is not an integer",
            ));
        }
        let exponent = cleared.numer().clone();
        if exponent == 0 {
            return Err(CertError::internal(
                "canonical exact-log expression produced a zero cleared exponent",
            ));
        }
        let absolute_exponent = exponent.clone().abs();
        if absolute_exponent > maximum_absolute_exponent {
            maximum_absolute_exponent = absolute_exponent.clone();
        }

        let argument_bits = u64::from(argument.numer().significant_bits())
            .checked_add(u64::from(argument.denom().significant_bits()))
            .ok_or_else(|| CertError::internal("exact-product argument bit estimate overflowed"))?;
        let mut term_projection = absolute_exponent.clone();
        term_projection *= argument_bits;
        projected_product_bits_upper_bound += term_projection;
    }

    let term_count = expression.len();
    let within_per_expression_limits = term_count <= MAX_EXACT_PRODUCT_TERMS_PER_EXPRESSION
        && maximum_absolute_exponent <= MAX_EXACT_PRODUCT_ABSOLUTE_EXPONENT
        && projected_product_bits_upper_bound <= MAX_EXACT_PRODUCT_PROJECTED_BITS_PER_EXPRESSION;
    let factors = if within_per_expression_limits {
        expression
            .terms()
            .map(|(argument, coefficient)| {
                let mut cleared = coefficient.clone();
                cleared *= total_count;
                let exponent = cleared.numer().clone();
                let absolute_exponent = exponent.clone().abs().to_u32().ok_or_else(|| {
                    CertError::internal(
                        "admitted exact-product exponent is not representable as u32",
                    )
                })?;
                Ok(ProductFactor {
                    argument: argument.clone(),
                    exponent_is_negative: exponent < 0,
                    absolute_exponent,
                })
            })
            .collect::<Result<Vec<_>, CertError>>()?
    } else {
        Vec::new()
    };

    Ok(ProductPlan {
        factors,
        term_count,
        maximum_absolute_exponent,
        projected_product_bits_upper_bound,
        within_per_expression_limits,
    })
}

fn compare_plan(
    plan: ProductPlan,
    admitted_under_total_projected_bits_limit: bool,
) -> Result<ExactProductResult, CertError> {
    let mut product = Rational::from(1);
    for factor in &plan.factors {
        let numerator_power = factor
            .argument
            .numer()
            .clone()
            .pow(factor.absolute_exponent);
        let denominator_power = factor
            .argument
            .denom()
            .clone()
            .pow(factor.absolute_exponent);
        let powered = if factor.exponent_is_negative {
            Rational::from((denominator_power, numerator_power))
        } else {
            Rational::from((numerator_power, denominator_power))
        };
        product *= powered;
    }

    if !plan.factors.is_empty() {
        let actual_bits = u64::from(product.numer().significant_bits())
            .checked_add(u64::from(product.denom().significant_bits()))
            .ok_or_else(|| CertError::internal("exact-product result bit count overflowed"))?;
        let projected_bits = plan
            .projected_product_bits_upper_bound
            .to_u64()
            .ok_or_else(|| CertError::internal("admitted exact-product projection overflowed"))?;
        if actual_bits > projected_bits {
            return Err(CertError::internal(
                "exact-product result exceeded its conservative preflight projection",
            ));
        }
    }

    let sign = if product > 1 {
        ExactProductSign::Positive
    } else if product < 1 {
        ExactProductSign::Negative
    } else {
        ExactProductSign::Zero
    };
    let decision = sign.decision();
    Ok(ExactProductResult {
        evidence: ExactProductEvidence {
            status: "compared",
            decision_source: DECISION_SOURCE,
            decision: Some(decision),
            exact_zero_witness: (sign == ExactProductSign::Zero)
                .then_some("exact_multiplicative_product_equals_one"),
            preflight: preflight_evidence(&plan, admitted_under_total_projected_bits_limit),
        },
        sign: Some(sign),
    })
}

fn unavailable_result(
    plan: &ProductPlan,
    status: &'static str,
    admitted_under_total_projected_bits_limit: bool,
) -> ExactProductResult {
    ExactProductResult {
        evidence: ExactProductEvidence {
            status,
            decision_source: DECISION_SOURCE,
            decision: None,
            exact_zero_witness: None,
            preflight: preflight_evidence(plan, admitted_under_total_projected_bits_limit),
        },
        sign: None,
    }
}

fn preflight_evidence(
    plan: &ProductPlan,
    admitted_under_total_projected_bits_limit: bool,
) -> ExactProductPreflightEvidence {
    ExactProductPreflightEvidence {
        term_count: plan.term_count,
        maximum_absolute_exponent: plan.maximum_absolute_exponent.to_string(),
        projected_product_bits_upper_bound: plan.projected_product_bits_upper_bound.to_string(),
        within_per_expression_limits: plan.within_per_expression_limits,
        admitted_under_total_projected_bits_limit,
    }
}

#[cfg(test)]
mod tests {
    use rug::{Integer, Rational};

    use crate::exact::LogExpression;
    use crate::resource::MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS;

    use super::{compare_all, ExactProductSign};

    #[test]
    fn nonempty_exact_log_expression_can_cancel_multiplicatively() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from((-1, 8)), Rational::from((8, 15)))
            .expect("valid first term");
        expression
            .add_term(Rational::from((1, 8)), Rational::from((4, 5)))
            .expect("valid second term");
        expression
            .add_term(Rational::from((1, 8)), Rational::from((8, 9)))
            .expect("valid third term");
        expression
            .add_term(Rational::from((1, 8)), Rational::from((4, 3)))
            .expect("valid fourth term");
        expression
            .add_term(Rational::from((-1, 8)), Rational::from((16, 9)))
            .expect("valid fifth term");

        assert!(!expression.is_symbolic_zero());
        let results = compare_all(&[&expression], &Integer::from(8))
            .expect("bounded product comparison must succeed");
        assert_eq!(results[0].sign, Some(ExactProductSign::Zero));
    }

    #[test]
    fn product_above_one_returns_positive_sign() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from((1, 2)), Rational::from((3, 2)))
            .expect("valid positive-sign term");

        let results = compare_all(&[&expression], &Integer::from(2))
            .expect("bounded product comparison must succeed");

        assert_eq!(results[0].sign, Some(ExactProductSign::Positive));
    }

    #[test]
    fn product_below_one_returns_negative_sign() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from((1, 2)), Rational::from((2, 3)))
            .expect("valid negative-sign term");

        let results = compare_all(&[&expression], &Integer::from(2))
            .expect("bounded product comparison must succeed");

        assert_eq!(results[0].sign, Some(ExactProductSign::Negative));
    }

    #[test]
    fn coefficient_not_cleared_by_total_count_is_rejected() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from((1, 3)), Rational::from((2, 3)))
            .expect("valid exact-log term");

        let error = compare_all(&[&expression], &Integer::from(2))
            .expect_err("nonintegral cleared exponent must fail closed");

        assert_eq!(error.code(), "internal_soundness_failure");
        assert_eq!(
            error.message(),
            "n times an averaged exact-log coefficient is not an integer"
        );
    }

    #[test]
    fn enormous_cleared_exponent_is_not_powered() {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(1), Rational::from((2, 3)))
            .expect("valid term");
        let total = Integer::from(1) << 8191;

        let results = compare_all(&[&expression], &total)
            .expect("resource fallback is a successful bounded outcome");
        assert_eq!(results[0].sign, None);
        assert_eq!(
            results[0].evidence.status,
            "not_compared_per_expression_preflight_limit"
        );
        assert!(!results[0].evidence.preflight.within_per_expression_limits);
    }

    fn aggregate_limit_expression() -> LogExpression {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(1), Rational::from((255, 128)))
            .expect("valid term at the per-expression projection limit");
        expression
    }

    #[test]
    fn aggregate_projection_over_limit_abstains_for_every_nonempty_admitted_plan() {
        let expressions = (0..5)
            .map(|_| aggregate_limit_expression())
            .collect::<Vec<_>>();
        let references = expressions.iter().collect::<Vec<_>>();
        let total = Integer::from(16_384);

        let results = compare_all(&references, &total)
            .expect("aggregate resource fallback is a successful bounded outcome");

        assert!(results.iter().all(|result| {
            result.sign.is_none()
                && result.evidence.status == "not_compared_total_preflight_limit"
                && result.evidence.preflight.within_per_expression_limits
                && !result
                    .evidence
                    .preflight
                    .admitted_under_total_projected_bits_limit
        }));
        let aggregate_projection = results
            .iter()
            .map(|result| {
                result
                    .evidence
                    .preflight
                    .projected_product_bits_upper_bound
                    .parse::<u64>()
                    .expect("bounded projection evidence")
            })
            .sum::<u64>();
        assert!(aggregate_projection > MAX_TOTAL_EXACT_PRODUCT_PROJECTED_BITS);
    }

    #[test]
    fn empty_expression_remains_exact_zero_when_nonempty_aggregate_is_over_limit() {
        let expressions = (0..5)
            .map(|_| aggregate_limit_expression())
            .collect::<Vec<_>>();
        let empty = LogExpression::default();
        let mut references = expressions.iter().collect::<Vec<_>>();
        references.push(&empty);

        let results = compare_all(&references, &Integer::from(16_384))
            .expect("an empty product remains a zero-cost exact comparison");
        let empty_result = results.last().expect("empty expression result");

        assert_eq!(empty_result.sign, Some(ExactProductSign::Zero));
        assert_eq!(empty_result.evidence.status, "compared");
        assert_eq!(empty_result.evidence.decision, Some("certified_exact_zero"));
        assert_eq!(
            empty_result.evidence.exact_zero_witness,
            Some("exact_multiplicative_product_equals_one")
        );
        assert!(
            empty_result
                .evidence
                .preflight
                .admitted_under_total_projected_bits_limit
        );
    }
}
