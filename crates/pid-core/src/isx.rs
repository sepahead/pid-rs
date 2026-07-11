use crate::error::{PidError, PidResult};
use crate::ksg::{ksg_local_mi_terms, ksg_local_mi_terms_xblocks, KsgConfig, NegativeHandling};
use crate::matrix::MatRef;
use crate::metric::Metric;
use crate::nn::{
    count_neighbors_within, kth_neighbor_distance_joint_max_with_scratch,
    kth_neighbor_shell_counts, strict_radius, validate_kth_neighbor_shell,
};
use crate::stats::{compensated_sum, digamma, digamma_int_table};
use crate::support::{
    validate_observed_sample_conditions, validate_support_contract, SupportContract,
};

#[derive(Clone, Copy)]
struct DistIsx2 {
    joint: f64,
    dt: f64,
    ds: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum IsxMethod {
    /// Paper-faithful kNN estimator for continuous shared-exclusions redundancy from:
    /// Ehrlich et al. (2024), Phys. Rev. E 110, 014115 (arXiv:2311.06373v3).
    ///
    /// Implements the bivariate redundancy `I^sx_∩(S1,S2;T)` via the KSG-style estimator
    /// (Appendix H, Algorithms 3–6) under the L∞/Chebyshev metric:
    ///
    /// I^sx_∩ = ψ(k) + ψ(n) - ⟨ ψ(n_α(i)) + ψ(n_T(i)) ⟩_i
    ///
    /// where:
    /// - ε_i is the kNN radius in the joint (source-disjunction, target) space,
    /// - n_α(i) counts neighbors in the *source disjunction* within ε_i,
    /// - n_T(i) counts neighbors in target space within ε_i.
    ///
    /// Note: This is the default method for `IsxConfig`.
    EhrlichKsg,
    /// Experimental heuristic sketch estimator.
    ///
    /// Provided as an explicit, clearly-labelled baseline only; it should be treated as
    /// untrusted until validated against synthetic systems with known information quantities.
    HeuristicSketch,
    /// Approximate shared-exclusions redundancy by taking the samplewise minimum
    /// of KSG local MI terms for (S1,T) and (S2,T), then averaging.
    LocalMinKsg,
    /// Experimental **unweighted inclusion–exclusion heuristic** over pointwise KSG local-MI
    /// terms:
    ///
    /// r(s1,s2;t) = log( exp(i(s1;t)) + exp(i(s2;t)) - exp(i(s1,s2;t)) )
    ///
    /// **This is NOT the shared-exclusions disjunction identity.** The true forms are:
    /// - discrete (Makkeh–Gutknecht–Wibral 2021):
    ///   `i^sx = log[(p(s1)e^{i1} + p(s2)e^{i2} − p(s1,s2)e^{i12}) / (p(s1)+p(s2)−p(s1,s2))]`
    ///   (probability-weighted);
    /// - continuous limit (Ehrlich et al. 2024, Def. 2; re-derived in
    ///   `tests/sxpid_gaussian_oracle.rs`):
    ///   `i^sx = log[w1·e^{i1} + w2·e^{i2}]` with density weights
    ///   `w_a = f_{S_a}(s_a) / (f_{S1}(s1) + f_{S2}(s2))` and **no** joint term (the discrete
    ///   joint-term weight `p(s1,s2)` vanishes in the continuum).
    ///
    /// This variant sets all weights to 1 and retains a full-weight joint term, so it estimates
    /// a *different* functional and does not converge to `I^sx_∩` as estimation error → 0; its
    /// log argument can also be non-positive (surfacing as `NumericalInstability`), whereas the
    /// true `i^sx` argument `P(∪|t)/P(∪)` is always positive. Baseline/diagnostic use only.
    DisjunctionFromLocalMi,
}

#[derive(Debug, Clone)]
pub struct IsxConfig {
    pub k: usize,
    pub metric: Metric,
    /// Reserved strict-radius compatibility field; must be exactly `0.0`.
    ///
    /// Strict counts use the floating-point predecessor of the raw kNN radius. A material
    /// subtraction would erode the neighborhood and estimate a different functional.
    pub tie_epsilon: f64,
    pub method: IsxMethod,
    /// Population-support assertion for every marginal and joint law used by this call.
    ///
    /// The default is [`SupportContract::Unspecified`] and deliberately fails closed. The current
    /// continuous shared-exclusions estimators accept only
    /// [`SupportContract::AssumeAbsolutelyContinuous`].
    pub support_contract: SupportContract,
}

impl Default for IsxConfig {
    fn default() -> Self {
        Self {
            k: 3,
            metric: Metric::Chebyshev,
            tie_epsilon: 0.0,
            method: IsxMethod::EhrlichKsg,
            support_contract: SupportContract::Unspecified,
        }
    }
}

impl IsxConfig {
    /// Construct the paper-faithful Chebyshev configuration with an explicit caller assertion that
    /// every required marginal and joint law is full-dimensional and absolutely continuous.
    pub fn assume_absolutely_continuous() -> Self {
        Self {
            support_contract: SupportContract::AssumeAbsolutelyContinuous,
            ..Self::default()
        }
    }
}

/// Continuous shared-exclusions redundancy I^sx_∩(S1,S2;T).
///
/// This is the core Wibral-group PID quantity (Makkeh et al. 2021; Ehrlich et al. 2024).
///
/// By default (`IsxMethod::EhrlichKsg`), this uses the paper-faithful KSG-style kNN estimator
/// for continuous variables (Ehrlich et al. 2024, Appendix H).
///
/// # Units
/// Returns redundancy in **nats** (natural log).
///
/// # Important: can be negative
/// `I^sx_∩` is a well-defined functional of the joint distribution, but it is **not guaranteed
/// to be non-negative** under all desiderata (see the PID inconsistency/impossibility results
/// discussed in Makkeh et al. 2021 and Matthias et al. 2025). Do not clamp this value to 0.
///
/// # Assumptions / failure modes (estimator-level)
/// The default estimator is kNN-based and inherits the usual kNN MI pathologies:
/// - The default support contract is unspecified and fails closed. Callers must explicitly assert
///   full-dimensional absolute continuity for every marginal and joint law used by the estimator.
///   Exact coordinate ties are incompatible with ideal i.i.d., unrounded continuous-sample
///   conditions but do not identify their cause or population support; all-unique finite
///   observations do not prove the model.
/// - Assumes i.i.d. samples from a continuous distribution; trajectory autocorrelation and
///   quantization/duplicates can collapse the kNN radius or create an ambiguous positive boundary.
///   Adding jitter changes the estimated distribution and is appropriate only under an explicit
///   observation-noise model or as a seeded, reported noise-scale sensitivity analysis; otherwise
///   use a discrete, quantized, or mixed-support estimator.
/// - Can fail in high ambient/intrinsic dimension due to distance concentration.
/// - Can require prohibitive samples under strong dependence (very large true MI).
/// - Exact deterministic continuous maps have infinite MI and fall outside the estimator's domain.
///   An explicit observation-noise model defines a different, finite-MI distribution; otherwise
///   use a suitable discrete/mixed estimator.
/// - The two source matrices must have the same ambient column count. The small-ball
///   disjunction compares their raw neighborhood radii, whose asymptotic scaling depends on
///   dimension; unequal-dimensional source balls therefore do not share the estimator's
///   required reference scaling. Equal ambient dimensions are only a necessary guard: they do
///   **not** prove equal intrinsic dimensions, compatible reference measures, or comparable
///   neighborhood geometry.
/// - Relative source units and preprocessing define the comparison between source neighborhoods
///   and are part of the continuous `I^sx_∩` estimand. Record the full scheme and do not compare
///   or pool results across different source scalings/projections.
///
/// Other `IsxMethod` variants are included only as explicit experimental baselines / cross-checks
/// against the default estimator, and should not be trusted without validation.
pub fn isx_redundancy(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy",
            left_rows: s1.nrows(),
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    if s1.ncols() == 0 || s2.ncols() == 0 || t.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "isx_redundancy",
            message: "inputs must have at least 1 column",
        });
    }
    if s1.ncols() != s2.ncols() {
        return Err(PidError::SourceDimensionMismatch {
            context: "isx_redundancy",
            left_cols: s1.ncols(),
            right_cols: s2.ncols(),
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context: "isx_redundancy",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.k == 0 || s1.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: s1.nrows(),
        });
    }
    // The paper-faithful continuous `I^sx_∩` implementation is restricted to its documented
    // L∞/Chebyshev convention. This is metric-domain validation, not a general consistency claim.
    // Do not silently “swap the geometry” (e.g., hyperbolic distances) and still call it `I^sx_∩`.
    if cfg.method == IsxMethod::EhrlichKsg && cfg.metric != Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context: "isx_redundancy",
            message:
                "IsxMethod::EhrlichKsg is restricted to its paper-faithful Metric::Chebyshev (L∞) convention; other metrics are research-gated",
        });
    }
    validate_support_contract("isx_redundancy", cfg.support_contract, cfg.metric)?;
    // The manifold research opt-in is MI-only; no shared-exclusions reference measure has been
    // defined or validated for it.
    if cfg.support_contract != SupportContract::AssumeAbsolutelyContinuous {
        return Err(PidError::UnsupportedSupportContract {
            context: "isx_redundancy",
            contract: cfg.support_contract,
        });
    }
    validate_observed_sample_conditions("isx_redundancy", cfg.support_contract, &[s1, s2, t])?;
    match cfg.method {
        IsxMethod::EhrlichKsg => isx_redundancy_ehrlich_ksg(s1, s2, t, cfg),
        IsxMethod::HeuristicSketch => isx_redundancy_heuristic_sketch(s1, s2, t, cfg),
        IsxMethod::LocalMinKsg => isx_redundancy_local_min_ksg(s1, s2, t, cfg),
        IsxMethod::DisjunctionFromLocalMi => {
            isx_redundancy_disjunction_from_local_mi(s1, s2, t, cfg)
        }
    }
}

