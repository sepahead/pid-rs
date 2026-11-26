"""Check the narrow true logarithm cell of a complete four-row counted law."""
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys


def require(value, label):
    if not value:
        raise ValueError(label)


def floor(value):
    return value.numerator//value.denominator


def upper(value):
    return -floor(-value)


def test_padding(lower, true, higher, a, b):
    require(lower <= true <= higher and a <= true <= b and higher-lower < 1, "padding hypotheses")
    require(a-1 <= floor(lower) <= upper(higher) <= b+1, "padded cell")


def run(path):
    require(sha256(path.read_bytes()).hexdigest() ==
            "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2", "original arithmetic")
    actual = runpy.run_path(str(path))
    n, m, p = 1706, 538, 2048
    rows = []
    for a in ("0", "1"):
        for target, count in ((a,m//2), ("x",(n-m)//2)):
            rows.append({"count":str(count),"source_states":[[a],["fixed"],["fixed"]],"target_state":[target]})
    cells, total, lengths = actual["typed_rows"](rows)
    require(total == n and len(cells) == 4, "table total and support")
    actual["reserve"](cells, total, lengths)
    plans = list(actual["projections"](actual["base_plans"](cells,total)))
    preflight = actual["preflight"](plans)
    selected = [(key, plan) for key,plan in plans if key == ("cumulative","net","01",(1,))]
    require(len(selected) == 1 and len(plans) == 108, "registered coordinate")
    q = actual["exact_product"](selected[0][1])
    require(q == (1 << m), "counted product 2^m")
    terms = 2100
    partial = sum((Fraction(1,k << k) for k in range(1,terms+1)),Fraction())
    tail = Fraction(1,(terms+1) << terms)
    scaled = Fraction((1 << p)*m,n)
    lo, hi = scaled*partial, scaled*(partial+tail)
    a = floor(lo)
    require(a < lo < hi < a+1, "strict unique 2048-bit cell")
    b = a+1
    fine = (Fraction(a,1 << p),Fraction(b,1 << p))
    require(fine[1]-fine[0] <= actual["MAX_WIDTH"], "fine cell width")
    replay = []
    for precision in actual["SCHEDULE"]:
        pair = actual["log_interval"](q,n,precision)
        require(not (fine[0] <= pair[0] <= pair[1] <= fine[1]), "unexpected unpadded containment")
        endpoints = [v*(1 << precision) for v in pair]
        require(all(v.denominator == 1 for v in endpoints), "output grid")
        if precision == p:
            require(a-1 <= endpoints[0] <= endpoints[1] <= b+1 and endpoints[1]-endpoints[0] == 2,
                    "one-unit padding at the true fine cell")
        replay.append({"precision":precision,"original_grid_indices":[str(v.numerator) for v in endpoints]})
    for lower, true, higher, left, right in [(Fraction(-1,3),0,Fraction(1,5),0,0),
                                              (Fraction(1,2),1,Fraction(6,5),1,2),
                                              (Fraction(3,4),1,Fraction(7,5),0,1)]:
        test_padding(lower,true,higher,left,right)
    try:
        test_padding(Fraction(-5,2),0,Fraction(1,5),0,0)
    except ValueError as error:
        require(str(error) == "padding hypotheses", "wrong wide-interval refusal")
    else:
        raise ValueError("accepted an invalid width premise")
    return {"n":n,"m":m,"counted_rows":rows,"all_original_plans":len(plans),
            "original_product_preflight":preflight,"true_interval_bits":p,"ordinary_log_terms":terms,
            "strict_true_cell_grid_indices":[str(a),str(b)],"padded_grid_indices":[str(a-1),str(b+1)],
            "zero_padding_rejections":replay,"rational_edge_examples":3,"width_controls":1}


if __name__ == "__main__":
    print(json.dumps(run(Path(sys.argv[1])),sort_keys=True,separators=(",",":")))
