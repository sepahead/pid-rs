#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
#
# The exact legacy/canonical LaTeX template fragments below derive from the
# Pandoc 3.1.3 and 3.10.2 release templates. The retained upstream BSD notice
# is pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt. The shape validation,
# custody policy, and source-specific transform are project-authored.
"""Normalize two audited Pandoc LaTeX projections for the results guide.

This is a source-specific compatibility transform, not a general LaTeX
normalizer. Pandoc 3.1.3 writes redundant heading ``\\hypertarget`` wrappers,
captionless longtables without the later ``none`` counter, and an older image
projection. Pandoc 3.10.2 writes the canonical forms bound below. The older
forms otherwise create extra named destinations and omit one crosswalk-image
marked-content record. See upstream Pandoc issues #8744 and #11201. Restoring
the canonical TeX image option does not establish a PDF ``/Alt`` entry,
accessible figures, or PDF/UA conformance.

The transform accepts only the complete audited legacy or canonical
compatibility projection. It does not validate unrelated TeX or the
mathematical body; it gains semantic credit only inside the complete PDF gate.
Mixed, partial, reordered, ambiguous, oversized, symbolic, or
version-inconsistent compatibility inputs fail closed.
"""

from __future__ import annotations

import os
import pathlib
import re
import stat as stat_module
import sys
from typing import NoReturn

MAX_INPUT_BYTES = 1_048_576
LEGACY_PANDOC_VERSION = "pandoc 3.1.3"
CANONICAL_PANDOC_VERSION = "pandoc 3.10.2"
SUPPORTED_PANDOC_VERSIONS = (LEGACY_PANDOC_VERSION, CANONICAL_PANDOC_VERSION)
VERSION_PATTERN = re.compile(r"pandoc [0-9]+(?:[.][0-9]+){1,3}(?:[-+][0-9A-Za-z.-]+)?")

EXPECTED_HEADING_IDS = (
    "1-reading-conventions-and-semantic-firewall",
    "evidence-labels",
    "five-distinct-lanes",
    "lattice-positions-versus-audit-coordinates",
    "2-result-map",
    "3-categorical-sx-theory",
    "31-foundational-semantic-audit",
    "32-fixed-finite-alphabet-plug-in-convergence",
    "33-support-change-tolerant-averaged-sx-continuity",
    "4-sampling-and-exact-finite-table-assurance",
    "41-dependency-color-concentration",
    "42-exact-two-source-categorical-sx-assurance",
    "5-higher-source-numerical-and-continuous-estimator-assurance",
    "51-sxpid3-source-marginal-factorization-and-bounded-audit",
    "52-represented-binary64-and-quantizer-assurance",
    "53-ksg-positive-integer-harmonic-arithmetic",
    "6-estimator-choice-global-nonclaims-and-further-reading",
)

TABLE_WRAPPER = "{\\def\\LTcaptype{none} % do not increment counter\n"
NONE_COUNTER = "\\newcounter{none} % for unnumbered tables\n"
LONGTABLE_BEGIN = "\\begin{longtable}[]{@{}\n"
LONGTABLE_END = "\\end{longtable}\n"

LEGACY_TABLE_PREAMBLE = r"""\usepackage{longtable,booktabs,array}
\usepackage{calc} % for calculating minipage widths
"""
CANONICAL_TABLE_PREAMBLE = r"""\usepackage{longtable,booktabs,array}
\usepackage{caption}
\captionsetup[table]{skip=6pt}
\newcounter{none} % for unnumbered tables
\usepackage{calc} % for calculating minipage widths
"""

LONGTABLE_SUPPORT_PROJECTION = r"""% Correct order of tables after \paragraph or \subparagraph
\usepackage{etoolbox}
\makeatletter
\patchcmd\longtable{\par}{\if@noskipsec\mbox{}\fi\par}{}{}
\makeatother
% Allow footnotes in longtable head/foot
\IfFileExists{footnotehyper.sty}{\usepackage{footnotehyper}}{\usepackage{footnote}}
\makesavenoteenv{longtable}
\usepackage{graphicx}
"""

