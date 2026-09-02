#!/usr/bin/env bash
# Hostile controls for the exact-only post-publication custody PDF gate.
#
# The accepted fixture uses the real reviewed PDF and real profile tools, but a
# constant-byte fixture builder.  Source-contract mutations cover bypasses that
# would otherwise require another pair of full Pandoc/LaTeX builds per case.
# Hostile shell fragments below are intentionally single-quoted data.
# shellcheck disable=SC2016
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
CHECKER="$ROOT/scripts/check-post-publication-custody-pdf.sh"
BUILDER="$ROOT/scripts/build-post-publication-custody-pdf.sh"
RECORD_CHECKER="$ROOT/scripts/check-post-publication-custody.py"
COMMITTED="$ROOT/output/pdf/post-publication-custody-2026-09-02.pdf"
VISUAL_RECEIPT="$ROOT/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md"
CHECK_NAME="post-publication custody PDF check self-test"

for command_name in awk bash cat chmod cmp cp env grep ln mkdir mktemp python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
for path in "$CHECKER" "$BUILDER" "$RECORD_CHECKER" "$COMMITTED" "$VISUAL_RECEIPT"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required production input is absent, non-regular, or symbolic: $path" >&2
    exit 2
  fi
done

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
if [[ ! -d "$TMP_BASE_INPUT" ]] \
    || ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "$CHECK_NAME: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
TEST_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-custody-pdf-self-test.XXXXXX")"
TEST_ROOT="$(CDPATH='' cd -- "$TEST_ROOT" && pwd -P)"
CHECKER_TMP="$TEST_ROOT/checker-tmp"
mkdir "$CHECKER_TMP"

cleanup() {
  local status="$1"
  trap - EXIT HUP INT TERM
  case "$TEST_ROOT" in
    "$TMP_BASE"/pid-rs-custody-pdf-self-test.*) rm -rf -- "$TEST_ROOT" || status=1 ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $TEST_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 129' HUP
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

PASS_COUNT=0
POSITIVE_COUNT=0
HOSTILE_COUNT=0
CONTRACT_COUNT=0

pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'ok %d - %s\n' "$PASS_COUNT" "$1"
}

replace_once() {
  local path="$1" before="$2" after="$3"
  python3 -I -S - "$path" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2]
after = sys.argv[3]
text = path.read_text(encoding="utf-8")
count = text.count(before)
if count != 1:
    raise SystemExit(
        f"mutation anchor count is {count}, expected one: {before!r}"
    )
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
}

validate_checker_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import re
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()

