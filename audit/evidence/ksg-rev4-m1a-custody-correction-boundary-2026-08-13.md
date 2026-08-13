# KSG revision-4 M1a custody-correction boundary

- Implementation anchor: `cb3f58f0b190454cb3f1090de8798261ec78f194`
- Implementation tree: `8070e0d3afbbd27d7381825f950ae6ff97ae7cf0`
- Direct parent of the implementation anchor:
  `bbdfda40f0a49a2260b10eafdcb438fc61ae94e9`
- Correction lifecycle: G1 / M1a custody repair
- Current policy state: **frozen reviewed inventory; exact local lifecycle validation enabled; hosted pending; no credit**
<!-- ksg-m1a-custody-correction-policy-state: frozen -->

## Why a child correction is required

The implementation anchor is the exact unsigned M1a commit and remains the implementation subject.
Its first hosted CI run, `31686107959` attempt 1, is retained as a terminal failed run. Standalone
CodeQL run `31686106737` attempt 1 succeeded on the same head. A later successful run cannot erase,
rewrite, relabel, or make the failed run green. The failure transfers no scientific or lifecycle
credit, while its preservation is part of the correction evidence.

The correction must be one unsigned direct child of `cb3f58f0...`. It may repair only lifecycle,
custody, verifier wiring, and their exact documentation and Lean replay consequences. It must not
move the implementation identity away from `cb3f58f0...`, modify the reviewed 83-path M1a
implementation projection, or turn revision 4 into an integration decision.

## Fixed implementation projection

The protected projection is the sorted union of:

1. the 72 keys of `packet_files` in the implementation anchor's
   `claims/KSG-INTEGER-HARMONIC-001/active-packet-v4.json`;
2. that active packet itself;
3. `crates/pid-core/src/{kdtree.rs,ksg.rs,nn.rs}`;
4. the revision-4 checker and self-test;
5. the original M1a phase checker and self-test; and
6. the original M1a boundary, frozen path policy, and receipt-v1 schema.

Each row is exactly `{path,git_mode,git_blob_oid_sha1,sha256,size_bytes}`. Rows are sorted by path,
encoded as compact ASCII JSON with sorted keys and one LF, and hashed with SHA-256. At the
implementation anchor the projection has exactly 83 paths and digest
`37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843`.
Both the correction candidate and the committed correction must reconstruct that exact projection
from Git objects. Equality preserves those bytes; it does not prove their correctness or origin.

## Correction construction and local disposition

The path policy remains provisional while discretionary/authored candidate bytes are moving.
Provisional validation can emit only `local_hosted_pending_no_credit`. Once every authored byte
other than the coordinated policy/boundary flip is final, the final policy, boundary, correction
checker frozen-state/digest literals, and Lean-r6 typed maps are prospectively derived and reviewed.
The checker and prospective Lean maps are patched first. Then the policy inventory/lifecycle-validation
fields and boundary machine/human state flip together as the final authored edits. The policy's
`credit_permitted` field remains false: freezing enables exact local lifecycle validation, never
local credit. After that flip, no authored byte may change.
Only the prescribed append-only r6 receipt/checker cycle finalization and
self-excluding current-source generation may follow. The complete normal and optimized hostile suite
is rerun and the externally sealed tree is constructed only after both prescribed generators finish.
An observed working-tree delta is not review, and mechanical resealing is forbidden.

After those prescribed generators settle, the final authored correction tree is sealed into the
exact alternate index. Only then is the unsigned direct-child checkpoint created: its strict
message trailer records that immutable index's lowercase SHA-256 and canonical decimal byte size.
The checker source pins the trailer grammar, never the resulting digest, so the order is acyclic:
final tree → sealed index → message commitment → commit. Precommit validation requires the trailer
to equal the actual `fd0` bytes before any ref update.

