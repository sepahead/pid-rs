//! Hyperbolic geometry helpers (Lorentz / hyperboloid model).
//!
//! This module supports **experimental MI-only** pipelines where embeddings are represented in a
//! hyperbolic space and neighborhood queries should use the **hyperbolic geodesic distance**.
//!
//! Important: this does **not** make the paper-faithful, restricted-domain shared-exclusions
//! `I^sx_∩` implementation “hyperbolic-correct” automatically. Treat hyperbolic + `I^sx_∩` as
//! research-gated; this crate claims no general consistency theorem for that combination.

use std::fmt;

use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::matrix::MatRef;
use crate::resource::{
    try_vec_with_capacity, CancellationProgress, CancellationToken, ResourceBudget,
    ResourceEstimate,
};

const CANCELLATION_CHECK_INTERVAL: usize = 1024;

// A checked Lorentz distance can scan both rows for finiteness, scan both spatial parts for their
// norms, compare the full rows, and scan the spatial directions again. Eight coordinate work units
// per coordinate conservatively cover those passes and their scalar arithmetic in resource hints.
pub(crate) const LORENTZ_DISTANCE_COORDINATE_WORK_FACTOR: u128 = 8;

/// Sectional curvature supported by the experimental hyperbolic coordinate APIs.
///
/// Curvature is part of the geometric estimand rather than an implicit implementation detail.
/// The 0.9 review surface supports only the Lorentz/Poincaré models with sectional curvature `-1`;
/// this restriction is proposed for 1.0 without making a 1.x compatibility promise. The enum is
/// deliberately non-exhaustive so future curvature scales require an explicit API extension.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum HyperbolicCurvature {
    /// Unit negative sectional curvature, `K = -1` (equivalently, `κ = 1`).
    NegativeOne,
}

impl HyperbolicCurvature {
    /// Return the signed sectional curvature `K`.
    pub const fn sectional_curvature(self) -> f64 {
        match self {
            Self::NegativeOne => -1.0,
        }
    }

    /// Return `κ = sqrt(-K)`, the inverse length scale used in hyperbolic formulas.
    pub const fn kappa(self) -> f64 {
        match self {
            Self::NegativeOne => 1.0,
        }
    }
}

impl fmt::Display for HyperbolicCurvature {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::NegativeOne => formatter.write_str("sectional curvature -1 (kappa=1)"),
        }
    }
}

/// Lorentz-model distance configuration for feature-gated hyperbolic entry points.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct HyperbolicMetric {
    /// Explicit curvature scale forming part of the geometric estimand.
    pub curvature: HyperbolicCurvature,
}

impl HyperbolicMetric {
    /// Construct a Lorentz-model metric at an explicitly selected curvature.
    pub const fn lorentz(curvature: HyperbolicCurvature) -> Self {
        Self { curvature }
    }

    /// Compute a checked Lorentz-model geodesic distance.
    pub fn distance(self, a: &[f64], b: &[f64]) -> PidResult<f64> {
        hyperbolic_distance_lorentz(a, b, self.curvature)
    }

    pub(crate) const fn kernel(self) -> crate::metric::KernelMetric {
        crate::metric::KernelMetric::HyperbolicLorentz {
            curvature: self.curvature,
        }
    }
}

