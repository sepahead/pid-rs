#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/ksg-m1a-composite-v4-process.tex"
COMMITTED="output/pdf/ksg-m1a-composite-v4-process.pdf"
FIGURE_SVG="audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.svg"
FIGURE_PDF="audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.pdf"
VISUAL_RECEIPT="audit/evidence/ksg-m1a-composite-v4-process-visual-receipt-2026-08-17.md"
RENDER_COMPARATOR="scripts/compare-formal-pdf-renders.py"
EXPECTED_RENDER_COMPARATOR_SHA256="7b230bef4371398c18a3975d6888207bc31a737eeffb0217f3d5bbc0aec3054b"
EXPECTED_RENDER_COMPARATOR_BYTES=16408
RENDER_DPI=120
EXPECTED_FIGURE_SVG_SHA256="9022812adeb3845e9d494428fb5e2f6489bb7cf938444c1c96c364c38d4f6095"
EXPECTED_FIGURE_SVG_BYTES=8326
EXPECTED_REPORT_PAGES=9
EXPECTED_FIGURE_PAGES=1
SOURCE_DATE_EPOCH_VALUE="1786744800"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in latexmk cmp cp env fc-cache kpsewhich lacheck mkdir pdffonts pdfinfo pdftoppm pdftotext python3 rsvg-convert shasum; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "composite-v4 process PDF check: missing command: $command" >&2
    exit 2
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-composite-v4-process-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
if [[ ! -f "$RENDER_COMPARATOR" || -L "$RENDER_COMPARATOR" ]]; then
  echo "composite-v4 process PDF check: render comparator is absent or not a regular file" >&2
  exit 1
fi
if [[ "$(wc -c < "$RENDER_COMPARATOR" | tr -d '[:space:]')" != "$EXPECTED_RENDER_COMPARATOR_BYTES" ]] ||
   [[ "$(shasum -a 256 "$RENDER_COMPARATOR" | awk '{print $1}')" != "$EXPECTED_RENDER_COMPARATOR_SHA256" ]]; then
  echo "composite-v4 process PDF check: render comparator bytes changed" >&2
  exit 1
fi
FIGURE_FONT_ROOT="$BUILD_DIR/figure-fonts"
FIGURE_FONT_CACHE="$BUILD_DIR/figure-font-cache"
FIGURE_FONT_CONFIG="$BUILD_DIR/figure-fonts.conf"
mkdir -p "$FIGURE_FONT_ROOT" "$FIGURE_FONT_CACHE"
for font_name in SourceSansPro-Bold.otf SourceSansPro-Semibold.otf lmroman10-regular.otf; do
  font_path="$(kpsewhich --must-exist "$font_name" || true)"
  if [[ -z "$font_path" || ! -f "$font_path" ]]; then
    echo "composite-v4 process PDF check: required figure font is unavailable: $font_name" >&2
    exit 2
  fi
  cp "$font_path" "$FIGURE_FONT_ROOT/$font_name"
done
python3 -I -S - "$FIGURE_FONT_CONFIG" "$FIGURE_FONT_ROOT" "$FIGURE_FONT_CACHE" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(
    f'''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>{sys.argv[2]}</dir>
  <cachedir>{sys.argv[3]}</cachedir>
  <config></config>
</fontconfig>
''',
    encoding="utf-8",
)
PY
FONTCONFIG_FILE="$FIGURE_FONT_CONFIG" FONTCONFIG_PATH="$BUILD_DIR" fc-cache -f >/dev/null
FIGURE_RENDER_ENV=(
  "PATH=$PATH"
  "LC_ALL=C"
  "LANG=C"
  "TZ=UTC"
  "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH_VALUE"
  "FONTCONFIG_FILE=$FIGURE_FONT_CONFIG"
  "FONTCONFIG_PATH=$BUILD_DIR"
  "PANGOCAIRO_BACKEND=fc"
  "OSFONTDIR=$FIGURE_FONT_ROOT"
)

python3 -I -S - "$FIGURE_SVG" "$EXPECTED_FIGURE_SVG_SHA256" "$EXPECTED_FIGURE_SVG_BYTES" <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v4 process PDF check: custody SVG {detail}")


path = Path(sys.argv[1])
expected_sha256 = sys.argv[2]
expected_bytes = int(sys.argv[3])
raw = path.read_bytes()
if len(raw) != expected_bytes:
    fail("byte count changed")
if hashlib.sha256(raw).hexdigest() != expected_sha256:
    fail("SHA-256 changed")
if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
    fail("contains a document type or entity declaration")

try:
    root = ET.fromstring(raw)
except ET.ParseError as error:
    fail(f"is not well-formed XML: {error}")

svg_namespace = "{http://www.w3.org/2000/svg}"
if root.tag != f"{svg_namespace}svg":
    fail("does not have an SVG root")
expected_root = {
    "width": "160mm",
    "height": "90mm",
    "viewBox": "0 0 1600 900",
    "role": "img",
    "aria-labelledby": "custody-title custody-desc",
    "data-contract-commit": "C4",
    "data-receipt-hashes": "capture-H-only",
    "data-manifest-scope": "all-visible-paths-except-M",
    "data-r4-delta": "A:H A:V M:M",
}
for key, value in expected_root.items():
    if root.get(key) != value:
        fail(f"root attribute {key!r} changed")

