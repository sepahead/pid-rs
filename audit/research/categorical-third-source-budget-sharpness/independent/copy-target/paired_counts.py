"""Compare all Shannon subset entropies and selected categorical atoms in two four-cell tables."""
import argparse
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import importlib.util
from itertools import combinations
import json
from math import prod
from pathlib import Path

EXPECTED_REFERENCE = "00b52c8e5e514d3bac05190352489aa6954814e06efff0b321cacafdb7122940"
FIRST = ((1, 0, 0), (0, 1, 1), (0, 1, 0))
SECOND = ((0, 1, 0), (1, 0, 1), (0, 1, 0))
LABELS = ("S1", "S2", "S3", "T")


def require(test, reason):
    if not test:
        raise ValueError(reason)


def load_reference(path):
    require(sha256(path.read_bytes()).hexdigest() == EXPECTED_REFERENCE, "unexpected reference")
    spec = importlib.util.spec_from_file_location("finite_budget_reference", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cells(matrix):
    return [
        (x, 0, w, x)
        for x, row in enumerate(matrix)
        for w, count in enumerate(row)
        for _ in range(count)
    ]


def entropy(histogram):
    """Return exp(N H), using integer-labelled counts."""
    total = sum(histogram.values())
    return Fraction(total**total, prod(count**count for count in histogram.values()))


def read_table(rows, exact):
    require(len(rows) == len(set(rows)) == 4, "four occupied unit cells")
    require(all(row[1] == 0 and row[0] == row[3] for row in rows), "constant source and copy target")
    marginals = [Counter(row[j] for row in rows) for j in (0, 2)]
    require(all(h == {0: 1, 1: 2, 2: 1} for h in marginals), "labelled row and column counts")
    h = {}
    for size in range(5):
        for js in combinations(range(4), size):
            name = ",".join(LABELS[j] for j in js) or "empty"
            frequencies = Counter(tuple(row[j] for j in js) for row in rows)
            h[name] = entropy(frequencies)
    direct = exact.observe(dict(Counter(rows)))
    all_five = {}
    for node in exact.OUTSIDE:
        p, q = direct["averages"][node]
        all_five[node] = p/q
    # Alternative two-source formula. Each reference target makes its first-source match sure.
    union = [sum(other[0] == r[0] or other[2] == r[2] for other in rows) for r in rows]
    r = prod(Fraction(4, good) for good in union)
    joint_mi = h["S1"] * h["S3"] / h["S1,S3"]
    complementary = {(4,): joint_mi/r, (5,): r/joint_mi, (6,): 1, (5,6): 1, (7,): 1}
    require(all_five == complementary, "five signed means from two routes")
    abs_mass = prod(max(f, 1/f) for f in all_five.values())
    a = h["S1,S2,S3"]/h["S1,S2"]
    b = h["S1,S2,S3,T"]/h["S1,S2,T"]
    require(a == b == 4 and (direct["A"],direct["B"]) == (a,b), "conditional entropies")
    require(direct["M"] == abs_mass and direct["gap"] == a*b/abs_mass, "full gap")
    require(direct["local_component_count"] == 144, "two components at all 18 nodes in four rows")
    return {
        "entropy_factors": {k: str(v) for k,v in h.items()},
        "match_counts": union,
        "x_w_mutual_information_factor": str(joint_mi),
        "shared_x_or_w_factor": str(r),
        "five_signed_factors": {str(k): str(v) for k,v in all_five.items()},
        "exp_four_A": str(a), "exp_four_B": str(b), "exp_four_M": str(abs_mass),
        "exp_four_G": str(direct["gap"]), "local_components": direct["local_component_count"],
    }


def check_pair(first, second, exact):
    one,two = read_table(first,exact), read_table(second,exact)
    require(one["entropy_factors"] == two["entropy_factors"] and len(one["entropy_factors"]) == 16, "all 16 entropies")
    require(set(one["entropy_factors"].values()) == {"1","64","256"}, "entropy scale")
    require(sorted(one["match_counts"]) == [1,2,2,3] and two["match_counts"] == [2]*4, "different event intersections")
    require((one["exp_four_M"],one["exp_four_G"]) == ("16/9","9"), "first exact gap")
    require((two["exp_four_M"],two["exp_four_G"]) == ("1","16"), "second exact gap")
    require(exact.minimum_factor(4,3)==9, "first case attains the sharp positive lower bound")
    return one,two


def hostile(exact, first, second, one):
    pairs=[
        ("swapped tables",second,first),
        ("missing observation",first[:-1],second),
        ("additional observation",first+[first[0]],second),
        ("moved cell",first[:-1]+[(2,0,2,2)],second),
        ("constant target",[(x,y,z,0) for x,y,z,_ in first],second),
    ]
    rejected = []
    for name,left,right in pairs:
        try:
            check_pair(left,right,exact)
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError("incorrect pair accepted "+name)
    require(Fraction(one["exp_four_A"])/Fraction(one["exp_four_B"])==1 != Fraction(one["exp_four_M"]), "substituting conditional information for absolute mass")
    rejected.append("conditional mutual information for absolute mass")
    require(Fraction(one["exp_four_G"])**4!=9, "count-cleared factor is not exp(G)")
    rejected.append("missing count exponent")
    return rejected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference",type=Path,required=True)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    exact=load_reference(args.reference)
    a,b=cells(FIRST),cells(SECOND)
    one,two=check_pair(a,b,exact)
    output={"counts":[FIRST,SECOND],"units":"Every factor is exp(4 times the quantity in nats).",
            "first":one,"second":two}
    if args.self_test:
        output["refused"] = hostile(exact,a,b,one)
    print(json.dumps(output,indent=2,sort_keys=True))


if __name__=="__main__":
    main()
