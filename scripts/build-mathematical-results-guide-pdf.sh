#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/MATHEMATICAL_RESULTS_GUIDE.md"
HEADER="$ROOT/audit/formal/latex/mathematical-results-guide/header.tex"
FILTER="$ROOT/audit/formal/latex/mathematical-results-guide/filter.lua"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
TAGPDF_OPENACTION_COMPAT_SHA256=6b638ef882260e54ad619b1ec9bfa775e7e8ecce04b24932ba41ca0e55e91f17
HGENERIC_URI_CONTENTS_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
HGENERIC_URI_CONTENTS_COMPAT_SHA256=6294db9644cff4d7ded8e2a98415d72cb73fae4f3a55ad705607b39edc391ad5
L3PDFFILE_FILESPEC_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
L3PDFFILE_FILESPEC_COMPAT_SHA256=a8eb78a26f554117fd5ff9661e617e0348e8e69fce3f63e3ff3c1321b51aa36a
PANDOC_TEX_NORMALIZER="$ROOT/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
PANDOC_TEX_NORMALIZER_SHA256=401271a933917833e7eca8654bd24e23f42fe19dfeab85c28165815bf55554bf
PANDOC_TEMPLATE_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
PANDOC_TEMPLATE_LICENSE_SHA256=cf5b70694cf50403b51f3315f98d010de6435022ff984911819219034a088180
CANONICAL_PANDOC_VERSION="pandoc 3.10.2"
LEGACY_PANDOC_VERSION="pandoc 3.1.3"
LEGACY_PANDOC_EXECUTABLE="/usr/bin/pandoc"
LEGACY_PANDOC_EXECUTABLE_SHA256=3dd273647f0265cb439f22976d5366a54b071a3783f6fec50838b47fb53d701b
FIGURE_ASSET_MANIFEST="$ROOT/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
FIGURE_ASSET_MANIFEST_SHA256=5bc3a24661b7a76c1a8a29d659f23aa27400d01ab5b6bd48cd3e75b91e88c852
FIGURE_ASSET_CHECK="$ROOT/scripts/check-mathematical-results-guide-figure-assets.py"
FIGURE_ASSET_CHECK_SHA256=075d5159f59eab5e927aef6a66f7380695269dc1aae447ef789bf3d84c4a5557
OPEN_FONT_REGENERATION="$ROOT/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json"
OPEN_FONT_REGENERATION_SHA256=250929cb33988a5914c1c427f76a24f7827e70fb499cad0ca361101666e7f4d3
OPEN_FONT_REGENERATOR="$ROOT/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
OPEN_FONT_REGENERATOR_SHA256=73d765c794167d206d6932084bb52e27cb503503407efc927f8ee261c3302b20
THIRD_PARTY_NOTICE="$ROOT/THIRD_PARTY_NOTICES.md"
THIRD_PARTY_NOTICE_SHA256=844a0c542d0ed3ce6af7eb0b0d4560e302963ced6d62da778203c1b953224427
SOURCE_SANS_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt"
SOURCE_SANS_LICENSE_SHA256=4a4a4179a96b5ef6786186d199f0d049b151352f460b8d2f3c00083792f37dd9
GUST_FONT_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt"
GUST_FONT_LICENSE_SHA256=49ea6cb9257bbee0a3979c48a774cd221550ac1c20c95549efe45fc99cc18050
LATIN_MODERN_MANIFEST="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt"
LATIN_MODERN_MANIFEST_SHA256=402c79f4ede8548a6fe6f82f42f0288cb0243ba2403dfdeeaadf55d189a46fae
ID_VARIANCE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance.py"
ID_VARIANCE_CHECK_SHA256=d8e87ecaf1d77ea4f4307fb8a397664c86dc059cf74840ca1583d69e16b5a6b7
FONT_ROSTER_CHECK="$ROOT/scripts/check-mathematical-results-guide-font-roster.py"
FONT_ROSTER_CHECK_SHA256=39e53d5c731a8c232f41691eb5378fb02df94b9a62819bcc6bcc3c8c849135d8
GUIDE_FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/mathematical-results-guide"
CROSSWALK_DIRECTORY="$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"
DEFAULT_OUTPUT="$ROOT/output/pdf/mathematical-results-guide.pdf"
SOURCE_DATE_EPOCH_VALUE=1787875200
JOB_NAME="mathematical-results-guide"
MODE="--exact"

