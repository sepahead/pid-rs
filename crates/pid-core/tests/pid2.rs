use pid_core::{
    ksg_mi, ksg_mi_concat_xy, pid2_isx, pid2_isx_report, IsxConfig, KsgConfig, MatRef, Metric,
    NegativeHandling, Pid2Config, Pid2Estimate, Pid2MethodStatus, Pid2Provenance,
    Pid2ReportWarning, Pid2Result, PidError, SupportContract,
};

mod common;

use common::Rng64;

#[test]
fn pid2_identities_hold_by_construction() {
    // This is not an "exact ground truth" test. It asserts the PID2 identities are satisfied
    // (within floating tolerance) when MI and redundancy are computed with the same estimator
    // configuration.
    let mut rng = Rng64::new(0x51A7_2026);
    let n = 350;

    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let a = rng.normal();
        let b = rng.normal();
        let noise = 0.2 * rng.normal();
        s1.push(a);
        s2.push(b);
        t.push(a + b + noise);
    }

    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let ksg = KsgConfig {
        k: 3,
        negative_handling: NegativeHandling::Allow,
        ..KsgConfig::assume_absolutely_continuous()
    };
    let cfg = Pid2Config {
        ksg: ksg.clone(),
        isx: IsxConfig::assume_absolutely_continuous(),
    };

    let out = pid2_isx(s1, s2, t, &cfg).unwrap();

    let i_s1_t = ksg_mi(s1, t, &ksg).unwrap();
    let i_s2_t = ksg_mi(s2, t, &ksg).unwrap();
    let i_s1s2_t = ksg_mi_concat_xy(s1, s2, t, &ksg).unwrap();

    // Unq1 = I(S1;T) - Red, Unq2 = I(S2;T) - Red
    assert!(
        ((out.unique_s1 + out.redundancy) - i_s1_t).abs() < 1e-10,
        "identity failed: Unq1+Red != I(S1;T): lhs={} rhs={}",
        out.unique_s1 + out.redundancy,
        i_s1_t
    );
    assert!(
        ((out.unique_s2 + out.redundancy) - i_s2_t).abs() < 1e-10,
        "identity failed: Unq2+Red != I(S2;T): lhs={} rhs={}",
        out.unique_s2 + out.redundancy,
        i_s2_t
    );

    // Sum of atoms equals total MI.
    let sum_atoms = out.redundancy + out.unique_s1 + out.unique_s2 + out.synergy;
    assert!(
        (sum_atoms - i_s1s2_t).abs() < 1e-10,
        "identity failed: Red+Unq1+Unq2+Syn != I(S1,S2;T): lhs={sum_atoms} rhs={i_s1s2_t}"
    );

    // Syn identity: Syn = I(S1,S2;T) - I(S1;T) - I(S2;T) + Red
    let syn_from_mi = i_s1s2_t - i_s1_t - i_s2_t + out.redundancy;
    assert!(
        (out.synergy - syn_from_mi).abs() < 1e-10,
        "identity failed: Syn mismatch: pid2={} mi-derived={syn_from_mi}",
        out.synergy
    );
}

#[test]
fn pid2_report_keeps_restricted_status_configuration_and_provenance_attached() {
    let s1_data = [0.13, 0.91, 0.37, 0.62, 0.04, 0.78, 0.49, 0.25];
    let s2_data = [0.84, 0.17, 0.55, 0.03, 0.69, 0.31, 0.96, 0.42];
    let target_data = [0.99, 1.06, 0.93, 0.61, 0.75, 1.08, 1.49, 0.64];
    let s1 = MatRef::new(&s1_data, 8, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 8, 1).unwrap();
    let target = MatRef::new(&target_data, 8, 1).unwrap();
    let cfg = Pid2Config::assume_absolutely_continuous();
    let provenance = Pid2Provenance::new(
        "source 1 standardized on training rows",
        "source 2 standardized on training rows",
        "target left in measured units",
        "ideal continuous observation model; no post-hoc jitter",
    )
    .unwrap();

    let report = pid2_isx_report(s1, s2, target, &cfg, &provenance).unwrap();

    assert_eq!(report.n_samples, 8);
    assert_eq!(report.source_ambient_dimensions, [1, 1]);
    assert_eq!(report.target_ambient_dimension, 1);
    assert_eq!(
        report.method_status,
        Pid2MethodStatus::ExperimentalRestrictedDomain
    );
    assert_eq!(
        report.support_contract,
        SupportContract::AssumeAbsolutelyContinuous
    );
    assert_eq!(report.effective_negative_handling, NegativeHandling::Allow);
    assert_eq!(report.supplied_ksg_config.k, cfg.ksg.k);
    assert_eq!(report.supplied_isx_config.method, cfg.isx.method);
    assert_eq!(
        report.provenance.source2_preprocessing_description(),
        "source 2 standardized on training rows"
    );
    assert!(report
        .warnings
        .contains(&Pid2ReportWarning::GeneralConsistencyNotEstablished));
    assert!(!report
        .warnings
        .contains(&Pid2ReportWarning::ExperimentalIsxBaseline));
    assert!(report.atoms.synergy.is_finite());
    assert!(report.estimate_terms.mi_s1s2_t.is_finite());
}

