//! L2-regularized binary logistic regression via Newton–IRLS.
//!
//! # Method provenance and availability
//!
//! **PAPER-DERIVED CLASSICAL METHOD.** Logistic likelihood, iteratively reweighted least squares,
//! and ridge penalization are established methods. This deterministic implementation is available
//! under `experimental-pipelines` as an internal-feature baseline. Solver fallback, convergence
//! policy, resource limits, and failure reporting are project-defined engineering; no new
//! regression theory is claimed.
//!
//! Method catalog: regression.logistic-irls
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

use crate::bootstrap::CancellationToken;
use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::resource::{try_vec_filled, try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use nalgebra as na;

// nalgebra's dense factorizations allocate internally through infallible constructors. This
// experimental utility therefore combines aggregate preflight with a hard solver-dimension
// quarantine; it does not represent the preflight as an allocator-failure guarantee.
const MAX_NALGEBRA_LOGISTIC_COLUMNS: usize = 1024;

fn checked_add(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_add(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_mul(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
}

/// Configuration for [`LogisticRegression::fit`].
#[derive(Debug, Clone, PartialEq)]
#[non_exhaustive]
pub struct LogisticRegressionConfig {
    /// Ridge penalty `λ ≥ 0` applied to the weights (not the intercept).
    pub l2: f64,
    /// Maximum Newton iterations.
    pub max_iters: usize,
    /// Convergence tolerance on both the maximum fitted-logit change and Newton decrement.
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
#[derive(Debug, PartialEq)]
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
    /// invalid, the labels contain only one class, the penalized Hessian is singular (only
    /// possible with `l2 == 0` on degenerate data), or Newton iteration does not converge.
    pub fn fit(x: MatRef<'_>, y: &[bool], cfg: &LogisticRegressionConfig) -> PidResult<Self> {
        Self::fit_with_budget(x, y, cfg, ResourceBudget::default())
    }

    /// Estimate the conservative peak dense-IRLS heap and arithmetic work.
    ///
    /// The estimate assumes every input feature is active and includes nalgebra expression,
    /// factorization, and fallback-solver scratch. It does not allocate.
    pub fn fit_resource_estimate(
        x: MatRef<'_>,
        cfg: &LogisticRegressionConfig,
    ) -> PidResult<ResourceEstimate> {
        const OPERATION: &str = "LogisticRegression::fit";
        let n = x.nrows();
        let d = x.ncols();
        if n == 0 || d == 0 {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "x must have at least one row and column",
            });
        }
        if !(cfg.l2.is_finite() && cfg.l2 >= 0.0)
            || cfg.max_iters == 0
            || !(cfg.tol.is_finite() && cfg.tol > 0.0)
        {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "invalid ridge, iteration, or tolerance configuration",
            });
        }
        let p = d.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
        if p > MAX_NALGEBRA_LOGISTIC_COLUMNS {
            return Err(PidError::ResourceLimitExceeded {
                operation: OPERATION,
                resource: "nalgebra_solver_columns",
                requested: p as u128,
                limit: MAX_NALGEBRA_LOGISTIC_COLUMNS as u128,
            });
        }
        let n = n as u128;
        let p = p as u128;
        let dense_rows = checked_mul(OPERATION, n, p)?;
        let dense_square = checked_mul(OPERATION, p, p)?;
        let f64_elements = [
            checked_mul(OPERATION, 4, dense_rows)?,
            checked_mul(OPERATION, 8, dense_square)?,
            checked_mul(OPERATION, 10, checked_add(OPERATION, n, p)?)?,
        ]
        .into_iter()
        .try_fold(0_u128, |sum, value| checked_add(OPERATION, sum, value))?;
        let per_iteration = [
            checked_mul(OPERATION, n, checked_mul(OPERATION, p, p)?)?,
            checked_mul(OPERATION, p, checked_mul(OPERATION, p, p)?)?,
            checked_mul(OPERATION, 10, dense_rows)?,
        ]
        .into_iter()
        .try_fold(0_u128, |sum, value| checked_add(OPERATION, sum, value))?;
        Ok(ResourceEstimate {
            estimated_bytes: checked_mul(
                OPERATION,
                f64_elements,
                std::mem::size_of::<f64>() as u128,
            )?,
            pairwise_distances: 0,
            operations_hint: checked_mul(OPERATION, cfg.max_iters as u128, per_iteration)?,
        })
    }

    /// Fit under an explicit aggregate dense-solver budget.
    ///
    /// nalgebra still owns some internal infallible allocations. The solver dimension is hard
    /// capped and all documented dense scratch is preflighted, but allocator exhaustion below a
    /// caller's ceiling remains a limitation of this default-off experimental backend.
    pub fn fit_with_budget(
        x: MatRef<'_>,
        y: &[bool],
        cfg: &LogisticRegressionConfig,
        budget: ResourceBudget,
    ) -> PidResult<Self> {
        let cancellation = CancellationToken::new();
        Self::fit_with_budget_and_cancellation(x, y, cfg, budget, &cancellation)
    }

    /// [`Self::fit_with_budget`] with cooperative checks between Newton–IRLS iterations.
    pub fn fit_with_budget_and_cancellation(
        x: MatRef<'_>,
        y: &[bool],
        cfg: &LogisticRegressionConfig,
        budget: ResourceBudget,
        cancellation: &CancellationToken,
    ) -> PidResult<Self> {
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
        let has_positive = y.iter().any(|&label| label);
        let has_negative = y.iter().any(|&label| !label);
        if !(has_positive && has_negative) {
            // The intercept is intentionally unpenalized. With a one-class response the
            // likelihood therefore has no finite maximizer: its intercept diverges even when
            // `l2 > 0` keeps the feature weights finite.
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::fit",
                message: "y must contain both classes",
            });
        }
        budget.check(
            "LogisticRegression::fit",
            Self::fit_resource_estimate(x, cfg)?,
        )?;
        cancellation.check("LogisticRegression::fit", 0, cfg.max_iters)?;

        // A constant feature is exactly collinear with the unpenalized intercept. With ridge its
        // unique optimum is a zero feature coefficient (the intercept absorbs the constant
        // offset); without ridge, choosing zero is the canonical representative of the same
        // fitted logits. Remove such columns before forming normal equations. Besides improving
        // conditioning, this avoids an otherwise spurious overflow for a column such as
        // `[f64::MAX; n]`: its `XᵀWX` entry is infinite even though the exact fitted weight is
        // zero and the intercept-only optimum is perfectly representable.
        let mut active_features =
            try_vec_with_capacity("LogisticRegression::fit active features", d, budget)?;
        for j in 0..d {
            let first = x.row(0)[j];
            if (1..n).any(|i| x.row(i)[j] != first) {
                active_features.push(j);
            }
        }

        // Augmented design with an intercept column at index 0.
        let p = active_features
            .len()
            .checked_add(1)
            .ok_or(PidError::InvalidConfig {
                context: "LogisticRegression::fit",
                message: "design column count overflow",
            })?;
        let mut xa = na::DMatrix::<f64>::zeros(n, p);
        for i in 0..n {
            let row = x.row(i);
            xa[(i, 0)] = 1.0;
            for (active_j, &j) in active_features.iter().enumerate() {
                let v = row[j];
                if !v.is_finite() {
                    return Err(PidError::InvalidConfig {
                        context: "LogisticRegression::fit",
                        message: "x must be finite",
                    });
                }
                xa[(i, active_j + 1)] = v;
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
            cancellation.check("LogisticRegression::fit", iter, cfg.max_iters)?;
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
            if grad.iter().any(|v| !v.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context:
                        "LogisticRegression::fit: non-finite gradient (input magnitude overflow)",
                });
            }

            // Hessian: XᵀWX + λR.
            let xw = scale_rows(&xa, &w);
            let mut hess = xa.tr_mul(&xw);
            for k in 0..p {
                hess[(k, k)] += ridge[k];
            }
            if hess.iter().any(|v| !v.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context:
                        "LogisticRegression::fit: non-finite Hessian (input magnitude overflow)",
                });
            }

            // Solve H Δ = grad; β ← β − Δ (Newton step on the penalized NLL).
            let delta = solve_spd(&hess, &grad).ok_or(PidError::NumericalInstability {
                context: "LogisticRegression::fit: singular penalized Hessian (try l2 > 0)",
            })?;
            if delta.iter().any(|v| !v.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context: "LogisticRegression::fit: linear solve produced non-finite step",
                });
            }

            // A raw coefficient step is not a scale-invariant stopping criterion: replacing a
            // feature `x_j` by `c*x_j` divides its coefficient update by `c` without making the
            // fitted model any closer to optimum. The induced logit change X*delta and the
            // Newton decrement sqrt(grad^T H^-1 grad) are invariant under such a reparameterization.
            let logit_delta = &xa * &delta;
            let max_logit_delta = logit_delta.amax();
            let decrement_sq = grad.dot(&delta);
            if !max_logit_delta.is_finite() || !decrement_sq.is_finite() || decrement_sq < 0.0 {
                return Err(PidError::NumericalInstability {
                    context:
                        "LogisticRegression::fit: invalid scale-invariant convergence statistic",
                });
            }
            beta -= &delta;
            if beta.iter().any(|v| !v.is_finite()) {
                return Err(PidError::NumericalInstability {
                    context:
                        "LogisticRegression::fit: Newton update produced non-finite coefficients",
                });
            }

            if max_logit_delta <= cfg.tol && decrement_sq.sqrt() <= cfg.tol {
                converged = true;
                break;
            }
        }

        if !converged {
            return Err(PidError::NumericalInstability {
                context: "LogisticRegression::fit: Newton iteration did not converge",
            });
        }

        let intercept = beta[0];
        let mut weights = try_vec_filled("LogisticRegression::fit weights", d, 0.0, budget)?;
        for (active_j, &original_j) in active_features.iter().enumerate() {
            weights[original_j] = beta[active_j + 1];
        }
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
        self.decision_function_with_budget(x, ResourceBudget::default())
    }

    /// [`Self::decision_function`] under an explicit output-allocation budget.
    pub fn decision_function_with_budget(
        &self,
        x: MatRef<'_>,
        budget: ResourceBudget,
    ) -> PidResult<Vec<f64>> {
        if x.ncols() != self.weights.len() {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::decision_function",
                message: "x column count does not match fitted weights",
            });
        }
        let mut logits =
            try_vec_with_capacity("LogisticRegression::decision_function", x.nrows(), budget)?;
        for i in 0..x.nrows() {
            let row = x.row(i);
            let logit = self.intercept
                + row
                    .iter()
                    .zip(&self.weights)
                    .map(|(a, b)| a * b)
                    .sum::<f64>();
            if !logit.is_finite() {
                return Err(PidError::NumericalInstability {
                    context: "LogisticRegression::decision_function: non-finite logit (input magnitude overflow)",
                });
            }
            logits.push(logit);
        }
        Ok(logits)
    }

    /// Predicted success probabilities `sigmoid(x·w + b)`.
    pub fn predict_proba(&self, x: MatRef<'_>) -> PidResult<Vec<f64>> {
        self.predict_proba_with_budget(x, ResourceBudget::default())
    }

    /// [`Self::predict_proba`] under an explicit output-allocation budget.
    pub fn predict_proba_with_budget(
        &self,
        x: MatRef<'_>,
        budget: ResourceBudget,
    ) -> PidResult<Vec<f64>> {
        let mut values = self.decision_function_with_budget(x, budget)?;
        values.iter_mut().for_each(|value| *value = sigmoid(*value));
        Ok(values)
    }

    /// Hard predictions at the given probability `threshold` (e.g. 0.5).
    pub fn predict(&self, x: MatRef<'_>, threshold: f64) -> PidResult<Vec<bool>> {
        self.predict_with_budget(x, threshold, ResourceBudget::default())
    }

    /// [`Self::predict`] under an explicit output-allocation budget.
    pub fn predict_with_budget(
        &self,
        x: MatRef<'_>,
        threshold: f64,
        budget: ResourceBudget,
    ) -> PidResult<Vec<bool>> {
        if !threshold.is_finite() || !(0.0..=1.0).contains(&threshold) {
            return Err(PidError::InvalidConfig {
                context: "LogisticRegression::predict",
                message: "threshold must be finite and in [0, 1]",
            });
        }
        let probabilities = self.predict_proba_with_budget(x, budget)?;
        let mut predictions =
            try_vec_with_capacity("LogisticRegression::predict", probabilities.len(), budget)?;
        predictions.extend(probabilities.into_iter().map(|p| p >= threshold));
        Ok(predictions)
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

    #[test]
    fn fit_rejects_tiny_budget_before_dense_solver_allocation() {
        let x = MatRef::new(&[-1.0, 1.0], 2, 1).unwrap();
        let budget = ResourceBudget {
            max_bytes: 1,
            max_pairwise_distances: 1,
            max_operations_hint: 1_000,
            max_threads: 1,
        };

        let result = LogisticRegression::fit_with_budget(
            x,
            &[false, true],
            &LogisticRegressionConfig::default(),
            budget,
        );

        assert!(matches!(
            result,
            Err(PidError::ResourceLimitExceeded { .. })
        ));
    }

    #[test]
    fn fit_honors_a_pre_cancelled_token() {
        let x = MatRef::new(&[-1.0, 1.0], 2, 1).unwrap();
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = LogisticRegression::fit_with_budget_and_cancellation(
            x,
            &[false, true],
            &LogisticRegressionConfig::default(),
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                completed_units: 0,
                ..
            })
        ));
    }

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

    #[test]
    fn rejects_one_class_labels_with_unpenalized_intercept() {
        let x = MatOwned::new(vec![-1.0, -0.5, 0.5, 1.0], 4, 1).unwrap();

        for labels in [[true; 4], [false; 4]] {
            let err =
                LogisticRegression::fit(x.as_ref(), &labels, &LogisticRegressionConfig::default())
                    .unwrap_err();
            assert!(matches!(err, PidError::InvalidConfig { .. }));
        }
    }

    #[test]
    fn convergence_is_invariant_to_feature_rescaling() {
        fn fit_at_scale(scale: f64) -> LogisticRegression {
            let data = [-scale, -scale, -scale, -scale, scale, scale, scale, scale];
            // Empirical success rates are 1/4 at -scale and 3/4 at +scale, so the finite
            // unregularized optimum predicts exactly those probabilities.
            let labels = [true, false, false, false, true, true, true, false];
            let x = MatRef::new(&data, data.len(), 1).unwrap();
            LogisticRegression::fit(
                x,
                &labels,
                &LogisticRegressionConfig {
                    l2: 0.0,
                    max_iters: 100,
                    tol: 1e-10,
                },
            )
            .unwrap()
        }

        let ordinary = fit_at_scale(1.0);
        let huge = fit_at_scale(1.0e12);
        let ordinary_logits = ordinary
            .decision_function(MatRef::new(&[-1.0, 1.0], 2, 1).unwrap())
            .unwrap();
        let huge_logits = huge
            .decision_function(MatRef::new(&[-1.0e12, 1.0e12], 2, 1).unwrap())
            .unwrap();

        for (left, right) in ordinary_logits.iter().zip(&huge_logits) {
            assert!((left - right).abs() < 1e-10, "left={left} right={right}");
        }
        assert!(
            huge.n_iters() > 1,
            "scaled features must not cause premature convergence"
        );
    }

    #[test]
    fn iteration_exhaustion_returns_error() {
        let data = [-1.0, -1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0];
        let labels = [true, false, false, false, true, true, true, false];
        let x = MatRef::new(&data, data.len(), 1).unwrap();

        let err = LogisticRegression::fit(
            x,
            &labels,
            &LogisticRegressionConfig {
                l2: 0.0,
                max_iters: 1,
                tol: 1e-12,
            },
        )
        .unwrap_err();

        assert!(matches!(err, PidError::NumericalInstability { .. }));
    }

    #[test]
    fn constant_extreme_feature_reduces_to_the_exact_intercept_only_model() {
        let x = MatOwned::new(vec![f64::MAX; 4], 4, 1).unwrap();
        let y = [true, false, true, false];

        let model =
            LogisticRegression::fit(x.as_ref(), &y, &LogisticRegressionConfig::default()).unwrap();

        assert_eq!(model.weights(), &[0.0]);
        assert_eq!(model.intercept(), 0.0);
        assert_eq!(model.decision_function(x.as_ref()).unwrap(), vec![0.0; 4]);
    }

    #[test]
    fn predict_rejects_invalid_probability_threshold() {
        let (x, y) = make_logit_data(20, &[1.0], 0.0, 17);
        let model =
            LogisticRegression::fit(x.as_ref(), &y, &LogisticRegressionConfig::default()).unwrap();

        for threshold in [f64::NAN, f64::NEG_INFINITY, -0.1, 1.1, f64::INFINITY] {
            assert!(model.predict(x.as_ref(), threshold).is_err());
        }
    }
}
