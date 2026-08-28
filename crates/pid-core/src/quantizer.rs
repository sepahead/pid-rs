//! Fitted equal-width quantization and quantization provenance.
//!
//! # Method provenance and availability
//!
//! **PAPER-DERIVED TRANSFORM / PROJECT-DEFINED FIT CONTRACT.** Equal-width scalar quantization is a standard
//! quantization construction. The exact training-minimum/maximum fit, held-out out-of-range
//! policy, occupancy diagnostics, hashes, and resource controls are pid-rs design choices. The
//! reusable fitted transform is available on the default stable surface.
//!
//! Method catalog: quantization.equal-width
//!
//! **PROJECT-DEFINED COMPOSITION.** Fitted-quantized shared-exclusions code applies the fitted
//! transform and then the paper-defined categorical `i^sx_∩` implementation. It estimates the PID
//! of the resulting categorical variables, not continuous PID, and no separate paper is claimed
//! for this composition. The fitted path is available on the default stable surface.
//!
//! Method catalog: shared-exclusions.fitted-quantized
//!
//! # New project validation
//!
//! The frozen-transform corollary in `FINITE_ALPHABET_PLUGIN_CONVERGENCE.md` applies only under the
//! following conditions. A training artifact is independent of the raw evaluation sequence. The
//! frozen map is measurable with respect to the training sigma-field and raw input. It returns a
//! valid finite output with conditional probability one. Evaluation rows are conditionally i.i.d.
//! given the training sigma-field. Under `OutOfRangePolicy::Error`, the
//! evaluation law must have conditional mass one inside all fitted ranges. On any fixed training
//! outcome, a positive conditional per-row failure probability makes an infinite valid prefix fail
//! with conditional probability one. `ClampToBoundary` supplies a total range map for otherwise
//! valid finite inputs, but it defines a tail-clamped categorical estimand. Same-row fitting,
//! changing transforms, dependence, and drift are outside this corollary. The method catalog
//! records the project analysis under
//! `validation.finite-alphabet-plugin-convergence`.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::error::{PidError, PidResult};
use crate::matrix::{DiscreteMatOwned, MatRef};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_with_capacity, CancellationToken, ResourceBudget,
    ResourceEstimate,
};

const CANCELLATION_CHECK_INTERVAL: usize = 1_024;
const TRAINING_INPUT_HASH_DOMAIN: &[u8] = b"pid-rs/quantizer/training-input/f64-bits-le/v1\0";
const TRANSFORM_INPUT_HASH_DOMAIN: &[u8] = b"pid-rs/quantizer/transform-input/f64-bits-le/v1\0";
const CATEGORICAL_OUTPUT_HASH_DOMAIN: &[u8] = b"pid-rs/quantizer/categorical-output/u128-le/v1\0";

/// Policy for held-out values outside the range observed during fitting.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[non_exhaustive]
pub enum OutOfRangePolicy {
    /// Fail rather than silently change the fitted transform.
    Error,
    /// Map values below/above the training range to the first/last fitted bin.
    ClampToBoundary,
}

/// Configuration for [`EqualWidthQuantizer::fit`].
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct QuantizerConfig {
    out_of_range_policy: OutOfRangePolicy,
    record_training_data_hash: bool,
    low_count_threshold: usize,
    scaling_description: String,
    resource_budget: ResourceBudget,
}

impl Default for QuantizerConfig {
    fn default() -> Self {
        Self {
            out_of_range_policy: OutOfRangePolicy::Error,
            record_training_data_hash: true,
            low_count_threshold: 5,
            scaling_description: "none; raw input units".to_owned(),
            resource_budget: ResourceBudget::default(),
        }
    }
}

impl QuantizerConfig {
    /// Construct a checked configuration. The scaling description is provenance, not an
    /// operation performed by the quantizer.
    pub fn new(
        out_of_range_policy: OutOfRangePolicy,
        record_training_data_hash: bool,
        low_count_threshold: usize,
        scaling_description: impl AsRef<str>,
        resource_budget: ResourceBudget,
    ) -> PidResult<Self> {
        const MAX_SCALING_DESCRIPTION_BYTES: usize = 16 * 1024;
        let scaling_description = scaling_description.as_ref();
        if scaling_description.trim().is_empty() {
            return Err(PidError::InvalidConfig {
                context: "QuantizerConfig::new",
                message: "scaling_description must be nonempty",
            });
        }
        if scaling_description.len() > MAX_SCALING_DESCRIPTION_BYTES {
            return Err(PidError::ResourceLimitExceeded {
                operation: "QuantizerConfig::new",
                resource: "scaling_description_bytes",
                requested: scaling_description.len() as u128,
                limit: MAX_SCALING_DESCRIPTION_BYTES as u128,
            });
        }
        if low_count_threshold == 0 {
            return Err(PidError::InvalidConfig {
                context: "QuantizerConfig::new",
                message: "low_count_threshold must be positive",
            });
        }
        resource_budget.validate("QuantizerConfig::new")?;
        let scaling_description = try_string_copy(
            "QuantizerConfig::new scaling description",
            scaling_description,
            resource_budget,
        )?;
        Ok(Self {
            out_of_range_policy,
            record_training_data_hash,
            low_count_threshold,
            scaling_description,
            resource_budget,
        })
    }

    pub fn out_of_range_policy(&self) -> OutOfRangePolicy {
        self.out_of_range_policy
    }

    pub fn low_count_threshold(&self) -> usize {
        self.low_count_threshold
    }

    pub fn scaling_description(&self) -> &str {
        &self.scaling_description
    }

    pub fn resource_budget(&self) -> ResourceBudget {
        self.resource_budget
    }

    /// Fallibly copy this heap-owning configuration under an explicit budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        Ok(Self {
            out_of_range_policy: self.out_of_range_policy,
            record_training_data_hash: self.record_training_data_hash,
            low_count_threshold: self.low_count_threshold,
            scaling_description: try_string_copy(
                "QuantizerConfig::try_clone_with_budget",
                &self.scaling_description,
                budget,
            )?,
            resource_budget: self.resource_budget,
        })
    }
}

/// Occupancy and provenance for one application of a fitted quantizer.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct QuantizationReport {
    pub bin_edges: Vec<Vec<f64>>,
    /// SHA-256 of the fitted training matrix's shape and exact binary64 bits in the versioned
    /// training-input domain; absent only when training-input hashing was disabled explicitly.
    pub training_input_hash: Option<[u8; 32]>,
    /// SHA-256 of this transform call's input shape and exact binary64 bits in the versioned
    /// transform-input domain.
    pub transform_input_hash: [u8; 32],
    /// SHA-256 of this transform call's categorical labels and shape in the versioned
    /// categorical-output domain.
    pub categorical_output_hash: [u8; 32],
    pub out_of_range_policy: OutOfRangePolicy,
    pub scaling_description: String,
    pub n_samples: usize,
    pub dimensions: usize,
    /// Requested nominal label count for every dimension. Binary64 edge collapse can make fewer
    /// labels structurally reachable; see [`Self::reachable_binary64_label_counts`].
    pub bins_per_dimension: usize,
    /// Per-dimension number of distinct stored binary64 edge payloads. `-0.0` and `+0.0` count as
    /// distinct payloads even though the transform compares them as the same numeric value.
    pub distinct_binary64_edge_value_counts: Vec<usize>,
    /// Per-dimension number of adjacent edge intervals with positive numeric width (`e_j <
    /// e_{j+1}`). This is structural transform metadata, not a support or occupancy estimate.
    pub positive_width_interval_counts: Vec<usize>,
    /// Per-dimension number of labels having at least one accepted finite binary64 preimage under
    /// the exact endpoint and partition semantics of this fitted transform.
    pub reachable_binary64_label_counts: Vec<usize>,
    /// Per-dimension number of labels present in this transform call's categorical output.
    pub observed_label_counts: Vec<usize>,
    /// `None` means `bins_per_dimension.pow(dimensions)` exceeds `u128`.
    pub nominal_joint_cardinality: Option<u128>,
    /// Product of [`Self::reachable_binary64_label_counts`], or `None` only when that product
    /// exceeds `u128`. This is map reachability, not population support or positive probability.
    pub reachable_joint_cardinality: Option<u128>,
    pub observed_joint_cardinality: usize,
    /// Nominal minus observed joint cells. This backwards-compatible field combines structurally
    /// unreachable nominal cells and reachable-but-unobserved cells; `None` means the nominal
    /// cardinality exceeds `u128`.
    pub empty_joint_cells: Option<u128>,
    /// Nominal minus binary64-reachable joint cells. `None` means nominal cardinality exceeds
    /// `u128`; it never means an inconsistent subtraction was ignored.
    pub structurally_unreachable_joint_cells: Option<u128>,
    /// Binary64-reachable minus observed joint cells. `None` means reachable joint cardinality
    /// exceeds `u128`; it never means an inconsistent subtraction was ignored.
    pub unobserved_reachable_joint_cells: Option<u128>,
    pub low_count_joint_cells: usize,
    pub minimum_observed_cell_count: usize,
    pub maximum_observed_cell_count: usize,
    pub estimand_statement: &'static str,
}

