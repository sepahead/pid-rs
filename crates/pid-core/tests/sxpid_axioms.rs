//! Property/axiom tests for the discrete shared-exclusions PID (`i^sx_∩`), and the honest
//! `I_min`-vs-`i^sx` comparison on the two-bit COPY (the Harder et al. 2013 identity axiom).

mod common;
use common::Rng64;

use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n, DiscreteSxPid2Result, SxPointwiseAtom,
};
use pid_core::stable::imin::imin_pid2;
use pid_core::DiscreteMatRef;

/// One canonical gate represented by truth-table rows `(s1, s2, t)`.
type Gate = &'static [(usize, usize, usize)];

/// Canonical 2-source gates used by several axiom tests: AND, XOR, UNQ (`T = S1`),
/// and the two-bit COPY (with its 4-value target alphabet).
const GATES: [Gate; 4] = [
    &[(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)],
    &[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)],
    &[(0, 0, 0), (0, 1, 0), (1, 0, 1), (1, 1, 1)],
    &[(0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 3)],
];

fn run2(rows: &[(usize, usize, usize)]) -> DiscreteSxPid2Result {
    let reps = 4;
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..reps {
        for &(a, b, c) in rows {
            s1.push(a);
            s2.push(b);
            t.push(c);
        }
    }
    let n = rows.len() * reps;
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();
    discrete_sxpid2(s1, s2, t).unwrap()
}

#[test]
fn reconstruction_and_self_redundancy() {
    // AND gate.
    let r = run2(&[(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]);
    let sum = r.unq1.net_nats() + r.unq2.net_nats() + r.syn.net_nats() + r.red.net_nats();
    assert!(
        (sum - r.mi_s1s2_t).abs() < 1e-9,
        "reconstruction: {sum} vs {}",
        r.mi_s1s2_t
    );
    // Self-redundancy: information below the marginal node {i} sums to I(S_i;T).
    assert!((r.unq1.net_nats() + r.red.net_nats() - r.mi_s1_t).abs() < 1e-9);
    assert!((r.unq2.net_nats() + r.red.net_nats() - r.mi_s2_t).abs() < 1e-9);
}

#[test]
fn net_equals_informative_minus_misinformative() {
    let r = run2(&[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]); // XOR
    for p in &r.pointwise {
        for a in [p.unq1, p.unq2, p.syn, p.red] {
            assert_eq!(a.net_nats(), a.informative_nats() - a.misinformative_nats());
        }
    }
    for a in [r.unq1, r.unq2, r.syn, r.red] {
        assert_eq!(a.net_nats(), a.informative_nats() - a.misinformative_nats());
    }
}

#[test]
fn negative_atoms_are_real() {
    // XOR: pointwise AND averaged redundancy are negative — must not be clamped.
    let r = run2(&[(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)]);
    assert!(
        r.red.net_nats() < 0.0,
        "XOR averaged red should be negative; got {}",
        r.red.net_nats()
    );
    assert!(r.pointwise.iter().all(|p| p.red.net_nats() < 0.0));
}

#[test]
fn symmetry_under_source_swap() {
    let rows = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)]; // AND
    let r = run2(&rows);
    let swapped: Vec<(usize, usize, usize)> = rows.iter().map(|&(a, b, c)| (b, a, c)).collect();
    let rs = run2(&swapped);
    assert!((r.unq1.net_nats() - rs.unq2.net_nats()).abs() < 1e-12);
    assert!((r.unq2.net_nats() - rs.unq1.net_nats()).abs() < 1e-12);
    assert!((r.red.net_nats() - rs.red.net_nats()).abs() < 1e-12);
    assert!((r.syn.net_nats() - rs.syn.net_nats()).abs() < 1e-12);
}

