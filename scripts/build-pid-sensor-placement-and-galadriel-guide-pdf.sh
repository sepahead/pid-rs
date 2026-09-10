#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md"
LATEX_DIR="$ROOT/audit/formal/latex/pid-sensor-placement-and-galadriel-guide"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
FIGURE_DIR="$ROOT/audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide"
FIGURE_MANIFEST="$FIGURE_DIR/figure-assets.json"
REUSED_CANCELLATION_PDF="$ROOT/audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation.pdf"
BUILD_EVIDENCE_DIR="${PID_GUIDE_BUILD_EVIDENCE_DIR:-}"
DEFAULT_OUTPUT="$ROOT/output/pdf/pid-sensor-placement-and-galadriel-guide.pdf"
OUTPUT="$DEFAULT_OUTPUT"
JOB="pid-sensor-placement-and-galadriel-guide"
FIGURE_STEMS=(
  "current-versus-proposed"
  "measurement-to-estimand"
  "placement-evidence-funnel"
)

# Freeze renderer timestamps and PDF identifiers for same-source reproducibility. The date is the
# publication date at 00:00 UTC; callers may override it only through SOURCE_DATE_EPOCH.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1788998400}"
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
  echo "PID sensor-placement guide PDF build failed: output must be an absolute .pdf path" >&2
  exit 1
}
OUTPUT_DIR="$(dirname "$OUTPUT")"
[[ -d "$OUTPUT_DIR" && ! -L "$OUTPUT_DIR" && "$OUTPUT_DIR" != "/" ]] || {
  echo "PID sensor-placement guide PDF build failed: output directory is unsafe or absent" >&2
  exit 1
}
[[ ! -e "$OUTPUT" || ( -f "$OUTPUT" && ! -L "$OUTPUT" ) ]] || {
  echo "PID sensor-placement guide PDF build failed: output is not a regular nonsymbolic file" >&2
  exit 1
}

if [[ -n "$BUILD_EVIDENCE_DIR" ]]; then
  [[ "$BUILD_EVIDENCE_DIR" == /* && "$BUILD_EVIDENCE_DIR" != */ \
      && ! -e "$BUILD_EVIDENCE_DIR" && ! -L "$BUILD_EVIDENCE_DIR" ]] || {
    echo "PID sensor-placement guide PDF build failed: evidence directory must be an absent absolute path" >&2
    exit 1
  }
  evidence_parent="$(dirname "$BUILD_EVIDENCE_DIR")"
  [[ -d "$evidence_parent" && ! -L "$evidence_parent" \
      && "$evidence_parent" == "$(cd "$evidence_parent" && pwd -P)" ]] || {
    echo "PID sensor-placement guide PDF build failed: evidence parent must be existing and canonical" >&2
    exit 1
  }
  canonical_output="$(cd "$OUTPUT_DIR" && pwd -P)/$(basename "$OUTPUT")"
  [[ "$BUILD_EVIDENCE_DIR" != "$canonical_output" ]] || {
    echo "PID sensor-placement guide PDF build failed: evidence directory aliases PDF output" >&2
    exit 1
  }
  command -v mkdir >/dev/null 2>&1 || {
    echo "PID sensor-placement guide PDF build failed: missing command for evidence retention: mkdir" >&2
    exit 1
  }
fi

for command_name in awk basename cp dirname mktemp mv pandoc pdfinfo pdffonts pdftotext \
    python3 rm shasum lualatex; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "PID sensor-placement guide PDF build failed: missing command: $command_name" >&2
    exit 1
  }
done

[[ -f "$SOURCE" && ! -L "$SOURCE" ]] || {
  echo "PID sensor-placement guide PDF build failed: canonical Markdown is absent or symbolic" >&2
  exit 1
}
[[ -f "$LATEX_DIR/header.tex" && -f "$LATEX_DIR/filter.lua" \
    && -f "$TAGPDF_OPENACTION_COMPAT" && ! -L "$TAGPDF_OPENACTION_COMPAT" ]] || {
  echo "PID sensor-placement guide PDF build failed: projection source is incomplete" >&2
  exit 1
}
[[ -d "$FIGURE_DIR" && ! -L "$FIGURE_DIR" && -f "$FIGURE_MANIFEST" \
    && ! -L "$FIGURE_MANIFEST" ]] || {
  echo "PID sensor-placement guide PDF build failed: figure directory or manifest is unsafe" >&2
  exit 1
}

