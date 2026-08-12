#!/usr/bin/env python3
"""Generate and check the compact stable-first method-catalog view."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types
from typing import Any

if sys.version_info < (3, 11):
    raise SystemExit("check-methods-summary.py requires Python 3.11+")


ROOT = Path(__file__).resolve().parent.parent
CATALOG = "method-catalog.json"
CATALOG_SCHEMA = "audit/schemas/method-catalog.schema.json"
VIEW = "audit/evidence/methods-summary-v1.json"
VIEW_SCHEMA = "audit/schemas/methods-summary-v1.schema.json"
MARKDOWN = "METHODS_SUMMARY.md"
GENERATOR = "scripts/check-methods-summary.py"
STATUS_ORDER = (
    "stable",
    "experimental",
    "research-only",
    "external-validation-only",
    "unsupported",
)


class SummaryError(RuntimeError):
    """The compact method view is stale or invalid."""


def load_schema_validator() -> tuple[type[ValueError], Any]:
    """Compile the exact checked-in validator source without sys.path imports."""
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
    module = types.ModuleType("methods_summary_json_schema_subset")
    module.__file__ = str(path)
    code = compile(
        bytes(source), str(path), "exec", dont_inherit=True, optimize=sys.flags.optimize
    )
    exec(code, module.__dict__)
    return module.SchemaValidationError, module.validate


SchemaValidationError, validate_json_schema = load_schema_validator()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--emit-json", action="store_true")
    parser.add_argument("--emit-markdown", action="store_true")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if sum((arguments.emit_json, arguments.emit_markdown, arguments.write)) > 1:
        parser.error("select at most one output mode")
    return arguments


def reject_constant(value: str) -> Any:
    raise SummaryError(f"non-finite JSON constant is forbidden: {value}")


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
        raise SummaryError(f"cannot canonicalize JSON: {error}") from error


def load_regular_bytes(path: Path, label: str) -> bytes:
    try:
        before = os.lstat(path)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise SummaryError(f"{label} is not a single-link regular file: {path}")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            raw = bytearray()
            while chunk := os.read(descriptor, 1024 * 1024):
                raw.extend(chunk)
            closed = os.fstat(descriptor)
        finally:
            os.close(descriptor)
        after = os.lstat(path)
    except OSError as error:
        raise SummaryError(f"cannot read {label} {path}: {error}") from error

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
        and len(raw) == before.st_size
    ):
        raise SummaryError(f"{label} changed during exact read: {path}")
    return bytes(raw)


def load_json(path: Path, label: str) -> tuple[Any, bytes]:
    raw = load_regular_bytes(path, label)
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, SummaryError) as error:
        raise SummaryError(f"cannot parse {label} {path}: {error}") from error
    if raw != canonical_bytes(value):
        raise SummaryError(f"{label} is not canonical sorted UTF-8 JSON: {path}")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def make_expected(root: Path) -> dict[str, Any]:
    catalog, catalog_raw = load_json(root / CATALOG, "method catalog")
    catalog_schema, _ = load_json(root / CATALOG_SCHEMA, "method-catalog schema")
    try:
        validate_json_schema(catalog, catalog_schema, name="method-catalog")
    except SchemaValidationError as error:
        raise SummaryError(str(error)) from error
    if (
        catalog.get("schema") != "pid-rs/method-catalog"
        or catalog.get("schema_revision") != 1
    ):
        raise SummaryError("unsupported method-catalog schema identity")
    methods = catalog.get("methods")
    if not isinstance(methods, list) or not methods:
        raise SummaryError("method catalog has no methods")
    rank = {status: index for index, status in enumerate(STATUS_ORDER)}
    ids = [method["id"] for method in methods]
    if len(ids) != len(set(ids)):
        raise SummaryError("method catalog contains duplicate method ids")
    unknown = sorted(
        {method["implementation_status"] for method in methods} - set(rank)
    )
    if unknown:
        raise SummaryError(f"unrecognized implementation status: {unknown}")
    rows = []
    for method in sorted(
        methods, key=lambda item: (rank[item["implementation_status"]], item["id"])
    ):
        rust = method["rust_entry_points"]
        python = method["python_entry_points"]
        rows.append(
            {
                "category": method["category"],
                "code_availability": method["code_availability"],
                "constraint_count": len(method["constraints"]),
                "definition_origin": method["definition_origin"],
                "depends_on": method["depends_on"],
                "feature_gates": method["cargo_features"],
                "id": method["id"],
                "implementation_origin": method["implementation_origin"],
                "implementation_status": method["implementation_status"],
                "public_surface": {
                    "python_count": len(python),
                    "python_examples": python[:2],
                    "rust_count": len(rust),
                    "rust_examples": rust[:2],
                },
                "scientific_novelty_claim": method["scientific_novelty_claim"],
                "summary": method["summary"],
                "title": method["title"],
                "validation": {
                    "evidence_path_count": len(method["validation"]["evidence_paths"]),
                    "level": method["validation"]["level"],
                },
            }
        )
    return {
        "derived_view_only": True,
        "detailed_view": "METHODS.md",
        "generated_by": GENERATOR,
        "nonimplications": [
            "This compact projection is not a competing method authority; method-catalog.json remains authoritative.",
            "A stable software label is not a claim of estimator consistency, calibration, application validity, or scientific novelty.",
            "A dependency, shared citation, binding, or similar name does not transfer an estimand, theorem, support premise, or validation result.",
            "Evidence counts and validation labels are inventory summaries; read the exhaustive row and exact artifacts before assigning credit.",
        ],
        "ordering": list(STATUS_ORDER),
        "rows": rows,
        "schema": "pid-rs/methods-summary",
        "schema_revision": 1,
        "scientific_claim_boundary": catalog["scientific_claim_boundary"],
        "source_catalog": {
            "path": CATALOG,
            "schema": catalog["schema"],
            "schema_revision": catalog["schema_revision"],
            "sha256": sha256(catalog_raw),
        },
    }


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def code_list(values: list[str], count: int) -> str:
    if not values:
        return f"none ({count})"
    rendered = ", ".join(f"`{markdown_escape(value)}`" for value in values)
    omitted = count - len(values)
    if omitted:
        rendered += f"; +{omitted} more"
    return rendered


def render_markdown(view: dict[str, Any]) -> str:
    lines = [
        "# Compact stable-first method view",
        "",
        "<!-- Generated by scripts/check-methods-summary.py; edit method-catalog.json instead. -->",
        "",
        "This is a non-authoritative navigation view of [`method-catalog.json`](method-catalog.json). "
        "The exhaustive generated record remains [`METHODS.md`](METHODS.md). A `stable` row names "
        "the catalog method/family status, not the stability of every displayed binding: entry "
        "points under `pid_core_rs.experimental.migration` remain experimental compatibility "
        "surfaces. Stability never means the scientific object is universally valid, calibrated, "
        "or appropriate for an application.",
        "",
        "Rows are ordered stable, experimental, research-only, external-validation-only, then "
        "unsupported. Counts are inventory only. Follow the detailed row before reviewing evidence.",
        "",
        "| Status | Method | Provenance | Surface (examples only) | Dependencies | Scope | Evidence index |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in view["rows"]:
        surface = row["public_surface"]
        features = ", ".join(f"`{item}`" for item in row["feature_gates"]) or "none"
        surface_text = (
            f"feature gates: {features}; Rust: "
            f"{code_list(surface['rust_examples'], surface['rust_count'])}; "
            f"Python: {code_list(surface['python_examples'], surface['python_count'])}"
        )
        dependencies = ", ".join(f"`{item}`" for item in row["depends_on"]) or "none"
        provenance = (
            f"definition `{row['definition_origin']}`; implementation "
            f"`{row['implementation_origin']}`; code `{row['code_availability']}`"
        )
        evidence = (
            f"`{row['validation']['level']}`; {row['validation']['evidence_path_count']} paths; "
            f"{row['constraint_count']} constraints; [details](METHODS.md)"
        )
        cells = [
            f"`{row['implementation_status']}`",
            f"`{row['id']}` — {markdown_escape(row['title'])}",
            provenance,
            surface_text,
            dependencies,
            markdown_escape(row["summary"]),
            evidence,
        ]
        for cell in cells:
            if len(cell.split()) > 120:
                raise SummaryError(f"Markdown cell exceeds 120 words for {row['id']}")
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(
        [
            "",
            "## Nonclaims",
            "",
            *[f"- {item}" for item in view["nonimplications"]],
            "",
            f"Source catalog SHA-256: `{view['source_catalog']['sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_outputs(root: Path, expected: dict[str, Any]) -> None:
    schema, _ = load_json(root / VIEW_SCHEMA, "methods-summary schema")
    actual, actual_raw = load_json(root / VIEW, "methods summary")
    validate_view(actual, schema, expected)
    if actual_raw != canonical_bytes(expected):
        raise SummaryError("methods summary JSON is not the expected canonical bytes")
    markdown = load_regular_bytes(root / MARKDOWN, "methods summary Markdown")
    expected_markdown = render_markdown(expected).encode("utf-8")
    if markdown != expected_markdown:
        raise SummaryError("METHODS_SUMMARY.md is stale; regenerate with --write")


def validate_view(
    actual: dict[str, Any], schema: dict[str, Any], expected: dict[str, Any]
) -> None:
    try:
        validate_json_schema(actual, schema, name="methods-summary")
    except SchemaValidationError as error:
        raise SummaryError(str(error)) from error
    if canonical_bytes(actual) != canonical_bytes(expected):
        raise SummaryError("methods summary JSON is stale; regenerate with --write")


def write_outputs(root: Path, view: dict[str, Any]) -> None:
    (root / VIEW).parent.mkdir(parents=True, exist_ok=True)
    (root / VIEW).write_bytes(canonical_bytes(view))
    (root / MARKDOWN).write_text(render_markdown(view), encoding="utf-8", newline="")


def main() -> int:
    arguments = parse_args()
    try:
        expected = make_expected(arguments.root)
        schema, _ = load_json(arguments.root / VIEW_SCHEMA, "methods-summary schema")
        validate_json_schema(expected, schema, name="expected-methods-summary")
        if arguments.emit_json:
            sys.stdout.buffer.write(canonical_bytes(expected))
        elif arguments.emit_markdown:
            sys.stdout.write(render_markdown(expected))
        elif arguments.write:
            write_outputs(arguments.root, expected)
            print("methods summary: GENERATED")
        else:
            validate_outputs(arguments.root, expected)
            print(f"methods summary: PASS ({len(expected['rows'])} rows; stable first)")
    except (OSError, SummaryError, SchemaValidationError) as error:
        print(f"methods summary: FAIL: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
