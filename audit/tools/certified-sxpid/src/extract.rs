use std::collections::BTreeMap;

use rug::{Integer, Rational};
use serde::Serialize;

use crate::error::CertError;
use crate::exact::LogExpression;
use crate::lattice2::{self, ATOM_IDS, MOBIUS_ATOM_FROM_CUMULATIVE, NODE_IDS, NODE_MASKS};
use crate::resource::MAX_CUMULATIVE_EXTRACTION_TERMS;
use crate::schema::{NormalizedInput, StateKey};

#[derive(Clone, Debug)]
pub(crate) struct ExactComponents {
    pub(crate) informative: [LogExpression; 4],
    pub(crate) misinformative: [LogExpression; 4],
    pub(crate) net: [LogExpression; 4],
}

#[derive(Clone, Debug)]
pub(crate) struct ExactExtraction {
    pub(crate) cumulative: ExactComponents,
    pub(crate) atoms: ExactComponents,
    pub(crate) checks: ExtractionChecks,
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct ExtractionChecks {
    pub(crate) positive_mass_constraints_checked: usize,
    pub(crate) local_net_ratio_identities_checked: usize,
    pub(crate) self_redundancy_identities_checked: usize,
    pub(crate) exact_mobius_reconstructions_checked: usize,
    pub(crate) all_passed: bool,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum SourceState {
    One(Vec<String>),
    Two(Vec<String>),
    Joint(Vec<String>, Vec<String>),
}

pub(crate) fn extract(input: &NormalizedInput) -> Result<ExactExtraction, CertError> {
    lattice2::validate_integer_matrices()?;

    let mut target_masses = BTreeMap::<Vec<String>, Integer>::new();
    for row in &input.rows {
        add_mass(&mut target_masses, row.state.target.clone(), &row.count);
    }

    let mut cumulative = ExactComponents {
        informative: std::array::from_fn(|_| LogExpression::default()),
        misinformative: std::array::from_fn(|_| LogExpression::default()),
        net: std::array::from_fn(|_| LogExpression::default()),
    };
    let mut constraint_checks = 0usize;
    let mut ratio_checks = 0usize;

    for realization in &input.rows {
        let target_mass = target_masses
            .get(&realization.state.target)
            .ok_or_else(|| CertError::internal("target marginal omitted an observed state"))?;
        let weight = positive_ratio(&realization.count, &input.total_count, "row weight")?;

        for (node_index, masks) in NODE_MASKS.iter().enumerate() {
            let union_mass = event_mass(input, &realization.state, masks, false);
            let target_union_mass = event_mass(input, &realization.state, masks, true);
            validate_event_masses(
                &realization.count,
                &input.total_count,
                &union_mass,
                target_mass,
                &target_union_mass,
                NODE_IDS[node_index],
            )?;
            constraint_checks = constraint_checks
                .checked_add(1)
                .ok_or_else(|| CertError::internal("constraint-check counter overflow"))?;

            let plus_argument =
                positive_ratio(&input.total_count, &union_mass, "informative log argument")?;
            let minus_argument = positive_ratio(
                target_mass,
                &target_union_mass,
                "misinformative log argument",
            )?;

            let mut net_numerator = input.total_count.clone();
            net_numerator *= &target_union_mass;
            let mut net_denominator = union_mass.clone();
            net_denominator *= target_mass;
            let net_argument =
                positive_ratio(&net_numerator, &net_denominator, "net log argument")?;

            let mut derived_net_argument = plus_argument.clone();
            derived_net_argument /= &minus_argument;
            if derived_net_argument != net_argument {
                return Err(CertError::internal(format!(
                    "exact local net ratio identity failed at node {}",
                    NODE_IDS[node_index]
                )));
            }
            ratio_checks = ratio_checks
                .checked_add(1)
                .ok_or_else(|| CertError::internal("ratio-check counter overflow"))?;

            cumulative.informative[node_index].add_term(weight.clone(), plus_argument)?;
            cumulative.misinformative[node_index].add_term(weight.clone(), minus_argument)?;
            cumulative.net[node_index].add_term(weight.clone(), net_argument)?;
        }
        validate_cumulative_resource_growth(&cumulative)?;
    }

    let mutual_information = [
        mutual_information_expression(input, 0)?,
        mutual_information_expression(input, 1)?,
        mutual_information_expression(input, 2)?,
    ];
    for index in 0..3 {
        if cumulative.net[index] != mutual_information[index] {
            return Err(CertError::internal(format!(
                "exact self-redundancy identity failed at node {}",
                NODE_IDS[index]
            )));
        }
    }

    let atoms = ExactComponents {
        informative: lattice2::invert(&cumulative.informative)?,
        misinformative: lattice2::invert(&cumulative.misinformative)?,
        net: lattice2::invert(&cumulative.net)?,
    };
    lattice2::validate_reconstruction(&cumulative.informative, &atoms.informative)?;
    lattice2::validate_reconstruction(&cumulative.misinformative, &atoms.misinformative)?;
    lattice2::validate_reconstruction(&cumulative.net, &atoms.net)?;

    validate_component_dimensions(&cumulative, &atoms)?;
    Ok(ExactExtraction {
        cumulative,
        atoms,
        checks: ExtractionChecks {
            positive_mass_constraints_checked: constraint_checks,
            local_net_ratio_identities_checked: ratio_checks,
            self_redundancy_identities_checked: 3,
            exact_mobius_reconstructions_checked: 12,
            all_passed: true,
        },
    })
}

fn validate_cumulative_resource_growth(cumulative: &ExactComponents) -> Result<(), CertError> {
    let total_terms = cumulative
        .informative
        .iter()
        .chain(&cumulative.misinformative)
        .chain(&cumulative.net)
        .try_fold(0usize, |total, expression| {
            total.checked_add(expression.len()).ok_or_else(|| {
                CertError::new(
                    "certificate_resource_limit",
                    "cumulative exact-expression term count overflowed",
                )
            })
        })?;
    if total_terms > MAX_CUMULATIVE_EXTRACTION_TERMS {
        return Err(CertError::new(
            "certificate_resource_limit",
            format!(
                "cumulative extraction reached {total_terms} terms; maximum is {MAX_CUMULATIVE_EXTRACTION_TERMS}"
            ),
        ));
    }
    Ok(())
}

fn validate_component_dimensions(
    cumulative: &ExactComponents,
    atoms: &ExactComponents,
) -> Result<(), CertError> {
    let cumulative_sets = [
        &cumulative.informative,
        &cumulative.misinformative,
        &cumulative.net,
    ];
    let atom_sets = [&atoms.informative, &atoms.misinformative, &atoms.net];
    if cumulative_sets
        .iter()
        .any(|set| set.len() != NODE_IDS.len())
        || atom_sets.iter().any(|set| set.len() != ATOM_IDS.len())
        || MOBIUS_ATOM_FROM_CUMULATIVE.len() != ATOM_IDS.len()
    {
        return Err(CertError::internal(
            "two-source extraction did not produce all 24 coordinates",
        ));
    }
    Ok(())
}

fn validate_event_masses(
    row_count: &Integer,
    total: &Integer,
    union: &Integer,
    target: &Integer,
    target_union: &Integer,
    node: &str,
) -> Result<(), CertError> {
    if row_count <= &0
        || row_count > total
        || row_count > target_union
        || union <= &0
        || union > total
        || target_union <= &0
        || target_union > union
        || target_union > target
        || target > total
    {
        return Err(CertError::internal(format!(
            "event-count constraints failed at node {node}"
        )));
    }
    Ok(())
}

fn event_mass(
    input: &NormalizedInput,
    realization: &StateKey,
    masks: &[u8],
    require_target: bool,
) -> Integer {
    let mut mass = Integer::from(0);
    for row in &input.rows {
        if require_target && row.state.target != realization.target {
            continue;
        }
        if masks
            .iter()
            .any(|mask| matches_collection(&row.state, realization, *mask))
        {
            mass += &row.count;
        }
    }
    mass
}

fn matches_collection(state: &StateKey, realization: &StateKey, mask: u8) -> bool {
    (mask & 0b01 == 0 || state.source_one == realization.source_one)
        && (mask & 0b10 == 0 || state.source_two == realization.source_two)
}

fn positive_ratio(
    numerator: &Integer,
    denominator: &Integer,
    context: &str,
) -> Result<Rational, CertError> {
    if numerator <= &0 || denominator <= &0 {
        return Err(CertError::internal(format!(
            "{context} received a nonpositive exact integer"
        )));
    }
    Ok(Rational::from((numerator.clone(), denominator.clone())))
}

fn add_mass<K: Ord>(masses: &mut BTreeMap<K, Integer>, key: K, count: &Integer) {
    masses
        .entry(key)
        .and_modify(|mass| *mass += count)
        .or_insert_with(|| count.clone());
}

fn source_state(state: &StateKey, source_index: usize) -> Result<SourceState, CertError> {
    match source_index {
        0 => Ok(SourceState::One(state.source_one.clone())),
        1 => Ok(SourceState::Two(state.source_two.clone())),
        2 => Ok(SourceState::Joint(
            state.source_one.clone(),
            state.source_two.clone(),
        )),
        _ => Err(CertError::internal(
            "unsupported self-redundancy source index",
        )),
    }
}

fn mutual_information_expression(
    input: &NormalizedInput,
    source_index: usize,
) -> Result<LogExpression, CertError> {
    let mut source_masses = BTreeMap::<SourceState, Integer>::new();
    let mut target_masses = BTreeMap::<Vec<String>, Integer>::new();
    let mut joint_masses = BTreeMap::<(SourceState, Vec<String>), Integer>::new();

    for row in &input.rows {
        let source = source_state(&row.state, source_index)?;
        add_mass(&mut source_masses, source.clone(), &row.count);
        add_mass(&mut target_masses, row.state.target.clone(), &row.count);
        add_mass(
            &mut joint_masses,
            (source, row.state.target.clone()),
            &row.count,
        );
    }

    let mut expression = LogExpression::default();
    for ((source, target), joint_mass) in joint_masses {
        let source_mass = source_masses
            .get(&source)
            .ok_or_else(|| CertError::internal("MI source marginal is absent"))?;
        let target_mass = target_masses
            .get(&target)
            .ok_or_else(|| CertError::internal("MI target marginal is absent"))?;

        let mut numerator = joint_mass.clone();
        numerator *= &input.total_count;
        let mut denominator = source_mass.clone();
        denominator *= target_mass;
        let argument = positive_ratio(&numerator, &denominator, "MI log argument")?;
        let coefficient = positive_ratio(&joint_mass, &input.total_count, "MI weight")?;
        expression.add_term(coefficient, argument)?;
    }
    Ok(expression)
}

#[cfg(test)]
mod tests {
    use rug::{Integer, Rational};
    use serde_json::to_vec;

    use crate::schema::{canonical_document, parse_and_validate, InputRow};

    use super::{extract, validate_event_masses};

    fn xor_input() -> Vec<u8> {
        let rows = vec![
            InputRow {
                source_states: [vec![String::from("0")], vec![String::from("0")]],
                target_state: vec![String::from("0")],
                count: String::from("1"),
            },
            InputRow {
                source_states: [vec![String::from("0")], vec![String::from("1")]],
                target_state: vec![String::from("1")],
                count: String::from("1"),
            },
            InputRow {
                source_states: [vec![String::from("1")], vec![String::from("0")]],
                target_state: vec![String::from("1")],
                count: String::from("1"),
            },
            InputRow {
                source_states: [vec![String::from("1")], vec![String::from("1")]],
                target_state: vec![String::from("0")],
                count: String::from("1"),
            },
        ];
        to_vec(&canonical_document(rows)).expect("serialize test input")
    }

    #[test]
    fn extract_should_produce_all_xor_coordinates_and_checks() {
        let input = parse_and_validate(&xor_input()).expect("valid XOR input");

        let result = extract(&input).expect("XOR extraction");

        assert_eq!(
            result.checks.positive_mass_constraints_checked,
            input.rows.len() * 4
        );
        let expected_net_atoms = [
            signed_log(-1, Rational::from((2, 3))),
            signed_log(-1, Rational::from((2, 3))),
            two_logs((1, Rational::from((2, 3))), (1, Rational::from(2))),
            single_log(Rational::from((2, 3))),
        ];
        assert_eq!(
            result.atoms.net, expected_net_atoms,
            "XOR must produce exact net atoms [ln(3/2), ln(3/2), ln(4/3), ln(2/3)]"
        );
    }

    #[test]
    fn constant_target_net_should_be_symbolically_zero_at_every_cumulative_node() {
        let rows = vec![
            InputRow {
                source_states: [vec![String::from("0")], vec![String::from("0")]],
                target_state: vec![String::from("only")],
                count: String::from("2"),
            },
            InputRow {
                source_states: [vec![String::from("1")], vec![String::from("1")]],
                target_state: vec![String::from("only")],
                count: String::from("3"),
            },
        ];
        let bytes = to_vec(&canonical_document(rows)).expect("serialize test input");
        let input = parse_and_validate(&bytes).expect("valid constant-target input");

        let result = extract(&input).expect("constant-target extraction");

        assert!(result
            .cumulative
            .net
            .iter()
            .all(LogExpression::is_symbolic_zero));
    }

    #[test]
    fn event_constraints_should_reject_keyed_mass_above_target_union() {
        let error = validate_event_masses(
            &Integer::from(2),
            &Integer::from(4),
            &Integer::from(3),
            &Integer::from(3),
            &Integer::from(1),
            "red",
        )
        .expect_err("the keyed realization must be contained in the target-restricted union");

        assert!(error.to_string().contains("event-count constraints failed"));
    }

    #[test]
    fn event_constraints_should_reject_target_union_above_source_union() {
        let error = validate_event_masses(
            &Integer::from(1),
            &Integer::from(4),
            &Integer::from(2),
            &Integer::from(4),
            &Integer::from(3),
            "red",
        )
        .expect_err("the target-restricted union must be contained in the source union");

        assert!(error.to_string().contains("event-count constraints failed"));
    }

    use crate::exact::LogExpression;

    fn single_log(argument: Rational) -> LogExpression {
        signed_log(1, argument)
    }

    fn signed_log(coefficient: i32, argument: Rational) -> LogExpression {
        let mut expression = LogExpression::default();
        expression
            .add_term(Rational::from(coefficient), argument)
            .expect("positive analytic log argument");
        expression
    }

    fn two_logs(left: (i32, Rational), right: (i32, Rational)) -> LogExpression {
        let mut expression = signed_log(left.0, left.1);
        expression
            .add_term(Rational::from(right.0), right.1)
            .expect("positive analytic log argument");
        expression
    }
}
