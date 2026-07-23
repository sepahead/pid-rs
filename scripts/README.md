# scripts

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Operational helper scripts for maintaining **pid-rs** and its downstream consumers.

## Release-scope checks

`check-release-scope.py` makes canonical, schema-validated `release-scope-1.0.json` authoritative
over the rendered `RELEASE_SCOPE_1_0.md`. It parses every direct `pid-core` re-export and public
module declaration, checks even symbol-empty parent modules, verifies Cargo feature closure and
every committed API-snapshot digest, compares the exact stable-namespace signature diff for every
complete activation profile, and requires an explicit `not_claimed` record for each optional
ecosystem integration. It also binds the embedded public Rust declaration-signature epoch/revision
to a repository-history-relative registry containing the exact source commit/tree, immutable
revision-scoped profile paths and digests, and the generation host/rustdoc target/tool/toolchain/
format. The
checker examines the source anchor, HEAD, every direct HEAD parent, and every commit that
`git rev-list --full-history HEAD -- <registry-path>` reports. Each retained registry must be an
exact prefix of the current registry, and comparable reachable states must preserve one another;
the source-to-evidence boundary appends at most one contiguous record. Source commits advance
monotonically by Git ancestry, and only the immutable revision-1 source may lack a historical
registry. For each snapshot path, the checker examines its binding commits, HEAD and every direct
HEAD parent, and every commit in its own full path history. Once a committed registry binding is an
ancestor of a checked state, the path must exist with the exact registered byte digest. Earlier
pre-binding path states and a path first bound only by the current uncommitted registry remain
outside that historical interval; current working-tree bytes are still checked exactly. These
claims cover the complete non-shallow history reachable from the checked HEAD. They do not cover a
never-merged branch that is no longer reachable, deleted references, or an externally replaced
repository history without an independent witness. This is not a cryptographic signature,
transparency log, or external timestamp. Its mutation tests include out-of-line modules,
parent-module exports, public extern crates, exported macros, combined-feature API, snapshot-source,
approval-binding, feature, SemVer, schema, profile, conditional-leak, generic-impl classification,
full-match patterns, non-finite JSON, path, duplicate-key, registry-digest, profile-evidence,
source-binding, identity-binding, ordering, canonical encoding, buried truncation/reissue,
merge-side drop/reissue, snapshot modification/deletion/rename restoration, merged-side snapshot
mutation, multi-parent history, valid pre-binding history, and uncommitted-genesis evidence.
Every Git evidence query uses a scrubbed environment: ambient repository/worktree/object/config,
namespace, shallow-file, replacement, and pathspec routing is removed; default replacement refs
and graft overlays are disabled; and Git's canonical worktree root must equal the repository whose
current files are checked. The history claim still remains relative to the repository objects and
references actually present, not to an external transparency witness.

`check-public-api-snapshots.sh` independently rebuilds all ten feature profiles (including a true
`--all-features` profile) with `cargo-public-api 0.52.0` and the exact nightly recorded in the
machine scope. The recorded host triple identifies the original generation host; it is not forced
onto the checker. The separate rustdoc target triple is passed explicitly on every regeneration.
CI deliberately regenerates that target on its current Linux host and requires identical bytes,
adding one cross-host reproducibility check without claiming build-host portability. The script
first rebuilds the exact historical source commit recorded by
the scope and then the working tree under review, comparing both sets of signatures byte-for-byte.
Every source/profile pair uses a distinct Cargo target directory so same-version build artifacts
cannot cross the evidence boundary. The checker does not rewrite the snapshots. Its self-test adds
a public method in an internal source module without touching `lib.rs` and proves the compiled
signature changes.

```bash
python3 scripts/check-release-scope.py
scripts/check-release-scope-self-test.sh
scripts/check-public-api-snapshots.sh
scripts/check-public-api-snapshots-self-test.sh
```

`materialize-public-api-source.sh` is the internal literal-tree boundary used by that gate. It
binds the canonical worktree and recorded commit tree while disabling ambient Git routing,
configuration, replacement/graft overlays, lazy fetching, and alternate ref backends. The
self-test installs a real replacement ref and proves that retained source bytes remain literal.
Git 2.45 or newer is required; effective `export-ignore`/`export-subst` attributes, tracked symbolic
links, and Git submodule entries are rejected because `git archive` cannot otherwise serve as a
literal, confined source-tree materializer. Raw retained bytes and executable modes are checked
without applying Git clean/text filters. Archive extraction also clears tar option variables.
Snapshot generation rejects Cargo configuration in the source directory or any ancestor and clears
the build environment to a documented minimal allowlist (tool paths/home, temporary directory,
locale/timezone, and network-proxy routing) before selecting its own Cargo home and target. A
scrubbed `cargo metadata --locked` preflight rejects stale or missing locks, and lock bytes must
remain unchanged through every declaration build.

