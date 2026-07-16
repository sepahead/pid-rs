//! Continuous co-information from alternating sums of KSG mutual-information estimates.
//!
//! # Method provenance and availability
//!
//! **PAPER-DEFINED INVARIANT / PAPER-DERIVED ESTIMATOR.** This module uses Bell's co-information
//! sign convention and estimates it by composing KSG terms. For three variables,
//! `CoI(X,Y;T) = I(X;Y) - I(X;Y|T)`; literature using McGill's historical interaction-information
//! convention may use the opposite sign. The report-first API, cancellation diagnostics, and
//! interpretation warnings are project-defined. It is available under `experimental-continuous`
//! and is not a PID decomposition.
//!
//! Method catalog: co-information.continuous-report
//!
//! **PAPER-DERIVED RESEARCH API.** Raw alternating-sum functions expose the same KSG composition
//! without complete constituent reports. They are available under `experimental-continuous` and
//! retain the conditioning and support limitations of every KSG term.
//!
//! Method catalog: co-information.continuous-raw

use serde::Serialize;

use crate::error::{PidError, PidResult};
use crate::ksg::{
    effective_thread_count, ksg_mi_concat_xy_with_budget, ksg_mi_report_with_budget,
    ksg_mi_with_budget, ksg_mi_xblocks_with_budget, ksg_report_resource_estimate,
    ksg_resource_estimate_for_threads, ksg_xblocks_report_resource_estimate,
    ksg_xblocks_resource_estimate, KsgConfig, KsgMiReport, KsgProvenance, NegativeHandling,
};
use crate::matrix::{concat_horiz_with_budget, MatRef};
use crate::resource::{ResourceBudget, ResourceEstimate};
use crate::stats::compensated_sum;
use crate::support::validate_support_contract;

/// Conditioning state for an alternating co-information sum.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum CoInformationConditioningStatus {
    Finite,
    AllTermsZero,
    ExactCancellation,
    AmplificationExceedsF64Range,
}

/// Scale-aware cancellation diagnostic for a co-information estimate.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct CoInformationCancellationDiagnostics {
    pub value_nats: f64,
    pub absolute_signed_term_sum_nats: f64,
    pub retained_fraction: Option<f64>,
    pub amplification_factor: Option<f64>,
    pub status: CoInformationConditioningStatus,
}

/// Interpretation warnings that must travel with a continuous co-information report.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub enum CoInformationReportWarning {
    /// Co-information is a Shannon invariant, not a PID atom or decomposition.
    NotAPidDecomposition,
    /// Ranking extrema and evaluating them on the same observations creates selection bias.
    SameSampleExtremumSelectionIsBiased,
    /// Triplet signs do not have the pairwise redundancy-minus-synergy interpretation.
    TripletSignIsParityDependent,
}

