#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
MD="audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md"
TEX="audit/formal/latex/ksg-m1a-composite-v6-boundary.tex"
SVG="audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.svg"
FIGURE_PDF="audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf"
PDF="output/pdf/ksg-m1a-composite-v6-boundary.pdf"
RENDERING_RECEIPT="output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv"
VISUAL_RECEIPT="audit/evidence/ksg-rev4-m1a-composite-v6-boundary-visual-receipt-2026-08-18.md"
COMPARATOR="scripts/compare-formal-pdf-renders.py"
EXPECTED_MD_SHA256="a0a1a675e470169f411c35f0ae4b496848f8cbe44300cbca0a763d1ec20a57f9"
EXPECTED_MD_BYTES=13367
EXPECTED_TEX_SHA256="d75ed1834dbc5d210bafb2a1f65784e13e465c199dcb36dc461eb27be3857e12"
EXPECTED_TEX_BYTES=13201
EXPECTED_SVG_SHA256="ce4e53c93a45c99c949e6c8408eeceb282a10cd13459f04874b022ea4692c9fd"
EXPECTED_SVG_BYTES=10774
EXPECTED_COMPARATOR_SHA256="7b230bef4371398c18a3975d6888207bc31a737eeffb0217f3d5bbc0aec3054b"
EXPECTED_COMPARATOR_BYTES=16408
EXPECTED_FIGURE_PDF_SHA256="20484c4321daf9b742fe0bf12092a10bbebb10b5ea6441cf5bef57f9dca913e5"
EXPECTED_FIGURE_PDF_BYTES=73089
EXPECTED_PDF_SHA256="52751c8701ad527040907e399f41ee6579616bc63db1af174bea65e5303da09a"
EXPECTED_PDF_BYTES=1042119
EXPECTED_RENDERING_RECEIPT_SHA256="333bb16caf3a793d383b06b70c51e3a30fa881f8c5743cd9a8798c4c20b5725d"
EXPECTED_RENDERING_RECEIPT_BYTES=1064
EXPECTED_VISUAL_RECEIPT_SHA256="ce04b42e37b2db4030452402403c4535c0739b8587a29eed40c091ad60450b67"
EXPECTED_VISUAL_RECEIPT_BYTES=3278
EXPECTED_PAGES=4
EXPECTED_FIGURE_PAGE=3
RENDER_DPI=120
SOURCE_DATE_EPOCH_VALUE=1787004000
HERMETICITY_NONCLAIM="The clean endpoints use ordinary Git status plus selected metadata checks; rejecting core.excludesFile removes one ignore-routing overlay, but repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure."
SVG_HERMETICITY_NONCLAIM="repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure."

fail() {
  echo "composite-v6 boundary PDF check: $*" >&2
  exit 1
}

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in awk cat cmp cp dirname env fc-cache grep kpsewhich lacheck latexmk mkdir mktemp \
  pdffonts pdfinfo pdftoppm pdftotext python3 rm rsvg-convert seq shasum sort tr wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite-v6 boundary PDF check: missing command: $command" >&2
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
verify_file "$FIGURE_PDF" "$EXPECTED_FIGURE_PDF_SHA256" "$EXPECTED_FIGURE_PDF_BYTES"
verify_file "$PDF" "$EXPECTED_PDF_SHA256" "$EXPECTED_PDF_BYTES"
verify_file "$RENDERING_RECEIPT" "$EXPECTED_RENDERING_RECEIPT_SHA256" \
  "$EXPECTED_RENDERING_RECEIPT_BYTES"
verify_file "$VISUAL_RECEIPT" "$EXPECTED_VISUAL_RECEIPT_SHA256" "$EXPECTED_VISUAL_RECEIPT_BYTES"

if grep -F -- "fresh attempt-1 local" "$MD" "$TEX" "$SVG" >/dev/null \
  || grep -F -- "fresh attempt-one local" "$MD" "$TEX" "$SVG" >/dev/null \
  || grep -F -- "one exact C6 - attempt 1 - all terminal success" "$MD" "$TEX" "$SVG" >/dev/null; then
  fail "local/hosted attempt-domain separation changed"
fi
if grep -F -- "where every term is terminal attempt-1 success" "$MD" >/dev/null \
  || grep -F -- "where every term means terminal success at attempt 1" "$TEX" >/dev/null; then
  fail "C5 local/hosted attempt-domain separation changed"
fi
grep -F -- "where \$L_5\$ is one fresh local qualification observation for exact C5" "$MD" >/dev/null \
  || fail "Markdown C5 local/hosted attempt-domain separation changed"
grep -F -- "one fresh exact-C6 local closure observation and fresh" "$MD" >/dev/null \
  || fail "Markdown local/hosted attempt-domain separation changed"
if grep -F -- "publishes no private absolute path" "$MD" "$TEX" "$SVG" >/dev/null \
  || grep -F -- "publish no ambient secrets" "$MD" "$TEX" "$SVG" >/dev/null \
  || grep -F -- "publishes no ambient secret" "$MD" "$TEX" "$SVG" >/dev/null; then
  fail "local privacy boundary changed"
fi
for semantic_source in "$MD" "$TEX" "$SVG"; do
  grep -F -- "ambient variables" "$semantic_source" >/dev/null \
    || fail "$semantic_source lost the bounded no-ambient-variable statement"
  grep -F -- "secret-like patterns and private-path prefixes" "$semantic_source" >/dev/null \
    || fail "$semantic_source lost the bounded output-scan statement"
done
for semantic_source in "$MD" "$TEX"; do
  tr '\n' ' ' <"$semantic_source" | grep -F -- "$HERMETICITY_NONCLAIM" >/dev/null \
    || fail "$semantic_source lost the exact local hermeticity nonclaim"
done
grep -F -- "$SVG_HERMETICITY_NONCLAIM" "$SVG" >/dev/null \
  || fail "SVG lost the bounded local hermeticity nonclaim"
if grep -F -- "proves hermetic" "$MD" "$TEX" "$SVG" >/dev/null \
  || grep -F -- "is a hermetic closure." "$MD" "$TEX" "$SVG" >/dev/null; then
  fail "local hermeticity boundary changed"
fi
grep -F -- '\texttt{just ksg-composite-v6}' "$TEX" >/dev/null \
  || fail "TeX fixed local command lost its texttt binding"
if grep -q $'\t' "$TEX"; then
  fail "TeX contains a tab control character"
fi

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-composite-v6-boundary-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_ROOT"' EXIT

python3 -I -S - "$SVG" <<'PY'
from __future__ import annotations

from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


XML_DECLARATION = b'<?xml version="1.0" encoding="UTF-8"?>\n'
NS = "{http://www.w3.org/2000/svg}"
EXPECTED_ROOT = {
    "{http://www.w3.org/XML/1998/namespace}lang": "en",
    "width": "160mm",
    "height": "90mm",
    "viewBox": "0 0 1600 900",
    "role": "img",
    "aria-labelledby": "v6-title v6-desc",
    "data-predecessor": "C5",
    "data-failed-contract": "v5",
    "data-successor": "C6",
    "data-receipt": "R6",
    "data-r5-status": "permanently-unissued",
    "data-defect": "cartesian-cross-toolchain-association",
    "data-repair-count": "1",
}
REQUIRED_TEXT = (
    "Wrong-lane comparison is not publication failure evidence",
    "C6 direct child of C5",
    "R5 UNISSUED",
    "Q5 = false",
    "One bounded correction",
    "Cartesian report x figure lanes",
    "same named failure surface in v4 + v5",
    "bind committed figure named by TeX",
    "compare fresh/committed separately",
    "freeze C6 before local closure and hosted attempt-1 evaluation",
    "Fresh C6 qualification only",
    "Q6 = L6 AND CI6 AND CodeQL6 AND D6",
    "fresh local record + hosted attempt 1 success",
    "Q6 permits R6",
    "retain local + hosted captures",
    "Bounded comparison",
    "C5 stays published - R5 stays unissued - C6 is a direct child - R6 needs fresh all-success evidence.",
    "no PID/KSG/math/security/application credit - no authentication - no independence - no PDF-UA.",
    "repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure.",
)