LEGACY_IMAGE_PREAMBLE = r"""\makeatletter
\def\maxwidth{\ifdim\Gin@nat@width>\linewidth\linewidth\else\Gin@nat@width\fi}
\def\maxheight{\ifdim\Gin@nat@height>\textheight\textheight\else\Gin@nat@height\fi}
\makeatother
% Scale images if necessary, so that they will not overflow the page
% margins by default, and it is still possible to overwrite the defaults
% using explicit options in \includegraphics[width, height, ...]{}
\setkeys{Gin}{width=\maxwidth,height=\maxheight,keepaspectratio}
% Set default figure placement to htbp
\makeatletter
\def\fps@figure{htbp}
\makeatother
"""

CANONICAL_IMAGE_PREAMBLE = r"""\makeatletter
\newsavebox\pandoc@box
\newcommand*\pandocbounded[1]{% scales image to fit in text height/width
  \sbox\pandoc@box{#1}%
  \Gscale@div\@tempa{\textheight}{\dimexpr\ht\pandoc@box+\dp\pandoc@box\relax}%
  \Gscale@div\@tempb{\linewidth}{\wd\pandoc@box}%
  \ifdim\@tempb\p@<\@tempa\p@\let\@tempa\@tempb\fi% select the smaller of both
  \ifdim\@tempa\p@<\p@\scalebox{\@tempa}{\usebox\pandoc@box}%
  \else\usebox{\pandoc@box}%
  \fi%
}
% Set default figure placement to htbp
\def\fps@figure{htbp}
\makeatother
"""

LEGACY_CROSSWALK = (
    "\\includegraphics{audit/formal/latex/figures/"
    "sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf}"
)
CANONICAL_CROSSWALK = (
    "\\pandocbounded{\\includegraphics[keepaspectratio,"
    "alt={The 108 audit expressions expand, rather than replace, the 18-position "
    "SxPID3 lattice.}]{audit/formal/latex/figures/"
    "sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf}}"
)
CROSSWALK_FRAME_PREFIX = "\\clearpage\\vspace*{\\fill}\n\n"
CROSSWALK_FRAME_SUFFIX = "\n\n\\vspace*{\\fill}\\clearpage\n"
DOCUMENT_BEGIN = "\\begin{document}\n"
DOCUMENT_END = "\\end{document}\n"

TOP_LEVEL_HEADING_IDS = frozenset(
    {
        "1-reading-conventions-and-semantic-firewall",
        "2-result-map",
        "3-categorical-sx-theory",
        "4-sampling-and-exact-finite-table-assurance",
        "5-higher-source-numerical-and-continuous-estimator-assurance",
        "6-estimator-choice-global-nonclaims-and-further-reading",
    }
)


def fail(message: str) -> NoReturn:
    raise SystemExit(f"Pandoc TeX normalization failed: {message}")


def absolute_lexical(path: pathlib.Path) -> pathlib.Path:
    return pathlib.Path(os.path.abspath(os.fspath(path)))


def reject_symbolic_ancestry(path: pathlib.Path, *, include_final: bool, label: str) -> None:
    absolute = absolute_lexical(path)
    parts = absolute.parts
    current = pathlib.Path(parts[0])
    stop = len(parts) if include_final else len(parts) - 1
    for component in parts[1:stop]:
        current /= component
        try:
            status = current.lstat()
        except FileNotFoundError:
            fail(f"{label} ancestry is absent: {current}")
        if stat_module.S_ISLNK(status.st_mode):
            fail(f"{label} ancestry is symbolic: {current}")
        if current != absolute and not stat_module.S_ISDIR(status.st_mode):
            fail(f"{label} ancestry is not a directory: {current}")


def source_identity(status: os.stat_result) -> tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_nlink,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def directory_identity(status: os.stat_result) -> tuple[int, ...]:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_uid,
        status.st_gid,
    )


