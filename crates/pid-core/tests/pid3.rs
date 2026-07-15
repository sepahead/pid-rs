#![cfg(feature = "research-mixed-dimension-pid3")]

use pid_core::experimental::continuous::raw_scalars::{ksg_mi, ksg_mi_concat_xy};
use pid_core::experimental::mixed_dimension_pid3::{
    pid3_isx, pid3_isx_report, Antichain3, Pid3Config, Pid3MethodStatus, Pid3Provenance,
};
use pid_core::stable::continuous::{KsgConfig, NegativeHandling, SupportContract};
use pid_core::{concat_horiz, MatRef, Metric, PidError};

mod common;

use common::csxpid_reference;

fn leq(a: Antichain3, b: Antichain3) -> bool {
    // a ⪯ b iff for every set B in b, there exists A in a with A ⊆ B.
    for &b_set in b.sets() {
        let mut found = false;
        for &a_set in a.sets() {
            if (a_set & b_set) == a_set {
                found = true;
                break;
            }
        }
        if !found {
            return false;
        }
    }
    true
}

fn csxpid_antichain(value: &serde_json::Value) -> Antichain3 {
    let sets = value
        .as_array()
        .unwrap()
        .iter()
        .map(|source_set| {
            source_set
                .as_array()
                .unwrap()
                .iter()
                .fold(0u8, |mask, source| {
                    let source = u32::try_from(source.as_u64().unwrap()).unwrap();
                    mask | (1u8 << source)
                })
        })
        .collect::<Vec<_>>();
    Antichain3::try_from_sets(&sets).unwrap()
}

