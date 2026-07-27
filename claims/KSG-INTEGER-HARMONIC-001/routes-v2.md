# Route registry for `KSG-INTEGER-HARMONIC-001` revision 2

| Route | Family | Independent starting point | Strongest result | Shared dependency | State |
|---|---|---|---|---|---|
| R-MATH | symbolic/special-function | positive-integer digamma recurrence | exact harmonic and symmetric-range identities | runtime coefficient/index map | complete for the exact theorem |
| R-RATIONAL | exact finite algebra | `Fraction` harmonic numbers | 6,920 feasible tuples through `n=16` and boundary values agree exactly | declared tuple domain | complete for its finite domain |
| R-DECIMAL | high-precision computation | standard-library Decimal prefix sums | committed 8,198 reference strings and generator replay | harmonic identity and generator custody | complete on frozen bytes; G1 open |
| R-PLAIN-FOUR | binary64 diagnostic | shared Neumaier prefix, uncompensated left association | `16` eps maximum, `764` swap asymmetries, `8` maximum ties | same prefix and fixture as selected route | rejected alternative; corrected label |
| R-NEUMAIER-FOUR | binary64 diagnostic | shared prefix, Neumaier reduction of four signed values | `8` eps maximum, `0` swap asymmetries, `39` maximum ties | same prefix and fixture as selected route | diagnostic alternative, not selected |
| R-SYMMETRIC-RANGE | binary64 implementation | shared prefix, sorted nonnegative range differences | `8` eps maximum, `0` swap asymmetries, `40` maximum ties | same prefix and fixture | selected; final compiled replay open |
| R-BIT-TRANSITION | compiled integration failure | unchanged frozen-reference tests | exact old/new arrays; four failures; 12 of 13 constants differ | dirty combined KSG/PID2 tree | counterexample to revision-1 E4 closure |
| R-KSG-TINY | exact count geometry plus rational arithmetic | eight explicit 1-D rows, `k=2` | row 5 has `(eps,nx,ny)=(79,4,1)` and exact term `107/210` | public KSG count implementation for replay | analytically checked; compiled replay open |
| R-ISX-TINY | exact disjunction-distance reduction | same rows with a dominating second-source distance | row 5 inclusive counts `(5,2)` and exact local term `107/210` | private local diagnostic/public propagation for replay | analytically checked; compiled replay open |
| R-LEAN-FORMAL | proof assistant / exact finite sum | rational `Finset` definition plus typed digamma premise | 14 kernel-checked recurrence, conditional cancellation, min/max, symmetry, and exclusive/inclusive index theorems | analytic digamma premise and human object map | complete for scoped formal obligations |
| R-Z3-FORMAL | independent SMT encoding | constrained `Int`, exact `Real`, and arbitrary harmonic values | three satisfiable preflights and three UNSAT negated cancellation/range/index obligations | analytic digamma instances and human object map | complete for scoped formal obligations |
| R-ADVERSARY | mutation/provenance | comment, string, live shadow, overwritten output, generator drift, stale oracle | identifies the boundary between textual and compiled evidence | checker implementation | old mutations closed; new named faults open |

## Independence accounting

The three binary64 association routes are not independent: they share the same prefix table,
fixture, tuple order, parsed Decimal values, and floating environment. Their differing signatures
are useful discriminators, not three confirmations of the estimator.

The exact `107/210` tiny KSG/ISX local target is independent of the large Decimal fixture, but its
event/count correspondence still depends on the hand-audited Chebyshev geometry. A compiled replay
checks implementation conformance; it does not turn that finite fixture into a population theorem.

The Lean and SMT routes share no generated fixture, Rust source, or proof code. Lean defines
universal rational harmonic sums and checks proof terms in a kernel; SMT uses an independently
written quantifier-free formula whose range/index result holds for arbitrary harmonic values.
They remain correlated at the positive-integer digamma premise, the human sign/index object map,
and their common author. They diversify exact-consequence checking; they are not two independent
proofs of analytic digamma truth or estimator validity.

The frozen-reference transition is a regression detector, not numerical ground truth. PID2 atom
bits depend on both the KSG input revision and represented-input exact synergy summation, so that
row has a two-claim cut.
