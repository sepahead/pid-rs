#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE="$ROOT/PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md"
PDF="$ROOT/output/pdf/pid-sensor-placement-and-galadriel-guide.pdf"
BUILDER="$ROOT/scripts/build-pid-sensor-placement-and-galadriel-guide-pdf.sh"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
EVIDENCE_RECEIPT="$ROOT/audit/evidence/categorical-pid-latency-718447aa-explicit-20260830.json"
EVIDENCE_ARCHIVE="$ROOT/audit/evidence/categorical-pid-latency-718447aa-explicit-20260830.tar.gz"
CHECK_NAME="PID sensor-placement guide PDF check"
MODE="${1:---exact}"

if [[ $# -gt 1 || ( "$MODE" != "--exact" && "$MODE" != "--cross-toolchain" ) ]]; then
  echo "usage: $0 [--exact|--cross-toolchain]" >&2
  exit 2
fi

for command_name in awk cmp find grep mktemp pdffonts pdfinfo pdftoppm pdftotext \
    python3 rm shasum; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "$CHECK_NAME failed: missing command: $command_name" >&2
    exit 1
  }
done

for required in "$SOURCE" "$PDF" "$BUILDER" "$TAGPDF_OPENACTION_COMPAT" \
    "$EVIDENCE_RECEIPT" "$EVIDENCE_ARCHIVE"; do
  [[ -f "$required" && ! -L "$required" ]] || {
    echo "$CHECK_NAME failed: required input is absent, nonregular, or symbolic: $required" >&2
    exit 1
  }
done

tmp_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-sensor-placement-check.XXXXXX")"
cleanup() {
  rm -rf -- "$tmp_root"
}
trap cleanup EXIT

python3 "$ROOT/scripts/check-markdown-math.py" "$SOURCE"

source_digest_record="$tmp_root/source-digests.txt"
(
  cd "$ROOT"
  shasum -a 256 \
    "PID_SENSOR_PLACEMENT_AND_GALADRIEL_GUIDE.md" \
    "audit/formal/latex/pid-sensor-placement-and-galadriel-guide/header.tex" \
    "audit/formal/latex/pid-sensor-placement-and-galadriel-guide/filter.lua" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex" \
    "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/figure-assets.json"
  for stem in current-versus-proposed measurement-to-estimand placement-evidence-funnel; do
    shasum -a 256 \
      "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/$stem.svg" \
      "audit/formal/latex/figures/pid-sensor-placement-and-galadriel-guide/$stem.pdf"
  done
) >"$source_digest_record"
expected_trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$expected_trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "$CHECK_NAME failed: expected source-derived trailer ID is malformed" >&2
  exit 1
}

python3 -I -B - "$EVIDENCE_RECEIPT" "$EVIDENCE_ARCHIVE" <<'PY'
import hashlib
import json
import pathlib
import sys
import tarfile

receipt_path = pathlib.Path(sys.argv[1])
archive_path = pathlib.Path(sys.argv[2])
receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
expected_archive = receipt["retained_evidence"]["archive_sha256"]
actual_archive = hashlib.sha256(archive_path.read_bytes()).hexdigest()
if actual_archive != expected_archive:
    raise SystemExit("benchmark archive digest disagrees with receipt")
with tarfile.open(archive_path, mode="r:gz") as archive:
    members = archive.getmembers()
    names = [member.name for member in members]
    if len(names) != len(set(names)):
        raise SystemExit("benchmark archive contains duplicate member names")
    for member in members:
        member_path = pathlib.PurePosixPath(member.name)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise SystemExit("benchmark archive contains an unsafe member path")
        if any(part.startswith("._") for part in member_path.parts):
            raise SystemExit("benchmark archive contains AppleDouble metadata")
        if not (member.isfile() or member.isdir()):
            raise SystemExit("benchmark archive contains a non-file, non-directory member")
    regular = [member for member in members if member.isfile()]
    if len(regular) != receipt["retained_evidence"]["regular_files"]:
        raise SystemExit("benchmark archive regular-file inventory disagrees with receipt")
    json_members = [member for member in regular if member.name.endswith(".json")]
    if len(json_members) != receipt["retained_evidence"]["criterion_json_files"]:
        raise SystemExit("benchmark archive JSON inventory disagrees with receipt")
    stdout_name = receipt["retained_evidence"]["raw_stdout_member"]
    stdout_member = archive.getmember(stdout_name)
    stream = archive.extractfile(stdout_member)
    if stream is None:
        raise SystemExit("benchmark archive stdout is unavailable")
    stdout_digest = hashlib.sha256(stream.read()).hexdigest()
