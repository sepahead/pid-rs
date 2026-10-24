"""Frozen finite checks and disconfirming controls; never a generic proof."""

import importlib.util
import json
from pathlib import Path
from fractions import Fraction
import sys

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('comparison_adapter', ROOT / 'adapter_v2.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)
C = A.C
V1 = A.load('preserved_candidate_v1', ROOT / 'candidate.py',
            '08e5014c73d01b776c1b073e54a04e9d11b66c78cac94a2aca846b9f13159b13')


def run():
    completed = []
    fixture_laws = [
        {(0,0,0,0): 1, (1,1,1,1): 1},
        {(0,0,1,0): 1, (0,1,1,1): 99},
        {(x,y,z,t): 1 for x in (0,1) for y in (0,1) for z in (0,1) for t in (0,1)}
    ]
    for law in fixture_laws:
        old, new = V1.evaluate(law, 2), C.evaluate(law, 2)
        C.require(old['nodes'] == new['nodes'], 'v1/v2 key drift')
        for stage in ('cumulative','atoms'):
            for component in ('plus','minus','net'):
                for a,b in zip(old[stage][component],new[stage][component]):
                    C.require(V1.exact_product(a) == C.exact_product(b), 'v1/v2 product drift')
    for value in (1,2,3,4,32772,65535,262144):
        terms=C.factors([(Fraction(value,3),5),(Fraction(3,value),2)])
        C.require(V1.exact_product(terms)==C.exact_product(terms),'prime cancellation drift')
    completed.append('v1/v2 exact product agreement before original control roster')
    constant = {(x, y, z, 0): 1 for x in (0, 1) for y in (0, 1) for z in (0, 1)}
    value = C.evaluate(constant, 4)
    A.compare(constant, 4, value)
    C.require(all(C.exact_product(f) == 1 for f in value['atoms']['net']), 'constant target')
    completed.append('constant target / absent classes / all54 reference products')
    heads = ((0, 0), (1, 1))
    for n in (2, 100, 10000):
        law = {(0, 0, 1, 0): 1, (0, 1, 1, 1): n-1}
        before = C.evaluate(law, 2)
        after = C.evaluate(C.transformed(law, heads), 2)
        entropy_terms = ((Fraction(n), n), (Fraction(n-1), -(n-1)))
        entropy_product = C.exact_product(entropy_terms)
        for val, expected_node in ((before, (2,)), (after, (2, 4))):
            for i, key in enumerate(val['nodes']):
                C.require(C.exact_product(val['atoms']['net'][i]) ==
                          (entropy_product if key == expected_node else 1), 'recoverability witness atoms')
                C.require(C.exact_product(val['atoms']['minus'][i]) == 1, 'witness minus')
        result = C.compare_laws(law, heads, 2, A.compare)
        C.require(result['lost_information']['sign'] == 0
                  and result['tuple_recovery_entropy']['sign'] == 0
                  and result['source_partition_preserved'] == [True, True, False], 'witness meanings')
        exact = C.interval(C.combine([(entropy_terms, 2)]), n)
        observed = tuple(Fraction(v) for v in result['allocation_interval'])
        C.require(max(exact[0], observed[0]) <= min(exact[1], observed[1]), 'witness enclosures')
        completed.append('recoverable tuple / D=2h / exact keys / delta=1/'+str(n))
    parity = {(x, y, z, x ^ y ^ z): 1 for x in (0, 1) for y in (0, 1) for z in (0, 1)}
    C.compare_laws(parity, heads, 2, A.compare)
    completed.append('parity / signed net atoms / full18 reconstruction')
    zero = {(0, 0, 0, 0): 3, (1, 1, 1, 1): 2}
    result = C.compare_laws(zero, heads, 2, A.compare)
    C.require(result['allocation_interval'] == ['0', '0'] and result['tail'] == '0', 'zero tail')
    completed.append('zero tail / unchanged full law')
    collision = {(0, 0, 0, 0): 49, (1, 1, 1, 1): 50, (0, 0, 1, 1): 1}
    result = C.compare_laws(collision, heads, 2, A.compare)
    q = C.transformed(collision, heads)
    C.require(q[(0, 0, 0, 1)] == 1 and result['tail'] == '1/100', 'created support')
    completed.append('support creation / exactTV / retainedXT')
    # Separately exercised mutants; scientific calls always use correct default events.
    A.refusal(lambda: A.compare(parity, 2, C.evaluate(parity, 2, wrong_or=True)))
    completed.append('within-branch OR mutant rejected by independent reference')
    bad = C.evaluate(collision, 2)
    bad['atoms']['net'] = list(reversed(bad['atoms']['net']))
    A.refusal(lambda: A.compare(collision, 2, bad))
    completed.append('reversed atom transport rejected')
    # Use an additional row that actually collides with an occupied destination.
    extended = dict(collision); extended[0, 0, 0, 1] = 4
    wrong = {}
    for (x, y, z, t), count in extended.items():
        yy, zz = (y, z) if (y, z) in heads else heads[0]
        wrong[x, yy, zz, t] = count
    C.require(sum(wrong.values()) != sum(extended.values()), 'collision-loss mutant not detected')
    old_xt = {(x,t): sum(c for z,c in collision.items() if (z[0],z[3]) == (x,t))
              for x,t in {(z[0],z[3]) for z in collision}}
    wrong_x = {(1-z[0],z[3]): c for z,c in collision.items()}
    wrong_t = {(z[0],1-z[3]): c for z,c in collision.items()}
    C.require(old_xt != wrong_x and old_xt != wrong_t, 'retained/target change witnesses')
    C.require(Fraction(sum(abs(collision.get(k,0)-q.get(k,0)) for k in collision.keys()|q.keys()), 100)
              != Fraction(1,100), 'wrong TV control')
    completed.append('collision overwrite, retained/target change and missing-half TV witnesses detected')
    for law in ({}, {(0,0,0,0): True}, {(0,0,0,0): -1}, {(0,0,0,0): 0},
                {(2,0,0,0): 1}, {(0,0,0,2): 1}, {(0,0,0,0): Fraction(1,2)}):
        A.refusal(lambda law=law: C.evaluate(law, 2))
    A.refusal(lambda: C.exact_product(((Fraction(2), C.MAX_BITS+1),)))
    A.refusal(lambda: C.logarithm(Fraction(0)))
    A.refusal(lambda: C.transformed(collision, ((0,0), (0,0))))
    completed.append('malformed/count/domain/bit-budget/head refusals')
    for base in (Fraction(1,2), Fraction(1,3), Fraction(2), Fraction(3)):
        lo, hi = C.logarithm(base); a,b = C.logarithm(1/base)
        C.require(lo+a <= 0 <= hi+b, 'negative range-reduction sign')
    completed.append('reciprocal-log outward sign consistency')
    return {'schema':'three-source-controls-v1','status':'PASS','checks':completed,
            'limits':'finite controls; no universal theorem, calibration or Rust refinement'}


if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True, separators=(',',':')))

