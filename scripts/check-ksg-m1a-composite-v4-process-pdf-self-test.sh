#!/usr/bin/env bash
set -euo pipefail
# Focused binding controls; the complete v4 publication gate is a separate run.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
GATE="scripts/check-ksg-m1a-composite-v4-process-pdf.sh"
if [[ "$#" -ne 0 ]]; then
  echo "usage: $0" >&2
  exit 2
fi
TEST_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/pid-rs-v4-authorship-controls.XXXXXX")"
trap 'rm -rf -- "$TEST_ROOT"' EXIT
run_controls() {
  local control_mode="$1"
  shift
  python3 "$@" -I -S - "$ROOT" "$GATE" "$TEST_ROOT/$control_mode" <<'PY_AUTHORSHIP_CONTROLS'
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
rendering=source.split('# BEGIN CURRENT AUTHORSHIP RENDERING\n',1)[1].split('# END CURRENT AUTHORSHIP RENDERING',1)[0]
guard='if [[ "$MODE" == "--exact" ]]; then'
if rendering.count(guard)!=1:
    raise SystemExit('authorship current-render mode guard is absent or ambiguous')
def mode_boundary(block,label):
    for mode in ('--exact','--cross-toolchain'):
        directory=test_root/('mode-'+label+mode);directory.mkdir(parents=True)
        prelude='''set -eu
MODE="$1"; BUILD_DIR="$2"; RENDER_DPI=120; COMMITTED=fixture.pdf
env() { printf 'fixture-render-boundary-reached\\n' >&2; return 17; }
'''
        result=subprocess.run(['bash','-c',prelude+block,'authorship-mode-control',mode,str(directory)],text=True,capture_output=True,timeout=10)
        if mode=='--exact':
            if result.returncode!=1 or 'fixture-render-boundary-reached' not in result.stderr or 'current authorship rendering failed' not in result.stderr:
                return False
        elif result.returncode!=0 or result.stdout or result.stderr or list(directory.iterdir()):
            return False
    return True
if not mode_boundary(rendering,'baseline'):
    raise SystemExit('authorship current-render exact/cross boundary failed')
for label,mutant in (('unconditional',rendering.replace(guard,'if true; then',1)),('inverted',rendering.replace(guard,'if [[ "$MODE" == "--cross-toolchain" ]]; then',1))):
    if mode_boundary(mutant,label):
        raise SystemExit('authorship mode-boundary hostile accepted: '+label)
print('OK: actual current-render block dispatch and two causal mode-boundary controls')
relative=re.search(r'^AUTHORSHIP_DIR="([^"]+)"$',source,re.M).group(1)
sha=re.search(r'^EXPECTED_AUTHORSHIP_SHA256="([0-9a-f]{64})"$',source,re.M).group(1)
pages=int(re.search(r'^EXPECTED_REPORT_PAGES=(\d+)$',source,re.M).group(1))
body=source.split('# BEGIN AUTHORSHIP SUCCESSOR\n',1)[1].split("<<'PY_AUTHORSHIP'\n",1)[1].split('\nPY_AUTHORSHIP\n',1)[0]
original=json.loads((root/relative/'SUCCESSOR.json').read_text())
version=original['version']; stem=f'ksg-m1a-composite-v{version}-process'
tex=f'audit/formal/latex/{stem}.tex'; render=f'output/pdf/{stem}.rendering-receipt.tsv'

def invoke(directory,expected_sha):
    command=[sys.executable]+(['-O'] if sys.flags.optimize else [])+['-I','-S','-',str(directory),relative,expected_sha,str(pages)]
    return subprocess.run(command,input=body,text=True,capture_output=True,timeout=45)

baseline=invoke(root,sha)
if baseline.returncode:
    raise SystemExit('authorship control baseline failed: '+baseline.stdout+baseline.stderr)

cases=(('record-digest','record digest differs'),('missing-preimage','bound path is absent or nonregular'),('float-pages','typed identity differs'),('float-bytes','typed bound bytes differ'),('extra-source','source changed beyond one author substitution'),('transferred-review','visual review scope differs'),('changed-body-render','non-title render row differs'),('wrong-title-image','actual first-page image binding differs'),('missing-record-path','file inventory differs'),('false-historical-render','previous rendering observation provenance differs'))
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
    elif name=='false-historical-render': record['previous_rendering_origin']='Historical rendering observation from August 2026.'
    elif name=='missing-record-path': del record['files'][relative+'/previous.pdf.bin']
    raw=(json.dumps(record,indent=2,sort_keys=True)+'\n').encode()
    if name=='record-digest': raw+=b' '
    (directory/relative/'SUCCESSOR.json').write_bytes(raw)
    expected_sha=sha if name=='record-digest' else hashlib.sha256(raw).hexdigest()
    result=invoke(directory,expected_sha)
    if result.returncode==0 or expected not in result.stdout+result.stderr:
        raise SystemExit('authorship hostile accepted or noncausal: '+name+'\n'+result.stdout+result.stderr)
print(f'OK: v{version} authorship baseline and ten causal successor controls; optimized={bool(sys.flags.optimize)}')
PY_AUTHORSHIP_CONTROLS
}
run_controls normal
run_controls optimized -O