def validate_svg(raw: bytes) -> None:
    if not raw.startswith(XML_DECLARATION):
        raise ValueError("XML declaration or framing changed")
    tail = raw[len(XML_DECLARATION):]
    if b"<?" in tail:
        raise ValueError("contains a processing instruction after the XML declaration")
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("contains a document type or entity declaration")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as error:
        raise ValueError(f"is not well-formed XML: {error}") from error
    if root.tag != f"{NS}svg":
        raise ValueError("does not have an SVG root")
    for key, value in EXPECTED_ROOT.items():
        if root.get(key) != value:
            raise ValueError(f"root attribute {key!r} changed")

    allowed_elements = {
        f"{NS}svg", f"{NS}title", f"{NS}desc", f"{NS}defs", f"{NS}marker",
        f"{NS}path", f"{NS}pattern", f"{NS}line", f"{NS}style", f"{NS}rect",
        f"{NS}text", f"{NS}g",
    }
    allowed_attributes = {
        "svg": {
            "lang", "width", "height", "viewBox", "role", "aria-labelledby",
            "data-predecessor", "data-failed-contract", "data-successor",
            "data-receipt", "data-r5-status", "data-defect", "data-repair-count",
        },
        "title": {"id"},
        "desc": {"id"},
        "defs": set(),
        "marker": {
            "id", "markerWidth", "markerHeight", "refX", "refY", "orient",
            "markerUnits",
        },
        "path": {
            "d", "fill", "stroke", "stroke-width", "stroke-dasharray", "marker-end",
        },
        "pattern": {
            "id", "width", "height", "patternUnits", "patternTransform",
        },
        "line": {"x1", "y1", "x2", "y2", "stroke", "stroke-width"},
        "style": set(),
        "rect": {"x", "y", "width", "height", "rx", "fill", "stroke", "stroke-width"},
        "text": {"x", "y", "class"},
        "g": set(),
    }
    elements = tuple(root.iter())
    ids: set[str] = set()
    for element in elements:
        identifier = element.get("id")
        if identifier:
            if identifier in ids:
                raise ValueError(f"repeats identifier {identifier!r}")
            ids.add(identifier)

    url_values: list[str] = []
    for element in elements:
        local_tag = element.tag.rsplit("}", 1)[-1]
        local_attributes = {name.rsplit("}", 1)[-1] for name in element.attrib}
        unexpected_attributes = local_attributes - allowed_attributes.get(local_tag, set())
        for name, value in element.attrib.items():
            local = name.rsplit("}", 1)[-1]
            if local.lower().startswith("on"):
                raise ValueError(f"contains event attribute {local!r}")
            if local.lower() in {"href", "src"}:
                raise ValueError(f"contains external resource attribute {local!r}")
            if local == "transform":
                raise ValueError("contains an unbounded transform attribute")
            if local in {"style", "font-size"}:
                raise ValueError(f"contains forbidden per-element style attribute {local!r}")
            if local in {
                "display", "visibility", "opacity", "fill-opacity", "stroke-opacity",
                "textLength", "lengthAdjust",
            }:
                raise ValueError(f"contains a hiding or text-distortion attribute {local!r}")
            url_values.append(value)
        if unexpected_attributes:
            raise ValueError(
                f"contains unbounded attribute {sorted(unexpected_attributes)[0]!r}"
            )
        if element.tag not in allowed_elements:
            raise ValueError(
                f"contains unsupported element {element.tag.rsplit('}', 1)[-1]!r}"
            )

    style_nodes = root.findall(f".//{NS}style")
    if len(style_nodes) != 1:
        raise ValueError("style element inventory changed")
    css = "".join(style_nodes[0].itertext())
    if re.search(r"@import\b|@font-face\b", css, flags=re.IGNORECASE):
        raise ValueError("contains a CSS import or font-face resource")
    if re.search(r"/\*|\*/", css):
        raise ValueError("contains an unbounded CSS comment")
    url_values.append(css)
    for value in url_values:
        for match in re.finditer(r"url\s*\(([^)]+)\)", value, flags=re.IGNORECASE):
            target = match.group(1).strip().strip("'\"")
            if not target.startswith("#"):
                raise ValueError("contains a nonlocal CSS resource")
            if target[1:] not in ids:
                raise ValueError(f"references absent local identifier {target!r}")

    class_sizes: dict[str, float] = {}
    cursor = 0
    for match in re.finditer(r"([^{}]+)\{([^{}]*)\}", css):
        if css[cursor:match.start()].strip():
            raise ValueError("contains unparsed CSS outside a rule")
        cursor = match.end()
        selectors = [item.strip() for item in match.group(1).split(",")]
        declarations: dict[str, str] = {}
        for raw_declaration in match.group(2).split(";"):
            raw_declaration = raw_declaration.strip()
            if not raw_declaration:
                continue
            if ":" not in raw_declaration:
                raise ValueError("contains a malformed CSS declaration")
            name, value = (item.strip() for item in raw_declaration.split(":", 1))
            if name in declarations:
                raise ValueError(f"repeats CSS property {name!r}")
            declarations[name] = value
        allowed_properties = {
            "font-family", "font-size", "font-weight", "letter-spacing", "fill",
            "text-anchor",
        }
        unexpected = set(declarations) - allowed_properties
        if unexpected:
            raise ValueError(
                f"contains unbounded CSS property {sorted(unexpected)[0]!r}"
            )
        if declarations.get("font-family") not in {
            "'Source Sans Pro', sans-serif", "'Latin Modern Roman', serif"
        }:
            raise ValueError("CSS font-family changed")
        if "font-weight" in declarations and declarations["font-weight"] not in {"600", "700"}:
            raise ValueError("CSS font-weight changed")
        if "letter-spacing" in declarations and declarations["letter-spacing"] not in {"1px", "2px"}:
            raise ValueError("CSS letter-spacing changed")
        if re.fullmatch(r"#[0-9A-F]{6}", declarations.get("fill", "")) is None:
            raise ValueError("CSS fill changed")
        if "text-anchor" in declarations and declarations["text-anchor"] != "middle":
            raise ValueError("CSS text-anchor changed")
        size_text = declarations.get("font-size")
        size_match = None if size_text is None else re.fullmatch(
            r"([0-9]+(?:\.[0-9]+)?)px", size_text
        )
        if size_match is None:
            raise ValueError("CSS class lacks one explicit pixel font size")
        size = float(size_match.group(1))
        if size < 25:
            raise ValueError("uses publication text below 25 SVG pixels")
        for selector in selectors:
            selector_match = re.fullmatch(r"\.([A-Za-z_][A-Za-z0-9_-]*)", selector)
            if selector_match is None:
                raise ValueError(f"contains unbounded CSS selector {selector!r}")
            name = selector_match.group(1)
            if name in class_sizes:
                raise ValueError(f"repeats CSS class {name!r}")
            class_sizes[name] = size
    if css[cursor:].strip():
        raise ValueError("contains unparsed CSS after the final rule")

    text_nodes = root.findall(f".//{NS}text")
    if not text_nodes:
        raise ValueError("contains no visible text nodes")
    for text in text_nodes:
        if set(text.attrib) != {"x", "y", "class"}:
            raise ValueError("text node attribute inventory changed")
        if re.fullmatch(r"-?[0-9]+(?:\.[0-9]+)?", text.get("x", "")) is None or re.fullmatch(
            r"-?[0-9]+(?:\.[0-9]+)?", text.get("y", "")
        ) is None:
            raise ValueError("text node coordinate changed")
        classes = text.get("class", "").split()
        sizes = [class_sizes[name] for name in classes if name in class_sizes]
        if len(classes) != 1 or len(sizes) != 1:
            raise ValueError("text node lacks one closed font-size class")
        if not "".join(text.itertext()).strip():
            raise ValueError("text node is empty")

    title = root.find(f"{NS}title")
    desc = root.find(f"{NS}desc")
    if title is None or title.get("id") != "v6-title":
        raise ValueError("title identity changed")
    if desc is None or desc.get("id") != "v6-desc":
        raise ValueError("description identity changed")
    visible = " ".join(" ".join(root.itertext()).split())
    for literal in REQUIRED_TEXT:
        if literal not in visible:
            raise ValueError(f"required literal is absent: {literal!r}")


raw = Path(sys.argv[1]).read_bytes()
try:
    validate_svg(raw)
except ValueError as error:
    raise SystemExit(f"composite-v6 boundary PDF check: SVG {error}") from error

hostiles = (
    (
        raw.replace(b"</style>", b"@import url(https://example.invalid/x.css);</style>", 1),
        "CSS import",
    ),
    (
        raw.replace(XML_DECLARATION, XML_DECLARATION + b'<?xml-stylesheet href="unsafe.css"?>\n', 1),
        "processing instruction",
    ),
    (raw.replace(b"<text ", b'<text font-size="1px" ', 1), "per-element style"),
    (raw.replace(b"<g>", b'<g transform="scale(0.01)">', 1), "unbounded transform"),
    (raw.replace(b"<rect ", b'<rect transform="scale(0.01)" ', 1), "unbounded transform"),
    (raw.replace(b"<rect ", b'<rect clip-path="url(#v6-blocked-hatch)" ', 1), "unbounded attribute"),
    (
        raw.replace(
            b"APPEND-ONLY PORTABILITY BOUNDARY</text>",
            b'<tspan transform="scale(0.01)">APPEND-ONLY PORTABILITY BOUNDARY</tspan></text>',
            1,
        ),
        "unbounded transform",
    ),
    (
        raw.replace(
            b"</style>", b".small { transform: scale(0.01); font-size: 25px; }</style>", 1
        ),
        "unbounded CSS property",
    ),
    (
        raw.replace(
            b"</style>", b".small { display: none; font-size: 25px; }</style>", 1
        ),
        "unbounded CSS property",
    ),
)
for hostile, expected in hostiles:
    try:
        validate_svg(hostile)
    except ValueError as error:
        if expected not in str(error):
            raise SystemExit(
                f"composite-v6 boundary PDF check: SVG hostile rejected noncausally: {error}"
            ) from error
    else:
        raise SystemExit(
            f"composite-v6 boundary PDF check: SVG {expected} hostile was accepted"
        )
PY

python3 -I -S - "$TEX" "$FIGURE_PDF" <<'PY'
from pathlib import Path, PurePosixPath
import re
import sys


