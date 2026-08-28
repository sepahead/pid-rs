#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/MATHEMATICAL_RESULTS_GUIDE.md"
HEADER="$ROOT/audit/formal/latex/mathematical-results-guide/header.tex"
FILTER="$ROOT/audit/formal/latex/mathematical-results-guide/filter.lua"
GUIDE_FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/mathematical-results-guide"
CROSSWALK_DIRECTORY="$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
DEFAULT_OUTPUT="$ROOT/output/pdf/mathematical-results-guide.pdf"
OUTPUT="${1:-$DEFAULT_OUTPUT}"
SOURCE_DATE_EPOCH_VALUE=1787875200
JOB_NAME="mathematical-results-guide"

if [[ "$#" -gt 1 || -z "$OUTPUT" ]]; then
  echo "usage: $0 [output.pdf]" >&2
  exit 2
fi

required_sources=(
  "$SOURCE"
  "$HEADER"
  "$FILTER"
  "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg"
  "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg"
  "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg"
)
for required_source in "${required_sources[@]}"; do
  if [[ ! -f "$required_source" || -L "$required_source" ]]; then
    echo "Mathematical results guide PDF build failed: missing or symbolic source: $required_source" >&2
    exit 1
  fi
done

validate_output_path() {
  local candidate="$1"
  local required_source

  # Bash's -ef compares the resolved device/inode pair. It therefore covers
  # exact, lexically normalized, parent-symlink, and hard-link aliases.
  for required_source in "${required_sources[@]}"; do
    if [[ "$candidate" -ef "$required_source" ]]; then
      echo "Mathematical results guide PDF build failed: output aliases canonical source: $required_source" >&2
      return 1
    fi
  done
  if [[ -L "$candidate" ]]; then
    echo "Mathematical results guide PDF build failed: output must not be symbolic: $candidate" >&2
    return 1
  fi
  if [[ "$candidate" != *.pdf ]]; then
    echo "Mathematical results guide PDF build failed: output path must end in .pdf: $candidate" >&2
    return 1
  fi
  if [[ -e "$candidate" && ! -f "$candidate" ]]; then
    echo "Mathematical results guide PDF build failed: existing output is not a regular file: $candidate" >&2
    return 1
  fi
}

# Reject unsafe destinations before dependency probes, temporary directories,
# source hashing, font discovery, or any renderer can run.
validate_output_path "$OUTPUT"

for command_name in awk cmp cp dirname fc-cache grep kpsewhich lualatex mkdir mktemp mv \
    pandoc pdffonts pdfinfo pdftotext rsvg-convert rm sed shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Mathematical results guide PDF build failed: missing command: $command_name" >&2
    exit 1
  fi
done

TMP_BASE="${PID_RS_PDF_TMPDIR:-${TMPDIR:-/tmp}}"
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-mathematical-results-guide-pdf.XXXXXX")"
OUTPUT_TEMP=""
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-mathematical-results-guide-pdf.*) rm -rf -- "$BUILD_ROOT" ;;
    *) echo "Mathematical results guide PDF build cleanup refused unexpected path: $BUILD_ROOT" >&2 ;;
  esac
  if [[ -n "$OUTPUT_TEMP" && -f "$OUTPUT_TEMP" && ! -L "$OUTPUT_TEMP" ]]; then
    rm -f -- "$OUTPUT_TEMP"
  fi
}
trap cleanup EXIT INT TERM

SOURCE_MANIFEST_BEFORE="$BUILD_ROOT/source-manifest-before.txt"
SOURCE_MANIFEST_PREPUBLISH="$BUILD_ROOT/source-manifest-prepublish.txt"
SOURCE_MANIFEST_AFTER_WRITE="$BUILD_ROOT/source-manifest-after-write.txt"
for required_source in "${required_sources[@]}"; do
  shasum -a 256 "$required_source"
done >"$SOURCE_MANIFEST_BEFORE"

LM_ROMAN="$(kpsewhich lmroman10-regular.otf)"
LM_SANS="$(kpsewhich lmsans10-regular.otf)"
LM_MONO="$(kpsewhich lmmonolt10-regular.otf)"
LM_MATH="$(kpsewhich latinmodern-math.otf)"
SOURCE_SANS="$(kpsewhich SourceSansPro-Regular.otf)"
for font_path in "$LM_ROMAN" "$LM_SANS" "$LM_MONO" "$LM_MATH" "$SOURCE_SANS"; do
  if [[ ! -f "$font_path" || -L "$font_path" ]]; then
    echo "Mathematical results guide PDF build failed: required font missing or symbolic" >&2
    exit 1
  fi
done
LM_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$LM_ROMAN")" && pwd -P)"
LM_MATH_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$LM_MATH")" && pwd -P)"
SOURCE_SANS_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$SOURCE_SANS")" && pwd -P)"

