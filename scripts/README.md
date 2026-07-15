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
evidence. Its profile comparison fails closed on any unrecorded stable-namespace feature delta;
the current scoped profiles isolate feature-only additions under the experimental namespace.

## Review evidence, bounded algebra, and oracle checks

`check-review-evidence.py` keeps three deliberately bounded artifacts coherent. The canonical
`assurance-registry.json` covers exactly the 34 release-scope families across definition, exact
algebra, Rust refinement, floating-point/numerical behavior, and statistical/application validity;
every layer has a stable assurance ID, evidence tier, assumption with an owner and failure
consequence, and an explicit gap disposition. `task-dispositions.json` covers exactly `T000`
through `T158`, records the completed 0.9 source-review publication separately from 155 open and
four externally blocked 1.0 tasks, and fixes both claim-removed and qualified-complete counts at
zero. A neutral `NOT_QUALIFIED` state expressly does not issue the final 1.0 decision. Bounded work
implemented at the 0.9 milestone is recorded separately from full task qualification, including
the quantizer-hash, KSG-report, release-boundary, and algorithm-identifier tasks.
`FILE_REVIEW_LEDGER.csv` is a 21-column object-database inventory of all 186 files in the exact
`v0.9.0` tagged commit. Its rows are uniformly `UNASSIGNED` and
`INVENTORIED_NOT_REVIEWED`; the inventory never implies line review or independent completion.

The normal command validates canonical JSON, closed schemas, unique assurance/assumption/gap IDs,
the verified handoff-ledger identity and commit-lineage relationship, all evidence paths, immutable
tag identities, every tagged blob ID and SHA-256 digest, exact CSV
bytes, and the non-escalation boundaries. `--write` is the only supported way to regenerate the
three mechanical artifacts. The mutation suite removes and duplicates families/tasks/files,
changes evidence tiers and dispositions, escalates completion, alters digests, and invents review
metadata to prove those changes fail closed.
Regeneration additionally requires the locally retained handoff commit object so its recorded
non-ancestry can be checked directly. Ordinary clean-clone validation still binds the verified
handoff-ledger digest and checks that lineage whenever the older object is available.

`generate-sxpid2-exhaustive-oracle.py` independently rebuilds the committed high-precision corpus
for every nonempty binary two-source count table with total mass at most four. It uses only the
Python standard library and the published event-probability definition, does not import pid-rs or
its bindings, and makes no claim beyond that finite bound. The Rust integration test compares all
494 tables against the generated corpus.

`generate-ksg-local-arithmetic-oracle.py` independently rebuilds 8,198 exact-harmonic/Decimal
reference values for the KSG local digamma expression, exhaustively through 16 samples and across
fixed stress tuples through one million samples. The in-module Rust test compares every value; the
corpus bounds local arithmetic only and does not validate neighbor search, support, or an MI
estimate.

`check-z3-pid2-algebra.py` requires the exact 64-bit Z3 4.16.0 CLI and checks three digest-pinned
QF_LRA obligations: four-atom reconstruction, formula-level source exchange, and four-node
Möbius inversion followed by reconstruction. The mutation self-test changes each obligation to an
exactly satisfiable case and verifies rejection. These proofs cover only the stated two-source
exact-real formulas; they do not establish estimator premises, floating-point refinement, a Lean
development, or any three- or four-source lattice.

```text
python3 scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/generate-sxpid2-exhaustive-oracle.py
python3 scripts/check-review-evidence.py
python3 scripts/check-review-evidence-self-test.py
python3 scripts/check-z3-pid2-algebra.py
python3 scripts/check-z3-pid2-algebra-self-test.py

# Maintainer-only mechanical regeneration after an intentional source change:
python3 scripts/check-review-evidence.py --write
python3 scripts/generate-ksg-local-arithmetic-oracle.py --write
python3 scripts/generate-sxpid2-exhaustive-oracle.py --write
```

## `collect-repository-snapshot.py`

