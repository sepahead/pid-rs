//! Population-support declarations and one-sided observed-sample diagnostics.
//!
//! # Method provenance and availability
//!
//! **PROJECT-DEFINED SCIENTIFIC CONTRACT.** The support enum, fail-closed validation, coordinate
//! cardinality summaries, and neighbor-shell reports are pid-rs safety/provenance design rather
//! than a published estimator. Ordinary contracts and diagnostics are on the default stable
//! surface; manifold variants require `experimental-hyperbolic`. Finite samples can reject
//! observations incompatible with a declared model, but cannot prove population absolute
//! continuity, support dimension, or finite mutual information.
//!
//! Method catalog: diagnostics.support-contracts

use std::fmt;

use serde::Serialize;

use crate::error::{PidError, PidResult};
#[cfg(feature = "experimental-hyperbolic")]
use crate::hyperbolic::HyperbolicMetric;
use crate::matrix::MatRef;
use crate::metric::{KernelMetric, Metric};
use crate::nn::kth_neighbor_shell_counts;
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_filled, try_vec_with_capacity,
    CancellationProgress, CancellationToken, ResourceBudget, ResourceEstimate,
};

/// Caller-declared support assumptions for a continuous estimator.
///
/// This is an assertion about the population law, not a classification inferred from one finite
/// sample. Runtime diagnostics reject observations that are incompatible with the estimator's
/// ideal i.i.d., unrounded continuous-sample conditions, but they neither identify the cause nor
/// prove absolute continuity, a common reference measure, or finite mutual information.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize)]
#[non_exhaustive]
pub enum SupportContract {
    /// No population support assumption has been declared. Continuous estimators fail closed.
    #[default]
    Unspecified,
    /// Caller asserts the regular, locally fixed-dimensional model required by ordinary ambient
    /// KSG. This remains a population assertion; diagnostics cannot prove it from finite data.
    AssumeRegularFullDimensional {
        boundary: BoundaryModel,
        density_regular: bool,
        finite_information: bool,
    },
    /// The law is known to contain atomic and continuous components, or its support type is mixed.
    KnownAtomicOrMixed,
    /// The observations are quantized numeric values.
    KnownQuantized,
    /// The law is singular, stratified, fractal, or lower-dimensional relative to the estimator's
    /// reference measure. The feature-gated smooth-manifold research path uses its own typed
    /// support declaration rather than extending this stable enum.
    KnownSingularOrLowerDimensional,
}

/// Caller-declared behavior of the population support boundary.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum BoundaryModel {
    InteriorOnly,
    ExternallyCorrected,
    Unknown,
}

impl SupportContract {
    /// Construct the ordinary Chebyshev KSG population-law assertion.
    ///
    /// This is a caller declaration, not a property inferred from the observed sample.
    pub const fn assume_regular_full_dimensional() -> Self {
        Self::AssumeRegularFullDimensional {
            boundary: BoundaryModel::Unknown,
            density_regular: true,
            finite_information: true,
        }
    }
}

impl fmt::Display for SupportContract {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Unspecified => f.write_str("unspecified"),
            Self::AssumeRegularFullDimensional {
                boundary,
                density_regular,
                finite_information,
            } => write!(
                f,
                "assume_regular_full_dimensional(boundary={boundary:?}, density_regular={density_regular}, finite_information={finite_information})"
            ),
            Self::KnownAtomicOrMixed => f.write_str("known_atomic_or_mixed"),
            Self::KnownQuantized => f.write_str("known_quantized"),
            Self::KnownSingularOrLowerDimensional => {
                f.write_str("known_singular_or_lower_dimensional")
            }
        }
    }
}

/// Exact-cardinality diagnostics for one observed coordinate.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub struct CoordinateCardinalityDiagnostics {
    pub coordinate: usize,
    pub unique_values: usize,
    /// Number of distinct values observed at least twice.
    pub tied_groups: usize,
    /// Number of observations beyond the first occurrence in each exact-value group.
    pub repeated_observations: usize,
    pub max_multiplicity: usize,
    /// Smallest positive spacing between adjacent distinct observed binary64 values.
    ///
    /// This is sample evidence of resolution/rounding, not an inferred population quantization
    /// step. It is `None` for a constant coordinate or when its only adjacent spacing exceeds the
    /// finite binary64 range; inspect [`Self::unrepresentable_positive_spacings`] to distinguish
    /// those cases.
    pub minimum_positive_spacing: Option<f64>,
    /// Largest representable positive adjacent spacing in the observed coordinate.
    pub maximum_positive_spacing: Option<f64>,
    /// Number of adjacent distinct pairs whose mathematical spacing exceeds `f64::MAX`.
    pub unrepresentable_positive_spacings: usize,
}

