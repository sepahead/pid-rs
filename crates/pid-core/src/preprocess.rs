use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use nalgebra as na;

#[derive(Debug, Clone)]
pub struct Standardizer {
    mean: Vec<f64>,
    inv_std: Vec<f64>,
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

        let mut mean = vec![0.0f64; d];
        for i in 0..n {
            for (j, &v) in x.row(i).iter().enumerate() {
                mean[j] += v;
            }
        }
        for m in &mut mean {
            *m /= n as f64;
        }

        let mut var = vec![0.0f64; d];
        for i in 0..n {
            for (j, &v) in x.row(i).iter().enumerate() {
                let dv = v - mean[j];
                var[j] += dv * dv;
            }
        }
        for v in &mut var {
            *v /= n as f64;
        }

        let mut inv_std = vec![0.0f64; d];
        for j in 0..d {
            let std = var[j].sqrt();
            // If a dimension is constant, keep it centered but unscaled.
            inv_std[j] = if std > 0.0 { 1.0 / std } else { 1.0 };
        }

        Ok(Self { mean, inv_std })
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
                out.push((v - self.mean[j]) * self.inv_std[j]);
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

    pub fn inv_std(&self) -> &[f64] {
        &self.inv_std
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

        let mut index = Vec::with_capacity(in_dim);
        let mut sign = Vec::with_capacity(in_dim);
        for j in 0..in_dim {
            let h = splitmix64_hash(seed, j as u64);
            index.push((h as usize) % out_dim);
            sign.push(if (h & 1) == 0 { 1.0 } else { -1.0 });
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
        let din = self.in_dim;
        let dout = self.out_dim;

        let mut out = vec![0.0f64; n.saturating_mul(dout)];
        for i in 0..n {
            let xi = x.row(i);
            let row_out = &mut out[i * dout..(i + 1) * dout];
            for j in 0..din {
                row_out[self.index[j]] += self.sign[j] * xi[j];
            }
        }

        MatOwned::new(out, n, dout)
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
///   regime for this repo’s brute-force kNN backend).
#[derive(Debug, Clone)]
pub struct PcaProjector {
    in_dim: usize,
    out_dim: usize,
    mean: Vec<f64>,
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

        // 1) Mean.
        let mut mean = vec![0.0f64; d];
        for i in 0..n {
            let xi = x.row(i);
            for j in 0..d {
                mean[j] += xi[j];
            }
        }
        for m in &mut mean {
            *m /= n as f64;
        }

        // 2) Gram matrix G = X_c X_c^T (n×n).
        let mut gram = vec![0.0f64; n.saturating_mul(n)];
        for i in 0..n {
            let xi = x.row(i);
            for j in 0..=i {
                let xj = x.row(j);
                let mut dot = 0.0;
                for k in 0..d {
                    let a = xi[k] - mean[k];
                    let b = xj[k] - mean[k];
                    dot += a * b;
                }
                gram[i * n + j] = dot;
                gram[j * n + i] = dot;
            }
        }

        // 3) Eigendecompose G (symmetric PSD).
        let g = na::DMatrix::from_row_slice(n, n, &gram);
        let eig = na::linalg::SymmetricEigen::new(g);
        let eigvals: Vec<f64> = eig.eigenvalues.iter().copied().collect();
        let eigvecs = eig.eigenvectors;

        // Sort eigenpairs by decreasing eigenvalue.
        let mut order: Vec<usize> = (0..n).collect();
        order.sort_by(|&a, &b| eigvals[b].partial_cmp(&eigvals[a]).unwrap());

        // 4) Build the top `out_dim` right-singular vectors / PCA components:
        // V_k = X_c^T U_k Σ_k^{-1}, where G = U Σ^2 U^T and Σ = diag(sqrt(eigvals)).
        let mut components = vec![0.0f64; out_dim.saturating_mul(d)];
        for comp in 0..out_dim {
            let idx = order[comp];
            let lambda = eigvals[idx];
            if !(lambda.is_finite()) || lambda <= 0.0 {
                return Err(PidError::NumericalInstability {
                    context: "PcaProjector::fit: non-positive eigenvalue in Gram matrix",
                });
            }
            let inv_sigma = 1.0 / lambda.sqrt();
            for feat in 0..d {
                let mut acc = 0.0;
                for i in 0..n {
                    // NOTE: nalgebra stores eigenvectors as columns.
                    let u_i = eigvecs[(i, idx)];
                    acc += (x.row(i)[feat] - mean[feat]) * u_i;
                }
                components[comp * d + feat] = acc * inv_sigma;
            }
        }

        Ok(Self {
            in_dim: d,
            out_dim,
            mean,
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

        let mut out = vec![0.0f64; n.saturating_mul(k)];
        for i in 0..n {
            let xi = x.row(i);
            let row_out = &mut out[i * k..(i + 1) * k];
            for (comp, outv) in row_out.iter_mut().enumerate() {
                let w = &self.components[comp * d..(comp + 1) * d];
                let mut dot = 0.0;
                for feat in 0..d {
                    dot += (xi[feat] - self.mean[feat]) * w[feat];
                }
                *outv = dot;
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

/// Add small i.i.d. Gaussian noise to break ties (useful for kNN estimators).
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
        // Box–Muller.
        let u1 = self.next_f64().max(1e-12);
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
