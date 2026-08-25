#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
cd "$ROOT"
MODE="${1:---exact}"

# Kpathsea treats a double slash in a search path as a recursive-directory
# request.  Canonicalize the aggregate gate's temporary root once so an
# ambient slash-terminated TMPDIR cannot turn each TeX build into an
# unrelated recursive scan.  The explicit override exists for isolated gate
# runners and is subject to the same boundary.
FORMAL_TMP_ROOT_INPUT="${PID_RS_PDF_GATE_TMPDIR:-${TMPDIR:-/tmp}}"
if ! FORMAL_TMP_ROOT="$(CDPATH='' cd -- "$FORMAL_TMP_ROOT_INPUT" && pwd -P)"; then
  echo "formal PDF set: cannot canonicalize temporary root: $FORMAL_TMP_ROOT_INPUT" >&2
  exit 2
fi
if [[ "$FORMAL_TMP_ROOT" == "/" ]]; then
  echo "formal PDF set: refusing filesystem root as temporary root" >&2
  exit 2
fi
export TMPDIR="$FORMAL_TMP_ROOT"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" \
    && "$MODE" != "--inventory-only" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain|--inventory-only]" >&2
  exit 2
fi

STANDALONE_LATEX_PAPERS=(
  "certified-sxpid2-executable-assurance"
  "dependency-colored-sxpid-concentration"
  "ecosystem-compatibility-audit"
  "exact-log-product-sxpid2-assurance"
  "finite-alphabet-plugin-convergence"
  "formal-tool-adoption-audit"
  "foundational-shared-exclusions-pid-audit"
  "ksg-m1a-composite-v4-process"
  "ksg-m1a-composite-v5-boundary"
  "ksg-m1a-composite-v6-boundary"
  "ksg-m1a-composite-v7-boundary"
  "mathematical-problem-solving-workflow"
  "support-change-tolerant-averaged-sxpid-continuity"
  "two-source-sxpid-count-atom-bridge"
)

LATEX_RENDER_FRAGMENTS=(
  "pid-discovery-verification-and-durability-blueprint-header"
)

expected_tex=()
while IFS= read -r stem; do
  expected_tex+=("$stem")
done < <(
  printf '%s\n' "${STANDALONE_LATEX_PAPERS[@]}" "${LATEX_RENDER_FRAGMENTS[@]}" \
    | LC_ALL=C sort
)

actual_tex=()
while IFS= read -r path; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "formal PDF set: TeX inventory entry is not a direct regular file: $path" >&2
    exit 1
  fi
  actual_tex+=("$(basename "$path" .tex)")
done < <(find audit/formal/latex -maxdepth 1 -name '*.tex' -print | LC_ALL=C sort)

actual_pdf=()
while IFS= read -r path; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "formal PDF set: PDF inventory entry is not a direct regular file: $path" >&2
    exit 1
  fi
  actual_pdf+=("$(basename "$path" .pdf)")
done < <(find output/pdf -maxdepth 1 -name '*.pdf' -print | LC_ALL=C sort)

if [[ "${actual_tex[*]}" != "${expected_tex[*]}" ]]; then
  echo "formal PDF set: typed TeX source inventory differs from the declared standalone/fragment set" >&2
  exit 1
fi

if [[ "${actual_pdf[*]}" != "${STANDALONE_LATEX_PAPERS[*]}" ]]; then
  echo "formal PDF set: rendered PDF inventory differs from the declared standalone-paper set" >&2
  exit 1
fi

if [[ "$MODE" == "--inventory-only" ]]; then
  echo "OK: standalone-paper, renderer-fragment, and PDF inventories are exact and direct-regular"
  exit 0
fi

scripts/check-formal-pdf-set-self-test.sh
python3 scripts/check-formal-pdf-style.py
python3 scripts/check-formal-pdf-style-self-test.py
python3 -I -S scripts/sync-mathematical-workflow-tex.py --check
python3 -I -S scripts/sync-mathematical-workflow-tex-self-test.py
python3 -O -I -S scripts/sync-mathematical-workflow-tex-self-test.py
scripts/check-formal-pdf-log-self-test.sh
python3 -I -S scripts/compare-formal-pdf-renders-self-test.py
python3 -O -I -S scripts/compare-formal-pdf-renders-self-test.py
scripts/check-mathematical-workflow-pdf-self-test.sh