if stdout_digest != receipt["retained_evidence"]["raw_stdout_sha256"]:
    raise SystemExit("benchmark stdout digest disagrees with receipt")
if receipt["retained_evidence"]["exit_status"] != 0 or len(receipt["results"]) != 4:
    raise SystemExit("benchmark receipt completion or result inventory changed")
if "real-time qualification" not in receipt["prohibited_claims"]:
    raise SystemExit("benchmark receipt lost its real-time nonclaim")
print(f"benchmark-evidence=GO archive_sha256={actual_archive} criterion_json={len(json_members)}")
PY

rebuilt="$tmp_root/rebuilt.pdf"
"$BUILDER" --output "$rebuilt"

validate_pdf() {
  local candidate="$1"
  local label="$2"
  local info="$tmp_root/$label.pdfinfo"
  local fonts="$tmp_root/$label.pdffonts"
  local fonts_stderr="$tmp_root/$label.pdffonts.stderr"
  local text="$tmp_root/$label.txt"

  LC_ALL=C pdfinfo "$candidate" >"$info"
  grep -Eq '^Pages:[[:space:]]+47$' "$info" || {
    echo "$CHECK_NAME failed: $label page count is not the reviewed 47 pages" >&2
    exit 1
  }
  for required_info in \
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

  if ! LC_ALL=C pdffonts "$candidate" >"$fonts" 2>"$fonts_stderr"; then
    cat "$fonts_stderr" >&2
    echo "$CHECK_NAME failed: pdffonts rejected $label" >&2
    exit 1
  fi
  if [[ -s "$fonts_stderr" ]]; then
    cat "$fonts_stderr" >&2
    echo "$CHECK_NAME failed: pdffonts emitted diagnostics for $label" >&2
    exit 1
  fi
  awk '
    function subset_family(name, prefix) {
      if (length(name) < 8 || substr(name, 7, 1) != "+") return ""
      prefix = substr(name, 1, 6)
      if (prefix !~ /^[A-Z][A-Z][A-Z][A-Z][A-Z][A-Z]$/) return ""
      return substr(name, 8)
    }
    NR == 1 {
      if (NF != 8 || $1 != "name" || $2 != "type" || $3 != "encoding" ||
          $4 != "emb" || $5 != "sub" || $6 != "uni" ||
          $7 != "object" || $8 != "ID") bad = 1
      next
    }
    NR == 2 {
      if (NF != 7) bad = 1
      for (i = 1; i <= NF; i++) if ($i !~ /^-+$/) bad = 1
      next
    }
    NR > 2 {
      if (NF == 0) { bad = 1; next }
      rows += 1
      # Parse from the right because the font-type field can contain spaces.
      encoding = $(NF - 5)
      embedded = $(NF - 4)
      subsetted = $(NF - 3)
      unicode = $(NF - 2)
      object_number = $(NF - 1)
      generation = $NF
      if (object_number !~ /^[0-9]+$/ || generation !~ /^[0-9]+$/ ||
          generation != "0" || seen_object[object_number ":" generation]++) bad = 1
      if (embedded != "yes" || unicode != "yes") bad = 1

      if (NF == 10 && $2 == "CID" && $3 == "Type" && $4 == "0C" &&
          encoding == "Identity-H") {
        family = subset_family($1)
        if (family == "" || subsetted != "yes") bad = 1
        family_count[family] += 1
        cid_type0c += 1
      } else if (NF == 8 && $2 == "TrueType" && encoding == "WinAnsi") {
        family = subset_family($1)
        if (family == "" || subsetted != "yes") bad = 1
        family_count[family] += 1
        truetype += 1
      } else if (NF == 9 && $1 == "[none]" && $2 == "Type" && $3 == "3" &&
          encoding == "Custom") {
        # Type 3 contains its complete CharProcs in the PDF, so Poppler reports
        # sub=no. The Python object check below admits only the inert U+0020 shim.
        if (subsetted != "no") bad = 1
        type3 += 1
      } else {
        bad = 1
      }
    }
    END {
      expected["AvenirNext-Bold"] = 11
      expected["AvenirNext-Medium"] = 7
      expected["LMMonoLt10-Regular"] = 1
      expected["LMRoman10-Bold"] = 2
      expected["LMRoman10-Italic"] = 1
      expected["LMRoman10-Regular"] = 2
      expected["LMRoman12-Bold"] = 1
      expected["LMRoman12-Regular"] = 1
      expected["LMRoman5-Regular"] = 1
      expected["LMRoman6-Regular"] = 1
      expected["LMRoman7-Regular"] = 1
      expected["LMRoman8-Bold"] = 1
      expected["LMRoman8-Regular"] = 2
      expected["LMRoman9-Bold"] = 1
      expected["LMRoman9-Regular"] = 1
      expected["LatinModernMath-Regular"] = 3
      expected["Menlo-Regular"] = 1
      expected["SourceSansPro-Regular"] = 1
      for (family in expected)
        if (family_count[family] != expected[family]) bad = 1
      for (family in family_count)
        if (!(family in expected)) bad = 1
      if (rows != 58 || cid_type0c != 20 || truetype != 19 || type3 != 19) bad = 1
      exit bad ? 1 : 0
    }
  ' "$fonts" || {
    cat "$fonts" >&2
    echo "$CHECK_NAME failed: $label font roster, embedding, subsetting, or Unicode mapping changed" >&2
    exit 1
  }

  LC_ALL=C pdftotext -layout "$candidate" "$text"
  for sentinel in \
      'Current Galadriel does not use PID for placement' \
      'The fixture has three ordered one-column sources and two targets' \
      'describe exact equalities among the columns of this' \
      'marginalized out and the PID2 law has four supported' \
      'Exactly which pid-rs work Galadriel consumes' \
      'Why a PID2 needs one extra definition' \
      'Oracle non-cheating contract' \
      'One-hundred-forty-lens council review' \
      'debd6e36e662dfe50e377bfdef588dc85019f389e5712035009666f112e1eb56' \
      '10.1137/21M1466542' \
      '10.3390/drones6110317' \
      'Measuring the Redundancy of Information from a Source Failure Perspective'; do
    grep -Fq "$sentinel" "$text" || {
      echo "$CHECK_NAME failed: $label omitted reviewed text: $sentinel" >&2
      exit 1
    }
  done
  if grep -Eq 'b8ca126968dee83326cbd52c10850715d23e49d9eb6238d82f17389f8e361a3b|21M1466499|2207\.01927|\\begin\{|\\end\{|�' "$text"; then
    echo "$CHECK_NAME failed: $label contains stale citation text, raw TeX, or replacement glyphs" >&2
    exit 1
  fi

  python3 -I -B - "$candidate" "$expected_trailer_id" <<'PY'
