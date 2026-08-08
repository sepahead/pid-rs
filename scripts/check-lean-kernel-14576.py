#!/usr/bin/env python3
"""Replay Lean kernel regression #14576 under the exact patched toolchain.

The two checked files are unmodified upstream Lean regression tests.  Each uses
``#guard_msgs`` to require the fixed kernel's precise ``invalid projection``
diagnostic.  This gate appends a private EOF canary only to a temporary copy, so
success requires the guarded diagnostic route, complete elaboration, and a zero
exit; an arbitrary nonzero process result never earns credit.
"""

# ruff: noqa: E402 -- the isolation contract must run before non-bootstrap imports.

from __future__ import annotations

import sys as _bootstrap_sys


def _bootstrap_runtime_supported(version_info: object, flags: object) -> bool:
    version = tuple(version_info)[:2]
    return version >= (3, 11) and (
        getattr(flags, "isolated", 0) == 1
        and getattr(flags, "safe_path", False) is True
        and getattr(flags, "no_site", 0) == 1
        and getattr(flags, "ignore_environment", 0) == 1
        and getattr(flags, "dont_write_bytecode", 0) == 1
    )


if _bootstrap_sys.version_info < (3, 11):
    print(
        "ERROR: check-lean-kernel-14576.py requires Python >= 3.11",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
if not _bootstrap_runtime_supported(_bootstrap_sys.version_info, _bootstrap_sys.flags):
    print(
        "ERROR: check-lean-kernel-14576.py requires Python -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from dataclasses import dataclass
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import Final


SCRIPT_PATH = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT_PATH.parent.parent
FIXTURE_ROOT = ROOT / "audit/formal/lean-kernel-regression/issue-14576"
TOOLCHAIN_METADATA_PATH = ROOT / "audit/formal/lean/toolchain-release-v4.32.2.json"

EXPECTED_TOOLCHAIN: Final = "leanprover/lean4:v4.32.2"
EXPECTED_LEAN_VERSION: Final = "4.32.2"
EXPECTED_LEAN_COMMIT: Final = "f3b06c705e6c85f5314019d5d3baab0fec5b580c"
EXPECTED_LEAN_BUILD: Final = "Release"
EXPECTED_LAKE_VERSION: Final = "5.0.0-src+f3b06c7"
EXPECTED_ORIGIN_SHA256: Final = (
    "fd725d7ba4b08071f40ac6acaca62ecad09aefa11aa3c78cb94d2873cc5ddde1"
)
EXPECTED_TOOLCHAIN_METADATA_POLICY_SHA256: Final = (
    "5f72b60bd7bda8172ef2b2be0f4807eb082fcc88c9690b9c26c98ae83216b292"
)
EXPECTED_TOOLCHAIN_METADATA_SCHEMA: Final = (
    "pid-rs/lean-toolchain-release-custody-metadata/v3"
)
RESULT_SCHEMA: Final = "pid-rs/lean-kernel-14576-check/v6"
EXPECTED_SCOPE_BOUNDARY: Final = {
    "active_scientific_lean_project": "none",
    "archive_custody": "none_by_nested_checker",
    "downstream_authorization": "none",
    "kernel_soundness": "none",
    "nanoda_or_external_checker": "none",
    "pdf_transfer": "none",
    "pid_estimator_population_transfer": "none",
    "publisher_provider_authentication": "none",
    "real_nested_regression": "checks_passed_unpublished_nested_result",
    "release_authorization": "none",
    "reproducible_build": "none",
    "rust_binary64_transfer": "none",
    "same_run_qualification": "forbidden",
    "source_to_binary_provenance": "none",
    "static_schema_validation": "metadata_projection_and_self_binding_checked",
    "theorem_truth": "none",
}
TIMEOUT_SECONDS: Final = 120
LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS: Final = 900
LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_COUNT: Final = 3
NESTED_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS: Final = TIMEOUT_SECONDS
NESTED_NON_REPLAY_LEAN_CHILD_COUNT: Final = 6
NESTED_IDENTITY_CHILD_TIMEOUT_SECONDS: Final = 60
NESTED_IDENTITY_CHILD_COUNT: Final = 4
NESTED_ORCHESTRATION_HEADROOM_SECONDS: Final = 240
NESTED_NON_REPLAY_MARGIN_SECONDS: Final = (
    NESTED_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS * NESTED_NON_REPLAY_LEAN_CHILD_COUNT
    + NESTED_IDENTITY_CHILD_TIMEOUT_SECONDS * NESTED_IDENTITY_CHILD_COUNT
    + NESTED_ORCHESTRATION_HEADROOM_SECONDS
)
NESTED_REQUIRED_OUTER_TIMEOUT_SECONDS: Final = (
    LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS
    * LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_COUNT
    + NESTED_NON_REPLAY_MARGIN_SECONDS
)
MAX_PROCESS_OUTPUT_BYTES: Final = 65_536
PROCESS_GROUP_TERM_GRACE_MILLISECONDS: Final = 500
PROCESS_GROUP_KILL_GRACE_MILLISECONDS: Final = 2_000
PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS: Final = 10
DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS: Final = 2_000
PROCESS_GROUP_TERM_GRACE_SECONDS: Final = PROCESS_GROUP_TERM_GRACE_MILLISECONDS / 1_000
PROCESS_GROUP_KILL_GRACE_SECONDS: Final = PROCESS_GROUP_KILL_GRACE_MILLISECONDS / 1_000
PROCESS_GROUP_POLL_INTERVAL_SECONDS: Final = (
    PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS / 1_000
)
DIRECT_CHILD_REAP_TIMEOUT_SECONDS: Final = (
    DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS / 1_000
)
UNGUARDED_SOURCE_SHA256: Final = (
    "79c675b9023e315c30c52eccb5713aa326fa3d7b8dbd05ac32d107dd7410e90f"
)
UNGUARDED_CANARY: Final = b"pid-rs/lean-14576/eof/issue_14576.lean/unguarded"
UNGUARDED_GUARD: Final = (
    b"/--\nerror: (kernel) invalid projection\n  w.1\n-/\n#guard_msgs in\nmkbug\n"
)
UNGUARDED_COMMAND: Final = b"mkbug\n"
TRUST_ZERO_ARGUMENT: Final = "--trust=0"
LEANCHECKER_FRESH_ENVIRONMENT_ARGUMENT: Final = "--fresh"
TRUST_ZERO_SEMANTICS: Final = {
    "argument": "--trust=0",
    "help_meaning": "do_not_trust_any_macro_and_type_check_all_imported_modules",
    "no_macros_trusted": True,
    "all_imported_modules_typechecked": True,
    "selected_lean_implementation_and_runtime_remain_trusted": True,
    "zero_tcb": False,
}
LEANCHECKER_FRESH_SEMANTICS: Final = {
    "argument": "--fresh",
    "external_verifier": False,
    "fresh_replay_rechecks_source_elaboration_or_guarded_commands": False,
    "full_fixture_bad_declaration_source_present": True,
    "full_fixture_bad_thmdecl_reached_or_attempted": False,
    "full_fixture_post_failure_unknown_bad_reference_guard": True,
    "guard_msgs_rerun": False,
    "initial_environment": "mkEmptyEnvironment",
    "independent_kernel_implementation": False,
    "ordinary_olean_count": 3,
    "ordinary_olean_files_in_mode_0700_private_temporary_tree": True,
    "complete_declaration_inventory_claimed": False,
    "selected_emitted_olean_name_probe_only": True,
    "residual_axiom_shaped_E_present_in_each_selected_target_olean": True,
    "rejected_constructor_E_mk_absent_in_each_selected_target_olean": True,
    "unreached_bad_declaration_absent_in_full_selected_target_olean": True,
    "minimum_fixture_bad_source_reference_probe_or_absence_claimed": False,
    "replayed_content": "imported_and_defined_constants",
    "same_executable_leaf_as_source_elaboration": False,
    "same_process_as_source_elaboration": False,
    "selected_release_implementation_and_runtime_remain_trusted": True,
    "source_reelaboration": False,
}
SAFE_CHILD_PATH: Final = os.defpath
ENVIRONMENT_PREFIXES_TO_REMOVE: Final = (
    "PYTHON",
    "LEAN",
    "LAKE",
    "ELAN",
    "LD_",
    "DYLD_",
    "GIT_",
)
ENVIRONMENT_KEYS_TO_REMOVE: Final = frozenset(
    (
        "CC",
        "CXX",
        "AR",
        "AS",
        "LD",
        "NM",
        "RANLIB",
        "STRIP",
        "OBJCOPY",
        "OBJDUMP",
        "CFLAGS",
        "CXXFLAGS",
        "CPPFLAGS",
        "LDFLAGS",
        "LIBRARY_PATH",
        "CPATH",
        "C_INCLUDE_PATH",
        "CPLUS_INCLUDE_PATH",
        "OBJC_INCLUDE_PATH",
        "SDKROOT",
        "MACOSX_DEPLOYMENT_TARGET",
        "DEVELOPER_DIR",
        "LIBPATH",
        "SHLIB_PATH",
        "GCONV_PATH",
        "GLIBC_TUNABLES",
        "RUSTC",
        "RUSTFLAGS",
        "RUSTDOCFLAGS",
        "RUSTUP_TOOLCHAIN",
        "CARGO_BUILD_RUSTC",
        "CARGO_ENCODED_RUSTFLAGS",
    )
)
HOST_ENVIRONMENT_KEYS_TO_RETAIN: Final = (
    "SystemRoot",
    "WINDIR",
)
BENIGN_SOURCE_SHA256: Final = (
    "f8b55af8ef253edd4f37dab119104caad470a6a1c787759797cbf8b402f34782"
)
BENIGN_CANARY: Final = b"pid-rs/lean-14576/eof/issue_14576_min.lean/benign"
BENIGN_INVALID_PROJECTION: Final = b"  let b := mkProj ``C 0 (mkProj ``C 0 w)\n"
BENIGN_VALID_PROJECTION: Final = b"  let b := mkProj ``W 0 w\n"
BENIGN_LOG_TYPE: Final = b"  logInfo ct\n"
BENIGN_LOG_ACCEPTED: Final = b'  logInfo "E accepted"\n'
TARGET_OLEAN_LOOKUP_POSITIVE: Final = "PidRsTargetOleanLookupPositive"
TARGET_OLEAN_LOOKUP_NEGATIVE: Final = "PidRsTargetOleanLookupNegative"

LEAN_VERSION_LINE = re.compile(
    rb"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    rb"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
    rb"commit (?P<commit>[0-9a-f]{40}), "
    rb"(?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)\n\Z"
)
LAKE_VERSION_LINE = re.compile(
    rb"Lake version (?P<version>[0-9]+\.[0-9]+\.[0-9]+-src\+[0-9a-f]{7}) "
    rb"\(Lean version (?P<lean_version>[0-9]+\.[0-9]+\.[0-9]+)\)\n\Z"
)


@dataclass(frozen=True)
class FixtureSpec:
    """Exact upstream regression identity and guarded diagnostic sentinels."""

    name: str
    size: int
    sha256: str
    guarded_diagnostic: bytes
    post_failure_bad_reference_guard: bytes | None

    @property
    def path(self) -> Path:
        return FIXTURE_ROOT / self.name

    @property
    def canary(self) -> bytes:
        token = f"pid-rs/lean-14576/eof/{self.name}/{self.sha256}"
        return token.encode("ascii")

    @property
    def target_olean_inventory_canary(self) -> bytes:
        token = f"pid-rs/lean-14576/target-olean-inventory/{self.name}/{self.sha256}"
        return token.encode("ascii")


FIXTURES: Final = (
    FixtureSpec(
        name="issue_14576.lean",
        size=2460,
        sha256="0aaec9548df29266061467e37026935391a05bf6142fd027915f40c687a889e2",
        guarded_diagnostic=(
            b"/--\nerror: (kernel) invalid projection\n  w.1\n-/\n"
            b"#guard_msgs in\nmkbug\n"
        ),
        post_failure_bad_reference_guard=(
            b"/-- error: Unknown identifier `bad` -/\n"
            b"#guard_msgs in\ntheorem boom : False := nomatch (bad : T false)\n"
        ),
    ),
    FixtureSpec(
        name="issue_14576_min.lean",
        size=804,
        sha256="77769c1ce88649f56bf1fc8a0ae89fafdef25eae17b744fc7f28cb7b9519cbb5",
        guarded_diagnostic=(
            b"/--\ninfo: (w : W) \xe2\x86\x92 L (E w) w.1.1 \xe2\x86\x92 E w\n---\n"
            b"error: (kernel) invalid projection\n  w.1\n-/\n"
            b"#guard_msgs in\nmkbug\n"
        ),
        post_failure_bad_reference_guard=None,
    ),
)


class LeanKernel14576Error(RuntimeError):
    """The pin, input custody, process route, or regression outcome failed."""


@dataclass(frozen=True)
class FileIdentity:
    """Leaf metadata used in the bounded pre/process/post stability window."""

    device: int
    inode: int
    mode: int
    links: int
    size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class PathComponentIdentity:
    """One lexical path component at a bounded observation endpoint."""

    path: Path
    identity: FileIdentity
    symlink_target: str | None


@dataclass(frozen=True)
class StableSnapshot:
    """Exact bytes plus stable leaf and lexical-parent endpoint identities."""

    path: Path
    data: bytes
    sha256: str
    identity: FileIdentity
    lexical_root: Path
    expected_permissions: int
    parent_identities: tuple[PathComponentIdentity, ...]


@dataclass(frozen=True)
class ExecutableSnapshot:
    """Absolute launch route plus the resolved executable leaf and exact bytes."""

    launch_path: Path
    launch_identity: FileIdentity
    launch_target: str | None
    canonical_path: Path
    canonical_identity: FileIdentity
    canonical_data: bytes
    canonical_sha256: str
    launch_route: tuple[PathComponentIdentity, ...]
    canonical_route: tuple[PathComponentIdentity, ...]


@dataclass(frozen=True)
class ProcessResult:
    """Raw bounded child-process result."""

    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass(frozen=True)
class LeanIdentity:
    """Portable fields parsed from one exact Lean version line."""

    version: str
    platform: str
    commit: str
    build: str


@dataclass(frozen=True)
class LakeIdentity:
    """Exact bundled Lake and Lean versions parsed from `lake --version`."""

    version: str
    lean_version: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanKernel14576Error(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_neutral_fresh_environment_namespace(source: bytes) -> None:
    forbidden = (
        b"same_" + b"kernel_fresh_environment",
        b"SAME_" + b"KERNEL_FRESH_ENVIRONMENT",
        b"same-" + b"kernel fresh-environment",
    )
    for token in forbidden:
        require(
            token not in source,
            "ambiguous legacy fresh-environment namespace resurfaced",
        )


def identity_from_stat(observed: os.stat_result) -> FileIdentity:
    return FileIdentity(
        device=observed.st_dev,
        inode=observed.st_ino,
        mode=observed.st_mode,
        links=observed.st_nlink,
        size=observed.st_size,
        modified_ns=observed.st_mtime_ns,
        changed_ns=observed.st_ctime_ns,
    )


def component_identity_from_stat(observed: os.stat_result) -> FileIdentity:
    """Bind directory object identity without unrelated child-entry metadata."""

    if stat.S_ISDIR(observed.st_mode):
        return FileIdentity(
            device=observed.st_dev,
            inode=observed.st_ino,
            mode=observed.st_mode,
            links=0,
            size=0,
            modified_ns=0,
            changed_ns=0,
        )
    return identity_from_stat(observed)


def private_directory_identity(path: Path) -> FileIdentity:
    absolute = Path(os.path.abspath(os.fspath(path)))
    try:
        observed = absolute.lstat()
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot lstat private temporary directory {absolute}: {error}"
        ) from error
    require(
        stat.S_ISDIR(observed.st_mode) and not stat.S_ISLNK(observed.st_mode),
        f"private temporary route is not a direct directory: {absolute}",
    )
    require(
        stat.S_IMODE(observed.st_mode) == 0o700,
        f"private temporary directory permissions drifted: {absolute}; "
        f"expected 0o700, found {oct(stat.S_IMODE(observed.st_mode))}",
    )
    return component_identity_from_stat(observed)


def enforce_private_directory_mode(path: Path) -> FileIdentity:
    """Set and verify mode 0700 after creation, independent of the ambient umask."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    try:
        before = absolute.lstat()
        require(
            stat.S_ISDIR(before.st_mode) and not stat.S_ISLNK(before.st_mode),
            f"private temporary route is not a direct directory: {absolute}",
        )
        absolute.chmod(0o700)
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot enforce private temporary directory mode: {absolute}: {error}"
        ) from error
    return private_directory_identity(absolute)


def require_private_directory_unchanged(path: Path, expected: FileIdentity) -> None:
    observed = private_directory_identity(path)
    require(
        observed == expected,
        f"private temporary directory identity changed: {path}",
    )


def file_identity(path: Path, *, single_link: bool = True) -> FileIdentity:
    try:
        observed = path.lstat()
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot lstat required input {path}: {error}"
        ) from error
    require(stat.S_ISREG(observed.st_mode), f"required input is not regular: {path}")
    require(not path.is_symlink(), f"required input is symbolic link: {path}")
    if single_link:
        require(
            observed.st_nlink == 1, f"required input must have one hard link: {path}"
        )
    return identity_from_stat(observed)


def inspect_lexical_parents(
    path: Path, lexical_root: Path
) -> tuple[PathComponentIdentity, ...]:
    """Bind non-symlink parents from one explicit lexical root to the leaf."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    root = Path(os.path.abspath(os.fspath(lexical_root)))
    try:
        relative = absolute.relative_to(root)
    except ValueError as error:
        raise LeanKernel14576Error(f"input escapes repository root: {path}") from error
    identities: list[PathComponentIdentity] = []
    cursor = root
    for part in (None, *relative.parts[:-1]):
        if part is not None:
            cursor /= part
        try:
            observed = cursor.lstat()
        except OSError as error:
            raise LeanKernel14576Error(
                f"cannot lstat lexical input parent {cursor}: {error}"
            ) from error
        require(
            stat.S_ISDIR(observed.st_mode), f"input parent is not a directory: {cursor}"
        )
        require(not cursor.is_symlink(), f"input parent is symbolic link: {cursor}")
        identities.append(
            PathComponentIdentity(
                path=cursor,
                identity=component_identity_from_stat(observed),
                symlink_target=None,
            )
        )
    return tuple(identities)


def inspect_absolute_route(path: Path) -> tuple[PathComponentIdentity, ...]:
    """Snapshot every lexical component, including symlink targets, of a route."""

    absolute = Path(os.path.abspath(os.fspath(path)))
    require(absolute.is_absolute(), f"path route is not absolute: {path}")
    components: list[PathComponentIdentity] = []
    cursor = Path(absolute.anchor)
    paths = [cursor]
    for part in absolute.parts[1:]:
        cursor /= part
        paths.append(cursor)
    for index, component in enumerate(paths):
        try:
            observed = component.lstat()
            target = os.readlink(component) if stat.S_ISLNK(observed.st_mode) else None
        except OSError as error:
            raise LeanKernel14576Error(
                f"cannot inspect executable route component {component}: {error}"
            ) from error
        if index + 1 < len(paths):
            require(
                stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode),
                f"executable route parent is neither directory nor symbolic link: {component}",
            )
        components.append(
            PathComponentIdentity(
                path=component,
                identity=component_identity_from_stat(observed),
                symlink_target=target,
            )
        )
    return tuple(components)


def read_descriptor_bytes(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def snapshot(
    path: Path,
    *,
    expected_permissions: int = 0o644,
    lexical_root: Path = ROOT,
) -> StableSnapshot:
    absolute = Path(os.path.abspath(os.fspath(path)))
    root = Path(os.path.abspath(os.fspath(lexical_root)))
    parents_before = inspect_lexical_parents(absolute, root)
    before = file_identity(absolute)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot open required input {absolute}: {error}"
        ) from error
    try:
        descriptor_before = identity_from_stat(os.fstat(descriptor))
        first = read_descriptor_bytes(descriptor)
        middle = identity_from_stat(os.fstat(descriptor))
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = read_descriptor_bytes(descriptor)
        descriptor_after = identity_from_stat(os.fstat(descriptor))
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot read required input {absolute}: {error}"
        ) from error
    finally:
        os.close(descriptor)
    after = file_identity(absolute)
    parents_after = inspect_lexical_parents(absolute, root)
    require(
        before == descriptor_before == middle == descriptor_after == after,
        f"input identity changed during double read: {absolute}",
    )
    require(first == second, f"input bytes changed during double read: {absolute}")
    require(
        len(first) == before.size, f"input size disagrees with metadata: {absolute}"
    )
    require(
        parents_after == parents_before,
        f"input parent identity changed during double read: {absolute}",
    )
    require(
        stat.S_IMODE(before.mode) == expected_permissions,
        f"required input permissions drifted: {absolute}; expected {oct(expected_permissions)}, "
        f"found {oct(stat.S_IMODE(before.mode))}",
    )
    return StableSnapshot(
        path=absolute,
        data=first,
        sha256=digest(first),
        identity=before,
        lexical_root=root,
        expected_permissions=expected_permissions,
        parent_identities=parents_before,
    )


