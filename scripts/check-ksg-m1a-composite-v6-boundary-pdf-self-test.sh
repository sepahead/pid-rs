#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
GATE="scripts/check-ksg-m1a-composite-v6-boundary-pdf.sh"
SVG="audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.svg"
PDF="output/pdf/ksg-m1a-composite-v6-boundary.pdf"
VISUAL="audit/evidence/ksg-rev4-m1a-composite-v6-boundary-visual-receipt-2026-08-18.md"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in bash cat chmod cp dirname mkdir mktemp python3 rg rm shasum wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite-v6 boundary PDF self-test: missing command: $command" >&2
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
  'data-r5-status'
  'contains external resource attribute'
  'contains a CSS import or font-face resource'
  'contains an unbounded transform attribute'
  'contains unbounded attribute'
  'contains unbounded CSS property'
  'local/hosted attempt-domain separation changed'
  'C5 local/hosted attempt-domain separation changed'
  'local privacy boundary changed'
  'local hermeticity boundary changed'
  'SVG lost the bounded local hermeticity nonclaim'
  'repository-ignored products and uninspected Git metadata remain outside the observation'
  'TeX fixed local command lost its texttt binding'
  'distinct stable mode-0600 file descriptors 3 and 4'
  'accepts no successor-capture/evidentiary stdin route'
  'EXPECTED_VISUAL_RECEIPT_SHA256'
  'uses publication text below 25 SVG pixels'
  'TeX-path association hostile was accepted'
  'associated_figure = PdfReader(figures[1], strict=True)'
  'contains a raster image XObject'
  'contains an inline raster image'
  'Pattern-reachable-raster'
  'Type3-reachable-raster'
  '/ExtGState resources differ'
  'wrong-lane association hostile control was accepted'
  'visible raster-overlay hostile control was accepted'
  'figure fonts are absent'
  'fresh/committed report font-family inventories differ'
  'figure Form placement is clipped, off-page, or unexpectedly scaled'
  'is not the bounded internal GoTo'
  'destination name tree is cyclic'
  'outline-action hostile control was accepted'
  'an object-structure hostile control was accepted'
  'font resource {resource_name} Unicode map differs'
  'same-family font-program hostile control was accepted'
  'soft-mask-reachable-raster'
  'unsupported XObject subtype'
  'unsupported PatternType'
  'rendering receipt does not bind the committed 120-dpi color/gray renders'
  'body paragraph inventory or order changed'
  'zero PID theories, zero PID functionals, zero estimators'
)
for literal in "${required_source_literals[@]}"; do
  [[ "$source_text" == *"$literal"* ]] || {
    echo "composite-v6 boundary PDF self-test: gate lost source policy: $literal" >&2
    exit 1
  }
done

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v6-boundary-self-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

copy_fixture() {
  local destination="$1"
  mkdir -p \
    "$destination/scripts" \
    "$destination/audit/evidence" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v6-boundary" \
    "$destination/output/pdf"
  cp "$ROOT/$GATE" "$destination/$GATE"
  cp "$ROOT/scripts/check-formal-pdf-log.sh" "$destination/scripts/check-formal-pdf-log.sh"
  cp "$ROOT/scripts/compare-formal-pdf-renders.py" "$destination/scripts/compare-formal-pdf-renders.py"
  cp "$ROOT/audit/formal/latex/pid-rs-report-tables.sty" "$destination/audit/formal/latex/pid-rs-report-tables.sty"
  cp "$ROOT/audit/formal/latex/ksg-m1a-composite-v6-boundary.tex" "$destination/audit/formal/latex/ksg-m1a-composite-v6-boundary.tex"
  cp "$ROOT/audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md" "$destination/audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md"
  cp "$ROOT/$SVG" "$destination/$SVG"
  cp "$ROOT/audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf"
  cp "$ROOT/$PDF" "$destination/$PDF"
  cp "$ROOT/output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv" \
    "$destination/output/pdf/ksg-m1a-composite-v6-boundary.rendering-receipt.tsv"
  cp "$ROOT/$VISUAL" "$destination/$VISUAL"
  chmod 755 "$destination/$GATE" "$destination/scripts/check-formal-pdf-log.sh"
}

