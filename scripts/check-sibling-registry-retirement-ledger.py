#!/usr/bin/env python3
"""Fail-closed validator for the public sibling-registry retirement ledger."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any


class LedgerError(RuntimeError):
    """A ledger, schema, or integrity contract failed."""


LEDGER_RELATIVE = Path(
    "audit/evidence/sibling-registry-retirement-ledger-2026-09-01.json"
)
SCHEMA_RELATIVE = Path(
    "audit/evidence/sibling-registry-retirement-ledger-v1.schema.json"
)
EXPECTED_LEDGER_SHA256 = (
    "25b226abce58071ffa383753528300b7b2ef7203c47b07bb5f9a1b3b02e08420"
)
EXPECTED_SCHEMA_SHA256 = (
    "1f3e35488bd30a0e91f48601de8862d7639f2db82b41a86f9eb5e2b0afedbec0"
)
EXPECTED_SEMANTIC_ENVELOPE_SHA256 = (
    "e753d8c74cece0c0da71b2e507d43d93b4238d2404e1d8750198f73ef537b1a9"
)
EXPECTED_SECTION_DIGESTS = {
    "cache_examples": "18b2faf75ac0220cb098c920bcfb1f35393478fe32bcbbc4fdb08af34abe99ad",
    "comparisons": "a0221c0c1f6eeedc2177fa3c3a358c00b329424e66fae8340be3eb49fb7b2041",
    "custody": "d770614b04752be6f135dc5d6eb9c90aaed70d5e6a81a478519e6ef1935b6f5a",
    "negative_controls": "f10224565d2db3bfb211aef4cf4401fc565b5a59704d61aaaa2c55f3a5906ccd",
    "object_availability": "8411c6647883f01aaa1b08392f5cbd2de1956647f88c160fd23e76da9de1b5cd",
    "registries": "1ca189e39f7fe21a846ceacb16d9e9bb99415dd56d7a0e7f27870c384c2f7fd5",
    "statuses": "2d16d12841eff639e7cfd136beff8c1e58b2a082d339523ccda66d5721b3509b",
    "unreachable_pairs": "248272fece0dfeca4b4df96acc20f0639f5317e69bf0119060daae9f54ff8826",
}
EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
LOGICAL_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FORBIDDEN_STRING_FRAGMENTS = (
    "/users/",
    "/private/",
    "/tmp/",
    "file://",
    "ssh://",
    "git@",
    "github_pat_",
    "ghp_",
    "begin private key",
    "akia",
)
EXPECTED_REFERENCE_COMMITS = {
    "live-remote-main": "eb9c21ae67e7a5cc9279dd7597cc96ed90f062a9",
    "integration-candidate": "30e6d19bf020b18ef1cc1f9478c2d4acba62ccf1",
}
EXPECTED_REGISTRY_IDS = {
    "legacy-copy",
    "c10-forensic",
    "c10-recovered",
    "c11-fresh",
    "c12-family",
    "program-dossier",
    "program-dossier-backup",
    "publication-synthesis",
    "science-synthesis",
    "sxpid3-independent",
}
EXPECTED_C12_WORKTREE_IDS = {
    "c12-repair",
    "c12-terminal",
    "c12-numerical",
    "c12-orca-integration",
}
EXPECTED_PUBLICATION_CHECKPOINT = {
    "identifier_kind": "sha1_full",
    "object_identifier": "df22846a66bf439b5ee8642166b0599de03a7835",
    "parent_sha1": "662505cd1bba27a34fdd720d5867b6ed791aefc9",
    "status": "established",
    "tree_sha1": "77cf10062d9dce6fcf123187c10ac288694185e0",
}
EXPECTED_COMPARISON_ROWS = {
    "cmp-c10-forensic": (
        "c10-forensic",
        "c10-forensic",
        "live-remote-main",
        "observed_dirty_path_corpus",
        0,
        23,
        12,
        35,
        None,
    ),
    "cmp-c10-recovered": (
        "c10-recovered",
        "c10-recovered",
        "live-remote-main",
        "observed_dirty_path_corpus",
        0,
        20,
        11,
        31,
        None,
    ),
    "cmp-c12-terminal-workflow": (
        "c12-family",
        "c12-terminal",
        "live-remote-main",
        "selected_workflow_blob_corpus",
        5,
        0,
        0,
        5,
        None,
    ),
    "cmp-c12-numerical-to-integration-candidate": (
        "c12-family",
        "c12-numerical",
        "integration-candidate",
        "committed_path_corpus",
        22,
        28,
        0,
        50,
        "32622986f8f0a4b6b62275c61429bd56d439cbde",
    ),
    "cmp-c12-numerical-to-live-remote-main": (
        "c12-family",
        "c12-numerical",
        "live-remote-main",
        "committed_path_corpus",
        23,
        27,
        0,
        50,
        "32622986f8f0a4b6b62275c61429bd56d439cbde",
    ),
    "cmp-c12-orca-integration-to-integration-candidate": (
        "c12-family",
        "c12-orca-integration",
        "integration-candidate",
        "observed_dirty_path_corpus",
        9,
        79,
        30,
        118,
        None,
    ),
    "cmp-c12-orca-integration-to-live-remote-main": (
        "c12-family",
        "c12-orca-integration",
        "live-remote-main",
        "observed_dirty_path_corpus",
        6,
        77,
        35,
        118,
        None,
    ),
    "cmp-publication-synthesis": (
        "publication-synthesis",
        "publication-synthesis",
        "live-remote-main",
        "observed_dirty_path_corpus",
        0,
        0,
        2,
        2,
        None,
    ),
    "cmp-science-synthesis": (
        "science-synthesis",
        "science-synthesis",
        "live-remote-main",
        "observed_dirty_path_corpus",
        0,
        14,
        9,
        23,
        None,
    ),
    "cmp-sxpid3-independent": (
        "sxpid3-independent",
        "sxpid3-independent",
        "live-remote-main",
        "observed_dirty_path_corpus",
        0,
        2,
        2,
        4,
        None,
    ),
}
EXPECTED_NEGATIVE_CONTROL_IDS = {
    "staged-paths",
    "stash-refs",
    "lock-files",
    "alternates",
    "grafts",
    "replace-refs",
    "shallow-registries",
    "partial-clone-registries",
    "tracked-gitlinks",
    "tracked-symbolic-links",
    "active-owner-processes",
}
EXPECTED_NEGATIVE_CONTROL_COUNTS = {
    control_id: (1 if control_id == "partial-clone-registries" else 0)
    for control_id in EXPECTED_NEGATIVE_CONTROL_IDS
}
EXPECTED_PUBLIC_BUNDLE_ARTIFACTS = {
    "custody-c10-forensic-public-receipt-bundle": (
        23650436,
        "d07c43bea4a920f37de5650db4168de95a95cb8635a6c9f8693d7c3d83735b6c",
    ),
    "custody-c12-milestone2-public-receipt-bundle": (
        30319870,
        "29d8a06df72ac2aa5d1994c1a5457b88579f141e8fbddd93fe20533a434d7f47",
    ),
    "custody-c12-milestone-archive-public-receipt-bundle": (
        30382519,
        "0635ed934e7dc4cc1530ac3c4088a9e6b505236f11857a5373dc14ed6fa12f4e",
    ),
    "custody-c12-milestone1-public-receipt-bundle": (
        29880437,
        "40a06fd0815c600e6df0eccf7cd8dd24dd877b69113a449fc0e4898983290058",
    ),
}
EXPECTED_PAIR_CUSTODY = {
    "544c4ceba92228c249de656c01ac5b5214d65d37": {
        "advertised_object_sha1": "544c4ceba92228c249de656c01ac5b5214d65d37",
        "bundle_byte_size": 30319870,
        "bundle_label": "milestone2-clean-repository-2026-08-27.bundle",
        "bundle_sha256": "29d8a06df72ac2aa5d1994c1a5457b88579f141e8fbddd93fe20533a434d7f47",
        "bundle_verify_complete_history": True,
        "custody_artifact_id": "custody-c12-milestone2-public-receipt-bundle",
        "public_receipt_path": "audit/evidence/worktree-and-branch-preservation-2026-08-27.md",
        "receipt_section": "independently_verified_bundle_inventory",
    },
    "c94202db75472380d53a7177c2dfedd04ee5c1c0": {
        "advertised_object_sha1": "c94202db75472380d53a7177c2dfedd04ee5c1c0",
        "bundle_byte_size": 30382519,
        "bundle_label": "milestone-archive-clean-repository-2026-08-27.bundle",
        "bundle_sha256": "0635ed934e7dc4cc1530ac3c4088a9e6b505236f11857a5373dc14ed6fa12f4e",
        "bundle_verify_complete_history": True,
        "custody_artifact_id": "custody-c12-milestone-archive-public-receipt-bundle",
        "public_receipt_path": "audit/evidence/worktree-and-branch-preservation-2026-08-27.md",
        "receipt_section": "independently_verified_bundle_inventory",
    },
    "fd718f20198ab61b669a1d3cf20155d21aa36368": {
        "advertised_object_sha1": "fd718f20198ab61b669a1d3cf20155d21aa36368",
        "bundle_byte_size": 29880437,
        "bundle_label": "milestone1-clean-repository-2026-08-27.bundle",
        "bundle_sha256": "40a06fd0815c600e6df0eccf7cd8dd24dd877b69113a449fc0e4898983290058",
        "bundle_verify_complete_history": True,
        "custody_artifact_id": "custody-c12-milestone1-public-receipt-bundle",
        "public_receipt_path": "audit/evidence/worktree-and-branch-preservation-2026-08-27.md",
        "receipt_section": "independently_verified_bundle_inventory",
    },
}
EXPECTED_BOUNDARY_IDS = {
    "live-registry",
    "git-bundle",
    "archive-checkpoint",
    "restricted-file-package",
    "cache-candidate",
}
ALLOWED_SCHEMA_KEYWORDS = {
    "$defs",
    "$id",
    "$ref",
    "$schema",
    "additionalProperties",
    "const",
    "enum",
    "exclusiveMinimum",
    "items",
    "minItems",
    "minLength",
    "minimum",
    "pattern",
    "properties",
    "required",
    "title",
    "type",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise LedgerError(message)


def canonical_bytes(value: Any, *, pretty: bool = False) -> bytes:
    if pretty:
        text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    else:
        text = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    return text.encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    return sha256_bytes(canonical_bytes(value))


def reject_nonfinite(token: str) -> None:
    raise LedgerError(f"non-finite JSON number is prohibited: {token}")


def reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw: bytes, label: str) -> Any:
    require(not raw.startswith(b"\xef\xbb\xbf"), f"{label}: UTF-8 BOM is prohibited")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise LedgerError(f"{label}: invalid UTF-8: {exc}") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=reject_duplicate_pairs,
            parse_constant=reject_nonfinite,
        )
    except (json.JSONDecodeError, LedgerError) as exc:
        if isinstance(exc, LedgerError):
            raise
        raise LedgerError(f"{label}: invalid JSON: {exc}") from exc


def stat_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def read_single_link_regular(path: Path) -> bytes:
    """Read one stable regular-file pathname without following symbolic links."""
    try:
        before = os.lstat(path)
    except OSError as exc:
        raise LedgerError(f"cannot inspect required file {path}: {exc}") from exc
    require(
        stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
        f"required path is not a single-link regular file: {path}",
    )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LedgerError(f"cannot open required file without following links {path}: {exc}") from exc
    try:
        opened = os.fstat(descriptor)
        require(
            stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1,
            f"opened path is not a single-link regular file: {path}",
        )
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        raw = b"".join(chunks)
        closed = os.fstat(descriptor)
        try:
            after = os.lstat(path)
        except OSError as exc:
            raise LedgerError(f"required file disappeared during read: {path}: {exc}") from exc
        require(
            stat.S_ISREG(after.st_mode)
            and after.st_nlink == 1
            and stat_identity(before)
            == stat_identity(opened)
            == stat_identity(closed)
            == stat_identity(after),
            f"required file identity changed during read: {path}",
        )
        require(len(raw) == closed.st_size, f"required file size changed during read: {path}")
        return raw
    except OSError as exc:
        raise LedgerError(f"cannot read required file {path}: {exc}") from exc
    finally:
        os.close(descriptor)


def json_equal(left: Any, right: Any) -> bool:
    return canonical_bytes(left) == canonical_bytes(right)


def resolve_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    prefix = "#/$defs/"
    require(reference.startswith(prefix), f"external or unsupported schema reference: {reference}")
    name = reference[len(prefix) :]
    require("/" not in name and name, f"malformed schema reference: {reference}")
    definitions = root_schema.get("$defs")
    require(isinstance(definitions, dict), "schema $defs must be an object")
    target = definitions.get(name)
    require(isinstance(target, dict), f"unresolved schema reference: {reference}")
    return target


def matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    raise LedgerError(f"unsupported schema type: {expected}")


def validate_against_schema(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> None:
    if "$ref" in schema:
        require(len(schema) == 1, f"{path}: sibling keywords beside $ref are prohibited")
        validate_against_schema(value, resolve_ref(root_schema, schema["$ref"]), root_schema, path)
        return

    if "const" in schema:
        require(json_equal(value, schema["const"]), f"{path}: value does not match const")
    if "enum" in schema:
        require(
            any(json_equal(value, candidate) for candidate in schema["enum"]),
            f"{path}: value is outside enum",
        )

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        require(
            isinstance(expected_types, list)
            and expected_types
            and all(isinstance(item, str) for item in expected_types),
            f"{path}: malformed schema type",
        )
        require(
            any(matches_type(value, item) for item in expected_types),
            f"{path}: unexpected JSON type",
        )

    if isinstance(value, dict) and schema.get("type") == "object":
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        require(isinstance(properties, dict), f"{path}: schema properties must be an object")
        require(isinstance(required, list), f"{path}: schema required must be an array")
        missing = set(required) - set(value)
        require(not missing, f"{path}: missing required keys: {sorted(missing)}")
        if schema.get("additionalProperties") is False:
            unexpected = set(value) - set(properties)
            require(not unexpected, f"{path}: unexpected keys: {sorted(unexpected)}")
        for key, item in value.items():
            child_schema = properties.get(key)
            if child_schema is not None:
                require(isinstance(child_schema, dict), f"{path}.{key}: malformed child schema")
                validate_against_schema(item, child_schema, root_schema, f"{path}.{key}")

    if isinstance(value, list) and schema.get("type") == "array":
        minimum_items = schema.get("minItems")
        if minimum_items is not None:
            require(len(value) >= minimum_items, f"{path}: too few array items")
        item_schema = schema.get("items")
        if item_schema is not None:
            require(isinstance(item_schema, dict), f"{path}: malformed items schema")
            for index, item in enumerate(value):
                validate_against_schema(item, item_schema, root_schema, f"{path}[{index}]")

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None:
            require(len(value) >= minimum_length, f"{path}: string is too short")
        pattern = schema.get("pattern")
        if pattern is not None:
            require(re.search(pattern, value) is not None, f"{path}: string fails pattern")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None:
            require(value >= minimum, f"{path}: number is below minimum")
        exclusive_minimum = schema.get("exclusiveMinimum")
        if exclusive_minimum is not None:
            require(value > exclusive_minimum, f"{path}: number is below exclusive minimum")


def validate_schema_document(schema: Any) -> dict[str, Any]:
    require(isinstance(schema, dict), "schema root must be an object")
    require(
        schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
        "schema draft identity mismatch",
    )
    require(schema.get("type") == "object", "schema root must type an object")

    def walk(node: Any, path: str, *, definition_map: bool = False) -> None:
        if isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, f"{path}[{index}]")
            return
        if not isinstance(node, dict):
            return
        if definition_map:
            for name, child in node.items():
                require(isinstance(name, str) and name, f"{path}: invalid definition name")
                require(isinstance(child, dict), f"{path}.{name}: definition must be an object")
                walk(child, f"{path}.{name}")
            return
        unknown = set(node) - ALLOWED_SCHEMA_KEYWORDS
        require(not unknown, f"{path}: unsupported schema keywords: {sorted(unknown)}")
        if node.get("type") == "object":
            require(
                node.get("additionalProperties") is False,
                f"{path}: every object schema must set additionalProperties=false",
            )
            properties = node.get("properties")
            required = node.get("required")
            require(isinstance(properties, dict), f"{path}: object properties missing")
            require(isinstance(required, list), f"{path}: object required list missing")
            require(
                len(required) == len(set(required)),
                f"{path}: duplicate required key",
            )
            require(
                set(required) == set(properties),
                f"{path}: closed object must require every declared property",
            )
        reference = node.get("$ref")
        if reference is not None:
            require(isinstance(reference, str), f"{path}: $ref must be a string")
            resolve_ref(schema, reference)
        for key, child in node.items():
            if key == "$defs":
                require(isinstance(child, dict), f"{path}.$defs must be an object")
                walk(child, f"{path}.$defs", definition_map=True)
            elif key == "properties":
                require(isinstance(child, dict), f"{path}.properties must be an object")
                for name, property_schema in child.items():
                    require(
                        isinstance(property_schema, dict),
                        f"{path}.properties.{name}: property schema must be an object",
                    )
                    walk(property_schema, f"{path}.properties.{name}")
            elif key == "items":
                walk(child, f"{path}.items")

    walk(schema, "$schema")
    return schema


def validate_logical_id(value: Any, label: str) -> str:
    require(isinstance(value, str) and LOGICAL_ID_RE.fullmatch(value), f"{label}: invalid logical ID")
    return value


def validate_sha1(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA1_RE.fullmatch(value), f"{label}: invalid SHA-1")
    return value


def validate_sha256(value: Any, label: str) -> str:
    require(isinstance(value, str) and SHA256_RE.fullmatch(value), f"{label}: invalid SHA-256")
    return value


def scan_for_private_locators(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_for_private_locators(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            scan_for_private_locators(child, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    lowered = value.lower()
    require(
        not re.match(r"^(?:/|~[/\\]|[a-zA-Z]:[/\\])", value),
        f"{path}: absolute or home-relative locator is prohibited",
    )
    for fragment in FORBIDDEN_STRING_FRAGMENTS:
        require(fragment not in lowered, f"{path}: prohibited locator or secret-like fragment")


def unique_values(values: list[str], label: str) -> None:
    require(len(values) == len(set(values)), f"{label}: duplicate identifiers")


def validate_ledger_document(
    ledger: Any,
    schema: dict[str, Any],
    *,
    enforce_section_digests: bool = True,
    enforce_semantic_envelope: bool = True,
) -> dict[str, Any]:
    require(isinstance(ledger, dict), "ledger root must be an object")
    validate_against_schema(ledger, schema, schema)
    scan_for_private_locators(ledger)

    require(
        ledger["schema_id"] == "pid-rs/sibling-registry-retirement-ledger"
        and ledger["schema_revision"] == 1
        and ledger["record_id"] == "SRRL-20260901-01",
        "ledger identity mismatch",
    )
    observation = ledger["observation"]
    expected_observation = {
        "architecture": "arm64",
        "ended_at_utc": "2026-09-01T07:38:43Z",
        "git_object_format": "sha1",
        "git_version": "2.55.0",
        "host_build": "25F80",
        "host_operating_system": "macOS",
        "host_operating_system_version": "26.5.1",
        "mode": "read_only",
        "observation_id": "sibling-audit-20260901-073207z",
        "started_at_utc": "2026-09-01T07:32:07Z",
    }
    require(observation == expected_observation, "observation window or toolchain drift")

    checker_contract = ledger["checker_contract"]
    require(
        checker_contract["classification"] == "snapshot_integrity_validator"
        and checker_contract["external_replay_required_for_cleanup"] is True,
        "checker replay boundary drift",
    )
    require(
        "does not access sibling registries" in checker_contract["does_not"].lower()
        and "does not freshly replay" in checker_contract["does_not"].lower(),
        "checker contract overstates external replay",
    )

    references = ledger["reference_commits"]
    reference_ids = [validate_logical_id(item["reference_id"], "reference ID") for item in references]
    unique_values(reference_ids, "reference commits")
    reference_map = {
        item["reference_id"]: validate_sha1(item["commit_sha1"], "reference commit")
        for item in references
    }
    require(reference_map == EXPECTED_REFERENCE_COMMITS, "reference commit set drift")

    registries = ledger["registries"]
    registry_ids = [validate_logical_id(item["registry_id"], "registry ID") for item in registries]
    common_ids = [
        validate_logical_id(item["common_git_directory_id"], "common Git directory ID")
        for item in registries
    ]
    unique_values(registry_ids, "registries")
    unique_values(common_ids, "common Git directories")
    require(set(registry_ids) == EXPECTED_REGISTRY_IDS, "registry inventory drift")
    require(len(registries) == 10 and len(common_ids) == 10, "ten-registry scope drift")

    worktrees: list[tuple[str, dict[str, Any]]] = []
    archive_count = 0
    for registry in registries:
        registry_id = registry["registry_id"]
        validate_sha1(registry["registry_head_sha1"], f"{registry_id} registry HEAD")
        validate_sha1(registry["registry_tree_sha1"], f"{registry_id} registry tree")
        members = registry["worktrees"]
        require(registry["bare"] == (len(members) == 0), f"{registry_id}: bare/worktree mismatch")
        if members:
            require(
                members[0]["head_sha1"] == registry["registry_head_sha1"]
                and members[0]["tree_sha1"] == registry["registry_tree_sha1"],
                f"{registry_id}: registry anchor is not its first worktree",
            )
        checkpoint = registry["archive_checkpoint"]
        checkpoint_status = checkpoint["status"]
        checkpoint_kind = checkpoint["identifier_kind"]
        checkpoint_value = checkpoint["object_identifier"]
        checkpoint_parent = checkpoint["parent_sha1"]
        checkpoint_tree = checkpoint["tree_sha1"]
        if checkpoint_status == "not_established":
            require(
                checkpoint_kind == "none"
                and checkpoint_value == ""
                and checkpoint_parent is None
                and checkpoint_tree is None,
                f"{registry_id}: absent checkpoint must carry no object identifier",
            )
        elif checkpoint_status == "established":
            validate_sha1(checkpoint_value, f"{registry_id} archive checkpoint")
            require(checkpoint_kind == "sha1_full", f"{registry_id}: full checkpoint kind mismatch")
            if checkpoint_parent is not None:
                validate_sha1(checkpoint_parent, f"{registry_id} archive checkpoint parent")
            if checkpoint_tree is not None:
                validate_sha1(checkpoint_tree, f"{registry_id} archive checkpoint tree")
            archive_count += 1
        else:
            raise LedgerError(f"{registry_id}: unknown archive checkpoint status")
        for worktree in members:
            worktree_id = validate_logical_id(worktree["worktree_id"], "worktree ID")
            validate_sha1(worktree["head_sha1"], f"{worktree_id} HEAD")
            validate_sha1(worktree["tree_sha1"], f"{worktree_id} tree")
            branch_label = validate_logical_id(worktree["branch_label"], f"{worktree_id} branch label")
            if worktree["head_mode"] == "detached":
                require(branch_label == "none", f"{worktree_id}: detached HEAD must use branch label none")
            else:
                require(branch_label != "none", f"{worktree_id}: named branch lacks a label")
            status_record = worktree["status"]
            validate_sha256(status_record["capture_sha256"], f"{worktree_id} status capture")
            for count_name in ("staged", "unstaged", "untracked"):
                count = status_record[count_name]
                require(
                    isinstance(count, int) and not isinstance(count, bool) and count >= 0,
                    f"{worktree_id}: invalid {count_name} count",
                )
            if sum(status_record[name] for name in ("staged", "unstaged", "untracked")) == 0:
                require(
                    status_record["capture_sha256"] == EMPTY_SHA256,
                    f"{worktree_id}: clean status must bind the empty capture digest",
                )
            worktrees.append((registry_id, worktree))

    worktree_ids = [item[1]["worktree_id"] for item in worktrees]
    unique_values(worktree_ids, "worktrees")
    require(len(worktrees) == 12, "worktree count drift")
    c12_members = {
        worktree["worktree_id"]
        for registry_id, worktree in worktrees
        if registry_id == "c12-family"
    }
    require(c12_members == EXPECTED_C12_WORKTREE_IDS, "C12 four-worktree coverage drift")
    require(
        sum(1 for item in registries if item["bare"]) == 1,
        "bare registry count drift",
    )
    require(archive_count == 7, "archive checkpoint count drift")
    publication_registry = next(
        item for item in registries if item["registry_id"] == "publication-synthesis"
    )
    require(
        publication_registry["archive_checkpoint"] == EXPECTED_PUBLICATION_CHECKPOINT,
        "publication-synthesis exact commit/tree/parent checkpoint drift",
    )
    require(
        publication_registry["registry_head_sha1"]
        == EXPECTED_PUBLICATION_CHECKPOINT["parent_sha1"],
        "publication-synthesis archive parent does not match the observed worktree HEAD",
    )

    status_rows = [
        {
            "capture_sha256": worktree["status"]["capture_sha256"],
            "registry_id": registry_id,
            "staged": worktree["status"]["staged"],
            "unstaged": worktree["status"]["unstaged"],
            "untracked": worktree["status"]["untracked"],
            "worktree_id": worktree["worktree_id"],
        }
        for registry_id, worktree in worktrees
    ]
    status_digest = canonical_sha256(status_rows)
    registry_digest = canonical_sha256(registries)
    if enforce_section_digests:
        require(status_digest == EXPECTED_SECTION_DIGESTS["statuses"], "status inventory drift")
        require(
            registry_digest == EXPECTED_SECTION_DIGESTS["registries"],
            "registry inventory digest drift",
        )

    worktree_lookup = {(registry_id, worktree["worktree_id"]) for registry_id, worktree in worktrees}
    comparisons = ledger["comparisons"]
    comparison_ids = [
        validate_logical_id(item["comparison_id"], "comparison ID") for item in comparisons
    ]
    unique_values(comparison_ids, "comparisons")
    require(
        set(comparison_ids) == set(EXPECTED_COMPARISON_ROWS),
        "comparison identity set drift",
    )
    for comparison in comparisons:
        require(
            (comparison["registry_id"], comparison["worktree_id"]) in worktree_lookup,
            f"{comparison['comparison_id']}: comparison worktree is outside the registry inventory",
        )
        require(
            comparison["target_id"] in EXPECTED_REFERENCE_COMMITS,
            f"{comparison['comparison_id']}: comparison target is not a declared reference",
        )
        require(
            comparison["total"]
            == comparison["exact"] + comparison["evolved"] + comparison["absent"],
            f"{comparison['comparison_id']}: exact/evolved/absent partition mismatch",
        )
        support = comparison["supporting_commit_sha1"]
        if support is not None:
            validate_sha1(support, f"{comparison['comparison_id']} supporting commit")
        observed_row = (
            comparison["registry_id"],
            comparison["worktree_id"],
            comparison["target_id"],
            comparison["basis"],
            comparison["exact"],
            comparison["evolved"],
            comparison["absent"],
            comparison["total"],
            comparison["supporting_commit_sha1"],
        )
        require(
            observed_row == EXPECTED_COMPARISON_ROWS[comparison["comparison_id"]],
            f"{comparison['comparison_id']}: target-specific comparison row drift",
        )
    require(len(comparisons) == 10, "comparison record count drift")
    for worktree_id in ("c12-numerical", "c12-orca-integration"):
        target_rows = {
            item["target_id"]: item
            for item in comparisons
            if item["registry_id"] == "c12-family"
            and item["worktree_id"] == worktree_id
        }
        require(
            set(target_rows) == {"integration-candidate", "live-remote-main"},
            f"{worktree_id}: candidate/remote-main comparison pair drift",
        )
        candidate_row = target_rows["integration-candidate"]
        remote_row = target_rows["live-remote-main"]
        require(
            candidate_row["basis"] == remote_row["basis"]
            and candidate_row["total"] == remote_row["total"]
            and candidate_row["supporting_commit_sha1"]
            == remote_row["supporting_commit_sha1"],
            f"{worktree_id}: paired comparison corpus identity drift",
        )
    comparison_digest = canonical_sha256(comparisons)
    if enforce_section_digests:
        require(
            comparison_digest == EXPECTED_SECTION_DIGESTS["comparisons"],
            "comparison inventory digest drift",
        )

    relations = ledger["relations"]
    require(len(relations) == 1, "relation inventory drift")
    relation = relations[0]
    require(
        relation
        == {
            "ahead": 0,
            "behind": 52,
            "relation": "ancestor",
            "relation_id": "c12-terminal-to-integration-candidate",
            "source_sha1": "f7811023da638fe7ede921b7b51c32fef8eb2c80",
            "target_reference_id": "integration-candidate",
        },
        "C12 terminal ancestry relation drift",
    )

    controls = ledger["negative_controls"]
    control_ids = [validate_logical_id(item["control_id"], "control ID") for item in controls]
    unique_values(control_ids, "negative controls")
    require(set(control_ids) == EXPECTED_NEGATIVE_CONTROL_IDS, "negative-control set drift")
    control_counts = {item["control_id"]: item["observed_count"] for item in controls}
    require(
        control_counts == EXPECTED_NEGATIVE_CONTROL_COUNTS,
        "negative-control counts drift; exactly one partial-clone registry is required",
    )
    negative_digest = canonical_sha256(controls)
    if enforce_section_digests:
        require(
            negative_digest == EXPECTED_SECTION_DIGESTS["negative_controls"],
            "negative-control digest drift",
        )

    availability = ledger["object_availability"]
    partial_observations = availability["partial_clone_observations"]
    custody_replays = availability["custody_replays"]
    require(
        len(partial_observations) == 1 and len(custody_replays) == 1,
        "object-availability observation count drift",
    )
    partial = partial_observations[0]
    require(
        partial
        == {
            "global_registry_completeness_established": False,
            "lazy_fetch_disabled": True,
            "missing_object_count": 0,
            "observed_head_sha1": "337fe9b7f7cf30a8f00138310ce0398d9e95b9c5",
            "partial_clone_filter": "blob:none",
            "partial_clone_filter_config_count": 1,
            "promisor_pack_marker_count": 6,
            "promisor_remote_config_count": 1,
            "promisor_remote_value": "true",
            "registry_id": "c10-forensic",
            "remote_label": "origin",
            "scope": "objects_reachable_from_observed_head",
            "verification": "git_rev_list_objects_missing_print",
        },
        "c10-forensic promisor configuration or bounded head-availability check drift",
    )
    c10_registry = next(item for item in registries if item["registry_id"] == "c10-forensic")
    require(
        partial["observed_head_sha1"] == c10_registry["registry_head_sha1"],
        "partial-clone availability check is not bound to the observed registry HEAD",
    )
    replay = custody_replays[0]
    require(
        replay
        == {
            "archive_commit_sha1": "9cef1844d9994e72eab0c7069f3c02b03124b7f0",
            "bundle_byte_size": 23650436,
            "bundle_label": "c10-forensic-dirty-worktree-2026-08-27.bundle",
            "bundle_sha256": "d07c43bea4a920f37de5650db4168de95a95cb8635a6c9f8693d7c3d83735b6c",
            "bundle_verify_complete_history": True,
            "custody_artifact_id": "custody-c10-forensic-public-receipt-bundle",
            "fresh_isolated_bare_repository": True,
            "fsck_full_strict_no_reflogs_passed": True,
            "global_registry_completeness_established": False,
            "lazy_fetch_disabled": True,
            "public_receipt_path": "audit/evidence/worktree-and-branch-preservation-2026-08-27.md",
            "receipt_section": "independently_verified_bundle_inventory",
            "registry_id": "c10-forensic",
            "replay_id": "c10-forensic-archive-bundle-replay",
            "scope": "exact_archive_ref_from_restricted_bundle",
        },
        "c10-forensic isolated bundle-custody replay drift",
    )
    require(
        replay["archive_commit_sha1"]
        == c10_registry["archive_checkpoint"]["object_identifier"],
        "c10-forensic custody replay is not bound to the recorded archive checkpoint",
    )
    require(
        partial["scope"] != replay["scope"]
        and partial["global_registry_completeness_established"] is False
        and replay["global_registry_completeness_established"] is False,
        "live object availability and bundle custody were conflated",
    )
    availability_digest = canonical_sha256(availability)
    if enforce_section_digests:
        require(
            availability_digest == EXPECTED_SECTION_DIGESTS["object_availability"],
            "object-availability inventory digest drift",
        )

    custody = ledger["custody_artifacts"]
    custody_ids = [validate_logical_id(item["artifact_id"], "custody artifact ID") for item in custody]
    unique_values(custody_ids, "custody artifacts")
    custody_by_id = {item["artifact_id"]: item for item in custody}
    for artifact in custody:
        validate_sha256(artifact["sha256"], f"{artifact['artifact_id']} artifact digest")
        require(artifact["byte_size"] > 0 and artifact["content_count"] > 0, "empty custody artifact")
    require(len(custody) == 9, "custody artifact count drift")
    require(
        sum(1 for item in custody if item["custody_class"] == "restricted_nonpublic") == 1,
        "restricted-nonpublic custody boundary drift",
    )
    require(
        set(EXPECTED_PUBLIC_BUNDLE_ARTIFACTS).issubset(custody_by_id),
        "public-receipt bundle custody inventory drift",
    )
    for artifact_id, (byte_size, digest) in EXPECTED_PUBLIC_BUNDLE_ARTIFACTS.items():
        artifact = custody_by_id[artifact_id]
        require(
            artifact["artifact_kind"] == "git_bundle"
            and artifact["byte_size"] == byte_size
            and artifact["sha256"] == digest
            and artifact["content_count"] == 1
            and artifact["content_count_unit"] == "refs"
            and artifact["custody_class"] == "restricted",
            f"{artifact_id}: public-receipt custody metadata drift",
        )
    replay_artifact = custody_by_id.get(replay["custody_artifact_id"])
    require(replay_artifact is not None, "c10 custody replay artifact is absent")
    require(
        replay_artifact["byte_size"] == replay["bundle_byte_size"]
        and replay_artifact["sha256"] == replay["bundle_sha256"],
        "c10 custody replay does not resolve to its declared artifact bytes",
    )
    custody_digest = canonical_sha256(custody)
    if enforce_section_digests:
        require(
            custody_digest == EXPECTED_SECTION_DIGESTS["custody"],
            "custody inventory digest drift",
        )

    boundaries = ledger["custody_boundaries"]
    boundary_ids = [validate_logical_id(item["boundary_id"], "custody boundary ID") for item in boundaries]
    unique_values(boundary_ids, "custody boundaries")
    require(set(boundary_ids) == EXPECTED_BOUNDARY_IDS, "custody boundary inventory drift")

    cache = ledger["cache_candidates"]
    require(cache["allocated_bytes"] == 52718612480, "cache allocated-byte total drift")
    require(
        cache["candidate_count_status"] == "not_established"
        and cache["candidate_count"] is None,
        "cache candidate count must remain explicitly unestablished",
    )
    require(
        cache["classification"] == "preliminary_non_authorizing_candidates"
        and cache["deletion_authorized"] is False
        and cache["example_values_are_aggregate_inputs"] is False,
        "cache non-authorizing boundary drift",
    )
    examples = cache["examples"]
    require(len(examples) == 11, "cache example inventory drift")
    for example in examples:
        require(
            (example["registry_id"], example["worktree_id"]) in worktree_lookup,
            "cache example refers outside the observed worktrees",
        )
        require(
            isinstance(example["approximate_decimal_gb"], (int, float))
            and not isinstance(example["approximate_decimal_gb"], bool)
            and math.isfinite(float(example["approximate_decimal_gb"]))
            and example["approximate_decimal_gb"] > 0,
            "invalid approximate cache example size",
        )
    cache_digest = canonical_sha256(examples)
    if enforce_section_digests:
        require(
            cache_digest == EXPECTED_SECTION_DIGESTS["cache_examples"],
            "cache example inventory digest drift",
        )

    pairs = ledger["unreachable_commit_pairs"]
    pair_ids = [validate_logical_id(item["pair_id"], "unreachable pair ID") for item in pairs]
    unique_values(pair_ids, "unreachable commit pairs")
    commit_ids: list[str] = []
    patch_ids: list[str] = []
    for pair in pairs:
        unreachable = validate_sha1(pair["unreachable_commit_sha1"], "unreachable commit")
        reachable = validate_sha1(pair["reachable_commit_sha1"], "reachable comparison commit")
        validate_sha1(pair["tree_sha1"], "pair tree")
        patch_ids.append(validate_sha1(pair["stable_patch_id"], "stable patch ID"))
        require(unreachable != reachable, "unreachable and reachable commit identities collapse")
        require(pair["exact_commit_identity_equal"] is False, "pair falsely claims exact commit identity")
        require(pair["tree_identity_equal"] is True, "pair tree-equality observation drift")
        require(
            pair["disposition"]
            == "same_patch_and_tree_evidence_exact_commit_custody_bound_no_pair_specific_registry_retention",
            "unreachable commit disposition drift",
        )
        require(pair["live_ref_reachable"] is False, "pair live-ref reachability drift")
        require(pair["custody_bound"] is True, "exact commit lost its custody binding")
        require(
            pair["registry_retention_required_for_pair"] is False,
            "custody-bound pair incorrectly retains the registry",
        )
        binding = pair["custody_binding"]
        require(
            binding == EXPECTED_PAIR_CUSTODY.get(unreachable),
            "pair custody evidence does not match the public preservation receipt",
        )
        require(
            binding["advertised_object_sha1"] == unreachable,
            "pair custody artifact advertises a different object",
        )
        bound_artifact = custody_by_id.get(binding["custody_artifact_id"])
        require(bound_artifact is not None, "pair custody artifact is absent from the inventory")
        require(
            bound_artifact["artifact_kind"] == "git_bundle"
            and bound_artifact["byte_size"] == binding["bundle_byte_size"]
            and bound_artifact["sha256"] == binding["bundle_sha256"],
            "pair custody binding does not resolve to the declared artifact bytes",
        )
        commit_ids.extend((unreachable, reachable))
    require(len(pairs) == 3, "unreachable pair count drift")
    unique_values(commit_ids, "unreachable/reachable commit identities")
    unique_values(patch_ids, "stable patch IDs")
    require(
        {pair["unreachable_commit_sha1"] for pair in pairs}
        == set(EXPECTED_PAIR_CUSTODY),
        "custody-bound live-unreachable commit set drift",
    )
    pair_digest = canonical_sha256(pairs)
    if enforce_section_digests:
        require(
            pair_digest == EXPECTED_SECTION_DIGESTS["unreachable_pairs"],
            "unreachable-pair inventory digest drift",
        )

    authorization = ledger["authorization"]
    require(authorization["decision"] == "retain_and_adjudicate", "authorization decision drift")
    require(
        authorization["retention_basis"] == "genuinely_unadjudicated_scope_only"
        and authorization["c12_custody_bound_pairs_require_registry_retention"] is False,
        "custody-bound pairs incorrectly contribute to the registry-retention basis",
    )
    for key, value in authorization.items():
        if key not in {"decision", "retention_basis"}:
            require(value is False, f"{key}: this ledger grants no authority")

    staged = sum(row["staged"] for row in status_rows)
    unstaged = sum(row["unstaged"] for row in status_rows)
    untracked = sum(row["untracked"] for row in status_rows)
    clean = sum(
        1 for row in status_rows if row["staged"] + row["unstaged"] + row["untracked"] == 0
    )
    expected_summary = {
        "archive_checkpoint_count": archive_count,
        "bare_registry_count": sum(1 for item in registries if item["bare"]),
        "cache_example_inventory_sha256": cache_digest,
        "clean_worktree_count": clean,
        "common_git_directory_count": len(common_ids),
        "comparison_absent": sum(item["absent"] for item in comparisons),
        "comparison_evolved": sum(item["evolved"] for item in comparisons),
        "comparison_exact": sum(item["exact"] for item in comparisons),
        "comparison_inventory_sha256": comparison_digest,
        "comparison_record_count": len(comparisons),
        "comparison_total": sum(item["total"] for item in comparisons),
        "custody_artifact_count": len(custody),
        "custody_inventory_sha256": custody_digest,
        "dirty_worktree_count": len(status_rows) - clean,
        "negative_control_inventory_sha256": negative_digest,
        "object_availability_inventory_sha256": availability_digest,
        "registry_count": len(registries),
        "registry_inventory_sha256": registry_digest,
        "status_inventory_sha256": status_digest,
        "total_staged": staged,
        "total_unstaged": unstaged,
        "total_untracked": untracked,
        "unreachable_pair_count": len(pairs),
        "unreachable_pair_inventory_sha256": pair_digest,
        "worktree_count": len(status_rows),
    }
    require(ledger["summary"] == expected_summary, "summary is not the exact derived projection")
    require(
        (staged, unstaged, untracked, clean, len(status_rows) - clean) == (0, 122, 110, 5, 7),
        "status aggregate drift",
    )
    require(
        (
            expected_summary["comparison_exact"],
            expected_summary["comparison_evolved"],
            expected_summary["comparison_absent"],
            expected_summary["comparison_total"],
        )
        == (65, 270, 101, 436),
        "comparison aggregate drift",
    )

    semantic_envelope = {key: value for key, value in ledger.items() if key != "summary"}
    if enforce_semantic_envelope:
        require(
            canonical_sha256(semantic_envelope) == EXPECTED_SEMANTIC_ENVELOPE_SHA256,
            "semantic envelope drift",
        )
    return ledger


def validate_artifacts(ledger_raw: bytes, schema_raw: bytes) -> dict[str, Any]:
    require(sha256_bytes(ledger_raw) == EXPECTED_LEDGER_SHA256, "ledger file SHA-256 drift")
    require(sha256_bytes(schema_raw) == EXPECTED_SCHEMA_SHA256, "schema file SHA-256 drift")
    ledger = parse_json(ledger_raw, "ledger")
    schema = validate_schema_document(parse_json(schema_raw, "schema"))
    require(ledger_raw == canonical_bytes(ledger, pretty=True), "ledger JSON is not canonical")
    require(schema_raw == canonical_bytes(schema, pretty=True), "schema JSON is not canonical")
    return validate_ledger_document(ledger, schema)


def main() -> int:
    repository_root = Path(__file__).resolve().parent.parent
    ledger_path = repository_root / LEDGER_RELATIVE
    schema_path = repository_root / SCHEMA_RELATIVE
    try:
        ledger_raw = read_single_link_regular(ledger_path)
        schema_raw = read_single_link_regular(schema_path)
        ledger = validate_artifacts(ledger_raw, schema_raw)
    except LedgerError as exc:
        print(f"FAIL sibling-registry retirement ledger: {exc}", file=sys.stderr)
        return 1
    summary = ledger["summary"]
    print(
        "PASS sibling-registry retirement ledger: "
        f"{summary['registry_count']} registries, "
        f"{summary['worktree_count']} worktrees, "
        f"status={summary['total_staged']}/"
        f"{summary['total_unstaged']}/{summary['total_untracked']}, "
        f"comparisons={summary['comparison_exact']}/"
        f"{summary['comparison_evolved']}/{summary['comparison_absent']}, "
        "deletion_authorized=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
