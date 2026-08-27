#!/usr/bin/env bash
# Method catalog: validation.sxpid3-source-marginal-bounded-audit
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-sxpid3-source-marginal-audit-pdf.sh"
COMMITTED="$ROOT/output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf"
MODE="${1:---exact}"
CHECK_NAME="SxPID3 source-marginal/bounded-audit PDF check"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
for command_name in awk bash cat cmp diff grep mktemp pdffonts pdfinfo pdftotext rm shasum sort; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
for path in \
    "$BUILDER" \
    "$ROOT/SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md" \
    "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/header.tex" \
    "$ROOT/audit/formal/latex/sxpid3-source-marginal-and-bounded-audit/filter.lua" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/source-cylinder-factorization.svg" \
    "$COMMITTED"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required input absent, non-regular, or symbolic: $path" >&2
    exit 1
  fi
done

TMP_BASE="${TMPDIR:-/tmp}"
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-sxpid3-audit-check.XXXXXX")"
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-sxpid3-audit-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *) echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2 ;;
  esac
}
trap cleanup EXIT INT TERM

BUILT="$BUILD_ROOT/built.pdf"
PID_RS_PDF_TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$BUILT" \
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
  awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$fonts" || {
    echo "$CHECK_NAME: $label has nonembedded or non-Unicode fonts" >&2
    exit 1
  }
  for sentinel in '18/108/166 crosswalk' '20,348 tables' '2,197,584' \
      'complete certificate' 'Explicit nonclaims and negative results'; do
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
  LC_ALL=C pdfinfo -url "$pdf" >"$urls"
  if ! awk 'NR==1{next} NF==0{next} NF!=3{bad=1;next} {print $3} END{exit bad}' \
      "$urls" | LC_ALL=C sort -u >"$observed_urls"; then
    echo "$CHECK_NAME: $label contains malformed or unapproved URI" >&2
    exit 1
  fi
  cat >"$expected_urls" <<'EOF'
../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md
../../audit/evidence/sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-2026-08-26.json
../../audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md
../../audit/formal/lean-sxpid3-informative-invariance/PidSxPid3InformativeInvariance.lean
https://arxiv.org/abs/1004.2515
https://arxiv.org/abs/2002.03356v5
https://doi.org/10.1007/BF00531932
https://doi.org/10.1098/rspa.2021.0110
https://doi.org/10.1103/PhysRevE.103.032149
https://doi.org/10.1103/PhysRevE.110.014115
https://doi.org/10.3390/e16042161
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
      ../../*)
        target="${target#../../}"
        if [[ ! -f "$ROOT/$target" || -L "$ROOT/$target" ]]; then
          echo "$CHECK_NAME: $label local hyperlink target is absent or symbolic: $target" >&2
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
