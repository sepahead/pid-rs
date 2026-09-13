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
  audit/evidence/finite-target-copy-mgw-synergy.md
  audit/evidence/mgw-fixed-world-added-information-2026-09-09.md
  NUMERICAL_ASSURANCE.md
  PID2_REPRESENTED_COORDINATE_ASSURANCE.md
  PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md
  audit/evidence/post-publication-custody-2026-09-02.md
  audit/formal/lean-prefix-mgw-bias/EXPOSITION.md
  audit/formal/lean-prefix-mgw-bias/SUMMARY.md
  audit/formal/lean-prefix-mgw-mean/EXPOSITION.current.md
  audit/evidence/real-occupancy-sensors-example-2026-09-08.md
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
  finite-target-copy-mgw-synergy
  mathematical-problem-solving-workflow
  mgw-fixed-world-added-information
  numerical-assurance
  pid2-represented-coordinate-assurance
  pid-sensor-placement-and-galadriel-guide
  post-publication-custody-2026-09-02
  prefix-mgw-bias
  prefix-mgw-bias-summary
  prefix-mgw-mean
  recorded-office-sensors
  support-change-tolerant-averaged-sxpid-continuity
  sxpid3-source-marginal-and-bounded-audit
  two-source-sxpid-count-atom-bridge
)
FRAGMENT=pid-discovery-verification-and-durability-blueprint-header

make_fixture() {
  local fixture="$1"
  local stem
  mkdir -p "$fixture/scripts" "$fixture/audit/evidence" \
    "$fixture/audit/formal/latex" "$fixture/output/pdf" \
    "$fixture/audit/formal/lean-prefix-mgw-mean" \
    "$fixture/audit/formal/lean-prefix-mgw-bias"
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
    'WORKFLOW_GATE_XDG_ROOT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-formal-workflow-xdg.XXXXXX")"',
    'WORKFLOW_GATE_XDG_CONFIG="$WORKFLOW_GATE_XDG_ROOT/config"',
    'WORKFLOW_GATE_XDG_CACHE="$WORKFLOW_GATE_XDG_ROOT/cache"',
    'mkdir -m 0700 -- "$WORKFLOW_GATE_XDG_CONFIG" "$WORKFLOW_GATE_XDG_CACHE"',
    '"XDG_CONFIG_HOME=$WORKFLOW_GATE_XDG_CONFIG"',
    '"XDG_CACHE_HOME=$WORKFLOW_GATE_XDG_CACHE"',
)
for literal in required:
    if text.count(literal) != 1:
        raise SystemExit(f"temporary-root custody literal drifted: {literal!r}")
positions = [text.index(literal) for literal in required]
if positions != sorted(positions):
    raise SystemExit("temporary-root custody operations are out of order")
for forbidden in ("WORKFLOW_GATE_HOME", "PID_RS_PDF_GATE_HOME", '"HOME='):
    if forbidden in text:
        raise SystemExit(f"workflow environment reassigns HOME: {forbidden!r}")
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
    'case "${WORKFLOW_GATE_XDG_ROOT:-}" in',
    'formal PDF set: refusing to remove unexpected workflow XDG root',
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
    'rm -f -- "$WORKFLOW_GATE_STDERR"\nWORKFLOW_GATE_STDERR=""',
    'rm -rf -- "$WORKFLOW_GATE_XDG_ROOT"\nWORKFLOW_GATE_XDG_ROOT=""\ntrap - EXIT INT TERM',
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
early_bias_end = '  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind summary --exact --check --registration "$PID_RS_BIAS_SUMMARY_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"\nfi\n\n'
required_block = early_bias_end + "\n".join(required) + "\n"
if text.count(required_block) != 1:
    raise SystemExit(
        "publication-link gates are not one exact contiguous post-inventory block"
    )
if text.index(inventory_exit) > text.index(required_block):
    raise SystemExit("publication-link inventory boundary drifted")
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

validate_mean_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected = '# The new mean exposition admits exact reviewed bytes only; retain fresh build evidence.\nif [[ "$MODE" == "--exact" ]]; then\n  MEAN_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mean-publication.XXXXXX")"\n  python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact --check --work-dir "$MEAN_BUILD_PARENT/build"\nelse\n  if python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --cross-toolchain; then\n    echo "formal PDF set: mean exposition cross-toolchain mode unexpectedly accepted" >&2\n    exit 1\n  else\n    MEAN_CROSS_STATUS=$?\n  fi\n  if [[ "$MEAN_CROSS_STATUS" -ne 2 ]]; then\n    echo "formal PDF set: mean exposition refusal returned $MEAN_CROSS_STATUS, expected 2" >&2\n    exit 1\n  fi\nfi\n\n'
if text.count(expected) != 1:
    raise SystemExit("mean exposition exact/refusal wiring drifted")
PY
}

