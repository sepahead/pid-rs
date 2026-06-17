# Contributing to pid-rs

Thanks for your interest in improving pid-rs! Contributions of all kinds are welcome — bug
reports, documentation, tests, and code.

## Ground rules

- Be respectful. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- This is a **scientific** library: correctness and reproducibility come first. A change that
  alters a numerical result must explain *why* the new value is correct (ideally against an
  analytic ground truth or a cited paper), not merely that tests still pass.

## Development

```bash
git clone https://github.com/sepehrmn/pid-rs
cd pid-rs

cargo test --workspace --all-features      # tests
cargo fmt --all                            # format
cargo clippy --workspace --all-targets -- -D warnings   # lint (must be clean)
cargo run --release --example ksg_and_pid  # worked example
cargo doc --workspace --no-deps --open     # docs
```

Optional but encouraged:

```bash
cargo deny check         # supply-chain / license check (see deny.toml)
```

## Pull requests

1. Open an issue first for anything non-trivial, so we can agree on the approach.
2. Keep PRs focused; one logical change per PR.
3. Add or update tests. For estimators, prefer a test against a **known analytic value**
   (Gaussian-channel MI, XOR = pure synergy, COPY = pure redundancy, independence → 0) over a
   self-consistency check.
4. Run `cargo fmt`, `cargo clippy -- -D warnings`, and `cargo test` before pushing.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Numerical conventions (please preserve)

- All information quantities are in **nats**.
- MI terms that feed PID identities must be computed with `NegativeHandling::Allow` (clamping a
  term before a subtraction breaks `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`).
- Accumulations over count maps must be **order-deterministic** (use `BTreeMap`/sorted keys, not
  `HashMap`) so results are bit-reproducible.

## Licensing of contributions

Unless you state otherwise, any contribution you submit is dual-licensed under
**MIT OR Apache-2.0**, matching the project license.