impl QuantizationReport {
    pub(crate) fn copy_operations_hint(&self, operation: &'static str) -> PidResult<u128> {
        let edge_count = self.bin_edges.iter().try_fold(0u128, |total, column| {
            total
                .checked_add(column.len() as u128)
                .ok_or(PidError::SizeOverflow { operation })
        })?;
        let diagnostic_count = [
            self.distinct_binary64_edge_value_counts.len(),
            self.positive_width_interval_counts.len(),
            self.reachable_binary64_label_counts.len(),
            self.observed_label_counts.len(),
        ]
        .into_iter()
        .try_fold(0u128, |sum, length| {
            sum.checked_add(length as u128)
                .ok_or(PidError::SizeOverflow { operation })
        })?;
        edge_count
            .checked_add(diagnostic_count)
            .and_then(|value| value.checked_add(self.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow { operation })
    }

    /// Fallibly deep-copy report provenance and fitted edges under an aggregate budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        let edge_count = self.bin_edges.iter().try_fold(0usize, |total, column| {
            total
                .checked_add(column.len())
                .ok_or(PidError::SizeOverflow {
                    operation: "QuantizationReport::try_clone_with_budget",
                })
        })?;
        let diagnostic_count = [
            self.distinct_binary64_edge_value_counts.len(),
            self.positive_width_interval_counts.len(),
            self.reachable_binary64_label_counts.len(),
            self.observed_label_counts.len(),
        ]
        .into_iter()
        .try_fold(0usize, |sum, length| {
            sum.checked_add(length).ok_or(PidError::SizeOverflow {
                operation: "QuantizationReport::try_clone_with_budget",
            })
        })?;
        let estimated_bytes = (edge_count as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (self.bin_edges.len() as u128)
                        .checked_mul(std::mem::size_of::<Vec<f64>>() as u128)?,
                )
            })
            .and_then(|value| {
                value.checked_add(
                    (diagnostic_count as u128).checked_mul(std::mem::size_of::<usize>() as u128)?,
                )
            })
            .and_then(|value| value.checked_add(self.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "QuantizationReport::try_clone_with_budget",
            })?;
        budget.check(
            "QuantizationReport::try_clone_with_budget",
            ResourceEstimate {
                estimated_bytes,
                pairwise_distances: 0,
                operations_hint: self
                    .copy_operations_hint("QuantizationReport::try_clone_with_budget")?,
            },
        )?;
        Ok(Self {
            bin_edges: try_clone_edges(
                "QuantizationReport::try_clone_with_budget",
                &self.bin_edges,
                budget,
            )?,
            training_input_hash: self.training_input_hash,
            transform_input_hash: self.transform_input_hash,
            categorical_output_hash: self.categorical_output_hash,
            out_of_range_policy: self.out_of_range_policy,
            scaling_description: try_string_copy(
                "QuantizationReport::try_clone_with_budget",
                &self.scaling_description,
                budget,
            )?,
            n_samples: self.n_samples,
            dimensions: self.dimensions,
            bins_per_dimension: self.bins_per_dimension,
            distinct_binary64_edge_value_counts: try_clone_usize_counts(
                "QuantizationReport::try_clone_with_budget",
                &self.distinct_binary64_edge_value_counts,
                budget,
            )?,
            positive_width_interval_counts: try_clone_usize_counts(
                "QuantizationReport::try_clone_with_budget",
                &self.positive_width_interval_counts,
                budget,
            )?,
            reachable_binary64_label_counts: try_clone_usize_counts(
                "QuantizationReport::try_clone_with_budget",
                &self.reachable_binary64_label_counts,
                budget,
            )?,
            observed_label_counts: try_clone_usize_counts(
                "QuantizationReport::try_clone_with_budget",
                &self.observed_label_counts,
                budget,
            )?,
            nominal_joint_cardinality: self.nominal_joint_cardinality,
            reachable_joint_cardinality: self.reachable_joint_cardinality,
            observed_joint_cardinality: self.observed_joint_cardinality,
            empty_joint_cells: self.empty_joint_cells,
            structurally_unreachable_joint_cells: self.structurally_unreachable_joint_cells,
            unobserved_reachable_joint_cells: self.unobserved_reachable_joint_cells,
            low_count_joint_cells: self.low_count_joint_cells,
            minimum_observed_cell_count: self.minimum_observed_cell_count,
            maximum_observed_cell_count: self.maximum_observed_cell_count,
            estimand_statement: self.estimand_statement,
        })
    }
}

/// A train-fitted, reusable equal-width categorical transform.
///
/// The edges, training identity, out-of-range policy, and prior scaling are part of the resulting
/// quantized estimand. Fitting on evaluation rows is therefore not equivalent to applying this
/// object to held-out rows.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct EqualWidthQuantizer {
    edges: Vec<Vec<f64>>,
    bins: usize,
    training_input_hash: Option<[u8; 32]>,
    config: QuantizerConfig,
}

