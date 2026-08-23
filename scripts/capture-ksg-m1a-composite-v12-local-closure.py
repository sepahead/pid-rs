#!/usr/bin/env python3
"""Preflight or capture one bounded local composite-v12 closure observation.

The production command is exactly ``just ksg-composite-v12``. Preflight reads
the real authority roster and Git objects but neither runs that command nor
writes evidence. The recorder checksum-binds and reuses the frozen v11 local
transport while this wrapper supplies the disjoint C12/L12 semantics.
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
    and sys.flags.optimize in {0, 1}
):
    print(
        "ERROR: capture-ksg-m1a-composite-v12-local-closure.py requires "
        "GIL-enabled CPython 3.14.6 -I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)

import argparse
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
C11_COMMIT = "91d954160a7e717ae46b6088175ae52e92570127"
C11_TREE = "97841c6eda10573ddc3537c9e3b2ca41a93a3fa1"
C12_MESSAGE = "Repair KSG M1a composite v12 contract\n"
V11_RELATIVE = "scripts/capture-ksg-m1a-composite-v11-local-closure.py"
V11_PATH = ROOT / V11_RELATIVE
V11_SHA256 = "e86afacbcc089d19d7e6b5e1e3415cfe2f1a6455f2645095d5bccf54016ceb6d"
V11_SIZE_BYTES = 53_843
COMMAND_ARGV = ("just", "ksg-composite-v12")
COMMAND_TIMEOUT_SECONDS = 14_400
MAX_VERSION_STREAM_BYTES = 64 * 1024
MAX_ORDINARY_AUTHORITY_BYTES = 2 * 1024 * 1024
MAX_AUTHORITY_AGGREGATE_BYTES = 16 * 1024 * 1024
MAX_COMMAND_STREAM_BYTES = 8 * 1024 * 1024
MAX_RECORD_BYTES = 32 * 1024 * 1024
MAX_EXECUTABLE_BYTES = 256 * 1024 * 1024
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LIMITS = {
    "authority_aggregate_bytes": MAX_AUTHORITY_AGGREGATE_BYTES,
    "command_stream_bytes": MAX_COMMAND_STREAM_BYTES,
    "executable_bytes": MAX_EXECUTABLE_BYTES,
    "ordinary_authority_bytes": MAX_ORDINARY_AUTHORITY_BYTES,
    "record_bytes": MAX_RECORD_BYTES,
    "version_stream_bytes": MAX_VERSION_STREAM_BYTES,
}
NONIMPLICATIONS = [
    "This unsigned local record is an unauthenticated operator-side observation; it has no signer or attestation authority.",
    "One local execution is correlated with the C12 checkout and is neither independent replication nor hosted first-attempt authority.",
    "The consumed failed L11, false Q11, and permanently unissued R11 grant no L12 or C12 qualification credit.",
    "Wall-clock and monotonic ordering plus clean pre/post observations are not trusted time or an atomic worktree snapshot.",
    "Executable hashes, version output, and captured command output do not prove which bytes the operating system executed or exclude interference.",
    "The reviewed executable roster is a bounded named subset, not a complete inventory of scripts, builtins, libraries, TeX helpers, or transitive processes.",
    "Every authority is capped at 2 MiB and the complete roster at 16 MiB; a nearby path or role receives no larger implicit class.",
    "The redacted environment-route digest is an opaque correlated fingerprint, not a publicly recomputable path authority.",
    "HOME is absent; isolated XDG and TeX roots do not prove absence of every passwd-derived fallback.",
    "The bounded pipe-drain rule rejects an escaped descriptor holder but does not prove every descendant was identified or terminated.",
    "The bounded secret and private-path scan can reject named patterns but cannot prove output contains no sensitive information.",
    "Ordinary Git status plus selected metadata checks exclude ignored products and uninspected Git metadata, so this is not hermetic closure.",
    "A local closure pass is not PID, KSG, mathematical, scientific, security, privacy, accessibility, application, or cross-platform evidence.",
]


class BootstrapError(RuntimeError):
    """The exact frozen v11 local transport could not be loaded."""


def bootstrap_require(predicate: bool, message: str) -> None:
    if not predicate:
        raise BootstrapError(message)


def read_bound_v11(path: Path = V11_PATH) -> bytes:
    before = path.lstat()
    bootstrap_require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and before.st_size == V11_SIZE_BYTES,
        "frozen v11 local primitive metadata changed",
    )
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
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
            "opened frozen v11 local primitive identity changed",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            bootstrap_require(chunk != b"", "short frozen v11 local primitive read")
            chunks.append(chunk)
            remaining -= len(chunk)
        bootstrap_require(
            os.read(descriptor, 1) == b"", "frozen v11 local primitive grew"
        )
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
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
            "frozen v11 local primitive changed while read",
        )
    raw = b"".join(chunks)
    bootstrap_require(
        hashlib.sha256(raw).hexdigest() == V11_SHA256,
        "frozen v11 local primitive digest changed",
    )
    return raw


def load_bound_v11(raw: bytes) -> types.ModuleType:
    module_name = "pid_rs_capture_ksg_m1a_composite_v11_local_frozen"
    bootstrap_require(
        module_name not in sys.modules, "frozen v11 module name is occupied"
    )
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(V11_PATH)
    module.__package__ = ""
    code = compile(
        raw,
        os.fspath(V11_PATH),
        "exec",
        flags=0,
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    sys.modules[module_name] = module
    try:
        exec(code, module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


try:
    V11_RAW = read_bound_v11()
    V11 = load_bound_v11(V11_RAW)
    V11_SELF_TEST = V11.offline_self_test()
    bootstrap_require(
        V11_SELF_TEST.get("result") == "pass",
        "frozen v11 local primitive self-test failed",
    )
except (BootstrapError, OSError, SyntaxError) as error:
    print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(2) from None
except Exception:
    print("ERROR: unexpected frozen-v11 local primitive load failure", file=sys.stderr)
    raise SystemExit(2) from None


CaptureError = V11.CaptureError
require = V11.require
PRIMITIVES = V11.PRIMITIVES
AuthoritySpec = V11.AuthoritySpec
ordinary = V11.ordinary
canonical_json = PRIMITIVES.canonical_json

CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
CURRENT_SOURCE_SELF_TEST = "scripts/check-current-source-state-v1-self-test.py"
CURRENT_SOURCE_MANIFEST = "audit/evidence/current-source-state-v1.json"
AUTHORITY_SPECS = tuple(
    sorted(
        (
            ordinary(".github/workflows/ci.yml", "repository_ci_authority"),
            ordinary(
                ".github/workflows/ksg-m1a-composite-v11.yml",
                "retired_v11_manual_refusal",
            ),
            ordinary(
                ".github/workflows/ksg-m1a-composite-v12.yml",
                "dedicated_v12_workflow_authority",
            ),
            ordinary(".gitleaks.toml", "narrow_secret_scan_policy_authority"),
            ordinary("crates/pid-core/build_support.rs", "rust_1_98_parser_repair"),
            ordinary("justfile", "local_command_wiring"),
            ordinary(
                "audit/evidence/ksg-rev4-m1a-composite-v12-boundary-2026-08-23.md",
                "v12_semantic_boundary",
            ),
            ordinary(
                "audit/evidence/ksg-rev4-m1a-composite-v12-path-policy-v1.json",
                "v12_path_policy",
            ),
            AuthoritySpec(
                "audit/evidence/ksg-rev4-m1a-composite-v11-local-closure-failure-v12-2026-08-23.json",
                "consumed_l11_failure_diagnostic",
                "100644",
                0o644,
                "ordinary_2mib",
                False,
            ),
            ordinary(
                "audit/schemas/ksg-rev4-m1a-composite-v11-failure-v12.schema.json",
                "consumed_l11_failure_schema",
            ),
            ordinary(
                "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v12.schema.json",
                "v12_hosted_capture_schema",
            ),
            ordinary(
                "audit/schemas/ksg-rev4-m1a-composite-local-closure-v12.schema.json",
                "local_l12_closure_schema",
            ),
            ordinary(
                "audit/schemas/ksg-rev4-m1a-composite-receipt-v12.schema.json",
                "v12_receipt_schema",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v8.py", "frozen_v8_hosted_transport"
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v8-local-closure.py",
                "frozen_v8_local_transport",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v11.py",
                "frozen_v11_hosted_transport",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v11-local-closure.py",
                "frozen_v11_local_transport",
            ),
            ordinary(
                "scripts/check-ksg-m1a-composite-v11.py",
                "frozen_v11_checker_primitives",
            ),
            ordinary(
                "scripts/check-ksg-m1a-composite-v11-self-test.py",
                "frozen_v11_checker_hostile_suite",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v12.py",
                "bounded_hosted_v12_capture_tool",
            ),
            ordinary(
                "scripts/capture-ksg-m1a-composite-v12-local-closure.py",
                "bounded_local_l12_capture_tool",
            ),
            ordinary(
                "scripts/check-ksg-m1a-composite-v12.py", "composite_v12_semantic_gate"
            ),
            ordinary(
                "scripts/check-ksg-m1a-composite-v12-self-test.py",
                "composite_v12_hostile_suite",
            ),
            ordinary(
                "scripts/normalize-actions-checkout-git-info-exclude.py",
                "git_info_exclude_normalizer",
            ),
            ordinary(
                "scripts/normalize-actions-checkout-git-info-exclude-self-test.py",
                "git_info_exclude_hostile_suite",
            ),
            ordinary(
                "scripts/check-certified-sxpid2-claim.py", "certified_sxpid_claim_gate"
            ),
            ordinary(
                "scripts/check-certified-sxpid2-claim-self-test.py",
                "certified_sxpid_claim_hostile_suite",
            ),
            ordinary(
                "scripts/check-lean-toolchain-freeze.py",
                "current_c12_lean_freeze_gate",
            ),
            ordinary(
                "scripts/check-lean-toolchain-freeze-self-test.py",
                "current_c12_lean_freeze_hostile_suite",
            ),
            ordinary(
                "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-19-r14.json",
                "preserved_lean_r14_receipt",
            ),
            ordinary(
                CURRENT_SOURCE_CHECKER, "current_source_semantic_gate", executable=True
            ),
            ordinary(
                CURRENT_SOURCE_MANIFEST,
                "fresh_current_source_generation_17_manifest",
            ),
            ordinary(
                "audit/schemas/current-source-state-v1.schema.json",
                "current_source_manifest_schema",
            ),
            ordinary(
                CURRENT_SOURCE_SELF_TEST,
                "current_source_hostile_suite",
                executable=True,
            ),
        ),
        key=lambda item: item.path,
    )
)
AUTHORITY_BY_PATH = {item.path: item for item in AUTHORITY_SPECS}
LIMIT_CLASS_BYTES = {"ordinary_2mib": MAX_ORDINARY_AUTHORITY_BYTES}

# Rebind only the identity/roster globals that the frozen v11 transport resolves
# dynamically. Its descriptor, Git-object, subprocess, environment, and output
# implementations remain byte-identical to the checksum-bound source.
V11.AUTHORITY_SPECS = AUTHORITY_SPECS
V11.AUTHORITY_BY_PATH = AUTHORITY_BY_PATH
V11.LIMIT_CLASS_BYTES = LIMIT_CLASS_BYTES
V11.LIMITS = LIMITS
V11.C9_COMMIT = C11_COMMIT
V11.C9_TREE = C11_TREE
V11.C11_MESSAGE = C12_MESSAGE
V11.COMMAND_ARGV = COMMAND_ARGV
V11.COMMAND_TIMEOUT_SECONDS = COMMAND_TIMEOUT_SECONDS
V11.MAX_AUTHORITY_AGGREGATE_BYTES = MAX_AUTHORITY_AGGREGATE_BYTES
V11.MAX_ORDINARY_AUTHORITY_BYTES = MAX_ORDINARY_AUTHORITY_BYTES
V11.MAX_RECORD_BYTES = MAX_RECORD_BYTES
PRIMITIVES.C5_COMMIT = C11_COMMIT
PRIMITIVES.C6_MESSAGE = C12_MESSAGE


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def byte_binding(raw: bytes) -> dict[str, Any]:
    return V11.byte_binding(raw)


def authority_spec_invariants() -> None:
    paths = [item.path for item in AUTHORITY_SPECS]
    roles = [item.role for item in AUTHORITY_SPECS]
    require(
        len(AUTHORITY_SPECS) == 34
        and paths == sorted(paths)
        and len(paths) == len(set(paths))
        and len(roles) == len(set(roles))
        and all(item.limit_class == "ordinary_2mib" for item in AUTHORITY_SPECS),
        "v12 authority roster or resource classes changed",
    )
    require(
        AUTHORITY_BY_PATH[CURRENT_SOURCE_CHECKER].git_mode == "100755"
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_CHECKER].live_mode == 0o755
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_SELF_TEST].git_mode == "100755"
        and AUTHORITY_BY_PATH[CURRENT_SOURCE_SELF_TEST].live_mode == 0o755,
        "current-source executable modes changed",
    )


def summarize_authorities(
    authorities: list[dict[str, Any]],
) -> tuple[int, dict[str, int]]:
    aggregate = sum(
        item["size_bytes"]
        for item in authorities
        if type(item.get("size_bytes")) is int
    )
    require(
        aggregate <= MAX_AUTHORITY_AGGREGATE_BYTES, "authority aggregate exceeds 16 MiB"
    )
    states: dict[str, int] = {}
    for item in authorities:
        state = item["binding_state"]
        states[state] = states.get(state, 0) + 1
    return aggregate, dict(sorted(states.items()))


def preflight_live() -> dict[str, Any]:
    authority_spec_invariants()
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-c12-live-preflight-",
        dir="/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
    ) as temporary_text:
        temporary_root = Path(temporary_text)
        directories = PRIMITIVES.fixed_path_directories()
        environment, _route_digest = PRIMITIVES.minimal_environment(
            directories, temporary_root
        )
        git_path = PRIMITIVES.resolve_executable("git", directories)
        _code, head_raw = V11.git_output(
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
        tree = V11.verify_commit_tree_objects(git_path, environment, head)
        authorities = V11.inspect_authorities(
            git_path, environment, head, require_committed=False
        )
    pending = [
        item["path"]
        for item in authorities
        if item["binding_state"] == "pending_evidence_absent"
    ]
    require(
        pending
        in (
            [],
            [
                "audit/evidence/ksg-rev4-m1a-composite-v11-local-closure-failure-v12-2026-08-23.json"
            ],
        ),
        "unexpected pending v12 authority",
    )
    aggregate, states = summarize_authorities(authorities)
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
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-live-preflight/v1",
        "state_counts": states,
    }


def offline_self_test() -> dict[str, Any]:
    authority_spec_invariants()
    require(
        V11_SELF_TEST.get("result") == "pass",
        "frozen v11 local primitive self-test changed",
    )
    V11.expect_bound(MAX_ORDINARY_AUTHORITY_BYTES, MAX_ORDINARY_AUTHORITY_BYTES, True)
    V11.expect_bound(
        MAX_ORDINARY_AUTHORITY_BYTES + 1,
        MAX_ORDINARY_AUTHORITY_BYTES,
        False,
    )
    return {
        "authority_specifications_verified": len(AUTHORITY_SPECS),
        "frozen_v11_local_self_test": "pass",
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v12-local-capture-self-test/v1",
        "special_limit_paths": [],
        "synthetic_authority_bound_acceptances": 1,
        "synthetic_authority_bound_rejections": 1,
    }


def validate_constructed_record(value: dict[str, Any]) -> None:
    require(
        set(value)
        == {
            "authorities",
            "immutable_v8_primitives",
            "immutable_v11_primitives",
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
        and value["repository"] == REPOSITORY
        and value["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v12"
        and value["schema_revision"] == 12
        and value["limits"] == LIMITS
        and value["nonimplications"] == NONIMPLICATIONS,
        "constructed L12 root identity changed",
    )
    authorities = value["authorities"]
    require(
        type(authorities) is list
        and [item.get("path") for item in authorities]
        == [item.path for item in AUTHORITY_SPECS]
        and all(item.get("binding_state") == "bound_to_head" for item in authorities),
        "constructed L12 authority roster changed",
    )
    invocation = value["invocation"]
    require(
        invocation["argv"] == list(COMMAND_ARGV)
        and invocation["exit_code"] == 0
        and invocation["signal"] is None
        and invocation["timed_out"] is False
        and invocation["timeout_seconds"] == COMMAND_TIMEOUT_SECONDS,
        "constructed L12 invocation changed",
    )


def capture_under_fixed_umask(output_path: str) -> None:
    PRIMITIVES.reject_ambient_secrets(dict(os.environ))
    require(
        platform.system() == "Darwin"
        and platform.machine() in {"arm64", "aarch64"}
        and platform.python_implementation() == "CPython"
        and platform.python_version() == "3.14.6"
        and sys._is_gil_enabled(),
        "L12 capture requires the reviewed Darwin arm64 GIL-enabled CPython 3.14.6 lane",
    )
    descriptor_fd = -1
    destination: Path | None = None
    created_device_inode: tuple[int, int] | None = None
    rendered = b""
    try:
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-c12-local-closure-",
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
            require(before_state["parent"] == C11_COMMIT, "L12 parent changed")
            verified_tree = V11.verify_commit_tree_objects(
                executables["git"], environment, before_state["head"]
            )
            require(
                verified_tree == before_state["tree"],
                "L12 snapshot tree differs from verified Git object",
            )
            authorities = V11.inspect_authorities(
                executables["git"],
                environment,
                before_state["head"],
                require_committed=True,
            )
            require(
                all(item["binding_state"] == "bound_to_head" for item in authorities),
                "L12 production authority is not bound to HEAD",
            )
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
                "L12 command did not complete successfully",
            )
            PRIMITIVES.reject_sensitive_output(
                stdout, private_prefixes, "L12 command stdout"
            )
            PRIMITIVES.reject_sensitive_output(
                stderr, private_prefixes, "L12 command stderr"
            )
            require(stdout + stderr != b"", "L12 command retained no output")
            after_authorities = V11.inspect_authorities(
                executables["git"],
                environment,
                before_state["head"],
                require_committed=True,
            )
            require(
                after_authorities == authorities,
                "L12 authority roster changed during execution",
            )
            after_state = PRIMITIVES.repository_snapshot(
                executables["git"], environment
            )
            require(
                {key: before_state[key] for key in before_state if key != "observed_at"}
                == {
                    key: after_state[key] for key in after_state if key != "observed_at"
                },
                "L12 repository endpoint changed during execution",
            )
            elapsed = monotonic_end - monotonic_start
            require(elapsed > 0, "L12 monotonic interval changed")
            value = {
                "authorities": authorities,
                "immutable_v8_primitives": {
                    "path": V11.V8_RELATIVE,
                    "sha256": V11.V8_SHA256,
                    "size_bytes": V11.V8_SIZE_BYTES,
                },
                "immutable_v11_primitives": {
                    "path": V11_RELATIVE,
                    "sha256": V11_SHA256,
                    "size_bytes": V11_SIZE_BYTES,
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
                "schema": "pid-rs/ksg-rev4-m1a-composite-local-closure/v12",
                "schema_revision": 12,
                "subject": {
                    "c11_parent": C11_COMMIT,
                    "c12_commit": before_state["head"],
                    "c12_message": C12_MESSAGE,
                    "c12_tree": before_state["tree"],
                },
            }
            validate_constructed_record(value)
            rendered = canonical_json(value)
            require(
                0 < len(rendered) <= MAX_RECORD_BYTES,
                "L12 record exceeds byte bound",
            )
        descriptor_fd, destination = PRIMITIVES.create_output(output_path)
        created = os.fstat(descriptor_fd)
        created_device_inode = (created.st_dev, created.st_ino)
        PRIMITIVES.validate_output_descriptor(descriptor_fd)
        written = 0
        while written < len(rendered):
            count = os.write(descriptor_fd, rendered[written:])
            require(count > 0, "L12 output write made no progress")
            written += count
        os.fsync(descriptor_fd)
        PRIMITIVES.validate_output_descriptor(descriptor_fd)
        os.close(descriptor_fd)
        descriptor_fd = -1
        require(destination is not None, "L12 output destination disappeared")
        metadata = destination.lstat()
        require(
            metadata.st_size == len(rendered)
            and stat.S_IMODE(metadata.st_mode) == 0o600
            and destination.read_bytes() == rendered,
            "installed L12 record bytes changed",
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
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--preflight-live", action="store_true")
    modes.add_argument("--output")
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        current_v11 = read_bound_v11()
        require(current_v11 == V11_RAW, "frozen v11 local transport changed after load")
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
    except (BootstrapError, CaptureError, OSError, subprocess.SubprocessError):
        print("ERROR: bounded local L12 capture failed closed", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: unexpected bounded local L12 capture failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