def require_source(path: pathlib.Path) -> tuple[tuple[int, ...], bytes]:
    reject_symbolic_ancestry(path, include_final=True, label="input")
    try:
        initial_path_status = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        fail(f"input is absent: {path}")
    if not stat_module.S_ISREG(initial_path_status.st_mode):
        fail(f"input is not regular: {path}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    # A hostile final-path swap to a FIFO must not block before fstat can
    # reject it. O_NONBLOCK has no effect on an ordinary regular file.
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"input could not be opened without following links: {error}")
    try:
        before = os.fstat(descriptor)
        if not stat_module.S_ISREG(before.st_mode):
            fail(f"input is not regular: {path}")
        if before.st_nlink != 1:
            fail(f"input must have exactly one hard link: {path}")
        if before.st_size <= 0 or before.st_size > MAX_INPUT_BYTES:
            fail(f"input byte count is outside 1..{MAX_INPUT_BYTES}: {before.st_size}")
        chunks: list[bytes] = []
        remaining = MAX_INPUT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if source_identity(before) != source_identity(after) or len(data) != before.st_size:
        fail("input changed while it was read")
    reject_symbolic_ancestry(path, include_final=True, label="input")
    try:
        path_status = path.stat(follow_symlinks=False)
    except FileNotFoundError:
        fail("input disappeared after it was read")
    if source_identity(path_status) != source_identity(before):
        fail("input path changed while it was read")
    if data.startswith(b"\xef\xbb\xbf"):
        fail("input must not contain a UTF-8 byte-order mark")
    if b"\x00" in data or b"\r" in data:
        fail("input must be NUL-free UTF-8 with LF line endings")
    return source_identity(before), data


def require_unchanged_source(
    path: pathlib.Path,
    expected_identity: tuple[int, ...],
    expected_data: bytes,
) -> None:
    identity, data = require_source(path)
    if identity != expected_identity or data != expected_data:
        fail("input changed after normalization began")


def require_output(path: pathlib.Path, source: pathlib.Path) -> tuple[int, ...]:
    reject_symbolic_ancestry(path, include_final=False, label="output")
    if absolute_lexical(path) == absolute_lexical(source):
        fail("input and output paths must differ")
    try:
        path.lstat()
    except FileNotFoundError:
        pass
    else:
        fail(f"output must be absent: {path}")
    parent = path.parent
    try:
        parent_status = parent.stat(follow_symlinks=False)
    except FileNotFoundError:
        fail(f"output parent is absent: {parent}")
    if not stat_module.S_ISDIR(parent_status.st_mode):
        fail(f"output parent is not a directory: {parent}")
    return directory_identity(parent_status)


def expected_heading_command(heading_id: str) -> str:
    return "section" if heading_id in TOP_LEVEL_HEADING_IDS else "subsection"


def validate_document_projection(text: str, mode: str) -> None:
    if text.count(DOCUMENT_BEGIN) != 1 or text.count(DOCUMENT_END) != 1:
        fail("document begin/end marker count changed")
    begin_offset = text.index(DOCUMENT_BEGIN)
    end_offset = text.index(DOCUMENT_END)
    if begin_offset >= end_offset:
        fail("document begin/end markers are reordered")
    if not text.endswith(DOCUMENT_END):
        fail("document end marker must terminate the input")

    table_preamble = (
        LEGACY_TABLE_PREAMBLE if mode == "legacy-3.1.3" else CANONICAL_TABLE_PREAMBLE
    )
    image_preamble = (
        LEGACY_IMAGE_PREAMBLE if mode == "legacy-3.1.3" else CANONICAL_IMAGE_PREAMBLE
    )
    template_projection = table_preamble + LONGTABLE_SUPPORT_PROJECTION + image_preamble
    if text.count(template_projection) != 1:
        fail("table/image template projection moved, split, or changed")
    if text.index(template_projection) >= begin_offset:
        fail("table/image template projection moved into the document body")

    crosswalk = LEGACY_CROSSWALK if mode == "legacy-3.1.3" else CANONICAL_CROSSWALK
    framed_crosswalk = CROSSWALK_FRAME_PREFIX + crosswalk + CROSSWALK_FRAME_SUFFIX
    if text.count(framed_crosswalk) != 1:
        fail("crosswalk image projection moved or lost its page frame")
    crosswalk_offset = text.index(framed_crosswalk)
    if not (begin_offset < crosswalk_offset < end_offset):
        fail("crosswalk image projection moved outside the document body")

    expected_labels = set(EXPECTED_HEADING_IDS)
    observed_labels = tuple(
        match.group(1)
        for match in re.finditer(r"\\label\{([^{}]+)\}", text)
        if match.group(1) in expected_labels
    )
    if observed_labels != EXPECTED_HEADING_IDS:
        fail("heading labels are missing, duplicated, or reordered")


