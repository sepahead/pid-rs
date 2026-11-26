"""Exercise the two finite numerical checkers on the September 2026 panels.

Use checker_self_test_v2.py DISCRETE_DUMP CONTINUOUS_DUMP. The two unmodified
inputs must pass. Each of the 17 changed inputs must fail for its own reason.
"""
import argparse
import copy
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOLERANCE = 1e-12
CHECKERS = {
    "discrete": HERE / "check_discrete.py",
    "continuous": HERE / "check_continuous.py",
}
DISCRETE_KEYS = sorted(
    ["imin2", "imin3_atom", "imin3_red", "three_minus", "three_plus",
     "two_mi_terms", "two_minus", "two_plus"]
    + [f"n{size}_{quantity}" for size in (2, 3, 4)
       for quantity in ("jointmi", "minus", "net", "plus", "subset_mi", "sum_atoms_vs_mi")]
)
CONTINUOUS_KEYS = (
    "ksg_s0_t", "ksg_s1_t", "ksg_s0s1_t", "ksg_local",
    "isx", "pid2", "inc_pid3", "full_pid3",
)
# Original stdout on these fixed scientific inputs. The full output and input
# identities appear in results/hostile-input-observer-2026-11-25.json.
FIXED_NUMERICAL_OUTPUTS = {
    ("discrete", None): "e342e7572b26a6e90a2c2f807a686fc151c122def71bf076b978565ced4e8ffe",
    ("continuous", None): "e009833bfa1f408f7029f620eedbfdd35351d6a4436ef07fdef56dbc3017cac5",
    ("discrete", "n2_plus"): "9f866423c3f33a8722d32af17039f07c5985df2f765add51015ab4224a242785",
    ("discrete", "n2_subset_mi"): "5dfc45445c9a42dfd225b95857c655c4dbb951580ef24ab28a978ba6b8c226e6",
    ("continuous", "isx"): "693c4e82db42b67425368741a06cef4e82f0007301a9c969629f6d56837176d1",
}
ABSOLUTE_MAXIMA = {"ksg_local", "pid2", "inc_pid3", "full_pid3"}
SCIENTIFIC_NUMBER = r"[+-]?[0-9]+(?:\.[0-9]+)?[eE][+-][0-9]+"


class CheckFailure(ValueError):
    """The declared positive or negative observation was not obtained."""


def require(condition, description):
    if not condition:
        raise CheckFailure(description)


def run_child(checker, path):
    # The native invocation is explicit when the parent has -O or -OO.
    # Clear the environment override so a child cannot silently change mode.
    flags = {0: [], 1: ["-O"], 2: ["-OO"]}[sys.flags.optimize]
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    return subprocess.run(
        [sys.executable, *flags, "-B", str(checker), str(path)],
        capture_output=True, text=True, env=env, timeout=240,
    )


def check_discrete(lines, expected_metric):
    require(len(lines) == len(DISCRETE_KEYS) + 2 and lines[-2] == "cases: 60",
            "the categorical checker must report all 60 cases and all metrics")
    errors = {}
    for label, line in zip(DISCRETE_KEYS, lines[:-2], strict=True):
        match = re.fullmatch(re.escape(f"{label:24s} max|diff| = ") + "(" + SCIENTIFIC_NUMBER + ")", line)
        require(match is not None, f"missing categorical metric {label}")
        value = float(match[1])
        require(math.isfinite(value) and format(value, ".3e") == match[1]
                and not match[1].startswith("-"), f"invalid printed categorical maximum {label}")
        errors[label] = value
    expected = set() if expected_metric is None else {expected_metric}
    exceeded = {key for key, error in errors.items() if error > TOLERANCE}
    verdict = "PASS" if not expected else f"FAIL {expected_metric}"
    require(exceeded == expected and lines[-1] == f"tolerance 1e-12 nats: {verdict}",
            "the categorical diagnostic must identify the expected inaccurate metric")


def check_printed_estimate(label, printed, supplied, signed_residual):
    """Recover the only four-decimal value compatible with the printed residual."""
    # The checker subtracts its recomputed estimate from the stored binary64 value.
    # It prints the resulting difference with one digit after the decimal in scientific notation.
    center = Fraction(signed_residual)
    spread = Fraction(0)
    if center:
        exponent = int(signed_residual.split("e")[1])
        half_print_unit = Fraction(10) ** (exponent - 1) / 2
        # Bound rounding of binary64 subtraction as well as rounding for the printed result.
        binary_rounding = (abs(center) + half_print_unit) / 2**52 + Fraction(1, 2**1074)
        spread = half_print_unit + binary_rounding
    # Two binary64 inputs differ by an integer multiple of the smallest subnormal.
    # A subtraction that prints a zero scientific mantissa therefore had zero difference.
    estimate = Fraction.from_float(supplied) - center
    lower = estimate - spread
    upper = estimate + spread
    reported_cell = Fraction(printed) * 10_000
    require(round(lower * 10_000) == reported_cell == round(upper * 10_000),
            f"wrong or ambiguous four-decimal estimate {label}")
    if reported_cell == 0:
        require((lower >= 0 and printed.startswith("+"))
                or (upper < 0 and printed.startswith("-")),
                f"wrong or ambiguous sign for {label}")


