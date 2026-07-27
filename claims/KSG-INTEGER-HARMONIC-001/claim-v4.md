# Claim `KSG-INTEGER-HARMONIC-001`, revision 4

## Status, chronology, and evidence class

Revision 4 is the active **post-result integration** revision. It was written after the exact
identity, schema-2 corpus, formal extensions, and modular residues were observed; it is not a
preregistration. It preserves revisions 1--3 byte-for-byte. Revision 3 remains a frozen
pre-closure **NO-GO** because its custody and completion statements were not simultaneously true.

The exact positive-integer arithmetic core, the scoped Lean/Z3 obligations, and the bounded
8,198-row modular classification are **GO on their stated domains**. Repository/publication
integration is **NO-GO** until the open gates in `integration-disposition-v4.md` close on one
isolated settled tree. No final revision-4 evidence matrix or decision is asserted yet.

## Exact object, domain, range, and units

Let

```text
H_0 = 0
H_j = sum_(r=1)^j 1/r
T = psi(k) + psi(n) - psi(x) - psi(y)
D = H_(n-1) - H_(k-1).
```

Information quantities are in **nats**. The rectangular positive-integer arithmetic domain fed by
the inventoried estimator mappings is

```text
n >= 2
1 <= k < n
k <= x <= n
k <= y <= n.
```

Exclusive KSG counts satisfy `k-1 <= nx,ny < n` and map to `x=nx+1,y=ny+1`. Inventoried
anchor-inclusive Ehrlich ISX/PID3 counts satisfy `k <= x,y <= n` after their declared shell checks
and are passed directly. These inequalities are an outer box, not a claim that every tuple is
realizable by unique-shell neighbour geometry. Only the coefficient vector
`(+1,+1,-1,-1)` is eligible.

Under the typed analytic premise

```text
psi(m) = H_(m-1) - gamma
```

at the four positive integer arguments, exact cancellation gives

```text
T = H_(k-1) + H_(n-1) - H_(x-1) - H_(y-1)
  = (H_(n-1) - H_(max(x,y)-1))
    - (H_(min(x,y)-1) - H_(k-1)).
```

Harmonic monotonicity yields the sharp two-sided bound over that rectangular arithmetic domain

```text
-D <= T <= D.
```

The pure Lean arithmetic theorem admits the slightly larger domain `1 <= k <= n`; this does not
authorize a runtime estimator to accept `k=n`. The box-domain bound permits negative terms. It is
forbidden to clamp them, and it is not a bound on MI, redundancy, any PID atom, estimator bias,
calibration, or application error. At the smallest rectangular boundary `n=2,k=1`, helper tuples
realize `+D`, `-D`, and zero. The `-D` tuple is not asserted to be realizable by a runtime
unique-shell geometry.

A post-observation set derivation establishes `x+y <= n+k` only as a **conditional source lemma**:
the local call must have a finite positive max-product radius, an unambiguous unique kth shell,
exact strict-radius membership counts on one common row set, and the inventoried exclusive or
anchor-inclusive count map. Under those premises, inclusion--exclusion gives the inequality. On
the constrained integer outer domain it yields the candidate lower bound

```text
H_(k-1) + H_(n-1)
  - H_(floor((n+k)/2)-1)
  - H_(ceil((n+k)/2)-1)
<= T.
```

That bound is sharp on the constrained integer domain, but neither it nor `x+y <= n+k` is promoted
into the revision-4 theorem inventory. Source refinement, formalization, compiled witnesses,
mutations, and provenance remain open; runtime attainability of the balancing tuple is not
asserted.

## Frozen schema-2 and binary64 result

The reviewed generator/fixture/sidecar digests are:

```text
a4ef8a87a154ad0e1edd84013f025462fe80c32e2012f07154bb8db8ca78143b  generator
560e36346272c845ad1cd443c13741738b06b02a8035ea43c8ced06b1d80147c  fixture
fb91172bdb767b3e11e15ef4e89bb0482b932c5c2450f87d566245eda87a8ec7  sidecar file
```

The fixture contains 8,198 unique ordered rows: 6,920 exhaustive rectangular-arithmetic
outer-box rows through `n=16` and 1,278 declared stress rows. “Exhaustive” does not mean
runtime-realizable. The sufficient structural endpoint predicate is

```text
(nx == k-1 and ny == n-1) or (nx == n-1 and ny == k-1).
```

