#!/usr/bin/env python3
"""Validate and render the pid-rs ecosystem capability and evidence-gap contract."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTRACT = ROOT / "ecosystem-capabilities.json"
DEFAULT_MARKDOWN = ROOT / "ECOSYSTEM_CAPABILITIES.md"
DEFAULT_SCHEMA = ROOT / "audit/schemas/ecosystem-capabilities.schema.json"
SCHEMA = "pid-rs/ecosystem-capabilities"
SCHEMA_REVISION = 1
CLAIM_BOUNDARY = (
    "This contract classifies pid-rs as a standalone, protocol-neutral library "
    "and tooling project. It is not an NCP peer, provider, or consumer and "
    "receives no NCP role receipt. It records pid-rs capabilities, retained "
    "boundaries, and missing evidence against four historical consumer snapshots. "
    "It does not claim compatibility, integration, qualification, operational "
    "validation, or application validity."
)
CLAIMS_NOT_MADE = [
    "Compatibility with current or historical consumer code.",
    "Consumer integration or deployable adapters.",
    "Scientific validation of consumer data, preprocessing, or estimands.",
    "Sequential, alerting, mission, or authorization suitability.",
    "Authenticity or freshness of consumer repositories beyond the bound historical snapshot.",
    "Independent review or holdout qualification.",
    (
        "NCP compatibility or any NCP peer, provider, consumer, transport, "
        "authority, or role-receipt status."
    ),
]
EXPECTED_CONSUMERS = ("crebain", "galadriel", "haldir", "prisoma")
EXPECTED_EXCLUDED_INTEGRATIONS = ("external-authority",)
EXPECTED_REQUIREMENT_SOURCES = {
    "crebain": [
        "docs/GALADRIEL_PRODUCER.md",
        "docs/MODEL_CONTRACTS.md",
        "docs/PLANT_APPLY_OBSERVATION_V1.md",
        "scripts/fixtures/phase0-evidence-artifact-valid.json",
        "src-tauri/src/pid_observation.rs",
    ],
    "galadriel": [
        "crates/galadriel-eval/src/evidence_main.rs",
        "crates/galadriel-ncp/schemas/galadriel-pid-envelope-v1.schema.json",
        "docs/PRODUCER-CONTRACT.md",
        "evidence/pid-rs-1.0-migration.json",
        "evidence/post-audit-v1.json",
    ],
    "haldir": [
        "contracts/vectors/README.md",
        "crates/haldir-deployment/src/contract.rs",
        "crates/haldir-evidence/src/gate_journal.rs",
        "docs/EVIDENCE-SEMANTICS.md",
        "docs/RESEARCH-PROTOCOL.md",
    ],
    "prisoma": [
        "crates/pid-bridge/src/bin/contract.rs",
        "protocols/capability_matrix_current_v1.json",
        "protocols/ecosystem_evidence_current_v1.json",
        "protocols/holdout_registry_v1.json",
        "protocols/research_claim_registry_v1.json",
    ],
}
LOCAL_METHOD_MATURITY_MEANINGS = {
    "experimental": (
        "At least one named primary pid-rs method is an experimental local implementation."
    ),
    "retained-boundary": (
        "The requirement is deliberately outside the local pid-rs implementation boundary."
    ),
    "stable": "Every named primary pid-rs method is a stable local implementation.",
    "unavailable": "No primary pid-rs implementation is named for the requirement.",
}
EXPECTED_BINDINGS = {
    "assurance-registry": (
        "audit/evidence/assurance-registry.json",
        "Release-family assurance layers and explicit gaps.",
    ),
    "method-catalog": (
        "method-catalog.json",
        "Method origin, implementation status, constraints, and evidence.",
    ),
    "release-scope": (
        "release-scope-1.0.json",
        "Proposed 1.0 family boundary and integration claim status.",
    ),
    "repository-snapshot": (
        "audit/evidence/repository-snapshot.json",
        "Historical repository identity evidence only.",
    ),
}
EXPECTED_HISTORICAL_SNAPSHOT_SHA256 = (
    "b57e506bbf30183c29bea4ff062a3711a3e471400dd91ebbdd8f787152af4b56"
)
EXPECTED_HISTORICAL_BASE_SEMANTIC_PROJECTION_SHA256 = (
    "63a843b4fbd36c43534ab8fa6dd9da2174c673862b13368c3dd6eed4fc2c5280"
)
EXPECTED_CONSUMER_INVENTORY_PROJECTION_SHA256 = (
    "ccc5ba5ad414a9c923f56619a3acb09ebc1f5e18ee014ce8f02e152ae24d3d40"
)
HISTORICAL_BASE_MOVING_AUTHORITY_SHA256 = {
    "assurance-registry": (
        "846fe4947c59ce1f5956270f77c202cb96f373d7867b64864d4a676c69991ceb"
    ),
    "method-catalog": (
        "eb428177d3b42996dfd43b72918034d61c058fbd9b15eed9dffe349550fdaf41"
    ),
    "release-scope": (
        "90fb0c1dc83231f0faa4a0ce622799a579ca9f069478e9eef873e94be44649c8"
    ),
}
EXPECTED_CURRENT_KSG_AUTHORITY_SHA256 = {
    "assurance-registry": (
        "355fb84902fb344657e04f36767ac3a0865f24539496b28e174f03eaf3789e51"
    ),
    "method-catalog": (
        "9bb61e401c68c4872ed7ec644b9d09cabdd6a4f58ef4d04057f2f001b037d360"
    ),
    "release-scope": (
        "98473c97b3f49877e6231350c6a798c1a8745fa2c78eff9abf624b9a88f60ecf"
    ),
}
EVIDENCE_CLASS_MEANINGS = {
    "assumption-certificate": (
        "A machine-readable contract records the scientific assumptions needed by the route."
    ),
    "authorization-safety-case": (
        "An independently reviewed safety case governs any authority-relevant use."
    ),
    "bounded-software-test": (
        "Executable tests cover a stated finite domain, property set, or fixture corpus."
    ),
    "consumer-commit-integration": (
        "A named consumer commit pins and exercises the exact pid-rs API and configuration."
    ),
    "deductive-rust-refinement": (
        "A deductive proof connects the executable Rust kernel to the formal specification."
    ),
    "definition-provenance": (
        "The method catalog identifies the definition origin, implementation origin, and constraints."
    ),
    "formal-or-analytic": (
        "A machine-checked or exact analytic argument covers a stated mathematical obligation."
    ),
    "holdout-benchmark": (
        "A preregistered held-out challenge evaluates the exact consumer route."
    ),
    "implementation-contract": (
        "Typed code and tests enforce the declared software and interpretation boundary."
    ),
    "independent-review": (
        "A reviewer independent of the implementation records a scoped assessment."
    ),
    "negative-mutation": (
        "A fail-closed test rejects a scientifically invalid or metadata-invalid route."
    ),
    "numerical-stress": (
        "High-precision or adversarial fixtures challenge finite-precision behavior."
    ),
    "certified-numerical-bound": (
        "A rigorous enclosure bounds finite-precision error for the reported quantity."
    ),
    "runlog-replay": (
        "A bounded reader validates and replays the relevant run-log schema."
    ),
    "sequential-inference": (
        "A theorem or calibrated procedure controls repeated, adaptive, or post-selection use."
    ),
    "statistical-validation": (
        "Calibration evidence covers the stated sampling process, estimator, and uncertainty claim."
    ),
    "trusted-catalog-binding": (
        "Runtime evidence binds a canonical method entry and verifies its exact digest."
    ),
}
PRIMARY_FORBIDDEN_CATEGORIES = {"unsupported", "validation"}
PRIMARY_ALLOWED_STATUSES = {"experimental", "stable"}
DISPOSITION_OWNER = {
    "BLOCKED_EXTERNAL": "external",
    "OPEN_CONSUMER": "consumer",
    "OPEN_JOINT": "joint",
    "OPEN_LOCAL": "pid-rs",
    "RETAINED_BOUNDARY": "pid-rs",
}
PRIORITY_RANK = {"P0": 0, "P1": 1, "P2": 2}
OVERCLAIM_RE = re.compile(
    r"\b(?:"
    r"certified(?:\s+safe)?|compatible|deployable|"
    r"(?:consumer\s+)?(?:integration|implementation|requirement|route|work)\s+is\s+complete|"
    r"fully\s+satisfied|integrated|meets?\s+all\s+(?:consumer\s+)?needs|"
    r"mission\s+authorization|operationally\s+validated|production[- ]ready|"
    r"qualified|ready\s+for|validated|verified"
    r")\b",
    re.IGNORECASE,
)
DIRECT_NEGATION_RE = re.compile(
    r"\b(?:"
    r"absent|cannot|does\s+not|do\s+not|has\s+no|is\s+not|lack|lacks|"
    r"missing|must\s+not|no|not|reject|retained\s+boundary|unavailable|without"
    r")\b(?:\W+\w+){0,8}\W*$",
    re.IGNORECASE,
)
NEGATIVE_TEST_PATHS_BY_REQUIREMENT = {
    "crebain.runlog-binding": {
        "crates/pid-runlog/tests/scientific_contract.rs",
        "scripts/check-method-catalog-self-test.py",
    },
    "prisoma.mixed-support": {
        "crates/pid-runlog/tests/scientific_contract.rs",
    },
}
ASSURANCE_LAYER_FOR_CLASS = {
    "assumption-certificate": "statistical_application_validity",
    "bounded-software-test": "rust_refinement",
    "certified-numerical-bound": "floating_point_numerical_behavior",
    "deductive-rust-refinement": "rust_refinement",
    "formal-or-analytic": "exact_algebra",
    "implementation-contract": "rust_refinement",
    "numerical-stress": "floating_point_numerical_behavior",
}
ASSURANCE_STATUS_FOR_CLASS = {
    "assumption-certificate": {
        ("ASSUMPTION_GATED", "ASSUMPTION_DECLARATION"),
        ("NOT_CLAIMED", "ASSUMPTION_DECLARATION"),
    },
    "bounded-software-test": {
        ("BOUNDED", "BOUNDED_TEST"),
        ("TESTED", "IMPLEMENTATION_TEST"),
    },
    "formal-or-analytic": {
        ("BOUNDED", "BOUNDED_TEST"),
        ("TESTED", "IMPLEMENTATION_TEST"),
    },
    "implementation-contract": {("TESTED", "IMPLEMENTATION_TEST")},
    "numerical-stress": {("BOUNDED", "BOUNDED_TEST")},
}
EXPECTED_CONSUMER_SUMMARIES = {
    "crebain": (
        "The selected historical Crebain sources define observation, producer, and model "
        "contracts but contain no direct pid-rs dependency evidence."
    ),
    "galadriel": (
        "The selected historical Galadriel sources define a PID evidence envelope and record "
        "one bounded synthetic pid-rs migration. They do not establish current release or "
        "deployment qualification."
    ),
    "haldir": (
        "The selected historical Haldir sources define authority and evidence boundaries and "
        "contain no direct PID integration evidence. The PID requirements below are "
        "conservative implications of those boundaries."
    ),
    "prisoma": (
        "The selected historical Prisoma sources record bounded producer-consumer fixtures and "
        "research-claim gates. They do not establish current pid-rs release qualification or "
        "application validity."
    ),
}
INVENTORY_SCOPE = (
    "This is a selected, non-exhaustive risk projection from the bound historical sources. "
    "It is not a complete inventory of current or historical consumer requirements."
)
EXPECTED_HISTORICAL_EVIDENCE = {
    "crebain": [],
    "galadriel": [
        {
            "class": "bounded-historical-consumer-integration",
            "id": "galadriel.synthetic-migration",
            "limitation": (
                "The artifact classifies itself as synthetic compatibility only and "
                "does not provide deployment calibration."
            ),
            "pid_rs_revision": "1cd2424f7967e1752dcc8e53859e8fdad3566f51",
            "scope": (
                "Exact historical Galadriel and pid-rs revisions, commands, seeds, "
                "hashes, and paired synthetic outputs."
            ),
            "source_paths": ["evidence/pid-rs-1.0-migration.json"],
        }
    ],
    "haldir": [],
    "prisoma": [
        {
            "class": "bounded-historical-consumer-integration",
            "id": "prisoma.report-abstention",
            "limitation": (
                "Positive and abstaining synthetic fixtures do not validate real "
                "embedding support, estimates, or application claims."
            ),
            "pid_rs_revision": "ac4a7803c5a77408f5e9176c60cda71c65c38260",
            "scope": (
                "A pinned pid-rs producer and Prisoma consumer were tested together "
                "on positive and abstaining fixtures."
            ),
            "source_paths": ["protocols/capability_matrix_current_v1.json"],
        },
        {
            "class": "bounded-historical-consumer-integration",
            "id": "prisoma.schema2-replay",
            "limitation": (
                "Schema 2 fixture replay does not establish schema 3 scientific replay, "
                "policy replay, or current release qualification."
            ),
            "pid_rs_revision": "ac4a7803c5a77408f5e9176c60cda71c65c38260",
            "scope": (
                "A pinned pid-runlog producer and Prisoma consumer were tested together "
                "on schema 2 validation and replay fixtures."
            ),
            "source_paths": ["protocols/capability_matrix_current_v1.json"],
        },
    ],
}


class EcosystemContractError(RuntimeError):
    """The ecosystem contract or one of its bound authorities is inconsistent."""


def canonical_assurance_projection() -> dict[str, Any]:
    """Build the assurance registry with its authoritative generator."""

    checker_path = ROOT / "scripts/check-review-evidence.py"
    spec = importlib.util.spec_from_file_location(
        "pid_rs_check_review_evidence_for_ecosystem", checker_path
    )
    if spec is None or spec.loader is None:
        raise EcosystemContractError(
            f"cannot load assurance-registry generator: {checker_path}"
        )
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        projection = module.build_assurance_registry()
    except Exception as error:
        raise EcosystemContractError(
            f"cannot build canonical assurance-registry projection: {error}"
        ) from error
    if not isinstance(projection, dict):
        raise EcosystemContractError(
            "canonical assurance-registry projection is not a JSON object"
        )
    return projection


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EcosystemContractError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def reject_non_finite_json_constant(token: str) -> None:
    raise EcosystemContractError(f"non-finite JSON number is forbidden: {token}")


def load_json_bytes(path: Path, *, canonical: bool = False) -> tuple[Any, bytes]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EcosystemContractError(f"cannot read {path}: {error}") from error
    if canonical:
        expected = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
        if text != expected:
            raise EcosystemContractError(
                f"{path} is not canonical sorted two-space JSON with one final LF"
            )
    return value, raw


def load_json(path: Path, *, canonical: bool = False) -> Any:
    return load_json_bytes(path, canonical=canonical)[0]


def safe_repo_file(root: Path, relative: Any, *, label: str) -> Path:
    if not isinstance(relative, str) or not relative:
        raise EcosystemContractError(
            f"{label}: path must be a non-empty repository-relative string"
        )
    candidate_relative = Path(relative)
    if candidate_relative.is_absolute() or ".." in candidate_relative.parts:
        raise EcosystemContractError(f"{label}: unsafe repository path {relative!r}")
    current = root.resolve(strict=True)
    for component in candidate_relative.parts:
        current = current / component
        if current.is_symlink():
            raise EcosystemContractError(
                f"{label}: symlink paths are forbidden: {relative!r}"
            )
    try:
        resolved = (root / candidate_relative).resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise EcosystemContractError(
            f"{label}: file is missing or escapes the repository: {relative!r}"
        ) from error
    if not resolved.is_file():
        raise EcosystemContractError(
            f"{label}: expected a regular file: {relative!r}"
        )
    return resolved


def require_sorted(values: list[Any], *, label: str, key=None) -> None:
    expected = sorted(values, key=key)
    if values != expected:
        raise EcosystemContractError(f"{label}: values must be in canonical order")


def reject_affirmative_overclaim(value: str, *, label: str) -> None:
    for sentence in re.split(r"(?<=[.!?])\s+", value):
        for match in OVERCLAIM_RE.finditer(sentence):
            clause_prefix = re.split(r"[;:]", sentence[: match.start()])[-1]
            if not DIRECT_NEGATION_RE.search(clause_prefix):
                raise EcosystemContractError(
                    f"{label}: prohibited affirmative claim wording"
                )


def historical_base_semantic_projection(
    contract: dict[str, Any],
) -> dict[str, Any]:
    """Select reviewed semantics with the three moving digests at their base values."""

    historical_bindings = []
    for binding in contract["source_bindings"]:
        projected_binding = dict(binding)
        historical_sha256 = HISTORICAL_BASE_MOVING_AUTHORITY_SHA256.get(
            binding["id"]
        )
        if historical_sha256 is not None:
            projected_binding["sha256"] = historical_sha256
        historical_bindings.append(projected_binding)

    return {
        "inventory_scope": contract["inventory_scope"],
        "source_bindings": historical_bindings,
        "consumers": contract["consumers"],
    }


def consumer_inventory_projection(contract: dict[str, Any]) -> dict[str, Any]:
    """Select the invariant inventory boundary and consumer records."""

    return {
        "inventory_scope": contract["inventory_scope"],
        "consumers": contract["consumers"],
    }


def projection_sha256(value: dict[str, Any]) -> str:
    """Hash a projection with the contract's canonical compact encoding."""

    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_semantic_projections(contract: dict[str, Any]) -> None:
    """Reject drift outside the independently checked moving authority digests."""

    historical_observed = projection_sha256(
        historical_base_semantic_projection(contract)
    )
    if historical_observed != EXPECTED_HISTORICAL_BASE_SEMANTIC_PROJECTION_SHA256:
        raise EcosystemContractError(
            "historical/base semantic projection differs from its reviewed binding"
        )
    consumer_observed = projection_sha256(consumer_inventory_projection(contract))
    if consumer_observed != EXPECTED_CONSUMER_INVENTORY_PROJECTION_SHA256:
        raise EcosystemContractError(
            "consumer/inventory projection differs from its reviewed binding"
        )