/// Empirical quantiles of a non-empty collection of finite distances.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct DistanceQuantiles {
    pub min: f64,
    pub p10: f64,
    pub median: f64,
    pub p90: f64,
    pub p99: f64,
    pub max: f64,
}

/// Diagnostics for independently selected marginal or joint k-th-neighbor shells.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct NeighborShellDiagnostics {
    pub query_count: usize,
    pub zero_radius_queries: usize,
    pub ambiguous_positive_shell_queries: usize,
    pub kth_radius: DistanceQuantiles,
}

/// Sample diagnostics for one continuous input block.
///
/// Exact values use binary64 equality with `-0.0` and `0.0` canonicalized to the same value.
/// These fields expose exact sample multiplicities but cannot identify their cause or certify
/// continuous population support.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct ContinuousInputDiagnostics {
    pub n_samples: usize,
    pub ambient_dimension: usize,
    pub unique_rows: usize,
    pub tied_row_groups: usize,
    pub repeated_rows: usize,
    pub max_row_multiplicity: usize,
    pub coordinates: Vec<CoordinateCardinalityDiagnostics>,
    pub marginal_shells: NeighborShellDiagnostics,
}

/// Compute exact-cardinality and marginal k-th-neighbor-shell diagnostics for one input block.
///
/// This diagnostic is intentionally available even when a continuous estimator's support contract
/// would reject the data, so callers can inspect the evidence and choose a discrete, quantized, or
/// mixed-law method instead.
pub fn continuous_input_diagnostics(
    input: MatRef<'_>,
    k: usize,
    metric: Metric,
) -> PidResult<ContinuousInputDiagnostics> {
    continuous_input_diagnostics_with_budget(input, k, metric, ResourceBudget::default())
}

/// Preflight exact-cardinality storage and pairwise shell work for one input block.
pub fn continuous_input_diagnostics_resource_estimate(
    input: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    continuous_diagnostics_resource_estimate(&[input], true, 1)
}

/// Compute one-block support diagnostics under an explicit resource budget.
pub fn continuous_input_diagnostics_with_budget(
    input: MatRef<'_>,
    k: usize,
    metric: Metric,
    budget: ResourceBudget,
) -> PidResult<ContinuousInputDiagnostics> {
    let cancellation = CancellationToken::new();
    continuous_input_diagnostics_with_budget_and_cancellation(
        input,
        k,
        metric,
        budget,
        &cancellation,
    )
}

/// Compute one-block support diagnostics with resource and cancellation controls.
pub fn continuous_input_diagnostics_with_budget_and_cancellation(
    input: MatRef<'_>,
    k: usize,
    metric: Metric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<ContinuousInputDiagnostics> {
    continuous_input_diagnostics_with_kernel_and_cancellation(
        input,
        k,
        metric.into(),
        budget,
        cancellation,
    )
}

/// Compute one-block support diagnostics with Lorentz-model neighbor shells.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_input_diagnostics(
    input: MatRef<'_>,
    k: usize,
    metric: HyperbolicMetric,
) -> PidResult<ContinuousInputDiagnostics> {
    hyperbolic_continuous_input_diagnostics_with_budget(input, k, metric, ResourceBudget::default())
}

/// Preflight exact-cardinality storage and Lorentz-model shell work for one input block.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_input_diagnostics_resource_estimate(
    input: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    continuous_diagnostics_resource_estimate(
        &[input],
        true,
        crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR,
    )
}

/// Compute one-block Lorentz-model support diagnostics under an explicit resource budget.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_input_diagnostics_with_budget(
    input: MatRef<'_>,
    k: usize,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
) -> PidResult<ContinuousInputDiagnostics> {
    let cancellation = CancellationToken::new();
    hyperbolic_continuous_input_diagnostics_with_budget_and_cancellation(
        input,
        k,
        metric,
        budget,
        &cancellation,
    )
}

/// Compute one-block Lorentz-model support diagnostics with resource and cancellation controls.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_input_diagnostics_with_budget_and_cancellation(
    input: MatRef<'_>,
    k: usize,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<ContinuousInputDiagnostics> {
    validate_diagnostic_shape("continuous_input_diagnostics", &[input], k)?;
    crate::hyperbolic::validate_lorentz_matrix_widths("continuous_input_diagnostics", &[input])?;
    continuous_input_diagnostics_with_kernel_and_cancellation(
        input,
        k,
        metric.kernel(),
        budget,
        cancellation,
    )
}

