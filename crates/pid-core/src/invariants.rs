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

    let mut counts: BTreeMap<u32, usize> = BTreeMap::new();
    for &xi in x {
        *counts.entry(xi).or_insert(0) += 1;
    }

    Ok(entropy_from_counts(counts.values().copied(), x.len()))
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

    let m = vars.len();
    let mut counts: BTreeMap<Vec<u32>, usize> = BTreeMap::new();
    for i in 0..n {
        let mut key = Vec::with_capacity(m);
        for v in vars {
            key.push(v[i]);
        }
        *counts.entry(key).or_insert(0) += 1;
    }

    Ok(entropy_from_counts(counts.values().copied(), n))
}

/// Degree of Redundancy (Red°), computed on discrete variables — a **target-free
/// entropy-ratio analogue** of the degree-of-redundancy invariant of Gutknecht et al.
/// (2025) (their `r̄` is stated in the MI-to-a-target form; this applies the same
/// Shannon-invariants framework to the joint entropy, with no target `Y`):
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

    let entropies = vars
        .iter()
        .map(|&v| entropy_discrete(v))
        .collect::<PidResult<Vec<_>>>()?;
    let sum = compensated_sum(entropies);
    Ok(sum / h_joint)
}

/// Degree of Vulnerability (Vul°), computed on discrete variables — a **target-free
/// entropy-ratio analogue** of the degree-of-vulnerability invariant of Gutknecht et al.
/// (2025) (their `v̄` is stated in the MI-to-a-target form; this applies the same
/// Shannon-invariants framework to the joint entropy, with no target `Y`):
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

    // Sum the conditional-entropy differences directly. Forming `m * H_joint` first can overflow
    // even when cancellation leaves a representable result.
    let mut conditional_entropies = Vec::with_capacity(m);
    for drop_i in 0..m {
        let mut subset: Vec<&[u32]> = Vec::with_capacity(m.saturating_sub(1));
        for (j, &v) in vars.iter().enumerate() {
            if j != drop_i {
                subset.push(v);
            }
        }
        conditional_entropies.push(h_joint - joint_entropy_discrete(&subset)?);
    }

    let sum_cond = compensated_sum(conditional_entropies);
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

    let marginal_entropies = vars
        .iter()
        .map(|&v| entropy_discrete(v))
        .collect::<PidResult<Vec<_>>>()?;
    let mut leave_one_out_entropies = Vec::with_capacity(n_vars);
    for drop_i in 0..n_vars {
        let mut subset: Vec<&[u32]> = Vec::with_capacity(n_vars.saturating_sub(1));
        for (j, &v) in vars.iter().enumerate() {
            if j != drop_i {
                subset.push(v);
            }
        }
        leave_one_out_entropies.push(joint_entropy_discrete(&subset)?);
    }

    Ok(compensated_sum(
        (0..n_vars.saturating_sub(2))
            .map(|_| h_joint)
            .chain(marginal_entropies)
            .chain(leave_one_out_entropies.into_iter().map(|value| -value)),
    ))
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

    Ok(compensated_sum([
        h_x1, h_x2, h_y, -h_x1y, -h_x2y, -h_x1x2, h_x1x2y,
    ]))
}