def validate_canonical_heading_shapes(text: str) -> None:
    for heading_id in EXPECTED_HEADING_IDS:
        command = expected_heading_command(heading_id)
        pattern = re.compile(
            rf"\\{command}\{{[^{{}}\n]*(?:\n[^{{}}\n]*)?\}}"
            rf"\\label\{{{re.escape(heading_id)}\}}\n"
        )
        if len(pattern.findall(text)) != 1:
            fail(f"canonical heading command/body changed: {heading_id}")


def detect_mode(lines: list[str], pandoc_version: str) -> str:
    legacy_ids = tuple(
        match.group(1)
        for line in lines
        if (match := re.fullmatch(r"\\hypertarget\{([^{}]+)\}\{%\n", line))
    )
    text = "".join(lines)
    table_wrappers = sum(line == TABLE_WRAPPER for line in lines)
    none_counters = sum(line == NONE_COUNTER for line in lines)
    legacy_table_preambles = text.count(LEGACY_TABLE_PREAMBLE)
    canonical_table_preambles = text.count(CANONICAL_TABLE_PREAMBLE)
    if (
        legacy_ids == EXPECTED_HEADING_IDS
        and text.count("\\hypertarget{") == len(EXPECTED_HEADING_IDS)
        and table_wrappers == 0
        and none_counters == 0
        and legacy_table_preambles == 1
        and canonical_table_preambles == 0
    ):
        if pandoc_version != LEGACY_PANDOC_VERSION:
            fail(
                "legacy writer shape is authorized only for "
                f"{LEGACY_PANDOC_VERSION}, not {pandoc_version}"
            )
        return "legacy-3.1.3"
    if (
        legacy_ids == ()
        and "\\hypertarget{" not in text
        and table_wrappers == 4
        and none_counters == 1
        and legacy_table_preambles == 0
        and canonical_table_preambles == 1
    ):
        if pandoc_version == LEGACY_PANDOC_VERSION:
            fail("Pandoc 3.1.3 unexpectedly emitted the canonical writer shape")
        return "canonical"
    fail(
        "writer shape is neither complete legacy nor complete canonical form "
        f"(heading_wrappers={len(legacy_ids)}, table_wrappers={table_wrappers}, "
        f"none_counters={none_counters}, legacy_table_preambles="
        f"{legacy_table_preambles}, canonical_table_preambles="
        f"{canonical_table_preambles})"
    )


