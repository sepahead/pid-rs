"""Compare all Shannon subset entropies and all categorical shared-exclusion atoms on two exact tables."""

from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import prod
import json

FIRST = ((1, 0, 0), (0, 1, 1), (0, 1, 0))
SECOND = ((0, 1, 0), (1, 0, 1), (0, 1, 0))


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def below(left, right):
    return all(any(low & high == low for low in left) for high in right)


def antichains():
    nodes = []
    for size in range(1, 8):
        for node in combinations(range(1, 8), size):
            if all(a & b not in (a, b) for a, b in combinations(node, 2)):
                nodes.append(node)
    return sorted(nodes, key=lambda top: sum(below(other, top) for other in nodes))


def outcomes(matrix):
    return {(i, 0, j, i): count for i, row in enumerate(matrix)
            for j, count in enumerate(row) if count}


def subset_entropy(table, mask):
    """Return exp(N H), with projected state counts and natural logarithms."""
    groups = Counter()
    for row, count in table.items():
        projected = tuple(v for column, v in enumerate(row) if mask & (1 << column))
        groups[projected] += count
    total = sum(table.values())
    return Fraction(total ** total, prod(n ** n for n in groups.values()))


def inspect(matrix):
    table = outcomes(matrix)
    total = sum(table.values())
    nodes = antichains()
    selected = [node for node in nodes if not below(node, (3,))]
    require(len(nodes) == 18 and len(selected) == 5 and total == 4, 'three sources and four counted rows')
    plus = {node: Fraction(1) for node in nodes}
    minus = plus.copy()
    for row, count in table.items():
        local = {}
        target = sum(w for z, w in table.items() if z[3] == row[3])
        for node in nodes:
            event = joint = 0
            for z, w in table.items():
                matched = sum(1 << i for i in range(3) if row[i] == z[i])
                if any(matched & group == group for group in node):
                    event += w
                    if z[3] == row[3]:
                        joint += w
            left, right = Fraction(total, event), Fraction(target, joint)
            for prior, (a, b) in local.items():
                if below(prior, node):
                    left /= a
                    right /= b
            local[node] = left, right
            plus[node] *= left ** count
            minus[node] *= right ** count
    nets = {node: plus[node] / minus[node] for node in nodes}
    magnitude = prod(max(nets[node], 1 / nets[node]) for node in selected)
    entropy = {mask: subset_entropy(table, mask) for mask in range(16)}
    A = entropy[7] / entropy[3]
    B = entropy[15] / entropy[11]
    gap = A * B / magnitude
    ring = {','.join(map(str, node)): [str(plus[node]), str(minus[node]), str(nets[node])] for node in nodes}
    return {'entropy': [str(entropy[i]) for i in range(16)], 'node_components': ring,
            'exp_4A': str(A), 'exp_4B': str(B), 'exp_4M': str(magnitude), 'exp_4G': str(gap)}


def main():
    first, second = map(inspect, (FIRST, SECOND))
    expected = []
    for mask in range(16):
        row = bool(mask & 9)
        col = bool(mask & 4)
        expected.append('256' if row and col else '64' if row or col else '1')
    require(first['entropy'] == second['entropy'] == expected, 'all sixteen entropy factors')
    require(first['exp_4A'] == first['exp_4B'] == second['exp_4A'] == second['exp_4B'] == '4', 'two entropies')
    require((first['exp_4M'],first['exp_4G']) == ('16/9','9'), 'first allocation')
    require((second['exp_4M'],second['exp_4G']) == ('1','16'), 'second allocation')
    require(first['node_components']['4'] == ['3','4','3/4'] and
            second['node_components']['4'] == ['4','4','1'], 'third singleton node')
    require(first['node_components']['5'][2] == '4/3' and
            second['node_components']['5'][2] == '1','joint first and third signed node')
    return {'definition': 'MGW arXiv:2002.03356v5. Every listed value is exp(4 times the averaged value in nats).',
            'matrices': [FIRST, SECOND], 'roles':'tuple (row, constant, column, row), with the last entry the target',
            'first':first, 'second':second}


if __name__ == '__main__':
    print(json.dumps(main(), indent=2, sort_keys=True))
