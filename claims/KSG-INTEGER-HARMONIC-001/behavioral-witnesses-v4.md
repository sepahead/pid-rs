# Behavioral witnesses for `KSG-INTEGER-HARMONIC-001`, revision 4

## W0 — smallest signed-boundary witness

In the pure helper domain take `n=2,k=1`, so `D=H_1-H_0=1`. Then:

```text
(x,y)=(1,1) -> +1 = +D
(x,y)=(2,2) -> -1 = -D
(x,y)=(1,2) or (2,1) -> 0.
```

This proves the two-sided bound is attained at the smallest domain boundary and refutes
nonnegativity on the rectangular helper domain or any silent clamping. It is exact arithmetic,
not a claim that all four count configurations arise from runtime unique-shell neighbor geometry;
in particular, this witness does not establish runtime attainability of `-D`.

## W1 — ordered exclusive KSG bridge

Use `n=8`, `k=2` and the fixed one-dimensional source/target rows retained in revisions 2 and 3.
The production-private diagnostic at zero-based row 5 must report:

```text
joint radius = 79
exclusive marginal counts = (nx,ny) = (4,1)
helper call order (k,n,x,y) = (2,8,5,2)
exact-real local term = H_7-H_4 = 107/210
selected bits = 0x3fe04e04e04e04e0.
```

The ordered count assertion matters because the public scalar and helper are source symmetric; a
swapped implementation could otherwise preserve that scalar. Brute-force and kd-tree backends
must produce the same ordered diagnostic. This finite bridge does not prove neighbor correctness
outside the fixture.

## W2 — anchor-inclusive Ehrlich bridge

Reuse W1 as source 1 and target, and set `s2[i]=1000*s1[i]+i`. The source disjunction distance
reduces to source 1's distance on every pair. At the same zero-based row 5 the anchor-inclusive
counts are:

```text
n_alpha = 5
n_t = 2
helper call order (k,n,x,y) = (2,8,5,2)
exact-real local term = 107/210
selected local bits = 0x3fe04e04e04e04e0.
```

The public compensated mean has bits `0x3fb5a35a35a35a3e`; the correctly rounded exact `71/840`
has bits `0x3fb5a35a35a35a36`. Their unsigned encodings differ by eight
ordered-binary64 positions. This wording does not assert eight ULPs or an estimator-error bound.

### W2b — all-unique structural-zero count endpoint

Anchor inclusion does not force `n_alpha >= k+1`: the kth joint neighbour can lie on the joint
shell because of its source-disjunction coordinate and therefore fail the strict source count.
Take zero-based query row 0 of:

```text
n=3, k=1
target = [0, 0.4, 0.8]
s1     = [0, 1,   3]
s2     = [0, 10, 30].
```

The two joint distances are `1` and `3`, so the unique first-neighbour shell has raw radius `1`.
Both non-anchor target distances are strictly below `1`, while neither non-anchor
source-disjunction distance is. Hence:

```text
n_alpha = 1 = k
n_t     = 3 = n
helper call order (k,n,x,y) = (1,3,1,3)
exact-real and selected local term = +0.
```

Every coordinate value is unique, and all three query rows have a unique positive first-neighbour
shell. Private diagnostics bind the radius, counts, and positive-zero bits; the public route binds
support preflight and the positive-zero compensated mean. This is a finite implementation witness.
All-unique samples do not prove the declared population-support model.

## W3 — 354 structural endpoint cancellations

For a fixture row satisfying

```text
{nx,ny} = {k-1,n-1},
```

the exact four-harmonic multiset cancels pairwise. Schema 2 contains 354 such rows: 240 exhaustive
and 114 stress. Every reference is canonical string `"0"`; the selected range route produces
354 `+0` outputs and zero `-0` outputs.

The selected Neumaier-prefix ordinary-left route is nonzero on 150/354 endpoints and has zero
negative-zero outputs. A separately constructed naive-prefix route gives 121/354 and zero
negative-zero outputs. Therefore an association count must name its prefix. The zero-sign results
are structural regression tripwires, not independent validation or universal signed-zero
theorems.

Compiled Rust now also checks finiteness before classifying every selected output in the full
8,198-row corpus and directly obtains `+0/-0/nonzero=354/0/7844`. That scan closes a prior
source-to-claim correspondence gap. It shares the fixture, endpoint rule, and helper with the
other corpus routes and therefore is not independent mathematical evidence.

## W4 — selected modular separation

For each prime below, u32 big-endian residues are stored in fixture order:

