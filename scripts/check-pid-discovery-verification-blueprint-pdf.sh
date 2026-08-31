#!/usr/bin/env bash
# Verify only the canonical, same-toolchain blueprint publication relation.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-pid-discovery-verification-blueprint.sh"
SOURCE="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md"
COMMITTED="$ROOT/PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.pdf"
HEADER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-header.tex"
FILTER="$ROOT/audit/formal/latex/pid-discovery-verification-and-durability-blueprint-filter.lua"
FIGURE_DIRECTORY="$ROOT/audit/formal/latex/figures/pid-discovery-verification-and-durability-blueprint"
SELF_TEST="$ROOT/scripts/check-pid-discovery-verification-blueprint-pdf-self-test.sh"
DECISION_V2="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md"
EVIDENCE_ADJUDICATION_INDEX="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md"
CONVENTIONS="$ROOT/claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md"
DECISION_V2_SHA256="f5bfef2afa6237661e031d416497e17f2aad01b17de61f15e9aba1a6e9ff6c59"
EVIDENCE_ADJUDICATION_INDEX_SHA256="0410df9f4163d2ccd2e4bb993fed9fd3d1598fae13bd3bc58cf30784966bbab4"
CONVENTIONS_SHA256="2d14bea9d6f0a2d07493ddaf7d89a130f4ad62680319cb9efba465590c2250c7"
CHECK_NAME="PID discovery/verification/durability blueprint PDF check"
MODE="${1:---exact}"

if [[ "$#" -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain equivalence relation or producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi

for command_name in awk bash cmp find grep mktemp pdffonts pdfinfo pdftoppm pdftotext \
    rm shasum wc; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done

required_inputs=(
  "$BUILDER"
  "$SOURCE"
  "$COMMITTED"
  "$HEADER"
  "$FILTER"
  "$SELF_TEST"
  "$DECISION_V2"
  "$EVIDENCE_ADJUDICATION_INDEX"
  "$CONVENTIONS"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-source-card.svg"
  "$FIGURE_DIRECTORY/semantic-transfer-firewall-pid-card.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-stages.svg"
  "$FIGURE_DIRECTORY/durable-promotion-state-machine-storage.svg"
)
for required_input in "${required_inputs[@]}"; do
  if [[ ! -f "$required_input" || -L "$required_input" ]]; then
    echo "$CHECK_NAME: required input is absent, non-regular, or symbolic: $required_input" >&2
    exit 1
  fi
done

require_sha256() {
  local path="$1" expected="$2" label="$3"
  local observed
  observed="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$observed" != "$expected" ]]; then
    echo "$CHECK_NAME: $label identity drifted: expected $expected, observed $observed" >&2
    exit 1
  fi
}

require_unique_line() {
  local path="$1" literal="$2" label="$3"
  local count
  count="$(grep -Fxc -- "$literal" "$path" || true)"
  if [[ "$count" != "1" ]]; then
    echo "$CHECK_NAME: $label drifted; expected one exact line, observed $count" >&2
    exit 1
  fi
}

require_unique_fragment() {
  local path="$1" literal="$2" label="$3"
  local count
  count="$(grep -Fc -- "$literal" "$path" || true)"
  if [[ "$count" != "1" ]]; then
    echo "$CHECK_NAME: $label drifted; expected one exact fragment, observed $count" >&2
    exit 1
  fi
}

require_sha256 "$DECISION_V2" "$DECISION_V2_SHA256" "decision-v2 current-evidence"
require_sha256 "$EVIDENCE_ADJUDICATION_INDEX" "$EVIDENCE_ADJUDICATION_INDEX_SHA256" \
  "evidence-adjudication index"
require_sha256 "$CONVENTIONS" "$CONVENTIONS_SHA256" "frozen SxPID3 conventions"

require_unique_line "$DECISION_V2" '**Disposition: proposed/open.**' \
  "decision-v2 disposition boundary"
require_unique_line "$DECISION_V2" \
  '**Complete target-implication evidence label: no accepted end-to-end evidence.**' \
  "decision-v2 complete-target boundary"
require_unique_fragment "$DECISION_V2" \
  'Neither result closes the prospective certificate implication.' \
  "decision-v2 scoped-result boundary"
require_unique_fragment "$DECISION_V2" \
  '| A: source and combinatorial semantics | Partial |' \
  "decision-v2 Program A status"
require_unique_fragment "$DECISION_V2" \
  '| B: dual formal semantics | Partial at the generic algebra layer |' \
  "decision-v2 Program B status"
require_unique_fragment "$DECISION_V2" \
  '| C: certified numerics | Bounded exact sign/zero partial result |' \
  "decision-v2 Program C status"
require_unique_fragment "$DECISION_V2" \
  '| D: compiled Rust refinement | Lexical routing observation only |' \
  "decision-v2 Program D status"
require_unique_fragment "$DECISION_V2" \
  '| E: replay, provenance, and adjudication | Source-bound local receipt and partial mutation evidence |' \
  "decision-v2 Program E status"
require_unique_fragment "$DECISION_V2" \
  '- 108 PID atoms, lattice nodes, or independent degrees of freedom;' \
  "decision-v2 108-expression taxonomy"
require_unique_fragment "$DECISION_V2" \
  '- the 166-position SxPID4 lattice;' \
  "decision-v2 four-source boundary"
