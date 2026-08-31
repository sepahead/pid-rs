#!/usr/bin/env bash
# Hostile controls for the exact-only blueprint PDF gate.
# Hostile mutations below intentionally pass single-quoted shell-source fragments as data.
# shellcheck disable=SC2016
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CHECKER="$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
BUILDER="$ROOT/scripts/build-pid-discovery-verification-blueprint.sh"
CHECK_NAME="PID blueprint PDF check self-test"

for command_name in awk bash cmp cp grep mkdir mktemp mv python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
for path in "$CHECKER" "$BUILDER" "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"; do
  [[ -f "$path" && ! -L "$path" ]] || {
    echo "$CHECK_NAME: required production input is absent, non-regular, or symbolic: $path" >&2
    exit 2
  }
done

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
if ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "$CHECK_NAME: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
TEST_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-blueprint-pdf-self-test.XXXXXX")"
cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$TEST_ROOT" in
    "$TMP_BASE"/pid-rs-blueprint-pdf-self-test.*) rm -rf -- "$TEST_ROOT" ;;
    *) echo "$CHECK_NAME: refusing unexpected cleanup path: $TEST_ROOT" >&2; status=1 ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

PASS_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT + 1)); printf 'ok %d - %s\n' "$PASS_COUNT" "$1"; }

replace_once() {
  local path="$1" before="$2" after="$3"
  python3 -I -S - "$path" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2]
after = sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(before) != 1:
    raise SystemExit(f"mutation anchor count is {text.count(before)}, expected one: {before!r}")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
}

reseal_fixture_input() {
  local fixture="$1" variable="$2" relative="$3"
  local checker="$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
  local old_digest new_digest
  old_digest="$(awk -F'"' -v prefix="$variable=" '$0 ~ ("^" prefix) {print $2}' "$checker")"
  new_digest="$(shasum -a 256 "$fixture/$relative" | awk '{print $1}')"
  if [[ ! "$old_digest" =~ ^[0-9a-f]{64}$ || ! "$new_digest" =~ ^[0-9a-f]{64}$ ]]; then
    echo "$CHECK_NAME: cannot reseal hostile fixture input: $variable" >&2
    exit 1
  fi
  replace_once "$checker" "$old_digest" "$new_digest"
}

make_fixture() {
  local fixture="$1"
  mkdir -p \
    "$fixture/scripts" \
    "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001" \
    "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
  cp "$CHECKER" "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh"
  cp "$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh" "$fixture/scripts/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" "$fixture/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" "$fixture/"
  cp "$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf" "$fixture/expected-builder-output.pdf"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md" "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/"
  cp "$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-header.tex" "$fixture/audit/formal/latex/"
  cp "$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-filter.lua" "$fixture/audit/formal/latex/"
  cp "$ROOT/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/"*.svg "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/"
  cat >"$fixture/scripts/build-pid-discovery-verification-blueprint.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$#" -eq 1 ]] || exit 2
cp "$ROOT/expected-builder-output.pdf" "$1"
printf 'OK: fixture same-toolchain builder\n'
EOF
  chmod 0755 "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" "$fixture/scripts/build-pid-discovery-verification-blueprint.sh"
}

expect_success() {
  local fixture="$1"
  if ! TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" >"$fixture/out" 2>"$fixture/err"; then
    cat "$fixture/out" "$fixture/err" >&2
    echo "$CHECK_NAME: exact fixture was rejected" >&2
    exit 1
  fi
  grep -Fq 'exact committed-byte relation passed' "$fixture/out" || {
    cat "$fixture/out" >&2
    echo "$CHECK_NAME: exact fixture success contract changed" >&2
    exit 1
  }
}

expect_failure() {
  local fixture="$1" needle="$2"
  if TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" >"$fixture/out" 2>"$fixture/err"; then
    echo "$CHECK_NAME: hostile fixture was accepted" >&2
    exit 1
  fi
  grep -Fq "$needle" "$fixture/err" || {
    cat "$fixture/out" "$fixture/err" >&2
    echo "$CHECK_NAME: hostile fixture failed for a noncausal reason" >&2
    exit 1
  }
}

