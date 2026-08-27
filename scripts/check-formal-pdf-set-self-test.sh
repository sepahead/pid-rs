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
MARKDOWN_SOURCE=SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md
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
  sxpid3-source-marginal-and-bounded-audit
  two-source-sxpid-count-atom-bridge
)
FRAGMENT=pid-discovery-verification-and-durability-blueprint-header

make_fixture() {
  local fixture="$1"
  local stem
  mkdir -p "$fixture/scripts" "$fixture/audit/formal/latex" "$fixture/output/pdf"
  cp "$PRODUCTION_GATE" "$fixture/scripts/check-formal-pdf-set.sh"
  chmod 0755 "$fixture/scripts/check-formal-pdf-set.sh"
  for stem in "${LATEX_STANDALONE[@]}"; do
    cp "$ROOT/audit/formal/latex/$stem.tex" "$fixture/audit/formal/latex/$stem.tex"
  done
  cp "$ROOT/$MARKDOWN_SOURCE" "$fixture/$MARKDOWN_SOURCE"
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

fixture="$TEST_ROOT/missing-markdown-source"
make_fixture "$fixture"
mv "$fixture/$MARKDOWN_SOURCE" "$fixture/removed-markdown-source.md"
expect_failure "missing Markdown paper source is rejected" "$fixture" \
  "Markdown source is not a direct regular file"

fixture="$TEST_ROOT/symbolic-markdown-source"
make_fixture "$fixture"
mv "$fixture/$MARKDOWN_SOURCE" "$fixture/markdown-source-target.md"
ln -s markdown-source-target.md "$fixture/$MARKDOWN_SOURCE"
expect_failure "symbolic Markdown paper source is rejected" "$fixture" \
  "Markdown source is not a direct regular file"

echo "OK: $PASS_COUNT formal-PDF typed-inventory controls passed"
