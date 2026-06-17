use crate::error::{PidError, PidResult};
use crate::isx::{isx_redundancy, IsxConfig};
use crate::ksg::{ksg_mi, ksg_mi_concat_xy, ksg_mi_xblocks, KsgConfig};
use crate::matrix::MatRef;
use crate::pid2::{Pid2Estimate, Pid2Result};
use crate::pid3::{pid3_isx, Pid3Config, Pid3Result};

#[derive(Debug, Clone)]
pub enum PairSelection {
    /// Compute PID for every pair (O(m²) pairs).
    All,
    /// Compute PID only for the `k` pairs with the most negative co-information (most "synergy-like").
    TopKMostNegativeCi { k: usize },
    /// Compute PID for pairs whose co-information is <= `threshold`.
    CiBelow { threshold: f64 },
}

#[derive(Debug, Clone)]
pub struct HierarchicalConfig {
    pub ksg: KsgConfig,
    pub isx: IsxConfig,
    pub pid3: Pid3Config,
    pub selection: PairSelection,
    /// If false, only compute Level-1 screening (CI + MI terms); `pid` is always `None`.
    pub compute_pid: bool,
    /// If true, compute the full 3-source SxPID (18 atoms) for `hierarchical_triplet`.
    ///
    /// This is expensive (offline only); prefer Level 1/2 for real-time paths.
    pub compute_pid3: bool,
}

impl Default for HierarchicalConfig {
    fn default() -> Self {
        Self {
            ksg: KsgConfig::default(),
            isx: IsxConfig::default(),
            pid3: Pid3Config::default(),
            selection: PairSelection::TopKMostNegativeCi { k: 16 },
            compute_pid: true,
            compute_pid3: false,
        }
    }
}

#[derive(Debug, Clone)]
pub struct PairwiseScreen {
    pub i: usize,
    pub j: usize,
    /// Co-information CI(X_i, X_j; T) = I(X_i;T) + I(X_j;T) - I((X_i,X_j);T)
    pub ci: f64,
    pub mi_i_t: f64,
    pub mi_j_t: f64,
    pub mi_ij_t: f64,
    /// Optional Level-2 PID computed for selected pairs only.
    pub pid: Option<Pid2Result>,
}

#[derive(Debug, Clone)]
pub struct HierarchicalTriplet {
    pub pairwise: Vec<PairwiseScreen>,
    /// 3-source co-information CI(X,Y,Z;T) computed from MI terms.
    pub ci_triplet: f64,
    /// Joint MI term I(X,Y,Z;T) used in `ci_triplet`.
    pub mi_xyz_t: f64,
    /// Optional Level-3 full 3-source SxPID (18 atoms).
    pub pid3: Option<Pid3Result>,
}

