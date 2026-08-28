#!/usr/bin/env python3
"""Hostile tests for the versioned KSG revision-4 descendant preservation gate."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import NoReturn


if sys.version_info < (3, 11):
    raise SystemExit(
        "check-ksg-harmonic-revision-v4-preservation-self-test.py requires Python 3.11+"
    )


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-ksg-harmonic-revision-v4-preservation.py"
HISTORICAL_CHECKER_RELATIVE = "scripts/check-ksg-harmonic-revision.py"
CURRENT_CATALOG_SCHEMA_HELPER_RELATIVE = "scripts/json_schema_subset.py"
SOURCE_MATERIALIZER_RELATIVE = "scripts/materialize-public-api-source.sh"
COMPONENT_SHA256 = {
    "scripts/check-method-catalog.py": (
        "6c0fa60625286689107875fcecff52c794ad74d2782449c2dcc84106d4442238"
    ),
    "scripts/check-method-catalog-self-test.py": (
        "6614f0424747d959a4ec1326f4bcacccd88569543a47e7b2ed06969ca4798aac"
    ),
    CURRENT_CATALOG_SCHEMA_HELPER_RELATIVE: (
        "067e6d6b10d33f5b9c1bab6bc621735267a06f2461d6c0da3c8342ac8bd391a6"
    ),
    HISTORICAL_CHECKER_RELATIVE: (
        "cf4692597bc49448d520580d96e1e6d23b4fc65834539095152bb561ec6450e9"
    ),
    "scripts/check-ksg-harmonic-revision-self-test.py": (
        "2abbfe7a54e0c2e3263f3dbe1b8776b197ae13cd8fedacc6d1cc1997f94ee6f0"
    ),
    SOURCE_MATERIALIZER_RELATIVE: (
        "b395f9deca3340f8a631f7de52b4998c970bad75fa6f5b2b96c3f2e620b4f1b6"
    ),
}
COMPONENT_ROSTER_SHA256 = (
    "d882ae3842815a2aac7808e51f5b29d7385276bbc3a0ca89e06d70d1020f9545"
)
SUCCESS_LINE = (
    "KSG revision-4 preservation check passed: 6 pinned components; "
    "5 live-applicable historical scoped routes x normal/-O; 1 superseded live route "
    "retained by exact-tree replay; 2 current catalog authorities x "
    "normal/-O; exact status/stdout/stderr parity\n"
)
HISTORICAL_REPLAY_SUCCESS_LINE = (
    "KSG revision-4 exact-tree mutation replay passed: pinned SHA-1 commit/tree; "
    "241 full-suite and 147 claim-suite mutations x normal/-O; exact "
    "status/stdout/stderr parity\n"
)
FAILURE_PREFIX = "KSG revision-4 preservation check failed: "
EXPECTED_MUTATIONS = 35


class SelfTestError(RuntimeError):
    """A hostile test did not exercise the expected fail-closed path."""


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=True,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in (
        "PYTHONHOME",
        "PYTHONINSPECT",
        "PYTHONOPTIMIZE",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONUSERBASE",
    ):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def run_checker(
    checker: Path,
    repo_root: Path,
    *,
    optimized: bool,
    arguments: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[bytes]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(
        (
            "-I",
            "-S",
            "-B",
            str(checker),
            "--repo-root",
            str(repo_root),
            *arguments,
        )
    )
    return subprocess.run(
        command,
        cwd=ROOT,
        env=child_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=900,
    )


def require_baseline() -> None:
    cases = (
        ((), SUCCESS_LINE, "default"),
        (
            ("--historical-tree-replay",),
            HISTORICAL_REPLAY_SUCCESS_LINE,
            "historical-tree-replay",
        ),
    )
    for arguments, expected_stdout, label in cases:
        outputs: list[bytes] = []
        for optimized in (False, True):
            result = run_checker(
                CHECKER,
                ROOT,
                optimized=optimized,
                arguments=arguments,
            )
            if (
                result.returncode != 0
                or result.stderr != b""
                or result.stdout != expected_stdout.encode()
            ):
                mode = "optimized" if optimized else "normal"
                fail(
                    f"{label} baseline failed in {mode} mode: "
                    f"status={result.returncode}; stdout={result.stdout!r}; "
                    f"stderr={result.stderr!r}"
                )
            outputs.append(result.stdout)
        if outputs[0] != outputs[1]:
            fail(f"{label} baseline normal/-O output parity drifted")


def require_failure(
    checker: Path,
    repo_root: Path,
    mutation: str,
    expected_fragment: str,
    *,
    arguments: tuple[str, ...] = (),
) -> None:
    for optimized in (False, True):
        result = run_checker(
            checker,
            repo_root,
            optimized=optimized,
            arguments=arguments,
        )
        diagnostics = result.stderr.decode("utf-8", errors="replace").splitlines()
        if (
            result.returncode != 1
            or result.stdout != b""
            or len(diagnostics) != 1
            or not diagnostics[0].startswith(FAILURE_PREFIX)
            or expected_fragment not in diagnostics[0]
        ):
            mode = "optimized" if optimized else "normal"
            fail(
                f"{mutation}: did not fail through the intended contract in {mode} "
                f"mode: status={result.returncode}; stdout={result.stdout!r}; "
                f"stderr={result.stderr!r}"
            )


def replace_once(source: str, old: str, new: str, mutation: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{mutation}: replacement anchor occurs {count} times")
    return source.replace(old, new, 1)


def source_mutation(
    source: str,
    mutation: str,
    old: str,
    new: str,
    expected_fragment: str,
    *,
    arguments: tuple[str, ...] = (),
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-v4-preservation-source-"
    ) as directory:
        checker = Path(directory) / "mutated-preservation.py"
        checker.write_text(
            replace_once(source, old, new, mutation),
            encoding="utf-8",
        )
        require_failure(
            checker,
            ROOT,
            mutation,
            expected_fragment,
            arguments=arguments,
        )


def copy_components(destination: Path) -> None:
    for relative in COMPONENT_SHA256:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def component_mutations() -> list[str]:
    killed: list[str] = []
    for relative in COMPONENT_SHA256:
        mutation = f"component-bytes-{Path(relative).name}"
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-v4-preservation-component-"
        ) as directory:
            repo_root = Path(directory)
            copy_components(repo_root)
            target = repo_root / relative
            target.write_bytes(
                target.read_bytes() + b"\n# hostile component mutation\n"
            )
            require_failure(
                CHECKER,
                repo_root,
                mutation,
                f"pinned component SHA-256 mismatch: {relative}",
            )
        killed.append(mutation)

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-v4-preservation-symlink-"
    ) as directory:
        repo_root = Path(directory)
        copy_components(repo_root)
        target = repo_root / HISTORICAL_CHECKER_RELATIVE
        replacement = target.with_name("historical-checker-target.py")
        target.rename(replacement)
        target.symlink_to(replacement.name)
        mutation = "component-symlink-substitution"
        require_failure(
            CHECKER,
            repo_root,
            mutation,
            "component is not a regular non-symlink file",
        )
        killed.append(mutation)

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-v4-preservation-hardlink-"
    ) as directory:
        repo_root = Path(directory)
        copy_components(repo_root)
        target = repo_root / HISTORICAL_CHECKER_RELATIVE
        os.link(target, target.with_name("historical-checker-hardlink.py"))
        mutation = "component-hardlink-substitution"
        require_failure(
            CHECKER,
            repo_root,
            mutation,
            "component has an unexpected hard-link count",
        )
        killed.append(mutation)
    return killed


def repin_historical_checker(source: str, fake_bytes: bytes, mutation: str) -> str:
    old_hash = COMPONENT_SHA256[HISTORICAL_CHECKER_RELATIVE]
    new_hash = hashlib.sha256(fake_bytes).hexdigest()
    rebound = replace_once(source, old_hash, new_hash, mutation)
    component_map = dict(COMPONENT_SHA256)
    component_map[HISTORICAL_CHECKER_RELATIVE] = new_hash
    return replace_once(
        rebound,
        COMPONENT_ROSTER_SHA256,
        canonical_sha256(component_map),
        mutation,
    )


def substituted_child_mutation(
    source: str,
    mutation: str,
    fake_bytes: bytes,
    expected_fragment: str,
) -> None:
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-ksg-v4-preservation-child-"
    ) as directory:
        repo_root = Path(directory)
        copy_components(repo_root)
        (repo_root / HISTORICAL_CHECKER_RELATIVE).write_bytes(fake_bytes)
        checker = repo_root / "scripts/mutated-preservation.py"
        checker.write_text(
            repin_historical_checker(source, fake_bytes, mutation),
            encoding="utf-8",
        )
        require_failure(checker, repo_root, mutation, expected_fragment)


def main() -> int:
    try:
        if not (
            sys.flags.isolated == 1
            and sys.flags.safe_path
            and sys.flags.no_site == 1
            and sys.flags.ignore_environment == 1
            and sys.dont_write_bytecode
        ):
            fail("self-test requires Python 3.11+ invoked with -I -S -B")
        source = CHECKER.read_text(encoding="utf-8")
        require_baseline()
        killed: list[str] = []

        roster_mutations = (
            (
                "route-roster-remove",
                '    "--source-only",\n',
                "",
            ),
            (
                "route-roster-reorder",
                '    "--exact-only",\n    "--binary64-only",\n',
                '    "--binary64-only",\n    "--exact-only",\n',
            ),
            (
                "route-roster-duplicate",
                '    "--claim-only",\n',
                '    "--claim-only",\n    "--claim-only",\n',
            ),
            (
                "route-roster-add-historical-catalog",
                '    "--enclosure-only",\n',
                '    "--enclosure-only",\n    "--catalog-only",\n',
            ),
        )
        for mutation, old, new in roster_mutations:
            source_mutation(
                source,
                mutation,
                old,
                new,
                "historical scoped-route roster drifted",
            )
            killed.append(mutation)

        source_mutation(
            source,
            "route-roster-hash",
            "07318eda33eeb92a2595be740224b321675933e249bdcb3639904ef3c90b7410",
            "17318eda33eeb92a2595be740224b321675933e249bdcb3639904ef3c90b7410",
            "historical scoped-route roster drifted",
        )
        killed.append("route-roster-hash")

        source_mutation(
            source,
            "superseded-route-roster-hash",
            "1b5a7e15d0acfc691a3245b30a6ed03d44a90db62ee81f9f3c7f96169c268244",
            "0b5a7e15d0acfc691a3245b30a6ed03d44a90db62ee81f9f3c7f96169c268244",
            "superseded live-route roster or rationale drifted",
        )
        killed.append("superseded-route-roster-hash")

        source_mutation(
            source,
            "superseded-route-rationale",
            "Superseded on the live descendant by six separately scoped and reviewed ",
            "Superseded without a reviewed scope by six ",
            "superseded live-route roster or rationale drifted",
        )
        killed.append("superseded-route-rationale")

        source_mutation(
            source,
            "component-roster-hash",
            COMPONENT_ROSTER_SHA256,
            "4ab07bce3de7ddac991234367345bff2d1bb7b5e8f03e0ec3ec09a6ab9088c7a",
            "pinned component roster or digest drifted",
        )
        killed.append("component-roster-hash")

        source_mutation(
            source,
            "component-leaf-hash",
            COMPONENT_SHA256[HISTORICAL_CHECKER_RELATIVE],
            "df4692597bc49448d520580d96e1e6d23b4fc65834539095152bb561ec6450e9",
            "pinned component roster or digest drifted",
        )
        killed.append("component-leaf-hash")

        source_mutation(
            source,
            "historical-source-roster-hash",
            "90ab1cc556319c5bb3dc76b3b193bb5ca31418dbcf67c10a837f948f1a95d46f",
            "00ab1cc556319c5bb3dc76b3b193bb5ca31418dbcf67c10a837f948f1a95d46f",
            "historical source commit/tree/object-format roster drifted",
        )
        killed.append("historical-source-roster-hash")

        source_mutation(
            source,
            "historical-source-commit",
            "cb3f58f0b190454cb3f1090de8798261ec78f194",
            "db3f58f0b190454cb3f1090de8798261ec78f194",
            "historical source commit/tree/object-format roster drifted",
        )
        killed.append("historical-source-commit")

        source_mutation(
            source,
            "historical-source-tree",
            "8070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
            "9070e0d3afbbd27d7381825f950ae6ff97ae7cf0",
            "historical source commit/tree/object-format roster drifted",
        )
        killed.append("historical-source-tree")

        source_mutation(
            source,
            "descendant-child-flags",
            'PYTHON_CHILD_FLAGS = ("-S", "-B")',
            'PYTHON_CHILD_FLAGS = ("-B",)',
            "descendant child-interpreter flag roster drifted",
        )
        killed.append("descendant-child-flags")

        source_mutation(
            source,
            "historical-replay-flags",
            'HISTORICAL_REPLAY_FLAGS = ("-I", "-S", "-B")',
            'HISTORICAL_REPLAY_FLAGS = ("-I", "-B")',
            "historical replay interpreter flag roster drifted",
        )
        killed.append("historical-replay-flags")

        source_mutation(
            source,
            "isolated-git-environment",
            '        "GIT_GRAFT_FILE": os.devnull,\n',
            "",
            "isolated Git environment roster drifted",
        )
        killed.append("isolated-git-environment")

        source_mutation(
            source,
            "historical-checker-self-test-substitution",
            "            HISTORICAL_CHECKER_RELATIVE,\n            arguments,\n            optimized=False,\n",
            "            HISTORICAL_SELF_TEST_RELATIVE,\n            arguments,\n            optimized=False,\n",
            "child status drifted",
        )
        killed.append("historical-checker-self-test-substitution")

        source_mutation(
            source,
            "catalog-execution-roster-substitution",
            "CURRENT_CATALOG_COMMANDS = (\n    CURRENT_CATALOG_CHECKER_RELATIVE,\n    CURRENT_CATALOG_SELF_TEST_RELATIVE,\n)",
            "CURRENT_CATALOG_COMMANDS = (\n    CURRENT_CATALOG_SELF_TEST_RELATIVE,\n    CURRENT_CATALOG_SELF_TEST_RELATIVE,\n)",
            "current catalog execution roster drifted",
        )
        killed.append("catalog-execution-roster-substitution")

        source_mutation(
            source,
            "claim-output-authority",
            "integration_no_go; 72 mapped files; 36 historical hashes; ",
            "integration_go; 72 mapped files; 36 historical hashes; ",
            "exact stdout drifted",
        )
        killed.append("claim-output-authority")

        source_mutation(
            source,
            "historical-route-call-erasure",
            "    route_receipt = run_historical_routes(repo_root)\n",
            "    route_receipt = ()\n",
            "historical scoped-route execution receipt drifted",
        )
        killed.append("historical-route-call-erasure")

        source_mutation(
            source,
            "current-catalog-call-erasure",
            "    catalog_receipt = run_current_catalog_authority(repo_root)\n",
            "    catalog_receipt = ()\n",
            "current catalog execution receipt drifted",
        )
        killed.append("current-catalog-call-erasure")

        source_mutation(
            source,
            "historical-tree-call-erasure",
            "    replay_receipt = run_historical_tree_replay(repo_root)\n",
            "    replay_receipt = ()\n",
            "historical exact-tree execution receipt drifted",
            arguments=("--historical-tree-replay",),
        )
        killed.append("historical-tree-call-erasure")

        source_mutation(
            source,
            "historical-full-suite-erasure",
            '        ((), EXPECTED_HISTORICAL_SELF_TEST_STDOUT, "historical full mutation suite"),\n',
            "",
            "historical exact-tree execution receipt drifted",
            arguments=("--historical-tree-replay",),
        )
        killed.append("historical-full-suite-erasure")

        source_mutation(
            source,
            "historical-claim-suite-erasure",
            (
                "        (\n"
                '            ("--claim-only",),\n'
                "            EXPECTED_HISTORICAL_CLAIM_SELF_TEST_STDOUT,\n"
                '            "historical claim mutation suite",\n'
                "        ),\n"
            ),
            "",
            "historical exact-tree execution receipt drifted",
            arguments=("--historical-tree-replay",),
        )
        killed.append("historical-claim-suite-erasure")

        killed.extend(component_mutations())

        substituted_child_mutation(
            source,
            "child-nonzero-status",
            b"#!/usr/bin/env python3\nraise SystemExit(7)\n",
            "child status drifted",
        )
        killed.append("child-nonzero-status")

        substituted_child_mutation(
            source,
            "child-stderr",
            (
                b"#!/usr/bin/env python3\n"
                b"import sys\n"
                b"sys.stderr.write('hostile stderr\\n')\n"
            ),
            "child stderr is not empty",
        )
        killed.append("child-stderr")

        substituted_child_mutation(
            source,
            "child-exact-output",
            b"#!/usr/bin/env python3\nprint('hostile substituted output')\n",
            "exact stdout drifted",
        )
        killed.append("child-exact-output")

        substituted_child_mutation(
            source,
            "child-normal-optimized-parity",
            (
                b"#!/usr/bin/env python3\n"
                b"import sys\n"
                b"if sys.flags.optimize:\n"
                b"    print('hostile optimized output')\n"
                b"else:\n"
                b"    print('hostile normal output')\n"
            ),
            "normal/-O stdout parity drifted",
        )
        killed.append("child-normal-optimized-parity")

        if len(killed) != EXPECTED_MUTATIONS:
            fail(
                f"mutation count drifted: expected {EXPECTED_MUTATIONS}, got {len(killed)}"
            )
        if len(killed) != len(set(killed)):
            fail("mutation names are not unique")
    except (OSError, SelfTestError, subprocess.SubprocessError, ValueError) as error:
        print(
            f"KSG revision-4 preservation self-test failed: {error}",
            file=sys.stderr,
        )
        return 1
    print(
        "KSG revision-4 preservation self-test passed: "
        f"{len(killed)} hostile mutations rejected; default and historical-tree "
        "baselines normal/-O exact"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
