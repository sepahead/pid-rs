use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use crate::stats::{finite_mean, finite_mean_std_population};
use nalgebra as na;

fn zeroed_f64(len: usize, context: &'static str) -> PidResult<Vec<f64>> {
    let mut values = Vec::new();
    values
        .try_reserve_exact(len)
        .map_err(|_| PidError::InvalidConfig {
            context,
            message: "requested output allocation is too large",
        })?;
    values.resize(len, 0.0);
    Ok(values)
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

#[derive(Debug, Clone)]
pub struct Standardizer {
    mean: Vec<f64>,
    column_scale: Vec<f64>,
    mean_scaled: Vec<f64>,
    std_scaled: Vec<f64>,
}

impl Standardizer {
    pub fn fit(x: MatRef<'_>) -> PidResult<Self> {
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
        let mut mean = vec![0.0f64; d];
        let mut column_scale = vec![0.0f64; d];
        let mut mean_scaled = vec![0.0f64; d];
        let mut std_scaled = vec![0.0f64; d];
        for j in 0..d {
            let scale = (0..n).map(|i| x.row(i)[j].abs()).fold(0.0_f64, f64::max);
            column_scale[j] = scale;
            if scale == 0.0 {
                continue;
            }

            let column: Vec<f64> = (0..n).map(|i| x.row(i)[j] / scale).collect();
            let (scaled_mean, scaled_std) = finite_mean_std_population(
                &column,
                "Standardizer::fit: non-finite scaled column moments",
            )?;
            mean_scaled[j] = scaled_mean;
            std_scaled[j] = scaled_std;
            mean[j] = scaled_mean * scale;
        }

        Ok(Self {
            mean,
            column_scale,
            mean_scaled,
            std_scaled,
        })
    }

    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        if x.ncols() != self.mean.len() {
            return Err(PidError::ShapeMismatch {
                context: "Standardizer::transform",
                expected_len: self.mean.len(),
                actual_len: x.ncols(),
            });
        }
        let n = x.nrows();
        let d = x.ncols();

        let mut out = Vec::with_capacity(n.saturating_mul(d));
        for i in 0..n {
            for (j, &v) in x.row(i).iter().enumerate() {
                let standardized = if self.std_scaled[j] > 0.0 {
                    // Standardize entirely in scaled coordinates. This avoids materializing an
                    // underflowed standard deviation or its overflowing reciprocal.
                    (v / self.column_scale[j] - self.mean_scaled[j]) / self.std_scaled[j]
                } else {
                    // A constant training column is deliberately centered but unscaled.
                    v - self.mean[j]
                };
                out.push(standardized);
            }
        }
        MatOwned::new(out, n, d)
    }

    pub fn fit_transform(x: MatRef<'_>) -> PidResult<(MatOwned, Self)> {
        let s = Self::fit(x)?;
        let y = s.transform(x)?;
        Ok((y, s))
    }

    pub fn mean(&self) -> &[f64] {
        &self.mean
    }

    /// Derive the original-unit reciprocal standard deviations.
    ///
    /// Constant columns return `1`, matching [`transform`](Self::transform)'s centered-but-unscaled
    /// convention. A nonconstant subnormal column may still be transformed through the private
    /// scaled representation even when its standalone original-unit reciprocal is not representable;
    /// this accessor returns [`PidError::NumericalInstability`] in that case.
    pub fn inv_std(&self) -> PidResult<Vec<f64>> {
        self.column_scale
            .iter()
            .zip(&self.std_scaled)
            .map(|(&scale, &scaled_std)| {
                if scaled_std == 0.0 {
                    return Ok(1.0);
                }
                let std = scale * scaled_std;
                let inverse = 1.0 / std;
                if std > 0.0 && inverse.is_finite() {
                    Ok(inverse)
                } else {
                    Err(PidError::NumericalInstability {
                        context: "Standardizer::inv_std: reciprocal standard deviation is not representable",
                    })
                }
            })
            .collect()
    }
}

#[cfg(test)]
mod standardizer_tests {
    use super::*;

    #[test]
    fn constant_max_column_has_finite_parameters_and_zero_scores() {
        let data = [f64::MAX; 4];
        let x = MatRef::new(&data, 4, 1).unwrap();

        let (scores, standardizer) = Standardizer::fit_transform(x).unwrap();

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

        let (scores, standardizer) = Standardizer::fit_transform(x).unwrap();

        assert_eq!(standardizer.mean(), &[f64::MAX * 0.5]);
        assert!((scores.as_ref().row(0)[0] + 1.0).abs() < 2.0 * f64::EPSILON);
        assert!((scores.as_ref().row(1)[0] - 1.0).abs() < 2.0 * f64::EPSILON);
    }

    #[test]
    fn tiny_scaled_column_retains_unit_standardized_geometry() {
        let data = [0.0, 1.0e-200, 2.0e-200, 3.0e-200];
        let x = MatRef::new(&data, 4, 1).unwrap();

        let (scores, _) = Standardizer::fit_transform(x).unwrap();

        let values: Vec<f64> = (0..4).map(|i| scores.as_ref().row(i)[0]).collect();
        assert!((values[0] + 1.341_640_786_499_873_8).abs() < 1e-14);
        assert!((values[3] - 1.341_640_786_499_873_8).abs() < 1e-14);
    }

