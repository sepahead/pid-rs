#!/usr/bin/env python3
"""Mutation tests for the trailer-ID observation receipt checker."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
CHECKER = ROOT / "scripts/check-mathematical-results-guide-trailer-id-observation.py"
RECEIPT = (
    ROOT / "audit/evidence/"
    "mathematical-results-guide-old-toolchain-trailer-id-observation-v1.json"
)
ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
CHILD_PREFIX = [sys.executable] + (["-O"] if sys.flags.optimize else []) + ["-I", "-B"]


def fail(message: str) -> NoReturn:
    raise SystemExit(
        "Mathematical results guide trailer-ID observation receipt self-test "
        f"failed: {message}"
    )


def run(
    receipt: pathlib.Path,
    first: pathlib.Path | None = None,
    second: pathlib.Path | None = None,
) -> subprocess.CompletedProcess[str]:
    arguments = [*CHILD_PREFIX, str(CHECKER), "--receipt", str(receipt)]
    if first is not None or second is not None:
        if first is None or second is None:
            fail("self-test constructed an incomplete pair invocation")
        arguments.extend((str(first), str(second)))
    return subprocess.run(
        arguments,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def require_pass(
    receipt: pathlib.Path,
    label: str,
    first: pathlib.Path | None = None,
    second: pathlib.Path | None = None,
) -> None:
    result = run(receipt, first, second)
    required_output = (
        "OK:",
        "capture=diagnostic_wrapper_not_pandoc",
        "portability_credit=none",
        "execution_credit=none",
    )
    if (
        result.returncode != 0
        or any(token not in result.stdout for token in required_output)
        or result.stderr
    ):
        fail(f"{label} was rejected:\n{result.stdout}{result.stderr}")


def require_failure(
    receipt: pathlib.Path,
    expected: str,
    label: str,
    first: pathlib.Path | None = None,
    second: pathlib.Path | None = None,
) -> None:
    result = run(receipt, first, second)
    if result.returncode == 0:
        fail(f"{label} passed")
    combined = result.stdout + result.stderr
    if expected not in combined:
        fail(f"{label} diagnostic changed:\n{combined}")


def write_json(path: pathlib.Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def make_fake_pdf(identifier: bytes) -> bytes:
    if len(identifier) != 32 or re.fullmatch(rb"[0-9A-F]{32}", identifier) is None:
        fail("fake fixture requested an invalid ID")
    prefix = b"%PDF-1.7\n"
    embedded = (
        b"1 0 obj\n"
        b"<< /Producer (luahbtex-1.17.0) "
        b"/PTEX.FullBanner (This is LuaHBTeX, Version 1.17.0 (TeX Live 2023/Debian)) >>\n"
        b"endobj\n"
    )
    xref_offset = len(prefix) + len(embedded)
    xref = (
        b"7 0 obj\n"
        b"<< /Type /XRef /Size 8 /W [1 2 1] /ID [<"
        + identifier
        + b"><"
        + identifier
        + b">] /Length 0 >>\n"
        b"stream\n\nendstream\nendobj\n"
    )
    return (
        prefix + embedded + xref + f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
    )


def measure(data: bytes) -> dict[str, object]:
    match = ID_PATTERN.search(data)
    if match is None:
        fail("fake fixture lacks a strict ID")
    spans = [
        {"start": match.start(group), "end_exclusive": match.end(group)}
        for group in (1, 2)
    ]
    projected = bytearray(data)
    for span in spans:
        projected[span["start"] : span["end_exclusive"]] = b"0" * 32
    return {
        "byte_length": len(data),
        "raw_sha256": hashlib.sha256(data).hexdigest(),
        "trailer_id_entries_hex": [
            match.group(1).decode("ascii"),
            match.group(2).decode("ascii"),
        ],
        "id_payload_spans": spans,
        "projected_sha256": hashlib.sha256(projected).hexdigest(),
    }


def receipt_for_pair(
    base: dict[str, object], first: bytes, second: bytes
) -> dict[str, object]:
    if len(first) != len(second):
        fail("fake fixture pair lengths differ")
    result = copy.deepcopy(base)
    first_measurement = measure(first)
    second_measurement = measure(second)
    measurements = result["measurements"]
    measurements["pair_byte_length"] = len(first)
    measurements["raw_differing_offset_count"] = sum(
        left != right for left, right in zip(first, second)
    )
    for role, entry, observed in zip(
        ("first", "second"),
        measurements["files"],
        (first_measurement, second_measurement),
    ):
        entry.clear()
        entry.update(
            {
                "role": role,
                "retained_name": f"{role}.pdf",
                **observed,
            }
        )
    projected_sha = first_measurement["projected_sha256"]
    if projected_sha != second_measurement["projected_sha256"]:
        fail("fake fixture projection does not agree")
    result["projection"]["projected_sha256"] = projected_sha
    return result


def main() -> int:
    for path, label in ((CHECKER, "checker"), (RECEIPT, "receipt")):
        if path.is_symlink() or not path.is_file():
            fail(f"{label} is absent, non-regular, or symbolic")
    try:
        base = json.loads(RECEIPT.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        fail(f"cannot load production receipt: {error}")

    controls = 0
    hostiles = 0
    with tempfile.TemporaryDirectory(
        prefix="pid-rs-guide-trailer-receipt-self-test."
    ) as raw:
        root = pathlib.Path(raw)
        production_copy = root / "production.json"
        write_json(production_copy, base)
        require_pass(production_copy, "production receipt-only control")
        controls += 1

        first_bytes = make_fake_pdf(b"0123456789ABCDEF0123456789ABCDEF")
        second_bytes = make_fake_pdf(b"FEDCBA9876543210FEDCBA9876543210")
        fixture = receipt_for_pair(base, first_bytes, second_bytes)
        fixture_receipt = root / "fixture.json"
        first = root / "first.pdf"
        second = root / "second.pdf"
        write_json(fixture_receipt, fixture)
        first.write_bytes(first_bytes)
        second.write_bytes(second_bytes)
        require_pass(fixture_receipt, "synthetic receipt-only control")
        controls += 1
        require_pass(fixture_receipt, "synthetic remeasurement control", first, second)
        controls += 1

        def hostile_receipt(
            label: str,
            mutate: Callable[[dict[str, object]], None],
            expected: str,
        ) -> None:
            nonlocal hostiles
            changed = copy.deepcopy(fixture)
            mutate(changed)
            path = root / f"hostile-receipt-{hostiles + 1}.json"
            write_json(path, changed)
            require_failure(path, expected, label)
            hostiles += 1

        hostile_receipt(
            "missing root key",
            lambda value: value.pop("claims"),
            "missing keys: claims",
        )
        hostile_receipt(
            "extra root key",
            lambda value: value.update({"extra": 1}),
            "unknown keys: extra",
        )
        hostile_receipt(
            "wrong schema",
            lambda value: value.update({"schema": "v2"}),
            "receipt.schema must be",
        )
        hostile_receipt(
            "unstable receipt ID",
            lambda value: value.update({"receipt_id": "UPPER"}),
            "lowercase stable identifier",
        )
        hostile_receipt(
            "tracked raw-PDF status",
            lambda value: value["artifact"].update(
                {"raw_pdf_repository_status": "tracked"}
            ),
            "raw_pdf_repository_status must be 'not_tracked'",
        )
        hostile_receipt(
            "proof semantics",
            lambda value: value["artifact"].update({"receipt_semantics": "proof"}),
            "receipt_semantics must be 'measurement_identity_not_proof'",
        )
        hostile_receipt(
            "Boolean receipt date",
            lambda value: value["context"].update({"receipt_date": True}),
            "receipt.context.receipt_date must be a non-empty string",
        )
        hostile_receipt(
            "extra environment field",
            lambda value: value["context"]["reported_environment"].update(
                {"image_digest": "unknown"}
            ),
            "unknown keys: image_digest",
        )
        hostile_receipt(
            "strengthened context source",
            lambda value: value["context"]["reported_environment"].update(
                {"context_source": "proven"}
            ),
            "context_source must be",
        )
        hostile_receipt(
            "upgraded evidence credit",
            lambda value: value["artifact"].update(
                {"evidence_credit": "portability_evidence"}
            ),
            "evidence_credit must be 'finite_byte_observation_only'",
        )
        hostile_receipt(
            "invented genuine Pandoc resolution",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"resolved_pandoc_path": "/usr/bin/pandoc"}
            ),
            "resolved_pandoc_path must be '/usr/local/bin/pandoc'",
        )
        hostile_receipt(
            "invented genuine Pandoc kind",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"resolved_pandoc_kind": "pandoc_3.1.3"}
            ),
            "resolved_pandoc_kind must be 'diagnostic_wrapper_not_pandoc'",
        )
        hostile_receipt(
            "invented Pandoc-used field",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"pandoc_used_version": "3.1.3"}
            ),
            "unknown keys: pandoc_used_version",
        )
        hostile_receipt(
            "changed wrapper size",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"resolved_pandoc_file_size_bytes": 320}
            ),
            "resolved_pandoc_file_size_bytes must be 319",
        )
        hostile_receipt(
            "invented renderer action",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"wrapper_action": "rendered_markdown"}
            ),
            "wrapper_action must be 'copied_pre_existing_raw_tex'",
        )
        hostile_receipt(
            "invented pre-capture Pandoc install",
            lambda value: value["context"]["operator_observed_capture_facts"].update(
                {"system_pandoc_install_timing": "installed_before_capture"}
            ),
            "system_pandoc_install_timing must be 'installed_after_retained_pair_capture'",
        )
        hostile_receipt(
            "invented raw-TeX origin",
            lambda value: value["context"]["provenance"].update(
                {"raw_tex_origin": "repository_source"}
            ),
            "raw_tex_origin must be 'unknown'",
        )
        hostile_receipt(
            "invented source revision custody",
            lambda value: value["context"]["provenance"].update(
                {"source_revision": "9ed6831d"}
            ),
            "source_revision must be 'unknown'",
        )
        hostile_receipt(
            "invented exact capture provenance",
            lambda value: value["context"]["provenance"].update(
                {"exact_capture_provenance": "authenticated"}
            ),
            "exact_capture_provenance must be 'unknown'",
        )
        hostile_receipt(
            "invented exact command custody",
            lambda value: value["context"]["provenance"].update(
                {"exact_capture_command": "builder --cross-toolchain"}
            ),
            "exact_capture_command must be 'unknown'",
        )
        hostile_receipt(
            "invented authenticated chronology",
            lambda value: value["context"]["provenance"].update(
                {"build_chronology": "authenticated"}
            ),
            "build_chronology must be 'not_authenticated'",
        )
        hostile_receipt(
            "broadened projection",
            lambda value: value["projection"].update({"name": "normalize_pdf"}),
            "receipt.projection.name must be",
        )
        hostile_receipt(
            "rewrite projection",
            lambda value: value["projection"].update({"scope": "rewrite"}),
            "receipt.projection.scope must be 'comparison_only_no_pdf_rewrite'",
        )
        hostile_receipt(
            "wrong replacement",
            lambda value: value["projection"].update({"replacement_ascii_byte": "X"}),
            "replacement_ascii_byte must be '0'",
        )
        hostile_receipt(
            "Boolean payload count",
            lambda value: value["projection"].update({"payload_count_per_file": True}),
            "payload_count_per_file must be an integer",
        )
        hostile_receipt(
            "wrong payload width",
            lambda value: value["projection"].update({"payload_bytes_per_span": 16}),
            "payload_bytes_per_span must be 32",
        )
        hostile_receipt(
            "uppercase projected hash",
            lambda value: value["projection"].update(
                {"projected_sha256": value["projection"]["projected_sha256"].upper()}
            ),
            "projected_sha256 is invalid",
        )
        hostile_receipt(
            "Boolean pair length",
            lambda value: value["measurements"].update({"pair_byte_length": True}),
            "pair_byte_length must be an integer",
        )
        hostile_receipt(
            "wrong differing-offset count",
            lambda value: value["measurements"].update(
                {
                    "raw_differing_offset_count": value["measurements"][
                        "raw_differing_offset_count"
                    ]
                    + 1
                }
            ),
            "does not equal the duplicated-ID payload arithmetic",
        )
        hostile_receipt(
            "reversed role",
            lambda value: value["measurements"]["files"][0].update({"role": "second"}),
            "files[0].role must be 'first'",
        )
        hostile_receipt(
            "extra file field",
            lambda value: value["measurements"]["files"][0].update(
                {"path": "/tmp/first.pdf"}
            ),
            "unknown keys: path",
        )
        hostile_receipt(
            "uppercase raw hash",
            lambda value: value["measurements"]["files"][0].update(
                {"raw_sha256": value["measurements"]["files"][0]["raw_sha256"].upper()}
            ),
            "raw_sha256 is invalid",
        )
        hostile_receipt(
            "lowercase ID",
            lambda value: value["measurements"]["files"][0].update(
                {"trailer_id_entries_hex": ["a" * 32, "a" * 32]}
            ),
            "trailer_id_entries_hex[0] is invalid",
        )
        hostile_receipt(
            "nonduplicated ID",
            lambda value: value["measurements"]["files"][0].update(
                {"trailer_id_entries_hex": ["A" * 32, "B" * 32]}
            ),
            "trailer ID must be duplicated",
        )
        hostile_receipt(
            "short ID span",
            lambda value: value["measurements"]["files"][0]["id_payload_spans"][
                0
            ].update(
                {
                    "end_exclusive": value["measurements"]["files"][0][
                        "id_payload_spans"
                    ][0]["end_exclusive"]
                    - 1
                }
            ),
            "must span 32 bytes",
        )
        hostile_receipt(
            "misaligned pair spans",
            lambda value: value["measurements"]["files"][1]["id_payload_spans"][
                0
            ].update(
                {
                    "start": value["measurements"]["files"][1]["id_payload_spans"][0][
                        "start"
                    ]
                    + 1,
                    "end_exclusive": value["measurements"]["files"][1][
                        "id_payload_spans"
                    ][0]["end_exclusive"]
                    + 1,
                }
            ),
            "ID payload spans must align",
        )
        hostile_receipt(
            "equal raw hashes",
            lambda value: value["measurements"]["files"][1].update(
                {"raw_sha256": value["measurements"]["files"][0]["raw_sha256"]}
            ),
            "raw PDF hashes must differ",
        )
        hostile_receipt(
            "raw equality claim",
            lambda value: value["claims"].update({"raw_byte_equality": True}),
            "raw_byte_equality must be false",
        )
        hostile_receipt(
            "tracked-PDF claim",
            lambda value: value["claims"].update({"raw_pdfs_are_tracked": True}),
            "raw_pdfs_are_tracked must be false",
        )
        hostile_receipt(
            "proof claim",
            lambda value: value["claims"].update({"receipt_is_proof": True}),
            "receipt_is_proof must be false",
        )
        hostile_receipt(
            "genuine Pandoc claim",
            lambda value: value["claims"].update({"genuine_pandoc_render": True}),
            "genuine_pandoc_render must be false",
        )
        hostile_receipt(
            "end-to-end old-toolchain claim",
            lambda value: value["claims"].update(
                {"end_to_end_old_toolchain_build": True}
            ),
            "end_to_end_old_toolchain_build must be false",
        )
        hostile_receipt(
            "portability-credit upgrade",
            lambda value: value["claims"].update({"portability_credit": "full"}),
            "portability_credit must be 'none'",
        )
        hostile_receipt(
            "execution-credit upgrade",
            lambda value: value["claims"].update({"execution_credit": "full"}),
            "execution_credit must be 'none'",
        )
        hostile_receipt(
            "removed limitation",
            lambda value: value["limitations"].pop(),
            "exact nine-item limitation set",
        )

        duplicate = root / "hostile-duplicate-key.json"
        duplicate.write_text(
            '{"schema":"duplicate",' + fixture_receipt.read_text(encoding="utf-8")[1:],
            encoding="utf-8",
        )
        require_failure(duplicate, "duplicate JSON key: schema", "duplicate JSON key")
        hostiles += 1

        receipt_symlink = root / "receipt-symlink.json"
        receipt_symlink.symlink_to(fixture_receipt)
        require_failure(
            receipt_symlink,
            "receipt must be a regular, non-symbolic file",
            "symbolic receipt",
        )
        hostiles += 1

        require_failure(
            fixture_receipt,
            "first PDF remeasurement",
            "reversed observed pair",
            second,
            first,
        )
        hostiles += 1

        outside = root / "outside.pdf"
        outside_bytes = bytearray(second_bytes)
        outside_bytes[1] = ord("Q")
        outside.write_bytes(outside_bytes)
        outside_receipt_value = copy.deepcopy(fixture)
        outside_receipt_value["measurements"]["files"][1]["raw_sha256"] = (
            hashlib.sha256(outside_bytes).hexdigest()
        )
        outside_receipt = root / "outside.json"
        write_json(outside_receipt, outside_receipt_value)
        require_failure(
            outside_receipt,
            "second PDF remeasurement does not match receipt field projected_sha256",
            "outside-ID byte mutation",
            first,
            outside,
        )
        hostiles += 1

        nonduplicated = root / "nonduplicated.pdf"
        nonduplicated_bytes = bytearray(second_bytes)
        second_match = ID_PATTERN.search(second_bytes)
        if second_match is None:
            fail("cannot locate synthetic second ID")
        nonduplicated_bytes[second_match.start(2)] = ord("A")
        nonduplicated.write_bytes(nonduplicated_bytes)
        nonduplicated_receipt_value = copy.deepcopy(fixture)
        nonduplicated_receipt_value["measurements"]["files"][1]["raw_sha256"] = (
            hashlib.sha256(nonduplicated_bytes).hexdigest()
        )
        nonduplicated_receipt = root / "nonduplicated.json"
        write_json(nonduplicated_receipt, nonduplicated_receipt_value)
        require_failure(
            nonduplicated_receipt,
            "trailer /ID pair is not duplicated",
            "nonduplicated observed ID",
            first,
            nonduplicated,
        )
        hostiles += 1

        wrong_type_first = first_bytes.replace(b"/Type /XRef", b"/Type /YRef", 1)
        wrong_type_second = second_bytes.replace(b"/Type /XRef", b"/Type /YRef", 1)
        wrong_type_first_path = root / "wrong-type-first.pdf"
        wrong_type_second_path = root / "wrong-type-second.pdf"
        wrong_type_first_path.write_bytes(wrong_type_first)
        wrong_type_second_path.write_bytes(wrong_type_second)
        wrong_type_receipt_value = receipt_for_pair(
            base, wrong_type_first, wrong_type_second
        )
        wrong_type_receipt = root / "wrong-type.json"
        write_json(wrong_type_receipt, wrong_type_receipt_value)
        require_failure(
            wrong_type_receipt,
            "final object is not a typed XRef stream",
            "non-XRef final owner",
            wrong_type_first_path,
            wrong_type_second_path,
        )
        hostiles += 1

        wrong_producer_first = first_bytes.replace(
            b"/Producer (luahbtex-1.17.0)", b"/Producer (luahbtex-1.18.0)", 1
        )
        wrong_producer_second = second_bytes.replace(
            b"/Producer (luahbtex-1.17.0)", b"/Producer (luahbtex-1.18.0)", 1
        )
        wrong_producer_first_path = root / "wrong-producer-first.pdf"
        wrong_producer_second_path = root / "wrong-producer-second.pdf"
        wrong_producer_first_path.write_bytes(wrong_producer_first)
        wrong_producer_second_path.write_bytes(wrong_producer_second)
        wrong_producer_receipt_value = receipt_for_pair(
            base, wrong_producer_first, wrong_producer_second
        )
        wrong_producer_receipt = root / "wrong-producer.json"
        write_json(wrong_producer_receipt, wrong_producer_receipt_value)
        require_failure(
            wrong_producer_receipt,
            "does not contain exactly one recorded embedded LuaHBTeX producer",
            "changed embedded producer",
            wrong_producer_first_path,
            wrong_producer_second_path,
        )
        hostiles += 1

        first_symlink = root / "first-symlink.pdf"
        first_symlink.symlink_to(first)
        require_failure(
            fixture_receipt,
            "first PDF must be regular and non-symbolic",
            "symbolic first PDF",
            first_symlink,
            second,
        )
        hostiles += 1

        alias = root / "alias.pdf"
        alias.hardlink_to(first)
        require_failure(
            fixture_receipt,
            "PDF inputs alias the same file",
            "aliased pair",
            first,
            alias,
        )
        hostiles += 1
        require_failure(
            fixture_receipt,
            "first PDF must be singly linked",
            "third-path hard link",
            first,
            second,
        )
        hostiles += 1
        alias.unlink()

        malformed_cli = subprocess.run(
            [
                *CHILD_PREFIX,
                str(CHECKER),
                "--receipt",
                str(fixture_receipt),
                str(first),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if malformed_cli.returncode == 0 or "usage:" not in malformed_cli.stderr:
            fail(
                f"one-path CLI hostile changed:\n{malformed_cli.stdout}{malformed_cli.stderr}"
            )
        hostiles += 1

    print(
        "OK: trailer-ID observation receipt self-test "
        f"({controls} controls; {hostiles} hostile mutations; optimized={bool(sys.flags.optimize)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
