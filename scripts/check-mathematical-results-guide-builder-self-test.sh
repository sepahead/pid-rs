#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-mathematical-results-guide-pdf.sh"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
HGENERIC_URI_CONTENTS_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
L3PDFFILE_FILESPEC_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
PANDOC_TEX_NORMALIZER="$ROOT/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
PANDOC_TEMPLATE_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
FIGURE_ASSET_MANIFEST="$ROOT/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
FIGURE_ASSET_CHECK="$ROOT/scripts/check-mathematical-results-guide-figure-assets.py"
OPEN_FONT_REGENERATION="$ROOT/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json"
OPEN_FONT_REGENERATOR="$ROOT/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
THIRD_PARTY_NOTICE="$ROOT/THIRD_PARTY_NOTICES.md"
SOURCE_SANS_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt"
GUST_FONT_LICENSE="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt"
LATIN_MODERN_MANIFEST="$ROOT/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt"
ID_VARIANCE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-id-variance.py"
FONT_ROSTER_CHECK="$ROOT/scripts/check-mathematical-results-guide-font-roster.py"
CANONICAL_GUIDE="$ROOT/output/pdf/mathematical-results-guide.pdf"
GUIDE_FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/mathematical-results-guide"
CROSSWALK_DIRECTORY="$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit"

for command_name in awk bash chmod cmp cp grep ln mkdir mktemp python3 rm sed shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Mathematical results guide builder self-test failed: missing command: $command_name" >&2
    exit 1
  fi
done
REAL_CP="$(command -v cp)"
REAL_CMP="$(command -v cmp)"
for source in "$BUILDER" "$TAGPDF_OPENACTION_COMPAT" "$HGENERIC_URI_CONTENTS_COMPAT" \
    "$L3PDFFILE_FILESPEC_COMPAT" "$PANDOC_TEX_NORMALIZER" "$PANDOC_TEMPLATE_LICENSE" \
    "$FIGURE_ASSET_MANIFEST" "$FIGURE_ASSET_CHECK" \
    "$OPEN_FONT_REGENERATION" "$OPEN_FONT_REGENERATOR" "$THIRD_PARTY_NOTICE" \
    "$SOURCE_SANS_LICENSE" "$GUST_FONT_LICENSE" "$LATIN_MODERN_MANIFEST" \
    "$ID_VARIANCE_CHECK" "$FONT_ROSTER_CHECK" \
    "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" \
    "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.pdf" \
    "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg" \
    "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.pdf" \
    "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg" \
    "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.pdf" \
    "$CROSSWALK_DIRECTORY/source-cylinder-factorization.svg" \
    "$CROSSWALK_DIRECTORY/source-cylinder-factorization.pdf"; do
  if [[ ! -f "$source" || -L "$source" ]]; then
    echo "Mathematical results guide builder self-test failed: required source is absent, non-regular, or symbolic: $source" >&2
    exit 1
  fi
done
if [[ ! -f "$CANONICAL_GUIDE" || -L "$CANONICAL_GUIDE" ]]; then
  echo "Mathematical results guide builder self-test failed: canonical guide is absent, non-regular, or symbolic" >&2
  exit 1
fi

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-mathematical-results-guide-builder-self-test.XXXXXX")"
cleanup() {
  case "$TEST_ROOT" in
    "${TMPDIR:-/tmp}"/pid-rs-mathematical-results-guide-builder-self-test.*)
      rm -rf -- "$TEST_ROOT"
      ;;
    *)
      echo "Mathematical results guide builder self-test cleanup refused unexpected path: $TEST_ROOT" >&2
      ;;
  esac
}
trap cleanup EXIT INT TERM

FIXTURE_REPO="$TEST_ROOT/repository"
FAKE_BIN="$TEST_ROOT/fake-bin"
MARKER="$TEST_ROOT/kpsewhich-called.txt"
RUN_TMP="$TEST_ROOT/build-tmp"
mkdir -p \
  "$FIXTURE_REPO/scripts" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses" \
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit" \
  "$FAKE_BIN" "$RUN_TMP"
cp "$BUILDER" "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh"
chmod +x "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh"

printf '%s\n' \
  '# Fixture guide' \
  'Five distinct lanes' \
  'Thus, SxPID3 has 18 net atoms.' \
  'The audit evaluates 2,197,584 products per route.' \
  'repository/publication integration remains' \
  >"$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/header.tex"
printf '%s\n' 'return {}' \
  >"$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/filter.lua"
cp "$TAGPDF_OPENACTION_COMPAT" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
cp "$HGENERIC_URI_CONTENTS_COMPAT" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
cp "$L3PDFFILE_FILESPEC_COMPAT" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
cp "$PANDOC_TEX_NORMALIZER" \
  "$FIXTURE_REPO/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
cp "$PANDOC_TEMPLATE_LICENSE" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
cp "$FIGURE_ASSET_MANIFEST" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
cp "$FIGURE_ASSET_CHECK" "$FIXTURE_REPO/scripts/check-mathematical-results-guide-figure-assets.py"
cp "$OPEN_FONT_REGENERATION" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json"
cp "$OPEN_FONT_REGENERATOR" \
  "$FIXTURE_REPO/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
cp "$THIRD_PARTY_NOTICE" "$FIXTURE_REPO/THIRD_PARTY_NOTICES.md"
cp "$SOURCE_SANS_LICENSE" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt"
cp "$GUST_FONT_LICENSE" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt"
cp "$LATIN_MODERN_MANIFEST" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt"
cp "$ID_VARIANCE_CHECK" "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
cp "$FONT_ROSTER_CHECK" "$FIXTURE_REPO/scripts/check-mathematical-results-guide-font-roster.py"
cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" \
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"
cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.pdf" \
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf"
cp "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.svg" \
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg"
cp "$GUIDE_FIGURE_DIRECTORY/result-evidence-map.pdf" \
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf"
cp "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.svg" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg"
cp "$CROSSWALK_DIRECTORY/audit-coordinate-crosswalk.pdf" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf"
cp "$CROSSWALK_DIRECTORY/source-cylinder-factorization.svg" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.svg"
cp "$CROSSWALK_DIRECTORY/source-cylinder-factorization.pdf" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.pdf"

# shellcheck disable=SC2016 # The generated fake expands these variables at runtime.
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "$*" >>"$PID_RS_BUILDER_TEST_MARKER"' \
  'exit 97' >"$FAKE_BIN/kpsewhich"
chmod +x "$FAKE_BIN/kpsewhich"
for command_name in fc-cache lualatex pdffonts pdfinfo pdftotext; do
  printf '%s\n' '#!/usr/bin/env bash' 'exit 98' >"$FAKE_BIN/$command_name"
  chmod +x "$FAKE_BIN/$command_name"
done
write_preflight_pandoc() {
  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'if [[ "$#" -eq 1 && "$1" == --version ]]; then' \
    '  printf "%s\n" "pandoc 3.10.2" "Features: +lua" "User data directory: /fixture" "Copyright (C) 2006-2026 John MacFarlane. Web: https://pandoc.org"' \
    '  exit 0' \
    'fi' \
    'exit 98' \
    >"$FAKE_BIN/pandoc"
  chmod +x "$FAKE_BIN/pandoc"
}
write_preflight_pandoc

required_sources=(
  "$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/header.tex"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/filter.lua"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
  "$FIXTURE_REPO/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-figure-assets.py"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json"
  "$FIXTURE_REPO/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
  "$FIXTURE_REPO/THIRD_PARTY_NOTICES.md"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt"
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
  "$FIXTURE_REPO/scripts/check-mathematical-results-guide-font-roster.py"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf"
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf"
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.pdf"
)
source_manifest() {
  local required_source
  for required_source in "${required_sources[@]}"; do
    shasum -a 256 "$required_source"
  done
}
BASELINE_MANIFEST="$(source_manifest)"

