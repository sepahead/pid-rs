<!-- Thanks for contributing to pid-rs! Please skim CONTRIBUTING.md (numerical conventions + test commands) first. -->

## Summary

<!-- What does this PR change, and why? -->

## Method provenance

<!-- If a method, estimator, diagnostic, workflow, or binding changes, identify it as
     paper-defined, paper-derived, project-defined, external reference code, or no implementation,
     and update method-catalog.json / generated METHODS.md. “New in pid-rs” means new repository
     implementation/API/engineering, not a claim of scientific novelty. Write "not applicable" if
     this PR has no method-surface effect. -->

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
- [ ] `python3 scripts/check-method-catalog.py` passes; affected paper/code/origin entries and source markers are updated
- [ ] Tests added/updated (prefer independent ground truth for estimator changes — Gaussian-channel MI; Williams–Beer $I_{\min}$ XOR/redundant-copy fixtures; shared-exclusions reference atoms; mutual information of independent variables equals 0)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] If `pid-python` changed: `maturin develop --release --locked -m crates/pid-python/Cargo.toml && pytest crates/pid-python/tests -q` passes

## Numerical impact

<!-- Does this change any numerical result? If so, explain why the new value is correct
     (cite a paper or an analytic value), and note that all information quantities are in **nats**.
     If a PID atom changes, confirm the Möbius identity Red + Unq1 + Unq2 + Syn = I(S1,S2;T) still
     holds. If nothing numerical changes, write "none". -->

## Related issues

<!-- e.g. "Closes #123". Optional. -->
