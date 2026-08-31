#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/NUMERICAL_ASSURANCE.md"
LATEX_DIR="$ROOT/audit/formal/latex/numerical-assurance"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
FIGURE_DIR="$ROOT/audit/formal/latex/figures/numerical-assurance"
FIGURE_MANIFEST="$FIGURE_DIR/figure-assets.json"
DEFAULT_OUTPUT="$ROOT/output/pdf/numerical-assurance.pdf"
OUTPUT="$DEFAULT_OUTPUT"
JOB="numerical-assurance"
FIGURE_STEMS=(
  "quantizer-cardinality"
  "represented-sum-boundary"
)

# Freeze renderer timestamps and PDF identifiers for same-source reproducibility. The date is the
# publication date at 00:00 UTC; callers may override it only through SOURCE_DATE_EPOCH.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1788134400}"
export FORCE_SOURCE_DATE=1
export TZ=UTC
export LC_ALL=C

if [[ $# -eq 2 && "$1" == "--output" ]]; then
  OUTPUT="$2"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--output ABSOLUTE_PDF_PATH]" >&2
  exit 2
fi

[[ "$OUTPUT" == /* && "$OUTPUT" == *.pdf ]] || {
  echo "Numerical assurance PDF build failed: output must be an absolute .pdf path" >&2
  exit 1
}
OUTPUT_DIR="$(dirname "$OUTPUT")"
[[ -d "$OUTPUT_DIR" && ! -L "$OUTPUT_DIR" && "$OUTPUT_DIR" != "/" ]] || {
  echo "Numerical assurance PDF build failed: output directory is unsafe or absent" >&2
  exit 1
}
[[ ! -e "$OUTPUT" || ( -f "$OUTPUT" && ! -L "$OUTPUT" ) ]] || {
  echo "Numerical assurance PDF build failed: output is not a regular nonsymbolic file" >&2
  exit 1
}

for command_name in awk basename cp dirname mktemp mv pandoc pdfinfo pdffonts pdftotext \
    python3 rm shasum lualatex; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Numerical assurance PDF build failed: missing command: $command_name" >&2
    exit 1
  }
done

[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || {
  echo "Numerical assurance PDF build failed: canonical Markdown is absent or symbolic" >&2
  exit 1
}
[[ -f "$LATEX_DIR/header.tex" && -f "$LATEX_DIR/filter.lua" \
    && -f "$TAGPDF_OPENACTION_COMPAT" && ! -L "$TAGPDF_OPENACTION_COMPAT" ]] || {
  echo "Numerical assurance PDF build failed: projection source is incomplete" >&2
  exit 1
}
[[ -d "$FIGURE_DIR" && ! -L "$FIGURE_DIR" && -f "$FIGURE_MANIFEST" \
    && ! -L "$FIGURE_MANIFEST" ]] || {
  echo "Numerical assurance PDF build failed: figure directory or manifest is unsafe" >&2
  exit 1
}

validate_figure_assets() {
  local stem
  for stem in "${FIGURE_STEMS[@]}"; do
    [[ -f "$FIGURE_DIR/$stem.svg" && ! -L "$FIGURE_DIR/$stem.svg" \
        && -f "$FIGURE_DIR/$stem.pdf" && ! -L "$FIGURE_DIR/$stem.pdf" ]] || {
      echo "Numerical assurance PDF build failed: tracked figure pair is incomplete: $stem" >&2
      return 1
    }
  done
  python3 -I -B - "$FIGURE_MANIFEST" "$FIGURE_DIR" <<'PY'
import hashlib
import json
import math
import pathlib
import sys

from pypdf import PdfReader

manifest_path = pathlib.Path(sys.argv[1])
figure_dir = pathlib.Path(sys.argv[2])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
expected_stems = [
    "quantizer-cardinality",
    "represented-sum-boundary",
]
assets = manifest.get("assets")
if manifest.get("schema") != "pid-rs.numerical-assurance-figure-assets.v1":
    raise SystemExit("figure manifest schema changed")
if not isinstance(assets, list) or [entry.get("stem") for entry in assets] != expected_stems:
    raise SystemExit("figure manifest inventory or order changed")
for entry in assets:
    stem = entry["stem"]
    for suffix in ("svg", "pdf"):
        path = figure_dir / f"{stem}.{suffix}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != entry[f"{suffix}_sha256"]:
            raise SystemExit(f"figure digest changed: {path.name}")
    reader = PdfReader(figure_dir / f"{stem}.pdf", strict=True)
    if len(reader.pages) != entry["pdf_pages"] or len(reader.pages) != 1:
        raise SystemExit(f"figure page count changed: {stem}")
    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    expected_width, expected_height = entry["pdf_page_points"]
    if not math.isclose(width, expected_width, abs_tol=0.002) or not math.isclose(
        height, expected_height, abs_tol=0.002
    ):
        raise SystemExit(f"figure page geometry changed: {stem}")
    page.get_contents()
print("figure-assets=GO count=2")
PY
}

validate_figure_assets

work_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-numerical-assurance-pdf.XXXXXX")"
cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT

raw_tex="$work_root/raw.tex"
tagged_tex="$work_root/tagged.tex"
source_digest_record="$work_root/source-digests.txt"

# Bind the duplicated 16-byte trailer ID to the canonical Markdown, projection sources, and SVGs.
# LuaTeX otherwise generates a new ID for each build even when SOURCE_DATE_EPOCH is fixed.
(
  cd "$ROOT"
  shasum -a 256 \
    "NUMERICAL_ASSURANCE.md" \
    "audit/formal/latex/numerical-assurance/header.tex" \
    "audit/formal/latex/numerical-assurance/filter.lua" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "audit/formal/latex/figures/numerical-assurance/figure-assets.json"
  for stem in "${FIGURE_STEMS[@]}"; do
    shasum -a 256 \
      "audit/formal/latex/figures/numerical-assurance/$stem.svg" \
      "audit/formal/latex/figures/numerical-assurance/$stem.pdf"
  done
) >"$source_digest_record"
trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "Numerical assurance PDF build failed: source-derived trailer ID is malformed" >&2
  exit 1
}

(
  cd "$ROOT"
  PID_NUMERICAL_FIGURE_PDF_DIR="$FIGURE_DIR" \
  pandoc "$(basename "$SOURCE")" \
    --from=gfm+tex_math_dollars --to=latex --standalone --table-of-contents --toc-depth=2 \
    --lua-filter="$LATEX_DIR/filter.lua" \
    --include-in-header="$LATEX_DIR/header.tex" \
    --include-in-header="$TAGPDF_OPENACTION_COMPAT" \
    --metadata=title:'Represented-binary64 assurance for PID' \
    --metadata=author:'pid-rs project analysis' \
    --metadata=date:'31 August 2026' \
    --variable=colorlinks=true --variable=linkcolor:PidTeal --variable=toccolor:PidTeal \
    --variable=urlcolor:PidBronze --variable=citecolor:PidTeal \
    --variable=papersize:a4 --variable=fontsize:10pt --variable=geometry:margin=18mm \
    --variable=linestretch:1.035 --variable=mainfont:'Latin Modern Roman' \
    --variable=sansfont:'Source Sans Pro' --variable=monofont:'Latin Modern Mono Light' \
    --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
)

[[ -s "$raw_tex" && ! -L "$raw_tex" ]] || {
  echo "Numerical assurance PDF build failed: Pandoc did not produce TeX" >&2
  exit 1
}

awk -v trailer_id="$trailer_id" 'BEGIN {
  print "\\DocumentMetadata{testphase=phase-II,lang=en-US}"
}
{
  print
  if ($0 == "\\begin{document}") {
    print "\\pdfvariable trailerid {[ <" trailer_id "> <" trailer_id "> ]}"
    inserted += 1
  }
}
END {
  if (inserted != 1) exit 42
}' \
  "$raw_tex" >"$tagged_tex"

for pass in 1 2 3; do
  if ! lualatex --interaction=nonstopmode --halt-on-error --file-line-error \
      --jobname="$JOB" --output-directory="$work_root" "$tagged_tex" \
      >"$work_root/pass-$pass.log" 2>&1; then
    cat "$work_root/pass-$pass.log" >&2
    echo "Numerical assurance PDF build failed: LuaLaTeX pass $pass failed" >&2
    exit 1
  fi
done

validate_figure_assets

built="$work_root/$JOB.pdf"
log="$work_root/$JOB.log"
[[ -s "$built" && -s "$log" ]] || {
  echo "Numerical assurance PDF build failed: compiled PDF or log is absent" >&2
  exit 1
}

if grep -En 'Overfull \\[hv]box|Undefined control sequence|Missing character:' "$log" >&2; then
  echo "Numerical assurance PDF build failed: layout or glyph error" >&2
  exit 1
fi

python3 -I -B - "$built" <<'PY'
import pathlib
import sys
from pypdf import PdfReader

path = pathlib.Path(sys.argv[1])
reader = PdfReader(path, strict=True)
if not reader.pages:
    raise SystemExit("compiled PDF has no pages")
for page in reader.pages:
    page.get_contents()
PY
page_count="$(pdfinfo "$built" | awk '/^Pages:/ {print $2}')"
[[ "$page_count" =~ ^[1-9][0-9]*$ ]] || {
  echo "Numerical assurance PDF build failed: invalid page count" >&2
  exit 1
}
pdftotext "$built" "$work_root/extracted.txt"
for sentinel in \
    'Exact reduction of already represented binary64 operands is not exact estimation.' \
    'Exact reduction of represented operands' \
    'The highest set bit of' \
    'There is no test-only switch' \
    'Twelve materially distinct routes considered' \
    'Fifty-lens hostile review' \
    'References and exact repository routes'; do
  grep -Fq "$sentinel" "$work_root/extracted.txt" || {
    echo "Numerical assurance PDF build failed: missing text sentinel: $sentinel" >&2
    exit 1
  }
done

font_rows="$(pdffonts "$built" | awk 'NR > 2 {count += 1} END {print count + 0}')"
[[ "$font_rows" -gt 0 ]] || {
  echo "Numerical assurance PDF build failed: no embedded font rows" >&2
  exit 1
}
if pdffonts "$built" | awk 'NR > 2 && $(NF-4) != "yes" {exit 1}'; then
  :
else
  pdffonts "$built" >&2
  echo "Numerical assurance PDF build failed: a font is not embedded" >&2
  exit 1
fi

candidate="$(mktemp "$OUTPUT_DIR/.numerical-assurance.XXXXXX.pdf")"
trap 'rm -f -- "$candidate"; cleanup' EXIT
cp "$built" "$candidate"
mv "$candidate" "$OUTPUT"
trap cleanup EXIT
printf 'OK: built %s pages=%s sha256=%s\n' \
  "$OUTPUT" "$page_count" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