EXPECTED = PurePosixPath(
    "figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf"
)


def validate_includegraphics(source: str) -> None:
    uncommented = re.sub(r"(?<!\\)%[^\n]*", "", source)
    if re.search(r"\\graphicspath\s*\{", uncommented):
        raise ValueError("TeX graphicspath indirection is forbidden")
    matches = re.findall(
        r"\\includegraphics\s*(?:\[[^\]]*\]\s*)?\{([^{}]+)\}",
        uncommented,
        flags=re.DOTALL,
    )
    if len(matches) != 1:
        raise ValueError("TeX includegraphics inventory is not exactly one")
    raw_path = "".join(matches[0].split())
    candidate = PurePosixPath(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts or candidate != EXPECTED:
        raise ValueError("TeX figure association is not the exact committed figure path")


source_path = Path(sys.argv[1])
figure_path = Path(sys.argv[2])
source = source_path.read_text(encoding="utf-8")
try:
    validate_includegraphics(source)
except ValueError as error:
    raise SystemExit(f"composite-v6 boundary PDF check: {error}") from error
resolved = (source_path.parent / EXPECTED).resolve()
if resolved != figure_path.resolve() or not resolved.is_file():
    raise SystemExit(
        "composite-v6 boundary PDF check: TeX figure association does not resolve to the committed figure"
    )
hostile = source.replace(str(EXPECTED), "figures/unreferenced-lane.pdf", 1)
try:
    validate_includegraphics(hostile)
except ValueError as error:
    if "exact committed figure path" not in str(error):
        raise SystemExit(
            f"composite-v6 boundary PDF check: TeX-path hostile rejected noncausally: {error}"
        ) from error
else:
    raise SystemExit(
        "composite-v6 boundary PDF check: TeX-path association hostile was accepted"
    )
PY

FONT_ROOT="$BUILD_ROOT/fonts"
FONT_CACHE="$BUILD_ROOT/font-cache"
FONT_CONFIG="$BUILD_ROOT/fonts.conf"
mkdir -p "$FONT_ROOT" "$FONT_CACHE"
for font_name in SourceSansPro-Bold.otf SourceSansPro-Semibold.otf lmroman10-regular.otf; do
  font_path="$(kpsewhich --must-exist "$font_name" || true)"
  [[ -n "$font_path" && -f "$font_path" ]] || {
    echo "composite-v6 boundary PDF check: required font unavailable: $font_name" >&2
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
  if ! env -i PATH="$PATH" LC_ALL=C LANG=C TZ=UTC HOME="$BUILD_ROOT" TMPDIR="$BUILD_ROOT" \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    TEXINPUTS="$ROOT/audit/formal/latex:" \
    latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -no-shell-escape \
      -outdir="$directory" "$TEX" >"$BUILD_ROOT/$label.stdout" 2>&1; then
    cat "$BUILD_ROOT/$label.stdout" >&2
    fail "LaTeX build failed: $label"
  fi
  scripts/check-formal-pdf-log.sh "$directory/ksg-m1a-composite-v6-boundary.log"
}
BUILD_A="$BUILD_ROOT/build-a"
BUILD_B="$BUILD_ROOT/build-b"
build_report "$BUILD_A" build-a
build_report "$BUILD_B" build-b
BUILT="$BUILD_A/ksg-m1a-composite-v6-boundary.pdf"
cmp -s "$BUILT" "$BUILD_B/ksg-m1a-composite-v6-boundary.pdf" || \
  fail "two clean LaTeX builds differ"

RASTER_OVERLAY_PDF="$BUILD_ROOT/raster-overlay-hostile.pdf"
FONT_PROGRAM_PDF="$BUILD_ROOT/font-program-hostile.pdf"
python3 -I -B - "$BUILT" "$PDF" "$FIGURE_A" "$FIGURE_PDF" "$EXPECTED_PAGES" \
  "$EXPECTED_FIGURE_PAGE" "$RASTER_OVERLAY_PDF" "$FONT_PROGRAM_PDF" <<'PY'
from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import sys

import pypdf
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, BooleanObject, ByteStringObject, DecodedStreamObject, DictionaryObject, FloatObject, NameObject, NullObject, NumberObject, RectangleObject, StreamObject, TextStringObject


def fail(detail: str) -> None:
    raise SystemExit(f"composite-v6 boundary PDF check: PDF structure {detail}")


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


def reference_key(reference: object) -> tuple[object, ...]:
    if hasattr(reference, "idnum"):
        return (
            "indirect",
            getattr(reference, "idnum"),
            getattr(reference, "generation", 0),
        )
    return ("direct", id(resolve(reference)))


def validate_explicit_destination(value: object, report: PdfReader) -> None:
    value = resolve(value)
    if isinstance(value, DictionaryObject):
        if set(map(str, value.keys())) != {"/D"}:
            raise ValueError("internal destination dictionary has extra keys")
        validate_explicit_destination(value["/D"], report)
        return
    if not isinstance(value, ArrayObject) or len(value) not in {2, 5}:
        raise ValueError("internal destination array shape changed")
    page_keys = {
        reference_key(page.indirect_reference)
        for page in report.pages
        if page.indirect_reference is not None
    }
    if reference_key(value[0]) not in page_keys:
        raise ValueError("internal destination targets a non-report page")
    kind = str(value[1])
    if len(value) == 2:
        if kind != "/Fit":
            raise ValueError("two-item internal destination is not /Fit")
        return
    if kind != "/XYZ":
        raise ValueError("five-item internal destination is not /XYZ")
    for operand in value[2:]:
        operand = resolve(operand)
        if not isinstance(operand, (NullObject, NumberObject, FloatObject, int, float)):
            raise ValueError("internal /XYZ destination has a nonnumeric operand")


def validate_name_tree(value: object, report: PdfReader) -> dict[str, object]:
    named: dict[str, object] = {}
    seen: set[tuple[object, ...]] = set()

    def walk(reference: object, depth: int) -> tuple[str, str]:
        if depth > 8 or len(seen) >= 64:
            raise ValueError("destination name tree exceeds its bounded depth or size")
        identity = reference_key(reference)
        if identity in seen:
            raise ValueError("destination name tree is cyclic")
        seen.add(identity)
        node = resolve(reference)
        if not isinstance(node, DictionaryObject):
            raise ValueError("destination name-tree node is not a dictionary")
        keys = set(map(str, node.keys()))
        if keys not in ({"/Kids", "/Limits"}, {"/Names", "/Limits"}):
            raise ValueError("destination name-tree node keys changed")
        limits = resolve(node["/Limits"])
        if not isinstance(limits, ArrayObject) or len(limits) != 2:
            raise ValueError("destination name-tree limits changed")
        low, high = map(str, limits)
        if low > high:
            raise ValueError("destination name-tree limits are reversed")
        if "/Kids" in keys:
            kids = resolve(node["/Kids"])
            if not isinstance(kids, ArrayObject) or not 1 <= len(kids) <= 64:
                raise ValueError("destination name-tree child inventory changed")
            child_limits = [walk(child, depth + 1) for child in kids]
            if any(
                left[1] >= right[0]
                for left, right in zip(child_limits, child_limits[1:], strict=False)
            ):
                raise ValueError("destination name-tree child limits overlap or are unordered")
            if (low, high) != (child_limits[0][0], child_limits[-1][1]):
                raise ValueError("destination name-tree parent limits changed")
        else:
            entries = resolve(node["/Names"])
            if not isinstance(entries, ArrayObject) or not 2 <= len(entries) <= 512 or len(entries) % 2:
                raise ValueError("destination name-tree leaf inventory changed")
            names = [str(entries[index]) for index in range(0, len(entries), 2)]
            if names != sorted(names) or len(set(names)) != len(names):
                raise ValueError("destination name-tree leaf names are unordered or repeated")
            if (low, high) != (names[0], names[-1]):
                raise ValueError("destination name-tree leaf limits changed")
            for index, name in enumerate(names):
                destination = entries[2 * index + 1]
                validate_explicit_destination(destination, report)
                if name in named:
                    raise ValueError("destination name repeats across leaves")
                named[name] = destination
        return low, high

    walk(value, 0)
    if not 1 <= len(named) <= 128:
        raise ValueError("destination name inventory is outside its bound")
    return named


def validate_goto_action(
    value: object, named: dict[str, object], report: PdfReader, label: str
) -> None:
    value = resolve(value)
    if not isinstance(value, DictionaryObject) or set(map(str, value.keys())) != {"/S", "/D"}:
        raise ValueError(f"{label} action keys changed")
    if str(value.get("/S")) != "/GoTo":
        raise ValueError(f"{label} is not the bounded internal GoTo")
    destination = resolve(value.get("/D"))
    if isinstance(destination, str):
        if str(destination) not in named:
            raise ValueError(f"{label} names an absent internal destination")
    else:
        validate_explicit_destination(destination, report)


def validate_outlines(
    raw_outlines: object, named: dict[str, object], report: PdfReader
) -> None:
    outlines = resolve(raw_outlines)
    if not isinstance(outlines, DictionaryObject) or set(map(str, outlines.keys())) != {
        "/Type", "/First", "/Last", "/Count"
    }:
        raise ValueError("outline root keys changed")
    if str(outlines.get("/Type")) != "/Outlines" or int(outlines.get("/Count", -1)) != 6:
        raise ValueError("outline root type or count changed")
    expected_titles = (
        "Attempt-1 decision",
        "Terminal hosted observations",
        "The Cartesian association failure surface",
        "Direct C5 to C6 topology",
        "Publication gate and causal controls",
        "Scope boundary",
    )
    first = outlines.raw_get("/First")
    last = outlines.raw_get("/Last")
    current: object | None = first
    previous: object | None = None
    seen: set[tuple[object, ...]] = set()
    titles: list[str] = []
    while current is not None:
        identity = reference_key(current)
        if identity in seen or len(seen) >= 16:
            raise ValueError("outline list is cyclic or exceeds its bound")
        seen.add(identity)
        item = resolve(current)
        if not isinstance(item, DictionaryObject):
            raise ValueError("outline item is not a dictionary")
        keys = set(map(str, item.keys()))
        expected_keys = {"/Title", "/A", "/Parent"}
        if previous is not None:
            expected_keys.add("/Prev")
        if item.get("/Next") is not None:
            expected_keys.add("/Next")
        if keys != expected_keys:
            raise ValueError("outline item keys changed")
        if reference_key(item.raw_get("/Parent")) != reference_key(raw_outlines):
            raise ValueError("outline item parent changed")
        if previous is not None and reference_key(item.raw_get("/Prev")) != reference_key(previous):
            raise ValueError("outline previous link changed")
        title = str(item["/Title"])
        titles.append(title)
        validate_goto_action(item["/A"], named, report, f"outline {title!r}")
        previous = current
        current = item.raw_get("/Next") if "/Next" in item else None
    if tuple(titles) != expected_titles or previous is None or reference_key(previous) != reference_key(last):
        raise ValueError("outline order, titles, or last link changed")


def validate_catalog(report: PdfReader) -> None:
    root = report.trailer["/Root"]
    if set(map(str, root.keys())) != {
        "/Type", "/Pages", "/Outlines", "/Names", "/PageMode", "/OpenAction"
    }:
        raise ValueError("catalog key inventory changed")
    if str(root.get("/Type")) != "/Catalog" or str(root.get("/PageMode")) != "/UseOutlines":
        raise ValueError("catalog type or page mode changed")
    names = resolve(root["/Names"])
    if not isinstance(names, DictionaryObject) or set(map(str, names.keys())) != {"/Dests"}:
        raise ValueError("catalog Names is malformed or contains an unbounded name tree")
    named = validate_name_tree(names.raw_get("/Dests"), report)
    validate_goto_action(root["/OpenAction"], named, report, "catalog OpenAction")
    open_destination = resolve(resolve(root["/OpenAction"])["/D"])
    first_page = report.pages[0].indirect_reference
    if (
        not isinstance(open_destination, ArrayObject)
        or len(open_destination) != 2
        or str(open_destination[1]) != "/Fit"
        or first_page is None
        or reference_key(open_destination[0]) != reference_key(first_page)
    ):
        raise ValueError("catalog OpenAction does not target the first page with /Fit")
    validate_outlines(root.raw_get("/Outlines"), named, report)


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


def decoded_nonempty_stream(value: object, label: str) -> bytes:
    value = resolve(value)
    if not isinstance(value, StreamObject):
        raise ValueError(f"{label} is not a stream")
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


def expanded_encoding(value: object) -> tuple[str, object]:
    value = resolve(value)
    if isinstance(value, NameObject):
        return "named", str(value)
    if not isinstance(value, DictionaryObject) or set(map(str, value.keys())) != {
        "/Type", "/Differences"
    } or str(value.get("/Type")) != "/Encoding":
        raise ValueError("font encoding is outside the bounded routes")
    differences = resolve(value["/Differences"])
    if not isinstance(differences, ArrayObject) or not differences:
        raise ValueError("font encoding Differences are absent")
    mapping: dict[int, str] = {}
    code: int | None = None
    for item in differences:
        item = resolve(item)
        if isinstance(item, (NumberObject, int)):
            code = int(item)
            if not 0 <= code <= 255:
                raise ValueError("font encoding Differences code is out of range")
        elif isinstance(item, NameObject) and code is not None:
            if code in mapping or code > 255:
                raise ValueError("font encoding Differences repeat or overflow a code")
            mapping[code] = str(item)
            code += 1
        else:
            raise ValueError("font encoding Differences item is malformed")
    return "differences", tuple(sorted(mapping.items()))


def validate_font_resource_equivalence(form_value: object, figure_value: object) -> None:
    form_resources = resolve(form_value)
    figure_resources = resolve(figure_value)
    if not isinstance(form_resources, DictionaryObject) or not isinstance(
        figure_resources, DictionaryObject
    ):
        raise ValueError("figure resources are not dictionaries")
    expected_categories = {"/ExtGState", "/Pattern", "/Font"}
    if set(map(str, form_resources.keys())) != expected_categories or set(
        map(str, figure_resources.keys())
    ) != expected_categories:
        raise ValueError("embedded/standalone resource-category inventories differ")
    for category in ("/ExtGState", "/Pattern"):
        if canonical_object(form_resources[category]) != canonical_object(
            figure_resources[category]
        ):
            raise ValueError(f"embedded/standalone {category} resources differ")

    form_fonts = resolve(form_resources["/Font"])
    figure_fonts = resolve(figure_resources["/Font"])
    if not isinstance(form_fonts, DictionaryObject) or not isinstance(
        figure_fonts, DictionaryObject
    ) or set(map(str, form_fonts.keys())) != set(map(str, figure_fonts.keys())) or not form_fonts:
        raise ValueError("embedded/standalone font-resource inventories differ")
    for resource_name in sorted(form_fonts, key=str):
        form_font = resolve(form_fonts[resource_name])
        figure_font = resolve(figure_fonts[resource_name])
        if not isinstance(form_font, DictionaryObject) or not isinstance(
            figure_font, DictionaryObject
        ):
            raise ValueError(f"font resource {resource_name} is not a dictionary")
        for field in ("/Type", "/Subtype"):
            if str(form_font.get(field)) != str(figure_font.get(field)):
                raise ValueError(f"font resource {resource_name} {field} differs")
        if str(form_font.get("/Subtype")) != "/Type1":
            raise ValueError(f"font resource {resource_name} is not bounded Type1")
        if subset_neutral_font_name(form_font.get("/BaseFont")) != subset_neutral_font_name(
            figure_font.get("/BaseFont")
        ):
            raise ValueError(f"font resource {resource_name} family differs")
        for field in ("/FirstChar", "/LastChar"):
            if int(form_font.get(field, -1)) != int(figure_font.get(field, -1)):
                raise ValueError(f"font resource {resource_name} {field} differs")
        if canonical_object(form_font.get("/Widths")) != canonical_object(
            figure_font.get("/Widths")
        ):
            raise ValueError(f"font resource {resource_name} widths differ")
        if decoded_nonempty_stream(
            form_font.get("/ToUnicode"), f"embedded font {resource_name} ToUnicode"
        ) != decoded_nonempty_stream(
            figure_font.get("/ToUnicode"), f"standalone font {resource_name} ToUnicode"
        ):
            raise ValueError(f"font resource {resource_name} Unicode map differs")
        form_encoding = expanded_encoding(form_font.get("/Encoding"))
        figure_encoding = expanded_encoding(figure_font.get("/Encoding"))
        encoding_equal = form_encoding == figure_encoding
        expanded_winansi = (
            figure_encoding == ("named", "/WinAnsiEncoding")
            and form_encoding[0] == "differences"
            and tuple(code for code, _name in form_encoding[1]) == tuple(range(32, 256))
        )
        if not encoding_equal and not expanded_winansi:
            raise ValueError(f"font resource {resource_name} encoding route differs")
        for label, font in (("embedded", form_font), ("standalone", figure_font)):
            descriptor = resolve(font.get("/FontDescriptor"))
            if not isinstance(descriptor, DictionaryObject):
                raise ValueError(f"{label} font {resource_name} descriptor is absent")
            programs = [
                descriptor.get(field)
                for field in ("/FontFile", "/FontFile2", "/FontFile3")
                if descriptor.get(field) is not None
            ]
            if len(programs) != 1:
                raise ValueError(f"{label} font {resource_name} embedding changed")
            decoded_nonempty_stream(programs[0], f"{label} font {resource_name} program")


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


def canonical_object(value: object, active: set[int] | None = None) -> object:
    value = resolve(value)
    stack = set() if active is None else active
    if isinstance(value, (DictionaryObject, ArrayObject)):
        identity = id(value)
        if identity in stack:
            return ("cycle",)
        stack.add(identity)
        try:
            if isinstance(value, StreamObject):
                items = tuple(
                    (str(key), canonical_object(item, stack))
                    for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
                    if str(key) != "/Length"
                )
                return ("stream", items, sha256(value.get_data()).hexdigest())
            if isinstance(value, DictionaryObject):
                return (
                    "dictionary",
                    tuple(
                        (str(key), canonical_object(item, stack))
                        for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
                    ),
                )
            return ("array", tuple(canonical_object(item, stack) for item in value))
        finally:
            stack.remove(identity)
    if isinstance(value, NameObject):
        return ("name", str(value))
    if isinstance(value, TextStringObject):
        return ("text", str(value))
    if isinstance(value, ByteStringObject):
        return ("bytes", bytes(value).hex())
    if isinstance(value, BooleanObject):
        return ("boolean", bool(value))
    if isinstance(value, NullObject):
        return ("null",)
    if isinstance(value, (NumberObject, FloatObject, int, float)):
        return ("number", str(value))
    return ("atom", type(value).__name__, str(value))


def reference_identity(reference: object, value: object) -> tuple[object, ...]:
    if hasattr(reference, "idnum"):
        return (
            "indirect",
            getattr(reference, "idnum"),
            getattr(reference, "generation", 0),
        )
    return ("direct", id(value))


def reject_raster_content(
    contents: object,
    resources: object,
    owner: object,
    label: str,
    seen: set[tuple[object, ...]] | None = None,
) -> None:
    visited = set() if seen is None else seen
    if contents is not None:
        try:
            operations = pypdf.generic.ContentStream(contents, owner).operations
        except Exception as error:
            raise ValueError(f"{label} content stream cannot be parsed: {error}") from error
        if any(operator == b"INLINE IMAGE" for _operands, operator in operations):
            raise ValueError(f"{label} contains an inline raster image")
    resources = resolve(resources)
    if not isinstance(resources, DictionaryObject):
        raise ValueError(f"{label} resources are not a dictionary")

    raw_xobjects = resources.get("/XObject")
    if raw_xobjects is not None:
        xobjects = resolve(raw_xobjects)
        if not isinstance(xobjects, DictionaryObject):
            raise ValueError(f"{label} XObject inventory is not a dictionary")
        for reference in xobjects.values():
            value = resolve(reference)
            if not isinstance(value, DictionaryObject):
                raise ValueError(f"{label} XObject is not a dictionary")
            identity = reference_identity(reference, value)
            if identity in visited:
                continue
            visited.add(identity)
            subtype = str(value.get("/Subtype"))
            if subtype == "/Image":
                raise ValueError(f"{label} contains a raster image XObject")
            if subtype == "/Form":
                reject_raster_content(
                    value, value.get("/Resources"), owner, label, visited
                )
            elif subtype != "/Image":
                raise ValueError(f"{label} contains unsupported XObject subtype {subtype!r}")

    raw_patterns = resources.get("/Pattern")
    if raw_patterns is not None:
        patterns = resolve(raw_patterns)
        if not isinstance(patterns, DictionaryObject):
            raise ValueError(f"{label} Pattern inventory is not a dictionary")
        for reference in patterns.values():
            pattern = resolve(reference)
            if not isinstance(pattern, DictionaryObject):
                raise ValueError(f"{label} Pattern is not a dictionary")
            identity = reference_identity(reference, pattern)
            if identity in visited:
                continue
            visited.add(identity)
            pattern_type = int(pattern.get("/PatternType", 0))
            if pattern_type == 1:
                if not isinstance(pattern, StreamObject):
                    raise ValueError(f"{label} tiling Pattern is not a stream")
                reject_raster_content(
                    pattern, pattern.get("/Resources"), owner, label, visited
                )
            elif pattern_type != 2:
                raise ValueError(f"{label} contains unsupported PatternType {pattern_type}")

    raw_extgstates = resources.get("/ExtGState")
    if raw_extgstates is not None:
        extgstates = resolve(raw_extgstates)
        if not isinstance(extgstates, DictionaryObject):
            raise ValueError(f"{label} ExtGState inventory is not a dictionary")
        for reference in extgstates.values():
            extgstate = resolve(reference)
            if not isinstance(extgstate, DictionaryObject):
                raise ValueError(f"{label} ExtGState is not a dictionary")
            raw_smask = extgstate.get("/SMask")
            if raw_smask is None or str(resolve(raw_smask)) == "/None":
                continue
            smask = resolve(raw_smask)
            if not isinstance(smask, DictionaryObject) or smask.get("/G") is None:
                raise ValueError(f"{label} soft mask is malformed")
            group_reference = smask["/G"]
            group = resolve(group_reference)
            if not isinstance(group, StreamObject) or str(group.get("/Subtype")) != "/Form":
                raise ValueError(f"{label} soft-mask group is not a Form")
            identity = reference_identity(group_reference, group)
            if identity in visited:
                continue
            visited.add(identity)
            reject_raster_content(
                group, group.get("/Resources"), owner, label, visited
            )

    raw_fonts = resources.get("/Font")
    if raw_fonts is not None:
        fonts = resolve(raw_fonts)
        if not isinstance(fonts, DictionaryObject):
            raise ValueError(f"{label} Font inventory is not a dictionary")
        for reference in fonts.values():
            font = resolve(reference)
            if not isinstance(font, DictionaryObject):
                raise ValueError(f"{label} font is not a dictionary")
            if str(font.get("/Subtype")) != "/Type3":
                continue
            identity = reference_identity(reference, font)
            if identity in visited:
                continue
            visited.add(identity)
            font_resources = font.get("/Resources")
            reject_raster_content(None, font_resources, owner, label, visited)
            char_procs = resolve(font.get("/CharProcs"))
            if not isinstance(char_procs, DictionaryObject) or not char_procs:
                raise ValueError(f"{label} Type3 CharProcs are absent")
            for char_reference in char_procs.values():
                char_proc = resolve(char_reference)
                if not isinstance(char_proc, StreamObject):
                    raise ValueError(f"{label} Type3 CharProc is not a stream")
                reject_raster_content(
                    char_proc, font_resources, owner, label, visited
                )


def validate_standalone(figure: PdfReader) -> tuple[object, set[str]]:
    if len(figure.pages) != 1:
        raise ValueError("standalone figure page inventory changed")
    figure_root = figure.trailer["/Root"]
    if set(map(str, figure_root.keys())) != {"/Type", "/Pages"} or str(
        figure_root.get("/Type")
    ) != "/Catalog":
        raise ValueError("standalone figure catalog key inventory changed")
    standalone = figure.pages[0]
    standalone_keys = set(map(str, standalone.keys()))
    if not {
        "/Type", "/Parent", "/MediaBox", "/Contents", "/Group", "/Resources",
        "/StructParents",
    } <= standalone_keys or standalone_keys - {
        "/Type", "/Parent", "/MediaBox", "/CropBox", "/Contents", "/Group",
        "/Resources", "/StructParents",
    }:
        raise ValueError("standalone figure page key inventory changed")
    expected_figure_box = (0.0, 0.0, 453.543307, 255.11811)
    if standalone.get("/Annots") is not None or standalone.get("/AA") is not None:
        raise ValueError("standalone figure contains annotations or additional actions")
    if not close_box(box(standalone.mediabox), expected_figure_box) or not close_box(
        box(standalone.cropbox), expected_figure_box
    ):
        raise ValueError("standalone figure page box changed")
    for key in ("/BleedBox", "/TrimBox", "/ArtBox"):
        if standalone.get(key) is not None and not close_box(box(standalone.get(key)), expected_figure_box):
            raise ValueError(f"standalone figure {key} changed")
    if int(standalone.get("/Rotate", 0)) != 0 or float(standalone.get("/UserUnit", 1)) != 1.0:
        raise ValueError("standalone figure rotation or UserUnit changed")
    reject_raster_content(
        standalone.get_contents(), standalone.get("/Resources"), figure, "standalone figure"
    )
    return standalone, font_families(standalone.get("/Resources"))


def validate(report: PdfReader, figure: PdfReader, expected_pages: int, figure_page: int) -> None:
    if len(report.pages) != expected_pages:
        raise ValueError("report page inventory changed")
    validate_catalog(report)
    a4 = (0.0, 0.0, 595.276, 841.89)
    for number, page in enumerate(report.pages, start=1):
        page_keys = set(map(str, page.keys()))
        if not {"/Type", "/Contents", "/Resources", "/MediaBox", "/Parent"} <= page_keys or page_keys - {
            "/Type", "/Contents", "/Resources", "/MediaBox", "/Parent", "/Group"
        }:
            raise ValueError(f"page {number} key inventory changed")
        if page.get("/Annots") is not None:
            raise ValueError(f"page {number} contains annotations")
        if page.get("/AA") is not None:
            raise ValueError(f"page {number} contains an additional action")
        if page.get("/AF") is not None:
            raise ValueError(f"page {number} contains an associated file")
        if not close_box(box(page.mediabox), a4) or not close_box(box(page.cropbox), a4):
            raise ValueError(f"page {number} is not zero-origin A4")
        for key in ("/BleedBox", "/TrimBox", "/ArtBox"):
            if page.get(key) is not None and not close_box(box(page.get(key)), a4):
                raise ValueError(f"page {number} {key} changed")
        if int(page.get("/Rotate", 0)) != 0 or float(page.get("/UserUnit", 1)) != 1.0:
            raise ValueError(f"page {number} rotation or UserUnit changed")
        reject_raster_content(
            page.get_contents(), page.get("/Resources"), report, f"report page {number}"
        )
    standalone, standalone_fonts = validate_standalone(figure)
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
    if canonical_object(form.get("/Group")) != canonical_object(standalone.get("/Group")):
        raise ValueError("embedded/standalone transparency groups differ")
    form_resources = form.get("/Resources")
    standalone_resources = standalone.get("/Resources")
    validate_font_resource_equivalence(form_resources, standalone_resources)
    if font_families(form_resources) != standalone_fonts:
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
    if (
        placement[0] <= 0
        or placement[3] <= 0
        or abs(placement[1]) > 1e-6
        or abs(placement[2]) > 1e-6
    ):
        raise ValueError("figure Form placement is reflected, rotated, or skewed")
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
overlay_path = Path(sys.argv[7])
font_program_path = Path(sys.argv[8])
try:
    # Both TeX report lanes reference the committed standalone figure.  The fresh
    # standalone figure is a separate portability operand, never a Cartesian substitute.
    associated_figure = PdfReader(figures[1], strict=True)
    _fresh_page, fresh_fonts = validate_standalone(PdfReader(figures[0], strict=True))
    _associated_page, associated_fonts = validate_standalone(associated_figure)
    if fresh_fonts != associated_fonts:
        raise ValueError("fresh/committed standalone font-family inventories differ")
    for report_path in reports:
        validate(PdfReader(report_path, strict=True), associated_figure, pages, figure_page)
except Exception as error:
    fail(str(error))

# Exact hostile objects exercise the predicates, rather than a checksum-only rejection.
raw = reports[0].read_bytes()
figure = PdfReader(figures[1], strict=True)
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
catalog_extra = PdfReader(BytesIO(raw), strict=True)
catalog_extra.trailer["/Root"][NameObject("/AA")] = DictionaryObject()
outline_uri = PdfReader(BytesIO(raw), strict=True)
outline_first = resolve(resolve(outline_uri.trailer["/Root"]["/Outlines"])["/First"])
outline_first[NameObject("/A")] = DictionaryObject({
    NameObject("/S"): NameObject("/URI"),
    NameObject("/D"): TextStringObject("https://example.invalid/unsafe"),
})
relocated = PdfReader(BytesIO(raw), strict=True)
source_resources = resolve(relocated.pages[figure_page - 1]["/Resources"])
target_resources = resolve(relocated.pages[figure_page]["/Resources"])
target_resources[NameObject("/XObject")] = source_resources.pop(NameObject("/XObject"))
empty_resources = PdfReader(BytesIO(raw), strict=True)
forms(empty_resources)[0][2][NameObject("/Resources")] = DictionaryObject()
resource_inventory_drift = PdfReader(BytesIO(raw), strict=True)
inventory_resources = resolve(forms(resource_inventory_drift)[0][2]["/Resources"])
inventory_resources.pop(NameObject("/Pattern"))
nonfont_drift = PdfReader(BytesIO(raw), strict=True)
nonfont_form_resources = resolve(forms(nonfont_drift)[0][2]["/Resources"])
nonfont_extgstates = resolve(nonfont_form_resources["/ExtGState"])
nonfont_extgstate = resolve(next(iter(nonfont_extgstates.values())))
nonfont_extgstate[NameObject("/ca")] = FloatObject(0.5)
encoding_drift = PdfReader(BytesIO(raw), strict=True)
encoding_fonts = resolve(resolve(forms(encoding_drift)[0][2]["/Resources"])["/Font"])
resolve(next(iter(encoding_fonts.values())))[NameObject("/Encoding")] = NameObject(
    "/MacRomanEncoding"
)
unicode_drift = PdfReader(BytesIO(raw), strict=True)
unicode_fonts = resolve(resolve(forms(unicode_drift)[0][2]["/Resources"])["/Font"])
unicode_font = resolve(next(iter(unicode_fonts.values())))
unicode_stream = resolve(unicode_font["/ToUnicode"])
unicode_hostile_stream = DecodedStreamObject()
unicode_hostile_stream.set_data(
    unicode_stream.get_data() + b"\n% hostile Unicode-map drift\n"
)
unicode_font[NameObject("/ToUnicode")] = unicode_hostile_stream
width_drift = PdfReader(BytesIO(raw), strict=True)
width_fonts = resolve(resolve(forms(width_drift)[0][2]["/Resources"])["/Font"])
width_font = resolve(next(iter(width_fonts.values())))
widths = resolve(width_font["/Widths"])
widths[0] = NumberObject(int(widths[0]) + 1)
clip_writer = PdfWriter(clone_from=BytesIO(raw))
clip_page = clip_writer.pages[figure_page - 1]
clip_name = forms(clip_writer)[0][1]
clip_stream = pypdf.generic.ContentStream(clip_page.get_contents(), clip_writer)
clip_indices = [
    index
    for index, (operands, op) in enumerate(clip_stream.operations)
    if op == b"Do" and str(operands[0]) == clip_name
]
if len(clip_indices) != 1:
    fail("clipping hostile cannot locate the figure invocation")
clip_stream.operations[clip_indices[0]:clip_indices[0]] = [
    ([NumberObject(0), NumberObject(0), NumberObject(10), NumberObject(10)], b"re"),
    ([], b"W"),
    ([], b"n"),
]
clip_page.replace_contents(clip_stream)
clip_buffer = BytesIO()
clip_writer.write(clip_buffer)
clip_writer.close()
clipped = PdfReader(BytesIO(clip_buffer.getvalue()), strict=True)
for hostile in (wrong_box, annotated, matrix, zero_scale, scripted, catalog_extra, relocated, empty_resources, clipped):
    try:
        validate(hostile, figure, pages, figure_page)
    except ValueError:
        pass
    else:
        fail("an object-structure hostile control was accepted")
try:
    validate(outline_uri, figure, pages, figure_page)
except ValueError as error:
    if "is not the bounded internal GoTo" not in str(error):
        fail(f"the outline-action hostile was rejected noncausally: {error}")
else:
    fail("the outline-action hostile control was accepted")
for hostile, expected, label in (
    (
        resource_inventory_drift,
        "resource-category inventories differ",
        "resource-inventory",
    ),
    (nonfont_drift, "/ExtGState resources differ", "non-font-resource"),
    (encoding_drift, "encoding route differs", "font-encoding"),
    (unicode_drift, "Unicode map differs", "font-Unicode-map"),
    (width_drift, "widths differ", "font-widths"),
):
    try:
        validate(hostile, figure, pages, figure_page)
    except ValueError as error:
        if expected not in str(error):
            fail(f"the {label} hostile was rejected noncausally: {error}")
    else:
        fail(f"the {label} hostile control was accepted")
rotated_figure = PdfReader(figures[0], strict=True)
rotated_figure.pages[0][NameObject("/Rotate")] = NumberObject(90)
try:
    validate(PdfReader(reports[0], strict=True), rotated_figure, pages, figure_page)
except ValueError:
    pass
else:
    fail("the standalone-figure geometry hostile control was accepted")
def expect_standalone_rejection(candidate: PdfReader, expected: str, label: str) -> None:
    try:
        validate_standalone(candidate)
    except ValueError as error:
        if expected not in str(error):
            fail(f"the {label} hostile was rejected noncausally: {error}")
    else:
        fail(f"the {label} hostile control was accepted")


raster_figure = PdfReader(figures[1], strict=True)
raster_resources = resolve(raster_figure.pages[0]["/Resources"])
raster_xobjects = resolve(raster_resources.get("/XObject", DictionaryObject()))
if not isinstance(raster_xobjects, DictionaryObject):
    fail("raster hostile cannot obtain the standalone XObject inventory")
raster_xobjects[NameObject("/ImHostile")] = DictionaryObject({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/Image"),
})
raster_resources[NameObject("/XObject")] = raster_xobjects
expect_standalone_rejection(raster_figure, "raster image XObject", "raster-image")

pattern_raster = PdfReader(figures[1], strict=True)
pattern_resources = resolve(pattern_raster.pages[0]["/Resources"])
patterns = resolve(pattern_resources["/Pattern"])
pattern = resolve(next(iter(patterns.values())))
pattern_xobjects = resolve(resolve(pattern["/Resources"])["/XObject"])
pattern_xobject = resolve(next(iter(pattern_xobjects.values())))
pattern_xobject[NameObject("/Subtype")] = NameObject("/Image")
expect_standalone_rejection(
    pattern_raster, "raster image XObject", "Pattern-reachable-raster"
)

inline_raster = PdfReader(figures[1], strict=True)
inline_resources = resolve(inline_raster.pages[0]["/Resources"])
inline_xobjects = resolve(inline_resources.get("/XObject", DictionaryObject()))
inline_form = DecodedStreamObject()
inline_form.update({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/Form"),
    NameObject("/BBox"): ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
    ),
    NameObject("/Resources"): DictionaryObject(),
})
inline_form.set_data(
    b"q\nBI /W 1 /H 1 /BPC 8 /CS /DeviceGray ID \x00 EI\nQ\n"
)
inline_xobjects[NameObject("/InlineHostile")] = inline_form
inline_resources[NameObject("/XObject")] = inline_xobjects
expect_standalone_rejection(inline_raster, "inline raster image", "inline-image")