import math
import sys
from collections import Counter
from urllib.parse import urlparse

import pypdf
from pypdf import PdfReader
from pypdf.generic import (
    ArrayObject,
    BooleanObject,
    DictionaryObject,
    FloatObject,
    IndirectObject,
    NumberObject,
    StreamObject,
)

path = sys.argv[1]
expected_trailer_id = bytes.fromhex(sys.argv[2])

def dereference(value):
    return value.get_object() if isinstance(value, IndirectObject) else value

def fail(message):
    raise SystemExit(f"PDF object check failed: {message}")

if pypdf.__version__ != "6.15.0":
    fail(f"unaudited pypdf version: {pypdf.__version__}")

reader = PdfReader(path, strict=True)
root = reader.trailer["/Root"]

def pdf_boolean_is_true(value):
    return isinstance(value, BooleanObject) and value.value is True

# pypdf BooleanObject(False) is truthy as a Python object. Keep an executable
# canary so a future refactor cannot silently replace typed value inspection
# with bool(value).
if not pdf_boolean_is_true(BooleanObject(True)) or pdf_boolean_is_true(BooleanObject(False)):
    fail("pypdf BooleanObject semantics changed")

if len(reader.pages) != 47:
    fail("page count changed")
trailer_ids = reader.trailer.get("/ID")
if not isinstance(trailer_ids, ArrayObject) or len(trailer_ids) != 2:
    fail("trailer ID is not a duplicated pair")