require_unique_line "$EVIDENCE_ADJUDICATION_INDEX" \
  '| 1 | 2 | [claim-v1.md](claim-v1.md) | [decision-v2.md](decision-v2.md) | [evidence-matrix-v2.md](evidence-matrix-v2.md) | Current proposed/open decision; two scoped sub-results receive credit, but Programs A--E remain open |' \
  "evidence-adjudication current pointer/status boundary"
require_unique_fragment "$SOURCE" \
  'Decision record 2 keeps the complete target **proposed/open**;' \
  "blueprint current-decision summary"
require_unique_fragment "$SOURCE" \
  'None closes an end-to-end implication, and this report does not close the claim.' \
  "blueprint Program A--E status summary"

for required_link in \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v2.md' \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md' \
    'claims/SX-CERTIFIED-AVERAGED-PID3-001/conventions.md#the-complete-18-node-carrier'; do
  if ! grep -Fq "]($required_link)" "$SOURCE"; then
    echo "$CHECK_NAME: source lacks required current-evidence link: $required_link" >&2
    exit 1
  fi
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
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-blueprint-pdf-check.XXXXXX")"
cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-blueprint-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

BUILT="$BUILD_ROOT/rebuilt.pdf"
if ! TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$BUILT" \
    >"$BUILD_ROOT/builder.stdout" 2>"$BUILD_ROOT/builder.stderr"; then
  cat "$BUILD_ROOT/builder.stdout" "$BUILD_ROOT/builder.stderr" >&2
  echo "$CHECK_NAME: builder failed" >&2
  exit 1
fi
if [[ -s "$BUILD_ROOT/builder.stderr" ]]; then
  cat "$BUILD_ROOT/builder.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi

validate_pdf() {
  local label="$1" pdf="$2"
  local info="$BUILD_ROOT/$label.pdfinfo"
  local fonts="$BUILD_ROOT/$label.pdffonts"
  local text="$BUILD_ROOT/$label.txt"
  local render_prefix="$BUILD_ROOT/$label-page"

  LC_ALL=C pdfinfo "$pdf" >"$info"
  LC_ALL=C pdffonts "$pdf" >"$fonts"
  LC_ALL=C pdftotext -layout "$pdf" "$text"
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$info")"
  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 18 || "$pages" -gt 32 ]]; then
    echo "$CHECK_NAME: $label has implausible page count: ${pages:-missing}" >&2
    exit 1
  fi
  if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$info"; then
    echo "$CHECK_NAME: $label is not A4" >&2
    exit 1
  fi
  for metadata in \
      '^Tagged:[[:space:]]+no$' \
      '^Form:[[:space:]]+none$' \
      '^JavaScript:[[:space:]]+no$' \
      '^Encrypted:[[:space:]]+no$'; do
    if ! grep -Eq "$metadata" "$info"; then
      echo "$CHECK_NAME: $label PDF metadata omitted: $metadata" >&2
      exit 1
    fi
  done
  if ! awk '
    NR <= 2 { next }
    NF == 0 { next }
    { seen = 1; if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1 }
    END { exit (!seen || bad) }
  ' "$fonts"; then
    echo "$CHECK_NAME: $label has a nonembedded or non-Unicode-mapped font" >&2
    exit 1
  fi
  for sentinel in \
      'PrimeGapsLib observations are dated 19 August 2026' \
      'Decision record 2 keeps the complete target' \
      '108 keyed scalar audit expressions' \
      'Current 31 August 2026 adversarial publication closure' \
      'Fifty named hostile lenses' \
      'Ten materially distinct routes' \
      'Semantic transfer firewall, part 1' \
      'Semantic transfer firewall, part 2' \
      'Durable promotion state machine, part 1' \
      'Durable promotion state machine, part 2' \
      'There is no accepted cross-toolchain equivalence relation' \
      'Source-anchored claim register'; do
    if ! grep -Fq "$sentinel" "$text"; then
      echo "$CHECK_NAME: $label lacks rendered sentinel: $sentinel" >&2
      exit 1
    fi
  done
  if grep -Fq $'\357\277\275' "$text"; then
    echo "$CHECK_NAME: $label contains a Unicode replacement character" >&2
    exit 1
  fi
  if grep -Eq '\\begin\{|\\end\{|\.pdf\.pdf|[0-9]+\.[0-9]+\.[0-9]+\.' "$text"; then
    echo "$CHECK_NAME: $label exposes raw TeX, a doubled PDF suffix, or a doubly numbered heading" >&2
    exit 1
  fi
  pdftoppm -f 1 -l "$pages" -r 36 -png "$pdf" "$render_prefix" >/dev/null 2>&1
  local rendered_count
  rendered_count="$(find "$BUILD_ROOT" -maxdepth 1 -type f -name "$label-page-*.png" -size +0c | wc -l | awk '{print $1}')"
  if [[ "$rendered_count" != "$pages" ]]; then
    echo "$CHECK_NAME: $label did not render every nonempty page" >&2
    exit 1
  fi
}

validate_pdf rebuilt "$BUILT"
validate_pdf committed "$COMMITTED"

if ! cmp -s "$BUILT" "$COMMITTED"; then
  echo "$CHECK_NAME: committed PDF is stale or not same-toolchain reproducible" >&2
  exit 1
fi

printf 'OK: %s exact committed-byte relation passed (sha256=%s)\n' \
  "$CHECK_NAME" "$(shasum -a 256 "$COMMITTED" | awk '{print $1}')"
