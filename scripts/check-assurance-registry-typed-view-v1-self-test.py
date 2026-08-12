#!/usr/bin/env python3
"""Hostile mutation suite for the typed assurance-registry view."""

from __future__ import annotations

import copy
import csv
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts/check-assurance-registry-typed-view-v1.py"


def load_checker_from_exact_source() -> types.ModuleType:
    """Compile the observed source bytes directly; never consult a bytecode cache."""
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
        raise SystemExit("typed-view checker source changed during exact-source read")
    module = types.ModuleType("assurance_typed_view_v1")
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
            "typed-view checker failed its isolated CLI bootstrap: "
            f"{completed.stderr.strip()}"
        )


check_isolated_cli()

schema, _ = checker.load_json(
    checker.DEFAULT_SCHEMA, "typed-view schema", require_canonical=True
)
view, _ = checker.load_json(
    checker.DEFAULT_VIEW, "typed assurance view", require_canonical=True
)
expected = checker.make_expected(ROOT)
checker.validate_view(view, schema, expected)

rejections = 0


def rejected(label: str, mutation: object) -> None:
    global rejections
    try:
        checker.validate_view(mutation, schema, expected)
    except (checker.ViewError, checker.SchemaValidationError):
        rejections += 1
        return
    raise SystemExit(f"{label}: hostile view mutation passed")


mutation = copy.deepcopy(view)
mutation["derived_view_only"] = False
rejected("authority escalation", mutation)

mutation = copy.deepcopy(view)
mutation["transitive_chain_status"] = "established"
rejected("transitive closure escalation", mutation)

mutation = copy.deepcopy(view)
mutation["families"][0]["transitive_five_edge_chain_claimed"] = True
rejected("family chain escalation", mutation)

mutation = copy.deepcopy(view)
mutation["families"][0]["edges"][2]["source_component_status"] = "bounded"
rejected("hidden formal-to-executable gap", mutation)

mutation = copy.deepcopy(view)
mutation["families"][0]["edges"][1]["correspondence_status"] = "bounded_nontransitive"
rejected("component evidence promoted to formal correspondence", mutation)

mutation = copy.deepcopy(view)
mutation["families"][0]["edges"][0]["evidence_classes"] = ["human_review"]
rejected("documentation relabeled human review", mutation)

mutation = copy.deepcopy(view)
mutation["review_records"][0]["evidence_class"] = "line_review"
rejected("inventory relabeled line review", mutation)

mutation = copy.deepcopy(view)
mutation["review_records"][1]["reviewer_class"] = "named_external_human"
rejected("model relabeled human", mutation)

mutation = copy.deepcopy(view)
mutation["review_records"][1]["independence"]["institutional"] = "claimed"
rejected("model independence escalation", mutation)

mutation = copy.deepcopy(view)
mutation["review_records"][2]["object_count"] = 1
rejected("invented line review", mutation)

mutation = copy.deepcopy(view)
mutation["review_records"][3]["object_count"] = 1
rejected("invented human review", mutation)

mutation = copy.deepcopy(view)
mutation["release_facts"][0]["review_completion_inferred"] = True
rejected("tag fact promoted to review", mutation)

mutation = copy.deepcopy(view)
mutation["source_registry"]["sha256"] = "0" * 64
rejected("source registry rebind", mutation)

mutation = copy.deepcopy(view)
mutation["unexpected"] = True
rejected("unknown top-level field", mutation)

schema_mutation = copy.deepcopy(schema)
schema_mutation["unsupported_assertion"] = True
try:
    checker.validate_json_schema(
        view, schema_mutation, name="hostile-typed-view-schema"
    )
except checker.SchemaValidationError:
    rejections += 1
else:
    raise SystemExit("unsupported schema assertion was silently accepted")

with tempfile.TemporaryDirectory(prefix="pid-rs-assurance-view-v1-") as temporary:
    temp_root = Path(temporary)
    for relative in (
        "audit/evidence/assurance-registry.json",
        "audit/evidence/FILE_REVIEW_LEDGER.csv",
        "audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md",
    ):
        source = ROOT / relative
        destination = temp_root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    registry_path = temp_root / "audit/evidence/assurance-registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["families"][0]["layers"]["definition"]["assurance"]["claim"] += (
        " hostile mutation"
    )
    registry_path.write_bytes(checker.canonical_bytes(registry))
    changed = checker.make_expected(temp_root)
    if checker.canonical_bytes(changed) == checker.canonical_bytes(expected):
        raise SystemExit("source-registry mutation did not alter derived view")
    try:
        checker.validate_view(view, schema, changed)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("stale view accepted after source-registry mutation")

    shutil.copyfile(
        ROOT / "audit/evidence/assurance-registry.json",
        registry_path,
    )
    model_path = (
        temp_root / "audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md"
    )
    model_path.write_text(
        model_path.read_text(encoding="utf-8") + "\nhostile mutation\n",
        encoding="utf-8",
    )
    changed = checker.make_expected(temp_root)
    try:
        checker.validate_view(view, schema, changed)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("stale model-review hash was accepted")

    shutil.copyfile(
        ROOT / "audit/evidence/external-model-pid-rs-deep-audit-2026-08-12.md",
        model_path,
    )
    ledger_path = temp_root / "audit/evidence/FILE_REVIEW_LEDGER.csv"
    with ledger_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if fieldnames is None:
        raise SystemExit("ledger fieldnames missing in self-test")
    rows[0]["review_status"] = "COMPLETE"
    rows[0]["reviewer"] = "invented-reviewer"
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    ledger_path.write_text(stream.getvalue(), encoding="utf-8", newline="")
    try:
        checker.make_expected(temp_root)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("review completion was accepted without a new view revision")

    shutil.copyfile(
        ROOT / "audit/evidence/FILE_REVIEW_LEDGER.csv",
        ledger_path,
    )
    registry_path.unlink()
    registry_path.symlink_to("external-model-pid-rs-deep-audit-2026-08-12.md")
    try:
        checker.make_expected(temp_root)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("symlink assurance registry was accepted")
    registry_path.unlink()
    shutil.copyfile(ROOT / "audit/evidence/assurance-registry.json", registry_path)

    ledger_path.unlink()
    ledger_path.symlink_to("external-model-pid-rs-deep-audit-2026-08-12.md")
    try:
        checker.make_expected(temp_root)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("symlink review ledger was accepted")
    ledger_path.unlink()
    shutil.copyfile(ROOT / "audit/evidence/FILE_REVIEW_LEDGER.csv", ledger_path)

    model_path.unlink()
    model_path.symlink_to("FILE_REVIEW_LEDGER.csv")
    try:
        checker.make_expected(temp_root)
    except checker.ViewError:
        rejections += 1
    else:
        raise SystemExit("symlink external model review was accepted")

expected_rejections = 21
if rejections != expected_rejections:
    raise SystemExit(
        f"typed-view mutation accounting mismatch: {rejections} != {expected_rejections}"
    )

print(
    "OK: typed assurance-view baseline passed and "
    f"{rejections}/{expected_rejections} hostile mutations were rejected"
)