/// Report-first pairwise co-information with every KSG constituent retained.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct PairwiseCoInformationReport {
    pub co_information_nats: f64,
    pub signed_term_order: [&'static str; 3],
    pub signed_terms_nats: [f64; 3],
    pub x_target_report: KsgMiReport,
    pub y_target_report: KsgMiReport,
    pub joint_xy_target_report: KsgMiReport,
    pub cancellation: CoInformationCancellationDiagnostics,
    pub warnings: [CoInformationReportWarning; 2],
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

/// Report-first triplet interaction/co-information with all seven KSG constituents retained.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct TripletCoInformationReport {
    pub co_information_nats: f64,
    pub signed_term_order: [&'static str; 7],
    pub signed_terms_nats: [f64; 7],
    pub x_target_report: KsgMiReport,
    pub y_target_report: KsgMiReport,
    pub z_target_report: KsgMiReport,
    pub joint_xy_target_report: KsgMiReport,
    pub joint_xz_target_report: KsgMiReport,
    pub joint_yz_target_report: KsgMiReport,
    pub joint_xyz_target_report: KsgMiReport,
    pub cancellation: CoInformationCancellationDiagnostics,
    pub warnings: [CoInformationReportWarning; 3],
    pub resource_estimate: ResourceEstimate,
    pub resource_budget: ResourceBudget,
}

/// Pairwise co-information with complete constituent reports and cancellation diagnostics.
pub fn co_information_pairwise_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    target: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<PairwiseCoInformationReport> {
    co_information_pairwise_report_with_budget(
        x,
        y,
        target,
        cfg,
        provenance,
        ResourceBudget::default(),
    )
}

/// Pairwise co-information report under an aggregate resource ceiling.
pub fn co_information_pairwise_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    target: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<PairwiseCoInformationReport> {
    validate_co_information_inputs("co_information_pairwise_report", &[x, y], target, cfg)?;
    let threads = effective_thread_count(budget.max_threads, target.nrows());
    let resource_estimate = co_information_pairwise_report_resource_estimate_for_threads(
        x, y, target, provenance, threads,
    )?;
    budget.check("co_information_pairwise_report", resource_estimate)?;
    let report_cfg = cfg.clone().with_negative_handling(NegativeHandling::Allow);
    let x_target_report = ksg_mi_report_with_budget(x, target, &report_cfg, provenance, budget)?;
    let y_target_report = ksg_mi_report_with_budget(y, target, &report_cfg, provenance, budget)?;
    let joined = concat_horiz_with_budget(x, y, budget)?;
    let joint_xy_target_report =
        ksg_mi_report_with_budget(joined.as_ref(), target, &report_cfg, provenance, budget)?;
    let signed_terms_nats = [
        x_target_report.estimate_nats,
        y_target_report.estimate_nats,
        -joint_xy_target_report.estimate_nats,
    ];
    let co_information_nats = compensated_sum(signed_terms_nats);
    let cancellation = co_information_cancellation(co_information_nats, &signed_terms_nats)?;
    Ok(PairwiseCoInformationReport {
        co_information_nats,
        signed_term_order: ["I(X;T)", "I(Y;T)", "-I((X,Y);T)"],
        signed_terms_nats,
        x_target_report,
        y_target_report,
        joint_xy_target_report,
        cancellation,
        warnings: [
            CoInformationReportWarning::NotAPidDecomposition,
            CoInformationReportWarning::SameSampleExtremumSelectionIsBiased,
        ],
        resource_estimate,
        resource_budget: budget,
    })
}

/// Triplet interaction/co-information with all seven constituent reports retained.
pub fn co_information_triplet_report(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    target: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
) -> PidResult<TripletCoInformationReport> {
    co_information_triplet_report_with_budget(
        x,
        y,
        z,
        target,
        cfg,
        provenance,
        ResourceBudget::default(),
    )
}

/// Triplet co-information report under an aggregate resource ceiling.
pub fn co_information_triplet_report_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    target: MatRef<'_>,
    cfg: &KsgConfig,
    provenance: &KsgProvenance,
    budget: ResourceBudget,
) -> PidResult<TripletCoInformationReport> {
    validate_co_information_inputs("co_information_triplet_report", &[x, y, z], target, cfg)?;
    let threads = effective_thread_count(budget.max_threads, target.nrows());
    let resource_estimate = co_information_triplet_report_resource_estimate_for_threads(
        x, y, z, target, provenance, threads,
    )?;
    budget.check("co_information_triplet_report", resource_estimate)?;
    let report_cfg = cfg.clone().with_negative_handling(NegativeHandling::Allow);
    let x_target_report = ksg_mi_report_with_budget(x, target, &report_cfg, provenance, budget)?;
    let y_target_report = ksg_mi_report_with_budget(y, target, &report_cfg, provenance, budget)?;
    let z_target_report = ksg_mi_report_with_budget(z, target, &report_cfg, provenance, budget)?;

    let xy = concat_horiz_with_budget(x, y, budget)?;
    let joint_xy_target_report =
        ksg_mi_report_with_budget(xy.as_ref(), target, &report_cfg, provenance, budget)?;
    drop(xy);
    let xz = concat_horiz_with_budget(x, z, budget)?;
    let joint_xz_target_report =
        ksg_mi_report_with_budget(xz.as_ref(), target, &report_cfg, provenance, budget)?;
    drop(xz);
    let yz = concat_horiz_with_budget(y, z, budget)?;
    let joint_yz_target_report =
        ksg_mi_report_with_budget(yz.as_ref(), target, &report_cfg, provenance, budget)?;
    drop(yz);
    let xy = concat_horiz_with_budget(x, y, budget)?;
    let xyz = concat_horiz_with_budget(xy.as_ref(), z, budget)?;
    let joint_xyz_target_report =
        ksg_mi_report_with_budget(xyz.as_ref(), target, &report_cfg, provenance, budget)?;

    let signed_terms_nats = [
        x_target_report.estimate_nats,
        y_target_report.estimate_nats,
        z_target_report.estimate_nats,
        -joint_xy_target_report.estimate_nats,
        -joint_xz_target_report.estimate_nats,
        -joint_yz_target_report.estimate_nats,
        joint_xyz_target_report.estimate_nats,
    ];
    let co_information_nats = compensated_sum(signed_terms_nats);
    let cancellation = co_information_cancellation(co_information_nats, &signed_terms_nats)?;
    Ok(TripletCoInformationReport {
        co_information_nats,
        signed_term_order: [
            "I(X;T)",
            "I(Y;T)",
            "I(Z;T)",
            "-I((X,Y);T)",
            "-I((X,Z);T)",
            "-I((Y,Z);T)",
            "I((X,Y,Z);T)",
        ],
        signed_terms_nats,
        x_target_report,
        y_target_report,
        z_target_report,
        joint_xy_target_report,
        joint_xz_target_report,
        joint_yz_target_report,
        joint_xyz_target_report,
        cancellation,
        warnings: [
            CoInformationReportWarning::NotAPidDecomposition,
            CoInformationReportWarning::SameSampleExtremumSelectionIsBiased,
            CoInformationReportWarning::TripletSignIsParityDependent,
        ],
        resource_estimate,
        resource_budget: budget,
    })
}

