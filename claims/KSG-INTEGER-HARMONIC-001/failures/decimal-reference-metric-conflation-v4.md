# Decimal-reference metric conflation, revision 4

## Failure

The first revision-4 packet described an observed maximum of
`8 * f64::EPSILON` nats with 40 ties as though it were error against the stored
80-digit Decimal values. That was false. Both the Rust test and the Python
binary64 route first converted each Decimal string to binary64, then subtracted
two binary64 values.

The old number therefore measured

```text
abs(selected_binary64 - binary64(stored_decimal_text)).
```

It did not measure

```text
abs(exact_value(selected_binary64) - exact_harmonic_rational).
```

Frozen revisions 1--3 are not rewritten. This memo preserves the revision-4
false statement and its correction.

## Separately implemented directed-enclosure route

`scripts/check-ksg-harmonic-exact-enclosure.py` does not import pid-rs, the
oracle generator, or the main revision checker. It reconstructs the 8,198-row
order, then builds lower and upper harmonic-prefix bounds with separate
160-digit `ROUND_FLOOR` and `ROUND_CEILING` Decimal contexts. For each
nonendpoint row it propagates the signs through directed interval arithmetic.
Structural endpoints are cancelled symbolically. This route assumes the Python
Decimal implementation obeys its documented directed-rounding semantics; it
is computational enclosure evidence, not a kernel proof.

Both interval endpoints round to the same 80-digit `ROUND_HALF_EVEN` value for
all 8,198 rows. The newline-delimited exact-rounded vector has SHA-256:

```text
1d33f7f89c973a70c4e76619a4fa494ce163992509d31be7daea381bb1e9e747
```

An exact `Fraction` reconstruction separately checks containment for all 6,920 exhaustive
rectangular-arithmetic outer-box rows; this is not a runtime-shell-image enumeration. It shares
the formula, generated row order, and structural-endpoint classification with the directed route,
so engine separation is not failure independence. That finite cross-check does not extend to the
1,278 stress rows; those retain Python Decimal directed rounding as a computational premise.

A second exact-rational use has a different scope: after both stored and exact-rounded 80-digit
strings pass canonical finite-Decimal validation, each Decimal operand is converted exactly to
`Fraction`. All 8,198 stored/reference absolute differences are subtracted and ordered as
rationals. This removes the ambient Decimal precision context from the **difference comparator**;
it does not make stress-row harmonic construction Fraction-exact.

## Corrected results

The binary64-rounded-reference comparator remains:

```text
maximum             = 8 * f64::EPSILON nats
tie count           = 40
first zero-based row = 7598
(n,k,nx,ny)         = (4096,1,2048,2048).
```

Against the exact harmonic rational, directed bounds isolate one unique
maximizer at zero-based row 7673, tuple `(4096,4,2049,2049)`. The selected
binary64 value is:

```text
-0x1.6b52fe6a01407p+2
= -5.67694053985633839687352519831620156764984130859375.
```

The exact-rational absolute error is enclosed by:

```text
lower =
2.167446422088005150275671429474969824136427179560898493282553682662172266784817744579758400790213907338588461575762025354130852141897942153682690e-15

upper =
2.167446422088005150275671429474969824136427179560898493282553682662172266784817744579758400790213907338588461575762025354130852141897942153690778e-15
```

Thus the maximum is below `9.761311 * f64::EPSILON` nats and remains below the
finite-corpus ceiling `32 * f64::EPSILON` nats. The next-largest row's upper
bound is below the winning row's lower bound, so uniqueness is not inferred
from rounded display values. The strict comparison uses a downward-rounded
epsilon threshold, so an upward-rounded threshold cannot create a false pass.

The stored prefix-sum Decimal strings are also not exact-rational references:

```text
stored strings textually unequal to exact-rounded strings = 6509
stored values numerically unequal at 80 digits            = 5934
maximum stored/exact-rounded difference                 = 8.18e-77 nats
exact maximum difference                                = 818/10^79
reduced exact maximum difference                        = 409/(5*10^78)
unique zero-based row                                   = 7952
(n,k,nx,ny)                                             = (65536,64,32799,32799)
binary64 conversions that differ                        = 0.
```

The zero binary64-conversion differences explain why the former comparator
still produced a coherent binary64 regression signature. They do not make the
two mathematical metrics interchangeable.

Across the full corpus, the selected route produces exactly 354 positive zeros,
zero negative zeros, and 7,844 nonzeros. The exact-enclosure self-test kills
29/29 registered direction, precision, containment, uniqueness, selected-value,
signed-zero, metric-separation, ceiling, custody, and scope mutations in both
normal and optimized Python. The rounded-Decimal-subtraction regression and wrong-exact-fraction
controls belong to a separate exact-comparator firewall; they do not increase the 29
scientific/custody mutation count. Normal and optimized replay rejects both `2/2` comparator
controls while retaining `29/29` registered mutation kills.

## Boundary

These are finite-corpus, association-specific arithmetic results. The
160-digit working precision is validated for this corpus by interval
co-rounding; it is not a universal precision theorem. Nothing here proves Rust
or Decimal implementation refinement, portable binary64 identity, neighbor
counts, KSG or Ehrlich estimator validity, population support, PID semantics,
calibration, or application suitability.
