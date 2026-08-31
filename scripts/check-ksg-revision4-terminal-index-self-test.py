#!/usr/bin/env python3
"""Hostile controls for the current KSG revision-4 terminal-index check."""

from __future__ import annotations

import sys


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: check-ksg-revision4-terminal-index-self-test.py requires "
        "Python 3.11+ -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
from typing import Any, Callable, NoReturn


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
CHECKER_PATH = ROOT / "scripts/check-ksg-revision4-terminal-index.py"
CHECKER_SIZE = 23_418
CHECKER_SHA256 = "c9a54df51b2d3f28ed07bc2c47c606b0016f7f82158fccf2db1b2839fb592d7b"


class SelfTestError(RuntimeError):
    """The hostile suite itself did not behave as required."""


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def require(predicate: bool, message: str) -> None:
    if not predicate:
        fail(message)


def read_checker() -> bytes:
    before = CHECKER_PATH.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not CHECKER_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == CHECKER_SIZE,
        "checker metadata changed",
    )
    descriptor = os.open(CHECKER_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        require(
            (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_size)
            == (before.st_dev, before.st_ino, before.st_mode, before.st_size),
            "checker opened identity changed",
        )
        chunks: list[bytes] = []
        remaining = CHECKER_SIZE
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", "checker ended during read")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", "checker grew during read")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = CHECKER_PATH.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "checker changed during read",
        )
    raw = b"".join(chunks)
    require(hashlib.sha256(raw).hexdigest() == CHECKER_SHA256, "checker digest changed")
    return raw


def load_checker() -> Any:
    specification = importlib.util.spec_from_file_location(
        "pid_rs_ksg_revision4_terminal_index_checker", CHECKER_PATH
    )
    require(
        specification is not None and specification.loader is not None,
        "cannot load checker module",
    )
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def child_environment() -> dict[str, str]:
    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "TZ": "UTC",
        "XDG_CONFIG_HOME": "/nonexistent",
    }


def run_checker(arguments: tuple[str, ...]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, *arguments, os.fspath(CHECKER_PATH)],
        cwd=ROOT,
        env=child_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=180,
    )


def expect_contract_refusal(
    module: Any,
    label: str,
    operation: Callable[[], object],
) -> None:
    try:
        operation()
    except module.ContractError:
        return
    except Exception as error:
        fail(f"{label} escaped as {type(error).__name__}: {error}")
    fail(f"{label} was accepted")


def replace_once(raw: bytes, old: bytes, new: bytes, label: str) -> bytes:
    require(raw.count(old) == 1, f"{label} mutation source count changed")
    return raw.replace(old, new, 1)


def canonical(module: Any, value: Any) -> bytes:
    return module.canonical_json(value)


