#!/usr/bin/env python3
"""Validate the immutable external handoff intake without claiming task closure."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

from json_schema_subset import SchemaValidationError, validate as validate_json_schema


ROOT = Path(__file__).resolve().parent.parent
INTAKE = ROOT / "audit" / "evidence" / "handoff-intake.json"
SIDECAR = ROOT / "audit" / "evidence" / "handoff-intake.json.sha256"
SCHEMA = ROOT / "audit" / "schemas" / "handoff-intake.schema.json"
FROZEN_COMMIT = "85b3d3e463cad77e4fd36c434dfe1633e2420825"
EXPECTED_INTAKE_SHA256 = (
    "7437fa901fd610daf9cd77a6745f867b9e92836c1ebd45b2091ee79cfc028011"
)
EXPECTED_MASTER_MANIFEST_SHA256 = (
    "0d4d1c19600bd8e5d930cb269fcaa204e80e9728914572664af7961566d3ba57"
)
EXPECTED_PID_PACKAGE_MANIFEST_SHA256 = (
    "d510728e286cbb0bd15357c53c7b75a2ea70b15981df4c9312379808f2723bb1"
)
EXPECTED_PID_LEDGER_SHA256 = (
    "d1a03ea81d2dcb2a99f58c19c292bdcd62c5164273eea0e41704bfed21ed8b8d"
)
EXPECTED_PACKAGES = {
    "CREBAIN_V1_0_CURRENT_HEAD_MAX_EFFORT_HANDOFF.zip": "c7c8a342e5a4b94c2d4c411299c63ed1c01163acff847d9bf7389ed8ea8c052a",
    "GALADRIEL_V1_0_CURRENT_HEAD_MAX_EFFORT_HANDOFF.zip": "41bd414e38e7f46a0417005d59e2b0c0eb5e139ec38cce632e006b60a750cd94",
    "HALDIR_V1_0_CURRENT_HEAD_MAX_EFFORT_HANDOFF.zip": "1de5cfc2a577621c24ef10e97fd2319799d02b602cfb3de54954928a0d988efe",
    "NCP_V1_0_CURRENT_HEAD_MAX_EFFORT_HANDOFF.zip": "661c5a9bd6a62a8a973bc953fd45ba1a58d44592985c871fc6b039c9cbdd333b",
    "PID_RS_V1_0_CURRENT_HEAD_MAX_EFFORT_HANDOFF.zip": "9fcdcaf1e5254942c8dbdf4cea3890f6a858674bd6fd613b14f353b2a60e4730",
    "SEPAHEAD_V1_0_CURRENT_HEAD_CROSS_REPO_RECONCILIATION_HANDOFF.zip": "ae06b5525537e88de4ae37aa49b40de01893061bdc3096bcf1059c5c6d71e3d4",
}


class IntakeError(RuntimeError):
    """The checked-in intake is ambiguous, stale, or internally inconsistent."""


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise IntakeError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def validate_intake_record(raw: bytes, sidecar_text: str) -> dict[str, Any]:
    intake = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    schema = json.loads(
        SCHEMA.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys
    )
    validate_json_schema(intake, schema, name="handoff-intake.json")
    if raw != canonical_json_bytes(intake):
        raise IntakeError("handoff intake is not canonical JSON")

    digest = hashlib.sha256(raw).hexdigest()
    expected_sidecar = f"{digest}  handoff-intake.json\n"
    if sidecar_text != expected_sidecar:
        raise IntakeError("handoff intake SHA-256 sidecar is stale")
    packages = {item["name"]: item["sha256"] for item in intake["packages"]}
    if packages != EXPECTED_PACKAGES:
        raise IntakeError("handoff package identities differ from the verified intake")
    if intake["master_manifest_sha256"] != EXPECTED_MASTER_MANIFEST_SHA256:
        raise IntakeError(
            "master handoff manifest identity differs from the verified intake"
        )
    if intake["pid_package_manifest_sha256"] != EXPECTED_PID_PACKAGE_MANIFEST_SHA256:
        raise IntakeError(
            "pid-rs package manifest identity differs from the verified intake"
        )
    if intake["pid_ledger"]["sha256"] != EXPECTED_PID_LEDGER_SHA256:
        raise IntakeError("pid-rs ledger identity differs from the verified intake")
    if intake["repository_frozen_commit"] != FROZEN_COMMIT:
        raise IntakeError("handoff frozen commit differs from the verified intake")
    if digest != EXPECTED_INTAKE_SHA256:
        raise IntakeError("handoff intake differs from the exact verified record")
    return intake


def main() -> int:
    try:
        raw = INTAKE.read_bytes()
        validate_intake_record(raw, SIDECAR.read_text(encoding="utf-8"))

        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", FROZEN_COMMIT, "HEAD"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if ancestry.returncode != 0:
            raise IntakeError(
                "current HEAD does not descend from the frozen handoff commit"
            )
    except (OSError, json.JSONDecodeError, SchemaValidationError, IntakeError) as error:
        print(f"handoff intake error: {error}")
        return 1

    print(
        "OK: immutable handoff intake is canonical, checksum-bound, and remains non-closure evidence"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
