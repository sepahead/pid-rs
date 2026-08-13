# KSG revision-4 M1a candidate boundary

- Anchor commit: `bbdfda40f0a49a2260b10eafdcb438fc61ae94e9`
- Anchor tree: `b54a8bad05ab7b115f8016fd3c993a5aea74162c`
- Lifecycle gate: G1 / M1a
- Current policy state: **frozen reviewed inventory; M1a credit eligible only with external custody**
<!-- ksg-m1a-policy-state: frozen -->
- Final receipt path, created only by a descendant:
  `audit/evidence/ksg-rev4-m1a-implementation-receipt-2026-08-13.json`

## Purpose and present status

The all-green `bbdfda4...` state is the declared parent, not the canonical M1a implementation.
Its delta repaired post-commit source-state, Lean, and SxPID custody and did not introduce a
bounded KSG implementation change. M1a therefore requires a new direct child whose exact delta is
limited by [`ksg-rev4-m1a-path-policy-v1.json`](ksg-rev4-m1a-path-policy-v1.json).

The policy inventory covers the runtime, revision-4 preclosure, mandatory changelog, durable
program-status coordination, Lean-r5, current-source-state, and lifecycle consequences. Its exact
state is the line and machine marker above: the provisional state grants no credit, while the
frozen state is eligible only after human review of the exact sorted inventory and successful
hostile replay. The checker binds that live state and, once frozen, the reviewed policy digest.
Observing a moving Git delta is never a substitute for that review.

## Scientific and engineering boundary

M1a may bind fixed-input KSG implementation correspondence: strict-radius predecessor behavior,
exclusive count successors, brute/kd-tree equality on the reviewed witness, x-block/pair route
parity, and the existing inclusive Ehrlich witness where revision-4 already requires it. This is
not a general neighbor-search proof, estimator consistency or calibration result, population
support evidence, or a transfer to continuous PID2/PID3, categorical MGW SxPID, Williams--Beer
`I_min`, fitted-quantized compositions, wrappers, consumers, or applications.

General `nextafter`-adjacent and boundary-shell brute/kd-tree parity remains a separate P2 backlog
item. A bounded immediate-predecessor strict-radius regression used to guard the KSG count map
does not close that general item and must not be reported as doing so. The exact harmonic identity
and its rectangular-arithmetic-domain bound likewise do not assert that every outer-box tuple is
runtime attainable.

Revision 4 remains `integration_no_go` throughout M1a. All 13 integration gates remain open, and
`evidence-matrix-v4.md` plus `decision-v4.md` remain absent. Neither the M1a commit nor a green
hosted run is scientific evidence or final repository-integration authority.

## Cycle-free construction and promotion

1. Stop every discretionary/authored writer and freeze the reviewed policy inventory. Then run
   the prescribed append-only Lean-r5 generator and finalize its non-cyclic receipt/checker pair.
   Regenerate the self-excluding current-source manifest last and freeze it too. These two bounded
   generators are part of the reviewed inventory, not discretionary additions after review.
2. Starting from the exact bbdf index, construct a separate alternate index outside the repository
   worktree containing exactly the frozen policy delta. Record its bytes, mode, link count, entry
   count, and SHA-256 externally.
3. Open that sealed file as standard input and give the checker only its externally recorded
   SHA-256 and entry count. The checker verifies regular-file descriptor 0 is read-only,
   positioned at byte zero, mode `0400`, single-link, and stable while it reads the bounded bytes
   once; it then makes
   two private copies and uses the same fixed Git implementation twice to reconstruct and
   enumerate the tree. Both repetitions must equal the externally recorded candidate tree and its
   exact entries. This is repeated reconstruction plus external custody, not an independent tree
   algorithm. The checker receives no alternate-index pathname and makes no path-residency claim.
4. Create one unsigned detached `git commit-tree` checkpoint with that tree, bbdf as its sole
   parent, the exact reviewed human identity, and the policy message. The checkpoint itself is the
   prospective M1a commit; do not create a second content-equivalent commit.
5. In precommit mode, the phase checker requires symbolic branch `main`, no merge/rebase/
   cherry-pick/revert/bisect/sequencer state, HEAD=bbdf, the primary index equal to bbdf, the
   repository-visible worktree/untracked overlay equal to the policy delta, the sealed
   alternate-index bytes on standard input to reconstruct the supplied tree, and the supplied
   checkpoint to match it exactly.
6. After all settled-tree gates pass, move the branch ref directly to the checkpoint with an
   expected-old-value guard. Then load the checkpoint into the primary index without changing the
   worktree and require a clean postcommit state.
7. In postcommit mode, the checker requires symbolic branch `main`, no active Git operation,
   HEAD=checkpoint, one parent bbdf, the exact tree/delta, and no tracked, repository-visible
   untracked, staged, signature, attribution, or replacement/graft contamination. Ignored build
   products are outside the candidate source projection and are not enumerated or claimed absent.
   Push by fast-forward only if remote `main` still names bbdf.

The phase checker and its self-test cannot hash themselves without a cycle. Their bytes are bound
by the independently recorded candidate tree, detached checkpoint, eventual unsigned commit,
remote observation, and later receipt. A tree made only after coordinated verifier weakening is
consistency evidence, not trust; human review and external custody remain cuts.

## Descendant receipt and M1c

After M1a is pushed and remotely observed, a separate descendant may add the canonical receipt
defined by
[`ksg-rev4-m1a-receipt-v1.schema.json`](../schemas/ksg-rev4-m1a-receipt-v1.schema.json).
It records only the pre-existing M1a subject, phase-custody outputs, remote observation, hosted run,
and uploaded post-commit source-state-v2 artifact. It is absent from the M1a tree, does not hash
itself, and makes no claim about its own containing commit.

At M1c, the active packet must content-bind the receipt path and SHA-256; the decision's
`m1a_receipt` object is exactly `{path, sha256}`, and its implementation commit must equal the
receipt's `subject.implementation_commit`. The M1a receipt is distinct from whatever gate-specific
evidence contracts a future M1c checker ultimately defines. M1c cannot claim its own hosted success
inside itself; that needs a later external observation or another descendant.

The current revision-4 harmonic checker intentionally contains no positive M1c/final-authority
parser. Its default route remains red. The final lifecycle, subject typing, gate-specific evidence
contracts, and later hosted observation must be designed and reviewed as a separate versioned
checker only after the real M1a receipt exists; synthetic precommit fixtures grant no such credit.
