//! Build script: capture build-provenance metadata (git commit, rustc version) at compile time
//! and expose it to the crate as `PID_CORE_GIT_COMMIT` / `PID_CORE_RUSTC_VERSION` env vars.
//!
//! This lets the `exp0` binary fold the exact toolchain + source revision that produced it into
//! its run-log `config_hash`, so a run certifies the binary that generated it. Both probes are
//! best-effort: if `git`/`rustc` are unavailable (e.g. a packaged source build), the value is
//! reported as `"unknown"` rather than failing the build.
use std::process::Command;

fn main() {
    // Re-run if the git HEAD moves so the embedded commit stays current.
    println!("cargo:rerun-if-changed=../../.git/HEAD");
    println!("cargo:rerun-if-changed=../../.git/refs");
    println!("cargo:rerun-if-env-changed=RUSTC");

    let git_commit = Command::new("git")
        .args(["rev-parse", "HEAD"])
        .output()
        .ok()
        .filter(|out| out.status.success())
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".to_string());
    println!("cargo:rustc-env=PID_CORE_GIT_COMMIT={git_commit}");

    let rustc = std::env::var("RUSTC").unwrap_or_else(|_| "rustc".to_string());
    let rustc_version = Command::new(rustc)
        .arg("--version")
        .output()
        .ok()
        .filter(|out| out.status.success())
        .and_then(|out| String::from_utf8(out.stdout).ok())
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
        .unwrap_or_else(|| "unknown".to_string());
    println!("cargo:rustc-env=PID_CORE_RUSTC_VERSION={rustc_version}");
}