It identifies 354 rows, split into 240 exhaustive and 114 stress rows. On this frozen corpus only,
the modular certificate proves that exact rational `T=0` **iff** this predicate holds. The
structural predicate is only asserted sufficient outside this corpus; no universal
harmonic-zero-classification theorem is claimed.

The selected binary64 route uses a Neumaier-compensated harmonic prefix and sorted symmetric range
association. On exactly these 8,198 rows it has:

```text
binary64-rounded-reference maximum = 8 * f64::EPSILON nats
first rounded-reference maximum    = (4096,1,2048,2048)
rounded-reference maximum ties     = 40
exact-rational maximum upper bound < 9.761311 * f64::EPSILON nats
unique exact-rational maximum      = row 7673, (4096,4,2049,2049)
selected value at exact maximum    = -0x1.6b52fe6a01407p+2
allowed finite-corpus ceiling      = 32 * f64::EPSILON nats
source-swap bit asymmetries        = 0
selected endpoint outputs          = 354 positive zeros
selected endpoint negative zeros   = 0
selected endpoint nonzeros         = 0
selected full-corpus outputs        = 354 positive zeros, 0 negative zeros, 7,844 nonzeros
```

The full-corpus partition is now counted directly by compiled Rust over every selected helper
output, with finiteness checked for the stored rounded reference, selected result, and swapped
result before bit classification. It is fixed-corpus implementation correspondence, not an
independent proof of the exact zero classification.

The `8*EPSILON` quantity first rounds each stored Decimal reference to binary64. It is not the
error against the stored Decimal value or exact harmonic rational, not eight ULPs, and not an
ordered-binary64-position distance. A separately implemented 160-digit directed-rounding
enclosure gives the exact-rational maximum above and isolates its unique row. The strict epsilon
comparison uses a downward-rounded threshold; the complete interval is retained in
`failures/decimal-reference-metric-conflation-v4.md`. Its baseline-first self-test kills 29/29
registered mutations in normal and optimized Python. Exact-`Fraction` comparator controls are
reported separately, reject 2/2 registered faults in normal and optimized Python, and do not
increase that scientific/custody mutation count.

The stored 80-digit prefix-sum strings differ textually from the exact-rational correctly rounded
80-digit strings on 6,509 rows and differ numerically on 5,934 rows. Each finite Decimal operand
is converted exactly to `Fraction` before subtraction and ordering. The unique maximum numeric
difference is exactly
`818/10^79 = 409/(5*10^78) = 8.18e-77` nats at zero-based row 7,952, but all 8,198 pairs convert
to the same binary64 value. The exact-rounded vector digest is
`1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747`.
This is a retained negative result, not permission to conflate the references.

Over the same selected Neumaier prefix, ordinary four-term left association is nonzero at 150/354
endpoints and produces zero negative zeros. A separately constructed naive prefix has a
different 121/354 result and zero negative zeros. Neither signed-zero count is a discriminating
theorem; they are exact finite-corpus regression tripwires.

## Behavioral bridges

W1 reaches production-private ordered KSG diagnostics at zero-based row 5:

```text
radius = 79
exclusive counts = (nx,ny) = (4,1)
helper call order (k,n,x,y) = (2,8,5,2)
exact-real T = 107/210
selected bits = 0x3fe04e04e04e04e0.
```

W2 uses the inclusive Ehrlich map `(5,2)` and reaches the same local target. Its public
compensated mean differs from the correctly rounded exact `71/840` by eight
**ordered-binary64 positions**. That is a fixture/path observation, not an ULP-error theorem and
not a validation of an Ehrlich estimator.

## Formal and modular results

The revision-4 Lean source has SHA-256
`32b5d5e11aa244cb9683d71281f05b27e8093dd9a4d5e677ad4b1e68ffc76ee4`.
It checks 19 theorem declarations and kills 14/14 baseline-first semantic mutations. The Z3 route
has four satisfiable positive preflights, four unsatisfiable negated obligations, and 12/12
satisfiable semantic countermodels; the local-bound source digest is
`33c9bb7a13c9e8c0cc88ca1750b9510481b3f64ea4ecac8c7497e16d6850df31`.

