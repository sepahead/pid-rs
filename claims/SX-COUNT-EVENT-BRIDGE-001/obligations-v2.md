# Obligations for SX-COUNT-EVENT-BRIDGE-001 revision 2

Revision 2 supersedes revision 1's full-support prose with arbitrary natural counts, positive
total, and a strictly positive-support logarithm domain. The revision-1 files remain retained.

## Obligation graph

```text
Q0 count-quantifier correction ------+
S1 fixed two-source node semantics --+
E1 keyed Sx event semantics ---------+
C1 exact counts/total/support -------+--> M1 exact empirical event masses
                                             |
               +-----------------------------+----------------------------+
               v                             v                            v
       M2 redundancy IE          M3 restricted redundancy IE      M4 joint keyed count
               +-----------------------------+----------------------------+
                                             v
                                  P1 supported ratio positivity
                                             v
                                  L1 local net count identity
                                             v
                                  A1 averaged count expression

K1 kernel/inventory + K2 mutations + D1 scope/catalog
  --> bounded formal-semantics decision
```

## Table

| ID | Obligation | State | Closure |
|---|---|---|---|
| Q0 | Correct revision-1 full-support prose without rewriting retained history. | closed | `claim-v2.md` plus retained failure note |
| S1 | Define exactly the source-one, source-two, joint-source, and redundancy collections over `Fin 2`. | closed | `SxPid2Node`, `sxPid2Collections`, exact semantic witness |
| C1 | Define total count, positive support, event count, and empirical law with positive total. | closed | exact definitions plus nonnegativity and normalization theorems |
| M1 | Prove event mass is the exact event-count/total-count ratio. | closed | `event_mass_empirical_law_eq_count_ratio` |
| M2 | Prove redundancy source-union inclusion-exclusion. | closed | exact union, intersection, and count theorems |
| M3 | Prove target-restricted redundancy inclusion-exclusion. | closed | exact restricted union, intersection, and count theorems |
| M4 | Prove the joint-source target-restricted event count is the anchor count. | closed | singleton and keyed-count theorems |
| P1 | Derive positivity of every supported count argument and denominator. | closed | anchor-membership count and empirical-mass positivity chain |
| L1 | Prove the probability local signed-net ratio equals the exact rational count ratio. | closed | checked logarithm and rational-cast bridge |
| A1 | Prove the main averaged cumulative expression for all four nodes. | closed | `sxpid2_averaged_cumulative_net_count_expression` |
| K1 | Extend source inventory, imports, declaration counts, `collectAxioms`, and paper-facing semantic examples. | closed | 263 declarations, 201 named theorem audits, SHA-256-bound bridge, and digest-bound semantic contract |
| K2 | Reject same-name theorem weakening, union/intersection, target erasure, source swap, marginal-for-joint, positivity, evaluator, and scope mutations. | closed | ten static and five isolated baseline-first mutation kills |
| D1 | Update method catalog/generated view, assurance registry, public formal maps, limitations, changelog, and rendered artifacts without broadening claims. | closed | bounded catalog/public-document binding, four deterministic PDF artifacts, and review-evidence regeneration |

## Residual cut sets after formal closure

- bytes, rows, or JSON to the exact count function;
- Rust categorical sorting and histogram extraction to the count function;
- concrete `NODES2`, `invert2`, atom order, and result-field refinement;
- informative/misinformative binary64 logs and subtraction;
- canonical exact-expression normalization and bounded rational-product comparison;
- standalone-certifier, MPFR, Python, runtime, compiler, parser, overflow, and resource semantics;
- concrete Möbius atoms and more than two sources; and
- sampling, concentration, population, calibration, priority, release, and consumer claims.

These nodes remain open even though every revision-2 obligation is closed. They are exclusions from
the completed bounded claim, not silently discharged refinement edges.
