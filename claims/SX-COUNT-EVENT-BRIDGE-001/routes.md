# Route registry for SX-COUNT-EVENT-BRIDGE-001 revision 1

> **Historical/superseded revision.** The active route authority is
> [`routes-v2.md`](routes-v2.md). The states below record the abandoned revision-1 plan and must
> not be read as current route status.

| Route | Family | Starting point | Strongest current result | State |
|---|---|---|---|---|
| R-EVENT | formal finite-set semantics | existing `SxEventBridge.lean` | exact keyed event unions, target intersections, and positivity of event masses | complete input route |
| R-COUNT | exact combinatorial algebra | empirical natural counts and Finset cardinal sums | proposed count/mass and inclusion–exclusion bridge | active |
| R-CERT | separately implemented executable exact algebra | certifier extractor plus standard-library Python verifier | exact two-source event expressions and inclusion–exclusion on accepted tables | bounded executable corroboration |
| R-RUST | implementation differential | `union_prob_with_cancellation` raw event scan | exhaustive bounded agreement with independent fixtures, but no formal refinement | open boundary |
| R-MUT | semantic fault injection | asymmetric source laws and target restrictions | proposed six-family mutation suite | proposed |

`R-EVENT` and `R-COUNT` become one formal route at their shared node map. `R-CERT` and `R-RUST`
are useful fault-finding implementations but do not independently prove the Lean theorem or one
another. The route registry therefore does not count three implementations as three proofs.