decoded_ids = []
for value in trailer_ids:
    raw = getattr(value, "original_bytes", None)
    if raw is None and isinstance(value, bytes):
        raw = bytes(value)
    if raw is None:
        fail("trailer ID is not a byte string")
    decoded_ids.append(raw)
if decoded_ids != [expected_trailer_id, expected_trailer_id]:
    fail("trailer ID is not the source-derived identifier")
if str(root.get("/Lang")) != "en-US":
    fail("catalog language is not en-US")
mark_info = dereference(root.get("/MarkInfo"))
marked = mark_info.get("/Marked") if isinstance(mark_info, DictionaryObject) else None
if not pdf_boolean_is_true(marked):
    fail("tagged-document MarkInfo is absent")
if root.get("/StructTreeRoot") is None:
    fail("structure tree is absent")
for key in ("/AcroForm", "/AA", "/AF", "/Collection"):
    if root.get(key) is not None:
        fail(f"catalog contains forbidden {key}")

open_action = dereference(root.get("/OpenAction"))
if not isinstance(open_action, DictionaryObject) or str(open_action.get("/S")) != "/GoTo":
    fail("catalog OpenAction is not a bounded internal GoTo")
destination = dereference(open_action.get("/D"))
if not isinstance(destination, ArrayObject) or len(destination) != 2 or str(destination[1]) != "/Fit":
    fail("catalog OpenAction destination is malformed")
first_page_ref = reader.pages[0].indirect_reference
target_ref = destination[0]
if not isinstance(target_ref, IndirectObject) or first_page_ref is None:
    fail("catalog OpenAction target is not an indirect page")
if (target_ref.idnum, target_ref.generation) != (first_page_ref.idnum, first_page_ref.generation):
    fail("catalog OpenAction does not target page one")

names = dereference(root.get("/Names"))
if isinstance(names, DictionaryObject):
    for key in ("/JavaScript", "/EmbeddedFiles"):
        if names.get(key) is not None:
            fail(f"catalog names contain forbidden {key}")

forbidden_keys = {"/AA", "/JS", "/JavaScript", "/Launch", "/SubmitForm", "/ImportData", "/RichMedia", "/Movie", "/Sound", "/FileAttachment", "/EmbeddedFile", "/XFA"}
seen_indirect = set()
type3_identities = set()
type3_shapes = []

TYPE3_FONT_KEYS = frozenset({
    "/Type", "/Subtype", "/FontBBox", "/FontMatrix", "/Encoding",
    "/CharProcs", "/FirstChar", "/LastChar", "/Widths", "/ToUnicode",
    "/Resources",
})
EXPECTED_SPACE_TOUNICODE = (
    b"/CIDInit /ProcSet findresource begin\n"
    b"12 dict begin\n"
    b"begincmap\n"
    b"/CIDSystemInfo\n"
    b"<< /Registry (Adobe)\n"
    b"   /Ordering (UCS)\n"
    b"   /Supplement 0\n"
    b">> def\n"
    b"/CMapName /Adobe-Identity-UCS def\n"
    b"/CMapType 2 def\n"
    b"1 begincodespacerange\n"
    b"<00> <ff>\n"
    b"endcodespacerange\n"
    b"1 beginbfchar\n"
    b"<00> <0020>\n"
    b"endbfchar\n"
    b"endcmap\n"
    b"CMapName currentdict /CMap defineresource pop\n"
    b"end\n"
    b"end\n"
)

def require_dictionary(value, where):
    value = dereference(value)
    if not isinstance(value, DictionaryObject):
        fail(f"{where} is not a dictionary")
    return value

