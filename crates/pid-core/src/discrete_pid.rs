//! Williams--Beer `I_min` on an explicit empirical categorical distribution.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED.** The redundancy functional and PID identities implement Williams and Beer
//! (2010). The default stable surface provides empirical categorical two- and three-source code.
//! Budgeted entry points cover both source counts; the two-source path additionally exposes
//! cooperative cancellation. These are project-defined software contracts around the same
//! categorical functional.
//!
//! Method catalog: pid.imin
//!
//! **PROJECT-DEFINED COMPOSITION.** The fitted-quantized entry points consume categorical matrices
//! produced by reusable fitted quantizers, retain their reports, and then evaluate `I_min`.
//! Quantized inputs define a different categorical estimand and do not turn `I_min` into a
//! continuous estimator.
//!
//! Method catalog: pid.fitted-quantized-imin
//!
//! # New project validation
//!
//! `FINITE_ALPHABET_PLUGIN_CONVERGENCE.md` gives a new pid-rs proof for the existing paper-defined
//! functional. It proves exact-real plug-in convergence for the fixed two- and three-source
//! lattices on fixed finite alphabets. It allows minimum ties because a finite minimum is
//! continuous, but it does not claim differentiability at a tie. The sampling result needs i.i.d.
//! or strictly stationary and ergodic rows. A training artifact must be independent of the raw
//! evaluation sequence. The frozen map must be measurable with respect to the training sigma-field
//! and raw input. It must return a valid finite output with conditional probability one. Evaluation
//! rows must be conditionally i.i.d. given the training sigma-field. The result does not prove
//! binary64 asymptotics, dependence-aware validity, or a new PID method. The method catalog
//! records this evidence under `validation.finite-alphabet-plugin-convergence`.
//!
//! Numeric quantization defines new categorical variables; it does not evade dimensionality or
//! estimate continuous PID. The stable API uses a reusable fitted quantizer so training edges are
//! never silently re-fit on held-out evaluation rows.
//!
//! # Strategy
//!
//! The public paths differ only in how their categorical variables are defined:
//!
//! 1. `imin_pid2` and `imin_pid3` consume caller-supplied categorical row labels directly.
//!    Equality of complete rows defines each empirical state; numeric label spacing and order have
//!    no meaning.
//! 2. `imin_pid*_quantized` consumes the outputs of separately fitted, fixed
//!    [`crate::stable::quantized::EqualWidthQuantizer`] instances. The retained reports make the
//!    training edges, transform hashes, out-of-range policy, and evaluation occupancy part of the
//!    quantized estimand.
//! 3. The feature-gated `same_sample_quantized_imin_pid*` compatibility paths derive each
//!    column's range from the evaluated rows and select bins with the exact binary64-significand
//!    rule used by the feature-gated internal `quantize_equal_width` implementation. They
//!    materialize no fitted edge vector. Their
//!    wrapper marks that exploratory target-use contract explicitly; they are not substitutes for
//!    the fitted-transform path in held-out inference.
//!
//! Method catalog: pid.same-sample-quantized-imin
//! Method catalog: quantization.same-sample-exact-significand
//!
//! After the categorical variables are fixed, every path counts one empirical PMF, computes all
//! required mutual informations and minimum-specific-information redundancies from that same PMF,
//! and applies the Williams--Beer Möbius identities. The two-source result has four named atoms;
//! the three-source result evaluates and inverts the full 18-antichain lattice.
//!
//! # Measure identity (discrete `I_min` vs continuous `I^sx_∩` — do not blur)
//!
//! The redundancy implemented here is the Williams & Beer (2010, arXiv:1004.2515)
//! `I_min` functional, **not** the discrete shared-exclusions `i^sx_∩` of
//! Makkeh et al. (2021). Non-negativity: this module is a **pure plug-in** — every
//! quantity (MI, `I_min`, and the Möbius atoms) is computed from the *same*
//! empirical (binned) pmf, so the mathematical output is the Williams–Beer decomposition of that
//! empirical pmf, and WB's non-negativity theorem applies directly. The implementation evaluates
//! logarithms and expectations in binary64, so atoms are non-negative only up to scale-aware
//! floating-point roundoff; no universal `1e-15` bound applies. A materially negative atom from
//! this module
//! indicates a bug, not a sampling artifact. (The situation differs for paths
//! that *mix* estimators — e.g. the continuous `pid2_isx`, whose `Unq`/`Syn`
//! subtract KSG MI and Ehrlich `I^sx` estimates with different bias profiles and
//! can go negative from estimator error alone — and from `I^sx_∩` itself, which
//! admits **genuinely** negative atoms by construction.) What finite samples and
//! quantization *do* cost this module is accuracy: the plug-in atoms of the
//! empirical pmf are biased, noisy estimates of the population atoms, so treat
//! small atom values as within sampling/quantization error, and use more samples
//! or fewer bins when the saturation diagnostics say so. Comparing this module's
//! output against the continuous `I^sx_∩` path
//! is a cross-measure comparison (Warning 6), valid only as a robustness check.
//! Separately, `I_min` does not satisfy the Harder et al. identity axiom: on independent two-bit
//! COPY it assigns `ln(2)` nats of redundancy, whereas that named axiom requires redundancy equal
//! to `I(S1;S2)`, which is zero for these independent sources. This is a property of the published
//! functional, not a numerical implementation defect.
//!
//! This replaces local-distance sparsity with empirical-cell sparsity: with `b` bins in each of
//! `d` coordinates there can be `b^d` joint cells. Results therefore require occupancy and
//! bin-sensitivity diagnostics even though their estimand no longer uses kNN geometry.
//!
//! # When this separate estimand can be useful
//!
//! - When the scientific question explicitly concerns declared quantized variables and the
//!   quantization design is part of the estimand.
//! - As a separately labeled cross-estimand sensitivity analysis after a continuous route
//!   abstains. Agreement is descriptive only; disagreement does not select either functional.
//! - Use reusable fitted quantizers when training/evaluation separation and full transform reports
//!   are required. The same-sample compatibility helpers are exploratory and retain only the
//!   requested bin count in Rust; deprecated Python migration dictionaries discard even that
//!   wrapper.
//!
//! # Limitations
//!
//! - Quantization destroys fine-grained information; results depend on `num_bins`.
//! - High-dimensional quantization is combinatorial (curse of dimensionality in bin counts).
//! - This module is designed for **low effective dimension** targets (after PLS/PCA reduction)
//!   or for scalar/low-d action spaces.

use crate::error::{PidError, PidResult};
use crate::exact_binary64::{
    exact_binary64_sum, EXACT_BINARY64_ADD_LIMB_VISIT_BOUND, EXACT_BINARY64_TOTAL_LIMB_VISIT_BOUND,
};
use crate::matrix::DiscreteMatRef;
#[cfg(feature = "experimental-pipelines")]
use crate::matrix::MatRef;
use crate::quantizer::{QuantizationReport, QuantizedData};
use crate::resource::{
    sort_unstable_by_with_cancellation, try_vec_with_capacity, CancellationToken, ResourceBudget,
    ResourceEstimate,
};
use crate::stats::compensated_sum;
use serde::Serialize;
use std::cmp::Ordering;

const MAX_EXACT_EMPIRICAL_SAMPLES: u128 = 1_u128 << 53;
const CANCELLATION_CHECK_INTERVAL: usize = 1_024;

/// How the categorical variables supplied to an `I_min` result were defined.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub enum IminInputEncoding {
    /// Caller-supplied categorical labels; only equality of complete rows is meaningful.
    Categorical,
    /// Labels produced by fixed quantizers fitted separately from the evaluated rows.
    FittedEqualWidth {
        /// Reports for each source in argument order, followed by the target.
        quantization_reports: Vec<QuantizationReport>,
    },
}

/// Empirical-input provenance carried by every Williams--Beer `I_min` result.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IminInputMetadata {
    pub encoding: IminInputEncoding,
    /// Observed row-state cardinality for each source, followed by the target.
    pub observed_cardinalities: Vec<usize>,
    pub population_caveat: &'static str,
}

/// Occupancy diagnostics for the joint empirical source-target PMF.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct IminEmpiricalPmfDiagnostics {
    pub sample_count: usize,
    pub observed_joint_states: usize,
    pub singleton_joint_states: usize,
    pub low_count_joint_states: usize,
    pub minimum_observed_count: usize,
    pub maximum_observed_count: usize,
    pub observed_coverage_indicator: f64,
}

/// Result of a discrete 2-source PID decomposition.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct IminPid2Result {
    pub redundancy: f64,
    pub unique_s1: f64,
    pub unique_s2: f64,
    pub synergy: f64,
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    pub mi_s1s2_t: f64,
    pub input: IminInputMetadata,
    pub empirical_pmf: IminEmpiricalPmfDiagnostics,
}

/// Quantize a continuous matrix into equal-width bins per dimension.
///
/// Each column is independently binned into `num_bins` equal-width bins spanning
/// the column's [min, max] range. Values exactly at `max` are placed in the last bin.
/// The final `fraction × num_bins` scaling is evaluated with integer significand arithmetic, so
/// bin counts above `2^53` are not rounded through an intermediate `f64`.
///
/// Returns a matrix of bin indices (nrows × ncols), stored row-major.
#[cfg(feature = "experimental-pipelines")]
pub(crate) fn quantize_equal_width(x: MatRef<'_>, num_bins: usize) -> PidResult<Vec<Vec<usize>>> {
    quantize_equal_width_with_budget(x, num_bins, ResourceBudget::default())
}

