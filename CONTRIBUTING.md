# Contributing to pid-rs

Thanks for your interest in improving pid-rs! Contributions of all kinds are welcome — bug
reports, documentation, tests, and code.

## Ground rules

- Be respectful. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- This is a **scientific** library: correctness and reproducibility come first. A change that
  alters a numerical result must explain *why* the new value is correct (ideally against an
  analytic ground truth or a cited paper), not merely that tests still pass.
- **“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
  this repository; it is not a claim of scientific novelty.** Keep
  [`method-catalog.json`](method-catalog.json), its generated [`METHODS.md`](METHODS.md) rendering,
  and source-level method markers aligned. Distinguish paper-defined methods, paper-derived
  compositions, project-defined work, external reference code, and requests with no implementation.
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
python3 scripts/check-method-catalog.py  # method/paper/code/provenance coherence
python3 scripts/check-ecosystem-capabilities.py  # historical consumer capability/gap coherence
python3 scripts/check-ecosystem-capabilities-self-test.py  # fail-closed contract mutations
python3 scripts/check-software-identity.py  # identity/schema/feature/digest/package coherence
python3 scripts/check-software-identity-self-test.py  # fail-closed identity mutations
python3 scripts/check-release-scope.py  # scope/symbol/signature-registry coherence
scripts/check-release-scope-self-test.sh  # fail-closed scope/history mutations
scripts/check-public-api-snapshots.sh  # rebuild all immutable declaration snapshots
```

The method-catalog, ecosystem-capability, software-identity, and release-scope checkers and their
mutation self-tests require Python 3.11 or newer for the standard-library `tomllib` module.

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
3. Classify every affected method in the canonical catalog. A paper citation does not by itself
   make a repository composition paper-defined, and Python/API availability does not imply
   estimator validity. State whether external reference code exists or no implementation is
   provided.
4. If public identity or API evidence changes, keep the typed Rust/Python surface, identity schema
   and manifest, exact feature inventory, method catalog, signature-revision registry, immutable
   release-scope profile snapshots, generation metadata, and exact-byte forensic hashes coherent.
   The software-identity contract is project-defined infrastructure with no estimator-paper or
   attestation claim.
   If a change affects a recorded historical consumer need, update
   [`ecosystem-capabilities.json`](ecosystem-capabilities.json) and its generated
   [`ECOSYSTEM_CAPABILITIES.md`](ECOSYSTEM_CAPABILITIES.md). Do not infer current integration or
   application validity from that historical projection.
5. If the change adds or revises a mathematical or statistical claim, use the
   [mathematical problem-solving workflow](MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md). Link its
   versioned claim packet, assumptions, falsifiers, evidence class, completion criterion, retained
   invalidated approaches, route memos, applicable semantic-closure domain, exceptional cases,
   claim-to-evidence classes, and open go/no-go gates. Model output cannot close an obligation
   without replayable evidence. For a blind benchmark, freeze the commitment and record independent
   time evidence before holdout access.
6. Add or update tests. For estimators, prefer a test against a **known analytic value**
   (Gaussian-channel MI; Williams–Beer $I_{\min}$ XOR pure synergy and redundant-copy pure
   redundancy; shared-exclusions reference atoms; mutual information of independent variables
   equals 0) over a
   self-consistency check.
7. Run the locked test, lint, docs, MSRV, supply-chain, method-catalog, and software-identity
   commands above before
   pushing.
8. Update `CHANGELOG.md` under `[Unreleased]`.

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
1.x compatibility promise and carries no software DOI or Zenodo record. The exhaustive
paper/code/origin boundary is [`METHODS.md`](METHODS.md), not a release-status inference.

## Numerical conventions (please preserve)

- All information quantities are in **nats**.
- MI terms that feed PID identities must be computed with `NegativeHandling::Allow`. Clamping a
  term before a subtraction breaks this identity:

  $$
  \mathrm{Red}+\mathrm{Unq}_1+\mathrm{Unq}_2+\mathrm{Syn}
  =I(S_1,S_2;T).
  $$
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
