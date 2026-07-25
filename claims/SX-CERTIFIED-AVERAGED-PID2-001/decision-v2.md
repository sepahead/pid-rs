# Decision for SX-CERTIFIED-AVERAGED-PID2-001, revision 2

## Decision

**Conditionally supported for revision-2 per-input interval containment and, only where status is
`compared`, exact rational-product zero/strict-sign decisions.**

This is a re-adjudication, not an automatic carry-forward. Revision 1 required re-adjudication for
exactly the schema, resource-policy, source-manifest, verifier, sign-semantics, and claim-boundary
changes made here. Its historical decision remains in [decision.md](decision.md).

## Supported wording

> For a revision-2 certificate accepted by the bound independent verifier, every dyadic interval
> contains the independently reconstructed exact-real averaged categorical SxPID2 coordinate.
> When the same verifier independently validates a coordinate's bounded exact-product record with
> status `compared`, its exact-zero or strict-sign decision follows from exact rational comparison
> after integer denominator clearing. The interval and exact-product decisions remain distinct.

The decision is conditional on the reviewed verifier source and its explicit runtime and semantic
premises. It is not formal verification, binary64 refinement, statistical certification, or
release authority.

## Why the extension is justified

1. The frozen empirical coordinate has the exact form $F=(1/n)\log R$ with $n>0$ and exact
   positive rational $R$ after integer denominator clearing.
2. Comparing the numerator and denominator of $R$ is a complete exact decision for $F=0$, $F>0$,
   or $F<0$ and invokes no transcendental approximation.
3. The producer computes term-count, exponent, per-expression projected-bit, and aggregate
   projected-bit evidence before allocating powers.
4. The independent verifier reconstructs the expression and product, recomputes all preflight
   fields, validates the product decision, and separately proves interval containment.
5. A retained total-eight binary table demonstrates why empty-term-only zero detection is sound
   but incomplete: a nonempty five-term net-unique expression has product exactly one while the
   directed interval remains `unresolved_sign`.
6. Exhaustive and mutation evidence challenges both mathematical identities and implementation
   boundaries on explicitly finite domains without being promoted to universal proof.

## Required abstention semantics

Product status other than `compared` supplies no sign or exact-zero claim. It must carry no
decision and no zero witness. The revision-2 interval route remains authoritative for value
containment. Absence of a product decision must never be converted into a sign, zero, error bar,
or confidence statement.

## Open obligations preventing stronger wording

- No end-to-end proof assistant refinement connects accepted bytes to the executable verifier.
- Six generic log/product/sign theorems and the retained witness's exact five-factor rational
  identity are Lean checked. The exact-rational and Rust routes separately bind those factors to
  the SxPID coordinate, but Lean does not check concrete SxPID event extraction, lattice binding,
  resource preflight, verifier refinement, or runtime semantics.
- Python, `Fraction`, JSON, SHA-256, filesystem/process behavior, and the verifier implementation
  remain trusted.
- A full containing Git commit can provide ordinary immutable repository-source retrieval, but the
  packet has no independent custody, external transparency record, authorship proof, or binary
  attestation.
- No statistical, population, application, or downstream qualification is part of this decision.

## Prohibited wording

- “pid-rs is formally verified”;
- “the `pid-core` or binary64 estimator is certified”;
- “the interval is a confidence interval”;
- “all SxPID atoms have a proved sign”;
- “product preflight abstention proves zero or nonzero”;
- “continuous or higher-source PID is covered”;
- “the data or executable is authentic”; or
- “independent review/custody is complete.”

## Revision-2 re-adjudication triggers

Revision 2 requires a new revision if any of the following changes:

1. an input, report, expression, verification, resource-policy, or exact-product evidence schema;
2. the definition revision, event masks, coordinate order, Möbius matrix, or zeta matrix;
3. exact-term normalization or denominator-clearing rule;
4. product preflight projection, ceiling, powering, comparison, status, decision, or witness;
5. rational-log range reduction, series, tail bound, fixed-point scale, or rounding;
6. interval normalization, width, sign, consistency, or subset-acceptance semantics;
7. source-manifest membership or encoding;
8. verifier source/runtime requirements or permitted/excluded claim boundary; or
9. any claimed evidence count, immutable binding, or external-review status.

Historical revisions must remain identifiable and must not be silently rewritten.
