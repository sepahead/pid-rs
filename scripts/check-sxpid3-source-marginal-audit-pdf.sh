#!/usr/bin/env bash
# Method catalog: validation.sxpid3-source-marginal-bounded-audit
set -euo pipefail
unset BASH_ENV ENV

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-sxpid3-source-marginal-audit-pdf.sh"
BUILDER_SELF_TEST="$ROOT/scripts/check-sxpid3-source-marginal-audit-builder-self-test.sh"
COMMITTED="$ROOT/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
FIGURE_ASSET_CHECK="$ROOT/scripts/check-mathematical-results-guide-figure-assets.py"
MODE="${1:---exact}"
CHECK_NAME="SxPID3 source-marginal/bounded-audit PDF check"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
for command_name in awk bash cat cmp diff grep mktemp pdffonts pdfinfo pdftotext python3 rm shasum sort; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
if [[ "${BASH:-}" != /* || ! -f "$BASH" || -L "$BASH" || ! -x "$BASH" ]]; then
  echo "$CHECK_NAME: current Bash executable is not a direct executable file" >&2
  exit 2
fi

capture_directory_identity() {
  python3 -I -S -B - "$1" <<'PY'
import os
import stat
import sys

try:
    metadata = os.lstat(sys.argv[1])
except OSError:
    raise SystemExit(1)
if metadata.st_uid != os.geteuid() or not stat.S_ISDIR(metadata.st_mode):
    raise SystemExit(1)
print(f"{metadata.st_dev}:{metadata.st_ino}")
PY
}

directory_has_identity() {
  local observed
  observed="$(capture_directory_identity "$1")" || return 1
  [[ "$observed" == "$2" ]]
}
for path in \
    "$BUILDER" \
    "$BUILDER_SELF_TEST" \
    "$ROOT/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md" \
    "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/header.tex" \
    "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/filter.lua" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.pdf" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.svg" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.pdf" \
    "$FIGURE_ASSET_CHECK" \
    "$COMMITTED"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required input absent, non-regular, or symbolic: $path" >&2
    exit 1
  fi
done
python3 -I -B -c 'import pypdf' >/dev/null 2>&1 || {
  echo "$CHECK_NAME: pypdf is required for canonical figure-asset validation" >&2
  exit 2
}
python3 -I -B "$FIGURE_ASSET_CHECK"
python3 -O -I -B "$FIGURE_ASSET_CHECK"
/usr/bin/env -i PATH="$PATH" HOME="${HOME:-/tmp}" TMPDIR="${TMPDIR:-/tmp}" \
  LC_ALL=C LANG=C TZ=UTC "$BASH" --noprofile --norc "$BUILDER_SELF_TEST"

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
if ! TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"; then
  echo "$CHECK_NAME: cannot canonicalize temporary root: $TMP_BASE_INPUT" >&2
  exit 2
fi
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT_LEXICAL="$(mktemp -d "$TMP_BASE/pid-rs-sxpid3-audit-check.XXXXXX")"
if [[ ! -d "$BUILD_ROOT_LEXICAL" || -L "$BUILD_ROOT_LEXICAL" ]] \
    || ! BUILD_ROOT="$(CDPATH='' cd -- "$BUILD_ROOT_LEXICAL" && pwd -P)"; then
  echo "$CHECK_NAME: mktemp did not create a direct directory" >&2
  exit 2
fi
BUILD_ROOT_NAME="${BUILD_ROOT##*/}"
if [[ "$BUILD_ROOT_LEXICAL" != "$BUILD_ROOT" \
    || "$BUILD_ROOT" != "$TMP_BASE/$BUILD_ROOT_NAME" \
    || ! "$BUILD_ROOT_NAME" =~ ^pid-rs-sxpid3-audit-check\.[[:alnum:]]+$ ]]; then
  echo "$CHECK_NAME: mktemp returned an unexpected build directory" >&2
  exit 2
fi
if ! BUILD_ROOT_ID="$(capture_directory_identity "$BUILD_ROOT")"; then
  echo "$CHECK_NAME: mktemp build directory lacks fresh-object custody" >&2
  exit 2
fi
cleanup() {
  local status=$?
  if [[ "$BUILD_ROOT" == "$TMP_BASE/$BUILD_ROOT_NAME" \
      && "$BUILD_ROOT_NAME" =~ ^pid-rs-sxpid3-audit-check\.[[:alnum:]]+$ \
      && -d "$BUILD_ROOT" && ! -L "$BUILD_ROOT" ]] \
      && directory_has_identity "$BUILD_ROOT" "$BUILD_ROOT_ID"; then
    rm -rf -- "$BUILD_ROOT"
  elif [[ -e "$BUILD_ROOT" || -L "$BUILD_ROOT" ]]; then
    echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2
    status=1
  fi
  return "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

BUILT="$BUILD_ROOT/built.pdf"
/usr/bin/env -i PATH="$PATH" HOME="${HOME:-$BUILD_ROOT}" TMPDIR="${TMPDIR:-/tmp}" \
  PID_RS_PDF_TMPDIR="$BUILD_ROOT" LC_ALL=C LANG=C TZ=UTC \
  "$BASH" --noprofile --norc "$BUILDER" "$MODE" "$BUILT" \
  >"$BUILD_ROOT/build.stdout" 2>"$BUILD_ROOT/build.stderr" || {
    cat "$BUILD_ROOT/build.stdout" "$BUILD_ROOT/build.stderr" >&2
    exit 1
  }
if [[ -s "$BUILD_ROOT/build.stderr" ]]; then
  cat "$BUILD_ROOT/build.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi

validate_pdf() {
  local label="$1" pdf="$2"
  local info="$BUILD_ROOT/$label.info" fonts="$BUILD_ROOT/$label.fonts"
  local text="$BUILD_ROOT/$label.txt" urls="$BUILD_ROOT/$label.urls"
  local observed_urls="$BUILD_ROOT/$label.observed-urls"
  local expected_urls="$BUILD_ROOT/$label.expected-urls"
  LC_ALL=C pdfinfo "$pdf" >"$info"
  LC_ALL=C pdffonts "$pdf" >"$fonts"
  LC_ALL=C pdftotext -layout "$pdf" "$text"
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$info")"
  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 15 || "$pages" -gt 60 ]]; then
    echo "$CHECK_NAME: $label has implausible page count: ${pages:-missing}" >&2
    exit 1
  fi
  grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$info" || {
    echo "$CHECK_NAME: $label is not A4" >&2
    exit 1
  }
  grep -Eq '^Tagged:[[:space:]]+yes$' "$info" || {
    echo "$CHECK_NAME: $label lacks a PDF structure tree" >&2
    exit 1
  }
  awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$fonts" || {
    echo "$CHECK_NAME: $label has nonembedded or non-Unicode fonts" >&2
    exit 1
  }
  for sentinel in 'fresh owner-controlled HTTPS' 'separate exact compatibility edge' \
      '18/108/166 crosswalk' '20,348 tables' '2,197,584' \
      'complete certificate' 'Averaged informative component' \
      'Averaged misinformative component' 'compatibility-literal rejections' \
      'exact type, shape, and value' 'disposable-checkout integrity failure' \
      'Explicit nonclaims and negative results'; do
    grep -Fiq -- "$sentinel" "$text" || {
      echo "$CHECK_NAME: $label lacks rendered sentinel: $sentinel" >&2
      exit 1
    }
  done
  if grep -Fq $'\357\277\275' "$text"; then
    echo "$CHECK_NAME: $label contains a Unicode replacement character" >&2
    exit 1
  fi
  local raw_fragment
  for raw_fragment in '$$' '\log' '\mathcal' '\left' '\right' '\sum' '\cdot' \
      '\alpha' '\forall' '\exists'; do
    if grep -Fq -- "$raw_fragment" "$text"; then
      echo "$CHECK_NAME: $label exposes raw TeX in visible text: $raw_fragment" >&2
      exit 1
    fi
  done
  if grep -Eq '^[[:space:]]*[0-9]+([.][0-9]+)?[[:space:]]+[0-9]+([.][0-9]+)*[.][[:space:]]' "$text"; then
    echo "$CHECK_NAME: $label contains a doubly numbered section heading" >&2
    exit 1
  fi
  python3 -I -S -B - "$text" <<'PY'
