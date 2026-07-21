//! General n-source discrete SxPID: agreement with the specialized 2-/3-source paths, plus
//! 4-source axioms (the source count IDTxl's SxPID supports).

use pid_core::stable::categorical::{discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n};
use pid_core::DiscreteMatRef;

fn leq(a: &[u8], b: &[u8]) -> bool {
    b.iter().all(|bb| a.iter().any(|aa| aa & !bb == 0))
}

#[test]
fn nsource_matches_sxpid2_exactly() {
    // AND gate; the general lattice path must reproduce discrete_sxpid2 within 1e-12.
    let rows = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)];
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..4 {
        for &(a, b, c) in &rows {
            s1.push(a);
            s2.push(b);
            t.push(c);
        }
    }
    let n = rows.len() * 4;
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();

    let two = discrete_sxpid2(s1, s2, t).unwrap();
    let general = discrete_sxpid_n(&[s1, s2], t).unwrap();

    // Map the named 2-source atoms onto the general antichain keys.
    let g = |sets: &[u8]| general.atom(sets).unwrap();
    assert!((g(&[0b01]).net_nats() - two.unq1.net_nats()).abs() < 1e-12);
    assert!((g(&[0b10]).net_nats() - two.unq2.net_nats()).abs() < 1e-12);
    assert!((g(&[0b11]).net_nats() - two.syn.net_nats()).abs() < 1e-12);
    assert!((g(&[0b01, 0b10]).net_nats() - two.red.net_nats()).abs() < 1e-12);
    // informative/misinformative split too.
    assert!((g(&[0b01, 0b10]).informative_nats() - two.red.informative_nats()).abs() < 1e-12);
    assert!((g(&[0b01, 0b10]).misinformative_nats() - two.red.misinformative_nats()).abs() < 1e-12);
    assert_eq!(general.antichains.len(), 4);
}

#[test]
fn nsource_matches_sxpid3_exactly() {
    // 3-way XOR (HASH); general path must reproduce discrete_sxpid3 on all 18 atoms.
    let (mut s0, mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for _ in 0..4 {
        for a in 0..2 {
            for b in 0..2 {
                for c in 0..2 {
                    s0.push(a);
                    s1.push(b);
                    s2.push(c);
                    t.push(a ^ b ^ c);
                }
            }
        }
    }
    let n = 4 * 8;
    let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();

    let three = discrete_sxpid3(s0, s1, s2, t).unwrap();
    let general = discrete_sxpid_n(&[s0, s1, s2], t).unwrap();
    assert_eq!(general.antichains.len(), 18);

    // Every antichain in the 3-source result has the same atom in the general result.
    for (sets, atom) in three.antichains.iter().zip(&three.atoms) {
        let g = general
            .atom(sets)
            .expect("antichain present in general lattice");
        assert!(
            (g.net_nats() - atom.net_nats()).abs() < 1e-12,
            "mismatch at {sets:?}"
        );
        assert!((g.informative_nats() - atom.informative_nats()).abs() < 1e-12);
        assert!((g.misinformative_nats() - atom.misinformative_nats()).abs() < 1e-12);
    }
}

#[test]
fn nsource_lattice_has_166_antichains_for_4_sources() {
    // The 4-source redundancy lattice has 166 antichains (Dedekind D(4)=168, minus the empty
    // antichain and the {∅} antichain). A 4-way giant bit: all info is in the all-singletons
    // (global) redundancy; reconstruction holds.
    let (mut s0, mut s1, mut s2, mut s3, mut t) =
        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for _ in 0..4 {
        for b in [0, 1] {
            s0.push(b);
            s1.push(b);
            s2.push(b);
            s3.push(b);
            t.push(b);
        }
    }
    let n = 4 * 2;
    let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let s3 = DiscreteMatRef::new(&s3, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();

    let r = discrete_sxpid_n(&[s0, s1, s2, s3], t).unwrap();
    assert_eq!(r.antichains.len(), 166, "4-source antichain count");
    assert_eq!(r.atoms.len(), 166);
    assert_eq!(r.subset_mis.len(), 15);

    // Reconstruction: Σ atoms = joint MI = ln 2 (giant bit).
    let sum: f64 = r.atoms.iter().map(|a| a.net_nats()).sum();
    assert!(
        (sum - r.joint_mi).abs() < 1e-9,
        "Σ={sum} joint_mi={}",
        r.joint_mi
    );
    assert!((r.joint_mi - 2.0_f64.ln()).abs() < 1e-9);
    assert!((r.joint_mi - r.subset_mis[14]).abs() < 1e-12);

    for mask in 1u8..=0b1111 {
        let downset_sum: f64 = r
            .antichains
            .iter()
            .zip(&r.atoms)
            .filter(|(antichain, _)| leq(antichain, &[mask]))
            .map(|(_, atom)| atom.net_nats())
            .sum();
        assert!(
            (downset_sum - r.subset_mis[usize::from(mask - 1)]).abs() < 1e-9,
            "self-redundancy mismatch for source mask {mask:#06b}"
        );
    }

    // All shared information sits in the all-singletons redundancy node.
    let red_all = r.atom(&[0b0001, 0b0010, 0b0100, 0b1000]).unwrap();
    assert!(
        (red_all.net_nats() - 2.0_f64.ln()).abs() < 1e-9,
        "global red = {}",
        red_all.net_nats()
    );
}

#[test]
fn nsource_4source_symmetry_and_reconstruction() {
    // T = S0; S1,S2,S3 noise. Fully enumerate {0,1}^4 so symmetry among S1,S2,S3 is exact.
    let (mut s0, mut s1, mut s2, mut s3, mut t) =
        (Vec::new(), Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for _ in 0..3 {
        for a in 0..2 {
            for b in 0..2 {
                for c in 0..2 {
                    for d in 0..2 {
                        s0.push(a);
                        s1.push(b);
                        s2.push(c);
                        s3.push(d);
                        t.push(a); // T = S0
                    }
                }
            }
        }
    }
    let n = 3 * 16;
    let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let s3 = DiscreteMatRef::new(&s3, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();

    let r = discrete_sxpid_n(&[s0, s1, s2, s3], t).unwrap();
    let sum: f64 = r.atoms.iter().map(|a| a.net_nats()).sum();
    assert!((sum - r.joint_mi).abs() < 1e-9);
    assert!((r.joint_mi - 2.0_f64.ln()).abs() < 1e-9); // I(S0..S3;T)=H(S0)=ln2

    // Exact symmetry among the noise sources S1,S2,S3: their unique atoms coincide.
    let u1 = r.atom(&[0b0010]).unwrap().net_nats();
    let u2 = r.atom(&[0b0100]).unwrap().net_nats();
    let u3 = r.atom(&[0b1000]).unwrap().net_nats();
    assert!(
        (u1 - u2).abs() < 1e-12 && (u2 - u3).abs() < 1e-12,
        "u1={u1} u2={u2} u3={u3}"
    );

    // net == informative − misinformative everywhere.
    for a in &r.atoms {
        assert_eq!(a.net_nats(), a.informative_nats() - a.misinformative_nats());
    }
}
