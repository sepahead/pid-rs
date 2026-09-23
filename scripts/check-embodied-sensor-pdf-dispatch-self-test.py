#!/usr/bin/env python3
"""Exercise the aggregate's bias/derivative/sensor prefix with inert call-recording substitutes.

No publication builder, PDF parser, renderer, or prover runs.
All registration guards, the inventory return, and all twelve early calls run as one
source slice. Controls check preflight before any call, argument and original endpoint
forwarding, mode separation, and failure propagation.
"""
from pathlib import Path
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
FIELDS = (
    'PYTHON', 'MANIFEST_SHA256',
    'CONTROL_NORMAL_REGISTRATION', 'CONTROL_NORMAL_REGISTRATION_SHA256', 'CONTROL_NORMAL_OUTPUT',
    'CONTROL_OPTIMIZED_REGISTRATION', 'CONTROL_OPTIMIZED_REGISTRATION_SHA256', 'CONTROL_OPTIMIZED_OUTPUT',
    'CONTROL_MONOTONIC_DEADLINE',
    'FULL_REGISTRATION', 'FULL_REGISTRATION_SHA256', 'FULL_WORK_DIR',
    'OVERVIEW_REGISTRATION', 'OVERVIEW_REGISTRATION_SHA256', 'OVERVIEW_WORK_DIR',
    'PRODUCTION_MONOTONIC_DEADLINE',
)
BIAS_DIAGNOSTICS = {
    'PYTHON': 'exact bias work requires its pinned Python selector',
    'CONTROL_NORMAL_REGISTRATION': 'normal bias-control registration is required',
    'CONTROL_NORMAL_REGISTRATION_SHA256': 'normal bias-control registration hash is required',
    'CONTROL_NORMAL_OUTPUT': 'normal bias-control output is required',
    'CONTROL_OPTIMIZED_REGISTRATION': 'optimized bias-control registration is required',
    'CONTROL_OPTIMIZED_REGISTRATION_SHA256': 'optimized bias-control registration hash is required',
    'CONTROL_OPTIMIZED_OUTPUT': 'optimized bias-control output is required',
    'FULL_REGISTRATION': 'full bias registration is required',
    'FULL_REGISTRATION_SHA256': 'full bias registration hash is required',
    'FULL_WORK_DIR': 'full bias work directory is required',
    'SUMMARY_REGISTRATION': 'summary bias registration is required',
    'SUMMARY_REGISTRATION_SHA256': 'summary bias registration hash is required',
    'SUMMARY_WORK_DIR': 'summary bias work directory is required',
}


def need(ok, why):
    if not ok:
        raise RuntimeError(why)


def block(source, label):
    start = '# BEGIN EMBODIED SENSOR ' + label + '\n'
    end = '# END EMBODIED SENSOR ' + label + '\n'
    need(source.count(start) == source.count(end) == 1, 'dispatch markers differ')
    left = source.index(start)
    right = source.index(end, left) + len(end)
    return source[left:right], left, right


