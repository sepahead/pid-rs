#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/dependency-colored-sxpid-concentration.tex"
COMMITTED="output/pdf/dependency-colored-sxpid-concentration.pdf"
SOURCE_DATE_EPOCH_VALUE="1784678400"

for command in latexmk cmp; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "dependency-colored SxPID PDF check: missing command: $command" >&2
    exit 2
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-dependency-colored-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR" \
  "$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "dependency-colored SxPID PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/dependency-colored-sxpid-concentration.log"
BUILT="$BUILD_DIR/dependency-colored-sxpid-concentration.pdf"

if grep -E \
  '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
  "$LOG" >/dev/null; then
  grep -E \
    '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
    "$LOG" >&2
  echo "dependency-colored SxPID PDF check: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

if ! cmp -s "$BUILT" "$COMMITTED"; then
  echo "dependency-colored SxPID PDF check: committed PDF is stale or not reproducible" >&2
  exit 1
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

echo "OK: dependency-colored SxPID PDF is warning-free and reproducible ($DIGEST)"
