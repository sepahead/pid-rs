# Author: Sepehr Mahmoudian, 2026.
"""Causal input controls for the bounded threshold down-set comparison.

Run with the retained categorical dump. Each control invokes the actual checker in a
fresh process. Run this script normally and with -O; each mode propagates to its children.
The optional checker path supports an explicit historical regression demonstration.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    if len(sys.argv) not in (2, 3):
        raise SystemExit("usage: check_threshold_down_sets_self_test.py <dump.json> [checker.py]")
    dump = Path(sys.argv[1]).read_text()
    cases = json.loads(dump)
    checker = Path(sys.argv[2]) if len(sys.argv) == 3 else Path(__file__).with_name("check_threshold_down_sets.py")
    controls = [("baseline", dump, 0)]

    def mutation(name, edit):
        data = copy.deepcopy(cases)
        edit(data)
        controls.append((name, json.dumps(data), 1))

    for name, value in (("nan", float("nan")), ("positive-infinity", float("inf")),
                        ("negative-infinity", float("-inf")), ("boolean-atom", True),
                        ("string-atom", "0"), ("finite-wrong-atom", 1e6)):
        mutation(name, lambda data, value=value: data[0]["n"][0].__setitem__("net", value))
    controls.append(("json-number-overflow", controls[2][1].replace("Infinity", "1e999"), 1))
    controls.append(("duplicate-json-key", dump.replace('"n_sources":', '"n_sources":2,"n_sources":', 1), 1))
    mutation("float-source-count", lambda data: data[0].__setitem__("n_sources", 2.0))
    mutation("missing-target", lambda data: data[0].pop("target"))
    mutation("empty-target", lambda data: data[0].__setitem__("target", []))
    mutation("ragged-column", lambda data: data[0]["sources"][0].append(0))
    mutation("boolean-category", lambda data: data[0]["sources"][0].__setitem__(0, True))
    mutation("negative-category", lambda data: data[0]["target"].__setitem__(0, -1))
    mutation("wrong-source-shape", lambda data: data[0]["sources"].append(data[0]["target"]))
    for name, masks in (("empty-antichain", []), ("boolean-mask", [True]),
                        ("zero-mask", [0]), ("outside-mask", [4]),
                        ("repeated-mask", [1, 1]), ("comparable-masks", [1, 3])):
        mutation(name, lambda data, masks=masks: data[0]["n"][0].__setitem__("antichain", masks))
    mutation("duplicate-node", lambda data: data[0]["n"].__setitem__(0, data[0]["n"][1]))
    mutation("missing-node", lambda data: data[0]["n"].pop())
    mutation("wrong-arity-census", lambda data: data.__setitem__(20, copy.deepcopy(data[0])))

    def overflow(data):
        for atom in data[0]["n"]:
            atom["net"] = 1e308
    mutation("finite-input-sum-overflow", overflow)
    failures = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-threshold-controls-") as tmp:
        for name, payload, expected in controls:
            path = Path(tmp) / (name + ".json")
            path.write_text(payload)
            argv = [sys.executable] + (["-O"] if sys.flags.optimize else [])
            argv += ["-I", "-S", "-B", str(checker.resolve()), str(path)]
            result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
            accepted = result.returncode == 0
            if accepted != (expected == 0):
                failures.append(name)
                print(f"FAIL: {name}: exit {result.returncode}")
            elif expected == 0 and ("systems: 60; tolerance 1e-12 nats: PASS" not in result.stdout or result.stderr):
                failures.append(name)
                print(f"FAIL: {name}: baseline did not finish cleanly")
    if failures:
        print(f"FAIL: {len(failures)} of {len(controls)} controls")
        return 1
    print(f"PASS: {len(controls)} threshold controls (1 accepted, {len(controls)-1} rejected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
