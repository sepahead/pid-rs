#!/usr/bin/env python3
"""Check full-SHA action refs and the reviewed upload-artifact source pin."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Final


if not (
    sys.version_info >= (3, 11)
    and sys.flags.isolated == 1
    and sys.flags.safe_path
    and sys.flags.no_site == 1
    and sys.flags.ignore_environment == 1
    and sys.dont_write_bytecode
):
    print(
        "ERROR: check-github-action-pins.py requires Python 3.11+ -I -S -B",
        file=sys.stderr,
    )
    raise SystemExit(2)


SCRIPT = Path(os.path.abspath(os.fspath(Path(__file__))))
ROOT = SCRIPT.parent.parent
WORKFLOWS = ROOT / ".github/workflows"
MAX_WORKFLOW_BYTES: Final = 2 * 1024 * 1024
SHA40 = re.compile(r"[0-9a-f]{40}")
USES_LINE = re.compile(
    r"^ *(?:- +)?uses:[ \t]+"
    r"(?:(?P<double>\"[^\"\r\n]+\")|(?P<single>'[^'\r\n]+')|(?P<bare>[^ \t\r\n]+))"
    r"(?:[ \t]+#.*|[ \t]*)$"
)
USES_PREFIX = re.compile(r"^ *(?:- +)?uses:")
USES_KEY_CANDIDATE = re.compile(r"(?<![A-Za-z0-9_.-])uses[ \t]*:", re.IGNORECASE)
BLOCK_SCALAR = re.compile(r"^ *(?:- +)?[^#\r\n]+:[ \t]*[>|][-+0-9]*(?:[ \t]+#.*|[ \t]*)$")
QUOTED_KEY_PREFIX = re.compile(r"^ *(?:- +)?[\"']")
QUOTED_MAPPING_KEY = re.compile(r"[\"'][^\"'\r\n]+[\"'][ \t]*:")
FLOW_MAPPING_PREFIX = re.compile(r"^ *- *\{")
EXPLICIT_KEY_PREFIX = re.compile(r"^ *[?:](?:[ \t]|$)")
ANCHOR_OR_ALIAS = re.compile(
    r"(?:^|[ \t\[\]{},:])(?P<token>[&*][A-Za-z0-9_-]+)(?:[ \t\[\]{},#]|$)"
)
EXTERNAL_ACTION = re.compile(
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
    r"(?:/(?P<subpath>[^@\s]+))?@(?P<ref>[^@\s]+)"
)
RAW_EXTERNAL_ACTION = re.compile(
    rb"(?<![A-Za-z0-9_./-])"
    rb"(?P<route>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*)@"
    rb"(?P<ref>[^\s\"',}\]]+)"
)

# The v7.0.1 release tag and major tag were both observed at this exact object
# through the public actions/upload-artifact Git repository on 2026-08-19.
# This binds the selected source identity; it is not an authenticity or
# reproducible-build claim.
REVIEWED_EXACT_ACTION_PINS: Final = {
    "actions/upload-artifact": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
}
UPLOAD_ROUTE = b"actions/upload-artifact@"


class PinError(RuntimeError):
    """A workflow path, syntax, action route, or revision violated the policy."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PinError(message)


def read_regular(path: Path) -> bytes:
    before = path.lstat()
    require(
        stat.S_ISREG(before.st_mode)
        and not path.is_symlink()
        and before.st_nlink == 1
        and stat.S_IMODE(before.st_mode) == 0o644
        and 0 < before.st_size <= MAX_WORKFLOW_BYTES,
        f"workflow has unsupported metadata: {path.relative_to(ROOT)}",
    )
    descriptor = os.open(path, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        require(
            (opened.st_dev, opened.st_ino, opened.st_mode, opened.st_nlink, opened.st_size)
            == (before.st_dev, before.st_ino, before.st_mode, before.st_nlink, before.st_size),
            f"workflow identity changed while opening: {path.relative_to(ROOT)}",
        )
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 1024 * 1024))
            require(chunk != b"", f"short workflow read: {path.relative_to(ROOT)}")
            chunks.append(chunk)
            remaining -= len(chunk)
        require(os.read(descriptor, 1) == b"", f"workflow grew while read: {path.relative_to(ROOT)}")
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after = path.lstat()
    require(
        all(
            getattr(before, field)
            == getattr(opened, field)
            == getattr(after_fd, field)
            == getattr(after, field)
            for field in (
                "st_dev",
                "st_ino",
                "st_mode",
                "st_nlink",
                "st_size",
                "st_mtime_ns",
                "st_ctime_ns",
            )
        ),
        f"workflow changed while read: {path.relative_to(ROOT)}",
    )
    return b"".join(chunks)