type3_raster = PdfReader(figures[1], strict=True)
type3_resources = resolve(type3_raster.pages[0]["/Resources"])
type3_fonts = resolve(type3_resources["/Font"])
type3_image = DictionaryObject({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/Image"),
})
type3_char = DecodedStreamObject()
type3_char.set_data(b"")
type3_font = DictionaryObject({
    NameObject("/Type"): NameObject("/Font"),
    NameObject("/Subtype"): NameObject("/Type3"),
    NameObject("/Resources"): DictionaryObject({
        NameObject("/XObject"): DictionaryObject(
            {NameObject("/ImHostile"): type3_image}
        )
    }),
    NameObject("/CharProcs"): DictionaryObject(
        {NameObject("/a"): type3_char}
    ),
})
type3_fonts[NameObject("/Type3Hostile")] = type3_font
expect_standalone_rejection(
    type3_raster, "raster image XObject", "Type3-reachable-raster"
)

smask_raster = PdfReader(figures[1], strict=True)
smask_resources = resolve(smask_raster.pages[0]["/Resources"])
smask_extgstates = resolve(smask_resources["/ExtGState"])
smask_image = DictionaryObject({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/Image"),
})
smask_group = DecodedStreamObject()
smask_group.update({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/Form"),
    NameObject("/BBox"): ArrayObject(
        [NumberObject(0), NumberObject(0), NumberObject(1), NumberObject(1)]
    ),
    NameObject("/Resources"): DictionaryObject({
        NameObject("/XObject"): DictionaryObject(
            {NameObject("/ImHostile"): smask_image}
        )
    }),
})
smask_group.set_data(b"")
smask_extgstates[NameObject("/SMaskHostile")] = DictionaryObject({
    NameObject("/SMask"): DictionaryObject({
        NameObject("/S"): NameObject("/Alpha"),
        NameObject("/G"): smask_group,
    })
})
expect_standalone_rejection(
    smask_raster, "raster image XObject", "soft-mask-reachable-raster"
)

