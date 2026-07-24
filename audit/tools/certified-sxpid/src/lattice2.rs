use serde::Serialize;

use crate::digest::canonical_digest;
use crate::error::CertError;
use crate::exact::LogExpression;

pub(crate) const NODE_MASKS: [&[u8]; 4] = [&[0b01], &[0b10], &[0b11], &[0b01, 0b10]];
pub(crate) const NODE_IDS: [&str; 4] = ["source_one", "source_two", "joint_sources", "redundancy"];
pub(crate) const ATOM_IDS: [&str; 4] = ["unique_one", "unique_two", "synergy", "redundancy"];

pub(crate) const MOBIUS_ATOM_FROM_CUMULATIVE: [[i32; 4]; 4] =
    [[1, 0, 0, -1], [0, 1, 0, -1], [-1, -1, 1, 1], [0, 0, 0, 1]];

pub(crate) const ZETA_CUMULATIVE_FROM_ATOM: [[i32; 4]; 4] =
    [[1, 0, 0, 1], [0, 1, 0, 1], [1, 1, 1, 1], [0, 0, 0, 1]];

#[derive(Clone, Debug, Serialize)]
pub(crate) struct LatticeEvidence {
    pub(crate) cumulative_node_order: [LatticeNodeEvidence; 4],
    pub(crate) atom_order: [&'static str; 4],
    pub(crate) mobius_atom_from_cumulative: [[i32; 4]; 4],
    pub(crate) zeta_cumulative_from_atom: [[i32; 4]; 4],
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct LatticeNodeEvidence {
    pub(crate) id: &'static str,
    pub(crate) source_collection_masks: &'static [u8],
}

pub(crate) fn evidence() -> LatticeEvidence {
    LatticeEvidence {
        cumulative_node_order: std::array::from_fn(|index| LatticeNodeEvidence {
            id: NODE_IDS[index],
            source_collection_masks: NODE_MASKS[index],
        }),
        atom_order: ATOM_IDS,
        mobius_atom_from_cumulative: MOBIUS_ATOM_FROM_CUMULATIVE,
        zeta_cumulative_from_atom: ZETA_CUMULATIVE_FROM_ATOM,
    }
}

pub(crate) fn digest() -> Result<String, CertError> {
    canonical_digest(&evidence())
}

pub(crate) fn validate_integer_matrices() -> Result<(), CertError> {
    for (row, zeta_row) in ZETA_CUMULATIVE_FROM_ATOM.iter().enumerate() {
        for (column, _) in MOBIUS_ATOM_FROM_CUMULATIVE[0].iter().enumerate() {
            let product = zeta_row
                .iter()
                .zip(MOBIUS_ATOM_FROM_CUMULATIVE.iter())
                .map(|(zeta_coefficient, mobius_row)| zeta_coefficient * mobius_row[column])
                .sum::<i32>();
            let expected = i32::from(row == column);
            if product != expected {
                return Err(CertError::internal(format!(
                    "two-source zeta and Möbius matrices are not inverse at ({row}, {column})"
                )));
            }
        }
    }
    Ok(())
}

pub(crate) fn invert(cumulative: &[LogExpression; 4]) -> Result<[LogExpression; 4], CertError> {
    Ok([
        LogExpression::linear_combination(cumulative, MOBIUS_ATOM_FROM_CUMULATIVE[0])?,
        LogExpression::linear_combination(cumulative, MOBIUS_ATOM_FROM_CUMULATIVE[1])?,
        LogExpression::linear_combination(cumulative, MOBIUS_ATOM_FROM_CUMULATIVE[2])?,
        LogExpression::linear_combination(cumulative, MOBIUS_ATOM_FROM_CUMULATIVE[3])?,
    ])
}

pub(crate) fn validate_reconstruction(
    cumulative: &[LogExpression; 4],
    atoms: &[LogExpression; 4],
) -> Result<(), CertError> {
    for row in 0..4 {
        let reconstructed =
            LogExpression::linear_combination(atoms, ZETA_CUMULATIVE_FROM_ATOM[row])?;
        if reconstructed != cumulative[row] {
            return Err(CertError::internal(format!(
                "exact zeta reconstruction failed at cumulative node {}",
                NODE_IDS[row]
            )));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use crate::resource::{MAX_CUMULATIVE_EXTRACTION_TERMS, MAX_TOTAL_EXACT_TERMS};

    use super::{validate_integer_matrices, MOBIUS_ATOM_FROM_CUMULATIVE};

    #[test]
    fn fixed_zeta_and_mobius_matrices_should_be_exact_inverses() {
        validate_integer_matrices().expect("fixed matrices must be inverse");
    }

    #[test]
    fn cumulative_term_budget_should_cover_worst_case_mobius_expansion() {
        let maximum_column_multiplicity = (0..4)
            .map(|column| {
                MOBIUS_ATOM_FROM_CUMULATIVE
                    .iter()
                    .filter(|row| row[column] != 0)
                    .count()
            })
            .max()
            .expect("nonempty matrix");

        assert_eq!(maximum_column_multiplicity, 4);
        assert!(
            MAX_CUMULATIVE_EXTRACTION_TERMS * (1 + maximum_column_multiplicity)
                <= MAX_TOTAL_EXACT_TERMS
        );
    }
}
