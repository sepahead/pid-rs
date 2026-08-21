# Route registry for SX-CERTIFIED-AVERAGED-PID3-001, revision 1

## Independence rule

There are five required closure programs. A program can contain more than one subroute, and some
programs deliberately require two implementations. Program count is not evidence count: routes
sharing the same event code, generated matrix, rational oracle, proof axiom, or certificate bytes
remain correlated at that dependency.

All five programs are currently open. The external audit is retained as adversarial intake, not
promoted to a sixth accepted route.

## Program A: primary-source and exact combinatorial semantics

| Field | Value |
|---|---|
| Route ID | `P3-A-SEMANTIC-COMBINATORIAL` |
| Family | Primary-source mapping, finite set/count semantics, incidence algebra |
| Independent starting point | Pinned Makkeh--Gutknecht--Wibral source plus a source-blind derivation from the frozen formulas |
| Current obligations | S1, D2, L1, L2, A1, A2, B1 |
| Strongest current result | The packet gives an explicit DNF event, 18-node carrier, order, zeta orientation, Möbius rows, exact products, and small exact falsifiers |
| Exact evidence | Hand-checkable integer/rational witnesses in [failures/](failures/) |
| Counterexamples attempted | OR/AND swap, within-mask OR, missing target intersection, mask-order swap, uniform support weighting, negative-net clamping |
| Critical cuts | C-MGW, C-EVENT, C-LATTICE |
| State | Active/open |
| Reopen/close condition | Independent source record plus a general count derivation and independently generated complete 18-node incidence certificate |

Required deliverables:

1. A source application map naming the exact paper equations and local objects.
2. A source-blind proof that the event-count formulas implement the frozen union of conjunctions
   and target intersection.
3. An antichain-completeness derivation from the seven nonempty masks.
4. Exact order, zeta, inverse, self-redundancy, full-joint reconstruction, and all six
   source-permutation checks.
5. One retained minimal witness for every semantic mutation class.

This route cannot close executable parsing, intervals, or Rust refinement.

## Program B: dual formal semantics

| Field | Value |
|---|---|
| Route ID | `P3-B-DUAL-FORMAL` |
| Family | Kernel-checked theorem proving plus independently encoded SMT finite verification |
| Independent starting point | The frozen mathematical packet, not a generated producer table |
| Current obligations | F1, F2, with formal support for D2, L1, L2, A1, A2, N1 |
| Strongest current result | Existing repository Lean work covers generic finite events and a two-source count bridge only; existing Z3 work does not bind the concrete three-source event carrier end to end |
| Counterexamples attempted | Wrong order direction, transposed zeta, missing antichain, padded zero mask, OR/AND mutations, wrong target restriction, altered Möbius row |
| Critical cuts | C-MGW remains an external premise; C-EVENT and C-LATTICE must be independently encoded |
| State | Open |
| Reopen/close condition | Both B-L and B-S close their stated scopes and a theorem map exposes every unformalized bridge |

### B-L: Lean concrete route

The Lean route must define rather than assume:

- nonzero source masks over `Fin 3`;
- the subset and antichain predicates;
- the exact 18-element carrier and its completeness;
- the declared redundancy order;
- event membership for arbitrary finite categorical row types;
- natural count masses $U,V,T,N$ and their positivity on supported keys;
- zeta construction and the concrete Möbius inverse;
- cumulative and atom count-cleared products;
- informative, misinformative, and net reconstruction; and
- exact product-one/strict-sign implications.

The checker must pin Lean, Mathlib, lake manifest, theorem inventory, and axiom inventory; reject
`sorry`, undeclared axioms, theorem replacement, and proof-escape mutations; and report what remains
a typed premise. A theorem about an abstract supplied $18\times18$ matrix does not close the
carrier/order bridge.

### B-S: SMT route

The SMT route must be written independently of the Lean carrier and generated matrices. It must:

- enumerate subsets and antichains from Boolean mask constraints;
- prove exactly 18 canonical nodes with no duplicates;
- encode the order definition directly;
- derive all 324 zeta entries from that order;
- verify both integer inverse products;
- prove the six source permutations are order automorphisms; and
- discharge the finite event-mutation witnesses from raw cell predicates.

Replay is required under pinned Z3 and at least one second solver on a solver-neutral finite
encoding. `sat` for a wanted theorem is not success: theorem obligations use unsatisfiability of
their negations, and each mutation must become satisfiable with a retained model or otherwise fail
the checker. SMT does not close real-log interval or compiled-Rust obligations.

Lean and SMT diversify proof kernels and encodings. They still share the paper-to-formula premise,
so Program A remains required.

## Program C: exact products and independent directed magnitude

| Field | Value |
|---|---|
| Route ID | `P3-C-CERTIFIED-NUMERICS` |
| Family | Exact integer/rational arithmetic, directed transcendental enclosure, resource proofs |
| Independent starting point | Producer exact expressions versus verifier reconstruction from canonical input |
| Current obligations | N1, N2, R1, X1, X2 |
| Strongest current result | The algebraic reduction $F=(1/N)\ln R$ is explicit; two-source infrastructure is only a design reference and is not inherited evidence |
| Counterexamples attempted | Nonempty product one, exact-zero binary64 residual, interval overlap without containment, endpoint touch, factor/exponent mutation, preflight-after-power |
| Critical cuts | C-DECODE, C-EVENT, C-LATTICE, C-PRODUCT, C-LOG |
| State | Open |
| Reopen/close condition | Bound producer and dependency-disjoint verifier agree on exact products while independent directed intervals satisfy subset containment for every coordinate |