def method_index(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    methods = {method["id"]: method for method in catalog["methods"]}
    if len(methods) != len(catalog["methods"]):
        raise EcosystemContractError("method catalog contains duplicate method IDs")
    return methods


def family_index(scope: dict[str, Any]) -> dict[str, dict[str, Any]]:
    families = {family["id"]: family for family in scope["families"]}
    if len(families) != len(scope["families"]):
        raise EcosystemContractError("release scope contains duplicate family IDs")
    return families


def validate_source_bindings(
    root: Path, contract: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    bindings = contract["source_bindings"]
    require_sorted(bindings, label="source_bindings", key=lambda item: item["id"])
    actual_ids = {binding["id"] for binding in bindings}
    if actual_ids != set(EXPECTED_BINDINGS):
        raise EcosystemContractError(
            "source_bindings must cover exactly "
            f"{sorted(EXPECTED_BINDINGS)!r}, observed {sorted(actual_ids)!r}"
        )
    loaded: dict[str, dict[str, Any]] = {}
    for binding in bindings:
        binding_id = binding["id"]
        expected_path, expected_role = EXPECTED_BINDINGS[binding_id]
        if binding["path"] != expected_path or binding["role"] != expected_role:
            raise EcosystemContractError(
                f"{binding_id}: bound path or role differs from the fixed contract"
            )
        expected_current_sha256 = EXPECTED_CURRENT_KSG_AUTHORITY_SHA256.get(
            binding_id
        )
        if (
            expected_current_sha256 is not None
            and binding["sha256"] != expected_current_sha256
        ):
            raise EcosystemContractError(
                f"{binding_id}: digest differs from the reviewed current "
                "KSG authority binding"
            )
        path = safe_repo_file(root, binding["path"], label=f"{binding_id}.path")
        value, raw = load_json_bytes(path, canonical=True)
        observed_sha256 = hashlib.sha256(raw).hexdigest()
        if binding["sha256"] != observed_sha256:
            raise EcosystemContractError(
                f"{binding_id}: stale SHA-256; expected {observed_sha256}, "
                f"observed {binding['sha256']}"
            )
        if (
            binding_id == "repository-snapshot"
            and observed_sha256 != EXPECTED_HISTORICAL_SNAPSHOT_SHA256
        ):
            raise EcosystemContractError(
                "repository-snapshot: immutable historical snapshot digest changed"
            )
        if not isinstance(value, dict):
            raise EcosystemContractError(f"{binding_id}: expected a JSON object")
        loaded[binding_id] = value
    return loaded


def is_executable_test_path(path: str) -> bool:
    candidate = Path(path)
    if "/tests/" in f"/{path}" and candidate.suffix in {".py", ".rs", ".sh"}:
        return "/fixtures/" not in f"/{path}"
    return candidate.name.endswith("-self-test.py") or candidate.name.endswith(
        "-self-test.sh"
    )


def is_typed_source_path(path: str) -> bool:
    return Path(path).suffix == ".rs" and "/src/" in f"/{path}"


def is_formal_source_path(path: str) -> bool:
    return Path(path).suffix in {".lean", ".smt2"}


def is_fixture_path(path: str) -> bool:
    return "/fixtures/" in f"/{path}"


def assurance_family_index(
    assurance: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    families = {family["family_id"]: family for family in assurance["families"]}
    if len(families) != len(assurance["families"]):
        raise EcosystemContractError(
            "assurance registry contains duplicate family IDs"
        )
    return families


def relevant_method_evidence(
    requirement: dict[str, Any], methods: dict[str, dict[str, Any]]
) -> set[str]:
    method_ids = (
        requirement["primary_method_ids"]
        + requirement["validation_method_ids"]
        + requirement["boundary_method_ids"]
    )
    return {
        path
        for method_id in method_ids
        for path in (
            methods[method_id]["source_files"]
            + methods[method_id]["source_marker_files"]
            + methods[method_id]["validation"]["evidence_paths"]
        )
    }


def applicable_layer_records(
    requirement: dict[str, Any],
    assurance_families: dict[str, dict[str, Any]],
    layer_id: str,
    *,
    label: str,
) -> list[tuple[str, dict[str, Any]]]:
    records: list[tuple[str, dict[str, Any]]] = []
    for family_id in requirement["release_scope_family_ids"]:
        family = assurance_families[family_id]
        try:
            layer = family["layers"][layer_id]
        except KeyError as error:
            raise EcosystemContractError(
                f"{label}: assurance layer {layer_id!r} is absent for {family_id!r}"
            ) from error
        records.append((family_id, layer))
    return records


def require_per_family_path_membership(
    paths: set[str],
    layers: list[tuple[str, dict[str, Any]]],
    *,
    label: str,
    predicate=None,
) -> None:
    for family_id, layer in layers:
        allowed = set(layer["assurance"]["evidence"])
        matching = paths & allowed
        if predicate is not None:
            matching = {path for path in matching if predicate(path)}
        if not matching:
            raise EcosystemContractError(
                f"{label}: no class-appropriate artifact covers assurance family "
                f"{family_id!r}"
            )


def validate_evidence(
    root: Path,
    requirement: dict[str, Any],
    methods: dict[str, dict[str, Any]],
    assurance_families: dict[str, dict[str, Any]],
    *,
    label: str,
) -> set[str]:
    evidence = requirement["evidence"]
    required = evidence["required_classes"]
    missing = evidence["missing_classes"]
    present = evidence["present"]
    require_sorted(required, label=f"{label}.evidence.required_classes")
    require_sorted(missing, label=f"{label}.evidence.missing_classes")
    require_sorted(
        present,
        label=f"{label}.evidence.present",
        key=lambda record: record["class"],
    )
    present_classes = [record["class"] for record in present]
    if len(present_classes) != len(set(present_classes)):
        raise EcosystemContractError(f"{label}: duplicate present evidence class")
    if set(present_classes) & set(missing):
        raise EcosystemContractError(
            f"{label}: present and missing evidence classes overlap"
        )
    if set(required) != set(present_classes) | set(missing):
        raise EcosystemContractError(
            f"{label}: required evidence must equal present plus missing evidence"
        )
    method_evidence = relevant_method_evidence(requirement, methods)
    assurance_evidence = {
        path
        for family_id in requirement["release_scope_family_ids"]
        for layer in assurance_families[family_id]["layers"].values()
        for path in layer["assurance"]["evidence"]
    }
    eligible_paths = (
        method_evidence
        | assurance_evidence
        | {
            path
            for paths in NEGATIVE_TEST_PATHS_BY_REQUIREMENT.values()
            for path in paths
        }
        | {"method-catalog.json"}
    )
    for record in present:
        evidence_class = record["class"]
        require_sorted(
            record["paths"],
            label=f"{label}.evidence.{evidence_class}.paths",
        )
        record_paths = set(record["paths"])
        for index, path in enumerate(record["paths"]):
            safe_repo_file(
                root,
                path,
                label=f"{label}.evidence.{evidence_class}.paths[{index}]",
            )
            if path not in eligible_paths:
                raise EcosystemContractError(
                    f"{label}.evidence.{evidence_class}: {path!r} is not a member "
                    "of a relevant method-validation or assurance-layer authority"
                )

        if evidence_class == "definition-provenance":
            if record["paths"] != ["method-catalog.json"]:
                raise EcosystemContractError(
                    f"{label}: definition provenance must bind method-catalog.json"
                )
            for family_id, layer in applicable_layer_records(
                requirement,
                assurance_families,
                "definition",
                label=label,
            ):
                assurance_record = layer["assurance"]
                if (
                    assurance_record["status"],
                    assurance_record["evidence_tier"],
                ) != ("DOCUMENTED", "DOCUMENTATION"):
                    raise EcosystemContractError(
                        f"{label}: {family_id!r} lacks documented definition assurance"
                    )

        layer_id = ASSURANCE_LAYER_FOR_CLASS.get(evidence_class)
        layers: list[tuple[str, dict[str, Any]]] = []
        if layer_id is not None:
            layers = applicable_layer_records(
                requirement,
                assurance_families,
                layer_id,
                label=label,
            )
            allowed_statuses = ASSURANCE_STATUS_FOR_CLASS.get(evidence_class)
            if allowed_statuses is None:
                raise EcosystemContractError(
                    f"{label}: {evidence_class!r} cannot be marked present"
                )
            for family_id, layer in layers:
                observed = (
                    layer["assurance"]["status"],
                    layer["assurance"]["evidence_tier"],
                )
                if observed not in allowed_statuses:
                    raise EcosystemContractError(
                        f"{label}: {evidence_class!r} is not supported by "
                        f"{family_id!r} layer status/tier {observed!r}"
                    )

        if evidence_class == "bounded-software-test":
            if not any(is_executable_test_path(path) for path in record_paths):
                raise EcosystemContractError(
                    f"{label}: bounded software evidence requires an executable test"
                )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}",
                predicate=is_executable_test_path,
            )
        elif evidence_class == "implementation-contract":
            if not any(is_typed_source_path(path) for path in record_paths) or not any(
                is_executable_test_path(path) for path in record_paths
            ):
                raise EcosystemContractError(
                    f"{label}: implementation contract requires typed source and "
                    "an executable test"
                )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}.source",
                predicate=is_typed_source_path,
            )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}.test",
                predicate=is_executable_test_path,
            )
        elif evidence_class == "formal-or-analytic":
            if not any(is_formal_source_path(path) for path in record_paths):
                raise EcosystemContractError(
                    f"{label}: formal evidence requires a Lean or SMT source"
                )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}",
                predicate=is_formal_source_path,
            )
        elif evidence_class == "numerical-stress":
            if not any(is_executable_test_path(path) for path in record_paths):
                raise EcosystemContractError(
                    f"{label}: numerical stress evidence requires an executable test"
                )
            if not (
                any(is_fixture_path(path) for path in record_paths)
                or any(
                    token in Path(path).stem
                    for path in record_paths
                    for token in ("gaussian", "known_failures", "oracle")
                )
            ):
                raise EcosystemContractError(
                    f"{label}: numerical stress evidence needs an adversarial, "
                    "oracle, Gaussian, or fixture artifact"
                )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}",
                predicate=is_executable_test_path,
            )
        elif evidence_class == "assumption-certificate":
            if not any(is_typed_source_path(path) for path in record_paths) or not any(
                is_executable_test_path(path) for path in record_paths
            ):
                raise EcosystemContractError(
                    f"{label}: assumption certificate requires a typed contract "
                    "and an exercising test"
                )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}.contract",
                predicate=is_typed_source_path,
            )
            require_per_family_path_membership(
                record_paths,
                layers,
                label=f"{label}.evidence.{evidence_class}.test",
                predicate=is_executable_test_path,
            )
        elif evidence_class == "negative-mutation":
            approved_paths = NEGATIVE_TEST_PATHS_BY_REQUIREMENT.get(
                requirement["id"], set()
            )
            if record_paths != approved_paths:
                raise EcosystemContractError(
                    f"{label}: negative-mutation evidence differs from its exact "
                    "approved executable test set"
                )
            if any(
                not is_executable_test_path(path) and not is_fixture_path(path)
                for path in record_paths
            ):
                raise EcosystemContractError(
                    f"{label}: negative-mutation evidence cannot use prose or "
                    "configuration as a test"
                )
        elif evidence_class == "runlog-replay":
            expected = {
                "crates/pid-runlog/src/lib.rs",
                "crates/pid-runlog/tests/replay_cli.rs",
            }
            if record_paths != expected:
                raise EcosystemContractError(
                    f"{label}: schema 2 run-log replay requires the exact reader "
                    "and replay CLI test artifacts"
                )
            if "software.runlog-schema-replay" not in requirement["primary_method_ids"]:
                raise EcosystemContractError(
                    f"{label}: run-log replay evidence lacks the schema 2 method"
                )
            if (
                "software.scientific-outcome-contract-foundation"
                in requirement["primary_method_ids"]
            ):
                raise EcosystemContractError(
                    f"{label}: schema 2 replay cannot satisfy a schema 3 "
                    "scientific-outcome replay requirement"
                )
        elif evidence_class in {
            "authorization-safety-case",
            "certified-numerical-bound",
            "consumer-commit-integration",
            "deductive-rust-refinement",
            "holdout-benchmark",
            "independent-review",
            "sequential-inference",
            "statistical-validation",
            "trusted-catalog-binding",
        }:
            raise EcosystemContractError(
                f"{label}: {evidence_class!r} has no present-evidence authority"
            )
    return set(missing)


