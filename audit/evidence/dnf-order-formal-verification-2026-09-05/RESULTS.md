# DNF and categorical event order: formal verification record

Thirteen exact Lean statements passed the complete adopted revision-3 judge on 5 September
2026. The selected source and a predeclared comment-only variant each passed in normal and
optimized Python. Each run emitted thirteen actual theorem records and passed
`leanchecker --fresh SemanticJudge`. The [source correspondence](../../formal/lean-sx-dnf-order/SOURCE_CORRESPONDENCE.md)
states the premises of each result. The [exposition](../../formal/lean-sx-dnf-order/EXPOSITION.md)
explains the proof and its limits.

The [accepted source](../../formal/lean-sx-dnf-order/Candidate.lean) has 10,272 bytes and SHA-256
`af925aacc56cf765e875ba8bdce41e62139fc9c8be9317a87e5d63df69cf7af2`.
The [contract](../../formal/lean-sx-dnf-order/Contract.lean) has SHA-256
`569bf11314d02ff599309bfcfa0d80109bf0f121032d5d665e8519513219a5c0`.
The original aggregate Lean project and its historical receipts remain separate.

## Complete campaign outcomes

| Full slot | Source and executor role | Python mode | Actual result | Public projected record |
|---|---|---|---|---|
| 1 | Original source, proof author | Normal | Reporting module failed to elaborate | [Failure 1](runs/full-01-reporting-failure.json) |
| 2 | Original source, coordinator | Normal | Original reporting failure reproduced | [Failure 2](runs/full-02-reporting-failure.json) |
| 3 | Original source, reviewer | Normal | Exact public export roster rejected seven extra theorems | [Failure 3](runs/full-03-roster-failure.json) |
| 4 | Repaired selected source, coordinator | Normal | Thirteen records; fresh kernel pass | [Selected normal](runs/full-04-selected-normal.json) |
| 5 | Repaired selected source, coordinator | Optimized | Thirteen records; fresh kernel pass | [Selected optimized](runs/full-05-selected-optimized.json) |
| 6 | Comment-only variant, reviewer | Normal | Thirteen records; fresh kernel pass | [Cosmetic normal](runs/full-06-cosmetic-normal.json) |
| 7 | Comment-only variant, reviewer | Optimized | Thirteen records; fresh kernel pass | [Cosmetic optimized](runs/full-07-cosmetic-optimized.json) |

The [matrix comparison](required-matrix.json) records the exact source and raw receipt digests.
All four successful semantic stdout streams are byte-identical. Each has SHA-256
`d59a9b8f1c15e8eb7a4689ae09119c406f6b718d15e459c819c6a3e7b0eab334`.
The [retained actual stream](streams/full-04-selected-normal-semantic-judge-stdout.log) contains
the full reported types, theorem names, raw and alias target names, universes, and transitive
axiom sets. `singleton_not_all_patterns` uses only `propext`. The other twelve exports use
`Classical.choice`, `Quot.sound`, and `propext`. These are the only permitted axioms.

Seven of the eight allowed full-wrapper slots were consumed. Six development compilations
were consumed under the limit of sixty-four. The last required full run ended at 07:59:10 UTC,
before the original 08:32:36 UTC deadline. Slot 8 remained unused. The source repair did not
reset the budget. New public routing checks are separate packaging work and receive no credit
as additional executions of this completed campaign.

## Reporting failure and later judge amendment

The original reporting module called `Lean.Elab.Command.liftIO` inside `liftTermElabM` at
thirteen sites. That call produced `CommandElabM Unit` where a term-elaboration result was
required. Twelve sites required `TermElabM Unit`; the final site required a term-result
metavariable. The [first complete diagnostic](streams/full-01-reporting-failure-semantic-judge-stdout.log)
and [coordinator reproduction](streams/full-02-reporting-failure-semantic-judge-stdout.log)
retain the failures. Neither run emitted an accepted theorem record or reached fresh semantic
kernel replay.

The seventy original controls omitted this complete reporting path. Their positive type
fixtures discarded the result. A small reporting smoke control could have found this defect
before candidate work. The controls' original pass status did not imply that the full judge
could report candidate results.

