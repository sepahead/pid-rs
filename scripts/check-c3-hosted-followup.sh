#!/usr/bin/env bash
set -euo pipefail

# Git checkout applies the invoking process's umask to worktree files.  The
# checker deliberately requires canonical 0644/0755 modes, so make the private
# fixture checkouts deterministic even when the caller uses a restrictive
# umask.  TemporaryDirectory still creates the containing scratch root 0700.
umask 022

readonly CHECKER_RELATIVE="scripts/check-c3-hosted-followup.py"
readonly SELF_TEST_RELATIVE="scripts/check-c3-hosted-followup-self-test.py"
readonly MAX_SOURCE_SIZE="262144"
readonly CHECKER_SIZE="150661"
readonly SELF_TEST_SIZE="261793"
readonly CHECKER_SHA256="379471aa2156a634846c59cbdc4c78ef3ff701238e0714f2710dcb9c0a521db0"
readonly SELF_TEST_SHA256="a169c038c0735c1da9f10fd0a990cfe3be79c716a34fe9db834348bcd79e4ec5"

if [[ "$#" -lt 2 ]]; then
  printf 'usage: %s {normal|optimized} {checker|self-test} [arguments...]\n' "$0" >&2
  exit 2
fi
readonly MODE="$1"
readonly TARGET="$2"
shift 2

case "$MODE" in
  normal)
    python_arguments=(-I -S -)
    ;;
  optimized)
    python_arguments=(-I -S -O -)
    ;;
  *)
    printf 'invalid follow-up Python mode: %s\n' "$MODE" >&2
    exit 2
    ;;
esac

case "$TARGET" in
  checker)
    readonly TARGET_RELATIVE="$CHECKER_RELATIVE"
    readonly TARGET_SIZE="$CHECKER_SIZE"
    readonly TARGET_SHA256="$CHECKER_SHA256"
    ;;
  self-test)
    readonly TARGET_RELATIVE="$SELF_TEST_RELATIVE"
    readonly TARGET_SIZE="$SELF_TEST_SIZE"
    readonly TARGET_SHA256="$SELF_TEST_SHA256"
    ;;
  *)
    printf 'invalid follow-up verifier target: %s\n' "$TARGET" >&2
    exit 2
    ;;
esac

