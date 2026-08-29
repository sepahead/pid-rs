#!/usr/bin/env python3
"""Admit only a strict trailer-ID delta in a cross-toolchain guide comparison.

This checker is deliberately narrower than PDF equivalence.  It accepts two
different regular PDF files only when each file has one direct trailer ``/ID``
array, both entries in that array are the same 16-byte hex string, the typed
and raw representations agree, and every byte outside the four hex payload
spans is equal.  It never rewrites either input.

The ``--validate-inputs`` route checks only the shared file-custody preconditions
for a repeated-build pair.  It accepts exact byte equality and does not apply
the trailer-ID projection.

The result supports the declared cross-toolchain diagnostic only.  It is not
raw-byte reproducibility, document identity, authenticity, or a general PDF
normalization rule.  Canonical and same-toolchain exact checks must use raw
``cmp`` before this exceptional projection is considered.
"""

from __future__ import annotations

import hashlib
import io
import os
import pathlib
import re
import stat
import sys
from typing import NoReturn

from pypdf import PdfReader
from pypdf.generic import ArrayObject, ByteStringObject, TextStringObject


CHECK_NAME = "Mathematical results guide PDF trailer-ID variance check"
MAX_PDF_BYTES = 16 * 1024 * 1024
ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
ID_NAME_PATTERN = re.compile(rb"/ID(?=$|[\x00\t\n\f\r ()<>\[\]{}/%])")
FINAL_STARTXREF_PATTERN = re.compile(
    rb"startxref[ \t\r\n]+([0-9]+)[ \t\r\n]+%%EOF[ \t\r\n]*\Z"
)
STABLE_FIELDS = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"{CHECK_NAME} failed: {message}")


def open_exact_regular(raw: str, label: str) -> tuple[pathlib.Path, int, os.stat_result]:
    path = pathlib.Path(raw)
    try:
        path_before = path.lstat()
    except FileNotFoundError:
        fail(f"{label} input is absent, non-regular, or symbolic: {raw}")
    except OSError as error:
        fail(f"cannot inspect {label} input: {error}")
    if stat.S_ISLNK(path_before.st_mode) or not stat.S_ISREG(path_before.st_mode):
        fail(f"{label} input is absent, non-regular, or symbolic: {raw}")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        fail("this platform cannot open inputs without following symbolic links")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"cannot open {label} input without following symbolic links: {error}")
    try:
        opened = os.fstat(descriptor)
    except OSError as error:
        os.close(descriptor)
        fail(f"cannot inspect opened {label} input: {error}")
    if not stat.S_ISREG(opened.st_mode):
        os.close(descriptor)
        fail(f"{label} input changed to a non-regular file before opening")
    if (path_before.st_dev, path_before.st_ino) != (opened.st_dev, opened.st_ino):
        os.close(descriptor)
        fail(f"{label} input identity changed before opening")
    return path, descriptor, opened


def read_bounded(
    path: pathlib.Path, descriptor: int, before: os.stat_result, label: str
) -> bytes:
    if before.st_size == 0:
        fail(f"{label} input is empty")
    if before.st_size > MAX_PDF_BYTES:
        fail(f"{label} input exceeds the {MAX_PDF_BYTES}-byte bound")
    try:
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            stream.seek(0)
            data = stream.read(MAX_PDF_BYTES + 1)
        after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail(f"cannot read {label} input: {error}")
    if any(getattr(before, field) != getattr(after, field) for field in STABLE_FIELDS):
        fail(f"{label} input changed while it was read")
    if any(getattr(before, field) != getattr(path_after, field) for field in STABLE_FIELDS):
        fail(f"{label} input path changed while it was read")
    if len(data) != before.st_size:
        fail(f"{label} input length changed while it was read")
    return data


def require_still_opened(
    path: pathlib.Path, descriptor: int, before: os.stat_result, label: str
) -> None:
    try:
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail(f"cannot recheck {label} input after reading the pair: {error}")
    if any(
        getattr(before, field) != getattr(descriptor_after, field)
        for field in STABLE_FIELDS
    ):
        fail(f"{label} input changed before the pair read completed")
    if any(
        getattr(before, field) != getattr(path_after, field) for field in STABLE_FIELDS
    ):
        fail(f"{label} input path changed before the pair read completed")


def original_bytes(value: object, label: str) -> bytes:
    raw = getattr(value, "original_bytes", None)
    if not isinstance(raw, bytes):
        fail(f"{label} typed PDF string lacks original bytes")
    return raw


def require_final_trailer_owner(data: bytes, match: re.Match[bytes], label: str) -> None:
    final_startxref = FINAL_STARTXREF_PATTERN.search(data)
    if final_startxref is None:
        fail(f"{label} input lacks one final direct startxref/EOF boundary")
    xref_offset = int(final_startxref.group(1))
    if xref_offset < 0 or xref_offset >= final_startxref.start():
        fail(f"{label} startxref offset is outside the final file body")

    object_header = re.match(rb"[0-9]+[ \t]+[0-9]+[ \t\r\n]+obj\b", data[xref_offset:])
    if object_header is None:
        fail(f"{label} startxref does not select a direct xref-stream object")
    stream_start = data.find(b"stream", xref_offset, final_startxref.start())
    if stream_start < 0:
        fail(f"{label} xref-stream object lacks its stream boundary")
    owner = data[xref_offset:stream_start]
    owner_start = xref_offset
    if re.search(rb"/Type[ \t\r\n]+/XRef\b", owner) is None:
        fail(f"{label} startxref object is not a typed XRef stream")

    owner_names = list(ID_NAME_PATTERN.finditer(owner))
    if len(owner_names) != 1:
        fail(f"{label} final trailer does not contain exactly one /ID name")
    if match.start() != owner_start + owner_names[0].start():
        fail(f"{label} strict /ID is not owned by the final trailer")


