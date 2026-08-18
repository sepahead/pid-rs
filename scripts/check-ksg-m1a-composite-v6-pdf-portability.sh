#!/usr/bin/env bash
set -euo pipefail

# Append-only portability adjudication for the two immutable composite publications.
# This checker does not amend either publication gate.  In exact mode it first replays
# both historical exact gates.  Its cross-toolchain relation is deliberately narrower:
# each rebuilt/committed report is checked only against the committed figure named by
# that report's TeX source.  The freshly rendered SVG figure is a separate portability
# peer of that committed figure.  The publication relation is keyed, never Cartesian.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
COMPARATOR="scripts/compare-formal-pdf-renders.py"
COMPARATOR_SHA256="7b230bef4371398c18a3975d6888207bc31a737eeffb0217f3d5bbc0aec3054b"
COMPARATOR_BYTES=16408
RENDER_DPI=120

# The raster comparisons below are bounded same-renderer differential evidence.
# They are not PDF/UA or accessibility certification, renderer independence,
# universal visual equivalence, source authenticity, or scientific qualification.

fail() {
  echo "composite publication PDF v6 adjudication: $*" >&2
  exit 1
}

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in awk bash cmp cp env fc-cache kpsewhich lacheck latexmk mkdir \
  pdffonts pdfinfo pdftoppm pdftotext python3 rg rsvg-convert shasum sort wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite publication PDF v6 adjudication: missing command: $command" >&2
    exit 2
  }
done

cd "$ROOT"
for historical_gate in \
  scripts/check-ksg-m1a-composite-v4-process-pdf.sh \
  scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh; do
  [[ -f "$historical_gate" && ! -L "$historical_gate" ]] || \
    fail "immutable gate is absent, nonregular, or a symlink: $historical_gate"
  bash -n "$historical_gate"
done
[[ -f "$COMPARATOR" && ! -L "$COMPARATOR" ]] || fail "render comparator is absent or unsafe"
[[ "$(wc -c <"$COMPARATOR" | tr -d '[:space:]')" == "$COMPARATOR_BYTES" ]] || \
  fail "render comparator byte count changed"
[[ "$(shasum -a 256 "$COMPARATOR" | awk '{print $1}')" == "$COMPARATOR_SHA256" ]] || \
  fail "render comparator SHA-256 changed"

# Exact replay remains delegated to the immutable gates that own exact source,
# publication, rendering-receipt, and visual-receipt custody.  Cross mode does not
# invoke their older all-pairs relation; the independent keyed relation below is the
# append-only portability adjudication.
if [[ "$MODE" == "--exact" ]]; then
  scripts/check-ksg-m1a-composite-v4-process-pdf.sh --exact >/dev/null
  scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh --exact >/dev/null
fi

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-composite-publication-v6-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_ROOT"' EXIT

FONT_ROOT="$BUILD_ROOT/fonts"
FONT_CACHE="$BUILD_ROOT/font-cache"
FONT_CONFIG="$BUILD_ROOT/fonts.conf"
mkdir -p "$FONT_ROOT" "$FONT_CACHE"
for font_name in SourceSansPro-Bold.otf SourceSansPro-Semibold.otf lmroman10-regular.otf; do
  font_path="$(kpsewhich --must-exist "$font_name" || true)"
  [[ -n "$font_path" && -f "$font_path" ]] || {
    echo "composite publication PDF v6 adjudication: required font unavailable: $font_name" >&2
    exit 2
  }
  cp "$font_path" "$FONT_ROOT/$font_name"
done
python3 -I -S - "$FONT_CONFIG" "$FONT_ROOT" "$FONT_CACHE" <<'PY'
from pathlib import Path
import sys

Path(sys.argv[1]).write_text(
    '<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n'
    f'<fontconfig><dir>{sys.argv[2]}</dir><cachedir>{sys.argv[3]}</cachedir>'
    '<config></config></fontconfig>\n',
    encoding="utf-8",
    newline="\n",
)
PY
FONTCONFIG_FILE="$FONT_CONFIG" FONTCONFIG_PATH="$BUILD_ROOT" fc-cache -f >/dev/null

render_svg() {
  local svg="$1" output="$2" epoch="$3" label="$4"
  if ! env -i PATH="$PATH" LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$epoch" \
    FONTCONFIG_FILE="$FONT_CONFIG" FONTCONFIG_PATH="$BUILD_ROOT" \
    PANGOCAIRO_BACKEND=fc OSFONTDIR="$FONT_ROOT" \
    rsvg-convert --format=pdf --keep-aspect-ratio --output="$output" "$svg" \
    >"$BUILD_ROOT/$label.stdout" 2>"$BUILD_ROOT/$label.stderr"; then
    cat "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr" >&2
    fail "fresh figure build failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label.stdout" && ! -s "$BUILD_ROOT/$label.stderr" ]] || {
    cat "$BUILD_ROOT/$label.stdout" "$BUILD_ROOT/$label.stderr" >&2
    fail "fresh figure build emitted diagnostics: $label"
  }
}

