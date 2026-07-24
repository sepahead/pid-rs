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
    scripts/check-current-release-state.sh
    scripts/check-release-state-self-test.sh
    python3 scripts/check-software-identity.py
    python3 scripts/check-software-identity-self-test.py
    python3 scripts/check-method-catalog.py
    python3 scripts/check-method-catalog-self-test.py
    python3 scripts/check-ecosystem-capabilities.py
    python3 scripts/check-ecosystem-capabilities-self-test.py
    scripts/check-handoff-intake.py
    scripts/check-handoff-intake-self-test.py
    python3 scripts/generate-finite-alphabet-plugin-oracle.py
    python3 scripts/generate-dependency-colored-sxpid-oracle.py
    python3 scripts/generate-support-change-tolerant-sxpid-oracle.py
    python3 scripts/generate-ksg-local-arithmetic-oracle.py
    python3 scripts/generate-sxpid2-exhaustive-oracle.py
    python3 scripts/check-markdown-math.py
    python3 scripts/check-markdown-math-self-test.py
    python3 scripts/check-review-evidence.py
    python3 scripts/check-review-evidence-self-test.py
    scripts/collect-repository-snapshot.py --validate audit/evidence/repository-snapshot.json
    scripts/check-repository-snapshot-self-test.sh
    scripts/repin-pidrs-self-test.sh
    scripts/check-release-scope.py
    scripts/check-release-scope-self-test.sh

# Rebuild all frozen pid-core public API profiles (requires cargo-public-api 0.52.0 and the
# pinned nightly recorded in release-scope-1.0.json).
api-snapshots:
    scripts/check-public-api-snapshots.sh
    scripts/check-public-api-snapshots-self-test.sh

# Bounded exact-real PID2 and PID3 algebra obligations (requires Z3 4.16.0, 64-bit CLI).
# The target keeps its original name as a compatibility route.
formal-pid2:
    python3 scripts/check-z3-pid2-algebra.py
    python3 scripts/check-z3-pid2-algebra-self-test.py

# Deterministic finite-alphabet convergence core (requires Lean 4.32.0 and the pinned mathlib).
formal-finite-convergence:
    python3 scripts/check-lean-finite-convergence.py

# Standalone exact-count, directed-rounding SxPID2 certifier (Rug/MPFR; source-only).
certified-sxpid:
    CARGO_TARGET_DIR=target/certified-sxpid cargo test --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml
    CARGO_TARGET_DIR=target/certified-sxpid cargo clippy --locked --manifest-path audit/tools/certified-sxpid/Cargo.toml --all-targets -- -D warnings
    RUSTDOCFLAGS="-D warnings" CARGO_TARGET_DIR=target/certified-sxpid cargo doc --locked --no-deps --manifest-path audit/tools/certified-sxpid/Cargo.toml
    cargo fmt --manifest-path audit/tools/certified-sxpid/Cargo.toml --all --check
    python3 audit/tools/certified-sxpid/scripts/check-static-policy.py
    python3 audit/tools/certified-sxpid/scripts/check-static-policy-self-test.py
    cargo deny --manifest-path audit/tools/certified-sxpid/Cargo.toml check --config audit/tools/certified-sxpid/deny.toml

# Rebuild the standalone finite-alphabet mathematical paper and compare its exact PDF bytes.
formal-finite-convergence-pdf:
    scripts/check-finite-alphabet-convergence-pdf.sh

# Rebuild the dependency-colored SxPID paper and compare its exact PDF bytes.
formal-dependency-sxpid-pdf:
    scripts/check-dependency-colored-sxpid-pdf.sh

# Rebuild the support-change-tolerant averaged SxPID paper and compare its exact PDF bytes.
formal-support-change-sxpid-pdf:
    scripts/check-support-change-tolerant-sxpid-pdf.sh

# Rebuild the formal-tool adoption decision record and compare its exact PDF bytes.
formal-tool-adoption-pdf:
    scripts/check-formal-tool-adoption-pdf.sh

# Require a one-to-one inventory of formal LaTeX sources and rendered PDFs, then replay
# every warning-free deterministic PDF build.
formal-pdfs:
    scripts/check-formal-pdf-set.sh

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
release-audit: lint test test-stable test-parallel test-all-features test-release doc msrv deny smoke version-check formal-pid2 formal-finite-convergence formal-pdfs
    cargo publish --locked -p pid-runlog --dry-run
    scripts/verify-package-archives.sh

# Core local gates. CI additionally runs OS/Python matrices, coverage, fuzz, SBOM, semver/package,
# a full-history secret scan, and the pinned MSRV matrix.
ci: lint test test-stable test-parallel test-all-features doc deny smoke version-check
