#!/usr/bin/env python3
"""Fail-closed validation of the inert July 2026 advisory-prompt archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any


if sys.version_info < (3, 11):
    raise SystemExit("check-advisory-councils-archive.py requires Python 3.11 or newer")


ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_REL = PurePosixPath("audit/archive/advisory-councils-20260725-20260726")
ARCHIVE_ID = "advisory-councils-20260725-20260726"
INDEX_SHA256 = "dfdf236cfb1b60ce912e1e039903f3b421d355d32e9d2f25f08bbd481d9063be"
INDEX_BYTES = 41_874
SCHEMA_SHA256 = "297888d3fc10fd18be9f4ec12f6a55824ca54de5b0f1a17d24b919669f03bfbe"
SCHEMA_BYTES = 13_587
DISPOSITION_SHA256 = "6d8266a8c04db630c9e7eb24d1c938d67bbb7a9743f9ebbb8e362ed1da3de3a4"
DISPOSITION_BYTES = 7_566
SOURCE_BRANCH = "review/sx-count-event-bridge-r2"
SOURCE_HEAD = "9bbcf5ef04d26b0fd5ec552fe6a065f9a474fd56"
FROZEN_INTAKE_HEAD = "ca2eaf31ce7b719d04a43e0d6e1d2c21c6ff06a7"
SOURCE_STATUS_SHA256 = (
    "6de84fa32b4a92a14a295ccae0ec1ed04cfd869c5a518edff473012748c7e943"
)
EXPECTED_LICENSE = {
    "authorship_or_external_rights_verified": False,
    "basis": (
        "Project-material publication designation for this archive milestone; it does not "
        "authenticate authorship or grant rights over any separately withheld response or context."
    ),
    "expression": "MIT OR Apache-2.0",
    "external_payload_embedded": False,
}
EXPECTED_PROVENANCE = {
    "frozen_intake_head": FROZEN_INTAKE_HEAD,
    "observed_source_branch": SOURCE_BRANCH,
    "observed_source_head": SOURCE_HEAD,
    "source_head_binds_payload": False,
    "tracked_state": "untracked",
}
EXPECTED_PAYLOADS = {
    "completion-triage-20260725": {
        "name": "fable5-completion-triage-prompt.md",
        "original_path": "audit/evidence/fable5-completion-triage-prompt.md",
        "sha256": "653e9aad00bfffce440f70c8c4fe254893a389866e3a1ccf20dfd9fd530b6961",
        "bytes": 4_966,
        "source_date": "2026-07-25",
        "successors": [
            ("AGENTS.md", "current scientific-object and evidence policy"),
            (
                "PID_MATHEMATICAL_AUDIT_PROTOCOL.md",
                "current object-card review workflow",
            ),
            ("audit/evidence/assurance-registry.json", "current assurance authority"),
            (
                "audit/evidence/completion-run-ledger-2026-07-25.md",
                "retained process ledger with its own bounded status",
            ),
        ],
    },
    "imin-tie-swap-20260725": {
        "name": "fable5-imin-tie-swap-review-prompt.md",
        "original_path": "audit/evidence/fable5-imin-tie-swap-review-prompt.md",
        "sha256": "c510e9ce10d1a1526fbcae1455303dca45dcb94d24734edcfe3ec638ffb11202",
        "bytes": 3_491,
        "source_date": "2026-07-25",
        "successors": [
            (
                "NUMERICAL_ASSURANCE.md",
                "current numerical assurance and nonclaim boundary",
            ),
            (
                "crates/pid-core/tests/imin_numerical_boundary.rs",
                "current executable finite-domain and boundary evidence",
            ),
            ("audit/evidence/assurance-registry.json", "current assurance authority"),
            ("method-catalog.json", "current method provenance authority"),
        ],
    },
    "pid2-represented-sum-20260725": {
        "name": "fable5-pid2-represented-sum-review-prompt.md",
        "original_path": "audit/evidence/fable5-pid2-represented-sum-review-prompt.md",
        "sha256": "8607fec9c789e7963e905c799880d1a0e0c97250f86b3373e7d29dec9d7f4ecb",
        "bytes": 5_306,
        "source_date": "2026-07-25",
        "successors": [
            (
                "crates/pid-core/src/pid2.rs",
                "current executable constructor implementation",
            ),
            (
                "NUMERICAL_ASSURANCE.md",
                "current numerical assurance and boundary statement",
            ),
            ("release-scope-1.0.json", "current release-family authority"),
            ("audit/evidence/assurance-registry.json", "current assurance authority"),
        ],
    },
    "ksg-integer-harmonic-20260725": {
        "name": "fable5-ksg-integer-harmonic-review-prompt.md",
        "original_path": "audit/evidence/fable5-ksg-integer-harmonic-review-prompt.md",
        "sha256": "ffd9df7bec08d218bdf114ae1efb3b91c14e5ee53d02f7e2dfab892e258aedd5",
        "bytes": 6_311,
        "source_date": "2026-07-25",
        "successors": [
            (
                "claims/KSG-INTEGER-HARMONIC-001/claim-v4.md",
                "current scoped claim statement",
            ),
            ("scripts/check-ksg-harmonic-revision.py", "current composite checker"),
            ("audit/evidence/assurance-registry.json", "current assurance authority"),
            ("crates/pid-core/src/stats.rs", "current arithmetic implementation"),
        ],
    },
    "frontier-five-lens-20260726": {
        "name": "fable5-frontier-five-lens-prompt-20260726T084258Z.md",
        "original_path": (
            "audit/evidence/fable5-frontier-five-lens-prompt-20260726T084258Z.md"
        ),
        "sha256": "7cab7b0f5f6ca08d177ce95b503a1ea4fa5af9291c83205d00677ed4667f1a80",
        "bytes": 11_141,
        "source_date": "2026-07-26",
        "successors": [
            (
                "PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md",
                "current discovery and durability workflow",
            ),
            (
                "PID_MATHEMATICAL_AUDIT_PROTOCOL.md",
                "current object-card review workflow",
            ),
            ("KNOWN_LIMITATIONS.md", "current scientific limitations boundary"),
            (
                "claims/SX-CERTIFIED-AVERAGED-PID3-001",
                "current categorical SxPID3 claim packet directory",
            ),
            ("audit/evidence/assurance-registry.json", "current assurance authority"),
        ],
    },
}
EXPECTED_WITHHELD = {
    "completion-triage-response-20260725": (
        "audit/evidence/fable5-completion-triage-review-2026-07-25.md",
        "9d36c5967d1fad19e5c79227d02d3ab11b5bebdaacdbfbbd9141bc928b395611",
        8_307,
        "advisory response",
    ),
    "imin-tie-swap-response-20260725": (
        "audit/evidence/fable5-imin-tie-swap-review-2026-07-25.md",
        "1fc1f05a2229f3d23d9eaa4dff2c6cde1f5c3913abf07bc7825db12fd369cf6e",
        9_026,
        "advisory response",
    ),
    "pid2-represented-sum-response-20260725": (
        "audit/evidence/fable5-pid2-represented-sum-review-2026-07-25.md",
        "2c3ff67a869e112eb20be95d1365ad3694f333234d59a8fbed5fdaaba249b246",
        19_964,
        "advisory response",
    ),
    "ksg-integer-harmonic-response-20260725": (
        "audit/evidence/fable5-ksg-integer-harmonic-review-2026-07-25.md",
        "b6657928d551a8440b149f0472dc5546436d6dcf037f47aff390bc9614608749",
        19_403,
        "advisory response",
    ),
    "frontier-five-lens-context-20260726": (
        "audit/evidence/fable5-frontier-five-lens-20260726T084258Z-context.md",
        "91564363da3b48721bcfc0cc251f16a2110fdb206386964675cae9fa4a4018dd",
        1_119_380,
        "frozen context bundle",
    ),
    "frontier-five-lens-receipt-20260726": (
        "audit/evidence/fable5-frontier-five-lens-20260726T084258Z-receipt.json",
        "17189a8b44e0de8ee623a791b32c5f03ce8faf8846e2854524fa718e044b6ea9",
        10_978,
        "provider receipt",
    ),
    "frontier-five-lens-response-20260726": (
        "audit/evidence/fable5-frontier-five-lens-20260726T084258Z-response.md",
        "72d402c19ca6d933ea9dc231645b74f32b5684562a8d429ae699c39571437f8f",
        31_911,
        "advisory response",
    ),
    "frontier-five-lens-sanity-20260726": (
        (
            "audit/evidence/"
            "fable5-frontier-five-lens-independent-sanity-check-20260726T084258Z.md"
        ),
        "eac7018e4392d447ffa822363a8a37d723458ede4b8fbed1743a7701e9d3e543",
        7_050,
        "separate sanity note",
    ),
    "frontier-five-lens-preflight-failure-20260726": (
        "audit/evidence/fable5-frontier-five-lens-preflight-failure-20260726T084258Z.md",
        "98af79085d1449dab08c52a14894e0972bb263d4ad99afdc984901505507f727",
        810,
        "preflight failure note",
    ),
    "frontier-five-lens-runner-20260726": (
        "audit/evidence/fable5-frontier-five-lens-runner-20260726T084258Z.mjs",
        "c04a00e33285bf0e08c71c773913a07c9a135e9f8eb5bb0a21191c4dedae519a",
        17_291,
        "runner source",
    ),
}
EXPECTED_REDERIVATION_IDS = {
    "dependency-coloring-independence-premise",
    "imin-exact-target-tie-predicate",
    "imin-pid2-source-swap-bit-equivariance",
    "ksg-count-index-correspondence",
    "ksg-positive-integer-harmonic-cancellation",
    "mgw-categorical-count-event-bridge",
    "mgw-categorical-pid3-mobius-closure",
    "continuous-mixed-rank-common-radius-criterion",
    "pid2-represented-input-rounding",
    "pid2-scaling-acceptance-boundary",
}
AUTHORITY_SURFACES = (
    "method-catalog.json",
    "METHODS.md",
    "release-scope-1.0.json",
    "RELEASE_SCOPE_1_0.md",
    "audit/evidence/assurance-registry.json",
    "audit/evidence/assurance-registry-typed-view-v1.json",
    "ecosystem-capabilities.json",
    "ECOSYSTEM_CAPABILITIES.md",
    "audit/source-errata.json",
)
CHECKER_REL = "scripts/check-advisory-councils-archive.py"
SELF_TEST_REL = "scripts/check-advisory-councils-archive-self-test.py"


class ArchiveError(RuntimeError):
    """The bounded archive contract failed."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="repository root; intended for isolated hostile fixtures",
    )
    return parser.parse_args()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def duplicate_guard(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def reject_nonfinite(value: str) -> None:
    raise ArchiveError(f"non-standard JSON constant: {value}")


def load_canonical_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    raw = read_regular(path, label, 0o644)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ArchiveError(f"{label} is not UTF-8: {error}") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=duplicate_guard,
            parse_constant=reject_nonfinite,
        )
    except (json.JSONDecodeError, ArchiveError) as error:
        raise ArchiveError(f"invalid {label}: {error}") from error
    if not isinstance(value, dict):
        raise ArchiveError(f"{label} root must be an object")
    canonical = (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise ArchiveError(f"{label} is not canonical sorted JSON")
    return value, raw


def read_regular(path: Path, label: str, expected_mode: int | None = None) -> bytes:
    try:
        info = path.lstat()
    except OSError as error:
        raise ArchiveError(f"cannot stat {label} {path}: {error}") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise ArchiveError(f"{label} must be a regular non-symlink file: {path}")
    if expected_mode is not None and stat.S_IMODE(info.st_mode) != expected_mode:
        raise ArchiveError(
            f"{label} mode drifted: expected {expected_mode:04o}, "
            f"observed {stat.S_IMODE(info.st_mode):04o}"
        )
    try:
        return path.read_bytes()
    except OSError as error:
        raise ArchiveError(f"cannot read {label} {path}: {error}") from error


def require_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ArchiveError(
            f"{label} keys changed: missing={sorted(expected - actual)!r} "
            f"extra={sorted(actual - expected)!r}"
        )


def require_bool(value: Any, expected: bool, label: str) -> None:
    if type(value) is not bool or value is not expected:
        raise ArchiveError(f"{label} must be exact boolean {expected!r}")


def require_nonempty_strings(value: Any, minimum: int, label: str) -> None:
    if not isinstance(value, list) or len(value) < minimum:
        raise ArchiveError(f"{label} must contain at least {minimum} entries")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ArchiveError(f"{label} must contain only nonempty strings")
    if len(value) != len(set(value)):
        raise ArchiveError(f"{label} must not contain duplicates")


def validate_archive_inventory(root: Path, archive: Path) -> None:
    if archive.is_symlink() or not archive.is_dir():
        raise ArchiveError("archive root must be a non-symlink directory")
    expected_files = {
        "DISPOSITION.md",
        "INDEX.json",
        "INDEX.schema.json",
        *{f"payload/{record['name']}" for record in EXPECTED_PAYLOADS.values()},
    }
    observed_files: set[str] = set()
    observed_dirs: set[str] = set()
    for candidate in archive.rglob("*"):
        relative = candidate.relative_to(archive).as_posix()
        if candidate.is_symlink():
            raise ArchiveError(f"archive symlink is forbidden: {relative}")
        if candidate.is_dir():
            observed_dirs.add(relative)
        elif candidate.is_file():
            observed_files.add(relative)
        else:
            raise ArchiveError(f"archive special node is forbidden: {relative}")
    if observed_dirs != {"payload"}:
        raise ArchiveError(
            f"archive directory inventory changed: {sorted(observed_dirs)!r}"
        )
    if observed_files != expected_files:
        raise ArchiveError(
            "archive file inventory changed: "
            f"missing={sorted(expected_files - observed_files)!r} "
            f"extra={sorted(observed_files - expected_files)!r}"
        )
    if any(path.name.casefold() == "readme.md" for path in archive.rglob("*")):
        raise ArchiveError("README-iff violation: archive must not contain README.md")
    resolved_root = root.resolve(strict=True)
    resolved_archive = archive.resolve(strict=True)
    if not resolved_archive.is_relative_to(resolved_root):
        raise ArchiveError("archive resolves outside repository root")


def validate_schema(schema: dict[str, Any], raw: bytes) -> None:
    if len(raw) != SCHEMA_BYTES or sha256(raw) != SCHEMA_SHA256:
        raise ArchiveError("INDEX.schema.json size or digest changed")
    if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        raise ArchiveError("schema dialect changed")
    if schema.get("$id") != "pid-rs/advisory-councils-archive-index/v1":
        raise ArchiveError("schema identity changed")
    if (
        schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
    ):
        raise ArchiveError("schema root is not fail-closed")
    payload_status = (
        schema.get("$defs", {})
        .get("payload", {})
        .get("properties", {})
        .get("status", {})
        .get("const")
    )
    if payload_status != "historical-prompt":
        raise ArchiveError("schema historical-prompt status guard changed")
    rederive_status = (
        schema.get("$defs", {})
        .get("rederivation", {})
        .get("properties", {})
        .get("status", {})
        .get("const")
    )
    if rederive_status != "not_imported_requires_fresh_derivation":
        raise ArchiveError("schema rederivation abstention guard changed")


def validate_top_level(index: dict[str, Any]) -> None:
    require_exact_keys(
        index,
        {
            "$schema",
            "archive_id",
            "archive_period",
            "authority",
            "classification",
            "execution_policy",
            "format",
            "license_boundary",
            "payloads",
            "privacy_boundary",
            "rederivation_queue",
            "source_observation",
            "withheld_records",
        },
        "INDEX",
    )
    if index["$schema"] != "INDEX.schema.json":
        raise ArchiveError("INDEX schema locator changed")
    if index["archive_id"] != ARCHIVE_ID:
        raise ArchiveError("archive id changed")
    if index["classification"] != "historical-prompt-archive":
        raise ArchiveError("archive classification changed")
    if index["format"] != "pid-rs/advisory-councils-archive/v1":
        raise ArchiveError("archive format changed")
    authority = index["authority"]
    if not isinstance(authority, dict):
        raise ArchiveError("authority must be an object")
    require_exact_keys(
        authority,
        {"current_authority", "evidence_authority", "model_output_class"},
        "authority",
    )
    require_bool(authority["current_authority"], False, "authority.current_authority")
    require_bool(authority["evidence_authority"], False, "authority.evidence_authority")
    if authority["model_output_class"] != "advisory only":
        raise ArchiveError("model-output class changed")
    execution = index["execution_policy"]
    if not isinstance(execution, dict):
        raise ArchiveError("execution_policy must be an object")
    require_exact_keys(
        execution,
        {"executable", "importable", "inert_payloads_only", "payload_use"},
        "execution_policy",
    )
    require_bool(execution["executable"], False, "execution_policy.executable")
    require_bool(execution["importable"], False, "execution_policy.importable")
    require_bool(
        execution["inert_payloads_only"],
        True,
        "execution_policy.inert_payloads_only",
    )
    if execution["payload_use"] != "human historical inspection only":
        raise ArchiveError("payload-use boundary changed")
    if index["license_boundary"] != EXPECTED_LICENSE:
        raise ArchiveError("top-level license boundary drifted")


def validate_source_and_privacy(index: dict[str, Any]) -> None:
    source = index["source_observation"]
    expected_source = {
        "frozen_intake_head": FROZEN_INTAKE_HEAD,
        "observed_at_utc": "2026-08-25T09:57:13Z",
        "observed_source_branch": SOURCE_BRANCH,
        "observed_source_head": SOURCE_HEAD,
        "payload_tracked_state": "untracked",
        "source_head_binds_payload": False,
        "source_location_class": (
            "protected primary worktree; absolute host locator intentionally omitted from the index"
        ),
        "source_status_sha256": SOURCE_STATUS_SHA256,
    }
    if source != expected_source:
        raise ArchiveError("source branch/head/intake/status provenance drifted")
    privacy = index["privacy_boundary"]
    if not isinstance(privacy, dict):
        raise ArchiveError("privacy_boundary must be an object")
    expected_privacy = {
        "exact_prompt_bytes_authorized_for_this_public_archive": True,
        "external_or_companion_payloads_authorized": False,
        "literal_absolute_local_paths_retained": 5,
        "privacy_review_scope": "five prompt payloads only",
        "secrets_scan": {
            "observed_at_utc": "2026-08-25T10:09:41Z",
            "result": "no findings",
            "scope": "five exact prompt payload files",
            "tool": "gitleaks 8.30.1",
        },
        "secrets_scan_nonclaim": (
            "Pattern scanning does not prove that sensitive information is absent."
        ),
    }
    if privacy != expected_privacy:
        raise ArchiveError("privacy/scan boundary drifted")


def validate_payloads(root: Path, archive: Path, index: dict[str, Any]) -> None:
    payloads = index["payloads"]
    if not isinstance(payloads, list) or len(payloads) != len(EXPECTED_PAYLOADS):
        raise ArchiveError("payload count changed")
    by_id: dict[str, dict[str, Any]] = {}
    for value in payloads:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            raise ArchiveError("each payload must be an object with a string id")
        if value["id"] in by_id:
            raise ArchiveError(f"duplicate payload id: {value['id']}")
        by_id[value["id"]] = value
    if set(by_id) != set(EXPECTED_PAYLOADS):
        raise ArchiveError("payload id set changed")

    total_absolute_paths = 0
    for payload_id, expected in EXPECTED_PAYLOADS.items():
        value = by_id[payload_id]
        if value.get("status") != "historical-prompt":
            raise ArchiveError(f"{payload_id}: status must remain historical-prompt")
        for field in (
            "current_authority",
            "evidence_authority",
            "executable",
            "importable",
        ):
            require_bool(value.get(field), False, f"{payload_id}.{field}")
        require_bool(value.get("inert"), True, f"{payload_id}.inert")
        if value.get("provenance") != EXPECTED_PROVENANCE:
            raise ArchiveError(f"{payload_id}: provenance drifted")
        if value.get("license") != EXPECTED_LICENSE:
            raise ArchiveError(f"{payload_id}: license boundary drifted")
        if value.get("original_path") != expected["original_path"]:
            raise ArchiveError(f"{payload_id}: original path drifted")
        archive_path = (ARCHIVE_REL / "payload" / expected["name"]).as_posix()
        if value.get("archive_path") != archive_path:
            raise ArchiveError(f"{payload_id}: archive path drifted")
        if value.get("sha256") != expected["sha256"]:
            raise ArchiveError(f"{payload_id}: declared digest drifted")
        if type(value.get("bytes")) is not int or value["bytes"] != expected["bytes"]:
            raise ArchiveError(f"{payload_id}: declared byte length drifted")
        if value.get("source_date") != expected["source_date"]:
            raise ArchiveError(f"{payload_id}: source date drifted")
        if (
            not isinstance(value.get("chronology_within_date"), str)
            or not value["chronology_within_date"].strip()
        ):
            raise ArchiveError(f"{payload_id}: chronology boundary missing")
        successors = value.get("current_successors")
        expected_successors = [
            {"path": path, "role": role} for path, role in expected["successors"]
        ]
        if successors != expected_successors:
            raise ArchiveError(
                f"{payload_id}: current successor set/order/role drifted"
            )
        for successor in successors:
            successor_path = root / successor["path"]
            if successor_path.is_symlink() or not successor_path.exists():
                raise ArchiveError(
                    f"{payload_id}: current successor missing or symlinked: "
                    f"{successor['path']}"
                )
            if ARCHIVE_ID in successor["path"]:
                raise ArchiveError(f"{payload_id}: archive cannot succeed itself")
        require_nonempty_strings(
            value.get("known_risks"), 3, f"{payload_id}.known_risks"
        )
        require_nonempty_strings(
            value.get("prohibited_inferences"),
            6,
            f"{payload_id}.prohibited_inferences",
        )
        if (
            not isinstance(value.get("scientific_value"), str)
            or not value["scientific_value"].strip()
        ):
            raise ArchiveError(f"{payload_id}: scientific value missing")
        privacy = value.get("privacy")
        if not isinstance(privacy, dict):
            raise ArchiveError(f"{payload_id}: privacy must be an object")
        if privacy.get("absolute_user_path_occurrences") != 1:
            raise ArchiveError(f"{payload_id}: absolute-path disclosure count drifted")
        expected_privacy_flags = {
            "known_credential_values_intentionally_retained": False,
            "exact_bytes_preserved_without_redaction": True,
            "literal_local_path_disclosed": True,
        }
        for field, expected_flag in expected_privacy_flags.items():
            require_bool(
                privacy.get(field), expected_flag, f"{payload_id}.privacy.{field}"
            )
        if set(privacy) != {
            "absolute_user_path_occurrences",
            "known_credential_values_intentionally_retained",
            "exact_bytes_preserved_without_redaction",
            "literal_local_path_disclosed",
            "scan_claim_boundary",
            "scan_result",
        }:
            raise ArchiveError(f"{payload_id}: privacy field set drifted")
        if not privacy["scan_claim_boundary"] or not privacy["scan_result"]:
            raise ArchiveError(f"{payload_id}: privacy scan boundary missing")

        path = archive / "payload" / expected["name"]
        raw = read_regular(path, f"payload {payload_id}", 0o644)
        if raw.startswith(b"#!"):
            raise ArchiveError(f"{payload_id}: payload shebang is forbidden")
        if path.suffix != ".md":
            raise ArchiveError(f"{payload_id}: only Markdown payloads are permitted")
        if len(raw) != expected["bytes"] or sha256(raw) != expected["sha256"]:
            raise ArchiveError(f"{payload_id}: payload bytes or digest changed")
        occurrence_count = len(re.findall(rb"/Users/[A-Za-z0-9._-]+", raw))
        if occurrence_count != 1:
            raise ArchiveError(f"{payload_id}: literal absolute-path count changed")
        total_absolute_paths += occurrence_count
        if (root / expected["original_path"]).exists():
            raise ArchiveError(
                f"{payload_id}: original evidence-path copy is forbidden; archive only"
            )
    if total_absolute_paths != 5:
        raise ArchiveError("aggregate literal absolute-path count changed")


def validate_withheld(root: Path, archive: Path, index: dict[str, Any]) -> None:
    values = index["withheld_records"]
    if not isinstance(values, list) or len(values) != len(EXPECTED_WITHHELD):
        raise ArchiveError("withheld-record count changed")
    by_id: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            raise ArchiveError("each withheld record must have a string id")
        if value["id"] in by_id:
            raise ArchiveError(f"duplicate withheld id: {value['id']}")
        by_id[value["id"]] = value
    if set(by_id) != set(EXPECTED_WITHHELD):
        raise ArchiveError("withheld-record id set changed")
    for record_id, (
        original,
        digest,
        byte_length,
        artifact_class,
    ) in EXPECTED_WITHHELD.items():
        value = by_id[record_id]
        if value.get("original_path") != original:
            raise ArchiveError(f"{record_id}: withheld original path drifted")
        if value.get("sha256") != digest or value.get("bytes") != byte_length:
            raise ArchiveError(f"{record_id}: withheld digest/length drifted")
        if value.get("artifact_class") != artifact_class:
            raise ArchiveError(f"{record_id}: withheld artifact class drifted")
        require_bool(value.get("included"), False, f"{record_id}.included")
        require_bool(
            value.get("recovery_locator_published"),
            False,
            f"{record_id}.recovery_locator_published",
        )
        require_bool(
            value.get("source_head_context_only"),
            True,
            f"{record_id}.source_head_context_only",
        )
        if value.get("payload_path") is not None:
            raise ArchiveError(f"{record_id}: withheld payload path must remain null")
        if value.get("disposition") != (
            "withheld_pending_semantic_privacy_rights_review"
        ):
            raise ArchiveError(f"{record_id}: withheld disposition drifted")
        if value.get("provenance") != EXPECTED_PROVENANCE:
            raise ArchiveError(f"{record_id}: withheld provenance drifted")
        if not isinstance(value.get("nonclaim"), str) or not value["nonclaim"].strip():
            raise ArchiveError(f"{record_id}: withheld nonclaim missing")
        if (root / original).exists():
            raise ArchiveError(f"{record_id}: raw withheld companion is present")
        basename = PurePosixPath(original).name
        if any(path.name == basename for path in archive.rglob("*")):
            raise ArchiveError(f"{record_id}: withheld companion entered archive")


def validate_rederivation(index: dict[str, Any]) -> None:
    values = index["rederivation_queue"]
    if not isinstance(values, list) or len(values) != len(EXPECTED_REDERIVATION_IDS):
        raise ArchiveError("rederivation queue count changed")
    observed_ids: set[str] = set()
    valid_prompt_ids = set(EXPECTED_PAYLOADS)
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("id"), str):
            raise ArchiveError("each rederivation record must have a string id")
        record_id = value["id"]
        if record_id in observed_ids:
            raise ArchiveError(f"duplicate rederivation id: {record_id}")
        observed_ids.add(record_id)
        if value.get("status") != "not_imported_requires_fresh_derivation":
            raise ArchiveError(f"{record_id}: rederivation status was promoted")
        for field in ("candidate_statement", "source_domain"):
            if not isinstance(value.get(field), str) or not value[field].strip():
                raise ArchiveError(f"{record_id}: {field} missing")
        require_nonempty_strings(
            value.get("required_closure"), 4, f"{record_id}.required_closure"
        )
        prompt_ids = value.get("source_prompt_ids")
        require_nonempty_strings(prompt_ids, 1, f"{record_id}.source_prompt_ids")
        if not set(prompt_ids).issubset(valid_prompt_ids):
            raise ArchiveError(f"{record_id}: unknown source prompt id")
    if observed_ids != EXPECTED_REDERIVATION_IDS:
        raise ArchiveError("rederivation id set changed")