build_report() {
  local tex="$1" output_directory="$2" epoch="$3" stem="$4"
  mkdir -p "$output_directory"
  if ! SOURCE_DATE_EPOCH="$epoch" TZ=UTC \
    TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" \
    latexmk -pdf -interaction=nonstopmode -halt-on-error -no-shell-escape \
      -outdir="$output_directory" "$tex" \
      >"$BUILD_ROOT/$stem-latexmk.stdout" 2>&1; then
    cat "$BUILD_ROOT/$stem-latexmk.stdout" >&2
    fail "fresh report build failed: $stem"
  fi
  scripts/check-formal-pdf-log.sh "$output_directory/$stem.log"
}

check_tex_reference() {
  local tex="$1" expected="$2" label="$3"
  python3 -I -S - "$tex" "$expected" "$label" <<'PY'
from pathlib import Path, PurePosixPath
import re
import sys

tex = Path(sys.argv[1])
expected = PurePosixPath(sys.argv[2])
label = sys.argv[3]
raw = tex.read_text(encoding="utf-8")
matches = re.findall(
    r"\\includegraphics\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}", raw, flags=re.DOTALL
)
if len(matches) != 1:
    raise SystemExit(
        f"composite publication PDF v6 adjudication: {label} TeX does not name exactly one literal figure"
    )
observed = PurePosixPath("audit/formal/latex") / PurePosixPath(matches[0].strip())
if observed != expected:
    raise SystemExit(
        f"composite publication PDF v6 adjudication: {label} TeX figure reference changed: {observed}"
    )
PY
}

prepare_lane() {
  local label="$1" tex="$2" svg="$3" committed_figure="$4" committed_report="$5" \
    pages="$6" figure_page="$7" epoch="$8" stem="$9"
  for path in "$tex" "$svg" "$committed_figure" "$committed_report"; do
    [[ -f "$path" && ! -L "$path" ]] || fail "$label input is absent, nonregular, or a symlink: $path"
  done
  check_tex_reference "$tex" "$committed_figure" "$label"
  if ! lacheck "$tex" >"$BUILD_ROOT/$label-lacheck.stdout" 2>&1; then
    cat "$BUILD_ROOT/$label-lacheck.stdout" >&2
    fail "$label LaTeX lint failed"
  fi
  [[ ! -s "$BUILD_ROOT/$label-lacheck.stdout" ]] || {
    cat "$BUILD_ROOT/$label-lacheck.stdout" >&2
    fail "$label LaTeX lint emitted diagnostics"
  }
  render_svg "$svg" "$BUILD_ROOT/$label-figure.pdf" "$epoch" "$label-figure-a"
  render_svg "$svg" "$BUILD_ROOT/$label-figure-repeat.pdf" "$epoch" "$label-figure-b"
  cmp -s "$BUILD_ROOT/$label-figure.pdf" "$BUILD_ROOT/$label-figure-repeat.pdf" || \
    fail "$label two isolated fresh figure builds differ"
  build_report "$tex" "$BUILD_ROOT/$label-report" "$epoch" "$stem"
  [[ -f "$BUILD_ROOT/$label-report/$stem.pdf" ]] || fail "$label fresh report is absent"
  if [[ "$MODE" == "--exact" ]]; then
    cmp -s "$BUILD_ROOT/$label-figure.pdf" "$committed_figure" || \
      fail "$label fresh figure is not exact on the maintainer toolchain"
    cmp -s "$BUILD_ROOT/$label-report/$stem.pdf" "$committed_report" || \
      fail "$label fresh report is not exact on the maintainer toolchain"
  fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$label" "$BUILD_ROOT/$label-report/$stem.pdf" "$committed_report" \
    "$BUILD_ROOT/$label-figure.pdf" "$committed_figure" "$pages" "$figure_page" \
    >>"$BUILD_ROOT/lanes.tsv"
}

: >"$BUILD_ROOT/lanes.tsv"
prepare_lane \
  v4 \
  audit/formal/latex/ksg-m1a-composite-v4-process.tex \
  audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.svg \
  audit/formal/latex/figures/ksg-m1a-composite-v4-process/c4-r4-acyclic-custody.pdf \
  output/pdf/ksg-m1a-composite-v4-process.pdf \
  9 3 1786744800 ksg-m1a-composite-v4-process
prepare_lane \
  v5 \
  audit/formal/latex/ksg-m1a-composite-v5-boundary.tex \
  audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg \
  audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf \
  output/pdf/ksg-m1a-composite-v5-boundary.pdf \
  4 3 1787004000 ksg-m1a-composite-v5-boundary

# The object validator owns the keyed report-to-committed-figure relation.  Fresh
# figures never participate in report Form binding.  It also creates the positive
# serialization fixtures and the normalization-only visibility hostile used below.
python3 -I -B - "$BUILD_ROOT/lanes.tsv" "$BUILD_ROOT" <<'PY'
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import hashlib
import sys

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    ByteStringObject,
    ContentStream,
    DecodedStreamObject,
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
    raise SystemExit(f"composite publication PDF v6 adjudication: PDF objects {detail}")


