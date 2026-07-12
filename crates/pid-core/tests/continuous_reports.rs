#![cfg(feature = "experimental-continuous")]

use pid_core::experimental::continuous::{
    co_information_pairwise_report, co_information_triplet_report, pid2_isx_cross_fit_reports,
    pid2_isx_report, CoInformationReportWarning, Pid2Config, Pid2CrossFitAggregation,
    Pid2CrossFitFold, Pid2Provenance, Pid2ReportWarning,
};
use pid_core::stable::continuous::{KsgConfig, KsgProvenance};
use pid_core::MatRef;

fn continuous_data(n: usize, offset: f64) -> (Vec<f64>, Vec<f64>, Vec<f64>, Vec<f64>) {
    let mut x = Vec::with_capacity(n);
    let mut y = Vec::with_capacity(n);
    let mut z = Vec::with_capacity(n);
    let mut target = Vec::with_capacity(n);
    for index in 0..n {
        let u = index as f64 + offset;
        let x_value = (0.731 * u + 0.017 * u * u).sin() + 0.011 * u;
        let y_value = (1.113 * u + 0.013 * u * u).cos() - 0.007 * u;
        let z_value = (0.419 * u + 0.019 * u * u).sin() + 0.003 * u;
        x.push(x_value);
        y.push(y_value);
        z.push(z_value);
        target.push(0.4 * x_value - 0.3 * y_value + 0.2 * z_value + 0.001 * u * u);
    }
    (x, y, z, target)
}

fn ksg_provenance() -> KsgProvenance {
    KsgProvenance::new(
        "fixed source-specific transforms fitted outside evaluation rows",
        "declared i.i.d. continuous observation model with finite sensor noise",
        None,
    )
    .unwrap()
    .with_sampling_model_and_splits("i.i.d. evaluation rows", Some("train"), Some("eval"))
    .unwrap()
}

#[test]
fn co_information_reports_retain_every_constituent_and_serialize() {
    let n = 36;
    let (x, y, z, target) = continuous_data(n, 0.37);
    let x = MatRef::new(&x, n, 1).unwrap();
    let y = MatRef::new(&y, n, 1).unwrap();
    let z = MatRef::new(&z, n, 1).unwrap();
    let target = MatRef::new(&target, n, 1).unwrap();
    let cfg = KsgConfig::assume_regular_full_dimensional();
    let provenance = ksg_provenance();

    let pair = co_information_pairwise_report(x, y, target, &cfg, &provenance).unwrap();
    assert_eq!(pair.x_target_report.n_samples, n);
    assert_eq!(pair.y_target_report.n_samples, n);
    assert_eq!(pair.joint_xy_target_report.n_samples, n);
    assert!(pair.co_information_nats.is_finite());
    assert!(pair
        .warnings
        .contains(&CoInformationReportWarning::SameSampleExtremumSelectionIsBiased));
    let pair_json = serde_json::to_string(&pair).unwrap();
    assert!(!pair_json.contains("NaN"));

    let triplet = co_information_triplet_report(x, y, z, target, &cfg, &provenance).unwrap();
    assert!(triplet.co_information_nats.is_finite());
    assert_eq!(triplet.signed_terms_nats.len(), 7);
    assert_eq!(triplet.joint_xyz_target_report.n_samples, n);
    let triplet_json = serde_json::to_string(&triplet).unwrap();
    assert!(!triplet_json.contains("NaN"));
}

#[test]
fn pid2_report_embeds_complete_reports_and_propagated_local_covariance() {
    let n = 40;
    let (s1, s2, _z, target) = continuous_data(n, 1.19);
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let target = MatRef::new(&target, n, 1).unwrap();
    let cfg = Pid2Config::assume_regular_full_dimensional();
    let provenance = Pid2Provenance::new(
        "source 1 transform fixed on training rows",
        "source 2 transform fixed on training rows",
        "target transform fixed on training rows",
        "continuous noisy observation model",
    )
    .unwrap()
    .with_sampling_model_and_splits("i.i.d. evaluation rows", Some("train"), Some("eval"))
    .unwrap();

    let report = pid2_isx_report(s1, s2, target, &cfg, &provenance).unwrap();
    assert_eq!(
        report.mi_s1_t_report.estimate_nats,
        report.estimate_terms.mi_s1_t
    );
    assert_eq!(
        report.mi_s2_t_report.estimate_nats,
        report.estimate_terms.mi_s2_t
    );
    assert_eq!(
        report.mi_s1s2_t_report.estimate_nats,
        report.estimate_terms.mi_s1s2_t
    );
    assert_eq!(
        report.redundancy_isx_report.estimate_nats,
        report.estimate_terms.redundancy_isx
    );
    for row in 0..4 {
        for column in 0..4 {
            assert_eq!(
                report.joint_diagnostics.local_contribution_covariance_nats2[row][column],
                report.joint_diagnostics.local_contribution_covariance_nats2[column][row]
            );
            assert_eq!(
                report
                    .joint_diagnostics
                    .propagated_atom_local_covariance_nats2[row][column],
                report
                    .joint_diagnostics
                    .propagated_atom_local_covariance_nats2[column][row]
            );
        }
    }
    assert!(report
        .warnings
        .contains(&Pid2ReportWarning::LocalContributionCovarianceIsNotSamplingCovariance));
    let json = serde_json::to_string(&report).unwrap();
    assert!(!json.contains("NaN"));
}

#[test]
fn cross_fit_reports_keep_fold_coordinates_separate() {
    let n = 24;
    let (s1_a, s2_a, _z_a, target_a) = continuous_data(n, 2.31);
    let (s1_b, s2_b, _z_b, target_b) = continuous_data(n, 71.07);
    let s1_a = MatRef::new(&s1_a, n, 1).unwrap();
    let s2_a = MatRef::new(&s2_a, n, 1).unwrap();
    let target_a = MatRef::new(&target_a, n, 1).unwrap();
    let s1_b = MatRef::new(&s1_b, n, 1).unwrap();
    let s2_b = MatRef::new(&s2_b, n, 1).unwrap();
    let target_b = MatRef::new(&target_b, n, 1).unwrap();
    let provenance_a = Pid2Provenance::new(
        "fold A source 1 transform",
        "fold A source 2 transform",
        "fold A target transform",
        "continuous noisy observation model",
    )
    .unwrap()
    .with_sampling_model_and_splits("i.i.d. rows", Some("fold-B-train"), Some("fold-A"))
    .unwrap();
    let provenance_b = Pid2Provenance::new(
        "fold B source 1 transform",
        "fold B source 2 transform",
        "fold B target transform",
        "continuous noisy observation model",
    )
    .unwrap()
    .with_sampling_model_and_splits("i.i.d. rows", Some("fold-A-train"), Some("fold-B"))
    .unwrap();
    let fold_a = Pid2CrossFitFold::new("fold-A", s1_a, s2_a, target_a, &provenance_a).unwrap();
    let fold_b = Pid2CrossFitFold::new("fold-B", s1_b, s2_b, target_b, &provenance_b).unwrap();

    let report = pid2_isx_cross_fit_reports(
        &[fold_a, fold_b],
        &Pid2Config::assume_regular_full_dimensional(),
    )
    .unwrap();
    assert_eq!(report.folds.len(), 2);
    assert_eq!(
        report.aggregation,
        Pid2CrossFitAggregation::FoldCoordinatesRemainSeparate
    );
    assert!(report.warning.contains("not pooled"));
    serde_json::to_string(&report).unwrap();
}
