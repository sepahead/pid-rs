#!/usr/bin/env python3
"""Generate non-authoritative typed-view revision 1 from assurance-registry revision 2.

The checked-in assurance registry remains the authority.  This view adds queryable
correspondence-edge, evidence-class, and reviewer-scope labels without upgrading any
claim or treating inventory, model output, formal artifacts, tests, or tag facts as
interchangeable forms of review.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import types
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-assurance-registry-typed-view-v1.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent


def load_schema_validator() -> tuple[type[ValueError], Any]:
    """Load the exact validator source without relying on sys.path or bytecode caches."""
    path = ROOT / "scripts/json_schema_subset.py"
    before = os.lstat(path)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise SystemExit("JSON-schema validator is not a single-link regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        source = bytearray()
        while chunk := os.read(descriptor, 1024 * 1024):
            source.extend(chunk)
        closed = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = os.lstat(path)

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_nlink,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if not (
        identity(before) == identity(opened) == identity(closed) == identity(after)
        and len(source) == before.st_size
    ):
        raise SystemExit("JSON-schema validator changed during exact-source read")
    module = types.ModuleType("assurance_typed_view_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source),
        str(path),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


SchemaValidationError, validate_json_schema = load_schema_validator()
DEFAULT_VIEW = ROOT / "audit/evidence/assurance-registry-typed-view-v1.json"
DEFAULT_SCHEMA = ROOT / "audit/schemas/assurance-registry-typed-view-v1.schema.json"
VIEW_SCHEMA = "pid-rs/assurance-registry-typed-view"
VIEW_REVISION = 1
GENERATOR = "scripts/check-assurance-registry-typed-view-v1.py"

LAYER_ORDER = (
    "definition",
    "exact_algebra",
    "rust_refinement",
    "floating_point_numerical_behavior",
    "statistical_application_validity",
)
EDGE_SPECS = (
    (
        "source_to_repository_specification",
        ("definition",),
        "Transcription of formulas, units, domains, support, and source errata.",
    ),
    (
        "repository_specification_to_formal_model",
        ("exact_algebra",),
        "Correspondence between the repository statement and a formal statement.",
    ),
    (
        "formal_model_to_executable_algorithm",
        (),
        "Coverage of branches, indexing, support logic, and termination by the formal model.",
    ),
    (
        "executable_algorithm_to_language_and_numeric_execution",
        ("rust_refinement", "floating_point_numerical_behavior"),
        "Refinement to Rust/Python plus the separately recorded finite-precision boundary.",
    ),
    (
        "implementation_output_to_scientific_estimand_application",
        ("statistical_application_validity",),
        "Sampling, support, calibration, and application-domain validity.",
    ),
)
EVIDENCE_CLASS_DEFINITIONS = {
    "documentation": (
        "Narrative, specification, source, or metadata record; not review completion."
    ),
    "execution_evidence": (
        "A test, checker, fixture, or execution receipt bounded to its declared inputs."
    ),
    "formal_proof": (
        "A Lean or SMT artifact bounded to its encoded statement and trusted toolchain."
    ),
    "human_review": (
        "A named human review disposition; absent unless a record explicitly supplies it."
    ),
    "inventory": (
        "A file/object inventory; it does not imply that lines or mathematics were reviewed."
    ),
    "line_review": (
        "A blob-bound line/code review disposition; absent unless explicitly recorded."
    ),
    "model_review": (
        "Advisory output from a model; not human, institutional, or independent review."
    ),
    "tag_release_fact": (
        "A Git tag or release-state fact; not a scientific or code-review disposition."
    ),
}
INDEPENDENCE_DIMENSIONS = (
    "semantic",
    "implementation",
    "custody",
    "institutional",
    "data",
)


class ViewError(RuntimeError):
    """Typed-view validation failed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", type=Path, default=DEFAULT_VIEW)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--emit",
        action="store_true",
        help="write the deterministic expected view to stdout instead of validating",
    )
    return parser.parse_args()


