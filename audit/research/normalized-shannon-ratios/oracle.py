"""Generate expected public reports for a finite set of represented binary64 summaries."""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "crates/pid-core/tests/fixtures/normalized_shannon_ratio.json"
SIGN = 1 << 63
MAXIMUM = 0x7FEFFFFFFFFFFFFF
INF = MAXIMUM + 1
DEFAULT = "3d719799812dea11"  # 1e-12, the public default denominator threshold in nats.
DEFINITIONS = {
    "redundancy": "sum_i I(T;S_i) / I(T;S_1,...,S_n)",
    "vulnerability": "sum_i (I(T;S_1,...,S_n) - I(T;S_-i)) / I(T;S_1,...,S_n)",
}


def bits(value):
    return struct.unpack(">Q", struct.pack(">d", value))[0]


def number(word):
    return struct.unpack(">d", struct.pack(">Q", word))[0]


def hexword(word):
    return f"{word:016x}"


def exact(word):
    return Fraction.from_float(number(word))


def rounded(value):
    """CPython Fraction rounds to nearest, with ties to even; encode overflow as absent."""
    try:
        return hexword(bits(float(value)))
    except OverflowError:
        return None


def binary_fraction(word):
    """Independent integer decode of a finite nonnegative binary64 word."""
    if word == 0:
        return Fraction()
    field, significand = divmod(word, 1 << 52)
    if field:
        significand += 1 << 52
    return Fraction(significand) * Fraction(2) ** (max(field, 1) - 1075)


def neighbor_round(value):
    """Bracket using ordered integer encodings and compare rational distances."""
    magnitude = abs(value)
    sign = SIGN if value < 0 else 0
    top = binary_fraction(MAXIMUM)
    if magnitude >= top + 2**970:
        return None
    if magnitude >= top:
        return hexword(MAXIMUM | sign)
    low, high = 0, MAXIMUM
    while high - low > 1:
        mid = (high + low) // 2
        if binary_fraction(mid) <= magnitude:
            low = mid
        else:
            high = mid
    step = 2 * magnitude - binary_fraction(low) - binary_fraction(high)
    chosen = high if step > 0 or (step == 0 and high % 2 == 0) else low
    return hexword(chosen | sign)


def expected(method, terms, joint, threshold, convert):
    finite_joint = (joint & ~SIGN) < INF
    outcome = {"status": "Defined", "value": None, "numerator_nats": None,
               "denominator_nats": hexword(joint) if finite_joint else None,
               "definition": DEFINITIONS[method], "unit": "Unitless",
               "minimum_denominator_nats": hexword(threshold)}
    if not terms:
        outcome["status"] = "EmptyTerms"
    elif not finite_joint or any((word & ~SIGN) >= INF for word in terms):
        outcome["status"] = "NonFiniteInput"
    elif exact(joint) <= 0:
        outcome["status"] = "NonPositiveDenominator"
    elif exact(joint) <= exact(threshold):
        outcome["status"] = "DenominatorBelowPolicyThreshold"
    else:
        d = exact(joint)
        total = sum(map(exact, terms), Fraction())
        if method == "vulnerability":
            total = len(terms) * d - total
        value = convert(total / d)
        if value is None:
            outcome["status"] = "NumericallyUnrepresentable"
        else:
            outcome["value"] = value
            outcome["numerator_nats"] = convert(total)
    return outcome


