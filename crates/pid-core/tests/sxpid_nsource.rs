//! General n-source discrete SxPID: bounded-exhaustive agreement with the specialized 2-/3-source
//! paths, plus 4-source axioms (the source count IDTxl's SxPID supports).
//!
//! The two-source equivalence domain is complete: every nonempty empirical count table with total
//! mass `1..=4` over the eight binary `(S0,S1,T)` states. Stars-and-bars gives
//! `C(8,7)+C(9,7)+C(10,7)+C(11,7)=494` tables and 1,320 distinct positive-mass pointwise states
//! across the corpus. Each table is also checked after swapping the two sources, including the
//! induced atom permutation.
//!
//! The three-source equivalence domain is likewise complete within its stated bound: every
//! nonempty count table with total mass `1..=3` over the sixteen binary `(S0,S1,S2,T)` states,
//! giving `C(16,15)+C(17,15)+C(18,15)=968` tables and 2,448 distinct positive-mass pointwise
//! states. Every informative, misinformative, and net component is compared at every averaged and
//! pointwise antichain coordinate, before and after swapping the first two sources.
//!
//! This is bounded implementation-equivalence evidence, not an unbounded refinement proof or a
//! population theorem. The public API promises specialized/general agreement within floating-point
//! tolerance rather than bit identity because the paths use separate Möbius-inversion routines.
//! Realization keys, counts, empirical probabilities, subset mutual informations, and diagnostics
//! are nevertheless required to be bit-identical where their computations are shared. A raw-bit
//! probe on the first one-cell table found the exact boundary case `-0.0` versus `+0.0` for the
//! all-singletons informative atom, so this suite deliberately does not conflate numerical
//! equality with signed-zero bit identity.

use pid_core::stable::categorical::{
    discrete_sxpid2, discrete_sxpid2_averaged, discrete_sxpid3, discrete_sxpid3_averaged,
    discrete_sxpid_n, discrete_sxpid_n_averaged, DiscreteSxPid2Result, DiscreteSxPid3Result,
    DiscreteSxPidNResult, EmpiricalPmfDiagnostics, SxAveragedAtom, SxPointwise2, SxPointwiseAtom,
};
use pid_core::DiscreteMatRef;

const TWO_SOURCE_MAX_TOTAL_MASS: usize = 4;
const TWO_SOURCE_CELL_COUNT: usize = 8;
const TWO_SOURCE_CASE_COUNT: usize = 494;
const TWO_SOURCE_POINTWISE_STATE_COUNT: usize = 1_320;
const THREE_SOURCE_MAX_TOTAL_MASS: usize = 3;
const THREE_SOURCE_CELL_COUNT: usize = 16;
const THREE_SOURCE_CASE_COUNT: usize = 968;
const THREE_SOURCE_POINTWISE_STATE_COUNT: usize = 2_448;
const MAX_PATH_DIFFERENCE_EPSILONS: f64 = 64.0;
const TWO_SOURCE_ANTICHAINS: [&[u8]; 4] = [&[0b01], &[0b10], &[0b11], &[0b01, 0b10]];
type FourSourceRows = (Vec<usize>, Vec<usize>, Vec<usize>, Vec<usize>, Vec<usize>);

fn leq(a: &[u8], b: &[u8]) -> bool {
    b.iter().all(|bb| a.iter().any(|aa| aa & !bb == 0))
}

fn for_each_weak_composition(
    total: usize,
    counts: &mut [usize],
    position: usize,
    visit: &mut impl FnMut(&[usize]),
) {
    if position + 1 == counts.len() {
        counts[position] = total;
        visit(counts);
        return;
    }
    for count in 0..=total {
        counts[position] = count;
        for_each_weak_composition(total - count, counts, position + 1, visit);
    }
}

fn for_each_nonempty_count_table(
    cell_count: usize,
    max_total_mass: usize,
    mut visit: impl FnMut(&[usize]),
) {
    let mut counts = vec![0; cell_count];
    for total_mass in 1..=max_total_mass {
        for_each_weak_composition(total_mass, &mut counts, 0, &mut visit);
    }
}

fn binary_two_source_rows(counts: &[usize]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let total_mass = counts.iter().sum();
    let mut source_one = Vec::with_capacity(total_mass);
    let mut source_two = Vec::with_capacity(total_mass);
    let mut target = Vec::with_capacity(total_mass);
    for (cell, &count) in counts.iter().enumerate() {
        source_one.extend(std::iter::repeat_n((cell >> 2) & 1, count));
        source_two.extend(std::iter::repeat_n((cell >> 1) & 1, count));
        target.extend(std::iter::repeat_n(cell & 1, count));
    }
    (source_one, source_two, target)
}

fn binary_three_source_rows(counts: &[usize]) -> (Vec<usize>, Vec<usize>, Vec<usize>, Vec<usize>) {
    let total_mass = counts.iter().sum();
    let mut source_zero = Vec::with_capacity(total_mass);
    let mut source_one = Vec::with_capacity(total_mass);
    let mut source_two = Vec::with_capacity(total_mass);
    let mut target = Vec::with_capacity(total_mass);
    for (cell, &count) in counts.iter().enumerate() {
        source_zero.extend(std::iter::repeat_n((cell >> 3) & 1, count));
        source_one.extend(std::iter::repeat_n((cell >> 2) & 1, count));
        source_two.extend(std::iter::repeat_n((cell >> 1) & 1, count));
        target.extend(std::iter::repeat_n(cell & 1, count));
    }
    (source_zero, source_one, source_two, target)
}