impl EqualWidthQuantizer {
    /// Fallibly copy a fitted quantizer under an aggregate allocation budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        let edge_count = self.edges.iter().try_fold(0usize, |total, column| {
            total
                .checked_add(column.len())
                .ok_or(PidError::SizeOverflow {
                    operation: "EqualWidthQuantizer::try_clone_with_budget",
                })
        })?;
        let edge_bytes = (edge_count as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (self.edges.len() as u128)
                        .checked_mul(std::mem::size_of::<Vec<f64>>() as u128)?,
                )
            })
            .and_then(|value| value.checked_add(self.config.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "EqualWidthQuantizer::try_clone_with_budget",
            })?;
        budget.check(
            "EqualWidthQuantizer::try_clone_with_budget",
            ResourceEstimate {
                estimated_bytes: edge_bytes,
                pairwise_distances: 0,
                operations_hint: (edge_count as u128)
                    .checked_add(self.config.scaling_description.len() as u128)
                    .ok_or(PidError::SizeOverflow {
                        operation: "EqualWidthQuantizer::try_clone_with_budget",
                    })?,
            },
        )?;
        Ok(Self {
            edges: try_clone_edges(
                "EqualWidthQuantizer::try_clone_with_budget",
                &self.edges,
                budget,
            )?,
            bins: self.bins,
            training_input_hash: self.training_input_hash,
            config: self.config.try_clone_with_budget(budget)?,
        })
    }

    /// Preflight fitted-edge storage and fitting work.
    pub fn fit_resource_estimate(train: MatRef<'_>, bins: usize) -> PidResult<ResourceEstimate> {
        const OPERATION: &str = "EqualWidthQuantizer::fit";
        let edges_per_column = bins.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
        let edge_count =
            train
                .ncols()
                .checked_mul(edges_per_column)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let estimated_bytes = (edge_count as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (train.ncols() as u128).checked_mul(std::mem::size_of::<Vec<f64>>() as u128)?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let operations_hint = (train.nrows() as u128)
            .checked_mul(train.ncols() as u128)
            .and_then(|value| value.checked_mul(2))
            .and_then(|value| value.checked_add((edge_count as u128).checked_mul(2)?))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        Ok(ResourceEstimate {
            estimated_bytes,
            pairwise_distances: 0,
            operations_hint,
        })
    }

    /// Fit bin edges on training rows only.
    pub fn fit(train: MatRef<'_>, bins: usize, config: QuantizerConfig) -> PidResult<Self> {
        let cancellation = CancellationToken::new();
        Self::fit_with_cancellation(train, bins, config, &cancellation)
    }

    /// [`Self::fit`] with cooperative cancellation during input scans, edge construction, and
    /// provenance hashing.
    pub fn fit_with_cancellation(
        train: MatRef<'_>,
        bins: usize,
        config: QuantizerConfig,
        cancellation: &CancellationToken,
    ) -> PidResult<Self> {
        const OPERATION: &str = "EqualWidthQuantizer::fit";
        if train.nrows() == 0 || train.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "training data must have at least one row and one column",
            });
        }
        if bins < 2 {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "bins must be at least 2",
            });
        }
        config.resource_budget.validate(OPERATION)?;
        let edges_per_column = bins.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
        config
            .resource_budget
            .check(OPERATION, Self::fit_resource_estimate(train, bins)?)?;

        let coordinate_count =
            train
                .nrows()
                .checked_mul(train.ncols())
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let edge_count =
            train
                .ncols()
                .checked_mul(edges_per_column)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let hash_count = if config.record_training_data_hash {
            coordinate_count
        } else {
            0
        };
        let total_work = coordinate_count
            .checked_add(edge_count)
            .and_then(|value| value.checked_add(edge_count))
            .and_then(|value| value.checked_add(hash_count))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let mut completed_work = 0usize;
        check_cancellation(cancellation, OPERATION, completed_work, total_work)?;

        let mut edges = try_vec_with_capacity(OPERATION, train.ncols(), config.resource_budget)?;
        for column in 0..train.ncols() {
            let mut minimum = f64::INFINITY;
            let mut maximum = f64::NEG_INFINITY;
            for row in 0..train.nrows() {
                check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
                let value = train.row(row)[column];
                // `f64::min` and `f64::max` can lower to target-dependent instructions whose
                // equal-operand choice does not retain both signed-zero payloads. `MatRef`
                // guarantees finite inputs, so the binary64 total order differs from numeric
                // order here only by placing -0.0 below +0.0. This makes the documented endpoint
                // payload contract independent of row order and optimization level on supported
                // Rust targets governed by these binary64 semantics.
                if value.total_cmp(&minimum).is_lt() {
                    minimum = value;
                }
                if value.total_cmp(&maximum).is_gt() {
                    maximum = value;
                }
                completed_work += 1;
            }
            let mut column_edges =
                try_vec_with_capacity(OPERATION, edges_per_column, config.resource_budget)?;
            if minimum == maximum {
                for _ in 0..edges_per_column {
                    check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
                    column_edges.push(minimum);
                    completed_work += 1;
                }
            } else {
                for edge in 0..=bins {
                    check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
                    let fraction = edge as f64 / bins as f64;
                    column_edges.push(stable_lerp(minimum, maximum, fraction));
                    completed_work += 1;
                }
            }
            // Endpoint assignment is exact, including the distinct signs of a signed-zero range.
            column_edges[0] = minimum;
            column_edges[bins] = maximum;
            validate_fitted_edges(
                &column_edges,
                bins,
                minimum,
                maximum,
                cancellation,
                &mut completed_work,
                total_work,
            )?;
            edges.push(column_edges);
        }

        let training_input_hash = if config.record_training_data_hash {
            Some(hash_matrix_with_cancellation(
                train,
                TRAINING_INPUT_HASH_DOMAIN,
                cancellation,
                OPERATION,
                &mut completed_work,
                total_work,
            )?)
        } else {
            None
        };
        check_cancellation(cancellation, OPERATION, total_work, total_work)?;
        Ok(Self {
            edges,
            bins,
            training_input_hash,
            config,
        })
    }

    /// Apply the fixed training edges to data and return only categorical labels.
    pub fn transform(&self, data: MatRef<'_>) -> PidResult<DiscreteMatOwned> {
        let cancellation = CancellationToken::new();
        self.transform_with_cancellation(data, &cancellation)
    }

    /// [`Self::transform`] with cooperative cancellation.
    pub fn transform_with_cancellation(
        &self,
        data: MatRef<'_>,
        cancellation: &CancellationToken,
    ) -> PidResult<DiscreteMatOwned> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        let output_len = self.validate_transform_input(data)?;
        // COMPATIBILITY: This public estimate predates the labels-only fast path. Preserve its
        // report-sized admission envelope so existing resource budgets keep the same outcome.
        self.config
            .resource_budget
            .check(OPERATION, self.transform_resource_estimate(data)?)?;

        let mut completed_work = 0usize;
        check_cancellation(cancellation, OPERATION, completed_work, output_len)?;
        let labels =
            self.label_data_with_cancellation(data, cancellation, &mut completed_work, output_len)?;
        check_cancellation(cancellation, OPERATION, output_len, output_len)?;
        DiscreteMatOwned::new(labels, data.nrows(), data.ncols())
    }

    /// Preflight labels, occupancy sorting, report copies, and transform work.
    pub fn transform_resource_estimate(&self, data: MatRef<'_>) -> PidResult<ResourceEstimate> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        let output_len = data
            .nrows()
            .checked_mul(data.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let edge_count = self.edges.iter().try_fold(0usize, |total, edges| {
            total
                .checked_add(edges.len())
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })
        })?;
        let label_bytes = (output_len as u128)
            .checked_mul(std::mem::size_of::<usize>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let row_order_bytes = (data.nrows() as u128)
            .checked_mul(std::mem::size_of::<usize>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let observed_label_flag_count =
            data.ncols()
                .checked_mul(self.bins)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let diagnostic_count = data.ncols().checked_mul(4).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
        let report_bytes = (edge_count as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (self.edges.len() as u128)
                        .checked_mul(std::mem::size_of::<Vec<f64>>() as u128)?,
                )
            })
            .and_then(|value| {
                value.checked_add(
                    (diagnostic_count as u128).checked_mul(std::mem::size_of::<usize>() as u128)?,
                )
            })
            .and_then(|value| value.checked_add(self.config.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let log_rows = ceil_log2(data.nrows());
        let log_bins = ceil_log2(self.bins);
        let per_coordinate_work = 4u128
            .checked_add(log_rows as u128)
            .and_then(|value| value.checked_add(log_bins as u128))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let report_diagnostic_work =
            (diagnostic_count as u128)
                .checked_add((data.ncols() as u128).checked_mul(2).ok_or(
                    PidError::SizeOverflow {
                        operation: OPERATION,
                    },
                )?)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        Ok(ResourceEstimate {
            estimated_bytes: label_bytes
                .checked_add(row_order_bytes)
                .and_then(|value| value.checked_add(observed_label_flag_count as u128))
                .and_then(|value| value.checked_add(report_bytes))
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
            pairwise_distances: 0,
            operations_hint: (output_len as u128)
                .checked_mul(per_coordinate_work)
                .and_then(|value| value.checked_add(observed_label_flag_count as u128))
                .and_then(|value| value.checked_add((edge_count as u128).checked_mul(3)?))
                .and_then(|value| value.checked_add(report_diagnostic_work))
                .and_then(|value| value.checked_add(self.config.scaling_description.len() as u128))
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        })
    }

    /// Apply the fixed training edges and retain occupancy/provenance metadata.
    pub fn transform_with_report(&self, data: MatRef<'_>) -> PidResult<QuantizedData> {
        let cancellation = CancellationToken::new();
        self.transform_with_report_with_cancellation(data, &cancellation)
    }

    /// [`Self::transform_with_report`] with cooperative cancellation during labeling, occupancy
    /// analysis, report cloning, and provenance hashing.
    pub fn transform_with_report_with_cancellation(
        &self,
        data: MatRef<'_>,
        cancellation: &CancellationToken,
    ) -> PidResult<QuantizedData> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        let output_len = self.validate_transform_input(data)?;
        self.config
            .resource_budget
            .check(OPERATION, self.transform_resource_estimate(data)?)?;
        let diagnostic_edge_count = self.edges.iter().try_fold(0usize, |total, edges| {
            total
                .checked_add(edges.len())
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })
        })?;
        let observed_label_flag_count =
            data.ncols()
                .checked_mul(self.bins)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let total_work = output_len
            .checked_mul(4)
            .and_then(|value| value.checked_add(data.nrows()))
            .and_then(|value| value.checked_add(diagnostic_edge_count.checked_mul(3)?))
            .and_then(|value| value.checked_add(observed_label_flag_count))
            .and_then(|value| value.checked_add(data.ncols().checked_mul(2)?))
            .and_then(|value| value.checked_add(self.config.scaling_description.len()))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let mut completed_work = 0usize;
        check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
        let labels =
            self.label_data_with_cancellation(data, cancellation, &mut completed_work, total_work)?;
        let report = self.occupancy_report_with_cancellation(
            data,
            &labels,
            cancellation,
            &mut completed_work,
            total_work,
        )?;
        check_cancellation(cancellation, OPERATION, total_work, total_work)?;
        let matrix = DiscreteMatOwned::new(labels, data.nrows(), data.ncols())?;
        Ok(QuantizedData { matrix, report })
    }

    pub fn edges(&self) -> &[Vec<f64>] {
        &self.edges
    }

    pub fn bins(&self) -> usize {
        self.bins
    }

    pub fn training_input_hash(&self) -> Option<[u8; 32]> {
        self.training_input_hash
    }

    pub fn config(&self) -> &QuantizerConfig {
        &self.config
    }

    fn validate_transform_input(&self, data: MatRef<'_>) -> PidResult<usize> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        if data.ncols() != self.edges.len() {
            return Err(PidError::ShapeMismatch {
                context: OPERATION,
                expected_len: self.edges.len(),
                actual_len: data.ncols(),
            });
        }
        if data.nrows() == 0 {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "data must contain at least one row",
            });
        }
        data.nrows()
            .checked_mul(data.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })
    }

    fn label_data_with_cancellation(
        &self,
        data: MatRef<'_>,
        cancellation: &CancellationToken,
        completed_work: &mut usize,
        total_work: usize,
    ) -> PidResult<Vec<usize>> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        let output_len = data
            .nrows()
            .checked_mul(data.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let mut labels = try_vec_with_capacity(OPERATION, output_len, self.config.resource_budget)?;
        for row in 0..data.nrows() {
            for column in 0..data.ncols() {
                check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
                labels.push(self.bin_value(column, data.row(row)[column])?);
                *completed_work = completed_work
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
            }
        }
        Ok(labels)
    }

    fn bin_value(&self, column: usize, value: f64) -> PidResult<usize> {
        // Public transform inputs already pass through `MatRef`'s finite-value gate. Retain this
        // local guard so the partition helper cannot silently classify NaN if its internal call
        // boundary changes in the future.
        if !value.is_finite() {
            return Err(PidError::NonFiniteInput {
                context: "EqualWidthQuantizer::transform",
            });
        }
        let edges = &self.edges[column];
        let minimum = edges[0];
        let maximum = edges[self.bins];
        if minimum == maximum {
            if value == minimum
                || self.config.out_of_range_policy == OutOfRangePolicy::ClampToBoundary
            {
                return Ok(0);
            }
            return Err(PidError::QuantizerOutOfRange {
                column,
                value,
                training_min: minimum,
                training_max: maximum,
            });
        }
        if value < minimum {
            return match self.config.out_of_range_policy {
                OutOfRangePolicy::Error => Err(PidError::QuantizerOutOfRange {
                    column,
                    value,
                    training_min: minimum,
                    training_max: maximum,
                }),
                OutOfRangePolicy::ClampToBoundary => Ok(0),
            };
        }
        if value > maximum {
            return match self.config.out_of_range_policy {
                OutOfRangePolicy::Error => Err(PidError::QuantizerOutOfRange {
                    column,
                    value,
                    training_min: minimum,
                    training_max: maximum,
                }),
                OutOfRangePolicy::ClampToBoundary => Ok(self.bins - 1),
            };
        }
        if value == minimum {
            return Ok(0);
        }
        if value == maximum {
            return Ok(self.bins - 1);
        }
        let upper = edges.partition_point(|edge| *edge <= value);
        Ok(upper.saturating_sub(1).min(self.bins - 1))
    }

    fn occupancy_report_with_cancellation(
        &self,
        data: MatRef<'_>,
        labels: &[usize],
        cancellation: &CancellationToken,
        completed_work: &mut usize,
        total_work: usize,
    ) -> PidResult<QuantizationReport> {
        const OPERATION: &str = "EqualWidthQuantizer::transform";
        let mut row_order =
            try_vec_with_capacity(OPERATION, data.nrows(), self.config.resource_budget)?;
        for row in 0..data.nrows() {
            if row.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
                cancellation.check(OPERATION, *completed_work, total_work)?;
            }
            row_order.push(row);
        }
        let dimensions = data.ncols();
        cancellation.check(OPERATION, *completed_work, total_work)?;
        sort_unstable_by_with_cancellation(
            OPERATION,
            &mut row_order,
            cancellation,
            |&left, &right| {
                labels[left * dimensions..(left + 1) * dimensions]
                    .cmp(&labels[right * dimensions..(right + 1) * dimensions])
                    .then_with(|| left.cmp(&right))
            },
        )?;
        cancellation.check(OPERATION, *completed_work, total_work)?;

        let mut observed_joint_cardinality = 0usize;
        let mut low_count_joint_cells = 0usize;
        let mut minimum_observed_cell_count = usize::MAX;
        let mut maximum_observed_cell_count = 0usize;
        let mut start = 0usize;
        while start < row_order.len() {
            check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
            let first = row_order[start];
            let first_row = &labels[first * dimensions..(first + 1) * dimensions];
            let mut end = start + 1;
            while end < row_order.len() {
                if end.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
                    cancellation.check(OPERATION, *completed_work, total_work)?;
                }
                let candidate = row_order[end];
                if labels[candidate * dimensions..(candidate + 1) * dimensions] != *first_row {
                    break;
                }
                end += 1;
            }
            let count = end - start;
            observed_joint_cardinality =
                observed_joint_cardinality
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
            if count <= self.config.low_count_threshold {
                low_count_joint_cells =
                    low_count_joint_cells
                        .checked_add(1)
                        .ok_or(PidError::SizeOverflow {
                            operation: OPERATION,
                        })?;
            }
            minimum_observed_cell_count = minimum_observed_cell_count.min(count);
            maximum_observed_cell_count = maximum_observed_cell_count.max(count);
            *completed_work = completed_work
                .checked_add(count)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
            start = end;
        }

        let observed_label_flag_count =
            dimensions
                .checked_mul(self.bins)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let mut observed_label_flags = try_vec_with_capacity(
            OPERATION,
            observed_label_flag_count,
            self.config.resource_budget,
        )?;
        while observed_label_flags.len() < observed_label_flag_count {
            check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
            let chunk_len = CANCELLATION_CHECK_INTERVAL
                .min(observed_label_flag_count - observed_label_flags.len());
            observed_label_flags.extend(std::iter::repeat_n(0_u8, chunk_len));
            *completed_work =
                completed_work
                    .checked_add(chunk_len)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
        }
        let mut observed_label_counts =
            try_vec_with_capacity(OPERATION, dimensions, self.config.resource_budget)?;
        for _ in 0..dimensions {
            check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
            observed_label_counts.push(0usize);
            *completed_work = completed_work
                .checked_add(1)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        }
        for row in 0..data.nrows() {
            for column in 0..dimensions {
                check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
                let label = labels[row * dimensions + column];
                let flag_index = column
                    .checked_mul(self.bins)
                    .and_then(|offset| offset.checked_add(label))
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
                let Some(flag) = observed_label_flags.get_mut(flag_index) else {
                    return Err(PidError::NumericalInstability {
                        context: "EqualWidthQuantizer::transform label outside fitted range",
                    });
                };
                if *flag == 0 {
                    *flag = 1;
                    observed_label_counts[column] = observed_label_counts[column]
                        .checked_add(1)
                        .ok_or(PidError::SizeOverflow {
                            operation: OPERATION,
                        })?;
                }
                *completed_work = completed_work
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
            }
        }

        let mut distinct_binary64_edge_value_counts =
            try_vec_with_capacity(OPERATION, dimensions, self.config.resource_budget)?;
        let mut positive_width_interval_counts =
            try_vec_with_capacity(OPERATION, dimensions, self.config.resource_budget)?;
        let mut reachable_binary64_label_counts =
            try_vec_with_capacity(OPERATION, dimensions, self.config.resource_budget)?;
        for edges in &self.edges {
            let (distinct_edges, positive_widths, reachable_labels) =
                binary64_dimension_structure_with_cancellation(
                    edges,
                    self.bins,
                    cancellation,
                    completed_work,
                    total_work,
                )?;
            distinct_binary64_edge_value_counts.push(distinct_edges);
            positive_width_interval_counts.push(positive_widths);
            reachable_binary64_label_counts.push(reachable_labels);
        }

        let nominal_joint_cardinality = checked_pow_u128_with_cancellation(
            self.bins as u128,
            data.ncols(),
            cancellation,
            OPERATION,
            *completed_work,
            total_work,
        )?;
        let mut reachable_joint_cardinality = Some(1_u128);
        for &count in &reachable_binary64_label_counts {
            check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
            reachable_joint_cardinality =
                reachable_joint_cardinality.and_then(|value| value.checked_mul(count as u128));
            *completed_work = completed_work
                .checked_add(1)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        }
        let observed_joint_cardinality_u128 = observed_joint_cardinality as u128;
        let empty_joint_cells = checked_optional_cardinality_difference(
            nominal_joint_cardinality,
            observed_joint_cardinality_u128,
            "EqualWidthQuantizer nominal joint cardinality below observed cardinality",
        )?;
        let structurally_unreachable_joint_cells = match (
            nominal_joint_cardinality,
            reachable_joint_cardinality,
        ) {
            (Some(nominal), Some(reachable)) => Some(nominal.checked_sub(reachable).ok_or(
                PidError::NumericalInstability {
                    context:
                        "EqualWidthQuantizer reachable joint cardinality exceeds nominal cardinality",
                },
            )?),
            (None, _) => None,
            (Some(_), None) => {
                return Err(PidError::NumericalInstability {
                    context:
                        "EqualWidthQuantizer reachable cardinality overflowed below finite nominal cardinality",
                });
            }
        };
        let unobserved_reachable_joint_cells = checked_optional_cardinality_difference(
            reachable_joint_cardinality,
            observed_joint_cardinality_u128,
            "EqualWidthQuantizer reachable joint cardinality below observed cardinality",
        )?;
        if let (Some(empty), Some(structural), Some(unobserved)) = (
            empty_joint_cells,
            structurally_unreachable_joint_cells,
            unobserved_reachable_joint_cells,
        ) {
            if structural.checked_add(unobserved) != Some(empty) {
                return Err(PidError::NumericalInstability {
                    context: "EqualWidthQuantizer empty-cell partition is inconsistent",
                });
            }
        }
        let bin_edges = try_clone_edges_with_cancellation(
            OPERATION,
            &self.edges,
            self.config.resource_budget,
            cancellation,
            completed_work,
            total_work,
        )?;
        cancellation.check(OPERATION, *completed_work, total_work)?;
        let scaling_description = try_string_copy(
            OPERATION,
            &self.config.scaling_description,
            self.config.resource_budget,
        )?;
        *completed_work = completed_work
            .checked_add(self.config.scaling_description.len())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        cancellation.check(OPERATION, *completed_work, total_work)?;
        let transform_input_hash = hash_matrix_with_cancellation(
            data,
            TRANSFORM_INPUT_HASH_DOMAIN,
            cancellation,
            OPERATION,
            completed_work,
            total_work,
        )?;
        let categorical_output_hash = hash_categorical_matrix_with_cancellation(
            labels,
            data.nrows(),
            data.ncols(),
            cancellation,
            OPERATION,
            completed_work,
            total_work,
        )?;
        Ok(QuantizationReport {
            bin_edges,
            training_input_hash: self.training_input_hash,
            transform_input_hash,
            categorical_output_hash,
            out_of_range_policy: self.config.out_of_range_policy,
            scaling_description,
            n_samples: data.nrows(),
            dimensions: data.ncols(),
            bins_per_dimension: self.bins,
            distinct_binary64_edge_value_counts,
            positive_width_interval_counts,
            reachable_binary64_label_counts,
            observed_label_counts,
            nominal_joint_cardinality,
            reachable_joint_cardinality,
            observed_joint_cardinality,
            empty_joint_cells,
            structurally_unreachable_joint_cells,
            unobserved_reachable_joint_cells,
            low_count_joint_cells,
            minimum_observed_cell_count,
            maximum_observed_cell_count,
            estimand_statement:
                "PID of the declared fitted equal-width quantized variables; not continuous PID",
        })
    }
}

