"""Fixed MGW report/custody predicates; no filesystem or process orchestration.

The caller supplies independently retained actual-record bindings. Successful
validation does not authenticate fabricated bindings, execute a kernel, or
admit the other eight baseline commands or mathematical prose correspondence.
"""
import copy
import hashlib
import json
import re
import sys

SCHEMA = 'pid-rs-mgw-fixed-world-judge-report-v1'
CLAIM = 'MGW-FIXED-WORLD-COUNTEREXAMPLE-001/v1'
OBSERVATION_SCHEMA = 'pid-rs-mgw-native-observation-v1'
ALLOWLIST = ('Classical.choice', 'Quot.sound', 'propext')
TARGET_NAMES = (
    ('world_normalization', 'WorldNormalization'), ('world_marginals', 'WorldMarginals'),
    ('world_factorization', 'WorldFactorization'), ('observation_identity', 'ObservationIdentity'),
    ('count_table', 'CountTable'), ('totals', 'Totals'), ('nonnegative', 'Nonnegative'),
    ('normalization', 'Normalization'), ('pushforward', 'Pushforward'),
    ('source_masses', 'SourceMasses'), ('event_counts', 'EventCounts'),
    ('net_arguments', 'NetArguments'), ('irrelevant_averages', 'IrrelevantAverages'),
    ('completing_averages', 'CompletingAverages'), ('irrelevant_synergy', 'IrrelevantSynergy'),
    ('completing_synergy', 'CompletingSynergy'), ('conditional_ratio', 'ConditionalRatio'),
    ('irrelevant_cmi', 'IrrelevantCmi'), ('completing_cmi', 'CompletingCmi'),
    ('synergy_equal', 'SynergyEqual'), ('cmi_different', 'CmiDifferent'))
PAIRS = tuple(('PidMgwFixedWorld.Candidate.' + a, 'PidMgwFixedWorld.RawTargets.' + b)
              for a, b in TARGET_NAMES)
TOP_KEYS = frozenset(('schema', 'claim', 'status', 'count', 'theorems'))
ROW_KEYS = frozenset(('candidate_fqn', 'target_fqn', 'candidate_kind', 'target_kind',
    'candidate_universes', 'target_universes', 'candidate_type', 'target_type',
    'target_value', 'type_defeq', 'candidate_axioms', 'target_axioms'))
RECORD_KEYS = frozenset(('schema', 'role', 'argv', 'cwd', 'status', 'actual_exit',
    'timed_out', 'timeout_seconds', 'stdout_sha256', 'stdout_bytes', 'stderr_sha256',
    'stderr_bytes', 'source_manifest_sha256', 'object_manifest_sha256'))
BINDING_KEYS = frozenset(('record_sha256', 'record_bytes', 'argv', 'cwd',
    'source_manifest_sha256', 'object_manifest_sha256'))
EMPTY_SHA256 = hashlib.sha256(b'').hexdigest()


class ValidationError(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _need(condition, code):
    if not condition:
        raise ValidationError(code)


def _keys(value, expected, code):
    _need(type(value) is dict and set(value) == expected, code)


def _pairs_hook(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, 'json.duplicate_key')
        result[key] = value
    return result


def _constant(_value):
    raise ValidationError('json.nonfinite_constant')


def _decode(raw, limit):
    _need(type(raw) is bytes and 0 < len(raw) <= limit, 'json.bytes')
    _need(raw.startswith(b'{') and raw.endswith(b'}\n'), 'json.frame')
    try:
        return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs_hook, parse_constant=_constant)
    except ValidationError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise ValidationError('json.malformed') from exc


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _text(value):
    return (type(value) is str and bool(value.strip()) and
            not any(0xD800 <= ord(c) <= 0xDFFF for c in value))


def validate_judge_report(raw):
    """Validate the exact frozen 21-row JSON contract; return the parsed report.

    Expression strings are observed text, not substitute proof terms. This
    predicate intentionally cannot distinguish a valid-shaped forgery alone.
    """
    report = _decode(raw, 8 * 1024**2)
    _keys(report, TOP_KEYS, 'report.keys')
    _need(report['schema'] == SCHEMA and report['claim'] == CLAIM and
          report['status'] == 'type-and-axiom-checks-passed', 'report.fixed')
    _need(type(report['count']) is int and report['count'] == 21, 'report.count')
    rows = report['theorems']
    _need(type(rows) is list and len(rows) == 21, 'report.rows')
    for row, pair in zip(rows, PAIRS):
        _keys(row, ROW_KEYS, 'row.keys')
        _need((row['candidate_fqn'], row['target_fqn']) == pair, 'row.fqn')
        _need(row['candidate_kind'] == 'theorem' and row['target_kind'] == 'definition', 'row.kind')
        _need(type(row['candidate_universes']) is list and row['candidate_universes'] == [] and
              type(row['target_universes']) is list and row['target_universes'] == [], 'row.universes')
        _need(row['type_defeq'] is True, 'row.type_defeq')
        for field in ('candidate_type', 'target_type', 'target_value'):
            _need(_text(row[field]), 'row.expression')
        for field in ('candidate_axioms', 'target_axioms'):
            values = row[field]
            _need(type(values) is list and all(type(x) is str for x in values), 'row.axiom_type')
            _need(all(x in ALLOWLIST for x in values), 'row.axiom_allowlist')
            _need(values == sorted(set(values)), 'row.axiom_order_unique')
    return report


