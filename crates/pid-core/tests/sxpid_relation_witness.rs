//! Exact regression for the witness pair in Lyu--Clark--Raviv (arXiv:2604.03869v2).
//!
//! The paper assigns the same three coordinate-recoverability descriptors to both systems.
//! Those stipulated descriptors are not shared-exclusions PID atoms.  The paper-defined SxPID
//! event probabilities distinguish the systems, and the resulting 18-atom vectors reconstruct
//! their different mutual informations.

use pid_core::stable::categorical::{discrete_sxpid3, DiscreteSxPid3Result, SxAveragedAtom};
use pid_core::DiscreteMatRef;

type Row = ([usize; 3], [usize; 3], [usize; 3], [usize; 3]);

fn evaluate(rows: &[Row]) -> DiscreteSxPid3Result {
    let n = rows.len();
    let mut s0 = Vec::with_capacity(3 * n);
    let mut s1 = Vec::with_capacity(3 * n);
    let mut s2 = Vec::with_capacity(3 * n);
    let mut target = Vec::with_capacity(3 * n);

    for &(a, b, c, t) in rows {
        s0.extend(a);
        s1.extend(b);
        s2.extend(c);
        target.extend(t);
    }

    discrete_sxpid3(
        DiscreteMatRef::new(&s0, n, 3).expect("valid first-source matrix"),
        DiscreteMatRef::new(&s1, n, 3).expect("valid second-source matrix"),
        DiscreteMatRef::new(&s2, n, 3).expect("valid third-source matrix"),
        DiscreteMatRef::new(&target, n, 3).expect("valid target matrix"),
    )
    .expect("the exact categorical witness is valid")
}

fn hat_system() -> Vec<Row> {
    let mut rows = Vec::with_capacity(64);
    for x1 in 0..=1 {
        for x2 in 0..=1 {
            for x4 in 0..=1 {
                for x5 in 0..=1 {
                    for x7 in 0..=1 {
                        for x8 in 0..=1 {
                            let x3 = x1 ^ x2;
                            let x6 = x4 ^ x5;
                            let x9 = x7 ^ x8;
                            rows.push(([x1, x4, x7], [x2, x5, x8], [x3, x6, x9], [x1, x5, x9]));
                        }
                    }
                }
            }
        }
    }
    rows
}

fn tilde_system() -> Vec<Row> {
    let mut rows = Vec::with_capacity(32);
    for x1 in 0..=1 {
        for x2 in 0..=1 {
            for x4 in 0..=1 {
                for x5 in 0..=1 {
                    for x7 in 0..=1 {
                        let x3 = x1 ^ x2;
                        let x6 = x4 ^ x5;
                        let x9 = x1 ^ x5;
                        let x8 = x7 ^ x1 ^ x5;
                        rows.push(([x1, x4, x7], [x2, x5, x8], [x3, x6, x9], [x1, x5, x9]));
                    }
                }
            }
        }
    }
    rows
}

fn assert_close(actual: f64, expected: f64, context: &str) {
    let scale = actual.abs().max(expected.abs()).max(1.0);
    assert!(
        (actual - expected).abs() <= 2.0e-13 * scale,
        "{context}: expected {expected:.17e}, got {actual:.17e}"
    );
}

fn atom(result: &DiscreteSxPid3Result, antichain: &[u8]) -> SxAveragedAtom {
    result
        .atom(antichain)
        .unwrap_or_else(|| panic!("missing antichain {antichain:?}"))
}

fn assert_components(
    result: &DiscreteSxPid3Result,
    nodes: &[&[u8]],
    informative_ratio: f64,
    misinformative_ratio: f64,
    net_ratio: f64,
    system: &str,
) {
    for &node in nodes {
        let value = atom(result, node);
        assert_close(
            value.informative_nats(),
            informative_ratio.ln(),
            &format!("{system} {node:?} informative atom"),
        );
        assert_close(
            value.misinformative_nats(),
            misinformative_ratio.ln(),
            &format!("{system} {node:?} misinformative atom"),
        );
        assert_close(
            value.net_nats(),
            net_ratio.ln(),
            &format!("{system} {node:?} net atom"),
        );
    }
}

fn assert_exact_product(numerators: &[u128], denominators: &[u128], expected: u128) {
    let numerator = numerators.iter().copied().product::<u128>();
    let denominator = denominators.iter().copied().product::<u128>();
    assert_eq!(numerator, expected * denominator);
}

