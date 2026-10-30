"""Certified chain lower bounds on allocation movement for the 30 published study laws.

The seven coalition mutual-information changes l_B = I(S_B;T) - I(S'_B;T) constrain the
atom-change vector d by A d = l, where row B of A selects the atoms below the node {B}.
The smallest L1 norm over those vectors equals the largest total variation of l along a
maximal coalition chain {i} < {i,j} < {1,2,3}, with l of the empty set taken as zero
(ADDENDUM-2026-10-30.md, section 2). Each chain and sign choice gives an integer dual witness
y = (s1-s2) e_{i} + (s2-s3) e_{ij} + s3 e_{123}; this script checks |(A^T y)_alpha| <= 1 on all
18 nodes in exact arithmetic, so y . l <= D. Evaluating y . l at the saved outward endpoints
of each l_B gives a rational lower bound on D that uses no floating point. Nothing is written.
"""

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
CAMPAIGN = ROOT.parent / 'evidence' / 'campaign'
REPORT_SHA256 = 'ad0f9781265c7bdf3a9eadae04c063428e4507f946644d0cbbc42b240521bc2b'


def require(condition, message):
    if not condition:
        raise SystemExit(f'chain lower certificate: {message}')


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f'duplicate JSON member {key!r}')
            result[key] = value
        return result

    def constant(token):
        raise SystemExit(f'chain lower certificate: non-standard JSON constant {token}')

    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)


def carrier():
    """Antichains of nonempty subsets of three sources, as tuples of bit masks."""
    nodes = []
    for choice in range(1, 128):
        upset = {mask for mask in range(1, 8) if choice >> (mask - 1) & 1}
        if all(other in upset for mask in upset for other in range(1, 8) if mask & other == mask):
            nodes.append(tuple(sorted(m for m in upset if not any(o != m and o & m == o for o in upset))))
    require(len(nodes) == 18, 'carrier does not have 18 nodes')
    return nodes


def below_single(node, coalition):
    """True when node <= {coalition}: some branch of the node is contained in the coalition."""
    return any(branch & coalition == branch for branch in node)


def witnesses(nodes):
    """All chain/sign dual witnesses, each checked for exact dual feasibility."""
    result = []
    for i in (1, 2, 4):
        for j in (1, 2, 4):
            if j == i:
                continue
            pair = i | j
            for s1 in (-1, 1):
                for s2 in (-1, 1):
                    for s3 in (-1, 1):
                        y = {i: s1 - s2, pair: s2 - s3, 7: s3}
                        for node in nodes:
                            value = sum(weight for mask, weight in y.items() if below_single(node, mask))
                            require(abs(value) <= 1, f'dual witness {y} is infeasible at node {node}')
                        result.append(y)
    require(len(result) == 48, 'witness roster is not 48')
    return result


def main():
    require(len(sys.argv) == 1, 'takes no arguments and writes nothing')
    nodes = carrier()
    duals = witnesses(nodes)
    report_raw = (CAMPAIGN / 'REPORT.json').read_bytes()
    require(hashlib.sha256(report_raw).hexdigest() == REPORT_SHA256, 'campaign index digest differs')
    report = strict_json(report_raw)
    rows = []
    for recording in report['recordings']:
        for pointer in recording['laws']:
            raw = (CAMPAIGN / pointer['path']).read_bytes()
            require(len(raw) == pointer['bytes'] and hashlib.sha256(raw).hexdigest() == pointer['sha256'],
                    'law identity')
            law = strict_json(raw)
            intervals = {}
            for row in law['coordinates']:
                if row['stage'] == 'cumulative' and row['component'] == 'net' and len(row['branches']) == 1:
                    mask = row['branches'][0]
                    before = [Fraction(x) for x in row['before']['interval']]
                    after = [Fraction(x) for x in row['after']['interval']]
                    require(mask not in intervals and before[0] <= before[1] and after[0] <= after[1],
                            'coalition interval roster')
                    intervals[mask] = (before[0] - after[1], before[1] - after[0])
            require(sorted(intervals) == list(range(1, 8)), 'seven coalition intervals')
            best = max(sum(w * (intervals[m][0] if w > 0 else intervals[m][1]) for m, w in y.items() if w)
                       for y in duals)
            allocation = [Fraction(x) for x in law['allocation_interval']]
            saved_cut = Fraction(law['mi_cut_lower_nats'])
            require(best <= allocation[1], 'certified lower bound exceeds the saved allocation enclosure')
            rows.append({'recording': recording['metadata']['recording'], 'law': law['law'],
                         'certified_chain_lower_nats': f'{float(best):.12f}',
                         'saved_cut_lower_nats': f'{float(saved_cut):.12f}',
                         'improves_saved_cut': best > saved_cut,
                         'allocation_upper_nats': f'{float(allocation[1]):.12f}'})
    require(len(rows) == 30, 'all-law roster')
    print(json.dumps({'status': 'PASS', 'scope': 'exact dual witnesses on saved outward intervals; '
                      'a lower bound on these 30 empirical laws, not a population or calibration claim',
                      'witnesses': len(duals), 'laws': rows,
                      'improved_laws': sum(row['improves_saved_cut'] for row in rows)}, indent=1))


if __name__ == '__main__':
    main()
