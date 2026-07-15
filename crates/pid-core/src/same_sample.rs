use serde::Serialize;

/// Provenance for an exploratory equal-width transform fitted on the evaluated rows.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct SameSampleEqualWidthProvenance {
    /// Number of bins fitted independently for each input column.
    pub num_bins: usize,
}

/// Result of an exploratory same-sample transform followed by a categorical estimator.
///
/// The inner result records `Categorical` because it describes the labels supplied to the
/// categorical estimator. [`Self::quantization`] records how the exploratory adapter produced
/// those labels without extending a stable encoding enum with feature-dependent variants.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct ExploratorySameSampleQuantizedResult<T> {
    /// Result returned by the categorical estimator after quantization.
    pub categorical_result: T,
    /// Same-row quantization provenance owned by the exploratory adapter.
    pub quantization: SameSampleEqualWidthProvenance,
}

impl<T> ExploratorySameSampleQuantizedResult<T> {
    pub(crate) const fn new(categorical_result: T, num_bins: usize) -> Self {
        Self {
            categorical_result,
            quantization: SameSampleEqualWidthProvenance { num_bins },
        }
    }

    /// Consume the exploratory wrapper and return its categorical result.
    ///
    /// This deliberately discards [`Self::quantization`]; callers that retain provenance should
    /// destructure or serialize the wrapper instead.
    pub fn into_categorical_result(self) -> T {
        self.categorical_result
    }
}