def resolve(value: object) -> object:
    return value.get_object() if isinstance(value, IndirectObject) else value


def dictionary(value: object, label: str) -> DictionaryObject:
    value = resolve(value)
    if not isinstance(value, DictionaryObject):
        raise ValueError(f"{label} is not a dictionary")
    return value


def stream_data(value: object, label: str) -> bytes:
    value = resolve(value)
    if not isinstance(value, StreamObject):
        raise ValueError(f"{label} is not a stream")
    data = value.get_data()
    if not data:
        raise ValueError(f"{label} is empty")
    return data


def box(value: object) -> tuple[float, float, float, float]:
    return tuple(float(item) for item in value)  # type: ignore[arg-type,return-value]


def close_box(left: tuple[float, ...], right: tuple[float, ...]) -> bool:
    return len(left) == len(right) and all(abs(a - b) <= 0.02 for a, b in zip(left, right))


def subset_neutral(value: object) -> str:
    name = str(value).removeprefix("/")
    prefix, plus, suffix = name.partition("+")
    return suffix if plus and len(prefix) == 6 and prefix.isalpha() and prefix.isupper() else name


def normalized_object(value: object) -> object:
    budget = [0]
    active: set[int] = set()

    def walk(current: object, depth: int) -> object:
        budget[0] += 1
        if budget[0] > 8192 or depth > 64:
            raise ValueError("resource graph exceeds its bound")
        current = resolve(current)
        if current is None or isinstance(current, NullObject):
            return ("null",)
        if isinstance(current, BooleanObject) or type(current) is bool:
            return ("bool", bool(current))
        if isinstance(current, NameObject):
            return ("name", str(current))
        if isinstance(current, TextStringObject) or type(current) is str:
            return ("text", str(current))
        if isinstance(current, ByteStringObject) or type(current) is bytes:
            return ("bytes", current.hex())
        if isinstance(current, (NumberObject, FloatObject)) or type(current) in (int, float):
            return ("number", format(float(current), ".15g"))
        identity = id(current)
        if identity in active:
            raise ValueError("resource graph contains a cycle")
        active.add(identity)
        try:
            if isinstance(current, StreamObject):
                metadata = tuple(
                    sorted(
                        (str(key), walk(item, depth + 1))
                        for key, item in current.items()
                        if str(key) not in {"/Length", "/Filter", "/DecodeParms"}
                    )
                )
                return ("stream", metadata, hashlib.sha256(current.get_data()).hexdigest())
            if isinstance(current, DictionaryObject):
                return (
                    "dict",
                    tuple(sorted((str(key), walk(item, depth + 1)) for key, item in current.items())),
                )
            if isinstance(current, (ArrayObject, list, tuple)):
                return ("array", tuple(walk(item, depth + 1) for item in current))
        finally:
            active.remove(identity)
        raise ValueError(f"unsupported resource object: {type(current).__name__}")

    return walk(value, 0)


def validate_open_action(value: object, report: PdfReader) -> None:
    action = dictionary(value, "catalog OpenAction")
    if str(action.get("/S")) != "/GoTo":
        raise ValueError("catalog OpenAction is not the bounded internal GoTo")
    destination = resolve(action.get("/D"))
    if not isinstance(destination, ArrayObject) or len(destination) != 2 or str(destination[1]) != "/Fit":
        raise ValueError("catalog OpenAction destination changed")
    target = destination[0]
    expected = report.pages[0].indirect_reference
    if not isinstance(target, IndirectObject) or expected is None or target.idnum != expected.idnum:
        raise ValueError("catalog OpenAction does not target the first page")


def validate_catalog(reader: PdfReader, label: str, *, report: bool) -> None:
    root = dictionary(reader.trailer["/Root"], f"{label} catalog")
    for forbidden in ("/AcroForm", "/JavaScript", "/AA"):
        if root.get(forbidden) is not None:
            raise ValueError(f"{label} catalog contains {forbidden}")
    names = resolve(root.get("/Names", DictionaryObject()))
    if isinstance(names, DictionaryObject) and any(
        key in names for key in ("/JavaScript", "/EmbeddedFiles")
    ):
        raise ValueError(f"{label} catalog contains an executable or embedded name tree")
    action = root.get("/OpenAction")
    if report:
        if action is not None:
            validate_open_action(action, reader)
    elif action is not None or root.get("/Names") is not None:
        raise ValueError(f"{label} standalone figure contains an action or name tree")


def font_map(resources_value: object, label: str) -> dict[str, DictionaryObject]:
    resources = dictionary(resources_value, f"{label} resources")
    fonts = dictionary(resources.get("/Font"), f"{label} fonts")
    if not fonts:
        raise ValueError(f"{label} fonts are absent")
    result: dict[str, DictionaryObject] = {}
    for reference in fonts.values():
        font = dictionary(reference, f"{label} font")
        family = subset_neutral(font.get("/BaseFont", ""))
        if family in result:
            raise ValueError(f"{label} repeats font family {family}")
        if str(font.get("/Subtype")) != "/Type1":
            raise ValueError(f"{label} font {family} subtype changed")
        stream_data(font.get("/ToUnicode"), f"{label} font {family} ToUnicode")
        descriptor = dictionary(font.get("/FontDescriptor"), f"{label} font {family} descriptor")
        programs = [
            descriptor.get(key)
            for key in ("/FontFile", "/FontFile2", "/FontFile3")
            if descriptor.get(key) is not None
        ]
        if len(programs) != 1:
            raise ValueError(f"{label} font {family} is not singly embedded")
        stream_data(programs[0], f"{label} font {family} program")
        result[family] = font
    return result


