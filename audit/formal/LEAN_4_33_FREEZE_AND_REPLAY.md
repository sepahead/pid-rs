# Lean 4.33.0 active baseline, replay, and freeze boundary

The active formal project is pinned exactly to `leanprover/lean4:v4.33.0`, Lean source commit
`d8b18978322de05a8f3dba51ef03cf5461676c17`, Mathlib tag `v4.33.0`, and Mathlib commit
`db584cd6d46c92f209a44c0f1c829460d327499d`. The complete nine-package closure is pinned by
[`lake-manifest.json`](lean/lake-manifest.json). The active policy is machine-readable in
[`toolchain-freeze-policy.json`](lean/toolchain-freeze-policy.json), and the bounded Darwin replay
is recorded separately in
[`lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json`](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json).
The [first 11 August replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json)
and [first 12 August replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json)
and [finalized r2 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r2.json)
and [finalized r3 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r3.json)
and [finalized r4 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r4.json)
and [finalized r5 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json)
and [finalized r6 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r6.json)
and [finalized r7 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r7.json)
and [finalized r8 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-14-r8.json)
and [finalized r9 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9.json)
and [finalized r10 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r10.json)
and [finalized r11 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r11.json)
and [finalized r12 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r12.json)
and [finalized r13 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r13.json)
remain byte-preserved prior execution evidence. The 11 August receipt predates the hardened
runner; none is current runner custody. The `r14` suffix denotes the fourteenth accepted slot in the
sequence beginning 12 August. Counting the separate 11 August historical receipt, it is the
fifteenth receipt in the accepted/historical lineage. Rejected same-slot artifacts are additional
zero-credit documents; no total count of every generated receipt is claimed. The suffix does not
denote a calendar date, replay schema, theorem, review, assurance tier, or independence revision;
the current receipt remains schema v2 and receives execution credit only when it exists and
validates.

One additional schema-v2 document is retained as a failed-publication attempt rather than as an
accepted current member of that sequence. Its [bounded execution and receipt-finalization
predicates passed, but C4 closure
rejected it before push](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-15-r9-prepublication-closure-rejected-2026-08-17.json)
for the same 748 entries: the generator's 132,893 newline-free compact bytes hash to
`b336e6f54450090693731f2391b1ef3e112095dd9a9c8cbdadddbf2f855fba47`, while the first
composite checker's 132,894 bytes with one terminal line feed hash to
`7d4d4fd6bc478aeb20008cd05d1efe4b92b6ca9fd72a72043e67322e6a722f20`. The exact
132,710-byte artifact has SHA-256
`fb162cc40da3059b61eab9024f4aa38cf6daf2d84ef7e1d8a26dc7d345291e70`. Its internal
`status = passed` records only that attempt's bounded execution. Local commit
`e02d27bec91f142949336f9f28550c672d22b297` was never pushed or accepted as C4; the candidate
receives no C4-publication, hosted, scientific, accepted-current-replay, or independence credit.
The corrected current receipt must bind those raw bytes as retained pre-publication closure
evidence outside the accepted replay lineage, without renumbering or relabelling them.

Published C8's repository CI and dedicated-v8 route both ended at the exact marker
`certified SxPID2 claim check failed: release-audit just dependency line exact digest changed`.
That is the first reached comparison, not a complete mismatch inventory.