pub(crate) fn validate_lorentz_matrix_widths(
    context: &'static str,
    inputs: &[MatRef<'_>],
) -> PidResult<()> {
    if inputs.iter().any(|input| input.ncols() < 2) {
        return Err(PidError::InvalidConfig {
            context,
            message: "Lorentz-hyperboloid inputs must have row width d+1 >= 2",
        });
    }
    Ok(())
}

/// Minkowski / Lorentz bilinear form for vectors in the Lorentz model of hyperbolic space.
///
/// Convention: `⟨x,y⟩_L = -x0*y0 + Σ_{i>=1} xi*yi`.
/// Products of finite binary64 inputs are accumulated exactly in a fixed-width integer
/// superaccumulator and rounded once (nearest, ties-to-even). This retains small residuals after
/// cancellations whose individual products overflow or underflow; a genuinely out-of-range result
/// is returned as a structured numerical error rather than a non-finite sentinel.
#[inline]
pub fn lorentz_dot(a: &[f64], b: &[f64]) -> PidResult<f64> {
    if a.len() != b.len() || a.len() < 2 {
        return Err(PidError::InvalidConfig {
            context: "lorentz_dot",
            message: "vectors must have equal length d+1 >= 2",
        });
    }
    if a.iter().chain(b).any(|value| !value.is_finite()) {
        return Err(PidError::NonFiniteInput {
            context: "lorentz_dot",
        });
    }
    let value =
        exact_signed_product_sum(a.iter().zip(b).enumerate().map(|(index, (&left, &right))| {
            // The time coordinate is the sole negative basis direction.
            (left, right, index == 0)
        }));
    if value.is_finite() {
        Ok(value)
    } else {
        Err(PidError::NumericalInstability {
            context: "lorentz_dot result exceeds finite binary64 range",
        })
    }
}

// Every finite binary64 is an integer significand times 2^shift. The smallest product bit is
// 2^-2148; the largest individual product is below 2^2048. Even summing usize::MAX products needs
// fewer than 2^64 additional units in the exponent, so 68 64-bit limbs cover the exact result on
// every supported 32-/64-bit target with room to spare.
const PRODUCT_SUM_BASE_EXPONENT: i32 = -2148;
const PRODUCT_SUM_LIMBS: usize = 68;

fn exact_signed_product_sum(terms: impl IntoIterator<Item = (f64, f64, bool)>) -> f64 {
    let mut positive = [0_u64; PRODUCT_SUM_LIMBS];
    let mut negative = [0_u64; PRODUCT_SUM_LIMBS];

    for (left, right, negate_basis) in terms {
        let (left_negative, left_significand, left_shift) = finite_binary_parts(left);
        let (right_negative, right_significand, right_shift) = finite_binary_parts(right);
        if left_significand == 0 || right_significand == 0 {
            continue;
        }
        let product = u128::from(left_significand) * u128::from(right_significand);
        let product_shift = left_shift + right_shift - PRODUCT_SUM_BASE_EXPONENT;
        debug_assert!(product_shift >= 0);
        let is_negative = left_negative ^ right_negative ^ negate_basis;
        let accumulator = if is_negative {
            &mut negative
        } else {
            &mut positive
        };
        // The fixed range above proves this cannot overflow for a realizable f64 slice. Keep the
        // guard defensive so a future exponent-format change fails closed rather than wrapping.
        if !add_shifted_u128(accumulator, product, product_shift as usize) {
            return if is_negative {
                f64::NEG_INFINITY
            } else {
                f64::INFINITY
            };
        }
    }

    match compare_limbs(&positive, &negative) {
        std::cmp::Ordering::Equal => 0.0,
        std::cmp::Ordering::Greater => {
            let magnitude = subtract_limbs(&positive, &negative);
            round_product_sum(&magnitude, false)
        }
        std::cmp::Ordering::Less => {
            let magnitude = subtract_limbs(&negative, &positive);
            round_product_sum(&magnitude, true)
        }
    }
}

/// `(negative, integer significand, power-of-two shift)` for one finite binary64.
fn finite_binary_parts(value: f64) -> (bool, u64, i32) {
    let bits = value.to_bits();
    let negative = bits >> 63 != 0;
    let exponent = ((bits >> 52) & 0x7ff) as i32;
    let fraction = bits & ((1_u64 << 52) - 1);
    if exponent == 0 {
        (negative, fraction, -1074)
    } else {
        (negative, (1_u64 << 52) | fraction, exponent - 1075)
    }
}

fn add_shifted_u128(accumulator: &mut [u64; PRODUCT_SUM_LIMBS], value: u128, shift: usize) -> bool {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = value as u64;
    let high = (value >> 64) as u64;

    if !add_limb(accumulator, limb, low << offset) {
        return false;
    }
    if offset == 0 {
        add_limb(accumulator, limb + 1, high)
    } else {
        add_limb(accumulator, limb + 1, low >> (64 - offset))
            && add_limb(accumulator, limb + 1, high << offset)
            && add_limb(accumulator, limb + 2, high >> (64 - offset))
    }
}

fn add_limb(accumulator: &mut [u64; PRODUCT_SUM_LIMBS], mut index: usize, value: u64) -> bool {
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

fn compare_limbs(
    left: &[u64; PRODUCT_SUM_LIMBS],
    right: &[u64; PRODUCT_SUM_LIMBS],
) -> std::cmp::Ordering {
    left.iter().rev().cmp(right.iter().rev())
}

/// Exact magnitude subtraction; requires `larger >= smaller`.
fn subtract_limbs(
    larger: &[u64; PRODUCT_SUM_LIMBS],
    smaller: &[u64; PRODUCT_SUM_LIMBS],
) -> [u64; PRODUCT_SUM_LIMBS] {
    let mut out = [0_u64; PRODUCT_SUM_LIMBS];
    let mut borrow = false;
    for index in 0..PRODUCT_SUM_LIMBS {
        let (without_value, value_borrow) = larger[index].overflowing_sub(smaller[index]);
        let (difference, carry_borrow) = without_value.overflowing_sub(u64::from(borrow));
        out[index] = difference;
        borrow = value_borrow || carry_borrow;
    }
    debug_assert!(!borrow);
    out
}

fn highest_set_bit(value: &[u64; PRODUCT_SUM_LIMBS]) -> Option<usize> {
    value
        .iter()
        .rposition(|&limb| limb != 0)
        .map(|index| index * 64 + (63 - value[index].leading_zeros() as usize))
}

fn bit_at(value: &[u64; PRODUCT_SUM_LIMBS], bit: usize) -> bool {
    value
        .get(bit / 64)
        .is_some_and(|limb| limb & (1_u64 << (bit % 64)) != 0)
}

fn any_bits_below(value: &[u64; PRODUCT_SUM_LIMBS], bit_exclusive: usize) -> bool {
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

fn low_u64_after_shift(value: &[u64; PRODUCT_SUM_LIMBS], shift: usize) -> u64 {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = value.get(limb).copied().unwrap_or(0) >> offset;
    if offset == 0 {
        low
    } else {
        low | (value.get(limb + 1).copied().unwrap_or(0) << (64 - offset))
    }
}

/// Round an exact nonzero integer multiple of 2^-2148 to binary64, ties to even.
fn round_product_sum(magnitude: &[u64; PRODUCT_SUM_LIMBS], negative: bool) -> f64 {
    let Some(highest) = highest_set_bit(magnitude) else {
        // The caller invokes rounding only after a strict nonzero magnitude comparison. Keep the
        // boundary total and panic-free if that invariant is changed in a future refactor.
        return 0.0;
    };
    let exact_exponent = highest as i32 + PRODUCT_SUM_BASE_EXPONENT;

    let (cutoff, mut significand, mut output_exponent) = if exact_exponent < -1022 {
        // Subnormal values are integer multiples of 2^-1074, which is accumulator bit 1074.
        let cutoff = (-1074 - PRODUCT_SUM_BASE_EXPONENT) as usize;
        (cutoff, low_u64_after_shift(magnitude, cutoff), -1022)
    } else {
        let cutoff = highest.saturating_sub(52);
        (
            cutoff,
            low_u64_after_shift(magnitude, cutoff),
            exact_exponent,
        )
    };

    if cutoff > 0 {
        let halfway = bit_at(magnitude, cutoff - 1);
        let sticky = any_bits_below(magnitude, cutoff - 1);
        if halfway && (sticky || significand & 1 != 0) {
            significand += 1;
        }
    }

    let sign = if negative { 1_u64 << 63 } else { 0 };
    if exact_exponent < -1022 {
        if significand == 0 {
            return f64::from_bits(sign);
        }
        if significand < 1_u64 << 52 {
            return f64::from_bits(sign | significand);
        }
        // Rounding the largest subnormal can carry into the smallest normal.
        return f64::from_bits(sign | (1_u64 << 52));
    }

    if significand == 1_u64 << 53 {
        significand >>= 1;
        output_exponent += 1;
    }
    if output_exponent > 1023 {
        return f64::from_bits(sign | (0x7ff_u64 << 52));
    }
    let exponent_bits = (output_exponent + 1023) as u64;
    let fraction_bits = significand - (1_u64 << 52);
    f64::from_bits(sign | (exponent_bits << 52) | fraction_bits)
}

/// Geodesic distance in the Lorentz (hyperboloid) model at an explicit curvature.
///
/// At [`HyperbolicCurvature::NegativeOne`], valid points satisfy
/// `⟨x,x⟩_L = -1`, `x0>0`, and the distance is
/// `d(x,y) = arcosh( -⟨x,y⟩_L )`. This implementation uses two numerically robust ingredients:
///
/// 1. **Per-point validity gate.** Each input must lie on the upper unit hyperboloid. Its time
///    coordinate is checked against the stable identity `x0 = hypot(‖x_spatial‖, 1)`. Points whose
///    unit offset is too ill-conditioned to verify in `f64` are rejected instead of being silently
///    admitted.
/// 2. **Hyperbolic polar distance.** Write a point as
///    `x = (cosh(ρ), sinh(ρ) n)`, where `n` is a Euclidean unit vector. The implementation uses
///
///    `sinh²(d/2) = sinh²((ρx−ρy)/2) + sinh(ρx)sinh(ρy)‖nx−ny‖²/4`.
///
///    This avoids the catastrophic cancellation in `acosh(−⟨x,y⟩)`, the Lorentz difference
///    quadratic form, and the Poincaré-ball map for nearby points far from the origin.
///
/// # Errors
///
/// Returns a structured error when dimensions differ, an input is non-finite or off the declared
/// upper hyperboloid, the unit offset cannot be verified at binary64 precision, or distinct rows
/// become numerically indistinguishable. No failure is encoded as `NaN`.
pub fn hyperbolic_distance_lorentz(
    a: &[f64],
    b: &[f64],
    curvature: HyperbolicCurvature,
) -> PidResult<f64> {
    hyperbolic_distance_lorentz_with_context(a, b, curvature, "hyperbolic_distance_lorentz")
}

pub(crate) fn hyperbolic_distance_lorentz_with_context(
    a: &[f64],
    b: &[f64],
    curvature: HyperbolicCurvature,
    context: &'static str,
) -> PidResult<f64> {
    let cancellation = CancellationToken::new();
    hyperbolic_distance_lorentz_with_context_and_cancellation(
        a,
        b,
        curvature,
        context,
        CancellationProgress::new(context, 0, 1),
        &cancellation,
    )
}

pub(crate) fn hyperbolic_distance_lorentz_with_context_and_cancellation(
    a: &[f64],
    b: &[f64],
    curvature: HyperbolicCurvature,
    context: &'static str,
    cancellation_progress: CancellationProgress,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    match curvature {
        HyperbolicCurvature::NegativeOne => {}
    }
    if a.len() != b.len() {
        return Err(PidError::ShapeMismatch {
            context,
            expected_len: a.len(),
            actual_len: b.len(),
        });
    }
    let a_radius = validated_spatial_radius_with_cancellation(
        a,
        context,
        cancellation_progress,
        cancellation,
    )?;
    let b_radius = validated_spatial_radius_with_cancellation(
        b,
        context,
        cancellation_progress,
        cancellation,
    )?;
    if points_equal_with_cancellation(a, b, cancellation_progress, cancellation)? {
        return Ok(0.0);
    }

    let radial_distance = stable_asinh_difference(a_radius, b_radius);
    // Work with twice the half-chord. A representable subnormal distance need not have a
    // representable half, so forming sinh(d/2) first can spuriously collapse it to zero.
    let radial_chord = radial_distance.sinh() / (0.5 * radial_distance).cosh();

    let angular_chord = if a_radius == 0.0 || b_radius == 0.0 {
        0.0
    } else {
        let mut direction_difference = 0.0_f64;
        for i in 1..a.len() {
            if i.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
                cancellation_progress.check(cancellation)?;
            }
            direction_difference = direction_difference.hypot(a[i] / a_radius - b[i] / b_radius);
        }
        cancellation_progress.check(cancellation)?;
        // Form the doubled angular half-chord directly. Rounding a subnormal half-chord and then
        // doubling can be off by one whole subnormal ulp even when the final distance is
        // representable.
        a_radius.sqrt() * b_radius.sqrt() * direction_difference
    };
    let chord = radial_chord.hypot(angular_chord);
    if !chord.is_finite() || chord == 0.0 {
        // Distinct representable rows whose polar coordinates collapse at f64 precision cannot
        // be assigned a trustworthy distance. Fail closed instead of manufacturing a duplicate.
        return Err(PidError::NumericalInstability { context });
    }

    // For a subnormal doubled half-chord, dividing by two destroys information even though the
    // final `2*asinh(chord/2)` is representable. In that range the cubic correction is far below
    // the smallest f64, so the correctly rounded result is `chord` itself.
    let distance = if chord < f64::MIN_POSITIVE {
        chord
    } else {
        2.0 * (0.5 * chord).asinh()
    };
    if !distance.is_finite() || distance < 0.0 {
        return Err(PidError::NumericalInstability { context });
    }
    cancellation_progress.check(cancellation)?;
    Ok(distance)
}

fn points_equal_with_cancellation(
    a: &[f64],
    b: &[f64],
    cancellation_progress: CancellationProgress,
    cancellation: &CancellationToken,
) -> PidResult<bool> {
    cancellation_progress.check(cancellation)?;
    for (index, (&left, &right)) in a.iter().zip(b).enumerate() {
        if index.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
            cancellation_progress.check(cancellation)?;
        }
        if left != right {
            return Ok(false);
        }
    }
    cancellation_progress.check(cancellation)?;
    Ok(true)
}

/// Return `|asinh(a) - asinh(b)|` without subtracting two rounded logarithm-sized values.
fn stable_asinh_difference(a: f64, b: f64) -> f64 {
    let (upper, lower) = if a >= b { (a, b) } else { (b, a) };
    if upper == lower {
        return 0.0;
    }
    let upper_time = upper.hypot(1.0);
    let lower_time = lower.hypot(1.0);
    // asinh(u)-asinh(l) = ln(1 + (u-l)*(1+(u+l)/(tu+tl))/(l+tl)).
    // The factored square-root difference retains adjacent-radius separations at large radius.
    let relative = (upper - lower) * (1.0 + (upper + lower) / (upper_time + lower_time))
        / (lower + lower_time);
    relative.ln_1p()
}

fn validated_spatial_radius(point: &[f64], context: &'static str) -> PidResult<f64> {
    let cancellation = CancellationToken::new();
    validated_spatial_radius_with_cancellation(
        point,
        context,
        CancellationProgress::new(context, 0, 1),
        &cancellation,
    )
}

fn validated_spatial_radius_with_cancellation(
    point: &[f64],
    context: &'static str,
    cancellation_progress: CancellationProgress,
    cancellation: &CancellationToken,
) -> PidResult<f64> {
    if point.len() < 2 {
        return Err(PidError::InvalidConfig {
            context,
            message: "a Lorentz point must contain one time and at least one spatial coordinate",
        });
    }
    cancellation_progress.check(cancellation)?;
    for (index, coordinate) in point.iter().enumerate() {
        if index.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
            cancellation_progress.check(cancellation)?;
        }
        if !coordinate.is_finite() {
            return Err(PidError::NonFiniteInput { context });
        }
    }
    cancellation_progress.check(cancellation)?;
    if point[0] <= 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "a Lorentz point must lie on the upper unit hyperboloid",
        });
    }
    let mut spatial_norm = 0.0_f64;
    for (index, &coordinate) in point[1..].iter().enumerate() {
        if index.is_multiple_of(CANCELLATION_CHECK_INTERVAL) {
            cancellation_progress.check(cancellation)?;
        }
        spatial_norm = spatial_norm.hypot(coordinate);
    }
    cancellation_progress.check(cancellation)?;
    let expected_time = spatial_norm.hypot(1.0);
    if !expected_time.is_finite() {
        return Err(PidError::NumericalInstability { context });
    }
    let next_time = f64::from_bits(expected_time.to_bits() + 1);
    let ulp = next_time - expected_time;
    // The spatial norm uses one rounded `hypot` per coordinate, followed by the final unit-offset
    // `hypot`; the supplied time coordinate has also been rounded independently. Allow twice that
    // count of output ulps for conservative propagation, instead of a relative epsilon band whose
    // width can span tens of ulps and admit materially off-hyperboloid rows at large radius.
    let tolerance = 2.0 * (point.len() as f64 + 1.0) * ulp;
    let unit_offset = expected_time - spatial_norm;
    // A row is verifiable only when the represented unit offset is larger than the tolerance used
    // to admit coordinate rounding. Merely checking `expected_time > spatial_norm` is insufficient:
    // near the representability boundary, a null row `[r, r]` can otherwise fall inside the much
    // wider tolerance band and be accepted as a unit-hyperboloid point.
    if !ulp.is_finite() || ulp <= 0.0 || !tolerance.is_finite() || unit_offset <= tolerance {
        return Err(PidError::NumericalInstability { context });
    }
    if (point[0] - expected_time).abs() > tolerance {
        return Err(PidError::InvalidConfig {
            context,
            message: "a Lorentz point must lie on the upper unit hyperboloid",
        });
    }
    Ok(spatial_norm)
}