#[test]
fn pid2_provenance_rejects_empty_descriptions() {
    let error = Pid2Provenance::new("source 1", " ", "target", "observation model").unwrap_err();
    assert!(error
        .to_string()
        .contains("source2_preprocessing_description must be nonempty"));
}

#[test]
fn pid2_rejects_incoherent_estimator_configs() {
    let n = 8;
    let s1_data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let s2_data = [0.0, -0.1, -0.3, -0.6, -1.0, -1.5, -2.1, -2.8];
    let t_data = [0.0, 0.0, 0.1, 0.2, 0.4, 0.7, 1.1, 1.6];

    let s1 = MatRef::new(&s1_data, n, 1).unwrap();
    let s2 = MatRef::new(&s2_data, n, 1).unwrap();
    let t = MatRef::new(&t_data, n, 1).unwrap();

    let cfg = Pid2Config {
        ksg: KsgConfig {
            k: 3,
            ..Default::default()
        },
        isx: IsxConfig {
            k: 4,
            ..Default::default()
        },
    };
    assert!(pid2_isx(s1, s2, t, &cfg)
        .unwrap_err()
        .to_string()
        .contains("k values must match"));

    let cfg = Pid2Config {
        ksg: KsgConfig {
            metric: Metric::HyperbolicLorentz,
            ..Default::default()
        },
        isx: IsxConfig::default(),
    };
    assert!(pid2_isx(s1, s2, t, &cfg)
        .unwrap_err()
        .to_string()
        .contains("metrics must match"));

    let cfg = Pid2Config {
        ksg: KsgConfig {
            tie_epsilon: 1e-12,
            ..Default::default()
        },
        isx: IsxConfig::default(),
    };
    assert!(pid2_isx(s1, s2, t, &cfg)
        .unwrap_err()
        .to_string()
        .contains("tie_epsilon values must match"));

    let cfg = Pid2Config {
        ksg: KsgConfig::assume_absolutely_continuous(),
        isx: IsxConfig {
            support_contract: SupportContract::KnownAtomicOrMixed,
            ..IsxConfig::default()
        },
    };
    assert!(pid2_isx(s1, s2, t, &cfg)
        .unwrap_err()
        .to_string()
        .contains("support contracts must match"));

    let tied_data = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0];
    let tied = MatRef::new(&tied_data, n, 1).unwrap();
    let cfg = Pid2Config {
        ksg: KsgConfig {
            tie_epsilon: 1.0e-6,
            ..KsgConfig::assume_absolutely_continuous()
        },
        isx: IsxConfig {
            tie_epsilon: 1.0e-6,
            ..IsxConfig::assume_absolutely_continuous()
        },
    };
    let error = pid2_isx(tied, s2, t, &cfg).unwrap_err();
    assert!(error
        .to_string()
        .contains("tie_epsilon must both be exactly 0"));
}