def scan_authority_and_execution_surfaces(root: Path) -> None:
    markers = {
        ARCHIVE_REL.as_posix().encode("utf-8"),
        ARCHIVE_ID.encode("utf-8"),
        *{record["name"].encode("utf-8") for record in EXPECTED_PAYLOADS.values()},
    }
    for relative in AUTHORITY_SURFACES:
        path = root / relative
        raw = read_regular(path, f"authority surface {relative}")
        for marker in markers:
            if marker in raw:
                raise ArchiveError(
                    f"archive authority wiring is forbidden: {relative} contains "
                    f"{marker.decode('utf-8')}"
                )

    surfaces: set[Path] = {root / "Cargo.toml", root / "justfile"}
    for base, suffixes in (
        (root / "crates", {".rs", ".toml"}),
        (root / ".github" / "workflows", {".yml", ".yaml"}),
        (root / "scripts", {".py", ".sh", ".mjs"}),
    ):
        if not base.exists():
            raise ArchiveError(f"execution surface directory missing: {base}")
        for candidate in base.rglob("*"):
            if candidate.is_file() and candidate.suffix in suffixes:
                surfaces.add(candidate)
    excluded = {root / CHECKER_REL, root / SELF_TEST_REL}
    for path in sorted(surfaces):
        if path in excluded:
            continue
        if path.is_symlink():
            raise ArchiveError(
                f"execution surface is symlinked: {path.relative_to(root)}"
            )
        raw = read_regular(path, f"execution surface {path.relative_to(root)}")
        for marker in markers:
            if marker in raw:
                raise ArchiveError(
                    "archive execution/import wiring is forbidden: "
                    f"{path.relative_to(root)} contains {marker.decode('utf-8')}"
                )