fn isx_redundancy_ehrlich_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_ehrlich_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // This is the bivariate antichain α = {{1},{2}}; the disjunction distance in source space is:
    // d_S_disj(i,j) = min( d(S1_i,S1_j), d(S2_i,S2_j) ).
    //
    // With Chebyshev/L∞ and a shared target ball, the joint disjunction distance is:
    // d_ST_disj(i,j) = max( d(T_i,T_j), d_S_disj(i,j) ).
    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    // Per-point local term. Each point is independent and allocates its own scratch, so the
    // closure is pure and can run data-parallel. Results are collected **in index order** and
    // reduced with the same deterministic compensated summation in both paths, so the `parallel`
    // path is bit-for-bit identical to the serial path (see `map_index_ordered`).
    let local = |i: usize| -> PidResult<f64> {
        let mut scratch = Vec::with_capacity(n.saturating_sub(1));
        let s1i = s1.row(i);
        let s2i = s2.row(i);
        let ti = t.row(i);
        for j in 0..n {
            if i == j {
                continue;
            }
            let ds1 = cfg.metric.checked_distance(
                s1i,
                s1.row(j),
                "isx_redundancy_ehrlich_ksg: s1 distance",
            )?;
            let ds2 = cfg.metric.checked_distance(
                s2i,
                s2.row(j),
                "isx_redundancy_ehrlich_ksg: s2 distance",
            )?;
            let dt = cfg.metric.checked_distance(
                ti,
                t.row(j),
                "isx_redundancy_ehrlich_ksg: target distance",
            )?;
            let ds = ds1.min(ds2);
            scratch.push(DistIsx2 {
                joint: dt.max(ds),
                dt,
                ds,
            });
        }

        let kth = k - 1;
        scratch.select_nth_unstable_by(kth, |a, b| a.joint.total_cmp(&b.joint));
        let eps_raw = scratch[kth].joint;
        if eps_raw == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_ehrlich_ksg: kNN radius is non-positive; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().map(|distance| distance.joint), eps_raw);
        validate_kth_neighbor_shell(
            "isx_redundancy_ehrlich_ksg",
            i,
            k,
            eps_raw,
            interior_count,
            boundary_count,
        )?;
        let eps = strict_radius(eps_raw);

        // Counts exclude self; the estimator needs counts including self.
        let mut n_t = 1usize;
        let mut n_alpha = 1usize;
        for d in &scratch {
            if d.dt <= eps {
                n_t += 1;
            }
            if d.ds <= eps {
                n_alpha += 1;
            }
        }

        Ok(psi_k + psi_n - psi_int[n_alpha] - psi_int[n_t])
    };

    let terms = crate::par::map_index_ordered(n, local)?;
    let sum = compensated_sum(terms.iter().copied());
    Ok(sum / (n as f64))
}