    #[test]
    fn asymmetric_opposite_extremes_do_not_overflow_centering() {
        let data = [-f64::MAX, f64::MAX, f64::MAX];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let (scores, _) = Standardizer::fit_transform(x).unwrap();

        assert!((scores.as_ref().row(0)[0] + 2.0_f64.sqrt()).abs() < 1e-14);
        assert!((scores.as_ref().row(1)[0] - 1.0 / 2.0_f64.sqrt()).abs() < 1e-14);
        assert!((scores.as_ref().row(2)[0] - 1.0 / 2.0_f64.sqrt()).abs() < 1e-14);
    }

    #[test]
    fn subnormal_standard_deviation_still_produces_unit_scores() {
        let smallest = f64::from_bits(1);
        let data = [0.0, 2.0 * smallest];
        let x = MatRef::new(&data, 2, 1).unwrap();

        let (scores, standardizer) = Standardizer::fit_transform(x).unwrap();

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
#[derive(Debug, Clone)]
pub struct HashProjector {
    in_dim: usize,
    out_dim: usize,
    index: Vec<usize>,
    sign: Vec<f64>,
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

        let mut index = Vec::new();
        index
            .try_reserve_exact(in_dim)
            .map_err(|_| PidError::InvalidConfig {
                context: "HashProjector::new",
                message: "requested input dimension is too large",
            })?;
        let mut sign = Vec::new();
        sign.try_reserve_exact(in_dim)
            .map_err(|_| PidError::InvalidConfig {
                context: "HashProjector::new",
                message: "requested input dimension is too large",
            })?;
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

        Ok(Self {
            in_dim,
            out_dim,
            index,
            sign,
        })
    }

    pub fn in_dim(&self) -> usize {
        self.in_dim
    }

    pub fn out_dim(&self) -> usize {
        self.out_dim
    }

    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        if x.ncols() != self.in_dim {
            return Err(PidError::ShapeMismatch {
                context: "HashProjector::transform",
                expected_len: self.in_dim,
                actual_len: x.ncols(),
            });
        }

        let n = x.nrows();
        let dout = self.out_dim;

        let out_len = n.checked_mul(dout).ok_or(PidError::InvalidConfig {
            context: "HashProjector::transform",
            message: "output size overflow",
        })?;
        let mut out = zeroed_f64(out_len, "HashProjector::transform")?;
        let mut bucket_scales = zeroed_f64(dout, "HashProjector::transform")?;
        let mut bucket_corrections = zeroed_f64(dout, "HashProjector::transform")?;
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
            Err(PidError::InvalidConfig { .. })
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
/// - Uses `nalgebra`’s symmetric eigendecomposition on the `n×n` Gram matrix (`X_c X_c^T`). This is
///   a correctness-first baseline and is most appropriate when `n` is modest (which is already the
///   regime for this repo's exact kNN backend, regardless of whether it selects the kd-tree or
///   brute-force path).
#[derive(Debug, Clone)]
pub struct PcaProjector {
    in_dim: usize,
    out_dim: usize,
    mean: Vec<f64>,
    column_scales: Vec<f64>,
    mean_scaled: Vec<f64>,
    // Row-major (out_dim × in_dim): each component is a length-in_dim vector.
    components: Vec<f64>,
}

impl PcaProjector {
    pub fn fit(x: MatRef<'_>, out_dim: usize) -> PidResult<Self> {
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

        // 1) Center each column in its own scaled coordinates. A single input-wide scale would
        // erase a tiny varying feature merely because another feature has a huge constant offset.
        // Per-column scaling removes offsets safely; a later global log scale restores the correct
        // relative centered magnitudes for PCA.
        let mut mean = vec![0.0f64; d];
        let mut mean_scaled = vec![0.0f64; d];
        let mut column_scales = vec![0.0f64; d];
        for j in 0..d {
            let column_scale = (0..n).map(|i| x.row(i)[j].abs()).fold(0.0_f64, f64::max);
            column_scales[j] = column_scale;
            if column_scale == 0.0 {
                continue;
            }
            let column: Vec<f64> = (0..n).map(|i| x.row(i)[j] / column_scale).collect();
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

        // 3) Eigendecompose G (symmetric PSD).
        let g = na::DMatrix::from_row_slice(n, n, &gram);
        let eig = na::linalg::SymmetricEigen::new(g);
        let eigvals: Vec<f64> = eig.eigenvalues.iter().copied().collect();
        let eigvecs = eig.eigenvectors;

        // Sort eigenpairs by decreasing eigenvalue. `total_cmp` is a total order (never `None`),
        // so the sort cannot panic regardless of the eigenvalues.
        let mut order: Vec<usize> = (0..n).collect();
        order.sort_by(|&a, &b| eigvals[b].total_cmp(&eigvals[a]));

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
                    // NOTE: nalgebra stores eigenvectors as columns.
                    let u_i = eigvecs[(i, idx)];
                    acc += centered[i * d + feat] * u_i;
                }
                components[comp * d + feat] = acc * inv_sigma;
            }
        }

        Ok(Self {
            in_dim: d,
            out_dim,
            mean,
            column_scales,
            mean_scaled,
            components,
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
pub struct Jitter {
    std: f64,
    seed: u64,
}

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

        let mut out = Vec::with_capacity(n.saturating_mul(d));
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

    fn next_f64(&mut self) -> f64 {
        // 53 bits -> [0,1)
        let u = self.next_u64() >> 11;
        (u as f64) * (1.0 / ((1u64 << 53) as f64))
    }

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
