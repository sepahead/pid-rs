#![cfg(feature = "experimental-pipelines")]

//! Deterministic adversarial properties for the exact categorical SxPID and quantized `I_min`
//! paths. These complement the closed-form gate fixtures with skewed arbitrary empirical laws.

use pid_core::experimental::pipelines::{
    exploratory_same_sample_quantized_imin_pid2 as discrete_pid2,
    exploratory_same_sample_quantized_imin_pid3 as discrete_pid3,
    exploratory_same_sample_quantized_sxpid2 as quantized_sxpid2,
};
use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid3, discrete_sxpid_n, DiscreteInputEncoding, SxAtom,
};
use pid_core::{DiscreteMatRef, MatRef};

fn next(state: &mut u64) -> u64 {
    *state = state
        .wrapping_mul(6_364_136_223_846_793_005)
        .wrapping_add(1_442_695_040_888_963_407);
    *state
}

fn skewed_ternary(state: &mut u64) -> usize {
    match (next(state) >> 32) % 10 {
        0..=5 => 0,
        6..=8 => 1,
        _ => 2,
    }
}

fn assert_atom_finite_and_parts_nonnegative(atom: SxAtom, context: &str) {
    assert!(atom.informative.is_finite(), "{context}: {atom:?}");
    assert!(atom.misinformative.is_finite(), "{context}: {atom:?}");
    assert!(atom.net.is_finite(), "{context}: {atom:?}");
    assert!(atom.informative >= -2.0e-12, "{context}: {atom:?}");
    assert!(atom.misinformative >= -2.0e-12, "{context}: {atom:?}");
    assert_eq!(atom.net, atom.informative - atom.misinformative);
}

fn leq(a: &[u8], b: &[u8]) -> bool {
    b.iter().all(|&bb| a.iter().any(|&aa| aa & !bb == 0))
}

fn remap_mask_to_permuted_sources(mask: u8, new_to_old: [usize; 4]) -> u8 {
    new_to_old
        .iter()
        .enumerate()
        .fold(0_u8, |mapped, (new_index, &old_index)| {
            if mask & (1 << old_index) == 0 {
                mapped
            } else {
                mapped | (1 << new_index)
            }
        })
}

#[test]
fn randomized_discrete_pid2_invariants() {
    for seed in 1..=500_u64 {
        let mut state = seed;
        let n = 8 + (next(&mut state) as usize % 57);
        let mut s1 = Vec::with_capacity(n);
        let mut s2 = Vec::with_capacity(n);
        let mut target = Vec::with_capacity(n);
        for _ in 0..n {
            s1.push(skewed_ternary(&mut state));
            s2.push(skewed_ternary(&mut state));
            target.push(skewed_ternary(&mut state));
        }
        let exact = discrete_sxpid2(
            DiscreteMatRef::new(&s1, n, 1).unwrap(),
            DiscreteMatRef::new(&s2, n, 1).unwrap(),
            DiscreteMatRef::new(&target, n, 1).unwrap(),
        )
        .unwrap();
        for (name, atom) in [
            ("unq1", exact.unq1),
            ("unq2", exact.unq2),
            ("syn", exact.syn),
            ("red", exact.red),
        ] {
            assert_atom_finite_and_parts_nonnegative(atom, &format!("seed={seed} {name}"));
        }
        for point in &exact.pointwise {
            for atom in [point.unq1, point.unq2, point.syn, point.red] {
                assert_atom_finite_and_parts_nonnegative(atom, &format!("seed={seed} point"));
            }
        }
        let sum = exact.unq1.net + exact.unq2.net + exact.syn.net + exact.red.net;
        assert!((sum - exact.mi_s1s2_t).abs() < 2.0e-11, "seed={seed}");
        assert!((exact.unq1.net + exact.red.net - exact.mi_s1_t).abs() < 2.0e-11);
        assert!((exact.unq2.net + exact.red.net - exact.mi_s2_t).abs() < 2.0e-11);

        let f1: Vec<f64> = s1.iter().map(|&value| value as f64).collect();
        let f2: Vec<f64> = s2.iter().map(|&value| value as f64).collect();
        let ft: Vec<f64> = target.iter().map(|&value| value as f64).collect();
        let wb = discrete_pid2(
            MatRef::new(&f1, n, 1).unwrap(),
            MatRef::new(&f2, n, 1).unwrap(),
            MatRef::new(&ft, n, 1).unwrap(),
            3,
        )
        .unwrap()
        .into_categorical_result();
        for atom in [wb.redundancy, wb.unique_s1, wb.unique_s2, wb.synergy] {
            assert!(
                atom.is_finite() && atom >= -2.0e-12,
                "seed={seed} wb={wb:?}"
            );
        }
        assert!(
            (wb.redundancy + wb.unique_s1 + wb.unique_s2 + wb.synergy - wb.mi_s1s2_t).abs()
                < 2.0e-12
        );
    }
}

