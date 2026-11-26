"""Compare a fixed triple of singleton alphabets with an attainable unrestricted bound."""

import argparse
from fractions import Fraction
import importlib.util
import json
from pathlib import Path

source = Path(__file__).with_name("verify.py")
spec = importlib.util.spec_from_file_location("third_source_gap", source)
direct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(direct)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def calculate():
    rows = []
    for a in (1, 2, 3):
        b = 4 - a
        observed = direct.observe({(0, 0, 0, 0): a, (0, 0, 1, 0): b})
        entropy = Fraction(4**4, a**a * b**b)
        require(
            observed["N"] == 4 and observed["ell"] == 2,
            "two occupied labels at total four",
        )
        require(
            all(data[0] == data[1] for data in observed["averages"].values()),
            "18 exact zero signed means",
        )
        require(
            observed["A"] == observed["B"] == entropy and observed["M"] == 1,
            "constant-target entropy",
        )
        require(observed["gap"] == entropy**2, "four times the restricted gap")
        rows.append({"third_counts": [a, b], "exp_four_gap": str(observed["gap"])})
    records = [Fraction(row["exp_four_gap"]) for row in rows]
    restricted = min(records)
    winners = [
        row["third_counts"]
        for row, val in zip(rows, records, strict=True)
        if val == restricted
    ]
    free = direct.observe(direct.witness(4, 2))
    require(
        winners == [[1, 3], [3, 1]] and records[1] == 256,
        "three labelled splits and their order",
    )
    require(
        restricted == Fraction(65536, 729)
        and free["gap"] == Fraction(81, 16) < restricted,
        "universal minimum and restricted minimum",
    )
    return {
        "N": 4,
        "occupied_third_labels": 2,
        "fixed_first_second_and_target_labels": [1, 1, 1],
        "restricted_splits": rows,
        "restricted_minimizers": winners,
        "restricted_exp_four_gap_min": str(restricted),
        "freely_chosen_other_alphabets_exp_four_gap_min": str(free["gap"]),
    }


def hostile(result):
    equal_counts = result["restricted_splits"][1]["third_counts"]
    require(
        result["restricted_exp_four_gap_min"]
        != result["freely_chosen_other_alphabets_exp_four_gap_min"],
        "using the freely attainable minimum for the singleton alphabets",
    )
    require(
        len(set(equal_counts)) != result["occupied_third_labels"],
        "using the number of different counts for the number of labels",
    )
    omitted = direct.observe({(0, 0, 0, 0): 4})
    require(
        omitted["ell"] == 1 and omitted["B"] == omitted["gap"] == 1,
        "a one-label table has zero conditional entropy and gap",
    )
    try:
        direct.minimum_factor(omitted["N"], omitted["ell"])
    except ValueError as error:
        require(str(error) == "need 2 <= ell <= N", "unexpected rejection")
    else:
        raise ValueError("the positive minimum admitted only one occupied label")
    return 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    result = calculate()
    if args.self_test:
        result["false_substitutions_rejected"] = hostile(result)
    print(json.dumps(result, indent=2, sort_keys=True))
