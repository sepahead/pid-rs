use std::collections::BTreeMap;

use crate::{PidError, PidResult};

/// Shannon entropy H(X) for a discrete variable represented as integer labels.
///
/// - Units: **nats** (natural log).
/// - This is the plug-in / empirical entropy of the observed sample distribution.
pub fn entropy_discrete(x: &[u32]) -> PidResult<f64> {
    if x.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "entropy_discrete",
            message: "empty sample set (need n_samples > 0)",
        });
    }

    let n = x.len() as f64;
    let mut counts: BTreeMap<u32, usize> = BTreeMap::new();
    for &xi in x {
        *counts.entry(xi).or_insert(0) += 1;
    }

    let mut h = 0.0;
    for &c in counts.values() {
        let p = (c as f64) / n;
        // p>0 by construction.
        h -= p * p.ln();
    }
    Ok(h)
}

/// Joint Shannon entropy H(X1, ..., Xm) for discrete variables represented as integer labels.
///
/// - Units: **nats** (natural log).
/// - By convention, H(∅) = 0.
/// - All variables must have the same number of samples.
pub fn joint_entropy_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    if vars.is_empty() {
        return Ok(0.0);
    }

    let n = vars[0].len();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context: "joint_entropy_discrete",
            message: "empty sample set (need n_samples > 0)",
        });
    }
    for (j, v) in vars.iter().enumerate().skip(1) {
        if v.len() != n {
            return Err(PidError::RowCountMismatch {
                context: "joint_entropy_discrete",
                left_rows: n,
                right_rows: v.len(),
            });
        }
        let _ = j; // keep the loop index for debugging if needed
    }

    let n_f = n as f64;
    let m = vars.len();
    let mut counts: BTreeMap<Vec<u32>, usize> = BTreeMap::new();
    for i in 0..n {
        let mut key = Vec::with_capacity(m);
        for v in vars {
            key.push(v[i]);
        }
        *counts.entry(key).or_insert(0) += 1;
    }

    let mut h = 0.0;
    for &c in counts.values() {
        let p = (c as f64) / n_f;
        h -= p * p.ln();
    }
    Ok(h)
}

/// Degree of Redundancy (Red°) from Gutknecht et al. (2025), computed on discrete variables:
///
/// ```text
/// Red°(X1,...,Xm) := (Σ_i H(Xi)) / H(X1,...,Xm)
/// ```
///
/// Notes:
/// - Unitless ratio; log base cancels (we compute entropies in nats).
/// - Undefined when H(X1,...,Xm)=0 (all variables constant jointly); returns an error.
pub fn red_degree_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    if vars.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "red_degree_discrete",
            message: "need at least 1 variable",
        });
    }

    let h_joint = joint_entropy_discrete(vars)?;
    if h_joint == 0.0 {
        return Err(PidError::InvalidConfig {
            context: "red_degree_discrete",
            message: "joint entropy is zero; Red° is undefined",
        });
    }

    let mut sum = 0.0;
    for &v in vars {
        sum += entropy_discrete(v)?;
    }
    Ok(sum / h_joint)
}

/// Degree of Vulnerability (Vul°) from Gutknecht et al. (2025), computed on discrete variables:
///
/// ```text
/// Vul°(X1,...,Xm) := (Σ_i H(Xi | X_-i)) / H(X1,...,Xm)
/// ```
///
/// Notes:
/// - Unitless ratio; log base cancels (we compute entropies in nats).
/// - We compute H(Xi|X_-i) via entropies: H(Xi|X_-i)=H(X1..Xm)-H(X_-i).
/// - Undefined when H(X1,...,Xm)=0; returns an error.
pub fn vul_degree_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    if vars.is_empty() {
        return Err(PidError::InvalidConfig {
            context: "vul_degree_discrete",
            message: "need at least 1 variable",
        });
    }

    let m = vars.len();
    let h_joint = joint_entropy_discrete(vars)?;
    if h_joint == 0.0 {
        return Err(PidError::InvalidConfig {
            context: "vul_degree_discrete",
            message: "joint entropy is zero; Vul° is undefined",
        });
    }

    // Σ_i H(Xi|X_-i) = Σ_i (H_joint - H(X_-i)) = m*H_joint - Σ_i H(X_-i)
    let mut sum_h_minus_i = 0.0;
    for drop_i in 0..m {
        let mut subset: Vec<&[u32]> = Vec::with_capacity(m.saturating_sub(1));
        for (j, &v) in vars.iter().enumerate() {
            if j != drop_i {
                subset.push(v);
            }
        }
        sum_h_minus_i += joint_entropy_discrete(&subset)?;
    }

    let sum_cond = (m as f64) * h_joint - sum_h_minus_i;
    Ok(sum_cond / h_joint)
}

