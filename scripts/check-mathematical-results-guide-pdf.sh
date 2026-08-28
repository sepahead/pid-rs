#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-mathematical-results-guide-pdf.sh"
COMMITTED="$ROOT/output/pdf/mathematical-results-guide.pdf"
MODE="${1:---exact}"
CHECK_NAME="Mathematical results guide PDF check"
PROSE_CHECK="$ROOT/scripts/check-mathematical-results-guide-prose.py"
PROSE_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-prose-self-test.py"
BUILDER_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-builder-self-test.sh"
STRUCTURE_CHECK="$ROOT/scripts/check-mathematical-results-guide-pdf-structure.py"
STRUCTURE_SELF_TEST="$ROOT/scripts/check-mathematical-results-guide-pdf-structure-self-test.py"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || {
  echo "$CHECK_NAME: missing command: python3" >&2
  exit 2
}
for guide_gate in "$PROSE_CHECK" "$PROSE_SELF_TEST" "$BUILDER_SELF_TEST" \
    "$STRUCTURE_CHECK" "$STRUCTURE_SELF_TEST"; do
  if [[ ! -f "$guide_gate" || -L "$guide_gate" ]]; then
    echo "$CHECK_NAME: guide gate absent, non-regular, or symbolic: $guide_gate" >&2
    exit 1
  fi
done
for command_name in awk bash cat cmp diff find grep mktemp pdffonts pdfinfo pdftoppm \
    pdftotext python3 rm shasum sort wc; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $command_name" >&2
    exit 2
  }
done
python3 -I -B -c 'import pypdf' >/dev/null 2>&1 || {
  echo "$CHECK_NAME: missing Python package: pypdf" >&2
  exit 2
}
for path in \
    "$BUILDER" \
    "$ROOT/MATHEMATICAL_RESULTS_GUIDE.md" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/header.tex" \
    "$ROOT/audit/formal/latex/mathematical-results-guide/filter.lua" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/semantic-firewall.svg" \
    "$ROOT/audit/formal/latex/figures/mathematical-results-guide/result-evidence-map.svg" \
    "$ROOT/audit/formal/latex/figures/sxpid3-source-marginal-and-bounded-audit/audit-coordinate-crosswalk.svg" \
    "$COMMITTED"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required input absent, non-regular, or symbolic: $path" >&2
    exit 1
  fi
done

bash --noprofile --norc "$BUILDER_SELF_TEST"
python3 -I -B "$PROSE_CHECK"
python3 -O -I -B "$PROSE_CHECK"
python3 -I -B "$PROSE_SELF_TEST"
python3 -O -I -B "$PROSE_SELF_TEST"
python3 -I -B "$STRUCTURE_SELF_TEST" "$COMMITTED"
python3 -O -I -B "$STRUCTURE_SELF_TEST" "$COMMITTED"

HEADER="$ROOT/audit/formal/latex/mathematical-results-guide/header.tex"
for design_contract in \
    '\definecolor{PidNavy}{HTML}{2C3E50}' \
    '\definecolor{PidTeal}{HTML}{1F6968}' \
    '\definecolor{PidBronze}{HTML}{916400}' \
    '\definecolor{PidGold}{HTML}{DCA520}' \
    '\definecolor{PidPaper}{HTML}{F7F3E9}' \
    '{\Large\bfseries\color{PidNavy}}' \
    '{\large\bfseries\color{PidTeal}}'; do
  grep -Fq -- "$design_contract" "$HEADER" || {
    echo "$CHECK_NAME: source design contract absent: $design_contract" >&2
    exit 1
  }
done
if grep -Eq '\\fontsize\{(2[4-9]|[3-9][0-9])\}[^\n]*\\color\{PidTeal\}' "$HEADER"; then
  echo "$CHECK_NAME: PidTeal must not style a large title" >&2
  exit 1
fi

