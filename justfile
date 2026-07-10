# Development tasks for pid-rs — executable mirror of the canonical commands in AGENTS.md.
# Install `just`: https://github.com/casey/just   (then run `just` to list recipes)

# List available recipes
default:
    @just --list

# Full workspace test suite (pid-python is tested via maturin; see `py-test`)
test:
    cargo test --locked --workspace --exclude pid-python

# The exact data-parallel kNN path (must stay bit-identical to serial)
test-parallel:
    cargo test --locked -p pid-core --features parallel

# Format check + clippy (mirrors CI's lint gate — the whole workspace, pid-python included;
# clippy is check-based and never links libpython)
lint:
    cargo fmt --all --check
    cargo clippy --locked --workspace --all-targets -- -D warnings
    cargo clippy --locked -p pid-core --all-targets --features parallel -- -D warnings

# Auto-format the tree
fmt:
    cargo fmt --all

# Build docs with warnings denied
doc:
    RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --no-deps

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
    cargo run --locked --release --example ksg_and_pid
    cargo run --locked --release --example discrete_sxpid

# exp0 diagnostic + run-log round-trip smoke
smoke:
    cargo run --locked -p pid-core --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
    cargo run --locked -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl

# Build + test the Python bindings via maturin (needs: pip install maturin numpy pytest)
py-test:
    maturin develop --release --locked -m crates/pid-python/Cargo.toml
    pytest crates/pid-python/tests -q

# Version coherence (Cargo workspace version == CITATION.cff; CI also runs a tag mode on tag pushes)
version-check:
    scripts/check-version-coherence.sh

# Core local gates. CI additionally runs OS/Python matrices, a full-history secret scan,
# and the pinned MSRV check (`cargo +1.83 check --locked --workspace --all-features`).
ci: lint test test-parallel doc deny smoke version-check
