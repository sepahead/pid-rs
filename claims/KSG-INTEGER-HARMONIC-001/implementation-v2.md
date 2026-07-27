# KSG-only implementation plan and frozen correspondence, revision 2

## Selected source change

`crates/pid-core/src/stats.rs` owns a checked `table[m]=H_(m-1)` Neumaier prefix and a
source-symmetric range helper. Eligible KSG/ISX/PID3 callers use the helper with their distinct
exclusive/inclusive maps. The heuristic path with non-cancelling coefficients remains on general
digamma arithmetic. Runtime report revisions and 15 release-family revisions identify the changed
estimator arithmetic without changing method definitions.

## KSG-only release phase

This revision deliberately excludes the PID2 exact represented-sum constructor and I_min
numerical-boundary work. Four transitive families stop at KSG-only bridge strings; 20 unrelated
families, including the two I_min families, are exact protected controls. PID2 serial/parallel
constants must be captured against the parent PID2 constructor combined only with the KSG source,
not copied from the later combined dirty tree.

## Fixture schema revision 2

The generator canonicalizes only the sufficient structural endpoint cancellation before Decimal
evaluation and records total/exhaustive/stress counts and rule text. Nonendpoint cells retain the
80-digit Decimal prefix route. Generator no-write replay is required because checker/Rust summary
validation alone cannot prove arbitrary non-summary fixture rows were generated.

## Required staged-snapshot validation

Build an index-derived or clean worktree containing only:

- selected KSG source/test/fixture/generator changes;
- revision-3 claim, formal, behavioral, correction, failure, checker, and mutation artifacts;
- KSG-only catalog/release/review/identity/ecosystem bytes;
- exact CI/`just`/operator wiring; and
- no PID2 exact-sum, I_min, categorical frontier, unrelated formal/PDF, or combined identity bytes.

Run the full obligation matrix there. Ambient combined-tree success is not accepted as evidence for
the isolated milestone.
