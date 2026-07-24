use std::cmp::Ordering;
use std::str::FromStr;

use rug::Integer;
use serde::{Deserialize, Serialize};

use crate::digest::{canonical_digest, sha256_hex};
use crate::error::CertError;
use crate::resource::{
    DEFINITION_REVISION, INPUT_SCHEMA, MAX_COUNT_DIGITS, MAX_INPUT_BYTES, MAX_ROWS,
    MAX_STATE_WIDTH, MAX_TOKEN_BYTES, MAX_TOTAL_COUNT_BITS, RESOURCE_POLICY_ID, UNITS,
};

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct InputDocument {
    pub(crate) schema: String,
    pub(crate) definition_revision: String,
    pub(crate) units: String,
    pub(crate) resource_policy_id: String,
    pub(crate) rows: Vec<InputRow>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct InputRow {
    pub(crate) source_states: [Vec<String>; 2],
    pub(crate) target_state: Vec<String>,
    pub(crate) count: String,
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub(crate) struct StateKey {
    pub(crate) source_one: Vec<String>,
    pub(crate) source_two: Vec<String>,
    pub(crate) target: Vec<String>,
}

#[derive(Clone, Debug)]
pub(crate) struct CountRow {
    pub(crate) state: StateKey,
    pub(crate) count: Integer,
}

#[derive(Clone, Debug)]
pub(crate) struct NormalizedInput {
    pub(crate) rows: Vec<CountRow>,
    pub(crate) total_count: Integer,
    pub(crate) source_widths: [usize; 2],
    pub(crate) target_width: usize,
    pub(crate) raw_input_sha256: String,
    pub(crate) semantic_input_sha256: String,
}

pub(crate) fn parse_and_validate(bytes: &[u8]) -> Result<NormalizedInput, CertError> {
    if bytes.len() > MAX_INPUT_BYTES {
        return Err(CertError::new(
            "input_too_large",
            format!(
                "input has {} bytes; maximum is {MAX_INPUT_BYTES}",
                bytes.len()
            ),
        ));
    }

    let document: InputDocument = serde_json::from_slice(bytes).map_err(|error| {
        CertError::new(
            "invalid_json_or_schema",
            format!("strict JSON decoding failed: {error}"),
        )
    })?;
    validate_document(bytes, document)
}

fn validate_document(
    raw_bytes: &[u8],
    document: InputDocument,
) -> Result<NormalizedInput, CertError> {
    if document.schema != INPUT_SCHEMA {
        return Err(CertError::new(
            "unsupported_schema",
            format!(
                "schema must be {INPUT_SCHEMA:?}, found {:?}",
                document.schema
            ),
        ));
    }
    if document.definition_revision != DEFINITION_REVISION {
        return Err(CertError::new(
            "unsupported_definition_revision",
            format!(
                "definition_revision must be {DEFINITION_REVISION:?}, found {:?}",
                document.definition_revision
            ),
        ));
    }
    if document.units != UNITS {
        return Err(CertError::new(
            "unsupported_units",
            format!("units must be {UNITS:?}, found {:?}", document.units),
        ));
    }
    if document.resource_policy_id != RESOURCE_POLICY_ID {
        return Err(CertError::new(
            "unsupported_resource_policy",
            format!(
                "resource_policy_id must be {RESOURCE_POLICY_ID:?}, found {:?}",
                document.resource_policy_id
            ),
        ));
    }
    if document.rows.is_empty() || document.rows.len() > MAX_ROWS {
        return Err(CertError::new(
            "invalid_row_count",
            format!("row count must be in 1..={MAX_ROWS}"),
        ));
    }

    let first = document
        .rows
        .first()
        .ok_or_else(|| CertError::internal("nonempty row check lost its first row"))?;
    let source_widths = [first.source_states[0].len(), first.source_states[1].len()];
    let target_width = first.target_state.len();
    validate_width(source_widths[0], "source one")?;
    validate_width(source_widths[1], "source two")?;
    validate_width(target_width, "target")?;

    let mut normalized_rows = Vec::with_capacity(document.rows.len());
    let mut total_count = Integer::from(0);
    let mut previous_state: Option<StateKey> = None;

    for (index, row) in document.rows.iter().enumerate() {
        if row.source_states[0].len() != source_widths[0]
            || row.source_states[1].len() != source_widths[1]
            || row.target_state.len() != target_width
        {
            return Err(CertError::new(
                "inconsistent_state_width",
                format!("row {index} does not match the first row's fixed state widths"),
            ));
        }
        validate_tokens(&row.source_states[0], index, "source one")?;
        validate_tokens(&row.source_states[1], index, "source two")?;
        validate_tokens(&row.target_state, index, "target")?;

        let state = StateKey {
            source_one: row.source_states[0].clone(),
            source_two: row.source_states[1].clone(),
            target: row.target_state.clone(),
        };
        if let Some(previous) = &previous_state {
            match state.cmp(previous) {
                Ordering::Less => {
                    return Err(CertError::new(
                        "noncanonical_row_order",
                        format!("row {index} is not in canonical lexicographic order"),
                    ));
                }
                Ordering::Equal => {
                    return Err(CertError::new(
                        "duplicate_state",
                        format!("row {index} duplicates the preceding categorical state"),
                    ));
                }
                Ordering::Greater => {}
            }
        }

        let count = parse_count(&row.count, index)?;
        total_count += &count;
        if total_count.significant_bits() > MAX_TOTAL_COUNT_BITS {
            return Err(CertError::new(
                "total_count_too_large",
                format!("total count exceeds the {MAX_TOTAL_COUNT_BITS}-bit structural limit"),
            ));
        }
        previous_state = Some(state.clone());
        normalized_rows.push(CountRow { state, count });
    }

    let semantic_input_sha256 = canonical_digest(&document)?;
    Ok(NormalizedInput {
        rows: normalized_rows,
        total_count,
        source_widths,
        target_width,
        raw_input_sha256: sha256_hex(raw_bytes),
        semantic_input_sha256,
    })
}

fn validate_width(width: usize, label: &str) -> Result<(), CertError> {
    if width == 0 || width > MAX_STATE_WIDTH {
        return Err(CertError::new(
            "invalid_state_width",
            format!("{label} width must be in 1..={MAX_STATE_WIDTH}"),
        ));
    }
    Ok(())
}

fn validate_tokens(tokens: &[String], row: usize, label: &str) -> Result<(), CertError> {
    for (column, token) in tokens.iter().enumerate() {
        if token.is_empty() || token.len() > MAX_TOKEN_BYTES {
            return Err(CertError::new(
                "invalid_state_token",
                format!(
                    "row {row} {label} column {column} token length must be in 1..={MAX_TOKEN_BYTES}"
                ),
            ));
        }
        if !token.bytes().all(is_canonical_token_byte) {
            return Err(CertError::new(
                "invalid_state_token",
                format!("row {row} {label} column {column} must match [A-Za-z0-9._:+-]+"),
            ));
        }
    }
    Ok(())
}

fn is_canonical_token_byte(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b':' | b'+' | b'-')
}

fn parse_count(text: &str, row: usize) -> Result<Integer, CertError> {
    if text.is_empty()
        || text.len() > MAX_COUNT_DIGITS
        || text.starts_with('0')
        || !text.bytes().all(|byte| byte.is_ascii_digit())
    {
        return Err(CertError::new(
            "invalid_count",
            format!(
                "row {row} count must match [1-9][0-9]* with at most {MAX_COUNT_DIGITS} digits"
            ),
        ));
    }
    let count = Integer::from_str(text).map_err(|error| {
        CertError::new(
            "invalid_count",
            format!("row {row} count cannot be parsed as an exact integer: {error}"),
        )
    })?;
    if count <= 0 {
        return Err(CertError::internal(
            "canonical positive count parsed as nonpositive",
        ));
    }
    Ok(count)
}

#[cfg(test)]
pub(crate) fn canonical_document(rows: Vec<InputRow>) -> InputDocument {
    InputDocument {
        schema: INPUT_SCHEMA.to_owned(),
        definition_revision: DEFINITION_REVISION.to_owned(),
        units: UNITS.to_owned(),
        resource_policy_id: RESOURCE_POLICY_ID.to_owned(),
        rows,
    }
}
