# Formal assurance for `KSG-INTEGER-HARMONIC-001` revision 3

## Lean route

The pinned Lean package proves 14 narrow exact theorems covering finite harmonic sums, recurrence,
the four-term/range identity, source symmetry, exact-real bounds, and exclusive/inclusive index
consequences. The integer-digamma theorem is a typed premise. The route contains no Rust semantics,
floating-point model, neighbor geometry, support model, estimator, PID lattice, or MGW functional.

The Lean mutation suite must reject nine named changes to the denominator, min/max ranges, signs,
successor/identity maps, and bounds. Mutation kills establish load-bearing use of those statements;
they do not prove the analytic premise.

## Z3 route

The pinned Z3 package checks three QF_UFLIRA obligations by showing the positive formulation
satisfiable and its negation unsatisfiable under explicit premises. Harmonic values are supplied by
an uninterpreted function. The route proves linear/range consequences of premises, not harmonic
analysis. The mutation suite must reject eight named premise/conclusion changes.

Z3 output is a solver result, not a proof certificate checked by a smaller independent kernel.

## Shared-cut accounting

Lean and Z3 share:

- the analytic positive-integer digamma premise;
- the human `(+1,+1,-1,-1)` sign transcription;
- the exclusive successor and inclusive identity correspondence; and
- the chosen theorem/domain statements.

They are different execution engines, but agreement cannot close a defect in a shared premise or
mapping. Exact `Fraction`, behavioral W1/W2, source checks, and compiled corpus tests attack other
parts of the chain without proving the analytic premise from first principles.

## Formal non-claims

Revision 3 does not call this end-to-end formal verification. It does not prove Rust refinement,
binary64 error, generator correctness, neighbor search, estimator consistency, shared-exclusions
validity, PID atoms, or application conclusions.