fn isx_redundancy_disjunction_from_local_mi(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_disjunction_from_local_mi",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let mut i1 = ksg_local_mi_terms(s1, t, &ksg_cfg)?;
    let i2 = ksg_local_mi_terms(s2, t, &ksg_cfg)?;
    let i12 = ksg_local_mi_terms_xblocks(&[s1, s2], t, &ksg_cfg)?;

    for ((a, &b), &c) in i1.iter_mut().zip(i2.iter()).zip(i12.iter()) {
        // Compute: log(exp(a)+exp(b)-exp(c)) stably.
        let m = (*a).max(b).max(c);
        let sa = (*a - m).exp();
        let sb = (b - m).exp();
        let sc = (c - m).exp();
        let s = sa + sb - sc;
        if !s.is_finite() || s <= 0.0 {
            return Err(PidError::NumericalInstability {
                context:
                    "isx_redundancy_disjunction_from_local_mi: disjunction argument is non-positive",
            });
        }
        *a = m + s.ln();
    }

    Ok(compensated_sum(i1) / (n as f64))
}

fn isx_redundancy_local_min_ksg(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_local_min_ksg",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    let ksg_cfg = KsgConfig {
        k: cfg.k,
        metric: cfg.metric,
        tie_epsilon: cfg.tie_epsilon,
        negative_handling: NegativeHandling::Allow,
        support_contract: cfg.support_contract,
    };

    let local_s1 = ksg_local_mi_terms(s1, t, &ksg_cfg)?;
    let local_s2 = ksg_local_mi_terms(s2, t, &ksg_cfg)?;

    let red = compensated_sum(
        local_s1
            .iter()
            .zip(local_s2.iter())
            .map(|(&a, &b)| a.min(b)),
    ) / (n as f64);

    Ok(red)
}

