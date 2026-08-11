# Claim SX-COUNT-ATOM-BRIDGE-001, revision 1

> **Historical superseded revision.** Revision 1 records the pre-integration candidate and hold.
> It is retained for provenance only. The active bounded claim is [`claim-v2.md`](claim-v2.md).

## Preliminary status

State: **preliminary candidate; not yet accepted as repository assurance**.

The candidate Lean source is
[`TwoSourceMobiusAtomBridge.lean`](../../audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean).
It extends the completed, supplied-count
[`SX-COUNT-EVENT-BRIDGE-001`](../SX-COUNT-EVENT-BRIDGE-001/claim-v2.md) boundary from four
signed-net cumulative quantities to a fixed surface of 24 averaged quantities:

```text
3 components * (4 cumulatives + 4 Mobius atoms) = 24 coordinates.
```

The components are informative, misinformative, and signed net. The cumulative nodes are source
one, source two, joint sources, and redundancy. The atoms are unique one, unique two, synergy, and
redundancy. This revision remains preliminary until the candidate source is bound to a pinned Lean
kernel checker, negative semantic variations, the rendered report, repository-wide scope records,
and independent review. Source text by itself is not completion evidence.

## Publication and project boundary

Makkeh, Gutknecht, and Wibral define the finite categorical pointwise shared-exclusions
construction, its informative/misinformative split, its signed-net quantity, and the passage from
cumulative quantities to partial-information atoms by Möbius inversion in
[“Introducing a Differentiable Measure of Pointwise Shared Information”](https://doi.org/10.1103/PhysRevE.103.032149)
(2021). The parthood and logical event organization is developed further by Gutknecht, Wibral, and
Makkeh in
[“Bits and Pieces”](https://doi.org/10.1098/rspa.2021.0110) (2021).

Those categorical quantities and transforms are **paper-defined**. This repository's choices of
Lean types, exact source and atom orders, a 24-coordinate enumeration, supplied-count interfaces,
exact rational product representatives, theorem factoring, and replay gates are a
**project-defined formalization and assurance composition**. They define no new PID measure and
make no scientific-novelty claim. The correspondence from the publication formulas to the chosen
Lean definitions is a reviewed transcription boundary; it is not derived inside Lean from the
paper text.

## Exact candidate target

Let `count` be an arbitrary natural-valued function on the complete finite two-source/target key
space, and assume `0 < totalCount count`. Zero-count complete keys are permitted. Local logarithms
and empirical averaging are restricted to `positiveSupport count`.

For each supported anchor, component, and cumulative node, the candidate defines exact rational
arguments

```text
informative:     total_count / source_event_count
misinformative: target_event_count / target_restricted_event_count
net:             informative / misinformative
```

and proves that the corresponding probability-domain local cumulative at the exact empirical law
is the natural logarithm of that argument. The concrete two-source Möbius transform is

```text
R  = C_R
U1 = C_1  - C_R
U2 = C_2  - C_R
S  = C_12 - C_1 - C_2 + C_R.
```

The inverse zeta transform reconstructs

```text
C_R  = R
C_1  = U1 + R
C_2  = U2 + R
C_12 = U1 + U2 + S + R.
```

These transforms are generic over an additive commutative group. The candidate proves both
compositions are identities, the expected reconstruction equations, equivariance under exchanging
the two source-labelled coordinate positions, and linearity with respect to component subtraction.
The coordinate theorem acts on an arbitrary four-entry cumulative function; it does not transport
heterogeneous source types, keys, counts, laws, or inherited events.

## Complete coordinate theorem

The central supplied-count statement is quantified over the coordinate type rather than repeated
24 times:

```lean
theorem all_24_averaged_coordinates_empirical_eq_count_expression
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (coordinate : SxPid2Coordinate)
    (h_total : 0 < totalCount count) :
    averagedSxPid2Coordinate (empiricalLaw count) coordinate =
      sxPid2CountCoordinateExpression count coordinate
```

`SxPid2Coordinate` has four cumulative or four atom positions for each of three components. The
candidate also fixes an ordered 24-element list, proves its length and absence of duplicates,
proves its finite-set projection is the complete coordinate universe, and proves the coordinate
type has cardinality 24.

For every component and atom, the finite empirical average of pointwise Möbius atoms equals the
Möbius transform of the four averaged cumulatives:

```lean
theorem averaged_pointwise_atom_eq_mobius_of_averaged_cumulatives ...
```

Thus the paper-defined “invert pointwise, then average” and “average cumulatives, then invert”
routes coincide for the fixed finite empirical formalization.

## Exact product and sign reduction

For a coordinate `coordinate`, the candidate constructs a positive real product from exact
rational local arguments and an exact rational counterpart. It proves

```lean
averagedSxPid2Coordinate (empiricalLaw count) coordinate =
  (1 / (totalCount count : ℝ)) *
    Real.log (countCoordinateRealProduct count coordinate)
```

and that the real product is the cast of the exact rational product. Since the total is positive
and the product is positive, the candidate derives:

```text
coordinate > 0  iff  product > 1
coordinate < 0  iff  product < 1
coordinate = 0  iff  product = 1.
```

These are mathematical equivalences for the supplied exact count function. They do not verify a
parser, product evaluator, comparison implementation, report schema, or resource bound.

## Assumptions and units

- The source index is exactly `Fin 2`; source alphabets may be heterogeneous but are finite.
- The target alphabet is finite.
- Source and target values have decidable equality.
- Counts are exact natural numbers and total count is positive.
- Only positive-count anchors enter local logarithms and averages.
- All logarithms are natural logarithms; quantities are in nats.
- The fixed event map and its publication correspondence are supplied semantics, not conclusions
  of this module.

## Explicit nonclaims

This preliminary claim does **not** establish:

- nonnegativity of informative or misinformative atoms, or any other universal atom-sign theorem;
- row, byte, table, file, or JSON parsing into the supplied count function;
- refinement of Rust `NODES2`, `invert2`, pointwise accumulation, result fields, or atom order;
- equality to `pid-core` binary64 logarithms or summation;
- refinement of the standalone certifier, Python bindings, MPFR, a compiler, or a runtime;
- overflow, allocation, cancellation, time, memory, or other resource behavior;
- a sampling, concentration, uncertainty, population, calibration, or consistency result;
- continuous Ehrlich/KSG shared-exclusions estimators, fitted quantized wrappers, `I_min`, or
  Shannon-invariant families;
- a three-source or general higher-source lattice;
- scientific priority, uniqueness, application validity, release readiness, or downstream
  authority; or
- completion before the pending checker, semantic variations, PDF verification, scope binding, and
  independent review all pass.

The sign equivalences classify a coordinate once its exact product is known. They neither prove a
particular coordinate is negative nor replace the omitted component-nonnegativity theorem.

## Preliminary evidence state

The theorem-to-obligation crosswalk is in [`formal/theorem-map.md`](formal/theorem-map.md). The
current evidence inventory is in [`evidence-matrix.md`](evidence-matrix.md), and the acceptance
gates are in [`obligations.md`](obligations.md). [`decision-v1.md`](decision-v1.md) records a hold
for integration rather than a mathematical rejection. Until those gates close, references to this
packet must use “candidate”, “preliminary”, or equivalent wording.
