#!/usr/bin/env python3
"""Baseline-first hostile tests for the KSG Git phase-isolation checker."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parent.parent
CHECKER_RELATIVE = "scripts/check-ksg-phase-isolation.py"
SELF_RELATIVE = "scripts/check-ksg-phase-isolation-self-test.py"
POLICY_RELATIVE = "audit/evidence/ksg-rev4-phase-path-policy.json"
CORRECTIVE_EVIDENCE = "audit/evidence/ksg-rev4-ci-corrective-phase-2026-07-28.md"
INTEGRATION_ANCHOR = "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"
CURRENT_ANCHOR = "dc7b8de0a87443ef2bcde71b19938642f1af2197"
CORRECTIVE_PATHS = frozenset(
    {
        ".github/workflows/ci.yml",
        "CHANGELOG.md",
        "ECOSYSTEM_CAPABILITIES.md",
        "FORMAL_TOOL_ADOPTION_AUDIT.md",
        "METHODS.md",
        (
            "audit/evidence/"
            "certified-sxpid2-cpython311-loaded-execution-incident-20260728.md"
        ),
        CORRECTIVE_EVIDENCE,
        POLICY_RELATIVE,
        "audit/formal/latex/certified-sxpid2-executable-assurance.tex",
        "audit/formal/latex/formal-tool-adoption-audit.tex",
        "audit/tools/certified-sxpid/README.md",
        (
            "audit/tools/certified-sxpid/scripts/"
            "check-independent-verifier.py"
        ),
        "audit/tools/certified-sxpid/scripts/verify_certificate.py",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/bindings-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/claim-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/evidence-matrix-v3.md",
        (
            "claims/SX-CERTIFIED-AVERAGED-PID2-001/failures/"
            "retained-negative-controls-v3.md"
        ),
        (
            "claims/SX-CERTIFIED-AVERAGED-PID2-001/formal/"
            "theorem-evidence-map-v3.md"
        ),
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/obligations-v3.md",
        "claims/SX-CERTIFIED-AVERAGED-PID2-001/revision-index.md",
        "crates/pid-core/identity/software-identity-reference-v1.json",
        "crates/pid-core/src/stats.rs",
        (
            "crates/pid-core/tests/fixtures/"
            "generate-ksg-local-arithmetic-oracle.py.snapshot"
        ),
        "ecosystem-capabilities.json",
        "method-catalog.json",
        "output/pdf/certified-sxpid2-executable-assurance.pdf",
        "output/pdf/formal-tool-adoption-audit.pdf",
        "scripts/README.md",
        "scripts/check-certified-sxpid2-claim-self-test.py",
        "scripts/check-certified-sxpid2-claim.py",
        "scripts/check-ecosystem-capabilities.py",
        "scripts/check-ksg-harmonic-revision-self-test.py",
        "scripts/check-ksg-harmonic-revision.py",
        CHECKER_RELATIVE,
        SELF_RELATIVE,
        "scripts/verify-package-archives.sh",
    }
)
GENERATED_BEGIN = "# BEGIN GENERATED PHASE FACTS"
GENERATED_END = "# END GENERATED PHASE FACTS"


class SelfTestError(RuntimeError):
    """The checker accepted a mutation or the self-test lost custody."""


@dataclass(frozen=True)
class Backup:
    exists: bool
    raw: bytes
    mode: int


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


def python_command(
    script: Path, *arguments: str, force_optimized: bool | None = None
) -> list[str]:
    optimized = sys.flags.optimize > 0 if force_optimized is None else force_optimized
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend((str(script), *arguments))
    return command


def run(
    command: list[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
        }
    )
    if environment_overrides is not None:
        environment.update(environment_overrides)
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        input=input_bytes,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_checker(
    root: Path,
    *,
    expect_success: bool,
    expected_fragment: str = "",
    force_optimized: bool | None = None,
    arguments: tuple[str, ...] = (),
    environment_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    checker = root / CHECKER_RELATIVE
    process = run(
        python_command(
            checker,
            *arguments,
            force_optimized=force_optimized,
        ),
        cwd=root,
        environment_overrides=environment_overrides,
    )
    stdout = process.stdout.decode("utf-8", errors="replace")
    stderr = process.stderr.decode("utf-8", errors="replace")
    combined = stdout + stderr
    if expect_success:
        require(
            process.returncode == 0 and "OK: KSG phase provenance only" in stdout,
            "unmodified phase checker did not pass:\n" + combined,
        )
    else:
        require(
            process.returncode != 0,
            "phase checker falsely accepted a hostile mutation",
        )
        require(
            expected_fragment in combined,
            (
                f"phase checker rejected a mutation for the wrong reason; "
                f"missing {expected_fragment!r}:\n{combined}"
            ),
        )
    return process


def current_facts(root: Path) -> dict[str, object]:
    checker = root / CHECKER_RELATIVE
    process = run(
        python_command(
            checker,
            "--emit-current-facts-json",
            force_optimized=False,
        ),
        cwd=root,
    )
    require(
        process.returncode == 0,
        "cannot collect diagnostic phase facts:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    try:
        facts = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise SelfTestError("diagnostic phase facts are not JSON") from error
    require(
        isinstance(facts, dict)
        and facts.get("schema") == "pid-rs/ksg-phase-current-facts"
        and facts.get("diagnostic_only") is True,
        "diagnostic phase facts have the wrong typed envelope",
    )
    return facts


def generated_block(root: Path) -> str:
    checker = root / CHECKER_RELATIVE
    process = run(
        python_command(
            checker,
            "--emit-current-facts-python",
            force_optimized=False,
        ),
        cwd=root,
    )
    require(
        process.returncode == 0,
        "cannot generate rebased phase facts:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    try:
        block = process.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise SelfTestError("generated phase block is not UTF-8") from error
    require(
        block.startswith(GENERATED_BEGIN)
        and block.endswith(GENERATED_END)
        and block.count(GENERATED_BEGIN) == 1
        and block.count(GENERATED_END) == 1,
        "generated phase block has invalid boundaries",
    )
    return block


def rebase_checker(root: Path) -> None:
    checker = root / CHECKER_RELATIVE
    source = checker.read_text(encoding="utf-8")
    begin_marker = GENERATED_BEGIN + "\n"
    end_marker = GENERATED_END + "\n"
    begin = source.find(begin_marker)
    end_start = source.find(end_marker, begin + len(begin_marker))
    require(
        begin >= 0
        and end_start > begin
        and source.find(begin_marker, begin + len(begin_marker)) < 0
        and source.find(end_marker, end_start + len(end_marker)) < 0,
        "checker generated phase boundaries are not unique",
    )
    end = end_start + len(GENERATED_END)
    replacement = generated_block(root)
    checker.write_text(
        source[:begin] + replacement + source[end:],
        encoding="utf-8",
        newline="\n",
    )


def backup(root: Path, relatives: Iterable[str]) -> dict[str, Backup]:
    result: dict[str, Backup] = {}
    for relative in relatives:
        path = root / relative
        if path.is_symlink():
            raise SelfTestError(f"pristine mutation target is a symlink: {relative}")
        if path.exists():
            metadata = path.stat()
            require(
                stat.S_ISREG(metadata.st_mode),
                f"mutation target is not regular: {relative}",
            )
            result[relative] = Backup(
                exists=True,
                raw=path.read_bytes(),
                mode=stat.S_IMODE(metadata.st_mode),
            )
        else:
            result[relative] = Backup(exists=False, raw=b"", mode=0)
    return result


def restore(root: Path, saved: dict[str, Backup]) -> None:
    for relative, item in saved.items():
        path = root / relative
        if path.is_symlink() or path.exists():
            if path.is_dir() and not path.is_symlink():
                raise SelfTestError(
                    f"mutation unexpectedly created a directory: {relative}"
                )
            path.unlink()
        if item.exists:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.raw)
            path.chmod(item.mode)


def replace_once(path: Path, old: bytes, new: bytes) -> None:
    raw = path.read_bytes()
    require(raw.count(old) == 1, f"mutation anchor is not unique in {path}")
    path.write_bytes(raw.replace(old, new, 1))


def append_bytes(path: Path, raw: bytes) -> None:
    path.write_bytes(path.read_bytes() + raw)


def common_git_dir(root: Path) -> Path:
    process = run(["git", "rev-parse", "--git-common-dir"], cwd=root)
    require(process.returncode == 0, "cannot resolve temporary Git common directory")
    try:
        value = process.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise SelfTestError("temporary Git common directory is not UTF-8") from error
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve(strict=True)


def backup_absolute(paths: Iterable[Path]) -> dict[Path, Backup]:
    result: dict[Path, Backup] = {}
    for path in paths:
        if path.is_symlink():
            raise SelfTestError(f"pristine metadata target is a symlink: {path}")
        if path.exists():
            metadata = path.stat()
            require(
                stat.S_ISREG(metadata.st_mode),
                f"metadata target is not regular: {path}",
            )
            result[path] = Backup(
                exists=True,
                raw=path.read_bytes(),
                mode=stat.S_IMODE(metadata.st_mode),
            )
        else:
            result[path] = Backup(exists=False, raw=b"", mode=0)
    return result


def restore_absolute(saved: dict[Path, Backup]) -> None:
    for path, item in saved.items():
        if path.is_symlink() or path.exists():
            require(not path.is_dir(), f"metadata mutation created a directory: {path}")
            path.unlink()
        if item.exists:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(item.raw)
            path.chmod(item.mode)


def metadata_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[Path],
    mutate: Callable[[], None],
    expected_fragment: str,
) -> None:
    saved = backup_absolute(paths)
    try:
        mutate()
        run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore_absolute(saved)
    run_checker(root, expect_success=True)


def metadata_invariance(
    root: Path,
    *,
    label: str,
    paths: Iterable[Path],
    mutate: Callable[[], None],
) -> None:
    saved = backup_absolute(paths)
    try:
        before = current_facts(root)
        mutate()
        run_checker(root, expect_success=True)
        after = current_facts(root)
        require(
            after == before,
            "irrelevant local metadata changed emitted candidate facts",
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore_absolute(saved)
    run_checker(root, expect_success=True)


def baseline_first_rebased_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[str],
    mutate: Callable[[Path], None],
    first_fragment: str,
    semantic_fragment: str,
    repin_stats_for_downstream: bool = False,
    repin_package_script_for_downstream: bool = False,
) -> None:
    touched = tuple(dict.fromkeys((*paths, CHECKER_RELATIVE)))
    bypass_corrective_policy = not set(paths).issubset(CORRECTIVE_PATHS)
    saved = backup(root, touched)
    try:
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=(
                "candidate anchor delta differs from the separately reviewed A/M "
                "path policy"
                if bypass_corrective_policy
                else first_fragment
            ),
        )
        if bypass_corrective_policy:
            replace_once(
                root / CHECKER_RELATIVE,
                b"        actual_delta == policy_delta,\n",
                b"        True,\n",
            )
        if repin_stats_for_downstream:
            require(
                "crates/pid-core/src/stats.rs" in paths,
                "stats digest repin requested without the stats.rs mutation path",
            )
            mutated_digest = hashlib.sha256(
                (root / "crates/pid-core/src/stats.rs").read_bytes()
            ).hexdigest()
            replace_once(
                root / CHECKER_RELATIVE,
                (
                    b"PACKAGE_STATS_SHA256 = (\n"
                    b'    "204080f7a8854cc390754907e56aff31321853bf350542ea9c8b570038920a8e"\n'
                    b")"
                ),
                (
                    b"PACKAGE_STATS_SHA256 = (\n"
                    + f'    "{mutated_digest}"\n'.encode("ascii")
                    + b")"
                ),
            )
        if repin_package_script_for_downstream:
            require(
                "scripts/verify-package-archives.sh" in paths,
                "package-script digest repin requested without its mutation path",
            )
            mutated_digest = hashlib.sha256(
                (root / "scripts/verify-package-archives.sh").read_bytes()
            ).hexdigest()
            replace_once(
                root / CHECKER_RELATIVE,
                (
                    b"PACKAGE_ARCHIVE_SCRIPT_SHA256 = (\n"
                    b'    "13bf728a06c5a22289a5cdd0ba2a229440d584108918b256898a4fac4252f256"\n'
                    b")"
                ),
                (
                    b"PACKAGE_ARCHIVE_SCRIPT_SHA256 = (\n"
                    + f'    "{mutated_digest}"\n'.encode("ascii")
                    + b")"
                ),
            )
        rebase_checker(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=semantic_fragment,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def hostile_policy_repin_attack(
    root: Path,
    *,
    label: str,
    mutate: Callable[[Path], None],
    semantic_fragment: str,
) -> None:
    saved = backup(root, (POLICY_RELATIVE, CHECKER_RELATIVE))
    checker = root / CHECKER_RELATIVE
    policy = root / POLICY_RELATIVE
    try:
        old_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment="policy digest differs",
        )
        new_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode("ascii")
        replace_once(checker, old_digest, new_digest)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=semantic_fragment,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def simple_attack(
    root: Path,
    *,
    label: str,
    paths: Iterable[str],
    mutate: Callable[[Path], None],
    expected_fragment: str,
    force_optimized: bool | None = None,
) -> None:
    saved = backup(root, paths)
    try:
        mutate(root)
        run_checker(
            root,
            expect_success=False,
            expected_fragment=expected_fragment,
            force_optimized=force_optimized,
        )
    except SelfTestError as error:
        raise SelfTestError(f"{label}: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)


def optimization_preflight(temporary: Path) -> None:
    sentinel = temporary / "optimization-sentinel.py"
    sentinel.write_text(
        "assert False, 'optimization sentinel was not removed'\n",
        encoding="utf-8",
        newline="\n",
    )
    normal = run(python_command(sentinel, force_optimized=False), cwd=temporary)
    optimized = run(python_command(sentinel, force_optimized=True), cwd=temporary)
    require(
        normal.returncode != 0 and optimized.returncode == 0,
        "child interpreter does not distinguish normal and optimized assertions",
    )


def static_source_preflight() -> None:
    for relative in (CHECKER_RELATIVE, SELF_RELATIVE):
        path = ROOT / relative
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            raise SelfTestError(
                f"cannot parse source model {relative}: {error}"
            ) from error
        assert_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
        require(
            not assert_nodes,
            f"{relative} contains an optimization-removable assert statement",
        )


def clone_candidate(source: Path, destination: Path, facts: dict[str, object]) -> None:
    process = run(
        [
            "git",
            "clone",
            "--no-local",
            "--quiet",
            "--no-checkout",
            str(source),
            str(destination),
        ],
        cwd=source,
    )
    require(
        process.returncode == 0,
        "cannot create isolated self-test clone:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    checkout = run(
        ["git", "checkout", "--quiet", "--detach", CURRENT_ANCHOR],
        cwd=destination,
    )
    require(
        checkout.returncode == 0,
        "cannot check out exact self-test anchor:\n"
        + checkout.stderr.decode("utf-8", errors="replace"),
    )
    changed = facts.get("changed_paths")
    require(
        isinstance(changed, list)
        and changed
        and all(isinstance(path, str) and path for path in changed),
        "diagnostic changed-path inventory is invalid",
    )
    for relative in changed:
        source_path = source / relative
        destination_path = destination / relative
        require(
            source_path.is_file() and not source_path.is_symlink(),
            f"candidate overlay source is not a regular file: {relative}",
        )
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)


def anchor_delta_paths(facts: dict[str, object]) -> tuple[str, ...]:
    raw_delta = facts.get("anchor_delta")
    require(isinstance(raw_delta, list) and raw_delta, "anchor delta facts are invalid")
    result: list[str] = []
    for item in raw_delta:
        require(
            isinstance(item, dict)
            and set(item) == {"path", "status"}
            and isinstance(item.get("path"), str)
            and item.get("status") in {"A", "M"},
            "anchor delta fact has an invalid shape",
        )
        result.append(item["path"])
    require(
        tuple(result) == tuple(sorted(result)) and len(result) == len(set(result)),
        "anchor delta facts are not sorted and duplicate-free",
    )
    return tuple(result)


def write_candidate_tree(root: Path, facts: dict[str, object]) -> str:
    with tempfile.TemporaryDirectory(prefix="pid-rs-phase-index.") as temporary_raw:
        index_path = Path(temporary_raw) / "index"
        environment = {"GIT_INDEX_FILE": str(index_path)}
        read_tree = run(
            ["git", "read-tree", CURRENT_ANCHOR],
            cwd=root,
            environment_overrides=environment,
        )
        require(read_tree.returncode == 0, "cannot seed external candidate index")
        paths = anchor_delta_paths(facts)
        stage = run(
            ["git", "add", "--", *paths],
            cwd=root,
            environment_overrides=environment,
        )
        require(
            stage.returncode == 0,
            "cannot stage exact policy paths in external candidate index:\n"
            + stage.stderr.decode("utf-8", errors="replace"),
        )
        write_tree = run(
            ["git", "write-tree"],
            cwd=root,
            environment_overrides=environment,
        )
        require(write_tree.returncode == 0, "cannot write external candidate tree")
        tree = write_tree.stdout.decode("ascii", errors="strict").strip()
        require(len(tree) == 40, "external candidate tree id has the wrong shape")
        return tree


def write_checkpoint_commit(root: Path, tree: str, parent: str) -> str:
    process = run(
        ["git", "commit-tree", tree, "-p", parent],
        cwd=root,
        input_bytes=b"phase isolation self-test checkpoint\n",
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": "phase-self-test@example.invalid",
            "GIT_AUTHOR_NAME": "Phase Self Test",
            "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": "phase-self-test@example.invalid",
            "GIT_COMMITTER_NAME": "Phase Self Test",
        },
    )
    require(
        process.returncode == 0,
        "cannot create detached self-test checkpoint:\n"
        + process.stderr.decode("utf-8", errors="replace"),
    )
    commit = process.stdout.decode("ascii", errors="strict").strip()
    require(len(commit) == 40, "checkpoint commit id has the wrong shape")
    return commit


def commit_exact_paths(
    root: Path,
    paths: Iterable[str],
    *,
    message: str,
) -> str:
    ordered = tuple(paths)
    require(
        ordered and len(ordered) == len(set(ordered)),
        "commit path inventory must be nonempty and duplicate-free",
    )
    stage = run(["git", "add", "--", *ordered], cwd=root)
    require(
        stage.returncode == 0,
        "cannot stage exact lifecycle paths:\n"
        + stage.stderr.decode("utf-8", errors="replace"),
    )
    staged = run(
        ["git", "diff", "--cached", "--name-only", "-z"],
        cwd=root,
    )
    require(staged.returncode == 0, "cannot inspect staged lifecycle paths")
    observed = tuple(
        item.decode("utf-8", errors="strict")
        for item in staged.stdout.split(b"\0")
        if item
    )
    require(
        set(observed) == set(ordered),
        "staged lifecycle path inventory differs from the exact request",
    )
    commit = run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--no-gpg-sign",
            "--no-verify",
            "--quiet",
            "-m",
            message,
        ],
        cwd=root,
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-02T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": "phase-self-test@example.invalid",
            "GIT_AUTHOR_NAME": "Phase Self Test",
            "GIT_COMMITTER_DATE": "2000-01-02T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": "phase-self-test@example.invalid",
            "GIT_COMMITTER_NAME": "Phase Self Test",
        },
    )
    require(
        commit.returncode == 0,
        "cannot commit exact lifecycle paths:\n"
        + commit.stderr.decode("utf-8", errors="replace"),
    )
    head = run(["git", "rev-parse", "HEAD"], cwd=root)
    require(head.returncode == 0, "cannot resolve lifecycle commit")
    return head.stdout.decode("ascii", errors="strict").strip()


def commit_empty(root: Path, *, message: str) -> str:
    commit = run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "--no-gpg-sign",
            "--no-verify",
            "--quiet",
            "-m",
            message,
        ],
        cwd=root,
        environment_overrides={
            "GIT_AUTHOR_DATE": "2000-01-03T00:00:00+00:00",
            "GIT_AUTHOR_EMAIL": "phase-self-test@example.invalid",
            "GIT_AUTHOR_NAME": "Phase Self Test",
            "GIT_COMMITTER_DATE": "2000-01-03T00:00:00+00:00",
            "GIT_COMMITTER_EMAIL": "phase-self-test@example.invalid",
            "GIT_COMMITTER_NAME": "Phase Self Test",
        },
    )
    require(
        commit.returncode == 0,
        "cannot create empty lifecycle commit:\n"
        + commit.stderr.decode("utf-8", errors="replace"),
    )
    head = run(["git", "rev-parse", "HEAD"], cwd=root)
    require(head.returncode == 0, "cannot resolve empty lifecycle commit")
    return head.stdout.decode("ascii", errors="strict").strip()


def run_checker_model_attacks(root: Path) -> int:
    attacks = 0
    checker = root / CHECKER_RELATIVE

    mutations = (
        (
            "scientific-baseline-commit-pin",
            b'e96122b56c15e895c081379210103d1a26eac25f"',
            b'e96122b56c15e895c081379210103d1a26eac250"',
            "git cat-file",
        ),
        (
            "scientific-baseline-tree-pin",
            b'fee2346732da20af0cde32844fcab527ec2d6c4a"',
            b'fee2346732da20af0cde32844fcab527ec2d6c40"',
            "scientific baseline tree pin mismatch",
        ),
        (
            "delivery-commit-pin",
            b'9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"',
            b'e96122b56c15e895c081379210103d1a26eac25f"',
            "delivery parent tree pin mismatch",
        ),
        (
            "delivery-tree-pin",
            b'13b15a7564fdd52df16e2e4380f6293db4ea4367"',
            b'13b15a7564fdd52df16e2e4380f6293db4ea4360"',
            "delivery parent tree pin mismatch",
        ),
        (
            "formal-anchor-commit-pin",
            b'118e1de6a2d6d2ae33fe7bdc224736257e42a83f"',
            b'118e1de6a2d6d2ae33fe7bdc224736257e42a830"',
            "git cat-file",
        ),
        (
            "formal-anchor-tree-pin",
            b'd02ffc69a7045984c1cf58f3adbd39b7e3af0e89"',
            b'd02ffc69a7045984c1cf58f3adbd39b7e3af0e80"',
            "declared tree pin mismatch",
        ),
        (
            "recovery-anchor-commit-pin",
            b'ca24ab8ebade81a94ffc001531abaf5a5579d5e9"',
            b'ca24ab8ebade81a94ffc001531abaf5a5579d5e0"',
            "git cat-file",
        ),
        (
            "recovery-anchor-tree-pin",
            b'82b0aec08c5fd71b6f67d653f05a32f097745a03"',
            b'82b0aec08c5fd71b6f67d653f05a32f097745a00"',
            "declared tree pin mismatch",
        ),
        (
            "integration-anchor-commit-pin",
            b'a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"',
            b'a9aa60c962261a6e0e6698b05551fbcdbf7bf410"',
            "git cat-file",
        ),
        (
            "integration-anchor-tree-pin",
            b'88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e6f"',
            b'88a8dd7a39fed07fcf4be03f3ec3ae6fd7c17e60"',
            "declared tree pin mismatch",
        ),
        (
            "current-anchor-commit-pin",
            b'dc7b8de0a87443ef2bcde71b19938642f1af2197"',
            b'dc7b8de0a87443ef2bcde71b19938642f1af2190"',
            "git cat-file",
        ),
        (
            "current-anchor-tree-pin",
            b'88b24c0ba4fcad4bd749b9146486143397b6a6eb"',
            b'88b24c0ba4fcad4bd749b9146486143397b6a6e0"',
            "declared tree pin mismatch",
        ),
        (
            "root-gitignore-protected-blob-pin",
            b"918f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
            b"018f4cf153cfa4a0f6e5b4d07bd647e417c06e383e4b580946acbede783873d1",
            "pinned protected baseline fact mismatch: .gitignore",
        ),
    )
    for label, old, new, fragment in mutations:
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new: replace_once(checker, old, new),
            expected_fragment=fragment,
        )
        attacks += 1

    simple_attack(
        root,
        label="optimized-assert-source",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b") -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:\n",
            (
                b") -> tuple[str, int, int, int, int, str | None, GitBinaryIdentity]:\n"
                b"    assert True\n"
            ),
        ),
        expected_fragment="optimization-removable assert",
        force_optimized=True,
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-parallel-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_parallel_semantics()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-ci-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_ci_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-package-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_package_archive_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    simple_attack(
        root,
        label="critical-ecosystem-corrective-gate-removal",
        paths=(CHECKER_RELATIVE,),
        mutate=lambda _root: replace_once(
            checker,
            b"    validate_ecosystem_corrective_firewall()\n",
            b"",
        ),
        expected_fragment="direct top-level critical gate sequence changed",
    )
    attacks += 1

    direct_gate_mutations = (
        (
            "critical-gate-dead-branch",
            b"    validate_parallel_semantics()\n",
            b"    if False:\n        validate_parallel_semantics()\n",
        ),
        (
            "critical-gate-nested-helper",
            b"    validate_parallel_semantics()\n",
            (
                b"    def hidden_parallel_gate() -> None:\n"
                b"        validate_parallel_semantics()\n"
                b"    hidden_parallel_gate()\n"
            ),
        ),
        (
            "critical-gate-try-swallow",
            b"    validate_parallel_semantics()\n",
            (
                b"    try:\n"
                b"        validate_parallel_semantics()\n"
                b"    except PhaseIsolationError:\n"
                b"        pass\n"
            ),
        ),
        (
            "critical-gate-reorder",
            (b"    validate_stats_firewall()\n    validate_parallel_semantics()\n"),
            (b"    validate_parallel_semantics()\n    validate_stats_firewall()\n"),
        ),
        (
            "repository-context-replay-removal",
            b"    replay_context = validate_repository_context()\n",
            b"    replay_context = repository_context\n",
        ),
    )
    for label, old, new in direct_gate_mutations:
        simple_attack(
            root,
            label=label,
            paths=(CHECKER_RELATIVE,),
            mutate=lambda _root, old=old, new=new: replace_once(checker, old, new),
            expected_fragment="direct top-level critical gate sequence changed",
        )
        attacks += 1
    return attacks


def run_policy_authority_attacks(root: Path) -> int:
    attacks = 0
    policy = root / POLICY_RELATIVE

    hostile_policy_repin_attack(
        root,
        label="policy-authorizes-deletions",
        mutate=lambda _root: replace_once(
            policy,
            b'"deletions_permitted": false',
            b'"deletions_permitted": true',
        ),
        semantic_fragment="must forbid every deletion",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-mechanical-resealing",
        mutate=lambda _root: replace_once(
            policy,
            b'"mechanical_resealing_permitted": false',
            b'"mechanical_resealing_permitted": true',
        ),
        semantic_fragment="phase path policy authority contract",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-deletion-status",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": ".github/workflows/ci.yml",\n'
                b'      "review_class": "verification_wiring",\n'
                b'      "status": "M"'
            ),
            (
                b'"path": ".github/workflows/ci.yml",\n'
                b'      "review_class": "verification_wiring",\n'
                b'      "status": "D"'
            ),
        ),
        semantic_fragment="not classified A or M",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-unknown-review-class",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": "audit/evidence/ksg-rev4-ci-corrective-phase-'
                b'2026-07-28.md",\n'
                b'      "review_class": "corrective_evidence"'
            ),
            (
                b'"path": "audit/evidence/ksg-rev4-ci-corrective-phase-'
                b'2026-07-28.md",\n'
                b'      "review_class": "not_reviewed"'
            ),
        ),
        semantic_fragment="unknown review class",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-workflow-review-class-drift",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": ".github/workflows/ci.yml",\n'
                b'      "review_class": "verification_wiring"'
            ),
            (
                b'"path": ".github/workflows/ci.yml",\n'
                b'      "review_class": "verification_tool"'
            ),
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-corrective-path-count-rationale-drift",
        mutate=lambda _root: replace_once(
            policy,
            b"forty-five-path corrective delta",
            b"forty-four-path corrective delta",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-boundary-replay-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Make ordinary exact-product boundary replay read-only; require an "
                b"explicit evidence-update mode; validate exact dynamic, stable, and "
                b"excluded-field inventories; and bind 51 targeted controls plus the "
                b"exhaustive 276-leaf and 960-leaf sensitivity partitions without "
                b"claiming cross-build, cross-platform, source, executable, or "
                b"dependency identity."
            ),
            b"Permit ordinary boundary replay to replace evidence.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-package-exact-test-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            b"with an exact one-test/one-pass receipt",
            b"without an execution receipt",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-claim-dependency-closure-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"raw-bind the complete retained revision authorities, reviewed "
                b"documentation, executable dependency closure, assurance sources, "
                b"and PDFs; canonically project the certified method and machine "
                b"evidence objects"
            ),
            b"bind only the two source rows",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-package-authenticity-overclaim",
        mutate=lambda _root: replace_once(
            policy,
            b"avoid treating the marker as archive authenticity",
            b"treat the marker as archive authenticity",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-ecosystem-preservation-obligation-erasure",
        mutate=lambda _root: replace_once(
            policy,
            (
                b"Refresh the ecosystem contract's exact current method-catalog "
                b"binding and human rendering while preserving its historical "
                b"semantic projection, consumer inventory, release claims, and "
                b"every other authority binding."
            ),
            b"Refresh the ecosystem contract.",
        ),
        semantic_fragment="review-class rationale/obligation contracts changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-package-script-reclassification",
        mutate=lambda _root: replace_once(
            policy,
            (
                b'"path": "scripts/verify-package-archives.sh",\n'
                b'      "review_class": "package_archive"'
            ),
            (
                b'"path": "scripts/verify-package-archives.sh",\n'
                b'      "review_class": "verification_tool"'
            ),
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-package-script-entry-omission",
        mutate=lambda _root: replace_once(
            policy,
            (
                b',\n    {\n'
                b'      "path": "scripts/verify-package-archives.sh",\n'
                b'      "review_class": "package_archive",\n'
                b'      "status": "M"\n'
                b"    }\n"
                b"  ],"
            ),
            b"\n  ],",
        ),
        semantic_fragment="corrective phase path/status/review-class inventory changed",
    )
    attacks += 1

    hostile_policy_repin_attack(
        root,
        label="policy-anchor-rollback",
        mutate=lambda _root: replace_once(
            policy,
            b'"commit": "dc7b8de0a87443ef2bcde71b19938642f1af2197"',
            b'"commit": "a9aa60c962261a6e0e6698b05551fbcdbf7bf41c"',
        ),
        semantic_fragment="phase path policy anchor value changed at $/commit",
    )
    attacks += 1
    return attacks


def run_json_type_firewall_controls(root: Path) -> int:
    """Exercise type-confusion controls separately from the hostile attacks."""

    controls = 0
    policy = root / POLICY_RELATIVE

    hostile_policy_repin_attack(
        root,
        label="json-type-firewall-schema-revision-boolean",
        mutate=lambda _root: replace_once(
            policy,
            b'"schema_revision": 2',
            b'"schema_revision": true',
        ),
        semantic_fragment="wrong JSON type at $",
    )
    controls += 1

    hostile_policy_repin_attack(
        root,
        label="json-type-firewall-authoritative-integer",
        mutate=lambda _root: replace_once(
            policy,
            b'"authoritative": true',
            b'"authoritative": 1',
        ),
        semantic_fragment="wrong JSON type at $/authoritative",
    )
    controls += 1
    return controls


def run_path_and_custody_attacks(root: Path) -> int:
    attacks = 0
    added_path = CORRECTIVE_EVIDENCE

    simple_attack(
        root,
        label="unreviewed-path-addition",
        paths=("phase-stray.txt",),
        mutate=lambda candidate: (candidate / "phase-stray.txt").write_text(
            "not reviewed\n", encoding="utf-8", newline="\n"
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="allowed-path-removal",
        paths=(added_path,),
        mutate=lambda candidate: (candidate / added_path).unlink(),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="self-test-path-removal",
        paths=(SELF_RELATIVE,),
        mutate=lambda candidate: (candidate / SELF_RELATIVE).unlink(),
        expected_fragment="candidate path is missing",
    )
    attacks += 1

    simple_attack(
        root,
        label="protected-pid2-blob",
        paths=("crates/pid-core/src/pid2.rs",),
        mutate=lambda candidate: append_bytes(
            candidate / "crates/pid-core/src/pid2.rs",
            b"\n// forbidden KSG-phase mutation\n",
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="protected-pid2-mode",
        paths=("crates/pid-core/src/pid2.rs",),
        mutate=lambda candidate: (candidate / "crates/pid-core/src/pid2.rs").chmod(
            0o755
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    forbidden_claim = "claims/PID2-REPRESENTED-SUM-001/phase-injection.md"
    simple_attack(
        root,
        label="forbidden-later-claim",
        paths=(forbidden_claim,),
        mutate=lambda candidate: (
            (candidate / forbidden_claim).parent.mkdir(parents=True, exist_ok=True),
            (candidate / forbidden_claim).write_text(
                "later wave\n", encoding="utf-8", newline="\n"
            ),
        ),
        expected_fragment="separately reviewed A/M path policy",
    )
    attacks += 1

    simple_attack(
        root,
        label="allowed-file-symlink",
        paths=(".github/workflows/ci.yml",),
        mutate=lambda candidate: (
            (candidate / ".github/workflows/ci.yml").unlink(),
            (candidate / ".github/workflows/ci.yml").symlink_to(
                "../../scripts/check-ksg-phase-isolation.py"
            ),
        ),
        expected_fragment="regular non-symlink",
    )
    attacks += 1

    def hardlink_mutation(candidate: Path) -> None:
        target = candidate / ".github/workflows/ci.yml"
        donor = candidate / CORRECTIVE_EVIDENCE
        target.unlink()
        os.link(donor, target)

    simple_attack(
        root,
        label="allowed-file-hardlink",
        paths=(".github/workflows/ci.yml", CORRECTIVE_EVIDENCE),
        mutate=hardlink_mutation,
        expected_fragment="hard-linked candidate file is forbidden",
    )
    attacks += 1
    return attacks


def run_external_tree_custody_tests(
    root: Path,
    facts: dict[str, object],
) -> int:
    tests = 0
    candidate_tree = write_candidate_tree(root, facts)
    checkpoint = write_checkpoint_commit(root, candidate_tree, CURRENT_ANCHOR)
    run_checker(
        root,
        expect_success=True,
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            checkpoint,
        ),
    )
    tests += 1

    head_tree_process = run(["git", "rev-parse", "HEAD^{tree}"], cwd=root)
    require(head_tree_process.returncode == 0, "cannot resolve hostile HEAD tree")
    head_tree = head_tree_process.stdout.decode("ascii", errors="strict").strip()
    run_checker(
        root,
        expect_success=False,
        expected_fragment="staged/checkpoint tree differs",
        arguments=("--expected-candidate-tree", head_tree),
    )
    tests += 1

    wrong_tree_commit = write_checkpoint_commit(root, head_tree, CURRENT_ANCHOR)
    run_checker(
        root,
        expect_success=False,
        expected_fragment="checkpoint commit tree differs",
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            wrong_tree_commit,
        ),
    )
    tests += 1

    parent_process = run(["git", "rev-parse", f"{CURRENT_ANCHOR}^"], cwd=root)
    require(parent_process.returncode == 0, "cannot resolve hostile checkpoint parent")
    wrong_parent = parent_process.stdout.decode("ascii", errors="strict").strip()
    wrong_parent_commit = write_checkpoint_commit(root, candidate_tree, wrong_parent)
    run_checker(
        root,
        expect_success=False,
        expected_fragment="not the exact child of snapshot HEAD",
        arguments=(
            "--expected-candidate-tree",
            candidate_tree,
            "--checkpoint-commit",
            wrong_parent_commit,
        ),
    )
    tests += 1

    run_checker(
        root,
        expect_success=False,
        expected_fragment="requires --expected-candidate-tree",
        arguments=("--checkpoint-commit", checkpoint),
    )
    tests += 1
    return tests


def run_retained_self_reference_boundary(
    root: Path,
    facts: dict[str, object],
) -> int:
    """Retain the coordinated-rebase cut and prove only a pre-pinned tree rejects it."""

    pristine_tree = write_candidate_tree(root, facts)
    pristine_checkpoint = write_checkpoint_commit(root, pristine_tree, CURRENT_ANCHOR)
    saved = backup(root, (POLICY_RELATIVE, CHECKER_RELATIVE))
    checker = root / CHECKER_RELATIVE
    policy = root / POLICY_RELATIVE
    try:
        old_policy_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode(
            "ascii"
        )
        replace_once(
            policy,
            (
                b'"path": "audit/evidence/ksg-rev4-ci-corrective-phase-'
                b'2026-07-28.md",\n'
                b'      "review_class": "corrective_evidence"'
            ),
            (
                b'"path": "audit/evidence/ksg-rev4-ci-corrective-phase-'
                b'2026-07-28.md",\n'
                b'      "review_class": "phase_authority"'
            ),
        )
        new_policy_digest = hashlib.sha256(policy.read_bytes()).hexdigest().encode(
            "ascii"
        )
        replace_once(checker, old_policy_digest, new_policy_digest)
        replace_once(
            checker,
            b'(CORRECTIVE_EVIDENCE, "A", "corrective_evidence"),',
            b'(CORRECTIVE_EVIDENCE, "A", "phase_authority"),',
        )
        rebase_checker(root)

        # This acceptance is the retained negative result: the checker cannot
        # authenticate a coordinated mutation of its own source and policy.
        run_checker(root, expect_success=True)
        attacker_tree = write_candidate_tree(root, facts)
        attacker_checkpoint = write_checkpoint_commit(
            root,
            attacker_tree,
            CURRENT_ANCHOR,
        )
        run_checker(
            root,
            expect_success=True,
            arguments=(
                "--expected-candidate-tree",
                attacker_tree,
                "--checkpoint-commit",
                attacker_checkpoint,
            ),
        )
        run_checker(
            root,
            expect_success=False,
            expected_fragment="staged/checkpoint tree differs",
            arguments=(
                "--expected-candidate-tree",
                pristine_tree,
                "--checkpoint-commit",
                pristine_checkpoint,
            ),
        )
    except SelfTestError as error:
        raise SelfTestError(f"retained-self-reference-boundary: {error}") from error
    finally:
        restore(root, saved)
    run_checker(root, expect_success=True)
    return 1


def run_repository_context_attacks(root: Path) -> int:
    attacks = 0
    common = common_git_dir(root)
    config = common / "config"

    config_attacks = (
        (
            "local-attr-tree",
            ["git", "config", "--local", "attr.tree", CURRENT_ANCHOR],
            "forbidden local Git configuration key: attr.tree",
        ),
        (
            "local-clean-filter",
            ["git", "config", "--local", "filter.phase.clean", "/usr/bin/true"],
            "forbidden local Git configuration key: filter.phase.clean",
        ),
        (
            "local-include",
            ["git", "config", "--local", "include.path", "/tmp/phase-include"],
            "forbidden local Git configuration key: include.path",
        ),
        (
            "local-attributes-file",
            ["git", "config", "--local", "core.attributesFile", "/tmp/phase-attrs"],
            "forbidden local Git configuration key: core.attributesfile",
        ),
        (
            "local-excludes-file",
            ["git", "config", "--local", "core.excludesFile", "/tmp/phase-ignore"],
            "forbidden local Git configuration key: core.excludesfile",
        ),
        (
            "local-fsmonitor",
            ["git", "config", "--local", "core.fsmonitor", "/tmp/phase-fsmonitor"],
            "forbidden local Git configuration key: core.fsmonitor",
        ),
        (
            "local-sparse-index",
            ["git", "config", "--local", "index.sparse", "true"],
            "forbidden local Git configuration key: index.sparse",
        ),
    )
    for label, command, fragment in config_attacks:

        def mutate_config(command: list[str] = command) -> None:
            process = run(command, cwd=root)
            require(process.returncode == 0, f"{label}: cannot mutate local config")

        metadata_attack(
            root,
            label=label,
            paths=(config,),
            mutate=mutate_config,
            expected_fragment=fragment,
        )
        attacks += 1

    info_exclude = common / "info/exclude"
    metadata_invariance(
        root,
        label="info-exclude-match-all-is-irrelevant",
        paths=(info_exclude,),
        mutate=lambda: info_exclude.write_text(
            "*\n",
            encoding="utf-8",
            newline="\n",
        ),
    )
    attacks += 1
    metadata_invariance(
        root,
        label="info-exclude-appended-rule-is-irrelevant",
        paths=(info_exclude,),
        mutate=lambda: append_bytes(info_exclude, b"\nphase-hidden\n"),
    )
    attacks += 1

    simple_attack(
        root,
        label="second-nested-gitignore-source",
        paths=("claims/KSG-INTEGER-HARMONIC-001/.gitignore",),
        mutate=lambda candidate: (
            candidate / "claims/KSG-INTEGER-HARMONIC-001/.gitignore"
        ).write_text(
            "claim-v4.md\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="candidate anchor delta differs",
    )
    attacks += 1

    info_attributes = common / "info/attributes"
    metadata_attack(
        root,
        label="info-attributes-overlay",
        paths=(info_attributes,),
        mutate=lambda: info_attributes.write_text(
            "* filter=phase\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: info/attributes",
    )
    attacks += 1

    worktree_config = common / "config.worktree"
    metadata_attack(
        root,
        label="worktree-config-overlay",
        paths=(worktree_config,),
        mutate=lambda: worktree_config.write_text(
            "[attr]\n\ttree = HEAD\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: config.worktree",
    )
    attacks += 1

    grafts = common / "info/grafts"
    metadata_attack(
        root,
        label="legacy-grafts-overlay",
        paths=(grafts,),
        mutate=lambda: grafts.write_text(
            f"{CURRENT_ANCHOR}\n",
            encoding="utf-8",
            newline="\n",
        ),
        expected_fragment="Git overlay file is forbidden: info/grafts",
    )
    attacks += 1

    with tempfile.TemporaryDirectory(prefix="pid-rs-empty-alternate.") as alternate_raw:
        alternates = common / "objects/info/alternates"
        metadata_attack(
            root,
            label="alternate-object-overlay",
            paths=(alternates,),
            mutate=lambda: alternates.write_text(
                str(Path(alternate_raw).resolve(strict=True)) + "\n",
                encoding="utf-8",
                newline="\n",
            ),
            expected_fragment="Git overlay file is forbidden: objects/info/alternates",
        )
    attacks += 1

    replace_ref = common / f"refs/replace/{CURRENT_ANCHOR}"
    parent = run(["git", "rev-parse", f"{CURRENT_ANCHOR}^"], cwd=root)
    require(parent.returncode == 0, "cannot resolve replacement-ref negative control")
    parent_oid = parent.stdout.decode("ascii", errors="strict").strip()
    metadata_attack(
        root,
        label="replacement-ref-overlay",
        paths=(replace_ref,),
        mutate=lambda: (
            replace_ref.parent.mkdir(parents=True, exist_ok=True),
            replace_ref.write_text(
                parent_oid + "\n",
                encoding="ascii",
                newline="\n",
            ),
        ),
        expected_fragment="Git replacement references are forbidden",
    )
    attacks += 1

    run_checker(
        root,
        expect_success=True,
        environment_overrides={
            "GIT_ATTR_SOURCE": "refs/heads/not-real",
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "core.attributesFile",
            "GIT_CONFIG_VALUE_0": "/tmp/hostile-attributes",
            "GIT_DIR": "/tmp/not-a-repository",
            "GIT_INDEX_FILE": "/tmp/hostile-index",
            "GIT_OBJECT_DIRECTORY": "/tmp/hostile-objects",
        },
    )
    attacks += 1
    return attacks


def committed_candidate(
    source: Path,
    destination: Path,
    facts: dict[str, object],
) -> str:
    clone_candidate(source, destination, facts)
    return commit_exact_paths(
        destination,
        anchor_delta_paths(facts),
        message="phase isolation committed lifecycle fixture",
    )


def run_committed_checker(root: Path) -> subprocess.CompletedProcess[bytes]:
    head_process = run(["git", "rev-parse", "HEAD"], cwd=root)
    tree_process = run(["git", "rev-parse", "HEAD^{tree}"], cwd=root)
    require(
        head_process.returncode == 0 and tree_process.returncode == 0,
        "cannot resolve committed lifecycle HEAD/tree",
    )
    head = head_process.stdout.decode("ascii", errors="strict").strip()
    tree = tree_process.stdout.decode("ascii", errors="strict").strip()
    return run_checker(
        root,
        expect_success=True,
        arguments=(
            "--expected-candidate-tree",
            tree,
            "--checkpoint-commit",
            head,
        ),
    )


def run_lifecycle_history_tests(
    source: Path,
    temporary: Path,
    facts: dict[str, object],
) -> int:
    tests = 0

    clean = temporary / "committed-clean"
    committed_candidate(source, clean, facts)
    process = run_committed_checker(clean)
    require(
        b"lifecycle=committed-descendant" in process.stdout,
        "clean descendant did not report the committed lifecycle",
    )
    tests += 1
    run_checker(
        clean,
        expect_success=False,
        expected_fragment="committed lifecycle requires --expected-candidate-tree",
    )
    tests += 1

    disjoint = temporary / "committed-disjoint-monotone"
    clone_candidate(source, disjoint, facts)
    delta = facts.get("anchor_delta")
    require(isinstance(delta, list), "anchor delta facts are unavailable")
    modified_paths = tuple(
        item["path"]
        for item in delta
        if isinstance(item, dict) and item.get("status") == "M"
    )
    added_paths = tuple(
        item["path"]
        for item in delta
        if isinstance(item, dict) and item.get("status") == "A"
    )
    require(
        modified_paths and added_paths,
        "disjoint monotone lifecycle requires both M and A policy paths",
    )
    commit_exact_paths(
        disjoint,
        modified_paths,
        message="phase isolation exact modified subset",
    )
    commit_empty(
        disjoint,
        message="phase isolation permitted empty transition",
    )
    commit_exact_paths(
        disjoint,
        added_paths,
        message="phase isolation exact delayed added subset",
    )
    run_committed_checker(disjoint)
    tests += 1

    hostile_allowed = temporary / "committed-allowed-hostile-restore"
    allowed_base = committed_candidate(source, hostile_allowed, facts)
    allowed_path = ".github/workflows/ci.yml"
    append_bytes(
        hostile_allowed / allowed_path,
        b"\n# transient fourth workflow edit\n",
    )
    commit_exact_paths(
        hostile_allowed,
        (allowed_path,),
        message="phase isolation allowed-path hostile blob",
    )
    restore_allowed = run(
        ["git", "checkout", allowed_base, "--", allowed_path],
        cwd=hostile_allowed,
    )
    require(restore_allowed.returncode == 0, "cannot restore allowed lifecycle path")
    commit_exact_paths(
        hostile_allowed,
        (allowed_path,),
        message="phase isolation allowed-path exact restoration",
    )
    run_checker(
        hostile_allowed,
        expect_success=False,
        expected_fragment="changed after its exact final transition",
    )
    tests += 1

    draft_added = temporary / "committed-added-draft-restore"
    clone_candidate(source, draft_added, facts)
    draft_path = CORRECTIVE_EVIDENCE
    final_draft_bytes = (draft_added / draft_path).read_bytes()
    (draft_added / draft_path).write_bytes(b"# transient draft claim\n")
    commit_exact_paths(
        draft_added,
        anchor_delta_paths(facts),
        message="phase isolation draft added-path negative control",
    )
    (draft_added / draft_path).write_bytes(final_draft_bytes)
    commit_exact_paths(
        draft_added,
        (draft_path,),
        message="phase isolation final added-path restoration",
    )
    run_checker(
        draft_added,
        expect_success=False,
        expected_fragment="not a monotone composition",
    )
    tests += 1

    reverted = temporary / "committed-final-anchor-final"
    final_base = committed_candidate(source, reverted, facts)
    reverted_path = ".github/workflows/ci.yml"
    checkout_anchor = run(
        ["git", "checkout", CURRENT_ANCHOR, "--", reverted_path],
        cwd=reverted,
    )
    require(checkout_anchor.returncode == 0, "cannot restore anchor lifecycle bytes")
    commit_exact_paths(
        reverted,
        (reverted_path,),
        message="phase isolation forbidden return to anchor",
    )
    checkout_final = run(
        ["git", "checkout", final_base, "--", reverted_path],
        cwd=reverted,
    )
    require(checkout_final.returncode == 0, "cannot restore final lifecycle bytes")
    commit_exact_paths(
        reverted,
        (reverted_path,),
        message="phase isolation second final transition",
    )
    run_checker(
        reverted,
        expect_success=False,
        expected_fragment="changed after its exact final transition",
    )
    tests += 1

    mode_change = temporary / "committed-mode-change-restore"
    mode_base = committed_candidate(source, mode_change, facts)
    mode_path = ".github/workflows/ci.yml"
    (mode_change / mode_path).chmod(0o755)
    commit_exact_paths(
        mode_change,
        (mode_path,),
        message="phase isolation forbidden mode transition",
    )
    restore_mode = run(
        ["git", "checkout", mode_base, "--", mode_path],
        cwd=mode_change,
    )
    require(restore_mode.returncode == 0, "cannot restore final lifecycle mode")
    commit_exact_paths(
        mode_change,
        (mode_path,),
        message="phase isolation exact mode restoration",
    )
    run_checker(
        mode_change,
        expect_success=False,
        expected_fragment="changed after its exact final transition",
    )
    tests += 1

    symlink_change = temporary / "committed-symlink-restore"
    symlink_base = committed_candidate(source, symlink_change, facts)
    symlink_path = ".github/workflows/ci.yml"
    (symlink_change / symlink_path).unlink()
    (symlink_change / symlink_path).symlink_to(
        "../../scripts/check-ksg-phase-isolation.py"
    )
    commit_exact_paths(
        symlink_change,
        (symlink_path,),
        message="phase isolation forbidden symlink transition",
    )
    restore_symlink = run(
        ["git", "checkout", symlink_base, "--", symlink_path],
        cwd=symlink_change,
    )
    require(restore_symlink.returncode == 0, "cannot restore final symlink path")
    commit_exact_paths(
        symlink_change,
        (symlink_path,),
        message="phase isolation exact symlink restoration",
    )
    run_checker(
        symlink_change,
        expect_success=False,
        expected_fragment="forbidden Git delta status 'T'",
    )
    tests += 1

    deletion = temporary / "committed-delete-restore"
    base_commit = committed_candidate(source, deletion, facts)
    added_path = CORRECTIVE_EVIDENCE
    (deletion / added_path).unlink()
    commit_exact_paths(
        deletion,
        (added_path,),
        message="phase isolation deletion negative control",
    )
    restore_path = run(
        ["git", "checkout", base_commit, "--", added_path],
        cwd=deletion,
    )
    require(restore_path.returncode == 0, "cannot restore deleted lifecycle path")
    commit_exact_paths(
        deletion,
        (added_path,),
        message="phase isolation deletion restoration",
    )
    run_checker(
        deletion,
        expect_success=False,
        expected_fragment="history contains forbidden deletion",
    )
    tests += 1

    protected = temporary / "committed-protected-restore"
    protected_base = committed_candidate(source, protected, facts)
    protected_path = "crates/pid-core/src/pid2.rs"
    append_bytes(
        protected / protected_path,
        b"\n// transient forbidden history touch\n",
    )
    commit_exact_paths(
        protected,
        (protected_path,),
        message="phase isolation protected touch negative control",
    )
    restore_protected = run(
        ["git", "checkout", protected_base, "--", protected_path],
        cwd=protected,
    )
    require(
        restore_protected.returncode == 0,
        "cannot restore protected lifecycle path",
    )
    commit_exact_paths(
        protected,
        (protected_path,),
        message="phase isolation protected restoration",
    )
    run_checker(
        protected,
        expect_success=False,
        expected_fragment="history touched non-policy path",
    )
    tests += 1
    return tests


def run_rebased_semantic_attacks(root: Path) -> int:
    attacks = 0

    package_stats = "crates/pid-core/src/stats.rs"
    package_snapshot = (
        "crates/pid-core/tests/fixtures/"
        "generate-ksg-local-arithmetic-oracle.py.snapshot"
    )
    canonical_generator = "scripts/generate-ksg-local-arithmetic-oracle.py"
    baseline_first_rebased_attack(
        root,
        label="package-stats-full-blob-drift",
        paths=(package_stats,),
        mutate=lambda candidate: append_bytes(
            candidate / package_stats,
            b"\n// unauthorized package corrective drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="manually reviewed full blob",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-generator-snapshot-drift",
        paths=(package_snapshot,),
        mutate=lambda candidate: append_bytes(
            candidate / package_snapshot,
            b"\n# unauthorized snapshot drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="snapshot differs from the exact dc7 source bytes",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-canonical-generator-drift",
        paths=(canonical_generator,),
        mutate=lambda candidate: append_bytes(
            candidate / canonical_generator,
            b"\n# unauthorized canonical generator drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="canonical KSG generator changed",
    )
    attacks += 1

    package_script = "scripts/verify-package-archives.sh"
    baseline_first_rebased_attack(
        root,
        label="package-archive-test-name-drift",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"stats::tests::packaged_ksg_generator_snapshot_matches_workspace_source_when_available",
            b"stats::tests::unreviewed_archive_branch",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed exact extracted-package test name",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-exact-filter-removal",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"    --exact \\\n",
            b"    --nocapture \\\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed exact libtest filter",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-color-control-removal",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"    --color never 2>&1",
            b"    --nocapture 2>&1",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed deterministic libtest color",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-one-test-receipt-weakened",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"'running 1 test'",
            b"'running 0 tests'",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed one-test receipt",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-named-pass-receipt-weakened",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b'"test $archive_test_name ... ok"',
            b'"test result: ok"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed named-test receipt",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-summary-regex-escape-drift",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b"^test result: ok\\. 1 passed;",
            b"^test result: ok\\\\. 1 passed;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed exact one-pass summary parser",
        repin_package_script_for_downstream=True,
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-absent-generator-precondition-removed",
        paths=(package_script,),
        mutate=lambda candidate: replace_once(
            candidate / package_script,
            b'if [[ -e "$archive_workspace_generator" || -L "$archive_workspace_generator" ]]; then',
            b"if false; then",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier differs from its manually reviewed full blob",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-archive-unrelated-script-drift",
        paths=(package_script,),
        mutate=lambda candidate: append_bytes(
            candidate / package_script,
            b"\n# unrelated unreviewed package drift\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="package archive verifier differs from its manually reviewed full blob",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="package-marker-duplicate-rejection-weakened",
        paths=(package_stats,),
        mutate=lambda candidate: replace_once(
            candidate / package_stats,
            b"serde_json::from_slice::<CargoPackageContext>(ambiguous).is_err()",
            b"serde_json::from_slice::<CargoPackageContext>(ambiguous).is_ok()",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed duplicate marker rejection",
        repin_stats_for_downstream=True,
    )
    attacks += 1

    workflow = ".github/workflows/ci.yml"
    workflow_mutations = (
        (
            "workflow-checkout-residue-digest-drift",
            (
                b'expected_worktree_config_sha256="443a5f645c23c3d0c0aa09f634b2ad'
                b'111d46ef61946b598a2fb311678ab47454"'
            ),
            (
                b'expected_worktree_config_sha256="043a5f645c23c3d0c0aa09f634b2ad'
                b'111d46ef61946b598a2fb311678ab47454"'
            ),
        ),
        (
            "workflow-checkout-symlink-guard-removal",
            b'if [[ ! -f "$worktree_config" || -L "$worktree_config" ]]; then',
            b'if [[ ! -f "$worktree_config" ]]; then',
        ),
        (
            "workflow-checkout-broad-removal",
            b'            unlink -- "$worktree_config"',
            b'            rm -f -- "$worktree_config"',
        ),
        (
            "workflow-lacheck-removal",
            b"            latexmk \\\n            lacheck \\\n            lmodern \\\n",
            b"            latexmk \\\n            lmodern \\\n",
        ),
        (
            "workflow-cargo-deny-order-regression",
            (
                b"          cargo deny --manifest-path "
                b"audit/tools/certified-sxpid/Cargo.toml\n"
                b"          --config audit/tools/certified-sxpid/deny.toml check\n"
            ),
            (
                b"          cargo deny --manifest-path "
                b"audit/tools/certified-sxpid/Cargo.toml check\n"
                b"          --config audit/tools/certified-sxpid/deny.toml\n"
            ),
        ),
    )
    for label, before, after in workflow_mutations:
        baseline_first_rebased_attack(
            root,
            label=label,
            paths=(workflow,),
            mutate=lambda candidate, before=before, after=after: replace_once(
                candidate / workflow,
                before,
                after,
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment="exact three-edit dc7 transform",
        )
        attacks += 1

    baseline_first_rebased_attack(
        root,
        label="workflow-unrelated-fourth-edit",
        paths=(workflow,),
        mutate=lambda candidate: append_bytes(
            candidate / workflow,
            b"\n# unauthorized fourth corrective edit\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="exact three-edit dc7 transform",
    )
    attacks += 1

    ecosystem_surfaces = (
        "ECOSYSTEM_CAPABILITIES.md",
        "ecosystem-capabilities.json",
        "scripts/check-ecosystem-capabilities.py",
    )
    current_catalog_digest = (
        b"637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"
    )
    for ecosystem_surface in ecosystem_surfaces:
        baseline_first_rebased_attack(
            root,
            label=f"ecosystem-transform-drift-{ecosystem_surface}",
            paths=(ecosystem_surface,),
            mutate=lambda candidate, relative=ecosystem_surface: replace_once(
                candidate / relative,
                current_catalog_digest,
                b"01a305873716117b540b26113560d4693eb9d9e356718fbee01713618bee3383",
            ),
            first_fragment="changed-byte projection digest mismatch",
            semantic_fragment=(
                f"{ecosystem_surface} differs from the exact one-digest "
                "ecosystem transform"
            ),
        )
        attacks += 1

    def mutate_coordinated_ecosystem(candidate: Path) -> None:
        append_bytes(
            candidate / "method-catalog.json",
            b" ",
        )
        alternate_digest = hashlib.sha256(
            (candidate / "method-catalog.json").read_bytes()
        ).hexdigest().encode("ascii")
        for relative in ecosystem_surfaces:
            replace_once(
                candidate / relative,
                current_catalog_digest,
                alternate_digest,
            )

    baseline_first_rebased_attack(
        root,
        label="coordinated-alternate-catalog-and-ecosystem-surfaces",
        paths=("method-catalog.json", *ecosystem_surfaces),
        mutate=mutate_coordinated_ecosystem,
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment=(
            "current method catalog differs from the manually reviewed "
            "corrective digest"
        ),
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="stats-forbidden-exact-sum-token",
        paths=("crates/pid-core/src/stats.rs",),
        mutate=lambda candidate: append_bytes(
            candidate / "crates/pid-core/src/stats.rs",
            b"\nfn exact_binary64_sum() {}\n",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="forbidden later-wave exact-sum token",
        repin_stats_for_downstream=True,
    )
    attacks += 1

    parallel = "crates/pid-core/tests/parallel_bit_identity.rs"
    baseline_first_rebased_attack(
        root,
        label="ambient-pid2-synergy-bits",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"const PID2_SYN_BITS: u64 = 4591732782175321776;",
            b"const PID2_SYN_BITS: u64 = 4591732782175321784;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="PID2_SYN_BITS is not the unique KSG-only value",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-false-zero-crate-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b'#![cfg(feature = "experimental-pipelines")]',
            (b'#![cfg(all(feature = "experimental-pipelines", feature = "parallel"))]'),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="zero-test-capable crate gate",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-second-crate-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b'#![cfg(feature = "experimental-pipelines")]\n\n',
            (
                b'#![cfg(feature = "experimental-pipelines")]\n\n'
                b'#![cfg(feature = "parallel")]\n'
            ),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-module-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"mod common;\n",
            b'#[cfg(feature = "parallel")]\nmod common;\n',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    first_parallel_test = (
        b"#[test]\n"
        b"fn ksg_report_is_identical_for_thread_budgets_one_two_three_four_and_available_maximum() {"
    )
    baseline_first_rebased_attack(
        root,
        label="serial-individual-test-cfg-gate",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (b'#[cfg(feature = "parallel")]\n' + first_parallel_test),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-cfg-attr-ignore",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (b'#[cfg_attr(not(feature = "parallel"), ignore)]\n' + first_parallel_test),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-unconditional-ignore",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            b"#[ignore]\n" + first_parallel_test,
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="conditional/ignore attribute inventory changed",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-runtime-cfg-macro",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            (first_parallel_test + b'\n    if cfg!(feature = "parallel") { return; }'),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="runtime cfg! gate",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-early-return-bypass",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            first_parallel_test,
            first_parallel_test + b"\n    return;",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="early-return bypass",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="serial-test-inventory-removal",
        paths=(parallel,),
        mutate=lambda candidate: replace_once(
            candidate / parallel,
            b"#[test]\nfn ksg_local_mi_terms_match_serial_reference(",
            b"fn ksg_local_mi_terms_match_serial_reference(",
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="12 nonzero serial tests",
    )
    attacks += 1

    release = "release-scope-1.0.json"
    baseline_first_rebased_attack(
        root,
        label="combined-pid2-release-revision",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b"separate-biased-term-pid2-integer-harmonic-v2",
            (
                b"separate-biased-term-pid2-with-integer-harmonic-inputs-and-"
                b"represented-input-exact-synergy-sum-v2"
            ),
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="KSG-only bridge revision",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="release-revision-type-confusion",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b'"estimator_revision": "separate-biased-term-pid2-integer-harmonic-v2"',
            b'"estimator_revision": 17',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="invalid typed identity/revision",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="release-duplicate-key",
        paths=(release,),
        mutate=lambda candidate: replace_once(
            candidate / release,
            b'{\n  "acceptance_blockers"',
            b'{\n  "schema": "pid-rs/release-scope",\n  "acceptance_blockers"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="duplicate JSON key",
    )
    attacks += 1

    identity = "crates/pid-core/identity/software-identity-reference-v1.json"
    baseline_first_rebased_attack(
        root,
        label="combined-identity-field",
        paths=(identity,),
        mutate=lambda candidate: replace_once(
            candidate / identity,
            b'"attestation": "none"',
            b'"attestation": "local"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="changed outside the two authorized forensic digests",
    )
    attacks += 1

    baseline_first_rebased_attack(
        root,
        label="identity-catalog-digest-drift",
        paths=(identity,),
        mutate=lambda candidate: replace_once(
            candidate / identity,
            b'"canonical_json_sha256": "637719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"',
            b'"canonical_json_sha256": "037719c0204d083cdcbd5c499d1a611ac381583fea4c43ffd6cf55ea42d0c86f"',
        ),
        first_fragment="changed-byte projection digest mismatch",
        semantic_fragment="does not bind current canonical bytes",
    )
    attacks += 1
    return attacks


def main() -> int:
    try:
        static_source_preflight()
        source_facts = current_facts(ROOT)
        with tempfile.TemporaryDirectory(
            prefix="pid-rs-ksg-phase-self-test."
        ) as temporary_raw:
            temporary = Path(temporary_raw)
            optimization_preflight(temporary)
            candidate = temporary / "candidate"
            clone_candidate(ROOT, candidate, source_facts)
            run_checker(candidate, expect_success=True)

            checker_model = run_checker_model_attacks(candidate)
            policy = run_policy_authority_attacks(candidate)
            json_type_firewall = run_json_type_firewall_controls(candidate)
            path_custody = run_path_and_custody_attacks(candidate)
            tree_custody = run_external_tree_custody_tests(candidate, source_facts)
            retained_self_reference = run_retained_self_reference_boundary(
                candidate,
                source_facts,
            )
            repository_context = run_repository_context_attacks(candidate)
            semantic = run_rebased_semantic_attacks(candidate)
            lifecycle = run_lifecycle_history_tests(
                ROOT,
                temporary,
                source_facts,
            )
            run_checker(candidate, expect_success=True)
            require(
                json_type_firewall == 2,
                "JSON type-firewall control inventory changed",
            )
            require(
                retained_self_reference == 1,
                "retained self-reference boundary inventory changed",
            )
    except (OSError, SelfTestError) as error:
        print(f"ERROR: KSG phase-isolation self-test: {error}", file=sys.stderr)
        return 1

    total = (
        checker_model
        + policy
        + path_custody
        + tree_custody
        + repository_context
        + semantic
        + lifecycle
    )
    print(
        "OK: KSG phase-isolation hostile suite; "
        f"checker-model={checker_model}; policy-authority={policy}; "
        f"path-custody={path_custody}; external-tree={tree_custody}; "
        f"git-context={repository_context}; "
        f"hash-rebased-semantics={semantic}; lifecycle-history={lifecycle}; "
        f"total={total}; "
        f"json-type-firewall={json_type_firewall}/2 (separate from total); "
        f"retained-self-reference={retained_self_reference}/1 "
        "(accepted coordinated rebase; pre-pinned tree rejection; separate from total); "
        f"mode={'optimized' if sys.flags.optimize else 'normal'}. "
        "Mechanical fact rebasing never edited the separately reviewed path policy; "
        "the checker cannot authenticate coordinated mutation of its own bytes; "
        "this tests bounded custody cuts, not KSG science."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