Collector v2 records full commits and trees, public HTTPS remotes, live remote HEAD/tag
projections, submodule/gitlink agreement, lock and toolchain digests, declared Rust versions,
exact Git dependency pins, contract-file digests, and the complete paginated public GitHub Release
projection. Authenticated draft releases are excluded so caller privileges do not change that
public projection. It never treats cached tracking refs or local tags as current remote evidence.
It brackets collection with matching live HEAD/tag and public-release projections and performs
clean/branch/commit/tree/origin checks both before and after local reads to reject ordinary
concurrent changes. Lock/toolchain/contract hashes and Cargo manifest projections are read from the
recorded `HEAD` tree, so sparse checkouts, symlink targets, and `assume-unchanged` worktree edits
cannot diverge those details from `tree_sha`. The paired checks cannot make several repositories
and remote APIs globally atomic or close a mutation immediately after the final check, so
collection still requires quiescent clones and records an observed cut rather than a transaction.
Collection time is stored in a separate envelope and therefore does not alter the snapshot digest.
Exactly `pid-rs` is `claimed_core`; downstream repositories are `not_claimed`.

The checked `audit/evidence/repository-snapshot.json` is the exact historical collector-v1 cut.
V1 used cached `origin/HEAD` and local tag refs; its digest is pinned and accepted only for
validation, never as newly collected live-remote evidence. Its command log, envelope, sidecar, and
human rendering remain the original v1 provenance. A v2 collection intentionally cannot compare
byte-for-byte equal to that v1 body.

```bash
scripts/collect-repository-snapshot.py \
  --validate audit/evidence/repository-snapshot.json
scripts/collect-repository-snapshot.py \
  --workspace /path/to/parent-containing-five-clean-clones \
  --output-dir /tmp/pid-rs-repository-snapshot-v2
scripts/check-repository-snapshot-self-test.sh
```

`--skip-github` is a test-only, explicit opt-in. A v2 body with skipped release state is rejected
by normal validation; validating such a fixture requires supplying `--skip-github` again. Release
evidence must omit that flag and contain the complete queried projection.

The self-test proves unchanged v2 reruns are byte-identical and rejects a dirty checkout, URL
rewriting, a stale tracking ref after the live origin advances, non-commit remote tags, a submodule
working tree that differs from its gitlink, abbreviated identities, incomplete cross-repository
checks (including omitted dependency pins and a misbound Prisoma gitlink), incorrect core claims,
unknown schema fields, stale release-projection hashes, unsorted/paginated/duplicate release inputs,
draft leakage, concurrent checkout and live-origin mutations, mismatched repository URLs, and
inconsistent head tags; it also proves a concealed worktree edit cannot perturb a `HEAD`-bound file
projection.

## Handoff-intake check

`check-handoff-intake.py` validates the canonical, SHA-256-bound record of the complete external
master handoff read at the 0.9 audit cut. The record preserves package hashes, read counts, the
159-task/3,180-open-lens state, defects found in the supplied process and oracle material, the
requested 0.9/no-DOI disposition, and work that still requires independent humans. It explicitly
cannot turn external review input into completion or signoff evidence.

```bash
scripts/check-handoff-intake.py
scripts/check-handoff-intake-self-test.py
```

The checker binds the complete canonical JSON digest, all six package identities, both package
manifest identities, the PID ledger identity, and the frozen repository commit. The self-test
recomputes sidecars after mutating each identity and proves those substitutions still fail.

## Release-state and version-coherence checks

`check-release-state.sh` enforces truthful public metadata across candidate, GitHub-only review,
finalized registry-source, and annotated-tag states. Candidate mode rejects a release date, final
tag, present-tense registry claim, or qualified downstream-integration claim. `review-source`
accepts only exact version 0.9.0 with coherent CFF/changelog dates, the exact GitHub-only
source-review wording, explicit crates.io/PyPI non-publication, no 1.x compatibility promise,
and no top-level software DOI or Zenodo identifier. It works in an extracted source archive without
`.git`; `review-tagged` reads the exact tag tree and additionally requires a directly annotated,
unsigned tag whose internal name matches the requested ref.

`final-source` and `tagged` retain the separately qualified registry-release contract. The former
works in an extracted source archive; the latter reads and verifies the annotated tag tree.
`check-version-coherence.sh` supplies the corresponding candidate, review-source, review-tagged,
final-source, and legacy one-argument tagged modes, adding locked workspace/package/dependency
coherence and exact sole-author checks across Cargo, CFF, and Python metadata. Release references
and workspace versions use exact SemVer numeric components (no leading zeroes), source modes reject
symlinked authoritative inputs, and the selector infers a local tag only from a clean worktree.

At the deliberate candidate-to-review transition, both `README.md` and `RELEASE_NOTES.md` must
contain these exact statements (Markdown emphasis may wrap the status statement without changing
its text):

