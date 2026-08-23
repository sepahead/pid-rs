#!/usr/bin/env python3
"""Independently check the fresh C9-to-C11 operational contract.

Authoring mode validates the live production source roster while allowing the
one not-yet-produced predecessor capture and prospective C11 bytes. Candidate
mode requires a clean direct C9 child and exact Git/live authority equality.
Neither mode produces evidence or grants scientific credit.
"""

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
        "ERROR: check-ksg-m1a-composite-v11.py requires Python 3.11+ "
        "-I -S -B and at most one -O",
        file=sys.stderr,
    )
    raise SystemExit(2)


import argparse
import ast
import base64
import binascii
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import struct
import subprocess
import time
from typing import Any, NoReturn
import zipfile
import zlib


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
REPOSITORY = "sepahead/pid-rs"
C9_COMMIT = "337fe9b7f7cf30a8f00138310ce0398d9e95b9c5"
C9_TREE = "325f9fb463e2ec8ed36f0c7b1d61c119e6861d9c"
C10_COMMIT = "8a9c52c4871f62cf4165102fa5d1c671f866ae73"
C10_TREE = "c33fdfd8340594c8233128034baf1804084abc75"
C11_MESSAGE = "Repair KSG M1a composite v11 contract\n"
R11_MESSAGE = "Record KSG M1a composite v11 receipt\n"
SPECIAL_PATH = "audit/evidence/ksg-rev4-m1a-composite-c9-terminal-hosted-capture-v10-2026-08-23.json"
POLICY_PATH = "audit/evidence/ksg-rev4-m1a-composite-v11-path-policy-v1.json"
BOUNDARY_PATH = "audit/evidence/ksg-rev4-m1a-composite-v11-boundary-2026-08-23.md"
DIAGNOSTIC_PATH = (
    "audit/evidence/ksg-rev4-m1a-composite-v10-diagnostic-failure-2026-08-23.json"
)
LOCAL_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-local-closure-v11.schema.json"
HOSTED_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-hosted-capture-v11.schema.json"
RECEIPT_SCHEMA = "audit/schemas/ksg-rev4-m1a-composite-receipt-v11.schema.json"
LOCAL_TOOL = "scripts/capture-ksg-m1a-composite-v11-local-closure.py"
HOSTED_TOOL = "scripts/capture-ksg-m1a-composite-v11.py"
SELF_TEST = "scripts/check-ksg-m1a-composite-v11-self-test.py"
CHECKER = "scripts/check-ksg-m1a-composite-v11.py"
WORKFLOW = ".github/workflows/ksg-m1a-composite-v11.yml"
RETIRED_V9_WORKFLOW = ".github/workflows/ksg-m1a-composite-v9.yml"
NORMALIZER = "scripts/normalize-actions-checkout-git-info-exclude.py"
NORMALIZER_SELF_TEST = (
    "scripts/normalize-actions-checkout-git-info-exclude-self-test.py"
)
CURRENT_SOURCE_CHECKER = "scripts/check-current-source-state-v1.py"
CURRENT_SOURCE_SELF_TEST = "scripts/check-current-source-state-v1-self-test.py"
CURRENT_SOURCE_MANIFEST = "audit/evidence/current-source-state-v1.json"
CURRENT_SOURCE_SCHEMA = "audit/schemas/current-source-state-v1.schema.json"
LOCAL_EVIDENCE = (
    "audit/evidence/ksg-rev4-m1a-composite-local-closure-v11-2026-08-23.json"
)
SUCCESSOR_CAPTURE = (
    "audit/evidence/ksg-rev4-m1a-composite-successor-qualification-"
    "hosted-capture-v11-2026-08-23.json"
)
RECEIPT = "audit/evidence/ksg-rev4-m1a-composite-receipt-v11-2026-08-23.json"
ORDINARY_LIMIT = 2 * 1024 * 1024
SPECIAL_LIMIT = 4 * 1024 * 1024
AGGREGATE_LIMIT = 16 * 1024 * 1024
VERSION_LIMIT = 64 * 1024
GIT_METADATA_LIMIT = 2 * 1024 * 1024
CAPTURE_BODY_LIMIT = 22 * 1024 * 1024
RECORD_LIMIT = 32 * 1024 * 1024
CAPTURE_ROW_LIMIT = 4096
ZIP_MEMBER_READ_CHUNK = 64 * 1024
GIT_EXECUTABLE = Path("/usr/bin/git")
OID_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CAPTURE_V8 = {
    "path": "scripts/capture-ksg-m1a-composite-v8.py",
    "sha256": "79ffbe59dc57ed99d2b4032aa71cac300448d0978a42a52fcf7b40b08236ae6f",
    "size_bytes": 24_111,
}
PREDECESSOR_RUNS = {
    "predecessor_ci": 32_600_674_974,
    "predecessor_codeql": 32_600_674_616,
    "predecessor_contract": 32_600_674_991,
}
PREDECESSOR_CONCLUSIONS = {
    "predecessor_ci": "failure",
    "predecessor_codeql": "success",
    "predecessor_contract": "failure",
}
PREDECESSOR_FAILED_JOBS = {
    "predecessor_ci": [97_098_355_474, 97_098_355_544, 97_098_355_596],
    "predecessor_codeql": [],
    "predecessor_contract": [97_098_355_185],
}
CAPTURE_NONIMPLICATIONS = [
    "Captured HTTPS response bytes do not authenticate themselves.",
    "Two retrieval repetitions are correlated provider observations, not independent replications.",
    "The predecessor phase freshly records three separate C9 operational outcomes and cannot issue R9, qualify C10, or qualify C11.",
    "The C9 dedicated-v9 route failed its static checker; that does not identify or transfer a cause to the distinct repository-CI failures.",
    "The C9 repository CI Clippy, secret-scan, and SemVer failures remain distinct observations; no secret, API break, numerical defect, theorem defect, or common cause is inferred.",
    "Same-generation repository-CI and dedicated-workflow executions in either phase are correlated GitHub observations, not independent replications.",
    "Rejected C10 bytes, its unissued L10/R10, and its rejected R15 have zero C11 credit and are not inputs to this fresh capture.",
    "A successful successor phase is operational evidence, not mathematical, estimator, security, accessibility, or application validation.",
    "Code-scanning analysis and alert endpoints are repository-level current-state snapshots, not run-foreign-keyed historical observations.",
    "Capture time, provider response order, provider completeness, authentication, and trusted time are not claimed.",
    "A newly emitted capture binds the current capture-tool descriptor and repeated response bytes, but freshness is controlled operator process rather than authenticated collection time; the format cannot distinguish live collection from manual reconstruction of identical public response bytes plus a changed descriptor.",
    "No observation transfers among PID functionals, estimators, support classes, or downstream uses.",
]
EXPECTED_C11_DELTA = tuple(
    sorted(
        (
            (".github/workflows/ci.yml", "M", "100644"),
            (RETIRED_V9_WORKFLOW, "M", "100644"),
            (WORKFLOW, "A", "100644"),
            (".gitleaks.toml", "M", "100644"),
            ("crates/pid-core/build_support.rs", "M", "100644"),
            ("justfile", "M", "100644"),
            (CURRENT_SOURCE_MANIFEST, "M", "100644"),
            (SPECIAL_PATH, "A", "100644"),
            (DIAGNOSTIC_PATH, "A", "100644"),
            (BOUNDARY_PATH, "A", "100644"),
            (POLICY_PATH, "A", "100644"),
            (HOSTED_SCHEMA, "A", "100644"),
            (LOCAL_SCHEMA, "A", "100644"),
            (RECEIPT_SCHEMA, "A", "100644"),
            (HOSTED_TOOL, "A", "100644"),
            (LOCAL_TOOL, "A", "100644"),
            (CHECKER, "A", "100644"),
            (SELF_TEST, "A", "100644"),
            (NORMALIZER, "A", "100644"),
            (NORMALIZER_SELF_TEST, "A", "100644"),
        )
    )
)
EXPECTED_R11_DELTA = tuple(
    sorted(
        (
            (CURRENT_SOURCE_MANIFEST, "M", "100644"),
            (LOCAL_EVIDENCE, "A", "100644"),
            (SUCCESSOR_CAPTURE, "A", "100644"),
            (RECEIPT, "A", "100644"),
        )
    )
)
PRESERVED_R11_PATHS = (LOCAL_EVIDENCE, SUCCESSOR_CAPTURE, RECEIPT)
PYTHON_LITERAL_KEY_SOURCES = (
    HOSTED_TOOL,
    LOCAL_TOOL,
    CHECKER,
    SELF_TEST,
    NORMALIZER,
    NORMALIZER_SELF_TEST,
)
RECEIPT_NONIMPLICATIONS = [
    "Q11 is an operational conjunction for one exact C11 identity, not PID, KSG, theorem, numerical, security, privacy, accessibility, or application validation.",
    "L11 records one bounded local execution and cannot prove hermeticity, operator uniqueness, or absence of an undisclosed parallel launch.",
    "GitHub response bytes, repeated retrievals, timestamps, digests, and unsigned Git objects do not authenticate themselves or establish trusted time.",
    "CodeQL analysis and alert endpoints are repository-level current-state observations rather than run-foreign-keyed historical facts.",
    "C10, L10, R10, R15, and unrecovered C10 bytes grant no ancestry, evidence, or qualification credit to C11 or R11.",
]