unsupported_xobject = PdfReader(figures[1], strict=True)
unsupported_resources = resolve(unsupported_xobject.pages[0]["/Resources"])
unsupported_xobjects = resolve(unsupported_resources.get("/XObject", DictionaryObject()))
unsupported_xobjects[NameObject("/PSHostile")] = DictionaryObject({
    NameObject("/Type"): NameObject("/XObject"),
    NameObject("/Subtype"): NameObject("/PS"),
})
unsupported_resources[NameObject("/XObject")] = unsupported_xobjects
expect_standalone_rejection(
    unsupported_xobject, "unsupported XObject subtype", "unsupported-XObject"
)

unsupported_pattern = PdfReader(figures[1], strict=True)
unsupported_pattern_resources = resolve(unsupported_pattern.pages[0]["/Resources"])
unsupported_patterns = resolve(unsupported_pattern_resources["/Pattern"])
resolve(next(iter(unsupported_patterns.values())))[NameObject("/PatternType")] = NumberObject(99)
expect_standalone_rejection(
    unsupported_pattern, "unsupported PatternType", "unsupported-PatternType"
)

# A safe but unreferenced standalone lane must not substitute for the figure
# actually embedded by TeX.  Appending a balanced no-op makes that lane exact-byte
# different without introducing an unsafe object.
lane_writer = PdfWriter(clone_from=figures[1])
lane_page = lane_writer.pages[0]
lane_stream = pypdf.generic.ContentStream(lane_page.get_contents(), lane_writer)
lane_stream.operations.extend([([], b"q"), ([], b"Q")])
lane_page.replace_contents(lane_stream)
lane_buffer = BytesIO()
lane_writer.write(lane_buffer)
lane_writer.close()
wrong_lane = PdfReader(BytesIO(lane_buffer.getvalue()), strict=True)
validate_standalone(wrong_lane)
try:
    validate(PdfReader(reports[0], strict=True), wrong_lane, pages, figure_page)
