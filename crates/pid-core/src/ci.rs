use crate::error::PidResult;
use crate::ksg::{ksg_mi, ksg_mi_concat_xy, ksg_mi_xblocks, KsgConfig, NegativeHandling};
use crate::matrix::MatRef;

/// Pairwise co-information (a Shannon invariant) computed via KSG MI estimates:
///
/// CI(X,Y;T) = I(X;T) + I(Y;T) - I((X,Y);T)
///
/// Sign convention (2 sources): `CI = Red − Syn`, so **negative** co-information indicates net
/// synergy and **positive** indicates net redundancy.
pub fn co_information_pairwise(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    // Co-information requires unclamped cancellation of the MI terms; force `Allow`.
    let cfg = &KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.clone()
    };
    let i_xt = ksg_mi(x, t, cfg)?;
    let i_yt = ksg_mi(y, t, cfg)?;
    let i_xyt = ksg_mi_concat_xy(x, y, t, cfg)?;
    Ok(i_xt + i_yt - i_xyt)
}

/// 3-source co-information (interaction information / Shannon invariant) computed via KSG MI estimates:
///
/// CI(X,Y,Z;T) = I(X;T)+I(Y;T)+I(Z;T)
///              - I(X,Y;T) - I(X,Z;T) - I(Y,Z;T)
///              + I(X,Y,Z;T)
///
/// Sign interpretation is **parity-flipped** vs. the 2-source case and is *not* a clean
/// synergy/redundancy indicator: a pure 3-way synergy (`T = X⊕Y⊕Z`) gives `CI > 0`, and at
/// 3 sources `CI` conflates redundancy and synergy. Use it only as a coarse screen, not a verdict.
pub fn co_information_triplet(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    // Co-information requires unclamped cancellation of the MI terms; force `Allow`.
    let cfg = &KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.clone()
    };
    let i_xt = ksg_mi(x, t, cfg)?;
    let i_yt = ksg_mi(y, t, cfg)?;
    let i_zt = ksg_mi(z, t, cfg)?;

    let i_xyt = ksg_mi_concat_xy(x, y, t, cfg)?;
    let i_xzt = ksg_mi_concat_xy(x, z, t, cfg)?;
    let i_yzt = ksg_mi_concat_xy(y, z, t, cfg)?;

    let i_xyzt = ksg_mi_xblocks(&[x, y, z], t, cfg)?;

    Ok(i_xt + i_yt + i_zt - i_xyt - i_xzt - i_yzt + i_xyzt)
}
