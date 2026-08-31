#!/usr/bin/env python3
"""Regenerate seven publication figure PDFs with an exact open-font set.

This is a candidate-generation tool, not a canonical refresh command.  It
requires a new output directory outside the repository, renders every SVG
twice with independent Fontconfig state, and publishes only byte-identical
results.  It never invokes Pandoc and has no mode that overwrites the tracked
figure PDFs.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import NoReturn
from xml.sax.saxutils import escape as xml_escape

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject


CHECK_NAME = "publication open-font figure regeneration"
SOURCE_DATE_EPOCH = "1787875200"
MAX_FONT_BYTES = 16 * 1024 * 1024
MAX_PDF_BYTES = 1024 * 1024

FONT_SPECS = (
    {
        "filename": "SourceSansPro-Regular.otf",
        "relative": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Regular.otf",
        "sha256": "7134d229b15cdd0827376d8a24f6f531f616eb1b3fecd16e1cf8a86d0bf6bc51",
        "root": "texmf-dist",
        "postscript": "SourceSansPro-Regular",
        "query": "Source Sans Pro:style=Regular",
        "provenance": "Source Sans Pro 3.006R",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "SourceSansPro-Semibold.otf",
        "relative": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Semibold.otf",
        "sha256": "aa53ed4fc17334a0c2ee8412c1e4e728bfb732a96b119164f7354343dad8f2f2",
        "root": "texmf-dist",
        "postscript": "SourceSansPro-Semibold",
        "query": "Source Sans Pro:style=Semibold",
        "provenance": "Source Sans Pro 3.006R",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "SourceSansPro-Bold.otf",
        "relative": "fonts/opentype/adobe/sourcesanspro/SourceSansPro-Bold.otf",
        "sha256": "daccddbe3dd60fe10f6e8a785eda187925da6b611141024dffa43626998dfc7c",
        "root": "texmf-dist",
        "postscript": "SourceSansPro-Bold",
        "query": "Source Sans Pro:style=Bold",
        "provenance": "Source Sans Pro 3.006R",
        "license_identifier": "OFL-1.1",
    },
    {
        "filename": "lmsans10-regular.otf",
        "relative": "fonts/opentype/public/lm/lmsans10-regular.otf",
        "sha256": "d431b786b9b603662718e79cfe9b441f47a8b0b3e854dde89d5acb3ed7cfd682",
        "root": "texmf-dist-or-debian",
        "postscript": "LMSans10-Regular",
        "query": "Latin Modern Sans:style=Regular",
        "provenance": "installed Latin Modern 2.004 program",
        "license_identifier": "LicenseRef-GUST-Font-License-1.0",
    },
    {
        "filename": "lmsans10-bold.otf",
        "relative": "fonts/opentype/public/lm/lmsans10-bold.otf",
        "sha256": "a597b710326c1a8a2c7238d808e5d38711638a72a32383478db4829d63afd687",
        "root": "texmf-dist-or-debian",
        "postscript": "LMSans10-Bold",
        "query": "Latin Modern Sans:style=Bold",
        "provenance": "installed Latin Modern 2.004 program",
        "license_identifier": "LicenseRef-GUST-Font-License-1.0",
    },
)

FIGURE_SPECS = (
    {
        "source": "audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg",
        "source_sha256": "e79ef4f3290f094efc1f786977800f4d4bd8a101760f57ed528c988d6d621042",
        "output": "semantic-firewall.pdf",
        "font_programs": {
            "SourceSansPro-Regular",
            "SourceSansPro-Semibold",
            "SourceSansPro-Bold",
        },
        "css_family": 'font-family: "Source Sans Pro";',
        "css_weights": {400, 600, 700},
    },
    {
        "source": "audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg",
        "source_sha256": "34a4225a4fda9d7cdfcb8c4b72839e1394445d382c036f5f1ae0163a759c38f7",
        "output": "result-evidence-map.pdf",
        "font_programs": {
            "SourceSansPro-Semibold",
            "SourceSansPro-Bold",
        },
        "css_family": 'font-family: "Source Sans Pro";',
        "css_weights": {600, 700},
    },
    {
        "source": "audit/formal/latex/figures/mathematical-results-guide/common-radius-small-ball-bridge.svg",
        "source_sha256": "db7c44960fdbad22586e9fbb793deb1944991ff155ceeb13efb9e86774e7a388",
        "output": "common-radius-small-ball-bridge.pdf",
        "font_programs": {
            "SourceSansPro-Regular",
            "SourceSansPro-Semibold",
            "SourceSansPro-Bold",
        },
        "css_family": 'font-family: "Source Sans Pro";',
        "css_weights": {400, 600, 700},
    },
    {
        "source": "audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg",
        "source_sha256": "5619f118cf53a11f16524c906f1d4542e22ebea685161998aade8acc5bae469a",
        "output": "audit-coordinate-crosswalk.pdf",
        "font_programs": {"LMSans10-Regular", "LMSans10-Bold"},
        "css_family": "'Latin Modern Sans'",
        "css_weights": {400, 700},
    },
    {
        "source": "audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.svg",
        "source_sha256": "a4c22c813275b1db3c554cc58ed82566dffe12594ef3b15660ccf0e1032ea061",
        "output": "source-cylinder-factorization.pdf",
        "font_programs": {"LMSans10-Regular", "LMSans10-Bold"},
        "css_family": "'Latin Modern Sans'",
        "css_weights": {400, 700},
    },
    {
        "source": "audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg",
        "source_sha256": "4226063f230341e0f3287ba8217fde62ddb5e9838cd84072d3578cf99531bd36",
        "output": "quantizer-cardinality.pdf",
        "font_programs": {
            "SourceSansPro-Regular",
            "SourceSansPro-Semibold",
            "SourceSansPro-Bold",
            "LMSans10-Regular",
        },
        "css_family": 'font-family: "Source Sans Pro";',
        "css_weights": {400, 600, 700},
    },
    {
        "source": "audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.svg",
        "source_sha256": "142ff6540f13be02d88a5db09d0f909aac3fa43e653f0d956a093802d0e1d217",
        "output": "represented-sum-boundary.pdf",
        "font_programs": {
            "SourceSansPro-Regular",
            "SourceSansPro-Semibold",
            "SourceSansPro-Bold",
            "LMSans10-Regular",
        },
        "css_family": 'font-family: "Source Sans Pro";',
        "css_weights": {400, 600, 700},
    },
)

LICENSE_ARTIFACT_SPECS = (
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "source-sans-pro-ofl-1.1-tex-live-2024.txt"
        ),
        "bytes": 4529,
        "sha256": "4a4a4179a96b5ef6786186d199f0d049b151352f460b8d2f3c00083792f37dd9",
        "role": (
            "Exact installed TeX Live 2024 Source Sans Pro package license evidence; "
            "its generic 2010/2012 header does not replace the accepted OTF programs' "
            "2010-2019 metadata."
        ),
    },
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "gust-font-license-1.0-tex-live-2024.txt"
        ),
        "bytes": 1377,
        "sha256": "49ea6cb9257bbee0a3979c48a774cd221550ac1c20c95549efe45fc99cc18050",
        "role": "Exact installed TeX Live 2024 GUST Font License 1.0 evidence.",
    },
    {
        "path": (
            "audit/formal/latex/mathematical-results-guide/font-licenses/"
            "manifest-latin-modern-2.004-tex-live-2024.txt"
        ),
        "bytes": 52635,
        "sha256": "402c79f4ede8548a6fe6f82f42f0288cb0243ba2403dfdeeaadf55d189a46fae",
        "role": (
            "Exact installed TeX Live 2024 Latin Modern v2.004 package manifest "
            "evidence; this is distinct from the GUST license text."
        ),
    },
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


def fail(detail: str) -> NoReturn:
    raise SystemExit(f"{CHECK_NAME} failed: {detail}")


def identity(status: os.stat_result) -> tuple[int, ...]:
    return tuple(int(getattr(status, field)) for field in STABLE_FIELDS)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_absolute_canonical(raw: str, label: str, *, must_exist: bool) -> Path:
    if not raw or "\n" in raw or "\r" in raw:
        fail(f"{label} is empty or contains a line break")
    candidate = Path(raw)
    if not candidate.is_absolute() or os.path.normpath(raw) != raw:
        fail(f"{label} is not an exact canonical absolute path: {raw!r}")
    try:
        resolved = candidate.resolve(strict=must_exist)
    except OSError as error:
        fail(f"cannot resolve {label}: {error}")
    if resolved != candidate:
        fail(f"{label} contains a symbolic or non-canonical component: {raw}")
    return candidate


def open_directory_chain(path: Path) -> tuple[int, tuple[tuple[int, int, int], ...]]:
    required = ("O_CLOEXEC", "O_DIRECTORY", "O_NOFOLLOW", "O_NONBLOCK")
    missing = [name for name in required if not hasattr(os, name)]
    if missing:
        fail(f"platform lacks required no-follow descriptor flags: {missing}")
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    chain: list[tuple[int, int, int]] = []
    try:
        root_status = os.fstat(descriptor)
        chain.append((root_status.st_dev, root_status.st_ino, root_status.st_mode))
        for component in path.parts[1:]:
            try:
                child = os.open(component, flags, dir_fd=descriptor)
            except OSError as error:
                fail(f"cannot open direct directory component {component!r} in {path}: {error}")
            os.close(descriptor)
            descriptor = child
            status = os.fstat(descriptor)
            chain.append((status.st_dev, status.st_ino, status.st_mode))
        return descriptor, tuple(chain)
    except BaseException:
        os.close(descriptor)
        raise


def read_beneath(root: Path, relative_raw: str, label: str, maximum: int) -> bytes:
    relative = Path(relative_raw)
    if relative.is_absolute() or not relative.parts or any(
        part in ("", ".", "..") for part in relative.parts
    ):
        fail(f"internal path is not canonical for {label}: {relative_raw!r}")
    root_fd, root_chain_before = open_directory_chain(root)
    parent_fd = os.dup(root_fd)
    file_fd = -1
    directory_chain: list[tuple[int, int, int]] = []
    try:
        for component in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
            try:
                child = os.open(component, flags, dir_fd=parent_fd)
            except OSError as error:
                fail(f"cannot open direct path component {component!r} for {label}: {error}")
            os.close(parent_fd)
            parent_fd = child
            status = os.fstat(parent_fd)
            directory_chain.append((status.st_dev, status.st_ino, status.st_mode))
        leaf = relative.parts[-1]
        try:
            before_name = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        except OSError as error:
            fail(f"cannot stat {label}: {error}")
        if not stat.S_ISREG(before_name.st_mode):
            fail(f"{label} is not a direct regular file")
        flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK
        try:
            file_fd = os.open(leaf, flags, dir_fd=parent_fd)
        except OSError as error:
            fail(f"cannot open direct regular file for {label}: {error}")
        before = os.fstat(file_fd)
        if not stat.S_ISREG(before.st_mode):
            fail(f"{label} is not a direct regular file")
        if (before_name.st_dev, before_name.st_ino) != (before.st_dev, before.st_ino):
            fail(f"{label} changed during descriptor open")
        if before.st_size < 1 or before.st_size > maximum:
            fail(f"{label} size is outside 1..{maximum} bytes: {before.st_size}")
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(file_fd, min(1024 * 1024, remaining))
            if not chunk:
                fail(f"{label} became short during descriptor read")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(file_fd, 1):
            fail(f"{label} grew during descriptor read")
        after = os.fstat(file_fd)
        after_name = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        if identity(before_name) != identity(before) or identity(before) != identity(after):
            fail(f"{label} changed during descriptor read")
        if identity(after_name) != identity(after):
            fail(f"{label} namespace changed during descriptor read")
        data = b"".join(chunks)
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)
        os.close(root_fd)

    root_fd, root_chain_after = open_directory_chain(root)
    parent_fd = os.dup(root_fd)
    file_fd = -1
    final_directory_chain: list[tuple[int, int, int]] = []
    try:
        for component in relative.parts[:-1]:
            flags = os.O_RDONLY | os.O_CLOEXEC | os.O_DIRECTORY | os.O_NOFOLLOW
            child = os.open(component, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child
            status = os.fstat(parent_fd)
            final_directory_chain.append((status.st_dev, status.st_ino, status.st_mode))
        leaf = relative.parts[-1]
        final_name = os.stat(leaf, dir_fd=parent_fd, follow_symlinks=False)
        file_fd = os.open(
            leaf,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=parent_fd,
        )
        final_status = os.fstat(file_fd)
        if (
            root_chain_before != root_chain_after
            or tuple(directory_chain) != tuple(final_directory_chain)
            or identity(final_name) != identity(after)
            or identity(final_status) != identity(after)
        ):
            fail(f"{label} path changed across descriptor capture")
    except OSError as error:
        fail(f"cannot revalidate {label}: {error}")
    finally:
        if file_fd >= 0:
            os.close(file_fd)
        os.close(parent_fd)
        os.close(root_fd)
    return data


def write_exclusive(path: Path, data: bytes, mode: int = 0o600) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC | os.O_NOFOLLOW
    descriptor = os.open(path, flags, mode)
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size != 0:
            fail(f"new output is not a single-link empty regular file: {path}")
        offset = 0
        while offset < len(data):
            written = os.write(descriptor, data[offset:])
            if written <= 0:
                fail(f"write made no progress for {path}")
            offset += written
        os.fsync(descriptor)
        after = os.fstat(descriptor)
        named = os.stat(path, follow_symlinks=False)
        if after.st_nlink != 1 or after.st_size != len(data) or identity(named) != identity(after):
            fail(f"new output changed during publication: {path}")
    finally:
        os.close(descriptor)


def read_direct(path: Path, label: str, maximum: int) -> bytes:
    parent = path.parent
    return read_beneath(parent, path.name, label, maximum)


def resolve_tool(raw: str, label: str) -> Path:
    selected = raw if "/" in raw else shutil.which(raw)
    if not selected:
        fail(f"required tool is unavailable: {label}")
    candidate = Path(selected).resolve(strict=True)
    try:
        status = candidate.stat()
    except OSError as error:
        fail(f"cannot stat {label}: {error}")
    if not stat.S_ISREG(status.st_mode) or not os.access(candidate, os.X_OK):
        fail(f"{label} is not an executable regular file: {candidate}")
    return candidate


def run_tool(command: list[str], environment: dict[str, str], label: str) -> subprocess.CompletedProcess[bytes]:
    try:
        result = subprocess.run(
            command,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        fail(f"{label} could not run: {error}")
    if result.returncode != 0:
        diagnostic = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        fail(f"{label} exited {result.returncode}: {diagnostic[:500]}")
    return result


def validate_svg_css(spec: dict[str, object], data: bytes) -> None:
    label = str(spec["source"])
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"{label} is not UTF-8: {error}")
    family = str(spec["css_family"])
    if family not in text:
        fail(f"{label} lacks its exact open-font CSS family")
    forbidden = ("Source Sans 3", "Helvetica", "Arial", "sans-serif")
    if any(token in text for token in forbidden):
        fail(f"{label} retains a fallback or non-admitted font family")
    if "Source Sans Pro" in family:
        weights = {int(value) for value in re.findall(r"font-weight:\s*([0-9]+)", text)}
    else:
        weights = {int(value) for value in re.findall(r"font:\s*([0-9]+)\s", text)}
    if weights != spec["css_weights"]:
        fail(f"{label} CSS weights changed: {sorted(weights)}")


def capture_fonts(
    texmf_dist: Path, texmf_debian: Path | None, destination: Path
) -> tuple[list[dict[str, str]], dict[str, bytes]]:
    receipt: list[dict[str, str]] = []
    captured: dict[str, bytes] = {}
    for spec in FONT_SPECS:
        roots: list[tuple[str, Path]] = [("texmf-dist", texmf_dist)]
        if spec["root"] == "texmf-dist-or-debian" and texmf_debian is not None:
            roots.append(("texmf-debian", texmf_debian))
        selected: tuple[str, Path, bytes] | None = None
        for root_name, root in roots:
            candidate = root / str(spec["relative"])
            try:
                os.lstat(candidate)
            except FileNotFoundError:
                continue
            except OSError as error:
                fail(f"cannot inspect font candidate {candidate}: {error}")
            data = read_beneath(
                root,
                str(spec["relative"]),
                f"font {spec['filename']} from {root_name}",
                MAX_FONT_BYTES,
            )
            observed = sha256(data)
            if observed != spec["sha256"]:
                fail(
                    f"font hash mismatch for {spec['filename']} from {root_name}: {observed}"
                )
            selected = (root_name, candidate, data)
            break
        if selected is None:
            fail(f"exact font is absent at every admitted path: {spec['filename']}")
        root_name, _candidate, data = selected
        destination_path = destination / str(spec["filename"])
        write_exclusive(destination_path, data, 0o400)
        captured[str(spec["filename"])] = data
        receipt.append(
            {
                "filename": str(spec["filename"]),
                "source_root": root_name,
                "relative_path": str(spec["relative"]),
                "sha256": str(spec["sha256"]),
                "postscript_name": str(spec["postscript"]),
                "provenance": str(spec["provenance"]),
                "license_identifier": str(spec["license_identifier"]),
            }
        )
    return receipt, captured


def make_fontconfig(run_directory: Path, font_directory: Path) -> tuple[Path, bytes, dict[str, str]]:
    home = run_directory / "home"
    config_home = run_directory / "xdg-config"
    cache_home = run_directory / "xdg-cache"
    font_cache = run_directory / "font-cache"
    empty_path = run_directory / "empty-fontconfig-path"
    temp_directory = run_directory / "tmp"
    for directory in (home, config_home, cache_home, font_cache, empty_path, temp_directory):
        directory.mkdir(mode=0o700)
    config = run_directory / "fontconfig.xml"
    config_bytes = (
        '<?xml version="1.0"?>\n'
        '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
        "<fontconfig>\n"
        "  <reset-dirs/>\n"
        f"  <dir>{xml_escape(str(font_directory))}</dir>\n"
        f"  <cachedir>{xml_escape(str(font_cache))}</cachedir>\n"
        "  <config></config>\n"
        "</fontconfig>\n"
    ).encode("utf-8")
    write_exclusive(config, config_bytes)
    environment = {
        "PATH": "/usr/bin:/bin",
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(config_home),
        "XDG_CACHE_HOME": str(cache_home),
        "FONTCONFIG_FILE": str(config),
        "FONTCONFIG_PATH": str(empty_path),
        "FONTCONFIG_USE_MMAP": "0",
        # Homebrew Pango also has a CoreText backend.  Force the Fontconfig
        # backend so the five-file inventory above is the renderer's inventory.
        "PANGOCAIRO_BACKEND": "fontconfig",
        "TMPDIR": str(temp_directory),
        "SOURCE_DATE_EPOCH": SOURCE_DATE_EPOCH,
        "TZ": "UTC",
        "LANG": "C",
        "LC_ALL": "C",
    }
    return config, config_bytes, environment


def validate_immutable(path: Path, expected: bytes, label: str, maximum: int) -> None:
    try:
        status = os.lstat(path)
    except OSError as error:
        fail(f"cannot inspect {label}: {error}")
    if not stat.S_ISREG(status.st_mode) or status.st_nlink != 1:
        fail(f"{label} is not a direct single-link regular file")
    observed = read_direct(path, label, maximum)
    if observed != expected:
        fail(f"{label} changed")


def validate_fontconfig_selection(
    fc_list: Path,
    fc_match: Path,
    environment: dict[str, str],
    config_path: Path,
    config_bytes: bytes,
    font_directory: Path,
) -> None:
    validate_immutable(config_path, config_bytes, "Fontconfig configuration", 1024 * 1024)
    inventory = run_tool(
        [str(fc_list), "-f", "%{file}\t%{postscriptname}\\n"],
        environment,
        "isolated font inventory",
    )
    validate_immutable(config_path, config_bytes, "Fontconfig configuration", 1024 * 1024)
    try:
        lines = inventory.stdout.decode("utf-8").splitlines()
    except UnicodeDecodeError as error:
        fail(f"isolated font inventory is not UTF-8: {error}")
    expected_inventory = {
        f"{font_directory / str(spec['filename'])}\t{spec['postscript']}" for spec in FONT_SPECS
    }
    if set(lines) != expected_inventory or len(lines) != len(expected_inventory):
        fail(f"isolated Fontconfig inventory changed: {lines!r}")
    for spec in FONT_SPECS:
        result = run_tool(
            [
                str(fc_match),
                "-f",
                "%{file}\t%{postscriptname}\\n",
                str(spec["query"]),
            ],
            environment,
            f"font selection for {spec['postscript']}",
        )
        validate_immutable(config_path, config_bytes, "Fontconfig configuration", 1024 * 1024)
        expected = f"{font_directory / str(spec['filename'])}\t{spec['postscript']}\n".encode()
        if result.stdout != expected:
            fail(
                f"Fontconfig selected the wrong program for {spec['postscript']}: "
                f"{result.stdout.decode('utf-8', errors='replace')!r}"
            )


def dereference(value: object) -> object:
    seen: set[tuple[int, int]] = set()
    while isinstance(value, IndirectObject):
        key = (value.idnum, value.generation)
        if key in seen:
            fail(f"PDF indirect-object cycle at {key[0]} {key[1]}")
        seen.add(key)
        value = value.get_object()
    return value


def clean_font_name(value: object) -> str:
    name = str(value).lstrip("/")
    return re.sub(r"^[A-Z]{6}\+", "", name)


def require_font_stream(descriptor: DictionaryObject, label: str) -> None:
    entries = [key for key in ("/FontFile", "/FontFile2", "/FontFile3") if key in descriptor]
    if len(entries) != 1:
        fail(f"{label} does not contain exactly one embedded font program")
    stream = dereference(descriptor.raw_get(entries[0]))
    if not isinstance(stream, StreamObject):
        fail(f"{label} font program is not a stream")
    try:
        data = stream.get_data()
    except Exception as error:
        fail(f"{label} font program cannot be decoded: {error}")
    if not data:
        fail(f"{label} embedded font program is empty")


def validate_space_only_type3(font: DictionaryObject, label: str) -> None:
    """Admit Cairo's zero-outline space carrier, never a visible fallback font."""
    if str(font.get("/FirstChar")) != "0" or str(font.get("/LastChar")) != "0":
        fail(f"{label} Type3 resource is not limited to character zero")
    if [str(value) for value in font.get("/FontBBox", [])] != ["0", "0", "0", "0"]:
        fail(f"{label} Type3 resource has a nonzero FontBBox")
    char_procs = dereference(font.raw_get("/CharProcs"))
    if not isinstance(char_procs, DictionaryObject) or [str(key) for key in char_procs] != ["/0"]:
        fail(f"{label} Type3 resource has an unexpected glyph inventory")
    glyph = dereference(char_procs.raw_get("/0"))
    if not isinstance(glyph, StreamObject):
        fail(f"{label} Type3 space glyph is not a stream")
    try:
        glyph_data = glyph.get_data()
    except Exception as error:
        fail(f"{label} Type3 space glyph cannot be decoded: {error}")
    # Cairo emits only a d1 metrics operator for its zero-outline space carrier.
    if not re.fullmatch(rb"\s*[-+0-9. ]+d1\s*", glyph_data):
        fail(f"{label} Type3 resource contains a visible or unrecognized glyph program")
    to_unicode = dereference(font.raw_get("/ToUnicode"))
    if not isinstance(to_unicode, StreamObject):
        fail(f"{label} Type3 resource lacks a ToUnicode stream")
    try:
        unicode_data = to_unicode.get_data()
    except Exception as error:
        fail(f"{label} Type3 ToUnicode cannot be decoded: {error}")
    mappings = re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", unicode_data)
    if mappings != [(b"00", b"ff"), (b"00", b"0020")]:
        fail(f"{label} Type3 resource does not map only character zero to U+0020")


