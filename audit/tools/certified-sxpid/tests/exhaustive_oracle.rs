//! Exhaustive interval agreement against the independent standard-library Decimal oracle.
//!
//! The fixture generator evaluates the published two-source event definition directly and does
//! not import either `pid-core` or this certifier. This is bounded implementation-path and
//! arithmetic diversity, not a proof of the general implementation or a population theorem. Each
//! comparison requires the certified enclosure to overlap a decimal-oracle tolerance interval; it
//! does not claim that the finite Decimal value is itself a rigorous enclosure.

use std::collections::BTreeMap;
use std::str::FromStr;

use pid_certified_sxpid::certify_sxpid2;
use rug::{Integer, Rational};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const FIXTURE_BYTES: &[u8] =
    include_bytes!("../../../../crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json");
const FIXTURE_SIDECAR: &str =
    include_str!("../../../../crates/pid-core/tests/fixtures/sxpid2_exhaustive_oracle.json.sha256");
const GENERATOR_BYTES: &[u8] =
    include_bytes!("../../../../scripts/generate-sxpid2-exhaustive-oracle.py");
const EXPECTED_FIXTURE_SHA256: &str =
    "29c72afd551b446a5141ca54b25608386616d46572bf385bab94c9b56c14342d";
const EXPECTED_GENERATOR_SHA256: &str =
    "184404dddf0a1dac8caeecfb445036b2c73f02d303e2f88152dc17b485ea50cc";
const EXPECTED_CASES: usize = 494;
const ORACLE_DECIMAL_TOLERANCE_DIGITS: u32 = 70;
const STATES: [(u8, u8, u8); 8] = [
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
    generator: GeneratorEvidence,
}

#[derive(Deserialize)]
struct Bounds {
    case_count: usize,
    max_total_samples: usize,
    state_order: Vec<[u8; 3]>,
}

#[derive(Deserialize)]
struct OracleCase {
    atoms: BTreeMap<String, OracleCoordinate>,
    counts: Vec<usize>,
    cumulatives: BTreeMap<String, OracleCoordinate>,
    mutual_information: OracleMutualInformation,
    total_samples: usize,
}

#[derive(Deserialize)]
struct OracleCoordinate {
    informative: String,
    misinformative: String,
    net: String,
}

#[derive(Deserialize)]
struct GeneratorEvidence {
    imports_pid_rs: bool,
    path: String,
    sha256: String,
    third_party_dependencies: Vec<String>,
}

#[derive(Deserialize)]
struct OracleMutualInformation {
    source_one_target: String,
    source_two_target: String,
    joint_sources_target: String,
}

#[test]
fn all_494_binary_count_tables_cover_every_coordinate_and_direct_mi_identity() {
    assert_fixture_digest();
    let fixture: Fixture =
        serde_json::from_slice(FIXTURE_BYTES).expect("fixture must contain valid JSON");
    assert_generator_evidence(&fixture.generator);
    assert_eq!(fixture.bounds.case_count, EXPECTED_CASES);
    assert_eq!(fixture.cases.len(), EXPECTED_CASES);
    assert_eq!(fixture.bounds.max_total_samples, 4);
    assert_eq!(
        fixture.bounds.state_order,
        STATES.map(|(one, two, target)| [one, two, target])
    );

    let mut coordinate_comparisons = 0usize;
    let mut direct_mi_comparisons = 0usize;
    for (case_index, case) in fixture.cases.iter().enumerate() {
        assert_eq!(case.counts.len(), STATES.len());
        assert_eq!(case.counts.iter().sum::<usize>(), case.total_samples);
        let input = canonical_input(case);
        let certificate = certify_sxpid2(&input).expect("bounded table must certify");
        let report = serde_json::to_value(certificate).expect("certificate must serialize");

        for (kind, coordinates) in [("atom", &case.atoms), ("cumulative", &case.cumulatives)] {
            assert_eq!(coordinates.len(), 4);
            for (node, coordinate) in coordinates {
                for (component, expected) in [
                    ("informative", &coordinate.informative),
                    ("misinformative", &coordinate.misinformative),
                    ("net", &coordinate.net),
                ] {
                    assert_overlaps_oracle_tolerance(
                        &report, kind, node, component, expected, case_index,
                    );
                    coordinate_comparisons += 1;
                }
            }
        }
        for (node, expected) in [
            ("source_one", &case.mutual_information.source_one_target),
            ("source_two", &case.mutual_information.source_two_target),
            (
                "joint_sources",
                &case.mutual_information.joint_sources_target,
            ),
        ] {
            assert_overlaps_oracle_tolerance(
                &report,
                "cumulative",
                node,
                "net",
                expected,
                case_index,
            );
            direct_mi_comparisons += 1;
        }
    }
    assert_eq!(coordinate_comparisons, EXPECTED_CASES * 24);
    assert_eq!(direct_mi_comparisons, EXPECTED_CASES * 3);
}

