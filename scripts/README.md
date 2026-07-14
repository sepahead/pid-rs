# scripts

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Operational helper scripts for maintaining **pid-rs** and its downstream consumers.

## Release-scope checks

`check-release-scope.py` makes canonical, schema-validated `release-scope-1.0.json` authoritative
over the rendered `RELEASE_SCOPE_1_0.md`. It parses every direct `pid-core` re-export and public
module declaration, checks even symbol-empty parent modules, verifies Cargo feature closure and
every committed API-snapshot digest, compares the exact stable-namespace signature diff for every
complete activation profile, and requires an explicit `not_claimed` record for each optional
ecosystem integration. Its mutation tests include out-of-line modules, parent-module exports,
public extern crates, exported macros, combined-feature API, snapshot-source, approval-binding,
feature, SemVer, schema, profile, conditional-leak, path, and duplicate-key failures.

`check-public-api-snapshots.sh` independently rebuilds all ten feature profiles (including a true
`--all-features` profile) with `cargo-public-api 0.52.0` and the exact nightly recorded in the
machine scope. It first rebuilds the exact historical source commit recorded by the scope and then
the working tree under review, comparing both sets of signatures byte-for-byte. It does not rewrite
the snapshots. Its self-test adds a public method in an internal source module without touching
`lib.rs` and proves the compiled signature changes.

```bash
python3 scripts/check-release-scope.py
scripts/check-release-scope-self-test.sh
scripts/check-public-api-snapshots.sh
scripts/check-public-api-snapshots-self-test.sh
```

The scope is a release-candidate claim boundary, not reviewer approval or scientific-validation
evidence. The disclosed stable-namespace leaks must be removed before the API freeze can close.

## `collect-repository-snapshot.py`

Collects the exact clean repository cut that anchors the 1.0 audit. The canonical snapshot records
full commits and trees, public HTTPS remotes, submodule/gitlink agreement, lock and toolchain
digests, declared Rust versions, exact Git dependency pins, contract-file digests, tags, and public
GitHub Release state. Collection time is stored in a separate envelope and therefore does not alter
the snapshot digest. Downstream repositories are recorded as `not_claimed` for the core-only
release.

```bash
scripts/collect-repository-snapshot.py \
  --workspace /path/to/parent-containing-five-clean-clones \
  --compare audit/evidence/repository-snapshot.json
scripts/collect-repository-snapshot.py \
  --validate audit/evidence/repository-snapshot.json
scripts/check-repository-snapshot-self-test.sh
```

The self-test proves unchanged reruns are byte-identical and rejects a dirty checkout, a submodule
working tree that differs from its gitlink, and an abbreviated commit SHA.

## `check-release-state.sh`

Enforces truthful public metadata across candidate, extracted-final-source, and annotated-tag
states. Candidate mode rejects a release date, final tag, present-tense registry claim, or qualified
downstream-integration claim. `final-source` validates finalized version/date/link metadata in an
extracted release archive without requiring `.git`; tagged mode applies the same checks to the
annotated tag tree and additionally verifies the tag object.

```bash
scripts/check-release-state.sh candidate
scripts/check-release-state.sh final-source v0.9.0
scripts/check-release-state.sh tagged v0.9.0
scripts/check-release-state-self-test.sh
```

The self-test proves valid candidate, Git-free final-source, and annotated-tag states are accepted,
then injects a fictitious candidate release date, an unqualified registry claim, and isolated
final-source/tagged CFF-versus-changelog date mismatches and proves that each is rejected.

## `generate-csxpid-reference.py`

Regenerates the machine-readable continuous-SxPID cross-validation fixture used by the
`pid-core` bivariate and trivariate estimator tests. The upstream implementation is the public
package linked by Ehrlich et al. (2024), pinned to commit
`7bb984611a422cf7944ece68993fe3a27e2eadec`. The script rejects a different or dirty checkout and
an unpinned Python environment before importing upstream code.

```bash
git clone https://gitlab.gwdg.de/wibral/continuouspidestimator.git /tmp/continuouspidestimator
git -C /tmp/continuouspidestimator checkout --detach 7bb984611a422cf7944ece68993fe3a27e2eadec

uv venv --python 3.10 /tmp/csxpid-venv
uv pip install --python /tmp/csxpid-venv/bin/python \
  numpy==1.23.1 scipy==1.8.1 mpmath==1.2.1 setuptools==63.2.0

/tmp/csxpid-venv/bin/python scripts/generate-csxpid-reference.py \
  --csxpid-checkout /tmp/continuouspidestimator
/tmp/csxpid-venv/bin/python scripts/generate-csxpid-reference.py \
  --csxpid-checkout /tmp/continuouspidestimator --check
```

The tracked fixture contains the complete deterministic inputs, upstream estimates in bits, their
conversion to pid-rs's nats, the backend and environment pins, and the upstream source revision.
Its `.sha256` sidecar covers the complete JSON artifact; the current digest is
`d952e742879cb83bcdd2c46b779a9b90d9ee0729917a0fb312ad8d1918a40536`.

## `verify-package-archives.sh`

Builds and tests the exact `pid-runlog` and `pid-core` Cargo package archives without publishing
anything. This closes the initial-release dependency-order gap: before `pid-runlog 0.9.0` exists
on crates.io, ordinary `cargo package -p pid-core` refuses to resolve it. The script instead
creates a temporary local registry from the checked-in lockfile, seeds that registry with the
freshly verified `pid-runlog` archive, runs Cargo's normal `pid-core` package verification, then
unpacks the exact core archive and compiles every shipped target with every feature, locked and
offline.

It requires the pinned registry helper used by CI:

```bash
cargo install cargo-local-registry --locked --version 0.2.12
scripts/verify-package-archives.sh
```

The temporary registry is deleted on exit. The script neither publishes nor contacts an upload
endpoint. A true crates.io `cargo publish --dry-run -p pid-core` remains intentionally sequenced
after `pid-runlog` registry visibility in the release workflow.

## `repin-pidrs.sh`

Bumps `prisoma`'s `pid-rs` git submodule to a target **pid-rs tag** and refreshes
`prisoma`'s root `Cargo.lock` so the `pid-core` / `pid-runlog` path-deps re-resolve to the
new version. It stages the gitlink (`git add pid-rs`) and the refreshed lock, then prints a
suggested commit — it does **not** commit or push.

```bash
# Pin prisoma's pid-rs submodule to tag v0.9.0 (sibling prisoma layout, auto-detected):
scripts/repin-pidrs.sh v0.9.0

# Or point at an explicit prisoma checkout:
scripts/repin-pidrs.sh v0.9.0 /path/to/prisoma
```

**Why an explicit fetch + checkout, never `git submodule update --remote`:** `prisoma`'s
`pid-rs` submodule history *diverged* from canonical `sepahead/pid-rs` — the prior pin was
not an ancestor of canonical `main`. `git submodule update --remote` resolves the branch tip
recorded in `.gitmodules` and fast-forwards; with a diverged history that either fails or
lands on the wrong commit. Instead the script does `git fetch origin --tags --force` and
`git checkout --detach refs/tags/<tag>`, which pins the requested tag by name unambiguously,
regardless of ancestry.

The lock refresh prefers `cargo update -p pid-core -p pid-runlog`, falling back to a plain
`cargo check` (never `--locked`, which would refuse a stale-by-design lock after a bump).

## License

Licensed under either of [MIT](../LICENSE-MIT) or [Apache-2.0](../LICENSE-APACHE) at your option.
