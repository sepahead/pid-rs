#!/usr/bin/env python3
"""Preserve the immutable KSG revision-4 lanes on a changing descendant.

The revision-4 checker and mutation suite are immutable historical objects bound by the retained
Lean r14 receipt.  Their full catalog route intentionally freezes unrelated catalog rows and is
therefore not a live descendant gate.  This versioned preservation checker pins those two objects,
replays every still-applicable scoped route in normal and optimized Python, and separately invokes
the current complete method-catalog authority and its hostile suite in both modes.

The historical ``--claim-only`` and ``--release-only`` routes are superseded on the live
descendant: exact C12's terminal revision index is now the claim authority, and the release family
has separately scoped successors.  ``--catalog-only`` is historical-only because the current
catalog checker replaces its frozen projection.  Exact-tree replay retains all three historical
routes.  Returned tuples are bounded in-process
execution receipts: they detect the registered call-erasure mutations, but are not authenticity,
atomic-filesystem, anti-transient-substitution, or coordinated checker/self-test rewrite proofs.

This is operational preservation and current catalog-custody evidence.  It does not promote the
revision-4 ``integration_no_go`` packet, reinterpret historical evidence, or establish KSG/PID
theorem truth, estimator validity, numerical portability, or application validity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from typing import NoReturn


if sys.version_info < (3, 11):
    raise SystemExit(
        "check-ksg-harmonic-revision-v4-preservation.py requires Python 3.11+"
    )


ROOT = Path(__file__).resolve().parent.parent
HISTORICAL_CHECKER_RELATIVE = "scripts/check-ksg-harmonic-revision.py"
HISTORICAL_SELF_TEST_RELATIVE = "scripts/check-ksg-harmonic-revision-self-test.py"
CURRENT_CATALOG_CHECKER_RELATIVE = "scripts/check-method-catalog.py"
CURRENT_CATALOG_SELF_TEST_RELATIVE = "scripts/check-method-catalog-self-test.py"
CURRENT_CATALOG_SCHEMA_HELPER_RELATIVE = "scripts/json_schema_subset.py"
SOURCE_MATERIALIZER_RELATIVE = "scripts/materialize-public-api-source.sh"

HISTORICAL_SOURCE = {
    "commit_sha": "cb3f58f0b190454cb3f1090de8798261ec78f194",
    "object_format": "sha1",
    "tree_sha": "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
}
EXPECTED_HISTORICAL_SOURCE_ROSTER_SHA256 = (
    "90ab1cc556319c5bb3dc76b3b193bb5ca31418dbcf67c10a837f948f1a95d46f"
)

EXPECTED_COMPONENT_SHA256 = {
    CURRENT_CATALOG_CHECKER_RELATIVE: (
        "ada2f616f5b29e5907e6fb3242deb875a4af95b6609910d0f3774d1450878918"
    ),
    CURRENT_CATALOG_SELF_TEST_RELATIVE: (
        "6614f0424747d959a4ec1326f4bcacccd88569543a47e7b2ed06969ca4798aac"
    ),
    CURRENT_CATALOG_SCHEMA_HELPER_RELATIVE: (
        "067e6d6b10d33f5b9c1bab6bc621735267a06f2461d6c0da3c8342ac8bd391a6"
    ),
    HISTORICAL_CHECKER_RELATIVE: (
        "cf4692597bc49448d520580d96e1e6d23b4fc65834539095152bb561ec6450e9"
    ),
    HISTORICAL_SELF_TEST_RELATIVE: (
        "2abbfe7a54e0c2e3263f3dbe1b8776b197ae13cd8fedacc6d1cc1997f94ee6f0"
    ),
    SOURCE_MATERIALIZER_RELATIVE: (
        "b395f9deca3340f8a631f7de52b4998c970bad75fa6f5b2b96c3f2e620b4f1b6"
    ),
}
EXPECTED_COMPONENT_ROSTER_SHA256 = (
    "306537be043abf6c8b3d58e312cc402610e5292666e16233e625631ccb679147"
)

PYTHON_CHILD_FLAGS = ("-S", "-B")
EXPECTED_PYTHON_CHILD_FLAG_ROSTER_SHA256 = (
    "cfba3a280d946df2979a080477e71b4577d5d28cdd33f8e70b72bf7f3a969d63"
)
HISTORICAL_REPLAY_FLAGS = ("-I", "-S", "-B")
EXPECTED_HISTORICAL_REPLAY_FLAG_ROSTER_SHA256 = (
    "211f87eed550d5d15c3ba68223d1b470149e0c26a2ccc1f56bff01d335bb755b"
)
EXPECTED_GIT_ENVIRONMENT_SHA256 = (
    "18633bf675798e1dcaac8b525c56da9f246f3aedd1c2c11dc31fbeb527177f18"
)

ROUTES = (
    "--source-only",
    "--exact-only",
    "--binary64-only",
    "--enclosure-only",
)
EXPECTED_ROUTE_ROSTER_SHA256 = (
    "42bdb9579a6cb38e82ed6c9b81d76d433adfb274690b264df35a677bd5bde6d3"
)
SUPERSEDED_LIVE_ROUTES = {
    "--claim-only": (
        "Superseded on the live descendant because the exact-C12 terminal revision "
        "index is now the current claim authority; the pinned historical-tree replay "
        "retains the original claim-only gate."
    ),
    "--release-only": (
        "Superseded on the live descendant by six separately scoped and reviewed "
        "release-family revisions of represented-input PID2 synergy; the pinned "
        "historical-tree replay retains the original release-only gate."
    )
}
EXPECTED_SUPERSEDED_LIVE_ROUTE_ROSTER_SHA256 = (
    "4a46e452b51828f161b5d41e44f756b0336a86e82f5da63f59d40d0b902ee137"
)
EXPECTED_ROUTE_STDOUT = {
    "--source-only": b"KSG harmonic-revision source check passed\n",
    "--exact-only": (b"KSG harmonic-revision exact check passed: 6,920 tuples\n"),
    "--binary64-only": (
        "KSG harmonic-revision binary64 check passed: 8,198 Decimal cells; "
        "binary64-rounded-reference max 8 eps with 40 ties, allowed 32 eps; "
        "exact-rational error is checked separately; zero source-swap asymmetries\n"
    ).encode(),
    "--enclosure-only": (
        "KSG harmonic-revision exact-enclosure check passed: "
        "8,198 directed intervals; 6,920 exact-Fraction containments; "
        "29-mutation suite is a separate gate\n"
    ).encode(),
}
EXPECTED_CATALOG_STDOUT = {
    CURRENT_CATALOG_CHECKER_RELATIVE: (
        b"OK: 75 method entries and 48 references are coherent\n"
    ),
    CURRENT_CATALOG_SELF_TEST_RELATIVE: (
        b"OK: 85 method-catalog mutations were rejected\n"
    ),
}
CURRENT_CATALOG_COMMANDS = (
    CURRENT_CATALOG_CHECKER_RELATIVE,
    CURRENT_CATALOG_SELF_TEST_RELATIVE,
)
EXPECTED_CURRENT_CATALOG_COMMAND_ROSTER_SHA256 = (
    "8ff169026350e7e0f9d520107a8c6abe63f33be74471ad992403d3a02eb47f11"
)
DEFAULT_SUCCESS_LINE = (
    "KSG revision-4 preservation check passed: 6 pinned components; "
    "4 live-applicable historical scoped routes x normal/-O; 2 superseded live routes "
    "retained by exact-tree replay; 2 current catalog authorities x "
    "normal/-O; exact status/stdout/stderr parity"
)
HISTORICAL_REPLAY_SUCCESS_LINE = (
    "KSG revision-4 exact-tree mutation replay passed: pinned SHA-1 commit/tree; "
    "241 full-suite and 147 claim-suite mutations x normal/-O; exact "
    "status/stdout/stderr parity"
)
EXPECTED_HISTORICAL_TREE_REPLAY_RECEIPT = (
    "historical-source-facts-before",
    "source-materializer-pinned",
    "historical-source-materialized",
    "historical-components-before",
    "historical full mutation suite",
    "historical claim mutation suite",
    "historical-components-after",
    "historical-source-facts-after",
)
EXPECTED_HISTORICAL_TREE_REPLAY_RECEIPT_SHA256 = (
    "6f7c6452f85c310db5fb0ac59f59da9c8ea6dbd645e5103cec68bcb053312fe5"
)
EXPECTED_HISTORICAL_SELF_TEST_STDOUT = (
    "KSG harmonic-revision self-test passed: 241 mutations rejected "
    "(checker-model=16, fixture-custody=2, fixture-semantics=12, "
    "textual-source=78, release=78, catalog=55); scope-isolation-preflights=2\n"
).encode()
EXPECTED_HISTORICAL_CLAIM_SELF_TEST_STDOUT = (
    "KSG harmonic-revision claim self-test passed: 147 mutations rejected "
    "(custody=3, manifest-structure=70, resealed-semantics=74); each resealed "
    "mutation was rejected first by packet custody and then after leaf hashes plus "
    "the unavoidable manifest-envelope digest were rebound, using the separate "
    "reviewed-artifact byte map or typed/lifecycle contract\n"
).encode()
GIT = Path("/usr/bin/git")


class ContractError(RuntimeError):
    """A preservation or execution contract failed."""


def fail(message: str) -> NoReturn:
    raise ContractError(message)


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def check_interpreter_contract() -> None:
    if not (
        sys.version_info >= (3, 11)
        and sys.flags.isolated == 1
        and sys.flags.safe_path
        and sys.flags.no_site == 1
        and sys.flags.ignore_environment == 1
        and sys.dont_write_bytecode
    ):
        fail("checker requires Python 3.11+ invoked with -I -S -B")


def check_static_contract() -> None:
    if canonical_sha256(HISTORICAL_SOURCE) != EXPECTED_HISTORICAL_SOURCE_ROSTER_SHA256:
        fail("historical source commit/tree/object-format roster drifted")
    if canonical_sha256(list(ROUTES)) != EXPECTED_ROUTE_ROSTER_SHA256:
        fail("historical scoped-route roster drifted")
    if (
        canonical_sha256(SUPERSEDED_LIVE_ROUTES)
        != EXPECTED_SUPERSEDED_LIVE_ROUTE_ROSTER_SHA256
    ):
        fail("superseded live-route roster or rationale drifted")
    if set(SUPERSEDED_LIVE_ROUTES) != {"--claim-only", "--release-only"}:
        fail("superseded live-route partition drifted")
    if set(ROUTES).intersection(SUPERSEDED_LIVE_ROUTES):
        fail("live and superseded historical route partitions overlap")
    if set(EXPECTED_ROUTE_STDOUT) != set(ROUTES):
        fail("historical route/output roster partition drifted")
    if canonical_sha256(EXPECTED_COMPONENT_SHA256) != EXPECTED_COMPONENT_ROSTER_SHA256:
        fail("pinned component roster or digest drifted")
    expected_paths = {
        HISTORICAL_CHECKER_RELATIVE,
        HISTORICAL_SELF_TEST_RELATIVE,
        CURRENT_CATALOG_CHECKER_RELATIVE,
        CURRENT_CATALOG_SELF_TEST_RELATIVE,
        CURRENT_CATALOG_SCHEMA_HELPER_RELATIVE,
        SOURCE_MATERIALIZER_RELATIVE,
    }
    if set(EXPECTED_COMPONENT_SHA256) != expected_paths:
        fail("pinned component role/path partition drifted")
    if set(EXPECTED_CATALOG_STDOUT) != {
        CURRENT_CATALOG_CHECKER_RELATIVE,
        CURRENT_CATALOG_SELF_TEST_RELATIVE,
    }:
        fail("current catalog command/output roster drifted")
    if (
        canonical_sha256(list(CURRENT_CATALOG_COMMANDS))
        != EXPECTED_CURRENT_CATALOG_COMMAND_ROSTER_SHA256
    ):
        fail("current catalog execution roster drifted")
    if (
        canonical_sha256(list(PYTHON_CHILD_FLAGS))
        != EXPECTED_PYTHON_CHILD_FLAG_ROSTER_SHA256
    ):
        fail("descendant child-interpreter flag roster drifted")
    if (
        canonical_sha256(list(HISTORICAL_REPLAY_FLAGS))
        != EXPECTED_HISTORICAL_REPLAY_FLAG_ROSTER_SHA256
    ):
        fail("historical replay interpreter flag roster drifted")
    if (
        canonical_sha256(list(EXPECTED_HISTORICAL_TREE_REPLAY_RECEIPT))
        != EXPECTED_HISTORICAL_TREE_REPLAY_RECEIPT_SHA256
    ):
        fail("historical exact-tree execution receipt roster drifted")
    if canonical_sha256(git_environment()) != EXPECTED_GIT_ENVIRONMENT_SHA256:
        fail("isolated Git environment roster drifted")


def stable_regular_bytes(repo_root: Path, relative: str) -> bytes:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        fail(f"component path escapes repository: {relative}")
    component = repo_root / relative_path
    before = component.lstat()
    if not stat.S_ISREG(before.st_mode) or component.is_symlink():
        fail(f"component is not a regular non-symlink file: {relative}")
    if before.st_nlink != 1:
        fail(f"component has an unexpected hard-link count: {relative}")
    raw = component.read_bytes()
    after = component.lstat()
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_nlink,
        before.st_size,
        before.st_mtime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_nlink,
        after.st_size,
        after.st_mtime_ns,
    )
    if identity_before != identity_after or len(raw) != before.st_size:
        fail(f"component changed during stable read: {relative}")
    return raw


def check_component_hashes(repo_root: Path) -> None:
    for relative, expected in sorted(EXPECTED_COMPONENT_SHA256.items()):
        actual = hashlib.sha256(stable_regular_bytes(repo_root, relative)).hexdigest()
        if actual != expected:
            fail(f"pinned component SHA-256 mismatch: {relative}")


def child_environment() -> dict[str, str]:
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
    }


def run_python(
    repo_root: Path,
    relative: str,
    arguments: tuple[str, ...],
    *,
    optimized: bool,
) -> subprocess.CompletedProcess[bytes]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend((*PYTHON_CHILD_FLAGS, str(repo_root / relative), *arguments))
    return subprocess.run(
        command,
        cwd=repo_root,
        env=child_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=600,
    )


def check_execution_pair(
    label: str,
    normal: subprocess.CompletedProcess[bytes],
    optimized: subprocess.CompletedProcess[bytes],
    expected_stdout: bytes,
) -> None:
    if normal.returncode != 0 or optimized.returncode != 0:
        fail(
            f"{label}: child status drifted: "
            f"normal={normal.returncode}, optimized={optimized.returncode}"
        )
    if normal.stderr != b"" or optimized.stderr != b"":
        fail(f"{label}: child stderr is not empty")
    if normal.stdout != optimized.stdout:
        fail(f"{label}: normal/-O stdout parity drifted")
    if normal.stdout != expected_stdout:
        fail(f"{label}: exact stdout drifted")


def run_historical_routes(repo_root: Path) -> tuple[str, ...]:
    completed: list[str] = []
    for route in ROUTES:
        arguments = ("--repo-root", str(repo_root), route)
        normal = run_python(
            repo_root,
            HISTORICAL_CHECKER_RELATIVE,
            arguments,
            optimized=False,
        )
        optimized = run_python(
            repo_root,
            HISTORICAL_CHECKER_RELATIVE,
            arguments,
            optimized=True,
        )
        check_execution_pair(route, normal, optimized, EXPECTED_ROUTE_STDOUT[route])
        completed.append(route)
    return tuple(completed)


def run_current_catalog_authority(repo_root: Path) -> tuple[str, ...]:
    completed: list[str] = []
    for relative in CURRENT_CATALOG_COMMANDS:
        normal = run_python(repo_root, relative, (), optimized=False)
        optimized = run_python(repo_root, relative, (), optimized=True)
        check_execution_pair(
            f"current catalog authority {relative}",
            normal,
            optimized,
            EXPECTED_CATALOG_STDOUT[relative],
        )
        completed.append(relative)
    return tuple(completed)


def inspect_fixed_git() -> None:
    try:
        observed = GIT.lstat()
        resolved = GIT.resolve(strict=True)
    except OSError as error:
        fail(f"cannot inspect fixed Git executable: {error}")
    if resolved != GIT or not stat.S_ISREG(observed.st_mode):
        fail("fixed Git executable is not a canonical regular file")


def git_environment() -> dict[str, str]:
    return {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_GRAFT_FILE": os.devnull,
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "PAGER": "cat",
        "PATH": "/usr/bin:/bin",
    }


def run_git(repo_root: Path, *arguments: str) -> bytes:
    inspect_fixed_git()
    result = subprocess.run(
        [
            os.fspath(GIT),
            "-c",
            "advice.graftFileDeprecated=false",
            "-c",
            f"core.attributesFile={os.devnull}",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-C",
            os.fspath(repo_root),
            *arguments,
        ],
        env=git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if result.returncode != 0 or result.stderr != b"":
        fail(
            f"isolated Git command failed: arguments={arguments!r}; "
            f"status={result.returncode}; stderr={result.stderr!r}"
        )
    return result.stdout


def historical_source_facts(repo_root: Path) -> tuple[bytes, ...]:
    commit = HISTORICAL_SOURCE["commit_sha"]
    tree = HISTORICAL_SOURCE["tree_sha"]
    expected_root = os.fsencode(os.fspath(repo_root)) + b"\n"
    head = run_git(repo_root, "rev-parse", "--verify", "HEAD^{commit}")
    if (
        len(head) != 41
        or not head.endswith(b"\n")
        or any(byte not in b"0123456789abcdef" for byte in head[:-1])
    ):
        fail("current HEAD is not one canonical SHA-1 commit identifier")
    ancestor = run_git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        commit,
        head[:-1].decode("ascii"),
    )
    facts = (
        run_git(repo_root, "rev-parse", "--show-toplevel"),
        run_git(repo_root, "rev-parse", "--show-object-format"),
        run_git(repo_root, "rev-parse", "--is-shallow-repository"),
        head,
        ancestor,
        run_git(repo_root, "rev-parse", "--verify", f"{commit}^{{commit}}"),
        run_git(repo_root, "cat-file", "-t", commit),
        run_git(repo_root, "rev-parse", "--verify", f"{commit}^{{tree}}"),
        run_git(repo_root, "cat-file", "-t", tree),
    )
    expected = (
        expected_root,
        b"sha1\n",
        b"false\n",
        head,
        b"",
        commit.encode("ascii") + b"\n",
        b"commit\n",
        tree.encode("ascii") + b"\n",
        b"tree\n",
    )
    if facts != expected:
        fail("historical source Git object facts drifted")
    return facts


def materializer_environment() -> dict[str, str]:
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }


def write_private_executable(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o700)
    with os.fdopen(descriptor, "wb") as destination:
        destination.write(data)
        destination.flush()
        os.fsync(destination.fileno())


def check_materialized_historical_components(repo_root: Path) -> None:
    for relative in (HISTORICAL_CHECKER_RELATIVE, HISTORICAL_SELF_TEST_RELATIVE):
        actual = hashlib.sha256(stable_regular_bytes(repo_root, relative)).hexdigest()
        expected = EXPECTED_COMPONENT_SHA256[relative]
        if actual != expected:
            fail(f"materialized historical component SHA-256 mismatch: {relative}")


def run_materialized_historical_self_tests(repo_root: Path) -> tuple[str, ...]:
    cases = (
        ((), EXPECTED_HISTORICAL_SELF_TEST_STDOUT, "historical full mutation suite"),
        (
            ("--claim-only",),
            EXPECTED_HISTORICAL_CLAIM_SELF_TEST_STDOUT,
            "historical claim mutation suite",
        ),
    )
    completed: list[str] = []
    for arguments, expected_stdout, label in cases:
        results: list[subprocess.CompletedProcess[bytes]] = []
        for optimized in (False, True):
            command = [sys.executable]
            if optimized:
                command.append("-O")
            command.extend(
                (
                    *HISTORICAL_REPLAY_FLAGS,
                    os.fspath(repo_root / HISTORICAL_SELF_TEST_RELATIVE),
                    *arguments,
                )
            )
            results.append(
                subprocess.run(
                    command,
                    cwd=repo_root,
                    env=child_environment(),
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                    timeout=1800,
                )
            )
        check_execution_pair(label, results[0], results[1], expected_stdout)
        completed.append(label)
    return tuple(completed)


def run_historical_tree_replay(repo_root: Path) -> tuple[str, ...]:
    completed: list[str] = []
    before = historical_source_facts(repo_root)
    completed.append("historical-source-facts-before")
    materializer_bytes = stable_regular_bytes(repo_root, SOURCE_MATERIALIZER_RELATIVE)
    expected_materializer = EXPECTED_COMPONENT_SHA256[SOURCE_MATERIALIZER_RELATIVE]
    if hashlib.sha256(materializer_bytes).hexdigest() != expected_materializer:
        fail("source materializer SHA-256 drifted before exact-tree replay")
    completed.append("source-materializer-pinned")
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-revision-v4-exact-tree-"
    ) as directory:
        temporary_root = Path(directory)
        materializer = temporary_root / "materialize.sh"
        destination = temporary_root / "historical-source"
        write_private_executable(materializer, materializer_bytes)
        result = subprocess.run(
            [
                os.fspath(materializer),
                os.fspath(repo_root),
                HISTORICAL_SOURCE["commit_sha"],
                HISTORICAL_SOURCE["tree_sha"],
                os.fspath(destination),
            ],
            cwd=repo_root,
            env=materializer_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=600,
        )
        if result.returncode != 0 or result.stdout != b"" or result.stderr != b"":
            fail(
                "historical source materialization failed exact status/output contract: "
                f"status={result.returncode}; stdout={result.stdout!r}; "
                f"stderr={result.stderr!r}"
            )
        completed.append("historical-source-materialized")
        check_materialized_historical_components(destination)
        completed.append("historical-components-before")
        completed.extend(run_materialized_historical_self_tests(destination))
        check_materialized_historical_components(destination)
        completed.append("historical-components-after")
    after = historical_source_facts(repo_root)
    if before != after:
        fail("historical Git source facts changed across exact-tree replay")
    completed.append("historical-source-facts-after")
    return tuple(completed)


def check(repo_root: Path) -> None:
    check_interpreter_contract()
    check_static_contract()
    check_component_hashes(repo_root)
    route_receipt = run_historical_routes(repo_root)
    if route_receipt != ROUTES:
        fail("historical scoped-route execution receipt drifted")
    catalog_receipt = run_current_catalog_authority(repo_root)
    if catalog_receipt != CURRENT_CATALOG_COMMANDS:
        fail("current catalog execution receipt drifted")
    check_component_hashes(repo_root)


def check_historical_replay(repo_root: Path) -> None:
    check_interpreter_contract()
    check_static_contract()
    check_component_hashes(repo_root)
    replay_receipt = run_historical_tree_replay(repo_root)
    if replay_receipt != EXPECTED_HISTORICAL_TREE_REPLAY_RECEIPT:
        fail("historical exact-tree execution receipt drifted")
    check_component_hashes(repo_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=ROOT,
        help="repository root to check (used by the hostile self-test)",
    )
    parser.add_argument(
        "--historical-tree-replay",
        action="store_true",
        help=(
            "materialize the pinned historical commit/tree and replay its full and "
            "claim-only mutation suites; this is not a live descendant catalog gate"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        repo_root = args.repo_root.resolve(strict=True)
        if not repo_root.is_dir():
            fail("repository root is not a directory")
        if args.historical_tree_replay:
            check_historical_replay(repo_root)
            success_line = HISTORICAL_REPLAY_SUCCESS_LINE
        else:
            check(repo_root)
            success_line = DEFAULT_SUCCESS_LINE
    except (
        ContractError,
        OSError,
        subprocess.SubprocessError,
        TypeError,
        ValueError,
    ) as error:
        print(f"KSG revision-4 preservation check failed: {error}", file=sys.stderr)
        return 1
    print(success_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
