#!/usr/bin/env python3
"""Frozen development reference: five count forecasts, no fitting or tuning."""
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
DATA = ROOT / 'audit/evidence/real-occupancy-sensors-example-2026-09-08/descriptive-comparisons.json'
RUNTIME = DATA.with_name('runtime-results.json')
MODELS = ('constant', 'light', 'co2', 'joint', 'or')
TOL = 1e-12


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def counts(record):
    out = {}
    for row in record['shannon']['joint_counts']:
        key = row['light_bin'], row['co2_bin'], row['occupancy']
        if key in out or key[0] not in range(4) or key[1] not in range(4) or key[2] not in (0, 1):
            raise ValueError('Invalid or repeated joint count key')
        if type(row['count']) is not int or row['count'] <= 0:
            raise ValueError('Counts must be positive integers')
        out[key] = row['count']
    if sum(out.values()) != record['shannon']['n']:
        raise ValueError('Joint count sum differs from recorded sample count')
    return out


def event_counts(table, model, a, b):
    # Select each joint state once. In particular, OR is inclusive, not a sum
    # of two separately smoothed single-source forecasts.
    selected = [(y, n) for (i, j, y), n in table.items() if
                model == 'constant' or
                (model == 'light' and i == a) or
                (model == 'co2' and j == b) or
                (model == 'joint' and i == a and j == b) or
                (model == 'or' and (i == a or j == b))]
    return tuple(sum(n for y, n in selected if y == label) for label in (0, 1))


def add_one(pair):
    return tuple(Fraction(n + 1, sum(pair) + 2) for n in pair)


def score(table, forecasts):
    n = sum(table.values())
    return {
        'n': n,
        'log_loss_nats': math.fsum(-c * math.log(float(forecasts[a, b][y]))
                                   for (a, b, y), c in table.items()) / n,
        'brier_score': math.fsum(c * (float(forecasts[a, b][1]) - y) ** 2
                                for (a, b, y), c in table.items()) / n,
    }


