use crate::error::{PidError, PidResult};
use crate::isx::{isx_redundancy, IsxConfig};
use crate::ksg::{ksg_mi, ksg_mi_concat_xy, KsgConfig, NegativeHandling};
use crate::matrix::MatRef;

#[derive(Debug, Clone, Default)]
pub struct Pid2Config {
    pub ksg: KsgConfig,
    pub isx: IsxConfig,
}

#[derive(Debug, Clone)]
pub struct Pid2Estimate {
    pub mi_s1_t: f64,
    pub mi_s2_t: f64,
    pub mi_s1s2_t: f64,
    pub redundancy_isx: f64,
}

#[derive(Debug, Clone)]
pub struct Pid2Result {
    pub redundancy: f64,
    pub unique_s1: f64,
    pub unique_s2: f64,
    pub synergy: f64,
}

/// 2-source PID atoms (Red, Unq₁, Unq₂, Syn) from KSG mutual information and the `I^sx_∩`
/// redundancy, satisfying `Red + Unq₁ + Unq₂ + Syn = I(S1,S2;T)` by construction.
///
/// The redundancy term follows `cfg.isx.method`. Only `IsxMethod::EhrlichKsg` (the default)
/// is the validated continuous estimator; the other methods are experimental baselines, and
/// combining them with the KSG MI terms mixes estimators with different bias profiles —
/// interpret such atoms with care (see the `isx` module docs).
///
/// Relative source units/preprocessing are part of the continuous shared-exclusions estimand;
/// record them and do not compare atoms across schemes. Exact deterministic continuous maps have
/// infinite MI and require a justified noise model or a suitable discrete/mixed estimator.
/// Both sources must also have the same ambient column count. This is a necessary small-ball
/// scaling guard, not proof that their intrinsic dimensions or reference measures are compatible.
///
/// # Example
/// ```
/// use pid_core::{pid2_isx, MatRef, Pid2Config};
/// // T depends on both sources, so expect non-trivial synergy/redundancy.
/// let s1 = [0.13, 0.91, 0.37, 0.62, 0.04, 0.78, 0.49, 0.25];
/// let s2 = [0.84, 0.17, 0.55, 0.03, 0.69, 0.31, 0.96, 0.42];
/// let noise = [0.03, -0.02, 0.01, -0.04, 0.02, -0.01, 0.04, -0.03];
/// let t: Vec<f64> = (0..8).map(|i| s1[i] + s2[i] + noise[i]).collect();
/// let s1 = MatRef::new(&s1, 8, 1)?;
/// let s2 = MatRef::new(&s2, 8, 1)?;
/// let t = MatRef::new(&t, 8, 1)?;
/// let pid = pid2_isx(s1, s2, t, &Pid2Config::default())?;
/// // Atoms reconstruct the joint MI by construction.
/// let sum = pid.redundancy + pid.unique_s1 + pid.unique_s2 + pid.synergy;
/// assert!(sum.is_finite());
/// # Ok::<(), pid_core::PidError>(())
/// ```
pub fn pid2_isx(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Pid2Result> {
    let estimate = pid2_isx_estimate(s1, s2, t, cfg)?;
    Pid2Result::from_estimate(estimate)
}

pub fn pid2_isx_estimate(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Pid2Estimate> {
    validate_pid2_config(cfg)?;
    if s1.ncols() != s2.ncols() {
        return Err(PidError::SourceDimensionMismatch {
            context: "pid2_isx_estimate",
            left_cols: s1.ncols(),
            right_cols: s2.ncols(),
        });
    }
    // The MI terms feed algebraic identities (`Unq`/`Syn` are differences of MIs), so they must
    // not be clamped: clamping a term before a subtraction would break the identity
    // `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`. Force `Allow` regardless of the caller's config so
    // the default path is correct; clamp only the final reported atoms if you need to.
    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.ksg.clone()
    };
    let mi_s1_t = ksg_mi(s1, t, &ksg)?;
    let mi_s2_t = ksg_mi(s2, t, &ksg)?;
    let mi_s1s2_t = ksg_mi_concat_xy(s1, s2, t, &ksg)?;
    let redundancy_isx = isx_redundancy(s1, s2, t, &cfg.isx)?;

    Ok(Pid2Estimate {
        mi_s1_t,
        mi_s2_t,
        mi_s1s2_t,
        redundancy_isx,
    })
}

/// Enforce the KSG/ISX parameter-consistency contract shared by every path that mixes KSG MI
/// terms with an `isx_redundancy` estimate (`pid2_isx`, `hierarchical_pairwise`): the two
/// estimators must agree on `k`, `metric`, and `tie_epsilon` or the atoms mix incompatible
/// neighbourhood geometries.
pub(crate) fn validate_ksg_isx_consistency(
    context: &'static str,
    ksg: &crate::ksg::KsgConfig,
    isx: &crate::isx::IsxConfig,
) -> PidResult<()> {
    if ksg.k != isx.k {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX k values must match",
        });
    }
    if ksg.metric != isx.metric {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX metrics must match",
        });
    }
    if ksg.tie_epsilon != isx.tie_epsilon {
        return Err(PidError::InvalidConfig {
            context,
            message: "KSG and ISX tie_epsilon values must match",
        });
    }
    Ok(())
}