#[cfg(feature = "experimental-pipelines")]
pub(crate) fn quantize_equal_width_with_budget(
    x: MatRef<'_>,
    num_bins: usize,
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<usize>>> {
    const OPERATION: &str = "quantize_equal_width";
    if num_bins < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "num_bins must be >= 2",
        });
    }
    let n = x.nrows();
    let d = x.ncols();
    let coordinate_count = n.checked_mul(d).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    let estimated_bytes = (d as u128)
        .checked_mul(2 * std::mem::size_of::<f64>() as u128)
        .and_then(|bytes| {
            bytes.checked_add((n as u128).checked_mul(std::mem::size_of::<Vec<usize>>() as u128)?)
        })
        .and_then(|bytes| {
            bytes.checked_add(
                (coordinate_count as u128).checked_mul(std::mem::size_of::<usize>() as u128)?,
            )
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    budget.check(
        OPERATION,
        ResourceEstimate {
            estimated_bytes,
            pairwise_distances: 0,
            operations_hint: coordinate_count as u128,
        },
    )?;

    // Compute column min/max.
    let mut col_min = crate::resource::try_vec_filled(OPERATION, d, f64::INFINITY, budget)?;
    let mut col_max = crate::resource::try_vec_filled(OPERATION, d, f64::NEG_INFINITY, budget)?;
    for i in 0..n {
        let row = x.row(i);
        for j in 0..d {
            if row[j] < col_min[j] {
                col_min[j] = row[j];
            }
            if row[j] > col_max[j] {
                col_max[j] = row[j];
            }
        }
    }

    let mut out = try_vec_with_capacity(OPERATION, n, budget)?;
    for i in 0..n {
        let mut out_row = crate::resource::try_vec_filled(OPERATION, d, 0usize, budget)?;
        let row = x.row(i);
        for j in 0..d {
            let min = col_min[j];
            let max = col_max[j];
            let range = max - min;
            let bin = if min == max {
                0 // Constant column → all in bin 0.
            } else {
                // For opposite-sign values near f64::MAX, `max - min` overflows even though
                // every input is finite. Scale first in that case. Do not use a relative
                // "constant" tolerance here: at a large offset it can erase real, exactly
                // representable categories (for example 1e12 and 1e12 + 0.5).
                let frac = if range.is_finite() {
                    (row[j] - min) / range
                } else {
                    let scale = min.abs().max(max.abs());
                    let scaled_min = min / scale;
                    let scaled_max = max / scale;
                    (row[j] / scale - scaled_min) / (scaled_max - scaled_min)
                };
                scaled_equal_width_bin(frac.clamp(0.0, 1.0), num_bins)
            };
            out_row[j] = bin;
        }
        out.push(out_row);
    }
    Ok(out)
}

/// Return `floor(frac * num_bins)` without first rounding `num_bins` to an `f64`.
///
/// A `usize` bin count above `2^53` is not necessarily exactly representable in binary64. A direct
/// `frac * num_bins as f64` can therefore select the wrong bin even for an exact fraction such as
/// one half. Decomposing the finite binary64 fraction into its integer significand and power-of-two
/// denominator makes the product exact in `u128` on every supported 32-/64-bit target. `frac == 1`
/// retains the documented convention that the column maximum belongs to the final bin. The caller
/// must supply a finite fraction in `[0, 1]`.
#[cfg(feature = "experimental-pipelines")]
fn scaled_equal_width_bin(frac: f64, num_bins: usize) -> usize {
    debug_assert!(frac.is_finite() && (0.0..=1.0).contains(&frac));
    if frac <= 0.0 {
        return 0;
    }
    if frac >= 1.0 {
        return num_bins - 1;
    }

    let bits = frac.to_bits();
    let exponent_bits = ((bits >> 52) & 0x7ff) as u32;
    let fraction_bits = bits & ((1_u64 << 52) - 1);
    let (significand, denominator_shift) = if exponent_bits == 0 {
        // Subnormal: fraction_bits * 2^-1074. With a <=64-bit bin count the quotient is zero,
        // but retain the general representation rather than relying on that observation.
        (fraction_bits, 1074_u32)
    } else {
        ((1_u64 << 52) | fraction_bits, 1075_u32 - exponent_bits)
    };
    let product = u128::from(significand) * num_bins as u128;
    let bin = if denominator_shift >= u128::BITS {
        0
    } else {
        (product >> denominator_shift) as usize
    };
    bin.min(num_bins - 1)
}

/// Compute discrete Shannon entropy H(X) from bin assignments.
///
/// `bins` is n×d_x; entropy is computed over the joint distribution of all columns.
/// Units: nats (natural logarithm).
///
/// Occupancy is counted per **distinct bin vector** (the row slice is the histogram
/// key), so there is no packed-integer key and therefore no overflow/collision in
/// high dimension — distinct joint states never alias. `num_bins` is accepted for
/// interface symmetry with the quantize-based callers; the count is independent of
/// it.
#[cfg(test)]
pub(crate) fn discrete_entropy(bins: &[Vec<usize>], num_bins: usize) -> PidResult<f64> {
    let _ = num_bins;
    let n = bins.len();
    if n == 0 {
        return Ok(0.0);
    }
    let counts = count_dist(bins, ResourceBudget::default())?;
    Ok(entropy_from_counts(counts.counts.iter().copied(), n))
}

/// Compute discrete mutual information I(X;Y) from quantized data.
///
/// `x_bins` is n×d_x, `y_bins` is n×d_y.
/// I(X;Y) = H(X) + H(Y) - H(X,Y).
#[cfg(test)]
pub(crate) fn discrete_mi(
    x_bins: &[Vec<usize>],
    y_bins: &[Vec<usize>],
    num_bins: usize,
) -> PidResult<f64> {
    discrete_mi_with_budget(x_bins, y_bins, num_bins, ResourceBudget::default())
}

pub(crate) fn discrete_mi_with_budget(
    x_bins: &[Vec<usize>],
    y_bins: &[Vec<usize>],
    num_bins: usize,
    budget: ResourceBudget,
) -> PidResult<f64> {
    let cancellation = CancellationToken::new();
    discrete_mi_with_budget_and_cancellation(x_bins, y_bins, num_bins, budget, &cancellation)
}

pub(crate) fn discrete_mi_with_budget_and_cancellation(
    x_bins: &[Vec<usize>],
    y_bins: &[Vec<usize>],
    num_bins: usize,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    const OPERATION: &str = "discrete_mi";
    let _ = num_bins;
    if x_bins.len() != y_bins.len() {
        return Err(PidError::RowCountMismatch {
            context: "discrete_mi",
            left_rows: x_bins.len(),
            right_rows: y_bins.len(),
        });
    }
    let n = x_bins.len();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context: "discrete_mi",
            message: "need at least one paired sample",
        });
    }

    cancellation.check(OPERATION, 0, n)?;
    let x_width = x_bins[0].len();
    let y_width = y_bins[0].len();
    if x_width == 0 || y_width == 0 {
        return Err(PidError::InvalidConfig {
            context: "discrete_mi",
            message: "variables must have at least one categorical coordinate",
        });
    }
    if x_bins.iter().any(|row| row.len() != x_width)
        || y_bins.iter().any(|row| row.len() != y_width)
    {
        return Err(PidError::InvalidConfig {
            context: "discrete_mi",
            message: "categorical matrices must be rectangular",
        });
    }

    // Preserve the X/Y boundary explicitly. Concatenating ragged public inputs can alias distinct
    // pairs such as ([0], [1,2]) and ([0,1], [2]); rectangular validation above is still useful
    // because the documented inputs are matrices rather than arbitrary state sequences.
    validate_exact_sample_count("discrete_mi", n)?;
    let x_counts = count_dist_with_cancellation(x_bins, budget, cancellation)?;
    let y_counts = count_dist_with_cancellation(y_bins, budget, cancellation)?;
    let joint_counts = count_joint_dist_with_cancellation(x_bins, y_bins, budget, cancellation)?;
    let mut mi_sum = 0.0;
    let mut mi_correction = 0.0;
    let mut absolute_sum = 0.0;
    let mut absolute_correction = 0.0;
    for (index, ((x_state, y_state), joint_count)) in joint_counts.iter().enumerate() {
        check_cancellation(cancellation, OPERATION, index, joint_counts.len())?;
        let x_count = x_counts
            .get(x_state)
            .ok_or(PidError::NumericalInstability {
                context: "discrete_mi: missing X marginal count",
            })?;
        let y_count = y_counts
            .get(y_state)
            .ok_or(PidError::NumericalInstability {
                context: "discrete_mi: missing Y marginal count",
            })?;
        let term = discrete_mi_count_term(joint_count, n, x_count, y_count);
        neumaier_add(term, &mut mi_sum, &mut mi_correction);
        neumaier_add(term.abs(), &mut absolute_sum, &mut absolute_correction);
    }
    let mi = mi_sum + mi_correction;
    let absolute_term_sum = absolute_sum + absolute_correction;
    cancellation.check(OPERATION, joint_counts.len(), joint_counts.len())?;
    finalize_discrete_mi(mi, absolute_term_sum)
}

