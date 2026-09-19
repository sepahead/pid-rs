#!/usr/bin/env python3
"""Match reviewed guide build diagnostics to their exact generated TeX.

This check permits only the recorded package diagnostics under a content and
visual review scope. It does not establish PDF/UA or assistive-reader conformance.
The caller must pin the manifest digest and keep inputs stable during execution.
Before/after reads are not an atomic snapshot. No manifest is generated during a build.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

INPUT_LIMIT = 8 * 1024 * 1024
DIAGNOSTIC = re.compile(
    r"LaTeX(?: Font)? Warning:|Package [^\s]+ Warning:|Class [^\s]+ Warning:"
    r"|Font Warning:|(?:pdfTeX|LuaTeX|LuaHBTeX) warning"
    r"|warning\s+\(pdf backend\):|xdvipdfmx:warning:"
    r"|Missing character:|(?:Overfull|Underfull) \\[hv]box"
    r"|undefined references|undefined citations|multiply defined"
    r"|Rerun to get (?:cross-references|outlines) right"
    r"|Fatal error|Emergency stop|TeX capacity exceeded|Runaway argument"
    r"|Undefined control sequence|^! |(?:LaTeX|Package [^\s]+) Error:"
)
REVIEWED_PACKAGE = re.compile(r"^Package (tagpdf|microtype|footnotehyper) Warning:")
SOURCE_LINE = re.compile(r"on (?:input )?line\s+(\d+)")
FOOTNOTE_COMMAND = re.compile(r"\\footnote(?:mark|text)?\b")
DIGEST = re.compile(r"[0-9a-f]{64}")
MANIFEST_KEYS = {
    "schema", "profile", "scope", "pdf_ua_claim", "tex_sha256", "diagnostics"
}


class DiagnosticError(ValueError):
    """A source, manifest, or diagnostic is outside the reviewed scope."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiagnosticError(message)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def strict_json(data: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def nonfinite(value: str) -> object:
        raise DiagnosticError(f"nonfinite JSON value: {value}")

    return json.loads(data, object_pairs_hook=pairs, parse_constant=nonfinite)


def read_regular(path: Path) -> bytes:
    require(path.is_absolute() and path.resolve(strict=True) == path,
            "input must have a canonical absolute path")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= INPUT_LIMIT,
            "input must be a bounded regular file")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        opened = os.fstat(fd)
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(INPUT_LIMIT + 1)
        closed = os.fstat(fd)
    finally:
        os.close(fd)
    after = path.lstat()

    def identity(value: os.stat_result) -> tuple[int, ...]:
        return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
                value.st_size, value.st_mtime_ns, value.st_ctime_ns)

    require(identity(before) == identity(opened) == identity(closed) == identity(after)
            and len(data) == before.st_size, "input changed during read")
    return data


def observe(log: str, tex: str) -> list[dict[str, object]]:
    """Retain each complete known-package warning and its source-line anchors."""
    lines = log.splitlines()
    source = tex.splitlines()
    result: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        if not DIAGNOSTIC.search(lines[index]):
            index += 1
            continue
        block = [lines[index]]
        index += 1
        if REVIEWED_PACKAGE.match(block[0]):
            while (index < len(lines) and lines[index].strip()
                   and not DIAGNOSTIC.search(lines[index])):
                block.append(lines[index])
                index += 1
        message = "\n".join(block)
        anchors = []
        for match in SOURCE_LINE.finditer(message):
            line = int(match.group(1))
            require(1 <= line <= len(source), "warning source line is outside TeX")
            anchors.append({"line": line, "text": source[line - 1]})
        result.append({"message": message, "anchors": anchors})
    return result


def validate_manifest(value: object, profile: str) -> dict[str, object]:
    require(type(value) is dict and set(value) == MANIFEST_KEYS,
            "unexpected diagnostic manifest fields")
    require(value["schema"] == "guide-scoped-diagnostics-v1"
            and type(value["profile"]) is str and value["profile"] == profile,
            "wrong diagnostic schema or profile")
    require(value["scope"] == "content-visual-structure-profile-only"
            and value["pdf_ua_claim"] is False, "wrong publication scope")
    require(type(value["tex_sha256"]) is str
            and DIGEST.fullmatch(value["tex_sha256"]) is not None,
            "invalid TeX digest")
    rows = value["diagnostics"]
    require(type(rows) is list and len(rows) <= 512, "invalid diagnostic roster")
    for row in rows:
        require(type(row) is dict and set(row) == {"message", "anchors"},
                "invalid diagnostic record")
        require(type(row["message"]) is str
                and REVIEWED_PACKAGE.match(row["message"]) is not None,
                "manifest permits an unreviewed diagnostic class")
        require(type(row["anchors"]) is list, "invalid source anchors")
        for anchor in row["anchors"]:
            require(type(anchor) is dict and set(anchor) == {"line", "text"}
                    and type(anchor["line"]) is int and anchor["line"] >= 1
                    and type(anchor["text"]) is str, "invalid source anchor")
    return value


def check(log: bytes, tex: bytes, manifest: bytes, expected_digest: str,
          profile: str) -> dict[str, object]:
    require(DIGEST.fullmatch(expected_digest) is not None
            and digest(manifest) == expected_digest, "unreviewed manifest bytes")
    expected = validate_manifest(strict_json(manifest), profile)
    require(expected["tex_sha256"] == digest(tex), "unreviewed generated TeX")
    text = tex.decode("utf-8")
    require(FOOTNOTE_COMMAND.search(text) is None,
            "footnote use requires a separately reviewed compatibility policy")
    rows = observe(log.decode("utf-8"), text)
    require(all(REVIEWED_PACKAGE.match(row["message"]) for row in rows),
            "layout, reference, glyph, or unreviewed warning/error diagnostic")
    require(rows == expected["diagnostics"], "diagnostic messages or source anchors changed")
    return {
        "schema": "guide-diagnostic-observation-v1",
        "profile": profile,
        "log_sha256": digest(log),
        "tex_sha256": digest(tex),
        "manifest_sha256": digest(manifest),
        "diagnostics": rows,
        "status": "matched-scoped-diagnostics",
        "pdf_ua_claim": False,
        "visual_acceptance": False,
        "warning_free": not rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("tex", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("expected_manifest_sha256")
    parser.add_argument("profile")
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    require(args.receipt.is_absolute()
            and args.receipt.parent.resolve(strict=True) == args.receipt.parent,
            "receipt must have a canonical absolute parent")
    require(not args.receipt.is_symlink(), "receipt must not be symbolic")
    paths = (args.log, args.tex, args.manifest)
    before = tuple(read_regular(path) for path in paths)
    result = check(*before, args.expected_manifest_sha256, args.profile)
    require(tuple(read_regular(path) for path in paths) == before,
            "inputs changed before receipt creation")
    with args.receipt.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, DiagnosticError, json.JSONDecodeError, UnicodeError, KeyError, TypeError) as error:
        print(f"guide diagnostic check: {error}", file=sys.stderr)
        raise SystemExit(1)