validate_occupancy_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected = '# Recorded sensors retain discovery separately from an admitted exact reference.\nOCCUPANCY_CONTROL_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-recorded-sensors-controls.XXXXXX")"\npython3 -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/normal"\npython3 -O -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/optimized"\nif [[ "$MODE" == "--exact" ]]; then\n  if [[ -z "${PID_RS_OCCUPANCY_TEX_ROOT:-}" ]]; then\n    echo "formal PDF set: exact recorded sensors require PID_RS_OCCUPANCY_TEX_ROOT" >&2\n    exit 2\n  fi\n  OCCUPANCY_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-recorded-sensors.XXXXXX")"\n  python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$OCCUPANCY_BUILD_PARENT/build"\nelse\n  if python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --cross-toolchain; then\n    echo "formal PDF set: recorded sensors cross-toolchain mode unexpectedly accepted" >&2\n    exit 1\n  else\n    OCCUPANCY_CROSS_STATUS=$?\n  fi\n  if [[ "$OCCUPANCY_CROSS_STATUS" -ne 2 ]]; then\n    echo "formal PDF set: recorded sensors refusal returned $OCCUPANCY_CROSS_STATUS, expected 2" >&2\n    exit 1\n  fi\nfi\n\n'
if text.count(expected) != 1:
    raise SystemExit("recorded-sensor exact/refusal/control wiring drifted")
PY
}

validate_mgw_fixed_world_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected = "# Finite MGW retains discovery separately from an admitted exact reference.\nMGW_FIXED_WORLD_CONTROL_PARENT=\"$(mktemp -d \"$FORMAL_TMP_ROOT/pid-rs-mgw-fixed-world-controls.XXXXXX\")\"\npython3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir \"$MGW_FIXED_WORLD_CONTROL_PARENT/normal\"\npython3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir \"$MGW_FIXED_WORLD_CONTROL_PARENT/optimized\"\nif [[ \"$MODE\" == \"--exact\" ]]; then\n  if [[ -z \"${PID_RS_MGW_FIXED_WORLD_TEX_ROOT:-}\" ]]; then\n    echo \"formal PDF set: exact finite MGW requires PID_RS_MGW_FIXED_WORLD_TEX_ROOT\" >&2\n    exit 2\n  fi\n  MGW_FIXED_WORLD_BUILD_PARENT=\"$(mktemp -d \"$FORMAL_TMP_ROOT/pid-rs-mgw-fixed-world.XXXXXX\")\"\n  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root \"$PID_RS_MGW_FIXED_WORLD_TEX_ROOT\" --work-dir \"$MGW_FIXED_WORLD_BUILD_PARENT/build\"\nelse\n  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then\n    echo \"formal PDF set: finite MGW cross-toolchain mode unexpectedly accepted\" >&2\n    exit 1\n  else\n    MGW_FIXED_WORLD_CROSS_STATUS=$?\n  fi\n  if [[ \"$MGW_FIXED_WORLD_CROSS_STATUS\" -ne 2 ]]; then\n    echo \"formal PDF set: finite MGW refusal returned $MGW_FIXED_WORLD_CROSS_STATUS, expected 2\" >&2\n    exit 1\n  fi\nfi\n\n"
if text.count(expected) != 1:
    raise SystemExit("finite MGW exact/refusal/control wiring drifted")
PY
}