const POINCARE_TO_LORENTZ_OPERATION: &str = "poincare_to_lorentz";
const LORENTZ_TO_POINCARE_OPERATION: &str = "lorentz_to_poincare";

/// Estimate owned output memory and arithmetic for Poincaré-to-Lorentz conversion.
///
/// The input dimension excludes the Lorentz time coordinate. The estimate itself does not
/// inspect or allocate input coordinates.
pub fn poincare_to_lorentz_resource_estimate(
    poincare_dimension: usize,
) -> PidResult<ResourceEstimate> {
    if poincare_dimension == 0 {
        return Err(PidError::InvalidConfig {
            context: POINCARE_TO_LORENTZ_OPERATION,
            message: "a Poincare point must have at least one coordinate",
        });
    }
    let output_len = poincare_dimension
        .checked_add(1)
        .ok_or(PidError::SizeOverflow {
            operation: POINCARE_TO_LORENTZ_OPERATION,
        })?;
    conversion_resource_estimate(
        POINCARE_TO_LORENTZ_OPERATION,
        output_len,
        poincare_dimension,
        8,
    )
}

/// Convert a point from the Poincaré ball model to the Lorentz model.
///
/// At [`HyperbolicCurvature::NegativeOne`], the input must satisfy `‖u‖ < 1` and
///
/// - `x0 = (1 + ‖u‖²) / (1 - ‖u‖²)`;
/// - `xi = 2 u_i / (1 - ‖u‖²)`.
///
/// The Euclidean norm is accumulated with repeated `hypot`, avoiding overflow, underflow, and
/// loss of small components inherent in a naive sum of squares. Inputs mathematically inside the
/// open unit ball are nevertheless rejected when their mapped Lorentz unit offset is no longer
/// verifiable in binary64. Thus the representable near-boundary domain is intentionally smaller
/// than `‖u‖ < 1`; the API never returns an unverifiable hyperboloid row.
///
/// # Errors
///
/// Returns a structured error for an empty/non-finite point, a point on or outside the unit-ball
/// boundary, size/resource overflow, allocation failure, or an unverifiable near-boundary map.
pub fn poincare_to_lorentz(u: &[f64], curvature: HyperbolicCurvature) -> PidResult<Vec<f64>> {
    poincare_to_lorentz_with_budget(u, curvature, ResourceBudget::default())
}