import pathlib
import sys

pages = [" ".join(page.split()) for page in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").split("\f")]

def require_same_page(label, first, second):
    if not any(first in page and second in page for page in body_pages):
        raise SystemExit(f"pagination contract failed for {label}")

abstract_pages = [page for page in pages if "This report documents three related but logically separate" in page]
if len(abstract_pages) != 1 or "Contents" in abstract_pages[0]:
    raise SystemExit("pagination contract failed for fresh-page abstract")
contents_pages = [
    page for page in pages
    if "Contents" in page
    and "Status and claim boundary" in page
    and "Reproduction entry points" in page
]
if len(contents_pages) != 1:
    raise SystemExit("pagination contract failed for unique contents page")
body_pages = [page for page in pages if page not in contents_pages]
require_same_page("paired Dedekind equations", "𝑀 (3) − 2 = 20 − 2 = 18", "𝑀 (4) − 2 = 168 − 2 = 166")
require_same_page("paper event distinction", "Paper event semantics: Equation (4) is not Equation (6)", "MGW Equation (4) and Equations (5)")
require_same_page("crosswalk heading and body", "The 18/108/166 crosswalk", "The source arity determines the carrier")
require_same_page("zeta lead-in and inverse display", "With cumulatives as rows and atoms as columns, define", "Π𝑢𝑖 =")
require_same_page("fixed-inverse lead-in and display", "and, for one fixed Möbius inverse", "Π𝑢 =")
require_same_page("averaged-cumulative lead-in and display", "For every component", "𝐼𝛼𝑢 (𝑃 ) =")
require_same_page("prohibited-transfer result", "Standing assumptions for this counterexample", "under both laws, while")
require_same_page("prohibited-transfer heading and body", "Retained prohibited-transfer witness", "Standing assumptions for this counterexample")
require_same_page("source-cylinder component boundary", "the averaged informative component stays at ln 2 nats", "Its averaged misinformative component changes from ln 2 to 0 nats")
require_same_page("separate-marginals witness laws", "Standing assumptions for the separate-marginals counterexample", "𝑄𝑆 =")
require_same_page("fixed-matrix continuity display", "For one fixed matrix", "The support-change theorem applies because")
require_same_page("total-variation radius sharpening", "total-variation radius sharpening", "Marginalization is a contraction in total variation")
require_same_page("total-variation non-strictness", "total-variation radius sharpening", "no strict improvement is guaranteed")
require_same_page("total-variation residual caveat", "total-variation radius sharpening", "residual-entropy term changes")
require_same_page("total-variation component boundary", "total-variation radius sharpening", "transfer to the misinformative or signed-net components")
require_same_page("total-variation statistical nonclaim", "total-variation radius sharpening", "deterministic stability statement, not a confidence bound")
require_same_page("total-variation random-radius nonclaim", "total-variation radius sharpening", "A separate statistical theorem is required")
require_same_page("finite-count opening definition", "There are exactly three ordered binary sources", "𝒵+ =")
require_same_page("three local count forms", "Substitution into the three law-level definitions", "𝑖net")
require_same_page("three cumulative products", "For each cumulative, the exact positive-rational products are", "𝑄net")
require_same_page("table-count totals lead-in and display", "The totals contribute respectively", "16, 136, 816, 3,876, 15,504")
require_same_page("table-count heading and opening", "Why there are 20,348 tables", "Standing assumptions for this count")
require_same_page("route-limit paragraph", "Source inspection and hostile tests found", "The correct description is therefore")
require_same_page("receipt lead-in and list", "The authoritative receipt is the source-bound bounded-audit receipt", "the receipt schema and exact source inputs")
require_same_page("negative-witness conclusion", "Hence", "Πnet 02+04")
require_same_page("formal-evidence heading and opening", "Formal, executable, and receipt evidence", "Factorization-result evidence")
require_same_page("estimator-boundary paragraph", "No new estimator is required to evaluate these deterministic identities", "treated as a transparent bridge")
require_same_page("nonclaim heading and opening", "Explicit nonclaims and negative results", "The factorization does not extend in general")
require_same_page("nonclaim final pair", "Within each census block, every labelled-table/antichain-key pair has unit weight", "The receipt provides repository custody")
require_same_page("reproduction tail", "The underlying exact lanes and their hostile tests are", "The two-source count/event bridge")
reference_pages = [
    page for page in body_pages if "References" in page and "Abdullah Makkeh" in page
]
if len(reference_pages) != 1 or "The two-source count/event bridge" in reference_pages[0]:
    raise SystemExit("pagination contract failed for fresh-page references")
require_same_page("Ehrlich reference item", "David A. Ehrlich", "Shared Exclusions")
PY
  LC_ALL=C pdfinfo -url "$pdf" >"$urls"
  if ! awk 'NR==1{next} NF==0{next} NF!=3{bad=1;next} {print $3} END{exit bad}' \
      "$urls" | LC_ALL=C sort -u >"$observed_urls"; then
    echo "$CHECK_NAME: $label contains malformed or unapproved URI" >&2
    exit 1
  fi
  cat >"$expected_urls" <<'EOF'
https://arxiv.org/abs/1004.2515
https://arxiv.org/abs/2002.03356v5
https://doi.org/10.1007/BF00531932
https://doi.org/10.1098/rspa.2021.0110
https://doi.org/10.1103/PhysRevE.103.032149
https://doi.org/10.1103/PhysRevE.110.014115
https://doi.org/10.3390/e16042161
https://github.com/sepahead/pid-rs/blob/main/SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md
https://github.com/sepahead/pid-rs/blob/main/audit/archive/sxpid3-s1-historical-checkers-v1/DISPOSITION.md
https://github.com/sepahead/pid-rs/blob/main/audit/evidence/sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-2026-08-26.json
https://github.com/sepahead/pid-rs/blob/main/audit/evidence/sxpid3-mgw-v5-program-a-semantic-bridge-v4.json
https://github.com/sepahead/pid-rs/blob/main/audit/evidence/sxpid3-pdf-checkout-integrity-incident-2026-09-04.md
https://github.com/sepahead/pid-rs/blob/main/audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md
https://github.com/sepahead/pid-rs/blob/main/audit/formal/lean-sxpid3-informative-invariance/PidSxPid3InformativeInvariance.lean
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/decision-v3.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/evidence-adjudication-index.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/failures/python-status-type-coercion.md
https://github.com/sepahead/pid-rs/blob/main/claims/SX-CERTIFIED-AVERAGED-PID3-001/source-correspondence-v4.md
https://oeis.org/A000372
EOF
  if ! cmp -s "$expected_urls" "$observed_urls"; then
    echo "$CHECK_NAME: $label hyperlink target set changed" >&2
    diff -u "$expected_urls" "$observed_urls" >&2 || true
    exit 1
  fi
  local target
  while IFS= read -r target; do
    case "$target" in
      https://github.com/sepahead/pid-rs/blob/main/*)
        target="${target#https://github.com/sepahead/pid-rs/blob/main/}"
        if [[ ! -f "$ROOT/$target" || -L "$ROOT/$target" ]]; then
          echo "$CHECK_NAME: $label repository hyperlink target is absent or symbolic: $target" >&2
          exit 1
        fi
        ;;
    esac
  done <"$observed_urls"
}

validate_pdf built "$BUILT"
validate_pdf committed "$COMMITTED"

if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$BUILT" "$COMMITTED" || {
    echo "$CHECK_NAME: committed PDF is stale or not same-toolchain reproducible" >&2
    exit 1
  }
else
  cmp -s "$BUILD_ROOT/built.txt" "$BUILD_ROOT/committed.txt" || {
    echo "$CHECK_NAME: extracted text changed across toolchains" >&2
    exit 1
  }
  grep -E '^(Pages|Page size):' "$BUILD_ROOT/built.info" >"$BUILD_ROOT/built.geometry"
  grep -E '^(Pages|Page size):' "$BUILD_ROOT/committed.info" >"$BUILD_ROOT/committed.geometry"
  cmp -s "$BUILD_ROOT/built.geometry" "$BUILD_ROOT/committed.geometry" || {
    echo "$CHECK_NAME: geometry changed across toolchains" >&2
    exit 1
  }
fi

echo "OK: $CHECK_NAME passed ($(shasum -a 256 "$BUILT" | awk '{print $1}'))"