validate_figure_assets() {
  local stem
  for stem in "${FIGURE_STEMS[@]}"; do
    [[ -f "$FIGURE_DIR/$stem.svg" && ! -L "$FIGURE_DIR/$stem.svg" \
        && -f "$FIGURE_DIR/$stem.pdf" && ! -L "$FIGURE_DIR/$stem.pdf" ]] || {
      echo "PID sensor-placement guide PDF build failed: tracked figure pair is incomplete: $stem" >&2
      return 1
    }
  done
  python3 -I -B - "$FIGURE_MANIFEST" "$FIGURE_DIR" "$ROOT" <<'PY'
import hashlib
import json
import math
import pathlib
import stat
import sys

from pypdf import PdfReader

manifest_path = pathlib.Path(sys.argv[1])
figure_dir = pathlib.Path(sys.argv[2])
repository_root = pathlib.Path(sys.argv[3])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
expected_stems = [
    "current-versus-proposed",
    "measurement-to-estimand",
    "placement-evidence-funnel",
]
assets = manifest.get("assets")
if manifest.get("schema") != "pid-rs.pid-sensor-placement-guide-figure-assets.v2":
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

# This is an exact import of existing repository assets, not a new renderer observation.
expected_reused = {
    "stem": "signed-cancellation",
    "svg_repository_path": "audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation.svg",
    "svg_bytes": 2650,
    "svg_mode": "0o644",
    "svg_sha256": "15d07f2c94cb7f82787ee6e78301f896b3a06a023fa8db4906d52b9ecdb8f620",
    "pdf_repository_path": "audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation.pdf",
    "pdf_bytes": 42100,
    "pdf_mode": "0o644",
    "pdf_sha256": "5ae5a52dedf8fa43f53b74ffdcdcca2d65f4708dc6ff7281db75618711a7f6df"
}
reused = manifest.get("reused_assets")
if type(reused) is not list or len(reused) != 1 or type(reused[0]) is not dict:
    raise SystemExit("reused figure inventory changed")
entry = reused[0]
if set(entry) != set(expected_reused):
    raise SystemExit("reused figure fields changed")
for key, expected in expected_reused.items():
    if type(entry[key]) is not type(expected) or entry[key] != expected:
        raise SystemExit(f"reused figure identity changed: {key}")
for suffix in ("svg", "pdf"):
    path = repository_root / entry[f"{suffix}_repository_path"]
    if path.is_symlink() or not path.is_file() or path.resolve(strict=True) != path:
        raise SystemExit(f"reused figure path is not canonical direct-regular: {path}")
    if oct(stat.S_IMODE(path.stat().st_mode)) != entry[f"{suffix}_mode"]:
        raise SystemExit(f"reused figure mode changed: {path.name}")
    raw = path.read_bytes()
    if len(raw) != entry[f"{suffix}_bytes"] or hashlib.sha256(raw).hexdigest() != entry[f"{suffix}_sha256"]:
        raise SystemExit(f"reused figure bytes changed: {path.name}")
# Exact bytes bind this derivative. No new paper page/font/shim profile is inferred.
reader = PdfReader(repository_root / entry["pdf_repository_path"], strict=True)
for page in reader.pages:
    page.get_contents()
print("figure-assets=GO count=3 reused=1")
PY
}

validate_figure_assets

if [[ -n "$BUILD_EVIDENCE_DIR" ]]; then
  mkdir -m 700 "$BUILD_EVIDENCE_DIR"
  work_root="$BUILD_EVIDENCE_DIR"
else
  work_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-sensor-placement-pdf.XXXXXX")"