/// Budgeted [`poincare_to_lorentz`] conversion.
pub fn poincare_to_lorentz_with_budget(
    u: &[f64],
    curvature: HyperbolicCurvature,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    match curvature {
        HyperbolicCurvature::NegativeOne => {}
    }
    let estimate = poincare_to_lorentz_resource_estimate(u.len())?;
    budget.check(POINCARE_TO_LORENTZ_OPERATION, estimate)?;
    if u.iter().any(|coordinate| !coordinate.is_finite()) {
        return Err(PidError::NonFiniteInput {
            context: POINCARE_TO_LORENTZ_OPERATION,
        });
    }

    let norm = scaled_euclidean_norm(u);
    if !norm.is_finite() {
        return Err(PidError::NumericalInstability {
            context: POINCARE_TO_LORENTZ_OPERATION,
        });
    }
    if norm >= 1.0 {
        return Err(PidError::InvalidConfig {
            context: POINCARE_TO_LORENTZ_OPERATION,
            message: "a Poincare point must have Euclidean norm strictly below one",
        });
    }

    // Factoring 1-r² as (1-r)(1+r) avoids subtracting a separately rounded square near the
    // boundary. The following validity gate still rejects maps whose unit offset is unresolvable.
    let denominator = (1.0 - norm) * (1.0 + norm);
    let norm_squared = norm * norm;
    let time = (1.0 + norm_squared) / denominator;
    let scale = 2.0 / denominator;
    if !(denominator.is_finite() && denominator > 0.0 && time.is_finite() && scale.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: POINCARE_TO_LORENTZ_OPERATION,
        });
    }

    let output_len = u.len().checked_add(1).ok_or(PidError::SizeOverflow {
        operation: POINCARE_TO_LORENTZ_OPERATION,
    })?;
    let mut out = try_vec_with_capacity(POINCARE_TO_LORENTZ_OPERATION, output_len, budget)?;
    out.push(time);
    for &coordinate in u {
        let mapped = scale * coordinate;
        if !mapped.is_finite() {
            return Err(PidError::NumericalInstability {
                context: POINCARE_TO_LORENTZ_OPERATION,
            });
        }
        out.push(mapped);
    }
    validated_spatial_radius(&out, POINCARE_TO_LORENTZ_OPERATION)?;
    Ok(out)
}