forbidden_elements = {
    f"{svg_namespace}animate",
    f"{svg_namespace}animateMotion",
    f"{svg_namespace}animateTransform",
    f"{svg_namespace}filter",
    f"{svg_namespace}foreignObject",
    f"{svg_namespace}linearGradient",
    f"{svg_namespace}radialGradient",
    f"{svg_namespace}script",
    f"{svg_namespace}set",
}
identifiers: set[str] = set()
for element in root.iter():
    if element.tag in forbidden_elements:
        fail(f"contains forbidden element {element.tag.rsplit('}', 1)[-1]!r}")
    identifier = element.get("id")
    if identifier is not None:
        if identifier in identifiers:
            fail(f"repeats identifier {identifier!r}")
        identifiers.add(identifier)
    for name, value in element.attrib.items():
        local_name = name.rsplit("}", 1)[-1]
        if local_name.lower().startswith("on"):
            fail(f"contains event attribute {local_name!r}")
        if local_name in {"href", "src"}:
            fail(f"contains external-resource attribute {local_name!r}")
        for match in re.finditer(r"url\(([^)]+)\)", value):
            if not match.group(1).strip().startswith("#"):
                fail("contains a nonlocal CSS resource")

title = root.find(f"{svg_namespace}title")
description = root.find(f"{svg_namespace}desc")
if title is None or title.get("id") != "custody-title" or not "Acyclic C4-to-R4" in "".join(title.itertext()):
    fail("title identity or text changed")
if description is None or description.get("id") != "custody-desc":
    fail("description identity changed")

visible = " ".join(" ".join(root.itertext()).split())
required_literals = (
    "Capture first, derive once, inventory without self-reference",
    "Terminal runs",
    "Raw capture",
    "Typed receipt",
    "embeds SHA-256(H)",
    "Visible path inputs",
    "never inventories itself",
    "R4 · DIRECT CHILD",
    "A capture H",
    "A receipt V",
    "M manifest M",
    "C4 is the sole parent",
    "R4 tree and commit are outputs",
    "NO SCIENCE CREDIT",
    "no KSG correctness",
    "no PID validity",
    "no authentication",
    "no attestation",
)
for literal in required_literals:
    if literal not in visible:
        fail(f"required literal is absent: {literal!r}")

style_text = "\n".join(
    "".join(element.itertext())
    for element in root.findall(f".//{svg_namespace}style")
)
font_sizes = [float(value) for value in re.findall(r"font-size:\s*([0-9]+(?:\.[0-9]+)?)px", style_text)]
if not font_sizes or min(font_sizes) < 25:
    fail("uses publication text below 25 SVG pixels")
PY

FIGURE_A="$BUILD_DIR/c4-r4-acyclic-custody-a.pdf"
FIGURE_B="$BUILD_DIR/c4-r4-acyclic-custody-b.pdf"
env -i "${FIGURE_RENDER_ENV[@]}" \
  rsvg-convert --format=pdf --keep-aspect-ratio --output="$FIGURE_A" "$FIGURE_SVG"
env -i "${FIGURE_RENDER_ENV[@]}" \
  rsvg-convert --format=pdf --keep-aspect-ratio --output="$FIGURE_B" "$FIGURE_SVG"
if ! cmp -s "$FIGURE_A" "$FIGURE_B"; then
  echo "composite-v4 process PDF check: two custody-figure builds differ" >&2
  exit 1
fi
if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$FIGURE_A" "$FIGURE_PDF"; then
    echo "composite-v4 process PDF check: custody-figure PDF is stale" >&2
    exit 1
  fi
else
  pdftotext "$FIGURE_A" "$BUILD_DIR/figure-a.txt"
  pdftotext "$FIGURE_PDF" "$BUILD_DIR/figure-committed.txt"
  if ! cmp -s "$BUILD_DIR/figure-a.txt" "$BUILD_DIR/figure-committed.txt"; then
    echo "composite-v4 process PDF check: custody-figure text changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$FIGURE_A" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/figure-a.info"
  pdfinfo "$FIGURE_PDF" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/figure-committed.info"
  if ! cmp -s "$BUILD_DIR/figure-a.info" "$BUILD_DIR/figure-committed.info"; then
    echo "composite-v4 process PDF check: custody-figure geometry changed across toolchains" >&2
    exit 1
  fi
fi

if ! lacheck "$SOURCE" >"$BUILD_DIR/lacheck.stdout" 2>&1; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "composite-v4 process PDF check: static LaTeX lint failed" >&2
  exit 1
fi
if [[ -s "$BUILD_DIR/lacheck.stdout" ]]; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "composite-v4 process PDF check: static LaTeX lint reported diagnostics" >&2
  exit 1
fi

if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
  TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -no-shell-escape \
  -outdir="$BUILD_DIR" \
  "$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "composite-v4 process PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/ksg-m1a-composite-v4-process.log"
BUILT="$BUILD_DIR/ksg-m1a-composite-v4-process.pdf"
scripts/check-formal-pdf-log.sh "$LOG"

python3 -I -B - \
  "$BUILT" "$COMMITTED" "$FIGURE_A" "$FIGURE_PDF" \
  "$EXPECTED_REPORT_PAGES" "$EXPECTED_FIGURE_PAGES" \
  "$BUILD_DIR/hostile-clipped-form.pdf" \
  "$BUILD_DIR/hostile-font-programs.pdf" \
  "$BUILD_DIR/hostile-figure-font-programs.pdf" <<'PY'
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path
import re
import subprocess
import sys

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    ContentStream,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NameObject,
    NullObject,
    NumberObject,
    RectangleObject,
    StreamObject,
    TextStringObject,
)


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v4 process PDF check: {detail}")