#[test]
fn sxpid3_reconstruction_and_symmetry() {
    // T = S0 (unique to source 0); S0,S1,S2 fully enumerated over {0,1}^3 so the empirical law is
    // EXACTLY symmetric under S1↔S2. Reconstruction: Σ_α Π(α) = I(S0,S1,S2;T) = H(S0) = ln 2.
    let (mut s0, mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
    for _ in 0..4 {
        for a in 0..2 {
            for b in 0..2 {
                for c in 0..2 {
                    s0.push(a);
                    s1.push(b);
                    s2.push(c);
                    t.push(a); // T = S0
                }
            }
        }
    }
    let n = 4 * 8;
    let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
    let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let t = DiscreteMatRef::new(&t, n, 1).unwrap();
    let r = discrete_sxpid3(s0, s1, s2, t).unwrap();

    // Reconstruction.
    let sum: f64 = r.atoms.iter().map(|a| a.net_nats()).sum();
    assert!(
        (sum - r.mi_s0s1s2_t).abs() < 1e-9,
        "Σ={sum} vs joint MI {}",
        r.mi_s0s1s2_t
    );
    assert!((r.mi_s0s1s2_t - 2.0_f64.ln()).abs() < 1e-9);

    // Exact symmetry under S1↔S2: the unique-to-1 and unique-to-2 atoms coincide, as do the
    // {{0},{1}}-type pairs. (1=bit0 of source0, 2=bit1 of source1, 4=bit2 of source2.)
    let u1 = r.atom(&[0b010]).unwrap().net_nats();
    let u2 = r.atom(&[0b100]).unwrap().net_nats();
    assert!((u1 - u2).abs() < 1e-12, "unq1={u1} unq2={u2}");
    let p01 = r.atom(&[0b001, 0b010]).unwrap().net_nats(); // {{0},{1}}
    let p02 = r.atom(&[0b001, 0b100]).unwrap().net_nats(); // {{0},{2}}
    assert!(
        (p01 - p02).abs() < 1e-12,
        "{{0}}{{1}}={p01} {{0}}{{2}}={p02}"
    );

    // Net atom equals informative − misinformative everywhere.
    for a in &r.atoms {
        assert_eq!(a.net_nats(), a.informative_nats() - a.misinformative_nats());
    }
}

/// MGW 2021, **Theorem IV.3**: the informative and misinformative parts of every *pointwise*
/// atom are non-negative — only their difference (the net atom) may be negative. Checked on
/// the canonical gates and a skewed random-system sweep across 2, 3, and 4 sources (the
/// averaged parts inherit non-negativity as full-realization probability-weighted sums).
#[test]
fn mgw_theorem_iv3_pointwise_plus_minus_parts_nonnegative() {
    const TOL: f64 = -1e-12; // observed worst round-off is ~-5e-15

    for rows in GATES {
        let r = run2(rows);
        for p in &r.pointwise {
            for a in [p.unq1, p.unq2, p.syn, p.red] {
                assert!(
                    a.informative_nats() >= TOL && a.misinformative_nats() >= TOL,
                    "Thm IV.3 violated on gate {rows:?}: inf={} misinf={}",
                    a.informative_nats(),
                    a.misinformative_nats()
                );
            }
        }
        for a in [r.unq1, r.unq2, r.syn, r.red] {
            assert!(a.informative_nats() >= TOL && a.misinformative_nats() >= TOL);
        }
    }

    // Random sweep through the general n-source lattice path (2, 3, and 4 sources).
    let mut rng = Rng64::new(0x71E0_4E11);
    for trial in 0..12usize {
        let n_sources = 2 + trial % 3;
        let n = 80 + trial * 13;
        let alpha = 2 + trial % 2;
        let cols: Vec<Vec<usize>> = (0..n_sources)
            .map(|_| {
                (0..n)
                    .map(|_| {
                        let u = rng.next_f64();
                        (u * u * alpha as f64) as usize
                    })
                    .collect()
            })
            .collect();
        let t: Vec<usize> = (0..n)
            .map(|i| {
                let mix: usize =
                    cols.iter().map(|c| c[i]).sum::<usize>() + (rng.next_u64() as usize % 2);
                mix % alpha
            })
            .collect();
        let mats: Vec<DiscreteMatRef<'_>> = cols
            .iter()
            .map(|c| DiscreteMatRef::new(c, n, 1).unwrap())
            .collect();
        let tm = DiscreteMatRef::new(&t, n, 1).unwrap();
        let r = discrete_sxpid_n(&mats, tm).unwrap();
        for p in &r.pointwise {
            for a in &p.atoms {
                assert!(
                    a.informative_nats() >= TOL && a.misinformative_nats() >= TOL,
                    "Thm IV.3 violated (trial {trial}, {n_sources} sources): inf={} misinf={}",
                    a.informative_nats(),
                    a.misinformative_nats()
                );
            }
        }
    }
}

/// MGW 2021, **Theorem IV.2**: the cumulative node values `i^±_∩(t:β) = Σ_{α ⪯ β} π^±(α)` are
/// monotone along the redundancy-lattice order (`α ⪯ β` ⇔ every `b ∈ β` contains some
/// `a ∈ α`). Verified pointwise on the 2-source lattice for the canonical gates, and on the
/// full 18-node 3-source lattice (pointwise), reconstructing down-set sums from the atoms.
#[test]
fn mgw_theorem_iv2_cumulative_parts_monotone_on_lattice() {
    const TOL: f64 = 1e-9;

    // 2-source lattice: {1}{2} ⪯ {1} ⪯ {12} and {1}{2} ⪯ {2} ⪯ {12}.
    for rows in GATES {
        let r = run2(rows);
        for p in &r.pointwise {
            for part in [
                |a: &SxPointwiseAtom| a.informative_nats(),
                |a: &SxPointwiseAtom| a.misinformative_nats(),
            ] {
                let bot = part(&p.red);
                let n1 = part(&p.red) + part(&p.unq1);
                let n2 = part(&p.red) + part(&p.unq2);
                let top = n1 + part(&p.unq2) + part(&p.syn);
                assert!(
                    bot <= n1 + TOL && bot <= n2 + TOL,
                    "Thm IV.2: bottom above marginal"
                );
                assert!(
                    n1 <= top + TOL && n2 <= top + TOL,
                    "Thm IV.2: marginal above top"
                );
            }
        }
    }

    // 3-source lattice (18 nodes): standard antichain order over source-subset bitmasks.
    fn leq(a: &[u8], b: &[u8]) -> bool {
        b.iter().all(|bb| a.iter().any(|aa| aa & bb == *aa))
    }
    // Two structured systems (T = S0; 3-way XOR) exercised over the full support.
    for gate in [0usize, 1] {
        let (mut s0, mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new(), Vec::new());
        for a in 0..2usize {
            for b in 0..2usize {
                for c in 0..2usize {
                    s0.push(a);
                    s1.push(b);
                    s2.push(c);
                    t.push(if gate == 0 { a } else { a ^ b ^ c });
                }
            }
        }
        let n = 8;
        let s0 = DiscreteMatRef::new(&s0, n, 1).unwrap();
        let s1 = DiscreteMatRef::new(&s1, n, 1).unwrap();
        let s2 = DiscreteMatRef::new(&s2, n, 1).unwrap();
        let tm = DiscreteMatRef::new(&t, n, 1).unwrap();
        let r = discrete_sxpid3(s0, s1, s2, tm).unwrap();

        let m = r.antichains.len();
        assert_eq!(m, 18);
        for p in &r.pointwise {
            for part in [
                |a: &SxPointwiseAtom| a.informative_nats(),
                |a: &SxPointwiseAtom| a.misinformative_nats(),
            ] {
                // cum(β) = Σ_{α ⪯ β} π(α), i.e. the down-set sum of atoms.
                let cum: Vec<f64> = (0..m)
                    .map(|i| {
                        (0..m)
                            .filter(|&k| leq(&r.antichains[k], &r.antichains[i]))
                            .map(|k| part(&p.atoms[k]))
                            .sum()
                    })
                    .collect();
                for i in 0..m {
                    for j in 0..m {
                        if leq(&r.antichains[i], &r.antichains[j]) {
                            assert!(
                                cum[i] <= cum[j] + TOL,
                                "Thm IV.2 violated (gate {gate}): cum±({:?})={} > cum±({:?})={}",
                                r.antichains[i],
                                cum[i],
                                r.antichains[j],
                                cum[j]
                            );
                        }
                    }
                }
            }
        }
    }
}

#[test]
fn identity_axiom_imin_overattributes_vs_sxpid() {
    // Two-bit COPY of INDEPENDENT sources: T = (S1, S2), encoded as 2*s1 + s2.
    // Harder et al. (2013) identity axiom: redundancy should be I(S1;S2) = 0.
    //   - I_min assigns the MAXIMAL 1 bit (= min of the marginal MIs) — the classic
    //     over-attribution that motivated SxPID.
    //   - i^sx assigns only log2(4/3) ≈ 0.415 bits — strictly less (though still > 0: SxPID
    //     gives up the averaged identity axiom even at two sources in exchange for its
    //     pointwise structure. Identity and non-negativity are jointly satisfiable at two
    //     sources — e.g. BROJA: Bertschinger, Rauh, Olbrich, Jost & Ay 2014, Entropy 16(4) —
    //     but identity is incompatible with non-negativity for three or more sources:
    //     Rauh, Bertschinger, Olbrich & Jost 2014, ISIT / arXiv:1404.3146).
    let rows = [(0, 0, 0), (0, 1, 1), (1, 0, 2), (1, 1, 3)];
    let reps = 4;
    let (mut s1, mut s2, mut t) = (Vec::new(), Vec::new(), Vec::new());
    for _ in 0..reps {
        for &(a, b, c) in &rows {
            s1.push(a);
            s2.push(b);
            t.push(c);
        }
    }
    let n = rows.len() * reps;
    let s1m = DiscreteMatRef::new(&s1, n, 1).unwrap();
    let s2m = DiscreteMatRef::new(&s2, n, 1).unwrap();
    let tm = DiscreteMatRef::new(&t, n, 1).unwrap();

    let imin = imin_pid2(s1m, s2m, tm).unwrap();
    let sx = discrete_sxpid2(
        DiscreteMatRef::new(&s1, n, 1).unwrap(),
        DiscreteMatRef::new(&s2, n, 1).unwrap(),
        DiscreteMatRef::new(&t, n, 1).unwrap(),
    )
    .unwrap();

    let ln2 = 2.0_f64.ln();
    let ln_4_3 = (4.0_f64 / 3.0).ln();

    assert!(
        (imin.redundancy - ln2).abs() < 1e-9,
        "I_min copy redundancy should be 1 bit (ln2); got {}",
        imin.redundancy
    );
    assert!(
        (sx.red.net_nats() - ln_4_3).abs() < 1e-9,
        "i^sx copy redundancy should be log(4/3); got {}",
        sx.red.net_nats()
    );
    // The headline: SxPID attributes strictly less spurious redundancy than I_min.
    assert!(
        sx.red.net_nats() < imin.redundancy - 1e-3,
        "i^sx ({}) should attribute less redundancy than I_min ({})",
        sx.red.net_nats(),
        imin.redundancy
    );
}
