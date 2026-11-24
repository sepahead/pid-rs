"""Check the identity and labels of the complete, recorded UCI 138 sensor arrays."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from calculation import read_events
from replay import canonical, read_members, sha


AXES = ("Fx", "Fy", "Fz", "Tx", "Ty", "Tz")
SOURCE_SHA = "34e112b870fc01f6c45857924f79d3e351504e64a3f46711a411899aa7d5b9a8"
PUBLISHED = HERE / "trace-provenance.json"
# This digest binds the published record definition, source attribution, scope and archive identities.
# The two numerical fields are recomputed from the five original data files.
METADATA_SHA = "d957faf0f9fd5f78bc90743001c97919959da34532d165c4841e6ad054a8c54b"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_record(raw):
    """Require unambiguous field names and integer syntax for every JSON number."""
    def distinct(items):
        fields = dict(items)
        require(len(fields) == len(items), "duplicate field in trace record")
        return fields

    def reject_number(token):
        raise ValueError(f"expected an integer in the trace record, found {token}")

    result = json.loads(raw.decode("utf-8"), object_pairs_hook=distinct,
                        parse_float=reject_number, parse_constant=reject_number)
    require(isinstance(result, dict), "expected a JSON object for the trace record")
    return result


def check_record(raw, matches, informative):
    """Bind the documentary fields separately from the two recomputed results."""
    record = read_record(raw)
    metadata = {key: value for key, value in record.items()
                if key not in ("measurement_results", "informative_redundancy")}
    require(sha(canonical(metadata)) == METADATA_SHA,
            "published source attribution, definition or scope differs")
    # JSON booleans and integers denote different things even when Python compares them equal.
    require(canonical(record.get("measurement_results")) == canonical(matches) and
            canonical(record.get("informative_redundancy")) == canonical(informative),
            "published trace or source-marginal results differ")


def measurements(data, meta):
    """Keep the donor label and the 90 integers in their original sample and axis order."""
    lines = [line.strip() for line in data.decode("ascii").splitlines() if line.strip()]
    require(len(lines) == 16 * meta["n"], "expected one label and 15 rows per recording")
    rows = []
    for start in range(0, len(lines), 16):
        label = lines[start]
        require(label in meta["labels"], "unrecognized donor label")
        values = []
        for line in lines[start + 1:start + 16]:
            words = line.split()
            require(len(words) == 6 and all(re.fullmatch(r"[+-]?[0-9]+", word) for word in words),
                    "expected six signed integers in each sample")
            values.extend(map(int, words))
        rows.append((tuple(values), label))
    return rows


def within_task(rows):
    groups = defaultdict(list)
    for ordinal, (trace, label) in enumerate(rows, 1):
        groups[trace].append((ordinal, label))
    repeated = []
    best = 0
    for entries in groups.values():
        counts = Counter(label for _, label in entries)
        best += max(counts.values())
        if len(entries) > 1:
            repeated.append({"rows": [i for i, _ in entries], "labels": [label for _, label in entries]})
    return {"rows": len(rows), "distinct_arrays": len(groups), "repeated_arrays": repeated,
            "max_correct_using_full_array_on_this_table": best}


def compare_record_order(left, right):
    """Return one-based positions and changed cells for the registered concatenation."""
    require(len(left) == len(right), "ordered comparison requires the same row count")
    mismatches = []
    for ordinal, (a, b) in enumerate(zip(left, right, strict=True), 1):
        require(len(a) == len(b) == 90, "expected complete arrays")
        changed = [{"sample": k//6 + 1, "channel": AXES[k%6], "left": u, "right": v}
                   for k, (u, v) in enumerate(zip(a, b, strict=True)) if u != v]
        if changed:
            mismatches.append({"row": ordinal, "changed_cells": changed})
    return {"compared": len(left), "same": len(left) - len(mismatches), "different": mismatches}


def comparison(rows):
    ordered = {name: [trace for trace, _ in data] for name, data in rows.items()}
    bags = {name: Counter(values) for name, values in ordered.items()}
    pairs = {}
    for first, second in combinations(rows, 2):
        shared = bags[first] & bags[second]
        pairs[first + "/" + second] = {"distinct_arrays": len(shared), "with_multiplicity": sum(shared.values())}
    all_arrays = set().union(*bags.values())
    return {"tasks": {name: within_task(data) for name, data in rows.items()}, "task_pairs": pairs,
            "all_task_rows": sum(map(len, ordered.values())), "all_distinct_arrays": len(all_arrays),
            "LP2_and_LP3_same_arrays_in_same_order": ordered["LP2"] == ordered["LP3"],
            "LP2_then_LP4_compared_with_LP5": compare_record_order(ordered["LP2"] + ordered["LP4"], ordered["LP5"])}


def informative_factors(events):
    """Count the same categorical source disjunction for every occupied sign pair."""
    joint = Counter((f, q) for f, q, _ in events)
    force = Counter(f for f, _, _ in events)
    torque = Counter(q for _, q, _ in events)
    n = len(events)
    result = []
    product = Fraction(1)
    for (f, q), count in sorted(joint.items()):
        union = force[f] + torque[q] - count
        require(0 < count <= union <= n, "occupied category and source-event size")
        result.append({"sign_pair": [f, q], "count": count, "union": union})
        product *= Fraction(n, union) ** count
    return {"records": n, "terms": result, "exp_n_times_informative_redundancy":
            {"numerator": str(product.numerator), "denominator": str(product.denominator)}}


def source_marginal_comparison(members):
    factors = {}
    for task, data in members:
        if task["id"] in ("LP2", "LP3"):
            events = read_events(data, task["labels"], task["n"])
            factors[task["id"]] = informative_factors(events)
    return factors


def self_test():
    a, b = tuple(range(90)), (0,) * 90
    duplicate = within_task([(a, "tool"), (a, "part"), (b, "tool")])
    require(duplicate["distinct_arrays"] == 2 and duplicate["max_correct_using_full_array_on_this_table"] == 2,
            "a conflicting label for the same input costs a correct decision")
    require(duplicate["repeated_arrays"] == [{"rows": [1, 2], "labels": ["tool", "part"]}], "one-based rows")
    changed = list(a)
    changed[68] = -777
    one = compare_record_order([a], [tuple(changed)])
    require(one["different"] == [{"row": 1, "changed_cells": [{"sample": 12, "channel": "Fz",
                                                               "left": 68, "right": -777}]}], "sample and axis")
    require(compare_record_order([a, b], [b, a])["same"] == 0, "preserve measurement order")
    groups = {"LP1": [(b, "a")], "LP2": [(a, "x"), (a, "x")], "LP3": [(a, "q"), (a, "q")],
              "LP4": [(b, "y")], "LP5": [(a, "o"), (a, "z"), (b, "w")]}
    fixture = comparison(groups)
    require(fixture["task_pairs"]["LP2/LP5"] == {"distinct_arrays": 1, "with_multiplicity": 2},
            "use multiplicity in intersections independently of task labels")
    require(fixture["all_distinct_arrays"] == 2 and fixture["all_task_rows"] == 9, "unique arrays and labeled rows")
    square = informative_factors([(-1, -1, "a"), (-1, 1, "b"), (1, -1, "b"), (1, 1, "a")])
    require([v["union"] for v in square["terms"]] == [3, 3, 3, 3] and
            square["exp_n_times_informative_redundancy"] == {"numerator": "256", "denominator": "81"},
            "source-only cumulative on four equal pairs")
    # Use the real, frozen documentary fields with the independently constructed example.
    record = read_record(PUBLISHED.read_bytes())
    record["measurement_results"] = fixture
    info = {"LP2": square, "LP3": square}
    record["informative_redundancy"] = info
    good = canonical(record)
    check_record(good, fixture, info)
    changes = [
        (b'"count":1', b'"count":true'),
        (b'"LP2_and_LP3_same_arrays_in_same_order":true',
         b'"LP2_and_LP3_same_arrays_in_same_order":1'),
        (b'"count":1', b'"count":1.0'),
        (b'"count":1', b'"count":NaN'),
        (b'"count":1', b'"count":0,"count":1'),
        (b'"count":1', b'"extra":3,"count":1'),
        (b'"dataset_doi":', b'"extra":3,"dataset_doi":'),
        (b'"Luis Seabra Lopes"', b'"another source"'),
        (b'"task_pairs"', b'"omitted_pairs"'),
    ]
    for before, after in changes:
        require(before in good, "trace control does not apply to its input")
        try:
            check_record(good.replace(before, after, 1), fixture, info)
        except ValueError:
            continue
        raise ValueError("altered trace record was accepted")
    return "synthetic shape, order, changed coordinate, duplicate labels and multiplicity passed"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    source = cli.add_mutually_exclusive_group()
    source.add_argument("--archive", type=Path, help="locally saved original UCI ZIP")
    source.add_argument("--fetch", action="store_true", help="retrieve the pinned ZIP from UCI")
    cli.add_argument("--self-test", action="store_true", help="exercise the synthetic dependency cases")
    args = cli.parse_args()
    require(args.archive or args.fetch or args.self_test, "use --archive, --fetch or --self-test")
    if args.self_test:
        print(self_test())
    if args.archive or args.fetch:
        meta_bytes = (HERE / "sources.json").read_bytes()
        require(sha(meta_bytes) == SOURCE_SHA, "original measurement source specification differs")
        meta = json.loads(meta_bytes)
        members = read_members(meta, args.archive, args.fetch)
        tasks = {task["id"]: measurements(data, task) for task, data in members}
        require(list(tasks) == [f"LP{i}" for i in range(1, 6)], "five original task files")
        check_record(PUBLISHED.read_bytes(), comparison(tasks), source_marginal_comparison(members))
        print("All 463 rows, ten task pairs, five label tables and the ordered recording comparison passed.")


if __name__ == "__main__":
    main()
