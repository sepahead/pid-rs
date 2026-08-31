#!/usr/bin/env python3
"""Mutation-test the frozen Lean 4.33.0 replay custody gate."""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.version_info >= (3, 11)
    and _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
    and _bootstrap_sys.dont_write_bytecode
):
    print(
        "ERROR: check-lean-toolchain-freeze-self-test.py requires Python 3.11+ -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import time
from types import ModuleType


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
CHECKER = ROOT / "scripts/check-lean-toolchain-freeze.py"
CURRENT_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-19-r14.json"
)
PRIOR_AUG12_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json"
)
PRIOR_AUG12_R2_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-12-r2.json"
)
PRIOR_AUG12_R3_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-12-r3.json"
)
PRIOR_AUG12_R4_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-12-r4.json"
)
PRIOR_AUG13_R5_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-13-r5.json"
)
PRIOR_AUG13_R6_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-13-r6.json"
)
PRIOR_AUG13_R7_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-13-r7.json"
)
PRIOR_AUG14_R8_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-14-r8.json"
)
PRIOR_AUG15_R9_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-15-r9.json"
)
PRIOR_AUG18_R10_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r10.json"
)
PRIOR_AUG18_R11_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r11.json"
)
PRIOR_AUG18_R12_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-18-r12.json"
)
PRIOR_AUG19_R13_RECEIPT_RELATIVE = (
    "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
    "2026-08-19-r13.json"
)
CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
MAX_MODULE_SOURCE_BYTES = 8 * 1024 * 1024
_CHECKER_SNAPSHOT_READ_COUNT = 0
_CHECKER_MODULE_INSTANTIATION_COUNT = 0