required_lines = (
    "set -euo pipefail",
    'MODE="${1:---exact}"',
    'if [[ "$#" -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then',
    'for path in "$BUILDER" "$RECORD_CHECKER" "$COMMITTED" "$VISUAL_RECEIPT"; do',
    '  if [[ ! -f "$path" || -L "$path" ]]; then',
    '  observed="$(shasum -a 256 "$path" | awk \'{print $1}\')"',
    '  count="$(grep -Fxc -- "$literal" "$VISUAL_RECEIPT" || true)"',
    'require_sha256 "$VISUAL_RECEIPT" "$VISUAL_RECEIPT_SHA256" \\',
    'require_sha256 "$COMMITTED" "$VISUAL_RECEIPT_PDF_SHA256" \\',
    '  "schema: \\`pid-rs/post-publication-custody-visual-review/v1\\`" \\',
    '  "subject: \\`output/pdf/post-publication-custody-2026-09-02.pdf\\`" \\',
    'require_unique_line "pdf_sha256: \\`$VISUAL_RECEIPT_PDF_SHA256\\`" \\',
    'require_unique_line "pages: \\`6\\`" "visual-review receipt page scope"',
    'require_unique_line "color_144_dpi_pages_reviewed: \\`1-6\\`" \\',
    'require_unique_line "grayscale_120_dpi_pages_reviewed: \\`1-6\\`" \\',
    'require_unique_line "lens_count: \\`20\\`" "visual-review receipt lens count"',
    'require_unique_line "status: \\`passed\\`" "visual-review receipt disposition"',
    'python3 -I -S -B "$RECORD_CHECKER"',
    'python3 -O -I -S -B "$RECORD_CHECKER"',
    'TMP_BASE="$(CDPATH=\'\' cd -- "$TMP_BASE_INPUT" && pwd -P)"',
    'if [[ "$TMP_BASE" == "/" ]]; then',
    'BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-custody-pdf-check.XXXXXX")"',
    '    "$TMP_BASE"/pid-rs-custody-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;',
    '  exit "$status"',
    'trap \'cleanup "$?"\' EXIT',
    'trap \'cleanup 129\' HUP',
    'trap \'cleanup 130\' INT',
    'trap \'cleanup 143\' TERM',
    'TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$FIRST" >"$BUILD_ROOT/first.stdout" 2>"$BUILD_ROOT/first.stderr"',
    'TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$SECOND" >"$BUILD_ROOT/second.stdout" 2>"$BUILD_ROOT/second.stderr"',
    'if [[ -s "$BUILD_ROOT/first.stderr" || -s "$BUILD_ROOT/second.stderr" ]]; then',
    'cmp -s "$FIRST" "$SECOND" || {',
    'cmp -s "$FIRST" "$COMMITTED" || {',
    'LC_ALL=C pdfinfo "$COMMITTED" >"$BUILD_ROOT/pdfinfo"',
    'LC_ALL=C pdffonts "$COMMITTED" >"$BUILD_ROOT/pdffonts"',
    "if ! grep -Eq '^Page size:[[:space:]]+595\\.[0-9]+ x 841\\.[0-9]+ pts \\(A4\\)$' \"$BUILD_ROOT/pdfinfo\"; then",
    "if ! grep -Eq '^PDF version:[[:space:]]+1\\.7$' \"$BUILD_ROOT/pdfinfo\"; then",
    '  { seen = 1; if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1 }',
    '  END { exit (!seen || bad) }',
    'echo "OK: custody receipt is a reproducible $pages-page A4 PDF 1.7 artifact with embedded fonts and bounded HTTPS actions"',
)
for line in required_lines:
    if lines.count(line) != 1:
        raise SystemExit(f"checker contract line drifted: {line!r}")

required_blocks = (
    '''if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi
''',
    '''cleanup() {
  local status="$1"
  trap - EXIT HUP INT TERM
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-custody-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
''',
    '''for metadata in \\
    '^Tagged:[[:space:]]+no$' \\
    '^Form:[[:space:]]+none$' \\
    '^JavaScript:[[:space:]]+no$' \\
    '^Encrypted:[[:space:]]+no$'; do
''',
    '''if [[ -s "$BUILD_ROOT/first.stderr" || -s "$BUILD_ROOT/second.stderr" ]]; then
  cat "$BUILD_ROOT/first.stderr" "$BUILD_ROOT/second.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi
''',
)
for block in required_blocks:
    if text.count(block) != 1:
        raise SystemExit(f"checker contract block drifted: {block.splitlines()[0]!r}")

for variable in ("VISUAL_RECEIPT_SHA256", "VISUAL_RECEIPT_PDF_SHA256"):
    match = re.search(rf'^{variable}="([0-9a-f]{{64}})"$', text, re.MULTILINE)
    if match is None:
        raise SystemExit(f"checker digest binding drifted: {variable}")

ordered = (
    'require_sha256 "$VISUAL_RECEIPT"',
    'python3 -I -S -B "$RECORD_CHECKER"',
    'BUILD_ROOT="$(mktemp -d',
    'TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$FIRST"',
    'TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$SECOND"',
    'if [[ -s "$BUILD_ROOT/first.stderr"',
    'cmp -s "$FIRST" "$SECOND"',
    'cmp -s "$FIRST" "$COMMITTED"',
    'LC_ALL=C pdfinfo "$COMMITTED"',
    "if ! grep -Eq '^Page size:",
    "if ! grep -Eq '^PDF version:",
    "if ! awk '",
    'echo "OK: custody receipt is a reproducible',
)
positions = [text.index(item) for item in ordered]
if positions != sorted(positions):
    raise SystemExit("checker evidence/build/comparison/profile order drifted")
PY
}