TMP_BASE="${TMPDIR:-/tmp}"
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-mathematical-results-guide-check.XXXXXX")"
cleanup() {
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-mathematical-results-guide-check.*) rm -rf -- "$BUILD_ROOT" ;;
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
  local text="$BUILD_ROOT/$label.txt"
  local observed_urls="$BUILD_ROOT/$label.observed-urls"
  local observed_navigation="$BUILD_ROOT/$label.observed-navigation"
  local optimized_urls="$BUILD_ROOT/$label.optimized-urls"
  local optimized_navigation="$BUILD_ROOT/$label.optimized-navigation"
  local expected_urls="$BUILD_ROOT/$label.expected-urls"
  LC_ALL=C pdfinfo "$pdf" >"$info" 2>"$BUILD_ROOT/$label.info.stderr"
  LC_ALL=C pdffonts "$pdf" >"$fonts" 2>"$BUILD_ROOT/$label.fonts.stderr"
  LC_ALL=C pdftotext -layout "$pdf" "$text" 2>"$BUILD_ROOT/$label.text.stderr"
  local parser_stderr
  for parser_stderr in "$BUILD_ROOT/$label.info.stderr" "$BUILD_ROOT/$label.fonts.stderr" \
      "$BUILD_ROOT/$label.text.stderr"; do
    if [[ -s "$parser_stderr" ]]; then
      cat "$parser_stderr" >&2
      echo "$CHECK_NAME: $label caused PDF parser diagnostics" >&2
      exit 1
    fi
  done
  local pages
  pages="$(awk '/^Pages:/ {print $2}' "$info")"
  if [[ ! "$pages" =~ ^[0-9]+$ || "$pages" -lt 14 || "$pages" -gt 60 ]]; then
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
  grep -Eq '^Suspects:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label is structurally suspect" >&2
    exit 1
  }
  grep -Eq '^Form:[[:space:]]+none$' "$info" || {
    echo "$CHECK_NAME: $label contains an interactive form" >&2
    exit 1
  }
  grep -Eq '^JavaScript:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label contains JavaScript" >&2
    exit 1
  }
  grep -Eq '^Encrypted:[[:space:]]+no$' "$info" || {
    echo "$CHECK_NAME: $label is encrypted" >&2
    exit 1
  }
  grep -Eq '^Page rot:[[:space:]]+0$' "$info" || {
    echo "$CHECK_NAME: $label has a rotated page" >&2
    exit 1
  }
  grep -Eq '^PDF version:[[:space:]]+1[.]7$' "$info" || {
    echo "$CHECK_NAME: $label is not PDF 1.7" >&2
    exit 1
  }
  awk 'NR<=2{next} NF==0{next} {seen=1;if($(NF-4)!="yes"||$(NF-2)!="yes")bad=1} END{exit(!seen||bad)}' "$fonts" || {
    echo "$CHECK_NAME: $label has nonembedded or non-Unicode fonts" >&2
    exit 1
  }
  for sentinel in \
      'Non-authoritative guide' \
      'Five distinct lanes' \
      'Five lanes. No silent transfer.' \
      'Three different counts for three different objects' \
      'Eight families, four evidence questions' \
      'Fixed finite-alphabet plug-in convergence' \
      'Support-change-tolerant averaged-Sx continuity' \
      'Dependency-color concentration' \
      'Exact two-source categorical-Sx assurance' \
      '20,348' \
      '2,197,584' \
      'Represented-binary64 and quantizer assurance' \
      'repository/publication integration remains NO-GO' \
      'These workflows preserve evidence'; do
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
  for raw_fragment in '$$' '\\log' '\\mathcal' '\\left' '\\right' '\\sum' '\\cdot' \
      '\\alpha' '\\forall' '\\exists' '\\operatorname'; do
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
    if not any(first in page and second in page for page in pages):
        raise SystemExit(f"pagination contract failed for {label}")

contracts = [
    ("foundational opening", "Foundational semantic audit", "Scope and formula"),
    ("plug-in opening", "Fixed finite-alphabet plug-in convergence", "Assumptions/result"),
    ("continuity opening", "Support-change-tolerant averaged-Sx continuity", "The result fixes three objects"),
    ("continuity-to-sampling transition", "The result applies when rare cells enter/leave", "Sampling and exact finite-table assurance"),
    ("sampling section opening", "Sampling and exact finite-table assurance", "Dependency-color concentration"),
    ("dependency opening", "Dependency-color concentration", "Complete rows"),
    ("two-source opening", "Exact two-source categorical-Sx assurance", "Exactly two finite categorical sources"),
    ("SxPID3 opening", "SxPID3 source-marginal factorization", "The factorization assumes"),
    ("binary64 opening", "Represented-binary64 and quantizer assurance", "Every finite binary64 number"),
    ("KSG opening", "KSG positive-integer harmonic arithmetic", "Revision 4 is active"),
    ("semantic figure", "Five lanes. No silent transfer.", "No equality"),
    ("evidence figure", "Eight families, four evidence questions", "Dedicated result PDF open"),
    ("crosswalk figure", "Three different counts for three different objects", "Retaining all six views"),
]
for contract in contracts:
    require_same_page(*contract)
