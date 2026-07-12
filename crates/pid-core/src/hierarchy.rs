use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::isx::IsxConfig;
use crate::ksg::{
    effective_thread_count, hash_matrix, ksg_mi_concat_xy_with_budget, ksg_mi_with_budget,
    ksg_mi_xblocks_with_budget, ksg_resource_estimate_for_threads, ksg_xblocks_resource_estimate,
    KsgConfig, NegativeHandling,
};
use crate::matrix::MatRef;
use crate::pid2::{
    pid2_isx_with_budget, pid2_resource_estimate_for_threads, validate_ksg_isx_consistency,
    Pid2Config, Pid2Result,
};
use crate::resource::{try_vec_filled, try_vec_with_capacity, ResourceBudget, ResourceEstimate};
use crate::stats::compensated_sum;

#[derive(Debug, Clone, PartialEq, Serialize)]
#[non_exhaustive]
pub enum PairSelection {
    /// Select every screened pair (O(m²) evaluations).
    All,
    /// Select the `k` pairs with the most negative co-information on the screening split.
    TopKMostNegativeCoInformation { k: usize },
    /// Select pairs whose screening co-information is <= `threshold`.
    CoInformationAtOrBelow { threshold: f64 },
}

#[derive(Debug, Clone)]
pub struct HierarchicalConfig {
    pub ksg: KsgConfig,
    pub isx: IsxConfig,
    pub selection: PairSelection,
    /// `false` selects same-sample screening only. `true` is accepted only by the explicit split
    /// API, where selected PID2 pairs are evaluated on a distinct row set.
    pub compute_pid: bool,
}

impl Default for HierarchicalConfig {
    /// Construct a fail-closed template whose continuous support contracts remain unspecified.
    fn default() -> Self {
        Self {
            ksg: KsgConfig::default(),
            isx: IsxConfig::default(),
            selection: PairSelection::TopKMostNegativeCoInformation { k: 16 },
            compute_pid: false,
        }
    }
}

impl HierarchicalConfig {
    /// Construct the hierarchy with matching explicit absolute-continuity assertions at every
    /// continuous level.
    pub fn assume_regular_full_dimensional() -> Self {
        Self {
            ksg: KsgConfig::assume_regular_full_dimensional(),
            isx: IsxConfig::assume_regular_full_dimensional(),
            ..Self::default()
        }
    }
}

#[derive(Debug, Clone, Serialize)]
#[non_exhaustive]
pub struct PairwiseScreen {
    pub i: usize,
    pub j: usize,
    /// Co-information `I(X_i;T) + I(X_j;T) - I((X_i,X_j);T)` in nats.
    pub co_information_nats: f64,
    pub mi_i_t: f64,
    pub mi_j_t: f64,
    pub mi_ij_t: f64,
    /// Held-out PID2 for selected pairs; always `None` on the same-sample screening API.
    pub pid: Option<Pid2Result>,
}

#[derive(Debug, Clone)]
#[non_exhaustive]
pub struct HierarchicalTriplet {
    pub pairwise: Vec<PairwiseScreen>,
    /// Three-source interaction/co-information computed from seven MI terms.
    pub triplet_co_information_nats: f64,
    /// Joint MI term I(X,Y,Z;T) used in `triplet_co_information_nats`.
    pub mi_xyz_t: f64,
}

/// Caller-declared identities for disjoint screening and evaluation row sets.
#[derive(Debug, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct HierarchySplitIdentity {
    screening_split_id: String,
    evaluation_split_id: String,
}

impl HierarchySplitIdentity {
    pub fn new(screening_split_id: &str, evaluation_split_id: &str) -> PidResult<Self> {
        for value in [screening_split_id, evaluation_split_id] {
            if value.trim().is_empty() || value.len() > 16 * 1024 {
                return Err(PidError::InvalidConfig {
                    context: "HierarchySplitIdentity::new",
                    message: "split identifiers must be nonempty and at most 16 KiB",
                });
            }
        }
        if screening_split_id == evaluation_split_id {
            return Err(PidError::InvalidConfig {
                context: "HierarchySplitIdentity::new",
                message: "screening and evaluation split identifiers must differ",
            });
        }
        Ok(Self {
            screening_split_id: try_hierarchy_text(screening_split_id)?,
            evaluation_split_id: try_hierarchy_text(evaluation_split_id)?,
        })
    }

