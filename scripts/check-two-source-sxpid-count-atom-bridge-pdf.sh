#!/usr/bin/env bash
set -euo pipefail

# Method catalog: validation.two-source-sxpid-count-atom-bridge

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="audit/formal/latex/two-source-sxpid-count-atom-bridge.tex"
COMMITTED="output/pdf/two-source-sxpid-count-atom-bridge.pdf"
LEAN_SOURCE="audit/formal/lean/PidFiniteConvergence/TwoSourceMobiusAtomBridge.lean"
SOURCE_DATE_EPOCH_VALUE="1786320000"
MODE="${1:---exact}"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

commands=(latexmk cmp lacheck pdffonts pdfinfo pdftotext)
for command in "${commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "two-source SxPID count-to-atom PDF check: missing command: $command" >&2
    exit 2
  fi
done

TMP_ROOT="${TMPDIR:-/tmp}"
BUILD_DIR="$(mktemp -d "$TMP_ROOT/pid-rs-two-source-sxpid-count-atom-pdf.XXXXXX")"
trap 'rm -rf -- "$BUILD_DIR"' EXIT

cd "$ROOT"
if ! grep -F -- '\texttt{sx\_pid2\_mobius\_coordinate\_swap\_equivariant}' "$SOURCE" >/dev/null; then
  echo "two-source SxPID count-to-atom PDF check: current coordinate-swap theorem is absent from the source crosswalk" >&2
  exit 1
fi
if grep -F -- 'sx\_pid2\_mobius\_source\_swap\_equivariant' "$SOURCE" >/dev/null; then
  echo "two-source SxPID count-to-atom PDF check: obsolete source-swap theorem remains in the source crosswalk" >&2
  exit 1
fi
if ! grep -F -- 'theorem sx_pid2_mobius_coordinate_swap_equivariant' "$LEAN_SOURCE" >/dev/null; then
  echo "two-source SxPID count-to-atom PDF check: bound Lean coordinate-swap declaration is absent" >&2
  exit 1
fi
if ! lacheck "$SOURCE" >"$BUILD_DIR/lacheck.stdout" 2>&1; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "two-source SxPID count-to-atom PDF check: static LaTeX lint failed" >&2
  exit 1
fi
if [[ -s "$BUILD_DIR/lacheck.stdout" ]]; then
  cat "$BUILD_DIR/lacheck.stdout" >&2
  echo "two-source SxPID count-to-atom PDF check: static LaTeX lint reported diagnostics" >&2
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
  echo "two-source SxPID count-to-atom PDF check: LaTeX build failed" >&2
  exit 1
fi

LOG="$BUILD_DIR/two-source-sxpid-count-atom-bridge.log"
BUILT="$BUILD_DIR/two-source-sxpid-count-atom-bridge.pdf"

if ! scripts/check-formal-pdf-log.sh "$LOG"; then
  echo "two-source SxPID count-to-atom PDF check: strict shared LaTeX log policy failed" >&2
  exit 1
fi

pdftotext "$BUILT" "$BUILD_DIR/built.semantic.txt"
required_text=(
  "Exact rational products"
  "The exact 24-coordinate surface"
  "sx_pid2_mobius_coordinate_swap_equivariant"
  "Component-nonnegativity is not proved"
  "no typed source-data"
  "transport is claimed"
  "Rust, binary64, parsing, standalone-certifier, Python, and"
  "resource semantics remain outside the theorem"
  "sampling uncertainty, concentration, consistency, population support, or calibration"
  "three-source or general higher-source lattices"
  "scientific priority, uniqueness, application validity, release readiness, or downstream"
  "Residual boundaries"
)
for sentinel in "${required_text[@]}"; do
  if ! grep -F -- "$sentinel" "$BUILD_DIR/built.semantic.txt" >/dev/null; then
    echo "two-source SxPID count-to-atom PDF check: required text is absent: $sentinel" >&2
    exit 1
  fi
done
if grep -F -- "sx_pid2_mobius_source_swap_equivariant" "$BUILD_DIR/built.semantic.txt" >/dev/null; then
  echo "two-source SxPID count-to-atom PDF check: rendered PDF contains obsolete source-swap theorem" >&2
  exit 1
fi

for pdf in "$BUILT" "$COMMITTED"; do
  if ! pdffonts "$pdf" | awk '
    NR > 2 {
      seen = 1
      if ($(NF - 4) != "yes" || $(NF - 3) != "yes" || $(NF - 2) != "yes") bad = 1
    }
    END { exit (!seen || bad) }
  '; then
    echo "two-source SxPID count-to-atom PDF check: every font must be embedded, subset, and Unicode-mapped" >&2
    exit 1
  fi
done

if [[ "$MODE" == "--exact" ]]; then
  if ! cmp -s "$BUILT" "$COMMITTED"; then
    echo "two-source SxPID count-to-atom PDF check: committed PDF is stale or not reproducible" >&2
    exit 1
  fi
else
  pdftotext -layout "$BUILT" "$BUILD_DIR/built.txt"
  pdftotext -layout "$COMMITTED" "$BUILD_DIR/committed.txt"
  if ! cmp -s "$BUILD_DIR/built.txt" "$BUILD_DIR/committed.txt"; then
    echo "two-source SxPID count-to-atom PDF check: extracted text/layout changed across toolchains" >&2
    exit 1
  fi
  pdfinfo "$BUILT" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/built.info"
  pdfinfo "$COMMITTED" | grep -E '^(Pages|Page size):' >"$BUILD_DIR/committed.info"
  if ! cmp -s "$BUILD_DIR/built.info" "$BUILD_DIR/committed.info"; then
    echo "two-source SxPID count-to-atom PDF check: page geometry changed across toolchains" >&2
    exit 1
  fi
fi

if command -v shasum >/dev/null 2>&1; then
  DIGEST="$(shasum -a 256 "$BUILT" | awk '{print $1}')"
else
  DIGEST="$(sha256sum "$BUILT" | awk '{print $1}')"
fi

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: two-source SxPID count-to-atom PDF is lint-clean, contains the required bounded-scope sections, is font-complete and warning-free, and is same-toolchain reproducible ($DIGEST)"
else
  echo "OK: two-source SxPID count-to-atom PDF is lint-clean, contains the required bounded-scope sections, is font-complete and warning-free, and is cross-toolchain structurally equivalent ($DIGEST)"
fi
