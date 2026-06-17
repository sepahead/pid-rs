use std::fmt;

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
    InvalidK {
        k: usize,
        n_samples: usize,
    },
    NonFiniteInput {
        context: &'static str,
    },
    NumericalInstability {
        context: &'static str,
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
            PidError::InvalidK { k, n_samples } => {
                write!(f, "invalid k={k} for n={n_samples} (require n > k >= 1)")
            }
            PidError::NonFiniteInput { context } => write!(f, "{context}: non-finite input"),
            PidError::NumericalInstability { context } => {
                write!(f, "{context}: numerical instability")
            }
            PidError::NotImplemented { feature } => write!(f, "not implemented: {feature}"),
        }
    }
}

impl std::error::Error for PidError {}
