#!/usr/bin/env python3
"""Generate one exact, environment-isolated Lean 4.33 current-project replay receipt."""

# ruff: noqa: E402 -- isolation is checked before non-bootstrap imports.

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
        "ERROR: generator requires Python 3.11+ -I -S -B",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

import atexit
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import types


PINNED_ROOT = Path("/private/tmp/pid-rs-sxpid2-atom-bridge.LHX9JM/repo")
SCRIPT = PINNED_ROOT / "scripts/generate-lean-4.33-replay.py"
ROOT = PINNED_ROOT
PINNED_LEAN_BIN = Path(
    "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64/bin"
)
PINNED_PYTHON = Path(
    "/opt/homebrew/Cellar/python@3.14/3.14.6/Frameworks/Python.framework/Versions/3.14/bin/python3.14"
)
PINNED_ARCHIVE = Path(
    "/private/tmp/pid-rs-lean4330-extract.wGhf6H/lean-4.33.0-darwin_aarch64.tar.zst"
)
PINNED_GIT = Path("/usr/bin/git")
PINNED_EXECUTABLE_SHA256 = {
    "git": "179301dcb41ea78accc3fa0048a7e6f6710d891945a751a34addd622020c1818",
    "lake": "58261a1a2fa1a362376c71e02ca854a093e71cc5e6ea64b287a931cb2565273d",
    "lean": "1b370cfcbf44e80d1b004ab1b1ab9a4c73951f9f7c242140bcff9bc577576554",
    "leanchecker": "257f505f8241ab595c6b557d661fd832dbdace6839ab35d9d1600b3dcbce5880",
    "python": "b502cb4c5b46b8d4192ec6bcb600ce8922f1afc396fcf646e8765c6eba74a0bf",
}
PINNED_EXECUTABLE_SIZE_BYTES = {
    "git": 118_928,
    "lake": 51_840,
    "lean": 49_968,
    "leanchecker": 78_128,
    "python": 52_448,
}
PINNED_EXECUTABLE_LINK_COUNTS = {
    "git": 78,
    "lake": 1,
    "lean": 1,
    "leanchecker": 1,
    "python": 1,
}
NORMALIZED_SIGNALS = ("SIGHUP", "SIGINT", "SIGTERM", "SIGPIPE", "SIGCHLD")
COMMAND_TIMEOUT_SECONDS = 3_600
MAX_STDOUT_BYTES = 16 * 1024 * 1024
MAX_STDERR_BYTES = 16 * 1024 * 1024
PROCESS_GROUP_TERM_GRACE_SECONDS = 2.0
PROCESS_GROUP_KILL_GRACE_SECONDS = 2.0
PROCESS_GROUP_POLL_SECONDS = 0.02
OUTPUT = (
    ROOT
    / "audit/evidence/lean-4.33.0-darwin-aarch64-current-project-replay-2026-08-18-r11.json"
)
OUTPUT_TEMPORARY_LEAF = OUTPUT.name + ".tmp"
LEAN_CHECKER_RELATIVE = "scripts/check-lean-toolchain-freeze.py"
COMPOSITE_V6_CHECKER_RELATIVE = "scripts/check-ksg-m1a-composite-v6.py"
GIT_FIXED_ARGUMENTS = (
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.hooksPath=/dev/null",
    "-c",
    "core.attributesFile=/dev/null",
    "-c",
    "diff.external=",
)
FORBIDDEN_LOCAL_GIT_CONFIG_KEYS = {
    "core.attributesfile",
    "core.fsmonitor",
    "core.hookspath",
    "core.worktree",
    "diff.external",
}


def die(message: str) -> None:
    raise SystemExit(message)


def validate_composite_v6_cut_bytes(
    lean_raw: bytes,
    composite_raw: bytes,
    expected_operational: dict[str, str],
) -> None:
    """Require the exact successor cut state before one-shot publication."""

    try:
        lean_source = lean_raw.decode("utf-8", errors="strict")
        composite_source = composite_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        die(f"replay checksum-cut source is not UTF-8: {error}")
    projection_placeholder = 'EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "0" * 64'
    if lean_source.count(projection_placeholder) != 1:
        die("replay projection cut is not the unique zero placeholder")
    projection_assignment_pattern = re.compile(
        r"^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = .+$", re.MULTILINE
    )
    projection_final_pattern = re.compile(
        r'^EXPECTED_REPLAY_RECEIPT_PROJECTION_SHA256 = "([0-9a-f]{64})"$',
        re.MULTILINE,
    )
    if projection_final_pattern.search(lean_source) is not None:
        die("replay projection cut was finalized before the one-shot replay")
    if len(projection_assignment_pattern.findall(lean_source)) != 1:
        die("replay projection cut is not the unique zero placeholder")
    composite_pattern = re.compile(
        r'^EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "([0-9a-f]{64})"$',
        re.MULTILINE,
    )
    operational_pattern = re.compile(
        r'^    "scripts/check-ksg-m1a-composite-v6\.py": "([0-9a-f]{64})",$',
        re.MULTILINE,
    )
    normalized_pattern = re.compile(
        r'^EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = "([0-9a-f]{64})"$',
        re.MULTILINE,
    )
    composite_assignment_pattern = re.compile(
        r"^EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = .+$", re.MULTILINE
    )
    operational_assignment_pattern = re.compile(
        r'^    "scripts/check-ksg-m1a-composite-v6\.py": .+$', re.MULTILINE
    )
    normalized_assignment_pattern = re.compile(
        r"^EXPECTED_NORMALIZED_LEAN_CHECKER_SHA256 = .+$", re.MULTILINE
    )
    composite_matches = list(composite_pattern.finditer(lean_source))
    operational_matches = list(operational_pattern.finditer(lean_source))
    normalized_matches = list(normalized_pattern.finditer(composite_source))
    if (
        len(composite_matches) != 1
        or len(operational_matches) != 1
        or len(composite_assignment_pattern.findall(lean_source)) != 1
        or len(operational_assignment_pattern.findall(lean_source)) != 1
    ):
        die("composite-v6 checker digest cuts are not unique final literals")
    if (
        len(normalized_matches) != 1
        or len(normalized_assignment_pattern.findall(composite_source)) != 1
    ):
        die("normalized Lean checker cut is not a unique final literal")
    composite_digest = hashlib.sha256(composite_raw).hexdigest()
    composite_cut = composite_matches[0].group(1)
    operational_cut = operational_matches[0].group(1)
    normalized_cut = normalized_matches[0].group(1)
    if (
        composite_cut == "0" * 64
        or operational_cut == "0" * 64
        or composite_cut != operational_cut
        or composite_cut != composite_digest
        or expected_operational.get(COMPOSITE_V6_CHECKER_RELATIVE) != composite_digest
    ):
        die("composite-v6 checker digest cuts do not bind the exact checker bytes")
    if normalized_cut == "0" * 64:
        die("normalized Lean checker cut remains a placeholder")
    normalized_lean_source = composite_pattern.sub(
        'EXPECTED_COMPOSITE_V6_CHECKER_OPERATIONAL_SHA256 = "0" * 64',
        lean_source,
        count=1,
    )
    normalized_lean_source = operational_pattern.sub(
        '    "scripts/check-ksg-m1a-composite-v6.py": "0" * 64,',
        normalized_lean_source,
        count=1,
    )
    normalized_digest = hashlib.sha256(
        normalized_lean_source.encode("utf-8")
    ).hexdigest()
    if normalized_cut != normalized_digest:
        die("normalized Lean checker cut does not bind the exact three-cut source")


