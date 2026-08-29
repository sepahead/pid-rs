#!/usr/bin/env python3
"""Validate and normalize the final mathematical-results-guide font roster.

The input is the plain-text report emitted by Poppler's ``pdffonts``.  This
gate is deliberately specific to the guide: its body must use Latin Modern,
and its three canonical figures must contribute the declared Source Sans Pro
and Latin Modern Sans faces.  A generic "all fonts are embedded" check cannot
detect a stale figure PDF that still carries a platform fallback font.
"""

from __future__ import annotations

import pathlib
import re
import stat
import sys
from typing import NoReturn


MAX_REPORT_BYTES = 1_000_000
HEADER = "name type encoding emb sub uni object ID"
ROW = re.compile(
    r"^(?P<name>\S+)\s+"
    r"(?P<kind>.+?)\s+"
    r"(?P<encoding>\S+)\s+"
    r"(?P<embedded>yes|no)\s+"
    r"(?P<subset>yes|no)\s+"
    r"(?P<unicode>yes|no)\s+"
    r"(?P<object>\d+)\s+(?P<generation>\d+)\s*$"
)
SUBSET_NAME = re.compile(r"^[A-Z]{6}\+(?P<base>.+)$")
ALLOWED_NAMES = (
    re.compile(r"^LMRoman\d+-(?:Regular|Bold|Italic|BoldItalic)$"),
    re.compile(r"^LMMonoLt10-Regular$"),
    re.compile(r"^LatinModernMath-Regular$"),
    re.compile(r"^SourceSansPro-(?:Regular|Semibold|Bold)$"),
    re.compile(r"^LMSans10-(?:Regular|Bold)$"),
)
ALLOWED_KIND_ENCODINGS = {
    ("Type 1C", "WinAnsi"),
    ("CID Type 0C", "Identity-H"),
}
REQUIRED_FACES = {
    "SourceSansPro-Regular",
    "SourceSansPro-Semibold",
    "SourceSansPro-Bold",
    "LMSans10-Regular",
    "LMSans10-Bold",
}


class RosterError(ValueError):
    """The report does not satisfy the guide-specific font contract."""


def fail(message: str) -> NoReturn:
    raise RosterError(message)


def read_regular_file(path: pathlib.Path) -> str:
    try:
        metadata = path.lstat()
    except OSError as error:
        fail(f"cannot stat report: {error}")
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        fail("report must be a non-symbolic regular file")
    if metadata.st_size <= 0 or metadata.st_size > MAX_REPORT_BYTES:
        fail(f"report size must be in 1..{MAX_REPORT_BYTES} bytes")
    try:
        payload = path.read_bytes()
    except OSError as error:
        fail(f"cannot read report: {error}")
    if len(payload) != metadata.st_size:
        fail("report size changed while it was read")
    if b"\x00" in payload:
        fail("report contains a NUL byte")
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"report is not UTF-8: {error}")


def normalize_report(text: str) -> tuple[str, ...]:
    lines = text.splitlines()
    if len(lines) < 2 or " ".join(lines[0].split()) != HEADER:
        fail("report header is absent or malformed")
    if not re.fullmatch(r"[- ]+", lines[1]) or "-" not in lines[1]:
        fail("report separator is absent or malformed")

    roster: set[tuple[str, str, str]] = set()
    observed_faces: set[str] = set()
    rows = 0
    for number, line in enumerate(lines[2:], start=3):
        if not line.strip():
            continue
        match = ROW.fullmatch(line)
        if match is None:
            fail(f"malformed font row at line {number}")
        rows += 1
        raw_name = match.group("name")
        subset_match = SUBSET_NAME.fullmatch(raw_name)
        if subset_match is None:
            fail(f"font row {number} lacks a canonical six-letter subset prefix")
        name = subset_match.group("base")
        if not any(pattern.fullmatch(name) for pattern in ALLOWED_NAMES):
            fail(f"font row {number} uses a non-contract face: {name}")
        kind = " ".join(match.group("kind").split())
        encoding = match.group("encoding")
        if (kind, encoding) not in ALLOWED_KIND_ENCODINGS:
            fail(
                f"font row {number} uses a non-contract kind/encoding pair: "
                f"{kind} + {encoding}"
            )
        for field, description in (
            ("embedded", "embedded"),
            ("subset", "subset"),
            ("unicode", "Unicode-mapped"),
        ):
            if match.group(field) != "yes":
                fail(f"font row {number} is not {description}")
        observed_faces.add(name)
        roster.add((name, kind, encoding))

    if rows == 0:
        fail("report contains no font rows")
    missing = sorted(REQUIRED_FACES - observed_faces)
    if missing:
        fail("required canonical-figure faces are absent: " + ", ".join(missing))
    return tuple("\t".join(item) for item in sorted(roster))


def main(argv: list[str]) -> int:
    if len(argv) != 2 or argv[1].startswith("-"):
        print(f"usage: {pathlib.Path(argv[0]).name} PDF_FONTS_REPORT", file=sys.stderr)
        return 2
    try:
        roster = normalize_report(read_regular_file(pathlib.Path(argv[1])))
    except RosterError as error:
        print(f"Mathematical results guide font-roster check failed: {error}", file=sys.stderr)
        return 1
    for record in roster:
        print(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
