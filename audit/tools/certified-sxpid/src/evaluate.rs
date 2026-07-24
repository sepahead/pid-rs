use crate::directed::{evaluate, Enclosure};
use crate::error::CertError;
use crate::extract::ExactExtraction;
use crate::report::{expressions, EvaluationResult};
use crate::resource::PrecisionPolicy;

pub(crate) fn evaluate_all(
    extraction: &ExactExtraction,
    policy: &PrecisionPolicy,
) -> Result<EvaluationResult, CertError> {
    policy.validate()?;
    let expressions = expressions(extraction);
    if expressions.len() != 24 {
        return Err(CertError::internal(
            "precision engine requires exactly 24 expressions",
        ));
    }

    let mut precision = policy.initial_bits;
    let mut aggregate: Option<Vec<Enclosure>> = None;
    let mut intersections_checked = 0usize;

    for iteration_index in 0..policy.maximum_iterations {
        let current = expressions
            .iter()
            .map(|expression| evaluate(expression, precision))
            .collect::<Result<Vec<_>, _>>()?;

        aggregate = Some(if let Some(previous) = aggregate {
            let intersections = previous
                .iter()
                .zip(&current)
                .map(|(left, right)| left.intersect(right))
                .collect::<Result<Vec<_>, _>>()?;
            intersections_checked = intersections_checked
                .checked_add(intersections.len())
                .ok_or_else(|| CertError::internal("interval-intersection counter overflow"))?;
            intersections
        } else {
            current
        });

        let accepted = aggregate
            .as_ref()
            .ok_or_else(|| CertError::internal("precision engine lost its aggregate"))?
            .iter()
            .all(|interval| interval.width() <= policy.target_width);
        if accepted {
            return Ok(EvaluationResult {
                intervals: aggregate
                    .ok_or_else(|| CertError::internal("accepted aggregate is absent"))?,
                final_precision_bits: precision,
                iterations: iteration_index + 1,
                successive_intersections_checked: intersections_checked,
            });
        }

        if precision == policy.maximum_bits {
            break;
        }
        precision = policy.next_precision(precision);
    }

    Err(CertError::new(
        "precision_limit",
        format!(
            "the {}-bit maximum and {}-iteration limit did not meet the exact target width",
            policy.maximum_bits, policy.maximum_iterations
        ),
    ))
}