def inspect_pdf(data: bytes, output_name: str, expected_fonts: set[str]) -> list[str]:
    if len(data) < 1 or len(data) > MAX_PDF_BYTES or not data.startswith(b"%PDF-"):
        fail(f"{output_name} is outside the PDF byte/header contract")
    try:
        reader = PdfReader(io.BytesIO(data), strict=True)
    except Exception as error:
        fail(f"{output_name} is not a strict readable PDF: {error}")
    if reader.is_encrypted or len(reader.pages) != 1:
        fail(f"{output_name} must be one unencrypted page")
    page = reader.pages[0]
    if page.get("/Annots") is not None:
        fail(f"{output_name} unexpectedly contains annotations")
    media_box = page.mediabox
    if float(media_box.width) <= 0 or float(media_box.height) <= 0:
        fail(f"{output_name} has a non-positive MediaBox")
    resources = dereference(page.raw_get("/Resources"))
    if not isinstance(resources, DictionaryObject):
        fail(f"{output_name} lacks a resource dictionary")
    fonts = dereference(resources.raw_get("/Font"))
    if not isinstance(fonts, DictionaryObject) or not fonts:
        fail(f"{output_name} lacks font resources")
    observed: list[str] = []
    for resource_name in sorted(fonts.keys(), key=str):
        font = dereference(fonts.raw_get(resource_name))
        if not isinstance(font, DictionaryObject) or str(font.get("/Type")) != "/Font":
            fail(f"{output_name} font {resource_name} is malformed")
        if "/ToUnicode" not in font:
            fail(f"{output_name} font {resource_name} lacks ToUnicode")
        subtype = str(font.get("/Subtype"))
        if subtype == "/Type3":
            validate_space_only_type3(font, f"{output_name} font {resource_name}")
            continue
        if subtype == "/Type0":
            descendants = dereference(font.raw_get("/DescendantFonts"))
            if not isinstance(descendants, ArrayObject) or len(descendants) != 1:
                fail(f"{output_name} font {resource_name} has invalid descendants")
            concrete = dereference(list.__getitem__(descendants, 0))
        elif subtype in ("/TrueType", "/Type1"):
            concrete = font
        else:
            fail(f"{output_name} font {resource_name} uses unsupported subtype {subtype}")
        if not isinstance(concrete, DictionaryObject):
            fail(f"{output_name} font {resource_name} has no concrete font dictionary")
        descriptor = dereference(concrete.raw_get("/FontDescriptor"))
        if not isinstance(descriptor, DictionaryObject):
            fail(f"{output_name} font {resource_name} lacks a descriptor")
        font_name = clean_font_name(descriptor.get("/FontName"))
        base_name = clean_font_name(font.get("/BaseFont"))
        if font_name != base_name:
            fail(
                f"{output_name} font {resource_name} BaseFont/FontName disagree: "
                f"{base_name!r} versus {font_name!r}"
            )
        require_font_stream(descriptor, f"{output_name} font {resource_name}")
        observed.append(font_name)
    if set(observed) != expected_fonts:
        fail(f"{output_name} embedded font programs changed: {sorted(set(observed))}")
    # Cairo may create more than one subset resource from the same exact source
    # program for separate text runs.  The program-name set, not resource count,
    # is the relevant no-fallback boundary here.
    return sorted(set(observed))


