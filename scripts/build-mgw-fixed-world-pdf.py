#!/usr/bin/env python3
"""Build the finite MGW v7 paper; discovery is not reference adoption.

Uses the existing bounded Runner/Snapshot without proof or preparation hooks.
Pins the finite source map and nine theorem modules without executing Lean.
Native dependencies are a proposed recorded profile, not a hermetic closure.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import time
from types import ModuleType
from xml.sax.saxutils import escape

ASSETS = "audit/formal/latex/mgw-fixed-world/"
FIGURES = "audit/formal/latex/figures/mgw-fixed-world/"
EVIDENCE = "audit/evidence/mgw-fixed-world-added-information-2026-09-09/"
UNIT = "audit/formal/lean-mgw-fixed-world/"
MARKDOWN = EVIDENCE[:-1] + ".md"
PDF = "output/pdf/mgw-fixed-world-added-information.pdf"
JOBNAME = "mgw-fixed-world"
FIGURE_NAMES = ("observation-maps", "shared-exclusion-events", "mgw-matched-comparison")
REQUIRED_RECORDED_LOCAL = frozenset({
    "publication.tex", "body.tex", "pid-rs-report-tables.sty",
    "pid-rs-workflow-publication.sty", *(name + ".pdf" for name in FIGURE_NAMES),
})
MANIFEST = ASSETS + "publication-inputs-v1.json"
MANIFEST_SHA = "6b98817dc2367eab36c3ba6cb4a1566929f91ceb4d9494bf424470f153804d28"
RUNTIME = "audit/formal/lean-prefix-mgw-mean/replay-support/runtime.py"
RUNTIME_SHA = "bd8a9f2272a20422863c9902ce2148d2957471bb958d13949fece923cb6a7f5d"
EXPECTED_PDF_SHA = "24c16b51c970d9cec8847f923d76f0d7e8a0bd137f54512e028de0e2712ec378"
EXPECTED_PDF_BYTES = 231798
EXPECTED_PDF_PAGES = 9  # Prior inspected reference; no PDF page parser runs here.
EXPECTED_MARKDOWN_SHA = "01f12cf08104181b88b7d842bf275cfdd68db4d5a087348f0a0c2e667d2a7abf"
EXPECTED_BODY_SHA = "e725b0186210a3bacd04d2fc85e9cb29f26d00c029d39738bc20501d7df54b88"
EXPECTED_MAP_SHA = "b579fbbf742c84844519b4ccab85cfb5757a28985308f8496ae5bdacdcc78744"
EXPECTED_GRAPH_SHA = "11a229b232d7b605fe5ec5e83b4c5c36d50e7fc7dbd79991cd5e5e45c38fe9f0"
SOURCE_MAP = EVIDENCE + "source-map.json"
SOURCE_GRAPH = UNIT + "SOURCE_GRAPH.json"
ARCHIVE_FILES = frozenset({
    "audit/evidence/mgw-fixed-world-added-information-2026-09-09.md",
    "audit/evidence/mgw-fixed-world-added-information-2026-09-09/target-report.json",
    "audit/formal/latex/figures/mgw-fixed-world/mgw-matched-comparison.pdf",
    "audit/formal/latex/figures/mgw-fixed-world/mgw-matched-comparison.svg",
    "audit/formal/latex/figures/mgw-fixed-world/observation-maps.pdf",
    "audit/formal/latex/figures/mgw-fixed-world/observation-maps.svg",
    "audit/formal/latex/figures/mgw-fixed-world/shared-exclusion-events.pdf",
    "audit/formal/latex/figures/mgw-fixed-world/shared-exclusion-events.svg",
    "audit/formal/latex/mgw-fixed-world/filter.lua",
    "audit/formal/latex/mgw-fixed-world/publication.tex",
    "audit/formal/lean-mgw-fixed-world/EVIDENCE.md",
    "audit/formal/lean-mgw-fixed-world/HISTORICAL_EXECUTION.json",
    "audit/formal/lean-mgw-fixed-world/LATER_EXECUTION.json",
    "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Contract.lean",
    "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Judge.lean",
    "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/RawTargets.lean",
    "audit/formal/lean-mgw-fixed-world/REPLAY.md",
    "audit/formal/lean-mgw-fixed-world/SOURCE_GRAPH.json",
    "audit/formal/lean-mgw-fixed-world/evidence/later-01.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-01.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-02.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-02.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-03.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-03.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-04.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-04.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-05.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-05.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-06.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-06.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-07.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-07.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-08.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-08.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-09.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-09.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/later-10.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/later-10.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-01.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-01.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-02.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-02.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-03.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-03.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-04.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-04.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-05.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-05.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-06.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-06.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-07.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-07.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-08.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-08.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-09.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-09.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-10.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-10.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-11.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-11.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-12.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-12.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-13.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-13.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-14.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-14.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-15.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-15.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-16.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-16.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/original-17.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/original-17.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-01.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-01.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-02.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-02.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-03.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-03.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-04.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-04.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-05.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-05.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-06.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-06.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-07.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-07.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-08.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-08.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-09.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-09.stdout",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-10.stderr",
    "audit/formal/lean-mgw-fixed-world/evidence/suffix-10.stdout",
    "audit/formal/lean-mgw-fixed-world/negative/original-M01/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/original-M02/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/original-M03/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/original-M04/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M04/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M05/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M06/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M07/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M07/PidMgwFixedWorld/NegativeHelper.lean",
    "audit/formal/lean-mgw-fixed-world/negative/suffix-M08/PidMgwFixedWorld/Candidate.lean",
    "audit/formal/lean-mgw-fixed-world/replay-support/STATIC_CONTROL_PLAN_V2.json",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/judge_report_validation.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/observe-installed-post.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/observe-installed.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/prepare.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/run-one.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/runtime.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/adapter-v2/static-controls.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/installed-profile-macos-arm64-v1.json.gz",
    "audit/formal/lean-mgw-fixed-world/replay-support/negative/preparation-v1/DISPOSITION.json",
    "audit/formal/lean-mgw-fixed-world/replay-support/negative/preparation-v1/prepare.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/negative/preparation-v1/run-one.py",
    "audit/formal/lean-mgw-fixed-world/replay-support/static-normal-v2.json",
    "audit/formal/lean-mgw-fixed-world/replay-support/static-optimized-v2.json",
})
FROZEN_MODULES = [
    {
        "bytes": 9093,
        "imports": [
            "Mathlib.Analysis.SpecialFunctions.Log.NegMulLog"
        ],
        "module": "PidFiniteConvergence.Deterministic",
        "repository_path": "audit/formal/lean/PidFiniteConvergence/Deterministic.lean",
        "sha256": "e9dbd7c5b4578aabf92b76c0b8b684db4c1c1038dcdb033239b0076685c41610"
    },
    {
        "bytes": 27203,
        "imports": [
            "PidFiniteConvergence.Deterministic",
            "Mathlib.Data.Fintype.Pi"
        ],
        "module": "PidFiniteConvergence.SxEventBridge",
        "repository_path": "audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean",
        "sha256": "cfedf974c73e11e56041013a47797462100f4b896235d6c4185c9ca0a232d77e"
    },
    {
        "bytes": 25943,
        "imports": [
            "PidFiniteConvergence.SxEventBridge"
        ],
        "module": "PidFiniteConvergence.FractionalCover",
        "repository_path": "audit/formal/lean/PidFiniteConvergence/FractionalCover.lean",
        "sha256": "4ea504a565a69f5222c205e01050b750e780ed17cb02558fe08e0c32e2f5718c"
    },
    {
        "bytes": 24105,
        "imports": [
            "PidFiniteConvergence.FractionalCover"
        ],
        "module": "PidFiniteConvergence.TwoSourceCountEventBridge",
        "repository_path": "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean",
        "sha256": "fa3a1c5450648da4c4768dbd88e261abf1bcd3051f5af4526a63631c83f8648a"
    },
    {
        "bytes": 47567,
        "imports": [
            "PidFiniteConvergence.TwoSourceCountEventBridge"
        ],
        "module": "PidFiniteConvergence.TwoSourceMobiusAtomBridge",
        "repository_path": "audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean",
        "sha256": "bc282ca506f50ac5af661b87b166cc76561a4da308ffe39892ad8df7f2fd875e"
    },
    {
        "bytes": 4117,
        "imports": [
            "PidFiniteConvergence.TwoSourceMobiusAtomBridge"
        ],
        "module": "PidMgwFixedWorld.Contract",
        "repository_path": "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Contract.lean",
        "sha256": "d5e34836c52bead88f6279d63ea7c4261613ebe5455e3986d2ef333b15490df9"
    },
    {
        "bytes": 3238,
        "imports": [
            "PidMgwFixedWorld.Contract"
        ],
        "module": "PidMgwFixedWorld.RawTargets",
        "repository_path": "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/RawTargets.lean",
        "sha256": "308c379003168dc89fffc3a40cb47923489f573ed79bbd4500b0163f1eb7ed76"
    },
    {
        "bytes": 20329,
        "imports": [
            "PidMgwFixedWorld.RawTargets"
        ],
        "module": "PidMgwFixedWorld.Candidate",
        "repository_path": "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Candidate.lean",
        "sha256": "ebcb137d87aac64569ac9ec055eb5839e8f252fdf0913490f1efe761956cd4a4"
    },
    {
        "bytes": 6067,
        "imports": [
            "PidMgwFixedWorld.RawTargets",
            "PidMgwFixedWorld.Candidate",
            "Lean",
            "Lean.Util.CollectAxioms"
        ],
        "module": "PidMgwFixedWorld.Judge",
        "repository_path": "audit/formal/lean-mgw-fixed-world/PidMgwFixedWorld/Judge.lean",
        "sha256": "ac55f846665e3016736b9f9cc0f07e876d639cdafdbda9041829cb07794317bb"
    }
]
SOURCE_FILES = ARCHIVE_FILES | frozenset({
    "METHODS.md",
    "audit/evidence/mgw-fixed-world-added-information-2026-09-09/source-map.json",
    "audit/evidence/real-occupancy-sensors-example-2026-09-08.md",
    "audit/formal/latex/mgw-fixed-world/body.expected.tex",
    "audit/formal/latex/pid-rs-report-tables.sty",
    "audit/formal/latex/pid-rs-workflow-publication.sty",
    "audit/formal/lean-prefix-mgw-mean/replay-support/runtime.py",
    "audit/formal/lean/PidFiniteConvergence/Deterministic.lean",
    "audit/formal/lean/PidFiniteConvergence/FractionalCover.lean",
    "audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean",
    "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean",
    "audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean",
    "scripts/check-formal-pdf-log.sh",
})
HEX = re.compile(r"[0-9a-f]{64}\Z")
PRIMARY_SECONDS = 120
TOTAL_SECONDS = 900
STREAM_BYTES = 4 * 1024**2
RSS_BYTES = 4 * 1024**3
DISK_KIB = 2 * 1024**2


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def record(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def direct_directory(path: Path) -> Path:
    path = path.absolute()
    require(path == path.resolve(strict=True) and path.is_dir(),
            "directory must be canonical and free of symlink components")
    return path


def bootstrap(path: Path) -> bytes:
    """Capture the one pinned runtime before executing its module definitions."""
    direct_directory(path.parent)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            "runtime must be a direct single-link regular file")
    require(before.st_size <= 128 * 1024, "runtime source exceeds bootstrap bound")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    identity = lambda s: (s.st_dev, s.st_ino, s.st_mode, s.st_nlink,
                          s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    require(identity(before) == identity(opened) == identity(after)
            == identity(path.lstat()) and len(raw) == before.st_size,
            "runtime changed during capture")
    require(sha(raw) == RUNTIME_SHA, "runtime digest changed")
    return raw


def load_runtime(path: Path) -> ModuleType:
    raw = bootstrap(path)
    module = ModuleType("finite_mgw_publication_runtime")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True,
                 optimize=sys.flags.optimize), module.__dict__)
    return module


def relative_path(value: object) -> str:
    require(type(value) is str and bool(value) and "\\" not in value,
            "unsafe profile path")
    path = PurePosixPath(value)
    require(not path.is_absolute() and ".." not in path.parts
            and str(path) == value and ":" not in value,
            "unsafe profile path")
    return value


def validate_pin(pin: object, label: str) -> None:
    require(type(pin) is dict and set(pin) == {"sha256", "bytes", "mode"}
            and type(pin["bytes"]) is int and pin["bytes"] >= 0
            and type(pin["sha256"]) is str and HEX.fullmatch(pin["sha256"])
            and type(pin["mode"]) is str and re.fullmatch(r"0o[0-7]{3,4}", pin["mode"]),
            "malformed pin: " + label)


def check_pin(raw: bytes, pin: object, label: str, path: Path) -> None:
    validate_pin(pin, label)
    require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"],
            "input digest changed: " + label)
    require(oct(stat.S_IMODE(path.lstat().st_mode)) == pin["mode"],
            "input mode changed: " + label)


def read_pinned(snapshot: object, path: Path, pin: object, label: str) -> bytes:
    validate_pin(pin, label)
    before = path.lstat()
    require(before.st_size == pin["bytes"], "input size changed: " + label)
    require(oct(stat.S_IMODE(before.st_mode)) == pin["mode"], "input mode changed: " + label)
    raw = snapshot.read(path)
    check_pin(raw, pin, label, path)
    return raw


def verify_finite_sources(sources: dict[str, bytes], runtime: ModuleType) -> dict:
    """Join frozen paper/archive/module bytes; this never executes or proves Lean."""
    for path, expected, label in (
        (MARKDOWN, EXPECTED_MARKDOWN_SHA, "Markdown"),
        (ASSETS + "body.expected.tex", EXPECTED_BODY_SHA, "body expectation"),
        (SOURCE_MAP, EXPECTED_MAP_SHA, "source map"),
        (SOURCE_GRAPH, EXPECTED_GRAPH_SHA, "source graph"),
    ):
        require(sha(sources[path]) == expected, "finite paper " + label + " identity changed")
    source_map = runtime.strict_json(sources[SOURCE_MAP])
    require(type(source_map) is dict and type(source_map.get("files")) is dict
            and set(source_map["files"]) == ARCHIVE_FILES,
            "finite archive source-map roster changed")
    for relative, pin in source_map["files"].items():
        require(type(pin) is dict and set(pin) == {"bytes", "sha256"}
                and type(pin["bytes"]) is int and pin["bytes"] >= 0
                and type(pin["sha256"]) is str and HEX.fullmatch(pin["sha256"]),
                "malformed finite source-map pin: " + relative)
        raw = sources[relative_path(relative)]
        require(len(raw) == pin["bytes"] and sha(raw) == pin["sha256"],
                "finite archive source-map join changed: " + relative)
    graph = runtime.strict_json(sources[SOURCE_GRAPH])
    require(type(graph) is dict and graph.get("schema") == "pid-rs/mgw-fixed-world-source-graph-v1"
            and graph.get("modules_in_compile_order") == FROZEN_MODULES,
            "finite nine-module graph changed")
    for item in FROZEN_MODULES:
        relative = item["repository_path"]
        raw = sources[relative]
        require(len(raw) == item["bytes"] and sha(raw) == item["sha256"],
                "finite theorem source changed: " + relative)
    return {"scope": "exact archival source joins only; no kernel, solver or theorem replay",
            "source_map_entries": len(ARCHIVE_FILES), "project_modules": len(FROZEN_MODULES),
            "markdown_sha256": EXPECTED_MARKDOWN_SHA, "source_map_sha256": EXPECTED_MAP_SHA,
            "source_graph_sha256": EXPECTED_GRAPH_SHA}


def verify_recorder(build: Path, tex_root: Path, profile: dict, snapshot: object) -> None:
    """Require the recorded paper inputs and reject undeclared recorder inputs.

    The seven required local inputs occur in both retained v7 recorder files.
    This is a bounded recorder check, not independent observation of native reads.
    """
    allowed_local = {"publication.tex", "body.tex", "pid-rs-report-tables.sty",
                     "pid-rs-workflow-publication.sty",
                     *(name + ".pdf" for name in FIGURE_NAMES),
                     *(JOBNAME + suffix for suffix in (".aux", ".out", ".toc"))}
    recorded_local = set()
    for line in (build / (JOBNAME + ".fls")).read_text().splitlines():
        if not line.startswith("INPUT "):
            continue
        path = Path(line[6:])
        path = path if path.is_absolute() else build / path
        path = path.resolve(strict=True)
        if path.is_relative_to(tex_root):
            relative = str(path.relative_to(tex_root))
            require(relative in profile["tex_files"], "undeclared TeX input: " + relative)
            read_pinned(snapshot, path, profile["tex_files"][relative], relative)
        elif path.is_relative_to(build):
            relative = path.relative_to(build)
            recorded_local.add(str(relative))
            require(str(relative) in allowed_local
                    or relative.parts[0] in {"cache", "fonts", "texmf-var"},
                    "undeclared local TeX input: " + str(relative))
        else:
            raise RuntimeError("TeX recorder input outside captured roots: " + str(path))
    require(REQUIRED_RECORDED_LOCAL <= recorded_local,
            "TeX recorder omits required local inputs: "
            + ", ".join(sorted(REQUIRED_RECORDED_LOCAL - recorded_local)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--work-dir", type=Path, help="fresh, retained directory")
    parser.add_argument("--output", type=Path, help="new output; never the canonical reference")
    parser.add_argument("--tex-root", type=Path, help="canonical selected TeX Live root")
    parser.add_argument("--check", action="store_true", help="make two fresh builds")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--discover", action="store_true")
    modes.add_argument("--exact", action="store_true")
    modes.add_argument("--cross-toolchain", action="store_true")
    args = parser.parse_args(argv)
    if args.cross_toolchain:
        print("Finite MGW: no reviewed cross-toolchain relation; status 2 refusal.",
              file=sys.stderr)
        return 2
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires Python 3.11+ -I -S -B, optionally -O")
    require(args.work_dir is not None and args.tex_root is not None,
            "build requires --work-dir and --tex-root")
    work = args.work_dir.absolute()
    direct_directory(work.parent)
    require(not work.exists() and not work.is_symlink(), "work directory already exists")
    work.mkdir(mode=0o700)
    started, started_ns = now(), time.monotonic_ns()
    deadline, deadline_ns = started + dt.timedelta(seconds=TOTAL_SECONDS), started_ns + TOTAL_SECONDS * 10**9
    result = {"status": "failed", "started_utc": started.isoformat(),
              "start_monotonic_ns": started_ns, "deadline_utc": deadline.isoformat(),
              "deadline_monotonic_ns": deadline_ns, "mode": "exact" if args.exact else "discovery",
              "scope": "document bytes only; no scientific or visual adoption",
              "disk_policy": "pre/post samples; no hard quota or cadence guarantee"}
    snapshot = None
    runners = []
    disk_count = 0
    try:
        root, tex_root = direct_directory(args.root), direct_directory(args.tex_root)
        output = None if args.output is None else args.output.absolute()
        if output is not None:
            direct_directory(output.parent)
            require(not output.is_relative_to(work) and output != root / PDF
                    and not output.exists() and not output.is_symlink(),
                    "output must be a new path outside work and distinct from the canonical reference")
        runtime = load_runtime(root / RUNTIME)
        snapshot = runtime.Snapshot()
        require(sha(snapshot.read(root / RUNTIME)) == RUNTIME_SHA, "runtime changed after load")
        snapshot.read(Path(__file__).absolute())
        require((root / MANIFEST).lstat().st_size <= 1024**2, "publication manifest exceeds source bound")
        manifest_raw = snapshot.read(root / MANIFEST)
        require(sha(manifest_raw) == MANIFEST_SHA, "publication manifest digest changed")
        profile = runtime.strict_json(manifest_raw)
        require(type(profile) is dict and profile["schema"] == "pid-rs/mgw-fixed-world-publication-v1"
                and set(profile["files"]) == SOURCE_FILES,
                "publication source roster changed")
        require(profile["profile"] == "darwin-arm64-texlive-2024-pandoc-3.10.2"
                and profile["source_epoch"] == "1788912000", "unsupported publication profile")
        require(set(profile) == {"schema", "profile", "source_epoch", "scope", "reference",
                "expected_document", "body_expectation", "input_observation_scope", "font_lookup_scope",
                "files", "tex_files", "fonts", "tools"}, "publication profile key roster changed")
        expected_document = {"path": PDF, "sha256": EXPECTED_PDF_SHA,
                             "bytes": EXPECTED_PDF_BYTES, "reported_pages": EXPECTED_PDF_PAGES}
        require(type(profile["expected_document"]) is dict
                and type(profile["expected_document"].get("bytes")) is int
                and type(profile["expected_document"].get("reported_pages")) is int
                and profile["expected_document"] == expected_document,
                "finite expected PDF identity changed")
        reference = profile["reference"]
        require(type(reference) is dict and set(reference) == {"status", "sha256"}
                and reference["status"] in {"pending", "admitted"}, "invalid reference state")
        require((reference["status"] == "pending" and reference["sha256"] is None)
                or (reference["status"] == "admitted" and reference["sha256"] == EXPECTED_PDF_SHA),
                "reference must be pending or admit only the fixed finite PDF")
        if args.exact:
            require(reference["status"] == "admitted"
                    and type(reference["sha256"]) is str and HEX.fullmatch(reference["sha256"]),
                    "exact reference is pending; use discovery without adoption credit")
            reference_bytes = snapshot.read(root / PDF)
            require(len(reference_bytes) == EXPECTED_PDF_BYTES
                    and sha(reference_bytes) == EXPECTED_PDF_SHA, "admitted reference changed")
        else:
            reference_bytes = None
        sources = {}
        for relative, pin in profile["files"].items():
            data = read_pinned(snapshot, root / relative_path(relative), pin, relative)
            sources[relative] = data
        finite_bindings = verify_finite_sources(sources, runtime)
        record(work / "FINITE_SOURCE_BINDINGS.json", finite_bindings)
        require(type(profile["tex_files"]) is dict and bool(profile["tex_files"]),
                "missing recorded TeX profile")
        for relative, pin in profile["tex_files"].items():
            path = tex_root / relative_path(relative)
            read_pinned(snapshot, path, pin, relative)
        require(set(profile["fonts"]) == {
                "SourceSansPro-Bold.otf",
                "SourceSansPro-Regular.otf",
                "SourceSansPro-RegularIt.otf",
                "SourceSansPro-Semibold.otf",
                "SourceSansPro-SemiboldIt.otf",
                "latinmodern-math.otf",
                "lmmono10-italic.otf",
                "lmmono10-regular.otf",
                "lmmonolt10-bold.otf",
                "lmmonolt10-boldoblique.otf",
                "lmroman10-bold.otf",
                "lmroman10-bolditalic.otf",
                "lmroman10-italic.otf",
                "lmroman10-regular.otf",
                "lmroman12-bold.otf",
                "lmroman12-regular.otf",
                }, "controlled font roster changed")
        for relative in profile["fonts"].values():
            require(relative_path(relative) in profile["tex_files"], "unbound controlled font")
        require(set(profile["tools"]) == {"pandoc", "lualatex", "bash", "python", "du", "ps"},
                "tool roster changed")
        selectors = {"python": sys.executable, "bash": "/bin/bash", "du": "/usr/bin/du", "ps": "/bin/ps"}
        for name in ("pandoc", "lualatex"):
            selected = shutil.which(name)
            require(selected is not None and Path(selected).is_absolute(), "missing tool: " + name)
            selectors[name] = selected
        targets = {name: Path(path).resolve(strict=True) for name, path in selectors.items()}
        for name, path in targets.items():
            read_pinned(snapshot, path, profile["tools"][name], "tool " + name)
        snapshot.save(work)
        record(work / "INPUTS.json", snapshot.manifest())

        build_snapshot = None

        def guard() -> None:
            require(now() < deadline - dt.timedelta(seconds=15)
                    and time.monotonic_ns() < deadline_ns - 15 * 10**9,
                    "publication original deadline exhausted")
            snapshot.verify()
            if build_snapshot is not None:
                build_snapshot.verify()
            require(all(Path(selectors[name]).resolve(strict=True) == target
                        for name, target in targets.items()), "tool selector changed")
            require(now() < deadline - dt.timedelta(seconds=15)
                    and time.monotonic_ns() < deadline_ns - 15 * 10**9,
                    "publication original deadline exhausted during input checks")

        def disk(phase: str) -> None:
            nonlocal disk_count
            disk_count += 1
            require(disk_count <= 20, "disk observation roster exceeded")
            completed = subprocess.run([selectors["du"], "-sk", str(work)],
                stdin=subprocess.DEVNULL, capture_output=True, timeout=5, check=False,
                env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"})
            row = {"phase": phase, "utc": now().isoformat(), "monotonic_ns": time.monotonic_ns(),
                   "returncode": completed.returncode, "stdout": completed.stdout.decode(),
                   "stderr": completed.stderr.decode()}
            record(work / ("DISK-%02d.json" % disk_count), row)
            require(completed.returncode == 0 and not completed.stderr, "disk observation failed")
            require(int(completed.stdout.split()[0]) <= DISK_KIB, "sampled disk limit exceeded")

        produced = []
        for index in range(2 if args.check else 1):
            guard()
            build = work / ("build-" + str(index + 1))
            build.mkdir(mode=0o700)
            for name in ("tmp", "cache", "texmf-var", "texmf-config", "fonts", "font-cache", "execution"):
                (build / name).mkdir(mode=0o700)
            (build / "cache/luatex-cache/generic/names").mkdir(parents=True)
            (build / "cache/luatex-cache/generic/fonts/otl").mkdir(parents=True)
            for name, relative in profile["fonts"].items():
                (build / "fonts" / name).write_bytes(snapshot.read(tex_root / relative))
            for relative, name in (
                (ASSETS + "publication.tex", "publication.tex"), (ASSETS + "filter.lua", "filter.lua"),
                (MARKDOWN, "body.md"),
                *((FIGURES + name + ".pdf", name + ".pdf") for name in FIGURE_NAMES),
                ("audit/formal/latex/pid-rs-report-tables.sty", "pid-rs-report-tables.sty"),
                ("audit/formal/latex/pid-rs-workflow-publication.sty", "pid-rs-workflow-publication.sty"),
            ):
                (build / name).write_bytes(sources[relative])
            (build / "fonts.conf").write_text(
                '<?xml version="1.0"?>\n<fontconfig><dir>' + escape(str(build / "fonts"))
                + '</dir><cachedir>' + escape(str(build / "font-cache"))
                + '</cachedir><alias><family>Arial</family><prefer><family>Source Sans Pro</family>'
                  '</prefer></alias><alias><family>sans-serif</family><prefer><family>Source Sans Pro'
                  '</family></prefer></alias><config></config></fontconfig>\n')
            environment = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TEXINPUTS": str(build) + ":", "TEXMFVAR": str(build / "texmf-var"),
                "TEXMFCONFIG": str(build / "texmf-config"), "TEXMFCACHE": str(build / "cache"),
                "TEXMFOUTPUT": str(build), "SOURCE_DATE_EPOCH": profile["source_epoch"],
                "FORCE_SOURCE_DATE": "1", "FONTCONFIG_FILE": str(build / "fonts.conf"),
                "FONTCONFIG_PATH": str(build), "PANGOCAIRO_BACKEND": "fc",
                "OSFONTDIR": str(build / "fonts"), "TMPDIR": str(build / "tmp")}
            record(build / "ENVIRONMENT.json", environment)
            build_snapshot = runtime.Snapshot()
            for name in ("publication.tex", "filter.lua", "body.md",
                         *(name + ".pdf" for name in FIGURE_NAMES), "pid-rs-report-tables.sty",
                         "pid-rs-workflow-publication.sty", "fonts.conf"):
                build_snapshot.read(build / name)
            for name in profile["fonts"]:
                build_snapshot.read(build / "fonts" / name)
            record(build / "COPY_INPUTS.json", build_snapshot.manifest())
            runner = runtime.Runner(build / "execution", environment, preparation=False)
            runners.append(runner)

            def run(command: list[str], label: str) -> None:
                guard()
                disk(label + " before")
                remaining = (deadline_ns - time.monotonic_ns()) / 10**9 - 15
                require(remaining > 0, "publication original deadline exhausted")
                runner.run(command, build, label, timeout=min(PRIMARY_SECONDS, remaining),
                           cap=STREAM_BYTES, memory=RSS_BYTES, allow_stdout=True)
                guard()
                disk(label + " after")

            run([selectors["pandoc"], str(build / "body.md"), "--from=markdown", "--to=latex",
                 "--wrap=none", "--lua-filter", str(build / "filter.lua"),
                 "--output", str(build / "body.tex")], "pandoc")
            require(build_snapshot.read(build / "body.tex") == sources[ASSETS + "body.expected.tex"],
                    "generated TeX differs from the pinned canonical projection")
            record(build / "BODY_INPUT.json", {"body.tex": {
                "sha256": sha(sources[ASSETS + "body.expected.tex"]),
                "bytes": len(sources[ASSETS + "body.expected.tex"])}})
            for number in (1, 2):
                run([selectors["lualatex"], "-no-shell-escape", "-interaction=nonstopmode",
                     "-halt-on-error", "-file-line-error", "-recorder",
                     "-jobname=" + JOBNAME, "publication.tex"], "lualatex-" + str(number))
                verify_recorder(build, tex_root, profile, snapshot)
                log_command = [selectors["bash"], str(root / "scripts/check-formal-pdf-log.sh")]
                if number == 1:
                    log_command.append("--intermediate")
                run(log_command + [str(build / (JOBNAME + ".log"))], "log-" + str(number))
            pdf = (build / (JOBNAME + ".pdf")).read_bytes()
            require(pdf.startswith(b"%PDF-") and b"%%EOF" in pdf[-1024:], "missing or incomplete PDF")
            if reference_bytes is not None:
                require(pdf == reference_bytes, "rebuilt PDF differs from the admitted reference")
            produced.append(pdf)
        guard()
        require(all(pdf == produced[0] for pdf in produced), "fresh repeated PDFs differ")
        if output is not None:
            direct_directory(output.parent)
            with output.open("xb") as stream:
                stream.write(produced[0])
                stream.flush()
                os.fsync(stream.fileno())
        guard()
        result.update(status="exact_reference_reproduced" if args.exact else "discovery_requires_artifact_review",
                      builds=len(produced), pdf_sha256=sha(produced[0]), pdf_bytes=len(produced[0]),
                      sources_and_tools_unchanged=True, finite_source_bindings=finite_bindings,
                      expected_document=expected_document,
                      matches_expected_finite_pdf=(len(produced[0]) == EXPECTED_PDF_BYTES
                                                   and sha(produced[0]) == EXPECTED_PDF_SHA),
                      link_review="existing staged publication-link gate required; no new reader executed",
                      visual_review="separate actual page/font/navigation review required")
        print("OK: finite MGW " + result["status"] + "; builds=" + str(len(produced)))
        return 0
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        completed, completed_ns = now(), time.monotonic_ns()
        late = completed >= deadline or completed_ns >= deadline_ns
        successful_body = result["status"] != "failed"
        if late and successful_body:
            result.update(status="failed", failure="deadline exhausted before final receipt")
        result["completed_utc"] = completed.isoformat()
        result["completed_monotonic_ns"] = completed_ns
        result["commands"] = [command for runner in runners for command in runner.commands]
        result["disk_observations"] = disk_count
        record(work / "RESULT.json", result)
        if successful_body:
            require(not late and now() < deadline and time.monotonic_ns() < deadline_ns,
                    "publication deadline exhausted at final receipt; actual outer exit is required")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print("Finite MGW publication failed: " + str(error), file=sys.stderr)
        print(json.dumps({"status": "failed", "failure": str(error),
              "receipt_scope": "RESULT.json only after ownership of fresh work; retain this actual outer stderr"}),
              file=sys.stderr)
        raise SystemExit(1)