fn binary_four_source_rows(counts: &[usize]) -> FourSourceRows {
    let total_mass = counts.iter().sum();
    let mut source_zero = Vec::with_capacity(total_mass);
    let mut source_one = Vec::with_capacity(total_mass);
    let mut source_two = Vec::with_capacity(total_mass);
    let mut source_three = Vec::with_capacity(total_mass);
    let mut target = Vec::with_capacity(total_mass);
    for (cell, &count) in counts.iter().enumerate() {
        source_zero.extend(std::iter::repeat_n((cell >> 4) & 1, count));
        source_one.extend(std::iter::repeat_n((cell >> 3) & 1, count));
        source_two.extend(std::iter::repeat_n((cell >> 2) & 1, count));
        source_three.extend(std::iter::repeat_n((cell >> 1) & 1, count));
        target.extend(std::iter::repeat_n(cell & 1, count));
    }
    (source_zero, source_one, source_two, source_three, target)
}

fn assert_same_bits(left: f64, right: f64, context: &str, case_index: usize) {
    assert_eq!(
        left.to_bits(),
        right.to_bits(),
        "{context} differs in case {case_index}: left={left:.17e}, right={right:.17e}"
    );
}

fn averaged_atom_bits(atom: SxAveragedAtom) -> [u64; 3] {
    [
        atom.informative_nats().to_bits(),
        atom.misinformative_nats().to_bits(),
        atom.net_nats().to_bits(),
    ]
}

fn historical_neumaier(values: impl IntoIterator<Item = f64>) -> f64 {
    let mut sum = 0.0_f64;
    let mut correction = 0.0_f64;
    for value in values {
        let next = sum + value;
        if sum.abs() >= value.abs() {
            correction += (sum - next) + value;
        } else {
            correction += (value - next) + sum;
        }
        sum = next;
    }
    sum + correction
}

fn historical_average_bits(
    weighted_atoms: impl IntoIterator<Item = (f64, SxPointwiseAtom)> + Clone,
) -> [u64; 3] {
    let informative = historical_neumaier(
        weighted_atoms
            .clone()
            .into_iter()
            .map(|(probability, atom)| probability * atom.informative_nats()),
    );
    let misinformative = historical_neumaier(
        weighted_atoms
            .into_iter()
            .map(|(probability, atom)| probability * atom.misinformative_nats()),
    );
    [
        informative.to_bits(),
        misinformative.to_bits(),
        (informative - misinformative).to_bits(),
    ]
}

fn assert_same_pmf_diagnostics(
    left: &EmpiricalPmfDiagnostics,
    right: &EmpiricalPmfDiagnostics,
    context: &str,
    case_index: usize,
) {
    assert_eq!(
        left, right,
        "{context} PMF diagnostics differ in case {case_index}"
    );
    assert_same_bits(
        left.observed_coverage_indicator,
        right.observed_coverage_indicator,
        context,
        case_index,
    );
}

fn assert_path_close(
    left: f64,
    right: f64,
    scope: &str,
    antichain: &[u8],
    component: &str,
    case_index: usize,
) {
    assert!(
        left.is_finite() && right.is_finite(),
        "{scope} {antichain:?}.{component} is non-finite in case {case_index}: \
         left={left:?}, right={right:?}"
    );
    let scale = 1.0 + left.abs().max(right.abs());
    let tolerance = MAX_PATH_DIFFERENCE_EPSILONS * f64::EPSILON * scale;
    let difference = (left - right).abs();
    assert!(
        difference <= tolerance,
        "{scope} {antichain:?}.{component} differs in case {case_index}: \
         left={left:.17e}, right={right:.17e}, |delta|={difference:.17e}, \
         tolerance={tolerance:.17e}"
    );
}

fn assert_averaged_atom_close(
    left: SxAveragedAtom,
    right: SxAveragedAtom,
    scope: &str,
    antichain: &[u8],
    case_index: usize,
) -> usize {
    assert_eq!(left.interpretation(), right.interpretation());
    for (component, left, right) in [
        (
            "informative",
            left.informative_nats(),
            right.informative_nats(),
        ),
        (
            "misinformative",
            left.misinformative_nats(),
            right.misinformative_nats(),
        ),
        ("net", left.net_nats(), right.net_nats()),
    ] {
        assert_path_close(left, right, scope, antichain, component, case_index);
    }
    3
}

fn assert_pointwise_atom_close(
    left: SxPointwiseAtom,
    right: SxPointwiseAtom,
    scope: &str,
    antichain: &[u8],
    case_index: usize,
) -> usize {
    assert_eq!(left.interpretation(), right.interpretation());
    for (component, left, right) in [
        (
            "informative",
            left.informative_nats(),
            right.informative_nats(),
        ),
        (
            "misinformative",
            left.misinformative_nats(),
            right.misinformative_nats(),
        ),
        ("net", left.net_nats(), right.net_nats()),
    ] {
        assert_path_close(left, right, scope, antichain, component, case_index);
    }
    3
}

