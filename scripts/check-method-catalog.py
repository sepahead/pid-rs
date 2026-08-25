#!/usr/bin/env python3
"""Validate and render the pid-rs fine-grained method provenance catalog."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata

if sys.version_info < (3, 11):
    raise SystemExit("check-method-catalog.py requires Python 3.11 or newer")

import tomllib

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = ROOT / "method-catalog.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/method-catalog.schema.json"
DEFAULT_SEMANTIC_AUTHORITY = (
    ROOT / "audit/evidence/method-catalog-semantic-authority-v1.json"
)
DEFAULT_SEMANTIC_AUTHORITY_SCHEMA = (
    ROOT / "audit/schemas/method-catalog-semantic-authority-v1.schema.json"
)
DEFAULT_SCOPE = ROOT / "release-scope-1.0.json"
DEFAULT_MARKDOWN = ROOT / "METHODS.md"
DEFAULT_CARGO = ROOT / "crates/pid-core/Cargo.toml"
DEFAULT_SCIENTIFIC_CONTRACT_FIXTURES = (
    ROOT / "crates/pid-runlog/tests/fixtures/scientific_method_catalog_fixtures.json"
)
SCHEMA = "pid-rs/method-catalog"
SCHEMA_REVISION = 1
SEMANTIC_AUTHORITY_SCHEMA = "pid-rs/method-catalog-semantic-authority"
SEMANTIC_AUTHORITY_SCHEMA_REVISION = 1
SEMANTIC_ALIAS_DIAGNOSTIC_REVISION = 1
# Updating this reviewed root is the explicit re-adjudication step for any catalog semantic
# payload, typed fact, linked-reference record, alias diagnostic, or authority-schema change.
EXPECTED_SEMANTIC_AUTHORITY_ROOT_SHA256 = (
    "535268ca2df175478702339982d8b90fa0e3fd094329836646ac54c21f0678a8"
)
MIGRATION_METHOD_ID = "software.python-experimental-migration-bindings"
PYTHON_V1_METHOD_ID = "software.python-v1-bindings"
MIGRATION_PREFIX = "pid_core_rs.experimental.migration."
MIGRATION_ENTRYPOINT_OWNERS = {
    f"{MIGRATION_PREFIX}PlsProjector": frozenset({"preprocessing.pls"}),
    f"{MIGRATION_PREFIX}compute_co_information": frozenset(
        {"co-information.continuous-raw"}
    ),
    f"{MIGRATION_PREFIX}compute_discrete_pid2": frozenset(
        {"pid.same-sample-quantized-imin"}
    ),
    f"{MIGRATION_PREFIX}compute_discrete_pid3": frozenset(
        {"pid.same-sample-quantized-imin"}
    ),
    f"{MIGRATION_PREFIX}compute_discrete_sxpid2": frozenset(
        {"shared-exclusions.categorical"}
    ),
    f"{MIGRATION_PREFIX}compute_discrete_sxpid3": frozenset(
        {"shared-exclusions.categorical"}
    ),
    f"{MIGRATION_PREFIX}compute_discrete_sxpid_n": frozenset(
        {"shared-exclusions.categorical"}
    ),
    f"{MIGRATION_PREFIX}compute_invariants": frozenset(
        {"shannon-invariants.continuous-ksg-composition"}
    ),
    f"{MIGRATION_PREFIX}compute_mi": frozenset({"mutual-information.ksg1-raw"}),
    f"{MIGRATION_PREFIX}compute_mi_report": frozenset(
        {"mutual-information.hyperbolic-ksg", "mutual-information.ksg1-report"}
    ),
    f"{MIGRATION_PREFIX}compute_pid2": frozenset(
        {"pid.continuous-pid2", "shared-exclusions.continuous-heuristics"}
    ),
    f"{MIGRATION_PREFIX}compute_pid2_report": frozenset({"pid.continuous-pid2"}),
    f"{MIGRATION_PREFIX}compute_pid3": frozenset({"pid.mixed-dimension-pid3"}),
    f"{MIGRATION_PREFIX}compute_pid3_partial": frozenset(
        {"pid.incomplete-continuous-pid3"}
    ),
    f"{MIGRATION_PREFIX}compute_quantized_sxpid2": frozenset(
        {"shared-exclusions.same-sample-quantized"}
    ),
    f"{MIGRATION_PREFIX}compute_quantized_sxpid3": frozenset(
        {"shared-exclusions.same-sample-quantized"}
    ),
    f"{MIGRATION_PREFIX}compute_quantized_sxpid_n": frozenset(
        {"shared-exclusions.same-sample-quantized"}
    ),
    f"{MIGRATION_PREFIX}compute_redundancy": frozenset(
        {
            "shared-exclusions.continuous-heuristics",
            "shared-exclusions.continuous-raw",
        }
    ),
    f"{MIGRATION_PREFIX}continuous_input_diagnostics": frozenset(
        {"diagnostics.hyperbolic", "diagnostics.support-contracts"}
    ),
    f"{MIGRATION_PREFIX}distance_stats": frozenset(
        {"diagnostics.distance-concentration", "diagnostics.hyperbolic"}
    ),
    f"{MIGRATION_PREFIX}estimate_gromov_delta": frozenset(
        {"diagnostics.four-point-delta", "diagnostics.hyperbolic"}
    ),
    f"{MIGRATION_PREFIX}estimate_intrinsic_dimension": frozenset(
        {"diagnostics.hyperbolic", "diagnostics.intrinsic-dimension"}
    ),
    f"{MIGRATION_PREFIX}hash_project": frozenset({"preprocessing.hash-projection"}),
    f"{MIGRATION_PREFIX}pca_transform": frozenset({"preprocessing.pca"}),
    f"{MIGRATION_PREFIX}pls_transform": frozenset({"preprocessing.pls"}),
    f"{MIGRATION_PREFIX}sampled_four_point_delta_summary": frozenset(
        {"diagnostics.four-point-delta", "diagnostics.hyperbolic"}
    ),
    f"{MIGRATION_PREFIX}standardize": frozenset({"preprocessing.standardization"}),
}
MIGRATION_POLICY_ATTRIBUTES = frozenset(
    {
        f"{MIGRATION_PREFIX}RESOURCE_MAX_BYTES",
        f"{MIGRATION_PREFIX}RESOURCE_MAX_OPERATIONS_HINT",
        f"{MIGRATION_PREFIX}RESOURCE_POLICY",
    }
)
UNMAPPED_EXACT_ENTRYPOINTS = {
    "shannon-invariants.continuous-ksg-composition": (
        frozenset(),
        frozenset({f"{MIGRATION_PREFIX}compute_invariants"}),
    ),
    "software.runlog-schema-replay": (
        frozenset(
            {
                "pid_runlog::canonical_json_hash_v2",
                "pid_runlog::replay_events",
                "pid_runlog::validate_events",
            }
        ),
        frozenset(),
    ),
    "software.scientific-outcome-contract-foundation": (
        frozenset(
            {
                "pid_runlog::experimental::schema3::ScientificAnalysisPlan",
                "pid_runlog::experimental::schema3::ScientificMethodIdentity",
                "pid_runlog::experimental::schema3::ScientificOutcomeCoverage",
                "pid_runlog::experimental::schema3::ScientificOutcomeCoverageValidator",
                "pid_runlog::experimental::schema3::ScientificOutcomeReport",
                "pid_runlog::experimental::schema3::ScientificRegime",
                "pid_runlog::experimental::schema3::ScientificRequestLedger",
                "pid_runlog::experimental::schema3::ScientificValueSet",
                "pid_runlog::experimental::schema3::scientific_f64_matrix_identity_v1",
                "pid_runlog::experimental::schema3::scientific_split_membership_identity_v1",
                "pid_runlog::experimental::schema3::scientific_u64_matrix_identity_v1",
            }
        ),
        frozenset(),
    ),
    "validation.exp0": (frozenset({"exp0"}), frozenset()),
}
MARKER_RE = re.compile(r"Method catalog:\s*([a-z0-9]+(?:[.-][a-z0-9]+)*)")
EXTRA_SOURCE_MARKER_FILES = (
    "audit/tools/certified-sxpid/src/lib.rs",
    "scripts/check-foundational-sxpid-audit-pdf.sh",
    "scripts/check-two-source-sxpid-count-atom-bridge-pdf.sh",
)
SCIENTIFIC_CONTRACT_FIXTURE_SCHEMA = "pid-rs/scientific-method-test-fixtures"
SCIENTIFIC_CONTRACT_FIXTURE_SCHEMA_REVISION = 1
EXPECTED_SCIENTIFIC_CONTRACT_FIXTURES = {
    "continuous_pid2": {
        "catalog_id": "pid.continuous-pid2",
        "completeness": "complete",
        "estimand_regime": "conditional_continuous",
    },
    "mixed_support_gap": {
        "catalog_id": "unsupported.mixed-support-continuous-pid",
        "completeness": "not_applicable",
        "estimand_regime": "contract_defined",
    },
}
SCIENTIFIC_API_MATURITY_BY_STATUS = {
    "stable": "stable",
    "experimental": "experimental",
    "research-only": "research_only",
    "external-validation-only": "not_applicable",
    "unsupported": "not_applicable",
}
SCIENTIFIC_AVAILABILITY_BY_CODE = {
    "local": "local_implementation",
    "external": "external_reference_code",
    "none": "no_implementation",
}
LOCAL_STATUSES = {
    "stable": 0,
    "experimental": 1,
    "research-only": 2,
}
REQUIRED_UNSUPPORTED = {
    "unsupported.generic-knn-bootstrap-ci",
    "unsupported.hyperbolic-shared-exclusions-pid",
    "unsupported.mixed-support-continuous-pid",
}
ALLOWED_UNMAPPED = {
    "shannon-invariants.continuous-ksg-composition",
    MIGRATION_METHOD_ID,
    "software.runlog-schema-replay",
    "software.scientific-outcome-contract-foundation",
    "validation.csxpid-reference-code",
    "validation.exp0",
    "validation.idtxl-reference-code",
    "validation.sxpid-reference-code",
    *REQUIRED_UNSUPPORTED,
}
OVERCLAIM_PATTERNS = {
    "breakthrough": re.compile(r"\bbreakthrough\b", re.IGNORECASE),
    "first-ever": re.compile(r"\b(?:the first|first[- ]ever)\b", re.IGNORECASE),
    "invented": re.compile(r"\binvent(?:ed|ion)\b", re.IGNORECASE),
    "novel": re.compile(r"\bnovel(?:ty)?\b", re.IGNORECASE),
    "scientifically-new": re.compile(r"\bscientifically new\b", re.IGNORECASE),
    "state-of-the-art": re.compile(r"\bstate[- ]of[- ]the[- ]art\b", re.IGNORECASE),
    "unprecedented": re.compile(r"\bunprecedented\b", re.IGNORECASE),
}
SEMANTIC_AUTHORITY_BOUNDARY = (
    "This authority is a deterministic canonical-JSON change detector over every complete "
    "method row, its resolved linked-reference records, and four reviewed typed facts. It "
    "forces an explicit checker-root re-adjudication after any catalog-byte, authority-schema, "
    "typed-fact, alias-inventory, or semantic-prose change. It is not natural-language "
    "understanding, literature interpretation, truth inference, independent review, or evidence "
    "that a claim is scientifically valid; a coordinated authority rebase can still encode a "
    "wrong claim and therefore requires human review."
)
SEMANTIC_ALIAS_NORMALIZATION = (
    "unicode-nfkc-casefold-curated-latin-confusable-ascii-alnum-skeleton-v1"
)
SEMANTIC_ALIAS_BOUNDARY = (
    "The versioned alias diagnostic recognizes only its closed curated spellings after the "
    "declared Unicode/confusable normalization. It is not NLP, transliteration, authorship "
    "resolution, or a complete vocabulary. Exact payload freezing, not alias coverage, rejects "
    "vocabulary-free or otherwise unrecognized prose drift."
)
SEMANTIC_FACT_SEMANTICS = {
    "conditioning": (
        "External analysis-design, fitted-artifact, observation-model, or composition "
        "conditioning attached to the implemented row; this field does not inventory every "
        "conditional probability inside a defining formula."
    ),
    "data_domain": (
        "Scientific input-variable or record kind addressed by the row; a storage dtype or "
        "successful parse does not establish this domain."
    ),
    "estimand_family": (
        "Closed method-family identity for this row; shared names, dependencies, units, and "
        "bindings do not transfer estimands or theorems between families."
    ),
    "population_support": (
        "Declared, induced, inherited, diagnostic-only, or unavailable population-support "
        "regime; this field is not inferred from samples and is not a consistency or calibration "
        "claim."
    ),
}
SEMANTIC_FACT_FIELDS = frozenset(
    {"conditioning", "data_domain", "estimand_family", "population_support"}
)
SEMANTIC_CONDITIONING_VALUES = frozenset(
    {
        "caller-supplied-summary-terms",
        "declared-dependence-design",
        "declared-embedding-geometry",
        "declared-hypothesis-family",
        "declared-observation-model",
        "declared-preprocessing-gauge",
        "declared-resampling-or-null-design",
        "external-code-defined",
        "evaluation-sample-derived-transform",
        "evaluation-sample-fitted-artifact",
        "fixed-fitted-artifact",
        "fixed-transform-artifact",
        "inherits-composed-method-contracts",
        "not-applicable",
        "unconditioned",
    }
)
SEMANTIC_DATA_DOMAIN_VALUES = frozenset(
    {
        "continuous-to-finite-categorical",
        "euclidean-continuous",
        "finite-categorical",
        "lorentz-continuous",
        "method-results",
        "mixed-variable",
        "none",
        "numeric-matrix",
        "software-artifact",
    }
)
SEMANTIC_POPULATION_SUPPORT_VALUES = frozenset(
    {
        "declared-lorentz-manifold-research",
        "declared-observation-model",
        "empirical-finite-pmf",
        "external-code-scope",
        "finite-categorical-law",
        "finite-sample-diagnostic-only",
        "fixed-transform-induced-finite-pmf",
        "inherits-composed-method-contracts",
        "not-applicable",
        "regular-full-dimensional-continuous-required",
        "unsupported-no-estimator",
    }
)
SEMANTIC_ESTIMAND_FAMILY_VALUES = frozenset(
    {
        "bell-co-information",
        "bh-by-fdr-adjustment",
        "categorical-sxpid-validation",
        "certified-categorical-sxpid2-validation",
        "continuous-pid3-availability-diagnostic",
        "dependency-color-sxpid-concentration-validation",
        "distance-concentration-diagnostic",
        "distance-matrix-infrastructure",
        "ehrlich-continuous-pid2",
        "ehrlich-continuous-pid3",
        "ehrlich-continuous-shared-exclusions",
        "equal-width-quantization-transform",
        "exp0-validation-diagnostic",
        "external-validation-code",
        "finite-alphabet-plugin-validation",
        "fitted-quantized-mgw-shared-exclusions",
        "fitted-quantized-williams-beer-imin",
        "four-point-delta-diagnostic",
        "gaussian-noise-transform",
        "generic-analysis-pipeline",
        "generic-preprocessing-transform",
        "generic-resampling-procedure",
        "hyperbolic-geometry-diagnostic",
        "hyperbolic-geometry-utilities",
        "intrinsic-dimension-diagnostic",
        "jitter-transform",
        "ksg-config-infrastructure",
        "ksg-mutual-information",
        "ksg-sensitivity-diagnostic",
        "logistic-regression",
        "lorentz-ksg-mutual-information",
        "mgw-categorical-shared-exclusions",
        "moving-block-bootstrap",
        "o-information",
        "permutation-inference",
        "project-continuous-shared-exclusions-heuristic",
        "project-target-free-shannon-ratios",
        "python-binding",
        "report-contract-infrastructure",
        "resource-contract-infrastructure",
        "row-bootstrap-pipeline",
        "runlog-infrastructure",
        "same-sample-quantization-provenance",
        "same-sample-exact-significand-quantization",
        "same-sample-quantized-mgw-shared-exclusions",
        "same-sample-quantized-williams-beer-imin",
        "scientific-outcome-contract-infrastructure",
        "shannon-average-degrees",
        "shannon-entropy",
        "shannon-ksg-composition",
        "software-identity-infrastructure",
        "support-contract-infrastructure",
        "sxpid-interpretation-contract",
        "unsupported-general-mixed-support-shared-exclusions",
        "unsupported-generic-knn-bootstrap-ci",
        "unsupported-hyperbolic-shared-exclusions-pid",
        "williams-beer-imin",
    }
)
REQUIRED_SAME_SAMPLE_SEPARATION = {
    "pipelines.same-sample-quantization": {
        "category": "software",
        "depends_on": [],
        "python_entry_points": [],
        "release_scope_families": [
            "pid-core.experimental.pipelines.same-sample-quantization"
        ],
        "rust_entry_points": [
            "pid_core::experimental::pipelines::ExploratorySameSampleQuantizedResult",
            "pid_core::experimental::pipelines::SameSampleEqualWidthProvenance",
        ],
        "facts": {
            "conditioning": "not-applicable",
            "data_domain": "software-artifact",
            "estimand_family": "same-sample-quantization-provenance",
            "population_support": "not-applicable",
        },
    },
    "pid.same-sample-quantized-imin": {
        "category": "pipeline",
        "depends_on": [
            "pid.imin",
            "pipelines.same-sample-quantization",
            "quantization.same-sample-exact-significand",
        ],
        "python_entry_points": [
            "pid_core_rs.experimental.migration.compute_discrete_pid2",
            "pid_core_rs.experimental.migration.compute_discrete_pid3",
        ],
        "release_scope_families": [
            "pid-core.experimental.pipelines.same-sample-quantized-imin"
        ],
        "rust_entry_points": [
            "pid_core::experimental::pipelines::exploratory_same_sample_quantized_imin_pid2",
            "pid_core::experimental::pipelines::exploratory_same_sample_quantized_imin_pid3",
        ],
        "facts": {
            "conditioning": "evaluation-sample-derived-transform",
            "data_domain": "continuous-to-finite-categorical",
            "estimand_family": "same-sample-quantized-williams-beer-imin",
            "population_support": "empirical-finite-pmf",
        },
    },
    "quantization.same-sample-exact-significand": {
        "category": "preprocessing",
        "depends_on": [],
        "python_entry_points": [],
        "release_scope_families": [
            "pid-core.experimental.pipelines.same-sample-quantized-imin",
            "pid-core.experimental.pipelines.same-sample-quantized-sxpid",
        ],
        "rust_entry_points": [],
        "facts": {
            "conditioning": "evaluation-sample-derived-transform",
            "data_domain": "continuous-to-finite-categorical",
            "estimand_family": "same-sample-exact-significand-quantization",
            "population_support": "not-applicable",
        },
    },
    "shared-exclusions.same-sample-quantized": {
        "category": "pipeline",
        "depends_on": [
            "pipelines.same-sample-quantization",
            "quantization.same-sample-exact-significand",
            "shared-exclusions.categorical",
            "software.sxpid-interpretation-contract",
        ],
        "python_entry_points": [
            "pid_core_rs.experimental.migration.compute_quantized_sxpid2",
            "pid_core_rs.experimental.migration.compute_quantized_sxpid3",
            "pid_core_rs.experimental.migration.compute_quantized_sxpid_n",
        ],
        "release_scope_families": [
            "pid-core.experimental.pipelines.same-sample-quantized-sxpid"
        ],
        "rust_entry_points": [
            "pid_core::experimental::pipelines::exploratory_same_sample_quantized_sxpid2",
            "pid_core::experimental::pipelines::exploratory_same_sample_quantized_sxpid3",
            "pid_core::experimental::pipelines::exploratory_same_sample_quantized_sxpid_n",
        ],
        "facts": {
            "conditioning": "evaluation-sample-derived-transform",
            "data_domain": "continuous-to-finite-categorical",
            "estimand_family": "same-sample-quantized-mgw-shared-exclusions",
            "population_support": "empirical-finite-pmf",
        },
    },
}
SEMANTIC_ALIAS_ENTRIES = (
    {
        "family": "ehrlich-continuous-shared-exclusions",
        "spellings": ["Ehrlich"],
    },
    {
        "family": "ksg-mutual-information",
        "spellings": ["KSG", "Kraskov", "Kraskov Stögbauer Grassberger"],
    },
    {
        "family": "mgw-categorical-shared-exclusions",
        "spellings": ["M.G.W.", "Makkeh", "Makkeh-Gutknecht-Wibral"],
    },
    {
        "family": "schick-poland-general-shared-exclusions",
        "spellings": ["Schick-Poland"],
    },
    {
        "family": "williams-beer-imin",
        "spellings": ["I_min", "Williams-Beer"],
    },
)
SEMANTIC_CONFUSABLES = str.maketrans(
    {
        # Curated Cyrillic and Greek glyphs commonly confusable with the Latin aliases above.
        "а": "a",
        "в": "b",
        "е": "e",
        "і": "i",
        "ј": "j",
        "к": "k",
        "м": "m",
        "н": "h",
        "о": "o",
        "р": "p",
        "с": "c",
        "т": "t",
        "у": "y",
        "х": "x",
        "α": "a",
        "β": "b",
        "ε": "e",
        "ι": "i",
        "κ": "k",
        "ν": "v",
        "ο": "o",
        "ρ": "p",
        "τ": "t",
        "υ": "y",
        "χ": "x",
    }
)


class CatalogError(RuntimeError):
    """The method catalog, its source markers, or its rendered view disagree."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def load_json(path: Path, *, canonical: bool = False) -> Any:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (OSError, json.JSONDecodeError) as error:
        raise CatalogError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if raw != expected:
            raise CatalogError(
                f"{path} is not canonical sorted two-space JSON with one final LF"
            )
    return value