case "${BASH_SOURCE[0]}" in
  */*) SCRIPT_PARENT="${BASH_SOURCE[0]%/*}" ;;
  *) SCRIPT_PARENT="." ;;
esac
readonly SCRIPT_PARENT
SCRIPT_DIRECTORY="$(CDPATH='' cd -- "$SCRIPT_PARENT" && pwd -P)"
readonly SCRIPT_DIRECTORY
REPOSITORY_ROOT="$(CDPATH='' cd -- "$SCRIPT_DIRECTORY/.." && pwd -P)"
readonly REPOSITORY_ROOT
PYTHON_EXECUTABLE="$(type -P python3)"
readonly PYTHON_EXECUTABLE
if [[ "$PYTHON_EXECUTABLE" != /* || ! -x "$PYTHON_EXECUTABLE" || -d "$PYTHON_EXECUTABLE" ]]; then
  printf 'an absolute executable python3 is unavailable\n' >&2
  exit 2
fi

"$PYTHON_EXECUTABLE" "${python_arguments[@]}" \
  "$REPOSITORY_ROOT" "$TARGET_RELATIVE" "$TARGET_SIZE" "$TARGET_SHA256" \
  "$MAX_SOURCE_SIZE" "$@" <<'PYTHON_BOOTSTRAP'
from __future__ import annotations

import hashlib
import os
import stat
import sys

if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path):
    raise SystemExit("exact-source bootstrap requires Python -I -S")
if len(sys.argv) < 6:
    raise SystemExit("exact-source bootstrap arguments are incomplete")

(
    root,
    relative,
    expected_size_raw,
    expected_sha256,
    maximum_size_raw,
    *target_arguments,
) = sys.argv[1:]
try:
    expected_size = int(expected_size_raw, 10)
    maximum_size = int(maximum_size_raw, 10)
except ValueError:
    raise SystemExit("exact-source bootstrap size is not canonical decimal") from None
parts = relative.split("/")
if (
    not os.path.isabs(root)
    or os.path.normpath(root) != root
    or not relative
    or relative.startswith("/")
    or any(part in {"", ".", ".."} for part in parts)
    or str(expected_size) != expected_size_raw
    or str(maximum_size) != maximum_size_raw
    or expected_size <= 0
    or maximum_size != 262_144
    or expected_size > maximum_size
    or len(expected_sha256) != 64
    or any(character not in "0123456789abcdef" for character in expected_sha256)
):
    raise SystemExit("exact-source bootstrap path, size, or digest is invalid")
if not all(
    hasattr(os, name)
    for name in ("O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
):
    raise SystemExit("exact-source bootstrap requires POSIX no-follow descriptors")

def read_declared(file_descriptor: int, declared_size: int) -> bytes:
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = declared_size
    while remaining:
        chunk = os.read(file_descriptor, min(64 * 1024, remaining))
        if not chunk:
            raise RuntimeError("exact-source leaf is shorter than its declared size")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(file_descriptor, 1):
        raise RuntimeError("exact-source leaf exceeds its declared size")
    return b"".join(chunks)


def compare_declared(
    file_descriptor: int,
    reference: bytes,
) -> bool:
    os.lseek(file_descriptor, 0, os.SEEK_SET)
    offset = 0
    while offset < len(reference):
        chunk = os.read(file_descriptor, min(64 * 1024, len(reference) - offset))
        if not chunk or chunk != reference[offset : offset + len(chunk)]:
            return False
        offset += len(chunk)
    return not os.read(file_descriptor, 1)


def leaf_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
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
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
    )


directory_flags = (
    os.O_RDONLY
    | os.O_DIRECTORY
    | os.O_NOFOLLOW
    | getattr(os, "O_CLOEXEC", 0)
)
leaf_flags = (
    os.O_RDONLY
    | os.O_NOFOLLOW
    | getattr(os, "O_CLOEXEC", 0)
    | os.O_NONBLOCK
)
root_components = tuple(component for component in root.split("/") if component)
if any(component in {".", ".."} for component in root_components):
    raise SystemExit("exact-source bootstrap root is not canonical")
walk_components = (*root_components, *parts[:-1])

def retain_close_error(primary, secondary):
    if primary is None:
        return secondary
    try:
        primary.add_note("additional exact-source descriptor close failed")
    except BaseException:
        pass
    return primary


def close_one(descriptor, primary):
    if descriptor is None:
        return primary
    try:
        os.close(descriptor)
    except BaseException as error:
        return retain_close_error(primary, error)
    return primary


def close_many(descriptors, primary):
    for descriptor in reversed(descriptors):
        primary = close_one(descriptor, primary)
    return primary


directory_descriptors = []
directory_identities = []
pending_directory = None
leaf = None
primary_error = None
try:
    pending_directory = os.open("/", directory_flags)
    root_identity = directory_identity(os.fstat(pending_directory))
    directory_descriptors.append(pending_directory)
    pending_directory = None
    directory_identities.append(root_identity)
    for component in walk_components:
        pending_directory = os.open(
            component,
            directory_flags,
            dir_fd=directory_descriptors[-1],
        )
        pending_identity = directory_identity(os.fstat(pending_directory))
        directory_descriptors.append(pending_directory)
        pending_directory = None
        directory_identities.append(pending_identity)
    leaf = os.open(parts[-1], leaf_flags, dir_fd=directory_descriptors[-1])
    before = os.fstat(leaf)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise RuntimeError("exact-source leaf is not a single-linked regular file")
    if stat.S_IMODE(before.st_mode) not in {0o644, 0o755}:
        raise RuntimeError("exact-source leaf has noncanonical permissions")
    if before.st_size != expected_size or before.st_size > maximum_size:
        raise RuntimeError("exact-source leaf size differs from its frozen bound")
    first = read_declared(leaf, expected_size)
    middle = os.fstat(leaf)
    second_matches = compare_declared(leaf, first)
    after = os.fstat(leaf)
    if (
        leaf_identity(before) != leaf_identity(middle)
        or leaf_identity(middle) != leaf_identity(after)
        or not second_matches
    ):
        raise RuntimeError("exact-source leaf changed during capture")
    if hashlib.sha256(first).hexdigest() != expected_sha256:
        raise RuntimeError("exact-source leaf digest mismatch")
    source_name = os.path.join(root, relative)
    code = compile(
        first,
        source_name,
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    namespace = {
        "__builtins__": __builtins__,
        "__cached__": None,
        "__file__": source_name,
        "__loader__": None,
        "__name__": "__main__",
        "__package__": None,
        "__pid_rs_exact_source_context__": {
            "optimize": sys.flags.optimize,
            "relative": relative,
            "sha256": expected_sha256,
            "size": expected_size,
        },
        "__spec__": None,
    }
    sys.argv = [source_name, *target_arguments]
    pending = None
    try:
        exec(code, namespace, namespace)
    except BaseException:
        pending = sys.exc_info()
    endpoint_before = os.fstat(leaf)
    endpoint_matches = compare_declared(leaf, first)
    endpoint_after = os.fstat(leaf)
    if (
        leaf_identity(endpoint_before) != leaf_identity(after)
        or leaf_identity(endpoint_after) != leaf_identity(after)
        or not endpoint_matches
    ):
        raise RuntimeError("exact-source leaf changed before execution returned")
    fresh_descriptors = []
    pending_fresh_directory = None
    endpoint_leaf = None
    fresh_primary_error = None
    try:
        pending_fresh_directory = os.open("/", directory_flags)
        fresh_root_identity = directory_identity(os.fstat(pending_fresh_directory))
        fresh_descriptors.append(pending_fresh_directory)
        pending_fresh_directory = None
        if (
            fresh_root_identity != directory_identities[0]
        ):
            raise RuntimeError("filesystem root identity changed during execution")
        for offset, component in enumerate(walk_components, start=1):
            pending_fresh_directory = os.open(
                component,
                directory_flags,
                dir_fd=fresh_descriptors[-1],
            )
            fresh_identity = directory_identity(os.fstat(pending_fresh_directory))
            fresh_descriptors.append(pending_fresh_directory)
            pending_fresh_directory = None
            if fresh_identity != directory_identities[offset]:
                raise RuntimeError(
                    "exact-source directory identity changed during execution"
                )
        endpoint_leaf = os.open(
            parts[-1],
            leaf_flags,
            dir_fd=fresh_descriptors[-1],
        )
        reopened_before = os.fstat(endpoint_leaf)
        reopened_matches = compare_declared(endpoint_leaf, first)
        reopened_after = os.fstat(endpoint_leaf)
    except BaseException as error:
        fresh_primary_error = error
        raise
    finally:
        fresh_cleanup_error = fresh_primary_error
        fresh_cleanup_error = close_one(endpoint_leaf, fresh_cleanup_error)
        fresh_cleanup_error = close_one(
            pending_fresh_directory, fresh_cleanup_error
        )
        fresh_cleanup_error = close_many(fresh_descriptors, fresh_cleanup_error)
        if fresh_primary_error is None and fresh_cleanup_error is not None:
            raise RuntimeError("endpoint descriptor cleanup failed") from fresh_cleanup_error
    if (
        leaf_identity(reopened_before) != leaf_identity(after)
        or leaf_identity(reopened_after) != leaf_identity(after)
        or not reopened_matches
    ):
        raise RuntimeError("exact-source path no longer names the captured leaf")
    if pending is not None:
        _kind, value, traceback = pending
        raise value.with_traceback(traceback)
except BaseException as error:
    primary_error = error
    raise
finally:
    cleanup_error = primary_error
    cleanup_error = close_one(leaf, cleanup_error)
    cleanup_error = close_one(pending_directory, cleanup_error)
    cleanup_error = close_many(directory_descriptors, cleanup_error)
    if primary_error is None and cleanup_error is not None:
        raise RuntimeError("exact-source descriptor cleanup failed") from cleanup_error
PYTHON_BOOTSTRAP