The producer route may use exact integer products and directed MPFR/Arb. The verifier route must
reconstruct event counts, expressions, product plans, and the rational-series interval without
importing producer code, generated expressions, matrices, or intervals.

Mandatory controls include:

1. no big power before per-coordinate and aggregate preflight;
2. exact numerator/denominator comparison for all zero/strict-sign decisions;
3. independent interval subset containment, not overlap;
4. precision-schedule exhaustion as rejection;
5. exact product/interval consistency;
6. nonsyntactic product-one and negative-net witnesses;
7. huge-count and projected-bit refusal; and
8. source, schema, registry, policy, input, expression, report, and verifier mutations.

This program establishes neither Rust parity nor population calibration.

## Program D: compiled Rust keyed refinement

| Field | Value |
|---|---|
| Route ID | `P3-D-RUST-REFINEMENT` |
| Family | Specification-to-source-to-binary refinement and bounded differential execution |
| Independent starting point | Current specialized and general Rust categorical APIs, compared to the frozen exact specification by semantic key |
| Current obligations | X3, Q1, Q2, applicable Q3 and P1 |
| Strongest current result | Source inspection finds the intended OR-of-AND event and target check, but neither exact product certificates nor a compiled refinement theorem exists |
| Counterexamples attempted | Specialized/certificate `(3)`--`(4)` positional swap, generic-order positional comparison, exact-zero residual, source permutations, relabelings, count replication |
| Critical cuts | C-EXEC plus the exact verifier's C-EVENT and C-LATTICE reference |
| State | Open |
| Reopen/close condition | Bound compiled paths replay exact event counts and all 108 keyed coordinates with complete bounded and mutation receipts |

Mandatory execution matrix:

- specialized averaged three-source API;
- specialized pointwise-enabled API, comparing its averaged projection only;
- general $n=3$ averaged and pointwise-enabled APIs;
- serial and every feature path that can change categorical execution;
- debug and release builds;
- Linux, macOS, and Windows if the release claim names all three; and
- the exact certificate producer invoked on the same canonical count table.

The bounded binary replay is exactly 20,348 count vectors and 2,197,584 averaged coordinate
verdicts. Results are keyed by canonical mask set. It must additionally check six source
permutations, binary value relabelings, replication invariance, constant and deterministic cases,
XOR/copy/unique gates, all retained failures, cancellation, and resource refusal.

A floating tolerance comparison can remain useful differential evidence, but cannot replace exact
product equality, directed enclosure, or key correspondence.

## Program E: adversarial replay, provenance, and adjudication

| Field | Value |
|---|---|
| Route ID | `P3-E-ADVERSARIAL-REPLAY` |
| Family | Dependency audit, mutation adequacy, immutable evidence, fresh replay, final integration |
| Independent starting point | Fresh extraction of settled source plus the frozen claim packet, without producer-author summaries |
| Current obligations | Q3, P1, H1, J1 |
| Strongest current result | External scripts expose useful bounded results and independence failures; no settled implementation or external custody exists |
| Counterexamples attempted | Shared imported event code disguised as independence, stale digest, self-consistent reseal, optimized-Python `assert` removal, partial-output acceptance |
| Critical cuts | Every shared cut, especially C-EVIDENCE and C-EXEC |
| State | Open |
| Reopen/close condition | Fresh replay verifies all hashes and commands, mutation receipts are complete, dependency overlaps are recorded, and an independent reviewer adjudicates every obligation |

The final auditor must:

1. reconstruct the target from `claim-v1.md` and `conventions.md`;
2. inspect actual formal declarations, source, binaries, schemas, and reports;
3. verify every bounded cardinality and coordinate count mechanically;
4. run normal and optimized checker modes where language assertions can disappear;
5. verify mutations fail for the intended reason;
6. compare first-result records with regenerated results;
7. preserve every negative result and open boundary;
8. trace contradictions to the smallest obligation rather than majority-vote them away; and
9. authorize only the wording in the final decision.

External human custody is required before any claim of independently reproduced public assurance.
Local model reviews can strengthen attacks but cannot satisfy H1.

## External audit intake route: retained but not independent

| Field | Value |
|---|---|
| Route ID | `INTAKE-WIBRAL-FINAL-SXPID3` |
| Family | Python exact enumeration and floating differential |
| Strongest reported result | 20,348 binary count vectors through total five; 54 atom/component values per table; a 968-table second-path differential through total three |
| Useful evidence | First exact-zero residual, bounded exact reconstruction checks, direct-versus-recursive floating disagreement |
| Shared dependencies | The second script imports primary cell, weak-composition, event, antichain, Möbius, compute, and sign functions |
| Correction | Treat as one correlated bounded route with partial independent subchecks, not two end-to-end implementations |
| State | Diagnostic only |
| Reopen condition | Rewrite the second route without imports or generated artifacts from the primary and bind both executions immutably |

The intake's reported 1,098,792 values are $20{,}348\times54$, not the 108-coordinate certificate
scope. The 20,348 objects are count vectors; only 20,164 are primitive rational laws. These scope
corrections do not invalidate the bounded 54-coordinate arithmetic observations, but they prevent
their promotion to this claim.

## Five-program acceptance rule

The target remains proposed until Programs A--E all close. Program B requires both B-L and B-S;
Program C requires both producer and independent interval/product reconstruction. No program may be
waived because another program passes:

- formal lattice algebra does not prove event transcription;
- exact products do not prove logarithm enclosure;
- bounded enumeration does not prove arbitrary-alphabet parser/verifier refinement;
- compiled Rust parity does not prove the paper correspondence; and
- immutable hashes do not prove scientific correctness.
