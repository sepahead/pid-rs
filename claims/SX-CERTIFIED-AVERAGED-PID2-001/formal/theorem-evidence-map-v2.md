# Revision-2 theorem/evidence map for SX-CERTIFIED-AVERAGED-PID2-001

## Exact-product statements

| ID | Statement | Analytic basis | Machine evidence | Formal boundary |
|---|---|---|---|---|
| P1 | Count-weighted averaged cumulatives and integer-Möbius atoms have coefficients with integer $n$-clearing. | Empirical weights $c_z/n$ and integer lattice coefficients | Producer/verifier integer-denominator checks | Concrete derivation not kernel checked |
| P2 | For cleared expression $F$, $F=(1/n)\log\prod_jq_j^{na_j}$. | Finite log product and integer-power identities | Independent exact product reconstruction | Generic identity Lean checked; concrete expression bridge open |
| P3 | $R=1$, $R>1$, and $R<1$ are equivalent to $F=0$, $F>0$, and $F<0$. | $n>0$ and strict monotonicity of `log` | Exact rational three-way comparison | Generic layer Lean checked |
| P4 | Empty term map implies product one, but the converse fails. | Empty product; explicit five-term product-one identity | Total-eight boundary exhaustion | Counterexample exact; universal classification not claimed |
| P5 | Conservative product projection is computed without powering. | Integer bit-length upper estimate | Reviewed Rust/Python planners, resource tests, and two zero-power-call sentinel controls | No formal cost semantics/refinement |
| P6 | Product preflight abstention supplies no sign result. | Typed case distinction | Schema and verifier checks | Consumer correctness remains external |
| P7 | Compared product and dyadic interval are mutually consistent. | Sign/enclosure necessary conditions | Producer/verifier checks and mutations | Does not prove either route independently correct |
| P8 | Revision-2 verifier acceptance implies exact product decision for every `compared` coordinate. | P1--P7 plus strict reconstruction/schema/source checks | Bounded live/exhaustive/mutation replay | Conditional theorem; no end-to-end proof |

## Lean boundary

The pinned Lean project checks six generic algebra theorems about finite products, logarithms,
positive scaling, and sign/zero transfer, plus the exact five-factor rational product identity of
the retained total-eight witness. The exact-rational and Rust routes separately bind those five
factors to the SxPID coordinate. Its permitted axioms are `propext`, `Classical.choice`, and
`Quot.sound`. It does **not** encode:

- JSON parsing or canonical count-table bytes;
- Makkeh--Gutknecht--Wibral source-event unions and target restriction;
- exact count extraction or canonical log-term normalization;
- the concrete two-source Möbius lattice;
- resource preflight or big-integer execution;
- the Python or Rust verifier; or
- statistical or downstream validity.

Therefore the permitted statement is:

> Lean kernel-checks the generic log/product/sign algebra used by the exact-product argument and
> the retained five-factor rational identity; exact-rational and Rust routes separately bind that
> identity to the SxPID coordinate.

The statement “Lean formally verifies the SxPID2 certifier” is false.

## Open bridges

1. Formalize accepted byte semantics and strict schema rejection.
2. Formalize the keyed SxPID event map and its paper-to-specification correspondence.
3. Prove extraction of all 24 canonical exact expressions and the concrete lattice transform.
4. Prove the preflight projection and executable product comparison refine the exact specification.
5. Connect the revision-2 independent verifier to these definitions through a checked runtime or
   proof-producing certificate.
6. Independently replay and retain the complete packet under separate custody.
