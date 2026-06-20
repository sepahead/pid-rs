<!-- Thanks for contributing to pid-rs! Please skim CONTRIBUTING.md (numerical conventions + test commands) first. -->

## Summary

<!-- What does this PR change, and why? -->

## Checklist

Mirrors the CI jobs in [`.github/workflows/ci.yml`](workflows/ci.yml); running these locally first avoids a red PR.

- [ ] `cargo fmt --all --check` passes
- [ ] `cargo clippy --workspace --all-targets -- -D warnings` is clean
- [ ] `cargo test --workspace --exclude pid-python` passes (`pid-python` is a PyO3 module, exercised separately via `maturin` + `pytest`)
- [ ] If `pid-core`'s parallel path could be affected: `cargo test -p pid-core --features parallel` passes and `cargo clippy -p pid-core --all-targets --features parallel -- -D warnings` is clean (results must stay **bit-identical** to the serial path)
- [ ] Docs build clean: `RUSTDOCFLAGS="-D warnings" cargo doc --workspace --no-deps --exclude pid-python`
- [ ] Still builds on the MSRV (Rust 1.80): `cargo +1.80 check --workspace`
- [ ] Tests added/updated (prefer an analytic ground-truth check for estimator changes — Gaussian-channel MI, XOR = pure synergy, COPY = pure redundancy, independence → 0)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] If `pid-python` changed: `maturin develop --release -m crates/pid-python/Cargo.toml && pytest crates/pid-python/tests -q` passes

## Numerical impact

<!-- Does this change any numerical result? If so, explain why the new value is correct
     (cite a paper or an analytic value), and note that all information quantities are in **nats**.
     If a PID atom changes, confirm the Möbius identity Red + Unq1 + Unq2 + Syn = I(S1,S2;T) still
     holds. If nothing numerical changes, write "none". -->

## Related issues

<!-- e.g. "Closes #123". Optional. -->
