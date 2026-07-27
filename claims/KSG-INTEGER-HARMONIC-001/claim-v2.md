# Claim `KSG-INTEGER-HARMONIC-001`, revision 2

## Status and revision boundary

State: **active**. Revision 2 retains revision 1's mathematical statement and narrows its
executable-evidence claims. It is an evidence and integration correction, not a new KSG estimator,
a new shared-exclusions functional, or a population/statistical theorem.

The applicable scientific line is the positive-integer local count arithmetic used by KSG1 and
the inventoried Ehrlich shared-exclusions estimator paths. Nothing in this packet transfers a
claim from another PID definition to Makkeh--Gutknecht--Wibral shared exclusions.

## Exact claim retained from revision 1

For integers

```text
n >= 2,
1 <= k < n,
k - 1 <= nx < n,
k - 1 <= ny < n,
```

the KSG1 local count term satisfies

$$
\psi(k)+\psi(n)-\psi(n_x+1)-\psi(n_y+1)
=H_{k-1}+H_{n-1}-H_{n_x}-H_{n_y},
$$

where $H_0=0$ and information is in nats. More generally, for positive integer arguments
$k\leq x,y\leq n$,

$$
\psi(k)+\psi(n)-\psi(x)-\psi(y)
=(H_{n-1}-H_{\max(x,y)-1})-(H_{\min(x,y)-1}-H_{k-1}).
$$

This follows from $\psi(m)=H_{m-1}-\gamma$ and cancellation of coefficients
$(+1,+1,-1,-1)$. KSG's exclusive counts map to `x=nx+1,y=ny+1`; the inventoried Ehrlich
ISX/PID3 counts include the anchor and are passed directly. A non-cancelling heuristic remains
outside the claim.

## Corrected bounded executable claim

On the committed 8,198-cell Decimal corpus, the frozen Neumaier-prefix, source-symmetric range
evaluation has:

- maximum absolute error `8 * f64::EPSILON` nats against the parsed Decimal references;
- zero count-swap bit asymmetries by the observed replay and structural `min`/`max` construction;
- exactly 40 cells attaining that maximum; and
- `(4096,1,2048,2048)` as the first maximum-attaining `(n,k,nx,ny)` tuple in corpus order.

The allowed gate remains `32 * f64::EPSILON` on that finite corpus. The error is an absolute error
in nats, not an ULP distance at the result's magnitude. This claim assumes the tested binary64
rounding environment and is neither a universal enclosure nor a correct-rounding theorem.

## Audit-frozen pre-correction context

The independent audit was run from Git `ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7` in a dirty
integration tree with Rust/Cargo 1.96.0. The load-bearing inspected bytes were:

| Artifact | SHA-256 |
|---|---|
| `crates/pid-core/tests/parallel_bit_identity.rs` | `0e729aa3bd047b29d09994fea163419868fb9984f6ec3ca8496bc92d1819fc3f` |
| `crates/pid-core/src/stats.rs` | `8571b4e90d9d6ad2e496704db8a0da5e3bbc50a643e282b29a6f6d75dd2b392a` |
| `crates/pid-core/src/ksg.rs` | `cb2084ddd60d1f802ec54f3e4cd388157929f2b309d949c61146fe72c6537a3b` |
| `crates/pid-core/src/isx.rs` | `5aca9a2b3108fe37aa80834f22c101ef647f8f48734d302bc26f866e47a05201` |
| `crates/pid-core/src/pid2.rs` | `cca6134429468df041399513bd54953720ed82aad814204de97b445398e5eab9` |
| `crates/pid-core/src/pid3.rs` | `f1f9d18b73312fb2e25e725382e65edf42bdaecd73d611d7dffc943221b2bfcd` |
| Decimal fixture | `4cb0c14c0b7ceae7e465ea5c54111ce784597b03eae15fbcebd91dbaaa92b5f4` |
| Decimal generator | `8912d49bb830444fcfd3c4b65ec15792ea86b487d2ae91cf985b53d58b408615` |
| claim checker | `c6bfe0a9d8164e03e808401f79486c19ede096376eb58c78ed2dfa914ca93b67` |
| checker self-test | `abbd508700947750773ed7990c46468b367d77f58cbaa993e2fa9bb4f250c8eb` |

These hashes identify the detector state; they are not final release identities.

## Objects, assumptions, and boundaries

- The exact objects are positive integer digamma arguments and rational harmonic numbers.
- The executable objects are one deterministic Neumaier prefix table and the declared binary64
  association over the finite committed corpus.
- The estimator formula must have coefficient sum zero with the displayed signs and mapped
  indices. The identity does not apply to a different coefficient vector.
- Neighbor-shell correctness, inclusive/exclusive count construction, and population-support
  premises are separate obligations. The arithmetic theorem does not establish them.
- Bare observed rows do not establish regular full-dimensional support. Tiny conformance fixtures
  may exercise a declared compatible support model but are not support or calibration evidence.
- The Decimal fixture and Rust/Python replays share the harmonic identity. Agreement is correlated
  at that cut and is not multiple independent proofs of the theorem.

## Non-solutions

- Silently replacing the frozen bit constants until tests pass.
- Calling all 13 constants changed when one is unchanged.
- Attributing the combined PID2 atom transition only to KSG.
- Rewriting the revision-1 route memo instead of retaining an erratum.
- Treating a sidecar hash as independent custody when the same change can reseal the fixture.
- Treating marker-presence checks as compiled def-use verification.
- Running only a `parallel`-enabled frozen-reference test and calling it an independent serial
  capture.
- Promoting finite arithmetic evidence to KSG consistency, shared-exclusions estimator
  calibration, population-support validity, or consumer readiness.

## Falsifiers and completion check

Revision 2 fails if the exact identity or index map is contradicted, the selected helper no longer
has the frozen finite-corpus signature, a generator/fixture mutation is accepted, a live
shadow/overwrite mutant survives its named gate, the corrected serial constants do not replay in
both serial and parallel builds, or the tiny count witnesses do not reach their derived indices.

Completion requires all obligations in `obligations-v2.md`, including final debug/release and
feature replay. A re-freeze is accepted only as a transition record after the mathematical,
fixture, compiled-behavior, and provenance gates pass; the new constants do not prove themselves.
