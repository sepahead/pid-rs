# Finite MGW proof: source and execution guide

This candidate packet presents the finite proof, its original controls, and a
later completed replay from fresh project objects. A complete public replay
system, independent publication acceptance and mainline integration remain open.

The [standalone derivation](../../evidence/mgw-fixed-world-added-information-2026-09-09.md)
defines independent fair bits A, B and U, target Y=(A,B), baseline A, and two added
sources C=U and C=B. For the categorical Makkeh–Gutknecht–Wibral shared-exclusions
functional, both choices have synergy ln(4/3), while I(C;Y|A) is respectively zero
and ln(2). This comparison explains why that single signed atom is insufficient
for ranking added Shannon information. It does not establish a sensor's task
utility. The complete signed decomposition and task losses answer other questions.

## Read the sources in order

1. [Contract.lean](PidMgwFixedWorld/Contract.lean) defines the finite probability
   space, both observation maps, counts, event probabilities and functionals.
2. [RawTargets.lean](PidMgwFixedWorld/RawTargets.lean) fixes 21 propositions.
3. [Candidate.lean](PidMgwFixedWorld/Candidate.lean) proves those propositions.
4. [Judge.lean](PidMgwFixedWorld/Judge.lean) checks the named declarations against
   the fixed target expressions and checks their transitive axiom use.

[SOURCE_GRAPH.json](SOURCE_GRAPH.json) gives all nine project modules in compile
order: five existing finite-convergence dependencies followed by these four files.
Each entry binds the source path, bytes and SHA-256 digest. The five dependencies
remain under their existing source contract. No file is added to that frozen
project. The four new files retain their exact historically checked bytes,
including proposal-time comments. Those comments describe their creation state;
the execution map below describes the subsequent observations.

The recorded toolchain is Lean 4.33.0 Release, commit
`d8b18978322de05a8f3dba51ef03cf5461676c17`, with Mathlib revision
`db584cd6d46c92f209a44c0f1c829460d327499d` and the listed package revisions.
Package identities do not authenticate an installed tool or compiled cache.

## What the historical executions show

[HISTORICAL_EXECUTION.json](HISTORICAL_EXECUTION.json) contains 27 native observations
from two closed campaigns. The native stdout and stderr files are exact copies.
The JSON is a projection of local raw records: it omits machine-specific command
paths and retains the original record digests. It is neither an authenticated
execution certificate nor the complete local custody archive.

In the original campaign, calls 1–8 compiled the five dependencies, contract,
targets and candidate from fresh project sources. Call 9 compiled the judge and
produced the [21-target report](evidence/original-09.stdout). Call 10 successfully
rechecked the candidate in a fresh environment using the same Lean kernel
implementation. Its empty output is meaningful only with the successful actual
terminal record. It is not an independent external verifier.

The historical wrapper could load a Python cache. A later source/cache inspection
found identical current code objects. It did not trace past cache selection or
establish complete Python or operating-system provenance. This limitation remains
part of the evidence; the new packet does not remove it.

## What the later replay adds

[LATER_EXECUTION.json](LATER_EXECUTION.json) records ten subsequent native
observations: nine fresh project compilations and a fresh same-kernel check. The
later judge output is an exact copy at [later 9](evidence/later-09.stdout); it is
byte-identical to the original 21-target report. All ten commands returned zero,
with empty stderr, no reported operational failure, and no remaining observed
process-group members. Only the judge emitted stdout. The kernel check took
163.27 seconds. These durations describe this execution, not estimator performance.

The later adapter loads the captured Python helper source with `compile` and
`exec`, bypassing that helper's bytecode cache. It retains the existing runtime
monitor and unchanged report validator. Normal synthetic checks covered 12 entry
prefixes, 16 function/loader cases and 43 validator cases. Optimized Python checked
the intended refusal of native entry, the same 16 function/loader cases and 43
validator cases. These checks did not execute Lean; they are separate from the ten
native observations and from the earlier mathematical mutations.

Full before/after observations matched 139,934 pinned installed files. Per-command
checks also observed source bytes, installed metadata and load-path membership.
One historical CLI search component is absent. The adapter records that absence
and rejects its later appearance. The first materialization failed because it
incorrectly required that component to exist. Its two adapter sources and
[disposition](replay-support/negative/preparation-v1/DISPOSITION.json) remain in a
separate negative directory. No Lean command ran in that failed materialization.

