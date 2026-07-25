#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/certified-sxpid2-executable-assurance.tex"
COMMITTED="output/pdf/certified-sxpid2-executable-assurance.pdf"
SOURCE_DATE_EPOCH_VALUE="1784851200"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp)
if [[ "$MODE" == "--cross-toolchain" ]]; then
  commands+=(pdffonts pdfinfo pdftotext)
fi
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "certified SxPID2 assurance PDF check: missing command: $command" >&2
    exit 2
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-certified-sxpid2-assurance-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
if ! SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH_VALUE" TZ=UTC \
  TEXINPUTS="$ROOT/audit/formal/latex:${TEXINPUTS:-}" latexmk \
  -pdf \
  -interaction=nonstopmode \
  -halt-on-error \
  -outdir="$BUILD_DIR" \
  "$SOURCE" \
  >"$BUILD_DIR/latexmk.stdout" 2>&1; then
  cat "$BUILD_DIR/latexmk.stdout" >&2
  echo "certified SxPID2 assurance PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/certified-sxpid2-executable-assurance.log"
BUILT="$BUILD_DIR/certified-sxpid2-executable-assurance.pdf"

if grep -E \
  '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
  "$LOG" >/dev/null; then
  grep -E \
    '(^| )(LaTeX|Package [^ ]+) Warning:|Overfull \\hbox|Underfull \\hbox|undefined references|Fatal error' \
    "$LOG" >&2
  echo "certified SxPID2 assurance PDF check: LaTeX log contains a rejected diagnostic" >&2
  exit 1
fi

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$COMMITTED"; then
    echo "certified SxPID2 assurance PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
  pdftotext -layout "$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "certified SxPID2 assurance PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "certified SxPID2 assurance PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
  for pdf in "$BUILT" "$COMMITTED"; do
    if ! pdffonts "$pdf" | awk '
      NR > 2 { seen = 1; if ($(NF - 4) != "yes") bad = 1 }
      END { exit (!seen || bad) }
    '; then
      echo "certified SxPID2 assurance PDF check: PDF has a missing or non-embedded font" >&2
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
  echo "OK: certified SxPID2 assurance PDF is warning-free and same-toolchain reproducible ($DIGEST)"
else
  echo "OK: certified SxPID2 assurance PDF is warning-free and cross-toolchain structurally equivalent ($DIGEST)"
fi