def parse_uses_value(line: str, location: str) -> str:
    match = USES_LINE.fullmatch(line)
    require(match is not None, f"malformed uses declaration at {location}")
    value = next(item for item in match.group("double", "single", "bare") if item is not None)
    if value[:1] in {'"', "'"}:
        require(value[-1:] == value[:1] and len(value) >= 3, f"malformed quoted uses value at {location}")
        value = value[1:-1]
    require(value != "", f"empty uses value at {location}")
    return value


def validate_uses_value(value: str, location: str) -> tuple[str, str] | None:
    if value.startswith("./"):
        require("@" not in value and "${{" not in value, f"dynamic local-action route at {location}")
        return None
    require(not value.startswith("docker://"), f"unsupported Docker action route at {location}")
    match = EXTERNAL_ACTION.fullmatch(value)
    require(match is not None, f"unsupported or dynamic external action route at {location}: {value}")
    revision = match.group("ref")
    require(
        SHA40.fullmatch(revision) is not None,
        f"external action is not pinned to an exact lowercase 40-hex commit at {location}: {value}",
    )
    route = f"{match.group('owner')}/{match.group('repo')}"
    reviewed_routes = {
        canonical.casefold(): (canonical, pin)
        for canonical, pin in REVIEWED_EXACT_ACTION_PINS.items()
    }
    reviewed_entry = reviewed_routes.get(route.casefold())
    if reviewed_entry is not None:
        canonical_route, reviewed = reviewed_entry
        require(route == canonical_route, f"reviewed action route case changed at {location}: {value}")
    else:
        reviewed = None
    if reviewed is not None:
        require(revision == reviewed, f"reviewed action source pin changed at {location}: {value}")
    return route, revision


def validate_raw_upload_occurrences(raw: bytes, relative: str) -> int:
    folded = raw.lower()
    expected = REVIEWED_EXACT_ACTION_PINS["actions/upload-artifact"].encode("ascii")
    offsets: list[int] = []
    cursor = 0
    while (offset := folded.find(UPLOAD_ROUTE, cursor)) >= 0:
        offsets.append(offset)
        start = offset + len(UPLOAD_ROUTE)
        observed = raw[start : start + len(expected)]
        require(
            observed == expected,
            f"raw upload-artifact occurrence is not the reviewed exact pin at {relative}:{offset}",
        )
        following = raw[start + len(expected) : start + len(expected) + 1]
        require(
            following == b"" or following in b" \t\r\n\"',}]",
            f"raw upload-artifact occurrence has a non-delimited pin at {relative}:{offset}",
        )
        cursor = start + len(expected)
    return len(offsets)


def validate_raw_external_occurrences(raw: bytes, relative: str) -> int:
    matches = list(RAW_EXTERNAL_ACTION.finditer(raw))
    for match in matches:
        revision = match.group("ref")
        require(
            re.fullmatch(rb"[0-9a-f]{40}", revision) is not None,
            f"raw external-action token is not an exact lowercase 40-hex ref at {relative}:{match.start()}",
        )
    return len(matches)