def validate_table_shape(lines: list[str], mode: str) -> None:
    text = "".join(lines)
    begin_indices = [index for index, line in enumerate(lines) if line == LONGTABLE_BEGIN]
    end_indices = [index for index, line in enumerate(lines) if line == LONGTABLE_END]
    if (
        len(begin_indices) != 4
        or len(end_indices) != 4
        or text.count("\\begin{longtable}") != 4
        or text.count("\\end{longtable}") != 4
    ):
        fail(
            "longtable token count changed "
            f"(exact_begins={len(begin_indices)}, exact_ends={len(end_indices)})"
        )
    depth = 0
    for index, line in enumerate(lines):
        if line == LONGTABLE_BEGIN:
            if depth != 0:
                fail("longtables must not nest")
            depth = 1
            if mode == "canonical" and (index == 0 or lines[index - 1] != TABLE_WRAPPER):
                fail("canonical longtable lost its adjacent opening wrapper")
        elif line == LONGTABLE_END:
            if depth != 1:
                fail("longtable end does not close one active table")
            depth = 0
            if mode == "canonical" and (
                index + 1 >= len(lines) or lines[index + 1] != "}\n"
            ):
                fail("canonical longtable lost its adjacent closing wrapper")
    if depth != 0:
        fail("longtable remained open at end of input")
    if mode == "canonical":
        wrapper_indices = [index for index, line in enumerate(lines) if line == TABLE_WRAPPER]
        if wrapper_indices != [index - 1 for index in begin_indices]:
            fail("canonical longtable wrappers moved or became ambiguous")


def normalize(text: str, pandoc_version: str) -> tuple[str, str]:
    if VERSION_PATTERN.fullmatch(pandoc_version) is None:
        fail(f"Pandoc version line changed shape: {pandoc_version!r}")
    if pandoc_version not in SUPPORTED_PANDOC_VERSIONS:
        fail(
            "Pandoc version is outside the two audited writer projections: "
            f"{pandoc_version}"
        )
    lines = text.splitlines(keepends=True)
    if not lines or any(not line.endswith("\n") for line in lines):
        fail("input must be nonempty and end every line with LF")
    mode = detect_mode(lines, pandoc_version)
    validate_document_projection(text, mode)
    validate_table_shape(lines, mode)

    for heading_id in EXPECTED_HEADING_IDS:
        if text.count(f"\\label{{{heading_id}}}") != 1:
            fail(f"heading label count changed: {heading_id}")

    output: list[str] = []
    pending_heading: str | None = None
    pending_heading_line_count = 0
    table_begins = 0
    table_ends = 0
    for line in lines:
        heading = re.fullmatch(r"\\hypertarget\{([^{}]+)\}\{%\n", line)
        if heading:
            if mode != "legacy-3.1.3" or pending_heading is not None:
                fail("nested or unexpected heading wrapper")
            pending_heading = heading.group(1)
            pending_heading_line_count = 0
            continue
        if pending_heading is not None:
            pending_heading_line_count += 1
            expected_command = expected_heading_command(pending_heading)
            stripped = line.removesuffix("\n")
            one_line_pattern = re.compile(
                rf"\\{expected_command}\{{[^{{}}\n]*\}}"
                rf"\\label\{{{re.escape(pending_heading)}\}}\}}"
            )
            first_of_two_pattern = re.compile(
                rf"\\{expected_command}\{{[^{{}}\n]*\n"
            )
            second_of_two_pattern = re.compile(
                rf"[^{{}}\n]*\}}\\label\{{{re.escape(pending_heading)}\}}\}}"
            )
            if pending_heading_line_count == 1 and one_line_pattern.fullmatch(stripped):
                line = stripped[:-1] + "\n"
                pending_heading = None
            elif pending_heading_line_count == 1 and first_of_two_pattern.fullmatch(line):
                pass
            elif pending_heading_line_count == 2 and second_of_two_pattern.fullmatch(stripped):
                line = stripped[:-1] + "\n"
                pending_heading = None
            else:
                fail(
                    "legacy heading wrapper body changed or exceeded two lines: "
                    f"{pending_heading}"
                )
        if mode == "legacy-3.1.3" and line == LONGTABLE_BEGIN:
            output.append(TABLE_WRAPPER)
            table_begins += 1
        output.append(line)
        if mode == "legacy-3.1.3" and line == LONGTABLE_END:
            output.append("}\n")
            table_ends += 1

    if pending_heading is not None:
        fail(f"unterminated legacy heading wrapper: {pending_heading}")
    if mode == "legacy-3.1.3":
        if (table_begins, table_ends) != (4, 4):
            fail(
                "legacy table projection changed "
                f"(begins={table_begins}, ends={table_ends})"
            )

    normalized = "".join(output)
    if mode == "legacy-3.1.3":
        if normalized.count(LEGACY_TABLE_PREAMBLE) != 1:
            fail("legacy table preamble changed during normalization")
        normalized = normalized.replace(LEGACY_TABLE_PREAMBLE, CANONICAL_TABLE_PREAMBLE)
        if normalized.count(LEGACY_IMAGE_PREAMBLE) != 1:
            fail("legacy image preamble changed")
        if normalized.count(LEGACY_CROSSWALK) != 1:
            fail("legacy crosswalk image projection changed")
        normalized = normalized.replace(LEGACY_IMAGE_PREAMBLE, CANONICAL_IMAGE_PREAMBLE)
        normalized = normalized.replace(LEGACY_CROSSWALK, CANONICAL_CROSSWALK)
    elif (
        normalized.count(CANONICAL_IMAGE_PREAMBLE) != 1
        or normalized.count(CANONICAL_CROSSWALK) != 1
    ):
        fail("canonical image projection changed")

    if "\\hypertarget{" in normalized:
        fail("a heading hypertarget remained after normalization")
    if normalized.count(TABLE_WRAPPER) != 4:
        fail("canonical captionless-table wrapper count changed")
    if normalized.count(NONE_COUNTER) != 1:
        fail("canonical unnumbered-table counter count changed")
    if normalized.count(CANONICAL_TABLE_PREAMBLE) != 1:
        fail("canonical table preamble count changed")
    if LEGACY_TABLE_PREAMBLE in normalized:
        fail("legacy table preamble remained after normalization")
    if LEGACY_IMAGE_PREAMBLE in normalized or LEGACY_CROSSWALK in normalized:
        fail("a legacy image projection remained after normalization")
    if (
        normalized.count(CANONICAL_IMAGE_PREAMBLE) != 1
        or normalized.count(CANONICAL_CROSSWALK) != 1
    ):
        fail("canonical image projection count changed")
    if len(normalized.encode("utf-8")) > MAX_INPUT_BYTES:
        fail("normalized output exceeds the source-specific byte bound")
    if mode == "canonical" and normalized != text:
        fail("canonical mode must preserve every input byte")
    validate_document_projection(normalized, "canonical")
    validate_canonical_heading_shapes(normalized)
    return mode, normalized