def pdfinfo(path: Path) -> str:
    result = subprocess.run(
        ["pdfinfo", str(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0 or result.stderr:
        fail(f"pdfinfo failed for {path}")
    return result.stdout


def close(left: float, right: float, tolerance: float = 0.02) -> bool:
    return abs(left - right) <= tolerance


def box_tuple(box: object) -> tuple[float, float, float, float]:
    return tuple(float(value) for value in box)  # type: ignore[arg-type,return-value]


def normalize_pdf_object(value: object) -> object:
    """Resolve a bounded PDF object graph without preserving object-number accidents."""

    budget = [0]
    stack: set[int] = set()

    def walk(current: object, depth: int) -> object:
        budget[0] += 1
        if budget[0] > 8_192 or depth > 64:
            raise ValueError("PDF resource graph exceeds its structural bound")
        if isinstance(current, IndirectObject):
            return walk(current.get_object(), depth + 1)
        if isinstance(current, NullObject) or current is None:
            return ("null",)
        if isinstance(current, BooleanObject) or type(current) is bool:
            return ("bool", bool(current))
        if isinstance(current, NameObject):
            return ("name", str(current))
        if isinstance(current, TextStringObject) or type(current) is str:
            return ("text", str(current))
        if isinstance(current, ByteStringObject) or type(current) is bytes:
            return ("bytes", bytes(current).hex())
        if isinstance(current, (NumberObject, FloatObject)) or type(current) in (int, float):
            return ("number", format(float(current), ".15g"))

        identity = id(current)
        if identity in stack:
            raise ValueError("PDF resource graph contains a cycle")
        stack.add(identity)
        try:
            if isinstance(current, StreamObject):
                metadata = tuple(
                    sorted(
                        (
                            str(key),
                            walk(item, depth + 1),
                        )
                        for key, item in current.items()
                        if str(key) not in {"/Length", "/Filter", "/DecodeParms"}
                    )
                )
                return (
                    "stream",
                    metadata,
                    hashlib.sha256(current.get_data()).hexdigest(),
                )
            if isinstance(current, (DictionaryObject, dict)):
                return (
                    "dict",
                    tuple(
                        sorted(
                            (str(key), walk(item, depth + 1))
                            for key, item in current.items()
                        )
                    ),
                )
            if isinstance(current, (ArrayObject, list, tuple)):
                return ("array", tuple(walk(item, depth + 1) for item in current))
        finally:
            stack.remove(identity)
        raise ValueError(f"unsupported PDF resource object: {type(current).__name__}")

    return walk(value, 0)


def resolved_dictionary(value: object, label: str) -> DictionaryObject | dict[object, object]:
    if isinstance(value, IndirectObject):
        value = value.get_object()
    if not isinstance(value, (DictionaryObject, dict)):
        raise ValueError(f"{label} is not a PDF dictionary")
    return value


def decoded_stream(value: object, label: str) -> bytes:
    if isinstance(value, IndirectObject):
        value = value.get_object()
    if not isinstance(value, StreamObject):
        raise ValueError(f"{label} is not a PDF stream")
    data = value.get_data()
    if not data:
        raise ValueError(f"{label} is empty")
    return data


def subset_neutral_font_name(value: object) -> str:
    name = str(value).removeprefix("/")
    prefix, separator, suffix = name.partition("+")
    if separator and len(prefix) == 6 and prefix.isalpha() and prefix.isupper():
        return suffix
    return name


def validate_resource_equivalence(form_value: object, figure_value: object) -> None:
    """Compare the semantics that survive pdfTeX's deterministic font re-embedding."""

    form_resources = resolved_dictionary(form_value, "embedded Form resources")
    figure_resources = resolved_dictionary(figure_value, "standalone figure resources")
    expected_root_keys = {"/ExtGState", "/Pattern", "/Font"}
    if {str(key) for key in form_resources} != expected_root_keys or {
        str(key) for key in figure_resources
    } != expected_root_keys:
        raise ValueError("custody figure resource-category inventory changed")

    for category in ("/ExtGState", "/Pattern"):
        if normalize_pdf_object(form_resources[category]) != normalize_pdf_object(
            figure_resources[category]
        ):
            raise ValueError(f"embedded custody Form {category} differs from the figure")

    form_fonts = resolved_dictionary(form_resources["/Font"], "embedded Form fonts")
    figure_fonts = resolved_dictionary(figure_resources["/Font"], "standalone figure fonts")
    if {str(key) for key in form_fonts} != {str(key) for key in figure_fonts} or not form_fonts:
        raise ValueError("custody figure font-resource inventory changed")
    for font_name in sorted(form_fonts, key=str):
        form_font = resolved_dictionary(form_fonts[font_name], f"embedded font {font_name}")
        figure_font = resolved_dictionary(
            figure_fonts[font_name], f"standalone font {font_name}"
        )
        for field in ("/Type", "/Subtype"):
            if str(form_font.get(field)) != str(figure_font.get(field)):
                raise ValueError(f"custody figure font {font_name} {field} changed")
        if subset_neutral_font_name(form_font.get("/BaseFont")) != subset_neutral_font_name(
            figure_font.get("/BaseFont")
        ):
            raise ValueError(f"custody figure font {font_name} family changed")
        if decoded_stream(
            form_font.get("/ToUnicode"), f"embedded font {font_name} ToUnicode"
        ) != decoded_stream(
            figure_font.get("/ToUnicode"), f"standalone font {font_name} ToUnicode"
        ):
            raise ValueError(f"custody figure font {font_name} Unicode map changed")
        for label, font in (("embedded", form_font), ("standalone", figure_font)):
            descriptor = resolved_dictionary(
                font.get("/FontDescriptor"), f"{label} font {font_name} descriptor"
            )
            programs = [
                descriptor[field]
                for field in ("/FontFile", "/FontFile2", "/FontFile3")
                if field in descriptor
            ]
            if len(programs) != 1:
                raise ValueError(f"{label} font {font_name} embedding changed")
            decoded_stream(programs[0], f"{label} font {font_name} program")


def transform_point(
    matrix: tuple[float, float, float, float, float, float],
    x: float,
    y: float,
) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def concatenate(
    current: tuple[float, float, float, float, float, float],
    update: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float, float, float, float]:
    a, b, c, d, e, f = current
    g, h, i, j, k, l = update
    return (
        a * g + c * h,
        b * g + d * h,
        a * i + c * j,
        b * i + d * j,
        a * k + c * l + e,
        b * k + d * l + f,
    )


def validate_pdf_objects(
    report: PdfReader,
    figure: PdfReader,
    expected_report_pages: int,
    expected_figure_pages: int,
) -> None:
    if (
        len(report.pages) != expected_report_pages
        or len(figure.pages) != expected_figure_pages
    ):
        raise ValueError("pypdf page inventory changed")
    expected_a4 = (0.0, 0.0, 595.276, 841.89)
    forms: list[tuple[int, str, object]] = []
    for number, page in enumerate(report.pages, start=1):
        if page.get("/Annots") is not None:
            raise ValueError(f"report page {number} contains an undeclared annotation")
        media = box_tuple(page.mediabox)
        crop = box_tuple(page.cropbox)
        if not all(close(value, expected) for value, expected in zip(media, expected_a4)):
            raise ValueError(f"report page {number} MediaBox is not zero-origin portrait A4")
        if not all(close(value, expected) for value, expected in zip(crop, expected_a4)):
            raise ValueError(f"report page {number} CropBox is not zero-origin portrait A4")
        for optional_name in ("/BleedBox", "/TrimBox", "/ArtBox"):
            optional = page.get(optional_name)
            if optional is not None and not all(
                close(value, expected)
                for value, expected in zip(box_tuple(optional), expected_a4)
            ):
                raise ValueError(f"report page {number} {optional_name} differs from A4")
        if int(page.get("/Rotate", 0)) != 0 or float(page.get("/UserUnit", 1)) != 1.0:
            raise ValueError(f"report page {number} rotation or UserUnit changed")
        resources = page.get("/Resources")
        xobjects = {} if resources is None else resources.get_object().get("/XObject", {})
        for name, reference in xobjects.items():
            value = reference.get_object()
            if value.get("/Subtype") == "/Form":
                forms.append((number, str(name), value))
    if len(forms) != 1 or forms[0][0] != 3:
        raise ValueError("custody Form XObject is not unique on report page 3")

    _page_number, form_name, form = forms[0]
    figure_page = figure.pages[0]
    matrix = form.get("/Matrix")
    if matrix is not None:
        identity_matrix = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
        values = tuple(float(value) for value in matrix)
        if len(values) != 6 or any(
            abs(value - expected) > 1e-9
            for value, expected in zip(values, identity_matrix)
        ):
            raise ValueError("embedded custody Form has a nonidentity Matrix")
    if form.get_data() != figure_page.get_contents().get_data():
        raise ValueError("embedded custody Form content differs from the standalone figure")
    figure_media = box_tuple(figure_page.mediabox)
    form_box = box_tuple(form.get("/BBox"))
    if not all(close(value, expected) for value, expected in zip(form_box, figure_media)):
        raise ValueError("embedded custody Form BBox differs from the standalone figure")
    validate_resource_equivalence(form.get("/Resources"), figure_page.get("/Resources"))
    if normalize_pdf_object(form.get("/Group")) != normalize_pdf_object(
        figure_page.get("/Group")
    ):
        raise ValueError("embedded custody Form group differs from the standalone figure")

    page = report.pages[2]
    stream = ContentStream(page.get_contents(), report)
    current = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    stack: list[tuple[float, float, float, float, float, float]] = []
    placements: list[tuple[float, float, float, float]] = []
    for operands, operator in stream.operations:
        if operator == b"q":
            stack.append(current)
        elif operator == b"Q":
            if not stack:
                raise ValueError("report graphics-state stack underflowed")
            current = stack.pop()
        elif operator == b"cm":
            current = concatenate(current, tuple(float(value) for value in operands))
        elif operator == b"Do" and str(operands[0]) == form_name:
            points = [
                transform_point(current, form_box[0], form_box[1]),
                transform_point(current, form_box[0], form_box[3]),
                transform_point(current, form_box[2], form_box[1]),
                transform_point(current, form_box[2], form_box[3]),
            ]
            placements.append(
                (
                    min(point[0] for point in points),
                    min(point[1] for point in points),
                    max(point[0] for point in points),
                    max(point[1] for point in points),
                )
            )
    if stack or len(placements) != 1:
        raise ValueError("custody Form invocation or graphics-state balance changed")
    left, bottom, right, top = placements[0]
    if (
        left < 0
        or bottom < 0
        or right > expected_a4[2]
        or top > expected_a4[3]
        or right - left < 400
        or top - bottom < 200
    ):
        raise ValueError("custody Form is clipped, off-page, or unexpectedly scaled")


def sole_page_form(page: object) -> tuple[str, object]:
    resources = resolved_dictionary(page.get("/Resources"), "report page resources")
    xobjects = resolved_dictionary(resources.get("/XObject"), "report page XObjects")
    forms = [
        (str(name), reference.get_object())
        for name, reference in xobjects.items()
        if reference.get_object().get("/Subtype") == "/Form"
    ]
    if len(forms) != 1:
        raise ValueError("report page does not contain exactly one Form XObject")
    return forms[0]


def swap_source_sans_programs(fonts_value: object, label: str) -> None:
    fonts = resolved_dictionary(fonts_value, f"{label} fonts")
    programs: dict[str, tuple[object, str, object]] = {}
    for resource_name, reference in fonts.items():
        font = resolved_dictionary(reference, f"{label} font {resource_name}")
        family = subset_neutral_font_name(font.get("/BaseFont"))
        descriptor = resolved_dictionary(
            font.get("/FontDescriptor"), f"{label} font {resource_name} descriptor"
        )
        fields = [
            field
            for field in ("/FontFile", "/FontFile2", "/FontFile3")
            if field in descriptor
        ]
        if len(fields) != 1:
            fail(f"font-program hostile control found an invalid embedding for {family}")
        programs[family] = (descriptor, fields[0], descriptor[fields[0]])
    expected_families = {
        "SourceSansPro-Bold",
        "SourceSansPro-Semibold",
        "LMRoman10-Regular",
    }
    if set(programs) != expected_families:
        fail(f"font-program hostile control found an unexpected {label} font inventory")
    bold_descriptor, bold_field, _bold_program = programs["SourceSansPro-Bold"]
    semibold_descriptor, semibold_field, _semibold_program = programs[
        "SourceSansPro-Semibold"
    ]
    _roman_descriptor, _roman_field, roman_program = programs["LMRoman10-Regular"]
    bold_descriptor[NameObject(bold_field)] = roman_program
    semibold_descriptor[NameObject(semibold_field)] = roman_program


def validate_info(text: str, expected_pages: int, *, require_a4: bool) -> None:
    pages = re.search(r"(?m)^Pages:\s+([0-9]+)\s*$", text)
    size = re.search(
        r"(?m)^Page size:\s+([0-9]+(?:\.[0-9]+)?) x "
        r"([0-9]+(?:\.[0-9]+)?) pts(?: \(([^)]+)\))?\s*$",
        text,
    )
    if pages is None or int(pages.group(1)) != expected_pages:
        fail(f"PDF page count is not exactly {expected_pages}")
    if size is None:
        fail("PDF page geometry is absent or malformed")
    width, height = float(size.group(1)), float(size.group(2))
    if width <= 0 or height <= 0:
        fail("PDF page geometry is nonpositive")
    if require_a4 and (
        abs(width - 595.276) > 0.02
        or abs(height - 841.89) > 0.02
        or size.group(3) != "A4"
    ):
        fail("report pages are not portrait A4")


report_pages = int(sys.argv[5])
figure_pages = int(sys.argv[6])
clipped_form_path = Path(sys.argv[7])
font_programs_path = Path(sys.argv[8])
figure_font_programs_path = Path(sys.argv[9])
report_paths = [Path(value) for value in sys.argv[1:3]]
figure_paths = [Path(value) for value in sys.argv[3:5]]
report_info = [pdfinfo(path) for path in report_paths]
figure_info = [pdfinfo(path) for path in figure_paths]
for value in report_info:
    validate_info(value, report_pages, require_a4=True)
for value in figure_info:
    validate_info(value, figure_pages, require_a4=False)
if pypdf.__version__ != "6.15.0":
    fail(f"pypdf version changed: {pypdf.__version__!r}")
pypdf_path = Path(pypdf.__file__).resolve(strict=True)
if Path.cwd().resolve(strict=True) in pypdf_path.parents:
    fail("pypdf resolved from inside the repository")
try:
    for report_path in report_paths:
        for figure_path in figure_paths:
            validate_pdf_objects(
                PdfReader(report_path, strict=True),
                PdfReader(figure_path, strict=True),
                report_pages,
                figure_pages,
            )
except Exception as error:
    fail(f"PDF object structure changed: {error}")

# Causal fail-closure controls for the exact parser above. Each mutation leaves the
# remaining metadata well formed, so rejection reaches the predicate it names.
mutations = (
    (
        re.sub(
            rf"(?m)^Pages:\s+{report_pages}\s*$",
            f"Pages:           {report_pages + 1}",
            report_info[0],
        ),
        report_pages,
        True,
    ),
    (
        re.sub(
            r"(?m)^Page size:.*$",
            "Page size:       612 x 792 pts (letter)",
            report_info[0],
        ),
        report_pages,
        True,
    ),
    (re.sub(r"(?m)^Pages:\s+1\s*$", "Pages:           2", figure_info[0]), 1, False),
)
for mutated, pages, require_a4 in mutations:
    try:
        validate_info(mutated, pages, require_a4=require_a4)
    except SystemExit:
        pass
    else:
        fail("PDF-metadata hostile control was accepted")

# The object-level controls exercise the two prior false-positive classes while
# leaving all unrelated pages and figure bytes unchanged.
report_raw = report_paths[0].read_bytes()
figure_reader = PdfReader(figure_paths[0], strict=True)
late_box = PdfReader(BytesIO(report_raw), strict=True)
late_box.pages[-1].mediabox = RectangleObject((0, 0, 612, 841.89))
late_box.pages[-1].cropbox = RectangleObject((0, 0, 612, 841.89))
relocated = PdfReader(BytesIO(report_raw), strict=True)
page_three_resources = relocated.pages[2]["/Resources"].get_object()
page_four_resources = relocated.pages[3]["/Resources"].get_object()
page_four_resources[NameObject("/XObject")] = page_three_resources.pop(
    NameObject("/XObject")
)
off_page_matrix = PdfReader(BytesIO(report_raw), strict=True)
off_page_xobjects = (
    off_page_matrix.pages[2]["/Resources"].get_object()["/XObject"].get_object()
)
off_page_form = next(
    reference.get_object()
    for reference in off_page_xobjects.values()
    if reference.get_object().get("/Subtype") == "/Form"
)
off_page_form[NameObject("/Matrix")] = ArrayObject(
    [
        FloatObject(1),
        FloatObject(0),
        FloatObject(0),
        FloatObject(1),
        FloatObject(10_000),
        FloatObject(0),
    ]
)
empty_resources = PdfReader(BytesIO(report_raw), strict=True)
empty_xobjects = (
    empty_resources.pages[2]["/Resources"].get_object()["/XObject"].get_object()
)
empty_form = next(
    reference.get_object()
    for reference in empty_xobjects.values()
    if reference.get_object().get("/Subtype") == "/Form"
)
empty_form[NameObject("/Resources")] = DictionaryObject()
linked = PdfReader(BytesIO(report_raw), strict=True)
linked.pages[1][NameObject("/Annots")] = ArrayObject(
    [
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Annot"),
                NameObject("/Subtype"): NameObject("/Link"),
                NameObject("/Rect"): RectangleObject((72, 72, 180, 90)),
                NameObject("/A"): DictionaryObject(
                    {
                        NameObject("/S"): NameObject("/URI"),
                        NameObject("/URI"): TextStringObject("relative-target.json"),
                    }
                ),
            }
        )
    ]
)
for hostile in (late_box, relocated, off_page_matrix, empty_resources, linked):
    try:
        validate_pdf_objects(hostile, figure_reader, report_pages, figure_pages)
    except ValueError:
        pass
    else:
        fail("PDF object-structure hostile control was accepted")

# Render-level causal controls for two visibility mutations that preserve text
# extraction and most PDF object metadata. The shell below exercises the actual
# bounded raster predicate against both generated files.
clipped_writer = PdfWriter(clone_from=BytesIO(report_raw))
clipped_page = clipped_writer.pages[2]
clipped_form_name, _clipped_form = sole_page_form(clipped_page)
clipped_stream = ContentStream(clipped_page.get_contents(), clipped_writer)
invocations = [
    index
    for index, (operands, operator) in enumerate(clipped_stream.operations)
    if operator == b"Do"
    and len(operands) == 1
    and str(operands[0]) == clipped_form_name
]
if len(invocations) != 1:
    fail("clipping hostile control cannot locate the unique custody Form invocation")
clipped_stream.operations[invocations[0]:invocations[0]] = [
    (
        [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)],
        b"re",
    ),
    ([], b"W"),
    ([], b"n"),
]
clipped_page.replace_contents(clipped_stream)
clipped_writer.write(clipped_form_path)
clipped_writer.close()