except ValueError as error:
    if "embedded Form content differs" not in str(error):
        fail(f"wrong-lane hostile was rejected noncausally: {error}")
else:
    fail("the wrong-lane association hostile control was accepted")

# Emit a structurally safe, visibly different report for the later raster-bound
# hostile.  Its large vector overlay must survive rendering and exceed the bound.
overlay_writer = PdfWriter(clone_from=BytesIO(raw))
overlay_page = overlay_writer.pages[0]
overlay_stream = pypdf.generic.ContentStream(overlay_page.get_contents(), overlay_writer)
overlay_stream.operations.extend([
    ([], b"q"),
    ([NumberObject(0), NumberObject(0), NumberObject(0)], b"rg"),
    ([NumberObject(60), NumberObject(80), NumberObject(240), NumberObject(240)], b"re"),
    ([], b"f"),
    ([], b"Q"),
])
overlay_page.replace_contents(overlay_stream)
with overlay_path.open("wb") as stream:
    overlay_writer.write(stream)
overlay_writer.close()

# A same-family font-program substitution preserves resource names, widths,
# encodings, and ToUnicode bytes. It must pass bounded object semantics and be
# rejected causally by the rendered-pixel predicate.
font_writer = PdfWriter(clone_from=BytesIO(raw))
font_form = forms(font_writer)[0][2]
font_resources = resolve(resolve(font_form["/Resources"])["/Font"])
programs: dict[str, tuple[DictionaryObject, str, object]] = {}
for resource_name, reference in font_resources.items():
    font = resolve(reference)
    descriptor = resolve(font["/FontDescriptor"])
    fields = [
        field
        for field in ("/FontFile", "/FontFile2", "/FontFile3")
        if descriptor.get(field) is not None
    ]
    if len(fields) != 1:
        fail(f"font-program hostile found invalid embedding at {resource_name}")
    programs[subset_neutral_font_name(font.get("/BaseFont"))] = (
        descriptor,
        fields[0],
        descriptor[fields[0]],
    )
