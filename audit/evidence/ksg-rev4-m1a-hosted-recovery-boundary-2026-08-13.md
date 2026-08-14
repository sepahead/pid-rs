# KSG revision-4 M1a hosted-recovery boundary

- Implementation anchor: `cb3f58f0b190454cb3f1090de8798261ec78f194`
- Failed custody-correction anchor: `7473e62acef6077c2c1147e09d5d1297f2a2874b`
- Failed correction tree: `d0b2613e678a89318550c1797ba9cc59a4ec9478`
- Recovery lifecycle: G1 / M1a hosted wiring repair
- Current policy state: **frozen reviewed inventory; exact local lifecycle validation enabled; hosted pending; no credit**
<!-- ksg-m1a-hosted-recovery-policy-state: frozen -->

## Why a fast-forward recovery is required

The implementation identity remains `cb3f58f0...`. Its exact direct child `7473e62a...` remains the
frozen custody-correction subject, and its local precommit and postcommit custody observations
remain true only within their recorded scope. They did not observe a future hosted run.

CI run `31724449805` attempt 1 on `7473e62a...` completed with 43 successful and two failed jobs.
Job `94529230276`, **Exact-count directed-rounding SxPID2 reference**, passed the certified
mathematical checker in normal and optimized modes. Its subsequent normal certified self-test
failed because it deliberately reads the fixed `cb3f58f0...` checker authority with `git show`,
while that job's checkout retained only depth one. The exact public checkout invocation used
`--depth=1`; the fixed authority object was absent.

Job `94529230323`, **KSG integer-harmonic arithmetic and phase isolation**, separately failed in
the hosted custody-correction lifecycle with the exact visible line `KSG M1a custody-correction
self-test failed: accepted vector failed: certified_protocol: b''`. The provider record does not
expose or establish the hidden cause. A separate local cross-version reproduction found that the
frozen correction checker compared `ast.dump` text hashed under a different CPython minor even
though the reviewed certified bootstrap bytes were unchanged. The recovery therefore removes
that interpreter-minor-dependent comparison from its live protocol validation and uses exact raw
bytes plus version-stable source/AST relations; this diagnosis is reviewer-derived and is not
relabeled as a provider observation. Standalone CodeQL run `31724449083` attempt 1 succeeded on
the same head with no new alert number. None of these observations authenticates the provider,
proves causation, grants scientific credit, or changes another run's conclusion.

The failed CI run cannot be repaired by a rerun: an attempt-2 success would not rewrite attempt 1,
and the frozen composite-v2 parser requires a successful attempt 1 on the exact correction head.
No composite-v2 receipt is therefore issued. The public commit is not amended, reset, force-pushed,
or relabeled. One unsigned fast-forward sole-child recovery may repair only the missing hosted
history custody and its verifier, documentation, negative-evidence, byte-preserved Lean-r7,
append-only Lean-r8, and source-state consequences. The future composite-v3 receipt must bind the
entire linear chain and every distinct hosted observation.

## Exact repair

The certified-SxPID2 job's pinned `actions/checkout` step gains exactly:

```yaml
fetch-depth: 0
```

`persist-credentials: false` remains. Full history is required because later evidence descendants
move `cb3f58f0...` beyond every fixed finite depth. The repair must not substitute `HEAD^`, vendor a
second checker authority, skip on missing history, weaken the fixed SHA, or change the certified
mathematical packet. Only the reviewed workflow, Justfile, scripts README, exact certified job and
recipe container commitments may be rebound. The certified self-test continues to reconstruct the
candidate checker from `cb3f58f0...` and to reject a fourth container or unbounded semantic change.
The recovery verifier also replaces the failed correction checker's stored, CPython-minor-bearing
`ast.dump` digest with exact marked bootstrap bytes and structural relations computed within the
same running interpreter. It must reject semantic drift without claiming cross-version AST-text
identity or changing the certified mathematical result.

## Immutable predecessor custody

The recovery checker must read and rehash the exact Git objects for `cb3f58f0...` and
`7473e62a...`, including all nested tree objects and blobs. It binds:

1. the implementation tree `8070e0d3afbbd27d7381825f950ae6ff97ae7cf0` and sole parent
   `bbdfda40f0a49a2260b10eafdcb438fc61ae94e9`;
2. the unchanged 83-path protected projection, digest
   `37789ee0a6db5cab13629d08e70763eed6a55c1aeecbe94300717527419d0843`;
3. the failed correction's exact tree, sole parent, unsigned human envelope, message, and
   committed sealed-index SHA-256 `f9d1f42a...f232bc`, size `87963`, and entry count `724`;
