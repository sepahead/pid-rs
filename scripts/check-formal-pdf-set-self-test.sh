#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
PRODUCTION_GATE="$ROOT/scripts/check-formal-pdf-set.sh"
CHECK_NAME="formal PDF typed-inventory self-test"

for command_name in bash basename cat chmod cp find grep ln mkdir mktemp mv python3 rm sort; do
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
TMP_ROOT="$(CDPATH='' cd -- "$TMP_ROOT_INPUT" && pwd -P)"
if [[ "$TMP_ROOT" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
TEST_ROOT="$(mktemp -d "$TMP_ROOT/pid-rs-formal-pdf-set-self-test.XXXXXX")"
TEST_ROOT="$(CDPATH='' cd -- "$TEST_ROOT" && pwd -P)"
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

LATEX_STANDALONE=(
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
MARKDOWN_SOURCES=(
  MATHEMATICAL_RESULTS_GUIDE.md
  NUMERICAL_ASSURANCE.md
  PID2_REPRESENTED_COORDINATE_ASSURANCE.md
  PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md
  audit/evidence/post-publication-custody-2026-09-02.md
  SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md
)
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
  mathematical-results-guide
  mathematical-problem-solving-workflow
  numerical-assurance
  pid2-represented-coordinate-assurance
  pid-sensor-placement-and-galadriel-guide
  post-publication-custody-2026-09-02
  support-change-tolerant-averaged-sxpid-continuity
  sxpid3-source-marginal-and-bounded-audit
  two-source-sxpid-count-atom-bridge
)
FRAGMENT=pid-discovery-verification-and-durability-blueprint-header

make_fixture() {
  local fixture="$1"
  local stem
  mkdir -p "$fixture/scripts" "$fixture/audit/evidence" \
    "$fixture/audit/formal/latex" "$fixture/output/pdf"
  cp "$PRODUCTION_GATE" "$fixture/scripts/check-formal-pdf-set.sh"
  chmod 0755 "$fixture/scripts/check-formal-pdf-set.sh"
  for stem in "${LATEX_STANDALONE[@]}"; do
    cp "$ROOT/audit/formal/latex/$stem.tex" "$fixture/audit/formal/latex/$stem.tex"
  done
  local markdown_source
  for markdown_source in "${MARKDOWN_SOURCES[@]}"; do
    cp "$ROOT/$markdown_source" "$fixture/$markdown_source"
  done
  for stem in "${STANDALONE[@]}"; do
    cp "$ROOT/output/pdf/$stem.pdf" "$fixture/output/pdf/$stem.pdf"
  done
  cp "$ROOT/audit/formal/latex/$FRAGMENT.tex" \
    "$fixture/audit/formal/latex/$FRAGMENT.tex"
}

run_inventory() {
  local fixture="$1"
  if [[ -n "${PID_RS_SELF_TEST_TMP_OVERRIDE:-}" ]]; then
    (CDPATH="${PID_RS_SELF_TEST_CDPATH_OVERRIDE:-}" cd -- "$fixture" && \
      CDPATH="${PID_RS_SELF_TEST_CDPATH_OVERRIDE:-}" \
      PID_RS_PDF_GATE_TMPDIR="$PID_RS_SELF_TEST_TMP_OVERRIDE" \
      "$fixture/scripts/check-formal-pdf-set.sh" --inventory-only)
  else
    (CDPATH="${PID_RS_SELF_TEST_CDPATH_OVERRIDE:-}" cd -- "$fixture" && \
      CDPATH="${PID_RS_SELF_TEST_CDPATH_OVERRIDE:-}" \
      "$fixture/scripts/check-formal-pdf-set.sh" --inventory-only)
  fi
}

PASS_COUNT=0
pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  printf 'ok %d - %s\n' "$PASS_COUNT" "$1"
}

expect_success() {
  local label="$1"
  local fixture="$2"
  local temp_override="${3:-}"
  local cdpath_override="${4:-}"
  local stdout="$TEST_ROOT/success-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/success-$PASS_COUNT.stderr"
  if ! PID_RS_SELF_TEST_TMP_OVERRIDE="$temp_override" \
      PID_RS_SELF_TEST_CDPATH_OVERRIDE="$cdpath_override" \
      run_inventory "$fixture" >"$stdout" 2>"$stderr"; then
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
  local temp_override="${4:-}"
  local cdpath_override="${5:-}"
  local stdout="$TEST_ROOT/failure-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/failure-$PASS_COUNT.stderr"
  if PID_RS_SELF_TEST_TMP_OVERRIDE="$temp_override" \
      PID_RS_SELF_TEST_CDPATH_OVERRIDE="$cdpath_override" \
      run_inventory "$fixture" >"$stdout" 2>"$stderr"; then
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

validate_temporary_root_custody() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required = (
    'FORMAL_TMP_ROOT_INPUT="${PID_RS_PDF_GATE_TMPDIR:-${TMPDIR:-/tmp}}"',
    'FORMAL_TMP_ROOT="$(CDPATH=\'\' cd -- "$FORMAL_TMP_ROOT_INPUT" && pwd -P)"',
    'export TMPDIR="$FORMAL_TMP_ROOT"',
    'WORKFLOW_GATE_TMPDIR="$FORMAL_TMP_ROOT"',
)
for literal in required:
    if text.count(literal) != 1:
        raise SystemExit(f"temporary-root custody literal drifted: {literal!r}")
positions = [text.index(literal) for literal in required]
if positions != sorted(positions):
    raise SystemExit("temporary-root custody operations are out of order")
PY
}

validate_workflow_diagnostic_custody() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required = (
    'WORKFLOW_GATE_STDERR="$(mktemp "$FORMAL_TMP_ROOT/pid-rs-formal-workflow-stderr.XXXXXX")"',
    'cleanup_workflow_gate_stderr() {',
    'local status="$1"',
    'local cleanup_failed=0',
    'rm -f -- "$WORKFLOW_GATE_STDERR" || cleanup_failed=1',
    'if [[ "$status" -eq 0 && "$cleanup_failed" -ne 0 ]]; then\n    status=1\n  fi\n  exit "$status"\n}',
    'trap \'cleanup_workflow_gate_stderr "$?"\' EXIT',
    'trap \'cleanup_workflow_gate_stderr 130\' INT',
    'trap \'cleanup_workflow_gate_stderr 143\' TERM',
    '2>"$WORKFLOW_GATE_STDERR"; then',
    'WORKFLOW_GATE_STATUS=0',
    'WORKFLOW_GATE_STATUS=$?',
    'if [[ "$WORKFLOW_GATE_STATUS" -ne 0 || -s "$WORKFLOW_GATE_STDERR" ]]; then',
    'cat "$WORKFLOW_GATE_STDERR" >&2',
    'formal PDF set: workflow gate emitted a diagnostic despite status zero',
    'exit "$WORKFLOW_GATE_STATUS"',
    'rm -f -- "$WORKFLOW_GATE_STDERR"\nWORKFLOW_GATE_STDERR=""\ntrap - EXIT INT TERM',
)
for literal in required:
    if text.count(literal) != 1:
        raise SystemExit(f"workflow diagnostic-custody literal drifted: {literal!r}")
positions = [text.index(literal) for literal in required]
if positions != sorted(positions):
    raise SystemExit("workflow diagnostic-custody operations are out of order")
PY
}

