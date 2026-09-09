#!/usr/bin/env python3
"""Finite whole-entrypoint controls with inert producers; never a PDF reproduction.

Fixture manifests deliberately pin synthetic inputs/tools. The production source
is copied verbatim except for the fixture manifest digest. All evidence is kept.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import time
from types import ModuleType

BUILDER = "scripts/build-recorded-office-sensors-pdf.py"
FAKE_PDF = b"%PDF-1.7\nINERT CONTROL: not a publication PDF\n%%EOF\n"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw),
            "mode": oct(stat.S_IMODE(path.stat().st_mode))}


def save_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).absolute().parents[1])
    parser.add_argument("--work-dir", type=Path, required=True, help="fresh retained evidence directory")
    args = parser.parse_args()
    require(sys.version_info >= (3, 11) and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires Python 3.11+ -I -S -B, optionally -O")
    root = args.root.absolute()
    require(root == root.resolve(strict=True), "root must be canonical")
    work = args.work_dir.absolute()
    require(work.parent == work.parent.resolve(strict=True) and not work.exists()
            and not work.is_symlink(), "control work directory must be fresh and canonical")
    work.mkdir(mode=0o700)
    source = (root / BUILDER).read_bytes()
    module = ModuleType("recorded_sensor_publication_controls_subject")
    module.__file__ = str(root / BUILDER)
    exec(compile(source, str(root / BUILDER), "exec", dont_inherit=True,
                 optimize=sys.flags.optimize), module.__dict__)
    runtime = module.load_runtime(root / module.RUNTIME)
    snapshot = runtime.Snapshot()
    snapshot.read(root / BUILDER)
    snapshot.read(Path(__file__).absolute())
    require(hashlib.sha256(snapshot.read(root / module.RUNTIME)).hexdigest() == module.RUNTIME_SHA,
            "runtime changed")
    manifest_raw = snapshot.read(root / module.MANIFEST)
    require(hashlib.sha256(manifest_raw).hexdigest() == module.MANIFEST_SHA,
            "production manifest changed")
    production = runtime.strict_json(manifest_raw)
    captured = {}
    for relative in module.SOURCE_FILES:
        raw = module.read_pinned(snapshot, root / relative, production["files"][relative], relative)
        captured[relative] = raw
    (work / "execution").mkdir()
    cutoff = time.monotonic_ns() + 600 * 10**9
    rows = []
    cases = (
        ("discovery-positive", "discover", "normal", 0, "discovery_requires_artifact_review", 10),
        ("exact-inert-positive", "exact", "normal", 0, "exact_reference_reproduced", 10),
        ("cross-no-inputs", "cross", "normal", 2, "status 2 refusal", 0),
        ("pending-reference", "exact", "pending", 1, "exact reference is pending", 0),
        ("manifest-drift", "discover", "manifest-drift", 1, "manifest digest changed", 0),
        ("duplicate-json", "discover", "duplicate-json", 1, "duplicate JSON key", 0),
        ("boolean-byte-count", "discover", "boolean-byte-count", 1, "malformed pin", 0),
        ("missing-markdown", "discover", "missing-markdown", 1, "No such file", 0),
        ("drifted-markdown", "discover", "drifted-markdown", 1, "input size changed", 0),
        ("wrong-input-mode", "discover", "wrong-input-mode", 1, "input mode changed", 0),
        ("work-output-alias", "discover", "work-output-alias", 1, "output must be a new path", 0),
        ("unsupported-profile", "discover", "unsupported-profile", 1, "unsupported publication profile", 0),
        ("wrong-tool", "discover", "wrong-tool", 1, "input digest changed: tool pandoc", 0),
        ("missing-producer", "discover", "missing-producer", 1, "missing tool: pandoc", 0),
        ("failed-producer", "discover", "failed-producer", 1, "nonzero process status", 2),
        ("producer-stderr", "discover", "producer-stderr", 1, "unexpected stderr", 2),
        ("body-drift", "discover", "body-drift", 1, "generated TeX differs", 1),
        ("copied-input-drift", "discover", "copied-input-drift", 1, "input changed after capture", 1),
        ("absent-output", "discover", "absent-output", 1, "No such file", 5),
        ("post-capture-drift", "discover", "post-capture-drift", 1, "input changed after capture", 2),
        ("unsafe-output-byte-drift", "exact", "unsafe-output-byte-drift", 1, "differs from the admitted reference", 5),
        ("repeat-drift", "discover", "repeat-drift", 1, "fresh repeated PDFs differ", 10),
        ("reference-drift", "exact", "reference-drift", 1, "admitted reference changed", 0),
    )
    result = {"status": "failed", "scope": "synthetic command/input controls; no actual PDF or theorem credit",
              "unsafe_link_scope": "byte drift here; semantic action mutations are in the existing publication-link suite",
              "cases": rows}
    try:
        for label, mode, behavior, expected_exit, message, expected_children in cases:
            require(time.monotonic_ns() < cutoff - 60 * 10**9, "control original deadline exhausted")
            fixture = work / label
            fixture.mkdir()
            for relative, raw in captured.items():
                path = fixture / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                path.chmod(int(production["files"][relative]["mode"], 8))
            (fixture / BUILDER).parent.mkdir(parents=True, exist_ok=True)
            tex = fixture / "tex"
            tex.mkdir()
            profile = json.loads(manifest_raw)
            profile["tex_files"] = {}
            for relative in set(profile["fonts"].values()):
                path = tex / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"inert font fixture\n")
                profile["tex_files"][relative] = pin(path)
            binary = fixture / "bin"
            binary.mkdir()
            expected_body = repr(captured[module.ASSETS + "body.expected.tex"])
            fake = (
                "#!" + str(Path(sys.executable).resolve(strict=True)) + "\n"
                "from pathlib import Path\nimport sys\n"
                + "behavior = " + repr(behavior) + "\n"
                + "body = " + expected_body + "\n"
                + "pdf = " + repr(FAKE_PDF) + "\n"
                + "md = Path(" + repr(str(fixture / module.MARKDOWN)) + ")\n"
                + "if Path(sys.argv[0]).name == 'pandoc':\n"
                  "    out = Path(sys.argv[sys.argv.index('--output') + 1])\n"
                  "    out.write_bytes(body + (b'drift' if behavior == 'body-drift' else b''))\n"
                  "    if behavior == 'copied-input-drift': Path('filter.lua').write_bytes(b'drift')\n"
                  "else:\n"
                  "    if behavior == 'failed-producer': sys.exit(7)\n"
                  "    if behavior == 'producer-stderr': print('deliberate stderr', file=sys.stderr)\n"
                  "    if behavior == 'post-capture-drift': md.write_bytes(md.read_bytes() + b'drift')\n"
                  "    Path('recorded-office-sensors.log').write_text('inert log\\n')\n"
                  "    Path('recorded-office-sensors.fls').write_text('INPUT ./body.tex\\n')\n"
                  "    if behavior == 'unsafe-output-byte-drift': pdf += b'/AA /Launch\\n%%EOF\\n'\n"
                  "    if behavior == 'repeat-drift': pdf += str(Path.cwd()).encode() + b'\\n%%EOF\\n'\n"
                  "    if behavior != 'absent-output': Path('recorded-office-sensors.pdf').write_bytes(pdf)\n"
            )
            for name in ("pandoc", "lualatex"):
                path = binary / name
                path.write_text(fake)
                path.chmod(0o755)
                profile["tools"][name] = pin(path)
            for name, path in {"python": Path(sys.executable), "bash": Path("/bin/bash"),
                               "du": Path("/usr/bin/du"), "ps": Path("/bin/ps")}.items():
                profile["tools"][name] = pin(path.resolve(strict=True))
            profile["reference"] = {"status": "pending" if behavior == "pending" else "admitted",
                                    "sha256": hashlib.sha256(FAKE_PDF).hexdigest()}
            reference = fixture / module.PDF
            reference.parent.mkdir(parents=True)
            reference.write_bytes(FAKE_PDF + (b"drift" if behavior == "reference-drift" else b""))
            if behavior == "unsupported-profile":
                profile["profile"] = "unreviewed-platform"
            if behavior == "wrong-tool":
                profile["tools"]["pandoc"]["sha256"] = "0" * 64
            if behavior == "boolean-byte-count":
                profile["files"][module.MARKDOWN]["bytes"] = True
            manifest = fixture / module.MANIFEST
            save_json(manifest, profile)
            if behavior == "duplicate-json":
                manifest.write_bytes(manifest.read_bytes().replace(
                    b"{\n", b'{"schema": "duplicate fixture",\n', 1))
            fixture_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            before = ('MANIFEST_SHA = "' + module.MANIFEST_SHA + '"').encode()
            require(source.count(before) == 1, "fixture manifest pin anchor drifted")
            (fixture / BUILDER).write_bytes(source.replace(before, ('MANIFEST_SHA = "' + fixture_sha + '"').encode()))
            if behavior == "manifest-drift":
                manifest.write_bytes(manifest.read_bytes() + b" ")
            if behavior == "missing-markdown":
                (fixture / module.MARKDOWN).unlink()
            if behavior == "drifted-markdown":
                (fixture / module.MARKDOWN).write_bytes(captured[module.MARKDOWN] + b"drift")
            if behavior == "wrong-input-mode":
                (fixture / module.MARKDOWN).chmod(0o600)
            if behavior == "missing-producer":
                (binary / "pandoc").unlink()
            command = [sys.executable, "-I", "-S", "-B"]
            if sys.flags.optimize:
                command.append("-O")
            command += [str(fixture / BUILDER)]
            if mode == "cross":
                command += ["--cross-toolchain", "--root", str(fixture / "absent-root")]
            else:
                command += ["--" + mode, "--check", "--root", str(fixture),
                            "--tex-root", str(tex), "--work-dir", str(fixture / "build-evidence")]
                if behavior == "work-output-alias":
                    command += ["--output", str(fixture / "build-evidence")]
            environment = {"PATH": str(binary), "LC_ALL": "C", "LANG": "C"}
            runner = runtime.Runner(work / "execution", environment, preparation=False)
            try:
                runner.run(command, fixture, label, timeout=45, cap=2 * 1024**2,
                           memory=4 * 1024**3, allow_stdout=True)
            except RuntimeError:
                pass  # Expected entrypoint refusals are judged by their retained actual record.
            require(len(runner.commands) == 1, label + ": no actual outer command record")
            observed = runner.commands[0]
            require(observed["failure"] is None and not observed["remaining_live_group_processes"],
                    label + ": operational failure cannot count as a control result")
            require(observed["returncode"] == expected_exit, label + ": wrong outer exit")
            logs = work / "execution" / ("00-" + label)
            raw = (logs / "stdout.log").read_bytes() + (logs / "stderr.log").read_bytes()
            require(message.encode() in raw, label + ": noncausal failure")
            child_records = list((fixture / "build-evidence").glob("build-*/execution/*/command.json"))
            require(len(child_records) == expected_children, label + ": producer roster differs")
            if expected_exit == 0:
                require(not (logs / "stderr.log").read_bytes(), label + ": unexpected outer stderr")
            snapshot.verify()
            rows.append({"case": label, "actual_outer_exit": observed["returncode"],
                         "primary_child_records": len(child_records), "expected": message,
                         "status": "expected_control_outcome"})
        result["status"] = "finite_synthetic_controls_completed"
        print("OK: " + str(len(rows)) + " recorded-sensor publication controls; no native document reproduction")
        return 0
    except BaseException as error:
        result["failure"] = repr(error)
        raise
    finally:
        save_json(work / "RESULT.json", result)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print("Recorded-sensor publication self-test failed: " + str(error), file=sys.stderr)
        raise SystemExit(1)