/// Labels plus the report that defines their quantized estimand.
#[derive(Debug, PartialEq)]
#[non_exhaustive]
pub struct QuantizedData {
    pub matrix: DiscreteMatOwned,
    pub report: QuantizationReport,
}

fn stable_lerp(minimum: f64, maximum: f64, fraction: f64) -> f64 {
    debug_assert!(minimum.is_finite() && maximum.is_finite());
    debug_assert!((0.0..=1.0).contains(&fraction));
    if fraction == 0.0 {
        minimum
    } else if fraction == 1.0 {
        maximum
    } else {
        let span = maximum - minimum;
        let candidate = if span.is_finite() {
            minimum + fraction * span
        } else {
            // A finite-endpoint subtraction can overflow only across a sufficiently wide
            // opposite-sign interval. Each convex term is then finite and has the endpoint's
            // sign, so their sum remains within the mathematical interval.
            minimum * (1.0 - fraction) + maximum * fraction
        };
        if candidate.is_finite() {
            candidate.max(minimum).min(maximum)
        } else {
            candidate
        }
    }
}

fn validate_fitted_edges(
    edges: &[f64],
    bins: usize,
    minimum: f64,
    maximum: f64,
    cancellation: &CancellationToken,
    completed_work: &mut usize,
    total_work: usize,
) -> PidResult<()> {
    const CONTEXT: &str = "EqualWidthQuantizer::fit edges";
    if edges.len() != bins + 1
        || edges
            .first()
            .is_none_or(|edge| edge.to_bits() != minimum.to_bits())
        || edges
            .last()
            .is_none_or(|edge| edge.to_bits() != maximum.to_bits())
    {
        return Err(PidError::NumericalInstability { context: CONTEXT });
    }
    for (index, &edge) in edges.iter().enumerate() {
        check_cancellation(
            cancellation,
            "EqualWidthQuantizer::fit",
            *completed_work,
            total_work,
        )?;
        if !edge.is_finite()
            || edge < minimum
            || edge > maximum
            || (index > 0 && edges[index - 1] > edge)
        {
            return Err(PidError::NumericalInstability { context: CONTEXT });
        }
        *completed_work = completed_work
            .checked_add(1)
            .ok_or(PidError::SizeOverflow {
                operation: "EqualWidthQuantizer::fit",
            })?;
    }
    Ok(())
}

