"""Replay the exact count study and check every declared finite output."""

import argparse
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CONTROL_NAMES = {
    "both_conditioning_sources",
    "converse_support_implication_refuted",
    "count_repetition",
    "overstated_or_unoccupied_bound_refuted",
    "signed_component_dominance_refuted",
    "target_conditioning",
    "zero_count_ignored",
}
EXPECTED = "29a5f56546520458e3590c46bbcb477849984f19bbc8653815d0e2e3a02eb5f2"


def require(value, message):
    if not value:
        raise ValueError(message)


def unique_pairs(values):
    result = {}
    for key, value in values:
        require(key not in result, "repeated JSON key")
        result[key] = value
    return result


def whole_number(value, expected=None):
    require(
        type(value) is int and (expected is None or value == expected), "integer value"
    )
    return value


def check_records(records):
    require(type(records) is list, "a list of attaining cases")
    answer = {}
    for item in records:
        require(
            type(item) is dict and set(item) == {"N", "ell", "exp_N_gap"},
            "exact witness fields",
        )
        n, labels = whole_number(item["N"]), whole_number(item["ell"])
        require(
            2 <= labels <= n and (n, labels) not in answer, "feasible unique count pair"
        )
        rest = n + 2 - labels
        a, b = rest // 2, (rest + 1) // 2
        ratio = Fraction((a * b + a + b + 1) ** 2, (a * b) ** 2)
        require(
            type(item["exp_N_gap"]) is str and str(ratio) == item["exp_N_gap"],
            "exact reduced positive gap",
        )
        answer[n, labels] = ratio
    return answer


def check(obj):
    require(
        type(obj) is dict
        and set(obj)
        == {
            "units",
            "adverse_controls",
            "all18_local_component_checks_on_census_and_witnesses",
            "binary_labelled_census",
            "binary_observed_minima",
            "sharp_witness_count",
            "sharp_witnesses",
        },
        "exact fields",
    )
    require(
        obj["units"] == "All listed ratios are exp(N times the quantity in nats).",
        "count-cleared scale",
    )
    whole_number(obj["all18_local_component_checks_on_census_and_witnesses"], 125208)
    whole_number(obj["sharp_witness_count"], 123)
    expected = {(n, i) for n in range(2, 17) for i in range(2, n + 1)} | {
        (25, 2),
        (25, 3),
        (25, 25),
    }
    require(
        set(check_records(obj["sharp_witnesses"])) == expected,
        "complete attainment roster",
    )
    require(
        check_records(obj["binary_observed_minima"])
        == {(2, 2): Fraction(16), (3, 2): Fraction(9)},
        "binary minima",
    )
    suite = obj["binary_labelled_census"]
    require(type(suite) is list and len(suite) == 3, "three binary totals")
    for row, data in zip(suite, ((1, 16, 0), (2, 136, 8), (3, 816, 128)), strict=True):
        n, count, positive = data
        require(
            type(row) is dict and set(row) == {"N", "tables", "B_positive", "B_zero"},
            "census fields",
        )
        for key, value in (
            ("N", n),
            ("tables", count),
            ("B_positive", positive),
            ("B_zero", count - positive),
        ):
            whole_number(row[key], value)
    controls = obj["adverse_controls"]
    require(
        type(controls) is dict
        and set(controls) == CONTROL_NAMES | {"rejected_invalid_count_inputs"},
        "control roster",
    )
    whole_number(controls["rejected_invalid_count_inputs"], 6)
    require(
        all(controls[name] is True for name in CONTROL_NAMES),
        "typed scientific control",
    )


def adverse(obj):
    edits = (
        lambda d: d["sharp_witnesses"][0].update(N=True),
        lambda d: d["sharp_witnesses"][0].update(ell=3),
        lambda d: d["sharp_witnesses"].pop(),
        lambda d: d["sharp_witnesses"][3].update(exp_N_gap="4"),
        lambda d: d["binary_labelled_census"][1].update(B_positive=128, B_zero=8),
        lambda d: d["adverse_controls"].update(target_conditioning=1),
        lambda d: d.update(all18_local_component_checks_on_census_and_witnesses=125207),
    )
    for change in edits:
        changed = copy.deepcopy(obj)
        change(changed)
        try:
            check(changed)
        except ValueError:
            continue
        raise ValueError("accepted altered finite output")
    try:
        json.loads('{"N":6,"N":7}', object_pairs_hook=unique_pairs)
    except ValueError:
        return len(edits) + 1
    raise ValueError("accepted duplicate field")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    command = [
        sys.executable,
        *(["-O"] if sys.flags.optimize else []),
        "-I",
        "-S",
        "-B",
        str(HERE / "verify.py"),
        "--self-test",
    ]
    returning = subprocess.run(command, check=True, capture_output=True, timeout=90)
    original = (HERE / "RESULT.json").read_bytes()
    require(
        not returning.stderr and returning.stdout == original,
        "scientific run differs from the full stored output",
    )
    obj = json.loads(original, object_pairs_hook=unique_pairs)
    check(obj)
    digest = hashlib.sha256(original).hexdigest()
    require(digest == EXPECTED, "original source return changed")
    result = {
        "sharp_count_pairs": 123,
        "binary_tables": 968,
        "scientific_sha256": digest,
    }
    if args.self_test:
        result["refused_changed_returns"] = adverse(obj)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
