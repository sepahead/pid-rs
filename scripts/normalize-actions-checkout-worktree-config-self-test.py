#!/usr/bin/env python3
"""Hostile fixtures for the exact Actions checkout residue normalizer."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import stat
import sys
import tempfile


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: normalize-actions-checkout-worktree-config-self-test.py requires "
        "Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
NORMALIZER = ROOT / "scripts/normalize-actions-checkout-worktree-config.py"


class SelfTestError(RuntimeError):
    """A hostile filesystem shape was accepted or a positive control failed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_normalizer():
    specification = importlib.util.spec_from_file_location(
        "pid_rs_actions_checkout_normalizer", NORMALIZER
    )
    require(specification is not None and specification.loader is not None, "module spec")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def fixture(parent: Path, name: str) -> tuple[Path, Path]:
    root = parent / name
    git_dir = root / ".git"
    git_dir.mkdir(parents=True)
    return root, git_dir / "config.worktree"


def expect_rejection(module, root: Path, expected: str) -> None:
    try:
        module.normalize(root)
    except module.NormalizationError as error:
        require(str(error) == expected, f"wrong rejection: {error}")
        return
    except OSError:
        return
    raise SelfTestError(f"hostile fixture passed: {expected}")


def main() -> int:
    module = load_normalizer()
    with tempfile.TemporaryDirectory(prefix="pid-rs-actions-worktree-config-") as raw:
        parent = Path(raw).resolve(strict=True)

        absent_root, _ = fixture(parent, "absent")
        absent = module.normalize(absent_root)
        require(absent["disposition"] == "already_absent", "absent positive")

        exact_root, exact_path = fixture(parent, "exact")
        exact_path.write_bytes(module.EXPECTED)
        exact = module.normalize(exact_root)
        require(
            exact["disposition"] == "reviewed_inert_residue_removed"
            and not os.path.lexists(exact_path),
            "exact positive",
        )

        wrong_root, wrong_path = fixture(parent, "wrong")
        wrong_path.write_bytes(module.EXPECTED[:-1] + b"X")
        expect_rejection(module, wrong_root, "worktree config bytes are not the reviewed inert residue")
        require(wrong_path.exists(), "wrong bytes were removed")

        empty_root, empty_path = fixture(parent, "empty")
        empty_path.write_bytes(b"")
        expect_rejection(module, empty_root, "worktree config size changed")

        symlink_root, symlink_path = fixture(parent, "symlink")
        symlink_target = parent / "symlink-target"
        symlink_target.write_bytes(module.EXPECTED)
        symlink_path.symlink_to(symlink_target)
        expect_rejection(module, symlink_root, "worktree config is not a regular file")
        require(symlink_target.read_bytes() == module.EXPECTED, "symlink target changed")

        hardlink_root, hardlink_path = fixture(parent, "hardlink")
        hardlink_target = parent / "hardlink-target"
        hardlink_target.write_bytes(module.EXPECTED)
        os.link(hardlink_target, hardlink_path)
        expect_rejection(module, hardlink_root, "worktree config is hard-linked")

        directory_root, directory_path = fixture(parent, "directory")
        directory_path.mkdir()
        expect_rejection(module, directory_root, "worktree config is not a regular file")

        writable_root, writable_path = fixture(parent, "writable")
        writable_path.write_bytes(module.EXPECTED)
        writable_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IWGRP)
        expect_rejection(module, writable_root, "worktree config mode changed")

        executable_root, executable_path = fixture(parent, "executable")
        executable_path.write_bytes(module.EXPECTED)
        executable_path.chmod(0o744)
        expect_rejection(module, executable_root, "worktree config mode changed")

        readonly_root, readonly_path = fixture(parent, "readonly")
        readonly_path.write_bytes(module.EXPECTED)
        readonly_path.chmod(0o400)
        expect_rejection(module, readonly_root, "worktree config mode changed")

        git_symlink_root = parent / "git-symlink"
        git_symlink_root.mkdir()
        (git_symlink_root / ".git").symlink_to(absent_root / ".git")
        expect_rejection(module, git_symlink_root, "expected a real .git directory at the checkout root")

    print(
        "OK: Actions worktree-config normalizer accepted 2 positive states and rejected "
        "9 hostile filesystem/byte states"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"actions worktree-config normalizer self-test: {error}", file=sys.stderr)
        raise SystemExit(1)