CASES=0
assert_sources_unchanged() {
  local observed
  observed="$(source_manifest)"
  if [[ "$observed" != "$BASELINE_MANIFEST" ]]; then
    echo "Mathematical results guide builder self-test failed: a fixture source changed" >&2
    exit 1
  fi
}

expect_fast_failure() {
  local name="$1"
  local output_path="$2"
  local expected_message="$3"
  local transcript status

  rm -f -- "$MARKER"
  if transcript="$(
    PATH="$FAKE_BIN:$PATH" \
      PID_RS_BUILDER_TEST_MARKER="$MARKER" \
      PID_RS_BUILDER_TEST_REAL_CP="$REAL_CP" \
      PID_RS_BUILDER_TEST_SUBSTITUTE_SOURCE="${PID_RS_BUILDER_TEST_SUBSTITUTE_SOURCE:-}" \
      PID_RS_BUILDER_TEST_SUBSTITUTE_BYTES="${PID_RS_BUILDER_TEST_SUBSTITUTE_BYTES:-}" \
      PID_RS_BUILDER_TEST_FONT_CONTROL="${FIXTURE_HEADER:-}" \
      PID_RS_PDF_TMPDIR="$RUN_TMP" \
      bash "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh" \
        "$output_path" 2>&1
  )"; then
    echo "Mathematical results guide builder self-test failed: $name unexpectedly passed" >&2
    exit 1
  else
    status=$?
  fi
  if [[ "$status" -eq 0 || ! "$transcript" =~ $expected_message ]]; then
    echo "Mathematical results guide builder self-test failed: $name had an unexpected failure" >&2
    printf '%s\n' "$transcript" >&2
    exit 1
  fi
  if [[ -e "$MARKER" ]]; then
    echo "Mathematical results guide builder self-test failed: $name reached font discovery" >&2
    exit 1
  fi
  assert_sources_unchanged
  CASES=$((CASES + 1))
}

expect_argument_failure() {
  local name="$1"
  local expected_message="$2"
  shift 2
  local transcript status

  rm -f -- "$MARKER"
  if transcript="$(
    PATH="$FAKE_BIN:$PATH" \
      PID_RS_BUILDER_TEST_MARKER="$MARKER" \
      PID_RS_PDF_TMPDIR="$RUN_TMP" \
      bash "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh" \
        "$@" 2>&1
  )"; then
    echo "Mathematical results guide builder self-test failed: $name unexpectedly passed" >&2
    exit 1
  else
    status=$?
  fi
  if [[ "$status" -eq 0 || ! "$transcript" =~ $expected_message ]]; then
    echo "Mathematical results guide builder self-test failed: $name had an unexpected failure" >&2
    printf '%s\n' "$transcript" >&2
    exit 1
  fi
  if [[ -e "$MARKER" ]]; then
    echo "Mathematical results guide builder self-test failed: $name reached font discovery" >&2
    exit 1
  fi
  assert_sources_unchanged
  CASES=$((CASES + 1))
}

expect_mutated_source_failure() {
  local name="$1"
  local expected_message="$2"
  local transcript status

  rm -f -- "$MARKER"
  if transcript="$(
    PATH="$FAKE_BIN:$PATH" \
      PID_RS_BUILDER_TEST_MARKER="$MARKER" \
      PID_RS_PDF_TMPDIR="$RUN_TMP" \
      bash "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh" \
        "$TEST_ROOT/mutated-source.pdf" 2>&1
  )"; then
    echo "Mathematical results guide builder self-test failed: $name unexpectedly passed" >&2
    exit 1
  else
    status=$?
  fi
  if [[ "$status" -eq 0 || ! "$transcript" =~ $expected_message ]]; then
    echo "Mathematical results guide builder self-test failed: $name had an unexpected failure" >&2
    printf '%s\n' "$transcript" >&2
    exit 1
  fi
  if [[ -e "$MARKER" ]]; then
    echo "Mathematical results guide builder self-test failed: $name reached font discovery" >&2
    exit 1
  fi
  CASES=$((CASES + 1))
}

FIXTURE_HEADER="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/header.tex"
FIXTURE_COMPAT="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
FIXTURE_URI_COMPAT="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/hgeneric-uri-contents-compat.tex"
FIXTURE_FILESPEC_COMPAT="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/l3pdffile-filespec-f-compat.tex"
FIXTURE_PANDOC_TEX_NORMALIZER="$FIXTURE_REPO/scripts/normalize-mathematical-results-guide-pandoc-tex.py"
FIXTURE_PANDOC_TEMPLATE_LICENSE="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt"
FIXTURE_FIGURE_MANIFEST="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/canonical-figure-pdfs.json"
FIXTURE_FIGURE_CHECK="$FIXTURE_REPO/scripts/check-mathematical-results-guide-figure-assets.py"
FIXTURE_OPEN_FONT_REGENERATION="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json"
FIXTURE_OPEN_FONT_REGENERATOR="$FIXTURE_REPO/scripts/regenerate-mathematical-results-guide-open-font-figures.py"
FIXTURE_THIRD_PARTY_NOTICE="$FIXTURE_REPO/THIRD_PARTY_NOTICES.md"
FIXTURE_SOURCE_SANS_LICENSE="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt"
FIXTURE_GUST_FONT_LICENSE="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt"
FIXTURE_LATIN_MODERN_MANIFEST="$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt"
FIXTURE_ID_VARIANCE_CHECK="$FIXTURE_REPO/scripts/check-mathematical-results-guide-pdf-id-variance.py"
FIXTURE_FONT_ROSTER_CHECK="$FIXTURE_REPO/scripts/check-mathematical-results-guide-font-roster.py"
FIXTURE_SEMANTIC_SVG="$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"
FIXTURE_SEMANTIC_PDF="$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf"
FIXTURE_RESULT_PDF="$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.pdf"
FIXTURE_BUILDER="$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh"

rm -f -- "$FIXTURE_COMPAT"
expect_mutated_source_failure \
  "removed compatibility source" \
  "missing or symbolic source"
cp "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT"
assert_sources_unchanged

printf '%s\n' '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "duplicate compatibility application" \
  "compatibility input must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

printf '%s\n' '\input {mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "spacing-varied tagpdf compatibility application" \
  "tagpdf compatibility basename must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

rm -f -- "$FIXTURE_URI_COMPAT"
expect_mutated_source_failure \
  "removed URI-Contents compatibility source" \
  "missing or symbolic source"
cp "$HGENERIC_URI_CONTENTS_COMPAT" "$FIXTURE_URI_COMPAT"
assert_sources_unchanged

rm -f -- "$FIXTURE_FILESPEC_COMPAT"
expect_mutated_source_failure \
  "removed file-specification compatibility source" \
  "missing or symbolic source"
cp "$L3PDFFILE_FILESPEC_COMPAT" "$FIXTURE_FILESPEC_COMPAT"
assert_sources_unchanged

printf '%s\n' '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "duplicate URI-Contents compatibility application" \
  "hgeneric URI-Contents compatibility input must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

printf '%s\n' '\input {mathematical-results-guide-hgeneric-uri-contents-compat.tex}' \
  >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "spacing-varied URI-Contents compatibility application" \
  "hgeneric URI-Contents compatibility basename must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

printf '%s\n' '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "duplicate file-specification compatibility application" \
  "l3pdffile file-specification compatibility input must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

