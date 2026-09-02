#!/usr/bin/env bash
# Verify the canonical custody receipt with the reviewed local producer profile.
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
BUILDER="$ROOT/scripts/build-post-publication-custody-pdf.sh"
RECORD_CHECKER="$ROOT/scripts/check-post-publication-custody.py"
COMMITTED="$ROOT/output/pdf/post-publication-custody-2026-09-02.pdf"
VISUAL_RECEIPT="$ROOT/audit/evidence/post-publication-custody-visual-receipt-2026-09-02.md"
VISUAL_RECEIPT_SHA256="f176cf45a9dd703e490328fdbe8f992e592ec6ddff0fbcef2073aa162bd2fbd4"
VISUAL_RECEIPT_PDF_SHA256="d122cec2e2f77cf613a00d28601161cc75a28a93f777700e7919afb4f5fb8550"
MODE="${1:---exact}"
CHECK_NAME="post-publication custody PDF check"

if [[ "$#" -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi
if [[ "$MODE" == "--cross-toolchain" ]]; then
  echo "$CHECK_NAME: no reviewed cross-toolchain producer profile exists; no cross-toolchain acceptance is issued" >&2
  exit 2
fi

for tool in awk bash cmp grep mktemp pdffonts pdfinfo python3 rm shasum; do
  command -v "$tool" >/dev/null 2>&1 || {
    echo "$CHECK_NAME: missing command: $tool" >&2
    exit 2
  }
done
for path in "$BUILDER" "$RECORD_CHECKER" "$COMMITTED" "$VISUAL_RECEIPT"; do
  if [[ ! -f "$path" || -L "$path" ]]; then
    echo "$CHECK_NAME: required input is absent, non-regular, or symbolic: $path" >&2
    exit 1
  fi
done

require_sha256() {
  local path="$1" expected="$2" label="$3"
  local observed
  observed="$(shasum -a 256 "$path" | awk '{print $1}')"
  if [[ "$observed" != "$expected" ]]; then
    echo "$CHECK_NAME: $label identity drifted: expected $expected, observed $observed" >&2
    exit 1
  fi
}

require_unique_line() {
  local literal="$1" label="$2"
  local count
  count="$(grep -Fxc -- "$literal" "$VISUAL_RECEIPT" || true)"
  if [[ "$count" != "1" ]]; then
    echo "$CHECK_NAME: $label drifted; expected one exact line, observed $count" >&2
    exit 1
  fi
}

require_sha256 "$VISUAL_RECEIPT" "$VISUAL_RECEIPT_SHA256" \
  "visual-review receipt"
require_sha256 "$COMMITTED" "$VISUAL_RECEIPT_PDF_SHA256" \
  "visual-review receipt subject PDF"
require_unique_line \
  "schema: \`pid-rs/post-publication-custody-visual-review/v1\`" \
  "visual-review receipt schema"
require_unique_line \
  "subject: \`output/pdf/post-publication-custody-2026-09-02.pdf\`" \
  "visual-review receipt subject"
require_unique_line "pdf_sha256: \`$VISUAL_RECEIPT_PDF_SHA256\`" \
  "visual-review receipt PDF binding"
require_unique_line "pages: \`6\`" "visual-review receipt page scope"
require_unique_line "color_144_dpi_pages_reviewed: \`1-6\`" \
  "visual-review receipt color scope"
require_unique_line "grayscale_120_dpi_pages_reviewed: \`1-6\`" \
  "visual-review receipt grayscale scope"
require_unique_line "lens_count: \`20\`" "visual-review receipt lens count"
require_unique_line "status: \`passed\`" "visual-review receipt disposition"

python3 -I -S -B "$RECORD_CHECKER"
python3 -O -I -S -B "$RECORD_CHECKER"

TMP_BASE_INPUT="${TMPDIR:-/tmp}"
TMP_BASE="$(CDPATH='' cd -- "$TMP_BASE_INPUT" && pwd -P)"
if [[ "$TMP_BASE" == "/" ]]; then
  echo "$CHECK_NAME: refusing filesystem root as temporary root" >&2
  exit 2
fi
BUILD_ROOT="$(mktemp -d "$TMP_BASE/pid-rs-custody-pdf-check.XXXXXX")"
cleanup() {
  local status="$1"
  trap - EXIT HUP INT TERM
  case "$BUILD_ROOT" in
    "$TMP_BASE"/pid-rs-custody-pdf-check.*) rm -rf -- "$BUILD_ROOT" ;;
    *)
      echo "$CHECK_NAME: refusing unexpected cleanup path: $BUILD_ROOT" >&2
      status=1
      ;;
  esac
  exit "$status"
}
trap 'cleanup "$?"' EXIT
trap 'cleanup 129' HUP
trap 'cleanup 130' INT
trap 'cleanup 143' TERM

