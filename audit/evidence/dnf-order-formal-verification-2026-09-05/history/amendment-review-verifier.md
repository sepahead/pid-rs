# Independent initial recommendation: DNF judge reporting amendment

The frozen revision-2 judge cannot complete its reporting command. Preserve that judge and its
adoption record. Prepare a separate revision-3 successor with a narrow reporting correction and
an explicit after-candidate amendment record. No candidate proof or mathematical target should
change to accommodate this failure.

This recommendation was written before reading the coordinator's initial amendment proposal.
It uses the actual frozen source and the two reported complete-run failures. The independent
reviewer authored the original judge; this is a separated first critique, not external custody.

## Evidence and cause

`SemanticJudge.lean` has thirteen `liftIO` calls at lines 57 through 81 inside
`run_cmd liftTermElabM do`. The module opens `Lean Elab Command`. Pinned Lean defines
`Lean.Elab.Command.liftIO` at `Lean/Elab/Command.lean:222` with result `CommandElabM`.
The enclosing block requires `TermElabM`. Both complete runs fail during elaboration at these
thirteen reporting calls. This is an execution defect in the judge, not a theorem counterexample.
No actual thirteen-record semantic acceptance result was produced by those failed commands.

The candidate compiled before either full judge run. Its retained SHA-256 is
`76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
The original freeze SHA-256 is
`e4baedd90547d230e18bcfee1867d54e9697238f44ff306cbbd2529bc34b1d05`.
The candidate-run failure receipt is
`74d9aec375c5dd8919c541ab47c547803b4228dd2e62751ac4066062b9bda676`;
the coordinator's independent original-judge failure receipt is
`f14e29462e063ecc5f1e07a6128ffc6f3df48e1333b5031741505a07ad315d30`.

The seventy preparation controls exercised the core type comparison, aliases, axiom and source
rules, parser, custody, and process controls. Their positive type fixtures discard the result
and use `pure ()`; they did not compile and execute the actual reporting statements. That is a
coverage gap. It must remain in the negative record. A synthetic reporting fixture could have
exercised this monad boundary before the candidate existed, so the gap must not be described
as an unavoidable consequence of having no candidate proof.

## Bounded repair and review routes

1. Retain the original judge unchanged: required for the failure record; it cannot accept the candidate.
2. Replace only the thirteen ambiguous reporting lifts with a suitable explicit generic IO lift:
   preferred, after a small compilation check of the exact pinned Lean API.
3. Move all semantic work to `CommandElabM`: rejected because it changes more than the failed boundary.
4. Replace semantic comparison with printed theorem text: rejected; it weakens target checking.
5. Accept candidate compilation alone: rejected; it omits the independent semantic judge.
6. Change the proof candidate to alter judge name resolution: rejected; the judge must own the repair.
7. Relax stderr, output counts, or parse failures: rejected; it hides the defect.
8. Reuse the old freeze and call the replacement pre-candidate: rejected; the chronology would be false.
9. Add a separate reporting emitter fixture only: useful causal control, insufficient acceptance coverage.
10. Run the actual complete thirteen-export path, its cosmetic variant, and a restored-defect control:
    required with the minimal repair, while preserving the remaining run budget.

Keep `Contract.lean`, `JudgeCore.lean`, `JudgeTargets.lean`, `JudgeAliases.lean`,
`ContractJudge.lean`, the thirteen-export roster, allowed axioms, candidate source rules, strict
record parser, fresh-kernel command, source pins, resource bounds, and cleanup logic unchanged.
Record any necessary successor-version labels and metadata changes separately from semantic
code. The wrapper currently requires status `frozen_before_candidate`; the successor must
require a truthful after-candidate, before-amended-replay state and bind its predecessor and
unchanged candidate identity. Changing only the manifest prose would leave the executable
custody condition inconsistent.

## Required evidence

Retain all seventy existing controls in normal and optimized Python modes. Add a regression
that executes the actual complete reporting module. A copy with all thirteen original `liftIO`
statements restored must fail for the observed `CommandElabM` versus `TermElabM` mismatch,
with unchanged candidate bytes, before any result can be accepted. The repaired complete
candidate must produce exactly thirteen records and pass fresh kernel replay in normal and
optimized modes. A whitespace/comment-only candidate variant, with its own declared byte hash,
must also pass both modes and fresh kernel replay. Neither source policy nor theorem targets
may be weakened for those checks. The resource, malformed-record, wrong-target, and finite
counterexample controls remain separate evidence classes.

The original campaign remains in force: 120-minute deadline 08:32:36 UTC, 64 development
compilations, and eight complete judge runs. Two complete old-judge runs have been consumed.
The amendment must retain that count; it must not reset the campaign or hide an operational
failure. Record which remaining runs exercise positive, cosmetic, and restored-defect cases.
Freeze the actual successor bytes before amended full-candidate replay. State explicitly that
the candidate already existed and had compiled before that successor freeze.
