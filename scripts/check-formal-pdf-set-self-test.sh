#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PRODUCTION_GATE="$ROOT/scripts/check-formal-pdf-set.sh"
CHECK_NAME="formal PDF typed-inventory self-test"

for command_name in bash basename cat chmod cp find grep ln mkdir mktemp mv rm sort; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  fi
done
if [[ ! -f "$PRODUCTION_GATE" || -L "$PRODUCTION_GATE" ]]; then
  echo "$CHECK_NAME: production gate is absent or symbolic" >&2
  exit 2
fi

TMP_ROOT_INPUT="${TMPDIR:-/tmp}"
if [[ ! -d "$TMP_ROOT_INPUT" ]]; then
  echo "$CHECK_NAME: temporary root is not a directory" >&2
  exit 2
fi
TMP_ROOT="$(cd "$TMP_ROOT_INPUT" && pwd -P)"
if [[ "$TMP_ROOT" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
TEST_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-formal-pdf-set-self-test.XXXXXX")"
TEST_ROOT="$(cd "$TEST_ROOT" && pwd -P)"
cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$TEST_ROOT" in
    "$TMP_ROOT"/pid-rs-formal-pdf-set-self-test.*) rm -rf -- "$TEST_ROOT" ;;
    *)
      echo "$CHECK_NAME: refusing to clean an unexpected path: $TEST_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

STANDALONE=(
  certified-sxpid2-executable-assurance
  dependency-colored-sxpid-concentration
  ecosystem-compatibility-audit
  exact-log-product-sxpid2-assurance
  finite-alphabet-plugin-convergence
  formal-tool-adoption-audit
  foundational-shared-exclusions-pid-audit
  ksg-m1a-composite-v4-process
  ksg-m1a-composite-v5-boundary
  ksg-m1a-composite-v6-boundary
  ksg-m1a-composite-v7-boundary
  mathematical-problem-solving-workflow
  support-change-tolerant-averaged-sxpid-continuity
  two-source-sxpid-count-atom-bridge
)
FRAGMENT=pid-discovery-verification-and-durability-blueprint-header

make_fixture() {
  local fixture="$1"
  local stem
  mkdir -p "$fixture/scripts" "$fixture/audit/formal/latex" "$fixture/output/pdf"
  cp "$PRODUCTION_GATE" "$fixture/scripts/check-formal-pdf-set.sh"
  chmod 0755 "$fixture/scripts/check-formal-pdf-set.sh"
  for stem in "${STANDALONE[@]}"; do
    cp "$ROOT/audit/formal/latex/$stem.tex" "$fixture/audit/formal/latex/$stem.tex"
    cp "$ROOT/output/pdf/$stem.pdf" "$fixture/output/pdf/$stem.pdf"
  done
  cp "$ROOT/audit/formal/latex/$FRAGMENT.tex" \
    "$fixture/audit/formal/latex/$FRAGMENT.tex"
}

run_inventory() {
  local fixture="$1"
  (cd "$fixture" && "$fixture/scripts/check-formal-pdf-set.sh" --inventory-only)
}

PASS_COUNT=0
pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'ok %d - %s\n' "$PASS_COUNT" "$1"
}

expect_success() {
  local label="$1"
  local fixture="$2"
  local stdout="$TEST_ROOT/success-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/success-$PASS_COUNT.stderr"
  if ! run_inventory "$fixture" >"$stdout" 2>"$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label failed" >&2
    return 1
  fi
  if [[ -s "$stderr" ]] || ! grep -Fq \
      "standalone-paper, renderer-fragment, and PDF inventories are exact" "$stdout"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label did not emit the expected success contract" >&2
    return 1
  fi
  pass "$label"
}

expect_failure() {
  local label="$1"
  local fixture="$2"
  local expected="$3"
  local stdout="$TEST_ROOT/failure-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/failure-$PASS_COUNT.stderr"
  if run_inventory "$fixture" >"$stdout" 2>"$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label was accepted" >&2
    return 1
  fi
  if ! grep -Fq -- "$expected" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label failed for a noncausal reason" >&2
    return 1
  fi
  pass "$label"
}

fixture="$TEST_ROOT/baseline"
make_fixture "$fixture"
expect_success "declared source-typed inventory is accepted" "$fixture"

fixture="$TEST_ROOT/missing-fragment"
make_fixture "$fixture"
mv "$fixture/audit/formal/latex/$FRAGMENT.tex" "$fixture/removed-fragment.tex"
expect_failure "missing renderer fragment is rejected" "$fixture" \
  "typed TeX source inventory differs"

fixture="$TEST_ROOT/extra-tex"
make_fixture "$fixture"
cp "$fixture/audit/formal/latex/$FRAGMENT.tex" \
  "$fixture/audit/formal/latex/unexpected-helper.tex"
expect_failure "unexpected TeX source is rejected" "$fixture" \
  "typed TeX source inventory differs"

fixture="$TEST_ROOT/symbolic-tex"
make_fixture "$fixture"
mv "$fixture/audit/formal/latex/$FRAGMENT.tex" "$fixture/fragment-target.tex"
ln -s ../../../fragment-target.tex "$fixture/audit/formal/latex/$FRAGMENT.tex"
expect_failure "symbolic TeX source is rejected" "$fixture" \
  "TeX inventory entry is not a direct regular file"

fixture="$TEST_ROOT/missing-pdf"
make_fixture "$fixture"
mv "$fixture/output/pdf/${STANDALONE[0]}.pdf" "$fixture/removed-paper.pdf"
expect_failure "missing standalone-paper PDF is rejected" "$fixture" \
  "rendered PDF inventory differs"

fixture="$TEST_ROOT/extra-pdf"
make_fixture "$fixture"
cp "$fixture/output/pdf/${STANDALONE[0]}.pdf" "$fixture/output/pdf/unexpected.pdf"
expect_failure "unexpected PDF is rejected" "$fixture" \
  "rendered PDF inventory differs"

fixture="$TEST_ROOT/symbolic-pdf"
make_fixture "$fixture"
mv "$fixture/output/pdf/${STANDALONE[0]}.pdf" "$fixture/paper-target.pdf"
ln -s ../../paper-target.pdf "$fixture/output/pdf/${STANDALONE[0]}.pdf"
expect_failure "symbolic PDF is rejected" "$fixture" \
  "PDF inventory entry is not a direct regular file"

fixture="$TEST_ROOT/nonregular-pdf"
make_fixture "$fixture"
mkdir "$fixture/output/pdf/unexpected-directory.pdf"
expect_failure "nonregular PDF inventory entry is rejected" "$fixture" \
  "PDF inventory entry is not a direct regular file"

echo "OK: $PASS_COUNT formal-PDF typed-inventory controls passed"