PY

  if ! python3 -I -B "$STRUCTURE_CHECK" "$pdf" "$observed_urls" "$observed_navigation" \
      >"$BUILD_ROOT/$label.structure.stdout" 2>"$BUILD_ROOT/$label.structure.stderr"; then
    cat "$BUILD_ROOT/$label.structure.stdout" "$BUILD_ROOT/$label.structure.stderr" >&2
    exit 1
  fi
  if ! python3 -O -I -B "$STRUCTURE_CHECK" "$pdf" "$optimized_urls" \
      "$optimized_navigation" >"$BUILD_ROOT/$label.structure-optimized.stdout" \
      2>"$BUILD_ROOT/$label.structure-optimized.stderr"; then
    cat "$BUILD_ROOT/$label.structure-optimized.stdout" \
      "$BUILD_ROOT/$label.structure-optimized.stderr" >&2
    exit 1
  fi
  for structure_stderr in "$BUILD_ROOT/$label.structure.stderr" \
      "$BUILD_ROOT/$label.structure-optimized.stderr"; do
    if [[ -s "$structure_stderr" ]]; then
      cat "$structure_stderr" >&2
      echo "$CHECK_NAME: $label structure validator emitted stderr" >&2
      exit 1
    fi
  done
  if ! cmp -s "$observed_urls" "$optimized_urls" \
      || ! cmp -s "$observed_navigation" "$optimized_navigation"; then
    echo "$CHECK_NAME: $label structure result differs under optimized Python" >&2
    exit 1
  fi
  cat >"$expected_urls" <<'EOF'
../../DEPENDENCY_COLORED_SXPID_CONCENTRATION.md
../../FINITE_ALPHABET_PLUGIN_CONVERGENCE.md
../../FORMAL_TOOL_ADOPTION_AUDIT.md
../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md
../../KNOWN_LIMITATIONS.md
../../MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md
../../METHODS.md
../../METHODS_SUMMARY.md
../../NUMERICAL_ASSURANCE.md
../../PID_DISCOVERY_VERIFICATION_AND_DURABILITY_BLUEPRINT.md
../../PID_MATHEMATICAL_AUDIT_PROTOCOL.md
../../SUPPORT_CHANGE_TOLERANT_AVERAGED_SXPID_CONTINUITY.md
../../SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md
../../audit/formal/EXACT_LOG_PRODUCT_SXPID2_ASSURANCE.md
../../audit/formal/TWO_SOURCE_SXPID_COUNT_ATOM_BRIDGE.md
../../claims/KSG-INTEGER-HARMONIC-001/claim-v4.md
../../claims/KSG-INTEGER-HARMONIC-001/formal-assurance-v4.md
../../claims/KSG-INTEGER-HARMONIC-001/integration-disposition-v4.md
../../claims/KSG-INTEGER-HARMONIC-001/revision-index.md
../../claims/SX-CERTIFIED-AVERAGED-PID2-001/decision-v3.md
../../claims/SX-CERTIFIED-AVERAGED-PID3-001/decision.md
../../claims/SX-CERTIFIED-AVERAGED-PID3-001/revision-index.md
../../claims/SX-COUNT-ATOM-BRIDGE-001/decision-v2.md
../../method-catalog.json
../../output/pdf/dependency-colored-sxpid-concentration.pdf
../../output/pdf/exact-log-product-sxpid2-assurance.pdf
../../output/pdf/finite-alphabet-plugin-convergence.pdf
../../output/pdf/foundational-shared-exclusions-pid-audit.pdf
../../output/pdf/mathematical-problem-solving-workflow.pdf
../../output/pdf/support-change-tolerant-averaged-sxpid-continuity.pdf
../../output/pdf/sxpid3-source-marginal-and-bounded-audit.pdf
../../output/pdf/two-source-sxpid-count-atom-bridge.pdf
https://arxiv.org/abs/1004.2515
https://dlmf.nist.gov/5.4.E14
https://doi.org/10.1002/rsa.20008
https://doi.org/10.1007/BF00531932
https://doi.org/10.1080/01621459.1963.10500830
https://doi.org/10.1098/rspa.2021.0110
https://doi.org/10.1103/PhysRevE.103.032149
https://doi.org/10.1103/PhysRevE.110.014115
https://doi.org/10.1103/PhysRevE.69.066138
https://doi.org/10.3390/e16042161
https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf
EOF
  if ! cmp -s "$expected_urls" "$observed_urls"; then
    echo "$CHECK_NAME: $label hyperlink target set changed" >&2
    diff -u "$expected_urls" "$observed_urls" >&2 || true
    exit 1
  fi
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

