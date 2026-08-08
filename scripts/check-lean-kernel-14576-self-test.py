#!/usr/bin/env python3
"""Fail-closed controls for the exact Lean kernel #14576 regression gate."""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if _bootstrap_sys.version_info < (3, 11):
    print(
        "ERROR: check-lean-kernel-14576-self-test.py requires Python >= 3.11",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
if not (
    _bootstrap_sys.flags.isolated == 1
    and getattr(_bootstrap_sys.flags, "safe_path", False) is True
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.flags.dont_write_bytecode == 1
):
    print(
        "ERROR: check-lean-kernel-14576-self-test.py requires Python -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import py_compile
import stat
import subprocess
import sys
import tempfile
import time
import types
from typing import Callable


SELF_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SELF_PATH.parent.parent
CHECKER_PATH = ROOT / "scripts/check-lean-kernel-14576.py"
EXPECTED_CHECKER_SOURCE_SHA256 = (
    "9e6881e90c42475607aef3ceb42161ad6a32b971471029d063703043c7e337b4"
)
EXPECTED_NEGATIVE_CONTROL_COUNT = 199


class SelfTestError(RuntimeError):
    """The baseline or one separately named negative control failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def source_parent_identities(
    path: Path, role: str
) -> tuple[tuple[str, int, int, int], ...]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    identities: list[tuple[str, int, int, int]] = []
    for parent in reversed(absolute.parents):
        observed = parent.lstat()
        require(
            stat.S_ISDIR(observed.st_mode) and not stat.S_ISLNK(observed.st_mode),
            f"{role} traverses a symbolic-link or non-directory parent",
        )
        identities.append(
            (os.fspath(parent), observed.st_dev, observed.st_ino, observed.st_mode)
        )
    return tuple(identities)


def source_stat_identity(
    observed: os.stat_result,
) -> tuple[int, int, int, int, int, int, int]:
    return (
        observed.st_dev,
        observed.st_ino,
        observed.st_mode,
        observed.st_nlink,
        observed.st_size,
        observed.st_mtime_ns,
        observed.st_ctime_ns,
    )


def read_all(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def read_exact_source(path: Path, *, expected_sha256: str, role: str) -> bytes:
    absolute = Path(os.path.abspath(os.fspath(path)))
    parents_before = source_parent_identities(absolute, role)
    try:
        before = absolute.lstat()
    except OSError as error:
        raise SelfTestError(f"cannot lstat {role}: {error}") from error
    require(stat.S_ISREG(before.st_mode), f"{role} is not a regular file")
    require(not absolute.is_symlink(), f"{role} is a symbolic link")
    require(before.st_nlink == 1, f"{role} must have one hard link")
    require(stat.S_IMODE(before.st_mode) == 0o644, f"{role} mode must be 0644")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
        descriptor_before = os.fstat(descriptor)
        first = read_all(descriptor)
        middle = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = read_all(descriptor)
        descriptor_after = os.fstat(descriptor)
    except OSError as error:
        raise SelfTestError(f"cannot read {role}: {error}") from error
    finally:
        if "descriptor" in locals():
            os.close(descriptor)
    after = absolute.lstat()
    identities = tuple(
        source_stat_identity(item)
        for item in (before, descriptor_before, middle, descriptor_after, after)
    )
    require(
        all(identity == identities[0] for identity in identities[1:]),
        f"{role} metadata changed during double read",
    )
    require(first == second, f"{role} bytes changed during double read")
    require(len(first) == before.st_size, f"{role} byte length changed during read")
    require(
        source_parent_identities(absolute, role) == parents_before,
        f"{role} parent identity changed during double read",
    )
    actual = hashlib.sha256(first).hexdigest()
    require(actual == expected_sha256, f"{role} exact source digest differs")
    return first


def load_exact_module(
    path: Path, *, expected_sha256: str, role: str
) -> tuple[types.ModuleType, bytes]:
    raw = read_exact_source(
        path,
        expected_sha256=expected_sha256,
        role=role,
    )
    safe_role = "".join(character if character.isalnum() else "_" for character in role)
    base_name = f"_pid_rs_exact_{safe_role}_{expected_sha256}"
    module_name = base_name
    suffix = 0
    while module_name in sys.modules:
        suffix += 1
        module_name = f"{base_name}_{suffix}"
    code = compile(
        raw,
        os.fspath(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module, raw


def load_checker() -> tuple[types.ModuleType, bytes]:
    return load_exact_module(
        CHECKER_PATH,
        expected_sha256=EXPECTED_CHECKER_SOURCE_SHA256,
        role="Lean #14576 checker",
    )


checker, CHECKER_SOURCE = load_checker()


def expect_typed_failure(
    name: str,
    operation: Callable[[], object],
    expected: str,
    *,
    exception_type: type[BaseException] = checker.LeanKernel14576Error,
) -> dict[str, object]:
    try:
        operation()
    except exception_type as error:
        observed = str(error)
        require(
            expected in observed,
            f"{name} failed for wrong reason: expected {expected!r}, found {observed!r}",
        )
        # Retain the exact asserted rejection predicate, not a host-specific
        # diagnostic that may contain the random TemporaryDirectory pathname.
        # The full observed message is still checked above before this stable
        # evidence projection is emitted.
        return {"name": name, "rejected": True, "reason_contains": expected}
    raise SelfTestError(f"negative control survived: {name}")


def version_controls() -> list[dict[str, object]]:
    valid = (
        b"Lean (version 4.32.2, x86_64-unknown-linux-gnu, commit "
        b"f3b06c705e6c85f5314019d5d3baab0fec5b580c, Release)\n"
    )
    positive = checker.parse_version_result(checker.ProcessResult(0, valid, b""))
    require(positive.version == "4.32.2", "positive version control drifted")
    cases = (
        ("version_nonzero", checker.ProcessResult(7, valid, b""), "exited 7"),
        (
            "version_stderr",
            checker.ProcessResult(0, valid, b"warning\n"),
            "emitted stderr",
        ),
        (
            "version_wrong_patch",
            checker.ProcessResult(0, valid.replace(b"4.32.2", b"4.32.0"), b""),
            "unexpected Lean version",
        ),
        (
            "version_wrong_commit",
            checker.ProcessResult(0, valid.replace(b"f3b06c", b"03b06c", 1), b""),
            "unexpected Lean source commit",
        ),
        (
            "version_debug",
            checker.ProcessResult(0, valid.replace(b"Release", b"Debug"), b""),
            "unexpected Lean build kind",
        ),
        (
            "version_missing_newline",
            checker.ProcessResult(0, valid[:-1], b""),
            "unexpected Lean version output",
        ),
        (
            "version_extra_line",
            checker.ProcessResult(0, valid + b"extra\n", b""),
            "unexpected Lean version output",
        ),
        (
            "version_malformed_platform",
            checker.ProcessResult(
                0, valid.replace(b"x86_64-unknown-linux-gnu", b"linux"), b""
            ),
            "unexpected Lean version output",
        ),
        (
            "version_crlf",
            checker.ProcessResult(0, valid[:-1] + b"\r\n", b""),
            "carriage return",
        ),
    )
    results = [
        expect_typed_failure(
            name,
            lambda result=result: checker.parse_version_result(result),
            expected,
        )
        for name, result, expected in cases
    ]
    results.append(
        expect_typed_failure(
            "post_version_identity_substitution",
            lambda: checker.require_same_lean_identity(
                positive,
                replace(positive, commit="03b06c705e6c85f5314019d5d3baab0fec5b580c"),
            ),
            "identity changed across regression execution",
        )
    )
    results.append(
        expect_typed_failure(
            "post_version_platform_substitution",
            lambda: checker.require_same_lean_identity(
                positive,
                replace(positive, platform="aarch64-unknown-linux-gnu"),
            ),
            "identity changed across regression execution",
        )
    )
    return results


def lake_version_controls() -> list[dict[str, object]]:
    valid = b"Lake version 5.0.0-src+f3b06c7 (Lean version 4.32.2)\n"
    positive = checker.parse_lake_version_result(checker.ProcessResult(0, valid, b""))
    require(
        positive.version == checker.EXPECTED_LAKE_VERSION,
        "positive Lake version drifted",
    )
    cases = (
        ("lake_version_nonzero", checker.ProcessResult(9, valid, b""), "exited 9"),
        (
            "lake_version_stderr",
            checker.ProcessResult(0, valid, b"warning\n"),
            "emitted stderr",
        ),
        (
            "lake_version_wrong_version",
            checker.ProcessResult(0, valid.replace(b"5.0.0", b"5.0.1"), b""),
            "unexpected Lake version",
        ),
        (
            "lake_version_wrong_commit",
            checker.ProcessResult(0, valid.replace(b"f3b06c7", b"03b06c7"), b""),
            "unexpected Lake version",
        ),
        (
            "lake_version_wrong_lean",
            checker.ProcessResult(0, valid.replace(b"4.32.2", b"4.32.1"), b""),
            "unexpected Lake Lean version",
        ),
        (
            "lake_version_missing_newline",
            checker.ProcessResult(0, valid[:-1], b""),
            "unexpected Lake version output",
        ),
        (
            "lake_version_extra_line",
            checker.ProcessResult(0, valid + b"extra\n", b""),
            "unexpected Lake version output",
        ),
        (
            "lake_version_crlf",
            checker.ProcessResult(0, valid[:-1] + b"\r\n", b""),
            "carriage return",
        ),
    )
    results = [
        expect_typed_failure(
            name,
            lambda result=result: checker.parse_lake_version_result(result),
            expected,
        )
        for name, result, expected in cases
    ]
    results.append(
        expect_typed_failure(
            "post_lake_identity_substitution",
            lambda: checker.require_same_lake_identity(
                positive,
                replace(positive, version="5.0.1-src+f3b06c7"),
            ),
            "Lake identity changed across regression execution",
        )
    )
    return results


def direct_toolchain_controls() -> list[dict[str, object]]:
    checker_source = checker.snapshot(checker.SCRIPT_PATH)
    metadata_snapshot = checker.snapshot(checker.TOOLCHAIN_METADATA_PATH)
    metadata = checker.load_toolchain_metadata_policy(metadata_snapshot, checker_source)
    assets = metadata["assets"]
    require(
        isinstance(assets, list)
        and [asset.get("key") for asset in assets if isinstance(asset, dict)]
        == ["darwin-aarch64", "linux-x86_64"],
        "toolchain asset inventory drifted",
    )
    asset = assets[0]
    require(isinstance(asset, dict), "Darwin asset baseline is malformed")
    mutated_metadata = json.loads(json.dumps(metadata))
    mutated_metadata["subject"]["release"]["tag"] = "v4.32.1"
    mutated_bytes = checker.canonical_metadata_bytes(mutated_metadata)
    mutated_snapshot = replace(
        metadata_snapshot,
        data=mutated_bytes,
        sha256=hashlib.sha256(mutated_bytes).hexdigest(),
    )
    nested_size_mutation = json.loads(json.dumps(metadata))
    nested_size_mutation["checker_binding"]["nested_checker_binding"]["bytes"] += 1
    nested_size_bytes = checker.canonical_metadata_bytes(nested_size_mutation)
    nested_size_snapshot = replace(
        metadata_snapshot,
        data=nested_size_bytes,
        sha256=hashlib.sha256(nested_size_bytes).hexdigest(),
    )
    nested_sha_mutation = json.loads(json.dumps(metadata))
    nested_sha_mutation["checker_binding"]["nested_checker_binding"]["sha256"] = (
        "0" * 64
    )
    nested_sha_bytes = checker.canonical_metadata_bytes(nested_sha_mutation)
    nested_sha_snapshot = replace(
        metadata_snapshot,
        data=nested_sha_bytes,
        sha256=hashlib.sha256(nested_sha_bytes).hexdigest(),
    )

    def select_host_asset(
        candidate_metadata: dict[str, object], system: str, machine: str
    ) -> object:
        original_system = checker.platform.system
        original_machine = checker.platform.machine
        checker.platform.system = lambda: system
        checker.platform.machine = lambda: machine
        try:
            return checker.reviewed_strict_replay_host_asset(candidate_metadata)
        finally:
            checker.platform.system = original_system
            checker.platform.machine = original_machine

    selected_darwin = select_host_asset(metadata, "Darwin", "arm64")
    require(selected_darwin is asset, "reviewed Darwin strict-replay selection drifted")
    old_qualified = json.loads(json.dumps(metadata))
    old_qualified["assets"][0]["custody_lifecycle"]["state"] = "qualified"
    wrong_route = json.loads(json.dumps(metadata))
    wrong_route["assets"][0]["custody_lifecycle"]["permitted_route"] = (
        "observation_only"
    )

    results = [
        expect_typed_failure(
            "toolchain_metadata_policy_drift",
            lambda: checker.load_toolchain_metadata_policy(
                mutated_snapshot, checker_source
            ),
            "metadata policy projection SHA-256 drifted",
        ),
        expect_typed_failure(
            "toolchain_nested_self_size_substitution",
            lambda: checker.load_toolchain_metadata_policy(
                nested_size_snapshot, checker_source
            ),
            "nested checker byte-length binding drifted",
        ),
        expect_typed_failure(
            "toolchain_nested_self_sha_substitution",
            lambda: checker.load_toolchain_metadata_policy(
                nested_sha_snapshot, checker_source
            ),
            "nested checker SHA-256 binding drifted",
        ),
        expect_typed_failure(
            "toolchain_linux_host_remains_pending",
            lambda: select_host_asset(metadata, "Linux", "x86_64"),
            "is not a reviewed-pin strict-replay asset",
        ),
        expect_typed_failure(
            "toolchain_old_qualified_state_rejected",
            lambda: select_host_asset(old_qualified, "Darwin", "arm64"),
            "is not a reviewed-pin strict-replay asset",
        ),
        expect_typed_failure(
            "toolchain_reviewed_state_observation_route_rejected",
            lambda: select_host_asset(wrong_route, "Darwin", "arm64"),
            "is not a reviewed-pin strict-replay asset",
        ),
        expect_typed_failure(
            "direct_toolchain_relative_root",
            lambda: checker.snapshot_direct_toolchain(
                Path("lean-4.32.2-darwin_aarch64"), asset
            ),
            "--toolchain-root must be absolute",
        ),
    ]
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-14576-direct-root-selftest-"
    ) as temporary:
        root = Path(temporary).resolve(strict=True)
        wrong = root / "wrong-root"
        wrong.mkdir()
        results.append(
            expect_typed_failure(
                "direct_toolchain_wrong_archive_root",
                lambda: checker.snapshot_direct_toolchain(wrong, asset),
                "basename differs from reviewed archive root",
            )
        )
        target = root / "lean-4.32.2-darwin_aarch64"
        target.mkdir()
        link = root / "linked-root"
        link.symlink_to(target, target_is_directory=True)
        linked_asset = json.loads(json.dumps(asset))
        linked_asset["archive"]["root"] = "linked-root"
        results.append(
            expect_typed_failure(
                "direct_toolchain_symbolic_root",
                lambda: checker.snapshot_direct_toolchain(link, linked_asset),
                "not a real directory",
            )
        )
    return results


def process_result_controls() -> list[dict[str, object]]:
    spec = checker.FIXTURES[0]
    valid = checker.ProcessResult(0, spec.canary + b"\n", b"")
    checker.validate_fixture_result(spec, valid)
    cases = (
        ("arbitrary_nonzero", checker.ProcessResult(1, b"", b""), "exit 1"),
        (
            "unrelated_parse_error",
            checker.ProcessResult(1, b"", b"parse error\n"),
            "exit 1",
        ),
        (
            "unrelated_import_error",
            checker.ProcessResult(1, b"", b"unknown module\n"),
            "exit 1",
        ),
        ("signal_exit", checker.ProcessResult(-9, b"", b""), "exit -9"),
        ("missing_eof_canary", checker.ProcessResult(0, b"", b""), "EOF canary"),
        ("wrong_eof_canary", checker.ProcessResult(0, b"wrong\n", b""), "EOF canary"),
        (
            "truncated_eof_canary",
            checker.ProcessResult(0, spec.canary, b""),
            "EOF canary",
        ),
        (
            "extra_stdout",
            checker.ProcessResult(0, spec.canary + b"\nextra\n", b""),
            "EOF canary",
        ),
        (
            "successful_stderr",
            checker.ProcessResult(0, spec.canary + b"\n", b"warning\n"),
            "unexpected stderr",
        ),
        (
            "stdout_crlf",
            checker.ProcessResult(0, spec.canary + b"\r\n", b""),
            "carriage return",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda result=result: checker.validate_fixture_result(spec, result),
            expected,
        )
        for name, result, expected in cases
    ]


def leanchecker_fresh_environment_replay_result_controls() -> list[dict[str, object]]:
    module = "Issue14576Full"
    valid = checker.ProcessResult(0, b"", b"")
    checker.validate_leanchecker_fresh_environment_replay_result(module, valid)
    cases = (
        ("leanchecker_nonzero", replace(valid, returncode=1), "exited 1"),
        (
            "leanchecker_stdout",
            replace(valid, stdout=b"unexpected\n"),
            "emitted stdout",
        ),
        (
            "leanchecker_stderr",
            replace(valid, stderr=b"unexpected\n"),
            "emitted stderr",
        ),
        (
            "leanchecker_stdout_cr",
            replace(valid, stdout=b"unexpected\r"),
            "stdout contains CR",
        ),
        (
            "leanchecker_stderr_cr",
            replace(valid, stderr=b"unexpected\r"),
            "stderr contains CR",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda result=result: (
                checker.validate_leanchecker_fresh_environment_replay_result(
                    module, result
                )
            ),
            expected,
        )
        for name, result, expected in cases
    ]


def target_olean_inventory_probe_result_controls() -> list[dict[str, object]]:
    spec = checker.FIXTURES[0]
    valid = checker.ProcessResult(0, spec.target_olean_inventory_canary + b"\n", b"")
    checker.validate_target_olean_inventory_probe_result(spec, valid)
    cases = (
        ("inventory_probe_nonzero", replace(valid, returncode=1), "exited 1"),
        (
            "inventory_probe_wrong_canary",
            replace(valid, stdout=b"wrong\n"),
            "EOF canary drifted",
        ),
        (
            "inventory_probe_stderr",
            replace(valid, stderr=b"warning\n"),
            "emitted stderr",
        ),
        (
            "inventory_probe_stdout_cr",
            replace(valid, stdout=spec.target_olean_inventory_canary + b"\r\n"),
            "stdout contains CR",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda result=result: checker.validate_target_olean_inventory_probe_result(
                spec, result
            ),
            expected,
        )
        for name, result, expected in cases
    ]


def target_olean_inventory_probe_source_controls() -> list[dict[str, object]]:
    expected = {
        "issue_14576.lean": (
            "Issue14576Full",
            621,
            "9e62ee47c67457f21ad6cdab44c69fec42b0a7a7b9ad347416294b69edf4f033",
        ),
        "issue_14576_min.lean": (
            "Issue14576Min",
            560,
            "7804185ed6b01627e02cfdd5b03ac36a19cd0d4f4411373dd64f97d972b8f47a",
        ),
    }
    results: list[dict[str, object]] = []
    for spec in checker.FIXTURES:
        module, expected_bytes, expected_sha256 = expected[spec.name]
        source = checker.target_olean_inventory_probe(spec, module)
        checker.validate_target_olean_inventory_probe_source(spec, module, source)
        require(len(source) == expected_bytes, "inventory-probe source bytes drifted")
        require(
            hashlib.sha256(source).hexdigest() == expected_sha256,
            "inventory-probe source SHA-256 drifted",
        )
        cases = (
            (
                "bracketing_positive",
                source.replace(
                    b"info: axiom PidRsTargetOleanLookupPositive : Nat",
                    b"info: theorem PidRsTargetOleanLookupPositive : Nat",
                    1,
                ),
                "separate-positive clause",
            ),
            (
                "bracketing_negative",
                source.replace(
                    b"Unknown constant `PidRsTargetOleanLookupNegative`",
                    b"Unknown constant `PidRsTargetOleanLookupMissing`",
                    1,
                ),
                "separate-negative clause",
            ),
            (
                "residual_axiom_shaped_E",
                source.replace(b"info: axiom E : sorry", b"info: theorem E : sorry", 1),
                "residual-E clause",
            ),
            (
                "absent_E_mk",
                source.replace(
                    b"Unknown constant `E.mk`", b"Unknown constant `E.Mk`", 1
                ),
                "absent-E.mk clause",
            ),
            (
                "EOF",
                source.replace(spec.target_olean_inventory_canary, b"wrong-canary", 1),
                "EOF clause",
            ),
        )
        if spec.name == "issue_14576.lean":
            cases += (
                (
                    "post_abort_absent_bad",
                    source.replace(
                        b"Unknown constant `bad`", b"Unknown constant `Bad`", 1
                    ),
                    "full-only post-abort absent-bad clause",
                ),
            )
        else:
            cases += (
                (
                    "unexpected_bad_probe",
                    source.replace(
                        b"#eval IO.println",
                        b"/-- error: Unknown constant `bad` -/\n"
                        b"#guard_msgs in\n#print bad\n\n#eval IO.println",
                        1,
                    ),
                    "full-only post-abort absent-bad clause",
                ),
            )
        results.extend(
            expect_typed_failure(
                f"{spec.name}_inventory_probe_{name}_source_drift",
                lambda mutated=mutated, spec=spec, module=module: (
                    checker.validate_target_olean_inventory_probe_source(
                        spec, module, mutated
                    )
                ),
                reason,
            )
            for name, mutated, reason in cases
        )
    return results


def nested_timing_contract_controls() -> list[dict[str, object]]:
    valid = checker.nested_timing_contract()

    def mutated(key: str, value: object) -> dict[str, object]:
        candidate = dict(valid)
        candidate[key] = value
        return candidate

    cases = (
        (
            "nested_timing_inner_bound",
            mutated("inner_per_replay_timeout_seconds", 899),
            "inner bound drifted",
        ),
        (
            "nested_timing_replay_count",
            mutated("replay_count", 2),
            "replay count drifted",
        ),
        (
            "nested_timing_non_replay_lean_child_bound",
            mutated("non_replay_lean_child_timeout_seconds", 119),
            "non-replay Lean-child bound drifted",
        ),
        (
            "nested_timing_non_replay_lean_child_count",
            mutated("non_replay_lean_child_count", 5),
            "non-replay Lean-child count drifted",
        ),
        (
            "nested_timing_identity_child_bound",
            mutated("identity_child_timeout_seconds", 59),
            "identity-child bound drifted",
        ),
        (
            "nested_timing_identity_child_count",
            mutated("identity_child_count", 3),
            "identity-child count drifted",
        ),
        (
            "nested_timing_orchestration_headroom",
            mutated("orchestration_headroom_seconds", 239),
            "orchestration headroom drifted",
        ),
        (
            "nested_timing_non_replay_allocation",
            mutated("declared_non_replay_margin_seconds", 1_199),
            "non-replay allocation drifted or is contradictory",
        ),
        (
            "nested_timing_required_outer_bound",
            mutated("required_outer_timeout_seconds", 3_899),
            "required outer bound drifted or is contradictory",
        ),
        (
            "nested_timing_derivation",
            mutated("derivation", "arbitrary"),
            "derivation drifted",
        ),
        (
            "nested_timing_environmental_premise",
            mutated("environmental_premise", "guaranteed"),
            "environmental premise drifted",
        ),
        (
            "nested_timing_extra_key",
            mutated("unexpected", True),
            "keys drifted",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda candidate=candidate: checker.validate_nested_timing_contract(
                candidate
            ),
            reason,
        )
        for name, candidate, reason in cases
    ]


def unguarded_result_controls() -> list[dict[str, object]]:
    query = Path("/private/tmp/pid-rs-lean-14576-self-test/issue_14576_unguarded.lean")
    diagnostic = f"{query}:58:0: error: (kernel) invalid projection\n  w.1\n".encode(
        "utf-8"
    )
    valid = checker.ProcessResult(1, diagnostic + checker.UNGUARDED_CANARY + b"\n", b"")
    checker.validate_unguarded_result(query, valid)
    cases = (
        ("unguarded_zero_exit", replace(valid, returncode=0), "exited 0, expected 1"),
        (
            "unguarded_arbitrary_nonzero",
            replace(valid, returncode=2),
            "exited 2, expected 1",
        ),
        (
            "unguarded_missing_canary",
            replace(valid, stdout=diagnostic),
            "diagnostic/EOF output drifted",
        ),
        (
            "unguarded_unrelated_diagnostic",
            replace(
                valid,
                stdout=(
                    f"{query}:58:0: error: parse error\n".encode("utf-8")
                    + checker.UNGUARDED_CANARY
                    + b"\n"
                ),
            ),
            "diagnostic/EOF output drifted",
        ),
        (
            "unguarded_extra_diagnostic",
            replace(
                valid, stdout=diagnostic + b"extra\n" + checker.UNGUARDED_CANARY + b"\n"
            ),
            "diagnostic/EOF output drifted",
        ),
        (
            "unguarded_truncated_diagnostic",
            replace(valid, stdout=diagnostic[:-1] + checker.UNGUARDED_CANARY + b"\n"),
            "diagnostic/EOF output drifted",
        ),
        (
            "unguarded_stdout_crlf",
            replace(valid, stdout=diagnostic + checker.UNGUARDED_CANARY + b"\r\n"),
            "stdout contains a carriage return",
        ),
        (
            "unguarded_stderr_crlf",
            replace(valid, stderr=b"unexpected\r\n"),
            "stderr contains a carriage return",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda result=result: checker.validate_unguarded_result(query, result),
            expected,
        )
        for name, result, expected in cases
    ]


def benign_result_controls() -> list[dict[str, object]]:
    valid = checker.ProcessResult(0, checker.BENIGN_CANARY + b"\n", b"")
    checker.validate_benign_result(valid)
    cases = (
        ("benign_nonzero", replace(valid, returncode=1), "exited 1"),
        ("benign_missing_canary", replace(valid, stdout=b""), "EOF canary"),
        (
            "benign_extra_stdout",
            replace(valid, stdout=checker.BENIGN_CANARY + b"\nextra\n"),
            "EOF canary",
        ),
        (
            "benign_unexpected_stderr",
            replace(valid, stderr=b"warning\n"),
            "unexpected stderr",
        ),
        (
            "benign_stdout_crlf",
            replace(valid, stdout=checker.BENIGN_CANARY + b"\r\n"),
            "stdout contains a carriage return",
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda result=result: checker.validate_benign_result(result),
            expected,
        )
        for name, result, expected in cases
    ]


def command_controls() -> list[dict[str, object]]:
    lean = Path("/private/tmp/pid-rs-lean-14576-self-test/toolchain/bin/lean")
    lake = lean.with_name("lake")
    leanchecker = lean.with_name("leanchecker")
    source = Path("/private/tmp/pid-rs-lean-14576-self-test/query.lean")
    olean = source.with_suffix(".olean")
    module = "Issue14576Full"
    version = checker.lean_version_command(lean)
    lake_version = checker.lake_version_command(lake)
    checked = checker.lean_source_command(lean, source)
    compiled = checker.lean_compile_command(lean, source, olean)
    replayed = checker.leanchecker_command(leanchecker, module)
    checker.validate_lean_version_command(version, lean)
    checker.validate_lake_version_command(lake_version, lake)
    checker.validate_lean_source_command(checked, lean, source)
    checker.validate_lean_compile_command(compiled, lean, source, olean)
    checker.validate_leanchecker_command(replayed, leanchecker, module)
    cases = (
        (
            "version_command_shim_route",
            lambda: checker.validate_lean_version_command(
                ("/usr/bin/env", "lean", "--version"), lean
            ),
            "version command arguments drifted",
        ),
        (
            "version_command_extra_argument",
            lambda: checker.validate_lean_version_command(
                (*version, "--trust=0"), lean
            ),
            "version command arguments drifted",
        ),
        (
            "lake_version_command_extra_argument",
            lambda: checker.validate_lake_version_command(
                (*lake_version, "extra"), lake
            ),
            "Lake version command arguments drifted",
        ),
        (
            "source_command_missing_trust_zero",
            lambda: checker.validate_lean_source_command(
                (str(lean), str(source)), lean, source
            ),
            "source command arguments drifted",
        ),
        (
            "source_command_wrong_trust",
            lambda: checker.validate_lean_source_command(
                (str(lean), "--trust=1", str(source)),
                lean,
                source,
            ),
            "source command arguments drifted",
        ),
        (
            "source_command_reordered_trust",
            lambda: checker.validate_lean_source_command(
                (str(lean), str(source), "--trust=0"),
                lean,
                source,
            ),
            "source command arguments drifted",
        ),
        (
            "source_command_extra_argument",
            lambda: checker.validate_lean_source_command(
                (*checked, "--quiet"), lean, source
            ),
            "source command arguments drifted",
        ),
        (
            "compile_command_missing_trust_zero",
            lambda: checker.validate_lean_compile_command(
                (str(lean), "-o", str(olean), str(source)),
                lean,
                source,
                olean,
            ),
            "compile command arguments drifted",
        ),
        (
            "compile_command_wrong_order",
            lambda: checker.validate_lean_compile_command(
                (str(lean), "-o", str(olean), "--trust=0", str(source)),
                lean,
                source,
                olean,
            ),
            "compile command arguments drifted",
        ),
        (
            "compile_command_output_source_reversed",
            lambda: checker.validate_lean_compile_command(
                (str(lean), "--trust=0", "-o", str(source), str(olean)),
                lean,
                source,
                olean,
            ),
            "compile command arguments drifted",
        ),
        (
            "leanchecker_missing_fresh",
            lambda: checker.validate_leanchecker_command(
                (str(leanchecker), module), leanchecker, module
            ),
            "leanchecker command arguments drifted",
        ),
        (
            "leanchecker_wrong_fresh_order",
            lambda: checker.validate_leanchecker_command(
                (str(leanchecker), module, "--fresh"), leanchecker, module
            ),
            "leanchecker command arguments drifted",
        ),
        (
            "leanchecker_wrong_module",
            lambda: checker.validate_leanchecker_command(
                (str(leanchecker), "Issue14576Min"), leanchecker, module
            ),
            "leanchecker command arguments drifted",
        ),
        (
            "leanchecker_extra_argument",
            lambda: checker.validate_leanchecker_command(
                (*replayed, "extra"), leanchecker, module
            ),
            "leanchecker command arguments drifted",
        ),
        (
            "leanchecker_unsafe_module_grammar",
            lambda: checker.leanchecker_command(leanchecker, "../alternate"),
            "outside the finite safe grammar",
        ),
        (
            "relative_version_executable",
            lambda: checker.lean_version_command(Path("lean")),
            "executable route is not absolute",
        ),
        (
            "relative_source_executable",
            lambda: checker.lean_source_command(Path("lean"), source),
            "executable route is not absolute",
        ),
        (
            "relative_source_route",
            lambda: checker.lean_source_command(lean, Path("query.lean")),
            "source route is not absolute",
        ),
        (
            "relative_compile_output_route",
            lambda: checker.lean_compile_command(lean, source, Path("query.olean")),
            "output route is not absolute",
        ),
        (
            "relative_leanchecker_executable",
            lambda: checker.leanchecker_command(Path("leanchecker"), module),
            "executable route is not absolute",
        ),
    )
    return [
        expect_typed_failure(name, operation, expected)
        for name, operation, expected in cases
    ]


def executable_and_diagnostic_path_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-paths-") as temporary:
        root = Path(temporary).resolve(strict=True)
        tool_bin = root / "toolchain" / "bin"
        tool_bin.mkdir(parents=True)
        selected_tools: dict[str, object] = {}
        for role in ("lean", "lake", "leanchecker"):
            leaf = tool_bin / role
            leaf.write_bytes(f"#!/bin/sh\n# {role}\nexit 0\n".encode("ascii"))
            leaf.chmod(0o700)
            selected_tools[role] = checker.snapshot_executable_route(leaf)
        checker.validate_direct_tool_layout(selected_tools)
        results.append(
            expect_typed_failure(
                "direct_tool_inventory_order_substitution",
                lambda: checker.validate_direct_tool_layout(
                    {
                        "lake": selected_tools["lake"],
                        "lean": selected_tools["lean"],
                        "leanchecker": selected_tools["leanchecker"],
                    }
                ),
                "inventory or order drifted",
            )
        )
        other_bin = root / "other" / "bin"
        other_bin.mkdir(parents=True)
        other_checker = other_bin / "leanchecker"
        other_checker.write_bytes(b"#!/bin/sh\nexit 0\n")
        other_checker.chmod(0o700)
        results.append(
            expect_typed_failure(
                "direct_leanchecker_different_toolchain_parent",
                lambda: checker.validate_direct_tool_layout(
                    {
                        "lean": selected_tools["lean"],
                        "lake": selected_tools["lake"],
                        "leanchecker": checker.snapshot_executable_route(other_checker),
                    }
                ),
                "do not share one bin directory",
            )
        )
        executable = root / "lake-real"
        executable.write_bytes(b"#!/bin/sh\nexit 0\n")
        executable.chmod(0o700)
        executable_snapshot = checker.snapshot_executable_route(executable)
        require(
            executable_snapshot.launch_path == executable,
            "executable launch route drifted",
        )
        require(
            executable_snapshot.canonical_path == executable,
            "canonical executable drifted",
        )
        link = root / "lake-link"
        link.symlink_to(executable)
        link_snapshot = checker.snapshot_executable_route(link)
        require(
            link_snapshot.launch_path == link
            and link_snapshot.canonical_path == executable,
            "executable symlink route was not separated from its canonical leaf",
        )
        executable.chmod(0o600)
        results.append(
            expect_typed_failure(
                "executable_mode_removed",
                lambda: checker.snapshot_executable_route(executable),
                "lacks execute mode",
            )
        )
        executable.chmod(0o700)
        executable.write_bytes(b"#!/bin/sh\nexit 1\n")
        executable.chmod(0o700)
        results.append(
            expect_typed_failure(
                "direct_lean_executable_leaf_substitution",
                lambda: checker.require_executable_unchanged(link_snapshot),
                "canonical executable leaf changed",
            )
        )
        directory = root / "executable-directory"
        directory.mkdir()
        results.append(
            expect_typed_failure(
                "executable_directory_route",
                lambda: checker.snapshot_executable_route(directory),
                "neither regular nor symbolic link",
            )
        )
        dangling = root / "dangling"
        dangling.symlink_to(root / "absent")
        results.append(
            expect_typed_failure(
                "dangling_executable_symlink",
                lambda: checker.snapshot_executable_route(dangling),
                "cannot resolve executable",
            )
        )
        results.append(
            expect_typed_failure(
                "relative_executable_snapshot",
                lambda: checker.snapshot_executable_route(Path("lake")),
                "launch route is not absolute",
            )
        )
        first_target = root / "first-target"
        second_target = root / "second-target"
        first_target.write_bytes(b"#!/bin/sh\nexit 0\n")
        second_target.write_bytes(b"#!/bin/sh\nexit 0\n")
        first_target.chmod(0o700)
        second_target.chmod(0o700)
        mutable_link = root / "mutable-link"
        mutable_link.symlink_to(first_target)
        route_before_mutation = checker.snapshot_executable_route(mutable_link)
        mutable_link.unlink()
        mutable_link.symlink_to(second_target)
        results.append(
            expect_typed_failure(
                "selected_lean_executable_symlink_retarget",
                lambda: checker.require_executable_unchanged(route_before_mutation),
                "executable launch route changed",
            )
        )

    portable = Path("/private/tmp/pid-rs-lean-14576 path/λ-query.lean")
    expected = f"{portable}:58:0: error: (kernel) invalid projection\n  w.1\n".encode(
        "utf-8"
    )
    require(
        checker.expected_unguarded_diagnostic(portable) == expected,
        "space/Unicode diagnostic-path positive control drifted",
    )
    results.extend(
        [
            expect_typed_failure(
                "relative_diagnostic_path",
                lambda: checker.expected_unguarded_diagnostic(Path("query.lean")),
                "route is not absolute",
            ),
            expect_typed_failure(
                "line_break_diagnostic_path",
                lambda: checker.expected_unguarded_diagnostic(
                    Path("/private/tmp/query\nmutated.lean")
                ),
                "contains a line break",
            ),
        ]
    )
    return results


def environment_route_controls() -> list[dict[str, object]]:
    checker.require_environment_scrubbed(checker.scrubbed_environment())
    contaminated_environment = {
        "HOME": "/retained/home",
        "PATH": "/alternate/bin",
        "LEAN_SYSROOT": "/alternate/sysroot",
        "LEAN_PATH": "/alternate/imports",
        "LAKE_HOME": "/alternate/lake",
        "ELAN_TOOLCHAIN": "alternate",
        "PYTHONPATH": "/alternate/python",
        "DYLD_INSERT_LIBRARIES": "/alternate/contaminant.dylib",
        "LD_PRELOAD": "/alternate/contaminant.so",
        "GIT_CONFIG_GLOBAL": "/alternate/gitconfig",
        "CC": "/alternate/cc",
    }
    scrubbed = checker.scrubbed_environment(ambient=contaminated_environment)
    checker.require_environment_scrubbed(scrubbed)
    require(scrubbed["PATH"] == checker.SAFE_CHILD_PATH, "fake ambient PATH survived")
    require("HOME" not in scrubbed, "ambient HOME projection survived")
    require(
        not set(contaminated_environment).intersection(scrubbed).difference({"PATH"}),
        "ambient-routing contamination survived explicit projection",
    )
    controlled_import = Path("/private/tmp/pid-rs-lean-14576-self-test/oleans")
    controlled_bin = Path("/private/tmp/pid-rs-lean-14576-self-test/toolchain/bin")
    replay_environment = checker.scrubbed_environment(
        ambient=contaminated_environment,
        lean_path=controlled_import,
        tool_bin=controlled_bin,
    )
    checker.require_environment_scrubbed(
        replay_environment,
        allowed_lean_path=controlled_import,
        allowed_tool_bin=controlled_bin,
    )
    require(
        replay_environment["LEAN_PATH"] == str(controlled_import)
        and replay_environment["PATH"].split(os.pathsep)[0] == str(controlled_bin),
        "controlled leanchecker import/tool routing drifted",
    )
    return [
        expect_typed_failure(
            "ambient_home_routing_contamination",
            lambda: checker.require_environment_scrubbed(
                {
                    "PATH": checker.SAFE_CHILD_PATH,
                    "LANG": "C",
                    "LC_ALL": "C",
                    "HOME": "/ambient/home",
                }
            ),
            "unexpected child-process environment keys remain",
        ),
        expect_typed_failure(
            "ambient_dynamic_loader_routing_contamination",
            lambda: checker.require_environment_scrubbed(
                {
                    "PATH": checker.SAFE_CHILD_PATH,
                    "LANG": "C",
                    "LC_ALL": "C",
                    "LD_PRELOAD": "/tmp/injected.so",
                }
            ),
            "unexpected child-process environment keys remain",
        ),
        expect_typed_failure(
            "ambient_compiler_environment_routing",
            lambda: checker.require_environment_scrubbed(
                {
                    "PATH": checker.SAFE_CHILD_PATH,
                    "LANG": "C",
                    "LC_ALL": "C",
                    "CC": "/tmp/substituted-cc",
                }
            ),
            "unexpected child-process environment keys remain",
        ),
        expect_typed_failure(
            "ambient_path_routing_contamination",
            lambda: checker.require_environment_scrubbed(
                {"PATH": "/alternate/bin", "LANG": "C", "LC_ALL": "C"}
            ),
            "child PATH is not the fixed safe path",
        ),
        expect_typed_failure(
            "ambient_lean_sysroot_routing_contamination",
            lambda: checker.require_environment_scrubbed(
                {
                    "PATH": checker.SAFE_CHILD_PATH,
                    "LANG": "C",
                    "LC_ALL": "C",
                    "LEAN_SYSROOT": "/alternate/sysroot",
                }
            ),
            "unexpected child-process environment keys remain",
        ),
        expect_typed_failure(
            "leanchecker_import_path_substitution",
            lambda: checker.require_environment_scrubbed(
                replay_environment,
                allowed_lean_path=Path("/private/tmp/other-imports"),
                allowed_tool_bin=controlled_bin,
            ),
            "controlled Lean import root drifted",
        ),
        expect_typed_failure(
            "leanchecker_tool_path_substitution",
            lambda: checker.require_environment_scrubbed(
                replay_environment,
                allowed_lean_path=controlled_import,
                allowed_tool_bin=Path("/private/tmp/other-bin"),
            ),
            "child PATH is not the fixed safe path",
        ),
    ]


def interpreter_flag_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for role, path in (("checker", CHECKER_PATH), ("self_test", SELF_PATH)):
        for missing, flags in (
            ("I", ("-S", "-B")),
            ("S", ("-I", "-B")),
            ("B", ("-I", "-S")),
        ):
            process = subprocess.run(
                [sys.executable, *flags, os.fspath(path)],
                cwd=ROOT,
                env=checker.scrubbed_environment(),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            expected = f"ERROR: {path.name} requires Python -I -S -B\n".encode("utf-8")
            require(
                process.returncode == 2
                and process.stdout == b""
                and process.stderr == expected,
                f"{role} missing -{missing} did not fail at the exact bootstrap guard",
            )
            results.append(
                {
                    "name": f"{role}_missing_python_{missing}",
                    "rejected": True,
                    "reason_contains": "requires Python -I -S -B",
                }
            )
    return results


def bootstrap_runtime_contract_controls() -> list[dict[str, object]]:
    valid_flags = types.SimpleNamespace(
        isolated=1,
        safe_path=True,
        no_site=1,
        ignore_environment=1,
        dont_write_bytecode=1,
    )
    require(
        checker._bootstrap_runtime_supported((3, 11), valid_flags),
        "valid Python bootstrap runtime was rejected",
    )
    cases = (
        ("bootstrap_python_minimum", (3, 10), valid_flags),
        (
            "bootstrap_missing_safe_path_attribute",
            (3, 11),
            types.SimpleNamespace(
                isolated=1,
                no_site=1,
                ignore_environment=1,
                dont_write_bytecode=1,
            ),
        ),
        (
            "bootstrap_no_bytecode_state_false",
            (3, 11),
            types.SimpleNamespace(
                isolated=1,
                safe_path=True,
                no_site=1,
                ignore_environment=1,
                dont_write_bytecode=0,
            ),
        ),
    )
    return [
        expect_typed_failure(
            name,
            lambda version=version, flags=flags: require(
                checker._bootstrap_runtime_supported(version, flags),
                "unsupported Python bootstrap runtime",
            ),
            "unsupported Python bootstrap runtime",
            exception_type=SelfTestError,
        )
        for name, version, flags in cases
    ]


def early_exit_descendant_command(
    ready: Path, marker: Path, returncode: int
) -> list[str]:
    descendant = """\
import pathlib
import sys
import time

pathlib.Path(sys.argv[1]).write_text(str(__import__('os').getpid()), encoding='ascii')
time.sleep(0.6)
pathlib.Path(sys.argv[2]).write_text('survived', encoding='ascii')
time.sleep(60)
"""
    leader = """\
import pathlib
import subprocess
import sys
import time

ready = pathlib.Path(sys.argv[1])
subprocess.Popen(
    [sys.executable, '-I', '-S', '-B', '-c', sys.argv[4], sys.argv[1], sys.argv[2]],
    stdin=subprocess.DEVNULL,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    close_fds=True,
)
deadline = time.monotonic() + 5
while not ready.exists() and time.monotonic() < deadline:
    time.sleep(0.01)
if not ready.exists():
    raise SystemExit(99)
raise SystemExit(int(sys.argv[3]))
"""
    return [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-c",
        leader,
        os.fspath(ready),
        os.fspath(marker),
        str(returncode),
        descendant,
    ]


def require_delayed_descendant_absent(marker: Path, role: str) -> None:
    time.sleep(0.75)
    require(not marker.exists(), f"{role} delayed descendant survived group cleanup")


def process_boundary_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    results = [
        expect_typed_failure(
            "stdout_capture_ceiling",
            lambda: checker.run_process(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    f"import sys;sys.stdout.buffer.write(b'x'*{checker.MAX_PROCESS_OUTPUT_BYTES + 1})",
                ],
                cwd=ROOT,
            ),
            "stdout exceeds the post-capture rejection ceiling",
        ),
        expect_typed_failure(
            "stderr_capture_ceiling",
            lambda: checker.run_process(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    f"import sys;sys.stderr.buffer.write(b'x'*{checker.MAX_PROCESS_OUTPUT_BYTES + 1})",
                ],
                cwd=ROOT,
            ),
            "stderr exceeds the post-capture rejection ceiling",
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-tree-") as temporary:
        marker = Path(temporary) / "descendant-survived"
        child = (
            "import pathlib,sys,time;time.sleep(1);"
            "pathlib.Path(sys.argv[1]).write_text('survived');time.sleep(60)"
        )
        parent = (
            "import subprocess,sys,time;"
            "subprocess.Popen([sys.executable,'-I','-S','-B','-c',sys.argv[2],sys.argv[1]]);"
            "time.sleep(60)"
        )
        results.append(
            expect_typed_failure(
                "timeout_process_tree_cleanup",
                lambda: checker.run_process(
                    [
                        sys.executable,
                        "-I",
                        "-S",
                        "-B",
                        "-c",
                        parent,
                        str(marker),
                        child,
                    ],
                    cwd=ROOT,
                    timeout=0.25,
                ),
                "timed out after 0.25 seconds",
            )
        )
        time.sleep(1.25)
        require(
            not marker.exists(),
            "timed-out process descendant survived its process group",
        )
    results.append(
        expect_typed_failure(
            "shared_outer_process_group_boolean_integer_collapse",
            lambda: checker.run_process(
                [sys.executable, "-I", "-S", "-B", "-c", "pass"],
                cwd=ROOT,
                shared_outer_process_group=1,
            ),
            "selection must be Boolean",
        )
    )
    positive_controls: list[dict[str, object]] = []
    private_environment_child = (
        "import os,pathlib,stat;"
        "h=pathlib.Path(os.environ['HOME']);t=pathlib.Path(os.environ['TMPDIR']);"
        "ok=h.parent==t.parent and h.name=='home' and t.name=='tmp' and "
        "all(stat.S_IMODE(p.stat().st_mode)==0o700 for p in (h.parent,h,t)) and "
        "all(k not in os.environ for k in ('LOGNAME','USER'));"
        "raise SystemExit(0 if ok else 93)"
    )
    for mask in (0o000, 0o777):
        previous = os.umask(mask)
        try:
            private_environment_result = checker.run_process(
                [
                    sys.executable,
                    "-I",
                    "-S",
                    "-B",
                    "-c",
                    private_environment_child,
                ],
                cwd=ROOT,
            )
        finally:
            os.umask(previous)
        require(
            private_environment_result == checker.ProcessResult(0, b"", b""),
            f"per-child private environment drifted under umask {mask:03o}",
        )
        positive_controls.append(
            {
                "name": f"per_child_private_home_tmp_umask_{mask:03o}",
                "accepted": True,
                "route": "real_run_process_environment",
            }
        )
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-14576-early-exit-group-"
    ) as temporary:
        root = Path(temporary)
        for returncode in (0, 7):
            ready = root / f"leader-{returncode}.ready"
            marker = root / f"leader-{returncode}.survived"
            observed = checker.run_process(
                early_exit_descendant_command(ready, marker, returncode),
                cwd=ROOT,
            )
            require(
                observed.returncode == returncode,
                f"early leader return code {returncode} drifted",
            )
            require_delayed_descendant_absent(
                marker, f"standalone run_process return code {returncode}"
            )
            positive_controls.append(
                {
                    "name": f"isolated_process_early_leader_exit_{returncode}_cleanup",
                    "accepted": True,
                    "route": "real_run_process",
                }
            )

        ready = root / "wait-exception.ready"
        marker = root / "wait-exception.survived"
        original_popen = checker.subprocess.Popen

        class WaitExceptionProxy:
            def __init__(self, process: subprocess.Popen[bytes]) -> None:
                self._process = process
                self._raised = False

            @property
            def pid(self) -> int:
                return self._process.pid

            @property
            def returncode(self) -> int | None:
                return self._process.returncode

            def poll(self) -> int | None:
                return self._process.poll()

            def wait(self, timeout: float | None = None) -> int:
                if not self._raised:
                    deadline = time.monotonic() + 5
                    while not ready.exists() and time.monotonic() < deadline:
                        time.sleep(0.01)
                    self._raised = True
                    raise RuntimeError("synthetic wait failure")
                return self._process.wait(timeout=timeout)

        def raising_popen(*args: object, **kwargs: object) -> WaitExceptionProxy:
            return WaitExceptionProxy(original_popen(*args, **kwargs))

        checker.subprocess.Popen = raising_popen
        try:
            results.append(
                expect_typed_failure(
                    "process_unexpected_wait_exception_cleans_group",
                    lambda: checker.run_process(
                        early_exit_descendant_command(ready, marker, 0), cwd=ROOT
                    ),
                    "synthetic wait failure",
                    exception_type=RuntimeError,
                )
            )
        finally:
            checker.subprocess.Popen = original_popen
        require_delayed_descendant_absent(marker, "unexpected wait exception")

    if os.name == "posix":
        supervisor = (
            "import hashlib,pathlib,sys,types;"
            "p=pathlib.Path(sys.argv[1]);"
            "raw=p.read_bytes();"
            "hashlib.sha256(raw).hexdigest()==sys.argv[3] or (_ for _ in ()).throw(SystemExit(91));"
            "m=types.ModuleType('shared_checker');m.__file__=str(p);m.__package__='';"
            "m.__loader__=None;m.__spec__=None;m.__cached__=None;"
            "sys.modules['shared_checker']=m;"
            "exec(compile(raw,str(p),'exec',dont_inherit=True,optimize=sys.flags.optimize),m.__dict__);"
            "r=m.run_process([sys.executable,'-I','-S','-B','-c','pass'],"
            "cwd=pathlib.Path(sys.argv[2]),shared_outer_process_group=True);"
            "raise SystemExit(r.returncode)"
        )
        process = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                "-B",
                "-c",
                supervisor,
                os.fspath(CHECKER_PATH),
                os.fspath(ROOT),
                EXPECTED_CHECKER_SOURCE_SHA256,
            ],
            cwd=ROOT,
            env=checker.scrubbed_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            timeout=10,
            check=False,
        )
        require(
            process.returncode == 0 and process.stdout == b"" and process.stderr == b"",
            "shared-group nested mode incorrectly signalled its own supervisor group",
        )
        positive_controls.append(
            {
                "name": "shared_group_mode_does_not_signal_own_group",
                "accepted": True,
                "route": "real_run_process_shared_mode",
                "source_load": "exact_sha256_compile_exec_no_import_loader",
            }
        )
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-lean-14576-umask-control-"
        ) as temporary:
            root = Path(temporary)
            for mask in (0o000, 0o777):
                target = root / f"umask-{mask:03o}"
                previous = os.umask(mask)
                try:
                    target.mkdir(mode=0o700)
                finally:
                    os.umask(previous)
                identity = checker.enforce_private_directory_mode(target)
                require(
                    stat.S_IMODE(identity.mode) == 0o700,
                    f"private-directory mode enforcement failed under umask {mask:03o}",
                )
                positive_controls.append(
                    {
                        "name": f"private_directory_mode_enforced_under_umask_{mask:03o}",
                        "accepted": True,
                        "route": "real_enforce_private_directory_mode",
                    }
                )
    return results, positive_controls


def fixture_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    checker.validate_fixture_inventory(checker.FIXTURES)
    results.append(
        expect_typed_failure(
            "fixture_inventory_reordered",
            lambda: checker.validate_fixture_inventory(
                tuple(reversed(checker.FIXTURES))
            ),
            "fixture order or identity drifted",
        )
    )
    for spec in checker.FIXTURES:
        data = spec.path.read_bytes()
        checker.validate_fixture_payload(spec, data)
        if spec.name == "issue_14576.lean":
            transformed = checker.transformed_unguarded_source(spec, data)
            require(
                hashlib.sha256(transformed).hexdigest()
                == checker.UNGUARDED_SOURCE_SHA256,
                "unguarded transformed-source baseline drifted",
            )
        if spec.name == "issue_14576_min.lean":
            benign = checker.transformed_benign_source(spec, data)
            require(
                hashlib.sha256(benign).hexdigest() == checker.BENIGN_SOURCE_SHA256,
                "benign transformed-source baseline drifted",
            )
        mutated = data.replace(b"invalid projection", b"invalid Projection", 1)
        results.append(
            expect_typed_failure(
                f"{spec.name}_byte_drift",
                lambda spec=spec, mutated=mutated: checker.validate_fixture_payload(
                    spec, mutated
                ),
                "SHA-256 drifted",
            )
        )
        missing_eof = data[:-1]
        missing_eof_spec = replace(
            spec,
            size=len(missing_eof),
            sha256=hashlib.sha256(missing_eof).hexdigest(),
        )
        results.append(
            expect_typed_failure(
                f"{spec.name}_missing_source_eof_newline",
                lambda spec=missing_eof_spec, mutated=missing_eof: (
                    checker.validate_fixture_payload(spec, mutated)
                ),
                "lacks one final newline",
            )
        )
        duplicated_guard = data + spec.guarded_diagnostic
        duplicated_guard_spec = replace(
            spec,
            size=len(duplicated_guard),
            sha256=hashlib.sha256(duplicated_guard).hexdigest(),
        )
        results.append(
            expect_typed_failure(
                f"{spec.name}_duplicate_invalid_projection_guard",
                lambda spec=duplicated_guard_spec, mutated=duplicated_guard: (
                    checker.validate_fixture_payload(spec, mutated)
                ),
                "invalid-projection guard is absent or ambiguous",
            )
        )
        if spec.post_failure_bad_reference_guard is not None:
            removed_second = data.replace(spec.post_failure_bad_reference_guard, b"", 1)
            removed_second_spec = replace(
                spec,
                size=len(removed_second),
                sha256=hashlib.sha256(removed_second).hexdigest(),
            )
            results.append(
                expect_typed_failure(
                    f"{spec.name}_missing_post_failure_unknown_reference_guard",
                    lambda spec=removed_second_spec, mutated=removed_second: (
                        checker.validate_fixture_payload(spec, mutated)
                    ),
                    "post-failure unknown-identifier reference guard",
                )
            )
        semantic_spec = replace(spec, sha256=hashlib.sha256(mutated).hexdigest())
        results.append(
            expect_typed_failure(
                f"{spec.name}_diagnostic_drift",
                lambda spec=semantic_spec, mutated=mutated: (
                    checker.validate_fixture_payload(spec, mutated)
                ),
                "invalid-projection guard",
            )
        )
    origin = (checker.FIXTURE_ROOT / "origin.json").read_bytes()
    checker.validate_origin_payload(origin)
    results.append(
        expect_typed_failure(
            "origin_commit_drift",
            lambda: checker.validate_origin_payload(
                origin.replace(b"f3b06c", b"03b06c", 1)
            ),
            "SHA-256 drifted",
        )
    )
    parsed_origin = json.loads(origin.decode("utf-8"))
    for name, payload, expected in (
        (
            "origin_json_duplicate_root_key",
            b'{"value":1,"value":2}\n',
            "duplicate JSON object key",
        ),
        (
            "origin_json_duplicate_nested_key",
            b'{"outer":{"value":1,"value":2}}\n',
            "duplicate JSON object key",
        ),
        (
            "origin_json_nonfinite_nan",
            b'{"value":NaN}\n',
            "non-finite JSON constant is forbidden",
        ),
        (
            "origin_json_nonfinite_positive_infinity",
            b'{"value":Infinity}\n',
            "non-finite JSON constant is forbidden",
        ),
        (
            "origin_json_nonfinite_negative_infinity",
            b'{"value":-Infinity}\n',
            "non-finite JSON constant is forbidden",
        ),
        (
            "origin_json_float_token",
            b'{"value":1.0}\n',
            "JSON floating-point number is forbidden",
        ),
        (
            "origin_json_float_positive_overflow",
            b'{"value":1e9999}\n',
            "JSON floating-point number is forbidden",
        ),
        (
            "origin_json_float_negative_overflow",
            b'{"value":-1e9999}\n',
            "JSON floating-point number is forbidden",
        ),
    ):
        results.append(
            expect_typed_failure(
                name,
                lambda payload=payload: checker.parse_json_object(
                    payload, "origin synthetic strict JSON"
                ),
                expected,
            )
        )

    def mutated_origin(*path: str | int, value: object) -> dict[str, object]:
        candidate = json.loads(json.dumps(parsed_origin))
        cursor: object = candidate
        for component in path[:-1]:
            if isinstance(component, str):
                require(
                    isinstance(cursor, dict),
                    f"origin mutation path is not an object: {path}",
                )
                cursor = cursor[component]
            else:
                require(
                    isinstance(cursor, list),
                    f"origin mutation path is not an array: {path}",
                )
                cursor = cursor[component]
        final = path[-1]
        if isinstance(final, str):
            require(
                isinstance(cursor, dict),
                f"origin mutation target is not an object: {path}",
            )
            cursor[final] = value
        else:
            require(
                isinstance(cursor, list),
                f"origin mutation target is not an array: {path}",
            )
            cursor[final] = value
        return candidate

    semantic_origin_cases = (
        (
            "origin_schema_semantic_drift",
            ("schema",),
            "pid-rs/lean-upstream-regression-origin/v3",
        ),
        (
            "origin_fixture_retrieval_date_drift",
            ("fixtures_retrieved_utc_date",),
            "2026-08-03",
        ),
        ("origin_missing_postmortem", ("official_postmortem",), None),
        ("origin_extra_postmortem_field", ("official_postmortem", "unexpected"), True),
        (
            "origin_postmortem_url_drift",
            ("official_postmortem", "url"),
            "https://example.invalid/",
        ),
        (
            "origin_postmortem_bug_area_drift",
            ("official_postmortem", "bug_area"),
            "frontend_only",
        ),
        (
            "origin_postmortem_external_checker_drift",
            ("official_postmortem", "external_checker_named_by_postmortem"),
            "leanchecker",
        ),
        (
            "origin_postmortem_fix_pr_drift",
            ("official_postmortem", "fix_pull_request"),
            14576,
        ),
        (
            "origin_postmortem_frontend_trust_drift",
            ("official_postmortem", "frontend_is_untrusted_by_design"),
            False,
        ),
        (
            "origin_postmortem_frontend_catch_drift",
            (
                "official_postmortem",
                "frontend_checks_arguments_and_catches_ill_typed_term",
            ),
            False,
        ),
        (
            "origin_postmortem_frontend_sufficiency_drift",
            (
                "official_postmortem",
                "frontend_rejection_is_sufficient_kernel_assurance",
            ),
            True,
        ),
        (
            "origin_postmortem_independent_kernel_drift",
            ("official_postmortem", "independent_kernel_is_distinct_assurance_layer"),
            False,
        ),
        (
            "origin_postmortem_patch_status_drift",
            (
                "official_postmortem",
                "patch_releases_reported_without_version_identification",
            ),
            False,
        ),
        (
            "origin_postmortem_review_date_drift",
            ("official_postmortem", "postmortem_checked_utc_date"),
            "2026-08-02",
        ),
        (
            "origin_postmortem_publication_date_drift",
            ("official_postmortem", "publication_date"),
            "2026-08-02",
        ),
        (
            "origin_postmortem_boolean_integer_collapse",
            ("official_postmortem", "independent_kernel_is_distinct_assurance_layer"),
            1,
        ),
        (
            "origin_local_mapping_leanchecker_drift",
            (
                "local_mapping_boundary",
                "leanchecker_fresh_is_postmortem_named_external_checker",
            ),
            True,
        ),
        (
            "origin_project_defined_record_provenance_drift",
            ("record_provenance",),
            "upstream_file",
        ),
        (
            "origin_source_observation_authentication_drift",
            ("implementation_source_observations", "authentication"),
            "authenticated",
        ),
        (
            "origin_source_observation_retention_drift",
            ("implementation_source_observations", "bytes_retained_in_this_packet"),
            True,
        ),
        (
            "origin_source_observation_commit_drift",
            ("implementation_source_observations", "source_commit"),
            "0" * 40,
        ),
        (
            "origin_source_to_binary_claim_drift",
            ("implementation_source_observations", "source_to_binary_provenance"),
            True,
        ),
        (
            "origin_shell_source_sha_drift",
            ("implementation_source_observations", "files", 0, "sha256"),
            "0" * 64,
        ),
        (
            "origin_leanchecker_source_blob_drift",
            ("implementation_source_observations", "files", 1, "git_blob_sha1"),
            "0" * 40,
        ),
        (
            "origin_environment_source_bytes_drift",
            ("implementation_source_observations", "files", 2, "bytes"),
            133_866,
        ),
        (
            "origin_leanchecker_support_scope_drift",
            (
                "implementation_source_observations",
                "files",
                1,
                "supports_selected_claims",
            ),
            ["fresh_replayFromFresh_uses_mkEmptyEnvironment"],
        ),
    )
    results.extend(
        expect_typed_failure(
            name,
            lambda path=path, value=value: checker.validate_origin_semantics(
                mutated_origin(*path, value=value)
            ),
            "origin.json",
        )
        for name, path, value in semantic_origin_cases
    )
    reordered_origin = (
        json.dumps(
            parsed_origin,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    require(reordered_origin != origin, "origin ordering mutation was not distinct")
    results.append(
        expect_typed_failure(
            "origin_json_order_drift",
            lambda: checker.validate_origin_payload(reordered_origin),
            "SHA-256 drifted",
        )
    )
    results.append(
        expect_typed_failure(
            "origin_missing_eof_newline",
            lambda: checker.validate_origin_payload(origin[:-1]),
            "SHA-256 drifted",
        )
    )
    return results


def exact_source_loader_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]
]:
    positives: list[dict[str, object]] = []
    negatives: list[dict[str, object]] = []
    retained_negatives: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-loader-") as temporary:
        root = Path(temporary).resolve(strict=True)
        reviewed = root / "reviewed.py"
        stale_cache_source = root / "stale-cache-source.py"
        reviewed_bytes = b'VALUE = "reviewed-source"\n'
        stale_cache_bytes = b'VALUE = "stale-cache"\n'
        reviewed.write_bytes(reviewed_bytes)
        stale_cache_source.write_bytes(stale_cache_bytes)
        reviewed.chmod(0o644)
        stale_cache_source.chmod(0o644)
        cache = Path(importlib.util.cache_from_source(os.fspath(reviewed)))
        cache.parent.mkdir(parents=True, exist_ok=True)
        py_compile.compile(
            os.fspath(stale_cache_source),
            cfile=os.fspath(cache),
            dfile=os.fspath(reviewed),
            doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH,
        )
        unchecked_name = "_pid_rs_lean_14576_unchecked_hash_cache"
        unchecked_spec = importlib.util.spec_from_file_location(
            unchecked_name, reviewed
        )
        require(
            unchecked_spec is not None and unchecked_spec.loader is not None,
            "could not construct unchecked-hash cache control",
        )
        unchecked = importlib.util.module_from_spec(unchecked_spec)
        sys.modules[unchecked_name] = unchecked
        try:
            unchecked_spec.loader.exec_module(unchecked)
            unchecked_value = getattr(unchecked, "VALUE", None)
        finally:
            sys.modules.pop(unchecked_name, None)
        require(
            unchecked_value == "stale-cache",
            "unchecked-hash bytecode cache did not demonstrate substitution",
        )
        reviewed_sha256 = hashlib.sha256(reviewed_bytes).hexdigest()
        base_name = f"_pid_rs_exact_cache_control_{reviewed_sha256}"
        contaminant = types.ModuleType(base_name)
        contaminant.VALUE = "import-cache-contaminant"
        sys.modules[base_name] = contaminant
        exact: types.ModuleType | None = None
        try:
            exact, exact_bytes = load_exact_module(
                reviewed,
                expected_sha256=reviewed_sha256,
                role="cache control",
            )
            require(
                exact.__name__ != base_name
                and exact.VALUE == "reviewed-source"
                and exact_bytes == reviewed_bytes,
                "exact-source loader consumed import or bytecode cache contamination",
            )
        finally:
            sys.modules.pop(base_name, None)
            if exact is not None:
                sys.modules.pop(exact.__name__, None)
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "unchecked_hash_pyc_substitution_no_credit",
                "observed": "stale-cache",
            }
        )
        positives.append(
            {
                "accepted": True,
                "name": "exact_source_bypasses_pyc_and_sys_modules_contamination",
                "observed": "reviewed-source",
            }
        )
        mutated = root / "mutated.py"
        mutated.write_bytes(reviewed_bytes + b"# drift\n")
        negatives.append(
            expect_typed_failure(
                "exact_source_precompile_digest_mutation",
                lambda: load_exact_module(
                    mutated,
                    expected_sha256=reviewed_sha256,
                    role="mutated exact source",
                ),
                "exact source digest differs",
                exception_type=SelfTestError,
            )
        )
        wrong_mode = root / "wrong-mode.py"
        wrong_mode.write_bytes(reviewed_bytes)
        wrong_mode.chmod(0o600)
        negatives.append(
            expect_typed_failure(
                "exact_source_initial_mode_mutation",
                lambda: load_exact_module(
                    wrong_mode,
                    expected_sha256=reviewed_sha256,
                    role="wrong-mode exact source",
                ),
                "mode must be 0644",
                exception_type=SelfTestError,
            )
        )
    return positives, negatives, retained_negatives


def race_and_cache_controls() -> tuple[
    list[dict[str, object]], list[dict[str, object]]
]:
    negatives: list[dict[str, object]] = []
    retained_negatives: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-race-") as temporary:
        root = Path(temporary).resolve(strict=True)
        executable = root / "tool"
        executable_bytes = b"#!/bin/sh\nexit 0\n"
        executable.write_bytes(executable_bytes)
        executable.chmod(0o700)
        source = root / "query.lean"
        source_bytes = b"#check Nat\n"
        source.write_bytes(source_bytes)
        source.chmod(0o644)
        executable_snapshot = checker.snapshot_executable_route(executable)
        source_snapshot = checker.snapshot(source, lexical_root=root)
        command = (os.fspath(executable), "probe")
        original_run_process = checker.run_process

        def mutate_source(*_arguments: object, **_keywords: object) -> object:
            source.write_bytes(b"#check False\n")
            source.chmod(0o644)
            return checker.ProcessResult(0, b"", b"")

        checker.run_process = mutate_source
        try:
            negatives.append(
                expect_typed_failure(
                    "immediate_post_source_mutation",
                    lambda: checker.run_bound_process(
                        command,
                        cwd=root,
                        executable=executable_snapshot,
                        sources=(source_snapshot,),
                    ),
                    "changed across Lean execution",
                )
            )
        finally:
            checker.run_process = original_run_process

        source.write_bytes(source_bytes)
        source.chmod(0o644)
        source_snapshot = checker.snapshot(source, lexical_root=root)

        def mutate_tool(*_arguments: object, **_keywords: object) -> object:
            executable.write_bytes(b"#!/bin/sh\nexit 9\n")
            executable.chmod(0o700)
            return checker.ProcessResult(0, b"", b"")

        checker.run_process = mutate_tool
        try:
            negatives.append(
                expect_typed_failure(
                    "immediate_post_selected_leaf_substitution",
                    lambda: checker.run_bound_process(
                        command,
                        cwd=root,
                        executable=executable_snapshot,
                        sources=(source_snapshot,),
                    ),
                    "changed across Lean execution",
                )
            )
        finally:
            checker.run_process = original_run_process

        executable.write_bytes(executable_bytes)
        executable.chmod(0o700)
        executable_snapshot = checker.snapshot_executable_route(executable)

        live = root / "source-live"
        alternate = root / "source-alternate"
        held = root / "source-held"
        live.mkdir()
        alternate.mkdir()
        live_source = live / "query.lean"
        alternate_source = alternate / "query.lean"
        live_source.write_bytes(source_bytes)
        live_source.chmod(0o644)
        alternate_bytes = b"#check False\n"
        alternate_source.write_bytes(alternate_bytes)
        alternate_source.chmod(0o644)
        live_snapshot = checker.snapshot(live_source, lexical_root=root)
        consumed_source: list[bytes] = []

        def source_swap_use_restore(*_arguments: object, **_keywords: object) -> object:
            live.rename(held)
            alternate.rename(live)
            try:
                consumed_source.append((live / "query.lean").read_bytes())
            finally:
                live.rename(alternate)
                held.rename(live)
            return checker.ProcessResult(0, b"", b"")

        checker.run_process = source_swap_use_restore
        try:
            survived = checker.run_bound_process(
                command,
                cwd=root,
                executable=executable_snapshot,
                sources=(live_snapshot,),
            )
        finally:
            checker.run_process = original_run_process
        require(
            survived.returncode == 0 and consumed_source == [alternate_bytes],
            "source swap/use/restore retained negative did not consume alternate bytes",
        )
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "same_uid_source_parent_swap_use_restore_survives_endpoints",
                "observed_sha256": hashlib.sha256(alternate_bytes).hexdigest(),
            }
        )

        tool_live = root / "tool-live"
        tool_alternate = root / "tool-alternate"
        tool_held = root / "tool-held"
        (tool_live / "bin").mkdir(parents=True)
        (tool_alternate / "bin").mkdir(parents=True)
        live_tool = tool_live / "bin" / "lean"
        alternate_tool = tool_alternate / "bin" / "lean"
        live_tool.write_bytes(executable_bytes)
        live_tool.chmod(0o700)
        alternate_tool_bytes = b"#!/bin/sh\nexit 23\n"
        alternate_tool.write_bytes(alternate_tool_bytes)
        alternate_tool.chmod(0o700)
        live_tool_snapshot = checker.snapshot_executable_route(live_tool)
        consumed_tool: list[bytes] = []

        def tool_swap_use_restore(*_arguments: object, **_keywords: object) -> object:
            tool_live.rename(tool_held)
            tool_alternate.rename(tool_live)
            try:
                consumed_tool.append((tool_live / "bin" / "lean").read_bytes())
            finally:
                tool_live.rename(tool_alternate)
                tool_held.rename(tool_live)
            return checker.ProcessResult(0, b"", b"")

        checker.run_process = tool_swap_use_restore
        try:
            survived = checker.run_bound_process(
                (os.fspath(live_tool), "probe"),
                cwd=root,
                executable=live_tool_snapshot,
            )
        finally:
            checker.run_process = original_run_process
        require(
            survived.returncode == 0 and consumed_tool == [alternate_tool_bytes],
            "tool swap/use/restore retained negative did not consume alternate bytes",
        )
        retained_negatives.append(
            {
                "demonstrated": True,
                "name": "same_uid_tool_parent_swap_use_restore_survives_endpoints",
                "observed_sha256": hashlib.sha256(alternate_tool_bytes).hexdigest(),
            }
        )

        stale_olean = root / "Issue14576Full.olean"
        stale_olean.write_bytes(b"stale-cache")
        negatives.append(
            expect_typed_failure(
                "preexisting_olean_cache_output",
                lambda: checker.require_absent_output(stale_olean),
                "already exists",
            )
        )
    return negatives, retained_negatives


def custody_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-selftest-") as temporary:
        root = Path(temporary).resolve(strict=True)
        source_copy = root / "checker.py"
        source_copy.write_bytes(CHECKER_SOURCE + b"\n")
        results.append(
            expect_typed_failure(
                "exact_checker_source_drift",
                lambda: read_exact_source(
                    source_copy,
                    expected_sha256=EXPECTED_CHECKER_SOURCE_SHA256,
                    role="mutated checker",
                ),
                "exact source digest differs",
                exception_type=SelfTestError,
            )
        )

        replay = root / "stable-input"
        replay.write_bytes(b"stable\n")
        replay.chmod(0o644)
        observed = checker.snapshot(replay, lexical_root=root)
        replay.write_bytes(b"mutated\n")
        results.append(
            expect_typed_failure(
                "pre_post_input_mutation",
                lambda: checker.require_unchanged(observed),
                "changed across Lean execution",
            )
        )

        mode_mutation = root / "mode-mutation"
        mode_mutation.write_bytes(b"stable\n")
        mode_mutation.chmod(0o644)
        observed = checker.snapshot(mode_mutation, lexical_root=root)
        mode_mutation.chmod(0o600)
        results.append(
            expect_typed_failure(
                "pre_post_mode_mutation",
                lambda: checker.require_unchanged(observed),
                "required input permissions drifted",
            )
        )

        wrong_initial_mode = root / "wrong-initial-mode"
        wrong_initial_mode.write_bytes(b"stable\n")
        wrong_initial_mode.chmod(0o600)
        results.append(
            expect_typed_failure(
                "wrong_initial_input_mode",
                lambda: checker.snapshot(wrong_initial_mode, lexical_root=root),
                "required input permissions drifted",
            )
        )

        symlink_target = root / "symlink-target"
        symlink_target.write_bytes(b"stable\n")
        symlink_target.chmod(0o644)
        symlink_input = root / "symlink-input"
        symlink_input.symlink_to(symlink_target)
        results.append(
            expect_typed_failure(
                "symbolic_link_input",
                lambda: checker.snapshot(symlink_input, lexical_root=root),
                "required input is not regular",
            )
        )

    return results


def private_directory_controls() -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-lean-14576-private-directory-controls-"
    ) as temporary:
        root = Path(temporary)
        root.chmod(0o700)
        valid = root / "valid"
        valid.mkdir(mode=0o700)
        valid_identity = checker.private_directory_identity(valid)
        checker.require_private_directory_unchanged(valid, valid_identity)

        wrong_mode = root / "wrong-mode"
        wrong_mode.mkdir(mode=0o700)
        wrong_mode.chmod(0o755)
        results.append(
            expect_typed_failure(
                "private_directory_wrong_mode",
                lambda: checker.private_directory_identity(wrong_mode),
                "permissions drifted",
            )
        )

        regular_file = root / "regular-file"
        regular_file.write_bytes(b"not a directory\n")
        regular_file.chmod(0o700)
        results.append(
            expect_typed_failure(
                "private_directory_regular_file",
                lambda: checker.private_directory_identity(regular_file),
                "not a direct directory",
            )
        )

        symbolic_link = root / "symbolic-link"
        symbolic_link.symlink_to(valid, target_is_directory=True)
        results.append(
            expect_typed_failure(
                "private_directory_symbolic_link",
                lambda: checker.private_directory_identity(symbolic_link),
                "not a direct directory",
            )
        )

        live = root / "replacement-live"
        held = root / "replacement-held"
        live.mkdir(mode=0o700)
        live_identity = checker.private_directory_identity(live)
        live.rename(held)
        live.mkdir(mode=0o700)
        results.append(
            expect_typed_failure(
                "private_directory_identity_substitution",
                lambda: checker.require_private_directory_unchanged(
                    live, live_identity
                ),
                "identity changed",
            )
        )
    return results


def terminology_residue_controls() -> list[dict[str, object]]:
    checker.validate_neutral_fresh_environment_namespace(CHECKER_SOURCE)
    residue = b"same_" + b"kernel_fresh_environment"
    return [
        expect_typed_failure(
            "ambiguous_same_kernel_fresh_namespace_residue",
            lambda: checker.validate_neutral_fresh_environment_namespace(
                CHECKER_SOURCE + b"\n" + residue
            ),
            "ambiguous legacy fresh-environment namespace resurfaced",
        )
    ]


def literal_dict_key_controls() -> list[dict[str, object]]:
    def duplicate_keys(source: bytes) -> list[str]:
        tree = ast.parse(source, filename="<literal-dict-key-audit>")
        duplicates: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            seen: set[str] = set()
            for key in node.keys:
                if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                    continue
                if key.value in seen:
                    duplicates.append(key.value)
                seen.add(key.value)
        return duplicates

    require(
        duplicate_keys(CHECKER_SOURCE) == [],
        "checker contains a duplicate literal dictionary key",
    )
    return [
        expect_typed_failure(
            "duplicate_literal_dictionary_key",
            lambda: require(
                duplicate_keys(b"packet = {'route': 1, 'route': 2}\n") == [],
                "checker contains a duplicate literal dictionary key",
            ),
            "duplicate literal dictionary key",
            exception_type=SelfTestError,
        )
    ]


def main() -> int:
    try:
        require(
            not hasattr(checker, "PROJECT")
            and not hasattr(checker, "EXPECTED_MATHLIB_REVISION")
            and not hasattr(checker, "EXPECTED_MANIFEST_SHA256")
            and not hasattr(checker, "validate_project_inputs"),
            "standalone kernel regression checker still binds active scientific project inputs",
        )
        initial_self_bytes = SELF_PATH.read_bytes()
        self_source_sha256 = hashlib.sha256(initial_self_bytes).hexdigest()
        require(
            read_exact_source(
                SELF_PATH,
                expected_sha256=self_source_sha256,
                role="Lean #14576 self-test",
            )
            == initial_self_bytes,
            "self-test exact-source endpoint drifted",
        )
        loader_positives, loader_negatives, loader_retained = (
            exact_source_loader_controls()
        )
        race_negatives, race_retained = race_and_cache_controls()
        process_negatives, process_positives = process_boundary_controls()
        controls = [
            *version_controls(),
            *lake_version_controls(),
            *direct_toolchain_controls(),
            *process_result_controls(),
            *target_olean_inventory_probe_result_controls(),
            *target_olean_inventory_probe_source_controls(),
            *leanchecker_fresh_environment_replay_result_controls(),
            *nested_timing_contract_controls(),
            *unguarded_result_controls(),
            *benign_result_controls(),
            *command_controls(),
            *executable_and_diagnostic_path_controls(),
            *environment_route_controls(),
            *interpreter_flag_controls(),
            *bootstrap_runtime_contract_controls(),
            *process_negatives,
            *private_directory_controls(),
            *terminology_residue_controls(),
            *literal_dict_key_controls(),
            *fixture_controls(),
            *loader_negatives,
            *race_negatives,
            *custody_controls(),
        ]
        positive_controls = [*loader_positives, *process_positives]
        retained_negatives = [*loader_retained, *race_retained]
        names = [str(control["name"]) for control in controls]
        require(
            len(names) == EXPECTED_NEGATIVE_CONTROL_COUNT,
            f"negative-control count drifted: {len(names)}",
        )
        require(len(set(names)) == len(names), "negative-control names are not unique")
        require(
            len({str(item["name"]) for item in positive_controls})
            == len(positive_controls),
            "positive-control names are not unique",
        )
        require(
            set(names).isdisjoint({str(item["name"]) for item in positive_controls}),
            "positive- and negative-control names are not disjoint",
        )
        require(
            len({str(item["name"]) for item in retained_negatives})
            == len(retained_negatives),
            "retained-negative names are not unique",
        )
        require(
            read_exact_source(
                CHECKER_PATH,
                expected_sha256=EXPECTED_CHECKER_SOURCE_SHA256,
                role="post-control Lean #14576 checker",
            )
            == CHECKER_SOURCE,
            "checker exact source changed across self-test execution",
        )
        require(
            read_exact_source(
                SELF_PATH,
                expected_sha256=self_source_sha256,
                role="post-control Lean #14576 self-test",
            )
            == initial_self_bytes,
            "self-test source changed across self-test execution",
        )
        evidence = {
            "schema": "pid-rs/lean-kernel-14576-self-test/v6",
            "status": "passed",
            "checker_source_sha256": EXPECTED_CHECKER_SOURCE_SHA256,
            "self_test_source_sha256": self_source_sha256,
            "live_baseline": {
                "status": "not_run_by_self_test",
                "required_separate_route": (
                    "same-transaction archive custody plus kernel regression"
                ),
            },
            "positive_controls_accepted": len(positive_controls),
            "positive_controls": positive_controls,
            "negative_controls_rejected": len(controls),
            "negative_control_inventory_interpretation": (
                f"{EXPECTED_NEGATIVE_CONTROL_COUNT} controls are executed per Python mode; "
                "normal and optimized invocations therefore execute "
                f"{2 * EXPECTED_NEGATIVE_CONTROL_COUNT} named rejected instances in aggregate"
            ),
            "negative_controls": controls,
            "retained_negatives_no_credit": retained_negatives,
            "retained_negatives_no_credit_count": len(retained_negatives),
            "boundary": (
                "The controls require Python >=3.11 isolated/no-site/no-bytecode runtime state; "
                "actual missing -I, -S, and -B invocations fail at the exact entry guard. They "
                "exercise exact-source "
                "loading that bypasses unchecked-hash pyc and sys.modules contamination, fixed "
                "Lean and Lake version/commit/build parsing, guarded zero-exit EOF completion, "
                "the minimum fixture's valid W-projection near-neighbor, trust-zero compilation, "
                "exact --fresh "
                "leanchecker command order, reviewed-pin direct Lean/Lake/leanchecker leaves, "
                "typed result semantics that --trust=0 trusts no macros and typechecks every "
                "imported module while retaining the selected Lean implementation/runtime, and "
                "that --fresh replays imported and defined constants from three ordinary olean "
                "files into mkEmptyEnvironment in a distinct process through a distinct "
                "leanchecker executable leaf, without source re-elaboration or #guard_msgs "
                "rerun and without independent-kernel credit. Exact import/lookup probes establish "
                "only selected emitted-olean name facts: both targets contain the residual "
                "axiom-shaped rendering `axiom E : sorry` left by the failed inductive route. "
                "This proves neither the intended E type nor acceptance as the intended inductive. "
                "`E.mk` is attempted, rejected, and absent from both. In the full fixture the synchronous "
                "inductive addDecl failure makes the downstream `bad` thmDecl unreachable and not "
                "attempted; a full-only lookup confirms that name is absent, while the later "
                "separate `boom` command is guarded for its unknown-identifier rejection. The "
                "minimum fixture contains no `bad` source, reference, probe, or absence claim. "
                "Same-route present/absent sentinels bracket the lookup "
                "mechanism without independent-evidence credit; fresh replay cannot replay source "
                "elaboration, the rejected E.mk attempt, unreachable `bad` code, or the later guard. "
                "The controls exercise private import routing, exact upstream fixture bytes and the project-defined "
                "typed origin/mapping record, stale "
                "olean rejection, source/tool endpoint mutation, environment contamination, "
                "bounded output, standalone isolated-session descendant cleanup, and shared-group "
                "cleanup for members that remain in the initially inherited group; a descendant's "
                "process-group or session changes are not continuously observed. They also exercise a "
                "standalone release-regression "
                "policy that consumes none of the active scientific Lean project inputs, and "
                "the current reviewed-pin/hosted-pending lifecycle boundary. The retained pyc demonstration "
                "earns no gate credit, and concrete same-UID source and tool parent "
                "swap/use/restore demonstrations prove that endpoint snapshots are not atomic. "
                "The tests do not cap peak subprocess memory, authenticate observed tool bytes, "
                "add an independent kernel, prove absence of other Lean defects, validate theorem "
                "meanings, or establish a PID estimator or scientific claim."
            ),
        }
        print(
            json.dumps(
                evidence,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
        return 0
    except (
        SelfTestError,
        checker.LeanKernel14576Error,
        OSError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(f"Lean kernel #14576 self-test failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