/// Estimate owned output memory and arithmetic for Lorentz-to-Poincaré conversion.
pub fn lorentz_to_poincare_resource_estimate(
    lorentz_dimension: usize,
) -> PidResult<ResourceEstimate> {
    if lorentz_dimension < 2 {
        return Err(PidError::InvalidConfig {
            context: LORENTZ_TO_POINCARE_OPERATION,
            message: "a Lorentz point must contain one time and at least one spatial coordinate",
        });
    }
    conversion_resource_estimate(
        LORENTZ_TO_POINCARE_OPERATION,
        lorentz_dimension - 1,
        lorentz_dimension,
        6,
    )
}

/// Convert a validated upper-hyperboloid Lorentz point to the Poincaré ball model.
///
/// # Errors
///
/// Returns a structured error when the Lorentz row is invalid or unverifiable, or when the output
/// allocation/resource preflight fails. Returned coordinates always have a finite norm below one.
pub fn lorentz_to_poincare(point: &[f64], curvature: HyperbolicCurvature) -> PidResult<Vec<f64>> {
    lorentz_to_poincare_with_budget(point, curvature, ResourceBudget::default())
}

/// Budgeted [`lorentz_to_poincare`] conversion.
pub fn lorentz_to_poincare_with_budget(
    point: &[f64],
    curvature: HyperbolicCurvature,
    budget: ResourceBudget,
) -> PidResult<Vec<f64>> {
    match curvature {
        HyperbolicCurvature::NegativeOne => {}
    }
    let estimate = lorentz_to_poincare_resource_estimate(point.len())?;
    budget.check(LORENTZ_TO_POINCARE_OPERATION, estimate)?;
    validated_spatial_radius(point, LORENTZ_TO_POINCARE_OPERATION)?;

    let denominator = point[0] + 1.0;
    if !denominator.is_finite() || denominator <= 0.0 {
        return Err(PidError::NumericalInstability {
            context: LORENTZ_TO_POINCARE_OPERATION,
        });
    }
    let output_len = point.len() - 1;
    let mut out = try_vec_with_capacity(LORENTZ_TO_POINCARE_OPERATION, output_len, budget)?;
    for &coordinate in &point[1..] {
        let mapped = coordinate / denominator;
        if !mapped.is_finite() {
            return Err(PidError::NumericalInstability {
                context: LORENTZ_TO_POINCARE_OPERATION,
            });
        }
        out.push(mapped);
    }
    let norm = scaled_euclidean_norm(&out);
    if !norm.is_finite() || norm >= 1.0 {
        return Err(PidError::NumericalInstability {
            context: LORENTZ_TO_POINCARE_OPERATION,
        });
    }
    Ok(out)
}

fn scaled_euclidean_norm(coordinates: &[f64]) -> f64 {
    coordinates
        .iter()
        .fold(0.0_f64, |norm, &coordinate| norm.hypot(coordinate))
}

fn conversion_resource_estimate(
    operation: &'static str,
    output_len: usize,
    arithmetic_dimension: usize,
    operations_per_coordinate: u128,
) -> PidResult<ResourceEstimate> {
    let memory = ResourceEstimate::contiguous::<f64>(operation, output_len)?;
    let operations_hint = (arithmetic_dimension as u128)
        .checked_mul(operations_per_coordinate)
        .and_then(|operations| operations.checked_add(16))
        .ok_or(PidError::SizeOverflow { operation })?;
    Ok(ResourceEstimate {
        operations_hint,
        ..memory
    })
}

