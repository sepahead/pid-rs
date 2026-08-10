# Obligations for SX-COUNT-EVENT-BRIDGE-001 revision 1

> **Historical/superseded revision.** These open states describe the abandoned revision-1 target,
> not current work. Revision 2 closes the corrected supplied-count scope in
> [`obligations-v2.md`](obligations-v2.md).

## Obligation graph

```text
S1 fixed two-source node semantics ----+
E1 keyed Sx event semantics (existing)+
C1 exact counts/total/support ---------+--> M1 exact empirical event masses
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

The minimal shared cut is the binding between the four fixed nodes and the keyed event map. Both
the raw-event and inclusion–exclusion routes depend on it. An asymmetric exact example and
source-swap fault injection were required to exercise that cut directly.

## Table

| ID | Obligation | State | Required closure |
|---|---|---|---|
| S1 | Define exactly the source-one, source-two, joint-source, and redundancy collections over `Fin 2`. | open | explicit definitions and asymmetric examples |
| C1 | Define total count, positive support, event count, and empirical law with a proved positive denominator. | open | Lean definitions and basic normalization lemmas |
| M1 | Prove event mass is the coerced rational count ratio. | open | kernel-checked finite-sum theorem |
| M2 | Prove redundancy source-union inclusion–exclusion. | open | exact Finset identity |
| M3 | Prove the target-restricted redundancy identity. | open | exact Finset identity |
| M4 | Prove the joint-source target-restricted event count is the anchor count. | open | keyed-event extensional theorem |
| P1 | Derive positivity of every supported count argument and denominator. | open | no positivity axioms |
| L1 | Prove the probability local signed-net ratio equals the exact rational count ratio. | open | algebraic/log-domain bridge |
| A1 | Prove the main averaged cumulative expression for all four nodes. | open | theorem with concrete event/count definitions |
| K1 | Extend source inventory, imports, declaration counts, `collectAxioms`, and paper-facing semantic examples. | open | strict checker replay |
| K2 | Reject union/intersection, target-erasure, source-swap, marginal-for-joint, positivity, and scope mutations. | open | named self-test kills |
| D1 | Update formal map, method catalog/generated view, limitations, and changelog without broadening claims. | open | coherence checks |

## Residual cut sets after completion

- bytes/JSON to exact count function;
- Rust categorical row sorting and histogram extraction to the count function;
- concrete `NODES2` and `invert2` source refinement;
- informative/misinformative binary64 logs and subtraction;
- canonical exact-expression normalization and bounded rational-product comparison;
- MPFR/Python/runtime/compiler semantics; and
- sampling, population, calibration, consumer, and release claims.

These nodes remain open even if every revision-1 theorem passes.