font_writer = PdfWriter(clone_from=BytesIO(report_raw))
_font_form_name, font_form = sole_page_form(font_writer.pages[2])
font_resources = resolved_dictionary(font_form.get("/Resources"), "hostile Form resources")
swap_source_sans_programs(font_resources.get("/Font"), "embedded Form")
font_writer.write(font_programs_path)
font_writer.close()

figure_writer = PdfWriter(clone_from=figure_paths[0])
figure_resources = resolved_dictionary(
    figure_writer.pages[0].get("/Resources"), "standalone hostile figure resources"
)
swap_source_sans_programs(figure_resources.get("/Font"), "standalone figure")
figure_writer.write(figure_font_programs_path)
figure_writer.close()

for hostile_report, hostile_figure, label in (
    (clipped_form_path, figure_paths[0], "clipped Form"),
    (font_programs_path, figure_paths[0], "embedded font programs"),
    (report_paths[0], figure_font_programs_path, "standalone font programs"),
):
    try:
        validate_pdf_objects(
            PdfReader(hostile_report, strict=True),
            PdfReader(hostile_figure, strict=True),
            report_pages,
            figure_pages,
        )
    except Exception as error:
        fail(f"render hostile control was rejected before raster comparison ({label}): {error}")
PY

mkdir -p "$BUILD_DIR/pdf-tools-home" "$BUILD_DIR/pdf-tools-tmp"

