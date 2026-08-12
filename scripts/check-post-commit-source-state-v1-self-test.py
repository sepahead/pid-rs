#!/usr/bin/env python3
"""CLI-only hostile tests for the post-commit source-state artifact."""

from __future__ import annotations

import ast
import copy
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
POST_CHECKER_RELATIVE = "scripts/check-post-commit-source-state-v1.py"
CURRENT_CHECKER_RELATIVE = "scripts/check-current-source-state-v1.py"
POST_SELF_TEST_RELATIVE = "scripts/check-post-commit-source-state-v1-self-test.py"
CURRENT_SELF_TEST_RELATIVE = "scripts/check-current-source-state-v1-self-test.py"
POST_SCHEMA_RELATIVE = "audit/schemas/post-commit-source-state-v1.schema.json"
CURRENT_SCHEMA_RELATIVE = "audit/schemas/current-source-state-v1.schema.json"
CURRENT_MANIFEST_RELATIVE = "audit/evidence/current-source-state-v1.json"
EXPECTED_CURRENT_SCHEMA_SHA256 = (
    "1027cc3826aa6933a23dea1736b5d007b9c5bc1568f41ac87dea98e5f2924a97"
)
EXPECTED_POST_SCHEMA_SHA256 = (
    "7779897953e5fa886c5b7e99b4ac537da5878db3037c2f19529cfb65e41b0fcd"
)
EXPECTED_PDF_PATHS = (
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "output/pdf/ecosystem-compatibility-audit.pdf",
    "output/pdf/exact-log-product-sxpid2-assurance.pdf",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "output/pdf/mathematical-problem-solving-workflow.pdf",
    "output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf",
    "output/pdf/two-source-sxpid-count-atom-bridge.pdf",
)
VERIFIER_PATHS = (
    CURRENT_CHECKER_RELATIVE,
    CURRENT_SELF_TEST_RELATIVE,
    POST_CHECKER_RELATIVE,
    POST_SELF_TEST_RELATIVE,
)
GIT = Path("/usr/bin/git")


def exact_source(path: Path, label: str) -> bytes:
    """Read one exact single-link regular source without following a symlink."""
    try:
        before = path.lstat()
    except OSError as error:
        raise SystemExit(f"cannot stat {label}: {error}") from error
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit(f"{label} is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        raise SystemExit(f"cannot open {label}: {error}") from error
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        after = path.lstat()
    except OSError as error:
        raise SystemExit(f"cannot restat {label}: {error}") from error

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    source = b"".join(chunks)
    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size
    ):
        raise SystemExit(f"{label} changed during exact-source read")
    return source


def canonical_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SystemExit(f"cannot canonicalize self-test JSON: {error}") from error


def compact_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SystemExit(f"cannot compact self-test JSON: {error}") from error


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def require_fixed_git() -> None:
    try:
        candidate = GIT.resolve(strict=True)
        metadata = GIT.lstat()
    except OSError as error:
        raise SystemExit(f"cannot inspect fixed Git executable: {error}") from error
    if candidate != GIT or not stat.S_ISREG(metadata.st_mode):
        raise SystemExit(f"fixed Git executable is not canonical and regular: {GIT}")


require_fixed_git()


def run_git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        [os.fspath(GIT), "-C", os.fspath(root), *arguments],
        cwd=root,
        env={
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "LANG": "C",
            "LC_ALL": "C",
            "PATH": "/usr/bin:/bin",
        },
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"self-test Git command failed: {arguments!r}: "
            f"{completed.stderr.decode('utf-8', errors='replace').strip()}"
        )
    try:
        return completed.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise SystemExit(f"self-test Git output is not UTF-8: {arguments!r}") from error


