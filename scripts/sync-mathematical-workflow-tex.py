#!/usr/bin/env python3
"""Synchronize the workflow's canonical Markdown enclosure without altering TeX framing."""

from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
import ctypes
import ctypes.util
from dataclasses import dataclass
import errno
import fcntl
import hashlib
import os
from pathlib import Path
import platform
import secrets
import stat
from typing import Iterator


ROOT = Path(__file__).resolve().parents[1]
MARKDOWN = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
TEX = ROOT / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
BEGIN_TOKEN = b"\\begin{markdown}"
END_TOKEN = b"\\end{markdown}"
BEGIN = BEGIN_TOKEN + b"\n"
END = END_TOKEN
CANONICAL_DATA_MODE = 0o644
READ_CHUNK_SIZE = 1024 * 1024
TEMPORARY_NAME_ATTEMPTS = 128


@dataclass(frozen=True)
class NodeIdentity:
    device: int
    inode: int
    mode: int
    owner: int
    group: int


@dataclass(frozen=True)
class FileIdentity:
    node: NodeIdentity
    links: int
    size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class FileSnapshot:
    identity: FileIdentity
    data: bytes


@dataclass(frozen=True)
class DirectoryEntry:
    parent_descriptor: int
    name: str
    identity: NodeIdentity
    label: str


@dataclass(frozen=True)
class AnchoredPaths:
    root_descriptor: int
    root_identity: NodeIdentity
    markdown_directory_descriptor: int
    markdown_name: str
    tex_directory_descriptor: int
    tex_name: str
    directory_entries: tuple[DirectoryEntry, ...]


def _node_identity(status: os.stat_result) -> NodeIdentity:
    return NodeIdentity(
        device=status.st_dev,
        inode=status.st_ino,
        mode=status.st_mode,
        owner=status.st_uid,
        group=status.st_gid,
    )


@contextmanager
def _publication_lock() -> Iterator[None]:
    """Hold the same advisory writer lock as the PDF publication pipeline."""

    lock_root = Path("/tmp").resolve(strict=True)
    root_digest = hashlib.sha256(os.fsencode(str(ROOT.resolve(strict=True)))).hexdigest()
    lock_path = (
        lock_root
        / f"pid-rs-mathematical-workflow-{os.getuid()}-{root_digest}.lock"
    )
    descriptor = os.open(
        lock_path,
        os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
        0o600,
    )
    try:
        named = lock_path.lstat()
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(named.st_mode)
            or not stat.S_ISREG(opened.st_mode)
            or (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino)
            or named.st_nlink != 1
            or opened.st_nlink != 1
            or named.st_uid != os.getuid()
            or opened.st_uid != os.getuid()
            or stat.S_IMODE(named.st_mode) != 0o600
            or stat.S_IMODE(opened.st_mode) != 0o600
        ):
            raise RuntimeError("publication lock has an unsafe identity or mode")
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        named_after = lock_path.lstat()
        opened_after = os.fstat(descriptor)
        if (named_after.st_dev, named_after.st_ino) != (
            opened_after.st_dev,
            opened_after.st_ino,
        ):
            raise RuntimeError("publication lock path changed during acquisition")
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _file_identity(status: os.stat_result) -> FileIdentity:
    return FileIdentity(
        node=_node_identity(status),
        links=status.st_nlink,
        size=status.st_size,
        modified_ns=status.st_mtime_ns,
        changed_ns=status.st_ctime_ns,
    )


def _require_primitives() -> None:
    missing = [
        name
        for name in ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
        if not hasattr(os, name)
    ]
    if os.name != "posix" or missing:
        detail = f"; missing {', '.join(missing)}" if missing else ""
        raise RuntimeError(f"required POSIX no-follow primitives are unavailable{detail}")
    if os.open not in os.supports_dir_fd or os.stat not in os.supports_dir_fd:
        raise RuntimeError("required descriptor-relative open/stat operations are unavailable")
    if os.stat not in os.supports_follow_symlinks or os.unlink not in os.supports_dir_fd:
        raise RuntimeError("required no-follow stat/unlink operations are unavailable")


