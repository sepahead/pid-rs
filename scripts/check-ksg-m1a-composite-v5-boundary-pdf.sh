#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
MD="audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md"
TEX="audit/formal/latex/ksg-m1a-composite-v5-boundary.tex"
SVG="audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg"
FIGURE_PDF="audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf"
PDF="output/pdf/ksg-m1a-composite-v5-boundary.pdf"
RENDERING_RECEIPT="output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv"
VISUAL_RECEIPT="audit/evidence/ksg-rev4-m1a-composite-v5-boundary-visual-receipt-2026-08-18.md"
COMPARATOR="scripts/compare-formal-pdf-renders.py"
EXPECTED_MD_SHA256="6596e3c7e4a8bca989ad4724efb2f9c7592564b359b29f3a2a7a224ce2270a29"
EXPECTED_MD_BYTES=13398
EXPECTED_TEX_SHA256="8f32bf892c102b73c20d507c92b631d2387ab07b686ab7e0a163eae7f1f52527"
EXPECTED_TEX_BYTES=12800
EXPECTED_SVG_SHA256="2f5040914e30e2db84c43035c3983a5e7a0150288a1ea53f8291cd4b5e7bc081"
EXPECTED_SVG_BYTES=9835
EXPECTED_COMPARATOR_SHA256="7b230bef4371398c18a3975d6888207bc31a737eeffb0217f3d5bbc0aec3054b"
EXPECTED_COMPARATOR_BYTES=16408
EXPECTED_PAGES=4
EXPECTED_FIGURE_PAGE=3
RENDER_DPI=120
SOURCE_DATE_EPOCH_VALUE=1787004000

fail() {
  echo "composite-v5 boundary PDF check: $*" >&2
  exit 1
}

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in awk cmp cp env fc-cache kpsewhich lacheck latexmk mkdir pdffonts pdfinfo \
  pdftoppm pdftotext python3 rsvg-convert shasum wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite-v5 boundary PDF check: missing command: $command" >&2
    exit 2
  }
done

verify_file() {
  local path="$1" expected_sha="$2" expected_bytes="$3"
  [[ -f "$path" && ! -L "$path" ]] || fail "$path is absent, nonregular, or a symlink"
  [[ "$(wc -c <"$path" | tr -d '[:space:]')" == "$expected_bytes" ]] || \
    fail "$path byte count changed"
  [[ "$(shasum -a 256 "$path" | awk '{print $1}')" == "$expected_sha" ]] || \
    fail "$path SHA-256 changed"
}

cd "$ROOT"
verify_file "$MD" "$EXPECTED_MD_SHA256" "$EXPECTED_MD_BYTES"
verify_file "$TEX" "$EXPECTED_TEX_SHA256" "$EXPECTED_TEX_BYTES"
verify_file "$SVG" "$EXPECTED_SVG_SHA256" "$EXPECTED_SVG_BYTES"
verify_file "$COMPARATOR" "$EXPECTED_COMPARATOR_SHA256" "$EXPECTED_COMPARATOR_BYTES"
for path in "$FIGURE_PDF" "$PDF" "$RENDERING_RECEIPT" "$VISUAL_RECEIPT"; do
  [[ -f "$path" && ! -L "$path" ]] || fail "$path is absent, nonregular, or a symlink"
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-composite-v5-boundary-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_ROOT"' EXIT

python3 -I -S - "$SVG" <<'PY'
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v5 boundary PDF check: SVG {detail}")


raw = Path(sys.argv[1]).read_bytes()
if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
    fail("contains a document type or entity declaration")
try:
    root = ET.fromstring(raw)
except ET.ParseError as error:
    fail(f"is not well-formed XML: {error}")
ns = "{http://www.w3.org/2000/svg}"
if root.tag != f"{ns}svg":
    fail("does not have an SVG root")
expected_root = {
    "width": "160mm",
    "height": "90mm",
    "viewBox": "0 0 1600 900",
    "role": "img",
    "aria-labelledby": "v5-title v5-desc",
    "data-predecessor": "C4",
    "data-failed-contract": "v4",
    "data-successor": "C5",
    "data-receipt": "R5",
    "data-r4-status": "permanently-unissued",
    "data-repair-count": "5",
    "data-fifth-repair": "legacy-hosted-recovery-readme-token-expectation",
}
for key, value in expected_root.items():
    if root.get(key) != value:
        fail(f"root attribute {key!r} changed")
forbidden = {
    f"{ns}animate", f"{ns}animateMotion", f"{ns}animateTransform", f"{ns}filter",
    f"{ns}foreignObject", f"{ns}image", f"{ns}linearGradient", f"{ns}radialGradient",
    f"{ns}script", f"{ns}set",
}
ids: set[str] = set()
for element in root.iter():
    if element.tag in forbidden:
        fail(f"contains forbidden element {element.tag.rsplit('}', 1)[-1]!r}")
    identifier = element.get("id")
    if identifier:
        if identifier in ids:
            fail(f"repeats identifier {identifier!r}")
        ids.add(identifier)
    for name, value in element.attrib.items():
        local = name.rsplit("}", 1)[-1]
        if local.lower().startswith("on"):
            fail(f"contains event attribute {local!r}")
        if local in {"href", "src"}:
            fail(f"contains external resource attribute {local!r}")
        for match in re.finditer(r"url\(([^)]+)\)", value):
            target = match.group(1).strip().strip("'\"")
            if not target.startswith("#"):
                fail("contains a nonlocal CSS resource")
            if target[1:] not in ids and target[1:] not in {
                candidate.get("id") for candidate in root.iter()
            }:
                fail(f"references absent local identifier {target!r}")
