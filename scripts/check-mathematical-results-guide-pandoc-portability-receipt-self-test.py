#!/usr/bin/env python3
"""Mutation suite for the closed Pandoc 3.1.3 portability receipt checker."""

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
EXPECTED_SUCCESS = (
    "OK: closed Pandoc 3.1.3 guide-portability operator-observation receipt "
    "(translated_x86_64=yes; native_x86_64=no; normalization_deltas=25; "
    "final_destinations=39; navigation=167; raw_artifacts=not_tracked)\n"
)
FAILURE_PREFIX = "Pandoc portability receipt check failed:"
HASH_LINE = re.compile(r'^RECEIPT_SHA256 = "[0-9a-f]{64}"$', re.MULTILINE)
EXPECTED_COUNTS = (2, 28, 7)


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
