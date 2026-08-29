#!/usr/bin/env python3
"""Mutation tests for the cross-toolchain trailer-ID variance checker."""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys
import tempfile
from typing import NoReturn


ROOT = pathlib.Path(__file__).resolve(strict=True).parent.parent
CHECKER = ROOT / "scripts/check-mathematical-results-guide-pdf-id-variance.py"
CANONICAL = ROOT / "output/pdf/mathematical-results-guide.pdf"
ID_PATTERN = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
FINAL_STARTXREF_PATTERN = re.compile(
    rb"startxref[ \t\r\n]+([0-9]+)[ \t\r\n]+%%EOF[ \t\r\n]*\Z"
)
CHILD_PREFIX = [sys.executable] + (["-O"] if sys.flags.optimize else []) + ["-I", "-B"]


def fail(message: str) -> NoReturn:
    raise SystemExit(
        f"Mathematical results guide PDF trailer-ID variance self-test failed: {message}"
    )


def run(
    first: pathlib.Path, second: pathlib.Path, *, inputs_only: bool = False
) -> subprocess.CompletedProcess[str]:
    arguments = ["--validate-inputs"] if inputs_only else []
    return subprocess.run(
        [*CHILD_PREFIX, str(CHECKER), *arguments, str(first), str(second)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def require_pass(first: pathlib.Path, second: pathlib.Path, label: str) -> None:
    result = run(first, second)
    if result.returncode != 0 or "byte-equal outside" not in result.stdout or result.stderr:
        fail(f"{label} was rejected:\n{result.stdout}{result.stderr}")


def require_failure(
    first: pathlib.Path, second: pathlib.Path, expected: str, label: str
) -> None:
    result = run(first, second)
    if result.returncode == 0:
        fail(f"{label} passed")
    combined = result.stdout + result.stderr
    if expected not in combined:
        fail(f"{label} diagnostic changed:\n{combined}")


def replace_id(data: bytes, first_hex: bytes, second_hex: bytes) -> bytes:
    match = ID_PATTERN.search(data)
    if match is None:
        fail("canonical fixture lacks a strict trailer /ID")
    if len(first_hex) != 32 or len(second_hex) != 32:
        fail("self-test requested a non-32-hex replacement")
    changed = bytearray(data)
    changed[match.start(1) : match.end(1)] = first_hex
    changed[match.start(2) : match.end(2)] = second_hex
    return bytes(changed)


def main() -> int:
    for path, label in ((CHECKER, "checker"), (CANONICAL, "canonical PDF")):
        if path.is_symlink() or not path.is_file():
            fail(f"{label} is absent, non-regular, or symbolic")
    canonical_source = CANONICAL.read_bytes()
    match = ID_PATTERN.search(canonical_source)
    if match is None or match.group(1).lower() != match.group(2).lower():
        fail("canonical PDF lacks one duplicated strict trailer /ID")
    canonical = canonical_source
    replacement = b"0123456789ABCDEF0123456789ABCDEF"
    if match.group(1).upper() == replacement:
        replacement = b"FEDCBA9876543210FEDCBA9876543210"
    varied = replace_id(canonical, replacement, replacement)

    controls = 0
    hostiles = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-guide-id-variance-self-test.") as raw:
        root = pathlib.Path(raw)
        first = root / "first.pdf"
        second = root / "second.pdf"
        first.write_bytes(canonical)
        second.write_bytes(varied)
        require_pass(first, second, "strict variance control")
        controls += 1
        require_pass(second, first, "reversed strict variance control")
        controls += 1

        exact_copy = root / "exact-copy.pdf"
        exact_copy.write_bytes(canonical)
        input_result = run(first, exact_copy, inputs_only=True)
        if (
            input_result.returncode != 0
            or "inputs are distinct, singly linked, bounded" not in input_result.stdout
            or input_result.stderr
        ):
            fail(
                "exact input-contract control was rejected:\n"
                f"{input_result.stdout}{input_result.stderr}"
            )
        controls += 1

        third_id = b"ABCDEF0123456789ABCDEF0123456789"
        if third_id in (match.group(1), replacement):
            third_id = b"9876543210FEDCBA9876543210FEDCBA"
        third_path = root / "second-distinct-id.pdf"
        third_path.write_bytes(replace_id(canonical, third_id, third_id))
        require_pass(first, third_path, "second distinct-ID control")
        controls += 1

        def hostile(
            label: str, left: bytes, right: bytes, expected: str
        ) -> None:
            nonlocal hostiles
            left_path = root / f"hostile-{hostiles + 1}-left.pdf"
            right_path = root / f"hostile-{hostiles + 1}-right.pdf"
            left_path.write_bytes(left)
            right_path.write_bytes(right)
            require_failure(left_path, right_path, expected, label)
            hostiles += 1

        hostile("identical input", canonical, canonical, "inputs are byte-identical")
        same_value_case_drift = replace_id(
            canonical, match.group(1).upper(), match.group(1).upper()
        )
        same_id_lexical_drift = replace_id(canonical, match.group(1), match.group(1))
        hostile(
            "case-only equal decoded ID",
            canonical,
            same_value_case_drift,
            "decoded trailer /ID values are equal",
        )
        same_id_lexical_drift = same_id_lexical_drift.replace(b"/ID [", b"/ID\n[", 1)
        hostile(
            "equal decoded ID with lexical drift",
            canonical,
            same_id_lexical_drift,
            "decoded trailer /ID values are equal",
        )
        hostile("size drift", canonical, varied + b"x", "input byte lengths differ")
        hostile(
            "header drift",
            canonical,
            b"%PDF-1.6" + varied[len(b"%PDF-1.7") :],
            "differ outside the exact duplicated trailer /ID payloads",
        )

        varied_match = ID_PATTERN.search(varied)
        if varied_match is None:
            fail("varied fixture lacks the strict ID")
        whitespace_drift = bytearray(varied)
        whitespace = next(
            (
                index
                for index in range(varied_match.start() + 3, varied_match.start(1) - 1)
                if whitespace_drift[index] in b" \t\r\n"
            ),
            None,
        )
        if whitespace is None:
            fail("cannot locate trailer-ID whitespace mutation target")
        whitespace_drift[whitespace] = ord("\n") if whitespace_drift[whitespace] != ord("\n") else ord("\t")
        hostile(
            "ID-adjacent whitespace drift",
            canonical,
            bytes(whitespace_drift),
            "differ outside the exact duplicated trailer /ID payloads",
        )

        nonduplicated = replace_id(varied, replacement, b"A" * 32)
        hostile(
            "nonduplicated second ID",
            canonical,
            nonduplicated,
            "trailer /ID pair is not duplicated",
        )
        nonduplicated_first = replace_id(canonical, match.group(1), b"B" * 32)
        hostile(
            "nonduplicated first ID",
            nonduplicated_first,
            varied,
            "trailer /ID pair is not duplicated",
        )

        extra_token = b"\n/ID [<00000000000000000000000000000000><00000000000000000000000000000000>]\n"
        hostile(
            "extra ID token",
            canonical + extra_token,
            varied + extra_token,
            "does not contain exactly one strict trailer /ID",
        )

        missing_name_left_buffer = bytearray(canonical)
        missing_name_left_buffer[match.start() : match.start() + 3] = b"/IX"
        missing_name_left = bytes(missing_name_left_buffer)
        missing_name_right_buffer = bytearray(varied)
        missing_name_right_buffer[varied_match.start() : varied_match.start() + 3] = b"/IX"
        missing_name_right = bytes(missing_name_right_buffer)
        hostile(
            "missing ID name",
            missing_name_left,
            missing_name_right,
            "does not contain exactly one strict trailer /ID",
        )

        literal_left = canonical
        literal_right = bytearray(varied)
        literal_match = ID_PATTERN.search(varied)
        if literal_match is None:
            fail("cannot locate literal-ID mutation target")
        literal_right[literal_match.start(1) - 1] = ord("(")
        literal_right[literal_match.end(1)] = ord(")")
        hostile(
            "literal-string ID",
            literal_left,
            bytes(literal_right),
            "does not contain exactly one strict trailer /ID",
        )

        malformed_left = canonical
        malformed_right = bytearray(varied)
        malformed_right[varied_match.end(2)] = ord(" ")
        hostile(
            "missing closing hex delimiter",
            malformed_left,
            bytes(malformed_right),
            "does not contain exactly one strict trailer /ID",
        )

        bad_startxref = bytearray(varied)
        final_startxref = FINAL_STARTXREF_PATTERN.search(varied)
        if final_startxref is None:
            fail("cannot locate final startxref mutation target")
        bad_startxref[
            final_startxref.start(1) : final_startxref.end(1)
        ] = b"0" * len(final_startxref.group(1))
        hostile(
            "startxref does not select its xref stream",
            canonical,
            bytes(bad_startxref),
            "second startxref does not select a direct xref-stream object",
        )

        wrong_xref_type = bytearray(varied)
        xref_offset = int(final_startxref.group(1))
        stream_start = varied.find(b"stream", xref_offset, final_startxref.start())
        xref_name = varied.find(b"/XRef", xref_offset, stream_start)
        if stream_start < 0 or xref_name < 0:
            fail("cannot locate typed xref-stream mutation target")
        wrong_xref_type[xref_name + 1] = ord("Y")
        hostile(
            "startxref object loses its XRef type",
            canonical,
            bytes(wrong_xref_type),
            "second startxref object is not a typed XRef stream",
        )

        unowned_id = bytearray(varied)
        strict_id = varied[varied_match.start() : varied_match.end()]
        owner_separator = varied_match.start() + len(b"/ID")
        if unowned_id[owner_separator] not in b" \t\r\n":
            fail("cannot locate final-owner ID separator mutation target")
        unowned_id[owner_separator] = ord("%")
        external_start = len(b"%PDF-1.7\n")
        external_end = external_start + len(strict_id)
        if external_end >= xref_offset:
            fail("unowned-ID mutation window overlaps the final xref stream")
        unowned_id[external_start:external_end] = strict_id
        hostile(
            "sole strict ID is outside the final trailer owner",
            canonical,
            bytes(unowned_id),
            "second strict /ID is not owned by the final trailer",
        )

        first_symlink = root / "first-symlink.pdf"
        first_symlink.symlink_to(first)
        require_failure(first_symlink, second, "absent, non-regular, or symbolic", "first symlink")
        hostiles += 1
        second_symlink = root / "second-symlink.pdf"
        second_symlink.symlink_to(second)
        require_failure(first, second_symlink, "absent, non-regular, or symbolic", "second symlink")
        hostiles += 1

        alias = root / "alias.pdf"
        alias.hardlink_to(first)
        require_failure(first, alias, "inputs alias the same file", "hard-link alias")
        hostiles += 1
        require_failure(
            first,
            second,
            "first input is not singly linked",
            "first input third-path hard link",
        )
        hostiles += 1
        alias.unlink()
        second_alias = root / "second-alias.pdf"
        second_alias.hardlink_to(second)
        require_failure(
            first,
            second,
            "second input is not singly linked",
            "second input third-path hard link",
        )
        hostiles += 1
        second_alias.unlink()

        missing = root / "missing.pdf"
        require_failure(missing, second, "absent, non-regular, or symbolic", "missing input")
        hostiles += 1
        directory = root / "directory.pdf"
        directory.mkdir()
        require_failure(directory, second, "absent, non-regular, or symbolic", "directory input")
        hostiles += 1

        oversized = root / "oversized.pdf"
        with oversized.open("wb") as stream:
            stream.truncate(16 * 1024 * 1024 + 1)
        require_failure(oversized, second, "exceeds the 16777216-byte bound", "oversized input")
        hostiles += 1

        empty = root / "empty.pdf"
        empty.write_bytes(b"")
        require_failure(empty, second, "first input is empty", "empty input")
        hostiles += 1

        result = subprocess.run(
            [*CHILD_PREFIX, str(CHECKER), str(first)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "usage:" not in result.stdout + result.stderr:
            fail(f"CLI arity mutation diagnostic changed:\n{result.stdout}{result.stderr}")
        hostiles += 1

        result = subprocess.run(
            [*CHILD_PREFIX, str(CHECKER), "--unknown", str(first), str(second)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "usage:" not in result.stdout + result.stderr:
            fail(f"CLI mode mutation diagnostic changed:\n{result.stdout}{result.stderr}")
        hostiles += 1

        result = subprocess.run(
            [*CHILD_PREFIX, str(CHECKER), "--validate-inputs", str(first)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "usage:" not in result.stdout + result.stderr:
            fail(f"CLI missing-operand diagnostic changed:\n{result.stdout}{result.stderr}")
        hostiles += 1

        result = subprocess.run(
            [*CHILD_PREFIX, str(CHECKER), "--unknown", str(first)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 or "usage:" not in result.stdout + result.stderr:
            fail(f"CLI short-unknown-mode diagnostic changed:\n{result.stdout}{result.stderr}")
        hostiles += 1

    print(
        "Mathematical results guide PDF trailer-ID variance self-test passed: "
        f"controls={controls} hostiles={hostiles}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
