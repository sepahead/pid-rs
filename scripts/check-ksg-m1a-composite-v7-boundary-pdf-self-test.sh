#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
MODE="${1:---exact}"
GATE="scripts/check-ksg-m1a-composite-v7-boundary-pdf.sh"
SVG="audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.svg"
PDF="output/pdf/ksg-m1a-composite-v7-boundary.pdf"
VISUAL="audit/evidence/ksg-rev4-m1a-composite-v7-boundary-visual-receipt-2026-08-18.md"
COUNTEREXAMPLE="audit/evidence/ksg-rev4-m1a-composite-v6-local-closure-counterexample-v7-2026-08-18.json"
COUNTEREXAMPLE_SCHEMA="audit/schemas/ksg-rev4-m1a-composite-local-closure-counterexample-v7.schema.json"

if [[ "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command in bash cat chmod cp dirname mkdir mktemp python3 rg rm shasum wc; do
  command -v "$command" >/dev/null 2>&1 || {
    echo "composite-v7 boundary PDF self-test: missing command: $command" >&2
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
  'data-r6-status'
  'contains external resource attribute'
  'contains a CSS import or font-face resource'
  'contains an unbounded transform attribute'
  'contains unbounded attribute'
  'contains unbounded CSS property'
  'local/hosted attempt-domain separation changed'
  'local hermeticity boundary changed'
  'hosted correlation or PDF-content boundary changed'
  'terminal predecessor facts changed'
  'Markdown retains stale draft/pending/unresolved/under-review state'
  'Markdown final C7 status changed'
  'Markdown final topology disposition changed'
  'Markdown final C7 closure bindings changed'
  'Markdown path-policy tree derivation changed'
  'Markdown conditional R7 disposition changed'
  'Markdown publication quiescence changed'
  'Markdown publication exact-row inclusion changed'
  'normalize_prose_file() {'
  "LC_ALL=C tr '[:space:]' ' '"
  'prose_contains() {'
  'lost authority-only 2 MiB repair'
  'lost exact package closure'
  'lost exact rg executable closure'
  'lost rg version probe'
  'lost apt byte-pinning nonclaim'
  'lost immutable-v6 byte boundary'
  'lost finalized C6-era r11 predecessor'
  'lost fresh current C7 r12'
  'validated-commit authority route or inherited-probe boundary changed'
  'lost validated exact-C7 authority subject'
  'lost new-wrapper-only bound selection'
  'raise ValueError("top-level inventory changed")'
  'fail("schema dialect, identifier, or root closure changed")'
  'TeX fixed local command lost its texttt binding'
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
  'figure Form Matrix is nonidentity'
  'figure Form is preceded by a clipping operator'
  'page-transform hostile cannot locate the figure invocation'
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
    echo "composite-v7 boundary PDF self-test: gate lost source policy: $literal" >&2
    exit 1
  }
done

TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-composite-v7-boundary-self-test.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT

copy_fixture() {
  local destination="$1"
  mkdir -p \
    "$destination/scripts" \
    "$destination/audit/evidence" \
    "$destination/audit/schemas" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v7-boundary" \
    "$destination/output/pdf"
  cp "$ROOT/$GATE" "$destination/$GATE"
  cp "$ROOT/scripts/check-formal-pdf-log.sh" "$destination/scripts/check-formal-pdf-log.sh"
  cp "$ROOT/scripts/compare-formal-pdf-renders.py" "$destination/scripts/compare-formal-pdf-renders.py"
  cp "$ROOT/audit/formal/latex/pid-rs-report-tables.sty" "$destination/audit/formal/latex/pid-rs-report-tables.sty"
  cp "$ROOT/audit/formal/latex/ksg-m1a-composite-v7-boundary.tex" "$destination/audit/formal/latex/ksg-m1a-composite-v7-boundary.tex"
  cp "$ROOT/audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" "$destination/audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md"
  cp "$ROOT/$COUNTEREXAMPLE" "$destination/$COUNTEREXAMPLE"
  cp "$ROOT/$COUNTEREXAMPLE_SCHEMA" "$destination/$COUNTEREXAMPLE_SCHEMA"
  cp "$ROOT/$SVG" "$destination/$SVG"
  cp "$ROOT/audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf" \
    "$destination/audit/formal/latex/figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf"
  cp "$ROOT/$PDF" "$destination/$PDF"
  cp "$ROOT/output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv" \
    "$destination/output/pdf/ksg-m1a-composite-v7-boundary.rendering-receipt.tsv"
  cp "$ROOT/$VISUAL" "$destination/$VISUAL"
  chmod 755 "$destination/$GATE" "$destination/scripts/check-formal-pdf-log.sh"
}

expect_failure() {
  local fixture="$1" expected="$2" label="$3"
  if (cd "$fixture" && "$GATE" "$MODE") >"$TEST_ROOT/$label.stdout" 2>"$TEST_ROOT/$label.stderr"; then
    echo "composite-v7 boundary PDF self-test: hostile was accepted: $label" >&2
    exit 1
  fi
  if ! rg -F -- "$expected" "$TEST_ROOT/$label.stderr" >/dev/null; then
    cat "$TEST_ROOT/$label.stdout" "$TEST_ROOT/$label.stderr" >&2
    echo "composite-v7 boundary PDF self-test: hostile was noncausal: $label" >&2
    exit 1
  fi
}

rebind_text_file() {
  local fixture="$1" relative="$2" needle="$3" replacement="$4" \
    sha_variable="$5" bytes_variable="$6"
  python3 -I -S - "$fixture/$relative" "$fixture/$GATE" "$needle" "$replacement" \
    "$sha_variable" "$bytes_variable" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path, gate = map(Path, sys.argv[1:3])
needle, replacement, sha_variable, bytes_variable = sys.argv[3:]
text = path.read_text(encoding="utf-8")
if text.count(needle) != 1:
    raise SystemExit(f"self-test mutation source count changed for {needle!r}")
path.write_text(text.replace(needle, replacement, 1), encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source, sha_count = re.subn(
    rf'{re.escape(sha_variable)}="[0-9a-f]{{64}}"',
    f'{sha_variable}="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source, bytes_count = re.subn(
    rf"{re.escape(bytes_variable)}=[0-9]+",
    f"{bytes_variable}={len(data)}",
    source,
    count=1,
)
if (sha_count, bytes_count) != (1, 1):
    raise SystemExit("self-test could not reseal source binding")
gate.write_text(source, encoding="utf-8", newline="\n")
PY
}

# Reintroduce each stale publication-state class while resealing the outer
# Markdown binding. Rejection must therefore reach the explicit final-state
# predicate rather than stop at the digest.
stale_draft_fixture="$TEST_ROOT/stale-draft"
copy_fixture "$stale_draft_fixture"
rebind_text_file "$stale_draft_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "Status: **final C7 process-publication boundary;" \
  "Status: **draft C7 process-publication boundary;" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$stale_draft_fixture" \
  "Markdown retains stale draft/pending/unresolved/under-review state" stale-draft-state

stale_pending_fixture="$TEST_ROOT/stale-pending"
copy_fixture "$stale_pending_fixture"
rebind_text_file "$stale_pending_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "The exact R7 delta is fixed independently of the frozen C7 rows:" \
  "The exact R7 delta remains pending despite the frozen C7 rows:" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$stale_pending_fixture" \
  "Markdown retains stale draft/pending/unresolved/under-review state" stale-pending-state

stale_unresolved_fixture="$TEST_ROOT/stale-unresolved"
copy_fixture "$stale_unresolved_fixture"
rebind_text_file "$stale_unresolved_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "file set is included in the frozen exact C7 row inventory" \
  "file set is included in the unresolved exact C7 row inventory" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$stale_unresolved_fixture" \
  "Markdown retains stale draft/pending/unresolved/under-review state" stale-unresolved-state

stale_review_fixture="$TEST_ROOT/stale-under-review"
copy_fixture "$stale_review_fixture"
rebind_text_file "$stale_review_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "The full v7 process-publication family is delivered and quiescent:" \
  "The full v7 process-publication family is delivered and under review:" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$stale_review_fixture" \
  "Markdown retains stale draft/pending/unresolved/under-review state" stale-under-review-state

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

# Rebind a source-level attempt-domain conflation. L7 is unnumbered; only
# hosted C7 terms have attempt-1 authority.
attempt_fixture="$TEST_ROOT/attempt-domain"
copy_fixture "$attempt_fixture"
rebind_text_file "$attempt_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "L7 carries no attempt-number authority." \
  "fresh attempt-1 local L7 is required." \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$attempt_fixture" \
  "local/hosted attempt-domain separation changed" attempt-domain-conflation

# Collapse the explicitly distinct local and hosted defects into one class.
conflation_fixture="$TEST_ROOT/defect-conflation"
copy_fixture "$conflation_fixture"
rebind_text_file "$conflation_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "Two bounded defect classes are known" \
  "One bounded defect class is known" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$conflation_fixture" \
  "Markdown lost the two-distinct-defect boundary" defect-conflation

# Mutate the exact terminal predecessor roster while preserving the Markdown
# digest, so the gate must reach the terminal-fact predicate.
terminal_fixture="$TEST_ROOT/terminal-roster"
copy_fixture "$terminal_fixture"
rebind_text_file "$terminal_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "45 jobs: 44 success and the sole" \
  "45 jobs: 43 success and the sole" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$terminal_fixture" \
  "terminal predecessor facts changed: 44 success" terminal-roster

# Turn the command-availability marker into a PDF-content overclaim.
pdf_claim_fixture="$TEST_ROOT/missing-rg-pdf-overclaim"
copy_fixture "$pdf_claim_fixture"
rebind_text_file "$pdf_claim_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "The hosted diagnostic is a dependency-closure failure, not evidence of PDF-content failure." \
  "The hosted diagnostic proves PDF-content failure." \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$pdf_claim_fixture" \
  "hosted correlation or PDF-content boundary changed" missing-rg-pdf-overclaim

# Collapse the authority-only 2 MiB repair back to the generic limit.
bound_fixture="$TEST_ROOT/wrong-authority-bound"
copy_fixture "$bound_fixture"
rebind_text_file "$bound_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "separate 2,097,152-byte authority-stream bound" \
  "separate 65,536-byte authority-stream bound" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$bound_fixture" \
  "Markdown or TeX lost exact authority bound" wrong-authority-bound

# Break the append-only direct-child topology while preserving outer custody.
topology_fixture="$TEST_ROOT/topology"
copy_fixture "$topology_fixture"
rebind_text_file "$topology_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "C7 is the exact unsigned direct child of C6." \
  "C7 may be a sibling of C6." \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$topology_fixture" \
  "Markdown direct-child topology changed" topology

# Rebind a positive hermeticity claim while retaining outer source custody.
hermeticity_fixture="$TEST_ROOT/hermeticity"
copy_fixture "$hermeticity_fixture"
rebind_text_file "$hermeticity_fixture" \
  "audit/evidence/ksg-rev4-m1a-composite-v7-boundary-2026-08-18.md" \
  "not hermetic execution" \
  "proves hermetic execution" \
  EXPECTED_MD_SHA256 EXPECTED_MD_BYTES
expect_failure "$hermeticity_fixture" \
  "local hermeticity boundary changed" hermeticity-overclaim

# Rebind the historical tab-for-backslash typo so the command presentation
# predicate, rather than the TeX digest, must reject it.
texttt_fixture="$TEST_ROOT/texttt"
copy_fixture "$texttt_fixture"
python3 -I -S - \
  "$texttt_fixture/audit/formal/latex/ksg-m1a-composite-v7-boundary.tex" \
  "$texttt_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    r"\texttt{just ksg-composite-v7}",
    "\texttt{just ksg-composite-v7}",
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
  "$tex_fixture/audit/formal/latex/ksg-m1a-composite-v7-boundary.tex" \
  "$tex_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import re
import sys

path = Path(sys.argv[1])
gate = Path(sys.argv[2])
text = path.read_text(encoding="utf-8").replace(
    "figures/ksg-m1a-composite-v7-boundary/c6-failure-c7-r7.pdf",
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

# Omit the machine counterexample list and reseal its outer digest so rejection
# must reach the closed semantic inventory.
counterexample_omission_fixture="$TEST_ROOT/counterexample-omission"
copy_fixture "$counterexample_omission_fixture"
python3 -I -S - \
  "$counterexample_omission_fixture/$COUNTEREXAMPLE" \
  "$counterexample_omission_fixture/$GATE" omission <<'PY'
from pathlib import Path
import hashlib
import json
import re
import sys

path, gate = map(Path, sys.argv[1:3])
mode = sys.argv[3]
value = json.loads(path.read_text(encoding="utf-8"))
if mode == "omission":
    del value["counterexamples"]
else:
    value["bounds"]["committed_internal_stream_bound_bytes"] = 2097152
path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_COUNTEREXAMPLE_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_COUNTEREXAMPLE_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_COUNTEREXAMPLE_BYTES=[0-9]+",
    f"EXPECTED_COUNTEREXAMPLE_BYTES={len(data)}",
    source,
    count=1,
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$counterexample_omission_fixture" \
  "counterexample top-level inventory changed" counterexample-omission

# Mutate the bound relation and reseal the counterexample digest.
counterexample_bound_fixture="$TEST_ROOT/counterexample-bound"
copy_fixture "$counterexample_bound_fixture"
python3 -I -S - \
  "$counterexample_bound_fixture/$COUNTEREXAMPLE" \
  "$counterexample_bound_fixture/$GATE" bound <<'PY'
from pathlib import Path
import hashlib
import json
import re
import sys

path, gate = map(Path, sys.argv[1:3])
value = json.loads(path.read_text(encoding="utf-8"))
value["bounds"]["committed_internal_stream_bound_bytes"] = 2097152
path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_COUNTEREXAMPLE_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_COUNTEREXAMPLE_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_COUNTEREXAMPLE_BYTES=[0-9]+",
    f"EXPECTED_COUNTEREXAMPLE_BYTES={len(data)}",
    source,
    count=1,
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$counterexample_bound_fixture" \
  "counterexample bound relation changed" counterexample-bound

# Remove one required schema property and reseal the schema digest.
schema_fixture="$TEST_ROOT/counterexample-schema"
copy_fixture "$schema_fixture"
python3 -I -S - \
  "$schema_fixture/$COUNTEREXAMPLE_SCHEMA" "$schema_fixture/$GATE" <<'PY'
from pathlib import Path
import hashlib
import json
import re
import sys

path, gate = map(Path, sys.argv[1:])
value = json.loads(path.read_text(encoding="utf-8"))
value["required"].remove("counterexamples")
path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
data = path.read_bytes()
source = gate.read_text(encoding="utf-8")
source = re.sub(
    r'EXPECTED_COUNTEREXAMPLE_SCHEMA_SHA256="[0-9a-f]{64}"',
    f'EXPECTED_COUNTEREXAMPLE_SCHEMA_SHA256="{hashlib.sha256(data).hexdigest()}"',
    source,
    count=1,
)
source = re.sub(
    r"EXPECTED_COUNTEREXAMPLE_SCHEMA_BYTES=[0-9]+",
    f"EXPECTED_COUNTEREXAMPLE_SCHEMA_BYTES={len(data)}",
    source,
    count=1,
)
gate.write_text(source, encoding="utf-8", newline="\n")
PY
expect_failure "$schema_fixture" \
  "counterexample schema dialect, identifier, or root closure changed" counterexample-schema

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
  echo "OK: composite-v7 boundary PDF exact/cross positives and nineteen external hostile fixtures passed"
else
  echo "OK: composite-v7 boundary PDF cross-toolchain positive and nineteen external hostile fixtures passed"
fi
