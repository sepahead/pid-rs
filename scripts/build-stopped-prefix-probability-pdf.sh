#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SOURCE_RELATIVE="audit/formal/lean-stopped-prefix-probability/EXPOSITION.md"
SOURCE="$ROOT/$SOURCE_RELATIVE"
FIGURE_RELATIVE="audit/formal/lean-stopped-prefix-probability/figures/first-hit-and-prefix-return.svg"
FIGURE="$ROOT/$FIGURE_RELATIVE"
LATEX_DIR="$ROOT/audit/formal/latex/stopped-prefix-probability"
FONT_MANIFEST="$LATEX_DIR/figure-fonts.json"
TAGPDF_OPENACTION_COMPAT="$ROOT/audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
STYLE_DIR="$ROOT/audit/formal/latex"
DEFAULT_OUTPUT="$ROOT/output/pdf/stopped-prefix-probability.pdf"
OUTPUT="$DEFAULT_OUTPUT"
JOB="stopped-prefix-probability"

# Freeze renderer timestamps and PDF identifiers for same-source reproducibility. The date is the
# publication date at 00:00 UTC; callers may override it only through SOURCE_DATE_EPOCH.
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1790467200}"
export FORCE_SOURCE_DATE=1
export TZ=UTC
export LC_ALL=C

