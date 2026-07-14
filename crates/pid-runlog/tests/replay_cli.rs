use std::collections::BTreeMap;
use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use pid_runlog::{
    canonical_json_hash, canonical_json_hash_v2, logical_trace_hash_v2, runlog_sidecar_paths,
    sha256_hex, validate_events, Actor, ActorType, RunLogEvent, RunLogWriter, RunStatus,
    MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION, RUN_LOG_SCHEMA_VERSION,
};

static TEMP_FILE_COUNTER: AtomicU64 = AtomicU64::new(0);

fn unique_temp_path(label: &str) -> PathBuf {
    let sequence = TEMP_FILE_COUNTER.fetch_add(1, Ordering::Relaxed);
    std::env::temp_dir().join(format!(
        "pid-runlog-replay-cli-{}-{sequence}-{label}",
        std::process::id()
    ))
}

struct TempRunLog(PathBuf);

impl TempRunLog {
    fn write(label: &str, events: &[RunLogEvent]) -> Self {
        let sequence = TEMP_FILE_COUNTER.fetch_add(1, Ordering::Relaxed);
        let path = std::env::temp_dir().join(format!(
            "pid-runlog-replay-cli-{}-{sequence}-{label}.jsonl",
            std::process::id()
        ));
        let mut writer = RunLogWriter::create(&path).unwrap();
        for event in events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);
        Self(path)
    }

    fn path(&self) -> &Path {
        &self.0
    }
}

impl Drop for TempRunLog {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}

fn replay_command(arguments: &[&OsStr]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_pid-runlog-replay"))
        .args(arguments)
        .output()
        .unwrap()
}

fn compare(flag: &str, left: &Path, right: &Path) -> Output {
    replay_command(&[OsStr::new(flag), left.as_os_str(), right.as_os_str()])
}

fn output_text(output: &Output) -> String {
    String::from_utf8(output.stdout.clone()).unwrap()
}

fn assert_output_alias_rejected(input: &Path, output: &Path) {
    let original = std::fs::read(input).unwrap();
    for flag in ["--summary-json", "--manifest-json"] {
        let result = replay_command(&[OsStr::new(flag), input.as_os_str(), output.as_os_str()]);
        assert!(!result.status.success(), "{flag} accepted an input alias");
        assert!(
            String::from_utf8_lossy(&result.stderr).contains("refusing to replace run-log input"),
            "unexpected {flag} error: {}",
            String::from_utf8_lossy(&result.stderr)
        );
        assert_eq!(std::fs::read(input).unwrap(), original);
    }
}