render_report_pages() {
  local pdf="$1"
  local output_directory="$2"
  local label="$3"
  local first_page="$4"
  local last_page="$5"
  local single_file="$6"
  local -a render_command=(pdftoppm -png)
  local output_prefix="$output_directory/page"
  if [[ "$single_file" == "yes" ]]; then
    render_command+=(-singlefile)
    output_prefix="$output_directory/page-1"
  elif [[ "$single_file" != "no" ]]; then
    echo "composite-v4 process PDF check: internal Poppler single-file mode changed" >&2
    exit 2
  fi
  render_command+=(
    -f "$first_page" -l "$last_page" -r "$RENDER_DPI" "$pdf" "$output_prefix"
  )
  mkdir -p "$output_directory"
  if ! env -i \
    "PATH=$PATH" \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    "HOME=$BUILD_DIR/pdf-tools-home" \
    "TMPDIR=$BUILD_DIR/pdf-tools-tmp" \
    "${render_command[@]}" \
      >"$BUILD_DIR/$label.stdout" 2>"$BUILD_DIR/$label.stderr"; then
    cat "$BUILD_DIR/$label.stdout" "$BUILD_DIR/$label.stderr" >&2
    echo "composite-v4 process PDF check: Poppler rendering failed: $label" >&2
    exit 1
  fi
  for diagnostic in "$BUILD_DIR/$label.stdout" "$BUILD_DIR/$label.stderr"; do
    if [[ -s "$diagnostic" ]]; then
      cat "$diagnostic" >&2
      echo "composite-v4 process PDF check: Poppler emitted a rendering diagnostic: $label" >&2
      exit 1
    fi
  done
}

