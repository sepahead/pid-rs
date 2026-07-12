use std::cmp::Ordering;
use std::mem::size_of;

use serde::Serialize;

use crate::resource::{try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::{PidError, PidResult};

/// Estimate peak memory and comparison work for [`entropy_discrete`].
///
/// The estimate covers the fallible row-index workspace. Sorting is in place and does not create
/// a second collection.
pub fn entropy_discrete_resource_estimate(n_samples: usize) -> PidResult<ResourceEstimate> {
    entropy_family_resource_estimate("entropy_discrete", n_samples, 1, 1)
}

/// Shannon entropy H(X) for a discrete variable represented as integer labels.
///
/// - Units: **nats** (natural log).
/// - This is the plug-in / empirical entropy of the observed sample distribution.
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn entropy_discrete(x: &[u32]) -> PidResult<f64> {
    entropy_discrete_with_budget(x, ResourceBudget::default())
}

/// Budgeted variant of [`entropy_discrete`].
///
/// # Errors
///
/// Returns a structured resource error before allocation when `budget` is too small, and returns
/// [`PidError::AllocationFailed`] if the allocator cannot provide the preflighted workspace.
pub fn entropy_discrete_with_budget(x: &[u32], budget: ResourceBudget) -> PidResult<f64> {
    const OPERATION: &str = "entropy_discrete";
    if x.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "empty sample set (need n_samples > 0)",
        });
    }

    budget.check(OPERATION, entropy_discrete_resource_estimate(x.len())?)?;
    let mut workspace = EntropyWorkspace::new(OPERATION, x.len(), budget)?;
    workspace.entropy_single(OPERATION, x)
}

/// Estimate peak memory and comparison work for [`joint_entropy_discrete`].
///
/// `n_samples` is the common row count and `n_variables` is the number of variables. When
/// `n_variables == 0`, the estimate is zero because H(∅) is returned without inspecting rows.
pub fn joint_entropy_discrete_resource_estimate(
    n_samples: usize,
    n_variables: usize,
) -> PidResult<ResourceEstimate> {
    if n_variables == 0 {
        return Ok(ResourceEstimate::ZERO);
    }
    entropy_family_resource_estimate("joint_entropy_discrete", n_samples, n_variables as u128, 1)
}

/// Joint Shannon entropy H(X1, ..., Xm) for discrete variables represented as integer labels.
///
/// - Units: **nats** (natural log).
/// - By convention, H(∅) = 0.
/// - All variables must have the same number of samples.
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn joint_entropy_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    joint_entropy_discrete_with_budget(vars, ResourceBudget::default())
}

/// Budgeted variant of [`joint_entropy_discrete`].
///
/// # Errors
///
/// Returns a row-count or empty-sample error for invalid data, a structured resource error before
/// allocation when `budget` is too small, or [`PidError::AllocationFailed`] if the allocator
/// cannot provide the preflighted workspace.
pub fn joint_entropy_discrete_with_budget(
    vars: &[&[u32]],
    budget: ResourceBudget,
) -> PidResult<f64> {
    const OPERATION: &str = "joint_entropy_discrete";
    if vars.is_empty() {
        return Ok(0.0);
    }

    let n_samples = validate_discrete_variables(OPERATION, vars)?;
    budget.check(
        OPERATION,
        joint_entropy_discrete_resource_estimate(n_samples, vars.len())?,
    )?;
    let mut workspace = EntropyWorkspace::new(OPERATION, n_samples, budget)?;
    workspace.entropy_joint(OPERATION, vars)
}

/// Estimate peak memory and aggregate comparison work for [`red_degree_discrete`].
pub fn red_degree_discrete_resource_estimate(
    n_samples: usize,
    n_variables: usize,
) -> PidResult<ResourceEstimate> {
    let variables = n_variables as u128;
    let total_projection_width = variables.checked_mul(2).ok_or(PidError::SizeOverflow {
        operation: "red_degree_discrete",
    })?;
    let projection_count = variables.checked_add(1).ok_or(PidError::SizeOverflow {
        operation: "red_degree_discrete",
    })?;
    entropy_family_resource_estimate(
        "red_degree_discrete",
        n_samples,
        total_projection_width,
        projection_count,
    )
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
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn red_degree_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    red_degree_discrete_with_budget(vars, ResourceBudget::default())
}