def validate_requirement_methods(
    requirement: dict[str, Any],
    methods: dict[str, dict[str, Any]],
    families: dict[str, dict[str, Any]],
    assurance_families: set[str],
    gaps: dict[str, dict[str, Any]],
    *,
    label: str,
) -> str:
    primary_ids = requirement["primary_method_ids"]
    validation_ids = requirement["validation_method_ids"]
    boundary_ids = requirement["boundary_method_ids"]
    for field, values in (
        ("primary_method_ids", primary_ids),
        ("validation_method_ids", validation_ids),
        ("boundary_method_ids", boundary_ids),
        ("release_scope_family_ids", requirement["release_scope_family_ids"]),
        ("gap_ids", requirement["gap_ids"]),
    ):
        require_sorted(values, label=f"{label}.{field}")
    all_ids = primary_ids + validation_ids + boundary_ids
    if len(all_ids) != len(set(all_ids)):
        raise EcosystemContractError(
            f"{label}: primary, validation, and boundary method roles overlap"
        )
    unknown = sorted(set(all_ids) - set(methods))
    if unknown:
        raise EcosystemContractError(f"{label}: unknown method IDs: {unknown!r}")

    for method_id in primary_ids:
        method = methods[method_id]
        if (
            method["category"] in PRIMARY_FORBIDDEN_CATEGORIES
            or method["code_availability"] != "local"
            or method["implementation_status"] not in PRIMARY_ALLOWED_STATUSES
        ):
            raise EcosystemContractError(
                f"{label}: {method_id!r} is not a stable or experimental local "
                "primary implementation"
            )
    for method_id in validation_ids:
        method = methods[method_id]
        if (
            method["category"] != "validation"
            or method["code_availability"] != "local"
            or method["implementation_status"] != "stable"
        ):
            raise EcosystemContractError(
                f"{label}: {method_id!r} is not a stable local validation method"
            )
    for method_id in boundary_ids:
        method = methods[method_id]
        if (
            method["category"] != "unsupported"
            or method["code_availability"] != "none"
            or method["implementation_status"] != "unsupported"
        ):
            raise EcosystemContractError(
                f"{label}: {method_id!r} is not an explicit unsupported boundary"
            )

    expected_families = sorted(
        {
            family_id
            for method_id in primary_ids
            for family_id in methods[method_id]["release_scope_families"]
        }
    )
    if requirement["release_scope_family_ids"] != expected_families:
        raise EcosystemContractError(
            f"{label}: release families must exactly equal the primary-method mapping; "
            f"expected {expected_families!r}"
        )
    unknown_families = sorted(set(expected_families) - set(families))
    if unknown_families:
        raise EcosystemContractError(
            f"{label}: unknown release-scope families: {unknown_families!r}"
        )
    missing_assurance = sorted(set(expected_families) - assurance_families)
    if missing_assurance:
        raise EcosystemContractError(
            f"{label}: families lack assurance-registry rows: {missing_assurance!r}"
        )

    local_maturity = requirement["local_method_maturity"]
    if local_maturity in {"stable", "experimental"} and not primary_ids:
        raise EcosystemContractError(
            f"{label}: {local_maturity} local maturity requires a primary implementation"
        )
    if local_maturity in {"retained-boundary", "unavailable"} and primary_ids:
        raise EcosystemContractError(
            f"{label}: {local_maturity} local maturity cannot name a primary implementation"
        )
    statuses = {methods[method_id]["implementation_status"] for method_id in primary_ids}
    has_retained_boundary = any(
        gap_id in gaps and gaps[gap_id]["disposition"] == "RETAINED_BOUNDARY"
        for gap_id in requirement["gap_ids"]
    )
    maturity = (
        "retained-boundary"
        if not statuses and (boundary_ids or has_retained_boundary)
        else "unavailable"
        if not statuses
        else "experimental"
        if "experimental" in statuses
        else "stable"
    )
    if local_maturity != maturity:
        raise EcosystemContractError(
            f"{label}: local_method_maturity must be derived from primary methods; "
            f"expected {maturity!r}, observed {local_maturity!r}"
        )
    return maturity


