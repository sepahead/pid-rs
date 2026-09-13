#!/usr/bin/env python3
"""Prepare and replay the exact private Markdown parser used by the workflow PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any


SCHEMA = "pid-rs/workflow-markdown-parser-profiles-v1"
RECEIPT_SCHEMA = "pid-rs/workflow-markdown-parser-transform-v1"
MAX_PROFILE_BYTES = 64 * 1024
MAX_MODULE_BYTES = 1024 * 1024
OUTPUT_NAME = "pid-rs-markdown-gc.lua"
RECEIPT_NAME = "pid-rs-markdown-gc-receipt.tsv"
CALLBACK = b"    self.parser_functions[name] = function(str)\n"
NEXT_STATEMENT = b"      if toplevel and options.stripIndent then\n"
INSERTION = b'      if not toplevel then collectgarbage("collect") end\n'
ANCHOR = CALLBACK + NEXT_STATEMENT
REPLACEMENT = CALLBACK + INSERTION + NEXT_STATEMENT
CREATE_PARSER = b"  self.create_parser = function(name, grammar, toplevel)\n"
MATCH = b"      local res = lpeg.match(grammar(), str)\n"
PROFILE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,79}\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"[0-9A-Za-z][0-9A-Za-z.+_-]{0,79}\Z")


class Failure(RuntimeError):
    pass


def fail(detail: str) -> None:
    raise Failure(detail)


def fingerprint(value: os.stat_result) -> tuple[int, ...]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_mode,
        value.st_nlink,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def read_regular(path: Path, maximum: int, label: str) -> tuple[bytes, os.stat_result]:
    if not path.is_absolute():
        fail(f"{label} path is not absolute")
    try:
        named = path.lstat()
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as error:
        fail(f"cannot open {label}: {error}")
    try:
        opened = os.fstat(descriptor)
        if (named.st_dev, named.st_ino) != (opened.st_dev, opened.st_ino):
            fail(f"{label} identity changed during open")
        if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
            fail(f"{label} is not a single-link regular file")
        if not 1 <= opened.st_size <= maximum:
            fail(f"{label} size is outside 1..{maximum} bytes")
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            block = os.read(descriptor, min(remaining, 1024 * 1024))
            if not block:
                fail(f"{label} truncated during capture")
            chunks.append(block)
            remaining -= len(block)
        if os.read(descriptor, 1):
            fail(f"{label} grew during capture")
        after = os.fstat(descriptor)
        final = path.lstat()
        if fingerprint(opened) != fingerprint(after) or fingerprint(opened) != fingerprint(final):
            fail(f"{label} identity or metadata changed during capture")
        return b"".join(chunks), opened
    finally:
        os.close(descriptor)


def strict_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        fail(f"{label} keys differ")
    return value


def load_profiles(profile_path: Path) -> list[dict[str, Any]]:
    raw, _ = read_regular(profile_path, MAX_PROFILE_BYTES, "profile manifest")
    try:
        document = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"profile manifest is not canonical JSON: {error}")
    canonical = (json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode(
        "ascii"
    )
    if raw != canonical:
        fail("profile manifest bytes are not canonical JSON")
    root = strict_object(document, {"schema", "profiles"}, "profile manifest")
    if root["schema"] != SCHEMA or not isinstance(root["profiles"], list):
        fail("profile manifest schema or profile array differs")
    if not 1 <= len(root["profiles"]) <= 8:
        fail("profile count is outside 1..8")
    profiles: list[dict[str, Any]] = []
    for index, raw_profile in enumerate(root["profiles"]):
        profile = strict_object(
            raw_profile,
            {
                "id",
                "metadata_version",
                "preimage_bytes",
                "preimage_sha256",
                "postimage_bytes",
                "postimage_sha256",
                "source",
            },
            f"profile {index}",
        )
        identifier = profile["id"]
        version = profile["metadata_version"]
        source = profile["source"]
        if not isinstance(identifier, str) or PROFILE_ID.fullmatch(identifier) is None:
            fail(f"profile {index} ID differs")
        if not isinstance(version, str) or VERSION.fullmatch(version) is None:
            fail(f"profile {index} metadata version differs")
        if not isinstance(source, str) or not 1 <= len(source) <= 512 or "\n" in source:
            fail(f"profile {index} source description differs")
        for prefix in ("preimage", "postimage"):
            byte_count = profile[f"{prefix}_bytes"]
            digest = profile[f"{prefix}_sha256"]
            if (
                type(byte_count) is not int
                or not 1 <= byte_count <= MAX_MODULE_BYTES
                or not isinstance(digest, str)
                or SHA256.fullmatch(digest) is None
            ):
                fail(f"profile {index} {prefix} identity differs")
        if profile["postimage_bytes"] != profile["preimage_bytes"] + len(INSERTION):
            fail(f"profile {index} postimage length does not encode the exact insertion")
        profiles.append(profile)
    identifiers = [profile["id"] for profile in profiles]
    preimages = [
        (profile["preimage_bytes"], profile["preimage_sha256"])
        for profile in profiles
    ]
    postimages = [
        (profile["postimage_bytes"], profile["postimage_sha256"])
        for profile in profiles
    ]
    if identifiers != sorted(identifiers) or len(identifiers) != len(set(identifiers)):
        fail("profile IDs are not unique and sorted")
    if len(preimages) != len(set(preimages)) or len(postimages) != len(set(postimages)):
        fail("profile source or candidate identities are not unique")
    return profiles


def select_profile(
    profiles: list[dict[str, Any]], data: bytes, requested: str | None, kind: str
) -> dict[str, Any]:
    identity = (len(data), hashlib.sha256(data).hexdigest())
    matches = [
        profile
        for profile in profiles
        if identity == (profile[f"{kind}_bytes"], profile[f"{kind}_sha256"])
    ]
    if len(matches) != 1:
        fail(f"{kind} module identity matches {len(matches)} admitted profiles")
    profile = matches[0]
    if requested is not None and profile["id"] != requested:
        fail(f"{kind} module does not match requested profile")
    return profile


def verify_preimage(data: bytes, profile: dict[str, Any]) -> None:
    version_literal = f'    version   = "{profile["metadata_version"]}",\n'.encode("ascii")
    for label, literal in (
        ("metadata version", version_literal),
        ("create_parser declaration", CREATE_PARSER),
        ("parser callback", CALLBACK),
        ("callback anchor", ANCHOR),
        ("match expression", MATCH),
    ):
        if data.count(literal) != 1:
            fail(f"preimage {label} occurrence count differs from one")
    if data.count(INSERTION) != 0:
        fail("preimage already contains the collection intervention")


def candidate_bytes(preimage: bytes, profile: dict[str, Any]) -> bytes:
    verify_preimage(preimage, profile)
    candidate = preimage.replace(ANCHOR, REPLACEMENT, 1)
    if candidate.count(INSERTION) != 1 or candidate.replace(INSERTION, b"", 1) != preimage:
        fail("candidate differs by more than the exact insertion")
    identity = (len(candidate), hashlib.sha256(candidate).hexdigest())
    expected = (profile["postimage_bytes"], profile["postimage_sha256"])
    if identity != expected:
        fail("candidate identity differs from the admitted profile")
    return candidate


def require_safe_destination(path: Path, expected_name: str, label: str) -> None:
    if not path.is_absolute() or path.name != expected_name:
        fail(f"{label} path or leaf differs")
    if any(character in os.fspath(path) for character in "\x00\r\n\t"):
        fail(f"{label} path contains an unsafe character")
    try:
        parent_named = path.parent.lstat()
        parent_resolved = path.parent.resolve(strict=True)
    except OSError as error:
        fail(f"cannot resolve {label} parent: {error}")
    if not stat.S_ISDIR(parent_named.st_mode) or parent_resolved != path.parent:
        fail(f"{label} parent is not a direct canonical directory")


def write_read_only(path: Path, data: bytes, label: str) -> None:
    require_safe_destination(path, path.name, label)
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as error:
        fail(f"cannot create {label}: {error}")
    try:
        view = memoryview(data)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                fail(f"{label} write made no progress")
            view = view[written:]
        os.fsync(descriptor)
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != len(data):
            fail(f"{label} destination custody differs")
        os.fchmod(descriptor, 0o444)
        after = os.fstat(descriptor)
        if (
            (before.st_dev, before.st_ino, before.st_nlink, before.st_size)
            != (after.st_dev, after.st_ino, 1, len(data))
            or stat.S_IMODE(after.st_mode) != 0o444
        ):
            fail(f"{label} read-only transition differs")
    finally:
        os.close(descriptor)
    leaf = path.lstat()
    if (
        (leaf.st_dev, leaf.st_ino, leaf.st_nlink, leaf.st_size)
        != (after.st_dev, after.st_ino, 1, len(data))
        or stat.S_IMODE(leaf.st_mode) != 0o444
    ):
        fail(f"{label} final path custody differs")


def identity_line(profile: dict[str, Any]) -> str:
    return "\t".join(
        str(value)
        for value in (
            profile["id"],
            profile["metadata_version"],
            profile["preimage_bytes"],
            profile["preimage_sha256"],
            profile["postimage_bytes"],
            profile["postimage_sha256"],
        )
    )


def identify(profile_path: Path, source_path: Path, requested: str | None) -> dict[str, Any]:
    profiles = load_profiles(profile_path)
    source, _ = read_regular(source_path, MAX_MODULE_BYTES, "Markdown module preimage")
    profile = select_profile(profiles, source, requested, "preimage")
    candidate_bytes(source, profile)
    return profile


def transform(
    profile_path: Path,
    source_path: Path,
    output_path: Path,
    receipt_path: Path,
    requested: str,
) -> dict[str, Any]:
    require_safe_destination(output_path, OUTPUT_NAME, "candidate module")
    require_safe_destination(receipt_path, RECEIPT_NAME, "transform receipt")
    if output_path.parent != receipt_path.parent:
        fail("candidate module and receipt do not share one private parent")
    profiles = load_profiles(profile_path)
    source, _ = read_regular(source_path, MAX_MODULE_BYTES, "Markdown module preimage")
    profile = select_profile(profiles, source, requested, "preimage")
    candidate = candidate_bytes(source, profile)
    receipt = expected_receipt(profile, source_path, output_path)
    write_read_only(output_path, candidate, "candidate module")
    write_read_only(receipt_path, receipt, "transform receipt")
    return profile


def expected_receipt(
    profile: dict[str, Any], source_path: Path, output_path: Path
) -> bytes:
    return (
        f"schema\t{RECEIPT_SCHEMA}\n"
        f"profile_id\t{profile['id']}\n"
        f"metadata_version\t{profile['metadata_version']}\n"
        f"preimage_path\t{source_path}\n"
        f"preimage_bytes\t{profile['preimage_bytes']}\n"
        f"preimage_sha256\t{profile['preimage_sha256']}\n"
        f"candidate_path\t{output_path}\n"
        f"candidate_bytes\t{profile['postimage_bytes']}\n"
        f"candidate_sha256\t{profile['postimage_sha256']}\n"
        f"inserted_bytes\t{len(INSERTION)}\n"
    ).encode("utf-8")


def verify_output(profile_path: Path, output_path: Path, requested: str) -> dict[str, Any]:
    profiles = load_profiles(profile_path)
    candidate, status = read_regular(output_path, MAX_MODULE_BYTES, "candidate module")
    if stat.S_IMODE(status.st_mode) != 0o444:
        fail("candidate module mode differs from 0444")
    profile = select_profile(profiles, candidate, requested, "postimage")
    if candidate.count(INSERTION) != 1:
        fail("candidate collection-line occurrence count differs from one")
    preimage = candidate.replace(INSERTION, b"", 1)
    selected = select_profile(profiles, preimage, requested, "preimage")
    if selected["id"] != profile["id"]:
        fail("candidate reverse projection changes profile")
    verify_preimage(preimage, profile)
    return profile


def verify_transform(
    profile_path: Path,
    source_path: Path,
    output_path: Path,
    receipt_path: Path,
    requested: str,
) -> dict[str, Any]:
    require_safe_destination(output_path, OUTPUT_NAME, "candidate module")
    require_safe_destination(receipt_path, RECEIPT_NAME, "transform receipt")
    if output_path.parent != receipt_path.parent:
        fail("candidate module and receipt do not share one private parent")
    profile = identify(profile_path, source_path, requested)
    verified = verify_output(profile_path, output_path, requested)
    if verified["id"] != profile["id"]:
        fail("source and candidate profiles differ")
    receipt, status = read_regular(receipt_path, MAX_PROFILE_BYTES, "transform receipt")
    if stat.S_IMODE(status.st_mode) != 0o444:
        fail("transform receipt mode differs from 0444")
    if receipt != expected_receipt(profile, source_path, output_path):
        fail("transform receipt differs from exact source/candidate binding")
    return profile


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    subcommands = result.add_subparsers(dest="command", required=True)
    for name in ("identify", "verify-source"):
        command = subcommands.add_parser(name)
        command.add_argument("--profiles", type=Path, required=True)
        command.add_argument("--source", type=Path, required=True)
        command.add_argument("--profile-id")
    command = subcommands.add_parser("transform")
    command.add_argument("--profiles", type=Path, required=True)
    command.add_argument("--source", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--receipt", type=Path, required=True)
    command.add_argument("--profile-id", required=True)
    command = subcommands.add_parser("verify-output")
    command.add_argument("--profiles", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--profile-id", required=True)
    command = subcommands.add_parser("verify-transform")
    command.add_argument("--profiles", type=Path, required=True)
    command.add_argument("--source", type=Path, required=True)
    command.add_argument("--output", type=Path, required=True)
    command.add_argument("--receipt", type=Path, required=True)
    command.add_argument("--profile-id", required=True)
    return result


def main() -> int:
    arguments = parser().parse_args()
    if arguments.command in {"identify", "verify-source"}:
        profile = identify(arguments.profiles, arguments.source, arguments.profile_id)
    elif arguments.command == "transform":
        profile = transform(
            arguments.profiles,
            arguments.source,
            arguments.output,
            arguments.receipt,
            arguments.profile_id,
        )
    elif arguments.command == "verify-output":
        profile = verify_output(arguments.profiles, arguments.output, arguments.profile_id)
    else:
        profile = verify_transform(
            arguments.profiles,
            arguments.source,
            arguments.output,
            arguments.receipt,
            arguments.profile_id,
        )
    print(identity_line(profile))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Failure as error:
        print(f"workflow Markdown parser preparation: {error}", file=sys.stderr)
        raise SystemExit(1)
