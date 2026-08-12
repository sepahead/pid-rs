#!/usr/bin/env python3
"""Hostile tests for the deterministic post-commit source-state artifact."""

from __future__ import annotations

import copy
import csv
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import types


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-post-commit-source-state-v1.py"
CURRENT_CHECKER = ROOT / "scripts/check-current-source-state-v1.py"


def exact_source(path: Path, label: str) -> bytes:
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit(f"{label} is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()

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


def load_module(path: Path, name: str) -> types.ModuleType:
    source = exact_source(path, name)
    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    code = compile(
        source,
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


checker = load_module(CHECKER, "post_commit_source_state_v1")
current_checker = load_module(
    CURRENT_CHECKER, "current_source_state_v1_for_post_commit"
)
schema, _ = checker.load_canonical_json(
    checker.DEFAULT_SCHEMA, "post-commit source-state schema"
)

rejections = 0


def run(
    root: Path,
    *arguments: str,
    env: dict[str, str] | None = None,
) -> str:
    completed = subprocess.run(
        list(arguments),
        cwd=root,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"self-test command failed: {arguments!r}: {completed.stderr.strip()}"
        )
    return completed.stdout.strip()


def write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


def expect_artifact_rejected(
    label: str, value: object, expected: dict[str, object]
) -> None:
    global rejections
    try:
        checker.validate_artifact(value, schema, expected)
    except (checker.PostCommitStateError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile post-commit artifact passed")


def expect_state_rejected(label: str, root: Path) -> None:
    global rejections
    try:
        checker.build_artifact(root)
    except (checker.PostCommitStateError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile repository state passed")


def expect_call_rejected(label: str, operation: object) -> None:
    global rejections
    try:
        operation()  # type: ignore[operator]
    except (checker.PostCommitStateError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile operation passed")


def canonical(value: object) -> bytes:
    return checker.canonical_bytes(value)


with tempfile.TemporaryDirectory(
    prefix="pid-rs-post-commit-source-state-v1-"
) as temporary:
    temporary_root = Path(temporary)
    root = temporary_root / "repo"
    artifact_dir = temporary_root / "artifacts"
    root.mkdir()
    artifact_dir.mkdir()
    run(root, "git", "init", "-q", "-b", "main")
    run(root, "git", "config", "user.name", "Post Commit State Self Test")
    run(root, "git", "config", "user.email", "post-commit-state-self-test.invalid")

    write(root / ".gitignore", b"ignored-product\n")
    write(root / "README.md", b"fixture readme\n")
    write(root / "RELEASE_NOTES.md", b"fixture release notes\n")
    write(root / "CHANGELOG.md", b"fixture changelog\n")
    write(root / "method-catalog.json", b"{}\n")
    write(root / "release-scope-1.0.json", b"{}\n")
    write(root / "source.txt", b"source bytes\n")
    (root / "source-link").symlink_to("source.txt")
    write(root / "audit/source-errata.json", b"{}\n")
    write(root / "audit/evidence/assurance-registry-typed-view-v1.json", b"{}\n")
    write(root / "claims/fixture/claim.md", b"bounded fixture claim\n")
    write(root / "audit/formal/fixture.lean", b"theorem fixture : True := by trivial\n")

    for relative in (
        "scripts/check-current-source-state-v1.py",
        "scripts/check-post-commit-source-state-v1.py",
        "scripts/json_schema_subset.py",
        "audit/schemas/current-source-state-v1.schema.json",
        "audit/schemas/post-commit-source-state-v1.schema.json",
    ):
        write(root / relative, exact_source(ROOT / relative, relative))
    for pdf_path in current_checker.EXPECTED_PDF_PATHS:
        write(root / pdf_path, f"%PDF-fixture {pdf_path}\n".encode("utf-8"))

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
    write(root / "audit/evidence/assurance-registry.json", b"{}\n")
    run(root, "git", "add", "-A")
    run(root, "git", "commit", "-qm", "fixture source")
    run(root, "git", "tag", "-a", "v0.9.0", "-m", "fixture tag")
    tag_object = run(root, "git", "rev-parse", "refs/tags/v0.9.0")
    tag_commit = run(root, "git", "rev-parse", "refs/tags/v0.9.0^{commit}")
    assurance = {
        "release_boundary": {
            "tag": "v0.9.0",
            "tag_object_sha": tag_object,
            "tagged_commit_sha": tag_commit,
        }
    }
    write(
        root / "audit/evidence/assurance-registry.json",
        current_checker.canonical_bytes(assurance),
    )

    manifest = current_checker.build_manifest(root)
    manifest_path = root / current_checker.MANIFEST_RELATIVE
    write(manifest_path, current_checker.canonical_bytes(manifest))
    run(root, "git", "add", "-A")
    run(root, "git", "commit", "-qm", "contain self-excluding manifest")

    baseline = checker.build_artifact(root)
    checker.validate_artifact(baseline, schema, baseline)

    # Exercise the exact CLI route in normal and optimized Python. The output is
    # outside the worktree and the optimized pass independently reconstructs HEAD.
    cli_artifact = artifact_dir / "cli-post-commit-state.json"
    normal = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-B",
            str(root / checker.GENERATOR),
            "--output",
            str(cli_artifact),
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if normal.returncode != 0 or normal.stderr or not normal.stdout.startswith("OK: "):
        raise SystemExit(
            f"normal isolated post-commit CLI failed: {normal.stderr.strip()}"
        )
    optimized = subprocess.run(
        [
            sys.executable,
            "-O",
            "-I",
            "-S",
            "-B",
            str(root / checker.GENERATOR),
            "--validate",
            str(cli_artifact),
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if (
        optimized.returncode != 0
        or optimized.stderr
        or not optimized.stdout.startswith("OK: ")
    ):
        raise SystemExit(
            f"optimized isolated post-commit CLI failed: {optimized.stderr.strip()}"
        )
    observed_cli, raw_cli = checker.load_canonical_json(
        cli_artifact, "self-test CLI artifact"
    )
    checker.validate_artifact(observed_cli, schema, baseline)
    if raw_cli != canonical(baseline):
        raise SystemExit("normal and optimized CLI artifact bytes differ")

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
        (
            "repository substitution",
            ("repository",),
            "attacker/pid-rs",
        ),
    )
    for label, route, replacement in artifact_mutations:
        mutation = copy.deepcopy(baseline)
        target = mutation
        for component in route[:-1]:
            target = target[component]
        target[route[-1]] = replacement
        expect_artifact_rejected(label, mutation, baseline)

    mutation = copy.deepcopy(baseline)
    mutation["nonimplications"].pop()
    expect_artifact_rejected("dropped nonimplication", mutation, baseline)
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
        mutation = copy.deepcopy(baseline)
        mutation["nonimplications"][index] = replacement
        expect_artifact_rejected(label, mutation, baseline)

    schema_mutation = copy.deepcopy(schema)
    schema_mutation["unsupported_assertion"] = True
    try:
        checker.validate_json_schema(
            baseline,
            schema_mutation,
            name="hostile-post-commit-source-state-schema",
        )
    except checker.SchemaValidationError:
        rejections += 1
    else:
        raise SystemExit("unsupported post-commit schema assertion was accepted")

    for label, field in (
        ("negative manifest size", "size_bytes"),
        ("negative source-projection count", "source_projection_entry_count"),
    ):
        schema_value = copy.deepcopy(baseline)
        schema_value["binding"]["manifest"][field] = -1
        try:
            checker.validate_json_schema(
                schema_value,
                schema,
                name="hostile-post-commit-source-state-value",
            )
        except checker.SchemaValidationError:
            rejections += 1
        else:
            raise SystemExit(f"{label}: standalone schema accepted hostile value")

    # A later empty commit changes only the post-commit artifact's commit binding.
    # The manifest, manifest blob, and tree remain unchanged, proving no commit cycle.
    first_containing_artifact = copy.deepcopy(baseline)
    run(root, "git", "commit", "--allow-empty", "-qm", "later containing commit")
    baseline = checker.build_artifact(root)
    if (
        baseline["binding"]["commit_oid"]
        == first_containing_artifact["binding"]["commit_oid"]
        or baseline["binding"]["tree_oid"]
        != first_containing_artifact["binding"]["tree_oid"]
        or baseline["binding"]["manifest"]
        != first_containing_artifact["binding"]["manifest"]
    ):
        raise SystemExit("post-commit binding introduced a manifest/commit cycle")
    expect_artifact_rejected(
        "artifact from prior containing commit", first_containing_artifact, baseline
    )

    expect_call_rejected(
        "artifact output inside worktree",
        lambda: checker.write_new_artifact(
            root, root / "post-commit-state.json", canonical(baseline)
        ),
    )
    existing_output = artifact_dir / "existing.json"
    existing_output.write_bytes(b"already exists\n")
    expect_call_rejected(
        "existing artifact overwrite",
        lambda: checker.write_new_artifact(root, existing_output, canonical(baseline)),
    )
    symlink_output = artifact_dir / "symlink.json"
    symlink_output.symlink_to(existing_output.name)
    expect_call_rejected(
        "symlink artifact overwrite",
        lambda: checker.write_new_artifact(root, symlink_output, canonical(baseline)),
    )

    rollback_output = artifact_dir / "rollback-after-readback-failure.json"
    original_reader = checker.read_artifact_leaf

    def fail_written_readback(parent_descriptor: int, leaf: str, label: str) -> bytes:
        if label == "written post-commit artifact":
            raise checker.PostCommitStateError("injected post-write readback failure")
        return original_reader(parent_descriptor, leaf, label)

    checker.read_artifact_leaf = fail_written_readback
    try:
        expect_call_rejected(
            "post-write failure rolls back exact artifact leaf",
            lambda: checker.write_new_artifact(
                root, rollback_output, canonical(baseline)
            ),
        )
    finally:
        checker.read_artifact_leaf = original_reader
    if rollback_output.exists() or rollback_output.is_symlink():
        raise SystemExit("post-write failure left a published artifact residue")

    swap_parent = artifact_dir / "swap-parent"
    moved_parent = artifact_dir / "swap-parent-moved"
    swap_parent.mkdir()
    swap_output = swap_parent / "raced.json"
    original_parent_revalidation = checker.revalidate_outside_worktree_parent
    swap_state = {"done": False}

    def swap_before_parent_revalidation(
        descriptor: int,
        parent: Path,
        expected_identity: tuple[int, int, int],
        label: str,
    ) -> None:
        if label == "artifact output" and not swap_state["done"]:
            swap_state["done"] = True
            parent.rename(moved_parent)
            parent.symlink_to(root, target_is_directory=True)
        original_parent_revalidation(descriptor, parent, expected_identity, label)

    checker.revalidate_outside_worktree_parent = swap_before_parent_revalidation
    try:
        expect_call_rejected(
            "outside artifact parent swap",
            lambda: checker.write_new_artifact(root, swap_output, canonical(baseline)),
        )
    finally:
        checker.revalidate_outside_worktree_parent = original_parent_revalidation
        if swap_parent.is_symlink():
            swap_parent.unlink()
        if moved_parent.exists():
            moved_parent.rename(swap_parent)
    if (root / swap_output.name).exists() or (swap_parent / swap_output.name).exists():
        raise SystemExit("outside-parent swap redirected or retained an artifact")

    source = root / "source.txt"
    original_source = source.read_bytes()

    source.write_bytes(b"staged hostile source\n")
    run(root, "git", "add", "source.txt")
    expect_state_rejected("staged/index divergence", root)
    source.write_bytes(original_source)
    run(root, "git", "add", "source.txt")

    source.write_bytes(b"unstaged hostile source\n")
    expect_state_rejected("unstaged worktree divergence", root)
    source.write_bytes(original_source)

    untracked = root / "visible-untracked.txt"
    untracked.write_bytes(b"visible source divergence\n")
    expect_state_rejected("repository-visible untracked divergence", root)
    untracked.unlink()

    info_exclude = root / ".git/info/exclude"
    original_info_exclude = info_exclude.read_bytes()
    info_exclude.write_bytes(original_info_exclude + b"ambient-hidden.txt\n")
    ambient_hidden = root / "ambient-hidden.txt"
    ambient_hidden.write_bytes(b"ambient exclude must not hide this\n")
    expect_state_rejected("ambient exclude cannot hide untracked divergence", root)
    ambient_hidden.unlink()
    info_exclude.write_bytes(original_info_exclude)

    run(root, "git", "update-index", "--assume-unchanged", "source.txt")
    source.write_bytes(b"assume-unchanged hostile source\n")
    expect_state_rejected("assume-unchanged worktree divergence", root)
    source.write_bytes(original_source)
    run(root, "git", "update-index", "--no-assume-unchanged", "source.txt")

    os.chmod(source, 0o755)
    expect_state_rejected("tracked executable-mode divergence", root)
    os.chmod(source, 0o644)

    ignored = root / "ignored-product"
    ignored.write_bytes(b"ignored build product\n")
    if checker.build_artifact(root) != baseline:
        raise SystemExit(
            "repository-ignored build product perturbed committed identity"
        )
    ignored.unlink()

    poisoned_environment = {
        "GIT_DIR": str(root / "not-the-real-git-dir"),
        "GIT_INDEX_FILE": str(root / "not-the-real-index"),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.replaceRefs",
        "GIT_CONFIG_VALUE_0": "true",
    }
    saved_environment = {name: os.environ.get(name) for name in poisoned_environment}
    try:
        os.environ.update(poisoned_environment)
        if checker.build_artifact(root) != baseline:
            raise SystemExit("ambient Git environment perturbed post-commit identity")
    finally:
        for name, value in saved_environment.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

    # A clean committed source change with the old manifest must fail even though
    # the index and worktree agree with the new HEAD.
    source.write_bytes(b"committed source without manifest refresh\n")
    run(root, "git", "add", "source.txt")
    run(root, "git", "commit", "-qm", "stale manifest fixture")
    expect_state_rejected("committed source with stale manifest", root)
    source.write_bytes(original_source)
    run(root, "git", "add", "source.txt")
    run(root, "git", "commit", "-qm", "restore source bytes")
    baseline = checker.build_artifact(root)

    original_manifest = manifest_path.read_bytes()
    hostile_manifest = json.loads(original_manifest)
    hostile_manifest["source_projection"]["entries"].append(
        {
            "git_mode": "100644",
            "path": current_checker.MANIFEST_RELATIVE,
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
    hostile_manifest["source_projection"]["entries_sha256"] = checker.sha256_bytes(
        checker.compact_bytes(hostile_manifest["source_projection"]["entries"])
    )
    manifest_path.write_bytes(canonical(hostile_manifest))
    run(root, "git", "add", current_checker.MANIFEST_RELATIVE)
    run(root, "git", "commit", "-qm", "hostile self-including manifest")
    expect_state_rejected("manifest self-inclusion", root)
    manifest_path.write_bytes(original_manifest)
    run(root, "git", "add", current_checker.MANIFEST_RELATIVE)
    run(root, "git", "commit", "-qm", "restore self-excluding manifest")
    baseline = checker.build_artifact(root)

    invented_review = json.loads(original_manifest)
    invented_review["review_inventory"]["line_review_dispositions"] = 1
    manifest_path.write_bytes(canonical(invented_review))
    run(root, "git", "add", current_checker.MANIFEST_RELATIVE)
    run(root, "git", "commit", "-qm", "hostile invented review")
    expect_state_rejected("manifest invented review", root)
    manifest_path.write_bytes(original_manifest)
    run(root, "git", "add", current_checker.MANIFEST_RELATIVE)
    run(root, "git", "commit", "-qm", "restore review boundary")
    checker.validate_artifact(
        checker.build_artifact(root), schema, checker.build_artifact(root)
    )

expected_rejections = 30
if rejections != expected_rejections:
    raise SystemExit(
        f"post-commit mutation accounting mismatch: {rejections} != {expected_rejections}"
    )

print(
    "OK: post-commit baseline and normal/-O CLI passed; commit binding stayed "
    f"non-circular and {rejections}/{expected_rejections} hostile mutations were rejected"
)
