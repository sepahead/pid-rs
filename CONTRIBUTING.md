# Contributing to pid-rs

Thanks for your interest in improving pid-rs! Contributions of all kinds are welcome — bug
reports, documentation, tests, and code.

## Ground rules

- Be respectful. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- This is a **scientific** library: correctness and reproducibility come first. A change that
  alters a numerical result must explain *why* the new value is correct (ideally against an
  analytic ground truth or a cited paper), not merely that tests still pass.
- Found a security issue? Do **not** open a public issue — follow [SECURITY.md](SECURITY.md) instead.

## Development

```bash
git clone https://github.com/sepahead/pid-rs
cd pid-rs

cargo test --locked --workspace --exclude pid-python  # tests (mirror CI)
cargo test --locked -p pid-core --no-default-features # approved stable default surface
cargo test --locked -p pid-core --features parallel    # exact data-parallel path
cargo test --locked -p pid-core --all-features         # default-off research surfaces
cargo fmt --all                            # format
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings  # lint every surface
cargo run --locked --release -p pid-core --features experimental-continuous --example ksg_and_pid  # experimental PID2 worked example
cargo run --locked -p pid-core --all-features --bin exp0 -- --seeds 1 --summary-json /tmp/summary.json --runlog /tmp/run.jsonl  # exp0 diagnostic + run-log
cargo run --locked -p pid-runlog --bin pid-runlog-replay -- --validate /tmp/run.jsonl  # replay/validate the run-log
RUSTDOCFLAGS="-D warnings" cargo doc --locked -p pid-core --no-default-features --no-deps  # stable docs
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps  # full docs
cargo +1.89 check --locked --workspace --all-features  # minimum supported Rust version
cargo deny --all-features --locked check  # required supply-chain / license gate
```

`pid-python` is a PyO3 extension module. It is excluded from the plain workspace test because that
path can depend on a host `libpython` and supplies no binding coverage; it remains included in
rustdoc. Exercise the real API via `maturin`. The quickest local loop uses `maturin develop`; CI
instead builds a wheel and installs
it (`maturin build --release --locked --manifest-path crates/pid-python/Cargo.toml --out dist` then
`pip install --no-index --find-links dist pid-core-rs`), but both run the same pytest suite:

```bash
pip install maturin numpy pytest
maturin develop --release --locked -m crates/pid-python/Cargo.toml
pytest crates/pid-python/tests -q
```

## Pull requests

1. Open an issue first for anything non-trivial, so we can agree on the approach.
2. Keep PRs focused; one logical change per PR.
3. Add or update tests. For estimators, prefer a test against a **known analytic value**
   (Gaussian-channel MI; Williams–Beer `I_min` XOR pure synergy and redundant-copy pure
   redundancy; shared-exclusions reference atoms; independence → 0) over a
   self-consistency check.
4. Run the locked test, lint, docs, MSRV, and supply-chain commands above before pushing.
5. Update `CHANGELOG.md` under `[Unreleased]`.

## Release policy

The release checklist and clean-room commands are in
[`RELEASE_REPRODUCTION.md`](RELEASE_REPRODUCTION.md). The 0.9 source-review release is a
GitHub-only source prerelease: its attached payload is limited to source, proposed-1.0 scope records,
review provenance, and SHA-256/SHA-512 manifests. It does not publish to crates.io, PyPI, or docs.rs,
and it does not contain packages, wheels, binaries, SBOMs, or separate build-provenance
attestations. Earlier release commits remain reachable through immutable changelog links, while the
obsolete pre-review tag refs have been retired. The published prerelease must
use GitHub release immutability, contain exactly the six documented attached files, remain outside
the latest-production slot, and expose GitHub's automatic signed release attestation.

Repository tags are annotated but deliberately unsigned. The later registry-publication workflow
is a separate qualification path: it requires reproducible packages, SBOMs, build-provenance
attestations, detached human sign-off records, protected-environment review, and public-registry
verification. Do not invoke that heavyweight path or describe it as completed evidence for the 0.9
source prerelease.

Do not call an experimental feature stable merely because its code is included in a review or
future release archive. The proposed scientific boundary is the table in
[`README.md`](README.md#proposed-10-scientific-status-09-review-surface), and every release must
include [`KNOWN_LIMITATIONS.md`](KNOWN_LIMITATIONS.md) in its tagged source. Version 0.9 makes no
1.x compatibility promise and carries no software DOI or Zenodo record.

## Numerical conventions (please preserve)

- All information quantities are in **nats**.
- MI terms that feed PID identities must be computed with `NegativeHandling::Allow` (clamping a
  term before a subtraction breaks `Red + Unq1 + Unq2 + Syn = I(S1,S2;T)`).
- Accumulations over count maps must be **order-deterministic** (use `BTreeMap`/sorted keys, not
  `HashMap`) so results are bit-reproducible.
- `exp0` is a **diagnostic gate**, not a pass/fail test: it reports a scoped `GO`/`NO-GO`
  high-dimensional MI/coherence verdict and a separate, non-gating `GO`/`PIVOT` geometry
  disposition, and **exits 0 by default**. These findings are expected at high dimensions (the
  default sweep deliberately reaches dimension 256 at n=500, where kNN MI is known to break down),
  and its monotonicity/invariant checks use scale-aware tolerances. Atom-measure validation remains
  `not_adjudicated` and atom-estimator validation remains `blocked`; neither is inferred from the MI
  verdict. CI runs `exp0` without `--strict-gate`, so it does not enforce a GO; `--strict-gate`
  implies `--strict-band` and enforces `GO` (exit
  code 3 otherwise) **only on the curated analytic band** — a d=1, n=4000 jointly-Gaussian grid
  whose MI terms are checked against their Cover–Thomas closed forms — never on the default
  high-dimensional sweep.

## Licensing of contributions

Unless you state otherwise, any contribution you submit is dual-licensed under
**MIT OR Apache-2.0**, matching the project license.