#[cfg(test)]
mod tests {
    use std::mem::size_of;

    use super::{
        hyperbolic_distance_lorentz as hyperbolic_distance_lorentz_result,
        lorentz_dot as lorentz_dot_result, lorentz_to_poincare,
        poincare_to_lorentz as poincare_to_lorentz_result, poincare_to_lorentz_resource_estimate,
        poincare_to_lorentz_with_budget, HyperbolicCurvature,
    };
    use crate::{PidError, ResourceBudget};

    const CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;

    fn hyperbolic_distance_lorentz(a: &[f64], b: &[f64]) -> f64 {
        hyperbolic_distance_lorentz_result(a, b, CURVATURE).unwrap_or(f64::NAN)
    }

    fn lorentz_dot(a: &[f64], b: &[f64]) -> f64 {
        lorentz_dot_result(a, b).expect("valid finite Lorentz product")
    }

    fn poincare_to_lorentz(point: &[f64]) -> Option<Vec<f64>> {
        poincare_to_lorentz_result(point, CURVATURE).ok()
    }

    #[test]
    fn lorentz_distance_matches_known_geodesic_in_h1() {
        // In H^1 (2D Lorentz vectors), points along a geodesic can be parameterized as:
        // x(t) = (cosh t, sinh t). Distance from x(0) to x(t) equals |t|.
        let t = 0.7_f64;
        let x0 = [1.0_f64, 0.0_f64];
        let xt = [t.cosh(), t.sinh()];

        // Check hyperboloid constraint: <x,x>_L = -1
        let n0 = lorentz_dot(&x0, &x0);
        let nt = lorentz_dot(&xt, &xt);
        assert!((n0 + 1.0).abs() < 1e-12);
        assert!((nt + 1.0).abs() < 1e-12);

        let d = hyperbolic_distance_lorentz(&x0, &xt);
        assert!((d - t).abs() < 1e-12, "d={d} t={t}");
        let d_sym = hyperbolic_distance_lorentz(&xt, &x0);
        assert!((d_sym - t).abs() < 1e-12, "d_sym={d_sym} t={t}");
        let d0 = hyperbolic_distance_lorentz(&x0, &x0);
        assert!(d0.abs() < 1e-12, "d0={d0}");
    }

    #[test]
    fn coincident_far_from_origin_point_has_zero_distance_not_nan() {
        // Regression: a point at large hyperbolic radius (Poincaré ball-norm 0.99) has a
        // Lorentz-dot cancellation error that exceeds the old fixed 1e-12 snap tolerance, so the
        // previous implementation returned NaN for d(x, x). The scale-aware tolerance + the
        // difference-based formula must return exactly 0.
        let u = [0.99_f64, 0.0];
        let x = poincare_to_lorentz(&u).expect("valid poincare point");
        assert!(x[0] > 50.0, "expected a far-from-origin point, x0={}", x[0]);
        let d = hyperbolic_distance_lorentz(&x, &x);
        assert!(
            d.is_finite() && d.abs() < 1e-9,
            "d(x,x)={d} should be ~0, not NaN"
        );

        // A nearby (not identical) far point still yields a small, finite, accurate distance.
        let u2 = [0.990_000_1_f64, 0.0];
        let y = poincare_to_lorentz(&u2).unwrap();
        let d2 = hyperbolic_distance_lorentz(&x, &y);
        assert!(
            d2.is_finite() && d2 > 0.0,
            "d(x,y)={d2} should be small positive"
        );
    }

    #[test]
    fn off_hyperboloid_points_return_nan() {
        // x0 = 0 is not a valid hyperboloid point (needs x0 = sqrt(1+||xi||^2) >= 1); the gate must
        // reject it (this underlies tests/hyperbolic_mi.rs::ksg_mi_rejects_invalid_hyperbolic).
        let a = [0.0_f64, 0.1];
        let b = [0.0_f64, 0.2];
        assert!(hyperbolic_distance_lorentz(&a, &b).is_nan());

        assert!(hyperbolic_distance_lorentz(&[2.0, 0.0], &[2.0, 0.0]).is_nan());
        assert!(hyperbolic_distance_lorentz(&[-1.0, 0.0], &[-1.0, 0.0]).is_nan());
    }

    #[test]
    fn nearby_far_points_do_not_collapse_to_zero_distance() {
        // Both rows satisfy x0^2-x1^2=1 in f64. Direct Lorentz-dot and difference-quadratic
        // formulas round their two large terms to equality and incorrectly produce distance 0.
        let a = [1_634_508.686_236_208_3, 1_634_508.686_235_902_4];
        let b = [1_634_672.145_277_647_3, 1_634_672.145_277_341_4];

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert!((distance - 1.0e-4).abs() < 2.0e-10, "distance={distance}");
    }

    #[test]
    fn nearby_far_points_retain_radial_distance_below_ball_precision() {
        // Exact H^1 rows for t=14.7 and t=14.699999999997999. Mapping both rows to the
        // Poincare ball loses most of this separation and used to overestimate it by about 134x.
        let a = [1.210_873_816_626_412_3e6, 1.210_873_816_625_999_5e6];
        let b = [1.210_873_816_623_990_4e6, 1.210_873_816_623_577_4e6];
        let expected = 2.000_177_801_164_682e-12;

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert!(
            (distance - expected).abs() < 5.0e-16,
            "distance={distance} expected={expected}"
        );
    }

    #[test]
    fn distinct_rows_below_ball_precision_retain_radial_distance() {
        let t0 = 15.0_f64;
        let t1 = t0 + 1.0e-11;
        let a = [t0.cosh(), t0.sinh()];
        let b = [t1.cosh(), t1.sinh()];
        assert_ne!(a, b);

        let distance = hyperbolic_distance_lorentz(&a, &b);
        let expected = (t1 - t0).abs();
        assert!((distance - expected).abs() < 5.0e-15);
    }