pub(crate) fn continuous_input_diagnostics_with_kernel_and_cancellation(
    input: MatRef<'_>,
    k: usize,
    metric: KernelMetric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<ContinuousInputDiagnostics> {
    validate_diagnostic_shape("continuous_input_diagnostics", &[input], k)?;
    budget.check(
        "continuous_input_diagnostics",
        continuous_diagnostics_resource_estimate(&[input], true, metric.coordinate_work_factor())?,
    )?;
    cancellation.check("continuous_input_diagnostics", 0, input.nrows())?;
    let cardinalities = exact_cardinalities_with_cancellation(input, budget, cancellation)?;
    let marginal_shells = neighbor_shell_diagnostics(
        &[input],
        k,
        metric,
        budget,
        "continuous_input_diagnostics",
        cancellation,
    )?;
    Ok(ContinuousInputDiagnostics {
        n_samples: input.nrows(),
        ambient_dimension: input.ncols(),
        unique_rows: cardinalities.unique_rows,
        tied_row_groups: cardinalities.tied_row_groups,
        repeated_rows: cardinalities.repeated_rows,
        max_row_multiplicity: cardinalities.max_row_multiplicity,
        coordinates: cardinalities.coordinates,
        marginal_shells,
    })
}

/// Compute k-th-neighbor-shell diagnostics in the max-product joint space of input blocks.
///
/// For one block this is the marginal shell diagnostic returned by
/// [`continuous_input_diagnostics`]. For multiple blocks it matches the joint max metric used by
/// KSG. Every block must have the same row count and at least one column.
pub fn continuous_joint_shell_diagnostics(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: Metric,
) -> PidResult<NeighborShellDiagnostics> {
    continuous_joint_shell_diagnostics_with_budget(inputs, k, metric, ResourceBudget::default())
}

/// Preflight pairwise shell work for a max-product joint space.
pub fn continuous_joint_shell_resource_estimate(
    inputs: &[MatRef<'_>],
) -> PidResult<ResourceEstimate> {
    continuous_diagnostics_resource_estimate(inputs, false, 1)
}

/// Compute joint-shell diagnostics under an explicit resource budget.
pub fn continuous_joint_shell_diagnostics_with_budget(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: Metric,
    budget: ResourceBudget,
) -> PidResult<NeighborShellDiagnostics> {
    let cancellation = CancellationToken::new();
    continuous_joint_shell_diagnostics_with_budget_and_cancellation(
        inputs,
        k,
        metric,
        budget,
        &cancellation,
    )
}

/// Compute joint-shell diagnostics with resource and cancellation controls.
pub fn continuous_joint_shell_diagnostics_with_budget_and_cancellation(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: Metric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<NeighborShellDiagnostics> {
    continuous_joint_shell_diagnostics_with_kernel_and_cancellation(
        inputs,
        k,
        metric.into(),
        budget,
        cancellation,
    )
}

/// Compute max-product joint-shell diagnostics from Lorentz-model input blocks.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_joint_shell_diagnostics(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: HyperbolicMetric,
) -> PidResult<NeighborShellDiagnostics> {
    hyperbolic_continuous_joint_shell_diagnostics_with_budget(
        inputs,
        k,
        metric,
        ResourceBudget::default(),
    )
}

/// Preflight pairwise Lorentz-model shell work for a max-product joint space.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_joint_shell_resource_estimate(
    inputs: &[MatRef<'_>],
) -> PidResult<ResourceEstimate> {
    continuous_diagnostics_resource_estimate(
        inputs,
        false,
        crate::hyperbolic::LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR,
    )
}

/// Compute Lorentz-model joint-shell diagnostics under an explicit resource budget.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_joint_shell_diagnostics_with_budget(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
) -> PidResult<NeighborShellDiagnostics> {
    let cancellation = CancellationToken::new();
    hyperbolic_continuous_joint_shell_diagnostics_with_budget_and_cancellation(
        inputs,
        k,
        metric,
        budget,
        &cancellation,
    )
}

/// Compute Lorentz-model joint-shell diagnostics with resource and cancellation controls.
#[cfg(feature = "experimental-hyperbolic")]
pub fn hyperbolic_continuous_joint_shell_diagnostics_with_budget_and_cancellation(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: HyperbolicMetric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<NeighborShellDiagnostics> {
    validate_diagnostic_shape("continuous_joint_shell_diagnostics", inputs, k)?;
    crate::hyperbolic::validate_lorentz_matrix_widths(
        "continuous_joint_shell_diagnostics",
        inputs,
    )?;
    continuous_joint_shell_diagnostics_with_kernel_and_cancellation(
        inputs,
        k,
        metric.kernel(),
        budget,
        cancellation,
    )
}

pub(crate) fn continuous_joint_shell_diagnostics_with_kernel_and_cancellation(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: KernelMetric,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<NeighborShellDiagnostics> {
    validate_diagnostic_shape("continuous_joint_shell_diagnostics", inputs, k)?;
    budget.check(
        "continuous_joint_shell_diagnostics",
        continuous_diagnostics_resource_estimate(inputs, false, metric.coordinate_work_factor())?,
    )?;
    neighbor_shell_diagnostics(
        inputs,
        k,
        metric,
        budget,
        "continuous_joint_shell_diagnostics",
        cancellation,
    )
}

pub(crate) fn continuous_diagnostics_resource_estimate(
    inputs: &[MatRef<'_>],
    include_cardinality: bool,
    coordinate_work_factor: u128,
) -> PidResult<ResourceEstimate> {
    let Some(first) = inputs.first() else {
        return Err(PidError::InvalidConfig {
            context: "continuous support diagnostics resource estimate",
            message: "need at least one input block",
        });
    };
    let dimensions = inputs.iter().try_fold(0u128, |total, input| {
        total
            .checked_add(input.ncols() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "continuous support diagnostics",
            })
    })?;
    let n = first.nrows() as u128;
    let pairs = n
        .checked_mul(n.saturating_sub(1))
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support diagnostics",
        })?;
    let shell_bytes = n
        .checked_mul(2)
        .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support diagnostics",
        })?;
    let cardinality = if include_cardinality {
        Some(continuous_cardinality_resource_estimate(*first)?)
    } else {
        None
    };
    let cardinality_bytes = cardinality.map_or(0, |estimate| estimate.estimated_bytes);
    let cardinality_operations = cardinality.map_or(0, |estimate| estimate.operations_hint);
    let log_n = if first.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (first.nrows() - 1).leading_zeros()) as u128
    };
    let shell_operations = pairs
        .checked_mul(2)
        .and_then(|value| {
            value.checked_mul(
                dimensions
                    .checked_mul(coordinate_work_factor)?
                    .checked_add(2)?,
            )
        })
        .and_then(|value| value.checked_add(n.checked_mul(log_n)?))
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support diagnostics",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes: shell_bytes.checked_add(cardinality_bytes).ok_or(
            PidError::SizeOverflow {
                operation: "continuous support diagnostics",
            },
        )?,
        pairwise_distances: pairs,
        // Shell diagnostics visit ordered query/candidate pairs, select one order statistic and
        // rescan every shell, then sort the retained radii.
        operations_hint: shell_operations.checked_add(cardinality_operations).ok_or(
            PidError::SizeOverflow {
                operation: "continuous support diagnostics",
            },
        )?,
    })
}

