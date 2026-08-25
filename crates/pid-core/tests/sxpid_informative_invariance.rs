//! Regression for the source-marginal invariance of averaged informative SxPID3 coordinates.
//!
//! The three empirical laws below reuse exactly the same source rows but have different target
//! channels: a constant target, an injective copy of the complete source tuple, and a target that
//! splits repeated occurrences within fixed source states.  The third channel exercises genuine
//! target-kernel reallocation rather than merely changing target labels.  Only the informative
//! cumulatives and their fixed Mobius transform are expected to be invariant.  Misinformative and
//! signed-net coordinates are explicit negative controls.

use std::collections::BTreeMap;

use pid_core::stable::categorical::{
    discrete_sxpid3_averaged, DiscreteSxPid3Result, SxAveragedAtom,
};
use pid_core::DiscreteMatRef;

type SourceRow = [usize; 3];
type AntichainKey = Vec<u8>;

// This is an order-independent semantic label roster, not the public result sequence.
const EXPECTED_ANTICHAINS: &[&[u8]] = &[
    &[1],
    &[2],
    &[3],
    &[4],
    &[5],
    &[6],
    &[7],
    &[1, 2],
    &[1, 4],
    &[1, 6],
    &[2, 4],
    &[2, 5],
    &[3, 4],
    &[3, 5],
    &[3, 6],
    &[5, 6],
    &[1, 2, 4],
    &[3, 5, 6],
];

#[derive(Clone, Copy)]
enum TargetChannel {
    Constant,
    CopiedSources,
    SplitOccurrences,
}

fn source_rows() -> Vec<SourceRow> {
    // Exercise unequal empirical weights while retaining every binary source tuple.
    const COUNTS: [usize; 8] = [1, 3, 2, 5, 4, 7, 6, 8];
    let mut rows = Vec::with_capacity(COUNTS.iter().sum());
    for (state, count) in COUNTS.into_iter().enumerate() {
        let row = [state & 1, (state >> 1) & 1, (state >> 2) & 1];
        rows.extend(std::iter::repeat_n(row, count));
    }
    rows
}

fn evaluate(rows: &[SourceRow], channel: TargetChannel) -> DiscreteSxPid3Result {
    let n = rows.len();
    let mut s0 = Vec::with_capacity(n);
    let mut s1 = Vec::with_capacity(n);
    let mut s2 = Vec::with_capacity(n);
    let target_columns = match channel {
        TargetChannel::CopiedSources => 3,
        TargetChannel::Constant | TargetChannel::SplitOccurrences => 1,
    };
    let mut target = Vec::with_capacity(target_columns * n);
    let mut source_occurrences = [0_usize; 8];

    for &row in rows {
        s0.push(row[0]);
        s1.push(row[1]);
        s2.push(row[2]);
        match channel {
            TargetChannel::Constant => target.push(0),
            TargetChannel::CopiedSources => target.extend(row),
            TargetChannel::SplitOccurrences => {
                let state = row[0] | (row[1] << 1) | (row[2] << 2);
                target.push(source_occurrences[state] & 1);
                source_occurrences[state] += 1;
            }
        }
    }

    discrete_sxpid3_averaged(
        DiscreteMatRef::new(&s0, n, 1).expect("valid source-zero matrix"),
        DiscreteMatRef::new(&s1, n, 1).expect("valid source-one matrix"),
        DiscreteMatRef::new(&s2, n, 1).expect("valid source-two matrix"),
        DiscreteMatRef::new(&target, n, target_columns).expect("valid target matrix"),
    )
    .expect("the categorical SxPID3 law is valid")
}

fn canonical_key(antichain: &[u8]) -> AntichainKey {
    let mut key = antichain.to_vec();
    key.sort_unstable();
    key
}

fn expected_keys() -> Vec<AntichainKey> {
    let mut keys = EXPECTED_ANTICHAINS
        .iter()
        .map(|antichain| canonical_key(antichain))
        .collect::<Vec<_>>();
    keys.sort(); // Align by semantic labels; Python and Rust use different display orders.
    keys
}

fn keyed_atoms(result: &DiscreteSxPid3Result) -> BTreeMap<AntichainKey, SxAveragedAtom> {
    assert_eq!(
        result.atoms.len(),
        result.antichains.len(),
        "every averaged atom must have exactly one aligned antichain label"
    );
    let mut atoms = BTreeMap::new();
    for antichain in &result.antichains {
        let key = canonical_key(antichain);
        let atom = result
            .atom(&key)
            .unwrap_or_else(|| panic!("missing averaged atom for antichain {key:?}"));
        assert!(
            atoms.insert(key.clone(), atom).is_none(),
            "duplicate antichain key {key:?}"
        );
    }
    assert_eq!(atoms.len(), 18, "the SxPID3 carrier must have 18 nodes");
    assert_eq!(
        atoms.keys().cloned().collect::<Vec<_>>(),
        expected_keys(),
        "the SxPID3 carrier labels must match the canonical three-source antichains"
    );
    atoms
}

/// Redundancy order: `lower <= upper` iff every collection in `upper` contains a collection in
/// `lower`.  The bitmasks encode source subsets.
fn antichain_leq(lower: &[u8], upper: &[u8]) -> bool {
    upper
        .iter()
        .all(|upper_mask| lower.iter().any(|lower_mask| lower_mask & !upper_mask == 0))
}

fn informative_cumulative(atoms: &BTreeMap<AntichainKey, SxAveragedAtom>, node: &[u8]) -> f64 {
    atoms
        .iter()
        .filter(|(lower, _)| antichain_leq(lower, node))
        .map(|(_, atom)| atom.informative_nats())
        .sum()
}