fn two_source_averaged_atoms(result: &DiscreteSxPid2Result) -> [SxAveragedAtom; 4] {
    [result.unq1, result.unq2, result.syn, result.red]
}

fn two_source_pointwise_atoms(point: &SxPointwise2) -> [SxPointwiseAtom; 4] {
    [point.unq1, point.unq2, point.syn, point.red]
}

fn find_antichain(antichains: &[Vec<u8>], expected: &[u8]) -> usize {
    antichains
        .iter()
        .position(|actual| {
            actual.len() == expected.len()
                && actual.iter().all(|mask| expected.contains(mask))
                && expected.iter().all(|mask| actual.contains(mask))
        })
        .unwrap_or_else(|| panic!("missing antichain {expected:?}"))
}

fn compare_two_source_paths(
    specialized: &DiscreteSxPid2Result,
    general: &DiscreteSxPidNResult,
    case_index: usize,
    scope: &str,
) -> usize {
    assert!(specialized.pointwise_included);
    assert!(general.pointwise_included);
    assert_eq!(general.n_sources, 2);
    assert_eq!(general.antichains.len(), 4);
    assert_eq!(specialized.pointwise.len(), general.pointwise.len());
    assert_eq!(specialized.input, general.input);
    assert_same_pmf_diagnostics(
        &specialized.empirical_pmf,
        &general.empirical_pmf,
        "two-source specialized/general",
        case_index,
    );
    assert_eq!(general.subset_mis.len(), 3);
    for (context, specialized_mi, general_mi) in [
        ("I(S0;T)", specialized.mi_s1_t, general.subset_mis[0]),
        ("I(S1;T)", specialized.mi_s2_t, general.subset_mis[1]),
        ("I(S0,S1;T)", specialized.mi_s1s2_t, general.subset_mis[2]),
        ("joint MI", specialized.mi_s1s2_t, general.joint_mi),
    ] {
        assert_same_bits(specialized_mi, general_mi, context, case_index);
    }

    let mut comparisons = 0;
    for (antichain, specialized_atom) in TWO_SOURCE_ANTICHAINS
        .iter()
        .zip(two_source_averaged_atoms(specialized))
    {
        let general_atom = general
            .atom(antichain)
            .expect("general two-source lattice must contain every specialized node");
        comparisons += assert_averaged_atom_close(
            specialized_atom,
            general_atom,
            scope,
            antichain,
            case_index,
        );
    }

    for specialized_point in &specialized.pointwise {
        let general_point = general
            .pointwise
            .iter()
            .find(|point| {
                point.realization.len() == 3
                    && point.realization[0] == specialized_point.s1
                    && point.realization[1] == specialized_point.s2
                    && point.realization[2] == specialized_point.t
            })
            .expect("general path must expose every specialized pointwise realization");
        assert_eq!(
            specialized_point.empirical_count,
            general_point.empirical_count
        );
        assert_same_bits(
            specialized_point.empirical_probability,
            general_point.empirical_probability,
            "pointwise empirical probability",
            case_index,
        );
        for ((antichain, specialized_atom), general_index) in TWO_SOURCE_ANTICHAINS
            .iter()
            .zip(two_source_pointwise_atoms(specialized_point))
            .zip(
                TWO_SOURCE_ANTICHAINS
                    .iter()
                    .map(|antichain| find_antichain(&general.antichains, antichain)),
            )
        {
            comparisons += assert_pointwise_atom_close(
                specialized_atom,
                general_point.atoms[general_index],
                scope,
                antichain,
                case_index,
            );
        }
    }
    comparisons
}

fn swap_first_two_source_mask(mask: u8) -> u8 {
    (mask & !0b11) | ((mask & 0b01) << 1) | ((mask & 0b10) >> 1)
}

fn swapped_first_two_source_antichain(antichain: &[u8]) -> Vec<u8> {
    let mut swapped = antichain
        .iter()
        .copied()
        .map(swap_first_two_source_mask)
        .collect::<Vec<_>>();
    swapped.sort_unstable();
    swapped
}

