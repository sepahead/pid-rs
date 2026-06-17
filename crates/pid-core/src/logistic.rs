//! L2-regularized binary logistic regression via Newton–IRLS.
//!
//! This is the estimator primitive behind an **internal-feature failure-detector
//! baseline** (a SAFE-class baseline): a learned classifier on a policy's internal
//! embedding features that predicts the success/failure label. It exists so that
//! information-decomposition features can be held to an *added-value* standard — they
//! must beat strong learned baselines like this one, or the negative result is reported.
//!
//! # Method
//!
//! Maximizes the L2-penalized Bernoulli log-likelihood
//! `Σ_i [y_i log p_i + (1-y_i) log(1-p_i)] - (λ/2) ||w||²`, where
//! `p_i = sigmoid(x_i·w + b)`. The intercept `b` is **not** penalized. Optimization
//! is Newton's method (iteratively reweighted least squares): each step solves the
//! penalized normal equations `(XᵀWX + λR) Δ = Xᵀ(y - p) - λR β` with `W = diag(p(1-p))`
//! and `R = diag(0, 1, …, 1)`. With `λ > 0` the penalized Hessian is positive
//! definite, so the solve is via Cholesky (LU fallback) and perfect separation does
//! not blow the weights up.
//!
//! Fitting is fully deterministic (no randomness): identical inputs yield identical
//! coefficients. Cost is `O(iters · (n·d² + d³))`; for high-dimensional embeddings,
//! reduce first (e.g. PLS) before fitting.

use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use nalgebra as na;

/// Configuration for [`LogisticRegression::fit`].
#[derive(Debug, Clone, PartialEq)]
pub struct LogisticRegressionConfig {
    /// Ridge penalty `λ ≥ 0` applied to the weights (not the intercept).
    pub l2: f64,
    /// Maximum Newton iterations.
    pub max_iters: usize,
    /// Convergence tolerance on the Newton step infinity-norm.
    pub tol: f64,
}

impl Default for LogisticRegressionConfig {
    fn default() -> Self {
        Self {
            l2: 1.0,
            max_iters: 100,
            tol: 1e-8,
        }
    }
}

/// A fitted binary logistic-regression model.
#[derive(Debug, Clone, PartialEq)]
pub struct LogisticRegression {
    weights: Vec<f64>,
    intercept: f64,
    n_iters: usize,
    converged: bool,
}

fn sigmoid(z: f64) -> f64 {
    // Numerically stable logistic.
    if z >= 0.0 {
        1.0 / (1.0 + (-z).exp())
    } else {
        let e = z.exp();
        e / (1.0 + e)
    }
}

