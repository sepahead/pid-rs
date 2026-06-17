use pid_core::{
    ksg_mi, ksg_mi_concat_xy, pid2_isx, IsxConfig, KsgConfig, MatRef, Metric, NegativeHandling,
    Pid2Config,
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
        ..Default::default()
    };
    let cfg = Pid2Config {
        ksg: ksg.clone(),
        isx: IsxConfig::default(),
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
}
