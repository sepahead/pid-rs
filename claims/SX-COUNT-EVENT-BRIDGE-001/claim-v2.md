# Claim SX-COUNT-EVENT-BRIDGE-001, revision 2

## Status and provenance

State: **complete within the bounded supplied-count formal-semantics scope**.
Revision 2 supersedes revision 1. Revision-1 files retain their historical proposal but now carry
explicit superseded labels so direct readers cannot mistake them for current authority. The only
mathematical target correction is the count quantifier: an empirical table is an arbitrary
natural-valued count function with positive total; individual complete keys may have zero count,
and logarithms are evaluated only on strictly positive count support. The retained correction is in
[`failures/revision-1-nonzero-cell-quantifier.md`](failures/revision-1-nonzero-cell-quantifier.md).
The active closure graph and route registry are [`obligations-v2.md`](obligations-v2.md) and
[`routes-v2.md`](routes-v2.md); [`revision-index.md`](revision-index.md) preserves the lineage.
The abandoned evaluator prototype and its evidence boundary are retained in
[`failures/abandoned-native-decide-prototype.md`](failures/abandoned-native-decide-prototype.md).

This remains a project-defined formal-semantics bridge for the existing paper-defined two-source
averaged categorical shared-exclusions functional. It defines no new PID measure and changes no
`pid-core` numerical semantics.

## Publication-to-formalization boundary

The categorical pointwise shared-exclusions construction and component decomposition are defined
by Abdullah Makkeh, Aaron J. Gutknecht, and Michael Wibral,
[“Introducing a Differentiable Measure of Pointwise Shared Information”](https://doi.org/10.1103/PhysRevE.103.032149)
(2021). The parthood, antichain, and formal-logic semantics used to organize the node collections
are developed by Aaron J. Gutknecht, Michael Wibral, and Abdullah Makkeh,
[“Bits and Pieces: Understanding Information Decomposition from Part-Whole Relationships and Formal Logic”](https://doi.org/10.1098/rspa.2021.0110)
(2021).

The correspondence from those publication formulas to `sxPid2Collections`, `sxPid2SourceEvent`,
and `sxPid2TargetRestrictedEvent` is a reviewed project transcription. It is not itself a theorem
proved by Lean. Lean proves the count/event consequences conditional on that selected formal
encoding. This bridge therefore supplies no assurance for continuous Ehrlich/KSG estimators,
`I_min`, quantized wrappers, or Shannon-invariant families.

## Exact target

For two heterogeneous finite source alphabets, one finite target alphabet, an arbitrary exact
natural count function on the complete key space, and positive total count, define:

- total count, exact empirical law, and strictly positive count support;
- the source-one, source-two, joint-source, and redundancy cumulative nodes;
- keyed source, target, and target-restricted events using `SxEventBridge`;
- exact event counts and their empirical masses;
- supported informative, misinformative, and signed-net local cumulatives; and
- the positive-support empirical average of each signed-net cumulative.

The checked main theorem is:

```lean
theorem sxpid2_averaged_cumulative_net_count_expression
    {sourceValue : Fin 2 → Type v} {targetValue : Type w}
    [∀ source, Fintype (sourceValue source)] [Fintype targetValue]
    [∀ source, DecidableEq (sourceValue source)] [DecidableEq targetValue]
    (count : CategoricalKey (Fin 2) sourceValue targetValue → ℕ)
    (node : SxPid2Node)
    (h_total : 0 < totalCount count) :
    averagedCumulativeNet (empiricalLaw count) node =
      ∑ anchor ∈ positiveSupport count,
        ((count anchor : ℝ) / (totalCount count : ℝ)) *
          Real.log ((countNetArgument count node anchor : ℚ) : ℝ)
```

For an anchor in `positiveSupport count`, the exact rational logarithm argument is

```text
total_count * target_restricted_event_count
------------------------------------------------- .
source_event_count * target_event_count
```

Every factor required in its denominator and numerator is proved positive from positive anchor
count and keyed-event anchor membership; positivity is not an input axiom.

## Quantifiers, assumptions, and units

- Universal over all finite heterogeneous two-source alphabets, finite target alphabets, natural
  count functions, all four fixed cumulative nodes, and every supported anchor.
- The total count is strictly positive. Zero-count keys are permitted and excluded from the
  averaging/logarithm domain.
- Natural logarithms and nats.
- Counts are supplied exact mathematical inputs. No histogram, parser, allocation, overflow, or
  resource behavior is modeled.

## Checked supporting conclusions

1. The empirical law is nonnegative and normalized when total count is positive.
2. Empirical mass of every finite event equals event count divided by total count.
3. Redundancy source-event count satisfies exact two-event inclusion-exclusion.
4. Target-restricted redundancy satisfies the corresponding identity.
5. The joint-source target-restricted event is the anchor singleton and has anchor count.
6. All three keyed event counts and masses are positive on positive count support.
7. The probability-domain local signed-net logarithm equals the exact rational count expression.
8. The main positive-support averaged count expression holds for all four nodes.

The exact theorem crosswalk is retained in [`formal/theorem-map.md`](formal/theorem-map.md).

## Definition-unfolding asymmetric semantic witness

For binary sources and target, the complete-key counts in `(s1,s2,t)` lexicographic order are

```text
[1, 2, 3, 4, 5, 8, 6, 7].
```

At anchor `(0,0,0)`, total count is `36`, target count is `15`, source-event counts in node order
are `[10,16,3,23]`, target-restricted counts are `[4,6,1,9]`, and the four exact rational net
arguments are `[24/25,9/10,4/5,108/115]`. Their pairwise distinction makes source swapping and
joint/redundancy conflation visible.

This witness unfolds the same checked definitions as the theorem source. It is a discriminating
regression witness, not an independent proof route.

## Explicit residual boundaries

This claim does **not** establish:

- bytes, rows, JSON, or another input representation to the Lean count function;
- Rust categorical row sorting or histogram extraction to that function;
- refinement of Rust `NODES2`, `invert2`, atom order, or output fields;
- binary64, MPFR, Python, compiler, runtime, or standalone-certifier semantics;
- integer overflow, expression normalization, parsing, allocation, cancellation, or budgets;
- concrete Möbius inversion or atom identities;
- more than two sources;
- formal derivation, uniqueness, or certification of the publication-to-Lean correspondence;
- the distinct continuous shared-exclusions/Ehrlich/KSG route, Williams–Beer `I_min`, fitted
  quantized wrappers, Shannon invariants, or another estimator or assurance family;
- an empirical-process, sampling, concentration, population, calibration, priority, release, or
  consumer-validity theorem.

Passing executable differential tests remains corroboration, not a replacement for any open
refinement edge above.

## Evidence and completion

The formal phase is bound by pinned Lean kernel replay, an exact ordered declaration inventory, a
SHA-256 pin over the complete two-source count/event bridge, `collectAxioms` audits of all 201 named
source theorem declarations, digest-pinned semantic examples, an asymmetric exact witness, and
baseline-first negative mutations. The 16 compiled semantic `example`s are digest-pinned as one
contract but are not individually passed through `collectAxioms`. `native_decide` is forbidden;
semantic finite enumeration uses kernel `decide`.

Obligation D1 binds this scope into the method catalog, generated method view, assurance registry,
public limitations, formal maps, and four deterministically checked rendered artifacts without
widening any residual boundary. The final adjudication is retained in
[`decision-v2.md`](decision-v2.md). Completion remains limited to supplied exact counts and
two-source signed-net cumulative mathematics.