expected_programs = {
    "SourceSansPro-Bold", "SourceSansPro-Semibold", "LMRoman10-Regular"
}
if set(programs) != expected_programs:
    fail("font-program hostile found an unexpected family inventory")
roman_program = programs["LMRoman10-Regular"][2]
for family in ("SourceSansPro-Bold", "SourceSansPro-Semibold"):
    descriptor, field, _program = programs[family]
    descriptor[NameObject(field)] = roman_program
with font_program_path.open("wb") as stream:
    font_writer.write(stream)
font_writer.close()
try:
    validate(PdfReader(font_program_path, strict=True), figure, pages, figure_page)
except Exception as error:
    fail(f"font-program hostile was rejected before raster comparison: {error}")
PY

for candidate in "$FIGURE_A" "$FIGURE_PDF" "$BUILT" "$PDF"; do
  pdffonts "$candidate" | awk '
    NR > 2 { seen=1; if ($(NF-4)!="yes" || $(NF-3)!="yes" || $(NF-2)!="yes") bad=1 }
    END { exit (!seen || bad) }
  ' || fail "every font must be embedded, subset, and Unicode-mapped: $candidate"
done

font_inventory() {
  pdffonts "$1" | awk '
    NR > 2 {
      name=$1
      sub(/^[A-Z][A-Z][A-Z][A-Z][A-Z][A-Z]\+/, "", name)
      print name
    }
  ' | sort -u
}
font_inventory "$FIGURE_A" >"$BUILD_ROOT/figure-fresh.fonts"
font_inventory "$FIGURE_PDF" >"$BUILD_ROOT/figure-committed.fonts"
font_inventory "$BUILT" >"$BUILD_ROOT/report-fresh.fonts"
font_inventory "$PDF" >"$BUILD_ROOT/report-committed.fonts"
cmp -s "$BUILD_ROOT/figure-fresh.fonts" "$BUILD_ROOT/figure-committed.fonts" || \
  fail "fresh/committed standalone font-family inventories differ"
cmp -s "$BUILD_ROOT/report-fresh.fonts" "$BUILD_ROOT/report-committed.fonts" || \
  fail "fresh/committed report font-family inventories differ"

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
  "Q5 = L5 ∧ CI5 ∧ CodeQL5 ∧ D5"
  "L5 is one fresh local qualification observation for exact C5"
  "hosted CI5 , CodeQL5 , and D5 terms require terminal success at attempt 1"
  "with no attempt-number or first-attempt authority"
  "D5 = false"
  "R5 permanently unissued"
  "C6 is an exact unsigned single-parent direct child of C5"
  "The Cartesian association failure surface"
  "composite-v4 process PDF check: PDF object structure changed: embedded custody Form content differs from the standalone figure"
  "composite-v5 boundary PDF check: PDF structure embedded Form content differs from standalone figure"
  "same named Cartesian association-rule failure surface"
  "wrong-lane comparisons"
  "committed figure referenced by TeX"
  "Q6 = L6 ∧ CI6 ∧ CodeQL6 ∧ D6"
  "L6 is local static, hostile, replay, source-state, and publication closure"
  "43-path delta: 21 modifications and 22 additions"
  "A typed local record establishes L6 only after receipt validation"
  "just ksg-composite-v6"
  "R6 has exactly four path changes"
  "The local record is not an attempt-number or first-attempt authority."
  "does not pass ambient variables to the command"
  "bounded scans reject named secret-like patterns and private-path prefixes"
  "distinct stable mode-0600 file descriptors 3 and 4"
  "accepts no successor-capture/evidentiary stdin route"
  "The clean endpoints use ordinary Git status plus selected metadata checks; rejecting core.excludesFile removes one ignore-routing overlay, but repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure."
  "issue(R6) ⇐⇒ Q6"
  "wrong-lane Cartesian substitution rejects"
  "same-renderer raster predicates"
  "zero PID theories, zero PID functionals, zero estimators"
  "Nothing transfers among categorical or continuous"
  "no authentication, attestation"
  "not renderer independence"
)
for sentinel in "${required_text[@]}"; do
  grep -F -- "$sentinel" "$BUILD_ROOT/built.semantic.normalized.txt" >/dev/null || \
    fail "required PDF text is absent: $sentinel"
