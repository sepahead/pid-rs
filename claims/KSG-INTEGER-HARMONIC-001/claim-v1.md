# Claim KSG-INTEGER-HARMONIC-001, revision 1

## Status and class

State: **active**. This packet freezes a proposed numerical-implementation refinement before any
estimator source is changed. It is not a new KSG estimator, a consistency theorem, or evidence that
neighbor counts, population support, or an application are valid.

The exact integer identity is a mathematical claim. Agreement of one binary64 implementation with
the committed corpus is a bounded executable-conformance claim. Those evidence classes remain
separate.

## Exact claim

For integers

```text
n >= 2,
1 <= k < n,
k - 1 <= nx < n,
k - 1 <= ny < n,
```

the KSG1 local count term satisfies the exact-real identity

$$
\psi(k)+\psi(n)-\psi(n_x+1)-\psi(n_y+1)
=H_{k-1}+H_{n-1}-H_{n_x}-H_{n_y},
$$

where $H_0=0$, $H_m=\sum_{j=1}^m 1/j$, and information is measured in nats. A runtime path
whose four digamma coefficients sum to zero may therefore evaluate the right-hand side directly,
without approximating Euler's constant or a noninteger digamma function.

Revision 1 proposes a second, bounded software claim: a compensated binary64 harmonic-prefix
implementation should match the existing independent 80-digit Decimal corpus on all 6,920
exhaustive feasible tuples through $n=16$ and 1,278 fixed stress tuples through $n=10^6$, with
a frozen post-implementation ceiling chosen only after final-tree replay. The finite corpus does
not establish a universal binary64 error theorem.

## Objects and quantifiers

- Exact objects: positive integer digamma arguments, rational harmonic numbers, and the KSG local
  count expression above.
- Software objects: the shared integer-count arithmetic used by Euclidean/hyperbolic KSG and any
  shared-exclusions research path with the same coefficient pattern; the independent fixture
  generator and committed fixture.
- Universal quantifier: the exact-real identity holds for every integer tuple in the displayed
  domain.
- Finite quantifier: executable error evidence covers exactly the committed tuple corpus.

## Assumptions

- The estimator formula actually has coefficients $(+1,+1,-1,-1)$ on four positive integer
  digamma arguments. A heuristic with another coefficient sum is outside this claim.
- Neighbor counts satisfy the displayed range. This packet does not prove that the neighbor search
  produces the correct counts.
- The executable check assumes IEEE 754 binary64 round-to-nearest behavior used by the tested Rust
  targets. No cross-platform transcendental identity is needed by the proposed harmonic path.

## Conclusion

The exact-real replacement is definition-preserving on the admitted integer-count paths. If the
software obligations close, it removes avoidable digamma-asymptotic and Euler-constant error from
those paths while preserving finite binary64 rounding and cancellation as explicit residual error
sources.

## Non-solutions

- Merely loosening the existing 256-epsilon test ceiling.
- Replacing the estimator or changing neighbor-shell semantics.
- Introducing exact rationals into the default runtime without a resource/API claim.
- Applying the cancellation identity to a heuristic whose digamma coefficients do not sum to
  zero.
- Calling bounded fixture agreement a proof of estimator consistency or universal correct
  rounding.

## Falsifiers

- A valid integer tuple for which the exact identity fails.
- A runtime call site classified as coefficient-cancelling when its coefficients do not sum to
  zero or its indices do not match the harmonic indices.
- Any committed oracle cell outside the frozen post-change executable ceiling.
- Changed neighbor counts, serial/parallel disagreement, a resource-estimate regression, or a
  material analytic-reference regression caused by the arithmetic change.
- Removal of the noninteger digamma path while a non-cancelling heuristic still requires it.

## Permitted evidence and completion check

Permitted evidence is: a source-independent symbolic derivation from
$\psi(m)=H_{m-1}-\gamma$; the standard-library-only Decimal generator; exact rational spot
checks; mutation/property tests; Rust feature-path replay; and analytic KSG fixtures.

Completion requires every obligation in `obligations.md` to close, the final numerical ceiling and
observed maximum to be recorded without extrapolation, documentation/catalog boundaries to remain
accurate, and all repository gates named by the affected methods to pass.