The scope is a release-candidate claim boundary, not reviewer approval or scientific-validation
evidence. Its profile comparison fails closed on any unrecorded stable-namespace feature delta;
the current scoped profiles isolate feature-only additions under the experimental namespace.

The evidence update is intentionally two-phase. The registry's source commit contains the code
whose declarations are captured; the following evidence commit adds the immutable snapshot bytes
and registry entry. Consequently, `git show <source-commit>:<snapshot-path>` is not the verification
rule and may report a missing or older file. `check-public-api-snapshots.sh` instead rebuilds the
source commit with the recorded toolchain and tool on the checker's current host, then compares
that output with the retained snapshot bytes. Keep the two commits adjacent, run the complete gate
on the evidence commit, and push them together; the source anchor alone is not a release candidate.

For a later declaration-evidence revision:

1. Update the public code and embedded epoch/revision/scope/status, then commit that exact source
   anchor without rewriting earlier registry entries or immutable snapshot files.
2. Generate every activation profile into a new revision-scoped directory using the recorded
   nightly and `cargo-public-api` version.
3. Append one registry record with the source commit/tree, generation metadata, profile paths, and
   exact digests; update the canonical release scope and any source/schema constants it binds.
4. Update the method catalog and software-identity reference hashes, regenerate `METHODS.md`,
   `RELEASE_SCOPE_1_0.md`, and assurance evidence, then run all checker mutation suites and the
   ten-profile rebuild before committing the evidence update.

The genesis commit/tree constants are permanent for registry schema revision 1. The history and
ancestry checks require a complete, non-shallow checkout of the objects reachable from HEAD;
shallow clones and source archives cannot perform this gate without fetching the recorded commits.
Fetching reachable history still cannot recover an unmerged branch whose references and objects
are absent or detect wholesale replacement without an independently retained remote or witness.

## Software-identity checks

`check-software-identity.py` validates the closed, canonical identity reference embedded in every
`pid-core` build. It keeps public Rust declaration-signature epoch/revision/profile scope/status,
the exact Cargo feature inventory, Cargo-package versus layout-matched-workspace source states, and the
explicit absence of binary attestation separate. Its two SHA-256 references bind the exact raw
canonical repository-file bytes of the method catalog and proposed release scope for forensic
comparison only. Layout-matched workspace builds verify those current files; package builds carry
the manifest values and need not contain or re-verify the repository-relative paths. Matching them
does not establish API compatibility, estimator validity, application validity, data quality, or
executable equality.

The checker rejects duplicate keys, unknown fields, unsafe paths, symlinks, stale or noncanonical
referenced JSON, feature drift, digest-domain substitution, a detached build-script manifest, and
package archives that omit identity sources. For the Python stub it checks every identity
`TypedDict` base and field, the exact root and stable return graph, special-form import provenance,
the zero-argument/root and self-only/stable call shapes, the stable alias, and public exports;
decorators, executable bodies, protected-name shadowing, conditional redefinitions, and non-field
record bodies fail closed. The mutation suite exercises those
failures and the Rust integration tests additionally cover malformed Cargo metadata, unrelated
enclosing Git repositories, symlink escapes, exact source-commit binding, and stable
serialization. Python tests require the nested dictionary, derived from Rust serialization, to
match the closed field and state contract.

```text
python3 scripts/check-software-identity.py
python3 scripts/check-software-identity-self-test.py
```

## Method-catalog checks

`check-method-catalog.py` keeps [`method-catalog.json`](../method-catalog.json), the generated
[`METHODS.md`](../METHODS.md) rendering, source-level catalog markers, release-scope family links,
feature names, implementation paths, and external-reference/unsupported declarations coherent.
The catalog distinguishes paper-defined methods, paper-derived compositions, project-defined work,
external reference code, and requests with no implementation. The checker also binds every
deprecated migration callable to its exact scientific owner rows and requires an experimental
composition to name any research-only dependency boundary in its constraints. Intentionally
unmapped CLI/run-log/composed rows have exact entry-point policies rather than escaping namespace
validation.