def validate_workflow_bytes(raw: bytes, relative: str) -> list[tuple[int, str, str]]:
    require(b"\r" not in raw and raw.endswith(b"\n"), f"workflow line endings changed: {relative}")
    raw_upload_count = validate_raw_upload_occurrences(raw, relative)
    raw_external_count = validate_raw_external_occurrences(raw, relative)
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise PinError(f"workflow is not UTF-8: {relative}: {error}") from None
    observations: list[tuple[int, str, str]] = []
    block_scalar_indent: int | None = None
    for number, line in enumerate(text.splitlines(), 1):
        leading = line[: len(line) - len(line.lstrip(" \t"))]
        require(
            "\t" not in leading,
            f"tab indentation is unsupported at {relative}:{number}",
        )
        indent = len(leading)
        if block_scalar_indent is not None:
            if line.strip() == "" or indent > block_scalar_indent:
                continue
            block_scalar_indent = None
        candidates = list(USES_KEY_CANDIDATE.finditer(line))
        if BLOCK_SCALAR.fullmatch(line) is not None:
            require(
                not candidates,
                f"block-scalar uses declaration is unsupported at {relative}:{number}",
            )
            block_scalar_indent = indent
            continue
        require(
            QUOTED_KEY_PREFIX.match(line) is None,
            f"quoted YAML mapping keys are unsupported at {relative}:{number}",
        )
        require(
            QUOTED_MAPPING_KEY.search(line) is None,
            f"quoted YAML mapping keys are unsupported at {relative}:{number}",
        )
        require(
            FLOW_MAPPING_PREFIX.match(line) is None,
            f"flow-mapping workflow syntax is unsupported at {relative}:{number}",
        )
        require(
            EXPLICIT_KEY_PREFIX.match(line) is None,
            f"explicit-key workflow syntax is unsupported at {relative}:{number}",
        )
        require(
            ANCHOR_OR_ALIAS.search(line) is None,
            f"YAML anchors and aliases are unsupported at {relative}:{number}",
        )
        if not candidates:
            continue
        require(
            len(candidates) == 1 and USES_PREFIX.match(line) is not None,
            f"non-canonical or embedded uses declaration at {relative}:{number}",
        )
        value = parse_uses_value(line, f"{relative}:{number}")
        validated = validate_uses_value(value, f"{relative}:{number}")
        if validated is not None:
            observations.append((number, *validated))
    parsed_upload_count = sum(
        route.casefold() == "actions/upload-artifact" for _line, route, _revision in observations
    )
    require(
        raw_upload_count == parsed_upload_count,
        f"raw versus canonical upload-artifact occurrence count changed: {relative}",
    )
    require(
        raw_external_count == len(observations),
        f"raw versus canonical external-action occurrence count changed: {relative}",
    )
    return observations


def workflow_paths() -> list[Path]:
    require(WORKFLOWS.is_dir() and not WORKFLOWS.is_symlink(), "workflow directory identity changed")
    paths = sorted((*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")))
    require(paths != [] and len(paths) == len(set(paths)), "workflow inventory is empty or duplicated")
    entries = sorted(item.name for item in WORKFLOWS.iterdir())
    require(
        entries == sorted(path.name for path in paths),
        "workflow directory contains a non-YAML or nested entry",
    )
    return paths


def validate_repository() -> dict[str, object]:
    workflows: list[dict[str, object]] = []
    action_count = 0
    for path in workflow_paths():
        relative = path.relative_to(ROOT).as_posix()
        raw = read_regular(path)
        actions = validate_workflow_bytes(raw, relative)
        action_count += len(actions)
        workflows.append(
            {
                "external_action_references": len(actions),
                "path": relative,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "size_bytes": len(raw),
            }
        )
    require(action_count > 0, "workflow inventory contains no external actions")
    return {
        "external_action_references": action_count,
        "result": "pass",
        "reviewed_exact_action_pins": REVIEWED_EXACT_ACTION_PINS,
        "schema": "pid-rs/github-action-pin-validation/v1",
        "workflows": workflows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        result = validate_repository()
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    except (OSError, PinError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