if ! cmp -s "$BUILD_ROOT/built.observed-urls" "$BUILD_ROOT/committed.observed-urls"; then
  echo "$CHECK_NAME: hyperlink target set differs between built and committed projections" >&2
  diff -u "$BUILD_ROOT/built.observed-urls" "$BUILD_ROOT/committed.observed-urls" >&2 || true
  exit 1
fi
if ! cmp -s "$BUILD_ROOT/built.observed-navigation" \
    "$BUILD_ROOT/committed.observed-navigation"; then
  echo "$CHECK_NAME: navigation structure differs between built and committed projections" >&2
  diff -u "$BUILD_ROOT/built.observed-navigation" \
    "$BUILD_ROOT/committed.observed-navigation" >&2 || true
  exit 1
fi
if [[ "$(wc -l <"$BUILD_ROOT/committed.observed-urls" | tr -d ' ')" != "43" ]]; then
  echo "$CHECK_NAME: hyperlink target count changed" >&2
  exit 1
fi
if [[ "$(wc -l <"$BUILD_ROOT/committed.observed-navigation" | tr -d ' ')" != "167" ]]; then
  echo "$CHECK_NAME: navigation-record count changed" >&2
  exit 1
fi
while IFS= read -r target; do
  case "$target" in
    ../../*)
      local_target="${target#../../}"
      if [[ ! -f "$ROOT/$local_target" || -L "$ROOT/$local_target" ]]; then
        echo "$CHECK_NAME: local hyperlink target is absent or symbolic: $local_target" >&2
        exit 1
      fi
      ;;
    http://*|https://*) ;;
    *)
      echo "$CHECK_NAME: unexpected hyperlink domain: $target" >&2
      exit 1
      ;;
  esac
done <"$BUILD_ROOT/committed.observed-urls"

RENDER_PREFIX="$BUILD_ROOT/render/page"
mkdir -p "$(dirname "$RENDER_PREFIX")"
PAGES="$(awk '/^Pages:/ {print $2}' "$BUILD_ROOT/committed.info")"
pdftoppm -f 1 -l "$PAGES" -r 72 -png "$COMMITTED" "$RENDER_PREFIX" \
  >"$BUILD_ROOT/render.stdout" 2>"$BUILD_ROOT/render.stderr" || {
  cat "$BUILD_ROOT/render.stdout" "$BUILD_ROOT/render.stderr" >&2
  echo "$CHECK_NAME: Poppler could not render all pages" >&2
  exit 1
}
if [[ -s "$BUILD_ROOT/render.stderr" ]]; then
  cat "$BUILD_ROOT/render.stderr" >&2
  echo "$CHECK_NAME: Poppler rendering emitted stderr" >&2
  exit 1
fi
RENDERED="$(find "$BUILD_ROOT/render" -type f -name 'page-*.png' | wc -l | tr -d ' ')"
if [[ "$RENDERED" != "$PAGES" ]]; then
  echo "$CHECK_NAME: rendered page count $RENDERED does not equal PDF page count $PAGES" >&2
  exit 1
fi

echo "OK: $CHECK_NAME passed ($(shasum -a 256 "$BUILT" | awk '{print $1}'))"
