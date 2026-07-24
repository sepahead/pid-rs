//! Offline exact-count, directed-rounding certification for two-source averaged categorical SxPID.
//!
//! This standalone audit crate is not part of the published `pid-rs` workspace. Its accepted
//! result is a conditional numerical enclosure of the exact expression that this tool encodes.
//! It does not certify `pid-core` binary64 output, data assumptions, or downstream validity.
//!
//! Method catalog: validation.certified-sxpid2-reference

#![forbid(unsafe_code)]

mod digest;
mod directed;
mod error;
mod evaluate;
mod exact;
mod extract;
mod lattice2;
mod report;
mod resource;
mod schema;

pub use error::CertError;
pub use report::{CertificateEnvelope, FailureEnvelope};
pub use resource::MAX_INPUT_BYTES;

use digest::{manifest_digest, sha256_hex};
use resource::PrecisionPolicy;

const SOURCE_MANIFEST: &[(&str, &[u8])] = &[
    ("build.rs", include_bytes!("../build.rs")),
    ("Cargo.lock", include_bytes!("../Cargo.lock")),
    ("Cargo.toml", include_bytes!("../Cargo.toml")),
    ("README.md", include_bytes!("../README.md")),
    ("src/digest.rs", include_bytes!("digest.rs")),
    ("src/directed.rs", include_bytes!("directed.rs")),
    ("src/error.rs", include_bytes!("error.rs")),
    ("src/evaluate.rs", include_bytes!("evaluate.rs")),
    ("src/exact.rs", include_bytes!("exact.rs")),
    ("src/extract.rs", include_bytes!("extract.rs")),
    ("src/lattice2.rs", include_bytes!("lattice2.rs")),
    ("src/lib.rs", include_bytes!("lib.rs")),
    ("src/main.rs", include_bytes!("main.rs")),
    ("src/report.rs", include_bytes!("report.rs")),
    ("src/resource.rs", include_bytes!("resource.rs")),
    ("src/schema.rs", include_bytes!("schema.rs")),
];

/// Certifies all 24 cumulative/atom and informative/misinformative/net coordinates.
///
/// # Errors
///
/// Returns a typed error for invalid canonical input, an exact semantic invariant failure, an
/// arithmetic soundness failure, or exhaustion of the versioned precision policy.
pub fn certify_sxpid2(input_json: &[u8]) -> Result<CertificateEnvelope, CertError> {
    certify_with_policy(input_json, &PrecisionPolicy::default_v1())
}

fn certify_with_policy(
    input_json: &[u8],
    policy: &PrecisionPolicy,
) -> Result<CertificateEnvelope, CertError> {
    let input = schema::parse_and_validate(input_json)?;
    let extraction = extract::extract(&input)?;
    report::validate_resource_bounds(&extraction)?;
    let evaluation = evaluate::evaluate_all(&extraction, policy)?;
    report::build_certificate(
        &input,
        &extraction,
        policy,
        evaluation,
        manifest_digest(SOURCE_MANIFEST)?,
        sha256_hex(include_bytes!("../Cargo.lock")),
    )
}

#[cfg(test)]
mod tests {
    use rug::{Integer, Rational};
    use serde_json::{json, to_vec, Value};

    use crate::resource::PrecisionPolicy;
    use crate::schema::{canonical_document, InputRow};

    use super::{certify_sxpid2, certify_with_policy};

    fn singleton_input() -> Vec<u8> {
        to_vec(&canonical_document(vec![InputRow {
            source_states: [vec![String::from("a")], vec![String::from("b")]],
            target_state: vec![String::from("t")],
            count: String::from("1"),
        }]))
        .expect("serialize singleton input")
    }

    fn nonzero_input() -> Vec<u8> {
        to_vec(&canonical_document(vec![
            InputRow {
                source_states: [vec![String::from("0")], vec![String::from("0")]],
                target_state: vec![String::from("0")],
                count: String::from("1"),
            },
            InputRow {
                source_states: [vec![String::from("1")], vec![String::from("1")]],
                target_state: vec![String::from("1")],
                count: String::from("1"),
            },
        ]))
        .expect("serialize nonzero input")
    }

    fn singleton_value() -> Value {
        serde_json::from_slice(&singleton_input()).expect("singleton input must be valid JSON")
    }

    fn encode_state(prefix: &str, value: &str, width: usize) -> Vec<String> {
        (0..width)
            .map(|column| format!("{prefix}{column}_{value}"))
            .collect::<Vec<_>>()
    }

