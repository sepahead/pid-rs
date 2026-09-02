#!/usr/bin/env bash
set -euo pipefail

# Build the dated custody addendum from its Markdown, PDF header, Lua link
# projection, and SVG figure. The dedicated checker binds this presentation
# artifact without treating it as scientific or mathematical evidence.

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/audit/evidence/post-publication-custody-2026-09-02.md"
RECORD="$ROOT/audit/evidence/post-publication-custody-2026-09-02.json"
HEADER="$ROOT/audit/evidence/post-publication-custody/header.tex"
FILTER="$ROOT/audit/evidence/post-publication-custody/filter.lua"
SVG="$ROOT/audit/formal/figures/post-publication-custody/state-machine.svg"
FIGURE_DIR="$ROOT/audit/formal/figures/post-publication-custody"
FIGURE="$FIGURE_DIR/state.pdf"
DEFAULT_OUTPUT="$ROOT/output/pdf/post-publication-custody-2026-09-02.pdf"
OUTPUT="${1:-$DEFAULT_OUTPUT}"
SOURCE_DATE_EPOCH_VALUE=1788324182

if [[ "$#" -gt 1 || -z "$OUTPUT" ]]; then
  echo "usage: $0 [output.pdf]" >&2
  exit 2
fi

export LC_ALL=C
export TZ=UTC
umask 022

for tool in chmod cp dirname mkdir mktemp mv pandoc lualatex rsvg-convert pdfinfo pdftotext python3 rm; do
  command -v "$tool" >/dev/null || { echo "missing required tool: $tool" >&2; exit 2; }
done
[ -f "$SOURCE" ] || { echo "missing source: $SOURCE" >&2; exit 2; }
[ -f "$RECORD" ] || { echo "missing record: $RECORD" >&2; exit 2; }
[ -f "$HEADER" ] || { echo "missing header: $HEADER" >&2; exit 2; }
[ -f "$FILTER" ] || { echo "missing filter: $FILTER" >&2; exit 2; }
[ -f "$SVG" ] || { echo "missing figure source: $SVG" >&2; exit 2; }

OUTPUT_DIR="$(dirname -- "$OUTPUT")"
mkdir -p "$FIGURE_DIR" "$OUTPUT_DIR"

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
TMP_BASE="$(cd -- "$TMP_BASE_INPUT" && pwd -P)"
if [[ "$TMP_BASE" == "/" ]]; then
  echo "refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-post-publication-pdf.XXXXXX")"
FIGURE_TEMP=""
OUTPUT_TEMP=""
cleanup() {
  local status="$1"
  trap - EXIT HUP INT TERM
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-post-publication-pdf.*) rm -rf -- "$BUILD_ROOT" ;;
    *)
      echo "refusing unexpected cleanup path: $BUILD_ROOT" >&2
      status=1
      ;;
  esac
  case "$FIGURE_TEMP" in
    "") ;;
    "$FIGURE_DIR"/.state.pdf.*) rm -f -- "$FIGURE_TEMP" ;;
    *)
      echo "refusing unexpected figure cleanup path: $FIGURE_TEMP" >&2
      status=1
      ;;
  esac
  case "$OUTPUT_TEMP" in
    "") ;;
    "$OUTPUT_DIR"/.post-publication-custody.pdf.*) rm -f -- "$OUTPUT_TEMP" ;;
    *)
      echo "refusing unexpected receipt cleanup path: $OUTPUT_TEMP" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 129' HUP
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

BUILT_FIGURE="$BUILD_ROOT/state.pdf"
BUILT="$BUILD_ROOT/post-publication-custody-2026-09-02.pdf"
SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
  rsvg-convert -f pdf -o "$BUILT_FIGURE" "$SVG"