run_resealed_decision_mutation() {
  local slug="$1" label="$2" before="$3" after="$4" needle="$5"
  local fixture="$TEST_ROOT/$slug"
  make_fixture "$fixture"
  replace_once \
    "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" \
    "$before" \
    "$after"
  reseal_fixture_input "$fixture" DECISION_V2_SHA256 \
    "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
  expect_failure "$fixture" "$needle"
  pass "$label"
}

expect_cross_status() {
  local fixture="$1" expected="$2"
  local observed
  if TMPDIR="$TEST_ROOT/" bash --noprofile --norc \
      "$fixture/scripts/check-pid-discovery-verification-blueprint-pdf.sh" \
      --cross-toolchain >"$fixture/cross.out" 2>"$fixture/cross.err"; then
    observed=0
  else
    observed=$?
  fi
  if [[ "$observed" -ne "$expected" ]]; then
    cat "$fixture/cross.out" "$fixture/cross.err" >&2
    echo "$CHECK_NAME: cross refusal returned $observed, expected $expected" >&2
    return 1
  fi
  grep -Fq 'no reviewed cross-toolchain equivalence relation or producer profile exists' \
    "$fixture/cross.err" || {
      cat "$fixture/cross.err" >&2
      echo "$CHECK_NAME: cross refusal diagnostic changed" >&2
      return 1
    }
}

validate_checker_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
lines = text.splitlines()
required_lines = (
    'require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"',
    'require_unique_line "$DECISION_V2" \'**Disposition: proposed/open.**\' \\',
    '    \'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier\'; do',
    '  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 18 || "$pages" -gt 32 ]]; then',
    '  if ! grep -Eq \'^Page size:[[:space:]]+595\\.[0-9]+ x 841\\.[0-9]+ pts \\(A4\\)$\' "$info"; then',
    '      \'^Tagged:[[:space:]]+no$\' \\',
    '      \'Current 31 August 2026 adversarial publication closure\' \\',
    '  pdftoppm -f 1 -l "$pages" -r 36 -png "$pdf" "$render_prefix" >/dev/null 2>&1',
    'validate_pdf rebuilt "$BUILT"',
    'validate_pdf committed "$COMMITTED"',
    'if ! cmp -s "$BUILT" "$COMMITTED"; then',
)
for line in required_lines:
    if lines.count(line) != 1:
        raise SystemExit(f"checker contract line drifted: {line!r}")
cross_block = '''if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain equivalence relation or producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi
'''
if text.count(cross_block) != 1:
    raise SystemExit("checker cross-toolchain refusal block drifted")
metadata_block = '''  for metadata in \\
      '^Tagged:[[:space:]]+no$' \\
      '^Form:[[:space:]]+none$' \\
      '^JavaScript:[[:space:]]+no$' \\
      '^Encrypted:[[:space:]]+no$'; do
'''
if text.count(metadata_block) != 1:
    raise SystemExit("checker PDF metadata block drifted")
font_predicate = 'if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1'
if text.count(font_predicate) != 1:
    raise SystemExit("checker embedded-font predicate drifted")
raster_count = 'if [[ "$rendered_count" != "$pages" ]]; then'
if text.count(raster_count) != 1:
    raise SystemExit("checker all-page raster-count predicate drifted")
ordered = (
    'require_sha256 "$DECISION_V2"',
    'for required_link in',
    'validate_pdf() {',
    'validate_pdf rebuilt "$BUILT"',
    'validate_pdf committed "$COMMITTED"',
    'if ! cmp -s "$BUILT" "$COMMITTED"; then',
)
positions = [text.index(item) for item in ordered]
if positions != sorted(positions):
    raise SystemExit("checker evidence/build/validation order drifted")
PY
}

run_contract_mutation() {
  local label="$1" before="$2" after="$3"
  local mutant="$TEST_ROOT/checker-contract-$PASS_COUNT.sh"
  cp "$CHECKER" "$mutant"
  replace_once "$mutant" "$before" "$after"
  if validate_checker_contract "$mutant" \
      >"$TEST_ROOT/checker-contract-$PASS_COUNT.out" \
      2>"$TEST_ROOT/checker-contract-$PASS_COUNT.err"; then
    echo "$CHECK_NAME: checker contract mutation was accepted: $label" >&2
    exit 1
  fi
  pass "$label"
}

