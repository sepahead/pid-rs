# Candidate roster rejection under unchanged judge revision 3

Full slot 3 rejected the unchanged selected candidate at the exact public-namespace roster
predicate. Candidate compilation succeeded. No actual thirteen-record theorem acceptance was
produced and no fresh SemanticJudge kernel replay occurred. This is a candidate interface
rejection under the frozen predicate. It is not evidence that a mathematical target is false.

The selected source remains SHA-256
`76298a9baaad74f831b5254ccdeb5eeda019ac67769df9fabf2a317694fc4a65`.
The frozen judge remains
`45a9309d4a8bb764fcd5ec11fbbd08787bf55da24ea1baf34fada3a22d213586`.
The complete slot-3 receipt is
`frozen-judge-copy/runs/selected-normal-03/receipt.json`, SHA-256
`fc14e33890d2fac9b8a23e51939b1b390573280681b9ff2dfe9dd8c7fd08219d`.
The stdout SHA-256 is
`140118c02ef1669ad28e047d2237a4ac04697749954c9bc2a0a4772e928c2deb`.
The exact failure is `DNF_JUDGE_EXPORT_ROSTER: expected exactly 13 public declarations`.

## Inspected declarations and source relation

A separately registered diagnostic imports the freshly compiled candidate from slot 3. It
verifies the recorded compiler and all compiled import artifact bytes before inspection. The
diagnostic lists twenty namespace declarations: thirteen expected theorems and seven extra
theorems. The complete expanded types and input identities are in
`diagnostics/roster-01/result.json`, SHA-256
`ab1d8cf0900ca1470b8018220511df1e44b7babaa7f9f46dd8c231ec1edf4fc8`.

All names below have prefix `PidSxDnfOrderCandidate.`. Their kind is theorem. Their names are
under that public namespace; this report does not reclassify them as private.

| Extra name | Proposition | Matching source subgoal |
|---|---|---|
| `singleton_event_collision._proof_1_4` | `singletonLeft ≠ singletonRight` | Line 165 |
| `singleton_event_collision._proof_1_5` | Negated order from left to right | Line 167 |
| `singleton_event_collision._proof_1_6` | Negated order from right to left | Line 169 |
| `antichain_premise_is_load_bearing._proof_1_2` | `absorbedFamily` is not an inclusion antichain | Line 210 |
| `antichain_premise_is_load_bearing._proof_1_3` | `absorbedFamily ≠ singletonLeft` | Line 211 |
| `antichain_premise_is_load_bearing._proof_1_4` | Order from absorbed family to singleton family | Line 213 |
| `antichain_premise_is_load_bearing._proof_1_5` | Order from singleton family to absorbed family | Line 215 |

Those seven source subgoals use `decide +kernel`. In the pinned Lean source,
`Lean/Elab/Tactic/Decide.lean:83` selects the kernel branch. Lines 108–118 call `mkAuxLemma`
and add the proof to the environment. The ordinary `decide` branch at lines 90–99 returns the
proof term directly; subsequent kernel checking still checks that term. The matching types,
source sites and tactic implementation support this source relation. No tactic-change control
has been executed here.

A narrow candidate-only replacement of the seven calls with ordinary `decide` is a possible
repair to test under the unchanged judge. It has not been authorized or applied by this
reviewer. It must have a new source snapshot, registration, compile, exact roster observation,
and full semantic/kernel acceptance. Do not relax the namespace roster or allowed axiom set to
make the old candidate pass. Do not describe generated declarations as private without source
and environment evidence.

The frozen complete reporting-regression script binds the old selected candidate identity.
A changed candidate therefore needs an explicitly reviewed direct diagnostic route; it cannot
be described as a pass of that old helper on a different source. The original helper and its
scope must remain intact.

## Accounting and preserved command preparation

Three complete wrapper failures are consumed: the two old reporting failures and this roster
rejection. Five full slots remain under the original cap of eight. Registrations 4–6 have not
run and are suspended pending coordinator adjudication. The original deadline remains
08:32:36 UTC on 2026-09-05. The declaration diagnostic is development compilation 5, after
four prior development compilations; fifty-nine remain under the cap of sixty-four.

The diagnostic's first registered command vector omitted the `-o` flag. Preflight corrected
that vector before any compiler execution. Both the unexecuted registration and its explicit
successor remain in the diagnostic directory. No compiler attempt is hidden by this correction.
The corrected command returned zero and retained all output and input bytes.

The previous allocation of six further successful wrapper runs no longer fits the five
remaining slots. Selected-candidate normal and optimized acceptance plus cosmetic normal and
optimized acceptance can fit in four runs. Any revised role allocation must be explicit. It
must not reset the campaign, erase a failure, or claim a duplicate acceptance pair that did not
run. No proof source, frozen judge source, tracked file, or remote ref changed in this review.
