#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
HEADER="$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/header.tex"
FILTER="$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/filter.lua"
FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
DEFAULT_OUTPUT="$ROOT/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
OUTPUT="${1:-$DEFAULT_OUTPUT}"
SOURCE_DATE_EPOCH_VALUE=1787788800
JOB_NAME="sxpid3-source-marginal-and-bounded-audit"

if [[ "$#" -gt 1 || -z "$OUTPUT" ]]; then
  echo "usage: $0 [output.pdf]" >&2
  exit 2
fi

for command_name in awk cmp cp dirname fc-cache grep kpsewhich lualatex mkdir mktemp mv \
    pandoc pdffonts pdfinfo pdftotext rsvg-convert rm sed shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "SxPID3 audit PDF build failed: missing command: $command_name" >&2
    exit 1
  fi
done

required_sources=(
  "$SOURCE"
  "$HEADER"
  "$FILTER"
  "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.svg"
  "$FIGURE_DIRECTORY/source-cylinder-factorization.svg"
)
for required_source in "${required_sources[@]}"; do
  if [[ ! -f "$required_source" || -L "$required_source" ]]; then
    echo "SxPID3 audit PDF build failed: missing or symbolic source: $required_source" >&2
    exit 1
  fi
done

TMP_BASE="${PID_RS_PDF_TMPDIR:-${TMPDIR:-/tmp}}"
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-sxpid3-audit-pdf.XXXXXX")"
OUTPUT_TEMP=""
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-sxpid3-audit-pdf.*) rm -rf -- "$BUILD_ROOT" ;;
    *) echo "SxPID3 audit PDF build cleanup refused unexpected path: $BUILD_ROOT" >&2 ;;
  esac
  if [[ -n "$OUTPUT_TEMP" && -f "$OUTPUT_TEMP" && ! -L "$OUTPUT_TEMP" ]]; then
    rm -f -- "$OUTPUT_TEMP"
  fi
}
trap cleanup EXIT INT TERM

LM_ROMAN="$(kpsewhich lmroman10-regular.otf)"
LM_SANS="$(kpsewhich lmsans10-regular.otf)"
LM_MONO="$(kpsewhich lmmonolt10-regular.otf)"
LM_MATH="$(kpsewhich latinmodern-math.otf)"
for font_path in "$LM_ROMAN" "$LM_SANS" "$LM_MONO" "$LM_MATH"; do
  if [[ ! -f "$font_path" || -L "$font_path" ]]; then
    echo "SxPID3 audit PDF build failed: Latin Modern font missing or symbolic" >&2
    exit 1
  fi
done
LM_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$LM_ROMAN")" && pwd -P)"
LM_MATH_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$LM_MATH")" && pwd -P)"

