#!/usr/bin/env python3
"""Fail-closed mutation suite for the guide-specific font-roster gate."""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile


CHECKER = pathlib.Path(__file__).with_name("check-mathematical-results-guide-font-roster.py")
HEADER = (
    "name                                 type              encoding         emb sub uni object ID\n"
    "------------------------------------ ----------------- ---------------- --- --- --- ---------\n"
)
ROWS = [
    "ABCDEF+LMRoman12-Bold                CID Type 0C       Identity-H       yes yes yes      8  0",
    "BCDEFG+LMRoman10-Regular             CID Type 0C       Identity-H       yes yes yes      9  0",
    "CDEFGH+LMMonoLt10-Regular            CID Type 0C       Identity-H       yes yes yes     10  0",
    "DEFGHI+LatinModernMath-Regular       CID Type 0C       Identity-H       yes yes yes     11  0",
    "EFGHIJ+SourceSansPro-Bold            Type 1C           WinAnsi          yes yes yes     12  0",
    "FGHIJK+SourceSansPro-Semibold        Type 1C           WinAnsi          yes yes yes     13  0",
    "GHIJKL+SourceSansPro-Regular         Type 1C           WinAnsi          yes yes yes     14  0",
    "HIJKLM+SourceSansPro-Regular         CID Type 0C       Identity-H       yes yes yes     15  0",
    "IJKLMN+LMSans10-Bold                 Type 1C           WinAnsi          yes yes yes     16  0",
    "JKLMNO+LMSans10-Regular              Type 1C           WinAnsi          yes yes yes     17  0",
    "KLMNOP+LMSans10-Regular              CID Type 0C       Identity-H       yes yes yes     18  0",
]


def report(rows: list[str] | None = None) -> bytes:
    return (HEADER + "\n".join(ROWS if rows is None else rows) + "\n").encode("utf-8")


def run(path: pathlib.Path) -> subprocess.CompletedProcess[bytes]:
    if sys.flags.optimize not in (0, 1):
        raise SystemExit("font-roster self-test supports only normal Python or exactly one -O")
    optimization = ["-O"] if sys.flags.optimize == 1 else []
    return subprocess.run(
        [
            sys.executable,
            *optimization,
            "-I",
            "-S",
            "-B",
            os.fspath(CHECKER),
            os.fspath(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def require_pass(path: pathlib.Path, expected: bytes | None = None) -> None:
    result = run(path)
    if result.returncode != 0 or result.stderr or (expected is not None and result.stdout != expected):
        raise SystemExit(
            "font-roster control failed\n"
            + result.stdout.decode("utf-8", "replace")
            + result.stderr.decode("utf-8", "replace")
        )


def require_fail(path: pathlib.Path, fragment: bytes) -> None:
    result = run(path)
    if result.returncode == 0 or result.stdout or fragment not in result.stderr:
        raise SystemExit(
            "font-roster hostile had an unexpected disposition\n"
            + result.stdout.decode("utf-8", "replace")
            + result.stderr.decode("utf-8", "replace")
        )


def main() -> int:
    if not CHECKER.is_file() or CHECKER.is_symlink():
        raise SystemExit("font-roster checker is absent, non-regular, or symbolic")
    controls = 0
    hostiles = 0
    with tempfile.TemporaryDirectory(prefix="pid-rs-font-roster-self-test-") as temporary:
        root = pathlib.Path(temporary)
        baseline = root / "baseline.txt"
        baseline.write_bytes(report())
        first = run(baseline)
        if first.returncode != 0 or first.stderr:
            raise SystemExit(first.stderr.decode("utf-8", "replace"))
        controls += 1

        reordered = root / "reordered.txt"
        reordered.write_bytes(report(list(reversed(ROWS))))
        require_pass(reordered, first.stdout)
        controls += 1

        mutations: list[tuple[str, bytes, bytes]] = [
            ("empty", b"", b"report size must be"),
            ("nul", report() + b"\x00", b"contains a NUL"),
            ("utf8", report() + b"\xff", b"not UTF-8"),
            ("header", report().replace(b"name ", b"face ", 1), b"header is absent"),
            ("separator", report().replace(b"----", b"xxxx", 1), b"separator is absent"),
            ("no-rows", HEADER.encode("utf-8"), b"contains no font rows"),
            ("malformed", report() + b"not a pdffonts row\n", b"malformed font row"),
            ("prefix", report().replace(b"ABCDEF+", b"ABCDE+", 1), b"subset prefix"),
            ("helvetica", report().replace(b"LMRoman12-Bold", b"Helvetica-Bold", 1), b"non-contract face"),
            ("unknown", report().replace(b"LMRoman12-Bold", b"MadeUp-Regular", 1), b"non-contract face"),
            ("type3", report().replace(b"CID Type 0C      ", b"Type 3           ", 1), b"non-contract kind/encoding pair"),
            ("truetype", report().replace(b"CID Type 0C      ", b"CID TrueType     ", 1), b"non-contract kind/encoding pair"),
            ("encoding", report().replace(b"Identity-H      ", b"Custom          ", 1), b"non-contract kind/encoding pair"),
            ("type1c-identity", report().replace(b"Type 1C           WinAnsi", b"Type 1C           Identity-H", 1), b"Type 1C + Identity-H"),
            ("type0c-winansi", report().replace(b"CID Type 0C       Identity-H", b"CID Type 0C       WinAnsi   ", 1), b"CID Type 0C + WinAnsi"),
            ("unembedded", report().replace(b"yes yes yes      8", b"no  yes yes      8", 1), b"not embedded"),
            ("whole-font", report().replace(b"yes yes yes      8", b"yes no  yes      8", 1), b"not subset"),
            ("no-unicode", report().replace(b"yes yes yes      8", b"yes yes no       8", 1), b"not Unicode-mapped"),
        ]
        for face in (
            b"SourceSansPro-Regular",
            b"SourceSansPro-Semibold",
            b"SourceSansPro-Bold",
            b"LMSans10-Regular",
            b"LMSans10-Bold",
        ):
            rows = [row for row in ROWS if face.decode("ascii") not in row]
            mutations.append(("missing-" + face.decode("ascii"), report(rows), b"faces are absent"))

        for name, payload, fragment in mutations:
            path = root / f"{name}.txt"
            path.write_bytes(payload)
            require_fail(path, fragment)
            hostiles += 1

        missing = root / "missing.txt"
        require_fail(missing, b"cannot stat report")
        hostiles += 1
        symbolic = root / "symbolic.txt"
        symbolic.symlink_to(baseline)
        require_fail(symbolic, b"non-symbolic regular file")
        hostiles += 1
        oversized = root / "oversized.txt"
        oversized.write_bytes(b"x" * 1_000_001)
        require_fail(oversized, b"report size must be")
        hostiles += 1

    print(f"Mathematical results guide font-roster self-test passed: controls={controls} hostiles={hostiles}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
