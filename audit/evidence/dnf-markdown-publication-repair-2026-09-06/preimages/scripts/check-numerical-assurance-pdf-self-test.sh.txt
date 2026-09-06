#!/usr/bin/env bash
# Bounded hostile controls for the numerical-assurance publication gate.
# This suite tests the checker, not the mathematical claims or PDF accessibility.
# Hostile source fragments are intentionally passed as single-quoted data below.
# shellcheck disable=SC2016
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
CHECKER="$ROOT/scripts/check-numerical-assurance-pdf.sh"
CHECK_NAME="Numerical assurance PDF check self-test"

for command_name in bash cat chmod cp git grep ln mkdir mktemp mv python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done

REQUIRED_PRODUCTION_INPUTS=(
  "$CHECKER"
  "$ROOT/scripts/check-markdown-math.py"
  "$ROOT/NUMERICAL_ASSURANCE.md"
  "$ROOT/output/pdf/numerical-assurance.pdf"
  "$ROOT/audit/formal/latex/numerical-assurance/header.tex"
  "$ROOT/audit/formal/latex/numerical-assurance/filter.lua"
  "$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
  "$ROOT/audit/formal/latex/figures/numerical-assurance/figure-assets.json"
  "$ROOT/audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg"
  "$ROOT/audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf"
  "$ROOT/audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.svg"
  "$ROOT/audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.pdf"
)
for required in "${REQUIRED_PRODUCTION_INPUTS[@]}"; do
  [[ -f "$required" && ! -L "$required" ]] || {
    echo "$CHECK_NAME: required production input is absent, nonregular, or symbolic: $required" >&2
    exit 2
  }
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
TEST_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-numerical-assurance-pdf-self-test.XXXXXX")"
TEST_ROOT="$(CDPATH='' cd -- "$TEST_ROOT" && pwd -P)"
mkdir "$TEST_ROOT/checker-tmp"

cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$TEST_ROOT" in
    "$TMP_BASE"/pid-rs-numerical-assurance-pdf-self-test.*)
      rm -rf -- "$TEST_ROOT" || status=1
      ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $TEST_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
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

make_fixture() {
  local fixture="$1"
  mkdir -p \
    "$fixture/scripts" \
    "$fixture/output/pdf" \
    "$fixture/audit/formal/latex/numerical-assurance" \
    "$fixture/audit/formal/latex/mathematical-results-guide" \
    "$fixture/audit/formal/latex/figures/numerical-assurance"

  cp "$CHECKER" "$fixture/scripts/check-numerical-assurance-pdf.sh"
  cp "$ROOT/scripts/check-markdown-math.py" "$fixture/scripts/"
  cp "$ROOT/NUMERICAL_ASSURANCE.md" "$fixture/"
  cp "$ROOT/output/pdf/numerical-assurance.pdf" \
    "$fixture/output/pdf/numerical-assurance.pdf"
  cp "$ROOT/output/pdf/numerical-assurance.pdf" "$fixture/expected-builder-output.pdf"
  cp "$ROOT/audit/formal/latex/numerical-assurance/header.tex" \
    "$fixture/audit/formal/latex/numerical-assurance/"
  cp "$ROOT/audit/formal/latex/numerical-assurance/filter.lua" \
    "$fixture/audit/formal/latex/numerical-assurance/"
  cp "$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "$fixture/audit/formal/latex/mathematical-results-guide/"
  cp \
    "$ROOT/audit/formal/latex/figures/numerical-assurance/figure-assets.json" \
    "$ROOT/audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg" \
    "$ROOT/audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf" \
    "$ROOT/audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.svg" \
    "$ROOT/audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.pdf" \
    "$fixture/audit/formal/latex/figures/numerical-assurance/"

  printf '%s\n' \
    '#!/usr/bin/env bash' \
    'set -euo pipefail' \
    'ROOT="$(CDPATH='"'"''"'"' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"' \
    'if [[ "$#" -ne 2 || "$1" != "--output" || "$2" != /* || "$2" != *.pdf ]]; then' \
    '  echo "fixture builder: usage: $0 --output ABSOLUTE_PDF_PATH" >&2' \
    '  exit 2' \
    'fi' \
    'cp "$ROOT/expected-builder-output.pdf" "$2"' \
    'printf "OK: fixture builder copied reviewed bytes\\n"' \
    >"$fixture/scripts/build-numerical-assurance-pdf.sh"

  chmod 0755 \
    "$fixture/scripts/check-numerical-assurance-pdf.sh" \
    "$fixture/scripts/build-numerical-assurance-pdf.sh"
  git -C "$fixture" init -q
}