/// Budgeted variant of [`red_degree_discrete`].
pub fn red_degree_discrete_with_budget(vars: &[&[u32]], budget: ResourceBudget) -> PidResult<f64> {
    const OPERATION: &str = "red_degree_discrete";
    if vars.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "need at least 1 variable",
        });
    }

    let n_samples = validate_discrete_variables(OPERATION, vars)?;
    budget.check(
        OPERATION,
        red_degree_discrete_resource_estimate(n_samples, vars.len())?,
    )?;
    let mut workspace = EntropyWorkspace::new(OPERATION, n_samples, budget)?;
    let h_joint = workspace.entropy_joint(OPERATION, vars)?;
    if h_joint == 0.0 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "joint entropy is zero; Red° is undefined",
        });
    }

    let mut marginal_sum = CompensatedAccumulator::default();
    for &variable in vars {
        marginal_sum.add(workspace.entropy_single(OPERATION, variable)?);
    }
    Ok(marginal_sum.finish() / h_joint)
}

/// Estimate peak memory and aggregate comparison work for [`vul_degree_discrete`].
pub fn vul_degree_discrete_resource_estimate(
    n_samples: usize,
    n_variables: usize,
) -> PidResult<ResourceEstimate> {
    let variables = n_variables as u128;
    let total_projection_width =
        variables
            .checked_mul(variables)
            .ok_or(PidError::SizeOverflow {
                operation: "vul_degree_discrete",
            })?;
    let projection_count = if n_variables <= 1 {
        variables
    } else {
        variables.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: "vul_degree_discrete",
        })?
    };
    entropy_family_resource_estimate(
        "vul_degree_discrete",
        n_samples,
        total_projection_width,
        projection_count,
    )
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
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn vul_degree_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    vul_degree_discrete_with_budget(vars, ResourceBudget::default())
}

/// Budgeted variant of [`vul_degree_discrete`].
pub fn vul_degree_discrete_with_budget(vars: &[&[u32]], budget: ResourceBudget) -> PidResult<f64> {
    const OPERATION: &str = "vul_degree_discrete";
    if vars.is_empty() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "need at least 1 variable",
        });
    }

    let n_samples = validate_discrete_variables(OPERATION, vars)?;
    budget.check(
        OPERATION,
        vul_degree_discrete_resource_estimate(n_samples, vars.len())?,
    )?;
    let mut workspace = EntropyWorkspace::new(OPERATION, n_samples, budget)?;
    let h_joint = workspace.entropy_joint(OPERATION, vars)?;
    if h_joint == 0.0 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "joint entropy is zero; Vul° is undefined",
        });
    }

    // Sum the conditional-entropy differences directly. Forming `m * H_joint` first can overflow
    // even when cancellation leaves a representable result.
    let mut conditional_sum = CompensatedAccumulator::default();
    for drop_index in 0..vars.len() {
        let leave_one_out = workspace.entropy_excluding(OPERATION, vars, drop_index)?;
        conditional_sum.add(h_joint - leave_one_out);
    }
    Ok(conditional_sum.finish() / h_joint)
}