if [[ "$#" -gt 0 ]]; then
  case "$1" in
    --exact|--cross-toolchain)
      MODE="$1"
      shift
      ;;
    --*)
      echo "usage: $0 [--exact [output.pdf] | --cross-toolchain output.pdf]" >&2
      exit 2
      ;;
  esac
fi
if [[ "$#" -gt 1 || ( "$MODE" == "--cross-toolchain" && "$#" -ne 1 ) ]]; then
  echo "usage: $0 [--exact [output.pdf] | --cross-toolchain output.pdf]" >&2
  exit 2
fi
OUTPUT="${1:-$DEFAULT_OUTPUT}"
if [[ -z "$OUTPUT" ]]; then
  echo "usage: $0 [--exact [output.pdf] | --cross-toolchain output.pdf]" >&2
  exit 2
fi

required_sources=(
  "$SOURCE"
  "$HEADER"
  "$FILTER"
  "$TAGPDF_OPENACTION_COMPAT"
  "$HGENERIC_URI_CONTENTS_COMPAT"
  "$L3PDFFILE_FILESPEC_COMPAT"
  "$PANDOC_TEX_NORMALIZER"
  "$PANDOC_TEMPLATE_LICENSE"
  "$FIGURE_ASSET_MANIFEST"
  "$FIGURE_ASSET_CHECK"
  "$OPEN_FONT_REGENERATION"
  "$OPEN_FONT_REGENERATOR"
  "$THIRD_PARTY_NOTICE"
  "$SOURCE_SANS_LICENSE"
  "$GUST_FONT_LICENSE"
  "$LATIN_MODERN_MANIFEST"
  "$ID_VARIANCE_CHECK"
  "$FONT_ROSTER_CHECK"
  "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg"
  "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.pdf"
  "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg"
  "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.pdf"
  "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg"
  "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.pdf"
  "$CROSSWALK_DIRECTORY/source-cylinder-factorization.svg"
  "$CROSSWALK_DIRECTORY/source-cylinder-factorization.pdf"
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
  if [[ "$MODE" == "--cross-toolchain" \
      && ( "$candidate" == "$DEFAULT_OUTPUT" || "$candidate" -ef "$DEFAULT_OUTPUT" ) ]]; then
    echo "Mathematical results guide PDF build failed: cross-toolchain mode cannot publish the canonical output" >&2
    return 1
  fi
}

# Reject unsafe destinations before dependency probes, temporary directories,
# source hashing, font discovery, or any renderer can run.
validate_output_path "$OUTPUT"

for command_name in awk cmp cp dirname fc-cache find grep kpsewhich lualatex mkdir mktemp mv \
    pandoc pdffonts pdfinfo pdftotext python3 rm sed shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Mathematical results guide PDF build failed: missing command: $command_name" >&2
    exit 1
  fi
done

PANDOC_VERSION_OUTPUT=""
if ! PANDOC_VERSION_OUTPUT="$(LC_ALL=C LANG=C pandoc --version 2>&1)"; then
  echo "Mathematical results guide PDF build failed: pandoc --version failed" >&2
  exit 1
