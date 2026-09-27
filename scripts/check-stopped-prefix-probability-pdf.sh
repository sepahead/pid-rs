#!/usr/bin/env bash
set -euo pipefail

ROOT="$(CDPATH='' cd -- "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/audit/formal/lean-stopped-prefix-probability/EXPOSITION.md"
FIGURE="$ROOT/audit/formal/lean-stopped-prefix-probability/figures/first-hit-and-prefix-return.svg"
PROFILE="$ROOT/audit/formal/latex/stopped-prefix-probability/profile.json"
FONT_MANIFEST="$ROOT/audit/formal/latex/stopped-prefix-probability/figure-fonts.json"
PDF="$ROOT/output/pdf/stopped-prefix-probability.pdf"
BUILDER="$ROOT/scripts/build-stopped-prefix-probability-pdf.sh"
HEADER="$ROOT/audit/formal/latex/stopped-prefix-probability/publication.tex"
FILTER="$ROOT/audit/formal/latex/stopped-prefix-probability/filter.lua"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
CHECK_NAME="Stopped-prefix probability PDF check"
EXPECTED_PAGES="$(python3 -I -B -c 'import json,sys; print(json.load(open(sys.argv[1]))["pages"])' "$PROFILE")"
[[ "$EXPECTED_PAGES" =~ ^[1-9][0-9]*$ ]] || { echo "invalid page profile" >&2; exit 1; }
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
  "$FIGURE"
  "$PROFILE"
  "$FONT_MANIFEST"
  "$PDF"
  "$BUILDER"
  "$HEADER"
  "$FILTER"
  "$TAGPDF_OPENACTION_COMPAT"
)
for required in "${required_inputs[@]}"; do
  [[ -f "$required" && ! -L "$required" ]] || {
    echo "$CHECK_NAME failed: required input is absent, nonregular, or symbolic: $required" >&2
    exit 1
  }
done

tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-stopped-prefix-probability-check.XXXXXX")"
cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT

python3 -I -B - "$ROOT" "$SOURCE" <<'PYMD'
from pathlib import Path
import runpy
import sys
root, source = map(Path, sys.argv[1:])
checker = runpy.run_path(str(root / "scripts/check-markdown-math.py"))
findings = checker["inspect_repository_path"](source, root=root)
if findings:
    raise SystemExit("\n".join(f"{f.path}:{f.line}: {f.message}" for f in findings))
PYMD

python3 -I -B - "$FONT_MANIFEST" <<'PYFONTMANIFEST'
import json
from pathlib import Path
import re
import sys

# BEGIN FIGURE FONT MANIFEST CONTRACT (identical in builder and checker)
def font_fail(message):
    raise SystemExit(f"Stopped-prefix figure fonts: {message}")