/// Average Degree of Redundancy (\bar{r}) for a target T and sources S_1, ..., S_n.
///
/// ```text
/// \bar{r}(T; S_1...S_n) = (Σ_i I(T; S_i)) / I(T; S_1...S_n)
/// ```
///
/// - `marginal_mis`: [I(T;S_1), ..., I(T;S_n)]
/// - `joint_mi`: I(T; S_1...S_n), which must be positive for the ratio to be meaningful.
/// - Returns NaN when the marginal list is empty, any input is non-finite, or
///   `joint_mi <= 1e-12`. A tiny or non-positive joint MI (possible from finite-sample/KSG noise
///   even though the true value is ≥ 0) would otherwise blow up or sign-flip the ratio.
pub fn average_degree_of_redundancy(marginal_mis: &[f64], joint_mi: f64) -> f64 {
    if marginal_mis.is_empty()
        || !joint_mi.is_finite()
        || joint_mi <= 1e-12
        || marginal_mis.iter().any(|value| !value.is_finite())
    {
        return f64::NAN;
    }
    stable_ratio_sum(marginal_mis, joint_mi)
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
/// - Returns NaN when the leave-one-out list is empty, any input is non-finite, or
///   `joint_mi <= 1e-12` (see [`average_degree_of_redundancy`]): a tiny or non-positive
///   denominator makes the degree ill-defined.
pub fn average_degree_of_vulnerability(joint_mi: f64, leave_one_out_mis: &[f64]) -> f64 {
    if leave_one_out_mis.is_empty()
        || !joint_mi.is_finite()
        || joint_mi <= 1e-12
        || leave_one_out_mis.iter().any(|value| !value.is_finite())
    {
        return f64::NAN;
    }
    stable_conditional_ratio_sum(joint_mi, leave_one_out_mis)
}

fn entropy_from_counts(counts: impl IntoIterator<Item = usize>, n: usize) -> f64 {
    let n = n as f64;
    compensated_sum(counts.into_iter().map(|count| {
        let count = count as f64;
        (count / n) * (n / count).ln()
    }))
}

/// Sum `values` and divide by `divisor` without forcing either the raw sum or every termwise ratio
/// through an overflowing intermediate.
fn stable_ratio_sum(values: &[f64], divisor: f64) -> f64 {
    let scale = values
        .iter()
        .fold(0.0_f64, |current, value| current.max(value.abs()));
    if scale == 0.0 {
        return 0.0;
    }
    let sum_scaled = compensated_sum(values.iter().map(|value| value / scale));
    if sum_scaled == 0.0 {
        return 0.0;
    }

    let ratio_by_scaled_divisor = sum_scaled * (scale / divisor);
    if ratio_by_scaled_divisor.is_finite() {
        return ratio_by_scaled_divisor;
    }
    let ratio_by_scaled_sum = (scale * sum_scaled) / divisor;
    if ratio_by_scaled_sum.is_finite() {
        ratio_by_scaled_sum
    } else {
        ratio_by_scaled_divisor
    }
}

/// Evaluate `Σ_i (joint - leave_i) / joint` without first rounding either `n - Σ ratios` or an
/// overflowing original-unit conditional difference.
fn stable_conditional_ratio_sum(joint: f64, leave_one_out: &[f64]) -> f64 {
    let max_magnitude = leave_one_out
        .iter()
        .fold(joint.abs(), |current, value| current.max(value.abs()));
    let exponent = (max_magnitude.to_bits() >> 52) & 0x7ff;
    let scale = if exponent == 0 {
        f64::from_bits(1)
    } else {
        f64::from_bits(exponent << 52)
    };
    let joint_scaled = joint / scale;
    let mut lost_nonzero_term = false;
    let sum_scaled = compensated_sum(leave_one_out.iter().flat_map(|value| {
        let leave_scaled = *value / scale;
        if *value != 0.0 && leave_scaled == 0.0 {
            lost_nonzero_term = true;
        }
        // TwoSum retains the conditional difference that rounds out of the leading term, such as
        // `1 - next_down(1)` or the unit offset in `1 - f64::MAX`.
        let rounded = joint_scaled - leave_scaled;
        let leave_virtual = rounded - joint_scaled;
        let error = (joint_scaled - (rounded - leave_virtual)) + (-leave_scaled - leave_virtual);
        [rounded, error]
    }));
    if lost_nonzero_term {
        return f64::NAN;
    }
    if sum_scaled == 0.0 {
        return 0.0;
    }

    let ratio_by_scaled_divisor = sum_scaled * (scale / joint);
    if ratio_by_scaled_divisor.is_finite() {
        return ratio_by_scaled_divisor;
    }
    let ratio_by_scaled_sum = (scale * sum_scaled) / joint;
    if ratio_by_scaled_sum.is_finite() {
        ratio_by_scaled_sum
    } else {
        ratio_by_scaled_divisor
    }
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