#[test]
fn pid3_isx_matches_pinned_csxpid_atoms_on_committed_fixture() {
    // The same pinned external artifact used by tests/isx.rs records all 18 csxpid atoms for
    // this three-source input. Match by antichain, because the two libraries expose different
    // but deterministic lattice orders.
    let reference = csxpid_reference();
    assert_eq!(
        reference["provenance"]["upstream"]["commit"].as_str(),
        Some("7bb984611a422cf7944ece68993fe3a27e2eadec")
    );

    let case = &reference["cases"]["trivariate"];
    let rows = case["rows"].as_array().unwrap();
    let n = rows.len();
    let k = 3usize;
    let mut s0 = Vec::with_capacity(n);
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for row in rows {
        let row = row.as_array().unwrap();
        assert_eq!(row.len(), 4);
        s0.push(row[0].as_f64().unwrap());
        s1.push(row[1].as_f64().unwrap());
        s2.push(row[2].as_f64().unwrap());
        t.push(row[3].as_f64().unwrap());
    }

    let s0 = MatRef::new(&s0, n, 1).unwrap();
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = Pid3Config {
        k,
        metric: Metric::Chebyshev,
        tie_epsilon: 0.0,
        support_contract: SupportContract::assume_regular_full_dimensional(),
        experimental_allow_mixed_dimension_lattice: true,
    };

    let out = pid3_isx(s0, s1, s2, t, &cfg).unwrap();
    assert_eq!(out.n_samples, n);
    assert_eq!(out.k, k);
    assert_eq!(out.source_ambient_dimensions, [1, 1, 1]);
    assert_eq!(out.target_ambient_dimension, 1);
    assert_eq!(
        out.method_status,
        Pid3MethodStatus::ExperimentalMixedDimension
    );
    assert_eq!(out.warnings.len(), 3);
    assert_eq!(out.redundancies.len(), 18);
    assert_eq!(out.atoms.len(), 18);

    let provenance = Pid3Provenance::new(
        "source 1 standardized on training rows",
        "source 2 standardized on training rows",
        "source 3 standardized on training rows",
        "target left in measured units",
        "ideal continuous observation model; no post-hoc jitter",
    )
    .unwrap();
    let report = pid3_isx_report(s0, s1, s2, t, &cfg, &provenance).unwrap();
    assert_eq!(
        report.provenance.source3_preprocessing_description(),
        "source 3 standardized on training rows"
    );
    assert_eq!(report.result.atoms.len(), 18);

    let expected_antichains = [
        Antichain3::try_from_sets(&[0b001]).unwrap(),
        Antichain3::try_from_sets(&[0b010]).unwrap(),
        Antichain3::try_from_sets(&[0b100]).unwrap(),
        Antichain3::try_from_sets(&[0b011]).unwrap(),
        Antichain3::try_from_sets(&[0b101]).unwrap(),
        Antichain3::try_from_sets(&[0b110]).unwrap(),
        Antichain3::try_from_sets(&[0b111]).unwrap(),
        Antichain3::try_from_sets(&[0b001, 0b010]).unwrap(),
        Antichain3::try_from_sets(&[0b001, 0b100]).unwrap(),
        Antichain3::try_from_sets(&[0b001, 0b110]).unwrap(),
        Antichain3::try_from_sets(&[0b010, 0b100]).unwrap(),
        Antichain3::try_from_sets(&[0b010, 0b101]).unwrap(),
        Antichain3::try_from_sets(&[0b011, 0b100]).unwrap(),
        Antichain3::try_from_sets(&[0b011, 0b101]).unwrap(),
        Antichain3::try_from_sets(&[0b011, 0b110]).unwrap(),
        Antichain3::try_from_sets(&[0b101, 0b110]).unwrap(),
        Antichain3::try_from_sets(&[0b001, 0b010, 0b100]).unwrap(),
        Antichain3::try_from_sets(&[0b011, 0b101, 0b110]).unwrap(),
    ];
    for (idx, atom) in out.atoms.iter().enumerate() {
        assert_eq!(
            atom.antichain, expected_antichains[idx],
            "unexpected antichain ordering at idx={idx}"
        );
    }

    let expected_atoms = case["atoms"]
        .as_array()
        .unwrap()
        .iter()
        .enumerate()
        .map(|(idx, atom)| {
            let bits = atom["value_bits"].as_f64().unwrap();
            let expected_nats = bits * std::f64::consts::LN_2;
            let stored_nats = atom["value_nats"].as_f64().unwrap();
            assert!(
                (stored_nats - expected_nats).abs() < 1e-15,
                "invalid bit-to-nat conversion in pinned csxpid atom {idx}: bits*ln(2)={expected_nats:.15e} stored={stored_nats:.15e}"
            );
            (
                csxpid_antichain(&atom["antichain"]),
                expected_nats,
            )
        })
        .collect::<Vec<_>>();
    assert_eq!(expected_atoms.len(), 18);

    let tol = 1e-12;
    for (idx, atom) in out.atoms.iter().enumerate() {
        let expected = expected_atoms
            .iter()
            .find_map(|&(antichain, value)| (antichain == atom.antichain).then_some(value))
            .unwrap();
        let got = atom.value;
        assert!(
            (got - expected).abs() < tol,
            "PID3 atom mismatch against pinned csxpid at idx={idx}: got={got:.15e} expected={expected:.15e}"
        );
    }

    // Möbius inversion sanity: for each redundancy, sum of atoms in its down-set matches it.
    for r in &out.redundancies {
        let mut sum = 0.0f64;
        for a in &out.atoms {
            if leq(a.antichain, r.antichain) {
                sum += a.value;
            }
        }
        assert!(
            (sum - r.value).abs() < 1e-10,
            "redundancy mismatch for {:?}: sum_atoms={sum:.15e} redundancy={:.15e}",
            r.antichain,
            r.value
        );
    }

    let mi_cfg = KsgConfig::assume_regular_full_dimensional()
        .with_k(k)
        .with_metric(Metric::Chebyshev)
        .with_tie_epsilon(0.0)
        .with_negative_handling(NegativeHandling::Allow)
        .with_support_contract(SupportContract::assume_regular_full_dimensional());

    // Singleton antichains reduce to KSG MI on the corresponding joint source block.
    let red_s0 = out.redundancy(expected_antichains[0]).unwrap();
    let red_s1 = out.redundancy(expected_antichains[1]).unwrap();
    let red_s2 = out.redundancy(expected_antichains[2]).unwrap();
    let red_s01 = out.redundancy(expected_antichains[3]).unwrap();
    let red_s02 = out.redundancy(expected_antichains[4]).unwrap();
    let red_s12 = out.redundancy(expected_antichains[5]).unwrap();
    let red_s012 = out.redundancy(expected_antichains[6]).unwrap();

    assert!((red_s0 - ksg_mi(s0, t, &mi_cfg).unwrap()).abs() < 1e-12);
    assert!((red_s1 - ksg_mi(s1, t, &mi_cfg).unwrap()).abs() < 1e-12);
    assert!((red_s2 - ksg_mi(s2, t, &mi_cfg).unwrap()).abs() < 1e-12);
    assert!((red_s01 - ksg_mi_concat_xy(s0, s1, t, &mi_cfg).unwrap()).abs() < 1e-12);
    assert!((red_s02 - ksg_mi_concat_xy(s0, s2, t, &mi_cfg).unwrap()).abs() < 1e-12);
    assert!((red_s12 - ksg_mi_concat_xy(s1, s2, t, &mi_cfg).unwrap()).abs() < 1e-12);

    let s01 = concat_horiz(s0, s1).unwrap();
    let s012 = concat_horiz(s01.as_ref(), s2).unwrap();
    let mi = ksg_mi(s012.as_ref(), t, &mi_cfg).unwrap();
    assert!(
        (mi - red_s012).abs() < 1e-12,
        "I(S0,S1,S2;T) mismatch: ksg_mi={mi:.15e} pid3_redundancy={red_s012:.15e}"
    );
}

