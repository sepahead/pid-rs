use std::collections::BTreeMap;
use std::fmt;

use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::kth_neighbor_shell_counts;

/// Caller-declared support assumptions for a continuous estimator.
///
/// This is an assertion about the population law, not a classification inferred from one finite
/// sample. Runtime diagnostics reject observations that are incompatible with the estimator's
/// ideal i.i.d., unrounded continuous-sample conditions, but they neither identify the cause nor
/// prove absolute continuity, a common reference measure, or finite mutual information.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
#[non_exhaustive]
pub enum SupportContract {
    /// No population support assumption has been declared. Continuous estimators fail closed.
    #[default]
    Unspecified,
    /// The caller asserts that every marginal and joint law used by the estimator is
    /// full-dimensional and absolutely continuous with respect to the relevant ambient Lebesgue
    /// measure, with finite mutual information.
    AssumeAbsolutelyContinuous,
    /// The caller asserts that X, Y, and every joint law used by pairwise MI have continuous
    /// densities relative to their relevant manifold/product-manifold volume measures, with finite
    /// mutual information.
    ///
    /// This is a population-model assertion accepted only for explicitly experimental standalone
    /// KSG with a manifold metric. It does not claim that this crate has proved a manifold-KSG
    /// consistency theorem.
    AssumeSmoothManifold,
    /// The law is known to contain atomic and continuous components, or its support type is mixed.
    KnownAtomicOrMixed,
    /// The observations are quantized numeric values.
    KnownQuantized,
    /// The law is singular, stratified, fractal, or lower-dimensional relative to the estimator's
    /// reference measure (apart from the explicit smooth-manifold research opt-in above).
    KnownSingularOrLowerDimensional,
}

impl fmt::Display for SupportContract {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let name = match self {
            Self::Unspecified => "unspecified",
            Self::AssumeAbsolutelyContinuous => "assume_absolutely_continuous",
            Self::AssumeSmoothManifold => "assume_smooth_manifold",
            Self::KnownAtomicOrMixed => "known_atomic_or_mixed",
            Self::KnownQuantized => "known_quantized",
            Self::KnownSingularOrLowerDimensional => "known_singular_or_lower_dimensional",
        };
        f.write_str(name)
    }
}

/// Exact-cardinality diagnostics for one observed coordinate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoordinateCardinalityDiagnostics {
    pub coordinate: usize,
    pub unique_values: usize,
    /// Number of distinct values observed at least twice.
    pub tied_groups: usize,
    /// Number of observations beyond the first occurrence in each exact-value group.
    pub repeated_observations: usize,
    pub max_multiplicity: usize,
}

/// Empirical quantiles of a non-empty collection of finite distances.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct DistanceQuantiles {
    pub min: f64,
    pub p10: f64,
    pub median: f64,
    pub p90: f64,
    pub p99: f64,
    pub max: f64,
}

/// Diagnostics for independently selected marginal or joint k-th-neighbor shells.
#[derive(Debug, Clone, Copy, PartialEq)]
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
#[derive(Debug, Clone, PartialEq)]
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
    validate_diagnostic_shape("continuous_input_diagnostics", &[input], k)?;
    let cardinalities = exact_cardinalities(input)?;
    let marginal_shells = neighbor_shell_diagnostics(&[input], k, metric)?;
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
    validate_diagnostic_shape("continuous_joint_shell_diagnostics", inputs, k)?;
    neighbor_shell_diagnostics(inputs, k, metric)
}

