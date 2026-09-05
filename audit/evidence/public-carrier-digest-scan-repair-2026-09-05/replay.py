#!/usr/bin/env python3
"""Replay the retained public carrier fixtures with an explicit reviewed scanner."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gitleaks', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--decisive', action='store_true')
    mode.add_argument('--inline', action='store_true')
    args = parser.parse_args()
    tool = args.gitleaks.resolve(strict=True)
    version = subprocess.run([str(tool), 'version'], capture_output=True, timeout=10)
    if version.returncode or version.stdout.strip() != b'8.30.1' or version.stderr:
        raise SystemExit('Gitleaks 8.30.1 is required')
    digest = hashlib.sha256((ROOT / 'carrier-preimage.json').read_bytes()).hexdigest()
    base = '"carrier_keys_sha256": "' + digest + '"'
    with tempfile.TemporaryDirectory(prefix='pid-carrier-evidence-') as temporary:
        temp = Path(temporary)
        if args.inline:
            source = (ROOT / 'ci-inline.py').read_text()
            old = '"/tmp/gitleaks"'
            if source.count(old) != 1:
                raise SystemExit('archived scanner invocation changed')
            adapted = source.replace(old, repr(str(tool)))
            (temp / '.gitleaks.toml').write_bytes((ROOT / 'candidate.gitleaks.toml').read_bytes())
            (temp / '.gitleaksignore').write_bytes((ROOT / 'historical-prose-fingerprints.txt').read_bytes())
            command = [sys.executable, '-I', '-S', '-B']
            if sys.flags.optimize:
                command.append('-O')
            command += ['-c', adapted]
            result = subprocess.run(command, cwd=temp, timeout=120)
            return result.returncode
        cases = json.loads((ROOT / 'rejected-v1-cases.json').read_bytes())['cases']
        names = {'baseline': 'baseline.gitleaks.toml', 'rejected_v1': 'rejected-v1.gitleaks.toml',
                 'accepted': 'candidate.gitleaks.toml'}
        results = []
        for case in cases:
            if case['context_recipe'] == 'json':
                raw = ('{\n  ' + base + ',\n  "description": "public carrier evidence"\n}\n').encode()
            elif case['context_recipe'] == 'python':
                raw = ('EXPECTED_DIGESTS: dict[str, str] = {\n    ' + base + ',\n    "other": "public"\n}\n').encode()
            else:
                raise SystemExit('unknown decisive context')
            if len(raw) != case['source_bytes'] or hashlib.sha256(raw).hexdigest() != case['source_sha256']:
                raise SystemExit('decisive source bytes differ')
            directory = temp / case['name']
            destination = directory / case['path']
            destination.parent.mkdir(parents=True)
            destination.write_bytes(raw)
            for policy, config in names.items():
                report = temp / (case['name'] + '-' + policy + '.json')
                command = [str(tool), 'dir', '.', '--config', str(ROOT / config),
                           '--gitleaks-ignore-path', '/dev/null', '--redact', '--no-banner',
                           '--report-format', 'json', '--report-path', str(report)]
                actual = subprocess.run(command, cwd=directory, capture_output=True, timeout=30)
                observed = json.loads(report.read_bytes()) if report.exists() else []
                expected = case['outcomes'][policy]
                fields = ('RuleID', 'StartLine', 'EndLine', 'StartColumn', 'EndColumn', 'File')
                project = lambda rows: sorted(tuple(row[key] for key in fields) for row in rows)
                if (actual.returncode != expected['exit_code'] or len(observed) != expected['finding_count']
                        or project(observed) != project(expected['findings'])):
                    raise SystemExit('decisive outcome differs: ' + case['name'] + '/' + policy)
                results.append({'case': case['name'], 'policy': policy, 'status': 'matched_recorded_outcome'})
        print(json.dumps({'status': 'pass', 'comparisons': len(results), 'results': results}, sort_keys=True))
        return 0


if __name__ == '__main__':
    raise SystemExit(main())