printf '%s\n' '\input {mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  >>"$FIXTURE_HEADER"
expect_mutated_source_failure \
  "spacing-varied file-specification compatibility application" \
  "l3pdffile file-specification compatibility basename must occur exactly once"
printf '%s\n' '% fixture header' \
  '\input{mathematical-results-guide-tagpdf-openaction-compat.tex}' \
  '\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}' \
  '\AtBeginDocument{\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}' \
  >"$FIXTURE_HEADER"
assert_sources_unchanged

sed 's|v0.96d|v0.96c|' "$HGENERIC_URI_CONTENTS_COMPAT" >"$FIXTURE_URI_COMPAT"
expect_mutated_source_failure \
  "URI-Contents compatibility source drift" \
  "hgeneric URI-Contents compatibility source digest changed"
cp "$HGENERIC_URI_CONTENTS_COMPAT" "$FIXTURE_URI_COMPAT"
assert_sources_unchanged

sed 's|0.96d|0.96c|' "$L3PDFFILE_FILESPEC_COMPAT" >"$FIXTURE_FILESPEC_COMPAT"
expect_mutated_source_failure \
  "file-specification compatibility source drift" \
  "l3pdffile file-specification compatibility source digest changed"
cp "$L3PDFFILE_FILESPEC_COMPAT" "$FIXTURE_FILESPEC_COMPAT"
assert_sources_unchanged

printf '%s\n' '# hostile normalizer drift' >>"$FIXTURE_PANDOC_TEX_NORMALIZER"
expect_mutated_source_failure \
  "Pandoc TeX normalizer drift" \
  "Pandoc TeX normalizer digest changed"
cp "$PANDOC_TEX_NORMALIZER" "$FIXTURE_PANDOC_TEX_NORMALIZER"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_PANDOC_TEMPLATE_LICENSE"
expect_mutated_source_failure \
  "Pandoc template license evidence drift" \
  "Pandoc template license evidence digest changed"
cp "$PANDOC_TEMPLATE_LICENSE" "$FIXTURE_PANDOC_TEMPLATE_LICENSE"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_FIGURE_MANIFEST"
expect_mutated_source_failure \
  "canonical figure manifest drift" \
  "canonical figure-asset manifest digest changed"
cp "$FIGURE_ASSET_MANIFEST" "$FIXTURE_FIGURE_MANIFEST"
assert_sources_unchanged

printf '%s\n' '# hostile checker drift' >>"$FIXTURE_FIGURE_CHECK"
expect_mutated_source_failure \
  "canonical figure checker drift" \
  "canonical figure-asset checker digest changed"
cp "$FIGURE_ASSET_CHECK" "$FIXTURE_FIGURE_CHECK"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_OPEN_FONT_REGENERATION"
expect_mutated_source_failure \
  "open-font regeneration contract drift" \
  "open-font regeneration contract digest changed"
cp "$OPEN_FONT_REGENERATION" "$FIXTURE_OPEN_FONT_REGENERATION"
assert_sources_unchanged

printf '%s\n' '# hostile regenerator drift' >>"$FIXTURE_OPEN_FONT_REGENERATOR"
expect_mutated_source_failure \
  "open-font regenerator drift" \
  "open-font regenerator digest changed"
cp "$OPEN_FONT_REGENERATOR" "$FIXTURE_OPEN_FONT_REGENERATOR"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_THIRD_PARTY_NOTICE"
expect_mutated_source_failure \
  "third-party font notice drift" \
  "third-party font notice digest changed"
cp "$THIRD_PARTY_NOTICE" "$FIXTURE_THIRD_PARTY_NOTICE"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_SOURCE_SANS_LICENSE"
expect_mutated_source_failure \
  "Source Sans Pro license evidence drift" \
  "Source Sans Pro license evidence digest changed"
cp "$SOURCE_SANS_LICENSE" "$FIXTURE_SOURCE_SANS_LICENSE"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_GUST_FONT_LICENSE"
expect_mutated_source_failure \
  "GUST Font License evidence drift" \
  "GUST Font License evidence digest changed"
cp "$GUST_FONT_LICENSE" "$FIXTURE_GUST_FONT_LICENSE"
assert_sources_unchanged

printf '%s\n' ' ' >>"$FIXTURE_LATIN_MODERN_MANIFEST"
expect_mutated_source_failure \
  "Latin Modern v2.004 manifest evidence drift" \
  "Latin Modern v2.004 manifest evidence digest changed"
cp "$LATIN_MODERN_MANIFEST" "$FIXTURE_LATIN_MODERN_MANIFEST"
assert_sources_unchanged

printf '%s\n' '# hostile trailer-ID checker drift' >>"$FIXTURE_ID_VARIANCE_CHECK"
expect_mutated_source_failure \
  "trailer-ID variance checker drift" \
  "trailer-ID variance checker digest changed"
cp "$ID_VARIANCE_CHECK" "$FIXTURE_ID_VARIANCE_CHECK"
assert_sources_unchanged

printf '%s\n' '# hostile final font-roster checker drift' >>"$FIXTURE_FONT_ROSTER_CHECK"
expect_mutated_source_failure \
  "final font-roster checker drift" \
  "final font-roster checker digest changed"
cp "$FONT_ROSTER_CHECK" "$FIXTURE_FONT_ROSTER_CHECK"
assert_sources_unchanged

printf '%s' 'hostile' >>"$FIXTURE_SEMANTIC_PDF"
expect_mutated_source_failure \
  "canonical figure derivative drift" \
  "derivative digest changed"
cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.pdf" "$FIXTURE_SEMANTIC_PDF"
assert_sources_unchanged

printf '%s\n' '<!-- hostile -->' >>"$FIXTURE_SEMANTIC_SVG"
expect_mutated_source_failure \
  "canonical figure SVG drift" \
  "source digest changed"
cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" "$FIXTURE_SEMANTIC_SVG"
assert_sources_unchanged

# A checker that changes a canonical input after the builder's initial digest
# capture must not make the changed bytes the new baseline. The fixture binds
# this deliberately hostile checker by its exact digest so the race reaches
# the post-validation source-manifest comparison.
cp "$FIXTURE_BUILDER" "$TEST_ROOT/builder-before-validation-race.sh"
cp "$FIXTURE_FIGURE_CHECK" "$TEST_ROOT/figure-check-before-validation-race.py"
printf '%s\n' \
  'from pathlib import Path' \
  'root = Path(__file__).resolve().parent.parent' \
  'target = root / "audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"' \
  'target.write_bytes(target.read_bytes() + b"\\n<!-- validation race -->\\n")' \
  >"$FIXTURE_FIGURE_CHECK"
RACE_CHECK_SHA256="$(shasum -a 256 "$FIXTURE_FIGURE_CHECK" | awk '{print $1}')"
sed "s|^FIGURE_ASSET_CHECK_SHA256=.*|FIGURE_ASSET_CHECK_SHA256=$RACE_CHECK_SHA256|" \
  "$TEST_ROOT/builder-before-validation-race.sh" >"$FIXTURE_BUILDER"
expect_mutated_source_failure \
  "canonical-source validation race" \
  "canonical sources changed during validation"
cp "$TEST_ROOT/builder-before-validation-race.sh" "$FIXTURE_BUILDER"
cp "$TEST_ROOT/figure-check-before-validation-race.py" "$FIXTURE_FIGURE_CHECK"
cp "$GUIDE_FIGURE_DIRECTORY/semantic-firewall.svg" "$FIXTURE_SEMANTIC_SVG"
assert_sources_unchanged

