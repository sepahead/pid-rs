"""Widths in output-grid units for the original signed rational logarithm routine.

Run with the path of the original arithmetic.py as the sole argument.
"""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import runpy
import sys


SOURCE = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"
GUARD = 1 << 24
BUDGET = 262144
MOST_POWER = BUDGET - 4
MOST_EXPONENT = BUDGET - 3


def check(predicate, message):
    if not predicate:
        raise ValueError(message)


def up(n, d):
    q, r = divmod(n, d)
    return q + int(r != 0)


def fixed_log_two(bits):
    """Independent implementation with quotient/remainder directed division."""
    s = 1 << bits
    lo, hi = s // 3, up(s, 3)
    step_lo, step_hi = lo * lo // s, up(hi * hi, s)
    lower, upper = 0, 1
    for j in range(up(bits, 3) + 1):
        r = 2 * j + 1
        check(hi - lo in (0, 1, 2), "paired powers")
        term_lo, term_hi = (2 * lo) // r, up(2 * hi, r)
        check(0 <= term_hi - term_lo <= 2, "paired terms")
        lower += term_lo
        upper += term_hi
        lo, hi = lo * step_lo // s, up(hi * step_hi, s)
    return lower, upper


def size(plan):
    return 2 + sum(abs(c) * (f.numerator.bit_length() + f.denominator.bit_length())
                   for f, c in plan.items())


def exponent(q):
    k = q.numerator.bit_length() - q.denominator.bit_length()
    power = Fraction(1 << k, 1) if k >= 0 else Fraction(1, 1 << -k)
    return k - int(q < power)


def width(record, q, n, p):
    lo, hi = record(q, n, p)
    endpoints = (lo * (1 << p), hi * (1 << p))
    check(all(x.denominator == 1 for x in endpoints), "final integer grid")
    return int(endpoints[1] - endpoints[0])


def residue_width(lower, upper, divisor):
    return up(lower % divisor + upper - lower, divisor)


def witness_exponent(lo, hi, n, expected):
    divisor = n * GUARD
    for k in range(MOST_POWER, 0, -1):
        if residue_width(k * lo, k * hi, divisor) == expected:
            return k
    raise ValueError("power witness not found")


def accepted_single_plan(original, plan):
    check(size(plan) <= BUDGET, "scalar bit budget")
    # The remaining 107 plans are empty solely to exercise the original plan checker.
    plans = [("synthetic-coordinate", plan)] + [(i, {}) for i in range(107)]
    _, _, checked_size, _ = original["preflight"](plans)
    check(checked_size == size(plan), "original coordinate preflight")


