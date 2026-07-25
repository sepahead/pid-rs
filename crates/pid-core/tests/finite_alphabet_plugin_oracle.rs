//! Bounded finite-alphabet comparison with an independent high-precision oracle.
//!
//! The fixture generator uses Python standard-library Decimal arithmetic and direct definitions.
//! These tests give software evidence on listed empirical count tables. They do not prove an
//! asymptotic theorem or establish population validity.

use std::collections::BTreeMap;
use std::io::ErrorKind;
use std::path::Path;

use pid_core::stable::categorical::{
    discrete_sxpid2_averaged, discrete_sxpid_n, discrete_sxpid_n_averaged, DiscreteSxPid2Result,
    DiscreteSxPidNResult, SxAveragedAtom,
};
use pid_core::stable::imin::{imin_pid2, imin_pid2_quantized, imin_pid3};
use pid_core::stable::quantized::{
    fitted_quantized_sxpid2, EqualWidthQuantizer, OutOfRangePolicy, QuantizerConfig,
};
use pid_core::{DiscreteMatRef, MatRef, PidError, ResourceBudget};
use serde::Deserialize;

const FIXTURE_BYTES: &[u8] = include_bytes!("fixtures/finite_alphabet_plugin_oracle.json");
const FIXTURE_CHECKSUM: &str = include_str!("fixtures/finite_alphabet_plugin_oracle.json.sha256");
const GENERATOR_BYTES: &[u8] =
    include_bytes!("fixtures/generators/generate-finite-alphabet-plugin-oracle.py");