/// Evaluate the Williams--Beer `I_min` comparator on an explicit empirical categorical PMF.
///
/// Complete rows are categorical states: numeric spacing and label order have no meaning. This is
/// direct plug-in evaluation of the empirical PMF, not an unbiased population estimate and not
/// shared-exclusions PID.
pub fn imin_pid2(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<IminPid2Result> {
    imin_pid2_with_budget(s1, s2, target, ResourceBudget::default())
}

/// Conservative allocation-volume and comparison-work preflight for [`imin_pid2`].
///
/// The byte estimate includes nested-vector headers, sorted run-length histograms (including
/// repeated histogram construction), joined-source rows, and retained specific-information
/// tables. It assumes every input row can be a distinct state.
pub fn imin_pid2_resource_estimate(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<ResourceEstimate> {
    imin_resource_estimate_impl("imin_pid2", &[s1, s2], target)
}

/// [`imin_pid2`] with an explicit preflight resource ceiling.
pub fn imin_pid2_with_budget(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<IminPid2Result> {
    let cancellation = CancellationToken::new();
    imin_pid2_with_budget_and_cancellation(s1, s2, target, budget, &cancellation)
}

/// [`imin_pid2_with_budget`] with cooperative cancellation during categorical materialization,
/// histogram construction, specific-information evaluation, and PMF diagnostics.
pub fn imin_pid2_with_budget_and_cancellation(
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<IminPid2Result> {
    const OPERATION: &str = "imin_pid2";
    validate_discrete_inputs("imin_pid2", &[s1, s2], target, budget)?;
    cancellation.check(OPERATION, 0, s1.nrows())?;
    let s1_states = states_from_discrete_with_cancellation(OPERATION, s1, budget, cancellation)?;
    let s2_states = states_from_discrete_with_cancellation(OPERATION, s2, budget, cancellation)?;
    let target_states =
        states_from_discrete_with_cancellation(OPERATION, target, budget, cancellation)?;
    imin_pid2_states_with_cancellation(
        &s1_states,
        &s2_states,
        &target_states,
        IminInputEncoding::Categorical,
        budget,
        cancellation,
    )
}

/// Evaluate `I_min` for variables produced by separately fitted, fixed quantizers.
///
/// Each quantization report is embedded in the result, making training edges, scaling,
/// out-of-range policy, and evaluation occupancy part of the serialized estimand.
pub fn imin_pid2_quantized(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<IminPid2Result> {
    imin_pid2_quantized_with_budget(s1, s2, target, ResourceBudget::default())
}

/// Resource preflight for [`imin_pid2_quantized`], including copied quantization provenance.
pub fn imin_pid2_quantized_resource_estimate(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<ResourceEstimate> {
    quantized_imin_resource_estimate(
        "imin_pid2_quantized",
        &[s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        &[&s1.report, &s2.report, &target.report],
    )
}

/// [`imin_pid2_quantized`] with an explicit preflight resource ceiling.
pub fn imin_pid2_quantized_with_budget(
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
    budget: ResourceBudget,
) -> PidResult<IminPid2Result> {
    validate_discrete_inputs(
        "imin_pid2_quantized",
        &[s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        budget,
    )?;
    budget.check(
        "imin_pid2_quantized",
        imin_pid2_quantized_resource_estimate(s1, s2, target)?,
    )?;
    let s1_states = states_from_discrete("imin_pid2_quantized", s1.matrix.as_ref(), budget)?;
    let s2_states = states_from_discrete("imin_pid2_quantized", s2.matrix.as_ref(), budget)?;
    let target_states =
        states_from_discrete("imin_pid2_quantized", target.matrix.as_ref(), budget)?;
    let mut quantization_reports = try_vec_with_capacity("imin_pid2_quantized reports", 3, budget)?;
    quantization_reports.push(try_clone_quantization_report(
        "imin_pid2_quantized reports",
        &s1.report,
        budget,
    )?);
    quantization_reports.push(try_clone_quantization_report(
        "imin_pid2_quantized reports",
        &s2.report,
        budget,
    )?);
    quantization_reports.push(try_clone_quantization_report(
        "imin_pid2_quantized reports",
        &target.report,
        budget,
    )?);
    imin_pid2_states(
        &s1_states,
        &s2_states,
        &target_states,
        IminInputEncoding::FittedEqualWidth {
            quantization_reports,
        },
        budget,
    )
}

/// Research-only compatibility helper that derives equal-width labels from the evaluated rows.
///
/// Sources S1, S2 and target T are each quantized into `num_bins` equal-width bins.
/// Redundancy uses the minimum-specific-information (`I_min`) formula:
///
/// `Red(S1,S2;T) = Σ_t p(t) min(i_spec(S1;t), i_spec(S2;t))`
///
/// where `i_spec(S;t) = Σ_s p(s|t) log(p(t|s)/p(t))` is the specific information.
#[cfg(feature = "experimental-pipelines")]
pub fn same_sample_quantized_imin_pid2(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<crate::same_sample::ExploratorySameSampleQuantizedResult<IminPid2Result>> {
    if num_bins < 2 {
        return Err(PidError::InvalidConfig {
            context: "same_sample_quantized_imin_pid2",
            message: "num_bins must be >= 2",
        });
    }
    let n = s1.nrows();
    if s2.nrows() != n || target.nrows() != n {
        return Err(PidError::RowCountMismatch {
            context: "same_sample_quantized_imin_pid2",
            left_rows: n,
            right_rows: if s2.nrows() != n {
                s2.nrows()
            } else {
                target.nrows()
            },
        });
    }
    if n == 0 {
        // An empty joint pmf would silently yield an all-zero decomposition; fail loudly.
        return Err(PidError::InvalidConfig {
            context: "same_sample_quantized_imin_pid2",
            message: "need at least 1 sample (got 0 rows)",
        });
    }

    check_same_sample_imin_aggregate_budget("same_sample_quantized_imin_pid2", &[s1, s2], target)?;

    // 1. Quantize all three variables.
    let s1_bins = quantize_equal_width(s1, num_bins)?;
    let s2_bins = quantize_equal_width(s2, num_bins)?;
    let t_bins = quantize_equal_width(target, num_bins)?;

    let categorical_result = imin_pid2_states(
        &s1_bins,
        &s2_bins,
        &t_bins,
        IminInputEncoding::Categorical,
        ResourceBudget::default(),
    )?;
    Ok(crate::same_sample::ExploratorySameSampleQuantizedResult::new(categorical_result, num_bins))
}

fn imin_pid2_states(
    s1_bins: &[Vec<usize>],
    s2_bins: &[Vec<usize>],
    t_bins: &[Vec<usize>],
    encoding: IminInputEncoding,
    budget: ResourceBudget,
) -> PidResult<IminPid2Result> {
    let cancellation = CancellationToken::new();
    imin_pid2_states_with_cancellation(s1_bins, s2_bins, t_bins, encoding, budget, &cancellation)
}

fn imin_pid2_states_with_cancellation(
    s1_bins: &[Vec<usize>],
    s2_bins: &[Vec<usize>],
    t_bins: &[Vec<usize>],
    encoding: IminInputEncoding,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<IminPid2Result> {
    // Compute MI terms from exactly the same empirical PMF.
    let mi_s1_t =
        discrete_mi_with_budget_and_cancellation(s1_bins, t_bins, 0, budget, cancellation)?;
    let mi_s2_t =
        discrete_mi_with_budget_and_cancellation(s2_bins, t_bins, 0, budget, cancellation)?;

    // For joint MI: concatenate S1 and S2 bins.
    let s1s2_bins = join_bins_pair_with_cancellation(s1_bins, s2_bins, budget, cancellation)?;
    let mi_s1s2_t =
        discrete_mi_with_budget_and_cancellation(&s1s2_bins, t_bins, 0, budget, cancellation)?;

    // 3. Compute the I_min redundancy via per-target-outcome specific information.
    let redundancy =
        discrete_imin_redundancy_with_cancellation(s1_bins, s2_bins, t_bins, budget, cancellation)?;

    // 4. Derive PID atoms.
    let unique_s1 = mi_s1_t - redundancy;
    let unique_s2 = mi_s2_t - redundancy;
    // Give the symmetric Williams--Beer PID2 residual one order-independent interpretation over
    // the four already represented coordinates. This does not make the MI or I_min estimators
    // exact and does not transfer any shared-exclusions claim into I_min.
    let synergy = exact_binary64_sum([mi_s1s2_t, -mi_s1_t, -mi_s2_t, redundancy]);

    let (input, empirical_pmf) = imin_input_metadata_with_cancellation(
        &[s1_bins, s2_bins, t_bins],
        encoding,
        budget,
        cancellation,
    )?;
    Ok(IminPid2Result {
        redundancy,
        unique_s1,
        unique_s2,
        synergy,
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        input,
        empirical_pmf,
    })
}

/// Discrete Williams–Beer-style `I_min` redundancy.
///
/// `Red(S1,S2;T) = Σ_t p(t) min(i_spec(S1;t), i_spec(S2;t))`
///
/// where `i_spec(S;t) = Σ_s p(s|t) log(p(t|s)/p(t))`.
fn discrete_imin_redundancy_with_cancellation(
    s1_bins: &[Vec<usize>],
    s2_bins: &[Vec<usize>],
    t_bins: &[Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    const OPERATION: &str = "I_min redundancy";
    let n = s1_bins.len();
    if n == 0 {
        return Ok(0.0);
    }
    let inv_n = 1.0 / n as f64;

    // Build marginal distributions and conditional distributions.
    // For each source S, compute p(s) and p(s|t) and p(t|s).
    cancellation.check(OPERATION, 0, n)?;
    let t_counts = count_dist_with_cancellation(t_bins, budget, cancellation)?;
    let s1_counts = count_dist_with_cancellation(s1_bins, budget, cancellation)?;
    let s2_counts = count_dist_with_cancellation(s2_bins, budget, cancellation)?;

    // Joint counts: (s, t) for each source.
    let s1t_counts = count_joint_dist_with_cancellation(s1_bins, t_bins, budget, cancellation)?;
    let s2t_counts = count_joint_dist_with_cancellation(s2_bins, t_bins, budget, cancellation)?;

    // Compute specific information for each (source, t) pair:
    // i_spec(S;t) = Σ_s p(s|t) log(p(t|s) / p(t))
    //             = Σ_s [p(s,t)/p(t)] log[p(s,t) * n / (p(s) * p(t) * n)]
    //             = Σ_s [count(s,t)/count(t)] log[count(s,t) * n / (count(s) * count(t))]
    let i_spec_s1 = specific_information_with_cancellation(
        &s1t_counts,
        &s1_counts,
        &t_counts,
        n,
        budget,
        cancellation,
    )?;
    let i_spec_s2 = specific_information_with_cancellation(
        &s2t_counts,
        &s2_counts,
        &t_counts,
        n,
        budget,
        cancellation,
    )?;

    // Red = Σ_t p(t) min(i_spec(S1;t), i_spec(S2;t))
    let mut sum = 0.0;
    let mut correction = 0.0;
    for (index, (t_key, ct)) in t_counts.iter().enumerate() {
        check_cancellation(cancellation, OPERATION, index, t_counts.len())?;
        let p_t = ct as f64 * inv_n;
        let is1 = i_spec_s1.required(
            t_key,
            "I_min PID2 redundancy: missing or non-finite source-1 specific information",
        )?;
        let is2 = i_spec_s2.required(
            t_key,
            "I_min PID2 redundancy: missing or non-finite source-2 specific information",
        )?;
        neumaier_add(p_t * is1.min(is2), &mut sum, &mut correction);
    }
    cancellation.check(OPERATION, t_counts.len(), t_counts.len())?;
    Ok(sum + correction)
}

fn validate_exact_sample_count(operation: &'static str, sample_count: usize) -> PidResult<()> {
    if sample_count as u128 > MAX_EXACT_EMPIRICAL_SAMPLES {
        return Err(PidError::SampleCountPrecisionExceeded {
            operation,
            sample_count: sample_count as u128,
            maximum_exact_sample_count: MAX_EXACT_EMPIRICAL_SAMPLES,
        });
    }
    Ok(())
}

fn check_cancellation(
    cancellation: &CancellationToken,
    operation: &'static str,
    completed_units: usize,
    total_units: usize,
) -> PidResult<()> {
    if completed_units == 0
        || completed_units == total_units
        || completed_units.is_multiple_of(CANCELLATION_CHECK_INTERVAL)
    {
        cancellation.check(operation, completed_units, total_units)?;
    }
    Ok(())
}

fn checked_add_resource(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_add(right)
        .ok_or(PidError::SizeOverflow { operation })
}

fn checked_mul_resource(operation: &'static str, left: u128, right: u128) -> PidResult<u128> {
    left.checked_mul(right)
        .ok_or(PidError::SizeOverflow { operation })
}

pub(crate) fn quantization_report_heap_bytes(
    operation: &'static str,
    report: &QuantizationReport,
) -> PidResult<u128> {
    let outer_headers = checked_mul_resource(
        operation,
        report.bin_edges.len() as u128,
        std::mem::size_of::<Vec<f64>>() as u128,
    )?;
    let edge_values = report.bin_edges.iter().try_fold(0u128, |sum, edges| {
        checked_add_resource(
            operation,
            sum,
            checked_mul_resource(
                operation,
                edges.len() as u128,
                std::mem::size_of::<f64>() as u128,
            )?,
        )
    })?;
    let diagnostic_values = [
        report.distinct_binary64_edge_value_counts.len(),
        report.positive_width_interval_counts.len(),
        report.reachable_binary64_label_counts.len(),
        report.observed_label_counts.len(),
    ]
    .into_iter()
    .try_fold(0u128, |sum, count| {
        checked_add_resource(
            operation,
            sum,
            checked_mul_resource(
                operation,
                count as u128,
                std::mem::size_of::<usize>() as u128,
            )?,
        )
    })?;
    checked_add_resource(
        operation,
        checked_add_resource(
            operation,
            checked_add_resource(operation, outer_headers, edge_values)?,
            diagnostic_values,
        )?,
        report.scaling_description.len() as u128,
    )
}

fn try_clone_usize_report_values(
    operation: &'static str,
    values: &[usize],
    budget: ResourceBudget,
) -> PidResult<Vec<usize>> {
    let mut copy = try_vec_with_capacity(operation, values.len(), budget)?;
    copy.extend_from_slice(values);
    Ok(copy)
}

fn try_clone_usize_report_values_with_cancellation(
    operation: &'static str,
    values: &[usize],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
    completed_units: &mut usize,
    total_units: usize,
) -> PidResult<Vec<usize>> {
    let mut copy = try_vec_with_capacity(operation, values.len(), budget)?;
    for chunk in values.chunks(CANCELLATION_CHECK_INTERVAL) {
        cancellation.check(operation, *completed_units, total_units)?;
        copy.extend_from_slice(chunk);
        *completed_units = completed_units
            .checked_add(chunk.len())
            .ok_or(PidError::SizeOverflow { operation })?;
    }
    Ok(copy)
}

pub(crate) fn try_clone_quantization_report(
    operation: &'static str,
    report: &QuantizationReport,
    budget: ResourceBudget,
) -> PidResult<QuantizationReport> {
    let mut bin_edges = try_vec_with_capacity(operation, report.bin_edges.len(), budget)?;
    for edges in &report.bin_edges {
        let mut copied_edges = try_vec_with_capacity(operation, edges.len(), budget)?;
        copied_edges.extend_from_slice(edges);
        bin_edges.push(copied_edges);
    }
    let distinct_binary64_edge_value_counts = try_clone_usize_report_values(
        operation,
        &report.distinct_binary64_edge_value_counts,
        budget,
    )?;
    let positive_width_interval_counts =
        try_clone_usize_report_values(operation, &report.positive_width_interval_counts, budget)?;
    let reachable_binary64_label_counts =
        try_clone_usize_report_values(operation, &report.reachable_binary64_label_counts, budget)?;
    let observed_label_counts =
        try_clone_usize_report_values(operation, &report.observed_label_counts, budget)?;
    let string_bytes =
        ResourceEstimate::contiguous::<u8>(operation, report.scaling_description.len())?;
    budget.check(operation, string_bytes)?;
    let mut scaling_description = String::new();
    scaling_description
        .try_reserve_exact(report.scaling_description.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: report.scaling_description.len() as u128,
        })?;
    scaling_description.push_str(&report.scaling_description);

    Ok(QuantizationReport {
        bin_edges,
        training_input_hash: report.training_input_hash,
        transform_input_hash: report.transform_input_hash,
        categorical_output_hash: report.categorical_output_hash,
        out_of_range_policy: report.out_of_range_policy,
        scaling_description,
        n_samples: report.n_samples,
        dimensions: report.dimensions,
        bins_per_dimension: report.bins_per_dimension,
        distinct_binary64_edge_value_counts,
        positive_width_interval_counts,
        reachable_binary64_label_counts,
        observed_label_counts,
        nominal_joint_cardinality: report.nominal_joint_cardinality,
        reachable_joint_cardinality: report.reachable_joint_cardinality,
        observed_joint_cardinality: report.observed_joint_cardinality,
        empty_joint_cells: report.empty_joint_cells,
        structurally_unreachable_joint_cells: report.structurally_unreachable_joint_cells,
        unobserved_reachable_joint_cells: report.unobserved_reachable_joint_cells,
        low_count_joint_cells: report.low_count_joint_cells,
        minimum_observed_cell_count: report.minimum_observed_cell_count,
        maximum_observed_cell_count: report.maximum_observed_cell_count,
        estimand_statement: report.estimand_statement,
    })
}

pub(crate) fn try_clone_quantization_report_with_cancellation(
    operation: &'static str,
    report: &QuantizationReport,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<QuantizationReport> {
    let edge_count = report.bin_edges.iter().try_fold(0usize, |total, edges| {
        total
            .checked_add(edges.len())
            .ok_or(PidError::SizeOverflow { operation })
    })?;
    let diagnostic_count = [
        report.distinct_binary64_edge_value_counts.len(),
        report.positive_width_interval_counts.len(),
        report.reachable_binary64_label_counts.len(),
        report.observed_label_counts.len(),
    ]
    .into_iter()
    .try_fold(0usize, |sum, count| {
        sum.checked_add(count)
            .ok_or(PidError::SizeOverflow { operation })
    })?;
    let total_units = edge_count
        .checked_add(diagnostic_count)
        .and_then(|value| value.checked_add(report.scaling_description.len()))
        .ok_or(PidError::SizeOverflow { operation })?;
    cancellation.check(operation, 0, total_units)?;
    let mut completed_units = 0usize;
    let mut bin_edges = try_vec_with_capacity(operation, report.bin_edges.len(), budget)?;
    for edges in &report.bin_edges {
        let mut copied_edges = try_vec_with_capacity(operation, edges.len(), budget)?;
        for chunk in edges.chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, completed_units, total_units)?;
            copied_edges.extend_from_slice(chunk);
            completed_units = completed_units
                .checked_add(chunk.len())
                .ok_or(PidError::SizeOverflow { operation })?;
        }
        bin_edges.push(copied_edges);
    }
    let distinct_binary64_edge_value_counts = try_clone_usize_report_values_with_cancellation(
        operation,
        &report.distinct_binary64_edge_value_counts,
        budget,
        cancellation,
        &mut completed_units,
        total_units,
    )?;
    let positive_width_interval_counts = try_clone_usize_report_values_with_cancellation(
        operation,
        &report.positive_width_interval_counts,
        budget,
        cancellation,
        &mut completed_units,
        total_units,
    )?;
    let reachable_binary64_label_counts = try_clone_usize_report_values_with_cancellation(
        operation,
        &report.reachable_binary64_label_counts,
        budget,
        cancellation,
        &mut completed_units,
        total_units,
    )?;
    let observed_label_counts = try_clone_usize_report_values_with_cancellation(
        operation,
        &report.observed_label_counts,
        budget,
        cancellation,
        &mut completed_units,
        total_units,
    )?;
    let string_bytes =
        ResourceEstimate::contiguous::<u8>(operation, report.scaling_description.len())?;
    budget.check(operation, string_bytes)?;
    let mut scaling_description = String::new();
    scaling_description
        .try_reserve_exact(report.scaling_description.len())
        .map_err(|_| PidError::AllocationFailed {
            operation,
            requested_bytes: report.scaling_description.len() as u128,
        })?;
    cancellation.check(operation, completed_units, total_units)?;
    scaling_description.push_str(&report.scaling_description);
    completed_units = completed_units
        .checked_add(report.scaling_description.len())
        .ok_or(PidError::SizeOverflow { operation })?;
    cancellation.check(operation, completed_units, total_units)?;

    Ok(QuantizationReport {
        bin_edges,
        training_input_hash: report.training_input_hash,
        transform_input_hash: report.transform_input_hash,
        categorical_output_hash: report.categorical_output_hash,
        out_of_range_policy: report.out_of_range_policy,
        scaling_description,
        n_samples: report.n_samples,
        dimensions: report.dimensions,
        bins_per_dimension: report.bins_per_dimension,
        distinct_binary64_edge_value_counts,
        positive_width_interval_counts,
        reachable_binary64_label_counts,
        observed_label_counts,
        nominal_joint_cardinality: report.nominal_joint_cardinality,
        reachable_joint_cardinality: report.reachable_joint_cardinality,
        observed_joint_cardinality: report.observed_joint_cardinality,
        empty_joint_cells: report.empty_joint_cells,
        structurally_unreachable_joint_cells: report.structurally_unreachable_joint_cells,
        unobserved_reachable_joint_cells: report.unobserved_reachable_joint_cells,
        low_count_joint_cells: report.low_count_joint_cells,
        minimum_observed_cell_count: report.minimum_observed_cell_count,
        maximum_observed_cell_count: report.maximum_observed_cell_count,
        estimand_statement: report.estimand_statement,
    })
}

fn add_estimate_resources(
    operation: &'static str,
    estimate: ResourceEstimate,
    extra_bytes: u128,
    extra_operations: u128,
) -> PidResult<ResourceEstimate> {
    Ok(ResourceEstimate {
        estimated_bytes: checked_add_resource(operation, estimate.estimated_bytes, extra_bytes)?,
        pairwise_distances: estimate.pairwise_distances,
        operations_hint: checked_add_resource(
            operation,
            estimate.operations_hint,
            extra_operations,
        )?,
    })
}

fn quantized_imin_resource_estimate(
    operation: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    reports: &[&QuantizationReport],
) -> PidResult<ResourceEstimate> {
    let reports_heap = reports.iter().try_fold(
        checked_mul_resource(
            operation,
            reports.len() as u128,
            std::mem::size_of::<QuantizationReport>() as u128,
        )?,
        |sum, report| {
            checked_add_resource(
                operation,
                sum,
                quantization_report_heap_bytes(operation, report)?,
            )
        },
    )?;
    let report_copy_operations = reports.iter().try_fold(0u128, |sum, report| {
        checked_add_resource(operation, sum, report.copy_operations_hint(operation)?)
    })?;
    add_estimate_resources(
        operation,
        imin_resource_estimate_impl(operation, sources, target)?,
        reports_heap,
        report_copy_operations,
    )
}

fn ceil_log2(value: usize) -> u128 {
    if value <= 1 {
        1
    } else {
        (usize::BITS - (value - 1).leading_zeros()) as u128
    }
}

fn validate_discrete_shapes(
    operation: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
) -> PidResult<()> {
    if sources.is_empty() {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "need at least one source",
        });
    }
    let n = target.nrows();
    if n == 0 {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "need at least one empirical sample",
        });
    }
    if target.ncols() == 0 || sources.iter().any(|source| source.ncols() == 0) {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "categorical variables must have at least one coordinate",
        });
    }
    for source in sources {
        if source.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: operation,
                left_rows: n,
                right_rows: source.nrows(),
            });
        }
    }
    validate_exact_sample_count(operation, n)
}

