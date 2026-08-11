# Rejected native-decision row-sum prototype

Date: 10 August 2026

Disposition: **rejected and removed; zero proof credit**.

## What failed

An intermediate proof of `sx_pid2_mobius_row_sum` used
`cases atom <;> native_decide`. The theorem statement was true and the module compiled, but exact
`#print axioms` inspection exposed four generated
`sx_pid2_mobius_row_sum.native_decide.ax_1_*` assumptions. That exceeded the repository's permitted
axiom basis and contradicted the existing finite-convergence checker rule that forbids
`native_decide` in the formal source surface.

## Correction

The proof now uses `cases atom <;> decide`, so the finite cases are discharged by the kernel rather
than by a native-evaluator axiom. Exact Lean 4.32.0 replay and the complete theorem inventory show
that every theorem in the final module has either no axioms or only a subset of `propext`,
`Classical.choice`, and `Quot.sound`.

The semantic-variation suite also includes an explicit regression route that reintroduces
`native_decide` and requires the checker to reject it. This note does not award the rejected
prototype any formal-assurance credit.
