use anyhow::{bail, Context, Result};
use std::io::ErrorKind;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

fn reject_output_alias(input: &Path, output: &Path) -> Result<()> {
    match same_file::is_same_file(input, output) {
        Ok(true) => bail!(
            "refusing to replace run-log input {} through output alias {}",
            input.display(),
            output.display()
        ),
        Ok(false) => Ok(()),
        Err(error) if error.kind() == ErrorKind::NotFound => Ok(()),
        Err(error) => Err(error).with_context(|| {
            format!(
                "failed to compare run-log input {} with output {}",
                input.display(),
                output.display()
            )
        }),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(exit_code) => exit_code,
        Err(error) => {
            eprintln!("error: {error:#}");
            ExitCode::from(2)
        }
    }
}

fn run() -> Result<ExitCode> {
    let args = std::env::args_os().collect::<Vec<_>>();
    let program = args
        .first()
        .cloned()
        .and_then(|s| s.into_string().ok())
        .unwrap_or_else(|| "pid-runlog-replay".to_string());

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare") {
        // Compare the full ordered event sequences, not the collapsed replay state — two
        // different traces can reach the same final state and would otherwise falsely match.
        let left_hash = pid_runlog::replay_trace_hash_from_path(PathBuf::from(args[2].clone()))?;
        let right_hash = pid_runlog::replay_trace_hash_from_path(PathBuf::from(args[3].clone()))?;
        println!("left_trace_hash={left_hash}");
        println!("right_trace_hash={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare-v2") {
        let left_hash = pid_runlog::replay_trace_hash_v2_from_path(PathBuf::from(args[2].clone()))?;
        let right_hash =
            pid_runlog::replay_trace_hash_v2_from_path(PathBuf::from(args[3].clone()))?;
        println!("left_trace_hash_v2={left_hash}");
        println!("right_trace_hash_v2={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare-logical") {
        // Schema-1 compatibility comparison: recursively excludes `timestamp_ns` keys.
        let left_hash = pid_runlog::logical_trace_hash_from_path(PathBuf::from(args[2].clone()))?;
        let right_hash = pid_runlog::logical_trace_hash_from_path(PathBuf::from(args[3].clone()))?;
        println!("left_logical_trace_hash={left_hash}");
        println!("right_logical_trace_hash={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare-logical-v2") {
        // Corrected comparison: only the event's top-level wall clock is excluded; nested
        // payload fields with the same name remain covered.
        let left_hash =
            pid_runlog::logical_trace_hash_v2_from_path(PathBuf::from(args[2].clone()))?;
        let right_hash =
            pid_runlog::logical_trace_hash_v2_from_path(PathBuf::from(args[3].clone()))?;
        println!("left_logical_trace_hash_v2={left_hash}");
        println!("right_logical_trace_hash_v2={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare-logical-v3") {
        let left_hash =
            pid_runlog::logical_trace_hash_v3_from_path(PathBuf::from(args[2].clone()))?;
        let right_hash =
            pid_runlog::logical_trace_hash_v3_from_path(PathBuf::from(args[3].clone()))?;
        println!("left_logical_trace_hash_v3={left_hash}");
        println!("right_logical_trace_hash_v3={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 3 && args.get(1).and_then(|s| s.to_str()) == Some("--validate") {
        let report = pid_runlog::validate_events_from_path(PathBuf::from(args[2].clone()))?;
        println!("valid={}", report.is_valid());
        println!("events={}", report.events);
        println!("errors={}", report.errors);
        println!("warnings={}", report.warnings);
        for issue in &report.issues {
            println!(
                "{:?} event={:?}: {}",
                issue.severity, issue.event_index, issue.message
            );
        }
        if !report.is_valid() {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--summary-json") {
        let input = PathBuf::from(args[2].clone());
        let output = PathBuf::from(args[3].clone());
        reject_output_alias(&input, &output)?;
        let summary = pid_runlog::summarize_path(&input)?;
        pid_runlog::write_json_file(&output, &summary)?;
        println!("wrote {}", output.display());
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--manifest-json") {
        let input = PathBuf::from(args[2].clone());
        let output = PathBuf::from(args[3].clone());
        reject_output_alias(&input, &output)?;
        let manifest = pid_runlog::manifest_for_path(&input)?;
        pid_runlog::write_json_file(&output, &manifest)?;
        println!("wrote {}", output.display());
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 3 && args.get(1).and_then(|s| s.to_str()) == Some("--write-sidecars") {
        let paths = pid_runlog::write_sidecars_for_path(PathBuf::from(args[2].clone()))?;
        println!("wrote {}", paths.validation.display());
        println!("wrote {}", paths.summary.display());
        println!("wrote {}", paths.manifest.display());
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() == 3 && args.get(1).and_then(|s| s.to_str()) == Some("--verify-sidecars") {
        let report = pid_runlog::verify_sidecars_for_path(PathBuf::from(args[2].clone()))?;
        println!("valid={}", report.is_valid());
        println!("sidecars_checked={}", report.checked);
        println!("issues={}", report.issues.len());
        for issue in &report.issues {
            println!(
                "sidecar={} path={}: {}",
                issue.sidecar, issue.path, issue.message
            );
        }
        if !report.is_valid() {
            return Ok(ExitCode::from(1));
        }
        return Ok(ExitCode::SUCCESS);
    }

    if args.len() != 2 {
        bail!(
            "usage: {program} <run-log.jsonl>\n       {program} --validate <run-log.jsonl>\n       {program} --compare <left.jsonl> <right.jsonl>\n       {program} --compare-v2 <left.jsonl> <right.jsonl>\n       {program} --compare-logical <left.jsonl> <right.jsonl>\n       {program} --compare-logical-v2 <left.jsonl> <right.jsonl>\n       {program} --compare-logical-v3 <left.jsonl> <right.jsonl>\n       {program} --summary-json <run-log.jsonl> <summary.json>\n       {program} --manifest-json <run-log.jsonl> <manifest.json>\n       {program} --write-sidecars <run-log.jsonl>\n       {program} --verify-sidecars <run-log.jsonl>"
        );
    }

    let path = PathBuf::from(args[1].clone());
    let summary = pid_runlog::summarize_path(&path)?;
    // This released digest cannot represent every arbitrary-precision payload accepted by the
    // current reader. Keep printing it for legacy-compatible logs without making new lossless
    // logs fail their otherwise valid summary.
    let logical_trace_hash_v2 = summary
        .hash_identities
        .as_ref()
        .and_then(|identities| identities.logical_top_level_clock_legacy.as_ref())
        .map(|identity| identity.digest.as_str());

    println!("events={}", summary.event_count);
    println!("valid={}", summary.validation_errors == 0);
    println!("validation_errors={}", summary.validation_errors);
    println!("validation_warnings={}", summary.validation_warnings);
    println!("trace_hash={}", summary.trace_hash);
    println!("trace_hash_v2={}", summary.trace_hash_v2);
    println!("logical_trace_hash={}", summary.logical_trace_hash);
    if let Some(hash) = logical_trace_hash_v2 {
        println!("logical_trace_hash_v2={hash}");
    }
    println!("logical_trace_hash_v3={}", summary.logical_trace_hash_v3);
    if let Some(run_id) = &summary.run_id {
        println!("run_id={run_id}");
    }
    if let Some(config_hash) = &summary.config_hash {
        println!("config_hash={config_hash}");
    }
    if let Some(step) = summary.last_step {
        println!("last_step={step}");
    }
    println!("actions={}", summary.actions);
    println!("interventions={}", summary.interventions);
    println!("objects={}", summary.objects);
    println!("pid_metrics={}", summary.pid_metrics);
    println!("geometry_metrics={}", summary.geometry_metrics);
    println!("evaluation_metrics={}", summary.evaluation_metrics);
    println!("pid_metric_events={}", summary.pid_metric_events);
    println!("geometry_metric_events={}", summary.geometry_metric_events);
    println!(
        "evaluation_metric_events={}",
        summary.evaluation_metric_events
    );
    println!("labels={}", summary.labels);
    println!("embeddings={}", summary.embeddings);
    println!("embedding_contracts={}", summary.embedding_contracts);
    println!("bridge_records={}", summary.bridge_records);
    println!("sim_snapshots={}", summary.sim_snapshots);
    println!("artifacts={}", summary.artifacts);
    println!("attributions={}", summary.attributions);
    println!("errors={}", summary.errors);
    println!("flow_gt_records={}", summary.flow_gt_records);
    println!("flow_pred_records={}", summary.flow_pred_records);

    Ok(ExitCode::SUCCESS)
}
