#!/usr/bin/env python3
"""Kernel-check descriptor factorization with digest-bound project inputs."""

from __future__ import annotations

import sys as _bootstrap_sys

if not (
    _bootstrap_sys.flags.isolated == 1
    and _bootstrap_sys.flags.safe_path
    and _bootstrap_sys.flags.no_site == 1
    and _bootstrap_sys.flags.ignore_environment == 1
):
    print(
        "ERROR: check-lean-descriptor-factorization.py requires Python -I -S",
        file=_bootstrap_sys.stderr,
    )
    raise SystemExit(2)
del _bootstrap_sys

from dataclasses import dataclass
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_PATH = Path(__file__)
SCRIPT_PATH = Path(os.path.abspath(os.fspath(SCRIPT_PATH)))
ROOT = SCRIPT_PATH.parent.parent
PROJECT = ROOT / "audit/formal/lean"
SOURCE = ROOT / "audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean"
EXPECTED_SOURCE_SHA256 = (
    "7e1e71d76d63137ae055f17b1b771fdd2eb01935c7210bca79142691f7f06034"
)
EXPECTED_MANIFEST_SHA256 = (
    "6527e482d9bdbcbf48bf47a420df1ccf9b99958ea0152693446816891cc910af"
)
EXPECTED_TOOLCHAIN_SHA256 = (
    "302cd63c54178885b89e669f33b38f12f4dd7ae7e5cac537b3203e3768d8fb2b"
)
EXPECTED_LAKEFILE_SHA256 = (
    "ec5def1f5f0aa36218f767993c144a1b76ed9b77d6a429028dd5bb8f857354e0"
)
EXPECTED_TOOLCHAIN = "leanprover/lean4:v4.33.0"
EXPECTED_LEAN_VERSION = "4.33.0"
EXPECTED_LEAN_COMMIT = "d8b18978322de05a8f3dba51ef03cf5461676c17"
EXPECTED_LEAN_BUILD = "Release"
THEOREMS = (
    "PidDescriptorFactorization.equal_descriptors_and_factorization_force_equal_atoms",
    "PidDescriptorFactorization.descriptor_collision_blocks_universal_reconstruction",
    "PidDescriptorFactorization.atom_distinction_refutes_descriptor_factorization",
)
PROHIBITED_SOURCE = re.compile(r"\b(sorry|admit|axiom|unsafe)\b")
LEAN_VERSION_LINE = re.compile(
    r"Lean \(version (?P<version>[0-9]+\.[0-9]+\.[0-9]+), "
    r"(?P<platform>[A-Za-z0-9_.+]+(?:-[A-Za-z0-9_.+]+){2,}), "
    r"commit (?P<commit>[0-9a-f]{40}), "
    r"(?P<build>[A-Za-z][A-Za-z0-9_.+-]*)\)"
)


class LeanDescriptorFactorizationError(RuntimeError):
    """The source, pinned environment, compilation, or axiom audit failed."""


@dataclass(frozen=True)
class LeanPortableIdentity:
    """Release fields reported by the selected Lean process."""

    version: str
    commit: str
    build: str

    def evidence(self) -> dict[str, str]:
        """Return the canonical machine-evidence projection."""

        return {
            "version": self.version,
            "commit": self.commit,
            "build": self.build,
        }


@dataclass(frozen=True)
class LeanExecutableObservation:
    """One fully parsed Lean version observation, including its host platform."""

    portable_identity: LeanPortableIdentity
    platform: str


@dataclass(frozen=True)
class FileIdentity:
    """Metadata used to detect replacement or mutation around a bounded read."""

    device: int
    inode: int
    mode: int
    links: int
    size: int
    modified_ns: int
    changed_ns: int


@dataclass(frozen=True)
class DirectoryIdentity:
    """Directory object identity without unrelated directory-content metadata."""

    device: int
    inode: int
    mode: int


@dataclass(frozen=True)
class PathComponentIdentity:
    """One lexical parent-directory identity observed without following links."""

    path: Path
    identity: DirectoryIdentity


