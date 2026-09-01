#!/usr/bin/env python3
"""Hostile mutation suite for the sibling-registry retirement ledger gate."""

from __future__ import annotations

import ast
import copy
import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable


class SelfTestError(RuntimeError):
    """The hostile suite did not observe the required fail-closed behavior."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfTestError(message)


ROOT = Path(__file__).resolve().parent.parent
CHECKER_PATH = ROOT / "scripts/check-sibling-registry-retirement-ledger.py"
SPEC = importlib.util.spec_from_file_location("sibling_registry_ledger_checker", CHECKER_PATH)
require(SPEC is not None and SPEC.loader is not None, "cannot load checker module")
CHECKER = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(CHECKER)


PREDICATE_DIAGNOSTICS = {
    "unknown-top-level-key": "$: unexpected keys: ['unknown']",
    "record-identity": "$.record_id: value does not match const",
    "observation-start": "$.observation.started_at_utc: value does not match const",
    "observation-end": "$.observation.ended_at_utc: value does not match const",
    "git-version": "$.observation.git_version: value does not match const",
    "live-main-identity": "reference commit set drift",
    "registry-removed": "registry inventory drift",
    "common-directory-collision": "common Git directories: duplicate identifiers",
    "registry-head": "legacy-copy: registry anchor is not its first worktree",
    "registry-tree": "legacy-copy: registry anchor is not its first worktree",
    "c12-worktree-removed": "worktree count drift",
    "bare-with-worktree": "program-dossier-backup: bare/worktree mismatch",
    "detached-branch-label": "sxpid3-independent: detached HEAD must use branch label none",
    "staged-path": "summary is not the exact derived projection",
    "clean-status-digest": "c11-fresh: clean status must bind the empty capture digest",
    "coherent-status-reprojection": "status aggregate drift",
    "publication-archive-full-identity-truncated": (
        "publication-synthesis archive checkpoint: invalid SHA-1"
    ),
    "publication-archive-tree": (
        "publication-synthesis exact commit/tree/parent checkpoint drift"
    ),
    "publication-archive-parent": (
        "publication-synthesis exact commit/tree/parent checkpoint drift"
    ),
    "coherent-publication-checkpoint-reprojection": (
        "publication-synthesis exact commit/tree/parent checkpoint drift"
    ),
    "archive-status-kind": (
        "$.registries[0].archive_checkpoint.identifier_kind: value is outside enum"
    ),
    "comparison-partition": "cmp-c10-forensic: exact/evolved/absent partition mismatch",
    "comparison-target": "cmp-c10-forensic: target-specific comparison row drift",
    "c12-candidate-labelled-remote-main": (
        "cmp-c12-numerical-to-integration-candidate: target-specific comparison row drift"
    ),
    "c12-remote-main-labelled-candidate": (
        "cmp-c12-numerical-to-live-remote-main: target-specific comparison row drift"
    ),
    "coherent-comparison-reprojection": (
        "cmp-c10-forensic: target-specific comparison row drift"
    ),
    "comparison-removed": "comparison identity set drift",
    "terminal-relation-behind": "C12 terminal ancestry relation drift",
    "negative-control-nonzero": (
        "negative-control counts drift; exactly one partial-clone registry is required"
    ),
    "partial-clone-observation-hidden": (
        "negative-control counts drift; exactly one partial-clone registry is required"
    ),
    "negative-control-removed": "negative-control set drift",
    "promisor-marker-count": (
        "$.object_availability.partial_clone_observations[0].promisor_pack_marker_count: "
        "value does not match const"
    ),
    "observed-head-missing-object": (
        "$.object_availability.partial_clone_observations[0].missing_object_count: "
        "value does not match const"
    ),
    "observed-head-global-completeness-overclaim": (
        "$.object_availability.partial_clone_observations[0]."
        "global_registry_completeness_established: value does not match const"
    ),
    "bundle-replay-fsck": (
        "$.object_availability.custody_replays[0].fsck_full_strict_no_reflogs_passed: "
        "value does not match const"
    ),
    "bundle-replay-archive-object": "c10-forensic isolated bundle-custody replay drift",
    "bundle-replay-custody-artifact": "c10-forensic isolated bundle-custody replay drift",
    "coherent-object-availability-reprojection": (
        "$.object_availability.partial_clone_observations[0].promisor_pack_marker_count: "
        "value does not match const"
    ),
    "custody-digest": "summary is not the exact derived projection",
    "custody-publicization": "restricted-nonpublic custody boundary drift",
    "custody-boundary-removed": "custody boundary inventory drift",
    "cache-byte-total": "cache allocated-byte total drift",
    "cache-count-invented": "cache candidate count must remain explicitly unestablished",
    "cache-deletion-authority": (
        "$.cache_candidates.deletion_authorized: value does not match const"
    ),
    "unreachable-exact-identity": "unreachable and reachable commit identities collapse",
    "unreachable-tree-claim": (
        "$.unreachable_commit_pairs[0].tree_identity_equal: value does not match const"
    ),
    "unreachable-custody-bound": (
        "$.unreachable_commit_pairs[0].custody_bound: value does not match const"
    ),
    "unreachable-pair-retains-registry": (
        "$.unreachable_commit_pairs[0].registry_retention_required_for_pair: "
        "value does not match const"
    ),
    "unreachable-advertised-object": (
        "pair custody evidence does not match the public preservation receipt"
    ),
    "unreachable-custody-artifact-reference": (
        "pair custody evidence does not match the public preservation receipt"
    ),
    "coherent-pair-custody-reprojection": (
        "pair custody evidence does not match the public preservation receipt"
    ),
    "unreachable-disposition": (
        "$.unreachable_commit_pairs[0].disposition: value does not match const"
    ),
    "registry-deletion-authority": (
        "$.authorization.registry_deletion_authorized: value does not match const"
    ),
    "checker-contract-external-replay": (
        "$.checker_contract.external_replay_required_for_cleanup: value does not match const"
    ),
    "c12-pair-retention-reintroduced": (
        "$.authorization.c12_custody_bound_pairs_require_registry_retention: "
        "value does not match const"
    ),
    "retention-basis-overreach": (
        "$.authorization.retention_basis: value does not match const"
    ),
    "garbage-collection-authority": (
        "$.authorization.garbage_collection_authorized: value does not match const"
    ),
    "absolute-locator": "$.limitations[0]: absolute or home-relative locator is prohibited",
    "private-transport-locator": (
        "$.limitations[0]: prohibited locator or secret-like fragment"
    ),
    "secret-like-fragment": "$.limitations[0]: prohibited locator or secret-like fragment",
    "summary-count": "summary is not the exact derived projection",
    "summary-digest": "summary is not the exact derived projection",
}
SECTION_SEAL_DIAGNOSTICS = {
    "coherent-cache-reprojection": "cache example inventory digest drift",
    "coherent-unreachable-reprojection": "unreachable-pair inventory digest drift",
}
ENVELOPE_SEAL_DIAGNOSTICS = {
    "limitation-removed": "semantic envelope drift",
}
SCHEMA_DIAGNOSTICS = {
    "schema-open-root": "$schema: every object schema must set additionalProperties=false",
    "schema-optional-root-property": (
        "$schema: closed object must require every declared property"
    ),
    "schema-unknown-keyword": "$schema: unsupported schema keywords: ['unevaluatedProperties']",
    "schema-external-reference": (
        "external or unsupported schema reference: https://example.invalid/schema"
    ),
    "schema-open-definition": (
        "$schema.$defs.worktree: every object schema must set additionalProperties=false"
    ),
    "schema-unresolved-reference": "unresolved schema reference: #/$defs/missing",
}
PARSER_DIAGNOSTICS = {
    "duplicate-json-key": "duplicate JSON key: schema_id",
    "nonfinite-json-number": "non-finite JSON number is prohibited: NaN",
}


def run_cli(optimized: bool, *, ambient_pythonpath: Path) -> None:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-S", "-B", str(CHECKER_PATH)))
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(ambient_pythonpath)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    require(
        completed.returncode == 0,
        f"production checker failed under {'-O' if optimized else 'normal'} mode: "
        f"{completed.stdout}{completed.stderr}",
    )
    require(
        completed.stdout.startswith("PASS sibling-registry retirement ledger:"),
        "production checker did not emit its PASS contract",
    )


def exercise_ambient_import_isolation() -> int:
    with tempfile.TemporaryDirectory(prefix="pid-rs-sibling-ledger-import-") as directory:
        poison_root = Path(directory)
        marker = "PID_RS_AMBIENT_IMPORT_EXECUTED"
        (poison_root / "hashlib.py").write_text(
            f"raise RuntimeError({marker!r})\n",
            encoding="utf-8",
        )
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(poison_root)
        unisolated = subprocess.run(
            [sys.executable, "-S", "-B", "-c", "import hashlib"],
            cwd=ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        require(
            unisolated.returncode != 0 and marker in unisolated.stderr,
            "ambient PYTHONPATH poison was not effective without isolated mode",
        )
        run_cli(optimized=False, ambient_pythonpath=poison_root)
        run_cli(optimized=True, ambient_pythonpath=poison_root)
    return 3


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    ledger_raw = CHECKER.read_single_link_regular(ROOT / CHECKER.LEDGER_RELATIVE)
    schema_raw = CHECKER.read_single_link_regular(ROOT / CHECKER.SCHEMA_RELATIVE)
    ledger = CHECKER.parse_json(ledger_raw, "self-test ledger")
    schema = CHECKER.validate_schema_document(
        CHECKER.parse_json(schema_raw, "self-test schema")
    )
    CHECKER.validate_ledger_document(ledger, schema)
    return ledger, schema, ledger_raw, schema_raw


def expect_ledger_rejection(
    name: str,
    ledger: dict[str, Any],
    schema: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> str:
    candidate = copy.deepcopy(ledger)
    mutate(candidate)
    diagnostic_sets = (
        PREDICATE_DIAGNOSTICS,
        SECTION_SEAL_DIAGNOSTICS,
        ENVELOPE_SEAL_DIAGNOSTICS,
    )
    membership_count = sum(name in diagnostics for diagnostics in diagnostic_sets)
    require(membership_count == 1, f"{name}: expected exactly one diagnostic class")
    if name in PREDICATE_DIAGNOSTICS:
        expected = PREDICATE_DIAGNOSTICS[name]
        enforce_sections = False
        enforce_envelope = False
    elif name in SECTION_SEAL_DIAGNOSTICS:
        expected = SECTION_SEAL_DIAGNOSTICS[name]
        enforce_sections = True
        enforce_envelope = False
    else:
        expected = ENVELOPE_SEAL_DIAGNOSTICS[name]
        enforce_sections = False
        enforce_envelope = True
    try:
        CHECKER.validate_ledger_document(
            candidate,
            schema,
            enforce_section_digests=enforce_sections,
            enforce_semantic_envelope=enforce_envelope,
        )
    except CHECKER.LedgerError as exc:
        require(
            str(exc) == expected,
            f"{name}: expected causal diagnostic {expected!r}, observed {str(exc)!r}",
        )
        return name
    raise SelfTestError(f"ledger mutation survived: {name}")


def exercise_path_custody_controls() -> int:
    rejections = 0

    def expect_path_rejected(label: str, path: Path, expected_fragment: str) -> None:
        nonlocal rejections
        try:
            CHECKER.read_single_link_regular(path)
        except CHECKER.LedgerError as exc:
            require(
                expected_fragment in str(exc),
                f"{label}: wrong path-custody diagnostic: {str(exc)!r}",
            )
            rejections += 1
            return
        raise SelfTestError(f"{label}: unsafe path was accepted")

    with tempfile.TemporaryDirectory(prefix="pid-rs-sibling-ledger-path-") as directory:
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
        original_read = CHECKER.os.read
        replaced = False

        def replace_during_read(descriptor: int, amount: int) -> bytes:
            nonlocal replaced
            if not replaced:
                os.replace(replacement, target)
                replaced = True
            return original_read(descriptor, amount)

        CHECKER.os.read = replace_during_read
        try:
            expect_path_rejected(
                target.name,
                target,
                "required file identity changed during read",
            )
        finally:
            CHECKER.os.read = original_read

    require(rejections == 3, f"path-custody rejection count drift: {rejections}")
    return rejections


def expect_schema_rejection(
    name: str,
    schema: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> str:
    candidate = copy.deepcopy(schema)
    mutate(candidate)
    require(name in SCHEMA_DIAGNOSTICS, f"{name}: schema diagnostic is not declared")
    try:
        CHECKER.validate_schema_document(candidate)
    except CHECKER.LedgerError as exc:
        require(
            str(exc) == SCHEMA_DIAGNOSTICS[name],
            f"{name}: expected causal schema diagnostic {SCHEMA_DIAGNOSTICS[name]!r}, "
            f"observed {str(exc)!r}",
        )
        return name
    raise SelfTestError(f"schema mutation survived: {name}")


def expect_parse_rejection(name: str, raw: bytes) -> str:
    require(name in PARSER_DIAGNOSTICS, f"{name}: parser diagnostic is not declared")
    try:
        CHECKER.parse_json(raw, name)
    except CHECKER.LedgerError as exc:
        require(
            str(exc) == PARSER_DIAGNOSTICS[name],
            f"{name}: expected causal parser diagnostic {PARSER_DIAGNOSTICS[name]!r}, "
            f"observed {str(exc)!r}",
        )
        return name
    raise SelfTestError(f"JSON parser mutation survived: {name}")


def status_rows(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for registry in candidate["registries"]:
        for worktree in registry["worktrees"]:
            rows.append(
                {
                    "capture_sha256": worktree["status"]["capture_sha256"],
                    "registry_id": registry["registry_id"],
                    "staged": worktree["status"]["staged"],
                    "unstaged": worktree["status"]["unstaged"],
                    "untracked": worktree["status"]["untracked"],
                    "worktree_id": worktree["worktree_id"],
                }
            )
    return rows


def coherent_status_mutation(candidate: dict[str, Any]) -> None:
    candidate["registries"][0]["worktrees"][0]["status"]["unstaged"] = 17
    rows = status_rows(candidate)
    candidate["summary"]["total_unstaged"] = sum(row["unstaged"] for row in rows)
    candidate["summary"]["status_inventory_sha256"] = CHECKER.canonical_sha256(rows)
    candidate["summary"]["registry_inventory_sha256"] = CHECKER.canonical_sha256(
        candidate["registries"]
    )


def coherent_comparison_mutation(candidate: dict[str, Any]) -> None:
    candidate["comparisons"][0]["exact"] = 1
    candidate["comparisons"][0]["evolved"] = 22
    candidate["summary"]["comparison_exact"] = sum(
        item["exact"] for item in candidate["comparisons"]
    )
    candidate["summary"]["comparison_evolved"] = sum(
        item["evolved"] for item in candidate["comparisons"]
    )
    candidate["summary"]["comparison_inventory_sha256"] = CHECKER.canonical_sha256(
        candidate["comparisons"]
    )


def coherent_cache_mutation(candidate: dict[str, Any]) -> None:
    candidate["cache_candidates"]["examples"][0]["approximate_decimal_gb"] = 10.55
    candidate["summary"]["cache_example_inventory_sha256"] = CHECKER.canonical_sha256(
        candidate["cache_candidates"]["examples"]
    )


def coherent_unreachable_mutation(candidate: dict[str, Any]) -> None:
    candidate["unreachable_commit_pairs"][0]["stable_patch_id"] = "0" * 40
    candidate["summary"]["unreachable_pair_inventory_sha256"] = CHECKER.canonical_sha256(
        candidate["unreachable_commit_pairs"]
    )


def coherent_publication_checkpoint_mutation(candidate: dict[str, Any]) -> None:
    candidate["registries"][7]["archive_checkpoint"]["tree_sha1"] = "0" * 40
    candidate["summary"]["registry_inventory_sha256"] = CHECKER.canonical_sha256(
        candidate["registries"]
    )


def coherent_object_availability_mutation(candidate: dict[str, Any]) -> None:
    candidate["object_availability"]["partial_clone_observations"][0][
        "promisor_pack_marker_count"
    ] = 5
    candidate["summary"]["object_availability_inventory_sha256"] = (
        CHECKER.canonical_sha256(candidate["object_availability"])
    )


def coherent_pair_custody_mutation(candidate: dict[str, Any]) -> None:
    candidate["unreachable_commit_pairs"][0]["custody_binding"][
        "bundle_byte_size"
    ] -= 1
    candidate["summary"]["unreachable_pair_inventory_sha256"] = (
        CHECKER.canonical_sha256(candidate["unreachable_commit_pairs"])
    )


def main() -> int:
    source = CHECKER_PATH.read_text(encoding="utf-8")
    parsed_source = ast.parse(source)
    require(
        not any(isinstance(node, ast.Assert) for node in ast.walk(parsed_source)),
        "checker must not depend on assert statements",
    )
    ambient_import_controls = exercise_ambient_import_isolation()
    ledger, schema, ledger_raw, schema_raw = load_inputs()

    mutations: list[str] = []
    cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("unknown-top-level-key", lambda item: item.__setitem__("unknown", 1)),
        ("record-identity", lambda item: item.__setitem__("record_id", "SRRL-20260901-02")),
        (
            "observation-start",
            lambda item: item["observation"].__setitem__("started_at_utc", "2026-09-01T07:32:08Z"),
        ),
        (
            "observation-end",
            lambda item: item["observation"].__setitem__("ended_at_utc", "2026-09-01T07:38:42Z"),
        ),
        (
            "git-version",
            lambda item: item["observation"].__setitem__("git_version", "2.54.0"),
        ),
        (
            "live-main-identity",
            lambda item: item["reference_commits"][0].__setitem__("commit_sha1", "0" * 40),
        ),
        ("registry-removed", lambda item: item["registries"].pop()),
        (
            "common-directory-collision",
            lambda item: item["registries"][1].__setitem__(
                "common_git_directory_id", item["registries"][0]["common_git_directory_id"]
            ),
        ),
        (
            "registry-head",
            lambda item: item["registries"][0].__setitem__("registry_head_sha1", "0" * 40),
        ),
        (
            "registry-tree",
            lambda item: item["registries"][0].__setitem__("registry_tree_sha1", "0" * 40),
        ),
        (
            "c12-worktree-removed",
            lambda item: item["registries"][4]["worktrees"].pop(),
        ),
        (
            "bare-with-worktree",
            lambda item: item["registries"][6].__setitem__(
                "worktrees", [copy.deepcopy(item["registries"][5]["worktrees"][0])]
            ),
        ),
        (
            "detached-branch-label",
            lambda item: item["registries"][9]["worktrees"][0].__setitem__(
                "branch_label", "science-synthesis"
            ),
        ),
        (
            "staged-path",
            lambda item: item["registries"][0]["worktrees"][0]["status"].__setitem__("staged", 1),
        ),
        (
            "clean-status-digest",
            lambda item: item["registries"][3]["worktrees"][0]["status"].__setitem__(
                "capture_sha256", "0" * 64
            ),
        ),
        ("coherent-status-reprojection", coherent_status_mutation),
        (
            "publication-archive-full-identity-truncated",
            lambda item: item["registries"][7]["archive_checkpoint"].__setitem__(
                "object_identifier", "df22846a"
            ),
        ),
        (
            "publication-archive-tree",
            lambda item: item["registries"][7]["archive_checkpoint"].__setitem__(
                "tree_sha1", "0" * 40
            ),
        ),
        (
            "publication-archive-parent",
            lambda item: item["registries"][7]["archive_checkpoint"].__setitem__(
                "parent_sha1", "0" * 40
            ),
        ),
        ("coherent-publication-checkpoint-reprojection", coherent_publication_checkpoint_mutation),
        (
            "archive-status-kind",
            lambda item: item["registries"][0]["archive_checkpoint"].__setitem__(
                "identifier_kind", "sha1_prefix_7"
            ),
        ),
        (
            "comparison-partition",
            lambda item: item["comparisons"][0].__setitem__("total", 34),
        ),
        (
            "comparison-target",
            lambda item: item["comparisons"][0].__setitem__("target_id", "integration-candidate"),
        ),
        (
            "c12-candidate-labelled-remote-main",
            lambda item: item["comparisons"][3].__setitem__("target_id", "live-remote-main"),
        ),
        (
            "c12-remote-main-labelled-candidate",
            lambda item: item["comparisons"][4].__setitem__("target_id", "integration-candidate"),
        ),
        ("coherent-comparison-reprojection", coherent_comparison_mutation),
        ("comparison-removed", lambda item: item["comparisons"].pop()),
        (
            "terminal-relation-behind",
            lambda item: item["relations"][0].__setitem__("behind", 51),
        ),
        (
            "negative-control-nonzero",
            lambda item: item["negative_controls"][0].__setitem__("observed_count", 1),
        ),
        (
            "partial-clone-observation-hidden",
            lambda item: item["negative_controls"][7].__setitem__("observed_count", 0),
        ),
        ("negative-control-removed", lambda item: item["negative_controls"].pop()),
        (
            "promisor-marker-count",
            lambda item: item["object_availability"]["partial_clone_observations"][0].__setitem__(
                "promisor_pack_marker_count", 5
            ),
        ),
        (
            "observed-head-missing-object",
            lambda item: item["object_availability"]["partial_clone_observations"][0].__setitem__(
                "missing_object_count", 1
            ),
        ),
        (
            "observed-head-global-completeness-overclaim",
            lambda item: item["object_availability"]["partial_clone_observations"][0].__setitem__(
                "global_registry_completeness_established", True
            ),
        ),
        (
            "bundle-replay-fsck",
            lambda item: item["object_availability"]["custody_replays"][0].__setitem__(
                "fsck_full_strict_no_reflogs_passed", False
            ),
        ),
        (
            "bundle-replay-archive-object",
            lambda item: item["object_availability"]["custody_replays"][0].__setitem__(
                "archive_commit_sha1", "0" * 40
            ),
        ),
        (
            "bundle-replay-custody-artifact",
            lambda item: item["object_availability"]["custody_replays"][0].__setitem__(
                "custody_artifact_id", "custody-c12-milestone2-public-receipt-bundle"
            ),
        ),
        ("coherent-object-availability-reprojection", coherent_object_availability_mutation),
        (
            "custody-digest",
            lambda item: item["custody_artifacts"][0].__setitem__("sha256", "0" * 64),
        ),
        (
            "custody-publicization",
            lambda item: item["custody_artifacts"][4].__setitem__("custody_class", "restricted"),
        ),
        ("custody-boundary-removed", lambda item: item["custody_boundaries"].pop()),
        (
            "cache-byte-total",
            lambda item: item["cache_candidates"].__setitem__("allocated_bytes", 52718612479),
        ),
        (
            "cache-count-invented",
            lambda item: item["cache_candidates"].__setitem__("candidate_count", 11),
        ),
        (
            "cache-deletion-authority",
            lambda item: item["cache_candidates"].__setitem__("deletion_authorized", True),
        ),
        ("coherent-cache-reprojection", coherent_cache_mutation),
        (
            "unreachable-exact-identity",
            lambda item: item["unreachable_commit_pairs"][0].__setitem__(
                "reachable_commit_sha1",
                item["unreachable_commit_pairs"][0]["unreachable_commit_sha1"],
            ),
        ),
        (
            "unreachable-tree-claim",
            lambda item: item["unreachable_commit_pairs"][0].__setitem__(
                "tree_identity_equal", False
            ),
        ),
        (
            "unreachable-custody-bound",
            lambda item: item["unreachable_commit_pairs"][0].__setitem__(
                "custody_bound", False
            ),
        ),
        (
            "unreachable-pair-retains-registry",
            lambda item: item["unreachable_commit_pairs"][0].__setitem__(
                "registry_retention_required_for_pair", True
            ),
        ),
        (
            "unreachable-advertised-object",
            lambda item: item["unreachable_commit_pairs"][0]["custody_binding"].__setitem__(
                "advertised_object_sha1", "0" * 40
            ),
        ),
        (
            "unreachable-custody-artifact-reference",
            lambda item: item["unreachable_commit_pairs"][0]["custody_binding"].__setitem__(
                "custody_artifact_id", "custody-c12-milestone1-public-receipt-bundle"
            ),
        ),
        ("coherent-pair-custody-reprojection", coherent_pair_custody_mutation),
        ("coherent-unreachable-reprojection", coherent_unreachable_mutation),
        (
            "unreachable-disposition",
            lambda item: item["unreachable_commit_pairs"][0].__setitem__(
                "disposition", "integrated"
            ),
        ),
        (
            "registry-deletion-authority",
            lambda item: item["authorization"].__setitem__("registry_deletion_authorized", True),
        ),
        (
            "checker-contract-external-replay",
            lambda item: item["checker_contract"].__setitem__(
                "external_replay_required_for_cleanup", False
            ),
        ),
        (
            "c12-pair-retention-reintroduced",
            lambda item: item["authorization"].__setitem__(
                "c12_custody_bound_pairs_require_registry_retention", True
            ),
        ),
        (
            "retention-basis-overreach",
            lambda item: item["authorization"].__setitem__(
                "retention_basis", "all_observed_scope"
            ),
        ),
        (
            "garbage-collection-authority",
            lambda item: item["authorization"].__setitem__("garbage_collection_authorized", True),
        ),
        ("limitation-removed", lambda item: item["limitations"].pop()),
        (
            "absolute-locator",
            lambda item: item["limitations"].__setitem__(
                0, "/" + "Users" + "/example/registry"
            ),
        ),
        (
            "private-transport-locator",
            lambda item: item["limitations"].__setitem__(0, "git" + "@host:owner/repo"),
        ),
        (
            "secret-like-fragment",
            lambda item: item["limitations"].__setitem__(0, "gh" + "p_exampletoken"),
        ),
        (
            "summary-count",
            lambda item: item["summary"].__setitem__("worktree_count", 13),
        ),
        (
            "summary-digest",
            lambda item: item["summary"].__setitem__("registry_inventory_sha256", "0" * 64),
        ),
    ]
    case_names = {name for name, _mutate in cases}
    diagnostic_names = (
        set(PREDICATE_DIAGNOSTICS)
        | set(SECTION_SEAL_DIAGNOSTICS)
        | set(ENVELOPE_SEAL_DIAGNOSTICS)
    )
    require(
        case_names == diagnostic_names and len(case_names) == len(cases),
        "ledger mutation cases and causal diagnostic inventory drifted",
    )
    require(
        len(PREDICATE_DIAGNOSTICS) == 62
        and len(SECTION_SEAL_DIAGNOSTICS) == 2
        and len(ENVELOPE_SEAL_DIAGNOSTICS) == 1,
        "predicate/section/envelope mutation partition drifted",
    )
    for name, mutate in cases:
        mutations.append(expect_ledger_rejection(name, ledger, schema, mutate))

    schema_cases: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        (
            "schema-open-root",
            lambda item: item.__setitem__("additionalProperties", True),
        ),
        (
            "schema-optional-root-property",
            lambda item: item["required"].remove("authorization"),
        ),
        (
            "schema-unknown-keyword",
            lambda item: item.__setitem__("unevaluatedProperties", False),
        ),
        (
            "schema-external-reference",
            lambda item: item["properties"]["summary"].__setitem__(
                "$ref", "https://example.invalid/schema"
            ),
        ),
        (
            "schema-open-definition",
            lambda item: item["$defs"]["worktree"].__setitem__("additionalProperties", True),
        ),
        (
            "schema-unresolved-reference",
            lambda item: item["properties"]["summary"].__setitem__(
                "$ref", "#/$defs/missing"
            ),
        ),
    ]
    require(
        {name for name, _mutate in schema_cases} == set(SCHEMA_DIAGNOSTICS),
        "schema mutation cases and diagnostic inventory drifted",
    )
    for name, mutate in schema_cases:
        mutations.append(expect_schema_rejection(name, schema, mutate))

    mutations.append(
        expect_parse_rejection(
            "duplicate-json-key",
            b'{"schema_id":"one","schema_id":"two"}',
        )
    )
    mutations.append(expect_parse_rejection("nonfinite-json-number", b'{"value":NaN}'))

    try:
        CHECKER.validate_artifacts(ledger_raw + b"\n", schema_raw)
    except CHECKER.LedgerError as exc:
        require(
            str(exc) == "ledger file SHA-256 drift",
            f"ledger-byte-drift: wrong exact-byte diagnostic: {str(exc)!r}",
        )
        mutations.append("ledger-byte-drift")
    else:
        raise SelfTestError("ledger byte drift survived production pins")
    try:
        CHECKER.validate_artifacts(ledger_raw, schema_raw + b"\n")
    except CHECKER.LedgerError as exc:
        require(
            str(exc) == "schema file SHA-256 drift",
            f"schema-byte-drift: wrong exact-byte diagnostic: {str(exc)!r}",
        )
        mutations.append("schema-byte-drift")
    else:
        raise SelfTestError("schema byte drift survived production pins")

    require(len(mutations) == 75, f"hostile mutation count drift: {len(mutations)}")
    path_custody_rejections = exercise_path_custody_controls()
    print(
        "PASS sibling-registry retirement ledger hostile self-test: "
        f"{len(mutations)} mutations rejected "
        "(predicate=62, section-seal=2, envelope-seal=1, schema/parser/exact-byte=10); "
        f"path-custody={path_custody_rejections}; "
        f"ambient-import-controls={ambient_import_controls}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SelfTestError as exc:
        print(f"FAIL sibling-registry retirement ledger self-test: {exc}", file=sys.stderr)
        raise SystemExit(1)
