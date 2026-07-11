use std::collections::BTreeMap;
use std::ffi::OsStr;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use pid_runlog::{
    canonical_json_hash, canonical_json_hash_v2, validate_events, Actor, ActorType, RunLogEvent,
    RunLogWriter, RunStatus, RUN_LOG_SCHEMA_VERSION,
};

static TEMP_FILE_COUNTER: AtomicU64 = AtomicU64::new(0);

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

fn valid_events_with_integer(integer: &str) -> Vec<RunLogEvent> {
    let payload: serde_json::Value =
        serde_json::from_str(&format!(r#"{{"value":{integer}}}"#)).unwrap();
    vec![
        RunLogEvent::RunStarted {
            schema_version: RUN_LOG_SCHEMA_VERSION,
            run_id: "adjacent-integer-cli".to_string(),
            timestamp_ns: 1,
            config_hash: "cfg".to_string(),
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
    assert!(validate_events(&left_events).is_valid());
    assert!(validate_events(&right_events).is_valid());
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
    assert_eq!(fields.get("trace_hash"), fields.get("trace_hash_v2"));
    assert_eq!(
        fields.get("logical_trace_hash"),
        fields.get("logical_trace_hash_v3")
    );
    assert_eq!(fields.get("trace_hash_v2").map(|hash| hash.len()), Some(64));
    assert_eq!(
        fields.get("logical_trace_hash_v3").map(|hash| hash.len()),
        Some(64)
    );
    assert!(!fields.contains_key("logical_trace_hash_v2"));
}