build_once() {
  local label="$1"
  local run_root="$BUILD_ROOT/$label"
  local staged_root="$run_root/repository"
  local staged_figures="$staged_root/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
  local build_directory="$run_root/build"
  local home_directory="$run_root/home"
  local cache_directory="$run_root/cache"
  local texmfvar_directory="$run_root/texmf-var"
  local texmfconfig_directory="$run_root/texmf-config"
  local fontconfig_file="$run_root/fontconfig.xml"
  local raw_tex="$staged_root/$JOB_NAME.raw.tex"
  local normalized_tex="$staged_root/$JOB_NAME.tex"

  mkdir -p "$staged_figures" "$build_directory" "$home_directory" \
    "$cache_directory/fontconfig" "$texmfvar_directory" "$texmfconfig_directory"
  cp "$SOURCE" "$staged_root/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
  cp "$HEADER" "$staged_root/sxpid3-source-marginal-and-bounded-audit-header.tex"
  cp "$FILTER" "$staged_root/sxpid3-source-marginal-and-bounded-audit-filter.lua"
  cp "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.svg" "$staged_figures/audit-coordinate-crosswalk.svg"
  cp "$FIGURE_DIRECTORY/source-cylinder-factorization.svg" "$staged_figures/source-cylinder-factorization.svg"

  printf '%s\n' \
    '<?xml version="1.0"?>' '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">' '<fontconfig>' \
    "  <dir>$LM_DIRECTORY</dir>" "  <dir>$LM_MATH_DIRECTORY</dir>" \
    "  <cachedir>$cache_directory/fontconfig</cachedir>" '<config></config>' '</fontconfig>' \
    >"$fontconfig_file"

  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    fc-cache -f >/dev/null

  local figure
  for figure in audit-coordinate-crosswalk source-cylinder-factorization; do
    env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
      XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
      LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
      rsvg-convert --format=pdf --keep-aspect-ratio \
        --output="$staged_figures/$figure.pdf" "$staged_figures/$figure.svg"
  done

  (
    cd "$staged_root"
    env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
      XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
      OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY" TEXMFVAR="$texmfvar_directory" \
      TEXMFCONFIG="$texmfconfig_directory" LC_ALL=C LANG=C TZ=UTC \
      SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" FORCE_SOURCE_DATE=1 \
      pandoc SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md \
        --from=gfm+tex_math_dollars --to=latex --standalone --table-of-contents \
        --toc-depth=3 \
        --lua-filter=sxpid3-source-marginal-and-bounded-audit-filter.lua \
        --include-in-header=sxpid3-source-marginal-and-bounded-audit-header.tex \
        --metadata=title:'Source-marginal factorization and a bounded exact audit of a declared categorical SxPID3 transcription' \
        --metadata=author:'pid-rs project analysis' \
        --metadata=date:'27 August 2026' \
        --variable=papersize:a4 --variable=fontsize:11pt --variable=geometry:margin=20mm \
        --variable=linestretch:1.06 --variable=mainfont:'Latin Modern Roman' \
        --variable=sansfont:'Latin Modern Sans' --variable=monofont:'Latin Modern Mono Light' \
        --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
  )

  sed 's/^\\captionsetup\[table\]{skip=6pt}$/\\captionsetup*[table]{skip=6pt}/' \
    "$raw_tex" >"$normalized_tex"

  local pass
  for pass in 1 2 3; do
    (
      cd "$staged_root"
      env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
        XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
        OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY" TEXMFVAR="$texmfvar_directory" \
        TEXMFCONFIG="$texmfconfig_directory" LC_ALL=C LANG=C TZ=UTC \
        SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" FORCE_SOURCE_DATE=1 \
        lualatex --interaction=nonstopmode --halt-on-error --file-line-error \
          --jobname="$JOB_NAME" --output-directory="$build_directory" \
          "$normalized_tex" >"$build_directory/pass-$pass.stdout" 2>&1
    )
  done

  local built_pdf="$build_directory/$JOB_NAME.pdf"
  local final_log="$build_directory/$JOB_NAME.log"
  if [[ ! -s "$built_pdf" || ! -s "$final_log" ]]; then
    echo "SxPID3 audit PDF build failed: expected PDF/log absent" >&2
    exit 1
  fi
  if grep -En '(^| )(LaTeX|Package|Font) Warning:|Overfull \\[hv]box|Undefined control sequence|Missing character:' "$final_log" >&2; then
    echo "SxPID3 audit PDF build failed: final pass contains warning or layout error" >&2
    exit 1
  fi
  printf '%s\n' "$built_pdf"
}

FIRST="$(build_once first)"
SECOND="$(build_once second)"
if ! cmp -s "$FIRST" "$SECOND"; then
  echo "SxPID3 audit PDF build failed: repeated builds differ" >&2
  exit 1
fi

INFO="$BUILD_ROOT/final.info"
FONTS="$BUILD_ROOT/final.fonts"
TEXT="$BUILD_ROOT/final.txt"
LC_ALL=C pdfinfo "$FIRST" >"$INFO"
LC_ALL=C pdffonts "$FIRST" >"$FONTS"
LC_ALL=C pdftotext -layout "$FIRST" "$TEXT"
PAGES="$(awk '/^Pages:/ {print $2}' "$INFO")"
if [[ ! "$PAGES" =~ ^[0-9]+$ || "$PAGES" -lt 15 || "$PAGES" -gt 60 ]]; then
  echo "SxPID3 audit PDF build failed: implausible page count: ${PAGES:-missing}" >&2
  exit 1
fi
if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$INFO"; then
  echo "SxPID3 audit PDF build failed: output is not A4" >&2
  exit 1
fi
if ! awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$FONTS"; then
  echo "SxPID3 audit PDF build failed: fonts must be embedded and Unicode-mapped" >&2
  exit 1
fi
for sentinel in '18/108/166 crosswalk' '20,348 tables' '2,197,584' \
    'complete certificate' 'Explicit nonclaims and negative results'; do
  if ! grep -Fiq -- "$sentinel" "$TEXT"; then
    echo "SxPID3 audit PDF build failed: missing rendered sentinel: $sentinel" >&2
    exit 1
  fi
done

mkdir -p "$(dirname "$OUTPUT")"
OUTPUT_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$OUTPUT")" && pwd -P)"
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIRECTORY/.sxpid3-audit.XXXXXX.pdf")"
cp "$FIRST" "$OUTPUT_TEMP"
mv -f -- "$OUTPUT_TEMP" "$OUTPUT"
OUTPUT_TEMP=""
echo "OK: built $OUTPUT ($PAGES pages; $(shasum -a 256 "$OUTPUT" | awk '{print $1}'))"