title = root.find(f"{ns}title")
desc = root.find(f"{ns}desc")
if title is None or title.get("id") != "v5-title":
    fail("title identity changed")
if desc is None or desc.get("id") != "v5-desc":
    fail("description identity changed")
visible = " ".join(" ".join(root.itertext()).split())
required = (
    "A failed attempt is evidence; it is not qualification",
    "C5 direct child of C4",
    "R4 UNISSUED",
    "Q4 = CI4 AND CodeQL4 AND D4 = false",
    "Five bounded repairs",
    "replace stale v3 README-token demand",
    "Fresh C5 qualification only",
    "Q5 = L5 AND CI5 AND CodeQL5 AND D5",
    "one exact C5 · attempt 1 · all terminal success",
    "Q5 permits R5",
    "Evidence, not authority",
    "C4 stays published · R4 stays unissued · C5 is a new child",
    "no PID/KSG correctness · no authentication · no independence · no scientific novelty",
)
for literal in required:
    if literal not in visible:
        fail(f"required literal is absent: {literal!r}")
style = "\n".join("".join(node.itertext()) for node in root.findall(f".//{ns}style"))
sizes = [float(value) for value in re.findall(r"font-size:\s*([0-9]+(?:\.[0-9]+)?)px", style)]
if not sizes or min(sizes) < 25:
    fail("uses publication text below 25 SVG pixels")
PY

FONT_ROOT="$BUILD_ROOT/fonts"
FONT_CACHE="$BUILD_ROOT/font-cache"
FONT_CONFIG="$BUILD_ROOT/fonts.conf"
mkdir -p "$FONT_ROOT" "$FONT_CACHE"
for font_name in SourceSansPro-Bold.otf SourceSansPro-Semibold.otf lmroman10-regular.otf; do
  font_path="$(kpsewhich --must-exist "$font_name" || true)"
  [[ -n "$font_path" && -f "$font_path" ]] || {
    echo "composite-v5 boundary PDF check: required font unavailable: $font_name" >&2
    exit 2
  }
  cp "$font_path" "$FONT_ROOT/$font_name"
done
python3 -I -S - "$FONT_CONFIG" "$FONT_ROOT" "$FONT_CACHE" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(
    '<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
    f'<fontconfig><dir>{sys.argv[2]}</dir><cachedir>{sys.argv[3]}</cachedir><config></config></fontconfig>\n',
    encoding="utf-8",
)
PY
FONTCONFIG_FILE="$FONT_CONFIG" FONTCONFIG_PATH="$BUILD_ROOT" fc-cache -f >/dev/null
FIGURE_ENV=(
  "PATH=$PATH" LC_ALL=C LANG=C TZ=UTC "SOURCE_DATE_EPOCH=$SOURCE_DATE_EPOCH_VALUE"
  "FONTCONFIG_FILE=$FONT_CONFIG" "FONTCONFIG_PATH=$BUILD_ROOT" PANGOCAIRO_BACKEND=fc
  "OSFONTDIR=$FONT_ROOT"
)
FIGURE_A="$BUILD_ROOT/figure-a.pdf"
FIGURE_B="$BUILD_ROOT/figure-b.pdf"
env -i "${FIGURE_ENV[@]}" rsvg-convert -f pdf -a -o "$FIGURE_A" "$SVG"
env -i "${FIGURE_ENV[@]}" rsvg-convert -f pdf -a -o "$FIGURE_B" "$SVG"
cmp -s "$FIGURE_A" "$FIGURE_B" || fail "two isolated SVG-to-PDF builds differ"

if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$FIGURE_A" "$FIGURE_PDF" || fail "committed figure PDF is stale or not reproducible"
else
  pdftotext "$FIGURE_A" "$BUILD_ROOT/figure-a.txt"
  pdftotext "$FIGURE_PDF" "$BUILD_ROOT/figure-committed.txt"
  cmp -s "$BUILD_ROOT/figure-a.txt" "$BUILD_ROOT/figure-committed.txt" || \
    fail "figure text changed across toolchains"
  pdfinfo "$FIGURE_A" | awk '/^(Pages|Page size):/' >"$BUILD_ROOT/figure-a.info"
  pdfinfo "$FIGURE_PDF" | awk '/^(Pages|Page size):/' >"$BUILD_ROOT/figure-committed.info"
  cmp -s "$BUILD_ROOT/figure-a.info" "$BUILD_ROOT/figure-committed.info" || \
    fail "figure geometry changed across toolchains"
fi

if ! lacheck "$TEX" >"$BUILD_ROOT/lacheck.out" 2>&1; then
  cat "$BUILD_ROOT/lacheck.out" >&2
  fail "LaTeX static lint failed"
fi
[[ ! -s "$BUILD_ROOT/lacheck.out" ]] || {
  cat "$BUILD_ROOT/lacheck.out" >&2
  fail "LaTeX static lint emitted diagnostics"
}