validate_publication_link_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
inventory_exit = '''if [[ "$MODE" == "--inventory-only" ]]; then
  echo "OK: standalone-paper, renderer-fragment, and PDF inventories are exact and direct-regular"
  exit 0
fi
'''
required = (
    "python3 -I -B scripts/check-publication-links.py",
    "python3 -O -I -B scripts/check-publication-links.py",
    "python3 -I -B scripts/check-publication-links-self-test.py",
    "python3 -O -I -B scripts/check-publication-links-self-test.py",
    "scripts/check-formal-pdf-set-self-test.sh",
)
if text.count(inventory_exit) != 1:
    raise SystemExit("publication-link inventory boundary drifted")
lines = text.splitlines()
for literal in required:
    if lines.count(literal) != 1:
        raise SystemExit(f"publication-link gate invocation drifted: {literal!r}")
required_block = inventory_exit + "\n" + "\n".join(required) + "\n"
if text.count(required_block) != 1:
    raise SystemExit(
        "publication-link gates are not one exact contiguous post-inventory block"
    )
PY
}

validate_numerical_self_test_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected_block = '''scripts/check-numerical-assurance-pdf.sh "$MODE"
scripts/check-numerical-assurance-pdf-self-test.sh
scripts/check-pid2-represented-coordinate-assurance-pdf.sh "$MODE"
'''
if text.count(expected_block) != 1:
    raise SystemExit(
        "numerical-assurance gate and hostile self-test are not one exact contiguous block"
    )
