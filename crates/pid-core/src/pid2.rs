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

pub fn pid2_isx(
    s1: MatRef<'_>,
    s2: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &Pid2Config,
) -> PidResult<Pid2Result> {
    let estimate = pid2_isx_estimate(s1, s2, t, cfg)?;
    Ok(Pid2Result::from_estimate(estimate))
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

fn validate_pid2_config(cfg: &Pid2Config) -> PidResult<()> {
    if cfg.ksg.k != cfg.isx.k {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_estimate",
            message: "KSG and ISX k values must match",
        });
    }
    if cfg.ksg.metric != cfg.isx.metric {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_estimate",
            message: "KSG and ISX metrics must match",
        });
    }
    if cfg.ksg.tie_epsilon != cfg.isx.tie_epsilon {
        return Err(PidError::InvalidConfig {
            context: "pid2_isx_estimate",
            message: "KSG and ISX tie_epsilon values must match",
        });
    }
    Ok(())
}

impl Pid2Result {
    pub fn from_estimate(est: Pid2Estimate) -> Self {
        let red = est.redundancy_isx;
        let unq1 = est.mi_s1_t - red;
        let unq2 = est.mi_s2_t - red;
        let syn = est.mi_s1s2_t - est.mi_s1_t - est.mi_s2_t + red;
        Self {
            redundancy: red,
            unique_s1: unq1,
            unique_s2: unq2,
            synergy: syn,
        }
    }
}
