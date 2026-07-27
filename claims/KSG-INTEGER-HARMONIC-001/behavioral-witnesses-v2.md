# Tiny behavioral witnesses for `KSG-INTEGER-HARMONIC-001` revision 2

These are frozen regression designs. Their distances, counts, rational target, and binary64
association were independently checked. They remain **open for compiled Rust replay** and must not
be cited as already implemented tests.

## W1 — KSG exclusive-count witness

Use `n=8`, `k=2`, one-dimensional inputs

```text
x = [7,194,144,75,61,138,38,9]
y = [17,48,166,120,2,199,43,93].
```

All rows and marginal values are unique. Every second-neighbor joint Chebyshev shell has exactly
one strict-interior and one boundary point. The `(eps_raw,nx,ny)` rows are

```text
(54,2,3)
(119,2,6)
(69,2,2)
(69,5,2)
(54,3,3)
(79,4,1)
(41,4,2)
(66,3,3).
```

At zero-based row 5, KSG must pass exclusive counts as `x=5,y=2`. The exact local term is

$$
H_1+H_7-H_4-H_1=H_7-H_4=\frac15+\frac16+\frac17=\frac{107}{210}.
$$

For this selected cell, the frozen range evaluation equals the correctly rounded rational value:

```text
hex float: 0x1.04e04e04e04e0p-1
raw bits:  0x3fe04e04e04e04e0
```

A public `ksg_local_mi_terms` test should assert the full shell validity and row-5 bits. It kills
an exclusive/inclusive or off-by-one call-site fault without using the large arithmetic fixture as
its count oracle.

## W2 — Ehrlich ISX anchor-inclusive witness

Reuse W1 as `s1=x` and `target=y`. Define

```text
s2[i] = 1000*x[i] + i.
```

For every distinct pair, the `s2` distance strictly exceeds the `s1` distance. The bivariate
source-disjunction distance `min(ds1,ds2)` is therefore exactly `ds1`, so the joint disjunction
shells and exclusive source/target counts are W1's. ISX initializes both counts with the anchor.
At row 5 it must therefore pass

```text
n_alpha = 4 + 1 = 5,
n_t     = 1 + 1 = 2,
```

and obtain the same exact local term `107/210` and raw bits `0x3fe04e04e04e04e0`.

The public redundancy is an implementation-level propagation check, not an exact-real rounding
target. With the frozen prefix/range/local-reduction order its expected bits are

```text
hex float: 0x1.5a35a35a35a3ep-4
raw bits:  0x3fb5a35a35a35a3e.
```

The exact-real average of the eight local formulas is `71/840`, whose correctly rounded bits are
`0x3fb5a35a35a35a36`. Their unsigned integer encodings differ by `8`, so they are eight binary64
ULP steps apart at this exponent. This distinction is intentional evidence separation: assert the
exact row-5 local target in a private diagnostic test, and assert the frozen public scalar
separately. Do not claim the public average is correctly rounded from the exact-real mean.

## Support and scope

These fixed rows are algorithmic conformance inputs compatible with an explicitly declared
full-dimensional continuous model; they do not infer that model from observed uniqueness. They do
not prove neighbor-search correctness outside the listed cells, population support, estimator
consistency, calibration, or Makkeh--Gutknecht--Wibral PID atom validity. The ISX fixture targets
the Ehrlich continuous shared-exclusions count path only.