fixture="$TEST_ROOT/positive"
make_fixture "$fixture"
expect_success "$fixture"
pass "exact fixture accepts matching committed bytes with a trailing-slash temporary root"

validate_checker_contract "$CHECKER"
pass "production checker retains the load-bearing exact/status/PDF validation contract"

expect_cross_status "$fixture" 2
pass "cross-toolchain mode refuses with exact status 2 and no invented profile"

run_contract_mutation "page-count weakening is rejected" \
  '"$pages" -lt 18' '"$pages" -lt 1'
run_contract_mutation "A4 predicate drift is rejected" \
  '\(A4\)$' '\(Letter\)$'
run_contract_mutation "metadata predicate drift is rejected" \
  "'^Encrypted:[[:space:]]+no$'" "'^Encrypted:[[:space:]]+yes$'"
run_contract_mutation "embedded-font predicate drift is rejected" \
  '$(NF - 4) != "yes"' '$(NF - 4) != "no"'
run_contract_mutation "current-closure sentinel removal is rejected" \
  "'Current 31 August 2026 adversarial publication closure'" \
  "'Current publication closure omitted'"
run_contract_mutation "all-page raster command drift is rejected" \
  'pdftoppm -f 1 -l "$pages" -r 36' 'pdftoppm -f 1 -l 1 -r 36'
run_contract_mutation "all-page raster count weakening is rejected" \
  '"$rendered_count" != "$pages"' '"$rendered_count" -lt 1'
run_contract_mutation "rebuilt-PDF validation bypass is rejected" \
  'validate_pdf rebuilt "$BUILT"' '# validate rebuilt omitted'
run_contract_mutation "committed-PDF validation bypass is rejected" \
  'validate_pdf committed "$COMMITTED"' '# validate committed omitted'
run_contract_mutation "committed-byte comparison inversion is rejected" \
  'if ! cmp -s "$BUILT" "$COMMITTED"; then' \
  'if cmp -s "$BUILT" "$COMMITTED"; then'
run_contract_mutation "decision freshness invocation removal is rejected" \
  'require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"' \
  '# decision freshness omitted'
run_contract_mutation "conventions-link binding removal is rejected" \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier' \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#omitted'
run_contract_mutation "cross refusal status weakening is rejected" \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 2' \
  $'no cross-toolchain acceptance is issued" >&2\n  exit 1'

fixture="$TEST_ROOT/stale"
make_fixture "$fixture"
printf '\n%% stale trailing byte\n' >>"$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"
expect_failure "$fixture" "committed PDF is stale or not same-toolchain reproducible"
pass "committed-byte drift rejects"

fixture="$TEST_ROOT/missing-builder"
make_fixture "$fixture"
rm -f -- "$fixture/scripts/build-pid-discovery-verification-blueprint.sh"
expect_failure "$fixture" "required input is absent, non-regular, or symbolic"
pass "missing builder rejects before publication comparison"

fixture="$TEST_ROOT/decision-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
expect_failure "$fixture" "decision-v2 current-evidence identity drifted"
pass "unresealed decision-v2 byte drift rejects"

fixture="$TEST_ROOT/decision-disposition-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md" \
  '**Disposition: proposed/open.**' \
  '**Disposition: accepted.**'
reseal_fixture_input "$fixture" DECISION_V2_SHA256 \
  "claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
expect_failure "$fixture" "decision-v2 disposition boundary drifted"
pass "coordinated decision digest reseal cannot promote the disposition"

run_resealed_decision_mutation \
  "complete-target-resealed" \
  "coordinated decision digest reseal cannot invent complete target evidence" \
  '**Complete target-implication evidence label: no accepted end-to-end evidence.**' \
  '**Complete target-implication evidence label: accepted end-to-end evidence.**' \
  "decision-v2 complete-target boundary drifted"

run_resealed_decision_mutation \
  "scoped-results-resealed" \
  "coordinated decision digest reseal cannot turn scoped results into closure" \
  'Neither result closes the prospective certificate implication.' \
  'Together the results close the prospective certificate implication.' \
  "decision-v2 scoped-result boundary drifted"

run_resealed_decision_mutation \
  "program-a-resealed" \
  "coordinated decision digest reseal cannot upgrade Program A" \
  '| A: source and combinatorial semantics | Partial |' \
  '| A: source and combinatorial semantics | Complete |' \
  "decision-v2 Program A status drifted"