# Pandoc resolves the image relative to the Markdown source. Keep all auxiliary
# files in the private build directory and publish only the final PDF.
PID_CUSTODY_FIGURE_PDF="$BUILT_FIGURE" \
SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
  pandoc \
    --from='gfm+tex_math_dollars' \
    --standalone \
    --pdf-engine=lualatex \
    --include-in-header="$HEADER" \
    --lua-filter="$FILTER" \
    --resource-path="$ROOT/audit/evidence:$ROOT" \
    --variable='fontsize=10pt' \
    --variable='colorlinks=true' \
    --variable='linkcolor=turquoise' \
    --variable='urlcolor=lapis' \
    --output="$BUILT" \
    "$SOURCE"

pages="$(pdfinfo "$BUILT" | awk '/^Pages:/ {print $2}')"
version="$(pdfinfo "$BUILT" | awk '/^PDF version:/ {print $3}')"
[ "${pages:-0}" -ge 1 ] || { echo "PDF has no pages" >&2; exit 1; }

# The Markdown is the human source, the JSON is the machine source, and the PDF
# is a presentation derivative. Check a bounded set of cross-format identity
# fields after extraction; this is not a claim of full semantic equivalence.
pdftotext -layout "$BUILT" "$BUILD_ROOT/receipt.txt"
pdftotext -bbox-layout "$BUILT" "$BUILD_ROOT/receipt-bbox.html"
python3 -I -S -B - "$RECORD" "$SOURCE" "$BUILD_ROOT/receipt.txt" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

record_path, source_path, text_path = map(Path, sys.argv[1:])
record = json.loads(record_path.read_text(encoding="utf-8"))
source = source_path.read_text(encoding="utf-8")
extracted = text_path.read_text(encoding="utf-8")

required = (
    record["record_id"],
    record["final_observed_at_utc"],
    record["publication"]["commit"],
    str(record["live_remote_heads"]["head_count"]),
    *(str(item["run_id"]) for item in record["hosted_runs"]),
)
for token in required:
    if token not in source:
        raise SystemExit(f"Markdown/JSON parity failure: source lacks {token!r}")
    if token not in extracted:
        raise SystemExit(f"PDF/JSON parity failure: extracted PDF lacks {token!r}")
if "PPC-20260902-01" in source or "PPC-20260902-01" in extracted:
    raise SystemExit("stale PPC-20260902-01 identifier remains in source or PDF")
PY

# Reject text outside the A4 page or outside a conservative 58--538 point
# horizontal reading band. This catches clipped long object IDs and timestamps;
# the decorative registration marks are vector paths and are intentionally not
# part of the text check.
python3 -I -S -B - "$BUILD_ROOT/receipt-bbox.html" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET

namespace = "{http://www.w3.org/1999/xhtml}"
root = ET.parse(Path(sys.argv[1])).getroot()
pages = list(root.iter(namespace + "page"))
if not pages:
    raise SystemExit("PDF bounding-box extraction produced no pages")
for page_number, page in enumerate(pages, start=1):
    width = float(page.attrib["width"])
    height = float(page.attrib["height"])
    for word in page.iter(namespace + "word"):
        x_min = float(word.attrib["xMin"])
        x_max = float(word.attrib["xMax"])
        y_min = float(word.attrib["yMin"])
        y_max = float(word.attrib["yMax"])
        if x_min < 0 or x_max > width or y_min < 0 or y_max > height:
            raise SystemExit(
                f"page {page_number} has text outside its page box: {word.text!r}"
            )
        if x_min < 58 or x_max > 538:
            raise SystemExit(
                f"page {page_number} has text outside the reviewed reading band: "
                f"{word.text!r} at {x_min:.3f}..{x_max:.3f}"
            )
PY

# Audit every page link annotation structurally. Markdown keeps relative links,
# while the PDF filter must project them to this exact HTTPS set. Pinning pypdf
# makes this an explicit outer-tool boundary, not a standard-library claim.
python3 -I -B - "$BUILT" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys
import sysconfig

for location in dict.fromkeys(
    (sysconfig.get_path("purelib"), sysconfig.get_path("platlib"))
):
    if location:
        sys.path.insert(0, location)

import pypdf
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

if pypdf.__version__ != "6.15.0":
    raise SystemExit(
        f"post-publication PDF audit requires pypdf 6.15.0; observed {pypdf.__version__}"
    )

