use pid_core::{
    ksg_mi_report, KsgConfig, KsgGeometryModel, KsgMethodStatus, KsgProvenance, KsgReportWarning,
    MatRef, Metric, NegativeHandling, PidError, SupportContract,
};

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
            Some("\t".to_owned()),
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
    let cfg = KsgConfig {
        k: 4,
        ..KsgConfig::assume_absolutely_continuous()
    };
    let provenance = KsgProvenance::new(
        "training-fold z-score parameters applied without refitting",
        "i.i.d. draws with an additive continuous sensor-noise model",
        None,
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(report.n_samples, n);
    assert_eq!(report.k, 4);
    assert_eq!(report.metric, Metric::Chebyshev);
    assert_eq!(report.negative_handling, NegativeHandling::Allow);
    assert_eq!(
        report.support_contract,
        SupportContract::AssumeAbsolutelyContinuous
    );
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
fn hyperbolic_report_requires_embedding_training_provenance() {
    let n = 16;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = KsgConfig {
        k: 3,
        ..KsgConfig::experimental_smooth_hyperbolic_manifold()
    };
    let provenance = KsgProvenance::new(
        "no coordinate preprocessing",
        "smooth densities relative to declared manifold volume",
        None,
    )
    .unwrap();

    let error = ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();

    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            ..
        }
    ));
}

#[test]
fn report_validates_shape_before_hyperbolic_provenance_gate() {
    let x_data = [1.0, 0.0, 1.0, 0.0, 1.0, 0.0];
    let y_data = [1.0, 0.0, 1.0, 0.0];
    let x = MatRef::new(&x_data, 3, 2).unwrap();
    let y = MatRef::new(&y_data, 2, 2).unwrap();
    let cfg = KsgConfig::experimental_smooth_hyperbolic_manifold();
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        None,
    )
    .unwrap();

    assert!(matches!(
        ksg_mi_report(x, y, &cfg, &provenance),
        Err(PidError::RowCountMismatch {
            context: "ksg_mi_report",
            ..
        })
    ));
}

#[test]
fn hyperbolic_report_rejects_row_width_below_two_as_configuration() {
    let x_data = [1.0, 1.1, 1.2, 1.3];
    let y_data = [1.0, 1.1, 1.2, 1.3];
    let x = MatRef::new(&x_data, 4, 1).unwrap();
    let y = MatRef::new(&y_data, 4, 1).unwrap();
    let cfg = KsgConfig::experimental_smooth_hyperbolic_manifold();
    let provenance = KsgProvenance::new(
        "projected to hyperboloid coordinates",
        "smooth manifold observation model",
        Some("frozen encoder checkpoint sha256:abc".to_owned()),
    )
    .unwrap();

    let error = ksg_mi_report(x, y, &cfg, &provenance).unwrap_err();
    assert!(matches!(
        error,
        PidError::InvalidConfig {
            context: "ksg_mi_report",
            message: "Lorentz-hyperboloid inputs must each have row width d+1 >= 2",
        }
    ));
}

#[test]
fn hyperbolic_report_records_model_curvature_dimensions_and_status() {
    let n = 24;
    let (x, y) = hyperbolic_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 3).unwrap();
    let cfg = KsgConfig {
        k: 3,
        ..KsgConfig::experimental_smooth_hyperbolic_manifold()
    };
    let provenance = KsgProvenance::new(
        "projected to the upper unit hyperboloid",
        "smooth manifold-valued observations",
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation".to_owned()),
    )
    .unwrap();

    let report = ksg_mi_report(x, y, &cfg, &provenance).unwrap();

    assert!(report.estimate_nats.is_finite());
    assert_eq!(report.metric, Metric::HyperbolicLorentz);
    assert_eq!(report.method_status, KsgMethodStatus::Experimental);
    assert_eq!(report.geometry_model, KsgGeometryModel::LorentzHyperboloid);
    assert_eq!(report.curvature, Some(-1.0));
    assert_eq!(report.x_hyperbolic_dimension, Some(1));
    assert_eq!(report.y_hyperbolic_dimension, Some(2));
    assert_eq!(
        report.provenance.embedding_training_provenance(),
        Some("encoder checkpoint sha256:0123456789abcdef; frozen before evaluation")
    );
    assert!(report
        .warnings
        .contains(&KsgReportWarning::HyperbolicConsistencyNotEstablished));
    assert!(KsgReportWarning::HyperbolicConsistencyNotEstablished
        .message()
        .contains("lacks a statistical consistency theorem"));
}

#[test]
fn report_is_deterministic() {
    let n = 32;
    let (x, y) = euclidean_data(n);
    let x = MatRef::new(&x, n, 2).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let cfg = KsgConfig {
        k: 4,
        ..KsgConfig::assume_absolutely_continuous()
    };
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