def compare_form_resources(form_value: object, figure_value: object) -> None:
    form = dictionary(form_value, "embedded Form resources")
    figure = dictionary(figure_value, "committed figure resources")
    expected = {"/ExtGState", "/Pattern", "/Font"}
    if {str(key) for key in form} != expected or {str(key) for key in figure} != expected:
        raise ValueError("figure resource-category inventory changed")
    for category in ("/ExtGState", "/Pattern"):
        if normalized_object(form[category]) != normalized_object(figure[category]):
            raise ValueError(f"embedded Form {category} differs from its committed figure")
    form_fonts = font_map(form, "embedded Form")
    figure_fonts = font_map(figure, "committed figure")
    if set(form_fonts) != set(figure_fonts):
        raise ValueError("embedded Form font families differ from its committed figure")
    for family in sorted(form_fonts):
        if stream_data(form_fonts[family].get("/ToUnicode"), f"embedded {family} ToUnicode") != \
           stream_data(figure_fonts[family].get("/ToUnicode"), f"figure {family} ToUnicode"):
            raise ValueError(f"embedded Form font {family} Unicode map changed")


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


def forms(reader: PdfReader) -> list[tuple[int, str, StreamObject]]:
    found: list[tuple[int, str, StreamObject]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        resources = dictionary(page.get("/Resources"), f"report page {page_number} resources")
        xobjects_value = resolve(resources.get("/XObject", DictionaryObject()))
        if not isinstance(xobjects_value, DictionaryObject):
            raise ValueError(f"report page {page_number} XObjects are not a dictionary")
        for name, reference in xobjects_value.items():
            value = resolve(reference)
            if isinstance(value, StreamObject) and str(value.get("/Subtype")) == "/Form":
                found.append((page_number, str(name), value))
    return found


def validate_figure(
    reader: PdfReader, label: str
) -> tuple[tuple[float, float, float, float], frozenset[str]]:
    validate_catalog(reader, label, report=False)
    if len(reader.pages) != 1:
        raise ValueError(f"{label} page inventory changed")
    page = reader.pages[0]
    if page.get("/Annots") is not None or page.get("/AA") is not None:
        raise ValueError(f"{label} contains annotations or additional actions")
    media = box(page.mediabox)
    crop = box(page.cropbox)
    if media[0:2] != (0.0, 0.0) or not close_box(media, crop) or media[2] <= 0 or media[3] <= 0:
        raise ValueError(f"{label} page geometry is unsafe")
    if int(page.get("/Rotate", 0)) != 0 or float(page.get("/UserUnit", 1)) != 1.0:
        raise ValueError(f"{label} rotation or UserUnit changed")
    stream_data(page.get_contents(), f"{label} page content")
    resources = dictionary(page.get("/Resources"), f"{label} resources")
    if {str(key) for key in resources} != {"/ExtGState", "/Pattern", "/Font"}:
        raise ValueError(f"{label} resource-category inventory changed")
    families = frozenset(font_map(resources, label))
    return media, families


def validate_report(
    report: PdfReader,
    committed_figure: PdfReader,
    expected_pages: int,
    figure_page: int,
    label: str,
) -> None:
    validate_catalog(report, label, report=True)
    figure_box, _figure_families = validate_figure(committed_figure, f"{label} committed figure")
    if len(report.pages) != expected_pages:
        raise ValueError(f"{label} page inventory changed")
    a4 = (0.0, 0.0, 595.276, 841.89)
    for number, page in enumerate(report.pages, start=1):
        if page.get("/Annots") is not None or page.get("/AA") is not None:
            raise ValueError(f"{label} page {number} contains annotations or actions")
        if not close_box(box(page.mediabox), a4) or not close_box(box(page.cropbox), a4):
            raise ValueError(f"{label} page {number} is not zero-origin portrait A4")
        if int(page.get("/Rotate", 0)) != 0 or float(page.get("/UserUnit", 1)) != 1.0:
            raise ValueError(f"{label} page {number} rotation or UserUnit changed")
    found = forms(report)
    if len(found) != 1 or found[0][0] != figure_page:
        raise ValueError(f"{label} figure Form is not unique on page {figure_page}")
    _page_number, form_name, form = found[0]
    matrix = form.get("/Matrix")
    if matrix is not None and tuple(float(item) for item in matrix) != (1, 0, 0, 1, 0, 0):
        raise ValueError(f"{label} figure Form Matrix is nonidentity")
    standalone = committed_figure.pages[0]
    if form.get_data() != stream_data(standalone.get_contents(), "committed figure content"):
        raise ValueError(f"{label} report Form is not exact-bound to its committed TeX figure")
    form_box = box(form.get("/BBox"))
    if not close_box(form_box, figure_box):
        raise ValueError(f"{label} report Form BBox differs from its committed TeX figure")
    compare_form_resources(form.get("/Resources"), standalone.get("/Resources"))
    if normalized_object(form.get("/Group")) != normalized_object(standalone.get("/Group")):
        raise ValueError(f"{label} report Form group differs from its committed TeX figure")

    page = report.pages[figure_page - 1]
    operations = ContentStream(page.get_contents(), report).operations
    current = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
    stack: list[tuple[float, float, float, float, float, float]] = []
    invocations: list[tuple[int, tuple[float, float, float, float, float, float]]] = []
    for index, (operands, operator) in enumerate(operations):
        if operator == b"q":
            stack.append(current)
        elif operator == b"Q":
            if not stack:
                raise ValueError(f"{label} graphics-state stack underflowed")
            current = stack.pop()
        elif operator == b"cm":
            current = concatenate(current, tuple(float(item) for item in operands))
        elif operator == b"Do" and str(operands[0]) == form_name:
            invocations.append((index, current))
    if stack or len(invocations) != 1:
        raise ValueError(f"{label} Form invocation or graphics-state balance changed")
    invocation_index, placement = invocations[0]
    if any(operator in {b"W", b"W*"} for _operands, operator in operations[:invocation_index]):
        raise ValueError(f"{label} Form is preceded by a clipping operator")
    points = [
        transform(placement, form_box[0], form_box[1]),
        transform(placement, form_box[0], form_box[3]),
        transform(placement, form_box[2], form_box[1]),
        transform(placement, form_box[2], form_box[3]),
    ]
    left = min(point[0] for point in points)
    bottom = min(point[1] for point in points)
    right = max(point[0] for point in points)
    top = max(point[1] for point in points)
    if left < 0 or bottom < 0 or right > a4[2] or top > a4[3] or right - left < 400 or top - bottom < 200:
        raise ValueError(f"{label} Form is clipped, off-page, or unexpectedly scaled")


def expect_rejected(callback: object, label: str) -> None:
    try:
        callback()  # type: ignore[operator]
    except Exception:
        return
    fail(f"{label} hostile control was accepted")


def rewritten(source: Path, output: Path, marker: str) -> None:
    writer = PdfWriter(clone_from=source)
    writer.add_metadata({"/Producer": marker})
    writer.write(output)
    writer.close()
    if output.read_bytes() == source.read_bytes():
        fail(f"{marker} positive fixture is not byte-different")


def rewritten_figure(source: Path, output: Path, marker: str) -> None:
    """Change serialization and decoded content bytes without changing painting."""

    original_content = stream_data(
        PdfReader(source, strict=True).pages[0].get_contents(),
        f"{marker} original figure content",
    )
    writer = PdfWriter(clone_from=source)
    page = writer.pages[0]
    content = DecodedStreamObject()
    content.set_data(original_content + b"\nq Q\n")
    page[NameObject("/Contents")] = writer._add_object(content)
    writer.add_metadata({"/Producer": marker})
    writer.write(output)
    writer.close()
    if output.read_bytes() == source.read_bytes():
        fail(f"{marker} positive fixture is not byte-different")
    rewritten_content = stream_data(
        PdfReader(output, strict=True).pages[0].get_contents(),
        f"{marker} rewritten figure content",
    )
    if rewritten_content == original_content:
        fail(f"{marker} positive fixture did not change decoded content bytes")


if pypdf.__version__ != "6.15.0":
    fail(f"requires pypdf 6.15.0, observed {pypdf.__version__!r}")
repo = Path.cwd().resolve()
if repo in Path(pypdf.__file__).resolve().parents:
    fail("pypdf resolved from inside the repository")

rows = []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    fields = line.split("\t")
    if len(fields) != 7:
        fail("lane inventory is malformed")
    label, built_report, committed_report, fresh_figure, committed_figure, pages, figure_page = fields
    rows.append((label, Path(built_report), Path(committed_report), Path(fresh_figure), Path(committed_figure), int(pages), int(figure_page)))
if [row[0] for row in rows] != ["v4", "v5"]:
    fail("lane inventory is not exactly ordered v4 then v5")

output = Path(sys.argv[2])
for label, built_report, committed_report, fresh_figure, committed_figure, pages, figure_page in rows:
    # Keyed relation: exactly these two reports bind only this lane's committed TeX figure.
    for report_path in (built_report, committed_report):
        validate_report(
            PdfReader(report_path, strict=True),
            PdfReader(committed_figure, strict=True),
            pages,
            figure_page,
            f"{label} {report_path.name}",
        )
    fresh_box, fresh_families = validate_figure(
        PdfReader(fresh_figure, strict=True), f"{label} fresh figure"
    )
    committed_box, committed_families = validate_figure(
        PdfReader(committed_figure, strict=True), f"{label} committed figure"
    )
    if not close_box(fresh_box, committed_box):
        fail(f"{label} fresh/committed figure geometry differs")
    if fresh_families != committed_families:
        fail(f"{label} fresh/committed figure font-family inventory differs")

    positive_report = output / f"positive-{label}-report.pdf"
    positive_figure = output / f"positive-{label}-figure.pdf"
    rewritten(committed_report, positive_report, f"pid-rs-v6-{label}-report-positive")
    rewritten_figure(committed_figure, positive_figure, f"pid-rs-v6-{label}-figure-positive")
    validate_report(
        PdfReader(positive_report, strict=True),
        PdfReader(committed_figure, strict=True),
        pages,
        figure_page,
        f"{label} byte-different report positive",
    )
    positive_box, positive_families = validate_figure(
        PdfReader(positive_figure, strict=True), f"{label} byte-different figure positive"
    )
    if not close_box(positive_box, committed_box) or positive_families != committed_families:
        fail(f"{label} byte-different figure positive changed geometry or font families")
    expect_rejected(
        lambda: validate_report(
            PdfReader(built_report, strict=True),
            PdfReader(positive_figure, strict=True),
            pages,
            figure_page,
            f"{label} same-lane Cartesian positive",
        ),
        "same-lane byte-different figure Cartesian pairing",
    )

# Wrong-lane pairing is a second causal anti-Cartesian control, even where the two
# figures happen to share page geometry and font-family inventories.
v4, v5 = rows
expect_rejected(
    lambda: validate_report(
        PdfReader(v4[1], strict=True), PdfReader(v5[4], strict=True), v4[5], v4[6], "v4 wrong-lane"
    ),
    "Cartesian report/figure pairing",
)

# Object hostiles retain the publication safety predicates.  Each is derived from
# the valid v5 report and evaluated against the one committed figure named by v5 TeX.
label, built_report, _committed_report, _fresh_figure, committed_figure, pages, figure_page = v5
raw = built_report.read_bytes()
figure_path = committed_figure

def reader() -> PdfReader:
    return PdfReader(BytesIO(raw), strict=True)

clipped_writer = PdfWriter(clone_from=BytesIO(raw))
clipped_page = clipped_writer.pages[figure_page - 1]
clipped_name = forms(clipped_writer)[0][1]
clipped_stream = ContentStream(clipped_page.get_contents(), clipped_writer)
indices = [
    index for index, (operands, operator) in enumerate(clipped_stream.operations)
    if operator == b"Do" and len(operands) == 1 and str(operands[0]) == clipped_name
]
if len(indices) != 1:
    fail("clipping hostile cannot locate the unique Form invocation")
clipped_stream.operations[indices[0]:indices[0]] = [
    ([NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)], b"re"),
    ([], b"W"),
    ([], b"n"),
]
clipped_page.replace_contents(clipped_stream)
clipped_bytes = BytesIO()
clipped_writer.write(clipped_bytes)
clipped_writer.close()

