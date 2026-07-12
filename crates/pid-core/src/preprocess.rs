use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use crate::resource::{try_vec_filled, try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::{finite_mean, finite_mean_std_population};

fn zeroed_f64(len: usize, context: &'static str) -> PidResult<Vec<f64>> {
    try_vec_filled(context, len, 0.0, ResourceBudget::default())
}

fn zeroed_f64_with_budget(
    len: usize,
    context: &'static str,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    try_vec_filled(context, len, 0.0, budget)
}

fn symmetric_eigen_jacobi(
    mut matrix: Vec<f64>,
    n: usize,
    budget: ResourceBudget,
) -> PidResult<(Vec<f64>, Vec<f64>)> {
    const OPERATION: &str = "PcaProjector::fit symmetric eigendecomposition";
    const MAX_SWEEPS: usize = 64;
    debug_assert_eq!(matrix.len(), n * n);

    let vector_len = n.checked_mul(n).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let mut eigenvectors = try_vec_filled(OPERATION, vector_len, 0.0, budget)?;
    for index in 0..n {
        eigenvectors[index * n + index] = 1.0;
    }

    let diagonal_scale = (0..n)
        .map(|index| matrix[index * n + index].abs())
        .fold(0.0_f64, f64::max);
    if !diagonal_scale.is_finite() {
        return Err(PidError::NumericalInstability { context: OPERATION });
    }
    let tolerance = 128.0 * f64::EPSILON * diagonal_scale.max(1.0);

    let mut converged = n <= 1;
    for _ in 0..MAX_SWEEPS {
        let mut rotated = false;
        for p in 0..n {
            for q in (p + 1)..n {
                let pq = p * n + q;
                let apq = matrix[pq];
                if apq.abs() <= tolerance {
                    matrix[pq] = 0.0;
                    matrix[q * n + p] = 0.0;
                    continue;
                }
                rotated = true;
                let app = matrix[p * n + p];
                let aqq = matrix[q * n + q];
                let tau = (aqq - app) / (2.0 * apq);
                let sign = if tau >= 0.0 { 1.0 } else { -1.0 };
                let tangent = if tau.is_infinite() {
                    0.0
                } else {
                    sign / (tau.abs() + tau.hypot(1.0))
                };
                let cosine = 1.0 / tangent.hypot(1.0);
                let sine = tangent * cosine;
                if !tangent.is_finite() || !cosine.is_finite() || !sine.is_finite() {
                    return Err(PidError::NumericalInstability { context: OPERATION });
                }

                for k in 0..n {
                    if k == p || k == q {
                        continue;
                    }
                    let akp = matrix[k * n + p];
                    let akq = matrix[k * n + q];
                    let next_kp = cosine * akp - sine * akq;
                    let next_kq = sine * akp + cosine * akq;
                    matrix[k * n + p] = next_kp;
                    matrix[p * n + k] = next_kp;
                    matrix[k * n + q] = next_kq;
                    matrix[q * n + k] = next_kq;
                }
                matrix[p * n + p] = app - tangent * apq;
                matrix[q * n + q] = aqq + tangent * apq;
                matrix[pq] = 0.0;
                matrix[q * n + p] = 0.0;

                for k in 0..n {
                    let vkp = eigenvectors[k * n + p];
                    let vkq = eigenvectors[k * n + q];
                    eigenvectors[k * n + p] = cosine * vkp - sine * vkq;
                    eigenvectors[k * n + q] = sine * vkp + cosine * vkq;
                }
            }
        }
        if !rotated {
            converged = true;
            break;
        }
    }
    if !converged && (0..n).any(|p| ((p + 1)..n).any(|q| matrix[p * n + q].abs() > 8.0 * tolerance))
    {
        return Err(PidError::NumericalInstability {
            context: "PcaProjector::fit: bounded Jacobi eigensolver did not converge",
        });
    }

    let mut eigenvalues = try_vec_with_capacity(OPERATION, n, budget)?;
    for index in 0..n {
        let value = matrix[index * n + index];
        if !value.is_finite() {
            return Err(PidError::NumericalInstability { context: OPERATION });
        }
        eigenvalues.push(value);
    }
    Ok((eigenvalues, eigenvectors))
}

fn stable_centered_dot(
    row: &[f64],
    column_scales: &[f64],
    mean_scaled: &[f64],
    weights: &[f64],
    context: &'static str,
) -> PidResult<f64> {
    debug_assert_eq!(row.len(), column_scales.len());
    debug_assert_eq!(row.len(), mean_scaled.len());
    debug_assert_eq!(row.len(), weights.len());

    let term = |feature: usize| -> PidResult<Option<(f64, f64)>> {
        let weight = weights[feature];
        if weight == 0.0 {
            return Ok(None);
        }
        let reference_scale = row[feature].abs().max(column_scales[feature]);
        if reference_scale == 0.0 {
            return Ok(None);
        }
        let centered_unit = row[feature] / reference_scale
            - mean_scaled[feature] * (column_scales[feature] / reference_scale);
        if !centered_unit.is_finite() || !weight.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        if centered_unit == 0.0 {
            return Ok(None);
        }
        let log_magnitude = centered_unit.abs().ln() + reference_scale.ln() + weight.abs().ln();
        if !log_magnitude.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        Ok(Some((
            centered_unit.signum() * weight.signum(),
            log_magnitude,
        )))
    };

    let mut max_log_magnitude = f64::NEG_INFINITY;
    for feature in 0..row.len() {
        if let Some((_, log_magnitude)) = term(feature)? {
            max_log_magnitude = max_log_magnitude.max(log_magnitude);
        }
    }
    if !max_log_magnitude.is_finite() {
        return Ok(0.0);
    }

    let mut sum = 0.0_f64;
    let mut correction = 0.0_f64;
    for feature in 0..row.len() {
        let Some((sign, log_magnitude)) = term(feature)? else {
            continue;
        };
        let magnitude = (log_magnitude - max_log_magnitude).exp();
        if magnitude == 0.0 || !magnitude.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        let value = sign * magnitude;
        let next = sum + value;
        correction += if sum.abs() >= value.abs() {
            (sum - next) + value
        } else {
            (value - next) + sum
        };
        sum = next;
    }

    let normalized = sum + correction;
    if !normalized.is_finite() {
        return Err(PidError::NumericalInstability { context });
    }
    if normalized == 0.0 {
        return Ok(0.0);
    }
    let result_log_magnitude = max_log_magnitude + normalized.abs().ln();
    if result_log_magnitude > f64::MAX.ln() {
        return Err(PidError::NumericalInstability { context });
    }
    let result = result_log_magnitude.exp().copysign(normalized);
    if result.is_finite() {
        Ok(result)
    } else {
        Err(PidError::NumericalInstability { context })
    }
}

fn scaled_sum_update(scale: &mut f64, sum: &mut f64, correction: &mut f64, value: f64) -> bool {
    if !value.is_finite() {
        return false;
    }
    if value == 0.0 {
        return true;
    }

    let magnitude = value.abs();
    if magnitude > *scale {
        let ratio = if *scale == 0.0 {
            0.0
        } else {
            *scale / magnitude
        };
        if ratio == 0.0 && (*sum != 0.0 || *correction != 0.0) {
            // Rescaling would silently erase a term that could become relevant after later
            // cancellation. Reject instead of returning an order-dependent sum.
            return false;
        }
        *sum *= ratio;
        *correction *= ratio;
        *scale = magnitude;
    }

    let normalized = value / *scale;
    if normalized == 0.0 || !normalized.is_finite() {
        return false;
    }
    let next = *sum + normalized;
    *correction += if sum.abs() >= normalized.abs() {
        (*sum - next) + normalized
    } else {
        (normalized - next) + *sum
    };
    *sum = next;
    sum.is_finite() && correction.is_finite()
}

fn scaled_sum_finish(scale: f64, sum: f64, correction: f64) -> Option<f64> {
    let normalized = sum + correction;
    if !normalized.is_finite() {
        return None;
    }
    let value = scale * normalized;
    value.is_finite().then_some(value)
}

fn preprocessing_matrix_hash(matrix: MatRef<'_>) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"pid-rs-preprocessing-training-matrix-sha256-v1");
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    for value in matrix.as_slice() {
        digest.update(value.to_bits().to_le_bytes());
    }
    digest.finalize().into()
}

fn update_f64_slice_hash(digest: &mut Sha256, values: &[f64]) {
    digest.update((values.len() as u128).to_le_bytes());
    for value in values {
        digest.update(value.to_bits().to_le_bytes());
    }
}

fn standardizer_parameter_hash(
    mean: &[f64],
    column_scale: &[f64],
    mean_scaled: &[f64],
    std_scaled: &[f64],
    retained_columns: &[usize],
    policy: ConstantColumnPolicy,
) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"pid-rs-standardizer-parameters-sha256-v1");
    digest.update([match policy {
        ConstantColumnPolicy::Drop => 0,
        ConstantColumnPolicy::Error => 1,
        ConstantColumnPolicy::Zero => 2,
        ConstantColumnPolicy::LeaveCentered => 3,
    }]);
    update_f64_slice_hash(&mut digest, mean);
    update_f64_slice_hash(&mut digest, column_scale);
    update_f64_slice_hash(&mut digest, mean_scaled);
    update_f64_slice_hash(&mut digest, std_scaled);
    digest.update((retained_columns.len() as u128).to_le_bytes());
    for &column in retained_columns {
        digest.update((column as u128).to_le_bytes());
    }
    digest.finalize().into()
}

