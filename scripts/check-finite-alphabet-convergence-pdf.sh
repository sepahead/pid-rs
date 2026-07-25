#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/finite-alphabet-plugin-convergence.tex"
COMMITTED="output/pdf/finite-alphabet-plugin-convergence.pdf"
SOURCE_DATE_EPOCH_VALUE="1784678400"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp lacheck pdffonts pdfinfo pdftotext)
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "finite-alphabet PDF check: missing command: $command" >&2
    exit 2
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-finite-alphabet-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
if ! lacheck "$SOURCE" >"$BUILD_DIR/lacheck.stdout" 2>&1; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "finite-alphabet PDF check: static LaTeX lint failed" >&2
  exit 1
fi
if [[ -s "$BUILD_DIR/lacheck.stdout" ]]; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "finite-alphabet PDF check: static LaTeX lint reported diagnostics" >&2
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
  echo "finite-alphabet PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/finite-alphabet-plugin-convergence.log"
BUILT="$BUILD_DIR/finite-alphabet-plugin-convergence.pdf"

if grep -E \
  '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
  "$LOG" >/dev/null; then
  grep -E \
    '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
    "$LOG" >&2
  echo "finite-alphabet PDF check: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

pdftotext "$BUILT" "$BUILD_DIR/built.semantic.txt"
required_text=(
  "Deterministic plug-in implication"
  "A time-uniform i.i.d. envelope"
  "Formal and executable evidence boundary"
)
for sentinel in "${required_text[@]}"; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.semantic.txt" >/dev/null; then
    echo "finite-alphabet PDF check: required text is absent: $sentinel" >&2
    exit 1
  fi
done

for pdf in "$BUILT" "$COMMITTED"; do
  if ! pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "finite-alphabet PDF check: every font must be embedded, subset, and Unicode-mapped" >&2
    exit 1
  fi
done

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$COMMITTED"; then
    echo "finite-alphabet PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
  pdftotext -layout "$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "finite-alphabet PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "finite-alphabet PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: finite-alphabet convergence PDF is lint-clean, semantically complete, font-complete, warning-free, and same-toolchain reproducible ($DIGEST)"
else
  echo "OK: finite-alphabet convergence PDF is lint-clean, semantically complete, font-complete, warning-free, and cross-toolchain structurally equivalent ($DIGEST)"
fi