The checker and its mutation self-test require Python 3.11 or newer because they read Cargo
manifests with the standard-library `tomllib` module.

**“New in pid-rs” means implementation, API, composition, diagnostic, or engineering work new to
this repository; it is not a claim of scientific novelty.** Passing the checker establishes
internal metadata and path coherence only; it does not establish a theorem, literature priority,
estimator validity, or independent review.

```text
python3 scripts/check-method-catalog.py
python3 scripts/check-method-catalog-self-test.py
```

## Review evidence, bounded algebra, and oracle checks

`check-review-evidence.py` keeps three deliberately bounded artifacts coherent. The canonical
`assurance-registry.json` covers exactly the 35 release-scope families across definition, exact
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

`generate-finite-alphabet-plugin-oracle.py` independently rebuilds a 100-digit Decimal corpus for
the listed two-, three-, and four-source SxPID tables and the listed two- and three-source `I_min`
tables. It also includes minimum-tie crossings and realization-key changes. The generator uses
direct published definitions and a generic finite-poset inversion. It imports no pid-rs code or
third-party package. The default command rejects stale fixture bytes, a stale fixture digest, or a
stale embedded generator identity. The Rust test binds the fixture, generator identity, definition
status, tested-code paths, and limitations. It separately checks fixed-quantizer wrapper equality
against direct categorical calls. This is bounded software evidence. It is not an asymptotic proof,
a portable binary64 error theorem, or external review.

`generate-dependency-colored-sxpid-oracle.py` rebuilds the dependency-colored SxPID challenge
corpus. It uses exact rational arithmetic for finite probability and count identities and
100-digit Decimal arithmetic for logarithms. It enumerates the finite-field
pairwise-independence counterexample, copied colors, singleton colors, adaptive coloring, support
deletion, an unspecified-mixing construction, a generic net-weight range extremizer,
univariate-marginal control, and new support. It also
checks class-size constants, the
telescoping error allocation, all displayed bounds on four committed two-source law pairs, and one
fixed-width overlapping-window population law. One full-support pair is a bounded near-tightness
challenge for the one-$\Lambda$ synergy constants. The retained generic range example is
superseded for the two-source SxPID-specific range conclusions. It is not an SxPID-realizability or
sharpness result. The Rust test compares the committed logarithmic values with the categorical
SxPID implementation. It independently reconstructs each local law pair, $\delta$, $\eta$,
$p_{\min}$, $\Lambda$, $L$, $h$, the diamond ceiling $J$, the atom family, and every bound from the
committed count tables. For reconstructed logarithmic constants and bounds, it uses the scale-aware
tolerance

$$
32\,\mathtt{f64::EPSILON}
\max(1,|x_{\mathrm{Rust}}|,|x_{\mathrm{oracle}}|).
$$

It uses an absolute ceiling of
$32\,\mathtt{f64::EPSILON}$ nats for categorical estimator outputs. This is bounded internal
evidence. It is not a proof of the concentration theorem or a general binary64 error certificate.

`check-lean-finite-convergence.py` requires Lean 4.32.0 and the committed Lake manifest. The
checker binds the full manifest bytes and all nine package revisions. It rejects extra packages.
It also checks each dependency checkout's root, revision, origin, and clean status. It disables
global and system Git configuration and Git environment routing for these checks. It retains the
checkout's local configuration so it can verify the recorded origin. Ignored build and cache files
do not make a checkout dirty. The checker rejects the tokens `admit`, `axiom`, `constant`, `sorry`,
and `sorryAx` in the Lean sources. It builds the project with Lake. It then replays the project
declarations with Lean's bundled kernel checker. The artifact proves only the deterministic,
exact-real continuity, dependency-color algebra, and generic perturbation lemmas that its module
headers list. It does not prove an empirical strong law, the probability theorem, the complete
categorical PID result, Rust refinement, or binary64 behavior. The dedicated CI job runs the same
build and kernel checks.

`check-finite-alphabet-convergence-pdf.sh` builds the standalone mathematical paper from
`audit/formal/latex/finite-alphabet-plugin-convergence.tex`. It fixes the build time and timezone,
rejects LaTeX warnings and box defects, and requires exact byte equality with
`output/pdf/finite-alphabet-plugin-convergence.pdf`. It needs `latexmk` and a pdfTeX installation.
The check establishes deterministic document generation in that toolchain. It does not enlarge any
mathematical claim.