@dataclass(frozen=True)
class StableFileSnapshot:
    """Exact bytes plus leaf and lexical-parent identities from one bounded read."""

    role: str
    path: Path
    raw: bytes
    identity: FileIdentity
    parent_identities: tuple[PathComponentIdentity, ...]
    single_link_required: bool

    @property
    def sha256(self) -> str:
        """Hash the exact bytes already read, without reopening the path."""

        return hashlib.sha256(self.raw).hexdigest()

    def utf8(self) -> str:
        """Decode the exact snapshotted bytes as strict UTF-8."""

        try:
            return self.raw.decode("utf-8")
        except UnicodeDecodeError as error:
            raise LeanDescriptorFactorizationError(
                f"{self.role} is not valid UTF-8"
            ) from error


@dataclass(frozen=True)
class VerifiedInputs:
    """Digest-bound inputs, private tracked configuration, and Lean observation."""

    lake: str
    lake_target: Path
    execution_project: Path
    execution_project_identity: DirectoryIdentity
    query_directory_identity: DirectoryIdentity
    environment: tuple[tuple[str, str], ...]
    source_text: str
    lean_observation: LeanExecutableObservation
    snapshots: tuple[StableFileSnapshot, ...]
    materialized_snapshots: tuple[StableFileSnapshot, ...]
    dependency_packages: Path
    dependency_packages_identity: FileIdentity


EXPECTED_LEAN_IDENTITY = LeanPortableIdentity(
    version=EXPECTED_LEAN_VERSION,
    commit=EXPECTED_LEAN_COMMIT,
    build=EXPECTED_LEAN_BUILD,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LeanDescriptorFactorizationError(message)


def _file_identity(metadata: os.stat_result) -> FileIdentity:
    return FileIdentity(
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        links=metadata.st_nlink,
        size=metadata.st_size,
        modified_ns=metadata.st_mtime_ns,
        changed_ns=metadata.st_ctime_ns,
    )


def _directory_identity(
    metadata: os.stat_result,
) -> DirectoryIdentity:
    return DirectoryIdentity(
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
    )


def _read_descriptor_bytes(descriptor: int) -> bytes:
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _absolute_lexical_path(path: Path) -> Path:
    """Return an absolute path without resolving any requested component."""

    return Path(os.path.abspath(os.fspath(path)))


def _inspect_parent_components(path: Path, role: str) -> tuple[
    PathComponentIdentity, ...
]:
    """Inspect every lexical parent and reject symbolic-link traversal."""

    identities: list[PathComponentIdentity] = []
    absolute = _absolute_lexical_path(path)
    parents = tuple(reversed(absolute.parents))
    for parent in parents:
        try:
            metadata = parent.lstat()
        except OSError as error:
            raise LeanDescriptorFactorizationError(
                f"cannot inspect a parent of {role}: {error}"
            ) from error
        require(
            not stat.S_ISLNK(metadata.st_mode),
            f"{role} must not be reached through a symbolic-link parent",
        )
        require(
            stat.S_ISDIR(metadata.st_mode),
            f"{role} has a non-directory parent component",
        )
        identities.append(
            PathComponentIdentity(
                path=parent,
                identity=_directory_identity(metadata),
            )
        )
    return tuple(identities)


def _descriptor_walk_available() -> bool:
    """Return whether Python exposes the required POSIX openat-style primitives."""

    return (
        os.name == "posix"
        and os.open in os.supports_dir_fd
        and os.stat in os.supports_dir_fd
        and os.stat in os.supports_follow_symlinks
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "fchdir")
    )


