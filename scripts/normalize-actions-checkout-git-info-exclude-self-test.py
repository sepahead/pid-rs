#!/usr/bin/env python3
"""Hostile fixtures for the exact Git info/exclude normalizer."""

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
        "ERROR: normalize-actions-checkout-git-info-exclude-self-test.py requires "
        "Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


ROOT = Path(os.path.abspath(os.fspath(Path(__file__)))).parent.parent
NORMALIZER = ROOT / "scripts/normalize-actions-checkout-git-info-exclude.py"


class SelfTestError(RuntimeError):
    """A hostile filesystem shape was accepted or a positive control failed."""


def require(predicate: bool, message: str) -> None:
    if not predicate:
        raise SelfTestError(message)


def load_normalizer():
    specification = importlib.util.spec_from_file_location(
        "pid_rs_actions_checkout_git_exclude_normalizer", NORMALIZER
    )
    require(
        specification is not None and specification.loader is not None, "module spec"
    )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def fixture(parent: Path, name: str) -> tuple[Path, Path]:
    root = parent / name
    target = root / ".git/info/exclude"
    target.parent.mkdir(parents=True)
    return root, target


def expect_rejection(module, root: Path, expected: str) -> None:
    try:
        module.normalize(root)
    except module.NormalizationError as error:
        require(str(error) == expected, f"wrong rejection: {error}")
        return
    except OSError:
        return
    raise SelfTestError(f"hostile fixture passed: {expected}")


def write_exact(path: Path, raw: bytes, mode: int = 0o644) -> None:
    path.write_bytes(raw)
    path.chmod(mode)


def run_cases(module) -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-actions-git-exclude-") as raw:
        parent = Path(raw).resolve(strict=True)

        absent_root, _ = fixture(parent, "absent")
        absent = module.normalize(absent_root)
        require(absent["disposition"] == "already_absent", "absent positive")

        for mode in (0o600, 0o604, 0o640, 0o644):
            exact_root, exact_path = fixture(parent, f"exact-{mode:o}")
            write_exact(exact_path, module.EXPECTED, mode)
            exact = module.normalize(exact_root)
            require(
                exact["disposition"] == "reviewed_default_residue_removed"
                and exact["observed_mode"] == f"{mode:04o}"
                and not os.path.lexists(exact_path),
                f"exact {mode:o} positive",
            )

        wrong_root, wrong_path = fixture(parent, "wrong")
        write_exact(wrong_path, module.EXPECTED[:-1] + b"X")
        expect_rejection(
            module,
            wrong_root,
            "git exclude bytes are not the reviewed default residue",
        )
        require(wrong_path.exists(), "wrong bytes were removed")

        short_root, short_path = fixture(parent, "short")
        write_exact(short_path, module.EXPECTED[:-1])
        expect_rejection(module, short_root, "git exclude size changed")

        long_root, long_path = fixture(parent, "long")
        write_exact(long_path, module.EXPECTED + b"X")
        expect_rejection(module, long_root, "git exclude size changed")

        symlink_root, symlink_path = fixture(parent, "symlink")
        symlink_target = parent / "symlink-target"
        write_exact(symlink_target, module.EXPECTED)
        symlink_path.symlink_to(symlink_target)
        expect_rejection(module, symlink_root, "git exclude is not a regular file")
        require(
            symlink_target.read_bytes() == module.EXPECTED, "symlink target changed"
        )

        hardlink_root, hardlink_path = fixture(parent, "hardlink")
        hardlink_target = parent / "hardlink-target"
        write_exact(hardlink_target, module.EXPECTED)
        os.link(hardlink_target, hardlink_path)
        expect_rejection(module, hardlink_root, "git exclude is hard-linked")

        directory_root, directory_path = fixture(parent, "directory")
        directory_path.mkdir()
        expect_rejection(module, directory_root, "git exclude is not a regular file")

        for mode in (0o400, 0o620, 0o664, 0o744):
            mode_root, mode_path = fixture(parent, f"mode-{mode:o}")
            write_exact(mode_path, module.EXPECTED, mode)
            expect_rejection(
                module,
                mode_root,
                "git exclude mode rejected: "
                f"observed={mode:04o}; required_bits=0600; permitted_bits=0644",
            )
            require(
                mode_path.read_bytes() == module.EXPECTED
                and stat.S_IMODE(mode_path.stat().st_mode) == mode,
                f"mode {mode:o} residue changed",
            )

        git_symlink_root = parent / "git-symlink"
        git_symlink_root.mkdir()
        (git_symlink_root / ".git").symlink_to(absent_root / ".git")
        expect_rejection(module, git_symlink_root, ".git is not a real directory")

        info_symlink_root = parent / "info-symlink"
        (info_symlink_root / ".git").mkdir(parents=True)
        (info_symlink_root / ".git/info").symlink_to(absent_root / ".git/info")
        expect_rejection(module, info_symlink_root, "info is not a real directory")

        routed_root, _ = fixture(parent, "routed-target")
        root_symlink = parent / "routed-root"
        root_symlink.symlink_to(routed_root, target_is_directory=True)
        expect_rejection(
            module,
            root_symlink,
            "repository root route is not canonical",
        )

    print(
        "OK: Git info/exclude normalizer accepted 5 positive states and rejected "
        "13 hostile route/filesystem/byte states"
    )
    return 0


def main() -> int:
    module = load_normalizer()
    previous_umask = os.umask(0o077)
    try:
        return run_cases(module)
    finally:
        os.umask(previous_umask)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(
            f"actions git-info/exclude normalizer self-test: {error}", file=sys.stderr
        )
        raise SystemExit(1)
