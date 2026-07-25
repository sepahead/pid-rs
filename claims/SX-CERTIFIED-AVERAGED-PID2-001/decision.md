# Decision for SX-CERTIFIED-AVERAGED-PID2-001, revision 1

## Decision

**Conditionally supported for the narrow per-input containment claim.**

The retained analytic argument and independent executable route support the following statement:

> For one accepted canonical exact two-source empirical count table and one certificate accepted
> by the bound independent verifier, every certificate interval contains the verifier's
> independently reconstructed exact-real averaged categorical SxPID2 coordinate, conditional on
> the verifier source, Python exact-integer/`Fraction` semantics, and the reviewed rational-log
> enclosure argument.

The decision is not “formally verified,” “independently certified,” or “release authority for
`pid-rs`.”

## Why this decision is justified

1. The claim freezes one exact definition revision, schema family, event map, two-source lattice,
   units, precision policy, and 24-coordinate order.
2. The verifier reconstructs events, exact terms, matrices, and direct mutual-information
   identities without importing the producer implementation.
3. Its logarithm route uses exact rational range reduction, a positive convergent series, an
   explicit tail bound, and exact-integer outward fixed-point rounding.
4. Acceptance requires the independently derived interval to be contained in the producer
   interval. Numerical overlap is not enough.
5. The verifier rechecks input, certificate, expression, resource, lattice, precision, source,
   lockfile, and claim-boundary evidence.
6. The bounded corpus and mutation suites provide substantial fault-finding evidence without being
   misrepresented as universal proof.
7. The exclusions prevent software evidence from being promoted into statistical or downstream
   validity.

## Open obligations that prevent stronger wording

- **Archive boundary:** the verifier and qualification harness are committed unchanged at
  `b8b9a48b88cb28d812d8cbd70b8f999a3bac5a8e`; exact file hashes are recorded in
  [bindings.md](bindings.md). This packet and its paper are retrievable through the enclosing Git
  history after publication, but there is no external transparency log, binary attestation,
  authorship proof, or independent custody.
- **F1, formal refinement:** no proof assistant or verified checker establishes the complete
  byte-to-expression-to-enclosure implementation.
- **H1, independent custody:** no independent person acquired, executed, and retained the evidence
  under separate custody.
- **Runtime trust:** Python, `Fraction`, JSON, SHA-256, filesystem, and operating-system behavior
  remain trusted.
- **Semantic transcription:** the paper-to-implementation correspondence is analytically reviewed,
  not kernel checked.

## Producer-only route

The Rust producer has a separate conditional theorem: if Rug/MPFR/GMP and the compiled directed
arithmetic wrapper obey their contracts, its intervals enclose its encoded exact expressions.
That route remains useful for construction and diagnosis.

The independent verifier is stronger for acceptance because it removes the correctness of
producer arithmetic and certificate-supplied expressions, lattice values, signs, and endpoints
from the containment trusted computing base. Those fields are still parsed as untrusted inputs,
and the producer endpoints necessarily define the interval against which subset containment is
checked. The verifier does not remove its own trusted computing base.

## Release-language gate

Permitted:

> The source-only reference certifier can be independently checked for exact-count averaged
> categorical SxPID2 interval containment under a narrow, explicit trust boundary.

Not permitted:

- “pid-rs is formally verified”;
- “the `f64` estimator is certified”;
- “this is a confidence interval”;
- “the population or support assumptions were verified”;
- “continuous or higher-source PID is covered”;
- “the input is authentic”; or
- “independent review or custody is complete.”

## Re-adjudication triggers

Revision 1 must be re-adjudicated if any of the following changes:

1. an input, report, expression, verification, or resource-policy schema identifier;
2. the definition revision;
3. event masks, node/atom order, $M$, or $Z$;
4. exact-term normalization;
5. the rational-log range reduction, series, tail bound, scale, or rounding rule;
6. interval normalization, width, sign, or acceptance semantics;
7. source-manifest membership or encoding;
8. the independent verifier or its runtime requirements; or
9. any excluded-claim boundary.

A changed claim requires a new revision. Historical revision 1 must not be silently rewritten.