def run(path):
    check(sha256(path.read_bytes()).hexdigest() == SOURCE, "unchanged source identity")
    original = runpy.run_path(str(path))
    schedule = (256, 384, 512, 768, 1024, 1536, 2048)
    check(schedule == original["SCHEDULE"], "precision schedule")
    ix = original["log_interval"]
    scalar = original["atanh_log_bounds"]
    keys, zeta, mu = original["lattice"]()
    norms = [sum(abs(v) for v in row) for row in mu]
    check(len(keys) == len(norms) == 18, "original finite lattice")
    for i in range(18):
        for j in range(18):
            check(sum(mu[i][k] * zeta[k][j] for k in range(18)) == int(i == j),
                  "right inverse")
            check(sum(zeta[i][k] * mu[k][j] for k in range(18)) == int(i == j),
                  "left inverse")
    maximum_norm = max(norms)
    threshold_witness = Fraction((1 << 2080) - 1, 1 << 2080)
    accepted_single_plan(original, {threshold_witness: 1})
    extreme_integer = Fraction((1 << MOST_EXPONENT) - 1)
    check(exponent(extreme_integer) == MOST_EXPONENT - 1, "upper exponent endpoint")
    check(exponent(1 / extreme_integer) == -MOST_EXPONENT, "lower exponent endpoint")
    accepted_single_plan(original, {extreme_integer: -1})
    # Mixed signed and cancelling plans, and the empty product.
    small_plans = [
        {}, {Fraction(2): 1, Fraction(3): 1, Fraction(6): -1},
        {Fraction(3, 2): 2, Fraction(5, 4): -3},
        {Fraction(3, 2): -2, Fraction(5, 4): 3},
    ]
    records = []
    for p in schedule:
        bits = p + 24
        terms = up(bits, 3) + 1
        lo, hi = fixed_log_two(bits)
        check((lo, hi) == original["log_two"](bits) == scalar(1, 3, bits),
              "fixed log-two measured by both implementations")
        constant = hi - lo
        check(0 < constant <= 2 * terms + 1 < GUARD, "helper width and final divisor")
        maximum_internal = MOST_EXPONENT * constant + 2 * terms + 1
        first_two = up(maximum_internal - 1, GUARD)
        examples = []
        for n in range(1, first_two):
            cap = 1 + up(maximum_internal - 1, n * GUARD)
            check(cap > 2, "finite search required")
            k = witness_exponent(lo, hi, n, cap)
            power = Fraction(1 << k)
            accepted_single_plan(original, {power: 1})
            accepted_single_plan(original, {power: -1})
            check(width(ix, power, n, p) == width(ix, 1 / power, n, p) == cap,
                  "both signs attain the proven scalar cap")
            # For a true input table these small totals have a separate projection bound.
            empirical_e = maximum_norm * n * (n - 1).bit_length() + 1
            check(empirical_e * constant + 2 * terms < n * GUARD,
                  "positive-total bound for the finite empirical projection")
            examples.append({"total": n, "sharp_width": cap, "plus_or_minus_power": k})
        for n in (1, first_two, first_two + 1, 10000, 1 << 8191):
            check(ix(threshold_witness, n, p) ==
                  (Fraction(-1, 1 << p), Fraction(1, 1 << p)),
                  "common near-one witness at every total")
        T = 1 << 2080
        check(Fraction(4 << bits, 3 * (3 * T - 2)) < Fraction(1, 3),
              "all-N mantissa has the same two starting integers as log two")
        check(ix(Fraction(1), 1, p) == ix(Fraction(1), 1 << 8191, p) == (0, 0),
              "unit returns exact zero")
        for plan in small_plans:
            q = original["exact_product"](plan)
            for n in (1, first_two):
                w = width(ix, q, n, p)
                check((w == 0) if q == 1 else (1 <= w <= 2),
                      "empty, cancelling and mixed signs")
        negative_edge = width(ix, 1 / extreme_integer, 1, p)
        positive_edge = width(ix, extreme_integer, 1, p)
        cap = 1 + up(maximum_internal - 1, GUARD)
        check(positive_edge <= cap and negative_edge <= cap,
              "extreme non-power rational factors")
        constants_bytes = ("%d,%d\n" % (lo, hi)).encode("ascii")
        records.append({"precision": p, "internal_bits": bits, "terms": terms,
                        "log_two_width": constant, "log_two_pair_sha256": sha256(constants_bytes).hexdigest(),
                        "range_width_bound": 2 * terms + 1, "sharp_all_positive_totals": cap,
                        "exact_width_two_for_every_total_from": first_two,
                        "exceptional_totals_witnessed_both_signs": examples,
                        "nonpower_extreme_grid_widths_positive_and_negative_log": [positive_edge, negative_edge]})
    return {"source_sha256": SOURCE, "units": "multiples of 2^(-p) in the final endpoints",
            "scalar_premises": "N is a positive integer independent of the reduced positive product; sum of factor bit-length costs plus two <= 262144",
            "small_total_example": "each listed 2^k and 2^-k realizes the bound at that point",
            "all_larger_totals_example": "(2^2080-1)/2^2080 returns [-2^-p,+2^-p] for every N",
            "every_precision_empirical_bound": 2,
            "empirical_qualification": "original 18-node projected products of a nonempty integer count table under the source bit budget; width <=2, N=1 gives zero; no sharpness or inclusion in a producer enclosure follows",
            "mobius_row_absolute_sums_in_original_order": norms, "maximum_mobius_row_norm": maximum_norm,
            "coordinate_cost_max": BUDGET, "proof_bound_on_e": [-MOST_EXPONENT, MOST_EXPONENT-1],
            "records": records}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])), indent=2, sort_keys=True))
