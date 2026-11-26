"""Verify the fixed-pair sharpness examples with exact MGW probability products."""
from collections import Counter
from fractions import Fraction
from itertools import combinations, product
from math import prod
import json


def require(truth, message):
    if not truth:
        raise ValueError(message)


def below(left, right):
    """Every named right clause contains some left clause."""
    return all(any(first & last == first for first in left) for last in right)


def antichains():
    masks = range(1, 8)
    nodes = [node for n in range(1, 8) for node in combinations(masks, n)
             if not any(a & b in (a, b) for a, b in combinations(node, 2))]
    ordered = sorted(nodes, key=lambda node: sum(below(other, node) for other in nodes))
    require(len(ordered) == 18, 'complete three-source family inventory')
    return ordered


NODES = antichains()
OUTSIDE = [n for n in NODES if not below(n, (3,))]
require(set(OUTSIDE) == {(4,), (5,), (6,), (5, 6), (7,)}, 'five-position cut')


def marginal(table, function):
    answer = Counter()
    for key, count in table.items():
        answer[function(key)] += count
    return answer


def finite_products(weights, length):
    """The weight of (u,v) is an integer. S=(x, constant, (u,v)), T=(x,u)."""
    require(type(length) is int and length > 0, 'positive number of uniform symbols')
    require(bool(weights) and all(type(w) is int and w > 0 for w in weights.values()),
            'nonempty occupied weighted cells')
    total = sum(weights.values())
    n = length * total
    support = len(weights)
    u_counts = marginal(weights, lambda p: p[0])
    rows = [((x, 0, z), (x, z[0]), w) for x in range(length) for z, w in weights.items()]
    aggregate = {node: Fraction(1) for node in NODES}
    factors = [Fraction(1)] * 3
    for source, target, weight in rows:
        target_mass = sum(w for _, t, w in rows if t == target)
        local = {}
        for node in NODES:
            in_union = both = 0
            for candidate, t, w in rows:
                matched = any(all(a == b for i, (a, b) in enumerate(zip(source, candidate))
                                  if mask & 2**i) for mask in node)
                if matched:
                    in_union += w
                    if t == target:
                        both += w
            cumulant = Fraction(both*n, in_union*target_mass)
            below_product = prod(value for key, value in local.items() if below(key, node))
            local[node] = cumulant / below_product
            aggregate[node] *= local[node]**weight
        z = source[2]
        r = Fraction(length*total, total + (length-1)*weights[z])
        a = Fraction(total, weights[z])
        delta = Fraction(total, u_counts[z[0]])
        expected = {(1, 4): r, (1,): length/r, (4,): delta/r, (5,): r}
        require(all(local[node] == expected.get(node, 1) for node in NODES),
                'all eighteen original local signed products')
        for i, value in enumerate([a, delta, r]):
            factors[i] *= value**weight
    a, delta, r = factors
    b = a / delta
    one = Fraction(1)
    mass = prod(max(aggregate[key], 1/aggregate[key]) for key in OUTSIDE)
    require(prod(aggregate[key] for key in OUTSIDE) == delta, 'five signed products')
    require(mass == r*max(delta/r, r/delta), 'finite absolute mass after averaging')
    deficit = (a*a/delta) / mass
    require(deficit == min(b, a/r)**2, 'exact deficiency')
    jensen = Fraction(length + support-1, length)**(2*n)
    require(one <= deficit <= jensen, 'upper bound at fixed length and support')
    require((deficit == one) == (b == one), 'finite attainment if and only if deterministic conditional V')
    if length == 1:
        require(r == one and mass == delta, 'singleton uniform source')
    return {'n': n, 'cells':len(rows), 'm':support, 'length':length,
            'signed':delta, 'mass': mass, 'delta':delta, 'r':r, 'b':b,
            'deficit': deficit, 'upper':jensen}


def pairwise_control():
    rows = [(u^v, u, v) for u, v in product(range(2), repeat=2)]
    for a, b in combinations(range(3), 2):
        require(len({(p[a],p[b]) for p in rows}) == 4, 'every pair is independent')
    given_x = prod(sum(p[0] == x for p in rows) for x, _, _ in rows)
    separate = prod(4 for _ in rows)
    require(given_x == 16 and separate == 256, 'distinct entropy products at sample size four')
    return [given_x, separate]


def main():
    fixed = {'one_cell':{(0,1):5}, 'copied_binary':{(0,0):1,(1,1):2},
             'fair_independent':{p:1 for p in product(range(2),repeat=2)},
             'dependent_three_cells':{(0,0):2,(0,1):1,(1,1):3},
             'unequal_four_cells':{(0,0):1,(0,1):2,(1,0):3,(1,1):6},
             'constant_u_skewed':{(0,0):1,(0,1):3,(0,2):5}}
    cases = [(k, w, l) for k,w in fixed.items() for l in (1,2,3,4,7)]
    for l, m in product((1,2,3,5,7), (1,2,3,5,7)):
        cases.append(('jensen_attainer', {(0,v):1 for v in range(m)},l))
    accepted = 0; local_rows = 0; jensen_equal = 0; positive = 0; finite_zero = 0
    for label,w,l in cases:
        result = finite_products(w,l)
        accepted += 1; local_rows += result['cells']; positive += result['b']>1; finite_zero += result['b']==1
        if label=='jensen_attainer':
            require(result['deficit']==result['upper'], 'sharp uniform V and constant U')
            jensen_equal += 1
            if l==len(w):
                require(result['deficit']==Fraction(2*l-1,l)**(2*result['n']), 'growing support')
    example=finite_products({(0,0):1,(0,1):1},2)
    require(example['deficit'] > Fraction(3,2)**example['n'], 'one instead of two is too small')
    require(example['r'] > example['delta'] and example['deficit'] > 1, 'signed atom is negative and finite shortfall positive')
    equal=finite_products({(0,0):1,(1,1):1},3)
    require(equal['mass']==equal['delta'] and equal['delta']>1, 'nonconstant attaining example with B=0')
    return {'fixed_family_cases':accepted,'occupied_local_rows':local_rows,'exact_local_atoms_checked':18*local_rows,
            'positive_conditional_entropy_cases':positive,'zero_conditional_entropy_cases':finite_zero,
            'sharp_uniform_attainers':jensen_equal,'independent_pairwise_only_counterexample_products':pairwise_control(),
            'fair_constant_U_L2':{k:str(example[k]) for k in ('n','r','delta','mass','deficit')},
            'scope':'Exact finite categorical signed pointwise and averaged MGW products. All rows construct the distribution. No sampling or external measurements.'}

if __name__=='__main__':
    print(json.dumps(main(),indent=2,sort_keys=True))