def check(root: Path) -> dict[str, Any]:
    root = root.resolve(strict=True)
    archive = root / ARCHIVE_REL
    validate_archive_inventory(root, archive)

    schema, schema_raw = load_canonical_json(
        archive / "INDEX.schema.json", "INDEX.schema.json"
    )
    validate_schema(schema, schema_raw)
    index, index_raw = load_canonical_json(archive / "INDEX.json", "INDEX.json")

    validate_top_level(index)
    validate_source_and_privacy(index)
    validate_payloads(root, archive, index)
    validate_withheld(root, archive, index)
    validate_rederivation(index)

    disposition = read_regular(archive / "DISPOSITION.md", "DISPOSITION.md", 0o644)
    if (
        len(disposition) != DISPOSITION_BYTES
        or sha256(disposition) != DISPOSITION_SHA256
    ):
        raise ArchiveError("DISPOSITION.md size or digest changed")
    scan_authority_and_execution_surfaces(root)

    if len(index_raw) != INDEX_BYTES or sha256(index_raw) != INDEX_SHA256:
        raise ArchiveError("INDEX.json size or digest changed")
    return {
        "archive_id": ARCHIVE_ID,
        "payloads": len(EXPECTED_PAYLOADS),
        "rederivation_candidates": len(EXPECTED_REDERIVATION_IDS),
        "status": "ok",
        "withheld_hash_only": len(EXPECTED_WITHHELD),
    }


def main() -> int:
    args = parse_args()
    try:
        result = check(args.root)
    except (ArchiveError, OSError) as error:
        print(f"advisory archive check failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