def erase_strict_id(data: bytes, label: str) -> tuple[bytes, str, bytes]:
    matches = list(ID_PATTERN.finditer(data))
    if len(matches) != 1:
        fail(f"{label} raw file does not contain exactly one strict trailer /ID")
    match = matches[0]
    require_final_trailer_owner(data, match, label)
    if match.group(1).lower() != match.group(2).lower():
        fail(f"{label} trailer /ID pair is not duplicated")

    try:
        typed = PdfReader(io.BytesIO(data), strict=True).trailer.raw_get("/ID")
    except Exception as error:
        fail(f"{label} input is not a strict readable PDF: {error}")
    if not isinstance(typed, ArrayObject) or len(typed) != 2:
        fail(f"{label} typed trailer /ID is not a direct two-element array")
    if any(
        not isinstance(value, (TextStringObject, ByteStringObject)) for value in typed
    ):
        fail(f"{label} typed trailer /ID elements are not PDF strings")
    typed_bytes = [original_bytes(value, f"{label} trailer /ID") for value in typed]
    raw_id = bytes.fromhex(match.group(1).decode("ascii"))
    if (
        any(len(value) != 16 for value in typed_bytes)
        or typed_bytes[0] != typed_bytes[1]
        or typed_bytes != [raw_id, raw_id]
    ):
        fail(f"{label} typed trailer /ID does not match the raw token")

    normalized = bytearray(data)
    for group in (1, 2):
        start, end = match.span(group)
        normalized[start:end] = b"0" * (end - start)
    return bytes(normalized), match.group(1).decode("ascii"), raw_id


def read_input_pair(first_raw: str, second_raw: str) -> tuple[bytes, bytes]:
    first_path, first_descriptor, first_opened = open_exact_regular(first_raw, "first")
    try:
        second_path, second_descriptor, second_opened = open_exact_regular(
            second_raw, "second"
        )
    except BaseException:
        os.close(first_descriptor)
        raise
    try:
        if (first_opened.st_dev, first_opened.st_ino) == (
            second_opened.st_dev,
            second_opened.st_ino,
        ):
            fail("inputs alias the same file")
        if first_opened.st_nlink != 1:
            fail("first input is not singly linked")
        if second_opened.st_nlink != 1:
            fail("second input is not singly linked")
        first = read_bounded(first_path, first_descriptor, first_opened, "first")
        second = read_bounded(second_path, second_descriptor, second_opened, "second")
        require_still_opened(first_path, first_descriptor, first_opened, "first")
        require_still_opened(second_path, second_descriptor, second_opened, "second")
    finally:
        os.close(second_descriptor)
        os.close(first_descriptor)
    if len(first) != len(second):
        fail(f"input byte lengths differ: {len(first)} != {len(second)}")
    return first, second


def main(argv: list[str]) -> int:
    inputs_only = len(argv) == 4 and argv[1] == "--validate-inputs"
    projected = len(argv) == 3 and not argv[1].startswith("-")
    if not inputs_only and not projected:
        fail(
            "usage: check-mathematical-results-guide-pdf-id-variance.py "
            "[--validate-inputs] FIRST.pdf SECOND.pdf"
        )
    first_raw, second_raw = (argv[2], argv[3]) if inputs_only else (argv[1], argv[2])
    first, second = read_input_pair(first_raw, second_raw)
    if inputs_only:
        print(
            "OK: repeated-build PDF inputs are distinct, singly linked, bounded, "
            f"stable regular files (bytes={len(first)}; "
            f"first_sha256={hashlib.sha256(first).hexdigest()}; "
            f"second_sha256={hashlib.sha256(second).hexdigest()})"
        )
        return 0
    if first == second:
        fail("inputs are byte-identical; the raw equality route must handle them")

    first_normalized, first_id_text, first_id = erase_strict_id(first, "first")
    second_normalized, second_id_text, second_id = erase_strict_id(second, "second")
    if first_id == second_id:
        fail("decoded trailer /ID values are equal; no ID variance was established")
    if first_normalized != second_normalized:
        fail("inputs differ outside the exact duplicated trailer /ID payloads")

    first_sha = hashlib.sha256(first).hexdigest()
    second_sha = hashlib.sha256(second).hexdigest()
    print(
        "OK: input PDFs are byte-equal outside their strict duplicated "
        f"trailer /ID payloads (bytes={len(first)}; first_sha256={first_sha}; "
        f"second_sha256={second_sha}; first_id={first_id_text}; "
        f"second_id={second_id_text})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