/// Estimate peak memory and aggregate comparison work for [`o_information_discrete`].
pub fn o_information_discrete_resource_estimate(
    n_samples: usize,
    n_variables: usize,
) -> PidResult<ResourceEstimate> {
    let variables = n_variables as u128;
    let total_projection_width = variables
        .checked_mul(variables.checked_add(1).ok_or(PidError::SizeOverflow {
            operation: "o_information_discrete",
        })?)
        .ok_or(PidError::SizeOverflow {
            operation: "o_information_discrete",
        })?;
    let projection_count = variables
        .checked_mul(2)
        .and_then(|value| value.checked_add(1))
        .ok_or(PidError::SizeOverflow {
            operation: "o_information_discrete",
        })?;
    entropy_family_resource_estimate(
        "o_information_discrete",
        n_samples,
        total_projection_width,
        projection_count,
    )
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
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn o_information_discrete(vars: &[&[u32]]) -> PidResult<f64> {
    o_information_discrete_with_budget(vars, ResourceBudget::default())
}

/// Budgeted variant of [`o_information_discrete`].
pub fn o_information_discrete_with_budget(
    vars: &[&[u32]],
    budget: ResourceBudget,
) -> PidResult<f64> {
    const OPERATION: &str = "o_information_discrete";
    let n_variables = vars.len();
    if n_variables < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "need at least 2 variables",
        });
    }

    let n_samples = validate_discrete_variables(OPERATION, vars)?;
    budget.check(
        OPERATION,
        o_information_discrete_resource_estimate(n_samples, n_variables)?,
    )?;
    let mut workspace = EntropyWorkspace::new(OPERATION, n_samples, budget)?;
    let h_joint = workspace.entropy_joint(OPERATION, vars)?;

    let mut total = CompensatedAccumulator::default();
    for _ in 0..n_variables.saturating_sub(2) {
        total.add(h_joint);
    }
    for &variable in vars {
        total.add(workspace.entropy_single(OPERATION, variable)?);
    }
    for drop_index in 0..n_variables {
        total.add(-workspace.entropy_excluding(OPERATION, vars, drop_index)?);
    }
    Ok(total.finish())
}

/// Estimate peak memory and aggregate comparison work for
/// [`co_information_pairwise_discrete`].
pub fn co_information_pairwise_discrete_resource_estimate(
    n_samples: usize,
) -> PidResult<ResourceEstimate> {
    // The inclusion-exclusion identity contains three width-one, three width-two, and one
    // width-three entropy projection: total width 12 across seven projections.
    entropy_family_resource_estimate("co_information_pairwise_discrete", n_samples, 12, 7)
}

/// Pairwise co-information CoI(X1, X2; Y) computed exactly from discrete entropies:
///
/// ```text
/// CoI(X1, X2; Y) = I(X1;Y) + I(X2;Y) - I(X1,X2;Y)
/// ```
///
/// Notes:
/// - Units: nats.
/// - This is a Shannon-invariant summary; it is **not** a PID atom by itself.
/// - Resource use is bounded by [`ResourceBudget::default`].
pub fn co_information_pairwise_discrete(x1: &[u32], x2: &[u32], y: &[u32]) -> PidResult<f64> {
    co_information_pairwise_discrete_with_budget(x1, x2, y, ResourceBudget::default())
}

/// Budgeted variant of [`co_information_pairwise_discrete`].
pub fn co_information_pairwise_discrete_with_budget(
    x1: &[u32],
    x2: &[u32],
    y: &[u32],
    budget: ResourceBudget,
) -> PidResult<f64> {
    const OPERATION: &str = "co_information_pairwise_discrete";
    let variables = [x1, x2, y];
    let n_samples = validate_discrete_variables(OPERATION, &variables)?;
    budget.check(
        OPERATION,
        co_information_pairwise_discrete_resource_estimate(n_samples)?,
    )?;
    let mut workspace = EntropyWorkspace::new(OPERATION, n_samples, budget)?;

    let h_x1 = workspace.entropy_single(OPERATION, x1)?;
    let h_x2 = workspace.entropy_single(OPERATION, x2)?;
    let h_y = workspace.entropy_single(OPERATION, y)?;
    let h_x1y = workspace.entropy_joint(OPERATION, &[x1, y])?;
    let h_x2y = workspace.entropy_joint(OPERATION, &[x2, y])?;
    let h_x1x2 = workspace.entropy_joint(OPERATION, &[x1, x2])?;
    let h_x1x2y = workspace.entropy_joint(OPERATION, &variables)?;

    Ok(compensated_sum([
        h_x1, h_x2, h_y, -h_x1y, -h_x2y, -h_x1x2, h_x1x2y,
    ]))
}