fn continuous_cardinality_resource_estimate(input: MatRef<'_>) -> PidResult<ResourceEstimate> {
    let n = input.nrows() as u128;
    let dimensions = input.ncols() as u128;
    let coordinates = n.checked_mul(dimensions).ok_or(PidError::SizeOverflow {
        operation: "continuous support cardinalities",
    })?;
    // Row keys and column-major values each retain one u64 per coordinate. Include one Vec header
    // per row and a conservative fixed diagnostic allowance per coordinate.
    let estimated_bytes = coordinates
        .checked_mul(2 * std::mem::size_of::<u64>() as u128)
        .and_then(|value| {
            value.checked_add(n.checked_mul(std::mem::size_of::<Vec<u64>>() as u128)?)
        })
        .and_then(|value| {
            value.checked_add(
                dimensions
                    .checked_mul(std::mem::size_of::<CoordinateCardinalityDiagnostics>() as u128)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support cardinalities",
        })?;
    let log_n = if input.nrows() <= 1 {
        1u128
    } else {
        (usize::BITS - (input.nrows() - 1).leading_zeros()) as u128
    };
    // Sorting row keys compares up to d coordinates; sorting every coordinate column adds a
    // second n*d*log(n) term. One further linear pass reports adjacent observed spacings.
    let operations_hint = coordinates
        .checked_mul(log_n)
        .and_then(|value| value.checked_mul(2))
        .and_then(|value| value.checked_add(coordinates))
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support cardinalities",
        })?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: 0,
        operations_hint,
    })
}

pub(crate) fn validate_support_contract(
    context: &'static str,
    contract: SupportContract,
    metric: Metric,
) -> PidResult<()> {
    match (contract, metric) {
        (
            SupportContract::AssumeRegularFullDimensional {
                density_regular: true,
                finite_information: true,
                ..
            },
            Metric::Chebyshev,
        ) => Ok(()),
        (SupportContract::Unspecified, _) => Err(PidError::SupportContractRequired { context }),
        (contract, _) => Err(PidError::UnsupportedSupportContract { context, contract }),
    }
}