fn imin_resource_estimate_impl(
    operation: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
) -> PidResult<ResourceEstimate> {
    validate_discrete_shapes(operation, sources, target)?;
    let source_coordinates = sources.iter().try_fold(0u128, |sum, source| {
        checked_add_resource(operation, sum, source.ncols() as u128)
    })?;
    imin_resource_estimate_from_dimensions(
        operation,
        target.nrows(),
        sources.len(),
        source_coordinates,
        target.ncols(),
    )
}

fn imin_resource_estimate_from_dimensions(
    operation: &'static str,
    n_rows: usize,
    source_count: usize,
    source_coordinates: u128,
    target_coordinates: usize,
) -> PidResult<ResourceEstimate> {
    if !matches!(source_count, 2 | 3) {
        return Err(PidError::NotImplemented {
            feature: "I_min resource estimates support exactly 2 or 3 sources",
        });
    }
    if n_rows == 0 {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "need at least one empirical sample",
        });
    }
    if source_coordinates == 0 || target_coordinates == 0 {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "categorical variables must have at least one coordinate",
        });
    }
    validate_exact_sample_count(operation, n_rows)?;

    let n = n_rows as u128;
    let variable_count = source_count as u128 + 1;
    let coordinates =
        checked_add_resource(operation, source_coordinates, target_coordinates as u128)?;
    let usize_bytes = std::mem::size_of::<usize>() as u128;
    let vec_header_bytes = std::mem::size_of::<Vec<usize>>() as u128;
    let slice_reference_bytes = std::mem::size_of::<&[usize]>() as u128;
    let joint_reference_bytes = std::mem::size_of::<(&[usize], &[usize])>() as u128;

    let state_payload = checked_mul_resource(
        operation,
        checked_mul_resource(operation, n, coordinates)?,
        usize_bytes,
    )?;
    let state_headers = checked_mul_resource(
        operation,
        checked_mul_resource(operation, n, variable_count)?,
        vec_header_bytes,
    )?;
    let materialized_states = checked_add_resource(operation, state_payload, state_headers)?;

    let sort_index = checked_mul_resource(operation, n, usize_bytes)?;
    let joint_table_entry = checked_add_resource(
        operation,
        checked_add_resource(operation, joint_reference_bytes, usize_bytes)?,
        usize_bytes,
    )?;
    let worst_histogram = checked_add_resource(
        operation,
        sort_index,
        checked_mul_resource(operation, n, joint_table_entry)?,
    )?;
    let specific_entry = checked_add_resource(
        operation,
        checked_add_resource(
            operation,
            slice_reference_bytes,
            std::mem::size_of::<f64>() as u128,
        )?,
        usize_bytes,
    )?;
    let specific_table = checked_mul_resource(operation, n, specific_entry)?;
    let joined_sources = checked_add_resource(
        operation,
        checked_mul_resource(
            operation,
            checked_mul_resource(operation, n, source_coordinates)?,
            usize_bytes,
        )?,
        checked_mul_resource(operation, n, vec_header_bytes)?,
    )?;

    let exact_add_work = EXACT_BINARY64_ADD_LIMB_VISIT_BOUND as u128;
    let exact_total_work = EXACT_BINARY64_TOTAL_LIMB_VISIT_BOUND as u128;
    let (histogram_passes, specific_tables, fixed_output_bytes, exact_reduction_work) =
        match source_count {
            2 => (
                20u128,
                2u128,
                0u128,
                checked_add_resource(
                    operation,
                    checked_mul_resource(operation, 4, exact_add_work)?,
                    exact_total_work,
                )?,
            ),
            3 => {
                let antichains = discrete_antichains_3();
                let total_sets = antichains
                    .iter()
                    .map(|antichain| antichain.iter().filter(|&&mask| mask != 0).count() as u128)
                    .try_fold(0u128, |sum, count| {
                        checked_add_resource(operation, sum, count)
                    })?;
                let histogram_passes = checked_add_resource(
                    operation,
                    44,
                    checked_mul_resource(operation, total_sets, 4)?,
                )?;
                let fixed_output_bytes = checked_add_resource(
                    operation,
                    checked_mul_resource(
                        operation,
                        antichains.len() as u128,
                        std::mem::size_of::<IminPid3Atom>() as u128,
                    )?,
                    checked_mul_resource(
                        operation,
                        antichains.len() as u128,
                        std::mem::size_of::<f64>() as u128,
                    )?,
                )?;
                (histogram_passes, 3, fixed_output_bytes, 0)
            }
            _ => {
                return Err(PidError::NotImplemented {
                    feature: "I_min resource estimates support exactly 2 or 3 sources",
                });
            }
        };

    // This intentionally counts every repeated histogram allocation, not merely the largest one.
    // It is a conservative upper bound on allocation exposure and includes pointer/count headers
    // that a payload-only estimate would miss.
    let repeated_histograms = checked_mul_resource(operation, histogram_passes, worst_histogram)?;
    let retained_specifics = checked_mul_resource(operation, specific_tables, specific_table)?;
    let estimated_bytes = [
        materialized_states,
        joined_sources,
        repeated_histograms,
        retained_specifics,
        fixed_output_bytes,
    ]
    .into_iter()
    .try_fold(0u128, |sum, bytes| {
        checked_add_resource(operation, sum, bytes)
    })?;

    let comparison_work = checked_mul_resource(
        operation,
        checked_mul_resource(operation, histogram_passes, n)?,
        checked_mul_resource(operation, ceil_log2(n_rows), coordinates.max(1))?,
    )?;
    let join_work = checked_mul_resource(operation, n, source_coordinates)?;
    let operations_hint = checked_add_resource(
        operation,
        checked_add_resource(operation, comparison_work, join_work)?,
        exact_reduction_work,
    )?;
    Ok(ResourceEstimate {
        estimated_bytes,
        pairwise_distances: 0,
        operations_hint,
    })
}

#[cfg(feature = "experimental-pipelines")]
fn check_same_sample_imin_aggregate_budget(
    operation: &'static str,
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
) -> PidResult<()> {
    if sources.is_empty() {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "need at least one source",
        });
    }
    let n_rows = target.nrows();
    for source in sources {
        if source.nrows() != n_rows {
            return Err(PidError::RowCountMismatch {
                context: operation,
                left_rows: n_rows,
                right_rows: source.nrows(),
            });
        }
    }
    if target.ncols() == 0 || sources.iter().any(|source| source.ncols() == 0) {
        return Err(PidError::InvalidConfig {
            context: operation,
            message: "categorical variables must have at least one coordinate",
        });
    }
    let source_coordinates = sources.iter().try_fold(0u128, |sum, source| {
        checked_add_resource(operation, sum, source.ncols() as u128)
    })?;
    let estimate = imin_resource_estimate_from_dimensions(
        operation,
        n_rows,
        sources.len(),
        source_coordinates,
        target.ncols(),
    )?;
    ResourceBudget::default().check(operation, estimate)
}

fn validate_discrete_inputs(
    operation: &'static str,
    sources: &[DiscreteMatRef<'_>],
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<()> {
    let estimate = imin_resource_estimate_impl(operation, sources, target)?;
    budget.check(operation, estimate)
}

fn states_from_discrete(
    operation: &'static str,
    matrix: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<usize>>> {
    let cancellation = CancellationToken::new();
    states_from_discrete_with_cancellation(operation, matrix, budget, &cancellation)
}

fn states_from_discrete_with_cancellation(
    operation: &'static str,
    matrix: DiscreteMatRef<'_>,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    let total_units = matrix
        .nrows()
        .checked_mul(matrix.ncols())
        .ok_or(PidError::SizeOverflow { operation })?;
    cancellation.check(operation, 0, total_units)?;
    let mut completed_units = 0usize;
    let mut states = try_vec_with_capacity(operation, matrix.nrows(), budget)?;
    for row in 0..matrix.nrows() {
        let mut state = try_vec_with_capacity(operation, matrix.ncols(), budget)?;
        for chunk in matrix.row(row).chunks(CANCELLATION_CHECK_INTERVAL) {
            cancellation.check(operation, completed_units, total_units)?;
            state.extend_from_slice(chunk);
            completed_units = completed_units
                .checked_add(chunk.len())
                .ok_or(PidError::SizeOverflow { operation })?;
        }
        states.push(state);
    }
    cancellation.check(operation, total_units, total_units)?;
    Ok(states)
}

fn imin_input_metadata(
    variables: &[&[Vec<usize>]],
    encoding: IminInputEncoding,
    budget: ResourceBudget,
) -> PidResult<(IminInputMetadata, IminEmpiricalPmfDiagnostics)> {
    let cancellation = CancellationToken::new();
    imin_input_metadata_with_cancellation(variables, encoding, budget, &cancellation)
}

fn imin_input_metadata_with_cancellation(
    variables: &[&[Vec<usize>]],
    encoding: IminInputEncoding,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<(IminInputMetadata, IminEmpiricalPmfDiagnostics)> {
    const OPERATION: &str = "I_min empirical PMF diagnostics";
    let n = variables.first().map_or(0, |rows| rows.len());
    validate_exact_sample_count(OPERATION, n)?;
    let mut observed_cardinalities = try_vec_with_capacity(OPERATION, variables.len(), budget)?;
    cancellation.check(OPERATION, 0, n)?;
    for rows in variables {
        observed_cardinalities
            .push(count_dist_with_cancellation(rows, budget, cancellation)?.len());
    }

    let joint_counts = count_joint_rows_with_cancellation(variables, budget, cancellation)?;
    let mut singleton_joint_states = 0usize;
    let mut low_count_joint_states = 0usize;
    let mut minimum_observed_count = usize::MAX;
    let mut maximum_observed_count = 0usize;
    for (index, &count) in joint_counts.iter().enumerate() {
        check_cancellation(cancellation, OPERATION, index, joint_counts.len())?;
        singleton_joint_states += usize::from(count == 1);
        low_count_joint_states += usize::from(count <= 5);
        minimum_observed_count = minimum_observed_count.min(count);
        maximum_observed_count = maximum_observed_count.max(count);
    }
    cancellation.check(OPERATION, joint_counts.len(), joint_counts.len())?;
    let empirical_pmf = IminEmpiricalPmfDiagnostics {
        sample_count: n,
        observed_joint_states: joint_counts.len(),
        singleton_joint_states,
        low_count_joint_states,
        minimum_observed_count: if joint_counts.is_empty() {
            0
        } else {
            minimum_observed_count
        },
        maximum_observed_count,
        observed_coverage_indicator: 1.0 - singleton_joint_states as f64 / n as f64,
    };
    let input = IminInputMetadata {
        encoding,
        observed_cardinalities,
        population_caveat: "Williams--Beer I_min evaluated on the empirical categorical PMF; unseen population states have zero empirical mass and plug-in bias remains",
    };
    Ok((input, empirical_pmf))
}

/// A deterministic run-length table over borrowed categorical rows.
///
/// Sorting row indices avoids both tree-node allocation and cloning input-sized keys. The table
/// owns only fallibly reserved pointer/count arrays; categorical state storage remains borrowed.
struct CountTable<'a> {
    states: Vec<&'a [usize]>,
    counts: Vec<usize>,
}

impl CountTable<'_> {
    fn len(&self) -> usize {
        self.states.len()
    }

    fn get(&self, state: &[usize]) -> Option<usize> {
        self.states
            .binary_search_by(|candidate| candidate.cmp(&state))
            .ok()
            .map(|index| self.counts[index])
    }

    fn iter(&self) -> impl Iterator<Item = (&[usize], usize)> + '_ {
        self.states.iter().copied().zip(self.counts.iter().copied())
    }
}

struct JointCountTable<'x, 'y> {
    states: Vec<(&'x [usize], &'y [usize])>,
    counts: Vec<usize>,
}

impl JointCountTable<'_, '_> {
    fn len(&self) -> usize {
        self.states.len()
    }

    fn iter(&self) -> impl Iterator<Item = ((&[usize], &[usize]), usize)> + '_ {
        self.states.iter().copied().zip(self.counts.iter().copied())
    }
}