/// Pairwise co-information (a Shannon invariant) computed via KSG MI estimates:
///
/// CoI(X,Y;T) = I(X;T) + I(Y;T) - I((X,Y);T)
///
/// This is Bell's co-information sign convention:
/// `CoI(X,Y;T) = I(X;Y) - I(X;Y|T)`. McGill-style interaction information is also written with
/// the opposite sign in the literature, so callers should compare formulas rather than names.
///
/// Sign convention (2 sources): `CoI = Red − Syn`, so **negative** co-information indicates net
/// synergy and **positive** indicates net redundancy.
pub fn co_information_pairwise(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    co_information_pairwise_with_budget(x, y, t, cfg, ResourceBudget::default())
}

/// Pairwise co-information under an explicit aggregate resource budget.
pub fn co_information_pairwise_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    validate_co_information_inputs("co_information_pairwise", &[x, y], t, cfg)?;
    let threads = effective_thread_count(budget.max_threads, t.nrows());
    let estimate = co_information_pairwise_resource_estimate_for_threads(x, y, t, threads)?;
    budget.check("co_information_pairwise", estimate)?;
    // Co-information requires unclamped cancellation of the MI terms; force `Allow`.
    let cfg = &KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.clone()
    };
    let i_xt = ksg_mi_with_budget(x, t, cfg, budget)?;
    let i_yt = ksg_mi_with_budget(y, t, cfg, budget)?;
    let i_xyt = ksg_mi_concat_xy_with_budget(x, y, t, cfg, budget)?;
    Ok(compensated_sum([i_xt, i_yt, -i_xyt]))
}

