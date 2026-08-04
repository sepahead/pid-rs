#!/usr/bin/env python3
"""Compare two Poppler PNG page sets under an explicit per-page pixel contract."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import os
from pathlib import Path
import re
import stat
import struct
import sys
import tempfile
from typing import NoReturn
import zlib


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
DECIMAL_ARGUMENT = re.compile(r"-?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)")
MAX_PAGES = 10_000
MAX_PNG_BYTES = 256 * 1024 * 1024
MAX_DECODED_BYTES = 128 * 1024 * 1024


def fail(detail: str) -> NoReturn:
    print(f"formal PDF render comparison: {detail}", file=sys.stderr)
    raise SystemExit(1)


def decimal_argument(raw: str) -> Fraction:
    if len(raw) > 128 or DECIMAL_ARGUMENT.fullmatch(raw) is None:
        raise argparse.ArgumentTypeError(
            "must be a finite decimal without exponent notation"
        )
    return Fraction(raw)


def canonical_decimal(value: Fraction) -> str:
    """Render a finite-decimal fraction without exponent or redundant zeroes."""
    sign = "-" if value < 0 else ""
    numerator = abs(value.numerator)
    denominator = value.denominator
    if denominator == 1:
        return f"{sign}{numerator}"
    twos = 0
    fives = 0
    remainder = denominator
    while remainder % 2 == 0:
        remainder //= 2
        twos += 1
    while remainder % 5 == 0:
        remainder //= 5
        fives += 1
    if remainder != 1:
        fail("internal threshold is not a finite decimal")
    places = max(twos, fives)
    scale = 10**places
    scaled = numerator * (scale // denominator)
    whole, fractional = divmod(scaled, scale)
    digits = f"{fractional:0{places}d}".rstrip("0")
    if not digits:
        return f"{sign}{whole}"
    return f"{sign}{whole}.{digits}"


def format_ratio(numerator: int, denominator: int) -> str:
    """Round a nonnegative exact ratio to nine places, ties to even."""
    scale = 1_000_000_000
    rounded, remainder = divmod(numerator * scale, denominator)
    doubled = remainder * 2
    if doubled > denominator or (doubled == denominator and rounded % 2 == 1):
        rounded += 1
    whole, fractional = divmod(rounded, scale)
    return f"{whole}.{fractional:09d}"


def ratio_exceeds(numerator: int, denominator: int, maximum: Fraction) -> bool:
    return numerator * maximum.denominator > maximum.numerator * denominator


def validate_receipt_destination(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as error:
        fail(f"cannot inspect receipt {path}: {error}")
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        fail(f"receipt destination is not a single-link regular file: {path}")


def write_receipt(path: Path, data: bytes) -> None:
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        fail(f"receipt parent is not a real directory: {parent}")
    validate_receipt_destination(path)
    temporary: Path | None = None
    try:
        descriptor, raw_temporary = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=parent
        )
        temporary = Path(raw_temporary)
        try:
            os.fchmod(descriptor, 0o644)
            view = memoryview(data)
            while view:
                written = os.write(descriptor, view)
                if written <= 0:
                    raise OSError("short receipt write")
                view = view[written:]
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_nlink != 1
                or metadata.st_size != len(data)
            ):
                fail("temporary receipt identity or size is invalid")
        finally:
            os.close(descriptor)
        # A replacement never follows a leaf symlink; this second check also makes a symlink
        # substitution before publication a reported failure instead of silently replacing it.
        validate_receipt_destination(path)
        os.replace(temporary, path)
        temporary = None
    except OSError as error:
        fail(f"cannot write receipt {path}: {error}")
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def paeth(left: int, up: int, upper_left: int) -> int:
    candidate = left + up - upper_left
    left_distance = abs(candidate - left)
    up_distance = abs(candidate - up)
    corner_distance = abs(candidate - upper_left)
    if left_distance <= up_distance and left_distance <= corner_distance:
        return left
    if up_distance <= corner_distance:
        return up
    return upper_left


def decode_png(path: Path) -> tuple[int, int, bytes, int, str]:
    try:
        data = path.read_bytes()
    except OSError as error:
        fail(f"cannot read {path}: {error}")
    if len(data) > MAX_PNG_BYTES:
        fail(f"{path} exceeds the PNG byte bound")
    if not data.startswith(PNG_SIGNATURE):
        fail(f"{path} is not a PNG")
    offset = len(PNG_SIGNATURE)
    idat = bytearray()
    width = height = bit_depth = color_type = interlace = None
    saw_idat = False
    saw_iend = False
    saw_plte = False
    ended_idat = False
    chunk_index = 0
    while offset < len(data):
        if offset + 12 > len(data):
            fail(f"{path} has a truncated chunk")
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        if not all(
            ord("A") <= value <= ord("Z") or ord("a") <= value <= ord("z")
            for value in kind
        ):
            fail(f"{path} has an invalid PNG chunk name")
        if not ord("A") <= kind[2] <= ord("Z"):
            fail(f"{path} sets the PNG reserved chunk-name bit")
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            fail(f"{path} has a truncated chunk payload")
        payload = data[payload_start:payload_end]
        observed_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        expected_crc = zlib.crc32(kind)
        expected_crc = zlib.crc32(payload, expected_crc) & 0xFFFFFFFF
        if observed_crc != expected_crc:
            fail(f"{path} has a bad {kind!r} CRC")
        if chunk_index == 0 and kind != b"IHDR":
            fail(f"{path} does not begin with IHDR")
        if kind == b"IHDR":
            if width is not None or length != 13:
                fail(f"{path} has a duplicate or malformed IHDR")
            width, height, bit_depth, color_type, compression, filtering, interlace = (
                struct.unpack(">IIBBBBB", payload)
            )
            if width == 0 or height == 0 or width > 0x7FFFFFFF or height > 0x7FFFFFFF:
                fail(f"{path} has invalid PNG dimensions")
            if compression != 0 or filtering != 0:
                fail(f"{path} uses an unsupported PNG codec")
            if bit_depth != 8 or interlace != 0 or color_type not in {0, 2}:
                fail(f"{path} is not an opaque, non-interlaced 8-bit gray/RGB PNG")
        elif kind == b"PLTE":
            if (
                saw_plte
                or saw_idat
                or color_type == 0
                or length == 0
                or length > 768
                or length % 3
            ):
                fail(f"{path} has a misplaced or malformed PLTE")
            saw_plte = True
        elif kind == b"IDAT":
            if ended_idat:
                fail(f"{path} has nonconsecutive IDAT chunks")
            saw_idat = True
            idat.extend(payload)
        elif kind == b"IEND":
            if length != 0 or not saw_idat or crc_end != len(data):
                fail(f"{path} has a malformed IEND or trailing bytes")
            saw_iend = True
            break
        else:
            if kind == b"tRNS":
                fail(f"{path} declares transparency")
            if kind[0] & 0x20 == 0:
                fail(f"{path} has unsupported critical chunk {kind!r}")
            if saw_idat:
                ended_idat = True
        offset = crc_end
        chunk_index += 1
    if not saw_iend or None in (width, height, bit_depth, color_type, interlace):
        fail(f"{path} lacks a complete PNG envelope")
    channels = 1 if color_type == 0 else 3
    stride = width * channels
    expected_decoded = height * (stride + 1)
    if expected_decoded > MAX_DECODED_BYTES or width * height * 3 > MAX_DECODED_BYTES:
        fail(f"{path} exceeds the decoded-pixel byte bound")
    decompressor = zlib.decompressobj()
    try:
        raw = decompressor.decompress(bytes(idat), expected_decoded + 1)
    except zlib.error as error:
        fail(f"{path} has invalid compressed pixels: {error}")
    if (
        len(raw) != expected_decoded
        or not decompressor.eof
        or decompressor.unconsumed_tail
        or decompressor.unused_data
    ):
        fail(f"{path} has an unexpected decoded byte count")
    previous = bytearray(stride)
    rgb = bytearray(width * height * 3)
    source_offset = 0
    target_offset = 0
    for _ in range(height):
        filter_type = raw[source_offset]
        scan = raw[source_offset + 1 : source_offset + 1 + stride]
        source_offset += stride + 1
        reconstructed = bytearray(stride)
        for index, value in enumerate(scan):
            left = reconstructed[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 0:
                prediction = 0
            elif filter_type == 1:
                prediction = left
            elif filter_type == 2:
                prediction = up
            elif filter_type == 3:
                prediction = (left + up) // 2
            elif filter_type == 4:
                prediction = paeth(left, up, upper_left)
            else:
                fail(f"{path} uses unsupported PNG filter {filter_type}")
            reconstructed[index] = (value + prediction) & 0xFF
        if channels == 3:
            rgb[target_offset : target_offset + width * 3] = reconstructed
        else:
            for value in reconstructed:
                rgb[target_offset : target_offset + 3] = bytes((value, value, value))
                target_offset += 3
            previous = reconstructed
            continue
        target_offset += width * 3
        previous = reconstructed
    return width, height, bytes(rgb), len(data), hashlib.sha256(data).hexdigest()


def inventory(directory: Path, expected_pages: int) -> list[Path]:
    if directory.is_symlink() or not directory.is_dir():
        fail(f"render directory is not a real directory: {directory}")
    digits = len(str(expected_pages))
    expected_names = [
        f"page-{page:0{digits}d}.png" for page in range(1, expected_pages + 1)
    ]
    try:
        entries = list(directory.iterdir())
    except OSError as error:
        fail(f"cannot inventory {directory}: {error}")
    by_name = {path.name: path for path in entries}
    observed_names = sorted(by_name)
    if observed_names != sorted(expected_names):
        fail(f"page inventory differs in {directory}: {observed_names!r}")
    paths = [by_name[name] for name in expected_names]
    for path in paths:
        if path.is_symlink() or not path.is_file():
            fail(f"page is not a real regular file: {path}")
    return paths


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left-dir", type=Path, required=True)
    parser.add_argument("--right-dir", type=Path, required=True)
    parser.add_argument("--pages", type=int, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--large-delta", type=int, default=24)
    parser.add_argument("--max-mean-abs", type=decimal_argument, default=Fraction(1, 5))
    parser.add_argument(
        "--max-changed-fraction", type=decimal_argument, default=Fraction(1, 100)
    )
    parser.add_argument(
        "--max-large-fraction", type=decimal_argument, default=Fraction(1, 1000)
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    if not 1 <= arguments.pages <= MAX_PAGES:
        fail(f"page count must be in [1,{MAX_PAGES}]")
    if not 0 <= arguments.large_delta <= 255:
        fail("large-delta threshold is outside [0,255]")
    for value, name, maximum in (
        (arguments.max_mean_abs, "max-mean-abs", Fraction(255)),
        (arguments.max_changed_fraction, "max-changed-fraction", Fraction(1)),
        (arguments.max_large_fraction, "max-large-fraction", Fraction(1)),
    ):
        if not 0 <= value <= maximum:
            fail(f"{name} must be in [0,{maximum}]")
    if (
        not arguments.label
        or len(arguments.label) > 128
        or arguments.label != arguments.label.strip()
        or any(not 0x20 <= ord(character) <= 0x7E for character in arguments.label)
    ):
        fail(
            "label must be 1-128 printable ASCII characters without surrounding whitespace"
        )
    left_paths = inventory(arguments.left_dir, arguments.pages)
    right_paths = inventory(arguments.right_dir, arguments.pages)
    rows = [
        "schema\tpid-rs-formal-render-comparison-v2\n",
        f"label\t{arguments.label}\n",
        f"pages\t{arguments.pages}\n",
        f"large_delta\t{arguments.large_delta}\n",
        f"max_mean_abs\t{canonical_decimal(arguments.max_mean_abs)}\n",
        f"max_changed_fraction\t{canonical_decimal(arguments.max_changed_fraction)}\n",
        f"max_large_fraction\t{canonical_decimal(arguments.max_large_fraction)}\n",
        "page\twidth\theight\tmean_abs\tchanged_pixels\tchanged_fraction\tlarge_pixels\tlarge_fraction\tmax_abs\tleft_bytes\tleft_sha256\tright_bytes\tright_sha256\n",
    ]
    for page, (left_path, right_path) in enumerate(
        zip(left_paths, right_paths, strict=True), start=1
    ):
        left_width, left_height, left_rgb, left_bytes, left_digest = decode_png(
            left_path
        )
        right_width, right_height, right_rgb, right_bytes, right_digest = decode_png(
            right_path
        )
        if (left_width, left_height) != (right_width, right_height):
            fail(f"{arguments.label} page {page} dimensions differ")
        pixels = left_width * left_height
        absolute_sum = 0
        changed_pixels = 0
        large_pixels = 0
        maximum = 0
        for offset in range(0, len(left_rgb), 3):
            channel_differences = tuple(
                abs(left_rgb[offset + channel] - right_rgb[offset + channel])
                for channel in range(3)
            )
            pixel_maximum = max(channel_differences)
            absolute_sum += sum(channel_differences)
            maximum = max(maximum, pixel_maximum)
            if pixel_maximum != 0:
                changed_pixels += 1
            if pixel_maximum > arguments.large_delta:
                large_pixels += 1
        mean_absolute = format_ratio(absolute_sum, pixels * 3)
        changed_fraction = format_ratio(changed_pixels, pixels)
        large_fraction = format_ratio(large_pixels, pixels)
        if (
            ratio_exceeds(absolute_sum, pixels * 3, arguments.max_mean_abs)
            or ratio_exceeds(changed_pixels, pixels, arguments.max_changed_fraction)
            or ratio_exceeds(large_pixels, pixels, arguments.max_large_fraction)
        ):
            fail(
                f"{arguments.label} page {page} exceeds its visual bound: "
                f"mean={mean_absolute}, changed={changed_fraction}, "
                f"large={large_fraction}, max={maximum}"
            )
        rows.append(
            f"{page}\t{left_width}\t{left_height}\t{mean_absolute}\t"
            f"{changed_pixels}\t{changed_fraction}\t{large_pixels}\t"
            f"{large_fraction}\t{maximum}\t{left_bytes}\t{left_digest}\t"
            f"{right_bytes}\t{right_digest}\n"
        )
    write_receipt(arguments.receipt, "".join(rows).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