def main():
    source = (ROOT / 'scripts/check-formal-pdf-set.sh').read_text()
    preflight, preflight_begin, preflight_end = block(source, 'PREFLIGHT')
    exact, begin, finish = block(source, 'EXACT DISPATCH')
    cross, cross_begin, _ = block(source, 'CROSS REFUSAL')
    bias_bindings = source.index(
        '# Exact bias controls and reproduction consume actual pre-reviewed external registrations.\n')
    inventory = source.index('if [[ "$MODE" == "--inventory-only" ]]; then')
    bias_calls = source.index(
        '# Keep the finite registration clocks causal: run fresh inert bias controls and both exact bias\n')
    first_long = source.index('python3 -I -B scripts/check-publication-links.py')
    need(preflight_begin < preflight_end < bias_bindings < inventory < bias_calls
         < begin < finish < first_long < cross_begin,
         'all binding guards must precede bias, derivative, and sensor work')
    derivative_start = source.index('# BEGIN DERIVATIVE PREFLIGHT\n')
    derivative_finish = source.index('# END DERIVATIVE EXACT DISPATCH\n') + len('# END DERIVATIVE EXACT DISPATCH\n')
    need(preflight_end < derivative_start < derivative_finish < begin,
         'sensor guards must precede all existing work; sensor dispatch follows it')
    need(source.count('scripts/build-mgw-derivative-notes-pdf.py') == 3
         and source.count('scripts/check-mgw-derivative-notes-pdf-self-test.py') == 2,
         'existing derivative call inventory changed')
    prefix = source[preflight_begin:finish]
    need(source.count('scripts/build-embodied-sensor-pdfs.py') == 3,
         'unexpected sensor production call outside the reviewed blocks')
    need(source.count('scripts/check-embodied-sensor-pdfs-self-test.py') == 2,
         'unexpected sensor control call outside the reviewed blocks')
    need(source.count('scripts/build-prefix-mgw-bias-pdf.py') == 3
         and source.count('scripts/check-prefix-mgw-bias-pdf-self-test.py') == 2,
         'unexpected bias call outside the reviewed prefix and cross refusal')
    passed = []
    with tempfile.TemporaryDirectory(prefix='pid-rs-embodied-sensor-dispatch-') as temporary:
        work = Path(temporary)
        substitute = work / 'python3'
        substitute.write_text('#!' + sys.executable + '\n' + '''from pathlib import Path
import json, os, sys
p = Path(os.environ['PID_RS_DISPATCH_CALLS'])
previous = p.read_text().splitlines()
with p.open('a') as stream:
    stream.write(json.dumps(sys.argv[1:]) + '\\n')
codes = json.loads(os.environ['PID_RS_DISPATCH_CODES'])
raise SystemExit(codes[len(previous)] if len(previous) < len(codes) else 97)
''')
        substitute.chmod(0o700)
        values = {name: 'test-' + name for name in FIELDS}
        values['PYTHON'] = str(substitute)
        values['CONTROL_MONOTONIC_DEADLINE'] = '12345.125'
        values['PRODUCTION_MONOTONIC_DEADLINE'] = '14567.875'
        bias_values = {name: 'bias-' + name for name in BIAS_DIAGNOSTICS}
        bias_values['PYTHON'] = str(substitute)
        environment_values = {'PID_RS_EMBODIED_SENSOR_' + key: value
                              for key, value in values.items()}
        environment_values.update({'PID_RS_BIAS_' + key: value
                                   for key, value in bias_values.items()})
        derivative_fields = tuple(name.replace('FULL_', 'GRADIENT_').replace('OVERVIEW_', 'CUSP_') for name in FIELDS)
        derivative_values = {name: 'derivative-' + name for name in derivative_fields}
        derivative_values['PYTHON'] = str(substitute)
        derivative_values['CONTROL_MONOTONIC_DEADLINE'] = '23456.5'
        derivative_values['PRODUCTION_MONOTONIC_DEADLINE'] = '25678.25'
        environment_values.update({'PID_RS_DERIVATIVE_' + key: value
                                   for key, value in derivative_values.items()})
        diagnostics = {'PID_RS_EMBODIED_SENSOR_' + key:
                       'PID_RS_EMBODIED_SENSOR_' + key + ' is required' for key in FIELDS}
        diagnostics.update({'PID_RS_BIAS_' + key: value
                            for key, value in BIAS_DIAGNOSTICS.items()})
        bias_expected = []
        for mode in ('NORMAL', 'OPTIMIZED'):
            bias_expected.append((['-O'] if mode == 'OPTIMIZED' else []) + [
                '-I', '-S', '-B', 'scripts/check-prefix-mgw-bias-pdf-self-test.py',
                '--root', 'test-root',
                '--registration', bias_values['CONTROL_' + mode + '_REGISTRATION'],
                '--registration-sha256', bias_values['CONTROL_' + mode + '_REGISTRATION_SHA256'],
                '--output', bias_values['CONTROL_' + mode + '_OUTPUT']])
        for kind in ('full', 'summary'):
            bias_expected.append([
                '-I', '-S', '-B', 'scripts/build-prefix-mgw-bias-pdf.py',
                '--root', 'test-root', '--kind', kind, '--exact', '--check',
                '--registration', bias_values[kind.upper() + '_REGISTRATION'],
                '--registration-sha256', bias_values[kind.upper() + '_REGISTRATION_SHA256'],
                '--work-dir', bias_values[kind.upper() + '_WORK_DIR']])
        derivative_expected = []
        for mode in ('NORMAL', 'OPTIMIZED'):
            derivative_expected.append((['-O'] if mode == 'OPTIMIZED' else []) + [
                '-I', '-S', '-B', 'scripts/check-mgw-derivative-notes-pdf-self-test.py',
                '--root', 'test-root', '--registration', derivative_values['CONTROL_' + mode + '_REGISTRATION'],
                '--registration-sha256', derivative_values['CONTROL_' + mode + '_REGISTRATION_SHA256'],
                '--output', derivative_values['CONTROL_' + mode + '_OUTPUT'],
                '--stage-monotonic-deadline', derivative_values['CONTROL_MONOTONIC_DEADLINE']])
        for kind in ('gradient', 'cusp'):
            derivative_expected.append([
                '-I', '-S', '-B', 'scripts/build-mgw-derivative-notes-pdf.py',
                '--kind', kind, '--exact', '--check', '--root', 'test-root',
                '--manifest-sha256', derivative_values['MANIFEST_SHA256'],
                '--registration', derivative_values[kind.upper() + '_REGISTRATION'],
                '--registration-sha256', derivative_values[kind.upper() + '_REGISTRATION_SHA256'],
                '--work-dir', derivative_values[kind.upper() + '_WORK_DIR'],
                '--stage-monotonic-deadline', derivative_values['PRODUCTION_MONOTONIC_DEADLINE']])
        expected = []
        for mode in ('NORMAL', 'OPTIMIZED'):
            expected.append((['-O'] if mode == 'OPTIMIZED' else []) + [
                '-I', '-S', '-B', 'scripts/check-embodied-sensor-pdfs-self-test.py',
                '--root', 'test-root', '--registration', values['CONTROL_' + mode + '_REGISTRATION'],
                '--registration-sha256', values['CONTROL_' + mode + '_REGISTRATION_SHA256'],
                '--output', values['CONTROL_' + mode + '_OUTPUT'],
                '--stage-monotonic-deadline', values['CONTROL_MONOTONIC_DEADLINE']])
        for kind in ('full', 'overview'):
            expected.append([
                '-I', '-S', '-B', 'scripts/build-embodied-sensor-pdfs.py',
                '--kind', kind, '--exact', '--check', '--root', 'test-root',
                '--manifest-sha256', values['MANIFEST_SHA256'],
                '--registration', values[kind.upper() + '_REGISTRATION'],
                '--registration-sha256', values[kind.upper() + '_REGISTRATION_SHA256'],
                '--work-dir', values[kind.upper() + '_WORK_DIR'],
                '--stage-monotonic-deadline', values['PRODUCTION_MONOTONIC_DEADLINE']])

        def run(label, selected, mode, codes, expected_calls, status, omit=(), empty=(),
                diagnostic=None, stdout=b''):
            lane = work / str(len(passed))
            lane.mkdir()
            calls = lane / 'calls.jsonl'
            calls.write_text('')
            driver = lane / 'driver.sh'
            driver.write_text('set -euo pipefail\nMODE="$1"\nROOT=test-root\n' + selected)
            environment = {
                'PATH': str(work) + ':/usr/bin:/bin',
                'PID_RS_DISPATCH_CALLS': str(calls),
                'PID_RS_DISPATCH_CODES': json.dumps(codes),
            }
            for key, value in environment_values.items():
                if key not in omit:
                    environment[key] = '' if key in empty else value
            result = subprocess.run(['/bin/bash', '--noprofile', '--norc', str(driver), mode],
                                    env=environment, cwd=lane, stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=10, check=False)
            actual = [json.loads(line) for line in calls.read_text().splitlines()]
            need(result.returncode == status, label + ': unexpected return status')
            need(result.stdout == stdout and actual == expected_calls,
                 label + ': incorrect forwarded calls or output')
            if diagnostic is None:
                need(not result.stderr, label + ': unexpected diagnostic')
            else:
                need(diagnostic.encode() in result.stderr, label + ': noncausal rejection')
            passed.append(label)

        all_expected = bias_expected + derivative_expected + expected
        run('exact twelve-call order and bindings', prefix, '--exact', [0] * 12, all_expected, 0)
        run('inventory returns before all calls', prefix, '--inventory-only', [], [], 0,
            omit=environment_values,
            stdout=b'OK: standalone-paper, renderer-fragment, and PDF inventories are exact and direct-regular\n')
        run('cross mode starts no exact calls', prefix, '--cross-toolchain', [], [], 0,
            omit=environment_values)
        for field, diagnostic in diagnostics.items():
            run('missing ' + field + ' starts zero calls', prefix, '--exact', [], [], 1,
                omit=(field,), diagnostic=diagnostic)
            run('empty ' + field + ' starts zero calls', prefix, '--exact', [], [], 1,
                empty=(field,), diagnostic=diagnostic)
        for failing in range(12):
            run('stop after failed exact call ' + str(failing), prefix, '--exact',
                [0] * failing + [7], all_expected[:failing + 1], 7)

        # Causal negative control: deliberately delay sensor preflight, using inert calls only.
        # The same absent sensor field must expose eight consumed bias/derivative calls here,
        # while the actual prefix above requires zero calls for that field.
        late = prefix.replace(preflight, '', 1).replace(exact, preflight + '\n' + exact, 1)
        field = 'PID_RS_EMBODIED_SENSOR_OVERVIEW_WORK_DIR'
        run('late sensor preflight consumes eight existing calls', late, '--exact', [0] * 8,
            bias_expected + derivative_expected, 1, omit=(field,), diagnostic=diagnostics[field])

        cross_calls = [['-I', '-S', '-B', 'scripts/build-embodied-sensor-pdfs.py',
                        '--kind', kind, '--cross-toolchain'] for kind in ('full', 'overview')]
        run('two explicit status-two refusals', cross, '--cross-toolchain', [2, 2],
            cross_calls, 0, omit=environment_values)
        for mode in ('--inventory-only', '--exact'):
            run('no cross calls in ' + mode, cross, mode, [], [], 0, omit=environment_values)
        for failing in range(2):
            for code in (0, 1, 3):
                kind = ('full', 'overview')[failing]
                diagnostic = (kind + ' embodied-sensor cross-toolchain mode unexpectedly accepted'
                              if code == 0 else kind + ' embodied-sensor refusal returned ' + str(code))
                run('reject cross status ' + str(code) + ' for ' + kind, cross,
                    '--cross-toolchain', [2] * failing + [code], cross_calls[:failing + 1],
                    1, omit=environment_values, diagnostic=diagnostic)
    print(json.dumps({'status': 'passed', 'cases': len(passed),
                      'scope': 'Inert aggregate argument and control-flow checks; no PDF/proof execution.',
                      'case_names': passed}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