def prescriptions():
    one, two, three = map(bits, (1.0, 2.0, 3.0))
    default = int(DEFAULT, 16)
    minimum_normal = 1 << 52
    maximum_subnormal = minimum_normal - 1
    half_ulp = bits(2.0**-53)
    half_overflow = bits(2.0**970)
    huge, tiny = bits(2.0**1000), bits(2.0**-500)
    r, v = "redundancy", "vulnerability"
    cases = [
        ("r-min-over-two", r, [1, 1], two, default),
        ("r-min-over-three-halves", r, [1, 1], bits(1.5), default),
        ("r-signed-cancellation", r, [huge, SIGN | huge, tiny], one, default),
        ("r-overflowed-numerator", r, [MAXIMUM, MAXIMUM], MAXIMUM, default),
        ("r-two-roundings", r, [one, half_ulp], three, default),
        ("r-negative-two-roundings", r, [SIGN | one, SIGN | half_ulp], three, default),
        ("r-cancel-overflow", r, [MAXIMUM, MAXIMUM, SIGN | MAXIMUM, SIGN | MAXIMUM, 1], one, default),
        ("r-swapping-method-changes-value", r, [one, one], three, default),
        ("v-swapping-method-changes-value", v, [one, one], three, default),
        ("v-finite-ratio-overflowed-numerator", v, [0, 0], MAXIMUM, default),
        ("v-cancel-wide", v, [MAXIMUM, SIGN | MAXIMUM], one, default),
        ("v-three-next-down", v, [one - 1] * 3, one, default),
        ("v-mixed-neighbors", v, [one - 1, one + 1], one, default),
        ("v-neg-overflow", v, [MAXIMUM], one - (1 << 52), default),
        ("v-pos-overflow", v, [SIGN | MAXIMUM], one - (1 << 52), default),
        ("v-subnormal-leave", v, [1, 1], two, default),
        ("v-nonzero-positive-numerator-zero-value", v, [bits(4.0), SIGN | 1], two, default),
        ("v-nonzero-negative-numerator-signed-zero-value", v, [bits(4.0), 1], two, default),
        ("v-negative-finite", v, [two, three], one, default),
        ("v-min-divisor-positive", v, [0, 1], 1, 0),
        ("v-min-divisor-negative", v, [3], 1, 0),
        ("v-return-rounded-numerator", v, [one, half_ulp], three, default),
    ]
    for sign, label in ((0,"positive"),(SIGN,"negative")):
        for offset, suffix in ((-1,"above-half"),(0,"half"),(1,"below-half")):
            cases.append((f"r-{label}-{suffix}",r,[sign | 1],two+offset,default))
        for offset in (-1,0,1):
            cases.append((f"r-{label}-overflow-midpoint-{offset}",r,
                          [sign | MAXIMUM, sign | (half_overflow + offset)],two,default))
        cases.extend([
            (f"r-{label}-normal-boundary-midpoint", r,
             [sign | minimum_normal, sign | maximum_subnormal], two, default),
            (f"r-{label}-high-binade-tie", r, [sign | (two-1), sign | half_ulp], one, default),
            (f"r-{label}-zero-or-two-min", r, [sign | 3], two, default),
            (f"r-{label}-true-ratio-overflow", r, [sign | MAXIMUM], 1, 0),
        ])
    for method in (r,v):
        for label, terms, d, floor in [
            ("empty-before-nan", [], INF + 42, default), ("empty-negative", [], SIGN | one, default),
            ("nan-before-zero", [INF + 17], 0, default), ("nan-denominator", [one], SIGN | (INF + 1), default),
            ("positive-infinity", [one], INF, default), ("negative-infinity", [one], SIGN | INF, default),
            ("infinite-term", [SIGN | INF], one, default), ("negative-zero-denominator", [one], SIGN, 0),
            ("positive-zero-denominator", [one], 0, 0), ("negative-denominator", [one], SIGN | 1, 0),
            ("below-threshold", [one], default-1, default), ("at-threshold", [one], default, default),
            ("above-threshold", [one], default+1, default), ("signed-zero-policy", [SIGN,0], one, SIGN),
            ("exact-zero-sign", [SIGN,0], one, default), ("exact-zero-difference", [two,two], two, default),
        ]:
            cases.append((method[0]+"-policy-"+label,method,terms,d,floor))
    # A reproducible finite cross-section through sign, binade edges, significand parity,
    # subnormals and multiplicities; selection depends only on this fixed seed and arithmetic.
    state = 0x7F6D42A179C3B85E
    pool = [0, 1, 2, 3, maximum_subnormal, minimum_normal, minimum_normal+1,
            tiny, half_ulp, one-1, one, one+1, two, two+1, three-1, three, huge, MAXIMUM-1, MAXIMUM]
    def take():
        nonlocal state
        state = (6364136223846793005 * state + 1442695040888963407) % (1 << 64)
        return state >> 24
    for i in range(48):
        method = (r,v)[i%2]
        d = pool[1 + take() % (len(pool)-1)]
        terms = [pool[take()%len(pool)] | (SIGN if take()%2 else 0) for _ in range(1+take()%6)]
        cases.append((f"deterministic-{i:02d}",method,terms,d,0))
    return cases


def fixture(check_round=False):
    results = []
    for stem, method, terms, joint, threshold in prescriptions():
        report = expected(method, terms, joint, threshold, rounded)
        if check_round and expected(method, terms, joint, threshold, neighbor_round) != report:
            raise ValueError("integer-neighbor oracle disagrees on " + stem)
        routes = ["default", "explicit"] if hexword(threshold) == DEFAULT else ["explicit"]
        for route in routes:
            results.append({"id":stem+"-"+route, "method":method, "wrapper":route,
                            "terms":list(map(hexword,terms)), "joint":hexword(joint),
                            "threshold":hexword(threshold), "expected":report})
    if len({r["id"] for r in results}) != len(results) or len(results)>300:
        raise ValueError("invalid case roster")
    return {"schema":"normalized-shannon-ratio-v1", "rows":results}


def canonical(data):
    lines = [json.dumps(r, sort_keys=True, allow_nan=False) for r in data["rows"]]
    return ('{\n  "schema": "'+data["schema"]+'",\n  "rows": [\n    '+',\n    '.join(lines)+'\n  ]\n}\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    op = parser.add_mutually_exclusive_group(required=True)
    op.add_argument("--write", metavar="PATH", type=Path)
    op.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = fixture(check_round=True)
    raw = canonical(rows)
    if args.check:
        if FIXTURE.read_bytes() != raw:
            raise ValueError("fixture differs from exact source-generated bytes")
    else:
        with args.write.open("xb") as stream:
            stream.write(raw)
    print(f"Verified {len(rows['rows'])} rows with Fraction and integer-neighbor rounding.")


if __name__ == "__main__":
    main()