The [revision-3 amendment](../../formal/lean-sx-dnf-order/judge-v3/AMENDMENT.md) replaced only the
thirteen command-specific lifts with direct `IO.println` actions in the semantic module. Its
freeze policy was also changed to state the actual after-candidate chronology. The formal
targets, type and universe comparisons, axiom policy, source rules, exact namespace roster,
parser, source pins, resource limits, and kernel route retained their prior predicates.
The [initial reviewer critique](history/amendment-review-verifier.md) and
[initial coordinator critique](history/amendment-review-coordinator.md) preceded review of
each other's conclusions. The reviewer authored the original judge. This division of roles
does not establish external custody or blinded review.

Revision 3 passed all seventy retained controls, two reporting controls, and three amendment
identity controls in [normal](runs/v3-controls-normal.json) and
[optimized](runs/v3-controls-optimized.json) Python. Each preparation run included fresh kernel
checking of the complete positive control closure. These seventy-five controls remain distinct
from the four complete candidate passes.

## Public roster rejection and source repair

The [original candidate](history/Candidate-before-ordinary-decide-repair.lean) compiled under
revision 3. Its seven `decide +kernel` calls created seven additional public theorem constants.
The judge found twenty declarations where its exact namespace contract required thirteen.
The [diagnostic record](history/roster-diagnostic.json) and
[review](history/roster-rejection.md) preserve the names and full proposition types. This was a
candidate interface rejection. It was not a mathematical counterexample or a new judge defect.

The [registered repair](history/repair-registration.json) changed exactly seven occurrences of
`decide +kernel` to ordinary `decide`. Every other source byte remained unchanged. The
[repair review](history/repair-and-scope-review.md) accepted this narrow change before testing.
In pinned Lean source, ordinary `decide` constructs a proof term; the kernel route remains the
final proof check. The seven generated constants were not reclassified as private, and the
allowed declaration roster was not expanded.

Three failed full runs left five available slots. The earlier plan for six further successful
runs could no longer fit. The [revised scope adoption](history/narrowed-scope-adoption.json)
therefore specified the coordinator's selected normal/optimized pair and the reviewer's
cosmetic normal/optimized pair before the repaired full runs. It removed an additional duplicate
selected pair. The earlier allocation remains in the immutable revision-3 freeze as history;
it is not a claim about the completed execution matrix.

The [cosmetic predeclaration](history/cosmetic-predeclaration.json) specified one comment prefix
before the variant was written. Its [exact source](history/Candidate-cosmetic.lean) has SHA-256
`6ca4bcaf51c3e94db7398c858aaac89d2be72de2ec2ee1b86ae1283db973826a`.

## Separate causal reporting regression

The original frozen reporting helper still binds the old candidate identity. It is not
applicable to the repaired source. A [separate supplemental helper](../../formal/lean-sx-dnf-order/supplemental/reporting-regression-repaired-candidate.py)
changes one candidate-identity expression and no other bytes. Its
[proposal](history/reporting-supplement-proposal.json) and
[adoption](history/reporting-supplement-adoption.json) have separate identities. The helper is
outside the original fifteen-file freeze roster.

After the selected normal pass, the helper used that run's accepted records, compiled imports,
compiler identity, and source bytes. It restored the exact original semantic module, SHA-256
`0c1cf11598048c39e8fee92384362e15e2c9e3555dd93f4befa4c15f865889ab`.
The [regression receipt](runs/reporting-regression.json) and
[complete projected diagnostic](streams/reporting-regression-restored-thirteen-reporting-sites-stdout.log)
record all thirteen original monad mismatches, no accepted record, and complete process-group
cleanup. The separately captured helper execution is in
[the source-capture projection](history/reporting-captured-execution.json). This direct compiler
control was development compilation 6; it was not an eighth full wrapper run.

## Evidence and scientific limits

[MANIFEST.json](MANIFEST.json) binds every proposed public payload file except itself and identifies its
representation. [PROJECTION.md](PROJECTION.md) states which bytes are exact, which are projected,
and which local artifacts are omitted. A raw-local digest beside a projected receipt does not
make that projection a complete original execution archive.

The accepted results concern finite-family logic, finite categorical equality events, and four
explicit failures of stronger claims. Generic source-index types are not restricted to `Fin 3`;
the four boundary witnesses are fixed finite examples. Full-pattern realization is an explicit
sufficient condition for reflection on a restricted domain. The results supply no new PID
functional, numerical estimator, Möbius compression theorem, Rust refinement, statistical
calibration, continuous transfer, or sensor/robotics performance result. No scientific novelty,
external attestation, or additional independent selected-pair execution is claimed.