impl LogisticRegression {
    /// Fit the model on design matrix `x` (`n × d`) and boolean labels `y` (length `n`).
    ///
    /// # Errors
    /// Returns an error if dimensions mismatch, inputs are non-finite, the config is
    /// invalid, or the penalized Hessian is singular (only possible with `l2 == 0` on
    /// degenerate data).
    pub fn fit(x: MatRef<'_>, y: &[bool], cfg: &LogisticRegressionConfig) -> PidResult<Self> {
        let n = x.nrows();
        let d = x.ncols();
        if y.len() != n {
            return Err(PidError::RowCountMismatch {
                context: "LogisticRegression::fit",
                left_rows: n,
                right_rows: y.len(),
            });
        }
        if n == 0 || d == 0 {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::fit",
                message: "x must have at least one row and column",
            });
        }
        if !(cfg.l2.is_finite() && cfg.l2 >= 0.0) {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::fit",
                message: "l2 must be finite and >= 0",
            });
        }
        if cfg.max_iters == 0 || !(cfg.tol.is_finite() && cfg.tol > 0.0) {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::fit",
                message: "max_iters must be > 0 and tol must be finite and > 0",
            });
        }

        // Augmented design with an intercept column at index 0.
        let p = d + 1;
        let mut xa = na::DMatrix::<f64>::zeros(n, p);
        for i in 0..n {
            let row = x.row(i);
            xa[(i, 0)] = 1.0;
            for (j, &v) in row.iter().enumerate() {
                if !v.is_finite() {
                    return Err(PidError::InvalidConfig {
                        context: "LogisticRegression::fit",
                        message: "x must be finite",
                    });
                }
                xa[(i, j + 1)] = v;
            }
        }
        let yv = na::DVector::<f64>::from_iterator(n, y.iter().map(|&b| if b { 1.0 } else { 0.0 }));

        // Ridge selector: 0 for the intercept, l2 for the weights.
        let mut ridge = na::DVector::<f64>::from_element(p, cfg.l2);
        ridge[0] = 0.0;

        let mut beta = na::DVector::<f64>::zeros(p);
        let mut converged = false;
        let mut n_iters = 0;
        for iter in 0..cfg.max_iters {
            n_iters = iter + 1;
            // Predictions and IRLS weights.
            let eta = &xa * &beta;
            let pvec = eta.map(sigmoid);
            let w = pvec.map(|pi| (pi * (1.0 - pi)).max(1e-12));

            // Gradient of penalized NLL: Xᵀ(p - y) + λR β.
            let mut grad = xa.tr_mul(&(&pvec - &yv));
            for k in 0..p {
                grad[k] += ridge[k] * beta[k];
            }

            // Hessian: XᵀWX + λR.
            let xw = scale_rows(&xa, &w);
            let mut hess = xa.tr_mul(&xw);
            for k in 0..p {
                hess[(k, k)] += ridge[k];
            }

            // Solve H Δ = grad; β ← β − Δ (Newton step on the penalized NLL).
            let delta = solve_spd(&hess, &grad).ok_or(PidError::NumericalInstability {
                context: "LogisticRegression::fit: singular penalized Hessian (try l2 > 0)",
            })?;
            beta -= &delta;

            if delta.amax() < cfg.tol {
                converged = true;
                break;
            }
        }

        let intercept = beta[0];
        let weights = beta.rows(1, d).iter().copied().collect();
        Ok(Self {
            weights,
            intercept,
            n_iters,
            converged,
        })
    }

    /// Fitted weights (length `d`, intercept excluded).
    pub fn weights(&self) -> &[f64] {
        &self.weights
    }

    /// Fitted intercept.
    pub fn intercept(&self) -> f64 {
        self.intercept
    }

    /// Number of Newton iterations actually run.
    pub fn n_iters(&self) -> usize {
        self.n_iters
    }

    /// Whether the Newton iteration converged within `max_iters`.
    pub fn converged(&self) -> bool {
        self.converged
    }

    /// Decision-function logits `x·w + b` for each row (use for AUROC ranking).
    pub fn decision_function(&self, x: MatRef<'_>) -> PidResult<Vec<f64>> {
        if x.ncols() != self.weights.len() {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::decision_function",
                message: "x column count does not match fitted weights",
            });
        }
        Ok((0..x.nrows())
            .map(|i| {
                let row = x.row(i);
                self.intercept
                    + row
                        .iter()
                        .zip(&self.weights)
                        .map(|(a, b)| a * b)
                        .sum::<f64>()
            })
            .collect())
    }

    /// Predicted success probabilities `sigmoid(x·w + b)`.
    pub fn predict_proba(&self, x: MatRef<'_>) -> PidResult<Vec<f64>> {
        Ok(self
            .decision_function(x)?
            .into_iter()
            .map(sigmoid)
            .collect())
    }

    /// Hard predictions at the given probability `threshold` (e.g. 0.5).
    pub fn predict(&self, x: MatRef<'_>, threshold: f64) -> PidResult<Vec<bool>> {
        Ok(self
            .predict_proba(x)?
            .into_iter()
            .map(|p| p >= threshold)
            .collect())
    }
}

/// Multiply each row `i` of `m` by scalar `w[i]` (returns a new matrix).
fn scale_rows(m: &na::DMatrix<f64>, w: &na::DVector<f64>) -> na::DMatrix<f64> {
    let mut out = m.clone();
    for i in 0..m.nrows() {
        let wi = w[i];
        for j in 0..m.ncols() {
            out[(i, j)] *= wi;
        }
    }
    out
}

