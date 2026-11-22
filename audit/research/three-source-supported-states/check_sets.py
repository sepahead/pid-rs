"""Finite controls on explicitly enumerated sets of indices."""
from fractions import Fraction
from itertools import combinations, product
import json
from math import prod


def require(ok, message):
    if not ok:
        raise ValueError(message)


def subsets(items):
    return tuple(frozenset(group) for size in range(len(items) + 1) for group in combinations(items, size))


COORDINATES = (0, 1, 2)
BRANCHES = subsets(COORDINATES)
FAMILIES = subsets(BRANCHES)
VALID = tuple(family for family in FAMILIES if family and all(family)
              and not any(a < b for a in family for b in family))
TOP = frozenset([frozenset(COORDINATES)])
STATES = tuple(product((0, 1), repeat=4))


def matches(family, row, key):
    return any(all(row[i] == key[i] for i in branch) for branch in family)


def count(table, key, family):
    # Keep each index, even when two indices have equal values.
    source_ids = {j for j,(row,_) in enumerate(table) if matches(family, row, key)}
    target_ids = {j for j,(row,_) in enumerate(table) if row[3] == key[3]}
    def measure(indices):
        return sum(table[j][1] for j in indices)
    return [measure(range(len(table))),measure(source_ids),measure(source_ids & target_ids),measure(target_ids)]


def rat(value):
    return [value.numerator,value.denominator]


def logical_check():
    counts = [0,0,0,0]
    for family in FAMILIES:
        for bits in product((False, True), repeat=3):
            for g in (False, True):
                source = any(all(bits[i] for i in branch) for branch in family)
                outside = g and source
                inside = any(all(g and bits[i] for i in branch) for branch in family)
                delta = int(inside) - int(outside)
                is_fault = frozenset() in family and not g
                require(delta == int(is_fault), "distributed-target identity")
                counts[0] += 1
                counts[1] += delta
                if family in VALID:
                    counts[2] += 1
                    counts[3] += delta
    require(counts == [4096,1024,288,0], "truth roster")
    return counts


def supported_laws():
    yield []
    for size in (1,2):
        for states in combinations(STATES,size):
            for weights in product((1,2),repeat=size):
                yield list(zip(states,weights))


def support_check():
    # Precompute only source membership. The weighted count is accumulated per finite law.
    memberships = {(key,row):[matches(family,row,key) for family in VALID] for key in STATES for row in STATES}
    totals = [0,0,0,0]
    top_index = VALID.index(TOP)
    for law in supported_laws():
        totals[0] += 1
        for key in STATES:
            joint = [0] * len(VALID)
            for row,w in law:
                if row[3] == key[3]:
                    joint = [v+w*e for v,e in zip(joint,memberships[key,row],strict=True)]
            cell = sum(w for row,w in law if row == key)
            require(joint[top_index] == min(joint) == cell, "minimum joint count at full node")
            require(all(v > 0 for v in joint) == (cell > 0), "simultaneous positivity")
            totals[1] += 1
            totals[2] += len(joint)
            totals[3] += int(cell > 0)
    require(totals == [513,8208,147744,992], "finite law scope")
    return totals


def fixture_checks():
    mixed = [((0,0,0,0),1),((1,0,1,1),1)]
    key = mixed[0][0]
    outside = count(mixed,key,frozenset([frozenset()]))[2]
    # The empty conjunction has no coordinate at which to check the target.
    inside = sum(w for row,w in mixed if all(row[3] == key[3] and row[i] == key[i] for i in ()))
    require([outside,inside] == [1,2], "empty branch counterexample")
    duplicate = [((0,0,0,0),2),((0,0,0,0),3),((1,1,1,1),1),((0,0,0,0),0)]
    duplicate_min = min(count(duplicate,duplicate[-1][0],a)[2] for a in VALID)
    outside_min = min(count(duplicate,(0,0,0,0),a)[2] for a in VALID)
    require([duplicate_min,outside_min] == [5,5], "zero-weight and outside representative")
    absent = (0,0,1,0)
    observed = [((0,0,0,0),1)]
    singleton_x = frozenset([frozenset([0])])
    one_node = [count(observed,absent,singleton_x),count(observed,absent,TOP)]
    require(one_node == [[1,1,1,1],[1,0,0,1]],"a single positive event does not imply positive joint support")

    signed_table = [((x,y,x^y,y),1) for x,y in product((0,1),repeat=2)]
    nodes = [frozenset([frozenset([0]),frozenset([1])]),singleton_x,frozenset([frozenset([1])])]
    expected = [[4,3,2,2],[4,2,1,2],[4,2,2,2]]
    signed = []
    for node,counts in zip(nodes,expected,strict=True):
        rows = [count(signed_table,row,node) for row,_ in signed_table]
        require(all(v == counts for v in rows),"four signed fixture rows")
        n,u,v,t = counts
        pos,neg = Fraction(n,u),Fraction(t,v)
        net = pos/neg
        require(net == Fraction(n*v,u*t),"equivalent local signed forms")
        signed.append({"counts":counts,"plus":rat(pos),"minus":rat(neg),"net":rat(net),"net_product":rat(net**4)})
    require([f["net"] for f in signed] == [[4,3],[1,1],[2,1]],"opposite signed directions")

    weighted = [((0,0,0,0),2),((1,1,1,1),1)]
    factors = []
    for row,w in weighted:
        n,u,v,t = count(weighted,row,TOP)
        require(t==v,"copy has zero misinformative part")
        factors.append((Fraction(n,u),w))
    cumulative_product = prod(q**w for q,w in factors)
    equally_weighted_factors = prod(q for q,_ in factors)
    require(cumulative_product == Fraction(27,4) and equally_weighted_factors == Fraction(9,2)
            and cumulative_product**2 != equally_weighted_factors**3,"key weighting")
    return {"empty_branch_joint_counts":[outside,inside],"duplicate_and_outside_minima":[duplicate_min,outside_min],
            "absent_singleton_and_top":one_node,"signed":signed,"weighted_copy_products":[rat(cumulative_product),rat(equally_weighted_factors)]}


def main():
    print(json.dumps({"truth":logical_check(),"support":support_check(),"fixtures":fixture_checks()},sort_keys=True))


if __name__ == "__main__":
    main()
