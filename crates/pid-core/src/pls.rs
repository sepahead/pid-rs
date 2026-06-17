//! Partial Least Squares (PLS) supervised dimensionality reduction.
//!
//! PLS finds directions in source space `X` that are maximally correlated with
//! a target `Y`. Unlike PCA (unsupervised), PLS uses label/target information to
//! project high-dimensional embeddings into a task-relevant subspace where kNN
//! estimators are more effective.
//!
//! This addresses the core finding in `findings.md`: unsupervised projection
//! (PCA, hash) fails when signal variance ≈ noise variance per dimension. PLS
//! succeeds because it uses `Y` (e.g., actions, success labels) to find the
//! informative subspace.
//!
//! # Algorithm (NIPALS-PLS2)
//!
//! For each latent component:
//! 1. Initialize `u` from a column of `Y`
//! 2. Iterate until convergence:
//!    - `w = X^T u / ||X^T u||` (X-weights)
//!    - `t = X w` (X-scores)
//!    - `c = Y^T t / (t^T t)` (Y-weights)
//!    - `u = Y c / ||Y c||` (Y-scores)
//! 3. `p = X^T t / (t^T t)` (X-loadings)
//! 4. Deflate: `X -= t p^T`, `Y -= t c^T`
//!
//! # Leakage warning
//!
//! PLS must be fit **only on the training split**. Never fit PLS on held-out
//! data; doing so leaks target information into the projection and invalidates
//! all downstream PID/CI estimates.

use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use nalgebra as na;

const MAX_ITER: usize = 200;
const CONVERGENCE_TOL: f64 = 1e-10;

/// Supervised dimensionality reduction via Partial Least Squares (NIPALS-PLS2).
#[derive(Debug, Clone)]
pub struct PlsProjector {
    in_dim: usize,
    out_dim: usize,
    target_dim: usize,
    x_mean: Vec<f64>,
    y_mean: Vec<f64>,
    /// Row-major (out_dim × in_dim): each row is a weight vector `w`.
    x_weights: Vec<f64>,
    /// Row-major (out_dim × target_dim): each row is a weight vector `c`.
    y_weights: Vec<f64>,
    /// Row-major (out_dim × in_dim): each row is a loading vector `p`.
    x_loadings: Vec<f64>,
}

