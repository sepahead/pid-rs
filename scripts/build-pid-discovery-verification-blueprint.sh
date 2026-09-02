#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md"
HEADER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-header.tex"
FILTER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-filter.lua"
FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
DEFAULT_OUTPUT="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"
OUTPUT="${1:-$DEFAULT_OUTPUT}"
SOURCE_DATE_EPOCH_VALUE=1788307200
JOB_NAME="pid-discovery-verification-and-durability-blueprint"

if [[ "$#" -gt 1 || -z "$OUTPUT" ]]; then
  echo "usage: $0 [output.pdf]" >&2
  exit 2
fi

required_commands=(
  awk
  chmod
  cmp
  cp
  dirname
  fc-cache
  grep
  kpsewhich
  lualatex
  mkdir
  mktemp
  mv
  pandoc
  pdffonts
  pdfinfo
  pdftotext
  rsvg-convert
  rm
  sed
  shasum
)
for command_name in "${required_commands[@]}"; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "blueprint PDF build failed: missing command: $command_name" >&2
    exit 1
  fi
done

required_sources=(
  "$SOURCE"
  "$HEADER"
  "$FILTER"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-source-card.svg"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-pid-card.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-stages.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-storage.svg"
)
for required_source in "${required_sources[@]}"; do
  if [[ ! -f "$required_source" || -L "$required_source" ]]; then
    echo "blueprint PDF build failed: missing or symbolic-link source: $required_source" >&2
    exit 1
  fi
done

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
if ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "blueprint PDF build failed: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "blueprint PDF build failed: refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-blueprint-pdf.XXXXXX")"
OUTPUT_TEMP=""
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-blueprint-pdf.*) rm -rf -- "$BUILD_ROOT" ;;
    *) echo "blueprint PDF build cleanup refused unexpected path: $BUILD_ROOT" >&2 ;;
  esac
  if [[ -n "$OUTPUT_TEMP" && -f "$OUTPUT_TEMP" && ! -L "$OUTPUT_TEMP" ]]; then
    rm -f -- "$OUTPUT_TEMP"
  fi
}
trap cleanup EXIT INT TERM

LM_ROMAN="$(kpsewhich lmroman10-regular.otf)"
LM_MONO="$(kpsewhich lmmonolt10-regular.otf)"
LM_MATH="$(kpsewhich latinmodern-math.otf)"
SOURCE_SANS_REGULAR="$(kpsewhich SourceSansPro-Regular.otf)"
SOURCE_SANS_REGULAR_ITALIC="$(kpsewhich SourceSansPro-RegularIt.otf)"
SOURCE_SANS_SEMIBOLD="$(kpsewhich SourceSansPro-Semibold.otf)"
SOURCE_SANS_SEMIBOLD_ITALIC="$(kpsewhich SourceSansPro-SemiboldIt.otf)"
SOURCE_SANS_BOLD="$(kpsewhich SourceSansPro-Bold.otf)"
SOURCE_SANS_BOLD_ITALIC="$(kpsewhich SourceSansPro-BoldIt.otf)"
SOURCE_SANS_BLACK="$(kpsewhich SourceSansPro-Black.otf)"
for font_path in "$LM_ROMAN" "$LM_MONO" "$LM_MATH" \
    "$SOURCE_SANS_REGULAR" "$SOURCE_SANS_REGULAR_ITALIC" \
    "$SOURCE_SANS_SEMIBOLD" "$SOURCE_SANS_SEMIBOLD_ITALIC" \
    "$SOURCE_SANS_BOLD" "$SOURCE_SANS_BOLD_ITALIC" "$SOURCE_SANS_BLACK"; do
  if [[ ! -f "$font_path" || -L "$font_path" ]]; then
    echo "blueprint PDF build failed: required publication font is missing or symbolic: $font_path" >&2
    exit 1
  fi
done
LM_DIRECTORY="$(cd "$(dirname "$LM_ROMAN")" && pwd -P)"
LM_MATH_DIRECTORY="$(cd "$(dirname "$LM_MATH")" && pwd -P)"
SOURCE_SANS_DIRECTORY="$(cd "$(dirname "$SOURCE_SANS_REGULAR")" && pwd -P)"

