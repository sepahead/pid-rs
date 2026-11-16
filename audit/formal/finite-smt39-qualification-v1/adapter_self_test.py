#!/usr/bin/env python3
"""Finite controls for the portable reader; no writes or child processes.

The in-memory binding mutations deliberately rebind the observation hash where
stated. They test semantic/type guards beyond a stale hash failure. They do not
change any file or the frozen checker, and supply no independent science credit.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent


def main():
    spec = importlib.util.spec_from_file_location('smt39_portable_reader_tested', str(ROOT / 'qualify.py'))
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    original_read = reader.read
    original_sha = reader.OBSERVATIONS_SHA
    observations_raw = original_read('OBSERVATIONS.json')
    observations = reader.strict_json(observations_raw)
    rows = []

    def accept(name, predicate):
        try:
            okay = predicate() is True
            rows.append({'id': name, 'expected': 'accept', 'observed': 'accept' if okay else 'mismatch'})
        except Exception as exc:
            rows.append({'id': name, 'expected': 'accept', 'observed': 'unexpected-exception',
                         'error': type(exc).__name__, 'message': str(exc)})

    def refuse(name, action, message):
        try:
            action()
            rows.append({'id': name, 'expected': 'refuse', 'observed': 'unexpected-accept'})
        except ValueError as exc:
            okay = str(exc) == message
            rows.append({'id': name, 'expected': 'refuse', 'observed': 'refuse' if okay else 'wrong-refusal',
                         'message': str(exc)})
        except Exception as exc:
            rows.append({'id': name, 'expected': 'refuse', 'observed': 'unexpected-exception',
                         'error': type(exc).__name__, 'message': str(exc)})

    def run_bound(replacements, rebind=False, late_checker=False):
        calls = 0

        def read(relative, cap=1048576):
            nonlocal calls
            if relative == 'model_checker.py':
                calls += 1
                if late_checker and calls > 1:
                    return original_read(relative, cap) + b'\n'
            return replacements[relative] if relative in replacements else original_read(relative, cap)

        reader.read = read
        if rebind:
            reader.OBSERVATIONS_SHA = hashlib.sha256(replacements['OBSERVATIONS.json']).hexdigest()
        try:
            return reader.qualify()
        finally:
            reader.read = original_read
            reader.OBSERVATIONS_SHA = original_sha

    def observation_change(name, change, message):
        changed = copy.deepcopy(observations)
        change(changed)
        raw = (json.dumps(changed, sort_keys=True, separators=(',', ':')) + '\n').encode()
        refuse(name, lambda: run_bound({'OBSERVATIONS.json': raw}, rebind=True), message)

    accept('P-strict-json-types', lambda: reader.exact(
        reader.strict_json(b'{"a":[false,0,0.0,null,"x"],"b":{"c":true}}'),
        {'a': [False, 0, 0.0, None, 'x'], 'b': {'c': True}}))
    accept('P-recursive-exact-equality', lambda: reader.exact(
        {'a': [False, 0, 5.0, {'b': None}]}, {'a': [False, 0, 5.0, {'b': None}]}))
    accept('P-public-readback', lambda: reader.qualify() == original_read('reports/retained-normal.json'))

    for name, raw in (
        ('N-duplicate-root', b'{"a":0,"a":0}'),
        ('N-duplicate-nested', b'{"a":{"b":0,"b":0}}'),
    ):
        refuse(name, lambda raw=raw: reader.strict_json(raw), 'duplicate JSON key')
    for value in ('NaN', 'Infinity', '-Infinity'):
        refuse('N-json-' + value, lambda value=value: reader.strict_json(('{"a":' + value + '}').encode()),
               'nonfinite JSON constant: ' + value)
    for name, left, right in (
        ('bool-int', False, 0), ('int-bool', 0, False), ('float-int', 5.0, 5), ('int-float', 5, 5.0),
        ('nested-bool', {'a': [False]}, {'a': [0]}),
        ('nested-float', {'a': [5.0]}, {'a': [5]}),
        ('dict-key-type', {'a': {False: 0}}, {'a': {0: 0}}),
        ('missing-key', {'a': 0}, {'a': 0, 'b': 0}),
        ('extra-key', {'a': 0, 'b': 0}, {'a': 0}),
    ):
        refuse('N-exact-' + name,
               lambda left=left, right=right: reader.need(reader.exact(left, right), 'inexact evidence'),
               'inexact evidence')

    for path, message in (
        ('model_checker.py', 'unchanged checker source'),
        ('fin3_smt.py', 'defining encoder source bytes'),
        ('OBSERVATIONS.json', 'selected observations source'),
    ):
        raw = original_read(path) + b'\n'
        refuse('N-byte-binding-' + path, lambda path=path, raw=raw: run_bound({path: raw}), message)
    for name, raw in (
        ('N-coherent-duplicate-root', observations_raw.replace(b'"case_count": 39,', b'"case_count": 39, "case_count": 39,', 1)),
        ('N-coherent-duplicate-nested', observations_raw.replace(b'"native_exit": 0,', b'"native_exit": 0, "native_exit": 0,', 1)),
    ):
        refuse(name, lambda raw=raw: run_bound({'OBSERVATIONS.json': raw}, rebind=True), 'duplicate JSON key')
    for key, value in (('case_count', 39.0), ('solver_observations', 78.0), ('historical_sat_projections', 34.0)):
        observation_change('N-coherent-float-' + key, lambda x, key=key, value=value: x.update({key: value}),
                           'projection identity')
    observation_change('N-coherent-extra-case-field', lambda x: x['cases'][0].update({'extra': 0}),
                       'exact original 39-case order and status roster')
    observation_change('N-coherent-case-order', lambda x: x['cases'].reverse(),
                       'exact original 39-case order and status roster')
    for name, value in (('False', False), ('float', 0.0)):
        observation_change('N-coherent-generator-native-' + name,
                           lambda x, value=value: x['cases'][0]['generator'].update({'native_exit': value}),
                           'selected generator observation')
        observation_change('N-coherent-solver-native-' + name,
                           lambda x, value=value: x['cases'][0]['solvers']['z3'].update({'native_exit': value}),
                           'selected solver observation')
        observation_change('N-coherent-stream-count-' + name,
                           lambda x, value=value: x['cases'][0]['generator']['streams']['stderr'].update({'bytes': value}),
                           'selected historical stream hash')
    observation_change('N-coherent-stream-extra-field',
                       lambda x: x['cases'][0]['generator']['streams']['stderr'].update({'extra': 0}),
                       'selected historical stream hash')
    path = 'raw/W01-carrier-complete/z3.stdout'
    refuse('N-raw-stream-binding', lambda: run_bound({path: original_read(path) + b'\n'}),
           'selected historical stream hash')
    for path in ('reports/retained-normal.json', 'reports/retained-optimized.json'):
        refuse('N-saved-report-' + path.split('/')[-1],
               lambda path=path: run_bound({path: original_read(path) + b'\n'}),
               'byte equality with both original qualified projection reports')
    refuse('N-checker-postread-change', lambda: run_bound({}, late_checker=True), 'source bytes stable after checking')

    passed = all(row['observed'] == row['expected'] for row in rows)
    counts = {'accept': sum(row['expected'] == 'accept' for row in rows),
              'refuse': sum(row['expected'] == 'refuse' for row in rows)}
    if not reader.exact(counts, {'accept': 3, 'refuse': 35}) or len(rows) != 38:
        raise RuntimeError('frozen portable adapter case inventory differs')
    result = {'schema': 'finite-smt39-portable-adapter-controls-v1', 'all_expected': passed,
              'count': len(rows), 'counts': counts, 'controls': rows,
              'credit': 'Exposed finite reader/parser/binding controls; same runtime and files; no new solver or scientific credit.'}
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n')
    return 0 if passed else 1


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('usage: python3 -I -S -B adapter_self_test.py')
    raise SystemExit(main())