build_once() {
  local label="$1"
  local run_root="$BUILD_ROOT/$label"
  local staged_root="$run_root/repository"
  local staged_guide_figures="$staged_root/audit/formal/latex/figures/mathematical-results-guide"
  local staged_crosswalk="$staged_root/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
  local build_directory="$run_root/build"
  local home_directory="$run_root/home"
  local cache_directory="$run_root/cache"
  local texmfvar_directory="$run_root/texmf-var"
  local texmfconfig_directory="$run_root/texmf-config"
  local fontconfig_file="$run_root/fontconfig.xml"
  local raw_tex="$staged_root/$JOB_NAME.raw.tex"
  local normalized_tex="$staged_root/$JOB_NAME.tex"

  mkdir -p "$staged_guide_figures" "$staged_crosswalk" "$build_directory" \
    "$home_directory" "$cache_directory/fontconfig" "$texmfvar_directory" \
    "$texmfconfig_directory"
  cp "$SOURCE" "$staged_root/MATHEMATICAL_RESULTS_GUIDE.md"
  cp "$HEADER" "$staged_root/mathematical-results-guide-header.tex"
  cp "$FILTER" "$staged_root/mathematical-results-guide-filter.lua"
  cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" "$staged_guide_figures/semantic-firewall.svg"
  cp "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg" "$staged_guide_figures/result-evidence-map.svg"
  cp "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg" "$staged_crosswalk/audit-coordinate-crosswalk.svg"

  printf '%s\n' \
    '<?xml version="1.0"?>' '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">' '<fontconfig>' \
    "  <dir>$LM_DIRECTORY</dir>" "  <dir>$LM_MATH_DIRECTORY</dir>" \
    "  <dir>$SOURCE_SANS_DIRECTORY</dir>" \
    "  <cachedir>$cache_directory/fontconfig</cachedir>" '<config></config>' '</fontconfig>' \
    >"$fontconfig_file"

  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    fc-cache -f >/dev/null

  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_guide_figures/semantic-firewall.pdf" \
      "$staged_guide_figures/semantic-firewall.svg"
  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_guide_figures/result-evidence-map.pdf" \
      "$staged_guide_figures/result-evidence-map.svg"
  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_crosswalk/audit-coordinate-crosswalk.pdf" \
      "$staged_crosswalk/audit-coordinate-crosswalk.svg"

  (
    cd "$staged_root"
    env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
      XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
      OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
      TEXMFVAR="$texmfvar_directory" TEXMFCONFIG="$texmfconfig_directory" \
      LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
      FORCE_SOURCE_DATE=1 \
      pandoc MATHEMATICAL_RESULTS_GUIDE.md \
        --from=gfm+tex_math_dollars --to=latex --standalone --table-of-contents \
        --toc-depth=2 \
        --lua-filter=mathematical-results-guide-filter.lua \
        --include-in-header=mathematical-results-guide-header.tex \
        --metadata=title:'Mathematical results in pid-rs' \
        --metadata=author:'pid-rs project analysis' \
        --metadata=date:'28 August 2026' \
        --variable=colorlinks=true --variable=linkcolor:PidTeal \
        --variable=urlcolor:PidBronze --variable=citecolor:PidTeal \
        --variable=papersize:a4 --variable=fontsize:11pt --variable=geometry:margin=19mm \
        --variable=linestretch:1.055 --variable=mainfont:'Latin Modern Roman' \
        --variable=sansfont:'Source Sans Pro' --variable=monofont:'Latin Modern Mono Light' \
        --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
  )

  # Phase II supplies the structure tree on this pinned toolchain. This is not a PDF/UA claim.
  sed 's/^\\captionsetup\[table\]{skip=6pt}$/\\captionsetup*[table]{skip=6pt}/' "$raw_tex" \
    | awk 'BEGIN { print "\\DocumentMetadata{testphase=phase-II,lang=en-US}" } { print }' \
    >"$normalized_tex"

  local pass
  for pass in 1 2 3; do
    if ! (
      cd "$staged_root"
      env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
        XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
        OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
        TEXMFVAR="$texmfvar_directory" TEXMFCONFIG="$texmfconfig_directory" \
        LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
        FORCE_SOURCE_DATE=1 \
        lualatex --interaction=nonstopmode --halt-on-error --file-line-error \
          --jobname="$JOB_NAME" --output-directory="$build_directory" \
          "$normalized_tex" >"$build_directory/pass-$pass.stdout" 2>&1
    ); then
      cat "$build_directory/pass-$pass.stdout" >&2
      echo "Mathematical results guide PDF build failed: LuaLaTeX pass $pass failed" >&2
      exit 1
    fi
  done

  local built_pdf="$build_directory/$JOB_NAME.pdf"
  local final_log="$build_directory/$JOB_NAME.log"
  if [[ ! -s "$built_pdf" || ! -s "$final_log" ]]; then
    echo "Mathematical results guide PDF build failed: expected PDF/log absent" >&2
    exit 1
  fi
  if grep -En '(^| )(LaTeX|Package|Font) Warning:|warning  \(pdf backend\):|Overfull \\[hv]box|Undefined control sequence|Missing character:' "$final_log" >&2; then
    echo "Mathematical results guide PDF build failed: final pass contains warning or layout error" >&2
    exit 1
  fi
  printf '%s\n' "$built_pdf"
}