class SelfTestError(RuntimeError):
    """The baseline failed or a hostile freeze/replay mutation survived."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def metadata_identity(
    value: os.stat_result,
) -> tuple[int, int, int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


@dataclass(frozen=True)
class CheckerSourceSnapshot:
    """One immutable, descriptor-bound read of the checker source."""

    raw: bytes
    identity: tuple[int, int, int, int, int, int, int]
    parent_identities: tuple[tuple[str, tuple[int, int, int]], ...]
    sha256: str


def parent_route_identities(path: Path) -> tuple[tuple[str, tuple[int, int, int]], ...]:
    result: list[tuple[str, tuple[int, int, int]]] = []
    cursor = path.parent
    while cursor != cursor.parent:
        metadata = os.lstat(cursor)
        require(
            stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode),
            f"checker parent route must not contain a symbolic link: {cursor}",
        )
        result.append(
            (os.fspath(cursor), (metadata.st_dev, metadata.st_ino, metadata.st_mode))
        )
        cursor = cursor.parent
    return tuple(result)


def read_checker_source_once() -> CheckerSourceSnapshot:
    global _CHECKER_SNAPSHOT_READ_COUNT

    require(
        _CHECKER_SNAPSHOT_READ_COUNT == 0,
        "Lean toolchain freeze checker source snapshot was requested more than once",
    )
    _CHECKER_SNAPSHOT_READ_COUNT += 1
    parent_identities = parent_route_identities(CHECKER)
    before = os.lstat(CHECKER)
    require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        "Lean toolchain freeze checker is not a single-link regular source file",
    )
    require(
        before.st_size <= MAX_MODULE_SOURCE_BYTES,
        "Lean toolchain freeze checker is too large",
    )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(CHECKER, flags)
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(
                chunk != b"", "Lean toolchain freeze checker shrank during exact read"
            )
            chunks.append(chunk)
            remaining -= len(chunk)
        require(
            os.read(descriptor, 1) == b"",
            "Lean toolchain freeze checker grew during exact read",
        )
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(CHECKER)
    identities = tuple(
        metadata_identity(value) for value in (before, opened, after_descriptor, after)
    )
    require(
        all(value == identities[0] for value in identities[1:]),
        "Lean toolchain freeze checker source changed during exact read",
    )
    raw = b"".join(chunks)
    require(
        len(raw) == before.st_size,
        "Lean toolchain freeze checker byte count disagrees with metadata",
    )
    require(
        parent_route_identities(CHECKER) == parent_identities,
        "Lean toolchain freeze checker parent route changed during exact read",
    )
    return CheckerSourceSnapshot(
        raw=raw,
        identity=identities[0],
        parent_identities=parent_identities,
        sha256=hashlib.sha256(raw).hexdigest(),
    )


def instantiate_checker(snapshot: CheckerSourceSnapshot) -> ModuleType:
    """Create a fresh checker module from the one immutable source snapshot."""

    global _CHECKER_MODULE_INSTANTIATION_COUNT

    _CHECKER_MODULE_INSTANTIATION_COUNT += 1
    name = (
        "pid_rs_lean_toolchain_freeze_checker_snapshot_"
        f"{_CHECKER_MODULE_INSTANTIATION_COUNT}"
    )
    require(
        name not in sys.modules, f"checker module name was already installed: {name}"
    )
    code = compile(
        snapshot.raw,
        os.fspath(CHECKER),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = ModuleType(name)
    module.__file__ = os.fspath(CHECKER)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    except BaseException as error:
        installed = sys.modules.pop(name, None)
        if installed is not module:
            raise SelfTestError(
                f"checker module registration changed during execution: {name}"
            ) from error
        raise
    installed = sys.modules.pop(name, None)
    require(
        installed is module and name not in sys.modules,
        f"checker module registration was not uniquely cleaned up: {name}",
    )
    return module


def check_checker_snapshot_contract(
    snapshot: CheckerSourceSnapshot, *, expected_instantiations: int
) -> None:
    require(
        _CHECKER_SNAPSHOT_READ_COUNT == 1,
        "Lean toolchain freeze checker did not use exactly one source snapshot",
    )
    require(
        _CHECKER_MODULE_INSTANTIATION_COUNT == expected_instantiations,
        "Lean toolchain freeze checker module instantiation inventory drifted",
    )
    require(
        isinstance(snapshot.raw, bytes)
        and len(snapshot.raw) == snapshot.identity[4]
        and hashlib.sha256(snapshot.raw).hexdigest() == snapshot.sha256,
        "Lean toolchain freeze checker immutable source snapshot drifted",
    )
    require(
        metadata_identity(os.lstat(CHECKER)) == snapshot.identity
        and parent_route_identities(CHECKER) == snapshot.parent_identities,
        "Lean toolchain freeze checker pathname changed after source snapshot",
    )


def load_exact_module(path: Path, name: str) -> ModuleType:
    before = os.lstat(path)
    require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        "Lean toolchain freeze checker is not a single-link regular source file",
    )
    require(
        before.st_size <= MAX_MODULE_SOURCE_BYTES,
        "exact Python module source is too large",
    )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        first = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            first.extend(chunk)
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            second.extend(chunk)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)

    identities = tuple(
        metadata_identity(value) for value in (before, opened, after_descriptor, after)
    )
    require(
        all(value == identities[0] for value in identities[1:])
        and bytes(first) == bytes(second)
        and len(first) == before.st_size,
        "Lean toolchain freeze checker source changed during exact read",
    )
    code = compile(
        bytes(first),
        os.fspath(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    module = ModuleType(name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    finally:
        sys.modules.pop(name, None)
    return module


def required_paths(checker: ModuleType) -> set[str]:
    return {
        "audit/formal/lean/toolchain-freeze-policy.json",
        CURRENT_RECEIPT_RELATIVE,
        *checker.EXPECTED_CONFIG_HASHES,
        *checker.EXPECTED_SOURCE_HASHES,
        *checker.EXPECTED_CURRENT_EVIDENCE_HASHES,
        *checker.EXPECTED_CHECKER_HASHES,
        *checker.EXPECTED_DERIVED_EVIDENCE_HASHES,
        *checker.EXPECTED_ACTIVE_CLAIM_HASHES,
        *checker.EXPECTED_ACTIVE_RESUME_HASHES,
        *checker.EXPECTED_OPERATIONAL_WIRING_HASHES,
        *checker.EXPECTED_CUSTODY_GATE_PATHS,
        *checker.PRESERVED_HISTORICAL_HASHES,
        *checker.PRESERVED_PRIOR_REPLAY_HASHES,
    }


def synthesize_pre_receipt_fixture(checker: ModuleType, destination: Path) -> None:
    """Make a non-evidentiary fixture so hostile tests can run before replay."""

    receipt = json.loads((destination / PRIOR_AUG19_R13_RECEIPT_RELATIVE).read_bytes())
    require(isinstance(receipt, dict), "prior replay fixture is not an object")
    environment = receipt.get("execution_environment")
    require(isinstance(environment, dict), "prior replay environment is malformed")
    historical_root = environment.get("repo_root_observed")
    current_root = checker.EXPECTED_LOCAL_REPLAY_ROUTES["repo_root"]
    require(
        isinstance(historical_root, str)
        and os.path.isabs(historical_root)
        and isinstance(current_root, str)
        and os.path.isabs(current_root)
        and historical_root != current_root,
        "pre-receipt route transition is not explicit",
    )
    command_records = receipt.get("command_records")
    require(isinstance(command_records, list), "prior command records are malformed")
    for record in command_records:
        require(isinstance(record, dict), "prior command record is malformed")
        relative = record.get("cwd_repo_relative")
        require(isinstance(relative, str), "prior command cwd is malformed")
        old_cwd = (
            historical_root
            if relative == "."
            else os.path.normpath(os.path.join(historical_root, relative))
        )
        new_cwd = (
            current_root
            if relative == "."
            else os.path.normpath(os.path.join(current_root, relative))
        )
        require(
            record.get("cwd_observed_absolute") == old_cwd,
            "prior command route cannot seed the r14 simulation",
        )
        record["cwd_observed_absolute"] = new_cwd
    dependency_records = receipt.get("dependency_checkout_preflight")
    dependency_specs = checker.expected_dependency_preflight_specs()
    require(
        isinstance(dependency_records, list)
        and len(dependency_records) == len(dependency_specs),
        "prior dependency routes are malformed",
    )
    for record, (name, relative, _arguments) in zip(
        dependency_records, dependency_specs, strict=True
    ):
        require(
            isinstance(record, dict) and record.get("name") == name,
            "prior dependency route name drifted",
        )
        old_cwd = os.path.normpath(os.path.join(historical_root, relative))
        new_cwd = os.path.normpath(os.path.join(current_root, relative))
        require(
            record.get("cwd_observed_absolute") == old_cwd,
            "prior dependency route cannot seed the r14 simulation",
        )
        record["cwd_observed_absolute"] = new_cwd
        if name.endswith(" root check"):
            expected_stdout = (new_cwd + "\n").encode("utf-8")
            record["stdout"] = {
                "bytes": len(expected_stdout),
                "sha256": hashlib.sha256(expected_stdout).hexdigest(),
            }
    environment["repo_root_observed"] = current_root
    receipt["active_claim_authority_sha256"] = checker.PRESERVED_R14_ACTIVE_CLAIM_HASHES
    receipt["active_configuration"] = checker.EXPECTED_CONFIG_HASHES
    receipt["active_resume_sha256"] = checker.EXPECTED_ACTIVE_RESUME_HASHES
    receipt["checker_sha256"] = checker.EXPECTED_CHECKER_HASHES
    receipt["current_evidence_sha256"] = checker.EXPECTED_CURRENT_EVIDENCE_HASHES
    receipt["derived_instance_evidence_sha256"] = (
        checker.EXPECTED_DERIVED_EVIDENCE_HASHES
    )
    receipt["historical_preservation_sha256"] = checker.PRESERVED_HISTORICAL_HASHES
    receipt["operational_wiring_sha256"] = (
        checker.PRESERVED_R14_OPERATIONAL_WIRING_HASHES
    )
    receipt["prior_replay_preservation_sha256"] = checker.PRESERVED_PRIOR_REPLAY_HASHES
    receipt["prior_replay_schema"] = checker.PRESERVED_PRIOR_REPLAY_SCHEMAS
    receipt["source_sha256"] = checker.EXPECTED_SOURCE_HASHES
    self_test_relative, checker_relative = checker.EXPECTED_CUSTODY_GATE_PATHS
    self_test_digest = hashlib.sha256(
        (destination / self_test_relative).read_bytes()
    ).hexdigest()
    replay_checker_source = (destination / checker_relative).read_bytes()
    replay_checker_digest = hashlib.sha256(replay_checker_source).hexdigest()
    receipt["custody_gate_sha256"] = {
        self_test_relative: self_test_digest,
        checker_relative: replay_checker_digest,
    }
    receipt["replay_custody_gate_sha256"] = {
        self_test_relative: self_test_digest,
        checker_relative: replay_checker_digest,
    }
    projection = checker.replay_receipt_projection_sha256(receipt)
    placeholder = b'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    final_literal = (
        'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + projection + '"'
    ).encode("ascii")
    require(
        replay_checker_source.count(placeholder) == 1,
        "pre-receipt checker placeholder inventory drifted",
    )
    final_checker_source = replay_checker_source.replace(placeholder, final_literal, 1)
    (destination / checker_relative).write_bytes(final_checker_source)
    receipt["custody_gate_sha256"][checker_relative] = hashlib.sha256(
        final_checker_source
    ).hexdigest()
    current = destination / CURRENT_RECEIPT_RELATIVE
    current.parent.mkdir(parents=True, exist_ok=True)
    current.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    checker.EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = projection


def copy_fixture(
    checker: ModuleType,
    checker_snapshot: CheckerSourceSnapshot,
    destination: Path,
) -> bool:
    pre_receipt = not (ROOT / CURRENT_RECEIPT_RELATIVE).exists()
    pending = set(checker.EXPECTED_PENDING_OPERATIONAL_PATHS) if pre_receipt else set()
    pending_claims = (
        set(checker.EXPECTED_PENDING_ACTIVE_CLAIM_PATHS) if pre_receipt else set()
    )
    pending_resume = (
        set(checker.EXPECTED_PENDING_ACTIVE_RESUME_PATHS) if pre_receipt else set()
    )
    for relative in sorted(required_paths(checker)):
        if pre_receipt and relative == CURRENT_RECEIPT_RELATIVE:
            continue
        source = ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if relative == CHECKER_RELATIVE:
            target.write_bytes(checker_snapshot.raw)
            continue
        if relative in pending:
            if source.is_file() and not source.is_symlink():
                shutil.copy2(source, target)
            elif not os.path.lexists(source):
                target.write_bytes(
                    f"non-evidentiary pending operational fixture: {relative}\n".encode(
                        "utf-8"
                    )
                )
            else:
                raise SelfTestError(
                    f"pending fixture source has unsupported identity: {relative}"
                )
            checker.EXPECTED_OPERATIONAL_WIRING_HASHES[relative] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
            continue
        require(
            source.is_file() and not source.is_symlink(),
            f"fixture source is not regular: {relative}",
        )
        shutil.copy2(source, target)
        if relative in pending_claims:
            checker.EXPECTED_ACTIVE_CLAIM_HASHES[relative] = hashlib.sha256(
                target.read_bytes()
            ).hexdigest()
        if relative in pending_resume:
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            checker.EXPECTED_ACTIVE_RESUME_HASHES[relative] = digest
            if relative == "audit/evidence/completion-active-resume.md":
                checker.EXPECTED_ACTIVE_RESUME_SHA256 = digest
    if pre_receipt:
        checker.EXPECTED_PENDING_OPERATIONAL_PATHS = ()
        checker.EXPECTED_PENDING_ACTIVE_CLAIM_PATHS = ()
        checker.EXPECTED_PENDING_ACTIVE_RESUME_PATHS = ()
        synthesize_pre_receipt_fixture(checker, destination)
    return pre_receipt


def canonical_json(path: Path, mutate: Callable[[dict], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON mutation root is not an object: {path}")
    mutate(value)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def configure_fixture(checker: ModuleType, root: Path) -> None:
    checker.ROOT = root
    checker.PROJECT = root / "audit/formal/lean"
    checker.POLICY = checker.PROJECT / "toolchain-freeze-policy.json"
    checker.RECEIPT = root / CURRENT_RECEIPT_RELATIVE


def check_structural_placeholder_contract(checker: ModuleType) -> None:
    pending = (
        *checker.EXPECTED_PENDING_OPERATIONAL_PATHS,
        *checker.EXPECTED_PENDING_ACTIVE_CLAIM_PATHS,
        *checker.EXPECTED_PENDING_ACTIVE_RESUME_PATHS,
    )
    if not pending:
        return
    require(
        not (ROOT / CURRENT_RECEIPT_RELATIVE).exists(),
        "r14 receipt exists while structural digest placeholders remain",
    )
    require(
        checker.EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 == "0" * 64,
        "structural digest placeholders survived after replay projection finalization",
    )
    try:
        checker.check_static_without_receipt()
    except checker.FreezeError as error:
        require(
            "digest placeholders remain" in str(error),
            f"structural placeholder contract produced wrong diagnostic: {error}",
        )
    else:
        raise SelfTestError("structural digest placeholders received replay readiness")


def mutate_policy_remove_trigger(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(path, lambda value: value["reevaluation_triggers"].pop())
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def mutate_policy_enable_latest(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["automatic_update_policy"].__setitem__(
            "check_latest_release", True
        ),
    )
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def mutate_policy_remove_nontrigger(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(path, lambda value: value["nontriggers"].pop())
    refresh_policy_binding(checker, root)


def mutate_policy_weaken_baseline_unavailability(
    checker: ModuleType, root: Path
) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"

    def mutate(value: dict) -> None:
        trigger = next(
            item
            for item in value["reevaluation_triggers"]
            if item["id"] == "baseline_unavailability"
        )
        trigger["description"] = "One transient download failed."

    canonical_json(path, mutate)
    refresh_policy_binding(checker, root)


def mutate_policy_disable_rollback(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["candidate_transition_policy"].__setitem__(
            "rollback_plan_required_before_activation", False
        ),
    )
    refresh_policy_binding(checker, root)


def mutate_receipt_archive_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["official_archive"].__setitem__("sha256", "0" * 64),
    )


def mutate_receipt_optimized_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["python_optimization_parity"]["pairs"]["finite_checker"][
            "optimized_stdout"
        ].__setitem__("sha256", "0" * 64),
    )


def mutate_receipt_scope(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["scope_boundary"].__setitem__(
            0, "This replay proves Lean kernel soundness and Rust refinement."
        ),
    )


def mutate_environment_inheritance(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["environment_policy"].__setitem__(
            "ambient_environment_inherited", True
        ),
    )


def mutate_stdin_inheritance(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["environment_policy"].__setitem__("stdin_inherited", True),
    )


def mutate_process_umask(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["environment_policy"].__setitem__("umask_octal", "0000"),
    )


def mutate_signal_state(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["environment_policy"]["signal_dispositions"].__setitem__(
            "SIGTERM", "SIG_IGN"
        ),
    )


def mutate_bounded_child_policy(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["environment_policy"].__setitem__(
            "command_timeout_seconds", 86_400
        ),
    )


def mutate_dependency_preflight_remove(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["dependency_checkout_preflight"].pop(),
    )


def mutate_dependency_preflight_argv(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["dependency_checkout_preflight"][0][
            "argv_executed"
        ].__setitem__(0, "/tmp/ambient-git"),
    )


def mutate_receipt_schema(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )


def mutate_current_receipt_self_digest_inventory(
    checker: ModuleType, root: Path
) -> None:
    checker.EXPECTED_ACTIVE_CLAIM_HASHES[CURRENT_RECEIPT_RELATIVE] = "0" * 64
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value["active_claim_authority_sha256"].__setitem__(
            CURRENT_RECEIPT_RELATIVE, "0" * 64
        ),
    )


def mutate_receipt_duplicate_key(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    text = path.read_text(encoding="utf-8")
    path.write_text('{\n  "status": "passed",' + text[1:], encoding="utf-8")


def mutate_receipt_noncanonical(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")


def mutate_receipt_repin_to_current_wiring(checker: ModuleType, root: Path) -> None:
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value.__setitem__(
            "operational_wiring_sha256",
            dict(checker.EXPECTED_OPERATIONAL_WIRING_HASHES),
        ),
    )


def mutate_preserved_r14_operational_digest(checker: ModuleType, _root: Path) -> None:
    checker.PRESERVED_R14_OPERATIONAL_WIRING_HASHES[".github/workflows/ci.yml"] = (
        "0" * 64
    )


def mutate_collapse_historical_current_wiring_split(
    checker: ModuleType, _root: Path
) -> None:
    checker.PRESERVED_R14_OPERATIONAL_WIRING_HASHES = (
        checker.EXPECTED_OPERATIONAL_WIRING_HASHES
    )


def mutate_receipt_repin_to_current_active_claims(
    checker: ModuleType, root: Path
) -> None:
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value.__setitem__(
            "active_claim_authority_sha256",
            dict(checker.EXPECTED_ACTIVE_CLAIM_HASHES),
        ),
    )


def mutate_preserved_r14_active_claim_digest(checker: ModuleType, _root: Path) -> None:
    checker.PRESERVED_R14_ACTIVE_CLAIM_HASHES[
        "claims/SX-COUNT-EVENT-BRIDGE-001/revision-index.md"
    ] = "0" * 64


def mutate_collapse_historical_current_active_claim_split(
    checker: ModuleType, _root: Path
) -> None:
    checker.PRESERVED_R14_ACTIVE_CLAIM_HASHES = checker.EXPECTED_ACTIVE_CLAIM_HASHES


def mutate_self_test_with_coordinated_receipt_hash(
    _checker: ModuleType, root: Path
) -> None:
    relative = "scripts/check-lean-toolchain-freeze-self-test.py"
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: (
            value["custody_gate_sha256"].__setitem__(relative, digest),
            value["replay_custody_gate_sha256"].__setitem__(relative, digest),
        ),
    )


def mutate_final_custody_missing(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value["custody_gate_sha256"].pop(
            "scripts/check-lean-toolchain-freeze-self-test.py"
        ),
    )


def mutate_replay_custody_extra(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value["replay_custody_gate_sha256"].__setitem__(
            "scripts/unreviewed-custody.py", "0" * 64
        ),
    )


def mutate_custody_in_operational_inventory(checker: ModuleType, root: Path) -> None:
    relative = "scripts/check-lean-toolchain-freeze.py"
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_OPERATIONAL_WIRING_HASHES[relative] = digest
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value["operational_wiring_sha256"].__setitem__(relative, digest),
    )


def mutate_custody_in_checker_inventory(checker: ModuleType, root: Path) -> None:
    relative = "scripts/check-lean-toolchain-freeze-self-test.py"
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_CHECKER_HASHES[relative] = digest
    canonical_json(
        root / CURRENT_RECEIPT_RELATIVE,
        lambda value: value["checker_sha256"].__setitem__(relative, digest),
    )


def mutate_replay_checker_endpoint_hash(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["replay_custody_gate_sha256"].__setitem__(
            "scripts/check-lean-toolchain-freeze.py", "0" * 64
        ),
    )


def mutate_local_archive_observation(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["official_archive_observation"].__setitem__(
            "sha256", "0" * 64
        ),
    )


def refresh_source_binding(checker: ModuleType, root: Path, relative: str) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_SOURCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: value["source_sha256"].__setitem__(relative, digest),
    )


def mutate_broad_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    old = "set_option backward.isDefEq.respectTransparency.types false in"
    require(text.count(old) == 1, "broad-option mutation anchor drifted")
    path.write_text(
        text.replace(old, "set_option backward.isDefEq.respectTransparency false", 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_missing_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    old = "set_option backward.isDefEq.respectTransparency.types false in\n"
    require(text.count(old) == 1, "missing-option mutation anchor drifted")
    path.write_text(text.replace(old, "", 1), encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_extra_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/SxEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    anchor = "set_option warningAsError true\n"
    require(text.count(anchor) == 1, "extra-option mutation anchor drifted")
    path.write_text(
        text.replace(anchor, anchor + checker.OPTION + "\n", 1), encoding="utf-8"
    )
    refresh_source_binding(checker, root, relative)


def mutate_manifest_pin(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/lake-manifest.json"
    path = root / relative
    value = json.loads(path.read_text(encoding="utf-8"))
    package = next(item for item in value["packages"] if item["name"] == "mathlib")
    package["rev"] = "0" * 40
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.EXPECTED_CONFIG_HASHES[relative] = digest


def mutate_historical_bytes(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.32.2-darwin-aarch64-strict-replay-q1-2026-08-08.stdout"
    )
    path.write_bytes(b"historical drift\n")


def mutate_derived_output(_checker: ModuleType, root: Path) -> None:
    path = root / "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-4.33.0.stdout"
    path.write_text(
        path.read_text(encoding="utf-8").replace("instance_reducible", "regular", 1),
        encoding="utf-8",
    )


def mutate_policy_symlink(_checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    target = path.with_name("policy-target.json")
    shutil.copy2(path, target)
    path.unlink()
    path.symlink_to(target.name)


def mutate_receipt_hardlink(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    os.link(path, path.with_name("replay-second-link.json"))


def canonical_compact_json(path: Path, mutate: Callable[[dict], None]) -> None:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"JSON mutation root is not an object: {path}")
    mutate(value)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def refresh_current_evidence_binding(
    checker: ModuleType, root: Path, relative: str
) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_CURRENT_EVIDENCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: value["current_evidence_sha256"].__setitem__(relative, digest),
    )


def refresh_policy_binding(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    checker.EXPECTED_POLICY_SHA256 = hashlib.sha256(path.read_bytes()).hexdigest()


def refresh_manifest_binding(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/lake-manifest.json"
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_CONFIG_HASHES[relative] = digest
    policy = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        policy,
        lambda value: value["active_pin"].__setitem__("lake_manifest_sha256", digest),
    )
    refresh_policy_binding(checker, root)
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: value["active_configuration"].__setitem__(relative, digest),
    )


def mutate_deriving_scope_after_target(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    target = checker.OPTION + "\nderiving instance Fintype for SxPid2Node"
    replacement = "deriving instance Fintype for SxPid2Node\n" + checker.OPTION
    require(text.count(target) == 1, "deriving-scope relocation anchor drifted")
    path.write_text(text.replace(target, replacement, 1), encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_deriving_scope_with_comment_spoof(checker: ModuleType, root: Path) -> None:
    mutate_deriving_scope_after_target(checker, root)
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    text += (
        "\n/- Raw-text-only target spoof:\n"
        + checker.OPTION
        + "\nderiving instance Fintype for SxPid2Node\n-/\n"
    )
    path.write_text(text, encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_proof_scope_to_file_header(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergenceSemanticContract.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    target = checker.EXPECTED_OPTION_TARGETS[relative][0]
    require(text.count(target) == 1, "proof-scope relocation target drifted")
    text = text.replace(
        target, target.replace(" :=\n  " + checker.OPTION + " by", " := by"), 1
    )
    header = "set_option warningAsError true\n"
    require(text.count(header) == 1, "proof-scope relocation header drifted")
    text = text.replace(header, header + checker.OPTION + " by\n", 1)
    path.write_text(text, encoding="utf-8")
    refresh_source_binding(checker, root, relative)


def mutate_option_true(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    require(text.count(checker.OPTION) == 1, "true-option mutation anchor drifted")
    path.write_text(
        text.replace(checker.OPTION, checker.OPTION.replace("false", "true"), 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_file_global_types_option(checker: ModuleType, root: Path) -> None:
    relative = "audit/formal/lean/PidFiniteConvergence/TwoSourceCountEventBridge.lean"
    path = root / relative
    text = path.read_text(encoding="utf-8")
    require(
        text.count(checker.OPTION) == 1, "file-global-option mutation anchor drifted"
    )
    path.write_text(
        text.replace(checker.OPTION, checker.OPTION.removesuffix(" in"), 1),
        encoding="utf-8",
    )
    refresh_source_binding(checker, root, relative)


def mutate_current_evidence_identity(
    checker: ModuleType, root: Path, replacement: str
) -> None:
    relative = "audit/evidence/lean-citation-edge-countermodel-4.33.0.json"
    path = root / relative
    canonical_compact_json(
        path,
        lambda value: value.__setitem__("lean_version", replacement),
    )
    refresh_current_evidence_binding(checker, root, relative)


def mutate_wrong_lean_commit(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + "0" * 40
        + ", Release)",
    )


def mutate_wrong_lean_build(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + checker.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Debug)",
    )


def mutate_wrong_lean_platform(checker: ModuleType, root: Path) -> None:
    mutate_current_evidence_identity(
        checker,
        root,
        "Lean (version 4.33.0, x86_64-unknown-linux-gnu, commit "
        + checker.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Release)",
    )


def mutate_manifest_regeneration_overclaim(checker: ModuleType, root: Path) -> None:
    relative = "audit/evidence/lean-4.33.0-manifest-regeneration-2026-08-11.json"
    path = root / relative
    canonical_compact_json(
        path,
        lambda value: value["procedure"].__setitem__("raw_command_log_retained", True),
    )
    refresh_current_evidence_binding(checker, root, relative)


def mutate_operational_wiring(root: Path, relative: str) -> None:
    path = root / relative
    path.write_bytes(path.read_bytes() + b"\n")


def refresh_operational_wiring_binding(
    checker: ModuleType, root: Path, relative: str
) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_OPERATIONAL_WIRING_HASHES[relative] = digest


def refresh_active_claim_binding(
    checker: ModuleType, root: Path, relative: str
) -> None:
    digest = hashlib.sha256((root / relative).read_bytes()).hexdigest()
    checker.EXPECTED_ACTIVE_CLAIM_HASHES[relative] = digest
    if relative in checker.PRESERVED_R14_ACTIVE_CLAIM_HASHES:
        checker.PRESERVED_R14_ACTIVE_CLAIM_HASHES[relative] = digest
        canonical_json(
            root / CURRENT_RECEIPT_RELATIVE,
            lambda value: value["active_claim_authority_sha256"].__setitem__(
                relative, digest
            ),
        )


def mutate_ci_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, ".github/workflows/ci.yml")


def mutate_agents_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "AGENTS.md")


def mutate_freeze_document_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md")


def mutate_just_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "justfile")


def mutate_scripts_readme_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/README.md")


def mutate_replay_generator_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/generate-lean-4.33-replay.py")


def mutate_changelog_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "CHANGELOG.md")


def mutate_deep_audit_adjudication_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root,
        "audit/evidence/external-model-pid-rs-deep-audit-adjudication-2026-08-12.md",
    )


def mutate_active_plan_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/evidence/wibral-pid-program-active-plan-2026-08-12.md"
    )


def mutate_m1a_boundary_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md"
    )


def mutate_m1a_custody_correction_boundary_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root,
        "audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md",
    )


def mutate_m1a_custody_correction_policy_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root,
        "audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json",
    )


def mutate_m1a_failed_ci_receipt_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json"
    )


def mutate_m1a_policy_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "audit/evidence/ksg-rev4-m1a-path-policy-v1.json")


def mutate_m1a_schema_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json")


def mutate_m1a_checker_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-ksg-m1a-phase.py")


def mutate_m1a_self_test_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-ksg-m1a-phase-self-test.py")


def mutate_m1a_composite_schema_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json"
    )


def mutate_m1a_custody_correction_checker_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(root, "scripts/check-ksg-m1a-custody-correction.py")


def mutate_m1a_custody_correction_self_test_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "scripts/check-ksg-m1a-custody-correction-self-test.py"
    )


def mutate_m1a_hosted_recovery_negative_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root,
        "audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json",
    )


def mutate_m1a_hosted_recovery_policy_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json"
    )


def mutate_m1a_hosted_recovery_boundary_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md"
    )


def mutate_m1a_hosted_recovery_composite_schema_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json"
    )


def mutate_m1a_hosted_recovery_checker_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-ksg-m1a-hosted-recovery.py")


def mutate_m1a_hosted_recovery_self_test_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "scripts/check-ksg-m1a-hosted-recovery-self-test.py"
    )


def mutate_ksg_revision4_terminal_index_checker_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(root, "scripts/check-ksg-revision4-terminal-index.py")


def mutate_ksg_revision4_terminal_index_self_test_wiring(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "scripts/check-ksg-revision4-terminal-index-self-test.py"
    )


def mutate_post_v2_schema_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "audit/schemas/post-commit-source-state-v2.schema.json"
    )


def mutate_certified_checker_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-certified-sxpid2-claim.py")


def mutate_certified_self_test_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-certified-sxpid2-claim-self-test.py")


def mutate_post_v2_checker_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-post-commit-source-state-v2.py")


def mutate_post_v2_self_test_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "scripts/check-post-commit-source-state-v2-self-test.py"
    )


def mutate_zeta_checker_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-zeta-pid-transfer-firewall.py")


def mutate_zeta_self_test_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "scripts/check-zeta-pid-transfer-firewall-self-test.py"
    )


def mutate_workflow_pdf_gate_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-mathematical-workflow-pdf.sh")


def mutate_workflow_pdf_self_test_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(
        root, "scripts/check-mathematical-workflow-pdf-self-test.sh"
    )


def mutate_formal_pdf_set_wiring(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "scripts/check-formal-pdf-set.sh")


def mutate_retired_v1_checker_recreated(_checker: ModuleType, root: Path) -> None:
    (root / "scripts/check-post-commit-source-state-v1.py").write_text(
        "# retired path unexpectedly recreated\n", encoding="utf-8"
    )


def mutate_retired_v1_self_test_recreated(_checker: ModuleType, root: Path) -> None:
    (root / "scripts/check-post-commit-source-state-v1-self-test.py").write_text(
        "# retired path unexpectedly recreated\n", encoding="utf-8"
    )


def mutate_current_ksg_revision_index(_checker: ModuleType, root: Path) -> None:
    mutate_operational_wiring(root, "claims/KSG-INTEGER-HARMONIC-001/revision-index.md")


def mutate_current_sx_count_event_revision_index(
    _checker: ModuleType, root: Path
) -> None:
    mutate_operational_wiring(
        root, "claims/SX-COUNT-EVENT-BRIDGE-001/revision-index.md"
    )


def mutate_coordinated_agents_pointer_rewind(checker: ModuleType, root: Path) -> None:
    relative = "AGENTS.md"
    path = root / relative
    current = "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    prior = "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r13.json"
    text = path.read_text(encoding="utf-8")
    require(text.count(current) == 1, "AGENTS current-replay mutation anchor drifted")
    path.write_text(text.replace(current, prior, 1), encoding="utf-8")
    refresh_operational_wiring_binding(checker, root, relative)


def mutate_coordinated_claim_pointer_rewind(checker: ModuleType, root: Path) -> None:
    relative = "claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md"
    path = root / relative
    current = "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    prior = "lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r13.json"
    text = path.read_text(encoding="utf-8")
    require(text.count(current) == 2, "claim current-replay mutation anchor drifted")
    path.write_text(text.replace(current, prior), encoding="utf-8")
    refresh_active_claim_binding(checker, root, relative)


def mutate_coordinated_agents_r14_sequence_conflation(
    checker: ModuleType, root: Path
) -> None:
    relative = "AGENTS.md"
    path = root / relative
    anchor = "fourteenth accepted slot in"
    text = path.read_text(encoding="utf-8")
    require(text.count(anchor) == 1, "AGENTS r14-sequence mutation anchor drifted")
    path.write_text(
        text.replace(anchor, "review revision fourteen in", 1),
        encoding="utf-8",
    )
    refresh_operational_wiring_binding(checker, root, relative)


def mutate_coordinated_agents_r8_replay_status_conflation(
    checker: ModuleType, root: Path
) -> None:
    relative = "AGENTS.md"
    path = root / relative
    anchor = "finalized `r8`"
    text = path.read_text(encoding="utf-8")
    require(text.count(anchor) == 1, "AGENTS finalized-r8 mutation anchor drifted")
    path.write_text(text.replace(anchor, "retained `r8`", 1), encoding="utf-8")
    refresh_operational_wiring_binding(checker, root, relative)


def mutate_prior_replay_aug11_bytes(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-11.json"
    )
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug12_bytes(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-12.json"
    )
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug12_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = (
        "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-"
        "2026-08-12.json"
    )
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug12_r2_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG12_R2_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug12_r2_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG12_R2_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug12_r3_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG12_R3_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug12_r3_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG12_R3_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug12_r4_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG12_R4_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug12_r4_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG12_R4_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug13_r5_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG13_R5_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug13_r5_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG13_R5_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug13_r6_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG13_R6_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug13_r6_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG13_R6_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug13_r7_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG13_R7_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug13_r7_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG13_R7_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug14_r8_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG14_R8_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug14_r8_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG14_R8_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug15_r9_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG15_R9_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug15_r9_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG15_R9_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug18_r10_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG18_R10_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug18_r10_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG18_R10_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug18_r11_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG18_R11_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug18_r11_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG18_R11_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug18_r12_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG18_R12_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug18_r12_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG18_R12_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_aug19_r13_bytes(_checker: ModuleType, root: Path) -> None:
    path = root / PRIOR_AUG19_R13_RECEIPT_RELATIVE
    path.write_bytes(path.read_bytes() + b"\n")


def mutate_prior_replay_aug19_r13_coordinated_schema(
    checker: ModuleType, root: Path
) -> None:
    relative = PRIOR_AUG19_R13_RECEIPT_RELATIVE
    path = root / relative
    canonical_json(
        path,
        lambda value: value.__setitem__(
            "schema", "pid-rs/lean-current-project-replay/v1"
        ),
    )
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.PRESERVED_PRIOR_REPLAY_HASHES[relative] = digest
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: (
            value["prior_replay_preservation_sha256"].__setitem__(relative, digest),
            value["prior_replay_schema"].__setitem__(
                relative, "pid-rs/lean-current-project-replay/v1"
            ),
        ),
    )


def mutate_prior_replay_operational_overlap(checker: ModuleType, root: Path) -> None:
    relative = PRIOR_AUG14_R8_RECEIPT_RELATIVE
    checker.EXPECTED_OPERATIONAL_WIRING_HASHES[relative] = (
        checker.PRESERVED_PRIOR_REPLAY_HASHES[relative]
    )
    receipt = root / CURRENT_RECEIPT_RELATIVE
    canonical_json(
        receipt,
        lambda value: value["operational_wiring_sha256"].__setitem__(
            relative, checker.PRESERVED_PRIOR_REPLAY_HASHES[relative]
        ),
    )


def mutate_exact_archive_route(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        path,
        lambda value: value["official_archive_observation"].__setitem__(
            "path_observed_absolute",
            "/private/tmp/alternate/lean-4.33.0-darwin_aarch64.tar.zst",
        ),
    )


def mutate_exact_python_route(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )

    def mutate(value: dict) -> None:
        replacement = "/opt/homebrew/bin/python3.14"
        value["execution_environment"]["python_executable"] = replacement
        for record in value["command_records"]:
            if record["argv_logical"][0] == "python3":
                record["argv_executed"][0] = replacement

    canonical_json(path, mutate)


def mutate_exact_lean_route(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )

    def mutate(value: dict) -> None:
        replacement = "/private/tmp/alternate/lean-bin"
        environment = value["execution_environment"]
        environment["lean_bin_directory"] = replacement
        environment["lean_executable"] = replacement + "/lean"
        environment["lake_executable"] = replacement + "/lake"
        value["environment_policy"]["effective_nonsecret_environment"]["PATH"] = (
            replacement + ":/opt/homebrew/bin:/usr/bin:/bin"
        )
        for record in value["command_records"]:
            logical = record["argv_logical"][0]
            if logical in ("lean", "lake"):
                record["argv_executed"][0] = replacement + "/" + logical

    canonical_json(path, mutate)


def mutate_executable_digest(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        path,
        lambda value: value["execution_environment"]["executable_sha256"].__setitem__(
            "lean", "0" * 64
        ),
    )


def mutate_git_route(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["execution_environment"].__setitem__(
            "git_executable", "/opt/homebrew/bin/git"
        ),
    )


def mutate_executable_size(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["execution_environment"][
            "executable_size_bytes"
        ].__setitem__("git", 0),
    )


def mutate_executable_link_count(_checker: ModuleType, root: Path) -> None:
    canonical_json(
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
        lambda value: value["execution_environment"][
            "executable_link_counts"
        ].__setitem__("git", 1),
    )


def check_generator_zero_argument_contract(root: Path) -> None:
    path = root / "scripts/generate-lean-4.33-replay.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=os.fspath(path))
    argv_attributes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "sys"
        and node.attr == "argv"
    ]
    require(
        len(argv_attributes) == 1,
        "replay generator must contain exactly one sys.argv access",
    )
    argument_guard = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Call)
        and isinstance(node.test.left.func, ast.Name)
        and node.test.left.func.id == "len"
        and len(node.test.left.args) == 1
        and not node.test.left.keywords
        and node.test.left.args[0] is argv_attributes[0]
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.NotEq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == 1
    ]
    require(
        len(argument_guard) == 1,
        "replay generator sys.argv access is not the unique exact zero-argument guard",
    )
    main_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    require(
        len(main_functions) == 1
        and len(main_functions[0].body) >= 3
        and main_functions[0].body[0] is argument_guard[0],
        "replay generator zero-argument guard is not the first main statement",
    )
    guard = argument_guard[0]
    require(
        not guard.orelse
        and len(guard.body) == 1
        and isinstance(guard.body[0], ast.Expr)
        and isinstance(guard.body[0].value, ast.Call)
        and isinstance(guard.body[0].value.func, ast.Name)
        and guard.body[0].value.func.id == "die"
        and len(guard.body[0].value.args) == 1
        and isinstance(guard.body[0].value.args[0], ast.Constant)
        and guard.body[0].value.args[0].value
        == "usage: generate-lean-4.33-replay.py (no arguments)"
        and not guard.body[0].value.keywords,
        "replay generator zero-argument guard does not terminate with the exact usage error",
    )
    die_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "die"
    ]
    require(
        len(die_functions) == 1
        and not die_functions[0].decorator_list
        and len(die_functions[0].args.args) == 1
        and die_functions[0].args.args[0].arg == "message"
        and len(die_functions[0].body) == 1
        and isinstance(die_functions[0].body[0], ast.Raise)
        and isinstance(die_functions[0].body[0].exc, ast.Call)
        and isinstance(die_functions[0].body[0].exc.func, ast.Name)
        and die_functions[0].body[0].exc.func.id == "SystemExit"
        and len(die_functions[0].body[0].exc.args) == 1
        and isinstance(die_functions[0].body[0].exc.args[0], ast.Name)
        and die_functions[0].body[0].exc.args[0].id == "message"
        and not die_functions[0].body[0].exc.keywords,
        "replay generator die helper is not an unconditional SystemExit",
    )
    require(
        not any(
            isinstance(node, ast.ImportFrom) and node.module in {"sys", "argparse"}
            for node in ast.walk(tree)
        )
        and not any(
            isinstance(node, (ast.Import, ast.ImportFrom))
            and any(alias.name == "argparse" for alias in node.names)
            for node in ast.walk(tree)
        )
        and not any(
            isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
            and node.id == "argv"
            for node in ast.walk(tree)
        )
        and not any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "input"
            for node in ast.walk(tree)
        ),
        "replay generator contains an alternate argument/input authority",
    )
    second_statement = main_functions[0].body[1]
    require(
        isinstance(second_statement, ast.Expr)
        and isinstance(second_statement.value, ast.Call)
        and isinstance(second_statement.value.func, ast.Attribute)
        and isinstance(second_statement.value.func.value, ast.Name)
        and second_statement.value.func.value.id == "os"
        and second_statement.value.func.attr == "umask"
        and len(second_statement.value.args) == 1
        and isinstance(second_statement.value.args[0], ast.Constant)
        and second_statement.value.args[0].value == 0o077
        and not second_statement.value.keywords,
        "replay generator fixed umask is not the second main statement",
    )
    third_statement = main_functions[0].body[2]
    require(
        isinstance(third_statement, ast.Expr)
        and isinstance(third_statement.value, ast.Call)
        and isinstance(third_statement.value.func, ast.Name)
        and third_statement.value.func.id == "normalize_process_signals"
        and not third_statement.value.args
        and not third_statement.value.keywords,
        "replay generator signal normalization is not the third main statement",
    )
    for literal in (
        'PINNED_ROOT = Path("/private/tmp/pid-rs-c9-oversize-rebuild.9AW1lT/repo")',
        'SCRIPT = PINNED_ROOT / "scripts/generate-lean-4.33-replay.py"',
        '/ "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"',
        'die("runner was not launched from the pinned repository route")',
        "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64/bin",
        "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64.tar.zst",
        "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/bin/python3.14",
        "if len(sys.argv) != 1:",
        "os.umask(0o077)",
        'input_bytes = b""',
        "os.fchmod(descriptor, 0o644)",
        "stat.S_IMODE(opened.st_mode) != 0o600",
        "(linked.st_dev, linked.st_ino) != temporary_device_inode",
        'die("private receipt construction identity drifted")',
        'die("private receipt identity drifted during construction")',
        'die("private receipt did not reach canonical publication identity")',
    ):
        require(
            source.count(literal) == 1, f"generator route contract drifted: {literal}"
        )
    for literal in (
        'die("pinned archive route is not canonical")',
        'die(f"pinned executable digest drifted: {name}")',
        'PINNED_GIT = Path("/usr/bin/git")',
        '"git": "179301dcb41ea78accc3fa0048a7e6f6710d891945a751a34addd622020c1818"',
        '"leanchecker": "257f505f8241ab595c6b557d661fd832dbdace6839ab35d9d1600b3dcbce5880"',
        'tempfile.TemporaryFile(dir=environment["TMPDIR"])',
        "src_dir_fd=parent_descriptor",
        "dst_dir_fd=parent_descriptor",
        "reject_repository_bytecode_cache(root)",
        'die("replay generator/checker receipt routes diverged")',
        "validate_composite_v9_cut_state(freeze, root)",
        '"schema": "pid-rs/lean-current-project-replay/v2"',
    ):
        require(
            source.count(literal) == 1,
            f"generator append-only publication contract drifted: {literal}",
        )
    require(
        "os.replace(temporary, output)" not in source,
        "generator can overwrite a versioned replay receipt",
    )
    require(
        source.index(
            "require_leaf_absent(\n        output_parent_descriptor, temporary_leaf"
        )
        < source.index("freeze = load_module("),
        "generator output no-clobber preflight moved after repository module load",
    )
    require(
        source.index("validate_composite_v9_cut_state(freeze, root)")
        < source.index("freeze.check_static_without_receipt()"),
        "generator checksum-cut preflight moved after replay static validation",
    )


def generator_test_environment(root: Path) -> dict[str, str]:
    home = root / "home"
    tmpdir = root / "tmp"
    home.mkdir(mode=0o700)
    tmpdir.mkdir(mode=0o700)
    return {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": os.fspath(home),
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": os.fspath(tmpdir),
        "TZ": "UTC",
    }


def check_generator_cut_preflight(generator: ModuleType) -> None:
    projection = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    composite = 'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "0" * 64'
    operational = '    "scripts/check-ksg-m1a-composite-v9.py": "0" * 64,'
    normalized_lean = (
        projection + "\n" + composite + "\n" + operational + "\n"
    ).encode("utf-8")
    normalized_digest = hashlib.sha256(normalized_lean).hexdigest()
    composite_raw = (
        'EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "' + normalized_digest + '"\n'
    ).encode("utf-8")

    def reseal_checker(checker_raw: bytes) -> tuple[bytes, dict[str, str]]:
        checker_digest = hashlib.sha256(checker_raw).hexdigest()
        lean_raw = normalized_lean.replace(
            composite.encode("utf-8"),
            (
                'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "'
                + checker_digest
                + '"'
            ).encode("utf-8"),
            1,
        ).replace(
            operational.encode("utf-8"),
            (
                '    "scripts/check-ksg-m1a-composite-v9.py": "' + checker_digest + '",'
            ).encode("utf-8"),
            1,
        )
        return lean_raw, {generator.COMPOSITE_V9_CHECKER_RELATIVE: checker_digest}

    ready_lean, expected = reseal_checker(composite_raw)
    composite_digest = expected[generator.COMPOSITE_V9_CHECKER_RELATIVE]
    generator.validate_composite_v9_cut_bytes(ready_lean, composite_raw, expected)

    placeholder_checker = composite_raw.replace(
        normalized_digest.encode("ascii"), b"0" * 64, 1
    )
    placeholder_lean, placeholder_expected = reseal_checker(placeholder_checker)
    mismatch_checker = composite_raw.replace(
        normalized_digest.encode("ascii"), b"3" * 64, 1
    )
    mismatch_lean, mismatch_expected = reseal_checker(mismatch_checker)
    multiline_checker = (
        b"EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = (\n"
        + b'    "'
        + normalized_digest.encode("ascii")
        + b'"\n)\n'
    )
    multiline_lean, multiline_expected = reseal_checker(multiline_checker)
    mutations = (
        (
            "finalized-projection",
            ready_lean.replace(
                projection.encode("utf-8"),
                (
                    'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + "1" * 64 + '"'
                ).encode("utf-8"),
                1,
            ),
            composite_raw,
            expected,
            "projection cut is not the unique zero placeholder",
        ),
        (
            "additional-finalized-projection",
            ready_lean
            + (
                'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "' + "1" * 64 + '"\n'
            ).encode("utf-8"),
            composite_raw,
            expected,
            "projection cut was finalized before the one-shot replay",
        ),
        (
            "missing-composite-final-cut",
            ready_lean.replace(
                (
                    'EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256 = "'
                    + composite_digest
                    + '"'
                ).encode("utf-8"),
                composite.encode("utf-8"),
                1,
            ),
            composite_raw,
            expected,
            "digest cuts are not unique final literals",
        ),
        (
            "mismatched-operational-cut",
            ready_lean.replace(
                (
                    '    "scripts/check-ksg-m1a-composite-v9.py": "'
                    + composite_digest
                    + '",'
                ).encode("utf-8"),
                (
                    '    "scripts/check-ksg-m1a-composite-v9.py": "' + "2" * 64 + '",'
                ).encode("utf-8"),
                1,
            ),
            composite_raw,
            expected,
            "do not bind the exact checker bytes",
        ),
        (
            "checker-drift-without-lean-reseal",
            ready_lean,
            composite_raw + b"# post-seal drift\n",
            expected,
            "do not bind the exact checker bytes",
        ),
        (
            "normalized-cut-placeholder",
            placeholder_lean,
            placeholder_checker,
            placeholder_expected,
            "normalized Lean checker cut remains a placeholder",
        ),
        (
            "duplicate-normalized-cut",
            reseal_checker(composite_raw + composite_raw)[0],
            composite_raw + composite_raw,
            reseal_checker(composite_raw + composite_raw)[1],
            "normalized Lean checker cut is not a unique final literal",
        ),
        (
            "normalized-cut-mismatch",
            mismatch_lean,
            mismatch_checker,
            mismatch_expected,
            "does not bind the exact three-cut source",
        ),
        (
            "normalized-cut-parenthesized-multiline",
            multiline_lean,
            multiline_checker,
            multiline_expected,
            "normalized Lean checker cut is not a unique final literal",
        ),
        (
            "operational-map-omission",
            ready_lean,
            composite_raw,
            {},
            "do not bind the exact checker bytes",
        ),
    )
    for role, lean_raw, checker_raw, operational_map, diagnostic in mutations:
        try:
            generator.validate_composite_v9_cut_bytes(
                lean_raw, checker_raw, operational_map
            )
        except SystemExit as error:
            require(
                diagnostic in str(error),
                f"generator checksum-cut mutation {role} produced wrong diagnostic",
            )
        else:
            raise SelfTestError(f"generator checksum-cut mutation survived: {role}")


def check_generator_behavior(root: Path, freeze: ModuleType) -> str:
    generator_path = root / "scripts/generate-lean-4.33-replay.py"
    generator = load_exact_module(generator_path, "pid_rs_lean_replay_generator_test")
    check_generator_cut_preflight(generator)
    placeholder = "0" * 64
    projection = freeze.EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256
    composite = freeze.EXPECTED_COMPOSITE_V9_CHECKER_OPERATIONAL_SHA256
    operational = freeze.EXPECTED_OPERATIONAL_WIRING_HASHES[
        generator.COMPOSITE_V9_CHECKER_RELATIVE
    ]
    if projection == placeholder and composite == placeholder:
        require(
            operational == placeholder,
            "composite-v9 all-placeholder authoring state is asymmetric",
        )
        generator_cut_state = "authoring-placeholders-not-generator-ready"
    elif projection == placeholder:
        generator.validate_composite_v9_cut_state(freeze, root)
        generator_cut_state = "live-pre-replay-ready"
    else:
        require(
            composite != placeholder
            and operational != placeholder
            and composite == operational,
            "composite-v9 post-replay cut state is incomplete",
        )
        generator_cut_state = "post-replay-receipt"
    temp_parent = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix="pid-lean-replay-helper-test-", dir=temp_parent
    ) as directory:
        fixture = Path(directory).resolve(strict=True)
        mutation_root = fixture / "source-mutation"
        mutation_scripts = mutation_root / "scripts"
        mutation_scripts.mkdir(parents=True)
        mutation_generator = mutation_scripts / "generate-lean-4.33-replay.py"
        reviewed_source = generator_path.read_text(encoding="utf-8")
        hostile_sources = (
            (
                "nonterminating-guard",
                reviewed_source.replace(
                    '        die("usage: generate-lean-4.33-replay.py (no arguments)")',
                    "        pass",
                    1,
                ),
                "does not terminate",
            ),
            (
                "argv-alias",
                reviewed_source.replace(
                    "    if len(sys.argv) != 1:\n",
                    "    forwarded = sys.argv\n    if len(forwarded) != 1:\n",
                    1,
                ),
                "unique exact zero-argument guard",
            ),
            (
                "interactive-input",
                reviewed_source.replace(
                    "def timestamp() -> str:\n",
                    "def timestamp() -> str:\n    input()\n",
                    1,
                ),
                "alternate argument/input authority",
            ),
        )
        for role, hostile_source, expected in hostile_sources:
            require(
                hostile_source != reviewed_source,
                f"hostile generator source mutation anchor drifted: {role}",
            )
            mutation_generator.write_text(hostile_source, encoding="utf-8")
            try:
                check_generator_zero_argument_contract(mutation_root)
            except SelfTestError as error:
                require(
                    expected in str(error),
                    f"hostile generator mutation {role} produced wrong diagnostic",
                )
            else:
                raise SelfTestError(f"hostile generator mutation survived: {role}")

        environment = generator_test_environment(fixture)
        temporary_directory_identity = generator.directory_identity(
            os.lstat(environment["TMPDIR"])
        )
        cwd = fixture
        payload = b"x" * 18_200
        command = (
            sys.executable,
            "-I",
            "-S",
            "-B",
            "-c",
            "import hashlib,sys;print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())",
        )
        code, stdout, stderr = generator.run_bounded_process(
            command, cwd, environment, payload, temporary_directory_identity
        )
        require(
            code == 0
            and stderr == b""
            and stdout == (hashlib.sha256(payload).hexdigest() + "\n").encode("ascii"),
            "bounded runner did not preserve the exact 18,200-byte stdin",
        )

        original_timeout = generator.COMMAND_TIMEOUT_SECONDS
        original_stdout = generator.MAX_STDOUT_BYTES
        original_stderr = generator.MAX_STDERR_BYTES
        original_term = generator.PROCESS_GROUP_TERM_GRACE_SECONDS
        original_kill = generator.PROCESS_GROUP_KILL_GRACE_SECONDS
        generator.COMMAND_TIMEOUT_SECONDS = 0.2
        generator.MAX_STDOUT_BYTES = 256
        generator.MAX_STDERR_BYTES = 256
        generator.PROCESS_GROUP_TERM_GRACE_SECONDS = 1.0
        generator.PROCESS_GROUP_KILL_GRACE_SECONDS = 1.0
        try:
            hostile_commands = (
                (
                    "timeout",
                    (
                        sys.executable,
                        "-I",
                        "-S",
                        "-B",
                        "-c",
                        "import time;time.sleep(60)",
                    ),
                    "exceeded 0.2 seconds",
                ),
                (
                    "stdout-cap",
                    (
                        sys.executable,
                        "-I",
                        "-S",
                        "-B",
                        "-c",
                        "import sys;sys.stdout.buffer.write(b'x'*257)",
                    ),
                    "child output exceeded 256 bytes",
                ),
                (
                    "stderr-cap",
                    (
                        sys.executable,
                        "-I",
                        "-S",
                        "-B",
                        "-c",
                        "import sys;sys.stderr.buffer.write(b'x'*257)",
                    ),
                    "child output exceeded 256 bytes",
                ),
            )
            for role, hostile, expected in hostile_commands:
                try:
                    generator.run_bounded_process(
                        hostile,
                        cwd,
                        environment,
                        b"",
                        temporary_directory_identity,
                    )
                except SystemExit as error:
                    require(
                        expected in str(error),
                        f"bounded runner {role} diagnostic drifted",
                    )
                else:
                    raise SelfTestError(f"bounded runner did not reject {role}")

            descendant_script = (
                "import subprocess,sys;"
                "p=subprocess.Popen([sys.executable,'-I','-S','-B','-c','import time;time.sleep(60)'],"
                "stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,close_fds=True);"
                "print(p.pid)"
            )
            code, stdout, stderr = generator.run_bounded_process(
                (sys.executable, "-I", "-S", "-B", "-c", descendant_script),
                cwd,
                environment,
                b"",
                temporary_directory_identity,
            )
            require(code == 0 and stderr == b"", "descendant-cleanup probe failed")
            descendant = int(stdout.decode("ascii").strip())
            deadline = time.monotonic() + 2.0
            while True:
                try:
                    os.kill(descendant, 0)
                except ProcessLookupError:
                    break
                if time.monotonic() >= deadline:
                    raise SelfTestError(
                        "bounded runner left a same-group descendant alive"
                    )
                time.sleep(0.02)
        finally:
            generator.COMMAND_TIMEOUT_SECONDS = original_timeout
            generator.MAX_STDOUT_BYTES = original_stdout
            generator.MAX_STDERR_BYTES = original_stderr
            generator.PROCESS_GROUP_TERM_GRACE_SECONDS = original_term
            generator.PROCESS_GROUP_KILL_GRACE_SECONDS = original_kill

        moved_tmpdir = fixture / "tmp-moved"
        Path(environment["TMPDIR"]).rename(moved_tmpdir)
        Path(environment["TMPDIR"]).mkdir(mode=0o700)
        try:
            generator.run_bounded_process(
                (sys.executable, "-I", "-S", "-B", "-c", "pass"),
                cwd,
                environment,
                b"",
                temporary_directory_identity,
            )
        except SystemExit as error:
            require(
                "temporary directory identity drifted" in str(error),
                "temporary-directory replacement diagnostic drifted",
            )
        else:
            raise SelfTestError(
                "bounded runner survived temporary-directory replacement"
            )

        scripts = fixture / "scripts"
        scripts.mkdir()
        cache = scripts / "__pycache__"
        cache.mkdir()
        (cache / "hostile.pyc").write_bytes(b"not bytecode")
        try:
            generator.reject_repository_bytecode_cache(fixture)
        except SystemExit as error:
            require(
                "bytecode cache is forbidden" in str(error),
                "pycache diagnostic drifted",
            )
        else:
            raise SelfTestError("repository pycache survived replay preflight")

        publication = fixture / "publication"
        publication.mkdir()
        descriptor, identity = generator.open_output_parent(publication)
        try:
            generator.publish_receipt_no_clobber(
                b"receipt\n",
                descriptor,
                publication,
                identity,
                "receipt.json",
                "receipt.tmp",
            )
            require(
                (publication / "receipt.json").read_bytes() == b"receipt\n"
                and stat.S_IMODE((publication / "receipt.json").stat().st_mode) == 0o644
                and not (publication / "receipt.tmp").exists(),
                "no-clobber publication did not durably publish exact bytes",
            )
            wrong_mode = publication / "wrong-mode.json"
            wrong_mode.write_bytes(b"wrong mode\n")
            wrong_mode.chmod(0o600)
            try:
                generator.validate_published_receipt(
                    descriptor, wrong_mode.name, b"wrong mode\n"
                )
            except SystemExit as error:
                require(
                    "published receipt identity drifted" in str(error),
                    "wrong-mode published receipt diagnostic drifted",
                )
            else:
                raise SelfTestError("wrong-mode published receipt was accepted")
            wrong_mode.unlink()
            try:
                generator.publish_receipt_no_clobber(
                    b"replacement\n",
                    descriptor,
                    publication,
                    identity,
                    "receipt.json",
                    "receipt.tmp",
                )
            except SystemExit as error:
                require(
                    "versioned output receipt already exists" in str(error),
                    "no-clobber diagnostic drifted",
                )
            else:
                raise SelfTestError("publication overwrote a versioned receipt")
            require(
                (publication / "receipt.json").read_bytes() == b"receipt\n",
                "no-clobber failure changed existing bytes",
            )

            original_validator = generator.validate_published_receipt
            generator.validate_published_receipt = lambda *_args: (_ for _ in ()).throw(
                RuntimeError("injected post-link failure")
            )
            try:
                try:
                    generator.publish_receipt_no_clobber(
                        b"candidate\n",
                        descriptor,
                        publication,
                        identity,
                        "candidate.json",
                        "candidate.tmp",
                    )
                except RuntimeError as error:
                    require(
                        "injected post-link failure" in str(error),
                        "post-link failure diagnostic drifted",
                    )
                else:
                    raise SelfTestError("post-link failure injection did not fail")
            finally:
                generator.validate_published_receipt = original_validator
            require(
                not (publication / "candidate.json").exists()
                and not (publication / "candidate.tmp").exists(),
                "post-link publication failure did not roll back invocation-owned leaves",
            )

            original_link_stat = generator.stat_newly_linked_receipt
            generator.stat_newly_linked_receipt = lambda *_args: (_ for _ in ()).throw(
                RuntimeError("injected first post-link stat failure")
            )
            try:
                try:
                    generator.publish_receipt_no_clobber(
                        b"post-link-stat\n",
                        descriptor,
                        publication,
                        identity,
                        "post-link-stat.json",
                        "post-link-stat.tmp",
                    )
                except RuntimeError as error:
                    require(
                        "injected first post-link stat failure" in str(error),
                        "first post-link stat failure diagnostic drifted",
                    )
                else:
                    raise SelfTestError(
                        "first post-link stat failure injection did not fail"
                    )
            finally:
                generator.stat_newly_linked_receipt = original_link_stat
            require(
                not (publication / "post-link-stat.json").exists()
                and not (publication / "post-link-stat.tmp").exists(),
                "first post-link stat failure did not roll back invocation-owned leaves",
            )

            def wrong_link_identity(parent_descriptor: int, output_leaf: str):
                observed = original_link_stat(parent_descriptor, output_leaf)
                fields = list(observed)
                fields[1] += 1
                return os.stat_result(fields)

            generator.stat_newly_linked_receipt = wrong_link_identity
            try:
                try:
                    generator.publish_receipt_no_clobber(
                        b"post-link-identity\n",
                        descriptor,
                        publication,
                        identity,
                        "post-link-identity.json",
                        "post-link-identity.tmp",
                    )
                except SystemExit as error:
                    require(
                        "published receipt link identity drifted" in str(error),
                        "wrong post-link identity diagnostic drifted",
                    )
                else:
                    raise SelfTestError("wrong post-link identity was accepted")
            finally:
                generator.stat_newly_linked_receipt = original_link_stat
            require(
                not (publication / "post-link-identity.json").exists()
                and not (publication / "post-link-identity.tmp").exists(),
                "wrong post-link identity did not roll back invocation-owned leaves",
            )
            target = publication / "symlink-target"
            target.write_bytes(b"target\n")
            (publication / "symlink.json").symlink_to(target.name)
            try:
                generator.publish_receipt_no_clobber(
                    b"replacement\n",
                    descriptor,
                    publication,
                    identity,
                    "symlink.json",
                    "symlink.tmp",
                )
            except SystemExit as error:
                require(
                    "versioned output receipt already exists" in str(error),
                    "symlink no-clobber diagnostic drifted",
                )
            else:
                raise SelfTestError("publication followed/replaced an output symlink")
            require(
                target.read_bytes() == b"target\n"
                and (publication / "symlink.json").is_symlink()
                and not (publication / "symlink.tmp").exists(),
                "symlink no-clobber failure changed existing state",
            )
        finally:
            os.close(descriptor)

        swap = fixture / "swap"
        swap.mkdir()
        swap_descriptor, swap_identity = generator.open_output_parent(swap)
        moved = fixture / "swap-moved"
        swap.rename(moved)
        swap.mkdir()
        try:
            try:
                generator.publish_receipt_no_clobber(
                    b"receipt\n",
                    swap_descriptor,
                    swap,
                    swap_identity,
                    "receipt.json",
                    "receipt.tmp",
                )
            except SystemExit as error:
                require(
                    "receipt parent route changed during replay" in str(error),
                    "output-parent swap diagnostic drifted",
                )
            else:
                raise SelfTestError(
                    "publication survived output-parent route replacement"
                )
            require(
                not (swap / "receipt.json").exists()
                and not (moved / "receipt.json").exists(),
                "output-parent swap created a receipt outside the bound route",
            )
        finally:
            os.close(swap_descriptor)
    return generator_cut_state


def mutate_mathlib_manifest_field(
    checker: ModuleType, root: Path, field: str, value: str
) -> None:
    path = root / "audit/formal/lean/lake-manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    package = next(item for item in manifest["packages"] if item["name"] == "mathlib")
    package[field] = value
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    refresh_manifest_binding(checker, root)


def mutate_wrong_mathlib_tag(checker: ModuleType, root: Path) -> None:
    mutate_mathlib_manifest_field(checker, root, "inputRev", "v4.32.0")


def mutate_wrong_mathlib_revision(checker: ModuleType, root: Path) -> None:
    mutate_mathlib_manifest_field(checker, root, "rev", "0" * 40)


def mutate_stale_policy_manifest(checker: ModuleType, root: Path) -> None:
    path = root / "audit/formal/lean/toolchain-freeze-policy.json"
    canonical_json(
        path,
        lambda value: value["active_pin"].__setitem__("lake_manifest_sha256", "0" * 64),
    )
    refresh_policy_binding(checker, root)


def mutate_receipt_missing_source(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        path,
        lambda value: value["source_sha256"].pop(next(iter(value["source_sha256"]))),
    )


def mutate_receipt_extra_evidence(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        path,
        lambda value: value["current_evidence_sha256"].__setitem__(
            "audit/evidence/unreviewed.json", "0" * 64
        ),
    )


def mutate_receipt_missing_checker(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        path,
        lambda value: value["checker_sha256"].pop(next(iter(value["checker_sha256"]))),
    )


def mutate_cached_build_credit(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )

    def mutate(value: dict) -> None:
        build = next(
            record
            for record in value["command_records"]
            if record["name"] == "clean_build"
        )
        build["cache_state"]["project_build_directory_absent_before"] = False
        build["cache_state"]["project_oleans_reused"] = True

    canonical_json(path, mutate)


def mutate_clean_build_transcript(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    replacement = b"unexpected clean-build output\n"

    def mutate(value: dict) -> None:
        build = next(
            record
            for record in value["command_records"]
            if record["name"] == "clean_build"
        )
        build["stdout"] = {
            "bytes": len(replacement),
            "sha256": hashlib.sha256(replacement).hexdigest(),
        }
        value["verification"]["clean_build"]["stdout_exact"] = replacement.decode(
            "utf-8"
        )

    canonical_json(path, mutate)


def mutate_valid_replay_timestamps(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )

    def shifted(value: str) -> str:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return (parsed + timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def mutate(value: dict) -> None:
        for record in value["command_records"]:
            record["start_utc"] = shifted(record["start_utc"])
            record["end_utc"] = shifted(record["end_utc"])
        value["execution_window"]["start_utc"] = shifted(
            value["execution_window"]["start_utc"]
        )
        value["execution_window"]["end_utc"] = shifted(
            value["execution_window"]["end_utc"]
        )

    canonical_json(path, mutate)


def mutate_valid_replay_root(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )

    def mutate(value: dict) -> None:
        replacement = "/private/tmp/pid-rs-alternate-replay-root"
        value["execution_environment"]["repo_root_observed"] = replacement
        for record in value["command_records"]:
            relative = record["cwd_repo_relative"]
            record["cwd_observed_absolute"] = (
                replacement if relative == "." else f"{replacement}/{relative}"
            )

    canonical_json(path, mutate)


def mutate_paired_checker_output(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    replacement = b"OK: forged paired checker output\n"
    forged_stream = {
        "bytes": len(replacement),
        "sha256": hashlib.sha256(replacement).hexdigest(),
    }

    def mutate(value: dict) -> None:
        for mode in ("normal", "optimized"):
            record = next(
                item
                for item in value["command_records"]
                if item["name"] == f"finite_self_test:{mode}"
            )
            record["stdout"] = dict(forged_stream)
        parity = value["python_optimization_parity"]["pairs"]["finite_self_test"]
        parity["normal_stdout"] = dict(forged_stream)
        parity["optimized_stdout"] = dict(forged_stream)

    canonical_json(path, mutate)


def mutate_axiom_audit_stdin(_checker: ModuleType, root: Path) -> None:
    path = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    trivial = b"#check True\n"

    def mutate(value: dict) -> None:
        audit = next(
            record
            for record in value["command_records"]
            if record["name"] == "theorem_axiom_audit"
        )
        audit["stdin"] = {
            "bytes": len(trivial),
            "sha256": hashlib.sha256(trivial).hexdigest(),
        }

    canonical_json(path, mutate)


def mutate_derived_receipt_overclaim(checker: ModuleType, root: Path) -> None:
    relative = "audit/evidence/lean-4.32.0-to-4.33.0-derived-instances-2026-08-11.json"
    path = root / relative

    def mutate(value: dict) -> None:
        comparison = value["comparison"]
        comparison.pop("normalized_printed_declaration_skeletons_and_synthesis_equal")
        comparison["normalized_types_bodies_and_synthesis_equal"] = True

    canonical_json(path, mutate)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checker.EXPECTED_DERIVED_EVIDENCE_HASHES[relative] = digest
    receipt = (
        root
        / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json"
    )
    canonical_json(
        receipt,
        lambda value: value["derived_instance_evidence_sha256"].__setitem__(
            relative, digest
        ),
    )


Mutation = tuple[str, Callable[[ModuleType, Path], None], str]
MUTATIONS: tuple[Mutation, ...] = (
    (
        "freeze-trigger-removal",
        mutate_policy_remove_trigger,
        "freeze trigger inventory drifted",
    ),
    (
        "latest-release-enable",
        mutate_policy_enable_latest,
        "enabled latest-release checks",
    ),
    (
        "freeze-nontrigger-removal",
        mutate_policy_remove_nontrigger,
        "freeze nontrigger inventory drifted",
    ),
    (
        "weaken-baseline-unavailability",
        mutate_policy_weaken_baseline_unavailability,
        "evidentiary threshold",
    ),
    (
        "disable-migration-rollback",
        mutate_policy_disable_rollback,
        "transition/rollback policy drifted",
    ),
    (
        "archive-digest",
        mutate_receipt_archive_hash,
        "official archive observation drifted",
    ),
    (
        "local-archive-observation-digest",
        mutate_local_archive_observation,
        "local archive bytes/identity drifted",
    ),
    (
        "exact-archive-route-drift",
        mutate_exact_archive_route,
        "replay host-local archive route drifted",
    ),
    (
        "exact-python-route-drift",
        mutate_exact_python_route,
        "replay host-local execution route drifted",
    ),
    (
        "exact-lean-route-drift",
        mutate_exact_lean_route,
        "replay host-local execution route drifted",
    ),
    (
        "executable-digest-drift",
        mutate_executable_digest,
        "replay host-local executable digest drifted",
    ),
    (
        "executable-size-drift",
        mutate_executable_size,
        "replay host-local executable size drifted",
    ),
    (
        "executable-link-count-drift",
        mutate_executable_link_count,
        "replay host-local executable link-count drifted",
    ),
    (
        "exact-git-route-drift",
        mutate_git_route,
        "replay host-local execution route drifted",
    ),
    (
        "dependency-preflight-removal",
        mutate_dependency_preflight_remove,
        "dependency preflight record count drifted",
    ),
    (
        "dependency-preflight-argv",
        mutate_dependency_preflight_argv,
        "dependency preflight argv drifted",
    ),
    (
        "optimized-parity",
        mutate_receipt_optimized_hash,
        "normal/-O replay parity summary drifted",
    ),
    ("scope-escalation", mutate_receipt_scope, "replay nonclaim disappeared"),
    (
        "ambient-environment-inheritance",
        mutate_environment_inheritance,
        "replay environment inherited ambient variables",
    ),
    (
        "ambient-stdin-inheritance",
        mutate_stdin_inheritance,
        "replay environment inherited ambient variables",
    ),
    (
        "ambient-process-umask",
        mutate_process_umask,
        "replay fixed process umask drifted",
    ),
    (
        "ambient-signal-state",
        mutate_signal_state,
        "replay normalized signal state drifted",
    ),
    (
        "bounded-child-policy",
        mutate_bounded_child_policy,
        "replay bounded-child policy drifted",
    ),
    ("replay-schema-v1", mutate_receipt_schema, "replay receipt schema drifted"),
    (
        "current-receipt-self-digest-inventory",
        mutate_current_receipt_self_digest_inventory,
        "current replay receipt entered its own digest inventory",
    ),
    ("duplicate-json-key", mutate_receipt_duplicate_key, "duplicate JSON key"),
    ("noncanonical-json", mutate_receipt_noncanonical, "not canonical JSON"),
    (
        "coordinated-self-test-custody-rewrite",
        mutate_self_test_with_coordinated_receipt_hash,
        "historical r14 final custody inventory drifted",
    ),
    (
        "historical-receipt-repin-to-current-wiring",
        mutate_receipt_repin_to_current_wiring,
        "historical r14 operational wiring inventory drifted",
    ),
    (
        "preserved-r14-operational-digest",
        mutate_preserved_r14_operational_digest,
        "historical r14 operational wiring inventory drifted",
    ),
    (
        "collapsed-historical-current-wiring-split",
        mutate_collapse_historical_current_wiring_split,
        "preserved-r14/current-C12 operational path split drifted",
    ),
    (
        "historical-receipt-repin-to-current-active-claims",
        mutate_receipt_repin_to_current_active_claims,
        "historical r14 active claim authority drifted",
    ),
    (
        "preserved-r14-active-claim-digest",
        mutate_preserved_r14_active_claim_digest,
        "historical r14 active claim authority drifted",
    ),
    (
        "collapsed-historical-current-active-claim-split",
        mutate_collapse_historical_current_active_claim_split,
        "preserved-r14/current active-claim authority split drifted",
    ),
    (
        "final-custody-missing-path",
        mutate_final_custody_missing,
        "replay custody-gate exact path set drifted",
    ),
    (
        "replay-custody-extra-path",
        mutate_replay_custody_extra,
        "replay-time custody-gate exact path set drifted",
    ),
    (
        "custody-path-in-operational-inventory",
        mutate_custody_in_operational_inventory,
        "custody-gate path entered an ordinary digest inventory: current C12 operational wiring",
    ),
    (
        "custody-path-in-checker-inventory",
        mutate_custody_in_checker_inventory,
        "custody-gate path entered an ordinary digest inventory: active Lean checker",
    ),
    (
        "replay-checker-endpoint-digest",
        mutate_replay_checker_endpoint_hash,
        "historical r14 replay-time custody inventory drifted",
    ),
    ("broad-transparency", mutate_broad_option, "transparency scope inventory drifted"),
    (
        "missing-transparency",
        mutate_missing_option,
        "transparency scope inventory drifted",
    ),
    ("extra-transparency", mutate_extra_option, "transparency scope inventory drifted"),
    ("true-transparency", mutate_option_true, "transparency scope inventory drifted"),
    (
        "file-global-types-transparency",
        mutate_file_global_types_option,
        "transparency scope inventory drifted",
    ),
    (
        "moved-deriving-scope",
        mutate_deriving_scope_after_target,
        "transparency setting moved away from reviewed target",
    ),
    (
        "moved-deriving-scope-comment-spoof",
        mutate_deriving_scope_with_comment_spoof,
        "transparency setting moved away from reviewed target",
    ),
    (
        "moved-proof-scope",
        mutate_proof_scope_to_file_header,
        "transparency setting moved away from reviewed target",
    ),
    ("wrong-lean-commit", mutate_wrong_lean_commit, "exact Lean identity line drifted"),
    ("wrong-lean-build", mutate_wrong_lean_build, "exact Lean identity line drifted"),
    (
        "wrong-lean-platform",
        mutate_wrong_lean_platform,
        "exact Lean identity line drifted",
    ),
    (
        "manifest-regeneration-overclaim",
        mutate_manifest_regeneration_overclaim,
        "manifest-regeneration procedure record drifted",
    ),
    (
        "ci-operational-wiring-drift",
        mutate_ci_wiring,
        "operational wiring digest mismatch: .github/workflows/ci.yml",
    ),
    (
        "agents-operational-wiring-drift",
        mutate_agents_wiring,
        "operational wiring digest mismatch: AGENTS.md",
    ),
    (
        "freeze-document-operational-wiring-drift",
        mutate_freeze_document_wiring,
        "operational wiring digest mismatch: audit/formal/LEAN_4_33_FREEZE_AND_REPLAY.md",
    ),
    (
        "just-operational-wiring-drift",
        mutate_just_wiring,
        "operational wiring digest mismatch: justfile",
    ),
    (
        "scripts-readme-operational-wiring-drift",
        mutate_scripts_readme_wiring,
        "operational wiring digest mismatch: scripts/README.md",
    ),
    (
        "replay-generator-operational-wiring-drift",
        mutate_replay_generator_wiring,
        "operational wiring digest mismatch: scripts/generate-lean-4.33-replay.py",
    ),
    (
        "changelog-operational-wiring-drift",
        mutate_changelog_wiring,
        "operational wiring digest mismatch: CHANGELOG.md",
    ),
    (
        "deep-audit-adjudication-operational-wiring-drift",
        mutate_deep_audit_adjudication_wiring,
        "operational wiring digest mismatch: audit/evidence/external-model-pid-rs-deep-audit-adjudication-2026-08-12.md",
    ),
    (
        "active-plan-operational-wiring-drift",
        mutate_active_plan_wiring,
        "operational wiring digest mismatch: audit/evidence/wibral-pid-program-active-plan-2026-08-12.md",
    ),
    (
        "m1a-boundary-operational-wiring-drift",
        mutate_m1a_boundary_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-candidate-boundary-2026-08-13.md",
    ),
    (
        "m1a-custody-correction-boundary-operational-wiring-drift",
        mutate_m1a_custody_correction_boundary_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-custody-correction-boundary-2026-08-13.md",
    ),
    (
        "m1a-custody-correction-policy-operational-wiring-drift",
        mutate_m1a_custody_correction_policy_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-custody-correction-path-policy-v1.json",
    ),
    (
        "m1a-failed-ci-receipt-operational-wiring-drift",
        mutate_m1a_failed_ci_receipt_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-public-ci-run-31686107959-failure.json",
    ),
    (
        "m1a-policy-operational-wiring-drift",
        mutate_m1a_policy_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-path-policy-v1.json",
    ),
    (
        "m1a-schema-operational-wiring-drift",
        mutate_m1a_schema_wiring,
        "operational wiring digest mismatch: audit/schemas/ksg-rev4-m1a-receipt-v1.schema.json",
    ),
    (
        "m1a-checker-operational-wiring-drift",
        mutate_m1a_checker_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-phase.py",
    ),
    (
        "m1a-self-test-operational-wiring-drift",
        mutate_m1a_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-phase-self-test.py",
    ),
    (
        "m1a-composite-schema-operational-wiring-drift",
        mutate_m1a_composite_schema_wiring,
        "operational wiring digest mismatch: audit/schemas/ksg-rev4-m1a-composite-receipt-v2.schema.json",
    ),
    (
        "m1a-custody-correction-checker-operational-wiring-drift",
        mutate_m1a_custody_correction_checker_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-custody-correction.py",
    ),
    (
        "m1a-custody-correction-self-test-operational-wiring-drift",
        mutate_m1a_custody_correction_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-custody-correction-self-test.py",
    ),
    (
        "m1a-hosted-recovery-negative-operational-wiring-drift",
        mutate_m1a_hosted_recovery_negative_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-custody-correction-ci-run-31724449805-failure.json",
    ),
    (
        "m1a-hosted-recovery-policy-operational-wiring-drift",
        mutate_m1a_hosted_recovery_policy_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-hosted-recovery-path-policy-v1.json",
    ),
    (
        "m1a-hosted-recovery-boundary-operational-wiring-drift",
        mutate_m1a_hosted_recovery_boundary_wiring,
        "operational wiring digest mismatch: audit/evidence/ksg-rev4-m1a-hosted-recovery-boundary-2026-08-13.md",
    ),
    (
        "m1a-hosted-recovery-composite-schema-operational-wiring-drift",
        mutate_m1a_hosted_recovery_composite_schema_wiring,
        "operational wiring digest mismatch: audit/schemas/ksg-rev4-m1a-composite-receipt-v3.schema.json",
    ),
    (
        "m1a-hosted-recovery-checker-operational-wiring-drift",
        mutate_m1a_hosted_recovery_checker_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-hosted-recovery.py",
    ),
    (
        "m1a-hosted-recovery-self-test-operational-wiring-drift",
        mutate_m1a_hosted_recovery_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-m1a-hosted-recovery-self-test.py",
    ),
    (
        "ksg-revision4-terminal-index-checker-operational-wiring-drift",
        mutate_ksg_revision4_terminal_index_checker_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-revision4-terminal-index.py",
    ),
    (
        "ksg-revision4-terminal-index-self-test-operational-wiring-drift",
        mutate_ksg_revision4_terminal_index_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-ksg-revision4-terminal-index-self-test.py",
    ),
    (
        "post-v2-schema-operational-wiring-drift",
        mutate_post_v2_schema_wiring,
        "operational wiring digest mismatch: audit/schemas/post-commit-source-state-v2.schema.json",
    ),
    (
        "certified-checker-operational-wiring-drift",
        mutate_certified_checker_wiring,
        "operational wiring digest mismatch: scripts/check-certified-sxpid2-claim.py",
    ),
    (
        "certified-self-test-operational-wiring-drift",
        mutate_certified_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-certified-sxpid2-claim-self-test.py",
    ),
    (
        "post-v2-checker-operational-wiring-drift",
        mutate_post_v2_checker_wiring,
        "operational wiring digest mismatch: scripts/check-post-commit-source-state-v2.py",
    ),
    (
        "post-v2-self-test-operational-wiring-drift",
        mutate_post_v2_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-post-commit-source-state-v2-self-test.py",
    ),
    (
        "zeta-checker-operational-wiring-drift",
        mutate_zeta_checker_wiring,
        "operational wiring digest mismatch: scripts/check-zeta-pid-transfer-firewall.py",
    ),
    (
        "zeta-self-test-operational-wiring-drift",
        mutate_zeta_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-zeta-pid-transfer-firewall-self-test.py",
    ),
    (
        "workflow-pdf-gate-operational-wiring-drift",
        mutate_workflow_pdf_gate_wiring,
        "operational wiring digest mismatch: scripts/check-mathematical-workflow-pdf.sh",
    ),
    (
        "workflow-pdf-self-test-operational-wiring-drift",
        mutate_workflow_pdf_self_test_wiring,
        "operational wiring digest mismatch: scripts/check-mathematical-workflow-pdf-self-test.sh",
    ),
    (
        "formal-pdf-set-operational-wiring-drift",
        mutate_formal_pdf_set_wiring,
        "operational wiring digest mismatch: scripts/check-formal-pdf-set.sh",
    ),
    (
        "retired-v1-checker-recreated",
        mutate_retired_v1_checker_recreated,
        "retired operational path unexpectedly exists: scripts/check-post-commit-source-state-v1.py",
    ),
    (
        "retired-v1-self-test-recreated",
        mutate_retired_v1_self_test_recreated,
        "retired operational path unexpectedly exists: scripts/check-post-commit-source-state-v1-self-test.py",
    ),
    (
        "current-ksg-revision-index-drift",
        mutate_current_ksg_revision_index,
        "active claim authority digest mismatch: claims/KSG-INTEGER-HARMONIC-001/revision-index.md",
    ),
    (
        "current-sx-count-event-revision-index-drift",
        mutate_current_sx_count_event_revision_index,
        "active claim authority digest mismatch: claims/SX-COUNT-EVENT-BRIDGE-001/revision-index.md",
    ),
    (
        "coordinated-agents-current-pointer-rewind",
        mutate_coordinated_agents_pointer_rewind,
        "current/prior r14 replay pointer semantics drifted: AGENTS.md",
    ),
    (
        "coordinated-claim-current-pointer-rewind",
        mutate_coordinated_claim_pointer_rewind,
        "current/prior r14 replay pointer semantics drifted: claims/SX-COUNT-ATOM-BRIDGE-001/claim-v2.md",
    ),
    (
        "coordinated-agents-r14-sequence-conflation",
        mutate_coordinated_agents_r14_sequence_conflation,
        "r14 sequencing/non-conflation boundary drifted: AGENTS.md",
    ),
    (
        "coordinated-agents-r8-replay-status-conflation",
        mutate_coordinated_agents_r8_replay_status_conflation,
        "current/prior r14 replay pointer semantics drifted: AGENTS.md",
    ),
    (
        "wrong-mathlib-tag",
        mutate_wrong_mathlib_tag,
        "Lake package pin drifted: mathlib",
    ),
    (
        "wrong-mathlib-revision",
        mutate_wrong_mathlib_revision,
        "Lake package pin drifted: mathlib",
    ),
    (
        "stale-policy-manifest",
        mutate_stale_policy_manifest,
        "freeze manifest digest drifted",
    ),
    (
        "missing-source-member",
        mutate_receipt_missing_source,
        "replay source inventory drifted",
    ),
    (
        "extra-evidence-member",
        mutate_receipt_extra_evidence,
        "replay current evidence inventory drifted",
    ),
    (
        "missing-checker-member",
        mutate_receipt_missing_checker,
        "replay checker inventory drifted",
    ),
    (
        "cached-build-credit",
        mutate_cached_build_credit,
        "clean build cache-isolation record drifted",
    ),
    (
        "clean-build-transcript-drift",
        mutate_clean_build_transcript,
        "clean build replay drifted",
    ),
    (
        "valid-timestamp-rewrite",
        mutate_valid_replay_timestamps,
        "replay receipt reviewed projection drifted",
    ),
    (
        "valid-observed-root-rewrite",
        mutate_valid_replay_root,
        "replay host-local execution route drifted",
    ),
    (
        "paired-checker-output-rewrite",
        mutate_paired_checker_output,
        "replay receipt reviewed projection drifted",
    ),
    ("trivial-axiom-audit-stdin", mutate_axiom_audit_stdin, "exact 246-name query"),
    (
        "historical-byte-drift",
        mutate_historical_bytes,
        "preserved historical 4.32 evidence digest mismatch",
    ),
    (
        "prior-replay-aug11-byte-drift",
        mutate_prior_replay_aug11_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug12-byte-drift",
        mutate_prior_replay_aug12_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug12-coordinated-schema-drift",
        mutate_prior_replay_aug12_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug12-r2-byte-drift",
        mutate_prior_replay_aug12_r2_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug12-r2-coordinated-schema-drift",
        mutate_prior_replay_aug12_r2_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug12-r3-byte-drift",
        mutate_prior_replay_aug12_r3_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug12-r3-coordinated-schema-drift",
        mutate_prior_replay_aug12_r3_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug12-r4-byte-drift",
        mutate_prior_replay_aug12_r4_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug12-r4-coordinated-schema-drift",
        mutate_prior_replay_aug12_r4_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug13-r5-byte-drift",
        mutate_prior_replay_aug13_r5_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug13-r5-coordinated-schema-drift",
        mutate_prior_replay_aug13_r5_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug13-r6-byte-drift",
        mutate_prior_replay_aug13_r6_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug13-r6-coordinated-schema-drift",
        mutate_prior_replay_aug13_r6_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug13-r7-byte-drift",
        mutate_prior_replay_aug13_r7_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug13-r7-coordinated-schema-drift",
        mutate_prior_replay_aug13_r7_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug14-r8-byte-drift",
        mutate_prior_replay_aug14_r8_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug14-r8-coordinated-schema-drift",
        mutate_prior_replay_aug14_r8_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug15-r9-byte-drift",
        mutate_prior_replay_aug15_r9_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug15-r9-coordinated-schema-drift",
        mutate_prior_replay_aug15_r9_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug18-r10-byte-drift",
        mutate_prior_replay_aug18_r10_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug18-r10-coordinated-schema-drift",
        mutate_prior_replay_aug18_r10_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug18-r11-byte-drift",
        mutate_prior_replay_aug18_r11_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug18-r11-coordinated-schema-drift",
        mutate_prior_replay_aug18_r11_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug18-r12-byte-drift",
        mutate_prior_replay_aug18_r12_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug18-r12-coordinated-schema-drift",
        mutate_prior_replay_aug18_r12_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-aug19-r13-byte-drift",
        mutate_prior_replay_aug19_r13_bytes,
        "preserved prior 4.33 replay digest mismatch",
    ),
    (
        "prior-replay-aug19-r13-coordinated-schema-drift",
        mutate_prior_replay_aug19_r13_coordinated_schema,
        "preserved prior replay lost its exact schema identity",
    ),
    (
        "prior-replay-operational-role-overlap",
        mutate_prior_replay_operational_overlap,
        "current operational wiring overlaps preserved prior replay evidence",
    ),
    (
        "derived-output-drift",
        mutate_derived_output,
        "derived-instance evidence digest mismatch",
    ),
    (
        "derived-body-overclaim",
        mutate_derived_receipt_overclaim,
        "overclaims full body equality",
    ),
    ("policy-symlink", mutate_policy_symlink, "regular non-symbolic-link"),
    ("receipt-hardlink", mutate_receipt_hardlink, "exactly one hard link"),
)


def run_mutation(
    checker_snapshot: CheckerSourceSnapshot,
    name: str,
    mutation: Callable[[ModuleType, Path], None],
    expected: str,
) -> None:
    checker = instantiate_checker(checker_snapshot)
    temp_parent = Path(tempfile.gettempdir()).resolve(strict=True)
    with tempfile.TemporaryDirectory(
        prefix=f"pid-lean-freeze-{name}-", dir=temp_parent
    ) as directory:
        fixture = Path(directory) / "repo"
        copy_fixture(checker, checker_snapshot, fixture)
        configure_fixture(checker, fixture)
        mutation(checker, fixture)
        try:
            checker.check_all()
        except (checker.FreezeError, OSError) as error:
            require(expected in str(error), f"{name}: wrong diagnostic: {error}")
        else:
            raise SelfTestError(f"freeze mutation survived: {name}")


def main() -> int:
    try:
        checker_snapshot = read_checker_source_once()
        baseline = instantiate_checker(checker_snapshot)
        check_checker_snapshot_contract(checker_snapshot, expected_instantiations=1)
    except (OSError, SelfTestError) as error:
        print(f"Lean toolchain freeze self-test failed: {error}", file=sys.stderr)
        return 1
    try:
        check_generator_zero_argument_contract(ROOT)
        generator_cut_state = check_generator_behavior(ROOT, baseline)
        check_structural_placeholder_contract(baseline)
        if (ROOT / CURRENT_RECEIPT_RELATIVE).exists():
            baseline.check_all()
        else:
            temp_parent = Path(tempfile.gettempdir()).resolve(strict=True)
            with tempfile.TemporaryDirectory(
                prefix="pid-lean-freeze-pre-receipt-baseline-", dir=temp_parent
            ) as directory:
                fixture = Path(directory) / "repo"
                copy_fixture(baseline, checker_snapshot, fixture)
                configure_fixture(baseline, fixture)
                baseline.check_all()
        for name, mutation, expected in MUTATIONS:
            run_mutation(checker_snapshot, name, mutation, expected)
        check_checker_snapshot_contract(
            checker_snapshot, expected_instantiations=1 + len(MUTATIONS)
        )
    except (baseline.FreezeError, OSError, SelfTestError) as error:
        print(f"Lean toolchain freeze self-test failed: {error}", file=sys.stderr)
        return 1
    print(
        "OK: Lean 4.33 freeze self-test rejected all "
        f"{len(MUTATIONS)} policy, replay, source-scope, pin, historical, "
        "derived-evidence, canonical-JSON, symlink, and hard-link mutations"
        f"; composite-v9 generator cut state: {generator_cut_state}"
        + (
            " against a non-evidentiary pre-receipt simulation"
            if not (ROOT / CURRENT_RECEIPT_RELATIVE).exists()
            else ""
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