def raw_sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as error:
        raise CatalogError(f"cannot hash {path}: {error}") from error


def canonical_json_sha256(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise CatalogError(
            f"semantic authority contains non-canonical JSON data: {error}"
        ) from error
    return hashlib.sha256(encoded).hexdigest()


def semantic_claim_texts(method: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        ("title", method["title"]),
        ("summary", method["summary"]),
        ("new_in_pid_rs", method["new_in_pid_rs"]),
        *[
            (f"constraints[{index}]", text)
            for index, text in enumerate(method["constraints"])
        ],
        ("validation.scope", method["validation"]["scope"]),
        ("validation.limitations", method["validation"]["limitations"]),
        *[
            (f"reference_links[{index}].locator", link["locator"])
            for index, link in enumerate(method["reference_links"])
        ],
    ]


def semantic_alias_skeleton(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    mapped = normalized.translate(SEMANTIC_CONFUSABLES)
    return "".join(
        character for character in mapped if character.isascii() and character.isalnum()
    )


def detected_semantic_alias_families(method: dict[str, Any]) -> list[str]:
    detected: set[str] = set()
    aliases = [
        (entry["family"], semantic_alias_skeleton(spelling))
        for entry in SEMANTIC_ALIAS_ENTRIES
        for spelling in entry["spellings"]
    ]
    for _field, text in semantic_claim_texts(method):
        skeleton = semantic_alias_skeleton(text)
        for family, alias in aliases:
            if alias in skeleton:
                detected.add(family)
    return sorted(detected)


def semantic_method_payload(
    method: dict[str, Any],
    record: dict[str, Any],
    references: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "facts": record["facts"],
        "method": method,
        "observed_alias_families": record["observed_alias_families"],
        "resolved_linked_references": [
            references[link["reference_id"]] for link in method["reference_links"]
        ],
    }


def semantic_authority_root_sha256(authority: dict[str, Any]) -> str:
    projection = {
        key: value for key, value in authority.items() if key != "ordered_root_sha256"
    }
    return canonical_json_sha256(projection)


def check_semantic_alias_diagnostic(
    method: dict[str, Any], record: dict[str, Any]
) -> None:
    method_id = method["id"]
    observed = record["observed_alias_families"]
    if observed != sorted(observed) or len(observed) != len(set(observed)):
        raise CatalogError(
            f"{method_id}: semantic alias families must be sorted and unique"
        )
    known_families = {entry["family"] for entry in SEMANTIC_ALIAS_ENTRIES}
    unknown = sorted(set(observed) - known_families)
    if unknown:
        raise CatalogError(
            f"{method_id}: semantic alias diagnostic names unknown families: "
            + ", ".join(unknown)
        )
    detected = detected_semantic_alias_families(method)
    if observed != detected:
        raise CatalogError(
            f"{method_id}: semantic alias diagnostic revision "
            f"{SEMANTIC_ALIAS_DIAGNOSTIC_REVISION} mismatch; "
            f"reviewed={observed!r}, detected={detected!r}"
        )


def check_required_same_sample_separation(
    methods: dict[str, dict[str, Any]],
    records: list[dict[str, Any]],
) -> None:
    """Keep provenance software, I_min, and MGW SxPID as distinct authorities."""

    records_by_id = {record["method_id"]: record for record in records}
    for method_id, expected in REQUIRED_SAME_SAMPLE_SEPARATION.items():
        method = methods.get(method_id)
        record = records_by_id.get(method_id)
        if method is None or record is None:
            raise CatalogError(
                f"{method_id}: required same-sample semantic identity is missing"
            )
        for field in (
            "category",
            "depends_on",
            "python_entry_points",
            "release_scope_families",
            "rust_entry_points",
        ):
            if method[field] != expected[field]:
                raise CatalogError(
                    f"{method_id}: same-sample semantic separation drifted for {field}; "
                    f"expected={expected[field]!r}, actual={method[field]!r}"
                )
        if record["facts"] != expected["facts"]:
            raise CatalogError(
                f"{method_id}: same-sample semantic separation drifted for facts; "
                f"expected={expected['facts']!r}, actual={record['facts']!r}"
            )


def check_semantic_authority(
    *,
    catalog: dict[str, Any],
    catalog_path: Path,
    authority: dict[str, Any],
    authority_schema_path: Path,
    methods: dict[str, dict[str, Any]],
    references: dict[str, dict[str, Any]],
) -> None:
    if (
        authority["schema"] != SEMANTIC_AUTHORITY_SCHEMA
        or authority["schema_revision"] != SEMANTIC_AUTHORITY_SCHEMA_REVISION
    ):
        raise CatalogError("unsupported method-catalog semantic authority identity")
    if (
        authority["catalog_schema"] != SCHEMA
        or authority["catalog_schema_revision"] != SCHEMA_REVISION
    ):
        raise CatalogError("semantic authority targets the wrong method-catalog schema")
    if authority["authority_boundary"] != SEMANTIC_AUTHORITY_BOUNDARY:
        raise CatalogError("semantic authority non-inference boundary drifted")
    if authority["fact_semantics"] != SEMANTIC_FACT_SEMANTICS:
        raise CatalogError("semantic authority typed-fact semantics drifted")

    alias_diagnostic = authority["alias_diagnostic"]
    expected_alias_diagnostic = {
        "boundary": SEMANTIC_ALIAS_BOUNDARY,
        "entries": list(SEMANTIC_ALIAS_ENTRIES),
        "normalization": SEMANTIC_ALIAS_NORMALIZATION,
        "revision": SEMANTIC_ALIAS_DIAGNOSTIC_REVISION,
    }
    if alias_diagnostic != expected_alias_diagnostic:
        raise CatalogError("semantic alias/confusable diagnostic registry drifted")

    actual_authority_schema_sha256 = raw_sha256(authority_schema_path)
    if authority["authority_schema_sha256"] != actual_authority_schema_sha256:
        raise CatalogError(
            "semantic authority schema SHA-256 mismatch: "
            f"reviewed={authority['authority_schema_sha256']}, "
            f"actual={actual_authority_schema_sha256}"
        )
    actual_catalog_sha256 = raw_sha256(catalog_path)
    if authority["catalog_sha256"] != actual_catalog_sha256:
        raise CatalogError(
            "semantic authority catalog SHA-256 mismatch: "
            f"reviewed={authority['catalog_sha256']}, actual={actual_catalog_sha256}"
        )
    actual_reference_sha256 = canonical_json_sha256(catalog["references"])
    if authority["reference_registry_sha256"] != actual_reference_sha256:
        raise CatalogError(
            "semantic authority reference-registry SHA-256 mismatch: "
            f"reviewed={authority['reference_registry_sha256']}, "
            f"actual={actual_reference_sha256}"
        )

    records = authority["method_payloads"]
    record_ids = [record["method_id"] for record in records]
    expected_ids = list(methods)
    if record_ids != expected_ids:
        raise CatalogError(
            "semantic authority method payloads must be a complete catalog-ordered inventory; "
            f"expected={expected_ids!r}, actual={record_ids!r}"
        )
    check_required_same_sample_separation(methods, records)
    for record in records:
        method_id = record["method_id"]
        facts = record["facts"]
        if set(facts) != SEMANTIC_FACT_FIELDS:
            raise CatalogError(
                f"{method_id}: semantic facts must have exactly "
                f"{sorted(SEMANTIC_FACT_FIELDS)!r}"
            )
        fact_policies = {
            "conditioning": SEMANTIC_CONDITIONING_VALUES,
            "data_domain": SEMANTIC_DATA_DOMAIN_VALUES,
            "estimand_family": SEMANTIC_ESTIMAND_FAMILY_VALUES,
            "population_support": SEMANTIC_POPULATION_SUPPORT_VALUES,
        }
        for field, allowed in fact_policies.items():
            if facts[field] not in allowed:
                raise CatalogError(
                    f"{method_id}: unsupported semantic fact {field}={facts[field]!r}"
                )
        method = methods[method_id]
        check_semantic_alias_diagnostic(method, record)
        actual_payload_sha256 = canonical_json_sha256(
            semantic_method_payload(method, record, references)
        )
        if record["payload_sha256"] != actual_payload_sha256:
            raise CatalogError(
                f"{method_id}: reviewed semantic payload SHA-256 mismatch; "
                f"reviewed={record['payload_sha256']}, actual={actual_payload_sha256}"
            )

    actual_root_sha256 = semantic_authority_root_sha256(authority)
    if authority["ordered_root_sha256"] != actual_root_sha256:
        raise CatalogError(
            "semantic authority ordered-root SHA-256 mismatch: "
            f"stored={authority['ordered_root_sha256']}, actual={actual_root_sha256}"
        )
    if actual_root_sha256 != EXPECTED_SEMANTIC_AUTHORITY_ROOT_SHA256:
        raise CatalogError(
            "semantic authority requires explicit checker-root re-adjudication: "
            f"expected={EXPECTED_SEMANTIC_AUTHORITY_ROOT_SHA256}, "
            f"actual={actual_root_sha256}"
        )


def python_surface_name(entry_point: str) -> str:
    """Return the release-scope spelling for a fully qualified Python entry point."""
    prefix = "pid_core_rs."
    return entry_point[len(prefix) :] if entry_point.startswith(prefix) else entry_point


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise CatalogError(
            f"{label}: path must be a non-empty repository-relative string"
        )
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise CatalogError(f"{label}: unsafe repository path {relative!r}")
    candidate = root / candidate_relative
    current = root
    for component in candidate_relative.parts:
        current = current / component
        if current.is_symlink():
            raise CatalogError(f"{label}: symlink paths are forbidden: {relative!r}")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise CatalogError(
            f"{label}: file is missing or escapes the repository: {relative!r}"
        ) from error
    if not resolved.is_file():
        raise CatalogError(f"{label}: expected a regular file: {relative!r}")
    return resolved


def registered_migration_surface(root: Path) -> set[str]:
    """Extract the exact callable, class, and policy-attribute compatibility surface."""
    path = root / "crates/pid-python/src/lib.rs"
    source = path.read_text(encoding="utf-8")
    start = source.find("pub(crate) fn register_legacy")
    if start < 0:
        raise CatalogError(f"{path}: register_legacy is missing")
    terminator = "\n    Ok(())\n}"
    end = source.find(terminator, start)
    if end < 0:
        raise CatalogError(f"{path}: register_legacy terminator is missing")
    body = source[start : end + len(terminator)]

    names = set(re.findall(r'm\.add\(\s*"([A-Z][A-Z0-9_]*)"', body))
    names.update(re.findall(r"wrap_pyfunction!\((\w+), m\)", body))

    class_names = {
        rust_name: python_name
        for python_name, rust_name in re.findall(
            r'#\[pyclass\(name\s*=\s*"([^"]+)"[^\]]*\)\]\s*struct\s+(\w+)',
            source,
        )
    }
    for rust_name in re.findall(r"m\.add_class::<(\w+)>\(\)", body):
        try:
            names.add(class_names[rust_name])
        except KeyError as error:
            raise CatalogError(
                f"{path}: cannot determine Python name for registered class {rust_name}"
            ) from error

    return {MIGRATION_PREFIX + name for name in names}


def unique_index(
    items: list[dict[str, Any]], *, label: str, require_sorted: bool = True
) -> dict[str, dict[str, Any]]:
    ids = [item["id"] for item in items]
    duplicates = sorted(item for item, count in Counter(ids).items() if count != 1)
    if duplicates:
        raise CatalogError(f"duplicate {label} IDs: {', '.join(duplicates)}")
    if require_sorted and ids != sorted(ids):
        raise CatalogError(f"{label} entries must be sorted by id")
    return {item["id"]: item for item in items}


def cargo_features(path: Path) -> set[str]:
    try:
        manifest = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise CatalogError(
            f"cannot read Cargo features from {path}: {error}"
        ) from error
    features = manifest.get("features")
    if not isinstance(features, dict):
        raise CatalogError(f"{path}: [features] table is missing")
    return set(features)


def check_dag(methods: dict[str, dict[str, Any]]) -> None:
    state: dict[str, int] = {}
    trail: list[str] = []

    def visit(method_id: str) -> None:
        status = state.get(method_id, 0)
        if status == 2:
            return
        if status == 1:
            cycle_start = trail.index(method_id)
            cycle = trail[cycle_start:] + [method_id]
            raise CatalogError(f"depends_on cycle: {' -> '.join(cycle)}")
        state[method_id] = 1
        trail.append(method_id)
        method = methods[method_id]
        for dependency in method["depends_on"]:
            if dependency not in methods:
                raise CatalogError(f"{method_id}: unknown depends_on ID {dependency!r}")
            visit(dependency)
            method_status = method["implementation_status"]
            dependency_status = methods[dependency]["implementation_status"]
            if method_status in LOCAL_STATUSES:
                if dependency_status not in LOCAL_STATUSES:
                    raise CatalogError(
                        f"{method_id}: supported method cannot depend on "
                        f"{dependency_status} method {dependency}"
                    )
                if method_status == "stable" and dependency_status != "stable":
                    raise CatalogError(
                        f"{method_id}: stable method depends on non-stable "
                        f"{dependency_status} method {dependency}"
                    )
                if (
                    method_status != "stable"
                    and LOCAL_STATUSES[dependency_status]
                    > LOCAL_STATUSES[method_status]
                ):
                    boundary = " ".join(method["constraints"]).casefold()
                    if dependency.casefold() not in boundary:
                        raise CatalogError(
                            f"{method_id}: stricter-status dependency boundary for "
                            f"{dependency} ({dependency_status}) is not named in constraints"
                        )
        trail.pop()
        state[method_id] = 2

    for method_id in methods:
        visit(method_id)


def check_method_rules(
    root: Path,
    method: dict[str, Any],
    references: dict[str, dict[str, Any]],
    families: dict[str, dict[str, Any]],
    features: set[str],
    migration_surface: set[str],
) -> None:
    method_id = method["id"]
    status = method["implementation_status"]
    availability = method["code_availability"]
    origin = method["implementation_origin"]
    mapped_families = method["release_scope_families"]
    method_features = method["cargo_features"]

    claim_texts = {
        "title": method["title"],
        "summary": method["summary"],
        "new_in_pid_rs": method["new_in_pid_rs"],
        "validation.scope": method["validation"]["scope"],
        "validation.limitations": method["validation"]["limitations"],
        **{
            f"constraints[{index}]": text
            for index, text in enumerate(method["constraints"])
        },
        **{
            f"reference_links[{index}].locator": link["locator"]
            for index, link in enumerate(method["reference_links"])
        },
    }
    for field, text in claim_texts.items():
        for label, pattern in OVERCLAIM_PATTERNS.items():
            if pattern.search(text):
                raise CatalogError(
                    f"{method_id}.{field}: prohibited overclaim wording: {label}"
                )

    if method["scientific_novelty_claim"] != "none":
        raise CatalogError(f"{method_id}: scientific_novelty_claim must be 'none'")

    if len(method["constraints"]) != len(set(method["constraints"])):
        raise CatalogError(f"{method_id}: duplicate constraints")

    for link in method["reference_links"]:
        reference_id = link["reference_id"]
        if reference_id not in references:
            raise CatalogError(f"{method_id}: unknown reference ID {reference_id!r}")

    roles = {link["role"] for link in method["reference_links"]}
    definition_origin = method["definition_origin"]
    if definition_origin == "paper-defined" and not roles.intersection(
        {"defining-paper", "estimator-paper"}
    ):
        raise CatalogError(
            f"{method_id}: paper-defined method lacks a primary paper link"
        )
    if definition_origin == "paper-derived" and not roles.intersection(
        {
            "defining-paper",
            "estimator-paper",
            "implementation-basis",
            "methodological-background",
        }
    ):
        raise CatalogError(
            f"{method_id}: paper-derived method lacks a literature basis"
        )

    unknown_features = sorted(set(method_features) - features)
    if unknown_features:
        raise CatalogError(
            f"{method_id}: unknown pid-core Cargo features: {', '.join(unknown_features)}"
        )
    unknown_families = sorted(set(mapped_families) - set(families))
    if unknown_families:
        raise CatalogError(
            f"{method_id}: unknown release-scope families: {', '.join(unknown_families)}"
        )
    if not mapped_families and method_id not in ALLOWED_UNMAPPED:
        raise CatalogError(
            f"{method_id}: local method lacks a release-scope family mapping"
        )

    mapped_features = {
        families[family_id]["cargo_feature"]
        for family_id in mapped_families
        if families[family_id]["cargo_feature"] is not None
    }
    if mapped_families and set(method_features) != mapped_features:
        raise CatalogError(
            f"{method_id}: Cargo features {method_features!r} do not exactly match "
            f"mapped release-scope gates {sorted(mapped_features)!r}"
        )
    for family_id in mapped_families:
        family_status = families[family_id]["software_stability"]
        if family_status != status:
            raise CatalogError(
                f"{method_id}: status {status!r} disagrees with {family_id} "
                f"status {family_status!r}"
            )
    for entry_point in method["python_entry_points"]:
        if (
            entry_point.startswith(MIGRATION_PREFIX)
            and entry_point not in migration_surface
        ):
            raise CatalogError(
                f"{method_id}: Python migration entry point {entry_point!r} is not registered"
            )
        if (
            entry_point.startswith(MIGRATION_PREFIX)
            and method_id != MIGRATION_METHOD_ID
            and method_id
            not in MIGRATION_ENTRYPOINT_OWNERS.get(entry_point, frozenset())
        ):
            raise CatalogError(
                f"{method_id}: Python migration entry point {entry_point!r} is not owned "
                "by this method"
            )
    if mapped_families:
        python_symbols = {
            symbol
            for family_id in mapped_families
            for symbol in families[family_id]["python_exposure"]
        }
        for entry_point in method["rust_entry_points"]:
            symbol = entry_point.rsplit("::", 1)[-1]
            matching_families = [
                families[family_id]
                for family_id in mapped_families
                if symbol in families[family_id]["symbols"]
            ]
            if not matching_families:
                raise CatalogError(
                    f"{method_id}: Rust entry point {entry_point!r} is absent from "
                    "the mapped release-scope families"
                )
            expected_paths = {
                f"{family['rust_exposure']}::{symbol}" for family in matching_families
            }
            if entry_point not in expected_paths:
                raise CatalogError(
                    f"{method_id}: Rust entry point {entry_point!r} has the wrong public "
                    f"namespace; expected one of {sorted(expected_paths)!r}"
                )
        for entry_point in method["python_entry_points"]:
            if entry_point.startswith(MIGRATION_PREFIX):
                continue
            symbol = python_surface_name(entry_point)
            if symbol not in python_symbols:
                raise CatalogError(
                    f"{method_id}: Python entry point {entry_point!r} is absent from "
                    "the mapped release-scope families"
                )
    elif method_id in UNMAPPED_EXACT_ENTRYPOINTS:
        expected_rust, expected_python = UNMAPPED_EXACT_ENTRYPOINTS[method_id]
        actual_rust = frozenset(method["rust_entry_points"])
        actual_python = frozenset(method["python_entry_points"])
        if actual_rust != expected_rust or actual_python != expected_python:
            raise CatalogError(
                f"{method_id}: unmapped entry-point policy disagrees; "
                f"expected_rust={sorted(expected_rust)!r}, "
                f"actual_rust={sorted(actual_rust)!r}, "
                f"expected_python={sorted(expected_python)!r}, "
                f"actual_python={sorted(actual_python)!r}"
            )

    for index, path in enumerate(method["source_files"]):
        safe_repo_file(root, path, label=f"{method_id}.source_files[{index}]")
    for index, path in enumerate(method["source_marker_files"]):
        safe_repo_file(root, path, label=f"{method_id}.source_marker_files[{index}]")
    for index, path in enumerate(method["validation"]["evidence_paths"]):
        safe_repo_file(
            root, path, label=f"{method_id}.validation.evidence_paths[{index}]"
        )

    external_code = method["external_code"]
    evidence = method["validation"]["evidence_paths"]
    level = method["validation"]["level"]
    if origin == "external":
        if availability != "external" or status != "external-validation-only":
            raise CatalogError(
                f"{method_id}: external implementation must be external-validation-only"
            )
        if external_code is None:
            raise CatalogError(
                f"{method_id}: external implementation lacks an immutable pin"
            )
        if mapped_families or method_features or method["source_files"]:
            raise CatalogError(
                f"{method_id}: external validation code cannot claim local families/features/source"
            )
        if method["rust_entry_points"] or method["python_entry_points"]:
            raise CatalogError(
                f"{method_id}: external validation code has local entry points"
            )
        if level != "reference-fixture" or not evidence:
            raise CatalogError(
                f"{method_id}: external validation code needs reference-fixture evidence"
            )
    elif external_code is not None:
        raise CatalogError(
            f"{method_id}: external_code is only valid for external origin"
        )

    if origin == "not-implemented":
        if (
            availability != "none"
            or status != "unsupported"
            or method["category"] != "unsupported"
        ):
            raise CatalogError(
                f"{method_id}: not-implemented entry must be unsupported"
            )
        if (
            mapped_families
            or method_features
            or method["source_files"]
            or method["rust_entry_points"]
            or method["python_entry_points"]
            or method["depends_on"]
            or evidence
            or level != "not-validated"
        ):
            raise CatalogError(
                f"{method_id}: unsupported entry claims code, dependencies, or validation"
            )
    elif availability == "local":
        if (
            origin not in {"binding", "local-implementation"}
            or status not in LOCAL_STATUSES
        ):
            raise CatalogError(
                f"{method_id}: invalid local implementation origin/status"
            )
        if not method["source_files"]:
            raise CatalogError(f"{method_id}: local code lacks source_files")
        if not evidence:
            raise CatalogError(
                f"{method_id}: local code lacks bounded validation evidence"
            )
        if level == "not-validated":
            raise CatalogError(f"{method_id}: local code cannot use not-validated")
    elif origin != "external":
        raise CatalogError(
            f"{method_id}: inconsistent code availability and implementation origin"
        )

    if status == "external-validation-only" and "validation-code" not in roles:
        raise CatalogError(
            f"{method_id}: external validation entry lacks validation-code role"
        )
    if status == "unsupported" and method_id not in REQUIRED_UNSUPPORTED:
        raise CatalogError(f"{method_id}: unexpected unsupported catalog entry")


def check_migration_ownership(
    methods: dict[str, dict[str, Any]],
    migration_surface: set[str],
) -> None:
    classified_surface = set(MIGRATION_ENTRYPOINT_OWNERS) | set(
        MIGRATION_POLICY_ATTRIBUTES
    )
    unclassified = sorted(migration_surface - classified_surface)
    if unclassified:
        raise CatalogError(
            "registered migration entries lack owner or policy classification: "
            + ", ".join(unclassified)
        )
    stale_classifications = sorted(classified_surface - migration_surface)
    if stale_classifications:
        raise CatalogError(
            "migration owner/policy classifications name unregistered entries: "
            + ", ".join(stale_classifications)
        )

    for entry_point, expected_owners in MIGRATION_ENTRYPOINT_OWNERS.items():
        unknown_owners = sorted(expected_owners - set(methods))
        if unknown_owners:
            raise CatalogError(
                f"{entry_point}: migration owner map names unknown methods: "
                + ", ".join(unknown_owners)
            )
        actual_owners = {
            method["id"]
            for method in methods.values()
            if method["id"] != MIGRATION_METHOD_ID
            and entry_point in method["python_entry_points"]
        }
        if actual_owners != expected_owners:
            raise CatalogError(
                f"{entry_point}: migration owner claims disagree; "
                f"expected={sorted(expected_owners)!r}, actual={sorted(actual_owners)!r}"
            )


def check_markers(
    root: Path,
    methods: dict[str, dict[str, Any]],
) -> None:
    occurrences: dict[str, list[str]] = defaultdict(list)
    sources = list((root / "crates").rglob("*.rs"))
    sources.extend(
        safe_repo_file(root, relative, label="extra source marker file")
        for relative in EXTRA_SOURCE_MARKER_FILES
    )
    for source in sorted(sources):
        relative = source.relative_to(root).as_posix()
        text = source.read_text(encoding="utf-8")
        for match in MARKER_RE.finditer(text):
            occurrences[match.group(1)].append(relative)

    unknown = sorted(set(occurrences) - set(methods))
    if unknown:
        raise CatalogError(
            f"source markers reference unknown catalog IDs: {', '.join(unknown)}"
        )
    missing = sorted(set(methods) - set(occurrences))
    if missing:
        raise CatalogError(f"catalog IDs lack source markers: {', '.join(missing)}")
    for method_id, method in methods.items():
        actual = occurrences[method_id]
        if len(actual) != 1:
            raise CatalogError(
                f"{method_id}: expected exactly one source marker, found {len(actual)}"
            )
        declared = set(method["source_marker_files"])
        if actual[0] not in declared:
            raise CatalogError(
                f"{method_id}: marker is in {actual[0]!r}, not declared marker files "
                f"{sorted(declared)!r}"
            )


def check_scientific_contract_fixtures(
    fixture_path: Path,
    methods: dict[str, dict[str, Any]],
) -> None:
    manifest = load_json(fixture_path, canonical=True)
    expected_top_fields = {"fixtures", "schema", "schema_revision"}
    if not isinstance(manifest, dict) or set(manifest) != expected_top_fields:
        raise CatalogError(
            "scientific-contract fixture manifest must have exactly "
            f"{sorted(expected_top_fields)!r}"
        )
    if (
        not isinstance(manifest["schema"], str)
        or type(manifest["schema_revision"]) is not int
        or manifest["schema"] != SCIENTIFIC_CONTRACT_FIXTURE_SCHEMA
        or manifest["schema_revision"] != SCIENTIFIC_CONTRACT_FIXTURE_SCHEMA_REVISION
    ):
        raise CatalogError("unsupported scientific-contract fixture schema identity")
    fixtures = manifest["fixtures"]
    if not isinstance(fixtures, list) or not all(
        isinstance(fixture, dict) for fixture in fixtures
    ):
        raise CatalogError("scientific-contract fixtures must be an object array")
    expected_fixture_fields = {
        "api_maturity",
        "availability",
        "catalog_id",
        "completeness",
        "estimand_regime",
        "fixture_id",
        "origin",
    }
    for index, fixture in enumerate(fixtures):
        if set(fixture) != expected_fixture_fields:
            raise CatalogError(
                f"scientific-contract fixture {index} must have exactly "
                f"{sorted(expected_fixture_fields)!r}"
            )
        if not all(isinstance(value, str) and value for value in fixture.values()):
            raise CatalogError(
                f"scientific-contract fixture {index} fields must be non-empty strings"
            )
    fixture_ids = [fixture["fixture_id"] for fixture in fixtures]
    if fixture_ids != sorted(fixture_ids):
        raise CatalogError("scientific-contract fixtures are not sorted by fixture_id")
    duplicate_ids = sorted(
        fixture_id for fixture_id, count in Counter(fixture_ids).items() if count != 1
    )
    if duplicate_ids:
        raise CatalogError(
            "duplicate scientific-contract fixture IDs: " + ", ".join(duplicate_ids)
        )
    indexed = {fixture["fixture_id"]: fixture for fixture in fixtures}
    if set(indexed) != set(EXPECTED_SCIENTIFIC_CONTRACT_FIXTURES):
        raise CatalogError(
            "scientific-contract fixture ID set mismatch: "
            f"expected={sorted(EXPECTED_SCIENTIFIC_CONTRACT_FIXTURES)!r}, "
            f"actual={sorted(indexed)!r}"
        )
    for fixture_id, expected in EXPECTED_SCIENTIFIC_CONTRACT_FIXTURES.items():
        fixture = indexed[fixture_id]
        for field, expected_value in expected.items():
            if fixture[field] != expected_value:
                raise CatalogError(
                    f"scientific-contract fixture {fixture_id} {field} "
                    f"{fixture[field]!r} disagrees with expected {expected_value!r}"
                )
        method_id = fixture["catalog_id"]
        method = methods.get(method_id)
        if method is None:
            raise CatalogError(
                f"scientific-contract fixture {fixture_id} names unknown method "
                f"{method_id!r}"
            )
        expected_origin = method["definition_origin"].replace("-", "_")
        if fixture["origin"] != expected_origin:
            raise CatalogError(
                f"scientific-contract fixture {fixture_id} origin "
                f"{fixture['origin']!r} "
                f"disagrees with catalog origin {expected_origin!r}"
            )
        expected_maturity = SCIENTIFIC_API_MATURITY_BY_STATUS[
            method["implementation_status"]
        ]
        if fixture["api_maturity"] != expected_maturity:
            raise CatalogError(
                f"scientific-contract fixture {fixture_id} API maturity "
                f"{fixture['api_maturity']!r} disagrees with catalog status "
                f"{method['implementation_status']!r}"
            )
        expected_availability = SCIENTIFIC_AVAILABILITY_BY_CODE[
            method["code_availability"]
        ]
        if fixture["availability"] != expected_availability:
            raise CatalogError(
                f"scientific-contract fixture {fixture_id} availability "
                f"{fixture['availability']!r} disagrees with catalog code availability "
                f"{method['code_availability']!r}"
            )


def markdown_escape(value: str) -> str:
    return value.replace("|", r"\|").replace("\n", " ")


def code_list(values: list[str], *, empty: str = "—") -> str:
    if not values:
        return empty
    return ", ".join(f"`{value}`" for value in values)


def reference_label(reference: dict[str, Any]) -> str:
    authors = reference["authors"]
    lead = authors[0] if len(authors) == 1 else f"{authors[0]} et al."
    return f"{lead} ({reference['year']})"


def render_markdown(catalog: dict[str, Any], semantic_authority: dict[str, Any]) -> str:
    references = {item["id"]: item for item in catalog["references"]}
    semantic_records = {
        item["method_id"]: item for item in semantic_authority["method_payloads"]
    }
    lines = [
        "# Method provenance and code availability",
        "",
        "<!-- Generated by scripts/check-method-catalog.py; edit method-catalog.json instead. -->",
        "",
        catalog["scientific_claim_boundary"],
        "",
        "## How to read the catalog",
        "",
        "- **Paper-defined** means the mathematical quantity or estimator is taken directly from a cited primary source.",
        "- **Paper-derived** means the implementation composes or adapts published components; the exact composition is not asserted to be a published estimator.",
        "- **Project-defined** means a local diagnostic, workflow, API contract, adapter, or software facility.",
        "- **Implementation origin** is `local-implementation` for code written in this repository, `binding` for a language wrapper, `external` for pinned validation-only code, and `not-implemented` for an explicit negative capability.",
        "- For software references, the displayed year is the year of the pinned validation revision, not a claim about project inception.",
        f"- **`depends_on` semantics:** {catalog['dependency_semantics']}",
        f"- **Rust entry-point semantics:** {catalog['rust_entry_point_semantics']}",
        f"- **Python entry-point semantics:** {catalog['python_entry_point_semantics']}",
        "- **New in pid-rs** describes repository engineering and packaging only. Every row records `scientific_novelty_claim = none`.",
        "- Validation levels are bounded evidence labels. Reference agreement, tests, and formal checks do not establish universal statistical or application validity.",
        f"- **Frozen semantic authority:** {semantic_authority['authority_boundary']}",
        f"- **Alias diagnostic boundary:** {semantic_authority['alias_diagnostic']['boundary']}",
        "",
        "## Frozen semantic authority",
        "",
        f"- **Authority schema:** `{semantic_authority['schema']}` revision `{semantic_authority['schema_revision']}`.",
        f"- **Ordered root SHA-256:** `{semantic_authority['ordered_root_sha256']}`.",
        f"- **Catalog SHA-256:** `{semantic_authority['catalog_sha256']}`.",
        f"- **Reference-registry SHA-256:** `{semantic_authority['reference_registry_sha256']}`.",
        f"- **Alias/confusable diagnostic:** revision `{semantic_authority['alias_diagnostic']['revision']}`; normalization `{semantic_authority['alias_diagnostic']['normalization']}`.",
        f"- **`data_domain` semantics:** {semantic_authority['fact_semantics']['data_domain']}",
        f"- **`population_support` semantics:** {semantic_authority['fact_semantics']['population_support']}",
        f"- **`conditioning` semantics:** {semantic_authority['fact_semantics']['conditioning']}",
        f"- **`estimand_family` semantics:** {semantic_authority['fact_semantics']['estimand_family']}",
        "",
        "## Implemented methods and software",
        "",
        "| Method | Origin / status | Code availability | Paper and reference availability | New in pid-rs | Bounded validation |",
        "|---|---|---|---|---|---|",
    ]
    for method in catalog["methods"]:
        if method["implementation_status"] == "unsupported":
            continue
        links = []
        for link in method["reference_links"]:
            reference = references[link["reference_id"]]
            links.append(
                f"[{reference_label(reference)}]({reference['url']}) ({link['role']})"
            )
        reference_text = (
            "; ".join(links) if links else "No dedicated paper; project-defined."
        )
        code_surface = method["rust_entry_points"] + method["python_entry_points"]
        code_text = code_list(code_surface)
        if method["external_code"] is not None:
            external = method["external_code"]
            code_text = (
                f"[upstream]({external['upstream_url']}) at "
                f"`{external['pinned_ref']}`; `{external['license']}`"
            )
        status_text = (
            f"definition {method['definition_origin']}; "
            f"implementation {method['implementation_origin']}; "
            f"status {method['implementation_status']}; "
            f"feature {code_list(method['cargo_features'])}"
        )
        validation = (
            f"{method['validation']['level']}; "
            f"{code_list(method['validation']['evidence_paths'])}"
        )
        lines.append(
            "| "
            + " | ".join(
                markdown_escape(value)
                for value in [
                    f"`{method['id']}` — {method['title']}",
                    status_text,
                    code_text,
                    reference_text,
                    method["new_in_pid_rs"],
                    validation,
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Explicitly unsupported methods",
            "",
            "These rows are negative capability declarations. They do not indicate a roadmap or an implicit endorsement.",
            "",
            "| Method | Why it is unsupported | Relevant context |",
            "|---|---|---|",
        ]
    )
    for method in catalog["methods"]:
        if method["implementation_status"] != "unsupported":
            continue
        links = []
        for link in method["reference_links"]:
            reference = references[link["reference_id"]]
            links.append(f"[{reference_label(reference)}]({reference['url']})")
        lines.append(
            "| "
            + " | ".join(
                markdown_escape(value)
                for value in [
                    f"`{method['id']}` — {method['title']}",
                    method["constraints"][0],
                    "; ".join(links) if links else "Project capability boundary.",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Method details",
            "",
            "These sections render every catalog field. Dependencies follow the curated semantics above and are not an exhaustive source call graph.",
            "",
        ]
    )
    for method in catalog["methods"]:
        semantic_record = semantic_records[method["id"]]
        semantic_facts = semantic_record["facts"]
        links = []
        for link in method["reference_links"]:
            reference = references[link["reference_id"]]
            links.append(
                f"[{reference_label(reference)}]({reference['url']}) "
                f"(`{link['role']}`; {link['locator']})"
            )
        external_text = "—"
        if method["external_code"] is not None:
            external = method["external_code"]
            external_text = (
                f"[upstream]({external['upstream_url']}) at "
                f"`{external['pinned_ref']}` under `{external['license']}`"
            )
        validation = method["validation"]
        lines.extend(
            [
                f"### `{method['id']}` — {method['title']}",
                "",
                method["summary"],
                "",
                f"- **Classification:** category `{method['category']}`; definition `{method['definition_origin']}`; implementation `{method['implementation_origin']}`; status `{method['implementation_status']}`; code availability `{method['code_availability']}`.",
                f"- **Cargo features:** {code_list(method['cargo_features'])}.",
                f"- **Rust entry points:** {code_list(method['rust_entry_points'])}.",
                f"- **Python entry points:** {code_list(method['python_entry_points'])}.",
                f"- **Source files:** {code_list(method['source_files'])}.",
                f"- **Source marker files:** {code_list(method['source_marker_files'])}.",
                f"- **Release-scope families:** {code_list(method['release_scope_families'])}.",
                f"- **Curated dependencies:** {code_list(method['depends_on'])}.",
                f"- **Papers/reference code:** {'; '.join(links) if links else 'No dedicated paper or external code is claimed.'}",
                f"- **External code pin:** {external_text}.",
                f"- **New in pid-rs:** {method['new_in_pid_rs']}",
                f"- **Scientific novelty claim:** `{method['scientific_novelty_claim']}`.",
                f"- **Typed semantic facts:** data domain `{semantic_facts['data_domain']}`; population support `{semantic_facts['population_support']}`; conditioning `{semantic_facts['conditioning']}`; estimand family `{semantic_facts['estimand_family']}`.",
                f"- **Observed alias families (diagnostic revision {semantic_authority['alias_diagnostic']['revision']}):** {code_list(semantic_record['observed_alias_families'])}.",
                f"- **Reviewed semantic payload SHA-256:** `{semantic_record['payload_sha256']}`.",
                f"- **Constraints:** {'<br>'.join(method['constraints'])}",
                f"- **Bounded validation:** `{validation['level']}` — {validation['scope']} Limitations: {validation['limitations']} Evidence: {code_list(validation['evidence_paths'])}.",
                "",
            ]
        )

    lines.extend(["## Reference registry", ""])
    for reference in catalog["references"]:
        identifiers = []
        if reference["doi"]:
            identifiers.append(f"DOI `{reference['doi']}`")
        if reference["arxiv"]:
            identifiers.append(f"arXiv `{reference['arxiv']}`")
        suffix = f" ({'; '.join(identifiers)})" if identifiers else ""
        lines.append(
            f"- `{reference['id']}` — "
            f"[{', '.join(reference['authors'])} ({reference['year']}), "
            f"*{reference['title']}*]({reference['url']}){suffix}."
        )
    lines.append("")
    return "\n".join(lines)


def validate_catalog(
    *,
    root: Path,
    catalog_path: Path,
    schema_path: Path,
    semantic_authority_path: Path,
    semantic_authority_schema_path: Path,
    scope_path: Path,
    markdown_path: Path,
    scientific_contract_fixtures_path: Path,
    check_markdown: bool,
) -> tuple[dict[str, Any], str]:
    catalog = load_json(catalog_path, canonical=True)
    schema = load_json(schema_path, canonical=True)
    semantic_authority = load_json(semantic_authority_path, canonical=True)
    semantic_authority_schema = load_json(
        semantic_authority_schema_path, canonical=True
    )
    scope = load_json(scope_path, canonical=True)
    try:
        validate_json_schema(catalog, schema, name=str(catalog_path))
        validate_json_schema(
            semantic_authority,
            semantic_authority_schema,
            name=str(semantic_authority_path),
        )
    except SchemaValidationError as error:
        raise CatalogError(f"schema validation failed: {error}") from error
    if catalog["schema"] != SCHEMA or catalog["schema_revision"] != SCHEMA_REVISION:
        raise CatalogError("unsupported method catalog schema identity")

    methods = unique_index(catalog["methods"], label="method")
    references = unique_index(catalog["references"], label="reference")
    families = unique_index(
        scope["families"], label="release-scope family", require_sorted=False
    )
    features = cargo_features(root / DEFAULT_CARGO.relative_to(ROOT))
    migration_surface = registered_migration_surface(root)
    migration_inventory = methods.get(MIGRATION_METHOD_ID)
    if migration_inventory is None:
        raise CatalogError(f"required method entry is missing: {MIGRATION_METHOD_ID}")
    cataloged_migration_surface = set(migration_inventory["python_entry_points"])
    if cataloged_migration_surface != migration_surface:
        missing = sorted(migration_surface - cataloged_migration_surface)
        extra = sorted(cataloged_migration_surface - migration_surface)
        raise CatalogError(
            f"{MIGRATION_METHOD_ID}: inventory does not match registered migration surface; "
            f"missing={missing!r}, extra={extra!r}"
        )
    check_migration_ownership(methods, migration_surface)
    for method in methods.values():
        check_method_rules(
            root,
            method,
            references,
            families,
            features,
            migration_surface,
        )
    check_dag(methods)

    coverage: dict[str, list[str]] = defaultdict(list)
    for method in methods.values():
        for family_id in method["release_scope_families"]:
            coverage[family_id].append(method["id"])
    missing_families = sorted(set(families) - set(coverage))
    if missing_families:
        raise CatalogError(
            "release-scope families lack method mappings: "
            + ", ".join(missing_families)
        )
    for family_id, family in families.items():
        expected_python = set(family["python_exposure"])
        if not expected_python:
            continue
        cataloged_python = {
            python_surface_name(entry_point)
            for method in methods.values()
            if method["id"] != PYTHON_V1_METHOD_ID
            if family_id in method["release_scope_families"]
            for entry_point in method["python_entry_points"]
        }
        expected_scientific_callables = {
            entry_point
            for entry_point in expected_python
            if entry_point.rsplit(".", 1)[-1][:1].islower()
        }
        missing_python = sorted(expected_scientific_callables - cataloged_python)
        if missing_python:
            raise CatalogError(
                f"{family_id}: Python exposure is not cataloged: "
                + ", ".join(missing_python)
            )
    missing_unsupported = sorted(REQUIRED_UNSUPPORTED - set(methods))
    if missing_unsupported:
        raise CatalogError(
            "required unsupported entries are missing: "
            + ", ".join(missing_unsupported)
        )

    check_markers(root, methods)
    check_scientific_contract_fixtures(scientific_contract_fixtures_path, methods)
    check_semantic_authority(
        catalog=catalog,
        catalog_path=catalog_path,
        authority=semantic_authority,
        authority_schema_path=semantic_authority_schema_path,
        methods=methods,
        references=references,
    )
    rendered = render_markdown(catalog, semantic_authority)
    if check_markdown:
        try:
            actual = markdown_path.read_text(encoding="utf-8")
        except OSError as error:
            raise CatalogError(
                f"cannot read generated Markdown {markdown_path}: {error}"
            ) from error
        if actual != rendered:
            raise CatalogError(
                f"{markdown_path} is stale; regenerate it from {catalog_path} "
                "with scripts/check-method-catalog.py --print-markdown"
            )
    return catalog, rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--semantic-authority",
        type=Path,
        default=DEFAULT_SEMANTIC_AUTHORITY,
    )
    parser.add_argument(
        "--semantic-authority-schema",
        type=Path,
        default=DEFAULT_SEMANTIC_AUTHORITY_SCHEMA,
    )
    parser.add_argument("--scope", type=Path, default=DEFAULT_SCOPE)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument(
        "--scientific-contract-fixtures",
        type=Path,
        default=DEFAULT_SCIENTIFIC_CONTRACT_FIXTURES,
    )
    parser.add_argument(
        "--print-markdown",
        action="store_true",
        help="print the canonical generated Markdown instead of checking the checked-in view",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        catalog, rendered = validate_catalog(
            root=root,
            catalog_path=args.catalog.resolve(),
            schema_path=args.schema.resolve(),
            semantic_authority_path=args.semantic_authority.resolve(),
            semantic_authority_schema_path=args.semantic_authority_schema.resolve(),
            scope_path=args.scope.resolve(),
            markdown_path=args.markdown.resolve(),
            scientific_contract_fixtures_path=args.scientific_contract_fixtures.resolve(),
            check_markdown=not args.print_markdown,
        )
    except CatalogError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.print_markdown:
        sys.stdout.write(rendered)
    else:
        print(
            f"OK: {len(catalog['methods'])} method entries and "
            f"{len(catalog['references'])} references are coherent"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