fn binary64_dimension_structure_with_cancellation(
    edges: &[f64],
    bins: usize,
    cancellation: &CancellationToken,
    completed_work: &mut usize,
    total_work: usize,
) -> PidResult<(usize, usize, usize)> {
    const OPERATION: &str = "EqualWidthQuantizer::transform";
    let mut positive_width_intervals = 0usize;
    let mut has_negative_zero = false;
    let mut has_positive_zero = false;
    for (index, &edge) in edges.iter().enumerate() {
        check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
        has_negative_zero |= edge.to_bits() == (-0.0_f64).to_bits();
        has_positive_zero |= edge.to_bits() == 0.0_f64.to_bits();
        if index > 0 && edges[index - 1] < edge {
            positive_width_intervals =
                positive_width_intervals
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
        }
        *completed_work = completed_work
            .checked_add(1)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    }
    // Monotone finite nonzero values have one binary64 payload per numeric value. A strictly
    // wider adjacent interval therefore introduces exactly one new value; signed zero is the
    // only numerically equal pair with two payloads.
    let distinct_binary64_edges = positive_width_intervals
        .checked_add(1)
        .and_then(|value| value.checked_add(usize::from(has_negative_zero && has_positive_zero)))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;

    let minimum = edges[0];
    let maximum = edges[bins];
    let mut reachable_labels = if minimum == maximum { 1usize } else { 2usize };
    if minimum != maximum {
        for label in 1..bins - 1 {
            check_cancellation(cancellation, OPERATION, *completed_work, total_work)?;
            let lower = edges[label];
            let upper = edges[label + 1];
            // Endpoint overrides make labels 0 and B-1 reachable. For an interior label j, the
            // accepted finite preimage is [e_j,e_{j+1}) intersected with (m,M). When e_j=m, the
            // next representable value must still lie strictly below e_{j+1}; subtraction would
            // lose exactly the adjacent-value cases this diagnostic is intended to expose.
            if (lower > minimum && lower < upper) || (lower == minimum && minimum.next_up() < upper)
            {
                reachable_labels =
                    reachable_labels
                        .checked_add(1)
                        .ok_or(PidError::SizeOverflow {
                            operation: OPERATION,
                        })?;
            }
            *completed_work = completed_work
                .checked_add(1)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        }
    }
    Ok((
        distinct_binary64_edges,
        positive_width_intervals,
        reachable_labels,
    ))
}

fn checked_optional_cardinality_difference(
    total: Option<u128>,
    part: u128,
    context: &'static str,
) -> PidResult<Option<u128>> {
    total
        .map(|value| {
            value
                .checked_sub(part)
                .ok_or(PidError::NumericalInstability { context })
        })
        .transpose()
}

fn check_cancellation(
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_units: usize,
    total_units: usize,
) -> PidResult<()> {
    if completed_units == 0
        || completed_units == total_units
        || completed_units.is_multiple_of(CANCELLATION_CHECK_INTERVAL)
    {
        cancellation.check(operation, completed_units, total_units)?;
    }
    Ok(())
}

fn hash_matrix_with_cancellation(
    matrix: MatRef<'_>,
    domain: &[u8],
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_work: &mut usize,
    total_work: usize,
) -> PidResult<[u8; 32]> {
    let mut digest = Sha256::new();
    digest.update(domain);
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    for row in 0..matrix.nrows() {
        for value in matrix.row(row) {
            check_cancellation(cancellation, operation, *completed_work, total_work)?;
            digest.update(value.to_bits().to_le_bytes());
            *completed_work = completed_work
                .checked_add(1)
                .ok_or(PidError::SizeOverflow { operation })?;
        }
    }
    Ok(digest.finalize().into())
}

fn hash_categorical_matrix_with_cancellation(
    labels: &[usize],
    nrows: usize,
    ncols: usize,
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_work: &mut usize,
    total_work: usize,
) -> PidResult<[u8; 32]> {
    let mut digest = Sha256::new();
    digest.update(CATEGORICAL_OUTPUT_HASH_DOMAIN);
    digest.update((nrows as u128).to_le_bytes());
    digest.update((ncols as u128).to_le_bytes());
    for &label in labels {
        check_cancellation(cancellation, operation, *completed_work, total_work)?;
        digest.update((label as u128).to_le_bytes());
        *completed_work = completed_work
            .checked_add(1)
            .ok_or(PidError::SizeOverflow { operation })?;
    }
    Ok(digest.finalize().into())
}

fn checked_pow_u128_with_cancellation(
    base: u128,
    exponent: usize,
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_work: usize,
    total_work: usize,
) -> PidResult<Option<u128>> {
    let mut result = 1_u128;
    for index in 0..exponent {
        if index.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, completed_work, total_work)?;
        }
        let Some(next) = result.checked_mul(base) else {
            return Ok(None);
        };
        result = next;
    }
    Ok(Some(result))
}

fn ceil_log2(value: usize) -> u32 {
    if value <= 1 {
        0
    } else {
        usize::BITS - (value - 1).leading_zeros()
    }
}

fn try_string_copy(
    operation: &'static str,
    value: &str,
    budget: ResourceBudget,
) -> PidResult<String> {
    let estimate = ResourceEstimate::contiguous::<u8>(operation, value.len())?;
    budget.check(operation, estimate)?;
    let mut copy = String::new();
    copy.try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: estimate.estimated_bytes,
        })?;
    copy.push_str(value);
    Ok(copy)
}

fn try_clone_edges(
    operation: &'static str,
    edges: &[Vec<f64>],
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<f64>>> {
    let mut cloned = try_vec_with_capacity(operation, edges.len(), budget)?;
    for column in edges {
        let mut cloned_column = try_vec_with_capacity(operation, column.len(), budget)?;
        cloned_column.extend_from_slice(column);
        cloned.push(cloned_column);
    }
    Ok(cloned)
}

fn try_clone_usize_counts(
    operation: &'static str,
    counts: &[usize],
    budget: ResourceBudget,
) -> PidResult<Vec<usize>> {
    let mut cloned = try_vec_with_capacity(operation, counts.len(), budget)?;
    cloned.extend_from_slice(counts);
    Ok(cloned)
}

fn try_clone_edges_with_cancellation(
    operation: &'static str,
    edges: &[Vec<f64>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
    completed_work: &mut usize,
    total_work: usize,
) -> PidResult<Vec<Vec<f64>>> {
    cancellation.check(operation, *completed_work, total_work)?;
    let mut cloned = try_vec_with_capacity(operation, edges.len(), budget)?;
    for column in edges {
        let mut cloned_column = try_vec_with_capacity(operation, column.len(), budget)?;
        for chunk in column.chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, *completed_work, total_work)?;
            cloned_column.extend_from_slice(chunk);
            *completed_work = completed_work
                .checked_add(chunk.len())
                .ok_or(PidError::SizeOverflow { operation })?;
        }
        cloned.push(cloned_column);
    }
    cancellation.check(operation, *completed_work, total_work)?;
    Ok(cloned)
}

#[cfg(test)]
mod tests {
    use super::{
        ceil_log2, hash_categorical_matrix_with_cancellation, EqualWidthQuantizer,
        OutOfRangePolicy, QuantizationReport, QuantizerConfig,
    };
    use crate::error::PidError;
    use crate::matrix::MatRef;
    use crate::resource::{CancellationToken, ResourceBudget};