def _observation(raw, binding, role):
    _keys(binding, BINDING_KEYS, 'binding.keys')
    _need(_sha(binding['record_sha256']) and type(binding['record_bytes']) is int and
          0 < binding['record_bytes'] <= 65536, 'binding.record_pin')
    _need(type(raw) is bytes and len(raw) == binding['record_bytes'] and
          hashlib.sha256(raw).hexdigest() == binding['record_sha256'], 'binding.record_bytes')
    _need(type(binding['argv']) is list and bool(binding['argv']) and
          all(_text(x) for x in binding['argv']) and _text(binding['cwd']), 'binding.invocation')
    _need(_sha(binding['source_manifest_sha256']) and _sha(binding['object_manifest_sha256']), 'binding.identity')
    record = _decode(raw, 65536)
    _keys(record, RECORD_KEYS, 'record.keys')
    _need(record['schema'] == OBSERVATION_SCHEMA and record['role'] == role, 'record.role')
    _need(type(record['argv']) is list and record['argv'] == binding['argv'] and
          record['cwd'] == binding['cwd'], 'record.invocation')
    _need(record['status'] == 'completed' and type(record['actual_exit']) is int and
          record['actual_exit'] == 0 and record['timed_out'] is False, 'record.terminal')
    _need(type(record['timeout_seconds']) is int and
          record['timeout_seconds'] == (60 if role == 'judge' else 300), 'record.timeout')
    for field in ('source_manifest_sha256', 'object_manifest_sha256'):
        _need(record[field] == binding[field], 'record.identity')
    for prefix in ('stdout', 'stderr'):
        _need(type(record[prefix + '_bytes']) is int and 0 <= record[prefix + '_bytes'] <= 8 * 1024**2 and
              _sha(record[prefix + '_sha256']), 'record.stream_pin')
    _need(record['stderr_bytes'] == 0 and record['stderr_sha256'] == EMPTY_SHA256, 'record.stderr')
    if role == 'kernel':
        _need(record['stdout_bytes'] == 0 and record['stdout_sha256'] == EMPTY_SHA256, 'record.kernel_stdout')
        _need(len(record['argv']) == 3 and record['argv'][1:] == ['--fresh', 'PidMgwFixedWorld.Candidate'], 'record.kernel_argv')
    else:
        _need(len(record['argv']) == 6 and record['argv'][1:4] == ['-t', '0', '-o'] and
              record['argv'][5] == 'PidMgwFixedWorld/Judge.lean', 'record.judge_argv')
    return record


def validate_completion(report_raw, judge_record_raw, kernel_record_raw, bindings):
    """Bind report and successful Judge/fresh-kernel observations to root pins.

    `bindings` has exactly judge/kernel keys, each with BINDING_KEYS. The root
    supplies pins independently from these candidate-controlled/actual records.
    The other eight baseline records, clocks/resources, complete source/runtime
    custody and semantic review remain the root's separate completion checks.
    """
    _keys(bindings, frozenset(('judge', 'kernel')), 'completion.bindings')
    judge = _observation(judge_record_raw, bindings['judge'], 'judge')
    kernel = _observation(kernel_record_raw, bindings['kernel'], 'kernel')
    _need(type(report_raw) is bytes and len(report_raw) == judge['stdout_bytes'] and
          hashlib.sha256(report_raw).hexdigest() == judge['stdout_sha256'], 'completion.report_bytes')
    report = validate_judge_report(report_raw)
    return {'status': 'supplied-report-and-terminal-bindings-valid', 'theorem_count': report['count'],
        'report_sha256': judge['stdout_sha256'], 'judge_record_sha256': bindings['judge']['record_sha256'],
        'kernel_record_sha256': bindings['kernel']['record_sha256'],
        'no_native_execution_or_full_claim_admission_by_this_function': True}