if [[ $# -eq 2 && "$1" == "--output" ]]; then
  OUTPUT="$2"
elif [[ $# -ne 0 ]]; then
  echo "usage: $0 [--output ABSOLUTE_PDF_PATH]" >&2
  exit 2
fi

[[ "$OUTPUT" == /* && "$OUTPUT" == *.pdf ]] || {
  echo "Stopped-prefix probability PDF build failed: output must be an absolute .pdf path" >&2
  exit 1
}
OUTPUT_DIR="$(dirname "$OUTPUT")"
[[ -d "$OUTPUT_DIR" && ! -L "$OUTPUT_DIR" && "$OUTPUT_DIR" != "/" ]] || {
  echo "Stopped-prefix probability PDF build failed: output directory is unsafe or absent" >&2
  exit 1
}
[[ ! -e "$OUTPUT" || ( -f "$OUTPUT" && ! -L "$OUTPUT" ) ]] || {
  echo "Stopped-prefix probability PDF build failed: output is not a regular nonsymbolic file" >&2
  exit 1
}

for command_name in awk basename cp dirname mktemp mv pandoc pdfinfo pdffonts pdftotext \
    python3 rm shasum lualatex rsvg-convert kpsewhich; do
  command -v "$command_name" >/dev/null 2>&1 || {
    echo "Stopped-prefix probability PDF build failed: missing command: $command_name" >&2
    exit 1
  }
done

[[ -f "$SOURCE" && ! -L "$SOURCE" && -f "$FIGURE" && ! -L "$FIGURE" ]] || {
  echo "Stopped-prefix probability PDF build failed: canonical Markdown is absent or symbolic" >&2
  exit 1
}
[[ -f "$FONT_MANIFEST" && ! -L "$FONT_MANIFEST" \
    && -f "$LATEX_DIR/publication.tex" && ! -L "$LATEX_DIR/publication.tex" \
    && -f "$LATEX_DIR/filter.lua" && ! -L "$LATEX_DIR/filter.lua" \
    && -f "$STYLE_DIR/pid-rs-report-tables.sty" && ! -L "$STYLE_DIR/pid-rs-report-tables.sty" \
    && -f "$STYLE_DIR/pid-rs-workflow-publication.sty" \
    && ! -L "$STYLE_DIR/pid-rs-workflow-publication.sty" \
    && -f "$TAGPDF_OPENACTION_COMPAT" && ! -L "$TAGPDF_OPENACTION_COMPAT" ]] || {
  echo "Stopped-prefix probability PDF build failed: projection source is incomplete" >&2
  exit 1
}

work_root="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-stopped-prefix-probability-pdf.XXXXXX")"
cleanup() {
  rm -rf -- "$work_root"
}
trap cleanup EXIT

raw_tex="$work_root/raw.tex"
tagged_tex="$work_root/tagged.tex"
source_digest_record="$work_root/source-digests.txt"

# Bind the duplicated 16-byte trailer ID to the canonical Markdown and projection sources.
# LuaTeX otherwise generates a new ID for each build even when SOURCE_DATE_EPOCH is fixed.
(
  cd "$ROOT"
  shasum -a 256 \
    "$SOURCE_RELATIVE" \
    "$FIGURE_RELATIVE" \
    "audit/formal/latex/stopped-prefix-probability/figure-fonts.json" \
    "audit/formal/latex/stopped-prefix-probability/publication.tex" \
    "audit/formal/latex/stopped-prefix-probability/filter.lua" \
    "audit/formal/latex/pid-rs-report-tables.sty" \
    "audit/formal/latex/pid-rs-workflow-publication.sty" \
    "audit/formal/latex/mathematical-results-guide/tagpdf-openaction-compat.tex"
) >"$source_digest_record"
trailer_id="$(shasum -a 256 "$source_digest_record" | awk '{print toupper(substr($1, 1, 32))}')"
[[ "$trailer_id" =~ ^[0-9A-F]{32}$ ]] || {
  echo "Stopped-prefix probability PDF build failed: source-derived trailer ID is malformed" >&2
  exit 1
}

python3 -I -B - "$FONT_MANIFEST" "$work_root" "$FIGURE" <<'PYFIGURE'
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from xml.sax.saxutils import escape

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

manifest_path, work, figure = map(Path, sys.argv[1:])
manifest, manifest_bytes = read_font_manifest(manifest_path)
private = work / "figure-fonts"
private.mkdir(mode=0o700)
for name in ("fonts", "font-cache", "home", "xdg-config", "xdg-cache", "empty-config", "tmp"):
    (private / name).mkdir(mode=0o700)
configuration = manifest["fontconfig_template"].format(
    font_directory=escape(str(private / "fonts")),
    cache_directory=escape(str(private / "font-cache")),
).encode("utf-8")
config_path = private / "fonts.conf"
config_path.write_bytes(configuration)
config_path.chmod(0o400)
# A fresh explicit environment keeps CoreText, user includes and inherited sysroots out.
environment = {
    "PATH": os.environ.get("PATH", os.defpath),
    "HOME": str(private / "home"),
    "XDG_CONFIG_HOME": str(private / "xdg-config"),
    "XDG_CACHE_HOME": str(private / "xdg-cache"),
    "TMPDIR": str(private / "tmp"),
    "FONTCONFIG_FILE": str(config_path),
    "FONTCONFIG_PATH": str(private / "empty-config"),
    "FONTCONFIG_USE_MMAP": "0",
    "PANGOCAIRO_BACKEND": "fc",
    "SOURCE_DATE_EPOCH": os.environ["SOURCE_DATE_EPOCH"],
    "TZ": "UTC", "LANG": "C", "LC_ALL": "C",
}
lookup = shutil.which("kpsewhich")
converter = shutil.which("rsvg-convert")
font_inspector = shutil.which("pdffonts")
if not all((lookup, converter, font_inspector)):
    font_fail("font lookup, renderer or font inspector is absent")
input_records = []
for font in manifest["fonts"]:
    found = subprocess.run(
        [lookup, "--must-exist", font["filename"]], env=environment,
        capture_output=True, text=True, timeout=30, check=True,
    )
    lines = found.stdout.splitlines()
    if len(lines) != 1 or not Path(lines[0]).is_absolute():
        font_fail(f"font lookup is not one absolute path: {font['filename']}")
    source = Path(lines[0])
    with os.fdopen(os.open(source, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > 4 * 1024 * 1024:
            font_fail(f"font is not a bounded regular file: {font['filename']}")
        data = stream.read(4 * 1024 * 1024 + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    if identity(before) != identity(after) or len(data) != before.st_size:
        font_fail(f"font changed during capture: {font['filename']}")
    digest = hashlib.sha256(data).hexdigest()
    if digest != font["sha256"]:
        font_fail(f"font digest mismatch: {font['filename']}")
    target = private / "fonts" / font["filename"]
    target.write_bytes(data)
    target.chmod(0o400)
    input_records.append({
        "filename": font["filename"], "source": str(source.resolve()),
        "captured": str(target), "bytes": len(data), "sha256": digest,
        "postscript_name": font["postscript_name"],
    })
figure_pdf = work / "first-hit-and-prefix-return.pdf"
subprocess.run(
    [converter, "-f", "pdf", "-o", str(figure_pdf), str(figure)],
    env=environment, timeout=120, check=True,
)
observed = subprocess.run(
    [font_inspector, str(figure_pdf)], env=environment,
    capture_output=True, text=True, timeout=30, check=True,
)
font_rows = []
for line in observed.stdout.splitlines()[2:]:
    fields = line.split()
    if len(fields) < 8 or not all(x.isdigit() for x in fields[-2:]):
        font_fail("figure font inventory is malformed")
    name = re.sub(r"^[A-Z]{6}\+", "", fields[0])
    font_type = " ".join(fields[1:-6])
    if fields[-5] != "yes" or font_type not in {"Type 1C", "CID Type 0C"}:
        font_fail(f"figure contains a nonembedded or unexpected font type: {line}")
    font_rows.append({"postscript_name": name, "type": font_type,
                      "embedded": fields[-5], "subset": fields[-4], "unicode": fields[-3]})
if {row["postscript_name"] for row in font_rows} != {f["postscript_name"] for f in manifest["fonts"]}:
    font_fail("figure font inventory differs from the four declared fonts")
if config_path.read_bytes() != configuration or manifest_path.read_bytes() != manifest_bytes:
    font_fail("manifest or private font configuration changed during rendering")
for record in input_records:
    if hashlib.sha256(Path(record["captured"]).read_bytes()).hexdigest() != record["sha256"]:
        font_fail("captured font changed during rendering")
print(json.dumps({
    "schema": "pid-rs-stopped-prefix-figure-font-receipt-v1",
    "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
    "font_inputs": input_records,
    "fontconfig_utf8": configuration.decode("utf-8"),
    "fontconfig_sha256": hashlib.sha256(configuration).hexdigest(),
    "renderer_environment": environment,
    "figure_pdf_sha256": hashlib.sha256(figure_pdf.read_bytes()).hexdigest(),
    "observed_figure_fonts": font_rows,
    "scope": "captured figure inputs and observed fonts; temporary paths are removed at build exit; no body-font or cross-toolchain guarantee",
}, sort_keys=True), flush=True)
PYFIGURE

(
  cd "$(dirname "$SOURCE")"
  PID_STOPPED_PREFIX_FIGURE_PDF="$work_root/first-hit-and-prefix-return.pdf" pandoc "$(basename "$SOURCE")" \
    --from=gfm+tex_math_dollars --to=latex --wrap=none --syntax-highlighting=none \
    --lua-filter="$LATEX_DIR/filter.lua" --output="$work_root/body.tex"
)
[[ -s "$work_root/body.tex" && ! -L "$work_root/body.tex" ]] || {
  echo "PDF build failed: Pandoc did not produce the body" >&2
  exit 1
}
cp "$LATEX_DIR/publication.tex" "$raw_tex"
cp "$TAGPDF_OPENACTION_COMPAT" "$work_root/tagpdf-openaction-compat.tex"

[[ -s "$raw_tex" && ! -L "$raw_tex" ]] || {
  echo "Stopped-prefix probability PDF build failed: Pandoc did not produce TeX" >&2
  exit 1
}

awk -v trailer_id="$trailer_id" 'BEGIN {
  print "\\DocumentMetadata{testphase=phase-II,lang=en-US}"
}
{
  print
  if ($0 == "\\begin{document}") {
    print "\\pdfvariable trailerid {[ <" trailer_id "> <" trailer_id "> ]}"
    inserted += 1
  }
}
END {
  if (inserted != 1) exit 42
}' \
  "$raw_tex" >"$tagged_tex"

for pass in 1 2 3; do
  if ! (cd "$work_root" && TEXINPUTS="$STYLE_DIR:" lualatex --interaction=nonstopmode \
      --halt-on-error --file-line-error --jobname="$JOB" --output-directory="$work_root" \
      "$tagged_tex" >"$work_root/pass-$pass.log" 2>&1); then
    cat "$work_root/pass-$pass.log" >&2
    echo "Stopped-prefix probability PDF build failed: LuaLaTeX pass $pass failed" >&2
    exit 1
  fi
done

built="$work_root/$JOB.pdf"
log="$work_root/$JOB.log"
[[ -s "$built" && -s "$log" ]] || {
  echo "Stopped-prefix probability PDF build failed: compiled PDF or log is absent" >&2
  exit 1
}

if grep -En 'Overfull \\[hv]box|Undefined control sequence|Missing character:' "$log" >&2; then
  echo "Stopped-prefix probability PDF build failed: layout or glyph error" >&2
  exit 1
fi

python3 -I -B - "$built" <<'PY'
import pathlib
import sys
from pypdf import PdfReader

path = pathlib.Path(sys.argv[1])
reader = PdfReader(path, strict=True)
if not reader.pages:
    raise SystemExit("compiled PDF has no pages")
for page in reader.pages:
    page.get_contents()
PY
page_count="$(pdfinfo "$built" | awk '/^Pages:/ {print $2}')"
[[ "$page_count" =~ ^[1-9][0-9]*$ ]] || {
  echo "Stopped-prefix probability PDF build failed: invalid page count" >&2
  exit 1
}
pdftotext "$built" "$work_root/extracted.txt"
LC_ALL=C tr '\f\n\r\t' '    ' <"$work_root/extracted.txt" | LC_ALL=C tr -s ' ' \
  >"$work_root/normalized.txt"
for sentinel in \
    'PID-RS TECHNICAL REPORT SERIES' \
    'Finite rows and their actual probability law' \
    'an unnormalized first-hit factorization' \
    'mass and endpoint cases' \
    'Rust implementation and computational cost' \
    'The unfinished stopping argument'; do
  grep -Fq "$sentinel" "$work_root/normalized.txt" || {
    echo "Stopped-prefix probability PDF build failed: missing text sentinel: $sentinel" >&2
    exit 1
  }
done

font_rows="$(pdffonts "$built" | awk 'NR > 2 {count += 1} END {print count + 0}')"
[[ "$font_rows" -gt 0 ]] || {
  echo "Stopped-prefix probability PDF build failed: no embedded font rows" >&2
  exit 1
}
if pdffonts "$built" | awk 'NR > 2 && $(NF-4) != "yes" {exit 1}'; then
  :
else
  pdffonts "$built" >&2
  echo "Stopped-prefix probability PDF build failed: a font is not embedded" >&2
  exit 1
fi

candidate="$(mktemp "$OUTPUT_DIR/.stopped-prefix-probability.XXXXXX.pdf")"
trap 'rm -f -- "$candidate"; cleanup' EXIT
cp "$built" "$candidate"
mv "$candidate" "$OUTPUT"
trap cleanup EXIT
printf 'OK: built %s pages=%s sha256=%s\n' \
  "$OUTPUT" "$page_count" "$(shasum -a 256 "$OUTPUT" | awk '{print $1}')"
