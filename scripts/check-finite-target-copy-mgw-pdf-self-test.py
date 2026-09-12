#!/usr/bin/env python3
"""Exercise target-copy PDF input, diagnostic and aggregate-dispatch failures.

Synthetic process checks test the controller, not a PDF renderer or native
closure. The actual two-build exact check is a separate required command.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build-finite-target-copy-mgw-pdf.py"
GATE = ROOT / "scripts/check-formal-pdf-set.sh"
BLOCK = r'''python3 -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py
python3 -O -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py
if [[ "$MODE" == "--exact" ]]; then
  if [[ -z "${PID_RS_MGW_TARGET_COPY_TEX_ROOT:-}" ]]; then
    echo "formal PDF set: exact target-copy MGW requires PID_RS_MGW_TARGET_COPY_TEX_ROOT" >&2
    exit 2
  fi
  MGW_TARGET_COPY_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mgw-target-copy.XXXXXX")"
  python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --check --tex-root "$PID_RS_MGW_TARGET_COPY_TEX_ROOT" --work-dir "$MGW_TARGET_COPY_BUILD_PARENT/build"
else
  if python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --cross-toolchain; then
    echo "formal PDF set: finite target-copy cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    MGW_TARGET_COPY_CROSS_STATUS=$?
  fi
  if [[ "$MGW_TARGET_COPY_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: finite target-copy refusal returned $MGW_TARGET_COPY_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi'''


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def gate_wiring(text: str) -> None:
    require(text.count(BLOCK) == 1, "target-copy exact/refusal/control wiring differs")


def main() -> None:
    before = BUILDER.read_bytes()
    module = runpy.run_path(str(BUILDER), run_name="target_copy_controls")
    error = module["BuildError"]
    accepted = rejected = 0

    def rejects(call, expected: str) -> None:
        nonlocal rejected
        try:
            call()
        except error as caught:
            require(expected in str(caught), f"noncausal rejection: {caught}")
            rejected += 1
        else:
            raise RuntimeError("mutation accepted: " + expected)

    with tempfile.TemporaryDirectory(prefix="pid-rs-target-copy-pdf-controls-") as temporary:
        root = Path(temporary)
        work = module["new_work_directory"](root / "fresh")
        require(work.is_dir(), "new workspace missing")
        accepted += 1
        canary = work / "canary"; canary.write_bytes(b"preserve")
        rejects(lambda: module["new_work_directory"](work), "must not already exist")
        symbolic = root / "symbolic"; symbolic.symlink_to(work, target_is_directory=True)
        rejects(lambda: module["new_work_directory"](symbolic), "must not already exist")
        rejects(lambda: module["new_work_directory"](canary), "must not already exist")
        require(canary.read_bytes() == b"preserve", "workspace refusal changed existing bytes")
        sample = root / "input"; sample.write_bytes(b"input")
        pin = {"bytes": 5, "sha256": hashlib.sha256(b"input").hexdigest()}
        require(module["checked_bytes"](sample, pin) == b"input", "input baseline failed")
        accepted += 1
        rejects(lambda: module["checked_bytes"](sample, {**pin, "bytes": True}), "invalid input byte bound")
        rejects(lambda: module["checked_bytes"](sample, {**pin, "bytes": 4}), "input size differs")
        rejects(lambda: module["checked_bytes"](sample, {**pin, "sha256": "0" * 64}), "input digest differs")
        rejects(lambda: module["unique_object"]([("x", 0), ("x", 1)]), "duplicate profile key")

        tools_dir = root / "tools"; tools_dir.mkdir()
        engine = tools_dir / "engine"
        engine.write_text('#!/bin/sh\nprintf "relative-path-tool\\n"\n')
        engine.chmod(0o755)
        alias = tools_dir / "format-alias"; alias.symlink_to(engine.name)
        original_path = os.environ.get("PATH")
        try:
            os.environ["PATH"] = os.path.relpath(tools_dir, Path.cwd())
            selected = module["tool_path"]("format-alias")
            require(Path(selected).is_absolute() and Path(selected).name == alias.name,
                    "relative PATH resolution lost the invocation basename")
            require(module["run"]([selected], work, {"PATH": ""}, "relative-path")
                    == b"relative-path-tool\n", "relative PATH tool failed after cwd change")
            accepted += 1
            rejects(lambda: module["tool_path"]("missing-tool"), "missing tool")
        finally:
            if original_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = original_path

        env = {"PATH": os.defpath}
        out = module["run"]([sys.executable, "-I", "-S", "-c", "print('retained')"],
                            work, env, "positive")
        require(out == b"retained\n" and (work / "positive.stdout").read_bytes() == out,
                "stdout retention failed")
        accepted += 1
        rejects(lambda: module["run"]([sys.executable, "-I", "-S", "-c",
                "import sys; print('warning', file=sys.stderr)"], work, env, "stderr"),
                "wrote stderr")
        require((work / "stderr.stderr").read_bytes() == b"warning\n", "stderr evidence lost")
        rejects(lambda: module["run"]([sys.executable, "-I", "-S", "-c",
                "import sys; print('failed'); sys.exit(7)"], work, env, "failure"), "exited 7")
        require((work / "failure.stdout").read_bytes() == b"failed\n", "failure evidence lost")

        harmless = "Package: infwarerr 2019/12/03 Providing info/warning/error messages"
        require(module["WARNINGS"].search(harmless) is None, "package-description false positive")
        accepted += 1
        for diagnostic in ("LaTeX Warning: undefined reference",
                           "LaTeX Font Warning: missing shape",
                           "Package microtype Warning: problem",
                           "Class article Warning: problem",
                           "LuaHBTeX warning: problem",
                           "warning  (pdf backend): ignoring duplicate destination",
                           r"Overfull \hbox (1pt too wide)",
                           r"Underfull \vbox",
                           "Missing character: There is no x",
                           "! Undefined control sequence."):
            require(module["WARNINGS"].search(diagnostic) is not None,
                    "missed TeX diagnostic: " + diagnostic)
            rejected += 1
        for optimized in (False, True):
            flags = [sys.executable, *(["-O"] if optimized else []), "-I", "-S", "-B", str(BUILDER)]
            refusal = subprocess.run([*flags, "--cross-toolchain"], capture_output=True, timeout=10,
                                     env={"PATH": ""})
            require(refusal.returncode == 2 and not refusal.stderr and b"refusing" in refusal.stdout,
                    "cross-toolchain refusal must precede prerequisites")
            rejected += 1
            mixed = subprocess.run([*flags, "--cross-toolchain", "--check"],
                                   capture_output=True, timeout=10)
            require(mixed.returncode == 2 and not mixed.stdout and b"not allowed" in mixed.stderr,
                    "conflicting modes accepted")
            rejected += 1
            missing = subprocess.run(flags, capture_output=True, timeout=10)
            require(missing.returncode == 1 and b"--tex-root is required" in missing.stderr,
                    "implicit TeX root accepted")
            rejected += 1

    gate = GATE.read_text()
    gate_wiring(gate); accepted += 1
    mutations = [
        ("python3 -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py", ":"),
        ("python3 -O -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py", ":"),
        ('if [[ "$MODE" == "--exact" ]]; then', 'if false; then'),
        ('if [[ -z "${PID_RS_MGW_TARGET_COPY_TEX_ROOT:-}" ]]; then', 'if false; then'),
        ('--check --tex-root "$PID_RS_MGW_TARGET_COPY_TEX_ROOT"', '--check'),
        ('--check --tex-root "$PID_RS_MGW_TARGET_COPY_TEX_ROOT"', '--tex-root "$PID_RS_MGW_TARGET_COPY_TEX_ROOT"'),
        ('--work-dir "$MGW_TARGET_COPY_BUILD_PARENT/build"', '--work-dir "$MGW_TARGET_COPY_BUILD_PARENT/build" || true'),
        ('if python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --cross-toolchain; then', 'if false; then'),
        ('--cross-toolchain; then', '--check; then'),
        ('MGW_TARGET_COPY_CROSS_STATUS=$?', 'MGW_TARGET_COPY_CROSS_STATUS=2'),
        ('"$MGW_TARGET_COPY_CROSS_STATUS" -ne 2', '"$MGW_TARGET_COPY_CROSS_STATUS" -ne 1'),
    ]
    for old, new in mutations:
        changed = BLOCK.replace(old, new, 1)
        require(changed != BLOCK, "gate mutation anchor missing")
        try:
            gate_wiring(gate.replace(BLOCK, changed, 1))
        except RuntimeError as caught:
            require("target-copy exact/refusal/control wiring differs" in str(caught), "wrong wiring rejection")
            rejected += 1
        else:
            raise RuntimeError("gate bypass accepted")
    require(BUILDER.read_bytes() == before and GATE.read_text() == gate, "source changed during controls")
    print(f"OK: {accepted} positive controls and {rejected} rejected input/diagnostic/dispatch cases; "
          "synthetic checks do not establish native PDF reproduction")


if __name__ == "__main__":
    main()
