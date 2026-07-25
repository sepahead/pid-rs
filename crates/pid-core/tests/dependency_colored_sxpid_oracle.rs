//! Bounded executable challenges for categorical SxPID analysis under a dependency coloring.
//!
//! The fixture generator uses exact Fraction arithmetic, 400-digit Decimal logarithms, and direct
//! finite enumeration. These tests bind the fixed-window population table to the Rust categorical
//! SxPID path. They do not prove the probability theorem, external validity, or binary64
//! asymptotics.

use std::collections::BTreeMap;
use std::io::ErrorKind;
use std::path::Path;

use pid_core::stable::categorical::{
    discrete_sxpid2, SxAveragedAtom, SxPointwise2, SxPointwiseAtom,
};
use pid_core::DiscreteMatRef;
use serde::Deserialize;

const FIXTURE_BYTES: &[u8] = include_bytes!("fixtures/dependency_colored_sxpid_oracle.json");
const FIXTURE_CHECKSUM: &str = include_str!("fixtures/dependency_colored_sxpid_oracle.json.sha256");
const GENERATOR_BYTES: &[u8] =
    include_bytes!("fixtures/generators/generate-dependency-colored-sxpid-oracle.py");
const REPOSITORY_GENERATOR_PATH: &str = "../../scripts/generate-dependency-colored-sxpid-oracle.py";
// These are bounded fixture tolerances, not a general floating-point error theorem.
const FIXTURE_EPSILON_MULTIPLIER: f64 = 32.0;
const MAX_OUTPUT_ABSOLUTE_ERROR_NATS: f64 = FIXTURE_EPSILON_MULTIPLIER * f64::EPSILON;

fn assert_repository_generator_matches_packaged_mirror() {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join(REPOSITORY_GENERATOR_PATH);
    match std::fs::read(&path) {
        Ok(repository_bytes) => assert_eq!(
            repository_bytes,
            GENERATOR_BYTES,
            "packaged fixture-generator mirror differs from {}",
            path.display()
        ),
        Err(error) if error.kind() == ErrorKind::NotFound => {
            // A published crate has no repository-level scripts directory. The embedded mirror
            // remains digest-bound below so every shipped test target is self-contained.
        }
        Err(error) => panic!(
            "cannot read repository generator {}: {error}",
            path.display()
        ),
    }
}

