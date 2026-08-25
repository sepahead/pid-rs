#!/usr/bin/env python3
"""Require byte-identical normal/optimized output for the separate Lean lane."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in (0, 1)
):
    print(
        "ERROR: check-lean-sxpid3-informative-invariance-parity.py requires "
        "Python 3.11+ -I -S -B, with -O optional",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-lean-sxpid3-informative-invariance.py"
SELF_TEST = ROOT / "scripts/check-lean-sxpid3-informative-invariance-self-test.py"
EXPECTED_CHECKER_STDOUT_SHA256 = (
    "4133a2c6fc1fe2217914631f3d7fff1af8d1ea37c209f3b55b9b0f8780b6a8b4"
)
EXPECTED_SELF_TEST_STDOUT_SHA256 = (
    "fff6c2577999cd6c69c628c3b7c86f1b30e07b3a04d08e658bcd55b499d950b2"
)


class ParityError(RuntimeError):
    """Normal/optimized execution or its pinned canonical output drifted."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ParityError(message)


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run(script: Path, optimized: bool) -> subprocess.CompletedProcess[bytes]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B"))
    command.append(str(script))
    return subprocess.run(
        command,
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=3600,
        check=False,
    )


def check_pair(script: Path, expected_sha256: str) -> str:
    normal = run(script, False)
    optimized = run(script, True)
    require(normal.returncode == 0, f"{script.name} normal run failed: {normal.stderr!r}")
    require(
        optimized.returncode == 0,
        f"{script.name} optimized run failed: {optimized.stderr!r}",
    )
    require(
        normal.stderr == b"" and optimized.stderr == b"",
        f"{script.name} emitted stderr",
    )
    require(
        normal.stdout == optimized.stdout,
        f"{script.name} normal/optimized stdout differs",
    )
    require(normal.stdout.endswith(b"\n"), f"{script.name} stdout lacks final LF")
    actual_sha256 = sha256(normal.stdout)
    require(
        actual_sha256 == expected_sha256,
        f"{script.name} canonical stdout digest drifted: "
        f"expected {expected_sha256}, found {actual_sha256}",
    )
    return actual_sha256


def main() -> int:
    try:
        checker_sha256 = check_pair(CHECKER, EXPECTED_CHECKER_STDOUT_SHA256)
        self_test_sha256 = check_pair(SELF_TEST, EXPECTED_SELF_TEST_STDOUT_SHA256)
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    result = {
        "schema": "pid-rs/lean-sxpid3-informative-invariance-parity/v1",
        "status": "passed",
        "checker_normal_optimized_identical": True,
        "checker_stdout_sha256": checker_sha256,
        "self_test_normal_optimized_identical": True,
        "self_test_stdout_sha256": self_test_sha256,
        "shared_kernel_boundary": (
            "Normal and optimized Python replay the same Lean executable, source, "
            "dependency closure, and checker logic; parity is a drift control, not an "
            "independent theorem or authenticity result."
        ),
    }
    print(json.dumps(result, ensure_ascii=True, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