offpage_writer = PdfWriter(clone_from=BytesIO(raw))
offpage_page = offpage_writer.pages[figure_page - 1]
offpage_name = forms(offpage_writer)[0][1]
offpage_stream = ContentStream(offpage_page.get_contents(), offpage_writer)
indices = [
    index for index, (operands, operator) in enumerate(offpage_stream.operations)
    if operator == b"Do" and len(operands) == 1 and str(operands[0]) == offpage_name
]
offpage_stream.operations[indices[0]:indices[0]] = [
    ([NumberObject(1), NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(10000), NumberObject(0)], b"cm")
]
offpage_page.replace_contents(offpage_stream)
offpage_bytes = BytesIO()
offpage_writer.write(offpage_bytes)
offpage_writer.close()

matrix = reader()
forms(matrix)[0][2][NameObject("/Matrix")] = ArrayObject(
    [FloatObject(1), FloatObject(0), FloatObject(0), FloatObject(1), FloatObject(10000), FloatObject(0)]
)
resources = reader()
forms(resources)[0][2][NameObject("/Resources")] = DictionaryObject()
action = reader()
action.trailer["/Root"][NameObject("/OpenAction")] = DictionaryObject(
    {NameObject("/S"): NameObject("/JavaScript"), NameObject("/JS"): TextStringObject("app.alert('unsafe')")}
)