def reject_constant(value: str) -> Any:
    raise ViewError(f"non-finite JSON constant is forbidden: {value}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                indent=2,
                sort_keys=True,
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ViewError(f"cannot canonicalize JSON: {error}") from error


def compact_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ViewError(f"cannot canonicalize projection: {error}") from error


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path, label: str, *, require_canonical: bool) -> tuple[Any, bytes]:
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ViewError(f"{label} is not a regular file: {path}")
        raw = path.read_bytes()
    except OSError as error:
        raise ViewError(f"cannot read {label} {path}: {error}") from error
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, ViewError) as error:
        raise ViewError(f"cannot parse {label} {path}: {error}") from error
    if require_canonical and raw != canonical_bytes(value):
        raise ViewError(f"{label} is not canonical sorted UTF-8 JSON: {path}")
    return value, raw


def relative_path(path: Path, root: Path) -> str:
    try:
        relative = path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ViewError(f"artifact escapes repository root: {path}: {error}") from error
    rendered = relative.as_posix()
    if (
        rendered != PurePosixPath(rendered).as_posix()
        or ".." in PurePosixPath(rendered).parts
    ):
        raise ViewError(
            f"artifact path is not canonical repository-relative POSIX: {rendered}"
        )
    return rendered


def classify_evidence_path(path: str) -> str:
    suffix = PurePosixPath(path).suffix
    if suffix in {".lean", ".smt2"}:
        return "formal_proof"
    if (
        "/tests/" in f"/{path}"
        or "/fixtures/" in f"/{path}"
        or path.startswith("scripts/check-")
        or "receipt" in PurePosixPath(path).name.lower()
    ):
        return "execution_evidence"
    return "documentation"


def projection_sha256(values: list[str]) -> str:
    return sha256_bytes(compact_bytes(values))


def edge_status(component_statuses: list[str]) -> str:
    if not component_statuses:
        return "not_explicitly_recorded"
    if all(value == "NOT_APPLICABLE" for value in component_statuses):
        return "not_applicable"
    if any(value in {"NOT_CLAIMED", "UNPROVED"} for value in component_statuses):
        return "open_or_not_claimed"
    if any(value == "ASSUMPTION_GATED" for value in component_statuses):
        return "assumption_gated"
    if any(value == "BOUNDED" for value in component_statuses):
        return "bounded"
    if any(value == "TESTED" for value in component_statuses):
        return "bounded_execution"
    if all(value == "DOCUMENTED" for value in component_statuses):
        return "documented"
    raise ViewError(f"unmapped assurance status combination: {component_statuses!r}")


def correspondence_status(edge_index: int, component_statuses: list[str]) -> str:
    """Fail closed on correspondence rather than promoting component evidence.

    The source registry records evidence *inside* five assurance layers.  Except for bounded
    executable evidence on edge four and declared assumptions on edge five, that is not itself a
    separately reviewed correspondence relation between adjacent objects.
    """
    if edge_index in {1, 2, 3}:
        return "not_established"
    if component_statuses and all(
        value == "NOT_APPLICABLE" for value in component_statuses
    ):
        return "not_applicable"
    if edge_index == 4 and any(
        value in {"BOUNDED", "TESTED"} for value in component_statuses
    ):
        return "bounded_nontransitive"
    if edge_index == 5 and any(
        value == "ASSUMPTION_GATED" for value in component_statuses
    ):
        return "assumption_only"
    return "not_established"


def load_ledger(path: Path) -> tuple[list[dict[str, str]], bytes]:
    try:
        if not stat.S_ISREG(path.lstat().st_mode):
            raise ViewError(f"review ledger is not a regular file: {path}")
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ViewError(f"cannot read UTF-8 review ledger {path}: {error}") from error
    if "\r" in text or not text.endswith("\n"):
        raise ViewError("review ledger must use LF and end with a newline")
    try:
        rows = list(csv.DictReader(io.StringIO(text, newline="")))
    except csv.Error as error:
        raise ViewError(f"cannot parse review ledger: {error}") from error
    if not rows or any(None in row for row in rows):
        raise ViewError("review ledger is empty or structurally malformed")
    required = {"path", "reviewer", "review_status"}
    if not required.issubset(rows[0]):
        raise ViewError("review ledger lacks path/reviewer/review_status columns")
    paths = [row["path"] for row in rows]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ViewError("review ledger paths must be unique and sorted")
    return rows, raw


