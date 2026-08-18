# scripts

[![License: MIT OR Apache-2.0](https://img.shields.io/badge/license-MIT%20OR%20Apache--2.0-blue.svg)](#license)

Operational helper scripts for maintaining **pid-rs** and its downstream consumers.

## Immutable KSG C3 and hosted-follow-up replay

`check-ksg-c3-checkpoint.sh` pins the published C3 parent, commit, tree, exact 19-path precommit
status, and both phase-verifier source digests. It replays the phase checker in normal and
optimized modes on a clean no-local clone of the checkpoint, then reconstructs the exact
parent-plus-overlay candidate in a second no-local clone and runs both checker modes plus both
351-case hostile self-test modes. This split is necessary because the hostile suite creates the
reviewed C3 commit and malformed descendants; starting that suite from the already committed tree
would erase the fixture delta. Git routing/configuration is scrubbed, Python uses `-I -S`, and the
precommit status is checked before and after the hostile runs. Before creating any clone, the
wrapper sets umask `022`: Git otherwise materializes tracked verifier sources as mode `0700` under
a restrictive caller umask, which the exact-source loader correctly rejects as noncanonical. The
private `mktemp` scratch root remains owner-only. A third no-local clone then checks out the exact
settled hosted-follow-up commit, rejects alternate/graft/shallow/replacement routing, and invokes
that commit's digest-bound normal-mode supervisor, which in turn compares checker and
child-self-test receipts across both Python modes. It then runs one final exact checker and repeats
clone/routing/source postconditions. Replaying the follow-up at its own immutable commit preserves
the one-child topology rule; the checker is not weakened to accept the current descendant.

```text
scripts/check-ksg-c3-checkpoint.sh
```

The wrapper establishes replay of the immutable C3 phase envelope and exact hosted-follow-up
engineering commit. It does not adjudicate the current descendant or imply arithmetic, estimator,
PID, statistical, hosted-CI, remote-authenticity, or security-clean success. Its long-lived C3
hostile children are bounded by the hosted job's finite timeout rather than a portable per-child
process-group supervisor.

`check-c3-hosted-followup.py` is the separate direct-child custody boundary for the engineering
correction after that checkpoint. It requires isolated/no-site Python, an exact reviewed path and
full-blob policy, equality of every protected C3 blob, a single unsigned direct child with the
reviewed human author/committer metadata, and a caller-supplied tree/checkpoint pair. Metadata does
not authenticate mechanical authorship. It recursively parses and rehashes each raw tree object
and blob, rejects empty tree paths, and brackets a single-linked private index whose
header/count/checksum, stage-zero entries, flags, and forbidden cache/indirection signatures are
checked without enabling filesystem monitoring. An independent bounded descriptor walk compares
the exact regular-file inventory and every implied directory, including special nodes and empty
directories that Git inventory can omit. The exact-source runner freezes the declared source size
and digest, captures at most 262,144 bytes through the retained no-follow leaf/path from the
filesystem root, verifies that capture before compilation or execution, then freshly traverses and
compares the path at the endpoint. The
checker applies pre-allocation object/file/aggregate/output/time budgets. Those are
application-visible bounds, not hard RSS, Git-internal allocation, filesystem-liveness, or
denial-of-service theorems. Its self-test attacks the policy, source entry, lifecycle, Git context,
object graph, index metadata and topology, wrapper pins, workflow commands, Rust regression seam,
modes, resource boundaries, receipt authority, and protected projection in normal and optimized
Python. Mutation-target families are correlated bookkeeping labels, not independent evidence.
The reviewed overlay contains exactly 13 paths (eight modified and five added), leaving 552 anchor
paths in the protected projection. The only SxPID2 claim-checker changes are three complete-byte
container/document digest rebinds for the mutable workflow, `justfile`, and this README, plus the
exact reviewed certified-method projection from `method-catalog.json`; its frozen
revision-1/2/3 authority, semantic checks, mutation logic, evidence, formal sources, and PDFs are
unchanged. The source
inventory contains 109 hostile cases in 18 bookkeeping families and declares 88
mutation-attributable verifier-target launches (86 checker and two self-test), while 22 local
receipt mutations launch no verifier target. Thirty-eight separately named deterministic harness
controls are also outside that count. These inventory values are not execution credit.
The runner normalizes only its own child-process umask to `0022`, because Git otherwise applies a
caller's restrictive umask to private checkout leaves that the checker correctly requires to be
canonical `0644`/`0755`; the self-test's containing temporary directory remains `0700`. This does
not repair or authenticate pre-existing worktree permissions.
Under the hosted supervisor, checker validations and child suites have explicit deadlines; a
standalone runner self-test has no separate whole-suite deadline beyond its caller. Both dedicated
verifiers require GIL-enabled CPython 3.11 through 3.14, the main and only enumerated Python thread,
unblocked/unpending `SIGALRM` and `SIGINT`, and actively reset inherited `SIGCHLD` actions to
`SIG_DFL` before any `Popen`. They install nonraising fixed-slot recorders for `SIGALRM`/`SIGINT`,
mask those signals from before each child launch through reap, post-reap `ESRCH`, and local-resource
closure, then restore the prior mask before adjudicating the deferred flags. The fork child unblocks
the pair in `preexec_fn` under that single-enumerated-thread premise. This does not authenticate
CPython, its standard library/extensions, or unenumerated native threads, and Python documents
`preexec_fn` as unsafe in the presence of threads. Child I/O and cooperative deadlines are bounded;
hard asynchronous preemption during an owned child lifecycle is not claimed. Exceptional cleanup
signals the owned original process group only before reaping its leader and retries post-reap
observation only to explicit `ESRCH`. Persistent post-reap presence or `EPERM` fails closed without
signaling or claiming reclamation. Other signal dispositions and masks are neither normalized nor
authenticated. In particular, inherited `SIGTERM`/`SIGHUP` dispositions are unauthenticated and
are not converted into cleanup exceptions; `SIGKILL` remains uncatchable.
The following direct commands are historical/development commands for a detached exact-f6 clone
or a deliberately constructed precommit fixture only. They are not operational descendant gates:
the one-child topology correctly rejects current f7-or-later `HEAD`. Local diagnostic mode emits a
distinct diagnostic/no-credit status and is explicitly no-credit:

```text
scripts/check-c3-hosted-followup.sh normal checker --diagnostic-without-external-custody
scripts/check-c3-hosted-followup.sh optimized checker --diagnostic-without-external-custody
scripts/check-c3-hosted-followup.sh normal self-test
scripts/check-c3-hosted-followup.sh optimized self-test
```

The direct-child gate remains frozen and valid only for the exact implementation child. CI now
replays it at that immutable commit through `check-ksg-c3-checkpoint.sh`; it does not apply the
direct-child predicate to a later descendant. Pull-request checkout still selects the exact PR
head rather than GitHub's synthetic merge. The current descendant requires its own acyclic receipt
and hosted result; immutable replay of its parent cannot authorize it.

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

## Ecosystem capability checks

`check-ecosystem-capabilities.py` validates
[`ecosystem-capabilities.json`](../ecosystem-capabilities.json) and regenerates
[`ECOSYSTEM_CAPABILITIES.md`](../ECOSYSTEM_CAPABILITIES.md). The closed contract projects the
method catalog and assurance registry onto four exact historical consumer snapshots. It binds the
method catalog, assurance registry, release scope, and retained repository snapshot by raw digest.
It derives local method maturity, release families, source identities, and `not_claimed`
integration states from those authorities. Present evidence must match its method-validation or
assurance-layer authority, artifact role, layer status, and layer tier. Multi-family requirements
need class-appropriate evidence for each family. Each missing evidence class must have an owned
gap. A reviewed semantic projection binds the source-derived needs, required evidence classes,
method routes, assumptions, limitations, gap responsibilities, and retained boundaries. Changing
one of these fields or an exact present/missing evidence path requires an intentional checker
update; internal consistency or family-level path membership alone cannot erase an evidence
obligation, launder unrelated tests, or transfer an external responsibility to pid-rs.
The same projection binds the exact authority records and digests. A changed catalog or scope
cannot become trusted merely by updating its digest in the contract.

The historical snapshots do not represent current consumer state. Passing the checker does not
establish compatibility, integration, qualification, operational validation, or application
validity. The mutation suite rejects evidence escalation, stale authority bindings, unsupported
method mappings, snapshot drift, schema-2/schema-3 replay confusion, one-family evidence reuse,
negation camouflage, coherent evidence-obligation erasure, responsibility laundering,
noncanonical JSON, duplicate keys, non-finite values, and stale generated Markdown.

```text
python3 scripts/check-ecosystem-capabilities.py
python3 scripts/check-ecosystem-capabilities-self-test.py
```

## Review evidence, bounded algebra, and oracle checks

`check-review-evidence.py` keeps three deliberately bounded artifacts coherent. The canonical
`assurance-registry.json` covers exactly the 37 release-scope families across definition, exact
algebra, Rust refinement, floating-point/numerical behavior, and statistical/application validity;
every layer has a stable assurance ID, evidence tier, assumption with an owner and failure
consequence, and an explicit gap disposition. `task-dispositions.json` covers exactly `T000`
through `T158`, records the 0.9 source-offer publication separately from 155 open and
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
bytes, and the non-escalation boundaries. Every registry-cited evidence file must have one
stage-zero regular-file entry in the active Git index, and its current raw bytes must hash to that
indexed blob. This is a point-in-time index/worktree coherence check, not an atomic snapshot,
authenticity proof, or review attestation. `--write` is the only supported way to regenerate the
two JSON registries; the tagged file ledger is verified but never rewritten. The mutation suite
removes and duplicates families/tasks/files, changes evidence tiers and dispositions, escalates
completion, alters digests, invents review metadata, and checks untracked and post-index-dirty
evidence paths to prove those changes fail closed.
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
fixed stress tuples through one million samples. The in-module Rust test compares every value.
The `8 * f64::EPSILON`-nat corpus maximum, attained on exactly 40 rows, compares the selected
binary64 result with `binary64(stored Decimal prefix text)`; it is not exact-rational error. The
separate `check-ksg-harmonic-exact-enclosure.py` route uses 160-digit directed Decimal bounds,
checks exact `Fraction` containment on all 6,920 exhaustive rows. Under the checker's stated Python
`Decimal` directed-rounding semantics, it certifies a unique exact-rational maximum below
`9.761311 * f64::EPSILON` nats across the full corpus, including the fixed stress rows. Both metrics
are below the reviewed `32 * f64::EPSILON`-nat ceiling. The stored references differ textually on
6,509 rows and numerically on 5,934 rows from exact-rounded values, while all binary64 conversions
agree. After canonical finite-Decimal validation, exact `Fraction(Decimal)` subtraction and
rational ordering compares all 8,198 pairs. The exact-enclosure self-test rejects 29/29 registered
scientific/custody mutations, while a separately reported comparator firewall rejects 2/2
Decimal-rounding/exact-fraction controls in both normal and optimized Python. The compiled Rust
corpus test directly checks every selected and source-swapped result for finiteness and classifies
the full output as `+0/-0/nonzero = 354/0/7844`. This is association-specific finite-corpus
evidence, not a ULP, universal, or portable result and not validation of neighbor search or
counts, an estimator, population support, or PID.

### KSG integer-harmonic revision-4 replay

The revision-4 lanes are deliberately separate. `check-ksg-harmonic-revision.py --claim-only`
checks internal correspondence among the canonical active packet, its mapped artifacts, complete
reviewed-prose bytes, typed facts, and explicit `integration_no_go` preclosure status. Its
companion mutation suite checks unresealed and bounded resealed custody/fact failures. This is not
artifact authenticity or general natural-language verification, nor a complete integration
checker, an immutable final evidence matrix, or a release decision. The default route of this
same checker is a deliberate fail-closed preclosure guard, not a future final mode.
The packet has 13 conjunctive open integration gates and therefore remains **NO-GO**. The canonical
unsigned M1a implementation commit must first be committed, pushed, and remotely verified while
that disposition remains red. Only a separate descendant/re-anchored M1c milestone may then bind
the immutable final evidence matrix and decision; preclosure evidence cannot grant that authority
early.

`check-ksg-m1a-phase.py` is the current-descendant lifecycle gate; it does not replace or reinterpret
the immutable historical C3 wrapper. Run it under isolated Python. Policy-only and hostile modes
are non-credit diagnostics. Creditable precommit mode requires an independently constructed exact
alternate-index tree, a sealed mode-`0400` single-link regular file supplied on standard input,
and a detached checkpoint; postcommit mode requires that same checkpoint as a clean direct-child
HEAD. No caller-controlled pathname enters the checker, and its output explicitly makes no
path-residency claim. The checker emits custody facts, not scientific evidence, authenticity, or
M1c authority:

```text
python3 -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
python3 -O -I -S -B scripts/check-ksg-m1a-phase.py --validate-policy-only
python3 -I -S -B scripts/check-ksg-m1a-phase-self-test.py
python3 -O -I -S -B scripts/check-ksg-m1a-phase-self-test.py
```

<!-- BEGIN KSG_M1A_CUSTODY_CORRECTION_README_V1 -->
The append-only M1a custody-correction route preserves the pushed `cb3f58f0...` scientific/runtime
tree and its fixed 83-path projection. Hosted CI run `31686107959` remains negative evidence: its
deterministic certified-SxPID2 full-container custody failure is not erased by exact-head CodeQL
run `31686106737` succeeding, and that combination is not an all-green hosted result. While the
correction policy inventory is provisional, only the following explicitly non-credit diagnostic
and hostile routes are valid:

```text
python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --validate-policy-only --allow-provisional-diagnostic
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --validate-policy-only --allow-provisional-diagnostic
python3 -I -S -B scripts/check-ksg-m1a-custody-correction-self-test.py
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction-self-test.py
```

After the exact correction inventory is human-frozen, precommit mode reads the sealed alternate
index only from descriptor 0; no index path is accepted on the checker CLI. Candidate-commit mode
checks a clean detached exact direct child (including a pull-request head) without fd0 or credit,
so the complete candidate is exercised before a main push. Postcommit mode requires that same
direct child as clean attached `main` HEAD and forbids alternate-index arguments. The lifecycle
forms are:

Freeze every authored correction-tree byte before constructing the checkpoint. Build the full
candidate index from those frozen bytes, seal that regular single-link index mode `0400`, and
record its SHA-256 and canonical decimal byte size. Create the unsigned direct-child checkpoint
with exactly this message, substituting those two observed values:

```text
Correct KSG M1a hosted custody wiring

Sealed-index-SHA256: <lowercase-sha256>
Sealed-index-Size: <canonical-decimal-bytes>
```

Run precommit validation with that same index on descriptor 0. This order is acyclic: neither the
checker nor the authored tree embeds the final index digest. A later strict descendant must retain
the identical raw index at
`audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin`; the composite receipt binds its
Git blob OID, SHA-256, size, reconstructed correction tree, and full entry count to the checkpoint
trailers and the historical precommit observation.

```text
python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode precommit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit> \
  --alternate-index-sha256 <sha256> \
  --alternate-index-entry-count <full-index-entry-count> < "$sealed_index"
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode precommit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit> \
  --alternate-index-sha256 <sha256> \
  --alternate-index-entry-count <full-index-entry-count> < "$sealed_index"
python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode candidate-commit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit>
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode candidate-commit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit>
python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode postcommit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit>
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --mode postcommit \
  --expected-candidate-tree <tree> \
  --checkpoint-commit <commit>
```

The alternate-index count is the full candidate-tree entry count. It is not the separately checked
83-path protected implementation projection.

Freezing the exact inventory enables exact local lifecycle validation only; it does not observe a
hosted run. Every local outcome remains `local_hosted_pending_no_credit`. Only a composite receipt
in a later committed descendant may observe exact-SHA hosted CI and CodeQL runs; neither local
custody success nor the r6 Lean replay may backfill hosted success or integration credit into
`cb3f58f0...`.

Once that later descendant receipt exists, pass its bounded canonical JSON bytes to the fixed
parser on standard input:

```text
python3 -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --validate-composite-receipt < receipt.json
python3 -O -I -S -B scripts/check-ksg-m1a-custody-correction.py \
  --validate-composite-receipt < receipt.json
```

This public mode accepts no receipt pathname and is mutually exclusive with every other checker
mode and lifecycle argument. The JSON Schema alone is insufficient: the fixed parser is required
to enforce the receipt's semantic and cross-field relationships and to recompute its compact
projections. A successful parse is still only typed descendant-receipt validation, with
`credit=none_typed_descendant_receipt_validation_only` and
`disposition=local_hosted_pending_no_credit`. The receipt is absent from both the implementation
and correction trees, so correction-commit CI does not invoke this later-descendant mode.

The same correction routes certified-SxPID2 hostile vectors through a fixed checker CLI protocol;
the self-test no longer imports repository checker bytes or accepts adjacent unchecked bytecode.
The checker and self-test both require isolated `-I -S -B` execution, and their official CI and
Just routes run normal and optimized isolated pairs. These bootstrap and protocol changes are
verifier custody only: the three container-digest rebinds remain distinct from the mathematical
packet, and none changes the certified mathematical result.
<!-- END KSG_M1A_CUSTODY_CORRECTION_README_V1 -->

<!-- BEGIN KSG_M1A_HOSTED_RECOVERY_README_V1 -->
## KSG M1a hosted-recovery verifier

Commit `7473e62acef6077c2c1147e09d5d1297f2a2874b` is the exact, frozen direct-child
custody correction of `cb3f58f0...`. Its local normal/optimized precommit and postcommit receipts
remain bounded custody evidence, not hosted success. Public CI run `31724449805` attempt 1 failed
with 43 successful and two failed jobs. The certified-SxPID2 self-test failed because that job's
depth-one checkout omitted the fixed `cb3f58f0...` checker authority. The KSG custody job separately
rejected the `certified_protocol` vector. Its public log exposes only the outer failure; a separate
reviewer-derived local cross-version reproduction found a CPython-minor-sensitive stored `ast.dump`
projection over unchanged bootstrap bytes. Same-head CodeQL run `31724449083` succeeded without a
new alert number. The CI and CodeQL observations remain separate and no composite-v2 receipt is
issued.

The bounded recovery is one unsigned fast-forward sole child of `7473e62a...`. It changes the
certified job's pinned checkout to `fetch-depth: 0`, preserving `persist-credentials: false`, the
fixed `cb3f58f0...` authority, the certified mathematical packet, and every non-container semantic
definition. It also validates marked certified bootstrap bytes and same-interpreter structural
relations instead of treating a stored cross-minor `ast.dump` digest as portable. Full history is
intentional: a later receipt descendant moves the fixed authority past any chosen finite depth.
The recovery checker independently reads and rehashes both historical subject commits, preserves
the implementation's exact 83-path projection, binds both terminal failed diagnostics and the
complete failed-run record, and validates only the reviewed 27-path recovery inventory: 19
modifications and eight additions.

The first r7-based local recovery seal failed closed on the repository's legitimate empty tracked
blob. Its unreachable checkpoint `37473f8fa9470fcec0bd419ec3df18ea4a6d805b`, candidate tree
`66f33f467f2bc661795599fa53ef81681ecd8406`, and mode-`0644`, 88,875-byte, 731-entry alternate
index SHA-256 `fb892aeaac2091e1d4c6b619a4ce0053771d8aeb0ee147105017613a3b46a56d`
are unauthenticated local observations, not sealed custody. The ref never advanced, and none of
those identities may be reused or relabeled. The append-only repair permits zero bytes only for a
regular, single-link candidate leaf compared with the matching zero-byte blob; authority and
static inputs remain positive-size. Its self-test exercises the real empty blob, a nonempty
mismatch, empty authority rejection, and independent symlink, hardlink, mode, size-bound, and
identity-stability failures. A full candidate scan requires every tracked regular leaf to have its
declared mode; seven pre-existing mode-0600 filesystem leaves were normalized to 0644 without
changing content, and finalized r7 remains byte-identical.

While the recovery policy is provisional, run:

```text
python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --validate-policy-only --allow-provisional-diagnostic
python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --validate-policy-only --allow-provisional-diagnostic
python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery-self-test.py
```

After every authored byte is independently reviewed and the recovery authority is frozen, preserve
finalized r7 and generate append-only Lean r8, then regenerate current-source state last. Construct a fresh full
alternate index, seal it as a regular single-link mode-`0400` file, and create the unsigned
sole-child checkpoint with exactly:

```text
Repair KSG M1a hosted recovery wiring

Sealed-index-SHA256: <lowercase-sha256>
Sealed-index-Size: <canonical-decimal-bytes>
```

The lifecycle commands mirror the historical correction but bind `7473e62a...` as the immediate
parent. Precommit accepts the index only on descriptor 0; candidate mode requires detached HEAD;
postcommit requires clean attached `main`. Every result is still hosted-pending and no-credit:

```text
python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode precommit --expected-candidate-tree <tree> --checkpoint-commit <commit> \
  --alternate-index-sha256 <sha256> --alternate-index-entry-count <count> < "$sealed_index"
python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode precommit --expected-candidate-tree <tree> --checkpoint-commit <commit> \
  --alternate-index-sha256 <sha256> --alternate-index-entry-count <count> < "$sealed_index"
python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode candidate-commit --expected-candidate-tree <tree> --checkpoint-commit <commit>
python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode candidate-commit --expected-candidate-tree <tree> --checkpoint-commit <commit>
python3 -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode postcommit --expected-candidate-tree <tree> --checkpoint-commit <commit>
python3 -O -I -S -B scripts/check-ksg-m1a-hosted-recovery.py \
  --mode postcommit --expected-candidate-tree <tree> --checkpoint-commit <commit>
```

The recovery head is exact commit `bc3aa80fb6025e709c2906a08bce25a4fac40578`. Its exact-SHA CI
and CodeQL runs completed successfully. Composite-v3 nevertheless cannot issue a truthful receipt:
its fixed semantic CodeQL language order conflicts with its increasing-analysis-ID predicate on the
actual recovery observations, and its exact-three-additions child cannot also update the
self-excluding current-source manifest. Preserve the v3 checker, self-test, schema, and permanent
absence of its reserved receipt. Do not reconstruct either unavailable historical index or invent
replacement custody.

The historical append-only v4 contract is documented in
`audit/evidence/ksg-rev4-m1a-composite-v4-process-2026-08-15.md` and its companion PDF. C4 is an
unsigned, single-parent direct child that changes only the exact operational policy inventory; R4
is a later unsigned, single-parent direct child that adds the raw capture and derived receipt and
regenerates current-source. C4 was published as
`da253576a5f76e99633fff4de5cf1118f967b90d`, but its attempt-1 hosted qualification failed; R4 is
therefore permanently unissued. These exact v4 local gates are historical replay routes, not a way
to reopen R4:

```text
tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v4.XXXXXX")"
python3 -I -S -B scripts/capture-ksg-m1a-composite-v4.py --self-test \
  > "$tmp_root/capture-self-test.json"
python3 -O -I -S -B scripts/capture-ksg-m1a-composite-v4.py --self-test \
  > "$tmp_root/capture-self-test.optimized.json"
cmp "$tmp_root/capture-self-test.json" "$tmp_root/capture-self-test.optimized.json"
python3 -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-static \
  > "$tmp_root/static.json"
python3 -O -I -S -B scripts/check-ksg-m1a-composite-v4.py --validate-static \
  > "$tmp_root/static.optimized.json"
cmp "$tmp_root/static.json" "$tmp_root/static.optimized.json"
python3 -I -S -B scripts/check-ksg-m1a-composite-v4-self-test.py \
  > "$tmp_root/self-test.json"
python3 -O -I -S -B scripts/check-ksg-m1a-composite-v4-self-test.py \
  > "$tmp_root/self-test.optimized.json"
cmp "$tmp_root/self-test.json" "$tmp_root/self-test.optimized.json"
scripts/check-ksg-m1a-composite-v4-process-pdf.sh --exact
```

The KSG process-PDF gate additionally pins the repository's standard-library render comparator.
Its cross-toolchain route rasterizes all nine rebuilt and committed report pages and the
standalone custody figure with the same local Poppler at 120 dpi, then requires every page to
remain inside explicit mean, changed-pixel, and large-delta bounds. Causal controls insert an
active one-point-square clipping path before the page-3 custody Form and replace both Source Sans
embedded font-program references with the LM Roman donor program in both the report Form and
standalone figure while retaining the declared font dictionaries; all three must fail at the raster
predicate. This is bounded same-renderer regression evidence. It is not exact visual identity,
renderer independence, accessibility
conformance, human review, or a proof against every PDF visibility manipulation.

The append-only correction is documented in
`audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md` and its four-page companion PDF.
C5 is the unsigned direct child of published C4 and uses a fresh `r10` replay. It narrowly
normalizes one exact checkout-residue byte image, isolates extracted release fixtures from ambient
Git ancestry, rebinds the reviewed zeta spelling, and rebinds the final certified-SxPID execution
containers. It also replaces the stale live README-token expectations for the never-issued
composite-v3 recovery route with the current C4/C5 nonissuance and capture-separation boundary,
while retaining the legacy checker's historical Git, custody, workflow, Just, and anti-revival
checks. It does not assert a unique cause for the release-state runner failure. Run:

```text
just ksg-composite-v5
scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh --cross-toolchain
scripts/check-ksg-m1a-composite-v5-boundary-pdf-self-test.sh
```

The v5 publication gate binds the exact Markdown, TeX, accessible SVG, standalone vector PDF,
four-page report, color/grayscale rendering receipt, and closed visual-review receipt. It builds
the figure and report twice, rejects external SVG resources and text below the declared print
floor, requires four zero-rotation A4 pages with no annotations or executable actions, and requires
the sole vector Form to be visible on page 3. Object hostiles exercise a wrong page box, relative
URI, nonidentity Form matrix, zero page transform, unsafe catalog action, and relocated Form. The
external self-test additionally reseals an unsafe SVG resource, a live PDF annotation, and receipt
body drift. Cross-toolchain mode compares all report pages and the standalone figure through the
same local Poppler at 120 dpi under explicit bounds; this remains differential same-renderer
evidence, not absolute visual correctness, PDF/UA, or renderer independence. Local L5 runs the
same-toolchain exact gate and the default exact/cross hostile suite. The Ubuntu dedicated-v5 route
installs the hash-pinned Python verifier plus its declared TeX/SVG/Poppler packages, then invokes
the gate and hostile suite with `--cross-toolchain`; it does not pretend Linux can reproduce the
macOS PDF bytes exactly.

The predecessor-failure capture belongs to C5. Only a fresh attempt-1 all-success C5 qualification
can permit R5, whose exact three-path delta adds the successor capture and typed receipt and
regenerates current-source last. The receipt binds both captures. Passing a subset, rerunning an
attempt, or changing C5 requires another append-only contract version.

That condition was not met. Published C5 commit
`be862b155d710573ec95356fc1cbe9a96a2b83b9` retained a successful attempt-1 CodeQL route, but its
dedicated-v5 publication step failed and the repository-CI formal-PDF job exposed the analogous
immutable-v4 lane; repository CI ended with 44 successful jobs and that one failure. Both old
cross-toolchain gates compared every report with every fresh and
committed standalone figure even though the TeX reports name the committed figure. R5 is therefore
permanently unissued. Preserve C5, r10, and both old gate scripts exactly; their failed hosted
observations receive no R5, scientific, authentication, or independence credit.

Composite-v6 adds a separately versioned keyed portability adjudicator and boundary publication.
Each rebuilt or committed report must match the exact committed figure its TeX source names. The
fresh standalone figure is checked separately against the committed standalone figure through
closed object-safety, text, page geometry, subset-neutral font-family, and bounded color/grayscale
same-renderer predicates. A decoded-content-different no-op positive proves the cross-toolchain
figure relation does not collapse back to byte identity, while the same fixture must be rejected
as a report's associated figure. Run the local exact lane from frozen bytes with:

```text
just ksg-composite-v6
scripts/check-ksg-m1a-composite-v6-pdf-portability.sh --exact
scripts/check-ksg-m1a-composite-v6-pdf-portability-self-test.sh --exact
scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh --exact
scripts/check-ksg-m1a-composite-v6-boundary-pdf-self-test.sh --exact
```

The dedicated Ubuntu v6 workflow runs the same two gate pairs with `--cross-toolchain`; it does
not claim that Linux can reproduce the committed macOS PDF bytes. C6 must be C5's exact unsigned
direct child and publishes fresh replay r11. From an exact clean committed C6 checkout, the typed
local recorder runs only the fixed `just ksg-composite-v6` command under its constructed
environment and writes a new mode-0600 staging file outside the repository:

```text
local_closure_dir="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-c6-local-closure.XXXXXX")"
python3 -I -S -B scripts/capture-ksg-m1a-composite-v6-local-closure.py \
  --output "$local_closure_dir/local-closure.json"
```

The staged record binds exact C6 topology, the fixed command, clean pre/post observations, bounded
stdout/stderr, and a reviewed executable subset. It is an unsigned correlated local observation,
not a first-attempt authority, complete transitive executable inventory, atomic snapshot,
authentication, trusted time, or independent reproduction. Install its exact bytes at
`audit/evidence/ksg-rev4-m1a-composite-local-closure-v6-2026-08-18.json` only after its schema and
semantic checks pass.

The clean endpoints use ordinary Git status plus selected metadata checks. Rejecting
`core.excludesFile` removes one ignore-routing overlay, but repository-ignored products and
uninspected Git metadata remain outside the observation and may remain side inputs; this is not a
hermetic closure.

After the successor hosted capture also validates, derive the candidate receipt from two distinct
new mode-0600 staging files. The derivation route accepts no evidentiary stdin route and requires
both inputs at offset zero through stable, single-link regular-file descriptors:

```text
set -o noclobber
umask 077
local_record="$local_closure_dir/local-closure.json"
successor_capture="/absolute/private/path/successor-capture.json"
receipt_staging="/absolute/private/path/composite-v6-receipt.json"
python3 -I -S -B scripts/check-ksg-m1a-composite-v6.py \
  --derive-receipt --local-closure-fd 3 --successor-capture-fd 4 \
  3<"$local_record" 4<"$successor_capture" >"$receipt_staging"
```

Do not install the derived bytes until the checker validates the staged receipt and both input
records against the exact C6/R6 contract. The two private staging paths are transport locations,
not evidence locators or durable authorities.

R6 remains an exact conditional four-path child: that local record, the fresh successor hosted
capture, the deterministically derived receipt, and current-source regenerated last. It is
permitted only after the fresh exact-C6 local closure and fresh attempt-1 repository CI, all four
CodeQL language jobs, and dedicated-v6 success for the same exact C6 SHA. The receipt validates and
binds the predecessor capture, local record, and successor capture before recording all four terms.
Any false, absent, nonterminal, wrong-attempt, or wrong-SHA hosted term—or an absent or invalid local
record—leaves R6 unissued and requires another append-only contract version.

This portability correction is one project-defined report/figure association repair manifested in
two immutable predecessor gates. It is not evidence that either committed publication is
defective, is not a generic PDF-equivalence theorem, and grants no PID, KSG, mathematical,
scientific, security, application, PDF/UA, renderer-independence, authentication, or independent
reproduction status.

The v4 capture and receipt commands documented by the historical process report described a
conditional route that was never admitted. C4's attempt-1 qualification failed, R4 is permanently
unissued, and the two reserved v4 evidence paths must remain absent. Do not run the v4 live capture,
derive an R4 receipt, reinterpret a rerun as attempt 1, or seed evidence from its synthetic fixture.
Composite-v5 uses separately versioned predecessor/successor captures and a separately typed R5
receipt; those artifacts preserve the failed observation without reviving or renaming R4.

The schema alone grants no status. Hosted identifiers, times, logs, alerts, and artifacts remain
unauthenticated observations. M1a stays `integration_no_go`; this route provides no KSG M1c,
estimator, support, calibration, categorical MGW, Schick--Poland, Ehrlich continuous, `I_min`,
PID2/PID3, quantized/mixed-support, package, release, objective, or application evidence.
<!-- END KSG_M1A_HOSTED_RECOVERY_README_V1 -->

The W1b runtime lane uses one finite `n=4,k=1` predecessor-adjacent fixture in both source orders.
Pair diagnostics bind ordered counts; pair and xblocks bind association-specific selected bits and
covered source mutations under forced brute/kd-tree backends. The selected bits are one ordered
position below correctly rounded exact-real `5/6`. This does not close the general P2 nextafter
corpus or establish neighbor geometry, support, consistency, calibration, or any PID result.

The modular certificate classifies exact zero versus nonzero only for the frozen 8,198 rows. Each
selected prime separately separates the 354 structural endpoints from the 7,844 nonendpoints;
the three primes are redundant fault-diversity lanes, not a CRT proof. The retained rejected-prime
collisions demonstrate that zero residue does not generally imply exact rational zero. The
odd-prime identity `H_(p-1-t) = H_t (mod p)` explains why the four `p=1000003` collisions are
signed/order copies of one `H_999999=H_3` event. The selected primes share this reflection
structure, so neither reflection-index presence/absence nor three fields supplies an independence
or separation proof; exact exhaustive certificate replay is the bounded authority. Recursive
path-aware JSON shape/type/value equality rejects 2/2 Boolean/integer controls separately from the
28/28 registered modular scientific/custody mutations in both interpreter modes. The composite
control `1000001=101*9901` bypasses the small-prime `2..37` prefilter and reaches the deterministic
u32 Miller--Rabin witness loop; that establishes path coverage only. The certificate is not a
universal harmonic-zero theorem.

Lean checks 19 exact finite-sum, index-map, symmetry, monotonicity, range-bound, and
rational-to-real theorems; Z3 checks four separately encoded, premise-explicit conditional
obligations. Both retain the positive-integer digamma identity as a typed analytic premise and
share human-selected signs, maps, and statements. They do not prove Rust or binary64 refinement,
neighbor geometry, estimator or support validity, continuous shared exclusions, PID semantics,
calibration, or application validity.

Before solver execution, the Z3 checker performs a bounded complete ASCII S-expression parse with
exact ordered per-file command/declaration/assertion profiles and `Bool`/`Int`/`Real` type checks.
It validates correlated raw-byte and token-stream pins, derives the positive preflight only from
the validated in-memory negative snapshot, and sends both snapshots to Z3 over standard input.
Normal and optimized replay retain 12/12 satisfiable semantic countermodels and separately reject
52/52 checker controls: 16 lexer/parser, 25 profile/type, and 11
custody/transport/result. Those inventories are not additive theorem counts. The two pins are
correlated custody views, not independent proof routes, and a retained well-typed wrong-theorem
dual rebase preserves the expected solver answers. Theorem intent therefore remains a
human/Git/receipt cut.

The source/count derivation `x+y <= n+k` is retained only as a conditional set lemma for an
eligible row with finite positive joint radius, an unambiguous unique kth shell, exact
strict-radius membership counts over one common row set, and the inventoried exclusive or
anchor-inclusive map. Neither it nor the resulting stronger balanced harmonic lower bound is
promoted to the revision-4 theorem inventory; source refinement, formal and compiled evidence,
mutations, provenance, and any runtime attainability claim remain open.

The scientific process, corrected claims, and negative paths are recorded in the
[revision-4 correction ledger](../claims/KSG-INTEGER-HARMONIC-001/correction-ledger-v4.md), the
[integration disposition](../claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md), and
the retained
[Decimal](../claims/KSG-INTEGER-HARMONIC-001/failures/decimal-reference-metric-conflation-v4.md),
[modular](../claims/KSG-INTEGER-HARMONIC-001/failures/modular-zero-residue-collisions-v4.md), and
[SMT-LIB](../claims/KSG-INTEGER-HARMONIC-001/failures/smtlib-shape-and-snapshot-v4.md) failure
memos. External model reviews are advisory process records only and are not claim evidence.

Replay the preclosure arithmetic, certificate, formal, and claim-custody lanes in normal and
optimized Python modes:

```text
python3 scripts/generate-ksg-local-arithmetic-oracle.py
python3 -O scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/check-ksg-harmonic-revision.py --exact-only
python3 -O scripts/check-ksg-harmonic-revision.py --exact-only
python3 scripts/check-ksg-harmonic-revision.py --binary64-only
python3 -O scripts/check-ksg-harmonic-revision.py --binary64-only
python3 scripts/check-ksg-harmonic-exact-enclosure.py
python3 -O scripts/check-ksg-harmonic-exact-enclosure.py
python3 scripts/check-ksg-harmonic-exact-enclosure-self-test.py
python3 -O scripts/check-ksg-harmonic-exact-enclosure-self-test.py
python3 scripts/check-ksg-harmonic-revision.py --enclosure-only
python3 -O scripts/check-ksg-harmonic-revision.py --enclosure-only
cargo test --locked -p pid-core --all-features stats::tests::ksg_integer_harmonic_range_matches_decimal_oracle -- --exact
cargo test --locked --release -p pid-core --all-features stats::tests::ksg_integer_harmonic_range_matches_decimal_oracle -- --exact

python3 scripts/generate-ksg-harmonic-modular-certificate.py
python3 -O scripts/generate-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate.py
python3 -O scripts/check-ksg-harmonic-modular-certificate.py
python3 scripts/check-ksg-harmonic-modular-certificate-self-test.py
python3 -O scripts/check-ksg-harmonic-modular-certificate-self-test.py

python3 scripts/check-lean-ksg-integer-harmonic.py
python3 -O scripts/check-lean-ksg-integer-harmonic.py
python3 scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-lean-ksg-integer-harmonic-self-test.py
python3 scripts/check-z3-ksg-integer-harmonic.py
python3 -O scripts/check-z3-ksg-integer-harmonic.py
python3 scripts/check-z3-ksg-integer-harmonic-self-test.py
python3 -O scripts/check-z3-ksg-integer-harmonic-self-test.py

python3 scripts/check-ksg-harmonic-revision.py --claim-only
python3 -O scripts/check-ksg-harmonic-revision.py --claim-only
python3 scripts/check-ksg-harmonic-revision-self-test.py --claim-only
python3 -O scripts/check-ksg-harmonic-revision-self-test.py --claim-only
```

The `--exact-only`, `--binary64-only`, `--enclosure-only`, and `--claim-only` switches are scoped
diagnostic routes. This revision checker is permanently preclosure-only: its default route
intentionally exits nonzero with the exact lifecycle status and it has no positive final parser.
It cannot substitute for the separately reviewed versioned M1c checker required after catalog,
release, source, identity, phase-isolation, and real M1a evidence are settled.

`generate-finite-alphabet-plugin-oracle.py` independently rebuilds a 100-digit Decimal corpus for
the listed two-, three-, and four-source SxPID tables and the listed two- and three-source `I_min`
tables. It also includes minimum-tie crossings and realization-key changes. The generator uses
direct published definitions and a generic finite-poset inversion. It imports no pid-rs code or
third-party package. The default command rejects stale fixture bytes, a stale fixture digest, or a
stale embedded generator identity. The Rust test binds the fixture, generator identity, definition
status, tested-code paths, and limitations. It separately checks fixed-quantizer wrapper equality
against direct categorical calls. This is bounded software evidence. It is not an asymptotic proof,
a portable binary64 error theorem, or external review.

`generate-dependency-colored-sxpid-oracle.py` rebuilds the SxPID-under-dependency-coloring challenge
corpus. It uses exact rational arithmetic for finite probability and count identities and
400-digit Decimal arithmetic for logarithms. It enumerates the finite-field
pairwise-independence counterexample, copied colors, singleton colors, adaptive coloring, support
deletion, an unspecified-mixing construction, a generic net-weight range extremizer,
univariate-marginal control and new support. It reconstructs three endpoint-valid negative-lift
counterexamples. It audits all 64 ordered conditioned-diamond coordinate pairs in each of seven
exact rational cases. It checks the ordinary-diamond and conditioned-nested exact identities on
the same inputs, which include zero-lift and unnormalized algebra-only boundaries. Nine cases have
six positive displayed masses that sum to one and realize all exact conditioned-diamond extremal
regimes. Two cases attain the refined union-reciprocal bound exactly; their ratio to the older
reciprocal-mass bound is $999/1000$. Six two-cell SxPID cases attain $\Lambda$ for redundancy and
unique components and reject the false all-atom $\Lambda-\eta$ refinement. It also checks
class-size constants, the
telescoping error allocation, all displayed bounds on six committed two-source law pairs, and one
fixed-width overlapping-window population law. One full-support pair is a bounded near-tightness
challenge for the refined $\Lambda-\eta$ synergy constant. The retained generic range example is
superseded for the two-source SxPID-specific range conclusions. It is not an SxPID-realizability or
sharpness result. The Rust test compares the committed logarithmic values with the categorical
SxPID implementation. It independently reconstructs each local law pair, $\delta$, $\eta$,
$p_{\min}$, $\Lambda$, $\Lambda-\eta$, $L$, $h$, the diamond ceilings $J$ and $J_q$, the atom
family, and every bound from the committed count tables. For reconstructed logarithmic constants
and bounds, it uses the scale-aware
tolerance

$$
32\,\mathtt{f64::EPSILON}
\max(1,|x_{\mathrm{Rust}}|,|x_{\mathrm{oracle}}|).
$$

It uses an absolute ceiling of
$32\,\mathtt{f64::EPSILON}$ nats for categorical estimator outputs. A separate bounded suite uses
ten refined-modulus cases and six endpoint-ceiling cases. It reconstructs 400-digit references
from the exact real values of parsed binary64 inputs. Stored hexadecimal payloads bind all parsed
operands and represented subtraction results. The cases include adjacent values around both
branch seams, zero displacement, a tiny ratio, a moderate ratio, an extreme normal-scale input,
the exact lower endpoint of the upper-branch floor ratio, normal and subnormal near-boundary
floors, a floor near one, the exact positive-zero endpoint, and the smallest positive subnormal
floor. The Rust test uses adaptive series, quotient-log,
transformed, and log-domain routes. It
requires selected naive inverse-quotient and cancellation routes to fail. An expected zero must
match positive zero bit for bit. Other stability comparisons use 256 × `f64::EPSILON` times the
larger of the oracle magnitude and the bounded operation scale. A selected naive route must be
nonfinite or differ by more than 1024 times that tolerance. This is bounded internal evidence. It
is not a proof of the concentration theorem, an interval implementation, or a general binary64
error certificate.

`generate-support-change-tolerant-sxpid-oracle.py` independently constructs a bounded categorical
SxPID challenge fixture without importing the Rust implementation. It uses exact `Fraction`
probabilities and lattice coefficients. It uses 160-digit `Decimal` arithmetic only for natural-log
reference values. The committed corpus contains 18 law pairs and replays 36 public count tables for
two through four sources. It includes support creation and deletion, endpoint cases, equality
witnesses, rare disappearing keys, the active-face Fannes falsifier, the net-residual shortcut
falsifier, full-lattice Möbius data, and a fixed seeded challenge set. The paired Rust test
reconstructs event probabilities, pointwise cumulatives, Möbius atoms, averages, and every declared
bound from raw count tables. This is implementation-separated bounded evidence. The decimal values
are not rigorous enclosures, the corpus is not a universal proof, and separation from the Rust
source is not independent authorship or external review.

`check-lean-finite-convergence.py` requires the frozen Lean 4.33.0 release at commit
`d8b18978322de05a8f3dba51ef03cf5461676c17` and the committed Lake manifest. Its version probe
requires one exact Release identity line and empty stderr. The
checker binds the full manifest bytes and all nine package revisions. It rejects extra packages.
It also checks each dependency checkout's root, revision, origin, and clean status. It disables
global and system Git configuration and Git environment routing for these checks. It retains the
checkout's local configuration so it can verify the recorded origin. Ignored build and cache files
do not make a checkout dirty. The checker rejects the tokens `admit`, `axiom`, `constant`, `sorry`,
and `sorryAx` in the Lean sources. It also rejects `native_decide` in executable Lean source. It
builds the project with Lake and replays the declarations with Lean's bundled kernel checker using
the cache-independent `leanchecker --fresh` route. It
enforces an exact ordered inventory of all 339 source-level declarations across eight imported
modules and runs `collectAxioms` on all 246 named source theorems. The complete two-source
count/event bridge and the complete two-source count-to-atom bridge are separately SHA-256
bound. Two separately digest-pinned semantic contracts compile with an unlimited heartbeat and
fix the reviewed count/event transcription, the complete two-source Möbius/zeta tables, all 24
componentwise cumulative/atom coordinates, exact products, scaling, and sign fixtures. Compiled
`example`s and private contract helpers are checked surfaces but are not included in the 246
named-theorem `collectAxioms` inventory.

The 4.33 migration permits exactly seven narrow `.types false` compatibility routes: three around
the generated `Fintype` derivations for the fixed two-source node/component/atom types and four
inside exact finite proof terms. Broad or file-global transparency switches fail closed. The
versioned replay and no-release-chasing policy are checked with:

```text
python3 -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
```

The current append-only receipt path is
`audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json`.
The 11 August receipt, unsuffixed 12 August receipt, finalized `r2` receipt, finalized `r3` receipt,
finalized `r4` receipt, finalized `r5` receipt, finalized `r6` receipt, finalized `r7` receipt,
finalized `r8` receipt, and finalized `r9` receipt remain exact-hash-bound prior evidence with their
original v1, v2, v2, v2, v2, v2, v2, v2, v2, and v2 schema identities. The `r10` suffix denotes
only the tenth receipt in the versioned sequence that originated on 12 August, and therefore the
eleventh current-project replay receipt overall; the 11 August historical receipt is outside that
versioned sequence. The suffix does not
denote a calendar date, schema, theorem, review, assurance tier, or independence revision. The
route receives current execution credit only when that exact receipt exists and validates.

The freeze gate binds the exact empty-output `lake --quiet --wfail` clean build,
`leanchecker --fresh`, the complete
246-name axiom-query input, current 4.33 evidence, the complete selected active KSG and SxPID bridge
authority, and immutable 4.32 history. A canonical replay-receipt projection covers every observed
timestamp, path, and stream; within the custody map only the checker digest that would create a
checksum cycle is omitted. The self-test digest remains in the reviewed projection, and both
custody digests are checked directly against live bytes. CI, `just`, `AGENTS.md`, this guide, and
the dedicated freeze document are separately exact-hash bound. The companion self-test includes
valid-but-rewritten receipt observations, wiring drift, manifest-record overclaim, and scope/pin
mutations so a self-consistent narrative rewrite does not receive replay credit.
The replay runner constructs an exact 15-variable environment with fresh empty `HOME` and
`TMPDIR`, fixed locale/timezone, and no inherited tool or Python routing; all Python children use
`-I -S -B`. Every child receives the exact theorem-audit payload or an explicitly supplied,
seekable-file-backed empty standard input, never the caller's stdin, and the runner fixes its process and child-file creation
mask to `0077`, clears the inherited signal mask, and restores default dispositions for five
reviewed control signals. Other operating-system process limits remain execution premises. It
validates exact Lean/Lake identity before building and rechecks the complete bound
static surface both before and after the command sequence. Those endpoint checks detect bounded
drift but are not an atomic snapshot. The tracked runner `generate-lean-4.33-replay.py` accepts no
arguments: it uses exact reviewed repository, output, Darwin Lean-bin, Python, and archive route
constants. It rejects any extra argument before runner-controlled repository/archive/output
lookup, repository-module load, child launch, or write; hashes the single-link archive through a
stable no-follow descriptor; and repeats symlink-aware build/config absence checks immediately
before the clean build. Receipt construction remains private at mode `0600`; the retained
descriptor is changed to exact mode `0644` and fsynced before the final name is linked, and the
published single-link receipt is revalidated at mode `0644`. Its exact
invocation and the boundary that fixed host-local routes are not authenticated executables are
recorded in the freeze document. The pinned executable set includes Lean, Lake, LeanChecker, and
Python; Lake child selection is bounded by the release-bin-first `PATH` and the same leaf
snapshots. Stable path/digest snapshots immediately before direct child launch and after replay
detect bounded drift but are not an atomic binding to the bytes the OS executed. The first
11 August replay, first 12 August replay, finalized `r2` replay, and finalized `r3` replay remain
byte-preserved prior evidence; none is relabelled as current runner custody. Replay-time
checker/self-test hashes are fully projected; after the reviewed projection
is pinned, finalization changes only that checker literal and the receipt's deliberately
projection-omitted live checker digest; the replay digest remains the endpoint hash. The final
checker reconstructs its zero-placeholder replay source and allows no other checker
replay/final-byte difference. The provisional no-clobber receipt becomes immutable only after this
two-edit finalization and normal/optimized checker plus self-test replay.

The runner also refuses to start unless the three-way composite-v5 checksum cut is invocation
ready. The replay projection must still be the unique exact zero-placeholder source expression;
the Lean composite-v5 scalar and the `scripts/check-ksg-m1a-composite-v5.py` operational-map row
must be equal nonzero literals hashing the exact final v5 checker; and the v5 checker's unique
nonzero `EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256` literal must reproduce the Lean source after
normalizing exactly the projection, v5 scalar, and v5 operational row to their reviewed placeholder
forms. The retained v4 checker, its ordinary operational-map row, and r9 receipt are immutable
prior evidence: they are neither rewritten nor part of the r10 normalization cut.

Finalization is deliberately acyclic. First freeze the v5 self-test, this guide, the freeze guide,
and every other non-cut byte and digest row. With all three Lean cut positions in placeholder form,
compute `H_L` from that exactly normalized Lean source and write only `H_L` into the v5 checker.
Then freeze the v5 checker, compute `H_V` from its exact final bytes, and write the same `H_V` into
only the Lean v5 scalar and v5 operational row. Leave the replay projection as `"0" * 64`, rerun
the normal and optimized hostile suites, and invoke the zero-argument replay generator exactly
once. Only after it no-clobber-publishes the provisional r10 receipt may the established two-edit
receipt finalization replace the projection literal and the projection-omitted live Lean-checker
custody digest. Any change to the v5 self-test or another normalized Lean input after `H_L` was
computed invalidates the cut and requires restarting this sequence. The generator predicates run
before replay commands and publication; the hostile suites exercise causal checker drift,
projection-finalized, missing, duplicated, mismatched, normalized-cut, and operational-map-omission
mutations.

For every natural-valued count function with positive total on a complete finite two-source key
space, the first bridge identifies the four signed-net averaged cumulatives as support-restricted
count-weighted logarithmic sums. The second bridge applies the exact four-node Möbius transform
componentwise and identifies all 24 informative, misinformative, and net cumulative/atom
coordinates with explicit positive rational products and scaled logarithms. Publication-facing
event semantics is a reviewed repository transcription, not a Lean theorem connecting a paper to
the formal definitions. Rust refinement, binary64 behavior, more than two sources, component
nonnegativity, and population validity remain out of scope. The dedicated CI job runs the same
inventory, build, kernel, semantic-contract, and axiom-basis checks.

`check-lean-finite-convergence-self-test.py` copies only the checked Lean sources into isolated
temporary fixtures. Under normal and optimized Python it rejects exact static source/digest
mutations plus baseline-first isolated mutations of the count/event module, atom module, and atom
semantic contract. The registered classes cover imports and inventories; same-name theorem
weakening; proof-escape and native-evaluator injection; event, count, coordinate, component,
Möbius/zeta, inverse, weighted-product, quotient, scaling, sign, and positivity changes; and
semantic-contract fixture drift. Each current route is bound to its declared rejection contract.
Comment and string masking prevents proof-escape words in non-code text from becoming false
positives. The exact mutation counts and identifiers are emitted by the checker rather than
duplicated in this prose.

`check-finite-alphabet-convergence-pdf.sh` builds the standalone mathematical paper from
`audit/formal/latex/finite-alphabet-plugin-convergence.tex`. It fixes the build time and timezone,
rejects LaTeX warnings and box defects, and requires exact byte equality with
`output/pdf/finite-alphabet-plugin-convergence.pdf`. It needs `latexmk` and a pdfTeX installation.
The check establishes deterministic document generation in that toolchain. It does not enlarge any
mathematical claim.

`check-two-source-sxpid-count-atom-bridge-pdf.sh` applies the same deterministic,
warning-free contract to the dedicated two-source count-to-atom bridge paper. It exact-rebuilds the
reviewed source/PDF bytes and requires rendered text naming the 24-coordinate surface and the
explicit boundary between exact Lean algebra and unproved publication correspondence,
Rust/binary64 refinement, component nonnegativity, higher-source generalization, and population
claims.

`check-dependency-colored-sxpid-pdf.sh` applies the same deterministic, warning-free build contract
to `audit/formal/latex/dependency-colored-sxpid-concentration.tex` and its committed PDF. The paper
states the probability proof, formal boundary, numerical checks, and retained counterexamples.
Exact PDF reproduction does not validate those scientific claims.

`check-support-change-tolerant-sxpid-pdf.sh` applies the same contract to the exact-real,
support-change-tolerant averaged categorical SxPID theorem. Its LaTeX source is
`audit/formal/latex/support-change-tolerant-averaged-sxpid-continuity.tex`; its rendered artifact
is `output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf`.

`check-formal-tool-adoption-pdf.sh` applies the same rendering and reproducibility contract to the
formal-tool adoption and implementation-status record. The record distinguishes the implemented
source-only Rug/MPFR reference lane from the remaining Kani, Verus, Rocq Interval, and Aeneas
pilots, and preserves pins, licenses, negative controls, trust boundaries, and permitted claim
language. It does not claim end-to-end verification of `pid-rs`.

`check-certified-sxpid2-assurance-pdf.sh` applies the same contract to the exact-count SxPID2
conditional-assurance paper. Its LaTeX source is
`audit/formal/latex/certified-sxpid2-executable-assurance.tex`; its rendered artifact is
`output/pdf/certified-sxpid2-executable-assurance.pdf`. The paper derives the exact count
expressions and conditional directed enclosure, records the executable evidence and retained
counterexamples, and states the Rust/native/statistical refinement boundary. Reproducible
rendering does not discharge that boundary.

`check-exact-log-product-sxpid2-pdf.sh` applies the same rendering contract to the bounded exact
rational-product zero/sign extension in
`audit/formal/latex/exact-log-product-sxpid2-assurance.tex` and
`output/pdf/exact-log-product-sxpid2-assurance.pdf`. The proof rewrites each admitted empirical
log-linear coordinate as a positive rational product after integer denominator clearing. It
supports exact zero/strict-sign decisions only where the separately reported product preflight
has status `compared`; it does not replace the dyadic magnitude enclosure, prove a statistical
sign, or extend the PID definition. The leaf gate compares every non-platform evidence field and
the portable Lean version/commit/build identity with the versioned 4.33 receipt; it deliberately
does not require a Linux CI runner to reproduce the Darwin platform token. The Darwin-specific
platform identity remains bound by the current project replay receipt. The unversioned Lean 4.32
receipt is immutable historical evidence, not a current-checker oracle.

`check-foundational-sxpid-audit-pdf.sh` applies the same rendering contract to the foundational
shared-exclusions audit in `audit/formal/latex/foundational-shared-exclusions-pid-audit.tex` and
`output/pdf/foundational-shared-exclusions-pid-audit.pdf`. That audit separates the published
local shared-exclusions functional from implementation and estimator claims, records exact
finite counterexample searches, and states the boundary of its descriptor-factorization Lean
proof. Reproducible rendering does not turn those scoped results into an axiomatic uniqueness,
population-consistency, or downstream-validity theorem.

`check-ecosystem-compatibility-audit-pdf.sh` applies the same rendering contract to the downstream
compatibility audit in `audit/formal/latex/ecosystem-compatibility-audit.tex` and
`output/pdf/ecosystem-compatibility-audit.pdf`. Its machine-readable compatibility matrix remains
the authority for implemented capabilities; the paper records realistic assumption regimes,
abstention requirements, and retained negative findings. The build gate establishes artifact
coherence, not that a downstream sampling or authorization contract is true.

`check-certified-sxpid2-claim.py` is the fail-closed governance gate for that revision boundary.
It requires the historical revision-1 and revision-2 re-adjudication rules, the distinct
revision-3 claim, decision, bindings, obligations, evidence matrix, theorem boundary, and retained
negative controls, synchronized report-v2/verifier-v3/resource-v2 identifiers, the complete
catalog artifact inventory, and ordinary CI/`just`/formal-PDF wiring. Revision 3 changes only the
independent verifier's loaded-execution digest normalization/configuration binding and schema.
Two named cache/code controls compare isolated cold/warm cache states and reject a post-import
live-code replacement. A separate sweep mutates all 51 declared semantic/configuration globals.
A CPython-3.11-only source mutant additionally removes the normalization call and must fail
through the intended integrity guard; other Python versions report that version-conditioned lane
as not exercised. The mutation self-test structurally attacks schemas, exact path-to-digest table
bindings, supported/unsupported claim rows, source bindings, evidence counts and boundaries,
catalog provenance, and active gate registration; every registered mutation must fail. This establishes
repository coherence and named fault sensitivity, not theorem truth, Python or runtime
correctness, portable semantic hashing, independent custody, or application validity.

The corresponding executable qualification commands are:

```text
python3 audit/tools/certified-sxpid/scripts/check-exact-products.py
python3 audit/tools/certified-sxpid/scripts/check-exact-products-self-test.py
python3 audit/tools/certified-sxpid/scripts/check-nonsyntactic-zero-boundary.py
python3 audit/tools/certified-sxpid/scripts/challenge-exact-products.py
python3 scripts/check-lean-exact-log-product.py
python3 -I -S -B scripts/check-certified-sxpid2-claim.py
python3 -O -I -S -B scripts/check-certified-sxpid2-claim.py
python3 -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
python3 -O -I -S -B scripts/check-certified-sxpid2-claim-self-test.py
```

The first three exact-product checks qualify all 11,856 coordinates in the exhaustive binary
total-at-most-four corpus, kill the named product mutations, and retain the first nonempty
product-one boundary at binary total eight. The deterministic evolutionary challenge is a bounded
falsifier search; its failure to find a negative informative or misinformative atom is explicitly
not a universal nonnegativity theorem. Lean checks the generic log/product/sign algebra and the
retained five-factor product identity, but not the concrete SxPID event extractor, lattice,
executable refinement, sampling model, or downstream use. The independent exact-rational and Rust
routes supply the concrete witness binding.

The non-syntactic-boundary command is read-only by default. It verifies a fresh certificate,
compares all bounded findings and stable bindings with the historical receipt, and writes the
complete live receipt only to standard output. Exactly two outer execution bindings may differ:
the executable digest and the full certificate digest. A replacement stable binding covers the
certificate payload after its full envelope digest and exact inventories are checked and only one
source-manifest leaf plus three build-environment leaves are removed: runtime source-manifest
digest, Rust version, build host, and build target. Fifty-one hostile controls bind the exclusion
and retention sets and malformed cases. A complete recorded-schema scalar-leaf sweep additionally
mutates 276 outer and 960 certificate leaves, recovering exactly the declared 274+2 and 956+4
changed/invariant partitions. Use `--update-evidence` only for an intentional reviewed custody
transition. The recorded
same-host replay is not cross-platform validation and the projection is not executable, source,
dependency, or portable-semantic identity.

`check-mathematical-workflow-pdf.sh` rebuilds the self-contained mathematical problem-solving
workflow from `audit/formal/latex/mathematical-problem-solving-workflow.tex` and compares it with
`output/pdf/mathematical-problem-solving-workflow.pdf`. The workflow's Python PDF parser is pinned
as a hash-checked distribution archive in `audit/formal/requirements-pdf.txt`; CI selects Python
3.12 and installs that requirement with `--require-hashes --no-deps --no-cache-dir`. The archive
pin does not authenticate an arbitrary pre-existing local installation, Python executable, system
library, TeX distribution, or operating system.

The gate compiles inside a disposable directory because the LaTeX Markdown renderer externalizes
fenced-code intermediates beside the current working directory. It checks that the root Markdown
is embedded byte-for-byte in the TeX framing and that the only post-Markdown bytes are the reviewed
document terminator. Required scientific assertions must occur in top-level Markdown prose rather
than only in fenced, quoted, or indented code. It replays the shared LaTeX-log mutation suite,
checks strict visible-text and exact-source contracts for the project-local SVG/PDF figure pairs,
and inspects the report's PDF structure, navigation, annotations, and rendered-page receipt. The
aggregate formal-PDF gate and the direct Just recipe run the Markdown synchronizer in read-only
mode, replay its mutation suite, replay the shared log self-test, and replay the render comparator's
adversarial cases before running a focused hostile suite against the top-level custody checker and
invoking the paper gate. The Python mutation suites are each run in ordinary and optimized mode to
catch stripped-assertion dependencies; those are two interpreter modes over the same cases, not
twice as many independent cases. The paper gate also replays the captured helpers it relies on.

CI and the direct Just recipe enter Bash through `/usr/bin/env -i`, an explicit admitted executable
path, fixed locale/time-zone values, controlled home and temporary directories, and
`--noprofile --norc`. The aggregate wrapper repeats that clean entry specifically for the workflow
checker. This removes `BASH_ENV` and other ambient startup variables before the invoked Bash starts;
it does not authenticate any admitted executable. The checker separately resolves, constrains,
hashes, and stability-checks the executable bytes used by the captured run.
On Ubuntu 24.04, `/usr/bin/luaotfload-tool` resolves outside those admitted executable roots to the
TeX Live script tree. The hosted job requires that exact canonical distro target, refuses to
replace any existing destination, copies the bytes without transformation into a same-directory
staging file, compares them byte-for-byte, and publishes the checked file with a hard link that
uses GNU `ln -T` and fails rather than clobbering or traversing a destination created in the
intervening window. It removes the staging name and compares the published path again. The pinned
`setup-python` `bin` directory is
already admitted and is first in both the supplied clean path and the checker's reconstructed path
because it contains the selected `python3`. A rejected first correction used a distinct private
subdirectory: the initial run found the copy, but a nested capture reconstructed `/usr/bin` ahead of
that lower-ranked directory and correctly rejected the changed resolution. The checker captures the
executed copy, its `env`/`texlua` interpreter chain, and all other admitted executable bytes before
and after the build/validation consumers. Optional refresh and final cleanup occur after the second
capture and are not covered by a universal after-use claim. This is a path-normalization step for
the observed distro layout, not authentication of TeX Live or an additional independent
verification route.

Font discovery has a separate exact-layout boundary. Under the same clean environment, the
optional Debian-overlay query admits only status 0 with a nonempty captured value or status 1 with
a value empty after Bash command substitution removes Kpathsea's trailing line feed. Any nonempty
root must be the canonical direct directory `/usr/share/texmf`. The checker asks
`kpsewhich --must-exist` for each of the fifteen literal
OpenType filenames, then accepts the selected canonical direct regular file only at its
filename-specific path under `TEXMFDIST`. Latin Modern and Latin Modern Math may additionally
resolve at that same relative path under the exact `TEXMFDEBIAN` root; Source Sans Pro may not. This
distinction is required because Ubuntu Noble's `lmodern` package depends on `fonts-lmodern`, whose
OpenType payload is installed in the Debian overlay rather than in
`/usr/share/texlive/texmf-dist`. The prior checker incorrectly constructed every Latin Modern path
under `TEXMFDIST` even though the required package and correctly named font were present. Empty,
relative, multiline, outside-allowlist, wrong-family-overlay, special-file, symlink, and
noncanonical selections fail closed. One Python process per font walks the selected absolute root
and every relative directory component with `O_DIRECTORY` and `O_NOFOLLOW`, opens the leaf with
`O_NOFOLLOW` and `O_NONBLOCK`, matches the leaf name and file descriptor before and after the
bounded read, and re-walks the complete source chain. It creates the copied font through a
descriptor for the private destination root with `O_EXCL`, requires a new single-link regular file,
and re-walks that root after writing. This closes the demonstrated validate/reopen
intermediate-directory symlink escape and binds one run's selected font bytes without ambient
fallback. It does not authenticate the distro package, prove the font correct, exclude privileged
mount-namespace changes, or make a cross-toolchain render byte-identical.

LuaHBTeX must load a generated `lualatex.fmt` before the report wrapper can execute. The first
hosted run of the map-free correction failed closed because Ubuntu selected
`/var/lib/texmf/web2c/luahbtex/lualatex.fmt` outside the admitted installation-root closure; on
the audited macOS TeX Live layout, the analogous ambient file happened to lie beneath the broad
`TEXMFROOT` boundary. The checker does not widen that boundary. It requires Kpathsea to select the
one exact `$TEXMFSYSVAR/web2c/luahbtex/lualatex.fmt` leaf, captures its bounded bytes through
no-follow descriptors, re-walks the source chain, creates one exclusive single-link mode-0444
private copy, requires that copy to be the only entry in a mode-0555 root, and replays its size and
SHA-256 before every compiler pass and after both builds. Literal `TEXFORMATS` points only at that
root: both `kpsewhich --show-path=fmt` and the selected `lualatex.fmt` path must equal their exact
private values. A leading, trailing, or doubled colon is forbidden because Kpathsea expands it to
ambient defaults, as documented by the
[Kpathsea manual](https://tug.org/texinfohtml/kpathsea.html). Every retained `.fls` pass must have
raw and resolved `.fmt` sets equal to the
single captured pathname; the format is admitted by exact equality, not by admitting its directory
or `TEXMFSYSVAR` generally.

This freezes the selected format bytes needed by the two isolated builds. It does not authenticate
TeX Live or how the format was generated, establish cross-platform format/PDF byte identity, make
`.fls` a syscall trace, sandbox pre-wrapper format behavior, or defeat privileged or same-UID
replace-and-restore while LuaHBTeX reopens the private pathname. The selected engine and format
remain toolchain premises, and later wrapper defenses cannot retroactively constrain format
initialization or `\everyjob` activity.

The workflow paper does not require the generated pdfTeX font map. On exact Noble predecessor
`30c8fa8`, LuaHBTeX nevertheless selected
`/var/lib/texmf/fonts/map/pdftex/updmap/pdftex_dl14.map`, outside the bounded `TEXMFROOT` input
closure. Enlarging the allowlist to all of mutable `TEXMFSYSVAR`, or copying one selected map while
trusting its name, would weaken rather than close that boundary. Each report build therefore starts
from a generated `pid-rs-map-file-free-entry.tex` wrapper. Its first explicit operation is
`\pdfextension mapfile {}`, which prevents the inherited default-map action after the captured
format loads and before the captured report source runs. Format initialization, `\everyjob`, and
other engine-supplied pre-wrapper activity are outside this ordering claim. The wrapper requires an empty
`luatexbase.callback_descriptions("find_map_file")` inventory, installs a handler that rejects every
later nonempty map-file lookup reaching `find_map_file` on the tested TeX `mapfile` or Lua
`pdf.mapfile` routes independently of requested spelling, installs a separate category-2 font-map
file-event defense in depth, emits
exactly one pre-source sentinel, and inputs the exact captured source. An explicit `-jobname`
preserves the canonical artifact stem.

The wrapper is created with exclusive/no-follow descriptor custody, replayed byte-for-byte through
that descriptor, required to remain one single-link regular file, and changed to mode 0444 before
use. LuaHBTeX subsequently reopens its pathname. Mode 0444 is read-only under the declared local
permission premise; it is neither filesystem immutability nor a defense against a same-UID
replace-and-restore race. Its content is synchronized before the final mode change; neither that
mode metadata nor the directory entry has a crash-persistence guarantee. Every retained `.fls`
pass must contain that exact per-run wrapper.
Raw and resolved recorder input paths independently reject a case-insensitive `.map` suffix or
adjacent case-insensitive
`fonts/map` components. Those recorder checks are secondary: a renamed map has no path signature,
and `.fls` is not a syscall trace. Runtime controls therefore request the toolchain-selected
`pdftex.map` bytes under neutral names through both TeX and Lua operations. Separate controls cover
relative and absolute paths through both front ends plus a TEXMF-shaped TeX path, while a named
accepted control records that file-free
TeX and Lua `mapline` state changes remain outside the denial.

The primitive bridge is explicit rather than inferred from similar names. The pinned LuaTeX 1.18
manual defines compatibility `\pdfmapfile` as `\pdfextension mapfile` and says `pdf.mapfile`
replaces the `\pdfmapfile` primitive inherited from pdfTeX. The pinned pdfTeX manual supplies the
early-empty-call/default-map semantics, while exact A/B execution supplies toolchain-specific
evidence for that bridge. This is not a theorem about future engines or formats.

This is not a sandbox for hostile TeX or Lua. It assumes the exact captured source and admitted
format/toolchain premises. Source-side callback replacement, arbitrary Lua I/O, pre-wrapper format
or `everyjob` state, privileged or same-UID replace-and-restore races, recorder completeness, and
file-free `mapline` are outside the claim. The category-2 callback is defense in depth, not evidence
that every encoding or map resource is denied. The official LuaTeX 1.18 manual labels category 2
as a font-map coupling event and documents `find_enc_file` separately; the direct category-2
control simulates that callback event rather than opening a real encoding resource. The wrapper
changes no PID estimand, estimator, theorem, Lean source, mathematical source, or PDF source.

Each control routed through the common accept/reject wrappers gives its probe/watchdog decision
phase a 180-second deadline; dedicated liveness controls use explicit one- or two-second decision
deadlines. That parameter is not a strict end-to-end wall-clock bound: decision publication and
readiness validation, the watchdog's two-second escalation, the five-second `ps` call, group-absence
polling, and process reaping are subsequent bounded stages under a cooperating-kernel/progress
premise. Direct fixture setup, extraction, and post-refresh checks are not separately timed, so the
aggregate suite still relies on its outer local or hosted-job deadline. For a bounded probe, an anchor retains the original
process-group identity while the parent adjudicates at most one typed completion, timeout, or
watchdog-error record. The parent no-follow descriptor-replays exactly one single-link mode-0600
record, checks its exact bounded payload, and captures the typed classification used by later
branch selection. A claimed decision directory without a canonical record becomes custody status
125. After the completion-record publisher child exits, the anchor installs its `USR1` release
trap, opens a no-clobber mode-0600 readiness node with shell builtins, writes the exact payload, and
self-stops. The one-second scheduling control deliberately induces a window in which that node is
empty; it does not claim that a descheduled parent necessarily observes the partial state. A
visible completion record ends the outer loop without a preliminary readiness-existence grace.
After central decision-record capture and watchdog reap, the parent starts the sole five-second
readiness validator. It does not equate pathname existence with readiness: a
no-follow/nonblocking descriptor replay retries
until stable descriptor/leaf identity and exact canonical bytes are observed. Failure to become
canonical within that one grace becomes custody status 125. The handshake is scheduling evidence,
not crash durability. After
expected ownership is proven, the ordinary-completion route sends
group `SIGSTOP` before its membership snapshot. The anchor catches TERM with a no-op handler rather
than exporting
`SIG_IGN` across `exec`; nested programs therefore retain their ordinary signal semantics. After a
record appears, the parent attempts to kill and reap the watchdog, then performs final cleanup
adjudication. If the parent is descheduled for more than the watchdog's two-second grace after a
timeout record, the watchdog's delayed group `SIGKILL` may win first; cleanup provenance is not
inferred from later absence. An ordinary completion first revalidates expected group ownership,
sends group `SIGSTOP`, takes a five-second `ps` membership snapshot, and releases only a lone
anchor. Unexpected members after proven ownership trigger an attempted group `SIGKILL`.
Missing/mismatched ownership, inspection failure, or other cleanup uncertainty triggers bounded cleanup attempts,
expected-PGID absence adjudication, and custody status 125; it does not prove that an observed or
possibly foreign group was killed. Every post-launch decision route polls for expected-PGID absence
before exposing its status. Timeout status 124 therefore depends on anchored-group absence after
adjudication, not on a claim that either the parent or watchdog necessarily issued the winning
signal.

The self-test exercises ordinary success and nonzero status preservation, an induced partial-node
window, invalid readiness bytes, wrong-mode and malformed completion records, a canonical
watchdog-error record, default-TERM and TERM-ignoring descendants, normal-exit orphan rejection, an
exclusive-decision publication stall, cleanup-helper and membership-command failure, and
post-cleanup absence. Its source mutations bind
late process-group adjudication before timeout classification and classification before advisory
termination. Rejection credit is the exact typed set `{1, 2}` under the suite's admitted trusted
fixture convention: status 1 denotes a detected artifact or semantic drift and status 2 a detected
prerequisite/environment contract violation. The marker and status do not provide a causal typing
theorem for an arbitrary hostile command. Timeout 124, the broader custody status 125, launch
failures, and signal-derived statuses remain uncreditable even if captured output contains the
expected marker. Result-log reset separately refuses symlinks, FIFOs,
directories, and multiply linked files before the shell reopens the validated private path.

The canonical Markdown uses four leading spaces at the numbered rank--trace argument's six display
delimiters and the first continuation after each display. This minimum source-level convention
makes Markdown 2.23 and 3.4 agree on the equations and following list items without broadly
reindenting the mathematics; it does not change the mathematics or relax the cross-toolchain text,
navigation, or raster predicates.

The direct self-test freezes exactly 322 controls in the partition 203 predecessor, 37
bounded-probe, 17 entry-wrapper, 7 runtime-map, 8 FLS-map-path, 3 transitive-executable-custody,
and 47 format-custody controls. The format family covers exact query and selected-path
canonicalization (including Kpathsea's empty-component default expansion), nonempty bounded source
bytes, descriptor capture/rewalk, exclusive single-link replay, sealed mode and inventory, exact
digest replay, actual compiler-environment consumption, verifier ordering before every compiler
pass and after both builds, the complete source/size/digest receipt, and case-insensitive
raw/resolved FLS format sets across direct and aliased paths. These are correlated deterministic
fault probes, not 322 independent defenses or scientific replications. The liveness
mechanism assumes admitted Bash job control, Python, `ps`, same-UID PID/process-group behavior, and
the suite's private root. It is not pidfd containment or a hard asynchronous preemption theorem;
deliberate process-group escape, external anchor death, PGID reuse outside the checked transitions,
a stalled cleanup runtime, or a noncooperating kernel remains outside the claim, and the hosted job
retains its independent finite deadline.

Readiness source mutants remove no-follow, regular/link, mode, descriptor/leaf-identity, and
exact-payload guards. Decision source mutants bypass root-mode, regular/link, identity, timeout
equality, and watchdog-error allowed-reason guards; dynamic hostile records separately exercise
decision mode and status-payload rejection. The shared two-occurrence flags invariant detects
either descriptor-flags deletion, although the named no-follow mutant edits the readiness route.
The decision record's 256-byte size check has no separately credited semantic mutant: descriptor
reading is independently capped at 257 bytes and the closed exact grammars reject any oversized
payload even if that early diagnostic guard is removed. This is an explicit redundant-guard
classification, not complete mutation coverage of every source line.

A standalone invocation of the self-test inherits its launching shell's startup environment and
search path; it does not by itself establish the enclosing checker's complete executable-manifest
custody. The production checker invokes its captured snapshot under the already isolated path and
revalidates the admitted executable closure. A separately recorded standalone replay is useful
corroboration only when its exact self-test and production-checker digests, invocation environment,
and process-group observations are retained; it remains correlated with the same sources, host,
toolchain, validators, and fixtures.

The same hosted entry gives the aggregate gate a newly created `HOME`. The Lean evidence wrappers
deliberately discard inherited `ELAN_*` routing before invoking the selected `lake` proxy, so an
unprovisioned clean home causes Elan to download the tracked toolchain and emit informational
stderr inside the otherwise silent version probe. That outcome is rejected; the proof checker is
not relaxed to admit bootstrap output. CI requires both clean-state paths to be absent, creates them
without `mkdir -p`, requires the literal toolchain request to equal the exact bytes of
`audit/formal/lean/lean-toolchain`, installs that release explicitly into the clean home's `.elan`
state with the already hash-pinned Elan launcher and isolated `TMPDIR`, rejects a symbolic-link
`.elan`, and only then enters the evidence lane. The Elan proxy directory is first in the outer
path so a runner-image `lake` cannot shadow it; the selected `python3` and normalized TeX script
still resolve from the next, already first-ranked `setup-python` directory. `HOME` and `ELAN_HOME`
name the same isolated state. The later checker still
validates the reported Lean version and source commit and still requires its own version probe to
have empty stderr. This makes bootstrap a visible setup premise; it does not authenticate the Lean
archive, Elan's download service, the runner, or the selected kernel, and it does not turn a
same-kernel replay into independent formal evidence.

Install the hash-pinned dependency into a Python installation under one of the checker's admitted
roots, then run the following canonical commands. CI's pinned `setup-python` installation lives
under `/opt/hostedtoolcache` and satisfies that path contract. An ordinary project or temporary
virtual environment is intentionally rejected even if it contains the same wheel, because its
executable path lies outside the admitted roots.

```text
python3 -m pip install --require-hashes --no-deps --no-cache-dir \
  --requirement audit/formal/requirements-pdf.txt
python3 -I -S scripts/sync-mathematical-workflow-tex.py --check
python3 -I -S scripts/sync-mathematical-workflow-tex-self-test.py
python3 -O -I -S scripts/sync-mathematical-workflow-tex-self-test.py
scripts/check-formal-pdf-log-self-test.sh
python3 -I -S scripts/compare-formal-pdf-renders-self-test.py
python3 -O -I -S scripts/compare-formal-pdf-renders-self-test.py
scripts/check-mathematical-workflow-pdf-self-test.sh
/usr/bin/env -i \
  PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin" \
  HOME=/nonexistent TMPDIR=/tmp LC_ALL=C LANG=C TZ=UTC \
  bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh
```

After an intentional source change, a maintainer may append `--refresh` to that same clean-
environment command. The refresh route still captures exact source, helper, executable, and
`pypdf` bytes; re-resolves every command under the isolated search path and closes admitted script
shebangs over their direct or `/usr/bin/env`-delegated interpreter bytes; validates the
Markdown/TeX correspondence, equation-tag sequence, figures, logs,
fonts, PDF structure, and active-content exclusions; performs two isolated fixed-point builds; and
renders all pages in color and grayscale. A same-host advisory lock serializes cooperating refresh
and verification processes for the same canonical repository root; it does not exclude privileged,
noncooperating, or remote writers. The initial shell waits for a Python child that acquires the
lock and replaces itself with the lock-bearing checker, then exits with that child's exact status;
it cannot resume the pipeline after the descriptor-owning child has finished. Inherited lock state
is accepted only as a complete numeric-descriptor/root-digest pair whose descriptor still names and
owns the expected lock. Partial, malformed, or root-mismatched state fails closed. The writer stages
the committed report PDF, its rendering
receipt, and all four source-bound figure PDFs after single-link, non-symlink, stable-descriptor,
cross-binding, readback, and `fsync` checks. Each existing destination is installed by an atomic
descriptor-relative exchange, and each absent destination by an atomic no-replace rename. On an
ordinary later failure, completed replacements are rolled back only if the installed node still
has the exact expected identity and bytes; a detected concurrent replacement is preserved rather
than overwritten. That rollback window extends through final descriptor-relative readback of all
six outputs, report/receipt cross-binding, a second exact capture of every non-output repository
input, and the closed four-SVG/four-PDF figure inventory. After the writer has committed that
transition and removed displaced recovery nodes, a separate read-only post-refresh recapture checks
the same non-output manifest and all six generated/source byte pairs. A failure in this later
confirmation is fail-closed but cannot safely restore the pre-refresh files; the advisory lock is
the stated premise against cooperating local writers, not an atomic repository snapshot. The six
names do not form one filesystem transaction: a process kill, kernel failure, or power loss between
renames can leave an old/new set, which the rendering-receipt digest, figure source-digest metadata,
and default exact gate reject. Refresh deliberately does not update or credit the independent
visual-review receipt. A fresh page-by-page color/grayscale review must bind the new hashes, after
which the default `--exact` route must pass. Thus `--refresh` is a controlled, fail-closed artifact
transition—not multi-name atomicity, a validation shortcut, or a publication claim.

The PDF includes the canonical repository protocol plus a novice-oriented primer, worked negative
examples, bounded evolutionary-search rules, and a typed evidence-aggregation model. The checker
binds the exact 74-entry outline depth/title/page manifest and, in exact/refresh mode, the 185-entry
named-destination page/type/coordinate manifest. The Markdown table renderer requires eight
baseline skips of remaining page space before entering each `longtable`, forcing an earlier page
break otherwise; this resolves the page boundary before its automatic named destination is
created. It records ordered annotation page/target/rectangle
rows; requires, for each URI value, at least as many rendered fragments as canonical source
occurrences; and rejects every rendered URI absent from the source. This aggregate count does not
pair repeated identical links one-to-one. A wrapped label may legitimately yield several same-URI
annotation rectangles, whose exact inventory remains in the navigation manifest.
The gate also rejects legacy competing destinations, nonzero page origins, unequal page boxes,
non-unit `UserUnit`, `QuadPoints`, and every nonzero link flag. Every internal `GoTo` must resolve,
and every link rectangle must stay within its page. Cross-toolchain mode retains exact
outline and route identities while allowing at most two PostScript points of coordinate movement;
this is a bounded layout tolerance, not coordinate identity. Source rules reject known
auto-numbering and heading-anchor forms; exact reviewed primer, Markdown, SVG, and publication-style
digests close finite lexical/parser boundaries without pretending that a digest proves semantics.
Each source SVG additionally requires canonical style classes, visible palette fills, supported
text transforms, in-view anchors, and source-SHA metadata in its one-page PDF derivative. The
checker also fails closed if the typed citation-edge heading, source-arrow field, or retained
adjacent-arrow countermodel is absent from either the canonical Markdown or rendered PDF. This is an
artifact-retention and rendering gate: it does not instantiate the citation-edge record for future
proofs, prove any PID claim, establish semantic correctness from visual structure, authenticate the
toolchain, or turn correlated checks of the same bytes into independent evidence.

The retained `.fls` files and closure manifests bind every raw and resolved input observed after
each compiler pass, and the two isolated builds must be byte-identical. Raw and resolved map-shaped
path checks are distinct aliases of recorder evidence, not a content classifier or syscall trace.
Capture is not atomic with LuaTeX's earlier reads. The result therefore assumes admitted external
TeX and font files remain stable during each bounded build; a privileged or noncooperating process
that mutates and restores such a file entirely between checkpoints is outside the claim.
Repository sources and generated report figures are separately copied into captured mode-0444/0555
read-only snapshots, and admitted executable and Python-package manifests are checked before and
after the run. Read-only modes do not make those snapshots immutable against the owner, privileged
actors, mount changes, or filesystem replacement.

`check-citation-edge-countermodel.py` exhaustively checks the finite sequence
`0 -> 0 -> C2 --id--> C2 -> 0`, with `C2 = Z/2`: every displayed table is a group
homomorphism, image equals the next kernel at all three internal terms, the right middle arrow is
an isomorphism, its left neighbor is not, and the middle group is nonzero. It also binds the
canonical Markdown byte-for-byte to the LaTeX-embedded copy and requires the typed source-arrow
field, the human-readable `Z/2` rendering of the same countermodel, the corrected equation-(27)
disposition, and the route-independence controls. For the inspected X-thread case it additionally
validates `audit/evidence/x-thread-citation-edge-application.json` against the exact bytes of
`audit/evidence/x-thread-citation-source-manifest.json`: artifact digests and page spans, stable
typed source-arrow signatures, predicate/arrow and source/local bindings, variable maps,
hypothesis evidence, unresolved ambiguity, the conditional equation disposition, and the scoped
downstream blast radius must agree. The external PDFs and X content are not retained, so this is a
record/cross-binding check, not a recomputation of the observed PDF hashes, a source-theorem proof,
or a complete thread archive. Its self-test rejects the existing nine countermodel/document
mutations plus neighboring-arrow swap, source-span removal, arrow reversal, missing hypothesis,
false equation disposition, digest drift, and page drift.

```text
python3 scripts/check-citation-edge-countermodel.py
python3 scripts/check-citation-edge-countermodel-self-test.py
```

This proves only that the local adjacent-arrow inference schema is invalid. It does not interpret
the motivic source theorem, validate any surviving manuscript result, or establish PID correctness.

`check-zeta-pid-transfer-firewall.py` checks three exact, pure-standard-library countermodels to
shortcut transfers from the reviewed zeta rank--trace argument: independent and parity systems
with the same covariance but different mutual information; diagonal Hermitian matrices with the
same trace and squared Frobenius norm but different rank/inertia; and a congruence that preserves
inertia while changing trace and squared Frobenius norm. It also exercises a nine-field mapping
firewall and exact local reviewed-source-record fields, requires the canonical Markdown/TeX
enclosure and its publication sentinels, and reports `ABSTAIN_NO_PID_MAPPING_SUBMITTED`. The source
record is not a retained elaborated Challenge signature, trusted-statement digest, or external
comparator replay. The companion self-test rejects five mechanism/record overclaims and eight
source/publication mutations at exact causal codes in normal and optimized modes.

```text
python3 -I -S -B scripts/check-zeta-pid-transfer-firewall.py
python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall.py
python3 -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
python3 -O -I -S -B scripts/check-zeta-pid-transfer-firewall-self-test.py
```

This gate is negative-control and workflow evidence only. It does not verify the external zeta
paper, prove that no future PID mapping can exist, validate a PID method or estimator, or establish
exact-real-to-binary64 refinement or numerical stability.

`check-lean-citation-edge-countermodel.py` checks the same `C2` sequence independently at the
implementation layer using frozen Lean 4.33.0, Mathlib additive homomorphisms, image/kernel
exactness, and the Lean kernel. It audits nine theorem declarations, prohibits proof escapes, pins
self-contained source/toolchain/manifest bytes, requires the exact 4.33.0 commit and Release build
identity with empty probe stderr, and records the permitted axiom inventory. The companion mutation
self-test kills five changes: collapsing `C2`, replacing the right identity with zero, replacing
image/kernel exactness with a vacuous top-range condition, and asserting either false adjacent-
arrow predicate.

```text
python3 scripts/check-lean-citation-edge-countermodel.py
python3 scripts/check-lean-citation-edge-countermodel-self-test.py
```

The Python and Lean artifacts diversify the semantics implementation and checking machinery, but
they encode the same finite countermodel and therefore are not independent mathematical routes.
Neither formalizes motivic homotopy, validates the cited theorem, establishes the imported-arrow
correspondence, or proves a PID claim.

`check-formal-pdf-set.sh` fails closed if the declared LaTeX and PDF basename inventories
differ, if an unexpected paper is present without an explicit inventory update, or if any
individual PDF gate fails. Its default `--exact` mode requires byte identity and is therefore a
same-toolchain reproducibility check. Its `--cross-toolchain` mode rebuilds warning-free PDFs and
compares extracted text/layout, page count and geometry, and font embedding. CI uses the latter
because an unpinned runner TeX installation cannot defensibly promise byte identity with the
maintainer toolchain. The structural mode is not a pixel-identity or cross-toolchain byte-
reproducibility claim. These checks prevent a mathematical source or rendered paper from being
silently omitted. They verify artifact completeness and rendering properties, not theorem truth.

Before any PDF build, `check-formal-pdf-style.py` enforces the twelve-paper shared visual-system
contract: every paper loads the common package and title/section/header helpers exactly once,
every explicit `booktabs` top rule is followed by an explicit header-row band, Markdown-generated
workflow tables install the same band hook, and no source introduces vertical or legacy table
rules. `check-formal-pdf-style-self-test.py` proves that missing and duplicate header bands, a
`toprule` redefinition, a missing Markdown hook, a legacy rule, and palette drift all fail closed.
This is syntactic regression protection. It does not replace rendered-page inspection, establish
accessibility conformance, or validate the papers' mathematics.

The local `just release-audit` route also replays the standalone exact-count certifier (including
its Rust 1.89 test), exact-product/interval evidence, independent verifier, mutation suites, Lean
log-product theorem, claim binding, and supply-chain policy, plus the typed citation-edge
countermodel. These lanes remain deliberately separate: passing all of them is a layered assurance
result, not one end-to-end theorem connecting arbitrary Rust executions to population PID claims.

`check-markdown-math.py` checks every tracked or untracked Markdown file in the repository. It
rejects nonportable TeX delimiters, malformed display blocks, unbalanced inline math, bare TeX
outside math, unsafe table delimiters, display-only constructs in inline math, and commands that
GitHub's safe MathJax configuration blocks. In particular, it rejects named-operator commands.
Use a render-safe built-in operator or `\mathrm{...}`. It also applies a conservative
formula-in-code check to the theory documents. Its mutation suite proves that each rejected form
fails closed. The checker verifies syntax and rendering conventions only. It does not verify a
mathematical statement.

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
python3 scripts/generate-support-change-tolerant-sxpid-oracle.py
python3 scripts/generate-ksg-local-arithmetic-oracle.py
python3 scripts/generate-sxpid2-exhaustive-oracle.py
python3 scripts/check-markdown-math.py
python3 scripts/check-markdown-math-self-test.py
python3 scripts/check-review-evidence.py
python3 scripts/check-review-evidence-self-test.py
python3 scripts/check-z3-pid2-algebra.py
python3 scripts/check-z3-pid2-algebra-self-test.py
python3 scripts/check-lean-finite-convergence.py
python3 -O scripts/check-lean-finite-convergence.py
python3 scripts/check-lean-finite-convergence-self-test.py
python3 -O scripts/check-lean-finite-convergence-self-test.py
scripts/check-formal-pdf-set.sh
python3 scripts/check-formal-pdf-style.py
python3 scripts/check-formal-pdf-style-self-test.py

# Maintainer-only mechanical regeneration after an intentional source change:
python3 scripts/check-review-evidence.py --write
python3 scripts/generate-finite-alphabet-plugin-oracle.py --write
python3 scripts/generate-dependency-colored-sxpid-oracle.py --write
python3 scripts/generate-support-change-tolerant-sxpid-oracle.py --write
python3 scripts/generate-ksg-local-arithmetic-oracle.py --write
python3 scripts/generate-sxpid2-exhaustive-oracle.py --write
```

### Source observations, typed assurance, compact method/PID views, and current source state

`check-source-errata.py` validates the versioned reviewer-observation registry for the pinned
Ehrlich v3 and Schick-Poland v2 sources. The registry distinguishes construction identity,
reviewer-derived observations, upstream confirmation, proposed resolution, and implementation
status. It neither calls reviewer observations author-confirmed errata nor transfers an observation
between MGW categorical SxPID, Schick-Poland's proposed measure-theoretic construction, Ehrlich's
continuous construction, KSG, or repository compositions.

`check-assurance-registry-typed-view-v1.py` validates a derived, non-authoritative five-edge view of
the current assurance registry. Component evidence and correspondence evidence are separate;
inventory, model review, human review, formal results, executions, and release facts are
non-interchangeable dimensions. Missing formal-object-to-executable correspondence remains
explicit rather than being inferred from adjacent evidence.

`check-methods-summary.py` generates and validates the non-authoritative stable-first
`METHODS_SUMMARY.md` navigation view from the method catalog. Empty feature-gate inventories are
reported literally as no gates, not as default-surface availability, and experimental migration
bindings do not inherit a stable method row's status. `check-pid-mathematical-audit-protocol.py`
generates and validates ten construction-separated object cards, including distinct cards for
two-source PID, incomplete PID3 availability, and the full research PID3 lattice. Both schemas
retain controlled provenance/evidence/edge/independence vocabularies and confer no review credit.

`check-current-source-state-v1.py` validates a deterministic self-excluding manifest of the current
repository-visible source state. The manifest omits itself and any containing commit identifier,
so it has no checksum cycle; readers resolve the containing commit through Git. It records the
historical v0.9.0 ledger as tag-scoped inventory rather than current line or human review. It is not
authenticity, review, scientific, formal, visual, release, or application evidence.

`check-post-commit-source-state-v2.py` performs that resolution without putting a commit identifier
back into the tracked manifest. From a clean committed checkout it compares the index and exact
tracked worktree bytes/modes with `HEAD`, rejects repository-visible untracked divergence, validates
the tracked manifest against both its v1 checker/schema and the `HEAD` tree minus the manifest, and
then emits canonical JSON only on standard output. Its separate replay invocation consumes bounded
canonical JSON only from standard input. The deterministic artifact binds the commit, tree, and
manifest blob; it has no timestamp and is never committed. Repository-ignored products remain
outside this committed-tree identity projection. Repeated endpoint checks are not an atomic
filesystem history. Storage, path selection, durability, and upload custody belong to the caller
and are explicitly not claims of the artifact. The path-accepting v1 checker CLI is no longer
current; its schema is retained only as the historical v1 artifact shape. The artifact is identity
evidence only: it is not authenticity, attestation,
provenance, review or review completion, CI-pass, release, formal/scientific/numerical correctness,
or application validity.

```text
python3 -I -S -B scripts/check-source-errata.py
python3 -O -I -S -B scripts/check-source-errata.py
python3 -I -S -B scripts/check-source-errata-self-test.py
python3 -O -I -S -B scripts/check-source-errata-self-test.py
python3 -I -S -B scripts/check-assurance-registry-typed-view-v1.py
python3 -O -I -S -B scripts/check-assurance-registry-typed-view-v1.py
python3 -I -S -B scripts/check-assurance-registry-typed-view-v1-self-test.py
python3 -O -I -S -B scripts/check-assurance-registry-typed-view-v1-self-test.py
python3 -I -S -B scripts/check-methods-summary.py
python3 -O -I -S -B scripts/check-methods-summary.py
python3 -I -S -B scripts/check-methods-summary-self-test.py
python3 -O -I -S -B scripts/check-methods-summary-self-test.py
python3 -I -S -B scripts/check-pid-mathematical-audit-protocol.py
python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol.py
python3 -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
python3 -O -I -S -B scripts/check-pid-mathematical-audit-protocol-self-test.py
python3 -I -S -B scripts/check-current-source-state-v1.py
python3 -O -I -S -B scripts/check-current-source-state-v1.py
python3 -I -S -B scripts/check-current-source-state-v1-self-test.py
python3 -O -I -S -B scripts/check-current-source-state-v1-self-test.py

# Maintainer-only final regeneration after every other source byte and file mode is frozen:
python3 -I -S -B scripts/check-current-source-state-v1.py --emit \
  > audit/evidence/current-source-state-v1.json
```

After committing that final manifest, use an exact clean checkout. The shell creates private
temporary files for transport; the checker itself accepts no path argument:

```text
artifact_dir="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-post-commit-source-state.XXXXXX")"
artifact="$artifact_dir/post-commit-source-state-v2.json"
(umask 077; set -o noclobber
 python3 -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact"
 python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --emit > "$artifact.optimized")
cmp "$artifact" "$artifact.optimized"
python3 -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
python3 -O -I -S -B scripts/check-post-commit-source-state-v2.py --validate-stdin < "$artifact"
python3 -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
python3 -O -I -S -B scripts/check-post-commit-source-state-v2-self-test.py
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
offline. It also proves that the canonical workspace generator is absent from the extracted
layout, executes the exact archive-context snapshot test, and requires Cargo to report exactly
that one named test as passing. The test's `.cargo_vcs_info.json` path check is package-layout
context only; neither the marker nor this local replay authenticates an archive or establishes
provenance.

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