fn hash_projector_parameter_hash(
    in_dim: usize,
    out_dim: usize,
    seed: u64,
    index: &[usize],
    sign: &[f64],
) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"pid-rs-hash-projector-parameters-sha256-v1");
    digest.update((in_dim as u128).to_le_bytes());
    digest.update((out_dim as u128).to_le_bytes());
    digest.update(seed.to_le_bytes());
    digest.update((index.len() as u128).to_le_bytes());
    for &bucket in index {
        digest.update((bucket as u128).to_le_bytes());
    }
    update_f64_slice_hash(&mut digest, sign);
    digest.finalize().into()
}

fn pca_parameter_hash(
    in_dim: usize,
    out_dim: usize,
    mean: &[f64],
    column_scales: &[f64],
    mean_scaled: &[f64],
    components: &[f64],
) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(b"pid-rs-pca-projector-parameters-sha256-v1");
    digest.update((in_dim as u128).to_le_bytes());
    digest.update((out_dim as u128).to_le_bytes());
    update_f64_slice_hash(&mut digest, mean);
    update_f64_slice_hash(&mut digest, column_scales);
    update_f64_slice_hash(&mut digest, mean_scaled);
    update_f64_slice_hash(&mut digest, components);
    digest.finalize().into()
}

/// Explicit treatment of columns that were constant on the fitting rows.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum ConstantColumnPolicy {
    /// Omit constant columns from transformed output.
    Drop,
    /// Reject fitting when any column is constant.
    Error,
    /// Retain the column but emit exactly zero for every transformed row.
    Zero,
    /// Retain the column and subtract its training mean without scaling.
    ///
    /// Held-out deviations remain visible. This is the pre-1.0 behavior.
    LeaveCentered,
}

#[derive(Debug)]
pub struct Standardizer {
    mean: Vec<f64>,
    column_scale: Vec<f64>,
    mean_scaled: Vec<f64>,
    std_scaled: Vec<f64>,
    retained_columns: Vec<usize>,
    constant_column_policy: ConstantColumnPolicy,
    training_data_hash_sha256: [u8; 32],
    parameter_hash_sha256: [u8; 32],
}

impl Standardizer {
    /// Fit with an explicit constant-column policy.
    ///
    /// Continuous shared-exclusions values depend on source gauges, so callers should record this
    /// fitted transform and its hashes alongside every downstream continuous report.
    pub fn fit(x: MatRef<'_>, constant_column_policy: ConstantColumnPolicy) -> PidResult<Self> {
        Self::fit_with_budget(x, constant_column_policy, ResourceBudget::default())
    }