/// 3-source co-information (interaction information / Shannon invariant) computed via KSG MI estimates:
///
/// CoI(X,Y,Z;T) = I(X;T)+I(Y;T)+I(Z;T)
///              - I(X,Y;T) - I(X,Z;T) - I(Y,Z;T)
///              + I(X,Y,Z;T)
///
/// Sign interpretation is **parity-flipped** vs. the 2-source case and is *not* a clean
/// synergy/redundancy indicator: a pure 3-way synergy (`T = X⊕Y⊕Z`) gives `CoI > 0`, and at
/// 3 sources co-information conflates redundancy and synergy. Use it only as a coarse screen, not
/// a verdict.
pub fn co_information_triplet(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<f64> {
    co_information_triplet_with_budget(x, y, z, t, cfg, ResourceBudget::default())
}

/// Triplet co-information under an explicit aggregate resource budget.
pub fn co_information_triplet_with_budget(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    cfg: &KsgConfig,
    budget: ResourceBudget,
) -> PidResult<f64> {
    validate_co_information_inputs("co_information_triplet", &[x, y, z], t, cfg)?;
    let threads = effective_thread_count(budget.max_threads, t.nrows());
    let estimate = co_information_triplet_resource_estimate_for_threads(x, y, z, t, threads)?;
    budget.check("co_information_triplet", estimate)?;
    // Co-information requires unclamped cancellation of the MI terms; force `Allow`.
    let cfg = &KsgConfig {
        negative_handling: NegativeHandling::Allow,
        ..cfg.clone()
    };
    let i_xt = ksg_mi_with_budget(x, t, cfg, budget)?;
    let i_yt = ksg_mi_with_budget(y, t, cfg, budget)?;
    let i_zt = ksg_mi_with_budget(z, t, cfg, budget)?;

    let i_xyt = ksg_mi_concat_xy_with_budget(x, y, t, cfg, budget)?;
    let i_xzt = ksg_mi_concat_xy_with_budget(x, z, t, cfg, budget)?;
    let i_yzt = ksg_mi_concat_xy_with_budget(y, z, t, cfg, budget)?;

    let i_xyzt = ksg_mi_xblocks_with_budget(&[x, y, z], t, cfg, budget)?;

    Ok(compensated_sum([
        i_xt, i_yt, i_zt, -i_xyt, -i_xzt, -i_yzt, i_xyzt,
    ]))
}

/// Aggregate resource estimate for all three pairwise co-information MI terms.
pub fn co_information_pairwise_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    co_information_pairwise_resource_estimate_for_threads(
        x,
        y,
        t,
        effective_thread_count(ResourceBudget::default().max_threads, t.nrows()),
    )
}

/// Pairwise co-information preflight including per-worker scratch and stack reservations.
pub fn co_information_pairwise_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    t: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    combine_sequential_estimates(
        "co_information_pairwise",
        &[
            ksg_resource_estimate_for_threads(x, t, max_threads)?,
            ksg_resource_estimate_for_threads(y, t, max_threads)?,
            ksg_xblocks_resource_estimate(&[x, y], t, max_threads)?,
        ],
    )
}

/// Aggregate resource estimate for all seven triplet co-information MI terms.
pub fn co_information_triplet_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
) -> PidResult<ResourceEstimate> {
    co_information_triplet_resource_estimate_for_threads(
        x,
        y,
        z,
        t,
        effective_thread_count(ResourceBudget::default().max_threads, t.nrows()),
    )
}

/// Triplet co-information preflight including per-worker scratch and stack reservations.
pub fn co_information_triplet_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    t: MatRef<'_>,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    combine_sequential_estimates(
        "co_information_triplet",
        &[
            ksg_resource_estimate_for_threads(x, t, max_threads)?,
            ksg_resource_estimate_for_threads(y, t, max_threads)?,
            ksg_resource_estimate_for_threads(z, t, max_threads)?,
            ksg_xblocks_resource_estimate(&[x, y], t, max_threads)?,
            ksg_xblocks_resource_estimate(&[x, z], t, max_threads)?,
            ksg_xblocks_resource_estimate(&[y, z], t, max_threads)?,
            ksg_xblocks_resource_estimate(&[x, y, z], t, max_threads)?,
        ],
    )
}

/// Aggregate preflight for the complete pairwise report.
pub fn co_information_pairwise_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &KsgProvenance,
) -> PidResult<ResourceEstimate> {
    co_information_pairwise_report_resource_estimate_for_threads(
        x,
        y,
        target,
        provenance,
        effective_thread_count(ResourceBudget::default().max_threads, target.nrows()),
    )
}