impl PlsProjector {
    /// Fit PLS on source `x` (n×d_x) and target `y` (n×d_y).
    ///
    /// `out_dim` is the number of latent components to extract.
    /// Must satisfy: `out_dim >= 1`, `out_dim <= min(d_x, n-1)`.
    #[allow(unused_assignments)]
    pub fn fit(x: MatRef<'_>, y: MatRef<'_>, out_dim: usize) -> PidResult<Self> {
        let n = x.nrows();
        let d_x = x.ncols();
        let d_y = y.ncols();

        if n < 2 || d_x == 0 {
            return Err(PidError::InvalidConfig {
                context: "PlsProjector::fit",
                message: "require n >= 2 and d_x >= 1",
            });
        }
        if y.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "PlsProjector::fit",
                left_rows: n,
                right_rows: y.nrows(),
            });
        }
        if d_y == 0 {
            return Err(PidError::InvalidConfig {
                context: "PlsProjector::fit",
                message: "target y must have d_y >= 1",
            });
        }
        if out_dim == 0 {
            return Err(PidError::InvalidConfig {
                context: "PlsProjector::fit",
                message: "out_dim must be >= 1",
            });
        }
        let max_out = d_x.min(n.saturating_sub(1));
        if out_dim > max_out {
            return Err(PidError::InvalidConfig {
                context: "PlsProjector::fit",
                message: "out_dim must be <= min(d_x, n-1)",
            });
        }

        // 1. Center X and Y.
        let mut x_mean = vec![0.0f64; d_x];
        let mut y_mean = vec![0.0f64; d_y];
        for i in 0..n {
            let xi = x.row(i);
            let yi = y.row(i);
            for j in 0..d_x {
                x_mean[j] += xi[j];
            }
            for j in 0..d_y {
                y_mean[j] += yi[j];
            }
        }
        for m in &mut x_mean {
            *m /= n as f64;
        }
        for m in &mut y_mean {
            *m /= n as f64;
        }

        // Work on centered copies (deflated in place).
        let mut xc = vec![0.0f64; n * d_x];
        let mut yc = vec![0.0f64; n * d_y];
        for i in 0..n {
            let xi = x.row(i);
            let yi = y.row(i);
            for j in 0..d_x {
                xc[i * d_x + j] = xi[j] - x_mean[j];
            }
            for j in 0..d_y {
                yc[i * d_y + j] = yi[j] - y_mean[j];
            }
        }

        let mut x_weights = vec![0.0f64; out_dim * d_x];
        let mut y_weights = vec![0.0f64; out_dim * d_y];
        let mut x_loadings = vec![0.0f64; out_dim * d_x];

        // 2. NIPALS iteration for each component.
        for comp in 0..out_dim {
            // Initialize u from the first column of Y_c.
            let mut u = vec![0.0f64; n];
            for i in 0..n {
                u[i] = yc[i * d_y];
            }
            let u_norm = dot_norm(&u);
            if u_norm < 1e-15 {
                // If first Y column is zero after centering, try other columns.
                let mut found = false;
                for j in 1..d_y {
                    for i in 0..n {
                        u[i] = yc[i * d_y + j];
                    }
                    if dot_norm(&u) >= 1e-15 {
                        found = true;
                        break;
                    }
                }
                if !found {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: target Y is zero after centering",
                    });
                }
            }

            let mut w = vec![0.0f64; d_x];
            let mut t = vec![0.0f64; n];
            let mut c_vec = vec![0.0f64; d_y];

            for _iter in 0..MAX_ITER {
                // w = X_c^T u / ||X_c^T u||
                mat_vec_t(&xc, &u, n, d_x, &mut w);
                let w_norm = dot_norm(&w);
                if w_norm < 1e-15 {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: X^T u is zero (no covariance)",
                    });
                }
                for v in &mut w {
                    *v /= w_norm;
                }

                // t = X_c w
                mat_vec(&xc, &w, n, d_x, &mut t);

                // c = Y_c^T t / (t^T t)
                let t_dot_t = dot(&t, &t);
                if t_dot_t < 1e-30 {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: t^T t ≈ 0",
                    });
                }
                mat_vec_t(&yc, &t, n, d_y, &mut c_vec);
                let inv_tt = 1.0 / t_dot_t;
                for v in &mut c_vec {
                    *v *= inv_tt;
                }

                // u_new = Y_c c / ||Y_c c||
                let mut u_new = vec![0.0f64; n];
                mat_vec(&yc, &c_vec, n, d_y, &mut u_new);
                let u_new_norm = dot_norm(&u_new);

                if u_new_norm < 1e-15 {
                    // Converged (or degenerate); stop.
                    u = u_new;
                    break;
                }
                for v in &mut u_new {
                    *v /= u_new_norm;
                }

                // Check convergence.
                let diff = vec_diff_norm(&u, &u_new);
                u = u_new;

                if diff < CONVERGENCE_TOL {
                    break;
                }
            }

            // Recompute t = X_c w after final iteration.
            mat_vec(&xc, &w, n, d_x, &mut t);
            let t_dot_t = dot(&t, &t);
            if t_dot_t < 1e-30 {
                return Err(PidError::NumericalInstability {
                    context: "PlsProjector::fit: final t^T t ≈ 0",
                });
            }

            // p = X_c^T t / (t^T t)
            let mut p = vec![0.0f64; d_x];
            mat_vec_t(&xc, &t, n, d_x, &mut p);
            let inv_tt = 1.0 / t_dot_t;
            for v in &mut p {
                *v *= inv_tt;
            }

            // Store w, c, p for this component.
            let w_out = &mut x_weights[comp * d_x..(comp + 1) * d_x];
            w_out.copy_from_slice(&w);
            let c_out = &mut y_weights[comp * d_y..(comp + 1) * d_y];
            c_out.copy_from_slice(&c_vec);
            let p_out = &mut x_loadings[comp * d_x..(comp + 1) * d_x];
            p_out.copy_from_slice(&p);

            // Deflate: X_c -= t p^T, Y_c -= t c^T
            for i in 0..n {
                let ti = t[i];
                for j in 0..d_x {
                    xc[i * d_x + j] -= ti * p[j];
                }
                for j in 0..d_y {
                    yc[i * d_y + j] -= ti * c_vec[j];
                }
            }
        }

        Ok(Self {
            in_dim: d_x,
            out_dim,
            target_dim: d_y,
            x_mean,
            y_mean,
            x_weights,
            y_weights,
            x_loadings,
        })
    }

    pub fn in_dim(&self) -> usize {
        self.in_dim
    }

    pub fn out_dim(&self) -> usize {
        self.out_dim
    }

    pub fn target_dim(&self) -> usize {
        self.target_dim
    }

    pub fn x_mean(&self) -> &[f64] {
        &self.x_mean
    }

    pub fn y_mean(&self) -> &[f64] {
        &self.y_mean
    }

    pub fn x_weights(&self) -> &[f64] {
        &self.x_weights
    }

    pub fn x_loadings(&self) -> &[f64] {
        &self.x_loadings
    }

    pub fn y_weights(&self) -> &[f64] {
        &self.y_weights
    }

    /// Project `x` (n×d_x) into the PLS latent space (n×out_dim).
    ///
    /// This computes `T = (X - mean_X) W` where W contains the X-weight vectors.
    pub fn transform(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        if x.ncols() != self.in_dim {
            return Err(PidError::ShapeMismatch {
                context: "PlsProjector::transform",
                expected_len: self.in_dim,
                actual_len: x.ncols(),
            });
        }
        let n = x.nrows();
        let d = self.in_dim;
        let k = self.out_dim;

        let mut out = vec![0.0f64; n * k];
        for i in 0..n {
            let xi = x.row(i);
            for (comp, outv) in out[i * k..(i + 1) * k].iter_mut().enumerate() {
                let w = &self.x_weights[comp * d..(comp + 1) * d];
                let mut dot = 0.0;
                for feat in 0..d {
                    dot += (xi[feat] - self.x_mean[feat]) * w[feat];
                }
                *outv = dot;
            }
        }
        MatOwned::new(out, n, k)
    }

    /// Convenience: fit + transform in one call.
    pub fn fit_transform(
        x: MatRef<'_>,
        y: MatRef<'_>,
        out_dim: usize,
    ) -> PidResult<(MatOwned, Self)> {
        let p = Self::fit(x, y, out_dim)?;
        let t = p.transform(x)?;
        Ok((t, p))
    }

    /// PLS regression coefficients `B` (in_dim × target_dim) mapping centered sources
    /// to centered targets: `Ŷ = (X − x_mean) · B + y_mean`.
    ///
    /// `B = W (Pᵀ W)⁻¹ Cᵀ`, where `W` are the X-weights, `P` the X-loadings, and `C`
    /// the Y-weights. The rotation `W (Pᵀ W)⁻¹` converts the raw NIPALS weights into
    /// the operator that maps centered `X` directly to the deflated scores, so `B`
    /// reproduces the exact in-sample NIPALS regression for **any** number of
    /// components (unlike applying [`transform`](Self::transform)'s scores to the
    /// Y-weights, which only coincides for a single component).
    ///
    /// `Pᵀ W` is upper-triangular with unit diagonal by NIPALS construction, hence
    /// always invertible once each component is non-degenerate (guaranteed by the
    /// `tᵀt` guards in [`fit`](Self::fit)).
    pub fn coefficients(&self) -> PidResult<MatOwned> {
        let k = self.out_dim;
        let d_x = self.in_dim;
        let d_y = self.target_dim;

        // M = Pᵀ W (k×k): M[i][j] = p_i · w_j.
        let m = na::DMatrix::<f64>::from_fn(k, k, |i, j| {
            let mut s = 0.0;
            for f in 0..d_x {
                s += self.x_loadings[i * d_x + f] * self.x_weights[j * d_x + f];
            }
            s
        });
        let minv = m.try_inverse().ok_or(PidError::NumericalInstability {
            context: "PlsProjector::coefficients: (PᵀW) is singular",
        })?;

        // B = W·Minv·Cᵀ. R = W·Minv (d_x×k); B = R·Cᵀ (d_x×d_y).
        let mut b = vec![0.0f64; d_x * d_y];
        let mut r = vec![0.0f64; k];
        for f in 0..d_x {
            for (c, rc) in r.iter_mut().enumerate() {
                let mut s = 0.0;
                for j in 0..k {
                    s += self.x_weights[j * d_x + f] * minv[(j, c)];
                }
                *rc = s;
            }
            for j in 0..d_y {
                let mut s = 0.0;
                for (c, &rc) in r.iter().enumerate() {
                    s += rc * self.y_weights[c * d_y + j];
                }
                b[f * d_y + j] = s;
            }
        }
        MatOwned::new(b, d_x, d_y)
    }

    /// Predict targets for `x` (n×in_dim) via the PLS regression `Ŷ = (X−x̄)B + ȳ`.
    ///
    /// This is the model's actual in-sample prediction; use it (not raw scores) for
    /// cross-validated `Q²` so the held-out point never sees its own target.
    pub fn predict(&self, x: MatRef<'_>) -> PidResult<MatOwned> {
        if x.ncols() != self.in_dim {
            return Err(PidError::ShapeMismatch {
                context: "PlsProjector::predict",
                expected_len: self.in_dim,
                actual_len: x.ncols(),
            });
        }
        let coeffs = self.coefficients()?;
        let b = coeffs.as_ref();
        let n = x.nrows();
        let d_y = self.target_dim;
        let mut out = vec![0.0f64; n * d_y];
        for i in 0..n {
            let xi = x.row(i);
            let out_row = &mut out[i * d_y..(i + 1) * d_y];
            // Ŷ_i = y_mean + Σ_f (x_if − x_mean_f) · B[f, :].
            out_row.copy_from_slice(&self.y_mean);
            for (f, (&xf, &mf)) in xi.iter().zip(&self.x_mean).enumerate() {
                let cf = xf - mf;
                if cf == 0.0 {
                    continue;
                }
                let b_row = b.row(f);
                for (slot, &b_fj) in out_row.iter_mut().zip(b_row) {
                    *slot += cf * b_fj;
                }
            }
        }
        MatOwned::new(out, n, d_y)
    }
}