    fn xor_input(widths: [usize; 3]) -> Vec<u8> {
        xor_input_with_count(widths, "1")
    }

    fn xor_input_with_count(widths: [usize; 3], count: &str) -> Vec<u8> {
        let rows = [
            ("0", "0", "0"),
            ("0", "1", "1"),
            ("1", "0", "1"),
            ("1", "1", "0"),
        ]
        .into_iter()
        .map(|(one, two, target)| InputRow {
            source_states: [
                encode_state("a", one, widths[0]),
                encode_state("b", two, widths[1]),
            ],
            target_state: encode_state("t", target, widths[2]),
            count: count.to_owned(),
        })
        .collect();
        to_vec(&canonical_document(rows)).expect("serialize XOR input")
    }

    fn assert_exact_coordinate_equivalence(left: &Value, right: &Value, context: &str) {
        let left_coordinates = left["payload"]["coordinates"]
            .as_array()
            .expect("left coordinates");
        let right_coordinates = right["payload"]["coordinates"]
            .as_array()
            .expect("right coordinates");
        assert_eq!(right_coordinates.len(), left_coordinates.len(), "{context}");
        for (left_coordinate, right_coordinate) in left_coordinates.iter().zip(right_coordinates) {
            assert_eq!(
                right_coordinate["identity"], left_coordinate["identity"],
                "{context}"
            );
            assert_eq!(
                right_coordinate["exact_terms"], left_coordinate["exact_terms"],
                "{context}, identity {}",
                left_coordinate["identity"]
            );
            assert_eq!(
                right_coordinate["expression_sha256"], left_coordinate["expression_sha256"],
                "{context}, identity {}",
                left_coordinate["identity"]
            );
        }
    }

    #[test]
    fn certify_should_emit_exactly_24_coordinates() {
        let certificate = certify_sxpid2(&singleton_input()).expect("singleton certificate");
        let json = serde_json::to_value(certificate).expect("serialize certificate");

        assert_eq!(
            json["payload"]["coordinates"].as_array().map(Vec::len),
            Some(24)
        );
    }

    #[test]
    fn certificate_payload_digest_should_match_declared_canonical_encoding() {
        let certificate = certify_sxpid2(&singleton_input()).expect("singleton certificate");
        let json = serde_json::to_value(certificate).expect("serialize certificate");
        let payload = json
            .get("payload")
            .expect("certificate payload must be present");
        let recomputed = crate::digest::sha256_hex(
            &crate::digest::canonical_json_bytes(payload).expect("canonical payload"),
        );

        assert_eq!(json["payload_sha256"].as_str(), Some(recomputed.as_str()));
        assert!(json["payload"]["arithmetic"]["native_archive_digests"].is_null());
        assert_eq!(
            json["payload"]["arithmetic"]["direct_gmp_mpfr_sys_dependency_status"].as_str(),
            Some("absent_to_remove_direct_dependency_feature_injection_surface")
        );
        assert_eq!(
            json["payload"]["arithmetic"]["effective_dependency_feature_resolution_status"]
                .as_str(),
            Some(
                "not_self_reported_or_bound_official_qualification_separately_requires_default_locked_metadata_graph"
            )
        );
        assert!(json["payload"]["arithmetic"]
            .get("configured_gmp_mpfr_sys_features")
            .is_none());
    }

    #[test]
    fn vector_state_encoding_should_preserve_every_exact_xor_expression() {
        let scalar = serde_json::to_value(
            certify_sxpid2(&xor_input([1, 1, 1])).expect("scalar XOR certificate"),
        )
        .expect("serialize scalar XOR certificate");

        for widths in [[2, 1, 1], [1, 2, 1], [1, 1, 2], [32, 32, 32]] {
            let vector = serde_json::to_value(
                certify_sxpid2(&xor_input(widths)).expect("vector XOR certificate"),
            )
            .expect("serialize vector XOR certificate");
            assert_exact_coordinate_equivalence(&scalar, &vector, &format!("widths {widths:?}"));
        }
    }

    #[test]
    fn common_thousand_digit_count_scale_should_preserve_every_exact_xor_expression() {
        let unit = serde_json::to_value(
            certify_sxpid2(&xor_input([1, 1, 1])).expect("unit-count XOR certificate"),
        )
        .expect("serialize unit-count XOR certificate");
        let thousand_digit_factor = "9".repeat(1000);
        let scaled = serde_json::to_value(
            certify_sxpid2(&xor_input_with_count([1, 1, 1], &thousand_digit_factor))
                .expect("large-count XOR certificate"),
        )
        .expect("serialize large-count XOR certificate");

        assert_exact_coordinate_equivalence(&unit, &scaled, "common 1000-digit count scale");
    }

