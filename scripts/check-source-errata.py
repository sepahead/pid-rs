#!/usr/bin/env python3
"""Fail-closed validation for the versioned source-errata registry."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any


if sys.version_info < (3, 11):
    raise SystemExit("check-source-errata.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = ROOT / "audit/source-errata.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/source-errata.schema.json"
SCHEMA_ID = "pid-rs/source-errata"
SCHEMA_REVISION = 1
EXPECTED_REGISTRY_SHA256 = (
    "ce527b2c4e94ca1315ce47643732d10d326696342a360097a246e5c423ed41f4"
)
EXPECTED_SCHEMA_SHA256 = (
    "64aacf4bd804ef436ae6eaefb6e0fef083b2c30fd45d5210083a2065ddebf06b"
)
REQUIRED_CONSTRUCTIONS = {
    "ehrlich-analytical-continuous-shared-exclusions": (
        "source_erratum_candidates",
        "purely_continuous_gauge_dependent",
    ),
    "mgw-categorical-shared-exclusions": (
        "firewall_only_no_errata_records",
        "finite_categorical",
    ),
    "schick-poland-general-measure-shared-exclusions": (
        "open_source_obligations",
        "general_measure_theoretic",
    ),
}
REQUIRED_SOURCES = {
    "ehrlich-arxiv-2311.06373v3": {
        "arxiv_revision": "arXiv:2311.06373v3",
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "sha256": "cf785c96d24a49d793e835d70e26d94ffe67b9c71251265e6e4040753ec8f563",
        "byte_length": 2_168_968,
    },
    "mgw-arxiv-2002.03356v5": {
        "arxiv_revision": "arXiv:2002.03356v5",
        "construction_id": "mgw-categorical-shared-exclusions",
        "sha256": "5939ce0f4c727f1998040421c07a1689af1b8d9a35a0ee3c83fe25cd85263dc6",
        "byte_length": 1_002_114,
    },
    "schick-poland-arxiv-2106.12393v2": {
        "arxiv_revision": "arXiv:2106.12393v2",
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "sha256": "05c84b9778aba21d81f5d0bed26c8052d678efd23625ac69fa16a48116af1728",
        "byte_length": 633_604,
    },
}
REQUIRED_RECORDS = {
    "ehrlich-v3-algorithm-6-wiring": {
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "source_id": "ehrlich-arxiv-2311.06373v3",
        "issue_class": "source_erratum_candidate",
        "pages": [28],
        "named_object": "Appendix H, Algorithm 6 (compute redundancy)",
        "reviewer_status": "reviewer_derived_candidate_correction",
        "resolution_status": "proposed_local_source_correction",
        "implementation_status": "implemented_with_bounded_regression",
        "binding_kind": "behavioral_regression",
        "binding_path": "crates/pid-core/src/isx.rs",
        "binding_test": "ehrlich_inclusive_counts_reach_the_exact_integer_harmonic_local_term",
    },
    "ehrlich-v3-equation-14-units": {
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "source_id": "ehrlich-arxiv-2311.06373v3",
        "issue_class": "source_erratum_candidate",
        "pages": [10],
        "named_object": "Equation (14)",
        "reviewer_status": "reviewer_derived_candidate_correction",
        "resolution_status": "proposed_local_source_correction",
        "implementation_status": "implemented_with_bounded_regression",
        "binding_kind": "behavioral_regression",
        "binding_path": "crates/pid-core/tests/isx.rs",
        "binding_test": "ehrlich_ksg_matches_pinned_csxpid_on_committed_fixture",
    },
    "ehrlich-v3-equation-8-overlap-factor": {
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "source_id": "ehrlich-arxiv-2311.06373v3",
        "issue_class": "source_erratum_candidate",
        "pages": [4],
        "named_object": "Equation (8)",
        "reviewer_status": "reviewer_derived_candidate_correction",
        "resolution_status": "proposed_local_source_correction",
        "implementation_status": "no_direct_implementation_effect",
        "binding_kind": "source_only_guard",
        "binding_path": "crates/pid-core/src/isx.rs",
        "binding_test": "not_applicable_source_only",
    },
    "ehrlich-v3-post-definition-2-differential": {
        "construction_id": "ehrlich-analytical-continuous-shared-exclusions",
        "source_id": "ehrlich-arxiv-2311.06373v3",
        "issue_class": "source_erratum_candidate",
        "pages": [5],
        "named_object": "Global expectation display immediately after Definition 2",
        "reviewer_status": "reviewer_derived_candidate_correction",
        "resolution_status": "proposed_local_source_correction",
        "implementation_status": "no_direct_implementation_effect",
        "binding_kind": "source_only_guard",
        "binding_path": "crates/pid-core/src/isx.rs",
        "binding_test": "not_applicable_source_only",
    },
    "schick-poland-v2-bimeasurable-bicontinuity": {
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "source_id": "schick-poland-arxiv-2106.12393v2",
        "issue_class": "open_source_obligation",
        "pages": [16],
        "named_object": "Section 4.3.3, Proposition 4.2 proof",
        "reviewer_status": "reviewer_derived_open_source_obligation",
        "resolution_status": "clarification_or_additional_theorem_required",
        "implementation_status": "not_implemented_fail_closed",
        "binding_kind": "negative_capability_guard",
        "binding_path": "crates/pid-core/src/pid3.rs",
        "binding_test": "not_applicable_negative_capability",
    },
    "schick-poland-v2-borel-isomorphism-density": {
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "source_id": "schick-poland-arxiv-2106.12393v2",
        "issue_class": "open_source_obligation",
        "pages": [9],
        "named_object": "Theorem 3.4 and Corollary 3.1",
        "reviewer_status": "reviewer_derived_open_source_obligation",
        "resolution_status": "clarification_or_additional_theorem_required",
        "implementation_status": "not_implemented_fail_closed",
        "binding_kind": "negative_capability_guard",
        "binding_path": "crates/pid-core/src/pid3.rs",
        "binding_test": "not_applicable_negative_capability",
    },
    "schick-poland-v2-discrete-recovery-normalization": {
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "source_id": "schick-poland-arxiv-2106.12393v2",
        "issue_class": "open_source_obligation",
        "pages": [13, 14],
        "named_object": "Section 4.3.1, Recovering the discrete definition",
        "reviewer_status": "reviewer_derived_open_source_obligation",
        "resolution_status": "clarification_or_additional_theorem_required",
        "implementation_status": "not_implemented_fail_closed",
        "binding_kind": "negative_capability_guard",
        "binding_path": "crates/pid-core/src/pid3.rs",
        "binding_test": "not_applicable_negative_capability",
    },
    "schick-poland-v2-null-event-rcp-version": {
        "construction_id": "schick-poland-general-measure-shared-exclusions",
        "source_id": "schick-poland-arxiv-2106.12393v2",
        "issue_class": "open_source_obligation",
        "pages": [11, 12, 13],
        "named_object": "Definitions 4.2-4.4 and Equations (18)-(19)",
        "reviewer_status": "reviewer_derived_open_source_obligation",
        "resolution_status": "clarification_or_additional_theorem_required",
        "implementation_status": "not_implemented_fail_closed",
        "binding_kind": "negative_capability_guard",
        "binding_path": "crates/pid-core/src/pid3.rs",
        "binding_test": "not_applicable_negative_capability",
    },
}
REQUIRED_NONIMPLICATION_FRAGMENTS = (
    "not author, publisher, or institutional confirmation",
    "does not establish estimator consistency",
    "No record transfers a theorem",
    "not permanent archive identifiers",
)
OVERBROAD_CANTOR_PHRASES = (
    "cantor law proves no mod-null",
    "cantor distribution proves no mod-null",
    "cantor law rules out every",
    "cantor distribution rules out every",
    "no mod-null measure-space representation exists",
)
FORBIDDEN_CONFIRMATION_STATUSES = {
    "author_confirmed",
    "author_confirmed_erratum",
    "publisher_confirmed",
    "publisher_confirmed_erratum",
}


class ErrataError(RuntimeError):
    """Registry validation failed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root used to resolve test bindings",
    )
    return parser.parse_args()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")