def _encoded(value):
    return (json.dumps(value, ensure_ascii=True, separators=(',', ':')) + '\n').encode()


def selfcheck():
    """Deterministic synthetic checks in this interpreter, never native children."""
    report = {'schema': SCHEMA, 'claim': CLAIM, 'status': 'type-and-axiom-checks-passed',
        'count': 21, 'theorems': []}
    for candidate, target in PAIRS:
        report['theorems'].append({'candidate_fqn': candidate, 'target_fqn': target,
            'candidate_kind': 'theorem', 'target_kind': 'definition', 'candidate_universes': [],
            'target_universes': [], 'candidate_type': 'synthetic fixture expression',
            'target_type': 'synthetic fixture expression', 'target_value': 'synthetic fixture expression',
            'type_defeq': True, 'candidate_axioms': [], 'target_axioms': []})
    raw = _encoded(report)
    records = {}
    bindings = {}
    for role in ('judge', 'kernel'):
        argv = ['/fixture/lean', '-t', '0', '-o', '/fixture/objects/Judge.olean', 'PidMgwFixedWorld/Judge.lean'] if role == 'judge' else ['/fixture/leanchecker', '--fresh', 'PidMgwFixedWorld.Candidate']
        records[role] = {'schema': OBSERVATION_SCHEMA, 'role': role, 'argv': argv,
            'cwd': '/fixture/work', 'status': 'completed', 'actual_exit': 0, 'timed_out': False,
            'timeout_seconds': 60 if role == 'judge' else 300,
            'stdout_sha256': hashlib.sha256(raw).hexdigest() if role == 'judge' else EMPTY_SHA256,
            'stdout_bytes': len(raw) if role == 'judge' else 0, 'stderr_sha256': EMPTY_SHA256,
            'stderr_bytes': 0, 'source_manifest_sha256': '1' * 64, 'object_manifest_sha256': '2' * 64}
        rr = _encoded(records[role])
        bindings[role] = {k: records[role][k] for k in ('argv', 'cwd', 'source_manifest_sha256', 'object_manifest_sha256')}
        bindings[role].update(record_sha256=hashlib.sha256(rr).hexdigest(), record_bytes=len(rr))
    outcomes = []

    def reject(case, call, code):
        try:
            call()
        except ValidationError as exc:
            _need(exc.code == code, 'selfcheck.wrong_cause.' + case + '.' + exc.code)
            outcomes.append({'case': case, 'expected': 'reject', 'actual': 'reject', 'code': code})
        else:
            raise ValidationError('selfcheck.false_accept.' + case)

    def report_case(case, edit, code):
        value = copy.deepcopy(report)
        edit(value)
        reject(case, lambda: validate_judge_report(_encoded(value)), code)

    def completion(value=raw, recs=None, pins=None):
        rs = records if recs is None else recs
        bs = bindings if pins is None else pins
        return validate_completion(value, _encoded(rs['judge']), _encoded(rs['kernel']), bs)

    def record_case(case, role, field, value, code):
        rs = copy.deepcopy(records)
        bs = copy.deepcopy(bindings)
        rs[role][field] = value
        rr = _encoded(rs[role])
        bs[role].update(record_sha256=hashlib.sha256(rr).hexdigest(), record_bytes=len(rr))
        reject(case, lambda: completion(recs=rs, pins=bs), code)

    validate_judge_report(raw)
    completion()
    outcomes.extend([{'case': 'positive-schema', 'expected': 'accept', 'actual': 'accept'},
                     {'case': 'positive-synthetic-bindings', 'expected': 'accept', 'actual': 'accept'}])
    reject('J01-missing', lambda: validate_judge_report(None), 'json.bytes')
    reject('J02-empty', lambda: validate_judge_report(b''), 'json.bytes')
    reject('J03-truncated', lambda: validate_judge_report(raw[:-2] + b'\n'), 'json.frame')
    reject('J04-second-document', lambda: validate_judge_report(raw + b'{}\n'), 'json.malformed')
    reject('J05-duplicate-key', lambda: validate_judge_report(raw.replace(b'"count":21', b'"count":21,"count":21', 1)), 'json.duplicate_key')
    for label, value in (('bool', True), ('float', 21.0), ('string', '21')):
        report_case('J06-' + label, lambda r, v=value: r.update(count=v), 'report.count')
    report_case('J07-missing-row', lambda r: r['theorems'].pop(), 'report.rows')
    report_case('J08-duplicate-row', lambda r: r['theorems'].__setitem__(20, copy.deepcopy(r['theorems'][19])), 'row.fqn')
    report_case('J09-order', lambda r: r['theorems'].__setitem__(slice(0, 2), list(reversed(r['theorems'][:2]))), 'row.fqn')
    report_case('J10-fqn', lambda r: r['theorems'][0].update(target_fqn='Wrong.Target'), 'row.fqn')
    report_case('J11-extra-top', lambda r: r.update(extra=0), 'report.keys')
    report_case('J11-missing-row-key', lambda r: r['theorems'][0].pop('target_type'), 'row.keys')
    report_case('J12-status', lambda r: r.update(status='forged'), 'report.fixed')
    report_case('J12-kind', lambda r: r['theorems'][0].update(candidate_kind='def'), 'row.kind')
    report_case('J12-universe', lambda r: r['theorems'][0].update(candidate_universes=['u']), 'row.universes')
    report_case('J12-defeq-type', lambda r: r['theorems'][0].update(type_defeq=1), 'row.type_defeq')
    for field in ('candidate_type', 'target_type', 'target_value'):
        report_case('J13-empty-' + field, lambda r, f=field: r['theorems'][0].__setitem__(f, ''), 'row.expression')
    report_case('J13-wrong-type', lambda r: r['theorems'][0].update(target_value=0), 'row.expression')
    report_case('J14-forbidden', lambda r: r['theorems'][0].update(candidate_axioms=['sorryAx']), 'row.axiom_allowlist')
    report_case('J14-duplicate', lambda r: r['theorems'][0].update(target_axioms=['propext', 'propext']), 'row.axiom_order_unique')
    report_case('J14-unsorted', lambda r: r['theorems'][0].update(candidate_axioms=['propext', 'Classical.choice']), 'row.axiom_order_unique')
    report_case('J14-wrong-type', lambda r: r['theorems'][0].update(target_axioms=[0]), 'row.axiom_type')
    forged = copy.deepcopy(report)
    forged['theorems'][0]['candidate_axioms'] = list(ALLOWLIST)
    forged_raw = _encoded(forged)
    validate_judge_report(forged_raw)
    outcomes.append({'case': 'J15-valid-shape-alone', 'expected': 'accept-schema-only', 'actual': 'accept-schema-only'})
    reject('J15-output-forgery', lambda: completion(forged_raw), 'completion.report_bytes')
    record_case('J16-failed-exit', 'judge', 'actual_exit', 1, 'record.terminal')
    record_case('J16-bool-exit', 'judge', 'actual_exit', False, 'record.terminal')
    record_case('J16-timeout', 'judge', 'timed_out', True, 'record.terminal')
    record_case('J16-status', 'judge', 'status', 'skipped', 'record.terminal')
    record_case('J16-argv', 'judge', 'argv', ['/different'], 'record.invocation')
    record_case('J16-source', 'judge', 'source_manifest_sha256', '3' * 64, 'record.identity')
    record_case('J16-objects', 'judge', 'object_manifest_sha256', '3' * 64, 'record.identity')
    record_case('J16-timeout-bound', 'judge', 'timeout_seconds', 61, 'record.timeout')
    record_case('J16-stderr', 'judge', 'stderr_bytes', 1, 'record.stderr')
    reject('J17-missing-kernel', lambda: validate_completion(raw, _encoded(records['judge']), None, bindings), 'binding.record_bytes')
    record_case('J17-failed-kernel', 'kernel', 'actual_exit', 1, 'record.terminal')
    record_case('J17-nonempty-kernel', 'kernel', 'stdout_bytes', 1, 'record.kernel_stdout')
    forged_records = copy.deepcopy(records)
    forged_records['judge'].update(stdout_sha256=hashlib.sha256(forged_raw).hexdigest(), stdout_bytes=len(forged_raw))
    reject('J18-self-rebased-forgery', lambda: completion(forged_raw, forged_records), 'binding.record_bytes')
    _need(len(outcomes) == 43, 'selfcheck.case_count')
    return {'status': 'synthetic-selfchecks-completed', 'optimized': not __debug__,
        'cases': outcomes, 'case_count': len(outcomes),
        'accepted_cases': sum(x['actual'].startswith('accept') for x in outcomes),
        'rejected_cases': sum(x['actual'] == 'reject' for x in outcomes),
        'fixture_report_sha256': hashlib.sha256(raw).hexdigest(),
        'native_children': 0, 'genuine_producer_or_theorem_credit': False}


if __name__ == '__main__':
    if sys.argv[1:] != ['--self-check']:
        raise SystemExit('usage: judge_report_validation.py --self-check')
    print(json.dumps(selfcheck(), sort_keys=True, separators=(',', ':')))