    #[test]
    fn fit_with_cancellation_honors_a_pre_cancelled_token() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = EqualWidthQuantizer::fit_with_cancellation(
            MatRef::new(&training, 4, 1).unwrap(),
            2,
            QuantizerConfig::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "EqualWidthQuantizer::fit",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn transform_with_cancellation_honors_a_pre_cancelled_token() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 4, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = quantizer.transform_with_report_with_cancellation(
            MatRef::new(&training, 4, 1).unwrap(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "EqualWidthQuantizer::transform",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn labels_only_transform_with_cancellation_honors_a_pre_cancelled_token() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let matrix = MatRef::new(&training, 4, 1).unwrap();
        let quantizer = EqualWidthQuantizer::fit(matrix, 2, QuantizerConfig::default()).unwrap();
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = quantizer.transform_with_cancellation(matrix, &cancellation);

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "EqualWidthQuantizer::transform",
                completed_units: 0,
                total_units: 4,
            })
        ));
    }

    #[test]
    fn uncancelled_quantizer_path_matches_compatibility_entry_points_exactly() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let matrix = MatRef::new(&training, 4, 1).unwrap();
        let expected = EqualWidthQuantizer::fit(matrix, 3, QuantizerConfig::default()).unwrap();
        let cancellation = CancellationToken::new();
        let actual = EqualWidthQuantizer::fit_with_cancellation(
            matrix,
            3,
            QuantizerConfig::default(),
            &cancellation,
        )
        .unwrap();

        assert_eq!(actual, expected);
        let expected_transform = expected.transform_with_report(matrix).unwrap();
        let actual_transform = actual
            .transform_with_report_with_cancellation(matrix, &cancellation)
            .unwrap();
        assert_eq!(actual_transform, expected_transform);
    }

    #[test]
    fn held_out_transform_reuses_training_edges_exactly() {
        let training = [0.0, 10.0];
        let evaluation = [2.0, 8.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();

        let transformed = quantizer
            .transform_with_report(MatRef::new(&evaluation, 2, 1).unwrap())
            .unwrap();

        assert_eq!(transformed.matrix.data(), &[0, 1]);
        assert_eq!(transformed.report.bin_edges, vec![vec![0.0, 5.0, 10.0]]);
    }

    #[test]
    fn labels_only_transform_matches_report_matrix_across_binary64_edge_cases() {
        let cases = [
            (vec![7.0, 7.0], 4),
            (vec![-0.0, 0.0], 4),
            (vec![1.0, 1.0_f64.next_up()], 9),
            (vec![-f64::MAX, f64::MAX], 100),
        ];

        for (training, bins) in cases {
            let matrix = MatRef::new(&training, training.len(), 1).unwrap();
            let quantizer =
                EqualWidthQuantizer::fit(matrix, bins, QuantizerConfig::default()).unwrap();

            assert_eq!(
                quantizer.transform(matrix).unwrap(),
                quantizer.transform_with_report(matrix).unwrap().matrix
            );
        }
    }

    #[test]
    fn labels_only_and_report_paths_match_out_of_range_policies() {
        let training = [0.0, 10.0];
        let evaluation = [-1.0, 0.0, 5.0, 10.0, 11.0];
        let training_matrix = MatRef::new(&training, 2, 1).unwrap();
        let evaluation_matrix = MatRef::new(&evaluation, 5, 1).unwrap();
        let clamp_config = QuantizerConfig::new(
            OutOfRangePolicy::ClampToBoundary,
            true,
            5,
            "none; raw input units",
            ResourceBudget::default(),
        )
        .unwrap();
        let clamp_quantizer = EqualWidthQuantizer::fit(training_matrix, 2, clamp_config).unwrap();

        assert_eq!(
            clamp_quantizer.transform(evaluation_matrix).unwrap(),
            clamp_quantizer
                .transform_with_report(evaluation_matrix)
                .unwrap()
                .matrix
        );

        let error_quantizer =
            EqualWidthQuantizer::fit(training_matrix, 2, QuantizerConfig::default()).unwrap();
        assert!(matches!(
            error_quantizer.transform(evaluation_matrix),
            Err(PidError::QuantizerOutOfRange {
                column: 0,
                value: -1.0,
                training_min: 0.0,
                training_max: 10.0,
            })
        ));
        assert!(matches!(
            error_quantizer.transform_with_report(evaluation_matrix),
            Err(PidError::QuantizerOutOfRange {
                column: 0,
                value: -1.0,
                training_min: 0.0,
                training_max: 10.0,
            })
        ));
    }

    #[test]
    fn adjacent_binary64_endpoints_keep_order_range_and_endpoint_labels() {
        for (minimum, maximum) in [
            (1.0, f64::from_bits(1.0_f64.to_bits() + 1)),
            (f64::from_bits(f64::MAX.to_bits() - 1), f64::MAX),
            (-f64::MAX, -f64::from_bits(f64::MAX.to_bits() - 1)),
            (f64::from_bits(1), f64::from_bits(2)),
        ] {
            for bins in [2, 3, 9, 100] {
                let training = [minimum, maximum];
                let matrix = MatRef::new(&training, 2, 1).unwrap();
                let quantizer =
                    EqualWidthQuantizer::fit(matrix, bins, QuantizerConfig::default()).unwrap();
                let edges = &quantizer.edges()[0];

                assert_eq!(edges.len(), bins + 1);
                assert_eq!(edges[0].to_bits(), minimum.to_bits());
                assert_eq!(edges[bins].to_bits(), maximum.to_bits());
                assert!(edges
                    .iter()
                    .all(|edge| { edge.is_finite() && *edge >= minimum && *edge <= maximum }));
                assert!(edges.windows(2).all(|pair| pair[0] <= pair[1]));

                let transformed = quantizer.transform(matrix).unwrap();
                assert_eq!(transformed.data(), &[0, bins - 1]);
            }
        }
    }

    #[test]
    fn difference_first_interpolation_repairs_legacy_edge_below_training_minimum() {
        let minimum = f64::from_bits(0x7fef_ffff_ffff_fffd);
        let maximum = f64::from_bits(0x7fef_ffff_ffff_fffe);
        let fraction = 3.0 / 7.0;
        let legacy_convex = minimum * (1.0 - fraction) + maximum * fraction;
        assert_eq!(legacy_convex.to_bits(), 0x7fef_ffff_ffff_fffc);
        assert!(legacy_convex < minimum);

        let training = [minimum, maximum];
        let matrix = MatRef::new(&training, 2, 1).unwrap();
        let quantizer = EqualWidthQuantizer::fit(matrix, 7, QuantizerConfig::default()).unwrap();
        let edges = &quantizer.edges()[0];

        assert_eq!(edges[3].to_bits(), minimum.to_bits());
        assert!(edges
            .iter()
            .all(|edge| *edge >= minimum && *edge <= maximum));
        assert!(edges.windows(2).all(|pair| pair[0] <= pair[1]));
    }

    #[test]
    fn signed_zero_fit_preserves_total_order_endpoints_for_both_row_orders() {
        for training in [[-0.0, 0.0], [0.0, -0.0]] {
            let matrix = MatRef::new(&training, 2, 1).unwrap();
            let quantizer =
                EqualWidthQuantizer::fit(matrix, 4, QuantizerConfig::default()).unwrap();
            let edges = &quantizer.edges()[0];

            assert_eq!(edges[0].to_bits(), (-0.0_f64).to_bits());
            assert_eq!(edges[4].to_bits(), 0.0_f64.to_bits());
            let transformed = quantizer.transform_with_report(matrix).unwrap();
            assert_eq!(transformed.matrix.data(), &[0, 0]);
            assert_eq!(transformed.report.distinct_binary64_edge_value_counts, [2]);
        }
    }

    #[test]
    fn report_separates_nominal_reachable_and_observed_labels() {
        let adjacent = 1.0_f64.next_up();
        let two_steps = adjacent.next_up();
        let cases = [
            // requested bins, training, distinct edge payloads, positive widths, reachable,
            // observed, structural nominal empties, reachable sampling empties
            (4, vec![7.0, 7.0], 1, 0, 1, 1, 3, 0),
            (4, vec![-0.0, 0.0], 2, 0, 1, 1, 3, 0),
            (4, vec![1.0, adjacent], 2, 1, 2, 2, 2, 0),
            (4, vec![1.0, two_steps], 3, 2, 3, 2, 1, 1),
        ];

        for (
            bins,
            training,
            distinct_edges,
            positive_widths,
            reachable,
            observed,
            structural,
            unobserved,
        ) in cases
        {
            let matrix = MatRef::new(&training, training.len(), 1).unwrap();
            let quantizer =
                EqualWidthQuantizer::fit(matrix, bins, QuantizerConfig::default()).unwrap();
            let transformed = quantizer.transform_with_report(matrix).unwrap();
            let report = transformed.report;

            assert_eq!(report.distinct_binary64_edge_value_counts, [distinct_edges]);
            assert_eq!(report.positive_width_interval_counts, [positive_widths]);
            assert_eq!(report.reachable_binary64_label_counts, [reachable]);
            assert_eq!(report.observed_label_counts, [observed]);
            assert_eq!(report.nominal_joint_cardinality, Some(bins as u128));
            assert_eq!(report.reachable_joint_cardinality, Some(reachable as u128));
            assert_eq!(report.observed_joint_cardinality, observed);
            assert_eq!(
                report.structurally_unreachable_joint_cells,
                Some(structural)
            );
            assert_eq!(report.unobserved_reachable_joint_cells, Some(unobserved));
            assert_eq!(report.empty_joint_cells, Some(structural + unobserved));
        }
    }

    #[test]
    fn report_reachable_label_count_handles_noncontiguous_preimage() {
        let minimum = 1.0_f64;
        let middle = minimum.next_up();
        let maximum = middle.next_up();
        let training = [minimum, maximum];
        let matrix = MatRef::new(&training, 2, 1).unwrap();
        let quantizer = EqualWidthQuantizer::fit(matrix, 4, QuantizerConfig::default()).unwrap();
        let transformed = quantizer.transform_with_report(matrix).unwrap();

        assert_eq!(
            quantizer.edges()[0],
            [minimum, minimum, middle, maximum, maximum]
        );
        assert_eq!(transformed.matrix.data(), &[0, 3]);
        assert_eq!(
            transformed.report.reachable_binary64_label_counts,
            [3],
            "the exact reachable label set is noncontiguous: {{0,2,3}}"
        );
        assert_eq!(transformed.report.observed_label_counts, [2]);
        assert_eq!(transformed.report.unobserved_reachable_joint_cells, Some(1));
    }

    #[test]
    fn report_cardinality_none_means_only_u128_product_overflow() {
        const DIMENSIONS: usize = 129;
        let constant_training = vec![1.0; DIMENSIONS];
        let constant_matrix = MatRef::new(&constant_training, 1, DIMENSIONS).unwrap();
        let constant_quantizer =
            EqualWidthQuantizer::fit(constant_matrix, 2, QuantizerConfig::default()).unwrap();
        let constant_report = constant_quantizer
            .transform_with_report(constant_matrix)
            .unwrap()
            .report;
        assert_eq!(constant_report.nominal_joint_cardinality, None);
        assert_eq!(constant_report.reachable_joint_cardinality, Some(1));
        assert_eq!(constant_report.structurally_unreachable_joint_cells, None);
        assert_eq!(constant_report.unobserved_reachable_joint_cells, Some(0));

        let mut resolved_training = vec![0.0; DIMENSIONS];
        resolved_training.extend(std::iter::repeat_n(1.0, DIMENSIONS));
        let resolved_matrix = MatRef::new(&resolved_training, 2, DIMENSIONS).unwrap();
        let resolved_quantizer =
            EqualWidthQuantizer::fit(resolved_matrix, 2, QuantizerConfig::default()).unwrap();
        let resolved_report = resolved_quantizer
            .transform_with_report(resolved_matrix)
            .unwrap()
            .report;
        assert_eq!(resolved_report.nominal_joint_cardinality, None);
        assert_eq!(resolved_report.reachable_joint_cardinality, None);
        assert_eq!(resolved_report.structurally_unreachable_joint_cells, None);
        assert_eq!(resolved_report.unobserved_reachable_joint_cells, None);
    }

    #[test]
    fn opposite_extreme_endpoints_use_a_finite_monotone_convex_fallback() {
        let training = [-f64::MAX, f64::MAX];
        let matrix = MatRef::new(&training, 2, 1).unwrap();
        let quantizer = EqualWidthQuantizer::fit(matrix, 100, QuantizerConfig::default()).unwrap();
        let edges = &quantizer.edges()[0];

        assert!(edges.iter().all(|edge| edge.is_finite()));
        assert!(edges.windows(2).all(|pair| pair[0] <= pair[1]));
        assert_eq!(edges[50].to_bits(), 0.0_f64.to_bits());
        assert_eq!(quantizer.transform(matrix).unwrap().data(), &[0, 99]);
    }

    #[test]
    fn held_out_outlier_obeys_explicit_error_policy() {
        let training = [0.0, 10.0];
        let evaluation = [11.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();

        assert!(matches!(
            quantizer.transform(MatRef::new(&evaluation, 1, 1).unwrap()),
            Err(PidError::QuantizerOutOfRange { column: 0, .. })
        ));
    }

    #[test]
    fn internal_partition_fails_closed_on_nonfinite_values() {
        let training = [0.0, 1.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();

        for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
            assert!(matches!(
                quantizer.bin_value(0, value),
                Err(PidError::NonFiniteInput {
                    context: "EqualWidthQuantizer::transform"
                })
            ));
        }
    }

    #[test]
    fn report_serializes_exact_fitted_edges_and_occupancy() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let config = QuantizerConfig::new(
            OutOfRangePolicy::ClampToBoundary,
            true,
            1,
            "training-standardizer-v1",
            ResourceBudget::default(),
        )
        .unwrap();
        let quantizer =
            EqualWidthQuantizer::fit(MatRef::new(&training, 4, 1).unwrap(), 3, config).unwrap();
        let transformed = quantizer
            .transform_with_report(MatRef::new(&training, 4, 1).unwrap())
            .unwrap();

        let json = serde_json::to_value(&transformed.report).unwrap();

        assert_eq!(json["bin_edges"], serde_json::json!([[0.0, 1.0, 2.0, 3.0]]));
        assert_eq!(json["observed_joint_cardinality"], 3);
        assert_eq!(
            json["distinct_binary64_edge_value_counts"],
            serde_json::json!([4])
        );
        assert_eq!(
            json["positive_width_interval_counts"],
            serde_json::json!([3])
        );
        assert_eq!(
            json["reachable_binary64_label_counts"],
            serde_json::json!([3])
        );
        assert_eq!(json["observed_label_counts"], serde_json::json!([3]));
        assert_eq!(json["reachable_joint_cardinality"], 3);
        assert_eq!(json["structurally_unreachable_joint_cells"], 0);
        assert_eq!(json["unobserved_reachable_joint_cells"], 0);
        assert!(json.get("training_input_hash").is_some());
        assert!(json.get("transform_input_hash").is_some());
        assert!(json.get("categorical_output_hash").is_some());
        assert!(json.get("training_data_hash").is_none());
        assert!(json.get("transformed_data_hash").is_none());
    }

    #[test]
    fn provenance_hash_domains_match_fixed_vectors() {
        let training = [0.0, 1.0, 2.0, 3.0];
        let matrix = MatRef::new(&training, 4, 1).unwrap();
        let quantizer = EqualWidthQuantizer::fit(matrix, 3, QuantizerConfig::default()).unwrap();
        let transformed = quantizer.transform_with_report(matrix).unwrap();

        assert_eq!(
            quantizer.training_input_hash(),
            Some([
                0xe3, 0xd2, 0x9e, 0xe9, 0xb7, 0x4e, 0x7d, 0x47, 0x81, 0xfd, 0x82, 0x37, 0x34, 0xa3,
                0x4f, 0x75, 0x41, 0xfc, 0x5e, 0xc0, 0xda, 0xe9, 0x25, 0x59, 0xeb, 0xba, 0x4a, 0x2b,
                0x47, 0x51, 0x74, 0x4a,
            ])
        );
        assert_eq!(
            transformed.report.transform_input_hash,
            [
                0xb6, 0xee, 0xda, 0x57, 0xf4, 0x85, 0xb3, 0x91, 0x0c, 0xa9, 0x55, 0x4b, 0x24, 0x51,
                0xd8, 0xa4, 0x68, 0x9f, 0xa2, 0xaf, 0xd0, 0xb9, 0xe8, 0x9c, 0x5f, 0x61, 0x88, 0x79,
                0xc7, 0xdc, 0x8d, 0x24,
            ]
        );
        assert_eq!(
            transformed.report.categorical_output_hash,
            [
                0x13, 0x42, 0xd2, 0x3a, 0x1b, 0xb7, 0x59, 0xe6, 0xbf, 0x91, 0xc2, 0xaa, 0xe2, 0x30,
                0x5c, 0xbf, 0x2f, 0x7e, 0x67, 0xd4, 0x58, 0xda, 0xae, 0x50, 0xc0, 0x61, 0xb2, 0xd0,
                0x47, 0x84, 0xd5, 0xf5,
            ]
        );
        assert_ne!(
            transformed.report.training_input_hash.unwrap(),
            transformed.report.transform_input_hash,
            "training and transform domains must differ even for identical matrix bytes"
        );
    }

    #[test]
    fn input_and_categorical_output_hashes_have_distinct_semantics() {
        let training = [0.0, 10.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();
        let first_values = [1.0, 2.0];
        let second_values = [3.0, 4.0];
        let third_values = [3.0, 9.0];
        let first = quantizer
            .transform_with_report(MatRef::new(&first_values, 2, 1).unwrap())
            .unwrap();
        let second = quantizer
            .transform_with_report(MatRef::new(&second_values, 2, 1).unwrap())
            .unwrap();
        let third = quantizer
            .transform_with_report(MatRef::new(&third_values, 2, 1).unwrap())
            .unwrap();

        assert_eq!(first.matrix.data(), second.matrix.data());
        assert_ne!(
            first.report.transform_input_hash,
            second.report.transform_input_hash
        );
        assert_eq!(
            first.report.categorical_output_hash,
            second.report.categorical_output_hash
        );
        assert_ne!(second.matrix.data(), third.matrix.data());
        assert_ne!(
            second.report.categorical_output_hash,
            third.report.categorical_output_hash
        );
    }

    #[test]
    fn categorical_output_hash_commits_to_matrix_shape() {
        let labels = [0, 1, 0, 1];
        let cancellation = CancellationToken::new();
        let mut completed = 0;
        let two_by_two = hash_categorical_matrix_with_cancellation(
            &labels,
            2,
            2,
            &cancellation,
            "categorical hash test",
            &mut completed,
            labels.len(),
        )
        .unwrap();
        let mut completed = 0;
        let four_by_one = hash_categorical_matrix_with_cancellation(
            &labels,
            4,
            1,
            &cancellation,
            "categorical hash test",
            &mut completed,
            labels.len(),
        )
        .unwrap();

        assert_ne!(two_by_two, four_by_one);
    }

    #[test]
    fn disabling_training_hash_does_not_disable_transform_provenance() {
        let training = [0.0, 1.0];
        let config = QuantizerConfig::new(
            OutOfRangePolicy::Error,
            false,
            1,
            "raw",
            ResourceBudget::default(),
        )
        .unwrap();
        let quantizer =
            EqualWidthQuantizer::fit(MatRef::new(&training, 2, 1).unwrap(), 2, config).unwrap();
        let transformed = quantizer
            .transform_with_report(MatRef::new(&training, 2, 1).unwrap())
            .unwrap();

        assert_eq!(quantizer.training_input_hash(), None);
        assert_eq!(transformed.report.training_input_hash, None);
        assert_ne!(transformed.report.transform_input_hash, [0; 32]);
        assert_ne!(transformed.report.categorical_output_hash, [0; 32]);
    }

    #[test]
    fn giant_bin_count_is_rejected_before_edge_allocation() {
        let training = [0.0, 1.0];
        let error = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            200_000_000,
            QuantizerConfig::default(),
        )
        .unwrap_err();

        assert!(matches!(error, PidError::ResourceLimitExceeded { .. }));
    }

    #[test]
    fn transform_checks_labels_sort_order_and_report_copy_as_one_budget() {
        let training = [0.0, 1.0];
        let budget = ResourceBudget {
            max_bytes: 64,
            ..ResourceBudget::default()
        };
        let config =
            QuantizerConfig::new(OutOfRangePolicy::Error, false, 1, "raw", budget).unwrap();
        let quantizer =
            EqualWidthQuantizer::fit(MatRef::new(&training, 2, 1).unwrap(), 2, config).unwrap();

        let error = quantizer
            .transform_with_report(MatRef::new(&training, 2, 1).unwrap())
            .unwrap_err();
        assert!(matches!(error, PidError::ResourceLimitExceeded { .. }));
    }

    #[test]
    fn fitted_state_and_report_copy_only_through_fallible_budgeted_paths() {
        let training = [0.0, 1.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();
        let transformed = quantizer
            .transform_with_report(MatRef::new(&training, 2, 1).unwrap())
            .unwrap();
        let tiny = ResourceBudget {
            max_bytes: 1,
            ..ResourceBudget::default()
        };

        assert!(matches!(
            quantizer.try_clone_with_budget(tiny),
            Err(PidError::ResourceLimitExceeded { .. })
        ));
        assert!(matches!(
            transformed.report.try_clone_with_budget(tiny),
            Err(PidError::ResourceLimitExceeded { .. })
        ));
        assert_eq!(
            quantizer
                .try_clone_with_budget(ResourceBudget::default())
                .unwrap(),
            quantizer
        );
    }

    #[test]
    fn fitted_quantizer_clone_preflight_tracks_edges_and_utf8_scaling_work_exactly() {
        let training = [0.0, 1.0];
        let scaling_description = "σ→τ".repeat(1_024);
        let config = QuantizerConfig::new(
            OutOfRangePolicy::Error,
            true,
            5,
            &scaling_description,
            ResourceBudget::default(),
        )
        .unwrap();
        let quantizer =
            EqualWidthQuantizer::fit(MatRef::new(&training, 2, 1).unwrap(), 17, config).unwrap();
        let edge_count = quantizer.edges.iter().map(Vec::len).sum::<usize>() as u128;
        let expected_bytes = edge_count * std::mem::size_of::<f64>() as u128
            + quantizer.edges.len() as u128 * std::mem::size_of::<Vec<f64>>() as u128
            + scaling_description.len() as u128;
        let expected_operations = edge_count + scaling_description.len() as u128;
        let defaults = ResourceBudget::default();
        let exact_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations,
            defaults.max_threads,
        )
        .unwrap();
        let byte_limited_budget = ResourceBudget::new(
            u64::try_from(expected_bytes - 1).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations,
            defaults.max_threads,
        )
        .unwrap();
        let operation_limited_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations - 1,
            defaults.max_threads,
        )
        .unwrap();

        assert_eq!(
            quantizer.try_clone_with_budget(exact_budget).unwrap(),
            quantizer
        );
        assert!(matches!(
            quantizer.try_clone_with_budget(byte_limited_budget),
            Err(PidError::ResourceLimitExceeded {
                operation: "EqualWidthQuantizer::try_clone_with_budget",
                resource: "bytes",
                requested,
                limit,
                ..
            }) if requested == expected_bytes && limit == expected_bytes - 1
        ));
        assert!(matches!(
            quantizer.try_clone_with_budget(operation_limited_budget),
            Err(PidError::ResourceLimitExceeded {
                operation: "EqualWidthQuantizer::try_clone_with_budget",
                resource: "operations_hint",
                requested,
                limit,
                ..
            }) if requested == expected_operations && limit == expected_operations - 1
        ));
    }

    #[test]
    fn transform_preflight_tracks_large_bin_report_copy_work_exactly() {
        let training = [0.0, 1.0];
        let evaluation = [0.5];
        let bins = 4_096usize;
        let scaling_description = "σ→τ".repeat(128);
        let config = QuantizerConfig::new(
            OutOfRangePolicy::Error,
            true,
            5,
            &scaling_description,
            ResourceBudget::default(),
        )
        .unwrap();
        let mut quantizer =
            EqualWidthQuantizer::fit(MatRef::new(&training, 2, 1).unwrap(), bins, config).unwrap();
        let data = MatRef::new(&evaluation, 1, 1).unwrap();
        let estimate = quantizer.transform_resource_estimate(data).unwrap();
        let edge_count = (bins + 1) as u128;
        let diagnostic_count = 4u128;
        let per_coordinate_work = 4u128 + ceil_log2(1) as u128 + ceil_log2(bins) as u128;
        let expected_bytes = std::mem::size_of::<usize>() as u128
            + std::mem::size_of::<usize>() as u128
            + bins as u128
            + edge_count * std::mem::size_of::<f64>() as u128
            + std::mem::size_of::<Vec<f64>>() as u128
            + diagnostic_count * std::mem::size_of::<usize>() as u128
            + scaling_description.len() as u128;
        let expected_operations = per_coordinate_work
            + bins as u128
            + 3 * edge_count
            + diagnostic_count
            + 2
            + scaling_description.len() as u128;

        assert_eq!(
            (estimate.estimated_bytes, estimate.operations_hint),
            (expected_bytes, expected_operations)
        );

        let defaults = ResourceBudget::default();
        let exact_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations,
            defaults.max_threads,
        )
        .unwrap();
        quantizer.config.resource_budget = exact_budget;
        assert!(quantizer.transform_with_report(data).is_ok());
        let operation_limited_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations - 1,
            defaults.max_threads,
        )
        .unwrap();
        quantizer.config.resource_budget = operation_limited_budget;
        assert!(matches!(
            quantizer.transform_with_report(data),
            Err(PidError::ResourceLimitExceeded {
                operation: "EqualWidthQuantizer::transform",
                resource: "operations_hint",
                requested,
                limit,
                ..
            }) if requested == expected_operations && limit == expected_operations - 1
        ));
    }

    #[test]
    fn labels_only_transform_preserves_report_sized_budget_admission() {
        let training = [0.0, 1.0];
        let evaluation = [0.5];
        let mut quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            4_096,
            QuantizerConfig::default(),
        )
        .unwrap();
        let data = MatRef::new(&evaluation, 1, 1).unwrap();
        let estimate = quantizer.transform_resource_estimate(data).unwrap();
        let defaults = ResourceBudget::default();
        quantizer.config.resource_budget = ResourceBudget::new(
            u64::try_from(estimate.estimated_bytes).unwrap(),
            defaults.max_pairwise_distances,
            estimate.operations_hint,
            defaults.max_threads,
        )
        .unwrap();
        assert_eq!(quantizer.transform(data).unwrap().data(), &[2_048]);

        quantizer.config.resource_budget = ResourceBudget::new(
            u64::try_from(estimate.estimated_bytes).unwrap(),
            defaults.max_pairwise_distances,
            estimate.operations_hint - 1,
            defaults.max_threads,
        )
        .unwrap();

        let result = quantizer.transform(data);

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded {
                operation: "EqualWidthQuantizer::transform",
                resource: "operations_hint",
                requested,
                limit,
                ..
            }) if requested == estimate.operations_hint && limit + 1 == requested
        ));
    }

    fn irregular_mutable_report() -> QuantizationReport {
        let training = [0.0, 1.0];
        let quantizer = EqualWidthQuantizer::fit(
            MatRef::new(&training, 2, 1).unwrap(),
            2,
            QuantizerConfig::default(),
        )
        .unwrap();
        let mut report = quantizer
            .transform_with_report(MatRef::new(&training, 2, 1).unwrap())
            .unwrap()
            .report;
        report.bin_edges = vec![vec![-1.0, 0.0], vec![], vec![1.0; 5]];
        report.distinct_binary64_edge_value_counts = vec![0; 2];
        report.positive_width_interval_counts = vec![0; 3];
        report.reachable_binary64_label_counts = vec![0; 5];
        report.observed_label_counts = vec![0; 7];
        report.scaling_description = "σ→τ".to_owned();
        assert_eq!(report.scaling_description.chars().count(), 3);
        assert_eq!(report.scaling_description.len(), 7);
        report
    }

    #[test]
    fn report_clone_preflight_tracks_actual_heap_and_copy_work_exactly() {
        let report = irregular_mutable_report();
        let edge_count = report.bin_edges.iter().map(Vec::len).sum::<usize>();
        let diagnostic_count = [
            report.distinct_binary64_edge_value_counts.len(),
            report.positive_width_interval_counts.len(),
            report.reachable_binary64_label_counts.len(),
            report.observed_label_counts.len(),
        ]
        .into_iter()
        .sum::<usize>();
        let expected_bytes = edge_count as u128 * std::mem::size_of::<f64>() as u128
            + report.bin_edges.len() as u128 * std::mem::size_of::<Vec<f64>>() as u128
            + diagnostic_count as u128 * std::mem::size_of::<usize>() as u128
            + report.scaling_description.len() as u128;
        let expected_operations = edge_count as u128
            + diagnostic_count as u128
            + report.scaling_description.len() as u128;
        let defaults = ResourceBudget::default();
        let exact_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations,
            defaults.max_threads,
        )
        .unwrap();
        let byte_limited_budget = ResourceBudget::new(
            u64::try_from(expected_bytes - 1).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations,
            defaults.max_threads,
        )
        .unwrap();
        let operation_limited_budget = ResourceBudget::new(
            u64::try_from(expected_bytes).unwrap(),
            defaults.max_pairwise_distances,
            expected_operations - 1,
            defaults.max_threads,
        )
        .unwrap();

        assert_eq!(report.try_clone_with_budget(exact_budget).unwrap(), report);
        assert!(matches!(
            report.try_clone_with_budget(byte_limited_budget),
            Err(PidError::ResourceLimitExceeded {
                operation: "QuantizationReport::try_clone_with_budget",
                resource: "bytes",
                requested,
                limit,
                ..
            }) if requested == expected_bytes && limit == expected_bytes - 1
        ));
        assert!(matches!(
            report.try_clone_with_budget(operation_limited_budget),
            Err(PidError::ResourceLimitExceeded {
                operation: "QuantizationReport::try_clone_with_budget",
                resource: "operations_hint",
                requested,
                limit,
                ..
            }) if requested == expected_operations && limit == expected_operations - 1
        ));
    }
}
