//! Bounded executable challenges for dependency-colored categorical SxPID analysis.
//!
//! The fixture generator uses exact Fraction arithmetic, 100-digit Decimal logarithms, and direct
//! finite enumeration. These tests bind the fixed-window population table to the Rust categorical
//! SxPID path. They do not prove the probability theorem, external validity, or binary64
//! asymptotics.

use std::collections::BTreeMap;

use pid_core::stable::categorical::{
    discrete_sxpid2, SxAveragedAtom, SxPointwise2, SxPointwiseAtom,
};
use pid_core::DiscreteMatRef;
use serde::Deserialize;

const FIXTURE_BYTES: &[u8] = include_bytes!("fixtures/dependency_colored_sxpid_oracle.json");
const FIXTURE_CHECKSUM: &str = include_str!("fixtures/dependency_colored_sxpid_oracle.json.sha256");
const GENERATOR_BYTES: &[u8] =
    include_bytes!("../../../scripts/generate-dependency-colored-sxpid-oracle.py");
// These are bounded fixture tolerances, not a general floating-point error theorem.
const FIXTURE_EPSILON_MULTIPLIER: f64 = 32.0;
const MAX_OUTPUT_ABSOLUTE_ERROR_NATS: f64 = FIXTURE_EPSILON_MULTIPLIER * f64::EPSILON;

#[derive(Deserialize)]
struct Fixture {
    arithmetic: Arithmetic,
    challenge_cases: ChallengeCases,
    generator: Generator,
    local_sxpid2_modulus_cases: Vec<LocalSxPid2ModulusCase>,
    method_provenance: MethodProvenance,
    schema: String,
    schema_revision: usize,
    scope_boundary: String,
    window_case: WindowCase,
}

#[derive(Deserialize)]
struct ChallengeCases {
    net_weight_half_factor: NetWeightHalfFactorCounterexample,
}

#[derive(Deserialize)]
struct NetWeightHalfFactorCounterexample {
    sxpid_specific_status: String,
}

#[derive(Deserialize)]
struct Arithmetic {
    decimal_precision_digits: usize,
    fraction_arithmetic: String,
    third_party_dependencies: Vec<String>,
}

#[derive(Deserialize)]
struct Generator {
    path: String,
    sha256: String,
    standard_library_only: bool,
}

#[derive(Deserialize)]
struct MethodProvenance {
    definition_origin: String,
    paper_defined_target: String,
    scientific_novelty_claim: String,
}

#[derive(Deserialize)]
struct WindowCase {
    adjacent_rows_factor: bool,
    color_classes: Vec<Vec<usize>>,
    color_classes_factor_jointly: bool,
    innovation_count_per_stream: usize,
    lag_two_rows_factor: bool,
    maximum_adjacent_factorization_error: String,
    population_count_table: Vec<CountedState>,
    row_count: usize,
    sxpid2: ExpectedSxPid2,
    window_width: usize,
}

#[derive(Deserialize)]
struct CountedState {
    count: usize,
    sources: Vec<usize>,
    target: usize,
}

#[derive(Deserialize)]
struct ExpectedSxPid2 {
    averaged_atoms: Vec<ExpectedAtom>,
    pointwise: Vec<ExpectedPointwise>,
}

#[derive(Deserialize)]
struct ExpectedAtom {
    informative_nats: String,
    misinformative_nats: String,
    net_nats: String,
    node_masks: Vec<u8>,
}

#[derive(Deserialize)]
struct ExpectedPointwise {
    atoms: Vec<ExpectedAtom>,
    count: usize,
    sources: Vec<usize>,
    target: usize,
}

#[derive(Deserialize)]
struct LocalSxPid2ModulusCase {
    bounds_by_node: Vec<NodeBounds>,
    delta_l1: String,
    eta_total_variation: String,
    h_nats: String,
    diamond_ceiling_nats: String,
    lambda_nats: String,
    log_support_floor_nats: String,
    name: String,
    p_min: String,
    p_population_count_table: Vec<CountedState>,
    p_sxpid2: ExpectedSxPid2,
    q_population_count_table: Vec<CountedState>,
    q_sxpid2: ExpectedSxPid2,
}

#[derive(Deserialize)]
struct NodeBounds {
    atom_family: String,
    averaged_bounds_nats: ComponentBounds,
    node_masks: Vec<u8>,
    pointwise_bounds_nats: ComponentBounds,
}

#[derive(Deserialize)]
struct ComponentBounds {
    informative: String,
    misinformative: String,
    net: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct ExactFraction {
    numerator: u128,
    denominator: u128,
}

impl ExactFraction {
    fn parse(value: &str) -> Self {
        let (numerator, denominator) = value
            .split_once('/')
            .unwrap_or_else(|| panic!("fixture fraction {value:?} must contain one slash"));
        assert!(
            !denominator.contains('/'),
            "fixture fraction {value:?} must contain one slash"
        );
        let numerator = numerator
            .parse::<u128>()
            .unwrap_or_else(|error| panic!("invalid fixture numerator in {value:?}: {error}"));
        let denominator = denominator
            .parse::<u128>()
            .unwrap_or_else(|error| panic!("invalid fixture denominator in {value:?}: {error}"));
        Self::new(numerator, denominator)
    }

