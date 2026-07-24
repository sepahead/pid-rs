//! Bounded executable checks for support-change-tolerant categorical SxPID bounds.
//!
//! Each check fixes one finite row table and a full redundancy lattice. The table
//! embeds in the complete Cartesian product of its coordinate alphabets; unlisted
//! product cells have implicit zero mass under both compared laws. The checks
//! permit listed cells to enter or leave support without assuming a positive
//! support-mass floor. The fixture generator is implementation-separated from
//! pid-rs and uses exact rational probabilities plus high-precision Decimal
//! logarithms. Decimal strings are reference values only: the Rust side
//! reconstructs event probabilities, lattice inversion, pointwise atoms, and
//! every tested bound directly from the raw count tables. This bounded replay is
//! not a universal proof, a certified real enclosure, or authorship-independent
//! review.

use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

use pid_core::stable::categorical::{
    discrete_sxpid_n, DiscreteSxPidNResult, SxAveragedAtom, SxPointwiseAtom,
};
use pid_core::DiscreteMatRef;
use serde::Deserialize;

const FIXTURE_BYTES: &[u8] = include_bytes!("fixtures/support_change_tolerant_sxpid_oracle.json");
const FIXTURE_CHECKSUM: &str =
    include_str!("fixtures/support_change_tolerant_sxpid_oracle.json.sha256");
