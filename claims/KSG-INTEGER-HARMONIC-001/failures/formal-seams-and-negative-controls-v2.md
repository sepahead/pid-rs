# Retained formal seams and negative controls for revision 2

## Full analytic digamma truth is not formalized

The tempting stronger statement was “the complete positive-integer digamma theorem is formally
verified.” It is not. The Lean route declares a proposition parameter

```text
PositiveIntegerDigammaPremise psi eulerConstant
```

and the SMT route asserts the four required instances. Both then prove cancellation. Neither
constructs the analytic digamma function, Euler's constant, its base value, or its recurrence.
The older mathematical recurrence/base derivation remains a separate evidence route and source
correspondence. Therefore the permitted wording is “formally checked conditional cancellation,”
not “formally verified digamma.”

## The SMT harmonic function is intentionally uninterpreted

A second tempting overstatement was “both formal systems define and prove the harmonic finite
sum.” Only Lean does. Z3 treats `harmonic : Int -> Real` as arbitrary. This is useful: the
range/index/symmetry results are algebraic and therefore stronger than a harmonic-only instance,
and the encoding does not share Lean's finite-sum machinery. It does not supply a second
finite-sum recurrence proof.

## Cross-tool carrier equivalence remains a reviewed seam

Lean uses `ℕ`, exact `ℚ` finite sums, and a coercion to `ℝ`; SMT uses constrained mathematical
`Int`, exact `Real`, and an uninterpreted function. Each file proves its own domain consequences.
There is no third machine-checked theorem equating the Lean and SMT abstract syntax or proving a
translation validator. The object/sign/index table in `formal-assurance-v2.md` is the retained
human correspondence layer.

## Solver UNSAT is not a kernel-checked proof certificate

Z3 4.16.0 returns exact `unsat` text for each pinned quantifier-free negated obligation, but the
checker does not request or replay an independently verified proof certificate. The Lean kernel
route diversifies this risk for the overlapping algebra. It does not turn the Z3 executable into
a verified kernel.

## Baseline-first Lean mutations

The baseline compiled before mutation. All nine altered theorem sources failed to compile:

| Mutation | Failure meaning |
|---|---|
| `shift_harmonic_denominator` | the universal successor recurrence depends on the exact `i+1` denominator |
| `break_range_maximum` | selecting a non-maximum endpoint breaks the exact range identity |
| `break_range_minimum` | selecting a non-minimum endpoint breaks the exact range identity |
| `break_four_term_coefficient` | the Euler-constant cancellation needs signs `(+1,+1,-1,-1)` |
| `shift_exclusive_argument_twice` | KSG's formula argument is `count+1`, not `count+2` |
| `shift_anchor_inclusive_argument` | an anchor-inclusive count receives no additional successor |
| `make_exclusive_upper_bound_strict` | `count=n-1` legitimately maps to formula argument `n` |
| `corrupt_exclusive_count_formula` | `(nx+1)-1` maps to `nx`, not `nx+1` |
| `corrupt_source_swap_target` | symmetry is equality, not equality up to a constant |

These failures test load-bearing proof content. They are not evidence that the unmutated theorem
matches Rust or a publication.

## Baseline-first SMT mutations

Each unmodified script first passed a satisfiable positive-theorem preflight and an unsatisfiable
negated-theorem check. All eight semantic mutations then returned exact `sat` and were rejected:

| Mutation | Exposed counterexample class |
|---|---|
| `nonzero_cancellation_offset` | exact cancellation cannot tolerate an added constant |
| `misbind_y_digamma_premise` | a premise attached to the wrong argument does not support the displayed term |
| `nonzero_range_offset` | range reassociation is exact, not approximate |
| `replace_min_with_left_argument` | the `x>y` branch requires the true minimum |
| `replace_max_with_left_argument` | the `x<y` branch requires the true maximum |
| `nonzero_exclusive_predecessor_offset` | exact predecessor recovery has no offset |
| `shift_exclusive_x_twice` | a doubled KSG successor violates the declared index map |
| `shift_anchor_inclusive_x` | adding a successor to an inclusive count violates the direct map |

A satisfying mutant is a counterexample to that mutant, not to the baseline theorem.

## Runtime and scientific boundaries retained

The formal objects contain declared counts, not neighbor coordinates or distance comparisons.
Consequently they cannot detect a wrong strict/interior shell, zero radius, nonunique neighbor,
wrong disjunction event, wrong anchor inclusion in runtime code, or a call site that passes another
integer. Tiny compiled witnesses and final source/feature replay remain necessary.

No floating-point operation occurs in either route. They cannot establish the frozen
8,198-cell error signature, correct rounding, prefix compensation, serial/parallel identity, or
overflow behavior.

Finally, exact KSG local arithmetic is measure-independent infrastructure used by inventoried
continuous shared-exclusions paths. It does not formalize the Makkeh--Gutknecht--Wibral
categorical shared-exclusions functional, an Ehrlich estimator consistency theorem, a PID atom,
population support, calibration, or downstream readiness.