expected = {
    "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/post-publication-custody-2026-09-02.json",
    "https://github.com/sepahead/pid-rs/blob/main/output/pdf/post-publication-custody-2026-09-02.pdf",
    "https://github.com/sepahead/pid-rs/blob/main/audit/evidence/post-publication-remote-heads-2026-09-02.tsv",
    "https://github.com/sepahead/pid-rs/actions/runs/33547094635",
    "https://github.com/sepahead/pid-rs/actions/runs/33547094668",
    "https://github.com/sepahead/pid-rs/actions/runs/33547093983",
    "https://github.com/sepahead/pid-rs/actions/runs/33547094598",
    "https://github.com/sepahead/pid-rs/actions/runs/33547094741",
    "https://github.com/sepahead/pid-rs/actions/runs/33558833307",
}

def resolve(value):
    while isinstance(value, IndirectObject):
        value = value.get_object()
    return value

reader = PdfReader(str(Path(sys.argv[1])), strict=True)
observed: list[str] = []
for page_number, page in enumerate(reader.pages, start=1):
    page_dictionary = resolve(page)
    for forbidden in ("/AA",):
        if forbidden in page_dictionary:
            raise SystemExit(f"page {page_number} contains forbidden {forbidden}")
    annotations = resolve(page_dictionary.get("/Annots", ArrayObject()))
    if not isinstance(annotations, ArrayObject):
        raise SystemExit(f"page {page_number} annotations are not an array")
    for annotation_ref in annotations:
        annotation = resolve(annotation_ref)
        if not isinstance(annotation, DictionaryObject):
            raise SystemExit(f"page {page_number} annotation is not a dictionary")
        if str(annotation.get("/Subtype")) != "/Link":
            raise SystemExit(f"page {page_number} has non-link annotation")
        if any(key in annotation for key in ("/Dest", "/AA")):
            raise SystemExit(f"page {page_number} link has a forbidden destination form")
        action = resolve(annotation.get("/A"))
        if not isinstance(action, DictionaryObject) or str(action.get("/S")) != "/URI":
            raise SystemExit(f"page {page_number} link is not one explicit URI action")
        if any(key in action for key in ("/F", "/FS", "/D", "/NewWindow")):
            raise SystemExit(f"page {page_number} URI action carries a file or remote destination")
        uri = str(action.get("/URI", ""))
        if not uri.startswith("https://github.com/sepahead/pid-rs/"):
            raise SystemExit(f"page {page_number} has non-project or non-HTTPS URI: {uri!r}")
        observed.append(uri)

if len(observed) != len(expected) or set(observed) != expected:
    raise SystemExit(
        f"PDF URI inventory differs: observed={sorted(observed)!r}, expected={sorted(expected)!r}"
    )
root = resolve(reader.trailer["/Root"])
if any(key in root for key in ("/OpenAction", "/AA")):
    raise SystemExit("PDF catalog has an automatic or additional action")
PY

# Publish only after every content, identity, and action check has passed. The
# two final renames are individually atomic; any interruption between them is
# detected by the bound artifact hashes and cannot create a passing receipt.
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIR/.post-publication-custody.pdf.XXXXXX")"
cp "$BUILT" "$OUTPUT_TEMP"
chmod 0644 "$OUTPUT_TEMP"
if [[ "$OUTPUT" == "$DEFAULT_OUTPUT" ]]; then
  FIGURE_TEMP="$(mktemp "$FIGURE_DIR/.state.pdf.XXXXXX")"
  cp "$BUILT_FIGURE" "$FIGURE_TEMP"
  chmod 0644 "$FIGURE_TEMP"
  mv -f -- "$FIGURE_TEMP" "$FIGURE"
  FIGURE_TEMP=""
fi
mv -f -- "$OUTPUT_TEMP" "$OUTPUT"
OUTPUT_TEMP=""

echo "OK: $OUTPUT ($pages pages, PDF $version; bounded JSON/Markdown/PDF parity; 9 HTTPS link annotations)"
