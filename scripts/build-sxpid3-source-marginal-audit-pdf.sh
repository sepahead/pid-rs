#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
HEADER="$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/header.tex"
FILTER="$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/filter.lua"
FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
DEFAULT_OUTPUT="$ROOT/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
ID_VARIANCE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance.py"
ID_VARIANCE_CHECK_SHA256=d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7
SOURCE_DATE_EPOCH_VALUE=1788393600
JOB_NAME="sxpid3-source-marginal-and-bounded-audit"
MODE="--exact"
OUTPUT="$DEFAULT_OUTPUT"

case "$#" in
  0) ;;
  1)
    case "$1" in
      --exact | --cross-toolchain) MODE="$1" ;;
      *) OUTPUT="$1" ;;
    esac
    ;;
  2)
    MODE="$1"
    OUTPUT="$2"
    ;;
  *)
    echo "usage: $0 [--exact [output.pdf] | --cross-toolchain output.pdf]" >&2
    exit 2
    ;;
esac
if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]] || [[ -z "$OUTPUT" ]]; then
  echo "usage: $0 [--exact [output.pdf] | --cross-toolchain output.pdf]" >&2
  exit 2
fi
if [[ "$MODE" == "--cross-toolchain" && "$OUTPUT" == "$DEFAULT_OUTPUT" ]]; then
  echo "SxPID3 audit PDF build failed: cross-toolchain mode requires an explicit scratch output distinct from the canonical PDF" >&2
  exit 2
fi

required_sources=(
  "$SOURCE"
  "$HEADER"
  "$FILTER"
  "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.svg"
  "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.pdf"
  "$FIGURE_DIRECTORY/source-cylinder-factorization.svg"
  "$FIGURE_DIRECTORY/source-cylinder-factorization.pdf"
  "$ID_VARIANCE_CHECK"
)

validate_required_sources() {
  local required_source
  for required_source in "${required_sources[@]}"; do
    if [[ ! -f "$required_source" || -L "$required_source" ]]; then
      echo "SxPID3 audit PDF build failed: missing or symbolic source: $required_source" >&2
      return 1
    fi
  done
}