def _open_regular_via_parent_descriptor(
    path: Path, role: str
) -> tuple[int, os.stat_result, tuple[PathComponentIdentity, ...]]:
    """Open a leaf relative to verified directory descriptors on POSIX."""

    absolute = _absolute_lexical_path(path)
    parts = absolute.parts
    require(
        bool(absolute.anchor) and len(parts) >= 2,
        f"{role} does not identify a regular-file leaf",
    )
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    current = -1
    identities: list[PathComponentIdentity] = []
    try:
        current = os.open(absolute.anchor, directory_flags)
        root_metadata = os.fstat(current)
        require(
            stat.S_ISDIR(root_metadata.st_mode),
            f"{role} filesystem anchor is not a directory",
        )
        current_path = Path(absolute.anchor)
        identities.append(
            PathComponentIdentity(
                path=current_path,
                identity=_directory_identity(root_metadata),
            )
        )
        parent_components = parts[1:-1]
        for component in parent_components:
            before = os.stat(component, dir_fd=current, follow_symlinks=False)
            require(
                not stat.S_ISLNK(before.st_mode) and stat.S_ISDIR(before.st_mode),
                f"{role} must not traverse a symbolic-link or non-directory parent",
            )
            child = os.open(component, directory_flags, dir_fd=current)
            try:
                child_metadata = os.fstat(child)
                after = os.stat(component, dir_fd=current, follow_symlinks=False)
                require(
                    _directory_identity(before)
                    == _directory_identity(child_metadata)
                    == _directory_identity(after),
                    f"{role} parent identity changed during descriptor traversal",
                )
            except BaseException:
                os.close(child)
                raise
            os.close(current)
            current = child
            current_path /= component
            identities.append(
                PathComponentIdentity(
                    path=current_path,
                    identity=_directory_identity(child_metadata),
                )
            )

        leaf = parts[-1]
        leaf_before = os.stat(leaf, dir_fd=current, follow_symlinks=False)
        require(
            not stat.S_ISLNK(leaf_before.st_mode)
            and stat.S_ISREG(leaf_before.st_mode),
            f"{role} must be a regular, non-symbolic-link file",
        )
        flags = (
            os.O_RDONLY
            | os.O_NOFOLLOW
            | getattr(os, "O_BINARY", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(leaf, flags, dir_fd=current)
        try:
            leaf_after = os.stat(leaf, dir_fd=current, follow_symlinks=False)
            require(
                _file_identity(leaf_before) == _file_identity(leaf_after),
                f"{role} leaf identity changed while opening by parent descriptor",
            )
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor, leaf_before, tuple(identities)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot open {role} through verified directory descriptors: {error}"
        ) from error
    finally:
        if current >= 0:
            os.close(current)


def _open_directory_via_parent_descriptor(
    path: Path, role: str
) -> tuple[int, DirectoryIdentity, tuple[PathComponentIdentity, ...]]:
    """Open one directory through verified lexical parent descriptors."""

    absolute = _absolute_lexical_path(path)
    parts = absolute.parts
    require(
        bool(absolute.anchor),
        f"{role} does not identify an absolute directory",
    )
    directory_flags = (
        os.O_RDONLY
        | os.O_DIRECTORY
        | os.O_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
    )
    current = -1
    identities: list[PathComponentIdentity] = []
    try:
        current = os.open(absolute.anchor, directory_flags)
        root_metadata = os.fstat(current)
        require(
            stat.S_ISDIR(root_metadata.st_mode),
            f"{role} filesystem anchor is not a directory",
        )
        current_path = Path(absolute.anchor)
        identities.append(
            PathComponentIdentity(
                path=current_path,
                identity=_directory_identity(root_metadata),
            )
        )
        for component in parts[1:]:
            before = os.stat(component, dir_fd=current, follow_symlinks=False)
            require(
                not stat.S_ISLNK(before.st_mode) and stat.S_ISDIR(before.st_mode),
                f"{role} must not traverse a symbolic-link or non-directory component",
            )
            child = os.open(component, directory_flags, dir_fd=current)
            try:
                child_metadata = os.fstat(child)
                after = os.stat(component, dir_fd=current, follow_symlinks=False)
                require(
                    _directory_identity(before)
                    == _directory_identity(child_metadata)
                    == _directory_identity(after),
                    f"{role} identity changed during descriptor traversal",
                )
            except BaseException:
                os.close(child)
                raise
            os.close(current)
            current = child
            current_path /= component
            identities.append(
                PathComponentIdentity(
                    path=current_path,
                    identity=_directory_identity(child_metadata),
                )
            )
        final_identity = _directory_identity(os.fstat(current))
        result = current
        current = -1
        return result, final_identity, tuple(identities)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot open {role} through verified directory descriptors: {error}"
        ) from error
    finally:
        if current >= 0:
            os.close(current)