def _validate_component(name: str, label: str) -> None:
    if not name or name in (".", "..") or os.sep in name:
        raise RuntimeError(f"unsafe {label} path component: {name!r}")
    if os.altsep is not None and os.altsep in name:
        raise RuntimeError(f"unsafe {label} path component: {name!r}")


def _relative_parts(path: Path, label: str) -> tuple[str, ...]:
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError(f"{label} is outside the repository root") from error
    parts = relative.parts
    if not parts:
        raise RuntimeError(f"{label} must name a file below the repository root")
    for part in parts:
        _validate_component(part, label)
    return parts


def _validate_directory(status: os.stat_result, label: str) -> None:
    if not stat.S_ISDIR(status.st_mode):
        raise RuntimeError(f"not a directory: {label}")


def _validate_regular(
    status: os.stat_result,
    label: str,
    *,
    expected_mode: int | None,
) -> None:
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        raise RuntimeError(f"not a single-link regular file: {label}")
    if expected_mode is not None and stat.S_IMODE(status.st_mode) != expected_mode:
        raise RuntimeError(
            f"noncanonical mode for {label}: "
            f"{stat.S_IMODE(status.st_mode):04o}, expected {expected_mode:04o}"
        )


def _open_root_directory() -> tuple[int, NodeIdentity]:
    before = ROOT.lstat()
    _validate_directory(before, str(ROOT))
    descriptor = os.open(
        ROOT,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        opened = os.fstat(descriptor)
        _validate_directory(opened, str(ROOT))
        if _node_identity(opened) != _node_identity(before):
            raise RuntimeError(f"repository root changed during open: {ROOT}")
        after = ROOT.lstat()
        if _node_identity(after) != _node_identity(opened):
            raise RuntimeError(f"repository root changed during open: {ROOT}")
        return descriptor, _node_identity(opened)
    except BaseException:
        os.close(descriptor)
        raise


def _open_directory_at(
    parent_descriptor: int,
    name: str,
    label: str,
) -> tuple[int, NodeIdentity]:
    _validate_component(name, label)
    before = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    _validate_directory(before, label)
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=parent_descriptor,
    )
    try:
        opened = os.fstat(descriptor)
        _validate_directory(opened, label)
        if _node_identity(opened) != _node_identity(before):
            raise RuntimeError(f"directory changed during open: {label}")
        after = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if _node_identity(after) != _node_identity(opened):
            raise RuntimeError(f"directory changed during open: {label}")
        return descriptor, _node_identity(opened)
    except BaseException:
        os.close(descriptor)
        raise


def _open_parent_chain(
    stack: ExitStack,
    root_descriptor: int,
    components: tuple[str, ...],
    label: str,
) -> tuple[int, list[DirectoryEntry]]:
    descriptor = root_descriptor
    entries: list[DirectoryEntry] = []
    traversed: list[str] = []
    for component in components:
        traversed.append(component)
        component_label = f"{label} parent {'/'.join(traversed)}"
        child, identity = _open_directory_at(descriptor, component, component_label)
        stack.callback(os.close, child)
        entries.append(DirectoryEntry(descriptor, component, identity, component_label))
        descriptor = child
    return descriptor, entries


@contextmanager
def _anchored_paths() -> Iterator[AnchoredPaths]:
    markdown_parts = _relative_parts(MARKDOWN, "Markdown source")
    tex_parts = _relative_parts(TEX, "TeX destination")
    with ExitStack() as stack:
        root_descriptor, root_identity = _open_root_directory()
        stack.callback(os.close, root_descriptor)
        markdown_directory, markdown_entries = _open_parent_chain(
            stack,
            root_descriptor,
            markdown_parts[:-1],
            "Markdown source",
        )
        tex_directory, tex_entries = _open_parent_chain(
            stack,
            root_descriptor,
            tex_parts[:-1],
            "TeX destination",
        )
        yield AnchoredPaths(
            root_descriptor=root_descriptor,
            root_identity=root_identity,
            markdown_directory_descriptor=markdown_directory,
            markdown_name=markdown_parts[-1],
            tex_directory_descriptor=tex_directory,
            tex_name=tex_parts[-1],
            directory_entries=tuple(markdown_entries + tex_entries),
        )


