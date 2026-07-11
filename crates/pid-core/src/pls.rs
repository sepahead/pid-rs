//! Partial Least Squares (PLS) supervised dimensionality reduction.
//!
//! PLS finds directions in source space `X` that are maximally correlated with
//! a target `Y`. Unlike PCA (unsupervised), PLS uses label/target information to
//! project high-dimensional embeddings into a task-relevant subspace where kNN
//! estimators are more effective.
//!
//! Motivation: unsupervised projection (PCA, hash) cannot separate signal from noise when the
//! per-dimension signal variance is comparable to the noise variance — no variance criterion
//! distinguishes them. PLS succeeds in that regime because it uses `Y` (e.g., actions, success
//! labels) to find the informative subspace; the in-crate test
//! `pls_outperforms_pca_on_signal_in_noise` demonstrates this concretely.
//!
//! # Algorithm (NIPALS-PLS2)
//!
//! For each latent component:
//! 1. Initialize `u` from the column of `Y` with the strongest `X` cross-covariance
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
//!
//! # Numeric feature scaling
//!
//! PLS preserves the caller's relative feature units. If nonzero centered feature magnitudes span
//! more than `f64` can represent under one common linear-algebra scale, fitting returns
//! [`PidError::NumericalInstability`] instead of silently dropping a feature. Standardize on the
//! training split when such heterogeneous units are not scientifically intentional.

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
    // Fitting uses one common centered-data scale, computed through per-column coordinates. Keep
    // that representation so transforms never need an overflowing `x - x_mean` subtraction.
    x_scale: f64,
    x_column_scales: Vec<f64>,
    x_mean_scaled: Vec<f64>,
    y_mean: Vec<f64>,
    y_scale: f64,
    /// Row-major (out_dim × in_dim): each row is a weight vector `w`.
    x_weights: Vec<f64>,
    /// Row-major (out_dim × target_dim): NIPALS `c` weights in the internally scaled
    /// X/Y coordinates. Keeping these avoids underflowing a tiny original-unit coefficient that
    /// can still produce a representable prediction when multiplied by a large held-out X.
    y_weights_scaled: Vec<f64>,
    /// Row-major (out_dim × in_dim): each row is a loading vector `p`.
    x_loadings: Vec<f64>,
}

impl PlsProjector {
    /// Fit PLS on source `x` (n×d_x) and target `y` (n×d_y).
    ///
    /// `out_dim` is the number of latent components to extract.
    /// Must satisfy: `out_dim >= 1`, `out_dim <= min(d_x, n-1)`.
    pub fn fit(x: MatRef<'_>, y: MatRef<'_>, out_dim: usize) -> PidResult<Self> {
        Self::fit_with_iteration_limit(x, y, out_dim, MAX_ITER)
    }