fn valid_events_with_integer(integer: &str) -> Vec<RunLogEvent> {
    let payload: serde_json::Value =
        serde_json::from_str(&format!(r#"{{"value":{integer}}}"#)).unwrap();
    vec![
        RunLogEvent::RunStarted {
            schema_version: MIN_SUPPORTED_RUN_LOG_SCHEMA_VERSION,
            run_id: "adjacent-integer-cli".to_string(),
            timestamp_ns: 1,
            config_hash: sha256_hex(b"cli config"),
            metadata: BTreeMap::new(),
        },
        RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 2,
            actor: Actor {
                actor_type: ActorType::Script,
                actor_id: "cli-test".to_string(),
                session_id: None,
            },
            action_type: "large-integer".to_string(),
            // Schema-1 canonicalization maps these adjacent large integers to the same finite-f64
            // value, so both valid events intentionally retain the same legacy content address.
            payload_hash: canonical_json_hash(&payload).unwrap(),
            payload,
        },
        RunLogEvent::RunEnded {
            run_id: "adjacent-integer-cli".to_string(),
            timestamp_ns: 3,
            status: RunStatus::Succeeded,
            message: None,
        },
    ]
}

#[test]
fn compare_modes_preserve_legacy_collision_and_distinguish_lossless_integers() {
    const FIRST: &str = "12345678901234567890123456789012345678901234567890";
    const SECOND: &str = "12345678901234567890123456789012345678901234567891";
    let left_events = valid_events_with_integer(FIRST);
    let right_events = valid_events_with_integer(SECOND);
    assert!(validate_events(&left_events).unwrap().is_valid());
    assert!(validate_events(&right_events).unwrap().is_valid());
    let left = TempRunLog::write("adjacent-left", &left_events);
    let right = TempRunLog::write("adjacent-right", &right_events);

    for flag in ["--compare", "--compare-logical", "--compare-logical-v2"] {
        let output = compare(flag, left.path(), right.path());
        assert!(
            output.status.success(),
            "{flag} unexpectedly differed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert!(output_text(&output).contains("match=true"));
    }

    for flag in ["--compare-v2", "--compare-logical-v3"] {
        let output = compare(flag, left.path(), right.path());
        assert_eq!(output.status.code(), Some(1), "{flag} unexpectedly matched");
        assert!(output_text(&output).contains("match=false"));
    }

    let output = replay_command(&[left.path().as_os_str()]);
    assert!(output.status.success());
    let expected = logical_trace_hash_v2(&left_events).unwrap();
    assert!(output_text(&output)
        .lines()
        .any(|line| line == format!("logical_trace_hash_v2={expected}")));
}

#[test]
fn bare_summary_accepts_valid_numbers_above_finite_f64() {
    let config: serde_json::Value = serde_json::from_str(r#"{"limit":1e400}"#).unwrap();
    let payload: serde_json::Value = serde_json::from_str(r#"{"magnitude":1e400}"#).unwrap();
    let config_hash = canonical_json_hash_v2(&config).unwrap();
    let events = [
        RunLogEvent::RunStarted {
            schema_version: RUN_LOG_SCHEMA_VERSION,
            run_id: "above-f64-cli".to_string(),
            timestamp_ns: 1,
            config_hash: config_hash.clone(),
            metadata: BTreeMap::new(),
        },
        RunLogEvent::ConfigLogged {
            timestamp_ns: 1,
            config_hash,
            config,
        },
        RunLogEvent::ActionApplied {
            step: 0,
            timestamp_ns: 2,
            actor: Actor {
                actor_type: ActorType::Script,
                actor_id: "cli-test".to_string(),
                session_id: None,
            },
            action_type: "large-number".to_string(),
            payload_hash: canonical_json_hash_v2(&payload).unwrap(),
            payload,
        },
        RunLogEvent::RunEnded {
            run_id: "above-f64-cli".to_string(),
            timestamp_ns: 3,
            status: RunStatus::Succeeded,
            message: None,
        },
    ];
    let run_log = TempRunLog::write("above-f64", &events);

    let output = replay_command(&[run_log.path().as_os_str()]);
    assert!(
        output.status.success(),
        "bare summary failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let stdout = output_text(&output);
    let fields = stdout
        .lines()
        .filter_map(|line| line.split_once('='))
        .collect::<BTreeMap<_, _>>();

    assert_eq!(fields.get("valid"), Some(&"true"));
    assert_eq!(fields.get("trace_hash"), Some(&""));
    assert_eq!(fields.get("logical_trace_hash"), Some(&""));
    assert_eq!(fields.get("trace_hash_v2").map(|hash| hash.len()), Some(64));
    assert_eq!(
        fields.get("logical_trace_hash_v3").map(|hash| hash.len()),
        Some(64)
    );
    assert!(!fields.contains_key("logical_trace_hash_v2"));
}

#[test]
fn json_output_modes_reject_exact_and_hardlink_input_aliases() {
    let run_log = TempRunLog::write("output-alias", &valid_events_with_integer("42"));
    assert_output_alias_rejected(run_log.path(), run_log.path());

    let hardlink = unique_temp_path("hardlink-output.json");
    std::fs::hard_link(run_log.path(), &hardlink).unwrap();
    assert_output_alias_rejected(run_log.path(), &hardlink);
    std::fs::remove_file(hardlink).unwrap();
}

#[cfg(unix)]
#[test]
fn json_output_modes_reject_symlink_input_aliases() {
    use std::os::unix::fs::symlink;

    let run_log = TempRunLog::write("symlink-alias", &valid_events_with_integer("42"));
    let symlink_path = unique_temp_path("symlink-output.json");
    symlink(run_log.path(), &symlink_path).unwrap();

    assert_output_alias_rejected(run_log.path(), &symlink_path);

    std::fs::remove_file(symlink_path).unwrap();
}

#[cfg(unix)]
#[test]
fn write_sidecars_rejects_every_derived_input_alias_before_mutation() {
    use std::os::unix::fs::symlink;

    let events = valid_events_with_integer("42");
    for target_kind in ["validation", "summary", "manifest"] {
        let input = unique_temp_path(&format!("sidecar-input-alias-{target_kind}.jsonl"));
        let outputs = runlog_sidecar_paths(&input);
        let target = match target_kind {
            "validation" => &outputs.validation,
            "summary" => &outputs.summary,
            "manifest" => &outputs.manifest,
            _ => unreachable!(),
        };
        let mut writer = RunLogWriter::create(target).unwrap();
        for event in &events {
            writer.append(event).unwrap();
        }
        writer.flush().unwrap();
        drop(writer);
        let original = std::fs::read(target).unwrap();
        symlink(target, &input).unwrap();

        let output = replay_command(&[OsStr::new("--write-sidecars"), input.as_os_str()]);

        assert_eq!(output.status.code(), Some(2));
        assert!(
            String::from_utf8_lossy(&output.stderr).contains("refusing to replace run-log input")
        );
        assert_eq!(std::fs::read(target).unwrap(), original);
        let _ = std::fs::remove_file(&input);
        for output in [&outputs.validation, &outputs.summary, &outputs.manifest] {
            let _ = std::fs::remove_file(output);
        }
    }
}

#[test]
fn exit_codes_distinguish_semantic_negatives_from_operational_failures() {
    let invalid = TempRunLog::write(
        "semantically-invalid",
        &[RunLogEvent::RunEnded {
            run_id: "never-started".to_string(),
            timestamp_ns: 1,
            status: RunStatus::Failed,
            message: None,
        }],
    );
    let invalid_output = replay_command(&[OsStr::new("--validate"), invalid.path().as_os_str()]);
    assert_eq!(invalid_output.status.code(), Some(1));

    let missing = unique_temp_path("missing-input.jsonl");
    let _ = std::fs::remove_file(&missing);
    let missing_output = replay_command(&[missing.as_os_str()]);
    assert_eq!(missing_output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&missing_output.stderr).contains("error:"));

    let usage_output = replay_command(&[]);
    assert_eq!(usage_output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&usage_output.stderr).contains("usage:"));
}