def require_array(value, where):
    value = dereference(value)
    if not isinstance(value, ArrayObject):
        fail(f"{where} is not an array")
    return value

def require_number(value, where):
    value = dereference(value)
    if isinstance(value, BooleanObject) or not isinstance(value, (NumberObject, FloatObject)):
        fail(f"{where} is not a PDF number")
    number = float(value)
    if not math.isfinite(number):
        fail(f"{where} is not finite")
    return number

def require_numeric_array(value, length, where):
    values = require_array(value, where)
    if len(values) != length:
        fail(f"{where} length changed")
    return tuple(require_number(item, f"{where}[{index}]") for index, item in enumerate(values))

def require_stream(value, where):
    value = dereference(value)
    if not isinstance(value, StreamObject):
        fail(f"{where} is not a stream")
    return value

def extract_type3_shape(font, where):
    encoding = require_dictionary(font.get("/Encoding"), f"{where} Encoding")
    differences = require_array(encoding.get("/Differences"), f"{where} Encoding Differences")
    if len(differences) != 2:
        fail(f"{where} Encoding Differences length changed")
    difference_code = require_number(differences[0], f"{where} Encoding Differences[0]")
    char_procs = require_dictionary(font.get("/CharProcs"), f"{where} CharProcs")
    if set(map(str, char_procs.keys())) != {"/0"}:
        # Explicitly rejects an extra-glyph Type 3 before any stream is trusted.
        fail(f"{where} CharProcs is not the one-glyph spacing shim")
    char_proc = require_stream(char_procs.get("/0"), f"{where} CharProcs /0")
    resources = require_dictionary(font.get("/Resources"), f"{where} Resources")
    to_unicode = require_stream(font.get("/ToUnicode"), f"{where} ToUnicode")
    return {
        "font_keys": frozenset(map(str, font.keys())),
        "font_type": str(font.get("/Type")),
        "font_subtype": str(font.get("/Subtype")),
        "first_char": require_number(font.get("/FirstChar"), f"{where} FirstChar"),
        "last_char": require_number(font.get("/LastChar"), f"{where} LastChar"),
        "font_bbox": require_numeric_array(font.get("/FontBBox"), 4, f"{where} FontBBox"),
        "font_matrix": require_numeric_array(font.get("/FontMatrix"), 6, f"{where} FontMatrix"),
        "widths": require_numeric_array(font.get("/Widths"), 1, f"{where} Widths"),
        "encoding_keys": frozenset(map(str, encoding.keys())),
        "encoding_type": str(encoding.get("/Type")),
        "difference_code": difference_code,
        "difference_name": str(differences[1]),
        "char_proc_keys": frozenset(map(str, char_procs.keys())),
        "char_proc_stream_keys": frozenset(map(str, char_proc.keys())),
        "char_proc_filter": str(char_proc.get("/Filter")),
        "char_proc_data": char_proc.get_data(),
        "resource_keys": frozenset(map(str, resources.keys())),
        "to_unicode_stream_keys": frozenset(map(str, to_unicode.keys())),
        "to_unicode_filter": str(to_unicode.get("/Filter")),
        "to_unicode_data": to_unicode.get_data(),
    }

