"""Check exact finite inequalities for three categorical sources and one target.

Each row has integer multiplicity. All exponentials below use the same
total-row scale. A logarithm or a floating-point comparison is unnecessary.
"""
from collections import Counter
from fractions import Fraction
from itertools import combinations, combinations_with_replacement, product
from math import prod
import json


def require(value, reason):
    if not value:
        raise ValueError(reason)


def included(subset, superset):
    return subset & superset == subset


def precedes(lower, upper):
    return all(any(included(a, b) for a in lower) for b in upper)


def carrier():
    nodes = []
    for size in range(1, 4):
        for family in combinations(range(1, 8), size):
            if not any(included(a, b) or included(b, a) for a, b in combinations(family, 2)):
                nodes.append(family)
    return sorted(nodes, key=lambda node: sum(precedes(other, node) for other in nodes))


NODES = carrier()
BELOW = {a: [b for b in NODES if b != a and precedes(b, a)] for a in NODES}
OUTSIDE = [a for a in NODES if not precedes(a, (3,))]
require(len(NODES) == 18 and set(OUTSIDE) == {(4,), (5,), (6,), (7,), (5, 6)}, 'wrong source lattice')


def entropy_product(table, retain):
    """Return exp(N H(S3 | retained columns)) for positive integer counts."""
    marginal = Counter()
    joint = Counter()
    for row, count in table.items():
        group = tuple(row[i] for i in retain)
        marginal[group] += count
        joint[(group, row[2])] += count
    return prod(Fraction(marginal[group], count) ** count for (group, _), count in joint.items())


def component_products(table):
    total = sum(table.values())
    n_target = Counter()
    for row, count in table.items():
        n_target[row[-1]] += count
    plus = dict.fromkeys(NODES, Fraction(1))
    minus = dict.fromkeys(NODES, Fraction(1))
    for ref, weight in table.items():
        mask_counts = Counter()
        same_target = Counter()
        for row, count in table.items():
            match = sum(1 << i for i in range(3) if row[i] == ref[i])
            mask_counts[match] += count
            if row[-1] == ref[-1]:
                same_target[match] += count
        for a in NODES:
            cover = [m for m in mask_counts if any(included(term, m) for term in a)]
            mass = sum(mask_counts[m] for m in cover)
            joint = sum(same_target[m] for m in cover)
            plus[a] *= Fraction(total, mass) ** weight
            minus[a] *= Fraction(n_target[ref[-1]], joint) ** weight
    for a in NODES:
        plus[a] /= prod(plus[b] for b in BELOW[a])
        minus[a] /= prod(minus[b] for b in BELOW[a])
    return plus, minus


def lower_factor(total, alphabet):
    split = total - alphabet + 2
    a = split // 2
    b = split - a
    return Fraction((a + 1) * (b + 1), a * b) ** 2


def check(table):
    total = sum(table.values())
    plus, minus = component_products(table)
    alphabet = len({row[2] for row in table})
    require(all(v >= 1 for v in (*plus.values(), *minus.values())), 'negative unsigned component')
    ea = entropy_product(table, (0, 1))
    eb = entropy_product(table, (0, 1, 3))
    require(ea == prod(plus[a] for a in OUTSIDE) and eb == prod(minus[a] for a in OUTSIDE), 'wrong outside budget')
    em = prod(max(plus[a] / minus[a], minus[a] / plus[a]) for a in OUTSIDE)
    gap = ea * eb / em
    require(gap == prod(min(plus[a], minus[a]) ** 2 for a in OUTSIDE), 'wrong signed deficit')
    require((gap == 1) == (eb == 1), 'equality characterization')
    if eb > 1:
        require(plus[(4,)] > 1 and minus[(4,)] > 1, 'missing overlap at singleton three')
        require(gap >= lower_factor(total, alphabet), 'count bound')
    return eb, gap


def balanced_example(total, alphabet):
    s = total - alphabet + 2
    a, b = s // 2, (s + 1) // 2
    table = Counter({(0, 0, 0, 0): 1, (0, 0, 1, 0): 1})
    for label, remaining in enumerate([a - 1, b - 1] + [1] * (alphabet - 2)):
        if remaining:
            # Each further (first source, target) stratum has only one third-source label.
            table[(label + 1, 0, label, label + 1)] = remaining
    return table


def main():
    cells = list(product(range(2), repeat=4))
    groups = {}
    for total in range(1, 5):
        stats = Counter()
        positive = []
        for sample in combinations_with_replacement(cells, total):
            eb, gap = check(Counter(sample))
            stats['tables'] += 1
            if eb > 1:
                stats['conflicting'] += 1
                positive.append(gap)
        groups[total] = dict(stats, least_positive_exponential=str(min(positive)) if positive else None)
    require([groups[n]['tables'] for n in range(1, 5)] == [16, 136, 816, 3876], 'exhaustive denominator')
    sharp = 0
    for total in range(2, 19):
        for alphabet in range(2, total + 1):
            example = balanced_example(total, alphabet)
            require(sum(example.values()) == total and len({r[2] for r in example}) == alphabet, 'example population')
            eb, gap = check(example)
            require(eb > 1 and gap == lower_factor(total, alphabet), 'integer minimum not attained')
            sharp += 1
    # The pairwise-only assumption fails on four equally probable states.
    xor_rows = Counter((u ^ v, 0, (u, v), (u ^ v, u)) for u, v in product(range(2), repeat=2))
    require(entropy_product(xor_rows, (0, 1)) == 2**4 and entropy_product(xor_rows, (0, 1, 3)) == 1, 'parity witness')
    require(sum(k for (x, _, uv, _), k in xor_rows.items() if x == 0 or uv == (0, 0)) == 2, 'true match union')
    print(json.dumps({'binary_tables': groups, 'total_tables': sum(v['tables'] for v in groups.values()),
                      'explicit_sharp_witnesses': sharp, 'largest_witness_total': 18,
                      'parity_actual_union': '1/2', 'pairwise_product_prediction': '5/8'}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