fi
PANDOC_VERSION_FIRST_LINE="$(printf '%s\n' "$PANDOC_VERSION_OUTPUT" | sed -n '1p')"
if [[ ! "$PANDOC_VERSION_FIRST_LINE" =~ ^pandoc[[:space:]][0-9]+([.][0-9]+){1,3}([-+][0-9A-Za-z.-]+)?$ \
    || "${#PANDOC_VERSION_OUTPUT}" -gt 8192 \
    || "$(printf '%s\n' "$PANDOC_VERSION_OUTPUT" \
      | grep -Ec '^User data directory: .+$')" != "1" \
    || "$(printf '%s\n' "$PANDOC_VERSION_OUTPUT" \
      | grep -Ec '^Copyright \(C\) 2006-[0-9]{4} John MacFarlane([.] Web:[[:space:]]+https://pandoc[.]org)?$')" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: pandoc --version is not a recognized genuine-looking Pandoc report" >&2
  exit 1
fi
if [[ "$MODE" == "--exact" && "$PANDOC_VERSION_FIRST_LINE" != "$CANONICAL_PANDOC_VERSION" ]]; then
  echo "Mathematical results guide PDF build failed: exact mode requires $CANONICAL_PANDOC_VERSION" >&2
  exit 1
fi
if [[ "$PANDOC_VERSION_FIRST_LINE" != "$CANONICAL_PANDOC_VERSION" \
    && "$PANDOC_VERSION_FIRST_LINE" != "$LEGACY_PANDOC_VERSION" ]]; then
  echo "Mathematical results guide PDF build failed: Pandoc version is outside the two audited writer projections" >&2
  exit 1
fi
if [[ "$PANDOC_VERSION_FIRST_LINE" == "$LEGACY_PANDOC_VERSION" ]]; then
  PANDOC_RESOLVED="$(command -v pandoc)"
  if [[ "$PANDOC_RESOLVED" != "$LEGACY_PANDOC_EXECUTABLE" \
      || ! -f "$PANDOC_RESOLVED" || -L "$PANDOC_RESOLVED" \
      || "$(find "$PANDOC_RESOLVED" -type f -links 1 -print)" != "$PANDOC_RESOLVED" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc 3.1.3 executable custody changed" >&2
    exit 1
  fi
  if ! printf '%s  %s\n' "$LEGACY_PANDOC_EXECUTABLE_SHA256" "$PANDOC_RESOLVED" \
      | shasum -a 256 --check --status; then
    echo "Mathematical results guide PDF build failed: Pandoc 3.1.3 executable digest changed" >&2
    exit 1
  fi
fi

TMP_BASE_INPUT="${PID_RS_PDF_TMPDIR:-${TMPDIR:-/tmp}}"
if [[ ! -d "$TMP_BASE_INPUT" ]]; then
  echo "Mathematical results guide PDF build failed: temporary-directory base is absent" >&2
  exit 1
fi
TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"
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
SOURCE_MANIFEST_VALIDATED="$BUILD_ROOT/source-manifest-validated.txt"
SOURCE_MANIFEST_PREPUBLISH="$BUILD_ROOT/source-manifest-prepublish.txt"
SOURCE_MANIFEST_AFTER_WRITE="$BUILD_ROOT/source-manifest-after-write.txt"
for required_source in "${required_sources[@]}"; do
  shasum -a 256 "$required_source"
done >"$SOURCE_MANIFEST_BEFORE"

count_literal_occurrences() {
  local needle="$1"
  local input_path="${2:-$HEADER}"
  awk -v needle="$needle" '
    {
      line = $0
      while ((position = index(line, needle)) > 0) {
        count += 1
        line = substr(line, position + length(needle))
      }
    }
    END { print count + 0 }
  ' "$input_path"
}

GUIDE_SOURCE_SENTINELS=(
  'Five distinct lanes'
  'Thus, SxPID3 has 18 net atoms.'
  'The audit evaluates 2,197,584 products per route.'
  'repository/publication integration remains'
)
for source_sentinel in "${GUIDE_SOURCE_SENTINELS[@]}"; do
  if [[ "$(count_literal_occurrences "$source_sentinel" "$SOURCE")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: canonical Markdown source sentinel must occur exactly once: $source_sentinel" >&2
    exit 1
  fi
done

TAGPDF_COMPAT_BASENAME=mathematical-results-guide-tagpdf-openaction-compat.tex
if [[ "$(grep -Fxc '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
    "$HEADER")" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: tagpdf compatibility input must occur exactly once" >&2
  exit 1
fi
if [[ "$(count_literal_occurrences "$TAGPDF_COMPAT_BASENAME")" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: tagpdf compatibility basename must occur exactly once" >&2
  exit 1
fi
if [[ "$(grep -Fxc '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
    "$HEADER")" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: hgeneric URI-Contents compatibility input must occur exactly once" >&2
  exit 1
fi
URI_CONTENTS_COMPAT_BASENAME=mathematical-results-guide-hgeneric-uri-contents-compat.tex
URI_CONTENTS_COMPAT_OCCURRENCES="$(count_literal_occurrences "$URI_CONTENTS_COMPAT_BASENAME")"
if [[ "$URI_CONTENTS_COMPAT_OCCURRENCES" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: hgeneric URI-Contents compatibility basename must occur exactly once" >&2
  exit 1
fi
FILESPEC_COMPAT_BASENAME=mathematical-results-guide-l3pdffile-filespec-f-compat.tex
if [[ "$(grep -Fxc '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
    "$HEADER")" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: l3pdffile file-specification compatibility input must occur exactly once" >&2
  exit 1
fi
if [[ "$(count_literal_occurrences "$FILESPEC_COMPAT_BASENAME")" != "1" ]]; then
  echo "Mathematical results guide PDF build failed: l3pdffile file-specification compatibility basename must occur exactly once" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$TAGPDF_OPENACTION_COMPAT_SHA256" "$TAGPDF_OPENACTION_COMPAT" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: tagpdf compatibility source digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$HGENERIC_URI_CONTENTS_COMPAT_SHA256" \
    "$HGENERIC_URI_CONTENTS_COMPAT" | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: hgeneric URI-Contents compatibility source digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$L3PDFFILE_FILESPEC_COMPAT_SHA256" \
    "$L3PDFFILE_FILESPEC_COMPAT" | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: l3pdffile file-specification compatibility source digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$PANDOC_TEX_NORMALIZER_SHA256" "$PANDOC_TEX_NORMALIZER" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: Pandoc TeX normalizer digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$PANDOC_TEMPLATE_LICENSE_SHA256" "$PANDOC_TEMPLATE_LICENSE" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: Pandoc template license evidence digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$FIGURE_ASSET_MANIFEST_SHA256" "$FIGURE_ASSET_MANIFEST" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: canonical figure-asset manifest digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$FIGURE_ASSET_CHECK_SHA256" "$FIGURE_ASSET_CHECK" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: canonical figure-asset checker digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$OPEN_FONT_REGENERATION_SHA256" "$OPEN_FONT_REGENERATION" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: open-font regeneration contract digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$OPEN_FONT_REGENERATOR_SHA256" "$OPEN_FONT_REGENERATOR" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: open-font regenerator digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$THIRD_PARTY_NOTICE_SHA256" "$THIRD_PARTY_NOTICE" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: third-party font notice digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$SOURCE_SANS_LICENSE_SHA256" "$SOURCE_SANS_LICENSE" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: Source Sans Pro license evidence digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$GUST_FONT_LICENSE_SHA256" "$GUST_FONT_LICENSE" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: GUST Font License evidence digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$LATIN_MODERN_MANIFEST_SHA256" "$LATIN_MODERN_MANIFEST" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: Latin Modern v2.004 manifest evidence digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$ID_VARIANCE_CHECK_SHA256" "$ID_VARIANCE_CHECK" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: trailer-ID variance checker digest changed" >&2
  exit 1
fi
if ! printf '%s  %s\n' "$FONT_ROSTER_CHECK_SHA256" "$FONT_ROSTER_CHECK" \
    | shasum -a 256 --check --status; then
  echo "Mathematical results guide PDF build failed: final font-roster checker digest changed" >&2
  exit 1
fi
if ! python3 -I -B "$FIGURE_ASSET_CHECK" >/dev/null; then
  echo "Mathematical results guide PDF build failed: canonical figure assets rejected" >&2
  exit 1
fi
for required_source in "${required_sources[@]}"; do
  shasum -a 256 "$required_source"
done >"$SOURCE_MANIFEST_VALIDATED"
if ! cmp -s "$SOURCE_MANIFEST_BEFORE" "$SOURCE_MANIFEST_VALIDATED"; then
  echo "Mathematical results guide PDF build failed: canonical sources changed during validation" >&2
  exit 1
fi

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
  local projected_tex="$staged_root/$JOB_NAME.projected.tex"
  local normalized_tex="$staged_root/$JOB_NAME.tex"
  local staged_manifest="$staged_root/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
  local staged_contract_directory="$staged_root/audit/formal/latex/mathematical-results-guide"
  local staged_license_directory="$staged_contract_directory/font-licenses"
  local staged_checker="$staged_root/scripts/check-mathematical-results-guide-figure-assets.py"
  local staged_normalizer="$staged_root/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
  local staged_pandoc_template_license="$staged_contract_directory/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
  local staged_regeneration="$staged_contract_directory/open-font-figure-regeneration-v1.json"
  local staged_regenerator="$staged_root/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
  local staged_notice="$staged_root/THIRD_PARTY_NOTICES.md"
  local staged_source_sans_license="$staged_license_directory/source-sans-pro-ofl-1.1-tex-live-2024.txt"
  local staged_gust_font_license="$staged_license_directory/gust-font-license-1.0-tex-live-2024.txt"
  local staged_latin_modern_manifest="$staged_license_directory/manifest-latin-modern-2.004-tex-live-2024.txt"
  local staged_id_variance_check="$staged_root/scripts/check-mathematical-results-guide-pdf-id-variance.py"
  local staged_font_roster_check="$staged_root/scripts/check-mathematical-results-guide-font-roster.py"
  local staged_manifest_before="$run_root/staged-source-manifest-before.txt"
  local staged_manifest_after="$run_root/staged-source-manifest-after.txt"
  local expected_digest_sequence="$run_root/expected-source-digests.txt"

  mkdir -p "$staged_guide_figures" "$staged_crosswalk" "$staged_license_directory" \
    "$staged_root/scripts" "$build_directory" \
    "$home_directory" "$cache_directory/fontconfig" \
    "$texmfvar_directory/luatex-cache/generic/names" \
    "$texmfconfig_directory"
  cp "$SOURCE" "$staged_root/MATHEMATICAL_RESULTS_GUIDE.md"
  cp "$HEADER" "$staged_root/mathematical-results-guide-header.tex"
  cp "$FILTER" "$staged_root/mathematical-results-guide-filter.lua"
  cp "$TAGPDF_OPENACTION_COMPAT" \
    "$staged_root/mathematical-results-guide-tagpdf-openaction-compat.tex"
  cp "$HGENERIC_URI_CONTENTS_COMPAT" \
    "$staged_root/mathematical-results-guide-hgeneric-uri-contents-compat.tex"
  cp "$L3PDFFILE_FILESPEC_COMPAT" \
    "$staged_root/mathematical-results-guide-l3pdffile-filespec-f-compat.tex"
  cp "$PANDOC_TEX_NORMALIZER" "$staged_normalizer"
  cp "$PANDOC_TEMPLATE_LICENSE" "$staged_pandoc_template_license"
  cp "$FIGURE_ASSET_MANIFEST" "$staged_manifest"
  cp "$FIGURE_ASSET_CHECK" "$staged_checker"
  cp "$OPEN_FONT_REGENERATION" "$staged_regeneration"
  cp "$OPEN_FONT_REGENERATOR" "$staged_regenerator"
  cp "$THIRD_PARTY_NOTICE" "$staged_notice"
  cp "$SOURCE_SANS_LICENSE" "$staged_source_sans_license"
  cp "$GUST_FONT_LICENSE" "$staged_gust_font_license"
  cp "$LATIN_MODERN_MANIFEST" "$staged_latin_modern_manifest"
  cp "$ID_VARIANCE_CHECK" "$staged_id_variance_check"
  cp "$FONT_ROSTER_CHECK" "$staged_font_roster_check"
  cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" "$staged_guide_figures/semantic-firewall.svg"
  cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.pdf" "$staged_guide_figures/semantic-firewall.pdf"
  cp "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg" "$staged_guide_figures/result-evidence-map.svg"
  cp "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.pdf" "$staged_guide_figures/result-evidence-map.pdf"
  cp "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg" "$staged_crosswalk/audit-coordinate-crosswalk.svg"
  cp "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.pdf" "$staged_crosswalk/audit-coordinate-crosswalk.pdf"
  cp "$CROSSWALK_DIRECTORY/source-cylinder-factorization.svg" "$staged_crosswalk/source-cylinder-factorization.svg"
  cp "$CROSSWALK_DIRECTORY/source-cylinder-factorization.pdf" "$staged_crosswalk/source-cylinder-factorization.pdf"

  local staged_sources=(
    "$staged_root/MATHEMATICAL_RESULTS_GUIDE.md"
    "$staged_root/mathematical-results-guide-header.tex"
    "$staged_root/mathematical-results-guide-filter.lua"
    "$staged_root/mathematical-results-guide-tagpdf-openaction-compat.tex"
    "$staged_root/mathematical-results-guide-hgeneric-uri-contents-compat.tex"
    "$staged_root/mathematical-results-guide-l3pdffile-filespec-f-compat.tex"
    "$staged_normalizer"
    "$staged_pandoc_template_license"
    "$staged_manifest"
    "$staged_checker"
    "$staged_regeneration"
    "$staged_regenerator"
    "$staged_notice"
    "$staged_source_sans_license"
    "$staged_gust_font_license"
    "$staged_latin_modern_manifest"
    "$staged_id_variance_check"
    "$staged_font_roster_check"
    "$staged_guide_figures/semantic-firewall.svg"
    "$staged_guide_figures/semantic-firewall.pdf"
    "$staged_guide_figures/result-evidence-map.svg"
    "$staged_guide_figures/result-evidence-map.pdf"
    "$staged_crosswalk/audit-coordinate-crosswalk.svg"
    "$staged_crosswalk/audit-coordinate-crosswalk.pdf"
    "$staged_crosswalk/source-cylinder-factorization.svg"
    "$staged_crosswalk/source-cylinder-factorization.pdf"
  )
  awk '{print $1}' "$SOURCE_MANIFEST_BEFORE" >"$expected_digest_sequence"
  for required_source in "${staged_sources[@]}"; do
    shasum -a 256 "$required_source"
  done | awk '{print $1}' >"$staged_manifest_before"
  if ! cmp -s "$expected_digest_sequence" "$staged_manifest_before"; then
    echo "Mathematical results guide PDF build failed: staged source bytes differ from validated sources" >&2
    exit 1
  fi
  if ! python3 -I -B "$staged_checker" "$staged_root" >/dev/null; then
    echo "Mathematical results guide PDF build failed: staged canonical figure assets rejected" >&2
    exit 1
  fi

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

  (
    cd "$staged_root"
    env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
      XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
      OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
      TEXMFVAR="$texmfvar_directory" TEXMFCACHE="$texmfvar_directory" \
      TEXMFCONFIG="$texmfconfig_directory" \
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
        --variable=toccolor:PidTeal \
        --variable=urlcolor:PidBronze --variable=citecolor:PidTeal \
        --variable=papersize:a4 --variable=fontsize:11pt --variable=geometry:margin=19mm \
        --variable=linestretch:1.055 --variable=mainfont:'Latin Modern Roman' \
        --variable=sansfont:'Source Sans Pro' --variable=monofont:'Latin Modern Mono Light' \
        --variable=mathfont:'Latin Modern Math' --output="$raw_tex"
  )

  if [[ ! -s "$raw_tex" || -L "$raw_tex" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc raw TeX is absent, empty, or symbolic" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
      "$raw_tex")" != "1" \
      || "$(count_literal_occurrences "$TAGPDF_COMPAT_BASENAME" "$raw_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc raw TeX does not contain exactly one tagpdf compatibility input" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
      "$raw_tex")" != "1" \
      || "$(count_literal_occurrences "$URI_CONTENTS_COMPAT_BASENAME" "$raw_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc raw TeX does not contain exactly one hgeneric URI-Contents compatibility input" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
      "$raw_tex")" != "1" \
      || "$(count_literal_occurrences "$FILESPEC_COMPAT_BASENAME" "$raw_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc raw TeX does not contain exactly one l3pdffile file-specification compatibility input" >&2
    exit 1
  fi
  for source_sentinel in "${GUIDE_SOURCE_SENTINELS[@]}"; do
    if [[ "$(count_literal_occurrences "$source_sentinel" "$raw_tex")" != "1" ]]; then
      echo "Mathematical results guide PDF build failed: Pandoc raw TeX source sentinel must occur exactly once: $source_sentinel" >&2
      exit 1
    fi
  done
  if grep -Fq '\hypersetup{linkcolor=}' "$raw_tex" \
      || [[ "$(grep -Fxc '\hypersetup{linkcolor=PidTeal}' "$raw_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: Pandoc raw TeX has an empty or unexpected table-of-contents link color" >&2
    exit 1
  fi

  local expected_normalizer_stdout
  if [[ "$PANDOC_VERSION_FIRST_LINE" == "$LEGACY_PANDOC_VERSION" ]]; then
    expected_normalizer_stdout='OK: normalized mathematical-results guide Pandoc TeX (mode=legacy-3.1.3; heading_wrappers_removed=17; table_wrappers_inserted=4; none_counter_inserted=1; table_preamble_replaced=1; image_preamble_replaced=1; crosswalk_projection_replaced=1; byte_identity=no)'
  else
    expected_normalizer_stdout='OK: normalized mathematical-results guide Pandoc TeX (mode=canonical; heading_wrappers_removed=0; table_wrappers_inserted=0; none_counter_inserted=0; table_preamble_replaced=0; image_preamble_replaced=0; crosswalk_projection_replaced=0; byte_identity=yes)'
  fi
  if ! printf '%s  %s\n' "$PANDOC_TEX_NORMALIZER_SHA256" "$staged_normalizer" \
      | shasum -a 256 --check --status; then
    echo "Mathematical results guide PDF build failed: staged Pandoc TeX normalizer digest changed" >&2
    exit 1
  fi
  local normalizer_stdout
  if ! normalizer_stdout="$(python3 -I -S -B "$staged_normalizer" \
      "$PANDOC_VERSION_FIRST_LINE" "$raw_tex" "$projected_tex" \
      2>"$run_root/pandoc-tex-normalizer.stderr")"; then
    cat "$run_root/pandoc-tex-normalizer.stderr" >&2
    echo "Mathematical results guide PDF build failed: Pandoc TeX normalization failed" >&2
    exit 1
  fi
  if [[ -s "$run_root/pandoc-tex-normalizer.stderr" \
      || "$normalizer_stdout" != "$expected_normalizer_stdout" ]]; then
    cat "$run_root/pandoc-tex-normalizer.stderr" >&2
    echo "Mathematical results guide PDF build failed: Pandoc TeX normalizer diagnostics changed" >&2
    exit 1
  fi
  if ! printf '%s  %s\n' "$PANDOC_TEX_NORMALIZER_SHA256" "$staged_normalizer" \
      | shasum -a 256 --check --status; then
    echo "Mathematical results guide PDF build failed: staged Pandoc TeX normalizer changed during execution" >&2
    exit 1
  fi
  if [[ ! -s "$projected_tex" || -L "$projected_tex" ]]; then
    echo "Mathematical results guide PDF build failed: normalized Pandoc TeX is absent, empty, or symbolic" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
      "$projected_tex")" != "1" \
      || "$(count_literal_occurrences "$TAGPDF_COMPAT_BASENAME" "$projected_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: normalized Pandoc TeX does not contain exactly one tagpdf compatibility input" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
      "$projected_tex")" != "1" \
      || "$(count_literal_occurrences "$URI_CONTENTS_COMPAT_BASENAME" "$projected_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: normalized Pandoc TeX does not contain exactly one hgeneric URI-Contents compatibility input" >&2
    exit 1
  fi
  if [[ "$(grep -Fxc '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
      "$projected_tex")" != "1" \
      || "$(count_literal_occurrences "$FILESPEC_COMPAT_BASENAME" "$projected_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: normalized Pandoc TeX does not contain exactly one l3pdffile file-specification compatibility input" >&2
    exit 1
  fi
  for source_sentinel in "${GUIDE_SOURCE_SENTINELS[@]}"; do
    if [[ "$(count_literal_occurrences "$source_sentinel" "$projected_tex")" != "1" ]]; then
      echo "Mathematical results guide PDF build failed: normalized Pandoc TeX source sentinel must occur exactly once: $source_sentinel" >&2
      exit 1
    fi
  done
  if grep -Fq '\hypersetup{linkcolor=}' "$projected_tex" \
      || [[ "$(grep -Fxc '\hypersetup{linkcolor=PidTeal}' "$projected_tex")" != "1" ]]; then
    echo "Mathematical results guide PDF build failed: normalized Pandoc TeX has an empty or unexpected table-of-contents link color" >&2
    exit 1
  fi

  # Phase II supplies the structure tree on this pinned toolchain. This is not a PDF/UA claim.
  sed 's/^\\captionsetup\[table\]{skip=6pt}$/\\captionsetup*[table]{skip=6pt}/' "$projected_tex" \
    | awk 'BEGIN { print "\\DocumentMetadata{testphase=phase-II,lang=en-US}" } { print }' \
    >"$normalized_tex"

  local pass
  for pass in 1 2 3; do
    if ! (
      cd "$staged_root"
      env -i PATH="$PATH" HOME="$home_directory" TMPDIR="$run_root" \
        XDG_CACHE_HOME="$cache_directory" FONTCONFIG_FILE="$fontconfig_file" \
        OSFONTDIR="$LM_DIRECTORY:$LM_MATH_DIRECTORY:$SOURCE_SANS_DIRECTORY" \
        TEXMFVAR="$texmfvar_directory" TEXMFCACHE="$texmfvar_directory" \
        TEXMFCONFIG="$texmfconfig_directory" \
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
  for required_source in "${staged_sources[@]}"; do
    shasum -a 256 "$required_source"
  done | awk '{print $1}' >"$staged_manifest_after"
  if ! cmp -s "$staged_manifest_before" "$staged_manifest_after"; then
    echo "Mathematical results guide PDF build failed: staged canonical sources changed during rendering" >&2
    exit 1
  fi
  printf '%s\n' "$built_pdf"
}

FIRST="$(build_once first)"
SECOND="$(build_once second)"
STAGED_ID_VARIANCE_CHECK="$BUILD_ROOT/second/repository/scripts/check-mathematical-results-guide-pdf-id-variance.py"
STAGED_FONT_ROSTER_CHECK="$BUILD_ROOT/second/repository/scripts/check-mathematical-results-guide-font-roster.py"
validate_staged_id_checker() {
  if [[ ! -f "$STAGED_ID_VARIANCE_CHECK" || -L "$STAGED_ID_VARIANCE_CHECK" ]]; then
    echo "Mathematical results guide PDF build failed: staged trailer-ID variance checker is absent, non-regular, or symbolic" >&2
    return 1
  fi
  if ! printf '%s  %s\n' "$ID_VARIANCE_CHECK_SHA256" "$STAGED_ID_VARIANCE_CHECK" \
      | shasum -a 256 --check --status; then
    echo "Mathematical results guide PDF build failed: staged trailer-ID variance checker digest changed" >&2
    return 1
  fi
}
validate_staged_font_roster_checker() {
  if [[ ! -f "$STAGED_FONT_ROSTER_CHECK" || -L "$STAGED_FONT_ROSTER_CHECK" ]]; then
    echo "Mathematical results guide PDF build failed: staged final font-roster checker is absent, non-regular, or symbolic" >&2
    return 1
  fi
  if ! printf '%s  %s\n' "$FONT_ROSTER_CHECK_SHA256" "$STAGED_FONT_ROSTER_CHECK" \
      | shasum -a 256 --check --status; then
    echo "Mathematical results guide PDF build failed: staged final font-roster checker digest changed" >&2
    return 1
  fi
}
validate_repeated_inputs() {
  validate_staged_id_checker
  validate_staged_font_roster_checker
  if ! python3 -I -B "$STAGED_ID_VARIANCE_CHECK" --validate-inputs \
      "$FIRST" "$SECOND" >/dev/null; then
    echo "Mathematical results guide PDF build failed: repeated-build output custody check failed" >&2
    return 1
  fi
  validate_staged_id_checker
  validate_staged_font_roster_checker
}

validate_repeated_inputs
FIRST_SHA256="$(shasum -a 256 "$FIRST" | awk '{print $1}')"
SECOND_SHA256="$(shasum -a 256 "$SECOND" | awk '{print $1}')"
if cmp -s "$FIRST" "$SECOND"; then
  :
else
  CMP_STATUS=$?
  if [[ "$CMP_STATUS" -ne 1 ]]; then
    echo "Mathematical results guide PDF build failed: repeated-build cmp had operational status $CMP_STATUS" >&2
    exit 1
  fi
  if [[ "$MODE" != "--cross-toolchain" ]]; then
    echo "Mathematical results guide PDF build failed: repeated builds differ" >&2
    exit 1
  fi
  validate_staged_id_checker
  if ! python3 -I -B \
      "$STAGED_ID_VARIANCE_CHECK" \
      "$FIRST" "$SECOND"; then
    echo "Mathematical results guide PDF build failed: cross-toolchain repeated builds differ beyond the strict trailer-ID projection" >&2
    exit 1
  fi
  validate_staged_id_checker
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
FONT_ROSTER="$BUILD_ROOT/final.font-roster"
FONT_ROSTER_OPTIMIZED="$BUILD_ROOT/final.font-roster-optimized"
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
validate_staged_font_roster_checker
if ! python3 -I -S -B "$STAGED_FONT_ROSTER_CHECK" "$FONTS" >"$FONT_ROSTER"; then
  echo "Mathematical results guide PDF build failed: final font roster violates the open-font contract" >&2
  exit 1
fi
validate_staged_font_roster_checker
if ! python3 -O -I -S -B "$STAGED_FONT_ROSTER_CHECK" "$FONTS" \
    >"$FONT_ROSTER_OPTIMIZED"; then
  echo "Mathematical results guide PDF build failed: optimized Python rejected the final font roster" >&2
  exit 1
fi
validate_staged_font_roster_checker
if ! cmp -s "$FONT_ROSTER" "$FONT_ROSTER_OPTIMIZED"; then
  echo "Mathematical results guide PDF build failed: final font roster differs under optimized Python" >&2
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
validate_repeated_inputs
if [[ "$(shasum -a 256 "$FIRST" | awk '{print $1}')" != "$FIRST_SHA256" \
    || "$(shasum -a 256 "$SECOND" | awk '{print $1}')" != "$SECOND_SHA256" ]]; then
  echo "Mathematical results guide PDF build failed: repeated-build output changed after comparison" >&2
  exit 1
fi
validate_output_path "$OUTPUT"
mkdir -p "$(dirname "$OUTPUT")"
validate_output_path "$OUTPUT"
OUTPUT_DIRECTORY="$(CDPATH='' cd -- "$(dirname "$OUTPUT")" && pwd -P)"
OUTPUT_TEMP="$(mktemp "$OUTPUT_DIRECTORY/.mathematical-results-guide.XXXXXX.pdf")"
cp "$FIRST" "$OUTPUT_TEMP"
if ! cmp -s "$FIRST" "$OUTPUT_TEMP"; then
  echo "Mathematical results guide PDF build failed: publication copy differs from the validated first build" >&2
  exit 1
fi
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