fn compare_two_source_swap(
    original_specialized: &DiscreteSxPid2Result,
    swapped_specialized: &DiscreteSxPid2Result,
    original_general: &DiscreteSxPidNResult,
    swapped_general: &DiscreteSxPidNResult,
    case_index: usize,
) -> usize {
    assert_same_pmf_diagnostics(
        &original_specialized.empirical_pmf,
        &swapped_specialized.empirical_pmf,
        "specialized two-source swap",
        case_index,
    );
    assert_same_pmf_diagnostics(
        &original_general.empirical_pmf,
        &swapped_general.empirical_pmf,
        "general two-source swap",
        case_index,
    );
    assert_eq!(
        original_specialized.input.observed_cardinalities,
        [
            swapped_specialized.input.observed_cardinalities[1],
            swapped_specialized.input.observed_cardinalities[0],
            swapped_specialized.input.observed_cardinalities[2],
        ]
    );
    assert_same_bits(
        original_specialized.mi_s1_t,
        swapped_specialized.mi_s2_t,
        "specialized swapped I(S0;T)",
        case_index,
    );
    assert_same_bits(
        original_specialized.mi_s2_t,
        swapped_specialized.mi_s1_t,
        "specialized swapped I(S1;T)",
        case_index,
    );
    assert_same_bits(
        original_specialized.mi_s1s2_t,
        swapped_specialized.mi_s1s2_t,
        "specialized swapped joint MI",
        case_index,
    );
    assert_same_bits(
        original_general.subset_mis[0],
        swapped_general.subset_mis[1],
        "general swapped I(S0;T)",
        case_index,
    );
    assert_same_bits(
        original_general.subset_mis[1],
        swapped_general.subset_mis[0],
        "general swapped I(S1;T)",
        case_index,
    );
    assert_same_bits(
        original_general.subset_mis[2],
        swapped_general.subset_mis[2],
        "general swapped joint MI",
        case_index,
    );

    let specialized_permutation = [1, 0, 2, 3];
    let original_specialized_atoms = two_source_averaged_atoms(original_specialized);
    let swapped_specialized_atoms = two_source_averaged_atoms(swapped_specialized);
    let mut comparisons = 0;
    for (original_index, &swapped_index) in specialized_permutation.iter().enumerate() {
        comparisons += assert_averaged_atom_close(
            original_specialized_atoms[original_index],
            swapped_specialized_atoms[swapped_index],
            "specialized source swap",
            TWO_SOURCE_ANTICHAINS[original_index],
            case_index,
        );
    }

    let general_permutation = original_general
        .antichains
        .iter()
        .map(|antichain| {
            find_antichain(
                &swapped_general.antichains,
                &swapped_first_two_source_antichain(antichain),
            )
        })
        .collect::<Vec<_>>();
    for (original_index, &swapped_index) in general_permutation.iter().enumerate() {
        comparisons += assert_averaged_atom_close(
            original_general.atoms[original_index],
            swapped_general.atoms[swapped_index],
            "general source swap",
            &original_general.antichains[original_index],
            case_index,
        );
    }

    for original_point in &original_specialized.pointwise {
        let swapped_point = swapped_specialized
            .pointwise
            .iter()
            .find(|point| {
                point.s1 == original_point.s2
                    && point.s2 == original_point.s1
                    && point.t == original_point.t
            })
            .expect("source swap must preserve every specialized pointwise realization");
        assert_eq!(
            original_point.empirical_count,
            swapped_point.empirical_count
        );
        assert_same_bits(
            original_point.empirical_probability,
            swapped_point.empirical_probability,
            "specialized swapped pointwise empirical probability",
            case_index,
        );
        let original_atoms = two_source_pointwise_atoms(original_point);
        let swapped_atoms = two_source_pointwise_atoms(swapped_point);
        for (original_index, &swapped_index) in specialized_permutation.iter().enumerate() {
            comparisons += assert_pointwise_atom_close(
                original_atoms[original_index],
                swapped_atoms[swapped_index],
                "specialized pointwise source swap",
                TWO_SOURCE_ANTICHAINS[original_index],
                case_index,
            );
        }
    }

    for original_point in &original_general.pointwise {
        let swapped_point = swapped_general
            .pointwise
            .iter()
            .find(|point| {
                point.realization.len() == 3
                    && point.realization[0] == original_point.realization[1]
                    && point.realization[1] == original_point.realization[0]
                    && point.realization[2] == original_point.realization[2]
            })
            .expect("source swap must preserve every general pointwise realization");
        assert_eq!(
            original_point.empirical_count,
            swapped_point.empirical_count
        );
        assert_same_bits(
            original_point.empirical_probability,
            swapped_point.empirical_probability,
            "general swapped pointwise empirical probability",
            case_index,
        );
        for (original_index, &swapped_index) in general_permutation.iter().enumerate() {
            comparisons += assert_pointwise_atom_close(
                original_point.atoms[original_index],
                swapped_point.atoms[swapped_index],
                "general pointwise source swap",
                &original_general.antichains[original_index],
                case_index,
            );
        }
    }
    comparisons
}

