#!/usr/bin/env python3
"""Check the frozen inert archive without executing historical payloads.

This binds a selected public projection. Private raw bytes, historical processes,
mathematical truth, and coordinated owner reseals are outside this check. Files
and their parent directories must remain stable during the bounded reads.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_RELATIVE = "audit/archive/mgw-target-copy-development-20260911"
EXPECTED_MANIFEST_SHA256 = "0972b3cf26a9aecbf48fb0a706a88675d88db0aa9925929e70f9dc3d83b1004c"
MAX_BYTES = 2 * 1024 * 1024
HEX256 = re.compile(r"[0-9a-f]{64}\Z")


class ArchiveError(ValueError):
    """A public preservation invariant failed."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ArchiveError(message)


def identity(info: os.stat_result) -> tuple[int, ...]:
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_regular(path: Path) -> bytes:
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
            f"not a single-link regular file: {path.name}")
    require(stat.S_IMODE(before.st_mode) == 0o644, f"unexpected file mode: {path.name}")
    require(before.st_size <= MAX_BYTES, f"file exceeds size limit: {path.name}")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        require(identity(before) == identity(os.fstat(stream.fileno())), "file changed before read")
        first = stream.read(MAX_BYTES + 1)
        stream.seek(0)
        second = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    require(first == second and len(first) == before.st_size, "file bytes changed during read")
    require(identity(before) == identity(after) == identity(path.lstat()),
            "file metadata changed during read")
    return first


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> object:
    raise ArchiveError(f"nonfinite JSON constant: {value}")


def payload_path(value: object) -> str:
    require(type(value) is str, "payload path must be a string")
    path = PurePosixPath(value)
    require(not path.is_absolute() and len(path.parts) >= 2
            and path.parts[0] == "payloads" and path.suffix == ".txt"
            and all(part not in (".", "..") for part in path.parts)
            and path.as_posix() == value and "\\" not in value
            and all(ord(char) >= 32 and ord(char) != 127 for char in value),
            f"unsafe or non-inert payload path: {value!r}")
    return value


def check_archive(root: Path) -> tuple[int, int]:
    archive = root / ARCHIVE_RELATIVE
    for directory in (root, root / "audit", root / "audit/archive", archive):
        require(stat.S_ISDIR(directory.lstat().st_mode), "symbolic or invalid archive directory")
    raw_manifest = read_regular(archive / "MANIFEST-v2.json")
    record = json.loads(raw_manifest, object_pairs_hook=unique_object, parse_constant=reject_constant)
    require(type(record) is dict, "manifest must be an object")
    require(record.get("schema") == "pid-rs-mgw-target-copy-negative-archive-v2", "unexpected schema")
    require(record.get("status") == "inert-retrospective-correction", "unexpected archive status")
    artifacts, routes = record.get("artifacts"), record.get("routes")
    require(type(artifacts) is list and len(artifacts) == 81, "expected 81 artifact entries")
    require(type(routes) is list and len(routes) == 6, "expected six route entries")
    by_id, by_path = {}, {}
    for item in artifacts:
        require(type(item) is dict, "artifact must be an object")
        require(set(item) == {"id", "path", "role", "raw_bytes", "raw_sha256",
                              "bytes", "sha256", "redactions", "mode"}, "artifact fields differ")
        identifier = item["id"]
        require(type(identifier) is str and identifier and identifier not in by_id,
                "duplicate or invalid artifact id")
        relative = payload_path(item["path"])
        require(relative not in by_path, "duplicate artifact path")
        for field in ("bytes", "raw_bytes"):
            require(type(item[field]) is int and 0 <= item[field] <= MAX_BYTES,
                    f"invalid integer {field}: {identifier}")
        for field in ("sha256", "raw_sha256"):
            require(type(item[field]) is str and HEX256.fullmatch(item[field]) is not None,
                    f"invalid digest {field}: {identifier}")
        require(item["mode"] == "0o644", "payload must have inert mode 0644")
        require(type(item["redactions"]) is dict, "redactions must be an object")
        if not item["redactions"]:
            require(item["bytes"] == item["raw_bytes"] and item["sha256"] == item["raw_sha256"],
                    "unredacted payload must equal raw commitment")
        by_id[identifier], by_path[relative] = item, item
    route_ids = set()
    for route in routes:
        require(type(route) is dict and type(route.get("id")) is str, "invalid route")
        require(route["id"] not in route_ids, "duplicate route id")
        route_ids.add(route["id"])
        require(type(route.get("accepted_target_proofs")) is int
                and route["accepted_target_proofs"] == 0, "archive cannot grant theorem credit")
        for field, digest_field in (("primary_source_artifact", "source_sha256"),
                                    ("diagnostic_artifact", "diagnostic_sha256")):
            require(route.get(field) in by_id, f"missing route artifact: {field}")
            require(route.get(digest_field) == by_id[route[field]]["raw_sha256"],
                    f"route/raw-artifact digest mismatch: {digest_field}")
        for artifact_id in route["run_records"].values():
            require(artifact_id in by_id, "missing run-record artifact")
        for command in route["commands"]:
            for artifact_id in command["records"].values():
                require(artifact_id in by_id, "missing command-record artifact")
        for binding in route["source_to_staged_custody"]:
            require(binding["source_artifact"] in by_id, "missing staged source artifact")
            source = by_id[binding["source_artifact"]]
            require(type(binding["raw_bytes"]) is int and binding["raw_bytes"] == source["raw_bytes"]
                    and binding["raw_sha256"] == source["raw_sha256"], "staged source binding differs")
    # This preserves all remaining fields, without authenticating observations.
    require(hashlib.sha256(raw_manifest).hexdigest() == EXPECTED_MANIFEST_SHA256,
            "frozen v2 manifest bytes differ")
    actual_paths = set()
    for directory, directories, files in os.walk(archive, followlinks=False):
        for name in directories:
            require(stat.S_ISDIR((Path(directory) / name).lstat().st_mode), "symbolic archive directory")
        for name in files:
            path = Path(directory) / name
            raw = read_regular(path)
            relative = path.relative_to(archive).as_posix()
            if path.relative_to(archive).parts[0] != "payloads":
                continue
            require(relative in by_path, f"unexpected payload: {relative}")
            actual_paths.add(relative)
            item = by_path[relative]
            require(len(raw) == item["bytes"] and hashlib.sha256(raw).hexdigest() == item["sha256"],
                    f"payload digest mismatch: {relative}")
    require(actual_paths == set(by_path), "missing payload file")
    return len(routes), len(actual_paths)


def main() -> int:
    try:
        require(len(sys.argv) == 1, "no alternate archive or manifest arguments are accepted")
        routes, payloads = check_archive(ROOT)
    except (ArchiveError, OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as error:
        print(f"MGW negative archive: {error}", file=sys.stderr)
        return 1
    print(f"OK: v2 inert MGW archive binds {routes} routes and {payloads} redacted payloads; "
          "private raw bytes and historical execution are outside this check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