def _read_exact(descriptor: int, size: int, label: str) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        try:
            chunk = os.read(descriptor, min(remaining, READ_CHUNK_SIZE))
        except InterruptedError:
            continue
        if not chunk:
            raise RuntimeError(f"file became shorter during read: {label}")
        chunks.append(chunk)
        remaining -= len(chunk)
    while True:
        try:
            extra = os.read(descriptor, 1)
            break
        except InterruptedError:
            continue
    if extra:
        raise RuntimeError(f"file became longer during read: {label}")
    return b"".join(chunks)


def _read_single_link_regular_at(
    directory_descriptor: int,
    name: str,
    label: str,
    *,
    expected_mode: int = CANONICAL_DATA_MODE,
    fsync_file: bool = False,
) -> FileSnapshot:
    _validate_component(name, label)
    before = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    _validate_regular(before, label, expected_mode=expected_mode)
    descriptor = os.open(
        name,
        os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
        dir_fd=directory_descriptor,
    )
    try:
        opened = os.fstat(descriptor)
        _validate_regular(opened, label, expected_mode=expected_mode)
        if _file_identity(opened) != _file_identity(before):
            raise RuntimeError(f"file changed during open: {label}")
        data = _read_exact(descriptor, opened.st_size, label)
        if fsync_file:
            os.fsync(descriptor)
        after = os.fstat(descriptor)
        if _file_identity(after) != _file_identity(opened):
            raise RuntimeError(f"file changed during read: {label}")
        path_after = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
        _validate_regular(path_after, label, expected_mode=expected_mode)
        if _file_identity(path_after) != _file_identity(opened):
            raise RuntimeError(f"file path changed during read: {label}")
        return FileSnapshot(_file_identity(opened), data)
    finally:
        os.close(descriptor)


def _node_identity_at(directory_descriptor: int, name: str) -> NodeIdentity:
    _validate_component(name, "directory entry")
    return _node_identity(
        os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    )


