# Claim `KSG-INTEGER-HARMONIC-001`, revision 3

## Status and revision boundary

Revision 3 is the active **KSG-only** bounded arithmetic claim. It retains revisions 1 and 2 and
does not rewrite their pre-correction observations, open gates, hashes, or decisions. This revision
was created after the exact identity, the first schema-revision-1 corpus result, and the first
91-mutation combined-tree run were observed. It is therefore a transparent post-result correction
and integration claim, not a preregistration of those observations. It freezes the schema-revision-2
corpus, KSG-only release phase, and remaining integration obligations before catalog/release
closure. Any later PID2-combined release state requires a new claim/release revision.

The claim is about a positive-integer local arithmetic kernel used by KSG and eligible Ehrlich
shared-exclusions paths. It is not a theorem about neighbor geometry, population support,
estimator consistency, bias, calibration, PID atoms, or the Makkeh--Gutknecht--Wibral functional.

## Exact objects, domains, and units

Let `H_0=0` and `H_j=sum_(r=1)^j 1/r`. All information values are in nats.

| Route | Domain | Helper arguments |
|---|---|---|
| exclusive KSG | integers `n>=2`, `1<=k<n`, `k-1<=nx,ny<n` | `x=nx+1`, `y=ny+1`, hence `k<=x,y<=n` |
| inclusive Ehrlich ISX/PID3 | integers `n>=2`, `1<=k<n`; counts include the anchor and satisfy `k<=x,y<=n` after the declared shell checks | pass `x,y` without a successor |

Only the coefficient-cancelling combination `(+1,+1,-1,-1)` is eligible. The heuristic branch
with a nonzero coefficient sum remains on general digamma arithmetic.

For positive integer `m`, assume the analytic identity

```text
psi(m) = H_(m-1) - gamma.
```

Then, for either mapped helper domain,

```text
T(n,k,x,y)
  = psi(k) + psi(n) - psi(x) - psi(y)
  = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1).
```

Writing `a=min(x,y)` and `b=max(x,y)`, exact algebra gives

```text
T = (H_(n-1) - H_(b-1)) - (H_(a-1) - H_(k-1)).
```

Both parenthesized ranges are nonnegative. With `D=H_(n-1)-H_(k-1)`, the exact-real bound is

```text
-D <= T <= D.
```

The result itself may be negative. This bound is exact-real and is not a binary64 error bound.

## Selected binary64 implementation and bounded result

The selected Rust path builds `table[m]=H_(m-1)` by a Neumaier-compensated positive prefix and
evaluates the source-symmetric range expression using `min(x,y)` and `max(x,y)`. It inherits the
Rust target's IEEE-754 binary64 round-to-nearest, ties-to-even operations. The claim does not cover
fast-math reassociation, foreign implementations, or a platform on which those semantics are not
provided.

The frozen schema-revision-2 fixture contains:

- every 6,920 feasible helper tuple through `2<=n<=16`;
- 1,278 deterministic stress tuples at
  `n in {17,32,64,256,4096,65536,1000000}`; and
- 8,198 total unique tuples in fixed order.

For the exact structural endpoint rule `{nx,ny}={k-1,n-1}`, the four harmonic terms cancel
pairwise before Decimal evaluation. The fixture contains 354 such cases (240 exhaustive and 114
stress), stores canonical reference string `"0"`, and the selected range path returns positive-zero
bits on all 354. This rule is sufficient; revision 3 does not claim it characterizes every possible
harmonic-sum zero.

Against the schema-revision-2 references, the selected binary64 path has on exactly this corpus:

```text
maximum absolute error       = 8 * f64::EPSILON nats
allowed finite-corpus ceiling = 32 * f64::EPSILON nats
first maximum tuple           = (n,k,nx,ny)=(4096,1,2048,2048)
maximum-error tie count       = 40
source-swap bit asymmetries   = 0
```

The error is an absolute error in nats. It is not an ULP count, a relative bound, a correct-rounding
claim, a universal binary64 theorem, or an error guarantee for an MI/PID estimate.

## Schema-revision-2 correction

Relative to the retained schema-revision-1 fixture, tuple membership, tuple order, and every case
field other than `expected_nats` are unchanged. Exactly 352 strings change: 26 nonzero Decimal
residuals of magnitude `1e-79` through `4e-79` become exact `"0"`; 326 numerical-zero spellings are
canonicalized; two endpoint strings were already `"0"`. Non-endpoint cells continue to use the
80-digit Decimal prefix calculation. Details and non-implications are retained in
`failures/decimal-endpoint-cancellation-residuals-v3.md`.

## Runtime correspondence claim

Subject to the existing finite-input, unique-positive-shell, support-declaration, and resource
checks in each caller:

1. KSG passes exclusive marginal counts as `nx+1,ny+1`;
2. eligible Ehrlich ISX/PID3 code passes anchor-inclusive counts directly;
3. the non-cancelling heuristic path does not call the integer-harmonic helper;
4. all 15 release families whose scalars can change carry KSG-only estimator revisions;
5. all 20 affected method-catalog entries cite this revision and its bounded evidence; and
6. every other release family is an exact negative control, including both unlanded I_min
   migrations.

The four PID2-emitting release families stop at their KSG-only bridge revisions. A subsequent PID2
milestone must advance them under a new claim; revision 3 must reject the combined strings.

## Formal-assurance boundary

Lean and Z3 establish exact algebra, ranges, symmetry, and index consequences under typed premises.
They do not prove the analytic digamma identity from first principles, Rust refinement, neighbor
search, binary64 behavior, estimator validity, or MGW PID. Lean and Z3 share the analytic premise
and the human sign/index correspondence. Z3 treats the harmonic function as uninterpreted. Their
distinct kernels do not make those shared cuts independent.

## Custody boundary

Fixture custody is the conjunction of pinned generator bytes, no-write byte reproduction, the
fixture sidecar, checker validation, and compiled Rust replay. The checker alone is not a proof
that the generator produced every row. SHA-256 is integrity/custody evidence, not authenticity or
scientific validity. Git history retains the schema-revision-1 fixture and generator bytes.

## Non-solutions and non-implications

- Do not use the non-cancelling digamma heuristic as evidence for this reduction.
- Do not call `8*EPSILON` eight ULPs or extrapolate the 8,198 cells to all integers.
- Do not infer support, finite MI, consistency, calibration, high-dimensional accuracy, or
  application validity from arithmetic conformance.
- Do not infer a theorem about continuous shared exclusions or any PID atom.
- Do not transfer evidence to `I_min`, categorical SxPID, fitted quantized SxPID, or another PID
  definition without an explicit mapping theorem.
- Do not claim this modifies or validates the Makkeh--Gutknecht--Wibral definition.
- Do not treat normal/optimized Python, debug/release Rust, serial/parallel Rust, or model-name
  agreement as fully independent mathematical proofs.

## Falsifiers and completion condition

Revision 3 is falsified or reopened by any exact counterexample to the stated identity/domain map;
any tuple/order/canonical-endpoint mismatch; any corpus error above the frozen ceiling; any changed
first maximum, tie count, or swap bit result; any eligible live call site with the wrong successor
map; any non-cancelling heuristic routed through the helper; any stale/combined/over-bumped release
identity; any affected catalog entry without the revision-3 evidence; a surviving registered
mutation; or a failed required compiled/formal/release gate.

Completion requires every AND-obligation in `obligations-v3.md`, an immutable evidence matrix and
decision, exact staged-snapshot replay, and a pushed unsigned commit. Open statistical, support,
application, and MGW obligations remain outside this narrow claim rather than being silently
promoted.