#[test]
fn lcr_recoverability_witnesses_have_distinct_sxpid_atoms_and_exact_reconstruction() {
    let hat = evaluate(&hat_system());
    let tilde = evaluate(&tilde_system());

    assert_eq!(hat.antichains, tilde.antichains);
    assert_eq!(hat.atoms.len(), 18);
    assert_eq!(tilde.atoms.len(), 18);
    assert_close(hat.mi_s0s1s2_t, 3.0 * std::f64::consts::LN_2, "hat MI");
    assert_close(tilde.mi_s0s1s2_t, 2.0 * std::f64::consts::LN_2, "tilde MI");

    let singleton_bottom: &[&[u8]] = &[&[0b001, 0b010, 0b100]];
    let singleton_pairs: &[&[u8]] = &[&[0b001, 0b010], &[0b001, 0b100], &[0b010, 0b100]];
    let recovery_labels: &[&[u8]] = &[&[0b001, 0b110], &[0b010, 0b101], &[0b011, 0b100]];
    let pair_cover: &[&[u8]] = &[&[0b011, 0b101, 0b110]];

    assert_components(&hat, singleton_bottom, 32.0 / 11.0, 2.0, 16.0 / 11.0, "hat");
    assert_components(
        &hat,
        singleton_pairs,
        22.0 / 15.0,
        4.0 / 3.0,
        11.0 / 10.0,
        "hat",
    );
    assert_components(
        &hat,
        recovery_labels,
        225.0 / 176.0,
        9.0 / 8.0,
        25.0 / 22.0,
        "hat",
    );
    assert_components(
        &hat,
        pair_cover,
        11264.0 / 3375.0,
        32.0 / 27.0,
        352.0 / 125.0,
        "hat",
    );

    assert_components(
        &tilde,
        singleton_bottom,
        16.0 / 5.0,
        2.0,
        8.0 / 5.0,
        "tilde",
    );
    assert_components(
        &tilde,
        singleton_pairs,
        10.0 / 7.0,
        4.0 / 3.0,
        15.0 / 14.0,
        "tilde",
    );
    assert_components(
        &tilde,
        recovery_labels,
        49.0 / 40.0,
        9.0 / 8.0,
        49.0 / 45.0,
        "tilde",
    );
    assert_components(
        &tilde,
        pair_cover,
        640.0 / 343.0,
        32.0 / 27.0,
        540.0 / 343.0,
        "tilde",
    );

    // Exact-product oracle for the displayed averaged atoms.  The tracked independent Python
    // event-count checker derives these ratios without importing pid-rs and also establishes that
    // every local atom is constant across each witness's equiprobable support.  The multiplicities
    // are the three symmetric nodes in each middle family.  These integer identities establish
    // reconstruction before any log or binary64 operation is evaluated.
    assert_exact_product(
        &[16, 11_u128.pow(3), 25_u128.pow(3), 352],
        &[11, 10_u128.pow(3), 22_u128.pow(3), 125],
        8,
    );
    assert_exact_product(
        &[8, 15_u128.pow(3), 49_u128.pow(3), 540],
        &[5, 14_u128.pow(3), 45_u128.pow(3), 343],
        4,
    );

    let designated = singleton_bottom
        .iter()
        .chain(singleton_pairs)
        .chain(recovery_labels)
        .chain(pair_cover)
        .copied()
        .collect::<Vec<_>>();
    for antichain in &hat.antichains {
        if !designated.iter().any(|candidate| {
            candidate.len() == antichain.len()
                && candidate.iter().all(|mask| antichain.contains(mask))
        }) {
            assert_close(atom(&hat, antichain).net_nats(), 0.0, "hat zero atom");
            assert_close(atom(&tilde, antichain).net_nats(), 0.0, "tilde zero atom");
        }
    }

    let hat_sum: f64 = hat.atoms.iter().map(|value| value.net_nats()).sum();
    let tilde_sum: f64 = tilde.atoms.iter().map(|value| value.net_nats()).sum();
    assert_close(hat_sum, hat.mi_s0s1s2_t, "hat atom reconstruction");
    assert_close(tilde_sum, tilde.mi_s0s1s2_t, "tilde atom reconstruction");

    let max_delta = hat
        .atoms
        .iter()
        .zip(&tilde.atoms)
        .map(|(left, right)| (left.net_nats() - right.net_nats()).abs())
        .fold(0.0_f64, f64::max);
    assert_close(
        max_delta,
        (352.0_f64 / 125.0).ln() - (540.0_f64 / 343.0).ln(),
        "maximum atom-vector difference",
    );
    assert!(max_delta > 0.5, "the SxPID atom vectors must be distinct");
}

#[test]
fn stipulated_recoverability_descriptor_mutation_is_rejected_as_sxpid() {
    let hat = evaluate(&hat_system());
    let tilde = evaluate(&tilde_system());
    let recovery_labels: &[&[u8]] = &[&[0b001, 0b110], &[0b010, 0b101], &[0b011, 0b100]];

    // The comparison paper stipulates three one-bit coordinate-recoverability descriptors and
    // zeros elsewhere.  That descriptor vector happens to sum to the hat system's three-bit MI,
    // but it overcounts the tilde system, whose target bits satisfy x9 = x1 XOR x5.
    let stipulated_sum = 3.0 * std::f64::consts::LN_2;
    assert_close(stipulated_sum, hat.mi_s0s1s2_t, "hat descriptor sum");
    assert!(
        (stipulated_sum - tilde.mi_s0s1s2_t).abs() > 0.5,
        "the stipulated vector must fail tilde WESP reconstruction"
    );

    for label in recovery_labels {
        assert!(
            (atom(&hat, label).net_nats() - std::f64::consts::LN_2).abs() > 0.5,
            "hat recovery descriptor must not be substituted for its SxPID atom"
        );
        assert!(
            (atom(&tilde, label).net_nats() - std::f64::consts::LN_2).abs() > 0.5,
            "tilde recovery descriptor must not be substituted for its SxPID atom"
        );
    }

    // SxPID also assigns nonzero net increments outside the three stipulated labels.  This is the
    // distribution-dependent relational information that the mutation discards.
    for label in [
        &[0b001, 0b010, 0b100][..],
        &[0b001, 0b010][..],
        &[0b011, 0b101, 0b110][..],
    ] {
        assert!(atom(&hat, label).net_nats() > 0.0);
        assert!(atom(&tilde, label).net_nats() > 0.0);
    }
}
