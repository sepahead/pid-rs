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
///
/// # Example
/// ```
/// use pid_core::{pid2_isx, MatRef, Pid2Config};
/// // T depends on both sources, so expect non-trivial synergy/redundancy.
/// let s1 = [0.0, 1.0, 0.0, 1.0, 0.2, 0.8, 0.1, 0.9];
/// let s2 = [0.0, 0.0, 1.0, 1.0, 0.1, 0.9, 0.8, 0.2];
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
        // Preserve the established ordinary-regime arithmetic bit-for-bit. Only retry with a
        // scale-safe linear reduction when the left-associated expression overflowed before later
        // terms could cancel it.
        let syn = if syn_direct.is_finite() {
            syn_direct
        } else {
            scaled_linear_sum([est.mi_s1s2_t, -est.mi_s1_t, -est.mi_s2_t, red])
        };
        if [red, unq1, unq2, syn]
            .iter()
            .any(|value| !value.is_finite())
        {
            return Err(PidError::NumericalInstability {
                context: "Pid2Result::from_estimate atoms",
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

fn scaled_linear_sum(terms: [f64; 4]) -> f64 {
    let scale = terms
        .iter()
        .fold(0.0_f64, |current, value| current.max(value.abs()));
    if scale == 0.0 {
        return 0.0;
    }

    let mut sum = 0.0;
    let mut correction = 0.0;
    for term in terms {
        let value = term / scale;
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    scale * (sum + correction)
}
