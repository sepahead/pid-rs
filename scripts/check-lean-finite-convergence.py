#!/usr/bin/env python3
"""Build the pinned Lean proof of finite-alphabet deterministic convergence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "audit" / "formal" / "lean"
TOOLCHAIN = "leanprover/lean4:v4.32.0"
MATHLIB_URL = "https://github.com/leanprover-community/mathlib4.git"
MATHLIB_REVISION = "81a5d257c8e410db227a6665ed08f64fea08e997"
EXPECTED_MANIFEST_SHA256 = (
    "e63604e84790371ae176fc905c755e98a0dbccf8cb50a07561b1f5419e33c5bd"
)
EXPECTED_PACKAGE_PINS = {
    "mathlib": (
        MATHLIB_URL,
        MATHLIB_REVISION,
        "v4.32.0",
        False,
    ),
    "plausible": (
        "https://github.com/leanprover-community/plausible",
        "e12c1910fe855cbfc38803cd4e55543906d5fa62",
        "main",
        True,
    ),
    "LeanSearchClient": (
        "https://github.com/leanprover-community/LeanSearchClient",
        "c5d5b8fe6e5158def25cd28eb94e4141ad97c843",
        "main",
        True,
    ),
    "importGraph": (
        "https://github.com/leanprover-community/import-graph",
        "7e9612bf0b9ee66db3cb5b9988a35afc706f5a12",
        "main",
        True,
    ),
    "proofwidgets": (
        "https://github.com/leanprover-community/ProofWidgets4",
        "6e311e2a844da9b2cc3971187df2fe0066947b93",
        "main",
        True,
    ),
    "aesop": (
        "https://github.com/leanprover-community/aesop",
        "a7dbf0c63b694e47f425f3dcddbc0e178bb432d3",
        "master",
        True,
    ),
    "Qq": (
        "https://github.com/leanprover-community/quote4",
        "38d591e778f100aec9762bb582f9c7f55f50e9dc",
        "master",
        True,
    ),
    "batteries": (
        "https://github.com/leanprover-community/batteries",
        "023ce7d62a0531e22a5331e20b587817a80d49ff",
        "main",
        True,
    ),
    "Cli": (
        "https://github.com/leanprover/lean4-cli",
        "88679d088c9720c27ebdf2ba4dafe17341747f94",
        "v4.32.0",
        True,
    ),
}
EXPECTED_LAKEFILE = """name = "pid-finite-convergence"
version = "0.1.0"
defaultTargets = ["PidFiniteConvergence"]

[[require]]
name = "mathlib"
git = "https://github.com/leanprover-community/mathlib4.git"
rev = "v4.32.0"

