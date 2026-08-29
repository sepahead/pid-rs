#!/usr/bin/env python3
"""Validate the finite diagnostic-wrapper trailer-ID observation receipt.

Without PDF arguments, this checker validates the closed receipt schema and
all arithmetic that can be checked from the receipt alone.  With FIRST.pdf and
SECOND.pdf, it additionally remeasures the retained byte sequences.  The
projection is comparison-only: this checker never rewrites or publishes a PDF.

The receipt is measurement identity for one observed pair, not a genuine
Pandoc render, an end-to-end old-toolchain build, or proof of PDF equivalence,
reproducibility, provenance, authenticity, or the cause of the ID variance.
It receives zero portability and execution credit.  Exact-mode PDF checks
remain raw-byte comparisons.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import stat
import sys
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
DEFAULT_RECEIPT = (
    ROOT / "audit/evidence/"
    "mathematical-results-guide-old-toolchain-trailer-id-observation-v1.json"
)
CHECK_NAME = "Mathematical results guide trailer-ID observation receipt check"
SCHEMA = "pid-rs.mathematical-results-guide.trailer-id-observation.v1"
MAX_RECEIPT_BYTES = 1024 * 1024
MAX_PDF_BYTES = 16 * 1024 * 1024
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}\Z")
ID_HEX_PATTERN = re.compile(r"[0-9A-F]{32}\Z")
RAW_ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
ID_NAME_PATTERN = re.compile(rb"/ID(?=$|[\x00\t\n\f\r ()<>\[\]{}/%])")
FINAL_STARTXREF_PATTERN = re.compile(
    rb"startxref[ \t\r\n]+([0-9]+)[ \t\r\n]+%%EOF[ \t\r\n]*\Z"
)
EMBEDDED_PRODUCER = "luahbtex-1.17.0"
EMBEDDED_FULL_BANNER = "This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)"
EMBEDDED_PRODUCER_TOKEN = f"/Producer ({EMBEDDED_PRODUCER})".encode("ascii")
EMBEDDED_FULL_BANNER_TOKEN = f"/PTEX.FullBanner ({EMBEDDED_FULL_BANNER})".encode(
    "ascii"
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
LIMITATIONS = [
    "The two raw PDFs are intentionally not tracked in the repository.",
    "This receipt identifies a finite byte-level measurement; it is not a proof or theorem.",
    "The retained pair was rendered after /usr/local/bin/pandoc resolved to a 319-byte diagnostic wrapper that copied a pre-existing /tmp/pid-rs-pdf-annotation-portability/raw.tex file.",
    "Pandoc 3.1.3 at /usr/bin/pandoc was installed only after this capture and was not used to produce the retained pair.",
    "The raw-TeX origin, source revision, exact capture provenance and command, container image digest, and build chronology are unknown or unauthenticated.",
    "The embedded LuaHBTeX producer and banner identify the final PDF engine only; they do not establish a genuine Pandoc render or an end-to-end old-toolchain build.",
    "The pair receives zero portability and execution credit; it is retained only as a finite byte observation.",
    "Equality after the declared projection does not establish raw-byte reproducibility, semantic equivalence, authenticity, or general PDF normalization.",
    "The observation does not establish the cause of the trailer-ID variance and must not weaken exact-mode comparisons.",
]


def fail(message: str) -> NoReturn:
    raise SystemExit(f"{CHECK_NAME} failed: {message}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def require_object(value: object, keys: set[str], label: str) -> dict[str, object]:
    require(type(value) is dict, f"{label} must be an object")
    result = value
    actual = set(result)
    missing = sorted(keys - actual)
    extra = sorted(actual - keys)
    require(not missing, f"{label} is missing keys: {', '.join(missing)}")
    require(not extra, f"{label} has unknown keys: {', '.join(extra)}")
    return result


def require_string(value: object, label: str) -> str:
    require(type(value) is str and bool(value), f"{label} must be a non-empty string")
    return value


def require_exact_string(value: object, expected: str, label: str) -> None:
    require_string(value, label)
    require(value == expected, f"{label} must be {expected!r}")


def require_integer(value: object, label: str, *, minimum: int = 0) -> int:
    require(
        type(value) is int and value >= minimum,
        f"{label} must be an integer >= {minimum}",
    )
    return value


def require_boolean(value: object, expected: bool, label: str) -> None:
    require(type(value) is bool, f"{label} must be a Boolean")
    require(value is expected, f"{label} must be {str(expected).lower()}")


def reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_receipt(path: pathlib.Path) -> dict[str, object]:
    try:
        path_before = path.lstat()
    except OSError as error:
        fail(f"cannot inspect receipt: {error}")
    require(
        stat.S_ISREG(path_before.st_mode) and not stat.S_ISLNK(path_before.st_mode),
        "receipt must be a regular, non-symbolic file",
    )
    nofollow = getattr(os, "O_NOFOLLOW", None)
    require(nofollow is not None, "platform lacks no-follow file opening")
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
        opened = os.fstat(descriptor)
        require(
            stat.S_ISREG(opened.st_mode)
            and (path_before.st_dev, path_before.st_ino)
            == (opened.st_dev, opened.st_ino),
            "receipt identity changed before opening",
        )
        require(
            0 < opened.st_size <= MAX_RECEIPT_BYTES,
            "receipt size is outside its bound",
        )
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(MAX_RECEIPT_BYTES + 1)
        descriptor_after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail(f"cannot read receipt: {error}")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    require(
        all(
            getattr(opened, field) == getattr(descriptor_after, field)
            for field in STABLE_FIELDS
        )
        and all(
            getattr(opened, field) == getattr(path_after, field)
            for field in STABLE_FIELDS
        ),
        "receipt changed while it was read",
    )
    require(len(raw) == opened.st_size, "receipt length changed while it was read")
    try:
        decoded = raw.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        fail(f"receipt is not strict duplicate-free UTF-8 JSON: {error}")
    require(type(value) is dict, "receipt root must be an object")
    return value


def validate_receipt(receipt: dict[str, object]) -> tuple[list[dict[str, object]], str]:
    root = require_object(
        receipt,
        {
            "schema",
            "receipt_id",
            "artifact",
            "context",
            "projection",
            "measurements",
            "claims",
            "limitations",
        },
        "receipt",
    )
    require_exact_string(root["schema"], SCHEMA, "receipt.schema")
    receipt_id = require_string(root["receipt_id"], "receipt.receipt_id")
    require(
        re.fullmatch(r"[a-z0-9][a-z0-9.-]*", receipt_id) is not None,
        "receipt.receipt_id must be a lowercase stable identifier",
    )

    artifact = require_object(
        root["artifact"],
        {
            "logical_name",
            "observation_kind",
            "raw_pdf_repository_status",
            "receipt_semantics",
            "evidence_credit",
        },
        "receipt.artifact",
    )
    require_exact_string(
        artifact["logical_name"],
        "mathematical-results-guide.pdf",
        "receipt.artifact.logical_name",
    )
    require_exact_string(
        artifact["observation_kind"],
        "retained_diagnostic_wrapper_repeated_luatex_pair",
        "receipt.artifact.observation_kind",
    )
    require_exact_string(
        artifact["raw_pdf_repository_status"],
        "not_tracked",
        "receipt.artifact.raw_pdf_repository_status",
    )
    require_exact_string(
        artifact["receipt_semantics"],
        "measurement_identity_not_proof",
        "receipt.artifact.receipt_semantics",
    )
    require_exact_string(
        artifact["evidence_credit"],
        "finite_byte_observation_only",
        "receipt.artifact.evidence_credit",
    )

    context = require_object(
        root["context"],
        {
            "receipt_date",
            "reported_environment",
            "embedded_pdf_facts",
            "operator_observed_capture_facts",
            "provenance",
        },
        "receipt.context",
    )
    receipt_date = require_string(
        context["receipt_date"], "receipt.context.receipt_date"
    )
    require(
        re.fullmatch(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]", receipt_date) is not None,
        "receipt.context.receipt_date must use YYYY-MM-DD",
    )
    environment = require_object(
        context["reported_environment"],
        {"operating_system", "architecture", "execution_context", "context_source"},
        "receipt.context.reported_environment",
    )
    for field in (
        "operating_system",
        "architecture",
        "execution_context",
        "context_source",
    ):
        require_string(
            environment[field], f"receipt.context.reported_environment.{field}"
        )
    require_exact_string(
        environment["context_source"],
        "operator-observed diagnostic-wrapper capture environment; not encoded completely in the PDFs",
        "receipt.context.reported_environment.context_source",
    )
    embedded = require_object(
        context["embedded_pdf_facts"],
        {
            "embedded_producer",
            "embedded_full_banner",
        },
        "receipt.context.embedded_pdf_facts",
    )
    require_exact_string(
        embedded["embedded_producer"],
        EMBEDDED_PRODUCER,
        "receipt.context.embedded_pdf_facts.embedded_producer",
    )
    require_exact_string(
        embedded["embedded_full_banner"],
        EMBEDDED_FULL_BANNER,
        "receipt.context.embedded_pdf_facts.embedded_full_banner",
    )
    capture = require_object(
        context["operator_observed_capture_facts"],
        {
            "resolved_pandoc_path",
            "resolved_pandoc_file_size_bytes",
            "resolved_pandoc_kind",
            "wrapper_action",
            "pre_existing_raw_tex_path",
            "system_pandoc_path",
            "system_pandoc_version",
            "system_pandoc_install_timing",
        },
        "receipt.context.operator_observed_capture_facts",
    )
    require_exact_string(
        capture["resolved_pandoc_path"],
        "/usr/local/bin/pandoc",
        "receipt.context.operator_observed_capture_facts.resolved_pandoc_path",
    )
    require(
        require_integer(
            capture["resolved_pandoc_file_size_bytes"],
            "receipt.context.operator_observed_capture_facts.resolved_pandoc_file_size_bytes",
            minimum=1,
        )
        == 319,
        "receipt.context.operator_observed_capture_facts.resolved_pandoc_file_size_bytes must be 319",
    )
    capture_strings = {
        "resolved_pandoc_kind": "diagnostic_wrapper_not_pandoc",
        "wrapper_action": "copied_pre_existing_raw_tex",
        "pre_existing_raw_tex_path": "/tmp/pid-rs-pdf-annotation-portability/raw.tex",
        "system_pandoc_path": "/usr/bin/pandoc",
        "system_pandoc_version": "3.1.3",
        "system_pandoc_install_timing": "installed_after_retained_pair_capture",
    }
    for field, expected in capture_strings.items():
        require_exact_string(
            capture[field],
            expected,
            f"receipt.context.operator_observed_capture_facts.{field}",
        )
    provenance = require_object(
        context["provenance"],
        {
            "raw_tex_origin",
            "source_revision",
            "exact_capture_provenance",
            "exact_capture_command",
            "container_image_digest",
            "build_chronology",
        },
        "receipt.context.provenance",
    )
    for field in (
        "raw_tex_origin",
        "source_revision",
        "exact_capture_provenance",
        "exact_capture_command",
        "container_image_digest",
    ):
        require_exact_string(
            provenance[field], "unknown", f"receipt.context.provenance.{field}"
        )
    require_exact_string(
        provenance["build_chronology"],
        "not_authenticated",
        "receipt.context.provenance.build_chronology",
    )

    projection = require_object(
        root["projection"],
        {
            "name",
            "scope",
            "replacement_ascii_byte",
            "payload_span_convention",
            "payload_count_per_file",
            "payload_bytes_per_span",
            "projected_sha256",
        },
        "receipt.projection",
    )
    require_exact_string(
        projection["name"],
        "zero_strict_duplicated_final_trailer_id_hex_payloads",
        "receipt.projection.name",
    )
    require_exact_string(
        projection["scope"],
        "comparison_only_no_pdf_rewrite",
        "receipt.projection.scope",
    )
    require_exact_string(
        projection["replacement_ascii_byte"],
        "0",
        "receipt.projection.replacement_ascii_byte",
    )
    require_exact_string(
        projection["payload_span_convention"],
        "zero_based_half_open_byte_offsets",
        "receipt.projection.payload_span_convention",
    )
    require(
        require_integer(
            projection["payload_count_per_file"],
            "receipt.projection.payload_count_per_file",
        )
        == 2,
        "receipt.projection.payload_count_per_file must be 2",
    )
    payload_bytes = require_integer(
        projection["payload_bytes_per_span"],
        "receipt.projection.payload_bytes_per_span",
    )
    require(payload_bytes == 32, "receipt.projection.payload_bytes_per_span must be 32")
    projected_sha = require_string(
        projection["projected_sha256"], "receipt.projection.projected_sha256"
    )
    require(
        SHA256_PATTERN.fullmatch(projected_sha) is not None,
        "receipt.projection.projected_sha256 is invalid",
    )

    measurements = require_object(
        root["measurements"],
        {"pair_byte_length", "raw_differing_offset_count", "files"},
        "receipt.measurements",
    )
    pair_length = require_integer(
        measurements["pair_byte_length"],
        "receipt.measurements.pair_byte_length",
        minimum=1,
    )
    require(
        pair_length <= MAX_PDF_BYTES,
        "receipt.measurements.pair_byte_length exceeds the PDF bound",
    )
    differing_count = require_integer(
        measurements["raw_differing_offset_count"],
        "receipt.measurements.raw_differing_offset_count",
        minimum=1,
    )
    files_value = measurements["files"]
    require(
        type(files_value) is list and len(files_value) == 2,
        "receipt.measurements.files must contain two entries",
    )
    files: list[dict[str, object]] = []
    expected_roles = ("first", "second")
    for index, expected_role in enumerate(expected_roles):
        entry = require_object(
            files_value[index],
            {
                "role",
                "retained_name",
                "byte_length",
                "raw_sha256",
                "trailer_id_entries_hex",
                "id_payload_spans",
                "projected_sha256",
            },
            f"receipt.measurements.files[{index}]",
        )
        require_exact_string(
            entry["role"], expected_role, f"receipt.measurements.files[{index}].role"
        )
        require_exact_string(
            entry["retained_name"],
            f"{expected_role}.pdf",
            f"receipt.measurements.files[{index}].retained_name",
        )
        require(
            require_integer(
                entry["byte_length"],
                f"receipt.measurements.files[{index}].byte_length",
                minimum=1,
            )
            == pair_length,
            f"receipt.measurements.files[{index}].byte_length must equal pair_byte_length",
        )
        raw_sha = require_string(
            entry["raw_sha256"], f"receipt.measurements.files[{index}].raw_sha256"
        )
        require(
            SHA256_PATTERN.fullmatch(raw_sha) is not None,
            f"receipt.measurements.files[{index}].raw_sha256 is invalid",
        )
        require_exact_string(
            entry["projected_sha256"],
            projected_sha,
            f"receipt.measurements.files[{index}].projected_sha256",
        )

        ids = entry["trailer_id_entries_hex"]
        require(
            type(ids) is list and len(ids) == 2,
            f"receipt.measurements.files[{index}].trailer_id_entries_hex must contain two entries",
        )
        for id_index, value in enumerate(ids):
            text = require_string(
                value,
                f"receipt.measurements.files[{index}].trailer_id_entries_hex[{id_index}]",
            )
            require(
                ID_HEX_PATTERN.fullmatch(text) is not None,
                f"receipt.measurements.files[{index}].trailer_id_entries_hex[{id_index}] is invalid",
            )
        require(
            ids[0] == ids[1],
            f"receipt.measurements.files[{index}] trailer ID must be duplicated",
        )

        spans = entry["id_payload_spans"]
        require(
            type(spans) is list and len(spans) == 2,
            f"receipt.measurements.files[{index}].id_payload_spans must contain two spans",
        )
        previous_end = -1
        for span_index, span_value in enumerate(spans):
            span = require_object(
                span_value,
                {"start", "end_exclusive"},
                f"receipt.measurements.files[{index}].id_payload_spans[{span_index}]",
            )
            start = require_integer(
                span["start"],
                f"receipt.measurements.files[{index}].id_payload_spans[{span_index}].start",
            )
            end = require_integer(
                span["end_exclusive"],
                f"receipt.measurements.files[{index}].id_payload_spans[{span_index}].end_exclusive",
            )
            require(
                end - start == payload_bytes,
                f"receipt.measurements.files[{index}].id_payload_spans[{span_index}] must span 32 bytes",
            )
            require(
                start >= previous_end,
                f"receipt.measurements.files[{index}].id_payload_spans must be ordered and non-overlapping",
            )
            require(
                end <= pair_length,
                f"receipt.measurements.files[{index}].id_payload_spans[{span_index}] exceeds the PDF",
            )
            previous_end = end
        files.append(entry)

    require(
        files[0]["raw_sha256"] != files[1]["raw_sha256"],
        "receipt raw PDF hashes must differ",
    )
    require(
        files[0]["trailer_id_entries_hex"][0] != files[1]["trailer_id_entries_hex"][0],
        "receipt decoded trailer IDs must differ",
    )
    require(
        files[0]["id_payload_spans"] == files[1]["id_payload_spans"],
        "receipt ID payload spans must align across the pair",
    )
    expected_differences = 2 * sum(
        left != right
        for left, right in zip(
            files[0]["trailer_id_entries_hex"][0],
            files[1]["trailer_id_entries_hex"][0],
        )
    )
    require(
        differing_count == expected_differences,
        "receipt raw_differing_offset_count does not equal the duplicated-ID payload arithmetic",
    )

    claims = require_object(
        root["claims"],
        {
            "observed_relation",
            "raw_byte_equality",
            "raw_pdfs_are_tracked",
            "receipt_is_proof",
            "genuine_pandoc_render",
            "end_to_end_old_toolchain_build",
            "portability_credit",
            "execution_credit",
        },
        "receipt.claims",
    )
    require_exact_string(
        claims["observed_relation"],
        "raw_bytes_differ_only_within_the_four_recorded_id_payload_spans",
        "receipt.claims.observed_relation",
    )
    require_boolean(
        claims["raw_byte_equality"], False, "receipt.claims.raw_byte_equality"
    )
    require_boolean(
        claims["raw_pdfs_are_tracked"], False, "receipt.claims.raw_pdfs_are_tracked"
    )
    require_boolean(
        claims["receipt_is_proof"], False, "receipt.claims.receipt_is_proof"
    )
    require_boolean(
        claims["genuine_pandoc_render"],
        False,
        "receipt.claims.genuine_pandoc_render",
    )
    require_boolean(
        claims["end_to_end_old_toolchain_build"],
        False,
        "receipt.claims.end_to_end_old_toolchain_build",
    )
    require_exact_string(
        claims["portability_credit"], "none", "receipt.claims.portability_credit"
    )
    require_exact_string(
        claims["execution_credit"], "none", "receipt.claims.execution_credit"
    )
    require(
        root["limitations"] == LIMITATIONS,
        "receipt.limitations must preserve the exact nine-item limitation set",
    )
    return files, projected_sha


def open_exact_regular(
    raw: str, label: str
) -> tuple[pathlib.Path, int, os.stat_result]:
    path = pathlib.Path(raw)
    try:
        before = path.lstat()
    except OSError as error:
        fail(f"cannot inspect {label} PDF: {error}")
    require(
        stat.S_ISREG(before.st_mode) and not stat.S_ISLNK(before.st_mode),
        f"{label} PDF must be regular and non-symbolic",
    )
    nofollow = getattr(os, "O_NOFOLLOW", None)
    require(nofollow is not None, "platform lacks no-follow file opening")
    try:
        descriptor = os.open(path, os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0))
        opened = os.fstat(descriptor)
    except OSError as error:
        fail(f"cannot open {label} PDF without following links: {error}")
    if not stat.S_ISREG(opened.st_mode) or (before.st_dev, before.st_ino) != (
        opened.st_dev,
        opened.st_ino,
    ):
        os.close(descriptor)
        fail(f"{label} PDF identity changed before opening")
    return path, descriptor, opened


def read_opened(
    path: pathlib.Path, descriptor: int, before: os.stat_result, label: str
) -> bytes:
    require(before.st_nlink == 1, f"{label} PDF must be singly linked")
    require(
        0 < before.st_size <= MAX_PDF_BYTES, f"{label} PDF size is outside its bound"
    )
    try:
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            data = stream.read(MAX_PDF_BYTES + 1)
        after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as error:
        fail(f"cannot read {label} PDF: {error}")
    require(
        all(getattr(before, field) == getattr(after, field) for field in STABLE_FIELDS),
        f"{label} PDF changed while it was read",
    )
    require(
        all(
            getattr(before, field) == getattr(path_after, field)
            for field in STABLE_FIELDS
        ),
        f"{label} PDF path changed while it was read",
    )
    require(
        len(data) == before.st_size, f"{label} PDF length changed while it was read"
    )
    return data


def read_pair(first_raw: str, second_raw: str) -> tuple[bytes, bytes]:
    first_path, first_fd, first_stat = open_exact_regular(first_raw, "first")
    try:
        second_path, second_fd, second_stat = open_exact_regular(second_raw, "second")
    except BaseException:
        os.close(first_fd)
        raise
    try:
        require(
            (first_stat.st_dev, first_stat.st_ino)
            != (second_stat.st_dev, second_stat.st_ino),
            "PDF inputs alias the same file",
        )
        first = read_opened(first_path, first_fd, first_stat, "first")
        second = read_opened(second_path, second_fd, second_stat, "second")
        for path, descriptor, before, label in (
            (first_path, first_fd, first_stat, "first"),
            (second_path, second_fd, second_stat, "second"),
        ):
            descriptor_after = os.fstat(descriptor)
            path_after = path.lstat()
            require(
                all(
                    getattr(before, field) == getattr(descriptor_after, field)
                    for field in STABLE_FIELDS
                )
                and all(
                    getattr(before, field) == getattr(path_after, field)
                    for field in STABLE_FIELDS
                ),
                f"{label} PDF changed before the pair read completed",
            )
    finally:
        os.close(second_fd)
        os.close(first_fd)
    return first, second


def measure_pdf(data: bytes, label: str) -> dict[str, object]:
    require(
        data.count(EMBEDDED_PRODUCER_TOKEN) == 1,
        f"{label} PDF does not contain exactly one recorded embedded LuaHBTeX producer",
    )
    require(
        data.count(EMBEDDED_FULL_BANNER_TOKEN) == 1,
        f"{label} PDF does not contain exactly one recorded embedded LuaHBTeX full banner",
    )
    matches = list(RAW_ID_PATTERN.finditer(data))
    require(
        len(matches) == 1, f"{label} PDF must contain exactly one strict trailer /ID"
    )
    match = matches[0]
    require(
        match.group(1).lower() == match.group(2).lower(),
        f"{label} PDF trailer /ID pair is not duplicated",
    )
    startxref = FINAL_STARTXREF_PATTERN.search(data)
    require(
        startxref is not None,
        f"{label} PDF lacks a final direct startxref/EOF boundary",
    )
    offset = int(startxref.group(1))
    require(
        0 <= offset < startxref.start(),
        f"{label} PDF startxref offset is outside the body",
    )
    object_header = re.match(rb"[0-9]+[ \t]+[0-9]+[ \t\r\n]+obj\b", data[offset:])
    require(
        object_header is not None,
        f"{label} PDF startxref does not select a direct object",
    )
    stream_start = data.find(b"stream", offset, startxref.start())
    require(stream_start >= 0, f"{label} PDF final xref object lacks a stream boundary")
    owner = data[offset:stream_start]
    require(
        re.search(rb"/Type[ \t\r\n]+/XRef\b", owner) is not None,
        f"{label} PDF final object is not a typed XRef stream",
    )
    names = list(ID_NAME_PATTERN.finditer(owner))
    require(
        len(names) == 1 and match.start() == offset + names[0].start(),
        f"{label} PDF strict /ID is not uniquely owned by the final trailer",
    )
    spans = [
        {"start": match.start(group), "end_exclusive": match.end(group)}
        for group in (1, 2)
    ]
    normalized = bytearray(data)
    for span in spans:
        normalized[span["start"] : span["end_exclusive"]] = b"0" * (
            span["end_exclusive"] - span["start"]
        )
    return {
        "byte_length": len(data),
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "trailer_id_entries_hex": [
            match.group(1).decode("ascii"),
            match.group(2).decode("ascii"),
        ],
        "id_payload_spans": spans,
        "projected_sha256": hashlib.sha256(normalized).hexdigest(),
        "projected_bytes": bytes(normalized),
    }


def validate_pair(
    first_raw: str,
    second_raw: str,
    receipt_files: list[dict[str, object]],
    projected_sha: str,
) -> tuple[int, int]:
    first, second = read_pair(first_raw, second_raw)
    require(len(first) == len(second), "observed PDF lengths differ")
    observed = [measure_pdf(first, "first"), measure_pdf(second, "second")]
    for index, role in enumerate(("first", "second")):
        for field in (
            "byte_length",
            "raw_sha256",
            "trailer_id_entries_hex",
            "id_payload_spans",
            "projected_sha256",
        ):
            require(
                observed[index][field] == receipt_files[index][field],
                f"{role} PDF remeasurement does not match receipt field {field}",
            )
    require(
        observed[0]["projected_sha256"] == projected_sha
        and observed[1]["projected_sha256"] == projected_sha,
        "remeasured projected hashes do not match the receipt projection",
    )
    require(
        observed[0]["projected_bytes"] == observed[1]["projected_bytes"],
        "observed PDFs differ outside the exact recorded ID payload spans",
    )
    differing = sum(left != right for left, right in zip(first, second))
    return len(first), differing


def parse_cli(argv: list[str]) -> tuple[pathlib.Path, list[str]]:
    arguments = argv[1:]
    receipt = DEFAULT_RECEIPT
    if arguments[:1] == ["--receipt"]:
        require(len(arguments) >= 2, "--receipt requires a path")
        receipt = pathlib.Path(arguments[1])
        arguments = arguments[2:]
    require(
        len(arguments) in (0, 2)
        and not any(value.startswith("-") for value in arguments),
        "usage: check-mathematical-results-guide-trailer-id-observation.py [--receipt RECEIPT.json] [FIRST.pdf SECOND.pdf]",
    )
    return receipt, arguments


def main(argv: list[str]) -> int:
    receipt_path, pair = parse_cli(argv)
    receipt = load_receipt(receipt_path)
    files, projected_sha = validate_receipt(receipt)
    measurements = receipt["measurements"]
    if not pair:
        print(
            "OK: closed trailer-ID observation receipt and internal arithmetic "
            f"(bytes={measurements['pair_byte_length']}; "
            f"raw_differing_offsets={measurements['raw_differing_offset_count']}; "
            f"projected_sha256={projected_sha}; raw_PDFs=not_tracked; "
            "capture=diagnostic_wrapper_not_pandoc; portability_credit=none; "
            "execution_credit=none; semantics=measurement_identity_not_proof)"
        )
        return 0
    byte_length, differing = validate_pair(pair[0], pair[1], files, projected_sha)
    require(
        differing == measurements["raw_differing_offset_count"],
        "remeasured differing-offset count does not match the receipt",
    )
    print(
        "OK: retained trailer-ID pair remeasures exactly against the receipt "
        f"(bytes={byte_length}; raw_differing_offsets={differing}; "
        f"projected_sha256={projected_sha}; raw_PDFs=not_tracked; "
        "capture=diagnostic_wrapper_not_pandoc; portability_credit=none; "
        "execution_credit=none; semantics=measurement_identity_not_proof)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
