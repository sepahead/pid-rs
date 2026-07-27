# Revision-2 erratum to the exact-numerics route memo

This file is append-only. It does not alter
`route-memo-exact-numerics-2026-07-25.md` or any other revision-1 byte.

## Corrected association table

All three rows below use the same Neumaier-compensated shifted-harmonic prefix table and the same
8,198 parsed Decimal references. `f64::EPSILON` is $2^{-52}$; the measurement is maximum absolute
error in nats divided by that constant.

| Association after prefix construction | Maximum error | Count-swap asymmetries | Cells attaining maximum |
|---|---:|---:|---:|
| plain left-associated `((Hk + Hn) - Hx) - Hy` | 16 eps | 764 | 8 |
| Neumaier reduction of `[Hk,Hn,-Hx,-Hy]` | 8 eps | 0 | 39 |
| selected sorted range `(Hn-Hmax)-(Hmin-Hk)` | 8 eps | 0 | 40 |

The revision-1 phrase “compensated direct four-term harmonic arithmetic” attached to the
`16`/`764` row is false: those numbers identify the uncompensated left-associated expression.
This is non-load-bearing for selection of the range route, but load-bearing for an accurate
evidence record.

## Complete maximum-tie set for the selected range

The first tuple in corpus order is `(4096,1,2048,2048)`. It is not a unique worst cell. The
complete 40-tuple `(n,k,nx,ny)` set observed on the frozen corpus is:

```text
(4096,1,2048,2048)
(4096,2,2048,2048)
(4096,3,2049,2049)
(4096,4,2049,2049)
(4096,16,2055,2055)
(65536,3,3,3)
(65536,4,32769,32769)
(1000000,1,500000,500000)
(1000000,1,500000,999998)
(1000000,1,999998,500000)
(1000000,1,999998,999998)
(1000000,2,500000,500000)
(1000000,2,500000,999998)
(1000000,2,999998,500000)
(1000000,2,999998,999998)
(1000000,3,2,3)
(1000000,3,3,2)
(1000000,3,3,3)
(1000000,3,500001,500001)
(1000000,3,500001,999998)
(1000000,3,999998,500001)
(1000000,3,999998,999998)
(1000000,4,3,3)
(1000000,4,3,4)
(1000000,4,4,3)
(1000000,4,4,4)
(1000000,4,999999,999999)
(1000000,8,7,7)
(1000000,8,7,8)
(1000000,8,8,7)
(1000000,8,8,8)
(1000000,8,500003,500003)
(1000000,8,500003,999999)
(1000000,8,999999,500003)
(1000000,8,999999,999999)
(1000000,64,500031,999999)
(1000000,64,999998,999998)
(1000000,64,999998,999999)
(1000000,64,999999,500031)
(1000000,64,999999,999998)
```

Freezing the multiplicity detects association or fixture changes that preserve both the eight-
epsilon maximum and its first attaining tuple. It remains a finite-corpus discriminator rather
than an error theorem.
