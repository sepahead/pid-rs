#[cfg(feature = "experimental-hyperbolic")]
use pid_core::experimental::hyperbolic::{
    hyperbolic_ksg_k_trajectory, hyperbolic_ksg_mi_report, hyperbolic_ksg_mi_report_with_budget,
    hyperbolic_ksg_report_resource_estimate, hyperbolic_ksg_sample_size_trajectory,
    HyperbolicCurvature, HyperbolicKsgConfig, HyperbolicKsgGeometryModel,
    HyperbolicKsgReportWarning, HyperbolicMetric,
};
#[cfg(feature = "experimental-hyperbolic")]
use pid_core::stable::continuous::ksg_report_resource_estimate;
use pid_core::stable::continuous::{
    ksg_mi_report, ksg_mi_report_with_budget, ksg_mi_report_with_budget_and_cancellation,
    Assumption, AssumptionState, KsgConfig, KsgGeometryModel, KsgMethodStatus, KsgNeighborBackend,
    KsgProvenance, KsgReportWarning, NegativeHandling, SupportContract,
};
use pid_core::{CancellationToken, MatRef, Metric, PidError, ResourceBudget};

#[cfg(feature = "experimental-hyperbolic")]
const HYPERBOLIC_CURVATURE: HyperbolicCurvature = HyperbolicCurvature::NegativeOne;

struct Rng(u64);

impl Rng {
    fn next_f64(&mut self) -> f64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        (x.wrapping_mul(0x2545_F491_4F6C_DD1D) >> 11) as f64 / (1_u64 << 53) as f64
    }
}

fn euclidean_data(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut rng = Rng(0xC0DE_5EED_1234_5678);
    let mut x = Vec::with_capacity(2 * n);
    let mut y = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.next_f64();
        let b = rng.next_f64();
        x.extend_from_slice(&[a, b]);
        y.push(0.3 * a + 0.2 * b + rng.next_f64());
    }
    (x, y)
}

#[test]
fn report_cancellation_is_preemptive_and_preserves_uncancelled_bits() {
    let n = 64;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();
    let budget = ResourceBudget::default();
    let baseline = ksg_mi_report_with_budget(x, y, &config, &provenance, budget).unwrap();
    let running = CancellationToken::new();
    let cancellable =
        ksg_mi_report_with_budget_and_cancellation(x, y, &config, &provenance, budget, &running)
            .unwrap();
    assert_eq!(baseline, cancellable);

    let cancelled = CancellationToken::new();
    cancelled.cancel();
    let error =
        ksg_mi_report_with_budget_and_cancellation(x, y, &config, &provenance, budget, &cancelled)
            .unwrap_err();
    assert!(matches!(error, PidError::Cancelled { .. }));
}