```text
Release status: GITHUB-ONLY SOURCE-REVIEW PRERELEASE.
Distribution is GitHub-only: crates.io and PyPI are not published for this 0.9.0 review prerelease.
This 0.9.0 review prerelease makes no 1.x compatibility promise.
```

```bash
scripts/check-release-state.sh candidate
scripts/check-release-state.sh review-source v0.9.0
scripts/check-release-state.sh review-tagged v0.9.0
scripts/check-release-state.sh final-source v1.0.0
scripts/check-release-state.sh tagged v1.0.0

scripts/check-version-coherence.sh
scripts/check-version-coherence.sh review-source v0.9.0
scripts/check-version-coherence.sh review-tagged v0.9.0
scripts/check-version-coherence.sh final-source v1.0.0
scripts/check-version-coherence.sh v1.0.0

scripts/check-release-state-self-test.sh
```

The self-test proves all five states, including Git-free review/final source archives and exact
annotated review/final tags. It then injects candidate publication claims; review date, wording,
registry, compatibility, version, DOI, Zenodo, and multi-author defects; lightweight, nested,
misnamed, and signed tags; and final-source/tagged date mismatches, proving each is rejected.

The manual `review-release.yml` workflow accepts only `v0.9.0` at the exact dispatch-time `main`
commit. Immediately before dispatch, an administrator must query GitHub's repository settings API,
confirm that `GET /repos/sepahead/pid-rs/immutable-releases` returns `enabled: true`, and supply the
exact `immutability_preflight=ENABLED` acknowledgement. The standard workflow `GITHUB_TOKEN` cannot
repeat that Administration-read query, so this is an explicit out-of-band trust boundary: an
administrator must not disable immutability between the check and publication. The acknowledgement,
exact CI run attempt, generating workflow attempt, release name, and release-notes digest are bound
into the checksummed provenance asset. Publication downloads the exact Actions artifact ID and
digest from an attempt-qualified artifact name (so `upload-artifact@v4` reruns cannot collide),
rechecks both the remote annotated-tag object and peeled commit immediately before release
mutation, atomically republishes the exact name/body while making the draft public, and verifies the
automatic immutable-release attestation. If the published release unexpectedly remains mutable,
the same publication step and its exit trap attempt to delete that release before failing; an
abrupt runner or network loss can still prevent cleanup.

A retry after publication does not compare the earlier, attempt-specific provenance bytes with a
new workflow attempt. Instead it downloads the immutable release's exact six-asset set, regenerates
both checksum manifests, compares the deterministic source archive and scope records with the
tagged source, and validates every release/provenance identity field. The provenance-named original
attempt must be a strictly earlier attempt of the same workflow run; GitHub's Actions API must show
the repository owner as both actor and triggering actor and must show exactly one publication job
whose authorization, preflight, draft creation, byte verification, and publication steps each
succeeded. The provenance-named CI run attempt is independently required to be the successful tag
push run for the same commit. These server-side lineage checks prevent a writer-planted immutable release
with merely self-consistent assets from being accepted. Once a release has been observed
immutable, verification is read-only and never attempts release deletion; mutable cleanup belongs
only to the conditional publication step that created the draft.

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
lands on the wrong commit. Instead the script requires the canonical public HTTPS origin in both
the submodule and `.gitmodules`, queries the live tag object and peeled commit, rejects
lightweight, indirect, signed, or locally substituted tags, fetches only that object into a
temporary ref, and checks out the verified commit. It also refuses to mix pre-existing submodule,
gitlink, or root-lockfile changes into the operation. The pin is therefore independent of cached
local tags and mutable tracking refs, regardless of ancestry.

The lock refresh prefers `cargo update -p pid-core -p pid-runlog`, falling back to a plain
`cargo check` (never `--locked`, which would refuse a stale-by-design lock after a bump). Before
reporting success it verifies that the root lock contains exactly one `pid-core` and one
`pid-runlog` entry and that both equal the version encoded by the verified tag; a successful cargo
command that leaves the lock stale is therefore rejected.
`scripts/repin-pidrs-self-test.sh` exercises canonical/resolved remote identity, committed and
working-tree `.gitmodules`, dirty-state refusal, lightweight/indirect/misnamed/signed tag rejection,
tag/workspace version agreement, and stale-lock rejection without contacting or mutating a real
consumer checkout.

## License

Licensed under either of [MIT](../LICENSE-MIT) or [Apache-2.0](../LICENSE-APACHE) at your option.