def remove_owned_output_at(
    parent_descriptor: int,
    name: str,
    identity: tuple[int, int],
) -> None:
    try:
        status = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return
    if (
        stat_module.S_ISREG(status.st_mode)
        and (status.st_dev, status.st_ino) == identity
    ):
        os.unlink(name, dir_fd=parent_descriptor)


def require_unchanged_output_parent(
    path: pathlib.Path,
    expected_identity: tuple[int, ...],
) -> None:
    reject_symbolic_ancestry(path, include_final=False, label="output")
    try:
        status = path.parent.stat(follow_symlinks=False)
    except FileNotFoundError:
        fail("output parent disappeared")
    if directory_identity(status) != expected_identity:
        fail("output parent path changed during normalization")


def write_exclusive(
    path: pathlib.Path,
    data: bytes,
    expected_parent_identity: tuple[int, ...],
) -> tuple[tuple[int, int], int]:
    parent_flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        parent_flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        parent_flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        parent_flags |= os.O_CLOEXEC
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    parent_descriptor: int | None = None
    descriptor: int | None = None
    owned_identity: tuple[int, int] | None = None
    try:
        parent_descriptor = os.open(path.parent, parent_flags)
        parent_status = os.fstat(parent_descriptor)
        if (
            not stat_module.S_ISDIR(parent_status.st_mode)
            or directory_identity(parent_status) != expected_parent_identity
        ):
            fail("output parent changed before exclusive creation")
        descriptor = os.open(path.name, flags, 0o600, dir_fd=parent_descriptor)
        opened_status = os.fstat(descriptor)
        owned_identity = (opened_status.st_dev, opened_status.st_ino)
        if not stat_module.S_ISREG(opened_status.st_mode) or opened_status.st_nlink != 1:
            fail("new output is not a singly linked regular file")
        with os.fdopen(descriptor, "wb", closefd=True) as output:
            descriptor = None
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            status = os.fstat(output.fileno())
            if not stat_module.S_ISREG(status.st_mode) or status.st_nlink != 1:
                fail("new output is not a singly linked regular file")
            identity = (status.st_dev, status.st_ino)
        entry_status = os.stat(path.name, dir_fd=parent_descriptor, follow_symlinks=False)
        if source_identity(entry_status) != source_identity(status):
            fail("new output directory entry changed after creation")
        os.fsync(parent_descriptor)
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        if parent_descriptor is not None:
            if owned_identity is not None:
                remove_owned_output_at(parent_descriptor, path.name, owned_identity)
            os.close(parent_descriptor)
        raise
    return identity, parent_descriptor