def make_review_records(
    root: Path,
    ledger_path: Path,
    model_path: Path,
    ledger_rows: list[dict[str, str]],
    ledger_raw: bytes,
    model_raw: bytes,
) -> list[dict[str, Any]]:
    inventoried = len(ledger_rows)
    line_reviewed = sum(
        row["review_status"] not in {"", "INVENTORIED_NOT_REVIEWED"}
        for row in ledger_rows
    )
    assigned = sum(row["reviewer"] not in {"", "UNASSIGNED"} for row in ledger_rows)
    if line_reviewed != 0 or assigned != 0:
        raise ViewError(
            "typed view v1 is pinned to the all-unreviewed v0.9.0 inventory; "
            "create a new view revision when review dispositions exist"
        )
    not_claimed = {dimension: "not_claimed" for dimension in INDEPENDENCE_DIMENSIONS}
    return [
        {
            "artifact": relative_path(ledger_path, root),
            "artifact_sha256": sha256_bytes(ledger_raw),
            "evidence_class": "inventory",
            "id": "REVIEW-INVENTORY-V0_9_0",
            "independence": dict(not_claimed),
            "object_count": inventoried,
            "reviewer_class": "none_recorded",
            "scope_precision": "exact_tag_tree_inventory",
            "status": "inventoried_not_reviewed",
        },
        {
            "artifact": relative_path(model_path, root),
            "artifact_sha256": sha256_bytes(model_raw),
            "evidence_class": "model_review",
            "id": "REVIEW-EXTERNAL-MODEL-2026_08_12",
            "independence": dict(not_claimed),
            "object_count": 1,
            "reviewer_class": "external_model",
            "scope_precision": "self_reported_partial_online_repository_review",
            "status": "advisory_not_independent_not_human",
        },
        {
            "artifact": relative_path(ledger_path, root),
            "artifact_sha256": sha256_bytes(ledger_raw),
            "evidence_class": "line_review",
            "id": "REVIEW-LINE-V0_9_0",
            "independence": dict(not_claimed),
            "object_count": line_reviewed,
            "reviewer_class": "none_recorded",
            "scope_precision": "exact_tag_tree_ledger",
            "status": "absent",
        },
        {
            "artifact": relative_path(ledger_path, root),
            "artifact_sha256": sha256_bytes(ledger_raw),
            "evidence_class": "human_review",
            "id": "REVIEW-HUMAN-V0_9_0",
            "independence": dict(not_claimed),
            "object_count": assigned,
            "reviewer_class": "none_recorded",
            "scope_precision": "exact_tag_tree_ledger",
            "status": "absent",
        },
    ]


