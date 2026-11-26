"""Compare ten named Rust floats against the copied-force exact products."""
import argparse
import hashlib
import json
import math
import re
import struct
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ARCHIVE = "cdfbe0b260f4a21c5249fe0da4b1baf4041959663a9182253885ee1f41a4568e"
MEMBER = "f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c"
DIRECT = "4b05b519d580f03c4ab7c0ff73523a2e085793b1a0861d9a54f99ebf1edd13ad"
CELLS = {(0, 0): 52, (0, 1): 25, (1, 0): 23, (1, 1): 17}
FACTORS = {52: Fraction(231, 208), 25: Fraction(1617, 1175),
           23: Fraction(750, 529), 17: Fraction(336, 221)}
FIVE = ((4,), (5,), (6,), (5, 6), (7,))
TOL = Fraction(1, 10**12)


def need(condition, msg):
    if not condition:
        raise ValueError(msg)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_load(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON token " + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def rows_from_original(path):
    need(digest(path.read_bytes()) == ARCHIVE, "original UCI archive")
    with ZipFile(path) as z:
        members = [s for s in z.namelist() if Path(s).name == "lp4.data"]
        need(len(members) == 1, "unique original LP4 member")
        raw = z.read(members[0])
    need(digest(raw) == MEMBER and len(raw) == 33619, "original LP4 bytes")
    tokens = [line.split() for line in raw.splitlines() if line.strip()]
    need(len(tokens) == 117 * 16, "117 labelled episodes")
    rows = []
    for pos in range(0, len(tokens), 16):
        need(tokens[pos] in ([b"normal"], [b"collision"], [b"obstruction"]), "original class line")
        values = tokens[pos + 1:pos + 16]
        need(all(len(v) == 6 for v in values), "six recorded channels")
        def encode(column):
            values_by_time = [int(line[column]) for line in values]
            difference = sum(i * (values_by_time[7+i] - values_by_time[7-i]) for i in range(1, 8))
            need(difference != 0, "binary nonzero slope on the fixed input")
            return int(difference > 0)
        force, torque = encode(2), encode(5)
        rows.append([force, 0, torque, force])
    need(Counter((r[0], r[2]) for r in rows) == CELLS, "source identities and joint multiplicities")
    return rows


def below(first, second):
    return all(any((i & j) == i for i in first) for j in second)


def registry():
    return {masks for count in range(1, 8) for masks in combinations(range(1, 8), count)
            if all((i & j) not in (i, j) for i, j in combinations(masks, 2))}


def wb_coefficients(rules):
    # A source group that contains force copies the target. A torque-only group
    # has specific information between zero and the target's own surprisal.
    order = sorted(rules, key=lambda a: sum(below(b, a) for b in rules))
    atoms = {}
    for a in order:
        grade = min(2 if m & 1 else 1 if m & 4 else 0 for m in a)
        pair = (int(grade == 2), int(grade == 1))
        atoms[a] = tuple(pair[i] - sum(value[i] for b, value in atoms.items() if below(b, a))
                         for i in range(2))
    need(all(atoms[a] == (0, 0) for a in FIVE), "Williams–Beer zero coefficients")
    return atoms


def log_interval(ratio):
    # Bound ln(r) by the positive atanh series plus a geometric tail.
    z = (ratio - 1) / (ratio + 1)
    need(0 <= z < 1, "positive-series domain")
    stop = 32
    lower = 2 * sum((z**(2*i + 1) / (2*i + 1) for i in range(stop)), Fraction())
    return lower, lower + 2 * z**(2*stop+1) / ((2*stop+1) * (1-z*z))


def decimal(q):
    with localcontext() as ctx:
        ctx.prec = 45
        return str(Decimal(q.numerator) / Decimal(q.denominator))


def key(masks):
    return "+".join(f"{m:02x}" for m in masks)


def reference():
    original = (HERE / "direct-oracle.json").read_bytes()
    need(digest(original) == DIRECT, "frozen exact all-108 reference")
    q = math.prod(r**n for n, r in FACTORS.items())
    products = dict(zip(FIVE, (1/q, q, Fraction(1), Fraction(1), Fraction(1)), strict=True))
    direct = strict_load(original)["scientific_result"]["five_signed_products"]
    need({key(a): str(v) for a, v in products.items()} == direct, "direct inversion vs cell products")
    li = [sum(n * log_interval(r)[i] for n, r in FACTORS.items()) / 117 for i in range(2)]
    bounds = {a: (Fraction(), Fraction()) for a in FIVE}
    bounds[(5,)] = tuple(li)
    bounds[(4,)] = (-li[1], -li[0])
    return products, bounds


def observe(word):
    need(isinstance(word, str) and re.fullmatch("[a-f0-9]{16}", word), "binary64 hexadecimal word")
    floating = struct.unpack(">d", bytes.fromhex(word))[0]
    need(math.isfinite(floating), "nonfinite native value")
    return Fraction.from_float(floating)


def validate_rows(rows, original):
    need(isinstance(rows, list) and all(isinstance(row, list) and len(row) == 4
         and all(type(x) is int for x in row) for row in rows) and rows == original,
         "117 original episode identities, signed labels and source order")


def compare(native):
    rules = registry()
    need(len(rules) == 18 and set(native) == {"mgw", "imin"}, "two methods and 18 rules")
    wb_coefficients(rules)
    products, bounds = reference()
    outputs = []
    for method in ("mgw", "imin"):
        report = native[method]
        need(report["cardinalities"] == [2, 1, 2, 2] and report["support"] == 4
             and report["encoding"] == "Categorical" and report["sample_count"] == 117, "empirical report identity")
        if method == "mgw":
            need(report["pointwise_included"] is False and report["pointwise_len"] == 0, "averaged-only API")
        values = {}
        for atom in report["atoms"]:
            masks = atom["masks"]
            need(isinstance(masks, list) and all(type(m) is int for m in masks), "actual integer source masks")
            name = tuple(sorted(masks))
            need(name in rules and name not in values, "unique labelled public atom")
            channels = ("informative", "misinformative", "signed") if method == "mgw" else ("imin",)
            for channel in channels:
                observe(atom[channel])
            values[name] = atom["signed" if method == "mgw" else "imin"]
        need(set(values) == rules, "all 18 source rules")
        for a in FIVE:
            x = observe(values[a])
            lo, hi = bounds[a] if method == "mgw" else (Fraction(), Fraction())
            need(hi - lo < Fraction(1, 10**43), "reference interval width")
            error = max(abs(x-lo), abs(x-hi))
            need(error <= TOL, "wrong native value or mask " + method + "/" + key(a))
            if hi < 0 or lo > 0:
                need(x * (lo + hi) > 0, "native sign")
            outputs.append({"method":method, "masks":list(a), "label":key(a), "binary64_word":values[a],
                "float_exact_fraction":str(x), "observed_nats":decimal(x),
                "reference_product":str(products[a]) if method == "mgw" else "1",
                "reference_nats_approx":decimal((lo+hi)/2), "nominal_zero":lo == hi == 0,
                "error_nats_approx":decimal(error), "exact_error_interval_maximum":str(error)})
    return {"observations":117, "source_columns":["force", "constant", "torque", "force"],
            "binary_coding":{"negative":0,"positive":1}, "units":"nats",
            "absolute_tolerance":"1/1000000000000", "measurements":outputs}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive", type=Path)
    p.add_argument("--rows", type=Path)
    p.add_argument("--native", type=Path)
    args = p.parse_args()
    original = rows_from_original(args.archive)
    if not args.native:
        print(json.dumps(original, separators=(",", ":")))
        return
    need(args.rows is not None, "actual native input required")
    validate_rows(strict_load(args.rows.read_bytes()), original)
    print(json.dumps(compare(strict_load(args.native.read_bytes())), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
