#!/usr/bin/env python3
"""Remove only the reviewed inert ``actions/checkout`` worktree-config residue.

The composite contract rejects worktree-scoped Git configuration.  GitHub's pinned
``actions/checkout`` revision can leave one exact, inert ``.git/config.worktree``
after disabling sparse checkout and unsetting ``extensions.worktreeConfig``.  This
normalizer accepts absence or that one byte image and refuses every other object.
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
        "ERROR: normalize-actions-checkout-worktree-config.py requires "
        "Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT: Final[Path] = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT: Final[Path] = SCRIPT.parent.parent
RELATIVE: Final[str] = ".git/config.worktree"
EXPECTED: Final[bytes] = (
    b"[core]\n"
    b"\tsparseCheckout = false\n"
    b"\tsparseCheckoutCone = false\n"
    b"[index]\n"
    b"\tsparse = false\n"
)
EXPECTED_SHA256: Final[str] = (
    "443a5f645c23c3d0c0aa09f634b2ad111d46ef61946b598a2fb311678ab47454"
)


class NormalizationError(RuntimeError):
    """The checkout residue was not the one reviewed inert byte image."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise NormalizationError(message)


def identity(info: os.stat_result) -> tuple[int, int, int, int, int, int, int]:
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_nlink,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def normalize(root: Path) -> dict[str, object]:
    require(root.is_absolute(), "repository root is not absolute")
    require(root.resolve(strict=True) == root, "repository root route is not canonical")
    git_dir = root / ".git"
    git_info = git_dir.lstat()
    require(
        stat.S_ISDIR(git_info.st_mode) and git_dir.resolve(strict=True) == git_dir,
        "expected a real .git directory at the checkout root",
    )
    directory_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        directory_flags |= os.O_DIRECTORY
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
    git_fd = os.open(git_dir, directory_flags)
    try:
        try:
            before = os.stat("config.worktree", dir_fd=git_fd, follow_symlinks=False)
        except FileNotFoundError:
            return {
                "disposition": "already_absent",
                "expected_sha256": EXPECTED_SHA256,
                "path": RELATIVE,
            }
        require(stat.S_ISREG(before.st_mode), "worktree config is not a regular file")
        require(before.st_nlink == 1, "worktree config is hard-linked")
        require(
            stat.S_IMODE(before.st_mode) == 0o644,
            "worktree config mode changed",
        )
        require(before.st_size == len(EXPECTED), "worktree config size changed")
        flags = os.O_RDONLY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        file_fd = os.open("config.worktree", flags, dir_fd=git_fd)
        try:
            opened = os.fstat(file_fd)
            require(identity(opened) == identity(before), "worktree config changed before read")
            raw = os.read(file_fd, len(EXPECTED) + 1)
            require(os.read(file_fd, 1) == b"", "worktree config exceeds the byte bound")
        finally:
            os.close(file_fd)
        after = os.stat("config.worktree", dir_fd=git_fd, follow_symlinks=False)
        require(identity(after) == identity(before), "worktree config changed during read")
        require(raw == EXPECTED, "worktree config bytes are not the reviewed inert residue")
        require(hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256, "internal digest drift")
        os.unlink("config.worktree", dir_fd=git_fd)
        try:
            os.stat("config.worktree", dir_fd=git_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise NormalizationError("worktree config survived exact normalization")
    finally:
        os.close(git_fd)
    return {
        "disposition": "reviewed_inert_residue_removed",
        "expected_sha256": EXPECTED_SHA256,
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
        print("ERROR: unexpected bounded checkout-normalization failure", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
