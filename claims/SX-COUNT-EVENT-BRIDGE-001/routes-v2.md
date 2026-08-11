# Route registry for SX-COUNT-EVENT-BRIDGE-001 revision 2

| Route | Family | Starting point | Strongest current result | State |
|---|---|---|---|---|
| R-EVENT | formal finite-set semantics | existing `SxEventBridge.lean` | exact keyed event unions, target intersections, and positivity of event masses | complete input route |
| R-COUNT | exact combinatorial algebra | arbitrary natural counts with positive total and finite sums | exact event-mass, inclusion-exclusion, positivity, local-log, and averaged count-expression bridge | complete formal route |
| R-CERT | separately implemented executable exact algebra | certifier extractor plus standard-library Python verifier | exact two-source event expressions and inclusion-exclusion on accepted tables | bounded executable corroboration |
| R-RUST | implementation differential | `union_prob_with_cancellation` raw event scan | exhaustive bounded agreement with separately generated fixtures, but no formal refinement | open boundary |
| R-MUT | semantic fault injection | theorem statements, asymmetric source laws, target restrictions, support, evaluator, and scope changes | count/event closure snapshot: ten static mutations plus five baseline-first isolated Lean semantic mutations | complete bounded fault-injection route; current aggregate successor cataloged separately |

`R-EVENT` and `R-COUNT` form one formal route at their shared node map. `R-CERT` and `R-RUST`
remain useful fault-finding implementations but do not independently prove the Lean theorem or one
another. The registry therefore does not count three implementations as three independent proofs.

The 15 R-MUT changes are this route registry's retained count/event closure snapshot. The current
aggregate checker reports 71 registered changes after the categorical-only atom successor; that
successor does not widen R-EVENT or R-COUNT here.

The formal route begins at a supplied exact count function. Bytes/rows/JSON to counts, Rust
histogram extraction, `NODES2`/`invert2`, binary64 and runtime behavior, certificate parsing,
concrete atom inversion, and every stochastic or population theorem remain untraversed edges.