    /// Conservative peak state, scratch, and work estimate for fitting.
    pub fn fit_resource_estimate(x: MatRef<'_>) -> PidResult<ResourceEstimate> {
        let n = x.nrows() as u128;
        let d = x.ncols() as u128;
        let state_bytes = d
            .checked_mul(4)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .and_then(|value| {
                value.checked_add(d.checked_mul(std::mem::size_of::<usize>() as u128)?)
            })
            .ok_or(PidError::SizeOverflow {
                operation: "Standardizer::fit",
            })?;
        let scratch_bytes =
            n.checked_mul(std::mem::size_of::<f64>() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: "Standardizer::fit",
                })?;
        let operations_hint = n
            .checked_mul(d)
            .and_then(|value| value.checked_mul(4))
            .and_then(|value| value.checked_add(d))
            .ok_or(PidError::SizeOverflow {
                operation: "Standardizer::fit",
            })?;
        Ok(ResourceEstimate {
            estimated_bytes: state_bytes.checked_add(scratch_bytes).ok_or(
                PidError::SizeOverflow {
                    operation: "Standardizer::fit",
                },
            )?,
            pairwise_distances: 0,
            operations_hint,
        })
    }

    /// Fit after checking a caller-supplied aggregate resource ceiling.
    pub fn fit_with_budget(
        x: MatRef<'_>,
        constant_column_policy: ConstantColumnPolicy,
        budget: ResourceBudget,
    ) -> PidResult<Self> {
        let n = x.nrows();
        let d = x.ncols();
        if n == 0 || d == 0 {
            return Err(PidError::ShapeMismatch {
                context: "Standardizer::fit",
                expected_len: 1,
                actual_len: 0,
            });
        }

        // Scale each column before forming its moments. Variance itself can overflow even when
        // the standard deviation is representable (for example `[0, f64::MAX]`).
        budget.check("Standardizer::fit", Self::fit_resource_estimate(x)?)?;
        let mut mean = zeroed_f64_with_budget(d, "Standardizer::fit mean", budget)?;
        let mut column_scale = zeroed_f64_with_budget(d, "Standardizer::fit column scale", budget)?;
        let mut mean_scaled = zeroed_f64_with_budget(d, "Standardizer::fit scaled mean", budget)?;
        let mut std_scaled =
            zeroed_f64_with_budget(d, "Standardizer::fit scaled standard deviation", budget)?;
        let mut column = zeroed_f64_with_budget(n, "Standardizer::fit column scratch", budget)?;
        for j in 0..d {
            let scale = (0..n).map(|i| x.row(i)[j].abs()).fold(0.0_f64, f64::max);
            column_scale[j] = scale;
            if scale == 0.0 {
                continue;
            }

            for (i, value) in column.iter_mut().enumerate() {
                *value = x.row(i)[j] / scale;
            }
            let (scaled_mean, scaled_std) = finite_mean_std_population(
                &column,
                "Standardizer::fit: non-finite scaled column moments",
            )?;
            mean_scaled[j] = scaled_mean;
            std_scaled[j] = scaled_std;
            mean[j] = scaled_mean * scale;
        }

        let mut retained_columns =
            try_vec_with_capacity("Standardizer::fit retained columns", d, budget)?;
        for (column_index, &scaled_std) in std_scaled.iter().enumerate() {
            let is_constant = scaled_std == 0.0;
            if is_constant && constant_column_policy == ConstantColumnPolicy::Error {
                return Err(PidError::InvalidConfig {
                    context: "Standardizer::fit",
                    message: "a training column is constant under ConstantColumnPolicy::Error",
                });
            }
            if !is_constant || constant_column_policy != ConstantColumnPolicy::Drop {
                retained_columns.push(column_index);
            }
        }
        let training_data_hash_sha256 = preprocessing_matrix_hash(x);
        let parameter_hash_sha256 = standardizer_parameter_hash(
            &mean,
            &column_scale,
            &mean_scaled,
            &std_scaled,
            &retained_columns,
            constant_column_policy,
        );

        Ok(Self {
            mean,
            column_scale,
            mean_scaled,
            std_scaled,
            retained_columns,
            constant_column_policy,
            training_data_hash_sha256,
            parameter_hash_sha256,
        })
    }

    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        self.transform_with_budget(x, ResourceBudget::default())
    }

    /// Output allocation and element-work estimate for a fitted transformation.
    pub fn transform_resource_estimate(&self, x: MatRef<'_>) -> PidResult<ResourceEstimate> {
        if x.ncols() != self.mean.len() {
            return Err(PidError::ShapeMismatch {
                context: "Standardizer::transform",
                expected_len: self.mean.len(),
                actual_len: x.ncols(),
            });
        }
        let output_len =
            x.nrows()
                .checked_mul(self.retained_columns.len())
                .ok_or(PidError::SizeOverflow {
                    operation: "Standardizer::transform",
                })?;
        ResourceEstimate::contiguous::<f64>("Standardizer::transform", output_len)
    }

    /// Transform after checking a caller-supplied output-allocation ceiling.
    pub fn transform_with_budget(
        &self,
        x: MatRef<'_>,
        budget: ResourceBudget,
    ) -> PidResult<MatOwned> {
        let estimate = self.transform_resource_estimate(x)?;
        budget.check("Standardizer::transform", estimate)?;
        let n = x.nrows();
        let d = self.retained_columns.len();
        let output_len = n.checked_mul(d).ok_or(PidError::SizeOverflow {
            operation: "Standardizer::transform",
        })?;
        let mut out = try_vec_with_capacity("Standardizer::transform", output_len, budget)?;
        for i in 0..n {
            for &j in &self.retained_columns {
                let v = x.row(i)[j];
                let standardized = if self.std_scaled[j] > 0.0 {
                    // Standardize entirely in scaled coordinates. This avoids materializing an
                    // underflowed standard deviation or its overflowing reciprocal.
                    (v / self.column_scale[j] - self.mean_scaled[j]) / self.std_scaled[j]
                } else {
                    match self.constant_column_policy {
                        ConstantColumnPolicy::Zero => 0.0,
                        ConstantColumnPolicy::LeaveCentered => v - self.mean[j],
                        // `Drop` excludes the column and `Error` rejects it during fit.
                        ConstantColumnPolicy::Drop | ConstantColumnPolicy::Error => {
                            return Err(PidError::InvalidConfig {
                                context: "Standardizer::transform",
                                message: "internal constant-column policy invariant was violated",
                            });
                        }
                    }
                };
                if !standardized.is_finite() {
                    return Err(PidError::NumericalInstability {
                        context: "Standardizer::transform output",
                    });
                }
                out.push(standardized);
            }
        }
        MatOwned::new(out, n, d)
    }

    pub fn fit_transform(
        x: MatRef<'_>,
        constant_column_policy: ConstantColumnPolicy,
    ) -> PidResult<(MatOwned, Self)> {
        Self::fit_transform_with_budget(x, constant_column_policy, ResourceBudget::default())
    }

    /// Conservative aggregate peak for the retained fitted state plus transformed output.
    pub fn fit_transform_resource_estimate(x: MatRef<'_>) -> PidResult<ResourceEstimate> {
        let fit = Self::fit_resource_estimate(x)?;
        let state_bytes = (x.ncols() as u128)
            .checked_mul(4)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .and_then(|value| {
                value.checked_add(
                    (x.ncols() as u128).checked_mul(std::mem::size_of::<usize>() as u128)?,
                )
            })
            .ok_or(PidError::SizeOverflow {
                operation: "Standardizer::fit_transform",
            })?;
        let output_bytes = (x.nrows() as u128)
            .checked_mul(x.ncols() as u128)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "Standardizer::fit_transform",
            })?;
        Ok(ResourceEstimate {
            estimated_bytes: fit
                .estimated_bytes
                .max(
                    state_bytes
                        .checked_add(output_bytes)
                        .ok_or(PidError::SizeOverflow {
                            operation: "Standardizer::fit_transform",
                        })?,
                ),
            pairwise_distances: 0,
            operations_hint: fit
                .operations_hint
                .checked_add((x.nrows() as u128).checked_mul(x.ncols() as u128).ok_or(
                    PidError::SizeOverflow {
                        operation: "Standardizer::fit_transform",
                    },
                )?)
                .ok_or(PidError::SizeOverflow {
                    operation: "Standardizer::fit_transform",
                })?,
        })
    }

    /// Fit and transform after checking the simultaneous state/output peak.
    pub fn fit_transform_with_budget(
        x: MatRef<'_>,
        constant_column_policy: ConstantColumnPolicy,
        budget: ResourceBudget,
    ) -> PidResult<(MatOwned, Self)> {
        budget.check(
            "Standardizer::fit_transform",
            Self::fit_transform_resource_estimate(x)?,
        )?;
        let standardizer = Self::fit_with_budget(x, constant_column_policy, budget)?;
        let transformed = standardizer.transform_with_budget(x, budget)?;
        Ok((transformed, standardizer))
    }

    pub fn mean(&self) -> &[f64] {
        &self.mean
    }

    pub fn input_dim(&self) -> usize {
        self.mean.len()
    }

    pub fn output_dim(&self) -> usize {
        self.retained_columns.len()
    }

    pub fn retained_columns(&self) -> &[usize] {
        &self.retained_columns
    }

    pub fn constant_column_policy(&self) -> ConstantColumnPolicy {
        self.constant_column_policy
    }

    pub fn training_data_hash_sha256(&self) -> [u8; 32] {
        self.training_data_hash_sha256
    }

    pub fn parameter_hash_sha256(&self) -> [u8; 32] {
        self.parameter_hash_sha256
    }

    /// Derive the original-unit reciprocal standard deviations.
    ///
    /// Constant columns return `1`, matching [`transform`](Self::transform)'s centered-but-unscaled
    /// convention. A nonconstant subnormal column may still be transformed through the private
    /// scaled representation even when its standalone original-unit reciprocal is not representable;
    /// this accessor returns [`PidError::NumericalInstability`] in that case.
    pub fn inv_std(&self) -> PidResult<Vec<f64>> {
        let mut inverse_standard_deviations = try_vec_with_capacity(
            "Standardizer::inv_std",
            self.column_scale.len(),
            ResourceBudget::default(),
        )?;
        for (&scale, &scaled_std) in self.column_scale.iter().zip(&self.std_scaled) {
            if scaled_std == 0.0 {
                inverse_standard_deviations.push(1.0);
                continue;
            }
            let std = scale * scaled_std;
            let inverse = 1.0 / std;
            if std > 0.0 && inverse.is_finite() {
                inverse_standard_deviations.push(inverse);
            } else {
                return Err(PidError::NumericalInstability {
                    context:
                        "Standardizer::inv_std: reciprocal standard deviation is not representable",
                });
            }
        }
        Ok(inverse_standard_deviations)
    }
}