/// Policy for normalized Shannon-invariant ratios.
///
/// A positive but very small estimated joint mutual information makes a normalized ratio
/// arbitrarily sensitive to estimation and rounding error. The threshold is therefore an
/// explicit analysis choice, in nats, rather than a hidden constant in the formula.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct NormalizedInvariantPolicy {
    minimum_denominator_nats: f64,
}

impl NormalizedInvariantPolicy {
    /// Construct a policy with an explicit positive-denominator stability threshold.
    pub fn new(minimum_denominator_nats: f64) -> PidResult<Self> {
        if !minimum_denominator_nats.is_finite() || minimum_denominator_nats < 0.0 {
            return Err(PidError::InvalidConfig {
                context: "NormalizedInvariantPolicy::new",
                message: "minimum_denominator_nats must be finite and >= 0",
            });
        }
        Ok(Self {
            minimum_denominator_nats,
        })
    }

    pub fn minimum_denominator_nats(self) -> f64 {
        self.minimum_denominator_nats
    }
}

impl Default for NormalizedInvariantPolicy {
    fn default() -> Self {
        Self {
            // This preserves the pre-1.0 screening convention while making it visible and
            // replaceable. It is a numerical/reporting policy, not a theorem threshold.
            minimum_denominator_nats: 1.0e-12,
        }
    }
}

/// Machine-readable state of a normalized Shannon-invariant report.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum NormalizedInvariantStatus {
    Defined,
    EmptyTerms,
    NonFiniteInput,
    NonPositiveDenominator,
    DenominatorBelowPolicyThreshold,
    NumericallyUnrepresentable,
}

/// Unit carried by a normalized invariant.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum NormalizedInvariantUnit {
    Unitless,
}

/// Typed result for a normalized Shannon-invariant analogue.
///
/// `value` is present exactly when `status == Defined`. Invalid or unstable inputs never become
/// an unexplained `NaN`, which keeps JSON/run-log handoff unambiguous. `numerator_nats` can be
/// absent for a defined ratio when the original-unit numerator overflows even though the scaled
/// ratio is representable.
#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub struct NormalizedInvariantReport {
    pub value: Option<f64>,
    pub numerator_nats: Option<f64>,
    pub denominator_nats: Option<f64>,
    pub definition: &'static str,
    pub unit: NormalizedInvariantUnit,
    pub status: NormalizedInvariantStatus,
    pub policy: NormalizedInvariantPolicy,
}

impl NormalizedInvariantReport {
    /// Return the defined value or a structured error suitable for scalar-only internal callers.
    pub fn require_value(&self, context: &'static str) -> PidResult<f64> {
        self.value.ok_or(PidError::NumericalInstability { context })
    }
}

/// Average Degree of Redundancy (\bar{r}) for a target T and sources S_1, ..., S_n.
///
/// ```text
/// \bar{r}(T; S_1...S_n) = (Σ_i I(T; S_i)) / I(T; S_1...S_n)
/// ```
///
/// - `marginal_mis`: [I(T;S_1), ..., I(T;S_n)]
/// - `joint_mi`: I(T; S_1...S_n), which must be positive for the ratio to be meaningful.
/// - Undefined and policy-unstable cases are represented by [`NormalizedInvariantStatus`], never
///   by a floating-point sentinel.
pub fn average_degree_of_redundancy(
    marginal_mis: &[f64],
    joint_mi: f64,
) -> NormalizedInvariantReport {
    average_degree_of_redundancy_with_policy(
        marginal_mis,
        joint_mi,
        NormalizedInvariantPolicy::default(),
    )
}