def type3_contract_error(shape):
    if shape["font_keys"] != TYPE3_FONT_KEYS:
        return "font dictionary keys changed"
    if shape["font_type"] != "/Font" or shape["font_subtype"] != "/Type3":
        return "font type changed"
    if shape["first_char"] != 0.0 or shape["last_char"] != 0.0:
        return "character interval is not the singleton code zero"
    if shape["font_bbox"] != (0.0, 0.0, 0.0, 0.0):
        return "font bounding box is not empty"
    if shape["font_matrix"] != (1.0, 0.0, 0.0, -1.0, 0.0, 0.0):
        return "font matrix changed"
    width = shape["widths"][0]
    if not any(math.isclose(width, allowed, rel_tol=0.0, abs_tol=1e-9) for allowed in (0.25, 0.602051)):
        return "spacing width changed"
    if shape["encoding_keys"] != frozenset({"/Type", "/Differences"}) or \
            shape["encoding_type"] != "/Encoding":
        return "encoding dictionary changed"
    if shape["difference_code"] != 0.0 or shape["difference_name"] != "/0":
        return "encoding is not code zero to glyph /0"
    if shape["char_proc_keys"] != frozenset({"/0"}):
        return "extra glyph appeared"
    if shape["char_proc_stream_keys"] != frozenset({"/Filter"}) or \
            shape["char_proc_filter"] != "/FlateDecode":
        return "glyph stream representation changed"
    expected_program = f"{width:g} 0 0 0 0 0 d1\n".encode("ascii")
    if shape["char_proc_data"] != expected_program:
        return "glyph program paints or differs from the width-only d1 shim"
    if shape["resource_keys"]:
        return "glyph resources are not empty"
    if shape["to_unicode_stream_keys"] != frozenset({"/Filter"}) or \
            shape["to_unicode_filter"] != "/FlateDecode":
        return "ToUnicode stream representation changed"
    if shape["to_unicode_data"] != EXPECTED_SPACE_TOUNICODE:
        return "ToUnicode is not the sole code-zero to U+0020 map"
    return None

def assert_type3_mutant_rejected(shape, label, **changes):
    mutant = dict(shape)
    mutant.update(changes)
    if type3_contract_error(mutant) is None:
        fail(f"Type 3 validator accepted its {label} hostile canary")

def walk(value, where):
    identity = None
    if isinstance(value, IndirectObject):
        identity = (id(value.pdf), value.idnum, value.generation)
        if identity in seen_indirect:
            return
        seen_indirect.add(identity)
        value = value.get_object()
    if isinstance(value, DictionaryObject):
        if str(value.get("/Type")) == "/Font" and str(value.get("/Subtype")) == "/Type3":
            if identity is None:
                fail(f"direct Type 3 font at {where}")
            shape = extract_type3_shape(value, where)
            error = type3_contract_error(shape)
            if error is not None:
                fail(f"Type 3 font at {where}: {error}")
            type3_identities.add(identity)
            type3_shapes.append(shape)
        # DictionaryObject inherits dict.items(); values stay indirect until
        # walk() deliberately resolves them and records their object identity.
        for key, child in value.items():
            key_text = str(key)
            if key_text in forbidden_keys:
                fail(f"reachable forbidden key {key_text} at {where}")
            walk(child, f"{where}/{key_text}")
    elif isinstance(value, ArrayObject):
        for index, child in enumerate(value):
            walk(child, f"{where}[{index}]")

walk(root, "catalog")

if len(type3_identities) != 19 or len(type3_shapes) != 19:
    fail("Type 3 spacing-shim inventory is not exactly 19 fonts")
width_profile = Counter(round(shape["widths"][0], 6) for shape in type3_shapes)
if width_profile != Counter({0.25: 18, 0.602051: 1}):
    fail(f"Type 3 spacing-width profile changed: {dict(width_profile)}")

# Local hostile canaries ensure that the narrow Type 3 exception cannot drift
# into accepting painting programs, non-space mappings, or extra glyphs.
canary_shape = type3_shapes[0]
assert_type3_mutant_rejected(
    canary_shape,
    "painting-program",
    char_proc_data=canary_shape["char_proc_data"] + b"0 0 1 1 re f\n",
)
assert_type3_mutant_rejected(
    canary_shape,
    "non-space-ToUnicode",
    to_unicode_data=canary_shape["to_unicode_data"].replace(b"<0020>", b"<0041>"),
)
assert_type3_mutant_rejected(canary_shape, "extra-glyph", last_char=1.0)

def collect_reachable_type3(value, seen, found):
    if isinstance(value, IndirectObject):
        identity = (id(value.pdf), value.idnum, value.generation)
        if identity in type3_identities:
            found.add(identity)
            return
        if identity in seen:
            return
        seen.add(identity)
        value = value.get_object()
    if isinstance(value, DictionaryObject):
        for child in value.values():
            collect_reachable_type3(child, seen, found)
    elif isinstance(value, ArrayObject):
        for child in value:
            collect_reachable_type3(child, seen, found)