run_contract_mutation() {
  local label="$1" before="$2" after="$3"
  local mutant="$TEST_ROOT/checker-contract-$PASS_COUNT.sh"
  cp "$CHECKER" "$mutant"
  replace_once "$mutant" "$before" "$after"
  if validate_checker_contract "$mutant" \
      >"$mutant.stdout" 2>"$mutant.stderr"; then
    echo "$CHECK_NAME: checker contract mutation was accepted: $label" >&2
    exit 1
  fi
  CONTRACT_COUNT=$((CONTRACT_COUNT + 1))
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

make_fixture() {
  local fixture="$1"
  mkdir -p "$fixture/scripts" "$fixture/output/pdf" "$fixture/audit/evidence"
  cp "$CHECKER" "$fixture/scripts/check-post-publication-custody-pdf.sh"
  cp "$COMMITTED" "$fixture/output/pdf/post-publication-custody-2026-09-02.pdf"
  cp "$COMMITTED" "$fixture/expected-builder-output.pdf"
  cp "$VISUAL_RECEIPT" "$fixture/audit/evidence/"

  cat >"$fixture/scripts/check-post-publication-custody.py" <<'PY'
#!/usr/bin/env python3
import os
import sys


if os.environ.get("FIXTURE_RECORD_OPT_FAIL") == "1" and sys.flags.optimize:
    print("fixture record checker rejected optimized mode", file=sys.stderr)
    raise SystemExit(1)
print("OK: fixture record checker")
PY

  cat >"$fixture/scripts/build-post-publication-custody-pdf.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ "$#" -ne 1 ]]; then
  echo "fixture builder: expected one output path" >&2
  exit 2
fi
printf '%s\n' "${1##*/}" >>"$ROOT/builder-invocations.log"
cp "$ROOT/expected-builder-output.pdf" "$1"
case "${FIXTURE_BUILDER_MODE:-copy}" in
  copy) ;;
  stderr) echo "fixture builder diagnostic on stderr" >&2 ;;
  second-drift)
    if [[ "${1##*/}" == "second.pdf" ]]; then
      printf '\n%% fixture second-build drift\n' >>"$1"
    fi
    ;;
  *)
    echo "fixture builder: unknown mode" >&2
    exit 2
    ;;
esac
printf 'OK: fixture builder copied reviewed bytes\n'
SH
  chmod 0755 \
    "$fixture/scripts/check-post-publication-custody-pdf.sh" \
    "$fixture/scripts/build-post-publication-custody-pdf.sh" \
    "$fixture/scripts/check-post-publication-custody.py"
}

assert_checker_tmp_empty() {
  local label="$1"
  if compgen -G "$CHECKER_TMP/pid-rs-custody-pdf-check.*" >/dev/null; then
    echo "$CHECK_NAME: checker temporary directory survived: $label" >&2
    return 1
  fi
}

run_checker() {
  local fixture="$1" mode="$2" stdout="$3" stderr="$4"
  shift 4
  env TMPDIR="$CHECKER_TMP/" "$@" bash --noprofile --norc \
    "$fixture/scripts/check-post-publication-custody-pdf.sh" "$mode" \
    >"$stdout" 2>"$stderr"
}

expect_success() {
  local fixture="$1" label="$2"
  local stdout="$fixture/success.stdout" stderr="$fixture/success.stderr"
  if ! run_checker "$fixture" --exact "$stdout" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: accepted fixture failed: $label" >&2
    exit 1
  fi
  if [[ -s "$stderr" ]] \
      || ! grep -Fq \
        'OK: custody receipt is a reproducible 6-page A4 PDF 1.7 artifact with embedded fonts and bounded HTTPS actions' \
        "$stdout"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: accepted fixture lacks the exact success contract: $label" >&2
    exit 1
  fi
  if [[ "$(awk 'END { print NR }' "$fixture/builder-invocations.log")" != "2" ]]; then
    echo "$CHECK_NAME: accepted fixture did not invoke exactly two isolated builds: $label" >&2
    exit 1
  fi
  assert_checker_tmp_empty "$label"
  POSITIVE_COUNT=$((POSITIVE_COUNT + 1))
  pass "$label"
}