#[cfg(feature = "experimental-hyperbolic")]
fn hyperbolic_data(n: usize) -> (Vec<f64>, Vec<f64>) {
    let mut rng = Rng(0xA11C_E5E5_7788_9900);
    let mut x = Vec::with_capacity(2 * n);
    let mut y = Vec::with_capacity(3 * n);
    for _ in 0..n {
        let x1 = 1.4 * rng.next_f64() - 0.7;
        x.extend_from_slice(&[x1.hypot(1.0), x1]);

        let y1 = 1.2 * rng.next_f64() - 0.6;
        let y2 = 1.2 * rng.next_f64() - 0.6;
        y.extend_from_slice(&[y1.hypot(y2).hypot(1.0), y1, y2]);
    }
    (x, y)
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_preflight_accounts_for_the_typed_wrapper() {
    let n = 24;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let estimate = hyperbolic_ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    let chebyshev_estimate = ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    assert!(estimate.operations_hint > chebyshev_estimate.operations_hint);
    let exact_budget = ResourceBudget::new(
        estimate.estimated_bytes.try_into().unwrap(),
        estimate.pairwise_distances.try_into().unwrap(),
        estimate.operations_hint,
        1,
    )
    .unwrap();

    let report =
        hyperbolic_ksg_mi_report_with_budget(x, y, &cfg, &provenance, exact_budget).unwrap();
    assert_eq!(report.resource_estimate, estimate);
    assert_eq!(report.resource_budget, exact_budget);

    let one_byte_short = ResourceBudget::new(
        exact_budget.max_bytes - 1,
        exact_budget.max_pairwise_distances,
        exact_budget.max_operations_hint,
        exact_budget.max_threads,
    )
    .unwrap();
    assert!(matches!(
        hyperbolic_ksg_mi_report_with_budget(x, y, &cfg, &provenance, one_byte_short),
        Err(PidError::ResourceLimitExceeded {
            operation: "hyperbolic_ksg_mi_report",
            resource: "bytes",
            requested,
            limit,
        }) if requested == estimate.estimated_bytes && limit == estimate.estimated_bytes - 1
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_trajectory_preflights_sum_typed_report_estimates() {
    let n = 24;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();

    let one = hyperbolic_ksg_report_resource_estimate(x, y, &provenance, 1).unwrap();
    let k_budget = ResourceBudget::new(
        (one.estimated_bytes * 2).try_into().unwrap(),
        (one.pairwise_distances * 2).try_into().unwrap(),
        one.operations_hint * 2,
        1,
    )
    .unwrap();
    let k_trajectory =
        hyperbolic_ksg_k_trajectory(x, y, &[2, 3], &cfg, &provenance, k_budget).unwrap();
    assert_eq!(
        k_trajectory.aggregate_resource_estimate.estimated_bytes,
        one.estimated_bytes * 2
    );

    let prefix_n = 12;
    let x_prefix = MatRef::new(&x_data[..prefix_n * 2], prefix_n, 2).unwrap();
    let y_prefix = MatRef::new(&y_data[..prefix_n * 3], prefix_n, 3).unwrap();
    let prefix =
        hyperbolic_ksg_report_resource_estimate(x_prefix, y_prefix, &provenance, 1).unwrap();
    let sample_budget = ResourceBudget::new(
        (prefix.estimated_bytes + one.estimated_bytes)
            .try_into()
            .unwrap(),
        (prefix.pairwise_distances + one.pairwise_distances)
            .try_into()
            .unwrap(),
        prefix.operations_hint + one.operations_hint,
        1,
    )
    .unwrap();
    let sample_trajectory = hyperbolic_ksg_sample_size_trajectory(
        x,
        y,
        &[prefix_n, n],
        &cfg,
        &provenance,
        sample_budget,
    )
    .unwrap();
    assert_eq!(
        sample_trajectory
            .aggregate_resource_estimate
            .estimated_bytes,
        prefix.estimated_bytes + one.estimated_bytes
    );
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_k_trajectory_validates_every_k_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_k_trajectory(x, y, &[2, n], &cfg, &provenance, tiny_budget),
        Err(PidError::InvalidK {
            k,
            n_samples,
        }) if k == n && n_samples == n
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_k_trajectory_validates_provenance_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        None,
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_k_trajectory(x, y, &[2, 3], &cfg, &provenance, tiny_budget),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_sample_trajectory_validates_config_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg =
        HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_tie_epsilon(0.25);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("frozen test embedding; no learned parameters"),
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_sample_size_trajectory(x, y, &[8, n], &cfg, &provenance, tiny_budget,),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "tie_epsilon must be exactly 0; strict counting uses next-down semantics",
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_sample_trajectory_validates_provenance_before_resource_preflight() {
    let n = 12;
    let (x_data, y_data) = hyperbolic_data(n);
    let x = MatRef::new(&x_data, n, 2).unwrap();
    let y = MatRef::new(&y_data, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        None,
    )
    .unwrap();
    let tiny_budget = ResourceBudget::new(1, 1, 1, 1).unwrap();

    assert!(matches!(
        hyperbolic_ksg_sample_size_trajectory(x, y, &[8, n], &cfg, &provenance, tiny_budget,),
        Err(PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperbolic reports require embedding_training_provenance",
        })
    ));
}

#[test]
fn provenance_rejects_empty_descriptions() {
    assert!(matches!(
        KsgProvenance::new("  ", "additive Gaussian sensor noise", None),
        Err(PidError::InvalidConfig { .. })
    ));
    assert!(matches!(
        KsgProvenance::new("z-score each column", "\n", None),
        Err(PidError::InvalidConfig { .. })
    ));
    assert!(matches!(
        KsgProvenance::new(
            "z-score each column",
            "additive Gaussian sensor noise",
            Some("\t"),
        ),
        Err(PidError::InvalidConfig { .. })
    ));
}

#[test]
fn euclidean_report_preserves_metadata_and_radius_diagnostics() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "training-fold z-score parameters applied without refitting",
        "i.i.d. draws with an additive continuous sensor-noise model",
        None,
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(
        report.estimate_nats.to_bits(),
        report.signed_estimate_nats.to_bits()
    );
    assert_eq!(report.n_samples, n);
    assert_eq!(report.k, 4);
    assert_eq!(report.metric, Metric::Chebyshev);
    assert_eq!(report.negative_handling, NegativeHandling::Allow);
    assert!(matches!(
        report.support_contract,
        SupportContract::AssumeRegularFullDimensional { .. }
    ));
    assert_eq!(report.method_status, KsgMethodStatus::RestrictedDomain);
    assert_eq!(report.geometry_model, KsgGeometryModel::AmbientChebyshev);
    assert_eq!(report.curvature, None);
    assert_eq!(report.x_hyperbolic_dimension, None);
    assert_eq!(report.y_hyperbolic_dimension, None);
    assert_eq!(report.x_diagnostics.ambient_dimension, 2);
    assert_eq!(report.y_diagnostics.ambient_dimension, 1);
    assert_eq!(report.x_diagnostics.marginal_shells.query_count, n);
    assert_eq!(report.y_diagnostics.marginal_shells.query_count, n);
    assert_eq!(report.joint_shells.query_count, n);
    assert!(report.x_diagnostics.marginal_shells.kth_radius.min > 0.0);
    assert!(report.y_diagnostics.marginal_shells.kth_radius.min > 0.0);
    assert!(report.joint_shells.kth_radius.min > 0.0);
    assert!(report.joint_shells.kth_radius.max >= report.joint_shells.kth_radius.min);
    let dimension_assumption = report
        .assumption_ledger
        .iter()
        .find(|entry| entry.assumption == Assumption::FixedLocalDimension)
        .unwrap();
    assert_eq!(
        dimension_assumption.state,
        AssumptionState::AssumptionsDeclared
    );
    assert!(dimension_assumption
        .note
        .contains("each required marginal and joint law"));
    assert_eq!(
        report.provenance.preprocessing_description(),
        "training-fold z-score parameters applied without refitting"
    );
    assert_eq!(
        report.provenance.observation_model_description(),
        "i.i.d. draws with an additive continuous sensor-noise model"
    );
    assert!(report
        .warnings
        .contains(&KsgReportWarning::SampleDiagnosticsCannotProveSupport));
    assert!(KsgReportWarning::SampleDiagnosticsCannotProveSupport
        .message()
        .contains("cannot determine the cause or prove"));
}

#[test]
fn report_records_the_selected_backend_without_claiming_a_fallback() {
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);

    let (small_x, small_y) = euclidean_data(32);
    let small = ksg_mi_report(
        MatRef::new(&small_x, 32, 2).unwrap(),
        MatRef::new(&small_y, 32, 1).unwrap(),
        &cfg,
        &provenance,
    )
    .unwrap();
    assert_eq!(small.neighbor_backend, KsgNeighborBackend::BruteForce);

    let (large_x, large_y) = euclidean_data(128);
    let large = ksg_mi_report(
        MatRef::new(&large_x, 128, 2).unwrap(),
        MatRef::new(&large_y, 128, 1).unwrap(),
        &cfg,
        &provenance,
    )
    .unwrap();
    assert_eq!(
        large.neighbor_backend,
        KsgNeighborBackend::ExactChebyshevKdTree
    );

    let json = serde_json::to_value(&large).unwrap();
    assert!(json.get("neighbor_backend").is_some());
    assert!(json.get("used_brute_force_fallback").is_none());
    assert!(json.get("backend_fallback_occurred").is_none());
}

#[test]
fn report_retains_signed_estimate_under_presentation_clamping() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let config = KsgConfig::assume_regular_full_dimensional()
        .with_k(4)
        .with_negative_handling(NegativeHandling::ClampToZero);
    let provenance = KsgProvenance::new(
        "identity transform",
        "i.i.d. continuous regression fixture",
        None,
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &config, &provenance).unwrap();

    assert_eq!(
        report.estimate_nats.to_bits(),
        report.signed_estimate_nats.max(0.0).to_bits()
    );
    let json = serde_json::to_value(&report).unwrap();
    assert_eq!(
        json["signed_estimate_nats"].as_f64().unwrap().to_bits(),
        report.signed_estimate_nats.to_bits()
    );
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_requires_embedding_training_provenance() {
    let n = 16;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "no coordinate preprocessing",
        "smooth densities relative to declared manifold volume",
        None,
    )
    .unwrap();

    let error = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();

    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            ..
        }
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn report_validates_shape_before_hyperbolic_provenance_gate() {
    let x_data = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0];
    let y_data = [1.0, 0.0, 1.0, 0.0];
    let x = MatRef::new(&x_data, 3, 2).unwrap();
    let y = MatRef::new(&y_data, 2, 2).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        None,
    )
    .unwrap();

    assert!(matches!(
        hyperbolic_ksg_mi_report(x, y, &cfg, &provenance),
        Err(PidError::RowCountMismatch {
            context: "ksg_mi_report",
            ..
        })
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_rejects_row_width_below_two_as_configuration() {
    let x_data = [1.0, 1.1, 1.2, 1.3];
    let y_data = [1.0, 1.1, 1.2, 1.3];
    let x = MatRef::new(&x_data, 4, 1).unwrap();
    let y = MatRef::new(&y_data, 4, 1).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE);
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        Some("frozen encoder checkpoint sha256:abc"),
    )
    .unwrap();

    let error = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();
    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        }
    ));
}

