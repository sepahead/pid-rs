#!/usr/bin/env python3
"""Dependency-free adversarial tests for compare-formal-pdf-renders.py."""

from __future__ import annotations

import hashlib
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
from typing import NoReturn
import zlib


COMPARATOR = Path(__file__).resolve().with_name("compare-formal-pdf-renders.py")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
HEADER = (
    "page\twidth\theight\tmean_abs\tchanged_pixels\tchanged_fraction\t"
    "large_pixels\tlarge_fraction\tmax_abs\tleft_bytes\tleft_sha256\t"
    "right_bytes\tright_sha256"
)
CASES: list[str] = []


class SelfTestError(RuntimeError):
    """A comparator control did not have its required disposition."""


def fail(detail: str) -> NoReturn:
    raise SelfTestError(detail)


def require(condition: bool, detail: str) -> None:
    if not condition:
        fail(detail)


def chunk(kind: bytes, payload: bytes) -> bytes:
    require(len(kind) == 4, "test fixture requested a malformed chunk name")
    checksum = zlib.crc32(kind)
    checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
    return (
        struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)
    )


def png_bytes(
    width: int,
    height: int,
    pixels: bytes,
    *,
    color_type: int = 2,
    filter_type: int = 0,
    interlace: int = 0,
    before_idat: tuple[tuple[bytes, bytes], ...] = (),
    compressed_suffix: bytes = b"",
) -> bytes:
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(color_type)
    require(channels is not None, "test fixture requested an unknown color type")
    require(
        len(pixels) == width * height * channels,
        "test fixture pixel count is inconsistent",
    )
    stride = width * channels
    raw = b"".join(
        bytes((filter_type,)) + pixels[row * stride : (row + 1) * stride]
        for row in range(height)
    )
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, interlace)
    return b"".join(
        (
            PNG_SIGNATURE,
            chunk(b"IHDR", ihdr),
            *(chunk(kind, payload) for kind, payload in before_idat),
            chunk(b"IDAT", zlib.compress(raw, 9) + compressed_suffix),
            chunk(b"IEND", b""),
        )
    )


def pair(
    root: Path,
    name: str,
    left_png: bytes,
    right_png: bytes,
) -> tuple[Path, Path, Path]:
    case_root = root / name
    left = case_root / "left"
    right = case_root / "right"
    left.mkdir(parents=True)
    right.mkdir()
    (left / "page-1.png").write_bytes(left_png)
    (right / "page-1.png").write_bytes(right_png)
    return left, right, case_root / "receipt.tsv"


def invoke(
    left: Path,
    right: Path,
    receipt: Path,
    *,
    label: str,
    pages: int = 1,
    extra: tuple[str, ...] = (),
) -> subprocess.CompletedProcess[bytes]:
    command = (
        sys.executable,
        "-I",
        "-S",
        str(COMPARATOR),
        "--left-dir",
        str(left),
        "--right-dir",
        str(right),
        "--pages",
        str(pages),
        "--label",
        label,
        "--receipt",
        str(receipt),
        *extra,
    )
    return subprocess.run(
        command,
        check=False,
        capture_output=True,
        env={"LANG": "C", "LC_ALL": "C", "TZ": "UTC"},
        timeout=20,
    )


def expect_success(
    name: str,
    left: Path,
    right: Path,
    receipt: Path,
    *,
    label: str,
    extra: tuple[str, ...] = (),
) -> bytes:
    process = invoke(left, right, receipt, label=label, extra=extra)
    require(
        process.returncode == 0,
        f"{name}: expected success, got {process.returncode}: "
        f"{(process.stdout + process.stderr).decode('utf-8', 'replace')}",
    )
    require(process.stdout == b"", f"{name}: successful comparator wrote to stdout")
    require(process.stderr == b"", f"{name}: successful comparator wrote to stderr")
    metadata = receipt.lstat()
    require(stat.S_ISREG(metadata.st_mode), f"{name}: receipt is not regular")
    require(metadata.st_nlink == 1, f"{name}: receipt has multiple links")
    require(
        stat.S_IMODE(metadata.st_mode) == 0o644, f"{name}: receipt mode is not 0644"
    )
    raw = receipt.read_bytes()
    require(raw.endswith(b"\n"), f"{name}: receipt lacks its final LF")
    require(not raw.endswith(b"\n\n"), f"{name}: receipt has redundant final LFs")
    require(b"\r" not in raw, f"{name}: receipt contains CR bytes")
    CASES.append(name)
    return raw


