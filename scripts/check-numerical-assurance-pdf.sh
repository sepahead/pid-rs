#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/NUMERICAL_ASSURANCE.md"
PDF="$ROOT/output/pdf/numerical-assurance.pdf"
BUILDER="$ROOT/scripts/build-numerical-assurance-pdf.sh"
HEADER="$ROOT/audit/formal/latex/numerical-assurance/header.tex"
FILTER="$ROOT/audit/formal/latex/numerical-assurance/filter.lua"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
FIGURE_DIR="$ROOT/audit/formal/latex/figures/numerical-assurance"
FIGURE_MANIFEST="$FIGURE_DIR/figure-assets.json"
CHECK_NAME="Numerical assurance PDF check"
MODE="${1:---exact}"

if [[ $# -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command_name in awk cmp find grep mktemp pdffonts pdfinfo pdftoppm pdftotext python3 rm shasum tr; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME failed: missing command: $command_name" >&2
    exit 1
  }
done

required_inputs=(
  "$SOURCE"
  "$PDF"
  "$BUILDER"
  "$HEADER"
  "$FILTER"
  "$TAGPDF_OPENACTION_COMPAT"
  "$FIGURE_MANIFEST"
  "$FIGURE_DIR/quantizer-cardinality.svg"
  "$FIGURE_DIR/quantizer-cardinality.pdf"
  "$FIGURE_DIR/represented-sum-boundary.svg"
  "$FIGURE_DIR/represented-sum-boundary.pdf"
)
for required in "${required_inputs[@]}"; do
  [[ -f "$required" && ! -L "$required" ]] || {
    echo "$CHECK_NAME failed: required input is absent, nonregular, or symbolic: $required" >&2
    exit 1
  }
done

tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-numerical-assurance-check.XXXXXX")"
cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT

python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"

source_digest_record="$tmp_root/source-digests.txt"
(
  cd "$ROOT"
  shasum -a 256 \
    "NUMERICAL_ASSURANCE.md" \
    "audit/formal/latex/numerical-assurance/header.tex" \
    "audit/formal/latex/numerical-assurance/filter.lua" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "audit/formal/latex/figures/numerical-assurance/figure-assets.json" \
    "audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.svg" \
    "audit/formal/latex/figures/numerical-assurance/quantizer-cardinality.pdf" \
    "audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.svg" \
    "audit/formal/latex/figures/numerical-assurance/represented-sum-boundary.pdf"
) >"$source_digest_record"
expected_trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$expected_trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "$CHECK_NAME failed: expected source-derived trailer ID is malformed" >&2
  exit 1
}

rebuilt="$tmp_root/rebuilt.pdf"
"$BUILDER" --output "$rebuilt"

validate_pdf() {
  local candidate="$1"
  local label="$2"
  local info="$tmp_root/$label.pdfinfo"
  local fonts="$tmp_root/$label.pdffonts"
  local text="$tmp_root/$label.txt"
  local normalized_text="$tmp_root/$label-normalized.txt"
  local render_prefix="$tmp_root/$label-page"

  LC_ALL=C pdfinfo "$candidate" >"$info"
  for required_info in \
      '^Pages:[[:space:]]+23$' \
      '^Tagged:[[:space:]]+yes$' \
      '^Suspects:[[:space:]]+no$' \
      '^Form:[[:space:]]+none$' \
      '^JavaScript:[[:space:]]+no$' \
      '^Encrypted:[[:space:]]+no$' \
      '^Page size:[[:space:]]+595\.276 x 841\.89 pts \(A4\)$' \
      '^Page rot:[[:space:]]+0$' \
      '^PDF version:[[:space:]]+1\.7$'; do
    grep -Eq "$required_info" "$info" || {
      echo "$CHECK_NAME failed: $label metadata omitted: $required_info" >&2
      exit 1
    }
  done

  LC_ALL=C pdffonts "$candidate" >"$fonts"
  awk '
    NR > 2 {
      rows += 1
      if ($(NF - 4) != "yes") bad = 1
    }
    END { exit (!rows || bad) }
  ' "$fonts" || {
    cat "$fonts" >&2
    echo "$CHECK_NAME failed: $label has a missing or nonembedded font" >&2
    exit 1
  }

  LC_ALL=C pdftotext -layout "$candidate" "$text"
  LC_ALL=C tr '\f\n\r\t' '    ' <"$text" | LC_ALL=C tr -s ' ' >"$normalized_text"
  for sentinel in \
      'Exact reduction of already represented binary64 operands is not exact estimation.' \
      'The highest set bit of' \
      'There is no test-only switch' \
      'Twelve materially distinct routes considered' \
      'Fifty-lens hostile review' \
      'Proposed CREBAIN' \
      'thermal window' \
      'References and exact repository routes' \
      'IEEE Standard for Floating-Point Arithmetic' \
      'Partial Information Decomposition for Continuous Variables based on'; do
    grep -Fq "$sentinel" "$normalized_text" || {
      echo "$CHECK_NAME failed: $label omitted reviewed text: $sentinel" >&2
      exit 1
    }
  done
  if grep -Eq '\\begin\{|\\end\{|\$\$|\\[[:alpha:]]+|�|Dedicated PDF absent|does not exist' "$text"; then
    echo "$CHECK_NAME failed: $label contains raw TeX, replacement glyphs, or stale absence text" >&2
    exit 1
  fi

  python3 -I -B - "$candidate" "$expected_trailer_id" <<'PY'
