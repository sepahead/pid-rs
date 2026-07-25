//! Process-level qualification of the bounded CLI and its exit/envelope contract.

use std::io::Write;
use std::process::{Command, Output, Stdio};

use pid_certified_sxpid::MAX_INPUT_BYTES;
use serde_json::{json, Value};

fn binary() -> &'static str {
    env!("CARGO_BIN_EXE_pid-certified-sxpid")
}

fn run(arguments: &[&str], stdin: Option<&[u8]>) -> Output {
    let mut command = Command::new(binary());
    command
        .args(arguments)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if stdin.is_some() {
        command.stdin(Stdio::piped());
    } else {
        command.stdin(Stdio::null());
    }
    let mut child = command.spawn().expect("certifier process must start");
    if let Some(bytes) = stdin {
        child
            .stdin
            .take()
            .expect("piped standard input must exist")
            .write_all(bytes)
            .expect("bounded test input must be writable");
    }
    child
        .wait_with_output()
        .expect("certifier process must terminate")
}

fn parse_single_envelope(output: &Output) -> Value {
    assert!(
        output.stderr.is_empty(),
        "machine-readable rejection must not write stderr: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        output.stdout.iter().filter(|byte| **byte == b'\n').count(),
        1,
        "stdout must contain exactly one compact JSON line"
    );
    serde_json::from_slice(&output.stdout).expect("stdout must be one JSON envelope")
}

fn singleton_input() -> Vec<u8> {
    serde_json::to_vec(&json!({
        "schema": "pid-rs/categorical-sxpid2-count-table/v1",
        "definition_revision": "makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1",
        "units": "nats",
        "resource_policy_id": "sxpid2-certification-default-v2",
        "rows": [{
            "source_states": [["a"], ["b"]],
            "target_state": ["t"],
            "count": "1"
        }]
    }))
    .expect("singleton input must serialize")
}

#[test]
fn stdin_success_should_emit_one_certificate_and_exit_zero() {
    let output = run(&["-"], Some(&singleton_input()));
    assert_eq!(output.status.code(), Some(0));
    let envelope = parse_single_envelope(&output);
    assert_eq!(
        envelope["payload"]["schema"],
        "pid-rs/certified-sxpid-report/v2"
    );
    assert_eq!(envelope["payload"]["status"], "certified");
    assert_eq!(
        envelope["payload"]["coordinates"].as_array().map(Vec::len),
        Some(24)
    );
}

#[test]
fn usage_errors_should_emit_one_rejection_and_exit_two() {
    for arguments in [Vec::<&str>::new(), vec!["one", "two"]] {
        let output = run(&arguments, None);
        assert_eq!(output.status.code(), Some(2));
        let envelope = parse_single_envelope(&output);
        assert_eq!(envelope["error_code"], "invalid_usage");
        assert_eq!(envelope["status"], "rejected");
        assert!(envelope.get("payload").is_none());
    }
}

#[test]
fn invalid_schema_should_emit_one_rejection_and_exit_two() {
    let input = br#"{"schema":"wrong","definition_revision":"makkeh-gutknecht-wibral-2021-empirical-sxpid2-v1","units":"nats","resource_policy_id":"sxpid2-certification-default-v2","rows":[]}"#;
    let output = run(&["-"], Some(input));
    assert_eq!(output.status.code(), Some(2));
    let envelope = parse_single_envelope(&output);
    assert_eq!(envelope["error_code"], "unsupported_schema");
    assert_eq!(envelope["status"], "rejected");
    assert!(envelope.get("payload").is_none());
}

#[test]
fn oversized_stdin_should_stop_at_limit_plus_one_and_exit_two() {
    let bytes = vec![b' '; MAX_INPUT_BYTES + 1];
    let output = run(&["-"], Some(&bytes));
    assert_eq!(output.status.code(), Some(2));
    let envelope = parse_single_envelope(&output);
    assert_eq!(envelope["error_code"], "input_io_failure");
    assert_eq!(envelope["status"], "rejected");
    assert!(envelope.get("payload").is_none());
}
