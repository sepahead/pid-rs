# Independent review of candidate-only repair and narrower execution scope

The proposed repair is acceptable for testing under the unchanged revision-3 judge. The revised
allocation can complete both candidate forms in both Python modes within the original campaign.
It provides fewer duplicate executions than previously planned. That loss must remain explicit.
No successful complete result exists for the repaired candidate at this review.

The reviewer inspected the registered source before a repaired full run. The coordinator selected
and wrote the repair. The reviewer authored the original judge and reported the roster failure;
this is a separate critical review, not external or blinded custody.

## Exact source and trust boundary

The retained old source has 10,328 bytes and SHA-256
`76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
The repaired source has 10,272 bytes and SHA-256
`af925aacc56cf765e875ba8bdce41e62139fc9c8be9317a87e5d63df69cf7af2`.
Byte comparison confirms exactly seven replacements of `decide +kernel` by `decide`, with no
other byte change. Every theorem statement, binder, import, option, assumption, and name remains.
The source registration SHA-256 is
`ce80b8b3e97d24dd92c7d19ad11b4c6a6121f5f6437faf8615b569dd207dce45`.

The old candidate produced seven additional theorem names inside the namespace that the frozen
judge constrains to thirteen names. The predicate rejected that candidate correctly. The repair
changes the tactic's proof construction; it does not remove the namespace check or reinterpret
those observed names as private. A new compile and environment check must establish whether the
repaired source has the required roster.

The pinned Lean source is `Lean/Elab/Tactic/Decide.lean`, SHA-256
`99e84ce67778157e77d7261aa25b64ed72da16e9d1f60031cf2aa26f5ea6ee68`.
Its `doElab` branch, lines 90–99, calls `mkDecideProof`, checks the reducible decision, and returns
the proof term. Its `doKernel` branch, lines 108–118, calls `mkAuxLemma` and returns the resulting
constant. Thus ordinary `decide` removes this auxiliary-lemma construction; it does not grant
an axiom or replace Lean's final proof checking with native evaluation. Actual execution and
the unchanged `leanchecker --fresh SemanticJudge` gate remain required. This source inspection
alone is not a complete candidate proof or an assertion of source-to-binary authenticity.

The pinned [Lean tactic source](https://github.com/leanprover/lean4/blob/d8b18978322de05a8f3dba51ef03cf5461676c17/src/Lean/Elab/Tactic/Decide.lean#L90)
provides the cited branch. The diagnostic records the compiler identity. `ROSTER_REJECTION.md`
maps all seven observed theorem names and full proposition types to the seven source calls.

## Ten considered routes

| Route | Disposition |
|---|---|
| Keep the old candidate and retry | Reject; its actual roster still has twenty declarations |
| Drop the exact namespace predicate | Reject; changes the adopted acceptance target |
| Treat all generated names as private | Reject without a distinct policy and source semantics |
| Add seven names to the allowed roster | Reject; expands the public interface |
| Add axioms or native evaluation | Reject; changes the proof trust boundary |
| Replace exactly seven tactics with ordinary `decide` | Accept for a registered test under unchanged predicates |
| Rewrite all finite proofs manually | Possible but broader than the identified construction issue |
| Preserve six further successful runs under cap eight | Impossible after three failures; do not claim this allocation ran |
| Raise or reset the campaign budget | Reject under the current instruction |
| Root runs selected normal/O; worker runs cosmetic normal/O | Accept with explicit loss of the additional duplicate selected pair |

## Evidence scope and remaining limits

Three failed full wrappers remain consumed. Root-selected normal and optimized runs use slots
4 and 5. Worker cosmetic normal and optimized runs use slots 6 and 7. Slot 8 is held for an
actual failure and is not an automatic repetition. The cap remains eight; the deadline remains
08:32:36 UTC on 2026-09-05. Five development compilations have run, including the declaration
diagnostic, under the existing cap of sixty-four.

The revised four required full runs still test selected and cosmetic forms in both Python
modes, with the full target types, transitive axiom roster, exact export set, source policy,
resource controls, and fresh kernel closure. The coordinator executes the selected pair, so
there is no additional successful worker-selected pair followed by a duplicate coordinator
pair. This is a narrower execution history; do not describe it as equivalent repetition or
independent confirmation of the superseded six-success plan.

The old candidate, its comment-only snapshot, all three failures, the unexecuted slot 4–6
registrations, and the old allocation remain in the archive. A repaired-candidate cosmetic
prefix must be declared before writing and testing that new variant. The record remains a
feedback-driven deterministic proof campaign. It supplies no statistical selection, novelty,
priority, estimator-calibration, or external-attestation claim.

## Separate complete reporting regression

The original frozen reporting helper binds the old candidate and is inapplicable to a complete
pass of the repaired source. Preserve the original file and its frozen hash. A separately
named helper may replace only that selected-source identity expression with the exact repaired
source hash. It must retain the positive receipt, freeze, artifact, compiler, thirteen-record,
fresh-kernel-status and exact restored-module checks. Its source must have a separate reviewed
manifest and execution registration. It is not a member of the old frozen file roster.

The complete regression must use imports from an actual accepted repaired-candidate run, restore
the exact old thirteen-site semantic source, and require the original twelve Unit plus one
metavariable mismatch shape. The helper's changed source must be captured and hash-checked before
execution and verified again afterward. No result from the old helper on the old candidate may
be relabelled as a result for the repaired candidate. All actual failures remain evidence.