def require_unchanged(original: StableSnapshot) -> None:
    replay = snapshot(
        original.path,
        expected_permissions=original.expected_permissions,
        lexical_root=original.lexical_root,
    )
    require(
        replay.identity == original.identity,
        f"input identity changed across Lean execution: {original.path}",
    )
    require(
        replay.data == original.data,
        f"input bytes changed across Lean execution: {original.path}",
    )
    require(
        replay.parent_identities == original.parent_identities,
        f"input parent identity changed across Lean execution: {original.path}",
    )


def validate_fixture_payload(spec: FixtureSpec, data: bytes) -> None:
    require(len(data) == spec.size, f"{spec.name} byte length drifted")
    require(digest(data) == spec.sha256, f"{spec.name} SHA-256 drifted")
    require(data.endswith(b"\n"), f"{spec.name} lacks one final newline")
    require(b"\r" not in data, f"{spec.name} contains a carriage return")
    require(
        data.count(spec.guarded_diagnostic) == 1,
        f"{spec.name} fixed invalid-projection guard is absent or ambiguous",
    )
    if spec.post_failure_bad_reference_guard is not None:
        require(
            data.count(spec.post_failure_bad_reference_guard) == 1,
            f"{spec.name} post-failure unknown-identifier reference guard is absent or ambiguous",
        )


def validate_fixture_inventory(specs: tuple[FixtureSpec, ...]) -> None:
    expected = (
        ("issue_14576.lean", 2460, FIXTURES[0].sha256),
        ("issue_14576_min.lean", 804, FIXTURES[1].sha256),
    )
    observed = tuple((spec.name, spec.size, spec.sha256) for spec in specs)
    require(observed == expected, "issue #14576 fixture order or identity drifted")


def expected_origin() -> dict[str, object]:
    return {
        "files": [
            {
                "bytes": 2460,
                "line_count": 67,
                "path": "issue_14576.lean",
                "raw_url": (
                    "https://raw.githubusercontent.com/leanprover/lean4/"
                    "f3b06c705e6c85f5314019d5d3baab0fec5b580c/tests/elab/"
                    "issue_14576.lean"
                ),
                "sha256": FIXTURES[0].sha256,
                "upstream_path": "tests/elab/issue_14576.lean",
            },
            {
                "bytes": 804,
                "line_count": 30,
                "path": "issue_14576_min.lean",
                "raw_url": (
                    "https://raw.githubusercontent.com/leanprover/lean4/"
                    "f3b06c705e6c85f5314019d5d3baab0fec5b580c/tests/elab/"
                    "issue_14576_min.lean"
                ),
                "sha256": FIXTURES[1].sha256,
                "upstream_path": "tests/elab/issue_14576_min.lean",
            },
        ],
        "fixtures_retrieved_utc_date": "2026-08-02",
        "implementation_source_observations": {
            "authentication": "none",
            "bytes_retained_in_this_packet": False,
            "files": [
                {
                    "bytes": 22_896,
                    "git_blob_sha1": "9362f91601943cac8b4c0a52da42337775517c3b",
                    "path": "src/Lean/Shell.lean",
                    "raw_url": (
                        "https://raw.githubusercontent.com/leanprover/lean4/"
                        "f3b06c705e6c85f5314019d5d3baab0fec5b580c/src/Lean/Shell.lean"
                    ),
                    "sha256": (
                        "6ffb68a347815e43fe5771205bd02236e1508132b9197c27a3d805fe1cad7ab7"
                    ),
                    "supports_selected_claims": ["trust_zero_cli_help_text"],
                },
                {
                    "bytes": 4_785,
                    "git_blob_sha1": "48cb20f85c581365e425e803b2cb9352d07eb29b",
                    "path": "src/LeanChecker.lean",
                    "raw_url": (
                        "https://raw.githubusercontent.com/leanprover/lean4/"
                        "f3b06c705e6c85f5314019d5d3baab0fec5b580c/src/LeanChecker.lean"
                    ),
                    "sha256": (
                        "eb5dee411837629f09c5c18d63cc833d30335a46048bc586642742e90aa65d5f"
                    ),
                    "supports_selected_claims": [
                        "fresh_replayFromFresh_uses_mkEmptyEnvironment",
                        "leanchecker_documented_as_not_an_external_verifier",
                    ],
                },
                {
                    "bytes": 133_867,
                    "git_blob_sha1": "cf5faa124bc5fee64aca6ad40754b0540498997f",
                    "path": "src/Lean/Environment.lean",
                    "raw_url": (
                        "https://raw.githubusercontent.com/leanprover/lean4/"
                        "f3b06c705e6c85f5314019d5d3baab0fec5b580c/src/Lean/Environment.lean"
                    ),
                    "sha256": (
                        "100b207523d1005ae87f62f4e1693806854a35c59cd9b3210dfeeaa875d0ff98"
                    ),
                    "supports_selected_claims": [
                        "imported_constant_trust_level_semantics"
                    ],
                },
            ],
            "observed_utc_date": "2026-08-07",
            "source_commit": EXPECTED_LEAN_COMMIT,
            "source_to_binary_provenance": False,
            "status": "exact_unauthenticated_source_byte_observations",
        },
        "issue_url": "https://github.com/leanprover/lean4/issues/14576",
        "local_mapping_boundary": {
            "leanchecker_fresh_is_postmortem_named_external_checker": False,
        },
        "official_postmortem": {
            "bug_area": "nested_inductive_kernel_handling",
            "external_checker_named_by_postmortem": "nanoda",
            "fix_pull_request": 14577,
            "frontend_checks_arguments_and_catches_ill_typed_term": True,
            "frontend_is_untrusted_by_design": True,
            "frontend_rejection_is_sufficient_kernel_assurance": False,
            "independent_kernel_is_distinct_assurance_layer": True,
            "patch_releases_reported_without_version_identification": True,
            "postmortem_checked_utc_date": "2026-08-07",
            "publication_date": "2026-08-01",
            "url": (
                "https://leodemoura.github.io/blog/2026-8-1-"
                "postmortem-for-kernel-soundness-bug-14576/"
            ),
        },
        "pr_url": "https://github.com/leanprover/lean4/pull/14577",
        "record_provenance": (
            "project_defined_metadata_binding_exact_upstream_fixture_bytes"
        ),
        "repository_path": "audit/formal/lean-kernel-regression/issue-14576",
        "schema": "pid-rs/lean-upstream-regression-origin/v4",
        "source_commit": EXPECTED_LEAN_COMMIT,
        "source_repository": "https://github.com/leanprover/lean4",
        "source_tag": "v4.32.2",
        "status": "exact_upstream_bytes_unmodified",
    }


