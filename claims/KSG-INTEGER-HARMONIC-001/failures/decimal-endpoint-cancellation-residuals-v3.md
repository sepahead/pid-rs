# Retained failure: Decimal endpoint-cancellation residuals and spellings

## Scope

This is a bounded oracle-construction correction for `KSG-INTEGER-HARMONIC-001`. It does not
change the exact positive-integer harmonic identity, the tuple domain, tuple order, production
arithmetic, neighbor counts, an estimator, or the Makkeh--Gutknecht--Wibral functional.

## Smallest structural family

For every feasible tuple with

```text
{nx, ny} = {k - 1, n - 1},
```

the exact multiset

```text
H_(k-1) + H_(n-1) - H_(nx) - H_(ny)
```

cancels pairwise to zero before any numerical operation. This rule is sufficient for exact zero;
it is not asserted to characterize every possible equality between two sums of harmonic numbers.
The frozen 8,198-cell corpus contains exactly 354 such structural endpoints: 240 in the complete
`2 <= n <= 16` enumeration and 114 in the declared stress set.

## Failure in schema revision 1

Schema revision 1 formed and stored 80-digit Decimal prefix sums before subtracting the four
selected values. Among the 354 exact endpoint cancellations:

- 26 strings were numerically nonzero residuals from `-4E-79` through `2E-79`;
- 326 were numerically zero with precision-dependent spellings such as `0E-79`, `0E-78`, or
  `0.0`; and
- two were already the canonical string `0`.

Thus 352 strings change under canonicalization, but only 26 are semantic numerical corrections.
A 160-digit diagnostic changed 28 parsed binary64 references at exact-zero endpoints. That
precision comparison is diagnostic evidence, not a new universal Decimal error theorem.

The frozen schema-revision-1 artifacts remain identifiable by:

```text
4cb0c14c0b7ceae7e465ea5c54111ce784597b03eae15fbcebd91dbaaa92b5f4  fixture
8912d49bb830444fcfd3c4b65ec15792ea86b487d2ae91cf985b53d58b408615  generator
```

They remain reachable in Git history and are not rewritten.

## Revision-3 correction

Schema revision 2 recognizes only the sufficient structural endpoint rule above and emits the
canonical positive-zero reference string `"0"` before Decimal evaluation. Every non-endpoint cell
continues to use the declared 80-digit Decimal prefix calculation. The production selected-range
path returns positive-zero bits `0x0000000000000000` on all 354 endpoints. Ordinary direct
left-association is nonzero on 150 of those 354 cells, so no global zero-sign or evaluation-order
claim follows.

The correction does not change the measured bounded result: replay still finds maximum absolute
error `8*f64::EPSILON` nats, first maximum `(4096,1,2048,2048)`, 40 maximum-error ties, and zero
source-swap bit asymmetries.

## Evidence and shared cuts

Custody is a conjunction, not a checker-only generation proof:

1. the generator is pinned by SHA-256 and declares standard-library-only dependencies;
2. generator no-write replay reproduces every canonical fixture byte;
3. the sidecar binds the fixture bytes;
4. Python and Rust validate schema, split counts, rule text, all endpoint references, and the
   absence of canonical `"0"` outside the structural endpoint set; and
5. resealed endpoint-to-nonzero and nonendpoint-to-zero mutations are rejected.

The generator branch and the exact algebra routes share the endpoint identity. At those 354 cells
the Decimal route is therefore not independent of that identity. The exact `Fraction`, Lean, Z3,
and compiled routes also share the human sign/index map unless explicitly stated otherwise.

## Non-implications

This correction does not establish correct rounding on nonzero cells, a universal error bound,
neighbor-search correctness, support validity, estimator consistency, PID-atom validity, or
application calibration.
