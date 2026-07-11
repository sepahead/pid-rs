use std::fmt;

use crate::support::SupportContract;

pub type PidResult<T> = Result<T, PidError>;

#[derive(Debug, Clone)]
pub enum PidError {
    ShapeMismatch {
        context: &'static str,
        expected_len: usize,
        actual_len: usize,
    },
    InvalidConfig {
        context: &'static str,
        message: &'static str,
    },
    RowCountMismatch {
        context: &'static str,
        left_rows: usize,
        right_rows: usize,
    },
    SourceDimensionMismatch {
        context: &'static str,
        left_cols: usize,
        right_cols: usize,
    },
    InvalidK {
        k: usize,
        n_samples: usize,
    },
    NonFiniteInput {
        context: &'static str,
    },
    SupportContractRequired {
        context: &'static str,
    },
    UnsupportedSupportContract {
        context: &'static str,
        contract: SupportContract,
    },
    ObservedContinuousSampleIncompatibility {
        context: &'static str,
        input_index: usize,
        coordinate: Option<usize>,
        unique_values: usize,
        n_samples: usize,
        max_multiplicity: usize,
    },
    NumericalInstability {
        context: &'static str,
    },
    AmbiguousKthNeighborShell {
        context: &'static str,
        query_index: usize,
        k: usize,
        radius: f64,
        interior_count: usize,
        boundary_count: usize,
    },
    NotImplemented {
        feature: &'static str,
    },
}

impl fmt::Display for PidError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            PidError::ShapeMismatch {
                context,
                expected_len,
                actual_len,
            } => write!(
                f,
                "{context}: shape mismatch (expected len {expected_len}, got {actual_len})"
            ),
            PidError::InvalidConfig { context, message } => {
                write!(f, "{context}: invalid config ({message})")
            }
            PidError::RowCountMismatch {
                context,
                left_rows,
                right_rows,
            } => write!(
                f,
                "{context}: row count mismatch (left {left_rows}, right {right_rows})"
            ),
            PidError::SourceDimensionMismatch {
                context,
                left_cols,
                right_cols,
            } => write!(
                f,
                "{context}: source dimension mismatch (left {left_cols} columns, right {right_cols} columns; continuous shared exclusions requires equal ambient source dimensions)"
            ),
            PidError::InvalidK { k, n_samples } => {
                write!(f, "invalid k={k} for n={n_samples} (require n > k >= 1)")
            }
            PidError::NonFiniteInput { context } => write!(f, "{context}: non-finite input"),
            PidError::SupportContractRequired { context } => write!(
                f,
                "{context}: continuous support contract is unspecified; explicitly assert the population support or use a discrete, quantized, or mixed-law estimator"
            ),
            PidError::UnsupportedSupportContract { context, contract } => write!(
                f,
                "{context}: support contract `{contract}` is unsupported by this continuous estimator"
            ),
            PidError::ObservedContinuousSampleIncompatibility {
                context,
                input_index,
                coordinate,
                unique_values,
                n_samples,
                max_multiplicity,
            } => {
                if let Some(coordinate) = coordinate {
                    write!(
                        f,
                        "{context}: observed exact ties are incompatible with the estimator's ideal i.i.d., unrounded continuous-sample conditions (input {input_index}, coordinate {coordinate}, {unique_values} unique values among {n_samples} samples, maximum multiplicity {max_multiplicity}); possible causes include dependence or resampling, measurement rounding, atoms, or quantization, and the ties do not by themselves identify population support"
                    )
                } else {
                    write!(
                        f,
                        "{context}: observed duplicate rows are incompatible with the estimator's ideal i.i.d., unrounded continuous-manifold sample conditions (input {input_index}, {unique_values} unique rows among {n_samples} samples, maximum multiplicity {max_multiplicity}); possible causes include dependence or resampling, measurement rounding, atoms, or quantization, and the duplicates do not by themselves identify population support"
                    )
                }
            }
            PidError::NumericalInstability { context } => {
                write!(f, "{context}: numerical instability")
            }
            PidError::AmbiguousKthNeighborShell {
                context,
                query_index,
                k,
                radius,
                interior_count,
                boundary_count,
            } => write!(
                f,
                "{context}: ambiguous k-th-neighbor shell at query {query_index} \
                 (k={k}, radius={radius:e}, strict interior count {interior_count}, \
                 boundary count {boundary_count}; expected {expected_interior} and 1)",
                expected_interior = k.saturating_sub(1),
            ),
            PidError::NotImplemented { feature } => write!(f, "not implemented: {feature}"),
        }
    }
}

impl std::error::Error for PidError {}