/// Reject observations incompatible with the estimator's ideal continuous-sample conditions.
///
/// Under ideal i.i.d., unrounded sampling from a full-dimensional absolutely continuous law, an
/// exact coordinate tie is a probability-zero event. A tie can instead arise from dependence or
/// resampling, measurement rounding, atoms, or quantization; this preflight rejects the sample but
/// does not infer which cause applies or classify the population support. Smooth-manifold
/// coordinates can legitimately be constant, so that research path rejects exact duplicate rows
/// and reports coordinate cardinalities only through the public diagnostic API.
#[cfg(any(feature = "experimental-continuous", test))]
#[cfg(test)]
pub(crate) fn validate_observed_sample_conditions(
    context: &'static str,
    contract: SupportContract,
    inputs: &[MatRef<'_>],
) -> PidResult<()> {
    validate_observed_sample_conditions_with_budget(
        context,
        contract,
        inputs,
        ResourceBudget::default(),
    )
}

#[cfg(any(feature = "experimental-continuous", test))]
pub(crate) fn validate_observed_sample_conditions_with_budget(
    context: &'static str,
    contract: SupportContract,
    inputs: &[MatRef<'_>],
    budget: ResourceBudget,
) -> PidResult<()> {
    let cancellation = CancellationToken::new();
    validate_observed_sample_conditions_with_budget_and_cancellation(
        context,
        contract,
        inputs,
        budget,
        &cancellation,
    )
}

pub(crate) fn validate_observed_sample_conditions_with_budget_and_cancellation(
    context: &'static str,
    contract: SupportContract,
    inputs: &[MatRef<'_>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<()> {
    for (input_index, &input) in inputs.iter().enumerate() {
        cancellation.check(context, input_index, inputs.len())?;
        let cardinalities = exact_cardinalities_with_cancellation(input, budget, cancellation)?;
        match contract {
            SupportContract::AssumeRegularFullDimensional { .. } => {
                reject_coordinate_ties(context, input_index, input, &cardinalities)?;
            }
            _ => {
                return Err(PidError::UnsupportedSupportContract { context, contract });
            }
        }
    }
    cancellation.check(context, inputs.len(), inputs.len())?;
    Ok(())
}

#[cfg(feature = "experimental-hyperbolic")]
pub(crate) fn validate_smooth_manifold_sample_conditions_with_budget_and_cancellation(
    context: &'static str,
    inputs: &[MatRef<'_>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<()> {
    for (input_index, &input) in inputs.iter().enumerate() {
        cancellation.check(context, input_index, inputs.len())?;
        let cardinalities = exact_cardinalities_with_cancellation(input, budget, cancellation)?;
        if cardinalities.unique_rows < input.nrows() {
            return Err(PidError::ObservedContinuousSampleIncompatibility {
                context,
                input_index,
                coordinate: None,
                unique_values: cardinalities.unique_rows,
                n_samples: input.nrows(),
                max_multiplicity: cardinalities.max_row_multiplicity,
            });
        }
    }
    cancellation.check(context, inputs.len(), inputs.len())?;
    Ok(())
}

fn reject_coordinate_ties(
    context: &'static str,
    input_index: usize,
    input: MatRef<'_>,
    cardinalities: &ExactCardinalities,
) -> PidResult<()> {
    if let Some(coordinate) = cardinalities
        .coordinates
        .iter()
        .find(|diagnostic| diagnostic.unique_values < input.nrows())
    {
        return Err(PidError::ObservedContinuousSampleIncompatibility {
            context,
            input_index,
            coordinate: Some(coordinate.coordinate),
            unique_values: coordinate.unique_values,
            n_samples: input.nrows(),
            max_multiplicity: coordinate.max_multiplicity,
        });
    }
    Ok(())
}

struct ExactCardinalities {
    unique_rows: usize,
    tied_row_groups: usize,
    repeated_rows: usize,
    max_row_multiplicity: usize,
    coordinates: Vec<CoordinateCardinalityDiagnostics>,
}

fn exact_cardinalities_with_cancellation(
    input: MatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<ExactCardinalities> {
    budget.check(
        "continuous support diagnostics",
        continuous_cardinality_resource_estimate(input)?,
    )?;
    let n = input.nrows();
    let d = input.ncols();
    let total_coordinates = n.checked_mul(d).ok_or(PidError::SizeOverflow {
        operation: "continuous support diagnostics",
    })?;
    let mut row_keys = try_vec_with_capacity("continuous support row keys", n, budget)?;
    let mut coordinate_values = try_vec_filled(
        "continuous support coordinate values",
        total_coordinates,
        0u64,
        budget,
    )?;
    cancellation.check("continuous support cardinalities", 0, total_coordinates)?;
    let mut completed_coordinates = 0usize;
    for row_index in 0..input.nrows() {
        let row = input.row(row_index);
        let mut key = try_vec_with_capacity("continuous support row key", row.len(), budget)?;
        for (coordinate, &value) in row.iter().enumerate() {
            let bits = canonical_f64_bits(value);
            key.push(bits);
            coordinate_values[coordinate * n + row_index] = bits;
            completed_coordinates += 1;
            if completed_coordinates.is_multiple_of(1024) {
                cancellation.check(
                    "continuous support cardinalities",
                    completed_coordinates,
                    total_coordinates,
                )?;
            }
        }
        row_keys.push(key);
    }

    sort_unstable_by_with_cancellation(
        "continuous support row-key sort",
        &mut row_keys,
        cancellation,
        Ord::cmp,
    )?;
    let (unique_rows, tied_row_groups, repeated_rows, max_row_multiplicity) =
        sorted_multiplicity_summary(&row_keys)?;
    let mut coordinates =
        try_vec_with_capacity("continuous support coordinate diagnostics", d, budget)?;
    for coordinate in 0..d {
        cancellation.check("continuous support coordinate diagnostics", coordinate, d)?;
        let values = &mut coordinate_values[coordinate * n..(coordinate + 1) * n];
        sort_unstable_by_with_cancellation(
            "continuous support coordinate sort",
            values,
            cancellation,
            |left, right| f64::from_bits(*left).total_cmp(&f64::from_bits(*right)),
        )?;
        let (unique_values, tied_groups, repeated_observations, max_multiplicity) =
            sorted_multiplicity_summary(values)?;
        let (minimum_positive_spacing, maximum_positive_spacing, unrepresentable_positive_spacings) =
            observed_coordinate_spacings(values)?;
        coordinates.push(CoordinateCardinalityDiagnostics {
            coordinate,
            unique_values,
            tied_groups,
            repeated_observations,
            max_multiplicity,
            minimum_positive_spacing,
            maximum_positive_spacing,
            unrepresentable_positive_spacings,
        });
    }
    cancellation.check("continuous support coordinate diagnostics", d, d)?;
    Ok(ExactCardinalities {
        unique_rows,
        tied_row_groups,
        repeated_rows,
        max_row_multiplicity,
        coordinates,
    })
}

fn observed_coordinate_spacings(values: &[u64]) -> PidResult<(Option<f64>, Option<f64>, usize)> {
    let mut previous = None;
    let mut minimum = None::<f64>;
    let mut maximum = None::<f64>;
    let mut unrepresentable = 0usize;
    for &bits in values {
        let value = f64::from_bits(bits);
        if previous == Some(value) {
            continue;
        }
        if let Some(previous_value) = previous {
            let spacing = value - previous_value;
            if spacing.is_finite() {
                if spacing <= 0.0 {
                    return Err(PidError::NumericalInstability {
                        context: "continuous support diagnostics: non-positive adjacent spacing",
                    });
                }
                minimum = Some(minimum.map_or(spacing, |current| current.min(spacing)));
                maximum = Some(maximum.map_or(spacing, |current| current.max(spacing)));
            } else {
                unrepresentable = unrepresentable
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow {
                        operation: "continuous support diagnostic spacings",
                    })?;
            }
        }
        previous = Some(value);
    }
    Ok((minimum, maximum, unrepresentable))
}

fn sorted_multiplicity_summary<T: Eq>(values: &[T]) -> PidResult<(usize, usize, usize, usize)> {
    if values.is_empty() {
        return Ok((0, 0, 0, 0));
    }
    let mut unique = 0usize;
    let mut tied_groups = 0usize;
    let mut repeated = 0usize;
    let mut max_multiplicity = 0usize;
    let mut start = 0usize;
    while start < values.len() {
        let mut end = start + 1;
        while end < values.len() && values[end] == values[start] {
            end += 1;
        }
        let count = end - start;
        unique = unique.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: "continuous support diagnostics",
        })?;
        max_multiplicity = max_multiplicity.max(count);
        if count > 1 {
            tied_groups = tied_groups.checked_add(1).ok_or(PidError::SizeOverflow {
                operation: "continuous support diagnostics",
            })?;
            repeated = repeated
                .checked_add(count - 1)
                .ok_or(PidError::SizeOverflow {
                    operation: "continuous support diagnostics",
                })?;
        }
        start = end;
    }
    Ok((unique, tied_groups, repeated, max_multiplicity))
}

fn canonical_f64_bits(value: f64) -> u64 {
    if value == 0.0 {
        0
    } else {
        value.to_bits()
    }
}

fn validate_diagnostic_shape(
    context: &'static str,
    inputs: &[MatRef<'_>],
    k: usize,
) -> PidResult<()> {
    let Some(first) = inputs.first() else {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least one input block",
        });
    };
    if first.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "input blocks must have at least one column",
        });
    }
    for input in &inputs[1..] {
        if input.nrows() != first.nrows() {
            return Err(PidError::RowCountMismatch {
                context,
                left_rows: first.nrows(),
                right_rows: input.nrows(),
            });
        }
        if input.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context,
                message: "input blocks must have at least one column",
            });
        }
    }
    if k == 0 || first.nrows() <= k {
        return Err(PidError::InvalidK {
            k,
            n_samples: first.nrows(),
        });
    }
    Ok(())
}

