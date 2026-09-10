#!/usr/bin/env python3
"""Focused sensor-figure import controls; no TeX or PDF production.

Runs the exact builder validation heredoc and actual Pandoc filter on retained
fixtures. This is not a whole-builder, new-PDF-profile, or visual acceptance test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import time

BUILDER = "scripts/build-pid-sensor-placement-and-galadriel-guide-pdf.sh"
FILTER = "audit/formal/latex/pid-sensor-placement-and-galadriel-guide/filter.lua"
MANIFEST = "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/figure-assets.json"
FIGURES = "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide"
REUSED = "audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation"
STEMS = ("current-versus-proposed", "measurement-to-estimand", "placement-evidence-funnel")
VALIDATOR_SHA = "17f006ab45bd7dbe02521a9ebe1cc4d4684f461fa3d7964947a564d37f3b0dfc"
FILTER_SHA = "769390a0e6b459eac1ac198e76011241cdd28e694a663e3cdac5381aa4b65d6f"
START = b"""  python3 -I -B - "$FIGURE_MANIFEST" "$FIGURE_DIR" "$ROOT" <<'PY'
"""
END = b"\nPY\n}\n\nvalidate_figure_assets\n"


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def pin(path: Path) -> dict:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "mode": oct(stat.S_IMODE(path.stat().st_mode))}


def save_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def write_new(path: Path, raw: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(mode)


def mutate(fixture: Path, kind: str, key: str, value: object) -> None:
    path = fixture / MANIFEST
    manifest = json.loads(path.read_bytes())
    if kind == "roster":
        if key == "missing":
            del manifest["reused_assets"]
        elif key == "mapping":
            manifest["reused_assets"] = {}
        elif key == "extra-entry":
            manifest["reused_assets"].append(dict(manifest["reused_assets"][0]))
        elif key == "extra-field":
            manifest["reused_assets"][0]["unexpected"] = None
        else:
            raise RuntimeError("unknown roster mutation")
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    elif kind == "field":
        manifest["reused_assets"][0][key] = value
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    elif kind in ("mode", "length", "digest", "symlink"):
        path = fixture / (REUSED + "." + key)
        raw = path.read_bytes()
        if kind == "mode":
            path.chmod(0o600)
            require(path.read_bytes() == raw, "mode fixture changed bytes")
        elif kind == "length":
            # Both length and digest change: this tests combined byte refusal,
            # not independent necessity of the redundant size predicate.
            path.write_bytes(raw + b"\n")
        elif kind == "digest":
            changed = bytes((raw[0] ^ 1,)) + raw[1:]
            require(len(changed) == len(raw), "digest fixture changed length")
            path.write_bytes(changed)
        else:
            target = fixture / ("exact-symlink-target." + key)
            path.rename(target)
            path.symlink_to(target)
    elif kind == "ancestor":
        directory = (fixture / REUSED).parent
        target = directory.with_name("retained-exact-occupancy-assets")
        directory.rename(target)
        directory.symlink_to(target, target_is_directory=True)
    elif kind != "baseline":
        raise RuntimeError("unknown fixture mutation")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--pandoc", required=True, type=Path)
    parser.add_argument("--pandoc-sha256", required=True)
    args = parser.parse_args()
    require(sys.version_info >= (3, 11) and sys.flags.isolated
            and sys.dont_write_bytecode and sys.flags.optimize in (0, 1),
            "requires Python 3.11+ -I -B, optionally -O")
    root, work, pandoc = args.root.absolute(), args.work_dir.absolute(), args.pandoc.absolute()
    require(root == root.resolve(strict=True), "root must be canonical")
    require(not work.exists() and not work.is_symlink()
            and work.parent == work.parent.resolve(strict=True),
            "work directory must be fresh with a canonical existing parent")
    require(pandoc.is_file() and not pandoc.is_symlink()
            and pandoc == pandoc.resolve(strict=True), "Pandoc must be a canonical regular file")
    require(pin(pandoc)["sha256"] == args.pandoc_sha256, "selected Pandoc digest changed")
    builder_raw = (root / BUILDER).read_bytes()
    filter_raw = (root / FILTER).read_bytes()
    require(builder_raw.count(START) == 1 and builder_raw.count(END) == 1,
            "builder validator boundaries changed")
    validator = builder_raw.split(START, 1)[1].split(END, 1)[0] + b"\n"
    require(hashlib.sha256(validator).hexdigest() == VALIDATOR_SHA,
            "builder validator source changed")
    require(hashlib.sha256(filter_raw).hexdigest() == FILTER_SHA, "filter source changed")
    inputs = [MANIFEST]
    inputs += [FIGURES + "/" + stem + "." + suffix for stem in STEMS for suffix in ("svg", "pdf")]
    inputs += [REUSED + "." + suffix for suffix in ("svg", "pdf")]
    captured = {relative: (root / relative).read_bytes() for relative in inputs}
    source_pins = {relative: pin(root / relative) for relative in [BUILDER, FILTER] + inputs}
    work.mkdir(mode=0o700)
    subject = work / "subject"
    subject.mkdir()
    write_new(subject / "validator.py", validator)
    write_new(subject / "filter.lua", filter_raw)
    save_json(work / "INPUTS.json", {
        "root": str(root), "sources": source_pins, "self": pin(Path(__file__)),
        "python": pin(Path(sys.executable).resolve(strict=True)), "pandoc": pin(pandoc),
        "validator_sha256": VALIDATOR_SHA, "filter_sha256": FILTER_SHA,
        "optimized": sys.flags.optimize,
        "scope": "actual validator and filter controls; no TeX/PDF production or whole-builder credit",
    })
    base = work / "base"
    base.mkdir()
    for relative, raw in captured.items():
        write_new(base / relative, raw, int(source_pins[relative]["mode"], 8))
    environment = dict(os.environ)
    environment.pop("PID_GUIDE_FIGURE_PDF_DIR", None)
    environment.pop("PID_GUIDE_REUSED_CANCELLATION_PDF", None)
    environment.update(LC_ALL="C", LANG="C", TZ="UTC")
    cutoff = time.monotonic() + 240
    rows = []
    result = {"status": "failed", "cases": rows,
              "scope": "finite validator/filter controls; actual PDF URI/profile review remains separate"}

    def invoke(label: str, command: list[str], cwd: Path, env: dict,
               expected_exit: int | None, message: bytes, *, baseline: bool = False) -> bytes:
        logs = work / ("logs-" + label)
        logs.mkdir()
        remaining = cutoff - time.monotonic()
        require(remaining > 1, "original control deadline exhausted")
        error = None
        actual_exit = None
        started = time.monotonic()
        try:
            with (logs / "stdout").open("xb") as stdout, (logs / "stderr").open("xb") as stderr:
                child = subprocess.run(command, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, check=False,
                                       timeout=min(20, remaining))
                actual_exit = child.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            error = repr(exc)
        observed = {
            "case": label, "command": command, "cwd": str(cwd), "actual_exit": actual_exit,
            "expected_exit": "positive nonzero" if expected_exit is None else expected_exit,
            "operational_error": error, "elapsed_seconds": time.monotonic() - started,
            "expected_message": message.decode("utf-8"),
            "stdout": pin(logs / "stdout"), "stderr": pin(logs / "stderr"),
        }
        save_json(logs / "COMMAND.json", observed)
        rows.append(observed)
        require(error is None, label + ": operational failure cannot pass a control")
        require(observed["stdout"]["bytes"] <= 65536 and observed["stderr"]["bytes"] <= 65536,
                label + ": retained stream exceeds the declared control limit")
        stdout = (logs / "stdout").read_bytes()
        stderr = (logs / "stderr").read_bytes()
        require(actual_exit > 0 if expected_exit is None else actual_exit == expected_exit,
                label + ": wrong exit")
        require(message in stdout + stderr, label + ": failure/result is not causal")
        if baseline:
            require(not stderr, label + ": unexpected baseline stderr")
        return stdout

    inventory_error = b"reused figure inventory changed"
    fields_error = b"reused figure fields changed"
    cases = [
        ("valid-import", "baseline", "", None, b"figure-assets=GO count=3 reused=1"),
        ("roster-missing", "roster", "missing", None, inventory_error),
        ("roster-mapping", "roster", "mapping", None, inventory_error),
        ("roster-extra-entry", "roster", "extra-entry", None, inventory_error),
        ("roster-extra-field", "roster", "extra-field", None, fields_error),
        ("svg-path", "field", "svg_repository_path", REUSED + "-other.svg",
         b"reused figure identity changed: svg_repository_path"),
        ("pdf-path", "field", "pdf_repository_path", REUSED + "-other.pdf",
         b"reused figure identity changed: pdf_repository_path"),
        ("declared-mode", "field", "svg_mode", "0o600", b"reused figure identity changed: svg_mode"),
        ("declared-size", "field", "svg_bytes", 2651, b"reused figure identity changed: svg_bytes"),
        ("declared-hash", "field", "svg_sha256", "0" * 64,
         b"reused figure identity changed: svg_sha256"),
    ]
    for suffix in ("svg", "pdf"):
        for kind, expected in (
            ("mode", b"reused figure mode changed: signed-cancellation."),
            ("length", b"reused figure bytes changed: signed-cancellation."),
            ("digest", b"reused figure bytes changed: signed-cancellation."),
            ("symlink", b"reused figure path is not canonical direct-regular:"),
        ):
            message = expected if kind == "symlink" else expected + suffix.encode()
            cases.append((suffix + "-" + kind, kind, suffix, None, message))
    cases.append(("ancestor-symlink", "ancestor", "", None,
                  b"reused figure path is not canonical direct-regular:"))
    try:
        for label, kind, key, value, expected in cases:
            fixture = work / label
            shutil.copytree(base, fixture)
            mutate(fixture, kind, key, value)
            command = [sys.executable, "-I", "-B"]
            if sys.flags.optimize:
                command.append("-O")
            command += [str(subject / "validator.py"), str(fixture / MANIFEST),
                        str(fixture / FIGURES), str(fixture)]
            invoke(label, command, fixture, environment, 0 if kind == "baseline" else 1,
                   expected, baseline=(kind == "baseline"))

        filter_fixture = work / "filter-input"
        shutil.copytree(base, filter_fixture)
        markdown = filter_fixture / "fixture.md"
        write_new(markdown, ("![CANCELLATION-IMPORT-CONTROL](" + REUSED + ".svg)\n").encode())
        command = [str(pandoc), str(markdown), "--from=gfm+tex_math_dollars", "--to=latex",
                   "--lua-filter=" + str(subject / "filter.lua")]
        present = dict(environment)
        present["PID_GUIDE_REUSED_CANCELLATION_PDF"] = str(filter_fixture / (REUSED + ".pdf"))
        output = invoke("filter-valid", command, filter_fixture, present, 0,
                        b"signed-cancellation.pdf", baseline=True)
        require(b"signed-cancellation.svg" not in output, "filter left the SVG reference unchanged")
        expected_pdf = str(filter_fixture / (REUSED + ".pdf")).encode()
        require(expected_pdf in output, "filter did not preserve the exact selected PDF path")
        invoke("filter-missing-environment", command, filter_fixture, environment, None,
               b"PID_GUIDE_REUSED_CANCELLATION_PDF is required for the exact reused figure")
        for relative, expected in source_pins.items():
            require(pin(root / relative) == expected, "selected source changed: " + relative)
        require(pin(pandoc)["sha256"] == args.pandoc_sha256, "selected Pandoc changed during controls")
        require(len(rows) == 21, "planned control roster changed")
        result["status"] = "focused_import_controls_completed"
        print("OK: 21 sensor import/filter controls; no TeX/PDF reproduction or new profile acceptance")
        return 0
    except BaseException as exc:
        result["failure"] = repr(exc)
        raise
    finally:
        save_json(work / "RESULT.json", result)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print("Sensor figure import self-test failed: " + str(exc), file=sys.stderr)
        raise SystemExit(1)
