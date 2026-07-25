#!/usr/bin/env bash
# Method catalog: validation.foundational-shared-exclusions-audit
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/foundational-shared-exclusions-pid-audit.tex"
COMMITTED="output/pdf/foundational-shared-exclusions-pid-audit.pdf"
EXACT_CHECKER="audit/tools/foundational_sxpid/check_lcr_relation_witness.py"
EVIDENCE="audit/evidence/foundational-sxpid-lcr-exact-audit.json"
LEAN_SOURCE="audit/formal/lean-foundational-sxpid/PidDescriptorFactorization.lean"
LEAN_CHECKER="scripts/check-lean-descriptor-factorization.py"
LEAN_EVIDENCE="audit/evidence/foundational-sxpid-descriptor-factorization-lean.json"
MUTATION_CHECKER="scripts/check-lean-descriptor-factorization-self-test.py"
MUTATION_EVIDENCE="audit/evidence/foundational-sxpid-descriptor-factorization-mutations.json"
SOURCE_DATE_EPOCH_VALUE="1784937600"
MODE="${1:---exact}"
CHECK_NAME="foundational shared-exclusions PID audit PDF check"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp pdffonts pdfinfo pdftotext pdftoppm chktex lacheck python3)
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$CHECK_NAME: missing command: $command" >&2
    exit 2
  fi
done

for required in \
  "$SOURCE" \
  "$COMMITTED" \
  "$EXACT_CHECKER" \
  "$EVIDENCE" \
  "$LEAN_SOURCE" \
  "$LEAN_CHECKER" \
  "$LEAN_EVIDENCE" \
  "$MUTATION_CHECKER" \
  "$MUTATION_EVIDENCE"; do
  if [[ ! -f "$ROOT/$required" ]]; then
    echo "$CHECK_NAME: missing artifact: $required" >&2
    exit 1
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-foundational-sxpid-audit-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"

KNOWN_CHKTEX_CONFIG_WARNING='chktex: WARNING -- Compilation of regular expression \[(?![^\]\[{}]*{(?![^\]\[{}]*}))[^\]]*\[ failed with error repetition-operator operand invalid.'
set +e
chktex -q "$SOURCE" >"$BUILD_DIR/chktex.stdout" 2>"$BUILD_DIR/chktex.stderr"
CHKTEX_STATUS=$?
set -e
if grep -E '^Warning [0-9]+ in ' "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >/dev/null; then
  cat "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX reported a source diagnostic" >&2
  exit 1
fi
grep -Fvx -- "$KNOWN_CHKTEX_CONFIG_WARNING" "$BUILD_DIR/chktex.stderr" \
  | grep -v -E '^[[:space:]]*$' >"$BUILD_DIR/chktex.unexpected" || true
if [[ -s "$BUILD_DIR/chktex.stdout" || -s "$BUILD_DIR/chktex.unexpected" ]]; then
  cat "$BUILD_DIR/chktex.stdout" "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX reported an unexpected diagnostic" >&2
  exit 1
fi
if [[ "$CHKTEX_STATUS" -ne 0 ]]; then
  cat "$BUILD_DIR/chktex.stderr" >&2
  echo "$CHECK_NAME: ChkTeX exited unsuccessfully" >&2
  exit 1
fi

lacheck "$SOURCE" >"$BUILD_DIR/lacheck.stdout" 2>"$BUILD_DIR/lacheck.stderr"
if [[ -s "$BUILD_DIR/lacheck.stdout" || -s "$BUILD_DIR/lacheck.stderr" ]]; then
  cat "$BUILD_DIR/lacheck.stdout" "$BUILD_DIR/lacheck.stderr" >&2
  echo "$CHECK_NAME: lacheck reported a source diagnostic" >&2
  exit 1
fi

python3 "$EXACT_CHECKER" --write-evidence "$BUILD_DIR/evidence.json" \
  >"$BUILD_DIR/exact-checker.stdout"
if ! cmp -s "$BUILD_DIR/evidence.json" "$EVIDENCE"; then
  echo "$CHECK_NAME: exact-rational evidence is stale or not reproducible" >&2
  exit 1
fi

python3 "$LEAN_CHECKER" >"$BUILD_DIR/lean-evidence.json"
if ! cmp -s "$BUILD_DIR/lean-evidence.json" "$LEAN_EVIDENCE"; then
  echo "$CHECK_NAME: Lean factorization evidence is stale or not reproducible" >&2
  exit 1
fi

python3 "$MUTATION_CHECKER" >"$BUILD_DIR/mutation-evidence.json"
if ! cmp -s "$BUILD_DIR/mutation-evidence.json" "$MUTATION_EVIDENCE"; then
  echo "$CHECK_NAME: Lean factorization mutation evidence is stale or not reproducible" >&2
  exit 1
fi

if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
  TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR" \
  "$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "$CHECK_NAME: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/foundational-shared-exclusions-pid-audit.log"
BUILT="$BUILD_DIR/foundational-shared-exclusions-pid-audit.pdf"
REJECTED_DIAGNOSTICS='(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error'
if grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >/dev/null; then
  grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >&2
  echo "$CHECK_NAME: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
for sentinel in \
  'No fatal algebraic contradiction was found' \
  'Compatibility firewall' \
  'Descriptor-factorization firewall' \
  'Valid theorem on the stated Definition 6 domain' \
  'What arXiv:2604.03869v2 does and does not imply' \
  'Three independent executable and formal routes' \
  '0.58147874590342'; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.txt" >/dev/null; then
    echo "$CHECK_NAME: rendered-text sentinel is absent: $sentinel" >&2
    exit 1
  fi
done
if grep -F -- '??' "$BUILD_DIR/built.txt" >/dev/null; then
  echo "$CHECK_NAME: rendered text contains an unresolved reference marker" >&2
  exit 1
fi

for pdf in "$BUILT" "$ROOT/$COMMITTED"; do
  if ! pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "$CHECK_NAME: PDF font is not embedded, subset, and Unicode-mapped" >&2
    exit 1
  fi
done

mkdir "$BUILD_DIR/rendered"
pdftoppm -png -r 72 "$BUILT" "$BUILD_DIR/rendered/page" >/dev/null 2>&1
EXPECTED_PAGES="$(pdfinfo "$BUILT" | awk '/^Pages:/ {print $2}')"
RENDERED_PAGES="$(find "$BUILD_DIR/rendered" -type f -name 'page-*.png' | wc -l | tr -d ' ')"
if [[ "$RENDERED_PAGES" != "$EXPECTED_PAGES" ]]; then
  echo "$CHECK_NAME: rendered $RENDERED_PAGES of $EXPECTED_PAGES pages" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$ROOT/$COMMITTED"; then
    echo "$CHECK_NAME: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$ROOT/$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "$CHECK_NAME: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$ROOT/$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "$CHECK_NAME: page geometry changed across toolchains" >&2
    exit 1
  fi
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

echo "OK: foundational SxPID audit PDF, exact witnesses, and Lean firewall are warning-free and reproducible ($DIGEST)"