import sys
from urllib.parse import urlparse

import pypdf
from pypdf import PdfReader
from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, IndirectObject

path = sys.argv[1]
expected_id = bytes.fromhex(sys.argv[2])

def dereference(value):
    return value.get_object() if isinstance(value, IndirectObject) else value

def fail(message):
    raise SystemExit(f"numerical assurance PDF object check failed: {message}")

if pypdf.__version__ != "6.15.0":
    fail(f"unaudited pypdf version: {pypdf.__version__}")
reader = PdfReader(path, strict=True)
if len(reader.pages) != 23:
    fail("page count changed")
root = reader.trailer["/Root"]
if str(root.get("/Lang")) != "en-US":
    fail("catalog language is not en-US")
mark_info = dereference(root.get("/MarkInfo"))
marked = mark_info.get("/Marked") if isinstance(mark_info, DictionaryObject) else None
if not isinstance(marked, BooleanObject) or marked.value is not True:
    fail("tagged-document MarkInfo is absent")
if root.get("/StructTreeRoot") is None:
    fail("structure tree is absent")
for key in ("/AcroForm", "/AA", "/AF", "/Collection", "/Perms"):
    if root.get(key) is not None:
        fail(f"catalog contains forbidden {key}")
names = dereference(root.get("/Names"))
if isinstance(names, DictionaryObject):
    for key in ("/JavaScript", "/EmbeddedFiles"):
        if names.get(key) is not None:
            fail(f"catalog names contain forbidden {key}")

trailer_ids = reader.trailer.get("/ID")
if not isinstance(trailer_ids, ArrayObject) or len(trailer_ids) != 2:
    fail("trailer ID is not a duplicated pair")
actual_ids = []
for value in trailer_ids:
    raw = getattr(value, "original_bytes", None)
    if raw is None and isinstance(value, bytes):
        raw = bytes(value)
    if raw is None:
        fail("trailer ID member is not a byte string")
    actual_ids.append(raw)
if actual_ids != [expected_id, expected_id]:
    fail("trailer ID is not source derived")

open_action = dereference(root.get("/OpenAction"))
if not isinstance(open_action, DictionaryObject) or str(open_action.get("/S")) != "/GoTo":
    fail("catalog OpenAction is not a bounded internal GoTo")
destination = dereference(open_action.get("/D"))
if not isinstance(destination, ArrayObject) or len(destination) != 2 or str(destination[1]) != "/Fit":
    fail("catalog OpenAction destination is malformed")
target = destination[0]
first_page = reader.pages[0].indirect_reference
if not isinstance(target, IndirectObject) or first_page is None:
    fail("catalog OpenAction target is not an indirect page")
if (target.idnum, target.generation) != (first_page.idnum, first_page.generation):
    fail("catalog OpenAction does not target page one")