const REPOSITORY_GENERATOR_PATH: &str = "../../scripts/generate-finite-alphabet-plugin-oracle.py";
const EXPECTED_SXPID_LATTICE_SIZES: [(usize, usize); 3] = [(2, 4), (3, 18), (4, 166)];
// Retain a 64-epsilon envelope for libm variation and cancellation in the 166-node inversion.
// This bound applies only to the committed fixture. It is not a universal binary64 error theorem.
const MAX_ABSOLUTE_ERROR_NATS: f64 = 64.0 * f64::EPSILON;

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
#[serde(deny_unknown_fields)]
struct Fixture {
    arithmetic: Arithmetic,
    claim_scope: String,
    generator: Generator,
    imin_cases: Vec<IminCase>,
    imin_minimum_tie_crossing: Vec<IminTieCase>,
    limitations: Vec<String>,
    method_scope: BTreeMap<String, MethodScope>,
    pointwise_fixed_face_case: PointwiseFixedFaceCase,
    schema: String,
    schema_revision: usize,
    sxpid_cases: Vec<SxCase>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Arithmetic {
    decimal_precision_digits: usize,
    logarithm: String,
    probability_source: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Generator {
    imports_pid_rs: bool,
    path: String,
    sha256: String,
    third_party_dependencies: Vec<String>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct MethodScope {
    #[serde(default)]
    composition_kind: Option<String>,
    definition_status: String,
    defining_reference: Option<String>,
    tested_code: Vec<String>,
}

#[derive(Deserialize)]
struct CountedState {
    count: usize,
    realization: Vec<usize>,
}

#[derive(Deserialize)]
struct ExpectedSxAtom {
    informative: String,
    misinformative: String,
    net: String,
    sets: Vec<u8>,
}

#[derive(Deserialize)]
struct ExpectedPointwise {
    atoms: Vec<ExpectedSxAtom>,
    count: usize,
    realization: Vec<usize>,
}

#[derive(Deserialize)]
struct SxCase {
    atoms: Vec<ExpectedSxAtom>,
    name: String,
    #[serde(default)]
    pointwise: Vec<ExpectedPointwise>,
    source_count: usize,
    states: Vec<CountedState>,
}

#[derive(Deserialize)]
struct PointwiseFixedFaceCase {
    fixed_face: SxCase,
    late_rare_realization: Vec<usize>,
    with_late_rare: SxCase,
}

#[derive(Deserialize)]
struct ExpectedIminNode {
    atom: String,
    redundancy: String,
    sets: Vec<u8>,
}

#[derive(Deserialize)]
struct IminCase {
    lattice: Vec<ExpectedIminNode>,
    name: String,
    source_count: usize,
    states: Vec<CountedState>,
}

#[derive(Deserialize)]
struct ExpectedSpecificInformation {
    source_mask: u8,
    value: String,
}

#[derive(Deserialize)]
struct IminTieCase {
    #[serde(flatten)]
    case: IminCase,
    crossing_target: usize,
    minimizer_masks: Vec<u8>,
    specific_information: Vec<ExpectedSpecificInformation>,
}

struct ExpandedTable {
    sources: Vec<Vec<usize>>,
    target: Vec<usize>,
}

impl ExpandedTable {
    fn rows(&self) -> usize {
        self.target.len()
    }

    fn source_refs(&self) -> Vec<DiscreteMatRef<'_>> {
        self.sources
            .iter()
            .map(|source| DiscreteMatRef::new(source, self.rows(), 1).unwrap())
            .collect()
    }

    fn target_ref(&self) -> DiscreteMatRef<'_> {
        DiscreteMatRef::new(&self.target, self.rows(), 1).unwrap()
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
        "finite-alphabet fixture does not match its committed SHA-256 digest"
    );
    serde_json::from_slice(FIXTURE_BYTES).expect("finite-alphabet fixture must contain valid JSON")
}

fn expected(value: &str) -> f64 {
    let parsed = value
        .parse::<f64>()
        .expect("oracle Decimal must be representable as f64");
    assert!(
        parsed.is_finite(),
        "oracle Decimal must parse as finite f64"
    );
    parsed
}

fn expand(states: &[CountedState], source_count: usize) -> ExpandedTable {
    let total = states.iter().map(|state| state.count).sum();
    let mut sources: Vec<Vec<usize>> = (0..source_count)
        .map(|_| Vec::with_capacity(total))
        .collect();
    let mut target = Vec::with_capacity(total);
    for state in states {
        assert_eq!(state.realization.len(), source_count + 1);
        assert!(state.count > 0);
        for _ in 0..state.count {
            for (source, values) in sources.iter_mut().enumerate() {
                values.push(state.realization[source]);
            }
            target.push(state.realization[source_count]);
        }
    }
    ExpandedTable { sources, target }
}

fn record_error(maximum: &mut f64, worst: &mut String, label: &str, actual: f64, expected: f64) {
    let error = if actual.is_finite() && expected.is_finite() {
        (actual - expected).abs()
    } else {
        f64::INFINITY
    };
    if error > *maximum {
        *maximum = error;
        *worst = format!("{label}: actual={actual:.17e}, expected={expected:.17e}");
    }
}

fn record_sx_atom_error(
    maximum: &mut f64,
    worst: &mut String,
    label: &str,
    actual: SxAveragedAtom,
    oracle: &ExpectedSxAtom,
) {
    for (component, actual_value, expected_value) in [
        (
            "informative",
            actual.informative_nats(),
            expected(&oracle.informative),
        ),
        (
            "misinformative",
            actual.misinformative_nats(),
            expected(&oracle.misinformative),
        ),
        ("net", actual.net_nats(), expected(&oracle.net)),
    ] {
        record_error(
            maximum,
            worst,
            &format!("{label} {component} {:?}", oracle.sets),
            actual_value,
            expected_value,
        );
    }
}

fn compare_averaged_sxpid(
    case: &SxCase,
    result: &DiscreteSxPidNResult,
    maximum: &mut f64,
    worst: &mut String,
) {
    assert_eq!(result.n_sources, case.source_count);
    assert_eq!(result.antichains.len(), case.atoms.len());
    for oracle in &case.atoms {
        let index = result
            .antichains
            .iter()
            .position(|sets| sets == &oracle.sets)
            .unwrap_or_else(|| panic!("{} omitted SxPID node {:?}", case.name, oracle.sets));
        record_sx_atom_error(maximum, worst, &case.name, result.atoms[index], oracle);
    }
}

fn pointwise_key(realization: &[Vec<usize>]) -> Vec<usize> {
    realization
        .iter()
        .map(|variable| {
            assert_eq!(variable.len(), 1);
            variable[0]
        })
        .collect()
}

fn compare_pointwise_sxpid(
    case: &SxCase,
    result: &DiscreteSxPidNResult,
    maximum: &mut f64,
    worst: &mut String,
) {
    let actual_by_key: BTreeMap<Vec<usize>, _> = result
        .pointwise
        .iter()
        .map(|point| (pointwise_key(&point.realization), point))
        .collect();
    assert_eq!(actual_by_key.len(), case.pointwise.len());

    for oracle_point in &case.pointwise {
        let actual_point = actual_by_key
            .get(&oracle_point.realization)
            .unwrap_or_else(|| {
                panic!(
                    "{} omitted pointwise realization {:?}",
                    case.name, oracle_point.realization
                )
            });
        assert_eq!(actual_point.empirical_count, oracle_point.count);
        for oracle_atom in &oracle_point.atoms {
            let index = result
                .antichains
                .iter()
                .position(|sets| sets == &oracle_atom.sets)
                .unwrap();
            let actual_atom = actual_point.atoms[index];
            for (component, actual_value, expected_value) in [
                (
                    "informative",
                    actual_atom.informative_nats(),
                    expected(&oracle_atom.informative),
                ),
                (
                    "misinformative",
                    actual_atom.misinformative_nats(),
                    expected(&oracle_atom.misinformative),
                ),
                ("net", actual_atom.net_nats(), expected(&oracle_atom.net)),
            ] {
                record_error(
                    maximum,
                    worst,
                    &format!(
                        "{} pointwise {:?} {component} {:?}",
                        case.name, oracle_point.realization, oracle_atom.sets
                    ),
                    actual_value,
                    expected_value,
                );
            }
        }
    }
}

fn evaluate_sxpid(case: &SxCase, include_pointwise: bool) -> DiscreteSxPidNResult {
    let table = expand(&case.states, case.source_count);
    if include_pointwise {
        discrete_sxpid_n(&table.source_refs(), table.target_ref()).unwrap()
    } else {
        discrete_sxpid_n_averaged(&table.source_refs(), table.target_ref()).unwrap()
    }
}

fn evaluate_imin(case: &IminCase) -> BTreeMap<Vec<u8>, (f64, f64)> {
    let table = expand(&case.states, case.source_count);
    let sources = table.source_refs();
    match case.source_count {
        2 => {
            let result = imin_pid2(sources[0], sources[1], table.target_ref()).unwrap();
            BTreeMap::from([
                (vec![0b01], (result.mi_s1_t, result.unique_s1)),
                (vec![0b10], (result.mi_s2_t, result.unique_s2)),
                (vec![0b11], (result.mi_s1s2_t, result.synergy)),
                (vec![0b01, 0b10], (result.redundancy, result.redundancy)),
            ])
        }
        3 => {
            let result = imin_pid3(sources[0], sources[1], sources[2], table.target_ref()).unwrap();
            result
                .atoms
                .iter()
                .zip(&result.redundancies)
                .map(|(atom, &redundancy)| (atom.antichain_sets.clone(), (redundancy, atom.value)))
                .collect()
        }
        _ => panic!("unsupported oracle I_min source count"),
    }
}

fn compare_imin_case(case: &IminCase, maximum: &mut f64, worst: &mut String) {
    let actual = evaluate_imin(case);
    assert_eq!(actual.len(), case.lattice.len());
    for node in &case.lattice {
        let &(redundancy, atom) = actual
            .get(&node.sets)
            .unwrap_or_else(|| panic!("{} omitted I_min node {:?}", case.name, node.sets));
        record_error(
            maximum,
            worst,
            &format!("{} redundancy {:?}", case.name, node.sets),
            redundancy,
            expected(&node.redundancy),
        );
        record_error(
            maximum,
            worst,
            &format!("{} atom {:?}", case.name, node.sets),
            atom,
            expected(&node.atom),
        );
    }
}

#[test]
fn sxpid_two_through_four_sources_match_decimal_event_probability_oracle() {
    let fixture = fixture();
    assert_eq!(fixture.arithmetic.decimal_precision_digits, 100);
    assert_eq!(fixture.arithmetic.logarithm, "natural");
    assert_eq!(
        fixture.arithmetic.probability_source,
        "exact positive integer empirical counts"
    );
    assert_eq!(
        fixture.claim_scope,
        "bounded software agreement; not an asymptotic proof"
    );
    assert!(!fixture.generator.imports_pid_rs);
    assert_eq!(
        fixture.generator.path,
        "scripts/generate-finite-alphabet-plugin-oracle.py"
    );
    assert_repository_generator_matches_packaged_mirror();
    assert_eq!(
        fixture.generator.sha256,
        pid_runlog::sha256_hex(GENERATOR_BYTES),
        "fixture generator identity is stale"
    );
    assert!(fixture.generator.third_party_dependencies.is_empty());
    let limitations: Vec<_> = fixture.limitations.iter().map(String::as_str).collect();
    assert_eq!(
        limitations,
        [
            "the fixture covers only the listed finite empirical count tables",
            "agreement does not prove an asymptotic convergence theorem",
            "implementation-path independence is not external review",
            "binary64 comparisons include a stated rounding envelope",
            "an absent realization has no canonical pointwise atom in this fixture",
            "fitted quantizer wrapper checks are software-composition checks, not population claims",
        ]
    );
    assert_eq!(fixture.schema, "pid-rs/finite-alphabet-plugin-oracle");
    assert_eq!(fixture.schema_revision, 1);
    assert_eq!(fixture.method_scope.len(), 3);
    assert_eq!(
        fixture.method_scope["categorical_sxpid"].definition_status,
        "paper-defined"
    );
    assert!(fixture.method_scope["categorical_sxpid"]
        .defining_reference
        .as_deref()
        .unwrap()
        .starts_with("https://doi.org/"));
    assert_eq!(
        fixture.method_scope["categorical_sxpid"].tested_code,
        [
            "pid_core::stable::categorical::discrete_sxpid_n",
            "pid_core::stable::categorical::discrete_sxpid_n_averaged",
        ]
    );
    assert_eq!(
        fixture.method_scope["categorical_imin"].definition_status,
        "paper-defined"
    );
    assert_eq!(
        fixture.method_scope["categorical_imin"]
            .defining_reference
            .as_deref(),
        Some("https://arxiv.org/abs/1004.2515")
    );
    assert_eq!(
        fixture.method_scope["categorical_imin"].tested_code,
        [
            "pid_core::stable::imin::imin_pid2",
            "pid_core::stable::imin::imin_pid3",
        ]
    );
    assert_eq!(
        fixture.method_scope["fitted_quantizer_wrappers"].definition_status,
        "project-defined"
    );
    assert_eq!(
        fixture.method_scope["fitted_quantizer_wrappers"]
            .composition_kind
            .as_deref(),
        Some("fitted quantizer plus categorical functional")
    );
    assert!(fixture.method_scope["fitted_quantizer_wrappers"]
        .defining_reference
        .is_none());
    assert_eq!(
        fixture.method_scope["fitted_quantizer_wrappers"].tested_code,
        [
            "pid_core::stable::quantized::fitted_quantized_sxpid2",
            "pid_core::stable::imin::imin_pid2_quantized",
        ]
    );
    assert_eq!(fixture.sxpid_cases.len(), 3);

    let mut maximum_error = 0.0;
    let mut worst = String::new();
    for (case, &(source_count, lattice_size)) in fixture
        .sxpid_cases
        .iter()
        .zip(&EXPECTED_SXPID_LATTICE_SIZES)
    {
        assert_eq!(case.source_count, source_count);
        assert_eq!(case.atoms.len(), lattice_size);
        let result = evaluate_sxpid(case, false);
        compare_averaged_sxpid(case, &result, &mut maximum_error, &mut worst);
    }
    assert!(
        maximum_error <= MAX_ABSOLUTE_ERROR_NATS,
        "maximum SxPID error {maximum_error:.17e} exceeded {MAX_ABSOLUTE_ERROR_NATS:.17e}; {worst}"
    );
}

#[test]
fn pointwise_atoms_use_realization_keys_and_exclude_an_absent_fixed_face_realization() {
    let fixture = fixture();
    let face = fixture.pointwise_fixed_face_case;
    assert_eq!(
        face.with_late_rare.states.last().unwrap().realization,
        face.late_rare_realization,
        "rare realization must be appended after every common input state"
    );

    let with_rare = evaluate_sxpid(&face.with_late_rare, true);
    let fixed_face = evaluate_sxpid(&face.fixed_face, true);
    let mut maximum_error = 0.0;
    let mut worst = String::new();
    compare_pointwise_sxpid(
        &face.with_late_rare,
        &with_rare,
        &mut maximum_error,
        &mut worst,
    );
    compare_pointwise_sxpid(
        &face.fixed_face,
        &fixed_face,
        &mut maximum_error,
        &mut worst,
    );

    let with_keys: Vec<_> = with_rare
        .pointwise
        .iter()
        .map(|point| pointwise_key(&point.realization))
        .collect();
    let face_keys: Vec<_> = fixed_face
        .pointwise
        .iter()
        .map(|point| pointwise_key(&point.realization))
        .collect();
    assert_eq!(with_keys.first().unwrap(), &face.late_rare_realization);
    assert_eq!(&with_keys[1..], face_keys.as_slice());
    assert!(!face_keys.contains(&face.late_rare_realization));
    assert!(
        maximum_error <= MAX_ABSOLUTE_ERROR_NATS,
        "maximum pointwise error {maximum_error:.17e} exceeded {MAX_ABSOLUTE_ERROR_NATS:.17e}; {worst}"
    );
}

#[test]
fn imin_two_and_three_sources_match_decimal_specific_information_oracle() {
    let fixture = fixture();
    assert_eq!(fixture.imin_cases.len(), 2);
    let mut maximum_error = 0.0;
    let mut worst = String::new();
    for case in &fixture.imin_cases {
        compare_imin_case(case, &mut maximum_error, &mut worst);
    }
    assert!(
        maximum_error <= MAX_ABSOLUTE_ERROR_NATS,
        "maximum I_min error {maximum_error:.17e} exceeded {MAX_ABSOLUTE_ERROR_NATS:.17e}; {worst}"
    );
}

#[test]
fn imin_minimum_switches_sides_through_an_exact_tie() {
    let fixture = fixture();
    let crossing = fixture.imin_minimum_tie_crossing;
    assert_eq!(crossing.len(), 6);
    assert!(crossing.iter().all(|case| case.crossing_target == 0));

    let mut maximum_error = 0.0;
    let mut worst = String::new();
    for (source_count, series) in [(2, &crossing[..3]), (3, &crossing[3..])] {
        assert!(series
            .iter()
            .all(|case| case.case.source_count == source_count));
        assert_eq!(series[0].minimizer_masks, [0b01]);
        assert_eq!(series[1].minimizer_masks, [0b01, 0b10]);
        assert_eq!(series[2].minimizer_masks, [0b10]);

        let middle_specific: BTreeMap<_, _> = series[1]
            .specific_information
            .iter()
            .map(|entry| (entry.source_mask, expected(&entry.value)))
            .collect();
        assert!(middle_specific[&0b01] > 0.0);
        assert!(middle_specific[&0b10] > 0.0);
        assert_eq!(
            middle_specific[&0b01].to_bits(),
            middle_specific[&0b10].to_bits(),
            "the Decimal tie must remain exact after binary64 parsing"
        );
        for case in series {
            compare_imin_case(&case.case, &mut maximum_error, &mut worst);
        }
    }
    assert!(
        maximum_error <= MAX_ABSOLUTE_ERROR_NATS,
        "maximum tie-crossing error {maximum_error:.17e} exceeded {MAX_ABSOLUTE_ERROR_NATS:.17e}; {worst}"
    );
}

fn quantizer(training: &[f64], policy: OutOfRangePolicy) -> EqualWidthQuantizer {
    let config = QuantizerConfig::new(
        policy,
        true,
        2,
        "separate fixed training range",
        ResourceBudget::default(),
    )
    .unwrap();
    EqualWidthQuantizer::fit(MatRef::new(training, training.len(), 1).unwrap(), 2, config).unwrap()
}

fn assert_same_sxpid2_numerics(left: &DiscreteSxPid2Result, right: &DiscreteSxPid2Result) {
    for (left_atom, right_atom) in [
        (left.unq1, right.unq1),
        (left.unq2, right.unq2),
        (left.syn, right.syn),
        (left.red, right.red),
    ] {
        assert_eq!(
            left_atom.informative_nats().to_bits(),
            right_atom.informative_nats().to_bits()
        );
        assert_eq!(
            left_atom.misinformative_nats().to_bits(),
            right_atom.misinformative_nats().to_bits()
        );
        assert_eq!(
            left_atom.net_nats().to_bits(),
            right_atom.net_nats().to_bits()
        );
    }
    assert_eq!(left.mi_s1_t.to_bits(), right.mi_s1_t.to_bits());
    assert_eq!(left.mi_s2_t.to_bits(), right.mi_s2_t.to_bits());
    assert_eq!(left.mi_s1s2_t.to_bits(), right.mi_s1s2_t.to_bits());
}

fn check_fixed_quantizer_composition(
    policy: OutOfRangePolicy,
    source_one_values: &[f64],
    source_two_values: &[f64],
    target_values: &[f64],
) {
    let source_one_quantizer = quantizer(&[-2.0, -1.0, 0.0, 1.0], policy);
    let source_two_quantizer = quantizer(&[10.0, 12.0, 14.0, 16.0], policy);
    let target_quantizer = quantizer(&[100.0, 200.0, 300.0, 400.0], policy);
    let rows = target_values.len();
    assert_eq!(source_one_values.len(), rows);
    assert_eq!(source_two_values.len(), rows);

    let source_one = source_one_quantizer
        .transform_with_report(MatRef::new(source_one_values, rows, 1).unwrap())
        .unwrap();
    let source_two = source_two_quantizer
        .transform_with_report(MatRef::new(source_two_values, rows, 1).unwrap())
        .unwrap();
    let target = target_quantizer
        .transform_with_report(MatRef::new(target_values, rows, 1).unwrap())
        .unwrap();

    let categorical_sxpid = discrete_sxpid2_averaged(
        source_one.matrix.as_ref(),
        source_two.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let wrapped_sxpid = fitted_quantized_sxpid2(&source_one, &source_two, &target).unwrap();
    assert_same_sxpid2_numerics(&wrapped_sxpid.pid, &categorical_sxpid);

    let categorical_imin = imin_pid2(
        source_one.matrix.as_ref(),
        source_two.matrix.as_ref(),
        target.matrix.as_ref(),
    )
    .unwrap();
    let wrapped_imin = imin_pid2_quantized(&source_one, &source_two, &target).unwrap();
    for (wrapped, categorical) in [
        (wrapped_imin.redundancy, categorical_imin.redundancy),
        (wrapped_imin.unique_s1, categorical_imin.unique_s1),
        (wrapped_imin.unique_s2, categorical_imin.unique_s2),
        (wrapped_imin.synergy, categorical_imin.synergy),
        (wrapped_imin.mi_s1_t, categorical_imin.mi_s1_t),
        (wrapped_imin.mi_s2_t, categorical_imin.mi_s2_t),
        (wrapped_imin.mi_s1s2_t, categorical_imin.mi_s1s2_t),
    ] {
        assert_eq!(wrapped.to_bits(), categorical.to_bits());
    }

    if policy == OutOfRangePolicy::ClampToBoundary {
        assert_eq!(source_one.matrix.data().first(), Some(&0));
        assert_eq!(source_one.matrix.data().last(), Some(&1));
        assert_eq!(source_two.matrix.data().first(), Some(&0));
        assert_eq!(source_two.matrix.data().last(), Some(&1));
        assert_eq!(target.matrix.data().first(), Some(&0));
        assert_eq!(target.matrix.data().get(4), Some(&1));
    }
}

#[test]
fn separately_fitted_quantizer_wrappers_equal_direct_categorical_evaluation() {
    check_fixed_quantizer_composition(
        OutOfRangePolicy::Error,
        &[-2.0, -1.0, -0.5, 0.0, 1.0, -2.0, -0.5, 1.0],
        &[10.0, 14.0, 12.0, 16.0, 10.0, 16.0, 13.0, 13.0],
        &[100.0, 400.0, 100.0, 400.0, 400.0, 100.0, 400.0, 100.0],
    );

    let error_quantizer = quantizer(&[-2.0, -1.0, 0.0, 1.0], OutOfRangePolicy::Error);
    for value in [-2.000_001, 1.000_001] {
        assert!(matches!(
            error_quantizer.transform_with_report(MatRef::new(&[value], 1, 1).unwrap()),
            Err(PidError::QuantizerOutOfRange { column: 0, .. })
        ));
    }

    check_fixed_quantizer_composition(
        OutOfRangePolicy::ClampToBoundary,
        &[-20.0, -2.0, -0.5, 1.0, 20.0, -1.0, 0.0, 2.0],
        &[-20.0, 10.0, 13.0, 16.0, 20.0, 12.0, 14.0, 30.0],
        &[0.0, 100.0, 250.0, 400.0, 500.0, 200.0, 300.0, 100.0],
    );
}