hostiles = (
    (PdfReader(BytesIO(clipped_bytes.getvalue()), strict=True), "clipping"),
    (PdfReader(BytesIO(offpage_bytes.getvalue()), strict=True), "off-page"),
    (matrix, "Form matrix"),
    (resources, "Form resources"),
    (action, "catalog action"),
)
for hostile, hostile_label in hostiles:
    expect_rejected(
        lambda hostile=hostile: validate_report(
            hostile, PdfReader(figure_path, strict=True), pages, figure_page, f"v5 {hostile_label} hostile"
        ),
        hostile_label,
    )

# This figure preserves text, page geometry, and font inventory but paints an opaque
# white rectangle last.  It must survive the normalization checks and fail the raster
# comparison; accepting it would make normalization-only evidence sufficient.
normalization_hostile = output / "normalization-only-v5-figure.pdf"
writer = PdfWriter(clone_from=committed_figure)
page = writer.pages[0]
original = stream_data(page.get_contents(), "normalization hostile source content")
overlay = DecodedStreamObject()
overlay.set_data(original + b"\nq 1 1 1 rg 0 0 453.543307 255.11811 re f Q\n")
page[NameObject("/Contents")] = writer._add_object(overlay)
writer.write(normalization_hostile)
writer.close()
validate_figure(PdfReader(normalization_hostile, strict=True), "normalization-only hostile")
PY