run_resealed_decision_mutation \
  "program-b-resealed" \
  "coordinated decision digest reseal cannot upgrade Program B" \
  '| B: dual formal semantics | Partial at the generic algebra layer |' \
  '| B: dual formal semantics | Complete |' \
  "decision-v2 Program B status drifted"

run_resealed_decision_mutation \
  "program-c-resealed" \
  "coordinated decision digest reseal cannot upgrade Program C" \
  '| C: certified numerics | Bounded exact sign/zero partial result |' \
  '| C: certified numerics | Complete accepted result |' \
  "decision-v2 Program C status drifted"

run_resealed_decision_mutation \
  "program-d-resealed" \
  "coordinated decision digest reseal cannot upgrade Program D" \
  '| D: compiled Rust refinement | Lexical routing observation only |' \
  '| D: compiled Rust refinement | Complete compiled refinement |' \
  "decision-v2 Program D status drifted"

run_resealed_decision_mutation \
  "program-e-resealed" \
  "coordinated decision digest reseal cannot upgrade Program E" \
  '| E: replay, provenance, and adjudication | Source-bound local receipt and partial mutation evidence |' \
  '| E: replay, provenance, and adjudication | Complete external replay and adjudication |' \
  "decision-v2 Program E status drifted"

run_resealed_decision_mutation \
  "taxonomy-108-resealed" \
  "coordinated decision digest reseal cannot relabel 108 expressions as atoms" \
  '- 108 PID atoms, lattice nodes, or independent degrees of freedom;' \
  '- 108 scalar expressions, all of which are PID atoms;' \
  "decision-v2 108-expression taxonomy drifted"

run_resealed_decision_mutation \
  "taxonomy-166-resealed" \
  "coordinated decision digest reseal cannot import the SxPID4 carrier" \
  '- the 166-position SxPID4 lattice;' \
  '- inclusion of the 166-position SxPID4 lattice;' \
  "decision-v2 four-source boundary drifted"

fixture="$TEST_ROOT/current-index-resealed"
make_fixture "$fixture"
replace_once \
  "$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md" \
  'Current proposed/open decision; two scoped sub-results receive credit, but Programs A--E remain open' \
  'Current accepted decision; all Programs A--E are closed'
reseal_fixture_input "$fixture" EVIDENCE_ADJUDICATION_INDEX_SHA256 \
  "claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md"
expect_failure "$fixture" "evidence-adjudication current pointer/status boundary drifted"
pass "coordinated index digest reseal cannot change the current status"

fixture="$TEST_ROOT/conventions-identity"
make_fixture "$fixture"
printf '\nidentity mutation\n' \
  >>"$fixture/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
expect_failure "$fixture" "frozen SxPID3 conventions identity drifted"
pass "frozen conventions byte drift rejects"

fixture="$TEST_ROOT/missing-conventions-link"
make_fixture "$fixture"
replace_once \
  "$fixture/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md" \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier' \
  'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#omitted'
expect_failure "$fixture" "source lacks required current-evidence link"
pass "missing complete-registry link rejects"

fixture="$TEST_ROOT/missing-svg"
make_fixture "$fixture"
rm -f -- \
  "$fixture/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint/semantic-transfer-firewall-source-card.svg"
expect_failure "$fixture" "required input is absent, non-regular, or symbolic"
pass "missing declared SVG source rejects"

actual_output="$TEST_ROOT/actual-trailing-slash.pdf"
TMPDIR="$TEST_ROOT/" bash --noprofile --norc "$BUILDER" "$actual_output" >"$TEST_ROOT/actual.out" 2>"$TEST_ROOT/actual.err" || {
  cat "$TEST_ROOT/actual.out" "$TEST_ROOT/actual.err" >&2
  echo "$CHECK_NAME: production builder rejected a trailing-slash temporary root" >&2
  exit 1
}
[[ -s "$actual_output" && ! -L "$actual_output" ]] || {
  echo "$CHECK_NAME: production builder did not create its trailing-slash regression artifact" >&2
  exit 1
}
pass "production builder canonicalizes a trailing-slash temporary root"

printf 'OK: %s passed %d checks\n' "$CHECK_NAME" "$PASS_COUNT"