def completed(
    module: Any,
    *,
    status: int = 0,
    stdout: bytes | None = None,
    stderr: bytes = b"",
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.CompletedProcess(
        ["terminal-checker"],
        status,
        module.EXPECTED_TERMINAL_STDOUT if stdout is None else stdout,
        stderr,
    )


def validate_record_payload(module: Any, raw: bytes) -> None:
    value = module.parse_json(raw, "mutated terminal record")
    module.require(
        raw == module.canonical_json(value), "terminal record is not canonical JSON"
    )
    module.validate_record_semantics(value)


def validate_schema_payload(module: Any, raw: bytes, record: dict[str, Any]) -> None:
    value = module.parse_json(raw, "mutated terminal schema")
    module.require(
        raw == module.canonical_json(value), "terminal schema is not canonical JSON"
    )
    module.validate_schema_semantics(value, record)


def run() -> int:
    if len(sys.argv) != 1:
        print("ERROR: this self-test accepts no arguments", file=sys.stderr)
        return 2
    read_checker()
    module = load_checker()

    expected_stdout = (
        json.dumps(module.check(), sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")
    baseline_normal = run_checker(("-I", "-S", "-B"))
    baseline_optimized = run_checker(("-O", "-I", "-S", "-B"))
    require(
        baseline_normal.returncode == 0
        and baseline_normal.stderr == b""
        and baseline_normal.stdout == expected_stdout,
        "normal baseline failed",
    )
    require(
        baseline_optimized.returncode == 0
        and baseline_optimized.stderr == b""
        and baseline_optimized.stdout == expected_stdout,
        "optimized baseline failed",
    )

    index_raw = (ROOT / module.INDEX).read_bytes()
    boundary_raw = (ROOT / module.BOUNDARY).read_bytes()
    record_raw = (ROOT / module.RECORD).read_bytes()
    schema_raw = (ROOT / module.SCHEMA).read_bytes()
    record = module.parse_json(record_raw, "baseline terminal record")
    schema = module.parse_json(schema_raw, "baseline terminal schema")

    mutations: list[tuple[str, Callable[[], object]]] = []

    def index_mutation(label: str, old: bytes, new: bytes) -> None:
        changed = replace_once(index_raw, old, new, label)
        mutations.append(
            (
                label,
                lambda changed=changed: module.validate_index_semantics(
                    changed, ROOT, check_targets=False
                ),
            )
        )

    index_mutation(
        "inactive revision",
        b"Revision 4 remains the active scientific packet.",
        b"Revision 4 is inactive.",
    )
    index_mutation(
        "integration promoted",
        b"repository and publication integration\nremain NO-GO.",
        b"repository and publication integration\nremain GO.",
    )
    index_mutation("Q12 revived", b"`Q12 = false`", b"`Q12 = true`")
    index_mutation(
        "R12 issued",
        b"`R12 = permanently_unissued`",
        b"`R12 = issued`",
    )
    index_mutation(
        "L12 adjudicated true",
        b"`L12 = not_adjudicated`",
        b"`L12 = true`",
    )
    index_mutation(
        "terminal result made mathematical",
        b"an operational lifecycle conclusion, not a refutation",
        b"a mathematical conclusion and a refutation",
    )
    index_mutation(
        "qualification credit transfer",
        b"could not inherit\nqualification credit from v12",
        b"could inherit\nqualification credit from v12",
    )
    index_mutation(
        "M1c reactivated",
        b"not a live instruction\nafter the exact v12 route became terminal",
        b"a live instruction\nafter the exact v12 route became terminal",
    )
    index_mutation(
        "final artifacts claimed present",
        b"`decision-v4.md` remain\nabsent",
        b"`decision-v4.md` are\npresent",
    )
    index_mutation(
        "C12 identity changed",
        module.C12.encode("ascii"),
        ("f" * 40).encode("ascii"),
    )
    index_mutation(
        "boundary link retargeted",
        b"ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md",
        b"ksg-rev4-m1a-composite-v12-terminal-failure-2026-08-23.json",
    )
    mutations.append(
        (
            "duplicate revision row",
            lambda: module.validate_index_semantics(
                index_raw + (module.INDEX_TABLE_ROWS[3] + "\n").encode("utf-8"),
                ROOT,
                check_targets=False,
            ),
        )
    )
    mutations.append(
        (
            "explicit attempt-1 reactivation",
            lambda: module.validate_index_semantics(
                index_raw + b"reactivate attempt 1\n", ROOT, check_targets=False
            ),
        )
    )
    mutations.append(
        (
            "invalid index UTF-8",
            lambda: module.validate_index_semantics(
                index_raw[:-1] + b"\xff\n", ROOT, check_targets=False
            ),
        )
    )

    def boundary_mutation(label: str, old: bytes, new: bytes) -> None:
        changed = replace_once(boundary_raw, old, new, label)
        mutations.append(
            (label, lambda changed=changed: module.validate_boundary_semantics(changed))
        )

    boundary_mutation("boundary Q12 revival", b"Q12 is false", b"Q12 is true")
    boundary_mutation(
        "boundary R12 issuance",
        b"R12 is permanently unissued",
        b"R12 is issued",
    )
    boundary_mutation(
        "boundary L12 success",
        b"L12 is not\n  adjudicated",
        b"L12 succeeded and is\n  adjudicated",
    )
    boundary_mutation(
        "boundary later launch",
        b"Later pushes cannot create L12",
        b"Later pushes can create L12",
    )
    boundary_mutation(
        "boundary scientific overclaim",
        b"It does not validate a PID functional",
        b"It validates a PID functional",
    )
    mutations.append(
        (
            "invalid boundary UTF-8",
            lambda: module.validate_boundary_semantics(boundary_raw[:-1] + b"\xff\n"),
        )
    )

    def record_mutation(label: str, change: Callable[[dict[str, Any]], None]) -> None:
        changed = copy.deepcopy(record)
        change(changed)
        raw = canonical(module, changed)
        mutations.append((label, lambda raw=raw: validate_record_payload(module, raw)))

    record_mutation(
        "record Q12 true", lambda value: value["qualification"].update(q12=True)
    )
    record_mutation(
        "record R12 issued",
        lambda value: value["qualification"].update(r12="issued"),
    )
    record_mutation(
        "record L12 false",
        lambda value: value["qualification"].update(l12=False),
    )
    record_mutation(
        "record nonzero credit",
        lambda value: value["qualification"].update(hosted_qualification_credit="one"),
    )
    record_mutation(
        "record formula OR",
        lambda value: value["qualification"].update(
            formula=value["qualification"]["formula"].replace(" AND ", " OR ", 1)
        ),
    )
    record_mutation(
        "repository CI revived",
        lambda value: value["hosted_attempt_1"]["repository_ci"].update(
            conclusion="success"
        ),
    )
    record_mutation(
        "dedicated attempt changed",
        lambda value: value["hosted_attempt_1"]["dedicated_v12"].update(attempt=2),
    )
    record_mutation(
        "CodeQL head changed",
        lambda value: value["hosted_attempt_1"]["codeql"].update(head_sha="f" * 40),
    )
    record_mutation(
        "job-count inconsistency",
        lambda value: value["hosted_attempt_1"]["repository_ci"]["job_counts"].update(
            total=46
        ),
    )
    record_mutation(
        "subject C12 changed",
        lambda value: value["subject"].update(c12_commit="f" * 40),
    )
    record_mutation(
        "successor made qualifying",
        lambda value: value["custody"].update(
            successor_workflow_role="qualifying_successor"
        ),
    )
    record_mutation(
        "R12 evidence removed",
        lambda value: value["custody"].update(forbidden_r12_evidence_paths=[]),
    )
    record_mutation(
        "nonimplication removed", lambda value: value["nonimplications"].pop(8)
    )
    mutations.append(
        (
            "duplicate record key",
            lambda: module.parse_json(b'{"q12":false,"q12":true}\n', "record"),
        )
    )
    mutations.append(
        (
            "noncanonical record JSON",
            lambda: validate_record_payload(
                module, json.dumps(record, sort_keys=True).encode("utf-8")
            ),
        )
    )

    def schema_mutation(label: str, change: Callable[[dict[str, Any]], None]) -> None:
        changed = copy.deepcopy(schema)
        change(changed)
        raw = canonical(module, changed)
        mutations.append(
            (
                label,
                lambda raw=raw: validate_schema_payload(module, raw, record),
            )
        )

    schema_mutation(
        "schema Q12 true",
        lambda value: value["properties"]["qualification"]["const"].update(q12=True),
    )
    schema_mutation(
        "schema root additions allowed",
        lambda value: value.update(additionalProperties=True),
    )
    schema_mutation(
        "schema C12 changed",
        lambda value: value["properties"]["subject"]["properties"]["c12_commit"].update(
            const="f" * 40
        ),
    )
    schema_mutation(
        "schema successor made qualifying",
        lambda value: value["properties"]["custody"]["properties"][
            "successor_workflow_role"
        ].update(const="qualifying_successor"),
    )
    schema_mutation(
        "schema R12 absence erased",
        lambda value: value["properties"]["custody"]["properties"][
            "forbidden_r12_evidence_paths"
        ].update(const=[]),
    )
    mutations.append(
        (
            "duplicate schema key",
            lambda: module.parse_json(
                b'{"additionalProperties":false,"additionalProperties":true}\n',
                "schema",
            ),
        )
    )
    mutations.append(
        (
            "noncanonical schema JSON",
            lambda: validate_schema_payload(
                module, json.dumps(schema, sort_keys=True).encode("utf-8"), record
            ),
        )
    )

    good = completed(module)
    terminal_cases = (
        (
            "terminal checker nonzero status",
            completed(module, status=1),
            good,
        ),
        (
            "terminal checker stderr",
            completed(module, stderr=b"warning\n"),
            good,
        ),
        (
            "terminal checker Q12 revival output",
            completed(
                module,
                stdout=module.EXPECTED_TERMINAL_STDOUT.replace(
                    b'"q12":false', b'"q12":true'
                ),
            ),
            good,
        ),
        (
            "terminal checker extra output",
            completed(module, stdout=module.EXPECTED_TERMINAL_STDOUT + b"extra\n"),
            good,
        ),
        (
            "optimized terminal checker differs",
            good,
            completed(
                module,
                stdout=module.EXPECTED_TERMINAL_STDOUT.replace(
                    b'"l12":"not_adjudicated"', b'"l12":false'
                ),
            ),
        ),
    )
    for label, normal, optimized in terminal_cases:
        mutations.append(
            (
                label,
                lambda normal=normal, optimized=optimized: (
                    module.validate_terminal_results(normal, optimized)
                ),
            )
        )

    with tempfile.TemporaryDirectory(prefix="pid-rs-ksg-index-self-test-") as raw_tmp:
        temporary = Path(raw_tmp)

        target = temporary / "target"
        target.write_bytes(b"x")
        target.chmod(0o644)
        symlink = temporary / "symlink"
        symlink.symlink_to(target.name)
        mutations.append(
            (
                "symlink artifact",
                lambda: module.stable_read(
                    temporary, "symlink", 1, hashlib.sha256(b"x").hexdigest()
                ),
            )
        )

        hard_target = temporary / "hard-target"
        hard_target.write_bytes(b"x")
        hard_target.chmod(0o644)
        hardlink = temporary / "hardlink"
        os.link(hard_target, hardlink)
        mutations.append(
            (
                "hard-linked artifact",
                lambda: module.stable_read(
                    temporary, "hardlink", 1, hashlib.sha256(b"x").hexdigest()
                ),
            )
        )

        fifo = temporary / "fifo"
        os.mkfifo(fifo, 0o644)
        mutations.append(
            (
                "nonregular artifact",
                lambda: module.stable_read(
                    temporary, "fifo", 0, hashlib.sha256(b"").hexdigest()
                ),
            )
        )

        wrong_mode = temporary / "wrong-mode"
        wrong_mode.write_bytes(b"x")
        wrong_mode.chmod(0o600)
        mutations.append(
            (
                "wrong artifact mode",
                lambda: module.stable_read(
                    temporary, "wrong-mode", 1, hashlib.sha256(b"x").hexdigest()
                ),
            )
        )

        wrong_digest = temporary / "wrong-digest"
        wrong_digest.write_bytes(b"x")
        wrong_digest.chmod(0o644)
        mutations.append(
            (
                "wrong artifact digest",
                lambda: module.stable_read(
                    temporary, "wrong-digest", 1, hashlib.sha256(b"y").hexdigest()
                ),
            )
        )

        for label, operation in mutations:
            expect_contract_refusal(module, label, operation)

    plain = run_checker(())
    require(
        plain.returncode == 2
        and plain.stdout == b""
        and b"requires Python 3.11+ -I -S -B" in plain.stderr,
        "non-isolated checker launch was accepted",
    )
    overoptimized = run_checker(("-OO", "-I", "-S", "-B"))
    require(
        overoptimized.returncode == 2
        and overoptimized.stdout == b""
        and b"requires Python 3.11+ -I -S -B" in overoptimized.stderr,
        "double-optimized checker launch was accepted",
    )

    result = {
        "baseline_modes": ["normal", "optimized"],
        "hostile_mutations_rejected": len(mutations) + 2,
        "result": "pass",
        "schema": "pid-rs/ksg-revision4-terminal-index-self-test/v1",
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


def main() -> int:
    try:
        return run()
    except (SelfTestError, OSError, subprocess.SubprocessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
