#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
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

STANDALONE_MARKDOWN_PAPERS=(
  "mathematical-results-guide"
  "finite-target-copy-mgw-synergy"
  "mgw-fixed-world-added-information"
  "numerical-assurance"
  "pid2-represented-coordinate-assurance"
  "pid-sensor-placement-and-galadriel-guide"
  "post-publication-custody-2026-09-02"
  "prefix-mgw-bias"
  "prefix-mgw-bias-summary"
  "prefix-mgw-mean"
  "recorded-office-sensors"
  "sxpid3-source-marginal-and-bounded-audit"
)

STANDALONE_MARKDOWN_SOURCES=(
  "MATHEMATICAL_RESULTS_GUIDE.md"
  "audit/evidence/finite-target-copy-mgw-synergy.md"
  "audit/evidence/mgw-fixed-world-added-information-2026-09-09.md"
  "NUMERICAL_ASSURANCE.md"
  "PID2_REPRESENTED_COORDINATE_ASSURANCE.md"
  "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md"
  "audit/evidence/post-publication-custody-2026-09-02.md"
  "audit/formal/lean-prefix-mgw-bias/EXPOSITION.md"
  "audit/formal/lean-prefix-mgw-bias/SUMMARY.md"
  "audit/formal/lean-prefix-mgw-mean/EXPOSITION.current.md"
  "audit/evidence/real-occupancy-sensors-example-2026-09-08.md"
  "SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md"
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

# Removing a suffix can change lexicographic order: bias-summary.pdf sorts before
# bias.pdf, while the stem bias sorts before bias-summary. Compare sorted stems.
sorted_actual_pdf=()
while IFS= read -r stem; do
  sorted_actual_pdf+=("$stem")
done < <(printf '%s\n' "${actual_pdf[@]}" | LC_ALL=C sort)
actual_pdf=("${sorted_actual_pdf[@]}")

expected_pdf=()
while IFS= read -r stem; do
  expected_pdf+=("$stem")
done < <(
  printf '%s\n' "${STANDALONE_LATEX_PAPERS[@]}" "${STANDALONE_MARKDOWN_PAPERS[@]}" \
    | LC_ALL=C sort
)

if [[ "${actual_tex[*]}" != "${expected_tex[*]}" ]]; then
  echo "formal PDF set: typed TeX source inventory differs from the declared standalone/fragment set" >&2
  exit 1
fi

for markdown_source in "${STANDALONE_MARKDOWN_SOURCES[@]}"; do
  if [[ ! -f "$markdown_source" || -L "$markdown_source" ]]; then
    echo "formal PDF set: Markdown source is not a direct regular file: $markdown_source" >&2
    exit 1
  fi
done

if [[ "${actual_pdf[*]}" != "${expected_pdf[*]}" ]]; then
  echo "formal PDF set: rendered PDF inventory differs from the declared standalone-paper set" >&2
  exit 1
fi

# Exact bias controls and reproduction consume actual pre-reviewed external registrations.
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

if [[ "$MODE" == "--inventory-only" ]]; then
  echo "OK: standalone-paper, renderer-fragment, and PDF inventories are exact and direct-regular"
  exit 0
fi

# Keep the finite registration clocks causal: run fresh inert bias controls and both exact bias
# reproductions before the older, longer aggregate gates.  These controls start no PDF/parser/proof
# child; the following builder calls retain their separate production meaning.
if [[ "$MODE" == "--exact" ]]; then
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_NORMAL_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_NORMAL_OUTPUT"
  "$PID_RS_BIAS_PYTHON" -O -I -S -B scripts/check-prefix-mgw-bias-pdf-self-test.py --root "$ROOT" --registration "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_CONTROL_OPTIMIZED_REGISTRATION_SHA256" --output "$PID_RS_BIAS_CONTROL_OPTIMIZED_OUTPUT"
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind full --exact --check --registration "$PID_RS_BIAS_FULL_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_FULL_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_FULL_WORK_DIR"
  "$PID_RS_BIAS_PYTHON" -I -S -B scripts/build-prefix-mgw-bias-pdf.py --root "$ROOT" --kind summary --exact --check --registration "$PID_RS_BIAS_SUMMARY_REGISTRATION" --registration-sha256 "$PID_RS_BIAS_SUMMARY_REGISTRATION_SHA256" --work-dir "$PID_RS_BIAS_SUMMARY_WORK_DIR"
fi

python3 -I -B scripts/check-publication-links.py
python3 -O -I -B scripts/check-publication-links.py
python3 -I -B scripts/check-publication-links-self-test.py
python3 -O -I -B scripts/check-publication-links-self-test.py
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
python3 -I -S -B scripts/prepare-mathematical-workflow-markdown-parser-self-test.py \
  --handoff \
  scripts/check-mathematical-workflow-pdf.sh \
  scripts/check-mathematical-workflow-pdf-self-test.sh \
  scripts/check-formal-pdf-set.sh \
  scripts/check-formal-pdf-set-self-test.sh \
  .github/workflows/ci.yml \
  justfile
python3 -O -I -S -B scripts/prepare-mathematical-workflow-markdown-parser-self-test.py \
  --handoff \
  scripts/check-mathematical-workflow-pdf.sh \
  scripts/check-mathematical-workflow-pdf-self-test.sh \
  scripts/check-formal-pdf-set.sh \
  scripts/check-formal-pdf-set-self-test.sh \
  .github/workflows/ci.yml \
  justfile
scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh

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

scripts/check-post-publication-custody-pdf-self-test.sh
python3 -I -S -B scripts/check-post-publication-custody.py
python3 -O -I -S -B scripts/check-post-publication-custody.py
python3 -I -S -B scripts/check-post-publication-custody-self-test.py
python3 -O -I -S -B scripts/check-post-publication-custody-self-test.py

if [[ "$MODE" == "--exact" ]]; then
  scripts/check-post-publication-custody-pdf.sh --exact
else
  if scripts/check-post-publication-custody-pdf.sh --cross-toolchain; then
    echo "formal PDF set: custody-receipt cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    CUSTODY_CROSS_STATUS=$?
  fi
  if [[ "$CUSTODY_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: custody-receipt cross-toolchain refusal returned $CUSTODY_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi

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
WORKFLOW_GATE_TMPDIR="$FORMAL_TMP_ROOT"
WORKFLOW_GATE_XDG_ROOT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-formal-workflow-xdg.XXXXXX")"
WORKFLOW_GATE_XDG_CONFIG="$WORKFLOW_GATE_XDG_ROOT/config"
WORKFLOW_GATE_XDG_CACHE="$WORKFLOW_GATE_XDG_ROOT/cache"
mkdir -m 0700 -- "$WORKFLOW_GATE_XDG_CONFIG" "$WORKFLOW_GATE_XDG_CACHE"
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
  case "${WORKFLOW_GATE_XDG_ROOT:-}" in
    "$FORMAL_TMP_ROOT"/pid-rs-formal-workflow-xdg.*)
      rm -rf -- "$WORKFLOW_GATE_XDG_ROOT" || cleanup_failed=1
      ;;
    "") ;;
    *)
      echo "formal PDF set: refusing to remove unexpected workflow XDG root" >&2
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
  "TMPDIR=$WORKFLOW_GATE_TMPDIR" \
  "XDG_CONFIG_HOME=$WORKFLOW_GATE_XDG_CONFIG" \
  "XDG_CACHE_HOME=$WORKFLOW_GATE_XDG_CACHE" \
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
rm -rf -- "$WORKFLOW_GATE_XDG_ROOT"
WORKFLOW_GATE_XDG_ROOT=""
trap - EXIT INT TERM
scripts/check-support-change-tolerant-sxpid-pdf.sh "$MODE"
scripts/check-mathematical-results-guide-pdf.sh "$MODE"
scripts/check-numerical-assurance-pdf.sh "$MODE"
scripts/check-numerical-assurance-pdf-self-test.sh
scripts/check-pid2-represented-coordinate-assurance-pdf.sh "$MODE"
scripts/check-pid-sensor-placement-and-galadriel-guide-pdf.sh "$MODE"
scripts/check-sxpid3-source-marginal-audit-pdf.sh "$MODE"
scripts/check-two-source-sxpid-count-atom-bridge-pdf.sh "$MODE"