compare_render_sets() {
  local left_directory="$1"
  local right_directory="$2"
  local pages="$3"
  local label="$4"
  local receipt="$5"
  python3 -I -S "$RENDER_COMPARATOR" \
    --left-dir "$left_directory" \
    --right-dir "$right_directory" \
    --pages "$pages" \
    --label "$label" \
    --receipt "$receipt" \
    --large-delta 24 \
    --max-mean-abs 0.20 \
    --max-changed-fraction 0.01 \
    --max-large-fraction 0.001
}

BUILT_PAGE_THREE="$BUILD_DIR/render-built-page-three"
render_report_pages "$BUILT" "$BUILT_PAGE_THREE" "render-built-page-three" 3 3 yes
compare_render_sets \
  "$BUILT_PAGE_THREE" "$BUILT_PAGE_THREE" 1 \
  "positive page-3 self-comparison" "$BUILD_DIR/render-positive.tsv"

for hostile_name in clipped-form font-programs; do
  hostile_pdf="$BUILD_DIR/hostile-$hostile_name.pdf"
  hostile_render="$BUILD_DIR/render-hostile-$hostile_name"
  hostile_receipt="$BUILD_DIR/render-hostile-$hostile_name.tsv"
  hostile_stdout="$BUILD_DIR/render-hostile-$hostile_name.compare.stdout"
  hostile_stderr="$BUILD_DIR/render-hostile-$hostile_name.compare.stderr"
  render_report_pages \
    "$hostile_pdf" "$hostile_render" "render-hostile-$hostile_name" 3 3 yes
  if compare_render_sets \
      "$BUILT_PAGE_THREE" "$hostile_render" 1 \
      "hostile $hostile_name" "$hostile_receipt" \
      >"$hostile_stdout" 2>"$hostile_stderr"; then
    echo "composite-v4 process PDF check: render hostile control was accepted: $hostile_name" >&2
    exit 1
  fi
  if [[ -e "$hostile_receipt" ]] ||
     ! grep -F -- "page 1 exceeds its visual bound" "$hostile_stderr" >/dev/null; then
    cat "$hostile_stdout" "$hostile_stderr" >&2
    echo "composite-v4 process PDF check: render hostile control was noncausal: $hostile_name" >&2
    exit 1
  fi