Precommit construction uses an alternate index outside the worktree. Its exact bytes are supplied
only as read-only regular-file descriptor 0 (`fd0`); there is no path-valued index option. The checker
requires mode `0400`, one link, position zero, a stable descriptor identity, the externally
recorded SHA-256 and entry count, and two fixed-`/usr/bin/git` reconstructions from private copies.
It binds the exact direct-child checkpoint, commit envelope, clean operation state, primary index,
worktree overlay, protected projection, retained failure, r5 preservation, r6 replay, self-excluding
current-source manifest, the exact three-literal certified-SxPID verifier rebind, and the bounded
isolated-execution/CLI custody changes in that verifier and its self-test. The reviewed workflow and
Just routes execute both files as normal and optimized `-I -S -B` pairs; this does not alter the
certified mathematical packet or grant scientific credit.

Each correction child is compiled from exact candidate-tree source bytes supplied to the reviewed
stdin bootstrap under its logical authoritative `__file__`; the mutable source pathname is not
reopened. The bootstrap itself runs from a unique mode-`0500`, single-link private copy of
stable-read resolved interpreter bytes in a mode-`0700` private temporary directory. Source,
interpreter, and directory identities are checked again after execution, and successful children
must leave standard error empty. This binds the executed interpreter leaf and source transport; it
does not bind the interpreter's dynamic-loader closure, shared libraries, standard library, kernel
scheduling, or prove an atomic operating-system execution event.

Postcommit validation requires the same checkpoint to be clean `main` HEAD with sole parent
`cb3f58f0...`. Even a passing postcommit check emits only `local_hosted_pending_no_credit`.
Hosted success is future external state and cannot be asserted by the correction commit.
A distinct `candidate-commit` diagnostic validates that same exact committed direct child in a
clean detached pull-request/diagnostic checkout before push. It rejects attachment to `main`, does
not attach or update a ref, and emits only the same explicit no-credit hosted-pending disposition;
the separate strict postcommit route remains required after an exact push to `refs/heads/main`.

Before that push, candidate-commit validation checks the same exact committed tree and direct-child
envelope as a clean detached HEAD, including pull-request head checkouts. It accepts no sealed-index
arguments and emits only a detached-candidate, hosted-pending, no-credit result. This diagnostic
cannot substitute for either the sealed precommit construction or the attached-main postcommit
lifecycle, but it prevents those substantive tree checks from being deferred until after a push.

## Composite descendant receipt

The composite receipt described by
[`ksg-rev4-m1a-composite-receipt-v2.schema.json`](../schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json)
must be absent from both the implementation and correction trees. Only a later descendant may bind:

- the unchanged implementation anchor, tree, parent, and 83-path projection;
- the terminal failed CI and successful CodeQL observations on the implementation head;
- the exact correction direct child and its local phase custody;
- terminal all-green CI and CodeQL observations on the distinct correction head; and
- the correction's uploaded post-commit source-state artifact.

The receipt does not attest its own bytes or containing commit. Hosted identifiers and digests are
unauthenticated provider observations, not trusted time, authorship, transparency, or provenance.
The same strict descendant must retain
`audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin`; its exact Git blob, SHA-256,
byte size, twice-reconstructed tree, and full entry count must equal the correction commit's message
commitment and the historical precommit observation. Descriptor mode/read-only/link observations
remain explicitly unauthenticated historical facts rather than properties inferred from that blob.

## Scope and nonclaims

Revision 4 stays `integration_no_go`; all 13 integration gates remain open, and
`evidence-matrix-v4.md` plus `decision-v4.md` remain absent. The correction is not scientific,
formal, estimator, calibration, support, PID, application, release, or package evidence. It does
not establish general neighbor-search correctness or transfer the fixed KSG witnesses to continuous
PID2/PID3, categorical MGW SxPID, Williams--Beer `I_min`, fitted-quantized compositions, wrappers,
or consumers. The r6 replay is fresh execution custody for its named Lean project only and does not
transfer a theorem to Rust or binary64.