A later same-slot `r14` from C9 candidate
`0a6ece9c525ad7aad061f55b3edea83554891b42`, tree
`1d5446f19d34b742feeb51429bf58a0706750757`, which was not observed accepted or published on `main`
as C9 in the bounded provider/history checks, is likewise outside the accepted sequence. Its exact
145,611 bytes hash to
`2a882358e158ebeae06dbdf8d1cd35637d698f59ce217c1e2fbecf1d8787dfb7`. Lean execution and
receipt finalization passed for those candidate bytes, but the subsequent required
`just ksg-composite-v9` run inherited `umask 077`; its last confirmed output line was
`ok 273 - refresh writer reports an injected second-replacement failure`, and the next observed
stable diagnostic had prefix `refresh destination mode drifted: ` and path suffix
`/root/output/pdf/workflow.pdf`. No complete raw transcript or whole-run digest of that required run
was retained. A separate direct workflow-PDF self-test under `umask 022` passed 366/366 controls but
is documentary only, was not checker-replayed as a C9 qualification run, and receives zero
qualification credit. No L8 record is installed; no operator-invocation history is claimed. No L9
exists; GitHub exposed no workflow run for the candidate on 21 August and
still resolved `main` to exact C8. Mutable provider ref
`refs/heads/archive/composite-v9-rejected-workflow-pdf-umask-20260821` was observed at the candidate
commit and is only a mutable recovery locator, not authentication, durability, or accepted-on-main
C9 publication. The deterministic checker binds the recorded identifiers but does not query the
provider archive, main, or workflow-run endpoints or require the sibling commit object. The rejected
receipt receives zero C9/R9,
accepted-current-replay, scientific, hosted, qualification, or independence credit; it must not
enter `prior_replay_*`, be copied, or be relabelled. A corrected fresh direct child of C8 must
generate a completely fresh one-shot `r14` after every operational byte settles. Reusing the same
relative pathname and sequence slot does not identify the bytes or transfer credit. The fresh C9
changed-path set contains 32 paths; the rejected candidate's changed-path set contained 31. The
sole path-set membership difference is the fresh C9 addition of
`scripts/check-mathematical-workflow-pdf-self-test.sh`; this is a set-membership statement, not a
claim that shared paths have identical bytes. That path is not a sixth stale binding,
production-writer, PDF, theorem, or estimator change.
Local-recipe and hosted-post-setup qualification select exact GIL-enabled CPython 3.14.6, while one
hosted pre-setup checkout-normalizer call plus four normal/optimized action-pin checker/self-test
calls remain runner-Python surfaces outside that lane. Exact
source-slice equality observed on CPython 3.11.13, 3.12.11, 3.13.7, and 3.14.6 is documentary only
and receives no qualification or portability credit; bounded preflights do not authenticate
interpreter bytes, prove atomicity or TOCTOU absence, or enumerate every transitive process. The
AST/source-route checks and hostile mutations are finite regression evidence for a fixed lexical
roster, not proofs of semantic soundness, causal execution, or non-bypass. Dynamic namespace
mutation and arbitrary execution custody remain outside those analyses. Exact whole-file, tree,
replay, and human-review custody remain authoritative within their stated bounds.

The exact dependency revisions were also checked against the separately generated manifest in the
bounded, retrospective
[`manifest-regeneration observation`](../evidence/lean-4.33.0-manifest-regeneration-2026-08-11.json).
That observation retains no raw command transcript or timestamps and therefore receives revision
and manifest-closure credit only, not execution-transcript or independent-review credit.

This is the final baseline until a declared trigger is met. A newer Lean release alone does not
trigger work. Reevaluation is permitted only for a material security or kernel issue; a required
maintained capability, dependency, platform, or build route that is blocked with no acceptable
pinned-baseline workaround; sustained and reproducible unavailability across maintained official
and repository-cache routes; or an exceptional, recorded human decision with rationale. A release
candidate, nightly, social post, elapsed cadence, optional capability, unmeasured performance
claim, automated dependency proposal, or transient network/host failure is not a trigger. The old
baseline remains current until every candidate gate closes and a rollback plan exists. Every later
migration must create a new versioned receipt; it must not edit an earlier observation to make it
look current.

## What changed for 4.33.0