# The new mean exposition admits exact reviewed bytes only; retain fresh build evidence.
if [[ "$MODE" == "--exact" ]]; then
  MEAN_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mean-publication.XXXXXX")"
  python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --exact --check --work-dir "$MEAN_BUILD_PARENT/build"
else
  if python3 -I -S -B scripts/build-prefix-mgw-mean-pdf.py --cross-toolchain; then
    echo "formal PDF set: mean exposition cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    MEAN_CROSS_STATUS=$?
  fi
  if [[ "$MEAN_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: mean exposition refusal returned $MEAN_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi

# Recorded sensors retain discovery separately from an admitted exact reference.
OCCUPANCY_CONTROL_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-recorded-sensors-controls.XXXXXX")"
python3 -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/normal"
python3 -O -I -S -B scripts/check-recorded-office-sensors-pdf-self-test.py --work-dir "$OCCUPANCY_CONTROL_PARENT/optimized"
if [[ "$MODE" == "--exact" ]]; then
  if [[ -z "${PID_RS_OCCUPANCY_TEX_ROOT:-}" ]]; then
    echo "formal PDF set: exact recorded sensors require PID_RS_OCCUPANCY_TEX_ROOT" >&2
    exit 2
  fi
  OCCUPANCY_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-recorded-sensors.XXXXXX")"
  python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --exact --check --tex-root "$PID_RS_OCCUPANCY_TEX_ROOT" --work-dir "$OCCUPANCY_BUILD_PARENT/build"
else
  if python3 -I -S -B scripts/build-recorded-office-sensors-pdf.py --cross-toolchain; then
    echo "formal PDF set: recorded sensors cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    OCCUPANCY_CROSS_STATUS=$?
  fi
  if [[ "$OCCUPANCY_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: recorded sensors refusal returned $OCCUPANCY_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi

# Finite MGW retains discovery separately from an admitted exact reference.
MGW_FIXED_WORLD_CONTROL_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mgw-fixed-world-controls.XXXXXX")"
python3 -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/normal"
python3 -O -I -S -B scripts/check-mgw-fixed-world-pdf-self-test.py --work-dir "$MGW_FIXED_WORLD_CONTROL_PARENT/optimized"
if [[ "$MODE" == "--exact" ]]; then
  if [[ -z "${PID_RS_MGW_FIXED_WORLD_TEX_ROOT:-}" ]]; then
    echo "formal PDF set: exact finite MGW requires PID_RS_MGW_FIXED_WORLD_TEX_ROOT" >&2
    exit 2
  fi
  MGW_FIXED_WORLD_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mgw-fixed-world.XXXXXX")"
  python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --exact --check --tex-root "$PID_RS_MGW_FIXED_WORLD_TEX_ROOT" --work-dir "$MGW_FIXED_WORLD_BUILD_PARENT/build"
else
  if python3 -I -S -B scripts/build-mgw-fixed-world-pdf.py --cross-toolchain; then
    echo "formal PDF set: finite MGW cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    MGW_FIXED_WORLD_CROSS_STATUS=$?
  fi
  if [[ "$MGW_FIXED_WORLD_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: finite MGW refusal returned $MGW_FIXED_WORLD_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi

# The finite target-copy note has a committed-source builder. Its exact relation is
# source Markdown/SVG -> same-profile PDF bytes; cross-toolchain equivalence is intentionally
# refused because no reviewed alternate producer profile exists.
python3 -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py
python3 -O -I -S -B scripts/check-finite-target-copy-mgw-pdf-self-test.py
if [[ "$MODE" == "--exact" ]]; then
  if [[ -z "${PID_RS_MGW_TARGET_COPY_TEX_ROOT:-}" ]]; then
    echo "formal PDF set: exact target-copy MGW requires PID_RS_MGW_TARGET_COPY_TEX_ROOT" >&2
    exit 2
  fi
  MGW_TARGET_COPY_BUILD_PARENT="$(mktemp -d "$FORMAL_TMP_ROOT/pid-rs-mgw-target-copy.XXXXXX")"
  python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --check --tex-root "$PID_RS_MGW_TARGET_COPY_TEX_ROOT" --work-dir "$MGW_TARGET_COPY_BUILD_PARENT/build"
else
  if python3 -I -S -B scripts/build-finite-target-copy-mgw-pdf.py --cross-toolchain; then
    echo "formal PDF set: finite target-copy cross-toolchain mode unexpectedly accepted" >&2
    exit 1
  else
    MGW_TARGET_COPY_CROSS_STATUS=$?
  fi
  if [[ "$MGW_TARGET_COPY_CROSS_STATUS" -ne 2 ]]; then
    echo "formal PDF set: finite target-copy refusal returned $MGW_TARGET_COPY_CROSS_STATUS, expected 2" >&2
    exit 1
  fi
fi

# No alternate producer profile relates either bias PDF to a Linux/cross-toolchain build.
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

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: every declared formal paper has a warning-free same-toolchain result; current bias inert source/data controls passed in normal and optimized Python; committed-byte relations are exact, including the root blueprint and post-publication custody receipt, and the source and renderer-fragment inventories are exact"
else
  echo "OK: every declared paper with a reviewed cross-toolchain profile passed its warning-free bounded gate; the root blueprint, post-publication custody receipt, mean exposition, recorded-sensor document, finite MGW paper, target-copy MGW note, full bias paper and bias summary intentionally have no accepted cross-toolchain relation, and all eight status-2 refusals plus the source and renderer-fragment inventories are exact"
fi