validate_bias_gate_wiring() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
bindings = '''# Exact bias controls and reproduction consume actual pre-reviewed external registrations.
# Inventory and unsupported cross requests never require or manufacture them.
if [[ "$MODE" == "--exact" ]]; then
  : "${PID_RS_BIAS_PYTHON:?formal PDF set: exact bias work requires its pinned Python selector}"
  : "${PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION:?formal PDF set: normal bias-control registration is required}"
  : "${PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256:?formal PDF set: normal bias-control registration hash is required}"
  : "${PID_RS_BIAS_CONTROL_NORMAL_OUTPUT:?formal PDF set: normal bias-control output is required}"
  : "${PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION:?formal PDF set: optimized bias-control registration is required}"
  : "${PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256:?formal PDF set: optimized bias-control registration hash is required}"
  : "${PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT:?formal PDF set: optimized bias-control output is required}"
  : "${PID_RS_BIAS_FULL_REGISTRATION:?formal PDF set: full bias registration is required}"
  : "${PID_RS_BIAS_FULL_REGISTRATION_SHA256:?formal PDF set: full bias registration hash is required}"
  : "${PID_RS_BIAS_FULL_WORK_DIR:?formal PDF set: full bias work directory is required}"
  : "${PID_RS_BIAS_SUMMARY_REGISTRATION:?formal PDF set: summary bias registration is required}"
  : "${PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256:?formal PDF set: summary bias registration hash is required}"
  : "${PID_RS_BIAS_SUMMARY_WORK_DIR:?formal PDF set: summary bias work directory is required}"
fi
'''
inventory = '''if [[ "$MODE" == "--inventory-only" ]]; then
  echo "OK: standalone-paper, renderer-fragment, and PDF inventories are exact and direct-regular"
  exit 0
fi
'''
early = '''# Keep the finite registration clocks causal: run fresh inert bias controls and both exact bias
# reproductions before the older, longer aggregate gates.  These controls start no PDF/parser/proof
# child; the following builder calls retain their separate production meaning.
if [[ "$MODE" == "--exact" ]]; then
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"
  "$PID_RS_BIAS_PYTHON" -O -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind full --exact --check --registration "$PID_RS_BIAS_FULL_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_FULL_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_FULL_WORK_DIR"
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind summary --exact --check --registration "$PID_RS_BIAS_SUMMARY_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"
fi
'''
cross = '''# No alternate producer profile relates either bias PDF to a Linux/cross-toolchain build.
# Exact controls and reproduction already ran at the early finite-registration boundary above.
if [[ "$MODE" == "--cross-toolchain" ]]; then
  for BIAS_KIND in full summary; do
    if python3 -I -S -B scripts/build-prefix-mgw-bias-pdf.py --kind "$BIAS_KIND" --cross-toolchain; then
      echo "formal PDF set: $BIAS_KIND bias cross-toolchain mode unexpectedly accepted" >&2
      exit 1
    else
      BIAS_CROSS_STATUS=$?
    fi
    if [[ "$BIAS_CROSS_STATUS" -ne 2 ]]; then
      echo "formal PDF set: $BIAS_KIND bias refusal returned $BIAS_CROSS_STATUS, expected 2" >&2
      exit 1
    fi
  done
fi
'''
for name, block in (("bindings", bindings), ("inventory", inventory),
                    ("early exact work", early), ("cross refusal", cross)):
    if text.count(block) != 1:
        raise SystemExit(f"bias exact/registration/refusal wiring drifted: {name}")
positions = [text.index(bindings), text.index(inventory), text.index(early),
             text.index('python3 -I -B scripts/check-publication-links.py'),
             text.index('# The new mean exposition admits exact reviewed bytes only; retain fresh build evidence.'),
             text.index(cross)]
if positions != sorted(positions):
    raise SystemExit("bias exact/registration/refusal wiring drifted: order")
if text.count(inventory + "\n" + early) != 1:
    raise SystemExit("bias exact/registration/refusal wiring drifted: early boundary")
PY
}

make_bias_registration_probe() {
  python3 -I -S - "$PRODUCTION_GATE" "$1" <<'PY'
from pathlib import Path
import sys

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = '# Exact bias controls and reproduction consume actual pre-reviewed external registrations.\n'
end = 'if [[ "$MODE" == "--inventory-only" ]]; then\n'
if text.count(start) != 1 or text.count(end) != 1:
    raise SystemExit("bias registration probe anchors drifted")
block = text[text.index(start):text.index(end)]
Path(sys.argv[2]).write_text('#!/usr/bin/env bash\nset -euo pipefail\nMODE="$1"\n' + block,
                           encoding="utf-8", newline="\n")
PY
}