# Validate the exact staged bytes rather than trusting a live-source digest.
# This fake cp substitutes a different reviewed PDF only while the builder
# stages the semantic-firewall derivative. The ordered digest comparison must
# reject it before any renderer runs. A dedicated kpsewhich control returns a
# direct regular fixture path so this case reaches staging after the builder's
# intentionally earlier font-path probes.
# shellcheck disable=SC2016 # The generated fake expands this variable at runtime.
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "$PID_RS_BUILDER_TEST_FONT_CONTROL"' \
  'exit 0' >"$FAKE_BIN/kpsewhich"
chmod +x "$FAKE_BIN/kpsewhich"
# shellcheck disable=SC2016 # The generated fake expands these variables at runtime.
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'set -euo pipefail' \
  'if [[ "$#" -eq 2 && "$1" == */repository/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf && "$2" == */repository/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.pdf ]]; then' \
  '  exec "$PID_RS_BUILDER_TEST_REAL_CP" "$PID_RS_BUILDER_TEST_SUBSTITUTE_BYTES" "$2"' \
  'fi' \
  'exec "$PID_RS_BUILDER_TEST_REAL_CP" "$@"' \
  >"$FAKE_BIN/cp"
chmod +x "$FAKE_BIN/cp"
PID_RS_BUILDER_TEST_SUBSTITUTE_BYTES="$FIXTURE_RESULT_PDF"
expect_fast_failure \
  "staged derivative substitution" \
  "$TEST_ROOT/staged-substitution.pdf" \
  "staged source bytes differ from validated sources"
unset PID_RS_BUILDER_TEST_SUBSTITUTE_BYTES
rm -f -- "$FAKE_BIN/cp"
# shellcheck disable=SC2016 # The generated fake expands these variables at runtime.
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "$*" >>"$PID_RS_BUILDER_TEST_MARKER"' \
  'exit 97' >"$FAKE_BIN/kpsewhich"
chmod +x "$FAKE_BIN/kpsewhich"
assert_sources_unchanged

sed 's|/D~\\l__pidrs_tagpdf_openaction_tl|/D~[0~/Fit]|' \
  "$TAGPDF_OPENACTION_COMPAT" >"$FIXTURE_COMPAT"
cmp -s "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT" && {
  echo "Mathematical results guide builder self-test failed: wrong-page mutation was inert" >&2
  exit 1
}
expect_mutated_source_failure \
  "wrong OpenAction page target" \
  "compatibility source digest changed"
cp "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT"
assert_sources_unchanged

sed 's|__tag/struct/1|__tag/struct/2|' \
  "$TAGPDF_OPENACTION_COMPAT" >"$FIXTURE_COMPAT"
cmp -s "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT" && {
  echo "Mathematical results guide builder self-test failed: wrong-structure mutation was inert" >&2
  exit 1
}
expect_mutated_source_failure \
  "wrong OpenAction StructTreeRoot/K target" \
  "compatibility source digest changed"
cp "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT"
assert_sources_unchanged

sed 's|2024/02/23|2024/02/22|' \
  "$TAGPDF_OPENACTION_COMPAT" >"$FIXTURE_COMPAT"
cmp -s "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT" && {
  echo "Mathematical results guide builder self-test failed: version-path mutation was inert" >&2
  exit 1
}
expect_mutated_source_failure \
  "tagpdf v0.98w exclusion cutoff drift" \
  "compatibility source digest changed"
cp "$TAGPDF_OPENACTION_COMPAT" "$FIXTURE_COMPAT"
assert_sources_unchanged

expect_argument_failure \
  "cross-toolchain mode without an explicit output" \
  "usage:" \
  --cross-toolchain
mkdir -p "$FIXTURE_REPO/output/pdf"
printf '%s\n' 'canonical fixture bytes' \
  >"$FIXTURE_REPO/output/pdf/mathematical-results-guide.pdf"
expect_argument_failure \
  "cross-toolchain canonical publication" \
  "cross-toolchain mode cannot publish the canonical output" \
  --cross-toolchain "$FIXTURE_REPO/output/pdf/mathematical-results-guide.pdf"
if [[ "$(<"$FIXTURE_REPO/output/pdf/mathematical-results-guide.pdf")" \
    != "canonical fixture bytes" ]]; then
  echo "Mathematical results guide builder self-test failed: cross mode changed canonical bytes" >&2
  exit 1
fi
expect_argument_failure \
  "unknown builder mode" \
  "usage:" \
  --projected

expect_fast_failure \
  "exact source alias" \
  "$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md" \
  "output aliases canonical source"
expect_fast_failure \
  "lexically normalized source alias" \
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/../mathematical-results-guide/header.tex" \
  "output aliases canonical source"

ln -s "$FIXTURE_REPO" "$TEST_ROOT/repository-alias"
expect_fast_failure \
  "parent-symlink source alias" \
  "$TEST_ROOT/repository-alias/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg" \
  "output aliases canonical source"

ln "$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md" "$TEST_ROOT/hardlink-alias.pdf"
expect_fast_failure \
  "hard-link source alias" \
  "$TEST_ROOT/hardlink-alias.pdf" \
  "output aliases canonical source"

printf '%s\n' 'safe target' >"$TEST_ROOT/safe-target.pdf"
ln -s "$TEST_ROOT/safe-target.pdf" "$TEST_ROOT/symbolic-output.pdf"
expect_fast_failure \
  "symbolic non-source output" \
  "$TEST_ROOT/symbolic-output.pdf" \
  "output must not be symbolic"
expect_fast_failure \
  "non-PDF output" \
  "$TEST_ROOT/output.txt" \
  "output path must end in .pdf"
mkdir "$TEST_ROOT/directory.pdf"
expect_fast_failure \
  "non-regular existing output" \
  "$TEST_ROOT/directory.pdf" \
  "existing output is not a regular file"

printf '%s\n' '#!/usr/bin/env bash' 'printf "%s\n" "pandoc fixture-copy wrapper"' \
  >"$FAKE_BIN/pandoc"
chmod +x "$FAKE_BIN/pandoc"
expect_fast_failure \
  "non-Pandoc version report" \
  "$TEST_ROOT/non-pandoc-version.pdf" \
  "pandoc --version is not a recognized genuine-looking Pandoc report"

printf '%s\n' '#!/usr/bin/env bash' 'printf "%s\n" "pandoc 3.1.3"' \
  >"$FAKE_BIN/pandoc"
chmod +x "$FAKE_BIN/pandoc"
expect_fast_failure \
  "incomplete Pandoc version report" \
  "$TEST_ROOT/incomplete-pandoc-version.pdf" \
  "pandoc --version is not a recognized genuine-looking Pandoc report"

printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "pandoc 3.1.3" "Features: +lua" "User data directory: /fixture" "Copyright (C) 2006-2023 John MacFarlane"' \
  >"$FAKE_BIN/pandoc"
chmod +x "$FAKE_BIN/pandoc"
expect_fast_failure \
  "exact mode rejects the legacy writer" \
  "$TEST_ROOT/exact-legacy-writer.pdf" \
  "exact mode requires pandoc 3.10.2"
expect_argument_failure \
  "cross mode rejects an unauthenticated legacy executable" \
  "Pandoc 3.1.3 executable custody changed" \
  --cross-toolchain "$TEST_ROOT/cross-unauthenticated-legacy-writer.pdf"
write_preflight_pandoc

rm -f -- "$MARKER"
SAFE_OUTPUT="$TEST_ROOT/safe-output.pdf"
if transcript="$(
  PATH="$FAKE_BIN:$PATH" \
    PID_RS_BUILDER_TEST_MARKER="$MARKER" \
    PID_RS_PDF_TMPDIR="$RUN_TMP" \
    bash "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh" \
      "$SAFE_OUTPUT" 2>&1
)"; then
  echo "Mathematical results guide builder self-test failed: safe path passed the fake renderer" >&2
  exit 1