def main():
    started = utc()
    protocol = json.loads((STUDY / 'PROTOCOL.json').read_text())
    freeze = json.loads((HERE / 'FROZEN.json').read_text())
    if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['deadline_utc']):
        raise RuntimeError('Original study deadline passed; calculation refused')
    if sha(Path(__file__)) != freeze['calculator_sha256']:
        raise RuntimeError('Calculator changed after its freeze')
    if sha(STUDY / 'PROTOCOL.json') != freeze['protocol_sha256']:
        raise RuntimeError('Protocol changed after calculator freeze')
    if sha(DATA) != protocol['data_sha256'] or sha(RUNTIME) != freeze['runtime_sha256']:
        raise RuntimeError('Input hash differs from frozen input')
    data = json.loads(DATA.read_text())
    runtime = {r['recording']: r for r in json.loads(RUNTIME.read_text())['results']}
    tables = {name: counts(record) for name, record in data['files'].items()}
    if {k: sum(v.values()) for k, v in tables.items()} != {
            'datatraining.txt': 8143, 'datatest.txt': 2665, 'datatest2.txt': 9752}:
        raise ValueError('Unexpected recording names or counts')
    if data['bins'] != 4 or data['training_file'] != 'datatraining.txt':
        raise ValueError('Unexpected fitted source alphabet or training file')
    queries = [(a, b) for a in range(4) for b in range(4)]
    train = tables[data['training_file']]
    failures = []
    checks = []

    def check(name, passed, **detail):
        checks.append({'name': name, 'passed': bool(passed), **detail})
        if not passed:
            failures.append(name)

    union_records = []
    for name, table in tables.items():
        for a, b in queries:
            direct = event_counts(table, 'or', a, b)
            for y in (0, 1):
                left = sum(c for (i, j, k), c in table.items() if i == a and k == y)
                right = sum(c for (i, j, k), c in table.items() if j == b and k == y)
                overlap = table.get((a, b, y), 0)
                union_records.append({'recording': name, 'query': [a, b], 'target': y,
                                      'left': left, 'right': right, 'overlap': overlap,
                                      'direct_union': direct[y],
                                      'inclusion_exclusion': left + right - overlap})
                check(f'union:{name}:{a}:{b}:{y}', direct[y] == left + right - overlap)

    forecasts = {model: {q: add_one(event_counts(train, model, *q)) for q in queries}
                 for model in MODELS}
    forecast_records = {}
    for model in MODELS:
        forecast_records[model] = []
        for q in queries:
            p = forecasts[model][q]
            raw = event_counts(train, model, *q)
            check(f'normalization:{model}:{q}', sum(p) == 1 and all(0 < v < 1 for v in p))
            if sum(raw) == 0:
                check(f'empty_prior:{model}:{q}', p == (Fraction(1, 2), Fraction(1, 2)))
            forecast_records[model].append({'query': list(q), 'training_counts_0_1': raw,
                                           'probabilities_0_1': [float(v) for v in p],
                                           'exact_probabilities_0_1': [str(v) for v in p]})
    check('algebraic_empty_event_prior', add_one((0, 0)) == (Fraction(1, 2), Fraction(1, 2)))

    results = {name: {model: score(table, forecasts[model]) for model in MODELS}
               for name, table in tables.items()}
    historical = []
    for name, record in data['files'].items():
        for old_name, model in (('light', 'light'), ('co2', 'co2'), ('pair', 'joint')):
            if old_name not in record['predictive']:
                historical.append({'recording': name, 'model': model, 'status': 'not_present_in_retained_artifact'})
                continue
            for metric in ('log_loss_nats', 'brier_score'):
                expected = record['predictive'][old_name][metric]
                actual = results[name][model][metric]
                delta = actual - expected
                historical.append({'recording': name, 'model': model, 'metric': metric,
                                   'actual': actual, 'historical': expected, 'difference': delta})
                check(f'historical:{name}:{model}:{metric}', abs(delta) <= TOL,
                      difference=delta, tolerance=TOL)
    # The old constant was UNSMOOTHED prevalence; preserve that comparator
    # without silently replacing this protocol's add-one constant model.
    marginal = event_counts(train, 'constant', 0, 0)
    old_constant = {q: tuple(Fraction(v, sum(marginal)) for v in marginal) for q in queries}
    historical_constant = {}
    for name, record in data['files'].items():
        if 'constant' in record['predictive']:
            actual = score(tables[name], old_constant)
            historical_constant[name] = actual
            for metric in ('log_loss_nats', 'brier_score'):
                delta = actual[metric] - record['predictive']['constant'][metric]
                check(f'historical_unsmoothed_constant:{name}:{metric}', abs(delta) <= TOL,
                      difference=delta, tolerance=TOL)

    empirical = {}
    for name, table in tables.items():
        n = sum(table.values())
        targets = event_counts(table, 'constant', 0, 0)
        entropy = math.fsum(-c / n * math.log(c / n) for c in targets if c)
        terms = []
        for (a, b, y), c in table.items():
            pool = event_counts(table, 'or', a, b)
            check(f'empirical_actual_support:{name}:{a}:{b}:{y}', pool[y] >= c > 0)
            terms.append(-c / n * math.log(pool[y] / sum(pool)))
        loss = math.fsum(terms)
        red = runtime[name]['shared_exclusions_empirical']['red']['net_nats']
        delta = entropy - loss - red
        empirical[name] = {'n': n, 'target_entropy_nats': entropy,
                           'unsmoothed_same_law_or_log_loss_nats': loss,
                           'entropy_minus_or_loss_nats': entropy - loss,
                           'retained_rust_redundancy_nats': red, 'difference': delta,
                           'note': 'Each law fits and scores its own unsmoothed event posterior; not an out-of-sample predictor comparison.'}
        check(f'empirical_redundancy:{name}', abs(delta) <= TOL, difference=delta, tolerance=TOL)

    out = {'started_utc': started, 'finished_utc': utc(), 'calculator_sha256': sha(Path(__file__)),
           'protocol_sha256': sha(STUDY / 'PROTOCOL.json'), 'data_sha256': sha(DATA),
           'runtime_sha256': sha(RUNTIME), 'tolerance': TOL,
           'scope': 'Retrospective development counts, fixed training-derived predictors; no tuning, sampling inference, calibration, causal, or PID-specific advantage claim.',
           'brier_convention': 'Mean binary (P(Y=1)-Y)^2; not the sum over both labels.',
           'fit': 'One pseudocount per target label after event selection; OR union counts each matching row once.',
           'results': results, 'forecasts': forecast_records, 'union_checks': union_records,
           'historical_comparisons': historical, 'historical_unsmoothed_constant_control': historical_constant,
           'empirical_law_or_identity': empirical, 'checks': checks, 'failures': failures,
           'check_count': len(checks), 'all_checks_passed': not failures,
           'limits': ['Published count tables were not reconstructed from raw sensor rows.',
                      'Retained Rust redundancy was read, not rerun.',
                      'Training and both test recordings have already been examined; no untouched confirmation.',
                      'Training OR pools are nonempty on all 16 valid queries; empty joint cells and algebraic empty-event fallback are checked.',
                      'The query-selected OR forecast is not asserted to reproduce a published masked-channel operational protocol.',
                      'Smoothed fixed-training forecast losses on other laws are not those laws MGW atoms.',
                      'No production Rust implementation or API was changed.']}
    (HERE / 'RESULTS.json').write_text(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: out[k] for k in ('results', 'empirical_law_or_identity', 'check_count', 'failures', 'all_checks_passed')}, indent=2))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
