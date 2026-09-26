"""Binary64 rounding in the raw-percentile indices of the pid-rs resampling summaries.

Previous implementation (bootstrap.rs and pipeline.rs before the equal-tail fix):
    lo = floor((alpha/2)*B);  hi = min(ceil((1-alpha/2)*B) - 1, B - 1)
Corrected implementation (equal_tail_percentile_indices):
    trim = min(floor((alpha/2)*B), (B-1)//2);  lo = trim;  hi = B - 1 - trim
Both are evaluated here in binary64 exactly as Rust evaluates them (IEEE 754 round to nearest).

In exact arithmetic both forms drop floor(alpha*B/2) order statistics from each tail, because
ceil(B - x) = B - floor(x) for every real x. Two exact references are used: the exact value of
the binary64 alpha the caller passes (Fraction(alpha)), and the decimal value the caller writes
(Fraction(repr(alpha))). The script exits with status 1 if the corrected form ever drops unequal
tails, inverts the range, changes a previous lower index, or differs from both references by
more than one.
"""
import math
import sys
from fractions import Fraction


def previous(alpha, n):
    lo = math.floor((alpha / 2.0) * n)
    hi = min(max(math.ceil((1.0 - alpha / 2.0) * n) - 1, 0), n - 1)
    return lo, hi


def corrected(alpha, n):
    trim = min(math.floor((alpha / 2.0) * n), (n - 1) // 2)
    return trim, n - 1 - trim


failures = []

print("Grid 1: the 12 alpha values of the first probe, B = 2..20000")
grid1 = [0.001, 0.002, 0.005, 0.01, 0.02, 0.025, 0.05, 0.1, 0.2, 0.3, 0.32, 0.5]
binary_mismatch, decimal_mismatch, asymmetric = [], [], []
for a in grid1:
    exact_binary, exact_decimal = Fraction(a), Fraction(repr(a))
    for n in range(2, 20001):
        lo, hi = previous(a, n)
        if lo != n - 1 - hi:
            asymmetric.append((a, n))
        if lo != math.floor(exact_binary * n / 2):
            binary_mismatch.append((a, n))
        if lo != math.floor(exact_decimal * n / 2):
            decimal_mismatch.append((a, n))
print(f"  previous form, unequal tails: {len(asymmetric)}")
print(f"  lower index differs from the exact binary64-alpha floor: {len(binary_mismatch)}; "
      f"alpha values {sorted({a for a, _ in binary_mismatch})}; "
      f"all B multiples of 20: {all(n % 20 == 0 for _, n in binary_mismatch)}")
print(f"  lower index differs from the exact decimal-alpha floor: {len(decimal_mismatch)}")

print("Grid 2: every two-decimal alpha 0.01..0.99, B = 1..20000")
alphas_with_asymmetry, asymmetric_pairs, first = set(), 0, {}
below_decimal = 0
below_decimal_examples = []
above_binary = 0
above_binary_examples = []
clamp_active = 0
for hundredths in range(1, 100):
    a = hundredths / 100
    exact_decimal = Fraction(hundredths, 100)
    exact_binary = Fraction(a)
    for n in range(1, 20001):
        lo, hi = previous(a, n)
        if lo != n - 1 - hi:
            alphas_with_asymmetry.add(a)
            asymmetric_pairs += 1
            first.setdefault(a, (n, lo, n - 1 - hi))
        c_lo, c_hi = corrected(a, n)
        if c_lo != n - 1 - c_hi or c_lo > c_hi or c_hi >= n:
            failures.append(("corrected form unequal or inverted", a, n))
        if c_lo != lo:
            failures.append(("corrected form changed a previous lower index", a, n))
        if math.floor((a / 2.0) * n) > (n - 1) // 2:
            clamp_active += 1
        binary_trim = math.floor(exact_binary * n / 2)
        if c_lo != binary_trim:
            above_binary += 1
            if c_lo != binary_trim + 1:
                failures.append(("corrected trim is not the binary64-alpha floor or one above", a, n))
            if len(above_binary_examples) < 4:
                above_binary_examples.append((a, n, c_lo, binary_trim))
        decimal_trim = math.floor(exact_decimal * n / 2)
        if c_lo != decimal_trim:
            below_decimal += 1
            if c_lo != decimal_trim - 1:
                failures.append(("corrected trim is not decimal floor or one below", a, n))
            if len(below_decimal_examples) < 6:
                below_decimal_examples.append((a, n, c_lo, decimal_trim))
print(f"  previous form: {len(alphas_with_asymmetry)} of 99 alpha values have some B with unequal "
      f"tails; {asymmetric_pairs} (alpha, B) pairs in total")
print("  first unequal B per alpha (alpha: B, dropped below, dropped above):")
for a in sorted(first):
    n, below, above = first[a]
    print(f"    {a}: B={n}, {below} below, {above} above")
print("  corrected form: unequal tails 0; lower index unchanged in every pair"
      if not failures else f"  corrected form FAILURES: {failures[:5]}")
print(f"  corrected trim is one below the decimal floor in {below_decimal} pairs "
      f"(decimal alpha*B/2 is an integer that binary64 rounds below); examples "
      f"(alpha, B, trim, decimal floor): {below_decimal_examples}")
print(f"  corrected trim is one above the exact floor for the binary64 alpha in {above_binary} "
      f"pairs (the rounded product reaches an integer); examples "
      f"(alpha, B, trim, binary64-alpha floor): {above_binary_examples}")
print(f"  pairs in which the clamp to (B-1)//2 was active: {clamp_active}")
sys.exit(1 if failures else 0)
