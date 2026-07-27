# Exact-numerics route memo for KSG-INTEGER-HARMONIC-001 revision 1

Route ID: `R-RANGE-HARMONIC`

Claim revision: `KSG-INTEGER-HARMONIC-001` revision 1

Artifact-verification labels: `CHECKED-EXACTLY` for the finite rational identity replay;
`CHECKED-SYMBOLICALLY` for the positive-integer digamma reduction; diagnostic observation for the
uncommitted binary64 replay. This memo does not close the Rust implementation obligation.

## Independent starting point

Start from the positive-integer identity

$$
\psi(m)=H_{m-1}-\gamma
$$

and the admitted KSG count domain, without importing the current `digamma` implementation or its
four-term operation order.

Set

$$
K=k-1,\qquad N=n-1,\qquad
a=\min(n_x,n_y),\qquad b=\max(n_x,n_y).
$$

The caller's count conditions imply $K\leq a\leq b\leq N$. Therefore

$$
\begin{aligned}
\psi(k)+\psi(n)-\psi(n_x+1)-\psi(n_y+1)
 &=H_K+H_N-H_a-H_b\\
 &=(H_N-H_b)-(H_a-H_K).
\end{aligned}
$$

This final range form is an exact-real rearrangement and is source symmetric by construction. For
the inclusive-count shared-exclusions path, the analogous harmonic indices are
`n_alpha - 1` and `n_t - 1`. The project-defined heuristic has coefficient sum two rather than
zero and is outside the claim; its general `digamma` path must remain.

## Retained finite replay results

The committed standard-library Decimal generator replayed successfully:

```text
python3 scripts/generate-ksg-local-arithmetic-oracle.py
OK: 8198 high-precision KSG local arithmetic cases match SHA-256
4cb0c14c0b7ceae7e465ea5c54111ce784597b03eae15fbcebd91dbaaa92b5f4
```

A separately written Python replay and a throwaway optimized, standard-library-only Rust replay
both used one Neumaier-compensated harmonic-prefix table and the displayed range expression. On
the exact committed corpus they independently reported:

| Path | Maximum absolute error against parsed Decimal reference | `nx`/`ny` swap bit asymmetries |
|---|---:|---:|
| reconstructed current digamma arithmetic | 96 binary64 epsilons | 1,570 |
| compensated direct four-term harmonic arithmetic | 16 binary64 epsilons | 764 |
| source-symmetric harmonic range form | 8 binary64 epsilons | 0 |

The range-form worst cell was `n=4096, k=1, nx=2048, ny=2048`. An exact `Fraction` replay of all
6,920 feasible tuples through `n=16` found zero algebra/index failures. The current and range-form
binary64 values differ in 7,138 of 8,198 corpus cells, so the proposed implementation is not
bit-compatible with the released finite-sample algorithm.

The throwaway replay source was not retained and is not a conformance artifact. The final Rust
helper and its committed test must reproduce these observations before E2/E3 can close.

## Proposed bounded executable criterion

For the exact final helper, freeze an absolute corpus ceiling of

```text
32 * f64::EPSILON nats
```

only if final-source replay again observes a maximum no larger than eight epsilons. This is a
four-times empirical margin for 8,198 frozen cases, not a universal error theorem or a
correct-rounding guarantee.

Do not gate by ULP distance from the parsed expected value. The 80-digit Decimal construction has
an approximately `-4e-79` residual in an exact-zero range-endpoint case
`n=4096, k=4095, nx=4094, ny=4095`; the exact range expression correctly produces positive zero.

## Resource and compatibility analysis

- One table of `n + 1` binary64 harmonic prefixes uses the same `8 * (n + 1)` byte shape as the
  existing integer-digamma table.
- Precomputation remains linear in `n`; each prefix step uses one division and compensated
  addition rather than a recurrence/asymptotic/log evaluation.
- Local evaluation adds a `min`/`max` and three subtractions. The estimator remains dominated by
  neighbor work. No performance claim follows without retained benchmarks.
- Neighbor counts, shell semantics, support contracts, public types, and statistical assumptions
  are unchanged.
- Because 7,138 finite outputs change, the KSG and shared-exclusions estimator-revision identities
  cannot remain the v3 values if this route is accepted. Raw/composed release-scope families whose
  output changes also need unambiguous algorithm-revision migration or retained child identities.

## Falsification attempts and merge blockers

- `k=1`, `k=n-1`, sparse and dense endpoints, and exact-zero endpoints;
- swapping `nx` and `ny` at every frozen cell;
- exact off-by-one mutations at `k-1`, `n-1`, and the inclusive shared-exclusions indices;
- retention of the non-cancelling heuristic's `digamma` path;
- unchanged neighbor counts, strict-shell behavior, serial/parallel equality, resource
  acceptance/rejection, and analytic fixtures;
- final-source maximum above the frozen finite ceiling; and
- any documentation that promotes the arithmetic result to support, consistency, calibration, or
  downstream-validity evidence.

## Strongest result and state

The exact algebraic reduction and its integer index map are established for the stated domain. The
finite exploratory implementation substantially improves the frozen arithmetic corpus and makes
source interchange bit symmetric. The route recommends implementation behind a complete
estimator-identity migration, but remains `active`: the final Rust source, mutation/property tests,
feature parity, resource checks, documentation, and release identity have not yet closed.

Critical cut set: the exact call-site index map plus the classification of coefficient-cancelling
paths. A wrong inclusive/exclusive count or accidental migration of the heuristic defeats every
implementation route even if the generic harmonic identity is correct.