/// Evaluate \bar{r} under an explicit small-denominator policy.
pub fn average_degree_of_redundancy_with_policy(
    marginal_mis: &[f64],
    joint_mi: f64,
    policy: NormalizedInvariantPolicy,
) -> NormalizedInvariantReport {
    const DEFINITION: &str = "sum_i I(T;S_i) / I(T;S_1,...,S_n)";
    let status = normalized_invariant_input_status(marginal_mis, joint_mi, policy);
    if status != NormalizedInvariantStatus::Defined {
        return undefined_normalized_report(DEFINITION, joint_mi, status, policy);
    }
    let value = stable_ratio_sum(marginal_mis, joint_mi);
    if !value.is_finite() {
        return undefined_normalized_report(
            DEFINITION,
            joint_mi,
            NormalizedInvariantStatus::NumericallyUnrepresentable,
            policy,
        );
    }
    NormalizedInvariantReport {
        value: Some(value),
        numerator_nats: finite_original_sum(marginal_mis),
        denominator_nats: Some(joint_mi),
        definition: DEFINITION,
        unit: NormalizedInvariantUnit::Unitless,
        status: NormalizedInvariantStatus::Defined,
        policy,
    }
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
/// - Undefined and policy-unstable cases are represented by [`NormalizedInvariantStatus`], never
///   by a floating-point sentinel.
pub fn average_degree_of_vulnerability(
    joint_mi: f64,
    leave_one_out_mis: &[f64],
) -> NormalizedInvariantReport {
    average_degree_of_vulnerability_with_policy(
        joint_mi,
        leave_one_out_mis,
        NormalizedInvariantPolicy::default(),
    )
}

/// Evaluate \bar{v} under an explicit small-denominator policy.
pub fn average_degree_of_vulnerability_with_policy(
    joint_mi: f64,
    leave_one_out_mis: &[f64],
    policy: NormalizedInvariantPolicy,
) -> NormalizedInvariantReport {
    const DEFINITION: &str = "sum_i (I(T;S_1,...,S_n) - I(T;S_-i)) / I(T;S_1,...,S_n)";
    let status = normalized_invariant_input_status(leave_one_out_mis, joint_mi, policy);
    if status != NormalizedInvariantStatus::Defined {
        return undefined_normalized_report(DEFINITION, joint_mi, status, policy);
    }
    let value = stable_conditional_ratio_sum(joint_mi, leave_one_out_mis);
    if !value.is_finite() {
        return undefined_normalized_report(
            DEFINITION,
            joint_mi,
            NormalizedInvariantStatus::NumericallyUnrepresentable,
            policy,
        );
    }
    let numerator = value * joint_mi;
    let numerator_nats = numerator.is_finite().then_some(numerator);
    NormalizedInvariantReport {
        value: Some(value),
        numerator_nats,
        denominator_nats: Some(joint_mi),
        definition: DEFINITION,
        unit: NormalizedInvariantUnit::Unitless,
        status: NormalizedInvariantStatus::Defined,
        policy,
    }
}

fn normalized_invariant_input_status(
    terms: &[f64],
    denominator: f64,
    policy: NormalizedInvariantPolicy,
) -> NormalizedInvariantStatus {
    if terms.is_empty() {
        return NormalizedInvariantStatus::EmptyTerms;
    }
    if !denominator.is_finite() || terms.iter().any(|value| !value.is_finite()) {
        return NormalizedInvariantStatus::NonFiniteInput;
    }
    if denominator <= 0.0 {
        return NormalizedInvariantStatus::NonPositiveDenominator;
    }
    if denominator <= policy.minimum_denominator_nats {
        return NormalizedInvariantStatus::DenominatorBelowPolicyThreshold;
    }
    NormalizedInvariantStatus::Defined
}

fn undefined_normalized_report(
    definition: &'static str,
    denominator: f64,
    status: NormalizedInvariantStatus,
    policy: NormalizedInvariantPolicy,
) -> NormalizedInvariantReport {
    NormalizedInvariantReport {
        value: None,
        numerator_nats: None,
        denominator_nats: denominator.is_finite().then_some(denominator),
        definition,
        unit: NormalizedInvariantUnit::Unitless,
        status,
        policy,
    }
}

fn finite_original_sum(values: &[f64]) -> Option<f64> {
    let sum = compensated_sum(values.iter().copied());
    sum.is_finite().then_some(sum)
}

fn validate_discrete_variables(context: &'static str, vars: &[&[u32]]) -> PidResult<usize> {
    let Some(first) = vars.first() else {
        return Err(PidError::InvalidConfig {
            context,
            message: "need at least 1 variable",
        });
    };
    let n_samples = first.len();
    if n_samples == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "empty sample set (need n_samples > 0)",
        });
    }
    for variable in vars.iter().skip(1) {
        if variable.len() != n_samples {
            return Err(PidError::RowCountMismatch {
                context,
                left_rows: n_samples,
                right_rows: variable.len(),
            });
        }
    }
    Ok(n_samples)
}

