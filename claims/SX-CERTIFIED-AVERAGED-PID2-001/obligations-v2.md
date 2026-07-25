# Revision-2 obligations for SX-CERTIFIED-AVERAGED-PID2-001

This file records the revision-2 delta. Revision-1 interval obligations remain in
[obligations.md](obligations.md) and are not retroactively strengthened.

## Obligation graph

```text
revision-1 exact table -> 24 exact log expressions -> interval containment
                                      |
                                      v
                         D1 integer denominator clearing
                                      |
                                      v
                         P1 bounded product preflight
                                      |
                                      v
                         P2 exact rational product R
                                      |
                           +----------+----------+
                           |                     |
                           v                     v
                  P3 compare R with 1    P4 interval/product consistency
                           |
                           v
                  S1 exact zero/strict sign

V1 independent reconstruction + V2 schema/resource/source binding
  -> revision-2 conditional adjudication

F1 complete proof-assistant refinement + H1 independent custody
  -> stronger formal/external assurance (not imported)
```

## Detailed obligations

| ID | Obligation | Status | Retained evidence | Remaining boundary |
|---|---|---|---|---|
| D1 | Prove and check that every emitted empirical coefficient satisfies $na_j\in\mathbb Z$. | Closed analytically; executably checked | Exact-product theorem; producer and independent verifier denominator checks | Implementations/runtime remain trusted |
| P1 | Compute term, exponent, per-expression bit, and aggregate bit evidence before allocating rational powers. | Closed for reviewed source; bounded mutation evidence | `src/product.rs`, verifier planning, resource tests, product mutation suite | No verified cost model, wall-clock bound, or compiled-code refinement |
| P2 | Reconstruct $R=\prod q_j^{na_j}$ exactly for every admitted coordinate. | Closed analytically; exact replay on qualified inputs | Rust `Rational`, independent Python `Fraction`, 11,856 product comparisons | Runtime and common specification faults remain possible |
| P3 | Compare $R$ with one and map the result to exactly one zero/strict-sign decision. | Closed analytically; exact replay | Product theorem, three-way numerator/denominator comparison, live certificates | No universal implementation proof |
| P4 | Reject a compared product whose sign contradicts the dyadic enclosure. | Closed for reviewed logic; mutation challenged | Producer consistency check and verifier recheck | This cross-check cannot prove both routes correct against a shared mistake |
| A1 | Preserve product preflight abstention without inventing a decision or invalidating interval containment. | Closed for reviewed schemas and tests | Two unavailable statuses, null decision/witness checks, resource adversaries | Application consumers can still misuse fields unless they enforce the contract |
| N1 | Retain a nonempty exact-product-one counterexample to empty-term-only zero completeness. | Qualified exact bounded evidence | Counts `[0,0,1,1,1,4,1,0]`, exact five-term identity, boundary exhaustion through total eight | Minimality is only over the stated binary finite domain |
| Q1 | Exhaustively challenge expression products/signs on all binary count tables with total at most four. | Qualified bounded | 494 tables, 11,856 coordinates and exact signs | Larger counts, alphabets, widths, and resource boundaries |
| Q2 | Exhaust the first non-syntactic product-one boundary through binary total eight. | Qualified bounded | 12,869 nonzero tables, 308,856 coordinates, 16 product-one cases at total eight | No universal classification theorem |
| Q3 | Kill named product evidence, source, and structural mutations. | Qualified bounded | 21 product adversaries plus the false-sign boundary mutation | Mutation adequacy is not proof |
| L1 | Kernel-check generic log/product/sign algebra and the retained witness product. | Closed for six generic theorems plus one exact five-factor rational identity | Pinned Lean 4.32 project and checker, permitted axioms recorded | Exact-rational and Rust routes bind the factors to SxPID; no Lean event/lattice/executable refinement |
| V1 | Independently reconstruct product plans, products, decisions, and evidence from untrusted report fields. | Closed for reviewed source; bounded replay | Revision-2 verifier and exact-product qualification | Python/verifier correctness remains trusted |
| V2 | Bind revision-2 schemas, resource policy, permitted claim, source manifest, and verifier semantics. | Closed locally for accepted reports | Exact identifiers, source-manifest member checks, semantic/source digests | No external immutable packet/custody record yet |
| Z2 | Re-adjudicate revision 2 without silently broadening revision 1. | Conditionally supported | [claim-v2.md](claim-v2.md), [decision-v2.md](decision-v2.md), revision checker | Formal refinement, external custody, statistics, and application claims remain open |
| F1 | Prove accepted bytes through event extraction, exact expressions, product preflight/comparison, interval enclosure, and acceptance. | Open | Generic algebra only | Requires a complete refinement proof or proof-producing checker |
| H1 | Obtain independent-human source acquisition, execution, review, and retained custody. | External/open | None | Requires another actor and durable external record |

## Acceptance invariant

An accepted revision-2 report must preserve both implications:

1. every coordinate has an independently contained dyadic value enclosure; and
2. only an independently validated `compared` product record supplies an exact zero/strict-sign
   decision.

Neither implication may be substituted for the other.