expected_type3_pages = {4: 5, 17: 6, 22: 8}
observed_type3_pages = {}
for page_number, page in enumerate(reader.pages, start=1):
    found = set()
    collect_reachable_type3(page.raw_get("/Resources"), set(), found)
    if found:
        observed_type3_pages[page_number] = len(found)
if observed_type3_pages != expected_type3_pages:
    fail(f"Type 3 spacing shims moved outside the three reviewed figure pages: {observed_type3_pages}")

uri_set = set()
for page_number, page in enumerate(reader.pages, start=1):
    media_box = [float(value) for value in page.mediabox]
    expected = [0.0, 0.0, 595.276, 841.89]
    if any(not math.isclose(got, want, abs_tol=0.002) for got, want in zip(media_box, expected)):
        fail(f"page {page_number} is not zero-origin portrait A4")
    if int(page.get("/Rotate", 0)) != 0:
        fail(f"page {page_number} has nonzero rotation")
    if page.get("/AA") is not None:
        fail(f"page {page_number} contains additional actions")
    annotations = dereference(page.get("/Annots", [])) or []
    for annotation_value in annotations:
        annotation = dereference(annotation_value)
        if not isinstance(annotation, DictionaryObject) or str(annotation.get("/Subtype")) != "/Link":
            fail(f"page {page_number} contains a non-link annotation")
        action = dereference(annotation.get("/A"))
        if not isinstance(action, DictionaryObject):
            fail(f"page {page_number} link has no action dictionary")
        action_type = str(action.get("/S"))
        if action_type == "/GoTo":
            if action.get("/D") is None:
                fail(f"page {page_number} internal link has no destination")
        elif action_type == "/URI":
            uri = str(action.get("/URI", ""))
            parsed = urlparse(uri)
            if parsed.scheme != "https" or not parsed.netloc:
                fail(f"page {page_number} has a non-HTTPS or malformed URI")
            uri_set.add(uri)
        else:
            fail(f"page {page_number} link action is {action_type}")

required_uris = {
    "https://arxiv.org/abs/1004.2515",
    "https://arxiv.org/abs/1404.3146",
    "https://arxiv.org/abs/2311.06373v3",
    "https://arxiv.org/abs/2404.01470",
    "https://arxiv.org/abs/2508.05530",
    "https://doi.org/10.1002/047174882X",
    "https://doi.org/10.1002/rsa.20008",
    "https://doi.org/10.1007/BF00531932",
    "https://doi.org/10.1007/BF01588971",
    "https://doi.org/10.1103/8rzp-w5z1",
    "https://doi.org/10.1103/PhysRevE.100.032305",
    "https://doi.org/10.1103/PhysRevE.103.032149",
    "https://doi.org/10.1103/PhysRevE.110.014115",
    "https://doi.org/10.1103/PhysRevE.69.066138",
    "https://doi.org/10.1103/PhysRevE.87.012130",
    "https://doi.org/10.1109/ISIT.2014.6875230",
    "https://doi.org/10.1109/TRA.2004.824698",
    "https://doi.org/10.1109/TSP.2008.2007095",
    "https://doi.org/10.1137/21M1466542",
    "https://doi.org/10.1162/089976603321780272",
    "https://doi.org/10.1515/9781400881970-018",
    "https://doi.org/10.3390/drones6110317",
    "https://doi.org/10.3390/e16042161",
    "https://epubs.siam.org/doi/abs/10.1137/21M1466542",
    "https://github.com/sepahead/crebain/blob/6ef60fabbf8c8a8008e7a77304d3e095b6b9e91d/src-tauri/tests/fixtures/crebain_drone_mgw_v1.json",
    "https://github.com/sepahead/galadriel/blob/466986416a711d2868b94dc26710e03e1761a57b/crates/galadriel-justify/src/crebain_mgw.rs",
    "https://github.com/sepahead/galadriel/blob/466986416a711d2868b94dc26710e03e1761a57b/crates/galadriel-justify/src/lib.rs",
    "https://github.com/sepahead/galadriel/blob/466986416a711d2868b94dc26710e03e1761a57b/crates/galadriel-justify/src/main.rs",
    "https://github.com/sepahead/galadriel/blob/466986416a711d2868b94dc26710e03e1761a57b/docs/CREBAIN-DRONE-MGW-STUDY.md",
    "https://github.com/sepahead/galadriel/blob/466986416a711d2868b94dc26710e03e1761a57b/docs/EVALUATION.md",
    "https://motion.me.ucsb.edu/pdf/2002j-cmkb.pdf",
    "https://openaccess.thecvf.com/content/ICCV2023/html/Jiang_Optimizing_the_Placement_of_Roadside_LiDARs_for_Autonomous_Driving_ICCV_2023_paper.html",
    "https://proceedings.mlr.press/v119/sundararajan20a.html",
    "https://www.mdpi.com/2504-446X/6/11/317",
    "https://proceedings.mlr.press/v258/westphal25a.html",
    "https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2003/HPL-2003-97R1.pdf",
    "https://web.stanford.edu/~boyd/papers/sensor_selection.html",
    "https://www.jmlr.org/papers/v24/21-0482.html",
    "https://www.jmlr.org/papers/v9/krause08a.html",
    "https://www.jmlr.org/papers/v9/krause08b.html",
}
missing = required_uris - uri_set
if missing:
    fail(f"required primary-source URI set is incomplete: {sorted(missing)}")
