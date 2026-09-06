# Initial coordinating review of the DNF judge reporting failure

This record precedes review of the verifier's amendment recommendation. The candidate author
reported the failure; that report informed this review. The coordinator inspected the exact
original judge and independently ran it on the unchanged candidate. This is not an independent
candidate proposal, external custody, or a blinded scientific review.

Candidate SHA-256: `76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
Original judge freeze: `e4baedd90547d230e18bcfee1867d54e9697238f44ff306cbbd2529bc34b1d05`.
Root original-judge receipt: `f14e29462e063ecc5f1e07a6128ffc6f3df48e1333b5031741505a07ad315d30`.
The complete13-proof source compiles, but the full judge is not accepted. No fresh semantic
closure kernel check occurred. Both full-run failures must remain terminal failures of v2.

## Cause and selected repair proposal

`SemanticJudge.lean` opens `Lean.Elab.Command`. Its13 unqualified `liftIO` calls resolve to
`Lean.Elab.Command.liftIO`, whose result is `CommandElabM`. They occur inside `liftTermElabM`,
which expects `TermElabM`. The pinned Lean source `Lean/Elab/Command.lean:222` defines that
command-specific function; line731 defines the term-to-command bridge. The error is an
elaboration mismatch in reporting code. It is not a counterexample to a DNF theorem.

The70 passing preparation controls tested the semantic core, raw/alias targets, finite controls,
wrong-target proofs, parsers, source custody, processes, and a fresh positive-control kernel
closure. They did not compile the complete reporting module. The full13-export positive remained
pending. The earlier control result remains true within that scope, but was insufficient to
establish end-to-end judge operability. A small IO/TermElab reporting smoke control could have
caught this before a candidate existed; absence of all13 proofs did not prevent that control.

Propose a separately frozen judge revision3, retaining mathematical contract revision2. Replace
only each erroneous `liftIO <| IO.println ...` with the direct `IO.println ...` action, using
Lean's ordinary automatic monad lift. Explicit generic `liftM` is a viable alternative; actual
compiler evidence must settle the replacement. The same JSON value/prefix must be emitted.
Preserve all exact types, universes, roster, axiom limits, parser enforcement, source pins,
resources, process containment, fresh project build and kernel-check requirements.

The wrapper currently requires a metadata status of `frozen_before_candidate`. Revision3 must
instead require a distinct truthful status, such as `frozen_after_candidate_before_replay`, and
bind the old freeze and already-existing candidate identities in the amendment record. Update
self-test metadata to the same new status. Do not claim any repaired bytes predate the candidate.
Do not call later repeated judge feedback an independent confirmation or statistical selection
result. The existing deterministic artifact can receive only the newly checked formal predicate.

## Ten routes considered

| Route | Disposition |
|---|---|
| No amendment; retain compiled proofs only | Valid stop, leaves required acceptance incomplete |
| Modify candidate to inject a reporting name or elaborator | Reject; wrong write scope and trust boundary |
| Delete failing output or accept empty output | Reject; loses actual theorem/axiom evidence |
| Direct IO action inside the existing term elaborator | Preferred minimal semantic-preserving repair, subject to execution |
| Explicit generic monad lift from IO to TermElabM | Viable if needed; preserves reporting, requires exact type check |
| Move all emission outside the term elaborator | Viable larger refactor; unnecessary unless the local correction fails |
| Add a reporting helper in JudgeCore | Viable but changes an otherwise tested semantic-core dependency |
| Replace structured emission with pretty-printer parsing | Reject; new parser and weaker identity without need |
| Replace the entire judge with an external checker | Defer; larger trust change than a reporting defect requires |
| Retry unchanged original under optimization | Reject as a repair; known elaboration error is independent of Python assertions |
| Reuse compiled candidate success as formal acceptance | Reject; omits full type/axiom/roster/fresh-kernel gates |

## Required controls and acceptance

Retain all70 prior controls. Add a positive reporting control inside the actual term-elaboration
monad and a causal negative that restores the original command-specific lift. Exercise the
complete revised SemanticJudge on the exact existing candidate, with all13 actual structured
records, complete expanded types and actual allowed axiom sets. Run normal and optimized wrapper
modes and fresh kernel closure. Also run the predeclared cosmetic-semantic variant in both modes;
its transformation must change only allowed comments/spacing. Keep all attempted source bytes,
commands, results and resource observations. A new operational failure remains a failure.

The candidate source is frozen. The amendment must not change a theorem, add an assumption,
weaken a check, raise a budget, or erase either original full failure. Register successor replay
attempts before execution and carry forward the campaign's original resource/deadline boundary.
The root and verifier must independently inspect the final difference and frozen hashes before
successor acceptance. Public status and custody remain open until publication and hosted gates.