    pub fn screening_split_id(&self) -> &str {
        &self.screening_split_id
    }

    pub fn evaluation_split_id(&self) -> &str {
        &self.evaluation_split_id
    }
}

/// Machine-readable record of the selection family and its held-out evaluation boundary.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct HierarchySelectionProvenance {
    pub screening_split_id: String,
    pub evaluation_split_id: String,
    /// SHA-256 hashes in source order followed by the target hash.
    pub screening_input_hashes_sha256: Vec<[u8; 32]>,
    /// SHA-256 hashes in source order followed by the target hash.
    pub evaluation_input_hashes_sha256: Vec<[u8; 32]>,
    pub family_size: usize,
    pub selected_count: usize,
    pub selection_rule: PairSelection,
    pub post_selection_p_values_provided: bool,
}

/// Exploratory hierarchy output with screening scores and held-out PID2 evaluations.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct HierarchicalPairwiseReport {
    pub pairs: Vec<PairwiseScreen>,
    pub selection: HierarchySelectionProvenance,
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
    pub warning: &'static str,
}

fn try_hierarchy_text(value: &str) -> PidResult<String> {
    let mut owned = String::new();
    owned
        .try_reserve_exact(value.len())
        .map_err(|_| PidError::AllocationFailed {
            operation: "hierarchy split identity",
            requested_bytes: value.len() as u128,
        })?;
    owned.push_str(value);
    Ok(owned)
}

/// Exploratory same-sample pairwise co-information screening.
///
/// `sources` is a list of (n×d_i) matrices; all must share the same `n` as `target`. Level-1
/// screening allows different `d_i`. PID evaluation is deliberately unavailable here; use
/// [`hierarchical_pairwise_split`] with `compute_pid=true` for held-out evaluation.
pub fn hierarchical_pairwise(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<Vec<PairwiseScreen>> {
    hierarchical_pairwise_with_budget(sources, target, cfg, ResourceBudget::default())
}

/// Same-sample screening under an aggregate resource budget.
pub fn hierarchical_pairwise_with_budget(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &HierarchicalConfig,
    budget: ResourceBudget,
) -> PidResult<Vec<PairwiseScreen>> {
    if cfg.compute_pid {
        return Err(PidError::InvalidConfig {
            context: "hierarchical_pairwise",
            message: "same-sample screening and PID evaluation is disabled; use hierarchical_pairwise_split_with_budget with distinct split identities",
        });
    }
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
    if let PairSelection::CoInformationAtOrBelow { threshold } = cfg.selection {
        if !threshold.is_finite() {
            return Err(PidError::InvalidConfig {
                context: "hierarchical_pairwise",
                message: "CoInformationAtOrBelow threshold must be finite",
            });
        }
    }
    let threads = effective_thread_count(budget.max_threads, target.nrows());
    let resource_estimate =
        hierarchical_pairwise_resource_estimate_for_threads(sources, target, cfg, threads)?;
    budget.check("hierarchical_pairwise", resource_estimate)?;

    // Force `Allow`: clamping before the alternating co-information sum breaks its identity.
    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.ksg.clone()
    };

    // Precompute I(X_i;T) for each source.
    let mut mi_i_t = try_vec_with_capacity(
        "hierarchical_pairwise source MI terms",
        sources.len(),
        budget,
    )?;
    for s in sources {
        mi_i_t.push(ksg_mi_with_budget(*s, target, &ksg, budget)?);
    }

    let m = sources.len();
    let pairs_cap = checked_pair_count("hierarchical_pairwise", m)?;
    let mut pairs =
        try_vec_with_capacity("hierarchical_pairwise retained pairs", pairs_cap, budget)?;
    for i in 0..m {
        for j in (i + 1)..m {
            let mi_ij_t =
                ksg_mi_concat_xy_with_budget(sources[i], sources[j], target, &ksg, budget)?;
            let co_information_nats = compensated_sum([mi_i_t[i], mi_i_t[j], -mi_ij_t]);
            pairs.push(PairwiseScreen {
                i,
                j,
                co_information_nats,
                mi_i_t: mi_i_t[i],
                mi_j_t: mi_i_t[j],
                mi_ij_t,
                pid: None,
            });
        }
    }

    Ok(pairs)
}