The Z3 checker additionally uses a bounded ASCII S-expression parser and exact ordered
per-obligation command, declaration, sort, operator, arity, and terminal-form profiles. It
validates all four raw-digest and token-stream-pinned snapshots before a solver starts, derives
the positive form only from the validated in-memory negative snapshot, and sends both forms over
standard input. Grammar/profile/pin/transport controls are a separate firewall class; they do not
increase the 12 solver-semantic countermodels. The repaired self-test rejects 52/52 controls in
both normal and optimized runs: 16 lexer/parser, 25 profile/type, and 11
custody/transport/result.
Raw and token pins remain correlated custody of the same source bytes, and the bounded profile is
not a semantic theorem prover. A retained well-typed wrong-theorem dual-rebase witness still
preserves the expected solver outcomes, so theorem-intent approval remains a human/Git/receipt cut.

Both routes share the analytic digamma premise, human signs, index maps, and selected theorem
statements. Z3's harmonic function is uninterpreted and its bound uses explicit local order
premises. Neither route proves Rust refinement, binary64 behavior, neighbor geometry, KSG/Ehrlich
validity, support, MGW PID, or application validity.

The current canonical modular certificate has SHA-256
`5c1923413edecb27bde19d388ab3365844e07bc0ba5f0fa9b28672053ef8901f`.
In each selected prime field `1000033`, `1000037`, and `1000081`, all 354 endpoints have
zero residue and all 7,844 nonendpoints have nonzero residue. Since every selected prime exceeds
the maximum reciprocal summand denominator/index `999999`, each denominator in every `1/j`
summand is invertible; a nonzero residue therefore implies the exact rational is nonzero. The
three primes provide redundant fault diversity, not CRT reconstruction and not three independent
proofs.

Rejected prime `1000003` has four exact-nonzero/nonendpoint zero-residue collisions. It
demonstrates that a zero residue does not imply an exact rational zero in general. The earlier
digest `1d5f61b1135b8bb69f6cf11c377ad8e9ba3ba3b806421bdff10a1d24355120bc`
is only a historical pre-artifact observation; it is not current certificate custody. The modular
self-test kills 28/28 registered mutations in normal and optimized Python. Recursive exact JSON
shape/type/value checks reject 2/2 registered Boolean/integer firewall controls in normal and
optimized Python; those controls are separate from the 28 scientific/custody mutations.

The rejected collision has an elementary field explanation. For an odd prime `p` and
`H_j = sum_(r=1)^j r^(-1) mod p`, pairing `r` with `p-r` gives
`H_(p-1-t) = H_t mod p`. At `p=1000003`, the frozen maximum index is
`999999=p-4`, so `H_999999=H_3 mod p`. This explains the four signed copies of one collision; it
does not prove selected-prime separation. In particular, index 33 occurs in the corpus, and
absence or presence of a reflected index is not a separation proof. The exhaustive canonical
certificate is the authority for the selected fields, which share this reflection structure and
are not independent.

## Ten-object firewall

This claim is confined to KSG local integer arithmetic. It does not transfer a theorem to:

1. the complete KSG MI estimator;
2. continuous Ehrlich shared-exclusions redundancy;
3. continuous PID2 compositions;
4. categorical Makkeh--Gutknecht--Wibral shared-exclusions PID;
5. Williams--Beer `I_min`;
6. fitted quantized SxPID;
7. project-defined ISX heuristics;
8. incomplete or research mixed-dimensional PID3;
9. resampling/report/Python wrappers; or
10. software identity, release, consumer, or application validity.

Such a transfer requires its own premises and an explicit mapping/refinement theorem. No such
theorem is supplied here.

## Falsifiers and completion boundary

The scoped core is reopened by an exact counterexample, an index/sign/domain error, a changed
schema-2 row/order/digest, a selected-prime nonendpoint collision, a structural endpoint nonzero,
a failed no-write generator replay, a noncanonical/type-confused/NaN fixture value, a failed
directed enclosure or reference-metric separation, a changed W1/W2 count map, a changed binary64
signature, a reviewed-prose byte mismatch, or a surviving registered formal, modular, custody, or
semantic mutation.

Repository integration remains NO-GO until claim custody, phase isolation, source/compiled replay,
catalog/release closure, generated audience artifacts, software identity, final hostile review,
and settled-tree CI all pass. The canonical unsigned M1a implementation commit must first be
pushed and verified while the disposition is still NO-GO. Only a separate descendant M1c
milestone may then create and bind immutable `evidence-matrix-v4.md` and `decision-v4.md`.