fn compare_three_source_paths(
    specialized: &DiscreteSxPid3Result,
    general: &DiscreteSxPidNResult,
    case_index: usize,
) -> usize {
    assert!(specialized.pointwise_included);
    assert!(general.pointwise_included);
    assert_eq!(general.n_sources, 3);
    assert_eq!(specialized.antichains.len(), 18);
    assert_eq!(general.antichains.len(), 18);
    assert_eq!(specialized.pointwise.len(), general.pointwise.len());
    assert_eq!(specialized.input, general.input);
    assert_same_pmf_diagnostics(
        &specialized.empirical_pmf,
        &general.empirical_pmf,
        "three-source specialized/general",
        case_index,
    );
    assert_eq!(specialized.subset_mis.len(), 7);
    assert_eq!(general.subset_mis.len(), 7);
    for (subset_index, (&specialized_mi, &general_mi)) in specialized
        .subset_mis
        .iter()
        .zip(&general.subset_mis)
        .enumerate()
    {
        assert_same_bits(
            specialized_mi,
            general_mi,
            &format!("three-source subset MI mask {}", subset_index + 1),
            case_index,
        );
    }
    for (context, named, subset) in [
        ("I(S0;T)", specialized.mi_s0_t, specialized.subset_mis[0]),
        ("I(S1;T)", specialized.mi_s1_t, specialized.subset_mis[1]),
        ("I(S2;T)", specialized.mi_s2_t, specialized.subset_mis[3]),
        (
            "I(S0,S1,S2;T)",
            specialized.mi_s0s1s2_t,
            specialized.subset_mis[6],
        ),
        (
            "general joint MI",
            general.joint_mi,
            specialized.subset_mis[6],
        ),
    ] {
        assert_same_bits(named, subset, context, case_index);
    }

    let general_indices = specialized
        .antichains
        .iter()
        .map(|antichain| find_antichain(&general.antichains, antichain))
        .collect::<Vec<_>>();
    let mut comparisons = 0;
    for ((antichain, specialized_atom), &general_index) in specialized
        .antichains
        .iter()
        .zip(&specialized.atoms)
        .zip(&general_indices)
    {
        comparisons += assert_averaged_atom_close(
            *specialized_atom,
            general.atoms[general_index],
            "three-source specialized/general averaged",
            antichain,
            case_index,
        );
    }

    for specialized_point in &specialized.pointwise {
        let general_point = general
            .pointwise
            .iter()
            .find(|point| {
                point.realization.len() == 4
                    && point.realization[0] == specialized_point.s0
                    && point.realization[1] == specialized_point.s1
                    && point.realization[2] == specialized_point.s2
                    && point.realization[3] == specialized_point.t
            })
            .expect("general path must expose every specialized pointwise realization");
        assert_eq!(
            specialized_point.empirical_count,
            general_point.empirical_count
        );
        assert_same_bits(
            specialized_point.empirical_probability,
            general_point.empirical_probability,
            "three-source pointwise empirical probability",
            case_index,
        );
        assert_eq!(specialized_point.atoms.len(), 18);
        assert_eq!(general_point.atoms.len(), 18);
        for ((antichain, specialized_atom), &general_index) in specialized
            .antichains
            .iter()
            .zip(&specialized_point.atoms)
            .zip(&general_indices)
        {
            comparisons += assert_pointwise_atom_close(
                *specialized_atom,
                general_point.atoms[general_index],
                "three-source specialized/general pointwise",
                antichain,
                case_index,
            );
        }
    }
    comparisons
}

fn compare_three_source_swap(
    original_specialized: &DiscreteSxPid3Result,
    swapped_specialized: &DiscreteSxPid3Result,
    original_general: &DiscreteSxPidNResult,
    swapped_general: &DiscreteSxPidNResult,
    case_index: usize,
) -> usize {
    assert_same_pmf_diagnostics(
        &original_specialized.empirical_pmf,
        &swapped_specialized.empirical_pmf,
        "specialized three-source swap",
        case_index,
    );
    assert_same_pmf_diagnostics(
        &original_general.empirical_pmf,
        &swapped_general.empirical_pmf,
        "general three-source swap",
        case_index,
    );
    assert_eq!(
        original_specialized.input.observed_cardinalities,
        [
            swapped_specialized.input.observed_cardinalities[1],
            swapped_specialized.input.observed_cardinalities[0],
            swapped_specialized.input.observed_cardinalities[2],
            swapped_specialized.input.observed_cardinalities[3],
        ]
    );
    for (context, original, swapped) in [
        (
            "specialized swapped I(S0;T)",
            original_specialized.mi_s0_t,
            swapped_specialized.mi_s1_t,
        ),
        (
            "specialized swapped I(S1;T)",
            original_specialized.mi_s1_t,
            swapped_specialized.mi_s0_t,
        ),
        (
            "specialized swapped I(S2;T)",
            original_specialized.mi_s2_t,
            swapped_specialized.mi_s2_t,
        ),
        (
            "specialized swapped joint MI",
            original_specialized.mi_s0s1s2_t,
            swapped_specialized.mi_s0s1s2_t,
        ),
        (
            "general swapped joint MI",
            original_general.joint_mi,
            swapped_general.joint_mi,
        ),
    ] {
        assert_same_bits(original, swapped, context, case_index);
    }
    for mask in 1u8..=0b111 {
        let swapped_mask = swap_first_two_source_mask(mask);
        assert_same_bits(
            original_specialized.subset_mis[usize::from(mask - 1)],
            swapped_specialized.subset_mis[usize::from(swapped_mask - 1)],
            "specialized source-swapped subset MI",
            case_index,
        );
        assert_same_bits(
            original_general.subset_mis[usize::from(mask - 1)],
            swapped_general.subset_mis[usize::from(swapped_mask - 1)],
            "general source-swapped subset MI",
            case_index,
        );
    }

    let specialized_permutation = original_specialized
        .antichains
        .iter()
        .map(|antichain| {
            find_antichain(
                &swapped_specialized.antichains,
                &swapped_first_two_source_antichain(antichain),
            )
        })
        .collect::<Vec<_>>();
    let general_permutation = original_general
        .antichains
        .iter()
        .map(|antichain| {
            find_antichain(
                &swapped_general.antichains,
                &swapped_first_two_source_antichain(antichain),
            )
        })
        .collect::<Vec<_>>();
    let mut comparisons = 0;
    for (original_index, &swapped_index) in specialized_permutation.iter().enumerate() {
        comparisons += assert_averaged_atom_close(
            original_specialized.atoms[original_index],
            swapped_specialized.atoms[swapped_index],
            "three-source specialized source swap",
            &original_specialized.antichains[original_index],
            case_index,
        );
    }
    for (original_index, &swapped_index) in general_permutation.iter().enumerate() {
        comparisons += assert_averaged_atom_close(
            original_general.atoms[original_index],
            swapped_general.atoms[swapped_index],
            "three-source general source swap",
            &original_general.antichains[original_index],
            case_index,
        );
    }

    for original_point in &original_specialized.pointwise {
        let swapped_point = swapped_specialized
            .pointwise
            .iter()
            .find(|point| {
                point.s0 == original_point.s1
                    && point.s1 == original_point.s0
                    && point.s2 == original_point.s2
                    && point.t == original_point.t
            })
            .expect("source swap must preserve every specialized three-source realization");
        assert_eq!(
            original_point.empirical_count,
            swapped_point.empirical_count
        );
        assert_same_bits(
            original_point.empirical_probability,
            swapped_point.empirical_probability,
            "specialized three-source swapped pointwise empirical probability",
            case_index,
        );
        for (original_index, &swapped_index) in specialized_permutation.iter().enumerate() {
            comparisons += assert_pointwise_atom_close(
                original_point.atoms[original_index],
                swapped_point.atoms[swapped_index],
                "three-source specialized pointwise source swap",
                &original_specialized.antichains[original_index],
                case_index,
            );
        }
    }
    for original_point in &original_general.pointwise {
        let swapped_point = swapped_general
            .pointwise
            .iter()
            .find(|point| {
                point.realization.len() == 4
                    && point.realization[0] == original_point.realization[1]
                    && point.realization[1] == original_point.realization[0]
                    && point.realization[2] == original_point.realization[2]
                    && point.realization[3] == original_point.realization[3]
            })
            .expect("source swap must preserve every general three-source realization");
        assert_eq!(
            original_point.empirical_count,
            swapped_point.empirical_count
        );
        assert_same_bits(
            original_point.empirical_probability,
            swapped_point.empirical_probability,
            "general three-source swapped pointwise empirical probability",
            case_index,
        );
        for (original_index, &swapped_index) in general_permutation.iter().enumerate() {
            comparisons += assert_pointwise_atom_close(
                original_point.atoms[original_index],
                swapped_point.atoms[swapped_index],
                "three-source general pointwise source swap",
                &original_general.antichains[original_index],
                case_index,
            );
        }
    }
    comparisons
}