[[lean_lib]]
name = "PidFiniteConvergence"
"""
EXPECTED_SOURCES = {
    "PidFiniteConvergence.lean",
    "PidFiniteConvergence/Dependence.lean",
    "PidFiniteConvergence/Deterministic.lean",
}
EXPECTED_ROOT_SOURCE = """import PidFiniteConvergence.Dependence
import PidFiniteConvergence.Deterministic
"""
REMOVED_ENVIRONMENT_KEYS = (
    "ELAN_TOOLCHAIN",
    "LEAN_PATH",
    "LEAN_SRC_PATH",
    "LEAN_SYSROOT",
)
TIMEOUT_SECONDS = 900
GIT_TIMEOUT_SECONDS = 30


class LeanProofError(RuntimeError):
    """Raised when the pinned formal artifact cannot be checked."""


def read_regular_text(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as error:
        raise LeanProofError(f"could not read UTF-8 file {path}: {error}") from error


def read_regular_bytes(path: Path) -> bytes:
    if not path.is_file() or path.is_symlink():
        raise LeanProofError(f"required regular file is missing: {path}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise LeanProofError(f"could not read file {path}: {error}") from error


def check_toolchain() -> None:
    actual = read_regular_text(PROJECT / "lean-toolchain")
    if actual != f"{TOOLCHAIN}\n":
        raise LeanProofError(
            f"lean-toolchain must contain exactly {TOOLCHAIN!r} and one newline"
        )


def check_lakefile() -> None:
    actual = read_regular_text(PROJECT / "lakefile.toml")
    if actual != EXPECTED_LAKEFILE:
        raise LeanProofError(
            "lakefile.toml does not match the pinned project declaration"
        )


def check_manifest() -> None:
    path = PROJECT / "lake-manifest.json"
    raw = read_regular_bytes(path)
    actual_sha256 = hashlib.sha256(raw).hexdigest()
    if actual_sha256 != EXPECTED_MANIFEST_SHA256:
        raise LeanProofError(
            "Lake manifest byte digest mismatch: "
            f"expected {EXPECTED_MANIFEST_SHA256}, found {actual_sha256}"
        )
    try:
        manifest = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise LeanProofError(f"invalid Lake manifest JSON: {error}") from error
    packages = manifest.get("packages")
    if not isinstance(packages, list):
        raise LeanProofError("Lake manifest packages must be a list")
    if not all(isinstance(package, dict) for package in packages):
        raise LeanProofError("each Lake manifest package must be an object")
    package_map = {package.get("name"): package for package in packages}
    if len(package_map) != len(packages):
        raise LeanProofError("Lake manifest package names must be unique")
    expected_names = set(EXPECTED_PACKAGE_PINS)
    actual_names = set(package_map)
    if actual_names != expected_names:
        raise LeanProofError(
            "Lake manifest package set mismatch: "
            f"missing={sorted(expected_names - actual_names)}, "
            f"unexpected={sorted(actual_names - expected_names)}"
        )
    for name, (
        url,
        revision,
        input_revision,
        inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        package = package_map[name]
        expected = {
            "type": "git",
            "url": url,
            "rev": revision,
            "inputRev": input_revision,
            "inherited": inherited,
        }
        mismatches = {
            key: (expected_value, package.get(key))
            for key, expected_value in expected.items()
            if package.get(key) != expected_value
        }
        if mismatches:
            raise LeanProofError(f"{name} manifest pin mismatch: {mismatches}")


def check_sources() -> int:
    sources = sorted(
        source
        for source in PROJECT.rglob("*.lean")
        if ".lake" not in source.relative_to(PROJECT).parts
    )
    if not sources:
        raise LeanProofError("Lean project contains no source files")
    relative_sources = {source.relative_to(PROJECT).as_posix() for source in sources}
    if relative_sources != EXPECTED_SOURCES:
        raise LeanProofError(
            "Lean source manifest mismatch: "
            f"missing={sorted(EXPECTED_SOURCES - relative_sources)}, "
            f"unexpected={sorted(relative_sources - EXPECTED_SOURCES)}"
        )
    placeholder = re.compile(r"\b(?:admit|axiom|constant|sorry|sorryAx)\b")
    for source in sources:
        text = read_regular_text(source)
        if (
            source == PROJECT / "PidFiniteConvergence.lean"
            and text != EXPECTED_ROOT_SOURCE
        ):
            raise LeanProofError(
                "PidFiniteConvergence.lean must import the checked deterministic module exactly"
            )
        if source.parent == PROJECT / "PidFiniteConvergence" and (
            "set_option warningAsError true\n" not in text
        ):
            raise LeanProofError(f"the checked module must enable warningAsError: {source}")
        match = placeholder.search(text)
        if match is not None:
            raise LeanProofError(
                f"forbidden proof placeholder or declaration in {source}: {match.group(0)}"
            )
    return len(sources)


def find_lake() -> Path:
    candidate = shutil.which("lake")
    if candidate is None:
        raise LeanProofError("lake was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"lake is not an executable file: {path}")
    return path


def find_git() -> Path:
    candidate = shutil.which("git")
    if candidate is None:
        raise LeanProofError("git was not found on PATH")
    path = Path(candidate)
    if not path.is_file() or not os.access(path, os.X_OK):
        raise LeanProofError(f"git is not an executable file: {path}")
    return path


def run_git(git: Path, checkout: Path, arguments: list[str], description: str) -> str:
    environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
    )
    try:
        process = subprocess.run(
            [str(git), "-C", str(checkout), *arguments],
            env=environment,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}: {process.stderr.strip()}"
        )
    return process.stdout


def check_dependency_checkouts(git: Path) -> None:
    packages_directory = PROJECT / ".lake" / "packages"
    for name, (
        url,
        revision,
        _input_revision,
        _inherited,
    ) in EXPECTED_PACKAGE_PINS.items():
        checkout = packages_directory / name
        if not checkout.is_dir() or checkout.is_symlink():
            raise LeanProofError(
                f"dependency checkout is not a regular directory: {checkout}"
            )
        top_level = Path(
            run_git(
                git, checkout, ["rev-parse", "--show-toplevel"], f"{name} root check"
            ).strip()
        )
        if top_level.resolve() != checkout.resolve():
            raise LeanProofError(
                f"dependency checkout root mismatch for {name}: {top_level}"
            )
        actual_revision = run_git(
            git, checkout, ["rev-parse", "--verify", "HEAD"], f"{name} revision check"
        ).strip()
        if actual_revision != revision:
            raise LeanProofError(
                f"dependency revision mismatch for {name}: "
                f"expected {revision}, found {actual_revision}"
            )
        actual_url = run_git(
            git,
            checkout,
            ["config", "--local", "--get", "remote.origin.url"],
            f"{name} origin check",
        ).strip()
        if actual_url != url:
            raise LeanProofError(
                f"dependency origin mismatch for {name}: expected {url}, found {actual_url}"
            )
        status = run_git(
            git,
            checkout,
            ["status", "--porcelain=v1", "--untracked-files=all"],
            f"{name} cleanliness check",
        )
        if status:
            raise LeanProofError(f"dependency checkout is not clean: {name}")


def run_checked(command: list[str], description: str) -> str:
    environment = os.environ.copy()
    for key in REMOVED_ENVIRONMENT_KEYS:
        environment.pop(key, None)
    try:
        process = subprocess.run(
            command,
            cwd=PROJECT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise LeanProofError(f"{description} failed: {error}") from error
    if process.returncode != 0:
        raise LeanProofError(
            f"{description} failed with exit {process.returncode}:\n"
            f"stdout:\n{process.stdout}\nstderr:\n{process.stderr}"
        )
    return process.stdout


def check_version(lake: Path) -> str:
    output = run_checked([str(lake), "env", "lean", "--version"], "Lean version check")
    lines = output.splitlines()
    if (
        len(lines) != 1
        or re.fullmatch(r"Lean \(version 4\.32\.0, .+\)", lines[0]) is None
    ):
        raise LeanProofError(f"unexpected Lean version output: {output!r}")
    return lines[0]


def main() -> int:
    try:
        check_toolchain()
        check_lakefile()
        check_manifest()
        source_count = check_sources()
        lake = find_lake()
        git = find_git()
        version = check_version(lake)
        check_dependency_checkouts(git)
        run_checked([str(lake), "build", "PidFiniteConvergence"], "Lean proof build")
        run_checked(
            [str(lake), "env", "leanchecker", "PidFiniteConvergence"],
            "Lean kernel replay",
        )
    except LeanProofError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: checked {source_count} Lean sources for the deterministic finite-alphabet "
        f"convergence and dependency-color core ({version})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