normalize_text() {
  local input="$1" output="$2" label="$3"
  if ! pdftotext "$input" "$BUILD_ROOT/$label.raw.txt" \
    >"$BUILD_ROOT/$label-pdftotext.stdout" 2>"$BUILD_ROOT/$label-pdftotext.stderr"; then
    cat "$BUILD_ROOT/$label-pdftotext.stdout" "$BUILD_ROOT/$label-pdftotext.stderr" >&2
    fail "text extraction failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label-pdftotext.stdout" && ! -s "$BUILD_ROOT/$label-pdftotext.stderr" ]] || {
    cat "$BUILD_ROOT/$label-pdftotext.stdout" "$BUILD_ROOT/$label-pdftotext.stderr" >&2
    fail "text extraction emitted diagnostics: $label"
  }
  python3 -I -S - "$BUILD_ROOT/$label.raw.txt" "$output" <<'PY'
from pathlib import Path
import sys
Path(sys.argv[2]).write_text(
    " ".join(Path(sys.argv[1]).read_text(encoding="utf-8").split()) + "\n",
    encoding="utf-8",
    newline="\n",
)
PY
}

check_pdf_envelope() {
  local input="$1" expected_pages="$2" label="$3"
  if ! pdfinfo "$input" >"$BUILD_ROOT/$label.pdfinfo" 2>"$BUILD_ROOT/$label.pdfinfo.stderr"; then
    cat "$BUILD_ROOT/$label.pdfinfo" "$BUILD_ROOT/$label.pdfinfo.stderr" >&2
    fail "pdfinfo failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label.pdfinfo.stderr" ]] || {
    cat "$BUILD_ROOT/$label.pdfinfo.stderr" >&2
    fail "pdfinfo emitted diagnostics: $label"
  }
  [[ "$(awk '/^Pages:/ {print $2}' "$BUILD_ROOT/$label.pdfinfo")" == "$expected_pages" ]] || \
    fail "$label page count changed"
  if ! pdffonts "$input" >"$BUILD_ROOT/$label.pdffonts" 2>"$BUILD_ROOT/$label.pdffonts.stderr"; then
    cat "$BUILD_ROOT/$label.pdffonts" "$BUILD_ROOT/$label.pdffonts.stderr" >&2
    fail "pdffonts failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label.pdffonts.stderr" ]] || {
    cat "$BUILD_ROOT/$label.pdffonts.stderr" >&2
    fail "pdffonts emitted diagnostics: $label"
  }
  awk '
    NR > 2 { seen=1; if ($(NF-4)!="yes" || $(NF-3)!="yes" || $(NF-2)!="yes") bad=1 }
    END { exit (!seen || bad) }
  ' "$BUILD_ROOT/$label.pdffonts" || fail "$label has a nonembedded, nonsubset, or non-Unicode font"
  awk 'NR > 2 { name=$1; sub(/^[A-Z][A-Z][A-Z][A-Z][A-Z][A-Z]\+/, "", name); print name }' \
    "$BUILD_ROOT/$label.pdffonts" | LC_ALL=C sort -u >"$BUILD_ROOT/$label.font-families"
  [[ -s "$BUILD_ROOT/$label.font-families" ]] || fail "$label font-family inventory is empty"
}

compare_semantics() {
  local left="$1" right="$2" pages="$3" label="$4"
  check_pdf_envelope "$left" "$pages" "$label-left"
  check_pdf_envelope "$right" "$pages" "$label-right"
  normalize_text "$left" "$BUILD_ROOT/$label-left.normalized.txt" "$label-left"
  normalize_text "$right" "$BUILD_ROOT/$label-right.normalized.txt" "$label-right"
  cmp -s "$BUILD_ROOT/$label-left.normalized.txt" "$BUILD_ROOT/$label-right.normalized.txt" || \
    fail "$label normalized extracted text changed"
  cmp -s "$BUILD_ROOT/$label-left.font-families" "$BUILD_ROOT/$label-right.font-families" || \
    fail "$label font-family inventory changed"
}

while IFS=$'\t' read -r label built_report committed_report fresh_figure committed_figure pages figure_page; do
  compare_semantics "$built_report" "$committed_report" "$pages" "$label-report"
  compare_semantics "$fresh_figure" "$committed_figure" 1 "$label-figure"
  compare_semantics "$BUILD_ROOT/positive-$label-report.pdf" "$committed_report" "$pages" "$label-positive-report"
  compare_semantics "$BUILD_ROOT/positive-$label-figure.pdf" "$committed_figure" 1 "$label-positive-figure"
done <"$BUILD_ROOT/lanes.tsv"