    #[test]
    fn certify_should_reject_duplicate_json_keys() {
        let input = br#"{
            "schema":"pid-rs/categorical-sxpid2-count-table/v1",
            "schema":"pid-rs/categorical-sxpid2-count-table/v1",
            "definition_revision":"makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1",
            "units":"nats",
            "resource_policy_id":"sxpid2-certification-default-v1",
            "rows":[]
        }"#;

        let error = certify_sxpid2(input).expect_err("duplicate key must fail");

        assert_eq!(error.code(), "invalid_json_or_schema");
    }

    #[test]
    fn certify_should_reject_schema_and_canonicalization_violations() {
        let valid = singleton_value();
        let mut cases = Vec::new();

        let mut unknown_top_level = valid.clone();
        unknown_top_level
            .as_object_mut()
            .expect("document must be an object")
            .insert("unexpected".to_owned(), json!(true));
        cases.push((
            "unknown top-level field",
            unknown_top_level,
            "invalid_json_or_schema",
        ));

        let mut unknown_row_field = valid.clone();
        unknown_row_field["rows"][0]
            .as_object_mut()
            .expect("row must be an object")
            .insert("unexpected".to_owned(), json!(true));
        cases.push((
            "unknown row field",
            unknown_row_field,
            "invalid_json_or_schema",
        ));

        for (label, field, value, expected_code) in [
            (
                "schema",
                "schema",
                json!("future-schema"),
                "unsupported_schema",
            ),
            (
                "definition",
                "definition_revision",
                json!("future-definition"),
                "unsupported_definition_revision",
            ),
            ("units", "units", json!("bits"), "unsupported_units"),
            (
                "resource policy",
                "resource_policy_id",
                json!("future-policy"),
                "unsupported_resource_policy",
            ),
        ] {
            let mut document = valid.clone();
            document[field] = value;
            cases.push((label, document, expected_code));
        }

        let mut empty_rows = valid.clone();
        empty_rows["rows"] = json!([]);
        cases.push(("empty rows", empty_rows, "invalid_row_count"));

        let mut empty_state = valid.clone();
        empty_state["rows"][0]["source_states"][0] = json!([]);
        cases.push(("empty source state", empty_state, "invalid_state_width"));

        let mut invalid_token = valid.clone();
        invalid_token["rows"][0]["target_state"][0] = json!("contains space");
        cases.push(("invalid token", invalid_token, "invalid_state_token"));

        for count in ["0", "01", "+1", "1.0"] {
            let mut invalid_count = valid.clone();
            invalid_count["rows"][0]["count"] = json!(count);
            cases.push(("noncanonical count", invalid_count, "invalid_count"));
        }

        let mut duplicate_state = valid.clone();
        duplicate_state["rows"] = json!([valid["rows"][0].clone(), valid["rows"][0].clone()]);
        cases.push(("duplicate state", duplicate_state, "duplicate_state"));

        let mut descending_rows: Value =
            serde_json::from_slice(&nonzero_input()).expect("nonzero input must be JSON");
        descending_rows["rows"]
            .as_array_mut()
            .expect("rows must be an array")
            .reverse();
        cases.push(("descending rows", descending_rows, "noncanonical_row_order"));

        let mut inconsistent_width: Value =
            serde_json::from_slice(&nonzero_input()).expect("nonzero input must be JSON");
        inconsistent_width["rows"][1]["source_states"][0] = json!(["1", "extra"]);
        cases.push((
            "inconsistent width",
            inconsistent_width,
            "inconsistent_state_width",
        ));

        for (label, document, expected_code) in cases {
            let bytes = serde_json::to_vec(&document).expect("negative case must serialize");
            let error = match certify_sxpid2(&bytes) {
                Ok(_) => panic!("{label}: expected {expected_code} rejection"),
                Err(error) => error,
            };
            assert_eq!(error.code(), expected_code, "{label}");
        }
    }

    #[test]
    fn certify_should_return_precision_limit_without_partial_certificate() {
        let target_denominator = Integer::from(1) << 1000;
        let policy = PrecisionPolicy::for_test(
            32,
            32,
            1,
            2,
            Rational::from((Integer::from(1), target_denominator)),
        );

        let error = certify_with_policy(&nonzero_input(), &policy)
            .expect_err("impossible width policy must fail closed");

        assert_eq!(error.code(), "precision_limit");
    }
}