def load_canonical_json(path: Path, label: str) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise ErrataError(f"cannot read {label} {path}: {error}") from error
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ErrataError(f"{label} is not UTF-8: {error}") from error
    try:
        value = json.loads(text, parse_constant=_reject_json_constant)
    except (json.JSONDecodeError, ErrataError) as error:
        raise ErrataError(f"invalid {label} JSON: {error}") from error
    if raw != canonical_bytes(value):
        raise ErrataError(
            f"{label} is not canonical JSON (sorted keys, two-space indent, ASCII escaping, final newline)"
        )
    return value, raw


def _reject_json_constant(value: str) -> None:
    raise ErrataError(f"non-standard JSON constant {value!r} is forbidden")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ErrataError(message)


def expect_object(value: Any, label: str) -> dict[str, Any]:
    require(type(value) is dict, f"{label} must be an object")
    return value


def expect_array(value: Any, label: str) -> list[Any]:
    require(type(value) is list, f"{label} must be an array")
    return value


def expect_string(value: Any, label: str) -> str:
    require(type(value) is str and bool(value), f"{label} must be a non-empty string")
    return value


def expect_int(value: Any, label: str) -> int:
    require(type(value) is int, f"{label} must be an integer")
    return value


def exact_keys(value: dict[str, Any], keys: set[str], label: str) -> None:
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise ErrataError(f"{label} has wrong keys: missing={missing} extra={extra}")


