#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/mathematical-problem-solving-workflow.tex"
COMMITTED="output/pdf/mathematical-problem-solving-workflow.pdf"
SOURCE_DATE_EPOCH_VALUE="1784851200"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp pdftotext python3)
if [[ "$MODE" == "--cross-toolchain" ]]; then
  commands+=(pdffonts pdfinfo)
fi
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "mathematical workflow PDF check: missing command: $command" >&2
    exit 2
  fi
done

python3 "$ROOT/scripts/check-citation-edge-countermodel.py"
python3 "$ROOT/scripts/check-citation-edge-countermodel-self-test.py"

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-mathematical-workflow-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

# The markdown LaTeX package externalizes fenced-code bodies beside the current working directory.
# Build inside the disposable directory so these deterministic intermediates never pollute the
# repository root.
cd "$BUILD_DIR"

sed -n '/^\\begin{markdown}$/,/^\\end{markdown}$/p' "$ROOT/$SOURCE" |
  sed '1d;$d' >"$BUILD_DIR/embedded-canonical.md"
if ! cmp -s "$BUILD_DIR/embedded-canonical.md" "$ROOT/MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md"; then
  echo "mathematical workflow PDF check: embedded canonical Markdown differs from root source" >&2
  exit 1
fi

protocol_sentinels=(
  'Citation-edge type check'
  'Named source arrow (domain -> codomain):'
  'Equation (27) is therefore false'
  '0 -> 0 -> Z/2 --id--> Z/2 -> 0'
  '0 -> 0 -> C2 --id--> C2 -> 0'
  'PidCitationEdgeCountermodel.lean'
  'materially distinct valid proof or solution'
  'passes by the same model against the same prompt'
)
for sentinel in "${protocol_sentinels[@]}"; do
  if ! grep -F -- "$sentinel" "$ROOT/MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md" >/dev/null; then
    echo "mathematical workflow PDF check: canonical protocol sentinel is absent: $sentinel" >&2
    exit 1
  fi
done

if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
  TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" latexmk \
  -pdf \
  -shell-escape \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR" \
  "$ROOT/$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "mathematical workflow PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/mathematical-problem-solving-workflow.log"
BUILT="$BUILD_DIR/mathematical-problem-solving-workflow.pdf"

if grep -E \
  '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
  "$LOG" >/dev/null; then
  grep -E \
    '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
    "$LOG" >&2
  echo "mathematical workflow PDF check: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
for sentinel in 'attempt -> failure' '<CLAIM-ID>' "${protocol_sentinels[@]}"; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.txt" >/dev/null; then
    echo "mathematical workflow PDF check: rendered-text sentinel is absent: $sentinel" >&2
    exit 1
  fi
done
if grep -E '[¿¡]' "$BUILD_DIR/built.txt" >/dev/null; then
  echo "mathematical workflow PDF check: rendered code contains inverted angle-bracket glyphs" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$ROOT/$COMMITTED"; then
    echo "mathematical workflow PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$ROOT/$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "mathematical workflow PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$ROOT/$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "mathematical workflow PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
  for pdf in "$BUILT" "$ROOT/$COMMITTED"; do
    if ! pdffonts "$pdf" | awk '
      NR > 2 { seen = 1; if ($(NF - 4) != "yes") bad = 1 }
      END { exit (!seen || bad) }
    '; then
      echo "mathematical workflow PDF check: PDF has a missing or non-embedded font" >&2
      exit 1
    fi
  done
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: mathematical workflow PDF is warning-free and same-toolchain reproducible ($DIGEST)"
else
  echo "OK: mathematical workflow PDF is warning-free and cross-toolchain structurally equivalent ($DIGEST)"
fi