class ContractError(RuntimeError):
    """The v11 contract or one of its bounded authorities diverged."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise ContractError(message)


def refuse(message: str) -> NoReturn:
    raise ContractError(message)


@dataclass(frozen=True)
class ExpectedAuthority:
    path: str
    role: str
    git_mode: str
    live_mode: int
    limit_class: str
    authoring_required: bool = True


def ordinary(path: str, role: str, *, executable: bool = False) -> ExpectedAuthority:
    return ExpectedAuthority(
        path,
        role,
        "100755" if executable else "100644",
        0o755 if executable else 0o644,
        "ordinary_2mib",
    )


EXPECTED_AUTHORITIES = tuple(
    sorted(
        (
            ordinary(".github/workflows/ci.yml", "repository_ci_authority"),
            ordinary(RETIRED_V9_WORKFLOW, "retired_v9_manual_refusal"),
            ordinary(WORKFLOW, "dedicated_v11_workflow_authority"),
            ordinary(".gitleaks.toml", "narrow_secret_scan_policy_authority"),
            ordinary("crates/pid-core/build_support.rs", "rust_1_98_parser_repair"),
            ordinary("justfile", "local_command_wiring"),
            ordinary(BOUNDARY_PATH, "v11_semantic_boundary"),
            ordinary(POLICY_PATH, "v11_path_policy"),
            ordinary(DIAGNOSTIC_PATH, "rejected_c10_diagnostic_record"),
            ordinary(HOSTED_SCHEMA, "v11_hosted_capture_schema"),
            ordinary(LOCAL_SCHEMA, "local_l11_closure_schema"),
            ordinary(RECEIPT_SCHEMA, "v11_receipt_schema"),
            ordinary(LOCAL_TOOL, "bounded_local_l11_capture_tool"),
            ordinary(HOSTED_TOOL, "bounded_hosted_v11_capture_tool"),
            ordinary(SELF_TEST, "composite_v11_hostile_suite"),
            ordinary(CHECKER, "composite_v11_semantic_gate"),
            ordinary(NORMALIZER, "git_info_exclude_normalizer"),
            ordinary(NORMALIZER_SELF_TEST, "git_info_exclude_hostile_suite"),
            ordinary(
                CURRENT_SOURCE_CHECKER, "current_source_semantic_gate", executable=True
            ),
            ordinary(CURRENT_SOURCE_MANIFEST, "fresh_r16_current_source_manifest"),
            ordinary(CURRENT_SOURCE_SCHEMA, "current_source_manifest_schema"),
            ordinary(
                CURRENT_SOURCE_SELF_TEST,
                "current_source_hostile_suite",
                executable=True,
            ),
            ExpectedAuthority(
                SPECIAL_PATH,
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
EXPECTED_BY_PATH = {item.path: item for item in EXPECTED_AUTHORITIES}
LIMITS = {
    "ordinary_2mib": ORDINARY_LIMIT,
    "terminal_c9_capture_4mib": SPECIAL_LIMIT,
}


def validate_authority_specification(
    authorities: tuple[ExpectedAuthority, ...] = EXPECTED_AUTHORITIES,
) -> None:
    paths = [item.path for item in authorities]
    roles = [item.role for item in authorities]
    require(
        paths == sorted(paths)
        and len(paths) == len(set(paths))
        and len(roles) == len(set(roles)),
        "authority paths or roles overlap",
    )
    special = [item.path for item in authorities if item.limit_class != "ordinary_2mib"]
    require(
        special == [SPECIAL_PATH]
        and EXPECTED_BY_PATH[SPECIAL_PATH].limit_class == "terminal_c9_capture_4mib"
        and all(
            item.limit_class == "ordinary_2mib"
            for item in authorities
            if item.path != SPECIAL_PATH
        ),
        "4 MiB class escaped the exact terminal-C9 capture path",
    )
    require(
        EXPECTED_BY_PATH[CURRENT_SOURCE_CHECKER].git_mode == "100755"
        and EXPECTED_BY_PATH[CURRENT_SOURCE_CHECKER].live_mode == 0o755
        and EXPECTED_BY_PATH[CURRENT_SOURCE_SELF_TEST].git_mode == "100755"
        and EXPECTED_BY_PATH[CURRENT_SOURCE_SELF_TEST].live_mode == 0o755,
        "latent v10 executable-mode repair regressed",
    )


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
    require(root.is_absolute(), "repository root is not absolute")
    require(root.resolve(strict=True) == root, "repository root route is not canonical")
    before = root.lstat()
    require(stat.S_ISDIR(before.st_mode), "repository root is not a real directory")
    descriptor = os.open(root, directory_flags())
    opened = os.fstat(descriptor)
    if metadata_identity(before) != metadata_identity(opened):
        os.close(descriptor)
        raise ContractError("repository root changed while opening")
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


def stable_read(root_fd: int, authority: ExpectedAuthority) -> bytes:
    components = authority.path.split("/")
    require(
        components
        and all(component not in {"", ".", ".."} for component in components),
        "unsafe authority route",
    )
    opened_directories: list[tuple[int, tuple[int, ...], int, str]] = []
    parent_fd = root_fd
    try:
        for component in components[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            require(
                stat.S_ISDIR(before.st_mode),
                f"non-directory ancestor: {authority.path}",
            )
            child_fd = os.open(component, directory_flags(), dir_fd=parent_fd)
            opened = os.fstat(child_fd)
            require(
                metadata_identity(before) == metadata_identity(opened),
                f"ancestor changed while opening: {authority.path}",
            )
            opened_directories.append(
                (child_fd, metadata_identity(opened), parent_fd, component)
            )
            parent_fd = child_fd
        leaf = components[-1]
        before = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(
            stat.S_ISREG(before.st_mode), f"authority is not regular: {authority.path}"
        )
        require(before.st_nlink == 1, f"authority is multiply linked: {authority.path}")
        require(
            stat.S_IMODE(before.st_mode) == authority.live_mode,
            f"authority live mode differs: {authority.path}",
        )
        maximum = LIMITS[authority.limit_class]
        require(
            0 < before.st_size <= maximum, f"authority exceeds class: {authority.path}"
        )
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(leaf, flags, dir_fd=parent_fd)
        try:
            opened = os.fstat(descriptor)
            require(
                metadata_identity(opened) == metadata_identity(before),
                f"authority changed before read: {authority.path}",
            )
            chunks: list[bytes] = []
            remaining = before.st_size
            while remaining:
                chunk = os.read(descriptor, min(remaining, 1024 * 1024))
                require(chunk != b"", f"short authority read: {authority.path}")
                chunks.append(chunk)
                remaining -= len(chunk)
            require(os.read(descriptor, 1) == b"", f"authority grew: {authority.path}")
            after_fd = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        require(
            metadata_identity(before)
            == metadata_identity(opened)
            == metadata_identity(after_fd)
            == metadata_identity(after),
            f"authority identity changed: {authority.path}",
        )
        for descriptor, identity, owning_parent_fd, component in opened_directories:
            require(
                metadata_identity(os.fstat(descriptor))
                == identity
                == metadata_identity(
                    os.stat(
                        component,
                        dir_fd=owning_parent_fd,
                        follow_symlinks=False,
                    )
                ),
                f"authority ancestor changed: {authority.path}",
            )
        return b"".join(chunks)
    finally:
        for descriptor, _identity, _parent_fd, _component in reversed(
            opened_directories
        ):
            os.close(descriptor)


def git_environment() -> dict[str, str]:
    return {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
    }


def terminate_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        process.kill()


def run_git_bounded(
    arguments: tuple[str, ...],
    maximum_stdout: int,
    accepted: frozenset[int],
) -> tuple[int, bytes, bytes]:
    require(
        type(maximum_stdout) is int and 0 <= maximum_stdout <= RECORD_LIMIT,
        "Git stdout bound changed",
    )
    before = GIT_EXECUTABLE.lstat()
    require(
        GIT_EXECUTABLE.resolve(strict=True) == GIT_EXECUTABLE
        and stat.S_ISREG(before.st_mode)
        and os.access(GIT_EXECUTABLE, os.X_OK),
        "fixed Git executable is not one canonical executable file",
    )
    process = subprocess.Popen(
        (
            os.fspath(GIT_EXECUTABLE),
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            *arguments,
        ),
        cwd=ROOT,
        env=git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
    )
    require(
        process.stdout is not None and process.stderr is not None,
        "Git pipe setup failed",
    )
    selector = selectors.DefaultSelector()
    stdout_fd = process.stdout.fileno()
    stderr_fd = process.stderr.fileno()
    os.set_blocking(stdout_fd, False)
    os.set_blocking(stderr_fd, False)
    streams = {stdout_fd: bytearray(), stderr_fd: bytearray()}
    bounds = {stdout_fd: maximum_stdout, stderr_fd: VERSION_LIMIT}
    selector.register(process.stdout, selectors.EVENT_READ)
    selector.register(process.stderr, selectors.EVENT_READ)
    deadline = time.monotonic() + 30
    drain_deadline: float | None = None
    try:
        while selector.get_map():
            now = time.monotonic()
            if process.poll() is None and now >= deadline:
                terminate_process_group(process)
                raise ContractError("isolated Git query timed out")
            if process.poll() is not None and drain_deadline is None:
                drain_deadline = now + 2
            if drain_deadline is not None and now >= drain_deadline:
                terminate_process_group(process)
                raise ContractError("isolated Git query left a pipe open")
            for key, _mask in selector.select(0.1):
                try:
                    chunk = os.read(key.fd, 65_536)
                except BlockingIOError:
                    continue
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                streams[key.fd].extend(chunk)
                if len(streams[key.fd]) > bounds[key.fd]:
                    terminate_process_group(process)
                    raise ContractError("isolated Git query exceeded its stream bound")
        return_code = process.wait(timeout=5)
    except Exception:
        terminate_process_group(process)
        process.wait(timeout=5)
        raise
    finally:
        selector.close()
    after = GIT_EXECUTABLE.lstat()
    require(
        metadata_identity(before) == metadata_identity(after),
        "fixed Git executable changed during invocation",
    )
    return return_code, bytes(streams[stdout_fd]), bytes(streams[stderr_fd])


def git(
    *arguments: str,
    maximum: int = VERSION_LIMIT,
    accepted: frozenset[int] = frozenset({0}),
) -> bytes:
    code, stdout, stderr = run_git_bounded(arguments, maximum, accepted)
    require(code in accepted, "isolated Git query returned an unexpected status")
    if code == 0:
        require(stderr == b"", "isolated Git query wrote stderr")
    return stdout


def git_oid(kind: str, raw: bytes) -> str:
    framed = f"{kind} {len(raw)}\0".encode("ascii") + raw
    return hashlib.sha1(framed, usedforsecurity=False).hexdigest()


def verify_object(kind: str, oid: str, maximum: int) -> bytes:
    require(kind in {"blob", "commit", "tree"}, "Git object kind changed")
    require(OID_RE.fullmatch(oid) is not None, "Git object identity is malformed")
    raw = git("cat-file", kind, oid, maximum=maximum)
    require(git_oid(kind, raw) == oid, f"Git {kind} object hash mismatch")
    return raw


def tree_entry(head: str, path: str) -> tuple[str, str] | None:
    raw = git("ls-tree", "-z", head, "--", path)
    if not raw:
        return None
    require(raw.endswith(b"\0") and raw.count(b"\0") == 1, "tree row count changed")
    metadata, separator, observed_path = raw[:-1].partition(b"\t")
    fields = metadata.split(b" ")
    require(
        separator == b"\t"
        and observed_path == path.encode("utf-8")
        and len(fields) == 3
        and fields[1] == b"blob",
        "tree row changed",
    )
    mode = fields[0].decode("ascii", errors="strict")
    oid = fields[2].decode("ascii", errors="strict")
    require(
        mode in {"100644", "100755"} and OID_RE.fullmatch(oid) is not None,
        "tree metadata changed",
    )
    return mode, oid


def tree_blob(commit: str, path: str, maximum: int) -> bytes:
    entry = tree_entry(commit, path)
    require(entry is not None, f"Git tree path is absent: {path}")
    mode, oid = entry
    require(mode in {"100644", "100755"}, f"Git tree path mode changed: {path}")
    return verify_object("blob", oid, maximum)


def parse_commit_envelope(raw: bytes) -> tuple[str, tuple[str, ...], str, bool]:
    require(b"\n\n" in raw, "commit object has no message boundary")
    header_raw, message_raw = raw.split(b"\n\n", 1)
    headers = header_raw.split(b"\n")
    tree_rows = [row for row in headers if row.startswith(b"tree ")]
    parent_rows = [row for row in headers if row.startswith(b"parent ")]
    signed = any(row.startswith((b"gpgsig ", b"gpgsig-sha256 ")) for row in headers)
    require(len(tree_rows) == 1, "commit object does not contain exactly one tree")
    try:
        tree = tree_rows[0][5:].decode("ascii", errors="strict")
        parents = tuple(row[7:].decode("ascii", errors="strict") for row in parent_rows)
        message = message_raw.decode("utf-8", errors="strict")
    except UnicodeError:
        raise ContractError("commit envelope encoding changed") from None
    require(
        OID_RE.fullmatch(tree) is not None
        and all(OID_RE.fullmatch(parent) is not None for parent in parents),
        "commit tree or parent identity is malformed",
    )
    return tree, parents, message, signed


def verify_head_objects(head: str) -> tuple[str, bytes]:
    commit_raw = verify_object("commit", head, ORDINARY_LIMIT)
    tree, _parents, _message, _signed = parse_commit_envelope(commit_raw)
    verify_object("tree", tree, ORDINARY_LIMIT)
    return tree, commit_raw


@dataclass(frozen=True)
class CommitEnvelope:
    oid: str
    tree: str
    parents: tuple[str, ...]
    message: str
    signed: bool


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str
    oid: str


def commit_envelope(oid: str) -> CommitEnvelope:
    raw = verify_object("commit", oid, ORDINARY_LIMIT)
    tree, parents, message, signed = parse_commit_envelope(raw)
    verify_object("tree", tree, ORDINARY_LIMIT)
    return CommitEnvelope(oid, tree, parents, message, signed)


def recursive_tree_entries(commit: str) -> dict[str, TreeEntry]:
    raw = git(
        "ls-tree",
        "-rz",
        "--full-tree",
        commit,
        maximum=GIT_METADATA_LIMIT,
    )
    require(
        not raw or raw.endswith(b"\0"), "recursive tree output lacks NUL termination"
    )
    result: dict[str, TreeEntry] = {}
    for row in raw[:-1].split(b"\0") if raw else ():
        metadata, separator, path_raw = row.partition(b"\t")
        fields = metadata.split(b" ")
        require(
            separator == b"\t" and len(fields) == 3,
            "recursive tree row changed",
        )
        try:
            mode = fields[0].decode("ascii", errors="strict")
            kind = fields[1].decode("ascii", errors="strict")
            oid = fields[2].decode("ascii", errors="strict")
            path = path_raw.decode("utf-8", errors="strict")
        except UnicodeError:
            raise ContractError("recursive tree row encoding changed") from None
        require(
            path
            and not path.startswith("/")
            and "\0" not in path
            and all(component not in {"", ".", ".."} for component in path.split("/"))
            and mode in {"100644", "100755", "120000", "160000"}
            and kind in {"blob", "commit"}
            and OID_RE.fullmatch(oid) is not None
            and path not in result,
            "recursive tree entry is unsupported or duplicated",
        )
        result[path] = TreeEntry(mode, kind, oid)
    require(list(result) == sorted(result), "recursive tree entries are not sorted")
    return result


def selected_tree_entries(commit: str, paths: tuple[str, ...]) -> dict[str, TreeEntry]:
    require(
        paths
        and len(paths) == len(set(paths))
        and all(
            path
            and not path.startswith("/")
            and all(component not in {"", ".", ".."} for component in path.split("/"))
            for path in paths
        ),
        "selected tree path roster changed",
    )
    raw = git(
        "ls-tree",
        "-z",
        commit,
        "--",
        *paths,
        maximum=ORDINARY_LIMIT,
    )
    require(
        not raw or raw.endswith(b"\0"), "selected tree output lacks NUL termination"
    )
    result: dict[str, TreeEntry] = {}
    for row in raw[:-1].split(b"\0") if raw else ():
        metadata, separator, path_raw = row.partition(b"\t")
        fields = metadata.split(b" ")
        try:
            mode = fields[0].decode("ascii", errors="strict")
            kind = fields[1].decode("ascii", errors="strict")
            oid = fields[2].decode("ascii", errors="strict")
            path = path_raw.decode("utf-8", errors="strict")
        except (IndexError, UnicodeError):
            raise ContractError("selected tree row encoding changed") from None
        require(
            separator == b"\t"
            and len(fields) == 3
            and path in paths
            and mode in {"100644", "100755"}
            and kind == "blob"
            and OID_RE.fullmatch(oid) is not None
            and path not in result,
            "selected tree row changed",
        )
        result[path] = TreeEntry(mode, kind, oid)
    require(list(result) == sorted(result), "selected tree entries are not sorted")
    return result


def changed_rows(
    before: dict[str, TreeEntry], after: dict[str, TreeEntry]
) -> tuple[tuple[str, str, str], ...]:
    rows: list[tuple[str, str, str]] = []
    for path in sorted(set(before) | set(after)):
        left = before.get(path)
        right = after.get(path)
        if left == right:
            continue
        if left is None:
            require(right is not None, "added tree entry disappeared")
            rows.append((path, "A", right.mode))
        elif right is None:
            rows.append((path, "D", left.mode))
        else:
            rows.append((path, "M", right.mode))
    return tuple(rows)


def reachable_commits(head: str) -> tuple[str, ...]:
    raw = git("rev-list", "--topo-order", head, maximum=GIT_METADATA_LIMIT)
    try:
        values = tuple(raw.decode("ascii", errors="strict").splitlines())
    except UnicodeError:
        raise ContractError("reachable commit list encoding changed") from None
    require(
        values
        and values[0] == head
        and len(values) == len(set(values))
        and len(values) <= 100_000
        and all(OID_RE.fullmatch(value) is not None for value in values),
        "reachable commit list changed",
    )
    return values


def verify_ancestor(ancestor: str, descendant: str) -> None:
    code, stdout, stderr = run_git_bounded(
        ("merge-base", "--is-ancestor", ancestor, descendant),
        0,
        frozenset({0, 1}),
    )
    require(
        code == 0 and stdout == b"" and stderr == b"", "required Git ancestry is absent"
    )


def ancestry_path_commits(ancestor: str, descendant: str) -> tuple[str, ...]:
    if ancestor == descendant:
        return ()
    raw = git(
        "rev-list",
        "--ancestry-path",
        f"{ancestor}..{descendant}",
        maximum=GIT_METADATA_LIMIT,
    )
    try:
        values = tuple(raw.decode("ascii", errors="strict").splitlines())
    except UnicodeError:
        raise ContractError("ancestry-path commit list encoding changed") from None
    require(
        values
        and values[0] == descendant
        and len(values) == len(set(values))
        and len(values) <= 100_000
        and all(OID_RE.fullmatch(value) is not None for value in values),
        "ancestry-path commit list changed",
    )
    return values


def unique_lifecycle_identity(values: list[str], label: str) -> str:
    require(
        len(values) == 1 and OID_RE.fullmatch(values[0]) is not None,
        f"{label} identity is absent or ambiguous",
    )
    return values[0]


def validate_evidence_introductions(
    introductions: dict[str, list[str]], r11_candidates: list[str]
) -> str:
    r11 = unique_lifecycle_identity(r11_candidates, "R11")
    require(
        set(introductions) == set(PRESERVED_R11_PATHS)
        and all(values == [r11] for values in introductions.values()),
        "R11 evidence introduction is absent, split, reused, or ambiguous",
    )
    return r11


def find_evidence_introductions(
    envelopes: dict[str, CommitEnvelope],
    selected_entries: dict[str, dict[str, TreeEntry]],
) -> dict[str, list[str]]:
    require(
        set(envelopes).issubset(selected_entries)
        and all(
            parent in selected_entries
            for envelope in envelopes.values()
            for parent in envelope.parents
        ),
        "reachable evidence-entry projection is incomplete",
    )
    introductions = {path: [] for path in PRESERVED_R11_PATHS}
    for oid, envelope in envelopes.items():
        entries = selected_entries[oid]
        for path in PRESERVED_R11_PATHS:
            if path not in entries:
                continue
            if not envelope.parents or all(
                path not in selected_entries[parent] for parent in envelope.parents
            ):
                introductions[path].append(oid)
    return introductions


def validate_lifecycle_message_uniqueness(
    envelopes: dict[str, CommitEnvelope],
    c11: str,
    r11: str | None,
) -> None:
    require(
        c11 in envelopes and (r11 is None or r11 in envelopes),
        "selected lifecycle identity is absent from reachable envelopes",
    )
    for oid, envelope in envelopes.items():
        if envelope.message == C11_MESSAGE:
            require(oid == c11, "C11 lifecycle message is reused outside exact C11")
        if envelope.message == R11_MESSAGE:
            require(
                r11 is not None and oid == r11,
                "R11 lifecycle message is reused outside exact R11",
            )


def validate_preserved_r11_entries(
    r11_entries: dict[str, TreeEntry],
    descendant_entries: dict[str, dict[str, TreeEntry]],
) -> None:
    for path in PRESERVED_R11_PATHS:
        require(
            r11_entries.get(path) is not None
            and all(
                entries.get(path) == r11_entries[path]
                for entries in descendant_entries.values()
            ),
            f"R11 evidence bytes or mode changed in descendant: {path}",
        )


def locate_lifecycle(head: str) -> dict[str, Any]:
    verify_ancestor(C9_COMMIT, head)
    commits = reachable_commits(head)
    require(C9_COMMIT in commits, "C9 is absent from reachable history")
    # Scan every HEAD-reachable commit, including merged branches that do not
    # descend from C9.  C11/R11 lineage is constrained separately below.
    envelopes = {oid: commit_envelope(oid) for oid in commits}
    c11_candidates = [
        oid
        for oid, envelope in envelopes.items()
        if envelope.parents == (C9_COMMIT,) and envelope.message == C11_MESSAGE
    ]
    c11 = unique_lifecycle_identity(c11_candidates, "C11")
    c11_commit = envelopes[c11]
    require(
        not c11_commit.signed and c11 not in {C9_COMMIT, C10_COMMIT},
        "C11 is signed or reuses a rejected identity",
    )
    c9_entries = recursive_tree_entries(C9_COMMIT)
    c11_entries = recursive_tree_entries(c11)
    require(
        changed_rows(c9_entries, c11_entries) == EXPECTED_C11_DELTA,
        "C9-to-C11 delta differs from the exact twenty-row cut",
    )
    require(
        all(path not in c11_entries for path in PRESERVED_R11_PATHS),
        "R11 evidence appears in C11",
    )

    r11_candidates: list[str] = []
    selected_entries = {
        oid: selected_tree_entries(oid, PRESERVED_R11_PATHS) for oid in commits
    }
    introductions = find_evidence_introductions(envelopes, selected_entries)
    for oid, envelope in envelopes.items():
        if envelope.parents == (c11,) and envelope.message == R11_MESSAGE:
            r11_candidates.append(oid)

    if not any(introductions.values()) and not r11_candidates:
        require(head == c11, "receipt-absent workflow state is not exact C11")
        validate_lifecycle_message_uniqueness(envelopes, c11, None)
        return {
            "c11": c11,
            "c11_tree": c11_commit.tree,
            "head": head,
            "head_tree": envelopes[head].tree,
            "phase": "candidate",
            "r11": None,
            "r11_tree": None,
        }

    r11 = validate_evidence_introductions(introductions, r11_candidates)
    r11_commit = envelopes[r11]
    require(not r11_commit.signed, "R11 is signed")
    r11_entries = recursive_tree_entries(r11)
    require(
        changed_rows(c11_entries, r11_entries) == EXPECTED_R11_DELTA,
        "C11-to-R11 delta differs from the exact four-row receipt cut",
    )
    verify_ancestor(r11, head)
    validate_lifecycle_message_uniqueness(envelopes, c11, r11)
    descendant_commits = ancestry_path_commits(r11, head)
    descendant_entries = {
        oid: recursive_tree_entries(oid) for oid in descendant_commits
    }
    validate_preserved_r11_entries(r11_entries, descendant_entries)
    return {
        "c11": c11,
        "c11_tree": c11_commit.tree,
        "head": head,
        "head_tree": envelopes[head].tree,
        "phase": "receipt" if head == r11 else "preservation",
        "r11": r11,
        "r11_tree": r11_commit.tree,
    }


def validate_repository_rule_bytes(raw: bytes, label: str) -> None:
    try:
        lines = raw.decode("utf-8", errors="strict").splitlines()
    except UnicodeError:
        raise ContractError(f"{label} is not UTF-8") from None
    require(
        all(not line or line.startswith("#") for line in lines),
        f"{label} contains an effective repository-local rule",
    )


def require_descriptor_absent(root_fd: int, relative: str, label: str) -> None:
    components = relative.split("/")
    require(
        components
        and all(component not in {"", ".", ".."} for component in components),
        f"unsafe absent-route check: {label}",
    )
    opened: list[tuple[int, tuple[int, ...], int, str]] = []
    parent_fd = root_fd
    try:
        for component in components[:-1]:
            before = os.stat(component, dir_fd=parent_fd, follow_symlinks=False)
            require(
                stat.S_ISDIR(before.st_mode),
                f"non-directory absent-route ancestor: {label}",
            )
            child_fd = os.open(component, directory_flags(), dir_fd=parent_fd)
            opened_value = os.fstat(child_fd)
            require(
                metadata_identity(before) == metadata_identity(opened_value),
                f"absent-route ancestor changed while opening: {label}",
            )
            opened.append(
                (child_fd, metadata_identity(opened_value), parent_fd, component)
            )
            parent_fd = child_fd
        try:
            os.stat(components[-1], dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            refuse(f"{label} is present")
        for descriptor, identity, owning_parent, component in opened:
            require(
                metadata_identity(os.fstat(descriptor))
                == identity
                == metadata_identity(
                    os.stat(component, dir_fd=owning_parent, follow_symlinks=False)
                ),
                f"absent-route ancestor changed: {label}",
            )
    finally:
        for descriptor, _identity, _parent, _component in reversed(opened):
            os.close(descriptor)


def validate_repository_config_names(raw: bytes) -> None:
    try:
        names = raw.decode("ascii", errors="strict").splitlines()
    except UnicodeError:
        raise ContractError("repository config key encoding changed") from None
    forbidden = {
        "core.attributesfile",
        "core.excludesfile",
        "core.fsmonitor",
        "core.hookspath",
        "core.sparsecheckout",
        "core.sparsecheckoutcone",
        "core.splitindex",
        "core.untrackedcache",
        "core.worktree",
        "extensions.objectformat",
        "extensions.partialclone",
        "extensions.refstorage",
        "extensions.worktreeconfig",
        "index.sparse",
    }
    require(
        names
        and len(names) == len(set(names))
        and all(
            name.lower() not in forbidden
            and not name.lower().startswith(
                ("alias.", "filter.", "include.", "includeif.", "submodule.", "url.")
            )
            and not (
                name.lower().startswith("remote.")
                and name.lower().endswith(".promisor")
            )
            for name in names
        ),
        "repository config contains an unsupported routing overlay",
    )


GIT_METADATA_ABSENCES = (
    (".git/config.worktree", "Git worktree config overlay"),
    (".git/commondir", "Git common-directory redirect"),
    (".git/info/grafts", "Git graft overlay"),
    (".git/objects/info/alternates", "Git alternates"),
    (".git/objects/info/http-alternates", "Git HTTP alternates"),
    (".git/shallow", "shallow history boundary"),
)


def filesystem_git_metadata_snapshot() -> dict[str, Any]:
    root_fd, root_identity = open_canonical_root(ROOT)
    git_directory = ROOT / ".git"
    rules: dict[str, bytes | None] = {}
    try:
        config_raw = stable_read(
            root_fd,
            ExpectedAuthority(
                ".git/config", "repository_config", "100644", 0o644, "ordinary_2mib"
            ),
        )
        lowered = config_raw.lower()
        require(
            all(
                token not in lowered
                for token in (
                    b"[include",
                    b"worktree =",
                    b"hookspath =",
                    b"attributesfile =",
                    b"excludesfile =",
                )
            ),
            "repository config bytes contain an unsupported routing overlay",
        )
        for relative, label in (
            (".git/info/attributes", "Git info attributes"),
            (".git/info/exclude", "Git info exclude"),
        ):
            path = ROOT / relative
            if os.path.lexists(path):
                raw = stable_read(
                    root_fd,
                    ExpectedAuthority(
                        relative,
                        label.lower().replace(" ", "_"),
                        "100644",
                        0o644,
                        "ordinary_2mib",
                    ),
                )
                validate_repository_rule_bytes(raw, label)
                rules[relative] = raw
            else:
                rules[relative] = None
    finally:
        recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)
    git_metadata = git_directory.lstat()
    require(
        stat.S_ISDIR(git_metadata.st_mode) and not stat.S_ISLNK(git_metadata.st_mode),
        "repository does not use one real canonical .git directory",
    )
    absences: dict[str, bool] = {}
    for relative, label in GIT_METADATA_ABSENCES:
        absent = not os.path.lexists(ROOT / relative)
        require(absent, f"{label} is present")
        absences[relative] = absent
    return {
        "absences": absences,
        "config_raw": config_raw,
        "git_directory_identity": metadata_identity(git_metadata),
        "rules": rules,
    }


def queried_git_metadata_snapshot() -> dict[str, bytes]:
    git_directory = ROOT / ".git"
    config_names = git(
        "config",
        "--local",
        "--no-includes",
        "--name-only",
        "--list",
        maximum=ORDINARY_LIMIT,
    )
    validate_repository_config_names(config_names)
    replacements = git(
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace/",
        maximum=ORDINARY_LIMIT,
    )
    require(replacements == b"", "Git replacement refs are present")
    toplevel = git("rev-parse", "--show-toplevel")
    git_dir = git("rev-parse", "--absolute-git-dir")
    common_dir = git("rev-parse", "--git-common-dir")
    object_format = git("rev-parse", "--show-object-format=storage")
    commit_signing = git("config", "--local", "--get-all", "commit.gpgsign")
    tag_signing = git("config", "--local", "--get-all", "tag.gpgsign")
    repository_format = git(
        "config", "--local", "--get-all", "core.repositoryformatversion"
    )
    bare = git("config", "--local", "--get-all", "core.bare")
    require(
        Path(os.fsdecode(toplevel.rstrip(b"\n"))).resolve(strict=True) == ROOT
        and Path(os.fsdecode(git_dir.rstrip(b"\n"))).resolve(strict=True)
        == git_directory,
        "Git repository root routing changed",
    )
    common_path = Path(os.fsdecode(common_dir.rstrip(b"\n")))
    if not common_path.is_absolute():
        common_path = ROOT / common_path
    require(
        common_path.resolve(strict=True) == git_directory
        and object_format == b"sha1\n",
        "Git common directory or object format changed",
    )
    require(
        commit_signing == b"false\n"
        and tag_signing == b"false\n"
        and repository_format == b"0\n"
        and bare == b"false\n",
        "repository signing or format configuration changed",
    )
    return {
        "bare": bare,
        "commit_signing": commit_signing,
        "common_dir": common_dir,
        "config_names": config_names,
        "git_dir": git_dir,
        "object_format": object_format,
        "replacements": replacements,
        "repository_format": repository_format,
        "tag_signing": tag_signing,
        "toplevel": toplevel,
    }


def complete_git_metadata_snapshot() -> dict[str, Any]:
    return {
        "filesystem": filesystem_git_metadata_snapshot(),
        "queries": queried_git_metadata_snapshot(),
    }


def validate_git_metadata() -> dict[str, str]:
    before = complete_git_metadata_snapshot()
    after = complete_git_metadata_snapshot()
    require(
        before == after,
        "Git metadata, configuration, routing, or replacement state changed across the bounded probe",
    )
    return {
        "alternates": "absent",
        "bounded_start_end_revalidation": "pass_not_atomic",
        "config_overlays": "absent",
        "grafts": "absent",
        "object_format": "sha1",
        "replacement_refs": "absent",
        "unsigned_commit_and_tag_policy": "false",
    }


def validate_complete_probe_endpoints(
    head_before: str,
    status_before: bytes,
    metadata_before: dict[str, Any],
    head_after: str,
    status_after: bytes,
    metadata_after: dict[str, Any],
) -> None:
    require(
        head_after == head_before
        and status_after == status_before
        and metadata_after == metadata_before,
        "HEAD, worktree status, or Git metadata changed across the complete checker probe",
    )


def validate_live_authorities(head: str, *, candidate: bool) -> dict[str, Any]:
    validate_authority_specification()
    root_fd, root_identity = open_canonical_root(ROOT)
    aggregate = 0
    pending: list[str] = []
    states: dict[str, int] = {}
    try:
        for authority in EXPECTED_AUTHORITIES:
            try:
                raw = stable_read(root_fd, authority)
            except FileNotFoundError:
                require(
                    not candidate and not authority.authoring_required,
                    f"required authority absent: {authority.path}",
                )
                pending.append(authority.path)
                states["pending_evidence_absent"] = (
                    states.get("pending_evidence_absent", 0) + 1
                )
                continue
            aggregate += len(raw)
            require(aggregate <= AGGREGATE_LIMIT, "authority aggregate exceeds 16 MiB")
            live_oid = git_oid("blob", raw)
            entry = tree_entry(head, authority.path)
            state = "prospective_not_in_head"
            if entry is not None:
                mode, oid = entry
                committed = verify_object("blob", oid, LIMITS[authority.limit_class])
                state = (
                    "bound_to_head"
                    if mode == authority.git_mode
                    and oid == live_oid
                    and committed == raw
                    else "worktree_differs_from_head"
                )
            require(
                not candidate or state == "bound_to_head",
                f"unbound candidate authority: {authority.path}",
            )
            states[state] = states.get(state, 0) + 1
    finally:
        recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)
    require(pending in ([], [SPECIAL_PATH]), "unexpected pending authority")
    return {
        "aggregate_bytes": aggregate,
        "pending": pending,
        "states": dict(sorted(states.items())),
    }


def duplicate_rejecting_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> NoReturn:
    raise ContractError(f"non-finite JSON constant is forbidden: {value}")


def parse_json(raw: bytes, label: str, *, maximum: int = ORDINARY_LIMIT) -> Any:
    require(0 < len(raw) <= maximum, f"{label} exceeds JSON bound")
    try:
        return json.loads(
            raw,
            object_pairs_hook=duplicate_rejecting_object,
            parse_constant=reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"{label} is not duplicate-free JSON: {error}") from None


def exact_keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    require(type(value) is dict and set(value) == expected, f"{label} keys changed")
    return value


def compact_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def pretty_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def hosted_pretty_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def parse_hosted_canonical_json(raw: bytes, label: str, maximum: int) -> Any:
    value = parse_json(raw, label, maximum=maximum)
    require(
        raw == hosted_pretty_json(value),
        f"{label} is not canonical sorted indented ASCII JSON",
    )
    return value


def descriptor(raw: bytes, path: str) -> dict[str, Any]:
    return {
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_bytes": len(raw),
    }


def decode_binding(value: Any, label: str, maximum: int) -> bytes:
    binding = exact_keys(value, {"body_base64", "sha256", "size_bytes"}, label)
    require(
        type(binding["body_base64"]) is str
        and type(binding["sha256"]) is str
        and SHA256_RE.fullmatch(binding["sha256"]) is not None
        and type(binding["size_bytes"]) is int
        and 0 <= binding["size_bytes"] <= maximum,
        f"{label} shape changed",
    )
    try:
        raw = base64.b64decode(binding["body_base64"], validate=True)
    except (ValueError, binascii.Error):
        raise ContractError(f"{label} is not canonical base64") from None
    require(
        base64.b64encode(raw).decode("ascii") == binding["body_base64"]
        and len(raw) == binding["size_bytes"]
        and hashlib.sha256(raw).hexdigest() == binding["sha256"],
        f"{label} bytes changed",
    )
    return raw


def parse_utc_timestamp(value: Any, label: str) -> datetime:
    require(
        type(value) is str
        and re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z",
            value,
        )
        is not None,
        f"{label} timestamp grammar changed",
    )
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ContractError(f"{label} timestamp changed") from None
    require(parsed.tzinfo == timezone.utc, f"{label} is not UTC")
    return parsed


def decode_capture_row(value: Any, label: str) -> tuple[dict[str, Any], bytes]:
    row = exact_keys(
        value,
        {
            "body_base64",
            "body_sha256",
            "body_size_bytes",
            "logical_request",
            "media_type",
            "page",
            "path",
            "redirect",
            "repetition",
            "response_kind",
            "status_code",
        },
        label,
    )
    require(
        type(row["body_base64"]) is str
        and type(row["body_sha256"]) is str
        and SHA256_RE.fullmatch(row["body_sha256"]) is not None
        and type(row["body_size_bytes"]) is int
        and 0 <= row["body_size_bytes"] <= RECORD_LIMIT
        and type(row["logical_request"]) is str
        and re.fullmatch(r"[a-z0-9_]+", row["logical_request"]) is not None
        and type(row["media_type"]) is str
        and 0 < len(row["media_type"]) <= 256
        and type(row["page"]) is int
        and row["page"] >= 0
        and type(row["path"]) is str
        and row["path"].startswith(f"/repos/{REPOSITORY}/")
        and all(" " <= character <= "~" for character in row["path"])
        and type(row["repetition"]) is int
        and row["repetition"] in {1, 2}
        and row["response_kind"] in {"json", "log", "zip"}
        and type(row["status_code"]) is int
        and row["status_code"] == 200,
        f"{label} shape changed",
    )
    redirect = row["redirect"]
    if redirect is not None:
        redirect = exact_keys(
            redirect,
            {"status_code", "target_host", "target_url_sha256"},
            f"{label} redirect",
        )
        require(
            type(redirect["status_code"]) is int
            and redirect["status_code"] in {301, 302, 303, 307, 308}
            and type(redirect["target_host"]) is str
            and 0 < len(redirect["target_host"]) <= 253
            and type(redirect["target_url_sha256"]) is str
            and SHA256_RE.fullmatch(redirect["target_url_sha256"]) is not None,
            f"{label} redirect changed",
        )
    try:
        raw = base64.b64decode(row["body_base64"], validate=True)
    except (ValueError, binascii.Error):
        raise ContractError(f"{label} body is not base64") from None
    require(
        base64.b64encode(raw).decode("ascii") == row["body_base64"]
        and len(raw) == row["body_size_bytes"]
        and hashlib.sha256(raw).hexdigest() == row["body_sha256"],
        f"{label} body binding changed",
    )
    return row, raw


def paired_capture_bodies(
    decoded: list[tuple[dict[str, Any], bytes]], logical: str
) -> list[tuple[dict[str, Any], bytes]]:
    rows = [(row, raw) for row, raw in decoded if row["logical_request"] == logical]
    require(rows, f"capture logical request is absent: {logical}")
    grouped: dict[tuple[int, str], list[tuple[dict[str, Any], bytes]]] = {}
    for row, raw in rows:
        grouped.setdefault((row["page"], row["path"]), []).append((row, raw))
    result: list[tuple[dict[str, Any], bytes]] = []
    for key in sorted(grouped):
        pair = sorted(grouped[key], key=lambda item: item[0]["repetition"])
        require(
            [row["repetition"] for row, _raw in pair] == [1, 2],
            f"capture request lacks two repetitions: {logical}",
        )
        left, right = pair
        require(
            left[1] == right[1]
            and all(
                left[0][field] == right[0][field]
                for field in (
                    "body_sha256",
                    "body_size_bytes",
                    "logical_request",
                    "media_type",
                    "page",
                    "path",
                    "response_kind",
                    "status_code",
                )
            )
            and (left[0]["redirect"] is None) == (right[0]["redirect"] is None)
            and (
                left[0]["redirect"] is None
                or (
                    left[0]["redirect"]["status_code"]
                    == right[0]["redirect"]["status_code"]
                    and left[0]["redirect"]["target_host"]
                    == right[0]["redirect"]["target_host"]
                )
            ),
            f"capture repetitions disagree: {logical}",
        )
        result.append(left)
    return result


def validate_predecessor_capture(raw: bytes, hosted_tool_raw: bytes) -> dict[str, Any]:
    value = parse_hosted_canonical_json(
        raw,
        "terminal C9 predecessor capture",
        SPECIAL_LIMIT,
    )
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v8_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        "terminal C9 capture",
    )
    require(
        root["capture_tool"] == descriptor(hosted_tool_raw, HOSTED_TOOL)
        and root["immutable_v8_primitives"] == CAPTURE_V8
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS
        and root["phase"] == "predecessor_failure"
        and root["repository"] == REPOSITORY
        and root["runs"] == PREDECESSOR_RUNS
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v11"
        and root["schema_revision"] == 11
        and root["subject"]
        == {"predecessor_commit": C9_COMMIT, "predecessor_tree": C9_TREE},
        "terminal C9 capture identity changed",
    )

    captures = root["captures"]
    require(
        type(captures) is list and 0 < len(captures) <= CAPTURE_ROW_LIMIT,
        "terminal C9 capture row count is outside the bound",
    )
    decoded = [
        decode_capture_row(item, f"terminal C9 capture row {index}")
        for index, item in enumerate(captures)
    ]
    require(
        sum(len(body) for _row, body in decoded) <= CAPTURE_BODY_LIMIT,
        "terminal C9 decoded bodies exceed the aggregate bound",
    )
    keys = [
        (row["logical_request"], row["repetition"], row["page"], row["path"])
        for row, _body in decoded
    ]
    require(keys == sorted(set(keys)), "terminal C9 capture rows are not sorted unique")

    retry_keys: list[tuple[str, int, int, str, int]] = []
    require(type(root["retry_events"]) is list, "capture retry ledger is not an array")
    for item in root["retry_events"]:
        event = exact_keys(
            item,
            {
                "attempt",
                "category",
                "logical_request",
                "page",
                "path",
                "repetition",
                "response_sha256",
                "response_size_bytes",
            },
            "capture retry event",
        )
        require(
            type(event["attempt"]) is int
            and event["attempt"] in {1, 2}
            and event["category"]
            in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(event["logical_request"]) is str
            and re.fullmatch(r"[a-z0-9_]+", event["logical_request"]) is not None
            and type(event["page"]) is int
            and event["page"] >= 0
            and type(event["path"]) is str
            and event["path"].startswith(f"/repos/{REPOSITORY}/")
            and type(event["repetition"]) is int
            and event["repetition"] in {1, 2}
            and type(event["response_sha256"]) is str
            and SHA256_RE.fullmatch(event["response_sha256"]) is not None
            and type(event["response_size_bytes"]) is int
            and 0 <= event["response_size_bytes"] <= RECORD_LIMIT,
            "capture retry event changed",
        )
        retry_keys.append(
            (
                event["logical_request"],
                event["repetition"],
                event["page"],
                event["path"],
                event["attempt"],
            )
        )
    require(
        retry_keys == sorted(set(retry_keys)), "capture retries are not sorted unique"
    )
    capture_keys = set(keys)
    retry_groups: dict[tuple[str, int, int, str], list[int]] = {}
    for logical, repetition, page, path, attempt in retry_keys:
        key = (logical, repetition, page, path)
        require(key in capture_keys, "retry event has no successful capture row")
        retry_groups.setdefault(key, []).append(attempt)
    require(
        all(
            attempts == list(range(1, len(attempts) + 1))
            for attempts in retry_groups.values()
        ),
        "capture retry attempts are not consecutive",
    )

    repository_ids: set[int] = set()
    observed_failed: dict[str, list[int]] = {}
    allowed_logicals: set[str] = set()
    routes = {
        "predecessor_ci": ("CI", ".github/workflows/ci.yml", "push"),
        "predecessor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
        ),
        "predecessor_contract": (
            "KSG M1a composite v9",
            ".github/workflows/ksg-m1a-composite-v9.yml",
            "push",
        ),
    }
    for role in sorted(PREDECESSOR_RUNS):
        run_id = PREDECESSOR_RUNS[role]
        run_logical = f"{role}_run"
        allowed_logicals.add(run_logical)
        run_rows = paired_capture_bodies(decoded, run_logical)
        require(
            len(run_rows) == 1
            and run_rows[0][0]["page"] == 0
            and run_rows[0][0]["path"] == f"/repos/{REPOSITORY}/actions/runs/{run_id}"
            and run_rows[0][0]["response_kind"] == "json",
            f"{role} run row changed",
        )
        run = parse_json(run_rows[0][1], f"{role} run body")
        require(type(run) is dict, f"{role} run body is not an object")
        repository = run.get("repository")
        head_repository = run.get("head_repository")
        require(
            run.get("id") == run_id
            and type(run.get("id")) is int
            and run.get("head_sha") == C9_COMMIT
            and run.get("head_branch") == "main"
            and run.get("run_attempt") == 1
            and type(run.get("run_attempt")) is int
            and run.get("status") == "completed"
            and run.get("conclusion") == PREDECESSOR_CONCLUSIONS[role]
            and (run.get("name"), run.get("path"), run.get("event")) == routes[role]
            and type(repository) is dict
            and repository.get("full_name") == REPOSITORY
            and type(repository.get("id")) is int
            and repository.get("id") > 0
            and type(head_repository) is dict
            and head_repository.get("full_name") == REPOSITORY
            and head_repository.get("id") == repository.get("id"),
            f"{role} terminal run identity changed",
        )
        repository_id = repository["id"]
        repository_ids.add(repository_id)

        jobs_logical = f"{role}_jobs"
        allowed_logicals.add(jobs_logical)
        job_pages = paired_capture_bodies(decoded, jobs_logical)
        require(
            [row["page"] for row, _body in job_pages]
            == list(range(1, len(job_pages) + 1)),
            f"{role} job pagination changed",
        )
        require(
            all(
                row["path"]
                == f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs?per_page=100&page={row['page']}"
                and row["response_kind"] == "json"
                for row, _body in job_pages
            ),
            f"{role} job page route changed",
        )
        jobs: list[dict[str, Any]] = []
        total_count: int | None = None
        for row, body in job_pages:
            page = parse_json(body, f"{role} jobs page {row['page']}")
            require(
                type(page) is dict
                and set(page) == {"jobs", "total_count"}
                and type(page["jobs"]) is list
                and type(page["total_count"]) is int
                and page["total_count"] >= 0,
                f"{role} jobs page changed",
            )
            if total_count is None:
                total_count = page["total_count"]
            require(page["total_count"] == total_count, f"{role} job total changed")
            jobs.extend(page["jobs"])
        require(total_count == len(jobs), f"{role} job total is incomplete")
        job_ids: list[int] = []
        failed_ids: list[int] = []
        for job in jobs:
            require(type(job) is dict, f"{role} job is not an object")
            job_id = job.get("id")
            require(
                type(job_id) is int
                and job_id > 0
                and job.get("run_id") == run_id
                and job.get("run_attempt") == 1
                and job.get("head_sha") == C9_COMMIT
                and job.get("status") == "completed"
                and job.get("conclusion")
                in {"success", "failure", "cancelled", "skipped", "neutral"},
                f"{role} job identity changed",
            )
            job_ids.append(job_id)
            if job.get("conclusion") == "failure":
                failed_ids.append(job_id)
        require(len(job_ids) == len(set(job_ids)), f"{role} job IDs are duplicated")
        observed_failed[role] = sorted(failed_ids)

        artifacts_logical = f"{role}_artifacts"
        allowed_logicals.add(artifacts_logical)
        artifact_pages = paired_capture_bodies(decoded, artifacts_logical)
        require(
            [row["page"] for row, _body in artifact_pages]
            == list(range(1, len(artifact_pages) + 1)),
            f"{role} artifact pagination changed",
        )
        require(
            all(
                row["path"]
                == f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100&page={row['page']}"
                and row["response_kind"] == "json"
                for row, _body in artifact_pages
            ),
            f"{role} artifact page route changed",
        )
        artifacts: list[dict[str, Any]] = []
        artifact_total: int | None = None
        for row, body in artifact_pages:
            page = parse_json(body, f"{role} artifacts page {row['page']}")
            require(
                type(page) is dict
                and set(page) == {"artifacts", "total_count"}
                and type(page["artifacts"]) is list
                and type(page["total_count"]) is int
                and page["total_count"] >= 0,
                f"{role} artifact page changed",
            )
            if artifact_total is None:
                artifact_total = page["total_count"]
            require(
                page["total_count"] == artifact_total, f"{role} artifact total changed"
            )
            artifacts.extend(page["artifacts"])
        require(
            artifact_total == len(artifacts), f"{role} artifact total is incomplete"
        )
        artifact_ids: list[int] = []
        artifact_names: list[str] = []
        for artifact in artifacts:
            require(type(artifact) is dict, f"{role} artifact is not an object")
            artifact_id = artifact.get("id")
            artifact_name = artifact.get("name")
            workflow_run = artifact.get("workflow_run")
            require(
                type(artifact_id) is int
                and artifact_id > 0
                and type(artifact_name) is str
                and artifact_name
                and artifact.get("expired") is False
                and type(artifact.get("size_in_bytes")) is int
                and artifact.get("size_in_bytes") > 0
                and type(workflow_run) is dict
                and workflow_run.get("id") == run_id
                and workflow_run.get("head_sha") == C9_COMMIT
                and workflow_run.get("head_branch") == "main"
                and workflow_run.get("repository_id") == repository_id
                and workflow_run.get("head_repository_id") == repository_id,
                f"{role} artifact join changed",
            )
            artifact_ids.append(artifact_id)
            artifact_names.append(artifact_name)
        require(
            len(artifact_ids) == len(set(artifact_ids))
            and len(artifact_names) == len(set(artifact_names))
            and (role == "predecessor_ci" or artifact_ids == []),
            f"{role} artifact inventory changed",
        )
        for artifact_id in sorted(artifact_ids):
            logical = f"{role}_artifact_{artifact_id}"
            allowed_logicals.add(logical)
            rows = paired_capture_bodies(decoded, logical)
            require(
                len(rows) == 1
                and rows[0][0]["page"] == 0
                and rows[0][0]["path"]
                == f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
                and rows[0][0]["response_kind"] == "zip",
                f"{role} artifact payload route changed",
            )

        for failed_job_id in sorted(failed_ids):
            logical = f"{role}_failed_job_{failed_job_id}_log"
            allowed_logicals.add(logical)
            rows = paired_capture_bodies(decoded, logical)
            require(
                len(rows) == 1
                and rows[0][0]["page"] == 0
                and rows[0][0]["path"]
                == f"/repos/{REPOSITORY}/actions/jobs/{failed_job_id}/logs"
                and rows[0][0]["response_kind"] == "log"
                and rows[0][1] != b"",
                f"{role} failed-job log route changed",
            )

    require(len(repository_ids) == 1, "terminal runs disagree on repository identity")
    require(
        observed_failed == PREDECESSOR_FAILED_JOBS,
        "terminal failed-job partition changed",
    )
    require(
        {row["logical_request"] for row, _body in decoded} == allowed_logicals,
        "terminal capture contains an unaccounted logical request",
    )
    return {
        "capture_rows": len(decoded),
        "failed_job_partition": observed_failed,
        "repository_id_consistent": True,
        "retry_events": len(retry_keys),
    }


def decode_capture_document(
    root: dict[str, Any], label: str
) -> tuple[list[tuple[dict[str, Any], bytes]], int]:
    captures = root["captures"]
    require(
        type(captures) is list and 0 < len(captures) <= CAPTURE_ROW_LIMIT,
        f"{label} row count is outside the bound",
    )
    decoded = [
        decode_capture_row(item, f"{label} row {index}")
        for index, item in enumerate(captures)
    ]
    require(
        sum(len(body) for _row, body in decoded) <= CAPTURE_BODY_LIMIT,
        f"{label} decoded bodies exceed the aggregate bound",
    )
    keys = [
        (row["logical_request"], row["repetition"], row["page"], row["path"])
        for row, _body in decoded
    ]
    require(keys == sorted(set(keys)), f"{label} rows are not sorted unique")
    retries = root["retry_events"]
    require(type(retries) is list, f"{label} retry ledger is not an array")
    retry_keys: list[tuple[str, int, int, str, int]] = []
    for item in retries:
        event = exact_keys(
            item,
            {
                "attempt",
                "category",
                "logical_request",
                "page",
                "path",
                "repetition",
                "response_sha256",
                "response_size_bytes",
            },
            f"{label} retry event",
        )
        require(
            type(event["attempt"]) is int
            and event["attempt"] in {1, 2}
            and event["category"]
            in {"http_429", "http_502", "http_503", "http_504", "transport"}
            and type(event["logical_request"]) is str
            and re.fullmatch(r"[a-z0-9_]+", event["logical_request"]) is not None
            and type(event["page"]) is int
            and event["page"] >= 0
            and type(event["path"]) is str
            and event["path"].startswith(f"/repos/{REPOSITORY}/")
            and type(event["repetition"]) is int
            and event["repetition"] in {1, 2}
            and type(event["response_sha256"]) is str
            and SHA256_RE.fullmatch(event["response_sha256"]) is not None
            and type(event["response_size_bytes"]) is int
            and 0 <= event["response_size_bytes"] <= SPECIAL_LIMIT,
            f"{label} retry event changed",
        )
        retry_keys.append(
            (
                event["logical_request"],
                event["repetition"],
                event["page"],
                event["path"],
                event["attempt"],
            )
        )
    require(
        retry_keys == sorted(set(retry_keys)), f"{label} retries are not sorted unique"
    )
    capture_keys = set(keys)
    retry_groups: dict[tuple[str, int, int, str], list[int]] = {}
    for logical, repetition, page, path, attempt in retry_keys:
        key = (logical, repetition, page, path)
        require(key in capture_keys, f"{label} retry has no successful response")
        retry_groups.setdefault(key, []).append(attempt)
    require(
        all(
            values == list(range(1, len(values) + 1))
            for values in retry_groups.values()
        ),
        f"{label} retry attempts are not consecutive",
    )
    return decoded, len(retry_keys)


def paged_object_array(
    decoded: list[tuple[dict[str, Any], bytes]],
    logical: str,
    route_prefix: str,
    array_key: str,
) -> list[dict[str, Any]]:
    pages = paired_capture_bodies(decoded, logical)
    require(
        0 < len(pages) <= 64
        and [row["page"] for row, _body in pages] == list(range(1, len(pages) + 1))
        and all(
            row["path"] == f"{route_prefix}{row['page']}"
            and row["response_kind"] == "json"
            for row, _body in pages
        ),
        f"{logical} pagination or route changed",
    )
    values: list[dict[str, Any]] = []
    total: int | None = None
    final_items: list[Any] | None = None
    for row, body in pages:
        page = parse_json(body, f"{logical} page {row['page']}")
        require(
            type(page) is dict
            and set(page) == {array_key, "total_count"}
            and type(page[array_key]) is list
            and type(page["total_count"]) is int
            and page["total_count"] >= 0,
            f"{logical} page shape changed",
        )
        final_items = page[array_key]
        if total is None:
            total = page["total_count"]
        require(page["total_count"] == total, f"{logical} total changed across pages")
        require(
            all(type(item) is dict for item in page[array_key]),
            f"{logical} contains a non-object",
        )
        values.extend(page[array_key])
    require(
        total == len(values) and final_items == [],
        f"{logical} pagination is incomplete or lacks its terminal empty page",
    )
    return values


def paged_json_array(
    decoded: list[tuple[dict[str, Any], bytes]], logical: str, route_prefix: str
) -> list[dict[str, Any]]:
    pages = paired_capture_bodies(decoded, logical)
    require(
        0 < len(pages) <= 64
        and [row["page"] for row, _body in pages] == list(range(1, len(pages) + 1))
        and all(
            row["path"] == f"{route_prefix}{row['page']}"
            and row["response_kind"] == "json"
            for row, _body in pages
        ),
        f"{logical} pagination or route changed",
    )
    result: list[dict[str, Any]] = []
    final_page: list[Any] | None = None
    for row, body in pages:
        page = parse_json(body, f"{logical} page {row['page']}")
        require(
            type(page) is list and all(type(item) is dict for item in page),
            f"{logical} page is not an object array",
        )
        final_page = page
        result.extend(page)
    require(final_page == [], f"{logical} lacks its terminal empty page")
    return result


def validate_zip_payload(raw: bytes, label: str) -> dict[str, bytes]:
    require(0 < len(raw) <= RECORD_LIMIT, f"{label} zip size changed")
    # Preflight the non-ZIP64 end record before ZipFile constructs its member
    # objects.  The input-byte cap alone would otherwise permit a central
    # directory with far more entries than this contract accepts.
    eocd_signature = b"PK\x05\x06"
    minimum_eocd_size = 22
    search_start = max(0, len(raw) - minimum_eocd_size - 65_535)
    eocd_offset = raw.rfind(eocd_signature, search_start)
    require(
        eocd_offset >= 0 and eocd_offset + minimum_eocd_size <= len(raw),
        f"{label} lacks a bounded ZIP end record",
    )
    (
        disk_number,
        central_directory_disk,
        entries_on_disk,
        entry_count,
        central_directory_size,
        central_directory_offset,
        comment_size,
    ) = struct.unpack_from("<HHHHIIH", raw, eocd_offset + 4)
    require(
        disk_number == 0
        and central_directory_disk == 0
        and entries_on_disk == entry_count
        and 0 < entry_count <= 10_000
        and entry_count != 0xFFFF
        and central_directory_size != 0xFFFFFFFF
        and central_directory_offset != 0xFFFFFFFF
        and central_directory_offset + central_directory_size == eocd_offset
        and eocd_offset + minimum_eocd_size + comment_size == len(raw),
        f"{label} ZIP end record, inventory bound, or trailing bytes changed",
    )
    try:
        with zipfile.ZipFile(io.BytesIO(raw), "r") as archive:
            infos = archive.infolist()
            require(
                len(infos) == entry_count,
                f"{label} zip inventory changed",
            )
            result: dict[str, bytes] = {}
            total = 0
            # Central-directory safety and the aggregate expansion ceiling are
            # established for every member before the first decompression.
            for info in infos:
                path = info.filename
                unix_type = (info.external_attr >> 16) & 0o170000
                require(
                    not info.is_dir()
                    and not info.flag_bits & 0x1
                    and info.compress_type in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    and unix_type in {0, stat.S_IFREG}
                    and path
                    and "\x00" not in path
                    and "\\" not in path
                    and not path.startswith("/")
                    and all(
                        component not in {"", ".", ".."}
                        for component in path.split("/")
                    )
                    and path not in result
                    and 0 <= info.file_size <= RECORD_LIMIT,
                    f"{label} zip member is unsafe",
                )
                total += info.file_size
                require(
                    total <= CAPTURE_BODY_LIMIT, f"{label} expanded zip exceeds bound"
                )
                result[path] = b""
            # ZipExtFile verifies the member CRC.  Reads begin only after all
            # advertised expanded sizes and shapes passed the preflight, and no
            # individual read request or accumulated result can exceed the
            # established contract.
            for info in infos:
                chunks: list[bytes] = []
                remaining = info.file_size
                with archive.open(info, "r") as member:
                    while remaining:
                        chunk = member.read(min(ZIP_MEMBER_READ_CHUNK, remaining))
                        require(
                            0 < len(chunk) <= min(ZIP_MEMBER_READ_CHUNK, remaining),
                            f"{label} zip member is short or overlong",
                        )
                        chunks.append(chunk)
                        remaining -= len(chunk)
                    require(
                        member.read(1) == b"",
                        f"{label} zip member exceeds its advertised size",
                    )
                body = b"".join(chunks)
                require(len(body) == info.file_size, f"{label} zip member is short")
                result[info.filename] = body
            return result
    except (
        EOFError,
        NotImplementedError,
        OSError,
        RuntimeError,
        zipfile.BadZipFile,
        zipfile.LargeZipFile,
        zlib.error,
    ):
        raise ContractError(f"{label} is not a bounded safe zip archive") from None


def validate_successor_capture(
    raw: bytes,
    hosted_tool_raw: bytes,
    c11: str,
    c11_tree: str,
) -> dict[str, Any]:
    value = parse_hosted_canonical_json(
        raw,
        "C11 successor capture",
        RECORD_LIMIT,
    )
    root = exact_keys(
        value,
        {
            "capture_tool",
            "captures",
            "immutable_v8_primitives",
            "nonimplications",
            "phase",
            "repository",
            "retry_events",
            "runs",
            "schema",
            "schema_revision",
            "subject",
        },
        "C11 successor capture",
    )
    runs = root["runs"]
    require(
        root["capture_tool"] == descriptor(hosted_tool_raw, HOSTED_TOOL)
        and root["immutable_v8_primitives"] == CAPTURE_V8
        and root["nonimplications"] == CAPTURE_NONIMPLICATIONS
        and root["phase"] == "successor_qualification"
        and root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-hosted-capture/v11"
        and root["schema_revision"] == 11
        and root["subject"]
        == {
            "predecessor_commit": C9_COMMIT,
            "predecessor_tree": C9_TREE,
            "successor_commit": c11,
            "successor_tree": c11_tree,
        }
        and type(runs) is dict
        and set(runs) == {"successor_ci", "successor_codeql", "successor_contract"}
        and all(type(run_id) is int and run_id > 0 for run_id in runs.values())
        and len(set(runs.values())) == 3,
        "C11 successor capture identity changed",
    )
    decoded, retry_count = decode_capture_document(root, "C11 successor capture")
    expected_routes = {
        "successor_ci": ("CI", ".github/workflows/ci.yml", "push", 45),
        "successor_codeql": (
            "Push on main",
            "dynamic/github-code-scanning/codeql",
            "dynamic",
            4,
        ),
        "successor_contract": (
            "KSG M1a composite v11",
            WORKFLOW,
            "push",
            1,
        ),
    }
    expected_artifacts = {
        "successor_ci": {
            "coverage-lcov",
            f"post-commit-source-state-v2-{c11}",
            "workspace-sbom",
        },
        "successor_codeql": set(),
        "successor_contract": {f"ksg-m1a-composite-v11-static-{c11}"},
    }
    repository_ids: set[int] = set()
    identifier_domains: dict[str, set[int]] = {
        "run": set(),
        "job": set(),
        "artifact": set(),
    }
    allowed_logicals: set[str] = set()
    codeql_job_names: set[str] = set()
    for role in sorted(runs):
        run_id = runs[role]
        require(run_id not in identifier_domains["run"], "successor run IDs overlap")
        identifier_domains["run"].add(run_id)
        run_logical = f"{role}_run"
        allowed_logicals.add(run_logical)
        run_rows = paired_capture_bodies(decoded, run_logical)
        require(
            len(run_rows) == 1
            and run_rows[0][0]["page"] == 0
            and run_rows[0][0]["path"] == f"/repos/{REPOSITORY}/actions/runs/{run_id}"
            and run_rows[0][0]["response_kind"] == "json",
            f"{role} run route changed",
        )
        run = parse_json(run_rows[0][1], f"{role} run")
        repository = run.get("repository") if type(run) is dict else None
        head_repository = run.get("head_repository") if type(run) is dict else None
        name, path, event, expected_jobs = expected_routes[role]
        require(
            type(run) is dict
            and run.get("id") == run_id
            and run.get("head_sha") == c11
            and run.get("head_branch") == "main"
            and run.get("run_attempt") == 1
            and type(run.get("run_attempt")) is int
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and (run.get("name"), run.get("path"), run.get("event"))
            == (name, path, event)
            and type(repository) is dict
            and repository.get("full_name") == REPOSITORY
            and type(repository.get("id")) is int
            and repository.get("id") > 0
            and type(head_repository) is dict
            and head_repository.get("full_name") == REPOSITORY
            and head_repository.get("id") == repository.get("id"),
            f"{role} attempt-1 terminal success identity changed",
        )
        repository_id = repository["id"]
        repository_ids.add(repository_id)

        jobs_logical = f"{role}_jobs"
        allowed_logicals.add(jobs_logical)
        jobs = paged_object_array(
            decoded,
            jobs_logical,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/attempts/1/jobs?per_page=100&page=",
            "jobs",
        )
        require(len(jobs) == expected_jobs, f"{role} job count changed")
        for job in jobs:
            job_id = job.get("id")
            steps = job.get("steps")
            require(
                type(job_id) is int
                and job_id > 0
                and job_id not in identifier_domains["job"]
                and job.get("run_id") == run_id
                and job.get("run_attempt") == 1
                and job.get("head_sha") == c11
                and job.get("status") == "completed"
                and job.get("conclusion") == "success"
                and type(steps) is list
                and steps
                and all(
                    type(step) is dict
                    and step.get("status") == "completed"
                    and step.get("conclusion") in {"success", "skipped"}
                    for step in steps
                ),
                f"{role} contains an adverse or foreign job",
            )
            identifier_domains["job"].add(job_id)
            if role == "successor_codeql":
                require(type(job.get("name")) is str, "CodeQL job name changed")
                codeql_job_names.add(job["name"])

        artifacts_logical = f"{role}_artifacts"
        allowed_logicals.add(artifacts_logical)
        artifacts = paged_object_array(
            decoded,
            artifacts_logical,
            f"/repos/{REPOSITORY}/actions/runs/{run_id}/artifacts?per_page=100&page=",
            "artifacts",
        )
        observed_names: set[str] = set()
        for artifact in artifacts:
            artifact_id = artifact.get("id")
            artifact_name = artifact.get("name")
            workflow_run = artifact.get("workflow_run")
            require(
                type(artifact_id) is int
                and artifact_id > 0
                and artifact_id not in identifier_domains["artifact"]
                and type(artifact_name) is str
                and artifact_name not in observed_names
                and artifact.get("expired") is False
                and type(artifact.get("size_in_bytes")) is int
                and artifact.get("size_in_bytes") > 0
                and type(workflow_run) is dict
                and workflow_run.get("id") == run_id
                and workflow_run.get("head_sha") == c11
                and workflow_run.get("head_branch") == "main"
                and workflow_run.get("repository_id") == repository_id
                and workflow_run.get("head_repository_id") == repository_id,
                f"{role} artifact join changed",
            )
            identifier_domains["artifact"].add(artifact_id)
            observed_names.add(artifact_name)
            logical = f"{role}_artifact_{artifact_id}"
            allowed_logicals.add(logical)
            payloads = paired_capture_bodies(decoded, logical)
            require(
                len(payloads) == 1
                and payloads[0][0]["page"] == 0
                and payloads[0][0]["path"]
                == f"/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip"
                and payloads[0][0]["response_kind"] == "zip",
                f"{role} artifact payload route changed",
            )
            members = validate_zip_payload(
                payloads[0][1], f"{role} artifact {artifact_id}"
            )
            if role == "successor_contract":
                require(
                    set(members) == {"ksg-m1a-composite-v11-static.json"},
                    "dedicated-v11 static artifact members changed",
                )
                static_raw = members["ksg-m1a-composite-v11-static.json"]
                static_value = parse_json(static_raw, "dedicated-v11 static result")
                require(
                    static_raw == compact_json(static_value)
                    and type(static_value) is dict
                    and static_value.get("result") == "pass"
                    and static_value.get("head") == c11
                    and static_value.get("tree") == c11_tree
                    and static_value.get("lifecycle_phase") == "candidate",
                    "dedicated-v11 static result changed",
                )
        require(
            observed_names == expected_artifacts[role], f"{role} artifact names changed"
        )

    analysis_ids: set[int] = set()
    analyses_logical = "successor_codeql_analyses"
    allowed_logicals.add(analyses_logical)
    analyses = paged_json_array(
        decoded,
        analyses_logical,
        f"/repos/{REPOSITORY}/code-scanning/analyses?ref=refs%2Fheads%2Fmain&per_page=100&page=",
    )
    exact_head_analyses = [
        analysis
        for analysis in analyses
        if analysis.get("commit_sha") == c11
        and analysis.get("ref") == "refs/heads/main"
    ]
    languages = ("actions", "javascript-typescript", "python", "rust")
    observed_languages: set[str] = set()
    for analysis in exact_head_analyses:
        identifier = analysis.get("id")
        category = analysis.get("category")
        matches = [
            language for language in languages if category == f"/language:{language}"
        ]
        require(
            type(identifier) is int
            and identifier > 0
            and identifier not in analysis_ids
            and len(matches) == 1
            and matches[0] not in observed_languages
            and f"Analyze ({matches[0]})" in codeql_job_names
            and type(analysis.get("results_count")) is int
            and analysis.get("results_count") >= 0
            and type(analysis.get("rules_count")) is int
            and analysis.get("rules_count") > 0
            and analysis.get("error") in {"", None}
            and analysis.get("warning") in {"", None},
            "CodeQL exact-head analysis identity or language/job join changed",
        )
        analysis_ids.add(identifier)
        observed_languages.add(matches[0])
    require(
        len(exact_head_analyses) == 4
        and observed_languages == set(languages)
        and codeql_job_names == {f"Analyze ({language})" for language in languages},
        "CodeQL exact-C11 analysis/job roster changed",
    )
    alert_numbers: set[int] = set()
    for state in ("dismissed", "fixed", "open"):
        logical = f"successor_codeql_alerts_{state}"
        allowed_logicals.add(logical)
        alerts = paged_json_array(
            decoded,
            logical,
            f"/repos/{REPOSITORY}/code-scanning/alerts?state={state}&per_page=100&page=",
        )
        for alert in alerts:
            number = alert.get("number")
            require(
                alert.get("state") == state
                and type(number) is int
                and number > 0
                and number not in alert_numbers,
                f"CodeQL {state} alert partition changed or overlaps",
            )
            alert_numbers.add(number)
    require(len(repository_ids) == 1, "successor runs disagree on repository identity")
    require(
        {row["logical_request"] for row, _body in decoded} == allowed_logicals,
        "successor capture contains an unaccounted logical request",
    )
    return {
        "capture_rows": len(decoded),
        "codeql_analysis_count": len(analysis_ids),
        "repository_id_consistent": True,
        "retry_events": retry_count,
        "run_ids": dict(sorted(runs.items())),
    }


LOCAL_LIMITS = {
    "authority_aggregate_bytes": AGGREGATE_LIMIT,
    "command_stream_bytes": 8 * 1024 * 1024,
    "executable_bytes": 256 * 1024 * 1024,
    "ordinary_authority_bytes": ORDINARY_LIMIT,
    "record_bytes": RECORD_LIMIT,
    "terminal_c9_capture_bytes": SPECIAL_LIMIT,
    "version_stream_bytes": VERSION_LIMIT,
}
LOCAL_V8 = {
    "path": "scripts/capture-ksg-m1a-composite-v8-local-closure.py",
    "sha256": "b9b0a41cb2027d1cba464040843656bc2486e317f8cf1d3079cb58b02f7c6ba7",
    "size_bytes": 40_584,
}
LOCAL_ENVIRONMENT = {
    "GIT_CONFIG_GLOBAL": "<NULL_DEVICE>",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_TERMINAL_PROMPT": "0",
    "LANG": "C",
    "LC_ALL": "C",
    "PATH": "<SANITIZED_TOOL_PATH>",
    "PYTHONDONTWRITEBYTECODE": "1",
    "TEXMFCACHE": "<PRIVATE_TEMP_TEXMF_CACHE>",
    "TEXMFCONFIG": "<PRIVATE_TEMP_TEXMF_CONFIG>",
    "TEXMFHOME": "<PRIVATE_TEMP_TEXMF_HOME>",
    "TEXMFVAR": "<PRIVATE_TEMP_TEXMF_VAR>",
    "TMPDIR": "<PRIVATE_TEMP_ROOT>",
    "TZ": "UTC",
    "XDG_CACHE_HOME": "<PRIVATE_TEMP_XDG_CACHE>",
    "XDG_CONFIG_HOME": "<PRIVATE_TEMP_XDG_CONFIG>",
    "XDG_DATA_HOME": "<PRIVATE_TEMP_XDG_DATA>",
}
LOCAL_NONIMPLICATIONS = [
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
LOCAL_TOOL_VERSIONS = {
    "bash": ["bash", "--version"],
    "chktex": ["chktex", "--version"],
    "fc-match": ["fc-match", "--version"],
    "git": ["git", "--version"],
    "just": ["just", "--version"],
    "lacheck": ["lacheck", "--version"],
    "latexmk": ["latexmk", "--version"],
    "lualatex": ["lualatex", "--version"],
    "pdfinfo": ["pdfinfo", "-v"],
    "pdffonts": ["pdffonts", "-v"],
    "pdftocairo": ["pdftocairo", "-v"],
    "pdftotext": ["pdftotext", "-v"],
    "python3": ["python3", "--version"],
    "rg": ["rg", "--version"],
    "rsvg-convert": ["rsvg-convert", "--version"],
    "xmllint": ["xmllint", "--version"],
}


def validate_local_snapshot(
    value: Any, c11: str, c11_tree: str, label: str
) -> datetime:
    snapshot = exact_keys(
        value,
        {
            "alternates",
            "common_dir",
            "config_overlays",
            "git_dir",
            "grafts",
            "head",
            "http_alternates",
            "info_attributes_rules",
            "info_exclude_rules",
            "message",
            "object_format",
            "observed_at",
            "parent",
            "replacement_refs",
            "shallow",
            "status",
            "tree",
            "worktree_root",
        },
        f"{label} local snapshot",
    )
    require(
        snapshot["alternates"] == "absent"
        and snapshot["common_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["config_overlays"] == "absent"
        and snapshot["git_dir"] == "<REPOSITORY_ROOT>/.git"
        and snapshot["grafts"] == "absent"
        and snapshot["head"] == c11
        and snapshot["http_alternates"] == "absent"
        and snapshot["info_attributes_rules"] == "absent"
        and snapshot["info_exclude_rules"] == "absent"
        and snapshot["message"] == C11_MESSAGE
        and snapshot["object_format"] == "sha1"
        and snapshot["parent"] == C9_COMMIT
        and snapshot["replacement_refs"] == []
        and snapshot["shallow"] == "absent"
        and snapshot["tree"] == c11_tree
        and snapshot["worktree_root"] == "<REPOSITORY_ROOT>"
        and decode_binding(snapshot["status"], f"{label} Git status", 0) == b"",
        f"{label} local snapshot identity changed",
    )
    return parse_utc_timestamp(snapshot["observed_at"], f"{label} observation")


def validate_local_evidence(raw: bytes, c11: str, c11_tree: str) -> dict[str, Any]:
    value = parse_json(raw, "L11 local closure", maximum=RECORD_LIMIT)
    require(raw == pretty_json(value), "L11 local closure is not canonical pretty JSON")
    root = exact_keys(
        value,
        {
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
        },
        "L11 local closure",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-local-closure/v11"
        and root["schema_revision"] == 11
        and root["limits"] == LOCAL_LIMITS
        and root["immutable_v8_primitives"] == LOCAL_V8
        and root["nonimplications"] == LOCAL_NONIMPLICATIONS,
        "L11 root identity changed",
    )
    subject = exact_keys(
        root["subject"],
        {"c9_parent", "c11_commit", "c11_message", "c11_tree"},
        "L11 subject",
    )
    require(
        subject
        == {
            "c9_parent": C9_COMMIT,
            "c11_commit": c11,
            "c11_message": C11_MESSAGE,
            "c11_tree": c11_tree,
        },
        "L11 subject differs from exact C11",
    )

    authorities = root["authorities"]
    require(
        type(authorities) is list
        and len(authorities) == len(EXPECTED_AUTHORITIES)
        and [item.get("path") for item in authorities]
        == [authority.path for authority in EXPECTED_AUTHORITIES],
        "L11 authority roster changed",
    )
    c11_entries = recursive_tree_entries(c11)
    aggregate = 0
    for item, expected in zip(authorities, EXPECTED_AUTHORITIES, strict=True):
        authority = exact_keys(
            item,
            {
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
            },
            f"L11 authority {expected.path}",
        )
        entry = c11_entries.get(expected.path)
        require(
            entry is not None
            and entry.kind == "blob"
            and entry.mode == expected.git_mode,
            f"C11 authority tree entry changed: {expected.path}",
        )
        blob = verify_object("blob", entry.oid, LIMITS[expected.limit_class])
        require(
            authority["binding_state"] == "bound_to_head"
            and authority["git_blob_oid"] == entry.oid
            and authority["live_blob_oid"] == entry.oid
            and authority["git_mode"] == expected.git_mode
            and authority["live_mode"] == f"{expected.live_mode:04o}"
            and authority["limit_class"] == expected.limit_class
            and authority["path"] == expected.path
            and authority["role"] == expected.role
            and authority["sha256"] == hashlib.sha256(blob).hexdigest()
            and authority["size_bytes"] == len(blob),
            f"L11 authority binding changed: {expected.path}",
        )
        aggregate += len(blob)
    require(aggregate <= AGGREGATE_LIMIT, "L11 authority aggregate exceeds 16 MiB")

    state = exact_keys(root["repository_state"], {"after", "before"}, "L11 state")
    before = validate_local_snapshot(state["before"], c11, c11_tree, "before")
    after = validate_local_snapshot(state["after"], c11, c11_tree, "after")
    require(
        {key: value for key, value in state["before"].items() if key != "observed_at"}
        == {
            key: value for key, value in state["after"].items() if key != "observed_at"
        },
        "L11 repository endpoints differ",
    )

    invocation = exact_keys(
        root["invocation"],
        {
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
        },
        "L11 invocation",
    )
    stdout = decode_binding(invocation["stdout"], "L11 stdout", 8 * 1024 * 1024)
    stderr = decode_binding(invocation["stderr"], "L11 stderr", 8 * 1024 * 1024)
    started = parse_utc_timestamp(invocation["started_at"], "L11 start")
    finished = parse_utc_timestamp(invocation["finished_at"], "L11 finish")
    require(
        invocation["argv"] == ["just", "ksg-composite-v11"]
        and invocation["cwd"] == "<REPOSITORY_ROOT>"
        and invocation["environment"] == LOCAL_ENVIRONMENT
        and type(invocation["environment_routes_sha256"]) is str
        and SHA256_RE.fullmatch(invocation["environment_routes_sha256"]) is not None
        and invocation["exit_code"] == 0
        and invocation["signal"] is None
        and invocation["timeout_seconds"] == 14_400
        and invocation["timed_out"] is False
        and invocation["umask"] == "0077"
        and invocation["monotonic_start_ns"] == 0
        and type(invocation["monotonic_finish_ns"]) is int
        and invocation["monotonic_finish_ns"] > 0
        and invocation["elapsed_monotonic_ns"] == invocation["monotonic_finish_ns"]
        and stdout + stderr != b""
        and before <= started <= finished <= after,
        "L11 invocation or ordering changed",
    )

    platform_value = exact_keys(
        root["platform"],
        {
            "architecture",
            "gil_enabled",
            "operating_system",
            "operating_system_release",
            "python_implementation",
            "python_version",
        },
        "L11 platform",
    )
    require(
        platform_value["operating_system"] == "Darwin"
        and platform_value["architecture"] in {"arm64", "aarch64"}
        and type(platform_value["operating_system_release"]) is str
        and platform_value["operating_system_release"]
        and platform_value["python_implementation"] == "CPython"
        and platform_value["python_version"] == "3.14.6"
        and platform_value["gil_enabled"] is True,
        "L11 reviewed platform changed",
    )

    records = root["reviewed_executables"]
    require(
        type(records) is list
        and [record.get("name") for record in records] == sorted(LOCAL_TOOL_VERSIONS),
        "L11 reviewed executable roster changed",
    )
    for record in records:
        name = record["name"]
        exact_keys(
            record,
            {
                "executable_sha256",
                "executable_size_bytes",
                "name",
                "route",
                "version_argv",
                "version_exit_code",
                "version_stderr",
                "version_stdout",
            },
            f"L11 executable {name}",
        )
        version_stdout = decode_binding(
            record["version_stdout"], f"{name} version stdout", VERSION_LIMIT
        )
        version_stderr = decode_binding(
            record["version_stderr"], f"{name} version stderr", VERSION_LIMIT
        )
        require(
            type(record["executable_sha256"]) is str
            and SHA256_RE.fullmatch(record["executable_sha256"]) is not None
            and type(record["executable_size_bytes"]) is int
            and 0 < record["executable_size_bytes"] <= 256 * 1024 * 1024
            and type(record["route"]) is str
            and re.fullmatch(
                rf"<(?:SYSTEM|USR_LOCAL|HOMEBREW|TEXLIVE)_BIN>/{re.escape(name)}",
                record["route"],
            )
            is not None
            and record["version_argv"] == LOCAL_TOOL_VERSIONS[name]
            and record["version_exit_code"] == 0
            and version_stdout + version_stderr != b"",
            f"L11 executable binding changed: {name}",
        )
    return {
        "authority_count": len(authorities),
        "command_exit_code": 0,
        "platform": "Darwin-arm64-CPython-3.14.6-GIL",
        "reviewed_executables": len(records),
    }


def expected_receipt(
    local_raw: bytes,
    successor_raw: bytes,
    c11: str,
    c11_tree: str,
) -> dict[str, Any]:
    return {
        "bindings": {
            "hosted_capture": descriptor(successor_raw, SUCCESSOR_CAPTURE),
            "local_closure": descriptor(local_raw, LOCAL_EVIDENCE),
        },
        "nonimplications": RECEIPT_NONIMPLICATIONS,
        "qualification": {
            "attempt": 1,
            "formula": "Q11 = L11 AND CI11_attempt1 AND CodeQL11_attempt1 AND Dedicated11_attempt1",
            "terms": {
                "CI11_attempt1": True,
                "CodeQL11_attempt1": True,
                "Dedicated11_attempt1": True,
                "L11": True,
            },
            "value": True,
        },
        "repository": REPOSITORY,
        "schema": "pid-rs/ksg-rev4-m1a-composite-receipt/v11",
        "schema_revision": 11,
        "subject": {
            "commit": c11,
            "message": C11_MESSAGE,
            "parent": C9_COMMIT,
            "tree": c11_tree,
        },
    }


def bounded_input_fd(
    fd: int, label: str, maximum: int
) -> tuple[bytes, tuple[int, int]]:
    require(type(fd) is int and fd >= 3, f"{label} descriptor is outside the bound")
    try:
        before = os.fstat(fd)
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        offset = os.lseek(fd, 0, os.SEEK_CUR)
    except OSError:
        raise ContractError(f"cannot inspect {label} descriptor") from None
    require(
        stat.S_ISREG(before.st_mode)
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o600
        and flags & os.O_ACCMODE == os.O_RDONLY
        and offset == 0
        and 0 < before.st_size <= maximum,
        f"{label} is not one bounded read-only mode-0600 file at offset zero",
    )
    chunks: list[bytes] = []
    remaining = before.st_size
    while remaining:
        chunk = os.read(fd, min(remaining, 1024 * 1024))
        require(chunk != b"", f"{label} ended early")
        chunks.append(chunk)
        remaining -= len(chunk)
    require(os.read(fd, 1) == b"", f"{label} grew while read")
    after = os.fstat(fd)
    require(
        metadata_identity(before) == metadata_identity(after),
        f"{label} changed while read",
    )
    return b"".join(chunks), (before.st_dev, before.st_ino)


def derive_receipt_from_descriptors(local_fd: int, successor_fd: int) -> dict[str, Any]:
    require(local_fd != successor_fd, "L11 and successor descriptor numbers alias")
    validate_git_metadata()
    head_raw = git("rev-parse", "--verify", "HEAD")
    try:
        head = head_raw.decode("ascii", errors="strict").strip()
    except UnicodeError:
        raise ContractError("receipt-derivation HEAD encoding changed") from None
    require(OID_RE.fullmatch(head) is not None, "receipt-derivation HEAD is malformed")
    topology = locate_lifecycle(head)
    require(
        topology["phase"] == "candidate"
        and topology["r11"] is None
        and head == topology["c11"]
        and git("status", "--porcelain=v1", "--untracked-files=all") == b"",
        "receipt derivation requires the clean exact receipt-absent C11",
    )
    local_raw, local_identity = bounded_input_fd(local_fd, "L11 input", RECORD_LIMIT)
    successor_raw, successor_identity = bounded_input_fd(
        successor_fd, "successor input", RECORD_LIMIT
    )
    require(
        local_identity != successor_identity, "L11 and successor inputs are one file"
    )
    c11 = topology["c11"]
    c11_tree = topology["c11_tree"]
    validate_local_evidence(local_raw, c11, c11_tree)
    validate_successor_capture(
        successor_raw,
        tree_blob(c11, HOSTED_TOOL, ORDINARY_LIMIT),
        c11,
        c11_tree,
    )
    result = expected_receipt(local_raw, successor_raw, c11, c11_tree)
    validate_schema(
        parse_json(tree_blob(c11, RECEIPT_SCHEMA, ORDINARY_LIMIT), RECEIPT_SCHEMA),
        RECEIPT_SCHEMA,
    )
    require(
        0 < len(pretty_json(result)) <= RECORD_LIMIT,
        "derived R11 receipt exceeds its output bound",
    )
    return result


def validate_r11_evidence(topology: dict[str, Any]) -> dict[str, Any]:
    r11 = topology["r11"]
    require(type(r11) is str and OID_RE.fullmatch(r11) is not None, "R11 is absent")
    c11 = topology["c11"]
    c11_tree = topology["c11_tree"]
    local_raw = tree_blob(r11, LOCAL_EVIDENCE, RECORD_LIMIT)
    successor_raw = tree_blob(r11, SUCCESSOR_CAPTURE, RECORD_LIMIT)
    receipt_raw = tree_blob(r11, RECEIPT, RECORD_LIMIT)
    hosted_tool_raw = tree_blob(c11, HOSTED_TOOL, ORDINARY_LIMIT)
    local_result = validate_local_evidence(local_raw, c11, c11_tree)
    successor_result = validate_successor_capture(
        successor_raw, hosted_tool_raw, c11, c11_tree
    )
    receipt_value = parse_json(receipt_raw, "R11 receipt", maximum=RECORD_LIMIT)
    require(
        receipt_raw == pretty_json(receipt_value)
        and receipt_value == expected_receipt(local_raw, successor_raw, c11, c11_tree),
        "R11 receipt is noncanonical or differs from exact L11/hosted derivation",
    )
    return {
        "local": local_result,
        "receipt_derived_from_exact_evidence": True,
        "successor": successor_result,
    }


def validate_diagnostic(value: Any) -> None:
    root = exact_keys(
        value,
        {
            "credit",
            "diagnostic_boundary",
            "first_observed_rejection",
            "fresh_repair_rule",
            "latent_not_reached_defects",
            "nonimplications",
            "repository",
            "schema",
            "schema_revision",
            "status",
        },
        "C10 diagnostic",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-v10-diagnostic-failure/v1"
        and root["schema_revision"] == 1
        and root["status"] == "rejected_off_main_zero_credit",
        "C10 diagnostic identity changed",
    )
    require(
        root["credit"]
        == {
            "c10_ancestry_for_c11": "none",
            "hosted_qualification": "none",
            "l10": "unissued",
            "r15": "rejected_not_reused",
            "r10": "unissued",
        }
        and root["fresh_repair_rule"]
        == {
            "c11_message": C11_MESSAGE,
            "c11_parent": C9_COMMIT,
            "c11_relationship_to_c10": "fresh_sibling_not_descendant",
            "c10_merge_or_cherry_pick": False,
            "reapply_scope": "independently_reviewed_non_evidentiary_repairs_only",
        }
        and root["nonimplications"]
        == [
            "The two mode-policy defects were latent later blockers; they were not reached and are not co-causes of the first observed oversize rejection.",
            "The oversize rejection does not imply that the captured public provider responses were false, authenticated, complete, or qualification-bearing.",
            "This diagnostic record reconstructs no missing C10 source, commit object, L10 observation, hosted success, or accepted R15 replay.",
            "No PID, KSG, theorem, numerical, security, privacy, accessibility, or application conclusion follows from this operational failure.",
        ],
        "C10 diagnostic credit or semantic boundary changed",
    )
    boundary = exact_keys(
        root["diagnostic_boundary"],
        {
            "c10_commit",
            "c10_parent",
            "c10_tree",
            "candidate_added_paths",
            "candidate_clean_when_observed",
            "candidate_modified_paths",
            "candidate_total_changed_paths",
            "c10_object_and_source_bytes_durable",
            "candidate_unsigned",
            "classification",
            "raw_failure_record_durable",
        },
        "C10 diagnostic boundary",
    )
    require(
        boundary["c10_commit"] == C10_COMMIT
        and boundary["c10_tree"] == C10_TREE
        and boundary["c10_parent"] == C9_COMMIT
        and boundary["c10_object_and_source_bytes_durable"] is False
        and boundary["candidate_clean_when_observed"] is True
        and boundary["candidate_unsigned"] is True
        and boundary["candidate_modified_paths"] == 22
        and boundary["candidate_added_paths"] == 17
        and boundary["candidate_total_changed_paths"] == 39
        and boundary["classification"]
        == "recorded_full_identity_metadata_not_recovered_Git_object_or_source_custody"
        and boundary["raw_failure_record_durable"] is False,
        "recorded C10 identity metadata changed",
    )
    first = exact_keys(
        root["first_observed_rejection"],
        {
            "authority_limit_bytes",
            "authority_observed_bytes",
            "authority_path",
            "bytes_over_limit",
            "failure_phase",
            "ordering",
            "status",
        },
        "C10 first observed rejection",
    )
    require(
        first
        == {
            "authority_limit_bytes": ORDINARY_LIMIT,
            "authority_observed_bytes": 2_264_350,
            "authority_path": SPECIAL_PATH,
            "bytes_over_limit": 167_198,
            "failure_phase": "local_L10_capture_authority_descriptors",
            "ordering": "lexicographically_first_rejected_authority",
            "status": "observed_blocker",
        },
        "first observed C10 rejection changed",
    )
    latent = root["latent_not_reached_defects"]
    require(
        type(latent) is list
        and [item["path"] for item in latent]
        == sorted((CURRENT_SOURCE_SELF_TEST, CURRENT_SOURCE_CHECKER))
        and all(
            type(item) is dict
            and set(item)
            == {
                "git_mode",
                "path",
                "v10_parallel_map_expected_live_mode",
                "worktree_mode",
            }
            and item["git_mode"] == "100755"
            and item["worktree_mode"] == "0755"
            and item["v10_parallel_map_expected_live_mode"] == "0644"
            for item in latent
        ),
        "latent mode defects changed or were promoted to observed causes",
    )


def validate_policy(value: Any) -> None:
    root = exact_keys(
        value,
        {
            "authority_contract",
            "c10",
            "c11",
            "l11",
            "nonimplications",
            "qualification",
            "r11",
            "r16_current_source",
            "repository",
            "schema",
            "schema_revision",
            "state",
        },
        "v11 policy",
    )
    require(
        root["repository"] == REPOSITORY
        and root["schema"] == "pid-rs/ksg-rev4-m1a-composite-v11-path-policy/v1"
        and root["schema_revision"] == 1
        and root["state"] == "candidate_authoring_no_evidence",
        "v11 policy identity changed",
    )
    contract = exact_keys(
        root["authority_contract"],
        {
            "aggregate_limit_bytes",
            "concurrency_boundary",
            "default_limit_bytes",
            "descriptor_read",
            "git_binding",
            "live_binding",
            "single_structure",
            "special_limits",
        },
        "v11 authority contract",
    )
    require(
        contract["default_limit_bytes"] == ORDINARY_LIMIT
        and contract["aggregate_limit_bytes"] == AGGREGATE_LIMIT
        and contract["concurrency_boundary"]
        == "complete_probe_start_end_metadata_config_ref_head_status_revalidation_pass_not_atomic_transient_or_same_uid_privileged_mutation_not_excluded"
        and contract["descriptor_read"]
        == "repository_root_dirfd_component_openat_no_follow_exact_size_and_eof_stable_identity"
        and contract["git_binding"]
        == "exact_tree_mode_blob_oid_and_python_verified_commit_tree_blob_object_hashes"
        and contract["live_binding"]
        == "exact_mode_single_link_regular_file_stable_descriptor_read"
        and contract["single_structure"] == "AuthoritySpec"
        and contract["special_limits"]
        == [
            {
                "limit_bytes": SPECIAL_LIMIT,
                "limit_class": "terminal_c9_capture_4mib",
                "path": SPECIAL_PATH,
            }
        ],
        "v11 authority policy changed",
    )
    require(
        root["c10"]["disposition"] == "rejected_off_main"
        and root["c10"]["ancestry_credit"] == "none"
        and root["c10"]["r15_credit"] == "none"
        and root["c10"]["merge_or_cherry_pick"] is False
        and root["c11"]["parent"] == C9_COMMIT
        and root["c11"]["message"] == C11_MESSAGE
        and root["c11"]["relationship_to_c10"] == "fresh_sibling",
        "fresh-sibling topology policy changed",
    )
    l11 = exact_keys(
        root["l11"],
        {
            "attempt_semantics",
            "capture_command",
            "operator_uniqueness_provable_by_recorder",
            "preflight_command_normal",
            "preflight_command_optimized",
            "preflight_consumes_attempt",
            "status",
        },
        "L11 policy",
    )
    r11 = exact_keys(
        root["r11"],
        {"derive_command", "issuance", "message", "status"},
        "R11 policy",
    )
    require(
        root["qualification"]["formula"]
        == "Q11 = L11 AND CI11_attempt1 AND CodeQL11_attempt1 AND Dedicated11_attempt1"
        and root["qualification"]["attempt"] == 1
        and root["qualification"]["status"] == "not_run"
        and r11["status"] == "unissued"
        and r11["issuance"] == "if_and_only_if_Q11"
        and r11["message"] == R11_MESSAGE
        and "--derive-receipt --local-fd 3 --successor-fd 4" in r11["derive_command"]
        and root["r16_current_source"]["accepted_r15_reuse"] is False
        and root["r16_current_source"]["fresh_after_exact_c11_bytes_settle"] is True
        and l11["attempt_semantics"]
        == "one_shot_per_exact_c11_identity_any_production_launch_outcome_consumes_attempt"
        and l11["operator_uniqueness_provable_by_recorder"] is False
        and l11["preflight_consumes_attempt"] is False
        and l11["status"] == "not_produced",
        "v11 qualification staging changed",
    )


def validate_schema(value: Any, path: str) -> None:
    require(type(value) is dict, f"schema root changed: {path}")
    require(
        value.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        and value.get("$id") == f"https://github.com/{REPOSITORY}/blob/main/{path}",
        f"schema identity changed: {path}",
    )
    if path == HOSTED_SCHEMA:
        root = exact_keys(value, {"$defs", "$id", "$schema", "oneOf"}, "hosted schema")
        definitions = root["$defs"]
        require(
            type(definitions) is dict
            and set(definitions)
            == {
                "capture",
                "captureArray",
                "commit",
                "descriptor",
                "nonimplications",
                "predecessorDocument",
                "predecessorRuns",
                "predecessorSubject",
                "redirect",
                "retry",
                "retryArray",
                "sha256",
                "successorDocument",
                "successorRuns",
                "successorSubject",
            }
            and root["oneOf"]
            == [
                {"$ref": "#/$defs/predecessorDocument"},
                {"$ref": "#/$defs/successorDocument"},
            ]
            and definitions["predecessorDocument"]["properties"]["phase"]
            == {"const": "predecessor_failure"}
            and definitions["successorDocument"]["properties"]["phase"]
            == {"const": "successor_qualification"}
            and definitions["predecessorSubject"]["properties"]
            == {
                "predecessor_commit": {"const": C9_COMMIT},
                "predecessor_tree": {"const": C9_TREE},
            }
            and definitions["successorSubject"]["required"]
            == [
                "predecessor_commit",
                "predecessor_tree",
                "successor_commit",
                "successor_tree",
            ],
            "hosted schema critical contract changed",
        )
    elif path == LOCAL_SCHEMA:
        root = exact_keys(
            value,
            {
                "$defs",
                "$id",
                "$schema",
                "additionalProperties",
                "properties",
                "required",
                "title",
                "type",
            },
            "local schema",
        )
        properties = root["properties"]
        subject = properties["subject"]["properties"]
        require(
            properties["authorities"]["minItems"] == len(EXPECTED_AUTHORITIES)
            and properties["authorities"]["maxItems"] == len(EXPECTED_AUTHORITIES)
            and properties["limits"] == {"const": LOCAL_LIMITS}
            and properties["schema"]
            == {"const": "pid-rs/ksg-rev4-m1a-composite-local-closure/v11"}
            and properties["schema_revision"] == {"const": 11}
            and subject["c9_parent"] == {"const": C9_COMMIT}
            and subject["c11_message"] == {"const": C11_MESSAGE}
            and root["additionalProperties"] is False,
            "local schema critical contract changed",
        )
    elif path == RECEIPT_SCHEMA:
        root = exact_keys(
            value,
            {
                "$defs",
                "$id",
                "$schema",
                "additionalProperties",
                "properties",
                "required",
                "title",
                "type",
            },
            "receipt schema",
        )
        properties = root["properties"]
        subject = properties["subject"]["properties"]
        qualification = properties["qualification"]["properties"]
        require(
            properties["schema"]
            == {"const": "pid-rs/ksg-rev4-m1a-composite-receipt/v11"}
            and properties["schema_revision"] == {"const": 11}
            and subject["message"] == {"const": C11_MESSAGE}
            and subject["parent"] == {"const": C9_COMMIT}
            and qualification["attempt"] == {"const": 1}
            and qualification["formula"]
            == {
                "const": "Q11 = L11 AND CI11_attempt1 AND CodeQL11_attempt1 AND Dedicated11_attempt1"
            }
            and qualification["value"] == {"const": True}
            and root["additionalProperties"] is False,
            "receipt schema critical contract changed",
        )
    else:
        refuse(f"unknown v11 schema: {path}")


def validate_no_duplicate_literal_dict_keys(raw: bytes, label: str) -> int:
    try:
        module = ast.parse(raw, filename=label, mode="exec")
    except (SyntaxError, ValueError):
        raise ContractError(f"{label} is not valid Python source") from None
    checked = 0
    for node in ast.walk(module):
        if not isinstance(node, ast.Dict):
            continue
        seen: set[Any] = set()
        for key in node.keys:
            if not isinstance(key, ast.Constant) or not isinstance(
                key.value, (str, bytes, int, float, complex, bool, type(None))
            ):
                continue
            marker = key.value
            require(
                marker not in seen,
                f"duplicate literal dict key in {label}: {key.value!r}",
            )
            seen.add(marker)
            checked += 1
    return checked


def validate_workflows(active: str, retired: str) -> None:
    require(
        "push:" in active
        and "workflow_dispatch:" in active
        and "KSG M1a composite v11" in active
        and "capture-ksg-m1a-composite-v11-local-closure.py --self-test" in active
        and "capture-ksg-m1a-composite-v11-local-closure.py --preflight-live" in active
        and "check-current-source-state-v1.py" in active
        and "check-current-source-state-v1-self-test.py" in active
        and "check-ksg-m1a-composite-v11-self-test.py" in active
        and "check-ksg-m1a-composite-v11.py --workflow" in active
        and "GITHUB_RUN_ATTEMPT" in active
        and 'test "${GITHUB_EVENT_NAME}" = "push"' in active
        and "continue-on-error" not in active
        and "[skip ci]" not in active,
        "active v11 workflow semantics changed",
    )
    require(
        "workflow_dispatch:" in retired
        and "push:" not in retired
        and "retired" in retired.lower()
        and "exit 1" in retired,
        "v9 workflow is not an inert manual refusal",
    )


def validate_repairs(root_fd: int) -> None:
    rust = stable_read(
        root_fd, ordinary("crates/pid-core/build_support.rs", "rust")
    ).decode("utf-8")
    require(
        rust.count("as_chunks::<3>()") == 1
        and rust.count("as_chunks::<2>()") == 1
        and "fields.chunks_exact(3)" not in rust
        and "fields.chunks_exact(2)" not in rust,
        "Rust 1.98 parser repair changed",
    )
    ci = stable_read(root_fd, ordinary(".github/workflows/ci.yml", "ci")).decode(
        "utf-8"
    )
    require(
        "cargo-semver-checks --locked --version 0.49.0" in ci
        and 'test "$(cargo semver-checks --version)" = "cargo-semver-checks 0.49.0"'
        in ci
        and "10 intended, 62 rejected" in ci
        and "normalize-actions-checkout-git-info-exclude.py" in ci,
        "CI compatibility repair wiring changed",
    )
    leaks = stable_read(root_fd, ordinary(".gitleaks.toml", "gitleaks")).decode("utf-8")
    require(
        'regexTarget = "line"' in leaks
        and "18-key serialization order, " + "108-coordinate certificate$" in leaks
        and "^claims/SX-CERTIFIED-AVERAGED-PID3-001/claim-v1\\.md$" in leaks,
        "narrow gitleaks firewall changed",
    )
    boundary = stable_read(root_fd, EXPECTED_BY_PATH[BOUNDARY_PATH]).decode(
        "utf-8", errors="strict"
    )
    require(
        "The oversize\nartifact itself was not recovered: only metadata about its observed identity, size, and digest was\nrecovered and retained."
        in boundary
        and "35 source-byte sequences were recovered privately" in boundary
        and "one-shot lifecycle action" in boundary
        and "The recorder cannot prove operator uniqueness" in boundary,
        "C10 recovery scope or one-shot L11 boundary changed",
    )
    literal_keys = 0
    for path in PYTHON_LITERAL_KEY_SOURCES:
        literal_keys += validate_no_duplicate_literal_dict_keys(
            stable_read(root_fd, EXPECTED_BY_PATH[path]), path
        )
    require(literal_keys > 0, "Python literal-key source scan examined no keys")


def check(mode: str) -> dict[str, Any]:
    require(mode in {"authoring", "candidate", "workflow"}, "unknown checker mode")
    outer_metadata_before = complete_git_metadata_snapshot()
    metadata = validate_git_metadata()
    head_raw = git("rev-parse", "--verify", "HEAD")
    try:
        head = head_raw.decode("ascii", errors="strict").strip()
    except UnicodeError:
        raise ContractError("HEAD identity encoding changed") from None
    require(OID_RE.fullmatch(head) is not None, "HEAD identity changed")
    status_before = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        maximum=GIT_METADATA_LIMIT,
    )
    tree, commit_raw = verify_head_objects(head)
    parsed_tree, parents, message, signed = parse_commit_envelope(commit_raw)
    require(parsed_tree == tree, "HEAD commit/tree binding changed")
    topology: dict[str, Any] | None = None
    strict = mode != "authoring"
    if mode == "authoring":
        require(
            head == C9_COMMIT and tree == C9_TREE and not signed,
            "authoring base is not exact unsigned C9",
        )
        lifecycle_phase = "authoring"
    else:
        require(status_before == b"" and not signed, "workflow HEAD is dirty or signed")
        topology = locate_lifecycle(head)
        lifecycle_phase = topology["phase"]
        if mode == "candidate":
            require(
                lifecycle_phase == "candidate"
                and parents == (C9_COMMIT,)
                and message == C11_MESSAGE
                and head == topology["c11"]
                and tree == topology["c11_tree"],
                "candidate mode requires exact clean unsigned C11",
            )
    roster = validate_live_authorities(head, candidate=strict)
    root_fd, root_identity = open_canonical_root(ROOT)
    predecessor_result: dict[str, Any] | None = None
    try:
        diagnostic = parse_json(
            stable_read(root_fd, EXPECTED_BY_PATH[DIAGNOSTIC_PATH]), "C10 diagnostic"
        )
        policy = parse_json(
            stable_read(root_fd, EXPECTED_BY_PATH[POLICY_PATH]), "v11 policy"
        )
        validate_diagnostic(diagnostic)
        validate_policy(policy)
        for path in (LOCAL_SCHEMA, HOSTED_SCHEMA, RECEIPT_SCHEMA):
            validate_schema(
                parse_json(stable_read(root_fd, EXPECTED_BY_PATH[path]), path), path
            )
        active = stable_read(root_fd, EXPECTED_BY_PATH[WORKFLOW]).decode(
            "utf-8", errors="strict"
        )
        retired = stable_read(root_fd, EXPECTED_BY_PATH[RETIRED_V9_WORKFLOW]).decode(
            "utf-8", errors="strict"
        )
        validate_workflows(active, retired)
        validate_repairs(root_fd)
        require_descriptor_absent(
            root_fd,
            ".github/workflows/ksg-m1a-composite-v10.yml",
            "active v10 lifecycle",
        )
        require(
            tree_entry(head, ".github/workflows/ksg-m1a-composite-v10.yml") is None,
            "active v10 lifecycle is committed",
        )
        if mode == "authoring":
            try:
                predecessor_raw = stable_read(root_fd, EXPECTED_BY_PATH[SPECIAL_PATH])
            except FileNotFoundError:
                predecessor_raw = None
        else:
            require(topology is not None, "strict lifecycle topology is absent")
            predecessor_raw = tree_blob(topology["c11"], SPECIAL_PATH, SPECIAL_LIMIT)
        if predecessor_raw is not None:
            hosted_raw = (
                stable_read(root_fd, EXPECTED_BY_PATH[HOSTED_TOOL])
                if mode == "authoring"
                else tree_blob(
                    topology["c11"] if topology is not None else head,
                    HOSTED_TOOL,
                    ORDINARY_LIMIT,
                )
            )
            predecessor_result = validate_predecessor_capture(
                predecessor_raw, hosted_raw
            )
        require(
            not strict or predecessor_result is not None,
            "committed C11 lacks its validated terminal-C9 predecessor capture",
        )
    finally:
        recheck_canonical_root(ROOT, root_fd, root_identity)
        os.close(root_fd)
    evidence_result = None
    if topology is not None and topology["r11"] is not None:
        evidence_result = validate_r11_evidence(topology)
    final_head = (
        git("rev-parse", "--verify", "HEAD").decode("ascii", errors="strict").strip()
    )
    status_after = git(
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
        maximum=GIT_METADATA_LIMIT,
    )
    outer_metadata_after = complete_git_metadata_snapshot()
    validate_complete_probe_endpoints(
        head,
        status_before,
        outer_metadata_before,
        final_head,
        status_after,
        outer_metadata_after,
    )
    return {
        "authority_aggregate_bytes": roster["aggregate_bytes"],
        "authority_count": len(EXPECTED_AUTHORITIES),
        "authority_states": roster["states"],
        "c10_credit": "none",
        "git_commit_and_tree_objects_verified": True,
        "git_metadata_isolation": metadata,
        "head": head,
        "lifecycle_phase": lifecycle_phase,
        "mode": mode,
        "pending_evidence_paths": roster["pending"],
        "predecessor_capture": predecessor_result,
        "r11_commit": None if topology is None else topology["r11"],
        "r11_evidence": evidence_result,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-check/v1",
        "tree": tree,
    }


def offline_self_test() -> dict[str, Any]:
    validate_authority_specification()
    require(
        git_oid("blob", b"") == "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"
        and git_oid("tree", b"") == "4b825dc642cb6eb9a060e54bf8d69288fbee4904",
        "Git object hash controls failed",
    )
    rejected = 0
    nearby = tuple(
        ExpectedAuthority(
            item.path + ".nearby" if item.path == SPECIAL_PATH else item.path,
            item.role,
            item.git_mode,
            item.live_mode,
            item.limit_class,
            item.authoring_required,
        )
        for item in EXPECTED_AUTHORITIES
    )
    try:
        validate_authority_specification(nearby)
    except ContractError:
        rejected += 1
    ordinary_special = tuple(
        ExpectedAuthority(
            item.path,
            item.role,
            item.git_mode,
            item.live_mode,
            "terminal_c9_capture_4mib" if item.path == CHECKER else item.limit_class,
            item.authoring_required,
        )
        for item in EXPECTED_AUTHORITIES
    )
    try:
        validate_authority_specification(ordinary_special)
    except ContractError:
        rejected += 1
    require(rejected == 2, "authority-class mutants were accepted")

    tree_control_rejections = 0
    c9_entries: dict[str, TreeEntry] = {}
    c11_entries: dict[str, TreeEntry] = {}
    for index, (path, status, mode) in enumerate(EXPECTED_C11_DELTA, start=1):
        old = TreeEntry(mode, "blob", f"{index:040x}")
        new = TreeEntry(mode, "blob", f"{index + 100:040x}")
        if status == "M":
            c9_entries[path] = old
        c11_entries[path] = new
    require(
        changed_rows(c9_entries, c11_entries) == EXPECTED_C11_DELTA,
        "exact C11 delta positive control failed",
    )
    hostile_c11 = dict(c11_entries)
    hostile_c11["unrelated.txt"] = TreeEntry("100644", "blob", "f" * 40)
    if changed_rows(c9_entries, hostile_c11) != EXPECTED_C11_DELTA:
        tree_control_rejections += 1
    r11_entries = dict(c11_entries)
    for index, (path, status, mode) in enumerate(EXPECTED_R11_DELTA, start=300):
        require(status in {"A", "M"}, "R11 fixture status changed")
        if status == "M":
            require(path in r11_entries, "R11 modified fixture path is absent")
        r11_entries[path] = TreeEntry(mode, "blob", f"{index:040x}")
    require(
        changed_rows(c11_entries, r11_entries) == EXPECTED_R11_DELTA,
        "exact R11 delta positive control failed",
    )
    hostile_r11 = dict(r11_entries)
    hostile_r11[RECEIPT] = TreeEntry("100755", "blob", hostile_r11[RECEIPT].oid)
    if changed_rows(c11_entries, hostile_r11) != EXPECTED_R11_DELTA:
        tree_control_rejections += 1
    require(tree_control_rejections == 2, "lifecycle delta mutants were accepted")
    introduction_rejections = 0
    fixture_r11 = "a" * 40
    require(
        validate_evidence_introductions(
            {path: [fixture_r11] for path in PRESERVED_R11_PATHS},
            [fixture_r11],
        )
        == fixture_r11,
        "R11 introduction positive control failed",
    )
    for introductions, candidates in (
        (
            {
                path: [fixture_r11, "b" * 40] if path == RECEIPT else [fixture_r11]
                for path in PRESERVED_R11_PATHS
            },
            [fixture_r11],
        ),
        (
            {path: [fixture_r11] for path in PRESERVED_R11_PATHS},
            [fixture_r11, "b" * 40],
        ),
        (
            {
                path: ["b" * 40] if path == LOCAL_EVIDENCE else [fixture_r11]
                for path in PRESERVED_R11_PATHS
            },
            [fixture_r11],
        ),
    ):
        try:
            validate_evidence_introductions(introductions, candidates)
        except ContractError:
            introduction_rejections += 1
    require(introduction_rejections == 3, "R11 introduction mutants were accepted")

    side_branch_rejections = 0
    fixture_base = "c" * 40
    fixture_side = "b" * 40
    fixture_envelopes = {
        fixture_r11: CommitEnvelope(
            fixture_r11,
            "1" * 40,
            (fixture_base,),
            R11_MESSAGE,
            False,
        ),
        fixture_side: CommitEnvelope(
            fixture_side,
            "2" * 40,
            (fixture_base,),
            "Merged-side evidence introduction\n",
            False,
        ),
    }
    fixture_selected = {
        fixture_base: {},
        fixture_r11: {
            path: TreeEntry("100644", "blob", f"{index:040x}")
            for index, path in enumerate(PRESERVED_R11_PATHS, start=1)
        },
        fixture_side: {
            RECEIPT: TreeEntry("100644", "blob", "9" * 40),
        },
    }
    side_introductions = find_evidence_introductions(
        fixture_envelopes,
        fixture_selected,
    )
    try:
        validate_evidence_introductions(side_introductions, [fixture_r11])
    except ContractError:
        side_branch_rejections += 1
    require(
        side_branch_rejections == 1,
        "merged side-branch evidence introduction was accepted",
    )

    message_reuse_rejections = 0
    fixture_c11 = "4" * 40
    fixture_message_side = "5" * 40
    base_c11_envelope = CommitEnvelope(
        fixture_c11,
        "6" * 40,
        (C9_COMMIT,),
        C11_MESSAGE,
        False,
    )
    validate_lifecycle_message_uniqueness(
        {fixture_c11: base_c11_envelope}, fixture_c11, None
    )
    for reused_message in (C11_MESSAGE, R11_MESSAGE):
        hostile = {
            fixture_c11: base_c11_envelope,
            fixture_message_side: CommitEnvelope(
                fixture_message_side,
                "7" * 40,
                ("8" * 40,),
                reused_message,
                False,
            ),
        }
        try:
            validate_lifecycle_message_uniqueness(hostile, fixture_c11, None)
        except ContractError:
            message_reuse_rejections += 1
    receipt_envelopes = {
        fixture_c11: base_c11_envelope,
        fixture_r11: CommitEnvelope(
            fixture_r11,
            "9" * 40,
            (fixture_c11,),
            R11_MESSAGE,
            False,
        ),
        fixture_message_side: CommitEnvelope(
            fixture_message_side,
            "a" * 40,
            ("8" * 40,),
            R11_MESSAGE,
            False,
        ),
    }
    try:
        validate_lifecycle_message_uniqueness(
            receipt_envelopes, fixture_c11, fixture_r11
        )
    except ContractError:
        message_reuse_rejections += 1
    require(
        message_reuse_rejections == 3,
        "candidate or receipt lifecycle-message reuse was accepted",
    )

    preservation_rejections = 0
    preserved_descendant = dict(r11_entries)
    validate_preserved_r11_entries(
        r11_entries,
        {"d" * 40: preserved_descendant},
    )
    changed_descendant = dict(preserved_descendant)
    changed_descendant[LOCAL_EVIDENCE] = TreeEntry("100644", "blob", "e" * 40)
    try:
        validate_preserved_r11_entries(
            r11_entries,
            {"d" * 40: preserved_descendant, "e" * 40: changed_descendant},
        )
    except ContractError:
        preservation_rejections += 1
    require(
        preservation_rejections == 1,
        "R11 descendant evidence mutation was accepted",
    )

    commit_controls = 0
    commit_fixture = (
        f"tree {'1' * 40}\nparent {C9_COMMIT}\nauthor A <a@example.invalid> 0 +0000\n"
        f"committer A <a@example.invalid> 0 +0000\n\n{C11_MESSAGE}"
    ).encode("utf-8")
    parsed = parse_commit_envelope(commit_fixture)
    require(
        parsed == ("1" * 40, (C9_COMMIT,), C11_MESSAGE, False),
        "unsigned commit envelope positive control failed",
    )
    signed_fixture = commit_fixture.replace(b"author ", b"gpgsig fixture\n author ", 1)
    if parse_commit_envelope(signed_fixture)[3] is True:
        commit_controls += 1
    multi_parent = commit_fixture.replace(
        f"parent {C9_COMMIT}\n".encode("ascii"),
        f"parent {C9_COMMIT}\nparent {'2' * 40}\n".encode("ascii"),
    )
    if parse_commit_envelope(multi_parent)[1] != (C9_COMMIT,):
        commit_controls += 1
    require(commit_controls == 2, "commit-envelope hostile controls failed")

    duplicate_literal_rejected = 0
    try:
        validate_no_duplicate_literal_dict_keys(
            b"x = {'schema': 1, 'schema': 2}\n", "fixture"
        )
    except ContractError:
        duplicate_literal_rejected += 1
    require(duplicate_literal_rejected == 1, "duplicate literal dict key was accepted")

    config_mutants = 0
    validate_repository_config_names(b"core.bare\ncommit.gpgsign\n")
    for raw in (b"core.bare\ninclude.path\n", b"core.bare\ncore.bare\n"):
        try:
            validate_repository_config_names(raw)
        except ContractError:
            config_mutants += 1
    require(config_mutants == 2, "repository config mutants were accepted")

    endpoint_mutants = 0
    endpoint_head = "1" * 40
    endpoint_status = b" M fixture\n"
    endpoint_metadata = {"filesystem": {"config_raw": b"fixture"}}
    validate_complete_probe_endpoints(
        endpoint_head,
        endpoint_status,
        endpoint_metadata,
        endpoint_head,
        endpoint_status,
        endpoint_metadata,
    )
    for final_head, final_status, final_metadata in (
        ("2" * 40, endpoint_status, endpoint_metadata),
        (endpoint_head, b"?? drift\n", endpoint_metadata),
        (endpoint_head, endpoint_status, {"filesystem": {"config_raw": b"drift"}}),
    ):
        try:
            validate_complete_probe_endpoints(
                endpoint_head,
                endpoint_status,
                endpoint_metadata,
                final_head,
                final_status,
                final_metadata,
            )
        except ContractError:
            endpoint_mutants += 1
    require(endpoint_mutants == 3, "complete-probe endpoint mutants were accepted")
    return {
        "authority_class_mutants_rejected": rejected,
        "authority_specifications_verified": len(EXPECTED_AUTHORITIES),
        "commit_envelope_hostiles_rejected": commit_controls,
        "complete_probe_endpoint_hostiles_rejected": endpoint_mutants,
        "duplicate_literal_dict_keys_rejected": duplicate_literal_rejected,
        "git_object_hash_controls": 2,
        "introduction_and_reuse_hostiles_rejected": introduction_rejections,
        "lifecycle_delta_hostiles_rejected": tree_control_rejections,
        "lifecycle_message_reuse_hostiles_rejected": message_reuse_rejections,
        "r11_descendant_preservation_hostiles_rejected": preservation_rejections,
        "repository_config_hostiles_rejected": config_mutants,
        "result": "pass",
        "schema": "pid-rs/ksg-rev4-m1a-composite-v11-checker-self-test/v1",
        "side_branch_introduction_hostiles_rejected": side_branch_rejections,
    }


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--authoring", action="store_true")
    modes.add_argument("--candidate", action="store_true")
    modes.add_argument("--workflow", action="store_true")
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--derive-receipt", action="store_true")
    parser.add_argument("--local-fd", type=int)
    parser.add_argument("--successor-fd", type=int)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    try:
        if arguments.derive_receipt:
            require(
                type(arguments.local_fd) is int and type(arguments.successor_fd) is int,
                "receipt derivation requires --local-fd and --successor-fd",
            )
            value = derive_receipt_from_descriptors(
                arguments.local_fd, arguments.successor_fd
            )
            sys.stdout.buffer.write(pretty_json(value))
            return 0
        require(
            arguments.local_fd is None and arguments.successor_fd is None,
            "input descriptors are accepted only for receipt derivation",
        )
        if arguments.self_test:
            value = offline_self_test()
        else:
            value = check(
                "workflow"
                if arguments.workflow
                else "candidate"
                if arguments.candidate
                else "authoring"
            )
        sys.stdout.write(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
        )
        return 0
    except (ContractError, OSError, subprocess.SubprocessError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print("ERROR: unexpected bounded v11 checker failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
