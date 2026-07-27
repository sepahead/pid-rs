# Behavioral witnesses for `KSG-INTEGER-HARMONIC-001` revision 3

## W1 — exclusive KSG count map

Use the fixed eight one-dimensional rows in `crates/pid-core/tests/ksg.rs`, `k=2`, Chebyshev
distance, and the declared finite algorithmic conditions. Every joint shell has one strict-interior
and one boundary neighbor. At row index 5:

```text
radius = 79
nx = 4
ny = 1
helper arguments = (k,n,x,y) = (2,8,5,2)
exact-real term = H_7 - H_4 = 107/210
selected binary64 bits = 0x3fe04e04e04e04e0
```

`107/210` is not exactly representable as binary64. The bit assertion pins the selected
association, not exact f64 representability or estimator calibration. The exact mean of the eight
local targets is `71/840`.

## W2 — inclusive Ehrlich map

Use the same first source and target and construct `s2[i]=1000*s1[i]+i`. For every selected row
pair, the second-source distance strictly exceeds the first-source distance, so the source
disjunction `min(d_s1,d_s2)` reduces exactly to `d_s1`. At row 5:

```text
inclusive source-union count = 5
inclusive target count = 2
helper arguments = (2,8,5,2)
exact-real term = 107/210
selected binary64 bits = 0x3fe04e04e04e04e0
```

The private local diagnostic and public redundancy propagation must both be replayed. The public
compensated average and the exactly rounded rational mean differ by eight ordered-binary64
positions on this fixture; that is a field/path implementation observation, not an error theorem.

## W3 — endpoint cancellation

For any fixture tuple with `{nx,ny}={k-1,n-1}`, the exact four-term multiset cancels. Schema
revision 2 contains 354 such endpoints (240 exhaustive, 114 stress). Every reference is canonical
string `"0"`, no nonendpoint reference has that string, and the selected Rust range path returns
positive-zero bits on every endpoint.

The schema-revision-1 direct Decimal-prefix expression produced 26 nonzero residual strings and
326 noncanonical zero spellings in this family. Ordinary binary64 left association is nonzero on
150 endpoints. Zero semantics are therefore path-specific.

## W4 — exact small boundaries

The exhaustive exact route retains:

```text
(n,k,x,y)=(4,1,1,1) -> 11/6
(4,2,2,2)           -> 5/6
(4,3,4,4)           -> -1/3
```

These demonstrate both signs and the successor boundary. They do not validate neighbor counts.

## Non-implications common to W1--W4

The witnesses are finite algorithmic/arithmetic conformance cases. They do not prove population
support, KSG or Ehrlich consistency, finite-sample calibration, PID-atom validity, high-dimensional
accuracy, or any Makkeh--Gutknecht--Wibral theorem.
