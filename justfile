# Development tasks for pid-rs — executable mirror of the canonical commands in AGENTS.md.
# Install `just`: https://github.com/casey/just   (then run `just` to list recipes)

# List available recipes
default:
    @just --list

# Full workspace test suite (pid-python is tested via maturin; see `py-test`)
test:
    cargo test --workspace --exclude pid-python

# The exact data-parallel kNN path (must stay bit-identical to serial)
test-parallel:
    cargo test -p pid-core --features parallel

# Format check + clippy (mirrors CI's lint gate)
lint:
    cargo fmt --all --check
    cargo clippy --workspace --exclude pid-python --all-targets -- -D warnings
    cargo clippy -p pid-core --all-targets --features parallel -- -D warnings

# Auto-format the tree
fmt:
    cargo fmt --all

# Build docs with warnings denied
doc:
    RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --exclude pid-python

# Estimator benchmarks
bench:
    cargo bench -p pid-core

# Supply-chain audit (advisories + licenses + bans + sources)
deny:
    cargo deny check

# The worked examples
examples:
    cargo run --release --example ksg_and_pid
    cargo run --release --example discrete_sxpid

# exp0 diagnostic + run-log round-trip smoke
smoke:
    cargo run -p pid-core --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl
    cargo run -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl

# Build + test the Python bindings via maturin (needs: pip install maturin numpy pytest)
py-test:
    maturin develop --release -m crates/pid-python/Cargo.toml
    pytest crates/pid-python/tests -q

# Everything CI runs, except the Python job
ci: lint test test-parallel doc deny smoke
