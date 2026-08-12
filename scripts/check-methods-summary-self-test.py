#!/usr/bin/env python3
"""Hostile mutation suite for the compact stable-first methods view."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-methods-summary.py"


def load_checker_from_exact_source() -> types.ModuleType:
    before = CHECKER.stat()
    source = CHECKER.read_bytes()
    after = CHECKER.stat()

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
            value.st_ctime_ns,
        )

    if identity(before) != identity(after) or len(source) != before.st_size:
        raise SystemExit("methods-summary checker changed during exact-source read")
    module = types.ModuleType("methods_summary_checker")
    module.__file__ = str(CHECKER)
    module.__package__ = ""
    module.__loader__ = None
    module.__spec__ = None
    module.__cached__ = None
    code = compile(
        source,
        str(CHECKER),
        "exec",
        dont_inherit=True,
        optimize=sys.flags.optimize,
    )
    exec(code, module.__dict__)
    return module


checker = load_checker_from_exact_source()


def check_isolated_cli() -> None:
    arguments = [sys.executable]
    if sys.flags.optimize:
        arguments.append("-O")
    arguments.extend(("-I", "-S", "-B", str(CHECKER)))
    completed = subprocess.run(
        arguments,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0 or completed.stderr:
        raise SystemExit(
            "methods-summary checker failed isolated CLI bootstrap: "
            f"{completed.stderr.strip()}"
        )


check_isolated_cli()
expected = checker.make_expected(ROOT)
schema, _ = checker.load_json(ROOT / checker.VIEW_SCHEMA, "methods-summary schema")
view, _ = checker.load_json(ROOT / checker.VIEW, "methods summary")
checker.validate_view(view, schema, expected)

rejections = 0


def rejected(label: str, mutation: object) -> None:
    global rejections
    try:
        checker.validate_view(mutation, schema, expected)
    except (checker.SummaryError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile methods-summary mutation passed")


mutation = copy.deepcopy(view)
mutation["derived_view_only"] = False
rejected("authority escalation", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0], mutation["rows"][-1] = mutation["rows"][-1], mutation["rows"][0]
rejected("stable-first ordering lost", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0]["implementation_status"] = "research-only"
rejected("stability relabel", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0]["definition_origin"] = "project-defined"
rejected("provenance relabel", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0]["summary"] += " Universally valid."
rejected("scientific escalation", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0]["validation"]["evidence_path_count"] += 1
rejected("invented evidence count", mutation)

mutation = copy.deepcopy(view)
mutation["rows"][0]["public_surface"]["rust_count"] += 1
rejected("invented API count", mutation)

mutation = copy.deepcopy(view)
mutation["source_catalog"]["sha256"] = "0" * 64
rejected("catalog rebind", mutation)

mutation = copy.deepcopy(view)
mutation["unexpected"] = True
rejected("unknown top-level field", mutation)

for label, mutate in (
    (
        "schema rejects unknown implementation status",
        lambda value: value["rows"][0].__setitem__(
            "implementation_status", "universally-valid"
        ),
    ),
    (
        "schema rejects unknown definition origin",
        lambda value: value["rows"][0].__setitem__(
            "definition_origin", "author-certified"
        ),
    ),
    (
        "schema rejects negative evidence count",
        lambda value: value["rows"][0]["validation"].__setitem__(
            "evidence_path_count", -1
        ),
    ),
):
    schema_value = copy.deepcopy(view)
    mutate(schema_value)
    try:
        checker.validate_json_schema(
            schema_value, schema, name="hostile-methods-summary-value"
        )
    except checker.SchemaValidationError:
        rejections += 1
    else:
        raise SystemExit(f"{label}: standalone schema accepted hostile value")

schema_mutation = copy.deepcopy(schema)
schema_mutation["unsupported_assertion"] = True
try:
    checker.validate_json_schema(
        view, schema_mutation, name="hostile-methods-summary-schema"
    )
except checker.SchemaValidationError:
    rejections += 1
else:
    raise SystemExit("unsupported schema assertion was silently accepted")

with tempfile.TemporaryDirectory(prefix="pid-rs-methods-summary-") as temporary:
    temp_root = Path(temporary)
    for relative in (
        checker.CATALOG,
        checker.CATALOG_SCHEMA,
        checker.VIEW,
        checker.VIEW_SCHEMA,
        checker.MARKDOWN,
    ):
        source = ROOT / relative
        destination = temp_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    catalog_path = temp_root / checker.CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["methods"][0]["summary"] += " hostile mutation"
    catalog_path.write_bytes(checker.canonical_bytes(catalog))
    changed = checker.make_expected(temp_root)
    try:
        checker.validate_outputs(temp_root, changed)
    except checker.SummaryError:
        rejections += 1
    else:
        raise SystemExit("stale methods view accepted after catalog mutation")

    shutil.copyfile(ROOT / checker.CATALOG, catalog_path)
    markdown_path = temp_root / checker.MARKDOWN
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8") + "\nUniversal proof.\n",
        encoding="utf-8",
    )
    try:
        checker.validate_outputs(temp_root, checker.make_expected(temp_root))
    except checker.SummaryError:
        rejections += 1
    else:
        raise SystemExit("stale Markdown summary was accepted")

    shutil.copyfile(ROOT / checker.MARKDOWN, markdown_path)
    catalog_path.unlink()
    catalog_path.symlink_to(checker.MARKDOWN)
    try:
        checker.make_expected(temp_root)
    except checker.SummaryError:
        rejections += 1
    else:
        raise SystemExit("symlink method catalog was accepted")

print(f"methods summary self-test: PASS ({rejections}/16 hostile cases rejected)")