def python_arguments(
    script: Path, arguments: tuple[str, ...], *, optimized: bool
) -> list[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", str(script), *arguments))
    return command


def invoke_python(
    root: Path,
    script: Path,
    *arguments: str,
    optimized: bool | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    use_optimized = bool(sys.flags.optimize) if optimized is None else optimized
    return subprocess.run(
        python_arguments(script, arguments, optimized=use_optimized),
        cwd=root,
        env=environment,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )


def invoke_post(
    root: Path,
    *arguments: str,
    optimized: bool | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return invoke_python(
        root,
        root / POST_CHECKER_RELATIVE,
        *arguments,
        optimized=optimized,
        environment=environment,
    )


def invoke_current(
    root: Path, *arguments: str, optimized: bool | None = None
) -> subprocess.CompletedProcess[bytes]:
    return invoke_python(
        root,
        root / CURRENT_CHECKER_RELATIVE,
        *arguments,
        optimized=optimized,
    )


def require_success(completed: subprocess.CompletedProcess[bytes], label: str) -> bytes:
    if (
        completed.returncode != 0
        or completed.stderr
        or not completed.stdout.startswith(b"OK: ")
    ):
        raise SystemExit(
            f"{label} failed: exit={completed.returncode}, "
            f"stdout={completed.stdout!r}, stderr={completed.stderr!r}"
        )
    return completed.stdout


def refresh_manifest(root: Path) -> bytes:
    completed = invoke_current(root, "--emit")
    if completed.returncode != 0 or completed.stderr:
        raise SystemExit(
            "current-source-state fixture emit failed: "
            f"exit={completed.returncode}, stderr={completed.stderr!r}"
        )
    try:
        parsed = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit("current-source-state fixture emit is not JSON") from error
    if completed.stdout != canonical_bytes(parsed):
        raise SystemExit("current-source-state fixture emit is not canonical JSON")
    write(root / CURRENT_MANIFEST_RELATIVE, completed.stdout)
    return completed.stdout


def capture_artifact(
    root: Path, output: Path, *, optimized: bool | None = None
) -> tuple[dict[str, Any], bytes]:
    completed = invoke_post(root, "--output", str(output), optimized=optimized)
    require_success(completed, f"post-commit output {output.name!r}")
    raw = output.read_bytes()
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"post-commit output is not JSON: {output}") from error
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise SystemExit(f"post-commit output is not canonical object JSON: {output}")
    return value, raw


def dotted_name(node: ast.AST) -> str | None:
    components: list[str] = []
    cursor = node
    while isinstance(cursor, ast.Attribute):
        components.append(cursor.attr)
        cursor = cursor.value
    if not isinstance(cursor, ast.Name):
        return None
    components.append(cursor.id)
    return ".".join(reversed(components))


def assert_static_custody() -> None:
    """Reject dynamic Python loaders and non-stdlib imports in all four verifiers."""
    forbidden_modules = {
        "builtins",
        "codeop",
        "importlib",
        "marshal",
        "pickle",
        "runpy",
        "types",
    }
    forbidden_names = {"__import__", "compile", "eval", "exec"}
    forbidden_methods = {"exec_module", "load_module"}
    allowed_nonmodule_roots = {"__future__"}

    for relative in VERIFIER_PATHS:
        raw = exact_source(ROOT / relative, relative)
        try:
            tree = ast.parse(raw.decode("utf-8"), filename=relative)
        except (UnicodeDecodeError, SyntaxError) as error:
            raise SystemExit(
                f"cannot parse verifier source {relative}: {error}"
            ) from error
        violations: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.partition(".")[0] for alias in node.names]
                for imported in roots:
                    if imported in forbidden_modules:
                        violations.append(f"forbidden import {imported!r}")
                    elif imported not in sys.stdlib_module_names:
                        violations.append(f"non-stdlib import {imported!r}")
            elif isinstance(node, ast.ImportFrom):
                if node.level != 0 or node.module is None:
                    violations.append("relative or anonymous import")
                else:
                    imported = node.module.partition(".")[0]
                    if imported in forbidden_modules:
                        violations.append(f"forbidden import {imported!r}")
                    elif (
                        imported not in sys.stdlib_module_names
                        and imported not in allowed_nonmodule_roots
                    ):
                        violations.append(f"non-stdlib import {imported!r}")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in forbidden_names:
                    violations.append(f"forbidden call {node.func.id!r}")
                rendered = dotted_name(node.func)
                if rendered is not None:
                    root_name, _, method = rendered.partition(".")
                    if root_name == "builtins" and method in forbidden_names:
                        violations.append(f"forbidden call {rendered!r}")
                    if rendered.rpartition(".")[2] in forbidden_methods:
                        violations.append(f"forbidden loader call {rendered!r}")
        if violations:
            rendered = "; ".join(sorted(set(violations)))
            raise SystemExit(
                f"static verifier custody failed for {relative}: {rendered}"
            )


def route_replacement(
    value: dict[str, Any], route: tuple[str, ...], replacement: Any
) -> None:
    target: Any = value
    for component in route[:-1]:
        target = target[component]
    target[route[-1]] = replacement


rejections = 0


def expect_post_rejected(
    label: str,
    root: Path,
    *arguments: str,
    expected_codes: tuple[int, ...] = (1,),
    environment: dict[str, str] | None = None,
) -> None:
    global rejections
    completed = invoke_post(root, *arguments, environment=environment)
    if completed.returncode not in expected_codes:
        raise SystemExit(
            f"{label}: hostile CLI was not rejected with {expected_codes}: "
            f"exit={completed.returncode}, stdout={completed.stdout!r}, "
            f"stderr={completed.stderr!r}"
        )
    rejections += 1


def expect_artifact_rejected(
    label: str,
    root: Path,
    artifact_dir: Path,
    index: int,
    value: dict[str, Any],
) -> None:
    candidate = artifact_dir / f"hostile-artifact-{index:02d}.json"
    write(candidate, canonical_bytes(value))
    expect_post_rejected(label, root, "--validate", str(candidate))


def build_fixture(root: Path, artifact_dir: Path) -> Path:
    root.mkdir()
    artifact_dir.mkdir()
    run_git(root, "init", "-q", "-b", "main")
    run_git(root, "config", "user.name", "Post Commit State Self Test")
    run_git(
        root,
        "config",
        "user.email",
        "post-commit-state-self-test.invalid",
    )

    poison_marker = artifact_dir / "json-schema-subset-executed"
    poison_source = (
        "from pathlib import Path\n"
        f"Path({str(poison_marker)!r}).write_text('executed', encoding='utf-8')\n"
        "raise RuntimeError('json_schema_subset must never execute')\n"
    ).encode("utf-8")

    write(root / ".gitignore", b"ignored-product\n")
    write(root / "README.md", b"fixture readme\n")
    write(root / "RELEASE_NOTES.md", b"fixture release notes\n")
    write(root / "CHANGELOG.md", b"fixture changelog\n")
    write(root / "method-catalog.json", b"{}\n")
    write(root / "release-scope-1.0.json", b"{}\n")
    write(root / "source.txt", b"source bytes\n")
    (root / "source-link").symlink_to("source.txt")
    write(root / "audit/source-errata.json", b"{}\n")
    write(root / "audit/evidence/assurance-registry.json", b"{}\n")
    write(root / "audit/evidence/assurance-registry-typed-view-v1.json", b"{}\n")
    write(root / "claims/fixture/claim.md", b"bounded fixture claim\n")
    write(
        root / "audit/formal/fixture.lean",
        b"theorem fixture : True := by trivial\n",
    )
    for relative in (
        POST_CHECKER_RELATIVE,
        CURRENT_CHECKER_RELATIVE,
        POST_SCHEMA_RELATIVE,
        CURRENT_SCHEMA_RELATIVE,
    ):
        write(root / relative, exact_source(ROOT / relative, relative))
    write(root / "scripts/json_schema_subset.py", poison_source)
    for relative in EXPECTED_PDF_PATHS:
        write(root / relative, f"%PDF-fixture {relative}\n".encode("utf-8"))

    ledger_stream = io.StringIO(newline="")
    ledger_writer = csv.DictWriter(
        ledger_stream,
        fieldnames=("path", "reviewer", "review_status"),
        lineterminator="\n",
    )
    ledger_writer.writeheader()
    for index in range(186):
        ledger_writer.writerow(
            {
                "path": f"historical/file-{index:03d}",
                "reviewer": "UNASSIGNED",
                "review_status": "INVENTORIED_NOT_REVIEWED",
            }
        )
    write(
        root / "audit/evidence/FILE_REVIEW_LEDGER.csv",
        ledger_stream.getvalue().encode("utf-8"),
    )

    run_git(root, "add", "-A")
    run_git(root, "commit", "-qm", "fixture source")
    run_git(
        root,
        "fetch",
        "-q",
        "--no-tags",
        os.fspath(ROOT),
        "refs/tags/v0.9.0:refs/tags/v0.9.0",
    )
    tag_object = run_git(root, "rev-parse", "refs/tags/v0.9.0")
    tag_commit = run_git(root, "rev-parse", "refs/tags/v0.9.0^{commit}")
    assurance = {
        "release_boundary": {
            "tag": "v0.9.0",
            "tag_object_sha": tag_object,
            "tagged_commit_sha": tag_commit,
        }
    }
    write(
        root / "audit/evidence/assurance-registry.json",
        canonical_bytes(assurance),
    )
    refresh_manifest(root)
    run_git(root, "add", "-A")
    run_git(root, "commit", "-qm", "contain self-excluding manifest")
    if run_git(root, "status", "--porcelain=v1"):
        raise SystemExit("fixture repository is not clean after manifest commit")
    return poison_marker


def main() -> None:
    global rejections

    assert_static_custody()
    if sha256_bytes(exact_source(ROOT / CURRENT_SCHEMA_RELATIVE, "current schema")) != (
        EXPECTED_CURRENT_SCHEMA_SHA256
    ):
        raise SystemExit("current-source-state schema raw-byte pin changed")
    if sha256_bytes(exact_source(ROOT / POST_SCHEMA_RELATIVE, "post schema")) != (
        EXPECTED_POST_SCHEMA_SHA256
    ):
        raise SystemExit("post-commit source-state schema raw-byte pin changed")

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-post-commit-source-state-v1-"
    ) as temporary:
        temporary_root = Path(temporary)
        root = temporary_root / "repo"
        artifact_dir = temporary_root / "artifacts"
        poison_marker = build_fixture(root, artifact_dir)

        require_success(invoke_post(root), "baseline post-commit CLI")
        normal_path = artifact_dir / "normal.json"
        optimized_path = artifact_dir / "optimized.json"
        baseline, normal_raw = capture_artifact(root, normal_path, optimized=False)
        optimized_value, optimized_raw = capture_artifact(
            root, optimized_path, optimized=True
        )
        if baseline != optimized_value or normal_raw != optimized_raw:
            raise SystemExit("normal and optimized post-commit artifact bytes differ")
        require_success(
            invoke_post(root, "--validate", str(optimized_path), optimized=False),
            "normal validation of optimized artifact",
        )
        require_success(
            invoke_post(root, "--validate", str(normal_path), optimized=True),
            "optimized validation of normal artifact",
        )
        if poison_marker.exists():
            raise SystemExit("adjacent json_schema_subset.py executed")

        weird_marker = root / "OUTPUT_PATH_WAS_EXECUTED"
        weird_path = (
            artifact_dir
            / "literal space\n-c;touch${IFS}OUTPUT_PATH_WAS_EXECUTED;--root[]{}.json"
        )
        _weird, weird_raw = capture_artifact(root, weird_path)
        if weird_raw != normal_raw or weird_marker.exists():
            raise SystemExit("artifact output path was not treated as literal data")

        fake_git_dir = temporary_root / "fake-bin"
        fake_git_dir.mkdir()
        fake_git_marker = temporary_root / "fake-git-executed"
        fake_git = fake_git_dir / "git"
        fake_git.write_text(
            "#!/bin/sh\n: > " + shlex.quote(str(fake_git_marker)) + "\nexit 97\n",
            encoding="utf-8",
        )
        fake_git.chmod(0o755)
        fake_environment = dict(os.environ)
        fake_environment["PATH"] = str(fake_git_dir)
        require_success(
            invoke_post(root, environment=fake_environment),
            "PATH-poisoned post-commit CLI",
        )
        if fake_git_marker.exists():
            raise SystemExit("caller-PATH fake Git executable was invoked")

        attacker_root = temporary_root / "attacker-root"
        attacker_checker_marker = temporary_root / "attacker-checker-executed"
        write(
            attacker_root / CURRENT_CHECKER_RELATIVE,
            (
                "from pathlib import Path\n"
                f"Path({str(attacker_checker_marker)!r}).write_text('executed')\n"
            ).encode("utf-8"),
        )
        expect_post_rejected(
            "alternate-root malicious checker",
            root,
            "--root",
            str(attacker_root),
            expected_codes=(2,),
        )
        if attacker_checker_marker.exists():
            raise SystemExit("alternate-root malicious current checker executed")

        fixed_checker = root / CURRENT_CHECKER_RELATIVE
        fixed_checker_bytes = fixed_checker.read_bytes()
        fixed_checker_marker = temporary_root / "fixed-checker-executed"
        write(
            fixed_checker,
            (
                "from pathlib import Path\n"
                f"Path({str(fixed_checker_marker)!r}).write_text('executed')\n"
            ).encode("utf-8"),
        )
        expect_post_rejected("modified fixed current checker", root)
        if fixed_checker_marker.exists():
            raise SystemExit("modified fixed current checker executed before rejection")
        write(fixed_checker, fixed_checker_bytes)

        artifact_mutations = (
            (
                "commit OID substitution",
                ("binding", "commit_oid"),
                "0" * len(baseline["binding"]["commit_oid"]),
            ),
            (
                "tree OID substitution",
                ("binding", "tree_oid"),
                "0" * len(baseline["binding"]["tree_oid"]),
            ),
            (
                "manifest blob substitution",
                ("binding", "manifest", "blob_oid"),
                "0" * len(baseline["binding"]["manifest"]["blob_oid"]),
            ),
            (
                "manifest SHA-256 substitution",
                ("binding", "manifest", "sha256"),
                "0" * 64,
            ),
            (
                "source projection digest substitution",
                ("binding", "manifest", "source_projection_entries_sha256"),
                "0" * 64,
            ),
            (
                "evidence-class promotion",
                ("evidence_class",),
                "authenticated_reviewed_scientific_evidence",
            ),
            (
                "checker result demotion",
                ("checks", "current_manifest_checker_passed"),
                False,
            ),
            ("repository substitution", ("repository",), "attacker/pid-rs"),
        )
        mutation_index = 0
        for label, route, replacement in artifact_mutations:
            mutation_index += 1
            mutation = copy.deepcopy(baseline)
            route_replacement(mutation, route, replacement)
            expect_artifact_rejected(
                label, root, artifact_dir, mutation_index, mutation
            )

        mutation_index += 1
        mutation = copy.deepcopy(baseline)
        mutation["nonimplications"].pop()
        expect_artifact_rejected(
            "dropped nonimplication", root, artifact_dir, mutation_index, mutation
        )
        for label, index, replacement in (
            (
                "authenticity nonimplication promotion",
                0,
                "This artifact authenticates the repository origin.",
            ),
            (
                "review nonimplication promotion",
                1,
                "This artifact establishes independent human review completion.",
            ),
            (
                "scientific nonimplication promotion",
                2,
                "This artifact establishes scientific and estimator validity.",
            ),
        ):
            mutation_index += 1
            mutation = copy.deepcopy(baseline)
            mutation["nonimplications"][index] = replacement
            expect_artifact_rejected(
                label, root, artifact_dir, mutation_index, mutation
            )
        for label, field in (
            ("negative manifest size", "size_bytes"),
            ("negative source-projection count", "source_projection_entry_count"),
        ):
            mutation_index += 1
            mutation = copy.deepcopy(baseline)
            mutation["binding"]["manifest"][field] = -1
            expect_artifact_rejected(
                label, root, artifact_dir, mutation_index, mutation
            )

        prior_artifact = copy.deepcopy(baseline)
        run_git(root, "commit", "--allow-empty", "-qm", "later containing commit")
        after_empty_path = artifact_dir / "after-empty.json"
        baseline, baseline_raw = capture_artifact(root, after_empty_path)
        if (
            baseline["binding"]["commit_oid"] == prior_artifact["binding"]["commit_oid"]
            or baseline["binding"]["tree_oid"] != prior_artifact["binding"]["tree_oid"]
            or baseline["binding"]["manifest"] != prior_artifact["binding"]["manifest"]
        ):
            raise SystemExit("post-commit binding introduced a manifest/commit cycle")
        expect_post_rejected(
            "artifact from prior containing commit",
            root,
            "--validate",
            str(normal_path),
        )

        inside_output = root / "post-commit-state.json"
        expect_post_rejected(
            "artifact output inside worktree",
            root,
            "--output",
            str(inside_output),
        )
        if inside_output.exists() or inside_output.is_symlink():
            raise SystemExit("inside-worktree output rejection left a residue")
        existing_output = artifact_dir / "existing.json"
        write(existing_output, b"already exists\n")
        expect_post_rejected(
            "existing artifact overwrite",
            root,
            "--output",
            str(existing_output),
        )
        if existing_output.read_bytes() != b"already exists\n":
            raise SystemExit("existing artifact bytes changed")
        symlink_output = artifact_dir / "symlink.json"
        symlink_output.symlink_to(existing_output.name)
        expect_post_rejected(
            "symlink artifact overwrite",
            root,
            "--output",
            str(symlink_output),
        )
        if not symlink_output.is_symlink():
            raise SystemExit("symlink artifact leaf was replaced")

        publication = invoke_post(root, "--self-test-publication")
        publication_stdout = require_success(
            publication, "internal publication fault self-test"
        )
        if b"2/2" not in publication_stdout:
            raise SystemExit(
                "publication fault self-test did not attest both injected rejections"
            )
        rejections += 2

        source = root / "source.txt"
        original_source = source.read_bytes()

        source.write_bytes(b"staged hostile source\n")
        run_git(root, "add", "source.txt")
        expect_post_rejected("staged/index divergence", root)
        source.write_bytes(original_source)
        run_git(root, "add", "source.txt")

        source.write_bytes(b"unstaged hostile source\n")
        expect_post_rejected("unstaged worktree divergence", root)
        source.write_bytes(original_source)

        visible_untracked = root / "visible-untracked.txt"
        write(visible_untracked, b"visible source divergence\n")
        expect_post_rejected("repository-visible untracked divergence", root)
        visible_untracked.unlink()

        info_exclude = root / ".git/info/exclude"
        original_info_exclude = info_exclude.read_bytes()
        info_exclude.write_bytes(original_info_exclude + b"ambient-hidden.txt\n")
        ambient_hidden = root / "ambient-hidden.txt"
        write(ambient_hidden, b"ambient exclude must not hide this\n")
        expect_post_rejected("ambient exclude cannot hide untracked divergence", root)
        ambient_hidden.unlink()
        info_exclude.write_bytes(original_info_exclude)

        run_git(root, "update-index", "--assume-unchanged", "source.txt")
        source.write_bytes(b"assume-unchanged hostile source\n")
        expect_post_rejected("assume-unchanged worktree divergence", root)
        source.write_bytes(original_source)
        run_git(root, "update-index", "--no-assume-unchanged", "source.txt")

        source.chmod(0o755)
        expect_post_rejected("tracked executable-mode divergence", root)
        source.chmod(0o644)

        ignored = root / "ignored-product"
        write(ignored, b"ignored build product\n")
        ignored_artifact = artifact_dir / "with-ignored-product.json"
        _ignored_value, ignored_raw = capture_artifact(root, ignored_artifact)
        if ignored_raw != baseline_raw:
            raise SystemExit("repository-ignored product perturbed committed identity")
        ignored.unlink()

        poisoned_environment = dict(os.environ)
        poisoned_environment.update(
            {
                "GIT_DIR": str(root / "not-the-real-git-dir"),
                "GIT_INDEX_FILE": str(root / "not-the-real-index"),
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "core.replaceRefs",
                "GIT_CONFIG_VALUE_0": "true",
            }
        )
        require_success(
            invoke_post(root, environment=poisoned_environment),
            "ambient-Git-environment post-commit CLI",
        )

        source.write_bytes(b"committed source without manifest refresh\n")
        run_git(root, "add", "source.txt")
        run_git(root, "commit", "-qm", "stale manifest fixture")
        expect_post_rejected("committed source with stale manifest", root)
        source.write_bytes(original_source)
        run_git(root, "add", "source.txt")
        run_git(root, "commit", "-qm", "restore source bytes")
        baseline, baseline_raw = capture_artifact(
            root, artifact_dir / "after-source-restore.json"
        )

        manifest_path = root / CURRENT_MANIFEST_RELATIVE
        original_manifest = manifest_path.read_bytes()
        hostile_manifest = json.loads(original_manifest)
        hostile_manifest["source_projection"]["entries"].append(
            {
                "git_mode": "100644",
                "path": CURRENT_MANIFEST_RELATIVE,
                "sha256": "0" * 64,
                "size_bytes": 0,
            }
        )
        hostile_manifest["source_projection"]["entries"].sort(
            key=lambda entry: entry["path"]
        )
        hostile_manifest["source_projection"]["entry_count"] = len(
            hostile_manifest["source_projection"]["entries"]
        )
        hostile_manifest["source_projection"]["entries_sha256"] = sha256_bytes(
            compact_bytes(hostile_manifest["source_projection"]["entries"])
        )
        write(manifest_path, canonical_bytes(hostile_manifest))
        run_git(root, "add", CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "hostile self-including manifest")
        expect_post_rejected("manifest self-inclusion", root)
        write(manifest_path, original_manifest)
        run_git(root, "add", CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "restore self-excluding manifest")
        baseline, baseline_raw = capture_artifact(
            root, artifact_dir / "after-self-exclusion-restore.json"
        )

        invented_review = json.loads(original_manifest)
        invented_review["review_inventory"]["line_review_dispositions"] = 1
        write(manifest_path, canonical_bytes(invented_review))
        run_git(root, "add", CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "hostile invented review")
        expect_post_rejected("manifest invented review", root)
        write(manifest_path, original_manifest)
        run_git(root, "add", CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "restore review boundary")
        baseline, baseline_raw = capture_artifact(
            root, artifact_dir / "after-review-restore.json"
        )

        post_schema_path = root / POST_SCHEMA_RELATIVE
        original_post_schema = post_schema_path.read_bytes()
        schema_mutation = json.loads(original_post_schema)
        schema_mutation["unsupported_assertion"] = True
        write(post_schema_path, canonical_bytes(schema_mutation))
        refresh_manifest(root)
        run_git(root, "add", POST_SCHEMA_RELATIVE, CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "hostile post schema bytes")
        expect_post_rejected("post-commit schema byte mismatch", root)
        write(post_schema_path, original_post_schema)
        refresh_manifest(root)
        run_git(root, "add", POST_SCHEMA_RELATIVE, CURRENT_MANIFEST_RELATIVE)
        run_git(root, "commit", "-qm", "restore post schema bytes")
        final_value, final_raw = capture_artifact(
            root, artifact_dir / "final-clean-state.json"
        )
        require_success(
            invoke_post(
                root,
                "--validate",
                str(artifact_dir / "final-clean-state.json"),
                optimized=True,
            ),
            "final optimized validation",
        )
        if final_raw != canonical_bytes(final_value):
            raise SystemExit("final clean artifact is not canonical")
        if poison_marker.exists():
            raise SystemExit("json_schema_subset.py executed during hostile suite")

    expected_rejections = 32
    if rejections != expected_rejections:
        raise SystemExit(
            "post-commit mutation accounting mismatch: "
            f"{rejections} != {expected_rejections}"
        )
    print(
        "OK: CLI-only post-commit baseline and normal/-O bytes passed; "
        "dynamic loaders, caller executables, and alternate roots were non-authoritative; "
        f"{rejections}/{expected_rejections} hostile cases were rejected"
    )


if __name__ == "__main__":
    main()