validate_output_path() {
  local candidate="$1"
  local output_name output_parent canonical_parent canonical_candidate required_source

  if [[ "$candidate" != /* || "$candidate" == *$'\n'* || "$candidate" == *$'\r'* ]]; then
    echo "SxPID3 audit PDF build failed: output must be a canonical absolute path" >&2
    return 1
  fi
  output_name="${candidate##*/}"
  output_parent="${candidate%/*}"
  [[ -n "$output_parent" ]] || output_parent="/"
  if [[ -z "$output_name" || "$output_name" == "." || "$output_name" == ".." \
      || "$output_name" != *.pdf ]]; then
    echo "SxPID3 audit PDF build failed: output path must name a .pdf file" >&2
    return 1
  fi
  if [[ ! -d "$output_parent" ]]; then
    echo "SxPID3 audit PDF build failed: output parent is absent or not a directory: $output_parent" >&2
    return 1
  fi
  if ! canonical_parent="$(CDPATH='' cd -- "$output_parent" && pwd -P)"; then
    echo "SxPID3 audit PDF build failed: cannot canonicalize output parent: $output_parent" >&2
    return 1
  fi
  if [[ "$canonical_parent" == "/" ]]; then
    echo "SxPID3 audit PDF build failed: filesystem root is not an admissible output parent" >&2
    return 1
  fi
  canonical_candidate="$canonical_parent/$output_name"
  if [[ "$candidate" != "$canonical_candidate" ]]; then
    echo "SxPID3 audit PDF build failed: output path has a symbolic or noncanonical component: $candidate" >&2
    return 1
  fi
  if [[ -L "$candidate" ]]; then
    echo "SxPID3 audit PDF build failed: output must not be symbolic: $candidate" >&2
    return 1
  fi
  if [[ -e "$candidate" && ! -f "$candidate" ]]; then
    echo "SxPID3 audit PDF build failed: existing output is not a regular file: $candidate" >&2
    return 1
  fi
  # Bash's -ef compares resolved device/inode identities, covering exact paths,
  # hard links, and symbolic aliases that survived an earlier path mutation.
  for required_source in "${required_sources[@]}"; do
    if [[ "$candidate" -ef "$required_source" ]]; then
      echo "SxPID3 audit PDF build failed: output aliases required source: $required_source" >&2
      return 1
    fi
  done
  if [[ "$MODE" == "--cross-toolchain" && -e "$DEFAULT_OUTPUT" \
      && "$candidate" -ef "$DEFAULT_OUTPUT" ]]; then
    echo "SxPID3 audit PDF build failed: cross-toolchain output aliases the canonical PDF" >&2
    return 1
  fi
}

# Reject unsafe destinations before dependency probes, temporary directories,
# source hashing, font discovery, or any renderer can run.
validate_required_sources
validate_output_path "$OUTPUT"

for command_name in awk cmp cp dirname fc-cache grep kpsewhich lualatex mkdir mktemp mv \
    pandoc pdffonts pdfinfo pdftotext python3 rm sed shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "SxPID3 audit PDF build failed: missing command: $command_name" >&2
    exit 1
  fi
done

validate_id_variance_checker() {
  local checker="$1"
  if [[ ! -f "$checker" || -L "$checker" ]]; then
    echo "SxPID3 audit PDF build failed: trailer-ID variance checker is absent, non-regular, or symbolic" >&2
    return 1
  fi
  if ! printf '%s  %s\n' "$ID_VARIANCE_CHECK_SHA256" "$checker" \
      | shasum -a 256 --check --status; then
    echo "SxPID3 audit PDF build failed: trailer-ID variance checker digest changed" >&2
    return 1
  fi
}
validate_id_variance_checker "$ID_VARIANCE_CHECK"
python3 -I -B -c 'import pypdf' >/dev/null 2>&1 || {
  echo "SxPID3 audit PDF build failed: pypdf is required for repeated-build custody" >&2
  exit 2
}

verify_figure_assets() {
  local directory="$1"
  printf '%s  %s\n' \
    5619f118cf53a11f16524c906f1d4542e22ebea685161998aade8acc5bae469a \
    "$directory/audit-coordinate-crosswalk.svg" \
    6cfa13f06f20b6240abb3b28e4aca60611b410fa88c9eb7a0074f2985bf1aa02 \
    "$directory/audit-coordinate-crosswalk.pdf" \
    a4c22c813275b1db3c554cc58ed82566dffe12594ef3b15660ccf0e1032ea061 \
    "$directory/source-cylinder-factorization.svg" \
    8578c1f911e56e91ff34849ea7ea19194fa7ae67c221db2e45b4b1c13aef639d \
    "$directory/source-cylinder-factorization.pdf" \
    | shasum -a 256 -c - >/dev/null || {
      echo "SxPID3 audit PDF build failed: canonical figure-asset bytes changed" >&2
      exit 1
    }
}
verify_figure_assets "$FIGURE_DIRECTORY"

TMP_BASE_INPUT="${PID_RS_PDF_TMPDIR:-${TMPDIR:-/tmp}}"
if ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "SxPID3 audit PDF build failed: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "SxPID3 audit PDF build failed: refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-sxpid3-audit-pdf.XXXXXX")"
OUTPUT_TEMP=""
SOURCE_MANIFEST_BEFORE="$BUILD_ROOT/source-manifest.before"
SOURCE_MANIFEST_CURRENT="$BUILD_ROOT/source-manifest.current"
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

source_manifest() {
  local required_source
  for required_source in "${required_sources[@]}"; do
    shasum -a 256 "$required_source"
  done
}

validate_repeated_inputs() {
  validate_required_sources
  source_manifest >"$SOURCE_MANIFEST_CURRENT"
  if ! cmp -s "$SOURCE_MANIFEST_BEFORE" "$SOURCE_MANIFEST_CURRENT"; then
    echo "SxPID3 audit PDF build failed: a required source changed during the build" >&2
    return 1
  fi
  verify_figure_assets "$FIGURE_DIRECTORY"
}

source_manifest >"$SOURCE_MANIFEST_BEFORE"

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
  local staged_id_variance_check="$staged_root/scripts/check-mathematical-results-guide-pdf-id-variance.py"

  mkdir -p "$staged_figures" "$staged_root/scripts" "$build_directory" "$home_directory" \
    "$cache_directory/fontconfig" "$texmfvar_directory" "$texmfconfig_directory"
  cp "$SOURCE" "$staged_root/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
  cp "$HEADER" "$staged_root/sxpid3-source-marginal-and-bounded-audit-header.tex"
  cp "$FILTER" "$staged_root/sxpid3-source-marginal-and-bounded-audit-filter.lua"
  cp "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.svg" "$staged_figures/audit-coordinate-crosswalk.svg"
  cp "$FIGURE_DIRECTORY/audit-coordinate-crosswalk.pdf" "$staged_figures/audit-coordinate-crosswalk.pdf"
  cp "$FIGURE_DIRECTORY/source-cylinder-factorization.svg" "$staged_figures/source-cylinder-factorization.svg"
  cp "$FIGURE_DIRECTORY/source-cylinder-factorization.pdf" "$staged_figures/source-cylinder-factorization.pdf"
  cp "$ID_VARIANCE_CHECK" "$staged_id_variance_check"
  verify_figure_assets "$staged_figures"
  validate_id_variance_checker "$staged_id_variance_check"

  printf '%s\n' \
    '<?xml version="1.0"?>' '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">' '<fontconfig>' \
    "  <dir>$LM_DIRECTORY</dir>" "  <dir>$LM_MATH_DIRECTORY</dir>" \
    "  <cachedir>$cache_directory/fontconfig</cachedir>" '<config></config>' '</fontconfig>' \
    >"$fontconfig_file"

  env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
    XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
    LC_ALL=C LANG=C TZ=UTC SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    fc-cache -f >/dev/null

  if ! (
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
        --metadata=date:'3 September 2026' \
        --variable=papersize:a4 --variable=fontsize:11pt --variable=geometry:margin=20mm \
        --variable=linestretch:1.06 --variable=mainfont:'Latin Modern Roman' \
        --variable=sansfont:'Latin Modern Sans' --variable=monofont:'Latin Modern Mono Light' \
        --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
  ); then
    echo "SxPID3 audit PDF build failed: Pandoc conversion failed" >&2
    exit 1
  fi

  sed 's/^\\captionsetup\[table\]{skip=6pt}$/\\captionsetup*[table]{skip=6pt}/' "$raw_tex" \
    | awk 'BEGIN { print "\\DocumentMetadata{testphase=phase-II,lang=en-US}" } { print }' \
    >"$normalized_tex"

  local pass
  for pass in 1 2 3; do
    if ! (
      cd "$staged_root"
      env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
        XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
        OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY" TEXMFVAR="$texmfvar_directory" \
        TEXMFCONFIG="$texmfconfig_directory" LC_ALL=C LANG=C TZ=UTC \
        SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" FORCE_SOURCE_DATE=1 \
        lualatex --interaction=nonstopmode --halt-on-error --file-line-error \
          --jobname="$JOB_NAME" --output-directory="$build_directory" \
          "$normalized_tex" >"$build_directory/pass-$pass.stdout" 2>&1
    ); then
      cat "$build_directory/pass-$pass.stdout" >&2
      echo "SxPID3 audit PDF build failed: LuaLaTeX pass $pass failed" >&2
      exit 1
    fi
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
  verify_figure_assets "$staged_figures"
  validate_id_variance_checker "$staged_id_variance_check"
}

