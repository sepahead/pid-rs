//! Compare the ordinary public normalized-invariant reports with exact represented-input answers.

use pid_core::diagnostics::{
    average_degree_of_redundancy, average_degree_of_redundancy_with_policy,
    average_degree_of_vulnerability, average_degree_of_vulnerability_with_policy,
    NormalizedInvariantPolicy, NormalizedInvariantReport,
};
use serde::Deserialize;
use serde_json::{json, Value};
use std::fs::OpenOptions;
use std::io::Write;

const INPUT: &[u8] = include_bytes!("fixtures/normalized_shannon_ratio.json");

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Fixture {
    schema: String,
    rows: Vec<Case>,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct Case {
    id: String,
    method: String,
    wrapper: String,
    terms: Vec<String>,
    joint: String,
    threshold: String,
    expected: Value,
}

fn from_hex(word: &str) -> f64 {
    assert_eq!(word.len(), 16, "fixture words must have 16 hex digits");
    f64::from_bits(u64::from_str_radix(word, 16).expect("invalid binary64 word in fixture"))
}

fn report_for(case: &Case) -> NormalizedInvariantReport {
    let terms: Vec<_> = case.terms.iter().map(|word| from_hex(word)).collect();
    let joint = from_hex(&case.joint);
    let floor = from_hex(&case.threshold);
    let policy = NormalizedInvariantPolicy::new(floor).expect("invalid fixture policy");
    match (case.method.as_str(), case.wrapper.as_str()) {
        ("redundancy", "default") => average_degree_of_redundancy(&terms, joint),
        ("redundancy", "explicit") => {
            average_degree_of_redundancy_with_policy(&terms, joint, policy)
        }
        ("vulnerability", "default") => average_degree_of_vulnerability(joint, &terms),
        ("vulnerability", "explicit") => {
            average_degree_of_vulnerability_with_policy(joint, &terms, policy)
        }
        _ => panic!("unrecognized method or wrapper in fixture"),
    }
}

fn hex(value: f64) -> String {
    format!("{:016x}", value.to_bits())
}

fn observe(report: &NormalizedInvariantReport) -> Value {
    json!({
        "status": report.status,
        "value": report.value.map(hex),
        "numerator_nats": report.numerator_nats.map(hex),
        "denominator_nats": report.denominator_nats.map(hex),
        "definition": report.definition,
        "unit": report.unit,
        "minimum_denominator_nats": hex(report.policy.minimum_denominator_nats()),
    })
}

#[test]
fn normalized_reports_match_exact_represented_inputs() {
    let fixture: Fixture = serde_json::from_slice(INPUT).expect("invalid normalized ratio fixture");
    assert_eq!(fixture.schema, "normalized-shannon-ratio-v1");
    assert_eq!(fixture.rows.len(), 184);
    let mut observations = Vec::with_capacity(fixture.rows.len());
    let mut failures = Vec::new();
    for case in &fixture.rows {
        let actual = observe(&report_for(case));
        if actual != case.expected {
            failures.push(&case.id);
        }
        observations.push(json!({"id":case.id, "report":actual}));
    }
    // Hosted observation changes only the output destination. The test predicate is identical.
    if let Some(path) = std::env::var_os("PID_RS_RATIO_OBSERVATIONS") {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(path)
            .expect("create fresh normalized-ratio observation");
        let record = json!({
            "schema":"normalized-shannon-observations-v1",
            "fixture_sha256":pid_runlog::sha256_hex(INPUT),
            "rows":observations,
        });
        serde_json::to_writer(&mut file, &record)
            .expect("write complete normalized-ratio observation");
        file.write_all(b"\n")
            .expect("finish normalized-ratio observation");
    }
    println!(
        "normalized-ratio rows={} mismatches={}",
        fixture.rows.len(),
        failures.len()
    );
    assert!(
        failures.is_empty(),
        "normalized-ratio field mismatch: {failures:?}"
    );
}