#[test]
fn antichain3_rejects_invalid_inputs() {
    assert!(Antichain3::try_from_sets(&[]).is_err());
    assert!(Antichain3::try_from_sets(&[0]).is_err());
    assert!(Antichain3::try_from_sets(&[0b1000]).is_err());
    assert!(Antichain3::try_from_sets(&[0b001, 0b001]).is_err());
    // Not an antichain: {0} ⊆ {0,1}.
    assert!(Antichain3::try_from_sets(&[0b001, 0b011]).is_err());
}

#[test]
fn pid3_requires_explicit_mixed_dimension_lattice_opt_in() {
    let data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let source = MatRef::new(&data, data.len(), 1).unwrap();

    let error = pid3_isx(source, source, source, source, &Pid3Config::default()).unwrap_err();

    assert!(error
        .to_string()
        .contains("experimental_allow_mixed_dimension_lattice=true"));
}

#[test]
fn pid3_validates_k_before_the_mixed_dimension_gate() {
    let data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let source = MatRef::new(&data, data.len(), 1).unwrap();
    let cfg = Pid3Config {
        k: 0,
        ..Pid3Config::default()
    };

    assert!(matches!(
        pid3_isx(source, source, source, source, &cfg),
        Err(PidError::InvalidK { k: 0, n_samples: 8 })
    ));
}

#[test]
fn full_pid3_still_requires_a_support_contract_after_the_research_opt_in() {
    let data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let source = MatRef::new(&data, data.len(), 1).unwrap();
    let config = Pid3Config {
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::default()
    };

    assert!(matches!(
        pid3_isx(source, source, source, source, &config),
        Err(PidError::SupportContractRequired { .. })
    ));
}

#[test]
fn pid3_rejects_an_ambiguous_positive_neighbor_shell() {
    let source_data = [0.0, 0.5, 1.0, 0.3, 3.0];
    let target_data = [0.0, 0.4, 0.2, 1.0, 3.0];
    let source = MatRef::new(&source_data, 5, 1).unwrap();
    let target = MatRef::new(&target_data, 5, 1).unwrap();
    let config = Pid3Config {
        k: 2,
        experimental_allow_mixed_dimension_lattice: true,
        ..Pid3Config::assume_regular_full_dimensional()
    };

    assert!(matches!(
        pid3_isx(source, source, source, target, &config),
        Err(PidError::AmbiguousKthNeighborShell { .. })
    ));
}

#[test]
fn pid3_rejects_every_nonzero_or_nonfinite_tie_epsilon() {
    let data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let source = MatRef::new(&data, data.len(), 1).unwrap();

    for tie_epsilon in [-1.0, 1.0e-12, f64::NAN, f64::INFINITY] {
        let config = Pid3Config {
            tie_epsilon,
            ..Pid3Config::default()
        };
        assert!(pid3_isx(source, source, source, source, &config).is_err());
    }
}