#[cfg(test)]
mod standardizer_tests {
    use super::*;

    #[test]
    fn constant_max_column_has_finite_parameters_and_zero_scores() {
        let data = [f64::MAX; 4];
        let x = MatRef::new(&data, 4, 1).unwrap();

        let (scores, standardizer) =
            Standardizer::fit_transform(x, ConstantColumnPolicy::Zero).unwrap();

        assert_eq!(standardizer.mean(), &[f64::MAX]);
        assert_eq!(standardizer.inv_std().unwrap(), vec![1.0]);
        assert!(scores.as_ref().row(0)[0] == 0.0);
        assert!(scores.as_ref().row(1)[0] == 0.0);
        assert!(scores.as_ref().row(2)[0] == 0.0);
        assert!(scores.as_ref().row(3)[0] == 0.0);
    }

    #[test]
    fn extreme_column_with_overflowing_raw_variance_standardizes_exactly() {
        let data = [0.0, f64::MAX];
        let x = MatRef::new(&data, 2, 1).unwrap();

        let (scores, standardizer) =
            Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

        assert_eq!(standardizer.mean(), &[f64::MAX * 0.5]);
        assert!((scores.as_ref().row(0)[0] + 1.0).abs() < 2.0 * f64::EPSILON);
        assert!((scores.as_ref().row(1)[0] - 1.0).abs() < 2.0 * f64::EPSILON);
    }