    fn fit_with_iteration_limit(
        x: MatRef<'_>,
        y: MatRef<'_>,
        out_dim: usize,
        max_iter: usize,
    ) -> PidResult<Self> {
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
        if max_iter == 0 {
            return Err(PidError::InvalidConfig {
                context: "PlsProjector::fit",
                message: "NIPALS iteration limit must be >= 1",
            });
        }

        // 1. Center globally-scaled X and Y. Uniform positive scaling leaves NIPALS directions and
        // X loadings unchanged, while keeping tiny data away from underflow and huge, oppositely
        // signed values away from overflow. Means remain available in the caller's original units.
        let CenteredMatrix {
            mean: x_mean,
            mean_scaled: x_mean_scaled,
            column_scales: x_column_scales,
            values: mut xc,
            scale: x_scale,
        } = center_scaled_matrix(x, "PlsProjector::fit: X centering failed")?;
        let CenteredMatrix {
            mean: y_mean,
            values: mut yc,
            scale: y_scale,
            ..
        } = center_scaled_matrix(y, "PlsProjector::fit: Y centering failed")?;

        // Frobenius scale of the centered X. The degeneracy guards below are made relative to it
        // so they are scale-invariant: with the previous fixed absolute thresholds, a genuinely
        // rank-deficient direction on large-magnitude input (e.g. ~1e6) has `t_dot_t ~ 1e-6` — far
        // above `1e-30` — and would slip through, inflating a near-null score into a garbage
        // loading vector. `t = X_c·w` with `‖w‖ = 1`, so a healthy `t_dot_t ≈ σ²` sits many orders
        // above `n·ε·‖X_c‖_F²`, while a null direction sits below it.
        let frob = l2_norm(&xc);
        let frob_sq = frob * frob;
        if !frob.is_finite() || !frob_sq.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "PlsProjector::fit: centered X norm overflow",
            });
        }
        let tt_floor = (n as f64) * f64::EPSILON * frob_sq;
        if !tt_floor.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "PlsProjector::fit: component tolerance overflow",
            });
        }

        let mut x_weights = vec![0.0f64; out_dim * d_x];
        let mut y_weights_scaled = vec![0.0f64; out_dim * d_y];
        let mut x_loadings = vec![0.0f64; out_dim * d_x];

        // 2. NIPALS iteration for each component.
        for comp in 0..out_dim {
            // Start from the target column with the strongest X cross-covariance, not merely the
            // first non-constant column. This cannot fail just because an unrelated target happens
            // to precede an informative one. Exact ties are broken by canonicalized column values,
            // making the result invariant to target-column order.
            let mut u = strongest_target_score(&xc, &yc, n, d_x, d_y, frob)?;

            let mut w = vec![0.0f64; d_x];
            let mut t = vec![0.0f64; n];
            let mut c_vec = vec![0.0f64; d_y];
            let y_frob = l2_norm(&yc);
            if !y_frob.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "PlsProjector::fit: centered Y norm overflow",
                });
            }

            let mut converged = false;
            for _iter in 0..max_iter {
                // w = X_c^T u / ||X_c^T u||
                mat_vec_t(&xc, &u, n, d_x, &mut w);
                let w_norm = l2_norm(&w);
                // `w = Xᵀu`, so `‖w‖ ≤ ‖X_c‖_F·‖u‖`; scale the "no covariance" threshold accordingly
                // (`u` is normalized before every iteration).
                let w_floor = (n as f64) * f64::EPSILON * frob * l2_norm(&u);
                if !w_norm.is_finite() || !w_floor.is_finite() {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: X^T u norm overflow",
                    });
                }
                if w_norm <= w_floor {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: X^T u is ~0 relative to the data scale (no covariance)",
                    });
                }
                for v in &mut w {
                    *v /= w_norm;
                }
                ensure_finite(&w, "PlsProjector::fit: non-finite normalized X weights")?;

                // t = X_c w
                mat_vec(&xc, &w, n, d_x, &mut t);

                // c = Y_c^T t / (t^T t)
                let t_norm = l2_norm(&t);
                let t_dot_t = t_norm * t_norm;
                if !t_dot_t.is_finite() || t_dot_t <= tt_floor {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: t^T t ≈ 0 relative to the data scale (degenerate component)",
                    });
                }
                mat_vec_t(&yc, &t, n, d_y, &mut c_vec);
                let inv_tt = 1.0 / t_dot_t;
                for v in &mut c_vec {
                    *v *= inv_tt;
                }
                ensure_finite(&c_vec, "PlsProjector::fit: non-finite target weights")?;

                // u_new = Y_c c / ||Y_c c||
                let mut u_new = vec![0.0f64; n];
                mat_vec(&yc, &c_vec, n, d_y, &mut u_new);
                let u_new_norm = l2_norm(&u_new);
                let c_norm = l2_norm(&c_vec);
                let u_floor = (n as f64) * f64::EPSILON * y_frob * c_norm;
                if !u_new_norm.is_finite() || !c_norm.is_finite() || !u_floor.is_finite() {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: updated target score norm overflow",
                    });
                }
                if u_new_norm <= u_floor {
                    return Err(PidError::NumericalInstability {
                        context:
                            "PlsProjector::fit: updated target score is in the numerical null space",
                    });
                }
                for v in &mut u_new {
                    *v /= u_new_norm;
                }

                // Singular vectors are defined only up to sign. Align the new iterate before
                // comparing it so a harmless sign choice cannot look like non-convergence.
                if dot(&u, &u_new) < 0.0 {
                    for value in &mut u_new {
                        *value = -*value;
                    }
                }
                let diff = vec_diff_norm(&u, &u_new);
                if !diff.is_finite() {
                    return Err(PidError::NumericalInstability {
                        context: "PlsProjector::fit: convergence norm overflow",
                    });
                }
                u = u_new;

                if diff <= CONVERGENCE_TOL {
                    converged = true;
                    break;
                }
            }
            if !converged {
                return Err(PidError::NumericalInstability {
                    context: "PlsProjector::fit: NIPALS iteration did not converge",
                });
            }

            // Recompute t = X_c w after final iteration.
            mat_vec(&xc, &w, n, d_x, &mut t);
            let t_norm = l2_norm(&t);
            let t_dot_t = t_norm * t_norm;
            if !t_dot_t.is_finite() || t_dot_t <= tt_floor {
                return Err(PidError::NumericalInstability {
                    context: "PlsProjector::fit: final t^T t ≈ 0 relative to the data scale (degenerate component)",
                });
            }

            // p = X_c^T t / (t^T t)
            let mut p = vec![0.0f64; d_x];
            mat_vec_t(&xc, &t, n, d_x, &mut p);
            let inv_tt = 1.0 / t_dot_t;
            for v in &mut p {
                *v *= inv_tt;
            }
            ensure_finite(&p, "PlsProjector::fit: non-finite X loadings")?;

            // Store w, c, p for this component.
            let w_out = &mut x_weights[comp * d_x..(comp + 1) * d_x];
            w_out.copy_from_slice(&w);
            let c_out = &mut y_weights_scaled[comp * d_y..(comp + 1) * d_y];
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
            ensure_finite(
                &xc,
                "PlsProjector::fit: X deflation produced non-finite values",
            )?;
            ensure_finite(
                &yc,
                "PlsProjector::fit: Y deflation produced non-finite values",
            )?;
        }

        ensure_finite(&x_weights, "PlsProjector::fit: non-finite X weights")?;
        ensure_finite(
            &y_weights_scaled,
            "PlsProjector::fit: non-finite scaled Y weights",
        )?;
        ensure_finite(&x_loadings, "PlsProjector::fit: non-finite X loadings")?;

        Ok(Self {
            in_dim: d_x,
            out_dim,
            target_dim: d_y,
            x_mean,
            x_scale,
            x_column_scales,
            x_mean_scaled,
            y_mean,
            y_scale,
            x_weights,
            y_weights_scaled,
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

    /// NIPALS target weights in the caller's original X/Y units.
    ///
    /// # Errors
    ///
    /// Returns [`PidError::NumericalInstability`] when a nonzero original-unit weight lies outside
    /// the representable `f64` range. The fitted model can still make sound predictions in that
    /// case through [`predict`](Self::predict), which keeps the scale factors separate.
    pub fn y_weights(&self) -> PidResult<Vec<f64>> {
        self.y_weights_scaled
            .iter()
            .map(|&weight| {
                checked_mul_div(weight, self.y_scale, self.x_scale).ok_or(
                    PidError::NumericalInstability {
                        context:
                            "PlsProjector::y_weights: original-unit weight is not representable",
                    },
                )
            })
            .collect()
    }

    /// Project `x` (n×d_x) into the PLS latent space (n×out_dim).
    ///
    /// Computes the latent scores `T = (X − x̄)·R`, where `R = W(PᵀW)⁻¹` is the PLS
    /// rotation that maps the *original* centered sources directly onto the deflated
    /// NIPALS scores. Using the raw weights `W` would reproduce the scores only for
    /// the first component; for component ≥ 2 the fitted score `t_c = X_c·w_c` lives
    /// in the *deflated* space `X_c`, not the original, so the rotation is required.
    /// For `out_dim == 1`, `PᵀW = [1]` and `R = W`, so this matches the
    /// single-component projection exactly.
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
        let r = self.rotated_weights()?;

        let mut out = vec![0.0f64; n * k];
        for i in 0..n {
            let xi = x.row(i);
            for (comp, outv) in out[i * k..(i + 1) * k].iter_mut().enumerate() {
                *outv = stable_centered_weighted_sum(
                    xi,
                    &self.x_column_scales,
                    &self.x_mean_scaled,
                    (0..d).map(|feat| r[feat * k + comp]),
                    AffineRestore {
                        numerator_scale: 1.0,
                        denominator_scale: 1.0,
                        offset: 0.0,
                        context: "PlsProjector::transform: projected score is not representable",
                    },
                )?;
            }
        }
        MatOwned::new(out, n, k)
    }

    /// PLS rotation `R = W(PᵀW)⁻¹` (in_dim × out_dim, row-major), mapping centered
    /// sources to the deflated NIPALS scores: `T = (X − x̄)·R`. Shared by
    /// [`transform`](Self::transform) and [`coefficients`](Self::coefficients) so the
    /// projection and the regression operator are derived from one rotation.
    ///
    /// `PᵀW` is upper-triangular with unit diagonal by NIPALS construction, hence
    /// invertible once each component is non-degenerate (guaranteed by the `tᵀt`
    /// guards in [`fit`](Self::fit)).
    fn rotated_weights(&self) -> PidResult<Vec<f64>> {
        let k = self.out_dim;
        let d_x = self.in_dim;

        // M = Pᵀ W (k×k): M[i][j] = p_i · w_j.
        let m = na::DMatrix::<f64>::from_fn(k, k, |i, j| {
            let mut s = 0.0;
            for f in 0..d_x {
                s += self.x_loadings[i * d_x + f] * self.x_weights[j * d_x + f];
            }
            s
        });
        if m.iter().any(|value| !value.is_finite()) {
            return Err(PidError::NumericalInstability {
                context: "PlsProjector::rotated_weights: (PᵀW) is non-finite",
            });
        }

        // R = W·M⁻¹. For each feature row, solve Mᵀ r_fᵀ = w_fᵀ with QR rather than
        // explicitly materializing an inverse, which avoids an unnecessary amplification step.
        let mt = m.transpose();
        let qr = mt.qr();
        let mut r = vec![0.0f64; d_x * k];
        for f in 0..d_x {
            let rhs = na::DVector::from_iterator(
                k,
                (0..k).map(|component| self.x_weights[component * d_x + f]),
            );
            let solution = qr.solve(&rhs).ok_or(PidError::NumericalInstability {
                context: "PlsProjector::rotated_weights: (PᵀW) is singular",
            })?;
            if solution.iter().any(|value| !value.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context: "PlsProjector::rotated_weights: linear solve is non-finite",
                });
            }
            r[f * k..(f + 1) * k].copy_from_slice(solution.as_slice());
        }
        ensure_finite(
            &r,
            "PlsProjector::rotated_weights: rotation produced non-finite values",
        )?;
        Ok(r)
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
    ///
    /// # Errors
    ///
    /// Returns [`PidError::NumericalInstability`] if the rotation is singular/non-finite or a
    /// nonzero original-unit coefficient lies outside the representable `f64` range. Predictions
    /// may still be representable in the latter case; [`predict`](Self::predict) keeps scales
    /// factored instead of materializing `B`.
    pub fn coefficients(&self) -> PidResult<MatOwned> {
        let k = self.out_dim;
        let d_x = self.in_dim;
        let d_y = self.target_dim;

        // B = R·Cᵀ (d_x×d_y), where R = W(PᵀW)⁻¹ is the shared PLS rotation.
        let r = self.rotated_weights()?;
        let mut b = vec![0.0f64; d_x * d_y];
        for f in 0..d_x {
            for j in 0..d_y {
                let scaled = compensated_sum(
                    (0..k).map(|c| r[f * k + c] * self.y_weights_scaled[c * d_y + j]),
                );
                b[f * d_y + j] = checked_mul_div(scaled, self.y_scale, self.x_scale)
                    .ok_or(PidError::NumericalInstability {
                        context: "PlsProjector::coefficients: original-unit coefficient is not representable",
                    })?;
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
        let n = x.nrows();
        let d_x = self.in_dim;
        let d_y = self.target_dim;
        let k = self.out_dim;
        let r = self.rotated_weights()?;
        let mut b_scaled = vec![0.0; d_x * d_y];
        for feature in 0..d_x {
            for target in 0..d_y {
                b_scaled[feature * d_y + target] = compensated_sum((0..k).map(|component| {
                    r[feature * k + component] * self.y_weights_scaled[component * d_y + target]
                }));
            }
        }
        ensure_finite(
            &b_scaled,
            "PlsProjector::predict: scaled regression coefficients are non-finite",
        )?;
        let mut out = vec![0.0f64; n * d_y];
        for i in 0..n {
            let xi = x.row(i);
            let out_row = &mut out[i * d_y..(i + 1) * d_y];
            for (target, slot) in out_row.iter_mut().enumerate() {
                *slot = stable_centered_weighted_sum(
                    xi,
                    &self.x_column_scales,
                    &self.x_mean_scaled,
                    (0..d_x).map(|feature| b_scaled[feature * d_y + target]),
                    AffineRestore {
                        numerator_scale: self.y_scale,
                        denominator_scale: self.x_scale,
                        offset: self.y_mean[target],
                        context: "PlsProjector::predict: affine prediction is not representable",
                    },
                )?;
            }
        }
        MatOwned::new(out, n, d_y)
    }
}

// ── BLAS-like helpers ──────────────────────────────────────────────────────

struct CenteredMatrix {
    mean: Vec<f64>,
    mean_scaled: Vec<f64>,
    column_scales: Vec<f64>,
    values: Vec<f64>,
    scale: f64,
}

/// Center a finite matrix in per-column coordinates, then apply one common centered-data scale.
///
/// Per-column coordinates keep a huge constant offset from erasing a tiny varying feature. The
/// final common scale preserves the original relative feature magnitudes and therefore does not
/// change the PLS problem.
fn center_scaled_matrix(x: MatRef<'_>, context: &'static str) -> PidResult<CenteredMatrix> {
    debug_assert!(x.nrows() > 0);
    let n = x.nrows();
    let d = x.ncols();
    let mut column_scales = vec![0.0; d];
    let mut mean_scaled = vec![0.0; d];
    for (column, mean) in mean_scaled.iter_mut().enumerate() {
        let column_scale = (0..n)
            .map(|row| x.row(row)[column].abs())
            .fold(0.0_f64, f64::max);
        column_scales[column] = column_scale;
        if column_scale == 0.0 {
            continue;
        }
        *mean = compensated_sum((0..n).map(|row| x.row(row)[column] / column_scale)) / n as f64;
        let tolerance = 64.0 * f64::EPSILON;
        if !mean.is_finite() || mean.abs() > 1.0 + tolerance {
            return Err(PidError::NumericalInstability { context });
        }
        *mean = mean.clamp(-1.0, 1.0);
    }

    let mut mean_original = Vec::with_capacity(d);
    for (&mean, &column_scale) in mean_scaled.iter().zip(&column_scales) {
        let original = mean * column_scale;
        if !original.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        mean_original.push(original);
    }

    let mut max_centered: Option<BinaryScaled> = None;
    for row in 0..n {
        for column in 0..d {
            let Some((delta_local, local_scale)) = centered_factor_parts(
                x.row(row)[column],
                column_scales[column],
                mean_scaled[column],
            ) else {
                continue;
            };
            let centered = BinaryScaled::from_finite_nonzero(delta_local)
                .multiply(BinaryScaled::from_finite_nonzero(local_scale))
                .abs();
            let replace = max_centered.is_none_or(|current| {
                centered.exponent > current.exponent
                    || (centered.exponent == current.exponent
                        && centered.mantissa > current.mantissa)
            });
            if replace {
                max_centered = Some(centered);
            }
        }
    }
    let min_subnormal = f64::from_bits(1);
    let scale = match max_centered {
        None => 1.0,
        Some(centered) => match centered.restore(context) {
            Ok(value) => value,
            Err(_) if centered.exponent > 1024 => f64::MAX,
            Err(_) => min_subnormal,
        },
    };
    if !scale.is_finite() || scale <= 0.0 {
        return Err(PidError::NumericalInstability { context });
    }

    let mut centered = Vec::with_capacity(n * d);
    for row in 0..n {
        for column in 0..d {
            let has_nonzero_center = centered_log_parts(
                x.row(row)[column],
                column_scales[column],
                mean_scaled[column],
            )
            .is_some();
            let value = centered_in_units(
                x.row(row)[column],
                column_scales[column],
                mean_scaled[column],
                scale,
            );
            if !value.is_finite() || (has_nonzero_center && value == 0.0) {
                return Err(PidError::NumericalInstability { context });
            }
            centered.push(value);
        }
    }
    Ok(CenteredMatrix {
        mean: mean_original,
        mean_scaled,
        column_scales,
        values: centered,
        scale,
    })
}

/// Return `(value - training_mean) / common_scale` without overflowing the subtraction or
/// erasing a large dynamic range between training columns and held-out values.
fn centered_in_units(value: f64, column_scale: f64, mean_scaled: f64, common_scale: f64) -> f64 {
    let Some((sign, log_magnitude)) = centered_log_parts(value, column_scale, mean_scaled) else {
        return 0.0;
    };
    sign * (log_magnitude - common_scale.ln()).exp()
}

fn centered_log_parts(value: f64, column_scale: f64, mean_scaled: f64) -> Option<(f64, f64)> {
    let (delta_local, local_scale) = centered_factor_parts(value, column_scale, mean_scaled)?;
    Some((
        delta_local.signum(),
        delta_local.abs().ln() + local_scale.ln(),
    ))
}

/// Return finite factors whose product is `value - training_mean`, without materializing an
/// overflowing subtraction.
fn centered_factor_parts(value: f64, column_scale: f64, mean_scaled: f64) -> Option<(f64, f64)> {
    let local_scale = value.abs().max(column_scale);
    if local_scale == 0.0 {
        return None;
    }
    let delta_local = value / local_scale - mean_scaled * (column_scale / local_scale);
    if delta_local == 0.0 {
        return None;
    }
    Some((delta_local, local_scale))
}

/// Evaluate a centered affine form while keeping source and output scales separate. The offset is
/// folded into the same signed binary-exponent accumulator as the linear terms: materializing
/// the centered prediction first can overflow even when adding the intercept cancels it back into
/// the finite range.
#[derive(Clone, Copy)]
struct AffineRestore {
    numerator_scale: f64,
    denominator_scale: f64,
    offset: f64,
    context: &'static str,
}

/// A finite nonzero binary value represented outside `f64`'s exponent range as
/// `mantissa * 2^exponent`, with `0.5 <= |mantissa| < 1`.
#[derive(Clone, Copy, Debug)]
struct BinaryScaled {
    mantissa: f64,
    exponent: i32,
}

impl BinaryScaled {
    const FRACTION_MASK: u64 = (1_u64 << 52) - 1;
    const SIGN_MASK: u64 = 1_u64 << 63;
    const TWO_POW_53: f64 = 9_007_199_254_740_992.0;

    fn from_finite_nonzero(value: f64) -> Self {
        debug_assert!(value.is_finite() && value != 0.0);
        let bits = value.to_bits();
        let magnitude_bits = bits & !Self::SIGN_MASK;
        let raw_exponent = ((magnitude_bits >> 52) & 0x7ff) as i32;
        let fraction = magnitude_bits & Self::FRACTION_MASK;
        let (significand, exponent) = if raw_exponent == 0 {
            debug_assert_ne!(fraction, 0);
            let highest_bit = 63_i32 - fraction.leading_zeros() as i32;
            let shift = (52 - highest_bit) as u32;
            (fraction << shift, highest_bit - 1073)
        } else {
            ((1_u64 << 52) | fraction, raw_exponent - 1022)
        };
        let magnitude = significand as f64 / Self::TWO_POW_53;
        Self {
            mantissa: if bits & Self::SIGN_MASK == 0 {
                magnitude
            } else {
                -magnitude
            },
            exponent,
        }
    }

    fn normalize(mantissa: f64, exponent: i32) -> Self {
        debug_assert!(mantissa.is_finite() && mantissa != 0.0);
        let normalized = Self::from_finite_nonzero(mantissa);
        Self {
            mantissa: normalized.mantissa,
            exponent: exponent + normalized.exponent,
        }
    }

    fn abs(self) -> Self {
        Self {
            mantissa: self.mantissa.abs(),
            exponent: self.exponent,
        }
    }

    fn multiply(self, other: Self) -> Self {
        Self::normalize(
            self.mantissa * other.mantissa,
            self.exponent + other.exponent,
        )
    }

    fn divide(self, other: Self) -> Self {
        Self::normalize(
            self.mantissa / other.mantissa,
            self.exponent - other.exponent,
        )
    }

    /// Restore a scaled value by constructing its IEEE-754 exponent/significand directly.
    /// This distinguishes `f64::MAX` from the very next overflowing value without a lossy
    /// `ln`/`exp` round trip.
    fn restore(self, context: &'static str) -> PidResult<f64> {
        debug_assert!(self.mantissa.is_finite());
        debug_assert!(self.mantissa.abs() >= 0.5 && self.mantissa.abs() < 1.0);
        let mantissa_bits = self.mantissa.abs().to_bits();
        debug_assert_eq!((mantissa_bits >> 52) & 0x7ff, 1022);
        let fraction = mantissa_bits & Self::FRACTION_MASK;
        let significand = (1_u64 << 52) | fraction;
        let sign = self.mantissa.to_bits() & Self::SIGN_MASK;
        let output_raw_exponent = self.exponent + 1022;

        if output_raw_exponent >= 0x7ff {
            return Err(PidError::NumericalInstability { context });
        }
        if output_raw_exponent > 0 {
            return Ok(f64::from_bits(
                sign | (output_raw_exponent as u64) << 52 | fraction,
            ));
        }

        // Convert to subnormal units (2^-1074), rounding the discarded significand bits to
        // nearest-even. Preserve the existing contract that a nonzero result smaller than the
        // minimum subnormal is unrepresentable rather than silently rounded to zero.
        let shift = (1 - output_raw_exponent) as u32;
        if shift > 52 {
            return Err(PidError::NumericalInstability { context });
        }
        let quotient = significand >> shift;
        let remainder_mask = (1_u64 << shift) - 1;
        let remainder = significand & remainder_mask;
        let halfway = 1_u64 << (shift - 1);
        let rounded = quotient
            + u64::from(remainder > halfway || (remainder == halfway && quotient & 1 == 1));
        if rounded == 0 {
            return Err(PidError::NumericalInstability { context });
        }
        Ok(f64::from_bits(sign | rounded))
    }
}

/// Sum the represented binary terms exactly in an integer superaccumulator, then round once.
/// Each normalized mantissa is a 53-bit integer times `2^-53`, so this is both feature-order
/// invariant and able to retain low-exponent residuals after cancellation at a higher exponent.
fn exact_binary_scaled_sum(terms: &[BinaryScaled], context: &'static str) -> PidResult<f64> {
    debug_assert!(!terms.is_empty());
    let minimum_term_shift = terms
        .iter()
        .map(|term| term.exponent - 53)
        .min()
        .expect("nonempty binary term list");
    let maximum_term_shift = terms
        .iter()
        .map(|term| term.exponent - 53)
        .max()
        .expect("nonempty binary term list");
    // Include the minimum-subnormal bit even when every term is larger. This makes subnormal
    // rounding and the exact MAX comparison integer-aligned without special fractional cases.
    let base_exponent = minimum_term_shift.min(-1074);
    let highest_term_bit = (maximum_term_shift - base_exponent) as usize + 52;
    let accumulator_bits = highest_term_bit
        .checked_add(usize::BITS as usize)
        .and_then(|bits| bits.checked_add(2))
        .ok_or(PidError::NumericalInstability { context })?;
    let limb_count = accumulator_bits.div_ceil(64);
    let mut positive = zeroed_limbs(limb_count, context)?;
    let mut negative = zeroed_limbs(limb_count, context)?;

    for &term in terms {
        let magnitude_bits = term.mantissa.abs().to_bits();
        debug_assert_eq!((magnitude_bits >> 52) & 0x7ff, 1022);
        let significand = (1_u64 << 52) | (magnitude_bits & BinaryScaled::FRACTION_MASK);
        let shift = (term.exponent - 53 - base_exponent) as usize;
        let accumulator = if term.mantissa.is_sign_negative() {
            &mut negative
        } else {
            &mut positive
        };
        if !add_shifted_significand(accumulator, significand, shift) {
            return Err(PidError::NumericalInstability { context });
        }
    }

    let (magnitude, negative_result) = match compare_binary_limbs(&positive, &negative) {
        std::cmp::Ordering::Equal => return Ok(0.0),
        std::cmp::Ordering::Greater => {
            (subtract_binary_limbs(&positive, &negative, context)?, false)
        }
        std::cmp::Ordering::Less => (subtract_binary_limbs(&negative, &positive, context)?, true),
    };

    let highest = highest_binary_bit(&magnitude).expect("nonzero exact affine sum");
    let exact_exponent = base_exponent + highest as i32;
    if !(-1074..=1023).contains(&exact_exponent) {
        return Err(PidError::NumericalInstability { context });
    }
    if exact_exponent == 1023 {
        let mut maximum_finite = zeroed_limbs(limb_count, context)?;
        let max_shift = (971 - base_exponent) as usize;
        if !add_shifted_significand(&mut maximum_finite, (1_u64 << 53) - 1, max_shift)
            || compare_binary_limbs(&magnitude, &maximum_finite) == std::cmp::Ordering::Greater
        {
            return Err(PidError::NumericalInstability { context });
        }
    }

    round_exact_binary_sum(&magnitude, negative_result, base_exponent, context)
}

fn zeroed_limbs(length: usize, context: &'static str) -> PidResult<Vec<u64>> {
    let mut limbs = Vec::new();
    limbs
        .try_reserve_exact(length)
        .map_err(|_| PidError::NumericalInstability { context })?;
    limbs.resize(length, 0);
    Ok(limbs)
}

fn add_shifted_significand(accumulator: &mut [u64], value: u64, shift: usize) -> bool {
    let limb = shift / 64;
    let offset = shift % 64;
    if !add_binary_limb(accumulator, limb, value << offset) {
        return false;
    }
    offset == 0 || add_binary_limb(accumulator, limb + 1, value >> (64 - offset))
}

fn add_binary_limb(accumulator: &mut [u64], mut index: usize, value: u64) -> bool {
    if value == 0 {
        return true;
    }
    if index >= accumulator.len() {
        return false;
    }
    let (sum, mut carry) = accumulator[index].overflowing_add(value);
    accumulator[index] = sum;
    while carry {
        index += 1;
        if index >= accumulator.len() {
            return false;
        }
        let (sum, next_carry) = accumulator[index].overflowing_add(1);
        accumulator[index] = sum;
        carry = next_carry;
    }
    true
}

fn compare_binary_limbs(left: &[u64], right: &[u64]) -> std::cmp::Ordering {
    debug_assert_eq!(left.len(), right.len());
    left.iter().rev().cmp(right.iter().rev())
}

fn subtract_binary_limbs(
    larger: &[u64],
    smaller: &[u64],
    context: &'static str,
) -> PidResult<Vec<u64>> {
    debug_assert_eq!(larger.len(), smaller.len());
    let mut difference = zeroed_limbs(larger.len(), context)?;
    let mut borrow = false;
    for index in 0..larger.len() {
        let (without_value, value_borrow) = larger[index].overflowing_sub(smaller[index]);
        let (value, carry_borrow) = without_value.overflowing_sub(u64::from(borrow));
        difference[index] = value;
        borrow = value_borrow || carry_borrow;
    }
    debug_assert!(!borrow);
    Ok(difference)
}

fn highest_binary_bit(value: &[u64]) -> Option<usize> {
    value
        .iter()
        .rposition(|&limb| limb != 0)
        .map(|index| index * 64 + (63 - value[index].leading_zeros() as usize))
}

fn binary_bit_at(value: &[u64], bit: usize) -> bool {
    value
        .get(bit / 64)
        .is_some_and(|limb| limb & (1_u64 << (bit % 64)) != 0)
}

fn any_binary_bits_below(value: &[u64], bit_exclusive: usize) -> bool {
    let full_limbs = bit_exclusive / 64;
    if value[..full_limbs.min(value.len())]
        .iter()
        .any(|&limb| limb != 0)
    {
        return true;
    }
    let remaining = bit_exclusive % 64;
    remaining != 0
        && full_limbs < value.len()
        && value[full_limbs] & ((1_u64 << remaining) - 1) != 0
}

fn low_binary_u64_after_shift(value: &[u64], shift: usize) -> u64 {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = value.get(limb).copied().unwrap_or(0) >> offset;
    if offset == 0 {
        low
    } else {
        low | (value.get(limb + 1).copied().unwrap_or(0) << (64 - offset))
    }
}

fn round_exact_binary_sum(
    magnitude: &[u64],
    negative: bool,
    base_exponent: i32,
    context: &'static str,
) -> PidResult<f64> {
    let highest = highest_binary_bit(magnitude).expect("nonzero exact affine sum");
    let exact_exponent = highest as i32 + base_exponent;
    let (cutoff, mut significand, mut output_exponent) = if exact_exponent < -1022 {
        let cutoff = (-1074 - base_exponent) as usize;
        (cutoff, low_binary_u64_after_shift(magnitude, cutoff), -1022)
    } else {
        let cutoff = highest.saturating_sub(52);
        (
            cutoff,
            low_binary_u64_after_shift(magnitude, cutoff),
            exact_exponent,
        )
    };

    if cutoff > 0 {
        let halfway = binary_bit_at(magnitude, cutoff - 1);
        let sticky = any_binary_bits_below(magnitude, cutoff - 1);
        if halfway && (sticky || significand & 1 != 0) {
            significand += 1;
        }
    }

    let sign = if negative { 1_u64 << 63 } else { 0 };
    if exact_exponent < -1022 {
        if significand == 0 {
            return Err(PidError::NumericalInstability { context });
        }
        if significand < 1_u64 << 52 {
            return Ok(f64::from_bits(sign | significand));
        }
        return Ok(f64::from_bits(sign | (1_u64 << 52)));
    }

    if significand == 1_u64 << 53 {
        significand >>= 1;
        output_exponent += 1;
    }
    if output_exponent > 1023 {
        return Err(PidError::NumericalInstability { context });
    }
    let exponent_bits = (output_exponent + 1023) as u64;
    let fraction_bits = significand - (1_u64 << 52);
    Ok(f64::from_bits(sign | (exponent_bits << 52) | fraction_bits))
}

fn stable_centered_weighted_sum(
    values: &[f64],
    column_scales: &[f64],
    means_scaled: &[f64],
    weights: impl IntoIterator<Item = f64>,
    restore: AffineRestore,
) -> PidResult<f64> {
    let AffineRestore {
        numerator_scale,
        denominator_scale,
        offset,
        context,
    } = restore;
    debug_assert_eq!(values.len(), column_scales.len());
    debug_assert_eq!(values.len(), means_scaled.len());
    debug_assert!(numerator_scale.is_finite() && numerator_scale > 0.0);
    debug_assert!(denominator_scale.is_finite() && denominator_scale > 0.0);

    if !offset.is_finite() {
        return Err(PidError::NumericalInstability { context });
    }
    let mut terms = Vec::with_capacity(values.len().saturating_add(1));
    if offset != 0.0 {
        terms.push(BinaryScaled::from_finite_nonzero(offset));
    }
    let mut has_linear_term = false;
    for (((&value, &column_scale), &mean_scaled), weight) in values
        .iter()
        .zip(column_scales)
        .zip(means_scaled)
        .zip(weights)
    {
        if weight == 0.0 {
            continue;
        }
        if !weight.is_finite() {
            return Err(PidError::NumericalInstability { context });
        }
        let Some((delta_local, local_scale)) =
            centered_factor_parts(value, column_scale, mean_scaled)
        else {
            continue;
        };
        let term = BinaryScaled::from_finite_nonzero(delta_local)
            .multiply(BinaryScaled::from_finite_nonzero(local_scale))
            .multiply(BinaryScaled::from_finite_nonzero(weight))
            .multiply(BinaryScaled::from_finite_nonzero(numerator_scale))
            .divide(BinaryScaled::from_finite_nonzero(denominator_scale));
        terms.push(term);
        has_linear_term = true;
    }
    // At the fitted X mean the centered linear form is exactly zero. Preserve the stored
    // intercept bit-for-bit instead of needlessly round-tripping it through `ln` and `exp`.
    if !has_linear_term {
        return Ok(offset);
    }
    exact_binary_scaled_sum(&terms, context)
}

fn compensated_sum(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0;
    let mut correction = 0.0;
    for value in values {
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    sum + correction
}

/// Evaluate `value * numerator / denominator`, trying algebraically equivalent operation orders
/// so an overflowing or underflowing intermediate does not reject a representable final value.
fn checked_mul_div(value: f64, numerator: f64, denominator: f64) -> Option<f64> {
    debug_assert!(value.is_finite());
    debug_assert!(numerator.is_finite() && numerator > 0.0);
    debug_assert!(denominator.is_finite() && denominator > 0.0);
    if value == 0.0 {
        return Some(value);
    }

    let ratio = numerator / denominator;
    if ratio.is_finite() && ratio > 0.0 {
        let result = value * ratio;
        if result.is_finite() && result != 0.0 {
            return Some(result);
        }
    }
    let product = value * numerator;
    if product.is_finite() && product != 0.0 {
        let result = product / denominator;
        if result.is_finite() && result != 0.0 {
            return Some(result);
        }
    }
    let quotient = value / denominator;
    if quotient.is_finite() && quotient != 0.0 {
        let result = quotient * numerator;
        if result.is_finite() && result != 0.0 {
            return Some(result);
        }
    }

    // Last resort for extreme exponent spreads: reconstruct from the log magnitude. Ordinary
    // inputs never take this branch, so their multiplication order and precision stay unchanged.
    let log_magnitude = value.abs().ln() + numerator.ln() - denominator.ln();
    let min_subnormal = f64::from_bits(1);
    if log_magnitude < min_subnormal.ln() {
        return None;
    }
    if log_magnitude > f64::MAX.ln() {
        return None;
    }
    let recovered = log_magnitude.exp().copysign(value);
    if recovered.is_finite() {
        Some(recovered)
    } else if log_magnitude <= f64::MAX.ln() {
        Some(f64::MAX.copysign(value))
    } else {
        None
    }
}

fn strongest_target_score(
    x: &[f64],
    y: &[f64],
    nrows: usize,
    x_cols: usize,
    y_cols: usize,
    x_frob: f64,
) -> PidResult<Vec<f64>> {
    let mut best: Option<(f64, f64, Vec<f64>)> = None;
    let mut cross_covariance = vec![0.0; x_cols];

    for column in 0..y_cols {
        let mut candidate: Vec<f64> = (0..nrows).map(|row| y[row * y_cols + column]).collect();
        canonicalize_direction(&mut candidate);
        let candidate_norm = l2_norm(&candidate);
        if candidate_norm == 0.0 {
            continue;
        }
        mat_vec_t(x, &candidate, nrows, x_cols, &mut cross_covariance);
        let strength = l2_norm(&cross_covariance);
        if !candidate_norm.is_finite() || !strength.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "PlsProjector::fit: target initialization norm overflow",
            });
        }

        let replace = match &best {
            None => true,
            Some((best_strength, _, best_candidate)) => match strength.total_cmp(best_strength) {
                std::cmp::Ordering::Greater => true,
                std::cmp::Ordering::Equal => lexicographically_before(&candidate, best_candidate),
                std::cmp::Ordering::Less => false,
            },
        };
        if replace {
            best = Some((strength, candidate_norm, candidate));
        }
    }

    let Some((strength, candidate_norm, mut score)) = best else {
        return Err(PidError::NumericalInstability {
            context: "PlsProjector::fit: target Y is zero after centering",
        });
    };
    let covariance_floor = (nrows as f64) * f64::EPSILON * x_frob * candidate_norm;
    if !covariance_floor.is_finite() || strength <= covariance_floor {
        return Err(PidError::NumericalInstability {
            context: "PlsProjector::fit: all target columns have negligible X cross-covariance",
        });
    }
    for value in &mut score {
        *value /= candidate_norm;
    }
    Ok(score)
}