def expect_failure(
    name: str,
    left: Path,
    right: Path,
    receipt: Path,
    *,
    fragment: bytes,
    label: str = "negative-control",
    pages: int = 1,
    extra: tuple[str, ...] = (),
    returncode: int = 1,
    receipt_may_exist: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    process = invoke(
        left,
        right,
        receipt,
        label=label,
        pages=pages,
        extra=extra,
    )
    require(
        process.returncode == returncode,
        f"{name}: expected exit {returncode}, got {process.returncode}: "
        f"{(process.stdout + process.stderr).decode('utf-8', 'replace')}",
    )
    require(process.stdout == b"", f"{name}: failing comparator wrote to stdout")
    require(
        fragment in process.stderr, f"{name}: missing failure fragment {fragment!r}"
    )
    if not receipt_may_exist:
        require(not receipt.exists(), f"{name}: failing comparator published a receipt")
        require(
            not receipt.is_symlink(),
            f"{name}: failing comparator published a receipt link",
        )
    CASES.append(name)
    return process


def run() -> None:
    require(COMPARATOR.is_file(), f"missing comparator: {COMPARATOR}")
    black = bytes(10 * 10 * 3)
    baseline = png_bytes(10, 10, black)

    with tempfile.TemporaryDirectory(
        prefix="pid-rs-formal-render-comparator-self-test."
    ) as raw:
        root = Path(raw)

        left, right, receipt = pair(root, "identical", baseline, baseline)
        expect_success("identical", left, right, receipt, label="identical")

        gray = png_bytes(10, 10, bytes(10 * 10), color_type=0)
        left, right, receipt = pair(root, "identical-gray", gray, gray)
        expect_success("identical-gray", left, right, receipt, label="identical-gray")

        at_cutoff_pixels = bytearray(black)
        at_cutoff_pixels[0:3] = bytes((24, 24, 24))
        at_cutoff_pixels[3:6] = bytes((24, 24, 24))
        at_cutoff = png_bytes(10, 10, bytes(at_cutoff_pixels))
        left, right, receipt = pair(root, "large-delta-at-cutoff", baseline, at_cutoff)
        raw_receipt = expect_success(
            "large-delta-at-cutoff",
            left,
            right,
            receipt,
            label="large-delta-at-cutoff",
            extra=(
                "--large-delta",
                "24",
                "--max-mean-abs",
                "0.48",
                "--max-changed-fraction",
                "0.02",
                "--max-large-fraction",
                "0",
            ),
        )
        at_cutoff_row = raw_receipt.decode("ascii").splitlines()[-1].split("\t")
        require(
            at_cutoff_row[3:9]
            == ["0.480000000", "2", "0.020000000", "0", "0.000000000", "24"],
            "delta equal to large-delta was not classified exactly",
        )

        bounded_pixels = bytearray(black)
        bounded_pixels[0:3] = bytes((24, 24, 24))
        bounded_pixels[3:6] = bytes((25, 25, 25))
        bounded = png_bytes(10, 10, bytes(bounded_pixels))
        left, right, receipt = pair(root, "threshold-equality", baseline, bounded)
        threshold_flags = (
            "--large-delta",
            "24",
            "--max-mean-abs",
            "0.4900",
            "--max-changed-fraction",
            "0.020",
            "--max-large-fraction",
            "0.0100",
        )
        threshold_receipt = expect_success(
            "threshold-equality",
            left,
            right,
            receipt,
            label="threshold-equality",
            extra=threshold_flags,
        )
        expected_receipt = (
            "schema\tpid-rs-formal-render-comparison-v2\n"
            "label\tthreshold-equality\n"
            "pages\t1\n"
            "large_delta\t24\n"
            "max_mean_abs\t0.49\n"
            "max_changed_fraction\t0.02\n"
            "max_large_fraction\t0.01\n"
            f"{HEADER}\n"
            f"1\t10\t10\t0.490000000\t2\t0.020000000\t1\t0.010000000\t25\t"
            f"{len(baseline)}\t{hashlib.sha256(baseline).hexdigest()}\t"
            f"{len(bounded)}\t{hashlib.sha256(bounded).hexdigest()}\n"
        ).encode("ascii")
        require(
            threshold_receipt == expected_receipt, "receipt bytes are not canonical"
        )

        equivalent_receipt = receipt.with_name("receipt-equivalent.tsv")
        equivalent = expect_success(
            "threshold-canonicalization",
            left,
            right,
            equivalent_receipt,
            label="threshold-equality",
            extra=(
                "--large-delta",
                "24",
                "--max-mean-abs",
                "00.49000",
                "--max-changed-fraction",
                "00.0200",
                "--max-large-fraction",
                "00.010",
            ),
        )
        require(
            equivalent == threshold_receipt, "equivalent decimals changed receipt bytes"
        )

        for name, flags in (
            (
                "mean-over-bound",
                (
                    "--max-mean-abs",
                    "0.489999999",
                    "--max-changed-fraction",
                    "1",
                    "--max-large-fraction",
                    "1",
                ),
            ),
            (
                "changed-over-bound",
                (
                    "--max-mean-abs",
                    "255",
                    "--max-changed-fraction",
                    "0.019999999",
                    "--max-large-fraction",
                    "1",
                ),
            ),
            (
                "large-over-bound",
                (
                    "--max-mean-abs",
                    "255",
                    "--max-changed-fraction",
                    "1",
                    "--max-large-fraction",
                    "0.009999999",
                ),
            ),
        ):
            case_receipt = receipt.with_name(f"{name}.tsv")
            expect_failure(
                name,
                left,
                right,
                case_receipt,
                fragment=b"exceeds its visual bound",
                extra=flags,
            )

        malformed_fixtures = (
            (
                "bad-crc",
                baseline[:-1] + bytes((baseline[-1] ^ 1,)),
                b"bad b'IEND' CRC",
            ),
            ("truncated", baseline[:-2], b"truncated chunk"),
            (
                "bad-filter",
                png_bytes(10, 10, black, filter_type=5),
                b"unsupported PNG filter 5",
            ),
            (
                "bad-color",
                png_bytes(10, 10, bytes(10 * 10 * 4), color_type=6),
                b"not an opaque, non-interlaced 8-bit gray/RGB PNG",
            ),
            (
                "interlaced",
                png_bytes(10, 10, black, interlace=1),
                b"not an opaque, non-interlaced 8-bit gray/RGB PNG",
            ),
            (
                "transparent",
                png_bytes(10, 10, black, before_idat=((b"tRNS", b"\0\0\0\0\0\0"),)),
                b"declares transparency",
            ),
            (
                "trailing-deflate-stream",
                png_bytes(10, 10, black, compressed_suffix=zlib.compress(b"")),
                b"unexpected decoded byte count",
            ),
        )
        for name, malformed, fragment in malformed_fixtures:
            left, right, receipt = pair(root, name, baseline, malformed)
            expect_failure(name, left, right, receipt, fragment=fragment)

        mismatched = png_bytes(11, 10, bytes(11 * 10 * 3))
        left, right, receipt = pair(root, "dimension-mismatch", baseline, mismatched)
        expect_failure(
            "dimension-mismatch",
            left,
            right,
            receipt,
            fragment=b"dimensions differ",
        )

        left, right, receipt = pair(root, "inventory-extra", baseline, baseline)
        (right / "page-2.png").write_bytes(baseline)
        expect_failure(
            "inventory-extra",
            left,
            right,
            receipt,
            fragment=b"page inventory differs",
        )

        left, right, receipt = pair(root, "inventory-padding", baseline, baseline)
        (right / "page-1.png").rename(right / "page-01.png")
        expect_failure(
            "inventory-padding",
            left,
            right,
            receipt,
            fragment=b"page inventory differs",
        )

        left, right, receipt = pair(root, "unsafe-label", baseline, baseline)
        expect_failure(
            "unsafe-label",
            left,
            right,
            receipt,
            label="safe\tinjected",
            fragment=b"label must be",
        )

        for name, option, value, code, fragment in (
            ("nonfinite-threshold", "--max-mean-abs", "nan", 2, b"finite decimal"),
            ("negative-threshold", "--max-mean-abs", "-0.1", 1, b"must be in"),
            ("mean-domain", "--max-mean-abs", "255.1", 1, b"must be in"),
            (
                "changed-domain",
                "--max-changed-fraction",
                "1.0001",
                1,
                b"must be in",
            ),
            ("large-domain", "--max-large-fraction", "1.0001", 1, b"must be in"),
        ):
            case_receipt = receipt.with_name(f"{name}.tsv")
            expect_failure(
                name,
                left,
                right,
                case_receipt,
                fragment=fragment,
                extra=(option, value),
                returncode=code,
            )

        left, right, _ = pair(root, "receipt-symlink", baseline, baseline)
        sentinel = root / "receipt-symlink-target.txt"
        sentinel.write_bytes(b"do not overwrite\n")
        linked_receipt = left.parent / "receipt.tsv"
        linked_receipt.symlink_to(sentinel)
        expect_failure(
            "receipt-symlink",
            left,
            right,
            linked_receipt,
            fragment=b"receipt destination is not a single-link regular file",
            receipt_may_exist=True,
        )
        require(linked_receipt.is_symlink(), "receipt symlink was replaced")
        require(
            sentinel.read_bytes() == b"do not overwrite\n",
            "receipt symlink target changed",
        )


def main() -> int:
    try:
        run()
    except (OSError, SelfTestError, subprocess.SubprocessError) as error:
        print(f"formal PDF render comparator self-test: {error}", file=sys.stderr)
        return 1
    print(
        f"OK: formal PDF render comparator passed {len(CASES)} deterministic adversarial cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