/// Screen one row set and evaluate selected PID2 pairs only on a distinct held-out row set.
pub fn hierarchical_pairwise_split(
    screening_sources: &[MatRef<'_>],
    screening_target: MatRef<'_>,
    evaluation_sources: &[MatRef<'_>],
    evaluation_target: MatRef<'_>,
    cfg: &HierarchicalConfig,
    split_identity: &HierarchySplitIdentity,
) -> PidResult<HierarchicalPairwiseReport> {
    hierarchical_pairwise_split_with_budget(
        screening_sources,
        screening_target,
        evaluation_sources,
        evaluation_target,
        cfg,
        split_identity,
        ResourceBudget::default(),
    )
}

/// Held-out hierarchy under an aggregate resource ceiling.
pub fn hierarchical_pairwise_split_with_budget(
    screening_sources: &[MatRef<'_>],
    screening_target: MatRef<'_>,
    evaluation_sources: &[MatRef<'_>],
    evaluation_target: MatRef<'_>,
    cfg: &HierarchicalConfig,
    split_identity: &HierarchySplitIdentity,
    budget: ResourceBudget,
) -> PidResult<HierarchicalPairwiseReport> {
    const OPERATION: &str = "hierarchical_pairwise_split";
    if !cfg.compute_pid {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "split hierarchy PID evaluation requires compute_pid=true",
        });
    }
    if screening_sources.len() != evaluation_sources.len() {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "screening and evaluation source families must have the same size and order",
        });
    }
    validate_ksg_isx_consistency(OPERATION, &cfg.ksg, &cfg.isx)?;
    let resource_estimate = hierarchical_pairwise_split_resource_estimate_for_threads(
        screening_sources,
        screening_target,
        evaluation_sources,
        evaluation_target,
        cfg,
        effective_thread_count(budget.max_threads, screening_target.nrows()),
    )?;
    budget.check(OPERATION, resource_estimate)?;

    let mut screening_hashes = try_vec_with_capacity(
        "hierarchy screening input hashes",
        screening_sources.len() + 1,
        budget,
    )?;
    screening_hashes.extend(screening_sources.iter().map(|source| hash_matrix(*source)));
    screening_hashes.push(hash_matrix(screening_target));
    let mut evaluation_hashes = try_vec_with_capacity(
        "hierarchy evaluation input hashes",
        evaluation_sources.len() + 1,
        budget,
    )?;
    evaluation_hashes.extend(evaluation_sources.iter().map(|source| hash_matrix(*source)));
    evaluation_hashes.push(hash_matrix(evaluation_target));
    if screening_hashes == evaluation_hashes {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "screening and evaluation matrices are identical; held-out evaluation requires distinct row sets",
        });
    }

    let mut screening_cfg = cfg.clone();
    screening_cfg.compute_pid = false;
    let mut pairs = hierarchical_pairwise_with_budget(
        screening_sources,
        screening_target,
        &screening_cfg,
        budget,
    )?;
    let selected = hierarchy_selection_mask(&pairs, &cfg.selection, budget)?;
    let pid_cfg = Pid2Config {
        ksg: cfg.ksg.clone(),
        isx: cfg.isx.clone(),
    };
    let mut selected_count = 0usize;
    for (index, pair) in pairs.iter_mut().enumerate() {
        if !selected[index] {
            continue;
        }
        selected_count = selected_count
            .checked_add(1)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        pair.pid = Some(pid2_isx_with_budget(
            evaluation_sources[pair.i],
            evaluation_sources[pair.j],
            evaluation_target,
            &pid_cfg,
            budget,
        )?);
    }
    let family_size = pairs.len();
    Ok(HierarchicalPairwiseReport {
        pairs,
        selection: HierarchySelectionProvenance {
            screening_split_id: try_hierarchy_text(split_identity.screening_split_id())?,
            evaluation_split_id: try_hierarchy_text(split_identity.evaluation_split_id())?,
            screening_input_hashes_sha256: screening_hashes,
            evaluation_input_hashes_sha256: evaluation_hashes,
            family_size,
            selected_count,
            selection_rule: cfg.selection.clone(),
            post_selection_p_values_provided: false,
        },
        resource_estimate,
        resource_budget: budget,
        warning: "pair selection was performed only on the screening split; held-out PID values are exploratory estimates and no post-selection p-values are supplied",
    })
}