def check_continuous(lines, cases, expected_metric):
    require(len(lines) == len(cases) + 2 and len(cases) == 6, "six continuous cases are required")
    count = sum(item["value"] is None for case in cases for item in case["inc_pid3"])
    require(lines[-2] == f"cases: 6; abstaining incomplete-PID3 entries: {count}",
            "the continuous output must identify its cases and abstentions")
    exceeded = set()
    residuals = []
    for index, (line, case) in enumerate(zip(lines[:-2], cases, strict=True)):
        header = re.fullmatch(
            r"n= *([0-9]+) d=([0-9]+) k=([0-9]+)  "
            r"I0=([+-][0-9]+\.[0-9]{4}) red=([+-][0-9]+\.[0-9]{4}) +(.+)", line,
        )
        require(header is not None, f"missing continuous results for row {index + 1}")
        require(tuple(map(int, header.group(1, 2, 3))) == (case["n"], case["d"], case["k"])
                and all(math.isfinite(float(x)) for x in header.group(4, 5)),
                f"wrong continuous case or nonfinite estimate on row {index + 1}")
        require(all(format(float(x), "+.4f") == x for x in header.group(4, 5)),
                "wrong printed estimate precision or sign")
        prefix = (f"n={case['n']:4d} d={case['d']} k={case['k']}  "
                  f"I0={header[4]} red={header[5]}   ")
        require(line == prefix + header[6], "wrong original continuous column format")
        fields = header[6].split("  ")
        require(len(fields) == len(CONTINUOUS_KEYS), "missing continuous residuals")
        signed = {}
        for key, field in zip(CONTINUOUS_KEYS, fields, strict=True):
            match = re.fullmatch(re.escape(key) + "=(" + SCIENTIFIC_NUMBER + ")", field)
            require(match is not None, f"missing continuous residual {key}")
            number = match[1]
            value = float(number)
            require(math.isfinite(value) and format(value, ".1e") == number,
                    f"wrong printed precision for residual {key}")
            require(key not in ABSOLUTE_MAXIMA or not number.startswith("-"),
                    f"absolute maximum {key} cannot have a negative sign")
            signed[key] = number
            magnitude = abs(value)
            residuals.append(magnitude)
            if magnitude > TOLERANCE:
                exceeded.add((index, key))
        check_printed_estimate("I0", header[4], case["ksg_s0_t"], signed["ksg_s0_t"])
        check_printed_estimate("red", header[5], case["isx_s0_s1_t"], signed["isx"])
    verdict = "PASS" if expected_metric is None else "FAIL"
    match = re.fullmatch(r"largest difference (" + SCIENTIFIC_NUMBER + r"); tolerance 1e-12 nats: "
                         + verdict, lines[-1])
    require(match is not None and match[1] == format(max(residuals), ".1e"),
            "the continuous summary must give its largest measured difference")
    expected = set() if expected_metric is None else {(0, expected_metric)}
    require(exceeded == expected, "the continuous residual must identify the right input and metric")


def inspect_result(result, kind, continuous_cases, *, message=None, metric=None):
    """Check a complete positive result, a structural refusal, or a numerical refusal."""
    expected_exit = int(message is not None or metric is not None)
    require(result.returncode == expected_exit,
            f"{kind} checker returned {result.returncode}; expected {expected_exit}. "
            f"{result.stderr.strip()[-350:]}")
    if message is not None:
        require(result.stdout == "" and result.stderr == message + "\n",
                f"expected diagnostic {message!r}; received {result.stderr.strip()[:350]!r}")
        return
    require(result.stderr == "", f"unexpected {kind} checker diagnostic {result.stderr.strip()[:350]}")
    lines = result.stdout.splitlines()
    require(result.stdout == "\n".join(lines) + "\n", "incomplete numerical output")
    if kind == "discrete":
        check_discrete(lines, metric)
    else:
        check_continuous(lines, continuous_cases, metric)
    received = hashlib.sha256(result.stdout.encode("utf-8")).hexdigest()
    require(received == FIXED_NUMERICAL_OUTPUTS.get((kind, metric)),
            "the finite numerical result differs from the recorded checker output")