pub(crate) fn validate_support_contract(
    context: &'static str,
    contract: SupportContract,
    metric: Metric,
) -> PidResult<()> {
    match (contract, metric) {
        (SupportContract::AssumeAbsolutelyContinuous, Metric::Chebyshev)
        | (SupportContract::AssumeSmoothManifold, Metric::HyperbolicLorentz) => Ok(()),
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
pub(crate) fn validate_observed_sample_conditions(
    context: &'static str,
    contract: SupportContract,
    inputs: &[MatRef<'_>],
) -> PidResult<()> {
    for (input_index, &input) in inputs.iter().enumerate() {
        let cardinalities = exact_cardinalities(input)?;
        match contract {
            SupportContract::AssumeAbsolutelyContinuous => {
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
            }
            SupportContract::AssumeSmoothManifold => {
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
            _ => {
                return Err(PidError::UnsupportedSupportContract { context, contract });
            }
        }
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

fn exact_cardinalities(input: MatRef<'_>) -> PidResult<ExactCardinalities> {
    let mut row_counts = BTreeMap::<Vec<u64>, usize>::new();
    let mut coordinate_counts = vec![BTreeMap::<u64, usize>::new(); input.ncols()];
    for row_index in 0..input.nrows() {
        let row = input.row(row_index);
        let mut key = Vec::new();
        key.try_reserve_exact(row.len())
            .map_err(|_| PidError::InvalidConfig {
                context: "continuous support diagnostics",
                message: "row-key allocation failed",
            })?;
        for (coordinate, &value) in row.iter().enumerate() {
            let bits = canonical_f64_bits(value);
            key.push(bits);
            let count = coordinate_counts[coordinate].entry(bits).or_default();
            *count = count.checked_add(1).ok_or(PidError::InvalidConfig {
                context: "continuous support diagnostics",
                message: "coordinate multiplicity overflow",
            })?;
        }
        let count = row_counts.entry(key).or_default();
        *count = count.checked_add(1).ok_or(PidError::InvalidConfig {
            context: "continuous support diagnostics",
            message: "row multiplicity overflow",
        })?;
    }

    let (tied_row_groups, repeated_rows, max_row_multiplicity) = multiplicity_summary(&row_counts)?;
    let mut coordinates = Vec::new();
    coordinates
        .try_reserve_exact(input.ncols())
        .map_err(|_| PidError::InvalidConfig {
            context: "continuous support diagnostics",
            message: "coordinate diagnostic allocation failed",
        })?;
    for (coordinate, counts) in coordinate_counts.iter().enumerate() {
        let (tied_groups, repeated_observations, max_multiplicity) = multiplicity_summary(counts)?;
        coordinates.push(CoordinateCardinalityDiagnostics {
            coordinate,
            unique_values: counts.len(),
            tied_groups,
            repeated_observations,
            max_multiplicity,
        });
    }
    Ok(ExactCardinalities {
        unique_rows: row_counts.len(),
        tied_row_groups,
        repeated_rows,
        max_row_multiplicity,
        coordinates,
    })
}

fn multiplicity_summary<K: Ord>(counts: &BTreeMap<K, usize>) -> PidResult<(usize, usize, usize)> {
    let mut tied_groups = 0usize;
    let mut repeated = 0usize;
    let mut max_multiplicity = 0usize;
    for &count in counts.values() {
        max_multiplicity = max_multiplicity.max(count);
        if count > 1 {
            tied_groups = tied_groups.checked_add(1).ok_or(PidError::InvalidConfig {
                context: "continuous support diagnostics",
                message: "tie-group count overflow",
            })?;
            repeated = repeated
                .checked_add(count - 1)
                .ok_or(PidError::InvalidConfig {
                    context: "continuous support diagnostics",
                    message: "repeated-observation count overflow",
                })?;
        }
    }
    Ok((tied_groups, repeated, max_multiplicity))
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
    metric: Metric,
) -> PidResult<NeighborShellDiagnostics> {
    let n = inputs[0].nrows();
    let kth = k - 1;
    let mut radii = Vec::new();
    radii
        .try_reserve_exact(n)
        .map_err(|_| PidError::InvalidConfig {
            context: "continuous support diagnostics",
            message: "radius diagnostic allocation failed",
        })?;
    let mut zero_radius_queries = 0usize;
    let mut ambiguous_positive_shell_queries = 0usize;
    for i in 0..n {
        let mut distances = Vec::new();
        distances
            .try_reserve_exact(n.saturating_sub(1))
            .map_err(|_| PidError::InvalidConfig {
                context: "continuous support diagnostics",
                message: "distance diagnostic allocation failed",
            })?;
        for j in 0..n {
            if i == j {
                continue;
            }
            let mut distance = 0.0_f64;
            for input in inputs {
                distance = distance.max(metric.checked_distance(
                    input.row(i),
                    input.row(j),
                    "continuous support diagnostics: distance",
                )?);
            }
            distances.push(distance);
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
    radii.sort_by(f64::total_cmp);
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
    sorted[lower] + fraction * (sorted[upper] - sorted[lower])
}

#[cfg(test)]
mod tests {
    use super::{
        continuous_input_diagnostics, validate_observed_sample_conditions, SupportContract,
    };
    use crate::{MatRef, Metric, PidError};

    #[test]
    fn signed_zero_is_one_exact_value() {
        let data = [-0.0, 0.0, 1.0, 2.0];
        let input = MatRef::new(&data, 4, 1).unwrap();
        let diagnostics = continuous_input_diagnostics(input, 1, Metric::Chebyshev).unwrap();

        assert_eq!(diagnostics.coordinates[0].unique_values, 3);
        assert_eq!(diagnostics.coordinates[0].tied_groups, 1);
        assert_eq!(diagnostics.coordinates[0].max_multiplicity, 2);
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
            SupportContract::AssumeAbsolutelyContinuous,
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
