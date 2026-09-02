#!/usr/bin/env python3
"""Hostile mutation suite for the post-publication custody snapshot gate.

The suite is intentionally standard-library-only.  It first proves that the
production checker accepts its bound baseline in normal and optimized Python,
then requires parser, manifest, identity, custody, evidence, presentation, and
nonclaim mutations to fail closed.  The final group targets contradictory
semantic additions that can otherwise survive substring-only checks.
"""

from __future__ import annotations

import ast
import copy
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, NoReturn


if sys.version_info < (3, 11):
    raise SystemExit("check-post-publication-custody-self-test.py requires Python 3.11+")


class SelfTestError(RuntimeError):
    """The production checker did not exhibit the required behavior."""


def fail(message: str) -> NoReturn:
    raise SelfTestError(message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-post-publication-custody.py"
EXPECTED_STDOUT = (
    "OK: post-publication custody snapshot and exact remote-head manifest "
    "are bounded and consistent\n"
)


def reject_assert_statements(path: Path) -> None:
    """Keep both gates meaningful when Python removes ``assert`` under ``-O``."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=os.fspath(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        fail(f"cannot inspect {path}: {error}")
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(tree)),
        f"optimization-sensitive assert statement found in {path}",
    )


for inspected_path in (Path(__file__).resolve(), CHECKER_PATH):
    reject_assert_statements(inspected_path)


SPEC = importlib.util.spec_from_file_location(
    "post_publication_custody_checker_self_test_subject", CHECKER_PATH
)
require(SPEC is not None and SPEC.loader is not None, "cannot load production checker")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(CHECKER)


def run_production_cli(*, optimized: bool, poison_root: Path) -> None:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", os.fspath(CHECKER_PATH)))
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = os.fspath(poison_root)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        input=b"",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    mode = "optimized" if optimized else "normal"
    require(
        completed.returncode == 0,
        f"production checker baseline failed in {mode} mode: "
        f"stdout={completed.stdout!r}, stderr={completed.stderr!r}",
    )
    require(
        completed.stdout.decode("utf-8", "strict") == EXPECTED_STDOUT,
        f"production checker emitted an unexpected {mode}-mode success contract",
    )
    require(not completed.stderr, f"production checker wrote stderr in {mode} mode")


def exercise_cli_isolation() -> int:
    """Prove that ``-I`` defeats an effective ambient import poison."""
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-post-publication-custody-import-"
    ) as directory:
        poison_root = Path(directory)
        marker = "PID_RS_CUSTODY_AMBIENT_HASHLIB_EXECUTED"
        (poison_root / "hashlib.py").write_text(
            f"raise RuntimeError({marker!r})\n", encoding="utf-8"
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = os.fspath(poison_root)
        poisoned = subprocess.run(
            [sys.executable, "-S", "-B", "-c", "import hashlib"],
            cwd=ROOT,
            env=environment,
            input=b"",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
        )
        require(
            poisoned.returncode != 0 and marker.encode("ascii") in poisoned.stderr,
            "ambient PYTHONPATH poison was not effective without isolated mode",
        )
        run_production_cli(optimized=False, poison_root=poison_root)
        run_production_cli(optimized=True, poison_root=poison_root)
    return 3


def expect_check_error(
    label: str,
    action: Callable[[], Any],
    expected_diagnostic: str | None = None,
) -> None:
    try:
        action()
    except CHECKER.CheckError as error:
        if expected_diagnostic is not None:
            require(
                expected_diagnostic in str(error),
                f"{label}: wrong rejection diagnostic: {error!s}",
            )
    except Exception as error:
        fail(f"{label}: checker raised an unclassified exception: {error!r}")
    else:
        fail(f"{label}: hostile input passed")


def load_baseline() -> tuple[dict[str, Any], bytes, bytes]:
    record_raw = CHECKER.read_regular(CHECKER.RECORD)
    manifest_file_raw = CHECKER.read_regular(CHECKER.MANIFEST)
    record = CHECKER.parse_record(record_raw)
    _, manifest_raw = CHECKER.parse_manifest(manifest_file_raw)
    CHECKER.check_snapshot(record, manifest_raw)
    return record, record_raw, manifest_raw


def exercise_record_parser(record_raw: bytes) -> int:
    cases: tuple[tuple[str, bytes, str], ...] = (
        (
            "duplicate-json-key",
            b'{"schema":"one","schema":"two"}\n',
            "duplicate JSON key: 'schema'",
        ),
        (
            "nonfinite-json-constant",
            b'{"value":NaN}\n',
            "non-finite JSON constant is forbidden: NaN",
        ),
        (
            "missing-final-newline",
            record_raw.rstrip(b"\n"),
            "record must be LF text ending in one newline",
        ),
        (
            "carriage-return",
            record_raw.replace(b"\n", b"\r\n", 1),
            "record must be LF text ending in one newline",
        ),
        (
            "invalid-utf8",
            b'{"schema":"\xff"}\n',
            "invalid record encoding or JSON",
        ),
        ("non-object-root", b"[]\n", "record root must be an object"),
    )
    for label, raw, diagnostic in cases:
        expect_check_error(
            label,
            lambda candidate=raw: CHECKER.parse_record(candidate),
            diagnostic,
        )
    return len(cases)


def exercise_manifest_parser(manifest_raw: bytes) -> int:
    lines = manifest_raw.splitlines(keepends=True)
    reordered = b"".join((lines[1], lines[0], *lines[2:]))
    invalid_oid = b"g" + manifest_raw[1:]
    missing_tab = manifest_raw.replace(b"\t", b" ", 1)
    ambiguous_ref = manifest_raw.replace(
        b"refs/heads/archive/composite-v5-rejected-umask-20260818",
        b"refs/heads/archive/../escape",
        1,
    )
    non_ascii = manifest_raw.replace(b"refs/heads/", b"refs/heads/\xff", 1)
    cases: tuple[tuple[str, bytes, str], ...] = (
        (
            "manifest-missing-final-newline",
            manifest_raw.rstrip(b"\n"),
            "remote manifest must be LF text ending in one newline",
        ),
        (
            "manifest-row-reordering",
            reordered,
            "remote manifest differs from the exact observed head set or order",
        ),
        ("manifest-invalid-oid", invalid_oid, "invalid Git object ID"),
        ("manifest-missing-tab", missing_tab, "must contain one tab"),
        ("manifest-ambiguous-ref", ambiguous_ref, "ambiguous ref spelling"),
        ("manifest-non-ascii", non_ascii, "is not ASCII"),
    )
    for label, raw, diagnostic in cases:
        expect_check_error(
            label,
            lambda candidate=raw: CHECKER.parse_manifest(candidate),
            diagnostic,
        )
    return len(cases)


Mutation = Callable[[dict[str, Any]], None]


def set_nested(path: tuple[Any, ...], value: Any) -> Mutation:
    def mutate(record: dict[str, Any]) -> None:
        target: Any = record
        for component in path[:-1]:
            target = target[component]
        target[path[-1]] = value

    return mutate


def append_text(path: tuple[Any, ...], suffix: str) -> Mutation:
    def mutate(record: dict[str, Any]) -> None:
        target: Any = record
        for component in path[:-1]:
            target = target[component]
        target[path[-1]] += suffix

    return mutate


def exercise_bound_mutations(record: dict[str, Any], manifest_raw: bytes) -> int:
    zero_oid = "0" * 40
    zero_digest = "0" * 64
    cases: tuple[tuple[str, Mutation, str], ...] = (
        ("schema", set_nested(("schema",), "pid-rs/post-publication-custody/v3"), "schema marker drifted"),
        ("record-identity", set_nested(("record_id",), "PPC-20260902-99"), "record identity drifted"),
        ("phase-time", set_nested(("actions_completed_at_utc",), "2026-09-02T00:07:36Z"), "phase timestamp identity drifted"),
        ("phase-basis", set_nested(("phase_timestamp_basis", "ordering"), "unordered"), "phase timestamp boundary weakened"),
        ("scope", set_nested(("scope",), "unbounded live authority"), "scope boundary weakened"),
        ("publication-main", set_nested(("publication", "remote_main"), zero_oid), "publication.remote_main drifted"),
        ("dirty-lane", set_nested(("publication", "primary_worktree_status"), "clean"), "dirty-lane boundary weakened"),
        ("remote-command", set_nested(("live_remote_heads", "observed_command"), "git branch -r"), "remote command drifted"),
        ("remote-entry", set_nested(("live_remote_heads", "entries", 0, "oid"), zero_oid), "JSON remote-entry projection differs"),
        ("packed-ref-digest", set_nested(("local_ref_reconciliation", "pre_packed_refs_sha256"), zero_digest), "pre-packed digest drifted"),
        ("tracking-cleanup", set_nested(("local_tracking_cleanup", 0, "action"), "deleted_without_observation"), "local tracking cleanup record drifted"),
        ("validation-boundary", set_nested(("local_validation", "note"), "ran somewhere"), "validation checkout distinction weakened"),
        ("retired-reason", set_nested(("retired_remote_branches", 0, "reason"), "unreviewed deletion"), "reason drifted"),
        ("containment-predicate", set_nested(("containment_checks", 0, "predicate"), "objects look similar"), "containment predicate wording drifted"),
        ("hosted-conclusion", set_nested(("hosted_runs", 0, "conclusion"), "neutral"), "hosted run scope/status drifted"),
        ("hosted-job-count", set_nested(("hosted_runs", 0, "jobs"), 48), "hosted run identity drifted"),
        ("hosted-census", set_nested(("hosted_census", "jobs"), 57), "hosted census drifted"),
        ("supplementary-run", set_nested(("hosted_census", "supplementary_runs", 0, "conclusion"), "failure"), "supplementary CodeQL run drifted"),
        ("retired-route", set_nested(("retired_ref_routes", 0, "route"), "byte_identical"), "mainline ancestry route drifted"),
        ("route-boundary", set_nested(("retired_ref_route_boundary",), "Ancestry is identity."), "ancestry boundary weakened"),
        ("worktree-bundle", set_nested(("retired_primary_worktrees", 0, "bundle_sha256"), zero_digest), "retired worktree identity/custody drifted"),
        ("garbage-collection", set_nested(("cleanup_controls", "garbage_collection"), "run"), "garbage-collection boundary weakened"),
        ("inventory-count", set_nested(("observed_local_inventory", "primary_local_heads"), 3), "local inventory value drifted"),
        ("final-observation", set_nested(("final_local_observation", "status_projection_sha256"), zero_digest), "final local observation drifted"),
        ("temporary-state-order", set_nested(("retired_temporary_state", 0, "kind"), "unknown"), "temporary-state identity/order drifted"),
        ("historical-interpretation", set_nested(("historical_records", "interpretation"), "current live authority"), "historical-ledger interpretation drifted"),
        ("divergent-branch", set_nested(("retained_state", "local_divergent_workflow_branches", 0), "refs/heads/main"), "divergent branch retention drifted"),
        ("private-package-digest", set_nested(("retained_state", "latest_private_primary_package", "manifest_sha256"), zero_digest), "private primary-package custody record drifted"),
        ("artifact-digest", set_nested(("presentation_artifacts", "builder", "sha256"), zero_digest), "presentation artifact bytes drifted: builder"),
        ("receipt-page-count", set_nested(("presentation_artifacts", "receipt_pdf", "pages"), 7), "receipt PDF profile drifted"),
        ("tool-profile", set_nested(("presentation_artifacts", "tool_versions", "pandoc"), "pandoc unknown"), "presentation tool profile drifted"),
        ("annotation-contract", set_nested(("presentation_artifacts", "annotation_contract"), "all actions admitted"), "annotation contract drifted"),
        ("review-count", set_nested(("review", "total_lenses"), 69), "review receipt drifted"),
        ("nonclaim", set_nested(("nonclaims", 0), "All PID theorems are certified."), "nonclaim list drifted"),
        ("private-locator", set_nested(("repository",), "/Users/example/private/pid-rs"), "repository identity drifted"),
    )
    for label, mutate, diagnostic in cases:
        candidate = copy.deepcopy(record)
        mutate(candidate)
        expect_check_error(
            label,
            lambda value=candidate: CHECKER.check_snapshot(value, manifest_raw),
            diagnostic,
        )
    return len(cases)


def exercise_semantic_escalations(
    record: dict[str, Any], manifest_raw: bytes
) -> int:
    """Require rejection of additions that contradict the receipt's boundaries."""
    cases: tuple[tuple[str, Mutation], ...] = (
        (
            "unknown-top-level-scientific-certificate",
            set_nested(("scientific_certificate",), True),
        ),
        (
            "unknown-publication-formal-certificate",
            set_nested(("publication", "formal_certificate"), "all theorems proved"),
        ),
        (
            "unknown-hosted-run-mathematical-certificate",
            set_nested(("hosted_runs", 0, "mathematical_certificate"), True),
        ),
        (
            "contradictory-scope-suffix",
            append_text(("scope",), " This record authorizes future deletion."),
        ),
        (
            "contradictory-remote-absence-suffix",
            append_text(
                ("live_remote_heads", "absence_scope"),
                " It also proves future absence.",
            ),
        ),
        (
            "contradictory-garbage-collection-suffix",
            append_text(
                ("local_ref_reconciliation", "result"),
                " Nevertheless, garbage collection was run and all bytes are unchanged.",
            ),
        ),
        (
            "contradictory-ancestry-boundary-suffix",
            append_text(
                ("retired_ref_route_boundary",),
                " Ancestry proves byte identity and continued future reachability.",
            ),
        ),
        (
            "temporary-state-deletion-authorization",
            append_text(
                ("retired_temporary_state", 1, "predicate"),
                " This authorizes deletion of all future copies.",
            ),
        ),
        (
            "retained-state-scientific-overclaim",
            set_nested(
                ("retained_state", "c12_registry_and_r4_worktree"),
                "This retained state proves every estimator is valid.",
            ),
        ),
    )
    misses: list[str] = []
    for label, mutate in cases:
        candidate = copy.deepcopy(record)
        mutate(candidate)
        try:
            CHECKER.check_snapshot(candidate, manifest_raw)
        except CHECKER.CheckError:
            continue
        except Exception as error:
            fail(f"{label}: checker raised an unclassified exception: {error!r}")
        misses.append(label)
    require(
        not misses,
        "semantic escalations passed instead of failing closed: " + ", ".join(misses),
    )
    return len(cases)


def main() -> int:
    controls = exercise_cli_isolation()
    record, record_raw, manifest_raw = load_baseline()
    parser_rejections = exercise_record_parser(record_raw)
    manifest_rejections = exercise_manifest_parser(manifest_raw)
    bound_rejections = exercise_bound_mutations(record, manifest_raw)
    semantic_rejections = exercise_semantic_escalations(record, manifest_raw)
    total = parser_rejections + manifest_rejections + bound_rejections + semantic_rejections
    print(
        "OK: post-publication custody hostile suite observed "
        f"{total} fail-closed mutations and {controls} baseline/isolation controls"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as error:
        print(f"post-publication custody self-test error: {error}", file=sys.stderr)
        raise SystemExit(1) from None
