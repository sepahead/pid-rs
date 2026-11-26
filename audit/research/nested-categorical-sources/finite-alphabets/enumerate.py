"""Exact cross-check on all labeled coarse partitions with one or two fine classes."""
from fractions import Fraction
import json


def require(condition, description):
    if not condition:
        raise ValueError(description)


def partitions(n):
    groups = []
    def visit(i):
        if i == n:
            yield tuple(groups)
            return
        bit = 1 << i
        for j in range(len(groups)):
            groups[j] |= bit
            yield from visit(i + 1)
            groups[j] ^= bit
        groups.append(bit)
        yield from visit(i + 1)
        groups.pop()
    yield from visit(0)


def product_counts(coarse, fine):
    num = den = 1
    split = [0] * len(fine)
    for x in coarse:
        margin = x.bit_count()
        for j, y in enumerate(fine):
            n = (x & y).bit_count()
            if n:
                split[j] += 1
                num *= (x | y).bit_count() ** n
                den *= margin ** n
    return num, den, any(k >= 2 for k in split)


def main():
    records = []
    for n in range(1, 9):
        whole = (1 << n) - 1
        fine_sets = [(whole,)] + [(mask, whole ^ mask) for mask in range(1, whole, 2)]
        count = failed = 0
        attained = [0, 0]
        minima = [None, None]
        for coarse in partitions(n):
            for fine in fine_sets:
                idx = len(fine) - 1
                num, den, split = product_counts(coarse, fine)
                require((num > den) == split, 'original directed event test')
                count += 1
                if not split:
                    continue
                failed += 1
                expected = (n**n, (n-1)**(n-1)) if idx == 0 else (2*n,n-1)
                excess = num*expected[1] - den*expected[0]
                require(excess >= 0, 'proposed lower bound')
                attained[idx] += excess == 0
                best = minima[idx]
                if best is None or num*best[1] < den*best[0]:
                    minima[idx] = (num, den)
        require(attained[0] == (0 if n==1 else 1 if n==2 else n), 'one-label equality count')
        require(attained[1] == (n*(n-1) if n>=3 else 0), 'two-label equality count')
        if n>=3:require(Fraction(*minima[1]) < Fraction(*minima[0]), 'one versus two labels')
        records.append({'n':n,'ordered_partitions':count,'failures':failed,'attaining_one_two':attained,
                        'minimum_one_two':[str(Fraction(*v)) if v else None for v in minima]})
    forward=product_counts((1,2,4),(3,4));reverse=product_counts((3,4),(1,2,4))
    require(forward[2] and not reverse[2] and Fraction(*forward[:2])==4 and Fraction(*reverse[:2])==1,'orientation')
    require(records[3]['minimum_one_two'][1]=='8/3' and Fraction(9,4)<Fraction(8,3),'third label needed at N=4')
    print(json.dumps({'records':records,'total':sum(x['ordered_partitions'] for x in records),'directional_control':['4','1']},sort_keys=True,indent=2))


if __name__ == '__main__':
    main()