fn assert_fixture_digest() {
    let sidecar = FIXTURE_SIDECAR
        .split_whitespace()
        .next()
        .expect("fixture sidecar must contain a digest");
    let actual = lower_hex(&Sha256::digest(FIXTURE_BYTES));
    assert_eq!(
        sidecar, EXPECTED_FIXTURE_SHA256,
        "fixture sidecar drifted from the reviewed literal"
    );
    assert_eq!(
        actual, EXPECTED_FIXTURE_SHA256,
        "fixture bytes drifted from the reviewed literal"
    );
}

fn assert_generator_evidence(generator: &GeneratorEvidence) {
    assert!(!generator.imports_pid_rs);
    assert_eq!(
        generator.path,
        "scripts/generate-sxpid2-exhaustive-oracle.py"
    );
    assert!(generator.third_party_dependencies.is_empty());
    assert_eq!(
        generator.sha256, EXPECTED_GENERATOR_SHA256,
        "fixture generator digest drifted from the reviewed literal"
    );
    assert_eq!(
        lower_hex(&Sha256::digest(GENERATOR_BYTES)),
        EXPECTED_GENERATOR_SHA256,
        "generator bytes drifted from the reviewed literal"
    );
}

fn canonical_input(case: &OracleCase) -> Vec<u8> {
    let rows = STATES
        .iter()
        .zip(&case.counts)
        .filter(|(_, count)| **count > 0)
        .map(|(&(one, two, target), count)| {
            json!({
                "source_states": [[one.to_string()], [two.to_string()]],
                "target_state": [target.to_string()],
                "count": count.to_string()
            })
        })
        .collect::<Vec<_>>();
    serde_json::to_vec(&json!({
        "schema": "pid-rs/categorical-sxpid2-count-table/v1",
        "definition_revision": "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1",
        "units": "nats",
        "resource_policy_id": "sxpid2-certification-default-v1",
        "rows": rows
    }))
    .expect("canonical test input must serialize")
}

fn assert_overlaps_oracle_tolerance(
    report: &Value,
    kind: &str,
    node: &str,
    component: &str,
    expected_decimal: &str,
    case_index: usize,
) {
    let coordinates = report["payload"]["coordinates"]
        .as_array()
        .expect("report must contain coordinate array");
    let coordinate = coordinates
        .iter()
        .find(|coordinate| {
            coordinate["identity"]["kind"] == kind
                && coordinate["identity"]["node"] == node
                && coordinate["identity"]["component"] == component
        })
        .expect("requested coordinate must be present");
    let lower = parse_dyadic(&coordinate["interval"]["lower"]);
    let upper = parse_dyadic(&coordinate["interval"]["upper"]);
    let expected = parse_decimal_rational(expected_decimal);
    let tolerance = Rational::from((
        Integer::from(1),
        power_of_ten(ORACLE_DECIMAL_TOLERANCE_DIGITS),
    ));
    let oracle_lower = expected.clone() - &tolerance;
    let oracle_upper = expected + tolerance;
    assert!(
        lower <= oracle_upper && oracle_lower <= upper,
        "case {case_index} {kind}/{node}/{component}: the Decimal oracle tolerance interval \
         around {expected_decimal} is disjoint from [{lower}, {upper}]"
    );
}

fn parse_dyadic(value: &Value) -> Rational {
    let significand = Integer::from_str(
        value["significand"]
            .as_str()
            .expect("dyadic significand must be a string"),
    )
    .expect("dyadic significand must be an integer");
    let exponent = value["exponent2"]
        .as_i64()
        .expect("dyadic exponent must be an integer");
    if exponent >= 0 {
        Rational::from(significand << u32::try_from(exponent).expect("bounded exponent"))
    } else {
        Rational::from((
            significand,
            Integer::from(1) << u32::try_from(-exponent).expect("bounded exponent"),
        ))
    }
}

fn parse_decimal_rational(text: &str) -> Rational {
    let (mantissa, exponent10) = match text.find(['e', 'E']) {
        Some(index) => (
            &text[..index],
            text[index + 1..]
                .parse::<i32>()
                .expect("oracle exponent must be a signed decimal integer"),
        ),
        None => (text, 0),
    };
    let negative = mantissa.starts_with('-');
    let unsigned = mantissa.strip_prefix(['-', '+']).unwrap_or(mantissa);
    let (whole, fractional) = unsigned.split_once('.').unwrap_or((unsigned, ""));
    let digits = format!("{whole}{fractional}");
    let mut integer = Integer::from_str(if digits.is_empty() { "0" } else { &digits })
        .expect("oracle mantissa must contain decimal digits");
    if negative {
        integer = -integer;
    }
    let scale = i32::try_from(fractional.len()).expect("oracle scale must fit i32") - exponent10;
    if scale <= 0 {
        Rational::from(integer * power_of_ten(scale.unsigned_abs()))
    } else {
        Rational::from((integer, power_of_ten(scale.unsigned_abs())))
    }
}

fn power_of_ten(exponent: u32) -> Integer {
    let mut value = Integer::from(1);
    for _ in 0..exponent {
        value *= 10;
    }
    value
}

fn lower_hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        output.push(char::from(DIGITS[usize::from(byte >> 4)]));
        output.push(char::from(DIGITS[usize::from(byte & 0x0f)]));
    }
    output
}