build_report() {
  local directory="$1" label="$2"
  mkdir -p "$directory"
  if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
    TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" \
    latexmk -pdf -interaction=nonstopmode -halt-on-error -no-shell-escape \
      -outdir="$directory" "$TEX" >"$BUILD_ROOT/$label.stdout" 2>&1; then
    cat "$BUILD_ROOT/$label.stdout" >&2
    fail "LaTeX build failed: $label"
  fi
  scripts/check-formal-pdf-log.sh "$directory/ksg-m1a-composite-v5-boundary.log"
}
BUILD_A="$BUILD_ROOT/build-a"
BUILD_B="$BUILD_ROOT/build-b"
build_report "$BUILD_A" build-a
build_report "$BUILD_B" build-b
BUILT="$BUILD_A/ksg-m1a-composite-v5-boundary.pdf"
cmp -s "$BUILT" "$BUILD_B/ksg-m1a-composite-v5-boundary.pdf" || \
  fail "two clean LaTeX builds differ"

python3 -I -B - "$BUILT" "$PDF" "$FIGURE_A" "$FIGURE_PDF" "$EXPECTED_PAGES" "$EXPECTED_FIGURE_PAGE" <<'PY'
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import sys

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, FloatObject, NameObject, NumberObject, RectangleObject, TextStringObject


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v5 boundary PDF check: PDF structure {detail}")


def resolve(value: object) -> object:
    return value.get_object() if hasattr(value, "get_object") else value


def box(value: object) -> tuple[float, float, float, float]:
    return tuple(float(item) for item in value)  # type: ignore[arg-type,return-value]


