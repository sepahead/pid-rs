#!/usr/bin/env python3
"""Failure-injection tests for the exact external handoff intake binding."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check-handoff-intake.py"
spec = importlib.util.spec_from_file_location("check_handoff_intake", CHECKER)
if spec is None or spec.loader is None:
    raise SystemExit("cannot load handoff checker")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)

raw = checker.INTAKE.read_bytes()
sidecar = checker.SIDECAR.read_text(encoding="utf-8")
checker.validate_intake_record(raw, sidecar)
baseline = json.loads(raw)


def expect_rejected(label: str, value: object) -> None:
    mutated = checker.canonical_json_bytes(value)
    matching_sidecar = f"{hashlib.sha256(mutated).hexdigest()}  handoff-intake.json\n"
    try:
        checker.validate_intake_record(mutated, matching_sidecar)
    except (checker.IntakeError, checker.SchemaValidationError):
        return
    raise SystemExit(f"{label} unexpectedly passed with a recomputed sidecar")


mutations: list[tuple[str, dict[str, object]]] = []
for label, route in (
    ("master manifest", ("master_manifest_sha256",)),
    ("pid package manifest", ("pid_package_manifest_sha256",)),
    ("pid ledger", ("pid_ledger", "sha256")),
):
    value = copy.deepcopy(baseline)
    target = value
    for component in route[:-1]:
        target = target[component]
    target[route[-1]] = "0" * 64
    mutations.append((label, value))

package = copy.deepcopy(baseline)
package["packages"][0]["sha256"] = "0" * 64
mutations.append(("package identity", package))

frozen = copy.deepcopy(baseline)
frozen["repository_frozen_commit"] = "0" * 40
mutations.append(("frozen commit", frozen))

closure = copy.deepcopy(baseline)
closure["disposition"]["completion_evidence"] = True
mutations.append(("completion-evidence escalation", closure))

for label, mutation in mutations:
    expect_rejected(label, mutation)

try:
    checker.validate_intake_record(raw, "0" * 64 + "  handoff-intake.json\n")
except checker.IntakeError:
    pass
else:
    raise SystemExit("stale sidecar unexpectedly passed")

print("OK: handoff intake digest, non-closure, and sidecar mutations were rejected")