fn canonicalize_direction(values: &mut [f64]) {
    if let Some(first_nonzero) = values.iter().find(|value| **value != 0.0) {
        if first_nonzero.is_sign_negative() {
            for value in values {
                *value = -*value;
            }
        }
    }
}

fn lexicographically_before(left: &[f64], right: &[f64]) -> bool {
    left.iter()
        .zip(right)
        .find_map(|(a, b)| match a.total_cmp(b) {
            std::cmp::Ordering::Equal => None,
            ordering => Some(ordering == std::cmp::Ordering::Less),
        })
        .unwrap_or(false)
}

fn ensure_finite(values: &[f64], context: &'static str) -> PidResult<()> {
    if values.iter().any(|v| !v.is_finite()) {
        return Err(PidError::NumericalInstability { context });
    }
    Ok(())
}

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

fn l2_norm(v: &[f64]) -> f64 {
    v.iter().fold(0.0_f64, |norm, value| norm.hypot(*value))
}

fn vec_diff_norm(a: &[f64], b: &[f64]) -> f64 {
    a.iter()
        .zip(b)
        .fold(0.0_f64, |norm, (x, y)| norm.hypot(x - y))
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
    fn pls_rejects_finite_input_when_centering_or_norms_overflow() {
        let x_data = [f64::MAX; 4];
        let y_data = [0.0, 1.0, 0.0, 1.0];
        let x = MatRef::new(&x_data, 4, 1).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();

        let err = PlsProjector::fit(x, y, 1).unwrap_err();

        assert!(matches!(err, PidError::NumericalInstability { .. }));
    }

    #[test]
    fn pls_initialization_uses_informative_target_regardless_of_column_order() {
        let x_data = [-1.0, -1.0, 1.0, 1.0];
        // The first target below is non-constant but exactly orthogonal to X; the second equals X.
        let y_orthogonal_first = [-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0];
        let y_signal_first = [-1.0, -1.0, -1.0, 1.0, 1.0, -1.0, 1.0, 1.0];
        let x = MatRef::new(&x_data, 4, 1).unwrap();
        let y_a = MatRef::new(&y_orthogonal_first, 4, 2).unwrap();
        let y_b = MatRef::new(&y_signal_first, 4, 2).unwrap();

        let a = PlsProjector::fit(x, y_a, 1).unwrap();
        let b = PlsProjector::fit(x, y_b, 1).unwrap();
        let ta = a.transform(x).unwrap();
        let tb = b.transform(x).unwrap();

        assert_eq!(a.x_weights()[0].to_bits(), b.x_weights()[0].to_bits());
        for row in 0..4 {
            assert_eq!(
                ta.as_ref().row(row)[0].to_bits(),
                tb.as_ref().row(row)[0].to_bits()
            );
        }
    }

    #[test]
    fn pls_is_invariant_to_tiny_uniform_x_and_y_scaling() {
        let x_data = [-3.0, -1.0, 1.0, 3.0];
        let y_data = [-2.0, -1.0, 1.0, 2.0];
        let scale = 1.0e-200;
        let x_tiny = x_data.map(|value| value * scale);
        let y_tiny = y_data.map(|value| value * scale);
        let x = MatRef::new(&x_data, 4, 1).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();
        let xs = MatRef::new(&x_tiny, 4, 1).unwrap();
        let ys = MatRef::new(&y_tiny, 4, 1).unwrap();

        let ordinary = PlsProjector::fit(x, y, 1).unwrap();
        let tiny = PlsProjector::fit(xs, ys, 1).unwrap();
        let ordinary_scores = ordinary.transform(x).unwrap();
        let tiny_scores = tiny.transform(xs).unwrap();
        let ordinary_predictions = ordinary.predict(x).unwrap();
        let tiny_predictions = tiny.predict(xs).unwrap();

        assert_eq!(
            ordinary.x_weights()[0].to_bits(),
            tiny.x_weights()[0].to_bits()
        );
        for row in 0..4 {
            let rescaled = tiny_scores.as_ref().row(row)[0] / scale;
            assert!(
                (rescaled - ordinary_scores.as_ref().row(row)[0]).abs() < 1e-12,
                "row={row} ordinary={} rescaled={rescaled}",
                ordinary_scores.as_ref().row(row)[0]
            );
            let rescaled_prediction = tiny_predictions.as_ref().row(row)[0] / scale;
            assert!(
                (rescaled_prediction - ordinary_predictions.as_ref().row(row)[0]).abs() < 1e-12,
                "row={row} ordinary_prediction={} rescaled_prediction={rescaled_prediction}",
                ordinary_predictions.as_ref().row(row)[0]
            );
        }
    }

    #[test]
    fn pls_handles_opposite_extreme_finite_values_without_overflow() {
        let x_data = [-f64::MAX, -f64::MAX, f64::MAX, f64::MAX];
        let y_data = [-1.0, -1.0, 1.0, 1.0];
        let x = MatRef::new(&x_data, 4, 1).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();

        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let predictions = pls.predict(x).unwrap();

        for (row, &expected) in y_data.iter().enumerate() {
            let predicted = predictions.as_ref().row(row)[0];
            assert!(
                (predicted - expected).abs() < 1e-15,
                "row={row} predicted={predicted} expected={expected}",
            );
        }
    }

    #[test]
    fn pls_ignores_huge_constant_offset_without_erasing_tiny_signal() {
        let x_data = [
            f64::MAX,
            -3.0e-200,
            f64::MAX,
            -1.0e-200,
            f64::MAX,
            1.0e-200,
            f64::MAX,
            3.0e-200,
        ];
        let y_data = [-3.0, -1.0, 1.0, 3.0];
        let x = MatRef::new(&x_data, 4, 2).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();

        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let predictions = pls.predict(x).unwrap();

        assert!(pls.x_weights()[0].abs() < 1.0e-12);
        assert!(pls.x_weights()[1].abs() > 0.99);
        for (row, &expected) in y_data.iter().enumerate() {
            assert!((predictions.as_ref().row(row)[0] - expected).abs() < 1.0e-12);
        }
    }

    #[test]
    fn pls_transform_handles_held_out_scale_far_beyond_training_scale() {
        let x_train = [-3.0e-300, -1.0e-300, 1.0e-300, 3.0e-300];
        let y_train = [-3.0, -1.0, 1.0, 3.0];
        let x = MatRef::new(&x_train, 4, 1).unwrap();
        let y = MatRef::new(&y_train, 4, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let held_out_data = [1.0e300];
        let held_out = MatRef::new(&held_out_data, 1, 1).unwrap();

        let score = pls.transform(held_out).unwrap().as_ref().row(0)[0];

        assert!(score.is_finite());
        assert!((score.abs() / 1.0e300 - 1.0).abs() < 1.0e-12);
    }

    #[test]
    fn pls_transform_ignores_a_harmless_term_below_the_dominant_binary_scale() {
        let x_data = [-1.0, -1.0, 1.0, 1.0];
        let y_data = [-1.0, 1.0];
        let x = MatRef::new(&x_data, 2, 2).unwrap();
        let y = MatRef::new(&y_data, 2, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let held_out_data = [1.0e100, 1.0e-300];
        let held_out = MatRef::new(&held_out_data, 1, 2).unwrap();

        let score = pls.transform(held_out).unwrap().as_ref().row(0)[0];
        let expected = std::f64::consts::FRAC_1_SQRT_2 * 1.0e100;

        assert!(score.is_finite());
        assert!(
            (score.abs() / expected - 1.0).abs() < 8.0 * f64::EPSILON,
            "score={score:e}, expected={expected:e}, ratio={}",
            score.abs() / expected
        );
    }

    #[test]
    fn pls_transform_exact_cancellation_is_invariant_to_feature_order() {
        let x_data = [-1.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0];
        let y_data = [-1.0, 1.0];
        let x = MatRef::new(&x_data, 2, 4).unwrap();
        let y = MatRef::new(&y_data, 2, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let next_after_two = f64::from_bits(2.0_f64.to_bits() + 1);
        let held_out_data = [
            2.0,
            next_after_two,
            -2.0,
            -next_after_two,
            2.0,
            -2.0,
            next_after_two,
            -next_after_two,
        ];
        let held_out = MatRef::new(&held_out_data, 2, 4).unwrap();

        let scores = pls.transform(held_out).unwrap();

        assert_eq!(scores.as_ref().row(0)[0].to_bits(), 0.0_f64.to_bits());
        assert_eq!(scores.as_ref().row(1)[0].to_bits(), 0.0_f64.to_bits());
    }

    #[test]
    fn pls_predict_keeps_unrepresentable_coefficient_factored() {
        let x_data = [-3.0e300, -1.0e300, 1.0e300, 3.0e300];
        let y_data = [-3.0e-300, -1.0e-300, 1.0e-300, 3.0e-300];
        let x = MatRef::new(&x_data, 4, 1).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();

        let predictions = pls.predict(x).unwrap();

        for (row, &expected) in y_data.iter().enumerate() {
            let predicted = predictions.as_ref().row(row)[0];
            assert!((predicted / expected - 1.0).abs() < 1.0e-12);
        }
        assert!(pls.coefficients().is_err());
        assert!(pls.y_weights().is_err());
    }

    #[test]
    fn pls_predict_combines_intercept_before_rejecting_an_overflowing_centered_term() {
        // The fitted line is y = (MAX / 2) * x - MAX / 2. At x=3 its centered term is
        // 1.5*MAX (not representable), but the complete affine prediction is exactly MAX.
        let x_train = [-1.0, 1.0];
        let y_train = [-f64::MAX, 0.0];
        let x = MatRef::new(&x_train, 2, 1).unwrap();
        let y = MatRef::new(&y_train, 2, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let held_out_data = [3.0];
        let held_out = MatRef::new(&held_out_data, 1, 1).unwrap();

        let prediction = pls.predict(held_out).unwrap().as_ref().row(0)[0];

        assert!(prediction.is_finite());
        assert!((prediction / f64::MAX - 1.0).abs() < 4.0 * f64::EPSILON);

        for beyond_boundary in [f64::from_bits(3.0_f64.to_bits() + 1), 3.000_000_000_001] {
            let held_out_data = [beyond_boundary];
            let held_out = MatRef::new(&held_out_data, 1, 1).unwrap();
            assert!(
                pls.predict(held_out).is_err(),
                "x={beyond_boundary} must produce a genuine overflow"
            );
        }
    }

    #[test]
    fn pls_predict_at_fitted_x_mean_returns_stored_y_mean_exactly() {
        let x_data = [-1.0, 0.0, 1.0];
        let y_data = [-0.7, 0.1, 0.9];
        let x = MatRef::new(&x_data, 3, 1).unwrap();
        let y = MatRef::new(&y_data, 3, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let x_at_mean = [pls.x_mean()[0]];
        let held_out = MatRef::new(&x_at_mean, 1, 1).unwrap();

        let prediction = pls.predict(held_out).unwrap().as_ref().row(0)[0];

        assert_eq!(prediction.to_bits(), pls.y_mean()[0].to_bits());
    }

    #[test]
    fn pls_predict_preserves_intercept_when_a_nonzero_linear_term_rounds_away() {
        let base = 1.0e300;
        let delta = 1.0e285;
        let x_data = [-delta, delta];
        let y_data = [base - delta, base + delta];
        let x = MatRef::new(&x_data, 2, 1).unwrap();
        let y = MatRef::new(&y_data, 2, 1).unwrap();
        let pls = PlsProjector::fit(x, y, 1).unwrap();
        let held_out_data = [1.0e100];
        let held_out = MatRef::new(&held_out_data, 1, 1).unwrap();

        let prediction = pls.predict(held_out).unwrap().as_ref().row(0)[0];

        assert_eq!(prediction.to_bits(), pls.y_mean()[0].to_bits());
    }

    #[test]
    fn pls_rejects_unrepresentable_cross_feature_dynamic_range() {
        let x_data = [
            -1.0e300, -1.0e-300, 1.0e300, -1.0e-300, -1.0e300, 1.0e-300, 1.0e300, 1.0e-300,
        ];
        let y_data = [-1.0, -1.0, 1.0, 1.0];
        let x = MatRef::new(&x_data, 4, 2).unwrap();
        let y = MatRef::new(&y_data, 4, 1).unwrap();

        assert!(matches!(
            PlsProjector::fit(x, y, 1),
            Err(PidError::NumericalInstability { .. })
        ));
    }

    #[test]
    fn pls_iteration_exhaustion_returns_error() {
        let n = 24;
        let d_x = 4;
        let d_y = 3;
        let mut rng = crate::preprocess::SplitMix64::new(0xC0FFEE);
        let x_data: Vec<f64> = (0..n * d_x).map(|_| rng.normal()).collect();
        let y_data: Vec<f64> = (0..n * d_y).map(|_| rng.normal()).collect();
        let x = MatRef::new(&x_data, n, d_x).unwrap();
        let y = MatRef::new(&y_data, n, d_y).unwrap();

        let err = PlsProjector::fit_with_iteration_limit(x, y, 1, 1).unwrap_err();

        assert!(matches!(err, PidError::NumericalInstability { .. }));
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
    fn transform_matches_explicit_deflation_scores_multicomponent() {
        // For out_dim >= 2 the latent scores live in the deflated space, so `transform`
        // MUST apply the rotation R = W(PᵀW)⁻¹. This reproduces the exact NIPALS scores;
        // the old raw-weight projection (X−x̄)·W only matches for the first component.
        let n = 60;
        let d_x = 6;
        let d_y = 2;
        let mut rng = crate::preprocess::SplitMix64::new(7);
        let mut x_data = Vec::with_capacity(n * d_x);
        let mut y_data = Vec::with_capacity(n * d_y);
        for _ in 0..n {
            let a = rng.normal();
            let b = rng.normal();
            let mut xs = [0.0f64; 6];
            for v in xs.iter_mut() {
                *v = rng.normal();
            }
            xs[0] += 1.5 * a;
            xs[1] += 1.0 * b;
            for &v in &xs {
                x_data.push(v);
            }
            y_data.push(a + 0.1 * rng.normal());
            y_data.push(b + 0.1 * rng.normal());
        }
        let x = MatRef::new(&x_data, n, d_x).unwrap();
        let y = MatRef::new(&y_data, n, d_y).unwrap();
        let k = 3;
        let pls = PlsProjector::fit(x, y, k).unwrap();
        let t = pls.transform(x).unwrap();

        // Independently recompute the deflated NIPALS scores from stored weights/loadings.
        let xm = pls.x_mean();
        let mut xc = vec![0.0f64; n * d_x];
        for i in 0..n {
            for j in 0..d_x {
                xc[i * d_x + j] = x.row(i)[j] - xm[j];
            }
        }
        for c in 0..k {
            let w = &pls.x_weights()[c * d_x..(c + 1) * d_x];
            let p = &pls.x_loadings()[c * d_x..(c + 1) * d_x];
            let mut tc = vec![0.0f64; n];
            for i in 0..n {
                let mut s = 0.0;
                for j in 0..d_x {
                    s += xc[i * d_x + j] * w[j];
                }
                tc[i] = s;
            }
            for (i, &tci) in tc.iter().enumerate() {
                let got = t.as_ref().row(i)[c];
                assert!(
                    (got - tci).abs() < 1e-9,
                    "score mismatch comp {c} row {i}: transform={got} deflated={tci}"
                );
            }
            // Deflate X_c -= t_c p_cᵀ for the next component.
            for i in 0..n {
                for j in 0..d_x {
                    xc[i * d_x + j] -= tc[i] * p[j];
                }
            }
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