def close_box(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    return len(left) == len(right) and all(abs(a - b) <= 0.02 for a, b in zip(left, right))


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


def transform(
    matrix: tuple[float, float, float, float, float, float], x: float, y: float
) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return a * x + c * y + e, b * x + d * y + f


def validate_action(value: object, report: PdfReader) -> None:
    value = resolve(value)
    if not isinstance(value, DictionaryObject) or str(value.get("/S")) != "/GoTo":
        raise ValueError("catalog OpenAction is not the bounded internal GoTo")
    destination = resolve(value.get("/D"))
    if not isinstance(destination, ArrayObject) or len(destination) != 2 or str(destination[1]) != "/Fit":
        raise ValueError("catalog OpenAction destination changed")
    target = destination[0]
    expected = report.pages[0].indirect_reference
    if not hasattr(target, "idnum") or expected is None or target.idnum != expected.idnum:
        raise ValueError("catalog OpenAction does not target the first page")


def font_families(resources: object) -> set[str]:
    resources = resolve(resources)
    if not isinstance(resources, DictionaryObject):
        raise ValueError("figure resources are not a dictionary")
    fonts = resolve(resources.get("/Font"))
    if not isinstance(fonts, DictionaryObject) or not fonts:
        raise ValueError("figure fonts are absent")
    result: set[str] = set()
    for reference in fonts.values():
        font = resolve(reference)
        name = str(font.get("/BaseFont", "")).removeprefix("/")
        prefix, plus, suffix = name.partition("+")
        if plus and len(prefix) == 6 and prefix.isalpha() and prefix.isupper():
            name = suffix
        result.add(name)
        if str(font.get("/Subtype")) != "/Type1" or font.get("/ToUnicode") is None:
            raise ValueError("figure font subtype or Unicode mapping changed")
        descriptor = resolve(font.get("/FontDescriptor"))
        if not isinstance(descriptor, DictionaryObject):
            raise ValueError("figure font descriptor is absent")
        programs = [descriptor.get(key) for key in ("/FontFile", "/FontFile2", "/FontFile3") if descriptor.get(key) is not None]
        if len(programs) != 1 or not resolve(programs[0]).get_data():
            raise ValueError("figure font is not embedded")
    return result


def forms(reader: PdfReader) -> list[tuple[int, str, object]]:
    found: list[tuple[int, str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        resources = resolve(page.get("/Resources"))
        xobjects = {} if not isinstance(resources, DictionaryObject) else resolve(resources.get("/XObject", {}))
        for name, reference in xobjects.items():
            value = resolve(reference)
            if value.get("/Subtype") == "/Form":
                found.append((page_number, str(name), value))
    return found


def validate(report: PdfReader, figure: PdfReader, expected_pages: int, figure_page: int) -> None:
    if len(report.pages) != expected_pages or len(figure.pages) != 1:
        raise ValueError("page inventory changed")
    root = report.trailer["/Root"]
    for forbidden in ("/AcroForm", "/JavaScript", "/AA"):
        if root.get(forbidden) is not None:
            raise ValueError(f"catalog contains {forbidden}")
    open_action = root.get("/OpenAction")
    if open_action is not None:
        validate_action(open_action, report)
    names = resolve(root.get("/Names", {}))
    if isinstance(names, DictionaryObject) and any(key in names for key in ("/JavaScript", "/EmbeddedFiles")):
        raise ValueError("catalog Names contains executable or embedded content")
    figure_root = figure.trailer["/Root"]
    if any(figure_root.get(key) is not None for key in ("/AcroForm", "/AA", "/OpenAction", "/Names")):
        raise ValueError("standalone figure catalog contains an action, name tree, or form")
    a4 = (0.0, 0.0, 595.276, 841.89)
    for number, page in enumerate(report.pages, start=1):
        if page.get("/Annots") is not None:
            raise ValueError(f"page {number} contains annotations")
        if page.get("/AA") is not None:
            raise ValueError(f"page {number} contains an additional action")
        if not close_box(box(page.mediabox), a4) or not close_box(box(page.cropbox), a4):
            raise ValueError(f"page {number} is not zero-origin A4")
        if int(page.get("/Rotate", 0)) != 0 or float(page.get("/UserUnit", 1)) != 1.0:
            raise ValueError(f"page {number} rotation or UserUnit changed")
    standalone = figure.pages[0]
    expected_figure_box = (0.0, 0.0, 453.543307, 255.11811)
    if standalone.get("/Annots") is not None or standalone.get("/AA") is not None:
        raise ValueError("standalone figure contains annotations or additional actions")
    if not close_box(box(standalone.mediabox), expected_figure_box) or not close_box(
        box(standalone.cropbox), expected_figure_box
    ):
        raise ValueError("standalone figure page box changed")
    if int(standalone.get("/Rotate", 0)) != 0 or float(standalone.get("/UserUnit", 1)) != 1.0:
        raise ValueError("standalone figure rotation or UserUnit changed")
    found = forms(report)
    if len(found) != 1 or found[0][0] != figure_page:
        raise ValueError("figure Form is not unique on page 3")
    _page, name, form = found[0]
    matrix = form.get("/Matrix")
    if matrix is not None and tuple(float(item) for item in matrix) != (1, 0, 0, 1, 0, 0):
        raise ValueError("figure Form Matrix is nonidentity")
    if form.get_data() != standalone.get_contents().get_data():
        raise ValueError("embedded Form content differs from standalone figure")
    if not close_box(box(form.get("/BBox")), box(standalone.mediabox)):
        raise ValueError("embedded Form BBox differs from standalone figure")
    if font_families(form.get("/Resources")) != font_families(standalone.get("/Resources")):
        raise ValueError("embedded/standalone font-family inventories differ")
    page = report.pages[figure_page - 1]
    operations = pypdf.generic.ContentStream(page.get_contents(), report).operations
    current = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    stack: list[tuple[float, float, float, float, float, float]] = []
    invocations: list[tuple[int, tuple[float, float, float, float, float, float]]] = []
    for index, (operands, operator) in enumerate(operations):
        if operator == b"q":
            stack.append(current)
        elif operator == b"Q":
            if not stack:
                raise ValueError("page graphics-state stack underflowed")
            current = stack.pop()
        elif operator == b"cm":
            current = concatenate(current, tuple(float(item) for item in operands))
        elif operator == b"Do" and str(operands[0]) == name:
            invocations.append((index, current))
    if stack or len(invocations) != 1:
        raise ValueError("figure Form invocation or graphics-state balance changed")
    invocation_index, placement = invocations[0]
    if any(op in {b"W", b"W*"} for _operands, op in operations[:invocation_index]):
        raise ValueError("figure Form is preceded by a clipping operator")
    form_box = box(form.get("/BBox"))
    points = [
        transform(placement, form_box[0], form_box[1]),
        transform(placement, form_box[0], form_box[3]),
        transform(placement, form_box[2], form_box[1]),
        transform(placement, form_box[2], form_box[3]),
    ]
    left, bottom = min(point[0] for point in points), min(point[1] for point in points)
    right, top = max(point[0] for point in points), max(point[1] for point in points)
    if left < 0 or bottom < 0 or right > a4[2] or top > a4[3] or right - left < 400 or top - bottom < 200:
        raise ValueError("figure Form placement is clipped, off-page, or unexpectedly scaled")


if pypdf.__version__ != "6.15.0":
    fail(f"requires pypdf 6.15.0, observed {pypdf.__version__}")
repo = Path.cwd().resolve()
if repo in Path(pypdf.__file__).resolve().parents:
    fail("pypdf resolved from inside the repository")
reports = [Path(sys.argv[1]), Path(sys.argv[2])]
figures = [Path(sys.argv[3]), Path(sys.argv[4])]
pages = int(sys.argv[5])
figure_page = int(sys.argv[6])
try:
    for report_path in reports:
        for figure_path in figures:
            validate(PdfReader(report_path, strict=True), PdfReader(figure_path, strict=True), pages, figure_page)
except Exception as error:
    fail(str(error))

# Exact hostile objects exercise the predicates, rather than a checksum-only rejection.
raw = reports[0].read_bytes()
figure = PdfReader(figures[0], strict=True)
wrong_box = PdfReader(BytesIO(raw), strict=True)
wrong_box.pages[-1].mediabox = RectangleObject((0, 0, 612, 792))
annotated = PdfReader(BytesIO(raw), strict=True)
annotated.pages[0][NameObject("/Annots")] = ArrayObject([DictionaryObject({
    NameObject("/Type"): NameObject("/Annot"), NameObject("/Subtype"): NameObject("/Link"),
    NameObject("/Rect"): RectangleObject((10, 10, 20, 20)),
    NameObject("/A"): DictionaryObject({NameObject("/S"): NameObject("/URI"), NameObject("/URI"): TextStringObject("relative.json")}),
})])
matrix = PdfReader(BytesIO(raw), strict=True)
matrix_form = forms(matrix)[0][2]
matrix_form[NameObject("/Matrix")] = ArrayObject([FloatObject(1), FloatObject(0), FloatObject(0), FloatObject(1), FloatObject(10000), FloatObject(0)])
zero_writer = PdfWriter(clone_from=BytesIO(raw))
zero_page = zero_writer.pages[figure_page - 1]
zero_name = forms(zero_writer)[0][1]
zero_stream = pypdf.generic.ContentStream(zero_page.get_contents(), zero_writer)
zero_indices = [index for index, (operands, op) in enumerate(zero_stream.operations) if op == b"Do" and str(operands[0]) == zero_name]
if len(zero_indices) != 1:
    fail("page-transform hostile cannot locate the figure invocation")
zero_stream.operations[zero_indices[0]:zero_indices[0]] = [
    ([NumberObject(0), NumberObject(0), NumberObject(0), NumberObject(0), NumberObject(0), NumberObject(0)], b"cm")
]
zero_page.replace_contents(zero_stream)
zero_buffer = BytesIO()
zero_writer.write(zero_buffer)
zero_writer.close()
zero_scale = PdfReader(BytesIO(zero_buffer.getvalue()), strict=True)
scripted = PdfReader(BytesIO(raw), strict=True)
scripted.trailer["/Root"][NameObject("/OpenAction")] = DictionaryObject({
    NameObject("/S"): NameObject("/JavaScript"),
    NameObject("/JS"): TextStringObject("app.alert('unsafe')"),
})
relocated = PdfReader(BytesIO(raw), strict=True)
source_resources = resolve(relocated.pages[figure_page - 1]["/Resources"])
target_resources = resolve(relocated.pages[figure_page]["/Resources"])
target_resources[NameObject("/XObject")] = source_resources.pop(NameObject("/XObject"))
for hostile in (wrong_box, annotated, matrix, zero_scale, scripted, relocated):
    try:
        validate(hostile, figure, pages, figure_page)
    except ValueError:
        pass
    else:
        fail("an object-structure hostile control was accepted")
rotated_figure = PdfReader(figures[0], strict=True)
rotated_figure.pages[0][NameObject("/Rotate")] = NumberObject(90)
try:
    validate(PdfReader(reports[0], strict=True), rotated_figure, pages, figure_page)
except ValueError:
    pass
else:
    fail("the standalone-figure geometry hostile control was accepted")
PY

for candidate in "$FIGURE_A" "$FIGURE_PDF" "$BUILT" "$PDF"; do
  pdffonts "$candidate" | awk '
    NR > 2 { seen=1; if ($(NF-4)!="yes" || $(NF-3)!="yes" || $(NF-2)!="yes") bad=1 }
    END { exit (!seen || bad) }
  ' || fail "every font must be embedded, subset, and Unicode-mapped: $candidate"
done

pdftotext "$BUILT" "$BUILD_ROOT/built.semantic.txt"
python3 -I -S - "$BUILD_ROOT/built.semantic.txt" "$BUILD_ROOT/built.semantic.normalized.txt" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[2]).write_text(
    " ".join(Path(sys.argv[1]).read_text(encoding="utf-8").split()) + "\n",
    encoding="utf-8",
    newline="\n",
)
PY
required_text=(
  "Q4 = CI4 ∧ CodeQL4 ∧ D4"
  "CI4 = false"
  "R4 is permanently unissued"
  "C5 is the exact unsigned direct child of C4"
  "Q5 = L5 ∧ CI5 ∧ CodeQL5 ∧ D5"
  "repository-CI all-jobs success"
  "success of every required CodeQL role"
  "dedicated composite-v5 workflow"
  "issue(R5) ⇐⇒ Q5"
  "remote URL, ref, commit OID"
  "predecessor and successor captures"
  "zero PID theories, zero PID functionals, zero estimators"
  "Legacy recovery wiring"
  "stale README-token expectation"
  "Nothing here transfers evidence"
  "not a KSG proof, PID validation, authentication"
)
for sentinel in "${required_text[@]}"; do
  grep -F -- "$sentinel" "$BUILD_ROOT/built.semantic.normalized.txt" >/dev/null || \
    fail "required PDF text is absent: $sentinel"
done
for page in $(seq 1 "$EXPECTED_PAGES"); do
  pdftotext -f "$page" -l "$page" "$BUILT" "$BUILD_ROOT/page-$page.txt"
  if [[ "$page" == "$EXPECTED_FIGURE_PAGE" ]]; then
    grep -F -- "Append-only qualification boundary" "$BUILD_ROOT/page-$page.txt" >/dev/null || \
      fail "figure caption is absent from page $page"
    grep -F -- "R4 UNISSUED" "$BUILD_ROOT/page-$page.txt" >/dev/null || \
      fail "figure text is absent from page $page"
  elif grep -F -- "R4 UNISSUED" "$BUILD_ROOT/page-$page.txt" >/dev/null; then
    fail "figure text appears outside page $EXPECTED_FIGURE_PAGE"
  fi
done

render_pages() {
  local input="$1" output="$2" label="$3" mode="$4"
  local -a command=(pdftoppm -png -r "$RENDER_DPI")
  [[ "$mode" == color ]] || command+=(-gray)
  mkdir -p "$output"
  if ! env -i PATH="$PATH" LC_ALL=C LANG=C TZ=UTC HOME="$BUILD_ROOT" TMPDIR="$BUILD_ROOT" \
    "${command[@]}" "$input" "$output/page" >"$BUILD_ROOT/$label.stdout" 2>"$BUILD_ROOT/$label.stderr"; then
    cat "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr" >&2
    fail "Poppler rendering failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label.stdout" && ! -s "$BUILD_ROOT/$label.stderr" ]] || {
    cat "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr" >&2
    fail "Poppler emitted a rendering diagnostic: $label"
  }
}