The source graph and mathematical source comments retain their earlier bytes and
creation-state labels. The later record supplies the later status; it does not
retroactively change a closed campaign. The [replay procedure](REPLAY.md) names
the exact executed adapter and the compressed installation profile. That profile
describes one observed macOS ARM64 installation. It does not install the tools,
prove their correspondence with source, or qualify another platform.

Raw compiler stdout/stderr are exact copies. Other later records are labelled
projections: machine paths and full local custody are omitted, while original
record digests are retained. The exact adapter retains older scope wording in
the copied installed-observer messages; the later record concerns only this
fixed-source replay. Neither that wording nor a matching hash supplies authenticity,
an atomic filesystem snapshot, complete Python/OS provenance, or independent review.

## Why the negative controls matter

Every variant changes the final `cmi_different` declaration or a dependency of
that declaration. Start with the positive source graph and overlay only the files
listed under `changed_negative_sources` in the execution map. Never import these
deliberately invalid variants as the positive library.

| Case | Deliberate defect | Observed cause and exact output |
|---|---|---|
| M01 | Prove `True` under the required theorem name | The judge rejects the full type: [original 12](evidence/original-12.stdout). |
| M02 | Introduce a local alias with the target's short name, but value `True` | The fully qualified target remains distinct: [original 14](evidence/original-14.stdout). |
| M03 | Rename the correct theorem | The required declaration is absent: [original 16](evidence/original-16.stdout). |
| M04 | Use a proposition-valued definition instead of a theorem | With the incidental definition linter disabled locally, the candidate compiles and the judge rejects the declaration kind: [suffix 2](evidence/suffix-02.stdout). |
| M05 | Add a `Unit` argument to an otherwise correct proof | The full proposition differs: [suffix 4](evidence/suffix-04.stdout). |
| M06 | Assume the conclusion as a local axiom | Transitive axiom collection finds the extra assumption: [suffix 6](evidence/suffix-06.stdout). |
| M07 | Import the conclusion as an axiom from a helper module | The imported assumption is still detected: [suffix 9](evidence/suffix-09.stdout). |
| M08 | Replace the proof body with `sorry` | The compiler rejects the warning under the fixed warning-as-error policy: [suffix 10](evidence/suffix-10.stdout). |

The first M04 attempt failed earlier than intended: the compiler's proposition
definition linter stopped it before the judge ran. Its source and
[original call 17 diagnostic](evidence/original-17.stdout) remain. Original calls
18–26 were not run. The separate suffix campaign checked M04–M08 with ten new
native calls and no new positive proof or kernel replay. A compiler error from
the wrong cause does not test the intended judge rule.

An expected native refusal has native exit 1 and wrapper exit 0: the wrapper
successfully observed the planned rejection. Original call 17 has both exits 1
because that compiler rejection was unexpected at that stage. The execution map
preserves both numbers. None of these adversarial checks proves all possible
checker defects absent.

## Requirements for a fresh replay

A new replay must use a new, bounded execution registration and empty project
object directory. It must copy and hash all nine exact source files, compile them
in the recorded order, retain the genuine judge output, and then perform a fresh
same-kernel check of `PidMgwFixedWorld.Candidate`. Its import path must use those
fresh project objects and the declared external library roots. Reusing a previous
project object cache does not satisfy this replay contract.

The judge must report all 21 fixed targets with the exact declaration names,
theorem kinds, proposition equality and empty universe parameters. The permitted
axioms are `propext`, `Classical.choice` and `Quot.sound`. Source hashes, report
shape, terminal status, semantic controls and human correspondence review serve
different purposes. No one of them substitutes for the others. The original
closed execution windows and immutable records must not be reopened.

This document supplies the source graph, original observations, later replay and
the exact executed research adapter. It does not admit a complete public runner.
The included control projections retain their narrow scope; full source custody
records and further parser/registry controls remain in the local archive until
their public projection is reviewed.
No estimator calibration, Rust numerical refinement, noisy-copy family theorem,
continuous or hyperbolic PID transfer, scientific priority, or deployment result
is established by this packet.