def require_exact_json_value(observed: object, expected: object, role: str) -> None:
    require(type(observed) is type(expected), f"{role} JSON type drifted")
    if isinstance(expected, dict):
        require(isinstance(observed, dict), f"{role} must be an object")
        require(set(observed) == set(expected), f"{role} object keys drifted")
        for key, expected_value in expected.items():
            require_exact_json_value(observed[key], expected_value, f"{role}.{key}")
        return
    if isinstance(expected, list):
        require(isinstance(observed, list), f"{role} must be an array")
        require(len(observed) == len(expected), f"{role} array length drifted")
        for index, expected_value in enumerate(expected):
            require_exact_json_value(
                observed[index], expected_value, f"{role}[{index}]"
            )
        return
    require(observed == expected, f"{role} JSON value drifted")


def validate_origin_semantics(parsed: object) -> None:
    require_exact_json_value(parsed, expected_origin(), "origin.json")


def validate_origin_payload(data: bytes) -> None:
    require(digest(data) == EXPECTED_ORIGIN_SHA256, "origin.json SHA-256 drifted")
    require(b"\r" not in data and data.endswith(b"\n"), "origin.json transport drifted")
    parsed = parse_json_object(data, "origin.json")
    validate_origin_semantics(parsed)


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Reject ambiguous JSON objects before any release-policy projection."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LeanKernel14576Error(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def reject_nonfinite_json_constant(token: str) -> object:
    """Reject Python's non-standard NaN/Infinity JSON extensions."""

    raise LeanKernel14576Error(f"non-finite JSON constant is forbidden: {token}")


def reject_json_float(token: str) -> object:
    """Reject every JSON float token; packet schemas contain integers only."""

    raise LeanKernel14576Error(f"JSON floating-point number is forbidden: {token}")


def parse_json_object(data: bytes, role: str) -> dict[str, object]:
    require(b"\r" not in data, f"{role} contains a carriage return")
    try:
        parsed = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_nonfinite_json_constant,
            parse_float=reject_json_float,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise LeanKernel14576Error(
            f"{role} is not strict duplicate-free UTF-8 JSON: {error}"
        ) from error
    require(isinstance(parsed, dict), f"{role} root must be an object")
    return parsed


def canonical_metadata_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise LeanKernel14576Error(
            f"toolchain metadata is not canonical JSON: {error}"
        ) from error
    return (rendered + "\n").encode("ascii")


def canonical_json_bytes(value: object) -> bytes:
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise LeanKernel14576Error(
            f"toolchain policy is not canonical JSON: {error}"
        ) from error
    return rendered.encode("ascii")


def toolchain_metadata_policy_projection(
    metadata: dict[str, object],
) -> dict[str, object]:
    """Return the acyclic policy projection consumed by this nested checker.

    The enclosing custody checker's finalized size/digest and this nested
    checker's finalized size/digest are omitted.  Their paths, topology policy,
    and every release/asset/lifecycle/non-implication field remain in the
    projection.  Runtime separately compares this checker's omitted size and
    digest to its exact source snapshot.
    """

    binding = metadata.get("checker_binding")
    require(isinstance(binding, dict), "toolchain checker binding is absent")
    expected_binding_keys = {
        "checker_bytes",
        "checker_path",
        "checker_sha256",
        "nested_checker_binding",
        "policy",
        "projection_omits",
    }
    require(
        set(binding) == expected_binding_keys,
        "toolchain checker binding keys drifted",
    )
    nested = binding.get("nested_checker_binding")
    require(isinstance(nested, dict), "nested checker binding is absent")
    expected_nested_keys = {
        "bytes",
        "mode",
        "path",
        "sha256",
        "single_hard_link",
        "symbolic_link",
    }
    require(
        set(nested) == expected_nested_keys,
        "nested checker binding keys drifted",
    )
    projected_nested = {
        key: value for key, value in nested.items() if key not in {"bytes", "sha256"}
    }
    projected_binding = {
        key: value
        for key, value in binding.items()
        if key not in {"checker_bytes", "checker_sha256", "nested_checker_binding"}
    }
    projected_binding["nested_checker_binding"] = projected_nested
    projection = dict(metadata)
    projection["checker_binding"] = projected_binding
    return projection


def toolchain_metadata_policy_sha256(metadata: dict[str, object]) -> str:
    return digest(canonical_json_bytes(toolchain_metadata_policy_projection(metadata)))


def validate_nested_self_binding(
    metadata: dict[str, object], checker_source: StableSnapshot
) -> None:
    binding = metadata["checker_binding"]
    require(isinstance(binding, dict), "toolchain checker binding is absent")
    nested = binding["nested_checker_binding"]
    require(isinstance(nested, dict), "nested checker binding is absent")
    expected_path = "scripts/check-lean-kernel-14576.py"
    require(nested.get("path") == expected_path, "nested checker path binding drifted")
    require(
        type(nested.get("bytes")) is int
        and nested["bytes"] == checker_source.identity.size,
        "nested checker byte-length binding drifted",
    )
    require(
        nested.get("sha256") == checker_source.sha256,
        "nested checker SHA-256 binding drifted",
    )
    require(nested.get("mode") == "0644", "nested checker mode binding drifted")
    require(
        nested.get("single_hard_link") is True and checker_source.identity.links == 1,
        "nested checker link-count binding drifted",
    )
    require(
        nested.get("symbolic_link") is False and not checker_source.path.is_symlink(),
        "nested checker symbolic-link binding drifted",
    )
    require(
        checker_source.path == ROOT / expected_path,
        "nested checker source path differs from its repository binding",
    )


def load_toolchain_metadata_policy(
    metadata_snapshot: StableSnapshot, checker_source: StableSnapshot
) -> dict[str, object]:
    metadata = parse_json_object(
        metadata_snapshot.data, "Lean toolchain release metadata"
    )
    require(
        metadata_snapshot.data == canonical_metadata_bytes(metadata),
        "Lean toolchain release metadata is not canonical sorted JSON",
    )
    require(
        metadata.get("schema") == EXPECTED_TOOLCHAIN_METADATA_SCHEMA,
        "Lean toolchain release metadata schema drifted",
    )
    require(
        toolchain_metadata_policy_sha256(metadata)
        == EXPECTED_TOOLCHAIN_METADATA_POLICY_SHA256,
        "Lean toolchain metadata policy projection SHA-256 drifted",
    )
    validate_nested_self_binding(metadata, checker_source)
    return metadata


def scrubbed_environment(
    *,
    ambient: dict[str, str] | None = None,
    lean_path: Path | None = None,
    tool_bin: Path | None = None,
) -> dict[str, str]:
    """Project only OS-required host state plus controlled path/import roots."""

    source = os.environ if ambient is None else ambient
    environment: dict[str, str] = {}
    for key in HOST_ENVIRONMENT_KEYS_TO_RETAIN:
        value = source.get(key)
        if value is not None:
            environment[key] = value
    child_path = SAFE_CHILD_PATH
    if tool_bin is not None:
        absolute_bin = Path(os.path.abspath(os.fspath(tool_bin)))
        require(absolute_bin.is_absolute(), "controlled tool bin is not absolute")
        require(
            os.pathsep not in os.fspath(absolute_bin),
            "controlled tool bin contains the path-list separator",
        )
        child_path = os.fspath(absolute_bin) + os.pathsep + SAFE_CHILD_PATH
    environment.update({"LANG": "C", "LC_ALL": "C", "PATH": child_path})
    if lean_path is not None:
        absolute = Path(os.path.abspath(os.fspath(lean_path)))
        require(absolute.is_absolute(), "controlled Lean import root is not absolute")
        require(
            os.pathsep not in os.fspath(absolute),
            "controlled Lean import root contains the path-list separator",
        )
        environment["LEAN_PATH"] = os.fspath(absolute)
    require_environment_scrubbed(
        environment,
        allowed_lean_path=lean_path,
        allowed_tool_bin=tool_bin,
    )
    return environment


def require_environment_scrubbed(
    environment: dict[str, str],
    *,
    allowed_lean_path: Path | None = None,
    allowed_tool_bin: Path | None = None,
    allowed_private_home: Path | None = None,
    allowed_private_tmp: Path | None = None,
) -> None:
    permitted = set(HOST_ENVIRONMENT_KEYS_TO_RETAIN) | {"LANG", "LC_ALL", "PATH"}
    expected_lean_path: str | None = None
    if allowed_lean_path is not None:
        expected_lean_path = os.fspath(
            Path(os.path.abspath(os.fspath(allowed_lean_path)))
        )
        permitted.add("LEAN_PATH")
    if allowed_private_home is not None:
        permitted.add("HOME")
    if allowed_private_tmp is not None:
        permitted.add("TMPDIR")
    unexpected = sorted(set(environment).difference(permitted))
    require(
        not unexpected,
        f"unexpected child-process environment keys remain: {unexpected}",
    )
    forbidden = sorted(
        key
        for key in environment
        if (
            key in ENVIRONMENT_KEYS_TO_REMOVE
            or key.startswith(ENVIRONMENT_PREFIXES_TO_REMOVE)
        )
        and not (key == "LEAN_PATH" and expected_lean_path is not None)
    )
    require(
        not forbidden, f"forbidden child-process environment routes remain: {forbidden}"
    )
    expected_path = SAFE_CHILD_PATH
    if allowed_tool_bin is not None:
        expected_path = (
            os.fspath(Path(os.path.abspath(os.fspath(allowed_tool_bin))))
            + os.pathsep
            + SAFE_CHILD_PATH
        )
    require(
        environment.get("PATH") == expected_path,
        "child PATH is not the fixed safe path",
    )
    require(
        environment.get("LANG") == "C" and environment.get("LC_ALL") == "C",
        "child locale is not fixed to C",
    )
    require(
        expected_lean_path is None
        or environment.get("LEAN_PATH") == expected_lean_path,
        "controlled Lean import root drifted",
    )
    require(
        allowed_private_home is None
        or environment.get("HOME")
        == os.fspath(Path(os.path.abspath(os.fspath(allowed_private_home)))),
        "private child HOME drifted",
    )
    require(
        allowed_private_tmp is None
        or environment.get("TMPDIR")
        == os.fspath(Path(os.path.abspath(os.fspath(allowed_private_tmp)))),
        "private child TMPDIR drifted",
    )
    require(
        all(
            "\x00" not in key and "\x00" not in value
            for key, value in environment.items()
        ),
        "child environment contains a NUL",
    )


def snapshot_executable_route(path: Path) -> ExecutableSnapshot:
    """Snapshot an absolute launcher route and its fully resolved executable leaf."""

    require(path.is_absolute(), f"executable launch route is not absolute: {path}")
    absolute = Path(os.path.abspath(os.fspath(path)))
    launch_route_before = inspect_absolute_route(absolute)
    try:
        launch_stat = absolute.lstat()
        require(
            stat.S_ISREG(launch_stat.st_mode) or stat.S_ISLNK(launch_stat.st_mode),
            f"executable launch route is neither regular nor symbolic link: {absolute}",
        )
        launch_target = os.readlink(absolute) if absolute.is_symlink() else None
        resolved = absolute.resolve(strict=True)
        canonical_route_before = inspect_absolute_route(resolved)
        before = file_identity(resolved)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(resolved, flags)
        try:
            descriptor_before = identity_from_stat(os.fstat(descriptor))
            first = read_descriptor_bytes(descriptor)
            middle = identity_from_stat(os.fstat(descriptor))
            os.lseek(descriptor, 0, os.SEEK_SET)
            second = read_descriptor_bytes(descriptor)
            descriptor_after = identity_from_stat(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        after = file_identity(resolved)
        canonical_route_after = inspect_absolute_route(resolved)
        launch_route_after = inspect_absolute_route(absolute)
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot resolve executable {path}: {error}"
        ) from error
    require(resolved.is_absolute(), f"executable route is not absolute: {resolved}")
    require(
        before == descriptor_before == middle == descriptor_after == after,
        f"executable leaf identity changed during double read: {resolved}",
    )
    require(
        first == second, f"executable leaf bytes changed during double read: {resolved}"
    )
    require(
        len(first) == before.size,
        f"executable leaf size disagrees with metadata: {resolved}",
    )
    require(before.mode & 0o111 != 0, f"executable leaf lacks execute mode: {resolved}")
    require(
        launch_route_before == launch_route_after,
        f"executable launch route changed during double read: {absolute}",
    )
    require(
        canonical_route_before == canonical_route_after,
        f"canonical executable route changed during double read: {resolved}",
    )
    return ExecutableSnapshot(
        launch_path=absolute,
        launch_identity=identity_from_stat(launch_stat),
        launch_target=launch_target,
        canonical_path=resolved,
        canonical_identity=before,
        canonical_data=first,
        canonical_sha256=digest(first),
        launch_route=launch_route_before,
        canonical_route=canonical_route_before,
    )


