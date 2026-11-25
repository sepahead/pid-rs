"""Rerun exact scientific fixtures and optional adverse inputs, without modifying the study."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile


STUDY = Path(__file__).resolve().parent
INTEGER = STUDY / "integer-witnesses"
PYTHON = [sys.executable] + (["-O"] if sys.flags.optimize else []) + ["-I", "-S", "-B"]
ARRAY_DIGEST = {
    "triangle": "4b8ca3f4d57b8578dcdf3aa8d769f3d4350ebee9d4ee79e20c531f4dfd3e810d",
    "upper": "251a82da3494b386bd94d46d9bf58fd427c71e2eec3cb1c00638e42103b38749",
}


def need(ok, text):
    if not ok:
        raise ValueError(text)


def invoke(script, *args, reason=None):
    run = subprocess.run([*PYTHON, str(script), *map(str, args)], capture_output=True, timeout=45)
    if reason is not None:
        need(run.returncode == 1 and not run.stdout
             and run.stderr.decode().splitlines()[-1] == "ValueError: " + reason, "expected refusal " + reason)
    else:
        need(run.returncode == 0 and not run.stderr, "child failed " + script.name)
    return run.stdout


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--self-test", action="store_true", help="also reject eight changed integer arrays and 18 changed five-row reports")
    args = cli.parse_args()
    saved = {}
    for src, output, extra in (
            ("finite.py", "finite-observations.json", []),
            ("two_arm.py", "exact-rows.json", [STUDY / "represented-report.json"]),
            ("whole_upper.py", "whole-upper-observations.json", []),
            ("three_rows.py", "three-row-observations.json", [])):
        stream = invoke(STUDY / src, *extra)
        need(stream == (STUDY / output).read_bytes(), "changed finite output " + output)
        saved[output] = sha256(stream).hexdigest()
    changed_reports = 0
    if args.self_test:
        tested = json.loads(invoke(STUDY / "two_arm.py", STUDY / "represented-report.json", "--self-test"))
        changed_reports = tested.pop("altered_reports_rejected")
        need(type(changed_reports) is int and changed_reports == 18
             and tested == json.loads((STUDY / "exact-rows.json").read_bytes()),
             "five-row report reader or its altered inputs")
    with tempfile.TemporaryDirectory(prefix="count-geometry-") as tmp:
        out = Path(tmp)
        proposals = {}
        for mode, producer in (("triangle", "construction.py"), ("upper", "upper-mean.py")):
            raw = invoke(INTEGER / producer)
            need(sha256(raw).hexdigest() == ARRAY_DIGEST[mode], "array identity " + mode)
            path = out / (mode + ".json")
            path.write_bytes(raw)
            stream = invoke(INTEGER / "geometry-judge.py", mode, path)
            need(stream == (INTEGER / (mode + "-result.json")).read_bytes(), "independent exact judge " + mode)
            saved[mode] = sha256(stream).hexdigest()
            proposals[mode] = json.loads(raw)
        if args.self_test:
            path = out / "wrong.json"
            def refuse(mode, obj, reason):
                path.write_text(json.dumps(obj))
                invoke(INTEGER / "geometry-judge.py", mode, path, reason=reason)
            path.write_bytes(b'[{"n":2,"n":2}]')
            invoke(INTEGER / "geometry-judge.py", "triangle", path, reason="duplicate property")
            tri = proposals["triangle"]
            refuse("triangle", [tri[0], tri[0]], "out of range, impossible or duplicate label")
            bad = deepcopy(tri[:1])
            bad[0]["n"] = True
            refuse("triangle", bad, "integer labels")
            refuse("triangle", tri[:-1], "exhaustive allowed count pairs")
            bad = deepcopy(tri[:1])
            bad[0]["kind"] = "open"
            refuse("triangle", bad, "exceptional/open label")
            bad = deepcopy(tri[:1])
            bad[0]["rows"][1] = list(bad[0]["rows"][0])
            refuse("triangle", bad, "distinct component observations")
            upper = deepcopy(proposals["upper"])
            upper[0]["kind"] = "corner"
            refuse("upper", upper, "all anchors at exceptional corner")
            refuse("upper", proposals["upper"][:-1], "upper case count")
    print(json.dumps({"exact_result_sha256": saved, "adverse_refusals": 8 if args.self_test else 0,
                      "altered_reports_rejected": changed_reports},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
