#!/usr/bin/env python3
"""Hostile mutation suite for the PID-only mathematical audit protocol."""

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
CHECKER = ROOT / "scripts/check-pid-mathematical-audit-protocol.py"


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
        raise SystemExit("PID-protocol checker changed during exact-source read")
    module = types.ModuleType("pid_mathematical_audit_protocol_checker")
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
            "PID-protocol checker failed isolated CLI bootstrap: "
            f"{completed.stderr.strip()}"
        )


check_isolated_cli()
expected = checker.make_expected(ROOT)
schema, _ = checker.load_json(ROOT / checker.VIEW_SCHEMA, "PID protocol schema")
view, _ = checker.load_json(ROOT / checker.VIEW, "PID protocol")
checker.validate_view(view, schema, expected)

rejections = 0


def rejected(label: str, mutation: object) -> None:
    global rejections
    try:
        checker.validate_view(mutation, schema, expected)
    except (checker.ProtocolError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile PID-protocol mutation passed")


mutation = copy.deepcopy(view)
mutation["derived_view_only"] = False
rejected("authority escalation", mutation)

mutation = copy.deepcopy(view)
mutation["transitive_chain_status"] = "established"
rejected("transitive-chain escalation", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][0], mutation["objects"][3] = (
    mutation["objects"][3],
    mutation["objects"][0],
)
rejected("object identity reorder", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][0]["source_observation_ids"] = mutation["objects"][3][
    "source_observation_ids"
]
rejected("Ehrlich errata transferred to MGW", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][6]["source_observation_ids"] = mutation["objects"][3][
    "source_observation_ids"
]
rejected("component observations directly credited to PID2", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][6]["component_source_review_routes"][0][
    "construction_id"
] = "mgw-categorical-shared-exclusions"
rejected("PID2 component route construction changed", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][7]["component_source_review_routes"][0][
    "via_object_id"
] = "mgw-categorical-shared-exclusions"
rejected("PID3 component route via-object changed", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][8]["component_source_review_routes"][0][
    "source_observation_ids"
].pop()
rejected("PID3 component route observation dropped", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][8]["component_source_review_routes"][0][
    "transfer_status"
] = "review_credit_transferred"
rejected("PID3 component route credit invented", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][1]["catalog_method_ids"].append(
    "shared-exclusions.continuous-report"
)
rejected("continuous estimator transferred to formal-logic object", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][2]["review_record_ids"] = ["REVIEW-EXTERNAL-MODEL-2026_08_12"]
rejected("unbound model review credited to object", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][2]["boundaries"] = ["Construction proved false."]
rejected("open Schick-Poland obligation escalated", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][4]["catalog_method_ids"].append(
    "shared-exclusions.continuous-report"
)
rejected("estimator row transferred to analytic population bridge", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][4]["assurance_families"] = copy.deepcopy(
    mutation["objects"][3]["assurance_families"]
)
rejected("estimator assurance transferred to analytic population bridge", mutation)

mutation = copy.deepcopy(view)
mutation["objects"][5]["assurance_families"][0]["edges"][0]["status"] = "established"
rejected("assurance edge promoted", mutation)

mutation = copy.deepcopy(view)
mutation["evidence_and_review"]["evidence_classes"][0]["meaning"] = (
    "Equivalent to independent human review."
)
rejected("evidence class conflation", mutation)

mutation = copy.deepcopy(view)
mutation["evidence_and_review"]["review_records"][1]["independence"]["semantic"] = (
    "independent"
)
rejected("independence invented", mutation)

mutation = copy.deepcopy(view)
mutation["authorities"][0]["sha256"] = "0" * 64
rejected("authority rebind", mutation)

mutation = copy.deepcopy(view)
mutation["unexpected"] = True
rejected("unknown top-level field", mutation)

for label, mutate in (
    (
        "schema rejects invented correspondence status",
        lambda value: value["objects"][0]["assurance_families"][0]["edges"][
            0
        ].__setitem__("status", "established"),
    ),
    (
        "schema rejects invented independence value",
        lambda value: value["evidence_and_review"]["review_records"][1][
            "independence"
        ].__setitem__("semantic", "independent"),
    ),
    (
        "schema rejects invented global correspondence edge",
        lambda value: value["correspondence_edges"][0].__setitem__(
            "id", "source_to_everything"
        ),
    ),
    (
        "schema rejects invented evidence class",
        lambda value: value["evidence_and_review"]["evidence_classes"][0].__setitem__(
            "class", "automatic_truth"
        ),
    ),
    (
        "schema rejects malformed review identifier",
        lambda value: value["evidence_and_review"]["review_records"][0].__setitem__(
            "id", "not-a-review-id"
        ),
    ),
):
    schema_value = copy.deepcopy(view)
    mutate(schema_value)
    try:
        checker.validate_json_schema(
            schema_value, schema, name="hostile-PID-protocol-value"
        )
    except checker.SchemaValidationError:
        rejections += 1
    else:
        raise SystemExit(f"{label}: standalone schema accepted hostile value")

schema_mutation = copy.deepcopy(schema)
schema_mutation["unsupported_assertion"] = True
try:
    checker.validate_json_schema(
        view, schema_mutation, name="hostile-PID-protocol-schema"
    )
except checker.SchemaValidationError:
    rejections += 1
else:
    raise SystemExit("unsupported PID-protocol schema assertion was silently accepted")

with tempfile.TemporaryDirectory(prefix="pid-rs-pid-protocol-") as temporary:
    temp_root = Path(temporary)
    for relative in (
        checker.CATALOG,
        checker.CATALOG_SCHEMA,
        checker.ERRATA,
        checker.ERRATA_SCHEMA,
        checker.ASSURANCE,
        checker.ASSURANCE_SCHEMA,
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
    except checker.ProtocolError:
        rejections += 1
    else:
        raise SystemExit("stale protocol accepted after catalog mutation")

    shutil.copyfile(ROOT / checker.CATALOG, catalog_path)
    errata_path = temp_root / checker.ERRATA
    errata = json.loads(errata_path.read_text(encoding="utf-8"))
    errata["records"][0]["implementation_disposition"]["summary"] += " hostile mutation"
    errata_path.write_bytes(checker.canonical_bytes(errata))
    changed = checker.make_expected(temp_root)
    try:
        checker.validate_outputs(temp_root, changed)
    except checker.ProtocolError:
        rejections += 1
    else:
        raise SystemExit("stale protocol accepted after source-errata mutation")

    shutil.copyfile(ROOT / checker.ERRATA, errata_path)
    assurance_path = temp_root / checker.ASSURANCE
    assurance = json.loads(assurance_path.read_text(encoding="utf-8"))
    assurance["families"][0]["definition_revision"] += "-hostile"
    assurance_path.write_bytes(checker.canonical_bytes(assurance))
    changed = checker.make_expected(temp_root)
    try:
        checker.validate_outputs(temp_root, changed)
    except checker.ProtocolError:
        rejections += 1
    else:
        raise SystemExit("stale protocol accepted after typed-assurance mutation")

    shutil.copyfile(ROOT / checker.ASSURANCE, assurance_path)
    markdown_path = temp_root / checker.MARKDOWN
    markdown_path.write_text(
        markdown_path.read_text(encoding="utf-8")
        + "\nAll constructions are equivalent.\n",
        encoding="utf-8",
    )
    try:
        checker.validate_outputs(temp_root, checker.make_expected(temp_root))
    except checker.ProtocolError:
        rejections += 1
    else:
        raise SystemExit("stale PID protocol Markdown was accepted")

    shutil.copyfile(ROOT / checker.MARKDOWN, markdown_path)
    catalog_path.unlink()
    catalog_path.symlink_to(checker.MARKDOWN)
    try:
        checker.make_expected(temp_root)
    except checker.ProtocolError:
        rejections += 1
    else:
        raise SystemExit("symlink method catalog was accepted")

print(f"PID protocol self-test: PASS ({rejections}/30 hostile cases rejected)")
