#!/usr/bin/env python3
"""Hostile mutation tests for the bounded retirement-ledger validator."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-worktree-and-branch-retirement-ledger.py"


def run_checker(*, optimized: bool) -> subprocess.CompletedProcess[bytes]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", os.fspath(CHECKER_PATH)))
    return subprocess.run(
        command,
        cwd=ROOT,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )


source = CHECKER_PATH.read_text(encoding="utf-8")
tree = ast.parse(source, filename=os.fspath(CHECKER_PATH))
if any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
    raise SystemExit("checker uses assert and is unsafe under Python -O")
if any(
    (
        isinstance(node, ast.ImportFrom)
        and node.module == "json_schema_subset"
    )
    or (
        isinstance(node, ast.Import)
        and any(alias.name == "json_schema_subset" for alias in node.names)
    )
    for node in ast.walk(tree)
):
    raise SystemExit("checker relies on an ambient json_schema_subset import")

for optimized in (False, True):
    result = run_checker(optimized=optimized)
    if result.returncode != 0 or result.stderr:
        raise SystemExit(
            f"baseline checker failed (optimized={optimized}): "
            f"exit={result.returncode}, stderr={result.stderr!r}"
        )
    expected_stdout = (
        b"OK: primary retirement ledger is exact, scope-bounded, "
        b"custody-bound, and authorizes no deletion\n"
    )
    if result.stdout != expected_stdout:
        raise SystemExit(
            f"baseline checker output drifted (optimized={optimized}): "
            f"stdout={result.stdout!r}"
        )

spec = importlib.util.spec_from_file_location("retirement_ledger_checker", CHECKER_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load retirement-ledger checker")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

ledger_raw = checker.read_single_link_regular(checker.LEDGER)
schema_raw = checker.read_single_link_regular(checker.SCHEMA)
ledger = json.loads(ledger_raw)
schema = json.loads(schema_raw)
checker.validate_record(ledger_raw, schema_raw, enforce_exact_bytes=True)


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


rejections = 0


def expect_rejected(label: str, value: object, expected_diagnostic: str | None = None) -> None:
    global rejections
    try:
        checker.validate_record(
            canonical_bytes(value),
            schema_raw,
            enforce_exact_bytes=False,
        )
    except checker.LedgerError as error:
        if expected_diagnostic is not None and str(error) != expected_diagnostic:
            raise SystemExit(
                f"{label}: wrong rejection diagnostic: expected {expected_diagnostic!r}, "
                f"observed {str(error)!r}"
            ) from error
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile mutation passed")


def exercise_path_custody_controls() -> int:
    path_rejections = 0

    def expect_path_rejected(label: str, path: Path, expected_fragment: str) -> None:
        nonlocal path_rejections
        try:
            checker.read_single_link_regular(path)
        except checker.LedgerError as error:
            if expected_fragment not in str(error):
                raise SystemExit(
                    f"{label}: wrong path-custody diagnostic: {str(error)!r}"
                ) from error
            path_rejections += 1
            return
        raise SystemExit(f"{label}: unsafe path was accepted")

    with tempfile.TemporaryDirectory(prefix="pid-rs-primary-ledger-path-") as directory:
        root = Path(directory)
        source = root / "source.json"
        source.write_bytes(b"{}\n")

        symbolic = root / "symbolic.json"
        symbolic.symlink_to(source.name)
        expect_path_rejected(symbolic.name, symbolic, "not a single-link regular file")

        hardlink = root / "hardlink.json"
        os.link(source, hardlink)
        expect_path_rejected(hardlink.name, hardlink, "not a single-link regular file")

        target = root / "replacement-race.json"
        replacement = root / "replacement.json"
        target.write_bytes(b"A" * (1024 * 1024 + 17))
        replacement.write_bytes(b"B" * (1024 * 1024 + 17))
        original_read = checker.os.read
        replaced = False

        def replace_during_read(descriptor: int, amount: int) -> bytes:
            nonlocal replaced
            if not replaced:
                os.replace(replacement, target)
                replaced = True
            return original_read(descriptor, amount)

        checker.os.read = replace_during_read
        try:
            expect_path_rejected(
                target.name,
                target,
                "required file identity changed during read",
            )
        finally:
            checker.os.read = original_read

    if path_rejections != 3:
        raise SystemExit(
            f"path-custody rejection census drifted: expected 3, observed {path_rejections}"
        )
    return path_rejections


mutations: list[tuple[str, dict[str, object]]] = []

value = copy.deepcopy(ledger)
value["global_decision"]["cleanup_authorized"] = True
mutations.append(("cleanup authorization", value))

value = copy.deepcopy(ledger)
value["global_decision"]["deletion_eligible_count"] = 1
mutations.append(("deletion census", value))

value = copy.deepcopy(ledger)
value["global_decision"]["final_main_candidate_established"] = True
mutations.append(("unfinished candidate escalation", value))

value = copy.deepcopy(ledger)
value["scope"]["sibling_and_global_registries"] = "cleared"
mutations.append(("sibling registry escalation", value))

value = copy.deepcopy(ledger)
value["worktrees"][0]["deletion_eligible"] = True
mutations.append(("worktree deletion eligibility", value))

value = copy.deepcopy(ledger)
value["worktrees"][0]["head"] = "0" * 40
mutations.append(("worktree head", value))

value = copy.deepcopy(ledger)
value["worktrees"][2]["untracked_leaf_paths"] = 71
mutations.append(("worktree path count", value))

value = copy.deepcopy(ledger)
value["worktrees"][3]["ignored_outputs"]["other_files"] = 28
mutations.append(("ignored-output accounting", value))

value = copy.deepcopy(ledger)
value["local_ref_namespaces"][2]["count"] = 6
mutations.append(("namespace ref count", value))

value = copy.deepcopy(ledger)
value["local_ref_namespaces"][3]["entries"][0]["object_id"] = "0" * 40
mutations.append(("quarantine object identity", value))

value = copy.deepcopy(ledger)
value["local_ref_namespaces"][0]["deletion_eligible"] = True
mutations.append(("namespace deletion eligibility", value))

value = copy.deepcopy(ledger)
value["hosted_branches"][10]["object_id"] = "0" * 40
mutations.append(("hosted main tip", value))

value = copy.deepcopy(ledger)
value["hosted_branches"][0]["disposition"] = "conditional_retirement_candidate"
mutations.append(("negative-evidence disposition", value))

value = copy.deepcopy(ledger)
value["hosted_branches"][11]["deletion_eligible"] = True
mutations.append(("hosted deletion eligibility", value))

value = copy.deepcopy(ledger)
value["restricted_custody"]["bundle"]["sha256"] = "0" * 64
mutations.append(("bundle byte identity", value))

value = copy.deepcopy(ledger)
value["restricted_custody"]["locator_in_public_ledger"] = True
mutations.append(("locator disclosure", value))

value = copy.deepcopy(ledger)
value["restricted_custody"]["deletion_authority"] = True
mutations.append(("bundle deletion authority", value))

value = copy.deepcopy(ledger)
value["restricted_custody"]["recovery_drill"]["advertised_object_ids_missing"] = 1
mutations.append(("missing recovered object", value))

value = copy.deepcopy(ledger)
value["restricted_custody"]["access_boundary"] = "/Users/example/restricted.bundle"
mutations.append(("absolute restricted locator", value))

value = copy.deepcopy(ledger)
value["snapshot"]["completed_at_utc"] = "2026-09-01T07:00:00Z"
mutations.append(("reversed snapshot interval", value))

value = copy.deepcopy(ledger)
value["nonclaims"].pop()
mutations.append(("removed nonclaim", value))

for label, mutation in mutations:
    expect_rejected(label, mutation)

value = copy.deepcopy(ledger)
value["repository_state"]["primary_head"] = "0" * 40
expect_rejected(
    "primary HEAD coherent drift",
    value,
    "primary worktree HEAD identity drifted",
)

value = copy.deepcopy(ledger)
value["worktrees"][0]["custody_status"] = "complete"
value["worktrees"][0]["disposition"] = "delete_now"
expect_rejected(
    "worktree semantic cleanup escalation",
    value,
    "primary-review: custody status drifted",
)

value = copy.deepcopy(ledger)
value["nonclaims"][0] = "The ledger is permission to delete any ref, branch, or worktree."
expect_rejected(
    "nonclaim inversion",
    value,
    "nonclaim identity or order drifted",
)

value = copy.deepcopy(ledger)
value["hosted_branches"][0]["disposition"], value["hosted_branches"][10]["disposition"] = (
    value["hosted_branches"][10]["disposition"],
    value["hosted_branches"][0]["disposition"],
)
expect_rejected(
    "hosted disposition swap preserving census",
    value,
    "hosted branch disposition/reason identity drifted",
)

duplicate_raw = b'{\n  "schema": "duplicate",' + ledger_raw[1:]
try:
    checker.validate_record(duplicate_raw, schema_raw, enforce_exact_bytes=False)
except checker.LedgerError:
    rejections += 1
else:
    raise SystemExit("duplicate JSON key passed")

schema_mutation = copy.deepcopy(schema)
schema_mutation["unsupported_weakening_keyword"] = True
try:
    checker.validate_record(
        canonical_bytes(ledger),
        canonical_bytes(schema_mutation),
        enforce_exact_bytes=False,
    )
except checker.LedgerError:
    rejections += 1
else:
    raise SystemExit("unknown schema keyword passed")

noncanonical = json.dumps(ledger, separators=(",", ":")).encode("utf-8")
try:
    checker.validate_record(noncanonical, schema_raw, enforce_exact_bytes=False)
except checker.LedgerError:
    rejections += 1
else:
    raise SystemExit("missing final LF passed")

if rejections != 28:
    raise SystemExit(f"hostile rejection census drifted: expected 28, observed {rejections}")

path_rejections = exercise_path_custody_controls()

print(
    "OK: retirement ledger baseline passed in isolated normal/-O modes; "
    f"hostile_rejections={rejections}; path_custody_rejections={path_rejections}"
)