fn hierarchy_selection_mask(
    pairs: &[PairwiseScreen],
    selection: &PairSelection,
    budget: ResourceBudget,
) -> PidResult<Vec<bool>> {
    let mut selected = try_vec_filled(
        "hierarchical pairwise selection mask",
        pairs.len(),
        false,
        budget,
    )?;
    match *selection {
        PairSelection::All => selected.fill(true),
        PairSelection::CoInformationAtOrBelow { threshold } => {
            if !threshold.is_finite() {
                return Err(PidError::InvalidConfig {
                    context: "hierarchical_pairwise_split",
                    message: "co-information threshold must be finite",
                });
            }
            for (index, pair) in pairs.iter().enumerate() {
                selected[index] = pair.co_information_nats <= threshold;
            }
        }
        PairSelection::TopKMostNegativeCoInformation { k } => {
            let mut ordering = try_vec_with_capacity(
                "hierarchical pairwise selection ordering",
                pairs.len(),
                budget,
            )?;
            ordering.extend(0..pairs.len());
            ordering.sort_unstable_by(|&left, &right| {
                pairs[left]
                    .co_information_nats
                    .total_cmp(&pairs[right].co_information_nats)
                    .then_with(|| pairs[left].i.cmp(&pairs[right].i))
                    .then_with(|| pairs[left].j.cmp(&pairs[right].j))
            });
            for &index in ordering.iter().take(k.min(ordering.len())) {
                selected[index] = true;
            }
        }
    }
    Ok(selected)
}

/// Conservative preflight for held-out pair screening and PID2 evaluation.
pub fn hierarchical_pairwise_split_resource_estimate_for_threads(
    screening_sources: &[MatRef<'_>],
    screening_target: MatRef<'_>,
    evaluation_sources: &[MatRef<'_>],
    evaluation_target: MatRef<'_>,
    cfg: &HierarchicalConfig,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "hierarchical_pairwise_split";
    if screening_sources.len() != evaluation_sources.len() || screening_sources.len() < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "screening and evaluation source families must have the same size >= 2",
        });
    }
    let mut screening_cfg = cfg.clone();
    screening_cfg.compute_pid = false;
    let mut estimate = hierarchical_pairwise_resource_estimate_for_threads(
        screening_sources,
        screening_target,
        &screening_cfg,
        max_threads,
    )?;
    if !matches!(
        cfg.selection,
        PairSelection::TopKMostNegativeCoInformation { k: 0 }
    ) {
        let pid_cfg = Pid2Config {
            ksg: cfg.ksg.clone(),
            isx: cfg.isx.clone(),
        };
        let mut evaluation_peak_bytes = 0u128;
        // Selection scores are not available during preflight. Account every possible selected
        // pair; this is conservative for thresholds and top-k rules and prevents under-budgeting.
        for i in 0..evaluation_sources.len() {
            for j in (i + 1)..evaluation_sources.len() {
                let pair = pid2_resource_estimate_for_threads(
                    evaluation_sources[i],
                    evaluation_sources[j],
                    evaluation_target,
                    &pid_cfg,
                    max_threads,
                )?;
                evaluation_peak_bytes = evaluation_peak_bytes.max(pair.estimated_bytes);
                estimate.pairwise_distances = estimate
                    .pairwise_distances
                    .checked_add(pair.pairwise_distances)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
                estimate.operations_hint = estimate
                    .operations_hint
                    .checked_add(pair.operations_hint)
                    .ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })?;
            }
        }
        estimate.estimated_bytes = estimate
            .estimated_bytes
            .checked_add(evaluation_peak_bytes)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
    }
    let hash_count = screening_sources
        .len()
        .checked_add(evaluation_sources.len())
        .and_then(|value| value.checked_add(2))
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(
            (hash_count as u128)
                .checked_mul(std::mem::size_of::<[u8; 32]>() as u128)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        )
        .and_then(|value| {
            value.checked_add(std::mem::size_of::<HierarchicalPairwiseReport>() as u128)
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let hashed_elements = screening_sources
        .iter()
        .chain(evaluation_sources)
        .map(|matrix| matrix.as_slice().len() as u128)
        .chain([
            screening_target.as_slice().len() as u128,
            evaluation_target.as_slice().len() as u128,
        ])
        .try_fold(0u128, |total, value| {
            total.checked_add(value).ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })
        })?;
    estimate.operations_hint = estimate
        .operations_hint
        .checked_add(hashed_elements)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(estimate)
}

