use std::error::Error;
use std::fmt::{Display, Formatter};

/// A fail-closed certifier error with a stable machine-readable code.
#[derive(Debug, Clone, Eq, PartialEq)]
pub struct CertError {
    code: &'static str,
    message: String,
}

impl CertError {
    pub(crate) fn new(code: &'static str, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }

    pub(crate) fn internal(message: impl Into<String>) -> Self {
        Self::new("internal_soundness_failure", message)
    }

    /// Creates a rejected-result error for command-line usage.
    #[must_use]
    pub fn usage(message: impl Into<String>) -> Self {
        Self::new("invalid_usage", message)
    }

    /// Creates a rejected-result error for bounded input acquisition.
    #[must_use]
    pub fn input_io(message: impl Into<String>) -> Self {
        Self::new("input_io_failure", message)
    }

    /// Returns the stable error code.
    #[must_use]
    pub const fn code(&self) -> &'static str {
        self.code
    }

    /// Returns the human-readable error detail.
    #[must_use]
    pub fn message(&self) -> &str {
        &self.message
    }

    /// Reports whether certification stopped at the declared precision boundary.
    #[must_use]
    pub fn is_precision_limit(&self) -> bool {
        self.code == "precision_limit"
    }
}

impl Display for CertError {
    fn fmt(&self, formatter: &mut Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {}", self.code, self.message)
    }
}

impl Error for CertError {}
