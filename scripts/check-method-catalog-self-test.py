#!/usr/bin/env python3
"""Mutation tests for check-method-catalog.py."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable

if sys.version_info < (3, 11):
    raise SystemExit("check-method-catalog-self-test.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-method-catalog.py"
CATALOG = ROOT / "method-catalog.json"
SEMANTIC_AUTHORITY = ROOT / "audit/evidence/method-catalog-semantic-authority-v1.json"
SEMANTIC_AUTHORITY_SCHEMA = (
    ROOT / "audit/schemas/method-catalog-semantic-authority-v1.schema.json"
)
MARKDOWN = ROOT / "METHODS.md"
EXPECTED_MUTATION_COUNT = 82
MUTATION_COUNT = 0


def canonical_write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def run_checker(*arguments: str) -> subprocess.CompletedProcess[str]:
    optimization_flags = [] if __debug__ else ["-O"]
    return subprocess.run(
        [sys.executable, *optimization_flags, str(CHECKER), *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def load_checker_module():
    spec = importlib.util.spec_from_file_location(
        "pid_rs_method_catalog_checker", CHECKER
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load method-catalog checker module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_process_failure(
    name: str,
    process: subprocess.CompletedProcess[str],
    expected: str,
) -> None:
    global MUTATION_COUNT
    combined = process.stdout + process.stderr
    if process.returncode == 0 or expected not in combined:
        raise RuntimeError(
            f"{name}: expected failure containing {expected!r}, got "
            f"status {process.returncode}:\n{combined}"
        )
    MUTATION_COUNT += 1


def expect_failure(
    directory: Path,
    name: str,
    base: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    candidate = copy.deepcopy(base)
    mutate(candidate)
    path = directory / f"{name}.json"
    canonical_write(path, candidate)
    process = run_checker("--catalog", str(path))
    expect_process_failure(name, process, expected)


def method(catalog: dict[str, Any], method_id: str) -> dict[str, Any]:
    return next(item for item in catalog["methods"] if item["id"] == method_id)


def authority_record(authority: dict[str, Any], method_id: str) -> dict[str, Any]:
    return next(
        item for item in authority["method_payloads"] if item["method_id"] == method_id
    )


def expect_direct_alias_failure(
    name: str,
    checker: Any,
    base: dict[str, Any],
    authority: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
) -> None:
    global MUTATION_COUNT
    candidate = copy.deepcopy(base)
    mutate(candidate)
    item = method(candidate, "diagnostics.distance-matrix")
    record = authority_record(authority, item["id"])
    try:
        checker.check_semantic_alias_diagnostic(item, record)
    except checker.CatalogError as error:
        if "semantic alias diagnostic revision" not in str(error):
            raise RuntimeError(f"{name}: wrong alias failure: {error}") from error
        MUTATION_COUNT += 1
    else:
        raise RuntimeError(f"{name}: alias/confusable transfer was not rejected")


def expect_direct_same_sample_failure(
    name: str,
    checker: Any,
    base: dict[str, Any],
    authority: dict[str, Any],
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    global MUTATION_COUNT
    candidate = copy.deepcopy(base)
    mutate(candidate)
    methods = {item["id"]: item for item in candidate["methods"]}
    try:
        checker.check_required_same_sample_separation(
            methods, authority["method_payloads"]
        )
    except checker.CatalogError as error:
        if expected not in str(error):
            raise RuntimeError(f"{name}: wrong separation failure: {error}") from error
        MUTATION_COUNT += 1
    else:
        raise RuntimeError(f"{name}: same-sample conflation was not rejected")


def expect_direct_same_sample_authority_failure(
    name: str,
    checker: Any,
    base: dict[str, Any],
    authority: dict[str, Any],
    method_id: str,
    mutate: Callable[[dict[str, Any]], None],
    expected: str,
) -> None:
    global MUTATION_COUNT
    candidate_authority = copy.deepcopy(authority)
    mutate(authority_record(candidate_authority, method_id))
    methods = {item["id"]: item for item in base["methods"]}
    try:
        checker.check_required_same_sample_separation(
            methods, candidate_authority["method_payloads"]
        )
    except checker.CatalogError as error:
        if expected not in str(error):
            raise RuntimeError(f"{name}: wrong separation failure: {error}") from error
        MUTATION_COUNT += 1
    else:
        raise RuntimeError(f"{name}: same-sample authority conflation was not rejected")


def rebind_editable_semantic_authority(
    checker: Any,
    catalog: dict[str, Any],
    catalog_path: Path,
    authority: dict[str, Any],
) -> None:
    methods = {item["id"]: item for item in catalog["methods"]}
    references = {item["id"]: item for item in catalog["references"]}
    authority["catalog_sha256"] = checker.raw_sha256(catalog_path)
    authority["reference_registry_sha256"] = checker.canonical_json_sha256(
        catalog["references"]
    )
    for record in authority["method_payloads"]:
        item = methods[record["method_id"]]
        record["payload_sha256"] = checker.canonical_json_sha256(
            checker.semantic_method_payload(item, record, references)
        )
    authority["ordered_root_sha256"] = checker.semantic_authority_root_sha256(authority)


def remove_primary_paper(catalog: dict[str, Any]) -> None:
    item = method(catalog, "pid.imin")
    item["reference_links"] = [
        link
        for link in item["reference_links"]
        if link["role"] not in {"defining-paper", "estimator-paper"}
    ]


def convert_to_unexpected_unsupported(catalog: dict[str, Any]) -> None:
    item = method(catalog, "validation.sxpid-reference-code")
    item.update(
        {
            "category": "unsupported",
            "code_availability": "none",
            "external_code": None,
            "implementation_origin": "not-implemented",
            "implementation_status": "unsupported",
            "cargo_features": [],
            "release_scope_families": [],
            "source_files": [],
            "rust_entry_points": [],
            "python_entry_points": [],
            "depends_on": [],
            "validation": {
                "evidence_paths": [],
                "level": "not-validated",
                "limitations": "Unsupported by design.",
                "scope": "Negative capability declaration.",
            },
        }
    )


def main() -> int:
    global MUTATION_COUNT
    baseline = run_checker()
    if baseline.returncode != 0:
        raise RuntimeError(
            f"baseline checker failed:\n{baseline.stderr}{baseline.stdout}"
        )
    base = json.loads(CATALOG.read_text(encoding="utf-8"))
    semantic_authority = json.loads(SEMANTIC_AUTHORITY.read_text(encoding="utf-8"))
    checker = load_checker_module()
    with tempfile.TemporaryDirectory(prefix="pid-rs-method-catalog-") as raw:
        directory = Path(raw)

        expect_failure(
            directory,
            "duplicate-id",
            base,
            lambda value: value["methods"].insert(
                1, copy.deepcopy(value["methods"][0])
            ),
            "array items are not unique",
        )
        expect_failure(
            directory,
            "unknown-dependency",
            base,
            lambda value: method(value, "co-information.continuous-raw")[
                "depends_on"
            ].append("missing.method"),
            "unknown depends_on ID",
        )
        expect_failure(
            directory,
            "dependency-semantics-drift",
            base,
            lambda value: value.update(
                {"dependency_semantics": "An exhaustive source-level call graph."}
            ),
            "schema validation failed",
        )
        expect_failure(
            directory,
            "dependency-cycle",
            base,
            lambda value: method(value, "mutual-information.ksg1-raw")[
                "depends_on"
            ].append("co-information.continuous-raw"),
            "depends_on cycle",
        )
        expect_failure(
            directory,
            "unsupported-entrypoint",
            base,
            lambda value: method(value, "unsupported.generic-knn-bootstrap-ci")[
                "rust_entry_points"
            ].append("not_real"),
            "unsupported entry claims code, dependencies, or validation",
        )
        expect_failure(
            directory,
            "external-floating-ref",
            base,
            lambda value: method(value, "validation.csxpid-reference-code")[
                "external_code"
            ].update({"pinned_ref": "main"}),
            "schema validation failed",
        )
        expect_failure(
            directory,
            "overclaim",
            base,
            lambda value: method(value, "pid.imin").update(
                {"new_in_pid_rs": "Provides a breakthrough estimator."}
            ),
            "prohibited overclaim wording",
        )
        expect_failure(
            directory,
            "reference-locator-overclaim",
            base,
            lambda value: method(value, "pid.imin")["reference_links"][0].update(
                {"locator": "A breakthrough definition."}
            ),
            "reference_links[0].locator: prohibited overclaim wording",
        )
        semantic_freeze_error = "semantic authority catalog SHA-256 mismatch"
        expect_failure(
            directory,
            "pid2-universal-atomic-calibration",
            base,
            lambda value: method(value, "pid.continuous-pid2").update(
                {
                    "summary": "This estimator is calibrated for every atomic population law."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid2-universal-singular-calibration",
            base,
            lambda value: method(value, "pid.continuous-pid2").update(
                {
                    "summary": "This estimator is calibrated for every singular joint law."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid2-universal-rounded-calibration",
            base,
            lambda value: method(value, "pid.continuous-pid2").update(
                {
                    "summary": "Rounded measurements preserve calibration without additional assumptions."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid2-universal-dependent-calibration",
            base,
            lambda value: method(value, "pid.continuous-pid2").update(
                {
                    "summary": "Arbitrarily dependent rows retain calibrated finite-sample inference."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid3-mixed-support-calibration",
            base,
            lambda value: method(value, "pid.mixed-dimension-pid3").update(
                {
                    "summary": "Mixed discrete-continuous population support is calibrated by this estimator."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid3-singular-support-calibration",
            base,
            lambda value: method(value, "pid.mixed-dimension-pid3").update(
                {
                    "summary": "Singular population support is calibrated by this estimator."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "heuristic-universal-consistency",
            base,
            lambda value: method(
                value, "shared-exclusions.continuous-heuristics"
            ).update(
                {
                    "summary": "These formulas consistently estimate continuous shared exclusions for every population law."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "imin-population-promotion",
            base,
            lambda value: method(value, "pid.imin").update(
                {
                    "summary": "The empirical plug-in output equals the population I_min for every sample."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "imin-universal-finite-sample-promotion",
            base,
            lambda value: method(value, "pid.imin").update(
                {
                    "summary": "Every finite sample is an exact calibrated population decomposition."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "pid2-paper-origin-demotion",
            base,
            lambda value: method(value, "pid.continuous-pid2").update(
                {"definition_origin": "paper-derived"}
            ),
            "disagrees with catalog origin",
        )
        expect_failure(
            directory,
            "unsupported-origin-demotion",
            base,
            lambda value: method(
                value, "unsupported.mixed-support-continuous-pid"
            ).update({"definition_origin": "paper-derived"}),
            "disagrees with catalog origin",
        )
        expect_failure(
            directory,
            "imin-origin-demotion",
            base,
            lambda value: method(value, "pid.imin").update(
                {"definition_origin": "paper-derived"}
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "imin-binding-software-reclassification",
            base,
            lambda value: method(value, "pid.imin").update(
                {"category": "software", "implementation_origin": "binding"}
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "distance-matrix-scientific-originality",
            base,
            lambda value: method(value, "diagnostics.distance-matrix").update(
                {
                    "new_in_pid_rs": "Establishes an original scientific theory of pairwise distance matrices."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "vocabulary-free-semantic-promotion",
            base,
            lambda value: method(value, "diagnostics.distance-matrix").update(
                {
                    "summary": "Every input receives a definitive result with no model qualification."
                }
            ),
            semantic_freeze_error,
        )
        expect_failure(
            directory,
            "benign-semantic-prose-drift",
            base,
            lambda value: method(value, "diagnostics.distance-matrix").update(
                {
                    "summary": method(value, "diagnostics.distance-matrix")["summary"]
                    + " Editorial clarification only."
                }
            ),
            semantic_freeze_error,
        )
        for alias_name, alias_text in (
            ("alias-mgw-initialism", "M.G.W."),
            (
                "alias-mgw-unicode-dashes",
                "Makkeh–Gutknecht–Wibral",
            ),
            ("alias-williams-ampersand-beer", "Williams & Beer"),
            (
                "alias-cyrillic-confusable",
                "Mаkkeh–Gutknecht–Wibral",
            ),
        ):
            expect_direct_alias_failure(
                alias_name,
                checker,
                base,
                semantic_authority,
                lambda value, text=alias_text: method(
                    value, "diagnostics.distance-matrix"
                ).update(
                    {
                        "summary": "Pairwise distance infrastructure relabelled as "
                        + text
                        + "."
                    }
                ),
            )
        expect_failure(
            directory,
            "paper-defined-without-primary-paper",
            base,
            remove_primary_paper,
            "paper-defined method lacks a primary paper link",
        )
        expect_failure(
            directory,
            "unknown-cargo-feature",
            base,
            lambda value: method(value, "pid.imin").update(
                {"cargo_features": ["catalog-test-missing-feature"]}
            ),
            "unknown pid-core Cargo features",
        )
        expect_failure(
            directory,
            "cargo-feature-family-mismatch",
            base,
            lambda value: method(value, "pid.imin").update(
                {"cargo_features": ["parallel"]}
            ),
            "Cargo features",
        )
        expect_failure(
            directory,
            "family-status-mismatch",
            base,
            lambda value: method(value, "pid.imin").update(
                {"implementation_status": "experimental"}
            ),
            "status 'experimental' disagrees",
        )
        expect_failure(
            directory,
            "wrong-marker-file",
            base,
            lambda value: method(value, "pid.imin").update(
                {"source_marker_files": ["crates/pid-core/src/ksg.rs"]}
            ),
            "not declared marker files",
        )
        expect_failure(
            directory,
            "missing-family-mapping",
            base,
            lambda value: method(value, "testing.row-permutation").update(
                {"cargo_features": [], "release_scope_families": []}
            ),
            "local method lacks a release-scope family mapping",
        )
        expect_failure(
            directory,
            "entrypoint-family-mismatch",
            base,
            lambda value: method(value, "pid.imin").update(
                {"rust_entry_points": ["pid_core::stable::imin::not_a_public_symbol"]}
            ),
            "is absent from the mapped release-scope families",
        )
        expect_failure(
            directory,
            "wrong-rust-namespace",
            base,
            lambda value: method(value, "pid.imin").update(
                {"rust_entry_points": ["pid_core::stable::categorical::imin_pid2"]}
            ),
            "has the wrong public namespace",
        )
        expect_failure(
            directory,
            "unsafe-evidence-path",
            base,
            lambda value: method(value, "pid.imin")["validation"].update(
                {"evidence_paths": ["../outside.rs"]}
            ),
            "unsafe repository path",
        )
        expect_failure(
            directory,
            "missing-python-family-exposure",
            base,
            lambda value: method(value, "mutual-information.ksg1-report").update(
                {
                    "python_entry_points": [
                        "pid_core_rs.experimental.migration.compute_mi_report"
                    ]
                }
            ),
            "Python exposure is not cataloged",
        )
        expect_failure(
            directory,
            "incomplete-migration-inventory",
            base,
            lambda value: method(
                value, "software.python-experimental-migration-bindings"
            )["python_entry_points"].pop(),
            "inventory does not match registered migration surface",
        )
        expect_failure(
            directory,
            "unexpected-unsupported-row",
            base,
            convert_to_unexpected_unsupported,
            "unexpected unsupported catalog entry",
        )
        expect_failure(
            directory,
            "stable-dependency",
            base,
            lambda value: method(value, "pid.imin")["depends_on"].append(
                "pid.continuous-pid2"
            ),
            "stable method depends on non-stable",
        )
        expect_direct_same_sample_failure(
            "same-sample-envelope-acquires-transform-dependency",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "pipelines.same-sample-quantization"
            )["depends_on"].append("quantization.same-sample-exact-significand"),
            "same-sample semantic separation drifted for depends_on",
        )
        expect_direct_same_sample_failure(
            "same-sample-imin-reverts-to-fitted-edge-dependency",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "pid.same-sample-quantized-imin"
            ).update(
                {
                    "depends_on": [
                        "pid.imin",
                        "pipelines.same-sample-quantization",
                        "quantization.equal-width",
                    ]
                }
            ),
            "same-sample semantic separation drifted for depends_on",
        )
        expect_direct_same_sample_failure(
            "same-sample-sxpid-reverts-to-fitted-edge-dependency",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "shared-exclusions.same-sample-quantized"
            ).update(
                {
                    "depends_on": [
                        "pipelines.same-sample-quantization",
                        "quantization.equal-width",
                        "shared-exclusions.categorical",
                        "software.sxpid-interpretation-contract",
                    ]
                }
            ),
            "same-sample semantic separation drifted for depends_on",
        )
        expect_direct_same_sample_failure(
            "same-sample-transform-drops-sxpid-release-edge",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "quantization.same-sample-exact-significand"
            ).update(
                {
                    "release_scope_families": [
                        "pid-core.experimental.pipelines.same-sample-quantized-imin"
                    ]
                }
            ),
            "same-sample semantic separation drifted for release_scope_families",
        )
        expect_direct_same_sample_failure(
            "same-sample-envelope-category-transfer",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "pipelines.same-sample-quantization"
            ).update({"category": "pipeline"}),
            "same-sample semantic separation drifted for category",
        )
        expect_direct_same_sample_failure(
            "same-sample-imin-python-entrypoint-transfer",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "pid.same-sample-quantized-imin"
            )["python_entry_points"].append(
                "pid_core_rs.experimental.migration.compute_mi_report"
            ),
            "same-sample semantic separation drifted for python_entry_points",
        )
        expect_direct_same_sample_failure(
            "same-sample-sxpid-rust-entrypoint-transfer",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "shared-exclusions.same-sample-quantized"
            )["rust_entry_points"].append(
                "pid_core::experimental::continuous::pid2_isx"
            ),
            "same-sample semantic separation drifted for rust_entry_points",
        )
        expect_direct_same_sample_failure(
            "same-sample-imin-acquires-ksg-dependency",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "pid.same-sample-quantized-imin"
            )["depends_on"].append("mutual-information.ksg1-report"),
            "same-sample semantic separation drifted for depends_on",
        )
        expect_direct_same_sample_failure(
            "same-sample-sxpid-acquires-ehrlich-dependency",
            checker,
            base,
            semantic_authority,
            lambda value: method(
                value, "shared-exclusions.same-sample-quantized"
            )["depends_on"].append("shared-exclusions.continuous-raw"),
            "same-sample semantic separation drifted for depends_on",
        )
        expect_direct_same_sample_authority_failure(
            "same-sample-imin-fact-transfers-to-mgw",
            checker,
            base,
            semantic_authority,
            "pid.same-sample-quantized-imin",
            lambda record: record["facts"].update(
                {
                    "estimand_family": (
                        "same-sample-quantized-mgw-shared-exclusions"
                    )
                }
            ),
            "same-sample semantic separation drifted for facts",
        )
        expect_failure(
            directory,
            "implicit-stricter-dependency",
            base,
            lambda value: method(value, "pipelines.pid3-permutation").update(
                {
                    "constraints": [
                        "The dependency is research-only; calibration depends on the declared permutation null."
                    ]
                }
            ),
            "stricter-status dependency boundary",
        )
        expect_failure(
            directory,
            "migration-entrypoint-misattribution",
            base,
            lambda value: method(value, "pid.imin")["python_entry_points"].append(
                "pid_core_rs.experimental.migration.compute_mi"
            ),
            "migration owner claims disagree",
        )
        expect_failure(
            directory,
            "missing-migration-owner-claim",
            base,
            lambda value: method(value, "preprocessing.hash-projection").update(
                {"python_entry_points": []}
            ),
            "migration owner claims disagree",
        )
        expect_failure(
            directory,
            "unmapped-entrypoint-drift",
            base,
            lambda value: method(value, "software.runlog-schema-replay").update(
                {"rust_entry_points": ["pid_runlog::validate_eventz"]}
            ),
            "unmapped entry-point policy disagrees",
        )

        noncanonical = directory / "noncanonical.json"
        noncanonical.write_text(json.dumps(base), encoding="utf-8")
        process = run_checker("--catalog", str(noncanonical))
        expect_process_failure("noncanonical-json", process, "not canonical")

        stale = directory / "METHODS.md"
        stale.write_text(
            MARKDOWN.read_text(encoding="utf-8") + "stale\n", encoding="utf-8"
        )
        process = run_checker("--markdown", str(stale))
        expect_process_failure("stale-generated-markdown", process, "is stale")

        def write_authority_mutation(
            name: str,
            mutate: Callable[[dict[str, Any]], None],
            expected: str,
        ) -> None:
            candidate = copy.deepcopy(semantic_authority)
            mutate(candidate)
            path = directory / f"semantic-authority-{name}.json"
            canonical_write(path, candidate)
            process = run_checker("--semantic-authority", str(path))
            expect_process_failure(f"semantic-authority-{name}", process, expected)

        write_authority_mutation(
            "missing-method-payload",
            lambda value: value["method_payloads"].pop(),
            "complete catalog-ordered inventory",
        )
        write_authority_mutation(
            "typed-support-drift",
            lambda value: authority_record(value, "pid.imin")["facts"].update(
                {"population_support": "regular-full-dimensional-continuous-required"}
            ),
            "reviewed semantic payload SHA-256 mismatch",
        )
        write_authority_mutation(
            "row-digest-drift",
            lambda value: authority_record(value, "pid.imin").update(
                {"payload_sha256": "0" * 64}
            ),
            "reviewed semantic payload SHA-256 mismatch",
        )
        write_authority_mutation(
            "method-order-drift",
            lambda value: value["method_payloads"].__setitem__(
                slice(0, 2), list(reversed(value["method_payloads"][:2]))
            ),
            "complete catalog-ordered inventory",
        )
        write_authority_mutation(
            "alias-normalization-drift",
            lambda value: value["alias_diagnostic"].update(
                {"normalization": "unicode-casefold-only"}
            ),
            "alias/confusable diagnostic registry drifted",
        )
        write_authority_mutation(
            "alias-version-drift",
            lambda value: value["alias_diagnostic"].update({"revision": 2}),
            "schema validation failed",
        )
        write_authority_mutation(
            "ordered-root-drift",
            lambda value: value.update({"ordered_root_sha256": "f" * 64}),
            "ordered-root SHA-256 mismatch",
        )

        authority_schema = json.loads(
            SEMANTIC_AUTHORITY_SCHEMA.read_text(encoding="utf-8")
        )
        authority_schema["title"] += " editorial drift"
        authority_schema_path = directory / "semantic-authority-schema-drift.json"
        canonical_write(authority_schema_path, authority_schema)
        process = run_checker("--semantic-authority-schema", str(authority_schema_path))
        expect_process_failure(
            "semantic-authority-schema-benign-drift",
            process,
            "semantic authority schema SHA-256 mismatch",
        )

        coordinated_catalog = copy.deepcopy(base)
        method(coordinated_catalog, "pid.continuous-pid2").update(
            {
                "summary": "All atomic, singular, rounded, and arbitrarily dependent laws are calibrated."
            }
        )
        coordinated_catalog_path = directory / "coordinated-semantic-catalog.json"
        canonical_write(coordinated_catalog_path, coordinated_catalog)
        coordinated_authority = copy.deepcopy(semantic_authority)
        rebind_editable_semantic_authority(
            checker,
            coordinated_catalog,
            coordinated_catalog_path,
            coordinated_authority,
        )
        coordinated_authority_path = directory / "coordinated-semantic-authority.json"
        canonical_write(coordinated_authority_path, coordinated_authority)
        process = run_checker(
            "--catalog",
            str(coordinated_catalog_path),
            "--semantic-authority",
            str(coordinated_authority_path),
        )
        expect_process_failure(
            "coordinated-prose-and-digest-rebase",
            process,
            "requires explicit checker-root re-adjudication",
        )

        family_transfer_authority = copy.deepcopy(semantic_authority)
        imin_facts = authority_record(family_transfer_authority, "pid.imin")["facts"]
        mgw_facts = authority_record(
            family_transfer_authority, "shared-exclusions.categorical"
        )["facts"]
        imin_facts["estimand_family"], mgw_facts["estimand_family"] = (
            mgw_facts["estimand_family"],
            imin_facts["estimand_family"],
        )
        rebind_editable_semantic_authority(
            checker,
            base,
            CATALOG,
            family_transfer_authority,
        )
        family_transfer_path = directory / "semantic-family-transfer.json"
        canonical_write(family_transfer_path, family_transfer_authority)
        process = run_checker("--semantic-authority", str(family_transfer_path))
        expect_process_failure(
            "semantic-family-transfer-with-rebound-digests",
            process,
            "requires explicit checker-root re-adjudication",
        )

        row_permutation_domain_revert_authority = copy.deepcopy(semantic_authority)
        authority_record(
            row_permutation_domain_revert_authority, "testing.row-permutation"
        )["facts"]["data_domain"] = "method-results"
        rebind_editable_semantic_authority(
            checker,
            base,
            CATALOG,
            row_permutation_domain_revert_authority,
        )
        row_permutation_domain_revert_path = (
            directory / "semantic-row-permutation-domain-revert.json"
        )
        canonical_write(
            row_permutation_domain_revert_path,
            row_permutation_domain_revert_authority,
        )
        process = run_checker(
            "--semantic-authority", str(row_permutation_domain_revert_path)
        )
        expect_process_failure(
            "row-permutation-domain-revert-with-rebound-digests",
            process,
            "requires explicit checker-root re-adjudication",
        )

        fixture_path = (
            ROOT / "crates/pid-runlog/tests/fixtures/"
            "scientific_method_catalog_fixtures.json"
        )
        fixture_manifest = json.loads(fixture_path.read_text(encoding="utf-8"))

        def write_fixture_mutation(
            name: str,
            mutate: Callable[[dict[str, Any]], None],
            expected: str,
        ) -> None:
            candidate = copy.deepcopy(fixture_manifest)
            mutate(candidate)
            path = directory / f"scientific-contract-{name}.json"
            canonical_write(path, candidate)
            process = run_checker("--scientific-contract-fixtures", str(path))
            expect_process_failure(f"scientific-contract-{name}", process, expected)

        write_fixture_mutation(
            "unknown-method",
            lambda value: value["fixtures"][0].update(
                {"catalog_id": "pid.missing-method"}
            ),
            "disagrees with expected",
        )
        write_fixture_mutation(
            "same-origin-id-swap",
            lambda value: (
                value["fixtures"][0].update(
                    {"catalog_id": "unsupported.mixed-support-continuous-pid"}
                ),
                value["fixtures"][1].update({"catalog_id": "pid.continuous-pid2"}),
            ),
            "disagrees with expected",
        )
        write_fixture_mutation(
            "origin-mismatch",
            lambda value: value["fixtures"][0].update({"origin": "paper_derived"}),
            "disagrees with catalog origin",
        )
        write_fixture_mutation(
            "maturity-mismatch",
            lambda value: value["fixtures"][0].update({"api_maturity": "stable"}),
            "disagrees with catalog status",
        )
        write_fixture_mutation(
            "availability-mismatch",
            lambda value: value["fixtures"][0].update(
                {"availability": "no_implementation"}
            ),
            "disagrees with catalog code availability",
        )
        write_fixture_mutation(
            "completeness-mismatch",
            lambda value: value["fixtures"][0].update(
                {"completeness": "incomplete_diagnostic"}
            ),
            "disagrees with expected",
        )
        write_fixture_mutation(
            "estimand-regime-mismatch",
            lambda value: value["fixtures"][0].update(
                {"estimand_regime": "empirical_pmf"}
            ),
            "disagrees with expected",
        )
        write_fixture_mutation(
            "duplicate-id",
            lambda value: value["fixtures"][1].update(
                {"fixture_id": value["fixtures"][0]["fixture_id"]}
            ),
            "duplicate scientific-contract fixture IDs",
        )
        write_fixture_mutation(
            "unknown-field",
            lambda value: value["fixtures"][0].update({"extra": "not allowed"}),
            "must have exactly",
        )
        write_fixture_mutation(
            "boolean-schema-revision",
            lambda value: value.update({"schema_revision": True}),
            "unsupported scientific-contract fixture schema identity",
        )

        noncanonical_fixture = directory / "scientific-contract-noncanonical.json"
        noncanonical_fixture.write_text(
            json.dumps(fixture_manifest),
            encoding="utf-8",
        )
        process = run_checker(
            "--scientific-contract-fixtures", str(noncanonical_fixture)
        )
        expect_process_failure(
            "scientific-contract-noncanonical",
            process,
            "not canonical",
        )

        duplicate_key_fixture = directory / "scientific-contract-duplicate-key.json"
        duplicate_key_fixture.write_text(
            fixture_path.read_text(encoding="utf-8").replace(
                '{\n  "fixtures":',
                '{\n  "schema": "pid-rs/scientific-method-test-fixtures",\n'
                '  "fixtures":',
                1,
            ),
            encoding="utf-8",
        )
        process = run_checker(
            "--scientific-contract-fixtures", str(duplicate_key_fixture)
        )
        expect_process_failure(
            "scientific-contract-duplicate-key",
            process,
            "duplicate JSON object key",
        )

        methods = {item["id"]: item for item in base["methods"]}
        migration_surface = checker.registered_migration_surface(ROOT)
        try:
            checker.check_migration_ownership(
                methods,
                migration_surface
                | {f"{checker.MIGRATION_PREFIX}future_unclassified_callable"},
            )
        except checker.CatalogError as error:
            if "lack owner or policy classification" not in str(error):
                raise RuntimeError(
                    "unclassified-migration-entry: wrong failure: " + str(error)
                ) from error
            MUTATION_COUNT += 1
        else:
            raise RuntimeError("unclassified migration entry was not rejected")

        missing_registered = next(iter(checker.MIGRATION_ENTRYPOINT_OWNERS))
        try:
            checker.check_migration_ownership(
                methods,
                migration_surface - {missing_registered},
            )
        except checker.CatalogError as error:
            if "classifications name unregistered entries" not in str(error):
                raise RuntimeError(
                    "stale-migration-classification: wrong failure: " + str(error)
                ) from error
            MUTATION_COUNT += 1
        else:
            raise RuntimeError("stale migration classification was not rejected")

    if MUTATION_COUNT != EXPECTED_MUTATION_COUNT:
        raise RuntimeError(
            "method-catalog mutation count drifted: "
            f"expected {EXPECTED_MUTATION_COUNT}, observed {MUTATION_COUNT}"
        )
    print(f"OK: {MUTATION_COUNT} method-catalog mutations were rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