else
  status=$?
fi
if [[ "$status" -ne 97 || ! -s "$MARKER" ]]; then
  echo "Mathematical results guide builder self-test failed: safe path did not reach fake font discovery" >&2
  printf '%s\n' "$transcript" >&2
  exit 1
fi
if [[ -e "$SAFE_OUTPUT" ]]; then
  echo "Mathematical results guide builder self-test failed: fake build published an output" >&2
  exit 1
fi
assert_sources_unchanged
CASES=$((CASES + 1))

# Drive the completed-build comparison and publication routes with exact PDF
# fixtures. These cases exercise the builder's mode wiring without invoking a
# real TeX renderer or weakening the separate end-to-end exact build.
PAIR_CONTROL="$TEST_ROOT/pair-control.pdf"
PAIR_ID_VARIANT="$TEST_ROOT/pair-id-variant.pdf"
PAIR_OUTSIDE_VARIANT="$TEST_ROOT/pair-outside-variant.pdf"
PAIR_OVERSIZED="$TEST_ROOT/pair-oversized.pdf"
PAIR_SHARED="$TEST_ROOT/pair-shared.pdf"
PAIR_EXTRA_LINK="$TEST_ROOT/pair-extra-link.pdf"
PAIR_MODE_FILE="$TEST_ROOT/pair-mode.txt"
PAIR_FONT="$TEST_ROOT/pair-font.otf"
PAIR_RAW_TEX="$TEST_ROOT/pair-canonical-pandoc.raw.tex"
cp "$CANONICAL_GUIDE" "$PAIR_CONTROL"
cp "$CANONICAL_GUIDE" "$PAIR_SHARED"
printf '%s\n' 'fixture font bytes' >"$PAIR_FONT"
python3 -I -S -B - "$PANDOC_TEX_NORMALIZER" "$PAIR_RAW_TEX" <<'PY'
from __future__ import annotations

import ast
import pathlib
import sys


normalizer, output = map(pathlib.Path, sys.argv[1:])
required = {
    "EXPECTED_HEADING_IDS",
    "TABLE_WRAPPER",
    "LONGTABLE_BEGIN",
    "LONGTABLE_END",
    "CANONICAL_TABLE_PREAMBLE",
    "LONGTABLE_SUPPORT_PROJECTION",
    "CANONICAL_IMAGE_PREAMBLE",
    "CANONICAL_CROSSWALK",
    "CROSSWALK_FRAME_PREFIX",
    "CROSSWALK_FRAME_SUFFIX",
    "DOCUMENT_BEGIN",
    "DOCUMENT_END",
    "TOP_LEVEL_HEADING_IDS",
}
tree = ast.parse(normalizer.read_text(encoding="utf-8"), filename=str(normalizer))
values: dict[str, object] = {}
for node in tree.body:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        continue
    target = node.targets[0]
    if not isinstance(target, ast.Name) or target.id not in required:
        continue
    if (
        isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "frozenset"
        and len(node.value.args) == 1
    ):
        values[target.id] = frozenset(ast.literal_eval(node.value.args[0]))
    else:
        values[target.id] = ast.literal_eval(node.value)
if set(values) != required:
    raise SystemExit(f"completed builder fixture lost normalizer constants: {sorted(required - set(values))}")

ids = values["EXPECTED_HEADING_IDS"]
top_level = values["TOP_LEVEL_HEADING_IDS"]
parts = [
    "\\documentclass{article}\n",
    values["CANONICAL_TABLE_PREAMBLE"],
    values["LONGTABLE_SUPPORT_PROJECTION"],
    values["CANONICAL_IMAGE_PREAMBLE"],
    "\\input{mathematical-results-guide-tagpdf-openaction-compat.tex}\n",
    "\\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}\n",
    "\\AtBeginDocument{\\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}\n",
    "\\hypersetup{linkcolor=PidTeal}\n",
    values["DOCUMENT_BEGIN"],
]
for index, heading_id in enumerate(ids, start=1):
    command = "section" if heading_id in top_level else "subsection"
    parts.append(f"\\{command}{{Synthetic heading {index:02d}}}\\label{{{heading_id}}}\n")
parts.extend(
    (
        "Five distinct lanes\n",
        "Thus, SxPID3 has 18 net atoms.\n",
        "The audit evaluates 2,197,584 products per route.\n",
        "repository/publication integration remains\n",
    )
)
for index in range(1, 5):
    parts.extend(
        (
            values["TABLE_WRAPPER"],
            values["LONGTABLE_BEGIN"],
            f"synthetic-{index} & value-{index} \\\\\n",
            values["LONGTABLE_END"],
            "}\n",
        )
    )
parts.extend(
    (
        values["CROSSWALK_FRAME_PREFIX"],
        values["CANONICAL_CROSSWALK"],
        values["CROSSWALK_FRAME_SUFFIX"],
        values["DOCUMENT_END"],
    )
)
output.write_text("".join(parts), encoding="utf-8", newline="\n")
PY
python3 -I -B - "$CANONICAL_GUIDE" "$PAIR_ID_VARIANT" \
    "$PAIR_OUTSIDE_VARIANT" "$PAIR_OVERSIZED" <<'PY'
from __future__ import annotations

import pathlib
import re
import sys


source, id_path, outside_path, oversized_path = map(pathlib.Path, sys.argv[1:])
data = source.read_bytes()
pattern = re.compile(
    rb"/ID[ \t\r\n]*\[[ \t\r\n]*<([0-9A-Fa-f]{32})>[ \t\r\n]*"
    rb"<([0-9A-Fa-f]{32})>[ \t\r\n]*\]"
)
matches = list(pattern.finditer(data))
if len(matches) != 1 or matches[0].group(1).lower() != matches[0].group(2).lower():
    raise SystemExit("builder integration fixture lacks one duplicated strict trailer ID")
replacement = b"0123456789ABCDEF0123456789ABCDEF"
if matches[0].group(1).upper() == replacement:
    replacement = b"FEDCBA9876543210FEDCBA9876543210"
changed = bytearray(data)
for group in (1, 2):
    start, end = matches[0].span(group)
    changed[start:end] = replacement
id_path.write_bytes(changed)
outside = bytearray(changed)
if not outside.startswith(b"%PDF-1.7"):
    raise SystemExit("builder integration fixture has an unexpected PDF header")
outside[:8] = b"%PDF-1.6"
outside_path.write_bytes(outside)
with oversized_path.open("wb") as stream:
    stream.truncate(16 * 1024 * 1024 + 1)
PY