def validate_contract(
    root: Path,
    contract: dict[str, Any],
    schema: dict[str, Any],
) -> tuple[
    dict[str, str],
    dict[str, dict[str, Any]],
    dict[str, str],
    dict[str, dict[str, Any]],
]:
    try:
        validate_json_schema(contract, schema)
    except SchemaValidationError as error:
        raise EcosystemContractError(f"schema validation failed: {error}") from error
    if contract["schema"] != SCHEMA or contract["schema_revision"] != SCHEMA_REVISION:
        raise EcosystemContractError("unsupported ecosystem contract schema identity")
    if (
        contract["semantic_projection_sha256"]
        != EXPECTED_HISTORICAL_BASE_SEMANTIC_PROJECTION_SHA256
    ):
        raise EcosystemContractError(
            "semantic_projection_sha256 differs from the historical/base binding"
        )
    if contract["claim_boundary"] != CLAIM_BOUNDARY:
        raise EcosystemContractError("claim_boundary differs from the fixed non-escalation text")
    if contract["claims_not_made"] != CLAIMS_NOT_MADE:
        raise EcosystemContractError("claims_not_made differs from the fixed claim exclusions")
    if contract["inventory_scope"] != INVENTORY_SCOPE:
        raise EcosystemContractError(
            "inventory_scope differs from the fixed non-exhaustive boundary"
        )
    if tuple(contract["excluded_integration_ids"]) != EXPECTED_EXCLUDED_INTEGRATIONS:
        raise EcosystemContractError("external-authority must be the sole excluded integration")

    maturity_definitions = contract["local_method_maturity_definitions"]
    require_sorted(
        maturity_definitions,
        label="local_method_maturity_definitions",
        key=lambda definition: definition["id"],
    )
    observed_maturity_definitions = {
        definition["id"]: definition["meaning"]
        for definition in maturity_definitions
    }
    if observed_maturity_definitions != LOCAL_METHOD_MATURITY_MEANINGS:
        raise EcosystemContractError(
            "local_method_maturity_definitions differs from the fixed vocabulary"
        )

    definitions = contract["evidence_class_definitions"]
    require_sorted(
        definitions,
        label="evidence_class_definitions",
        key=lambda definition: definition["id"],
    )
    observed_definitions = {
        definition["id"]: definition["meaning"] for definition in definitions
    }
    if observed_definitions != EVIDENCE_CLASS_MEANINGS:
        raise EcosystemContractError(
            "evidence_class_definitions differs from the fixed vocabulary"
        )

    validate_semantic_projections(contract)
    bound = validate_source_bindings(root, contract)
    catalog = bound["method-catalog"]
    scope = bound["release-scope"]
    snapshot = bound["repository-snapshot"]
    assurance = bound["assurance-registry"]
    if assurance != canonical_assurance_projection():
        raise EcosystemContractError(
            "assurance-registry differs from its canonical generated projection"
        )
    expected_schema_identities = {
        "method-catalog": ("pid-rs/method-catalog", 1),
        "release-scope": ("pid-rs/release-scope", 1),
        "repository-snapshot": ("pid-rs/repository-snapshot", 1),
        "assurance-registry": ("pid-rs/assurance-registry", 2),
    }
    for binding_id, (expected_schema, expected_revision) in (
        expected_schema_identities.items()
    ):
        value = bound[binding_id]
        if (
            value.get("schema") != expected_schema
            or value.get("schema_revision") != expected_revision
        ):
            raise EcosystemContractError(
                f"{binding_id}: bound schema identity differs from "
                f"{expected_schema!r} revision {expected_revision}"
            )
    if (
        snapshot.get("collector_revision")
        != "pid-rs-repository-snapshot-collector/1"
        or snapshot.get("release_scope") != "pid-rs-core-only"
    ):
        raise EcosystemContractError(
            "repository snapshot must remain collector revision 1 historical "
            "pid-rs-core-only evidence"
        )
    snapshot_digest = next(
        binding["sha256"]
        for binding in contract["source_bindings"]
        if binding["id"] == "repository-snapshot"
    )
    sidecar_path = safe_repo_file(
        root,
        "audit/evidence/repository-snapshot.json.sha256",
        label="repository snapshot sidecar",
    )
    try:
        sidecar = sidecar_path.read_text(encoding="ascii")
    except (OSError, UnicodeDecodeError) as error:
        raise EcosystemContractError(
            f"cannot read repository snapshot sidecar: {error}"
        ) from error
    if sidecar != f"{snapshot_digest}  repository-snapshot.json\n":
        raise EcosystemContractError("repository snapshot sidecar digest is stale")
    envelope_path = safe_repo_file(
        root,
        "audit/evidence/repository-snapshot-envelope.json",
        label="repository snapshot envelope",
    )
    envelope = load_json(envelope_path, canonical=True)
    if (
        envelope.get("snapshot_sha256") != snapshot_digest
        or envelope.get("collector_revision")
        != "pid-rs-repository-snapshot-collector/1"
        or envelope.get("source_kind") != "clean_public_https_clones"
    ):
        raise EcosystemContractError(
            "repository snapshot envelope differs from the bound historical snapshot"
        )
    methods = method_index(catalog)
    families = family_index(scope)
    assurance_by_family = assurance_family_index(assurance)
    if set(assurance_by_family) != set(families):
        raise EcosystemContractError(
            "assurance-registry family coverage differs from release scope"
        )
    release_scope_digest = next(
        binding["sha256"]
        for binding in contract["source_bindings"]
        if binding["id"] == "release-scope"
    )
    if assurance.get("release_scope_sha256") != release_scope_digest:
        raise EcosystemContractError(
            "assurance-registry release-scope digest differs from the bound authority"
        )

    integration_claims = {
        claim["integration_id"]: claim["claim_status"]
        for claim in scope["integration_claims"]
    }
    if len(integration_claims) != len(scope["integration_claims"]):
        raise EcosystemContractError(
            "release scope contains duplicate integration claim IDs"
        )
    covered_integrations = set(EXPECTED_CONSUMERS) | set(
        EXPECTED_EXCLUDED_INTEGRATIONS
    )
    if set(integration_claims) != covered_integrations:
        raise EcosystemContractError(
            "consumer plus excluded integration IDs must exactly cover release scope"
        )
    escalated = sorted(
        integration_id
        for integration_id, status in integration_claims.items()
        if status != "not_claimed"
    )
    if escalated:
        raise EcosystemContractError(
            f"release-scope integration claims escalated: {escalated!r}"
        )

    snapshot_rows = {
        repository["name"]: repository for repository in snapshot["repositories"]
    }
    if len(snapshot_rows) != len(snapshot["repositories"]):
        raise EcosystemContractError(
            "repository snapshot contains duplicate repository names"
        )
    consumers = contract["consumers"]
    require_sorted(consumers, label="consumers", key=lambda consumer: consumer["id"])
    consumer_ids = tuple(consumer["id"] for consumer in consumers)
    if consumer_ids != EXPECTED_CONSUMERS:
        raise EcosystemContractError(
            f"consumers must be exactly {EXPECTED_CONSUMERS!r}"
        )

    maturity_by_requirement: dict[str, str] = {}
    global_requirement_ids: set[str] = set()
    global_gap_ids: set[str] = set()
    for consumer in consumers:
        consumer_id = consumer["id"]
        if consumer["summary"] != EXPECTED_CONSUMER_SUMMARIES[consumer_id]:
            raise EcosystemContractError(
                f"{consumer_id}: summary differs from the fixed source-bounded statement"
            )
        snapshot_row = snapshot_rows.get(consumer_id)
        if snapshot_row is None:
            raise EcosystemContractError(
                f"{consumer_id}: historical snapshot row is missing"
            )
        if snapshot_row["release_claim_status"] != "not_claimed":
            raise EcosystemContractError(
                f"{consumer_id}: snapshot release claim must remain not_claimed"
            )
        requirement_sources = consumer["historical_requirement_sources"]
        require_sorted(
            requirement_sources,
            label=f"{consumer_id}.historical_requirement_sources",
        )
        if requirement_sources != EXPECTED_REQUIREMENT_SOURCES[consumer_id]:
            raise EcosystemContractError(
                f"{consumer_id}: historical requirement source selection differs "
                "from the fixed audit basis"
            )
        historical_evidence = consumer["historical_evidence"]
        if historical_evidence != EXPECTED_HISTORICAL_EVIDENCE[consumer_id]:
            raise EcosystemContractError(
                f"{consumer_id}: bounded historical evidence differs from the "
                "fixed source-scoped projection"
            )
        for evidence_record in historical_evidence:
            if evidence_record["source_paths"] != sorted(
                evidence_record["source_paths"]
            ):
                raise EcosystemContractError(
                    f"{consumer_id}.{evidence_record['id']}: historical source "
                    "paths must be sorted"
                )
            unknown_historical_paths = sorted(
                set(evidence_record["source_paths"]) - set(requirement_sources)
            )
            if unknown_historical_paths:
                raise EcosystemContractError(
                    f"{consumer_id}.{evidence_record['id']}: historical evidence "
                    f"uses unselected sources: {unknown_historical_paths!r}"
                )
        snapshot_source_hashes = {
            item["path"]: item["sha256"]
            for item in snapshot_row["contract_file_hashes"]
        }
        unknown_sources = sorted(set(requirement_sources) - set(snapshot_source_hashes))
        if unknown_sources:
            raise EcosystemContractError(
                f"{consumer_id}: requirement sources are absent from the historical "
                f"snapshot: {unknown_sources!r}"
            )

        requirements = consumer["requirements"]
        gaps = consumer["gaps"]
        require_sorted(
            requirements,
            label=f"{consumer_id}.requirements",
            key=lambda requirement: requirement["id"],
        )
        require_sorted(
            gaps,
            label=f"{consumer_id}.gaps",
            key=lambda gap: gap["id"],
        )
        requirement_by_id = {requirement["id"]: requirement for requirement in requirements}
        gap_by_id = {gap["id"]: gap for gap in gaps}
        if len(requirement_by_id) != len(requirements):
            raise EcosystemContractError(f"{consumer_id}: duplicate requirement ID")
        if len(gap_by_id) != len(gaps):
            raise EcosystemContractError(f"{consumer_id}: duplicate gap ID")
        overlap = global_requirement_ids & set(requirement_by_id)
        if overlap:
            raise EcosystemContractError(
                f"requirement IDs must be globally unique: {sorted(overlap)!r}"
            )
        overlap = global_gap_ids & set(gap_by_id)
        if overlap:
            raise EcosystemContractError(
                f"gap IDs must be globally unique: {sorted(overlap)!r}"
            )
        global_requirement_ids.update(requirement_by_id)
        global_gap_ids.update(gap_by_id)

        missing_by_requirement: dict[str, set[str]] = {}
        cited_requirement_sources: set[str] = set()
        for requirement in requirements:
            requirement_id = requirement["id"]
            label = f"{consumer_id}.{requirement_id}"
            historical_source_paths = requirement["historical_source_paths"]
            require_sorted(
                historical_source_paths,
                label=f"{label}.historical_source_paths",
            )
            unknown_historical_sources = sorted(
                set(historical_source_paths) - set(requirement_sources)
            )
            if unknown_historical_sources:
                raise EcosystemContractError(
                    f"{label}: requirement cites sources outside the fixed "
                    f"historical selection: {unknown_historical_sources!r}"
                )
            cited_requirement_sources.update(historical_source_paths)
            maturity_by_requirement[requirement_id] = validate_requirement_methods(
                requirement,
                methods,
                families,
                set(assurance_by_family),
                gap_by_id,
                label=label,
            )
            missing = validate_evidence(
                root,
                requirement,
                methods,
                assurance_by_family,
                label=label,
            )
            missing_by_requirement[requirement_id] = missing
            gap_ids = requirement["gap_ids"]
            if missing and not gap_ids:
                raise EcosystemContractError(
                    f"{label}: missing evidence must be assigned to at least one gap"
                )
            if not missing and gap_ids:
                raise EcosystemContractError(
                    f"{label}: gap IDs exist although no evidence class is missing"
                )
            unknown_gaps = sorted(set(gap_ids) - set(gap_by_id))
            if unknown_gaps:
                raise EcosystemContractError(
                    f"{label}: unknown gap IDs: {unknown_gaps!r}"
                )
            if requirement["local_method_maturity"] == "unavailable" and (
                "implementation-contract" not in missing
            ):
                raise EcosystemContractError(
                    f"{label}: unavailable maturity must record the missing implementation"
                )
            if requirement["local_method_maturity"] == "retained-boundary":
                dispositions = {
                    gap_by_id[gap_id]["disposition"] for gap_id in gap_ids
                }
                if "RETAINED_BOUNDARY" not in dispositions:
                    raise EcosystemContractError(
                        f"{label}: retained boundary lacks a RETAINED_BOUNDARY gap"
                    )

            for field in ("need", "title"):
                reject_affirmative_overclaim(
                    requirement[field],
                    label=f"{label}.{field}",
                )
            for field in ("assumptions", "limitations"):
                for index, value in enumerate(requirement[field]):
                    reject_affirmative_overclaim(
                        value,
                        label=f"{label}.{field}[{index}]",
                    )

        uncited_sources = sorted(
            set(requirement_sources) - cited_requirement_sources
        )
        if uncited_sources:
            raise EcosystemContractError(
                f"{consumer_id}: selected historical sources are not cited by "
                f"any requirement: {uncited_sources!r}"
            )

        linked_missing: dict[str, set[str]] = defaultdict(set)
        reverse_gap_ids: dict[str, list[str]] = defaultdict(list)
        for gap in gaps:
            gap_id = gap["id"]
            label = f"{consumer_id}.{gap_id}"
            require_sorted(
                gap["affected_requirement_ids"],
                label=f"{label}.affected_requirement_ids",
            )
            require_sorted(
                gap["evidence_paths"],
                label=f"{label}.evidence_paths",
            )
            require_sorted(
                gap["missing_evidence_classes"],
                label=f"{label}.missing_evidence_classes",
            )
            expected_owner = DISPOSITION_OWNER[gap["disposition"]]
            if gap["owner"] != expected_owner:
                raise EcosystemContractError(
                    f"{label}: owner {gap['owner']!r} disagrees with "
                    f"{gap['disposition']!r}"
                )
            unknown_requirements = sorted(
                set(gap["affected_requirement_ids"]) - set(requirement_by_id)
            )
            if unknown_requirements:
                raise EcosystemContractError(
                    f"{label}: unknown requirement IDs: {unknown_requirements!r}"
                )
            expected_priority = min(
                (
                    requirement_by_id[requirement_id]["priority"]
                    for requirement_id in gap["affected_requirement_ids"]
                ),
                key=lambda priority: PRIORITY_RANK[priority],
            )
            if gap["priority"] != expected_priority:
                raise EcosystemContractError(
                    f"{label}: gap priority must match the highest affected priority"
                )
            missing_classes = set(gap["missing_evidence_classes"])
            for requirement_id in gap["affected_requirement_ids"]:
                if not missing_classes <= missing_by_requirement[requirement_id]:
                    raise EcosystemContractError(
                        f"{label}: gap assigns evidence that {requirement_id} "
                        "does not mark missing"
                    )
                linked_missing[requirement_id].update(missing_classes)
                reverse_gap_ids[requirement_id].append(gap_id)
            for index, path in enumerate(gap["evidence_paths"]):
                safe_repo_file(
                    root,
                    path,
                    label=f"{label}.evidence_paths[{index}]",
                )
            if gap["priority"] == "P0" and (
                not gap["evidence_paths"] or not gap["negative_tests"]
            ):
                raise EcosystemContractError(
                    f"{label}: P0 gaps require evidence paths and negative tests"
                )
            reject_affirmative_overclaim(
                gap["statement"],
                label=f"{label}.statement",
            )
            for index, challenge in enumerate(gap["negative_tests"]):
                reject_affirmative_overclaim(
                    challenge,
                    label=f"{label}.negative_tests[{index}]",
                )

        for requirement_id, requirement in requirement_by_id.items():
            if linked_missing[requirement_id] != missing_by_requirement[requirement_id]:
                raise EcosystemContractError(
                    f"{consumer_id}.{requirement_id}: linked gaps do not account "
                    "for every missing evidence class"
                )
            if sorted(reverse_gap_ids[requirement_id]) != requirement["gap_ids"]:
                raise EcosystemContractError(
                    f"{consumer_id}.{requirement_id}: forward and reverse gap links differ"
                )

    forbidden_present = {
        "consumer-commit-integration",
        "holdout-benchmark",
        "independent-review",
        "statistical-validation",
    }
    for consumer in consumers:
        for requirement in consumer["requirements"]:
            present_classes = {
                record["class"] for record in requirement["evidence"]["present"]
            }
            prohibited = sorted(present_classes & forbidden_present)
            if prohibited:
                raise EcosystemContractError(
                    f"{consumer['id']}.{requirement['id']}: current contract cannot "
                    f"mark unrecorded qualification evidence present: {prohibited!r}"
                )

    return (
        maturity_by_requirement,
        snapshot_rows,
        integration_claims,
        assurance_by_family,
    )


