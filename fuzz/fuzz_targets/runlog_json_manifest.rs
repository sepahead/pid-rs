#![no_main]

use std::io::Cursor;

use libfuzzer_sys::fuzz_target;
use pid_runlog::{
    canonical_json_hash_v2, logical_trace_hash_v3, read_events_with_limits, replay_trace_hash_v2,
    RunLogLimits, RunManifest,
};

fuzz_target!(|data: &[u8]| {
    let input = &data[..data.len().min(16 * 1024)];
    if let Ok(value) = serde_json::from_slice::<serde_json::Value>(input) {
        let _ = canonical_json_hash_v2(&value);
    }
    if let Ok(manifest) = serde_json::from_slice::<RunManifest>(input) {
        if let Ok(encoded) = serde_json::to_vec(&manifest) {
            let _ = serde_json::from_slice::<RunManifest>(&encoded);
        }
    }
    let limits = RunLogLimits::default()
        .with_max_file_bytes(input.len().max(1) as u64)
        .with_max_line_bytes(input.len().clamp(1, 16 * 1024))
        .with_max_events(128)
        .with_max_string_bytes(4 * 1024)
        .with_max_array_len(1024)
        .with_max_object_entries(1024)
        .with_max_nesting_depth(32);
    if let Ok(events) = read_events_with_limits(Cursor::new(input), limits) {
        let _ = replay_trace_hash_v2(&events);
        let _ = logical_trace_hash_v3(&events);
    }
});