#[test]
fn all_494_binary_two_source_count_tables_match_general_path_and_source_swap() {
    let mut case_count = 0;
    let mut pointwise_state_count = 0;
    let mut atom_component_comparisons = 0;
    for_each_nonempty_count_table(TWO_SOURCE_CELL_COUNT, TWO_SOURCE_MAX_TOTAL_MASS, |counts| {
        let case_index = case_count;
        let (source_one, source_two, target) = binary_two_source_rows(counts);
        let total_mass = target.len();
        let source_one =
            DiscreteMatRef::new(&source_one, total_mass, 1).expect("valid source-one matrix");
        let source_two =
            DiscreteMatRef::new(&source_two, total_mass, 1).expect("valid source-two matrix");
        let target = DiscreteMatRef::new(&target, total_mass, 1).expect("valid target matrix");

        let specialized =
            discrete_sxpid2(source_one, source_two, target).expect("bounded table must evaluate");
        let general = discrete_sxpid_n(&[source_one, source_two], target)
            .expect("bounded table must evaluate through general path");
        let swapped_specialized =
            discrete_sxpid2(source_two, source_one, target).expect("swap must evaluate");
        let swapped_general = discrete_sxpid_n(&[source_two, source_one], target)
            .expect("swap must evaluate through general path");

        pointwise_state_count += specialized.pointwise.len();
        atom_component_comparisons += compare_two_source_paths(
            &specialized,
            &general,
            case_index,
            "two-source specialized/general",
        );
        atom_component_comparisons += compare_two_source_paths(
            &swapped_specialized,
            &swapped_general,
            case_index,
            "swapped two-source specialized/general",
        );
        atom_component_comparisons += compare_two_source_swap(
            &specialized,
            &swapped_specialized,
            &general,
            &swapped_general,
            case_index,
        );
        case_count += 1;
    });
    assert_eq!(case_count, TWO_SOURCE_CASE_COUNT);
    assert_eq!(pointwise_state_count, TWO_SOURCE_POINTWISE_STATE_COUNT);
    assert_eq!(
        atom_component_comparisons,
        48 * (TWO_SOURCE_CASE_COUNT + TWO_SOURCE_POINTWISE_STATE_COUNT)
    );
}

