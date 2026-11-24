"""Check the exact finite signs for the four-moment angular threshold."""
import argparse
from fractions import Fraction as Q
import importlib.util
import json
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOLERANCE = Q(1, 10**6)
GRID = 10**15
LAST = 40

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def coefficients(j):
    """Coefficient of the axial joint term and its proper-term multiplier."""
    require(type(j) is int and j >= 1, "positive integer index")
    k = Q(comb(2*j, j), 4**j * 2*j * (2*j-1))
    h = (2*(2*j+1)*Q(1,4)**j - (j+1)*Q(4,9)**j)
    return k, h

def threshold_sign(radius):
    """Return the sign only if the whole finite remainder interval has that sign."""
    require(isinstance(radius,Q) and 0 < radius < 1, "positive rational radius below one")
    s = radius*radius
    value = Q(0)
    for j in range(LAST, 0, -1):
        k,h = coefficients(j)
        value = s*(value + k*(int(j>4) - TOLERANCE*h))
    k,_ = coefficients(LAST+1)
    error = (1+2*TOLERANCE)*k*s**(LAST+1)/(1-s)
    lo,hi = value-error,value+error
    require(lo>0 or hi<0, "indeterminate threshold sign")
    return (1 if lo>0 else -1), (lo,hi)

def scaled(interval, scale):
    lo,hi = interval
    return [(lo*scale).__floor__(), (hi*scale).__ceil__()]

def threshold():
    low = Q(583,2048)*GRID
    high = Q(1197,4096)*GRID
    require(low.denominator == high.denominator == 1, "historical endpoints on grid")
    low,high = low.numerator,high.numerator
    signs = 0
    def at(i):
        nonlocal signs
        signs += 1
        require(signs<=52, "bisection budget")
        return threshold_sign(Q(i,GRID))
    left,left_interval = at(low)
    right,right_interval = at(high)
    require(left < 0 < right, "starting signs")
    while high-low>1:
        mid = (high+low)//2
        sign,iv = at(mid)
        if sign<0:
            low,left_interval = mid,iv
        else:
            high,right_interval = mid,iv
    return {"grid":GRID,"endpoints":[low,high],"N":LAST,"sign_decisions":signs,
            "F_times_10_to_26":[scaled(iv,10**26) for iv in (left_interval,right_interval)]}

def second_route():
    spec = importlib.util.spec_from_file_location("angular_closed_form", HERE/"closed_form.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def calculate():
    result = threshold()
    independent = second_route()
    independent_signs = [scaled(independent.threshold_interval(Q(i,GRID)),10**26) for i in result["endpoints"]]
    require(independent_signs==result["F_times_10_to_26"], "closed-form sign crosscheck")
    return {"schema":"angular-truncation-extremum-v1","critical_radius":result,
            "first_factor_counterexample":independent.counterexample()}

def distinct_keys(items):
    out = dict(items)
    require(len(out)==len(items), "duplicate JSON key")
    return out

def validate(data, expected):
    actual=json.loads(data,object_pairs_hook=distinct_keys)
    # Encode both sides to distinguish true/false from the integers 1/0.
    require(json.dumps(actual,sort_keys=True)==json.dumps(expected,sort_keys=True), "certificate mismatch")

def controls(expected):
    import copy
    hits = 0
    changes=[
      (("schema",),"other"), (("critical_radius","grid"),10**14),
      (("critical_radius","N"),39), (("critical_radius","sign_decisions"),44),
      (("critical_radius","endpoints"),list(reversed(expected["critical_radius"]["endpoints"]))),
      (("critical_radius","F_times_10_to_26"),[[811,812],[35403,35404]]),
      (("first_factor_counterexample","b"),[0,1]), (("first_factor_counterexample","B1"),[1,1]),
      (("first_factor_counterexample","G_times_10_to_15"),[1844,2123]),
    ]
    for keys,replacement in changes:
        bad=copy.deepcopy(expected)
        node=bad
        for key in keys[:-1]:node=node[key]
        node[keys[-1]]=replacement
        try:validate(json.dumps(bad),expected)
        except ValueError:hits+=1
        else:raise ValueError("undetected certificate mutation")
    duplicate=json.dumps(expected).replace('"schema":','"schema":"duplicate","schema":',1)
    try:validate(duplicate,expected)
    except ValueError:hits+=1
    else:raise ValueError("duplicate key admitted")
    return hits

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test",action="store_true",help="also reject ten altered certificates")
    args=parser.parse_args()
    expected=calculate()
    validate((HERE/"certificate.json").read_text(encoding="utf-8"),expected)
    output=dict(expected)
    if args.self_test:output["rejected_controls"]=controls(expected)
    print(json.dumps(output,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