The toolchain, Mathlib tag, and all transitive manifest revisions moved together. Lean 4.33 enables
`backward.isDefEq.respectTransparency.types` by default. The [official migration
note](https://lean-lang.org/doc/reference/latest/releases/v4.33.0/#breaking-changes) prescribes
`set_option backward.isDefEq.respectTransparency.types false` as the compatibility switch and says
to scope it as narrowly as possible. The broader parent option is deliberately forbidden: [Lean's
exact 4.33 source](https://github.com/leanprover/lean4/blob/d8b18978322de05a8f3dba51ef03cf5461676c17/src/Lean/Meta/ExprDefEq.lean#L27-L61)
shows that disabling it also changes implicit-argument unification, and the [diagnostic
path](https://github.com/leanprover/lean4/blob/d8b18978322de05a8f3dba51ef03cf5461676c17/src/Lean/Meta/ExprDefEq.lean#L479-L515)
distinguishes the narrower `.types` behavior.

Exactly seven narrow `set_option backward.isDefEq.respectTransparency.types false in` routes
remain: three command scopes and four proof-term-local scopes:

- one around only the generated `Fintype` instance for `SxPid2Node`;
- two around only the generated `Fintype` instances for `SxPid2Component` and `SxPid2Atom`;
- three inside the proof terms of the exact finite `decide` examples in
  `PidFiniteConvergenceSemanticContract.lean`; and
- one inside the proof term of the private `weighted_count_facts` theorem in the atom semantic
  contract.

There is no file-global or broad compatibility flag. Explicit `Finset` membership proof bodies in
`SxEventBridge.lean` and the first three semantic examples were also made well-typed under 4.33's
new default. No theorem statement, source-written non-proof public definition body, declaration name, import,
permitted-axiom policy, PID formula, or numerical implementation changed. The aggregate
source-written inventory remains 11 sources, eight imported modules, 339 entries, and 246 named
source theorems, with every theorem's axiom set contained in `propext`, `Classical.choice`, and
`Quot.sound`.

This is not a claim that the complete generated Lean environment is byte- or metadata-identical
across releases. In the bounded comparison, the six derived `Fintype`/`DecidableEq` instances for
`SxPid2Node`, `SxPid2Component`, and `SxPid2Atom` retain matching normalized pretty-printed
declaration skeletons and still synthesize, while their printed reducibility metadata changes from 4.32
`@[implicit_reducible]` to 4.33 `@[instance_reducible]`. That known elaboration-metadata delta is
recorded separately from the source-written inventory. Lean's pretty printer elides proof subterms
and names generated helper proofs without printing their bodies, so this receipt does not compare
those proof bodies or helper declarations.

## Replay and nonclaims

The versioned receipt records the official Darwin archive size and digest, pinned executable
path/digest snapshots and exact version output,
a static exact inspection of the nine-package committed manifest closure, exact source digests, a
project-build-clean `lake --quiet --wfail build PidFiniteConvergence` replay whose only accepted
successful streams are empty, 11 direct unlimited-heartbeat compilations, cache-independent
`leanchecker --fresh`, and the complete 246-name theorem-axiom audit. The generated axiom query is bound at exactly 18,200
bytes with SHA-256 `30acaa1de98051b247a91b735eb8ab08f2870a7f6e23b81c18c362815681b2e4`;
nonempty or ad hoc standard input receives no credit. Current companion Lean gates and their
normal/optimized Python output pairs are also recorded. Every replayed Python command uses
`-I -S -B` (and `-O -I -S -B` for its optimized pair). Every command receives either the exact
recorded theorem-audit payload or an explicitly supplied, seekable-file-backed empty standard
input; none inherits caller input. The runner fixes its process and child-file creation mask to `0077`, clears the inherited
signal mask, and restores default dispositions for `SIGHUP`, `SIGINT`, `SIGTERM`, `SIGPIPE`, and
`SIGCHLD`; other operating-system process limits remain execution premises. The command
environment is built from an
exact 15-variable nonsecret allowlist with fixed locale/timezone and fresh empty `HOME` and
`TMPDIR`; ambient Lean, Lake, Elan, Git, and Python routing is not inherited. Exact Lean and Lake
identity output is checked before the clean build begins.

The complete receipt-bound static surface is checked immediately before and after the ordered
command sequence. This endpoint equality detects bounded concurrent drift but is not an atomic
filesystem snapshot.

The retained, exact-hash-bound runner accepts no arguments. Its repository, output, Darwin
Lean-bin, Python, and archive routes are literal reviewed inputs rather than caller-controlled
path or executable authority:

```text
/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/bin/python3.14 \
  -I -S -B \
/private/tmp/pid-rs-c9-rebuild.vVNPnk/repo/scripts/generate-lean-4.33-replay.py
```

Finalized r6--r13 receipts retain their exact historical observed routes and bytes. Before r14
exists, the hostile suite uses r13 only as a non-evidentiary shape seed inside a disposable
fixture: it rehomes the synthetic execution root, command working directories, dependency
working directories, and the nine root-check output streams to the reviewed C9 route. It also
refreshes all checker-bound active/current and preservation inventory fields in the disposable
fixture and recomputes its synthetic projection/custody values. Every one of those changes is
confined to the non-evidentiary fixture: it never rewrites a retained receipt or assigns fresh
execution credit. The exact historical receipts remain independently hash- and schema-bound, while
the simulated r14 route must satisfy the current literal route checks.

Any extra argument is rejected before runner-controlled repository/archive/output lookup,
repository-module load, child launch, or write. The runner opens the pinned
archive without following symlinks, requires a single-link regular file, and checks stable
descriptor identity, exact size, and SHA-256 before any replay command. Immediately before the
clean build it uses symlink-aware entry checks for absent project build/config paths and the
retained dependency-package directory. Removing caller-controlled path selection does not
authenticate the pinned host-local executables or establish executed-tree-to-archive provenance.
The pinned set includes `lean`, `lake`, `leanchecker`, and Python. Lake's child selection is bounded
by the exact release-bin-first `PATH` and snapshots of the resolved Lean and LeanChecker leaves.
The stable executable snapshots immediately before each direct launch and after the replay detect
bounded drift, but neither they nor Lake's child selection prove the operating system executed
those exact bytes atomically.

The current KSG record is the 4.33 evidence JSON plus its versioned replay addendum. The unchanged
`formal-assurance-v4.md` remains historical 4.32 execution evidence. Likewise, the current
count/event and count/atom authority documents bind the 4.33 replay and 80-route aggregate while
their dated phase-A receipt remains a 4.32/71-route observation. The custody gate binds the complete
selected KSG, count/event, and count/atom active-authority inventory; it does not relabel any old
receipt.

The replay receipt has a reviewed canonical projection covering its timestamps, observed paths,
command streams, current evidence, and claim inventories. Within `custody_gate_sha256`, only the
checker digest is omitted from that projection to avoid a checker/receipt digest cycle; the
self-test digest remains reviewed, and both custody digests are compared directly with live files.
Before any replay command, the zero-argument runner independently checks the complete acyclic
composite-v9 cut state from source bytes. The replay-projection line is exactly the unique zero
placeholder. The Lean composite-v9 scalar and its v9 operational-map row are identical nonzero
literals equal to the final composite-v9 checker SHA-256. That v9 checker contains one nonzero
`EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256` literal equal to the Lean checker hash after normalizing
exactly the projection, v9 scalar, and v9 operational row to their exact placeholder forms. The
immutable composite-v4/v5/v6/v7/v8 checkers and r9/r10/r11/r12/r13 receipts remain prior evidence;
none is rewritten, and the ordinary retained v4/v5/v6/v7/v8 operational rows are outside this
normalization.

The cut is finalized in one direction. Freeze the v9 self-test and every non-cut Lean input first;
compute `H_L` from the three-placeholder Lean normalization and place only `H_L` in the v9
checker; hash those final v9 checker bytes as `H_V`; place the same `H_V` in only the Lean v9 scalar
and v9 operational row; and keep the replay projection as the zero expression until the one-shot
generator succeeds. Changing the v9 self-test, documentation, or any other normalized Lean input
after computing `H_L` invalidates the sequence. Missing, duplicated, stale, mismatched, causally
changed, or prematurely finalized cuts stop the runner before publication. The self-tests exercise
the positive construction plus checker-drift, projection-finalized, missing-cut, duplicated-cut,
mismatched-cut, normalized-cut, and operational-map-omission mutations.
The v9 hostile suite must also exercise the live pre-replay state: when the projection is the unique
zero placeholder and the scalar/map cuts bind the final v9 checker, the normalized-Lean binding in
that checker must be one unique one-line literal equal to the three-placeholder Lean hash. Synthetic
cut mutations do not establish this live readiness predicate. The Lean self-test therefore calls
the generator's own side-effect-free live cut validator in that state and emits
`live-pre-replay-ready`, which the replay transcript preserves; the distinct
`authoring-placeholders-not-generator-ready` result carries no readiness credit. The first fresh-C9 generator
invocation demonstrated the distinction by failing closed on a multiline binding before any Lean
child command, build/config creation, or receipt publication; it created no `r14`. The cut was reset
to placeholders, the live guard was added, and every affected digest must be recomputed before a
separately reviewed later invocation. That preflight failure has zero replay, execution,
qualification, or scientific credit.
The separate fully projected `replay_custody_gate_sha256` records the checker and self-test bytes
that were stable at both replay endpoints. The runner first no-clobber-publishes a provisional
receipt with the zero-placeholder checker. It constructs the receipt through a retained descriptor
on a private mode-`0600` temporary inode, verifies the complete bytes and identity, changes that
same inode to exact mode `0644`, fsyncs it, links the final no-clobber name, removes the temporary
name, and validates the final single-link mode-`0644` bytes. No post-publication chmod is part of
the lifecycle. Finalization has exactly two tracked edits: replace only
the checker's projection literal, then replace only the live
`custody_gate_sha256["scripts/check-lean-toolchain-freeze.py"]` value in that provisional receipt
with the final checker digest. The replay-custody checker digest remains the endpoint hash. The
reviewed projection deliberately omits the live checker digest, so it must remain unchanged and
equal the pinned value across the receipt edit. After normal/optimized checker and self-test replay,
the finalized receipt becomes immutable. The final checker reconstructs the zero-placeholder
replay bytes and verifies their hash, while the self-test replay and final hashes must remain
identical.
CI, local command wiring, this policy
document, and the operational guide are separately exact-hash bound. The custody checker and its
mutation suite validate these records, the freeze policy, active bytes, and preserved historical
hashes:

```text
python3 -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze.py
python3 -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
python3 -O -I -S -B scripts/check-lean-toolchain-freeze-self-test.py
```

These are correlated repository-local checks. They do not authenticate GitHub or Lean's publisher,
establish executed-tree-to-archive byte provenance, prove that the release archive was
reproducibly built from the reported source commit, prove Lean kernel soundness or theorem intent,
or refine exact-real results to Rust, binary64, estimators,
sampling laws, populations, or applications. The seven narrow compatibility scopes and explicit
proof rewrites preserve the checked source under this selected toolchain; they are not a general
semantic-equivalence theorem between Lean releases.

## Historical evidence

All existing Lean 4.32.0 and 4.32.2 receipts, phase records, formal-assurance snapshots, and the
standalone issue-14576 custody packet remain historical evidence. Their version strings, hashes,
limitations, and outcomes are intentionally unchanged. Current documents may cite this 4.33.0
replay in addition to those records, but must not relabel a 4.32 observation as a 4.33 execution.