scripts/check-certified-sxpid2-assurance-pdf.sh "$MODE"
scripts/check-dependency-colored-sxpid-pdf.sh "$MODE"
scripts/check-ecosystem-compatibility-audit-pdf.sh "$MODE"
scripts/check-exact-log-product-sxpid2-pdf.sh "$MODE"
scripts/check-finite-alphabet-convergence-pdf.sh "$MODE"
scripts/check-formal-tool-adoption-pdf.sh "$MODE"
scripts/check-foundational-sxpid-audit-pdf.sh "$MODE"
scripts/check-ksg-m1a-composite-v6-pdf-portability.sh "$MODE"
scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh "$MODE"
scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh "$MODE"
WORKFLOW_GATE_PATH="${PID_RS_PDF_GATE_PATH:-/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/local/sbin:/Library/TeX/texbin:/usr/bin:/bin:/usr/sbin:/sbin}"
WORKFLOW_GATE_HOME="${PID_RS_PDF_GATE_HOME:-/nonexistent}"
WORKFLOW_GATE_TMPDIR="$FORMAL_TMP_ROOT"
WORKFLOW_GATE_STDERR="$(mktemp "$FORMAL_TMP_ROOT/pid-rs-formal-workflow-stderr.XXXXXX")"
cleanup_workflow_gate_stderr() {
  local status="$1"
  local cleanup_failed=0
  trap - EXIT INT TERM
  case "${WORKFLOW_GATE_STDERR:-}" in
    "$FORMAL_TMP_ROOT"/pid-rs-formal-workflow-stderr.*)
      rm -f -- "$WORKFLOW_GATE_STDERR" || cleanup_failed=1
      ;;
    "") ;;
    *)
      echo "formal PDF set: refusing to remove unexpected workflow diagnostic path" >&2
      cleanup_failed=1
      ;;
  esac
  if [[ "$status" -eq 0 && "$cleanup_failed" -ne 0 ]]; then
    status=1
  fi
  exit "$status"
}
trap 'cleanup_workflow_gate_stderr "$?"' EXIT
trap 'cleanup_workflow_gate_stderr 130' INT
trap 'cleanup_workflow_gate_stderr 143' TERM
if /usr/bin/env -i \
  "PATH=$WORKFLOW_GATE_PATH" \
  "HOME=$WORKFLOW_GATE_HOME" \
  "TMPDIR=$WORKFLOW_GATE_TMPDIR" \
  LC_ALL=C \
  LANG=C \
  TZ=UTC \
  bash --noprofile --norc scripts/check-mathematical-workflow-pdf.sh "$MODE" \
    2>"$WORKFLOW_GATE_STDERR"; then
  WORKFLOW_GATE_STATUS=0
else
  WORKFLOW_GATE_STATUS=$?
fi
if [[ "$WORKFLOW_GATE_STATUS" -ne 0 || -s "$WORKFLOW_GATE_STDERR" ]]; then
  cat "$WORKFLOW_GATE_STDERR" >&2
  if [[ "$WORKFLOW_GATE_STATUS" -eq 0 ]]; then
    echo "formal PDF set: workflow gate emitted a diagnostic despite status zero" >&2
    exit 1
  fi
  echo "formal PDF set: workflow gate failed with status $WORKFLOW_GATE_STATUS" >&2
  exit "$WORKFLOW_GATE_STATUS"
fi
rm -f -- "$WORKFLOW_GATE_STDERR"
WORKFLOW_GATE_STDERR=""
trap - EXIT INT TERM
scripts/check-support-change-tolerant-sxpid-pdf.sh "$MODE"
scripts/check-two-source-sxpid-count-atom-bridge-pdf.sh "$MODE"

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: every standalone formal LaTeX paper has one warning-free same-toolchain-reproducible PDF; renderer-fragment inventory is exact"
else
  echo "OK: every standalone formal LaTeX paper passed its warning-free bounded cross-toolchain PDF gate; renderer-fragment inventory is exact"
fi