/// Pairwise report preflight including every retained constituent and explicit concatenation.
pub fn co_information_pairwise_report_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    let mut estimate = combine_retained_report_estimates(
        "co_information_pairwise_report",
        &[
            ksg_report_resource_estimate(x, target, provenance, max_threads)?,
            ksg_report_resource_estimate(y, target, provenance, max_threads)?,
            ksg_xblocks_report_resource_estimate(&[x, y], target, provenance, max_threads)?,
        ],
    )?;
    let joined_columns = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: "co_information_pairwise_report",
        })?;
    add_concat_workspace(
        "co_information_pairwise_report",
        &mut estimate,
        target.nrows(),
        joined_columns,
    )?;
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(std::mem::size_of::<PairwiseCoInformationReport>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: "co_information_pairwise_report",
        })?;
    Ok(estimate)
}

/// Aggregate preflight for the complete seven-term triplet report.
pub fn co_information_triplet_report_resource_estimate(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &KsgProvenance,
) -> PidResult<ResourceEstimate> {
    co_information_triplet_report_resource_estimate_for_threads(
        x,
        y,
        z,
        target,
        provenance,
        effective_thread_count(ResourceBudget::default().max_threads, target.nrows()),
    )
}

/// Triplet report preflight including all retained reports and explicit joined matrices.
pub fn co_information_triplet_report_resource_estimate_for_threads(
    x: MatRef<'_>,
    y: MatRef<'_>,
    z: MatRef<'_>,
    target: MatRef<'_>,
    provenance: &KsgProvenance,
    max_threads: usize,
) -> PidResult<ResourceEstimate> {
    const OPERATION: &str = "co_information_triplet_report";
    let mut estimate = combine_retained_report_estimates(
        OPERATION,
        &[
            ksg_report_resource_estimate(x, target, provenance, max_threads)?,
            ksg_report_resource_estimate(y, target, provenance, max_threads)?,
            ksg_report_resource_estimate(z, target, provenance, max_threads)?,
            ksg_xblocks_report_resource_estimate(&[x, y], target, provenance, max_threads)?,
            ksg_xblocks_report_resource_estimate(&[x, z], target, provenance, max_threads)?,
            ksg_xblocks_report_resource_estimate(&[y, z], target, provenance, max_threads)?,
            ksg_xblocks_report_resource_estimate(&[x, y, z], target, provenance, max_threads)?,
        ],
    )?;
    let xy = x
        .ncols()
        .checked_add(y.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let xz = x
        .ncols()
        .checked_add(z.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let yz = y
        .ncols()
        .checked_add(z.ncols())
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    let xyz = xy.checked_add(z.ncols()).ok_or(PidError::SizeOverflow {
        operation: OPERATION,
    })?;
    // `xy` is allocated twice: once for its own report and once as the input to `xyz`.
    for columns in [xy, xz, yz, xy, xyz] {
        add_concat_workspace(OPERATION, &mut estimate, target.nrows(), columns)?;
    }
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(std::mem::size_of::<TripletCoInformationReport>() as u128)
        .ok_or(PidError::SizeOverflow {
            operation: OPERATION,
        })?;
    Ok(estimate)
}

fn combine_retained_report_estimates(
    operation: &'static str,
    estimates: &[ResourceEstimate],
) -> PidResult<ResourceEstimate> {
    let mut aggregate = ResourceEstimate::ZERO;
    for estimate in estimates {
        aggregate.estimated_bytes = aggregate
            .estimated_bytes
            .checked_add(estimate.estimated_bytes)
            .ok_or(PidError::SizeOverflow { operation })?;
        aggregate.pairwise_distances = aggregate
            .pairwise_distances
            .checked_add(estimate.pairwise_distances)
            .ok_or(PidError::SizeOverflow { operation })?;
        aggregate.operations_hint = aggregate
            .operations_hint
            .checked_add(estimate.operations_hint)
            .ok_or(PidError::SizeOverflow { operation })?;
    }
    Ok(aggregate)
}

fn add_concat_workspace(
    operation: &'static str,
    estimate: &mut ResourceEstimate,
    rows: usize,
    columns: usize,
) -> PidResult<()> {
    let elements = (rows as u128)
        .checked_mul(columns as u128)
        .ok_or(PidError::SizeOverflow { operation })?;
    let bytes = elements
        .checked_mul(std::mem::size_of::<f64>() as u128)
        .ok_or(PidError::SizeOverflow { operation })?;
    estimate.estimated_bytes = estimate
        .estimated_bytes
        .checked_add(bytes)
        .ok_or(PidError::SizeOverflow { operation })?;
    estimate.operations_hint = estimate
        .operations_hint
        .checked_add(elements)
        .ok_or(PidError::SizeOverflow { operation })?;
    Ok(())
}

fn co_information_cancellation(
    value_nats: f64,
    signed_terms: &[f64],
) -> PidResult<CoInformationCancellationDiagnostics> {
    if !value_nats.is_finite() || signed_terms.iter().any(|value| !value.is_finite()) {
        return Err(PidError::NumericalInstability {
            context: "co-information cancellation diagnostics",
        });
    }
    let absolute_signed_term_sum_nats = compensated_sum(signed_terms.iter().map(|v| v.abs()));
    if !absolute_signed_term_sum_nats.is_finite() {
        return Err(PidError::NumericalInstability {
            context: "co-information cancellation scale",
        });
    }
    if absolute_signed_term_sum_nats == 0.0 {
        return Ok(CoInformationCancellationDiagnostics {
            value_nats,
            absolute_signed_term_sum_nats,
            retained_fraction: None,
            amplification_factor: None,
            status: CoInformationConditioningStatus::AllTermsZero,
        });
    }
    let retained_fraction = value_nats.abs() / absolute_signed_term_sum_nats;
    if value_nats == 0.0 {
        return Ok(CoInformationCancellationDiagnostics {
            value_nats,
            absolute_signed_term_sum_nats,
            retained_fraction: Some(0.0),
            amplification_factor: None,
            status: CoInformationConditioningStatus::ExactCancellation,
        });
    }
    let amplification_factor = absolute_signed_term_sum_nats / value_nats.abs();
    let (amplification_factor, status) = if amplification_factor.is_finite() {
        (
            Some(amplification_factor),
            CoInformationConditioningStatus::Finite,
        )
    } else {
        (
            None,
            CoInformationConditioningStatus::AmplificationExceedsF64Range,
        )
    };
    Ok(CoInformationCancellationDiagnostics {
        value_nats,
        absolute_signed_term_sum_nats,
        retained_fraction: Some(retained_fraction),
        amplification_factor,
        status,
    })
}

fn combine_sequential_estimates(
    operation: &'static str,
    estimates: &[ResourceEstimate],
) -> PidResult<ResourceEstimate> {
    let mut aggregate = ResourceEstimate::ZERO;
    for estimate in estimates {
        aggregate.estimated_bytes = aggregate.estimated_bytes.max(estimate.estimated_bytes);
        aggregate.pairwise_distances = aggregate
            .pairwise_distances
            .checked_add(estimate.pairwise_distances)
            .ok_or(PidError::SizeOverflow { operation })?;
        aggregate.operations_hint = aggregate
            .operations_hint
            .checked_add(estimate.operations_hint)
            .ok_or(PidError::SizeOverflow { operation })?;
    }
    Ok(aggregate)
}

fn validate_co_information_inputs(
    context: &'static str,
    sources: &[MatRef<'_>],
    target: MatRef<'_>,
    cfg: &KsgConfig,
) -> PidResult<()> {
    for source in sources {
        if source.nrows() != target.nrows() {
            return Err(PidError::RowCountMismatch {
                context,
                left_rows: target.nrows(),
                right_rows: source.nrows(),
            });
        }
        if source.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context,
                message: "sources must have at least one column",
            });
        }
    }
    if target.ncols() == 0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "target must have at least one column",
        });
    }
    if cfg.k == 0 || target.nrows() <= cfg.k {
        return Err(PidError::InvalidK {
            k: cfg.k,
            n_samples: target.nrows(),
        });
    }
    if cfg.tie_epsilon != 0.0 {
        return Err(PidError::InvalidConfig {
            context,
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        });
    }
    if cfg.metric != crate::metric::Metric::Chebyshev {
        return Err(PidError::InvalidConfig {
            context,
            message:
                "continuous co-information concatenation is defined only for Metric::Chebyshev (L∞)",
        });
    }
    validate_support_contract(context, cfg.support_contract, cfg.metric)
}
