#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/ecosystem-compatibility-audit.tex"
COMMITTED="output/pdf/ecosystem-compatibility-audit.pdf"
SOURCE_DATE_EPOCH_VALUE="1784937600"
MODE="${1:---exact}"
CHECK_NAME="ecosystem compatibility audit PDF check"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp pdffonts pdfinfo pdftotext chktex lacheck)
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "$CHECK_NAME: missing command: $command" >&2
    exit 2
  fi
done

if [[ ! -f "$ROOT/$SOURCE" ]]; then
  echo "$CHECK_NAME: missing LaTeX source: $SOURCE" >&2
  exit 1
fi
if [[ ! -f "$ROOT/$COMMITTED" ]]; then
  echo "$CHECK_NAME: missing committed PDF: $COMMITTED" >&2
  exit 1
fi

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-ecosystem-compatibility-audit-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"

# The installed ChkTeX configuration emits one known regex-compilation warning.
# Reject every source diagnostic and every other tool/configuration diagnostic.
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
  | grep -v -E '^[[:space:]]*$' \
    >"$BUILD_DIR/chktex.unexpected" || true
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

LOG="$BUILD_DIR/ecosystem-compatibility-audit.log"
BUILT="$BUILD_DIR/ecosystem-compatibility-audit.pdf"
REJECTED_DIAGNOSTICS='(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error'

if grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >/dev/null; then
  grep -E "$REJECTED_DIAGNOSTICS" "$LOG" >&2
  echo "$CHECK_NAME: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
for sentinel in \
  'Mandatory seven-lens assessment' \
  'No-transplant rule' \
  'Permanent negative corpus' \
  'Required adapter record'; do
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

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: ecosystem compatibility audit PDF is warning-free and same-toolchain reproducible ($DIGEST)"
else
  echo "OK: ecosystem compatibility audit PDF is warning-free and cross-toolchain structurally equivalent ($DIGEST)"
fi
