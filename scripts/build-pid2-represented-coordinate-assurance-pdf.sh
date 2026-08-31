#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/PID2_REPRESENTED_COORDINATE_ASSURANCE.md"
LATEX_DIR="$ROOT/audit/formal/latex/pid2-represented-coordinate-assurance"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
DEFAULT_OUTPUT="$ROOT/output/pdf/pid2-represented-coordinate-assurance.pdf"
OUTPUT="$DEFAULT_OUTPUT"
JOB="pid2-represented-coordinate-assurance"
CHECK_NAME="PID2 represented-coordinate assurance PDF build"

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
  echo "$CHECK_NAME failed: output must be an absolute .pdf path" >&2
  exit 1
}
output_dir="$(dirname "$OUTPUT")"
[[ -d "$output_dir" && ! -L "$output_dir" && "$output_dir" != "/" ]] || {
  echo "$CHECK_NAME failed: output directory is unsafe or absent" >&2
  exit 1
}
[[ ! -e "$OUTPUT" || ( -f "$OUTPUT" && ! -L "$OUTPUT" ) ]] || {
  echo "$CHECK_NAME failed: output is not a regular nonsymbolic file" >&2
  exit 1
}

for command_name in awk basename cp dirname grep lualatex mktemp mv pandoc pdffonts pdfinfo \
    pdftotext python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME failed: missing command: $command_name" >&2
    exit 1
  }
done

for required in "$SOURCE" "$LATEX_DIR/header.tex" "$LATEX_DIR/filter.lua" \
    "$TAGPDF_OPENACTION_COMPAT"; do
  [[ -f "$required" && ! -L "$required" ]] || {
    echo "$CHECK_NAME failed: required input is absent, nonregular, or symbolic: $required" >&2
    exit 1
  }
done

python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"

tmp_base="${TMPDIR:-/tmp}"
while [[ "$tmp_base" != "/" && "$tmp_base" == */ ]]; do tmp_base="${tmp_base%/}"; done
work_root="$(mktemp -d "$tmp_base/pid-rs-pid2-assurance-pdf.XXXXXX")"
cleanup() { rm -rf -- "$work_root"; }
trap cleanup EXIT

raw_tex="$work_root/raw.tex"
tagged_tex="$work_root/tagged.tex"
source_digest_record="$work_root/source-digests.txt"
(
  cd "$ROOT"
  shasum -a 256 \
    "PID2_REPRESENTED_COORDINATE_ASSURANCE.md" \
    "audit/formal/latex/pid2-represented-coordinate-assurance/header.tex" \
    "audit/formal/latex/pid2-represented-coordinate-assurance/filter.lua" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
) >"$source_digest_record"
trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "$CHECK_NAME failed: source-derived trailer ID is malformed" >&2
  exit 1
}

(
  cd "$ROOT"
  pandoc "$(basename "$SOURCE")" \
    --from=gfm+tex_math_dollars --to=latex --standalone --table-of-contents --toc-depth=2 \
    --lua-filter="$LATEX_DIR/filter.lua" \
    --include-in-header="$LATEX_DIR/header.tex" \
    --include-in-header="$TAGPDF_OPENACTION_COMPAT" \
    --metadata=title:'PID2 represented-coordinate assurance' \
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
  echo "$CHECK_NAME failed: Pandoc did not produce TeX" >&2
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
END { if (inserted != 1) exit 42 }' "$raw_tex" >"$tagged_tex"

for pass in 1 2 3; do
  if ! lualatex --interaction=nonstopmode --halt-on-error --file-line-error \
      --jobname="$JOB" --output-directory="$work_root" "$tagged_tex" \
      >"$work_root/pass-$pass.log" 2>&1; then
    cat "$work_root/pass-$pass.log" >&2
    echo "$CHECK_NAME failed: LuaLaTeX pass $pass failed" >&2
    exit 1
  fi
done

built="$work_root/$JOB.pdf"
log="$work_root/$JOB.log"
[[ -s "$built" && -s "$log" ]] || {
  echo "$CHECK_NAME failed: compiled PDF or log is absent" >&2
  exit 1
}
if grep -En 'Overfull \\[hv]box|Undefined control sequence|Missing character:' "$log" >&2; then
  echo "$CHECK_NAME failed: layout or glyph error" >&2
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
  echo "$CHECK_NAME failed: invalid page count" >&2
  exit 1
}
pdftotext -layout "$built" "$work_root/extracted.txt"
for sentinel in \
    'The evidence supports a represented-coordinate engineering claim.' \
    'Exact binary64 decoding' \
    'The 15/49 contract discriminator' \
    'Complete k=1..1023 acceptance-to-rejection family' \
    'Checker architecture and anti-cheating controls' \
    'not independent estimation, external replication, or independent review' \
    'Thirty-four-lens adversarial review' \
    'Neither profile enlarges the mathematical' \
    'Rundungsfehleranalyse'; do
  grep -Fq "$sentinel" "$work_root/extracted.txt" || {
    echo "$CHECK_NAME failed: missing text sentinel: $sentinel" >&2
    exit 1
  }
done

font_rows="$(pdffonts "$built" | awk 'NR > 2 {count += 1} END {print count + 0}')"
[[ "$font_rows" -gt 0 ]] || {
  echo "$CHECK_NAME failed: no embedded font rows" >&2
  exit 1
}
pdffonts "$built" | awk 'NR > 2 && $(NF-4) != "yes" {exit 1}' || {
  pdffonts "$built" >&2
  echo "$CHECK_NAME failed: a font is not embedded" >&2
  exit 1
}

candidate="$(mktemp "$output_dir/.pid2-represented-coordinate-assurance.XXXXXX.pdf")"
trap 'rm -f -- "$candidate"; cleanup' EXIT
cp "$built" "$candidate"
mv "$candidate" "$OUTPUT"
trap cleanup EXIT
printf 'OK: built %s pages=%s sha256=%s\n' \
  "$OUTPUT" "$page_count" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