FIRST="$BUILD_ROOT/first.pdf"
SECOND="$BUILD_ROOT/second.pdf"
TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$FIRST" >"$BUILD_ROOT/first.stdout" 2>"$BUILD_ROOT/first.stderr"
TMPDIR="$BUILD_ROOT" bash --noprofile --norc "$BUILDER" "$SECOND" >"$BUILD_ROOT/second.stdout" 2>"$BUILD_ROOT/second.stderr"
if [[ -s "$BUILD_ROOT/first.stderr" || -s "$BUILD_ROOT/second.stderr" ]]; then
  cat "$BUILD_ROOT/first.stderr" "$BUILD_ROOT/second.stderr" >&2
  echo "$CHECK_NAME: builder emitted stderr" >&2
  exit 1
fi
cmp -s "$FIRST" "$SECOND" || {
  echo "$CHECK_NAME: two isolated same-toolchain builds differ" >&2
  exit 1
}
cmp -s "$FIRST" "$COMMITTED" || {
  echo "$CHECK_NAME: committed PDF differs from the reproducible build" >&2
  exit 1
}

LC_ALL=C pdfinfo "$COMMITTED" >"$BUILD_ROOT/pdfinfo"
LC_ALL=C pdffonts "$COMMITTED" >"$BUILD_ROOT/pdffonts"
if ! grep -Eq '^Page size:[[:space:]]+595\.[0-9]+ x 841\.[0-9]+ pts \(A4\)$' "$BUILD_ROOT/pdfinfo"; then
  echo "$CHECK_NAME: committed PDF is not A4" >&2
  exit 1
fi
if ! grep -Eq '^PDF version:[[:space:]]+1\.7$' "$BUILD_ROOT/pdfinfo"; then
  echo "$CHECK_NAME: committed PDF is not PDF 1.7" >&2
  exit 1
fi
for metadata in \
    '^Tagged:[[:space:]]+no$' \
    '^Form:[[:space:]]+none$' \
    '^JavaScript:[[:space:]]+no$' \
    '^Encrypted:[[:space:]]+no$'; do
  if ! grep -Eq "$metadata" "$BUILD_ROOT/pdfinfo"; then
    echo "$CHECK_NAME: committed PDF metadata omitted: $metadata" >&2
    exit 1
  fi
done
if ! awk '
  NR <= 2 { next }
  NF == 0 { next }
  { seen = 1; if ($(NF - 4) != "yes" || $(NF - 2) != "yes") bad = 1 }
  END { exit (!seen || bad) }
' "$BUILD_ROOT/pdffonts"; then
  echo "$CHECK_NAME: committed PDF has a nonembedded or non-Unicode-mapped font" >&2
  exit 1
fi

pages="$(awk '/^Pages:/ {print $2}' "$BUILD_ROOT/pdfinfo")"
echo "OK: custody receipt is a reproducible $pages-page A4 PDF 1.7 artifact with embedded fonts and bounded HTTPS actions"
