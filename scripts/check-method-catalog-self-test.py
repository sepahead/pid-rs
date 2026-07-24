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
MARKDOWN = ROOT / "METHODS.md"
MUTATION_COUNT = 0


def canonical_write(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def run_checker(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def load_checker_module():
    spec = importlib.util.spec_from_file_location("pid_rs_method_catalog_checker", CHECKER)
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
        raise RuntimeError(f"baseline checker failed:\n{baseline.stderr}{baseline.stdout}")
    base = json.loads(CATALOG.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="pid-rs-method-catalog-") as raw:
        directory = Path(raw)

        expect_failure(
            directory,
            "duplicate-id",
            base,
            lambda value: value["methods"].insert(1, copy.deepcopy(value["methods"][0])),
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
                {
                    "rust_entry_points": [
                        "pid_core::stable::categorical::imin_pid2"
                    ]
                }
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
        stale.write_text(MARKDOWN.read_text(encoding="utf-8") + "stale\n", encoding="utf-8")
        process = run_checker("--markdown", str(stale))
        expect_process_failure("stale-generated-markdown", process, "is stale")

        fixture_path = (
            ROOT
            / "crates/pid-runlog/tests/fixtures/"
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
                    {
                        "catalog_id": "unsupported.mixed-support-continuous-pid"
                    }
                ),
                value["fixtures"][1].update(
                    {"catalog_id": "pid.continuous-pid2"}
                ),
            ),
            "disagrees with expected",
        )
        write_fixture_mutation(
            "origin-mismatch",
            lambda value: value["fixtures"][0].update(
                {"origin": "paper_derived"}
            ),
            "disagrees with catalog origin",
        )
        write_fixture_mutation(
            "maturity-mismatch",
            lambda value: value["fixtures"][0].update(
                {"api_maturity": "stable"}
            ),
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

        checker = load_checker_module()
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

    print(f"OK: {MUTATION_COUNT} method-catalog mutations were rejected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