done

BUILT_FIGURE_PAGE="$BUILD_DIR/render-built-figure"
HOSTILE_FIGURE_PAGE="$BUILD_DIR/render-hostile-figure-font-programs"
render_report_pages "$FIGURE_A" "$BUILT_FIGURE_PAGE" "render-built-figure" 1 1 yes
render_report_pages \
  "$BUILD_DIR/hostile-figure-font-programs.pdf" \
  "$HOSTILE_FIGURE_PAGE" "render-hostile-figure-font-programs" 1 1 yes
if compare_render_sets \
    "$BUILT_FIGURE_PAGE" "$HOSTILE_FIGURE_PAGE" 1 \
    "hostile standalone figure font-programs" \
    "$BUILD_DIR/render-hostile-figure-font-programs.tsv" \
    >"$BUILD_DIR/render-hostile-figure-font-programs.compare.stdout" \
    2>"$BUILD_DIR/render-hostile-figure-font-programs.compare.stderr"; then
  echo "composite-v4 process PDF check: standalone-figure render hostile control was accepted" >&2
  exit 1
fi
if [[ -e "$BUILD_DIR/render-hostile-figure-font-programs.tsv" ]] ||
   ! grep -F -- "page 1 exceeds its visual bound" \
      "$BUILD_DIR/render-hostile-figure-font-programs.compare.stderr" >/dev/null; then
  cat "$BUILD_DIR/render-hostile-figure-font-programs.compare.stdout" \
      "$BUILD_DIR/render-hostile-figure-font-programs.compare.stderr" >&2
  echo "composite-v4 process PDF check: standalone-figure render hostile control was noncausal" >&2
  exit 1
fi

pdftotext "$BUILT" "$BUILD_DIR/built.semantic.txt"
required_text=(
  "two separately sufficient"
  "Provider identifiers are"
  "single-parent direct child"
  "Acyclic C4-to-R4 byte custody"
  "R4 tree and commit identities are outputs"
  "receipt-finalization"
  "execution-custody evidence only"
  "b336e6f54450090693731f2391b1ef3e112095dd9a9c8cbdadddbf2f855fba47"
  "Rejected local pre-publication replay attempt"
  "fb162cc40da3059b61eab9024f4aa38cf6daf2d84ef7e1d8a26dc7d345291e70"
  "document is neither renumbered nor relabelled as the current receipt"
  "accepted-current-replay"
  "Withdrawn replay after a stale hostile fixture"
  "6d5068a2ade251b4ea005e847b78be"
  "mixed direct/safe redirect delivery as a positive"
  "digest alone provides neither recovery nor reproducibility"
  "Raw-to-typed join"
  "PID and method firewall"
  "Categorical MGW"
  "Analytic continuous"
  "Distinct discrete PID"
  "Research-queue non-evidence"
  "No v3 receipt is issued in the checked lineage"
)
for sentinel in "${required_text[@]}"; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.semantic.txt" >/dev/null; then
    echo "composite-v4 process PDF check: required text is absent: $sentinel" >&2
    exit 1
  fi
done

python3 -I -S - "$BUILD_DIR/built.semantic.txt" <<'PY'
from pathlib import Path
import sys

text = " ".join(Path(sys.argv[1]).read_text(encoding="utf-8").split())
ordered = (
    "Table 2: Green process evidence cannot cross a scientific-object boundary.",
    "Research-queue non-evidence",
    "They remain explicit future research items until",
)
positions = tuple(text.find(literal) for literal in ordered)
if any(position < 0 for position in positions) or positions != tuple(sorted(positions)):
    raise SystemExit(
        "composite-v4 process PDF check: scientific-boundary table crosses the research-queue reading order"
    )
PY

for page in $(seq 1 "$EXPECTED_REPORT_PAGES"); do
  page_text="$BUILD_DIR/built.page-$page.txt"
  pdftotext -f "$page" -l "$page" "$BUILT" "$page_text"
  if [[ "$page" == "3" ]]; then
    page_three_text=(
      "Figure 1: Acyclic C4-to-R4 byte custody."
      "Terminal runs"
      "Raw capture"
      "Typed receipt"
      "Visible path inputs"
      "NO SCIENCE CREDIT"
    )
    for literal in "${page_three_text[@]}"; do
      if ! grep -F -- "$literal" "$page_text" >/dev/null; then
        echo "composite-v4 process PDF check: custody figure text is absent from page 3: $literal" >&2
        exit 1
      fi
    done
  elif grep -F -- "Figure 1: Acyclic C4-to-R4 byte custody." "$page_text" >/dev/null; then
    echo "composite-v4 process PDF check: custody figure caption appears outside page 3" >&2
    exit 1
  fi
done

for pdf in "$FIGURE_A" "$FIGURE_PDF" "$BUILT" "$COMMITTED"; do
  if ! pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "composite-v4 process PDF check: every font must be embedded, subset, and Unicode-mapped" >&2
    exit 1
  fi