def require_executable_unchanged(original: ExecutableSnapshot) -> ExecutableSnapshot:
    replay = snapshot_executable_route(original.launch_path)
    require(
        replay.launch_identity == original.launch_identity
        and replay.launch_target == original.launch_target
        and replay.launch_route == original.launch_route,
        "executable launch route changed across Lean execution",
    )
    require(
        replay.canonical_path == original.canonical_path,
        "canonical executable path changed across Lean execution",
    )
    require(
        replay.canonical_identity == original.canonical_identity
        and replay.canonical_data == original.canonical_data
        and replay.canonical_route == original.canonical_route,
        "canonical executable leaf changed across Lean execution",
    )
    return replay


def executable_leaf_evidence(snapshot: ExecutableSnapshot) -> dict[str, object]:
    identity = snapshot.canonical_identity
    return {
        "launch_path": os.fspath(snapshot.launch_path),
        "canonical_path": os.fspath(snapshot.canonical_path),
        "bytes": len(snapshot.canonical_data),
        "sha256": snapshot.canonical_sha256,
        "identity": {
            "device": identity.device,
            "inode": identity.inode,
            "mode": identity.mode,
            "permissions": oct(stat.S_IMODE(identity.mode)),
            "links": identity.links,
            "size": identity.size,
            "modified_ns": identity.modified_ns,
            "changed_ns": identity.changed_ns,
        },
    }


def validate_direct_tool_layout(
    tools: dict[str, ExecutableSnapshot],
) -> None:
    """Require three distinct leaves selected from one exact toolchain bin directory."""

    require(
        tuple(tools) == ("lean", "lake", "leanchecker"),
        "direct tool inventory or order drifted",
    )
    launch_parents = {snapshot.launch_path.parent for snapshot in tools.values()}
    canonical_parents = {snapshot.canonical_path.parent for snapshot in tools.values()}
    require(
        len(launch_parents) == 1,
        "selected tool launch leaves do not share one bin directory",
    )
    require(
        len(canonical_parents) == 1,
        "selected tool canonical leaves do not share one bin directory",
    )
    require(
        len({snapshot.canonical_path for snapshot in tools.values()}) == len(tools),
        "selected tool canonical leaves are not distinct",
    )
    for role, observed in tools.items():
        require(
            observed.launch_path.name in {role, f"{role}.exe"},
            f"selected {role} leaf basename drifted",
        )
        require(
            observed.canonical_path.name in {role, f"{role}.exe"},
            f"canonical {role} leaf basename drifted",
        )


def reviewed_strict_replay_host_asset(
    metadata: dict[str, object],
) -> dict[str, object]:
    """Select the one reviewed-pin strict-replay asset for the current host."""

    assets = metadata.get("assets")
    require(isinstance(assets, list), "Lean toolchain asset inventory is absent")
    system = platform.system()
    machine = platform.machine().lower()
    matching: list[dict[str, object]] = []
    for candidate in assets:
        if not isinstance(candidate, dict):
            continue
        host = candidate.get("host")
        if not isinstance(host, dict):
            continue
        machines = host.get("machines")
        if (
            host.get("system") == system
            and isinstance(machines, list)
            and machine in [str(item).lower() for item in machines]
        ):
            matching.append(candidate)
    require(
        len(matching) == 1,
        f"expected one reviewed toolchain asset for {system}/{machine}, "
        f"found {len(matching)}",
    )
    asset = matching[0]
    lifecycle = asset.get("custody_lifecycle")
    require(
        isinstance(lifecycle, dict)
        and lifecycle.get("state") == "reviewed_pins_strict_replay_required"
        and lifecycle.get("permitted_route") == "strict_replay_only"
        and lifecycle.get("static_qualification_credit") == "none"
        and lifecycle.get("archive_custody_credit") == "none",
        f"toolchain asset {asset.get('key')!r} is not a reviewed-pin strict-replay asset",
    )
    leaves = lifecycle.get("leaves")
    require(
        isinstance(leaves, dict) and set(leaves) == {"lean", "lake", "leanchecker"},
        "reviewed toolchain executable-leaf inventory drifted",
    )
    archive = asset.get("archive")
    require(
        isinstance(archive, dict)
        and isinstance(archive.get("root"), str)
        and archive["root"],
        "reviewed toolchain archive root is absent",
    )
    return asset


def snapshot_direct_toolchain(
    toolchain_root: Path,
    asset: dict[str, object],
) -> dict[str, ExecutableSnapshot]:
    """Bind direct executable leaves to the reviewed archive metadata."""

    require(toolchain_root.is_absolute(), "--toolchain-root must be absolute")
    normalized = Path(os.path.abspath(os.fspath(toolchain_root)))
    require(
        normalized == toolchain_root,
        "--toolchain-root must be lexically normalized",
    )
    try:
        root_stat = normalized.lstat()
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot inspect direct toolchain root {normalized}: {error}"
        ) from error
    require(
        stat.S_ISDIR(root_stat.st_mode) and not stat.S_ISLNK(root_stat.st_mode),
        "direct toolchain root is not a real directory",
    )
    require(
        normalized.resolve(strict=True) == normalized,
        "direct toolchain root traverses a symbolic-link component",
    )
    archive = asset["archive"]
    require(
        normalized.name == archive["root"],
        "direct toolchain root basename differs from reviewed archive root",
    )
    lifecycle = asset["custody_lifecycle"]
    expected_leaves = lifecycle["leaves"]
    tools: dict[str, ExecutableSnapshot] = {}
    for role in ("lean", "lake", "leanchecker"):
        expected = expected_leaves[role]
        require(
            expected["path"] == f"bin/{role}" and expected["mode"] == "0755",
            f"reviewed {role} leaf route or mode drifted",
        )
        observed = snapshot_executable_route(normalized / "bin" / role)
        require(
            observed.launch_target is None
            and observed.launch_path == observed.canonical_path,
            f"direct {role} launch route is not a regular archive leaf",
        )
        require(
            observed.canonical_identity.size == expected["size"]
            and observed.canonical_sha256 == expected["sha256"]
            and stat.S_IMODE(observed.canonical_identity.mode) == 0o755,
            f"direct {role} leaf differs from reviewed archive metadata",
        )
        tools[role] = observed
    validate_direct_tool_layout(tools)
    return tools


def lean_version_command(lean: Path) -> tuple[str, ...]:
    require(lean.is_absolute(), "Lean version executable route is not absolute")
    return (os.fspath(lean), "--version")


def lake_version_command(lake: Path) -> tuple[str, ...]:
    require(lake.is_absolute(), "Lake version executable route is not absolute")
    return (os.fspath(lake), "--version")


def lean_source_command(lean: Path, source: Path) -> tuple[str, ...]:
    require(lean.is_absolute(), "Lean source executable route is not absolute")
    require(source.is_absolute(), "Lean source route is not absolute")
    return (os.fspath(lean), TRUST_ZERO_ARGUMENT, os.fspath(source))


def lean_compile_command(lean: Path, source: Path, olean: Path) -> tuple[str, ...]:
    require(lean.is_absolute(), "Lean compile executable route is not absolute")
    require(source.is_absolute(), "Lean compile source route is not absolute")
    require(olean.is_absolute(), "Lean compile output route is not absolute")
    return (
        os.fspath(lean),
        TRUST_ZERO_ARGUMENT,
        "-o",
        os.fspath(olean),
        os.fspath(source),
    )


def leanchecker_command(leanchecker: Path, module: str) -> tuple[str, ...]:
    require(leanchecker.is_absolute(), "leanchecker executable route is not absolute")
    require(
        re.fullmatch(r"[A-Z][A-Za-z0-9_]*", module) is not None,
        "leanchecker module name is outside the finite safe grammar",
    )
    return (
        os.fspath(leanchecker),
        LEANCHECKER_FRESH_ENVIRONMENT_ARGUMENT,
        module,
    )


def validate_lean_version_command(command: tuple[str, ...], lean: Path) -> None:
    require(
        command == lean_version_command(lean),
        f"Lean version command arguments drifted: {command!r}",
    )


def validate_lake_version_command(command: tuple[str, ...], lake: Path) -> None:
    require(
        command == lake_version_command(lake),
        f"Lake version command arguments drifted: {command!r}",
    )


def validate_lean_source_command(
    command: tuple[str, ...], lean: Path, source: Path
) -> None:
    require(
        command == lean_source_command(lean, source),
        f"Lean source command arguments drifted: {command!r}",
    )


def validate_lean_compile_command(
    command: tuple[str, ...], lean: Path, source: Path, olean: Path
) -> None:
    require(
        command == lean_compile_command(lean, source, olean),
        f"Lean compile command arguments drifted: {command!r}",
    )


def validate_leanchecker_command(
    command: tuple[str, ...], leanchecker: Path, module: str
) -> None:
    require(
        command == leanchecker_command(leanchecker, module),
        f"leanchecker command arguments drifted: {command!r}",
    )


def process_group_exists(process_group: int) -> bool:
    """Probe one captured POSIX process-group number without signalling members."""

    require(os.name == "posix", "process-group existence probes require POSIX")
    require(
        type(process_group) is int and process_group > 1,
        "captured process-group number is invalid",
    )
    require(
        process_group != os.getpgrp(),
        "refusing to inspect the current checker process group as a child group",
    )
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        # POSIX EPERM still proves that at least one process exists.  It can also be
        # observed briefly for an exited orphan/zombie group on supported hosts.
        # Keep treating the captured PGID as present and require bounded absence.
        return True
    return True


def wait_for_process_group_absence(
    process_group: int,
    seconds: float,
    direct_child: subprocess.Popen[bytes] | None = None,
) -> bool:
    """Poll for bounded group absence; this does not reap non-child descendants."""

    require(seconds >= 0.0, "process-group absence bound is negative")
    deadline = time.monotonic() + seconds
    if direct_child is not None:
        direct_child.poll()
    while process_group_exists(process_group):
        if direct_child is not None:
            direct_child.poll()
        remaining = deadline - time.monotonic()
        if remaining <= 0.0:
            return False
        time.sleep(min(PROCESS_GROUP_POLL_INTERVAL_SECONDS, remaining))
    return True