#[test]
fn all_968_binary_three_source_count_tables_through_three_samples_match_general_path() {
    let mut case_count = 0;
    let mut pointwise_state_count = 0;
    let mut atom_component_comparisons = 0;
    for_each_nonempty_count_table(
        THREE_SOURCE_CELL_COUNT,
        THREE_SOURCE_MAX_TOTAL_MASS,
        |counts| {
            let case_index = case_count;
            let (source_zero, source_one, source_two, target) = binary_three_source_rows(counts);
            let total_mass = target.len();
            let source_zero =
                DiscreteMatRef::new(&source_zero, total_mass, 1).expect("valid source-zero matrix");
            let source_one =
                DiscreteMatRef::new(&source_one, total_mass, 1).expect("valid source-one matrix");
            let source_two =
                DiscreteMatRef::new(&source_two, total_mass, 1).expect("valid source-two matrix");
            let target = DiscreteMatRef::new(&target, total_mass, 1).expect("valid target matrix");

            let specialized = discrete_sxpid3(source_zero, source_one, source_two, target)
                .expect("bounded table must evaluate");
            let general = discrete_sxpid_n(&[source_zero, source_one, source_two], target)
                .expect("bounded table must evaluate through general path");
            let swapped_specialized = discrete_sxpid3(source_one, source_zero, source_two, target)
                .expect("source-swapped bounded table must evaluate");
            let swapped_general = discrete_sxpid_n(&[source_one, source_zero, source_two], target)
                .expect("source-swapped bounded table must evaluate through general path");
            pointwise_state_count += specialized.pointwise.len();
            atom_component_comparisons +=
                compare_three_source_paths(&specialized, &general, case_index);
            atom_component_comparisons +=
                compare_three_source_paths(&swapped_specialized, &swapped_general, case_index);
            atom_component_comparisons += compare_three_source_swap(
                &specialized,
                &swapped_specialized,
                &general,
                &swapped_general,
                case_index,
            );
            case_count += 1;
        },
    );
    assert_eq!(case_count, THREE_SOURCE_CASE_COUNT);
    assert_eq!(pointwise_state_count, THREE_SOURCE_POINTWISE_STATE_COUNT);
    assert_eq!(
        atom_component_comparisons,
        216 * (THREE_SOURCE_CASE_COUNT + THREE_SOURCE_POINTWISE_STATE_COUNT)
    );
}

#[test]
fn pinned_two_source_average_is_bit_equivariant_after_source_swap() {
    let counts = [0, 1, 1, 1, 2, 1, 5, 1];
    let (source_one, source_two, target) = binary_two_source_rows(&counts);
    let n = target.len();
    let source_one = DiscreteMatRef::new(&source_one, n, 1).unwrap();
    let source_two = DiscreteMatRef::new(&source_two, n, 1).unwrap();
    let target = DiscreteMatRef::new(&target, n, 1).unwrap();

    let original = discrete_sxpid2(source_one, source_two, target).unwrap();
    let swapped = discrete_sxpid2(source_two, source_one, target).unwrap();
    let original_averaged = discrete_sxpid2_averaged(source_one, source_two, target).unwrap();
    let swapped_averaged = discrete_sxpid2_averaged(source_two, source_one, target).unwrap();
    let original_general = discrete_sxpid_n(&[source_one, source_two], target).unwrap();
    let swapped_general = discrete_sxpid_n(&[source_two, source_one], target).unwrap();
    let original_general_averaged =
        discrete_sxpid_n_averaged(&[source_one, source_two], target).unwrap();
    let swapped_general_averaged =
        discrete_sxpid_n_averaged(&[source_two, source_one], target).unwrap();

    let expected = [
        0x3fc8_ef0d_df2c_10fb,
        0x3fbd_c0ce_b963_b913,
        0x3fb4_1d4d_04f4_68e3,
    ];
    for atom in [
        original.syn,
        swapped.syn,
        original_averaged.syn,
        swapped_averaged.syn,
        original_general.atom(&[0b11]).unwrap(),
        swapped_general.atom(&[0b11]).unwrap(),
        original_general_averaged.atom(&[0b11]).unwrap(),
        swapped_general_averaged.atom(&[0b11]).unwrap(),
    ] {
        assert_eq!(averaged_atom_bits(atom), expected);
    }

    let historical_original = historical_average_bits(
        original
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.syn)),
    );
    let historical_swapped = historical_average_bits(
        swapped
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.syn)),
    );
    assert_eq!(historical_original[2], 0x3fb4_1d4d_04f4_68e3);
    assert_eq!(historical_swapped[2], 0x3fb4_1d4d_04f4_68e4);
    assert_ne!(historical_original, historical_swapped);
}