def validate_output_request(raw: str, repository_root: Path) -> tuple[Path, tuple[int, int, int]]:
    output = require_absolute_canonical(raw, "output directory", must_exist=False)
    if output.exists() or output.is_symlink():
        fail(f"output directory already exists: {output}")
    parent = require_absolute_canonical(str(output.parent), "output parent", must_exist=True)
    if parent == Path("/"):
        fail("output parent must not be the filesystem root")
    if repository_root == output or repository_root in output.parents:
        fail("output directory must be outside the repository")
    parent_fd, _chain = open_directory_chain(parent)
    try:
        parent_status = os.fstat(parent_fd)
        if not stat.S_ISDIR(parent_status.st_mode):
            fail("output parent is not a directory")
        parent_identity = (
            parent_status.st_dev,
            parent_status.st_ino,
            parent_status.st_mode,
        )
    finally:
        os.close(parent_fd)
    return output, parent_identity


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate non-canonical open-font PDF candidates for seven publication SVGs."
    )
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--texmf-dist", required=True)
    parser.add_argument("--texmf-debian")
    parser.add_argument("--rsvg-convert", default="rsvg-convert")
    parser.add_argument("--fc-list", default="fc-list")
    parser.add_argument("--fc-match", default="fc-match")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    arguments = parse_arguments(argv)
    repository_root = Path(__file__).resolve(strict=True).parent.parent
    output, output_parent_identity = validate_output_request(arguments.output_dir, repository_root)
    texmf_dist = require_absolute_canonical(arguments.texmf_dist, "TEXMFDIST", must_exist=True)
    texmf_debian = (
        require_absolute_canonical(arguments.texmf_debian, "TEXMFDEBIAN", must_exist=True)
        if arguments.texmf_debian
        else None
    )
    rsvg_convert = resolve_tool(arguments.rsvg_convert, "rsvg-convert")
    fc_list = resolve_tool(arguments.fc_list, "fc-list")
    fc_match = resolve_tool(arguments.fc_match, "fc-match")

    license_artifact_bytes: dict[str, bytes] = {}
    license_artifact_receipt: list[dict[str, object]] = []
    for spec in LICENSE_ARTIFACT_SPECS:
        relative = str(spec["path"])
        data = read_beneath(
            repository_root,
            relative,
            f"font-license evidence {relative}",
            1024 * 1024,
        )
        observed = sha256(data)
        if len(data) != spec["bytes"] or observed != spec["sha256"]:
            fail(
                f"font-license evidence bytes changed for {relative}: "
                f"bytes={len(data)} sha256={observed}"
            )
        license_artifact_bytes[relative] = data
        license_artifact_receipt.append(
            {
                "path": relative,
                "bytes": int(spec["bytes"]),
                "sha256": str(spec["sha256"]),
                "role": str(spec["role"]),
            }
        )

    svg_bytes: dict[str, bytes] = {}
    for spec in FIGURE_SPECS:
        source = str(spec["source"])
        data = read_beneath(repository_root, source, f"SVG source {source}", 4 * 1024 * 1024)
        observed = sha256(data)
        if observed != spec["source_sha256"]:
            fail(f"SVG source hash changed for {source}: {observed}")
        validate_svg_css(spec, data)
        svg_bytes[source] = data

    scratch = Path(tempfile.mkdtemp(prefix=".pid-rs-mrg-open-font-", dir=output.parent))
    published = False
    try:
        font_directory = scratch / "fonts"
        source_directory = scratch / "sources"
        font_directory.mkdir(mode=0o700)
        source_directory.mkdir(mode=0o700)
        font_receipt, captured_fonts = capture_fonts(texmf_dist, texmf_debian, font_directory)
        staged_sources: dict[str, Path] = {}
        for spec in FIGURE_SPECS:
            source = str(spec["source"])
            staged = source_directory / Path(source).name
            write_exclusive(staged, svg_bytes[source], 0o400)
            staged_sources[source] = staged

        version_environment = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(scratch),
            "LANG": "C",
            "LC_ALL": "C",
            "TZ": "UTC",
        }
        version = run_tool(
            [str(rsvg_convert), "--version"], version_environment, "rsvg-convert version query"
        )
        version_text = (version.stdout + version.stderr).decode("utf-8", errors="strict").strip()
        if not version_text.startswith("rsvg-convert version "):
            fail("rsvg-convert version response is not recognized")

        rendered: list[dict[str, bytes]] = []
        rendered_fonts: dict[str, list[str]] = {}
        for run_index in (1, 2):
            run_directory = scratch / f"run-{run_index}"
            run_directory.mkdir(mode=0o700)
            output_directory = run_directory / "pdf"
            output_directory.mkdir(mode=0o700)
            config_path, config_bytes, environment = make_fontconfig(
                run_directory, font_directory
            )
            validate_fontconfig_selection(
                fc_list,
                fc_match,
                environment,
                config_path,
                config_bytes,
                font_directory,
            )
            run_outputs: dict[str, bytes] = {}
            for spec in FIGURE_SPECS:
                source = str(spec["source"])
                output_name = str(spec["output"])
                derivative = output_directory / output_name
                validate_immutable(
                    config_path, config_bytes, "Fontconfig configuration", 1024 * 1024
                )
                for font_spec in FONT_SPECS:
                    filename = str(font_spec["filename"])
                    validate_immutable(
                        font_directory / filename,
                        captured_fonts[filename],
                        f"captured font {filename}",
                        MAX_FONT_BYTES,
                    )
                result = run_tool(
                    [
                        str(rsvg_convert),
                        "--format=pdf",
                        "--keep-aspect-ratio",
                        f"--output={derivative}",
                        str(staged_sources[source]),
                    ],
                    environment,
                    f"render {output_name} pass {run_index}",
                )
                if result.stdout or result.stderr:
                    fail(f"render {output_name} pass {run_index} emitted a diagnostic")
                validate_immutable(
                    config_path, config_bytes, "Fontconfig configuration", 1024 * 1024
                )
                try:
                    derivative_status = os.lstat(derivative)
                except OSError as error:
                    fail(f"cannot inspect rendered {output_name}: {error}")
                if (
                    not stat.S_ISREG(derivative_status.st_mode)
                    or derivative_status.st_nlink != 1
                ):
                    fail(f"rendered {output_name} is not a direct single-link regular file")
                data = read_direct(derivative, output_name, MAX_PDF_BYTES)
                fonts = inspect_pdf(data, output_name, set(spec["font_programs"]))
                if run_index == 1:
                    rendered_fonts[output_name] = fonts
                elif rendered_fonts[output_name] != fonts:
                    fail(f"{output_name} font inventory changed between render passes")
                run_outputs[output_name] = data
            rendered.append(run_outputs)

        for spec in FIGURE_SPECS:
            output_name = str(spec["output"])
            if rendered[0][output_name] != rendered[1][output_name]:
                fail(f"{output_name} is not byte-reproducible across independent render passes")

        for font_spec in FONT_SPECS:
            filename = str(font_spec["filename"])
            validate_immutable(
                font_directory / filename,
                captured_fonts[filename],
                f"captured font {filename}",
                MAX_FONT_BYTES,
            )
        for spec in FIGURE_SPECS:
            source = str(spec["source"])
            validate_immutable(
                staged_sources[source], svg_bytes[source], f"captured SVG {source}", 4 * 1024 * 1024
            )
        for spec in LICENSE_ARTIFACT_SPECS:
            relative = str(spec["path"])
            observed = read_beneath(
                repository_root,
                relative,
                f"font-license evidence {relative}",
                1024 * 1024,
            )
            if observed != license_artifact_bytes[relative]:
                fail(f"font-license evidence changed during regeneration: {relative}")

        receipt = {
            "format_version": 1,
            "purpose": "Non-canonical exact-open-font SVG-to-PDF candidate regeneration",
            "source_date_epoch": int(SOURCE_DATE_EPOCH),
            "renderer": {
                "program": "rsvg-convert",
                "version_observation": version_text.splitlines(),
                "command": "rsvg-convert --format=pdf --keep-aspect-ratio --output=DERIVATIVE SOURCE",
                "pango_cairo_backend": "fontconfig",
            },
            "fonts": font_receipt,
            "license_artifacts": license_artifact_receipt,
            "font_provenance": {
                "source_sans_pro": {
                    "release": "3.006R",
                    "peeled_upstream_commit_locator": (
                        "4bdf42c690a214a0f69410d71a6b889c5c4a695f"
                    ),
                    "boundary": (
                        "The commit is a release locator and observed correspondence. The exact "
                        "accepted hashes bind the installed inputs; neither fact authenticates "
                        "their download, package, or local provenance."
                    ),
                },
                "latin_modern_sans": {
                    "installed_program_version": "2.004",
                    "boundary": (
                        "The exact accepted hashes bind installed programs identified as Latin "
                        "Modern 2.004. No upstream repository byte identity or authenticated "
                        "acquisition route is claimed."
                    ),
                },
                "raw_font_files_tracked_in_repository": False,
                "notice_file": "THIRD_PARTY_NOTICES.md",
                "notice_boundary": (
                    "Retain the applicable font copyright and license notices when a "
                    "distribution scenario requires them. The receipt does not make a legal "
                    "determination for a downstream package."
                ),
            },
            "figures": [
                {
                    "source": str(spec["source"]),
                    "source_sha256": str(spec["source_sha256"]),
                    "derivative": str(spec["output"]),
                    "derivative_sha256": sha256(rendered[0][str(spec["output"])]),
                    "pdf_bytes": len(rendered[0][str(spec["output"])]),
                    "embedded_font_programs": rendered_fonts[str(spec["output"])],
                }
                for spec in FIGURE_SPECS
            ],
            "repeatability": {
                "independent_fontconfig_states": 2,
                "raw_byte_equality": True,
            },
            "pandoc_used": False,
            "canonical_publication": False,
            "claim_boundary": (
                "This receipt proves exact inputs, isolated font selection, and two-pass raw-byte "
                "agreement for this invocation only. It does not prove cross-host reproducibility, "
                "visual equivalence, accessibility, or canonical acceptance."
            ),
        }
        receipt_bytes = (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")

        parent_fd, _chain = open_directory_chain(output.parent)
        try:
            final_parent = os.fstat(parent_fd)
            if (
                final_parent.st_dev,
                final_parent.st_ino,
                final_parent.st_mode,
            ) != output_parent_identity:
                fail("output parent changed during regeneration")
            try:
                os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                fail("output path appeared during regeneration")
            os.mkdir(output.name, mode=0o700, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        published = True
        for spec in FIGURE_SPECS:
            output_name = str(spec["output"])
            write_exclusive(output / output_name, rendered[0][output_name], 0o600)
        write_exclusive(output / "open-font-regeneration-receipt.json", receipt_bytes, 0o600)
        for spec in FIGURE_SPECS:
            output_name = str(spec["output"])
            validate_immutable(
                output / output_name, rendered[0][output_name], f"published {output_name}", MAX_PDF_BYTES
            )
        validate_immutable(
            output / "open-font-regeneration-receipt.json",
            receipt_bytes,
            "published regeneration receipt",
            1024 * 1024,
        )
    finally:
        shutil.rmtree(scratch)

    if not published:
        fail("candidate publication did not complete")
    print(f"OK: wrote seven exact-open-font candidate PDFs to {output}")
    print("OK: independent render passes are byte-identical; Pandoc was not used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
