"""Check nine-decimal loss gains against the original integer office counts."""
from fractions import Fraction
from hashlib import sha256
import json
from math import ceil, floor
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SCALE = 10**9


def require(ok, message):
    if not ok:
        raise ValueError(message)


def rounded_integer(low, high):
    lo, hi = round(SCALE * low), round(SCALE * high)
    require(lo == hi, "the bounds do not determine the nine-place rounding")
    return lo


def displayed(integer):
    whole, fraction = divmod(abs(integer), SCALE)
    return f"{'-' if integer < 0 else ''}{whole}.{fraction:09d}"


def log_mean(table, train, log_interval, marginal):
    """Return outward bounds on the mean log ratio q_pair / q_light in nats."""
    light = marginal(train, (0,))
    light_target = marginal(train, (0, 2))
    pair = marginal(train, (0, 1))
    total = sum(table.values())
    low = high = Fraction(0)
    for (a, b, y), rows in sorted(table.items()):
        baseline = Fraction(light_target.get((a, y), 0) + 1, light.get((a,), 0) + 2)
        augmented = Fraction(train.get((a, b, y), 0) + 1, pair.get((a, b), 0) + 2)
        lo, hi = log_interval(augmented / baseline, 1, 256)
        weight = Fraction(rows, total)
        low += weight * lo
        high += weight * hi
    return low, high


def main():
    existing = runpy.run_path(str(HERE / "calculate.py"))
    arithmetic = ROOT / "audit/research/signed-log-certificate-enclosure/grid/fixed/arithmetic.py"
    interval = runpy.run_path(str(arithmetic))["log_interval"]
    path = HERE.parent / "real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json"
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == existing["INPUT_SHA"], "original count-table bytes")
    records = json.loads(raw)["files"]
    roster = existing["EXPECTED_ROWS"]
    require(set(records) == set(roster), "all three recordings")
    tables = {key: existing["counts"](records[key], n) for key, n in roster.items()}
    expected = {"datatraining.txt": 4636960, "datatest.txt": 8028892, "datatest2.txt": -3318968}
    require(set(tables) == set(expected), "fixed nine-decimal values")
    train = tables["datatraining.txt"]
    results = {}
    for key, table in tables.items():
        lo, hi = log_mean(table, train, interval, existing["marginal"])
        rounded = rounded_integer(lo, hi)
        require(rounded == expected[key], key + " gain")
        precision = 10**16
        results[key] = {
            "rows": sum(table.values()),
            "occupied_cells": len(table),
            "lower_units_of_1e-16_nats_per_row": floor(lo * precision),
            "upper_units_of_1e-16_nats_per_row": ceil(hi * precision),
            "rounded_gain_nats_per_row": displayed(rounded),
        }
    printed_sum = Fraction("0.001558012") + Fraction("0.014359564") - Fraction("0.019236545")
    require(printed_sum == Fraction("0.001558012") - Fraction("0.004876981") == Fraction("-0.003318969"),
            "exact subtraction of the displayed decimals")
    later = results["datatest2.txt"]["rounded_gain_nats_per_row"]
    require(printed_sum != Fraction(later), "rounding the inputs and rounding the final result give different answers")
    print(json.dumps({"units": "nats per recorded observation", "count_input_sha256": existing["INPUT_SHA"],
                      "rounded_inputs_sum": "-0.003318969", "records": results}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
