#!/usr/bin/env python3
"""Recheck the public selected projection with the unchanged finite checker.

No solver, generator, subprocess or file-writing API is used. Historical
capture metadata is a selected projection, not a public original receipt.
"""
import sys
sys.dont_write_bytecode = True

import hashlib
import importlib.util
import json
from pathlib import Path
import stat

ROOT = Path(__file__).resolve().parent
CHECKER_SHA = 'd6e23bf5d329368cf9681c4b7ee069a2a30930c368c842514253c8d6a3476d2e'
OBSERVATIONS_SHA = '16d16a65130140688f88860bbba5824350813df0fbd3af897ff63f0fc55bc9a8'
GENERATOR_SHA = '62cd492b20b3d908d26e3838d9d648475d1ea92b9ba5c714bab5844e3a4e6eeb'
SAVED_REPORT_SHA = 'eab596f22f289451861f7c657c3fad0d6f4d7775453ff044e3ae3e2a2d22807d'


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def exact(left, right):
    """Evidence equality includes recursive shape, exact type and value."""
    if type(left) is not type(right):
        return False
    if type(left) is dict:
        return (all(type(k) is str for k in left) and all(type(k) is str for k in right)
                and left.keys() == right.keys() and all(exact(left[k], right[k]) for k in left))
    if type(left) in (list, tuple):
        return len(left) == len(right) and all(exact(a, b) for a, b in zip(left, right))
    return left == right


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'duplicate JSON key')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('nonfinite JSON constant: ' + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def read(relative, cap=1048576):
    path = ROOT / relative
    need(path.resolve(strict=True) == path, 'package path route')
    before = path.lstat()
    need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= cap,
         'ordinary bounded package file')
    raw = path.read_bytes()
    need(len(raw) == before.st_size and path.lstat().st_size == before.st_size,
         'package file size stability')
    return raw


def stream(case, label, channel, expected):
    suffix = '.stdout.smt2' if label == 'generator' and channel == 'stdout' else '.' + channel
    relative = 'raw/' + case + '/' + label + suffix
    raw = read(relative, 65536 if label == 'generator' else 1048576)
    need(exact(expected, {'bytes': len(raw), 'sha256': sha(raw)}),
         'selected historical stream hash')
    return raw


def qualify():
    checker_raw = read('model_checker.py')
    need(sha(checker_raw) == CHECKER_SHA, 'unchanged checker source')
    observations_raw = read('OBSERVATIONS.json')
    need(sha(observations_raw) == OBSERVATIONS_SHA, 'selected observations source')
    need(sha(read('fin3_smt.py')) == GENERATOR_SHA, 'defining encoder source bytes')
    observations = strict_json(observations_raw)
    need(type(observations) is dict and exact(
        [observations['schema'], observations['generator_source_sha256'],
         observations['case_count'], observations['solver_observations'],
         observations['historical_sat_projections'], observations['historical_unsat_observations']],
        ['smt39-public-selected-historical-observations-v1', GENERATOR_SHA, 39, 78, 34, 44]),
         'projection identity')

    spec = importlib.util.spec_from_file_location('frozen_smt39_projection_checker', str(ROOT / 'model_checker.py'))
    checker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checker)
    cases = observations['cases']
    need(type(cases) is list and all(type(row) is dict and set(row) ==
         {'case', 'expected', 'generator', 'solvers'} for row in cases) and
         exact([[row['case'], row['expected']] for row in cases], [list(r) for r in checker.ROSTER]),
         'exact original 39-case order and status roster')
    records = []
    for row in cases:
        case, expected = row['case'], row['expected']
        generator = row['generator']
        need(type(generator) is dict and exact(
             [generator['native_exit'], generator['defining_source_sha256']], [0, GENERATOR_SHA]),
             'selected generator observation')
        formula = stream(case, 'generator', 'stdout', generator['streams']['stdout'])
        need(stream(case, 'generator', 'stderr', generator['streams']['stderr']) == b'',
             'historical generator stderr')
        need(type(row['solvers']) is dict and set(row['solvers']) == {'z3', 'cvc5'}, 'exact solver roster')
        for solver in ('z3', 'cvc5'):
            saved = row['solvers'][solver]
            need(type(saved) is dict and exact(
                 [saved['native_exit'], saved['status_observed']], [0, expected]), 'selected solver observation')
            out = stream(case, solver, 'stdout', saved['streams']['stdout'])
            err = stream(case, solver, 'stderr', saved['streams']['stderr'])
            decision = checker.validate(case, solver, out, err, saved['native_exit'])
            need(type(decision) is dict and exact(
                 [decision.get('accepted'), decision.get('status'),
                  decision.get('semantic_sat_model_checked'), decision.get('unsat_certificate_checked')],
                 [True, expected, expected == 'sat', False]),
                 'retained projected assignment decision')
            records.append({**decision, 'stdout_sha256': sha(out), 'stderr_sha256': sha(err),
                            'formula_sha256': sha(formula)})
    need(exact([len(records), sum(row['semantic_sat_model_checked'] is True for row in records)], [78, 34]),
         'complete historical protocol and SAT projection counts')
    nodes, zeta, inverse, negative, bottom = checker.geometry()
    result = {
        'status': 'retained78_protocol_and34_assignment_semantics_checked',
        'retained_observations_not_fresh': True,
        'unsat_certificates_checked': False,
        'scope': 'binary finite SMT39; no original-Finset transport, B-L, old-SPEC or Program closure',
        'model_helper_bodies_semantically_checked': False,
        'carrier': [checker.family_code(family) for family in nodes],
        'zeta': zeta, 'gaussian_inverse': inverse, 'negative_coordinate': negative,
        'bottom': checker.family_code(bottom), 'records': records,
    }
    encoded = (json.dumps(result, sort_keys=True, separators=(',', ':')) + '\n').encode()
    normal = read('reports/retained-normal.json')
    optimized = read('reports/retained-optimized.json')
    need(sha(normal) == SAVED_REPORT_SHA and normal == optimized and encoded == normal,
         'byte equality with both original qualified projection reports')
    need(read('model_checker.py') == checker_raw and read('OBSERVATIONS.json') == observations_raw,
         'source bytes stable after checking')
    return encoded


if __name__ == '__main__':
    if len(sys.argv) != 1:
        raise SystemExit('usage: python3 -I -S -B qualify.py')
    try:
        sys.stdout.buffer.write(qualify())
    except Exception as exc:
        print(json.dumps({'status': 'failed_STOP', 'error': type(exc).__name__, 'message': str(exc)}, sort_keys=True))
        raise SystemExit(1)