build_once first
build_once second
FIRST="$BUILD_ROOT/first/build/$JOB_NAME.pdf"
SECOND="$BUILD_ROOT/second/build/$JOB_NAME.pdf"
STAGED_ID_VARIANCE_CHECK="$BUILD_ROOT/second/repository/scripts/check-mathematical-results-guide-pdf-id-variance.py"
validate_repeated_inputs
validate_id_variance_checker "$STAGED_ID_VARIANCE_CHECK"
if ! python3 -I -B "$STAGED_ID_VARIANCE_CHECK" --validate-inputs \
    "$FIRST" "$SECOND" >/dev/null; then
  echo "SxPID3 audit PDF build failed: repeated-build output custody check failed" >&2
  exit 1
fi
validate_repeated_inputs
validate_id_variance_checker "$STAGED_ID_VARIANCE_CHECK"
FIRST_SHA256="$(shasum -a 256 "$FIRST" | awk '{print $1}')"
SECOND_SHA256="$(shasum -a 256 "$SECOND" | awk '{print $1}')"
validate_built_outputs() {
  local observed_first observed_second
  validate_id_variance_checker "$STAGED_ID_VARIANCE_CHECK"
  if [[ ! -f "$FIRST" || -L "$FIRST" || ! -f "$SECOND" || -L "$SECOND" ]]; then
    echo "SxPID3 audit PDF build failed: repeated-build output became non-regular or symbolic" >&2
    return 1
  fi
  observed_first="$(shasum -a 256 "$FIRST" | awk '{print $1}')"
  observed_second="$(shasum -a 256 "$SECOND" | awk '{print $1}')"
  if [[ "$observed_first" != "$FIRST_SHA256" || "$observed_second" != "$SECOND_SHA256" ]]; then
    echo "SxPID3 audit PDF build failed: repeated-build output changed after comparison" >&2
    return 1
  fi
}
if cmp -s "$FIRST" "$SECOND"; then
  :