def code_list(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "None"


def text_list(values: list[str]) -> str:
    return "; ".join(value.rstrip(".") for value in values) if values else "None"


def render_markdown(
    contract: dict[str, Any],
    maturity_by_requirement: dict[str, str],
    snapshot_rows: dict[str, dict[str, Any]],
    integration_claims: dict[str, str],
    assurance_by_family: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# Ecosystem capability and evidence-gap contract",
        "",
        "## Project classification",
        "",
        contract["claim_boundary"],
        "",
        contract["inventory_scope"],
        "",
        "The machine-readable authority is "
        "[`ecosystem-capabilities.json`](ecosystem-capabilities.json). "
        "The checker generates this file from that authority.",
        "",
        "The checker preserves the historical/base semantic projection at SHA-256 "
        f"`{contract['semantic_projection_sha256']}`. That custody projection covers "
        "the inventory boundary, all consumer semantics and evidence records, and "
        "the reviewed base authority records. For its digest only, the three moving "
        "current authority digests are replaced by their historical/base values.",
        "",
        "The checker separately binds the inventory boundary plus all consumer "
        "records to SHA-256 "
        f"`{EXPECTED_CONSUMER_INVENTORY_PROJECTION_SHA256}`. It independently "
        "hashes the exact canonical bytes of every current authority in the table "
        "below and requires each reviewed KSG-revision digest, live byte digest, "
        "path, role, and schema identity to match. Refreshing an authority digest "
        "does not claim current consumer compatibility or integration.",
        "",
        "## Bound authorities",
        "",
        "| Authority | Path | SHA-256 | Role |",
        "|---|---|---|---|",
    ]
    for binding in contract["source_bindings"]:
        lines.append(
            f"| `{binding['id']}` | `{binding['path']}` | "
            f"`{binding['sha256']}` | {binding['role']} |"
        )
    lines.extend(
        [
            "",
            "The repository snapshot records historical identity evidence. "
            "It does not prove API compatibility or current repository state.",
            "",
            "## Local method maturity labels",
            "",
            "| Label | Meaning |",
            "|---|---|",
        ]
    )
    for definition in contract["local_method_maturity_definitions"]:
        lines.append(f"| `{definition['id']}` | {definition['meaning']} |")
    lines.extend(
        [
            "",
            "## Evidence classes",
            "",
            "| Class | Meaning |",
            "|---|---|",
        ]
    )
    for definition in contract["evidence_class_definitions"]:
        lines.append(f"| `{definition['id']}` | {definition['meaning']} |")

    for consumer in contract["consumers"]:
        historical = snapshot_rows[consumer["id"]]
        source_hashes = {
            item["path"]: item["sha256"]
            for item in historical["contract_file_hashes"]
        }
        lines.extend(
            [
                "",
                f"## {consumer['id'].capitalize()}",
                "",
                consumer["summary"],
                "",
                f"- Integration claim status: `{integration_claims[consumer['id']]}`.",
                f"- Historical commit: `{historical['commit_sha']}`.",
                f"- Historical tree: `{historical['tree_sha']}`.",
                "- Snapshot scope: `historical_repository_identity_only`.",
                "",
                "### Historical requirement sources",
                "",
                "| Path | SHA-256 |",
                "|---|---|",
            ]
        )
        for path in consumer["historical_requirement_sources"]:
            lines.append(f"| `{path}` | `{source_hashes[path]}` |")
        if consumer["historical_evidence"]:
            lines.extend(
                [
                    "",
                    "### Bounded historical integration evidence",
                    "",
                    "These records describe exact historical fixtures only. They do not "
                    "change the current integration claim status.",
                    "",
                    "| ID | pid-rs revision | Sources | Scope | Limitation |",
                    "|---|---|---|---|---|",
                ]
            )
            for record in consumer["historical_evidence"]:
                lines.append(
                    f"| `{record['id']}` | `{record['pid_rs_revision']}` | "
                    f"{code_list(record['source_paths'])} | {record['scope']} | "
                    f"{record['limitation']} |"
                )
        lines.extend(
            [
                "",
                "### Requirements",
                "",
                "| ID | Priority | Local method maturity | Missing evidence | Gaps |",
                "|---|---|---|---|---|",
            ]
        )
        for requirement in consumer["requirements"]:
            lines.append(
                f"| `{requirement['id']}` | `{requirement['priority']}` | "
                f"`{maturity_by_requirement[requirement['id']]}` | "
                f"{code_list(requirement['evidence']['missing_classes'])} | "
                f"{code_list(requirement['gap_ids'])} |"
            )
        for requirement in consumer["requirements"]:
            lines.extend(
                [
                    "",
                    f"#### {requirement['id']}: {requirement['title']}",
                    "",
                    requirement["need"],
                    "",
                    f"- Primary methods: {code_list(requirement['primary_method_ids'])}.",
                    f"- Validation methods: {code_list(requirement['validation_method_ids'])}.",
                    f"- Boundary methods: {code_list(requirement['boundary_method_ids'])}.",
                    f"- Release families: {code_list(requirement['release_scope_family_ids'])}.",
                    (
                        "- Historical sources: "
                        f"{code_list(requirement['historical_source_paths'])}."
                    ),
                    f"- Assumptions: {text_list(requirement['assumptions'])}.",
                    f"- Limitations: {text_list(requirement['limitations'])}.",
                ]
            )
            for record in requirement["evidence"]["present"]:
                lines.append(
                    f"- Present `{record['class']}` evidence: "
                    f"{code_list(record['paths'])}."
                )
                layer_id = (
                    "definition"
                    if record["class"] == "definition-provenance"
                    else ASSURANCE_LAYER_FOR_CLASS.get(record["class"])
                )
                if layer_id is not None:
                    for family_id in requirement["release_scope_family_ids"]:
                        layer = assurance_by_family[family_id]["layers"][layer_id]
                        assurance = layer["assurance"]
                        gap_ids = [gap["id"] for gap in layer["gaps"]]
                        lines.append(
                            f"  - `{family_id}/{layer_id}`: "
                            f"`{assurance['status']}` / "
                            f"`{assurance['evidence_tier']}`; open or retained "
                            f"gap IDs: {code_list(gap_ids)}."
                        )

            if requirement["release_scope_family_ids"]:
                lines.extend(
                    [
                        "",
                        "Bound assurance layers:",
                        "",
                        "| Family | Layer | Status | Tier | Gap IDs |",
                        "|---|---|---|---|---|",
                    ]
                )
                for family_id in requirement["release_scope_family_ids"]:
                    for layer_id, layer in assurance_by_family[family_id][
                        "layers"
                    ].items():
                        assurance = layer["assurance"]
                        lines.append(
                            f"| `{family_id}` | `{layer_id}` | "
                            f"`{assurance['status']}` | "
                            f"`{assurance['evidence_tier']}` | "
                            f"{code_list([gap['id'] for gap in layer['gaps']])} |"
                        )

        lines.extend(
            [
                "",
                "### Open gaps and retained boundaries",
                "",
                "| ID | Priority | Disposition | Owner | Missing evidence | Statement |",
                "|---|---|---|---|---|---|",
            ]
        )
        for gap in consumer["gaps"]:
            lines.append(
                f"| `{gap['id']}` | `{gap['priority']}` | "
                f"`{gap['disposition']}` | `{gap['owner']}` | "
                f"{code_list(gap['missing_evidence_classes'])} | "
                f"{gap['statement']} |"
            )
        for gap in consumer["gaps"]:
            lines.extend(
                [
                    "",
                    f"#### {gap['id']}",
                    "",
                    f"- Evidence paths: {code_list(gap['evidence_paths'])}.",
                    "- Required negative challenges:",
                    "",
                ]
            )
            lines.extend(f"  - {challenge}" for challenge in gap["negative_tests"])

    lines.extend(
        [
            "",
            "## Claims not made",
            "",
        ]
    )
    lines.extend(f"- {claim}" for claim in contract["claims_not_made"])
    lines.extend(
        [
            "",
            "The release scope also contains `external-authority`. "
            "This contract excludes it because it is not one of the four audited consumers. "
            "Its release-scope status remains `not_claimed`.",
            "",
        ]
    )
    return "\n".join(lines)


def check_or_write_markdown(
    markdown_path: Path,
    rendered: str,
    *,
    write: bool,
) -> None:
    if write:
        markdown_path.write_text(rendered, encoding="utf-8")
        return
    try:
        observed = markdown_path.read_text(encoding="utf-8")
    except OSError as error:
        raise EcosystemContractError(
            f"cannot read generated Markdown {markdown_path}: {error}"
        ) from error
    if observed != rendered:
        raise EcosystemContractError(
            f"{markdown_path} is stale; run "
            "`python3 scripts/check-ecosystem-capabilities.py --write`"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--write",
        action="store_true",
        help="write the generated Markdown after all checks pass",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        contract = load_json(args.contract, canonical=True)
        schema = load_json(args.schema, canonical=True)
        (
            maturity,
            snapshot_rows,
            integration_claims,
            assurance_by_family,
        ) = validate_contract(
            args.root.resolve(strict=True), contract, schema
        )
        rendered = render_markdown(
            contract,
            maturity,
            snapshot_rows,
            integration_claims,
            assurance_by_family,
        )
        check_or_write_markdown(args.markdown, rendered, write=args.write)
    except EcosystemContractError as error:
        print(f"ecosystem capability check failed: {error}", file=sys.stderr)
        return 1
    action = "wrote" if args.write else "validated"
    print(
        f"{action} ecosystem capability contract for "
        f"{len(contract['consumers'])} consumers"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