    fn new(numerator: u128, denominator: u128) -> Self {
        assert!(
            denominator > 0,
            "fixture fraction denominator must be positive"
        );
        let divisor = greatest_common_divisor(numerator, denominator);
        Self {
            numerator: numerator / divisor,
            denominator: denominator / divisor,
        }
    }

    const fn from_integer(value: u128) -> Self {
        Self {
            numerator: value,
            denominator: 1,
        }
    }

    fn checked_add(self, other: Self) -> Self {
        let left = self
            .numerator
            .checked_mul(other.denominator)
            .expect("fixture fraction addition overflowed on the left");
        let right = other
            .numerator
            .checked_mul(self.denominator)
            .expect("fixture fraction addition overflowed on the right");
        let numerator = left
            .checked_add(right)
            .expect("fixture fraction addition numerator overflowed");
        let denominator = self
            .denominator
            .checked_mul(other.denominator)
            .expect("fixture fraction addition denominator overflowed");
        Self::new(numerator, denominator)
    }

    fn checked_sub(self, other: Self) -> Self {
        let left = self
            .numerator
            .checked_mul(other.denominator)
            .expect("fixture fraction subtraction overflowed on the left");
        let right = other
            .numerator
            .checked_mul(self.denominator)
            .expect("fixture fraction subtraction overflowed on the right");
        assert!(
            left >= right,
            "fixture fraction subtraction requires a non-negative result"
        );
        let denominator = self
            .denominator
            .checked_mul(other.denominator)
            .expect("fixture fraction subtraction denominator overflowed");
        Self::new(left - right, denominator)
    }

    fn absolute_difference(self, other: Self) -> Self {
        let left = self
            .numerator
            .checked_mul(other.denominator)
            .expect("fixture fraction difference overflowed on the left");
        let right = other
            .numerator
            .checked_mul(self.denominator)
            .expect("fixture fraction difference overflowed on the right");
        let denominator = self
            .denominator
            .checked_mul(other.denominator)
            .expect("fixture fraction difference denominator overflowed");
        Self::new(left.abs_diff(right), denominator)
    }

    fn checked_div(self, other: Self) -> Self {
        assert!(
            other.numerator > 0,
            "fixture fraction division requires a positive divisor"
        );
        let numerator = self
            .numerator
            .checked_mul(other.denominator)
            .expect("fixture fraction division numerator overflowed");
        let denominator = self
            .denominator
            .checked_mul(other.numerator)
            .expect("fixture fraction division denominator overflowed");
        Self::new(numerator, denominator)
    }

    fn reciprocal(self) -> Self {
        assert!(
            self.numerator > 0,
            "fixture fraction reciprocal requires a positive value"
        );
        Self::new(self.denominator, self.numerator)
    }

    fn is_strictly_less_than(self, other: Self) -> bool {
        let left = self
            .numerator
            .checked_mul(other.denominator)
            .expect("fixture fraction comparison overflowed");
        let right = other
            .numerator
            .checked_mul(self.denominator)
            .expect("fixture fraction comparison overflowed");
        left < right
    }

