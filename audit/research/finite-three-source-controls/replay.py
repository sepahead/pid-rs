#!/usr/bin/env python3
"""Recompile the published finite controls using an already provisioned Lean and Mathlib."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


HERE = Path(__file__).resolve().parent
MODULES = ["Contract", "RawTargets", "Candidate", "JudgeCore"]
MODULES.extend(f"Fault{i:02d}" for i in range(1, 13))
MODULES.append("SemanticFaults")


def run(command, *, cwd, env, timeout=120):
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    if result.returncode or result.stderr:
        raise RuntimeError(
            f"{Path(command[0]).name} failed or wrote diagnostics (exit {result.returncode})\n"
            + (result.stdout + result.stderr).decode(errors="replace")
        )
    return result.stdout


def replay(lean_bin, mathlib):
    pins = json.loads((HERE / "observations.json").read_bytes())
    expected = (HERE / "declarations.txt").read_bytes()
    if hashlib.sha256(expected).hexdigest() != pins["accepted_attempt"]["exports_stdout_sha256"]:
        raise ValueError("declarations.txt differs from the recorded declaration stream")
    sources = {source.name: source.read_bytes() for source in (HERE / "lean").glob("*.lean")}
    digests = {name: hashlib.sha256(data).hexdigest() for name, data in sources.items()}
    if set(sources) != {f"{name}.lean" for name in MODULES} or digests != pins["source_sha256"]:
        raise ValueError("the source roster or its hashes differ from observations.json")

    lean = lean_bin / "lean"
    checker = lean_bin / "leanchecker"
    if not lean.is_file() or not checker.is_file():
        raise ValueError("the Lean bin directory must contain lean and leanchecker")
    env = {"PATH": str(lean_bin) + os.pathsep + os.defpath, "LC_ALL": "C"}
    revision = run([lean, "--githash"], cwd=mathlib, env=env).decode().strip()
    version = run([lean, "--version"], cwd=mathlib, env=env).decode()
    if revision != pins["lean"]["revision"] or f"(version {pins['lean']['version']}," not in version:
        raise ValueError("Lean differs from the recorded version or revision")
    manifest = (mathlib / "lake-manifest.json").read_bytes()
    spec = pins["mathlib"]
    if hashlib.sha256(manifest).hexdigest() != spec["lake_manifest_sha256"]:
        raise ValueError("Mathlib's Lake manifest differs from the recorded bytes")

    packages = [(mathlib, spec["revision"])]
    packages.extend((mathlib / ".lake" / "packages" / name, rev)
                    for name, rev in spec["dependencies"].items())
    libraries = []
    for package, required in packages:
        actual = run(["git", "rev-parse", "HEAD"], cwd=package, env=env).decode().strip()
        if actual != required:
            raise ValueError(f"{package.name} has a different Git revision")
        library = package / ".lake" / "build" / "lib" / "lean"
        if library.is_dir():
            libraries.append(str(library))
    if str(mathlib / ".lake" / "build" / "lib" / "lean") not in libraries:
        raise ValueError("the pinned Mathlib checkout needs its prebuilt .olean files")

    with tempfile.TemporaryDirectory(prefix="pid-fin3-replay-") as tmp:
        scratch = Path(tmp).resolve()
        env["LEAN_PATH"] = os.pathsep.join([str(scratch), *libraries])
        for filename, data in sources.items():
            (scratch / filename).write_bytes(data)
        for module in MODULES:
            emitted = run([lean, "-j1", "-o", f"{module}.olean", f"{module}.lean"],
                          cwd=scratch, env=env)
            required = expected if module == "SemanticFaults" else b""
            if emitted != required:
                raise ValueError(f"{module} emitted a different declaration stream")
        emitted = run([checker, "--fresh", "SemanticFaults"], cwd=scratch, env=env, timeout=600)
        if emitted:
            raise ValueError("fresh checking emitted unexpected output")
    print("17 modules compiled; 24 declaration rows matched; fresh SemanticFaults replay passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean-bin", type=Path, required=True)
    parser.add_argument("--mathlib", type=Path, required=True)
    args = parser.parse_args()
    try:
        replay(args.lean_bin.resolve(), args.mathlib.resolve())
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as err:
        sys.exit(str(err))
