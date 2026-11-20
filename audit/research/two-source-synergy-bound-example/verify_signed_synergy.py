"""Verify the actual signed synergy change for the two fixed categorical AND tables."""
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
COUNTS_SHA256 = "9c7f4dd6701272fc498a0bb6d5fbcbb86d99fa865e2612033480ce130888d4df"
TABLES = ("reference", "changed")
CELLS = ("000", "010", "100", "111")
EXPECTED_ODDS = {
    "reference": ("1", "4/3", "4/3", "4/3"),
    "changed": ("1", "298/297", "102/101", "298/199"),
}
EXPECTED_NATS = {"reference": "0.215761554339", "changed": "0.105074106669",
                 "changed minus reference": "-0.110687447670"}
# Each tuple is a list of branches of the inclusive union for one cumulative node.
NODES = (((0,), (1,)), ((0,),), ((1,),), ((0, 1),))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def conditional_odds(table, key, branches):
    """Return exp(cumulative information) from its informative and misinformative parts."""
    event = [cell for cell in table if any(all(cell[i] == key[i] for i in group) for group in branches)]
    total = sum(table.values())
    mass = sum(table[cell] for cell in event)
    target_mass = sum(n for cell, n in table.items() if cell[2] == key[2])
    joint_mass = sum(table[cell] for cell in event if cell[2] == key[2])
    informative_ratio = Fraction(total, mass)
    misinformative_ratio = Fraction(target_mass, joint_mass)
    return informative_ratio / misinformative_ratio


def top_odds(table, key):
    redundant, first, second, joint = (conditional_odds(table, key, node) for node in NODES)
    unique_first = first / redundant
    unique_second = second / redundant
    return joint / (unique_first * unique_second * redundant)


def prime_powers(ratio, largest_count):
    """Every reduced factor comes from integer event counts of at most largest_count."""
    numerator, denominator = ratio.as_integer_ratio()
    result = {}
    for divisor in range(2, largest_count + 1):
        power = 0
        while numerator % divisor == 0:
            numerator //= divisor
            power += 1
        while denominator % divisor == 0:
            denominator //= divisor
            power -= 1
        if power:
            result[divisor] = power
    require(numerator == denominator == 1, "integer log product has an unexplained factor")
    return result


def bounded_log(ratio, total, log_interval):
    lower = upper = Fraction(0)
    powers = prime_powers(ratio, total)
    readback = Fraction(1)
    for prime, power in powers.items():
        readback *= Fraction(prime) ** power
        lo, hi = log_interval(Fraction(prime))
        a, b = sorted((power * lo, power * hi))
        lower += a
        upper += b
    require(readback == ratio, "integer log product disagrees")
    return lower / total, upper / total, powers


def verify():
    # The bound reader already supplies an exact log-series remainder, via its adjacent file.
    spec = importlib.util.spec_from_file_location("worked_bound_arithmetic", HERE / "verify_numbers.py")
    arithmetic = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arithmetic)
    raw = (HERE / "counts.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == COUNTS_SHA256, "fixed count table changed")
    rows = json.loads(raw)["rows"]
    require(tuple(row["cell"] for row in rows) == CELLS, "unexpected cell order")
    products = {}
    for side in TABLES:
        table = {row["cell"]: row[side] for row in rows}
        require(sum(table.values()) == 200, "the averaging factors require 200 counts")
        product = Fraction(1)
        for cell, expected in zip(CELLS, EXPECTED_ODDS[side], strict=True):
            factor = top_odds(table, cell)
            require(factor == Fraction(expected), f"pointwise factor disagrees for {side} {cell}")
            product *= factor ** table[cell]
        products[side] = product
    products["changed minus reference"] = products["changed"] / products["reference"]
    report = {}
    for name, product in products.items():
        lower, upper, powers = bounded_log(product, 200, arithmetic.log_interval)
        value = Fraction(EXPECTED_NATS[name])
        half_step = Fraction(1, 2 * 10**12)
        require(value - half_step < lower <= upper < value + half_step, f"rounded nats disagree for {name}")
        sign = (product > 1) - (product < 1)
        require(sign == (value > 0) - (value < 0), f"integer sign disagrees for {name}")
        report[name] = {"nats_rounded_to_12_places": EXPECTED_NATS[name], "exact_sign": sign,
                        "prime_exponents_in_exp_200_times_value": powers}
    return report


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