PY
}

validate_blueprint_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
required_lines = (
    "scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh",
    "  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact",
    "  if scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain; then",
    '  if [[ "$BLUEPRINT_CROSS_STATUS" -ne 2 ]]; then',
)
lines = text.splitlines()
for literal in required_lines:
    if lines.count(literal) != 1:
        raise SystemExit(f"blueprint gate invocation drifted: {literal!r}")
expected_block = '''scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh

# The root blueprint has an exact committed-byte relation only.  Cross-toolchain acceptance would
# require a separately reviewed profile, so CI proves that the requested cross mode refuses rather
# than treating text or geometry as a substitute equivalence relation.
if [[ "$MODE" == "--exact" ]]; then
  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact
else
  if scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain; then
    echo "formal PDF set: blueprint cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    BLUEPRINT_CROSS_STATUS=$?
  fi
  if [[ "$BLUEPRINT_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: blueprint cross-toolchain refusal returned $BLUEPRINT_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi
'''
if text.count(expected_block) != 1:
    raise SystemExit(
        "blueprint exact-only gate is not one unweakened contiguous block"
    )
PY
}

validate_custody_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected_record_block = '''scripts/check-post-publication-custody-pdf-self-test.sh
python3 -I -S -B scripts/check-post-publication-custody.py
python3 -O -I -S -B scripts/check-post-publication-custody.py
python3 -I -S -B scripts/check-post-publication-custody-self-test.py
python3 -O -I -S -B scripts/check-post-publication-custody-self-test.py
'''
if text.count(expected_record_block) != 1:
    raise SystemExit(
        "custody record gates and hostile suites are not one exact contiguous block"
    )
for literal in (
    '  scripts/check-post-publication-custody-pdf.sh --exact',
    '  if scripts/check-post-publication-custody-pdf.sh --cross-toolchain; then',
    '  if [[ "$CUSTODY_CROSS_STATUS" -ne 2 ]]; then',
):
    if text.splitlines().count(literal) != 1:
        raise SystemExit(f"custody PDF gate invocation drifted: {literal!r}")
PY
}

validate_terminal_success_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected = '''if [[ "$MODE" == "--exact" ]]; then
  echo "OK: every declared formal paper has a warning-free same-toolchain result; committed-byte relations are exact, including the root blueprint and post-publication custody receipt, and the source and renderer-fragment inventories are exact"
else
  echo "OK: every declared paper with a reviewed cross-toolchain profile passed its warning-free bounded gate; the root blueprint and post-publication custody receipt intentionally have no accepted cross-toolchain relation, and both status-2 refusals plus the source and renderer-fragment inventories are exact"
fi
'''
if text.count(expected) != 1:
    raise SystemExit("terminal exact/cross success contract drifted")
PY
}

make_workflow_cleanup_probe() {
  python3 -I -S - "$PRODUCTION_GATE" "$1" <<'PY'
from pathlib import Path
import sys


source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = "cleanup_workflow_gate_stderr() {\n"
end = "trap 'cleanup_workflow_gate_stderr 143' TERM\n"
if source.count(start) != 1 or source.count(end) != 1:
    raise SystemExit("workflow cleanup probe extraction anchors drifted")
begin = source.index(start)
finish = source.index(end, begin) + len(end)
block = source[begin:finish]
probe = f'''#!/usr/bin/env bash
set -euo pipefail
FORMAL_TMP_ROOT="$1"
WORKFLOW_GATE_STDERR="$2"
{block}case "$3" in
  success) exit 0 ;;
  ordinary) exit 7 ;;
  int) kill -INT "$$"; exit 99 ;;
  term) kill -TERM "$$"; exit 99 ;;
  *) exit 98 ;;
esac
'''
Path(sys.argv[2]).write_text(probe, encoding="utf-8", newline="\n")
PY
  chmod 0755 "$1"
}

