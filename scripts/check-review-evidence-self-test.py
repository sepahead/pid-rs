#!/usr/bin/env python3
"""Mutation tests for the bounded assurance, task-disposition, and file-inventory gate."""

from __future__ import annotations

import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import tempfile


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-review-evidence.py"
spec = importlib.util.spec_from_file_location("check_review_evidence", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load review-evidence checker")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

checker.require_release_boundary()
assurance_raw = checker.ASSURANCE_REGISTRY.read_bytes()
tasks_raw = checker.TASK_DISPOSITIONS.read_bytes()
ledger_raw = checker.FILE_REVIEW_LEDGER.read_bytes()
checker.validate_assurance_registry(assurance_raw)
checker.validate_task_dispositions(tasks_raw)
checker.validate_file_review_ledger(ledger_raw)

assurance = json.loads(assurance_raw)
tasks = json.loads(tasks_raw)


def expect_assurance_rejected(label: str, value: object) -> None:
    try:
        checker.validate_assurance_registry(checker.canonical_json_bytes(value))
    except (checker.ReviewEvidenceError, checker.SchemaValidationError):
        return
    raise SystemExit(f"{label} assurance mutation unexpectedly passed")


def expect_tasks_rejected(label: str, value: object) -> None:
    try:
        checker.validate_task_dispositions(checker.canonical_json_bytes(value))
    except (checker.ReviewEvidenceError, checker.SchemaValidationError):
        return
    raise SystemExit(f"{label} task mutation unexpectedly passed")


def ledger_bytes(rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=checker.LEDGER_COLUMNS,
        lineterminator="\n",
        extrasaction="raise",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def expect_ledger_rejected(label: str, rows: list[dict[str, str]]) -> None:
    try:
        checker.validate_file_review_ledger(ledger_bytes(rows))
    except checker.ReviewEvidenceError:
        return
    raise SystemExit(f"{label} file-inventory mutation unexpectedly passed")


mutation = copy.deepcopy(assurance)
mutation["families"].pop()
expect_assurance_rejected("missing family", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][1] = copy.deepcopy(mutation["families"][0])
expect_assurance_rejected("duplicate family", mutation)

mutation = copy.deepcopy(assurance)
del mutation["families"][0]["layers"]["definition"]
expect_assurance_rejected("missing correctness layer", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][14]["layers"]["exact_algebra"]["assurance"]["status"] = "TESTED"
expect_assurance_rejected("unproved-layer escalation", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][0]["layers"]["definition"]["assumptions"] = []
expect_assurance_rejected("missing assumption", mutation)

mutation = copy.deepcopy(assurance)
mutation["families"][0]["layers"]["definition"]["gaps"][0][
    "disposition"
] = "NOT_CLAIMED"
expect_assurance_rejected("gap disposition", mutation)

mutation = copy.deepcopy(assurance)
mutation["release_boundary"]["v1_0_qualification_status"] = "GO"
expect_assurance_rejected("qualification escalation", mutation)

mutation = copy.deepcopy(assurance)
mutation["release_boundary"]["final_decision_claimed"] = True
expect_assurance_rejected("final-decision inference", mutation)

try:
    checker.validate_assurance_registry(
        assurance_raw.replace(
            b'{\n  "families":',
            b'{\n  "schema": "pid-rs/assurance-registry",\n  "families":',
            1,
        )
    )
except checker.ReviewEvidenceError:
    pass
else:
    raise SystemExit("duplicate assurance JSON key unexpectedly passed")

mutation = copy.deepcopy(tasks)
mutation["tasks"].pop()
expect_tasks_rejected("missing task", mutation)

mutation = copy.deepcopy(tasks)
mutation["tasks"][1] = copy.deepcopy(mutation["tasks"][0])
expect_tasks_rejected("duplicate task", mutation)

mutation = copy.deepcopy(tasks)
mutation["tasks"][0], mutation["tasks"][1] = (
    mutation["tasks"][1],
    mutation["tasks"][0],
)
expect_tasks_rejected("reordered task", mutation)

mutation = copy.deepcopy(tasks)
blocked = next(task for task in mutation["tasks"] if task["v1_0_disposition"] == "BLOCKED_EXTERNAL")
blocked["v1_0_disposition"] = "OPEN_LOCAL"
expect_tasks_rejected("external blocker removal", mutation)

mutation = copy.deepcopy(tasks)
mutation["summary"]["qualified_complete"] = 1
expect_tasks_rejected("task completion escalation", mutation)

mutation = copy.deepcopy(tasks)
mutation["release_boundary"]["v0_9_source_review_status"] = "QUALIFIED"
expect_tasks_rejected("source-review qualification escalation", mutation)

mutation = copy.deepcopy(tasks)
milestone = next(task for task in mutation["tasks"] if task["task_id"] == "T145")
milestone["implementation_state"] = "NOT_ESTABLISHED_BY_THIS_ARTIFACT"
expect_tasks_rejected("milestone implementation erasure", mutation)

mutation = copy.deepcopy(tasks)
task_156 = next(task for task in mutation["tasks"] if task["task_id"] == "T156")
task_156["v1_0_disposition"] = "CLAIM_REMOVED"
expect_tasks_rejected("cross-repository task closure", mutation)

mutation = copy.deepcopy(tasks)
task_138 = next(task for task in mutation["tasks"] if task["task_id"] == "T138")
task_138["scope_note"] = "bounded evidence exists"
expect_tasks_rejected("oracle-scope truncation", mutation)

original_handoff_commit = checker.HANDOFF_LEDGER_DECLARED_COMMIT
checker.HANDOFF_LEDGER_DECLARED_COMMIT = checker.TAGGED_COMMIT
try:
    checker.require_release_boundary()
except checker.ReviewEvidenceError:
    pass
else:
    raise SystemExit("ancestor handoff-commit mutation unexpectedly passed")
finally:
    checker.HANDOFF_LEDGER_DECLARED_COMMIT = original_handoff_commit

intake = json.loads(checker.HANDOFF_INTAKE.read_bytes())
original_intake_path = checker.HANDOFF_INTAKE
with tempfile.TemporaryDirectory(prefix="pid-rs-review-evidence-") as directory:
    mutation = copy.deepcopy(intake)
    mutation["pid_ledger"]["sha256"] = "0" * 64
    checker.HANDOFF_INTAKE = Path(directory) / "handoff-intake.json"
    checker.HANDOFF_INTAKE.write_bytes(checker.canonical_json_bytes(mutation))
    try:
        checker.load_handoff_intake()
    except checker.ReviewEvidenceError:
        pass
    else:
        raise SystemExit("handoff ledger identity mutation unexpectedly passed")
checker.HANDOFF_INTAKE = original_intake_path

reader = csv.DictReader(io.StringIO(ledger_raw.decode("utf-8"), newline=""))
baseline_rows = list(reader)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["sha256"] = "0" * 64
expect_ledger_rejected("blob digest", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows[:-1])
expect_ledger_rejected("missing tagged file", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["reviewer"] = "named person"
expect_ledger_rejected("reviewer inference", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["review_status"] = "REVIEWED"
expect_ledger_rejected("review completion inference", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["completed_at"] = "2026-07-14"
expect_ledger_rejected("completion timestamp", mutation_rows)

mutation_rows = copy.deepcopy(baseline_rows)
mutation_rows[0]["generated"] = "true"
mutation_rows[0]["generator"] = "not applicable"
expect_ledger_rejected("missing generator", mutation_rows)

print(
    "OK: family/layer, task/status, tag-inventory, digest, generator, and review-claim mutations were rejected"
)
