#!/usr/bin/env python3
"""Preflight or capture one bounded local composite-v11 closure observation.

The fixed evidence command is ``just ksg-composite-v11``.  ``--preflight-live``
performs the real production-roster filesystem and Git-object checks without
running the command or writing evidence.  Final capture additionally requires a
clean direct C9->C11 commit and every authority bound to that exact Git tree.
"""

from __future__ import annotations

import sys


if not (
    sys.implementation.name == "cpython"
    and sys.version_info == (3, 14, 6, "final", 0)
    and sys._is_gil_enabled()
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: capture-ksg-m1a-composite-v11-local-closure.py requires GIL-enabled CPython 3.14.6 -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform
import pwd
import re
import stat
import subprocess
import tempfile
import time
import types
from typing import Any


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
REPOSITORY = "sepahead/pid-rs"
C9_COMMIT = "337fe9b7f7cf30a8f00138310ce0398d9e95b9c5"
C9_TREE = "325f9fb463e2ec8ed36f0c7b1d61c119e6861d9c"
C11_MESSAGE = "Repair KSG M1a composite v11 contract\n"
V8_RELATIVE = "scripts/capture-ksg-m1a-composite-v8-local-closure.py"
V8_PATH = ROOT / V8_RELATIVE
V8_SHA256 = "b9b0a41cb2027d1cba464040843656bc2486e317f8cf1d3079cb58b02f7c6ba7"
V8_SIZE_BYTES = 40_584
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v11-local-closure.py"
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v11.schema.json"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v11.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v11-self-test.py"
HOSTED_TOOL_RELATIVE = "scripts/capture-ksg-m1a-composite-v11.py"
HOSTED_SCHEMA_RELATIVE = (
    "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v11.schema.json"
)
RECEIPT_SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-receipt-v11.schema.json"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v11-path-policy-v1.json"
BOUNDARY_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-v11-boundary-2026-08-23.md"
C10_FAILURE_RELATIVE = (
    "audit/evidence/ksg-rev4-m1a-composite-v10-diagnostic-failure-2026-08-23.json"
)
WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v11.yml"
RETIRED_V9_WORKFLOW_RELATIVE = ".github/workflows/ksg-m1a-composite-v9.yml"
TERMINAL_C9_CAPTURE_RELATIVE = "audit/evidence/ksg-rev4-m1a-composite-c9-terminal-hosted-capture-v10-2026-08-23.json"
CURRENT_SOURCE_CHECKER_RELATIVE = "scripts/check-current-source-state-v1.py"
CURRENT_SOURCE_SELF_TEST_RELATIVE = "scripts/check-current-source-state-v1-self-test.py"
CURRENT_SOURCE_MANIFEST_RELATIVE = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_SCHEMA_RELATIVE = "audit/schemas/current-source-state-v1.schema.json"
NORMALIZER_RELATIVE = "scripts/normalize-actions-checkout-git-info-exclude.py"
NORMALIZER_SELF_TEST_RELATIVE = (
    "scripts/normalize-actions-checkout-git-info-exclude-self-test.py"
)
COMMAND_ARGV = ("just", "ksg-composite-v11")
COMMAND_TIMEOUT_SECONDS = 14_400
MAX_VERSION_STREAM_BYTES = 64 * 1024
MAX_ORDINARY_AUTHORITY_BYTES = 2 * 1024 * 1024
MAX_TERMINAL_C9_CAPTURE_BYTES = 4 * 1024 * 1024
MAX_AUTHORITY_AGGREGATE_BYTES = 16 * 1024 * 1024
MAX_COMMAND_STREAM_BYTES = 8 * 1024 * 1024
MAX_RECORD_BYTES = 32 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
LIMITS = {
    "authority_aggregate_bytes": MAX_AUTHORITY_AGGREGATE_BYTES,
    "ordinary_authority_bytes": MAX_ORDINARY_AUTHORITY_BYTES,
    "terminal_c9_capture_bytes": MAX_TERMINAL_C9_CAPTURE_BYTES,
    "command_stream_bytes": MAX_COMMAND_STREAM_BYTES,
    "executable_bytes": MAX_EXECUTABLE_BYTES,
    "record_bytes": MAX_RECORD_BYTES,
    "version_stream_bytes": MAX_VERSION_STREAM_BYTES,
}


@dataclass(frozen=True)
class AuthoritySpec:
    """One non-skewable Git/live/limit contract for an authority path."""

    path: str
    role: str
    git_mode: str
    live_mode: int
    limit_class: str
    authoring_required: bool = True


def ordinary(path: str, role: str, *, executable: bool = False) -> AuthoritySpec:
    return AuthoritySpec(
        path,
        role,
        "100755" if executable else "100644",
        0o755 if executable else 0o644,
        "ordinary_2mib",
    )


AUTHORITY_SPECS = tuple(
    sorted(
        (
            ordinary(".github/workflows/ci.yml", "repository_ci_authority"),
            ordinary(RETIRED_V9_WORKFLOW_RELATIVE, "retired_v9_manual_refusal"),
            ordinary(WORKFLOW_RELATIVE, "dedicated_v11_workflow_authority"),
            ordinary(".gitleaks.toml", "narrow_secret_scan_policy_authority"),
            ordinary("crates/pid-core/build_support.rs", "rust_1_98_parser_repair"),
            ordinary("justfile", "local_command_wiring"),
            ordinary(BOUNDARY_RELATIVE, "v11_semantic_boundary"),
            ordinary(POLICY_RELATIVE, "v11_path_policy"),
            ordinary(C10_FAILURE_RELATIVE, "rejected_c10_diagnostic_record"),
            ordinary(HOSTED_SCHEMA_RELATIVE, "v11_hosted_capture_schema"),
            ordinary(SCHEMA_RELATIVE, "local_l11_closure_schema"),
            ordinary(RECEIPT_SCHEMA_RELATIVE, "v11_receipt_schema"),
            ordinary(SCRIPT_RELATIVE, "bounded_local_l11_capture_tool"),
            ordinary(HOSTED_TOOL_RELATIVE, "bounded_hosted_v11_capture_tool"),
            ordinary(SELF_TEST_RELATIVE, "composite_v11_hostile_suite"),
            ordinary(CHECKER_RELATIVE, "composite_v11_semantic_gate"),
            ordinary(NORMALIZER_RELATIVE, "git_info_exclude_normalizer"),
            ordinary(NORMALIZER_SELF_TEST_RELATIVE, "git_info_exclude_hostile_suite"),
            ordinary(
                CURRENT_SOURCE_CHECKER_RELATIVE,
                "current_source_semantic_gate",
                executable=True,
            ),
            ordinary(
                CURRENT_SOURCE_MANIFEST_RELATIVE,
                "fresh_r16_current_source_manifest",
            ),
            ordinary(
                CURRENT_SOURCE_SCHEMA_RELATIVE,
                "current_source_manifest_schema",
            ),
            ordinary(
                CURRENT_SOURCE_SELF_TEST_RELATIVE,
                "current_source_hostile_suite",
                executable=True,
            ),
            AuthoritySpec(
                TERMINAL_C9_CAPTURE_RELATIVE,
                "terminal_c9_hosted_capture",
                "100644",
                0o644,
                "terminal_c9_capture_4mib",
                False,
            ),
        ),
        key=lambda item: item.path,
    )
)
LIMIT_CLASS_BYTES = {
    "ordinary_2mib": MAX_ORDINARY_AUTHORITY_BYTES,
    "terminal_c9_capture_4mib": MAX_TERMINAL_C9_CAPTURE_BYTES,
}
AUTHORITY_BY_PATH = {spec.path: spec for spec in AUTHORITY_SPECS}
NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C11 checkout and is neither independent replication nor hosted first-attempt authority.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, builtins, libraries, TeX helpers, or transitive processes.",
    "Only the exact named terminal-C9 hosted-capture path receives the 4 MiB class; every other authority remains at 2 MiB and the complete roster remains capped at 16 MiB.",
    "The redacted environment-route digest is an opaque correlated fingerprint, not a publicly recomputable path authority.",
    "HOME is absent; isolated XDG and TeX roots do not prove absence of every passwd-derived fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove every descendant was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove output contains no sensitive information.",
    "Ordinary Git status plus selected metadata checks exclude ignored products and uninspected Git metadata, so this is not hermetic closure.",
    "A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
    "C10 is a rejected off-main diagnostic subject: this record grants no C10, L10, R15, hosted-success, ancestry, or qualification credit.",
]