fn entropy_family_resource_estimate(
    operation: &'static str,
    n_samples: usize,
    total_projection_width: u128,
    projection_count: u128,
) -> PidResult<ResourceEstimate> {
    let samples = n_samples as u128;
    let estimated_bytes = samples
        .checked_mul(size_of::<usize>() as u128)
        .ok_or(PidError::SizeOverflow { operation })?;
    let sort_and_run_passes = u128::from(ceil_log2(n_samples))
        .checked_add(1)
        .ok_or(PidError::SizeOverflow { operation })?;
    let comparison_work = samples
        .checked_mul(total_projection_width)
        .and_then(|value| value.checked_mul(sort_and_run_passes))
        .ok_or(PidError::SizeOverflow { operation })?;
    let initialization_work = samples
        .checked_mul(projection_count)
        .ok_or(PidError::SizeOverflow { operation })?;
    let operations_hint = comparison_work
        .checked_add(initialization_work)
        .ok_or(PidError::SizeOverflow { operation })?;

    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: 0,
        operations_hint,
    })
}

fn ceil_log2(value: usize) -> u32 {
    if value <= 1 {
        0
    } else {
        usize::BITS - (value - 1).leading_zeros()
    }
}

struct EntropyWorkspace {
    indices: Vec<usize>,
}

impl EntropyWorkspace {
    fn new(operation: &'static str, n_samples: usize, budget: ResourceBudget) -> PidResult<Self> {
        Ok(Self {
            indices: try_vec_with_capacity(operation, n_samples, budget)?,
        })
    }

    fn entropy_single(&mut self, operation: &'static str, variable: &[u32]) -> PidResult<f64> {
        self.entropy_by(operation, variable.len(), |left, right| {
            variable[left].cmp(&variable[right])
        })
    }

    fn entropy_joint(&mut self, operation: &'static str, vars: &[&[u32]]) -> PidResult<f64> {
        if vars.is_empty() {
            return Ok(0.0);
        }
        self.entropy_by(operation, vars[0].len(), |left, right| {
            compare_joint_rows(vars, left, right, None)
        })
    }

    fn entropy_excluding(
        &mut self,
        operation: &'static str,
        vars: &[&[u32]],
        excluded: usize,
    ) -> PidResult<f64> {
        if vars.len() == 1 {
            return Ok(0.0);
        }
        self.entropy_by(operation, vars[0].len(), |left, right| {
            compare_joint_rows(vars, left, right, Some(excluded))
        })
    }

    fn entropy_by(
        &mut self,
        operation: &'static str,
        n_samples: usize,
        compare: impl Fn(usize, usize) -> Ordering,
    ) -> PidResult<f64> {
        self.indices.clear();
        self.indices.extend(0..n_samples);
        self.indices
            .sort_unstable_by(|left, right| compare(*left, *right));

        let n_float = n_samples as f64;
        let mut entropy = CompensatedAccumulator::default();
        let mut run_length = 1_usize;
        for rows in self.indices.windows(2) {
            if compare(rows[0], rows[1]) == Ordering::Equal {
                run_length = run_length
                    .checked_add(1)
                    .ok_or(PidError::SizeOverflow { operation })?;
            } else {
                entropy.add(entropy_term(run_length, n_float));
                run_length = 1;
            }
        }
        entropy.add(entropy_term(run_length, n_float));
        Ok(entropy.finish())
    }
}

