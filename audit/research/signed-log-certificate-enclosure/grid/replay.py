"""Replay the signed final-grid theorems with the recorded Lean 4.34.1 distribution."""

import argparse
import ast
from hashlib import file_digest, sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys


HERE = Path(__file__).resolve().parent
CRITERIA = {
    "v1": "c2ce0183e979cf7a3c6b346b227c8e0987019b6c46ec0a2dcb2471a183ef563e",
    "v2": "cfc713f68bc10120d3e14809314bb46b9f2ae33e84ba59da181f9576c0b71b05",
}
RETURNS = {"v1-r01": False, "v1-r02": False, "v2-r01": False, "v2-r02": False, "v2-r03": True}
EMPTY = sha256(b"").hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def read_json(path):
    return json.loads(path.read_bytes())


def fixed_inputs(out, version):
    fixed = out / version
    fixed.mkdir()
    ident = HERE / "history" / f"criterion-{version}.json"
    require(digest(ident) == CRITERIA[version], "original fixed predicate")
    context = read_json(HERE / "fixed/context.json")
    pins = read_json(ident)
    for name, expected in pins.items():
        path = fixed / name
        require(Path(name).name == name, "stock input name")
        if name in context:
            path.write_bytes(context[name].encode("utf-8"))
        else:
            if name == "Observer.lean" and version == "v1":
                origin = HERE / "history/Observer-v1.lean"
            elif name.endswith(".lean"):
                origin = HERE / name
            else:
                origin = HERE / "fixed" / name
            shutil.copyfile(origin, path)
        require(digest(path) == expected, f"original {version}/{name}")
    shutil.copyfile(ident, fixed / "FROZEN.json")
    return fixed


def relative_arguments(arguments, toolchain, attempt):
    result = []
    for argument in arguments:
        path = Path(argument)
        if path.is_absolute():
            if path.is_relative_to(toolchain):
                argument = "TOOLCHAIN/" + path.relative_to(toolchain).as_posix()
            else:
                require(path.is_relative_to(attempt), "unexpected native argument")
                argument = "ATTEMPT/" + path.relative_to(attempt).as_posix()
        result.append(argument)
    return result


def score(label, fixed, destination, toolchain, stream_map):
    candidate = HERE / "history" / (label + ".json")
    interpreter = [sys.executable, "-I", "-S", "-B"]
    if sys.flags.optimize:
        interpreter.append("-O")
    command = [*interpreter, fixed / "judge.py", candidate, destination, toolchain]
    run = subprocess.run(command, capture_output=True, timeout=240, check=False)
    for name, data in [("stdout", run.stdout), ("stderr", run.stderr)]:
        (destination.parent / f"{destination.name}-judge.{name}").write_bytes(data)
    passed = RETURNS[label]
    require((run.returncode == 0) if passed else (run.returncode > 0), f"{label} judge exit")
    actual = read_json(destination / "RESULT.json")
    require(actual["success"] is passed, f"{label} disposition")
    reference = read_json(HERE / "observed" / (label + ".json"))
    for record in actual["commands"]:
        record["argv"] = relative_arguments(record["argv"], toolchain, destination)
        for suffix in ("stdout", "stderr"):
            path = destination / (record["label"] + "." + suffix)
            ident = digest(path)
            require(ident == record[suffix], "recorded native stream")
            original_bytes = b"" if ident == EMPTY else (HERE / "observed" / stream_map[ident]).read_bytes()
            require(path.read_bytes() == original_bytes, f"{label} actual native output")
    if label == "v2-r01":
        # The historical judge printed an unordered Python set in this failure reason.
        expected = ("GridProof.next_padding", {"propext", "Quot.sound", "Classical.choice"})
        require(ast.literal_eval(actual["reason"]) == ast.literal_eval(reference["reason"]) == expected,
                "original theorem and forbidden axiom")
        actual["reason"] = reference["reason"]
    require(actual == reference, f"{label} native commands, objects, sources, predicates and axioms")
    for group in ("sources", "objects"):
        for name, expected in actual[group].items():
            require(digest(destination / group / name) == expected, f"{label}/{group}/{name}")
    if passed:
        require(len(actual["axioms"]) == 9, "nine declaration records")
        for name in actual["sources"]:
            require(digest(HERE / name) == actual["sources"][name], name)
    return {"candidate": actual["payload"], "predicate": actual["fixed"], "passed": passed,
            "reason": actual["reason"], "commands": len(actual["commands"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--toolchain", required=True, type=Path, help="unpacked official Apple arm64 4.34.1 release")
    parser.add_argument("--out", required=True, type=Path, help="new output directory")
    parser.add_argument("--history", action="store_true", help="also replay the four rejected candidates")
    args = parser.parse_args()
    toolchain = args.toolchain.resolve(strict=True)
    require(toolchain.is_dir(), "toolchain directory")
    out = args.out.resolve()
    out.mkdir(mode=0o700, exist_ok=False)
    manifest = read_json(HERE / "MANIFEST.json")
    files = {p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    require(files == set(manifest) | {"MANIFEST.json"}, "release member set")
    for name, expected in manifest.items():
        require(digest(HERE / name) == expected, name)
    streams = read_json(HERE / "observed/streams.json")
    for ident, name in streams.items():
        require(digest(HERE / "observed" / name) == ident, name)
    trials = {}
    for revision in ("v1", "v2"):
        labels = [label for label, passed in RETURNS.items()
                  if label.startswith(revision + "-") and (passed or args.history)]
        if labels:
            fixed = fixed_inputs(out, revision)
            for label in labels:
                trials[label] = score(label, fixed, out / ("trial-" + label), toolchain, streams)
    print(json.dumps(trials, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