    #[test]
    fn tiny_scaled_column_retains_unit_standardized_geometry() {
        let data = [0.0, 1.0e-200, 2.0e-200, 3.0e-200];
        let x = MatRef::new(&data, 4, 1).unwrap();

        let (scores, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

        let values: Vec<f64> = (0..4).map(|i| scores.as_ref().row(i)[0]).collect();
        assert!((values[0] + 1.341_640_786_499_873_8).abs() < 1e-14);
        assert!((values[3] - 1.341_640_786_499_873_8).abs() < 1e-14);
    }

    #[test]
    fn asymmetric_opposite_extremes_do_not_overflow_centering() {
        let data = [-f64::MAX, f64::MAX, f64::MAX];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let (scores, _) = Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

        assert!((scores.as_ref().row(0)[0] + 2.0_f64.sqrt()).abs() < 1e-14);
        assert!((scores.as_ref().row(1)[0] - 1.0 / 2.0_f64.sqrt()).abs() < 1e-14);
        assert!((scores.as_ref().row(2)[0] - 1.0 / 2.0_f64.sqrt()).abs() < 1e-14);
    }

    #[test]
    fn subnormal_standard_deviation_still_produces_unit_scores() {
        let smallest = f64::from_bits(1);
        let data = [0.0, 2.0 * smallest];
        let x = MatRef::new(&data, 2, 1).unwrap();

        let (scores, standardizer) =
            Standardizer::fit_transform(x, ConstantColumnPolicy::Error).unwrap();

        assert_eq!(standardizer.mean(), &[smallest]);
        assert!(matches!(
            standardizer.inv_std(),
            Err(PidError::NumericalInstability { .. })
        ));
        assert_eq!(scores.as_ref().row(0)[0], -1.0);
        assert_eq!(scores.as_ref().row(1)[0], 1.0);
    }
}

/// Deterministic dimensionality reduction via feature hashing / CountSketch-style projection.
///
/// This is a cheap alternative to PCA for high-dimensional embeddings when we mainly need
/// to avoid the worst kNN distance concentration regimes. Complexity: O(n * d_in).
///
/// Notes:
/// - This transform is *not* invertible. Always record `{seed, in_dim, out_dim}` with results.
/// - Apply the same projection strategy independently to each variable (S1/S2/T), but do not
///   fit a joint transform on concatenated variables.
#[derive(Debug)]
pub struct HashProjector {
    in_dim: usize,
    out_dim: usize,
    seed: u64,
    index: Vec<usize>,
    sign: Vec<f64>,
    parameter_hash_sha256: [u8; 32],
}

impl HashProjector {
    pub fn new(in_dim: usize, out_dim: usize, seed: u64) -> PidResult<Self> {
        if in_dim == 0 {
            return Err(PidError::InvalidConfig {
                context: "HashProjector::new",
                message: "in_dim must be >= 1",
            });
        }
        if out_dim == 0 {
            return Err(PidError::InvalidConfig {
                context: "HashProjector::new",
                message: "out_dim must be >= 1",
            });
        }

        let total_state_bytes = (in_dim as u128)
            .checked_mul((std::mem::size_of::<usize>() + std::mem::size_of::<f64>()) as u128)
            .ok_or(PidError::SizeOverflow {
                operation: "HashProjector::new",
            })?;
        ResourceBudget::default().check(
            "HashProjector::new",
            ResourceEstimate {
                estimated_bytes: total_state_bytes,
                pairwise_distances: 0,
                operations_hint: in_dim as u128,
            },
        )?;
        let mut index = try_vec_with_capacity(
            "HashProjector::new index",
            in_dim,
            ResourceBudget::default(),
        )?;
        let mut sign =
            try_vec_with_capacity("HashProjector::new sign", in_dim, ResourceBudget::default())?;
        for j in 0..in_dim {
            let h = splitmix64_hash(seed, j as u64);
            // CountSketch (Charikar–Chen–Farach-Colton 2002) requires the ±1 sign hash to be
            // independent of the bucket hash — that independence is what makes
            // E[⟨Px, Py⟩] = ⟨x, y⟩. Deriving both from one value `h` breaks this: for even
            // `out_dim`, `h & 1` equals the parity of `h % out_dim`, so the sign becomes a
            // deterministic function of the bucket and colliding features add constructively
            // (the sketch degenerates to unsigned feature hashing). Use a second, salted
            // splitmix stream for the sign.
            let h_sign = splitmix64_hash(seed ^ 0x5EED_51D3_5EED_51D3, j as u64);
            // Reduce modulo `out_dim` in u64 BEFORE narrowing to usize. `h as usize`
            // truncates to 32 bits on 32-bit targets, which would make the documented,
            // seed-reproducible bucketing platform-dependent.
            index.push((h % out_dim as u64) as usize);
            sign.push(if (h_sign & 1) == 0 { 1.0 } else { -1.0 });
        }

        let parameter_hash_sha256 =
            hash_projector_parameter_hash(in_dim, out_dim, seed, &index, &sign);
        Ok(Self {
            in_dim,
            out_dim,
            seed,
            index,
            sign,
            parameter_hash_sha256,
        })
    }

    pub fn in_dim(&self) -> usize {
        self.in_dim
    }

    pub fn out_dim(&self) -> usize {
        self.out_dim
    }

    pub fn seed(&self) -> u64 {
        self.seed
    }

    pub fn parameter_hash_sha256(&self) -> [u8; 32] {
        self.parameter_hash_sha256
    }

    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        self.transform_with_budget(x, ResourceBudget::default())
    }

    /// Preflight output, scratch memory, and projection work for [`Self::transform`].
    pub fn transform_resource_estimate(&self, x: MatRef<'_>) -> PidResult<ResourceEstimate> {
        let output_elements = x
            .nrows()
            .checked_mul(self.out_dim)
            .ok_or(PidError::SizeOverflow {
                operation: "HashProjector::transform",
            })? as u128;
        let scratch_elements =
            (self.out_dim as u128)
                .checked_mul(2)
                .ok_or(PidError::SizeOverflow {
                    operation: "HashProjector::transform",
                })?;
        let estimated_bytes = output_elements
            .checked_add(scratch_elements)
            .and_then(|value| value.checked_mul(std::mem::size_of::<f64>() as u128))
            .ok_or(PidError::SizeOverflow {
                operation: "HashProjector::transform",
            })?;
        let operations_hint = (x.nrows() as u128)
            .checked_mul(self.in_dim as u128)
            .and_then(|value| {
                value.checked_add((x.nrows() as u128).checked_mul(self.out_dim as u128)?)
            })
            .ok_or(PidError::SizeOverflow {
                operation: "HashProjector::transform",
            })?;
        Ok(ResourceEstimate {
            estimated_bytes,
            pairwise_distances: 0,
            operations_hint,
        })
    }