    fn to_f64(self) -> f64 {
        const LARGEST_EXACT_F64_INTEGER: u128 = 1_u128 << f64::MANTISSA_DIGITS;
        assert!(
            self.numerator <= LARGEST_EXACT_F64_INTEGER,
            "fixture numerator exceeds exact f64 integer range"
        );
        assert!(
            self.denominator <= LARGEST_EXACT_F64_INTEGER,
            "fixture denominator exceeds exact f64 integer range"
        );
        self.numerator as f64 / self.denominator as f64
    }
}

#[derive(Clone, Copy)]
struct NumericComponentBounds {
    informative: f64,
    misinformative: f64,
    net: f64,
}

#[derive(Clone, Copy)]
struct DerivedModulus {
    delta_l1: f64,
    eta_total_variation: f64,
    h_nats: f64,
    diamond_ceiling_nats: f64,
    lambda_nats: f64,
    log_support_floor_nats: f64,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum AtomFamily {
    RedundancyOrUnique,
    Synergy,
}

impl AtomFamily {
    const fn fixture_name(self) -> &'static str {
        match self {
            Self::RedundancyOrUnique => "redundancy-or-unique",
            Self::Synergy => "synergy",
        }
    }
}

struct ExpandedTable {
    s1: Vec<usize>,
    s2: Vec<usize>,
    target: Vec<usize>,
}

impl ExpandedTable {
    fn refs(&self) -> (DiscreteMatRef<'_>, DiscreteMatRef<'_>, DiscreteMatRef<'_>) {
        let rows = self.target.len();
        (
            DiscreteMatRef::new(&self.s1, rows, 1).unwrap(),
            DiscreteMatRef::new(&self.s2, rows, 1).unwrap(),
            DiscreteMatRef::new(&self.target, rows, 1).unwrap(),
        )
    }
}

fn fixture() -> Fixture {
    let expected_hash = FIXTURE_CHECKSUM
        .split_whitespace()
        .next()
        .expect("fixture checksum must contain a SHA-256 digest");
    assert_eq!(
        pid_runlog::sha256_hex(FIXTURE_BYTES),
        expected_hash,
        "dependency-colored fixture does not match its committed SHA-256 digest"
    );
    serde_json::from_slice(FIXTURE_BYTES)
        .expect("dependency-colored fixture must contain valid JSON")
}

fn expand(states: &[CountedState]) -> ExpandedTable {
    let rows = states.iter().map(|state| state.count).sum();
    let mut s1 = Vec::with_capacity(rows);
    let mut s2 = Vec::with_capacity(rows);
    let mut target = Vec::with_capacity(rows);
    for state in states {
        assert_eq!(state.sources.len(), 2);
        assert!(state.count > 0);
        for _ in 0..state.count {
            s1.push(state.sources[0]);
            s2.push(state.sources[1]);
            target.push(state.target);
        }
    }
    ExpandedTable { s1, s2, target }
}

fn decimal(value: &str) -> f64 {
    let parsed = value
        .parse::<f64>()
        .expect("oracle Decimal must be representable as f64");
    assert!(parsed.is_finite());
    parsed
}

fn greatest_common_divisor(mut left: u128, mut right: u128) -> u128 {
    while right != 0 {
        (left, right) = (right, left % right);
    }
    left
}

fn normalized_law(states: &[CountedState]) -> BTreeMap<(Vec<usize>, usize), ExactFraction> {
    let mut total = 0_u128;
    let mut counts = BTreeMap::new();
    for state in states {
        assert_eq!(state.sources.len(), 2);
        assert!(state.count > 0);
        let count = u128::try_from(state.count).expect("fixture count must fit in u128");
        total = total
            .checked_add(count)
            .expect("fixture total count overflowed");
        let stored = counts
            .entry((state.sources.clone(), state.target))
            .or_insert(0_u128);
        *stored = stored
            .checked_add(count)
            .expect("fixture state count overflowed");
    }
    assert!(total > 0, "fixture law must contain positive mass");
    counts
        .into_iter()
        .map(|(key, count)| (key, ExactFraction::new(count, total)))
        .collect()
}

fn derive_law_parameters(case: &LocalSxPid2ModulusCase) -> (ExactFraction, ExactFraction) {
    let p_law = normalized_law(&case.p_population_count_table);
    let q_law = normalized_law(&case.q_population_count_table);
    assert_eq!(
        p_law.keys().collect::<Vec<_>>(),
        q_law.keys().collect::<Vec<_>>(),
        "{} must have common support",
        case.name
    );
    let mut delta_l1 = ExactFraction::from_integer(0);
    let mut p_min = None;
    for (key, p_probability) in &p_law {
        let q_probability = q_law
            .get(key)
            .unwrap_or_else(|| panic!("{} q-law omitted state {key:?}", case.name));
        delta_l1 = delta_l1.checked_add(p_probability.absolute_difference(*q_probability));
        if p_min.is_none_or(|minimum| p_probability.is_strictly_less_than(minimum)) {
            p_min = Some(*p_probability);
        }
    }
    (
        delta_l1,
        p_min.expect("fixture p-law must contain one positive state"),
    )
}

fn derive_modulus(case: &LocalSxPid2ModulusCase) -> DerivedModulus {
    let stored_delta_l1 = ExactFraction::parse(&case.delta_l1);
    let stored_eta_total_variation = ExactFraction::parse(&case.eta_total_variation);
    let stored_p_min = ExactFraction::parse(&case.p_min);
    let (delta_l1, p_min) = derive_law_parameters(case);
    assert_eq!(
        delta_l1, stored_delta_l1,
        "{} stored delta_l1 does not match its count tables",
        case.name
    );
    assert_eq!(
        p_min, stored_p_min,
        "{} stored p_min does not match its p-law count table",
        case.name
    );
    assert!(
        p_min.numerator > 0,
        "{} must have a positive p_min",
        case.name
    );
    let eta_total_variation = delta_l1.checked_div(ExactFraction::from_integer(2));
    assert!(
        eta_total_variation.is_strictly_less_than(p_min),
        "{} must satisfy eta < p_min",
        case.name
    );
    assert_eq!(
        eta_total_variation, stored_eta_total_variation,
        "{} stored eta does not match delta_l1 / 2",
        case.name
    );
    let p_min_f64 = p_min.to_f64();
    let eta_f64 = eta_total_variation.to_f64();
    let lambda_nats = p_min
        .checked_div(p_min.checked_sub(eta_total_variation))
        .to_f64()
        .ln();
    let log_support_floor_nats = p_min.reciprocal().to_f64().ln();
    let h_nats = (2.0 / (1.0 + p_min_f64)).ln();
    let diamond_ceiling_nats = log_support_floor_nats - 2.0 * h_nats;
    assert!(lambda_nats.is_finite());
    assert!(log_support_floor_nats.is_finite());
    assert!(h_nats.is_finite());
    assert!(diamond_ceiling_nats.is_finite());
    assert!(
        diamond_ceiling_nats >= -MAX_OUTPUT_ABSOLUTE_ERROR_NATS
            && diamond_ceiling_nats <= log_support_floor_nats + MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
        "{} must have its diamond ceiling in [0, L]",
        case.name
    );
    DerivedModulus {
        delta_l1: delta_l1.to_f64(),
        eta_total_variation: eta_f64,
        h_nats,
        diamond_ceiling_nats,
        lambda_nats,
        log_support_floor_nats,
    }
}

fn derive_component_bounds(
    modulus: DerivedModulus,
    family: AtomFamily,
) -> (NumericComponentBounds, NumericComponentBounds) {
    let component_weight_range = match family {
        AtomFamily::RedundancyOrUnique => modulus.log_support_floor_nats,
        AtomFamily::Synergy => modulus.diamond_ceiling_nats,
    };
    let net_weight_range = match family {
        AtomFamily::RedundancyOrUnique => modulus.log_support_floor_nats - modulus.h_nats,
        AtomFamily::Synergy => modulus.diamond_ceiling_nats,
    };
    let averaged_component_bound = modulus
        .log_support_floor_nats
        .min(modulus.lambda_nats + modulus.eta_total_variation * component_weight_range);
    let averaged_net_bound = (2.0 * modulus.log_support_floor_nats)
        .min(modulus.lambda_nats + modulus.delta_l1 * net_weight_range);
    assert!(
        averaged_component_bound <= modulus.log_support_floor_nats,
        "averaged component bound must respect its range cap"
    );
    assert!(
        averaged_net_bound <= 2.0 * modulus.log_support_floor_nats,
        "averaged net bound must respect its range cap"
    );
    (
        NumericComponentBounds {
            informative: modulus.lambda_nats,
            misinformative: modulus.lambda_nats,
            net: modulus.lambda_nats,
        },
        NumericComponentBounds {
            informative: averaged_component_bound,
            misinformative: averaged_component_bound,
            net: averaged_net_bound,
        },
    )
}

fn atom_family(node_masks: &[u8]) -> AtomFamily {
    match node_masks {
        [0b01] | [0b10] | [0b01, 0b10] => AtomFamily::RedundancyOrUnique,
        [0b11] => AtomFamily::Synergy,
        other => panic!("unknown two-source lattice node {other:?}"),
    }
}

fn assert_decimal_matches(recomputed: f64, stored: &str, context: &str) {
    let stored = decimal(stored);
    let error = (recomputed - stored).abs();
    let scale = recomputed.abs().max(stored.abs()).max(1.0);
    let tolerance = FIXTURE_EPSILON_MULTIPLIER * f64::EPSILON * scale;
    assert!(
        error <= tolerance,
        "{context} recomputed value {recomputed:.17e} differs from stored value {stored:.17e} by \
         {error:.17e}, above the scale-aware tolerance {tolerance:.17e}"
    );
}

fn assert_bound_strings_match(
    recomputed: NumericComponentBounds,
    stored: &ComponentBounds,
    context: &str,
) {
    assert_decimal_matches(
        recomputed.informative,
        &stored.informative,
        &format!("{context} informative bound"),
    );
    assert_decimal_matches(
        recomputed.misinformative,
        &stored.misinformative,
        &format!("{context} misinformative bound"),
    );
    assert_decimal_matches(recomputed.net, &stored.net, &format!("{context} net bound"));
}

fn expected_by_node(atoms: &[ExpectedAtom]) -> BTreeMap<Vec<u8>, &ExpectedAtom> {
    atoms
        .iter()
        .map(|atom| (atom.node_masks.clone(), atom))
        .collect()
}

fn averaged_by_node(
    result: &pid_core::stable::categorical::DiscreteSxPid2Result,
) -> BTreeMap<Vec<u8>, SxAveragedAtom> {
    BTreeMap::from([
        (vec![0b01], result.unq1),
        (vec![0b10], result.unq2),
        (vec![0b11], result.syn),
        (vec![0b01, 0b10], result.red),
    ])
}

fn pointwise_by_node(point: &SxPointwise2) -> BTreeMap<Vec<u8>, SxPointwiseAtom> {
    BTreeMap::from([
        (vec![0b01], point.unq1),
        (vec![0b10], point.unq2),
        (vec![0b11], point.syn),
        (vec![0b01, 0b10], point.red),
    ])
}

fn averaged_components(atom: SxAveragedAtom) -> [f64; 3] {
    [
        atom.informative_nats(),
        atom.misinformative_nats(),
        atom.net_nats(),
    ]
}

fn pointwise_components(atom: SxPointwiseAtom) -> [f64; 3] {
    [
        atom.informative_nats(),
        atom.misinformative_nats(),
        atom.net_nats(),
    ]
}

fn assert_components_bit_identical(left: [f64; 3], right: [f64; 3], context: &str) {
    for (component, left, right) in [
        ("informative", left[0], right[0]),
        ("misinformative", left[1], right[1]),
        ("net", left[2], right[2]),
    ] {
        assert_eq!(
            left.to_bits(),
            right.to_bits(),
            "{context} {component} component changed bits after row reversal"
        );
    }
}

fn assert_results_bit_identical_after_row_reversal(
    forward: &pid_core::stable::categorical::DiscreteSxPid2Result,
    backward: &pid_core::stable::categorical::DiscreteSxPid2Result,
    context: &str,
) {
    let forward_averaged = averaged_by_node(forward);
    let backward_averaged = averaged_by_node(backward);
    assert_eq!(
        forward_averaged.keys().collect::<Vec<_>>(),
        backward_averaged.keys().collect::<Vec<_>>(),
        "{context} averaged lattice nodes changed after row reversal"
    );
    for (node, forward_atom) in forward_averaged {
        let backward_atom = backward_averaged
            .get(&node)
            .unwrap_or_else(|| panic!("{context} omitted averaged node {node:?} after reversal"));
        assert_components_bit_identical(
            averaged_components(forward_atom),
            averaged_components(*backward_atom),
            &format!("{context} averaged node {node:?}"),
        );
    }

    let forward_points = pointwise_results(forward);
    let backward_points = pointwise_results(backward);
    assert_eq!(
        forward_points.keys().collect::<Vec<_>>(),
        backward_points.keys().collect::<Vec<_>>(),
        "{context} pointwise realizations changed after row reversal"
    );
    for (key, forward_point) in forward_points {
        let backward_point = backward_points
            .get(&key)
            .unwrap_or_else(|| panic!("{context} omitted realization {key:?} after reversal"));
        assert_eq!(
            forward_point.empirical_count, backward_point.empirical_count,
            "{context} realization {key:?} changed count after row reversal"
        );
        let forward_atoms = pointwise_by_node(forward_point);
        let backward_atoms = pointwise_by_node(backward_point);
        assert_eq!(
            forward_atoms.keys().collect::<Vec<_>>(),
            backward_atoms.keys().collect::<Vec<_>>(),
            "{context} realization {key:?} changed lattice nodes after row reversal"
        );
        for (node, forward_atom) in forward_atoms {
            let backward_atom = backward_atoms.get(&node).unwrap_or_else(|| {
                panic!(
                    "{context} realization {key:?} omitted pointwise node {node:?} after reversal"
                )
            });
            assert_components_bit_identical(
                pointwise_components(forward_atom),
                pointwise_components(*backward_atom),
                &format!("{context} realization {key:?} pointwise node {node:?}"),
            );
        }
    }
}

fn reversed(table: &ExpandedTable) -> ExpandedTable {
    ExpandedTable {
        s1: table.s1.iter().copied().rev().collect(),
        s2: table.s2.iter().copied().rev().collect(),
        target: table.target.iter().copied().rev().collect(),
    }
}

fn assert_table_is_bit_identical_after_row_reversal(table: &ExpandedTable, context: &str) {
    let (s1, s2, target) = table.refs();
    let forward = discrete_sxpid2(s1, s2, target).unwrap();
    let backward_table = reversed(table);
    let (s1, s2, target) = backward_table.refs();
    let backward = discrete_sxpid2(s1, s2, target).unwrap();
    assert_results_bit_identical_after_row_reversal(&forward, &backward, context);
}

fn record_error(maximum: &mut f64, actual: f64, expected: f64) {
    let error = (actual - expected).abs();
    assert!(error.is_finite());
    *maximum = maximum.max(error);
}

fn compare_atom(
    maximum: &mut f64,
    actual_informative: f64,
    actual_misinformative: f64,
    actual_net: f64,
    expected: &ExpectedAtom,
) {
    record_error(
        maximum,
        actual_informative,
        decimal(&expected.informative_nats),
    );
    record_error(
        maximum,
        actual_misinformative,
        decimal(&expected.misinformative_nats),
    );
    record_error(maximum, actual_net, decimal(&expected.net_nats));
}

fn pointwise_results(
    result: &pid_core::stable::categorical::DiscreteSxPid2Result,
) -> BTreeMap<(usize, usize, usize), &SxPointwise2> {
    result
        .pointwise
        .iter()
        .map(|point| ((point.s1[0], point.s2[0], point.t[0]), point))
        .collect()
}

fn compare_result_to_oracle(
    result: &pid_core::stable::categorical::DiscreteSxPid2Result,
    expected: &ExpectedSxPid2,
) -> f64 {
    let expected_averaged = expected_by_node(&expected.averaged_atoms);
    let actual_averaged = averaged_by_node(result);
    assert_eq!(expected_averaged.len(), 4);
    assert_eq!(actual_averaged.len(), 4);
    let mut maximum_error = 0.0;
    for (node, expected_atom) in expected_averaged {
        let actual = actual_averaged
            .get(&node)
            .unwrap_or_else(|| panic!("Rust result omitted node {node:?}"));
        compare_atom(
            &mut maximum_error,
            actual.informative_nats(),
            actual.misinformative_nats(),
            actual.net_nats(),
            expected_atom,
        );
    }

    let actual_points = pointwise_results(result);
    assert_eq!(actual_points.len(), expected.pointwise.len());
    for expected_point in &expected.pointwise {
        assert_eq!(expected_point.sources.len(), 2);
        let key = (
            expected_point.sources[0],
            expected_point.sources[1],
            expected_point.target,
        );
        let actual_point = actual_points
            .get(&key)
            .unwrap_or_else(|| panic!("Rust result omitted realization {key:?}"));
        assert_eq!(actual_point.empirical_count, expected_point.count);
        let expected_atoms = expected_by_node(&expected_point.atoms);
        let actual_atoms = pointwise_by_node(actual_point);
        assert_eq!(expected_atoms.len(), 4);
        assert_eq!(actual_atoms.len(), 4);
        for (node, expected_atom) in expected_atoms {
            let actual_atom = actual_atoms
                .get(&node)
                .unwrap_or_else(|| panic!("Rust point omitted node {node:?}"));
            compare_atom(
                &mut maximum_error,
                actual_atom.informative_nats(),
                actual_atom.misinformative_nats(),
                actual_atom.net_nats(),
                expected_atom,
            );
        }
    }
    maximum_error
}

fn assert_component_change_within_bounds(
    p_components: [f64; 3],
    q_components: [f64; 3],
    bounds: NumericComponentBounds,
    context: &str,
) {
    let [p_informative, p_misinformative, p_net] = p_components;
    let [q_informative, q_misinformative, q_net] = q_components;
    for (component, change, bound) in [
        (
            "informative",
            (q_informative - p_informative).abs(),
            bounds.informative,
        ),
        (
            "misinformative",
            (q_misinformative - p_misinformative).abs(),
            bounds.misinformative,
        ),
        ("net", (q_net - p_net).abs(), bounds.net),
    ] {
        assert!(
            change <= bound + MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
            "{context} {component} change {change:.17e} exceeded bound {bound:.17e} plus \
             {MAX_OUTPUT_ABSOLUTE_ERROR_NATS:.17e}"
        );
    }
}

#[test]
fn fixture_binds_fraction_and_decimal_challenges_and_provenance() {
    let fixture = fixture();
    assert_eq!(fixture.schema, "pid-rs/dependency-colored-sxpid-oracle");
    assert_eq!(fixture.schema_revision, 3);
    assert_eq!(fixture.arithmetic.decimal_precision_digits, 100);
    assert_eq!(fixture.arithmetic.fraction_arithmetic, "exact");
    assert!(fixture.arithmetic.third_party_dependencies.is_empty());
    assert!(fixture.generator.standard_library_only);
    assert_eq!(
        fixture.generator.path,
        "scripts/generate-dependency-colored-sxpid-oracle.py"
    );
    assert_eq!(
        fixture.generator.sha256,
        pid_runlog::sha256_hex(GENERATOR_BYTES),
        "dependency-colored generator identity is stale"
    );
    assert_eq!(
        fixture.method_provenance.definition_origin,
        "project-defined"
    );
    assert_eq!(
        fixture.method_provenance.paper_defined_target,
        "categorical shared-exclusions PID"
    );
    assert_eq!(fixture.method_provenance.scientific_novelty_claim, "none");
    assert_eq!(
        fixture
            .challenge_cases
            .net_weight_half_factor
            .sxpid_specific_status,
        "superseded for two-source SxPID-specific range conclusions"
    );
    assert_eq!(
        fixture.scope_boundary,
        "bounded fraction-exact and 100-digit Decimal challenges; not a general theorem, binary64 certificate, external review, or continuous-PID result"
    );
    assert_eq!(fixture.window_case.window_width, 2);
    assert_eq!(fixture.window_case.row_count, 6);
    assert_eq!(fixture.window_case.innovation_count_per_stream, 7);
    assert_eq!(
        ExactFraction::parse(&fixture.window_case.maximum_adjacent_factorization_error),
        ExactFraction::new(19, 256)
    );
    assert_eq!(
        fixture.window_case.color_classes,
        [vec![0, 2, 4], vec![1, 3, 5]]
    );
    assert!(fixture.window_case.color_classes_factor_jointly);
    assert!(fixture.window_case.lag_two_rows_factor);
    assert!(!fixture.window_case.adjacent_rows_factor);
}

#[test]
fn fixed_window_population_sxpid_matches_independent_decimal_oracle() {
    let fixture = fixture();
    let table = expand(&fixture.window_case.population_count_table);
    let (s1, s2, target) = table.refs();
    let result = discrete_sxpid2(s1, s2, target).unwrap();
    let maximum_error = compare_result_to_oracle(&result, &fixture.window_case.sxpid2);
    assert!(
        maximum_error <= MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
        "maximum fixed-window SxPID error {maximum_error:.17e} exceeded \
         {MAX_OUTPUT_ABSOLUTE_ERROR_NATS:.17e}"
    );
}

#[test]
fn local_sxpid2_modulus_cases_match_oracle_and_rederived_bounds() {
    let fixture = fixture();
    assert_eq!(fixture.local_sxpid2_modulus_cases.len(), 4);
    for case in fixture.local_sxpid2_modulus_cases {
        let modulus = derive_modulus(&case);
        assert_decimal_matches(
            modulus.lambda_nats,
            &case.lambda_nats,
            &format!("{} lambda", case.name),
        );
        assert_decimal_matches(
            modulus.log_support_floor_nats,
            &case.log_support_floor_nats,
            &format!("{} support-floor logarithm", case.name),
        );
        assert_decimal_matches(modulus.h_nats, &case.h_nats, &format!("{} h", case.name));
        assert_decimal_matches(
            modulus.diamond_ceiling_nats,
            &case.diamond_ceiling_nats,
            &format!("{} diamond ceiling", case.name),
        );
        let p_table = expand(&case.p_population_count_table);
        let (p_s1, p_s2, p_target) = p_table.refs();
        let p_result = discrete_sxpid2(p_s1, p_s2, p_target).unwrap();
        let q_table = expand(&case.q_population_count_table);
        let (q_s1, q_s2, q_target) = q_table.refs();
        let q_result = discrete_sxpid2(q_s1, q_s2, q_target).unwrap();

        let p_error = compare_result_to_oracle(&p_result, &case.p_sxpid2);
        let q_error = compare_result_to_oracle(&q_result, &case.q_sxpid2);
        assert!(
            p_error <= MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
            "{} p-law SxPID error {p_error:.17e} exceeded \
             {MAX_OUTPUT_ABSOLUTE_ERROR_NATS:.17e}",
            case.name
        );
        assert!(
            q_error <= MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
            "{} q-law SxPID error {q_error:.17e} exceeded \
             {MAX_OUTPUT_ABSOLUTE_ERROR_NATS:.17e}",
            case.name
        );

        let p_averaged = averaged_by_node(&p_result);
        let q_averaged = averaged_by_node(&q_result);
        let p_points = pointwise_results(&p_result);
        let q_points = pointwise_results(&q_result);
        assert_eq!(
            p_points.keys().collect::<Vec<_>>(),
            q_points.keys().collect::<Vec<_>>()
        );
        assert_eq!(case.bounds_by_node.len(), 4);
        let mut observed_nodes = BTreeMap::new();
        let mut maximum_synergy_pointwise_change = [0.0_f64; 3];
        for node_bounds in &case.bounds_by_node {
            assert!(
                observed_nodes
                    .insert(node_bounds.node_masks.clone(), ())
                    .is_none(),
                "{} repeats a stored lattice-node bound",
                case.name
            );
            let family = atom_family(&node_bounds.node_masks);
            assert_eq!(
                node_bounds.atom_family,
                family.fixture_name(),
                "{} has an incorrect atom family for node {:?}",
                case.name,
                node_bounds.node_masks
            );
            let (pointwise_bounds, averaged_bounds) = derive_component_bounds(modulus, family);
            let node_context = format!("{} node {:?}", case.name, node_bounds.node_masks);
            assert_bound_strings_match(
                pointwise_bounds,
                &node_bounds.pointwise_bounds_nats,
                &format!("{node_context} pointwise"),
            );
            assert_bound_strings_match(
                averaged_bounds,
                &node_bounds.averaged_bounds_nats,
                &format!("{node_context} averaged"),
            );

            let p_atom = p_averaged
                .get(&node_bounds.node_masks)
                .unwrap_or_else(|| panic!("{} p-law omitted an averaged node", case.name));
            let q_atom = q_averaged
                .get(&node_bounds.node_masks)
                .unwrap_or_else(|| panic!("{} q-law omitted an averaged node", case.name));
            assert_component_change_within_bounds(
                [
                    p_atom.informative_nats(),
                    p_atom.misinformative_nats(),
                    p_atom.net_nats(),
                ],
                [
                    q_atom.informative_nats(),
                    q_atom.misinformative_nats(),
                    q_atom.net_nats(),
                ],
                averaged_bounds,
                &format!("{node_context} averaged"),
            );
            for (key, p_point) in &p_points {
                let q_point = q_points
                    .get(key)
                    .unwrap_or_else(|| panic!("{} q-law omitted realization {key:?}", case.name));
                let p_atom = pointwise_by_node(p_point)
                    .remove(&node_bounds.node_masks)
                    .unwrap_or_else(|| panic!("{} p-law omitted a pointwise node", case.name));
                let q_atom = pointwise_by_node(q_point)
                    .remove(&node_bounds.node_masks)
                    .unwrap_or_else(|| panic!("{} q-law omitted a pointwise node", case.name));
                if family == AtomFamily::Synergy {
                    for (maximum, change) in maximum_synergy_pointwise_change.iter_mut().zip([
                        (q_atom.informative_nats() - p_atom.informative_nats()).abs(),
                        (q_atom.misinformative_nats() - p_atom.misinformative_nats()).abs(),
                        (q_atom.net_nats() - p_atom.net_nats()).abs(),
                    ]) {
                        *maximum = maximum.max(change);
                    }
                }
                assert_component_change_within_bounds(
                    [
                        p_atom.informative_nats(),
                        p_atom.misinformative_nats(),
                        p_atom.net_nats(),
                    ],
                    [
                        q_atom.informative_nats(),
                        q_atom.misinformative_nats(),
                        q_atom.net_nats(),
                    ],
                    pointwise_bounds,
                    &format!(
                        "{} realization {key:?} node {:?}",
                        case.name, node_bounds.node_masks
                    ),
                );
            }
        }
        assert_eq!(
            observed_nodes.keys().collect::<Vec<_>>(),
            p_averaged.keys().collect::<Vec<_>>(),
            "{} stored bounds do not cover exactly the four two-source lattice nodes",
            case.name
        );
        if case.name == "full-binary-realizable-near-tight" {
            let (delta_l1, p_min) = derive_law_parameters(&case);
            let eta = delta_l1.checked_div(ExactFraction::from_integer(2));
            assert_eq!(case.p_population_count_table.len(), 8);
            assert_eq!(case.q_population_count_table.len(), 8);
            assert_eq!(
                case.p_population_count_table
                    .iter()
                    .map(|state| state.count)
                    .collect::<Vec<_>>(),
                [10, 100, 200, 10, 250, 10, 10, 10]
            );
            assert_eq!(
                case.q_population_count_table
                    .iter()
                    .map(|state| state.count)
                    .collect::<Vec<_>>(),
                [1, 100, 200, 10, 250, 10, 10, 19]
            );
            assert_eq!(delta_l1, ExactFraction::new(3, 100));
            assert_eq!(eta, ExactFraction::new(3, 200));
            assert_eq!(p_min, ExactFraction::new(1, 60));
            assert_eq!(
                p_min.checked_div(p_min.checked_sub(eta)),
                ExactFraction::from_integer(10)
            );
            let misinformative_ratio = maximum_synergy_pointwise_change[1] / modulus.lambda_nats;
            let net_ratio = maximum_synergy_pointwise_change[2] / modulus.lambda_nats;
            assert!(
                misinformative_ratio > 0.97 && misinformative_ratio <= 1.0,
                "near-tight synergy misinformative ratio {misinformative_ratio:.17e} must lie in \
                 (0.97, 1]"
            );
            assert!(
                net_ratio > 0.95 && net_ratio <= 1.0,
                "near-tight synergy net ratio {net_ratio:.17e} must lie in (0.95, 1]"
            );
        }
    }
}

#[test]
fn fixed_window_estimate_is_bit_identical_after_row_reversal() {
    let fixture = fixture();
    let table = expand(&fixture.window_case.population_count_table);
    assert_table_is_bit_identical_after_row_reversal(&table, "fixed-window population law");
}

#[test]
fn local_modulus_laws_are_bit_identical_after_row_reversal() {
    let fixture = fixture();
    assert_eq!(fixture.local_sxpid2_modulus_cases.len(), 4);
    for case in &fixture.local_sxpid2_modulus_cases {
        for (law, states) in [
            ("p-law", case.p_population_count_table.as_slice()),
            ("q-law", case.q_population_count_table.as_slice()),
        ] {
            let table = expand(states);
            assert_table_is_bit_identical_after_row_reversal(
                &table,
                &format!("{} {law}", case.name),
            );
        }
    }
}