    #[test]
    fn per_point_gate_rejects_small_but_material_norm_error() {
        let t = 15.0_f64;
        let off = [t.cosh() + 3.0e-8, t.sinh()];
        let valid = [t.cosh(), t.sinh()];

        assert!(hyperbolic_distance_lorentz(&off, &valid).is_nan());
    }

    #[test]
    fn per_point_gate_rejects_null_rows_before_the_offset_rounds_away() {
        let null = [30_000_000.0, 30_000_000.0];
        let origin = [1.0, 0.0];
        assert_eq!(lorentz_dot(&null, &null), 0.0);

        assert!(hyperbolic_distance_lorentz(&null, &origin).is_nan());
    }

    #[test]
    fn per_point_gate_rejects_rows_many_ulps_from_the_unit_hyperboloid() {
        let off = [10_000_000.000_000_086, 10_000_000.0];
        let origin = [1.0, 0.0];
        let represented_norm = lorentz_dot(&off, &off);
        assert!(
            (represented_norm + 1.0).abs() > 0.5,
            "row should have a material norm error, got {represented_norm}"
        );

        assert!(hyperbolic_distance_lorentz(&off, &origin).is_nan());
    }

    #[test]
    fn opposite_subnormal_directions_retain_representable_distance() {
        let smallest = f64::from_bits(1);
        let a = [1.0, smallest];
        let b = [1.0, -smallest];

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert_eq!(distance.to_bits(), 2);
    }

    #[test]
    fn origin_to_subnormal_radius_retains_the_final_distance() {
        let smallest = f64::from_bits(1);
        let origin = [1.0, 0.0];
        let neighbor = [1.0, smallest];

        let distance = hyperbolic_distance_lorentz(&origin, &neighbor);

        assert_eq!(distance.to_bits(), 1);
    }

    #[test]
    fn orthogonal_subnormal_directions_round_only_after_the_final_distance() {
        let smallest = f64::from_bits(1);
        let a = [1.0, smallest, 0.0];
        let b = [1.0, 0.0, smallest];

        let distance = hyperbolic_distance_lorentz(&a, &b);

        // sqrt(2) * min_subnormal rounds to one min-subnormal. Rounding the half-chord first and
        // then doubling used to return two.
        assert_eq!(distance.to_bits(), 1);
    }

    #[test]
    fn adjacent_far_radii_use_a_stable_rapidity_difference() {
        let radius_a = 1_000_000.0_f64;
        let radius_b = 1_000_000.000_000_001_f64;
        let a = [radius_a.hypot(1.0), radius_a];
        let b = [radius_b.hypot(1.0), radius_b];
        let expected = 1.047_737_896_441_889e-15;

        let distance = hyperbolic_distance_lorentz(&a, &b);

        assert!((distance - expected).abs() < 1.0e-28, "distance={distance}");
    }

    #[test]
    fn lorentz_dot_recovers_exact_cancellation_after_product_overflow() {
        let point = [f64::MAX, f64::MAX];

        let dot = lorentz_dot(&point, &point);

        assert_eq!(dot, 0.0);
    }

    #[test]
    fn lorentz_dot_retains_small_terms_after_overflow_scale_cancellation() {
        let positive = [f64::MAX, f64::MAX, 1.0];
        let negative = [f64::MAX, f64::MAX, -1.0];
        assert_eq!(lorentz_dot(&positive, &positive), 1.0);
        assert_eq!(lorentz_dot(&positive, &negative), -1.0);

        let mixed_a = [f64::MAX, f64::MAX, 2.0_f64.powi(500)];
        let mixed_b = [f64::MAX, f64::MAX, 2.0_f64.powi(-500)];
        assert_eq!(lorentz_dot(&mixed_a, &mixed_b), 1.0);
    }

    #[test]
    fn lorentz_dot_rounds_exact_subnormal_product_sums_once() {
        let smallest = f64::from_bits(1);
        // Each spatial product is exactly half a minimum subnormal. Their exact sum is one
        // minimum subnormal, even though separately rounded binary64 products would both be zero.
        assert_eq!(
            lorentz_dot(&[0.0, smallest, smallest], &[0.0, 0.5, 0.5]).to_bits(),
            1
        );
        // One half-minimum-subnormal is exactly halfway between zero and the first subnormal;
        // round-to-nearest, ties-to-even chooses +0.
        assert_eq!(lorentz_dot(&[0.0, smallest], &[0.0, 0.5]).to_bits(), 0);
    }

    #[test]
    fn lorentz_dot_returns_structured_error_for_an_uncancelled_overflow() {
        assert!(matches!(
            lorentz_dot_result(&[f64::MAX, 0.0], &[f64::MAX, 0.0]),
            Err(PidError::NumericalInstability { .. })
        ));
    }

    #[test]
    fn lorentz_superaccumulator_rounds_representative_single_products_like_binary64() {
        let values = [
            f64::from_bits(1),
            f64::from_bits((1_u64 << 52) - 1),
            f64::MIN_POSITIVE,
            2.0_f64.powi(-500),
            0.5,
            1.0,
            2.0,
            2.0_f64.powi(500),
            f64::MAX,
        ];
        for &left in &values {
            for &right in &values {
                let expected = left * right;
                let actual = lorentz_dot_result(&[0.0, left], &[0.0, right]);
                if expected.is_finite() {
                    let actual = actual.unwrap();
                    assert_eq!(
                        actual.to_bits(),
                        expected.to_bits(),
                        "left={left} right={right} actual={actual} expected={expected}"
                    );
                } else {
                    assert!(matches!(actual, Err(PidError::NumericalInstability { .. })));
                }
            }
        }
    }

