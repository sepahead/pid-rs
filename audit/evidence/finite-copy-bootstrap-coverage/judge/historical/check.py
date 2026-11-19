"""Frozen exact finite-law judge; imports no driver or production statistic code."""
from fractions import Fraction as F
from pathlib import Path
import hashlib, json, math, re, struct, sys


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def strict(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            need(key not in out, 'duplicate JSON key')
            out[key] = value
        return out
    def constant(_value):
        raise ValueError('nonfinite JSON primitive')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def integer(value, expected=None):
    need(type(value) is int, 'integer primitive required')
    if expected is not None:
        need(value == expected, 'integer value differs')
    return value


def bits(raw):
    need(type(raw) is str and re.fullmatch('[0-9a-f]{16}', raw) is not None, 'canonical binary64 bits')
    n = int(raw, 16)
    x = struct.unpack('>d', n.to_bytes(8, 'big'))[0]
    need(math.isfinite(x), 'nonfinite binary64 value')
    return n, x


def total_key(raw):
    n, _ = bits(raw)
    return (~n & ((1 << 64) - 1)) if n >> 63 else n | (1 << 63)


def log_interval(x, terms=192):
    """Range reduction and positive atanh series with an explicit geometric tail."""
    need(type(x) is F and x > 0, 'positive rational logarithm argument')
    power = 0
    while x >= 2:
        x /= 2; power += 1
    while x < 1:
        x *= 2; power -= 1
    def unit(y):
        z = (y - 1) / (y + 1)
        s = F(0)
        for j in range(terms):
            s += 2 * z ** (2 * j + 1) / (2 * j + 1)
        tail = 2 * z ** (2 * terms + 1) / ((2 * terms + 1) * (1 - z * z))
        return s, s + tail
    lo, hi = unit(x)
    l2, u2 = unit(F(2))
    return (lo + power * l2, hi + power * u2) if power >= 0 else (lo + power * u2, hi + power * l2)


def fraction_record(x):
    return {'numerator': str(x.numerator), 'denominator': str(x.denominator)}


def judge(raw):
    need(len(raw) <= 1048576, 'output byte cap')
    value = strict(raw)
    need(type(value) is dict and set(value) == {'schema', 'configuration', 'schedule_codes', 'rows'}, 'top-level schema')
    need(value['schema'] == 'pid-copy-bootstrap-calibration-v1', 'schema identity')
    cfg = value['configuration']
    need(type(cfg) is dict and set(cfg) == {'n', 'replicates', 'block_size', 'seed', 'alpha_bits', 'algorithm_revision'}, 'configuration shape')
    for key, expected in {'n': 4, 'replicates': 200, 'block_size': 1, 'seed': 7}.items():
        integer(cfg[key], expected)
    need(cfg['alpha_bits'] == '3fa999999999999a' and cfg['algorithm_revision'] == 'V1', 'configuration identity')
    schedule = value['schedule_codes']
    need(type(schedule) is list and len(schedule) == 200, 'complete schedule')
    need(all(0 <= integer(x) < 256 for x in schedule), 'schedule code domain')
    rows = value['rows']
    need(type(rows) is list and len(rows) == 16, 'complete ordered outer sample space')
    hlo, hhi = log_interval(F(27, 4)); hlo /= 3; hhi /= 3
    need(F(0) < hlo < hhi < 1 and hhi - hlo < F(1, 1 << 160), 'population entropy enclosure')
    empirical_reference = {}
    for count in range(5):
        if count in (0, 4):
            empirical_reference[count] = (F(0), F(0))
        else:
            p = F(count, 4)
            lp, up = log_interval(p); lq, uq = log_interval(1 - p)
            empirical_reference[count] = (-p * up - (1 - p) * uq, -p * lp - (1 - p) * lq)
    # A frozen finite-corpus accuracy requirement, not a global libm error theorem.
    window = F(1, 1 << 48)
    def check_empirical(raw_bits, count):
        represented = F(bits(raw_bits)[1])
        low, high = empirical_reference[count]
        if count in (0, 4):
            need(represented == 0, 'zero empirical entropy')
        else:
            need(high - window <= represented <= low + window, 'finite empirical entropy reference window')
    weight = covered_weight = failure_weight = 0
    results = []
    for mask, row in enumerate(rows):
        need(type(row) is dict and set(row) == {'mask', 'point_bits', 'lower_bits', 'upper_bits', 'replicate_bits'}, 'row schema')
        integer(row['mask'], mask)
        k = mask.bit_count()
        probability_numerator = 2 ** (4 - k)
        weight += probability_numerator
        point = bits(row['point_bits'])[1]
        check_empirical(row['point_bits'], k)
        replicas = row['replicate_bits']
        need(type(replicas) is list and len(replicas) == 200, 'complete replicate outcomes')
        for r in replicas:
            bits(r)
        ordered = sorted(replicas, key=total_key)
        # The frozen binary64 alpha/2*200 is exactly5.0; both tails use that one trim.
        need(row['lower_bits'] == ordered[5] and row['upper_bits'] == ordered[194], 'actual equal-rank endpoints')
        low, high = F(bits(row['lower_bits'])[1]), F(bits(row['upper_bits'])[1])
        need(low <= high, 'reversed interval')
        if k in (0, 4):
            need(point == 0 and low == high == 0 and all(bits(x)[1] == 0 for x in replicas), 'constant-sample zero statistic')
            failure_weight += probability_numerator
        # Classify coverage only when the whole independent exact entropy enclosure decides it.
        if low <= hlo and hhi <= high:
            covered = True; covered_weight += probability_numerator
        elif high < hlo or hhi < low:
            covered = False
        else:
            raise ValueError('population/represented endpoint comparison unresolved')
        # Decode the separately observed production schedule. A constant resample must give zero.
        for code, r in zip(schedule, replicas):
            indices = [(code >> shift) & 3 for shift in (6, 4, 2, 0)]
            count = sum((mask >> index) & 1 for index in indices)
            check_empirical(r, count)
            if count in (0, 4):
                need(bits(r)[1] == 0, 'constant resample not zero')
        results.append({'mask': mask, 'ones': k, 'probability_numerator': probability_numerator,
                        'denominator': 81, 'covered': covered})
    need(weight == 81 and failure_weight == 17 and covered_weight <= 64, 'exact law/failure-mass identity')
    return {'status': 'EXACT_DECLARED_FINITE_COVERAGE_CHECK_PASSED', 'outer_samples': 16,
            'coverage': fraction_record(F(covered_weight, 81)), 'constant_sample_failure_mass': fraction_record(F(17, 81)),
            'nominal_95_percent_coverage_attained': F(covered_weight, 81) >= F(19, 20),
            'production_contract': 'descriptive percentiles; no generic coverage claimed',
            'population_entropy_enclosure': [fraction_record(hlo), fraction_record(hhi)], 'rows': results,
            'finite_empirical_reference_absolute_window': fraction_record(window),
            'units': 'nats', 'scientific_scope': 'one fixed finite-law implemented percentile procedure; not generic calibrated inference',
            'input_sha256': hashlib.sha256(raw).hexdigest()}


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'one retained raw output path required')
    with Path(sys.argv[1]).open('rb') as stream:
        raw = stream.read(1048577)
    result = judge(raw)
    print(json.dumps(result, sort_keys=True), flush=True)
