#!/usr/bin/env python3
"""Check the typed X-thread application record and retained adjacent-arrow countermodel.

This deliberately proves only a small logical negative result: an isomorphism on one arrow of an
exact sequence cannot be transferred to its neighbor.  The application check validates retained
metadata and internal cross-bindings; it does not validate the cited motivic theorem, any other
part of the corrected manuscript, or a pid-rs theorem.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKFLOW = ROOT / "MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"
DEFAULT_TEX = ROOT / "audit/formal/latex/mathematical-problem-solving-workflow.tex"
DEFAULT_APPLICATION_RECORD = ROOT / "audit/evidence/x-thread-citation-edge-application.json"
DEFAULT_SOURCE_MANIFEST = ROOT / "audit/evidence/x-thread-citation-source-manifest.json"
REQUIRED_SENTINELS = (
    "Corrected vector-bundle claim: a typed citation-edge failure",
    "Equation (27) is therefore false",
    "Named source arrow (domain -> codomain):",
    "Citation-edge type check",
    "0 -> 0 -> Z/2 --id--> Z/2 -> 0",
    "0 -> 0 -> C2 --id--> C2 -> 0",
    "audit/formal/lean-citation-edge/PidCitationEdgeCountermodel.lean",
    "materially distinct valid proof or solution",
    "Repeated passes by the same model",
)

MANIFEST_ID = "X-VECTOR-BUNDLE-CITATION-SOURCES-001"
RECORD_ID = "X-VECTOR-BUNDLE-CITATION-EDGE-001"
EXPECTED_MANIFEST_SHA256 = "bc6db3d1d5c5dd8c2b0059280881d041ea1b07b5fd8aabd2d20c953ebed0b907"
SHA256_RE = re.compile(r"[0-9a-f]{64}")

EXPECTED_ARTIFACTS = {
    "abh-2306.04631v3": {
        "kind": "versioned_arxiv_pdf",
        "locator": "https://arxiv.org/pdf/2306.04631v3",
        "locator_stability": "versioned_content_locator_bytes_may_be_regenerated",
        "page_count": 75,
        "sha256": "d4bd95572c7e2c356e964407ceab26c64c37768a655b45b45feaa4ab50dd8536",
        "spans": {
            "abh-theorem-7.2.1": (70, 70),
            "abh-theorem-7.2.2-point-3": (70, 71),
        },
        "version": "2306.04631v3",
    },
    "draft-algebraizable-observed-2026-07-25": {
        "kind": "mutable_web_pdf_snapshot",
        "locator": "https://www.ulam.ai/research/algebraizable.pdf",
        "locator_stability": "mutable_locator_observed_at_manifest_date",
        "page_count": 18,
        "sha256": "ebb5aa2c8d1d08cd1c7692ac0526cf537c00985bf5e129ff165be128404e69ca",
        "spans": {
            "draft-theorem-7.1-equations-26-29": (11, 11),
            "draft-corollary-8.3-and-theorem-8.4": (13, 13),
            "draft-theorem-a-proof": (13, 14),
            "draft-theorem-a-statement": (2, 2),
            "draft-corollary-1.1-statement": (2, 2),
            "draft-corollary-1.1-proof": (14, 14),
        },
        "version": "observed-2026-07-25",
    },
    "rso-1604.00365v2": {
        "kind": "versioned_arxiv_pdf",
        "locator": "https://arxiv.org/pdf/1604.00365v2",
        "locator_stability": "versioned_content_locator_bytes_may_be_regenerated",
        "page_count": 66,
        "sha256": "bdcf6f0ef128457740c09c5fb38c1a187951b29119d5ec2b8ba0339cb7887966",
        "spans": {
            "rso-definition-2.1-and-remark-2.2": (5, 5),
            "rso-equation-1.1": (2, 2),
            "rso-theorem-5.5": (57, 57),
        },
        "version": "1604.00365v2",
    },
}

EXPECTED_WEB_LOCATORS = {
    "x-author-acknowledgement": (
        "https://x.com/prz_chojecki/status/2080766940604481575",
        "2080766940604481575",
        "author_acknowledgement",
    ),
    "x-author-correction": (
        "https://x.com/prz_chojecki/status/2080767793452970317",
        "2080767793452970317",
        "author_correction",
    ),
    "x-specific-objection": (
        "https://x.com/tonylfeng/status/2080757463780094146",
        "2080757463780094146",
        "specific_objection",
    ),
    "x-original-claim": (
        "https://x.com/prz_chojecki/status/2080659698085191915",
        "2080659698085191915",
        "original_claim",
    ),
}

EXPECTED_SOURCE_ARROWS = {
    "ABH-T721-ZERO-TO-KM": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.1",
        "0",
        "K^M_{d+2-j}/24",
    ),
    "ABH-T721-LEFT-NU": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.1",
        "K^M_{d+2-j}/24",
        "pi^A1_{d+j,j}(S^{2d-1,d})",
    ),
    "ABH-T721-RIGHT-GW": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.1",
        "pi^A1_{d+j,j}(S^{2d-1,d})",
        "GW^{d-j}_{d+1-j}",
    ),
    "ABH-T7223-ZERO-TO-KM": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.2-point-3",
        "0",
        "K^M_{d+2-r}/24",
    ),
    "ABH-T7223-LEFT-NU": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.2-point-3",
        "K^M_{d+2-r}/24",
        "pi^A1_{4+r,r}(S^{3+d,d})",
    ),
    "ABH-T7223-RIGHT-GW": (
        "abh-2306.04631v3",
        "abh-theorem-7.2.2-point-3",
        "pi^A1_{4+r,r}(S^{3+d,d})",
        "GW^{d-r}_{d+1-r}",
    ),
    "RSO-EQ11-ZERO-TO-KM": (
        "rso-1604.00365v2",
        "rso-equation-1.1",
        "0",
        "K^M_2(F)/24",
    ),
    "RSO-EQ11-LEFT-NU": (
        "rso-1604.00365v2",
        "rso-equation-1.1",
        "K^M_2(F)/24",
        "pi_{1,0} 1(F)",
    ),
    "RSO-EQ11-RIGHT-ARITHMETIC": (
        "rso-1604.00365v2",
        "rso-equation-1.1",
        "pi_{1,0} 1(F)",
        "direct_sum(F^x/(F^x)^2,Z/2)",
    ),
    "RSO-EQ11-ARITHMETIC-TO-ZERO": (
        "rso-1604.00365v2",
        "rso-equation-1.1",
        "direct_sum(F^x/(F^x)^2,Z/2)",
        "0",
    ),
}

EXPECTED_LOCAL_ARROWS = {
    "DRAFT-EQ27-NU-SPECIALIZATION": (
        "draft-algebraizable-observed-2026-07-25",
        "draft-theorem-7.1-equations-26-29",
        "K^M_2(C)/24",
        "pi^A1_{10,5}(S^{9,5})(C)",
    ),
    "DRAFT-EQ26-FIRST": (
        "draft-algebraizable-observed-2026-07-25",
        "draft-theorem-7.1-equations-26-29",
        "pi^A1_{10,5}(S^{9,5})(C)",
        "pi^A1_{9,5}(SL_4)(C)",
    ),
    "DRAFT-EQ26-SECOND": (
        "draft-algebraizable-observed-2026-07-25",
        "draft-theorem-7.1-equations-26-29",
        "pi^A1_{9,5}(SL_4)(C)",
        "pi^A1_{9,5}(SL_5)(C)",
    ),
}

EXPECTED_ARROW_SEQUENCES = {
    "ABH-T721-SEQUENCE": (
        "short_exact_as_stated",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        "abh-theorem-7.2.1",
        ["ABH-T721-ZERO-TO-KM", "ABH-T721-LEFT-NU", "ABH-T721-RIGHT-GW"],
    ),
    "ABH-T7223-SEQUENCE": (
        "short_exact_as_stated",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        "abh-theorem-7.2.2-point-3",
        ["ABH-T7223-ZERO-TO-KM", "ABH-T7223-LEFT-NU", "ABH-T7223-RIGHT-GW"],
    ),
    "RSO-EQ11-SEQUENCE": (
        "short_exact_as_stated",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        "rso-equation-1.1",
        [
            "RSO-EQ11-ZERO-TO-KM",
            "RSO-EQ11-LEFT-NU",
            "RSO-EQ11-RIGHT-ARITHMETIC",
            "RSO-EQ11-ARITHMETIC-TO-ZERO",
        ],
    ),
    "DRAFT-EQ26-EXACT-FRAGMENT": (
        "displayed_exact_fragment",
        "RECORDED_DRAFT_ARGUMENT",
        "draft-theorem-7.1-equations-26-29",
        ["DRAFT-EQ26-FIRST", "DRAFT-EQ26-SECOND"],
    ),
}

EXPECTED_VARIABLE_MAPS = {
    "ABH-D5-J5-R5-KC": {
        "d": ("integer", "5"),
        "j": ("integer", "5"),
        "k": ("field", "C"),
        "r": ("integer", "5"),
    },
    "RSO-FC-LAMBDAZ": {
        "F": ("field", "C"),
        "Lambda": ("coefficient_ring", "Z"),
    },
}

EXPECTED_EVIDENCE = {
    "E-ABH-SOURCE-STATEMENTS": (
        "source_span",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        {"abh-theorem-7.2.1", "abh-theorem-7.2.2-point-3"},
    ),
    "E-C-CHARACTERISTIC": ("local_exact_fact", "LOCAL_EXACT_CHECK", set()),
    "E-C-SQUARE-QUOTIENT-ZERO": ("local_exact_fact", "LOCAL_EXACT_CHECK", set()),
    "E-C2-COUNTERMODEL": (
        "executable_countermodel",
        "EXECUTABLE_FINITE_COUNTERMODEL",
        set(),
    ),
    "E-D5-J5-RANGE": ("local_exact_fact", "LOCAL_EXACT_CHECK", set()),
    "E-K2-C-MOD24-ZERO": ("local_exact_fact", "LOCAL_EXACT_CHECK", set()),
    "E-RSO-COMPATIBILITY": (
        "source_span",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        {"rso-definition-2.1-and-remark-2.2"},
    ),
    "E-RSO-EXACT-SEQUENCE": (
        "source_span",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        {"rso-equation-1.1", "rso-theorem-5.5"},
    ),
}

EXPECTED_HYPOTHESES = {
    "H-ABH-CHARACTERISTIC-ZERO": (
        "SATISFIED_BY_LOCAL_CHECK",
        {"E-C-CHARACTERISTIC"},
    ),
    "H-ABH-D-AT-LEAST-4": ("SATISFIED_BY_LOCAL_CHECK", {"E-D5-J5-RANGE"}),
    "H-ABH-SURJECTIVE-RANGE": ("SATISFIED_BY_LOCAL_CHECK", {"E-D5-J5-RANGE"}),
    "H-ABH-RSO-STABLE-COMPARISON": (
        "RECORDED_EXTERNAL_PREMISE_NOT_REPROVED",
        {"E-ABH-SOURCE-STATEMENTS", "E-RSO-EXACT-SEQUENCE"},
    ),
    "H-RSO-CHARACTERISTIC-NOT-2": (
        "SATISFIED_BY_LOCAL_CHECK",
        {"E-C-CHARACTERISTIC"},
    ),
    "H-RSO-COMPATIBLE-PAIR": (
        "SATISFIED_BY_RECORDED_SOURCE_DOMAIN_CHECK",
        {"E-C-CHARACTERISTIC", "E-RSO-COMPATIBILITY"},
    ),
}

EXPECTED_PREDICATE_BINDINGS = {
    "ABH-T7223-RIGHT-SURJECTIVE": (
        "surjective",
        "ABH-T7223-RIGHT-GW",
        "ABH-T7223-SEQUENCE",
        "RECORDED_SOURCE_PREMISE_NOT_REPROVED",
        {"abh-theorem-7.2.2-point-3"},
        {"H-ABH-CHARACTERISTIC-ZERO", "H-ABH-SURJECTIVE-RANGE"},
    ),
    "DRAFT-ATTEMPTED-ABH-LEFT-ISO": (
        "isomorphism",
        "ABH-T721-LEFT-NU",
        "ABH-T721-SEQUENCE",
        "REJECTED_UNRESOLVED_SOURCE_ANAPHOR",
        {"abh-theorem-7.2.1"},
        {"H-ABH-CHARACTERISTIC-ZERO", "H-ABH-D-AT-LEAST-4"},
    ),
}


class CheckFailure(Exception):
    """A closed countermodel or document-binding obligation failed."""


@dataclass(frozen=True)
class CyclicGroup:
    """The additive cyclic group Z/order; order one is the trivial group."""

    order: int

    def __post_init__(self) -> None:
        if self.order < 1:
            raise CheckFailure("cyclic-group order must be positive")

    @property
    def elements(self) -> tuple[int, ...]:
        return tuple(range(self.order))

    def add(self, left: int, right: int) -> int:
        return (left + right) % self.order


@dataclass(frozen=True)
class Homomorphism:
    source: CyclicGroup
    target: CyclicGroup
    images: tuple[int, ...]

    def is_homomorphism(self) -> bool:
        if len(self.images) != self.source.order:
            return False
        if any(image not in self.target.elements for image in self.images):
            return False
        return all(
            self.images[self.source.add(left, right)]
            == self.target.add(self.images[left], self.images[right])
            for left in self.source.elements
            for right in self.source.elements
        )

    @property
    def image(self) -> frozenset[int]:
        return frozenset(self.images)

    @property
    def kernel(self) -> frozenset[int]:
        return frozenset(
            element for element in self.source.elements if self.images[element] == 0
        )

    def is_injective(self) -> bool:
        return len(self.image) == self.source.order

    def is_surjective(self) -> bool:
        return self.image == frozenset(self.target.elements)

    def is_isomorphism(self) -> bool:
        return self.is_homomorphism() and self.is_injective() and self.is_surjective()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise CheckFailure(message)


def require_exact_keys(value: object, expected: set[str], context: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{context} must be an object")
    typed = value
    actual = set(typed)
    require(
        actual == expected,
        f"{context} keys differ: expected {sorted(expected)}, got {sorted(actual)}",
    )
    return typed


def require_nonempty_string(value: object, context: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{context} must be a nonempty string")
    return value


def require_string_list(value: object, context: str) -> list[str]:
    require(isinstance(value, list), f"{context} must be an array")
    require(
        all(isinstance(item, str) and item for item in value),
        f"{context} must contain only nonempty strings",
    )
    typed = value
    require(len(typed) == len(set(typed)), f"{context} contains duplicate values")
    return typed


def index_objects(value: object, id_field: str, context: str) -> dict[str, dict[str, Any]]:
    require(isinstance(value, list), f"{context} must be an array")
    indexed: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(value):
        require(isinstance(item, dict), f"{context}[{index}] must be an object")
        identifier = require_nonempty_string(item.get(id_field), f"{context}[{index}].{id_field}")
        require(identifier not in indexed, f"{context} contains duplicate id {identifier!r}")
        indexed[identifier] = item
    return indexed


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CheckFailure(f"JSON object contains duplicate key {key!r}")
        result[key] = value
    return result


def load_canonical_json(path: Path, context: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    try:
        value = json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except json.JSONDecodeError as error:
        raise CheckFailure(f"{context} is not valid JSON: {error}") from error
    require(isinstance(value, dict), f"{context} root must be an object")
    canonical = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    require(raw == canonical, f"{context} must use canonical sorted two-space JSON encoding")
    return value, raw


def validate_source_manifest(path: Path) -> tuple[dict[str, Any], dict[str, tuple[str, int, int]], bytes]:
    manifest, raw = load_canonical_json(path, "source manifest")
    require_exact_keys(
        manifest,
        {
            "artifacts",
            "claims",
            "digest_scope",
            "manifest_id",
            "observed_at",
            "schema",
            "web_locators",
        },
        "source manifest",
    )
    require(manifest["schema"] == 1, "source manifest schema must be 1")
    require(manifest["manifest_id"] == MANIFEST_ID, "source manifest id drifted")
    require(manifest["observed_at"] == "2026-07-25", "source observation date drifted")
    require(
        manifest["digest_scope"]
        == "sha256_of_raw_downloaded_pdf_bytes_observed_on_2026-07-25",
        "source digest scope drifted",
    )
    claims = require_exact_keys(
        manifest["claims"],
        {
            "external_pdf_bytes_retained_in_repository",
            "pdf_digest_recomputed_by_validator",
            "source_theorems_reproved_by_validator",
            "thread_completeness_claimed",
            "x_content_bytes_retained_in_repository",
        },
        "source manifest claims",
    )
    require(
        all(value is False for value in claims.values()),
        "source manifest must not claim retained bytes, source re-proof, or thread completeness",
    )

    artifacts = index_objects(manifest["artifacts"], "artifact_id", "source artifacts")
    require(set(artifacts) == set(EXPECTED_ARTIFACTS), "source artifact inventory drifted")
    spans: dict[str, tuple[str, int, int]] = {}
    for artifact_id, expected in EXPECTED_ARTIFACTS.items():
        artifact = require_exact_keys(
            artifacts[artifact_id],
            {
                "artifact_id",
                "canonical_locator",
                "kind",
                "locator_stability",
                "page_count",
                "retention",
                "sha256",
                "spans",
                "version",
            },
            f"source artifact {artifact_id}",
        )
        require(artifact["kind"] == expected["kind"], f"{artifact_id}: kind drifted")
        require(
            artifact["canonical_locator"] == expected["locator"],
            f"{artifact_id}: locator drifted",
        )
        require(
            artifact["locator_stability"] == expected["locator_stability"],
            f"{artifact_id}: locator-stability state drifted",
        )
        require(
            artifact["retention"] == "locator_digest_and_span_metadata_only",
            f"{artifact_id}: retention boundary drifted",
        )
        require(artifact["version"] == expected["version"], f"{artifact_id}: version drifted")
        require(
            artifact["page_count"] == expected["page_count"],
            f"{artifact_id}: page count drifted",
        )
        digest = require_nonempty_string(artifact["sha256"], f"{artifact_id}.sha256")
        require(SHA256_RE.fullmatch(digest) is not None, f"{artifact_id}: invalid SHA-256")
        require(digest == expected["sha256"], f"{artifact_id}: observed PDF digest drifted")

        artifact_spans = index_objects(artifact["spans"], "span_id", f"{artifact_id} spans")
        expected_spans = expected["spans"]
        require(set(artifact_spans) == set(expected_spans), f"{artifact_id}: span inventory drifted")
        for span_id, (expected_start, expected_end) in expected_spans.items():
            span = require_exact_keys(
                artifact_spans[span_id],
                {"end_anchor", "page_end", "page_start", "span_id", "start_anchor"},
                f"source span {span_id}",
            )
            page_start = span["page_start"]
            page_end = span["page_end"]
            require(
                isinstance(page_start, int) and not isinstance(page_start, bool),
                f"{span_id}: page_start must be an integer",
            )
            require(
                isinstance(page_end, int) and not isinstance(page_end, bool),
                f"{span_id}: page_end must be an integer",
            )
            require(
                (page_start, page_end) == (expected_start, expected_end),
                f"{span_id}: page span drifted",
            )
            require(
                1 <= page_start <= page_end <= artifact["page_count"],
                f"{span_id}: page span lies outside its artifact",
            )
            require_nonempty_string(span["start_anchor"], f"{span_id}.start_anchor")
            require_nonempty_string(span["end_anchor"], f"{span_id}.end_anchor")
            require(span_id not in spans, f"duplicate global source span id {span_id!r}")
            spans[span_id] = (artifact_id, page_start, page_end)

    web_locators = index_objects(manifest["web_locators"], "locator_id", "web locators")
    require(set(web_locators) == set(EXPECTED_WEB_LOCATORS), "X locator inventory drifted")
    for locator_id, (url, status_id, role) in EXPECTED_WEB_LOCATORS.items():
        locator = require_exact_keys(
            web_locators[locator_id],
            {
                "canonical_locator",
                "content_sha256",
                "locator_id",
                "retention",
                "role",
                "status_id",
            },
            f"web locator {locator_id}",
        )
        require(locator["canonical_locator"] == url, f"{locator_id}: URL drifted")
        require(locator["status_id"] == status_id, f"{locator_id}: status id drifted")
        require(url.endswith(status_id), f"{locator_id}: URL/status id mismatch")
        require(locator["role"] == role, f"{locator_id}: role drifted")
        require(locator["content_sha256"] is None, f"{locator_id}: unretained content has a digest")
        require(
            locator["retention"] == "locator_only_no_content_digest",
            f"{locator_id}: X retention boundary drifted",
        )

    return artifacts, spans, raw


def validate_typed_arrows(
    value: object,
    context: str,
    expected: dict[str, tuple[str, str, str, str]],
    artifacts: dict[str, dict[str, Any]],
    spans: dict[str, tuple[str, int, int]],
) -> dict[str, dict[str, Any]]:
    arrows = index_objects(value, "arrow_id", context)
    require(set(arrows) == set(expected), f"{context} inventory drifted")
    for arrow_id, (artifact_id, span_id, domain, codomain) in expected.items():
        arrow = require_exact_keys(
            arrows[arrow_id],
            {
                "arrow_id",
                "artifact_id",
                "codomain",
                "direction",
                "domain",
                "signature",
                "span_id",
            },
            f"{context} {arrow_id}",
        )
        require(arrow["artifact_id"] == artifact_id, f"{arrow_id}: artifact binding drifted")
        require(artifact_id in artifacts, f"{arrow_id}: unknown artifact")
        require(arrow["span_id"] == span_id, f"{arrow_id}: source span binding drifted")
        require(span_id in spans, f"{arrow_id}: unknown source span")
        require(spans[span_id][0] == artifact_id, f"{arrow_id}: span belongs to another artifact")
        require(arrow["domain"] == domain, f"{arrow_id}: domain drifted")
        require(arrow["codomain"] == codomain, f"{arrow_id}: codomain drifted")
        require(arrow["direction"] == "domain_to_codomain", f"{arrow_id}: direction reversed")
        require(arrow["signature"] == f"{domain} -> {codomain}", f"{arrow_id}: signature drifted")
    return arrows


def validate_application_record(
    path: Path,
    manifest_path: Path,
) -> dict[str, object]:
    artifacts, spans, manifest_raw = validate_source_manifest(manifest_path)
    record, _ = load_canonical_json(path, "citation-edge application record")
    require_exact_keys(
        record,
        {
            "ambiguity",
            "arrow_sequences",
            "blast_radius",
            "conclusion",
            "evidence",
            "hypotheses",
            "local_arrows",
            "local_correspondence",
            "manifest_id",
            "predicate_bindings",
            "record_id",
            "schema",
            "scope",
            "source_arrows",
            "source_bindings",
            "source_manifest_sha256",
            "variable_maps",
        },
        "citation-edge application record",
    )
    require(record["schema"] == 1, "application record schema must be 1")
    require(record["record_id"] == RECORD_ID, "application record id drifted")
    require(record["manifest_id"] == MANIFEST_ID, "application/manifest id mismatch")
    manifest_digest = hashlib.sha256(manifest_raw).hexdigest()
    require(
        manifest_digest == EXPECTED_MANIFEST_SHA256,
        "retained source manifest bytes drifted from the reviewed X-thread manifest",
    )
    declared_manifest_digest = require_nonempty_string(
        record["source_manifest_sha256"], "source_manifest_sha256"
    )
    require(
        SHA256_RE.fullmatch(declared_manifest_digest) is not None,
        "source_manifest_sha256 is not a lowercase SHA-256",
    )
    require(
        declared_manifest_digest == manifest_digest,
        "application record does not bind the exact source manifest bytes",
    )

    scope = require_exact_keys(
        record["scope"],
        {
            "case_id",
            "pid_claim_effect",
            "source_truth_validation",
            "thread_completeness",
            "validator_scope",
        },
        "application scope",
    )
    require(scope["case_id"] == "corrected-vector-bundle-x-thread", "case id drifted")
    require(scope["pid_claim_effect"] == "NONE", "record must remain PID-neutral")
    require(scope["source_truth_validation"] == "NOT_PERFORMED", "source-truth boundary drifted")
    require(scope["thread_completeness"] == "NOT_CLAIMED", "thread completeness is overclaimed")
    require(
        scope["validator_scope"]
        == "STRUCTURE_DIGEST_CROSS_BINDINGS_AND_FINITE_COUNTERMODEL",
        "validator-scope declaration drifted",
    )

    source_bindings = index_objects(record["source_bindings"], "artifact_id", "source bindings")
    require(set(source_bindings) == set(artifacts), "source binding artifact inventory drifted")
    for artifact_id, artifact in artifacts.items():
        binding = require_exact_keys(
            source_bindings[artifact_id],
            {"artifact_id", "sha256", "source_span_ids"},
            f"source binding {artifact_id}",
        )
        require(binding["sha256"] == artifact["sha256"], f"{artifact_id}: digest binding mismatch")
        span_ids = require_string_list(binding["source_span_ids"], f"{artifact_id}.source_span_ids")
        expected_span_ids = {
            span_id for span_id, (owner, _, _) in spans.items() if owner == artifact_id
        }
        require(set(span_ids) == expected_span_ids, f"{artifact_id}: bound source spans drifted")

    source_arrows = validate_typed_arrows(
        record["source_arrows"],
        "source arrows",
        EXPECTED_SOURCE_ARROWS,
        artifacts,
        spans,
    )
    local_arrows = validate_typed_arrows(
        record["local_arrows"],
        "local arrows",
        EXPECTED_LOCAL_ARROWS,
        artifacts,
        spans,
    )
    require(
        set(source_arrows).isdisjoint(local_arrows),
        "source and local arrow ids must be globally unique",
    )
    all_arrows = {**source_arrows, **local_arrows}
    sequences = index_objects(record["arrow_sequences"], "sequence_id", "arrow sequences")
    require(set(sequences) == set(EXPECTED_ARROW_SEQUENCES), "arrow-sequence inventory drifted")
    for sequence_id, expected in EXPECTED_ARROW_SEQUENCES.items():
        sequence_kind, truth_scope, span_id, expected_arrow_ids = expected
        sequence = require_exact_keys(
            sequences[sequence_id],
            {"arrow_ids", "sequence_id", "sequence_kind", "span_id", "truth_scope"},
            f"arrow sequence {sequence_id}",
        )
        require(sequence["sequence_kind"] == sequence_kind, f"{sequence_id}: kind drifted")
        require(sequence["truth_scope"] == truth_scope, f"{sequence_id}: truth scope drifted")
        require(sequence["span_id"] == span_id, f"{sequence_id}: source span drifted")
        require(span_id in spans, f"{sequence_id}: unknown source span")
        arrow_ids = require_string_list(sequence["arrow_ids"], f"{sequence_id}.arrow_ids")
        require(arrow_ids == expected_arrow_ids, f"{sequence_id}: arrow order drifted")
        require(all(arrow_id in all_arrows for arrow_id in arrow_ids), f"{sequence_id}: unknown arrow")
        for left_id, right_id in zip(arrow_ids, arrow_ids[1:]):
            require(
                all_arrows[left_id]["codomain"] == all_arrows[right_id]["domain"],
                f"{sequence_id}: non-composable adjacent arrows {left_id} and {right_id}",
            )

    variable_maps = index_objects(record["variable_maps"], "map_id", "variable maps")
    require(set(variable_maps) == set(EXPECTED_VARIABLE_MAPS), "variable-map inventory drifted")
    for map_id, expected_assignments in EXPECTED_VARIABLE_MAPS.items():
        variable_map = require_exact_keys(
            variable_maps[map_id], {"assignments", "map_id"}, f"variable map {map_id}"
        )
        assignments = index_objects(
            variable_map["assignments"], "source_variable", f"{map_id} assignments"
        )
        require(set(assignments) == set(expected_assignments), f"{map_id}: assignments drifted")
        for variable, (kind, local_value) in expected_assignments.items():
            assignment = require_exact_keys(
                assignments[variable],
                {"kind", "local_value", "source_variable"},
                f"{map_id}.{variable}",
            )
            require(assignment["kind"] == kind, f"{map_id}.{variable}: kind drifted")
            require(
                assignment["local_value"] == local_value,
                f"{map_id}.{variable}: local value drifted",
            )

    evidence = index_objects(record["evidence"], "evidence_id", "evidence")
    require(set(evidence) == set(EXPECTED_EVIDENCE), "evidence inventory drifted")
    for evidence_id, (kind, truth_scope, expected_spans) in EXPECTED_EVIDENCE.items():
        item = require_exact_keys(
            evidence[evidence_id],
            {"evidence_id", "kind", "source_span_ids", "statement", "truth_scope"},
            f"evidence {evidence_id}",
        )
        require(item["kind"] == kind, f"{evidence_id}: evidence kind drifted")
        require(item["truth_scope"] == truth_scope, f"{evidence_id}: truth scope drifted")
        require_nonempty_string(item["statement"], f"{evidence_id}.statement")
        source_span_ids = require_string_list(
            item["source_span_ids"], f"{evidence_id}.source_span_ids"
        )
        require(set(source_span_ids) == expected_spans, f"{evidence_id}: source spans drifted")
        require(all(span_id in spans for span_id in source_span_ids), f"{evidence_id}: unknown span")

    hypotheses = index_objects(record["hypotheses"], "hypothesis_id", "hypotheses")
    require(set(hypotheses) == set(EXPECTED_HYPOTHESES), "required hypothesis inventory drifted")
    for hypothesis_id, (status, expected_evidence) in EXPECTED_HYPOTHESES.items():
        hypothesis = require_exact_keys(
            hypotheses[hypothesis_id],
            {"evidence_ids", "hypothesis_id", "statement", "status"},
            f"hypothesis {hypothesis_id}",
        )
        require(hypothesis["status"] == status, f"{hypothesis_id}: status drifted")
        require_nonempty_string(hypothesis["statement"], f"{hypothesis_id}.statement")
        evidence_ids = require_string_list(
            hypothesis["evidence_ids"], f"{hypothesis_id}.evidence_ids"
        )
        require(set(evidence_ids) == expected_evidence, f"{hypothesis_id}: evidence drifted")
        require(all(item in evidence for item in evidence_ids), f"{hypothesis_id}: unknown evidence")

    predicates = index_objects(record["predicate_bindings"], "binding_id", "predicate bindings")
    require(set(predicates) == set(EXPECTED_PREDICATE_BINDINGS), "predicate-binding inventory drifted")
    for binding_id, expected in EXPECTED_PREDICATE_BINDINGS.items():
        predicate, arrow_id, sequence_id, status, expected_spans, expected_hypotheses = expected
        binding = require_exact_keys(
            predicates[binding_id],
            {
                "binding_id",
                "evidence_span_ids",
                "hypothesis_ids",
                "predicate",
                "sequence_id",
                "source_arrow_id",
                "status",
            },
            f"predicate binding {binding_id}",
        )
        require(binding["predicate"] == predicate, f"{binding_id}: predicate drifted")
        require(binding["source_arrow_id"] == arrow_id, f"{binding_id}: neighboring-arrow swap")
        require(arrow_id in source_arrows, f"{binding_id}: unknown source arrow")
        require(binding["sequence_id"] == sequence_id, f"{binding_id}: source sequence drifted")
        require(
            arrow_id in sequences[sequence_id]["arrow_ids"],
            f"{binding_id}: predicate arrow is outside its source sequence",
        )
        require(binding["status"] == status, f"{binding_id}: disposition drifted")
        binding_spans = require_string_list(
            binding["evidence_span_ids"], f"{binding_id}.evidence_span_ids"
        )
        require(set(binding_spans) == expected_spans, f"{binding_id}: evidence spans drifted")
        require(all(span_id in spans for span_id in binding_spans), f"{binding_id}: unknown span")
        hypothesis_ids = require_string_list(
            binding["hypothesis_ids"], f"{binding_id}.hypothesis_ids"
        )
        require(set(hypothesis_ids) == expected_hypotheses, f"{binding_id}: hypotheses drifted")
        require(all(item in hypotheses for item in hypothesis_ids), f"{binding_id}: unknown hypothesis")

    correspondence = require_exact_keys(
        record["local_correspondence"],
        {
            "codomain_after_variable_map",
            "direction_status",
            "domain_after_variable_map",
            "local_arrow_id",
            "source_arrow_id",
            "status",
            "variable_map_id",
        },
        "local correspondence",
    )
    require(correspondence["source_arrow_id"] == "ABH-T721-LEFT-NU", "source correspondence drifted")
    require(
        correspondence["local_arrow_id"] == "DRAFT-EQ27-NU-SPECIALIZATION",
        "local correspondence drifted",
    )
    require(
        correspondence["variable_map_id"] == "ABH-D5-J5-R5-KC",
        "variable map binding drifted",
    )
    require(correspondence["direction_status"] == "PRESERVED", "arrow direction is not preserved")
    require(
        correspondence["status"] == "TYPE_MATCH_ONLY_PREDICATE_NOT_ACCEPTED",
        "type match was promoted into predicate acceptance",
    )
    local_arrow = local_arrows[correspondence["local_arrow_id"]]
    source_arrow = source_arrows[correspondence["source_arrow_id"]]
    require(
        local_arrow["domain"] == correspondence["domain_after_variable_map"],
        "local domain does not match the recorded specialization",
    )
    require(
        local_arrow["codomain"] == correspondence["codomain_after_variable_map"],
        "local codomain does not match the recorded specialization",
    )
    require(
        local_arrow["direction"] == source_arrow["direction"],
        "source/local arrow direction mismatch",
    )

    ambiguity = require_exact_keys(
        record["ambiguity"],
        {
            "attempted_predicate_binding_id",
            "competing_arrow_ids",
            "context_evidence_span_ids",
            "favorable_referent_selection_permitted",
            "obligation_status",
            "source_span_id",
            "status",
        },
        "ambiguity record",
    )
    require(
        ambiguity["attempted_predicate_binding_id"] == "DRAFT-ATTEMPTED-ABH-LEFT-ISO",
        "ambiguity/attempted-predicate binding drifted",
    )
    competing = require_string_list(ambiguity["competing_arrow_ids"], "competing_arrow_ids")
    require(
        set(competing) == {"ABH-T721-LEFT-NU", "ABH-T721-RIGHT-GW"},
        "ambiguous neighboring-arrow set drifted",
    )
    require(all(arrow_id in source_arrows for arrow_id in competing), "unknown competing arrow")
    ambiguity_sequence = sequences["ABH-T721-SEQUENCE"]["arrow_ids"]
    competing_positions = sorted(ambiguity_sequence.index(arrow_id) for arrow_id in competing)
    require(
        competing_positions[1] - competing_positions[0] == 1,
        "ambiguous referents are not neighboring source arrows",
    )
    context_spans = require_string_list(
        ambiguity["context_evidence_span_ids"], "context_evidence_span_ids"
    )
    require(
        set(context_spans) == {"abh-theorem-7.2.2-point-3", "rso-theorem-5.5"},
        "ambiguity context spans drifted",
    )
    require(ambiguity["source_span_id"] == "abh-theorem-7.2.1", "ambiguity source span drifted")
    require(ambiguity["status"] == "UNRESOLVED_SOURCE_ANAPHOR", "ambiguity was falsely resolved")
    require(ambiguity["obligation_status"] == "BLOCKED", "ambiguous obligation must remain blocked")
    require(
        ambiguity["favorable_referent_selection_permitted"] is False,
        "favorable ambiguous-source selection must remain forbidden",
    )

    conclusion = require_exact_keys(
        record["conclusion"],
        {
            "basis_evidence_ids",
            "basis_hypothesis_ids",
            "claimed_equation_result",
            "corrected_result",
            "equation_disposition",
            "equation_id",
            "local_obligation_status",
            "source_truth_boundary",
            "theorem_7_1_disposition",
        },
        "conclusion",
    )
    require(conclusion["equation_id"] == "draft-equation-27", "equation id drifted")
    require(
        conclusion["equation_disposition"] == "FALSE_UNDER_RECORDED_SOURCE_PREMISES",
        "equation (27) disposition is not the retained false disposition",
    )
    require_nonempty_string(conclusion["claimed_equation_result"], "claimed_equation_result")
    require_nonempty_string(conclusion["corrected_result"], "corrected_result")
    require(
        conclusion["claimed_equation_result"] != conclusion["corrected_result"],
        "claimed and corrected equation results collapsed",
    )
    require(conclusion["local_obligation_status"] == "BLOCKED", "ambiguous import was closed")
    require(
        conclusion["source_truth_boundary"]
        == "RECORDED_EXTERNAL_PREMISES_NOT_REPROVED_BY_VALIDATOR",
        "source-truth conclusion boundary drifted",
    )
    require(
        conclusion["theorem_7_1_disposition"]
        == "DISPLAYED_PROOF_ROUTE_FAILED_THEOREM_NOT_ADJUDICATED",
        "equation failure was overextended to Theorem 7.1",
    )
    conclusion_evidence = require_string_list(
        conclusion["basis_evidence_ids"], "conclusion basis_evidence_ids"
    )
    require(
        set(conclusion_evidence)
        == {
            "E-C-SQUARE-QUOTIENT-ZERO",
            "E-C2-COUNTERMODEL",
            "E-K2-C-MOD24-ZERO",
            "E-RSO-EXACT-SEQUENCE",
        },
        "equation disposition evidence drifted",
    )
    conclusion_hypotheses = require_string_list(
        conclusion["basis_hypothesis_ids"], "conclusion basis_hypothesis_ids"
    )
    require(
        set(conclusion_hypotheses) == set(EXPECTED_HYPOTHESES),
        "equation disposition hypotheses drifted",
    )

    blast_radius = require_exact_keys(
        record["blast_radius"],
        {
            "conditional_local_remainder",
            "direct_failure_ids",
            "downstream_reopened",
            "not_adjudicated_claim_ids",
            "outside_cut_claim_ids",
            "state",
            "theorem_truth_disposition",
        },
        "blast radius",
    )
    require(
        blast_radius["state"] == "DOWNSTREAM_PROOF_ROUTE_REOPENED",
        "blast-radius state drifted",
    )
    require(
        blast_radius["theorem_truth_disposition"] == "NOT_ADJUDICATED",
        "blast radius overclaims theorem truth",
    )
    direct_failures = require_string_list(blast_radius["direct_failure_ids"], "direct_failure_ids")
    require(
        set(direct_failures) == {"draft-equation-27", "draft-theorem-7.1-displayed-proof"},
        "direct blast-radius failures drifted",
    )
    reopened = index_objects(blast_radius["downstream_reopened"], "claim_id", "downstream reopened")
    expected_reopened = {
        "draft-corollary-8.3": {"draft-corollary-8.3-and-theorem-8.4"},
        "draft-theorem-8.4": {"draft-corollary-8.3-and-theorem-8.4"},
        "draft-theorem-a-no-motivic-lift-route": {
            "draft-theorem-a-statement",
            "draft-theorem-a-proof",
        },
        "draft-corollary-1.1": {
            "draft-corollary-1.1-statement",
            "draft-corollary-1.1-proof",
        },
    }
    require(set(reopened) == set(expected_reopened), "downstream blast-radius inventory drifted")
    for claim_id, expected_spans in expected_reopened.items():
        item = require_exact_keys(
            reopened[claim_id], {"claim_id", "span_ids"}, f"downstream claim {claim_id}"
        )
        span_ids = require_string_list(item["span_ids"], f"{claim_id}.span_ids")
        require(set(span_ids) == expected_spans, f"{claim_id}: source spans drifted")
        require(all(span_id in spans for span_id in span_ids), f"{claim_id}: unknown source span")
    not_adjudicated = require_string_list(
        blast_radius["not_adjudicated_claim_ids"], "not_adjudicated_claim_ids"
    )
    require(
        set(not_adjudicated)
        == {
            "draft-theorem-7.1-truth",
            "draft-theorem-a-truth",
            "draft-nonalgebraizability-truth",
            "author-claim-that-other-machinery-survives",
        },
        "not-adjudicated boundary drifted",
    )
    outside_cut = require_string_list(blast_radius["outside_cut_claim_ids"], "outside_cut_claim_ids")
    require(
        outside_cut == ["draft-earlier-P4-projective-machinery"],
        "outside-cut boundary drifted",
    )
    require_nonempty_string(
        blast_radius["conditional_local_remainder"], "conditional_local_remainder"
    )

    return {
        "application_record_id": RECORD_ID,
        "blast_radius_state": blast_radius["state"],
        "equation_27_disposition": conclusion["equation_disposition"],
        "source_manifest_sha256": manifest_digest,
        "source_span_count": len(spans),
        "typed_source_arrow_count": len(source_arrows),
    }


def embedded_markdown(tex: str) -> str:
    begin = "\\begin{markdown}\n"
    end = "\n\\end{markdown}"
    require(tex.count(begin) == 1, "LaTeX must contain exactly one Markdown start marker")
    require(tex.count(end) == 1, "LaTeX must contain exactly one Markdown end marker")
    return tex.split(begin, 1)[1].split(end, 1)[0] + "\n"


def check_document_binding(workflow_path: Path, tex_path: Path) -> None:
    workflow = workflow_path.read_text(encoding="utf-8")
    tex = tex_path.read_text(encoding="utf-8")
    require(
        embedded_markdown(tex) == workflow,
        "LaTeX embedded Markdown differs from the canonical workflow",
    )
    for sentinel in REQUIRED_SENTINELS:
        require(sentinel in workflow, f"workflow sentinel is absent: {sentinel}")


def build_countermodel(mutation: str) -> tuple[tuple[CyclicGroup, ...], tuple[Homomorphism, ...], int]:
    trivial = CyclicGroup(1)
    c2 = trivial if mutation == "collapse-middle" else CyclicGroup(2)
    groups = (trivial, trivial, c2, c2, trivial)

    zero_to_zero = Homomorphism(trivial, trivial, (0,))
    zero_to_middle = Homomorphism(trivial, c2, (0,))
    middle_identity_images = tuple(c2.elements)
    if mutation == "break-exactness" and c2.order == 2:
        middle_identity_images = (0, 0)
    middle_map = Homomorphism(c2, c2, middle_identity_images)
    middle_to_zero = Homomorphism(c2, trivial, tuple(0 for _ in c2.elements))
    maps = (zero_to_zero, zero_to_middle, middle_map, middle_to_zero)

    certified_arrow = 1 if mutation == "bind-adjacent-arrow" else 2
    return groups, maps, certified_arrow


def check_countermodel(mutation: str) -> dict[str, object]:
    groups, maps, certified_arrow = build_countermodel(mutation)
    require(all(map_.is_homomorphism() for map_ in maps), "a displayed map is not a homomorphism")

    exact_at = tuple(maps[index - 1].image == maps[index].kernel for index in range(1, 4))
    require(all(exact_at), "the retained five-term sequence is not exact")
    require(
        maps[certified_arrow].is_isomorphism(),
        "the named source predicate is not true for the bound arrow",
    )
    require(not maps[1].is_isomorphism(), "the adjacent arrow unexpectedly is an isomorphism")
    require(groups[2].order > 1, "the middle group must be a retained nonzero witness")

    invalid_transfer_witnessed = (
        maps[2].is_isomorphism()
        and not maps[1].is_isomorphism()
        and groups[2].order > 1
    )
    require(
        invalid_transfer_witnessed,
        "the sequence does not refute adjacent-arrow isomorphism transfer",
    )

    return {
        "adjacent_arrow_isomorphism": maps[1].is_isomorphism(),
        "certified_arrow": certified_arrow,
        "exact_at_internal_terms": list(exact_at),
        "group_orders": [group.order for group in groups],
        "invalid_transfer_witnessed": invalid_transfer_witnessed,
        "right_arrow_isomorphism": maps[2].is_isomorphism(),
        "schema": 1,
        "scope": "local_exact_sequence_inference_only",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW)
    parser.add_argument("--tex", type=Path, default=DEFAULT_TEX)
    parser.add_argument(
        "--application-record",
        type=Path,
        default=DEFAULT_APPLICATION_RECORD,
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=DEFAULT_SOURCE_MANIFEST,
    )
    parser.add_argument(
        "--mutation",
        choices=("none", "bind-adjacent-arrow", "collapse-middle", "break-exactness"),
        default="none",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        check_document_binding(args.workflow, args.tex)
        application = validate_application_record(args.application_record, args.source_manifest)
        result = check_countermodel(args.mutation)
    except (CheckFailure, OSError, UnicodeError) as error:
        print(f"citation-edge countermodel check: {error}", file=sys.stderr)
        return 1

    result.update(application)
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
