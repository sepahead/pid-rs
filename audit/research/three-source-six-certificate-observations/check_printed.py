"""Check the six printed input tables, the node list and the exact endpoint rule."""
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
GRID = 2**164


def require(condition, description):
    if not condition:
        raise ValueError(description)


def panel_reader():
    source = (HERE / "check.py").read_bytes()
    require(sha256(source).hexdigest() == "9a6c3746937fa0db7ceaf1fc96a6753ce547948412133690778309781e60d1d6",
            "six-table reader identity")
    path = str(HERE / "check.py")
    namespace = {"__file__": path, "__name__": "six_table_reader"}
    exec(compile(source, path, "exec"), namespace)
    return namespace


def printed_tables(text):
    tables = {}
    for name in ("negative", "unit", "weighted"):
        lines = [line for line in text.splitlines() if line.startswith("| " + name.title() + " |")]
        require(len(lines) == 1, "printed base table " + name)
        literal = lines[0].split("|")[2]
        pairs = re.findall(r"\(([01]{4}),([1-9][0-9]*)\)", literal)
        require(pairs and len(pairs) == literal.count("("), "complete printed pairs")
        tables[name] = [(tuple(row), int(count)) for row, count in pairs]
    tables["relabel_negative"] = [
        (tuple(prefix + label for prefix, label in zip("ABCT", row)), count)
        for row, count in tables["negative"]
    ]
    tables["permute_negative"] = [
        ((row[1], row[2], row[0], row[3]), count) for row, count in tables["negative"]
    ]
    tables["replicate_unit"] = [(row, 2 * count) for row, count in tables["unit"]]
    return tables


def printed_keys(text):
    result = []
    for group in ("One", "Two", "Three"):
        lines = [line for line in text.splitlines() if line.startswith("| " + group + " |")]
        require(len(lines) == 1, "printed node group")
        result.extend(re.findall(r"`([0-9]{2}(?:\+[0-9]{2})*)`", lines[0]))
    require(len(set(result)) == len(result) == 18, "distinct printed keys")
    return result


@lru_cache(maxsize=64)
def unit_log_bounds(ratio):
    """Exact lower and upper bounds for ln(ratio), for ratios from one to two."""
    require(1 <= ratio <= 2, "reduced logarithm argument")
    t = (ratio - 1) / (ratio + 1)
    power = t
    lower = Fraction(0)
    for index in range(110):
        lower += 2 * power / (2 * index + 1)
        power *= t * t
    upper = lower + 2 * power / (221 * (1 - t*t))
    return lower, upper


@lru_cache(maxsize=64)
def grid_floor(product, total):
    ratio = product
    exponent = 0
    while ratio >= 2:
        ratio /= 2
        exponent += 1
    while ratio < 1:
        ratio *= 2
        exponent -= 1
    lower, upper = unit_log_bounds(ratio)
    lo2, hi2 = unit_log_bounds(Fraction(2))
    if exponent < 0:
        lo2, hi2 = hi2, lo2
    left = (lower + exponent * lo2) * GRID // total
    right = (upper + exponent * hi2) * GRID // total
    require(left == right, "one floor proved by rational bounds")
    return left


def run():
    text = (HERE / "README.md").read_text(encoding="utf-8")
    tables = printed_tables(text)
    keys = printed_keys(text)
    printed_floor = re.search(r"j=(-[0-9\\,]+)\s*\.", text)
    require(printed_floor is not None, "printed negative example")
    integer_text = printed_floor.group(1).replace(r"\,", "")
    require(int(integer_text) == grid_floor(Fraction(9, 16), 3), "printed example grid integer")
    reader = panel_reader()
    cases, _ = reader["run_panel"]()
    require(set(tables) == set(cases), "six fixed tables")
    zero_count = 0
    nonzero_count = 0
    for name, (rows, total, observations, _) in cases.items():
        typed = [(tuple((label,) for label in row), count) for row, count in tables[name]]
        require(sorted(typed) == list(rows), "printed table " + name)
        for offset, row in enumerate(observations):
            require(row["key"] == keys[offset % 18], "printed order")
            require(row["precision_bits"] == 256, "first precision")
            product = Fraction(int(row["numerator"]), int(row["denominator"]))
            lo = reader["endpoint"](row["producer_lower"])
            hi = reader["endpoint"](row["producer_upper"])
            if product == 1:
                require(lo == hi == 0, "zero interval")
                zero_count += 1
            else:
                index = grid_floor(product, total)
                require((lo, hi) == (Fraction(index - 1, GRID), Fraction(index + 2, GRID)),
                        "exact printed interval")
                nonzero_count += 1
    require((zero_count, nonzero_count) == (392, 256), "covered original intervals")
    return {"tables": len(cases), "keys": len(keys), "zero_intervals": zero_count,
            "three_tick_intervals": nonzero_count, "grid_bits": 164, "first_precision_bits": 256}


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True, separators=(",", ":")))
