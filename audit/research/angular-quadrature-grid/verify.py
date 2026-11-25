"""Verify the published angular grid record or compare every field with a new local calculation."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
PUBLISHED = "ba40c7e885d867368b45436235bf4ec965b171f4a85636552e2a0a0be2ae1e78"
CALCULATION = "d7dfdd039c2f0839600c927ab2bdcb3a8c84810f6d6c83cbfe28ce0fd5d96d8e"
HISTORICAL = "345eaa36d1c5cfe5da5e8f2ed45ee2d61217956807853689ad16379171a0f8b7"
EXAMPLE_FIELDS = {
    "a", "b", "atom_nats", "lower_bound_nats", "tail_nats",
    "tail_bound_nats", "added_conditional_information_nats",
}


def require(condition, explanation):
    if not condition:
        raise ValueError(explanation)


def decode(raw):
    def unique(pairs):
        record = dict(pairs)
        require(len(record) == len(pairs), "duplicate JSON field")
        return record

    def invalid(token):
        raise ValueError("nonfinite JSON number " + token)

    require(len(raw) <= 65536, "grid record size")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def pinned(name, wanted):
    path = HERE / name
    require(path.is_file() and not path.is_symlink(), "regular source " + name)
    raw = path.read_bytes()
    require(sha256(raw).hexdigest() == wanted, "source identity " + name)
    return raw


def ring_members(last):
    pairs = set()
    for ring in range(1, last + 1):
        for first in range(ring + 1):
            second = ring - first
            for i in (first, -first):
                for j in (second, -second):
                    pairs.add((i, j))
    require(len(pairs) == 2 * last * (last + 1), "whole-ring count")
    return sorted(pairs)


def pair_digest(pairs):
    word = "".join(f"{i},{j}\n" for i, j in pairs)
    return sha256(word.encode("ascii")).hexdigest()


def check_shape(data):
    require(type(data) is dict and set(data) == {
        "examples", "lower", "tail", "moments", "numpy_version", "parameter_count",
        "passed", "phase_count", "tolerance_nats",
    }, "complete grid record")
    require(data["passed"] is True and type(data["numpy_version"]) is str and
            bool(data["numpy_version"].strip()), "completion and NumPy version")
    for key, value in (("moments", 8), ("phase_count", 2048), ("parameter_count", 67)):
        require(type(data[key]) is int and data[key] == value, "grid extent " + key)
    require(type(data["tolerance_nats"]) is float and data["tolerance_nats"] == 1e-15,
            "absolute tolerance")
    for name, last in (("lower", 33), ("tail", 30)):
        row = data[name]
        require(type(row) is dict and set(row) == {
            "at", "at_indices", "integer_pairs_sha256", "minimum_margin_nats", "pairs",
        }, "complete margin record " + name)
        pairs = ring_members(last)
        require(type(row["pairs"]) is int and row["pairs"] == len(pairs) and
                row["integer_pairs_sha256"] == pair_digest(pairs), "roster " + name)
        indices = row["at_indices"]
        require(type(indices) is list and len(indices) == 2 and
                all(type(i) is int for i in indices) and tuple(indices) in pairs,
                "minimum indices " + name)
        point = row["at"]
        require(type(point) is list and len(point) == 2 and
                all(type(x) is float for x in point) and
                point == [3 * i / 100 for i in indices], "minimum coordinates " + name)
        margin = row["minimum_margin_nats"]
        require(type(margin) is float and math.isfinite(margin) and
                margin >= -data["tolerance_nats"], "nonfinite or failed margin " + name)
    examples = data["examples"]
    require(type(examples) is list and len(examples) == 2, "two worked records")
    for row, point in zip(examples, ((0.25, 0.25), (0.5, 0.0))):
        require(type(row) is dict and set(row) == EXAMPLE_FIELDS and
                all(type(x) is float and math.isfinite(x) for x in row.values()) and
                (row["a"], row["b"]) == point, "complete worked record")


def verify(raw, reference):
    data = decode(raw)
    check_shape(data)
    # Canonical JSON preserves integer/float, number sign, list order and every field.
    # Ordinary dictionary equality would silently identify JSON true with the integer 1.
    canonical = lambda x: json.dumps(x, sort_keys=True, allow_nan=False, separators=(",", ":"))
    require(canonical(data) == canonical(reference), "grid fields differ from selected reference")
    return data


def recompute():
    pinned("quadrature.py", CALCULATION)
    flags = ["-O"] if sys.flags.optimize else []
    env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
           "VECLIB_MAXIMUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    command = [sys.executable, *flags, "-I", "-B", HERE / "quadrature.py"]
    output = subprocess.run(command, cwd=HERE, env=env, capture_output=True,
                            check=True, timeout=1800)
    require(not output.stderr, "unexpected numerical-program diagnostic")
    data = decode(output.stdout)
    check_shape(data)
    return data


def historical_mask():
    import numpy as np

    old = np.linspace(-0.99, 0.99, 67)
    previous = {(i - 33, j - 33) for i, a in enumerate(old) for j, b in enumerate(old)
                if 0 < abs(a) + abs(b) <= 0.9}
    actual = set(ring_members(30))
    result = dict(numpy_version=np.__version__, old_tail_count=len(previous),
                  missing=sorted(actual - previous), extra=sorted(previous - actual))
    prior = decode(pinned("historical-grid.json", HISTORICAL))
    for field in ("old_tail_count", "missing", "extra"):
        require(json.dumps(result[field]) == json.dumps(prior[field]),
                "historical mask differs at " + field)
    return result


def self_test(reference):
    changes = [
        (("tail", "pairs"), 0), (("tail", "integer_pairs_sha256"), "0" * 64),
        (("tail", "at_indices"), [33, 33]),
        (("tail", "minimum_margin_nats"), float("nan")),
        (("tail", "minimum_margin_nats"), float("inf")),
        (("tail", "minimum_margin_nats"), -1.1e-15),
        (("tail", "minimum_margin_nats"), 100.0),
        (("examples", 0, "atom_nats"), -42.0),
        (("lower", "at_indices"), [False, True]),
        (("examples", 1, "tail_nats"), 0.0),
        (("phase_count",), 2048.0), (("passed",), 1),
        (("numpy_version",), reference["numpy_version"] + "-different"),
    ]
    trials = []
    for keys, value in changes:
        trial = deepcopy(reference)
        parent = trial
        for key in keys[:-1]:
            parent = parent[key]
        parent[keys[-1]] = value
        trials.append(json.dumps(trial))
    missing = deepcopy(reference)
    del missing["examples"][0]["lower_bound_nats"]
    extra = deepcopy(reference)
    extra["lower"]["unreported"] = 0
    text = json.dumps(reference)
    duplicate = text.replace('"phase_count": 2048', '"phase_count": 1, "phase_count": 2048')
    require(duplicate != text, "duplicate field control")
    trials.extend((json.dumps(missing), json.dumps(extra), duplicate))
    for number, trial in enumerate(trials, 1):
        try:
            verify(trial.encode(), reference)
        except ValueError:
            continue
        raise ValueError(f"accepted changed grid record {number}")
    return len(trials)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path, nargs="?", default=HERE / "quadrature-grid.json")
    parser.add_argument("--fresh", action="store_true",
                        help="rerun the complete local quadrature and compare every field")
    parser.add_argument("--historical", action="store_true", help="measure the earlier NumPy filter")
    parser.add_argument("--self-test", action="store_true", help="reject sixteen changed records")
    args = parser.parse_args()
    require(args.certificate.is_file() and args.certificate.stat().st_size <= 65536,
            "bounded input file")
    supplied = args.certificate.read_bytes()
    check_shape(decode(supplied))
    reference = recompute() if args.fresh else decode(pinned("quadrature-grid.json", PUBLISHED))
    check_shape(reference)
    verify(supplied, reference)
    output = {"whole_ring_counts": [len(ring_members(n)) for n in (33, 30)],
              "reference": "fresh local calculation" if args.fresh else "published calculation"}
    if args.self_test:
        output["changed_certificates_refused"] = self_test(reference)
    if args.historical:
        output["historical"] = historical_mask()
    print(json.dumps(output, indent=2, sort_keys=True, allow_nan=False))
