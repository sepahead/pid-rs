#!/usr/bin/env python3
"""Hostile CLI tests for the self-excluding current-source-state checker."""

from __future__ import annotations

import ast
import copy
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER_SOURCE = ROOT / "scripts/check-current-source-state-v1.py"
SCHEMA_SOURCE = ROOT / "audit/schemas/current-source-state-v1.schema.json"
GIT = Path("/usr/bin/git")
MANIFEST_RELATIVE = "audit/evidence/current-source-state-v1.json"
EXPECTED_PDF_PATHS = (
    "output/pdf/certified-sxpid2-executable-assurance.pdf",
    "output/pdf/dependency-colored-sxpid-concentration.pdf",
    "output/pdf/ecosystem-compatibility-audit.pdf",
    "output/pdf/exact-log-product-sxpid2-assurance.pdf",
    "output/pdf/finite-alphabet-plugin-convergence.pdf",
    "output/pdf/formal-tool-adoption-audit.pdf",
    "output/pdf/foundational-shared-exclusions-pid-audit.pdf",
    "output/pdf/ksg-m1a-composite-v4-process.pdf",
    "output/pdf/mathematical-problem-solving-workflow.pdf",
    "output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf",
    "output/pdf/two-source-sxpid-count-atom-bridge.pdf",
)


def canonical_bytes(value: object) -> bytes:
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


def write(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)


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
            f"fixture Git command failed: {arguments!r}: {completed.stderr!r}"
        )
    return completed.stdout.decode("ascii").strip()