fn neighbor_shell_diagnostics(
    inputs: &[MatRef<'_>],
    k: usize,
    metric: KernelMetric,
    budget: ResourceBudget,
    operation: &'static str,
    cancellation: &CancellationToken,
) -> PidResult<NeighborShellDiagnostics> {
    let n = inputs[0].nrows();
    let kth = k - 1;
    let mut radii = try_vec_with_capacity("continuous support diagnostic radii", n, budget)?;
    let mut distances = try_vec_with_capacity(
        "continuous support diagnostic distances",
        n.saturating_sub(1),
        budget,
    )?;
    let mut zero_radius_queries = 0usize;
    let mut ambiguous_positive_shell_queries = 0usize;
    let total_distances = n
        .checked_mul(n.saturating_sub(1))
        .ok_or(PidError::SizeOverflow {
            operation: "continuous support shell diagnostics",
        })?;
    let mut completed_distances = 0usize;
    cancellation.check(operation, completed_distances, total_distances)?;
    for i in 0..n {
        distances.clear();
        for j in 0..n {
            if i == j {
                continue;
            }
            let mut distance = 0.0_f64;
            for input in inputs {
                distance = distance.max(metric.checked_distance_with_cancellation(
                    input.row(i),
                    input.row(j),
                    "continuous support diagnostics: distance",
                    CancellationProgress::new(operation, completed_distances, total_distances),
                    cancellation,
                )?);
            }
            distances.push(distance);
            completed_distances += 1;
            if completed_distances.is_multiple_of(1024) {
                cancellation.check(operation, completed_distances, total_distances)?;
            }
        }
        distances.select_nth_unstable_by(kth, f64::total_cmp);
        let radius = distances[kth];
        radii.push(radius);
        if radius == 0.0 {
            zero_radius_queries += 1;
            continue;
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(distances.iter().copied(), radius);
        if interior_count != k - 1 || boundary_count != 1 {
            ambiguous_positive_shell_queries += 1;
        }
    }
    cancellation.check(operation, completed_distances, total_distances)?;
    sort_unstable_by_with_cancellation(operation, &mut radii, cancellation, f64::total_cmp)?;
    Ok(NeighborShellDiagnostics {
        query_count: n,
        zero_radius_queries,
        ambiguous_positive_shell_queries,
        kth_radius: DistanceQuantiles {
            min: radii[0],
            p10: linear_quantile(&radii, 0.1),
            median: linear_quantile(&radii, 0.5),
            p90: linear_quantile(&radii, 0.9),
            p99: linear_quantile(&radii, 0.99),
            max: radii[n - 1],
        },
    })
}

fn linear_quantile(sorted: &[f64], probability: f64) -> f64 {
    debug_assert!(!sorted.is_empty());
    let rank = probability * (sorted.len() - 1) as f64;
    let lower = rank.floor() as usize;
    let upper = rank.ceil() as usize;
    let fraction = rank - lower as f64;
    stable_interpolate(sorted[lower], sorted[upper], fraction)
}

fn stable_interpolate(lower: f64, upper: f64, fraction: f64) -> f64 {
    if lower == upper || fraction == 0.0 {
        return lower;
    }
    if fraction == 1.0 {
        return upper;
    }
    let difference = upper - lower;
    let interpolated = if difference.is_finite() {
        lower + fraction * difference
    } else {
        lower * (1.0 - fraction) + upper * fraction
    };
    interpolated.clamp(lower, upper)
}

#[cfg(test)]
mod tests {
    use super::{
        continuous_input_diagnostics, continuous_input_diagnostics_with_budget_and_cancellation,
        continuous_joint_shell_diagnostics_with_budget_and_cancellation,
        observed_coordinate_spacings, validate_observed_sample_conditions,
        validate_support_contract, BoundaryModel, SupportContract,
    };
    use crate::{CancellationToken, MatRef, Metric, PidError, ResourceBudget};

    #[test]
    fn continuous_diagnostics_cancellation_is_preemptive_and_preserves_parity() {
        let data = [0.0, 0.2, 1.0, 0.7, 2.0, 1.6, 4.0, 3.1];
        let input = MatRef::new(&data, 4, 2).unwrap();
        let baseline = continuous_input_diagnostics(input, 1, Metric::Chebyshev).unwrap();
        let running = CancellationToken::new();
        let cancellable = continuous_input_diagnostics_with_budget_and_cancellation(
            input,
            1,
            Metric::Chebyshev,
            ResourceBudget::default(),
            &running,
        )
        .unwrap();
        assert_eq!(baseline, cancellable);

        let cancelled = CancellationToken::new();
        cancelled.cancel();
        let error = continuous_input_diagnostics_with_budget_and_cancellation(
            input,
            1,
            Metric::Chebyshev,
            ResourceBudget::default(),
            &cancelled,
        )
        .unwrap_err();
        assert!(matches!(
            error,
            PidError::Cancelled {
                operation: "continuous_input_diagnostics",
                ..
            }
        ));

        let cancelled = CancellationToken::new();
        cancelled.cancel();
        let error = continuous_joint_shell_diagnostics_with_budget_and_cancellation(
            &[input],
            1,
            Metric::Chebyshev,
            ResourceBudget::default(),
            &cancelled,
        )
        .unwrap_err();
        assert!(matches!(
            error,
            PidError::Cancelled {
                operation: "continuous_joint_shell_diagnostics",
                ..
            }
        ));
    }

    #[test]
    fn regular_full_dimensional_contract_has_no_incoherent_single_dimension_claim() {
        let contract = SupportContract::assume_regular_full_dimensional();

        validate_support_contract("support contract test", contract, Metric::Chebyshev).unwrap();
        let rendered = contract.to_string();
        assert_eq!(
            rendered,
            "assume_regular_full_dimensional(boundary=Unknown, density_regular=true, finite_information=true)"
        );
        assert!(!rendered.contains("intrinsic_dimension"));
    }

    #[test]
    fn signed_zero_is_one_exact_value() {
        let data = [-0.0, 0.0, 1.0, 2.0];
        let input = MatRef::new(&data, 4, 1).unwrap();
        let diagnostics = continuous_input_diagnostics(input, 1, Metric::Chebyshev).unwrap();

        assert_eq!(diagnostics.coordinates[0].unique_values, 3);
        assert_eq!(diagnostics.coordinates[0].tied_groups, 1);
        assert_eq!(diagnostics.coordinates[0].max_multiplicity, 2);
        assert_eq!(
            diagnostics.coordinates[0].minimum_positive_spacing,
            Some(1.0)
        );
        assert_eq!(
            diagnostics.coordinates[0].maximum_positive_spacing,
            Some(1.0)
        );
        assert_eq!(
            diagnostics.coordinates[0].unrepresentable_positive_spacings,
            0
        );
    }

    #[test]
    fn coordinate_spacing_reports_an_unrepresentable_extreme_gap_without_nan() {
        // Construct the sorted canonical bit sequence explicitly; numerical order is what the
        // production path establishes before calling the helper.
        let values = [(-f64::MAX).to_bits(), f64::MAX.to_bits()];
        let (minimum, maximum, unrepresentable) = observed_coordinate_spacings(&values).unwrap();

        assert_eq!(minimum, None);
        assert_eq!(maximum, None);
        assert_eq!(unrepresentable, 1);
    }

    #[test]
    fn a_discrete_coordinate_is_rejected_even_when_rows_are_unique() {
        let data = [
            0.0, 0.11, 0.0, 0.27, 1.0, 0.38, 1.0, 0.59, 0.0, 0.73, 1.0, 0.91,
        ];
        let input = MatRef::new(&data, 6, 2).unwrap();
        let diagnostics = continuous_input_diagnostics(input, 2, Metric::Chebyshev).unwrap();
        assert_eq!(diagnostics.unique_rows, 6);
        assert_eq!(diagnostics.coordinates[0].unique_values, 2);

        let error = validate_observed_sample_conditions(
            "mixed-support regression",
            SupportContract::AssumeRegularFullDimensional {
                boundary: BoundaryModel::Unknown,
                density_regular: true,
                finite_information: true,
            },
            &[input],
        )
        .unwrap_err();
        assert!(matches!(
            error,
            PidError::ObservedContinuousSampleIncompatibility {
                coordinate: Some(0),
                unique_values: 2,
                ..
            }
        ));
    }
}