    /// Transform after enforcing a caller-supplied aggregate resource ceiling.
    pub fn transform_with_budget(
        &self,
        x: MatRef<'_>,
        budget: ResourceBudget,
    ) -> PidResult<MatOwned> {
        if x.ncols() != self.in_dim {
            return Err(PidError::ShapeMismatch {
                context: "HashProjector::transform",
                expected_len: self.in_dim,
                actual_len: x.ncols(),
            });
        }
        budget.check(
            "HashProjector::transform",
            self.transform_resource_estimate(x)?,
        )?;

        let n = x.nrows();
        let dout = self.out_dim;

        let out_len = n.checked_mul(dout).ok_or(PidError::SizeOverflow {
            operation: "HashProjector::transform",
        })?;
        let mut out = try_vec_filled("HashProjector::transform output", out_len, 0.0, budget)?;
        let mut bucket_scales =
            try_vec_filled("HashProjector::transform scales", dout, 0.0, budget)?;
        let mut bucket_corrections =
            try_vec_filled("HashProjector::transform corrections", dout, 0.0, budget)?;
        for i in 0..n {
            let xi = x.row(i);
            let row_out = &mut out[i * dout..(i + 1) * dout];
            bucket_scales.fill(0.0);
            bucket_corrections.fill(0.0);
            for (j, &value) in xi.iter().enumerate() {
                let bucket = self.index[j];
                if !scaled_sum_update(
                    &mut bucket_scales[bucket],
                    &mut row_out[bucket],
                    &mut bucket_corrections[bucket],
                    self.sign[j] * value,
                ) {
                    return Err(PidError::NumericalInstability {
                        context: "HashProjector::transform: bucket dynamic range exceeds finite f64 representation",
                    });
                }
            }
            for bucket in 0..dout {
                row_out[bucket] = scaled_sum_finish(
                    bucket_scales[bucket],
                    row_out[bucket],
                    bucket_corrections[bucket],
                )
                .ok_or(PidError::NumericalInstability {
                    context: "HashProjector::transform: bucket sum is not representable",
                })?;
            }
        }

        MatOwned::new(out, n, dout)
    }
}

#[cfg(test)]
mod hash_projector_tests {
    use super::*;

    #[test]
    fn oversized_input_dimension_returns_error_instead_of_panicking() {
        assert!(matches!(
            HashProjector::new(usize::MAX, 1, 7),
            Err(PidError::ResourceLimitExceeded { .. } | PidError::SizeOverflow { .. })
        ));
    }
}

/// Deterministic PCA-based projection (baseline implementation).
///
/// This fits PCA on a single variable `X` (n×d) and projects to `out_dim` dimensions.
///
/// Notes:
/// - This transform is *not* invertible. Always record `{in_dim, out_dim}` (and how it was fit)
///   with results.
/// - Apply PCA independently to each variable (S1/S2/T); do *not* fit PCA on concatenated
///   variables.
/// - Uses a bounded, preallocated cyclic-Jacobi eigendecomposition on the `n×n` Gram matrix
///   (`X_c X_c^T`). This is a correctness-first baseline and is most appropriate when `n` is
///   modest (which is already the regime for this repo's exact kNN backend).
#[derive(Debug)]
pub struct PcaProjector {
    in_dim: usize,
    out_dim: usize,
    mean: Vec<f64>,
    column_scales: Vec<f64>,
    mean_scaled: Vec<f64>,
    // Row-major (out_dim × in_dim): each component is a length-in_dim vector.
    components: Vec<f64>,
    training_data_hash_sha256: [u8; 32],
    parameter_hash_sha256: [u8; 32],
}

impl PcaProjector {
    /// Conservative peak-memory and work estimate for [`Self::fit`].
    ///
    /// The estimate includes centered input storage, the Gram matrix, eigensolver input/output
    /// and scratch allowance, fitted state, and cubic symmetric-eigendecomposition work.
    pub fn fit_resource_estimate(x: MatRef<'_>, out_dim: usize) -> PidResult<ResourceEstimate> {
        let n = x.nrows();
        let d = x.ncols();
        if n < 2 || d == 0 || out_dim == 0 || out_dim > d.min(n.saturating_sub(1)) {
            return Err(PidError::InvalidConfig {
                context: "PcaProjector::fit_resource_estimate",
                message: "require n >= 2, d >= 1, and 1 <= out_dim <= min(d, n-1)",
            });
        }

        let n128 = n as u128;
        let d128 = d as u128;
        let out128 = out_dim as u128;
        let centered = n128.checked_mul(d128).ok_or(PidError::SizeOverflow {
            operation: "PcaProjector::fit_resource_estimate",
        })?;
        let square = n128.checked_mul(n128).ok_or(PidError::SizeOverflow {
            operation: "PcaProjector::fit_resource_estimate",
        })?;
        let components = out128.checked_mul(d128).ok_or(PidError::SizeOverflow {
            operation: "PcaProjector::fit_resource_estimate",
        })?;
        let f64_elements = centered
            .checked_add(square.checked_mul(4).ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?)
            .and_then(|value| value.checked_add(components))
            .and_then(|value| value.checked_add(d128.checked_mul(3)?))
            .and_then(|value| value.checked_add(n128.checked_mul(3)?))
            .ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?;
        let estimated_bytes = f64_elements
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .and_then(|value| {
                value.checked_add(n128.checked_mul(std::mem::size_of::<usize>() as u128)?)
            })
            .ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?;
        let gram_entries = n128
            .checked_mul(n128.checked_add(1).ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?)
            .and_then(|value| value.checked_div(2))
            .ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?;
        let operations_hint = gram_entries
            .checked_mul(d128)
            .and_then(|value| value.checked_add(n128.checked_mul(square)?.checked_mul(64)?))
            .and_then(|value| value.checked_add(out128.checked_mul(n128)?.checked_mul(d128)?))
            .ok_or(PidError::SizeOverflow {
                operation: "PcaProjector::fit_resource_estimate",
            })?;

        Ok(ResourceEstimate {
            estimated_bytes,
            pairwise_distances: gram_entries,
            operations_hint,
        })
    }

    pub fn fit(x: MatRef<'_>, out_dim: usize) -> PidResult<Self> {
        Self::fit_with_budget(x, out_dim, ResourceBudget::default())
    }

