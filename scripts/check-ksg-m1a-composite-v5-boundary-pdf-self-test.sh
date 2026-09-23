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
  'source changed beyond one author substitution'
  'historical_review_applies_to_current_pdf'
  'non-title render row differs'
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
  mkdir -p "$destination/audit/evidence/ksg-publication-authorship-2026-09-23/v5"
  cp "$ROOT/audit/evidence/ksg-publication-authorship-2026-09-23/v5/"* "$destination/audit/evidence/ksg-publication-authorship-2026-09-23/v5/"
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

# BEGIN AUTHORSHIP SUCCESSOR CONTROLS
python3 -I -S - "$ROOT" "$GATE" "$TEST_ROOT" <<'PY_AUTHORSHIP_CONTROLS'
from pathlib import Path
import copy
import hashlib
import json
import re
import shutil
import subprocess
import sys

root=Path(sys.argv[1]); gate=Path(sys.argv[2]); test_root=Path(sys.argv[3])
source=(root/gate).read_text()
relative=re.search(r'^AUTHORSHIP_DIR="([^"]+)"$',source,re.M).group(1)
sha=re.search(r'^EXPECTED_AUTHORSHIP_SHA256="([0-9a-f]{64})"$',source,re.M).group(1)
pages=int(re.search(r'^EXPECTED_PAGES=(\d+)$',source,re.M).group(1))
body=source.split('# BEGIN AUTHORSHIP SUCCESSOR\n',1)[1].split("<<'PY_AUTHORSHIP'\n",1)[1].split('\nPY_AUTHORSHIP\n',1)[0]
original=json.loads((root/relative/'SUCCESSOR.json').read_text())
version=original['version']; stem=f'ksg-m1a-composite-v{version}-boundary'
tex=f'audit/formal/latex/{stem}.tex'; render=f'output/pdf/{stem}.rendering-receipt.tsv'

def invoke(directory,expected_sha):
    command=[sys.executable]+(['-O'] if sys.flags.optimize else [])+['-I','-S','-',str(directory),relative,expected_sha,str(pages)]
    return subprocess.run(command,input=body,text=True,capture_output=True,timeout=45)

baseline=invoke(root,sha)
if baseline.returncode:
    raise SystemExit('authorship control baseline failed: '+baseline.stdout+baseline.stderr)

cases=(('record-digest','record digest differs'),('missing-preimage','bound path is absent or nonregular'),('float-pages','typed identity differs'),('float-bytes','typed bound bytes differ'),('extra-source','source changed beyond one author substitution'),('transferred-review','visual review scope differs'),('changed-body-render','non-title render row differs'),('wrong-title-image','actual first-page image binding differs'),('missing-record-path','file inventory differs'))
for name,expected in cases:
    directory=test_root/('authorship-'+name);directory.mkdir(parents=True)
    record=copy.deepcopy(original)
    for path in [*record['files'],relative+'/SUCCESSOR.json']:
        target=directory/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/path,target)
    def rebind(path):
        data=(directory/path).read_bytes();record['files'][path]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    if name=='missing-preimage': (directory/relative/'previous.pdf.bin').unlink()
    elif name=='float-pages': record['pages']=float(pages)
    elif name=='float-bytes': record['files'][tex]['bytes']=float(record['files'][tex]['bytes'])
    elif name=='extra-source':
        with (directory/tex).open('ab') as out: out.write(b'\n% fixture-only unauthorized source change\n')
        rebind(tex)
    elif name=='transferred-review': record['visual_review']['historical_review_applies_to_current_pdf']=True
    elif name=='changed-body-render':
        rows=(directory/render).read_text().splitlines();fields=rows[6].split('\t');fields[-1]=str(int(fields[-1])+1);rows[6]='\t'.join(fields)
        (directory/render).write_text('\n'.join(rows)+'\n');rebind(render)
    elif name=='wrong-title-image':
        path=relative+'/first-page-color-120dpi.png';shutil.copyfile(directory/relative/'first-page-gray-120dpi.png',directory/path);rebind(path)
    elif name=='missing-record-path': del record['files'][relative+'/previous.pdf.bin']
    raw=(json.dumps(record,indent=2,sort_keys=True)+'\n').encode()
    if name=='record-digest': raw+=b' '
    (directory/relative/'SUCCESSOR.json').write_bytes(raw)
    expected_sha=sha if name=='record-digest' else hashlib.sha256(raw).hexdigest()
    result=invoke(directory,expected_sha)
    if result.returncode==0 or expected not in result.stdout+result.stderr:
        raise SystemExit('authorship hostile accepted or noncausal: '+name+'\n'+result.stdout+result.stderr)
print(f'OK: v{version} authorship baseline and nine causal successor controls; optimized={bool(sys.flags.optimize)}')
PY_AUTHORSHIP_CONTROLS
# END AUTHORSHIP SUCCESSOR CONTROLS

if [[ "$MODE" == "--exact" ]]; then
  echo "OK: composite-v5 boundary PDF exact/cross positives and three external hostile fixtures plus nine authorship successor controls passed"
else
  echo "OK: composite-v5 boundary PDF cross-toolchain positive and three external hostile fixtures plus nine authorship successor controls passed"
fi