#[test]
fn skewed_random_discrete_pid3_and_pid4_obey_lattice_invariants() {
    const NEW_TO_OLD: [usize; 4] = [2, 0, 3, 1];

    for seed in 1..=80_u64 {
        let mut state = seed ^ 0xa5a5_5a5a_1234_5678;
        let n = 24 + (next(&mut state) as usize % 31);
        let mut columns: [Vec<usize>; 4] = std::array::from_fn(|_| Vec::with_capacity(n));
        let mut target = Vec::with_capacity(n);
        for _ in 0..n {
            let values: [usize; 4] = std::array::from_fn(|_| skewed_ternary(&mut state));
            for (column, value) in columns.iter_mut().zip(values) {
                column.push(value);
            }
            let noise = usize::from((next(&mut state) >> 63) != 0);
            target.push((values[0] + 2 * values[1] + values[2] + 2 * values[3] + noise) % 3);
        }
        let mats: Vec<DiscreteMatRef<'_>> = columns
            .iter()
            .map(|column| DiscreteMatRef::new(column, n, 1).unwrap())
            .collect();
        let target_mat = DiscreteMatRef::new(&target, n, 1).unwrap();

        let pid3 = discrete_sxpid3(mats[0], mats[1], mats[2], target_mat).unwrap();
        for (idx, atom) in pid3.atoms.iter().copied().enumerate() {
            assert_atom_finite_and_parts_nonnegative(atom, &format!("seed={seed} pid3[{idx}]"));
        }
        for mask in 1_u8..=7 {
            let down: f64 = pid3
                .antichains
                .iter()
                .zip(&pid3.atoms)
                .filter(|(node, _)| leq(node, &[mask]))
                .map(|(_, atom)| atom.net)
                .sum();
            assert!(
                (down - pid3.subset_mis[usize::from(mask - 1)]).abs() < 5.0e-11,
                "seed={seed} mask={mask:#05b}"
            );
        }

        let floats: Vec<Vec<f64>> = columns
            .iter()
            .map(|column| column.iter().map(|&value| value as f64).collect())
            .collect();
        let target_floats: Vec<f64> = target.iter().map(|&value| value as f64).collect();
        let fmats: Vec<MatRef<'_>> = floats
            .iter()
            .map(|column| MatRef::new(column, n, 1).unwrap())
            .collect();
        let wb3 = discrete_pid3(
            fmats[0],
            fmats[1],
            fmats[2],
            MatRef::new(&target_floats, n, 1).unwrap(),
            3,
        )
        .unwrap()
        .into_categorical_result();
        for atom in &wb3.atoms {
            assert!(
                atom.value.is_finite() && atom.value >= -2.0e-11,
                "seed={seed} wb3={atom:?}"
            );
        }
        for (node_index, node) in wb3.atoms.iter().enumerate() {
            let down: f64 = wb3
                .atoms
                .iter()
                .filter(|atom| leq(&atom.antichain_sets, &node.antichain_sets))
                .map(|atom| atom.value)
                .sum();
            assert!(
                (down - wb3.redundancies[node_index]).abs() < 5.0e-11,
                "seed={seed} node={:?}: down={down} cumulative={}",
                node.antichain_sets,
                wb3.redundancies[node_index]
            );
        }
        let top_index = wb3
            .atoms
            .iter()
            .position(|atom| atom.antichain_sets == [0b111])
            .unwrap();
        assert!((wb3.redundancies[top_index] - wb3.mi_s0s1s2_t).abs() < 5.0e-11);

        if seed <= 12 {
            let pid4 = discrete_sxpid_n(&mats, target_mat).unwrap();
            assert_eq!(pid4.atoms.len(), 166);
            for (idx, atom) in pid4.atoms.iter().copied().enumerate() {
                assert_atom_finite_and_parts_nonnegative(atom, &format!("seed={seed} pid4[{idx}]"));
            }
            for (point_index, point) in pid4.pointwise.iter().enumerate() {
                for (atom_index, atom) in point.atoms.iter().copied().enumerate() {
                    assert_atom_finite_and_parts_nonnegative(
                        atom,
                        &format!("seed={seed} pid4 point[{point_index}][{atom_index}]"),
                    );
                }
            }
            for mask in 1_u8..=15 {
                let down: f64 = pid4
                    .antichains
                    .iter()
                    .zip(&pid4.atoms)
                    .filter(|(node, _)| leq(node, &[mask]))
                    .map(|(_, atom)| atom.net)
                    .sum();
                assert!(
                    (down - pid4.subset_mis[usize::from(mask - 1)]).abs() < 2.0e-10,
                    "seed={seed} mask={mask:#06b}"
                );
            }

            let permuted_mats = NEW_TO_OLD.map(|old_index| mats[old_index]);
            let permuted = discrete_sxpid_n(&permuted_mats, target_mat).unwrap();
            for (node, atom) in pid4.antichains.iter().zip(&pid4.atoms) {
                let mapped_node: Vec<u8> = node
                    .iter()
                    .map(|&mask| remap_mask_to_permuted_sources(mask, NEW_TO_OLD))
                    .collect();
                let mapped_atom = permuted.atom(&mapped_node).unwrap();
                assert!(
                    (atom.informative - mapped_atom.informative).abs() < 2.0e-10
                        && (atom.misinformative - mapped_atom.misinformative).abs() < 2.0e-10
                        && (atom.net - mapped_atom.net).abs() < 2.0e-10,
                    "seed={seed} node={node:?} mapped={mapped_node:?}"
                );
            }
            for old_mask in 1_u8..=15 {
                let new_mask = remap_mask_to_permuted_sources(old_mask, NEW_TO_OLD);
                assert!(
                    (pid4.subset_mis[usize::from(old_mask - 1)]
                        - permuted.subset_mis[usize::from(new_mask - 1)])
                    .abs()
                        < 2.0e-11
                );
            }
        }
    }
}

