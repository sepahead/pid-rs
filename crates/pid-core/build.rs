//! Build script: capture build-provenance metadata (git commit, rustc version) at compile time
//! and expose it to the crate as `PID_CORE_GIT_COMMIT` / `PID_CORE_RUSTC_VERSION` env vars.
//!
//! This lets the `exp0` binary fold the exact toolchain + source revision that produced it into
//! its run-log `config_hash`, so a run certifies the binary that generated it. Both probes are
//! best-effort: if `git`/`rustc` are unavailable (e.g. a packaged source build), the value is
//! reported as `"unknown"` rather than failing the build.
use std::process::Command;

fn main() {
    // Keep at least one rerun directive unconditional: emitting any `rerun-if-*` disables
    // cargo's default rerun-on-any-file-change, so the no-git "unknown" probe result stays
    // cached instead of re-running on every build (registry consumers have no .git at all).
    println!("cargo:rerun-if-env-changed=RUSTC");

    // Re-run when git HEAD moves so the embedded commit stays current. Resolve the real git
    // paths instead of hardcoding `../../.git/…`: that path does not exist in a published
    // .crate or in a git worktree (where HEAD lives in the per-worktree gitdir while refs/
    // packed-refs live in the common dir), and a nonexistent `rerun-if-changed` path makes
    // cargo treat the build script as perpetually dirty for registry consumers.
    if let Some(paths) = Command::new("git")
        .args([
            "rev-parse",
            "--git-path",
            "HEAD",
            "--git-path",
            "refs",
            "--git-path",
            "packed-refs",
        ])
        .output()
        .ok()
        .filter(|out| out.status.success())
        .and_then(|out| String::from_utf8(out.stdout).ok())
    {
        for path in paths.lines().map(str::trim).filter(|p| !p.is_empty()) {
            if std::path::Path::new(path).exists() {
                println!("cargo:rerun-if-changed={path}");
            }
        }
    }

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
