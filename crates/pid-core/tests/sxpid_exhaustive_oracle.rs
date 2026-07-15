//! Exhaustive two-source categorical SxPID comparison against a standalone Decimal oracle.
//!
//! The generator uses only Python's standard library and evaluates the published event-
//! probability definition directly.  This is implementation-path and arithmetic diversity on a
//! finite declared domain; it is not external review or a population-validity result.

use std::collections::BTreeMap;

use pid_core::stable::categorical::discrete_sxpid2_averaged;
use pid_core::DiscreteMatRef;
use serde::Deserialize;

const FIXTURE_BYTES: &[u8] = include_bytes!("fixtures/sxpid2_exhaustive_oracle.json");
const FIXTURE_CHECKSUM: &str = include_str!("fixtures/sxpid2_exhaustive_oracle.json.sha256");
const EXPECTED_CASES: usize = 494;
// The measured maximum on the complete corpus is one binary64 epsilon; retain a four-epsilon
// cross-platform ceiling while still rejecting even tiny formula or accumulation regressions.
const MAX_ABSOLUTE_ERROR_NATS: f64 = 4.0 * f64::EPSILON;
const STATES: [(usize, usize, usize); 8] = [
    (0, 0, 0),
    (0, 0, 1),
    (0, 1, 0),
    (0, 1, 1),
    (1, 0, 0),
    (1, 0, 1),
    (1, 1, 0),
    (1, 1, 1),
];

#[derive(Deserialize)]
struct Fixture {
    bounds: Bounds,
    cases: Vec<OracleCase>,
}

#[derive(Deserialize)]
struct Bounds {
    case_count: usize,
    max_total_samples: usize,
    state_order: Vec<[usize; 3]>,
}

#[derive(Deserialize)]
struct OracleCase {
    atoms: BTreeMap<String, OracleAtom>,
    counts: Vec<usize>,
    mutual_information: OracleMutualInformation,
    total_samples: usize,
}

#[derive(Deserialize)]
struct OracleAtom {
    informative: String,
    misinformative: String,
    net: String,
}

#[derive(Deserialize)]
struct OracleMutualInformation {
    source_one_target: String,
    source_two_target: String,
    joint_sources_target: String,
}

fn expected(value: &str) -> f64 {
    value
        .parse::<f64>()
        .expect("oracle Decimal must be representable as finite f64")
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

#[test]
fn all_binary_count_tables_through_four_samples_match_standalone_decimal_oracle() {
    let expected_hash = FIXTURE_CHECKSUM
        .split_whitespace()
        .next()
        .expect("oracle fixture checksum must contain a SHA-256 digest");
    assert_eq!(
        pid_runlog::sha256_hex(FIXTURE_BYTES),
        expected_hash,
        "oracle fixture does not match its committed SHA-256 digest"
    );

    let fixture: Fixture =
        serde_json::from_slice(FIXTURE_BYTES).expect("oracle fixture must contain valid JSON");
    assert_eq!(fixture.bounds.case_count, EXPECTED_CASES);
    assert_eq!(fixture.cases.len(), EXPECTED_CASES);
    assert_eq!(fixture.bounds.max_total_samples, 4);
    assert_eq!(
        fixture.bounds.state_order,
        STATES.map(|(source_one, source_two, target)| [source_one, source_two, target])
    );

    let mut maximum_error = 0.0_f64;
    let mut worst = String::new();
    for (case_index, case) in fixture.cases.iter().enumerate() {
        assert_eq!(case.counts.len(), STATES.len());
        assert_eq!(case.counts.iter().sum::<usize>(), case.total_samples);
        let mut source_one = Vec::with_capacity(case.total_samples);
        let mut source_two = Vec::with_capacity(case.total_samples);
        let mut target = Vec::with_capacity(case.total_samples);
        for (&count, &(one, two, outcome)) in case.counts.iter().zip(&STATES) {
            source_one.extend(std::iter::repeat_n(one, count));
            source_two.extend(std::iter::repeat_n(two, count));
            target.extend(std::iter::repeat_n(outcome, count));
        }

        let result = discrete_sxpid2_averaged(
            DiscreteMatRef::new(&source_one, case.total_samples, 1).unwrap(),
            DiscreteMatRef::new(&source_two, case.total_samples, 1).unwrap(),
            DiscreteMatRef::new(&target, case.total_samples, 1).unwrap(),
        )
        .unwrap();

        for (name, actual) in [
            ("unique_one", result.unq1),
            ("unique_two", result.unq2),
            ("synergy", result.syn),
            ("redundancy", result.red),
        ] {
            let oracle = &case.atoms[name];
            record_error(
                &mut maximum_error,
                &mut worst,
                &format!("case {case_index} {name}.informative"),
                actual.informative,
                expected(&oracle.informative),
            );
            record_error(
                &mut maximum_error,
                &mut worst,
                &format!("case {case_index} {name}.misinformative"),
                actual.misinformative,
                expected(&oracle.misinformative),
            );
            record_error(
                &mut maximum_error,
                &mut worst,
                &format!("case {case_index} {name}.net"),
                actual.net,
                expected(&oracle.net),
            );
        }
        for (label, actual, oracle) in [
            (
                "I(source_one;target)",
                result.mi_s1_t,
                &case.mutual_information.source_one_target,
            ),
            (
                "I(source_two;target)",
                result.mi_s2_t,
                &case.mutual_information.source_two_target,
            ),
            (
                "I(source_one,source_two;target)",
                result.mi_s1s2_t,
                &case.mutual_information.joint_sources_target,
            ),
        ] {
            record_error(
                &mut maximum_error,
                &mut worst,
                &format!("case {case_index} {label}"),
                actual,
                expected(oracle),
            );
        }
    }

    assert!(
        maximum_error <= MAX_ABSOLUTE_ERROR_NATS,
        "maximum absolute error {maximum_error:.17e} nats exceeds the declared bound \
         {MAX_ABSOLUTE_ERROR_NATS:.17e}; worst comparison: {worst}"
    );
}