def unique_members(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            font_fail(f"duplicate manifest key: {key}")
        result[key] = value
    return result


def read_font_manifest(path):
    raw = path.read_bytes()
    if len(raw) > 16384:
        font_fail("manifest exceeds its byte bound")
    try:
        manifest = json.loads(raw, object_pairs_hook=unique_members)
    except (ValueError, UnicodeError) as error:
        font_fail(f"invalid manifest JSON: {error}")
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "pango_backend", "fontconfig_template", "fonts"
    }:
        font_fail("manifest shape changed")
    if type(manifest["schema"]) is not int or manifest["schema"] != 1:
        font_fail("manifest schema changed")
    if manifest["pango_backend"] != "fc":
        font_fail("Pango backend must be fc")
    expected_template = (
        '<?xml version="1.0"?>\n<fontconfig>\n  <reset-dirs/>\n'
        '  <dir>{font_directory}</dir>\n'
        '  <cachedir>{cache_directory}</cachedir>\n</fontconfig>\n'
    )
    if manifest["fontconfig_template"] != expected_template:
        font_fail("font configuration changed: require reset, one private directory/cache, no DTD or includes")
    expected_names = [
        ("SourceSansPro-Regular.otf", "SourceSansPro-Regular"),
        ("SourceSansPro-Semibold.otf", "SourceSansPro-Semibold"),
        ("SourceSansPro-Bold.otf", "SourceSansPro-Bold"),
        ("latinmodern-math.otf", "LatinModernMath-Regular"),
    ]
    fonts = manifest["fonts"]
    if not isinstance(fonts, list) or len(fonts) != len(expected_names):
        font_fail("font roster changed")
    for font, (filename, postscript_name) in zip(fonts, expected_names):
        if not isinstance(font, dict) or set(font) != {"filename", "sha256", "postscript_name"}:
            font_fail("font entry shape changed")
        if font["filename"] != filename or font["postscript_name"] != postscript_name:
            font_fail("font filename or PostScript identity changed")
        if not isinstance(font["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", font["sha256"]) is None:
            font_fail("font digest is malformed")
    return manifest, raw
# END FIGURE FONT MANIFEST CONTRACT

read_font_manifest(Path(sys.argv[1]))
PYFONTMANIFEST

source_digest_record="$tmp_root/source-digests.txt"
(
  cd "$ROOT"
  shasum -a 256 \
    "audit/formal/lean-stopped-prefix-probability/EXPOSITION.md" \
    "audit/formal/lean-stopped-prefix-probability/figures/first-hit-and-prefix-return.svg" \
    "audit/formal/latex/stopped-prefix-probability/figure-fonts.json" \
    "audit/formal/latex/stopped-prefix-probability/publication.tex" \
    "audit/formal/latex/stopped-prefix-probability/filter.lua" \
    "audit/formal/latex/pid-rs-report-tables.sty" \
    "audit/formal/latex/pid-rs-workflow-publication.sty" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
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
      "^Pages:[[:space:]]+${EXPECTED_PAGES}$" \
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

  # Body fonts come from publication.tex and pid-rs-workflow-publication.sty;
  # the figure's four-font inventory is checked separately before composition.
  python3 -I -B - "$fonts" <<'PYPUBLICATIONFONTS'
from pathlib import Path
import re
import sys

body_fonts = {
    "LMRoman10-Regular", "LMRoman10-Italic", "LMRoman10-Bold", "LMRoman10-BoldItalic",
    "LMMono10-Regular", "LMMono10-Italic", "LMMonoLt10-Bold", "LMMonoLt10-BoldOblique",
    "SourceSansPro-Regular", "SourceSansPro-RegularIt",
    "SourceSansPro-Semibold", "SourceSansPro-SemiboldIt", "LatinModernMath-Regular",
}
figure_fonts = {
    "SourceSansPro-Regular", "SourceSansPro-Semibold", "SourceSansPro-Bold",
    "LatinModernMath-Regular",
}
for line in Path(sys.argv[1]).read_text().splitlines()[2:]:
    fields = line.split()
    if len(fields) < 8:
        raise SystemExit("Stopped-prefix probability PDF check failed: malformed publication font inventory")
    name = re.sub(r"^[A-Z]{6}\+", "", fields[0])
    if name not in body_fonts | figure_fonts:
        raise SystemExit(f"Stopped-prefix probability PDF check failed: undeclared publication font: {name}")
    if " ".join(fields[1:-6]) not in {"Type 1C", "CID Type 0C"}:
        raise SystemExit(f"Stopped-prefix probability PDF check failed: unexpected publication font type: {line}")
PYPUBLICATIONFONTS

  LC_ALL=C pdftotext -layout "$candidate" "$text"
  LC_ALL=C tr '\f\n\r\t' '    ' <"$text" | LC_ALL=C tr -s ' ' >"$normalized_text"
  for sentinel in \
      'PID-RS TECHNICAL REPORT SERIES' \
      'Sepehr Mahmoudian' \
      'Finite rows and their actual probability law' \
      'an unnormalized first-hit factorization' \
      'mass and endpoint cases' \
      'Rust implementation and computational cost' \
      'The unfinished stopping argument'; do
    grep -Fq "$sentinel" "$normalized_text" || {
      echo "$CHECK_NAME failed: $label omitted reviewed text: $sentinel" >&2
      exit 1
    }
  done
  if grep -Eq '\\begin\{|\\end\{|\$\$|\\[[:alpha:]]+|�' "$text"; then
    echo "$CHECK_NAME failed: $label contains raw TeX, replacement glyphs, or stale absence text" >&2
    exit 1
  fi

  python3 -I -B - "$candidate" "$expected_trailer_id" "$EXPECTED_PAGES" "$PROFILE" <<'PY'
import sys
import json
from urllib.parse import urlparse

import pypdf
from pypdf import PdfReader
from pypdf.generic import ArrayObject, BooleanObject, DictionaryObject, IndirectObject

path = sys.argv[1]
expected_id = bytes.fromhex(sys.argv[2])
expected_pages = int(sys.argv[3])
with open(sys.argv[4]) as source:
    profile = json.load(source)

def dereference(value):
    return value.get_object() if isinstance(value, IndirectObject) else value

def fail(message):
    raise SystemExit(f"stopped-prefix probability PDF object check failed: {message}")

if pypdf.__version__ != "6.16.1":
    fail(f"unaudited pypdf version: {pypdf.__version__}")
reader = PdfReader(path, strict=True)
if str(reader.metadata.get("/Author")) != "Sepehr Mahmoudian":
    fail("author metadata changed")
if str(reader.metadata.get("/Title")) != profile["title"]:
    fail("title metadata changed")
if len(reader.pages) != expected_pages:
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
if isinstance(open_action, DictionaryObject) and open_action.get("/Next") is not None:
    fail("catalog OpenAction contains a chained action")
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
expected_repository_uris = set(profile["repository_uris"])
observed_repository_uris = set()
observed_all_uris = set()
form_xobjects = set()
for page_index, page in enumerate(reader.pages):
    if page.get("/AA") is not None:
        fail(f"page {page_index + 1} contains additional actions")
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
        if annotation.get("/AA") is not None:
            fail(f"page {page_index + 1} annotation contains additional actions")
        action = dereference(annotation.get("/A"))
        if action is None:
            if annotation.get("/Dest") is None:
                fail(f"page {page_index + 1} link has neither action nor destination")
            action_counts["/GoTo"] += 1
            continue
        if not isinstance(action, DictionaryObject):
            fail(f"page {page_index + 1} link action is malformed")
        if action.get("/Next") is not None:
            fail(f"page {page_index + 1} contains a chained action")
        kind = str(action.get("/S"))
        if kind in forbidden_action_kinds or kind not in allowed_action_kinds:
            fail(f"page {page_index + 1} contains forbidden or unknown action {kind}")
        action_counts[kind] += 1
        if kind == "/URI":
            uri = str(action.get("/URI"))
            observed_all_uris.add(uri)
            parsed = urlparse(uri)
            if parsed.scheme == "https" and parsed.netloc:
                if uri.startswith("https://github.com/sepahead/pid-rs/blob/main/"):
                    observed_repository_uris.add(uri)
                continue
            fail(f"page {page_index + 1} contains a non-HTTPS URI")
if len(form_xobjects) != profile["form_xobjects"]:
    fail(f"form XObject inventory changed: {len(form_xobjects)}")
if observed_all_uris != set(profile["all_uris"]):
    fail("complete URI inventory changed")
if observed_repository_uris != expected_repository_uris:
    fail(f"repository-navigation URI inventory changed: {sorted(observed_repository_uris)}")
expected_action_counts = profile["action_counts"]
if action_counts != expected_action_counts:
    fail(f"navigation inventory changed: {action_counts}")
print(
    "pdf-objects=GO "
    f"pages={len(reader.pages)} forms={len(form_xobjects)} "
    f"goto={action_counts['/GoTo']} uri={action_counts['/URI']} gotor={action_counts['/GoToR']}"
)
PY

  pdftoppm -f 1 -l "$EXPECTED_PAGES" -r 36 -png "$candidate" "$render_prefix" >/dev/null 2>&1
  local rendered_count
  rendered_count="$(find "$tmp_root" -maxdepth 1 -type f -name "$label-page-*.png" -size +0c | wc -l | awk '{print $1}')"
  [[ "$rendered_count" == "$EXPECTED_PAGES" ]] || {
    echo "$CHECK_NAME failed: $label did not render all $EXPECTED_PAGES nonempty pages" >&2
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

printf 'OK: stopped-prefix probability PDF mode=%s pages=%s sha256=%s\n' \
  "$MODE" "$EXPECTED_PAGES" "$(shasum -a 256 "$PDF" | awk '{print $1}')"
