# Claim SX-COUNT-EVENT-BRIDGE-001, revision 1

> **Historical/superseded revision.** Revision 2 is the only active authority. This file retains
> revision 1's proposed scope for auditability; do not use its quantifier, obligations, routes, or
> state as current evidence. See [`claim-v2.md`](claim-v2.md) and
> [`revision-index.md`](revision-index.md).

## Status and provenance

State: **superseded by revision 2; historical only**. This was a proposed project-defined
formal-semantics bridge for the existing paper-defined two-source averaged categorical
shared-exclusions functional. It defined no new PID measure and did not alter `pid-core` numerical
semantics.

The target deliberately closes one contiguous mathematical-specification segment. It is not a
claim that Rust, a compiled binary, JSON parsing, the standalone certifier, sampling, or a
population estimator is end-to-end formally verified.

## Exact target

For two heterogeneous finite source alphabets, one finite target alphabet, and an exact nonzero
natural-number count assigned to every complete categorical key, define:

- the total count and exact empirical law;
- positive count support;
- the four fixed two-source SxPID cumulative nodes;
- keyed source, target, and target-restricted source events using `SxEventBridge`;
- exact event counts and their empirical masses;
- the supported local signed-net probability ratio; and
- the empirical average of each cumulative signed-net value.

The main theorem must prove that every averaged cumulative signed-net value equals the
positive-support count-weighted sum of logarithms of its exact positive rational count argument:

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

The final checked signature may refine names or expose positivity premises more explicitly, but it
must not weaken the mathematical objects or replace the count expression with an uninterpreted
function.

## Quantifiers, assumptions, and units

- Universal over all finite heterogeneous two-source alphabets, finite target alphabets, exact
  natural count functions, all four declared cumulative nodes, and all supported anchors.
- The total count is positive. Local logarithms are evaluated only on positive-support anchors,
  and every event denominator used there must be proved positive.
- Natural logarithms and nats.
- Counts are already exact mathematical inputs. No parser, histogram implementation, integer
  overflow, allocation, or resource behavior is assumed to be modeled.

## Mandatory supporting conclusions

1. Empirical mass of a finite event equals its exact event-count/total-count ratio.
2. The redundancy source-union count satisfies two-event inclusion–exclusion.
3. The target-restricted redundancy union satisfies the corresponding restricted identity.
4. The joint-source target-restricted event count equals the keyed anchor count.
5. Every supported exact net argument is positive.
6. The probability-domain local signed-net ratio equals the exact rational count ratio embedded in
   the main average.

## Non-solutions

- Another abstract finite-sum or logarithm lemma with no keyed Sx event instantiation.
- A concrete symmetric binary example in place of the quantified theorem.
- A theorem about an uninterpreted lattice node or event extractor.
- Reusing the independent Python verifier as a Lean axiom.
- Calling this a `pid-core`, binary64, certifier, or population refinement proof.
- Extending immediately to Möbius atoms or exact-product sign before this event/count bridge closes.

## Falsifiers

- Source-one/source-two node swapping passes on an asymmetric exact count example.
- Redundancy union is accidentally replaced by intersection or double-counted overlap.
- Target restriction can be removed without a checker/mutation failure.
- The joint target-restricted theorem returns a marginal rather than the complete keyed count.
- A zero-count anchor reaches a logarithm, or positivity is assumed rather than derived.
- Any theorem inventory, axiom audit, or semantic-contract example omits the new declarations.
- Documentation implies Rust/executable/population verification.

## Evidence class and completion

Revision-1 accepted evidence was a pinned Lean kernel replay, complete declaration and axiom
inventory, semantic examples for the intended publication correspondence, targeted negative
mutations, and separately checked exact asymmetric examples. Those examples unfold the same
definitions and are not an independent proof route. Executable differential tests may corroborate
the mapping but cannot promote it to Rust refinement.

Revision-1 completion required every obligation in `obligations.md` to close, all named mutations
to fail for their intended reason, the formal source/checker digests and method-catalog evidence to
be updated, and explicit residual boundaries to survive a scope mutation.
