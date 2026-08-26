#!/usr/bin/env python3
"""Hostile controls for API-r4 capture isolation and failure privacy."""

from __future__ import annotations

# The fail-closed runtime bootstrap intentionally precedes ordinary imports.
# ruff: noqa: E402
import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
    and _bootstrap_sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-public-api-capture-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import hashlib
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CAPTURE = ROOT / "scripts/capture-public-api-signature-revision.py"
PYTHON_EXECUTABLE = Path(os.path.realpath(sys.executable))
INNER_ARGUMENT = "--isolated-inner"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_capture() -> Any:
    spec = importlib.util.spec_from_file_location("pid_rs_api_capture", CAPTURE)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load API-r4 capture module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expected_record(operation: str, status: str, stdout: bytes, stderr: bytes) -> str:
    return (
        f"operation={operation} status={status} "
        f"stdout_sha256={sha256(stdout)} stdout_bytes={len(stdout)} "
        f"stderr_sha256={sha256(stderr)} stderr_bytes={len(stderr)}"
    )


def inner_main() -> int:
    capture = load_capture()
    with tempfile.TemporaryDirectory(prefix="pid-rs-api-tool-route-") as temp_name:
        temp = Path(temp_name)
        poison = temp / "poison-tools"
        poison.mkdir()
        hostile_cargo = poison / "cargo"
        hostile_cargo.write_text("#!/bin/sh\nexit 97\n", encoding="utf-8")
        hostile_cargo.chmod(0o700)
        original_path = os.environ.get("PATH")
        if not original_path:
            raise SystemExit("capture self-test requires PATH")
        os.environ["PATH"] = os.fspath(poison) + os.pathsep + original_path
        try:
            tool_environment = capture.isolated_environment(temp)
        finally:
            os.environ["PATH"] = original_path
        selected_cargo = shutil.which("cargo", path=tool_environment["PATH"])
        selected_rustup = shutil.which("rustup", path=tool_environment["PATH"])
        if selected_cargo is None or selected_rustup is None:
            raise SystemExit("isolated tool route omitted Cargo or rustup")
        if Path(selected_cargo).parent != Path(selected_rustup).parent:
            raise SystemExit(
                "isolated tool route did not prioritize the rustup Cargo proxy"
            )
        if Path(selected_cargo) == hostile_cargo:
            raise SystemExit("isolated tool route selected the competing system Cargo")

    private_argument = "/Users/private-owner/secret-capture-argument"
    private_stdout = b"private stdout /private/tmp/api-r4\n"
    private_stderr = b"private stderr /Users/private-owner/repository\n"
    payload = (
        "import os,sys;"
        f"os.write(1,{private_stdout!r});"
        f"os.write(2,{private_stderr!r});"
        "raise SystemExit(17)"
    )
    try:
        capture.run(
            [
                os.fspath(PYTHON_EXECUTABLE),
                "-I",
                "-S",
                "-B",
                "-c",
                payload,
                private_argument,
            ],
            operation="hostile-command",
        )
    except capture.CaptureError as error:
        command_record = str(error)
    else:
        raise SystemExit("hostile subprocess unexpectedly succeeded")
    if command_record != expected_record(
        "hostile-command", "exit-17", private_stdout, private_stderr
    ):
        raise SystemExit("subprocess failure envelope drifted")

    private_validation = "validation failed at /Users/private-owner/source"
    validation_record = str(
        capture.CaptureError(
            private_validation,
            operation="hostile-validation",
        )
    )
    if validation_record != expected_record(
        "hostile-validation", "rejected", b"", private_validation.encode("utf-8")
    ):
        raise SystemExit("validation failure envelope drifted")

    private_unexpected = "unexpected /private/tmp/api-r4 failure"
    unexpected_record = str(
        capture.normalize_capture_failure(RuntimeError(private_unexpected))
    )
    unexpected_detail = f"builtins.RuntimeError: {private_unexpected}".encode("utf-8")
    if unexpected_record != expected_record(
        "unexpected-capture-failure", "exception", b"", unexpected_detail
    ):
        raise SystemExit("unexpected failure envelope drifted")

    combined = "\n".join((command_record, validation_record, unexpected_record))
    forbidden = (
        private_argument,
        private_stdout.decode("utf-8").strip(),
        private_stderr.decode("utf-8").strip(),
        private_validation,
        private_unexpected,
        os.fspath(PYTHON_EXECUTABLE),
        "-I -S -B -c",
    )
    if any(token in combined for token in forbidden):
        raise SystemExit("privacy-normalized failure record disclosed raw failure data")

    print("OK: 5 API-r4 capture failure/isolation controls passed")
    return 0