`check-dependency-colored-sxpid-pdf.sh` applies the same deterministic, warning-free build contract
to `audit/formal/latex/dependency-colored-sxpid-concentration.tex` and its committed PDF. The paper
states the probability proof, formal boundary, numerical checks, and retained counterexamples.
Exact PDF reproduction does not validate those scientific claims.

`check-markdown-math.py` checks every tracked or untracked Markdown file in the repository. It
rejects nonportable TeX delimiters, malformed display blocks, unbalanced inline math, bare TeX
outside math, unsafe table delimiters, display-only constructs in inline math, and commands that
GitHub's safe MathJax configuration blocks. In particular, it rejects `\operatorname`; use a
render-safe built-in operator or `\mathrm{...}`. It also applies a conservative formula-in-code
check to the theory documents. Its mutation suite proves that each rejected form fails closed. The
checker verifies syntax and rendering conventions only. It does not verify a mathematical
statement.

`check-z3-pid2-algebra.py` requires the exact 64-bit Z3 4.16.0 CLI. It checks five digest-pinned
QF_LRA obligations. Three obligations cover PID2 four-atom reconstruction, formula-level source
exchange, and four-node Möbius inversion followed by reconstruction. Two obligations cover
Möbius inversion and zeta reconstruction on the complete 18-node PID3 lattice. They also cover
formula-level equivariance for the `S0`/`S1` and `S1`/`S2` swaps. These two swaps generate all six
permutations of three sources. The mutation self-test changes each obligation to an exactly
satisfiable case and verifies rejection. The PID3 proofs cover exact-real lattice formulas only.
They do not establish estimator premises, asymptotics, Rust refinement, floating-point behavior,
distributional claims, a Lean development, or a four-source lattice.

The checker keeps its original PID2 filename as a compatibility route for existing CI and
maintainer commands. Its checked manifest now contains both PID2 and PID3 obligations.
The release audit runs the same checker and mutation suite. The CI coherence job downloads the
official x86-64 Linux Z3 4.16.0 archive and verifies its pinned SHA-256 digest before use.

```text
python3 scripts/generate-finite-alphabet-plugin-oracle.py
python3 scripts/generate-dependency-colored-sxpid-oracle.py
python3 scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/generate-sxpid2-exhaustive-oracle.py
python3 scripts/check-markdown-math.py
python3 scripts/check-markdown-math-self-test.py
python3 scripts/check-review-evidence.py
python3 scripts/check-review-evidence-self-test.py
python3 scripts/check-z3-pid2-algebra.py
python3 scripts/check-z3-pid2-algebra-self-test.py
python3 scripts/check-lean-finite-convergence.py
scripts/check-dependency-colored-sxpid-pdf.sh

# Maintainer-only mechanical regeneration after an intentional source change:
python3 scripts/check-review-evidence.py --write
python3 scripts/generate-finite-alphabet-plugin-oracle.py --write
python3 scripts/generate-dependency-colored-sxpid-oracle.py --write
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
Its temporary repository copies the current non-ignored tracked and untracked working set while
respecting pending deletions, so an evidence addition can be checked before it is committed. Every
fixture Git operation uses a minimal environment with external routing, configuration, attributes,
replacement/graft overlays, hooks, and signing disabled.

The manual `review-release.yml` workflow accepts only `v0.9.0` at the exact dispatch-time `main`
commit. Immediately before dispatch, an administrator must query GitHub's repository settings API,
confirm that `GET /repos/sepahead/pid-rs/immutable-releases` returns `enabled: true`, and supply the
exact `immutability_preflight=ENABLED` acknowledgement. The standard workflow `GITHUB_TOKEN` cannot
repeat that Administration-read query, so this is an explicit out-of-band trust boundary: an
administrator must not disable immutability between the check and publication. The acknowledgement,
exact CI run attempt, generating workflow attempt, release name, and release-notes digest are bound
into the checksummed provenance asset. Publication downloads the exact Actions artifact ID and
digest from an attempt-qualified artifact name. The name prevents a rerun from using the same
artifact name. Publication rechecks the remote annotated-tag object and peeled commit before release
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
