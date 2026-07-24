use rug::{Integer, Rational};
use serde::Serialize;

use crate::digest::canonical_digest;
use crate::error::CertError;

pub(crate) const INPUT_SCHEMA: &str = "pid-rs/categorical-sxpid2-count-table/v1";
pub(crate) const DEFINITION_REVISION: &str = "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1";
pub(crate) const RESOURCE_POLICY_ID: &str = "sxpid2-certification-default-v1";
pub(crate) const UNITS: &str = "nats";

pub const MAX_INPUT_BYTES: usize = 4 * 1024 * 1024;
pub(crate) const MAX_ROWS: usize = 4096;
pub(crate) const MAX_STATE_WIDTH: usize = 32;
pub(crate) const MAX_TOKEN_BYTES: usize = 128;
pub(crate) const MAX_COUNT_DIGITS: usize = 1024;
pub(crate) const MAX_TOTAL_COUNT_BITS: u32 = 8192;
pub(crate) const MAX_TERMS_PER_EXPRESSION: usize = 4096;
pub(crate) const MAX_TOTAL_EXACT_TERMS: usize = 8192;
// One cumulative term can enter at most four two-source atoms through the pinned Möbius matrix.
// Bounding cumulative terms by floor(total / (1 + 4)) therefore bounds the later cumulative-plus-
// atom representation before any beneficial exact cancellation.
pub(crate) const MAX_CUMULATIVE_EXTRACTION_TERMS: usize = MAX_TOTAL_EXACT_TERMS / 5;
pub(crate) const MAX_ESTIMATED_EXACT_TERM_JSON_BYTES: usize = 8 * 1024 * 1024;
pub(crate) const MAX_CANONICAL_PAYLOAD_BYTES: usize = 10 * 1024 * 1024;

#[derive(Clone, Debug)]
pub(crate) struct PrecisionPolicy {
    pub(crate) initial_bits: u32,
    pub(crate) maximum_bits: u32,
    pub(crate) maximum_iterations: u32,
    pub(crate) growth_factor: u32,
    pub(crate) target_width: Rational,
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct PrecisionPolicyEvidence {
    pub(crate) id: &'static str,
    pub(crate) initial_bits: u32,
    pub(crate) maximum_bits: u32,
    pub(crate) maximum_iterations: u32,
    pub(crate) growth_factor: u32,
    pub(crate) target_width: TargetWidthEvidence,
    pub(crate) structural_limits: StructuralLimitsEvidence,
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct TargetWidthEvidence {
    pub(crate) significand: &'static str,
    pub(crate) exponent2: i64,
}

#[derive(Clone, Debug, Serialize)]
pub(crate) struct StructuralLimitsEvidence {
    pub(crate) maximum_input_bytes: usize,
    pub(crate) maximum_rows: usize,
    pub(crate) maximum_state_width: usize,
    pub(crate) maximum_token_bytes: usize,
    pub(crate) maximum_count_digits: usize,
    pub(crate) maximum_total_count_bits: u32,
    pub(crate) maximum_terms_per_expression: usize,
    pub(crate) maximum_total_exact_terms: usize,
    pub(crate) maximum_cumulative_extraction_terms: usize,
    pub(crate) maximum_estimated_exact_term_json_bytes: usize,
    pub(crate) maximum_canonical_payload_bytes: usize,
}

impl PrecisionPolicy {
    pub(crate) fn default_v1() -> Self {
        let denominator = Integer::from(1) << 160;
        Self {
            initial_bits: 128,
            maximum_bits: 4096,
            maximum_iterations: 6,
            growth_factor: 2,
            target_width: Rational::from((Integer::from(1), denominator)),
        }
    }

    #[cfg(test)]
    pub(crate) fn for_test(
        initial_bits: u32,
        maximum_bits: u32,
        maximum_iterations: u32,
        growth_factor: u32,
        target_width: Rational,
    ) -> Self {
        Self {
            initial_bits,
            maximum_bits,
            maximum_iterations,
            growth_factor,
            target_width,
        }
    }

    pub(crate) fn validate(&self) -> Result<(), CertError> {
        if self.initial_bits < 32 {
            return Err(CertError::new(
                "invalid_precision_policy",
                "initial precision must be at least 32 bits",
            ));
        }
        if self.maximum_bits < self.initial_bits || self.maximum_bits > 65_536 {
            return Err(CertError::new(
                "invalid_precision_policy",
                "maximum precision must be between the initial precision and 65536 bits",
            ));
        }
        if self.maximum_iterations == 0 || self.maximum_iterations > 32 {
            return Err(CertError::new(
                "invalid_precision_policy",
                "maximum iterations must be in 1..=32",
            ));
        }
        if !(2..=16).contains(&self.growth_factor) {
            return Err(CertError::new(
                "invalid_precision_policy",
                "precision growth factor must be in 2..=16",
            ));
        }
        if self.target_width <= 0 {
            return Err(CertError::new(
                "invalid_precision_policy",
                "target interval width must be positive",
            ));
        }
        if self.target_width.numer() != &Integer::from(1)
            || !self.target_width.denom().is_power_of_two()
        {
            return Err(CertError::new(
                "invalid_precision_policy",
                "target interval width must be exactly one divided by a power of two",
            ));
        }
        Ok(())
    }

    pub(crate) fn next_precision(&self, current: u32) -> u32 {
        current
            .checked_mul(self.growth_factor)
            .unwrap_or(self.maximum_bits)
            .min(self.maximum_bits)
    }

    pub(crate) fn evidence(&self) -> PrecisionPolicyEvidence {
        PrecisionPolicyEvidence {
            id: RESOURCE_POLICY_ID,
            initial_bits: self.initial_bits,
            maximum_bits: self.maximum_bits,
            maximum_iterations: self.maximum_iterations,
            growth_factor: self.growth_factor,
            target_width: TargetWidthEvidence {
                significand: "1",
                exponent2: 1 - i64::from(self.target_width.denom().significant_bits()),
            },
            structural_limits: StructuralLimitsEvidence {
                maximum_input_bytes: MAX_INPUT_BYTES,
                maximum_rows: MAX_ROWS,
                maximum_state_width: MAX_STATE_WIDTH,
                maximum_token_bytes: MAX_TOKEN_BYTES,
                maximum_count_digits: MAX_COUNT_DIGITS,
                maximum_total_count_bits: MAX_TOTAL_COUNT_BITS,
                maximum_terms_per_expression: MAX_TERMS_PER_EXPRESSION,
                maximum_total_exact_terms: MAX_TOTAL_EXACT_TERMS,
                maximum_cumulative_extraction_terms: MAX_CUMULATIVE_EXTRACTION_TERMS,
                maximum_estimated_exact_term_json_bytes: MAX_ESTIMATED_EXACT_TERM_JSON_BYTES,
                maximum_canonical_payload_bytes: MAX_CANONICAL_PAYLOAD_BYTES,
            },
        }
    }

    pub(crate) fn digest(&self) -> Result<String, CertError> {
        canonical_digest(&self.evidence())
    }
}