else
  CMP_STATUS=$?
  if [[ "$CMP_STATUS" -ne 1 ]]; then
    echo "SxPID3 audit PDF build failed: repeated-build cmp had operational status $CMP_STATUS" >&2
    exit 1
  fi
  if [[ "$MODE" != "--cross-toolchain" ]]; then
    echo "SxPID3 audit PDF build failed: repeated builds differ" >&2
    exit 1
  fi
  validate_repeated_inputs
  validate_id_variance_checker "$STAGED_ID_VARIANCE_CHECK"
  if ! python3 -I -B "$STAGED_ID_VARIANCE_CHECK" "$FIRST" "$SECOND"; then
    echo "SxPID3 audit PDF build failed: cross-toolchain repeated builds differ beyond the strict trailer-ID projection" >&2
    exit 1
  fi
  validate_repeated_inputs
  validate_id_variance_checker "$STAGED_ID_VARIANCE_CHECK"
fi
validate_repeated_inputs
validate_built_outputs

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
if ! grep -Eq '^Tagged:[[:space:]]+yes$' "$INFO"; then
  echo "SxPID3 audit PDF build failed: output must carry a PDF structure tree" >&2
  exit 1
fi
if ! awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$FONTS"; then
  echo "SxPID3 audit PDF build failed: fonts must be embedded and Unicode-mapped" >&2
  exit 1
fi
for sentinel in 'Paper event semantics' 'fresh owner-controlled HTTPS' \
    'separate exact compatibility edge' '18/108/166 crosswalk' '20,348 tables' '2,197,584' \
    'complete certificate' 'Explicit nonclaims and negative results'; do
  if ! grep -Fiq -- "$sentinel" "$TEXT"; then
    echo "SxPID3 audit PDF build failed: missing rendered sentinel: $sentinel" >&2
    exit 1
  fi
done

validate_repeated_inputs
validate_built_outputs
validate_output_path "$OUTPUT"
OUTPUT_DIRECTORY="${OUTPUT%/*}"
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIRECTORY/.sxpid3-audit.pdf.XXXXXX")"
cp "$FIRST" "$OUTPUT_TEMP"
if ! cmp -s "$FIRST" "$OUTPUT_TEMP"; then
  echo "SxPID3 audit PDF build failed: publication copy differs from the validated first build" >&2
  exit 1
fi
validate_repeated_inputs
validate_built_outputs
validate_output_path "$OUTPUT"
mv -f -- "$OUTPUT_TEMP" "$OUTPUT"
OUTPUT_TEMP=""
validate_repeated_inputs
validate_built_outputs
validate_output_path "$OUTPUT"
if ! cmp -s "$FIRST" "$OUTPUT"; then
  echo "SxPID3 audit PDF build failed: published output differs from the validated first build" >&2
  exit 1
fi
echo "OK: built $OUTPUT ($PAGES pages; $(shasum -a 256 "$OUTPUT" | awk '{print $1}'))"