| Prime | Endpoint zeros | Nonendpoint nonzeros | Residue-vector SHA-256 |
|---:|---:|---:|---|
| `1000033` | `354` | `7844` | `931c30fab8560d5692121f3c16be42afa4e9d0b73e640ca4285f5352f4cfff9b` |
| `1000037` | `354` | `7844` | `09b6d9e5a4f9f5ee4346dbfc869ba254710f6198cba97f2ac3449db8adb16479` |
| `1000081` | `354` | `7844` | `20b2596be7ed67e9fb07039465196da9c289f87d0e13b87d85e8bcf964b18de0` |

Every prime exceeds the maximum reciprocal summand denominator/index `999999`, so every
`1/j` summand used to construct the harmonic values has an invertible denominator. A nonzero
residue proves exact rational nonzero. The corpus-only iff combines that one-way implication for
nonendpoints with structural pair cancellation for endpoints.

## W5 — rejected-prime counterexamples

Prime `1000003` has residue-vector digest
`d90959d75ff1c84c56c3354b5b5f5d7d633fc873692266bd5d61874eb8254111`
and four nonendpoint zero-residue collisions:

| Zero-based index | `(n,k,nx,ny)` | Exact sign |
|---:|---|---|
| `8045` | `(1000000,3,2,3)` | positive |
| `8049` | `(1000000,3,3,2)` | positive |
| `8069` | `(1000000,4,3,3)` | positive |
| `8093` | `(1000000,4,999999,999999)` | negative |

The first three reduce to the same strictly positive reciprocal tail and the fourth to its
negative. Thus the four rows expose one modular divisibility event rather than four independent
events. One counterexample is sufficient: zero modular residue does not imply exact zero. The
selected triple is redundant fault diversity, not CRT.

For odd prime `p`, the shared event follows from the elementary prime-field reflection identity

```text
H_(p-1-t) = H_t mod p.
```

Indeed, pairing `r` with `p-r` gives `H_(p-1)=0`, and the last `t` reciprocal terms equal
`-H_t`. For `p=1000003`, `999999=p-4`, so `H_999999=H_3 mod p`. The selected fields have the same
reflection structure. Index 33 occurs in the corpus, and neither presence nor absence of a
reflected index proves separation; only exhaustive certificate replay establishes the selected
finite-corpus result.

## W6 — exact-rational enclosure and reference separation

Separate 160-digit directed-rounding prefix bounds co-round to one 80-digit exact-rational value
on every row. Their newline-delimited vector digest is
`1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747`.
They isolate a unique exact-rational maximum-error row:

```text
zero-based row = 7673
(n,k,nx,ny)    = (4096,4,2049,2049)
selected value = -0x1.6b52fe6a01407p+2
error upper    < 9.761311 * f64::EPSILON nats.
```

The earlier `8 * f64::EPSILON` result has 40 ties because it compares two binary64 values after
rounding each stored Decimal string. The stored prefix-sum strings are textually unequal to the
exact-rounded 80-digit strings on 6,509 rows and numerically unequal on 5,934 rows, but all pairs
convert to the same binary64 value. Exact `Fraction` subtraction of each finite Decimal pair gives
the unique stored/reference maximum
`818/10^79 = 409/(5*10^78) = 8.18e-77` at row 7952. This explains the old regression signature
without making the two metrics equivalent. The checker uses a downward-rounded strict epsilon
threshold; exact-comparator controls remain separate from its 29 registered enclosure mutations.

## W7 — conditional runtime count-set lemma

For a successful local call with a finite positive max-product radius and an unambiguous kth
shell, define the two strict-radius marginal membership sets `A,B` on the common sample rows.

- Exclusive KSG excludes the anchor:
  `|A intersect B|=k-1`, `|A union B|<=n-1`, and
  `(x,y)=(|A|+1,|B|+1)`.
- Anchor-inclusive Ehrlich includes the anchor:
  `|A intersect B|=k`, `|A union B|<=n`, and `(x,y)=(|A|,|B|)`.

In either mapping, inclusion--exclusion gives `x+y<=n+k`. Increasing harmonic prefixes make a
maximizer saturate that constraint; decreasing increments then make the balanced pair
`floor((n+k)/2),ceil((n+k)/2)` maximize `H_(x-1)+H_(y-1)` on the constrained integer outer
domain, yielding the candidate stronger lower bound recorded in `claim-v4.md`. This is a
conditional source/set lemma, not a promoted revision-4 theorem:
formal/refinement/mutation/provenance lanes and runtime attainability of the balanced pair remain
open.

## Common firewall

W0--W7 concern exact/local arithmetic, conditional set geometry, and finite implementation
bridges. They do not prove KSG MI consistency, continuous Ehrlich shared-exclusions calibration,
continuous PID2 atoms, categorical MGW SxPID, `I_min`, fitted quantized SxPID, heuristic
correctness, PID3 validity, support, application suitability, or consumer readiness.