fn compare_joint_rows(
    vars: &[&[u32]],
    left: usize,
    right: usize,
    excluded: Option<usize>,
) -> Ordering {
    for (index, variable) in vars.iter().enumerate() {
        if excluded == Some(index) {
            continue;
        }
        let order = variable[left].cmp(&variable[right]);
        if order != Ordering::Equal {
            return order;
        }
    }
    Ordering::Equal
}

fn entropy_term(count: usize, n: f64) -> f64 {
    let count = count as f64;
    (count / n) * (n / count).ln()
}

#[derive(Default)]
struct CompensatedAccumulator {
    sum: f64,
    correction: f64,
}

impl CompensatedAccumulator {
    fn add(&mut self, value: f64) {
        let next = self.sum + value;
        if self.sum.abs() >= value.abs() {
            self.correction += (self.sum - next) + value;
        } else {
            self.correction += (value - next) + self.sum;
        }
        self.sum = next;
    }

    fn finish(self) -> f64 {
        self.sum + self.correction
    }
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
    let mut accumulator = CompensatedAccumulator::default();
    for value in values {
        accumulator.add(value);
    }
    accumulator.finish()
}

#[cfg(test)]
mod tests {
    use super::{
        co_information_pairwise_discrete_with_budget, entropy_discrete_with_budget,
        joint_entropy_discrete_resource_estimate, o_information_discrete_with_budget,
    };
    use crate::{PidError, ResourceBudget};

    fn tiny_memory_budget() -> ResourceBudget {
        ResourceBudget {
            max_bytes: 7,
            max_pairwise_distances: 1,
            max_operations_hint: 10_000,
            max_threads: 1,
        }
    }

    #[test]
    fn entropy_rejects_tiny_budget_before_allocating() {
        let values = [0_u32, 1, 0, 1];

        let error = entropy_discrete_with_budget(&values, tiny_memory_budget()).unwrap_err();
        let expected_bytes = (values.len() * std::mem::size_of::<usize>()) as u128;

        assert!(matches!(
            error,
            PidError::ResourceLimitExceeded {
                operation: "entropy_discrete",
                resource: "bytes",
                requested,
                limit: 7,
            } if requested == expected_bytes
        ));
    }

    #[test]
    fn aggregate_invariant_rejects_tiny_budget_before_allocating() {
        let x = [0_u32, 0, 1, 1];
        let y = [0_u32, 1, 0, 1];
        let z = [0_u32, 1, 1, 0];

        let error =
            o_information_discrete_with_budget(&[&x, &y, &z], tiny_memory_budget()).unwrap_err();
        let expected_bytes = (x.len() * std::mem::size_of::<usize>()) as u128;

        assert!(matches!(
            error,
            PidError::ResourceLimitExceeded {
                operation: "o_information_discrete",
                resource: "bytes",
                requested,
                limit: 7,
            } if requested == expected_bytes
        ));
    }

    #[test]
    fn aggregate_invariant_checks_total_operation_budget() {
        let x = [0_u32, 0, 1, 1];
        let y = [0_u32, 1, 0, 1];
        let z = [0_u32, 1, 1, 0];
        let budget = ResourceBudget {
            max_bytes: 1_024,
            max_pairwise_distances: 1,
            max_operations_hint: 1,
            max_threads: 1,
        };

        let error = co_information_pairwise_discrete_with_budget(&x, &y, &z, budget).unwrap_err();

        assert!(matches!(
            error,
            PidError::ResourceLimitExceeded {
                operation: "co_information_pairwise_discrete",
                resource: "operations_hint",
                requested: 172,
                limit: 1,
            }
        ));
    }

    #[test]
    fn giant_joint_shape_produces_structured_resource_error() {
        let result =
            joint_entropy_discrete_resource_estimate(usize::MAX, usize::MAX).and_then(|estimate| {
                ResourceBudget::default().check("joint_entropy_discrete", estimate)
            });

        assert!(matches!(
            result,
            Err(PidError::SizeOverflow { .. } | PidError::ResourceLimitExceeded { .. })
        ));
    }
}