{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
  printf 'PAIR_FONT=%q\n' "$PAIR_FONT"
  printf '%s\n' 'printf "%s\n" "$PAIR_FONT"'
} >"$FAKE_BIN/kpsewhich"
printf '%s\n' '#!/usr/bin/env bash' 'exit 0' >"$FAKE_BIN/fc-cache"
{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
  printf 'PAIR_MODE_FILE=%q\n' "$PAIR_MODE_FILE"
  printf 'PAIR_RAW_TEX=%q\n' "$PAIR_RAW_TEX"
  printf 'REAL_CP=%q\n' "$REAL_CP"
  printf '%s\n' \
    'if [[ "$#" -eq 1 && "$1" == --version ]]; then' \
    '  printf "%s\n" "pandoc 3.10.2" "Features: +lua" "User data directory: /fixture" "Copyright (C) 2006-2026 John MacFarlane. Web: https://pandoc.org"' \
    '  exit 0' \
    'fi' \
    'mode="$(<"$PAIR_MODE_FILE")"' \
    'output=' \
    'toccolor_count=0' \
    'for argument in "$@"; do' \
    '  case "$argument" in' \
    '    --output=*) output="${argument#--output=}" ;;' \
    '    --variable=toccolor:PidTeal) toccolor_count=$((toccolor_count + 1)) ;;' \
    '  esac' \
    'done' \
    '[[ -n "$output" ]] || exit 91' \
    '[[ "$toccolor_count" -eq 1 ]] || exit 94' \
    '"$REAL_CP" "$PAIR_RAW_TEX" "$output"' \
    'case "$mode" in' \
    '  raw-missing-wiring) sed "/^\\\\input{mathematical-results-guide-tagpdf-openaction-compat[.]tex}$/d" "$output" >"$output.tmp"; mv "$output.tmp" "$output" ;;' \
    '  raw-duplicate-wiring) printf "%s\n" "\\input{mathematical-results-guide-tagpdf-openaction-compat.tex}" >>"$output" ;;' \
    '  raw-missing-filespec-wiring) sed "/^\\\\input{mathematical-results-guide-l3pdffile-filespec-f-compat[.]tex}$/d" "$output" >"$output.tmp"; mv "$output.tmp" "$output" ;;' \
    '  raw-duplicate-filespec-wiring) printf "%s\n" "\\input{mathematical-results-guide-l3pdffile-filespec-f-compat.tex}" >>"$output" ;;' \
    '  raw-missing-uri-wiring) sed "/^\\\\AtBeginDocument{\\\\input{mathematical-results-guide-hgeneric-uri-contents-compat[.]tex}}$/d" "$output" >"$output.tmp"; mv "$output.tmp" "$output" ;;' \
    '  raw-duplicate-uri-wiring) printf "%s\n" "\\AtBeginDocument{\\input{mathematical-results-guide-hgeneric-uri-contents-compat.tex}}" >>"$output" ;;' \
    '  raw-empty-toccolor) sed "s/^\\\\hypersetup{linkcolor=PidTeal}$/\\\\hypersetup{linkcolor=}/" "$output" >"$output.tmp"; mv "$output.tmp" "$output" ;;' \
    '  raw-missing-source-sentinel) sed "/^The audit evaluates 2,197,584 products per route[.]$/d" "$output" >"$output.tmp"; mv "$output.tmp" "$output" ;;' \
    'esac'
} >"$FAKE_BIN/pandoc"
{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
  printf 'PAIR_MODE_FILE=%q\n' "$PAIR_MODE_FILE"
  printf 'PAIR_CONTROL=%q\n' "$PAIR_CONTROL"
  printf 'PAIR_ID_VARIANT=%q\n' "$PAIR_ID_VARIANT"
  printf 'PAIR_OUTSIDE_VARIANT=%q\n' "$PAIR_OUTSIDE_VARIANT"
  printf 'PAIR_OVERSIZED=%q\n' "$PAIR_OVERSIZED"
  printf 'PAIR_SHARED=%q\n' "$PAIR_SHARED"
  printf 'PAIR_EXTRA_LINK=%q\n' "$PAIR_EXTRA_LINK"
  printf 'REAL_CP=%q\n' "$REAL_CP"
  printf '%s\n' \
    'mode="$(<"$PAIR_MODE_FILE")"' \
    'output_directory=' \
    'for argument in "$@"; do' \
    '  case "$argument" in --output-directory=*) output_directory="${argument#--output-directory=}" ;; esac' \
    'done' \
    '[[ -n "$output_directory" ]] || exit 92' \
    'output="$output_directory/mathematical-results-guide.pdf"' \
    'case "$output_directory" in' \
    '  */first/build) side=first ;;' \
    '  */second/build) side=second ;;' \
    '  *) exit 93 ;;' \
    'esac' \
    'case "$mode:$side" in' \
    '  id:first|outside:first|exact-different:first) artifact="$PAIR_CONTROL" ;;' \
    '  id:second|exact-different:second) artifact="$PAIR_ID_VARIANT" ;;' \
    '  outside:second) artifact="$PAIR_OUTSIDE_VARIANT" ;;' \
    '  oversized:*) artifact="$PAIR_OVERSIZED" ;;' \
    '  *) artifact="$PAIR_CONTROL" ;;' \
    'esac' \
    'case "$mode" in' \
    '  symlink) rm -f "$output"; ln -s "$artifact" "$output" ;;' \
    '  alias) rm -f "$output"; ln "$PAIR_SHARED" "$output" ;;' \
    '  first-third-link)' \
    '    "$REAL_CP" "$artifact" "$output"' \
    '    if [[ "$side" == first ]]; then rm -f "$PAIR_EXTRA_LINK"; ln "$output" "$PAIR_EXTRA_LINK"; fi ;;' \
    '  *) "$REAL_CP" "$artifact" "$output" ;;' \
    'esac' \
    'printf "%s\n" "clean fixture log" >"$output_directory/mathematical-results-guide.log"'
} >"$FAKE_BIN/lualatex"
printf '%s\n' '#!/usr/bin/env bash' \
  'printf "%s\n" "Pages:          16" "Page size:      595.276 x 841.890 pts (A4)" "Tagged:         yes"' \
  >"$FAKE_BIN/pdfinfo"
{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
  printf 'PAIR_MODE_FILE=%q\n' "$PAIR_MODE_FILE"
  printf '%s\n' \
    'mode="$(<"$PAIR_MODE_FILE")"' \
    'printf "%s\n" "name                                 type              encoding         emb sub uni object ID" "------------------------------------ ----------------- ---------------- --- --- --- ---------"' \
    'printf "%s\n" "ABCDEF+LMRoman12-Bold                CID Type 0C       Identity-H       yes yes yes      8  0"' \
    'printf "%s\n" "BCDEFG+LMRoman10-Regular             CID Type 0C       Identity-H       yes yes yes      9  0"' \
    'printf "%s\n" "CDEFGH+LMMonoLt10-Regular            CID Type 0C       Identity-H       yes yes yes     10  0"' \
    'printf "%s\n" "DEFGHI+LatinModernMath-Regular       CID Type 0C       Identity-H       yes yes yes     11  0"' \
    'printf "%s\n" "EFGHIJ+SourceSansPro-Bold            Type 1C           WinAnsi          yes yes yes     12  0"' \
    'printf "%s\n" "FGHIJK+SourceSansPro-Semibold        Type 1C           WinAnsi          yes yes yes     13  0"' \
    'printf "%s\n" "GHIJKL+SourceSansPro-Regular         Type 1C           WinAnsi          yes yes yes     14  0"' \
    'printf "%s\n" "HIJKLM+SourceSansPro-Regular         CID Type 0C       Identity-H       yes yes yes     15  0"' \
    'if [[ "$mode" != missing-figure-font ]]; then printf "%s\n" "IJKLMN+LMSans10-Bold                 Type 1C           WinAnsi          yes yes yes     16  0"; fi' \
    'printf "%s\n" "JKLMNO+LMSans10-Regular              Type 1C           WinAnsi          yes yes yes     17  0"' \
    'printf "%s\n" "KLMNOP+LMSans10-Regular              CID Type 0C       Identity-H       yes yes yes     18  0"' \
    'if [[ "$mode" == proprietary-font ]]; then printf "%s\n" "LMNOPQ+Helvetica-Bold                TrueType          WinAnsi          yes yes yes     19  0"; fi'
} >"$FAKE_BIN/pdffonts"
{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail' 'output=' \
    'for argument in "$@"; do output="$argument"; done' \
    'printf "%s\n" "Five distinct lanes" "18 net atoms" "20,348" "2,197,584" "Exact two-source categorical-Sx assurance" "Represented-binary64 and quantizer assurance" "repository/publication integration remains NO-GO" >"$output"'
} >"$FAKE_BIN/pdftotext"
{
  printf '%s\n' '#!/usr/bin/env bash' 'set -euo pipefail'
  printf 'PAIR_MODE_FILE=%q\n' "$PAIR_MODE_FILE"
  printf 'REAL_CMP=%q\n' "$REAL_CMP"
  printf '%s\n' \
    'if [[ "$(<"$PAIR_MODE_FILE")" == cmp-error && "$#" -eq 3 && "$1" == -s && "$2" == */first/build/mathematical-results-guide.pdf && "$3" == */second/build/mathematical-results-guide.pdf ]]; then' \
    '  exit 2' \
    'fi' \
    'exec "$REAL_CMP" "$@"'
} >"$FAKE_BIN/cmp"
chmod +x "$FAKE_BIN/kpsewhich" "$FAKE_BIN/fc-cache" "$FAKE_BIN/pandoc" \
  "$FAKE_BIN/lualatex" "$FAKE_BIN/pdfinfo" "$FAKE_BIN/pdffonts" \
  "$FAKE_BIN/pdftotext" "$FAKE_BIN/cmp"