fn isx_redundancy_heuristic_sketch(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &IsxConfig,
) -> PidResult<f64> {
    if s1.nrows() != s2.nrows() || s1.nrows() != t.nrows() {
        return Err(PidError::RowCountMismatch {
            context: "isx_redundancy_heuristic_sketch",
            left_rows: s1.nrows(),
            // Report the count that actually mismatches s1 (s2's if it differs, else t's).
            right_rows: if s2.nrows() != s1.nrows() {
                s2.nrows()
            } else {
                t.nrows()
            },
        });
    }
    let n = s1.nrows();
    let k = cfg.k;
    if k == 0 || n <= k {
        return Err(PidError::InvalidK { k, n_samples: n });
    }

    // 1) Per-sample kNN radii in the (S1,T) and (S2,T) joint spaces. (Steps 2–3 use only
    //    these two and their samplewise min; no (S1,S2,T) joint radius enters the estimate.)
    let mut eps_s1_t = vec![0.0f64; n];
    let mut eps_s2_t = vec![0.0f64; n];

    let mut scratch = Vec::with_capacity(n.saturating_sub(1));
    for i in 0..n {
        let e1 =
            kth_neighbor_distance_joint_max_with_scratch(&[s1, t], i, k, cfg.metric, &mut scratch)?;
        if e1 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e1);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s1,target)",
            i,
            k,
            e1,
            interior_count,
            boundary_count,
        )?;
        eps_s1_t[i] = e1;

        let e2 =
            kth_neighbor_distance_joint_max_with_scratch(&[s2, t], i, k, cfg.metric, &mut scratch)?;
        if e2 == 0.0 {
            return Err(PidError::NumericalInstability {
                context: "isx_redundancy_heuristic_sketch: kNN radius collapsed to 0; jitter changes the estimated distribution and is valid only under an explicit observation-noise model or a reported noise-scale sensitivity analysis; otherwise use a discrete, quantized, or mixed-support estimator",
            });
        }
        let (interior_count, boundary_count) =
            kth_neighbor_shell_counts(scratch.iter().copied(), e2);
        validate_kth_neighbor_shell(
            "isx_redundancy_heuristic_sketch (s2,target)",
            i,
            k,
            e2,
            interior_count,
            boundary_count,
        )?;
        eps_s2_t[i] = e2;
    }

    // 2) Count neighbors in target space within the respective radii.
    let mut n_t_s1 = vec![0usize; n];
    let mut n_t_s2 = vec![0usize; n];
    let mut n_t_shared = vec![0usize; n];

    for i in 0..n {
        let e1_raw = eps_s1_t[i];
        let e2_raw = eps_s2_t[i];

        let e1 = strict_radius(e1_raw);
        let e2 = strict_radius(e2_raw);
        let es = strict_radius(e1_raw.min(e2_raw));

        n_t_s1[i] = count_neighbors_within(t, i, e1, cfg.metric)?;
        n_t_s2[i] = count_neighbors_within(t, i, e2, cfg.metric)?;
        n_t_shared[i] = count_neighbors_within(t, i, es, cfg.metric)?;
    }

    // 3) Experimental heuristic sketch estimator.
    let psi_k = digamma(k as f64);
    let psi_n = digamma(n as f64);
    let psi_int = digamma_int_table(n);

    let avg_term = compensated_sum((0..n).map(|i| {
        let psi_shared = psi_int[n_t_shared[i] + 1];
        let psi_s1 = psi_int[n_t_s1[i] + 1];
        let psi_s2 = psi_int[n_t_s2[i] + 1];
        psi_shared - 0.5 * (psi_s1 + psi_s2)
    })) / (n as f64);

    let redundancy = psi_k + psi_n + avg_term;
    Ok(redundancy)
}