/// Hierarchical pairwise analysis:
///
/// - Level 1 (fast screening): compute CI for all pairs from MI terms.
/// - Level 2 (targeted): compute `I^sx_∩` PID only for selected pairs.
///
/// `sources` is a list of (n×d_i) matrices; all must share the same `n` as `target`.
pub fn hierarchical_pairwise(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<Vec<PairwiseScreen>> {
    if sources.len() < 2 {
        return Err(PidError::InvalidConfig {
            context: "hierarchical_pairwise",
            message: "need at least 2 sources",
        });
    }
    let n = target.nrows();
    for s in sources {
        if s.nrows() != n {
            return Err(PidError::RowCountMismatch {
                context: "hierarchical_pairwise",
                left_rows: n,
                right_rows: s.nrows(),
            });
        }
        if s.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: "hierarchical_pairwise",
                message: "source has 0 columns",
            });
        }
    }
    if target.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context: "hierarchical_pairwise",
            message: "target has 0 columns",
        });
    }

    // Precompute I(X_i;T) for each source.
    let mut mi_i_t = Vec::with_capacity(sources.len());
    for s in sources {
        mi_i_t.push(ksg_mi(*s, target, &cfg.ksg)?);
    }

    let m = sources.len();
    let pairs_cap = m.saturating_mul(m.saturating_sub(1)) / 2;
    let mut pairs = Vec::with_capacity(pairs_cap);
    for i in 0..m {
        for j in (i + 1)..m {
            let mi_ij_t = ksg_mi_concat_xy(sources[i], sources[j], target, &cfg.ksg)?;
            let ci = mi_i_t[i] + mi_i_t[j] - mi_ij_t;
            pairs.push(PairwiseScreen {
                i,
                j,
                ci,
                mi_i_t: mi_i_t[i],
                mi_j_t: mi_i_t[j],
                mi_ij_t,
                pid: None,
            });
        }
    }

    if !cfg.compute_pid {
        return Ok(pairs);
    }

    let mut selected = vec![false; pairs.len()];
    match cfg.selection {
        PairSelection::All => selected.fill(true),
        PairSelection::CiBelow { threshold } => {
            for (idx, p) in pairs.iter().enumerate() {
                if p.ci <= threshold {
                    selected[idx] = true;
                }
            }
        }
        PairSelection::TopKMostNegativeCi { k } => {
            if k == 0 {
                return Ok(pairs);
            }
            let mut idxs: Vec<usize> = (0..pairs.len()).collect();
            // Deterministic ordering: primary by ci ascending, then by (i,j).
            idxs.sort_by(|&a, &b| {
                pairs[a]
                    .ci
                    .total_cmp(&pairs[b].ci)
                    .then_with(|| pairs[a].i.cmp(&pairs[b].i))
                    .then_with(|| pairs[a].j.cmp(&pairs[b].j))
            });
            for &idx in idxs.iter().take(k.min(idxs.len())) {
                selected[idx] = true;
            }
        }
    }

    for (idx, p) in pairs.iter_mut().enumerate() {
        if !selected[idx] {
            continue;
        }
        let s1 = sources[p.i];
        let s2 = sources[p.j];
        let red = isx_redundancy(s1, s2, target, &cfg.isx)?;
        let est = Pid2Estimate {
            mi_s1_t: p.mi_i_t,
            mi_s2_t: p.mi_j_t,
            mi_s1s2_t: p.mi_ij_t,
            redundancy_isx: red,
        };
        p.pid = Some(Pid2Result::from_estimate(est));
    }

    Ok(pairs)
}

/// Hierarchical analysis for exactly three sources (X,Y,Z) and one target T.
///
/// - Computes pairwise Level-1 CI screening and optional Level-2 PIDs (via `hierarchical_pairwise`).
/// - Additionally computes the 3-source co-information CI(X,Y,Z;T) using 7 MI estimates.
pub fn hierarchical_triplet(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<HierarchicalTriplet> {
    let sources = [x, y, z];
    let pairwise = hierarchical_pairwise(&sources, t, cfg)?;

    let mut mi_i_t = [0.0f64; 3];
    let mut seen = [false; 3];
    let mut mi01 = None;
    let mut mi02 = None;
    let mut mi12 = None;

    for p in &pairwise {
        mi_i_t[p.i] = p.mi_i_t;
        seen[p.i] = true;
        mi_i_t[p.j] = p.mi_j_t;
        seen[p.j] = true;
        match (p.i, p.j) {
            (0, 1) => mi01 = Some(p.mi_ij_t),
            (0, 2) => mi02 = Some(p.mi_ij_t),
            (1, 2) => mi12 = Some(p.mi_ij_t),
            _ => {}
        }
    }

    if seen.iter().any(|&ok| !ok) || mi01.is_none() || mi02.is_none() || mi12.is_none() {
        return Err(PidError::InvalidConfig {
            context: "hierarchical_triplet",
            message: "unexpected pairwise index set",
        });
    }

    let mi_xyz_t = ksg_mi_xblocks(&sources, t, &cfg.ksg)?;
    let ci_triplet =
        mi_i_t[0] + mi_i_t[1] + mi_i_t[2] - mi01.unwrap() - mi02.unwrap() - mi12.unwrap()
            + mi_xyz_t;

    let pid3 = if cfg.compute_pid3 {
        Some(pid3_isx(x, y, z, t, &cfg.pid3)?)
    } else {
        None
    };

    Ok(HierarchicalTriplet {
        pairwise,
        ci_triplet,
        mi_xyz_t,
        pid3,
    })
}