#[cfg(target_pointer_width = "64")]
#[test]
fn high_bin_counts_flow_through_quantized_pid_and_sxpid_apis_without_rounding_the_count() {
    let num_bins = (1_usize << 53) + 3;
    let s1 = [0.0, 0.5, 1.0, 0.0, 0.5, 1.0];
    let s2 = [1.0, 0.5, 0.0, 1.0, 0.5, 0.0];
    let target = [0.0, 0.5, 1.0, 0.0, 0.5, 1.0];
    let s1 = MatRef::new(&s1, 6, 1).unwrap();
    let s2 = MatRef::new(&s2, 6, 1).unwrap();
    let target = MatRef::new(&target, 6, 1).unwrap();

    let imin = discrete_pid2(s1, s2, target, num_bins).unwrap();
    let sx = quantized_sxpid2(s1, s2, target, num_bins).unwrap();

    assert_eq!(imin.quantization.num_bins, num_bins);
    assert_eq!(sx.quantization.num_bins, num_bins);
    assert!(matches!(
        imin.categorical_result.input.encoding,
        pid_core::stable::imin::IminInputEncoding::Categorical
    ));
    assert_eq!(
        sx.categorical_result.input.encoding,
        DiscreteInputEncoding::Categorical
    );
    assert!((imin.categorical_result.mi_s1s2_t - sx.categorical_result.mi_s1s2_t).abs() < 1.0e-12);
}
