#!/usr/bin/env python3
"""Mutation suite for the Pandoc receipt and retained-replay adjudication."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from typing import Any, NoReturn


ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-mathematical-results-guide-pandoc-portability-receipt.py"
RECEIPT_RELATIVE = pathlib.Path(
    "audit/evidence/mathematical-results-guide-pandoc-3.1.3-portability-v1.json"
)
RECEIPT = ROOT / RECEIPT_RELATIVE
RETAINED_RELATIVE = pathlib.Path(
    "audit/evidence/"
    "mathematical-results-guide-pandoc-3.1.3-texlive-2023-font-alpha.pdf"
)
EXPECTED_SUCCESS = (
    "OK: historical Pandoc 3.1.3 observation plus raw-bound retained replay adjudication "
    "(translated_x86_64=yes; native_x86_64=no; normalization_deltas=25; "
    "historical_destinations=39; retained_relation=raw-then-typed; "
    "superseded_false_positives=2; retained_pdf=tracked)\n"
)
FAILURE_PREFIX = "Pandoc portability receipt check failed:"
HASH_LINE = re.compile(r'^RECEIPT_SHA256 = "[0-9a-f]{64}"$', re.MULTILINE)
EXPECTED_COUNTS = (2, 100, 12)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"Pandoc portability receipt self-test failed: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


try:
    PHYSICAL_TEMP_ROOT = pathlib.Path(tempfile.gettempdir()).resolve(strict=True)
except OSError as error:
    fail(f"cannot resolve the platform temporary directory: {error}")
require(PHYSICAL_TEMP_ROOT.is_dir(), "resolved temporary root is not a directory")
require(CHECKER.is_file() and not CHECKER.is_symlink(), "checker is absent or symbolic")
require(RECEIPT.is_file() and not RECEIPT.is_symlink(), "receipt is absent or symbolic")

BASELINE_BYTES = RECEIPT.read_bytes()
try:
    BASELINE = json.loads(BASELINE_BYTES.decode("utf-8"))
except (UnicodeDecodeError, json.JSONDecodeError) as error:
    fail(f"baseline receipt is invalid: {error}")
require(isinstance(BASELINE, dict), "baseline receipt root is not an object")
REPOSITORY_INPUTS = tuple(BASELINE["current_selected_repository_input_digests"])


def copy_fixture(directory: pathlib.Path) -> tuple[pathlib.Path, pathlib.Path]:
    fixture_root = directory / "repository"
    fixture_checker = (
        fixture_root
        / "scripts/check-mathematical-results-guide-pandoc-portability-receipt.py"
    )
    fixture_receipt = fixture_root / RECEIPT_RELATIVE
    fixture_checker.parent.mkdir(parents=True)
    fixture_receipt.parent.mkdir(parents=True)
    shutil.copyfile(CHECKER, fixture_checker)
    shutil.copyfile(RECEIPT, fixture_receipt)
    for relative in REPOSITORY_INPUTS:
        source = ROOT / relative
        destination = fixture_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return fixture_checker, fixture_receipt


def patch_receipt_digest(checker: pathlib.Path, receipt_bytes: bytes) -> None:
    source = checker.read_text(encoding="utf-8")
    replacement = f'RECEIPT_SHA256 = "{hashlib.sha256(receipt_bytes).hexdigest()}"'
    mutated, count = HASH_LINE.subn(replacement, source)
    require(count == 1, "checker receipt-digest anchor changed")
    checker.write_text(mutated, encoding="utf-8", newline="\n")


def invoke(checker: pathlib.Path, optimized: bool, *extra: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command.extend(("-I", "-B", str(checker), *extra))
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
        env={"PATH": os.environ.get("PATH", "")},
    )


def require_pass(result: subprocess.CompletedProcess[str], name: str) -> None:
    require(result.returncode == 0, f"{name} failed: {result.stderr!r}")
    require(result.stdout == EXPECTED_SUCCESS, f"{name} stdout changed: {result.stdout!r}")
    require(result.stderr == "", f"{name} emitted stderr: {result.stderr!r}")


def require_fail(result: subprocess.CompletedProcess[str], name: str) -> None:
    require(result.returncode != 0, f"{name} unexpectedly passed")
    require(result.stdout == "", f"{name} emitted stdout: {result.stdout!r}")
    require(FAILURE_PREFIX in result.stderr, f"{name} failed outside the checker: {result.stderr!r}")


def encoded(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


Mutation = Callable[[dict[str, Any]], None]


def semantic_mutations() -> tuple[tuple[str, Mutation], ...]:
    def set_path(*path_and_value: Any) -> Mutation:
        *path, value = path_and_value

        def mutate(document: dict[str, Any]) -> None:
            target: Any = document
            for component in path[:-1]:
                target = target[component]
            target[path[-1]] = value

        return mutate

    return (
        ("schema", set_path("schema", "pid-rs.wrong.v1")),
        ("status", set_path("status", "closed_native_execution_receipt")),
        ("evidence_class", set_path("evidence_class", "authenticated execution")),
        ("capture_time", set_path("captured_at_utc", "2026-08-29T11:21:05Z")),
        ("subject", set_path("subject", "README.md")),
        ("parent", set_path("source_state", "parent_commit", "0" * 40)),
        ("historical_parent", set_path("source_state", "historical_ksg_c3_parent", "0" * 40)),
        ("historical_child", set_path("source_state", "historical_ksg_c3_child", "0" * 40)),
        ("committed_capture", set_path("source_state", "working_tree_was_uncommitted", False)),
        ("native_hardware", set_path("execution_environment", "container", "native_x86_64_hardware", True)),
        (
            "oci_object_conflation",
            set_path(
                "execution_environment",
                "container",
                "linux_amd64_config_digest",
                "sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea",
            ),
        ),
        ("pandoc_version", set_path("execution_environment", "old_tools", "pandoc", "version", "3.10.2")),
        ("pandoc_digest", set_path("execution_environment", "old_tools", "pandoc", "sha256", "0" * 64)),
        ("normalizer_mode", set_path("normalization_observation", "mode", "canonical")),
        ("heading_delta", set_path("normalization_observation", "heading_wrappers_removed", 16)),
        ("raw_tex_digest", set_path("normalization_observation", "legacy_raw_tex", "sha256", "0" * 64)),
        ("negative_destination_count", set_path("pre_normalization_observation", "destination_count", 39)),
        ("malformed_claim", set_path("pre_normalization_observation", "interpretation", "malformed exploit")),
        ("final_destination_count", set_path("final_run_observation", "destination_count", 56)),
        ("navigation_count", set_path("final_run_observation", "navigation_records", 166)),
        ("gate_status", set_path("operator_reported_complete_gate_run", "status", "failed")),
        ("render_equality", set_path("operator_reported_poppler_comparison", "all_page_png_bytes_equal", False)),
        ("qemu_credit", set_path("negative_execution_evidence", "credit", "portability")),
        ("tracked_raw", set_path("artifact_retention", "raw_tex_tracked", True)),
        (
            "historical_retention_reason",
            set_path(
                "artifact_retention",
                "reason",
                "the later retained replay is one of the historical outputs",
            ),
        ),
        (
            "executable_causation_overclaim",
            set_path(
                "recorded_observations",
                0,
                "the exact hash-bound Pandoc 3.1.3 executable was invoked",
            ),
        ),
        ("missing_nonclaim", lambda document: document["does_not_establish"].pop()),
        ("extra_observation", lambda document: document["recorded_observations"].append("general equivalence")),
        ("repository_input_digest", lambda document: document["current_selected_repository_input_digests"].__setitem__("MATHEMATICAL_RESULTS_GUIDE.md", "0" * 64)),
        (
            "source_delta_classification",
            set_path(
                "post_observation_source_delta",
                "classification",
                "all changes covered by the old execution",
            ),
        ),
        (
            "source_delta_changed_path",
            lambda document: document["post_observation_source_delta"][
                "changed_paths"
            ].pop(),
        ),
        (
            "source_delta_credit_boundary",
            set_path(
                "post_observation_source_delta",
                "credit_boundary",
                "the earlier operator observation proves the corrected sources",
            ),
        ),
        (
            "replay_source_delta_inventory",
            lambda document: document["post_observation_source_delta"][
                "retained_replay_adjudication_changes"
            ].pop(),
        ),
        (
            "replay_structure_current_digest",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                0,
                "current_sha256",
                "0" * 64,
            ),
        ),
        (
            "replay_wrapper_baseline_digest",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                1,
                "pre_adjudication_sha256",
                "0" * 64,
            ),
        ),
        (
            "replay_added_path_state",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                2,
                "pre_adjudication_state",
                "present",
            ),
        ),
        (
            "replay_artifact_bytes",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                5,
                "bytes",
                581295,
            ),
        ),
        (
            "replay_wrapper_raw_baseline",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                1,
                "pre_raw_binding_sha256",
                "0" * 64,
            ),
        ),
        (
            "replay_comparator_superseded_digest",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                2,
                "superseded_sha256",
                "0" * 64,
            ),
        ),
        (
            "replay_comparator_zero_credit",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                2,
                "superseded_disposition",
                "accepted",
            ),
        ),
        (
            "replay_selftest_current_digest",
            set_path(
                "post_observation_source_delta",
                "retained_replay_adjudication_changes",
                3,
                "current_sha256",
                "0" * 64,
            ),
        ),
        (
            "retained_scope",
            set_path("retained_replay_adjudication", "scope", "the historical bytes were recovered"),
        ),
        (
            "retained_path",
            set_path(
                "retained_replay_adjudication",
                "retained_pdf",
                "path",
                "output/pdf/mathematical-results-guide.pdf",
            ),
        ),
        (
            "retained_bytes",
            set_path("retained_replay_adjudication", "retained_pdf", "bytes", 581295),
        ),
        (
            "retained_digest",
            set_path("retained_replay_adjudication", "retained_pdf", "sha256", "0" * 64),
        ),
        (
            "canonical_bytes",
            set_path("retained_replay_adjudication", "canonical_reference", "bytes", 581313),
        ),
        (
            "canonical_digest",
            set_path(
                "retained_replay_adjudication",
                "canonical_reference",
                "sha256",
                "0" * 64,
            ),
        ),
        (
            "raw_structure_status",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "status",
                "passed",
            ),
        ),
        (
            "retained_structure_digest",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "retained_structure_sha256",
                "e9adba3097ffc38de2f7723e448d2bb54265ee201e010c0857e1a7a40db9d99b",
            ),
        ),
        (
            "retained_navigation_digest",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "retained_navigation_sha256",
                "95ca1981ffb665ad4f0b9cb72d2ae508f76ae90814669ca910bc41de55aadcf8",
            ),
        ),
        (
            "navigation_difference_count",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "differing_navigation_records",
                0,
            ),
        ),
        (
            "invariant_record_count",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "invariant_records",
                1668,
            ),
        ),
        (
            "variant_partition",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "difference_partition",
                "other_records",
                1,
            ),
        ),
        (
            "historical_claim_adjudication",
            set_path(
                "retained_replay_adjudication",
                "raw_strict_structure_replay",
                "historical_claim_adjudication",
                "the earlier strict result is confirmed",
            ),
        ),
        (
            "font_alpha_status",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "status",
                "generic_equivalence",
            ),
        ),
        (
            "font_alpha_checker",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "checker",
                "scripts/check-mathematical-results-guide-pdf-structure.py",
            ),
        ),
        (
            "font_alpha_retained_precondition",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "retained_fixture_precondition",
                "the parser recognized a PDF",
            ),
        ),
        (
            "font_alpha_ordered_obligation",
            lambda document: document["retained_replay_adjudication"][
                "typed_font_resource_alpha_equivalence"
            ]["operational_relation_composition"]["ordered_obligations"].pop(),
        ),
        (
            "font_alpha_id_checker_digest",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "operational_relation_composition",
                "strict_trailer_id_checker_sha256",
                "0" * 64,
            ),
        ),
        (
            "font_alpha_candidate_raw_relation",
            lambda document: document["retained_replay_adjudication"][
                "typed_font_resource_alpha_equivalence"
            ]["operational_relation_composition"]["candidate_raw_relations"].pop(),
        ),
        (
            "font_alpha_typed_core_boundary",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "operational_relation_composition",
                "typed_core_boundary",
                "the typed core proves all serialized bytes",
            ),
        ),
        (
            "font_alpha_operations",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "parsed_content_operations",
                16361,
            ),
        ),
        (
            "font_alpha_tf_uses",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "Tf_uses",
                1372,
            ),
        ),
        (
            "font_alpha_mapping_count",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "document_font_mappings",
                12,
            ),
        ),
        (
            "font_alpha_mapping_digest",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "mapping_manifest_sha256",
                "0" * 64,
            ),
        ),
        (
            "font_alpha_pair_modes",
            lambda document: document["retained_replay_adjudication"][
                "typed_font_resource_alpha_equivalence"
            ]["current_pair_check_modes"].pop(),
        ),
        (
            "font_alpha_selftest_path",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "fail_closed_self_test",
                "path",
                "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py",
            ),
        ),
        (
            "font_alpha_selftest_total",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "fail_closed_self_test",
                "total_cases_per_mode",
                106,
            ),
        ),
        (
            "font_alpha_selftest_semantic_count",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "fail_closed_self_test",
                "semantic_hostiles",
                35,
            ),
        ),
        (
            "font_alpha_selftest_profile_count",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "fail_closed_self_test",
                "source_profile_hostiles",
                8,
            ),
        ),
        (
            "font_alpha_selftest_raw_boundary_count",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "fail_closed_self_test",
                "raw_boundary_hostiles",
                9,
            ),
        ),
        (
            "font_alpha_wrapper_path",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "wrapper_mode_wiring_self_test",
                "wrapper",
                "scripts/build-mathematical-results-guide-pdf.sh",
            ),
        ),
        (
            "font_alpha_wiring_controls",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "wrapper_mode_wiring_self_test",
                "controls",
                10,
            ),
        ),
        (
            "font_alpha_exact_dispatch",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "wrapper_mode_wiring_self_test",
                "exact_mode_alpha_artifact_invocations",
                1,
            ),
        ),
        (
            "font_alpha_cross_dispatch",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "wrapper_mode_wiring_self_test",
                "cross_mode_alpha_python_invocations",
                1,
            ),
        ),
        (
            "font_alpha_wiring_boundary",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "wrapper_mode_wiring_self_test",
                "boundary",
                "the dispatch test proves the renderer",
            ),
        ),
        (
            "font_alpha_preservation",
            lambda document: document["retained_replay_adjudication"]
            ["typed_font_resource_alpha_equivalence"]["exactly_preserved"].pop(),
        ),
        (
            "font_alpha_serialized_preservation",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "exactly_preserved",
                0,
                "unreachable trailing bytes are ignored",
            ),
        ),
        (
            "font_alpha_raw_typed_lane_conflation",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "typed_object_graph_admitted_difference_after_raw_precondition",
                "the font-key rename and trailer-ID projection are both typed differences",
            ),
        ),
        (
            "font_alpha_scope",
            set_path(
                "retained_replay_adjudication",
                "typed_font_resource_alpha_equivalence",
                "scope_boundary",
                "all PDFs and toolchains",
            ),
        ),
        (
            "superseded_comparator_disposition",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "disposition",
                "accepted for verification credit",
            ),
        ),
        (
            "superseded_comparator_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "superseded_checker_sha256",
                "0" * 64,
            ),
        ),
        (
            "superseded_failure_mode",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "failure_mode",
                "the typed result bound every serialized byte",
            ),
        ),
        (
            "superseded_exact_mode_impact",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "exact_mode_impact",
                "exact mode accepted both witnesses",
            ),
        ),
        (
            "superseded_custody_overclaim",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "evidence_custody_boundary",
                "the predecessor source and complete logs are retained",
            ),
        ),
        (
            "superseded_witness_base_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "witness_base",
                "sha256",
                "0" * 64,
            ),
        ),
        (
            "superseded_reconstruction_rule",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "reconstruction",
                "the witnesses cannot be reconstructed",
            ),
        ),
        (
            "superseded_first_suffix_hex",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                0,
                "suffix_hex",
                "0d",
            ),
        ),
        (
            "superseded_first_witness_bytes",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                0,
                "witness_bytes",
                581296,
            ),
        ),
        (
            "superseded_first_witness_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                0,
                "witness_sha256",
                "0" * 64,
            ),
        ),
        (
            "superseded_first_cli_exit",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                0,
                "superseded_cli_exit_code",
                1,
            ),
        ),
        (
            "superseded_first_stdout_disposition",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                0,
                "superseded_cli_stdout_disposition",
                "emitted a rejection",
            ),
        ),
        (
            "superseded_second_suffix_utf8",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                1,
                "suffix_utf8",
                "\n% different comment\n",
            ),
        ),
        (
            "superseded_second_witness_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "actual_cli_false_positives",
                1,
                "witness_sha256",
                "0" * 64,
            ),
        ),
        (
            "corrected_comparator_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "correction",
                "current_checker_sha256",
                "0" * 64,
            ),
        ),
        (
            "corrected_permanent_hostile",
            lambda document: document["retained_replay_adjudication"][
                "superseded_comparator_negative_evidence"
            ]["correction"]["permanent_raw_boundary_hostiles"].pop(),
        ),
        (
            "corrected_regression_scope",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "correction",
                "regression_scope",
                "the suite replays the absent predecessor source",
            ),
        ),
        (
            "corrected_selftest_digest",
            set_path(
                "retained_replay_adjudication",
                "superseded_comparator_negative_evidence",
                "correction",
                "self_test_sha256",
                "0" * 64,
            ),
        ),
        (
            "historical_record_preservation",
            lambda document: document["retained_replay_adjudication"][
                "historical_record_preserved"
            ].pop(),
        ),
        (
            "engineering_boundary",
            set_path(
                "retained_replay_adjudication",
                "current_engineering_boundary",
                "this proves the PID mathematics",
            ),
        ),
    )


def run_mode(optimized: bool) -> tuple[int, int, int]:
    mode = "optimized" if optimized else "normal"
    controls = 0
    semantic_count = 0
    custody_count = 0
    custody_names: set[str] = set()

    with tempfile.TemporaryDirectory(
        prefix=f"pid-rs-pandoc-portability-{mode}-baseline-",
        dir=PHYSICAL_TEMP_ROOT,
    ) as temporary:
        checker, receipt = copy_fixture(pathlib.Path(temporary))
        require_pass(invoke(checker, optimized), f"{mode} exact baseline")
        controls += 1
        reencoded = encoded(copy.deepcopy(BASELINE))
        receipt.write_bytes(reencoded)
        patch_receipt_digest(checker, reencoded)
        require_pass(invoke(checker, optimized), f"{mode} semantic baseline")
        controls += 1

    mutations = semantic_mutations()
    mutation_names = [name for name, _mutation in mutations]
    require(
        len(mutations) == EXPECTED_COUNTS[1]
        and len(set(mutation_names)) == len(mutation_names),
        f"{mode} semantic mutation inventory changed or contains duplicate names",
    )
    for name, mutation in mutations:
        with tempfile.TemporaryDirectory(
            prefix=f"pid-rs-pandoc-portability-{mode}-{name}-",
            dir=PHYSICAL_TEMP_ROOT,
        ) as temporary:
            checker, receipt = copy_fixture(pathlib.Path(temporary))
            document = copy.deepcopy(BASELINE)
            mutation(document)
            mutated = encoded(document)
            receipt.write_bytes(mutated)
            patch_receipt_digest(checker, mutated)
            require_fail(invoke(checker, optimized), f"{mode} semantic {name}")
            semantic_count += 1

    def custody_case(name: str, action: Callable[[pathlib.Path, pathlib.Path], None]) -> None:
        nonlocal custody_count
        require(name not in custody_names, f"{mode} duplicate custody-case name: {name}")
        custody_names.add(name)
        with tempfile.TemporaryDirectory(
            prefix=f"pid-rs-pandoc-portability-{mode}-{name}-",
            dir=PHYSICAL_TEMP_ROOT,
        ) as temporary:
            checker, receipt = copy_fixture(pathlib.Path(temporary))
            action(checker, receipt)
            require_fail(invoke(checker, optimized), f"{mode} custody {name}")
            custody_count += 1

    custody_case(
        "receipt_symlink",
        lambda _checker, receipt: (
            receipt.unlink(),
            receipt.symlink_to(RECEIPT),
        ),
    )

    def hardlink_receipt(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        os.link(receipt, receipt.with_suffix(".link"))

    custody_case("receipt_hardlink", hardlink_receipt)

    def fifo_receipt(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        receipt.unlink()
        os.mkfifo(receipt)

    custody_case("receipt_fifo", fifo_receipt)

    def duplicate_key(checker: pathlib.Path, receipt: pathlib.Path) -> None:
        mutated = BASELINE_BYTES.replace(b'{\n  "schema":', b'{\n  "schema": "duplicate",\n  "schema":', 1)
        receipt.write_bytes(mutated)
        patch_receipt_digest(checker, mutated)

    custody_case("duplicate_json_key", duplicate_key)

    def crlf(checker: pathlib.Path, receipt: pathlib.Path) -> None:
        mutated = BASELINE_BYTES.replace(b"\n", b"\r\n")
        receipt.write_bytes(mutated)
        patch_receipt_digest(checker, mutated)

    custody_case("receipt_crlf", crlf)

    def repository_input_drift(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        target = receipt.parents[2] / "MATHEMATICAL_RESULTS_GUIDE.md"
        target.write_bytes(target.read_bytes() + b"\n")

    custody_case("repository_input_drift", repository_input_drift)

    def retained_artifact_drift(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        target = receipt.parents[2] / RETAINED_RELATIVE
        target.write_bytes(target.read_bytes() + b"\n")

    custody_case("retained_artifact_drift", retained_artifact_drift)

    def retained_artifact_symlink(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        target = receipt.parents[2] / RETAINED_RELATIVE
        target.unlink()
        target.symlink_to(ROOT / RETAINED_RELATIVE)

    custody_case("retained_artifact_symlink", retained_artifact_symlink)

    def retained_artifact_hardlink(_checker: pathlib.Path, receipt: pathlib.Path) -> None:
        target = receipt.parents[2] / RETAINED_RELATIVE
        os.link(target, target.with_suffix(".hardlink.pdf"))

    custody_case("retained_artifact_hardlink", retained_artifact_hardlink)

    def corrected_comparator_drift(
        _checker: pathlib.Path, receipt: pathlib.Path
    ) -> None:
        target = (
            receipt.parents[2]
            / "scripts/check-mathematical-results-guide-pdf-font-alpha-equivalence.py"
        )
        target.write_bytes(target.read_bytes() + b"\n")

    custody_case("corrected_comparator_drift", corrected_comparator_drift)

    def corrected_wrapper_drift(
        _checker: pathlib.Path, receipt: pathlib.Path
    ) -> None:
        target = receipt.parents[2] / "scripts/check-mathematical-results-guide-pdf.sh"
        target.write_bytes(target.read_bytes() + b"\n")

    custody_case("corrected_wrapper_drift", corrected_wrapper_drift)

    with tempfile.TemporaryDirectory(
        prefix=f"pid-rs-pandoc-portability-{mode}-usage-",
        dir=PHYSICAL_TEMP_ROOT,
    ) as temporary:
        checker, _receipt = copy_fixture(pathlib.Path(temporary))
        require_fail(invoke(checker, optimized, "extra"), f"{mode} usage")
        require("usage" not in custody_names, f"{mode} duplicate custody-case name: usage")
        custody_names.add("usage")
        custody_count += 1

    require(
        (controls, semantic_count, custody_count) == EXPECTED_COUNTS
        and len(custody_names) == custody_count,
        f"{mode} self-test inventory changed: "
        f"{(controls, semantic_count, custody_count)!r}",
    )
    return controls, semantic_count, custody_count


def main() -> None:
    require(len(sys.argv) == 1, f"usage: {sys.argv[0]}")
    totals = [run_mode(False), run_mode(True)]
    require(totals[0] == totals[1], "normal and optimized case counts differ")
    require(totals[0] == EXPECTED_COUNTS, "self-test case cardinality changed")
    controls, semantic_count, custody_count = totals[0]
    print(
        "OK: Pandoc portability receipt self-test "
        f"(controls={controls}; semantic_mutations={semantic_count}; "
        f"custody_mutations={custody_count}; modes=2)"
    )


if __name__ == "__main__":
    main()