def validate_composite_v6_cut_state(freeze: types.ModuleType, root: Path) -> None:
    lean_raw = freeze.stable_read(
        root / LEAN_CHECKER_RELATIVE, "pre-replay Lean checker cut state"
    ).raw
    composite_raw = freeze.stable_read(
        root / COMPOSITE_V6_CHECKER_RELATIVE,
        "pre-replay composite-v6 checker cut state",
    ).raw
    validate_composite_v6_cut_bytes(
        lean_raw, composite_raw, freeze.EXPECTED_OPERATIONAL_WIRING_HASHES
    )


def leaf_metadata(parent_descriptor: int, leaf: str) -> os.stat_result | None:
    try:
        return os.stat(leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None


def require_leaf_absent(parent_descriptor: int, leaf: str, role: str) -> None:
    if leaf_metadata(parent_descriptor, leaf) is not None:
        die(f"{role} already exists")


def open_output_parent(path: Path) -> tuple[int, tuple[int, int, int]]:
    before = os.lstat(path)
    if not stat.S_ISDIR(before.st_mode) or stat.S_ISLNK(before.st_mode):
        die("receipt parent must be a real directory")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    opened = os.fstat(descriptor)
    if directory_identity(before) != directory_identity(opened):
        os.close(descriptor)
        die("receipt parent identity changed while opening")
    return descriptor, directory_identity(opened)


def revalidate_output_parent(
    descriptor: int,
    path: Path,
    expected_identity: tuple[int, int, int],
) -> None:
    descriptor_identity = directory_identity(os.fstat(descriptor))
    path_identity = directory_identity(os.lstat(path))
    if descriptor_identity != expected_identity or path_identity != expected_identity:
        die("receipt parent route changed during replay")


def unlink_matching_leaf(
    parent_descriptor: int, leaf: str, expected_device_inode: tuple[int, int]
) -> None:
    metadata = leaf_metadata(parent_descriptor, leaf)
    if metadata is None:
        return
    if (metadata.st_dev, metadata.st_ino) != expected_device_inode:
        raise RuntimeError(f"refusing to unlink replaced cleanup leaf: {leaf}")
    os.unlink(leaf, dir_fd=parent_descriptor)


def validate_published_receipt(
    parent_descriptor: int, output_leaf: str, expected: bytes
) -> tuple[int, int]:
    before = os.stat(output_leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    if (
        not stat.S_ISREG(before.st_mode)
        or stat.S_ISLNK(before.st_mode)
        or stat.S_IMODE(before.st_mode) != 0o644
        or before.st_nlink != 1
        or before.st_size != len(expected)
    ):
        die("published receipt identity drifted")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(output_leaf, flags, dir_fd=parent_descriptor)
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
    after = os.stat(output_leaf, dir_fd=parent_descriptor, follow_symlinks=False)
    identities = tuple(
        metadata_identity(value) for value in (before, opened, after_descriptor, after)
    )
    if any(value != identities[0] for value in identities[1:]):
        die("published receipt identity changed during validation")
    if bytes(first) != expected or bytes(second) != expected:
        die("published receipt bytes drifted")
    return before.st_dev, before.st_ino


def stat_newly_linked_receipt(
    parent_descriptor: int, output_leaf: str
) -> os.stat_result:
    """Inspect the newly created output link without following it."""

    return os.stat(output_leaf, dir_fd=parent_descriptor, follow_symlinks=False)


def publish_receipt_no_clobber(
    raw: bytes,
    parent_descriptor: int,
    parent_path: Path,
    parent_identity: tuple[int, int, int],
    output_leaf: str,
    temporary_leaf: str,
) -> None:
    """Durably publish once within one retained directory, or roll back our leaves."""

    revalidate_output_parent(parent_descriptor, parent_path, parent_identity)
    require_leaf_absent(parent_descriptor, temporary_leaf, "temporary receipt path")
    require_leaf_absent(parent_descriptor, output_leaf, "versioned output receipt")
    temporary_device_inode: tuple[int, int] | None = None
    published_device_inode: tuple[int, int] | None = None
    temporary_present = False
    published_present = False
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(temporary_leaf, flags, 0o600, dir_fd=parent_descriptor)
        temporary_present = True
        try:
            opened = os.fstat(descriptor)
            temporary_device_inode = (opened.st_dev, opened.st_ino)
            if (
                not stat.S_ISREG(opened.st_mode)
                or stat.S_IMODE(opened.st_mode) != 0o600
                or opened.st_nlink != 1
                or opened.st_size != 0
            ):
                die("private receipt construction identity drifted")
            remaining = memoryview(raw)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    die("receipt write made no progress")
                remaining = remaining[written:]
            written_state = os.fstat(descriptor)
            if (
                not stat.S_ISREG(written_state.st_mode)
                or stat.S_IMODE(written_state.st_mode) != 0o600
                or written_state.st_nlink != 1
                or written_state.st_size != len(raw)
                or (written_state.st_dev, written_state.st_ino)
                != temporary_device_inode
            ):
                die("private receipt identity drifted during construction")
            os.fchmod(descriptor, 0o644)
            ready = os.fstat(descriptor)
            if (
                not stat.S_ISREG(ready.st_mode)
                or stat.S_IMODE(ready.st_mode) != 0o644
                or ready.st_nlink != 1
                or ready.st_size != len(raw)
                or (ready.st_dev, ready.st_ino) != temporary_device_inode
            ):
                die("private receipt did not reach canonical publication identity")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        revalidate_output_parent(parent_descriptor, parent_path, parent_identity)
        require_leaf_absent(parent_descriptor, output_leaf, "versioned output receipt")
        os.link(
            temporary_leaf,
            output_leaf,
            src_dir_fd=parent_descriptor,
            dst_dir_fd=parent_descriptor,
            follow_symlinks=False,
        )
        published_present = True
        # The hard link names the already-observed temporary inode. Record that identity
        # before any fallible post-link observation so exact rollback remains possible.
        published_device_inode = temporary_device_inode
        linked = stat_newly_linked_receipt(parent_descriptor, output_leaf)
        if (
            (linked.st_dev, linked.st_ino) != temporary_device_inode
            or not stat.S_ISREG(linked.st_mode)
            or stat.S_IMODE(linked.st_mode) != 0o644
            or linked.st_nlink != 2
            or linked.st_size != len(raw)
        ):
            die("published receipt link identity drifted")
        os.fsync(parent_descriptor)
        unlink_matching_leaf(parent_descriptor, temporary_leaf, temporary_device_inode)
        temporary_present = False
        os.fsync(parent_descriptor)
        published_device_inode = validate_published_receipt(
            parent_descriptor, output_leaf, raw
        )
        revalidate_output_parent(parent_descriptor, parent_path, parent_identity)
        os.fsync(parent_descriptor)
    except BaseException as operation_error:
        cleanup_errors: list[BaseException] = []
        if temporary_present and temporary_device_inode is not None:
            try:
                unlink_matching_leaf(
                    parent_descriptor, temporary_leaf, temporary_device_inode
                )
            except BaseException as error:
                cleanup_errors.append(error)
        if published_present and published_device_inode is not None:
            try:
                unlink_matching_leaf(
                    parent_descriptor, output_leaf, published_device_inode
                )
            except BaseException as error:
                cleanup_errors.append(error)
        try:
            os.fsync(parent_descriptor)
        except BaseException as error:
            cleanup_errors.append(error)
        if cleanup_errors:
            raise RuntimeError(
                "receipt publication failed and exact-leaf rollback was incomplete"
            ) from operation_error
        raise


def read_exact_source(path: Path, maximum_bytes: int = 8 * 1024 * 1024) -> bytes:
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        die(f"exact module source is not a single-link regular file: {path}")
    if before.st_size > maximum_bytes:
        die(f"exact module source exceeds the size ceiling: {path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        first_buffer = bytearray()
        while len(first_buffer) <= maximum_bytes:
            chunk = os.read(
                descriptor, min(1024 * 1024, maximum_bytes + 1 - len(first_buffer))
            )
            if not chunk:
                break
            first_buffer.extend(chunk)
        first = bytes(first_buffer)
        if len(first) > maximum_bytes:
            die(f"exact module source exceeds the size ceiling: {path}")
        os.lseek(descriptor, 0, os.SEEK_SET)
        second_buffer = bytearray()
        while len(second_buffer) <= maximum_bytes:
            chunk = os.read(
                descriptor, min(1024 * 1024, maximum_bytes + 1 - len(second_buffer))
            )
            if not chunk:
                break
            second_buffer.extend(chunk)
        second = bytes(second_buffer)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)
    identities = tuple(
        metadata_identity(value) for value in (before, opened, after_descriptor, after)
    )
    if (
        any(value != identities[0] for value in identities[1:])
        or first != second
        or len(first) != before.st_size
    ):
        die(f"exact module source changed during read: {path}")
    return first


def load_module(path: Path, name: str):
    source = read_exact_source(path)
    code = compile(
        source, os.fspath(path), "exec", dont_inherit=True, optimize=sys.flags.optimize
    )
    module = types.ModuleType(name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    sys.modules[name] = module
    try:
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def stream(payload: bytes) -> dict[str, object]:
    return {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def metadata_identity(
    metadata: os.stat_result,
) -> tuple[int, int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def directory_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return metadata.st_dev, metadata.st_ino, metadata.st_mode


def executable_snapshot(
    path: Path,
    expected_size: int,
    expected_link_count: int,
) -> tuple[tuple[int, int, int, int, int, int, int], str]:
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != expected_link_count:
        die(f"pinned executable type/link count drifted: {path}")
    if before.st_size != expected_size:
        die(f"pinned executable size drifted before hashing: {path}")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        hasher = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            hasher.update(chunk)
        after_descriptor = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)
    identities = tuple(
        metadata_identity(value) for value in (before, opened, after_descriptor, after)
    )
    if any(value != identities[0] for value in identities[1:]):
        die(f"pinned executable identity changed during hashing: {path}")
    if opened.st_size != expected_size or opened.st_nlink != expected_link_count:
        die(f"pinned executable size/link count drifted during hashing: {path}")
    return identities[0], hasher.hexdigest()


def normalize_process_signals() -> None:
    if not hasattr(signal, "pthread_sigmask"):
        die("pthread_sigmask is required for the replay runner")
    signal.pthread_sigmask(signal.SIG_SETMASK, set())
    if signal.pthread_sigmask(signal.SIG_BLOCK, set()):
        die("runner signal mask is not empty")
    for name in NORMALIZED_SIGNALS:
        if not hasattr(signal, name):
            die(f"required signal is unavailable: {name}")
        signum = getattr(signal, name)
        signal.signal(signum, signal.SIG_DFL)
        if signal.getsignal(signum) is not signal.SIG_DFL:
            die(f"signal disposition did not normalize: {name}")


def process_group_exists(process_group: int) -> bool:
    if process_group <= 1 or process_group == os.getpgrp():
        die("refusing unsafe child process-group probe")
    try:
        os.killpg(process_group, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def wait_for_process_group_absence(
    process_group: int, seconds: float, process: subprocess.Popen[bytes]
) -> bool:
    deadline = time.monotonic() + seconds
    process.poll()
    while process_group_exists(process_group):
        process.poll()
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(PROCESS_GROUP_POLL_SECONDS, remaining))
    return True


def cleanup_process_group(process: subprocess.Popen[bytes]) -> None:
    process_group = process.pid
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
        if wait_for_process_group_absence(process_group, grace, process):
            break
    process.poll()
    if process_group_exists(process_group):
        die("captured child process group survived bounded cleanup")
    try:
        process.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        die("direct child was not reaped after bounded process-group cleanup")


def run_bounded_process(
    executed: tuple[str, ...],
    cwd: Path,
    environment: dict[str, str],
    input_bytes: bytes,
    temporary_directory_identity: tuple[int, int, int],
) -> tuple[int, bytes, bytes]:
    if not executed or not all(isinstance(item, str) and item for item in executed):
        die("child argv is not a nonempty tuple of text")
    if not isinstance(input_bytes, bytes):
        die("child input is not exact bytes")
    if not cwd.is_absolute() or cwd.resolve(strict=True) != cwd:
        die("child cwd is not a canonical existing route")
    if tuple(sorted(environment)) != (
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OPTIONAL_LOCKS",
        "GIT_PAGER",
        "GIT_TERMINAL_PROMPT",
        "HOME",
        "LANG",
        "LC_ALL",
        "PAGER",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
        "TMPDIR",
        "TZ",
    ):
        die("child environment allowlist drifted")
    temporary_directory = Path(environment["TMPDIR"])
    if (
        not temporary_directory.is_absolute()
        or directory_identity(os.lstat(temporary_directory))
        != temporary_directory_identity
        or temporary_directory.resolve(strict=True) != temporary_directory
    ):
        die("isolated child temporary directory identity drifted")
    input_file = tempfile.TemporaryFile(dir=environment["TMPDIR"])
    try:
        input_file.write(input_bytes)
        input_file.flush()
        input_file.seek(0)
        process = subprocess.Popen(
            executed,
            cwd=cwd,
            env=environment,
            stdin=input_file,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            start_new_session=True,
        )
    finally:
        input_file.close()
    if process.stdout is None or process.stderr is None:
        cleanup_process_group(process)
        die("child pipes were not created")
    stdout = bytearray()
    stderr = bytearray()
    selector = selectors.DefaultSelector()
    deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
    try:
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stderr.fileno(), False)
        selector.register(
            process.stdout, selectors.EVENT_READ, (stdout, MAX_STDOUT_BYTES)
        )
        selector.register(
            process.stderr, selectors.EVENT_READ, (stderr, MAX_STDERR_BYTES)
        )
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                die(f"child command exceeded {COMMAND_TIMEOUT_SECONDS} seconds")
            for key, _mask in selector.select(
                min(PROCESS_GROUP_POLL_SECONDS, remaining)
            ):
                chunk = os.read(key.fileobj.fileno(), 64 * 1024)
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                target, ceiling = key.data
                if len(target) + len(chunk) > ceiling:
                    die(f"child output exceeded {ceiling} bytes")
                target.extend(chunk)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            die(f"child command exceeded {COMMAND_TIMEOUT_SECONDS} seconds")
        returncode = process.wait(timeout=remaining)
    except BaseException as operation_error:
        try:
            cleanup_process_group(process)
        except BaseException as cleanup_error:
            raise cleanup_error from operation_error
        raise
    finally:
        selector.close()
    cleanup_process_group(process)
    return returncode, bytes(stdout), bytes(stderr)


def reject_repository_bytecode_cache(root: Path) -> None:
    scripts = root / "scripts"
    for directory, names, files in os.walk(scripts, topdown=True, followlinks=False):
        base = Path(directory)
        directory_metadata = os.lstat(base)
        if not stat.S_ISDIR(directory_metadata.st_mode) or stat.S_ISLNK(
            directory_metadata.st_mode
        ):
            die(f"scripts route contains a non-directory traversal node: {base}")
        for name in names:
            candidate = base / name
            metadata = os.lstat(candidate)
            if stat.S_ISLNK(metadata.st_mode):
                die(f"scripts route contains a symbolic-link directory: {candidate}")
            if name == "__pycache__":
                die(f"repository Python bytecode cache is forbidden: {candidate}")
        for name in files:
            candidate = base / name
            metadata = os.lstat(candidate)
            if stat.S_ISLNK(metadata.st_mode):
                die(f"scripts route contains a symbolic-link file: {candidate}")
            if name.endswith((".pyc", ".pyo")):
                die(f"repository Python bytecode cache is forbidden: {candidate}")


def decode_exact_line(payload: bytes, role: str) -> str:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeError as error:
        die(f"{role} is not UTF-8: {error}")
    if not text.endswith("\n") or "\n" in text[:-1] or "\x00" in text:
        die(f"{role} is not one exact line")
    return text[:-1]


def run_pinned_git(
    git: Path,
    git_snapshot: tuple[tuple[int, int, int, int, int, int, int], str],
    cwd: Path,
    environment: dict[str, str],
    arguments: tuple[str, ...],
    role: str,
    records: list[dict[str, object]],
    temporary_directory_identity: tuple[int, int, int],
) -> bytes:
    if (
        executable_snapshot(
            git,
            PINNED_EXECUTABLE_SIZE_BYTES["git"],
            PINNED_EXECUTABLE_LINK_COUNTS["git"],
        )
        != git_snapshot
    ):
        die("pinned Git executable changed before dependency preflight command")
    executed = (os.fspath(git), *GIT_FIXED_ARGUMENTS, *arguments)
    start = timestamp()
    returncode, stdout, stderr = run_bounded_process(
        executed,
        cwd,
        environment,
        b"",
        temporary_directory_identity,
    )
    if returncode != 0:
        die(f"{role} failed with exit {returncode}")
    if stderr:
        die(f"{role} emitted stderr")
    if (
        executable_snapshot(
            git,
            PINNED_EXECUTABLE_SIZE_BYTES["git"],
            PINNED_EXECUTABLE_LINK_COUNTS["git"],
        )
        != git_snapshot
    ):
        die("pinned Git executable changed after dependency preflight command")
    end = timestamp()
    records.append(
        {
            "argv_executed": list(executed),
            "cwd_observed_absolute": os.fspath(cwd),
            "end_utc": end,
            "executable_snapshot_equal_before_after": True,
            "exit_code": returncode,
            "name": role,
            "start_utc": start,
            "stderr": stream(stderr),
            "stdin": stream(b""),
            "stdout": stream(stdout),
        }
    )
    return stdout


def check_dependency_checkouts(
    packages_directory: Path,
    expected_package_pins: dict[str, tuple[str, str, str, bool]],
    git: Path,
    git_snapshot: tuple[tuple[int, int, int, int, int, int, int], str],
    environment: dict[str, str],
    records: list[dict[str, object]],
    temporary_directory_identity: tuple[int, int, int],
) -> None:
    if packages_directory.resolve(strict=True) != packages_directory:
        die("dependency packages route is not canonical")
    actual_names: set[str] = set()
    with os.scandir(packages_directory) as entries:
        for entry in entries:
            if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                die(f"dependency package entry is not a real directory: {entry.name}")
            actual_names.add(entry.name)
    expected_names = set(expected_package_pins)
    if actual_names != expected_names:
        die(
            "dependency package set drifted: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )
    for name in sorted(expected_names):
        url, revision, _input_revision, _inherited = expected_package_pins[name]
        checkout = packages_directory / name
        if checkout.resolve(strict=True) != checkout:
            die(f"dependency checkout route is not canonical: {name}")
        local_config = run_pinned_git(
            git,
            git_snapshot,
            checkout,
            environment,
            ("config", "--no-includes", "--local", "--name-only", "--list"),
            f"{name} local config inventory",
            records,
            temporary_directory_identity,
        )
        config_keys = {
            key.lower()
            for key in local_config.decode("utf-8", errors="strict").splitlines()
        }
        if any(
            key in FORBIDDEN_LOCAL_GIT_CONFIG_KEYS
            or key.startswith(("include.", "includeif.", "filter."))
            for key in config_keys
        ):
            die(f"dependency checkout has forbidden local Git configuration: {name}")
        top_level = decode_exact_line(
            run_pinned_git(
                git,
                git_snapshot,
                checkout,
                environment,
                ("rev-parse", "--show-toplevel"),
                f"{name} root check",
                records,
                temporary_directory_identity,
            ),
            f"{name} root output",
        )
        if top_level != os.fspath(checkout):
            die(f"dependency checkout root mismatch: {name}")
        actual_revision = decode_exact_line(
            run_pinned_git(
                git,
                git_snapshot,
                checkout,
                environment,
                ("rev-parse", "--verify", "HEAD"),
                f"{name} revision check",
                records,
                temporary_directory_identity,
            ),
            f"{name} revision output",
        )
        if actual_revision != revision:
            die(f"dependency revision mismatch: {name}")
        actual_url = decode_exact_line(
            run_pinned_git(
                git,
                git_snapshot,
                checkout,
                environment,
                ("config", "--no-includes", "--local", "--get", "remote.origin.url"),
                f"{name} origin check",
                records,
                temporary_directory_identity,
            ),
            f"{name} origin output",
        )
        if actual_url != url:
            die(f"dependency origin mismatch: {name}")
        status = run_pinned_git(
            git,
            git_snapshot,
            checkout,
            environment,
            ("status", "--porcelain=v1", "--untracked-files=all"),
            f"{name} cleanliness check",
            records,
            temporary_directory_identity,
        )
        if status:
            die(f"dependency checkout is not clean: {name}")


def main() -> int:
    if len(sys.argv) != 1:
        die("usage: generate-lean-4.33-replay.py (no arguments)")
    os.umask(0o077)
    normalize_process_signals()
    launched_script = Path(os.path.abspath(os.fspath(Path(__file__))))
    if launched_script != SCRIPT:
        die("runner was not launched from the pinned repository route")
    if SCRIPT.resolve(strict=True) != SCRIPT or ROOT.resolve(strict=True) != ROOT:
        die("runner and repository routes must be canonical non-symlink paths")
    root = ROOT
    lean_bin = PINNED_LEAN_BIN
    python = PINNED_PYTHON
    archive = PINNED_ARCHIVE
    output = OUTPUT
    output_leaf = output.name
    temporary_leaf = OUTPUT_TEMPORARY_LEAF
    if lean_bin.resolve(strict=True) != lean_bin:
        die("pinned Lean bin route is not canonical")
    if python.resolve(strict=True) != python:
        die("pinned Python route is not canonical")
    if archive.resolve(strict=True) != archive:
        die("pinned archive route is not canonical")
    if Path(sys.executable) != python or python.resolve(strict=True) != python:
        die("runner was not launched by the pinned Python executable")
    if PINNED_GIT.resolve(strict=True) != PINNED_GIT:
        die("pinned Git route is not canonical")
    if output.parent.resolve(strict=True) != output.parent:
        die("receipt parent route is not canonical")
    output_parent_descriptor, output_parent_identity = open_output_parent(output.parent)
    atexit.register(os.close, output_parent_descriptor)
    require_leaf_absent(
        output_parent_descriptor, temporary_leaf, "temporary receipt path"
    )
    require_leaf_absent(
        output_parent_descriptor, output_leaf, "versioned output receipt"
    )
    reject_repository_bytecode_cache(root)
    freeze = load_module(root / "scripts/check-lean-toolchain-freeze.py", "pid_freeze")
    if (
        freeze.RECEIPT != output
        or freeze.RECEIPT_RELATIVE != output.relative_to(root).as_posix()
    ):
        die("replay generator/checker receipt routes diverged")
    validate_composite_v6_cut_state(freeze, root)
    finite = load_module(
        root / "scripts/check-lean-finite-convergence.py", "pid_finite"
    )
    lake = lean_bin / "lake"
    lean = lean_bin / "lean"
    leanchecker = lean_bin / "leanchecker"
    for name, path in {"lake": lake, "lean": lean, "leanchecker": leanchecker}.items():
        if path.resolve(strict=True) != path:
            die(f"pinned Lean executable route is not canonical: {name}")
    executables = {
        "git": PINNED_GIT,
        "lake": lake,
        "lean": lean,
        "leanchecker": leanchecker,
        "python": python,
    }
    executable_snapshots = {
        name: executable_snapshot(
            path,
            PINNED_EXECUTABLE_SIZE_BYTES[name],
            PINNED_EXECUTABLE_LINK_COUNTS[name],
        )
        for name, path in executables.items()
    }
    for name, path in executables.items():
        if executable_snapshots[name][1] != PINNED_EXECUTABLE_SHA256[name]:
            die(f"pinned executable digest drifted: {name}")
    project = root / "audit/formal/lean"
    if os.path.lexists(project / ".lake/build") or os.path.lexists(
        project / ".lake/config"
    ):
        die("project build/config must be absent before replay")
    if (
        not os.path.lexists(project / ".lake/packages")
        or (project / ".lake/packages").is_symlink()
        or not (project / ".lake/packages").is_dir()
    ):
        die("dependency packages directory is absent")

    archive_start = timestamp()
    try:
        archive_lstat_before = os.lstat(archive)
    except OSError as error:
        die(f"cannot inspect archive: {error}")
    if (
        not stat.S_ISREG(archive_lstat_before.st_mode)
        or archive_lstat_before.st_nlink != 1
    ):
        die("archive must be a single-link regular file")
    if archive_lstat_before.st_size != freeze.EXPECTED_ARCHIVE["size_bytes"]:
        die("archive size differs from the frozen pin before hashing")
    archive_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        archive_flags |= os.O_NOFOLLOW
    descriptor = os.open(archive, archive_flags)
    try:
        archive_fstat_before = os.fstat(descriptor)
        if archive_fstat_before.st_size != freeze.EXPECTED_ARCHIVE["size_bytes"]:
            die("opened archive size differs from the frozen pin before hashing")
        archive_hasher = hashlib.sha256()
        while chunk := os.read(descriptor, 1024 * 1024):
            archive_hasher.update(chunk)
        archive_fstat_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    archive_lstat_after = os.lstat(archive)

    def archive_identity(value):
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        archive_identity(archive_lstat_before)
        == archive_identity(archive_fstat_before)
        == archive_identity(archive_fstat_after)
        == archive_identity(archive_lstat_after)
    ):
        die("archive identity changed during hashing")
    archive_digest = archive_hasher.hexdigest()
    if (
        archive_fstat_after.st_size != freeze.EXPECTED_ARCHIVE["size_bytes"]
        or archive_digest != freeze.EXPECTED_ARCHIVE["sha256"]
        or archive.name != freeze.EXPECTED_ARCHIVE["file_name"]
    ):
        die("archive size, digest, or basename differs from the frozen pin")
    archive_end = timestamp()
    archive_observation = {
        "end_utc": archive_end,
        "path_observed_absolute": os.fspath(archive),
        "sha256": archive_digest,
        "single_link_regular_file": True,
        "size_bytes": archive_fstat_after.st_size,
        "stable_descriptor_identity": True,
        "start_utc": archive_start,
    }

    environment_root = Path(
        tempfile.mkdtemp(prefix="pid-rs-lean433-replay-env.", dir="/private/tmp")
    ).resolve(strict=True)
    atexit.register(shutil.rmtree, environment_root, ignore_errors=True)
    isolated_home = environment_root / "home"
    isolated_tmpdir = environment_root / "tmp"
    isolated_home.mkdir(mode=0o700)
    isolated_tmpdir.mkdir(mode=0o700)
    isolated_tmpdir_identity = directory_identity(os.lstat(isolated_tmpdir))
    environment = {
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": os.fspath(isolated_home),
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": os.pathsep.join((os.fspath(lean_bin), "/usr/bin", "/bin")),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TMPDIR": os.fspath(isolated_tmpdir),
        "TZ": "UTC",
    }
    if tuple(sorted(environment)) != (
        "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_NOSYSTEM",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OPTIONAL_LOCKS",
        "GIT_PAGER",
        "GIT_TERMINAL_PROMPT",
        "HOME",
        "LANG",
        "LC_ALL",
        "PAGER",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "PYTHONNOUSERSITE",
        "TMPDIR",
        "TZ",
    ):
        die("effective environment allowlist drifted")
    freeze.check_static_without_receipt()
    dependency_preflight_records: list[dict[str, object]] = []
    check_dependency_checkouts(
        project / ".lake/packages",
        freeze.EXPECTED_PACKAGE_PINS,
        PINNED_GIT,
        executable_snapshots["git"],
        environment,
        dependency_preflight_records,
        isolated_tmpdir_identity,
    )
    custody_before = {
        relative: freeze.stable_read(
            root / relative, f"pre-replay custody gate: {relative}"
        )
        for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS
    }
    records: list[dict[str, object]] = []
    axiom_input: bytes | None = None
    build_stdout = b""

    for name, cwd_relative, logical in freeze.expected_command_specs():
        cwd = root if cwd_relative == "." else root / cwd_relative
        if logical[0] == "lean":
            executed = (os.fspath(lean), *logical[1:])
        elif logical[0] == "lake":
            executed = (os.fspath(lake), *logical[1:])
        elif logical[0] == "python3":
            executed = (os.fspath(python), *logical[1:])
        else:
            die(f"unsupported executable: {logical[0]}")
        input_bytes = b""
        cache_state = None
        if name == "theorem_axiom_audit":
            _source_count, _declaration_count, theorem_names = finite.check_sources()
            input_bytes = finite.theorem_axiom_audit_source(theorem_names).encode(
                "utf-8"
            )
            if stream(input_bytes) != freeze.EXPECTED_THEOREM_AXIOM_AUDIT_STDIN:
                die("theorem axiom query identity differs from the frozen expectation")
            axiom_input = input_bytes
        elif name == "clean_build":
            build_absent = not os.path.lexists(project / ".lake/build")
            config_absent = not os.path.lexists(project / ".lake/config")
            packages_present = (
                os.path.lexists(project / ".lake/packages")
                and not (project / ".lake/packages").is_symlink()
                and (project / ".lake/packages").is_dir()
            )
            if not (build_absent and config_absent and packages_present):
                die("clean-build cache preflight changed before launch")
            cache_state = {
                "dependency_packages_directory_present_before": packages_present,
                "project_build_directory_absent_before": build_absent,
                "project_config_directory_absent_before": config_absent,
                "project_oleans_reused": False,
            }
        start = timestamp()
        executable_name = {"lean": "lean", "lake": "lake", "python3": "python"}[
            logical[0]
        ]
        if (
            executable_snapshot(
                executables[executable_name],
                PINNED_EXECUTABLE_SIZE_BYTES[executable_name],
                PINNED_EXECUTABLE_LINK_COUNTS[executable_name],
            )
            != executable_snapshots[executable_name]
        ):
            die(f"pinned executable changed before launch: {executable_name}")
        if logical[0] == "python3" and (
            executable_snapshot(
                executables["git"],
                PINNED_EXECUTABLE_SIZE_BYTES["git"],
                PINNED_EXECUTABLE_LINK_COUNTS["git"],
            )
            != executable_snapshots["git"]
        ):
            die("pinned Git executable changed before Python formal gate")
        returncode, stdout, stderr = run_bounded_process(
            executed, cwd, environment, input_bytes, isolated_tmpdir_identity
        )
        end = timestamp()
        if returncode != 0:
            sys.stderr.buffer.write(stderr)
            die(f"{name} failed with exit {returncode}")
        if stderr:
            sys.stderr.buffer.write(stderr)
            die(f"{name} emitted stderr")
        if name == "lean_version_probe" and stdout != (
            "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
            + freeze.EXPECTED_LEAN_IDENTITY["commit"]
            + ", Release)\n"
        ).encode("utf-8"):
            die("Lean version probe did not match the frozen identity")
        if name == "lake_version_probe" and stdout != (
            "Lake version 5.0.0-src+d8b1897 (Lean version 4.33.0)\n"
        ).encode("utf-8"):
            die("Lake version probe did not match the frozen identity")
        if name == "clean_build":
            build_stdout = stdout
        records.append(
            {
                "argv_executed": list(executed),
                "argv_logical": list(logical),
                "cache_state": cache_state,
                "cwd_observed_absolute": os.fspath(cwd),
                "cwd_repo_relative": cwd_relative,
                "end_utc": end,
                "exit_code": returncode,
                "name": name,
                "start_utc": start,
                "stderr": stream(stderr),
                "stdin": stream(input_bytes),
                "stdout": stream(stdout),
            }
        )

    freeze.check_static_without_receipt()
    for name, path in executables.items():
        if (
            executable_snapshot(
                path,
                PINNED_EXECUTABLE_SIZE_BYTES[name],
                PINNED_EXECUTABLE_LINK_COUNTS[name],
            )
            != executable_snapshots[name]
        ):
            die(f"pinned executable changed during replay: {name}")
    custody_after = {
        relative: freeze.stable_read(
            root / relative, f"post-replay custody gate: {relative}"
        )
        for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS
    }
    for relative in freeze.EXPECTED_CUSTODY_GATE_PATHS:
        if (
            custody_before[relative].sha256 != custody_after[relative].sha256
            or custody_before[relative].identity != custody_after[relative].identity
        ):
            die(f"custody gate changed during replay: {relative}")
    by_name = {record["name"]: record for record in records}
    lean_line = (
        "Lean (version 4.33.0, arm64-apple-darwin24.6.0, commit "
        + freeze.EXPECTED_LEAN_IDENTITY["commit"]
        + ", Release)\n"
    )
    lake_line = "Lake version 5.0.0-src+d8b1897 (Lean version 4.33.0)\n"
    if by_name["lean_version_probe"]["stdout"] != stream(lean_line.encode("utf-8")):
        die("Lean version record drifted")
    if by_name["lake_version_probe"]["stdout"] != stream(lake_line.encode("utf-8")):
        die("Lake version record drifted")
    if (
        build_stdout.decode("utf-8", errors="strict")
        != freeze.EXPECTED_CLEAN_BUILD_STDOUT
    ):
        die("quiet warning-failing clean build emitted stdout")
    if axiom_input is None:
        die("axiom input was not recorded")

    parity: dict[str, object] = {}
    for pair in freeze.PYTHON_COMMAND_PAIRS:
        normal = by_name[f"{pair}:normal"]
        optimized = by_name[f"{pair}:optimized"]
        if (
            normal["stdout"] != optimized["stdout"]
            or normal["stderr"] != optimized["stderr"]
        ):
            die(f"normal/-O output differs: {pair}")
        parity[pair] = {
            "normal_stderr": normal["stderr"],
            "normal_stdout": normal["stdout"],
            "optimized_stderr": optimized["stderr"],
            "optimized_stdout": optimized["stdout"],
        }

    packages = {
        name: {
            "inherited": inherited,
            "input_revision": input_revision,
            "revision": revision,
            "url": url,
        }
        for name, (
            url,
            revision,
            input_revision,
            inherited,
        ) in freeze.EXPECTED_PACKAGE_PINS.items()
    }
    receipt = {
        "active_claim_authority_sha256": freeze.EXPECTED_ACTIVE_CLAIM_HASHES,
        "active_configuration": freeze.EXPECTED_CONFIG_HASHES,
        "active_resume_sha256": freeze.EXPECTED_ACTIVE_RESUME_HASHES,
        "checker_sha256": freeze.EXPECTED_CHECKER_HASHES,
        "command_records": records,
        "compatibility_scope": {
            "broad_or_file_global_occurrences": 0,
            "command_scoped_fintype_derivation_occurrences": 3,
            "option": freeze.OPTION,
            "proof_term_local_occurrences": 4,
            "total_occurrences": 7,
        },
        "current_evidence_sha256": freeze.EXPECTED_CURRENT_EVIDENCE_HASHES,
        "custody_gate_sha256": {
            path: custody_after[path].sha256
            for path in freeze.EXPECTED_CUSTODY_GATE_PATHS
        },
        "derived_instance_evidence_sha256": freeze.EXPECTED_DERIVED_EVIDENCE_HASHES,
        "dependency_checkout_preflight": dependency_preflight_records,
        "environment_policy": {
            "ambient_environment_inherited": False,
            "command_timeout_seconds": COMMAND_TIMEOUT_SECONDS,
            "effective_nonsecret_environment": environment,
            "isolated_home_initially_empty": True,
            "isolated_tmpdir_initially_empty": True,
            "isolated_tmpdir_identity_retained": True,
            "max_stderr_bytes": MAX_STDERR_BYTES,
            "max_stdout_bytes": MAX_STDOUT_BYTES,
            "new_session_process_group_each_command": True,
            "process_group_cleanup_bounded_best_effort": True,
            "python_isolation_flags": ["-I", "-S", "-B"],
            "routing_variables_inherited": [],
            "signal_dispositions": {name: "SIG_DFL" for name in NORMALIZED_SIGNALS},
            "signal_mask": [],
            "stdin_inherited": False,
            "umask_octal": "0077",
        },
        "execution_environment": {
            "executable_link_counts": PINNED_EXECUTABLE_LINK_COUNTS,
            "executable_sha256": PINNED_EXECUTABLE_SHA256,
            "executable_size_bytes": PINNED_EXECUTABLE_SIZE_BYTES,
            "git_executable": os.fspath(PINNED_GIT),
            "lake_executable": os.fspath(lake),
            "lean_bin_directory": os.fspath(lean_bin),
            "leanchecker_executable": os.fspath(leanchecker),
            "lean_executable": os.fspath(lean),
            "python_executable": os.fspath(python),
            "repo_root_observed": os.fspath(root),
        },
        "execution_window": {
            "end_utc": records[-1]["end_utc"],
            "start_utc": records[0]["start_utc"],
        },
        "historical_preservation_sha256": freeze.PRESERVED_HISTORICAL_HASHES,
        "prior_replay_preservation_sha256": freeze.PRESERVED_PRIOR_REPLAY_HASHES,
        "prior_replay_schema": freeze.PRESERVED_PRIOR_REPLAY_SCHEMAS,
        "lake_identity": freeze.EXPECTED_LAKE_IDENTITY,
        "lake_version_line": lake_line,
        "lake_version_stderr": stream(b""),
        "lean_identity": freeze.EXPECTED_LEAN_IDENTITY,
        "lean_version_line": lean_line,
        "lean_version_stderr": stream(b""),
        "official_archive": freeze.EXPECTED_ARCHIVE,
        "official_archive_observation": archive_observation,
        "operational_wiring_sha256": freeze.EXPECTED_OPERATIONAL_WIRING_HASHES,
        "package_pins": packages,
        "provider_observations": freeze.EXPECTED_PROVIDER_OBSERVATIONS,
        "python_optimization_parity": {"all_equal": True, "pairs": parity},
        "replay_custody_gate_sha256": {
            path: custody_after[path].sha256
            for path in freeze.EXPECTED_CUSTODY_GATE_PATHS
        },
        "schema": "pid-rs/lean-current-project-replay/v2",
        "scope_boundary": [
            "Archive digest equality is an observed provider-byte relationship; it does not establish executed-tree-to-archive byte provenance or publisher authentication.",
            "This is not a reproducible build from the reported Lean source commit.",
            "Kernel replay is bounded evidence, not a proof of kernel soundness.",
            "The compatibility port is not a theorem of semantic equivalence between Lean releases.",
            "Exact-real theorem replay does not establish refinement to Rust or binary64 arithmetic.",
            "Pretty-printed derived declarations do not expose or compare generated helper proof bodies.",
            "This replay does not establish theorem intent, scientific validity, estimator validity, sampling claims, or application correctness; pre/post static endpoint equality is not an atomic snapshot.",
            "The zero-argument runner removes caller-controlled path authority but does not authenticate its pinned host-local executables.",
            "Stable executable snapshots immediately before launch and after replay do not prove the operating system executed those exact bytes atomically.",
            "Pinned executable leaf hashes do not bind dynamic-loader inputs, shared libraries, Python standard-library or extension modules, or the wider runtime closure.",
            "Per-command process-group cleanup is bounded best effort, not a sandbox or containment guarantee; escaped descendants and process-group identifier reuse are outside its claim.",
        ],
        "source_sha256": freeze.EXPECTED_SOURCE_HASHES,
        "status": "passed",
        "verification": {
            "bound_static_surface": {
                "atomic_snapshot_claimed": False,
                "custody_gate_endpoint_identity_equal": True,
                "custody_gate_files": 2,
                "post_commands": "passed",
                "pre_commands": "passed",
            },
            "clean_build": {
                "dependency_cache_reused": True,
                "project_oleans_reused": False,
                "status": "passed",
                "stdout_exact": freeze.EXPECTED_CLEAN_BUILD_STDOUT,
                "warnings": 0,
                "warnings_fail_build": True,
            },
            "direct_lean_t0": {
                "count": 11,
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
            "forbidden_placeholder_hits": 0,
            "imported_modules": 8,
            "leanchecker": {
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
            "named_source_theorems": 246,
            "permitted_axioms": ["Classical.choice", "Quot.sound", "propext"],
            "python_checker_pairs": len(freeze.PYTHON_COMMAND_PAIRS),
            "source_written_declarations": 339,
            "theorem_axiom_audit": {
                "named_theorems": 246,
                "stderr_empty": True,
                "stdout_empty": True,
                "status": "passed",
            },
        },
    }
    raw = (
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    publish_receipt_no_clobber(
        raw,
        output_parent_descriptor,
        output.parent,
        output_parent_identity,
        output_leaf,
        temporary_leaf,
    )
    print(
        f"wrote {output} ({len(raw)} bytes, sha256={hashlib.sha256(raw).hexdigest()})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