compare_sets() {
  python3 -I -S "$COMPARATOR" --left-dir "$1" --right-dir "$2" --pages "$3" \
    --label "$4" --receipt "$5" --large-delta 24 --max-mean-abs 0.20 \
    --max-changed-fraction 0.01 --max-large-fraction 0.001
}

BUILT_COLOR="$BUILD_ROOT/built-color"
BUILT_GRAY="$BUILD_ROOT/built-gray"
COMMITTED_COLOR="$BUILD_ROOT/committed-color"
COMMITTED_GRAY="$BUILD_ROOT/committed-gray"
BUILT_FIGURE_COLOR="$BUILD_ROOT/built-figure-color"
BUILT_FIGURE_GRAY="$BUILD_ROOT/built-figure-gray"
COMMITTED_FIGURE_COLOR="$BUILD_ROOT/committed-figure-color"
COMMITTED_FIGURE_GRAY="$BUILD_ROOT/committed-figure-gray"
render_pages "$BUILT" "$BUILT_COLOR" built-color color
render_pages "$BUILT" "$BUILT_GRAY" built-gray gray
render_pages "$PDF" "$COMMITTED_COLOR" committed-color color
render_pages "$PDF" "$COMMITTED_GRAY" committed-gray gray
render_pages "$FIGURE_A" "$BUILT_FIGURE_COLOR" built-figure-color color
render_pages "$FIGURE_A" "$BUILT_FIGURE_GRAY" built-figure-gray gray
render_pages "$FIGURE_PDF" "$COMMITTED_FIGURE_COLOR" committed-figure-color color
render_pages "$FIGURE_PDF" "$COMMITTED_FIGURE_GRAY" committed-figure-gray gray
if [[ "$MODE" == "--cross-toolchain" ]]; then
  compare_sets "$BUILT_COLOR" "$COMMITTED_COLOR" "$EXPECTED_PAGES" report-color "$BUILD_ROOT/report-color.tsv"
  compare_sets "$BUILT_GRAY" "$COMMITTED_GRAY" "$EXPECTED_PAGES" report-gray "$BUILD_ROOT/report-gray.tsv"
  compare_sets "$BUILT_FIGURE_COLOR" "$COMMITTED_FIGURE_COLOR" 1 figure-color "$BUILD_ROOT/figure-color.tsv"
  compare_sets "$BUILT_FIGURE_GRAY" "$COMMITTED_FIGURE_GRAY" 1 figure-gray "$BUILD_ROOT/figure-gray.tsv"
