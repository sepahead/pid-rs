use anyhow::{bail, Result};
use std::path::PathBuf;

fn main() -> Result<()> {
    let args = std::env::args_os().collect::<Vec<_>>();
    let program = args
        .first()
        .cloned()
        .and_then(|s| s.into_string().ok())
        .unwrap_or_else(|| "pid-runlog-replay".to_string());

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--compare") {
        let left = pid_runlog::replay_state_from_path(PathBuf::from(args[2].clone()))?;
        let right = pid_runlog::replay_state_from_path(PathBuf::from(args[3].clone()))?;
        let left_hash = pid_runlog::canonical_json_hash(&left)?;
        let right_hash = pid_runlog::canonical_json_hash(&right)?;
        println!("left_trace_hash={left_hash}");
        println!("right_trace_hash={right_hash}");
        let matches = left_hash == right_hash;
        println!("match={matches}");
        if !matches {
            std::process::exit(1);
        }
        return Ok(());
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
            std::process::exit(1);
        }
        return Ok(());
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--summary-json") {
        let summary = pid_runlog::summarize_path(PathBuf::from(args[2].clone()))?;
        pid_runlog::write_json_file(PathBuf::from(args[3].clone()), &summary)?;
        println!("wrote {}", PathBuf::from(args[3].clone()).display());
        return Ok(());
    }

    if args.len() == 4 && args.get(1).and_then(|s| s.to_str()) == Some("--manifest-json") {
        let manifest = pid_runlog::manifest_for_path(PathBuf::from(args[2].clone()))?;
        pid_runlog::write_json_file(PathBuf::from(args[3].clone()), &manifest)?;
        println!("wrote {}", PathBuf::from(args[3].clone()).display());
        return Ok(());
    }

    if args.len() == 3 && args.get(1).and_then(|s| s.to_str()) == Some("--write-sidecars") {
        let paths = pid_runlog::write_sidecars_for_path(PathBuf::from(args[2].clone()))?;
        println!("wrote {}", paths.validation.display());
        println!("wrote {}", paths.summary.display());
        println!("wrote {}", paths.manifest.display());
        return Ok(());
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
            std::process::exit(1);
        }
        return Ok(());
    }

    if args.len() != 2 {
        bail!(
            "usage: {program} <run-log.jsonl>\n       {program} --validate <run-log.jsonl>\n       {program} --compare <left.jsonl> <right.jsonl>\n       {program} --summary-json <run-log.jsonl> <summary.json>\n       {program} --manifest-json <run-log.jsonl> <manifest.json>\n       {program} --write-sidecars <run-log.jsonl>\n       {program} --verify-sidecars <run-log.jsonl>"
        );
    }

    let path = PathBuf::from(args[1].clone());
    let events = pid_runlog::read_events_from_path(&path)?;
    let validation = pid_runlog::validate_events(&events);
    let state = pid_runlog::replay_events(&events);
    let trace_hash = pid_runlog::canonical_json_hash(&state)?;

    println!("events={}", state.events_seen);
    println!("valid={}", validation.is_valid());
    println!("validation_errors={}", validation.errors);
    println!("validation_warnings={}", validation.warnings);
    println!("trace_hash={trace_hash}");
    if let Some(run_id) = &state.run_id {
        println!("run_id={run_id}");
    }
    if let Some(config_hash) = &state.config_hash {
        println!("config_hash={config_hash}");
    }
    if let Some(step) = state.last_step {
        println!("last_step={step}");
    }
    println!("actions={}", state.actions.len());
    println!("interventions={}", state.interventions.len());
    println!("objects={}", state.object_poses.len());
    println!("pid_metrics={}", state.pid_metrics.len());
    println!("geometry_metrics={}", state.geometry_metrics.len());
    println!("evaluation_metrics={}", state.evaluation_metrics.len());
    println!("pid_metric_events={}", state.pid_metric_events);
    println!("geometry_metric_events={}", state.geometry_metric_events);
    println!(
        "evaluation_metric_events={}",
        state.evaluation_metric_events
    );
    println!("labels={}", state.labels.len());
    println!("embeddings={}", state.embeddings.len());
    println!("embedding_contracts={}", state.embedding_contracts.len());
    println!("bridge_records={}", state.bridge_records.len());
    println!("sim_snapshots={}", state.sim_snapshots);
    println!("artifacts={}", state.artifacts.len());
    println!("attributions={}", state.attributions.len());
    println!("errors={}", state.errors.len());
    println!("flow_gt_records={}", state.flow_gt_records);
    println!("flow_pred_records={}", state.flow_pred_records);

    Ok(())
}