FIRST="$(build_once first)"
SECOND="$(build_once second)"
if ! cmp -s "$FIRST" "$SECOND"; then
  echo "Mathematical results guide PDF build failed: repeated builds differ" >&2
  exit 1
fi

for required_source in "${required_sources[@]}"; do
  shasum -a 256 "$required_source"
done >"$SOURCE_MANIFEST_PREPUBLISH"
if ! cmp -s "$SOURCE_MANIFEST_BEFORE" "$SOURCE_MANIFEST_PREPUBLISH"; then
  echo "Mathematical results guide PDF build failed: a canonical source changed during the build" >&2
  exit 1
fi

INFO="$BUILD_ROOT/final.info"
FONTS="$BUILD_ROOT/final.fonts"
TEXT="$BUILD_ROOT/final.txt"
if ! LC_ALL=C pdfinfo "$FIRST" >"$INFO" 2>"$BUILD_ROOT/final.info.stderr"; then
  cat "$BUILD_ROOT/final.info.stderr" >&2
  echo "Mathematical results guide PDF build failed: pdfinfo rejected the PDF" >&2
  exit 1
fi
if ! LC_ALL=C pdffonts "$FIRST" >"$FONTS" 2>"$BUILD_ROOT/final.fonts.stderr"; then
  cat "$BUILD_ROOT/final.fonts.stderr" >&2
  echo "Mathematical results guide PDF build failed: pdffonts rejected the PDF" >&2
  exit 1
fi
if ! LC_ALL=C pdftotext -layout "$FIRST" "$TEXT" 2>"$BUILD_ROOT/final.text.stderr"; then
  cat "$BUILD_ROOT/final.text.stderr" >&2
  echo "Mathematical results guide PDF build failed: pdftotext rejected the PDF" >&2
  exit 1
fi
for parser_stderr in "$BUILD_ROOT/final.info.stderr" "$BUILD_ROOT/final.fonts.stderr" \
    "$BUILD_ROOT/final.text.stderr"; do
  if [[ -s "$parser_stderr" ]]; then
    cat "$parser_stderr" >&2
    echo "Mathematical results guide PDF build failed: PDF parser emitted stderr" >&2
    exit 1
  fi
done
PAGES="$(awk '/^Pages:/ {print $2}' "$INFO")"
if [[ ! "$PAGES" =~ ^[0-9]+$ || "$PAGES" -lt 14 || "$PAGES" -gt 60 ]]; then
  echo "Mathematical results guide PDF build failed: implausible page count: ${PAGES:-missing}" >&2
  exit 1
fi
if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$INFO"; then
  echo "Mathematical results guide PDF build failed: output is not A4" >&2
  exit 1
fi
if ! grep -Eq '^Tagged:[[:space:]]+yes$' "$INFO"; then
  echo "Mathematical results guide PDF build failed: output must carry a PDF structure tree" >&2
  exit 1
fi
if ! awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$FONTS"; then
  echo "Mathematical results guide PDF build failed: fonts must be embedded and Unicode-mapped" >&2
  exit 1
fi
for sentinel in 'Five distinct lanes' '18 net atoms' '20,348' '2,197,584' \
    'Exact two-source categorical-Sx assurance' 'Represented-binary64 and quantizer assurance' \
    'repository/publication integration remains NO-GO'; do
  if ! grep -Fiq -- "$sentinel" "$TEXT"; then
    echo "Mathematical results guide PDF build failed: missing rendered sentinel: $sentinel" >&2
    exit 1
  fi
done

# Revalidate after the long-running render and immediately before publication.
# This closes a destination race without weakening the initial fast-fail gate.
validate_output_path "$OUTPUT"
mkdir -p "$(dirname "$OUTPUT")"
validate_output_path "$OUTPUT"
OUTPUT_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$OUTPUT")" && pwd -P)"
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIRECTORY/.mathematical-results-guide.XXXXXX.pdf")"
cp "$FIRST" "$OUTPUT_TEMP"
mv -f -- "$OUTPUT_TEMP" "$OUTPUT"
OUTPUT_TEMP=""

for required_source in "${required_sources[@]}"; do
  shasum -a 256 "$required_source"
done >"$SOURCE_MANIFEST_AFTER_WRITE"
if ! cmp -s "$SOURCE_MANIFEST_BEFORE" "$SOURCE_MANIFEST_AFTER_WRITE"; then
  echo "Mathematical results guide PDF build failed: a canonical source changed before or during publication" >&2
  exit 1
fi

echo "OK: built $OUTPUT ($PAGES pages; $(shasum -a 256 "$OUTPUT" | awk '{print $1}'))"