const GENERATOR_BYTES: &[u8] =
    include_bytes!("../../../scripts/generate-support-change-tolerant-sxpid-oracle.py");

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Fixture {
    arithmetic: Arithmetic,
    bound_formulae: BoundFormulae,
    fannes_falsifiers: Vec<FannesFalsifier>,
    generator: Generator,
    law_pairs: Vec<LawPair>,
    mobius_cases: Vec<MobiusCase>,
    net_residual_shortcut: NetResidualShortcut,
    nonclaims: Vec<String>,
    rare_support_cases: Vec<RareSupportCase>,
    schema: String,
    schema_revision: usize,
    seeded_corpus: SeededCorpus,
    sharp_gamma_cases: Vec<SharpGammaCase>,
    tested_domain: TestedDomain,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Arithmetic {
    decimal_precision_digits: usize,
    decimal_reference_digits: usize,
    decimal_role: String,
    fraction_arithmetic: String,
    logarithm: String,
    third_party_dependencies: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct BoundFormulae {
    direct_minus: String,
    direct_net: String,
    direct_plus: String,
    ell: String,
    gamma_j: String,
    mobius_minus: String,
    mobius_net: String,
    mobius_plus: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Generator {
    imports_pid_rs: bool,
    path: String,
    sha256: String,
    standard_library_only: bool,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedComponents {
    informative_nats: String,
    misinformative_nats: String,
    net_nats: String,
    sets: Vec<u8>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct ExpectedLaw {
    atoms: Vec<ExpectedComponents>,
    joint_mi_nats: String,
    subset_mis_nats: Vec<String>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct LawPair {
    category: String,
    evidence_boundary: String,
    name: String,
    p_counts: Vec<usize>,
    p_expected: ExpectedLaw,
    p_probabilities: Vec<String>,
    q_counts: Vec<usize>,
    q_expected: ExpectedLaw,
    q_probabilities: Vec<String>,
    realizations: Vec<Vec<usize>>,
    source_count: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct FannesFalsifier {
    alphabet_size: usize,
    branch_count: usize,
    common_term_absolute_nats: String,
    difference_nats: String,
    eta: String,
    exact_inequality: String,
    exact_inequality_lhs: u128,
    exact_inequality_rhs: u128,
    fannes_nats: String,
    gamma_j_nats: String,
    gamma_sharp: bool,
    node_masks: Vec<u8>,
    pair_name: String,
    residual_entropy_nats: String,
    strict_excess_nats: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SharpGammaCase {
    branch_count: usize,
    common_term_absolute_nats: String,
    eta: String,
    gamma_j_nats: String,
    node_masks: Vec<u8>,
    pair_name: String,
    residual_entropy_nats: String,
    total_difference_nats: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RareSupportCase {
    averaged_unique_s1_nats: String,
    epsilon: String,
    exponent: u32,
    l1_distance: String,
    node_masks: Vec<u8>,
    pair_name: String,
    rare_pointwise_informative_nats: String,
    rare_pointwise_misinformative_nats: String,
    rare_pointwise_net_nats: String,
    rare_realization: Vec<usize>,
    unique_to_l1_ratio: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct NetResidualShortcut {
    eta: String,
    exact_inequality: String,
    left_pointwise_net_closed_form: String,
    left_pointwise_net_nats: String,
    left_residual_realization: Vec<usize>,
    max_residual_entropy_nats: String,
    node_masks: Vec<u8>,
    pair_name: String,
    residual_difference_closed_form: String,
    residual_difference_nats: String,
    right_pointwise_net_closed_form: String,
    right_pointwise_net_nats: String,
    right_residual_realization: Vec<usize>,
    strict_excess_nats: String,
    whole_common_term_closed_form: String,
    whole_common_term_nats: String,
    whole_unique_net_difference_closed_form: String,
    whole_unique_net_difference_nats: String,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct MobiusCase {
    bottom_node_masks: Vec<u8>,
    coefficient_counts: Vec<CoefficientCount>,
    max_absolute_row_norm: usize,
    node_count: usize,
    row_norm_histogram: Vec<RowNormCount>,
    row_sum_one_count: usize,
    row_sum_zero_count: usize,
    source_count: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct CoefficientCount {
    coefficient: i64,
    count: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct RowNormCount {
    count: usize,
    norm: usize,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct SeededCorpus {
    algorithm: String,
    case_names: Vec<String>,
    cases_per_source_count: usize,
    seed_decimal: String,
    source_counts: Vec<usize>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct TestedDomain {
    bound_components_per_node: Vec<String>,
    lattice_node_counts: Vec<LatticeNodeCount>,
    law_pair_count: usize,
    public_count_tables_replayed: usize,
    public_rust_route: String,
    source_counts: Vec<usize>,
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct LatticeNodeCount {
    node_count: usize,
    source_count: usize,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct Rational {
    numerator: u128,
    denominator: u128,
}

impl Rational {
    const ZERO: Self = Self {
        numerator: 0,
        denominator: 1,
    };

    const ONE: Self = Self {
        numerator: 1,
        denominator: 1,
    };

    fn new(numerator: u128, denominator: u128) -> Self {
        assert!(denominator > 0);
        let divisor = gcd(numerator, denominator);
        Self {
            numerator: numerator / divisor,
            denominator: denominator / divisor,
        }
    }

    fn parse(text: &str) -> Self {
        let (numerator, denominator) = text
            .split_once('/')
            .unwrap_or_else(|| panic!("rational must contain '/': {text}"));
        Self::new(
            numerator.parse().expect("rational numerator must be u128"),
            denominator
                .parse()
                .expect("rational denominator must be u128"),
        )
    }

    fn from_count(count: usize, total: usize) -> Self {
        Self::new(count as u128, total as u128)
    }

    fn add(self, other: Self) -> Self {
        let divisor = gcd(self.denominator, other.denominator);
        let left_scale = other.denominator / divisor;
        let right_scale = self.denominator / divisor;
        Self::new(
            self.numerator * left_scale + other.numerator * right_scale,
            self.denominator * left_scale,
        )
    }

    fn subtract(self, other: Self) -> Self {
        assert!(self >= other);
        let divisor = gcd(self.denominator, other.denominator);
        let left_scale = other.denominator / divisor;
        let right_scale = self.denominator / divisor;
        Self::new(
            self.numerator * left_scale - other.numerator * right_scale,
            self.denominator * left_scale,
        )
    }

    fn divide_by(self, divisor: u128) -> Self {
        Self::new(self.numerator, self.denominator * divisor)
    }

    fn multiply_by(self, factor: u128) -> Self {
        Self::new(self.numerator * factor, self.denominator)
    }

    fn absolute_difference(self, other: Self) -> Self {
        if self >= other {
            self.subtract(other)
        } else {
            other.subtract(self)
        }
    }

    fn to_f64(self) -> f64 {
        self.numerator as f64 / self.denominator as f64
    }
}

impl Ord for Rational {
    fn cmp(&self, other: &Self) -> Ordering {
        (self.numerator * other.denominator).cmp(&(other.numerator * self.denominator))
    }
}

impl PartialOrd for Rational {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

fn gcd(mut left: u128, mut right: u128) -> u128 {
    while right != 0 {
        (left, right) = (right, left % right);
    }
    left.max(1)
}

#[derive(Clone, Copy, Debug)]
struct Components {
    informative: f64,
    misinformative: f64,
    net: f64,
}

impl Components {
    const ZERO: Self = Self {
        informative: 0.0,
        misinformative: 0.0,
        net: 0.0,
    };

    fn add_scaled(&mut self, coefficient: i64, value: Self) {
        let coefficient = coefficient as f64;
        self.informative += coefficient * value.informative;
        self.misinformative += coefficient * value.misinformative;
        self.net += coefficient * value.net;
    }

    fn values(self) -> [f64; 3] {
        [self.informative, self.misinformative, self.net]
    }
}

#[derive(Debug)]
struct Lattice {
    nodes: Vec<Vec<u8>>,
    matrix: Vec<Vec<i64>>,
}

fn antichain_leq(lower: &[u8], upper: &[u8]) -> bool {
    upper.iter().all(|&upper_mask| {
        lower
            .iter()
            .any(|&lower_mask| lower_mask & !upper_mask == 0)
    })
}

fn lattice(source_count: usize) -> Lattice {
    assert!((2..=4).contains(&source_count));
    let mask_count = (1usize << source_count) - 1;
    let mut nodes = Vec::new();
    for selection in 1usize..(1usize << mask_count) {
        let node: Vec<u8> = (0..mask_count)
            .filter(|bit| selection & (1usize << bit) != 0)
            .map(|bit| (bit + 1) as u8)
            .collect();
        let is_antichain = node.iter().enumerate().all(|(left_index, &left)| {
            node.iter()
                .skip(left_index + 1)
                .all(|&right| left & right != left && left & right != right)
        });
        if is_antichain {
            nodes.push(node);
        }
    }
    nodes.sort_by(|left, right| (left.len(), left).cmp(&(right.len(), right)));

    let predecessors: Vec<Vec<usize>> = (0..nodes.len())
        .map(|upper| {
            (0..nodes.len())
                .filter(|&lower| lower != upper && antichain_leq(&nodes[lower], &nodes[upper]))
                .collect()
        })
        .collect();
    let mut remaining: BTreeSet<usize> = (0..nodes.len()).collect();
    let mut order = Vec::with_capacity(nodes.len());
    while !remaining.is_empty() {
        let ready: Vec<usize> = remaining
            .iter()
            .copied()
            .filter(|&node| {
                predecessors[node]
                    .iter()
                    .all(|lower| !remaining.contains(lower))
            })
            .collect();
        assert!(!ready.is_empty(), "redundancy lattice contains a cycle");
        for node in ready {
            remaining.remove(&node);
            order.push(node);
        }
    }

    let mut matrix = vec![vec![0i64; nodes.len()]; nodes.len()];
    for row in order {
        matrix[row][row] = 1;
        for &lower in &predecessors[row] {
            let lower_row = matrix[lower].clone();
            for (coefficient, lower_coefficient) in matrix[row].iter_mut().zip(lower_row) {
                *coefficient -= lower_coefficient;
            }
        }
    }
    for (upper, node) in nodes.iter().enumerate() {
        for column in 0..nodes.len() {
            let reconstructed: i64 = matrix
                .iter()
                .enumerate()
                .filter(|(lower, _)| antichain_leq(&nodes[*lower], node))
                .map(|(_, row)| row[column])
                .sum();
            assert_eq!(reconstructed, i64::from(upper == column));
        }
    }
    Lattice { nodes, matrix }
}

#[derive(Debug)]
struct OracleLaw {
    cumulatives: Vec<Components>,
    atoms: Vec<Components>,
    pointwise: BTreeMap<Vec<usize>, Vec<Components>>,
    joint_mi: f64,
    subset_mis: Vec<f64>,
}

fn probabilities(counts: &[usize]) -> Vec<Rational> {
    let total: usize = counts.iter().sum();
    assert!(total > 0);
    counts
        .iter()
        .map(|&count| Rational::from_count(count, total))
        .collect()
}

fn event_masses(
    realizations: &[Vec<usize>],
    probabilities: &[Rational],
    source_count: usize,
    node: &[u8],
    realization_index: usize,
) -> (Rational, Rational, Rational) {
    let realization = &realizations[realization_index];
    let mut source_mass = Rational::ZERO;
    let mut joint_mass = Rational::ZERO;
    let mut target_mass = Rational::ZERO;
    for (other, (candidate, &probability)) in realizations.iter().zip(probabilities).enumerate() {
        let source_union = node.iter().any(|&mask| {
            (0..source_count)
                .filter(|source| mask & (1 << source) != 0)
                .all(|source| realization[source] == candidate[source])
        });
        let target_equal = realization[source_count] == candidate[source_count];
        if source_union {
            source_mass = source_mass.add(probability);
        }
        if source_union && target_equal {
            joint_mass = joint_mass.add(probability);
        }
        if target_equal {
            target_mass = target_mass.add(probability);
        }
        let _ = other;
    }
    (source_mass, joint_mass, target_mass)
}

fn local_cumulative(
    realizations: &[Vec<usize>],
    probabilities: &[Rational],
    source_count: usize,
    node: &[u8],
    realization_index: usize,
) -> Components {
    let (source_mass, joint_mass, target_mass) = event_masses(
        realizations,
        probabilities,
        source_count,
        node,
        realization_index,
    );
    assert!(source_mass > Rational::ZERO);
    assert!(joint_mass > Rational::ZERO);
    assert!(target_mass > Rational::ZERO);
    let informative = -source_mass.to_f64().ln();
    let misinformative = (target_mass.to_f64() / joint_mass.to_f64()).ln();
    Components {
        informative,
        misinformative,
        net: informative - misinformative,
    }
}

fn invert_components(lattice: &Lattice, cumulatives: &[Components]) -> Vec<Components> {
    lattice
        .matrix
        .iter()
        .map(|row| {
            let mut atom = Components::ZERO;
            for (&coefficient, &cumulative) in row.iter().zip(cumulatives) {
                atom.add_scaled(coefficient, cumulative);
            }
            atom
        })
        .collect()
}

fn oracle_law(pair: &LawPair, counts: &[usize], lattice: &Lattice) -> OracleLaw {
    let probabilities = probabilities(counts);
    let mut cumulatives = vec![Components::ZERO; lattice.nodes.len()];
    for (node_index, node) in lattice.nodes.iter().enumerate() {
        for (realization_index, probability) in probabilities.iter().enumerate() {
            if *probability == Rational::ZERO {
                continue;
            }
            let local = local_cumulative(
                &pair.realizations,
                &probabilities,
                pair.source_count,
                node,
                realization_index,
            );
            let weight = probability.to_f64();
            cumulatives[node_index].informative += weight * local.informative;
            cumulatives[node_index].misinformative += weight * local.misinformative;
            cumulatives[node_index].net += weight * local.net;
        }
    }
    let atoms = invert_components(lattice, &cumulatives);
    let pointwise = pair
        .realizations
        .iter()
        .enumerate()
        .filter(|(index, _)| probabilities[*index] != Rational::ZERO)
        .map(|(realization_index, realization)| {
            let local_cumulatives: Vec<Components> = lattice
                .nodes
                .iter()
                .map(|node| {
                    local_cumulative(
                        &pair.realizations,
                        &probabilities,
                        pair.source_count,
                        node,
                        realization_index,
                    )
                })
                .collect();
            (
                realization.clone(),
                invert_components(lattice, &local_cumulatives),
            )
        })
        .collect();
    let joint_mi = atoms.iter().map(|atom| atom.net).sum();
    let subset_mis = (1..(1u8 << pair.source_count))
        .map(|mask| {
            let index = lattice
                .nodes
                .iter()
                .position(|node| node.as_slice() == [mask])
                .expect("singleton cumulative must exist");
            cumulatives[index].net
        })
        .collect();
    OracleLaw {
        cumulatives,
        atoms,
        pointwise,
        joint_mi,
        subset_mis,
    }
}

struct ExpandedTable {
    sources: Vec<Vec<usize>>,
    target: Vec<usize>,
}

impl ExpandedTable {
    fn source_refs(&self) -> Vec<DiscreteMatRef<'_>> {
        self.sources
            .iter()
            .map(|source| {
                DiscreteMatRef::new(source, self.target.len(), 1)
                    .expect("expanded source shape must be valid")
            })
            .collect()
    }

    fn target_ref(&self) -> DiscreteMatRef<'_> {
        DiscreteMatRef::new(&self.target, self.target.len(), 1)
            .expect("expanded target shape must be valid")
    }
}

fn expand(pair: &LawPair, counts: &[usize]) -> ExpandedTable {
    assert_eq!(pair.realizations.len(), counts.len());
    let total: usize = counts.iter().sum();
    let mut sources = (0..pair.source_count)
        .map(|_| Vec::with_capacity(total))
        .collect::<Vec<_>>();
    let mut target = Vec::with_capacity(total);
    for (realization, &count) in pair.realizations.iter().zip(counts) {
        assert_eq!(realization.len(), pair.source_count + 1);
        for _ in 0..count {
            for (source, values) in sources.iter_mut().enumerate() {
                values.push(realization[source]);
            }
            target.push(realization[pair.source_count]);
        }
    }
    ExpandedTable { sources, target }
}

fn evaluate_public(pair: &LawPair, counts: &[usize]) -> DiscreteSxPidNResult {
    let table = expand(pair, counts);
    discrete_sxpid_n(&table.source_refs(), table.target_ref())
        .unwrap_or_else(|error| panic!("{} public SxPID failed: {error}", pair.name))
}

fn fixture() -> Fixture {
    let expected_digest = FIXTURE_CHECKSUM
        .split_whitespace()
        .next()
        .expect("fixture checksum must contain a digest");
    assert_eq!(
        pid_runlog::sha256_hex(FIXTURE_BYTES),
        expected_digest,
        "support-change-tolerant fixture bytes do not match their SHA-256 sidecar"
    );
    serde_json::from_slice(FIXTURE_BYTES)
        .expect("support-change-tolerant fixture must contain valid, schema-exact JSON")
}

fn parse_decimal(text: &str) -> f64 {
    let parsed = text
        .parse::<f64>()
        .unwrap_or_else(|error| panic!("invalid Decimal reference {text:?}: {error}"));
    assert!(parsed.is_finite());
    parsed
}

fn tolerance(source_count: usize, scale: f64) -> f64 {
    // Scoped to these committed finite tables. The larger four-source allowance
    // covers cancellation through the 166-node inversion; it is not a universal
    // binary64 error theorem.
    let epsilon_units = match source_count {
        2 => 96.0,
        3 => 256.0,
        4 => 1024.0,
        _ => panic!("unsupported source count"),
    };
    epsilon_units * f64::EPSILON * scale.abs().max(1.0)
}

fn assert_close(label: &str, actual: f64, expected: f64, source_count: usize) {
    let allowed = tolerance(source_count, actual.abs().max(expected.abs()));
    assert!(
        actual.is_finite() && (actual - expected).abs() <= allowed,
        "{label}: actual={actual:.17e}, expected={expected:.17e}, \
         error={:.17e}, allowed={allowed:.17e}",
        (actual - expected).abs()
    );
}

fn expected_components(expected: &ExpectedComponents) -> Components {
    Components {
        informative: parse_decimal(&expected.informative_nats),
        misinformative: parse_decimal(&expected.misinformative_nats),
        net: parse_decimal(&expected.net_nats),
    }
}

fn public_pointwise_key(realization: &[Vec<usize>]) -> Vec<usize> {
    realization
        .iter()
        .map(|variable| {
            assert_eq!(variable.len(), 1);
            variable[0]
        })
        .collect()
}

fn compare_pointwise_atom(
    label: &str,
    actual: SxPointwiseAtom,
    expected: Components,
    source_count: usize,
) {
    for (component, actual_value, expected_value) in [
        (
            "informative",
            actual.informative_nats(),
            expected.informative,
        ),
        (
            "misinformative",
            actual.misinformative_nats(),
            expected.misinformative,
        ),
        ("net", actual.net_nats(), expected.net),
    ] {
        assert_close(
            &format!("{label} {component}"),
            actual_value,
            expected_value,
            source_count,
        );
    }
}

fn compare_averaged_atom(
    label: &str,
    actual: SxAveragedAtom,
    expected: Components,
    source_count: usize,
) {
    for (component, actual_value, expected_value) in [
        (
            "informative",
            actual.informative_nats(),
            expected.informative,
        ),
        (
            "misinformative",
            actual.misinformative_nats(),
            expected.misinformative,
        ),
        ("net", actual.net_nats(), expected.net),
    ] {
        assert_close(
            &format!("{label} {component}"),
            actual_value,
            expected_value,
            source_count,
        );
    }
}

fn compare_law(
    pair: &LawPair,
    side: &str,
    counts: &[usize],
    rational_references: &[String],
    decimal_reference: &ExpectedLaw,
    lattice: &Lattice,
) {
    let exact_probabilities = probabilities(counts);
    assert_eq!(exact_probabilities.len(), rational_references.len());
    for (index, (&actual, expected)) in exact_probabilities
        .iter()
        .zip(rational_references)
        .enumerate()
    {
        assert_eq!(
            actual,
            Rational::parse(expected),
            "{} {side} rational probability {index}",
            pair.name
        );
    }

    let oracle = oracle_law(pair, counts, lattice);
    assert_eq!(oracle.atoms.len(), decimal_reference.atoms.len());
    for expected in &decimal_reference.atoms {
        let index = lattice
            .nodes
            .iter()
            .position(|node| node == &expected.sets)
            .unwrap_or_else(|| {
                panic!(
                    "{} {side} reference contains unknown node {:?}",
                    pair.name, expected.sets
                )
            });
        let expected = expected_components(expected);
        for (component, actual, reference) in [
            (
                "informative",
                oracle.atoms[index].informative,
                expected.informative,
            ),
            (
                "misinformative",
                oracle.atoms[index].misinformative,
                expected.misinformative,
            ),
            ("net", oracle.atoms[index].net, expected.net),
        ] {
            assert_close(
                &format!(
                    "{} {side} Rust-oracle {component} {:?}",
                    pair.name, lattice.nodes[index]
                ),
                actual,
                reference,
                pair.source_count,
            );
        }
    }
    assert_close(
        &format!("{} {side} Rust-oracle joint MI", pair.name),
        oracle.joint_mi,
        parse_decimal(&decimal_reference.joint_mi_nats),
        pair.source_count,
    );
    assert_eq!(
        oracle.subset_mis.len(),
        decimal_reference.subset_mis_nats.len()
    );
    for (mask, (&actual, reference)) in oracle
        .subset_mis
        .iter()
        .zip(&decimal_reference.subset_mis_nats)
        .enumerate()
    {
        assert_close(
            &format!("{} {side} Rust-oracle subset MI {}", pair.name, mask + 1),
            actual,
            parse_decimal(reference),
            pair.source_count,
        );
    }

    let public = evaluate_public(pair, counts);
    assert_eq!(public.n_sources, pair.source_count);
    assert!(public.pointwise_included);
    assert_eq!(public.antichains.len(), lattice.nodes.len());
    for (index, node) in lattice.nodes.iter().enumerate() {
        let public_index = public
            .antichains
            .iter()
            .position(|candidate| candidate == node)
            .unwrap_or_else(|| panic!("{} public result omitted node {node:?}", pair.name));
        compare_averaged_atom(
            &format!("{} {side} public averaged {node:?}", pair.name),
            public.atoms[public_index],
            oracle.atoms[index],
            pair.source_count,
        );
    }
    assert_close(
        &format!("{} {side} public joint MI", pair.name),
        public.joint_mi,
        oracle.joint_mi,
        pair.source_count,
    );
    assert_eq!(public.subset_mis.len(), oracle.subset_mis.len());
    for (mask, (&actual, &expected)) in public.subset_mis.iter().zip(&oracle.subset_mis).enumerate()
    {
        assert_close(
            &format!("{} {side} public subset MI {}", pair.name, mask + 1),
            actual,
            expected,
            pair.source_count,
        );
    }

    let public_points: BTreeMap<Vec<usize>, _> = public
        .pointwise
        .iter()
        .map(|point| (public_pointwise_key(&point.realization), point))
        .collect();
    assert_eq!(public_points.len(), oracle.pointwise.len());
    let total: usize = counts.iter().sum();
    for (realization, expected_atoms) in &oracle.pointwise {
        let point = public_points.get(realization).unwrap_or_else(|| {
            panic!(
                "{} {side} public result omitted pointwise realization {realization:?}",
                pair.name
            )
        });
        let realization_index = pair
            .realizations
            .iter()
            .position(|candidate| candidate == realization)
            .unwrap();
        assert_eq!(point.empirical_count, counts[realization_index]);
        assert_close(
            &format!("{} {side} pointwise probability {realization:?}", pair.name),
            point.empirical_probability,
            counts[realization_index] as f64 / total as f64,
            pair.source_count,
        );
        assert_eq!(point.atoms.len(), lattice.nodes.len());
        for (node_index, node) in lattice.nodes.iter().enumerate() {
            let public_index = public
                .antichains
                .iter()
                .position(|candidate| candidate == node)
                .unwrap();
            compare_pointwise_atom(
                &format!(
                    "{} {side} public pointwise {realization:?} {node:?}",
                    pair.name
                ),
                point.atoms[public_index],
                expected_atoms[node_index],
                pair.source_count,
            );
        }
    }
}

fn residuals(
    left: &[Rational],
    right: &[Rational],
) -> (Vec<Rational>, Vec<Rational>, Vec<Rational>, Rational) {
    assert_eq!(left.len(), right.len());
    let common: Vec<Rational> = left.iter().zip(right).map(|(&x, &y)| x.min(y)).collect();
    let left_residual: Vec<Rational> = left
        .iter()
        .zip(&common)
        .map(|(&value, &overlap)| value.subtract(overlap))
        .collect();
    let right_residual: Vec<Rational> = right
        .iter()
        .zip(&common)
        .map(|(&value, &overlap)| value.subtract(overlap))
        .collect();
    let left_mass = left_residual
        .iter()
        .copied()
        .fold(Rational::ZERO, Rational::add);
    let right_mass = right_residual
        .iter()
        .copied()
        .fold(Rational::ZERO, Rational::add);
    assert_eq!(left_mass, right_mass);
    let variation = left
        .iter()
        .zip(right)
        .map(|(&x, &y)| x.absolute_difference(y))
        .fold(Rational::ZERO, Rational::add)
        .divide_by(2);
    assert_eq!(left_mass, variation);
    let common_mass = common.iter().copied().fold(Rational::ZERO, Rational::add);
    assert_eq!(common_mass.add(variation), Rational::ONE);
    (common, left_residual, right_residual, variation)
}

fn subprobability_entropy(values: &[Rational]) -> f64 {
    values
        .iter()
        .filter(|&&value| value != Rational::ZERO)
        .map(|&value| -value.to_f64() * value.to_f64().ln())
        .sum()
}

fn binary_entropy(value: Rational) -> f64 {
    subprobability_entropy(&[value, Rational::ONE.subtract(value)])
}

fn ell(eta: Rational) -> f64 {
    let retained = Rational::ONE.subtract(eta);
    if retained == Rational::ZERO {
        0.0
    } else {
        -retained.to_f64() * retained.to_f64().ln()
    }
}

fn gamma_union(branch_count: usize, eta: Rational) -> f64 {
    let retained = Rational::ONE.subtract(eta);
    if retained == Rational::ZERO {
        return 0.0;
    }
    let retained = retained.to_f64();
    retained * (1.0 + branch_count as f64 * eta.to_f64() / retained).ln()
}

fn fannes(alphabet_size: usize, eta: Rational) -> f64 {
    assert!(alphabet_size >= 2);
    if eta > Rational::new((alphabet_size - 1) as u128, alphabet_size as u128) {
        (alphabet_size as f64).ln()
    } else {
        binary_entropy(eta) + eta.to_f64() * ((alphabet_size - 1) as f64).ln()
    }
}

fn check_pair_bounds(pair: &LawPair, lattice: &Lattice) {
    let p = probabilities(&pair.p_counts);
    let q = probabilities(&pair.q_counts);
    let p_law = oracle_law(pair, &pair.p_counts, lattice);
    let q_law = oracle_law(pair, &pair.q_counts, lattice);
    let (_common, left_residual, right_residual, eta) = residuals(&p, &q);
    let entropy_left = subprobability_entropy(&left_residual);
    let entropy_right = subprobability_entropy(&right_residual);
    let entropy_max = entropy_left.max(entropy_right);
    let ell_value = ell(eta);
    let gammas: Vec<f64> = lattice
        .nodes
        .iter()
        .map(|node| gamma_union(node.len(), eta))
        .collect();

    for (node_index, node) in lattice.nodes.iter().enumerate() {
        let direct_bounds = [
            entropy_max + gammas[node_index],
            entropy_max + gammas[node_index] + ell_value,
            entropy_left + entropy_right + 2.0 * gammas[node_index] + ell_value,
        ];
        for (component, ((&left, &right), &bound)) in
            ["informative", "misinformative", "net"].into_iter().zip(
                p_law.cumulatives[node_index]
                    .values()
                    .iter()
                    .zip(q_law.cumulatives[node_index].values().iter())
                    .zip(direct_bounds.iter()),
            )
        {
            let difference = (left - right).abs();
            let allowed = tolerance(pair.source_count, bound.max(difference)) * 4.0;
            assert!(
                difference <= bound + allowed,
                "{} direct {component} {node:?}: difference={difference:.17e}, \
                 bound={bound:.17e}, allowed={allowed:.17e}",
                pair.name
            );
        }
    }

    for (row_index, (node, row)) in lattice.nodes.iter().zip(&lattice.matrix).enumerate() {
        let row_sum: i64 = row.iter().sum();
        let weighted_gamma: f64 = row
            .iter()
            .zip(&gammas)
            .map(|(&coefficient, &gamma)| coefficient.unsigned_abs() as f64 * gamma)
            .sum();
        let atom_bounds = [
            entropy_max + weighted_gamma,
            entropy_max + weighted_gamma + row_sum.unsigned_abs() as f64 * ell_value,
            entropy_left
                + entropy_right
                + 2.0 * weighted_gamma
                + row_sum.unsigned_abs() as f64 * ell_value,
        ];
        for (component, ((&left, &right), &bound)) in
            ["informative", "misinformative", "net"].into_iter().zip(
                p_law.atoms[row_index]
                    .values()
                    .iter()
                    .zip(q_law.atoms[row_index].values().iter())
                    .zip(atom_bounds.iter()),
            )
        {
            let difference = (left - right).abs();
            let allowed = tolerance(pair.source_count, bound.max(difference)) * 4.0;
            assert!(
                difference <= bound + allowed,
                "{} atom {component} {node:?}: difference={difference:.17e}, \
                 bound={bound:.17e}, allowed={allowed:.17e}",
                pair.name
            );
        }
    }
}

fn pair_by_name<'a>(fixture: &'a Fixture, name: &str) -> &'a LawPair {
    fixture
        .law_pairs
        .iter()
        .find(|pair| pair.name == name)
        .unwrap_or_else(|| panic!("fixture omitted law pair {name:?}"))
}

fn node_index(lattice: &Lattice, node: &[u8]) -> usize {
    lattice
        .nodes
        .iter()
        .position(|candidate| candidate == node)
        .unwrap_or_else(|| panic!("lattice omitted node {node:?}"))
}

fn public_pointwise_atom(
    pair: &LawPair,
    counts: &[usize],
    realization: &[usize],
    node: &[u8],
) -> SxPointwiseAtom {
    let result = evaluate_public(pair, counts);
    let point = result
        .pointwise
        .iter()
        .find(|point| public_pointwise_key(&point.realization) == realization)
        .unwrap_or_else(|| {
            panic!(
                "{} public result omitted realization {realization:?}",
                pair.name
            )
        });
    let index = result
        .antichains
        .iter()
        .position(|candidate| candidate == node)
        .unwrap_or_else(|| panic!("{} public result omitted node {node:?}", pair.name));
    point.atoms[index]
}

#[test]
fn fixture_identity_scope_and_tested_domain_are_bound() {
    let fixture = fixture();
    assert_eq!(
        fixture.schema,
        "pid-rs/support-change-tolerant-sxpid-oracle"
    );
    assert_eq!(fixture.schema_revision, 1);
    assert_eq!(fixture.arithmetic.decimal_precision_digits, 160);
    assert_eq!(fixture.arithmetic.decimal_reference_digits, 80);
    assert_eq!(
        fixture.arithmetic.decimal_role,
        "reference values for scoped binary64 comparisons only; not certified real-number enclosures"
    );
    assert_eq!(fixture.arithmetic.fraction_arithmetic, "exact");
    assert_eq!(fixture.arithmetic.logarithm, "natural");
    assert!(fixture.arithmetic.third_party_dependencies.is_empty());
    assert!(!fixture.generator.imports_pid_rs);
    assert!(fixture.generator.standard_library_only);
    assert_eq!(
        fixture.generator.path,
        "scripts/generate-support-change-tolerant-sxpid-oracle.py"
    );
    assert_eq!(
        fixture.generator.sha256,
        pid_runlog::sha256_hex(GENERATOR_BYTES),
        "fixture generator identity is stale"
    );

    assert_eq!(fixture.tested_domain.source_counts, [2, 3, 4]);
    assert_eq!(
        fixture.tested_domain.law_pair_count,
        fixture.law_pairs.len()
    );
    assert_eq!(
        fixture.tested_domain.public_count_tables_replayed,
        2 * fixture.law_pairs.len()
    );
    assert_eq!(
        fixture.tested_domain.public_rust_route,
        "pid_core::stable::categorical::discrete_sxpid_n"
    );
    assert_eq!(
        fixture
            .tested_domain
            .lattice_node_counts
            .iter()
            .map(|entry| (entry.source_count, entry.node_count))
            .collect::<Vec<_>>(),
        [(2, 4), (3, 18), (4, 166)]
    );
    assert_eq!(
        fixture.tested_domain.bound_components_per_node,
        [
            "cumulative informative",
            "cumulative misinformative",
            "cumulative net",
            "atom informative",
            "atom misinformative",
            "atom net",
        ]
    );
    assert_eq!(fixture.seeded_corpus.source_counts, [2, 3, 4]);
    assert_eq!(fixture.seeded_corpus.cases_per_source_count, 2);
    assert_eq!(
        fixture.seeded_corpus.algorithm,
        "SplitMix64 with modulo-bounded draws"
    );
    assert_eq!(fixture.seeded_corpus.seed_decimal, "6005638378708485714");
    assert_eq!(fixture.seeded_corpus.case_names.len(), 6);

    let names: BTreeSet<_> = fixture
        .law_pairs
        .iter()
        .map(|pair| pair.name.as_str())
        .collect();
    assert_eq!(names.len(), fixture.law_pairs.len());
    for pair in &fixture.law_pairs {
        assert!(!pair.category.is_empty());
        assert!(!pair.evidence_boundary.is_empty());
    }
    for name in &fixture.seeded_corpus.case_names {
        assert!(names.contains(name.as_str()));
    }

    assert_eq!(
        [
            fixture.bound_formulae.direct_plus.as_str(),
            fixture.bound_formulae.direct_minus.as_str(),
            fixture.bound_formulae.direct_net.as_str(),
            fixture.bound_formulae.ell.as_str(),
            fixture.bound_formulae.gamma_j.as_str(),
            fixture.bound_formulae.mobius_plus.as_str(),
            fixture.bound_formulae.mobius_minus.as_str(),
            fixture.bound_formulae.mobius_net.as_str(),
        ],
        [
            "Emax + gamma_J(A)",
            "Emax + gamma_J(B) + ell",
            "Ea + Eb + gamma_J(A) + gamma_J(B) + ell",
            "-(1-eta) ln(1-eta)",
            "(1-eta) ln(1 + J eta/(1-eta)); gamma_j(1)=0 at eta=1",
            "Emax + sum |M| gamma_J(A)",
            "Emax + sum |M| gamma_J(B) + |row_sum| ell",
            "Ea + Eb + sum |M|(gamma_J(A)+gamma_J(B)) + |row_sum| ell",
        ]
    );
    assert_eq!(fixture.nonclaims.len(), 8);
    assert!(fixture
        .nonclaims
        .iter()
        .any(|claim| claim.contains("not certified real-number bounds")));
    assert!(fixture
        .nonclaims
        .iter()
        .any(|claim| claim.contains("does not prove its asymptotic coefficient-two limit")));
}

#[test]
fn exact_mobius_rows_and_norms_match_two_through_four_source_fixture() {
    let fixture = fixture();
    assert_eq!(fixture.mobius_cases.len(), 3);
    for expected in &fixture.mobius_cases {
        let lattice = lattice(expected.source_count);
        assert_eq!(lattice.nodes.len(), expected.node_count);
        let bottom: Vec<u8> = (0..expected.source_count)
            .map(|source| 1u8 << source)
            .collect();
        assert_eq!(expected.bottom_node_masks, bottom);

        let row_sums: Vec<i64> = lattice.matrix.iter().map(|row| row.iter().sum()).collect();
        assert_eq!(
            row_sums.iter().filter(|&&value| value == 1).count(),
            expected.row_sum_one_count
        );
        assert_eq!(
            row_sums.iter().filter(|&&value| value == 0).count(),
            expected.row_sum_zero_count
        );
        for (node, &row_sum) in lattice.nodes.iter().zip(&row_sums) {
            assert_eq!(row_sum, i64::from(node == &bottom));
        }

        let norms: Vec<usize> = lattice
            .matrix
            .iter()
            .map(|row| {
                row.iter()
                    .map(|coefficient| coefficient.unsigned_abs() as usize)
                    .sum()
            })
            .collect();
        assert_eq!(
            norms.iter().copied().max().unwrap(),
            expected.max_absolute_row_norm
        );
        let norm_counts: BTreeMap<usize, usize> =
            norms.into_iter().fold(BTreeMap::new(), |mut counts, norm| {
                *counts.entry(norm).or_default() += 1;
                counts
            });
        assert_eq!(
            norm_counts,
            expected
                .row_norm_histogram
                .iter()
                .map(|entry| (entry.norm, entry.count))
                .collect()
        );
        let coefficient_counts: BTreeMap<i64, usize> =
            lattice.matrix.iter().flatten().copied().fold(
                BTreeMap::new(),
                |mut counts, coefficient| {
                    *counts.entry(coefficient).or_default() += 1;
                    counts
                },
            );
        assert_eq!(
            coefficient_counts,
            expected
                .coefficient_counts
                .iter()
                .map(|entry| (entry.coefficient, entry.count))
                .collect()
        );
    }
}

#[test]
fn every_realizable_table_matches_public_sxpid_and_every_bound_holds() {
    let fixture = fixture();
    let lattices = BTreeMap::from([(2, lattice(2)), (3, lattice(3)), (4, lattice(4))]);
    let mut table_count = 0;
    for pair in &fixture.law_pairs {
        let lattice = &lattices[&pair.source_count];
        compare_law(
            pair,
            "p",
            &pair.p_counts,
            &pair.p_probabilities,
            &pair.p_expected,
            lattice,
        );
        table_count += 1;
        compare_law(
            pair,
            "q",
            &pair.q_counts,
            &pair.q_probabilities,
            &pair.q_expected,
            lattice,
        );
        table_count += 1;
        check_pair_bounds(pair, lattice);
    }
    assert_eq!(
        table_count,
        fixture.tested_domain.public_count_tables_replayed
    );
}

#[test]
fn retained_exact_sharpness_falsifier_and_support_boundary_cases_replay() {
    let fixture = fixture();
    let lattices = BTreeMap::from([(2, lattice(2)), (3, lattice(3)), (4, lattice(4))]);

    assert_eq!(fixture.fannes_falsifiers.len(), 2);
    for case in &fixture.fannes_falsifiers {
        let pair = pair_by_name(&fixture, &case.pair_name);
        assert_eq!(pair.category, "fannes_falsifier");
        let lattice = &lattices[&pair.source_count];
        let index = node_index(lattice, &case.node_masks);
        let p = probabilities(&pair.p_counts);
        let q = probabilities(&pair.q_counts);
        let p_law = oracle_law(pair, &pair.p_counts, lattice);
        let q_law = oracle_law(pair, &pair.q_counts, lattice);
        let eta = total_variation(&p, &q);
        assert_eq!(eta, Rational::parse(&case.eta));
        assert_eq!(case.branch_count, case.node_masks.len());
        let (common, left_residual, _right_residual, _) = residuals(&p, &q);
        let mut common_term = 0.0;
        for (realization_index, &weight) in common.iter().enumerate() {
            if weight == Rational::ZERO {
                continue;
            }
            let (p_source_mass, _, _) = event_masses(
                &pair.realizations,
                &p,
                pair.source_count,
                &case.node_masks,
                realization_index,
            );
            let (q_source_mass, _, _) = event_masses(
                &pair.realizations,
                &q,
                pair.source_count,
                &case.node_masks,
                realization_index,
            );
            common_term += weight.to_f64() * (p_source_mass.to_f64() / q_source_mass.to_f64()).ln();
        }
        let gamma = gamma_union(case.branch_count, eta);
        let residual_entropy = subprobability_entropy(&left_residual);
        let difference =
            (p_law.cumulatives[index].informative - q_law.cumulatives[index].informative).abs();
        let fannes_value = fannes(case.alphabet_size, eta);
        let excess = difference - fannes_value;
        assert!(difference > fannes_value);
        assert!(case.exact_inequality_lhs > case.exact_inequality_rhs);
        match pair.name.as_str() {
            "fannes_three_source_five_cell" => {
                assert_eq!(case.exact_inequality, "6^9 > 4*5^9");
                assert_eq!(case.exact_inequality_lhs, 6u128.pow(9));
                assert_eq!(case.exact_inequality_rhs, 4 * 5u128.pow(9));
                assert!(case.gamma_sharp);
                assert_close(
                    "five-cell common term attains gamma_3",
                    common_term.abs(),
                    gamma,
                    pair.source_count,
                );
                assert_close(
                    "five-cell total is residual entropy plus gamma_3",
                    difference,
                    residual_entropy + gamma,
                    pair.source_count,
                );
            }
            "fannes_four_source_six_pair_star" => {
                assert_eq!(case.exact_inequality, "11^11 > 9*2^34");
                assert_eq!(case.exact_inequality_lhs, 11u128.pow(11));
                assert_eq!(case.exact_inequality_rhs, 9 * 2u128.pow(34));
                assert!(!case.gamma_sharp);
                assert!(common_term.abs() < gamma);
            }
            name => panic!("unknown Fannes falsifier {name}"),
        }
        assert_close(
            &format!("{} Fannes difference reference", pair.name),
            difference,
            parse_decimal(&case.difference_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} Fannes reference", pair.name),
            fannes_value,
            parse_decimal(&case.fannes_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} Fannes strict excess", pair.name),
            excess,
            parse_decimal(&case.strict_excess_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} common-term reference", pair.name),
            common_term.abs(),
            parse_decimal(&case.common_term_absolute_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} gamma reference", pair.name),
            gamma,
            parse_decimal(&case.gamma_j_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} residual-entropy reference", pair.name),
            residual_entropy,
            parse_decimal(&case.residual_entropy_nats),
            pair.source_count,
        );
        assert_close(
            &format!("{} constant-target minus change", pair.name),
            (p_law.cumulatives[index].misinformative - q_law.cumulatives[index].misinformative)
                .abs(),
            difference,
            pair.source_count,
        );
        assert_close(
            &format!("{} constant-target net", pair.name),
            p_law.cumulatives[index].net - q_law.cumulatives[index].net,
            0.0,
            pair.source_count,
        );
    }

    assert_eq!(fixture.sharp_gamma_cases.len(), 4);
    for case in &fixture.sharp_gamma_cases {
        let pair = pair_by_name(&fixture, &case.pair_name);
        assert_eq!(pair.category, "sharp_gamma");
        assert_eq!(case.branch_count, case.node_masks.len());
        let lattice = &lattices[&pair.source_count];
        let index = node_index(lattice, &case.node_masks);
        let p = probabilities(&pair.p_counts);
        let q = probabilities(&pair.q_counts);
        let (common, left_residual, _right_residual, eta) = residuals(&p, &q);
        assert_eq!(eta, Rational::parse(&case.eta));
        let mut common_term = 0.0;
        for (realization_index, &weight) in common.iter().enumerate() {
            if weight == Rational::ZERO {
                continue;
            }
            let (p_source_mass, _, _) = event_masses(
                &pair.realizations,
                &p,
                pair.source_count,
                &case.node_masks,
                realization_index,
            );
            let (q_source_mass, _, _) = event_masses(
                &pair.realizations,
                &q,
                pair.source_count,
                &case.node_masks,
                realization_index,
            );
            common_term += weight.to_f64() * (p_source_mass.to_f64() / q_source_mass.to_f64()).ln();
        }
        let gamma = gamma_union(case.branch_count, eta);
        let residual_entropy = subprobability_entropy(&left_residual);
        let p_law = oracle_law(pair, &pair.p_counts, lattice);
        let q_law = oracle_law(pair, &pair.q_counts, lattice);
        let total_difference =
            (p_law.cumulatives[index].informative - q_law.cumulatives[index].informative).abs();
        assert_close(
            &format!("{} sharp common term", pair.name),
            common_term.abs(),
            gamma,
            pair.source_count,
        );
        assert_close(
            &format!("{} sharp total identity", pair.name),
            total_difference,
            residual_entropy + gamma,
            pair.source_count,
        );
        for (label, actual, reference) in [
            (
                "common term",
                common_term.abs(),
                parse_decimal(&case.common_term_absolute_nats),
            ),
            ("gamma", gamma, parse_decimal(&case.gamma_j_nats)),
            (
                "residual entropy",
                residual_entropy,
                parse_decimal(&case.residual_entropy_nats),
            ),
            (
                "total difference",
                total_difference,
                parse_decimal(&case.total_difference_nats),
            ),
        ] {
            assert_close(
                &format!("{} {label} reference", pair.name),
                actual,
                reference,
                pair.source_count,
            );
        }
    }

    assert_eq!(fixture.rare_support_cases.len(), 5);
    let mut previous_ratio = 0.0;
    for case in &fixture.rare_support_cases {
        let pair = pair_by_name(&fixture, &case.pair_name);
        assert_eq!(pair.category, "rare_support");
        assert_eq!(case.node_masks, [1]);
        assert_eq!(case.rare_realization, [1, 0, 1]);
        let epsilon = Rational::new(1, 1u128 << case.exponent);
        assert_eq!(epsilon, Rational::parse(&case.epsilon));
        assert_eq!(epsilon.multiply_by(2), Rational::parse(&case.l1_distance));
        let entropy = binary_entropy(epsilon);
        let ratio = entropy / (2.0 * epsilon.to_f64());
        assert!(ratio > previous_ratio);
        previous_ratio = ratio;

        let p_result = evaluate_public(pair, &pair.p_counts);
        let q_result = evaluate_public(pair, &pair.q_counts);
        let p_index = p_result
            .antichains
            .iter()
            .position(|node| node == &case.node_masks)
            .unwrap();
        let q_index = q_result
            .antichains
            .iter()
            .position(|node| node == &case.node_masks)
            .unwrap();
        assert_close(
            &format!("{} baseline unique-S1", pair.name),
            p_result.atoms[p_index].net_nats(),
            0.0,
            pair.source_count,
        );
        assert_close(
            &format!("{} averaged unique-S1 h2", pair.name),
            q_result.atoms[q_index].net_nats(),
            entropy,
            pair.source_count,
        );
        let rare = public_pointwise_atom(
            pair,
            &pair.q_counts,
            &case.rare_realization,
            &case.node_masks,
        );
        let pointwise_magnitude = -epsilon.to_f64().ln();
        assert_close(
            &format!("{} rare informative", pair.name),
            rare.informative_nats(),
            pointwise_magnitude,
            pair.source_count,
        );
        assert_close(
            &format!("{} rare misinformative", pair.name),
            rare.misinformative_nats(),
            0.0,
            pair.source_count,
        );
        assert_close(
            &format!("{} rare net", pair.name),
            rare.net_nats(),
            pointwise_magnitude,
            pair.source_count,
        );
        for (label, actual, reference) in [
            (
                "averaged unique-S1",
                entropy,
                parse_decimal(&case.averaged_unique_s1_nats),
            ),
            ("ratio", ratio, parse_decimal(&case.unique_to_l1_ratio)),
            (
                "rare informative",
                rare.informative_nats(),
                parse_decimal(&case.rare_pointwise_informative_nats),
            ),
            (
                "rare misinformative",
                rare.misinformative_nats(),
                parse_decimal(&case.rare_pointwise_misinformative_nats),
            ),
            (
                "rare net",
                rare.net_nats(),
                parse_decimal(&case.rare_pointwise_net_nats),
            ),
        ] {
            assert_close(
                &format!("{} {label} reference", pair.name),
                actual,
                reference,
                pair.source_count,
            );
        }
    }

    let case = &fixture.net_residual_shortcut;
    let pair = pair_by_name(&fixture, &case.pair_name);
    assert_eq!(pair.category, "net_residual_shortcut");
    assert_eq!(case.node_masks, [1]);
    assert_eq!(case.eta, "1/10");
    assert_eq!(case.exact_inequality, "(1-eta)^2 > 0");
    assert_eq!(case.left_pointwise_net_closed_form, "ln(10)");
    assert_eq!(case.right_pointwise_net_closed_form, "ln(40/121)");
    assert_eq!(case.residual_difference_closed_form, "(1/5) ln(11/2)");
    assert_eq!(case.whole_common_term_closed_form, "(9/10) ln(11/9)");
    assert_eq!(
        case.whole_unique_net_difference_closed_form,
        "(1/5) ln(11/2) + (9/10) ln(11/9)"
    );
    let p = probabilities(&pair.p_counts);
    let q = probabilities(&pair.q_counts);
    let (_common, left_residual, right_residual, eta) = residuals(&p, &q);
    assert_eq!(eta, Rational::new(1, 10));
    let left = public_pointwise_atom(
        pair,
        &pair.p_counts,
        &case.left_residual_realization,
        &case.node_masks,
    )
    .net_nats();
    let right = public_pointwise_atom(
        pair,
        &pair.q_counts,
        &case.right_residual_realization,
        &case.node_masks,
    )
    .net_nats();
    assert_close("left residual local net", left, 10.0f64.ln(), 2);
    assert_close("right residual local net", right, (40.0f64 / 121.0).ln(), 2);
    let residual_difference = eta.to_f64() * (left - right);
    let entropy_left = subprobability_entropy(&left_residual);
    let entropy_right = subprobability_entropy(&right_residual);
    let entropy_max = entropy_left.max(entropy_right);
    assert_close(
        "residual closed form",
        residual_difference,
        0.2 * (11.0f64 / 2.0).ln(),
        2,
    );
    assert!(
        residual_difference > entropy_max,
        "the realizable signed residual terms must falsify the max-entropy shortcut"
    );
    let p_public = evaluate_public(pair, &pair.p_counts);
    let q_public = evaluate_public(pair, &pair.q_counts);
    let p_unique_s1 = p_public
        .atom(&case.node_masks)
        .expect("p result must contain the unique-S1 node")
        .net_nats();
    let q_unique_s1 = q_public
        .atom(&case.node_masks)
        .expect("q result must contain the unique-S1 node")
        .net_nats();
    let whole_unique_net_difference = (p_unique_s1 - q_unique_s1).abs();
    let whole_common_term = 0.9 * (11.0f64 / 9.0).ln();
    assert_close(
        "whole unique-S1 net closed form",
        whole_unique_net_difference,
        residual_difference + whole_common_term,
        2,
    );
    for (label, actual, reference) in [
        (
            "left residual reference",
            left,
            parse_decimal(&case.left_pointwise_net_nats),
        ),
        (
            "right residual reference",
            right,
            parse_decimal(&case.right_pointwise_net_nats),
        ),
        (
            "max residual entropy reference",
            entropy_max,
            parse_decimal(&case.max_residual_entropy_nats),
        ),
        (
            "residual difference reference",
            residual_difference,
            parse_decimal(&case.residual_difference_nats),
        ),
        (
            "strict excess reference",
            residual_difference - entropy_max,
            parse_decimal(&case.strict_excess_nats),
        ),
        (
            "whole common term reference",
            whole_common_term,
            parse_decimal(&case.whole_common_term_nats),
        ),
        (
            "whole unique-S1 net reference",
            whole_unique_net_difference,
            parse_decimal(&case.whole_unique_net_difference_nats),
        ),
    ] {
        assert_close(label, actual, reference, pair.source_count);
    }
}

fn total_variation(left: &[Rational], right: &[Rational]) -> Rational {
    left.iter()
        .zip(right)
        .map(|(&x, &y)| x.absolute_difference(y))
        .fold(Rational::ZERO, Rational::add)
        .divide_by(2)
}
