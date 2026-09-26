#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE_RELATIVE="audit/research/fault-tolerant-shared-exclusions/EXPOSITION.md"
SOURCE="$ROOT/$SOURCE_RELATIVE"
LATEX_DIR="$ROOT/audit/formal/latex/fault-tolerant-shared-exclusions"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
STYLE_DIR="$ROOT/audit/formal/latex"
DEFAULT_OUTPUT="$ROOT/output/pdf/fault-tolerant-shared-exclusions.pdf"
OUTPUT="$DEFAULT_OUTPUT"
JOB="fault-tolerant-shared-exclusions"

# Freeze renderer timestamps and PDF identifiers for same-source reproducibility. The date is the
# publication date at 00:00 UTC; callers may override it only through SOURCE_DATE_EPOCH.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1790380800}"
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
  echo "Fault-tolerance research note PDF build failed: output must be an absolute .pdf path" >&2
  exit 1
}
OUTPUT_DIR="$(dirname "$OUTPUT")"
[[ -d "$OUTPUT_DIR" && ! -L "$OUTPUT_DIR" && "$OUTPUT_DIR" != "/" ]] || {
  echo "Fault-tolerance research note PDF build failed: output directory is unsafe or absent" >&2
  exit 1
}
[[ ! -e "$OUTPUT" || ( -f "$OUTPUT" && ! -L "$OUTPUT" ) ]] || {
  echo "Fault-tolerance research note PDF build failed: output is not a regular nonsymbolic file" >&2
  exit 1
}

for command_name in awk basename cp dirname mktemp mv pandoc pdfinfo pdffonts pdftotext \
    python3 rm shasum lualatex; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Fault-tolerance research note PDF build failed: missing command: $command_name" >&2
    exit 1
  }
done

[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || {
  echo "Fault-tolerance research note PDF build failed: canonical Markdown is absent or symbolic" >&2
  exit 1
}
[[ -f "$LATEX_DIR/publication.tex" && ! -L "$LATEX_DIR/publication.tex" \
    && -f "$LATEX_DIR/filter.lua" && ! -L "$LATEX_DIR/filter.lua" \
    && -f "$STYLE_DIR/pid-rs-report-tables.sty" && ! -L "$STYLE_DIR/pid-rs-report-tables.sty" \
    && -f "$STYLE_DIR/pid-rs-workflow-publication.sty" \
    && ! -L "$STYLE_DIR/pid-rs-workflow-publication.sty" \
    && -f "$TAGPDF_OPENACTION_COMPAT" && ! -L "$TAGPDF_OPENACTION_COMPAT" ]] || {
  echo "Fault-tolerance research note PDF build failed: projection source is incomplete" >&2
  exit 1
}

work_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-fault-tolerant-shared-exclusions-pdf.XXXXXX")"
cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT

raw_tex="$work_root/raw.tex"
tagged_tex="$work_root/tagged.tex"
source_digest_record="$work_root/source-digests.txt"

# Bind the duplicated 16-byte trailer ID to the canonical Markdown and projection sources.
# LuaTeX otherwise generates a new ID for each build even when SOURCE_DATE_EPOCH is fixed.
(
  cd "$ROOT"
  shasum -a 256 \
    "$SOURCE_RELATIVE" \
    "audit/formal/latex/fault-tolerant-shared-exclusions/publication.tex" \
    "audit/formal/latex/fault-tolerant-shared-exclusions/filter.lua" \
    "audit/formal/latex/pid-rs-report-tables.sty" \
    "audit/formal/latex/pid-rs-workflow-publication.sty" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
) >"$source_digest_record"
trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "Fault-tolerance research note PDF build failed: source-derived trailer ID is malformed" >&2
  exit 1
}

(
  cd "$ROOT/audit/research/fault-tolerant-shared-exclusions"
  pandoc "$(basename "$SOURCE")" \
    --from=gfm+tex_math_dollars --to=latex --wrap=none --syntax-highlighting=none \
    --lua-filter="$LATEX_DIR/filter.lua" --output="$work_root/body.tex"
)
[[ -s "$work_root/body.tex" && ! -L "$work_root/body.tex" ]] || {
  echo "PDF build failed: Pandoc did not produce the body" >&2
  exit 1
}
cp "$LATEX_DIR/publication.tex" "$raw_tex"
cp "$TAGPDF_OPENACTION_COMPAT" "$work_root/tagpdf-openaction-compat.tex"

[[ -s "$raw_tex" && ! -L "$raw_tex" ]] || {
  echo "Fault-tolerance research note PDF build failed: Pandoc did not produce TeX" >&2
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
  if ! (cd "$work_root" && TEXINPUTS="$STYLE_DIR:" lualatex --interaction=nonstopmode \
      --halt-on-error --file-line-error --jobname="$JOB" --output-directory="$work_root" \
      "$tagged_tex" >"$work_root/pass-$pass.log" 2>&1); then
    cat "$work_root/pass-$pass.log" >&2
    echo "Fault-tolerance research note PDF build failed: LuaLaTeX pass $pass failed" >&2
    exit 1
  fi
done

built="$work_root/$JOB.pdf"
log="$work_root/$JOB.log"
[[ -s "$built" && -s "$log" ]] || {
  echo "Fault-tolerance research note PDF build failed: compiled PDF or log is absent" >&2
  exit 1
}

if grep -En 'Overfull \\[hv]box|Undefined control sequence|Missing character:' "$log" >&2; then
  echo "Fault-tolerance research note PDF build failed: layout or glyph error" >&2
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
  echo "Fault-tolerance research note PDF build failed: invalid page count" >&2
  exit 1
}
pdftotext "$built" "$work_root/extracted.txt"
LC_ALL=C tr '\f\n\r\t' '    ' <"$work_root/extracted.txt" | LC_ALL=C tr -s ' ' \
  >"$work_root/normalized.txt"
for sentinel in \
    'PID-RS TECHNICAL REPORT SERIES' \
    'The MGW event is a fault-consistency set' \
    'Validity under tolerated faults' \
    'Negative results and their reasons' \
    'Rust implementation and computational cost' \
    'Routes considered'; do
  grep -Fq "$sentinel" "$work_root/normalized.txt" || {
    echo "Fault-tolerance research note PDF build failed: missing text sentinel: $sentinel" >&2
    exit 1
  }
done

font_rows="$(pdffonts "$built" | awk 'NR > 2 {count += 1} END {print count + 0}')"
[[ "$font_rows" -gt 0 ]] || {
  echo "Fault-tolerance research note PDF build failed: no embedded font rows" >&2
  exit 1
}
if pdffonts "$built" | awk 'NR > 2 && $(NF-4) != "yes" {exit 1}'; then
  :
else
  pdffonts "$built" >&2
  echo "Fault-tolerance research note PDF build failed: a font is not embedded" >&2
  exit 1
fi

candidate="$(mktemp "$OUTPUT_DIR/.fault-tolerant-shared-exclusions.XXXXXX.pdf")"
trap 'rm -f -- "$candidate"; cleanup' EXIT
cp "$built" "$candidate"
mv "$candidate" "$OUTPUT"
trap cleanup EXIT
printf 'OK: built %s pages=%s sha256=%s\n' \
  "$OUTPUT" "$page_count" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