/// Solve `H x = b` for a symmetric positive-definite `H` (Cholesky, LU fallback).
fn solve_spd(h: &na::DMatrix<f64>, b: &na::DVector<f64>) -> Option<na::DVector<f64>> {
    if let Some(chol) = h.clone().cholesky() {
        return Some(chol.solve(b));
    }
    h.clone().lu().solve(b)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::matrix::MatOwned;
    use crate::preprocess::SplitMix64;

    /// Build an (n × d) matrix and labels from a linear logit rule with noise.
    fn make_logit_data(n: usize, true_w: &[f64], true_b: f64, seed: u64) -> (MatOwned, Vec<bool>) {
        let d = true_w.len();
        let mut rng = SplitMix64::new(seed);
        let mut data = Vec::with_capacity(n * d);
        let mut labels = Vec::with_capacity(n);
        for _ in 0..n {
            let mut logit = true_b;
            let mut row = Vec::with_capacity(d);
            for &wj in true_w {
                let xij = rng.normal();
                row.push(xij);
                logit += wj * xij;
            }
            data.extend_from_slice(&row);
            // Bernoulli draw from the true probability.
            let p = 1.0 / (1.0 + (-logit).exp());
            let u = (rng.next_u64() >> 11) as f64 / (1u64 << 53) as f64;
            labels.push(u < p);
        }
        (MatOwned::new(data, n, d).unwrap(), labels)
    }

    #[test]
    fn recovers_known_coefficients_sign_and_order() {
        // Large sample, light regularization: recovered weights should match the
        // true signs and rank the dominant feature highest.
        let true_w = [2.0, -1.0, 0.0];
        let (x, y) = make_logit_data(4000, &true_w, 0.5, 42);
        let cfg = LogisticRegressionConfig {
            l2: 1e-3,
            ..Default::default()
        };
        let model = LogisticRegression::fit(x.as_ref(), &y, &cfg).unwrap();
        assert!(model.converged());
        let w = model.weights();
        assert!(w[0] > 0.5, "w0={}", w[0]);
        assert!(w[1] < -0.2, "w1={}", w[1]);
        assert!(w[0].abs() > w[1].abs(), "dominant feature not largest");
        assert!(w[0].abs() > w[2].abs(), "noise feature too large");
        // Intercept recovered with the correct sign.
        assert!(model.intercept() > 0.0);
    }

    #[test]
    fn separable_data_stays_finite_with_ridge() {
        // Perfectly separable: x>0 -> true. Without ridge the MLE diverges; with
        // ridge the weights stay finite and the classifier separates the classes.
        let n = 200;
        let mut data = Vec::with_capacity(n);
        let mut y = Vec::with_capacity(n);
        for i in 0..n {
            let xv = (i as f64 - n as f64 / 2.0) / 10.0;
            data.push(xv);
            y.push(xv > 0.0);
        }
        let x = MatOwned::new(data, n, 1).unwrap();
        let model = LogisticRegression::fit(
            x.as_ref(),
            &y,
            &LogisticRegressionConfig {
                l2: 1.0,
                ..Default::default()
            },
        )
        .unwrap();
        assert!(model.weights()[0].is_finite());
        assert!(model.weights()[0] > 0.0);
        let preds = model.predict(x.as_ref(), 0.5).unwrap();
        let acc = preds.iter().zip(&y).filter(|(a, b)| a == b).count() as f64 / n as f64;
        assert!(acc > 0.95, "separable accuracy {acc}");
    }

    #[test]
    fn is_deterministic() {
        let true_w = [1.0, -0.5];
        let (x, y) = make_logit_data(500, &true_w, 0.0, 7);
        let cfg = LogisticRegressionConfig::default();
        let a = LogisticRegression::fit(x.as_ref(), &y, &cfg).unwrap();
        let b = LogisticRegression::fit(x.as_ref(), &y, &cfg).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn proba_in_unit_interval_and_threshold_consistent() {
        let true_w = [1.5, 0.0];
        let (x, y) = make_logit_data(300, &true_w, 0.0, 9);
        let model =
            LogisticRegression::fit(x.as_ref(), &y, &LogisticRegressionConfig::default()).unwrap();
        let proba = model.predict_proba(x.as_ref()).unwrap();
        assert!(proba.iter().all(|&p| (0.0..=1.0).contains(&p)));
        let preds = model.predict(x.as_ref(), 0.5).unwrap();
        for (p, pred) in proba.iter().zip(&preds) {
            assert_eq!(*pred, *p >= 0.5);
        }
        // Logits rank-correlate with probabilities (monotone link).
        let logits = model.decision_function(x.as_ref()).unwrap();
        for (lo, pr) in logits.iter().zip(&proba) {
            assert_eq!(*lo >= 0.0, *pr >= 0.5);
        }
    }

    #[test]
    fn rejects_mismatched_labels_and_bad_config() {
        let x = MatOwned::new(vec![1.0, 2.0, 3.0, 4.0], 2, 2).unwrap();
        assert!(
            LogisticRegression::fit(x.as_ref(), &[true], &LogisticRegressionConfig::default())
                .is_err()
        );
        assert!(LogisticRegression::fit(
            x.as_ref(),
            &[true, false],
            &LogisticRegressionConfig {
                l2: -1.0,
                ..Default::default()
            }
        )
        .is_err());
    }
}