def outer_main() -> int:
    if not (
        PYTHON_EXECUTABLE.is_absolute()
        and PYTHON_EXECUTABLE.is_file()
        and os.access(PYTHON_EXECUTABLE, os.X_OK)
    ):
        raise SystemExit("self-test could not resolve its running Python endpoint")
    with tempfile.TemporaryDirectory(prefix="pid-rs-api-capture-self-") as temp_name:
        temp = Path(temp_name)
        poison = temp / "poison"
        poison.mkdir()
        marker = temp / "sitecustomize-executed"
        (poison / "sitecustomize.py").write_text(
            "import os\n"
            "from pathlib import Path\n"
            "Path(os.environ['PID_RS_HOSTILE_SITE_MARKER']).write_text('executed\\n')\n"
            "raise RuntimeError('hostile sitecustomize executed')\n",
            encoding="utf-8",
        )
        (poison / "hashlib.py").write_text(
            "raise RuntimeError('hostile PYTHONPATH imported')\n",
            encoding="utf-8",
        )
        environment = dict(os.environ)
        environment.update(
            {
                "PID_RS_HOSTILE_SITE_MARKER": os.fspath(marker),
                "PYTHONOPTIMIZE": "2",
                "PYTHONPATH": os.fspath(poison),
                "PYTHONSTARTUP": os.fspath(poison / "sitecustomize.py"),
                "PYTHONUSERBASE": os.fspath(poison),
            }
        )
        isolated = subprocess.run(
            [
                os.fspath(PYTHON_EXECUTABLE),
                "-I",
                "-S",
                "-B",
                os.fspath(Path(__file__).resolve()),
                INNER_ARGUMENT,
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if isolated.returncode != 0 or isolated.stderr:
            raise SystemExit("isolated hostile-environment self-test failed")
        if (
            isolated.stdout
            != "OK: 5 API-r4 capture failure/isolation controls passed\n"
        ):
            raise SystemExit("isolated hostile-environment output drifted")
        if marker.exists():
            raise SystemExit("isolated capture route executed hostile sitecustomize")

        nonisolated = subprocess.run(
            [
                os.fspath(PYTHON_EXECUTABLE),
                "-S",
                "-B",
                os.fspath(CAPTURE),
            ],
            cwd=ROOT,
            env=environment,
            check=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        expected = (
            "ERROR: capture-public-api-signature-revision.py requires "
            "Python 3.11+ -I -S -B without -O\n"
        )
        if (
            nonisolated.returncode != 2
            or nonisolated.stdout
            or nonisolated.stderr != expected
        ):
            raise SystemExit("non-isolated capture invocation was not rejected cleanly")
        if marker.exists():
            raise SystemExit(
                "non-isolated bootstrap unexpectedly executed sitecustomize"
            )

    print("OK: 7 API-r4 capture failure/isolation controls passed")
    return 0


def main() -> int:
    if sys.argv[1:] == [INNER_ARGUMENT]:
        if sys.flags.optimize != 0:
            raise SystemExit("inner capture self-test must run without optimization")
        return inner_main()
    if sys.argv[1:]:
        raise SystemExit("usage: check-public-api-capture-self-test.py")
    return outer_main()


if __name__ == "__main__":
    raise SystemExit(main())