// ── BLAS-like helpers ──────────────────────────────────────────────────────

/// `out = A^T v` where A is (nrows × ncols) row-major, v is length nrows.
fn mat_vec_t(a: &[f64], v: &[f64], nrows: usize, ncols: usize, out: &mut [f64]) {
    for item in out.iter_mut().take(ncols) {
        *item = 0.0;
    }
    for i in 0..nrows {
        let vi = v[i];
        let row = &a[i * ncols..(i + 1) * ncols];
        for j in 0..ncols {
            out[j] += row[j] * vi;
        }
    }
}

/// `out = A v` where A is (nrows × ncols) row-major, v is length ncols.
fn mat_vec(a: &[f64], v: &[f64], nrows: usize, ncols: usize, out: &mut [f64]) {
    for i in 0..nrows {
        let row = &a[i * ncols..(i + 1) * ncols];
        let mut sum = 0.0;
        for j in 0..ncols {
            sum += row[j] * v[j];
        }
        out[i] = sum;
    }
}

fn dot(a: &[f64], b: &[f64]) -> f64 {
    a.iter().zip(b).map(|(x, y)| x * y).sum()
}

fn dot_norm(v: &[f64]) -> f64 {
    dot(v, v).sqrt()
}

fn vec_diff_norm(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .map(|(x, y)| {
            let d = x - y;
            d * d
        })
        .sum::<f64>()
        .sqrt()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pls_recovers_signal_direction() {
        // X is n×10, Y = X[:,0] (signal in first dimension only).
        // PLS should put most weight on dimension 0.
        let n = 100;
        let d_x = 10;
        let d_y = 1;
        let seed: u64 = 42;
        let mut rng = crate::preprocess::SplitMix64::new(seed);

        let mut x_data = Vec::with_capacity(n * d_x);
        let mut y_data = Vec::with_capacity(n * d_y);
        for _ in 0..n {
            let signal = rng.normal();
            x_data.push(signal);
            for _ in 1..d_x {
                x_data.push(rng.normal());
            }
            y_data.push(signal); // Y = X[:,0]
        }

        let x = MatRef::new(&x_data, n, d_x).unwrap();
        let y = MatRef::new(&y_data, n, d_y).unwrap();

        let pls = PlsProjector::fit(x, y, 2).unwrap();
        let t = pls.transform(x).unwrap();

        assert_eq!(t.as_ref().nrows(), n);
        assert_eq!(t.as_ref().ncols(), 2);

        // First weight vector should be dominated by dimension 0.
        let w0 = &pls.x_weights()[0..d_x];
        let w0_abs_max = w0.iter().map(|v| v.abs()).fold(0.0f64, f64::max);
        assert!(
            w0[0].abs() > 0.9 * w0_abs_max,
            "first PLS weight should concentrate on signal dim; w0={w0:?}"
        );

        // Projected scores should have nonzero variance.
        let t0: Vec<f64> = (0..n).map(|i| t.as_ref().row(i)[0]).collect();
        let t0_mean = t0.iter().sum::<f64>() / n as f64;
        let t0_var = t0.iter().map(|v| (v - t0_mean).powi(2)).sum::<f64>() / n as f64;
        assert!(
            t0_var > 0.01,
            "PLS scores should have variance; var={t0_var}"
        );
    }

    #[test]
    fn pls_rejects_bad_shapes() {
        let x = vec![0.0f64; 10];
        let y = vec![0.0f64; 5];
        let xm = MatRef::new(&x, 5, 2).unwrap();
        let ym = MatRef::new(&y, 5, 1).unwrap();
        assert!(PlsProjector::fit(xm, ym, 0).is_err());
        assert!(PlsProjector::fit(xm, ym, 5).is_err()); // out_dim > n-1
    }

    #[test]
    fn pls_deterministic() {
        let n = 50;
        let d_x = 5;
        let d_y = 2;
        let mut rng = crate::preprocess::SplitMix64::new(123);
        let mut x_data = Vec::with_capacity(n * d_x);
        let mut y_data = Vec::with_capacity(n * d_y);
        for _ in 0..n {
            for _ in 0..d_x {
                x_data.push(rng.normal());
            }
            for _ in 0..d_y {
                y_data.push(rng.normal());
            }
        }
        let x = MatRef::new(&x_data, n, d_x).unwrap();
        let y = MatRef::new(&y_data, n, d_y).unwrap();

        let (t1, p1) = PlsProjector::fit_transform(x, y, 3).unwrap();
        let (t2, p2) = PlsProjector::fit_transform(x, y, 3).unwrap();

        // Deterministic: same input → same output.
        for i in 0..n * 3 {
            assert!(
                (t1.as_ref().row(i / 3)[i % 3] - t2.as_ref().row(i / 3)[i % 3]).abs() < 1e-12,
                "PLS must be deterministic"
            );
        }
        for (a, b) in p1.x_weights().iter().zip(p2.x_weights()) {
            assert!((a - b).abs() < 1e-12);
        }
    }

    #[test]
    fn pls_outperforms_pca_on_signal_in_noise() {
        // Generate X with signal in dim 0, noise in dims 1..d.
        // Y depends only on dim 0. PCA cannot find this; PLS can.
        let n = 200;
        let d_x = 20;
        let d_y = 1;
        let mut rng = crate::preprocess::SplitMix64::new(99);
        let mut x_data = Vec::with_capacity(n * d_x);
        let mut y_data = Vec::with_capacity(n * d_y);
        for _ in 0..n {
            let signal = rng.normal();
            x_data.push(signal);
            for _ in 1..d_x {
                x_data.push(rng.normal());
            }
            y_data.push(signal + 0.1 * rng.normal());
        }
        let x = MatRef::new(&x_data, n, d_x).unwrap();
        let y = MatRef::new(&y_data, n, d_y).unwrap();

        // PLS: first weight should concentrate on dim 0.
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let w = &pls.x_weights()[0..d_x];
        assert!(
            w[0].abs() > 0.8,
            "PLS should find signal direction; w[0]={}",
            w[0]
        );
    }
}
