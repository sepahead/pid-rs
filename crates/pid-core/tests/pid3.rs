use pid_core::{
    concat_horiz, ksg_mi, ksg_mi_concat_xy, pid3_isx, Antichain3, KsgConfig, MatRef, Metric,
    Pid3Config,
};

mod common;

use common::Rng64;

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

#[test]
fn pid3_isx_matches_reference_implementation_on_fixed_data() {
    // Cross-check against the authors' reference implementation:
    // gitlab.gwdg.de/wibral/continuouspidestimator (csxpid), as described in
    // Ehrlich et al. (2024), arXiv:2311.06373v3.
    //
    // The expected atoms were produced by running csxpid on the exact same fixed dataset
    // and converting from bits to nats.

    let n = 80usize;
    let k = 3usize;

    let mut rng = Rng64::new(13_579);

    let mut s0 = Vec::with_capacity(n);
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let mut t = Vec::with_capacity(n);
    for _ in 0..n {
        let base = rng.next_f64();
        let u1 = rng.next_f64();
        let u2 = rng.next_f64();
        let u3 = rng.next_f64();
        s0.push(base);
        s1.push(base + 0.5 * u1);
        s2.push(base + 0.25 * u2);
        t.push(base + 0.125 * u3);
    }

    let s0 = MatRef::new(&s0, n, 1).unwrap();
    let s1 = MatRef::new(&s1, n, 1).unwrap();
    let s2 = MatRef::new(&s2, n, 1).unwrap();
    let t = MatRef::new(&t, n, 1).unwrap();

    let cfg = Pid3Config {
        k,
        metric: Metric::Chebyshev,
        tie_epsilon: 0.0,
    };

    let out = pid3_isx(s0, s1, s2, t, &cfg).unwrap();
    assert_eq!(out.redundancies.len(), 18);
    assert_eq!(out.atoms.len(), 18);

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

    #[allow(clippy::excessive_precision)]
    let expected_atoms = [
        0.045099345099344976_f64,
        -0.25302599236054757_f64,
        -0.065206767293164464_f64,
        0.087611792823188581_f64,
        0.0091861559600528997_f64,
        -0.1578255139667597_f64,
        0.05160428464444039_f64,
        0.14130341577777206_f64,
        0.22583182268862786_f64,
        0.099324132467325632_f64,
        -0.39571836828396945_f64,
        0.0039488653196135468_f64,
        0.076280456050004067_f64,
        0.069661404019956227_f64,
        0.063305913588905832_f64,
        -0.038322030298133331_f64,
        1.4427794123962949_f64,
        0.053884864740318422_f64,
    ];

    let tol = 1e-10;
    for (idx, (atom, &expected)) in out.atoms.iter().zip(expected_atoms.iter()).enumerate() {
        let got = atom.value;
        assert!(
            (got - expected).abs() < tol,
            "PID3 atom mismatch at idx={idx}: got={got:.15e} expected={expected:.15e}"
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

    let mi_cfg = KsgConfig {
        k,
        metric: Metric::Chebyshev,
        tie_epsilon: 0.0,
        negative_handling: pid_core::NegativeHandling::Allow,
    };

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
fn pid3_rejects_non_chebyshev_metric() {
    let data = [0.0, 0.1, 0.3, 0.6, 1.0, 1.5, 2.1, 2.8];
    let s0 = MatRef::new(&data, data.len(), 1).unwrap();
    let s1 = MatRef::new(&data, data.len(), 1).unwrap();
    let s2 = MatRef::new(&data, data.len(), 1).unwrap();
    let t = MatRef::new(&data, data.len(), 1).unwrap();
    let cfg = Pid3Config {
        metric: Metric::HyperbolicLorentz,
        ..Default::default()
    };

    assert!(pid3_isx(s0, s1, s2, t, &cfg)
        .unwrap_err()
        .to_string()
        .contains("validated only for Metric::Chebyshev"));
}