#[derive(Deserialize)]
struct Fixture {
    arithmetic: Arithmetic,
    binary64_stability_challenges: Binary64StabilityChallenges,
    challenge_cases: ChallengeCases,
    conditioned_diamond_extremal_regimes: Vec<ConditionedDiamondExtremalRegime>,
    conditioned_diamond_gradient_cases: Vec<ConditionedDiamondGradientCase>,
    generator: Generator,
    local_sxpid2_modulus_cases: Vec<LocalSxPid2ModulusCase>,
    method_provenance: MethodProvenance,
    schema: String,
    schema_revision: usize,
    scope_boundary: String,
    window_case: WindowCase,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Binary64StabilityChallenges {
    diamond_ceiling_cases: Vec<Binary64DiamondCeilingCase>,
    modulus_cases: Vec<Binary64ModulusCase>,
    reference_input_model: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Binary64ModulusCase {
    adaptive_branch: String,
    eta_binary64_bits: String,
    eta_input: String,
    expected_lambda_nats: String,
    expected_refined_modulus_nats: String,
    name: String,
    naive_route: String,
    naive_route_must_fail: bool,
    p_min_binary64_bits: String,
    p_min_input: String,
    q_floor_binary64: String,
    q_floor_binary64_bits: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Binary64DiamondCeilingCase {
    adaptive_branch: String,
    expected_diamond_ceiling_nats: String,
    name: String,
    naive_route: String,
    naive_route_must_fail: bool,
    q_floor_binary64_bits: String,
    q_floor_input: String,
}

#[derive(Deserialize)]
struct ChallengeCases {
    conditioned_diamond_negative_lift: Vec<ConditionedDiamondNegativeLiftCounterexample>,
    net_weight_half_factor: NetWeightHalfFactorCounterexample,
    non_synergy_refined_modulus: Vec<NonSynergyRefinedModulusCounterexample>,
}

#[derive(Deserialize)]
struct ConditionedDiamondNegativeLiftCounterexample {
    base_masses: Vec<String>,
    claimed_reciprocal_bound: String,
    full_masses: Vec<String>,
    gradient_values: BTreeMap<String, String>,
    maximum_diameter: String,
    maximizing_ordered_pairs: Vec<Vec<String>>,
    name: String,
    statement: String,
    violated_lift: Vec<String>,
}

#[derive(Deserialize)]
struct NetWeightHalfFactorCounterexample {
    sxpid_specific_status: String,
}

#[derive(Deserialize)]
struct NonSynergyRefinedModulusCounterexample {
    attained_lambda_nats: String,
    components: Vec<String>,
    first_sources: Vec<usize>,
    first_target: usize,
    name: String,
    node_masks: Vec<u8>,
    p_population_count_table: Vec<CountedState>,
    q_population_count_table: Vec<CountedState>,
    refined_synergy_modulus_nats: String,
    stored_component_changes_nats: BTreeMap<String, String>,
}

#[derive(Deserialize)]
struct ConditionedDiamondGradientCase {
    gradient_values: BTreeMap<String, String>,
    masses: ConditionedDiamondMasses,
    maximum_normalized_diameter: String,
    maximum_normalized_refined_diameter: String,
    maximizing_ordered_pairs: Vec<Vec<String>>,
    mass_scope: String,
    name: String,
    oriented_fb_minus_xc: String,
    ordered_pair_count: usize,
    reciprocal_x_a_bound: String,
    refined_diameter_bound: String,
}

#[derive(Deserialize)]
struct ConditionedDiamondExtremalRegime {
    diameter: String,
    masses: ConditionedDiamondMasses,
    maximum_coordinate: String,
    minimum_coordinate: String,
}

#[derive(Deserialize)]
struct ConditionedDiamondMasses {
    x_a: String,
    x_b: String,
    x_c: String,
    y_a: String,
    y_b: String,
    y_c: String,
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
    q_diamond_ceiling_nats: String,
    refined_synergy_modulus_nats: String,
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

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SignedExactFraction {
    numerator: i128,
    denominator: u128,
}

impl SignedExactFraction {
    fn parse(value: &str) -> Self {
        let (numerator, denominator) = value
            .split_once('/')
            .unwrap_or_else(|| panic!("signed fixture fraction {value:?} must contain one slash"));
        assert!(
            !denominator.contains('/'),
            "signed fixture fraction {value:?} must contain one slash"
        );
        let numerator = numerator
            .parse::<i128>()
            .unwrap_or_else(|error| panic!("invalid signed numerator in {value:?}: {error}"));
        let denominator = denominator
            .parse::<u128>()
            .unwrap_or_else(|error| panic!("invalid signed denominator in {value:?}: {error}"));
        Self::new(numerator, denominator)
    }

    fn new(numerator: i128, denominator: u128) -> Self {
        assert!(
            denominator > 0,
            "signed fixture fraction denominator must be positive"
        );
        let divisor = greatest_common_divisor(numerator.unsigned_abs(), denominator);
        Self {
            numerator: numerator
                / i128::try_from(divisor).expect("signed fraction divisor must fit in i128"),
            denominator: denominator / divisor,
        }
    }

    fn from_nonnegative(value: ExactFraction) -> Self {
        Self::new(
            i128::try_from(value.numerator).expect("fixture numerator must fit in i128"),
            value.denominator,
        )
    }

    fn reciprocal_of_positive(value: ExactFraction) -> Self {
        assert!(
            value.numerator > 0,
            "exact reciprocal requires a positive fraction"
        );
        Self::new(
            i128::try_from(value.denominator).expect("fixture denominator must fit in i128"),
            value.numerator,
        )
    }

    fn checked_add(self, other: Self) -> Self {
        let left = self
            .numerator
            .checked_mul(
                i128::try_from(other.denominator)
                    .expect("signed fraction denominator must fit in i128"),
            )
            .expect("signed fraction addition overflowed on the left");
        let right = other
            .numerator
            .checked_mul(
                i128::try_from(self.denominator)
                    .expect("signed fraction denominator must fit in i128"),
            )
            .expect("signed fraction addition overflowed on the right");
        let numerator = left
            .checked_add(right)
            .expect("signed fraction addition numerator overflowed");
        let denominator = self
            .denominator
            .checked_mul(other.denominator)
            .expect("signed fraction addition denominator overflowed");
        Self::new(numerator, denominator)
    }

    fn checked_sub(self, other: Self) -> Self {
        self.checked_add(Self::new(
            other
                .numerator
                .checked_neg()
                .expect("signed fraction negation overflowed"),
            other.denominator,
        ))
    }

    fn is_strictly_less_than(self, other: Self) -> bool {
        let left = self
            .numerator
            .checked_mul(
                i128::try_from(other.denominator)
                    .expect("signed fraction denominator must fit in i128"),
            )
            .expect("signed fraction comparison overflowed on the left");
        let right = other
            .numerator
            .checked_mul(
                i128::try_from(self.denominator)
                    .expect("signed fraction denominator must fit in i128"),
            )
            .expect("signed fraction comparison overflowed on the right");
        left < right
    }

    fn absolute_value(self) -> ExactFraction {
        ExactFraction::new(self.numerator.unsigned_abs(), self.denominator)
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
    q_diamond_ceiling_nats: f64,
    refined_synergy_modulus_nats: f64,
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

fn ordinary_diamond_gradient_exact(
    common: ExactFraction,
    left_exclusive: ExactFraction,
    right_exclusive: ExactFraction,
) -> [SignedExactFraction; 4] {
    assert!(common.numerator > 0);
    let common_left = common.checked_add(left_exclusive);
    let common_right = common.checked_add(right_exclusive);
    let union = common_left.checked_add(right_exclusive);
    let reciprocal_common = SignedExactFraction::reciprocal_of_positive(common);
    let reciprocal_left = SignedExactFraction::reciprocal_of_positive(common_left);
    let reciprocal_right = SignedExactFraction::reciprocal_of_positive(common_right);
    let reciprocal_union = SignedExactFraction::reciprocal_of_positive(union);
    [
        reciprocal_left
            .checked_add(reciprocal_right)
            .checked_sub(reciprocal_common)
            .checked_sub(reciprocal_union),
        reciprocal_left.checked_sub(reciprocal_union),
        reciprocal_right.checked_sub(reciprocal_union),
        SignedExactFraction::from_nonnegative(ExactFraction::from_integer(0)),
    ]
}

fn signed_coordinate_diameter(values: &[SignedExactFraction]) -> ExactFraction {
    values
        .iter()
        .flat_map(|left| {
            values
                .iter()
                .map(move |right| left.checked_sub(*right).absolute_value())
        })
        .fold(ExactFraction::from_integer(0), |maximum, difference| {
            if maximum.is_strictly_less_than(difference) {
                difference
            } else {
                maximum
            }
        })
}

fn minimum_signed_coordinate(values: &[SignedExactFraction]) -> SignedExactFraction {
    let mut minimum = *values
        .first()
        .expect("an exact coordinate collection must not be empty");
    for value in &values[1..] {
        if value.is_strictly_less_than(minimum) {
            minimum = *value;
        }
    }
    minimum
}

fn maximum_signed_coordinate(values: &[SignedExactFraction]) -> SignedExactFraction {
    let mut maximum = *values
        .first()
        .expect("an exact coordinate collection must not be empty");
    for value in &values[1..] {
        if maximum.is_strictly_less_than(*value) {
            maximum = *value;
        }
    }
    maximum
}

fn maximum_exact_fraction(values: &[ExactFraction]) -> ExactFraction {
    let mut maximum = *values
        .first()
        .expect("an exact fraction collection must not be empty");
    for value in &values[1..] {
        if maximum.is_strictly_less_than(*value) {
            maximum = *value;
        }
    }
    maximum
}

fn exact_ordinary_diamond_diameter(
    common: ExactFraction,
    left_exclusive: ExactFraction,
    right_exclusive: ExactFraction,
) -> ExactFraction {
    let larger_exclusive = if left_exclusive.is_strictly_less_than(right_exclusive) {
        right_exclusive
    } else {
        left_exclusive
    };
    common
        .reciprocal()
        .checked_sub(common.checked_add(larger_exclusive).reciprocal())
}

fn conditioned_nested_gradient_exact(
    x_a: ExactFraction,
    x_b: ExactFraction,
    y_a: ExactFraction,
    y_b: ExactFraction,
) -> [SignedExactFraction; 5] {
    let reciprocal_x_a = SignedExactFraction::reciprocal_of_positive(x_a);
    let reciprocal_x_ab = SignedExactFraction::reciprocal_of_positive(x_a.checked_add(x_b));
    let reciprocal_total_a = SignedExactFraction::reciprocal_of_positive(x_a.checked_add(y_a));
    let reciprocal_total_ab = SignedExactFraction::reciprocal_of_positive(
        x_a.checked_add(x_b).checked_add(y_a).checked_add(y_b),
    );
    [
        reciprocal_total_ab.checked_sub(reciprocal_total_a),
        reciprocal_total_ab,
        reciprocal_total_ab
            .checked_sub(reciprocal_total_a)
            .checked_sub(reciprocal_x_ab)
            .checked_add(reciprocal_x_a),
        reciprocal_total_ab.checked_sub(reciprocal_x_ab),
        SignedExactFraction::from_nonnegative(ExactFraction::from_integer(0)),
    ]
}

fn exact_conditioned_nested_closed_form_diameter(
    x_a: ExactFraction,
    x_b: ExactFraction,
    y_a: ExactFraction,
) -> ExactFraction {
    let reciprocal_x_a = x_a.reciprocal();
    let reciprocal_x_ab = x_a.checked_add(x_b).reciprocal();
    let reciprocal_total_a = x_a.checked_add(y_a).reciprocal();
    maximum_exact_fraction(&[
        reciprocal_total_a,
        reciprocal_x_ab,
        reciprocal_x_a.checked_sub(reciprocal_x_ab),
        reciprocal_x_a.checked_sub(reciprocal_total_a),
    ])
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
    let adaptive_modulus = adaptive_refined_modulus(p_min_f64, eta_f64);
    let lambda_nats = adaptive_modulus.lambda_nats;
    let refined_synergy_modulus_nats = adaptive_modulus.refined_nats;
    let log_support_floor_nats = p_min.reciprocal().to_f64().ln();
    let h_nats = (2.0 / (1.0 + p_min_f64)).ln();
    let diamond_ceiling_nats = log_support_floor_nats - 2.0 * h_nats;
    let q_floor = p_min_f64 - eta_f64;
    let q_log_floor_nats = q_floor.recip().ln();
    let q_h_nats = (2.0 / (1.0 + q_floor)).ln();
    let q_diamond_ceiling_nats = q_log_floor_nats - 2.0 * q_h_nats;
    assert!(lambda_nats.is_finite());
    assert!(
        refined_synergy_modulus_nats >= 0.0 && refined_synergy_modulus_nats.is_finite(),
        "{} must have a finite nonnegative refined synergy modulus",
        case.name
    );
    assert!(log_support_floor_nats.is_finite());
    assert!(h_nats.is_finite());
    assert!(diamond_ceiling_nats.is_finite());
    assert!(
        q_diamond_ceiling_nats + MAX_OUTPUT_ABSOLUTE_ERROR_NATS >= diamond_ceiling_nats
            && q_diamond_ceiling_nats <= q_log_floor_nats + MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
        "{} must have an ordered finite q-law diamond ceiling",
        case.name
    );
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
        q_diamond_ceiling_nats,
        refined_synergy_modulus_nats,
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
    let pointwise_modulus = match family {
        AtomFamily::RedundancyOrUnique => modulus.lambda_nats,
        AtomFamily::Synergy => modulus.refined_synergy_modulus_nats,
    };
    let mut averaged_component_bound = modulus
        .log_support_floor_nats
        .min(pointwise_modulus + modulus.eta_total_variation * component_weight_range);
    let mut averaged_net_bound = (2.0 * modulus.log_support_floor_nats)
        .min(pointwise_modulus + modulus.delta_l1 * net_weight_range);
    if family == AtomFamily::Synergy {
        averaged_component_bound = averaged_component_bound.min(modulus.q_diamond_ceiling_nats);
        averaged_net_bound =
            averaged_net_bound.min(modulus.diamond_ceiling_nats + modulus.q_diamond_ceiling_nats);
    }
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
            informative: pointwise_modulus,
            misinformative: pointwise_modulus,
            net: pointwise_modulus,
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

fn assert_stability_decimal_matches(
    actual: f64,
    stored: &str,
    operation_scale: f64,
    context: &str,
) -> f64 {
    let expected = decimal(stored);
    if expected == 0.0 {
        assert_eq!(
            stored, "0",
            "{context} stored reference must be exact algebraic zero, not an underflowed value"
        );
        assert_eq!(
            expected.to_bits(),
            0.0_f64.to_bits(),
            "{context} stored reference must be positive zero"
        );
        assert_eq!(
            actual.to_bits(),
            0.0_f64.to_bits(),
            "{context} must reconstruct exact positive zero"
        );
        return 0.0;
    }
    assert!(
        operation_scale.is_finite() && operation_scale >= 0.0,
        "{context} has an invalid bounded-operation scale"
    );
    let error = (actual - expected).abs();
    // This scale covers only the committed operations and their displayed cancellation.
    // It is not a general binary64 error theorem.
    let tolerance = 256.0 * f64::EPSILON * expected.abs().max(operation_scale);
    assert!(
        error <= tolerance,
        "{context} reconstructed value {actual:.17e} differs from the 400-digit reference \
         {expected:.17e} by {error:.17e}, above tolerance {tolerance:.17e}"
    );
    tolerance
}

fn positive_log1pmx_series(ratio: f64) -> f64 {
    assert!((0.0..=0.5).contains(&ratio));
    let mut sum = 0.0;
    let mut power = ratio * ratio;
    for denominator in 2_u32..=4096 {
        let next = sum + power / f64::from(denominator);
        if next.to_bits() == sum.to_bits() {
            return sum;
        }
        sum = next;
        power *= ratio;
    }
    panic!("positive log1pmx series did not converge within its bounded iteration count");
}

struct AdaptiveModulus {
    branch: &'static str,
    lambda_nats: f64,
    refined_nats: f64,
}

fn adaptive_refined_modulus(p_min: f64, eta: f64) -> AdaptiveModulus {
    assert!(p_min.is_finite() && eta.is_finite());
    assert!(p_min > 0.0 && p_min <= 1.0);
    assert!(eta >= 0.0 && eta < p_min);
    let q_floor = p_min - eta;
    assert!(
        q_floor.is_finite() && q_floor > 0.0,
        "the represented q-law floor must remain positive"
    );
    if eta == 0.0 {
        return AdaptiveModulus {
            branch: "zero",
            lambda_nats: 0.0,
            refined_nats: 0.0,
        };
    }

    let ratio = eta / p_min;
    if ratio <= 0.5 {
        let remainder = positive_log1pmx_series(ratio);
        AdaptiveModulus {
            branch: "series",
            lambda_nats: ratio + remainder,
            refined_nats: remainder + ratio * (1.0 - p_min),
        }
    } else {
        let floor_ratio = q_floor / p_min;
        // This bounded route assumes IEEE gradual underflow. FTZ and DAZ are outside its contract.
        let largest_below_half = f64::from_bits(0.5_f64.to_bits() - 1);
        assert!(
            floor_ratio >= 2.0_f64.powi(-53) && floor_ratio <= largest_below_half,
            "the bounded represented-input route requires q_floor / p_min in \
             [2^-53, nextDown(1/2)]"
        );
        let lambda_nats = -floor_ratio.ln();
        AdaptiveModulus {
            branch: "quotient-log",
            lambda_nats,
            refined_nats: lambda_nats - eta,
        }
    }
}

struct AdaptiveDiamondCeiling {
    branch: &'static str,
    value: f64,
}

fn adaptive_diamond_ceiling(q_floor: f64) -> AdaptiveDiamondCeiling {
    assert!(q_floor.is_finite() && q_floor > 0.0 && q_floor <= 1.0);
    if q_floor > 0.5 {
        let value = if q_floor == 1.0 {
            0.0
        } else {
            let transformed = (1.0 - q_floor) / (1.0 + q_floor);
            -(-(transformed * transformed)).ln_1p()
        };
        AdaptiveDiamondCeiling {
            branch: "atanh-transform",
            value,
        }
    } else {
        AdaptiveDiamondCeiling {
            branch: "log-domain",
            value: 2.0 * q_floor.ln_1p() - q_floor.ln() - 4.0_f64.ln(),
        }
    }
}

fn assert_naive_route_fails(naive: f64, expected: f64, tolerance: f64, context: &str) {
    assert!(
        tolerance.is_finite() && tolerance > 0.0,
        "{context} must have a finite positive tolerance before it challenges a naive route"
    );
    assert!(
        !naive.is_finite() || (naive - expected).abs() > 1024.0 * tolerance,
        "{context} did not separate the intended naive route from the high-precision reference"
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
    assert_eq!(fixture.schema_revision, 7);
    assert_eq!(fixture.arithmetic.decimal_precision_digits, 400);
    assert_eq!(fixture.arithmetic.fraction_arithmetic, "exact");
    assert!(fixture.arithmetic.third_party_dependencies.is_empty());
    assert!(fixture.generator.standard_library_only);
    assert_eq!(
        fixture.generator.path,
        "scripts/generate-dependency-colored-sxpid-oracle.py"
    );
    assert_repository_generator_matches_packaged_mirror();
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
    let conditioned_counterexamples = &fixture.challenge_cases.conditioned_diamond_negative_lift;
    assert_eq!(conditioned_counterexamples.len(), 3);
    assert!(conditioned_counterexamples.iter().all(|case| case.statement
        == "separately valid base and full diamonds do not suffice when a componentwise lift increment is negative"));
    assert_eq!(
        fixture.scope_boundary,
        "bounded fraction-exact and 400-digit Decimal challenges; not a general theorem, binary64 certificate, external review, or continuous-PID result"
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
fn binary64_stability_challenges_reconstruct_high_precision_references() {
    let one = std::hint::black_box(1.0_f64);
    let half_ulp_at_one = std::hint::black_box(2.0_f64.powi(-53));
    assert_eq!(
        (one + half_ulp_at_one).to_bits(),
        1.0_f64.to_bits(),
        "the bounded test requires round-to-nearest, ties-to-even binary64 arithmetic"
    );
    let three_half_ulps_at_one = std::hint::black_box(3.0_f64 * 2.0_f64.powi(-53));
    assert_eq!(
        (one + three_half_ulps_at_one).to_bits(),
        1.0_f64.to_bits() + 2,
        "the bounded test requires the even upper neighbor at the complementary tie"
    );
    let smallest_normal = std::hint::black_box(f64::MIN_POSITIVE);
    let two = std::hint::black_box(2.0_f64);
    assert_eq!(
        (smallest_normal / two).to_bits(),
        1_u64 << 51,
        "the bounded test requires IEEE gradual underflow"
    );

    let fixture = fixture();
    let challenges = fixture.binary64_stability_challenges;
    assert_eq!(
        challenges.reference_input_model,
        "400-digit Decimal functions applied to the exact real values of the binary64 numbers \
         parsed from the stored decimal inputs; stored hexadecimal payloads bind each parsed \
         operand and represented subtraction result"
    );
    assert_eq!(challenges.modulus_cases.len(), 10);
    assert_eq!(challenges.diamond_ceiling_cases.len(), 6);

    {
        let seam_eta = |name: &str| {
            let case = challenges
                .modulus_cases
                .iter()
                .find(|case| case.name == name)
                .unwrap_or_else(|| panic!("fixture omitted modulus seam case {name}"));
            assert_eq!(decimal(&case.p_min_input).to_bits(), 0.5_f64.to_bits());
            decimal(&case.eta_input)
        };
        let below = seam_eta("branch-seam-below-half");
        let at = seam_eta("branch-seam-at-half");
        let above = seam_eta("branch-seam-above-half");
        assert_eq!(below.to_bits() + 1, at.to_bits());
        assert_eq!(at.to_bits() + 1, above.to_bits());
        assert_eq!((at / 0.5).to_bits(), 0.5_f64.to_bits());
        assert!(below / 0.5 < 0.5);
        assert!(above / 0.5 > 0.5);
    }

    {
        let seam_floor = |name: &str| {
            let case = challenges
                .diamond_ceiling_cases
                .iter()
                .find(|case| case.name == name)
                .unwrap_or_else(|| panic!("fixture omitted diamond seam case {name}"));
            decimal(&case.q_floor_input)
        };
        let below = seam_floor("q-floor-seam-below-half");
        let at = seam_floor("q-floor-seam-at-half");
        let above = seam_floor("q-floor-seam-above-half");
        assert_eq!(below.to_bits() + 1, at.to_bits());
        assert_eq!(at.to_bits() + 1, above.to_bits());
    }

    for case in challenges.modulus_cases {
        let p_min = decimal(&case.p_min_input);
        let eta = decimal(&case.eta_input);
        let q_floor = p_min - eta;
        assert_eq!(
            format!("{:#018x}", p_min.to_bits()),
            case.p_min_binary64_bits,
            "{} changed its p_min binary64 payload",
            case.name
        );
        assert_eq!(
            format!("{:#018x}", eta.to_bits()),
            case.eta_binary64_bits,
            "{} changed its eta binary64 payload",
            case.name
        );
        assert_eq!(
            q_floor.to_bits(),
            decimal(&case.q_floor_binary64).to_bits(),
            "{} changed its represented q-law floor",
            case.name
        );
        assert_eq!(
            format!("{:#018x}", q_floor.to_bits()),
            case.q_floor_binary64_bits,
            "{} changed its q-law floor binary64 payload",
            case.name
        );
        let reconstructed = adaptive_refined_modulus(p_min, eta);
        assert_eq!(
            reconstructed.branch, case.adaptive_branch,
            "{} selected the wrong adaptive modulus branch",
            case.name
        );
        match case.name.as_str() {
            "extreme-normal-above-half" => {
                assert!(p_min.is_normal());
                assert!(eta.is_normal());
                assert!(q_floor.is_normal());
                assert_ne!(
                    case.expected_lambda_nats, case.expected_refined_modulus_nats,
                    "the high-precision reference must resolve the extreme refined subtraction"
                );
            }
            "near-boundary-subnormal-floor" => {
                assert!(p_min.is_normal());
                assert!(eta.is_normal());
                assert!(q_floor.is_subnormal());
            }
            "upper-floor-ratio-lower-endpoint" => {
                assert_eq!(p_min.to_bits(), 1.0_f64.to_bits());
                assert_eq!(eta.to_bits(), 1.0_f64.to_bits() - 1);
                assert_eq!(q_floor.to_bits(), 2.0_f64.powi(-53).to_bits());
                assert_eq!((q_floor / p_min).to_bits(), 2.0_f64.powi(-53).to_bits());
            }
            _ => {}
        }
        let quotient_log_scale = if reconstructed.branch == "quotient-log" {
            let floor_ratio = q_floor / p_min;
            assert!(
                (2.0_f64.powi(-53)..=f64::from_bits(0.5_f64.to_bits() - 1)).contains(&floor_ratio)
            );
            floor_ratio.ln().abs()
        } else {
            0.0
        };
        assert_stability_decimal_matches(
            reconstructed.lambda_nats,
            &case.expected_lambda_nats,
            quotient_log_scale,
            &format!("{} lambda", case.name),
        );
        let tolerance = assert_stability_decimal_matches(
            reconstructed.refined_nats,
            &case.expected_refined_modulus_nats,
            quotient_log_scale + eta.abs(),
            &format!("{} refined modulus", case.name),
        );
        let expected = decimal(&case.expected_refined_modulus_nats);
        match case.naive_route.as_str() {
            "none" => assert!(
                !case.naive_route_must_fail,
                "{} cannot require a missing naive route to fail",
                case.name
            ),
            "ratio-log-minus-eta" => {
                assert!(case.naive_route_must_fail);
                let naive = (p_min / q_floor).ln() - eta;
                assert_naive_route_fails(naive, expected, tolerance, &case.name);
            }
            "ratio-log1p-minus-eta" => {
                assert!(case.naive_route_must_fail);
                let ratio = eta / p_min;
                let naive = -(-ratio).ln_1p() - eta;
                assert_naive_route_fails(naive, expected, tolerance, &case.name);
            }
            other => panic!("{} has unknown naive modulus route {other:?}", case.name),
        }
    }

    for case in challenges.diamond_ceiling_cases {
        let q_floor = decimal(&case.q_floor_input);
        assert_eq!(
            format!("{:#018x}", q_floor.to_bits()),
            case.q_floor_binary64_bits,
            "{} changed its q-law floor binary64 payload",
            case.name
        );
        let reconstructed = adaptive_diamond_ceiling(q_floor);
        assert_eq!(
            reconstructed.branch, case.adaptive_branch,
            "{} selected the wrong adaptive diamond branch",
            case.name
        );
        if case.name == "q-floor-subnormal" {
            assert!(q_floor.is_subnormal());
        } else {
            assert!(q_floor.is_normal());
        }
        let operation_scale = if reconstructed.branch == "log-domain" {
            2.0 * q_floor.ln_1p().abs() + q_floor.ln().abs() + 4.0_f64.ln()
        } else {
            0.0
        };
        let tolerance = assert_stability_decimal_matches(
            reconstructed.value,
            &case.expected_diamond_ceiling_nats,
            operation_scale,
            &format!("{} diamond ceiling", case.name),
        );
        assert_eq!(case.naive_route, "product-ratio-log");
        if case.naive_route_must_fail {
            let naive = ((1.0 + q_floor).powi(2) / (4.0 * q_floor)).ln();
            assert_naive_route_fails(
                naive,
                decimal(&case.expected_diamond_ceiling_nats),
                tolerance,
                &case.name,
            );
        }
    }
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
fn conditioned_diamond_gradient_cases_cover_all_pairs_exactly() {
    let fixture = fixture();
    assert_eq!(fixture.schema_revision, 7);
    assert_eq!(fixture.conditioned_diamond_gradient_cases.len(), 7);
    let labels = ["Fa", "Fb", "Fc", "Fo", "Xa", "Xb", "Xc", "Xo"];
    for case in fixture.conditioned_diamond_gradient_cases {
        let x_a = ExactFraction::parse(&case.masses.x_a);
        let x_b = ExactFraction::parse(&case.masses.x_b);
        let x_c = ExactFraction::parse(&case.masses.x_c);
        let y_a = ExactFraction::parse(&case.masses.y_a);
        let y_b = ExactFraction::parse(&case.masses.y_b);
        let y_c = ExactFraction::parse(&case.masses.y_c);
        assert!(
            x_a.numerator > 0,
            "{} must have positive common target-region mass",
            case.name
        );
        let total_mass = x_a
            .checked_add(x_b)
            .checked_add(x_c)
            .checked_add(y_a)
            .checked_add(y_b)
            .checked_add(y_c);
        match case.mass_scope.as_str() {
            "probability-region-compatible" => assert!(
                !ExactFraction::from_integer(1).is_strictly_less_than(total_mass),
                "{} probability-region masses exceed one",
                case.name
            ),
            "algebra-only-unnormalized" => assert!(
                ExactFraction::from_integer(1).is_strictly_less_than(total_mass),
                "{} algebra-only masses no longer exceed one",
                case.name
            ),
            value => panic!("{} has unknown mass scope {value:?}", case.name),
        }

        let base = ordinary_diamond_gradient_exact(x_a, x_b, x_c);
        let total = ordinary_diamond_gradient_exact(
            x_a.checked_add(y_a),
            x_b.checked_add(y_b),
            x_c.checked_add(y_c),
        );
        assert_eq!(
            signed_coordinate_diameter(&base),
            exact_ordinary_diamond_diameter(x_a, x_b, x_c),
            "{} base ordinary-diamond diameter is not exact",
            case.name
        );
        assert_eq!(
            signed_coordinate_diameter(&total),
            exact_ordinary_diamond_diameter(
                x_a.checked_add(y_a),
                x_b.checked_add(y_b),
                x_c.checked_add(y_c),
            ),
            "{} full ordinary-diamond diameter is not exact",
            case.name
        );
        let gradients = [
            total[0],
            total[1],
            total[2],
            total[3],
            total[0].checked_sub(base[0]),
            total[1].checked_sub(base[1]),
            total[2].checked_sub(base[2]),
            total[3].checked_sub(base[3]),
        ];
        assert_eq!(
            case.gradient_values.len(),
            labels.len(),
            "{} must store exactly the eight lifted coordinates",
            case.name
        );
        for (label, value) in labels.iter().zip(gradients) {
            let stored = case
                .gradient_values
                .get(*label)
                .unwrap_or_else(|| panic!("{} omitted gradient {label}", case.name));
            assert_eq!(
                value,
                SignedExactFraction::parse(stored),
                "{} gradient {label} does not match the exact Rust reconstruction",
                case.name
            );
        }

        let reciprocal_x_a = SignedExactFraction::reciprocal_of_positive(x_a);
        let reciprocal_x_ab = SignedExactFraction::reciprocal_of_positive(x_a.checked_add(x_b));
        let reciprocal_x_ac = SignedExactFraction::reciprocal_of_positive(x_a.checked_add(x_c));
        let reciprocal_x_abc =
            SignedExactFraction::reciprocal_of_positive(x_a.checked_add(x_b).checked_add(x_c));
        let reciprocal_total_a = SignedExactFraction::reciprocal_of_positive(x_a.checked_add(y_a));
        let reciprocal_total_ab = SignedExactFraction::reciprocal_of_positive(
            x_a.checked_add(x_b).checked_add(y_a).checked_add(y_b),
        );
        let reciprocal_total_ac = SignedExactFraction::reciprocal_of_positive(
            x_a.checked_add(x_c).checked_add(y_a).checked_add(y_c),
        );
        let observed_candidate_differences = [
            gradients[1].checked_sub(gradients[0]),
            gradients[2].checked_sub(gradients[0]),
            gradients[4].checked_sub(gradients[0]),
            gradients[1].checked_sub(gradients[5]),
            gradients[2].checked_sub(gradients[6]),
            gradients[4].checked_sub(gradients[5]),
            gradients[4].checked_sub(gradients[6]),
            gradients[1].checked_sub(gradients[6]),
            gradients[2].checked_sub(gradients[5]),
        ];
        let closed_form_candidate_differences = [
            reciprocal_total_a.checked_sub(reciprocal_total_ac),
            reciprocal_total_a.checked_sub(reciprocal_total_ab),
            reciprocal_x_a
                .checked_add(reciprocal_x_abc)
                .checked_sub(reciprocal_x_ab)
                .checked_sub(reciprocal_x_ac),
            reciprocal_x_ab.checked_sub(reciprocal_x_abc),
            reciprocal_x_ac.checked_sub(reciprocal_x_abc),
            reciprocal_x_a
                .checked_sub(reciprocal_x_ac)
                .checked_add(reciprocal_total_ac)
                .checked_sub(reciprocal_total_a),
            reciprocal_x_a
                .checked_sub(reciprocal_x_ab)
                .checked_add(reciprocal_total_ab)
                .checked_sub(reciprocal_total_a),
            reciprocal_total_ab
                .checked_sub(reciprocal_total_ac)
                .checked_add(reciprocal_x_ac)
                .checked_sub(reciprocal_x_abc),
            reciprocal_total_ac
                .checked_sub(reciprocal_total_ab)
                .checked_add(reciprocal_x_ab)
                .checked_sub(reciprocal_x_abc),
        ];
        assert_eq!(
            observed_candidate_differences, closed_form_candidate_differences,
            "{} conditioned-diamond candidate identities are not exact",
            case.name
        );
        let candidate_lower =
            minimum_signed_coordinate(&[gradients[0], gradients[5], gradients[6]]);
        let candidate_upper =
            maximum_signed_coordinate(&[gradients[1], gradients[2], gradients[4]]);
        let candidate_diameter = candidate_upper
            .checked_sub(candidate_lower)
            .absolute_value();
        assert_eq!(
            candidate_diameter,
            maximum_signed_coordinate(&observed_candidate_differences).absolute_value(),
            "{} conditioned-diamond candidate extrema and nine differences disagree",
            case.name
        );

        let nested_gradients = conditioned_nested_gradient_exact(x_a, x_b, y_a, y_b);
        let nested_candidate_lower =
            minimum_signed_coordinate(&[nested_gradients[0], nested_gradients[3]]);
        let nested_candidate_upper =
            maximum_signed_coordinate(&[nested_gradients[1], nested_gradients[2]]);
        let nested_candidate_diameter = nested_candidate_upper
            .checked_sub(nested_candidate_lower)
            .absolute_value();
        let nested_closed_form_diameter =
            exact_conditioned_nested_closed_form_diameter(x_a, x_b, y_a);
        assert_eq!(
            signed_coordinate_diameter(&nested_gradients),
            nested_candidate_diameter,
            "{} conditioned-nested candidate extrema are not exact",
            case.name
        );
        assert_eq!(
            nested_candidate_diameter, nested_closed_form_diameter,
            "{} conditioned-nested closed-form diameter is not exact",
            case.name
        );

        let bound = x_a.reciprocal();
        let refined_bound = bound.checked_sub(total_mass.reciprocal());
        assert_eq!(
            bound,
            ExactFraction::parse(&case.reciprocal_x_a_bound),
            "{} reciprocal bound is stale",
            case.name
        );
        assert_eq!(
            refined_bound,
            ExactFraction::parse(&case.refined_diameter_bound),
            "{} refined diameter bound is stale",
            case.name
        );
        assert_eq!(
            case.ordered_pair_count,
            labels.len() * labels.len(),
            "{} does not declare all ordered coordinate pairs",
            case.name
        );
        let mut maximum = ExactFraction::from_integer(0);
        let mut maximizing_pairs = Vec::new();
        for (left_index, left_label) in labels.iter().enumerate() {
            for (right_index, right_label) in labels.iter().enumerate() {
                let difference = gradients[left_index]
                    .checked_sub(gradients[right_index])
                    .absolute_value();
                assert!(
                    !refined_bound.is_strictly_less_than(difference),
                    "{} pair {left_label}-{right_label} exceeds its refined bound",
                    case.name
                );
                if maximum.is_strictly_less_than(difference) {
                    maximum = difference;
                    maximizing_pairs.clear();
                }
                if maximum == difference {
                    maximizing_pairs
                        .push(vec![(*left_label).to_string(), (*right_label).to_string()]);
                }
            }
        }
        assert_eq!(
            maximizing_pairs, case.maximizing_ordered_pairs,
            "{} maximizing pair list is stale",
            case.name
        );
        assert_eq!(
            maximum, candidate_diameter,
            "{} conditioned-diamond candidate extrema do not give the exact diameter",
            case.name
        );
        assert_eq!(
            maximum.checked_div(bound),
            ExactFraction::parse(&case.maximum_normalized_diameter),
            "{} normalized diameter is stale",
            case.name
        );
        assert_eq!(
            maximum.checked_div(refined_bound),
            ExactFraction::parse(&case.maximum_normalized_refined_diameter),
            "{} refined normalized diameter is stale",
            case.name
        );
        if case.mass_scope == "probability-region-compatible" {
            let probability_domain_bound = bound.checked_sub(ExactFraction::from_integer(1));
            assert!(
                !probability_domain_bound.is_strictly_less_than(refined_bound),
                "{} refined bound exceeds its probability-domain corollary",
                case.name
            );
            assert!(
                !probability_domain_bound.is_strictly_less_than(maximum),
                "{} exact diameter exceeds its probability-domain corollary",
                case.name
            );
        }
        let oriented_fb_minus_xc = gradients[1].checked_sub(gradients[6]);
        assert_eq!(
            oriented_fb_minus_xc,
            SignedExactFraction::parse(&case.oriented_fb_minus_xc),
            "{} oriented Fb-Xc difference is stale",
            case.name
        );
        match case.name.as_str() {
            "positive-cross-near-sharp" => {
                assert_eq!(oriented_fb_minus_xc, SignedExactFraction::new(999, 1));
                assert_eq!(maximum, refined_bound);
            }
            "negative-cross-near-sharp" => {
                assert_eq!(oriented_fb_minus_xc, SignedExactFraction::new(-999, 1));
                assert_eq!(maximum, refined_bound);
            }
            "zero-lift-boundary" => {
                assert!(
                    gradients[4..]
                        .iter()
                        .all(|value| *value == SignedExactFraction::new(0, 1)),
                    "zero lift must make every conditioned coordinate zero"
                );
            }
            "unnormalized-algebra-only" => {
                assert_eq!(case.mass_scope, "algebra-only-unnormalized");
            }
            _ => {}
        }
    }
}

#[test]
fn conditioned_diamond_extremal_regimes_cover_all_nine_pairs() {
    let fixture = fixture();
    let cases = fixture.conditioned_diamond_extremal_regimes;
    assert_eq!(cases.len(), 9);
    let expected_pairs = [
        ("Fa", "Fb"),
        ("Fa", "Fc"),
        ("Fa", "Xa"),
        ("Xb", "Fb"),
        ("Xb", "Fc"),
        ("Xb", "Xa"),
        ("Xc", "Fb"),
        ("Xc", "Fc"),
        ("Xc", "Xa"),
    ];
    let mut observed_pairs = Vec::new();
    for case in cases {
        let x_a = ExactFraction::parse(&case.masses.x_a);
        let x_b = ExactFraction::parse(&case.masses.x_b);
        let x_c = ExactFraction::parse(&case.masses.x_c);
        let y_a = ExactFraction::parse(&case.masses.y_a);
        let y_b = ExactFraction::parse(&case.masses.y_b);
        let y_c = ExactFraction::parse(&case.masses.y_c);
        let total_mass = x_a
            .checked_add(x_b)
            .checked_add(x_c)
            .checked_add(y_a)
            .checked_add(y_b)
            .checked_add(y_c);
        assert_eq!(
            total_mass,
            ExactFraction::from_integer(1),
            "extremal regime must be a normalized probability assignment"
        );
        assert!(
            [x_a, x_b, x_c, y_a, y_b, y_c]
                .iter()
                .all(|mass| mass.numerator > 0),
            "extremal regime must be in the strict interior"
        );
        let base = ordinary_diamond_gradient_exact(x_a, x_b, x_c);
        let full = ordinary_diamond_gradient_exact(
            x_a.checked_add(y_a),
            x_b.checked_add(y_b),
            x_c.checked_add(y_c),
        );
        let gradients = BTreeMap::from([
            ("Fa", full[0]),
            ("Fb", full[1]),
            ("Fc", full[2]),
            ("Fo", full[3]),
            ("Xa", full[0].checked_sub(base[0])),
            ("Xb", full[1].checked_sub(base[1])),
            ("Xc", full[2].checked_sub(base[2])),
            ("Xo", full[3].checked_sub(base[3])),
        ]);
        let minimum = *gradients
            .get(case.minimum_coordinate.as_str())
            .unwrap_or_else(|| panic!("unknown minimum coordinate {}", case.minimum_coordinate));
        let maximum = *gradients
            .get(case.maximum_coordinate.as_str())
            .unwrap_or_else(|| panic!("unknown maximum coordinate {}", case.maximum_coordinate));
        assert!(
            gradients.iter().all(|(label, value)| {
                !value.is_strictly_less_than(minimum)
                    && (*label == case.minimum_coordinate || *value != minimum)
            }),
            "{} is not the unique minimum coordinate",
            case.minimum_coordinate
        );
        assert!(
            gradients.iter().all(|(label, value)| {
                !maximum.is_strictly_less_than(*value)
                    && (*label == case.maximum_coordinate || *value != maximum)
            }),
            "{} is not the unique maximum coordinate",
            case.maximum_coordinate
        );
        assert_eq!(
            maximum.checked_sub(minimum).absolute_value(),
            ExactFraction::parse(&case.diameter),
            "extremal regime diameter is stale"
        );
        observed_pairs.push((
            case.minimum_coordinate.as_str().to_owned(),
            case.maximum_coordinate.as_str().to_owned(),
        ));
    }
    assert_eq!(
        observed_pairs,
        expected_pairs
            .iter()
            .map(|(minimum, maximum)| ((*minimum).to_owned(), (*maximum).to_owned()))
            .collect::<Vec<_>>()
    );
}

#[test]
fn conditioned_diamond_negative_lift_cases_are_reconstructed_exactly() {
    let fixture = fixture();
    let labels = ["Fa", "Fb", "Fc", "Fo", "Xa", "Xb", "Xc", "Xo"];
    let increment_labels = ["y_a", "y_b", "y_c"];
    let cases = fixture.challenge_cases.conditioned_diamond_negative_lift;
    assert_eq!(cases.len(), 3);
    for case in cases {
        assert_eq!(
            case.base_masses.len(),
            3,
            "{} base arity changed",
            case.name
        );
        assert_eq!(
            case.full_masses.len(),
            3,
            "{} full arity changed",
            case.name
        );
        let base: [ExactFraction; 3] =
            std::array::from_fn(|index| ExactFraction::parse(&case.base_masses[index]));
        let full: [ExactFraction; 3] =
            std::array::from_fn(|index| ExactFraction::parse(&case.full_masses[index]));
        assert!(
            base[0].numerator > 0 && full[0].numerator > 0,
            "{} common masses must be positive at both endpoints",
            case.name
        );
        let base_gradient = ordinary_diamond_gradient_exact(base[0], base[1], base[2]);
        let full_gradient = ordinary_diamond_gradient_exact(full[0], full[1], full[2]);
        let gradients = [
            full_gradient[0],
            full_gradient[1],
            full_gradient[2],
            full_gradient[3],
            full_gradient[0].checked_sub(base_gradient[0]),
            full_gradient[1].checked_sub(base_gradient[1]),
            full_gradient[2].checked_sub(base_gradient[2]),
            full_gradient[3].checked_sub(base_gradient[3]),
        ];
        assert_eq!(
            case.gradient_values.len(),
            labels.len(),
            "{} must store exactly eight coordinates",
            case.name
        );
        for (label, value) in labels.iter().zip(gradients) {
            let stored = case
                .gradient_values
                .get(*label)
                .unwrap_or_else(|| panic!("{} omitted coordinate {label}", case.name));
            assert_eq!(
                value,
                SignedExactFraction::parse(stored),
                "{} coordinate {label} is stale",
                case.name
            );
        }

        let increments = std::array::from_fn::<_, 3, _>(|index| {
            SignedExactFraction::from_nonnegative(full[index])
                .checked_sub(SignedExactFraction::from_nonnegative(base[index]))
        });
        assert_eq!(
            increments
                .iter()
                .filter(|value| value.numerator < 0)
                .count(),
            1,
            "{} must have exactly one negative lift increment",
            case.name
        );
        assert_eq!(
            case.violated_lift.len(),
            2,
            "{} violated-lift record changed shape",
            case.name
        );
        let violated_index = increment_labels
            .iter()
            .position(|label| *label == case.violated_lift[0])
            .unwrap_or_else(|| {
                panic!(
                    "{} has unknown lift label {:?}",
                    case.name, case.violated_lift[0]
                )
            });
        assert_eq!(
            increments[violated_index],
            SignedExactFraction::parse(&case.violated_lift[1]),
            "{} violated lift value is stale",
            case.name
        );

        let mut maximum = ExactFraction::from_integer(0);
        let mut maximizing_pairs = Vec::new();
        for (left_index, left_label) in labels.iter().enumerate() {
            for (right_index, right_label) in labels.iter().enumerate() {
                let difference = gradients[left_index]
                    .checked_sub(gradients[right_index])
                    .absolute_value();
                if maximum.is_strictly_less_than(difference) {
                    maximum = difference;
                    maximizing_pairs.clear();
                }
                if maximum == difference {
                    maximizing_pairs
                        .push(vec![(*left_label).to_string(), (*right_label).to_string()]);
                }
            }
        }
        assert_eq!(
            maximum,
            ExactFraction::parse(&case.maximum_diameter),
            "{} maximum diameter is stale",
            case.name
        );
        assert_eq!(
            maximizing_pairs, case.maximizing_ordered_pairs,
            "{} maximizing pairs are stale",
            case.name
        );
        let claimed_bound = base[0].reciprocal();
        assert_eq!(
            claimed_bound,
            ExactFraction::parse(&case.claimed_reciprocal_bound),
            "{} reciprocal bound is stale",
            case.name
        );
        assert!(
            claimed_bound.is_strictly_less_than(maximum),
            "{} no longer violates the weakened endpoint-only claim",
            case.name
        );
    }
}

#[test]
fn non_synergy_atoms_reject_the_synergy_only_modulus() {
    let fixture = fixture();
    let cases = fixture.challenge_cases.non_synergy_refined_modulus;
    assert_eq!(cases.len(), 6);
    for case in cases {
        assert_ne!(
            case.node_masks,
            vec![0b11],
            "{} must not use the synergy node",
            case.name
        );
        let p_law = normalized_law(&case.p_population_count_table);
        let q_law = normalized_law(&case.q_population_count_table);
        assert_eq!(
            p_law.keys().collect::<Vec<_>>(),
            q_law.keys().collect::<Vec<_>>()
        );
        let delta_l1 = p_law
            .iter()
            .map(|(key, p_mass)| p_mass.absolute_difference(q_law[key]))
            .fold(ExactFraction::from_integer(0), ExactFraction::checked_add);
        let eta = delta_l1.checked_div(ExactFraction::from_integer(2));
        assert_eq!(delta_l1, ExactFraction::new(1, 5));
        assert_eq!(eta, ExactFraction::new(1, 10));
        let p_min = ExactFraction::new(1, 2);
        assert!(p_law
            .values()
            .all(|mass| !mass.is_strictly_less_than(p_min)));
        let lambda = -(-(eta.to_f64() / p_min.to_f64())).ln_1p();
        let refined = lambda - eta.to_f64();
        assert_decimal_matches(
            lambda,
            &case.attained_lambda_nats,
            &format!("{} attained lambda", case.name),
        );
        assert_decimal_matches(
            refined,
            &case.refined_synergy_modulus_nats,
            &format!("{} false all-atom modulus", case.name),
        );

        let p_table = expand(&case.p_population_count_table);
        let (p_s1, p_s2, p_target) = p_table.refs();
        let p_result = discrete_sxpid2(p_s1, p_s2, p_target).unwrap();
        let q_table = expand(&case.q_population_count_table);
        let (q_s1, q_s2, q_target) = q_table.refs();
        let q_result = discrete_sxpid2(q_s1, q_s2, q_target).unwrap();
        assert_eq!(case.first_sources.len(), 2);
        let key = (
            case.first_sources[0],
            case.first_sources[1],
            case.first_target,
        );
        let p_point = pointwise_results(&p_result)[&key];
        let q_point = pointwise_results(&q_result)[&key];
        let p_atom = pointwise_by_node(p_point)[&case.node_masks];
        let q_atom = pointwise_by_node(q_point)[&case.node_masks];
        assert_eq!(
            case.components.len(),
            case.stored_component_changes_nats.len(),
            "{} component ledger is incomplete",
            case.name
        );
        for component in &case.components {
            let change = match component.as_str() {
                "informative" => (q_atom.informative_nats() - p_atom.informative_nats()).abs(),
                "misinformative" => {
                    (q_atom.misinformative_nats() - p_atom.misinformative_nats()).abs()
                }
                "net" => (q_atom.net_nats() - p_atom.net_nats()).abs(),
                value => panic!("{} has unknown component {value:?}", case.name),
            };
            let stored = case
                .stored_component_changes_nats
                .get(component)
                .unwrap_or_else(|| panic!("{} omitted component {component}", case.name));
            assert_decimal_matches(change, stored, &format!("{} {component} change", case.name));
            assert!(
                (change - lambda).abs() <= MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
                "{} {component} must attain lambda",
                case.name
            );
            assert!(
                change > refined + MAX_OUTPUT_ABSOLUTE_ERROR_NATS,
                "{} {component} must violate the synergy-only modulus",
                case.name
            );
        }
    }
}

#[test]
fn local_sxpid2_modulus_cases_match_oracle_and_rederived_bounds() {
    let fixture = fixture();
    assert_eq!(fixture.local_sxpid2_modulus_cases.len(), 6);
    for case in fixture.local_sxpid2_modulus_cases {
        let modulus = derive_modulus(&case);
        assert_decimal_matches(
            modulus.lambda_nats,
            &case.lambda_nats,
            &format!("{} lambda", case.name),
        );
        assert_decimal_matches(
            modulus.refined_synergy_modulus_nats,
            &case.refined_synergy_modulus_nats,
            &format!("{} refined synergy modulus", case.name),
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
        assert_decimal_matches(
            modulus.q_diamond_ceiling_nats,
            &case.q_diamond_ceiling_nats,
            &format!("{} q-law diamond ceiling", case.name),
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
            if family == AtomFamily::Synergy && case.name == "two-cell-q-component-cap" {
                assert_eq!(
                    averaged_bounds.informative.to_bits(),
                    modulus.q_diamond_ceiling_nats.to_bits(),
                    "q-law component endpoint cap must be active"
                );
                assert_eq!(
                    averaged_bounds.misinformative.to_bits(),
                    modulus.q_diamond_ceiling_nats.to_bits(),
                    "q-law component endpoint cap must be active"
                );
            }
            if family == AtomFamily::Synergy && case.name == "two-cell-q-net-cap" {
                assert_eq!(
                    averaged_bounds.net.to_bits(),
                    (modulus.diamond_ceiling_nats + modulus.q_diamond_ceiling_nats).to_bits(),
                    "q-law net endpoint cap must be active"
                );
            }
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
            let misinformative_ratio =
                maximum_synergy_pointwise_change[1] / modulus.refined_synergy_modulus_nats;
            let net_ratio =
                maximum_synergy_pointwise_change[2] / modulus.refined_synergy_modulus_nats;
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
    assert_eq!(fixture.local_sxpid2_modulus_cases.len(), 6);
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