    /// Fit PCA after checking a caller-supplied peak-memory and work budget.
    pub fn fit_with_budget(
        x: MatRef<'_>,
        out_dim: usize,
        resource_budget: ResourceBudget,
    ) -> PidResult<Self> {
        let n = x.nrows();
        let d = x.ncols();
        if n < 2 || d == 0 {
            return Err(PidError::InvalidConfig {
                context: "PcaProjector::fit",
                message: "require n >= 2 and d >= 1",
            });
        }
        if out_dim == 0 {
            return Err(PidError::InvalidConfig {
                context: "PcaProjector::fit",
                message: "out_dim must be >= 1",
            });
        }
        let max_out = d.min(n.saturating_sub(1));
        if out_dim > max_out {
            return Err(PidError::InvalidConfig {
                context: "PcaProjector::fit",
                message: "out_dim must be <= min(d, n-1) after centering",
            });
        }
        resource_budget.check(
            "PcaProjector::fit",
            Self::fit_resource_estimate(x, out_dim)?,
        )?;

        // 1) Center each column in its own scaled coordinates. A single input-wide scale would
        // erase a tiny varying feature merely because another feature has a huge constant offset.
        // Per-column scaling removes offsets safely; a later global log scale restores the correct
        // relative centered magnitudes for PCA.
        let mut mean = zeroed_f64(d, "PcaProjector::fit mean")?;
        let mut mean_scaled = zeroed_f64(d, "PcaProjector::fit scaled mean")?;
        let mut column_scales = zeroed_f64(d, "PcaProjector::fit column scales")?;
        let mut column = zeroed_f64(n, "PcaProjector::fit column scratch")?;
        for j in 0..d {
            let column_scale = (0..n).map(|i| x.row(i)[j].abs()).fold(0.0_f64, f64::max);
            column_scales[j] = column_scale;
            if column_scale == 0.0 {
                continue;
            }
            for (i, value) in column.iter_mut().enumerate() {
                *value = x.row(i)[j] / column_scale;
            }
            mean_scaled[j] =
                finite_mean(&column, "PcaProjector::fit: scaled column mean overflow")?;
            mean[j] = mean_scaled[j] * column_scale;
        }

        let mut max_centered_log = f64::NEG_INFINITY;
        for i in 0..n {
            for (j, value) in x.row(i).iter().enumerate() {
                if column_scales[j] == 0.0 {
                    continue;
                }
                let centered_scaled = value / column_scales[j] - mean_scaled[j];
                if centered_scaled != 0.0 {
                    max_centered_log =
                        max_centered_log.max(centered_scaled.abs().ln() + column_scales[j].ln());
                }
            }
        }
        if !max_centered_log.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "PcaProjector::fit: all centered values are zero",
            });
        }

        let centered_len = n.checked_mul(d).ok_or(PidError::InvalidConfig {
            context: "PcaProjector::fit",
            message: "centered matrix size overflow",
        })?;
        let mut centered = zeroed_f64(centered_len, "PcaProjector::fit")?;
        for i in 0..n {
            for j in 0..d {
                let scale = column_scales[j];
                if scale == 0.0 {
                    continue;
                }
                let centered_scaled = x.row(i)[j] / scale - mean_scaled[j];
                if centered_scaled != 0.0 {
                    let normalized_magnitude =
                        (centered_scaled.abs().ln() + scale.ln() - max_centered_log).exp();
                    if normalized_magnitude == 0.0 || !normalized_magnitude.is_finite() {
                        return Err(PidError::NumericalInstability {
                            context: "PcaProjector::fit: centered feature dynamic range exceeds finite f64 representation",
                        });
                    }
                    centered[i * d + j] = centered_scaled.signum() * normalized_magnitude;
                }
            }
        }

        // 2) Scaled Gram matrix G = X_c X_c^T (n×n).
        let gram_len = n.checked_mul(n).ok_or(PidError::InvalidConfig {
            context: "PcaProjector::fit",
            message: "Gram matrix size overflow",
        })?;
        let mut gram = zeroed_f64(gram_len, "PcaProjector::fit")?;
        for i in 0..n {
            let xi = &centered[i * d..(i + 1) * d];
            for j in 0..=i {
                let xj = &centered[j * d..(j + 1) * d];
                let mut dot = 0.0;
                for k in 0..d {
                    dot += xi[k] * xj[k];
                }
                gram[i * n + j] = dot;
                gram[j * n + i] = dot;
            }
        }

        // The common scaling above bounds individual centered coordinates, but retain an explicit
        // finiteness gate before handing the accumulated Gram matrix to the eigensolver.
        if gram.iter().any(|v| !v.is_finite()) {
            return Err(PidError::NumericalInstability {
                context: "PcaProjector::fit: non-finite Gram matrix (input magnitude overflow)",
            });
        }

        // 3) Eigendecompose G (symmetric PSD) with a bounded cyclic Jacobi solver whose dynamic
        // storage was allocated fallibly above. This keeps the public allocation-error contract
        // intact instead of delegating externally sized hidden allocations to a library solver.
        let (eigvals, eigvecs) = symmetric_eigen_jacobi(gram, n, resource_budget)?;

        // Sort eigenpairs by decreasing eigenvalue. `total_cmp` is a total order (never `None`),
        // so the sort cannot panic regardless of the eigenvalues.
        let mut order = try_vec_with_capacity(
            "PcaProjector::fit eigenvalue order",
            n,
            ResourceBudget::default(),
        )?;
        order.extend(0..n);
        order.sort_unstable_by(|&a, &b| eigvals[b].total_cmp(&eigvals[a]).then_with(|| a.cmp(&b)));

        // Rank-aware noise floor: trailing eigenvalues of a collinear/rank-deficient Gram are
        // ~`ε·λ_max` but strictly positive, and `inv_sigma = 1/√λ` would amplify that rounding
        // noise into a garbage "component". Reject any requested component whose eigenvalue sits
        // at or below the floor (this also rejects all-constant data, whose λ_max is 0).
        let lambda_max = eigvals[order[0]];
        let eig_floor = (n as f64) * f64::EPSILON * lambda_max.max(0.0);

        // Truncating inside a repeated eigenspace makes the chosen coordinates depend on row
        // order and eigensolver details. Reject that non-identifiable projection unless the full
        // tied subspace is retained.
        if out_dim < order.len() {
            let lambda_kept = eigvals[order[out_dim - 1]];
            let lambda_next = eigvals[order[out_dim]];
            let gap_tolerance = 64.0 * (n.max(d) as f64) * f64::EPSILON * lambda_max.max(0.0);
            if lambda_next > eig_floor && lambda_kept - lambda_next <= gap_tolerance {
                return Err(PidError::NumericalInstability {
                    context: "PcaProjector::fit: truncation splits a numerically tied eigenspace; retain the full tied subspace",
                });
            }
        }

        // 4) Build the top `out_dim` right-singular vectors / PCA components:
        // V_k = X_c^T U_k Σ_k^{-1}, where G = U Σ^2 U^T and Σ = diag(sqrt(eigvals)).
        let component_len = out_dim.checked_mul(d).ok_or(PidError::InvalidConfig {
            context: "PcaProjector::fit",
            message: "component matrix size overflow",
        })?;
        let mut components = zeroed_f64(component_len, "PcaProjector::fit")?;
        for comp in 0..out_dim {
            let idx = order[comp];
            let lambda = eigvals[idx];
            if !lambda.is_finite() || lambda <= eig_floor {
                return Err(PidError::NumericalInstability {
                    context: "PcaProjector::fit: requested component is in the numerical null space (eigenvalue at/below the noise floor); reduce out_dim",
                });
            }
            let inv_sigma = 1.0 / lambda.sqrt();
            for feat in 0..d {
                let mut acc = 0.0;
                for i in 0..n {
                    // Eigenvectors are stored row-major with eigenvectors in columns.
                    let u_i = eigvecs[i * n + idx];
                    acc += centered[i * d + feat] * u_i;
                }
                components[comp * d + feat] = acc * inv_sigma;
            }
        }

        let training_data_hash_sha256 = preprocessing_matrix_hash(x);
        let parameter_hash_sha256 =
            pca_parameter_hash(d, out_dim, &mean, &column_scales, &mean_scaled, &components);
        Ok(Self {
            in_dim: d,
            out_dim,
            mean,
            column_scales,
            mean_scaled,
            components,
            training_data_hash_sha256,
            parameter_hash_sha256,
        })
    }

    pub fn in_dim(&self) -> usize {
        self.in_dim
    }

    pub fn out_dim(&self) -> usize {
        self.out_dim
    }

    pub fn mean(&self) -> &[f64] {
        &self.mean
    }

    pub fn components(&self) -> &[f64] {
        &self.components
    }

    pub fn training_data_hash_sha256(&self) -> [u8; 32] {
        self.training_data_hash_sha256
    }

    pub fn parameter_hash_sha256(&self) -> [u8; 32] {
        self.parameter_hash_sha256
    }

    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        if x.ncols() != self.in_dim {
            return Err(PidError::ShapeMismatch {
                context: "PcaProjector::transform",
                expected_len: self.in_dim,
                actual_len: x.ncols(),
            });
        }
        let n = x.nrows();
        let d = self.in_dim;
        let k = self.out_dim;

        let out_len = n.checked_mul(k).ok_or(PidError::InvalidConfig {
            context: "PcaProjector::transform",
            message: "output size overflow",
        })?;
        let mut out = zeroed_f64(out_len, "PcaProjector::transform")?;
        for i in 0..n {
            let xi = x.row(i);
            let row_out = &mut out[i * k..(i + 1) * k];
            for (comp, outv) in row_out.iter_mut().enumerate() {
                let w = &self.components[comp * d..(comp + 1) * d];
                *outv = stable_centered_dot(
                    xi,
                    &self.column_scales,
                    &self.mean_scaled,
                    w,
                    "PcaProjector::transform: centered component dynamic range exceeds finite f64 representation",
                )?;
            }
        }

        MatOwned::new(out, n, k)
    }

    pub fn fit_transform(x: MatRef<'_>, out_dim: usize) -> PidResult<(MatOwned, Self)> {
        let p = Self::fit(x, out_dim)?;
        let y = p.transform(x)?;
        Ok((y, p))
    }
}