def cleanup_isolated_process_group(process: subprocess.Popen[bytes]) -> None:
    """Boundedly TERM/KILL one captured non-self group on every isolated outcome.

    ``start_new_session=True`` makes the direct child's PID the initial process-group
    number before ``exec``.  The number is captured even when that leader exits before
    this function runs, so same-group descendants are still addressed.  The checks are
    endpoint observations, not an atomic lifetime monitor; PGID reuse and a descendant
    that changes process group or session remains outside this bounded route.
    """

    require(os.name == "posix", "isolated process-group cleanup requires POSIX")
    process_group = process.pid
    require(
        process_group != os.getpgrp(),
        "refusing to signal the current checker process group",
    )
    for selected_signal, grace in (
        (signal.SIGTERM, PROCESS_GROUP_TERM_GRACE_SECONDS),
        (signal.SIGKILL, PROCESS_GROUP_KILL_GRACE_SECONDS),
    ):
        if not process_group_exists(process_group):
            break
        try:
            os.killpg(process_group, selected_signal)
        except ProcessLookupError:
            break
        except PermissionError as error:
            if wait_for_process_group_absence(process_group, grace, process):
                break
            if selected_signal == signal.SIGKILL:
                raise LeanKernel14576Error(
                    "captured child process group remained permission-denied after "
                    "bounded TERM/KILL cleanup"
                ) from error
            continue
        if wait_for_process_group_absence(process_group, grace, process):
            break
    process.poll()
    require(
        not process_group_exists(process_group),
        "captured child process group remained after bounded TERM/KILL cleanup",
    )
    try:
        process.wait(timeout=DIRECT_CHILD_REAP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise LeanKernel14576Error(
            "isolated direct child was not reaped after bounded group cleanup"
        ) from error


def terminate_direct_child_without_group_signal(
    process: subprocess.Popen[bytes],
) -> None:
    """Terminate/reap only the direct child; the outer supervisor owns its group."""

    if process.poll() is None:
        try:
            process.kill()
        except ProcessLookupError:
            pass
    try:
        process.communicate(timeout=DIRECT_CHILD_REAP_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise LeanKernel14576Error(
            "shared-group direct child did not terminate for outer-supervisor cleanup"
        ) from error


def terminate_nonposix_process_tree(process: subprocess.Popen[bytes]) -> None:
    """Best-effort non-POSIX fallback retained outside the POSIX assurance claim."""

    tree_kill_sent = False
    if process.poll() is None:
        try:
            if os.name == "nt":
                completed = subprocess.run(
                    ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=10,
                    check=False,
                )
                tree_kill_sent = completed.returncode == 0
        except (OSError, subprocess.SubprocessError):
            tree_kill_sent = False
        if not tree_kill_sent and process.poll() is None:
            process.kill()
    try:
        process.communicate(timeout=10)
    except subprocess.TimeoutExpired as error:
        raise LeanKernel14576Error(
            "timed-out non-POSIX process did not terminate after tree-kill fallback"
        ) from error


def run_process(
    command: list[str],
    *,
    cwd: Path,
    timeout: int | float = TIMEOUT_SECONDS,
    environment: dict[str, str] | None = None,
    tool_bin: Path | None = None,
    shared_outer_process_group: bool = False,
) -> ProcessResult:
    require(
        type(shared_outer_process_group) is bool,
        "shared outer process-group selection must be Boolean",
    )
    if shared_outer_process_group and os.name == "posix":
        require(
            os.getpgrp() == os.getpid(),
            "shared outer process-group mode requires this checker to be its group leader",
        )
    base_environment = (
        scrubbed_environment(tool_bin=tool_bin) if environment is None else environment
    )
    allowed_lean_path = (
        Path(base_environment["LEAN_PATH"]) if "LEAN_PATH" in base_environment else None
    )
    with (
        tempfile.TemporaryDirectory(
            prefix="pid-rs-lean-14576-child-environment-"
        ) as private_name,
        tempfile.TemporaryFile() as stdout_file,
        tempfile.TemporaryFile() as stderr_file,
    ):
        private_root = Path(os.path.abspath(private_name))
        enforce_private_directory_mode(private_root)
        private_home = private_root / "home"
        private_tmp = private_root / "tmp"
        private_home.mkdir(mode=0o700)
        private_tmp.mkdir(mode=0o700)
        enforce_private_directory_mode(private_home)
        enforce_private_directory_mode(private_tmp)
        child_environment = dict(base_environment)
        child_environment["HOME"] = os.fspath(private_home)
        child_environment["TMPDIR"] = os.fspath(private_tmp)
        require_environment_scrubbed(
            child_environment,
            allowed_lean_path=allowed_lean_path,
            allowed_tool_bin=tool_bin,
            allowed_private_home=private_home,
            allowed_private_tmp=private_tmp,
        )
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=child_environment,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                close_fds=True,
                start_new_session=(
                    os.name == "posix" and not shared_outer_process_group
                ),
            )
        except OSError as error:
            raise LeanKernel14576Error(
                f"Lean process could not start: {error}"
            ) from error
        timed_out: subprocess.TimeoutExpired | None = None
        try:
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired as error:
                timed_out = error
                returncode = (
                    process.returncode if process.returncode is not None else -1
                )
        except BaseException as operation_error:
            try:
                if os.name == "posix" and not shared_outer_process_group:
                    cleanup_isolated_process_group(process)
                elif shared_outer_process_group and os.name == "posix":
                    terminate_direct_child_without_group_signal(process)
                else:
                    terminate_nonposix_process_tree(process)
            except BaseException as cleanup_error:
                raise cleanup_error from operation_error
            raise
        if os.name == "posix" and not shared_outer_process_group:
            cleanup_isolated_process_group(process)
        elif timed_out is not None:
            if shared_outer_process_group and os.name == "posix":
                terminate_direct_child_without_group_signal(process)
            else:
                terminate_nonposix_process_tree(process)
        if timed_out is not None:
            raise LeanKernel14576Error(
                f"Lean process timed out after {timeout} seconds"
            ) from timed_out
        stdout_file.flush()
        stderr_file.flush()
        stdout_size = stdout_file.tell()
        stderr_size = stderr_file.tell()
        require(
            stdout_size <= MAX_PROCESS_OUTPUT_BYTES,
            "Lean stdout exceeds the post-capture rejection ceiling (not a peak-memory cap)",
        )
        require(
            stderr_size <= MAX_PROCESS_OUTPUT_BYTES,
            "Lean stderr exceeds the post-capture rejection ceiling (not a peak-memory cap)",
        )
        stdout_file.seek(0)
        stderr_file.seek(0)
        return ProcessResult(returncode, stdout_file.read(), stderr_file.read())


def run_bound_process(
    command: tuple[str, ...],
    *,
    cwd: Path,
    executable: ExecutableSnapshot,
    sources: tuple[StableSnapshot, ...] = (),
    timeout: int | float = TIMEOUT_SECONDS,
    environment: dict[str, str] | None = None,
    tool_bin: Path | None = None,
    shared_outer_process_group: bool = False,
) -> ProcessResult:
    """Run between immediate endpoint replays of the consumed source/tool leaves."""

    require(command, "bounded process command is empty")
    require(
        command[0] == os.fspath(executable.launch_path),
        "bounded process command does not launch the snapshotted executable",
    )
    require(cwd.is_absolute(), "bounded process working directory is not absolute")

    def replay_endpoints() -> None:
        for source in sources:
            require_unchanged(source)
        require_executable_unchanged(executable)

    replay_endpoints()
    try:
        result = run_process(
            list(command),
            cwd=cwd,
            timeout=timeout,
            environment=environment,
            tool_bin=tool_bin,
            shared_outer_process_group=shared_outer_process_group,
        )
    except BaseException as process_error:
        try:
            replay_endpoints()
        except BaseException as endpoint_error:
            raise endpoint_error from process_error
        raise
    replay_endpoints()
    return result


def parse_version_result(result: ProcessResult) -> LeanIdentity:
    require(result.returncode == 0, f"Lean version probe exited {result.returncode}")
    require(result.stderr == b"", "Lean version probe emitted stderr")
    require(b"\r" not in result.stdout, "Lean version probe emitted a carriage return")
    matched = LEAN_VERSION_LINE.fullmatch(result.stdout)
    require(matched is not None, f"unexpected Lean version output: {result.stdout!r}")
    identity = LeanIdentity(
        version=matched.group("version").decode("ascii"),
        platform=matched.group("platform").decode("ascii"),
        commit=matched.group("commit").decode("ascii"),
        build=matched.group("build").decode("ascii"),
    )
    require(identity.version == EXPECTED_LEAN_VERSION, "unexpected Lean version")
    require(identity.commit == EXPECTED_LEAN_COMMIT, "unexpected Lean source commit")
    require(identity.build == EXPECTED_LEAN_BUILD, "unexpected Lean build kind")
    return identity


def parse_lake_version_result(result: ProcessResult) -> LakeIdentity:
    require(result.returncode == 0, f"Lake version probe exited {result.returncode}")
    require(result.stderr == b"", "Lake version probe emitted stderr")
    require(b"\r" not in result.stdout, "Lake version probe emitted a carriage return")
    matched = LAKE_VERSION_LINE.fullmatch(result.stdout)
    require(matched is not None, f"unexpected Lake version output: {result.stdout!r}")
    identity = LakeIdentity(
        version=matched.group("version").decode("ascii"),
        lean_version=matched.group("lean_version").decode("ascii"),
    )
    require(identity.version == EXPECTED_LAKE_VERSION, "unexpected Lake version")
    require(
        identity.lean_version == EXPECTED_LEAN_VERSION, "unexpected Lake Lean version"
    )
    require(
        identity.version.endswith(f"+{EXPECTED_LEAN_COMMIT[:7]}"),
        "Lake version does not bind the expected Lean commit prefix",
    )
    return identity


def require_same_lean_identity(before: LeanIdentity, after: LeanIdentity) -> None:
    require(after == before, "Lean identity changed across regression execution")


def require_same_lake_identity(before: LakeIdentity, after: LakeIdentity) -> None:
    require(after == before, "Lake identity changed across regression execution")


def derived_query(spec: FixtureSpec, data: bytes) -> bytes:
    validate_fixture_payload(spec, data)
    return data + b'\n#eval IO.println "' + spec.canary + b'"\n'


def validate_fixture_result(spec: FixtureSpec, result: ProcessResult) -> None:
    require(
        result.returncode == 0,
        f"{spec.name} did not complete its guarded fixed-kernel route: exit {result.returncode}",
    )
    require(result.stderr == b"", f"{spec.name} emitted unexpected stderr")
    require(b"\r" not in result.stdout, f"{spec.name} emitted a carriage return")
    require(
        result.stdout == spec.canary + b"\n",
        f"{spec.name} did not emit exactly its EOF canary",
    )


def target_olean_inventory_probe(spec: FixtureSpec, module: str) -> bytes:
    expected_module = {
        "issue_14576.lean": "Issue14576Full",
        "issue_14576_min.lean": "Issue14576Min",
    }.get(spec.name)
    require(module == expected_module, "target-olean inventory-probe module drifted")
    post_abort_bad_absence_clause = ""
    if spec.name == "issue_14576.lean":
        post_abort_bad_absence_clause = (
            "/-- error: Unknown constant `bad` -/\n#guard_msgs in\n#print bad\n\n"
        )
    return (
        f"import {module}\n\n"
        f"axiom {TARGET_OLEAN_LOOKUP_POSITIVE} : Nat\n\n"
        f"/-- info: axiom {TARGET_OLEAN_LOOKUP_POSITIVE} : Nat -/\n"
        "#guard_msgs in\n"
        f"#print {TARGET_OLEAN_LOOKUP_POSITIVE}\n\n"
        f"/-- error: Unknown constant `{TARGET_OLEAN_LOOKUP_NEGATIVE}` -/\n"
        "#guard_msgs in\n"
        f"#print {TARGET_OLEAN_LOOKUP_NEGATIVE}\n\n"
        "/-- info: axiom E : sorry -/\n"
        "#guard_msgs in\n"
        "#print E\n\n"
        "/-- error: Unknown constant `E.mk` -/\n"
        "#guard_msgs in\n"
        "#print E.mk\n\n"
        f"{post_abort_bad_absence_clause}"
        f'#eval IO.println "{spec.target_olean_inventory_canary.decode("ascii")}"\n'
    ).encode("ascii")


def validate_target_olean_inventory_probe_source(
    spec: FixtureSpec, module: str, source: bytes
) -> None:
    expected = target_olean_inventory_probe(spec, module)
    require(b"\r" not in source, "target-olean inventory probe contains CR")
    require(source.endswith(b"\n"), "target-olean inventory probe lacks final newline")
    require(
        source.count(f"import {module}\n".encode("ascii")) == 1,
        "target-olean inventory probe import clause is absent or ambiguous",
    )
    require(
        source.count(f"axiom {TARGET_OLEAN_LOOKUP_POSITIVE} : Nat\n".encode("ascii"))
        == 1
        and source.count(
            (
                f"/-- info: axiom {TARGET_OLEAN_LOOKUP_POSITIVE} : Nat -/\n"
                "#guard_msgs in\n"
                f"#print {TARGET_OLEAN_LOOKUP_POSITIVE}\n"
            ).encode("ascii")
        )
        == 1,
        "target-olean inventory probe separate-positive clause is absent or ambiguous",
    )
    require(
        source.count(
            (
                f"/-- error: Unknown constant `{TARGET_OLEAN_LOOKUP_NEGATIVE}` -/\n"
                "#guard_msgs in\n"
                f"#print {TARGET_OLEAN_LOOKUP_NEGATIVE}\n"
            ).encode("ascii")
        )
        == 1,
        "target-olean inventory probe separate-negative clause is absent or ambiguous",
    )
    require(
        source.count(b"/-- info: axiom E : sorry -/\n#guard_msgs in\n#print E\n") == 1,
        "target-olean inventory probe residual-E clause is absent or ambiguous",
    )
    require(
        source.count(
            b"/-- error: Unknown constant `E.mk` -/\n#guard_msgs in\n#print E.mk\n"
        )
        == 1,
        "target-olean inventory probe absent-E.mk clause is absent or ambiguous",
    )
    bad_clause_count = source.count(
        b"/-- error: Unknown constant `bad` -/\n#guard_msgs in\n#print bad\n"
    )
    require(
        bad_clause_count == (1 if spec.name == "issue_14576.lean" else 0),
        "target-olean inventory probe full-only post-abort absent-bad clause drifted",
    )
    require(
        source.count(
            b'#eval IO.println "' + spec.target_olean_inventory_canary + b'"\n'
        )
        == 1,
        "target-olean inventory probe EOF clause is absent or ambiguous",
    )
    require(source == expected, "target-olean inventory probe exact bytes drifted")


def validate_target_olean_inventory_probe_result(
    spec: FixtureSpec, result: ProcessResult
) -> None:
    require(
        result.returncode == 0,
        f"{spec.name} target-olean inventory probe exited {result.returncode}",
    )
    require(
        result.stderr == b"",
        f"{spec.name} target-olean inventory probe emitted stderr",
    )
    require(
        b"\r" not in result.stdout,
        f"{spec.name} target-olean inventory probe stdout contains CR",
    )
    require(
        result.stdout == spec.target_olean_inventory_canary + b"\n",
        f"{spec.name} target-olean inventory probe EOF canary drifted",
    )


def validate_leanchecker_fresh_environment_replay_result(
    module: str, result: ProcessResult
) -> None:
    require(
        result.returncode == 0,
        f"LeanChecker fresh-environment leanchecker replay for {module} "
        f"exited {result.returncode}: "
        f"stdout={result.stdout!r}, stderr={result.stderr!r}",
    )
    require(
        b"\r" not in result.stdout,
        f"LeanChecker fresh-environment replay for {module} stdout contains CR",
    )
    require(
        b"\r" not in result.stderr,
        f"LeanChecker fresh-environment replay for {module} stderr contains CR",
    )
    require(
        result.stdout == b"",
        f"LeanChecker fresh-environment replay for {module} emitted stdout",
    )
    require(
        result.stderr == b"",
        f"LeanChecker fresh-environment replay for {module} emitted stderr",
    )


def nested_timing_contract() -> dict[str, object]:
    """Return the finite nested-process timing contract."""

    contract: dict[str, object] = {
        "inner_per_replay_timeout_seconds": (
            LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS
        ),
        "replay_count": LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_COUNT,
        "non_replay_lean_child_timeout_seconds": (
            NESTED_NON_REPLAY_LEAN_CHILD_TIMEOUT_SECONDS
        ),
        "non_replay_lean_child_count": NESTED_NON_REPLAY_LEAN_CHILD_COUNT,
        "identity_child_timeout_seconds": NESTED_IDENTITY_CHILD_TIMEOUT_SECONDS,
        "identity_child_count": NESTED_IDENTITY_CHILD_COUNT,
        "orchestration_headroom_seconds": NESTED_ORCHESTRATION_HEADROOM_SECONDS,
        "declared_non_replay_margin_seconds": NESTED_NON_REPLAY_MARGIN_SECONDS,
        "required_outer_timeout_seconds": NESTED_REQUIRED_OUTER_TIMEOUT_SECONDS,
        "derivation": (
            "inner_per_replay_timeout_seconds*replay_count+"
            "non_replay_lean_child_timeout_seconds*non_replay_lean_child_count+"
            "identity_child_timeout_seconds*identity_child_count+"
            "orchestration_headroom_seconds"
        ),
        "environmental_premise": (
            "Wall duration depends on host load, scheduler behavior, dynamic loading, "
            "filesystem state, and hardware; the finite limits fail closed and are not "
            "performance guarantees."
        ),
    }
    validate_nested_timing_contract(contract)
    return contract


def validate_nested_timing_contract(contract: dict[str, object]) -> None:
    """Reject drift or arithmetic contradictions in the nested timing tuple."""

    expected_keys = {
        "inner_per_replay_timeout_seconds",
        "replay_count",
        "non_replay_lean_child_timeout_seconds",
        "non_replay_lean_child_count",
        "identity_child_timeout_seconds",
        "identity_child_count",
        "orchestration_headroom_seconds",
        "declared_non_replay_margin_seconds",
        "required_outer_timeout_seconds",
        "derivation",
        "environmental_premise",
    }
    require(set(contract) == expected_keys, "nested timing contract keys drifted")
    inner = contract["inner_per_replay_timeout_seconds"]
    count = contract["replay_count"]
    lean_timeout = contract["non_replay_lean_child_timeout_seconds"]
    lean_count = contract["non_replay_lean_child_count"]
    identity_timeout = contract["identity_child_timeout_seconds"]
    identity_count = contract["identity_child_count"]
    headroom = contract["orchestration_headroom_seconds"]
    margin = contract["declared_non_replay_margin_seconds"]
    required_outer = contract["required_outer_timeout_seconds"]
    require(type(inner) is int and inner == 900, "nested timing inner bound drifted")
    require(type(count) is int and count == 3, "nested timing replay count drifted")
    require(
        type(lean_timeout) is int and lean_timeout == 120,
        "nested timing non-replay Lean-child bound drifted",
    )
    require(
        type(lean_count) is int and lean_count == 6,
        "nested timing non-replay Lean-child count drifted",
    )
    require(
        type(identity_timeout) is int and identity_timeout == 60,
        "nested timing identity-child bound drifted",
    )
    require(
        type(identity_count) is int and identity_count == 4,
        "nested timing identity-child count drifted",
    )
    require(
        type(headroom) is int and headroom == 240,
        "nested timing orchestration headroom drifted",
    )
    require(
        type(margin) is int
        and margin
        == lean_timeout * lean_count + identity_timeout * identity_count + headroom
        and margin == 1_200,
        "nested timing non-replay allocation drifted or is contradictory",
    )
    require(
        type(required_outer) is int
        and required_outer == inner * count + margin
        and required_outer == 3_900,
        "nested timing required outer bound drifted or is contradictory",
    )
    require(
        contract["derivation"] == "inner_per_replay_timeout_seconds*replay_count+"
        "non_replay_lean_child_timeout_seconds*non_replay_lean_child_count+"
        "identity_child_timeout_seconds*identity_child_count+"
        "orchestration_headroom_seconds",
        "nested timing derivation drifted",
    )
    premise = contract["environmental_premise"]
    require(
        isinstance(premise, str)
        and "host load" in premise
        and "not performance guarantees" in premise,
        "nested timing environmental premise drifted",
    )


def transformed_unguarded_source(spec: FixtureSpec, data: bytes) -> bytes:
    """Remove only the full fixture's reviewed diagnostic guard."""

    validate_fixture_payload(spec, data)
    require(spec.name == "issue_14576.lean", "unguarded control selected wrong fixture")
    require(
        data.count(UNGUARDED_GUARD) == 1,
        "unguarded control guard is absent or ambiguous",
    )
    transformed = data.replace(UNGUARDED_GUARD, UNGUARDED_COMMAND, 1)
    require(len(transformed) == 2397, "unguarded control byte length drifted")
    require(
        digest(transformed) == UNGUARDED_SOURCE_SHA256,
        "unguarded control SHA-256 drifted",
    )
    return transformed


def derived_unguarded_query(spec: FixtureSpec, data: bytes) -> bytes:
    transformed = transformed_unguarded_source(spec, data)
    return transformed + b'\n#eval IO.println "' + UNGUARDED_CANARY + b'"\n'


def transformed_benign_source(spec: FixtureSpec, data: bytes) -> bytes:
    """Change only the malformed projection and diagnostic scaffolding in the min fixture."""

    validate_fixture_payload(spec, data)
    require(
        spec.name == "issue_14576_min.lean", "benign control selected wrong fixture"
    )
    replacements = (
        (BENIGN_INVALID_PROJECTION, BENIGN_VALID_PROJECTION),
        (BENIGN_LOG_TYPE, b""),
        (BENIGN_LOG_ACCEPTED, b""),
        (spec.guarded_diagnostic, b"mkbug\n"),
    )
    transformed = data
    for before, after in replacements:
        require(
            transformed.count(before) == 1,
            "benign control transformation anchor is absent or ambiguous",
        )
        transformed = transformed.replace(before, after, 1)
    require(len(transformed) == 646, "benign control byte length drifted")
    require(
        digest(transformed) == BENIGN_SOURCE_SHA256, "benign control SHA-256 drifted"
    )
    return transformed


def derived_benign_query(spec: FixtureSpec, data: bytes) -> bytes:
    transformed = transformed_benign_source(spec, data)
    return transformed + b'\n#eval IO.println "' + BENIGN_CANARY + b'"\n'


def validate_benign_result(result: ProcessResult) -> None:
    require(result.returncode == 0, f"benign near-neighbor exited {result.returncode}")
    require(
        b"\r" not in result.stdout,
        "benign near-neighbor stdout contains a carriage return",
    )
    require(
        b"\r" not in result.stderr,
        "benign near-neighbor stderr contains a carriage return",
    )
    require(result.stderr == b"", "benign near-neighbor emitted unexpected stderr")
    require(
        result.stdout == BENIGN_CANARY + b"\n",
        "benign near-neighbor did not emit exactly its EOF canary",
    )


def validate_unguarded_result(query: Path, result: ProcessResult) -> None:
    """Require the one exact live compiler rejection, not arbitrary failure."""

    require(
        result.returncode == 1,
        f"unguarded issue_14576.lean exited {result.returncode}, expected 1",
    )
    require(
        b"\r" not in result.stdout,
        "unguarded control stdout contains a carriage return",
    )
    require(
        b"\r" not in result.stderr,
        "unguarded control stderr contains a carriage return",
    )
    require(
        result.stderr == b"",
        "unguarded control emitted unexpected stderr",
    )
    expected_stdout = expected_unguarded_diagnostic(query) + UNGUARDED_CANARY + b"\n"
    require(
        result.stdout == expected_stdout,
        f"unguarded control diagnostic/EOF output drifted: {result.stdout!r}",
    )


def expected_unguarded_diagnostic(query: Path) -> bytes:
    require(query.is_absolute(), "unguarded diagnostic source route is not absolute")
    rendered = os.fspath(query)
    require(
        "\r" not in rendered and "\n" not in rendered,
        "unguarded diagnostic path contains a line break",
    )
    return f"{rendered}:58:0: error: (kernel) invalid projection\n  w.1\n".encode(
        "utf-8", errors="strict"
    )


def write_exclusive(path: Path, payload: bytes, role: str) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise LeanKernel14576Error(f"cannot materialize {role}: {error}") from error
    try:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            require(written > 0, f"short write while materializing {role}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def materialize_payload(
    directory: Path,
    filename: str,
    payload: bytes,
    *,
    lexical_root: Path,
    role: str,
) -> StableSnapshot:
    require(
        re.fullmatch(r"[A-Z][A-Za-z0-9_]*\.lean", filename) is not None,
        f"{role} filename is outside the finite safe grammar",
    )
    path = directory / filename
    write_exclusive(path, payload, role)
    observed = snapshot(path, expected_permissions=0o600, lexical_root=lexical_root)
    require(observed.data == payload, f"private {role} replay drifted")
    return observed


def require_absent_output(path: Path) -> None:
    require(path.is_absolute(), "Lean output route is not absolute")
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot inspect Lean output route {path}: {error}"
        ) from error
    raise LeanKernel14576Error(f"Lean output route already exists: {path}")