def read_stable_regular_file(
    path: Path,
    role: str,
    *,
    require_single_link: bool = True,
) -> StableFileSnapshot:
    """Double-read one single-linked leaf and bind its lexical parent identities."""

    absolute = _absolute_lexical_path(path)
    require(
        _descriptor_walk_available(),
        f"{role} requires POSIX openat-style directory-descriptor custody",
    )
    parents_before = _inspect_parent_components(absolute, role)
    descriptor, path_before, walked_parents = _open_regular_via_parent_descriptor(
        absolute,
        role,
    )
    try:
        require(
            walked_parents == parents_before,
            f"{role} parent identities changed before descriptor traversal",
        )
        descriptor_before = os.fstat(descriptor)
        require(
            stat.S_ISREG(descriptor_before.st_mode),
            f"{role} open descriptor is not a regular file",
        )
        if require_single_link:
            require(
                descriptor_before.st_nlink == 1,
                f"{role} must have exactly one hard link",
            )
        first = _read_descriptor_bytes(descriptor)
        descriptor_middle = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        second = _read_descriptor_bytes(descriptor)
        descriptor_after = os.fstat(descriptor)
    finally:
        os.close(descriptor)

    try:
        path_after = absolute.lstat()
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot replay metadata for {role}: {error}"
        ) from error
    require(
        not stat.S_ISLNK(path_after.st_mode) and stat.S_ISREG(path_after.st_mode),
        f"{role} changed file type during snapshot",
    )
    identities = (
        _file_identity(path_before),
        _file_identity(descriptor_before),
        _file_identity(descriptor_middle),
        _file_identity(descriptor_after),
        _file_identity(path_after),
    )
    require(
        all(identity == identities[0] for identity in identities[1:]),
        f"{role} metadata or identity changed during snapshot",
    )
    require(first == second, f"{role} bytes changed during double-read snapshot")
    require(
        len(first) == identities[0].size,
        f"{role} byte length differs from snapshotted metadata",
    )
    parents_after = _inspect_parent_components(absolute, role)
    require(
        parents_after == parents_before,
        f"{role} parent identity changed during snapshot",
    )
    return StableFileSnapshot(
        role=role,
        path=absolute,
        raw=first,
        identity=identities[0],
        parent_identities=parents_before,
        single_link_required=require_single_link,
    )


def require_snapshot_unchanged(snapshot: StableFileSnapshot) -> None:
    """Replay one stable snapshot and reject byte or identity drift."""

    replay = read_stable_regular_file(
        snapshot.path,
        snapshot.role,
        require_single_link=snapshot.single_link_required,
    )
    require(
        replay.identity == snapshot.identity,
        f"{snapshot.role} identity changed after initial snapshot",
    )
    require(
        replay.raw == snapshot.raw,
        f"{snapshot.role} bytes changed after initial snapshot",
    )
    require(
        replay.parent_identities == snapshot.parent_identities,
        f"{snapshot.role} parent identity changed after initial snapshot",
    )


def parse_lean_version_probe(
    probe: subprocess.CompletedProcess[str],
) -> LeanExecutableObservation:
    """Parse and validate one complete `lean --version` process result."""

    require(
        probe.returncode == 0,
        f"Lean version probe exited unsuccessfully: {probe.returncode}",
    )
    require(
        probe.stderr == "",
        f"Lean version probe emitted unexpected stderr: {probe.stderr!r}",
    )
    require(
        probe.stdout.endswith("\n"),
        "Lean version probe stdout lacks its final newline",
    )
    line = probe.stdout[:-1]
    require(
        "\n" not in line and "\r" not in line,
        "Lean version probe did not emit exactly one line",
    )
    matched = LEAN_VERSION_LINE.fullmatch(line)
    require(matched is not None, f"unexpected Lean version output: {probe.stdout!r}")
    groups = matched.groupdict()
    identity = LeanPortableIdentity(
        version=groups["version"],
        commit=groups["commit"],
        build=groups["build"],
    )
    require(
        identity == EXPECTED_LEAN_IDENTITY,
        f"unexpected Lean portable identity: {identity!r}",
    )
    return LeanExecutableObservation(
        portable_identity=identity,
        platform=groups["platform"],
    )


def decode_raw_lean_process(
    probe: subprocess.CompletedProcess[bytes],
) -> subprocess.CompletedProcess[str]:
    """Reject and decode each exact process stream in stdout/stderr order."""

    require(
        isinstance(probe.stdout, bytes) and isinstance(probe.stderr, bytes),
        "Lean process capture did not return exact byte streams",
    )
    decoded: dict[str, str] = {}
    for stream_name, raw in (("stdout", probe.stdout), ("stderr", probe.stderr)):
        require(
            b"\r" not in raw,
            f"Lean process raw {stream_name} contains a carriage return",
        )
        try:
            decoded[stream_name] = raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise LeanDescriptorFactorizationError(
                f"Lean process raw {stream_name} is not strict UTF-8"
            ) from error
    return subprocess.CompletedProcess(
        args=probe.args,
        returncode=probe.returncode,
        stdout=decoded["stdout"],
        stderr=decoded["stderr"],
    )