run_checker() {
  local fixture="$1" mode="$2" stdout="$3" stderr="$4"
  shift 4
  TMPDIR="$TEST_ROOT/checker-tmp/" \
    "$@" bash --noprofile --norc \
    "$fixture/scripts/check-numerical-assurance-pdf.sh" "$mode" \
    >"$stdout" 2>"$stderr"
}

expect_success() {
  local fixture="$1" mode="$2" label="$3"
  local slug="success-$PASS_COUNT-${mode#--}"
  local stdout="$TEST_ROOT/$slug.stdout" stderr="$TEST_ROOT/$slug.stderr"
  if ! run_checker "$fixture" "$mode" "$stdout" "$stderr" env; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: accepted control failed: $label" >&2
    exit 1
  fi
  if [[ -s "$stderr" ]] \
      || ! grep -Fq "OK: numerical assurance PDF mode=$mode pages=23 sha256=" "$stdout"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: accepted control lacks the exact success contract: $label" >&2
    exit 1
  fi
  POSITIVE_COUNT=$((POSITIVE_COUNT + 1))
  pass "$label"
}

expect_failure() {
  local fixture="$1" mode="$2" needle="$3" label="$4"
  local slug="failure-$PASS_COUNT-${mode#--}"
  local stdout="$TEST_ROOT/$slug.stdout" stderr="$TEST_ROOT/$slug.stderr"
  if run_checker "$fixture" "$mode" "$stdout" "$stderr" env; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: hostile control was accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq -- "$needle" "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: hostile control failed for a noncausal reason: $label" >&2
    exit 1
  fi
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

expect_usage_status() {
  local fixture="$1" expected_status="$2" label="$3"
  shift 3
  local stdout="$TEST_ROOT/usage-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/usage-$PASS_COUNT.stderr"
  local observed=0
  if TMPDIR="$TEST_ROOT/checker-tmp/" bash --noprofile --norc \
      "$fixture/scripts/check-numerical-assurance-pdf.sh" "$@" \
      >"$stdout" 2>"$stderr"; then
    observed=0
  else
    observed=$?
  fi
  if [[ "$observed" -ne "$expected_status" ]] \
      || ! grep -Fq 'usage:' "$stderr"; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: mode/arity control returned $observed, expected $expected_status: $label" >&2
    exit 1
  fi
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

mutate_pdf() {
  local source="$1" destination="$2" mutation="$3"
  python3 -I -B - "$source" "$destination" "$mutation" <<'PY'
from pathlib import Path
import sys

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, ByteStringObject, DictionaryObject, IndirectObject, NameObject


source = Path(sys.argv[1])
destination = Path(sys.argv[2])
mutation = sys.argv[3]
reader = PdfReader(source, strict=True)
writer = PdfWriter()
writer.clone_document_from_reader(reader)
writer.pdf_header = reader.pdf_header


def dereference(value):
    return value.get_object() if isinstance(value, IndirectObject) else value


def raw_bytes(value):
    raw = getattr(value, "original_bytes", None)
    if raw is None and isinstance(value, bytes):
        raw = bytes(value)
    if raw is None:
        raise SystemExit("fixture cannot preserve source trailer ID")
    return raw


source_ids = reader.trailer.get("/ID")
if not isinstance(source_ids, ArrayObject) or len(source_ids) != 2:
    raise SystemExit("fixture source trailer ID is malformed")
writer._ID = ArrayObject([ByteStringObject(raw_bytes(value)) for value in source_ids])

if mutation == "page-count":
    writer.remove_page(len(writer.pages) - 1)
elif mutation == "trailer-id":
    writer._ID = ArrayObject(
        [ByteStringObject(b"\x00" * 16), ByteStringObject(b"\x00" * 16)]
    )
elif mutation == "open-action":
    if writer.root_object.pop(NameObject("/OpenAction"), None) is None:
        raise SystemExit("fixture source lacks OpenAction")
elif mutation == "link-action":
    changed = False
    for page in writer.pages:
        annotations = dereference(page.get("/Annots"))
        if not isinstance(annotations, ArrayObject):
            continue
        for reference in annotations:
            annotation = dereference(reference)
            if not isinstance(annotation, DictionaryObject):
                continue
            action = dereference(annotation.get("/A"))
            if isinstance(action, DictionaryObject) and str(action.get("/S")) == "/URI":
                action[NameObject("/S")] = NameObject("/Launch")
                action.pop(NameObject("/URI"), None)
                changed = True
                break
        if changed:
            break
    if not changed:
        raise SystemExit("fixture source lacks a URI action")
else:
    raise SystemExit(f"unknown fixture mutation: {mutation}")

with destination.open("wb") as stream:
    writer.write(stream)
PY
}

install_mutated_pdf_pair() {
  local fixture="$1" mutation="$2"
  local mutated="$fixture/mutated-$mutation.pdf"
  mutate_pdf "$ROOT/output/pdf/numerical-assurance.pdf" "$mutated" "$mutation"
  mv "$mutated" "$fixture/output/pdf/numerical-assurance.pdf"
  cp "$fixture/output/pdf/numerical-assurance.pdf" "$fixture/expected-builder-output.pdf"
}

validate_checker_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required_once = (
    'if [[ $# -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then',
    '[[ -f "$required" && ! -L "$required" ]] || {',
    'python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"',
    '"audit/formal/latex/figures/numerical-assurance/figure-assets.json" \\',
    '"audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf" \\',
    '"audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.pdf"',
    '"$BUILDER" --output "$rebuilt"',
    "'^Pages:[[:space:]]+23$' \\",
    "'Exact reduction of already represented binary64 operands is not exact estimation.' \\",
    "'There is no test-only switch' \\",
    "'Fifty-lens hostile review' \\",
    "'thermal window' \\",
    "'Partial Information Decomposition for Continuous Variables based on'; do",
    "if grep -Eq '\\\\begin\\{|\\\\end\\{|\\$\\$|\\\\[[:alpha:]]+|�|Dedicated PDF absent|does not exist' \"$text\"; then",
    'if actual_ids != [expected_id, expected_id]:',
    'if not isinstance(open_action, DictionaryObject) or str(open_action.get("/S")) != "/GoTo":',
    'if kind in forbidden_action_kinds or kind not in allowed_action_kinds:',
    'if observed_repository_uris != expected_repository_uris:',
    'expected_action_counts = {"/GoTo": 34, "/GoToR": 0, "/URI": 15}',
    'pdftoppm -f 1 -l 23 -r 36 -png "$candidate" "$render_prefix" >/dev/null 2>&1',
    '[[ "$rendered_count" == "23" ]] || {',
    'validate_pdf "$PDF" committed',
    'validate_pdf "$rebuilt" rebuilt',
    'if [[ "$MODE" == "--exact" ]]; then',
    'cmp -s "$rebuilt" "$PDF" || {',
    'cmp -s "$tmp_root/committed-layout.txt" "$tmp_root/rebuilt-layout.txt" || {',
    'cmp -s "$tmp_root/committed-geometry.txt" "$tmp_root/rebuilt-geometry.txt" || {',
)
for literal in required_once:
    count = text.count(literal)
    if count != 1:
        raise SystemExit(
            f"checker contract literal count is {count}, expected one: {literal!r}"
        )

required_source_digest_order = (
    '"NUMERICAL_ASSURANCE.md" \\',
    '"audit/formal/latex/numerical-assurance/header.tex" \\',
    '"audit/formal/latex/numerical-assurance/filter.lua" \\',
    '"audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \\',
    '"audit/formal/latex/figures/numerical-assurance/figure-assets.json" \\',
    '"audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg" \\',
    '"audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf" \\',
    '"audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.svg" \\',
    '"audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.pdf"',
)
positions = []
cursor = text.index('source_digest_record="$tmp_root/source-digests.txt"')
for literal in required_source_digest_order:
    position = text.find(literal, cursor)
    if position < 0:
        raise SystemExit(f"source-derived trailer-ID input is absent: {literal!r}")
    positions.append(position)
    cursor = position + len(literal)
if positions != sorted(positions):
    raise SystemExit("source-derived trailer-ID inputs are out of order")

exact_block = '''if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$rebuilt" "$PDF" || {
    echo "$CHECK_NAME failed: committed PDF is stale or not same-toolchain reproducible" >&2
    exit 1
  }
else
'''
if text.count(exact_block) != 1:
    raise SystemExit("exact-byte comparison branch drifted")

cross_block = '''  pdftotext -layout "$PDF" "$tmp_root/committed-layout.txt"
  pdftotext -layout "$rebuilt" "$tmp_root/rebuilt-layout.txt"
  cmp -s "$tmp_root/committed-layout.txt" "$tmp_root/rebuilt-layout.txt" || {
    echo "$CHECK_NAME failed: cross-toolchain extracted layout text changed" >&2
    exit 1
  }
  pdfinfo "$PDF" | grep -E '^(Pages|Page size):' >"$tmp_root/committed-geometry.txt"
  pdfinfo "$rebuilt" | grep -E '^(Pages|Page size):' >"$tmp_root/rebuilt-geometry.txt"
  cmp -s "$tmp_root/committed-geometry.txt" "$tmp_root/rebuilt-geometry.txt" || {
    echo "$CHECK_NAME failed: cross-toolchain page geometry changed" >&2
    exit 1
  }
fi
'''
if text.count(cross_block) != 1:
    raise SystemExit("cross-toolchain comparison branch drifted")

ordered = (
    'python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"',
    'source_digest_record="$tmp_root/source-digests.txt"',
    '"$BUILDER" --output "$rebuilt"',
    'validate_pdf "$PDF" committed',
    'validate_pdf "$rebuilt" rebuilt',
    'if [[ "$MODE" == "--exact" ]]; then',
)
ordered_positions = [text.index(literal) for literal in ordered]
if ordered_positions != sorted(ordered_positions):
    raise SystemExit("source/build/validation/equivalence order drifted")
PY
}

run_contract_mutation() {
  local label="$1" before="$2" after="$3"
  local mutant="$TEST_ROOT/checker-contract-$PASS_COUNT.sh"
  cp "$CHECKER" "$mutant"
  replace_once "$mutant" "$before" "$after"
  if validate_checker_contract "$mutant" \
      >"$TEST_ROOT/contract-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/contract-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: checker-contract mutation was accepted: $label" >&2
    exit 1
  fi
  HOSTILE_COUNT=$((HOSTILE_COUNT + 1))
  pass "$label"
}

validate_checker_contract "$CHECKER"
CONTRACT_COUNT=$((CONTRACT_COUNT + 1))
pass "production checker retains its independent source, PDF, object, and mode contract"

fixture="$TEST_ROOT/positive"
make_fixture "$fixture"
expect_success "$fixture" --exact \
  "matching committed and rebuilt bytes pass exact mode"
expect_success "$fixture" --cross-toolchain \
  "matching committed and rebuilt bytes pass explicit cross-toolchain mode"
expect_usage_status "$fixture" 2 "unknown mode is rejected with status 2" --unknown
expect_usage_status "$fixture" 2 "extra arguments are rejected with status 2" --exact extra

fixture="$TEST_ROOT/source-drift"
make_fixture "$fixture"
printf '\nSelf-test source identity mutation.\n' >>"$fixture/NUMERICAL_ASSURANCE.md"
expect_failure "$fixture" --exact "trailer ID is not source derived" \
  "canonical Markdown drift invalidates exact-mode source identity"
expect_failure "$fixture" --cross-toolchain "trailer ID is not source derived" \
  "cross-toolchain mode cannot bypass canonical Markdown identity"

fixture="$TEST_ROOT/projection-drift"
make_fixture "$fixture"
printf '\n%% Self-test projection identity mutation.\n' \
  >>"$fixture/audit/formal/latex/numerical-assurance/header.tex"
expect_failure "$fixture" --exact "trailer ID is not source derived" \
  "projection-source drift invalidates the source-derived trailer ID"

fixture="$TEST_ROOT/figure-drift"
make_fixture "$fixture"
printf '\n<!-- Self-test figure identity mutation. -->\n' \
  >>"$fixture/audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg"
expect_failure "$fixture" --cross-toolchain "trailer ID is not source derived" \
  "cross-toolchain mode cannot bypass imported-figure identity"

fixture="$TEST_ROOT/symbolic-source"
make_fixture "$fixture"
mv "$fixture/NUMERICAL_ASSURANCE.md" "$fixture/source-target.md"
ln -s source-target.md "$fixture/NUMERICAL_ASSURANCE.md"
expect_failure "$fixture" --exact "required input is absent, nonregular, or symbolic" \
  "symbolic canonical source is rejected before the build"

fixture="$TEST_ROOT/serialization-only-drift"
make_fixture "$fixture"
printf '\n%% self-test trailing serialization byte\n' \
  >>"$fixture/output/pdf/numerical-assurance.pdf"
expect_failure "$fixture" --exact \
  "committed PDF is stale or not same-toolchain reproducible" \
  "default exact mode rejects serialization-only byte drift"
expect_success "$fixture" --cross-toolchain \
  "explicit cross-toolchain mode admits the reviewed serialization-only fixture"

fixture="$TEST_ROOT/page-count"
make_fixture "$fixture"
install_mutated_pdf_pair "$fixture" page-count
expect_failure "$fixture" --exact "committed metadata omitted: ^Pages:[[:space:]]+23$" \
  "matching 22-page PDFs cannot bypass the fixed page contract"

fixture="$TEST_ROOT/trailer-id"
make_fixture "$fixture"
install_mutated_pdf_pair "$fixture" trailer-id
expect_failure "$fixture" --exact "trailer ID is not source derived" \
  "matching PDFs with a forged trailer ID are rejected"

fixture="$TEST_ROOT/open-action"
make_fixture "$fixture"
install_mutated_pdf_pair "$fixture" open-action
expect_failure "$fixture" --exact "catalog OpenAction is not a bounded internal GoTo" \
  "matching PDFs without the bounded first-page OpenAction are rejected"

fixture="$TEST_ROOT/link-action"
make_fixture "$fixture"
install_mutated_pdf_pair "$fixture" link-action
expect_failure "$fixture" --cross-toolchain "contains forbidden or unknown action /Launch" \
  "cross-toolchain mode rejects matching PDFs with a forbidden Launch action"

run_contract_mutation "mode-guard weakening is detected" \
  '"$MODE" != "--exact" && "$MODE" != "--cross-toolchain"' \
  '"$MODE" != "--exact"'
run_contract_mutation "required-input symlink weakening is detected" \
  '[[ -f "$required" && ! -L "$required" ]]' \
  '[[ -f "$required" ]]'
run_contract_mutation "Markdown math-gate bypass is detected" \
  'python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"' \
  '# Markdown math gate omitted'
run_contract_mutation "figure-PDF source binding removal is detected" \
  '    "audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf" \
' \
  '    # quantizer-cardinality PDF omitted
'
run_contract_mutation "builder wiring drift is detected" \
  '"$BUILDER" --output "$rebuilt"' \
  'cp "$PDF" "$rebuilt"'
run_contract_mutation "fixed page-count weakening is detected" \
  "'^Pages:[[:space:]]+23$'" \
  "'^Pages:[[:space:]]+[1-9][0-9]*$'"
run_contract_mutation "reviewed text-sentinel removal is detected" \
  "'There is no test-only switch'" \
  "'There may be a test-only switch'"
run_contract_mutation "raw-TeX rejection weakening is detected" \
  '\$\$|\\[[:alpha:]]+' \
  '\\[[:alpha:]]+'
run_contract_mutation "source-derived trailer-ID equality inversion is detected" \
  'if actual_ids != [expected_id, expected_id]:' \
  'if actual_ids == [expected_id, expected_id]:'
run_contract_mutation "OpenAction predicate weakening is detected" \
  'or str(open_action.get("/S")) != "/GoTo"' \
  'or str(open_action.get("/S")) == "/GoTo"'
run_contract_mutation "forbidden-action predicate weakening is detected" \
  'if kind in forbidden_action_kinds or kind not in allowed_action_kinds:' \
  'if kind not in allowed_action_kinds:'
run_contract_mutation "repository-navigation inventory weakening is detected" \
  'if observed_repository_uris != expected_repository_uris:' \
  'if not observed_repository_uris.issubset(expected_repository_uris):'
run_contract_mutation "action-count weakening is detected" \
  'expected_action_counts = {"/GoTo": 34, "/GoToR": 0, "/URI": 15}' \
  'expected_action_counts = action_counts'
run_contract_mutation "all-page raster command weakening is detected" \
  'pdftoppm -f 1 -l 23 -r 36' \
  'pdftoppm -f 1 -l 1 -r 36'
run_contract_mutation "all-page raster-count weakening is detected" \
  '[[ "$rendered_count" == "23" ]]' \
  '[[ "$rendered_count" -ge 1 ]]'
run_contract_mutation "committed-PDF validation bypass is detected" \
  'validate_pdf "$PDF" committed' \
  '# committed PDF validation omitted'
run_contract_mutation "rebuilt-PDF validation bypass is detected" \
  'validate_pdf "$rebuilt" rebuilt' \
  '# rebuilt PDF validation omitted'
run_contract_mutation "exact-byte comparison inversion is detected" \
  'cmp -s "$rebuilt" "$PDF" || {' \
  'cmp -s "$rebuilt" "$PDF" && {'
run_contract_mutation "cross-toolchain text comparison bypass is detected" \
  'cmp -s "$tmp_root/committed-layout.txt" "$tmp_root/rebuilt-layout.txt" || {' \
  'true || {'
run_contract_mutation "cross-toolchain geometry comparison bypass is detected" \
  'cmp -s "$tmp_root/committed-geometry.txt" "$tmp_root/rebuilt-geometry.txt" || {' \
  'true || {'

EXPECTED_TOTAL=36
EXPECTED_POSITIVE=3
EXPECTED_HOSTILE=32
EXPECTED_CONTRACT=1
if [[ "$PASS_COUNT" -ne "$EXPECTED_TOTAL" \
    || "$POSITIVE_COUNT" -ne "$EXPECTED_POSITIVE" \
    || "$HOSTILE_COUNT" -ne "$EXPECTED_HOSTILE" \
    || "$CONTRACT_COUNT" -ne "$EXPECTED_CONTRACT" \
    || "$PASS_COUNT" -ne $((POSITIVE_COUNT + HOSTILE_COUNT + CONTRACT_COUNT)) ]]; then
  echo "$CHECK_NAME: accounting drifted: total=$PASS_COUNT contract=$CONTRACT_COUNT positive=$POSITIVE_COUNT hostile=$HOSTILE_COUNT" >&2
  exit 1
fi

printf 'OK: numerical assurance PDF checker passed %d controls (%d contract, %d accepted-mode, %d hostile); exact bytes remain mandatory in default mode and cross-toolchain acceptance remains explicit and structurally bounded\n' \
  "$PASS_COUNT" "$CONTRACT_COUNT" "$POSITIVE_COUNT" "$HOSTILE_COUNT"