struct SpecificInformationTable<'a> {
    targets: Vec<&'a [usize]>,
    values: Vec<f64>,
}

impl SpecificInformationTable<'_> {
    fn get(&self, target: &[usize]) -> Option<f64> {
        self.targets
            .binary_search_by(|candidate| candidate.cmp(&target))
            .ok()
            .and_then(|index| self.values.get(index).copied())
    }

    fn required(&self, target: &[usize], context: &'static str) -> PidResult<f64> {
        let value = self
            .get(target)
            .ok_or(PidError::NumericalInstability { context })?;
        if value.is_finite() {
            Ok(value)
        } else {
            Err(PidError::NumericalInstability { context })
        }
    }
}

/// Count each distinct bin vector without allocating owned histogram keys.
fn count_dist<'a>(bins: &'a [Vec<usize>], budget: ResourceBudget) -> PidResult<CountTable<'a>> {
    let cancellation = CancellationToken::new();
    count_dist_with_cancellation(bins, budget, &cancellation)
}

fn count_dist_with_cancellation<'a>(
    bins: &'a [Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<CountTable<'a>> {
    const OPERATION: &str = "count_dist";
    validate_exact_sample_count("count_dist", bins.len())?;
    let mut order = try_vec_with_capacity("count_dist row order", bins.len(), budget)?;
    cancellation.check(OPERATION, 0, bins.len())?;
    for index in 0..bins.len() {
        check_cancellation(cancellation, OPERATION, index, bins.len())?;
        order.push(index);
    }
    sort_unstable_by_with_cancellation(OPERATION, &mut order, cancellation, |&left, &right| {
        bins[left].cmp(&bins[right])
    })?;

    let mut states = try_vec_with_capacity("count_dist states", bins.len(), budget)?;
    let mut counts = try_vec_with_capacity("count_dist counts", bins.len(), budget)?;
    let mut cursor = 0;
    while cursor < order.len() {
        check_cancellation(cancellation, OPERATION, cursor, order.len())?;
        let state = bins[order[cursor]].as_slice();
        let mut next = cursor + 1;
        while next < order.len() && bins[order[next]].as_slice() == state {
            check_cancellation(cancellation, OPERATION, next, order.len())?;
            next += 1;
        }
        let count = next.checked_sub(cursor).ok_or(PidError::SizeOverflow {
            operation: "count_dist",
        })?;
        states.push(state);
        counts.push(count);
        cursor = next;
    }
    cancellation.check(OPERATION, order.len(), order.len())?;
    Ok(CountTable { states, counts })
}

/// Count joint `(X,Y)` states while preserving the former lexicographic `(X,Y)` order.
fn count_joint_dist<'x, 'y>(
    x_bins: &'x [Vec<usize>],
    y_bins: &'y [Vec<usize>],
    budget: ResourceBudget,
) -> PidResult<JointCountTable<'x, 'y>> {
    let cancellation = CancellationToken::new();
    count_joint_dist_with_cancellation(x_bins, y_bins, budget, &cancellation)
}

fn count_joint_dist_with_cancellation<'x, 'y>(
    x_bins: &'x [Vec<usize>],
    y_bins: &'y [Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<JointCountTable<'x, 'y>> {
    const OPERATION: &str = "count_joint_dist";
    if x_bins.len() != y_bins.len() {
        return Err(PidError::RowCountMismatch {
            context: "count_joint_dist",
            left_rows: x_bins.len(),
            right_rows: y_bins.len(),
        });
    }
    validate_exact_sample_count("count_joint_dist", x_bins.len())?;
    let mut order = try_vec_with_capacity("count_joint_dist row order", x_bins.len(), budget)?;
    cancellation.check(OPERATION, 0, x_bins.len())?;
    for index in 0..x_bins.len() {
        check_cancellation(cancellation, OPERATION, index, x_bins.len())?;
        order.push(index);
    }
    sort_unstable_by_with_cancellation(OPERATION, &mut order, cancellation, |&left, &right| {
        x_bins[left]
            .cmp(&x_bins[right])
            .then_with(|| y_bins[left].cmp(&y_bins[right]))
    })?;

    let mut states = try_vec_with_capacity("count_joint_dist states", x_bins.len(), budget)?;
    let mut counts = try_vec_with_capacity("count_joint_dist counts", x_bins.len(), budget)?;
    let mut cursor = 0;
    while cursor < order.len() {
        check_cancellation(cancellation, OPERATION, cursor, order.len())?;
        let x_state = x_bins[order[cursor]].as_slice();
        let y_state = y_bins[order[cursor]].as_slice();
        let mut next = cursor + 1;
        while next < order.len()
            && x_bins[order[next]].as_slice() == x_state
            && y_bins[order[next]].as_slice() == y_state
        {
            check_cancellation(cancellation, OPERATION, next, order.len())?;
            next += 1;
        }
        let count = next.checked_sub(cursor).ok_or(PidError::SizeOverflow {
            operation: "count_joint_dist",
        })?;
        states.push((x_state, y_state));
        counts.push(count);
        cursor = next;
    }
    cancellation.check(OPERATION, order.len(), order.len())?;
    Ok(JointCountTable { states, counts })
}

fn count_joint_rows_with_cancellation(
    variables: &[&[Vec<usize>]],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<usize>> {
    const OPERATION: &str = "I_min joint PMF run lengths";
    let n = variables.first().map_or(0, |rows| rows.len());
    let mut order = try_vec_with_capacity(OPERATION, n, budget)?;
    cancellation.check(OPERATION, 0, n)?;
    for index in 0..n {
        check_cancellation(cancellation, OPERATION, index, n)?;
        order.push(index);
    }
    sort_unstable_by_with_cancellation(OPERATION, &mut order, cancellation, |&left, &right| {
        variables
            .iter()
            .map(|rows| rows[left].cmp(&rows[right]))
            .find(|ordering| *ordering != Ordering::Equal)
            .unwrap_or(Ordering::Equal)
    })?;
    let mut counts = try_vec_with_capacity(OPERATION, n, budget)?;
    let mut cursor = 0;
    while cursor < order.len() {
        check_cancellation(cancellation, OPERATION, cursor, order.len())?;
        let mut next = cursor + 1;
        while next < order.len()
            && variables
                .iter()
                .all(|rows| rows[order[next]] == rows[order[cursor]])
        {
            check_cancellation(cancellation, OPERATION, next, order.len())?;
            next += 1;
        }
        counts.push(next.checked_sub(cursor).ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?);
        cursor = next;
    }
    cancellation.check(OPERATION, order.len(), order.len())?;
    Ok(counts)
}

fn discrete_mi_count_term(joint_count: usize, n: usize, x_count: usize, y_count: usize) -> f64 {
    // On supported 32-/64-bit targets, each product of two usize counts fits u128. Detect an exact
    // independent cell before converting counts to f64: beyond 2^53, separately rounded count
    // operands can otherwise turn a mathematically exact ratio of one into 1 +/- one ulp.
    let joint_product = (joint_count as u128).checked_mul(n as u128);
    let marginal_product = (x_count as u128).checked_mul(y_count as u128);
    if matches!((joint_product, marginal_product), (Some(left), Some(right)) if left == right) {
        return 0.0;
    }

    let n = n as f64;
    let joint_count = joint_count as f64;
    let probability = joint_count / n;
    let density_ratio = (joint_count * n) / ((x_count as f64) * (y_count as f64));
    probability * density_ratio.ln()
}

fn finalize_discrete_mi(mi: f64, absolute_term_sum: f64) -> PidResult<f64> {
    if !(mi.is_finite() && absolute_term_sum.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "discrete_mi",
        });
    }
    if mi >= 0.0 {
        return Ok(mi);
    }

    // Empirical MI is a KL divergence and cannot be materially negative. Permit only a conservative
    // floating-reduction envelope, normalised by the total absolute local contribution; anything
    // larger indicates broken arithmetic rather than sampling noise.
    let roundoff_tolerance = 64.0 * f64::EPSILON * (1.0 + absolute_term_sum);
    if mi >= -roundoff_tolerance {
        Ok(0.0)
    } else {
        Err(PidError::NumericalInstability {
            context: "discrete_mi: materially negative empirical mutual information",
        })
    }
}

/// Entropy from positive empirical counts, accumulated with compensation.
///
/// Writing each term as `(c/n) ln(n/c)` preserves exact zero for a one-state distribution. The
/// compensated reduction avoids the state-count-scaled drift of a plain left-to-right sum.
#[cfg(test)]
fn entropy_from_counts(counts: impl IntoIterator<Item = usize>, n: usize) -> f64 {
    let n_f = n as f64;
    compensated_sum(counts.into_iter().map(|count| {
        let count = count as f64;
        (count / n_f) * (n_f / count).ln()
    }))
}

fn neumaier_add(value: f64, sum: &mut f64, correction: &mut f64) {
    let next = *sum + value;
    if sum.abs() >= value.abs() {
        *correction += (*sum - next) + value;
    } else {
        *correction += (value - next) + *sum;
    }
    *sum = next;
}

/// Compute specific information `i(S; t)` for each target bin `t`.
///
/// `i(S; t) = Σ_s p(s|t) log(p(s,t) * n / (p(s) * p(t) * n))`
///           = Σ_s [count(s,t)/count(t)] * log[count(s,t) * n / (count(s) * count(t))]
fn specific_information<'target>(
    st_counts: &JointCountTable<'_, 'target>,
    s_counts: &CountTable<'_>,
    t_counts: &CountTable<'_>,
    n: usize,
    budget: ResourceBudget,
) -> PidResult<SpecificInformationTable<'target>> {
    let cancellation = CancellationToken::new();
    specific_information_with_cancellation(st_counts, s_counts, t_counts, n, budget, &cancellation)
}

fn specific_information_with_cancellation<'target>(
    st_counts: &JointCountTable<'_, 'target>,
    s_counts: &CountTable<'_>,
    t_counts: &CountTable<'_>,
    n: usize,
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<SpecificInformationTable<'target>> {
    const OPERATION: &str = "I_min specific information";
    // The MI path keeps `(source,target)` order to preserve its historical reduction order. A
    // second fallibly allocated index orders those borrowed entries by `(target,source)` for a
    // single streaming group-by without cloning either key.
    let mut order = try_vec_with_capacity(OPERATION, st_counts.len(), budget)?;
    cancellation.check(OPERATION, 0, st_counts.len())?;
    for index in 0..st_counts.len() {
        check_cancellation(cancellation, OPERATION, index, st_counts.len())?;
        order.push(index);
    }
    sort_unstable_by_with_cancellation(OPERATION, &mut order, cancellation, |&left, &right| {
        let (left_source, left_target) = st_counts.states[left];
        let (right_source, right_target) = st_counts.states[right];
        left_target
            .cmp(right_target)
            .then_with(|| left_source.cmp(right_source))
    })?;

    let mut targets = try_vec_with_capacity(OPERATION, t_counts.len(), budget)?;
    let mut values = try_vec_with_capacity(OPERATION, t_counts.len(), budget)?;
    let mut cursor = 0;
    while cursor < order.len() {
        check_cancellation(cancellation, OPERATION, cursor, order.len())?;
        let target = st_counts.states[order[cursor]].1;
        let target_count = t_counts.get(target).ok_or(PidError::NumericalInstability {
            context: "I_min specific information: missing target marginal count",
        })?;
        let mut sum = 0.0;
        let mut correction = 0.0;
        let mut next = cursor;
        while next < order.len() && st_counts.states[order[next]].1 == target {
            check_cancellation(cancellation, OPERATION, next, order.len())?;
            let entry = order[next];
            let (source, _) = st_counts.states[entry];
            let joint_count = st_counts.counts[entry];
            let source_count = s_counts.get(source).ok_or(PidError::NumericalInstability {
                context: "I_min specific information: missing source marginal count",
            })?;
            let log_ratio = ((joint_count as f64) * (n as f64)
                / ((source_count as f64) * (target_count as f64)))
                .ln();
            neumaier_add(
                (joint_count as f64 / target_count as f64) * log_ratio,
                &mut sum,
                &mut correction,
            );
            next += 1;
        }
        targets.push(target);
        values.push(sum + correction);
        cursor = next;
    }

    cancellation.check(OPERATION, order.len(), order.len())?;
    Ok(SpecificInformationTable { targets, values })
}

/// Result of a discrete 3-source PID decomposition (18 atoms on the redundancy lattice).
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct IminPid3Result {
    /// PID atoms in canonical antichain order (same 18 antichains as continuous pid3_isx).
    pub atoms: Vec<IminPid3Atom>,
    /// Per-antichain redundancy values.
    pub redundancies: Vec<f64>,
    /// MI terms: I(S0;T), I(S1;T), I(S2;T).
    pub mi_s0_t: f64,
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    /// Pairwise joint MIs: I(S0,S1;T), I(S0,S2;T), I(S1,S2;T).
    pub mi_s0s1_t: f64,
    pub mi_s0s2_t: f64,
    pub mi_s1s2_t: f64,
    /// Triple joint MI: I(S0,S1,S2;T).
    pub mi_s0s1s2_t: f64,
    pub input: IminInputMetadata,
    pub empirical_pmf: IminEmpiricalPmfDiagnostics,
}

/// A single PID atom for discrete 3-source decomposition.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct IminPid3Atom {
    /// Antichain identifying this atom (as a bitmask array, same encoding as pid3_isx).
    pub antichain_sets: Vec<u8>,
    pub value: f64,
}