def _write_exclusive_file(path: Path, raw: bytes, role: str) -> None:
    """Create one private regular file without following or replacing a path."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot materialize {role}: {error}"
        ) from error
    try:
        offset = 0
        while offset < len(raw):
            written = os.write(descriptor, raw[offset:])
            require(written > 0, f"short write while materializing {role}")
            offset += written
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_exclusive_file_in_directory(
    directory: Path,
    expected_directory_identity: DirectoryIdentity,
    filename: str,
    raw: bytes,
    role: str,
) -> None:
    """Create one finite-name file relative to an identity-bound directory."""

    require(
        bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.lean", filename)),
        f"{role} filename is not in the finite safe grammar",
    )
    descriptor, identity, _parents = _open_directory_via_parent_descriptor(
        directory,
        f"{role} directory",
    )
    try:
        require(
            identity == expected_directory_identity,
            f"{role} directory identity changed before materialization",
        )
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        try:
            leaf = os.open(filename, flags, 0o600, dir_fd=descriptor)
        except OSError as error:
            raise LeanDescriptorFactorizationError(
                f"cannot materialize {role}: {error}"
            ) from error
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(leaf, raw[offset:])
                require(written > 0, f"short write while materializing {role}")
                offset += written
            os.fsync(leaf)
        finally:
            os.close(leaf)
    finally:
        os.close(descriptor)


def _prepare_private_lean_project(
    directory: Path,
    tracked_project_snapshots: tuple[StableFileSnapshot, ...],
    *,
    dependency_packages: Path | None = None,
) -> tuple[
    Path,
    DirectoryIdentity,
    DirectoryIdentity,
    tuple[StableFileSnapshot, ...],
    Path,
    FileIdentity,
]:
    """Materialize exact tracked configuration and route only dependency packages."""

    require(
        len(tracked_project_snapshots) == 3,
        "private Lean project requires exactly three tracked configuration files",
    )
    require(
        tuple(snapshot.path.name for snapshot in tracked_project_snapshots)
        == ("lake-manifest.json", "lean-toolchain", "lakefile.toml"),
        "private Lean project tracked configuration order or basename changed",
    )
    execution_project = directory / "project"
    execution_project.mkdir(mode=0o700)
    targets: list[tuple[Path, StableFileSnapshot]] = []
    for snapshot in tracked_project_snapshots:
        target = execution_project / snapshot.path.name
        _write_exclusive_file(
            target,
            snapshot.raw,
            f"private {snapshot.role}",
        )
        targets.append((target, snapshot))
    lake_directory = execution_project / ".lake"
    lake_directory.mkdir(mode=0o700)
    (execution_project / "queries").mkdir(mode=0o700)
    materialized: list[StableFileSnapshot] = []
    for target, snapshot in targets:
        replay = read_stable_regular_file(target, f"private {snapshot.role}")
        require(
            replay.raw == snapshot.raw,
            f"private {snapshot.role} differs from digest-bound source bytes",
        )
        materialized.append(replay)

    if dependency_packages is None:
        dependency_packages = PROJECT / ".lake/packages"
    dependency_packages = _absolute_lexical_path(dependency_packages)
    try:
        dependency_metadata = dependency_packages.lstat()
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot inspect live Lake dependency packages: {error}"
        ) from error
    require(
        not stat.S_ISLNK(dependency_metadata.st_mode)
        and stat.S_ISDIR(dependency_metadata.st_mode),
        "live Lake dependency packages must be a non-symbolic-link directory",
    )
    routed_packages = lake_directory / "packages"
    try:
        routed_packages.symlink_to(dependency_packages, target_is_directory=True)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            "cannot route the live dependency-package cache into the private "
            f"Lean project: {error}"
        ) from error
    require(
        routed_packages.is_symlink()
        and Path(os.readlink(routed_packages)) == dependency_packages,
        "private Lean dependency-package route changed during creation",
    )
    execution_project_identity = _directory_identity(execution_project.lstat())
    query_directory_identity = _directory_identity(
        (execution_project / "queries").lstat()
    )
    return (
        execution_project,
        execution_project_identity,
        query_directory_identity,
        tuple(materialized),
        dependency_packages,
        _file_identity(dependency_metadata),
    )


def build_lean_environment(
    lake: str,
    *,
    ambient: dict[str, str] | None = None,
) -> tuple[tuple[str, str], ...]:
    """Remove Python/Lean/Lake/loader overrides and bound executable search."""

    source = dict(os.environ if ambient is None else ambient)
    forbidden_prefixes = (
        "DYLD_",
        "ELAN_",
        "LAKE_",
        "LD_",
        "LEAN_",
        "PYTHON",
    )
    environment = {
        key: value
        for key, value in source.items()
        if not key.upper().startswith(forbidden_prefixes)
    }
    lake_parent = str(Path(lake).parent)
    default_path = os.defpath
    environment.update(
        {
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": lake_parent + os.pathsep + default_path,
            "TZ": "UTC",
        }
    )
    return tuple(sorted(environment.items()))


def _run_lean_process(
    inputs: VerifiedInputs,
    arguments: list[str],
    *,
    timeout: int,
) -> subprocess.CompletedProcess[str]:
    """Run Lake from the pinned CWD and decode only exact raw byte streams."""

    descriptor, identity, _parents = _open_directory_via_parent_descriptor(
        inputs.execution_project,
        "private Lean execution project",
    )
    try:
        require(
            identity == inputs.execution_project_identity,
            "private Lean execution-project identity changed before launch",
        )

        def enter_private_project() -> None:
            os.fchdir(descriptor)

        raw_checked = subprocess.run(
            [inputs.lake, "env", "lean", *arguments],
            env=dict(inputs.environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=timeout,
            pass_fds=(descriptor,),
            preexec_fn=enter_private_project,
        )
    finally:
        os.close(descriptor)
    try:
        project_after = inputs.execution_project.lstat()
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot replay private Lean execution project: {error}"
        ) from error
    require(
        _directory_identity(project_after) == inputs.execution_project_identity,
        "private Lean execution-project identity changed during launch",
    )
    return decode_raw_lean_process(raw_checked)


def run_lean_text(
    inputs: VerifiedInputs,
    filename: str,
    source_text: str,
) -> subprocess.CompletedProcess[str]:
    """Submit private source under the settled-tree premise and replay its bytes."""

    require(
        bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*\.lean", filename)),
        "private Lean query filename is not in the finite safe grammar",
    )
    query_directory = inputs.execution_project / "queries"
    query_path = query_directory / filename
    query_raw = source_text.encode("utf-8")
    _write_exclusive_file_in_directory(
        query_directory,
        inputs.query_directory_identity,
        filename,
        query_raw,
        f"private Lean query {filename}",
    )
    query_snapshot = read_stable_regular_file(
        query_path,
        f"private Lean query {filename}",
    )
    require(
        query_snapshot.raw == query_raw,
        f"private Lean query {filename} differs from requested source bytes",
    )
    checked = _run_lean_process(
        inputs,
        [f"queries/{filename}"],
        timeout=180,
    )
    require_snapshot_unchanged(query_snapshot)
    return checked


def verify_environment_and_source(private_root: Path) -> VerifiedInputs:
    """Match frozen tracked bytes, privately materialize them, and observe Lean."""

    require(
        _descriptor_walk_available(),
        "full Lean kernel custody requires POSIX openat-style directory "
        "descriptors; POSIX no-kernel controls remain separately runnable",
    )
    initial_snapshots = (
        read_stable_regular_file(SOURCE, "Lean descriptor-factorization source"),
        read_stable_regular_file(
            PROJECT / "lake-manifest.json", "pinned Lake manifest"
        ),
        read_stable_regular_file(PROJECT / "lean-toolchain", "Lean toolchain file"),
        read_stable_regular_file(PROJECT / "lakefile.toml", "Lake configuration"),
        read_stable_regular_file(SCRIPT_PATH, "descriptor-factorization checker"),
    )
    expected_digests = (
        EXPECTED_SOURCE_SHA256,
        EXPECTED_MANIFEST_SHA256,
        EXPECTED_TOOLCHAIN_SHA256,
        EXPECTED_LAKEFILE_SHA256,
    )
    digest_messages = (
        "Lean descriptor-factorization source digest drifted",
        "pinned Lake manifest digest drifted",
        "Lean toolchain file digest drifted",
        "Lake configuration digest drifted",
    )
    for snapshot, expected, message in zip(
        initial_snapshots[:4], expected_digests, digest_messages, strict=True
    ):
        require(snapshot.sha256 == expected, message)

    toolchain_text = initial_snapshots[2].utf8()
    require(
        toolchain_text.strip() == EXPECTED_TOOLCHAIN,
        "Lean toolchain identifier drifted",
    )
    source_text = initial_snapshots[0].utf8()
    require(
        PROHIBITED_SOURCE.search(source_text) is None,
        "Lean source contains a prohibited proof escape",
    )

    selected_lake = shutil.which("lake")
    require(selected_lake is not None, "lake is not available")
    lake = str(_absolute_lexical_path(Path(selected_lake)))
    try:
        lake_target = Path(lake).resolve(strict=True)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot resolve the selected Lake launcher: {error}"
        ) from error
    lake_snapshot = read_stable_regular_file(
        lake_target,
        "selected Lake proxy target",
        require_single_link=False,
    )
    snapshots = (*initial_snapshots, lake_snapshot)
    (
        execution_project,
        execution_project_identity,
        query_directory_identity,
        materialized_snapshots,
        dependency_packages,
        dependency_packages_identity,
    ) = _prepare_private_lean_project(
        private_root,
        initial_snapshots[1:4],
    )
    environment = build_lean_environment(lake)
    provisional = VerifiedInputs(
        lake=lake,
        lake_target=lake_target,
        execution_project=execution_project,
        execution_project_identity=execution_project_identity,
        query_directory_identity=query_directory_identity,
        environment=environment,
        source_text=source_text,
        lean_observation=LeanExecutableObservation(
            portable_identity=EXPECTED_LEAN_IDENTITY,
            platform="provisional-before-version-probe",
        ),
        snapshots=snapshots,
        materialized_snapshots=materialized_snapshots,
        dependency_packages=dependency_packages,
        dependency_packages_identity=dependency_packages_identity,
    )
    version = _run_lean_process(provisional, ["--version"], timeout=60)
    observation = parse_lean_version_probe(version)
    return VerifiedInputs(
        lake=lake,
        lake_target=lake_target,
        execution_project=execution_project,
        execution_project_identity=execution_project_identity,
        query_directory_identity=query_directory_identity,
        environment=environment,
        source_text=source_text,
        lean_observation=observation,
        snapshots=snapshots,
        materialized_snapshots=materialized_snapshots,
        dependency_packages=dependency_packages,
        dependency_packages_identity=dependency_packages_identity,
    )


def verify_post_execution_custody(inputs: VerifiedInputs) -> None:
    """Recheck every input and the reported Lean identity after kernel execution."""

    replay = _run_lean_process(inputs, ["--version"], timeout=60)
    require(
        parse_lean_version_probe(replay) == inputs.lean_observation,
        "Lean executable observation changed after kernel execution",
    )
    for snapshot in inputs.snapshots:
        require_snapshot_unchanged(snapshot)
    for snapshot in inputs.materialized_snapshots:
        require_snapshot_unchanged(snapshot)
    dependency_metadata = inputs.dependency_packages.lstat()
    require(
        _file_identity(dependency_metadata) == inputs.dependency_packages_identity,
        "live dependency-package directory identity changed during kernel execution",
    )
    routed_packages = inputs.execution_project / ".lake/packages"
    require(
        routed_packages.is_symlink()
        and Path(os.readlink(routed_packages)) == inputs.dependency_packages,
        "private dependency-package route changed during kernel execution",
    )
    try:
        replay_target = Path(inputs.lake).resolve(strict=True)
    except OSError as error:
        raise LeanDescriptorFactorizationError(
            f"cannot replay the selected Lake proxy route: {error}"
        ) from error
    require(
        replay_target == inputs.lake_target,
        "selected Lake proxy route changed during kernel execution",
    )


def main() -> int:
    try:
        with tempfile.TemporaryDirectory(
            prefix="pid-descriptor-factorization-lean-"
        ) as directory:
            inputs = verify_environment_and_source(Path(directory).resolve())
            query = (
                inputs.source_text
                + "\n"
                + "\n".join(f"#print axioms {theorem}" for theorem in THEOREMS)
                + "\n"
            )
            checked = run_lean_text(
                inputs,
                "PidDescriptorFactorizationCheck.lean",
                query,
            )
            require(
                checked.returncode == 0,
                f"Lean kernel check failed: {checked.stderr}",
            )
            require(
                checked.stderr == "",
                f"Lean emitted unexpected stderr: {checked.stderr}",
            )
            expected_lines = [
                f"'{theorem}' does not depend on any axioms" for theorem in THEOREMS
            ]
            expected_stdout = "".join(f"{line}\n" for line in expected_lines)
            require(
                checked.stdout == expected_stdout,
                f"Lean theorem axiom inventory output changed: {checked.stdout!r}",
            )
            verify_post_execution_custody(inputs)

            result = {
                "schema": "pid-rs/lean-descriptor-factorization-check/v4",
                "status": "passed",
                "source_sha256": EXPECTED_SOURCE_SHA256,
                "checker_source_sha256": inputs.snapshots[4].sha256,
                "lake_manifest_sha256": EXPECTED_MANIFEST_SHA256,
                "lean_toolchain_sha256": EXPECTED_TOOLCHAIN_SHA256,
                "lakefile_sha256": EXPECTED_LAKEFILE_SHA256,
                "lean_toolchain": EXPECTED_TOOLCHAIN,
                "lean_executable_identity": (
                    inputs.lean_observation.portable_identity.evidence()
                ),
                "lean_platform_handling": ("parsed_and_validated_but_not_serialized"),
                "process_stream_transport": (
                    "stdout_then_stderr_each_reject_carriage_return_then_"
                    "strict_utf8_decode"
                ),
                "process_stdin_transport": "devnull_eof_no_parent_input",
                "input_snapshot_files_checked": len(inputs.snapshots),
                "input_snapshot_replays_unchanged": len(inputs.snapshots),
                "private_project_files_checked": len(inputs.materialized_snapshots),
                "private_project_replays_unchanged": len(
                    inputs.materialized_snapshots
                ),
                "private_query_files_checked": 1,
                "private_query_replays_unchanged": 1,
                "single_link_input_files_checked": len(inputs.snapshots) - 1,
                "launcher_target_files_observed": 1,
                "input_snapshot_method": (
                    "posix_component_descriptor_double_read_with_single_link_"
                    "tracked_inputs_and_separate_proxy_target_replay"
                ),
                "input_snapshot_boundary": (
                    "Frozen digests bind the theorem and three tracked project files "
                    "before use; Lake is launched with a descriptor-pinned private "
                    "POSIX working directory and finite relative query path. Component, "
                    "leaf, metadata, and byte endpoint checks reject unresolved "
                    "replacement, while descriptor pinning contains a private-project "
                    "pathname swap after launch preparation. It does not pin the "
                    "project's query-directory entry; the self-test retains a concrete "
                    "query-subtree swap/use/restore negative. Endpoint checks are not "
                    "an atomic history, so a settled query subtree and no concurrent "
                    "privileged or same-UID writer remain explicit premises. The "
                    "already-running script predates its first observation. Retained "
                    "HOME may influence selected launcher state, and dependency "
                    "package/cache contents remain live and unauthenticated. Regular "
                    "input bytes are accumulated without an explicit size ceiling."
                ),
                "lean_executable_identity_boundary": (
                    "The normalized version, source commit, and build flavor are "
                    "cross-platform release provenance only. The syntactically "
                    "validated host platform token is deliberately excluded from "
                    "reproducible evidence. Exact subprocess stdout and stderr are "
                    "captured as raw bytes, reject carriage returns, and decode as "
                    "strict UTF-8 before any version grammar is applied; child stdin "
                    "is /dev/null and cannot consume parent input. Captured stdout "
                    "and stderr have no explicit byte ceiling, and a timeout terminates "
                    "and waits for only the direct child rather than guaranteeing "
                    "descendant-process cleanup. The Lake proxy resolution plus terminal "
                    "target bytes and metadata are observed and replayed at bounded "
                    "endpoints; transient swap/restore remains possible. Neither Lake "
                    "nor Lean, the dynamic loader, libraries, or dependencies is "
                    "authenticated; no cross-platform kernel-equivalence theorem "
                    "follows."
                ),
                "theorems_kernel_checked": len(THEOREMS),
                "axioms": [],
                "boundary": (
                    "Generic descriptor-factorization logic only. The concrete "
                    "Lyu--Clark--Raviv descriptor collision and the nonfactorization "
                    "of SxPID are bound separately by exact-rational and Rust "
                    "witnesses; this check does not formalize SxPID."
                ),
            }
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (
        OSError,
        subprocess.SubprocessError,
        LeanDescriptorFactorizationError,
    ) as error:
        print(f"Lean descriptor-factorization check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