/// Same-sample pairwise and triplet co-information screening for three sources and one target.
///
/// This is a screening diagnostic, not a PID decomposition. Same-sample PID2/PID3 evaluation is
/// rejected; use the split pairwise API or a separately declared held-out PID3 workflow.
pub fn hierarchical_triplet(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<HierarchicalTriplet> {
    hierarchical_triplet_with_budget(x, y, z, t, cfg, ResourceBudget::default())
}

/// Three-source hierarchy under an aggregate resource budget.
pub fn hierarchical_triplet_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &HierarchicalConfig,
    budget: ResourceBudget,
) -> PidResult<HierarchicalTriplet> {
    let sources = [x, y, z];
    let threads = effective_thread_count(budget.max_threads, t.nrows());
    let resource_estimate =
        hierarchical_triplet_resource_estimate_for_threads(x, y, z, t, cfg, threads)?;
    budget.check("hierarchical_triplet", resource_estimate)?;
    let pairwise = hierarchical_pairwise_with_budget(&sources, t, cfg, budget)?;

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

    // Same convention as `hierarchical_pairwise`: this MI feeds the CoI(X,Y,Z;T) alternating
    // sum, so it must be unclamped.
    let ksg = KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.ksg.clone()
    };
    let mi_xyz_t = ksg_mi_xblocks_with_budget(&sources, t, &ksg, budget)?;
    let mi01 = mi01.ok_or(PidError::InvalidConfig {
        context: "hierarchical_triplet",
        message: "missing pair (0,1)",
    })?;
    let mi02 = mi02.ok_or(PidError::InvalidConfig {
        context: "hierarchical_triplet",
        message: "missing pair (0,2)",
    })?;
    let mi12 = mi12.ok_or(PidError::InvalidConfig {
        context: "hierarchical_triplet",
        message: "missing pair (1,2)",
    })?;
    let triplet_co_information_nats = compensated_sum([
        mi_i_t[0], mi_i_t[1], mi_i_t[2], -mi01, -mi02, -mi12, mi_xyz_t,
    ]);

    Ok(HierarchicalTriplet {
        pairwise,
        triplet_co_information_nats,
        mi_xyz_t,
    })
}