# Prove that the visibility hostile really is indistinguishable to the bounded
# normalization-only route before requiring the raster route to reject it.
compare_semantics \
  "$BUILD_ROOT/normalization-only-v5-figure.pdf" \
  audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf \
  1 normalization-only-hostile

render_pages() {
  local input="$1" output="$2" mode="$3" label="$4"
  local -a command=(pdftoppm -png -r "$RENDER_DPI")
  [[ "$mode" == "color" ]] || command+=(-gray)
  mkdir -p "$output"
  if ! env -i PATH="$PATH" LC_ALL=C LANG=C TZ=UTC HOME="$BUILD_ROOT" TMPDIR="$BUILD_ROOT" \
    "${command[@]}" "$input" "$output/page" \
    >"$BUILD_ROOT/$label-render.stdout" 2>"$BUILD_ROOT/$label-render.stderr"; then
    cat "$BUILD_ROOT/$label-render.stdout" "$BUILD_ROOT/$label-render.stderr" >&2
    fail "Poppler rendering failed: $label"
  fi
  [[ ! -s "$BUILD_ROOT/$label-render.stdout" && ! -s "$BUILD_ROOT/$label-render.stderr" ]] || {
    cat "$BUILD_ROOT/$label-render.stdout" "$BUILD_ROOT/$label-render.stderr" >&2
    fail "Poppler rendering emitted diagnostics: $label"
  }
}

compare_renders() {
  local left="$1" right="$2" pages="$3" label="$4"
  python3 -I -S "$COMPARATOR" --left-dir "$left" --right-dir "$right" --pages "$pages" \
    --label "$label" --receipt "$BUILD_ROOT/$label.tsv" --large-delta 24 \
    --max-mean-abs 0.20 --max-changed-fraction 0.01 --max-large-fraction 0.001
}

while IFS=$'\t' read -r label built_report committed_report fresh_figure committed_figure pages figure_page; do
  for mode in color gray; do
    render_pages "$built_report" "$BUILD_ROOT/$label-report-built-$mode" "$mode" "$label-report-built-$mode"
    render_pages "$committed_report" "$BUILD_ROOT/$label-report-committed-$mode" "$mode" "$label-report-committed-$mode"
    compare_renders "$BUILD_ROOT/$label-report-built-$mode" "$BUILD_ROOT/$label-report-committed-$mode" \
      "$pages" "$label-report-$mode"

    render_pages "$fresh_figure" "$BUILD_ROOT/$label-figure-fresh-$mode" "$mode" "$label-figure-fresh-$mode"
    render_pages "$committed_figure" "$BUILD_ROOT/$label-figure-committed-$mode" "$mode" "$label-figure-committed-$mode"
    compare_renders "$BUILD_ROOT/$label-figure-fresh-$mode" "$BUILD_ROOT/$label-figure-committed-$mode" \
      1 "$label-figure-$mode"

    render_pages "$BUILD_ROOT/positive-$label-report.pdf" "$BUILD_ROOT/$label-positive-report-$mode" \
      "$mode" "$label-positive-report-$mode"
    compare_renders "$BUILD_ROOT/$label-positive-report-$mode" "$BUILD_ROOT/$label-report-committed-$mode" \
      "$pages" "$label-positive-report-$mode"
    render_pages "$BUILD_ROOT/positive-$label-figure.pdf" "$BUILD_ROOT/$label-positive-figure-$mode" \
      "$mode" "$label-positive-figure-$mode"
    compare_renders "$BUILD_ROOT/$label-positive-figure-$mode" "$BUILD_ROOT/$label-figure-committed-$mode" \
      1 "$label-positive-figure-$mode"
  done
done <"$BUILD_ROOT/lanes.tsv"

for mode in color gray; do
  render_pages "$BUILD_ROOT/normalization-only-v5-figure.pdf" \
    "$BUILD_ROOT/normalization-only-$mode" "$mode" "normalization-only-$mode"
  if compare_renders \
    "$BUILD_ROOT/normalization-only-$mode" "$BUILD_ROOT/v5-figure-committed-$mode" \
    1 "normalization-only-$mode" \
    >"$BUILD_ROOT/normalization-only-$mode.stdout" \
    2>"$BUILD_ROOT/normalization-only-$mode.stderr"; then
    fail "normalization-only $mode visibility hostile was accepted"
  fi
  rg -F -- "exceeds its visual bound" "$BUILD_ROOT/normalization-only-$mode.stderr" >/dev/null || {
    cat "$BUILD_ROOT/normalization-only-$mode.stdout" "$BUILD_ROOT/normalization-only-$mode.stderr" >&2
    fail "normalization-only $mode visibility hostile was rejected noncausally"
  }
done

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: immutable v4/v5 exact publication gates and the keyed v6 object/text/geometry/font/color/gray adjudication passed; byte-different render-equivalent fixtures were admitted and all hostiles were rejected"
else
  echo "OK: immutable v4/v5 publications passed the keyed cross-toolchain v6 object/text/geometry/font/color/gray adjudication; byte-different render-equivalent fixtures were admitted and all hostiles were rejected"
fi