def require_published_output(
    parent_descriptor: int,
    name: str,
    expected_identity: tuple[int, int],
) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    if hasattr(os, "O_NONBLOCK"):
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        descriptor = os.open(name, flags, dir_fd=parent_descriptor)
    except OSError as error:
        fail(f"published output could not be reopened safely: {error}")
    try:
        before = os.fstat(descriptor)
        if (
            not stat_module.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or (before.st_dev, before.st_ino) != expected_identity
            or before.st_size <= 0
            or before.st_size > MAX_INPUT_BYTES
        ):
            fail("published output identity or shape changed")
        chunks: list[bytes] = []
        remaining = MAX_INPUT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    if source_identity(before) != source_identity(after) or len(data) != before.st_size:
        fail("published output changed while it was read")
    entry_status = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
    if source_identity(entry_status) != source_identity(before):
        fail("published output directory entry changed while it was read")
    return data


def deterministic_summary(mode: str) -> str:
    if mode == "legacy-3.1.3":
        values = (17, 4, 1, 1, 1, 1, "no")
    elif mode == "canonical":
        values = (0, 0, 0, 0, 0, 0, "yes")
    else:  # Defensive: normalize() returns only the two closed modes.
        fail(f"internal mode is unsupported: {mode}")
    return (
        f"mode={mode}; heading_wrappers_removed={values[0]}; "
        f"table_wrappers_inserted={values[1]}; none_counter_inserted={values[2]}; "
        f"table_preamble_replaced={values[3]}; image_preamble_replaced={values[4]}; "
        f"crosswalk_projection_replaced={values[5]}; byte_identity={values[6]}"
    )


def main() -> None:
    if len(sys.argv) != 4:
        fail(f"usage: {sys.argv[0]} 'pandoc VERSION' INPUT.tex OUTPUT.tex")
    pandoc_version = sys.argv[1]
    source = absolute_lexical(pathlib.Path(sys.argv[2]))
    destination = absolute_lexical(pathlib.Path(sys.argv[3]))
    output_parent_identity = require_output(destination, source)
    input_identity, raw = require_source(source)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"input is not UTF-8: {error}")
    mode, normalized = normalize(text, pandoc_version)
    output = normalized.encode("utf-8")
    require_unchanged_source(source, input_identity, raw)
    output_identity, output_parent_descriptor = write_exclusive(
        destination,
        output,
        output_parent_identity,
    )
    try:
        require_unchanged_source(source, input_identity, raw)
        published = require_published_output(
            output_parent_descriptor,
            destination.name,
            output_identity,
        )
        if published != output:
            fail("published output differs from the normalized bytes")
        require_unchanged_output_parent(destination, output_parent_identity)
    except BaseException:
        remove_owned_output_at(
            output_parent_descriptor,
            destination.name,
            output_identity,
        )
        raise
    finally:
        os.close(output_parent_descriptor)
    print(
        "OK: normalized mathematical-results guide Pandoc TeX "
        f"({deterministic_summary(mode)})"
    )


if __name__ == "__main__":
    main()
