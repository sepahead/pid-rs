#!/usr/bin/env python3
"""Capture one bounded, fail-closed local composite-v9 closure observation.

The fixed command is ``just ksg-composite-v9``. Version and small metadata
probes retain a 65,536-byte stream bound; exact authority-blob reads use a
separate 2 MiB bound. The tool accepts no caller-selected command and writes
canonical JSON only to a new mode-0600 path outside the repository.
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
        "ERROR: capture-ksg-m1a-composite-v9-local-closure.py requires GIL-enabled CPython 3.14.6 -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
import base64
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
C8_COMMIT = "7c80d48db415279fc4d744eadb1515797606912b"
C9_MESSAGE = "Repair KSG M1a composite v9 contract\n"
V8_RELATIVE = "scripts/capture-ksg-m1a-composite-v8-local-closure.py"
V8_PATH = ROOT / V8_RELATIVE
V8_SHA256 = "b9b0a41cb2027d1cba464040843656bc2486e317f8cf1d3079cb58b02f7c6ba7"
V8_SIZE_BYTES = 40_584
SCRIPT_RELATIVE = "scripts/capture-ksg-m1a-composite-v9-local-closure.py"
SCHEMA_RELATIVE = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v9.schema.json"
CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v9.py"
SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v9-self-test.py"
ACTION_PIN_CHECKER_RELATIVE = "scripts/check-github-action-pins.py"
ACTION_PIN_SELF_TEST_RELATIVE = "scripts/check-github-action-pins-self-test.py"
JUSTFILE_RELATIVE = "justfile"
SCRIPT_README_RELATIVE = "scripts/README.md"
FORMAL_PDF_SET_RELATIVE = "scripts/check-formal-pdf-set.sh"
WORKFLOW_PDF_GATE_RELATIVE = "scripts/check-mathematical-workflow-pdf.sh"
WORKFLOW_PDF_SELF_TEST_RELATIVE = "scripts/check-mathematical-workflow-pdf-self-test.sh"
V8_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v8.py"
V8_SELF_TEST_RELATIVE = "scripts/check-ksg-m1a-composite-v8-self-test.py"
COMMAND_ARGV = ("just", "ksg-composite-v9")
COMMAND_TIMEOUT_SECONDS = 14_400
MAX_VERSION_STREAM_BYTES = 64 * 1024
MAX_AUTHORITY_STREAM_BYTES = 2 * 1024 * 1024
MAX_COMMAND_STREAM_BYTES = 8 * 1024 * 1024
MAX_RECORD_BYTES = 32 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UTC_TIMESTAMP_RE = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z$"
)
LIMITS = {
    "authority_stream_bytes": MAX_AUTHORITY_STREAM_BYTES,
    "command_stream_bytes": MAX_COMMAND_STREAM_BYTES,
    "executable_bytes": MAX_EXECUTABLE_BYTES,
    "record_bytes": MAX_RECORD_BYTES,
    "version_stream_bytes": MAX_VERSION_STREAM_BYTES,
}
AUTHORITY_ROLES = {
    ACTION_PIN_CHECKER_RELATIVE: "github_action_pin_semantic_gate",
    ACTION_PIN_SELF_TEST_RELATIVE: "github_action_pin_hostile_suite",
    JUSTFILE_RELATIVE: "local_command_wiring",
    SCHEMA_RELATIVE: "local_l9_closure_schema",
    SCRIPT_RELATIVE: "bounded_local_l9_closure_capture_tool",
    SELF_TEST_RELATIVE: "composite_v9_hostile_suite",
    CHECKER_RELATIVE: "composite_v9_semantic_gate",
    FORMAL_PDF_SET_RELATIVE: "formal_pdf_aggregate_gate",
    SCRIPT_README_RELATIVE: "workflow_pdf_process_boundary",
    WORKFLOW_PDF_GATE_RELATIVE: "workflow_pdf_portability_gate",
    WORKFLOW_PDF_SELF_TEST_RELATIVE: (
        "workflow_pdf_portability_hostile_suite_fixture_mode_correction"
    ),
    V8_SELF_TEST_RELATIVE: "retained_v8_hostile_suite_authority",
    V8_CHECKER_RELATIVE: "retained_v8_semantic_gate_authority",
}
AUTHORITY_MODES = {
    path: (
        0o755
        if path
        in {
            FORMAL_PDF_SET_RELATIVE,
            WORKFLOW_PDF_GATE_RELATIVE,
            WORKFLOW_PDF_SELF_TEST_RELATIVE,
        }
        else 0o644
    )
    for path in AUTHORITY_ROLES
}
EXPECTED_OVERSIZED_AUTHORITY_PATHS = sorted(
    {
        CHECKER_RELATIVE,
        SCRIPT_README_RELATIVE,
        SELF_TEST_RELATIVE,
        V8_CHECKER_RELATIVE,
        WORKFLOW_PDF_GATE_RELATIVE,
        WORKFLOW_PDF_SELF_TEST_RELATIVE,
    }
)
NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C9 checkout and is neither independent replication nor first-attempt authority.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, builtins, libraries, TeX helpers, or transitive processes.",
    "The authority-stream class accommodates the exact named large authorities; it is not a generic executable-closure or hermeticity theorem.",
    "The redacted environment-route digest is an opaque correlated fingerprint, not a publicly recomputable path authority.",
    "HOME is absent; isolated XDG and TeX roots do not prove absence of every passwd-derived fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove every descendant was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove output contains no sensitive information.",
    "Ordinary Git status plus selected metadata checks exclude ignored products and uninspected Git metadata, so this is not hermetic closure.",
    "A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
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
        "immutable v8 local-recorder self-test failed before the v9 rebind",
    )
except Exception:
    print(
        "ERROR: immutable-v8 local-recorder self-test failed before v9 rebind",
        file=sys.stderr,
    )
    raise SystemExit(2) from None


CaptureError = V8.CaptureError
require = V8.require
sha256 = V8.sha256
canonical_json = V8.canonical_json
PRIMITIVES = V8.PRIMITIVES

# Reuse exact routing, process, executable, and repository primitives with the
# v9 subject. The record construction and authority-bound selection stay local
# to this module and are not monkey-patched into the immutable source bytes.
PRIMITIVES.C5_COMMIT = C8_COMMIT
PRIMITIVES.C6_MESSAGE = C9_MESSAGE
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


def descriptor(path: str, role: str, raw: bytes) -> dict[str, Any]:
    return {"path": path, "role": role, "sha256": sha256(raw), "size_bytes": len(raw)}


def run_internal(
    executable: Path,
    argv: tuple[str, ...],
    environment: dict[str, str],
    maximum_stream_bytes: int,
    *,
    allowed_exit_codes: frozenset[int] = frozenset({0}),
) -> tuple[int, bytes, bytes]:
    require(
        maximum_stream_bytes in {MAX_VERSION_STREAM_BYTES, MAX_AUTHORITY_STREAM_BYTES},
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


def git_authority_output(
    git_path: Path, environment: dict[str, str], head: str, relative: str
) -> bytes:
    _code, stdout, stderr = run_internal(
        git_path,
        ("git", "show", f"{head}:{relative}"),
        environment,
        MAX_AUTHORITY_STREAM_BYTES,
    )
    require(stderr == b"", "isolated Git authority read wrote stderr")
    return stdout


def authority_descriptors(
    git_path: Path, environment: dict[str, str], head: str
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for relative, role in sorted(AUTHORITY_ROLES.items()):
        raw = PRIMITIVES.read_regular(
            ROOT / relative, MAX_AUTHORITY_STREAM_BYTES, AUTHORITY_MODES[relative]
        )
        committed = git_authority_output(git_path, environment, head, relative)
        require(raw == committed, "local authority differs from the C9 tree")
        result.append(descriptor(relative, role, raw))
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
        and [item.get("path") for item in authorities] == sorted(AUTHORITY_ROLES)
        and all(
            type(item) is dict
            and set(item) == {"path", "role", "sha256", "size_bytes"}
            and item["role"] == AUTHORITY_ROLES[item["path"]]
            and type(item["sha256"]) is str
            and SHA256_RE.fullmatch(item["sha256"]) is not None
            and type(item["size_bytes"]) is int
            and 0 < item["size_bytes"] <= MAX_AUTHORITY_STREAM_BYTES
            for item in authorities
        ),
        "local closure authority inventory changed",
    )
    oversized = [
        item["path"]
        for item in authorities
        if item["size_bytes"] > MAX_VERSION_STREAM_BYTES
    ]
    require(
        oversized == EXPECTED_OVERSIZED_AUTHORITY_PATHS,
        "local closure named-oversize authority inventory changed",
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
        and value["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v5"
        and value["schema_revision"] == 5
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
        and set(subject) == {"c8_parent", "c9_commit", "c9_message", "c9_tree"}
        and subject["c8_parent"] == C8_COMMIT
        and type(subject["c9_commit"]) is str
        and SHA1_RE.fullmatch(subject["c9_commit"]) is not None
        and subject["c9_message"] == C9_MESSAGE
        and type(subject["c9_tree"]) is str
        and SHA1_RE.fullmatch(subject["c9_tree"]) is not None,
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
            state[label], subject["c9_commit"], subject["c9_tree"], label
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


def authority_roster_self_test() -> int:
    baseline = [
        {
            "path": path,
            "role": role,
            "sha256": "0" * 64,
            "size_bytes": (
                MAX_VERSION_STREAM_BYTES + 1
                if path in EXPECTED_OVERSIZED_AUTHORITY_PATHS
                else 1
            ),
        }
        for path, role in sorted(AUTHORITY_ROLES.items())
    ]
    validate_authority_roster(baseline)
    hostiles = 0
    for omitted in sorted(AUTHORITY_ROLES):
        without_authority = [item for item in baseline if item["path"] != omitted]
        expect_capture_error(
            lambda value=without_authority: validate_authority_roster(value),
            f"omitted named authority: {omitted}",
        )
        hostiles += 1
    role_drift = [dict(item) for item in baseline]
    for item in role_drift:
        if item["path"] == ACTION_PIN_SELF_TEST_RELATIVE:
            item["role"] = "generic_hostile_suite"
    expect_capture_error(
        lambda: validate_authority_roster(role_drift),
        "action-pin authority role drift",
    )
    hostiles += 1
    pdf_role_drift = [dict(item) for item in baseline]
    for item in pdf_role_drift:
        if item["path"] == WORKFLOW_PDF_GATE_RELATIVE:
            item["role"] = "generic_pdf_gate"
    expect_capture_error(
        lambda: validate_authority_roster(pdf_role_drift),
        "workflow-PDF authority role drift",
    )
    hostiles += 1
    unreviewed_oversize = [dict(item) for item in baseline]
    for item in unreviewed_oversize:
        if item["path"] == ACTION_PIN_CHECKER_RELATIVE:
            item["size_bytes"] = MAX_VERSION_STREAM_BYTES + 1
    expect_capture_error(
        lambda: validate_authority_roster(unreviewed_oversize),
        "unreviewed oversized authority",
    )
    hostiles += 1
    for relative in EXPECTED_OVERSIZED_AUTHORITY_PATHS:
        missing_named_oversize = [dict(item) for item in baseline]
        for item in missing_named_oversize:
            if item["path"] == relative:
                item["size_bytes"] = MAX_VERSION_STREAM_BYTES
        expect_capture_error(
            lambda value=missing_named_oversize: validate_authority_roster(value),
            f"named authority no longer oversized: {relative}",
        )
        hostiles += 1
    return hostiles


def authority_route_self_test() -> dict[str, int]:
    global ROOT, AUTHORITY_MODES, AUTHORITY_ROLES

    original_root = ROOT
    original_modes = AUTHORITY_MODES
    original_roles = AUTHORITY_ROLES
    original_v8_root = PRIMITIVES.ROOT
    original_v8_runner = PRIMITIVES.run_bounded
    original_v8_version_bound = PRIMITIVES.MAX_VERSION_STREAM_BYTES
    hostiles = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-c9-authority-route-") as temp_text:
        temporary_root = Path(temp_text)
        repository_root = temporary_root / "repository"
        repository_root.mkdir(mode=0o700)
        directories = PRIMITIVES.fixed_path_directories()
        environment, _route_digest = PRIMITIVES.minimal_environment(
            directories, temporary_root
        )
        git_path = PRIMITIVES.resolve_executable("git", directories)

        def git_fixture(*arguments: str) -> bytes:
            code, stdout, stderr, timed_out = original_v8_runner(
                ("git", *arguments),
                git_path,
                environment,
                repository_root,
                30,
                MAX_VERSION_STREAM_BYTES,
            )
            require(
                code == 0 and stderr == b"" and not timed_out,
                "authority-route Git fixture setup failed",
            )
            return stdout

        git_fixture("init", "-q")
        authority_path = repository_root / "authority.bin"
        authority_raw = b"A" * (MAX_VERSION_STREAM_BYTES + 1)
        authority_path.write_bytes(authority_raw)
        authority_path.chmod(0o644)
        git_fixture("add", "--", "authority.bin")
        git_fixture(
            "-c",
            "user.name=pid-rs fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-q",
            "-m",
            "authority fixture",
        )
        head = git_fixture("rev-parse", "--verify", "HEAD").decode("ascii").strip()
        blob = git_fixture("rev-parse", f"{head}:authority.bin").decode("ascii").strip()

        ROOT = repository_root
        AUTHORITY_ROLES = {"authority.bin": "oversize_committed_authority_fixture"}
        AUTHORITY_MODES = {"authority.bin": 0o644}
        PRIMITIVES.ROOT = repository_root
        try:
            observed = authority_descriptors(git_path, environment, head)
            require(
                observed
                == [
                    {
                        "path": "authority.bin",
                        "role": "oversize_committed_authority_fixture",
                        "sha256": sha256(authority_raw),
                        "size_bytes": len(authority_raw),
                    }
                ],
                "dedicated authority route changed committed oversize bytes",
            )

            expect_capture_error(
                lambda: PRIMITIVES.git_output(
                    git_path, environment, "show", f"{head}:authority.bin"
                ),
                "generic v8 Git output accepted a 65,537-byte authority",
            )
            hostiles += 1

            authority_path.write_bytes(authority_raw[:-1])
            authority_path.chmod(0o644)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "truncated committed authority",
            )
            hostiles += 1
            authority_path.write_bytes(b"B" + authority_raw[1:])
            authority_path.chmod(0o644)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "mutated committed authority",
            )
            hostiles += 1
            authority_path.write_bytes(authority_raw)
            authority_path.chmod(0o644)

            authority_target = repository_root / "authority-target.bin"
            authority_path.rename(authority_target)
            authority_path.symlink_to(authority_target.name)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "symbolic-link authority",
            )
            hostiles += 1
            authority_path.unlink()
            authority_target.rename(authority_path)

            hardlink = repository_root / "authority-hardlink.bin"
            os.link(authority_path, hardlink)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "multiply linked authority",
            )
            hostiles += 1
            hardlink.unlink()

            authority_path.chmod(0o600)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "wrong-mode authority",
            )
            hostiles += 1
            authority_path.chmod(0o644)

            class DriftingPath(type(repository_root)):
                drifted = False

                def read_bytes(self) -> bytes:
                    raw = super().read_bytes()
                    if self.name == "authority.bin" and not type(self).drifted:
                        type(self).drifted = True
                        changed = raw[:-1]
                        super().write_bytes(changed)
                        return changed
                    return raw

            ROOT = DriftingPath(repository_root)
            expect_capture_error(
                lambda: authority_descriptors(git_path, environment, head),
                "authority changing during local read",
            )
            hostiles += 1
            require(DriftingPath.drifted, "mid-read drift fixture did not execute")
            ROOT = repository_root
            authority_path.write_bytes(authority_raw)
            authority_path.chmod(0o644)

            for label, hostile_head, hostile_path in (
                ("wrong authority ref", "0" * 40, "authority.bin"),
                ("wrong authority path", head, "absent.bin"),
                ("wrong authority object type", blob, "authority.bin"),
            ):
                expect_capture_error(
                    lambda hostile_head=hostile_head, hostile_path=hostile_path: (
                        git_authority_output(
                            git_path, environment, hostile_head, hostile_path
                        )
                    ),
                    label,
                )
                hostiles += 1

            nonzero_directory = temporary_root / "nonzero"
            nonzero_directory.mkdir(mode=0o700)
            nonzero_git = nonzero_directory / "git"
            nonzero_git.write_bytes(b"#!/bin/sh\nexit 7\n")
            nonzero_git.chmod(0o700)
            nonzero_result = original_v8_runner(
                ("git", "show", f"{head}:authority.bin"),
                nonzero_git,
                environment,
                repository_root,
                30,
                MAX_AUTHORITY_STREAM_BYTES,
            )
            require(
                nonzero_result == (7, b"", b"", False),
                "nonzero authority fixture did not reach its exit status",
            )
            expect_capture_error(
                lambda: git_authority_output(
                    nonzero_git, environment, head, "authority.bin"
                ),
                "nonzero authority reader",
            )
            hostiles += 1

            stderr_directory = temporary_root / "stderr"
            stderr_directory.mkdir(mode=0o700)
            stderr_git = stderr_directory / "git"
            stderr_git.write_bytes(
                b"#!/bin/sh\nprintf 'fixture'\nprintf 'fixture stderr\\n' >&2\n"
            )
            stderr_git.chmod(0o700)
            stderr_result = original_v8_runner(
                ("git", "show", f"{head}:authority.bin"),
                stderr_git,
                environment,
                repository_root,
                30,
                MAX_AUTHORITY_STREAM_BYTES,
            )
            require(
                stderr_result == (0, b"fixture", b"fixture stderr\n", False),
                "stderr authority fixture did not reach the stderr check",
            )
            expect_capture_error(
                lambda: git_authority_output(
                    stderr_git, environment, head, "authority.bin"
                ),
                "stderr-writing authority reader",
            )
            hostiles += 1

            def timed_out_runner(
                *_arguments: Any, **_keywords: Any
            ) -> tuple[int, bytes, bytes, bool]:
                return -9, b"", b"", True

            PRIMITIVES.run_bounded = timed_out_runner
            expect_capture_error(
                lambda: git_authority_output(
                    git_path, environment, head, "authority.bin"
                ),
                "timed-out authority reader",
            )
            hostiles += 1
        finally:
            PRIMITIVES.run_bounded = original_v8_runner
            PRIMITIVES.ROOT = original_v8_root
            ROOT = original_root
            AUTHORITY_MODES = original_modes
            AUTHORITY_ROLES = original_roles

    require(
        PRIMITIVES.MAX_VERSION_STREAM_BYTES
        == original_v8_version_bound
        == MAX_VERSION_STREAM_BYTES,
        "immutable v8 version bound was mutated",
    )
    return {"hostiles_rejected": hostiles, "oversize_committed_authorities_accepted": 1}


def offline_self_test() -> dict[str, Any]:
    require(
        V8_SELF_TEST_BASELINE.get("result") == "pass",
        "immutable v8 local primitive self-test failed",
    )
    require(
        set(AUTHORITY_MODES) == set(AUTHORITY_ROLES)
        and {path for path, mode in AUTHORITY_MODES.items() if mode == 0o755}
        == {
            FORMAL_PDF_SET_RELATIVE,
            WORKFLOW_PDF_GATE_RELATIVE,
            WORKFLOW_PDF_SELF_TEST_RELATIVE,
        }
        and all(mode in {0o644, 0o755} for mode in AUTHORITY_MODES.values()),
        "named local authority mode inventory changed",
    )
    expect_bound(MAX_VERSION_STREAM_BYTES, MAX_VERSION_STREAM_BYTES, True)
    expect_bound(MAX_VERSION_STREAM_BYTES + 1, MAX_VERSION_STREAM_BYTES, False)
    expect_bound(MAX_VERSION_STREAM_BYTES + 1, MAX_AUTHORITY_STREAM_BYTES, True)
    expect_bound(MAX_AUTHORITY_STREAM_BYTES, MAX_AUTHORITY_STREAM_BYTES, True)
    expect_bound(MAX_AUTHORITY_STREAM_BYTES + 1, MAX_AUTHORITY_STREAM_BYTES, False)
    for relative, expected_size, expected_sha, expected_oversize in (
        (
            V8_SELF_TEST_RELATIVE,
            28_968,
            "483713bf21d615953f8eb759afa9f80e859de0c6436d8903736e383b8b69ed1a",
            False,
        ),
        (
            V8_CHECKER_RELATIVE,
            124_760,
            "ed0404c2e3cd2c3f2bd9f8fa177649c26ca87f620280e2e6e4f5ac49c551d1df",
            True,
        ),
    ):
        raw = PRIMITIVES.read_regular(
            ROOT / relative, MAX_AUTHORITY_STREAM_BYTES, 0o644
        )
        require(
            len(raw) == expected_size
            and sha256(raw) == expected_sha
            and (len(raw) > MAX_VERSION_STREAM_BYTES) is expected_oversize,
            "retained oversized v8 authority changed",
        )
    live_authorities = [
        descriptor(
            relative,
            role,
            PRIMITIVES.read_regular(
                ROOT / relative, MAX_AUTHORITY_STREAM_BYTES, AUTHORITY_MODES[relative]
            ),
        )
        for relative, role in sorted(AUTHORITY_ROLES.items())
    ]
    validate_authority_roster(live_authorities)
    route = authority_route_self_test()
    validate_authority_roster(live_authorities)
    roster_hostiles = authority_roster_self_test()
    return {
        "authority_route_hostiles_rejected": route["hostiles_rejected"],
        "authority_route_oversize_committed_acceptances": route[
            "oversize_committed_authorities_accepted"
        ],
        "immutable_v8_local_self_test": "pass",
        "named_authority_roster_hostiles_rejected": roster_hostiles,
        "named_authority_modes_verified": len(AUTHORITY_MODES),
        "result": "pass",
        "retained_authorities_verified": 2,
        "retained_oversize_authorities_verified": 1,
        "schema": "pid-rs/ksg-rev4-m1a-composite-v9-local-closure-capture-self-test/v1",
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
    rendered = b""
    try:
        descriptor_fd, destination = PRIMITIVES.create_output(output_path)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-c9-local-closure-",
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
            authorities = authority_descriptors(
                executables["git"], environment, before_state["head"]
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
                "schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v5",
                "schema_revision": 5,
                "subject": {
                    "c8_parent": C8_COMMIT,
                    "c9_commit": before_state["head"],
                    "c9_message": C9_MESSAGE,
                    "c9_tree": before_state["tree"],
                },
            }
            validate_record_value(value)
            rendered = canonical_json(value)
            require(
                0 < len(rendered) <= MAX_RECORD_BYTES,
                "local closure record exceeds bound",
            )
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
        if destination is not None and (
            destination.exists() or destination.is_symlink()
        ):
            try:
                destination.unlink()
            except OSError:
                pass
        raise


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.self_test:
            sys.stdout.buffer.write(canonical_json(offline_self_test()))
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