def unique_index(items: list[Any], key: str, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(items):
        item = expect_object(raw, f"{label}[{index}]")
        item_id = expect_string(item.get(key), f"{label}[{index}].{key}")
        require(item_id not in result, f"duplicate {label} {key} {item_id!r}")
        result[item_id] = item
    return result


def check_schema_document(schema: Any) -> None:
    root = expect_object(schema, "schema")
    require(
        root.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "schema must declare JSON Schema draft 2020-12",
    )
    require(
        root.get("$id") == "https://pid.rs/schemas/source-errata.schema.json",
        "schema $id mismatch",
    )
    require(root.get("additionalProperties") is False, "schema root must be closed")
    required = root.get("required")
    require(
        required
        == [
            "construction_firewall",
            "constructions",
            "nonimplications",
            "records",
            "schema",
            "schema_revision",
            "sources",
        ],
        "schema required-field contract mismatch",
    )
    definitions = expect_object(root.get("$defs"), "schema.$defs")
    for name in (
        "construction",
        "implementation_disposition",
        "locator",
        "proposed_resolution",
        "record",
        "retrieval",
        "reviewer_adjudication",
        "source",
        "test_binding",
        "upstream_confirmation",
    ):
        definition = expect_object(definitions.get(name), f"schema.$defs.{name}")
        require(
            definition.get("additionalProperties") is False,
            f"schema definition {name} must be closed",
        )
    confirmation = definitions["upstream_confirmation"]
    status = expect_object(
        expect_object(confirmation.get("properties"), "confirmation.properties").get(
            "status"
        ),
        "confirmation status schema",
    )
    require(
        status.get("const") == "not_author_or_publisher_confirmed",
        "schema must fail closed on upstream confirmation",
    )


def check_registry_shape(registry: Any) -> dict[str, Any]:
    root = expect_object(registry, "registry")
    exact_keys(
        root,
        {
            "construction_firewall",
            "constructions",
            "nonimplications",
            "records",
            "schema",
            "schema_revision",
            "sources",
        },
        "registry",
    )
    require(root["schema"] == SCHEMA_ID, "registry schema identifier mismatch")
    require(
        type(root["schema_revision"]) is int
        and root["schema_revision"] == SCHEMA_REVISION,
        "registry schema revision mismatch",
    )
    return root


def check_constructions(root: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = expect_array(root["constructions"], "constructions")
    constructions = unique_index(items, "id", "constructions")
    require(
        set(constructions) == set(REQUIRED_CONSTRUCTIONS),
        "construction inventory mismatch; construction transfer firewall must remain closed",
    )
    for construction_id, (eligibility, regime) in REQUIRED_CONSTRUCTIONS.items():
        item = constructions[construction_id]
        exact_keys(
            item,
            {
                "id",
                "label",
                "record_eligibility",
                "regime",
                "source_ids",
                "transfer_rule",
            },
            f"construction {construction_id}",
        )
        expect_string(item["label"], f"construction {construction_id}.label")
        require(
            item["record_eligibility"] == eligibility,
            f"construction {construction_id} eligibility mismatch",
        )
        require(
            item["regime"] == regime, f"construction {construction_id} regime mismatch"
        )
        source_ids = expect_array(
            item["source_ids"], f"construction {construction_id}.source_ids"
        )
        require(
            all(type(source_id) is str and source_id for source_id in source_ids),
            f"construction {construction_id} source IDs must be strings",
        )
        require(
            len(source_ids) == len(set(source_ids)),
            f"construction {construction_id} has duplicate source IDs",
        )
        expect_string(
            item["transfer_rule"], f"construction {construction_id}.transfer_rule"
        )
    return constructions


def check_sources(
    root: dict[str, Any], constructions: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    sources = unique_index(
        expect_array(root["sources"], "sources"), "source_id", "sources"
    )
    require(set(sources) == set(REQUIRED_SOURCES), "source inventory mismatch")
    for source_id, expected in REQUIRED_SOURCES.items():
        item = sources[source_id]
        exact_keys(
            item,
            {
                "arxiv_revision",
                "construction_id",
                "publication_locator",
                "retrieval",
                "retrieval_boundary",
                "source_id",
                "title",
            },
            f"source {source_id}",
        )
        require(
            item["arxiv_revision"] == expected["arxiv_revision"],
            f"source {source_id} arXiv revision mismatch",
        )
        require(
            item["construction_id"] == expected["construction_id"],
            f"source {source_id} construction mismatch",
        )
        require(
            item["construction_id"] in constructions,
            f"source {source_id} references unknown construction",
        )
        for field in ("publication_locator", "retrieval_boundary", "title"):
            expect_string(item[field], f"source {source_id}.{field}")
        boundary = item["retrieval_boundary"].lower()
        for fragment in (
            "not a permanent archive identifier",
            "not",
            "signature",
            "attestation",
        ):
            require(
                fragment in boundary,
                f"source {source_id} retrieval boundary omits {fragment!r}",
            )
        retrieval = expect_object(item["retrieval"], f"source {source_id}.retrieval")
        exact_keys(
            retrieval,
            {"byte_length", "retrieved_at_utc", "sha256", "url"},
            f"source {source_id}.retrieval",
        )
        require(
            expect_int(retrieval["byte_length"], f"source {source_id}.byte_length")
            == expected["byte_length"],
            f"source {source_id} byte length mismatch",
        )
        require(
            retrieval["sha256"] == expected["sha256"],
            f"source {source_id} observed retrieval hash mismatch",
        )
        require(
            re.fullmatch(r"[0-9a-f]{64}", retrieval["sha256"]) is not None,
            f"source {source_id} invalid SHA-256",
        )
        require(
            re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                expect_string(
                    retrieval["retrieved_at_utc"],
                    f"source {source_id}.retrieved_at_utc",
                ),
            )
            is not None,
            f"source {source_id} invalid retrieval date",
        )
        require(
            retrieval["url"]
            == f"https://export.arxiv.org/pdf/{expected['arxiv_revision'].removeprefix('arXiv:')}",
            f"source {source_id} retrieval URL is not exact-version HTTPS",
        )
    for construction_id, construction in constructions.items():
        expected_ids = sorted(
            source_id
            for source_id, source in sources.items()
            if source["construction_id"] == construction_id
        )
        require(
            construction["source_ids"] == expected_ids,
            f"construction {construction_id} source IDs must exactly match source registry",
        )
    return sources


def safe_binding_path(root: Path, text: str) -> Path:
    require("\\" not in text, f"test binding path uses backslash: {text!r}")
    relative = PurePosixPath(text)
    require(
        not relative.is_absolute(), f"absolute test binding path is forbidden: {text!r}"
    )
    require(
        relative.parts and all(part not in {"", ".", ".."} for part in relative.parts),
        f"unsafe test binding path: {text!r}",
    )
    require(
        relative.parts[0] in {"crates", "scripts"},
        f"test binding path outside allowed roots: {text!r}",
    )
    root_resolved = root.resolve(strict=True)
    candidate = root_resolved
    for part in relative.parts:
        candidate /= part
        require(
            not candidate.is_symlink(),
            f"test binding route contains a symbolic link: {text!r}",
        )
    path = candidate.resolve(strict=True)
    require(
        path == root_resolved or root_resolved in path.parents,
        f"test binding escapes repository root: {text!r}",
    )
    require(path.is_file(), f"test binding is not a regular file: {text!r}")
    return path


def check_binding(
    root: Path, record_id: str, binding: Any, *, require_test_attribute: bool = False
) -> None:
    item = expect_object(binding, f"record {record_id} test binding")
    exact_keys(
        item,
        {"kind", "marker", "path", "test_name"},
        f"record {record_id} test binding",
    )
    for field in ("kind", "marker", "path", "test_name"):
        expect_string(item[field], f"record {record_id} binding.{field}")
    path = safe_binding_path(root, item["path"])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ErrataError(
            f"cannot read test binding {item['path']}: {error}"
        ) from error
    require(
        item["marker"] in text,
        f"record {record_id} test marker missing from {item['path']}",
    )
    if item["kind"] == "behavioral_regression":
        test_name = re.escape(item["test_name"])
        require(
            re.search(rf"\bfn\s+{test_name}\s*\(", text) is not None,
            f"record {record_id} named test missing from {item['path']}",
        )
        if require_test_attribute:
            require(
                re.search(rf"#\[test\]\s*fn\s+{test_name}\s*\(", text) is not None,
                f"record {record_id} named function is not a Rust #[test]",
            )
    elif item["kind"] == "source_only_guard":
        require(
            item["test_name"] == "not_applicable_source_only",
            f"record {record_id} source-only binding has executable-test claim",
        )
    elif item["kind"] == "negative_capability_guard":
        require(
            item["test_name"] == "not_applicable_negative_capability",
            f"record {record_id} negative-capability binding has executable-test claim",
        )
    else:
        raise ErrataError(
            f"record {record_id} has unknown binding kind {item['kind']!r}"
        )


def check_records(
    root: dict[str, Any],
    constructions: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    repository_root: Path,
) -> None:
    records = unique_index(expect_array(root["records"], "records"), "id", "records")
    require(
        set(records) == set(REQUIRED_RECORDS),
        "required source errata/open-obligation record inventory mismatch",
    )
    for record_id, expected in REQUIRED_RECORDS.items():
        record = records[record_id]
        exact_keys(
            record,
            {
                "construction_id",
                "id",
                "implementation_disposition",
                "issue_class",
                "locator",
                "observed",
                "proposed_resolution",
                "reviewer_adjudication",
                "source_id",
                "test_bindings",
                "upstream_confirmation",
            },
            f"record {record_id}",
        )
        require(
            record["construction_id"] == expected["construction_id"],
            f"record {record_id} construction transfer detected",
        )
        require(
            record["source_id"] == expected["source_id"],
            f"record {record_id} source revision mismatch",
        )
        require(
            record["construction_id"] in constructions,
            f"record {record_id} unknown construction",
        )
        require(record["source_id"] in sources, f"record {record_id} unknown source")
        require(
            sources[record["source_id"]]["construction_id"]
            == record["construction_id"],
            f"record {record_id} crosses source construction",
        )
        require(
            record["issue_class"] == expected["issue_class"],
            f"record {record_id} issue-class mismatch",
        )
        locator = expect_object(record["locator"], f"record {record_id}.locator")
        exact_keys(
            locator,
            {"named_object", "physical_pdf_pages", "textual_anchor"},
            f"record {record_id}.locator",
        )
        require(
            locator["named_object"] == expected["named_object"],
            f"record {record_id} named locator mismatch",
        )
        pages = expect_array(
            locator["physical_pdf_pages"], f"record {record_id}.physical_pdf_pages"
        )
        require(
            all(type(page) is int and page > 0 for page in pages),
            f"record {record_id} physical PDF pages must be positive integers",
        )
        require(
            pages == expected["pages"], f"record {record_id} physical PDF page mismatch"
        )
        expect_string(locator["textual_anchor"], f"record {record_id}.textual_anchor")
        expect_string(record["observed"], f"record {record_id}.observed")
        reviewer = expect_object(
            record["reviewer_adjudication"], f"record {record_id}.reviewer_adjudication"
        )
        exact_keys(
            reviewer, {"basis", "status"}, f"record {record_id}.reviewer_adjudication"
        )
        expect_string(reviewer["basis"], f"record {record_id}.reviewer basis")
        require(
            reviewer["status"] == expected["reviewer_status"],
            f"record {record_id} reviewer adjudication mismatch",
        )
        resolution = expect_object(
            record["proposed_resolution"], f"record {record_id}.proposed_resolution"
        )
        exact_keys(
            resolution, {"status", "text"}, f"record {record_id}.proposed_resolution"
        )
        require(
            resolution["status"] == expected["resolution_status"],
            f"record {record_id} resolution status mismatch",
        )
        expect_string(resolution["text"], f"record {record_id}.resolution text")
        implementation = expect_object(
            record["implementation_disposition"],
            f"record {record_id}.implementation_disposition",
        )
        exact_keys(
            implementation,
            {"status", "summary"},
            f"record {record_id}.implementation_disposition",
        )
        require(
            implementation["status"] == expected["implementation_status"],
            f"record {record_id} implementation disposition mismatch",
        )
        expect_string(
            implementation["summary"], f"record {record_id}.implementation summary"
        )
        upstream = expect_object(
            record["upstream_confirmation"], f"record {record_id}.upstream_confirmation"
        )
        exact_keys(
            upstream, {"status", "summary"}, f"record {record_id}.upstream_confirmation"
        )
        require(
            upstream["status"] == "not_author_or_publisher_confirmed",
            f"record {record_id} fabricates author/publisher confirmation",
        )
        require(
            upstream["status"] not in FORBIDDEN_CONFIRMATION_STATUSES,
            f"record {record_id} uses forbidden confirmation status",
        )
        expect_string(upstream["summary"], f"record {record_id}.upstream summary")
        bindings = expect_array(
            record["test_bindings"], f"record {record_id}.test_bindings"
        )
        require(
            len(bindings) == 1,
            f"record {record_id} must have exactly one scoped binding",
        )
        binding = expect_object(bindings[0], f"record {record_id}.test_bindings[0]")
        require(
            binding.get("kind") == expected["binding_kind"],
            f"record {record_id} binding kind mismatch",
        )
        require(
            binding.get("path") == expected["binding_path"],
            f"record {record_id} binding path mismatch",
        )
        require(
            binding.get("test_name") == expected["binding_test"],
            f"record {record_id} binding test mismatch",
        )
        require(
            binding.get("marker")
            == (
                f"Source-erratum binding: {record_id}."
                if expected["binding_kind"] == "behavioral_regression"
                else record_id
            ),
            f"record {record_id} binding marker mismatch",
        )
        check_binding(
            repository_root,
            record_id,
            binding,
            require_test_attribute=expected["binding_kind"] == "behavioral_regression",
        )
    counts = Counter(record["issue_class"] for record in records.values())
    require(
        counts == Counter({"source_erratum_candidate": 4, "open_source_obligation": 4}),
        "registry must retain four Ehrlich candidate corrections and four Schick open obligations",
    )
    require(
        not any(
            record["construction_id"] == "mgw-categorical-shared-exclusions"
            for record in records.values()
        ),
        "MGW construction must not receive Ehrlich/Schick errata",
    )
    equation_14 = records["ehrlich-v3-equation-14-units"]
    resolution = equation_14["proposed_resolution"]["text"].lower()
    require(
        "divide" in resolution
        and "ln(2)" in resolution
        and "nats = bits * ln(2)" in resolution,
        "Equation (14) unit correction must bind division-by-ln(2) for bits and multiplication-by-ln(2) for bit fixtures",
    )
    algorithm_6 = records["ehrlich-v3-algorithm-6-wiring"]
    wiring = algorithm_6["proposed_resolution"]["text"]
    require(
        "compute_epsilons(S, T, antichain)" in wiring,
        "Algorithm 6 correction omits antichain from epsilon routine",
    )
    require(
        "compute_n_alpha(S, antichain, eps)" in wiring,
        "Algorithm 6 correction omits antichain from source routine",
    )
    require(
        "compute_n_T(T, eps)" in wiring,
        "Algorithm 6 correction uses wrong target routine",
    )
    cantor_text = " ".join(
        (
            records["schick-poland-v2-borel-isomorphism-density"]["observed"],
            records["schick-poland-v2-borel-isomorphism-density"][
                "proposed_resolution"
            ]["text"],
            records["schick-poland-v2-borel-isomorphism-density"][
                "upstream_confirmation"
            ]["summary"],
        )
    ).lower()
    for phrase in OVERBROAD_CANTOR_PHRASES:
        require(
            phrase not in cantor_text,
            f"overbroad Cantor/mod-null wording is forbidden: {phrase!r}",
        )
    for fragment in (
        "ambient-coordinate absolute continuity",
        "bare borel isomorphism",
        "stronger mod-null measure-space representation",
        "would be a different argument",
    ):
        require(
            fragment in cantor_text, f"narrow Cantor/Borel boundary omits {fragment!r}"
        )


def check_nonimplications(root: dict[str, Any]) -> None:
    values = expect_array(root["nonimplications"], "nonimplications")
    require(
        len(values) == 4, "nonimplications must retain exactly four reviewed boundaries"
    )
    require(
        all(type(value) is str and value for value in values),
        "nonimplications must be non-empty strings",
    )
    joined = "\n".join(values)
    for fragment in REQUIRED_NONIMPLICATION_FRAGMENTS:
        require(
            fragment in joined, f"nonimplications omit required boundary {fragment!r}"
        )


def check_firewall(root: dict[str, Any], repository_root: Path) -> None:
    firewall = expect_object(root["construction_firewall"], "construction_firewall")
    exact_keys(
        firewall,
        {"cross_construction_transfer", "mgw_uniform_binary_xor"},
        "construction_firewall",
    )
    transfer = expect_string(
        firewall["cross_construction_transfer"],
        "construction_firewall.cross_construction_transfer",
    )
    for fragment in (
        "exact source revision",
        "construction_id",
        "explicit mapping theorem",
    ):
        require(fragment in transfer, f"construction firewall omits {fragment!r}")
    xor = expect_object(
        firewall["mgw_uniform_binary_xor"],
        "construction_firewall.mgw_uniform_binary_xor",
    )
    exact_keys(
        xor,
        {
            "construction_id",
            "expected_redundancy_nats",
            "expected_synergy_nats",
            "scope",
            "test_binding",
        },
        "construction_firewall.mgw_uniform_binary_xor",
    )
    require(
        xor["construction_id"] == "mgw-categorical-shared-exclusions",
        "XOR firewall construction mismatch",
    )
    require(
        xor["expected_redundancy_nats"] == "ln(2/3)",
        "MGW XOR redundancy must remain ln(2/3) nats",
    )
    require(
        xor["expected_synergy_nats"] == "ln(4/3)",
        "MGW XOR synergy must remain ln(4/3) nats, not 1.58496 bits",
    )
    scope = expect_string(xor["scope"], "MGW XOR scope")
    for fragment in (
        "Uniform independent binary",
        "MGW categorical SxPID2",
        "not Ehrlich-continuous",
        "Williams-Beer I_min",
    ):
        require(
            fragment in scope, f"MGW XOR scope omits construction boundary {fragment!r}"
        )
    binding = expect_object(xor["test_binding"], "MGW XOR test binding")
    expected_binding = {
        "kind": "behavioral_regression",
        "marker": "XOR synergy does not equal ln(4/3)",
        "path": "scripts/generate-sxpid2-exhaustive-oracle.py",
        "test_name": "self_test",
    }
    require(binding == expected_binding, "MGW XOR test binding mismatch")
    path = safe_binding_path(repository_root, binding["path"])
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ErrataError(
            f"cannot read MGW XOR binding {binding['path']}: {error}"
        ) from error
    require(binding["marker"] in text, "MGW XOR exact-value marker is missing")
    require(
        re.search(r"\bdef\s+self_test\s*\(", text) is not None,
        "MGW XOR exact-value self-test function is missing",
    )


def run(
    registry_path: Path, schema_path: Path, repository_root: Path
) -> tuple[int, str, str]:
    registry, registry_raw = load_canonical_json(registry_path, "registry")
    schema, schema_raw = load_canonical_json(schema_path, "schema")
    check_schema_document(schema)
    root = check_registry_shape(registry)
    constructions = check_constructions(root)
    sources = check_sources(root, constructions)
    check_records(root, constructions, sources, repository_root)
    check_nonimplications(root)
    check_firewall(root, repository_root)
    registry_hash = hashlib.sha256(registry_raw).hexdigest()
    schema_hash = hashlib.sha256(schema_raw).hexdigest()
    require(
        registry_hash == EXPECTED_REGISTRY_SHA256,
        "registry bytes differ from the reviewed revision-1 authority; re-adjudicate and explicitly rebase the checker digest",
    )
    require(
        schema_hash == EXPECTED_SCHEMA_SHA256,
        "schema bytes differ from the reviewed revision-1 authority; re-adjudicate and explicitly rebase the checker digest",
    )
    return (
        len(root["records"]),
        registry_hash,
        schema_hash,
    )


def main() -> int:
    arguments = parse_args()
    try:
        record_count, registry_hash, schema_hash = run(
            arguments.registry, arguments.schema, arguments.root
        )
    except (ErrataError, OSError) as error:
        print(f"source-errata check failed: {error}", file=sys.stderr)
        return 1
    print(
        "source-errata check: OK "
        f"({record_count} records; registry_sha256={registry_hash}; schema_sha256={schema_hash})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
