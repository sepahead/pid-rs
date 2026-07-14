# Development tasks for pid-rs — executable mirror of the canonical commands in AGENTS.md.
# Install `just`: https://github.com/casey/just   (then run `just` to list recipes)

# List available recipes
default:
    @just --list

# Full workspace test suite (pid-python is tested via maturin; see `py-test`)
test:
    cargo test --locked --workspace --exclude pid-python

# Approved stable/default surface (default features are intentionally empty)
test-stable:
    cargo test --locked -p pid-core --no-default-features

# The exact data-parallel kNN path (must stay bit-identical to serial)
test-parallel:
    cargo test --locked -p pid-core --features parallel

# Every default-off experimental/research surface
test-all-features:
    cargo test --locked -p pid-core --all-features

# Release-mode numerical fixtures
test-release:
    cargo test --locked --release -p pid-core --all-features

# Format check + clippy (mirrors CI's lint gate — the whole workspace, pid-python included;
# clippy is check-based and never links libpython)
lint:
    cargo fmt --all --check
    cargo clippy --locked --workspace --all-targets --all-features -- -D warnings

# Auto-format the tree
fmt:
    cargo fmt --all

# Build docs with warnings denied, then the docs.rs `--cfg docsrs` gate
# (`--lib` is required: cargo refuses to forward rustdoc args to more than one target)
doc:
    RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps
    RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
    RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-core --all-features --lib -- --cfg docsrs
    RUSTDOCFLAGS="-D warnings" cargo rustdoc --locked -p pid-runlog --all-features --lib -- --cfg docsrs

# Estimator benchmarks
bench:
    cargo bench -p pid-core

# Supply-chain audit (advisories + licenses + bans + sources).
# --all-features so the `parallel` (rayon) dependency subtree is scanned, matching CI;
# top-level cargo-deny flags go BEFORE the `check` subcommand.
deny:
    cargo deny --all-features --locked check

# The worked examples
examples:
    cargo run --locked --release -p pid-core --features experimental-continuous --example ksg_and_pid
    cargo run --locked --release --example discrete_sxpid

# exp0 diagnostic + run-log round-trip smoke
smoke:
    cargo run --locked -p pid-core --all-features --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
    cargo run --locked -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl

# Build + test the Python bindings via maturin (needs: pip install maturin numpy pytest)
py-test:
    maturin develop --release --locked -m crates/pid-python/Cargo.toml
    pytest crates/pid-python/tests -q

# Version coherence (Cargo workspace version == CITATION.cff; CI also runs a tag mode on tag pushes)
version-check:
    scripts/check-version-coherence.sh
    scripts/check-release-state.sh candidate
    scripts/check-release-state-self-test.sh

# Minimum supported Rust version
msrv:
    cargo +1.89 check --locked --workspace
    cargo +1.89 check --locked --workspace --all-features

# Fixed corpus smoke; requires a rustup nightly and
# `cargo install cargo-fuzz --locked --version 0.13.2`.
fuzz-smoke:
    #!/usr/bin/env bash
    set -euo pipefail
    cd fuzz
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum --check corpus/SHA256SUMS
    else
      shasum -a 256 -c corpus/SHA256SUMS
    fi
    for target in matrix_shape public_configs_shells quantizer_sxpid experimental_antichain runlog_json_manifest experimental_hyperbolic resource_budgets; do
      cargo +nightly fuzz run "$target" -- -runs=128 -max_len=16384 -seed=424242
    done

# Release-candidate checks that are useful locally (CI also runs cross-platform/Python/coverage).
release-audit: lint test test-stable test-parallel test-all-features test-release doc msrv deny smoke version-check
    cargo publish --locked -p pid-runlog --dry-run
    scripts/verify-package-archives.sh

# Core local gates. CI additionally runs OS/Python matrices, coverage, fuzz, SBOM, semver/package,
# a full-history secret scan, and the pinned MSRV matrix.
ci: lint test test-stable test-parallel test-all-features doc deny smoke version-check
