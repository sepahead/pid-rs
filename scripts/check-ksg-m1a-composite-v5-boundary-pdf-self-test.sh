#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
GATE="scripts/check-ksg-m1a-composite-v5-boundary-pdf.sh"
SVG="audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.svg"
PDF="output/pdf/ksg-m1a-composite-v5-boundary.pdf"
VISUAL="audit/evidence/ksg-rev4-m1a-composite-v5-boundary-visual-receipt-2026-08-18.md"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in cp mkdir mktemp python3 rg shasum wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite-v5 boundary PDF self-test: missing command: $command" >&2
    exit 2
  }
done

cd "$ROOT"
bash -n "$GATE"
"$GATE" --cross-toolchain >/dev/null
if [[ "$MODE" == "--exact" ]]; then
  "$GATE" --exact >/dev/null
fi

source_text="$(<"$GATE")"
required_source_literals=(
  'data-r4-status'
  'contains external resource attribute'
  'uses publication text below 25 SVG pixels'
  'figure Form placement is clipped, off-page, or unexpectedly scaled'
  'catalog OpenAction is not the bounded internal GoTo'
  'an object-structure hostile control was accepted'
  'rendering receipt does not bind the committed 120-dpi color/gray renders'
  'body paragraph inventory or order changed'
  'zero PID theories, zero PID functionals, zero estimators'
)
for literal in "${required_source_literals[@]}"; do
  [[ "$source_text" == *"$literal"* ]] || {
    echo "composite-v5 boundary PDF self-test: gate lost source policy: $literal" >&2
    exit 1
  }
done

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v5-boundary-self-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

copy_fixture() {
  local destination="$1"
  mkdir -p \
    "$destination/scripts" \
    "$destination/audit/evidence" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v5-boundary" \
    "$destination/output/pdf"
  cp "$ROOT/$GATE" "$destination/$GATE"
  cp "$ROOT/scripts/check-formal-pdf-log.sh" "$destination/scripts/check-formal-pdf-log.sh"
  cp "$ROOT/scripts/compare-formal-pdf-renders.py" "$destination/scripts/compare-formal-pdf-renders.py"
  cp "$ROOT/audit/formal/latex/pid-rs-report-tables.sty" "$destination/audit/formal/latex/pid-rs-report-tables.sty"
  cp "$ROOT/audit/formal/latex/ksg-m1a-composite-v5-boundary.tex" "$destination/audit/formal/latex/ksg-m1a-composite-v5-boundary.tex"
  cp "$ROOT/audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md" "$destination/audit/evidence/ksg-rev4-m1a-composite-v5-boundary-2026-08-18.md"
  cp "$ROOT/$SVG" "$destination/$SVG"
  cp "$ROOT/audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v5-boundary/c4-failure-c5-r5.pdf"
  cp "$ROOT/$PDF" "$destination/$PDF"
  cp "$ROOT/output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv" \
    "$destination/output/pdf/ksg-m1a-composite-v5-boundary.rendering-receipt.tsv"
  cp "$ROOT/$VISUAL" "$destination/$VISUAL"
  chmod 755 "$destination/$GATE" "$destination/scripts/check-formal-pdf-log.sh"
}

expect_failure() {
  local fixture="$1" expected="$2" label="$3"
  if (cd "$fixture" && "$GATE" "$MODE") >"$TEST_ROOT/$label.stdout" 2>"$TEST_ROOT/$label.stderr"; then
    echo "composite-v5 boundary PDF self-test: hostile was accepted: $label" >&2
    exit 1
  fi
  if ! rg -F -- "$expected" "$TEST_ROOT/$label.stderr" >/dev/null; then
    cat "$TEST_ROOT/$label.stdout" "$TEST_ROOT/$label.stderr" >&2
    echo "composite-v5 boundary PDF self-test: hostile was noncausal: $label" >&2
    exit 1
  fi
}

# Change the exact bound SVG hash along with an unsafe resource insertion, so
# rejection must reach the XML/resource predicate rather than the outer digest.
svg_fixture="$TEST_ROOT/svg"
copy_fixture "$svg_fixture"
python3 -I -S - "$svg_fixture/$SVG" "$svg_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

svg = Path(sys.argv[1])
gate = Path(sys.argv[2])
raw = svg.read_text(encoding="utf-8").replace(
    "<defs>", '<a href="https://example.invalid/unsafe"><text>unsafe</text></a><defs>', 1
)
svg.write_text(raw, encoding="utf-8", newline="\n")
data = svg.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(r'EXPECTED_SVG_SHA256="[0-9a-f]{64}"', f'EXPECTED_SVG_SHA256="{hashlib.sha256(data).hexdigest()}"', source, count=1)
source = re.sub(r"EXPECTED_SVG_BYTES=[0-9]+", f"EXPECTED_SVG_BYTES={len(data)}", source, count=1)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$svg_fixture" "SVG contains external resource attribute" unsafe-svg-resource

# A live relative URI is structurally rejected before raw-byte or receipt checks.
pdf_fixture="$TEST_ROOT/pdf"
copy_fixture "$pdf_fixture"
python3 -I -B - "$pdf_fixture/$PDF" <<'PY'
from pathlib import Path
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, RectangleObject, TextStringObject

path = Path(sys.argv[1])
writer = PdfWriter(clone_from=path)
writer.pages[0][NameObject("/Annots")] = ArrayObject([DictionaryObject({
    NameObject("/Type"): NameObject("/Annot"),
    NameObject("/Subtype"): NameObject("/Link"),
    NameObject("/Rect"): RectangleObject((10, 10, 20, 20)),
    NameObject("/A"): DictionaryObject({
        NameObject("/S"): NameObject("/URI"),
        NameObject("/URI"): TextStringObject("relative.json"),
    }),
})])
writer.write(path)
writer.close()
PY
expect_failure "$pdf_fixture" "page 1 contains annotations" unsafe-pdf-annotation

# Receipt prose is a closed ordered inventory, not a bag of positive phrases.
receipt_fixture="$TEST_ROOT/receipt"
copy_fixture "$receipt_fixture"
python3 -I -S - "$receipt_fixture/$VISUAL" <<'PY'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
path.write_text(text + "\nContradictory extra review claim.\n", encoding="utf-8", newline="\n")
PY
expect_failure "$receipt_fixture" "visual receipt body paragraph inventory or order changed" receipt-body-drift

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite-v5 boundary PDF exact/cross positives and three external hostile fixtures passed"
else
  echo "OK: composite-v5 boundary PDF cross-toolchain positive and three external hostile fixtures passed"
fi
