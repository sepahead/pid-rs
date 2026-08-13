# Lean 4.33.0 active baseline, replay, and freeze boundary

The active formal project is pinned exactly to `leanprover/lean4:v4.33.0`, Lean source commit
`d8b18978322de05a8f3dba51ef03cf5461676c17`, Mathlib tag `v4.33.0`, and Mathlib commit
`db584cd6d46c92f209a44c0f1c829460d327499d`. The complete nine-package closure is pinned by
[`lake-manifest.json`](lean/lake-manifest.json). The active policy is machine-readable in
[`toolchain-freeze-policy.json`](lean/toolchain-freeze-policy.json), and the bounded Darwin replay
is recorded separately in
[`lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json`](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-13-r5.json).
The [first 11 August replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json)
and [first 12 August replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json)
and [finalized r2 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r2.json)
and [finalized r3 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r3.json)
and [finalized r4 replay](../evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12-r4.json)
remain byte-preserved prior execution evidence. The 11 August receipt predates the hardened
runner; none is current runner custody. The `r5` suffix denotes only the fifth receipt in the
versioned sequence that originated on 12 August, and therefore the sixth current-project replay
receipt overall; the 11 August historical receipt is outside that versioned sequence. The suffix
does not denote a calendar date, replay schema, theorem, review, assurance tier, or independence
revision; the current receipt remains schema v2 and receives execution credit only when it exists
and validates.
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
  /private/tmp/pid-rs-sxpid2-atom-bridge.LHX9JM/repo/scripts/generate-lean-4.33-replay.py
```

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
The separate fully projected `replay_custody_gate_sha256` records the checker and self-test bytes
that were stable at both replay endpoints. The runner first no-clobber-publishes a provisional
receipt with the zero-placeholder checker. Finalization has exactly two tracked edits: replace only
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
