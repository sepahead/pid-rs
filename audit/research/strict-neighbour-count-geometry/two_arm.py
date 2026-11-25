"""Check the fixed five-row Ehrlich report against the raw integer observations."""
import argparse
from copy import deepcopy
from fractions import Fraction
import json
import math
from pathlib import Path


POINTS = ((0, 0, 0), (2, 26, 3), (33, 5, 10), (19, 27, 2), (41, 22, 7))
RANK = 2
QUANTILES = {"min": 0, "p10": 10, "median": 50, "p90": 90, "p99": 99, "max": 100}
COUNTS = {
    "source_union_count", "target_count", "source1_count", "source2_count",
    "overlap_count", "overlap_half_radius_count",
}
TOLERANCE_NATS = 1e-12
STUDY = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def harmonic(index):
    return sum((Fraction(1, j) for j in range(1, index + 1)), Fraction(0))


def summary(series):
    ordered = sorted(series)
    require(bool(ordered), "empty quantile population")
    # The native quantile index is the nearest integer, with ties rounded up.
    return {name: ordered[(2 * (len(ordered) - 1) * percent + 100) // 200]
            for name, percent in QUANTILES.items()}


def overlap_ratio(left, right):
    union_size = len(left | right)
    return Fraction(len(left & right), union_size) if union_size else Fraction(0)


def exact():
    rows = []
    values = {}
    for anchor, reference in enumerate(POINTS):
        distances = {}
        for index, neighbour in enumerate(POINTS):
            if index != anchor:
                distances[index] = tuple(abs(a - b) for a, b in zip(neighbour, reference, strict=True))
        radii = sorted(max(min(left, right), target) for left, right, target in distances.values())
        radius = radii[RANK - 1]
        require(radius > 0 and radii.count(radius) == 1, "unique positive shell")
        first = {i for i, (left, right, target) in distances.items() if left < radius}
        second = {i for i, (left, right, target) in distances.items() if right < radius}
        targets = {i for i, (left, right, target) in distances.items() if target < radius}
        half_first = {i for i, (left, right, target) in distances.items() if 2 * left < radius}
        half_second = {i for i, (left, right, target) in distances.items() if 2 * right < radius}
        x, y = 1 + len(first | second), 1 + len(targets)
        term = harmonic(RANK - 1) + harmonic(len(POINTS) - 1) - harmonic(x - 1) - harmonic(y - 1)
        rows.append({
            "row": anchor, "r": radius, "x": x, "y": y, "c1": len(first), "c2": len(second),
            "overlap": len(first & second), "first": sorted(first - second),
            "second": sorted(second - first), "term": str(term),
        })
        quantities = {
            "joint_radius": radius, "source_union_count": x, "target_count": y,
            "source1_count": len(first), "source2_count": len(second), "overlap_count": len(first & second),
            "overlap_half_radius_count": len(half_first & half_second), "overlap_ratio": overlap_ratio(first, second),
            "overlap_half_radius_ratio": overlap_ratio(half_first, half_second), "local_redundancy_nats": term,
        }
        for channel, full, half in ((1, first, half_first), (2, second, half_second)):
            if full and half:
                # The slopes for these data are log2(1) exactly.
                require(len(full) == len(half), "unexpected nonzero fixture slope")
                quantities[f"source{channel}_scaling_slope"] = 0
        for name, value in quantities.items():
            values.setdefault(name, []).append(value)
    require([item["r"] for item in rows] == [10, 3, 10, 5, 5], "all five radii")
    require((rows[0]["x"], rows[0]["y"], rows[0]["first"], rows[0]["second"], rows[0]["term"])
            == (3, 4, [1], [2], "-1/4"), "both source arms must contribute")
    mean = sum(values["local_redundancy_nats"], Fraction(0)) / len(rows)
    return rows, values, mean


def load_record(raw):
    def unique(members):
        result = dict(members)
        require(len(result) == len(members), "duplicate field")
        return result

    def invalid(token):
        raise ValueError("nonfinite JSON number " + token)

    require(len(raw) <= 65536, "report exceeds the five-row record limit")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def compare_float(observed, expected, tolerance, label):
    require(type(observed) is float and math.isfinite(observed), label + " must be finite binary64")
    require(abs(observed - float(expected)) <= tolerance, label + " value")


def compare(raw, series, mean):
    data = load_record(raw)
    require(type(data) is dict and set(data) == {"n", "k", "mean_nats", "diagnostics", "bad_support", "bad_k"},
            "report fields")
    require(type(data["n"]) is int and data["n"] == len(POINTS), "row count")
    require(type(data["k"]) is int and data["k"] == RANK, "rank")
    require(data["bad_support"] is True and data["bad_k"] is True, "typed refusal flags")
    compare_float(data["mean_nats"], mean, TOLERANCE_NATS, "mean")
    observed = data["diagnostics"]
    undefined = {f"undefined_source{i}_slopes": len(POINTS) - len(series[f"source{i}_scaling_slope"])
                 for i in (1, 2)}
    require(type(observed) is dict and set(observed) == set(series) | set(undefined), "diagnostic fields")
    for name, expected_count in undefined.items():
        require(type(observed[name]) is int and observed[name] == expected_count, name)
    for name, values in series.items():
        estimated = observed[name]
        require(type(estimated) is dict and set(estimated) == set(QUANTILES), "quantile fields for " + name)
        for quantile, expected in summary(values).items():
            field = estimated[quantile]
            label = name + "." + quantile
            if name in COUNTS:
                require(type(field) is int and field == expected, "integer " + label)
            else:
                tolerance = TOLERANCE_NATS if name == "local_redundancy_nats" else 0.0
                compare_float(field, expected, tolerance, label)


def hostile(base, series, mean):
    original = load_record(base)
    def change(path, replacement):
        value = deepcopy(original)
        member = value
        for key in path[:-1]:
            member = member[key]
        member[path[-1]] = replacement
        return json.dumps(value).encode()

    d = "diagnostics"
    proposals = [
        change(["bad_k"], "no"), change(["bad_support"], 1), change(["n"], 5.0), change(["k"], 2.0),
        change([d, "source2_count", "max"], True), change([d, "source_union_count", "median"], 3.0000000000001),
        change(["mean_nats"], -7.0), change(["mean_nats"], float("nan")),
        change([d, "local_redundancy_nats", "p90"], 1.0), change([d, "overlap_half_radius_count", "min"], 1),
        change([d, "source2_scaling_slope"], None), change([d, "overlap_ratio", "median"], False),
        change([d, "undefined_source1_slopes"], 3), change([d, "source1_count"], {"max": 1}),
        change([d, "extra"], 0), change(["extra"], True),
        b'{"mean_nats":-20,' + json.dumps(original).encode()[1:],
        json.dumps(original).replace('"max": 1,', '"max": 99, "max": 1,', 1).encode(),
    ]
    for raw in proposals:
        try:
            compare(raw, series, mean)
        except ValueError:
            continue
        raise ValueError("altered report accepted")
    return len(proposals)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?", help="JSON from the five-row native example")
    parser.add_argument("--self-test", action="store_true", help="also reject changed native reports")
    args = parser.parse_args()
    rows, series, mean = exact()
    output = {"rows": rows, "mean": str(mean)}
    if args.report is not None or args.self_test:
        raw = (args.report or STUDY / "represented-report.json").read_bytes()
        compare(raw, series, mean)
        if args.self_test:
            output["altered_reports_rejected"] = hostile(raw, series, mean)
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