build_once() {
  local label="$1"
  local run_root="$BUILD_ROOT/$label"
  local staged_root="$run_root/repository"
  local staged_figure_directory="$staged_root/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
  local build_directory="$run_root/build"
  local home_directory="$run_root/home"
  local cache_directory="$run_root/cache"
  local texmfvar_directory="$run_root/texmf-var"
  local texmfconfig_directory="$run_root/texmf-config"
  local fontconfig_file="$run_root/fontconfig.xml"
  local empty_fontconfig_path="$run_root/empty-fontconfig-path"
  local raw_tex="$staged_root/$JOB_NAME.raw.tex"
  local normalized_tex="$staged_root/$JOB_NAME.tex"

  mkdir -p "$staged_figure_directory" "$build_directory" "$home_directory" \
    "$cache_directory/fontconfig" "$texmfvar_directory/luatex-cache/generic/names" \
    "$texmfconfig_directory" \
    "$empty_fontconfig_path"
  cp "$SOURCE" "$staged_root/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md"
  cp "$HEADER" "$staged_root/pid-discovery-verification-and-durability-blueprint-header.tex"
  cp "$FILTER" "$staged_root/pid-discovery-verification-and-durability-blueprint-filter.lua"
  cp "$FIGURE_DIRECTORY/semantic-transfer-firewall-source-card.svg" "$staged_figure_directory/semantic-transfer-firewall-source-card.svg"
  cp "$FIGURE_DIRECTORY/semantic-transfer-firewall-pid-card.svg" "$staged_figure_directory/semantic-transfer-firewall-pid-card.svg"
  cp "$FIGURE_DIRECTORY/durable-promotion-state-machine-stages.svg" "$staged_figure_directory/durable-promotion-state-machine-stages.svg"
  cp "$FIGURE_DIRECTORY/durable-promotion-state-machine-storage.svg" "$staged_figure_directory/durable-promotion-state-machine-storage.svg"

  printf '%s\n' \
    '<?xml version="1.0"?>' \
    '<!DOCTYPE fontconfig SYSTEM "fonts.dtd">' \
    '<fontconfig>' \
    "  <dir>$LM_DIRECTORY</dir>" \
    "  <dir>$LM_MATH_DIRECTORY</dir>" \
    "  <dir>$SOURCE_SANS_DIRECTORY</dir>" \
    "  <cachedir>$cache_directory/fontconfig</cachedir>" \
    '  <config></config>' \
    '</fontconfig>' >"$fontconfig_file"

  env -i \
    "PATH=$PATH" \
    "HOME=$home_directory" \
    "TMPDIR=$run_root" \
    "XDG_CACHE_HOME=$cache_directory" \
    "FONTCONFIG_FILE=$fontconfig_file" \
    "FONTCONFIG_PATH=$empty_fontconfig_path" \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    fc-cache -f >/dev/null

  env -i \
    "PATH=$PATH" \
    "HOME=$home_directory" \
    "TMPDIR=$run_root" \
    "XDG_CACHE_HOME=$cache_directory" \
    "FONTCONFIG_FILE=$fontconfig_file" \
    "FONTCONFIG_PATH=$empty_fontconfig_path" \
    PANGOCAIRO_BACKEND=fontconfig \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_figure_directory/semantic-transfer-firewall-source-card.pdf" \
      "$staged_figure_directory/semantic-transfer-firewall-source-card.svg"
  env -i \
    "PATH=$PATH" \
    "HOME=$home_directory" \
    "TMPDIR=$run_root" \
    "XDG_CACHE_HOME=$cache_directory" \
    "FONTCONFIG_FILE=$fontconfig_file" \
    "FONTCONFIG_PATH=$empty_fontconfig_path" \
    PANGOCAIRO_BACKEND=fontconfig \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_figure_directory/semantic-transfer-firewall-pid-card.pdf" \
      "$staged_figure_directory/semantic-transfer-firewall-pid-card.svg"
  env -i \
    "PATH=$PATH" \
    "HOME=$home_directory" \
    "TMPDIR=$run_root" \
    "XDG_CACHE_HOME=$cache_directory" \
    "FONTCONFIG_FILE=$fontconfig_file" \
    "FONTCONFIG_PATH=$empty_fontconfig_path" \
    PANGOCAIRO_BACKEND=fontconfig \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_figure_directory/durable-promotion-state-machine-stages.pdf" \
      "$staged_figure_directory/durable-promotion-state-machine-stages.svg"
  env -i \
    "PATH=$PATH" \
    "HOME=$home_directory" \
    "TMPDIR=$run_root" \
    "XDG_CACHE_HOME=$cache_directory" \
    "FONTCONFIG_FILE=$fontconfig_file" \
    "FONTCONFIG_PATH=$empty_fontconfig_path" \
    PANGOCAIRO_BACKEND=fontconfig \
    LC_ALL=C \
    LANG=C \
    TZ=UTC \
    SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
    rsvg-convert --format=pdf --keep-aspect-ratio \
      --output="$staged_figure_directory/durable-promotion-state-machine-storage.pdf" \
      "$staged_figure_directory/durable-promotion-state-machine-storage.svg"

  (
    cd "$staged_root"
    env -i \
      "PATH=$PATH" \
      "HOME=$home_directory" \
      "TMPDIR=$run_root" \
      "XDG_CACHE_HOME=$cache_directory" \
      "FONTCONFIG_FILE=$fontconfig_file" \
      "OSFONTDIR=$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
      "TEXMFVAR=$texmfvar_directory" \
      "TEXMFCACHE=$texmfvar_directory" \
      "TEXMFCONFIG=$texmfconfig_directory" \
      LC_ALL=C \
      LANG=C \
      TZ=UTC \
      SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
      FORCE_SOURCE_DATE=1 \
      pandoc PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md \
        --from=gfm+tex_math_dollars \
        --to=latex \
        --standalone \
        --table-of-contents \
        --toc-depth=3 \
        --number-sections \
        --lua-filter=pid-discovery-verification-and-durability-blueprint-filter.lua \
        --include-in-header=pid-discovery-verification-and-durability-blueprint-header.tex \
        --variable=papersize:a4 \
        --variable=fontsize:10pt \
        --variable=geometry:margin=18mm \
        --variable=linestretch:1.04 \
        --variable=mainfont:'Latin Modern Roman' \
        --variable=sansfont:'Source Sans Pro' \
        --variable=monofont:'Latin Modern Mono Light' \
        --variable=mathfont:'Latin Modern Math' \
        --output="$raw_tex"
  )

  # Pandoc's template emits an unused table-only caption setup for this caption-free report.
  # The starred form preserves the setting while suppressing caption's false-positive warning.
  sed 's/^\\captionsetup\[table\]{skip=6pt}$/\\captionsetup*[table]{skip=6pt}/' \
    "$raw_tex" >"$normalized_tex"

  local pass
  for pass in 1 2 3; do
    if ! (
      cd "$staged_root"
      env -i \
        "PATH=$PATH" \
        "HOME=$home_directory" \
        "TMPDIR=$run_root" \
        "XDG_CACHE_HOME=$cache_directory" \
        "FONTCONFIG_FILE=$fontconfig_file" \
        "OSFONTDIR=$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
        "TEXMFVAR=$texmfvar_directory" \
        "TEXMFCACHE=$texmfvar_directory" \
        "TEXMFCONFIG=$texmfconfig_directory" \
        LC_ALL=C \
        LANG=C \
        TZ=UTC \
        SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" \
        FORCE_SOURCE_DATE=1 \
        lualatex \
          --interaction=nonstopmode \
          --halt-on-error \
          --file-line-error \
          --jobname="$JOB_NAME" \
          --output-directory="$build_directory" \
          "$normalized_tex" >"$build_directory/pass-$pass.stdout" 2>&1
    ); then
      cat "$build_directory/pass-$pass.stdout" >&2
      echo "blueprint PDF build failed: LuaLaTeX pass $pass failed" >&2
      exit 1
    fi
  done

  local built_pdf="$build_directory/$JOB_NAME.pdf"
  local final_log="$build_directory/$JOB_NAME.log"
  if [[ ! -s "$built_pdf" || ! -s "$final_log" ]]; then
    echo "blueprint PDF build failed: compiler did not produce the expected PDF and log" >&2
    exit 1
  fi
  if grep -En '(^| )(LaTeX|Package|Font) Warning:|Overfull \\[hv]box|Undefined control sequence|Missing character:' "$final_log"; then
    echo "blueprint PDF build failed: final LuaLaTeX pass contains a warning or layout error" >&2
    exit 1
  fi

  LC_ALL=C pdfinfo "$built_pdf" >"$build_directory/pdfinfo.txt"
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$build_directory/pdfinfo.txt")"
  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 12 || "$pages" -gt 40 ]]; then
    echo "blueprint PDF build failed: implausible page count: $pages" >&2
    exit 1
  fi
  if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$build_directory/pdfinfo.txt"; then
    echo "blueprint PDF build failed: output is not A4" >&2
    exit 1
  fi
  if ! grep -Eq '^PDF version:[[:space:]]+1\.7$' "$build_directory/pdfinfo.txt"; then
    echo "blueprint PDF build failed: output is not PDF 1.7" >&2
    exit 1
  fi

  LC_ALL=C pdffonts "$built_pdf" >"$build_directory/pdffonts.txt"
  if ! awk '
    NR <= 2 { next }
    NF == 0 { next }
    {
      seen = 1
      if ($0 !~ /[[:space:]](Type 1C[[:space:]]+WinAnsi|CID Type 0C[[:space:]]+Identity-H)[[:space:]]+yes[[:space:]]+yes[[:space:]]+yes[[:space:]]+[0-9]+[[:space:]]+[0-9]+$/) {
        bad = 1
      }
    }
    END { exit (!seen || bad) }
  ' "$build_directory/pdffonts.txt"; then
    echo "blueprint PDF build failed: every font must be a subsetted, embedded, Unicode-mapped CFF program with its declared encoding" >&2
    exit 1
  fi
  for required_face in LMRoman LMMonoLt10-Regular LatinModernMath-Regular \
      SourceSansPro-Regular SourceSansPro-Semibold SourceSansPro-Bold SourceSansPro-Black; do
    if ! grep -Fq "$required_face" "$build_directory/pdffonts.txt"; then
      cat "$build_directory/pdffonts.txt" >&2
      echo "blueprint PDF build failed: required publication face is absent: $required_face" >&2
      exit 1
    fi
  done

  LC_ALL=C pdftotext -layout "$built_pdf" "$build_directory/layout.txt"
  required_text=(
    "Begin with source meaning"
    "Semantic transfer firewall, part 1"
    "averaged empirical categorical SxPID3"
    "108 keyed scalar audit expressions"
    "Dated 1 September 2026 adversarial publication closure"
    "PASS identifies current-byte evidence"
    "seventy typed rows in total"
    "Twenty mandatory core lenses"
    "Fifty additional artifact-specific hostile lenses"
    "Ten materially distinct routes"
    "D1 remains open"
    "bounded corpus and optional shards"
    "Autoresearch without evidence laundering"
    "Repository durability and promotion"
    "remote-ref, ancestry, hosted-run, and recovery-drill checks pass"
    "Durable promotion state machine, part 1"
    "Review-boundary safety disposition"
    "Source-anchored claim register"
  )
  for needle in "${required_text[@]}"; do
    if ! grep -Fq "$needle" "$build_directory/layout.txt"; then
      echo "blueprint PDF build failed: missing extracted-text anchor: $needle" >&2
      exit 1
    fi
  done
  if grep -Fq $'\357\277\275' "$build_directory/layout.txt"; then
    echo "blueprint PDF build failed: extracted text contains a Unicode replacement character" >&2
    exit 1
  fi

  cp "$built_pdf" "$run_root/final.pdf"
  printf '%s\t%s\t%s\n' "$label" "$pages" "$(shasum -a 256 "$run_root/final.pdf" | awk '{print $1}')"
}

build_once first
build_once second
if ! cmp "$BUILD_ROOT/first/final.pdf" "$BUILD_ROOT/second/final.pdf"; then
  echo "blueprint PDF build failed: isolated repeated builds are not byte-identical" >&2
  exit 1
fi

OUTPUT_DIRECTORY="$(dirname "$OUTPUT")"
mkdir -p "$OUTPUT_DIRECTORY"
if [[ -L "$OUTPUT" || ( -e "$OUTPUT" && ! -f "$OUTPUT" ) ]]; then
  echo "blueprint PDF build failed: output must be a regular file, never a symbolic link: $OUTPUT" >&2
  exit 1
fi
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIRECTORY/.pid-blueprint-pdf.XXXXXX")"
cp "$BUILD_ROOT/first/final.pdf" "$OUTPUT_TEMP"
chmod 0644 "$OUTPUT_TEMP"
mv -f -- "$OUTPUT_TEMP" "$OUTPUT"
OUTPUT_TEMP=""
printf 'OK: same-toolchain reproducible PID blueprint PDF\npath\t%s\nsha256\t%s\n' \
  "$OUTPUT" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
