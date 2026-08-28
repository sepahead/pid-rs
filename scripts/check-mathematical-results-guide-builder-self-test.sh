#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-mathematical-results-guide-pdf.sh"

for command_name in bash chmod cmp cp grep ln mkdir mktemp rm shasum; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "Mathematical results guide builder self-test failed: missing command: $command_name" >&2
    exit 1
  fi
done
if [[ ! -f "$BUILDER" || -L "$BUILDER" ]]; then
  echo "Mathematical results guide builder self-test failed: builder is absent, non-regular, or symbolic" >&2
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
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide" \
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit" \
  "$FAKE_BIN" "$RUN_TMP"
cp "$BUILDER" "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh"
chmod +x "$FIXTURE_REPO/scripts/build-mathematical-results-guide-pdf.sh"

printf '%s\n' '# Fixture guide' >"$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md"
printf '%s\n' '% fixture header' \
  >"$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/header.tex"
printf '%s\n' 'return {}' \
  >"$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/filter.lua"
printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg"/>' \
  >"$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"
printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg"/>' \
  >"$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg"
printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg"/>' \
  >"$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg"

# shellcheck disable=SC2016 # The generated fake expands these variables at runtime.
printf '%s\n' \
  '#!/usr/bin/env bash' \
  'printf "%s\n" "$*" >>"$PID_RS_BUILDER_TEST_MARKER"' \
  'exit 97' >"$FAKE_BIN/kpsewhich"
chmod +x "$FAKE_BIN/kpsewhich"
for command_name in fc-cache lualatex pandoc pdffonts pdfinfo pdftotext rsvg-convert; do
  printf '%s\n' '#!/usr/bin/env bash' 'exit 98' >"$FAKE_BIN/$command_name"
  chmod +x "$FAKE_BIN/$command_name"
done

required_sources=(
  "$FIXTURE_REPO/MATHEMATICAL_RESULTS_GUIDE.md"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/header.tex"
  "$FIXTURE_REPO/audit/formal/latex/mathematical-results-guide/filter.lua"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg"
  "$FIXTURE_REPO/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg"
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

echo "Mathematical results guide builder self-test passed: $CASES hostile/control cases."
echo "All unsafe outputs failed before font discovery, and every fixture source hash stayed unchanged."