#[cfg(feature = "experimental-hyperbolic")]
#[test]
fn hyperbolic_report_records_model_curvature_dimensions_and_status() {
    let n = 24;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = HyperbolicKsgConfig::assume_smooth_manifold(HYPERBOLIC_CURVATURE).with_k(3);
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation"),
    )
    .unwrap();

    let report = hyperbolic_ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(
        report.metric,
        HyperbolicMetric::lorentz(HYPERBOLIC_CURVATURE)
    );
    assert_eq!(report.method_status, KsgMethodStatus::Experimental);
    assert_eq!(
        report.geometry_model,
        HyperbolicKsgGeometryModel::LorentzHyperboloid
    );
    assert_eq!(report.curvature, HYPERBOLIC_CURVATURE);
    assert_eq!(report.x_hyperbolic_dimension, 1);
    assert_eq!(report.y_hyperbolic_dimension, 2);
    assert_eq!(
        report.provenance.embedding_training_provenance(),
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation")
    );
    assert!(report
        .warnings
        .contains(&HyperbolicKsgReportWarning::ConsistencyNotEstablished));
    assert!(HyperbolicKsgReportWarning::ConsistencyNotEstablished
        .message()
        .contains("lacks a statistical consistency theorem"));
}

#[test]
fn report_is_deterministic() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(4);
    let provenance = KsgProvenance::new(
        "fixed preprocessing recipe v2",
        "i.i.d. absolutely-continuous observation model",
        None,
    )
    .unwrap();

    let first = ksg_mi_report(x, y, &cfg, &provenance).unwrap();
    let second = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert_eq!(first, second);
}

#[test]
fn giant_thread_ceiling_is_capped_to_available_query_work() {
    let n = 16;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional().with_k(3);
    let provenance = KsgProvenance::new("identity", "i.i.d. continuous fixture", None).unwrap();
    let mut budget = ResourceBudget::default();
    budget.max_threads = usize::MAX;

    let report = ksg_mi_report_with_budget(x, y, &cfg, &provenance, budget).unwrap();
    assert!(report.estimate_nats.is_finite());
}
