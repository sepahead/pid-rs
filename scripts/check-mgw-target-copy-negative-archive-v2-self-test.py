#!/usr/bin/env python3
"""Causal subprocess checks for the inert target-copy archive gate."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = "audit/archive/mgw-target-copy-development-20260911"
CHECKER = "scripts/check-mgw-target-copy-negative-archive-v2.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    os.umask(0o022)
    source = (ROOT / CHECKER).read_bytes()
    manifest_bytes = (ROOT / ARCHIVE / "MANIFEST-v2.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    payload = "payloads/sources/Interface.lean.txt"
    cases = [
        ("missing terminal newline", "payload digest mismatch"),
        ("changed payload", "payload digest mismatch"),
        ("missing payload", "missing payload file"),
        ("extra payload", "unexpected payload"),
        ("symbolic payload", "single-link regular file"),
        ("hardlinked payload", "single-link regular file"),
        ("executable payload", "unexpected file mode"),
        ("symbolic directory", "symbolic archive directory"),
        ("special payload", "single-link regular file"),
        ("symbolic manifest", "single-link regular file"),
        ("duplicate JSON key", "duplicate JSON key"),
        ("wrong schema", "unexpected schema"),
        ("wrong status", "unexpected archive status"),
        ("duplicate artifact id", "duplicate or invalid artifact id"),
        ("duplicate complete artifact", "duplicate or invalid artifact id"),
        ("duplicate artifact path", "duplicate artifact path"),
        ("parent traversal", "unsafe or non-inert payload path"),
        ("absolute path", "unsafe or non-inert payload path"),
        ("noncanonical path", "unsafe or non-inert payload path"),
        ("executable suffix", "unsafe or non-inert payload path"),
        ("boolean byte count", "invalid integer bytes"),
        ("floating byte count", "invalid integer bytes"),
        ("negative byte count", "invalid integer bytes"),
        ("invalid raw hash", "invalid digest raw_sha256"),
        ("unredacted raw mismatch", "unredacted payload must equal raw commitment"),
        ("boolean theorem count", "archive cannot grant theorem credit"),
        ("nonzero theorem count", "archive cannot grant theorem credit"),
        ("duplicate route id", "duplicate route id"),
        ("wrong source association", "route/raw-artifact digest mismatch"),
        ("wrong diagnostic association", "route/raw-artifact digest mismatch"),
        ("missing run record", "missing run-record artifact"),
        ("missing command record", "missing command-record artifact"),
        ("changed omission", "frozen v2 manifest bytes differ"),
        ("nonfinite JSON", "nonfinite JSON constant"),
    ]
    baselines = failures = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-mgw-archive-controls-") as temporary:
        for optimized in (False, True):
            for name, expected in [("baseline", ""), *cases]:
                fixture = Path(temporary) / f"case-{baselines + failures}"
                archive = fixture / ARCHIVE
                shutil.copytree(ROOT / ARCHIVE, archive)
                (fixture / "scripts").mkdir()
                (fixture / CHECKER).write_bytes(source)
                record = copy.deepcopy(manifest)
                target = archive / payload
                item = record["artifacts"][0]
                changed_json = False
                if name == "missing terminal newline":
                    raw = target.read_bytes()
                    require(raw.endswith(b"\n\n"), "Interface baseline lost original terminal bytes")
                    target.write_bytes(raw[:-1])
                elif name == "changed payload":
                    target.write_bytes(target.read_bytes().replace(b"Prop", b"Type", 1))
                elif name == "missing payload":
                    target.unlink()
                elif name == "extra payload":
                    (archive / "payloads/unlisted.txt").write_text("unlisted\n")
                elif name in ("symbolic payload", "hardlinked payload"):
                    kept = fixture / "kept.txt"
                    target.rename(kept)
                    if name == "symbolic payload":
                        target.symlink_to(kept)
                    else:
                        os.link(kept, target)
                elif name == "executable payload":
                    target.chmod(0o755)
                elif name == "symbolic directory":
                    directory = archive / "payloads/sources"
                    moved = fixture / "sources"
                    directory.rename(moved)
                    directory.symlink_to(moved, target_is_directory=True)
                elif name == "special payload":
                    target.unlink()
                    os.mkfifo(target)
                elif name == "symbolic manifest":
                    path = archive / "MANIFEST-v2.json"
                    moved = fixture / "manifest.json"
                    path.rename(moved)
                    path.symlink_to(moved)
                elif name == "duplicate JSON key":
                    (archive / "MANIFEST-v2.json").write_bytes(
                        manifest_bytes.replace(b'{', b'{"schema":"discarded",', 1))
                elif name == "nonfinite JSON":
                    (archive / "MANIFEST-v2.json").write_bytes(
                        manifest_bytes.replace(b'"accepted_target_proofs": 0',
                                               b'"accepted_target_proofs": NaN', 1))
                elif name != "baseline":
                    changed_json = True
                    if name == "wrong schema": record["schema"] = "wrong"
                    elif name == "wrong status": record["status"] = "accepted"
                    elif name == "duplicate artifact id": record["artifacts"][1]["id"] = item["id"]
                    elif name == "duplicate complete artifact": record["artifacts"][1] = dict(item)
                    elif name == "duplicate artifact path": record["artifacts"][1]["path"] = item["path"]
                    elif name == "parent traversal": item["path"] = "payloads/../../escape.txt"
                    elif name == "absolute path": item["path"] = "/outside.txt"
                    elif name == "noncanonical path": item["path"] = "payloads//sources/L1.txt"
                    elif name == "executable suffix": item["path"] = "payloads/run.py"
                    elif name == "boolean byte count": item["bytes"] = True
                    elif name == "floating byte count": item["bytes"] = float(item["bytes"])
                    elif name == "negative byte count": item["bytes"] = -1
                    elif name == "invalid raw hash": item["raw_sha256"] = "x" * 64
                    elif name == "unredacted raw mismatch": item["raw_sha256"] = "0" * 64
                    elif name == "boolean theorem count": record["routes"][0]["accepted_target_proofs"] = False
                    elif name == "nonzero theorem count": record["routes"][0]["accepted_target_proofs"] = 1
                    elif name == "duplicate route id": record["routes"][1]["id"] = record["routes"][0]["id"]
                    elif name == "wrong source association": record["routes"][0]["source_sha256"] = "0" * 64
                    elif name == "wrong diagnostic association": record["routes"][0]["diagnostic_sha256"] = "0" * 64
                    elif name == "missing run record": record["routes"][0]["run_records"]["driver.py"] = "absent"
                    elif name == "missing command record": record["routes"][0]["commands"][0]["records"]["stdout"] = "absent"
                    elif name == "changed omission": record["omissions"][0] = "All history independently verified."
                    else: raise RuntimeError(f"unimplemented mutation: {name}")
                if changed_json:
                    (archive / "MANIFEST-v2.json").write_text(json.dumps(record, indent=2) + "\n")
                argv = [sys.executable, *(["-O"] if optimized else []),
                        "-I", "-S", "-B", str(fixture / CHECKER)]
                run = subprocess.run(argv, capture_output=True, timeout=15, cwd=fixture)
                if name == "baseline":
                    require(run.returncode == 0 and not run.stderr
                            and b"6 routes and 81 redacted payloads" in run.stdout,
                            f"baseline failed: {run.stderr!r}")
                    baselines += 1
                else:
                    require(run.returncode == 1 and not run.stdout
                            and expected.encode() in run.stderr,
                            f"{name} (optimized={optimized}) failed causally: {run.returncode} {run.stderr!r}")
                    failures += 1
        # Actual committed checker must still be the one exercised in every fixture.
        require((ROOT / CHECKER).read_bytes() == source, "checker changed during self-test")
        require((ROOT / ARCHIVE / "MANIFEST-v2.json").read_bytes() == manifest_bytes,
                "manifest changed during self-test")
    print(f"OK: {baselines} baselines and {failures} causal archive rejections "
          f"({len(cases)} cases in both Python modes); no historical execution credit")


if __name__ == "__main__":
    main()