fi

generate_receipt() {
  python3 -I -S - "$1" "$2" "$3" "$4" "$EXPECTED_PAGES" "$RENDER_DPI" <<'PY'
from __future__ import annotations
import hashlib
from pathlib import Path
import struct
import sys
import zlib

def fail(detail: str) -> None:
    raise SystemExit(f"composite-v5 boundary PDF check: rendering receipt {detail}")

def paeth(a: int, b: int, c: int) -> int:
    p=a+b-c; values=(abs(p-a),abs(p-b),abs(p-c)); return (a,b,c)[values.index(min(values))]

def inspect(path: Path, mode: str) -> tuple[int,int,int,int,int,int]:
    data=path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"): fail(f"{path.name} is not PNG")
    offset=8; chunks=bytearray(); width=height=depth=color=interlace=None
    while offset < len(data):
        length=struct.unpack(">I",data[offset:offset+4])[0]; kind=data[offset+4:offset+8]
        payload=data[offset+8:offset+8+length]
        if len(payload)!=length: fail(f"{path.name} is truncated")
        if kind==b"IHDR": width,height,depth,color,_,_,interlace=struct.unpack(">IIBBBBB",payload)
        elif kind==b"IDAT": chunks.extend(payload)
        elif kind==b"IEND": break
        offset += 12+length
    if (width,height)!=(993,1404) or depth!=8 or interlace!=0 or color not in {0,2}:
        fail(f"{path.name} PNG geometry/encoding changed")
    channels={0:1,2:3}[color]; stride=width*channels; raw=zlib.decompress(bytes(chunks))
    if len(raw)!=height*(stride+1): fail(f"{path.name} decoded length changed")
    previous=bytearray(stride); cursor=0; low=255; high=0; dark=0; chroma=0
    for _ in range(height):
        kind=raw[cursor]; scan=raw[cursor+1:cursor+1+stride]; cursor+=stride+1; row=bytearray(stride)
        for i,value in enumerate(scan):
            left=row[i-channels] if i>=channels else 0; up=previous[i]; corner=previous[i-channels] if i>=channels else 0
            predicted={0:lambda:0,1:lambda:left,2:lambda:up,3:lambda:(left+up)//2,4:lambda:paeth(left,up,corner)}.get(kind)
            if predicted is None: fail(f"{path.name} uses unsupported filter")
            row[i]=(value+predicted())&255
        for i in range(0,stride,channels):
            if color==2:
                r,g,b=row[i:i+3]; chroma += max(r,g,b)-min(r,g,b)>2; lum=(299*r+587*g+114*b)//1000
                if mode=="gray" and not (r==g==b): fail(f"{path.name} gray render retained chroma")
            else: lum=row[i]
            low=min(low,lum); high=max(high,lum); dark += lum<230
        previous=row
    if high-low<30 or dark<500: fail(f"{path.name} appears blank")
    if mode=="color" and chroma<500: fail(f"{path.name} lacks color content")
    if mode=="gray" and chroma: fail(f"{path.name} grayscale has chroma")
    return width,height,low,high,dark,chroma

pdf=Path(sys.argv[1]); color=Path(sys.argv[2]); gray=Path(sys.argv[3]); out=Path(sys.argv[4]); pages=int(sys.argv[5]); dpi=int(sys.argv[6])
rows=["schema\tpid-rs-formal-rendering-receipt-v2\n",f"pdf_sha256\t{hashlib.sha256(pdf.read_bytes()).hexdigest()}\n",f"pages\t{pages}\n",f"dpi\t{dpi}\n","mode\tpage\twidth\theight\tbytes\tsha256\tmin_luma\tmax_luma\tdark_pixels\tchromatic_pixels\n"]
for mode,directory in (("color",color),("gray",gray)):
    paths=sorted(directory.glob("page-*.png"))
    if len(paths)!=pages: fail(f"{mode} page inventory changed")
    for number,path in enumerate(paths,1):
        width,height,low,high,dark,chroma=inspect(path,mode); data=path.read_bytes()
        rows.append(f"{mode}\t{number}\t{width}\t{height}\t{len(data)}\t{hashlib.sha256(data).hexdigest()}\t{low}\t{high}\t{dark}\t{chroma}\n")
out.write_text("".join(rows),encoding="utf-8",newline="\n")
PY
}
generate_receipt "$BUILT" "$BUILT_COLOR" "$BUILT_GRAY" "$BUILD_ROOT/built.rendering.tsv"
generate_receipt "$PDF" "$COMMITTED_COLOR" "$COMMITTED_GRAY" "$BUILD_ROOT/committed.rendering.tsv"
python3 -I -S - "$RENDERING_RECEIPT" "$PDF" "$EXPECTED_PAGES" "$RENDER_DPI" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

receipt = Path(sys.argv[1])
pdf = Path(sys.argv[2])
pages = int(sys.argv[3])
dpi = int(sys.argv[4])
raw = receipt.read_bytes()
if not raw.endswith(b"\n") or b"\r" in raw:
    raise SystemExit("composite-v5 boundary PDF check: rendering receipt framing changed")
lines = raw.decode("utf-8", errors="strict").splitlines()
if len(lines) != 5 + 2 * pages:
    raise SystemExit("composite-v5 boundary PDF check: rendering receipt row count changed")
expected_prefix = (
    "schema\tpid-rs-formal-rendering-receipt-v2",
    f"pdf_sha256\t{hashlib.sha256(pdf.read_bytes()).hexdigest()}",
    f"pages\t{pages}",
    f"dpi\t{dpi}",
    "mode\tpage\twidth\theight\tbytes\tsha256\tmin_luma\tmax_luma\tdark_pixels\tchromatic_pixels",
)
if tuple(lines[:5]) != expected_prefix:
    raise SystemExit("composite-v5 boundary PDF check: rendering receipt header/PDF binding changed")
sha = re.compile(r"[0-9a-f]{64}")
uint = re.compile(r"0|[1-9][0-9]*")
expected_order = [(mode, page) for mode in ("color", "gray") for page in range(1, pages + 1)]

def canonical_uint(text: str, label: str) -> int:
    if uint.fullmatch(text) is None:
        raise ValueError(f"{label} is not a canonical unsigned integer")
    return int(text)

def validate_rows(candidate: list[str]) -> None:
    if tuple(candidate[:5]) != expected_prefix or len(candidate) != 5 + 2 * pages:
        raise ValueError("header or row inventory changed")
    for expected, line in zip(expected_order, candidate[5:], strict=True):
        row = line.split("\t")
        if len(row) != 10:
            raise ValueError("row shape changed")
        page = canonical_uint(row[1], "page")
        if (row[0], page) != expected:
            raise ValueError("row order changed")
        width, height, byte_count = (
            canonical_uint(row[index], label)
            for index, label in ((2, "width"), (3, "height"), (4, "byte count"))
        )
        low, high, dark, chroma = (
            canonical_uint(row[index], label)
            for index, label in (
                (6, "minimum luminance"),
                (7, "maximum luminance"),
                (8, "dark-pixel count"),
                (9, "chromatic-pixel count"),
            )
        )
        pixels = width * height
        if (width, height) != (993, 1404) or not (
            1024 <= byte_count <= 20 * 1024 * 1024
        ):
            raise ValueError("geometry or byte size is implausible")
        if sha.fullmatch(row[5]) is None or not (
            0 <= low <= high <= 255 and high - low >= 30 and 500 <= dark <= pixels
        ):
            raise ValueError("digest or contrast is implausible")
        if row[0] == "color" and not (500 <= chroma <= pixels):
            raise ValueError("color row chroma is implausible")
        if row[0] == "gray" and chroma != 0:
            raise ValueError("grayscale row retains chroma")

try:
    validate_rows(lines)
except ValueError as error:
    raise SystemExit(
        f"composite-v5 boundary PDF check: rendering receipt {error}"
    ) from error

hostiles: list[list[str]] = []
noncanonical = list(lines)
row = noncanonical[5].split("\t")
row[1] = "01"
noncanonical[5] = "\t".join(row)
hostiles.append(noncanonical)
impossible = list(lines)
row = impossible[5].split("\t")
row[8] = str(993 * 1404 + 1)
impossible[5] = "\t".join(row)
hostiles.append(impossible)
for hostile in hostiles:
    try:
        validate_rows(hostile)
    except ValueError:
        pass
    else:
        raise SystemExit(
            "composite-v5 boundary PDF check: rendering receipt hostile was accepted"
        )
PY

if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$BUILT" "$PDF" || fail "committed report PDF is stale or not reproducible"
  cmp -s "$BUILD_ROOT/committed.rendering.tsv" "$RENDERING_RECEIPT" || \
    fail "committed rendering receipt does not bind the committed 120-dpi color/gray renders"
  cmp -s "$BUILD_ROOT/built.rendering.tsv" "$RENDERING_RECEIPT" || \
    fail "rendering receipt is stale or not reproducible"
else
  pdftotext -layout "$BUILT" "$BUILD_ROOT/built.layout.txt"
  pdftotext -layout "$PDF" "$BUILD_ROOT/committed.layout.txt"
  cmp -s "$BUILD_ROOT/built.layout.txt" "$BUILD_ROOT/committed.layout.txt" || \
    fail "report text/layout changed across toolchains"
fi

python3 -I -S - "$VISUAL_RECEIPT" "$PDF" "$RENDERING_RECEIPT" "$SVG" "$FIGURE_PDF" <<'PY'
from __future__ import annotations
import hashlib
from pathlib import Path
import re
import sys

def fail(detail: str) -> None:
    raise SystemExit(f"composite-v5 boundary PDF check: visual receipt {detail}")

receipt,pdf,rendering,svg,figure=map(Path,sys.argv[1:])
raw=receipt.read_bytes()
if not raw.endswith(b"\n") or b"\r" in raw or len(raw)>16384: fail("byte framing changed")
text=raw.decode("utf-8",errors="strict"); lines=text.splitlines()
if lines[:2] != ["# Composite-v5 successor-boundary PDF visual-review receipt",""]: fail("title changed")
order=("schema","subject","pdf_sha256","rendering_receipt","rendering_receipt_sha256","figure_svg","figure_svg_sha256","figure_pdf","figure_pdf_sha256","pages","dpi","color_pages_reviewed","grayscale_pages_reviewed","figure_pages_reviewed","status","review_date_utc","reviewer_kind")
fields={}
for offset,name in enumerate(order,2):
    match=re.fullmatch(rf"{re.escape(name)}: `([^`]+)`",lines[offset]) if offset<len(lines) else None
    if match is None: fail(f"field order/syntax changed at {name}")
    fields[name]=match.group(1)
def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
expected={
 "schema":"pid-rs/composite-v5-boundary-visual-review/v1",
 "subject":"output/pdf/ksg-m1a-composite-v5-boundary.pdf","pdf_sha256":digest(pdf),
 "rendering_receipt":"output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv","rendering_receipt_sha256":digest(rendering),
 "figure_svg":"audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg","figure_svg_sha256":digest(svg),
 "figure_pdf":"audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf","figure_pdf_sha256":digest(figure),
 "pages":"4","dpi":"144","color_pages_reviewed":"1-4","grayscale_pages_reviewed":"1-4","figure_pages_reviewed":"3",
 "status":"passed","review_date_utc":"2026-08-18","reviewer_kind":"root-agent-visual-inspection",
}
for name,value in expected.items():
    if fields.get(name)!=value: fail(f"field {name} differs")
body_start=3+len(order)
paragraphs=tuple(" ".join(part.split()) for part in "\n".join(lines[body_start:]).strip().split("\n\n") if part.strip())
required=(
 "All four final color pages and all four final grayscale pages were viewed in page order at 144 dpi.",
 "The successor-boundary figure on page 3 was also reviewed at its native 1600-by-900-pixel size in color. Its failure, nonissuance, repair, fresh-qualification, receipt, and nonimplication states are distinguished by text, borders, line styles, and shape as well as color.",
 "Page 1 was checked for title hierarchy, the bounded disposition box, complete definitions of `Q4` and R4 issuance, and legible commit identity.",
 "Page 2 was checked for complete hosted-observation and repair tables, honest separation of exact causal findings from the release-fixture uncertainty, intact hashes, and a non-orphaned section transition.",
 "Page 3 was checked for complete definitions of `Q5` and R5 issuance, a clean native figure, nonoverlapping arrows and badges, legible caption, and correct reading order from qualification to receipt custody.",
 "Page 4 was checked for the r9/r10 numbering boundary, remote-main durability limitation, the twenty named review lenses, and the terminal zero-science/nontransfer statements.",
 "The final PDF contains no annotations, widgets, form field tree, JavaScript, or live relative URI. All four pages are zero-rotation A4 pages.",
 "No blank, clipped, overlapping, misordered, orphaned, or visibly corrupt page, table, equation, or figure element was observed. Color meaning remained distinguishable in grayscale.",
 "The root agent completed this bounded visual inspection. It grants neither human-review nor dependency-disjoint independence credit.",
 "This receipt binds the exact reviewed PDF, figure sources, and deterministic 120-dpi rendering receipt. It does not prove mathematical correctness, PDF/UA accessibility, renderer independence, provider authenticity, scientific validity, or archival preservation.",
)
def validate_body(candidate: tuple[str, ...]) -> None:
    if candidate != required:
        raise ValueError("body paragraph inventory or order changed")

try:
    validate_body(paragraphs)
except ValueError as error:
    fail(str(error))
for hostile in (required+("Contradictory extra claim.",),required[:-1],(required[1],required[0],*required[2:])):
    try:
        validate_body(hostile)
    except ValueError:
        pass
    else:
        fail("closed-body hostile control was accepted")
PY

digest="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite-v5 boundary PDF has exact source, vector, object, render, receipt, and same-toolchain custody ($digest)"
else
  echo "OK: composite-v5 boundary PDF has exact source/receipt custody and bounded same-renderer cross-toolchain agreement ($digest)"
fi