fn validate_pid2_config(cfg: &Pid2Config) -> PidResult<()> {
    validate_ksg_isx_consistency("pid2_isx_estimate", &cfg.ksg, &cfg.isx)
}

impl Pid2Result {
    /// Form PID atoms from already-computed MI/redundancy estimates.
    ///
    /// # Errors
    ///
    /// Returns [`PidError::NumericalInstability`] if an input is non-finite or the atom
    /// subtractions overflow. Estimator entry points are bounded in ordinary regimes, but this
    /// checked public boundary also protects callers constructing [`Pid2Estimate`] directly.
    pub fn from_estimate(est: Pid2Estimate) -> PidResult<Self> {
        if [est.mi_s1_t, est.mi_s2_t, est.mi_s1s2_t, est.redundancy_isx]
            .iter()
            .any(|value| !value.is_finite())
        {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate input",
            });
        }
        let red = est.redundancy_isx;
        let unq1 = est.mi_s1_t - red;
        let unq2 = est.mi_s2_t - red;
        let syn_direct = est.mi_s1s2_t - est.mi_s1_t - est.mi_s2_t + red;
        // Preserve the established ordinary-regime arithmetic bit-for-bit whenever its represented
        // atoms satisfy the PID identities. An exact reduction is needed immediately after an
        // overflow and may also be needed below when finite left-associated arithmetic erased a
        // small residual during cancellation.
        let mut syn = if syn_direct.is_finite() {
            syn_direct
        } else {
            exact_linear_sum([est.mi_s1s2_t, -est.mi_s1_t, -est.mi_s2_t, red])
        };
        if [red, unq1, unq2, syn]
            .iter()
            .any(|value| !value.is_finite())
        {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate atoms",
            });
        }
        // Finite atoms are not sufficient: if a small MI residual lies below the resolution of
        // much larger cancelling atoms, returning them would silently violate the defining PID
        // identities. Check the represented atoms themselves with an exactly accumulated,
        // once-rounded reduction and fail when the original MI cannot be reconstructed to a small
        // ULP budget.
        if !pid2_identities_match(&est, red, unq1, unq2, syn) && syn_direct.is_finite() {
            syn = exact_linear_sum([est.mi_s1s2_t, -est.mi_s1_t, -est.mi_s2_t, red]);
        }
        if !syn.is_finite() || !pid2_identities_match(&est, red, unq1, unq2, syn) {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate atoms cannot represent PID identities",
            });
        }
        Ok(Self {
            redundancy: red,
            unique_s1: unq1,
            unique_s2: unq2,
            synergy: syn,
        })
    }
}

fn pid2_identities_match(
    estimate: &Pid2Estimate,
    redundancy: f64,
    unique_s1: f64,
    unique_s2: f64,
    synergy: f64,
) -> bool {
    identity_matches(estimate.mi_s1_t, [redundancy, unique_s1])
        && identity_matches(estimate.mi_s2_t, [redundancy, unique_s2])
        && identity_matches(
            estimate.mi_s1s2_t,
            [redundancy, unique_s1, unique_s2, synergy],
        )
}

// Every finite binary64 is an integer multiple of 2^-1074. The largest significand occupies
// 2,098 bits at that scale; summing at most usize::MAX terms needs at most usize::BITS more.
const FINITE_SUM_LIMBS: usize = (2_098 + usize::BITS as usize).div_ceil(64);

fn exact_linear_sum<const N: usize>(terms: [f64; N]) -> f64 {
    let mut positive = [0_u64; FINITE_SUM_LIMBS];
    let mut negative = [0_u64; FINITE_SUM_LIMBS];

    for term in terms {
        let bits = term.to_bits();
        let exponent = ((bits >> 52) & 0x7ff) as usize;
        let fraction = bits & ((1_u64 << 52) - 1);
        let significand = if exponent == 0 {
            fraction
        } else {
            (1_u64 << 52) | fraction
        };
        if significand == 0 {
            continue;
        }
        let shift = exponent.saturating_sub(1);
        let accumulator = if bits >> 63 == 0 {
            &mut positive
        } else {
            &mut negative
        };
        if !add_shifted_significand(accumulator, significand, shift) {
            return if bits >> 63 == 0 {
                f64::INFINITY
            } else {
                f64::NEG_INFINITY
            };
        }
    }

    match positive.iter().rev().cmp(negative.iter().rev()) {
        std::cmp::Ordering::Equal => 0.0,
        std::cmp::Ordering::Greater => {
            let magnitude = subtract_finite_sum_limbs(&positive, &negative);
            round_finite_sum(&magnitude, false)
        }
        std::cmp::Ordering::Less => {
            let magnitude = subtract_finite_sum_limbs(&negative, &positive);
            round_finite_sum(&magnitude, true)
        }
    }
}