forbidden_action_kinds = {
    "/ImportData", "/JavaScript", "/Launch", "/Movie", "/Named", "/Rendition",
    "/ResetForm", "/RichMedia", "/SetOCGState", "/Sound", "/SubmitForm", "/Thread",
}
allowed_action_kinds = {"/GoTo", "/GoToR", "/URI"}
action_counts = {kind: 0 for kind in allowed_action_kinds}
expected_repository_uris = {
    "https://github.com/sepahead/pid-rs/blob/main/"
    "PID2_REPRESENTED_COORDINATE_ASSURANCE.md",
    "https://github.com/sepahead/pid-rs/blob/main/"
    "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md"
}
observed_repository_uris = set()
form_xobjects = set()
for page_index, page in enumerate(reader.pages):
    resources = dereference(page.get("/Resources"))
    xobjects = dereference(resources.get("/XObject")) if isinstance(resources, DictionaryObject) else None
    if isinstance(xobjects, DictionaryObject):
        for value in xobjects.values():
            reference = value if isinstance(value, IndirectObject) else getattr(value, "indirect_reference", None)
            obj = dereference(value)
            if isinstance(obj, DictionaryObject) and str(obj.get("/Subtype")) == "/Form" and isinstance(reference, IndirectObject):
                form_xobjects.add((reference.idnum, reference.generation))
    annotations = dereference(page.get("/Annots"))
    if annotations is None:
        continue
    if not isinstance(annotations, ArrayObject):
        fail(f"page {page_index + 1} annotations are malformed")
    for annotation_ref in annotations:
        annotation = dereference(annotation_ref)
        if not isinstance(annotation, DictionaryObject) or str(annotation.get("/Subtype")) != "/Link":
            fail(f"page {page_index + 1} contains a non-link annotation")
        action = dereference(annotation.get("/A"))
        if action is None:
            if annotation.get("/Dest") is None:
                fail(f"page {page_index + 1} link has neither action nor destination")
            action_counts["/GoTo"] += 1
            continue
        if not isinstance(action, DictionaryObject):
            fail(f"page {page_index + 1} link action is malformed")
        kind = str(action.get("/S"))
        if kind in forbidden_action_kinds or kind not in allowed_action_kinds:
            fail(f"page {page_index + 1} contains forbidden or unknown action {kind}")
        action_counts[kind] += 1
        if kind == "/URI":
            uri = str(action.get("/URI"))
            parsed = urlparse(uri)
            if parsed.scheme == "https" and parsed.netloc:
                if uri.startswith("https://github.com/sepahead/pid-rs/blob/main/"):
                    observed_repository_uris.add(uri)
                continue
            fail(f"page {page_index + 1} contains a non-HTTPS URI")
if len(form_xobjects) != 2:
    fail(f"canonical figure-form inventory changed: {len(form_xobjects)}")
if observed_repository_uris != expected_repository_uris:
    fail(f"repository-navigation URI inventory changed: {sorted(observed_repository_uris)}")
expected_action_counts = {"/GoTo": 34, "/GoToR": 0, "/URI": 15}
if action_counts != expected_action_counts:
    fail(f"navigation inventory changed: {action_counts}")
print(
    "pdf-objects=GO "
    f"pages={len(reader.pages)} forms={len(form_xobjects)} "
    f"goto={action_counts['/GoTo']} uri={action_counts['/URI']} gotor={action_counts['/GoToR']}"
)
PY

  pdftoppm -f 1 -l 23 -r 36 -png "$candidate" "$render_prefix" >/dev/null 2>&1
  local rendered_count
  rendered_count="$(find "$tmp_root" -maxdepth 1 -type f -name "$label-page-*.png" -size +0c | wc -l | awk '{print $1}')"
  [[ "$rendered_count" == "23" ]] || {
    echo "$CHECK_NAME failed: $label did not render all 23 nonempty pages" >&2
    exit 1
  }
}

validate_pdf "$PDF" committed
validate_pdf "$rebuilt" rebuilt

if [[ "$MODE" == "--exact" ]]; then
  cmp -s "$rebuilt" "$PDF" || {
    echo "$CHECK_NAME failed: committed PDF is stale or not same-toolchain reproducible" >&2
    exit 1
  }
else
  pdftotext -layout "$PDF" "$tmp_root/committed-layout.txt"
  pdftotext -layout "$rebuilt" "$tmp_root/rebuilt-layout.txt"
  cmp -s "$tmp_root/committed-layout.txt" "$tmp_root/rebuilt-layout.txt" || {
    echo "$CHECK_NAME failed: cross-toolchain extracted layout text changed" >&2
    exit 1
  }
  pdfinfo "$PDF" | grep -E '^(Pages|Page size):' >"$tmp_root/committed-geometry.txt"
  pdfinfo "$rebuilt" | grep -E '^(Pages|Page size):' >"$tmp_root/rebuilt-geometry.txt"
  cmp -s "$tmp_root/committed-geometry.txt" "$tmp_root/rebuilt-geometry.txt" || {
    echo "$CHECK_NAME failed: cross-toolchain page geometry changed" >&2
    exit 1
  }
fi

printf 'OK: numerical assurance PDF mode=%s pages=23 sha256=%s\n' \
  "$MODE" "$(shasum -a 256 "$PDF" | awk '{print $1}')"