    #[test]
    fn overflowing_validity_scale_or_difference_returns_nan() {
        // The signed Lorentz products cancel to a finite value while the magnitude sum
        // overflows. An infinite tolerance must not admit these off-hyperboloid points.
        let a = [1e154, 1e154, 1e154];
        let b = [1e154, 1e154, 0.0];
        assert!(hyperbolic_distance_lorentz(&a, &b).is_nan());

        // Finite coordinates can also produce a non-finite difference quadratic form.
        let c = [f64::MAX, 0.0];
        let d = [-f64::MAX, 0.0];
        assert!(hyperbolic_distance_lorentz(&c, &d).is_nan());
    }

    #[test]
    fn invalid_dimensions_return_errors_without_panicking() {
        assert!(matches!(
            lorentz_dot_result(&[], &[]),
            Err(PidError::InvalidConfig { .. })
        ));
        assert!(matches!(
            lorentz_dot_result(&[1.0, 0.0], &[1.0]),
            Err(PidError::InvalidConfig { .. })
        ));
        assert!(hyperbolic_distance_lorentz(&[1.0, 0.0], &[1.0]).is_nan());
    }

    #[test]
    fn poincare_to_lorentz_produces_valid_hyperboloid_points() {
        let u = [0.2_f64, -0.1_f64, 0.05_f64];
        let x = poincare_to_lorentz(&u).expect("valid poincare point");
        assert_eq!(x.len(), u.len() + 1);
        assert!(x[0] > 0.0);
        let n = lorentz_dot(&x, &x);
        assert!((n + 1.0).abs() < 1e-10, "lorentz norm={n}");
    }

    #[test]
    fn poincare_converter_rejects_unverifiable_near_boundary_output() {
        // This point is mathematically inside the ball, but its Lorentz radius is so large that
        // `hypot(radius, 1)` rounds back to `radius`; the unit offset is no longer represented.
        assert!(poincare_to_lorentz(&[0.999_999_999_9]).is_none());
    }

    #[test]
    fn public_distance_returns_structured_errors_instead_of_nan() {
        let error =
            hyperbolic_distance_lorentz_result(&[0.0, 0.1], &[0.0, 0.2], CURVATURE).unwrap_err();

        assert!(matches!(error, PidError::InvalidConfig { .. }));
    }

    #[test]
    fn curvature_accessors_preserve_the_declared_estimand() {
        assert_eq!(CURVATURE.sectional_curvature(), -1.0);
        assert_eq!(CURVATURE.kappa(), 1.0);
        assert_eq!(CURVATURE.to_string(), "sectional curvature -1 (kappa=1)");
    }

    #[test]
    fn poincare_lorentz_round_trip_covers_subnormal_plane_and_high_rapidity_points() {
        let smallest = f64::from_bits(1);
        let points: &[&[f64]] = &[
            &[smallest],
            &[0.2, -0.1, 0.05],
            &[0.99, 0.0],
            &[0.999_999, 0.0],
        ];

        for &point in points {
            let lorentz = poincare_to_lorentz_result(point, CURVATURE).unwrap();
            let round_trip = lorentz_to_poincare(&lorentz, CURVATURE).unwrap();
            for (&actual, &expected) in round_trip.iter().zip(point) {
                let scale = expected.abs().max(f64::MIN_POSITIVE);
                assert!(
                    (actual - expected).abs() <= 16.0 * f64::EPSILON * scale
                        || actual.to_bits().abs_diff(expected.to_bits()) <= 4,
                    "actual={actual:e} expected={expected:e} point={point:?}"
                );
            }
        }
    }

    #[test]
    fn high_rapidity_distance_matches_100_digit_decimal_analytic_oracle() {
        // For the exact binary64 input u=0.9999999, H1 rapidity is
        // ln((1+u)/(1-u)) =
        // 16.811242782044619721795816598281469199461674094818287... .
        // The reference was evaluated from u's exact integer ratio with 100-digit decimal
        // arithmetic; the test carries only the rounded constant and needs no runtime dependency.
        let poincare = [0.999_999_9_f64];
        let point = poincare_to_lorentz_result(&poincare, CURVATURE).unwrap();
        let origin = [1.0, 0.0];
        let distance = hyperbolic_distance_lorentz_result(&origin, &point, CURVATURE).unwrap();
        let oracle = 16.811_242_782_044_62_f64;

        assert!(
            (distance - oracle).abs() <= 8.0 * f64::EPSILON * oracle,
            "distance={distance:e} oracle={oracle:e}"
        );
    }

    #[test]
    fn adjacent_unit_ball_boundary_values_fail_closed_by_reason() {
        let adjacent_inside = f64::from_bits(1.0_f64.to_bits() - 1);
        let near_boundary = poincare_to_lorentz_result(&[adjacent_inside], CURVATURE);
        let boundary = poincare_to_lorentz_result(&[1.0], CURVATURE);

        assert!(matches!(
            near_boundary,
            Err(PidError::NumericalInstability { .. })
        ));
        assert!(matches!(boundary, Err(PidError::InvalidConfig { .. })));
    }

    #[test]
    fn conversion_resource_estimate_and_budget_cover_the_owned_output() {
        let estimate = poincare_to_lorentz_resource_estimate(3).unwrap();
        assert_eq!(estimate.estimated_bytes, 4 * size_of::<f64>() as u128);

        let budget = ResourceBudget {
            max_bytes: estimate.estimated_bytes as u64 - 1,
            max_pairwise_distances: 1,
            max_operations_hint: u128::MAX,
            max_threads: 1,
        };
        assert!(matches!(
            poincare_to_lorentz_with_budget(&[0.0, 0.0, 0.0], CURVATURE, budget),
            Err(PidError::ResourceLimitExceeded {
                resource: "bytes",
                ..
            })
        ));
    }

    #[test]
    fn conversion_estimate_rejects_dimension_overflow_without_allocating() {
        assert!(matches!(
            poincare_to_lorentz_resource_estimate(usize::MAX),
            Err(PidError::SizeOverflow { .. })
        ));
    }
}