def mutations(discrete, continuous):
    """Yield the same 17 changed JSON values as the original self-test, in order."""
    def case(name, kind, value, *, message=None, metric=None, raw=None):
        return (name, kind, json.dumps(value) if raw is None else raw, message, metric)

    yield case("discrete: empty list", "discrete", [], message="expected exactly 60 cases")
    yield case("discrete: four-source cases removed", "discrete",
               [row for row in discrete if row["n_sources"] != 4], message="expected exactly 60 cases")
    for name, value in (("emptied", []), ("truncated", discrete[0]["imin2"][:1])):
        changed = copy.deepcopy(discrete)
        changed[0]["imin2"] = value
        yield case(f"discrete: imin2 {name}", "discrete", changed,
                   message="case 0 imin2: expected a list of 7 numbers")
    changed = copy.deepcopy(discrete)
    zero = next(a for row in changed for a in row["n"] if a["net"] == 0.0)
    zero["net"] = False
    yield case("discrete: JSON false for a zero atom", "discrete", changed,
               message="net: expected a finite number, got False")
    changed = copy.deepcopy(discrete)
    changed[0]["n"][0]["plus"] += 1e-9
    yield case("discrete: atom perturbed by 1e-9", "discrete", changed,
               metric=f"n{discrete[0]['n_sources']}_plus")
    changed = copy.deepcopy(discrete)
    changed[0]["n"].append(copy.deepcopy(changed[0]["n"][0]))
    yield case("discrete: duplicate antichain", "discrete", changed,
               message=f"case 0: expected {len(discrete[0]['n'])} antichains")
    changed = copy.deepcopy(discrete)
    changed[0]["n"][0]["plus"] = "NaN"
    yield case("discrete: string value", "discrete", changed,
               message="plus: expected a finite number, got 'NaN'")
    changed = copy.deepcopy(discrete)
    changed[0]["n_subset_mis"][0] += 1e-9
    yield case("discrete: subset MI perturbed by 1e-9", "discrete", changed,
               metric=f"n{discrete[0]['n_sources']}_subset_mi")
    encoded = json.dumps(discrete)
    mark = '"n_sources": 2'
    require(mark in encoded and discrete[0]["n_sources"] == 2,
            "the duplicate-key control needs the original first two-source case")
    keys = list(discrete[0])
    keys.insert(keys.index("n_sources"), "n_sources")
    yield case("discrete: duplicate JSON key", "discrete", None,
               raw=encoded.replace(mark, mark + ", " + mark, 1), message=f"duplicate JSON key in {keys!r}")
    yield case("continuous: empty list", "continuous", [], message="expected exactly 6 cases")
    n = continuous[0]["n"]
    changed = copy.deepcopy(continuous)
    changed[0]["inc_pid3"] = []
    yield case("continuous: incomplete PID3 emptied", "continuous", changed,
               message=f"case n={n} incomplete PID3: expected 18 lattice entries")
    changed = copy.deepcopy(continuous)
    for entry in changed[0]["inc_pid3"]:
        entry["value"] = None
    yield case("continuous: incomplete PID3 all abstaining", "continuous", changed,
               message=f"case n={n} incomplete PID3: every entry abstained")
    changed = copy.deepcopy(continuous)
    changed[0]["full_pid3"] = [copy.deepcopy(changed[0]["full_pid3"][0]) for _ in range(18)]
    yield case("continuous: 18 copies of one full-PID3 antichain", "continuous", changed,
               message=f"case n={n} full PID3: lattice entries are not the 18 distinct antichains")
    changed = copy.deepcopy(continuous)
    changed[0]["full_pid3"] = "error: unavailable"
    yield case("continuous: full PID3 absent", "continuous", changed,
               message=f"case n={n}: the full PID3 lattice is absent: 'error: unavailable'")
    changed = copy.deepcopy(continuous)
    changed[0]["isx_s0_s1_t"] += 1e-9
    yield case("continuous: redundancy perturbed by 1e-9", "continuous", changed, metric="isx")
    changed = copy.deepcopy(continuous)
    changed[0]["pid2"] = changed[0]["pid2"][:3]
    yield case("continuous: PID2 shortened", "continuous", changed,
               message=f"case n={n}: wrong local-term or PID2 length")


def main(discrete_path, continuous_path):
    # Run directly on the supplied files so that a duplicate key is not lost on reserialization.
    continuous = json.loads(continuous_path.read_bytes())
    for kind, path in (("discrete", discrete_path), ("continuous", continuous_path)):
        result = run_child(CHECKERS[kind], path)
        inspect_result(result, kind, continuous)
        print(f"verified: original {kind} data")
    discrete = json.loads(discrete_path.read_bytes())
    total = 0
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "input.json"
        for name, kind, text, message, metric in mutations(discrete, continuous):
            path.write_text(text, encoding="utf-8")
            try:
                submitted = json.loads(text) if kind == "continuous" and metric else continuous
                inspect_result(run_child(CHECKERS[kind], path), kind, submitted,
                               message=message, metric=metric)
            except CheckFailure as error:
                raise CheckFailure(f"{name}: {error}") from error
            print(f"rejected: {name}")
            total += 1
    require(total == 17, "expected all 17 original changed inputs")
    print(f"{total} of {total} hostile inputs rejected for the expected reasons")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("discrete_dump", type=Path)
    parser.add_argument("continuous_dump", type=Path)
    args = parser.parse_args()
    try:
        main(args.discrete_dump, args.continuous_dump)
    except (CheckFailure, OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        sys.exit(str(error))
