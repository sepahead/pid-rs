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
    pub bins_per_dimension: usize,
    /// `None` means `bins_per_dimension.pow(dimensions)` exceeds `u128`.
    pub nominal_joint_cardinality: Option<u128>,
    pub observed_joint_cardinality: usize,
    /// `None` when nominal cardinality is not representable as `u128`.
    pub empty_joint_cells: Option<u128>,
    pub low_count_joint_cells: usize,
    pub minimum_observed_cell_count: usize,
    pub maximum_observed_cell_count: usize,
    pub estimand_statement: &'static str,
}

impl QuantizationReport {
    /// Fallibly deep-copy report provenance and fitted edges under an aggregate budget.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        let edge_count = self.bin_edges.iter().try_fold(0usize, |total, column| {
            total
                .checked_add(column.len())
                .ok_or(PidError::SizeOverflow {
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
            .and_then(|value| value.checked_add(self.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "QuantizationReport::try_clone_with_budget",
            })?;
        budget.check(
            "QuantizationReport::try_clone_with_budget",
            ResourceEstimate {
                estimated_bytes,
                pairwise_distances: 0,
                operations_hint: edge_count as u128,
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
            nominal_joint_cardinality: self.nominal_joint_cardinality,
            observed_joint_cardinality: self.observed_joint_cardinality,
            empty_joint_cells: self.empty_joint_cells,
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
                operations_hint: edge_count as u128,
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
            .and_then(|value| value.checked_add(edge_count as u128))
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
                minimum = minimum.min(value);
                maximum = maximum.max(value);
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
                column_edges[0] = minimum;
                column_edges[bins] = maximum;
            }
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
        self.transform_with_report_with_cancellation(data, cancellation)
            .map(|result| result.matrix)
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
        let report_bytes = (edge_count as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(
                    (self.edges.len() as u128)
                        .checked_mul(std::mem::size_of::<Vec<f64>>() as u128)?,
                )
            })
            .and_then(|value| value.checked_add(self.config.scaling_description.len() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let log_rows = ceil_log2(data.nrows());
        let log_bins = ceil_log2(self.bins);
        let per_coordinate_work = 3u128
            .checked_add(log_rows as u128)
            .and_then(|value| value.checked_add(log_bins as u128))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        Ok(ResourceEstimate {
            estimated_bytes: label_bytes
                .checked_add(row_order_bytes)
                .and_then(|value| value.checked_add(report_bytes))
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
            pairwise_distances: 0,
            operations_hint: (output_len as u128)
                .checked_mul(per_coordinate_work)
                .and_then(|value| value.checked_add(edge_count as u128))
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
        let output_len = data
            .nrows()
            .checked_mul(data.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        self.config
            .resource_budget
            .check(OPERATION, self.transform_resource_estimate(data)?)?;
        let total_work = output_len
            .checked_mul(3)
            .and_then(|value| value.checked_add(data.nrows()))
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let mut completed_work = 0usize;
        check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
        let mut labels = try_vec_with_capacity(OPERATION, output_len, self.config.resource_budget)?;
        for row in 0..data.nrows() {
            for column in 0..data.ncols() {
                check_cancellation(cancellation, OPERATION, completed_work, total_work)?;
                labels.push(self.bin_value(column, data.row(row)[column])?);
                completed_work += 1;
            }
        }
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

    fn bin_value(&self, column: usize, value: f64) -> PidResult<usize> {
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
        let nominal_joint_cardinality = checked_pow_u128_with_cancellation(
            self.bins as u128,
            data.ncols(),
            cancellation,
            OPERATION,
            *completed_work,
            total_work,
        )?;
        let empty_joint_cells = nominal_joint_cardinality
            .and_then(|nominal| nominal.checked_sub(observed_joint_cardinality as u128));
        let bin_edges = try_clone_edges_with_cancellation(
            OPERATION,
            &self.edges,
            self.config.resource_budget,
            cancellation,
            *completed_work,
            total_work,
        )?;
        let scaling_description = try_string_copy(
            OPERATION,
            &self.config.scaling_description,
            self.config.resource_budget,
        )?;
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
            nominal_joint_cardinality,
            observed_joint_cardinality,
            empty_joint_cells,
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
        minimum * (1.0 - fraction) + maximum * fraction
    }
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

fn try_clone_edges_with_cancellation(
    operation: &'static str,
    edges: &[Vec<f64>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
    completed_work: usize,
    total_work: usize,
) -> PidResult<Vec<Vec<f64>>> {
    cancellation.check(operation, completed_work, total_work)?;
    let mut cloned = try_vec_with_capacity(operation, edges.len(), budget)?;
    for column in edges {
        let mut cloned_column = try_vec_with_capacity(operation, column.len(), budget)?;
        for chunk in column.chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, completed_work, total_work)?;
            cloned_column.extend_from_slice(chunk);
        }
        cloned.push(cloned_column);
    }
    cancellation.check(operation, completed_work, total_work)?;
    Ok(cloned)
}

#[cfg(test)]
mod tests {
    use super::{
        hash_categorical_matrix_with_cancellation, EqualWidthQuantizer, OutOfRangePolicy,
        QuantizerConfig,
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
}
