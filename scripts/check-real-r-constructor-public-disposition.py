#!/usr/bin/env python3
"""Validate the inert, privacy-safe Real-R constructor V8 public disposition."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import stat
import sys
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from json_schema_subset import (  # noqa: E402
    SchemaValidationError,
    validate as validate_json_schema,
)


if sys.version_info < (3, 11):
    raise SystemExit(
        "check-real-r-constructor-public-disposition.py requires Python 3.11+"
    )


ROOT = SCRIPT_DIR.parent
ARCHIVE_RELATIVE = Path("audit/archive/real-r-constructor-v8-cb5a33ca-db79299d")
EXPECTED_FILES = (
    "ARCHITECTURE.md",
    "DISPOSITION.md",
    "INDEX.json",
    "INDEX.schema.json",
)
EXPECTED_IDENTITIES = {
    "ARCHITECTURE.md": (
        3721,
        "5afd5e9e2aade4f458d015002c2e8d5e5e0d69580d3e01b2fbac25149e1b2614",
    ),
    "DISPOSITION.md": (
        4598,
        "1437398882a38e26f0bdb57e1100f6dafcca00851029884d7d2e2010c45bc013",
    ),
    "INDEX.json": (
        3436,
        "a681fa30cddd468dde3b8851bf3c9ba969d4ff669824b3e61291179f51636652",
    ),
    "INDEX.schema.json": (
        9640,
        "255d8efa98cc884516701051a22287b49a75b9b7760150c3569f8aa4e3355f85",
    ),
}
EXPECTED_SUPPORT = {
    "ARCHITECTURE.md": (
        "architecture_record",
        EXPECTED_IDENTITIES["ARCHITECTURE.md"],
    ),
    "DISPOSITION.md": (
        "human_disposition",
        EXPECTED_IDENTITIES["DISPOSITION.md"],
    ),
    "INDEX.schema.json": (
        "index_schema",
        EXPECTED_IDENTITIES["INDEX.schema.json"],
    ),
}
FORBIDDEN_PUBLIC_BYTES = (
    b"/" + b"Users/",
    b"/private" + b"/tmp/",
    b".local/state/" + b"gh/device-id",
    b"construct_validate_real_r.py",
    b"audit_real_r_constructor.py",
)


class PublicDispositionError(ValueError):
    """The public disposition is malformed, overclaimed, or privacy-unsafe."""


def require(condition: bool, code: str, detail: str) -> None:
    if not condition:
        raise PublicDispositionError(f"{code}: {detail}")


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise PublicDispositionError(f"JSON.duplicate_key: {key!r}")
        result[key] = value
    return result


def reject_float(token: str) -> float:
    raise PublicDispositionError(f"JSON.float: floating value forbidden: {token!r}")


def parse_json(raw: bytes, *, label: str) -> Any:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as error:
        raise PublicDispositionError(f"{label}.encoding: ASCII required") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_float=reject_float,
            parse_constant=reject_float,
        )
    except json.JSONDecodeError as error:
        raise PublicDispositionError(f"{label}.json: {error.msg}") from error
    return value


def require_finite_json(value: Any, *, path: str = "$") -> None:
    if value is None or isinstance(value, (bool, int, str)):
        return
    if isinstance(value, float):
        require(math.isfinite(value), "JSON.nonfinite", path)
        raise PublicDispositionError(f"JSON.float: {path}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            require_finite_json(item, path=f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            require(type(key) is str, "JSON.key_type", path)
            require_finite_json(item, path=f"{path}.{key}")
        return
    raise PublicDispositionError(f"JSON.type: {path}: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    require_finite_json(value)
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("ascii")


def file_identity(path: Path, *, label: str) -> tuple[bytes, int, str]:
    try:
        metadata = path.lstat()
    except OSError as error:
        raise PublicDispositionError(f"{label}.lstat: {error}") from error
    require(stat.S_ISREG(metadata.st_mode), f"{label}.type", "regular file required")
    require(metadata.st_nlink == 1, f"{label}.links", "single-link file required")
    require(
        stat.S_IMODE(metadata.st_mode) == 0o644,
        f"{label}.mode",
        "tracked public metadata must be mode 0644",
    )
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise PublicDispositionError(f"{label}.read: {error}") from error
    digest = hashlib.sha256(raw).hexdigest()
    return raw, len(raw), digest


def validate_index_semantics(index: dict[str, Any], schema: dict[str, Any]) -> None:
    try:
        validate_json_schema(index, schema, name="public disposition INDEX.json")
    except SchemaValidationError as error:
        raise PublicDispositionError(f"INDEX.schema: {error}") from error

    architecture = index["architecture"]
    require(type(architecture) is dict, "INDEX.architecture", "object required")
    require(
        architecture["r10_controls"] + architecture["local_controls"]
        == architecture["total_controls"],
        "INDEX.control_arithmetic",
        "62 + 36 must equal 98",
    )
    require(
        architecture["packet_events_per_phase"] * 2
        == architecture["combined_authority_events"],
        "INDEX.event_arithmetic",
        "106 * 2 must equal 212",
    )

    support = index["support_files"]
    require(type(support) is list, "INDEX.support", "array required")
    support_by_name: dict[str, dict[str, Any]] = {}
    for record in support:
        require(type(record) is dict, "INDEX.support.record", "object required")
        relative = Path(record["path"])
        require(
            relative.parent == ARCHIVE_RELATIVE,
            "INDEX.support.path",
            str(relative),
        )
        require(
            relative.name not in support_by_name,
            "INDEX.support.duplicate",
            relative.name,
        )
        support_by_name[relative.name] = record
    require(
        set(support_by_name) == set(EXPECTED_SUPPORT),
        "INDEX.support.inventory",
        "drift",
    )
    for name, (role, (size, digest)) in EXPECTED_SUPPORT.items():
        record = support_by_name[name]
        require(
            record["role"] == role, f"INDEX.support.{name}.role", str(record["role"])
        )
        require(
            record["bytes"] == size, f"INDEX.support.{name}.bytes", str(record["bytes"])
        )
        require(
            record["sha256"] == digest,
            f"INDEX.support.{name}.sha256",
            str(record["sha256"]),
        )

    sources = index["source_identities"]
    require(type(sources) is list and len(sources) == 2, "INDEX.sources", "two records")
    require(
        [record["role"] for record in sources]
        == ["constructor", "independent_auditor_design"],
        "INDEX.sources.order",
        "constructor then auditor",
    )
    require(
        all(record["included_in_public_branch"] is False for record in sources),
        "INDEX.sources.withheld",
        "payload inclusion forbidden",
    )
    require(index["current_authority"] is False, "INDEX.authority", "must be false")
    require(index["privacy"]["payload_withheld"] is True, "INDEX.privacy", "withheld")
    require(
        index["privacy"]["explicit_owner_public_disclosure_approval_recorded"] is False,
        "INDEX.privacy_approval",
        "must remain false until separately authorized",
    )
    require(
        index["licensing"]["payload_publication_rights_confirmed"] is False,
        "INDEX.payload_rights",
        "must remain false until separately established",
    )
    require(
        index["execution"]["full_runtime_replayed_for_public_disposition"] is False,
        "INDEX.runtime_scope",
        "public disposition is metadata-only",
    )


def validate_public_disposition(root: Path = ROOT) -> dict[str, Any]:
    archive = root / ARCHIVE_RELATIVE
    try:
        archive_metadata = archive.lstat()
    except OSError as error:
        raise PublicDispositionError(f"ARCHIVE.lstat: {error}") from error
    require(
        stat.S_ISDIR(archive_metadata.st_mode), "ARCHIVE.type", "directory required"
    )

    observed_names = tuple(sorted(entry.name for entry in archive.iterdir()))
    require(observed_names == EXPECTED_FILES, "ARCHIVE.inventory", repr(observed_names))

    observed: dict[str, tuple[bytes, int, str]] = {}
    for name in EXPECTED_FILES:
        raw, size, digest = file_identity(archive / name, label=f"FILE.{name}")
        for forbidden in FORBIDDEN_PUBLIC_BYTES:
            require(
                forbidden not in raw,
                f"FILE.{name}.privacy",
                "forbidden raw path or withheld source name",
            )
        expected_size, expected_digest = EXPECTED_IDENTITIES[name]
        require(size == expected_size, f"FILE.{name}.bytes", str(size))
        require(digest == expected_digest, f"FILE.{name}.sha256", digest)
        observed[name] = (raw, size, digest)

    index_raw = observed["INDEX.json"][0]
    schema_raw = observed["INDEX.schema.json"][0]
    index = parse_json(index_raw, label="INDEX")
    schema = parse_json(schema_raw, label="SCHEMA")
    require(type(index) is dict, "INDEX.type", "object required")
    require(type(schema) is dict, "SCHEMA.type", "object required")
    require(
        index_raw == canonical_json_bytes(index), "INDEX.canonical", "exact one-LF form"
    )
    validate_index_semantics(index, schema)

    return {
        "archive_id": index["archive_id"],
        "current_authority": False,
        "directory_files": len(EXPECTED_FILES),
        "format": "pid-rs/real-r-constructor-public-disposition-check/v1",
        "index_sha256": observed["INDEX.json"][2],
        "payload_present": False,
        "status": "real_r_constructor_public_disposition_passed",
    }


def main() -> int:
    try:
        result = validate_public_disposition()
    except (OSError, PublicDispositionError, SchemaValidationError) as error:
        print(f"real-r constructor public disposition failed: {error}", file=sys.stderr)
        return 1
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