#[test]
fn pid2_rejects_unequal_source_dimensions_before_estimating_mi_terms() {
    let scalar_data = [0.0, 0.2, 0.5, 0.9];
    let vector_data = [0.0, 0.1, 0.2, 0.3, 0.5, 0.6, 0.9, 1.0];
    let target_data = [0.05, 0.25, 0.55, 0.95];
    let scalar = MatRef::new(&scalar_data, 4, 1).unwrap();
    let vector = MatRef::new(&vector_data, 4, 2).unwrap();
    let target = MatRef::new(&target_data, 4, 1).unwrap();

    let error = pid2_isx(scalar, vector, target, &Pid2Config::default()).unwrap_err();

    assert!(matches!(
        error,
        PidError::SourceDimensionMismatch {
            context: "pid2_isx_estimate",
            left_cols: 1,
            right_cols: 2,
        }
    ));
}

#[test]
fn pid2_rejects_all_row_mismatches_before_estimating_any_term() {
    let s1_data = [0.03, 0.17, 0.31, 0.52, 0.76, 1.01, 1.29, 1.62];
    let s2_data = [1.73, 1.41, 1.16, 0.88, 0.63, 0.39, 0.21];
    let target_data = [0.12, 0.29, 0.48, 0.71, 0.97, 1.22, 1.51, 1.85];
    let s1 = MatRef::new(&s1_data, 8, 1).unwrap();
    let s2 = MatRef::new(&s2_data, 7, 1).unwrap();
    let target = MatRef::new(&target_data, 8, 1).unwrap();

    assert!(matches!(
        pid2_isx(s1, s2, target, &Pid2Config::assume_absolutely_continuous()),
        Err(PidError::RowCountMismatch {
            context: "pid2_isx_estimate",
            left_rows: 8,
            right_rows: 7,
        })
    ));
}

#[test]
fn pid2_checked_constructor_rejects_nonfinite_inputs_and_atom_overflow() {
    let nonfinite = Pid2Estimate {
        mi_s1_t: f64::NAN,
        mi_s2_t: 0.0,
        mi_s1s2_t: 0.0,
        redundancy_isx: 0.0,
    };
    assert!(Pid2Result::from_estimate(nonfinite).is_err());

    let overflowing = Pid2Estimate {
        mi_s1_t: f64::MAX,
        mi_s2_t: -f64::MAX,
        mi_s1s2_t: 0.0,
        redundancy_isx: -f64::MAX,
    };
    assert!(Pid2Result::from_estimate(overflowing).is_err());
}

#[test]
fn pid2_checked_constructor_recovers_representable_synergy_after_intermediate_overflow() {
    let estimate = Pid2Estimate {
        mi_s1_t: -f64::MAX,
        mi_s2_t: f64::MAX,
        mi_s1s2_t: f64::MAX,
        redundancy_isx: 0.0,
    };

    let result = Pid2Result::from_estimate(estimate).unwrap();
    assert_eq!(result.unique_s1, -f64::MAX);
    assert_eq!(result.unique_s2, f64::MAX);
    assert_eq!(result.synergy, f64::MAX);
}

#[test]
fn pid2_checked_constructor_preserves_tiny_identity_across_extreme_atom_cancellation() {
    let tiny = f64::from_bits(50);
    let estimate = Pid2Estimate {
        mi_s1_t: f64::MAX,
        mi_s2_t: -f64::MAX,
        mi_s1s2_t: 2.0 * tiny,
        redundancy_isx: tiny,
    };

    let result = Pid2Result::from_estimate(estimate).unwrap();
    assert_eq!(
        [
            result.redundancy,
            result.unique_s1,
            result.unique_s2,
            result.synergy,
        ],
        [tiny, f64::MAX, -f64::MAX, tiny]
    );
}

#[test]
fn pid2_checked_constructor_recovers_tiny_synergy_after_finite_cancellation() {
    let tiny = f64::from_bits(50);
    let estimate = Pid2Estimate {
        mi_s1_t: f64::MAX,
        mi_s2_t: -f64::MAX,
        mi_s1s2_t: tiny,
        redundancy_isx: 0.0,
    };

    let result = Pid2Result::from_estimate(estimate).unwrap();
    assert_eq!(
        [
            result.redundancy,
            result.unique_s1,
            result.unique_s2,
            result.synergy,
        ],
        [0.0, f64::MAX, -f64::MAX, tiny]
    );
}