/// Preflight pair enumeration, retained screens, and every selected estimator pass.
pub fn hierarchical_pairwise_resource_estimate(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<ResourceEstimate> {
    hierarchical_pairwise_resource_estimate_for_threads(
        sources,
        target,
        cfg,
        effective_thread_count(ResourceBudget::default().max_threads, target.nrows()),
    )
}

/// Pairwise hierarchy preflight including per-worker scratch and stack reservations.
pub fn hierarchical_pairwise_resource_estimate_for_threads(
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &HierarchicalConfig,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "hierarchical_pairwise";
    if cfg.compute_pid {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "same-sample screening and PID evaluation is disabled; use hierarchical_pairwise_split_with_budget",
        });
    }
    if max_threads == 0 {
        return Err(PidError::ResourceLimitExceeded {
            operation: OPERATION,
            resource: "threads",
            requested: 1,
            limit: 0,
        });
    }
    if sources.len() < 2 {
        return Err(PidError::InvalidConfig {
            context: OPERATION,
            message: "need at least 2 sources",
        });
    }
    let pair_count = checked_pair_count(OPERATION, sources.len())?;
    let mut aggregate = ResourceEstimate::ZERO;
    for source in sources {
        accumulate_sequential(
            OPERATION,
            &mut aggregate,
            ksg_resource_estimate_for_threads(*source, target, max_threads)?,
        )?;
    }
    for i in 0..sources.len() {
        for j in (i + 1)..sources.len() {
            accumulate_sequential(
                OPERATION,
                &mut aggregate,
                ksg_xblocks_resource_estimate(&[sources[i], sources[j]], target, max_threads)?,
            )?;
        }
    }
    let selection_element_bytes = 0;
    let retained_bytes = (sources.len() as u128)
        .checked_mul(std::mem::size_of::<f64>() as u128)
        .and_then(|value| {
            value.checked_add((pair_count as u128).checked_mul(
                (std::mem::size_of::<PairwiseScreen>() + selection_element_bytes) as u128,
            )?)
        })
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.estimated_bytes = aggregate
        .estimated_bytes
        .checked_add(retained_bytes)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.operations_hint = aggregate
        .operations_hint
        .checked_add(
            (pair_count as u128)
                .checked_mul(8)
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        )
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(aggregate)
}

/// Preflight the complete three-source co-information hierarchy.
pub fn hierarchical_triplet_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &HierarchicalConfig,
) -> PidResult<ResourceEstimate> {
    hierarchical_triplet_resource_estimate_for_threads(
        x,
        y,
        z,
        t,
        cfg,
        effective_thread_count(ResourceBudget::default().max_threads, t.nrows()),
    )
}

/// Triplet hierarchy preflight including explicit per-worker reservations.
pub fn hierarchical_triplet_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &HierarchicalConfig,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "hierarchical_triplet";
    let mut aggregate =
        hierarchical_pairwise_resource_estimate_for_threads(&[x, y, z], t, cfg, max_threads)?;
    let joint = ksg_xblocks_resource_estimate(&[x, y, z], t, max_threads)?;
    aggregate.estimated_bytes = aggregate
        .estimated_bytes
        .checked_add(joint.estimated_bytes)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.pairwise_distances = aggregate
        .pairwise_distances
        .checked_add(joint.pairwise_distances)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    aggregate.operations_hint = aggregate
        .operations_hint
        .checked_add(joint.operations_hint)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(aggregate)
}

fn checked_pair_count(operation: &'static str, count: usize) -> PidResult<usize> {
    let pairs = (count as u128)
        .checked_mul(count.saturating_sub(1) as u128)
        .and_then(|value| value.checked_div(2))
        .ok_or(PidError::SizeOverflow { operation })?;
    usize::try_from(pairs).map_err(|_| PidError::SizeOverflow { operation })
}

fn accumulate_sequential(
    operation: &'static str,
    aggregate: &mut ResourceEstimate,
    next: ResourceEstimate,
) -> PidResult<()> {
    aggregate.estimated_bytes = aggregate.estimated_bytes.max(next.estimated_bytes);
    aggregate.pairwise_distances = aggregate
        .pairwise_distances
        .checked_add(next.pairwise_distances)
        .ok_or(PidError::SizeOverflow { operation })?;
    aggregate.operations_hint = aggregate
        .operations_hint
        .checked_add(next.operations_hint)
        .ok_or(PidError::SizeOverflow { operation })?;
    Ok(())
}