/// Evaluate three-source Williams--Beer `I_min` on an explicit empirical categorical PMF.
pub fn imin_pid3(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<IminPid3Result> {
    imin_pid3_with_budget(s0, s1, s2, target, ResourceBudget::default())
}

/// Conservative allocation-volume and comparison-work preflight for [`imin_pid3`].
///
/// The estimate includes the 18-node lattice's repeated source-subset histograms and up to three
/// retained specific-information tables per node, plus nested-vector and result headers.
pub fn imin_pid3_resource_estimate(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
) -> PidResult<ResourceEstimate> {
    imin_resource_estimate_impl("imin_pid3", &[s0, s1, s2], target)
}

/// [`imin_pid3`] with an explicit preflight resource ceiling.
pub fn imin_pid3_with_budget(
    s0: DiscreteMatRef<'_>,
    s1: DiscreteMatRef<'_>,
    s2: DiscreteMatRef<'_>,
    target: DiscreteMatRef<'_>,
    budget: ResourceBudget,
) -> PidResult<IminPid3Result> {
    validate_discrete_inputs("imin_pid3", &[s0, s1, s2], target, budget)?;
    let s0_states = states_from_discrete("imin_pid3", s0, budget)?;
    let s1_states = states_from_discrete("imin_pid3", s1, budget)?;
    let s2_states = states_from_discrete("imin_pid3", s2, budget)?;
    let target_states = states_from_discrete("imin_pid3", target, budget)?;
    imin_pid3_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        IminInputEncoding::Categorical,
        budget,
    )
}