#[test]
fn pinned_three_source_average_components_are_bit_equivariant_after_source_swap() {
    let counts = [4, 0, 3, 2, 1, 1, 0, 4, 0, 0, 1, 1, 3, 4, 0, 0];
    let (source_zero, source_one, source_two, target) = binary_three_source_rows(&counts);
    let n = target.len();
    let source_zero = DiscreteMatRef::new(&source_zero, n, 1).unwrap();
    let source_one = DiscreteMatRef::new(&source_one, n, 1).unwrap();
    let source_two = DiscreteMatRef::new(&source_two, n, 1).unwrap();
    let target = DiscreteMatRef::new(&target, n, 1).unwrap();

    let original = discrete_sxpid3(source_zero, source_one, source_two, target).unwrap();
    let swapped = discrete_sxpid3(source_one, source_zero, source_two, target).unwrap();
    let original_averaged =
        discrete_sxpid3_averaged(source_zero, source_one, source_two, target).unwrap();
    let swapped_averaged =
        discrete_sxpid3_averaged(source_one, source_zero, source_two, target).unwrap();
    let original_general =
        discrete_sxpid_n(&[source_zero, source_one, source_two], target).unwrap();
    let swapped_general = discrete_sxpid_n(&[source_one, source_zero, source_two], target).unwrap();
    let original_general_averaged =
        discrete_sxpid_n_averaged(&[source_zero, source_one, source_two], target).unwrap();
    let swapped_general_averaged =
        discrete_sxpid_n_averaged(&[source_one, source_zero, source_two], target).unwrap();

    let expected = [
        0x3fa3_b012_4a6b_77db,
        0x3f8a_61d9_7c81_3f4d,
        0x3f9a_2f37_d696_5010,
    ];
    for atom in [
        original.atom(&[0b001, 0b110]).unwrap(),
        swapped.atom(&[0b010, 0b101]).unwrap(),
        original_averaged.atom(&[0b001, 0b110]).unwrap(),
        swapped_averaged.atom(&[0b010, 0b101]).unwrap(),
        original_general.atom(&[0b001, 0b110]).unwrap(),
        swapped_general.atom(&[0b010, 0b101]).unwrap(),
        original_general_averaged.atom(&[0b001, 0b110]).unwrap(),
        swapped_general_averaged.atom(&[0b010, 0b101]).unwrap(),
    ] {
        assert_eq!(averaged_atom_bits(atom), expected);
    }

    let original_index = original
        .antichains
        .iter()
        .position(|antichain| antichain == &[0b001, 0b110])
        .unwrap();
    let swapped_index = swapped
        .antichains
        .iter()
        .position(|antichain| antichain == &[0b010, 0b101])
        .unwrap();
    let historical_original = historical_average_bits(
        original
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.atoms[original_index])),
    );
    let historical_swapped = historical_average_bits(
        swapped
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.atoms[swapped_index])),
    );
    assert_ne!(
        historical_original, historical_swapped,
        "the historical compensated final average must retain this reachable source-order defect"
    );
}

#[test]
fn pinned_four_source_average_components_are_bit_equivariant_after_source_swap() {
    // At parent 01466e8, the incidental final-average order changed the averaged misinformative
    // component by one bit under S0/S1 exchange for this reachable empirical table. Exact
    // represented-term final averaging removes that defect without claiming exact pointwise
    // atoms, probabilities, logarithms, or PID.
    let counts = [
        4, 4, 3, 1, 1, 4, 5, 0, 5, 3, 2, 0, 0, 1, 1, 2, 3, 1, 3, 0, 3, 2, 3, 4, 0, 2, 5, 4, 3, 2,
        3, 1,
    ];
    let (source_zero, source_one, source_two, source_three, target) =
        binary_four_source_rows(&counts);
    let n = target.len();
    assert_eq!(n, 75);
    let source_zero = DiscreteMatRef::new(&source_zero, n, 1).unwrap();
    let source_one = DiscreteMatRef::new(&source_one, n, 1).unwrap();
    let source_two = DiscreteMatRef::new(&source_two, n, 1).unwrap();
    let source_three = DiscreteMatRef::new(&source_three, n, 1).unwrap();
    let target = DiscreteMatRef::new(&target, n, 1).unwrap();

    let original =
        discrete_sxpid_n(&[source_zero, source_one, source_two, source_three], target).unwrap();
    let swapped =
        discrete_sxpid_n(&[source_one, source_zero, source_two, source_three], target).unwrap();
    let original_averaged =
        discrete_sxpid_n_averaged(&[source_zero, source_one, source_two, source_three], target)
            .unwrap();
    let swapped_averaged =
        discrete_sxpid_n_averaged(&[source_one, source_zero, source_two, source_three], target)
            .unwrap();

    let expected = [
        0x3f73_2f6d_ea98_a14d,
        0x3f72_1964_bc3d_4223,
        0x3f31_6092_e5b5_f2a0,
    ];
    for atom in [
        original.atom(&[0b0001, 0b0100, 0b1010]).unwrap(),
        swapped.atom(&[0b0010, 0b0100, 0b1001]).unwrap(),
        original_averaged.atom(&[0b0001, 0b0100, 0b1010]).unwrap(),
        swapped_averaged.atom(&[0b0010, 0b0100, 0b1001]).unwrap(),
    ] {
        assert_eq!(averaged_atom_bits(atom), expected);
    }

    let original_index = original
        .antichains
        .iter()
        .position(|antichain| antichain == &[0b0001, 0b0100, 0b1010])
        .unwrap();
    let swapped_index = swapped
        .antichains
        .iter()
        .position(|antichain| antichain == &[0b0010, 0b0100, 0b1001])
        .unwrap();
    let historical_original = historical_average_bits(
        original
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.atoms[original_index])),
    );
    let historical_swapped = historical_average_bits(
        swapped
            .pointwise
            .iter()
            .map(|point| (point.empirical_probability, point.atoms[swapped_index])),
    );
    assert_eq!(historical_original[1], 0x3f72_1964_bc3d_4223);
    assert_eq!(historical_swapped[1], 0x3f72_1964_bc3d_4222);
    assert_eq!(historical_original[2], 0x3f31_6092_e5b5_f2a0);
    assert_eq!(historical_swapped[2], 0x3f31_6092_e5b5_f2b0);
    assert_ne!(historical_original, historical_swapped);
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
