"""Read the unchanged public scalar procedure using a separately summed real series."""
from fractions import Fraction
from functools import cache
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import ModuleType


SOURCE = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"


def require(test, message):
    if not test:
        raise ValueError(message)


def original(path):
    data = Path(path).read_bytes()
    require(sha256(data).hexdigest() == SOURCE, "original source")
    module = ModuleType("original_log_arithmetic")
    exec(compile(data, "original-log-arithmetic.py", "exec"), module.__dict__)
    return module


@cache
def reference(q, terms):
    t = (q - 1) / (q + 1)
    x = abs(t)
    square = x * x
    power = x
    total = Fraction()
    for index in range(terms):
        total += 2 * power / (2 * index + 1)
        power *= square
    upper = total + 2 * power / ((2 * terms + 1) * (1 - square))
    return (total, upper) if t >= 0 else (-upper, -total)


def printed_bounds(bounds, precision):
    a, b = (bound * 2**precision for bound in bounds)
    require(a.denominator == b.denominator == 1, "dyadic grid")
    return [str(a.numerator), str(b.numerator)]


def run(path):
    model = original(path)
    selected = [(1, 1, 1), (2, 1, 1), (1, 2, 1), (1, 2, 3), (3, 2, 1),
                (3, 4, 1), (9, 16, 3), (27, 4, 3), (7, 15, 5), (4, 3, 2),
                (2, 1, 7), (1, 8, 3)]
    cases = []
    controls = []
    for a, b, n in selected:
        q = Fraction(a, b)
        lo_ref, hi_ref = (value/n for value in reference(q, 700))
        for precision in (256, 384):
            pair = model.log_interval(q, n, precision)
            require(pair[0] <= lo_ref <= hi_ref <= pair[1], ("reference", a, b, n, precision))
            if q == 1:
                require(pair == (0, 0), "equal to one")
            cases.append(dict(q=[a, b], n=n, precision=precision,
                              integer_endpoints=printed_bounds(pair, precision)))
    lo_log2, hi_log2 = reference(Fraction(2), 700)
    for precision in (256, 384):
        scale = 2 ** (precision + 24)
        l2, u2 = model.log_two(precision + 24)
        require(l2 <= scale*lo_log2 <= scale*hi_log2 <= u2, "diagonal inner enclosure")
        wrong = Fraction(-l2, scale)
        require(wrong > -lo_log2, "unreversed internal interval unexpectedly valid")
        controls.append(["negative_sign_reversal", precision])
        divisor = 3 * 2**24
        wrong = Fraction(-(u2//divisor), 2**precision)
        require(wrong > -lo_log2/3, "truncation unexpectedly gave a valid negative lower bound")
        controls.append(["signed_floor", precision])
        require(Fraction(u2, scale) > hi_log2/7, "omitting division retained lower bound")
        controls.append(["division_by_count", precision])
    tiny = Fraction(1, 2**2048)
    direct_lo, direct_hi = reference(1 + tiny, 2)
    require(0 < direct_lo <= direct_hi < tiny, "strict true range near one")
    near_one = []
    for precision in model.SCHEDULE:
        pair = model.log_interval(1 + tiny, 1, precision)
        require(pair[0] <= direct_lo <= direct_hi <= pair[1], "near-one direct reference")
        require(pair[0] == 0 and pair[1] > tiny, "expected producer containment refusal")
        near_one.append([precision, printed_bounds(pair, precision)])
    for a, n, p in [(0, 1, 256), (-1, 1, 256), (1, 0, 256), (1, 1, 255)]:
        try:
            model.log_interval(Fraction(a), n, p)
        except model.ArithmeticReject as error:
            require(str(error) == "log-domain", "wrong refusal")
        else:
            raise ValueError(("accepted invalid input", a, n, p))
    return dict(source=SOURCE, direct_series_counts=[700, 2], ordinary=cases,
                diagonal_checks=2, altered_inequalities=controls, domain_refusals=4,
                near_one_original_producer_refused=near_one)


if __name__ == "__main__":
    print(json.dumps(run(sys.argv[1]), sort_keys=True, separators=(",", ":")))