/// Evaluate three-source `I_min` for variables produced by fixed, separately fitted quantizers.
pub fn imin_pid3_quantized(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<IminPid3Result> {
    imin_pid3_quantized_with_budget(s0, s1, s2, target, ResourceBudget::default())
}

/// Resource preflight for [`imin_pid3_quantized`], including copied quantization provenance.
pub fn imin_pid3_quantized_resource_estimate(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
) -> PidResult<ResourceEstimate> {
    quantized_imin_resource_estimate(
        "imin_pid3_quantized",
        &[s0.matrix.as_ref(), s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        &[&s0.report, &s1.report, &s2.report, &target.report],
    )
}

/// [`imin_pid3_quantized`] with an explicit preflight resource ceiling.
pub fn imin_pid3_quantized_with_budget(
    s0: &QuantizedData,
    s1: &QuantizedData,
    s2: &QuantizedData,
    target: &QuantizedData,
    budget: ResourceBudget,
) -> PidResult<IminPid3Result> {
    validate_discrete_inputs(
        "imin_pid3_quantized",
        &[s0.matrix.as_ref(), s1.matrix.as_ref(), s2.matrix.as_ref()],
        target.matrix.as_ref(),
        budget,
    )?;
    budget.check(
        "imin_pid3_quantized",
        imin_pid3_quantized_resource_estimate(s0, s1, s2, target)?,
    )?;
    let reports = [&s0.report, &s1.report, &s2.report, &target.report];
    let s0_states = states_from_discrete("imin_pid3_quantized", s0.matrix.as_ref(), budget)?;
    let s1_states = states_from_discrete("imin_pid3_quantized", s1.matrix.as_ref(), budget)?;
    let s2_states = states_from_discrete("imin_pid3_quantized", s2.matrix.as_ref(), budget)?;
    let target_states =
        states_from_discrete("imin_pid3_quantized", target.matrix.as_ref(), budget)?;
    let mut quantization_reports = try_vec_with_capacity("imin_pid3_quantized reports", 4, budget)?;
    for report in reports {
        quantization_reports.push(try_clone_quantization_report(
            "imin_pid3_quantized reports",
            report,
            budget,
        )?);
    }
    imin_pid3_states(
        &s0_states,
        &s1_states,
        &s2_states,
        &target_states,
        IminInputEncoding::FittedEqualWidth {
            quantization_reports,
        },
        budget,
    )
}

/// Compute discrete 3-source PID atoms via quantization + a Williams–Beer-style
/// `I_min` redundancy over the full 18-antichain lattice (not discrete `i^sx_∩`;
/// see the module docs).
///
/// Sources S0, S1, S2 and target T are each quantized into `num_bins` equal-width bins.
/// All 18 antichains on the redundancy lattice are evaluated, and Möbius inversion
/// yields the PID atoms.
///
/// Units: nats (natural logarithm).
#[cfg(feature = "experimental-pipelines")]
pub fn same_sample_quantized_imin_pid3(
    s0: MatRef<'_>,
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    target: MatRef<'_>,
    num_bins: usize,
) -> PidResult<crate::same_sample::ExploratorySameSampleQuantizedResult<IminPid3Result>> {
    if num_bins < 2 {
        return Err(PidError::InvalidConfig {
            context: "same_sample_quantized_imin_pid3",
            message: "num_bins must be >= 2",
        });
    }
    let n = s0.nrows();
    if s1.nrows() != n || s2.nrows() != n || target.nrows() != n {
        // Report the first operand that actually mismatches, not min() (which can equal n
        // and hide the real culprit).
        let right_rows = if s1.nrows() != n {
            s1.nrows()
        } else if s2.nrows() != n {
            s2.nrows()
        } else {
            target.nrows()
        };
        return Err(PidError::RowCountMismatch {
            context: "same_sample_quantized_imin_pid3",
            left_rows: n,
            right_rows,
        });
    }
    if n == 0 {
        // An empty joint pmf would silently yield an all-zero decomposition; fail loudly.
        return Err(PidError::InvalidConfig {
            context: "same_sample_quantized_imin_pid3",
            message: "need at least 1 sample (got 0 rows)",
        });
    }

    check_same_sample_imin_aggregate_budget(
        "same_sample_quantized_imin_pid3",
        &[s0, s1, s2],
        target,
    )?;

    // Quantize all variables.
    let s0_bins = quantize_equal_width(s0, num_bins)?;
    let s1_bins = quantize_equal_width(s1, num_bins)?;
    let s2_bins = quantize_equal_width(s2, num_bins)?;
    let t_bins = quantize_equal_width(target, num_bins)?;
    let categorical_result = imin_pid3_states(
        &s0_bins,
        &s1_bins,
        &s2_bins,
        &t_bins,
        IminInputEncoding::Categorical,
        ResourceBudget::default(),
    )?;
    Ok(crate::same_sample::ExploratorySameSampleQuantizedResult::new(categorical_result, num_bins))
}

fn imin_pid3_states(
    s0_bins: &[Vec<usize>],
    s1_bins: &[Vec<usize>],
    s2_bins: &[Vec<usize>],
    t_bins: &[Vec<usize>],
    encoding: IminInputEncoding,
    budget: ResourceBudget,
) -> PidResult<IminPid3Result> {
    let sources: [&[Vec<usize>]; 3] = [s0_bins, s1_bins, s2_bins];

    // Compute MI terms.
    let mi_s0_t = discrete_mi_with_budget(s0_bins, t_bins, 0, budget)?;
    let mi_s1_t = discrete_mi_with_budget(s1_bins, t_bins, 0, budget)?;
    let mi_s2_t = discrete_mi_with_budget(s2_bins, t_bins, 0, budget)?;
    let mi_s0s1_t = discrete_mi_with_budget(
        &join_bins_pair(s0_bins, s1_bins, budget)?,
        t_bins,
        0,
        budget,
    )?;
    let mi_s0s2_t = discrete_mi_with_budget(
        &join_bins_pair(s0_bins, s2_bins, budget)?,
        t_bins,
        0,
        budget,
    )?;
    let mi_s1s2_t = discrete_mi_with_budget(
        &join_bins_pair(s1_bins, s2_bins, budget)?,
        t_bins,
        0,
        budget,
    )?;
    let mi_s0s1s2_t = discrete_mi_with_budget(
        &join_bins_triple(s0_bins, s1_bins, s2_bins, budget)?,
        t_bins,
        0,
        budget,
    )?;

    // Compute 18 antichain redundancies.
    let antichains = discrete_antichains_3();
    let mut redundancies = try_vec_with_capacity("imin_pid3", 18, budget)?;
    for &ac in &antichains {
        let val = discrete_imin_redundancy_3way(&sources, t_bins, ac, budget)?;
        redundancies.push(val);
    }

    // Möbius inversion to get atoms.
    let atoms = discrete_mobius_inversion_3(&antichains, &redundancies);

    let (input, empirical_pmf) =
        imin_input_metadata(&[s0_bins, s1_bins, s2_bins, t_bins], encoding, budget)?;
    Ok(IminPid3Result {
        atoms,
        redundancies,
        mi_s0_t,
        mi_s1_t,
        mi_s2_t,
        mi_s0s1_t,
        mi_s0s2_t,
        mi_s1s2_t,
        mi_s0s1s2_t,
        input,
        empirical_pmf,
    })
}

/// Build joint bins for a pair of sources (for subset mask with 2 bits set).
fn join_bins_pair(
    a: &[Vec<usize>],
    b: &[Vec<usize>],
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<usize>>> {
    let cancellation = CancellationToken::new();
    join_bins_pair_with_cancellation(a, b, budget, &cancellation)
}

fn join_bins_pair_with_cancellation(
    a: &[Vec<usize>],
    b: &[Vec<usize>],
    budget: ResourceBudget,
    cancellation: &CancellationToken,
) -> PidResult<Vec<Vec<usize>>> {
    const OPERATION: &str = "I_min join pair";
    cancellation.check(OPERATION, 0, a.len())?;
    let mut joined = try_vec_with_capacity("I_min join pair", a.len(), budget)?;
    for (row_index, (ar, br)) in a.iter().zip(b).enumerate() {
        check_cancellation(cancellation, OPERATION, row_index, a.len())?;
        let width = ar
            .len()
            .checked_add(br.len())
            .ok_or(PidError::SizeOverflow {
                operation: "I_min join pair",
            })?;
        let mut row = try_vec_with_capacity("I_min join pair", width, budget)?;
        for chunk in ar
            .chunks(CANCELLATION_CHECK_INTERVAL)
            .chain(br.chunks(CANCELLATION_CHECK_INTERVAL))
        {
            cancellation.check(OPERATION, row_index, a.len())?;
            row.extend_from_slice(chunk);
        }
        joined.push(row);
    }
    cancellation.check(OPERATION, a.len(), a.len())?;
    Ok(joined)
}

/// Build joint bins for three sources.
fn join_bins_triple(
    a: &[Vec<usize>],
    b: &[Vec<usize>],
    c: &[Vec<usize>],
    budget: ResourceBudget,
) -> PidResult<Vec<Vec<usize>>> {
    let mut joined = try_vec_with_capacity("I_min join triple", a.len(), budget)?;
    for ((ar, br), cr) in a.iter().zip(b).zip(c) {
        let width = ar
            .len()
            .checked_add(br.len())
            .and_then(|width| width.checked_add(cr.len()))
            .ok_or(PidError::SizeOverflow {
                operation: "I_min join triple",
            })?;
        let mut row = try_vec_with_capacity("I_min join triple", width, budget)?;
        row.extend_from_slice(ar);
        row.extend_from_slice(br);
        row.extend_from_slice(cr);
        joined.push(row);
    }
    Ok(joined)
}

/// 18 canonical antichains on {0,1,2}, encoded as bitmask arrays.
pub(crate) fn discrete_antichains_3() -> [[u8; 3]; 18] {
    [
        [0b001, 0, 0],
        [0b010, 0, 0],
        [0b100, 0, 0],
        [0b011, 0, 0],
        [0b101, 0, 0],
        [0b110, 0, 0],
        [0b111, 0, 0],
        [0b001, 0b010, 0],
        [0b001, 0b100, 0],
        [0b001, 0b110, 0],
        [0b010, 0b100, 0],
        [0b010, 0b101, 0],
        [0b011, 0b100, 0],
        [0b011, 0b101, 0],
        [0b011, 0b110, 0],
        [0b101, 0b110, 0],
        [0b001, 0b010, 0b100],
        [0b011, 0b101, 0b110],
    ]
}

/// Compute specific information i(S;t) for an arbitrary source subset mask.
///
/// The source subset is the joint distribution of the sources indicated by `mask`.
fn i_spec_for_mask<'target>(
    sources: &[&[Vec<usize>]; 3],
    t_bins: &'target [Vec<usize>],
    mask: u8,
    n: usize,
    budget: ResourceBudget,
) -> PidResult<SpecificInformationTable<'target>> {
    const OPERATION: &str = "I_min source-subset materialization";
    let width = sources
        .iter()
        .enumerate()
        .filter(|(source, _)| mask & (1 << source) != 0)
        .map(|(_, rows)| rows.first().map_or(0, Vec::len))
        .try_fold(0usize, usize::checked_add)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let mut joint = try_vec_with_capacity(OPERATION, n, budget)?;
    for row_index in 0..n {
        let mut row = try_vec_with_capacity(OPERATION, width, budget)?;
        for (source, rows) in sources.iter().enumerate() {
            if mask & (1 << source) != 0 {
                row.extend_from_slice(&rows[row_index]);
            }
        }
        joint.push(row);
    }
    let s_counts = count_dist(&joint, budget)?;
    let st_counts = count_joint_dist(&joint, t_bins, budget)?;
    let t_counts = count_dist(t_bins, budget)?;
    specific_information(&st_counts, &s_counts, &t_counts, n, budget)
}

/// 3-source discrete Williams–Beer-style `I_min` redundancy for a single antichain.
fn discrete_imin_redundancy_3way(
    sources: &[&[Vec<usize>]; 3],
    t_bins: &[Vec<usize>],
    antichain: [u8; 3],
    budget: ResourceBudget,
) -> PidResult<f64> {
    let n = t_bins.len();
    if n == 0 {
        return Ok(0.0);
    }
    let inv_n = 1.0 / n as f64;

    // Determine how many sets are in this antichain.
    let n_sets = if antichain[2] != 0 {
        3
    } else if antichain[1] != 0 {
        2
    } else {
        1
    };

    // Compute i_spec for each set in the antichain.
    let mut i_specs = try_vec_with_capacity("I_min 3-way specific information", n_sets, budget)?;
    for &mask in antichain.iter().take(n_sets) {
        i_specs.push(i_spec_for_mask(sources, t_bins, mask, n, budget)?);
    }

    // Red = Σ_t p(t) min_s i_spec(S_s; t)
    let t_counts = count_dist(t_bins, budget)?;
    let mut sum = 0.0;
    let mut correction = 0.0;
    for (t_key, ct) in t_counts.iter() {
        let p_t = ct as f64 * inv_n;
        let mut min_is = f64::INFINITY;
        for is in &i_specs {
            min_is = min_is.min(is.required(
                t_key,
                "I_min PID3 redundancy: missing or non-finite specific information",
            )?);
        }
        if !min_is.is_finite() {
            return Err(PidError::NumericalInstability {
                context: "I_min PID3 redundancy: no finite specific-information minimum",
            });
        }
        neumaier_add(p_t * min_is, &mut sum, &mut correction);
    }
    Ok(sum + correction)
}

/// Möbius inversion on the 3-source redundancy lattice to obtain PID atoms.
///
/// Measure-agnostic: it inverts any per-antichain *cumulative* functional that obeys
/// `cumulative(α) = Σ_{β ⪯ α} atom(β)`. Reused by both the `I_min` path here and the
/// shared-exclusions `i^sx_∩` path in the `sxpid` module.
pub(crate) fn discrete_mobius_inversion_3(
    antichains: &[[u8; 3]],
    redundancies: &[f64],
) -> Vec<IminPid3Atom> {
    let n = antichains.len();
    let mut atoms = vec![0.0f64; n];

    // Topological order: start from minimal antichains (fewest sets, smallest masks).
    let topo = discrete_topo_order_3(antichains);

    for (pos, &idx) in topo.iter().enumerate() {
        // Negate each lower atom before the compensated reduction, so subtracting a negative
        // contribution adds it without losing its sign through an intermediate partial sum.
        let lower_terms = topo[..pos]
            .iter()
            .filter_map(|&j| discrete_leq_3(antichains[j], antichains[idx]).then_some(-atoms[j]));
        atoms[idx] = compensated_sum(std::iter::once(redundancies[idx]).chain(lower_terms));
    }

    antichains
        .iter()
        .enumerate()
        .map(|(idx, ac)| {
            let sets: Vec<u8> = ac.iter().copied().filter(|&m| m != 0).collect();
            IminPid3Atom {
                antichain_sets: sets,
                value: atoms[idx],
            }
        })
        .collect()
}

/// Check if antichain a ⪯ b in the redundancy lattice ordering.
fn discrete_leq_3(a: [u8; 3], b: [u8; 3]) -> bool {
    let n_b = if b[2] != 0 {
        3
    } else if b[1] != 0 {
        2
    } else {
        1
    };
    let n_a = if a[2] != 0 {
        3
    } else if a[1] != 0 {
        2
    } else {
        1
    };
    for &b_j in b.iter().take(n_b) {
        let mut found = false;
        for &a_i in a.iter().take(n_a) {
            if (a_i & b_j) == a_i {
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

/// Topological sort for the 18-antichain lattice.
fn discrete_topo_order_3(antichains: &[[u8; 3]]) -> Vec<usize> {
    let n = antichains.len();
    let mut remaining: Vec<usize> = (0..n).collect();
    let mut out = Vec::with_capacity(n);
    while !remaining.is_empty() {
        let mut mins = Vec::new();
        'outer: for &i in &remaining {
            for &j in &remaining {
                if i == j {
                    continue;
                }
                if discrete_leq_3(antichains[j], antichains[i]) {
                    continue 'outer;
                }
            }
            mins.push(i);
        }
        mins.sort();
        let chosen = mins[0];
        out.push(chosen);
        remaining.retain(|&x| x != chosen);
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn specific_information_table_fails_closed_when_target_is_missing() {
        let target = [0usize];
        let table = SpecificInformationTable {
            targets: Vec::new(),
            values: Vec::new(),
        };

        let result = table.required(&target, "specific information test");

        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "specific information test"
            })
        ));
    }

    #[test]
    fn specific_information_table_fails_closed_when_value_is_missing() {
        let target = [0usize];
        let table = SpecificInformationTable {
            targets: vec![target.as_slice()],
            values: Vec::new(),
        };

        let result = table.required(&target, "specific information test");

        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "specific information test"
            })
        ));
    }

    #[test]
    fn specific_information_table_fails_closed_when_value_is_non_finite() {
        let target = [0usize];
        let table = SpecificInformationTable {
            targets: vec![target.as_slice()],
            values: vec![f64::NAN],
        };

        let result = table.required(&target, "specific information test");

        assert!(matches!(
            result,
            Err(PidError::NumericalInstability {
                context: "specific information test"
            })
        ));
    }

    #[test]
    fn specific_information_table_returns_a_present_finite_value_bit_exactly() {
        let target = [0usize];
        let value = f64::from_bits(0x3fd5_5555_5555_5555);
        let table = SpecificInformationTable {
            targets: vec![target.as_slice()],
            values: vec![value],
        };

        let result = table
            .required(&target, "specific information test")
            .unwrap();

        assert_eq!(result.to_bits(), value.to_bits());
    }

    #[test]
    fn imin_pid2_with_cancellation_honors_a_pre_cancelled_token() {
        let s1 = [0, 0, 1, 1];
        let s2 = [0, 1, 0, 1];
        let target = [0, 1, 1, 0];
        let cancellation = CancellationToken::new();
        cancellation.cancel();

        let result = imin_pid2_with_budget_and_cancellation(
            DiscreteMatRef::new(&s1, 4, 1).unwrap(),
            DiscreteMatRef::new(&s2, 4, 1).unwrap(),
            DiscreteMatRef::new(&target, 4, 1).unwrap(),
            ResourceBudget::default(),
            &cancellation,
        );

        assert!(matches!(
            result,
            Err(PidError::Cancelled {
                operation: "imin_pid2",
                completed_units: 0,
                ..
            })
        ));
    }

    #[test]
    fn uncancelled_imin_pid2_matches_compatibility_entry_point_bit_exactly() {
        let s1 = [0, 0, 1, 1];
        let s2 = [0, 1, 0, 1];
        let target = [0, 1, 1, 0];
        let s1 = DiscreteMatRef::new(&s1, 4, 1).unwrap();
        let s2 = DiscreteMatRef::new(&s2, 4, 1).unwrap();
        let target = DiscreteMatRef::new(&target, 4, 1).unwrap();
        let expected = imin_pid2_with_budget(s1, s2, target, ResourceBudget::default()).unwrap();
        let cancellation = CancellationToken::new();
        let actual = imin_pid2_with_budget_and_cancellation(
            s1,
            s2,
            target,
            ResourceBudget::default(),
            &cancellation,
        )
        .unwrap();

        assert_eq!(
            [
                actual.redundancy.to_bits(),
                actual.unique_s1.to_bits(),
                actual.unique_s2.to_bits(),
                actual.synergy.to_bits(),
                actual.mi_s1_t.to_bits(),
                actual.mi_s2_t.to_bits(),
                actual.mi_s1s2_t.to_bits(),
            ],
            [
                expected.redundancy.to_bits(),
                expected.unique_s1.to_bits(),
                expected.unique_s2.to_bits(),
                expected.synergy.to_bits(),
                expected.mi_s1_t.to_bits(),
                expected.mi_s2_t.to_bits(),
                expected.mi_s1s2_t.to_bits(),
            ]
        );
    }
    #[cfg(feature = "experimental-pipelines")]
    use crate::matrix::MatRef;

    #[test]
    fn discrete_mobius_inversion_compensates_mixed_sign_lower_atoms() {
        let antichains = [[0b001, 0, 0], [0b010, 0, 0], [0b100, 0, 0], [0b111, 0, 0]];
        let cumulative = [1.0e16, 1.0, -1.0e16, 0.0];

        let atoms = discrete_mobius_inversion_3(&antichains, &cumulative);
        let top = atoms
            .iter()
            .find(|atom| atom.antichain_sets == [0b111])
            .unwrap();

        assert_eq!(top.value, -1.0);
    }
    #[test]
    fn discrete_entropy_uniform() {
        // 4 equally likely bins → H = ln(4) ≈ 1.386
        let bins: Vec<Vec<usize>> = (0..400).map(|i| vec![i % 4]).collect();
        let h = discrete_entropy(&bins, 4).unwrap();
        assert!(
            (h - 4.0f64.ln()).abs() < 0.05,
            "H(uniform 4 bins) should be ≈ ln(4); got {h}"
        );
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn quantize_preserves_resolvable_variation_at_large_offsets() {
        let data = [1.0e12, 1.0e12 + 0.5, 1.0e12 + 1.0];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let bins = quantize_equal_width(x, 3).unwrap();

        assert_eq!(bins, vec![vec![0], vec![1], vec![2]]);
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn quantize_handles_finite_range_whose_subtraction_overflows() {
        let data = [-f64::MAX, 0.0, f64::MAX];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let bins = quantize_equal_width(x, 3).unwrap();

        assert_eq!(bins, vec![vec![0], vec![1], vec![2]]);
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn quantize_distinguishes_adjacent_subnormal_values() {
        let min_subnormal = f64::from_bits(1);
        let data = [0.0, min_subnormal, 2.0 * min_subnormal];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let bins = quantize_equal_width(x, 3).unwrap();

        assert_eq!(bins, vec![vec![0], vec![1], vec![2]]);
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn same_sample_quantization_relabels_existing_value_when_outlier_is_appended() {
        let before_data = [0.0, 1.0];
        let after_data = [0.0, 1.0, 100.0];
        let before = MatRef::new(&before_data, 2, 1).unwrap();
        let after = MatRef::new(&after_data, 3, 1).unwrap();

        let before_bins = quantize_equal_width(before, 2).unwrap();
        let after_bins = quantize_equal_width(after, 2).unwrap();

        assert_eq!((before_bins[1][0], after_bins[1][0]), (1, 0));
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn same_sample_quantization_has_exact_binary64_boundary_semantics() {
        let boundary = 0.3_f64;
        let successor = f64::from_bits(boundary.to_bits() + 1);
        let data = [0.0, boundary, successor, 1.0];
        let x = MatRef::new(&data, 4, 1).unwrap();

        let bins = quantize_equal_width(x, 10).unwrap();

        // Binary64 0.3 is slightly below the real number 3/10, while its immediate successor is
        // above it. Exact significand scaling therefore separates the two values. A separately
        // materialized binary64 edge at `3 / 10` would instead group them in bin 3.
        assert_eq!(bins, vec![vec![0], vec![2], vec![3], vec![9]]);
    }

    #[cfg(all(feature = "experimental-pipelines", target_pointer_width = "64"))]
    #[test]
    fn quantize_scales_bin_counts_above_f64_integer_precision_exactly() {
        // 2^53 + 3 rounds upward when converted to f64. The old `frac * num_bins as f64`
        // therefore put an exact midpoint one bin too high.
        let num_bins = (1_usize << 53) + 3;
        let data = [0.0, 0.5, 1.0];
        let x = MatRef::new(&data, 3, 1).unwrap();

        let bins = quantize_equal_width(x, num_bins).unwrap();

        assert_eq!(bins, vec![vec![0], vec![num_bins / 2], vec![num_bins - 1]]);
    }

    #[test]
    fn discrete_mi_independent() {
        // Independent X and Y → I(X;Y) ≈ 0
        let n = 1000;
        let mut rng = crate::preprocess::SplitMix64::new(42);
        let mut x_bins = Vec::with_capacity(n);
        let mut y_bins = Vec::with_capacity(n);
        for _ in 0..n {
            x_bins.push(vec![(rng.next_u64() as usize) % 4]);
            y_bins.push(vec![(rng.next_u64() as usize) % 4]);
        }
        let mi = discrete_mi(&x_bins, &y_bins, 4).unwrap();
        assert!(
            mi.abs() < 0.05,
            "MI of independent vars should be ≈ 0; got {mi}"
        );
    }

    #[test]
    fn discrete_mi_rejects_ragged_inputs_that_would_alias_joint_states() {
        let x = vec![vec![0], vec![0, 1]];
        let y = vec![vec![1, 2], vec![2]];

        assert!(discrete_mi(&x, &y, 0).is_err());
    }

    #[test]
    fn discrete_mi_rejects_empty_empirical_distribution() {
        assert!(discrete_mi(&[], &[], 0).is_err());
    }

    #[test]
    fn discrete_mi_is_zero_for_an_exact_large_independent_cartesian_distribution() {
        // Entropy subtraction accumulated about -1e-11 nats on this exact product pmf because
        // H(X,Y) has 194^2 singleton terms. Direct count-ratio MI makes every term log(1) = 0.
        let cardinality = 194usize;
        let mut x = Vec::with_capacity(cardinality * cardinality);
        let mut y = Vec::with_capacity(cardinality * cardinality);
        for x_state in 0..cardinality {
            for y_state in 0..cardinality {
                x.push(vec![x_state]);
                y.push(vec![y_state]);
            }
        }

        assert_eq!(discrete_mi(&x, &y, cardinality).unwrap(), 0.0);
    }

    #[cfg(target_pointer_width = "64")]
    #[test]
    fn discrete_mi_exact_independence_uses_integer_products_beyond_f64_integer_precision() {
        let n = 2_274_211_330_813_025_226usize;
        let x_count = 2_814_900_170_454usize;
        let y_count = 1_284_225_222_693usize;
        let joint_count = 1_589_547usize;
        let rounded_ratio =
            ((joint_count as f64) * (n as f64)) / ((x_count as f64) * (y_count as f64));
        assert_ne!(rounded_ratio, 1.0);
        assert_eq!(
            discrete_mi_count_term(joint_count, n, x_count, y_count),
            0.0
        );
    }

    #[test]
    fn discrete_mi_only_clamps_roundoff_scale_negativity() {
        assert_eq!(finalize_discrete_mi(-f64::EPSILON, 1.0).unwrap(), 0.0);
        assert!(finalize_discrete_mi(-1e-6, 1.0).is_err());
    }

    #[test]
    fn discrete_mi_copy() {
        // Y = X → I(X;Y) = H(X)
        let n = 500;
        let bins: Vec<Vec<usize>> = (0..n).map(|i| vec![i % 8]).collect();
        let mi = discrete_mi(&bins, &bins, 8).unwrap();
        let h = discrete_entropy(&bins, 8).unwrap();
        assert!(
            (mi - h).abs() < 0.01,
            "MI(X;X) should equal H(X); MI={mi}, H={h}"
        );
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid2_redundant_copy() {
        // S1 = S2 = signal → Red ≈ MI, Unq ≈ 0, Syn ≈ 0
        let n = 500;
        let d = 1;
        let mut rng = crate::preprocess::SplitMix64::new(99);
        let mut s1_data = Vec::with_capacity(n * d);
        let mut s2_data = Vec::with_capacity(n * d);
        let mut t_data = Vec::with_capacity(n * d);
        for _ in 0..n {
            let sig = rng.normal();
            s1_data.push(sig);
            s2_data.push(sig + 0.01 * rng.normal()); // Near-copy
            t_data.push(sig + 0.1 * rng.normal());
        }
        let s1 = MatRef::new(&s1_data, n, d).unwrap();
        let s2 = MatRef::new(&s2_data, n, d).unwrap();
        let t = MatRef::new(&t_data, n, d).unwrap();

        let result = same_sample_quantized_imin_pid2(s1, s2, t, 10)
            .unwrap()
            .into_categorical_result();

        // Redundancy should dominate; unique should be small.
        assert!(
            result.redundancy > 0.5 * result.mi_s1_t,
            "Redundancy should be > 50% of MI for near-copies; Red={}, MI={}",
            result.redundancy,
            result.mi_s1_t
        );
        assert!(
            result.unique_s1.abs() < 0.3 * result.mi_s1_t,
            "Unique S1 should be small for near-copies; Unq1={}",
            result.unique_s1
        );
    }

    /// Build an exactly-enumerated 2-input binary gate dataset: every (s1,s2) ∈ {0,1}²
    /// combination repeated `reps` times, with `t = gate(s1,s2)`. Because each of the four
    /// joint states appears equally often, the empirical distribution is *exact* (no sampling
    /// error), so the binned `I_min` PID equals its analytic closed form to machine precision.
    #[cfg(feature = "experimental-pipelines")]
    fn binary_gate_dataset(
        reps: usize,
        gate: impl Fn(u8, u8) -> u8,
    ) -> (Vec<f64>, Vec<f64>, Vec<f64>, usize) {
        let mut s1 = Vec::new();
        let mut s2 = Vec::new();
        let mut t = Vec::new();
        for _ in 0..reps {
            for a in 0u8..2 {
                for b in 0u8..2 {
                    s1.push(a as f64);
                    s2.push(b as f64);
                    t.push(gate(a, b) as f64);
                }
            }
        }
        let n = 4 * reps;
        (s1, s2, t, n)
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid2_xor_is_pure_synergy() {
        // Williams & Beer (2010), canonical XOR gate, uniform independent inputs:
        //   I(S1;T) = I(S2;T) = 0,  I(S1,S2;T) = ln 2  (1 bit)
        //   Red = 0, Unq1 = Unq2 = 0, Syn = ln 2.
        let (s1, s2, t, n) = binary_gate_dataset(64, |a, b| a ^ b);
        let s1 = MatRef::new(&s1, n, 1).unwrap();
        let s2 = MatRef::new(&s2, n, 1).unwrap();
        let t = MatRef::new(&t, n, 1).unwrap();

        let r = same_sample_quantized_imin_pid2(s1, s2, t, 2)
            .unwrap()
            .into_categorical_result();
        let ln2 = 2.0f64.ln();
        let tol = 1e-9;
        assert!(
            r.mi_s1_t.abs() < tol,
            "I(S1;T) should be 0; got {}",
            r.mi_s1_t
        );
        assert!(
            r.mi_s2_t.abs() < tol,
            "I(S2;T) should be 0; got {}",
            r.mi_s2_t
        );
        assert!(
            (r.mi_s1s2_t - ln2).abs() < tol,
            "I(S1,S2;T) should be ln 2; got {}",
            r.mi_s1s2_t
        );
        assert!(
            r.redundancy.abs() < tol,
            "Red should be 0; got {}",
            r.redundancy
        );
        assert!(
            r.unique_s1.abs() < tol,
            "Unq1 should be 0; got {}",
            r.unique_s1
        );
        assert!(
            r.unique_s2.abs() < tol,
            "Unq2 should be 0; got {}",
            r.unique_s2
        );
        assert!(
            (r.synergy - ln2).abs() < tol,
            "Syn should be ln 2; got {}",
            r.synergy
        );
        // Identity must hold exactly.
        assert!((r.redundancy + r.unique_s1 + r.unique_s2 + r.synergy - r.mi_s1s2_t).abs() < tol);
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid2_and_matches_williams_beer() {
        // Williams & Beer (2010), canonical AND gate, uniform independent inputs.
        // p(T=1) = 1/4. Analytic atoms (nats):
        //   H(T) = 0.25·ln4 + 0.75·ln(4/3) = 0.5623351446...
        //   I(S1;T) = I(S2;T) = H(T) − 0.5·ln2 = 0.75·ln(4/3) = 0.2157615543...
        //   Red = I(S1;T) (symmetric sources), Unq1 = Unq2 = 0,
        //   Syn = I(S1,S2;T) − I(S1;T) = H(T) − I(S1;T) = ln2/2 = 0.3465735903... (= 0.5 bits)
        let (s1, s2, t, n) = binary_gate_dataset(64, |a, b| a & b);
        let s1 = MatRef::new(&s1, n, 1).unwrap();
        let s2 = MatRef::new(&s2, n, 1).unwrap();
        let t = MatRef::new(&t, n, 1).unwrap();

        let r = same_sample_quantized_imin_pid2(s1, s2, t, 2)
            .unwrap()
            .into_categorical_result();

        let h_t = 0.25 * 4.0f64.ln() + 0.75 * (4.0f64 / 3.0).ln();
        let i_single = h_t - 0.5 * 2.0f64.ln();
        let syn = h_t - i_single;
        let tol = 1e-9;

        assert!(
            (r.mi_s1_t - i_single).abs() < tol,
            "I(S1;T)={} want {i_single}",
            r.mi_s1_t
        );
        assert!(
            (r.mi_s2_t - i_single).abs() < tol,
            "I(S2;T)={} want {i_single}",
            r.mi_s2_t
        );
        assert!(
            (r.mi_s1s2_t - h_t).abs() < tol,
            "I(S1,S2;T)={} want {h_t}",
            r.mi_s1s2_t
        );
        assert!(
            (r.redundancy - i_single).abs() < tol,
            "Red={} want {i_single}",
            r.redundancy
        );
        assert!(
            r.unique_s1.abs() < tol,
            "Unq1 should be 0; got {}",
            r.unique_s1
        );
        assert!(
            r.unique_s2.abs() < tol,
            "Unq2 should be 0; got {}",
            r.unique_s2
        );
        assert!(
            (r.synergy - syn).abs() < tol,
            "Syn={} want {syn}",
            r.synergy
        );
        assert!((r.redundancy + r.unique_s1 + r.unique_s2 + r.synergy - r.mi_s1s2_t).abs() < tol);
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn quantize_rejects_bad_bins() {
        let data = vec![0.0f64; 10];
        let m = MatRef::new(&data, 5, 2).unwrap();
        assert!(quantize_equal_width(m, 0).is_err());
        assert!(quantize_equal_width(m, 1).is_err());
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid3_produces_18_atoms() {
        let n = 80;
        let mut rng = crate::preprocess::SplitMix64::new(42);
        let mut s0_data = Vec::with_capacity(n * 2);
        let mut s1_data = Vec::with_capacity(n * 2);
        let mut s2_data = Vec::with_capacity(n);
        let mut t_data = Vec::with_capacity(n);
        for _ in 0..n {
            let signal = rng.normal();
            // S0 carries signal in dim 0.
            s0_data.push(signal + 0.1 * rng.normal());
            s0_data.push(rng.normal());
            // S1 carries signal in dim 0 (redundant with S0).
            s1_data.push(signal + 0.1 * rng.normal());
            s1_data.push(rng.normal());
            // S2 is pure noise.
            s2_data.push(rng.normal());
            // T = signal + small noise.
            t_data.push(signal + 0.05 * rng.normal());
        }
        let s0 = MatRef::new(&s0_data, n, 2).unwrap();
        let s1 = MatRef::new(&s1_data, n, 2).unwrap();
        let s2 = MatRef::new(&s2_data, n, 1).unwrap();
        let t = MatRef::new(&t_data, n, 1).unwrap();

        let result = same_sample_quantized_imin_pid3(s0, s1, s2, t, 8).unwrap();
        assert_eq!(result.quantization.num_bins, 8);
        let result = result.into_categorical_result();
        assert_eq!(result.atoms.len(), 18, "should produce 18 atoms");
        assert_eq!(result.redundancies.len(), 18);
        assert!(matches!(
            result.input.encoding,
            IminInputEncoding::Categorical
        ));
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid3_redundant_sources_dominant() {
        // S0 ≈ S1 (near-copy), S2 is noise → redundancy should dominate.
        let n = 200;
        let mut rng = crate::preprocess::SplitMix64::new(99);
        let mut s0 = Vec::with_capacity(n);
        let mut s1 = Vec::with_capacity(n);
        let mut s2 = Vec::with_capacity(n);
        let mut t = Vec::with_capacity(n);
        for _ in 0..n {
            let sig = rng.normal();
            s0.push(sig);
            s1.push(sig + 0.01 * rng.normal());
            s2.push(rng.normal());
            t.push(sig + 0.1 * rng.normal());
        }
        let s0_m = MatRef::new(&s0, n, 1).unwrap();
        let s1_m = MatRef::new(&s1, n, 1).unwrap();
        let s2_m = MatRef::new(&s2, n, 1).unwrap();
        let t_m = MatRef::new(&t, n, 1).unwrap();

        let result = same_sample_quantized_imin_pid3(s0_m, s1_m, s2_m, t_m, 10)
            .unwrap()
            .into_categorical_result();

        // Lattice landmarks (see `discrete_antichains_3()`), redundancies in antichain order:
        //   index 6  = {{0,1,2}}        — the single full collection = lattice TOP, whose
        //              I_min equals the joint MI I(S0,S1,S2;T) (NOT a redundancy);
        //   index 7  = {{0},{1}}        — pairwise redundancy of the two near-copies S0,S1;
        //   index 16 = {{0},{1},{2}}    — global redundancy shared by *all three* sources,
        //              hence diluted by the noise source S2.
        let joint_top = result.redundancies[6]; // {0b111} — joint MI, not redundancy
        let red_s0_s1 = result.redundancies[7]; // {{0},{1}} — pairwise redundancy
        let red_all = result.redundancies[16]; // {{0},{1},{2}} — global redundancy

        // The TOP node {{0,1,2}} is a *single* collection, so by the self-redundancy axiom its
        // I_min equals the joint MI I(S0,S1,S2;T) exactly — a strong invariant, not just a bound.
        assert!(
            (joint_top - result.mi_s0s1s2_t).abs() < 1e-9,
            "TOP node {{0,1,2}} must equal the joint MI exactly; top={joint_top}, joint MI={}",
            result.mi_s0s1s2_t
        );

        // Because S0 and S1 are near-copies, the information they *share* about T is sizable —
        // close to I(S0;T). This is the genuine redundancy-dominance claim.
        assert!(
            red_s0_s1 > 0.3 * result.mi_s0_t,
            "Pairwise redundancy of near-copies should be > 30% of I(S0;T); red_s0_s1={red_s0_s1}, MI={}",
            result.mi_s0_t
        );

        // Adding the pure-noise source S2 can only shrink the shared information: the global
        // (all-three) redundancy must not exceed the pairwise redundancy of S0,S1.
        assert!(
            red_all <= red_s0_s1 + 1e-9,
            "Global redundancy (incl. noise S2) must not exceed pairwise S0,S1 redundancy; \
             red_all={red_all}, red_s0_s1={red_s0_s1}"
        );
    }

    #[cfg(feature = "experimental-pipelines")]
    #[test]
    fn discrete_pid3_rejects_mismatched_rows() {
        let s0_data = vec![0.0; 10];
        let s1_data = vec![0.0; 5];
        let s2_data = vec![0.0; 10];
        let t_data = vec![0.0; 10];
        let s0 = MatRef::new(&s0_data, 10, 1).unwrap();
        let s1 = MatRef::new(&s1_data, 5, 1).unwrap();
        let s2 = MatRef::new(&s2_data, 10, 1).unwrap();
        let t = MatRef::new(&t_data, 10, 1).unwrap();
        assert!(same_sample_quantized_imin_pid3(s0, s1, s2, t, 5).is_err());
    }
}
