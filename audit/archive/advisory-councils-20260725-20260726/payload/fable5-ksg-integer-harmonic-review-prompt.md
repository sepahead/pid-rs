# Fable 5 Max adversarial brief — `KSG-INTEGER-HARMONIC-001` revision 1

You are an external, read-only adversarial reviewer. Do not edit, commit, push, or weaken any gate.
Use scratch files only under `/tmp`. Model agreement is not evidence. Re-derive and try to falsify
the claim from first principles; label every unretained search result as diagnostic.

## Frozen context

- Repository: `/Users/torusprime/Development/sepahead-github/pid-rs`
- Base commit: `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7`; the worktree intentionally contains a
  completion candidate, so hash every live file used.
- Date: 2026-07-25; binary64 round-to-nearest-even; information units are nats.
- `Cargo.lock` SHA-256:
  `2a390c1a3f468ed938e8c2e6597e78b26b933761c6200b0bf5e01d4b75f3c81d`.
- Claim/checkpoint SHA-256 values:
  - `claim-v1.md`: `726907d19af21db00f3b4245722ac7a0d83b7e6df814aa3e589db47624344c44`
  - `obligations.md`: `b22e061070d16e69a39ede6f367a01c600b9c917ab199debc5ebca267b3b502e`
  - `routes.md`: `23b521232290b30c5d346b42f8cc55ecb1c5f639607a4fa03496cbdd3d1fe256`
  - exact-numerics memo: `1487761f2da443771854a1ad61b25042bb18267d68a67452e43d3c3a89d7cc7e`
  - call-site map: `048aaa4209f5c42616f18339775c463f1ac45fe7d25581c7b9d37d571d79c5a6`
  - implementation checkpoint: `83ee2a03b55ebc2161c3fec6dfe9a40680e8fae0b0bcebb01d5a1533f6872440`
  - evidence matrix: `f9de6f6ebdd6fe30887c34e3abedef504ffbd2bba5e113a70f22a8f0b004b4fc`
  - decision: `0dabc4d4a0247cf55aa03f433bc47eab6f8b2f245824d27da0c7927ce30b79fe`
- Source/checker SHA-256 values:
  - `stats.rs`: `481a1e9c2dd33df01a2a98e32ebd5218f99478b2e7baf308f832851457ee9d96`
  - `ksg.rs`: `cb2084ddd60d1f802ec54f3e4cd388157929f2b309d949c61146fe72c6537a3b`
  - `isx.rs`: `5aca9a2b3108fe37aa80834f22c101ef647f8f48734d302bc26f866e47a05201`
  - `pid3.rs`: `f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd`
  - production checker: `c6bfe0a9d8164e03e808401f79486c19ede096376eb58c78ed2dfa914ca93b67`
  - self-test: `abbd508700947750773ed7990c46468b367d77f58cbaa993e2fa9bb4f250c8eb`
- Settled release-scope SHA-256:
  `33be6677db0550dea6693026a3c179ecfa5c2a238e8ca3e532ad18d592f5d030`.
- The method catalog is still awaiting unrelated PID2 evidence-path regeneration; its current
  provisional SHA-256 is `58029843233dce89492ebe8863617a356121df4d232db3b4671c90dc74def150`.

Read completely before judging:

- `AGENTS.md` and `MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md`;
- every file in `claims/KSG-INTEGER-HARMONIC-001/`;
- `crates/pid-core/src/{stats,ksg,isx,pid3}.rs` and all KSG/ISX/PID3 arithmetic tests;
- `scripts/check-ksg-harmonic-revision.py` and its self-test;
- the immutable Decimal fixture/generator and checksum;
- affected release/catalog entries, README/limitations/changelog wording, and the current diff.

## Exact claim under attack

At positive-integer call sites with digamma coefficients `(+1,+1,-1,-1)`, use

```text
psi(k)+psi(n)-psi(x)-psi(y)
  = (H_(n-1)-H_(max(x,y)-1)) - (H_(min(x,y)-1)-H_(k-1)).
```

KSG exclusive counts pass `x=nx+1,y=ny+1`; anchor-inclusive shared-exclusions sites pass their
counts directly. A Neumaier-compensated prefix table stores `table[m]=H_(m-1)`. The coefficient-
sum-two heuristic remains on general digamma. On the frozen 8,198-cell Decimal corpus the final
helper observes at most `8*f64::EPSILON`, is gated at `32*f64::EPSILON`, and has zero x/y-swap bit
asymmetries. This is a numerical estimator revision, not a universal error theorem or a change to
neighbor semantics, support assumptions, or method definitions.

## Required attacks

1. Re-derive the positive-integer digamma cancellation and every off-by-one mapping. Attack the
   `n=2,k=1`, sparse, dense, equal-count, exact-zero, and largest stress endpoints.
2. Independently reproduce or refute the 6,920 exact-rational cases and 8,198 Decimal comparisons.
   Inspect Decimal generation, parsing, cancellation residuals, absolute-vs-ULP error, and the
   asserted eight/32-epsilon figures.
3. Compare direct four-term, range, pairwise-sum, compensated, and alternative exact-real-
   equivalent associations. Explain whether source symmetry by construction hides any accuracy
   regression or merely resolves an arbitrary evaluation order.
4. Attack Neumaier prefix construction: table indexing, zero/unused entry, lost compensation,
   overflow of `usize` or `n+1`, division casts, large-n stagnation, resource preflight, allocation,
   serial/parallel determinism, and platform behavior.
5. Audit every call site. Find any coefficient that does not cancel, inclusive/exclusive mismatch,
   helper bypass, duplicate direct formula, or contamination of the non-cancelling heuristic.
6. Audit the 85-mutation suite. Distinguish textual source/release kills from compiled behavioral
   evidence, seek equivalent-mutant blind spots, and propose the smallest missing discriminators.
7. Independently reconstruct the 15 affected release families and 18 protected families. Pay
   special attention to the four combined PID2 revision strings without treating the separate PID2
   correction as KSG evidence.
8. Check docs/catalog wording for estimator-definition conflation, bounded-to-universal promotion,
   implied performance, support inference, calibration, source-swap claims, or consumer readiness.
9. Apply semantic, exact-mathematical, numerical, executable, formal-boundary, statistical,
   provenance, portability/resource, compatibility, and downstream-authority lenses.
10. Try hard to produce one exact counterexample or one executable failing case. If none survives,
    state exactly what was searched and why it remains finite evidence.

## Required output

- `GO`, `CONDITIONAL GO`, or `NO-GO`, with exact blockers;
- corrected obligation graph and minimal critical cut sets;
- independently derived arithmetic/index results and any retained counterexamples;
- exact affected/protected dependency closure;
- minimal regression/mutation additions, each paired with the fault it kills;
- strongest permitted wording and prohibited promotions; and
- at least twelve concrete adversarial failure scenarios paired with existing or missing gates.

Do not call finite/model-generated evidence a theorem, formal verification, universal rounding
bound, estimator calibration, compatibility proof, or consumer qualification.