def _verify_root_identity(expected: NodeIdentity) -> None:
    before = ROOT.lstat()
    _validate_directory(before, str(ROOT))
    if _node_identity(before) != expected:
        raise RuntimeError("repository root path identity changed")
    descriptor = os.open(
        ROOT,
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        if _node_identity(os.fstat(descriptor)) != expected:
            raise RuntimeError("repository root path identity changed during verification")
        after = ROOT.lstat()
        if _node_identity(after) != expected:
            raise RuntimeError("repository root path identity changed during verification")
    finally:
        os.close(descriptor)


def _verify_directory_entry(entry: DirectoryEntry) -> None:
    descriptor, identity = _open_directory_at(
        entry.parent_descriptor,
        entry.name,
        entry.label,
    )
    try:
        if identity != entry.identity:
            raise RuntimeError(f"directory path identity changed: {entry.label}")
    finally:
        os.close(descriptor)


def _verify_anchored_paths(paths: AnchoredPaths) -> None:
    _verify_root_identity(paths.root_identity)
    for entry in paths.directory_entries:
        _verify_directory_entry(entry)


def _assert_snapshot_unchanged(
    directory_descriptor: int,
    name: str,
    baseline: FileSnapshot,
    label: str,
) -> FileSnapshot:
    current = _read_single_link_regular_at(directory_descriptor, name, label)
    if current != baseline:
        raise RuntimeError(f"{label} identity or bytes changed during synchronization")
    return current


def synchronized_bytes(markdown: bytes, tex: bytes) -> bytes:
    for label, data in (("Markdown", markdown), ("TeX", tex)):
        if b"\r" in data:
            raise RuntimeError(f"{label} contains a carriage return")
        data.decode("utf-8")
    if not markdown.endswith(b"\n") or markdown.endswith(b"\n\n"):
        raise RuntimeError("Markdown must end with exactly one newline")
    if BEGIN_TOKEN in markdown or END_TOKEN in markdown:
        raise RuntimeError("Markdown contains a reserved TeX enclosure sentinel")
    if tex.count(BEGIN_TOKEN) != 1 or tex.count(END_TOKEN) != 1:
        raise RuntimeError("TeX must contain exactly one canonical Markdown enclosure")
    begin = tex.find(BEGIN)
    end = tex.find(END)
    content_start = begin + len(BEGIN)
    if begin < 0 or end < content_start:
        raise RuntimeError("TeX canonical Markdown enclosure sentinels are out of order")
    return tex[:content_start] + markdown + tex[end:]


def _create_temporary(
    directory_descriptor: int,
    destination_name: str,
) -> tuple[int, str, NodeIdentity]:
    for _ in range(TEMPORARY_NAME_ATTEMPTS):
        name = f".{destination_name}.tmp-{secrets.token_hex(16)}"
        try:
            descriptor = os.open(
                name,
                os.O_RDWR
                | os.O_CREAT
                | os.O_EXCL
                | os.O_NOFOLLOW
                | os.O_CLOEXEC,
                0o600,
                dir_fd=directory_descriptor,
            )
        except FileExistsError:
            continue
        identity: NodeIdentity | None = None
        try:
            opened = os.fstat(descriptor)
            identity = _node_identity(opened)
            _validate_regular(opened, "temporary TeX output", expected_mode=None)
            named = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
            _validate_regular(named, "temporary TeX output", expected_mode=None)
            if _file_identity(named) != _file_identity(opened):
                raise RuntimeError("temporary TeX output changed during creation")
            return descriptor, name, identity
        except BaseException:
            try:
                os.close(descriptor)
            finally:
                if identity is not None:
                    _cleanup_temporary(directory_descriptor, name, identity)
            raise
    raise RuntimeError("could not allocate a unique temporary TeX output")


def _write_all(descriptor: int, data: bytes) -> None:
    view = memoryview(data)
    offset = 0
    while offset < len(view):
        try:
            written = os.write(descriptor, view[offset:])
        except InterruptedError:
            continue
        if written <= 0:
            raise RuntimeError("short write to temporary TeX output")
        offset += written


def _atomic_exchange_at(directory_descriptor: int, left: str, right: str) -> None:
    """Atomically exchange two directory entries without following either leaf."""

    _validate_component(left, "exchange source")
    _validate_component(right, "exchange destination")
    system = platform.system()
    library = ctypes.CDLL(ctypes.util.find_library("c") or None, use_errno=True)
    if system == "Darwin":
        function = library.renameatx_np
        function.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        function.restype = ctypes.c_int
        result = function(
            directory_descriptor,
            os.fsencode(left),
            directory_descriptor,
            os.fsencode(right),
            0x00000002,  # RENAME_SWAP
        )
    elif system == "Linux":
        function = library.renameat2
        function.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        function.restype = ctypes.c_int
        result = function(
            directory_descriptor,
            os.fsencode(left),
            directory_descriptor,
            os.fsencode(right),
            0x00000002,  # RENAME_EXCHANGE
        )
    else:
        raise RuntimeError(f"atomic exchange is unsupported on {system}")
    if result != 0:
        error_number = ctypes.get_errno()
        raise OSError(error_number, os.strerror(error_number), f"{left} <-> {right}")


def _prepare_temporary(
    directory_descriptor: int,
    name: str,
    descriptor: int,
    expected: bytes,
) -> FileSnapshot:
    os.fchmod(descriptor, CANONICAL_DATA_MODE)
    _write_all(descriptor, expected)
    os.fsync(descriptor)
    opened = os.fstat(descriptor)
    _validate_regular(
        opened,
        "temporary TeX output",
        expected_mode=CANONICAL_DATA_MODE,
    )
    snapshot = _read_single_link_regular_at(
        directory_descriptor,
        name,
        "temporary TeX output",
    )
    if snapshot.data != expected or snapshot.identity.node != _node_identity(opened):
        raise RuntimeError("temporary TeX output failed byte-for-byte read-back")
    return snapshot


def _verify_installed(
    paths: AnchoredPaths,
    expected: bytes,
    temporary_snapshot: FileSnapshot,
) -> FileSnapshot:
    installed = _read_single_link_regular_at(
        paths.tex_directory_descriptor,
        paths.tex_name,
        "installed TeX destination",
        fsync_file=True,
    )
    if installed.data != expected:
        raise RuntimeError("installed TeX destination failed byte-for-byte read-back")
    if installed.identity.node != temporary_snapshot.identity.node:
        raise RuntimeError("installed TeX destination is not the prepared temporary file")
    return installed


def _cleanup_temporary(
    directory_descriptor: int,
    name: str,
    identity: NodeIdentity,
) -> None:
    try:
        current = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return
    if (
        _node_identity(current).device != identity.device
        or _node_identity(current).inode != identity.inode
        or not stat.S_ISREG(current.st_mode)
        or current.st_nlink != 1
    ):
        raise RuntimeError("temporary TeX path changed; refusing ambiguous cleanup")
    os.unlink(name, dir_fd=directory_descriptor)
    os.fsync(directory_descriptor)


def _synchronize(*, check: bool) -> int:
    _require_primitives()
    with _publication_lock(), _anchored_paths() as paths:
        markdown = _read_single_link_regular_at(
            paths.markdown_directory_descriptor,
            paths.markdown_name,
            "Markdown source",
        )
        tex = _read_single_link_regular_at(
            paths.tex_directory_descriptor,
            paths.tex_name,
            "TeX destination",
        )
        expected = synchronized_bytes(markdown.data, tex.data)
        if expected == tex.data:
            _verify_anchored_paths(paths)
            _assert_snapshot_unchanged(
                paths.markdown_directory_descriptor,
                paths.markdown_name,
                markdown,
                "Markdown source",
            )
            _assert_snapshot_unchanged(
                paths.tex_directory_descriptor,
                paths.tex_name,
                tex,
                "TeX destination",
            )
            print("OK: workflow TeX embeds the canonical Markdown byte-for-byte")
            return 0
        if check:
            raise RuntimeError("workflow TeX contains a stale canonical Markdown enclosure")

        temporary_descriptor, temporary_name, temporary_identity = _create_temporary(
            paths.tex_directory_descriptor,
            paths.tex_name,
        )
        cleanup_identity = temporary_identity
        preserve_temporary = False
        exchanged = False
        try:
            try:
                temporary_snapshot = _prepare_temporary(
                    paths.tex_directory_descriptor,
                    temporary_name,
                    temporary_descriptor,
                    expected,
                )
                if (
                    temporary_snapshot.identity.node.owner != tex.identity.node.owner
                    or temporary_snapshot.identity.node.group != tex.identity.node.group
                ):
                    raise RuntimeError("temporary TeX output ownership differs from destination")
                _verify_anchored_paths(paths)
                _assert_snapshot_unchanged(
                    paths.markdown_directory_descriptor,
                    paths.markdown_name,
                    markdown,
                    "Markdown source",
                )
                _assert_snapshot_unchanged(
                    paths.tex_directory_descriptor,
                    temporary_name,
                    temporary_snapshot,
                    "temporary TeX output",
                )
                _assert_snapshot_unchanged(
                    paths.tex_directory_descriptor,
                    paths.tex_name,
                    tex,
                    "TeX destination",
                )
                # Atomic exchange is the compare-and-swap primitive: after it, the temporary name
                # must contain the exact baseline destination.  A writer that wins the final
                # pre-exchange race is detected and restored rather than overwritten.
                _atomic_exchange_at(
                    paths.tex_directory_descriptor,
                    temporary_name,
                    paths.tex_name,
                )
                exchanged = True
                cleanup_identity = tex.identity.node
                displaced_node = _node_identity_at(
                    paths.tex_directory_descriptor,
                    temporary_name,
                )
                displaced_error: BaseException | None = None
                try:
                    displaced = _read_single_link_regular_at(
                        paths.tex_directory_descriptor,
                        temporary_name,
                        "atomically displaced TeX destination",
                    )
                except BaseException as error:
                    displaced = None
                    displaced_error = error
                if (
                    displaced_error is not None
                    or displaced is None
                    or displaced.data != tex.data
                    or displaced.identity.node != tex.identity.node
                ):
                    # Restore the exact displaced directory entry before trying to interpret it.
                    # A final-window writer may have installed a symlink or multiply linked file;
                    # requiring regular-file parsing first would strand that node at the random
                    # temporary name and leave our prepared bytes at the public destination.
                    try:
                        _atomic_exchange_at(
                            paths.tex_directory_descriptor,
                            temporary_name,
                            paths.tex_name,
                        )
                        os.fsync(paths.tex_directory_descriptor)
                        restored_node = _node_identity_at(
                            paths.tex_directory_descriptor,
                            paths.tex_name,
                        )
                        if (restored_node.device, restored_node.inode) != (
                            displaced_node.device,
                            displaced_node.inode,
                        ):
                            raise RuntimeError(
                                "restored final-window TeX node identity differs"
                            )
                    except BaseException as restore_error:
                        preserve_temporary = True
                        raise RuntimeError(
                            "TeX destination changed in the final compare-and-swap window and "
                            f"immediate restoration failed ({restore_error})"
                        ) from displaced_error
                    exchanged = False
                    cleanup_identity = temporary_identity
                    raise RuntimeError(
                        "TeX destination changed in the final compare-and-swap window"
                    ) from displaced_error
                installed = _verify_installed(paths, expected, temporary_snapshot)
                os.fsync(temporary_descriptor)
                os.fsync(paths.tex_directory_descriptor)

                _verify_anchored_paths(paths)
                _assert_snapshot_unchanged(
                    paths.markdown_directory_descriptor,
                    paths.markdown_name,
                    markdown,
                    "Markdown source",
                )
                durable = _read_single_link_regular_at(
                    paths.tex_directory_descriptor,
                    paths.tex_name,
                    "durable TeX destination",
                    fsync_file=True,
                )
                if durable != installed or durable.data != expected:
                    raise RuntimeError("durable TeX destination changed after replacement")
            except BaseException as synchronization_error:
                if exchanged:
                    # The temporary name holds the displaced pre-install node.  Preserve it on
                    # every exceptional path until a verified reverse exchange completes.
                    preserve_temporary = True
                    try:
                        current_destination = _read_single_link_regular_at(
                            paths.tex_directory_descriptor,
                            paths.tex_name,
                            "rollback candidate TeX destination",
                        )
                        displaced_destination = _read_single_link_regular_at(
                            paths.tex_directory_descriptor,
                            temporary_name,
                            "rollback displaced TeX destination",
                        )
                        if current_destination.identity.node != temporary_snapshot.identity.node:
                            preserve_temporary = True
                            raise RuntimeError(
                                "installed TeX path changed after exchange; preserving the displaced "
                                f"file at {temporary_name!r} and refusing destructive rollback"
                            )
                        _atomic_exchange_at(
                            paths.tex_directory_descriptor,
                            temporary_name,
                            paths.tex_name,
                        )
                        exchanged = False
                        cleanup_identity = temporary_identity
                        restored = _read_single_link_regular_at(
                            paths.tex_directory_descriptor,
                            paths.tex_name,
                            "rolled-back TeX destination",
                        )
                        if (
                            restored.data != displaced_destination.data
                            or restored.identity.node != displaced_destination.identity.node
                        ):
                            raise RuntimeError("atomic TeX rollback read-back differs")
                        preserve_temporary = False
                    except BaseException as rollback_error:
                        recovery = (
                            f"; displaced file retained at {temporary_name!r}"
                            if preserve_temporary
                            else ""
                        )
                        raise RuntimeError(
                            f"synchronization failed ({synchronization_error}); "
                            f"rollback failed ({rollback_error}){recovery}"
                        ) from rollback_error
                raise
        finally:
            os.close(temporary_descriptor)
            if not preserve_temporary:
                _cleanup_temporary(
                    paths.tex_directory_descriptor,
                    temporary_name,
                    cleanup_identity,
                )
    print("UPDATED: workflow TeX now embeds the canonical Markdown byte-for-byte")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    return _synchronize(check=args.check)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, UnicodeError, RuntimeError) as error:
        if isinstance(error, OSError) and error.errno == errno.ELOOP:
            error = RuntimeError("refusing a symbolic link in the synchronization path")
        raise SystemExit(f"workflow TeX synchronizer: {error}") from error
