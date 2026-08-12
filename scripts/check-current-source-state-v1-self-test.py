#!/usr/bin/env python3
"""Hostile tests for the deterministic self-excluding source-state manifest."""

from __future__ import annotations

import copy
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-current-source-state-v1.py"


def load_checker_from_exact_source() -> types.ModuleType:
    """Compile the observed source bytes directly; never consult a bytecode cache."""
    before = CHECKER.stat()
    source = CHECKER.read_bytes()
    after = CHECKER.stat()

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after) or len(source) != before.st_size:
        raise SystemExit("source-state checker source changed during exact-source read")
    module = types.ModuleType("current_source_state_v1")
    module.__file__ = str(CHECKER)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    code = compile(
        source,
        str(CHECKER),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


checker = load_checker_from_exact_source()


def check_isolated_cli() -> None:
    arguments = [sys.executable]
    if sys.flags.optimize:
        arguments.append("-O")
    arguments.extend(("-I", "-S", "-B", str(CHECKER), "--emit"))
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    try:
        emitted = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise SystemExit(
            "source-state checker emitted invalid JSON in isolated mode"
        ) from error
    if (
        completed.returncode != 0
        or completed.stderr
        or emitted.get("schema") != checker.SCHEMA_NAME
    ):
        raise SystemExit(
            "source-state checker failed its isolated CLI bootstrap: "
            f"{completed.stderr.strip()}"
        )


check_isolated_cli()

schema, _ = checker.load_canonical_json(
    checker.DEFAULT_SCHEMA, "source-state schema", require_regular=True
)

rejections = 0


def run(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        list(arguments),
        cwd=root,
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


def expect_stale(label: str, manifest: object, expected: dict[str, object]) -> None:
    global rejections
    try:
        checker.validate_manifest(manifest, schema, expected, enforce_production=False)
    except (checker.StateError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: stale or hostile manifest passed")


def expect_collection_rejected(label: str, root: Path) -> None:
    global rejections
    try:
        checker.build_manifest(root, enforce_production=False)
    except checker.StateError:
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile source state passed collection")


with tempfile.TemporaryDirectory(prefix="pid-rs-current-source-state-v1-") as temporary:
    root = Path(temporary) / "repo"
    root.mkdir()
    run(root, "git", "init", "-q", "-b", "main")
    run(root, "git", "config", "user.name", "Source State Self Test")
    run(root, "git", "config", "user.email", "source-state-self-test.invalid")

    write(root / ".gitignore", b"ignored-product\n")
    write(root / "README.md", b"fixture readme\n")
    write(root / "RELEASE_NOTES.md", b"fixture release notes\n")
    write(root / "CHANGELOG.md", b"fixture changelog\n")
    write(root / "method-catalog.json", b"{}\n")
    write(root / "release-scope-1.0.json", b"{}\n")
    write(root / "audit/source-errata.json", b"{}\n")
    write(root / "audit/evidence/assurance-registry-typed-view-v1.json", b"{}\n")
    write(root / "claims/fixture/claim.md", b"bounded fixture claim\n")
    write(root / "audit/formal/fixture.lean", b"theorem fixture : True := by trivial\n")
    for pdf_path in checker.EXPECTED_PDF_PATHS:
        write(root / pdf_path, f"%PDF-fixture {pdf_path}\n".encode("utf-8"))
    write(root / "source.txt", b"source bytes\n")

    ledger_stream = io.StringIO(newline="")
    ledger_writer = csv.DictWriter(
        ledger_stream,
        fieldnames=("path", "reviewer", "review_status"),
        lineterminator="\n",
    )
    ledger_writer.writeheader()
    ledger_writer.writerow(
        {
            "path": "source.txt",
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
    run(root, "git", "commit", "-qm", "fixture")
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
        checker.canonical_bytes(assurance),
    )

    baseline = checker.build_manifest(root, enforce_production=False)
    manifest_path = root / checker.MANIFEST_RELATIVE
    write(manifest_path, checker.canonical_bytes(baseline))
    checker.validate_manifest(baseline, schema, baseline, enforce_production=False)

    # The manifest's own bytes and a new containing commit are intentionally outside
    # the projection.  Neither operation changes the expected source-state body.
    write(manifest_path, checker.canonical_bytes(baseline) + b"\n")
    if checker.build_manifest(root, enforce_production=False) != baseline:
        raise SystemExit("manifest self-exclusion was not stable")
    write(manifest_path, checker.canonical_bytes(baseline))
    run(root, "git", "add", checker.MANIFEST_RELATIVE)
    run(root, "git", "commit", "-qm", "contain manifest")
    if checker.build_manifest(root, enforce_production=False) != baseline:
        raise SystemExit("containing commit was circularly embedded in manifest")

    mutation = copy.deepcopy(baseline)
    mutation["binding"]["commit_binding"] = run(root, "git", "rev-parse", "HEAD")
    expect_stale("self-asserted containing commit", mutation, baseline)

    mutation = copy.deepcopy(baseline)
    mutation["source_projection"]["entries_sha256"] = "0" * 64
    expect_stale("projection digest rebind", mutation, baseline)

    mutation = copy.deepcopy(baseline)
    mutation["review_inventory"]["line_review_dispositions"] = 1
    expect_stale("invented line review", mutation, baseline)

    mutation = copy.deepcopy(baseline)
    mutation["historical_release"]["review_completion_inferred"] = True
    expect_stale("tag promoted to review", mutation, baseline)

    mutation = copy.deepcopy(baseline)
    mutation["nonimplications"].pop()
    expect_stale("dropped nonimplication", mutation, baseline)

    schema_mutation = copy.deepcopy(schema)
    schema_mutation["unsupported_assertion"] = True
    try:
        checker.validate_json_schema(
            baseline, schema_mutation, name="hostile-source-state-schema"
        )
    except checker.SchemaValidationError:
        rejections += 1
    else:
        raise SystemExit("unsupported source-state schema assertion was accepted")

    source = root / "source.txt"
    original_source = source.read_bytes()
    source.write_bytes(b"mutated source bytes\n")
    changed = checker.build_manifest(root, enforce_production=False)
    expect_stale("tracked source mutation", baseline, changed)
    source.write_bytes(original_source)

    extra = root / "new-source.txt"
    extra.write_text("untracked but projected\n", encoding="utf-8")
    changed = checker.build_manifest(root, enforce_production=False)
    expect_stale("untracked source addition", baseline, changed)
    extra.unlink()

    info_exclude = root / ".git/info/exclude"
    original_info_exclude = info_exclude.read_bytes()
    info_exclude.write_bytes(original_info_exclude + b"ambient-hidden.txt\n")
    ambient_hidden = root / "ambient-hidden.txt"
    ambient_hidden.write_text("must remain projected\n", encoding="utf-8")
    changed = checker.build_manifest(root, enforce_production=False)
    if not any(
        entry["path"] == "ambient-hidden.txt"
        for entry in changed["source_projection"]["entries"]
    ):
        raise SystemExit(".git/info/exclude hid a source file")
    expect_stale("ambient exclude bypass", baseline, changed)
    ambient_hidden.unlink()
    info_exclude.write_bytes(original_info_exclude)

    ignored = root / "ignored-product"
    ignored.write_text("ignored build product\n", encoding="utf-8")
    if checker.build_manifest(root, enforce_production=False) != baseline:
        raise SystemExit("repository-ignored build product perturbed source state")
    ignored.unlink()

    executable = root / "new-executable"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    os.chmod(executable, 0o644)
    nonexec = checker.build_manifest(root, enforce_production=False)
    os.chmod(executable, 0o755)
    exec_state = checker.build_manifest(root, enforce_production=False)
    if nonexec == exec_state:
        raise SystemExit("untracked executable mode change was invisible")
    expect_stale("source mode mutation", nonexec, exec_state)
    executable.unlink()

    link = root / "source-link"
    link.symlink_to("source.txt")
    link_state = checker.build_manifest(root, enforce_production=False)
    link_entry = next(
        entry
        for entry in link_state["source_projection"]["entries"]
        if entry["path"] == "source-link"
    )
    if link_entry["git_mode"] != "120000":
        raise SystemExit("symlink was not represented by Git symlink mode")
    link.unlink()
    link.symlink_to("README.md")
    relinked = checker.build_manifest(root, enforce_production=False)
    expect_stale("symlink target mutation", link_state, relinked)
    link.unlink()

    catalog = root / "method-catalog.json"
    catalog_bytes = catalog.read_bytes()
    catalog.unlink()
    catalog.symlink_to("README.md")
    expect_collection_rejected("critical artifact symlink", root)
    catalog.unlink()
    catalog.write_bytes(catalog_bytes)

    manifest_bytes = manifest_path.read_bytes()
    manifest_path.unlink()
    manifest_path.symlink_to("README.md")
    try:
        checker.load_canonical_json(
            manifest_path, "current source-state manifest", require_regular=True
        )
    except checker.StateError:
        rejections += 1
    else:
        raise SystemExit("symlink manifest was accepted")
    manifest_path.unlink()
    manifest_path.write_bytes(manifest_bytes)

    run(root, "git", "tag", "-d", "v0.9.0")
    expect_collection_rejected("missing historical tag", root)

expected_rejections = 14
if rejections != expected_rejections:
    raise SystemExit(
        f"source-state mutation accounting mismatch: {rejections} != {expected_rejections}"
    )

print(
    "OK: source-state baseline passed; self/commit exclusion stayed non-circular and "
    f"{rejections}/{expected_rejections} hostile mutations were rejected"
)