CANONICAL_GUIDE_SHA256="$(shasum -a 256 "$CANONICAL_GUIDE" | awk '{print $1}')"
PAIR_BASELINE_MANIFEST="$(
  shasum -a 256 "$PAIR_CONTROL" "$PAIR_ID_VARIANT" "$PAIR_OUTSIDE_VARIANT" \
    "$PAIR_OVERSIZED" "$PAIR_SHARED" "$PAIR_FONT" "$PAIR_RAW_TEX"
)"
assert_completed_fixture_custody() {
  if ! cmp -s "$BUILDER" "$FIXTURE_BUILDER"; then
    echo "Mathematical results guide builder self-test failed: completed harness builder bytes changed" >&2
    exit 1
  fi
  if [[ "$(shasum -a 256 "$CANONICAL_GUIDE" | awk '{print $1}')" \
      != "$CANONICAL_GUIDE_SHA256" ]]; then
    echo "Mathematical results guide builder self-test failed: canonical guide bytes changed" >&2
    exit 1
  fi
  if [[ "$(
    shasum -a 256 "$PAIR_CONTROL" "$PAIR_ID_VARIANT" "$PAIR_OUTSIDE_VARIANT" \
      "$PAIR_OVERSIZED" "$PAIR_SHARED" "$PAIR_FONT" "$PAIR_RAW_TEX"
  )" != "$PAIR_BASELINE_MANIFEST" ]]; then
    echo "Mathematical results guide builder self-test failed: completed harness fixture bytes changed" >&2
    exit 1
  fi
}
assert_completed_fixture_custody

run_completed_builder() {
  local expectation="$1"
  local name="$2"
  local builder_mode="$3"
  local pair_mode="$4"
  local expected_message="${5:-}"
  local output="$TEST_ROOT/completed-$CASES.pdf"
  local transcript status
  printf '%s\n' "$pair_mode" >"$PAIR_MODE_FILE"
  rm -f -- "$PAIR_EXTRA_LINK" "$output"
  if transcript="$(
    PATH="$FAKE_BIN:$PATH" \
      PID_RS_PDF_TMPDIR="$RUN_TMP" \
      bash "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh" \
        "$builder_mode" "$output" 2>&1
  )"; then
    status=0
  else
    status=$?
  fi
  if [[ "$expectation" == pass ]]; then
    if [[ "$status" -ne 0 || ! -f "$output" || -L "$output" \
        || ! "$transcript" =~ OK:\ built ]]; then
      echo "Mathematical results guide builder self-test failed: $name did not pass" >&2
      printf '%s\n' "$transcript" >&2
      exit 1
    fi
    if ! "$REAL_CMP" -s "$PAIR_CONTROL" "$output"; then
      echo "Mathematical results guide builder self-test failed: $name published unexpected bytes" >&2
      exit 1
    fi
  else
    if [[ "$status" -eq 0 || ! "$transcript" =~ $expected_message || -e "$output" ]]; then
      echo "Mathematical results guide builder self-test failed: $name had an unexpected disposition" >&2
      printf '%s\n' "$transcript" >&2
      exit 1
    fi
  fi
  rm -f -- "$PAIR_EXTRA_LINK" "$output"
  assert_sources_unchanged
  CASES=$((CASES + 1))
}

run_completed_builder pass "exact raw-equality route" --exact equal
run_completed_builder pass "cross raw-equality route" --cross-toolchain equal
run_completed_builder pass "cross strict trailer-ID route" --cross-toolchain id
run_completed_builder fail "stale raw TeX omits compatibility wiring" \
  --exact raw-missing-wiring \
  "Pandoc raw TeX does not contain exactly one tagpdf compatibility input"
run_completed_builder fail "raw TeX duplicates compatibility wiring" \
  --exact raw-duplicate-wiring \
  "Pandoc raw TeX does not contain exactly one tagpdf compatibility input"
run_completed_builder fail "raw TeX omits URI-Contents compatibility wiring" \
  --exact raw-missing-uri-wiring \
  "Pandoc raw TeX does not contain exactly one hgeneric URI-Contents compatibility input"
run_completed_builder fail "raw TeX duplicates URI-Contents compatibility wiring" \
  --exact raw-duplicate-uri-wiring \
  "Pandoc raw TeX does not contain exactly one hgeneric URI-Contents compatibility input"
run_completed_builder fail "raw TeX omits file-specification compatibility wiring" \
  --exact raw-missing-filespec-wiring \
  "Pandoc raw TeX does not contain exactly one l3pdffile file-specification compatibility input"
run_completed_builder fail "raw TeX duplicates file-specification compatibility wiring" \
  --exact raw-duplicate-filespec-wiring \
  "Pandoc raw TeX does not contain exactly one l3pdffile file-specification compatibility input"
run_completed_builder fail "raw TeX omits a current source sentinel" \
  --exact raw-missing-source-sentinel \
  "Pandoc raw TeX source sentinel must occur exactly once"
run_completed_builder fail "raw TeX carries an empty TOC link color" \
  --exact raw-empty-toccolor \
  "Pandoc raw TeX has an empty or unexpected table-of-contents link color"
run_completed_builder fail "proprietary final font program" --exact proprietary-font \
  "uses a non-contract face: Helvetica-Bold"
run_completed_builder fail "missing canonical-figure font face" --exact missing-figure-font \
  "required canonical-figure faces are absent: LMSans10-Bold"
run_completed_builder fail "exact mode rejects trailer-ID variance" --exact exact-different \
  "repeated builds differ"
run_completed_builder fail "cross mode rejects outside-ID drift" --cross-toolchain outside \
  "differ beyond the strict trailer-ID projection"
run_completed_builder fail "cmp operational error" --exact cmp-error \
  "repeated-build cmp had operational status 2"
run_completed_builder fail "symbolic build outputs" --exact symlink \
  "repeated-build output custody check failed"
run_completed_builder fail "aliased build outputs" --exact alias \
  "repeated-build output custody check failed"
run_completed_builder fail "third-path hard link" --exact first-third-link \
  "repeated-build output custody check failed"
run_completed_builder fail "oversized build outputs" --exact oversized \
  "repeated-build output custody check failed"
assert_completed_fixture_custody

cp "$FIXTURE_BUILDER" "$TEST_ROOT/builder-before-staged-normalizer-race.sh"
cp "$FIXTURE_PANDOC_TEX_NORMALIZER" "$TEST_ROOT/normalizer-before-staged-normalizer-race.py"
python3 -I -B - "$FIXTURE_PANDOC_TEX_NORMALIZER" <<'PY'
from __future__ import annotations