run_workflow_cleanup_probe() {
  local probe="$1"
  local label="$2"
  local mode="$3"
  local expected_status="$4"
  local probe_root="$TEST_ROOT/workflow-cleanup-$mode"
  local diagnostic="$probe_root/pid-rs-formal-workflow-stderr.probe"
  local stdout="$probe_root/stdout"
  local stderr="$probe_root/stderr"
  local status
  mkdir -p "$probe_root"
  printf 'bounded diagnostic\n' >"$diagnostic"
  if bash --noprofile --norc "$probe" "$probe_root" "$diagnostic" "$mode" \
      >"$stdout" 2>"$stderr"; then
    status=0
  else
    status=$?
  fi
  if [[ "$status" -ne "$expected_status" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label returned $status, expected $expected_status" >&2
    return 1
  fi
  if [[ -e "$diagnostic" || -L "$diagnostic" ]]; then
    echo "$CHECK_NAME: $label left its diagnostic file behind" >&2
    return 1
  fi
  if [[ -s "$stdout" || -s "$stderr" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label emitted an unexpected diagnostic" >&2
    return 1
  fi
  pass "$label"
}

run_workflow_cleanup_failure_probe() {
  local probe="$1"
  local label="$2"
  local probe_root="$TEST_ROOT/workflow-cleanup-forced-failure"
  local diagnostic="$probe_root/pid-rs-formal-workflow-stderr.probe"
  local stdout="$probe_root/stdout"
  local stderr="$probe_root/stderr"
  local status
  mkdir -p "$diagnostic"
  if bash --noprofile --norc "$probe" "$probe_root" "$diagnostic" success \
      >"$stdout" 2>"$stderr"; then
    status=0
  else
    status=$?
  fi
  if [[ "$status" -ne 1 ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label returned $status, expected 1" >&2
    return 1
  fi
  if [[ ! -d "$diagnostic" || -L "$diagnostic" ]]; then
    echo "$CHECK_NAME: $label did not retain the forced-failure directory" >&2
    return 1
  fi
  if [[ -s "$stdout" || ! -s "$stderr" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label did not expose the cleanup failure" >&2
    return 1
  fi
  pass "$label"
}

make_workflow_decision_probe() {
  python3 -I -S - "$PRODUCTION_GATE" "$1" <<'PY'
from pathlib import Path
import sys


source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = 'if [[ "$WORKFLOW_GATE_STATUS" -ne 0 || -s "$WORKFLOW_GATE_STDERR" ]]; then\n'
end = '  exit "$WORKFLOW_GATE_STATUS"\nfi\n'
if source.count(start) != 1 or source.count(end) != 1:
    raise SystemExit("workflow decision probe extraction anchors drifted")
begin = source.index(start)
finish = source.index(end, begin) + len(end)
block = source[begin:finish]
probe = f'''#!/usr/bin/env bash
set -euo pipefail
WORKFLOW_GATE_STATUS="$1"
WORKFLOW_GATE_STDERR="$2"
{block}exit 0
'''
Path(sys.argv[2]).write_text(probe, encoding="utf-8", newline="\n")
PY
  chmod 0755 "$1"
}

run_workflow_decision_probe() {
  local probe="$1"
  local label="$2"
  local mode="$3"
  local child_status="$4"
  local expected_status="$5"
  local probe_root="$TEST_ROOT/workflow-decision-$mode"
  local diagnostic="$probe_root/pid-rs-formal-workflow-stderr.probe"
  local stdout="$probe_root/stdout"
  local stderr="$probe_root/stderr"
  local status
  mkdir -p "$probe_root"
  : >"$diagnostic"
  if [[ "$mode" == *-diagnostic ]]; then
    printf 'bounded decision diagnostic\n' >"$diagnostic"
  fi
  if bash --noprofile --norc "$probe" "$child_status" "$diagnostic" \
      >"$stdout" 2>"$stderr"; then
    status=0
  else
    status=$?
  fi
  if [[ "$status" -ne "$expected_status" || -s "$stdout" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: $label returned $status, expected $expected_status" >&2
    return 1
  fi
  case "$mode" in
    zero-silent)
      if [[ -s "$stderr" ]]; then
        cat "$stderr" >&2
        echo "$CHECK_NAME: $label emitted a diagnostic" >&2
        return 1
      fi
      ;;
    zero-diagnostic)
      if ! grep -Fq 'bounded decision diagnostic' "$stderr" || \
          ! grep -Fq 'workflow gate emitted a diagnostic despite status zero' "$stderr" || \
          grep -Fq 'workflow gate failed with status' "$stderr"; then
        cat "$stderr" >&2
        echo "$CHECK_NAME: $label did not preserve the status-zero diagnostic branch" >&2
        return 1
      fi
      ;;
    nonzero-silent)
      if ! grep -Fq 'workflow gate failed with status 7' "$stderr" || \
          grep -Fq 'bounded decision diagnostic' "$stderr"; then
        cat "$stderr" >&2
        echo "$CHECK_NAME: $label did not preserve the silent child failure" >&2
        return 1
      fi
      ;;
    nonzero-diagnostic)
      if ! grep -Fq 'bounded decision diagnostic' "$stderr" || \
          ! grep -Fq 'workflow gate failed with status 7' "$stderr"; then
        cat "$stderr" >&2
        echo "$CHECK_NAME: $label did not replay the causal child failure" >&2
        return 1
      fi
      ;;
    *)
      echo "$CHECK_NAME: unknown workflow decision probe mode: $mode" >&2
      return 1
      ;;
  esac
  pass "$label"
}

fixture="$TEST_ROOT/baseline"
make_fixture "$fixture"
expect_success "declared source-typed inventory is accepted" "$fixture"
expect_success "slash-terminated temporary root is canonicalized" "$fixture" "$TEST_ROOT/"
expect_failure "filesystem root is rejected as temporary root" "$fixture" \
  "refusing filesystem root as temporary root" "/"
expect_failure "absent temporary root is rejected" "$fixture" \
  "cannot canonicalize temporary root" "$TEST_ROOT/absent"

mkdir -p "$fixture/relative-temp" "$TEST_ROOT/hostile-cdpath/relative-temp"
expect_success "relative temporary root ignores hostile CDPATH" "$fixture" \
  "relative-temp" "$TEST_ROOT/hostile-cdpath"

if ! validate_temporary_root_custody "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production temporary-root custody was rejected" >&2
  exit 1
fi
pass "temporary-root resolution is CDPATH-isolated and shared"

if ! validate_publication_link_gate_wiring "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production publication-link wiring was rejected" >&2
  exit 1
fi
pass "staged publication links and hostile fixtures run in normal and optimized Python"

if ! validate_numerical_self_test_wiring "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production numerical-assurance hostile-suite wiring was rejected" >&2
  exit 1
fi
pass "numerical-assurance gate and hostile self-test are contiguous"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2]
after = sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(before) != 1:
    raise SystemExit(f"numerical self-test mutation anchor drifted: {before!r}")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_numerical_self_test_wiring "$case_file" \
      >"$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: numerical hostile-suite bypass was accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "numerical-assurance gate and hostile self-test" \
      "$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.stdout" \
      "$TEST_ROOT/numerical-self-test-wiring-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: numerical hostile-suite bypass failed for a noncausal reason" >&2
    exit 1
  fi
  pass "$label"
done <<'EOF'
removing the numerical-assurance hostile self-test is rejected	scripts/check-numerical-assurance-pdf-self-test.sh	# numerical hostile suite omitted
weakening the numerical-assurance hostile self-test with or-true is rejected	scripts/check-numerical-assurance-pdf-self-test.sh	scripts/check-numerical-assurance-pdf-self-test.sh || true
EOF

for removed_invocation in \
    "python3 -I -B scripts/check-publication-links.py" \
    "python3 -O -I -B scripts/check-publication-links.py" \
    "python3 -I -B scripts/check-publication-links-self-test.py" \
    "python3 -O -I -B scripts/check-publication-links-self-test.py"; do
  case_file="$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$removed_invocation" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
literal = sys.argv[2]
text = path.read_text(encoding="utf-8")
line = literal + "\n"
if text.count(line) != 1:
    raise SystemExit(f"publication-link mutation anchor drifted: {literal!r}")
path.write_text(text.replace(line, "", 1), encoding="utf-8", newline="\n")
PY
  if validate_publication_link_gate_wiring "$case_file" \
      >"$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: missing publication-link invocation was accepted: $removed_invocation" >&2
    exit 1
  fi
  if ! grep -Fq "publication-link gate invocation drifted" \
      "$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.stdout" \
      "$TEST_ROOT/publication-link-wiring-bypass-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: publication-link bypass failed for a noncausal reason" >&2
    exit 1
  fi
  pass "removing $removed_invocation is rejected"
done

for bypass_kind in suffix-or-true prefix-false-and; do
  case_file="$TEST_ROOT/publication-link-wiring-$bypass_kind.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$bypass_kind" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
bypass_kind = sys.argv[2]
text = path.read_text(encoding="utf-8")
invocation = "python3 -I -B scripts/check-publication-links.py"
line = invocation + "\n"
if text.count(line) != 1:
    raise SystemExit("publication-link bypass mutation anchor drifted")
if bypass_kind == "suffix-or-true":
    replacement = invocation + " || true\n"
elif bypass_kind == "prefix-false-and":
    replacement = "false && " + invocation + "\n"
else:
    raise SystemExit(f"unknown bypass mutation: {bypass_kind}")
path.write_text(text.replace(line, replacement, 1), encoding="utf-8", newline="\n")
PY
  if validate_publication_link_gate_wiring "$case_file" \
      >"$TEST_ROOT/publication-link-wiring-$bypass_kind.stdout" \
      2>"$TEST_ROOT/publication-link-wiring-$bypass_kind.stderr"; then
    echo "$CHECK_NAME: publication-link $bypass_kind bypass was accepted" >&2
    exit 1
  fi
  if ! grep -Fq "publication-link gate invocation drifted" \
      "$TEST_ROOT/publication-link-wiring-$bypass_kind.stderr"; then
    cat "$TEST_ROOT/publication-link-wiring-$bypass_kind.stdout" \
      "$TEST_ROOT/publication-link-wiring-$bypass_kind.stderr" >&2
    echo "$CHECK_NAME: publication-link $bypass_kind failed for a noncausal reason" >&2
    exit 1
  fi
  pass "publication-link $bypass_kind bypass is rejected"
done

case_file="$TEST_ROOT/publication-link-wiring-conditional.sh"
cp "$PRODUCTION_GATE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
first = "python3 -I -B scripts/check-publication-links.py\n"
last = "python3 -O -I -B scripts/check-publication-links-self-test.py\n"
if text.count(first) != 1 or text.count(last) != 1:
    raise SystemExit("publication-link conditional mutation anchors drifted")
text = text.replace(
    first,
    'if [[ "$MODE" == "--exact" ]]; then\n' + first,
    1,
)
text = text.replace(last, last + "fi\n", 1)
path.write_text(text, encoding="utf-8", newline="\n")
PY
if validate_publication_link_gate_wiring "$case_file" \
    >"$TEST_ROOT/publication-link-wiring-conditional.stdout" \
    2>"$TEST_ROOT/publication-link-wiring-conditional.stderr"; then
  echo "$CHECK_NAME: conditional publication-link bypass was accepted" >&2
  exit 1
fi
if ! grep -Fq "publication-link gates are not one exact contiguous post-inventory block" \
    "$TEST_ROOT/publication-link-wiring-conditional.stderr"; then
  cat "$TEST_ROOT/publication-link-wiring-conditional.stdout" \
    "$TEST_ROOT/publication-link-wiring-conditional.stderr" >&2
  echo "$CHECK_NAME: conditional publication-link bypass failed for a noncausal reason" >&2
  exit 1
fi
pass "conditional exact-only publication-link bypass is rejected"

if ! validate_blueprint_gate_wiring "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production blueprint exact-only wiring was rejected" >&2
  exit 1
fi
pass "blueprint self-test, exact relation, and status-2 cross refusal are contiguous"

if ! validate_custody_gate_wiring "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production custody wiring was rejected" >&2
  exit 1
fi
pass "custody record/PDF gates and hostile suites are contiguous"

if ! validate_terminal_success_contract "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production terminal success contract was rejected" >&2
  exit 1
fi
pass "terminal success messages distinguish profiled and exact-only papers"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/terminal-success-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2]
after = sys.argv[3]
text = path.read_text(encoding="utf-8")
if text.count(before) != 1:
    raise SystemExit(f"terminal-success mutation anchor drifted: {before!r}")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_terminal_success_contract "$case_file" \
      >"$TEST_ROOT/terminal-success-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/terminal-success-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: terminal-success drift was accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "terminal exact/cross success contract drifted" \
      "$TEST_ROOT/terminal-success-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/terminal-success-$PASS_COUNT.stdout" \
      "$TEST_ROOT/terminal-success-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: terminal-success mutation failed for a noncausal reason" >&2
    exit 1
  fi
  pass "$label"
done <<'CASES'
exact success message cannot omit the custody receipt	including the root blueprint and post-publication custody receipt	including the root blueprint
cross success message cannot call all papers profiled	every declared paper with a reviewed cross-toolchain profile	every declared paper
CASES

for removed_invocation in \
    "scripts/check-post-publication-custody-pdf-self-test.sh" \
    "python3 -I -S -B scripts/check-post-publication-custody.py" \
    "python3 -O -I -S -B scripts/check-post-publication-custody.py" \
    "python3 -I -S -B scripts/check-post-publication-custody-self-test.py" \
    "python3 -O -I -S -B scripts/check-post-publication-custody-self-test.py"; do
  case_file="$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$removed_invocation" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
line = sys.argv[2] + "\n"
text = path.read_text(encoding="utf-8")
if text.count(line) != 1:
    raise SystemExit(f"custody mutation anchor drifted: {line!r}")
path.write_text(text.replace(line, "", 1), encoding="utf-8", newline="\n")
PY
  if validate_custody_gate_wiring "$case_file" \
      >"$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: missing custody invocation was accepted: $removed_invocation" >&2
    exit 1
  fi
  if ! grep -Fq "custody record gates and hostile suites" \
      "$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.stdout" \
      "$TEST_ROOT/custody-gate-wiring-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: custody bypass failed for a noncausal reason" >&2
    exit 1
  fi
  pass "removing $removed_invocation is rejected"
done

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
before = sys.argv[2].replace(r"\n", "\n")
after = sys.argv[3].replace(r"\n", "\n")
text = path.read_text(encoding="utf-8")
if text.count(before) != 1:
    raise SystemExit(f"blueprint mutation anchor drifted: {before!r}")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_blueprint_gate_wiring "$case_file" \
      >"$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.stdout" \
      2>"$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: blueprint gate bypass was accepted: $label" >&2
    exit 1
  fi
  if ! grep -Eq \
      'blueprint (gate invocation drifted|exact-only gate is not one unweakened contiguous block)' \
      "$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.stdout" \
      "$TEST_ROOT/blueprint-gate-wiring-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: blueprint gate bypass failed for a noncausal reason" >&2
    exit 1
  fi
  pass "$label"
done <<'EOF'
removing the blueprint hostile self-test is rejected	scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh	# blueprint self-test omitted
changing the blueprint exact invocation to cross mode is rejected	  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact	  scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain
changing the blueprint cross probe to exact mode is rejected	  if scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain; then	  if scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact; then
weakening the blueprint exact invocation with or-true is rejected	  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact	  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact || true
inverting the blueprint cross refusal probe is rejected	  if scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain; then	  if ! scripts/check-pid-discovery-verification-blueprint-pdf.sh --cross-toolchain; then
changing the blueprint cross refusal contract from status 2 is rejected	  if [[ "$BLUEPRINT_CROSS_STATUS" -ne 2 ]]; then	  if [[ "$BLUEPRINT_CROSS_STATUS" -ne 1 ]]; then
conditionally skipping the blueprint exact branch is rejected	if [[ "$MODE" == "--exact" ]]; then\n  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact	if [[ "$MODE" == "--cross-toolchain" ]]; then\n  scripts/check-pid-discovery-verification-blueprint-pdf.sh --exact
EOF

case_file="$TEST_ROOT/temporary-root-cdpath-bypass.sh"
cp "$PRODUCTION_GATE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before = 'FORMAL_TMP_ROOT="$(CDPATH=\'\' cd -- "$FORMAL_TMP_ROOT_INPUT" && pwd -P)"'
after = 'FORMAL_TMP_ROOT="$(cd "$FORMAL_TMP_ROOT_INPUT" && pwd -P)"'
if text.count(before) != 1:
    raise SystemExit("temporary-root CDPATH mutation anchor drifted")
path.write_text(text.replace(before, after), encoding="utf-8", newline="\n")
PY
if validate_temporary_root_custody "$case_file" \
    >"$TEST_ROOT/temporary-root-cdpath-bypass.stdout" \
    2>"$TEST_ROOT/temporary-root-cdpath-bypass.stderr"; then
  echo "$CHECK_NAME: temporary-root CDPATH bypass was accepted" >&2
  exit 1
fi
if ! grep -Fq "temporary-root custody literal drifted" \
    "$TEST_ROOT/temporary-root-cdpath-bypass.stderr"; then
  cat "$TEST_ROOT/temporary-root-cdpath-bypass.stdout" \
    "$TEST_ROOT/temporary-root-cdpath-bypass.stderr" >&2
  echo "$CHECK_NAME: temporary-root CDPATH bypass failed for a noncausal reason" >&2
  exit 1
fi
pass "temporary-root CDPATH isolation bypass is rejected"

if ! validate_workflow_diagnostic_custody "$PRODUCTION_GATE"; then
  echo "$CHECK_NAME: production workflow diagnostic custody was rejected" >&2
  exit 1
fi
pass "workflow child requires zero status and silent stderr"

case_file="$TEST_ROOT/workflow-diagnostic-bypass.sh"
cp "$PRODUCTION_GATE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys


path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before = 'if [[ "$WORKFLOW_GATE_STATUS" -ne 0 || -s "$WORKFLOW_GATE_STDERR" ]]; then'
after = 'if [[ "$WORKFLOW_GATE_STATUS" -ne 0 ]]; then'
if text.count(before) != 1:
    raise SystemExit("workflow diagnostic guard mutation anchor drifted")
path.write_text(text.replace(before, after), encoding="utf-8", newline="\n")
PY
if validate_workflow_diagnostic_custody "$case_file" \
    >"$TEST_ROOT/workflow-diagnostic-bypass.stdout" \
    2>"$TEST_ROOT/workflow-diagnostic-bypass.stderr"; then
  echo "$CHECK_NAME: workflow diagnostic bypass was accepted" >&2
  exit 1
fi
if ! grep -Fq "workflow diagnostic-custody literal drifted" \
    "$TEST_ROOT/workflow-diagnostic-bypass.stderr"; then
  cat "$TEST_ROOT/workflow-diagnostic-bypass.stdout" \
    "$TEST_ROOT/workflow-diagnostic-bypass.stderr" >&2
  echo "$CHECK_NAME: workflow diagnostic bypass failed for a noncausal reason" >&2
  exit 1
fi
pass "workflow status-zero stderr bypass is rejected"

cleanup_probe="$TEST_ROOT/workflow-cleanup-probe.sh"
make_workflow_cleanup_probe "$cleanup_probe"
run_workflow_cleanup_probe "$cleanup_probe" \
  "workflow cleanup preserves success and removes its diagnostic" success 0
run_workflow_cleanup_probe "$cleanup_probe" \
  "workflow cleanup preserves an ordinary nonzero status" ordinary 7
run_workflow_cleanup_probe "$cleanup_probe" \
  "workflow cleanup preserves direct SIGINT as status 130" int 130
run_workflow_cleanup_probe "$cleanup_probe" \
  "workflow cleanup preserves direct SIGTERM as status 143" term 143
run_workflow_cleanup_failure_probe "$cleanup_probe" \
  "workflow cleanup failure escalates successful status to one"

decision_probe="$TEST_ROOT/workflow-decision-probe.sh"
make_workflow_decision_probe "$decision_probe"
run_workflow_decision_probe "$decision_probe" \
  "workflow decision accepts zero status with silent stderr" zero-silent 0 0
run_workflow_decision_probe "$decision_probe" \
  "workflow decision rejects zero status with stderr" zero-diagnostic 0 1
run_workflow_decision_probe "$decision_probe" \
  "workflow decision preserves nonzero status with silent stderr" nonzero-silent 7 7
run_workflow_decision_probe "$decision_probe" \
  "workflow decision preserves nonzero status while replaying stderr" nonzero-diagnostic 7 7

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

for markdown_source in "${MARKDOWN_SOURCES[@]}"; do
  source_stem="${markdown_source%.md}"

  fixture="$TEST_ROOT/missing-markdown-source-$source_stem"
  make_fixture "$fixture"
  mv "$fixture/$markdown_source" "$fixture/removed-markdown-source.md"
  expect_failure "missing Markdown paper source $markdown_source is rejected" "$fixture" \
    "Markdown source is not a direct regular file"

  fixture="$TEST_ROOT/symbolic-markdown-source-$source_stem"
  make_fixture "$fixture"
  mv "$fixture/$markdown_source" "$fixture/markdown-source-target.md"
  ln -s markdown-source-target.md "$fixture/$markdown_source"
  expect_failure "symbolic Markdown paper source $markdown_source is rejected" "$fixture" \
    "Markdown source is not a direct regular file"
done

echo "OK: $PASS_COUNT formal-PDF typed-inventory controls passed"