/// Add seeded i.i.d. Gaussian observation noise.
///
/// This transformation changes the estimated distribution; it is not a generic repair for tied
/// kNN data. Use it only when Gaussian observation noise is part of the declared model or in a
/// reported noise-scale sensitivity analysis. Otherwise select a discrete, quantized, or
/// mixed-support estimator whose sampling contract matches the data.
#[derive(Debug, Clone)]
#[cfg(feature = "experimental-pipelines")]
pub struct Jitter {
    std: f64,
    seed: u64,
}

#[cfg(feature = "experimental-pipelines")]
impl Jitter {
    pub fn new(std: f64, seed: u64) -> PidResult<Self> {
        if !std.is_finite() || std < 0.0 {
            return Err(PidError::InvalidConfig {
                context: "Jitter::new",
                message: "std must be finite and >= 0",
            });
        }
        Ok(Self { std, seed })
    }

    pub fn std(&self) -> f64 {
        self.std
    }

    pub fn apply(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        let n = x.nrows();
        let d = x.ncols();
        let mut rng = SplitMix64::new(self.seed);

        let output_len = n.checked_mul(d).ok_or(PidError::SizeOverflow {
            operation: "Jitter::apply",
        })?;
        let mut out =
            try_vec_with_capacity("Jitter::apply", output_len, ResourceBudget::default())?;
        for i in 0..n {
            for &v in x.row(i) {
                out.push(v + self.std * rng.normal());
            }
        }
        MatOwned::new(out, n, d)
    }
}

#[derive(Clone)]
pub(crate) struct SplitMix64 {
    state: u64,
}

impl SplitMix64 {
    pub(crate) fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    pub(crate) fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E37_79B9_7F4A_7C15);
        splitmix64_mix(self.state)
    }

    #[cfg(feature = "experimental-pipelines")]
    fn next_f64(&mut self) -> f64 {
        // 53 bits -> [0,1)
        let u = self.next_u64() >> 11;
        (u as f64) * (1.0 / ((1u64 << 53) as f64))
    }

    #[cfg(feature = "experimental-pipelines")]
    pub(crate) fn normal(&mut self) -> f64 {
        // Box–Muller requires an open lower endpoint. Redraw the single zero code instead of
        // clamping an entire tail interval and thereby truncating the Gaussian distribution.
        let u1 = loop {
            let draw = self.next_f64();
            if draw > 0.0 {
                break draw;
            }
        };
        let u2 = self.next_f64();
        let r = (-2.0 * u1.ln()).sqrt();
        let theta = 2.0 * std::f64::consts::PI * u2;
        r * theta.cos()
    }
}

#[inline]
fn splitmix64_hash(seed: u64, x: u64) -> u64 {
    splitmix64_mix(seed ^ x.wrapping_mul(0x9E37_79B9_7F4A_7C15))
}

#[inline]
fn splitmix64_mix(mut z: u64) -> u64 {
    z ^= z >> 30;
    z = z.wrapping_mul(0xBF58_476D_1CE4_E5B9);
    z ^= z >> 27;
    z = z.wrapping_mul(0x94D0_49BB_1331_11EB);
    z ^= z >> 31;
    z
}
