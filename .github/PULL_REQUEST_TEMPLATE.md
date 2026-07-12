<!-- Thanks for contributing to pid-rs! Please skim CONTRIBUTING.md (numerical conventions + test commands) first. -->

## Summary

<!-- What does this PR change, and why? -->

## Checklist

Covers most locally reproducible core gates in [`.github/workflows/ci.yml`](https://github.com/sepahead/pid-rs/blob/main/.github/workflows/ci.yml). GitHub also runs the OS/Python matrix and a full-history secret scan.

- [ ] `cargo fmt --all --check` passes
- [ ] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings` is clean
- [ ] `cargo test --locked --workspace --exclude pid-python` passes (`pid-python` is a PyO3 module, exercised separately via `maturin` + `pytest`)
- [ ] `pid-core` passes `--no-default-features`, `--features parallel`, every changed individual research feature, `--all-features`, and selected `--release` fixtures (parallel stays **bit-identical**)
- [ ] Docs build clean: `RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps`
- [ ] Still builds on the MSRV (Rust 1.89): `cargo +1.89 check --locked --workspace --all-features`
- [ ] `cargo deny --all-features --locked check` passes with no advisory exception
- [ ] Relevant deterministic property tests and fixed fuzz targets pass; resource/known-failure cases were added when applicable
- [ ] `cargo package --list`, version coherence, semver, and package/wheel contents were reviewed
- [ ] `scripts/check-version-coherence.sh` and the `exp0` + run-log replay smoke in `CONTRIBUTING.md` pass
- [ ] Tests added/updated (prefer independent ground truth for estimator changes — Gaussian-channel MI; Williams–Beer `I_min` XOR/redundant-copy fixtures; shared-exclusions reference atoms; independence → 0)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] If `pid-python` changed: `maturin develop --release --locked -m crates/pid-python/Cargo.toml && pytest crates/pid-python/tests -q` passes

## Numerical impact

<!-- Does this change any numerical result? If so, explain why the new value is correct
     (cite a paper or an analytic value), and note that all information quantities are in **nats**.
     If a PID atom changes, confirm the Möbius identity Red + Unq1 + Unq2 + Syn = I(S1,S2;T) still
     holds. If nothing numerical changes, write "none". -->

## Related issues

<!-- e.g. "Closes #123". Optional. -->
