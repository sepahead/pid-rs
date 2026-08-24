#!/usr/bin/env python3
"""Remove only Git's reviewed default ``.git/info/exclude`` byte image.

The composite source-capture contract excludes repository-local ignore inputs.  A
fresh checkout nevertheless contains Git's comment-only default exclude file.
This CI-checkout-only normalizer accepts absence or that one exact byte image, read through
descriptor-relative, no-follow operations, and refuses every other object.  The
final stable-stat-to-unlink interval assumes no concurrent same-UID or privileged
writer; this is a bounded checkout preparation step, not a race-free deletion
theorem.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys
from typing import Final


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: normalize-actions-checkout-git-info-exclude.py requires "
        "Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT: Final[Path] = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT: Final[Path] = SCRIPT.parent.parent
RELATIVE: Final[str] = ".git/info/exclude"
EXPECTED: Final[bytes] = (
    b"# git ls-files --others --exclude-from=.git/info/exclude\n"
    b"# Lines that start with '#' are comments.\n"
    b"# For a project mostly in C, the following would be a good set of\n"
    b"# exclude patterns (uncomment them if you want to use them):\n"
    b"# *.[oa]\n"
    b"# *~\n"
)
EXPECTED_SHA256: Final[str] = hashlib.sha256(EXPECTED).hexdigest()
# The Git template installed by the hosted Ubuntu 24.04 image is mode 0755; this
# was observed independently in jobs 97292206996 and 97292207140 of run
# 32678998559.  Execute bits on this exact regular, public, comment-only file do
# not grant write access.  Keep an exact allowlist rather than generalizing from
# that observation; every accepted mode still has owner read/write and no
# group/other write or special bits.
ALLOWED_MODES: Final[frozenset[int]] = frozenset(
    (0o600, 0o604, 0o640, 0o644, 0o755)
)
ALLOWED_MODE_SPELLINGS: Final[tuple[str, ...]] = tuple(
    f"{mode:04o}" for mode in sorted(ALLOWED_MODES)
)
ALLOWED_MODE_SUMMARY: Final[str] = ",".join(ALLOWED_MODE_SPELLINGS)


class NormalizationError(RuntimeError):
    """The checkout residue was not the reviewed comment-only byte image."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise NormalizationError(message)


def identity(info: os.stat_result) -> tuple[int, ...]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_uid,
        info.st_gid,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def reviewed_mode(mode: int) -> bool:
    """Accept only the reviewed checkout-template modes."""
    return mode in ALLOWED_MODES


def directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def open_stable_directory(parent_fd: int, name: str) -> int:
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    require(stat.S_ISDIR(before.st_mode), f"{name} is not a real directory")
    descriptor = os.open(name, directory_flags(), dir_fd=parent_fd)
    opened = os.fstat(descriptor)
    if identity(opened) != identity(before):
        os.close(descriptor)
        raise NormalizationError(f"{name} changed while opening")
    return descriptor


def read_bounded(descriptor: int, maximum: int) -> bytes:
    chunks: list[bytes] = []
    remaining = maximum + 1
    while remaining:
        chunk = os.read(descriptor, remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def normalize(root: Path) -> dict[str, object]:
    require(root.is_absolute(), "repository root is not absolute")
    require(root.resolve(strict=True) == root, "repository root route is not canonical")
    root_fd = os.open(root, directory_flags())
    try:
        git_fd = open_stable_directory(root_fd, ".git")
        try:
            info_fd = open_stable_directory(git_fd, "info")
            try:
                try:
                    before = os.stat("exclude", dir_fd=info_fd, follow_symlinks=False)
                except FileNotFoundError:
                    return {
                        "allowed_modes": list(ALLOWED_MODE_SPELLINGS),
                        "disposition": "already_absent",
                        "expected_sha256": EXPECTED_SHA256,
                        "path": RELATIVE,
                    }
                require(
                    stat.S_ISREG(before.st_mode), "git exclude is not a regular file"
                )
                require(before.st_nlink == 1, "git exclude is hard-linked")
                observed_mode = stat.S_IMODE(before.st_mode)
                require(
                    reviewed_mode(observed_mode),
                    "git exclude mode rejected: "
                    f"observed={observed_mode:04o}; "
                    f"allowed_modes={ALLOWED_MODE_SUMMARY}",
                )
                require(before.st_size == len(EXPECTED), "git exclude size changed")
                flags = os.O_RDONLY
                if hasattr(os, "O_CLOEXEC"):
                    flags |= os.O_CLOEXEC
                if hasattr(os, "O_NOFOLLOW"):
                    flags |= os.O_NOFOLLOW
                file_fd = os.open("exclude", flags, dir_fd=info_fd)
                try:
                    opened = os.fstat(file_fd)
                    require(
                        identity(opened) == identity(before),
                        "git exclude changed before read",
                    )
                    raw = read_bounded(file_fd, len(EXPECTED))
                    require(
                        os.read(file_fd, 1) == b"", "git exclude exceeds the byte bound"
                    )
                    closed_identity = identity(os.fstat(file_fd))
                finally:
                    os.close(file_fd)
                after = os.stat("exclude", dir_fd=info_fd, follow_symlinks=False)
                require(
                    identity(after) == identity(before) == closed_identity,
                    "git exclude changed during read",
                )
                require(
                    raw == EXPECTED,
                    "git exclude bytes are not the reviewed default residue",
                )
                require(
                    hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256,
                    "internal digest drift",
                )
                # Re-check immediately before removal. POSIX unlink-by-name has no
                # descriptor identity predicate, so the documented no-concurrent-
                # writer assumption remains necessary across this final interval.
                final = os.stat("exclude", dir_fd=info_fd, follow_symlinks=False)
                require(
                    identity(final) == identity(before),
                    "git exclude changed before removal",
                )
                os.unlink("exclude", dir_fd=info_fd)
                try:
                    os.stat("exclude", dir_fd=info_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise NormalizationError("git exclude survived exact normalization")
            finally:
                os.close(info_fd)
        finally:
            os.close(git_fd)
    finally:
        os.close(root_fd)
    return {
        "allowed_modes": list(ALLOWED_MODE_SPELLINGS),
        "disposition": "reviewed_default_residue_removed",
        "expected_sha256": EXPECTED_SHA256,
        "observed_mode": f"{observed_mode:04o}",
        "path": RELATIVE,
    }


def main() -> int:
    try:
        result = normalize(ROOT)
        sys.stdout.write(
            json.dumps(result, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        )
        return 0
    except (NormalizationError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    except Exception:
        print(
            "ERROR: unexpected bounded checkout-normalization failure", file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