fn add_shifted_significand(
    accumulator: &mut [u64; FINITE_SUM_LIMBS],
    significand: u64,
    shift: usize,
) -> bool {
    let limb = shift / 64;
    let offset = shift % 64;
    if !add_finite_sum_limb(accumulator, limb, significand << offset) {
        return false;
    }
    offset == 0 || add_finite_sum_limb(accumulator, limb + 1, significand >> (64 - offset))
}

fn add_finite_sum_limb(
    accumulator: &mut [u64; FINITE_SUM_LIMBS],
    mut index: usize,
    value: u64,
) -> bool {
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

fn subtract_finite_sum_limbs(
    larger: &[u64; FINITE_SUM_LIMBS],
    smaller: &[u64; FINITE_SUM_LIMBS],
) -> [u64; FINITE_SUM_LIMBS] {
    let mut difference = [0_u64; FINITE_SUM_LIMBS];
    let mut borrow = false;
    for index in 0..FINITE_SUM_LIMBS {
        let (without_value, value_borrow) = larger[index].overflowing_sub(smaller[index]);
        let (value, carry_borrow) = without_value.overflowing_sub(u64::from(borrow));
        difference[index] = value;
        borrow = value_borrow || carry_borrow;
    }
    debug_assert!(!borrow);
    difference
}

fn highest_finite_sum_bit(value: &[u64; FINITE_SUM_LIMBS]) -> Option<usize> {
    value
        .iter()
        .rposition(|&limb| limb != 0)
        .map(|index| index * 64 + (63 - value[index].leading_zeros() as usize))
}

fn finite_sum_bit(value: &[u64; FINITE_SUM_LIMBS], bit: usize) -> bool {
    value
        .get(bit / 64)
        .is_some_and(|limb| limb & (1_u64 << (bit % 64)) != 0)
}

fn any_finite_sum_bits_below(value: &[u64; FINITE_SUM_LIMBS], bit_exclusive: usize) -> bool {
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

fn low_finite_sum_u64_after_shift(value: &[u64; FINITE_SUM_LIMBS], shift: usize) -> u64 {
    let limb = shift / 64;
    let offset = shift % 64;
    let low = value.get(limb).copied().unwrap_or(0) >> offset;
    if offset == 0 {
        low
    } else {
        low | (value.get(limb + 1).copied().unwrap_or(0) << (64 - offset))
    }
}

/// Round an exact nonzero integer multiple of 2^-1074 to binary64, ties to even.
fn round_finite_sum(magnitude: &[u64; FINITE_SUM_LIMBS], negative: bool) -> f64 {
    let sign = if negative { 1_u64 << 63 } else { 0 };
    let Some(highest) = highest_finite_sum_bit(magnitude) else {
        return f64::from_bits(sign);
    };
    if highest < 52 {
        return f64::from_bits(sign | magnitude[0]);
    }

    let cutoff = highest - 52;
    let mut significand = low_finite_sum_u64_after_shift(magnitude, cutoff);
    if cutoff > 0 {
        let halfway = finite_sum_bit(magnitude, cutoff - 1);
        let sticky = any_finite_sum_bits_below(magnitude, cutoff - 1);
        if halfway && (sticky || significand & 1 != 0) {
            significand += 1;
        }
    }

    let mut exponent = highest as i32 - 1074;
    if significand == 1_u64 << 53 {
        significand >>= 1;
        exponent += 1;
    }
    if exponent > 1023 {
        return f64::from_bits(sign | (0x7ff_u64 << 52));
    }
    let exponent_bits = (exponent + 1023) as u64;
    let fraction_bits = significand - (1_u64 << 52);
    f64::from_bits(sign | (exponent_bits << 52) | fraction_bits)
}

fn identity_matches<const N: usize>(expected: f64, terms: [f64; N]) -> bool {
    let reconstructed = exact_linear_sum(terms);
    if !reconstructed.is_finite() {
        return false;
    }
    ordered_float_bits(reconstructed).abs_diff(ordered_float_bits(expected)) <= 32
}

fn ordered_float_bits(value: f64) -> u64 {
    const SIGN: u64 = 1 << 63;
    let bits = value.to_bits();
    if bits & SIGN == 0 {
        bits | SIGN
    } else {
        !bits
    }
}

#[cfg(test)]
mod tests {
    use super::{Pid2Estimate, Pid2Result};

    #[test]
    fn checked_constructor_rejects_finite_atoms_that_erase_an_mi_identity() {
        let estimate = Pid2Estimate {
            mi_s1_t: 1.0,
            mi_s2_t: 0.0,
            mi_s1s2_t: 0.0,
            redundancy_isx: 1.0e300,
        };

        assert!(Pid2Result::from_estimate(estimate).is_err());
    }
}