def checker_command(checker: Path, *arguments: str, optimized: bool) -> list[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", os.fspath(checker), *arguments))
    return command


def invoke(
    checker: Path,
    root: Path,
    *arguments: str,
    optimized: bool | None = None,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    use_optimized = bool(sys.flags.optimize) if optimized is None else optimized
    return subprocess.run(
        checker_command(checker, *arguments, optimized=use_optimized),
        cwd=root,
        env=environment,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )


def require_success(label: str, completed: subprocess.CompletedProcess[bytes]) -> bytes:
    if completed.returncode != 0 or completed.stderr:
        raise SystemExit(
            f"{label} failed: exit={completed.returncode}, stderr={completed.stderr!r}"
        )
    return completed.stdout


def emit(checker: Path, root: Path, *, optimized: bool | None = None) -> bytes:
    raw = require_success(
        "source-state fixture emit",
        invoke(checker, root, "--emit", optimized=optimized),
    )
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise SystemExit("source-state checker emitted invalid JSON") from error
    if raw != canonical_bytes(value):
        raise SystemExit("source-state checker emit was not canonical LF JSON")
    return raw


def assert_no_dynamic_execution(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=os.fspath(path))
    forbidden_calls = {"compile", "eval", "exec"}
    forbidden_modules = {"importlib", "marshal", "pickle", "runpy", "types"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
                raise SystemExit(f"dynamic execution call in {path}: {node.func.id}")
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "exec_module",
                "load_module",
            }:
                raise SystemExit(f"dynamic loader call in {path}: {node.func.attr}")
        elif isinstance(node, ast.Import):
            if any(
                alias.name.split(".", 1)[0] in forbidden_modules for alias in node.names
            ):
                raise SystemExit(f"dynamic loader import in {path}")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".", 1)[0] in forbidden_modules:
                raise SystemExit(f"dynamic loader import in {path}")


for inspected in (Path(__file__).resolve(), CHECKER_SOURCE):
    assert_no_dynamic_execution(inspected)


rejections = 0
custody_controls = 0


def expect_rejected(
    label: str,
    checker: Path,
    root: Path,
    *arguments: str,
    optimized: bool | None = None,
    environment: dict[str, str] | None = None,
) -> None:
    global rejections
    completed = invoke(
        checker,
        root,
        *arguments,
        optimized=optimized,
        environment=environment,
    )
    if completed.returncode == 0:
        raise SystemExit(f"{label}: hostile state passed")
    rejections += 1


with tempfile.TemporaryDirectory(prefix="pid-rs-current-source-state-v1-") as temporary:
    base = Path(temporary)
    root = base / "repo"
    root.mkdir()
    checker = root / "scripts/check-current-source-state-v1.py"
    schema = root / "audit/schemas/current-source-state-v1.schema.json"
    manifest_path = root / MANIFEST_RELATIVE
    write(checker, CHECKER_SOURCE.read_bytes())
    write(schema, SCHEMA_SOURCE.read_bytes())

    run_git(root, "init", "-q", "-b", "main")
    run_git(root, "config", "user.name", "Source State Self Test")
    run_git(root, "config", "user.email", "source-state-self-test.invalid")

    write(root / ".gitignore", b"ignored-product\nscripts/__pycache__/\n")
    write(root / "README.md", b"fixture readme\n")
    write(root / "RELEASE_NOTES.md", b"fixture release notes\n")
    write(root / "CHANGELOG.md", b"fixture changelog\n")
    write(root / "method-catalog.json", b"{}\n")
    write(root / "release-scope-1.0.json", b"{}\n")
    write(root / "audit/source-errata.json", b"{}\n")
    write(root / "audit/evidence/assurance-registry-typed-view-v1.json", b"{}\n")
    write(root / "claims/fixture/claim.md", b"bounded fixture claim\n")
    write(root / "audit/formal/fixture.lean", b"theorem fixture : True := by trivial\n")
    for pdf_path in EXPECTED_PDF_PATHS:
        write(root / pdf_path, f"%PDF-fixture {pdf_path}\n".encode("utf-8"))
    write(root / "source.txt", b"source bytes\n")

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
                "path": f"inventory/source-{index:03d}.txt",
                "reviewer": "UNASSIGNED",
                "review_status": "INVENTORIED_NOT_REVIEWED",
            }
        )
    write(
        root / "audit/evidence/FILE_REVIEW_LEDGER.csv",
        ledger_stream.getvalue().encode("utf-8"),
    )
    write(root / "audit/evidence/assurance-registry.json", b"{}\n")
    run_git(root, "add", "-A")
    run_git(root, "commit", "-qm", "fixture")
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
    write(
        root / "audit/evidence/assurance-registry.json",
        canonical_bytes(
            {
                "release_boundary": {
                    "tag": "v0.9.0",
                    "tag_object_sha": tag_object,
                    "tagged_commit_sha": tag_commit,
                }
            }
        ),
    )

    baseline_raw = emit(checker, root, optimized=False)
    optimized_raw = emit(checker, root, optimized=True)
    if baseline_raw != optimized_raw:
        raise SystemExit("normal and optimized source-state emits differ")
    baseline = json.loads(baseline_raw)
    if baseline.get("repository") != "sepahead/pid-rs":
        raise SystemExit("production-valid fixture did not retain repository identity")
    write(manifest_path, baseline_raw)
    require_success("positive baseline", invoke(checker, root))

    # The self-excluded manifest bytes and a containing commit cannot perturb its body.
    write(manifest_path, baseline_raw + b"\n")
    if emit(checker, root) != baseline_raw:
        raise SystemExit("manifest self-exclusion was not stable")
    write(manifest_path, baseline_raw)
    run_git(root, "add", MANIFEST_RELATIVE)
    run_git(root, "commit", "-qm", "contain manifest")
    if emit(checker, root) != baseline_raw:
        raise SystemExit("containing commit was circularly embedded in manifest")

    def validate_mutation(label: str, value: object) -> None:
        write(manifest_path, canonical_bytes(value))
        expect_rejected(label, checker, root)
        write(manifest_path, baseline_raw)

    mutation = copy.deepcopy(baseline)
    mutation["binding"]["commit_binding"] = run_git(root, "rev-parse", "HEAD")
    validate_mutation("self-asserted containing commit", mutation)

    mutation = copy.deepcopy(baseline)
    mutation["source_projection"]["entries_sha256"] = "0" * 64
    validate_mutation("projection digest rebind", mutation)

    mutation = copy.deepcopy(baseline)
    mutation["review_inventory"]["line_review_dispositions"] = 1
    validate_mutation("invented line review", mutation)

    mutation = copy.deepcopy(baseline)
    mutation["historical_release"]["review_completion_inferred"] = True
    validate_mutation("tag promoted to review", mutation)

    mutation = copy.deepcopy(baseline)
    mutation["nonimplications"].pop()
    validate_mutation("dropped nonimplication", mutation)

    schema_mutation = json.loads(schema.read_bytes())
    schema_mutation["unsupported_assertion"] = True
    schema_bytes = schema.read_bytes()
    write(schema, canonical_bytes(schema_mutation))
    expect_rejected("schema raw-byte mutation", checker, root)
    write(schema, schema_bytes)

    source = root / "source.txt"
    original_source = source.read_bytes()
    source.write_bytes(b"mutated source bytes\n")
    validate_mutation("tracked source mutation", baseline)
    source.write_bytes(original_source)

    extra = root / "new-source.txt"
    extra.write_text("untracked but projected\n", encoding="utf-8")
    validate_mutation("untracked source addition", baseline)
    extra.unlink()

    info_exclude = root / ".git/info/exclude"
    original_info_exclude = info_exclude.read_bytes()
    info_exclude.write_bytes(original_info_exclude + b"ambient-hidden.txt\n")
    ambient_hidden = root / "ambient-hidden.txt"
    ambient_hidden.write_text("must remain projected\n", encoding="utf-8")
    hidden_state = json.loads(emit(checker, root))
    if not any(
        entry["path"] == "ambient-hidden.txt"
        for entry in hidden_state["source_projection"]["entries"]
    ):
        raise SystemExit(".git/info/exclude hid a source file")
    validate_mutation("ambient exclude bypass", baseline)
    ambient_hidden.unlink()
    info_exclude.write_bytes(original_info_exclude)

    ignored = root / "ignored-product"
    ignored.write_text("ignored build product\n", encoding="utf-8")
    if emit(checker, root) != baseline_raw:
        raise SystemExit("repository-ignored build product perturbed source state")
    ignored.unlink()

    executable = root / "new-executable"
    executable.write_text("#!/bin/sh\n", encoding="utf-8")
    os.chmod(executable, 0o644)
    nonexec = json.loads(emit(checker, root))
    os.chmod(executable, 0o755)
    validate_mutation("source mode mutation", nonexec)
    executable.unlink()

    link = root / "source-link"
    link.symlink_to("source.txt")
    link_state = json.loads(emit(checker, root))
    link_entry = next(
        entry
        for entry in link_state["source_projection"]["entries"]
        if entry["path"] == "source-link"
    )
    if link_entry["git_mode"] != "120000":
        raise SystemExit("symlink was not represented by Git symlink mode")
    link.unlink()
    link.symlink_to("README.md")
    validate_mutation("symlink target mutation", link_state)
    link.unlink()

    catalog = root / "method-catalog.json"
    catalog_bytes = catalog.read_bytes()
    catalog.unlink()
    catalog.symlink_to("README.md")
    expect_rejected("critical artifact symlink", checker, root, "--emit")
    catalog.unlink()
    catalog.write_bytes(catalog_bytes)

    manifest_bytes = manifest_path.read_bytes()
    manifest_path.unlink()
    manifest_path.symlink_to("README.md")
    expect_rejected("symlink manifest", checker, root)
    manifest_path.unlink()
    manifest_path.write_bytes(manifest_bytes)

    run_git(root, "tag", "-d", "v0.9.0")
    expect_rejected("missing historical tag", checker, root, "--emit")
    run_git(root, "update-ref", "refs/tags/v0.9.0", tag_object)

    # Custody controls are counted separately from artifact-semantic mutations.
    for rejected_option in (
        "--root",
        "--manifest",
        "--schema",
        "--allow-fixture-repository",
    ):
        completed = invoke(checker, root, rejected_option, os.fspath(root))
        if completed.returncode == 0:
            raise SystemExit(f"unsupported authority option passed: {rejected_option}")
        custody_controls += 1

    poison = base / "poison"
    poison.mkdir()
    poison_marker = base / "sitecustomize-executed"
    write(
        poison / "sitecustomize.py",
        f"from pathlib import Path\nPath({os.fspath(poison_marker)!r}).write_text('x')\n".encode(),
    )
    hostile_environment = dict(os.environ)
    hostile_environment["PYTHONPATH"] = os.fspath(poison)
    require_success(
        "isolated PYTHONPATH non-consumption",
        invoke(checker, root, "--emit", environment=hostile_environment),
    )
    if poison_marker.exists():
        raise SystemExit("isolated checker executed hostile sitecustomize")
    custody_controls += 1

    fake_bin = base / "fake-bin"
    fake_bin.mkdir()
    fake_git_marker = base / "fake-git-executed"
    write(
        fake_bin / "git",
        f"#!/bin/sh\n: > {os.fspath(fake_git_marker)!r}\nexit 97\n".encode(),
    )
    os.chmod(fake_bin / "git", 0o755)
    hostile_environment = dict(os.environ)
    hostile_environment["PATH"] = f".:{fake_bin}:/usr/bin:/bin"
    require_success(
        "fixed Git route non-consumption",
        invoke(checker, root, "--emit", environment=hostile_environment),
    )
    if fake_git_marker.exists():
        raise SystemExit("checker executed PATH-selected fake Git")
    custody_controls += 1

expected_rejections = 14
expected_custody_controls = 6
if rejections != expected_rejections:
    raise SystemExit(
        f"source-state mutation accounting mismatch: {rejections} != {expected_rejections}"
    )
if custody_controls != expected_custody_controls:
    raise SystemExit(
        "source-state custody accounting mismatch: "
        f"{custody_controls} != {expected_custody_controls}"
    )

print(
    "OK: source-state positive baseline passed; self/commit exclusion stayed "
    f"non-circular; {rejections}/{expected_rejections} hostile mutations and "
    f"{custody_controls}/{expected_custody_controls} custody controls passed"
)