expect_failure() {
  local fixture="$1" mode="$2" expected_status="$3" needle="$4" label="$5"
  shift 5
  local stdout="$fixture/failure.stdout" stderr="$fixture/failure.stderr"
  local observed=0
  if run_checker "$fixture" "$mode" "$stdout" "$stderr" "$@"; then
    observed=0
  else
    observed=$?
  fi
  if [[ "$observed" -ne "$expected_status" ]] || ! grep -Fq -- "$needle" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: hostile fixture returned $observed, expected $expected_status for the causal diagnostic: $label" >&2
    exit 1
  fi
  assert_checker_tmp_empty "$label"
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

expect_invocation_failure() {
  local fixture="$1" expected_status="$2" needle="$3" label="$4"
  shift 4
  local stdout="$fixture/invocation.stdout" stderr="$fixture/invocation.stderr"
  local observed=0
  if env TMPDIR="$CHECKER_TMP/" bash --noprofile --norc \
      "$fixture/scripts/check-post-publication-custody-pdf.sh" "$@" \
      >"$stdout" 2>"$stderr"; then
    observed=0
  else
    observed=$?
  fi
  if [[ "$observed" -ne "$expected_status" ]] || ! grep -Fq -- "$needle" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: invocation control returned $observed, expected $expected_status: $label" >&2
    exit 1
  fi
  assert_checker_tmp_empty "$label"
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

reseal_visual_receipt() {
  local fixture="$1"
  local checker="$fixture/scripts/check-post-publication-custody-pdf.sh"
  local receipt="$fixture/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md"
  local old_digest new_digest
  old_digest="$(awk -F'"' '/^VISUAL_RECEIPT_SHA256=/ {print $2}' "$checker")"
  new_digest="$(shasum -a 256 "$receipt" | awk '{print $1}')"
  if [[ ! "$old_digest" =~ ^[0-9a-f]{64}$ || ! "$new_digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$CHECK_NAME: cannot reseal fixture visual receipt" >&2
    exit 1
  fi
  replace_once "$checker" \
    "VISUAL_RECEIPT_SHA256=\"$old_digest\"" \
    "VISUAL_RECEIPT_SHA256=\"$new_digest\""
}

reseal_visual_pdf_binding() {
  local fixture="$1"
  local checker="$fixture/scripts/check-post-publication-custody-pdf.sh"
  local receipt="$fixture/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md"
  local pdf="$fixture/output/pdf/post-publication-custody-2026-09-02.pdf"
  local old_digest new_digest
  old_digest="$(awk -F'"' '/^VISUAL_RECEIPT_PDF_SHA256=/ {print $2}' "$checker")"
  new_digest="$(shasum -a 256 "$pdf" | awk '{print $1}')"
  if [[ ! "$old_digest" =~ ^[0-9a-f]{64}$ || ! "$new_digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$CHECK_NAME: cannot reseal fixture visual PDF binding" >&2
    exit 1
  fi
  replace_once "$checker" \
    "VISUAL_RECEIPT_PDF_SHA256=\"$old_digest\"" \
    "VISUAL_RECEIPT_PDF_SHA256=\"$new_digest\""
  replace_once "$receipt" \
    "pdf_sha256: \`$old_digest\`" \
    "pdf_sha256: \`$new_digest\`"
  reseal_visual_receipt "$fixture"
}

mutate_pdf_version() {
  local path="$1"
  python3 -I -S - "$path" <<'PY'
from pathlib import Path
import os
import sys


path = Path(sys.argv[1])
raw = path.read_bytes()
if raw.count(b"%PDF-1.7") != 1:
    raise SystemExit("PDF-version mutation target drifted")
temporary = path.with_suffix(path.suffix + ".mutant")
temporary.write_bytes(raw.replace(b"%PDF-1.7", b"%PDF-1.6", 1))
os.replace(temporary, path)
PY
}

validate_checker_contract "$CHECKER"
POSITIVE_COUNT=$((POSITIVE_COUNT + 1))
pass "production checker retains the exact, receipt, profile, stderr, and cleanup contract"

run_contract_mutation "same-toolchain byte comparison removal is rejected" \
  'cmp -s "$FIRST" "$SECOND" || {' \
  'true || {'
run_contract_mutation "committed-byte comparison weakening is rejected" \
  'cmp -s "$FIRST" "$COMMITTED" || {' \
  'cmp -s "$FIRST" "$COMMITTED" && {'
run_contract_mutation "visual-receipt identity binding removal is rejected" \
  "require_sha256 \"\$VISUAL_RECEIPT\" \"\$VISUAL_RECEIPT_SHA256\" \\" \
  "# visual-receipt identity omitted \\"
run_contract_mutation "visual-receipt subject-PDF binding removal is rejected" \
  "require_sha256 \"\$COMMITTED\" \"\$VISUAL_RECEIPT_PDF_SHA256\" \\" \
  "# visual-receipt PDF binding omitted \\"
run_contract_mutation "visual-receipt subject-locator weakening is rejected" \
  'subject: \`output/pdf/post-publication-custody-2026-09-02.pdf\`' \
  'subject: \`output/pdf/unreviewed.pdf\`'
run_contract_mutation "visual-review page-scope weakening is rejected" \
  'require_unique_line "pages: \`6\`" "visual-review receipt page scope"' \
  'require_unique_line "pages: \`1\`" "visual-review receipt page scope"'
run_contract_mutation "visual-review disposition weakening is rejected" \
  'require_unique_line "status: \`passed\`" "visual-review receipt disposition"' \
  'require_unique_line "status: \`not-reviewed\`" "visual-review receipt disposition"'
run_contract_mutation "A4 profile weakening is rejected" \
  '\(A4\)$' '\(Letter\)$'
run_contract_mutation "PDF-version profile weakening is rejected" \
  "'^PDF version:[[:space:]]+1\\.7$'" \
  "'^PDF version:[[:space:]]+1\\.6$'"
run_contract_mutation "active-content metadata weakening is rejected" \
  "'^JavaScript:[[:space:]]+no$'" \
  "'^JavaScript:[[:space:]]+yes$'"
run_contract_mutation "embedded-font predicate weakening is rejected" \
  '$(NF - 4) != "yes"' '$(NF - 4) != "no"'
run_contract_mutation "cross-toolchain status weakening is rejected" \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 2' \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 1'
run_contract_mutation "builder-stderr rejection removal is rejected" \
  'if [[ -s "$BUILD_ROOT/first.stderr" || -s "$BUILD_ROOT/second.stderr" ]]; then' \
  'if [[ ! -s "$BUILD_ROOT/first.stderr" && ! -s "$BUILD_ROOT/second.stderr" ]]; then'
run_contract_mutation "isolated-shell builder control removal is rejected" \
  'TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$FIRST"' \
  'TMPDIR="$BUILD_ROOT" bash "$BUILDER" "$FIRST"'
run_contract_mutation "optimized custody-record check removal is rejected" \
  'python3 -O -I -S -B "$RECORD_CHECKER"' \
  '# optimized custody-record check omitted'
run_contract_mutation "temporary cleanup command removal is rejected" \
  '"$TMP_BASE"/pid-rs-custody-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;' \
  '"$TMP_BASE"/pid-rs-custody-pdf-check.*) : ;;'
run_contract_mutation "temporary cleanup target broadening is rejected" \
  '"$TMP_BASE"/pid-rs-custody-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;' \
  '"$TMP_BASE"/*) rm -rf -- "$BUILD_ROOT" ;;'
run_contract_mutation "EXIT cleanup trap removal is rejected" \
  'trap '\''cleanup "$?"'\'' EXIT' \
  '# EXIT cleanup trap omitted'
run_contract_mutation "cleanup failure-status preservation weakening is rejected" \
  '  exit "$status"' \
  '  exit 0'

fixture="$TEST_ROOT/positive"
make_fixture "$fixture"
expect_success "$fixture" \
  "matching bytes pass once after exactly two fast isolated builds and leave no checker scratch"

expect_failure "$fixture" --cross-toolchain 2 \
  "no reviewed cross-toolchain producer profile exists; no cross-toolchain acceptance is issued" \
  "cross-toolchain mode refuses with exact status 2"

expect_invocation_failure "$fixture" 2 "usage:" \
  "unknown mode refuses with usage status 2" --unknown
expect_invocation_failure "$fixture" 2 "usage:" \
  "extra argument refuses with usage status 2" --exact unexpected

fixture="$TEST_ROOT/visual-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md"
expect_failure "$fixture" --exact 1 "visual-review receipt identity drifted" \
  "unresealed visual-review receipt drift rejects before building"

fixture="$TEST_ROOT/visual-status-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md" \
  'status: `passed`' 'status: `not-reviewed`'
reseal_visual_receipt "$fixture"
expect_failure "$fixture" --exact 1 "visual-review receipt disposition drifted" \
  "coordinated receipt-digest reseal cannot weaken the visual disposition"

fixture="$TEST_ROOT/committed-drift-resealed"
make_fixture "$fixture"
printf '\n%% fixture committed-byte drift\n' \
  >>"$fixture/output/pdf/post-publication-custody-2026-09-02.pdf"
reseal_visual_pdf_binding "$fixture"
expect_failure "$fixture" --exact 1 \
  "committed PDF differs from the reproducible build" \
  "resealed committed-byte drift still fails the independent build comparison"

fixture="$TEST_ROOT/pdf-version-resealed"
make_fixture "$fixture"
mutate_pdf_version "$fixture/output/pdf/post-publication-custody-2026-09-02.pdf"
mutate_pdf_version "$fixture/expected-builder-output.pdf"
reseal_visual_pdf_binding "$fixture"
expect_failure "$fixture" --exact 1 "committed PDF is not PDF 1.7" \
  "coordinated PDF/build/receipt byte drift cannot weaken the PDF 1.7 profile"

fixture="$TEST_ROOT/builder-stderr"
make_fixture "$fixture"
expect_failure "$fixture" --exact 1 "builder emitted stderr" \
  "builder stderr is fatal and failure cleanup removes checker scratch" \
  FIXTURE_BUILDER_MODE=stderr

fixture="$TEST_ROOT/two-build-drift"
make_fixture "$fixture"
expect_failure "$fixture" --exact 1 "two isolated same-toolchain builds differ" \
  "nondeterministic second build is rejected and failure cleanup removes checker scratch" \
  FIXTURE_BUILDER_MODE=second-drift

fixture="$TEST_ROOT/optimized-record-failure"
make_fixture "$fixture"
expect_failure "$fixture" --exact 1 "fixture record checker rejected optimized mode" \
  "optimized custody-record failure cannot fall through to a PDF build" \
  FIXTURE_RECORD_OPT_FAIL=1

fixture="$TEST_ROOT/symbolic-builder"
make_fixture "$fixture"
rm -f -- "$fixture/scripts/build-post-publication-custody-pdf.sh"
ln -s ../expected-builder-output.pdf \
  "$fixture/scripts/build-post-publication-custody-pdf.sh"
expect_failure "$fixture" --exact 1 \
  "required input is absent, non-regular, or symbolic" \
  "symbolic builder input is rejected before execution"

fixture="$TEST_ROOT/root-tmp-refusal"
make_fixture "$fixture"
observed=0
if env TMPDIR=/ bash --noprofile --norc \
    "$fixture/scripts/check-post-publication-custody-pdf.sh" --exact \
    >"$fixture/root-tmp.stdout" 2>"$fixture/root-tmp.stderr"; then
  observed=0
else
  observed=$?
fi
if [[ "$observed" -ne 2 ]] \
    || ! grep -Fq "refusing filesystem root as temporary root" \
      "$fixture/root-tmp.stderr"; then
  cat "$fixture/root-tmp.stdout" "$fixture/root-tmp.stderr" >&2
  echo "$CHECK_NAME: filesystem-root temporary control returned $observed, expected 2" >&2
  exit 1
fi
assert_checker_tmp_empty "filesystem-root temporary refusal"
HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
pass "filesystem root is refused as a temporary cleanup domain"

EXPECTED_CONTRACTS=19
EXPECTED_POSITIVES=2
EXPECTED_HOSTILES=31
EXPECTED_TOTAL=33
if [[ "$CONTRACT_COUNT" -ne "$EXPECTED_CONTRACTS" \
    || "$POSITIVE_COUNT" -ne "$EXPECTED_POSITIVES" \
    || "$HOSTILE_COUNT" -ne "$EXPECTED_HOSTILES" \
    || "$PASS_COUNT" -ne "$EXPECTED_TOTAL" ]]; then
  echo "$CHECK_NAME: inventory drifted: contracts=$CONTRACT_COUNT/$EXPECTED_CONTRACTS positives=$POSITIVE_COUNT/$EXPECTED_POSITIVES hostiles=$HOSTILE_COUNT/$EXPECTED_HOSTILES total=$PASS_COUNT/$EXPECTED_TOTAL" >&2
  exit 1
fi

echo "OK: $CHECK_NAME passed $PASS_COUNT controls ($POSITIVE_COUNT accepted, $HOSTILE_COUNT hostile; $CONTRACT_COUNT source-contract mutations)"