def snapshot_olean(path: Path, *, lexical_root: Path) -> StableSnapshot:
    try:
        path.chmod(0o600)
    except OSError as error:
        raise LeanKernel14576Error(
            f"cannot make ordinary olean in private tree read-only to peers: {error}"
        ) from error
    observed = snapshot(path, expected_permissions=0o600, lexical_root=lexical_root)
    require(
        observed.data.startswith(b"olean"), f"compiled olean magic drifted: {path.name}"
    )
    return observed


def run_gate(
    toolchain_root: Path, *, shared_outer_process_group: bool = False
) -> dict[str, object]:
    require(
        type(shared_outer_process_group) is bool,
        "shared outer process-group selection must be Boolean",
    )
    if shared_outer_process_group and os.name == "posix":
        require(
            os.getpgrp() == os.getpid(),
            "shared outer process-group mode requires this checker to be its group leader",
        )
    validate_fixture_inventory(FIXTURES)
    checker_source = snapshot(SCRIPT_PATH)
    validate_neutral_fresh_environment_namespace(checker_source.data)
    origin = snapshot(FIXTURE_ROOT / "origin.json")
    validate_origin_payload(origin.data)
    fixture_snapshots: list[StableSnapshot] = []
    for spec in FIXTURES:
        observed = snapshot(spec.path)
        validate_fixture_payload(spec, observed.data)
        fixture_snapshots.append(observed)

    toolchain_metadata = snapshot(TOOLCHAIN_METADATA_PATH)
    metadata = load_toolchain_metadata_policy(toolchain_metadata, checker_source)
    asset = reviewed_strict_replay_host_asset(metadata)
    tool_snapshots = snapshot_direct_toolchain(toolchain_root, asset)
    lean_snapshot = tool_snapshots["lean"]
    lake_snapshot = tool_snapshots["lake"]
    leanchecker_snapshot = tool_snapshots["leanchecker"]
    lean_path = lean_snapshot.launch_path
    lake_path = lake_snapshot.launch_path
    leanchecker_path = leanchecker_snapshot.launch_path

    version_command = lean_version_command(lean_path)
    validate_lean_version_command(version_command, lean_path)
    version_result = run_bound_process(
        version_command,
        cwd=ROOT,
        executable=lean_snapshot,
        sources=(checker_source, toolchain_metadata),
        timeout=60,
        shared_outer_process_group=shared_outer_process_group,
    )
    identity = parse_version_result(version_result)
    lake_version = lake_version_command(lake_path)
    validate_lake_version_command(lake_version, lake_path)
    lake_identity = parse_lake_version_result(
        run_bound_process(
            lake_version,
            cwd=ROOT,
            executable=lake_snapshot,
            sources=(checker_source, toolchain_metadata),
            timeout=60,
            shared_outer_process_group=shared_outer_process_group,
        )
    )

    results: list[dict[str, object]] = []
    successful_oleans: list[StableSnapshot] = []
    leanchecker_fresh_environment_replayed_modules: list[str] = []
    leanchecker_fresh_environment_replay_measurements: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="pid-rs-lean-14576-") as temporary:
        directory = Path(os.path.abspath(temporary))
        queries = directory / "queries"
        oleans = directory / "oleans"
        directory_identity = enforce_private_directory_mode(directory)
        queries.mkdir(mode=0o700)
        oleans.mkdir(mode=0o700)
        private_directory_baselines = {
            "temporary_root": (directory, directory_identity),
            "query_root": (queries, enforce_private_directory_mode(queries)),
            "olean_root": (oleans, enforce_private_directory_mode(oleans)),
        }
        modules = ("Issue14576Full", "Issue14576Min")
        for module, spec, observed in zip(
            modules, FIXTURES, fixture_snapshots, strict=True
        ):
            query_snapshot = materialize_payload(
                queries,
                f"{module}.lean",
                derived_query(spec, observed.data),
                lexical_root=directory,
                role=f"{spec.name} guarded query",
            )
            olean_path = oleans / f"{module}.olean"
            require_absent_output(olean_path)
            compile_command = lean_compile_command(
                lean_path, query_snapshot.path, olean_path
            )
            validate_lean_compile_command(
                compile_command, lean_path, query_snapshot.path, olean_path
            )
            result = run_bound_process(
                compile_command,
                cwd=directory,
                executable=lean_snapshot,
                sources=(checker_source, observed, query_snapshot),
                shared_outer_process_group=shared_outer_process_group,
            )
            validate_fixture_result(spec, result)
            olean_snapshot = snapshot_olean(olean_path, lexical_root=directory)
            inventory_probe_payload = target_olean_inventory_probe(spec, module)
            validate_target_olean_inventory_probe_source(
                spec,
                module,
                inventory_probe_payload,
            )
            inventory_probe = materialize_payload(
                queries,
                f"{module}TargetOleanInventory.lean",
                inventory_probe_payload,
                lexical_root=directory,
                role=f"{spec.name} target-olean declaration inventory probe",
            )
            inventory_probe_command = lean_source_command(
                lean_path, inventory_probe.path
            )
            validate_lean_source_command(
                inventory_probe_command, lean_path, inventory_probe.path
            )
            inventory_probe_result = run_bound_process(
                inventory_probe_command,
                cwd=directory,
                executable=lean_snapshot,
                sources=(
                    checker_source,
                    observed,
                    query_snapshot,
                    olean_snapshot,
                    inventory_probe,
                ),
                environment=scrubbed_environment(
                    lean_path=oleans,
                    tool_bin=lean_path.parent,
                ),
                tool_bin=lean_path.parent,
                shared_outer_process_group=shared_outer_process_group,
            )
            validate_target_olean_inventory_probe_result(spec, inventory_probe_result)
            replay_command = leanchecker_command(leanchecker_path, module)
            validate_leanchecker_command(replay_command, leanchecker_path, module)
            replay_started_monotonic_ns = time.monotonic_ns()
            replay_result = run_bound_process(
                replay_command,
                cwd=directory,
                executable=leanchecker_snapshot,
                sources=(
                    checker_source,
                    toolchain_metadata,
                    query_snapshot,
                    olean_snapshot,
                ),
                timeout=LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS,
                environment=scrubbed_environment(
                    lean_path=oleans,
                    tool_bin=lean_path.parent,
                ),
                tool_bin=lean_path.parent,
                shared_outer_process_group=shared_outer_process_group,
            )
            replay_finished_monotonic_ns = time.monotonic_ns()
            replay_duration_monotonic_ns = (
                replay_finished_monotonic_ns - replay_started_monotonic_ns
            )
            require(
                replay_duration_monotonic_ns >= 0,
                f"monotonic clock moved backwards during replay for {module}",
            )
            validate_leanchecker_fresh_environment_replay_result(module, replay_result)
            leanchecker_fresh_environment_replayed_modules.append(module)
            leanchecker_fresh_environment_replay_measurements.append(
                {
                    "module": module,
                    "duration_monotonic_ns": replay_duration_monotonic_ns,
                    "timeout_seconds": (
                        LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS
                    ),
                }
            )
            successful_oleans.append(olean_snapshot)
            results.append(
                {
                    "name": spec.name,
                    "sha256": spec.sha256,
                    "bytes": spec.size,
                    "trust": 0,
                    "guarded_invalid_projection": True,
                    "eof_canary_observed": True,
                    "module": module,
                    "derived_query_bytes": len(query_snapshot.data),
                    "derived_query_sha256": query_snapshot.sha256,
                    "olean_bytes": len(olean_snapshot.data),
                    "olean_sha256": olean_snapshot.sha256,
                    "target_olean_inventory_probe": {
                        "claim_scope": "selected_names_in_this_emitted_olean_only",
                        "complete_declaration_inventory_claimed": False,
                        "bracketing_lookup_controls": {
                            "present": TARGET_OLEAN_LOOKUP_POSITIVE,
                            "absent": TARGET_OLEAN_LOOKUP_NEGATIVE,
                        },
                        "selected_declarations": [
                            {
                                "symbol": "E",
                                "status": "present",
                                "rendering": "axiom E : sorry",
                                "source_role": (
                                    "residual_axiom_shaped_declaration_from_failed_"
                                    "inductive_route"
                                ),
                            },
                            {
                                "symbol": "E.mk",
                                "status": "absent",
                                "rendering": "Unknown constant `E.mk`",
                                "source_role": "rejected_constructor_attempt",
                            },
                            *(
                                [
                                    {
                                        "symbol": "bad",
                                        "status": "absent",
                                        "rendering": "Unknown constant `bad`",
                                        "source_role": "unreached_downstream_declaration",
                                        "declaration_source_present": True,
                                        "thmdecl_reached_or_attempted": False,
                                        "post_failure_unknown_identifier_reference_guard": True,
                                    }
                                ]
                                if spec.name == "issue_14576.lean"
                                else []
                            ),
                        ],
                        "source_bytes": len(inventory_probe.data),
                        "source_sha256": inventory_probe.sha256,
                        "exit_code": inventory_probe_result.returncode,
                        "eof_canary_observed": True,
                        "target_olean_imported": True,
                    },
                    "leanchecker_fresh_environment_replayed": (
                        module in leanchecker_fresh_environment_replayed_modules
                    ),
                }
            )

        benign_spec = FIXTURES[1]
        benign_payload = derived_benign_query(
            benign_spec,
            fixture_snapshots[1].data,
        )
        benign_module = "Issue14576MinBenign"
        benign_query = materialize_payload(
            queries,
            f"{benign_module}.lean",
            benign_payload,
            lexical_root=directory,
            role="benign near-neighbor query",
        )
        benign_olean_path = oleans / f"{benign_module}.olean"
        require_absent_output(benign_olean_path)
        benign_command = lean_compile_command(
            lean_path, benign_query.path, benign_olean_path
        )
        validate_lean_compile_command(
            benign_command,
            lean_path,
            benign_query.path,
            benign_olean_path,
        )
        benign_result = run_bound_process(
            benign_command,
            cwd=directory,
            executable=lean_snapshot,
            sources=(checker_source, fixture_snapshots[1], benign_query),
            shared_outer_process_group=shared_outer_process_group,
        )
        validate_benign_result(benign_result)
        benign_olean = snapshot_olean(benign_olean_path, lexical_root=directory)
        benign_replay_command = leanchecker_command(leanchecker_path, benign_module)
        validate_leanchecker_command(
            benign_replay_command, leanchecker_path, benign_module
        )
        benign_replay_started_monotonic_ns = time.monotonic_ns()
        benign_replay_result = run_bound_process(
            benign_replay_command,
            cwd=directory,
            executable=leanchecker_snapshot,
            sources=(
                checker_source,
                toolchain_metadata,
                benign_query,
                benign_olean,
            ),
            timeout=LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS,
            environment=scrubbed_environment(
                lean_path=oleans,
                tool_bin=lean_path.parent,
            ),
            tool_bin=lean_path.parent,
            shared_outer_process_group=shared_outer_process_group,
        )
        benign_replay_finished_monotonic_ns = time.monotonic_ns()
        benign_replay_duration_monotonic_ns = (
            benign_replay_finished_monotonic_ns - benign_replay_started_monotonic_ns
        )
        require(
            benign_replay_duration_monotonic_ns >= 0,
            f"monotonic clock moved backwards during replay for {benign_module}",
        )
        validate_leanchecker_fresh_environment_replay_result(
            benign_module, benign_replay_result
        )
        leanchecker_fresh_environment_replayed_modules.append(benign_module)
        leanchecker_fresh_environment_replay_measurements.append(
            {
                "module": benign_module,
                "duration_monotonic_ns": benign_replay_duration_monotonic_ns,
                "timeout_seconds": LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS,
            }
        )
        successful_oleans.append(benign_olean)

        unguarded_spec = FIXTURES[0]
        unguarded_payload = derived_unguarded_query(
            unguarded_spec,
            fixture_snapshots[0].data,
        )
        unguarded_query = materialize_payload(
            queries,
            "Issue14576Unguarded.lean",
            unguarded_payload,
            lexical_root=directory,
            role="unguarded negative-control query",
        )
        unguarded_command = lean_source_command(lean_path, unguarded_query.path)
        validate_lean_source_command(unguarded_command, lean_path, unguarded_query.path)
        unguarded_result = run_bound_process(
            unguarded_command,
            cwd=directory,
            executable=lean_snapshot,
            sources=(checker_source, fixture_snapshots[0], unguarded_query),
            shared_outer_process_group=shared_outer_process_group,
        )
        validate_unguarded_result(unguarded_query.path, unguarded_result)

        for _private_role, (
            private_path,
            private_identity,
        ) in private_directory_baselines.items():
            require_private_directory_unchanged(private_path, private_identity)

    require(
        len(leanchecker_fresh_environment_replayed_modules)
        == LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_COUNT,
        "LeanChecker fresh-environment replay count drifted",
    )
    require(
        len(leanchecker_fresh_environment_replay_measurements)
        == LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_COUNT,
        "LeanChecker fresh-environment replay measurement count drifted",
    )

    post_version_command = lean_version_command(lean_path)
    validate_lean_version_command(post_version_command, lean_path)
    post_identity = parse_version_result(
        run_bound_process(
            post_version_command,
            cwd=ROOT,
            executable=lean_snapshot,
            sources=(checker_source, toolchain_metadata),
            timeout=60,
            shared_outer_process_group=shared_outer_process_group,
        )
    )
    require_same_lean_identity(identity, post_identity)
    post_lake_version_command = lake_version_command(lake_path)
    validate_lake_version_command(post_lake_version_command, lake_path)
    post_lake_identity = parse_lake_version_result(
        run_bound_process(
            post_lake_version_command,
            cwd=ROOT,
            executable=lake_snapshot,
            sources=(checker_source, toolchain_metadata),
            timeout=60,
            shared_outer_process_group=shared_outer_process_group,
        )
    )
    require_same_lake_identity(lake_identity, post_lake_identity)
    post_tool_snapshots = {
        role: require_executable_unchanged(observed)
        for role, observed in tool_snapshots.items()
    }
    for observed in (
        checker_source,
        toolchain_metadata,
        origin,
        *fixture_snapshots,
    ):
        require_unchanged(observed)
    post_lean_snapshot = post_tool_snapshots["lean"]
    post_lake_snapshot = post_tool_snapshots["lake"]
    post_leanchecker_snapshot = post_tool_snapshots["leanchecker"]

    return {
        "schema": RESULT_SCHEMA,
        "status": "regression_checks_passed",
        "checker_source_sha256": checker_source.sha256,
        "lean": {
            "version": identity.version,
            "platform": identity.platform,
            "commit": identity.commit,
            "build": identity.build,
            "toolchain": EXPECTED_TOOLCHAIN,
            "post_execution_identity_equal": True,
        },
        "lake": {
            "version": lake_identity.version,
            "lean_version": lake_identity.lean_version,
            "post_execution_identity_equal": True,
        },
        "execution_route": {
            "direct_toolchain_root": os.fspath(toolchain_root),
            "reviewed_pin_platform_key": asset["key"],
            "metadata_lifecycle_state": "reviewed_pins_strict_replay_required",
            "toolchain_metadata_sha256": toolchain_metadata.sha256,
            "toolchain_metadata_policy_projection_sha256": (
                EXPECTED_TOOLCHAIN_METADATA_POLICY_SHA256
            ),
            "nested_checker_self_binding_equal": True,
            "archive_derivation_claimed_by_this_checker": False,
            "required_archive_derivation_route": (
                "nested_same-transaction_execution_by_"
                "lean-toolchain-release-custody-check/v5"
            ),
            "elan_invoked": False,
            "direct_lean_pre_execution": executable_leaf_evidence(lean_snapshot),
            "direct_lean_post_execution": executable_leaf_evidence(post_lean_snapshot),
            "direct_lake_pre_execution": executable_leaf_evidence(lake_snapshot),
            "direct_lake_post_execution": executable_leaf_evidence(post_lake_snapshot),
            "direct_leanchecker_pre_execution": executable_leaf_evidence(
                leanchecker_snapshot
            ),
            "direct_leanchecker_post_execution": executable_leaf_evidence(
                post_leanchecker_snapshot
            ),
            "absolute_launch_and_source_paths": True,
            "source_compile_arguments": [
                TRUST_ZERO_ARGUMENT,
                "-o",
                "<absolute-private-olean>",
                "<absolute-private-query>",
            ],
            "unguarded_source_arguments": [TRUST_ZERO_ARGUMENT, "<absolute-query>"],
            "leanchecker_fresh_environment_replay_arguments": [
                LEANCHECKER_FRESH_ENVIRONMENT_ARGUMENT,
                "<private-module>",
            ],
            "leanchecker_fresh_environment_replay_timeout_seconds": (
                LEANCHECKER_FRESH_ENVIRONMENT_REPLAY_TIMEOUT_SECONDS
            ),
            "direct_tool_leaves_bound": ["lean", "lake", "leanchecker"],
            "direct_tool_leaf_bytes_equal_before_and_after": True,
            "version_commit_build_platform_equal_before_and_after": True,
            "immediate_pre_post_source_and_tool_endpoint_checks": True,
            "shared_outer_process_group": shared_outer_process_group,
            "inner_children_start_new_sessions": (
                os.name == "posix" and not shared_outer_process_group
            ),
            "isolated_child_group_cleanup_after_every_outcome": (
                os.name == "posix" and not shared_outer_process_group
            ),
            "isolated_child_group_cleanup_signal_policy": ["TERM", "KILL"],
            "process_group_cleanup_signal_policy_is_escalation_not_delivery_log": True,
            "process_group_cleanup_bounds_milliseconds": {
                "term_grace": PROCESS_GROUP_TERM_GRACE_MILLISECONDS,
                "kill_grace": PROCESS_GROUP_KILL_GRACE_MILLISECONDS,
                "absence_poll_interval": PROCESS_GROUP_POLL_INTERVAL_MILLISECONDS,
                "direct_child_reap_timeout": DIRECT_CHILD_REAP_TIMEOUT_MILLISECONDS,
            },
            "isolated_child_group_absence_checked": (
                os.name == "posix" and not shared_outer_process_group
            ),
            "non_child_descendants_reaped_by_this_checker": False,
            "process_group_observation_atomic": False,
            "process_group_reuse_excluded": False,
            "descendant_group_or_session_changes_continuously_observed": False,
            "shared_group_signal_from_nested_checker": False,
            "shared_group_cleanup_owned_by_outer_supervisor": (
                os.name == "posix" and shared_outer_process_group
            ),
            "private_temporary_directory_pre_post_identity_equal": True,
            "private_temporary_directory_modes": {
                "temporary_root": "0700",
                "query_root": "0700",
                "olean_root": "0700",
            },
            "private_lean_path_only_for_leanchecker_fresh_environment_replay": True,
            "version_output_is_identity_evidence_not_authenticity": True,
            "fixed_child_path": SAFE_CHILD_PATH,
            "leanchecker_fresh_environment_child_path_prefix": os.fspath(
                lean_path.parent
            ),
            "ambient_home_logname_user_retained": False,
            "per_child_private_home_and_tmp": True,
            "per_child_private_environment_directory_modes": {
                "temporary_root": "0700",
                "home": "0700",
                "tmp": "0700",
            },
            "child_environment_removed_prefixes": list(ENVIRONMENT_PREFIXES_TO_REMOVE),
            "child_environment_removed_keys": sorted(ENVIRONMENT_KEYS_TO_REMOVE),
        },
        "active_scientific_project_inputs_consumed": [],
        "active_scientific_project_toolchain_migration_claimed": False,
        "scope_boundary": dict(EXPECTED_SCOPE_BOUNDARY),
        "trust_zero_semantics": dict(TRUST_ZERO_SEMANTICS),
        "leanchecker_fresh_semantics": dict(LEANCHECKER_FRESH_SEMANTICS),
        "origin_sha256": EXPECTED_ORIGIN_SHA256,
        "fixtures": results,
        "trust_zero_olean_compilations": len(successful_oleans),
        "leanchecker_fresh_environment_replays": len(
            leanchecker_fresh_environment_replayed_modules
        ),
        "leanchecker_fresh_environment_replayed_modules": (
            leanchecker_fresh_environment_replayed_modules
        ),
        "leanchecker_fresh_environment_replay_measurements": (
            leanchecker_fresh_environment_replay_measurements
        ),
        "leanchecker_fresh_environment_replay_total_monotonic_ns": sum(
            int(measurement["duration_monotonic_ns"])
            for measurement in leanchecker_fresh_environment_replay_measurements
        ),
        "leanchecker_fresh_environment_replay_max_monotonic_ns": max(
            int(measurement["duration_monotonic_ns"])
            for measurement in leanchecker_fresh_environment_replay_measurements
        ),
        "nested_timing_contract": nested_timing_contract(),
        "benign_near_neighbor": {
            "source_fixture": benign_spec.name,
            "source_fixture_sha256": benign_spec.sha256,
            "transformation": (
                "replace_malformed_nested_C_projection_with_valid_W_projection_and_remove_"
                "only_the_expected_message_scaffolding"
            ),
            "transformed_source_sha256": BENIGN_SOURCE_SHA256,
            "exit_code": 0,
            "trust": 0,
            "eof_canary_observed": True,
            "module": benign_module,
            "derived_query_bytes": len(benign_query.data),
            "derived_query_sha256": benign_query.sha256,
            "olean_bytes": len(benign_olean.data),
            "olean_sha256": benign_olean.sha256,
            "leanchecker_fresh_environment_replayed": True,
        },
        "unguarded_negative_control": {
            "source_fixture": unguarded_spec.name,
            "source_fixture_sha256": unguarded_spec.sha256,
            "transformation": (
                "replace_exactly_one_reviewed_invalid_projection_message_guard_scaffolding_"
                "with_unguarded_mkbug"
            ),
            "transformed_source_sha256": UNGUARDED_SOURCE_SHA256,
            "transformed_source_bytes": 2397,
            "exit_code": 1,
            "diagnostic": "(kernel) invalid projection\\n  w.1",
            "diagnostic_stream": "stdout",
            "diagnostic_source_line": 58,
            "diagnostic_source_column": 0,
            "diagnostic_path": "exact_absolute_private_query_path",
            "stdout_shape": (
                "<exact-absolute-private-query>:58:0: error: (kernel) invalid projection\\n"
                "  w.1\\n<exact-eof-canary>\\n"
            ),
            "stderr": "empty",
            "trust": 0,
            "eof_canary_observed": True,
            "derived_query_bytes": len(unguarded_query.data),
            "derived_query_sha256": unguarded_query.sha256,
        },
        "boundary": (
            "This is exact-source regression evidence that the selected exact Lean 4.32.2 "
            "release executable emits the kernel-tagged rejection for the two upstream #14576 "
            "declaration attempts through their guarded invalid-projection diagnostics at "
            "explicit trust level zero; it is not source-to-binary provenance. Separately pinned "
            "release/Git metadata records stable tag f3b06c7 as the direct child of #14577 fix "
            "commit 8be817b, while the official postmortem reports patch releases without "
            "identifying their versions. A precisely derived "
            "valid-projection near-neighbor completes normally through its EOF canary. The three "
            "successful sources are compiled to ordinary .olean files in a mode-0700 private "
            "temporary tree; root/query/olean directory modes are explicitly set and verified "
            "after creation rather than inferred from the ambient umask. Every selected child "
            "also receives a distinct mode-0700 private HOME and TMPDIR; ambient HOME, LOGNAME, "
            "and USER are not retained. All three oleans are separately replayed through the direct "
            "leanchecker --fresh leaf with a private "
            "one-root LEAN_PATH. Here --trust=0 asks Lean to trust no macros and to typecheck "
            "all imported modules; it still trusts the selected Lean implementation and runtime "
            "and does not mean a zero trusted computing base. LeanChecker --fresh replays "
            "imported and defined constants into mkEmptyEnvironment. It runs in a distinct "
            "process through the distinct leanchecker executable leaf from the same selected "
            "release tree; the selected release implementation/runtime remain trusted, and no "
            "binary-equivalence claim is made. The project-defined origin record binds exact "
            "unauthenticated v4.32.2 Shell.lean, LeanChecker.lean, and Environment.lean path, Git "
            "blob, byte-length, SHA-256, and narrowly selected support-scope observations; those "
            "source bytes are not retained here and establish no source-to-binary provenance. "
            "Exact guarded import/lookup probes establish the "
            "bounded selected-name facts observed in these emitted olean bytes: both target "
            "oleans contain and render a residual `axiom E : sorry` left by the failed inductive "
            "route. That establishes only this selected emitted declaration's well-formedness; it "
            "proves neither the intended E type nor acceptance of E as the intended inductive. "
            "Both oleans lack the attempted and rejected "
            "constructor `E.mk`. In the full fixture, that synchronous inductive addDecl failure "
            "makes the downstream `bad` thmDecl source unreachable, so `bad` is not attempted; a "
            "full-only lookup confirms that the name is absent, and the later separate `boom` "
            "command is guarded for its unknown-identifier rejection. Separate known-present and "
            "known-absent clauses in the same probe bracket the "
            "lookup mechanism; they are correlated same-route controls, not an independent "
            "implementation or evidence lens. The minimum fixture contains no `bad` declaration "
            "or reference and has no `bad` probe or absence claim. This is neither a complete "
            "declaration inventory nor a claim that the source declaration attempt rolled back "
            "atomically or completely. Fresh "
            "replay therefore checks the residual emitted declaration and other emitted constants "
            "for well-formedness; it does "
            "not re-elaborate source, rerun #guard_msgs, replay the rejected E.mk attempt, execute "
            "the unreachable `bad` source, or replay the later guarded `boom` command. The local "
            "mapping boundary does not map LeanChecker to postmortem-named nanoda. LeanChecker "
            "is not a fresh or independent kernel implementation. Exact "
            "source/tool endpoint "
            "snapshots immediately bracket every child and are replayed at the end, but they are "
            "not an atomic history: a concurrent privileged or same-UID writer can still perform "
            "a swap/use/restore between endpoints. The already-running Python process predates its "
            "first self-source snapshot. The caller-supplied root is accepted only when all three "
            "direct executable leaves exactly match reviewed-pin release metadata. Those static "
            "pins grant no archive-custody or qualification credit; only a later immutable outer "
            "strict-replay result can carry scoped execution credit. This regression "
            "packet deliberately consumes none of the active scientific project's lean-toolchain, "
            "lakefile, lake manifest, Mathlib cache, proof sources, or generated artifacts, so a "
            "pass cannot migrate or validate that project. This checker's metadata policy seal "
            "omits only finalized custody-checker and nested-checker size/digest fields; the nested "
            "size/digest are separately compared with this exact source snapshot at runtime. "
            "This checker "
            "alone does not prove that the surrounding tree came from the reviewed archive; that "
            "requires its result to be nested in the custody checker's same extraction transaction. "
            "Lake is identity evidence only, not the source execution conduit, and leanchecker is a "
            "second distinct executable leaf from the same selected release tree, not an "
            "independently implemented checker. Reported "
            "monotonic replay durations include this process's bounded child execution and "
            "endpoint checks; they are measurements from this run, not performance guarantees. "
            "The LeanChecker fresh-environment timeout is an execution bound, not kernel evidence. "
            "In the required nested route, direct children are launched without a new session "
            "and initially inherit the outer checker's dedicated process group. The nested "
            "checker never signals its own group; after the nested checker exits on any outcome, "
            "the outer custody supervisor performs bounded TERM/KILL and group-absence checks. "
            "Standalone mode instead isolates each child session and performs that cleanup after "
            "every direct-child outcome, including zero and nonzero early leader exit. "
            "The TERM/KILL array is an escalation policy, not a claim that both signals were "
            "delivered on every outcome. These are "
            "non-atomic PGID endpoint observations: PGID reuse can misdirect or confound a later "
            "signal, descendants can escape by changing process group or session, and Python can "
            "reap only its "
            "direct child rather than non-child descendants. The exact selected Lean leaves are "
            "assumed not to change process group or session, rather than continuously observed. "
            "The 240-second "
            "orchestration allowance "
            "is an assumed budget, not a "
            "proved maximum for filesystem, hashing, process-start, scheduling, or cleanup work. "
            "This does not prove absence of other defects, cap "
            "peak child-output memory, validate theorem meanings or scientific interpretation, "
            "establish nanoda/comparator agreement, or transfer a result to Rust, binary64, PID "
            "estimators, or population claims."
        ),
    }


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--toolchain-root",
        required=True,
        type=Path,
        help=(
            "absolute extracted Lean release root; all three direct executable "
            "leaves must match reviewed-pin repository metadata"
        ),
    )
    parser.add_argument(
        "--shared-outer-process-group",
        action="store_true",
        help=(
            "required only when nested by the custody checker, which starts this checker as "
            "a dedicated process-group leader; direct Lean children are launched without a "
            "new session and initially inherit that group"
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_arguments(sys.argv[1:] if argv is None else argv)
        print(
            json.dumps(
                run_gate(
                    args.toolchain_root,
                    shared_outer_process_group=args.shared_outer_process_group,
                ),
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
        return 0
    except (LeanKernel14576Error, OSError, UnicodeError, ValueError) as error:
        print(f"Lean kernel #14576 regression check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