class BootstrapError(RuntimeError):
    """The immutable v8 local-recorder primitives could not be loaded."""


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v8() -> bytes:
    before = V8_PATH.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not V8_PATH.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V8_SIZE_BYTES,
        "immutable v8 local-recorder primitive metadata changed",
    )
    descriptor = os.open(V8_PATH, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        bootstrap_require(
            (
                opened.st_dev,
                opened.st_ino,
                opened.st_mode,
                opened.st_nlink,
                opened.st_size,
            )
            == (
                before.st_dev,
                before.st_ino,
                before.st_mode,
                before.st_nlink,
                before.st_size,
            ),
            "opened immutable v8 local-recorder identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "short immutable v8 local-recorder read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(
            os.read(descriptor, 1) == b"", "immutable v8 local recorder grew"
        )
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = V8_PATH.lstat()
    for field in (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    ):
        bootstrap_require(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field),
            "immutable v8 local-recorder primitive changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V8_SHA256,
        "immutable v8 local-recorder primitive digest changed",
    )
    return raw


def load_bound_v8(raw: bytes) -> types.ModuleType:
    module = types.ModuleType("pid_rs_capture_ksg_m1a_composite_v8_local_primitives")
    module.__file__ = os.fspath(V8_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V8_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


try:
    V8_RAW = read_bound_v8()
    V8 = load_bound_v8(V8_RAW)
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected immutable-v8 local-recorder load failure", file=sys.stderr)
    raise SystemExit(2) from None

try:
    V8_SELF_TEST_BASELINE = V8.offline_self_test()
    bootstrap_require(
        V8_SELF_TEST_BASELINE.get("result") == "pass",
        "immutable v8 local-recorder self-test failed before the v11 rebind",
    )
except Exception:
    print(
        "ERROR: immutable-v8 local-recorder self-test failed before v11 rebind",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CaptureError = V8.CaptureError
require = V8.require
sha256 = V8.sha256
canonical_json = V8.canonical_json
PRIMITIVES = V8.PRIMITIVES

# Reuse exact routing, process, executable, and repository primitives with the
# v11 subject. The record construction and authority-bound selection stay local
# to this module and are not monkey-patched into the immutable source bytes.
PRIMITIVES.C5_COMMIT = C9_COMMIT
PRIMITIVES.C6_MESSAGE = C11_MESSAGE
PRIMITIVES.TOOL_SPECS = dict(PRIMITIVES.TOOL_SPECS) | {"rg": ("--version",)}


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def byte_binding(raw: bytes) -> dict[str, Any]:
    return {
        "body_base64": base64.b64encode(raw).decode("ascii"),
        "sha256": sha256(raw),
        "size_bytes": len(raw),
    }


def metadata_identity(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_uid,
        value.st_gid,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def open_canonical_root(root: Path) -> tuple[int, tuple[int, ...]]:
    """Open one canonical, real repository root and bind its directory entry."""

    require(root.is_absolute(), "repository root is not absolute")
    require(root.resolve(strict=True) == root, "repository root route is not canonical")
    before = root.lstat()
    require(stat.S_ISDIR(before.st_mode), "repository root is not a real directory")
    descriptor = os.open(root, directory_flags())
    opened = os.fstat(descriptor)
    if metadata_identity(opened) != metadata_identity(before):
        os.close(descriptor)
        raise CaptureError("repository root changed while opening")
    return descriptor, metadata_identity(opened)


def recheck_canonical_root(
    root: Path, descriptor: int, expected: tuple[int, ...]
) -> None:
    require(
        metadata_identity(os.fstat(descriptor))
        == expected
        == metadata_identity(root.lstat()),
        "repository root route changed during authority inspection",
    )


def stable_authority_read(root_fd: int, spec: AuthoritySpec) -> bytes:
    """Read one authority component-by-component without following a symlink."""

    components = spec.path.split("/")
    require(
        components
        and all(component not in {"", ".", ".."} for component in components),
        "authority path is not a safe repository-relative route",
    )
    opened_directories: list[tuple[int, tuple[int, ...], int, str]] = []
    parent_fd = root_fd
    try:
        for component in components[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            require(
                stat.S_ISDIR(before.st_mode),
                f"authority ancestor is not a directory: {spec.path}",
            )
            descriptor_fd = os.open(component, directory_flags(), dir_fd=parent_fd)
            opened = os.fstat(descriptor_fd)
            require(
                metadata_identity(opened) == metadata_identity(before),
                f"authority ancestor changed while opening: {spec.path}",
            )
            opened_directories.append(
                (descriptor_fd, metadata_identity(opened), parent_fd, component)
            )
            parent_fd = descriptor_fd
        leaf = components[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(stat.S_ISREG(before.st_mode), f"authority is not regular: {spec.path}")
        require(before.st_nlink == 1, f"authority is multiply linked: {spec.path}")
        require(
            stat.S_IMODE(before.st_mode) == spec.live_mode,
            f"authority live mode differs: {spec.path}",
        )
        maximum = LIMIT_CLASS_BYTES[spec.limit_class]
        require(
            0 < before.st_size <= maximum, f"authority exceeds its class: {spec.path}"
        )
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        file_fd = os.open(leaf, flags, dir_fd=parent_fd)
        try:
            opened = os.fstat(file_fd)
            require(
                metadata_identity(opened) == metadata_identity(before),
                f"authority changed before read: {spec.path}",
            )
            chunks: list[bytes] = []
            remaining = before.st_size
            while remaining:
                chunk = os.read(file_fd, min(remaining, 1024 * 1024))
                require(chunk != b"", f"authority read was short: {spec.path}")
                chunks.append(chunk)
                remaining -= len(chunk)
            require(
                os.read(file_fd, 1) == b"", f"authority grew while read: {spec.path}"
            )
            after_fd = os.fstat(file_fd)
        finally:
            os.close(file_fd)
        after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(
            metadata_identity(before)
            == metadata_identity(opened)
            == metadata_identity(after_fd)
            == metadata_identity(after),
            f"authority identity changed during read: {spec.path}",
        )
        for descriptor_fd, expected, owning_parent_fd, component in opened_directories:
            require(
                metadata_identity(os.fstat(descriptor_fd))
                == expected
                == metadata_identity(
                    os.stat(
                        component,
                        dir_fd=owning_parent_fd,
                        follow_symlinks=False,
                    )
                ),
                f"authority ancestor changed during read: {spec.path}",
            )
        return b"".join(chunks)
    finally:
        for descriptor_fd, _expected, _parent_fd, _component in reversed(
            opened_directories
        ):
            os.close(descriptor_fd)


def git_object_oid(kind: str, raw: bytes) -> str:
    header = f"{kind} {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw, usedforsecurity=False).hexdigest()


def require_aggregate_bound(total: int) -> None:
    require(
        type(total) is int and 0 <= total <= MAX_AUTHORITY_AGGREGATE_BYTES,
        "authority aggregate exceeds 16 MiB",
    )


def run_internal(
    executable: Path,
    argv: tuple[str, ...],
    environment: dict[str, str],
    maximum_stream_bytes: int,
    *,
    allowed_exit_codes: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes, bytes]:
    require(
        maximum_stream_bytes
        in {
            MAX_VERSION_STREAM_BYTES,
            MAX_ORDINARY_AUTHORITY_BYTES,
            MAX_TERMINAL_C9_CAPTURE_BYTES,
        },
        "internal command stream class changed",
    )
    code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(
        argv,
        executable,
        environment,
        ROOT,
        60,
        maximum_stream_bytes,
    )
    require(
        not timed_out and code in allowed_exit_codes, "bounded internal command failed"
    )
    return code, stdout, stderr


def git_output(
    git_path: Path,
    environment: dict[str, str],
    maximum_stream_bytes: int,
    *arguments: str,
    allowed_exit_codes: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes]:
    code, stdout, stderr = run_internal(
        git_path,
        ("git", *arguments),
        environment,
        maximum_stream_bytes,
        allowed_exit_codes=allowed_exit_codes,
    )
    require(stderr == b"", "isolated Git query wrote stderr")
    return code, stdout


def git_tree_entry(
    git_path: Path, environment: dict[str, str], head: str, relative: str
) -> tuple[str, str] | None:
    _code, raw = git_output(
        git_path,
        environment,
        MAX_VERSION_STREAM_BYTES,
        "ls-tree",
        "-z",
        head,
        "--",
        relative,
    )
    if raw == b"":
        return None
    require(raw.endswith(b"\0") and raw.count(b"\0") == 1, "Git tree row changed")
    metadata, separator, path = raw[:-1].partition(b"\t")
    fields = metadata.split(b" ")
    require(
        separator == b"\t"
        and path == relative.encode("utf-8")
        and len(fields) == 3
        and fields[1] == b"blob",
        "Git tree authority row changed",
    )
    try:
        mode = fields[0].decode("ascii")
        oid = fields[2].decode("ascii")
    except UnicodeError:
        raise CaptureError("Git tree authority row is not ASCII") from None
    require(
        mode in {"100644", "100755"} and SHA1_RE.fullmatch(oid) is not None,
        "Git tree authority metadata changed",
    )
    return mode, oid


def verified_git_object(
    git_path: Path,
    environment: dict[str, str],
    kind: str,
    oid: str,
    maximum_stream_bytes: int,
) -> bytes:
    _code, raw = git_output(
        git_path,
        environment,
        maximum_stream_bytes,
        "cat-file",
        kind,
        oid,
    )
    require(git_object_oid(kind, raw) == oid, f"Git {kind} object hash mismatch")
    return raw


def verify_commit_tree_objects(
    git_path: Path, environment: dict[str, str], head: str
) -> str:
    verified_git_object(
        git_path, environment, "commit", head, MAX_ORDINARY_AUTHORITY_BYTES
    )
    _code, tree_raw = git_output(
        git_path,
        environment,
        MAX_VERSION_STREAM_BYTES,
        "rev-parse",
        "--verify",
        f"{head}^{{tree}}",
    )
    try:
        tree = tree_raw.decode("ascii", errors="strict").removesuffix("\n")
    except UnicodeError:
        raise CaptureError("Git tree identity is not ASCII") from None
    require(SHA1_RE.fullmatch(tree) is not None, "Git tree identity changed")
    verified_git_object(
        git_path, environment, "tree", tree, MAX_ORDINARY_AUTHORITY_BYTES
    )
    return tree


def inspect_authorities(
    git_path: Path,
    environment: dict[str, str],
    head: str,
    *,
    require_committed: bool,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    aggregate = 0
    root_fd, root_identity = open_canonical_root(ROOT)
    try:
        for spec in AUTHORITY_SPECS:
            try:
                raw = stable_authority_read(root_fd, spec)
            except FileNotFoundError:
                require(
                    not require_committed and not spec.authoring_required,
                    f"required authority is absent: {spec.path}",
                )
                result.append(
                    {
                        "binding_state": "pending_evidence_absent",
                        "git_blob_oid": None,
                        "git_mode": None,
                        "limit_class": spec.limit_class,
                        "live_blob_oid": None,
                        "live_mode": None,
                        "path": spec.path,
                        "role": spec.role,
                        "sha256": None,
                        "size_bytes": None,
                    }
                )
                continue
            aggregate += len(raw)
            require_aggregate_bound(aggregate)
            live_blob_oid = git_object_oid("blob", raw)
            entry = git_tree_entry(git_path, environment, head, spec.path)
            git_mode: str | None = None
            git_blob_oid: str | None = None
            binding_state = "prospective_not_in_head"
            if entry is not None:
                git_mode, git_blob_oid = entry
                committed = verified_git_object(
                    git_path,
                    environment,
                    "blob",
                    git_blob_oid,
                    LIMIT_CLASS_BYTES[spec.limit_class],
                )
                if (
                    git_mode == spec.git_mode
                    and git_blob_oid == live_blob_oid
                    and committed == raw
                ):
                    binding_state = "bound_to_head"
                else:
                    binding_state = "worktree_differs_from_head"
            if require_committed:
                require(
                    binding_state == "bound_to_head",
                    f"authority is not bound to the candidate tree: {spec.path}",
                )
            result.append(
                {
                    "binding_state": binding_state,
                    "git_blob_oid": git_blob_oid,
                    "git_mode": git_mode,
                    "limit_class": spec.limit_class,
                    "live_blob_oid": live_blob_oid,
                    "live_mode": f"{spec.live_mode:04o}",
                    "path": spec.path,
                    "role": spec.role,
                    "sha256": sha256(raw),
                    "size_bytes": len(raw),
                }
            )
    finally:
        recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)
    return result


def parse_timestamp(value: Any, label: str) -> datetime:
    require(
        type(value) is str and UTC_TIMESTAMP_RE.fullmatch(value) is not None,
        f"{label} timestamp changed",
    )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise CaptureError(f"{label} timestamp changed") from None
    require(parsed.utcoffset() is not None, f"{label} timestamp is not UTC-aware")
    return parsed


def validate_authority_roster(authorities: Any) -> None:
    require(
        type(authorities) is list
        and [item.get("path") for item in authorities]
        == [spec.path for spec in AUTHORITY_SPECS]
        and all(
            type(item) is dict
            and set(item)
            == {
                "binding_state",
                "git_blob_oid",
                "git_mode",
                "limit_class",
                "live_blob_oid",
                "live_mode",
                "path",
                "role",
                "sha256",
                "size_bytes",
            }
            and item["binding_state"] == "bound_to_head"
            and item["role"] == AUTHORITY_BY_PATH[item["path"]].role
            and item["git_mode"] == AUTHORITY_BY_PATH[item["path"]].git_mode
            and item["live_mode"] == f"{AUTHORITY_BY_PATH[item['path']].live_mode:04o}"
            and item["limit_class"] == AUTHORITY_BY_PATH[item["path"]].limit_class
            and item["git_blob_oid"] == item["live_blob_oid"]
            and type(item["git_blob_oid"]) is str
            and SHA1_RE.fullmatch(item["git_blob_oid"]) is not None
            and type(item["sha256"]) is str
            and SHA256_RE.fullmatch(item["sha256"]) is not None
            and type(item["size_bytes"]) is int
            and 0 < item["size_bytes"] <= LIMIT_CLASS_BYTES[item["limit_class"]]
            for item in authorities
        )
        and sum(item["size_bytes"] for item in authorities)
        <= MAX_AUTHORITY_AGGREGATE_BYTES,
        "local closure authority inventory changed",
    )
    require(
        [spec.path for spec in AUTHORITY_SPECS if spec.limit_class != "ordinary_2mib"]
        == [TERMINAL_C9_CAPTURE_RELATIVE]
        and AUTHORITY_BY_PATH[TERMINAL_C9_CAPTURE_RELATIVE].limit_class
        == "terminal_c9_capture_4mib"
        and all(
            spec.limit_class == "ordinary_2mib"
            for spec in AUTHORITY_SPECS
            if spec.path != TERMINAL_C9_CAPTURE_RELATIVE
        ),
        "special authority class escaped its exact path",
    )


def validate_record_value(value: Any) -> None:
    require(
        type(value) is dict
        and set(value)
        == {
            "authorities",
            "immutable_v8_primitives",
            "invocation",
            "limits",
            "nonimplications",
            "platform",
            "repository",
            "repository_state",
            "reviewed_executables",
            "schema",
            "schema_revision",
            "subject",
        }
        and value["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v11"
        and value["schema_revision"] == 11
        and value["repository"] == REPOSITORY
        and value["limits"] == LIMITS
        and value["nonimplications"] == NONIMPLICATIONS
        and value["immutable_v8_primitives"]
        == {"path": V8_RELATIVE, "sha256": V8_SHA256, "size_bytes": V8_SIZE_BYTES},
        "local closure root identity changed",
    )
    subject = value["subject"]
    require(
        type(subject) is dict
        and set(subject) == {"c9_parent", "c11_commit", "c11_message", "c11_tree"}
        and subject["c9_parent"] == C9_COMMIT
        and type(subject["c11_commit"]) is str
        and SHA1_RE.fullmatch(subject["c11_commit"]) is not None
        and subject["c11_message"] == C11_MESSAGE
        and type(subject["c11_tree"]) is str
        and SHA1_RE.fullmatch(subject["c11_tree"]) is not None,
        "local closure subject changed",
    )
    validate_authority_roster(value["authorities"])
    state = value["repository_state"]
    require(
        type(state) is dict and set(state) == {"after", "before"},
        "repository state pair changed",
    )
    for label in ("before", "after"):
        PRIMITIVES.validate_snapshot_value(
            state[label], subject["c11_commit"], subject["c11_tree"], label
        )
    require(
        {key: state["before"][key] for key in state["before"] if key != "observed_at"}
        == {key: state["after"][key] for key in state["after"] if key != "observed_at"},
        "repository endpoint changed during local closure",
    )
    invocation = value["invocation"]
    require(
        type(invocation) is dict
        and set(invocation)
        == {
            "argv",
            "cwd",
            "elapsed_monotonic_ns",
            "environment",
            "environment_routes_sha256",
            "exit_code",
            "finished_at",
            "monotonic_finish_ns",
            "monotonic_start_ns",
            "signal",
            "started_at",
            "stderr",
            "stdout",
            "timeout_seconds",
            "timed_out",
            "umask",
        }
        and invocation["argv"] == list(COMMAND_ARGV)
        and invocation["cwd"] == "<REPOSITORY_ROOT>"
        and invocation["environment"] == PRIMITIVES.NORMALIZED_ENVIRONMENT
        and type(invocation["environment_routes_sha256"]) is str
        and SHA256_RE.fullmatch(invocation["environment_routes_sha256"]) is not None
        and invocation["exit_code"] == 0
        and invocation["signal"] is None
        and invocation["timeout_seconds"] == COMMAND_TIMEOUT_SECONDS
        and invocation["timed_out"] is False
        and invocation["umask"] == "0077"
        and invocation["monotonic_start_ns"] == 0
        and type(invocation["monotonic_finish_ns"]) is int
        and invocation["monotonic_finish_ns"] > 0
        and invocation["elapsed_monotonic_ns"] == invocation["monotonic_finish_ns"],
        "local closure invocation changed",
    )
    stdout = PRIMITIVES.decode_binding(
        invocation["stdout"], "command stdout", MAX_COMMAND_STREAM_BYTES
    )
    stderr = PRIMITIVES.decode_binding(
        invocation["stderr"], "command stderr", MAX_COMMAND_STREAM_BYTES
    )
    require(stdout + stderr != b"", "local command retained no output")
    started = parse_timestamp(invocation["started_at"], "command start")
    finished = parse_timestamp(invocation["finished_at"], "command finish")
    before = parse_timestamp(state["before"]["observed_at"], "before observation")
    after = parse_timestamp(state["after"]["observed_at"], "after observation")
    require(
        before <= started <= finished <= after,
        "local closure wall-clock ordering changed",
    )
    platform_value = value["platform"]
    require(
        type(platform_value) is dict
        and set(platform_value)
        == {
            "architecture",
            "gil_enabled",
            "operating_system",
            "operating_system_release",
            "python_implementation",
            "python_version",
        }
        and platform_value["operating_system"] == "Darwin"
        and platform_value["architecture"] in {"arm64", "aarch64"}
        and platform_value["python_implementation"] == "CPython"
        and platform_value["python_version"] == "3.14.6"
        and platform_value["gil_enabled"] is True,
        "local closure platform changed",
    )
    PRIMITIVES.validate_toolchain_records(value["reviewed_executables"])
    require(
        "rg" in [record["name"] for record in value["reviewed_executables"]],
        "ripgrep is absent from reviewed executable roster",
    )


def emit_sized_output(size: int) -> tuple[str, ...]:
    return (
        Path(sys.executable).name,
        "-I",
        "-S",
        "-B",
        "-c",
        f"import sys; sys.stdout.buffer.write(b'x' * {size})",
    )


def expect_bound(size: int, bound: int, accepted: bool) -> None:
    executable = Path(sys.executable)
    try:
        code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(
            emit_sized_output(size), executable, dict(os.environ), ROOT, 30, bound
        )
    except CaptureError:
        require(not accepted, "bounded process unexpectedly rejected an accepted size")
        return
    require(
        accepted
        and code == 0
        and not timed_out
        and len(stdout) == size
        and stderr == b"",
        "bounded process unexpectedly accepted a rejected size",
    )


def expect_capture_error(operation: Any, label: str) -> None:
    try:
        operation()
    except (CaptureError, OSError, subprocess.SubprocessError):
        return
    raise CaptureError(f"{label} was accepted")


def authority_spec_invariants() -> None:
    paths = [spec.path for spec in AUTHORITY_SPECS]
    roles = [spec.role for spec in AUTHORITY_SPECS]
    require(
        paths == sorted(paths)
        and len(paths) == len(set(paths))
        and len(roles) == len(set(roles))
        and set(AUTHORITY_BY_PATH) == set(paths),
        "authority specification paths or roles overlap",
    )
    require(
        set(LIMIT_CLASS_BYTES) == {"ordinary_2mib", "terminal_c9_capture_4mib"}
        and LIMIT_CLASS_BYTES["ordinary_2mib"] == 2 * 1024 * 1024
        and LIMIT_CLASS_BYTES["terminal_c9_capture_4mib"] == 4 * 1024 * 1024
        and MAX_AUTHORITY_AGGREGATE_BYTES == 16 * 1024 * 1024,
        "authority limit constants drifted",
    )
    special = [
        spec.path
        for spec in AUTHORITY_SPECS
        if spec.limit_class == "terminal_c9_capture_4mib"
    ]
    require(
        special == [TERMINAL_C9_CAPTURE_RELATIVE]
        and AUTHORITY_BY_PATH[TERMINAL_C9_CAPTURE_RELATIVE].authoring_required is False
        and all(
            spec.limit_class == "ordinary_2mib"
            for spec in AUTHORITY_SPECS
            if spec.path != TERMINAL_C9_CAPTURE_RELATIVE
        ),
        "4 MiB exception is not confined to the named terminal C9 capture",
    )
    require(
        AUTHORITY_BY_PATH[CURRENT_SOURCE_CHECKER_RELATIVE].git_mode == "100755"
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_CHECKER_RELATIVE].live_mode == 0o755
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_SELF_TEST_RELATIVE].git_mode == "100755"
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_SELF_TEST_RELATIVE].live_mode == 0o755,
        "current-source executable authority modes drifted",
    )


def write_fixture(root: Path, spec: AuthoritySpec, raw: bytes, mode: int) -> Path:
    destination = root / spec.path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    destination.chmod(mode)
    return destination


def stable_read_self_test() -> int:
    hostiles = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-v11-authority-read-") as raw:
        fixture = Path(raw).resolve(strict=True)
        ordinary_spec = AuthoritySpec(
            "ordinary.bin", "ordinary_fixture", "100644", 0o644, "ordinary_2mib"
        )
        special_spec = AuthoritySpec(
            TERMINAL_C9_CAPTURE_RELATIVE,
            "terminal_c9_hosted_capture",
            "100644",
            0o644,
            "terminal_c9_capture_4mib",
            False,
        )
        ordinary_raw = b"A" * MAX_ORDINARY_AUTHORITY_BYTES
        special_raw = b"B" * (MAX_ORDINARY_AUTHORITY_BYTES + 1)
        ordinary_path = write_fixture(fixture, ordinary_spec, ordinary_raw, 0o644)
        special_path = write_fixture(fixture, special_spec, special_raw, 0o644)
        root_fd = os.open(fixture, directory_flags())
        try:
            require(
                stable_authority_read(root_fd, ordinary_spec) == ordinary_raw,
                "ordinary exact-bound positive failed",
            )
            require(
                stable_authority_read(root_fd, special_spec) == special_raw,
                "named special-class positive failed",
            )

            ordinary_path.write_bytes(ordinary_raw + b"X")
            ordinary_path.chmod(0o644)
            expect_capture_error(
                lambda: stable_authority_read(root_fd, ordinary_spec),
                "ordinary max-plus-one authority",
            )
            hostiles += 1
            ordinary_path.write_bytes(b"A")
            ordinary_path.chmod(0o600)
            expect_capture_error(
                lambda: stable_authority_read(root_fd, ordinary_spec),
                "wrong live mode authority",
            )
            hostiles += 1
            ordinary_path.chmod(0o644)

            link_target = fixture / "link-target.bin"
            link_target.write_bytes(b"A")
            link_target.chmod(0o644)
            ordinary_path.unlink()
            ordinary_path.symlink_to(link_target.name)
            expect_capture_error(
                lambda: stable_authority_read(root_fd, ordinary_spec),
                "symbolic-link authority",
            )
            hostiles += 1
            ordinary_path.unlink()
            ordinary_path.write_bytes(b"A")
            ordinary_path.chmod(0o644)

            hardlink = fixture / "hardlink.bin"
            os.link(ordinary_path, hardlink)
            expect_capture_error(
                lambda: stable_authority_read(root_fd, ordinary_spec),
                "multiply linked authority",
            )
            hostiles += 1
            hardlink.unlink()

            ancestor_target = fixture / "ancestor-target"
            ancestor_target.mkdir()
            (ancestor_target / "leaf.bin").write_bytes(b"A")
            (ancestor_target / "leaf.bin").chmod(0o644)
            (fixture / "linked").symlink_to(ancestor_target, target_is_directory=True)
            linked_spec = AuthoritySpec(
                "linked/leaf.bin",
                "linked_ancestor_fixture",
                "100644",
                0o644,
                "ordinary_2mib",
            )
            expect_capture_error(
                lambda: stable_authority_read(root_fd, linked_spec),
                "symbolic-link authority ancestor",
            )
            hostiles += 1

            special_path.write_bytes(b"B" * (MAX_TERMINAL_C9_CAPTURE_BYTES + 1))
            special_path.chmod(0o644)
            expect_capture_error(
                lambda: stable_authority_read(root_fd, special_spec),
                "special max-plus-one authority",
            )
            hostiles += 1
        finally:
            os.close(root_fd)

        routed = fixture.parent / (fixture.name + "-route")
        routed.symlink_to(fixture, target_is_directory=True)
        try:
            os.open(routed, directory_flags())
        except OSError:
            hostiles += 1
        else:
            raise CaptureError("symbolic-link repository root was accepted")
        finally:
            routed.unlink()

    expect_capture_error(
        lambda: require_aggregate_bound(MAX_AUTHORITY_AGGREGATE_BYTES + 1),
        "aggregate max-plus-one",
    )
    hostiles += 1
    require_aggregate_bound(MAX_AUTHORITY_AGGREGATE_BYTES)
    require(
        git_object_oid("blob", b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
        and git_object_oid("tree", b"") == "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
        "Python Git object hashing drifted",
    )
    return hostiles


def preflight_live() -> dict[str, Any]:
    authority_spec_invariants()
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-c11-live-preflight-",
        dir="/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
    ) as temporary_text:
        temporary_root = Path(temporary_text)
        directories = PRIMITIVES.fixed_path_directories()
        environment, _route_digest = PRIMITIVES.minimal_environment(
            directories, temporary_root
        )
        git_path = PRIMITIVES.resolve_executable("git", directories)
        _code, head_raw = git_output(
            git_path,
            environment,
            MAX_VERSION_STREAM_BYTES,
            "rev-parse",
            "--verify",
            "HEAD",
        )
        try:
            head = head_raw.decode("ascii", errors="strict").removesuffix("\n")
        except UnicodeError:
            raise CaptureError("live HEAD is not ASCII") from None
        require(SHA1_RE.fullmatch(head) is not None, "live HEAD identity changed")
        tree = verify_commit_tree_objects(git_path, environment, head)
        authorities = inspect_authorities(
            git_path, environment, head, require_committed=False
        )
    pending = [
        item["path"]
        for item in authorities
        if item["binding_state"] == "pending_evidence_absent"
    ]
    require(
        pending in ([], [TERMINAL_C9_CAPTURE_RELATIVE]),
        "unexpected pending production authority",
    )
    states: dict[str, int] = {}
    for item in authorities:
        state = item["binding_state"]
        states[state] = states.get(state, 0) + 1
    aggregate = sum(
        item["size_bytes"] for item in authorities if item["size_bytes"] is not None
    )
    require_aggregate_bound(aggregate)
    return {
        "aggregate_bytes_observed": aggregate,
        "authority_count": len(AUTHORITY_SPECS),
        "capture_ready": states.get("bound_to_head", 0) == len(AUTHORITY_SPECS),
        "git_commit_object_verified": True,
        "git_tree": tree,
        "git_tree_object_verified": True,
        "head": head,
        "limit_classes": LIMIT_CLASS_BYTES,
        "pending_evidence_paths": pending,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-live-preflight/v1",
        "state_counts": dict(sorted(states.items())),
    }


def offline_self_test() -> dict[str, Any]:
    require(
        V8_SELF_TEST_BASELINE.get("result") == "pass",
        "immutable v8 local primitive self-test failed",
    )
    authority_spec_invariants()
    expect_bound(MAX_VERSION_STREAM_BYTES, MAX_VERSION_STREAM_BYTES, True)
    expect_bound(MAX_VERSION_STREAM_BYTES + 1, MAX_VERSION_STREAM_BYTES, False)
    expect_bound(MAX_VERSION_STREAM_BYTES + 1, MAX_ORDINARY_AUTHORITY_BYTES, True)
    expect_bound(MAX_ORDINARY_AUTHORITY_BYTES, MAX_ORDINARY_AUTHORITY_BYTES, True)
    expect_bound(
        MAX_ORDINARY_AUTHORITY_BYTES + 1,
        MAX_ORDINARY_AUTHORITY_BYTES,
        False,
    )
    hostiles = stable_read_self_test()
    return {
        "authority_specifications_verified": len(AUTHORITY_SPECS),
        "git_object_hash_positive_controls": 2,
        "immutable_v8_local_self_test": "pass",
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-local-capture-self-test/v1",
        "special_limit_paths": [TERMINAL_C9_CAPTURE_RELATIVE],
        "stable_read_and_limit_hostiles_rejected": hostiles,
        "synthetic_authority_bound_acceptances": 2,
        "synthetic_authority_bound_rejections": 1,
        "version_bound_acceptances": 1,
        "version_bound_rejections": 1,
    }


def capture_under_fixed_umask(output_path: str) -> None:
    PRIMITIVES.reject_ambient_secrets(dict(os.environ))
    require(
        platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"}
        and platform.python_implementation() == "CPython"
        and platform.python_version() == "3.14.6"
        and sys._is_gil_enabled(),
        "local closure capture requires the reviewed Darwin arm64 GIL-enabled CPython 3.14.6 lane",
    )
    descriptor_fd = -1
    destination: Path | None = None
    created_device_inode: tuple[int, int] | None = None
    rendered = b""
    try:
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-c11-local-closure-",
            dir="/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
        ) as temporary_text:
            temporary_root = Path(temporary_text)
            directories = PRIMITIVES.fixed_path_directories()
            environment, route_digest = PRIMITIVES.minimal_environment(
                directories, temporary_root
            )
            private_prefixes = tuple(
                prefix
                for prefix in {
                    os.fsencode(ROOT.resolve()),
                    os.fsencode(Path(pwd.getpwuid(os.getuid()).pw_dir).resolve()),
                    os.fsencode(temporary_root.resolve()),
                    os.fsencode(temporary_root.parent.resolve()),
                    os.fsencode(Path(tempfile.gettempdir()).resolve()),
                }
                if prefix
            )
            toolchain, executables = PRIMITIVES.toolchain_observation(
                directories, environment, private_prefixes
            )
            before_state = PRIMITIVES.repository_snapshot(
                executables["git"], environment
            )
            verified_tree = verify_commit_tree_objects(
                executables["git"], environment, before_state["head"]
            )
            require(
                verified_tree == before_state["tree"],
                "snapshot tree differs from verified Git object",
            )
            authorities = inspect_authorities(
                executables["git"],
                environment,
                before_state["head"],
                require_committed=True,
            )
            validate_authority_roster(authorities)
            started_at = utc_now()
            monotonic_start = time.monotonic_ns()
            code, stdout, stderr, timed_out = PRIMITIVES.run_bounded(
                COMMAND_ARGV,
                executables["just"],
                environment,
                ROOT,
                COMMAND_TIMEOUT_SECONDS,
                MAX_COMMAND_STREAM_BYTES,
            )
            monotonic_end = time.monotonic_ns()
            finished_at = utc_now()
            require(
                not timed_out and code == 0,
                "local closure command did not complete successfully",
            )
            PRIMITIVES.reject_sensitive_output(
                stdout, private_prefixes, "local command stdout"
            )
            PRIMITIVES.reject_sensitive_output(
                stderr, private_prefixes, "local command stderr"
            )
            require(stdout + stderr != b"", "local closure command retained no output")
            after_authorities = inspect_authorities(
                executables["git"],
                environment,
                before_state["head"],
                require_committed=True,
            )
            require(
                after_authorities == authorities,
                "authority roster changed during local closure",
            )
            after_state = PRIMITIVES.repository_snapshot(
                executables["git"], environment
            )
            require(
                {key: before_state[key] for key in before_state if key != "observed_at"}
                == {
                    key: after_state[key] for key in after_state if key != "observed_at"
                },
                "repository endpoint changed during local closure",
            )
            elapsed = monotonic_end - monotonic_start
            require(elapsed > 0, "monotonic command interval changed")
            value = {
                "authorities": authorities,
                "immutable_v8_primitives": {
                    "path": V8_RELATIVE,
                    "sha256": V8_SHA256,
                    "size_bytes": V8_SIZE_BYTES,
                },
                "invocation": {
                    "argv": list(COMMAND_ARGV),
                    "cwd": "<REPOSITORY_ROOT>",
                    "elapsed_monotonic_ns": elapsed,
                    "environment": PRIMITIVES.NORMALIZED_ENVIRONMENT,
                    "environment_routes_sha256": route_digest,
                    "exit_code": 0,
                    "finished_at": finished_at,
                    "monotonic_finish_ns": elapsed,
                    "monotonic_start_ns": 0,
                    "signal": None,
                    "started_at": started_at,
                    "stderr": byte_binding(stderr),
                    "stdout": byte_binding(stdout),
                    "timeout_seconds": COMMAND_TIMEOUT_SECONDS,
                    "timed_out": False,
                    "umask": "0077",
                },
                "limits": LIMITS,
                "nonimplications": NONIMPLICATIONS,
                "platform": {
                    "architecture": platform.machine(),
                    "gil_enabled": sys._is_gil_enabled(),
                    "operating_system": platform.system(),
                    "operating_system_release": platform.release(),
                    "python_implementation": platform.python_implementation(),
                    "python_version": platform.python_version(),
                },
                "repository": REPOSITORY,
                "repository_state": {"after": after_state, "before": before_state},
                "reviewed_executables": toolchain,
                "schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v11",
                "schema_revision": 11,
                "subject": {
                    "c9_parent": C9_COMMIT,
                    "c11_commit": before_state["head"],
                    "c11_message": C11_MESSAGE,
                    "c11_tree": before_state["tree"],
                },
            }
            validate_record_value(value)
            rendered = canonical_json(value)
            require(
                0 < len(rendered) <= MAX_RECORD_BYTES,
                "local closure record exceeds bound",
            )
        descriptor_fd, destination = PRIMITIVES.create_output(output_path)
        created = os.fstat(descriptor_fd)
        created_device_inode = (created.st_dev, created.st_ino)
        PRIMITIVES.validate_output_descriptor(descriptor_fd)
        written = 0
        while written < len(rendered):
            count = os.write(descriptor_fd, rendered[written:])
            require(count > 0, "local closure output write made no progress")
            written += count
        os.fsync(descriptor_fd)
        PRIMITIVES.validate_output_descriptor(descriptor_fd)
        os.close(descriptor_fd)
        descriptor_fd = -1
        require(destination is not None, "output destination disappeared")
        metadata = destination.lstat()
        require(
            metadata.st_size == len(rendered)
            and stat.S_IMODE(metadata.st_mode) == 0o600
            and destination.read_bytes() == rendered,
            "installed local closure bytes changed",
        )
    except Exception:
        if descriptor_fd >= 0:
            os.close(descriptor_fd)
        if destination is not None and created_device_inode is not None:
            try:
                observed = destination.lstat()
                if (observed.st_dev, observed.st_ino) == created_device_inode:
                    destination.unlink()
            except (FileNotFoundError, OSError):
                pass
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--preflight-live", action="store_true")
    modes.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.self_test:
            sys.stdout.buffer.write(canonical_json(offline_self_test()))
        elif arguments.preflight_live:
            sys.stdout.buffer.write(canonical_json(preflight_live()))
        else:
            require(type(arguments.output) is str, "output path is required")
            PRIMITIVES.under_fixed_umask(
                lambda: capture_under_fixed_umask(arguments.output)
            )
        return 0
    except (CaptureError, OSError, subprocess.SubprocessError):
        print("ERROR: bounded local closure capture failed closed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