fi
cleanup() {
  if [[ -z "$BUILD_EVIDENCE_DIR" ]]; then
    rm -rf -- "$work_root"
  fi
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
    "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md" \
    "audit/formal/latex/pid-sensor-placement-and-galadriel-guide/header.tex" \
    "audit/formal/latex/pid-sensor-placement-and-galadriel-guide/filter.lua" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/figure-assets.json"
  for stem in "${FIGURE_STEMS[@]}"; do
    shasum -a 256 \
      "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/$stem.svg" \
      "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/$stem.pdf"
  done
  shasum -a 256 \
    "audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation.svg" \
    "audit/formal/latex/figures/real-occupancy-sensors/signed-cancellation.pdf"
) >"$source_digest_record"
trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "PID sensor-placement guide PDF build failed: source-derived trailer ID is malformed" >&2
  exit 1
}

(
  cd "$ROOT"
  PID_GUIDE_FIGURE_PDF_DIR="$FIGURE_DIR" \
  PID_GUIDE_REUSED_CANCELLATION_PDF="$REUSED_CANCELLATION_PDF" \
  pandoc "$(basename "$SOURCE")" \
    --from=gfm+tex_math_dollars --to=latex --standalone --table-of-contents --toc-depth=2 \
    --lua-filter="$LATEX_DIR/filter.lua" \
    --include-in-header="$LATEX_DIR/header.tex" \
    --include-in-header="$TAGPDF_OPENACTION_COMPAT" \
    --metadata=title:'PID in Galadriel and sensor placement' \
    --metadata=author:'pid-rs project analysis' \
    --metadata=date:'10 September 2026' \
    --variable=colorlinks=true --variable=linkcolor:PidTeal --variable=toccolor:PidTeal \
    --variable=urlcolor:PidBronze --variable=citecolor:PidTeal \
    --variable=papersize:a4 --variable=fontsize:10pt --variable=geometry:margin=18mm \
    --variable=linestretch:1.035 --variable=mainfont:'Latin Modern Roman' \
    --variable=sansfont:'Source Sans Pro' --variable=monofont:'Latin Modern Mono Light' \
    --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
)

[[ -s "$raw_tex" && ! -L "$raw_tex" ]] || {
  echo "PID sensor-placement guide PDF build failed: Pandoc did not produce TeX" >&2
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
    echo "PID sensor-placement guide PDF build failed: LuaLaTeX pass $pass failed" >&2
    exit 1
  fi
done

validate_figure_assets

built="$work_root/$JOB.pdf"
log="$work_root/$JOB.log"
[[ -s "$built" && -s "$log" ]] || {
  echo "PID sensor-placement guide PDF build failed: compiled PDF or log is absent" >&2
  exit 1
}

if grep -En 'Overfull \\[hv]box|Undefined control sequence|Missing character:' "$log" >&2; then
  echo "PID sensor-placement guide PDF build failed: layout or glyph error" >&2
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
  echo "PID sensor-placement guide PDF build failed: invalid page count" >&2
  exit 1
}
pdftotext "$built" "$work_root/extracted.txt"
for sentinel in \
    'PID in Galadriel and sensor placement' \
    'The actual no-thermal fixture' \
    'A proposed map-placement problem' \
    'Oracle non-cheating contract' \
    'One-hundred-forty-lens council review' \
    'Exact finite-categorical shared-exclusions PID' \
    'Current Galadriel does not use PID for placement'; do
  grep -Fq "$sentinel" "$work_root/extracted.txt" || {
    echo "PID sensor-placement guide PDF build failed: missing text sentinel: $sentinel" >&2
    exit 1
  }
done

font_rows="$(pdffonts "$built" | awk 'NR > 2 {count += 1} END {print count + 0}')"
[[ "$font_rows" -gt 0 ]] || {
  echo "PID sensor-placement guide PDF build failed: no embedded font rows" >&2
  exit 1
}
if pdffonts "$built" | awk 'NR > 2 && $(NF-4) != "yes" {exit 1}'; then
  :
else
  pdffonts "$built" >&2
  echo "PID sensor-placement guide PDF build failed: a font is not embedded" >&2
  exit 1
fi

candidate="$(mktemp "$OUTPUT_DIR/.pid-sensor-placement-guide.XXXXXX.pdf")"
trap 'rm -f -- "$candidate"; cleanup' EXIT
cp "$built" "$candidate"
mv "$candidate" "$OUTPUT"
trap cleanup EXIT
printf 'OK: built %s pages=%s sha256=%s\n' \
  "$OUTPUT" "$page_count" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