/// O-information Ω(X1,...,Xn) (Rosas et al. 2019), computed on discrete variables:
///
/// ```text
/// Ω(X1,...,Xn) = (n-2) H(X1,...,Xn) + Σ_i H(Xi) − Σ_i H(X_-i)
/// ```
///
/// Notes:
/// - Units: nats.
/// - Defined for n>=2. For n<2, returns an error (Ω is not meaningful).
pub fn o_information_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    let n_vars = vars.len();
    if n_vars < 2 {
        return Err(PidError::InvalidConfig {
            context: "o_information_discrete",
            message: "need at least 2 variables",
        });
    }

    let h_joint = joint_entropy_discrete(vars)?;

    let mut sum_h = 0.0;
    for &v in vars {
        sum_h += entropy_discrete(v)?;
    }

    let mut sum_h_minus_i = 0.0;
    for drop_i in 0..n_vars {
        let mut subset: Vec<&[u32]> = Vec::with_capacity(n_vars.saturating_sub(1));
        for (j, &v) in vars.iter().enumerate() {
            if j != drop_i {
                subset.push(v);
            }
        }
        sum_h_minus_i += joint_entropy_discrete(&subset)?;
    }

    Ok(((n_vars as f64) - 2.0) * h_joint + sum_h - sum_h_minus_i)
}

/// Pairwise co-information CI(X1, X2; Y) computed exactly from discrete entropies:
///
/// ```text
/// CI(X1, X2; Y) = I(X1;Y) + I(X2;Y) - I(X1,X2;Y)
/// ```
///
/// Notes:
/// - Units: nats.
/// - This is a Shannon-invariant summary; it is **not** a PID atom by itself.
pub fn co_information_pairwise_discrete(x1: &[u32], x2: &[u32], y: &[u32]) -> PidResult<f64> {
    if x1.len() != x2.len() {
        return Err(PidError::RowCountMismatch {
            context: "co_information_pairwise_discrete",
            left_rows: x1.len(),
            right_rows: x2.len(),
        });
    }
    if x1.len() != y.len() {
        return Err(PidError::RowCountMismatch {
            context: "co_information_pairwise_discrete",
            left_rows: x1.len(),
            right_rows: y.len(),
        });
    }

    let h_x1 = entropy_discrete(x1)?;
    let h_x2 = entropy_discrete(x2)?;
    let h_y = entropy_discrete(y)?;
    let h_x1y = joint_entropy_discrete(&[x1, y])?;
    let h_x2y = joint_entropy_discrete(&[x2, y])?;
    let h_x1x2 = joint_entropy_discrete(&[x1, x2])?;
    let h_x1x2y = joint_entropy_discrete(&[x1, x2, y])?;

    let i_x1_y = h_x1 + h_y - h_x1y;
    let i_x2_y = h_x2 + h_y - h_x2y;
    let i_x1x2_y = h_x1x2 + h_y - h_x1x2y;

    Ok(i_x1_y + i_x2_y - i_x1x2_y)
}

/// Average Degree of Redundancy (\bar{r}) for a target T and sources S_1, ..., S_n.
///
/// ```text
/// \bar{r}(T; S_1...S_n) = (Σ_i I(T; S_i)) / I(T; S_1...S_n)
/// ```
///
/// - `marginal_mis`: [I(T;S_1), ..., I(T;S_n)]
/// - `joint_mi`: I(T; S_1...S_n), which must be positive for the ratio to be meaningful.
/// - Returns NaN unless `joint_mi > 1e-12`. A tiny or non-positive joint MI (possible from
///   finite-sample/KSG noise even though the true value is ≥ 0) would otherwise blow up or
///   sign-flip the ratio.
pub fn average_degree_of_redundancy(marginal_mis: &[f64], joint_mi: f64) -> f64 {
    if !joint_mi.is_finite() || joint_mi <= 1e-12 {
        return f64::NAN;
    }
    marginal_mis.iter().sum::<f64>() / joint_mi
}

/// Average Degree of Vulnerability (\bar{v}) for a target T and sources S_1, ..., S_n.
///
/// ```text
/// \bar{v}(T; S_1...S_n) = (Σ_i I(T; S_i | S_-i)) / I(T; S_1...S_n)
/// ```
///
/// where I(T; S_i | S_-i) = I(T; S_1...S_n) - I(T; S_-i).
///
/// - `joint_mi`: I(T; S_1...S_n)
/// - `leave_one_out_mis`: [I(T; S_-1), ..., I(T; S_-n)]
///   (For n=2, this is just [I(T;S_2), I(T;S_1)]).
/// - Returns NaN unless `joint_mi > 1e-12` (see [`average_degree_of_redundancy`]): a tiny
///   or non-positive denominator makes the degree ill-defined.
pub fn average_degree_of_vulnerability(joint_mi: f64, leave_one_out_mis: &[f64]) -> f64 {
    if !joint_mi.is_finite() || joint_mi <= 1e-12 {
        return f64::NAN;
    }
    let n = leave_one_out_mis.len() as f64;
    let sum_loo: f64 = leave_one_out_mis.iter().sum();
    // Σ (I_joint - I_loo_i) = n * I_joint - Σ I_loo_i
    (n * joint_mi - sum_loo) / joint_mi
}