4. every frozen v1 correction policy, boundary, checker, self-test, composite-v2 schema, r6 receipt,
   negative record, and current-source byte in that tree; and
5. the terminal, canonical run-31724449805 negative record plus the same-head successful CodeQL
   observation, without transferring success between them.

The recovery candidate is exactly the 27-path inventory in
[`ksg-rev4-m1a-hosted-recovery-path-policy-v1.json`](ksg-rev4-m1a-hosted-recovery-path-policy-v1.json):
19 modifications and 8 additions, no deletion. It is a sole child of `7473e62a...`; it is not a
replacement direct child of `cb3f58f0...` and does not change the implementation identity.

## Retired local r7 seal attempt

One later local r7-based precommit attempt also failed closed before any ref update. Its
unreachable checkpoint `37473f8fa9470fcec0bd419ec3df18ea4a6d805b` had candidate tree
`66f33f467f2bc661795599fa53ef81681ecd8406` and bound alternate-index SHA-256
`fb892aeaac2091e1d4c6b619a4ce0053771d8aeb0ee147105017613a3b46a56d`, size `88875`, and entry
count `731`. The inspected index was mode `0644`, not mode `0400`, so it never obtained accepted
sealed-index custody. Normal precommit emitted empty stdout and a 140-byte stderr record at
SHA-256 `173c39b502a86b3f62848a537cb178a8c2f215235382905b93fef3eb931251db`; the exact rejection
identified the legitimate zero-byte tracked blob
`audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout` as unsafe. These
host-local observations are unauthenticated negative evidence, not trusted time or provenance.
The checkpoint, tree, index identity, and outputs are retired and must not be reused or relabeled;
the r8 repair must construct a different fresh index and checkpoint.

## Freeze, replay, and sealed lifecycle

While the policy is provisional, validators emit only `local_hosted_pending_no_credit`. After the
complete terminal negative record and every authored recovery byte are independently reviewed, the
checker and prospective Lean-r8 maps are derived first. The recovery policy and boundary state flip
together as the final authored edit. Only the prescribed append-only r8 two-cut finalization and
self-excluding current-source generation may follow. The r6 and r7 receipts and old correction
authority remain byte-for-byte prior evidence; neither is current r8 runner custody.

The frozen recovery tree is written to a fresh alternate Git index outside the worktree. The index
is sealed mode `0400`, single-link, hashed, and committed by the exact unsigned sole-child message:

```text
Repair KSG M1a hosted recovery wiring

Sealed-index-SHA256: <lowercase-sha256>
Sealed-index-Size: <canonical-decimal-bytes>
```

Precommit supplies those exact bytes only on descriptor 0. Candidate-commit validation covers a
clean detached candidate before push. Postcommit validation requires the same exact commit as clean
attached `main` HEAD. Every mode checks the primary index, active-operation state, worktree, exact
delta, protected projection, predecessor objects, negative record, bounded certified rebind,
r6/r7 preservation, r8, current-source, and child execution custody in normal and optimized
Python. A local pass remains hosted-pending and no-credit.

## Composite-v3 descendant

The recovery subject must not contain either sealed-index artifact or its own hosted receipt. Only
a strict later descendant may add:

- `audit/evidence/ksg-rev4-m1a-custody-correction-sealed-index.bin`;
- `audit/evidence/ksg-rev4-m1a-hosted-recovery-sealed-index.bin`; and
- `audit/evidence/ksg-rev4-m1a-composite-receipt-v3-2026-08-13.json`.

The fixed composite-v3 parser must bind the exact chain `cb3f58f0... -> 7473e62a... -> recovery`,
both failed CI attempt-1 observations, both same-head successful CodeQL observations, separately
observed all-green CI and CodeQL only on the recovery head, both local four-mode phase records, both
sealed indexes and reconstructed trees, the unchanged 83-path projection at every subject, r5/r6/r7
preservation, current r8 custody, and both postcommit source-state artifacts. The receipt does not
hash or attest its own bytes or containing descendant. Provider IDs, timestamps, logs, and digests
remain unauthenticated observations.

## Scope and nonclaims

Revision 4 remains `integration_no_go`; all 13 integration gates remain open, and immutable
`evidence-matrix-v4.md` plus `decision-v4.md` remain absent. This repair is not KSG M1c,
scientific/formal correspondence, estimator validation, support or calibration evidence, PID2 or
PID3 evidence, categorical MGW shared-exclusions evidence, Williams--Beer `I_min` evidence, a
release, package result, or application claim. The r8 replay is current execution custody only for
its named Lean project; r6 and r7 are byte-preserved prior evidence, not current runner custody,
and none transfers any theorem to Rust or binary64.