done
for page in $(seq 1 "$EXPECTED_PAGES"); do
  pdftotext -f "$page" -l "$page" "$BUILT" "$BUILD_ROOT/page-$page.txt"
  if [[ "$page" == "$EXPECTED_FIGURE_PAGE" ]]; then
    grep -F -- "Append-only portability boundary" "$BUILD_ROOT/page-$page.txt" >/dev/null || \
      fail "figure caption is absent from page $page"
    grep -F -- "R5 UNISSUED" "$BUILD_ROOT/page-$page.txt" >/dev/null || \
      fail "figure text is absent from page $page"
  elif grep -F -- "R5 UNISSUED" "$BUILD_ROOT/page-$page.txt" >/dev/null; then
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
RASTER_OVERLAY_COLOR="$BUILD_ROOT/raster-overlay-color"
FONT_PROGRAM_COLOR="$BUILD_ROOT/font-program-color"
render_pages "$BUILT" "$BUILT_COLOR" built-color color
render_pages "$BUILT" "$BUILT_GRAY" built-gray gray
render_pages "$PDF" "$COMMITTED_COLOR" committed-color color
render_pages "$PDF" "$COMMITTED_GRAY" committed-gray gray
render_pages "$FIGURE_A" "$BUILT_FIGURE_COLOR" built-figure-color color
render_pages "$FIGURE_A" "$BUILT_FIGURE_GRAY" built-figure-gray gray
render_pages "$FIGURE_PDF" "$COMMITTED_FIGURE_COLOR" committed-figure-color color
render_pages "$FIGURE_PDF" "$COMMITTED_FIGURE_GRAY" committed-figure-gray gray
render_pages "$RASTER_OVERLAY_PDF" "$RASTER_OVERLAY_COLOR" raster-overlay-color color
render_pages "$FONT_PROGRAM_PDF" "$FONT_PROGRAM_COLOR" font-program-color color
if compare_sets "$BUILT_COLOR" "$RASTER_OVERLAY_COLOR" "$EXPECTED_PAGES" \
  raster-overlay-hostile "$BUILD_ROOT/raster-overlay-hostile.tsv" \
  >"$BUILD_ROOT/raster-overlay.stdout" 2>"$BUILD_ROOT/raster-overlay.stderr"; then
  fail "the visible raster-overlay hostile control was accepted"
fi
if ! grep -F -- "exceeds its visual bound" "$BUILD_ROOT/raster-overlay.stderr" >/dev/null; then
  cat "$BUILD_ROOT/raster-overlay.stdout" "$BUILD_ROOT/raster-overlay.stderr" >&2
  fail "the visible raster-overlay hostile control was rejected noncausally"
fi
if compare_sets "$BUILT_COLOR" "$FONT_PROGRAM_COLOR" "$EXPECTED_PAGES" \
  font-program-hostile "$BUILD_ROOT/font-program-hostile.tsv" \
  >"$BUILD_ROOT/font-program.stdout" 2>"$BUILD_ROOT/font-program.stderr"; then
  fail "the same-family font-program hostile control was accepted"
fi
if ! grep -F -- "exceeds its visual bound" "$BUILD_ROOT/font-program.stderr" >/dev/null; then
  cat "$BUILD_ROOT/font-program.stdout" "$BUILD_ROOT/font-program.stderr" >&2
  fail "the same-family font-program hostile control was rejected noncausally"
fi
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
    raise SystemExit(f"composite-v6 boundary PDF check: rendering receipt {detail}")

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
    raise SystemExit("composite-v6 boundary PDF check: rendering receipt framing changed")
lines = raw.decode("utf-8", errors="strict").splitlines()
if len(lines) != 5 + 2 * pages:
    raise SystemExit("composite-v6 boundary PDF check: rendering receipt row count changed")
expected_prefix = (
    "schema\tpid-rs-formal-rendering-receipt-v2",
    f"pdf_sha256\t{hashlib.sha256(pdf.read_bytes()).hexdigest()}",
    f"pages\t{pages}",
    f"dpi\t{dpi}",
    "mode\tpage\twidth\theight\tbytes\tsha256\tmin_luma\tmax_luma\tdark_pixels\tchromatic_pixels",
)
if tuple(lines[:5]) != expected_prefix:
    raise SystemExit("composite-v6 boundary PDF check: rendering receipt header/PDF binding changed")
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
        f"composite-v6 boundary PDF check: rendering receipt {error}"
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
            "composite-v6 boundary PDF check: rendering receipt hostile was accepted"
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
    raise SystemExit(f"composite-v6 boundary PDF check: visual receipt {detail}")

receipt,pdf,rendering,svg,figure=map(Path,sys.argv[1:])
raw=receipt.read_bytes()
if not raw.endswith(b"\n") or b"\r" in raw or len(raw)>16384: fail("byte framing changed")
text=raw.decode("utf-8",errors="strict"); lines=text.splitlines()
if lines[:2] != ["# Composite-v6 successor-boundary PDF visual-review receipt",""]: fail("title changed")
order=("schema","subject","pdf_sha256","rendering_receipt","rendering_receipt_sha256","figure_svg","figure_svg_sha256","figure_pdf","figure_pdf_sha256","pages","dpi","color_pages_reviewed","grayscale_pages_reviewed","figure_pages_reviewed","status","review_date_utc","reviewer_kind")
fields={}
for offset,name in enumerate(order,2):
    match=re.fullmatch(rf"{re.escape(name)}: `([^`]+)`",lines[offset]) if offset<len(lines) else None
    if match is None: fail(f"field order/syntax changed at {name}")
    fields[name]=match.group(1)
def digest(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
expected={
 "schema":"pid-rs/composite-v6-boundary-visual-review/v1",
 "subject":"output/pdf/ksg-m1a-composite-v6-boundary.pdf","pdf_sha256":digest(pdf),
 "rendering_receipt":"output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv","rendering_receipt_sha256":digest(rendering),
 "figure_svg":"audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.svg","figure_svg_sha256":digest(svg),
 "figure_pdf":"audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf","figure_pdf_sha256":digest(figure),
 "pages":"4","dpi":"144","color_pages_reviewed":"1-4","grayscale_pages_reviewed":"1-4",
 "figure_pages_reviewed":"report page 3; standalone color and grayscale",
 "status":"passed","review_date_utc":"2026-08-18","reviewer_kind":"publication-lane-agent-visual-inspection",
}
for name,value in expected.items():
    if fields.get(name)!=value: fail(f"field {name} differs")
body_start=3+len(order)
paragraphs=tuple(" ".join(part.split()) for part in "\n".join(lines[body_start:]).strip().split("\n\n") if part.strip())
required=(
 "All four final color pages and all four final grayscale pages were viewed in page order at 144 dpi.",
 "The standalone successor-boundary figure and its page-3 placement were reviewed in color and grayscale at a 1600-by-900-pixel rasterization of its 1600-by-900 viewBox. Failure, nonissuance, correction, fresh qualification, conditional receipt, and nonimplication states remain distinct through text, borders, line styles, and shape as well as color.",
 "Page 1 was checked for title hierarchy, the bounded disposition box, complete definitions of `Q5` and R5 issuance, and legible C5 commit identity.",
 "Page 2 was checked for the terminal hosted-observation table, exact dedicated failure diagnostic, Cartesian association explanation, keyed C6 rule, and a non-orphaned section transition.",
 "Page 3 was checked for direct C5-to-C6 topology, complete definitions of `Q6` and R6 issuance, the durable typed local-closure requirement, a clean native figure, nonoverlapping arrows and badges, a legible caption, and correct reading order.",
 "Page 4 was checked for the publication-gate and causal-control table, same-renderer limitation, zero-science boundary, route nontransfer statement, and terminal nonclaims.",
 "The final PDF contains no annotations, widgets, form field tree, JavaScript, or live relative URI. All four pages are zero-rotation A4 pages.",
 "No blank, clipped, overlapping, misordered, orphaned, or visibly corrupt page, table, equation, or figure element was observed. Color meaning remained distinguishable in grayscale.",
 "The publication-lane agent completed this bounded visual inspection. It grants neither human-review nor dependency-disjoint independence credit.",
 "The clean endpoints use ordinary Git status plus selected metadata checks; rejecting core.excludesFile removes one ignore-routing overlay, but repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure.",
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
  echo "OK: composite-v6 boundary PDF has exact source, vector, object, render, receipt, and same-toolchain custody ($digest)"
else
  echo "OK: composite-v6 boundary PDF has exact source/receipt custody and bounded same-renderer cross-toolchain agreement ($digest)"
fi