def make_expected(root: Path) -> dict[str, Any]:
    assurance_path = root / "audit/evidence/assurance-registry.json"
    ledger_path = root / "audit/evidence/FILE_REVIEW_LEDGER.csv"
    model_path = root / "audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md"
    assurance, assurance_raw = load_json(
        assurance_path, "assurance registry", require_canonical=True
    )
    if not isinstance(assurance, dict):
        raise ViewError("assurance registry root must be an object")
    if (
        assurance.get("schema") != "pid-rs/assurance-registry"
        or assurance.get("schema_revision") != 2
    ):
        raise ViewError("typed view v1 requires assurance-registry revision 2")
    families = assurance.get("families")
    if not isinstance(families, list) or len(families) != 37:
        raise ViewError("typed view v1 requires exactly 37 release-scope families")
    ledger_rows, ledger_raw = load_ledger(ledger_path)
    try:
        if not stat.S_ISREG(model_path.lstat().st_mode):
            raise ViewError(
                f"external model review is not a regular file: {model_path}"
            )
        model_raw = model_path.read_bytes()
        model_raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ViewError(
            f"cannot read external model review {model_path}: {error}"
        ) from error

    typed_families: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    for family_index, family in enumerate(families):
        if not isinstance(family, dict):
            raise ViewError(f"family {family_index} is not an object")
        family_id = family.get("family_id")
        layers = family.get("layers")
        if (
            not isinstance(family_id, str)
            or not family_id
            or family_id in seen_families
        ):
            raise ViewError(f"invalid or duplicate family_id at index {family_index}")
        seen_families.add(family_id)
        if not isinstance(layers, dict) or tuple(sorted(layers)) != tuple(
            sorted(LAYER_ORDER)
        ):
            raise ViewError(f"{family_id}: source layer set changed")

        edges: list[dict[str, Any]] = []
        for edge_index, (kind, component_layers, meaning) in enumerate(EDGE_SPECS, 1):
            components: list[dict[str, Any]] = []
            evidence_paths: list[str] = []
            evidence_classes: set[str] = set()
            statuses: list[str] = []
            for layer_name in component_layers:
                layer = layers.get(layer_name)
                assurance_record = (
                    layer.get("assurance") if isinstance(layer, dict) else None
                )
                if not isinstance(assurance_record, dict):
                    raise ViewError(
                        f"{family_id}/{layer_name}: assurance record is absent"
                    )
                assurance_id = assurance_record.get("id")
                claim = assurance_record.get("claim")
                status = assurance_record.get("status")
                tier = assurance_record.get("evidence_tier")
                paths = assurance_record.get("evidence")
                if (
                    not isinstance(assurance_id, str)
                    or not isinstance(claim, str)
                    or not isinstance(status, str)
                    or not isinstance(tier, str)
                    or not isinstance(paths, list)
                    or any(not isinstance(path, str) for path in paths)
                ):
                    raise ViewError(
                        f"{family_id}/{layer_name}: malformed assurance record"
                    )
                if paths != sorted(paths) or len(paths) != len(set(paths)):
                    raise ViewError(
                        f"{family_id}/{layer_name}: evidence paths are not sorted unique"
                    )
                statuses.append(status)
                evidence_paths.extend(paths)
                evidence_classes.update(classify_evidence_path(path) for path in paths)
                components.append(
                    {
                        "claim_sha256": sha256_bytes(claim.encode("utf-8")),
                        "evidence_path_count": len(paths),
                        "evidence_paths_sha256": projection_sha256(paths),
                        "layer": layer_name,
                        "source_assurance_id": assurance_id,
                        "source_evidence_tier": tier,
                        "source_pointer": (
                            f"/families/{family_index}/layers/{layer_name}/assurance"
                        ),
                        "source_status": status,
                    }
                )
            unique_paths = sorted(set(evidence_paths))
            edges.append(
                {
                    "components": components,
                    "correspondence_status": correspondence_status(
                        edge_index, statuses
                    ),
                    "correspondence_edge": kind,
                    "evidence_classes": sorted(evidence_classes),
                    "evidence_path_count": len(unique_paths),
                    "evidence_paths_sha256": projection_sha256(unique_paths),
                    "id": f"EDGE-F{family_index + 1:03d}-E{edge_index}",
                    "meaning": meaning,
                    "review_record_ids": [],
                    "source_component_status": edge_status(statuses),
                }
            )
        typed_families.append(
            {
                "definition_revision": family.get("definition_revision"),
                "edges": edges,
                "estimator_revision": family.get("estimator_revision"),
                "family_id": family_id,
                "software_stability": family.get("software_stability"),
                "transitive_five_edge_chain_claimed": False,
            }
        )

    release_boundary = assurance.get("release_boundary")
    if not isinstance(release_boundary, dict):
        raise ViewError("assurance registry release_boundary is malformed")
    tagged_commit = release_boundary.get("tagged_commit_sha")
    tag_object = release_boundary.get("tag_object_sha")
    tag = release_boundary.get("tag")
    source_offer_status = release_boundary.get("v0_9_source_offer_status")
    if not all(
        isinstance(value, str)
        for value in (tagged_commit, tag_object, tag, source_offer_status)
    ):
        raise ViewError("release boundary tag fields are malformed")

    return {
        "derived_view_only": True,
        "evidence_class_definitions": EVIDENCE_CLASS_DEFINITIONS,
        "families": typed_families,
        "generated_by": GENERATOR,
        "nonimplications": [
            "The view is not an authority independent of audit/evidence/assurance-registry.json.",
            "No transitive paper-to-application correctness chain is established.",
            "Inventory is not line review; model review is not human or independent review.",
            "Formal artifacts do not by themselves establish source correspondence, implementation refinement, or application validity.",
            "Execution evidence remains bounded to its declared inputs, toolchains, and assumptions.",
            "Git tag and release facts do not establish review, authenticity, or scientific validity.",
        ],
        "release_facts": [
            {
                "evidence_class": "tag_release_fact",
                "id": "RELEASE-V0_9_0",
                "review_completion_inferred": False,
                "source_offer_status": source_offer_status,
                "status_semantics": (
                    "historical tag published for source review; no completed line or human review is inferred"
                ),
                "tag": tag,
                "tag_object_sha": tag_object,
                "tagged_commit_sha": tagged_commit,
            }
        ],
        "review_records": make_review_records(
            root, ledger_path, model_path, ledger_rows, ledger_raw, model_raw
        ),
        "schema": VIEW_SCHEMA,
        "schema_revision": VIEW_REVISION,
        "source_registry": {
            "path": relative_path(assurance_path, root),
            "schema": assurance["schema"],
            "schema_revision": assurance["schema_revision"],
            "sha256": sha256_bytes(assurance_raw),
        },
        "transitive_chain_status": "not_established",
    }