fn agrees_on_mask(anchor: &SourceRow, candidate: &SourceRow, mask: u8) -> bool {
    assert!(
        (1..=0b111).contains(&mask),
        "invalid source mask {mask:#05b}"
    );
    (0..3).all(|source| mask & (1 << source) == 0 || anchor[source] == candidate[source])
}

/// Independent source-only oracle for the averaged informative cumulative
/// `E[-ln P(union of source-agreement events)]`.
fn source_only_informative_cumulative(rows: &[SourceRow], node: &[u8]) -> f64 {
    assert!(!rows.is_empty());
    assert!(!node.is_empty());
    let sample_count = rows.len() as f64;
    rows.iter()
        .map(|anchor| {
            let event_count = rows
                .iter()
                .filter(|candidate| {
                    node.iter()
                        .any(|&mask| agrees_on_mask(anchor, candidate, mask))
                })
                .count();
            -(event_count as f64 / sample_count).ln()
        })
        .sum::<f64>()
        / sample_count
}

fn source_entropy(rows: &[SourceRow]) -> f64 {
    let mut counts = BTreeMap::<SourceRow, usize>::new();
    for &row in rows {
        *counts.entry(row).or_default() += 1;
    }
    let sample_count = rows.len() as f64;
    counts
        .values()
        .map(|&count| {
            let probability = count as f64 / sample_count;
            -probability * probability.ln()
        })
        .sum()
}

fn assert_close(actual: f64, expected: f64, context: &str) {
    let scale = actual.abs().max(expected.abs()).max(1.0);
    assert!(
        (actual - expected).abs() <= 2.0e-12 * scale,
        "{context}: expected {expected:.17e}, found {actual:.17e}"
    );
}

#[test]
fn averaged_informative_coordinates_depend_only_on_the_complete_source_marginal() {
    let rows = source_rows();
    let constant_target = evaluate(&rows, TargetChannel::Constant);
    let copied_target = evaluate(&rows, TargetChannel::CopiedSources);
    let split_target = evaluate(&rows, TargetChannel::SplitOccurrences);
    let constant_atoms = keyed_atoms(&constant_target);
    let copied_atoms = keyed_atoms(&copied_target);
    let split_atoms = keyed_atoms(&split_target);

    assert_eq!(
        constant_atoms.keys().collect::<Vec<_>>(),
        copied_atoms.keys().collect::<Vec<_>>(),
        "the target channel must not alter the stable SxPID3 carrier"
    );
    assert_eq!(
        constant_atoms.keys().collect::<Vec<_>>(),
        split_atoms.keys().collect::<Vec<_>>(),
        "target-kernel reallocation must not alter the stable SxPID3 carrier"
    );

    let mut misinformative_changed = false;
    let mut net_changed = false;
    for (node, constant_atom) in &constant_atoms {
        let copied_atom = copied_atoms
            .get(node)
            .unwrap_or_else(|| panic!("copied-target result is missing node {node:?}"));
        let split_atom = split_atoms
            .get(node)
            .unwrap_or_else(|| panic!("split-target result is missing node {node:?}"));

        assert_close(
            constant_atom.informative_nats(),
            copied_atom.informative_nats(),
            &format!("informative atom {node:?}"),
        );
        assert_close(
            constant_atom.informative_nats(),
            split_atom.informative_nats(),
            &format!("split-target informative atom {node:?}"),
        );

        let oracle = source_only_informative_cumulative(&rows, node);
        let constant_cumulative = informative_cumulative(&constant_atoms, node);
        let copied_cumulative = informative_cumulative(&copied_atoms, node);
        let split_cumulative = informative_cumulative(&split_atoms, node);
        assert_close(
            constant_cumulative,
            oracle,
            &format!("constant-target informative cumulative {node:?}"),
        );
        assert_close(
            copied_cumulative,
            oracle,
            &format!("copied-target informative cumulative {node:?}"),
        );
        assert_close(
            split_cumulative,
            oracle,
            &format!("split-target informative cumulative {node:?}"),
        );

        for (channel, atom) in [
            ("constant", constant_atom),
            ("copied", copied_atom),
            ("split", split_atom),
        ] {
            assert_close(
                atom.net_nats(),
                atom.informative_nats() - atom.misinformative_nats(),
                &format!("{channel}-target atom net identity {node:?}"),
            );
        }

        misinformative_changed |=
            (constant_atom.misinformative_nats() - copied_atom.misinformative_nats()).abs()
                > 1.0e-8;
        net_changed |= (constant_atom.net_nats() - copied_atom.net_nats()).abs() > 1.0e-8;
    }

    // These target channels are deliberately different.  Their joint MIs, minus coordinates,
    // and signed-net coordinates prevent accidental promotion of the informative-only theorem.
    let entropy = source_entropy(&rows);
    assert_close(
        constant_target.mi_s0s1s2_t,
        0.0,
        "constant-target joint mutual information",
    );
    assert_close(
        copied_target.mi_s0s1s2_t,
        entropy,
        "copied-target joint mutual information",
    );
    assert!(
        split_target.mi_s0s1s2_t > 0.0 && split_target.mi_s0s1s2_t < entropy,
        "the split target must induce a nontrivial, non-injective target kernel"
    );
    assert!(entropy > 1.0, "source law must be non-degenerate");
    assert!(
        misinformative_changed,
        "misinformative atoms must not be inferred invariant"
    );
    assert!(
        net_changed,
        "signed-net atoms must not be inferred invariant"
    );
}