expect_failure() {
  local fixture="$1" expected="$2" label="$3"
  if (cd "$fixture" && "$GATE" "$MODE") >"$TEST_ROOT/$label.stdout" 2>"$TEST_ROOT/$label.stderr"; then
    echo "composite-v6 boundary PDF self-test: hostile was accepted: $label" >&2
    exit 1
  fi
  if ! rg -F -- "$expected" "$TEST_ROOT/$label.stderr" >/dev/null; then
    cat "$TEST_ROOT/$label.stdout" "$TEST_ROOT/$label.stderr" >&2
    echo "composite-v6 boundary PDF self-test: hostile was noncausal: $label" >&2
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

# Rebind a source-level attempt-domain conflation so the gate must reject it
# independently of the outer Markdown digest.
attempt_fixture="$TEST_ROOT/attempt-domain"
copy_fixture "$attempt_fixture"
python3 -I -S - \
  "$attempt_fixture/audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md" \
  "$attempt_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "one fresh exact-C6 local closure observation and fresh",
    "fresh attempt-1 local, CI, CodeQL, and dedicated-v6 success;",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_MD_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_MD_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(r"EXPECTED_MD_BYTES=[0-9]+", f"EXPECTED_MD_BYTES={len(data)}", source, count=1)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$attempt_fixture" \
  "local/hosted attempt-domain separation changed" attempt-domain-conflation

# Rebind the predecessor-local attempt-domain conflation separately: L5 is a
# fresh exact-C5 local observation, not an attempt-1 authority.
q5_attempt_fixture="$TEST_ROOT/q5-attempt-domain"
copy_fixture "$q5_attempt_fixture"
python3 -I -S - \
  "$q5_attempt_fixture/audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md" \
  "$q5_attempt_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "where $L_5$ is one fresh local qualification observation for exact C5",
    "where every term is terminal attempt-1 success for the same exact C5 commit",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_MD_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_MD_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(r"EXPECTED_MD_BYTES=[0-9]+", f"EXPECTED_MD_BYTES={len(data)}", source, count=1)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$q5_attempt_fixture" \
  "C5 local/hosted attempt-domain separation changed" q5-attempt-domain-conflation

# Rebind an absolute privacy claim in the SVG description. The bounded scanner
# may reject named patterns; it cannot prove that no private path is published.
privacy_fixture="$TEST_ROOT/privacy"
copy_fixture "$privacy_fixture"
python3 -I -S - "$privacy_fixture/$SVG" "$privacy_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "It does not pass ambient variables to the command",
    "It publishes no ambient secret or private absolute path",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_SVG_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_SVG_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_SVG_BYTES=[0-9]+", f"EXPECTED_SVG_BYTES={len(data)}", source, count=1
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$privacy_fixture" "local privacy boundary changed" privacy-overclaim

# Rebind a positive hermeticity claim while retaining all outer source custody.
# Ordinary Git-clean excludes ignored products and cannot support that claim.
hermeticity_fixture="$TEST_ROOT/hermeticity"
copy_fixture "$hermeticity_fixture"
python3 -I -S - \
  "$hermeticity_fixture/audit/evidence/ksg-rev4-m1a-composite-v6-boundary-2026-08-18.md" \
  "$hermeticity_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "so this is not\na hermetic closure.",
    "so this proves hermetic closure.",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_MD_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_MD_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(r"EXPECTED_MD_BYTES=[0-9]+", f"EXPECTED_MD_BYTES={len(data)}", source, count=1)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$hermeticity_fixture" \
  "lost the exact local hermeticity nonclaim" hermeticity-overclaim

# Rebind an accessible-description hermeticity overclaim so the SVG-specific
# residual-side-input predicate, rather than its outer digest, must reject it.
svg_hermeticity_fixture="$TEST_ROOT/svg-hermeticity"
copy_fixture "$svg_hermeticity_fixture"
python3 -I -S - "$svg_hermeticity_fixture/$SVG" "$svg_hermeticity_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "repository-ignored products and uninspected Git metadata remain outside the observation and may remain side inputs, so this is not a hermetic closure.",
    "ordinary Git-clean proves hermetic closure.",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_SVG_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_SVG_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_SVG_BYTES=[0-9]+", f"EXPECTED_SVG_BYTES={len(data)}", source, count=1
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$svg_hermeticity_fixture" \
  "SVG lost the bounded local hermeticity nonclaim" svg-hermeticity-overclaim

# Rebind the historical tab-for-backslash typo so the command presentation
# predicate, rather than the TeX digest, must reject it.
texttt_fixture="$TEST_ROOT/texttt"
copy_fixture "$texttt_fixture"
python3 -I -S - \
  "$texttt_fixture/audit/formal/latex/ksg-m1a-composite-v6-boundary.tex" \
  "$texttt_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    r"\texttt{just ksg-composite-v6}",
    "\texttt{just ksg-composite-v6}",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_TEX_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_TEX_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_TEX_BYTES=[0-9]+", f"EXPECTED_TEX_BYTES={len(data)}", source, count=1
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$texttt_fixture" \
  "TeX fixed local command lost its texttt binding" texttt-command-binding

# Rebind a wrong includegraphics source so rejection must reach the unique,
# exact TeX-to-committed-figure association predicate.
tex_fixture="$TEST_ROOT/tex"
copy_fixture "$tex_fixture"
python3 -I -S - \
  "$tex_fixture/audit/formal/latex/ksg-m1a-composite-v6-boundary.tex" \
  "$tex_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "figures/ksg-m1a-composite-v6-boundary/c5-failure-c6-r6.pdf",
    "figures/unreferenced-lane.pdf",
    1,
)
path.write_text(text, encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_TEX_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_TEX_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_TEX_BYTES=[0-9]+", f"EXPECTED_TEX_BYTES={len(data)}", source, count=1
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$tex_fixture" \
  "TeX figure association is not the exact committed figure path" tex-figure-association

# Rebind the mutated report's outer digest so adding an annotation must reach
# the closed page-key inventory before any dependent receipt check.
pdf_fixture="$TEST_ROOT/pdf"
copy_fixture "$pdf_fixture"
python3 -I -B - "$pdf_fixture/$PDF" "$pdf_fixture/$GATE" <<'PY'
import hashlib
from pathlib import Path
import re
import sys
from pypdf import PdfWriter
from pypdf.generic import ArrayObject, DictionaryObject, NameObject, RectangleObject, TextStringObject

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
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
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_PDF_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_PDF_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(r"EXPECTED_PDF_BYTES=[0-9]+", f"EXPECTED_PDF_BYTES={len(data)}", source, count=1)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$pdf_fixture" "page 1 key inventory changed" unsafe-pdf-annotation

# Receipt prose is a closed ordered inventory, not a bag of positive phrases.
receipt_fixture="$TEST_ROOT/receipt"
copy_fixture "$receipt_fixture"
python3 -I -S - "$receipt_fixture/$VISUAL" "$receipt_fixture/$GATE" <<'PY'
import hashlib
from pathlib import Path
import re
import sys
path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8")
path.write_text(text + "\nContradictory extra review claim.\n", encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_VISUAL_RECEIPT_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_VISUAL_RECEIPT_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_VISUAL_RECEIPT_BYTES=[0-9]+",
    f"EXPECTED_VISUAL_RECEIPT_BYTES={len(data)}",
    source,
    count=1,
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$receipt_fixture" "visual receipt body paragraph inventory or order changed" receipt-body-drift

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite-v6 boundary PDF exact/cross positives and ten external hostile fixtures passed"
else
  echo "OK: composite-v6 boundary PDF cross-toolchain positive and ten external hostile fixtures passed"
fi
