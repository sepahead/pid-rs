"""Reproduce the two scalar schedule examples and the six-table precision count."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def load_reader():
    path = Path(__file__).with_name("check.py")
    source = path.read_bytes()
    require(sha256(source).hexdigest() == "9a6c3746937fa0db7ceaf1fc96a6753ce547948412133690778309781e60d1d6",
            "six-table reader source differs")
    reader = {"__name__": "six_table_reader", "__file__": str(path)}
    exec(compile(source, str(path), "exec"), reader)
    return reader


def scalar_example(reader, k):
    arithmetic = reader["A"]
    x = Fraction(1, 2**k)
    endpoint = reader["endpoint"]
    require(endpoint({"coefficient": "0", "exponent": 0}) == 0, "canonical zero")
    try:
        upper = endpoint({"coefficient": "1", "exponent": -k})
    except reader["Refusal"] as error:
        require(k == 4096 and str(error) == "panel dyadic representation", "unexpected refusal")
        admitted = False
    else:
        require(k == 2048 and upper == x, "unexpected upper endpoint")
        admitted = True

    numerators = []
    for p in arithmetic.SCHEDULE:
        lo, hi = arithmetic.log_interval(1 + x, 1, p)
        numerator = 2 if p == k else 1
        require(lo == 0 and hi == Fraction(numerator, 2**p) and x < hi, "schedule result")
        numerators.append(numerator)
    final = arithmetic.atanh_log_bounds(1, 2**(k + 1) + 1, 2048 + 24)
    expected = (2**24 - 2, 2**24 + 692) if k == 2048 else (0, 694)
    require(final == expected, "final series bounds with tail")
    return {"k": k, "panel_upper_admitted": admitted, "upper_numerators": numerators,
            "p2048_series_with_tail": final}


def run():
    reader = load_reader()
    cases, _ = reader["run_panel"]()
    frequencies = Counter(row["precision_bits"] for _, _, rows, _ in cases.values() for row in rows)
    require(frequencies == {256: 648}, "six-table precision count")
    examples = [scalar_example(reader, k) for k in (2048, 4096)]
    return {"empirical_precision_counts": dict(frequencies), "precisions": reader["A"].SCHEDULE,
            "scalar_total": 1, "scalar_lower_numerator": 0, "scalar_examples": examples}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