unexpected = uri_set - required_uris
if unexpected:
    fail(f"undeclared external URI set is nonempty: {sorted(unexpected)}")
for stale in ("21M1466499", "2207.01927"):
    if any(stale in uri for uri in uri_set):
        fail(f"stale source URI remains: {stale}")

for page in reader.pages:
    page.get_contents()
print(
    f"object-check=GO pages={len(reader.pages)} "
    f"links={sum(1 for page in reader.pages for _ in (dereference(page.get('/Annots', [])) or []))} "
    f"unique_https={len(uri_set)} type3_space_shims={len(type3_identities)}"
)
PY
}

validate_pdf "$PDF" canonical
validate_pdf "$rebuilt" rebuilt

relation="raw-byte-identical"
if ! cmp --silent "$PDF" "$rebuilt"; then
  if [[ "$MODE" == "--exact" ]]; then
    echo "$CHECK_NAME failed: canonical and same-toolchain rebuilt PDF bytes differ" >&2
    exit 1
  fi
  canonical_text="$tmp_root/canonical-cross.txt"
  rebuilt_text="$tmp_root/rebuilt-cross.txt"
  LC_ALL=C pdftotext -layout "$PDF" "$canonical_text"
  LC_ALL=C pdftotext -layout "$rebuilt" "$rebuilt_text"
  cmp --silent "$canonical_text" "$rebuilt_text" || {
    echo "$CHECK_NAME failed: cross-toolchain extracted text differs" >&2
    exit 1
  }
  relation="exact-layout-text-and-reviewed-page-geometry"
fi

render_dir="$tmp_root/rendered"
mkdir -p "$render_dir"
LC_ALL=C pdftoppm -r 110 -png "$PDF" "$render_dir/page" >/dev/null 2>"$tmp_root/render.stderr"
[[ ! -s "$tmp_root/render.stderr" ]] || {
  cat "$tmp_root/render.stderr" >&2
  echo "$CHECK_NAME failed: renderer emitted diagnostics" >&2
  exit 1
}
render_count="$(find "$render_dir" -type f -name 'page-*.png' | awk 'END {print NR + 0}')"
[[ "$render_count" -eq 47 ]] || {
  echo "$CHECK_NAME failed: rendered page count is $render_count, expected 47" >&2
  exit 1
}
find "$render_dir" -type f -name 'page-*.png' -size 0 -print -quit | grep -q . && {
  echo "$CHECK_NAME failed: a rendered page is empty" >&2
  exit 1
}

printf 'OK: %s mode=%s relation=%s sha256=%s pages=47 rendered=47\n' \
  "$PDF" "$MODE" "$relation" "$(shasum -a 256 "$PDF" | awk '{print $1}')"