done

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$COMMITTED"; then
    echo "composite-v4 process PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
  pdftotext -layout "$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "composite-v4 process PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "composite-v4 process PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
  BUILT_RENDER="$BUILD_DIR/render-built-report"
  COMMITTED_RENDER="$BUILD_DIR/render-committed-report"
  render_report_pages \
    "$BUILT" "$BUILT_RENDER" "render-built-report" \
    1 "$EXPECTED_REPORT_PAGES" no
  render_report_pages \
    "$COMMITTED" "$COMMITTED_RENDER" "render-committed-report" \
    1 "$EXPECTED_REPORT_PAGES" no
  compare_render_sets \
    "$BUILT_RENDER" "$COMMITTED_RENDER" "$EXPECTED_REPORT_PAGES" \
    "cross-toolchain report" "$BUILD_DIR/cross-toolchain-render.tsv"
  COMMITTED_FIGURE_RENDER="$BUILD_DIR/render-committed-figure"
  render_report_pages \
    "$FIGURE_PDF" "$COMMITTED_FIGURE_RENDER" "render-committed-figure" 1 1 yes
  compare_render_sets \
    "$BUILT_FIGURE_PAGE" "$COMMITTED_FIGURE_RENDER" 1 \
    "cross-toolchain custody figure" "$BUILD_DIR/cross-toolchain-figure-render.tsv"
fi

if [[ ! -f "$VISUAL_RECEIPT" || -L "$VISUAL_RECEIPT" ]]; then
  echo "composite-v4 process PDF check: visual-review receipt is absent or not a regular file" >&2
  exit 1
fi
python3 -I -S - \
  "$VISUAL_RECEIPT" "$COMMITTED" "$FIGURE_SVG" "$FIGURE_PDF" <<'PY'
from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v4 process PDF check: visual-review receipt {detail}")


receipt_path, report_path, svg_path, figure_path = map(Path, sys.argv[1:])
raw = receipt_path.read_bytes()
if not raw or len(raw) > 16_384 or b"\r" in raw or not raw.endswith(b"\n"):
    fail("has invalid byte framing")
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError as exc:
    fail(f"is not strict UTF-8: {exc}")
lines = text.splitlines()
if not lines or lines[0] != "# Composite-v4 process PDF visual-review receipt" or lines[1:2] != [""]:
    fail("lacks its canonical visible title")
field_order = (
    "schema",
    "subject",
    "pdf_sha256",
    "figure_svg",
    "figure_svg_sha256",
    "figure_pdf",
    "figure_pdf_sha256",
    "pages",
    "dpi",
    "color_pages_reviewed",
    "grayscale_pages_reviewed",
    "figure_pages_reviewed",
    "status",
    "review_date_utc",
    "reviewer_kind",
)
fields: dict[str, str] = {}
for offset, name in enumerate(field_order, start=2):
    if offset >= len(lines):
        fail(f"is truncated before {name}")
    match = re.fullmatch(rf"{re.escape(name)}: `([^`]+)`", lines[offset])
    if match is None:
        fail(f"has noncanonical field order or syntax at {name}")
    fields[name] = match.group(1)
if lines[2 + len(field_order):2 + len(field_order) + 1] != [""]:
    fail("does not terminate its field block with one blank line")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


expected = {
    "schema": "pid-rs/composite-v4-process-visual-review/v1",
    "subject": "output/pdf/ksg-m1a-composite-v4-process.pdf",
    "pdf_sha256": sha256(report_path),
    "figure_svg": "audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.svg",
    "figure_svg_sha256": sha256(svg_path),
    "figure_pdf": "audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.pdf",
    "figure_pdf_sha256": sha256(figure_path),
    "pages": "9",
    "dpi": "144",
    "color_pages_reviewed": "1-9",
    "grayscale_pages_reviewed": "1-9",
    "figure_pages_reviewed": "3",
    "status": "passed",
    "review_date_utc": "2026-08-17",
    "reviewer_kind": "agent-visual-inspection",
}
for name, value in expected.items():
    if fields.get(name) != value:
        fail(f"field {name} differs: {fields.get(name)!r}")
required = (
    "All nine color pages and all nine grayscale pages were viewed in page order at 144 dpi.",
    "The custody figure on page 3 was also reviewed at its native 1600-pixel width in color.",
    "The first rejected-attempt framing section on page 4 was checked for legible digests, clean line breaks, and separation of execution custody from publication acceptance.",
    "The stale-hostile-fixture disposition on pages 4 and 5 was checked for the mixed-delivery distinction, explicit raw-output omission, causal correction, and zero-credit boundary.",
    "The terminal nonclaims section on page 9 was checked as an intentional section page with clean hierarchy and whitespace, not a blank or spill page.",
    "The final PDF contains no annotations; repository paths are printed as noninteractive text, so no relative or unaudited URI is exposed.",
    "No blank, clipped, overlapping, misordered, or visibly corrupt page or figure element was observed.",
    "The root agent completed this bounded visual inspection; no dependency-disjoint or human-review credit is claimed.",
    "This receipt binds the reviewed bytes and review scope. It does not prove mathematical correctness, accessibility conformance, provider authenticity, or scientific validity.",
)
body_offset = 3 + len(field_order)
paragraphs = tuple(
    " ".join(paragraph.split())
    for paragraph in "\n".join(lines[body_offset:]).strip().split("\n\n")
    if paragraph.strip()
)
def validate_paragraphs(candidate: tuple[str, ...]) -> None:
    if candidate != required:
        raise ValueError("body paragraph inventory or order changed")


try:
    validate_paragraphs(paragraphs)
except ValueError as exc:
    fail(str(exc))

# Causal fail-closure controls for the actual closed-body predicate. These retain
# valid field syntax and otherwise-valid prose, so they cannot pass by accident.
hostile_bodies = (
    required + ("Contradictory extra review claim.",),
    required[:-1],
    (required[1], required[0], *required[2:]),
)
for hostile in hostile_bodies:
    try:
        validate_paragraphs(hostile)
    except ValueError:
        pass
    else:
        fail("visual-review hostile control was accepted")
PY

DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite-v4 process PDF has its required text, page structure, review scope, fonts, and same-toolchain bytes ($DIGEST)"
else
  echo "OK: composite-v4 process PDF has its required text, page structure, review scope, fonts, cross-toolchain structure, and bounded same-renderer raster agreement ($DIGEST)"
fi