run_bias_registration_probe() {
  local probe="$1"
  local mode="$2"
  local omitted="$3"
  local expected_status="$4"
  local expected_diagnostic="$5"
  local binding
  local status
  local environment=("PATH=$PATH")
  if [[ "$omitted" != "ALL" ]]; then
    for binding in PID_RS_BIAS_PYTHON \
        PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION \
        PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256 \
        PID_RS_BIAS_CONTROL_NORMAL_OUTPUT \
        PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION \
        PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256 \
        PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT \
        PID_RS_BIAS_FULL_REGISTRATION PID_RS_BIAS_FULL_REGISTRATION_SHA256 \
        PID_RS_BIAS_FULL_WORK_DIR PID_RS_BIAS_SUMMARY_REGISTRATION \
        PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256 PID_RS_BIAS_SUMMARY_WORK_DIR; do
      if [[ "$binding" != "$omitted" ]]; then
        environment+=("$binding=INERT_BINDING_NEVER_EXECUTED")
      fi
    done
  fi
  local stdout="$TEST_ROOT/bias-registration-$PASS_COUNT.stdout"
  local stderr="$TEST_ROOT/bias-registration-$PASS_COUNT.stderr"
  if /usr/bin/env -i "${environment[@]}" bash --noprofile --norc "$probe" "$mode" \
      >"$stdout" 2>"$stderr"; then
    status=0
  else
    status=$?
  fi
  if [[ "$status" -ne "$expected_status" || -s "$stdout" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: bias registration probe returned $status, expected $expected_status" >&2
    return 1
  fi
  if [[ "$expected_status" -eq 0 ]]; then
    if [[ -s "$stderr" ]]; then
      cat "$stderr" >&2
      return 1
    fi
  elif ! grep -Fq "$expected_diagnostic" "$stderr"; then
    cat "$stderr" >&2
    echo "$CHECK_NAME: bias registration probe failed for a noncausal reason" >&2
    return 1
  fi
  pass "bias registration presence mode=$mode omitted=$omitted"
}

make_bias_dispatch_probe() {
  python3 -I -S - "$PRODUCTION_GATE" "$1" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
start = "# Keep the finite registration clocks causal: run fresh inert bias controls and both exact bias\n"
end = '  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind summary --exact --check --registration "$PID_RS_BIAS_SUMMARY_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"\nfi\n'
if source.count(start) != 1 or source.count(end) != 1:
    raise SystemExit("bias dispatch probe anchors drifted")
begin = source.index(start)
finish = source.index(end, begin) + len(end)
block = source[begin:finish]
probe = f'''#!/usr/bin/env bash
set -euo pipefail
MODE="$1"
ROOT="$2"
{block}'''
Path(sys.argv[2]).write_text(probe, encoding="utf-8", newline="\n")
PY
  chmod 0755 "$1"
}

run_bias_dispatch_probe() {
  local probe="$1"
  local mode="$2"
  local probe_root="$TEST_ROOT/bias-dispatch-${mode#--}"
  local fake_python="$probe_root/fake-bias-python"
  local calls="$probe_root/calls.tsv"
  local stdout="$probe_root/stdout"
  local stderr="$probe_root/stderr"
  local status
  local environment=("PATH=$PATH")
  mkdir -p "$probe_root"
  : >"$calls"
  cat >"$fake_python" <<'FAKE'
#!/usr/bin/env bash
set -euo pipefail
{
  printf 'call'
  printf '\t%s' "$@"
  printf '\n'
} >>"$PID_RS_BIAS_CALL_LOG"
FAKE
  chmod 0755 "$fake_python"
  if [[ "$mode" == "--exact" ]]; then
    environment+=(
      "PID_RS_BIAS_CALL_LOG=$calls"
      "PID_RS_BIAS_PYTHON=$fake_python"
      "PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION=NORMAL_REGISTRATION"
      "PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256=NORMAL_REGISTRATION_SHA256"
      "PID_RS_BIAS_CONTROL_NORMAL_OUTPUT=NORMAL_OUTPUT"
      "PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION=OPTIMIZED_REGISTRATION"
      "PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256=OPTIMIZED_REGISTRATION_SHA256"
      "PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT=OPTIMIZED_OUTPUT"
      "PID_RS_BIAS_FULL_REGISTRATION=FULL_REGISTRATION"
      "PID_RS_BIAS_FULL_REGISTRATION_SHA256=FULL_REGISTRATION_SHA256"
      "PID_RS_BIAS_FULL_WORK_DIR=FULL_WORK_DIR"
      "PID_RS_BIAS_SUMMARY_REGISTRATION=SUMMARY_REGISTRATION"
      "PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256=SUMMARY_REGISTRATION_SHA256"
      "PID_RS_BIAS_SUMMARY_WORK_DIR=SUMMARY_WORK_DIR"
    )
  fi
  if /usr/bin/env -i "${environment[@]}" bash --noprofile --norc \
      "$probe" "$mode" PROBE_ROOT >"$stdout" 2>"$stderr"; then
    status=0
  else
    status=$?
  fi
  if [[ "$status" -ne 0 || -s "$stdout" || -s "$stderr" ]]; then
    cat "$stdout" "$stderr" >&2
    echo "$CHECK_NAME: bias dispatch probe mode=$mode returned $status" >&2
    return 1
  fi
  python3 -I -S - "$calls" "$mode" <<'PY'
from pathlib import Path
import sys

actual = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
mode = sys.argv[2]
expected = []
if mode == "--exact":
    expected = [
        "call\t-I\t-S\t-B\tscripts/check-prefix-mgw-bias-pdf-self-test.py\t--root\tPROBE_ROOT\t--registration\tNORMAL_REGISTRATION\t--registration-sha256\tNORMAL_REGISTRATION_SHA256\t--output\tNORMAL_OUTPUT",
        "call\t-O\t-I\t-S\t-B\tscripts/check-prefix-mgw-bias-pdf-self-test.py\t--root\tPROBE_ROOT\t--registration\tOPTIMIZED_REGISTRATION\t--registration-sha256\tOPTIMIZED_REGISTRATION_SHA256\t--output\tOPTIMIZED_OUTPUT",
        "call\t-I\t-S\t-B\tscripts/build-prefix-mgw-bias-pdf.py\t--root\tPROBE_ROOT\t--kind\tfull\t--exact\t--check\t--registration\tFULL_REGISTRATION\t--registration-sha256\tFULL_REGISTRATION_SHA256\t--work-dir\tFULL_WORK_DIR",
        "call\t-I\t-S\t-B\tscripts/build-prefix-mgw-bias-pdf.py\t--root\tPROBE_ROOT\t--kind\tsummary\t--exact\t--check\t--registration\tSUMMARY_REGISTRATION\t--registration-sha256\tSUMMARY_REGISTRATION_SHA256\t--work-dir\tSUMMARY_WORK_DIR",
    ]
if actual != expected:
    raise SystemExit(f"bias dispatch mode {mode} differs: {actual!r}")
PY
  pass "bias early dispatch mode=$mode has the exact private-call boundary"
}

validate_terminal_success_contract() {
  python3 -I -S - "$1" <<'PY'
from pathlib import Path
import sys


text = Path(sys.argv[1]).read_text(encoding="utf-8")
expected = '''if [[ "$MODE" == "--exact" ]]; then
  echo "OK: every declared formal paper has a warning-free same-toolchain result; current bias inert source/data controls passed in normal and optimized Python; committed-byte relations are exact, including the root blueprint and post-publication custody receipt, and the source and renderer-fragment inventories are exact"
else
  echo "OK: every declared paper with a reviewed cross-toolchain profile passed its warning-free bounded gate; the root blueprint, post-publication custody receipt, mean exposition, recorded-sensor document, finite MGW paper, target-copy MGW note, full bias paper and bias summary intentionally have no accepted cross-toolchain relation, and all eight status-2 refusals plus the source and renderer-fragment inventories are exact"
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
exact success message cannot omit current bias controls	current bias inert source/data controls passed in normal and optimized Python; 	
exact success message cannot omit the custody receipt	including the root blueprint and post-publication custody receipt	including the root blueprint
cross success message cannot call all papers profiled	every declared paper with a reviewed cross-toolchain profile	every declared paper
cross success message cannot omit the eighth refusal	all eight status-2 refusals	all seven status-2 refusals
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

if ! validate_mean_gate_wiring "$PRODUCTION_GATE" >"$TEST_ROOT/mean-production.stdout" 2>"$TEST_ROOT/mean-production.stderr"; then
  cat "$TEST_ROOT/mean-production.stderr" >&2
  exit 1
fi
pass "mean exposition exact build and explicit cross refusal are wired"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/mean-gate-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before, after = sys.argv[2:]
if text.count(before) != 1:
    raise SystemExit("mean mutation anchor drifted")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_mean_gate_wiring "$case_file" >"$TEST_ROOT/mean-$PASS_COUNT.stdout" 2>"$TEST_ROOT/mean-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: mean wiring mutation accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "mean exposition exact/refusal wiring drifted" "$TEST_ROOT/mean-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/mean-$PASS_COUNT.stderr" >&2
    exit 1
  fi
  pass "$label"
done <<'MEAN_CASES'
mean exact build cannot be skipped	  python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact --check --work-dir "$MEAN_BUILD_PARENT/build"	  :
mean exact failure cannot be ignored	--exact --check --work-dir "$MEAN_BUILD_PARENT/build"	--exact --check --work-dir "$MEAN_BUILD_PARENT/build" || true
mean repeated build cannot be removed	--exact --check --work-dir "$MEAN_BUILD_PARENT/build"	--exact --work-dir "$MEAN_BUILD_PARENT/build"
mean cross refusal cannot become exact mode	  if python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --cross-toolchain; then	  if python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact; then
mean cross success cannot be accepted	  if python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --cross-toolchain; then	  if ! python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --cross-toolchain; then
mean refusal must require status two	  if [[ "$MEAN_CROSS_STATUS" -ne 2 ]]; then	  if [[ "$MEAN_CROSS_STATUS" -ne 1 ]]; then
MEAN_CASES

if ! validate_occupancy_gate_wiring "$PRODUCTION_GATE" >"$TEST_ROOT/occupancy-production.stdout" 2>"$TEST_ROOT/occupancy-production.stderr"; then
  cat "$TEST_ROOT/occupancy-production.stderr" >&2
  exit 1
fi
pass "recorded-sensor exact build, controls and explicit cross refusal are wired"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/occupancy-gate-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before, after = sys.argv[2:]
if text.count(before) != 1:
    raise SystemExit("occupancy mutation anchor drifted")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_occupancy_gate_wiring "$case_file" >"$TEST_ROOT/occupancy-$PASS_COUNT.stdout" 2>"$TEST_ROOT/occupancy-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: occupancy wiring mutation accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "recorded-sensor exact/refusal/control wiring drifted" "$TEST_ROOT/occupancy-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/occupancy-$PASS_COUNT.stderr" >&2
    exit 1
  fi
  pass "$label"
done <<'OCCUPANCY_CASES'
occupancy exact build cannot be skipped	  python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$OCCUPANCY_BUILD_PARENT/build"	  :
occupancy exact failure cannot be ignored	--exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$OCCUPANCY_BUILD_PARENT/build"	--exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$OCCUPANCY_BUILD_PARENT/build" || true
occupancy repeat cannot be removed	--exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT"	--exact --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT"
occupancy exact gate cannot become discovery	--exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT"	--discover --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT"
occupancy cross refusal cannot become exact	  if python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --cross-toolchain; then	  if python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --exact; then
occupancy refusal must require status two	  if [[ "$OCCUPANCY_CROSS_STATUS" -ne 2 ]]; then	  if [[ "$OCCUPANCY_CROSS_STATUS" -ne 1 ]]; then
occupancy normal controls cannot be skipped	python3 -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/normal"	:
occupancy optimized controls cannot be ignored	python3 -O -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/optimized"	python3 -O -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/optimized" || true
OCCUPANCY_CASES

if ! validate_mgw_fixed_world_gate_wiring "$PRODUCTION_GATE" >"$TEST_ROOT/mgw-production.stdout" 2>"$TEST_ROOT/mgw-production.stderr"; then
  cat "$TEST_ROOT/mgw-production.stderr" >&2
  exit 1
fi
pass "finite MGW exact build, both control modes and status-2 cross refusal are wired"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/mgw-fixed-world-gate-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before = sys.argv[2].replace(r"\n", "\n")
after = sys.argv[3].replace(r"\n", "\n")
if text.count(before) != 1:
    raise SystemExit("finite MGW mutation anchor drifted")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_mgw_fixed_world_gate_wiring "$case_file" >"$TEST_ROOT/mgw-$PASS_COUNT.stdout" 2>"$TEST_ROOT/mgw-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: finite MGW wiring mutation accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "finite MGW exact/refusal/control wiring drifted" "$TEST_ROOT/mgw-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/mgw-$PASS_COUNT.stdout" "$TEST_ROOT/mgw-$PASS_COUNT.stderr" >&2
    echo "$CHECK_NAME: finite MGW wiring mutation failed for a noncausal reason: $label" >&2
    exit 1
  fi
  pass "$label"
done <<'MGW_FIXED_WORLD_CASES'
finite MGW exact build cannot be skipped	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  :
finite MGW exact failure cannot be swallowed	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build" || true
finite MGW repeated build cannot be removed	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"
finite MGW exact mode cannot become discovery	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --discover --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"
finite MGW exact branch cannot be conditionally skipped	if [[ "$MODE" == "--exact" ]]; then\n  if [[ -z "${PID_RS_MGW_FIXED_WORLD_TEX_ROOT:-}" ]]; then	if [[ "$MODE" == "--cross-toolchain" ]]; then\n  if [[ -z "${PID_RS_MGW_FIXED_WORLD_TEX_ROOT:-}" ]]; then
finite MGW requires an explicit TeX root	  if [[ -z "${PID_RS_MGW_FIXED_WORLD_TEX_ROOT:-}" ]]; then	  if false; then
finite MGW exact invocation cannot omit the TeX selector	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"
finite MGW cannot borrow the recorded-sensor TeX selector	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"	  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"
finite MGW cross probe cannot be omitted	  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then	  if false; then
finite MGW cross probe cannot become exact	  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then	  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact; then
finite MGW cross success cannot be accepted	  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then	  if ! python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then
finite MGW refusal must require status two	  if [[ "$MGW_FIXED_WORLD_CROSS_STATUS" -ne 2 ]]; then	  if [[ "$MGW_FIXED_WORLD_CROSS_STATUS" -ne 1 ]]; then
finite MGW cannot fabricate the child refusal status	    MGW_FIXED_WORLD_CROSS_STATUS=$?	    MGW_FIXED_WORLD_CROSS_STATUS=2
finite MGW normal controls cannot be skipped	python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"	:
finite MGW normal control failure cannot be swallowed	python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"	python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal" || true
finite MGW optimized controls cannot be skipped	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"	:
finite MGW optimized control failure cannot be swallowed	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized" || true
finite MGW optimized controls cannot lose optimization	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"	python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"
finite MGW control modes cannot share one work directory	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"	python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"
finite MGW normal controls cannot be skipped by a false prefix	python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"	false && python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"
MGW_FIXED_WORLD_CASES

if ! validate_bias_gate_wiring "$PRODUCTION_GATE" >"$TEST_ROOT/bias-production.stdout" 2>"$TEST_ROOT/bias-production.stderr"; then
  cat "$TEST_ROOT/bias-production.stderr" >&2
  exit 1
fi
pass "fresh bias controls, early exact invocations, external bindings and status-two refusals are wired"

while IFS=$'\t' read -r label before after; do
  case_file="$TEST_ROOT/bias-gate-$PASS_COUNT.sh"
  cp "$PRODUCTION_GATE" "$case_file"
  python3 -I -S - "$case_file" "$before" "$after" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
before, after = (value.replace(r"\n", "\n") for value in sys.argv[2:])
if text.count(before) != 1:
    raise SystemExit("bias mutation anchor drifted")
path.write_text(text.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  if validate_bias_gate_wiring "$case_file" >"$TEST_ROOT/bias-$PASS_COUNT.stdout" 2>"$TEST_ROOT/bias-$PASS_COUNT.stderr"; then
    echo "$CHECK_NAME: bias wiring mutation accepted: $label" >&2
    exit 1
  fi
  if ! grep -Fq "bias exact/registration/refusal wiring drifted" "$TEST_ROOT/bias-$PASS_COUNT.stderr"; then
    cat "$TEST_ROOT/bias-$PASS_COUNT.stderr" >&2
    exit 1
  fi
  pass "$label"
done <<'BIAS_CASES'
normal bias controls cannot be removed	"$PID_RS_BIAS_PYTHON" -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"	:
normal bias-control failure cannot be swallowed	--output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"	--output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT" || true
optimized bias controls cannot be removed	"$PID_RS_BIAS_PYTHON" -O -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"	:
optimized bias-control failure cannot be swallowed	--output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"	--output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT" || true
optimized bias controls cannot lose optimization	"$PID_RS_BIAS_PYTHON" -O -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py	"$PID_RS_BIAS_PYTHON" -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py
normal controls cannot use optimized registration	--registration "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION"	--registration "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION"
normal controls cannot use optimized registration hash	--registration-sha256 "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256"	--registration-sha256 "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256"
normal controls cannot use optimized output	--output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"	--output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"
optimized controls cannot use normal registration	--registration "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION"	--registration "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION"
optimized controls cannot use normal registration hash	--registration-sha256 "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256"	--registration-sha256 "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256"
optimized controls cannot use normal output	--output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"	--output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"
fresh bias controls cannot run in cross mode	# child; the following builder calls retain their separate production meaning.\nif [[ "$MODE" == "--exact" ]]; then	# child; the following builder calls retain their separate production meaning.\nif [[ "$MODE" == "--cross-toolchain" ]]; then
fresh bias controls cannot run in inventory mode	# child; the following builder calls retain their separate production meaning.\nif [[ "$MODE" == "--exact" ]]; then	# child; the following builder calls retain their separate production meaning.\nif [[ "$MODE" == "--inventory-only" ]]; then
private bias guards cannot run in cross mode	# Inventory and unsupported cross requests never require or manufacture them.\nif [[ "$MODE" == "--exact" ]]; then	# Inventory and unsupported cross requests never require or manufacture them.\nif [[ "$MODE" == "--cross-toolchain" ]]; then
private bias guards cannot run in inventory mode	# Inventory and unsupported cross requests never require or manufacture them.\nif [[ "$MODE" == "--exact" ]]; then	# Inventory and unsupported cross requests never require or manufacture them.\nif [[ "$MODE" == "--inventory-only" ]]; then
full bias repetition cannot be removed	--kind full --exact --check --registration	--kind full --exact --registration
summary bias repetition cannot be removed	--kind summary --exact --check --registration	--kind summary --exact --registration
full bias cannot request unsupported cross mode	--kind full --exact --check	--kind full --cross-toolchain --check
summary bias cannot request unsupported cross mode	--kind summary --exact --check	--kind summary --cross-toolchain --check
full bias registration hash cannot be omitted	--registration-sha256 "$PID_RS_BIAS_FULL_REGISTRATION_SHA256"	
summary bias registration hash cannot be omitted	--registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256"	
full bias failure cannot be ignored	--work-dir "$PID_RS_BIAS_FULL_WORK_DIR"	--work-dir "$PID_RS_BIAS_FULL_WORK_DIR" || true
summary bias failure cannot be ignored	--work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"	--work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR" || true
full bias registration cannot be replaced by summary registration	--registration "$PID_RS_BIAS_FULL_REGISTRATION"	--registration "$PID_RS_BIAS_SUMMARY_REGISTRATION"
both bias kinds need an unsupported-profile probe	for BIAS_KIND in full summary; do	for BIAS_KIND in full; do
bias cross success cannot be accepted	if python3 -I -S -B scripts/build-prefix-mgw-bias-pdf.py --kind "$BIAS_KIND" --cross-toolchain; then	if ! python3 -I -S -B scripts/build-prefix-mgw-bias-pdf.py --kind "$BIAS_KIND" --cross-toolchain; then
bias refusal must require status two	if [[ "$BIAS_CROSS_STATUS" -ne 2 ]]; then	if [[ "$BIAS_CROSS_STATUS" -ne 1 ]]; then
full bias registration must be required before other gates	  : "${PID_RS_BIAS_FULL_REGISTRATION:?formal PDF set: full bias registration is required}"	  :
summary bias work directory must be required before other gates	  : "${PID_RS_BIAS_SUMMARY_WORK_DIR:?formal PDF set: summary bias work directory is required}"	  :
BIAS_CASES

case_file="$TEST_ROOT/bias-gate-moved-after-long-gates.sh"
cp "$PRODUCTION_GATE" "$case_file"
python3 -I -S - "$case_file" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
start = "# Keep the finite registration clocks causal: run fresh inert bias controls and both exact bias\n"
end = '  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind summary --exact --check --registration "$PID_RS_BIAS_SUMMARY_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"\nfi\n\n'
cross = "# No alternate producer profile relates either bias PDF to a Linux/cross-toolchain build.\n"
if text.count(start) != 1 or text.count(end) != 1 or text.count(cross) != 1:
    raise SystemExit("bias late-placement mutation anchors drifted")
begin = text.index(start)
finish = text.index(end, begin) + len(end)
block = text[begin:finish]
text = text[:begin] + text[finish:]
text = text.replace(cross, block + cross, 1)
path.write_text(text, encoding="utf-8", newline="\n")
PY
if validate_bias_gate_wiring "$case_file" >"$TEST_ROOT/bias-moved.stdout" 2>"$TEST_ROOT/bias-moved.stderr"; then
  echo "$CHECK_NAME: bias controls/builds moved after long gates were accepted" >&2
  exit 1
fi
if ! grep -Fq "bias exact/registration/refusal wiring drifted" "$TEST_ROOT/bias-moved.stderr"; then
  cat "$TEST_ROOT/bias-moved.stderr" >&2
  echo "$CHECK_NAME: late bias work failed for a noncausal reason" >&2
  exit 1
fi
pass "fresh bias controls and exact builds cannot move after the long aggregate gates"

bias_registration_probe="$TEST_ROOT/bias-registration-probe.sh"
make_bias_registration_probe "$bias_registration_probe"
run_bias_registration_probe "$bias_registration_probe" --exact NONE 0 ""
run_bias_registration_probe "$bias_registration_probe" --inventory-only ALL 0 ""
run_bias_registration_probe "$bias_registration_probe" --cross-toolchain ALL 0 ""
while IFS=$'\t' read -r omitted diagnostic; do
  run_bias_registration_probe "$bias_registration_probe" --exact "$omitted" 1 "$diagnostic"
done <<'BIAS_BINDING_CASES'
PID_RS_BIAS_PYTHON	exact bias work requires its pinned Python selector
PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION	normal bias-control registration is required
PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256	normal bias-control registration hash is required
PID_RS_BIAS_CONTROL_NORMAL_OUTPUT	normal bias-control output is required
PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION	optimized bias-control registration is required
PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256	optimized bias-control registration hash is required
PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT	optimized bias-control output is required
PID_RS_BIAS_FULL_REGISTRATION	full bias registration is required
PID_RS_BIAS_FULL_REGISTRATION_SHA256	full bias registration hash is required
PID_RS_BIAS_FULL_WORK_DIR	full bias work directory is required
PID_RS_BIAS_SUMMARY_REGISTRATION	summary bias registration is required
PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256	summary bias registration hash is required
PID_RS_BIAS_SUMMARY_WORK_DIR	summary bias work directory is required
BIAS_BINDING_CASES

bias_dispatch_probe="$TEST_ROOT/bias-dispatch-probe.sh"
make_bias_dispatch_probe "$bias_dispatch_probe"
run_bias_dispatch_probe "$bias_dispatch_probe" --exact
run_bias_dispatch_probe "$bias_dispatch_probe" --inventory-only
run_bias_dispatch_probe "$bias_dispatch_probe" --cross-toolchain

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

fixture="$TEST_ROOT/missing-finite-mgw-pdf"
make_fixture "$fixture"
mv "$fixture/output/pdf/mgw-fixed-world-added-information.pdf" "$fixture/removed-finite-mgw.pdf"
expect_failure "missing finite MGW standalone PDF is rejected" "$fixture" \
  "rendered PDF inventory differs"

for bias_stem in prefix-mgw-bias prefix-mgw-bias-summary; do
  fixture="$TEST_ROOT/missing-$bias_stem-pdf"
  make_fixture "$fixture"
  mv "$fixture/output/pdf/$bias_stem.pdf" "$fixture/removed-bias-paper.pdf"
  expect_failure "missing $bias_stem PDF is rejected" "$fixture" \
    "rendered PDF inventory differs"
done

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

python3 -I -S -B "$ROOT/scripts/check-finite-target-copy-mgw-pdf-self-test.py"
python3 -O -I -S -B "$ROOT/scripts/check-finite-target-copy-mgw-pdf-self-test.py"

echo "OK: $PASS_COUNT formal-PDF typed-inventory controls passed; target-copy controller and dispatch controls also passed in both Python modes"
