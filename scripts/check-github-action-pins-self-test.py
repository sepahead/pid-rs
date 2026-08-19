#!/usr/bin/env python3
"""Mutation-test the exact GitHub Action pin policy."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import types


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-github-action-pins-self-test.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-github-action-pins.py"
EXPECTED_CHECKER_SHA256 = "c2b160fd385f884d4064309e5a44c62a66d392269dc93f7e6896f0cb656bd189"
EXPECTED_CHECKER_SIZE_BYTES = 12_496


class SelfTestError(RuntimeError):
    """The checker baseline failed or a hostile mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def load_checker() -> types.ModuleType:
    raw = CHECKER.read_bytes()
    require(
        EXPECTED_CHECKER_SIZE_BYTES == 0
        or (
            len(raw) == EXPECTED_CHECKER_SIZE_BYTES
            and hashlib.sha256(raw).hexdigest() == EXPECTED_CHECKER_SHA256
        ),
        "checker source binding changed",
    )
    module = types.ModuleType("pid_rs_github_action_pin_checker")
    module.__file__ = os.fspath(CHECKER)
    exec(compile(raw, os.fspath(CHECKER), "exec", flags=0, dont_inherit=True, optimize=sys.flags.optimize), module.__dict__)
    return module


def main() -> int:
    checker = load_checker()
    exact = "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a"
    positives = (
        f"      - uses: actions/upload-artifact@{exact} # v7.0.1\n",
        f"      - uses:\tactions/upload-artifact@{exact}\t# tab separator\n",
        "      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0\n",
        "      - uses: './.github/actions/local'\n",
    )
    for index, line in enumerate(positives):
        checker.validate_workflow_bytes(line.encode(), f"positive-{index}.yml")

    hostiles = (
        f"      - uses: actions/upload-artifact@{exact[:-1]} # truncated\n",
        f"      - uses: actions/upload-artifact@{exact}a # overlong\n",
        "      - uses: actions/upload-artifact@v7.0.1\n",
        "      - uses: actions/upload-artifact@${{ matrix.ref }}\n",
        f"      - uses: actions/upload-artifact@{exact.upper()}\n",
        f"      - uses: actions/upload-artifact@{'1' * 40}\n",
        f"      - uses: actions/upload-artifact@{exact}#adjacent-is-scalar-data\n",
        "      - uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0#adjacent-is-scalar-data\n",
        f'      - uses: "actions/upload-artifact@{exact}"#adjacent-is-not-a-comment\n',
        '      - uses: "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0"#adjacent-is-not-a-comment\n',
        "\t- uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0\n",
        "  \t- uses: actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0\n",
        f"      - uses : actions/upload-artifact@{'1' * 40}\n",
        f"      - {{ uses: actions/upload-artifact@{'1' * 40} }}\n",
        f"      - uses: Actions/upload-artifact@{'1' * 40}\n",
        f"      - uses: actions/Upload-Artifact@{'1' * 40}\n",
        f'      - "uses": actions/upload-artifact@{"1" * 40}\n',
        f"      - 'uses': actions/upload-artifact@{'1' * 40}\n",
        f'      - "us\\u0065s": actions/upload-artifact@{"1" * 40}\n',
        "      - uses: docker://alpine:3.23\n",
        "      - uses: actions/upload-artifact\n",
        "      - uses: \"actions/upload-artifact@v7\" trailing\n",
        "      - uses:\n",
        "      - uses: |\n          actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a\n",
        "      - uses: |#adjacent-is-not-a-comment\n          actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0\n",
        "      - uses: *upload_artifact\n",
        f"      - &upload_step uses: actions/upload-artifact@{exact}\n",
        f"      ? uses\n      : actions/upload-artifact@{exact}\n",
        f"      x-upload: &upload actions/upload-artifact@{exact}\n      - *upload\n",
        f"      - &upload\n        uses: actions/upload-artifact@{exact}\n      - *upload\n",
        f'      - !!str "us\\u0065s": actions/upload-artifact@{"1" * 40}\n',
        f'      steps: [{{"us\\u0065s": actions/upload-artifact@{"1" * 40}}}]\n',
        '      - !!str "us\\u0065s": actions/checkout@v7\n',
        '      steps: [{"us\\u0065s": actions/checkout@v7}]\n',
        '      - !!str "us\\u0065s": "actions\\/checkout@v7"\n',
        '      steps: [{"us\\u0065s": "actions\\/checkout@v7"}]\n',
        "      - uses: './local@dynamic'\n",
        f"      - uses: actions/upload-artifact@{exact}\r\n",
        f"      - uses: actions/upload-artifact@{exact}",
    )
    rejected = 0
    for index, line in enumerate(hostiles):
        try:
            checker.validate_workflow_bytes(line.encode(), f"hostile-{index}.yml")
        except checker.PinError:
            rejected += 1
    require(rejected == len(hostiles), "an action-pin hostile mutation survived")
    result = checker.validate_repository()
    require(result["result"] == "pass", "live workflow baseline failed")
    sys.stdout.write(
        '{"hostiles_rejected":%d,"live_external_action_references":%d,'
        '"result":"pass","schema":"pid-rs/github-action-pin-self-test/v1"}\n'
        % (rejected, result["external_action_references"])
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, SelfTestError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from None