import pathlib
import sys


path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = '    print(\n        "OK: normalized mathematical-results guide Pandoc TeX "\n'
payload = (
    '    _self = pathlib.Path(__file__)\n'
    '    _self.write_bytes(_self.read_bytes() + b"\\n# staged normalizer use race\\n")\n'
)
if source.count(needle) != 1:
    raise SystemExit("cannot locate staged-normalizer mutation anchor")
path.write_text(source.replace(needle, payload + needle), encoding="utf-8")
PY
HOSTILE_NORMALIZER_SHA256="$(shasum -a 256 "$FIXTURE_PANDOC_TEX_NORMALIZER" | awk '{print $1}')"
sed "s|^PANDOC_TEX_NORMALIZER_SHA256=.*|PANDOC_TEX_NORMALIZER_SHA256=$HOSTILE_NORMALIZER_SHA256|" \
  "$TEST_ROOT/builder-before-staged-normalizer-race.sh" >"$FIXTURE_BUILDER"
NORMALIZER_BASELINE_MANIFEST="$BASELINE_MANIFEST"
BASELINE_MANIFEST="$(source_manifest)"
run_completed_builder fail "staged Pandoc TeX normalizer mutation during use" --exact equal \
  "staged Pandoc TeX normalizer changed during execution"
cp "$TEST_ROOT/builder-before-staged-normalizer-race.sh" "$FIXTURE_BUILDER"
cp "$TEST_ROOT/normalizer-before-staged-normalizer-race.py" "$FIXTURE_PANDOC_TEX_NORMALIZER"
BASELINE_MANIFEST="$NORMALIZER_BASELINE_MANIFEST"
assert_sources_unchanged
assert_completed_fixture_custody

cp "$FIXTURE_BUILDER" "$TEST_ROOT/builder-before-staged-checker-race.sh"
cp "$FIXTURE_ID_VARIANCE_CHECK" "$TEST_ROOT/id-checker-before-staged-checker-race.py"
python3 -I -B - "$FIXTURE_ID_VARIANCE_CHECK" <<'PY'
from __future__ import annotations

import pathlib
import sys


path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = 'if __name__ == "__main__":\n'
payload = (
    'if "--validate-inputs" in sys.argv:\n'
    '    _self = pathlib.Path(__file__)\n'
    '    _self.write_bytes(_self.read_bytes() + b"\\n# staged use race\\n")\n\n'
)
if source.count(needle) != 1:
    raise SystemExit("cannot locate staged-checker mutation anchor")
path.write_text(source.replace(needle, payload + needle), encoding="utf-8")
PY
HOSTILE_ID_CHECK_SHA256="$(shasum -a 256 "$FIXTURE_ID_VARIANCE_CHECK" | awk '{print $1}')"
sed "s|^ID_VARIANCE_CHECK_SHA256=.*|ID_VARIANCE_CHECK_SHA256=$HOSTILE_ID_CHECK_SHA256|" \
  "$TEST_ROOT/builder-before-staged-checker-race.sh" >"$FIXTURE_BUILDER"
ORIGINAL_BASELINE_MANIFEST="$BASELINE_MANIFEST"
BASELINE_MANIFEST="$(source_manifest)"
run_completed_builder fail "staged trailer-ID checker mutation during use" --exact equal \
  "staged trailer-ID variance checker digest changed"
cp "$TEST_ROOT/builder-before-staged-checker-race.sh" "$FIXTURE_BUILDER"
cp "$TEST_ROOT/id-checker-before-staged-checker-race.py" "$FIXTURE_ID_VARIANCE_CHECK"
BASELINE_MANIFEST="$ORIGINAL_BASELINE_MANIFEST"
assert_sources_unchanged
assert_completed_fixture_custody

python3 -I -B - "$FIXTURE_ID_VARIANCE_CHECK" <<'PY'
from __future__ import annotations

import pathlib
import sys


path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = 'if __name__ == "__main__":\n'
payload = (
    'if "--validate-inputs" not in sys.argv and len(sys.argv) == 3:\n'
    '    _self = pathlib.Path(__file__)\n'
    '    _self.write_bytes(_self.read_bytes() + b"\\n# staged projection race\\n")\n\n'
)
if source.count(needle) != 1:
    raise SystemExit("cannot locate staged-projection mutation anchor")
path.write_text(source.replace(needle, payload + needle), encoding="utf-8")
PY
HOSTILE_ID_CHECK_SHA256="$(shasum -a 256 "$FIXTURE_ID_VARIANCE_CHECK" | awk '{print $1}')"
sed "s|^ID_VARIANCE_CHECK_SHA256=.*|ID_VARIANCE_CHECK_SHA256=$HOSTILE_ID_CHECK_SHA256|" \
  "$TEST_ROOT/builder-before-staged-checker-race.sh" >"$FIXTURE_BUILDER"
BASELINE_MANIFEST="$(source_manifest)"
run_completed_builder fail "staged trailer-ID checker mutation during projection" \
  --cross-toolchain id "staged trailer-ID variance checker digest changed"
cp "$TEST_ROOT/builder-before-staged-checker-race.sh" "$FIXTURE_BUILDER"
cp "$TEST_ROOT/id-checker-before-staged-checker-race.py" "$FIXTURE_ID_VARIANCE_CHECK"
BASELINE_MANIFEST="$ORIGINAL_BASELINE_MANIFEST"
assert_sources_unchanged
assert_completed_fixture_custody

cp "$FIXTURE_BUILDER" "$TEST_ROOT/builder-before-staged-font-checker-race.sh"
cp "$FIXTURE_FONT_ROSTER_CHECK" "$TEST_ROOT/font-checker-before-staged-checker-race.py"
python3 -I -B - "$FIXTURE_FONT_ROSTER_CHECK" <<'PY'
from __future__ import annotations

import pathlib
import sys


path = pathlib.Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = 'if __name__ == "__main__":\n'
payload = (
    'if len(sys.argv) == 2:\n'
    '    _self = pathlib.Path(__file__)\n'
    '    _self.write_bytes(_self.read_bytes() + b"\\n# staged font use race\\n")\n\n'
)
if source.count(needle) != 1:
    raise SystemExit("cannot locate staged font-checker mutation anchor")
path.write_text(source.replace(needle, payload + needle), encoding="utf-8")
PY
HOSTILE_FONT_CHECK_SHA256="$(shasum -a 256 "$FIXTURE_FONT_ROSTER_CHECK" | awk '{print $1}')"
sed "s|^FONT_ROSTER_CHECK_SHA256=.*|FONT_ROSTER_CHECK_SHA256=$HOSTILE_FONT_CHECK_SHA256|" \
  "$TEST_ROOT/builder-before-staged-font-checker-race.sh" >"$FIXTURE_BUILDER"
BASELINE_MANIFEST="$(source_manifest)"
run_completed_builder fail "staged final font-roster checker mutation during use" \
  --exact equal "staged final font-roster checker digest changed"
cp "$TEST_ROOT/builder-before-staged-font-checker-race.sh" "$FIXTURE_BUILDER"
cp "$TEST_ROOT/font-checker-before-staged-checker-race.py" "$FIXTURE_FONT_ROSTER_CHECK"
BASELINE_MANIFEST="$ORIGINAL_BASELINE_MANIFEST"
assert_sources_unchanged
assert_completed_fixture_custody

echo "Mathematical results guide builder self-test passed: $CASES hostile/control cases."
echo "Unsafe destinations failed before font discovery; staged substitution failed before rendering."
echo "Pandoc version-report shape, raw-TeX compatibility/source wiring, and TOC color failed closed."
echo "Every fixture source hash stayed unchanged."