def validate_view(value: Any, schema: Any, expected: dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise ViewError("typed-view schema root must be an object")
    try:
        validate_json_schema(value, schema, name="assurance-registry-typed-view-v1")
    except SchemaValidationError:
        raise
    if canonical_bytes(value) != canonical_bytes(expected):
        raise ViewError(
            "typed assurance view is stale or was edited independently; regenerate with "
            "python3 scripts/check-assurance-registry-typed-view-v1.py --emit"
        )
    family_count = len(expected["families"])
    edge_count = sum(len(family["edges"]) for family in expected["families"])
    if family_count != 37 or edge_count != 185:
        raise ViewError("typed view must contain exactly 37 families and 185 edges")
    if any(
        family["transitive_five_edge_chain_claimed"] for family in expected["families"]
    ):
        raise ViewError("typed view must not claim a transitive five-edge chain")
    missing = [
        family["family_id"]
        for family in expected["families"]
        if family["edges"][2]["source_component_status"] != "not_explicitly_recorded"
    ]
    if missing:
        raise ViewError(f"formal-to-executable gap was hidden for: {missing}")
    established = [
        edge["id"]
        for family in expected["families"]
        for edge in family["edges"]
        if edge["correspondence_status"]
        not in {
            "assumption_only",
            "bounded_nontransitive",
            "not_applicable",
            "not_established",
        }
    ]
    if established:
        raise ViewError(
            f"unknown correspondence status escaped validation: {established}"
        )
    review_by_class = {
        record["evidence_class"]: record for record in expected["review_records"]
    }
    if review_by_class["inventory"]["object_count"] != 186:
        raise ViewError("v0.9.0 inventory count changed; issue a new view revision")
    if review_by_class["line_review"]["object_count"] != 0:
        raise ViewError("line review must not be inferred from inventory")
    if review_by_class["human_review"]["object_count"] != 0:
        raise ViewError("human review must not be inferred from inventory")


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=True)
    expected = make_expected(root)
    if args.emit:
        sys.stdout.buffer.write(canonical_bytes(expected))
        return 0
    schema, _ = load_json(args.schema, "typed-view schema", require_canonical=True)
    view, raw = load_json(args.view, "typed assurance view", require_canonical=True)
    validate_view(view, schema, expected)
    if raw != canonical_bytes(expected):
        raise ViewError("typed assurance view byte comparison changed unexpectedly")
    print(
        "OK: typed assurance view binds 37 release-scope families and 185 five-edge records; "
        "inventory/model/formal/execution/release classes remain non-interchangeable"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ViewError, SchemaValidationError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
