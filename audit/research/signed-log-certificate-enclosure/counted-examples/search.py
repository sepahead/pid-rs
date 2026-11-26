"""Search the fixed two-state copy family, retaining exact original-source receivers."""
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

SOURCE = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"
LIMIT = 3000
INTERNAL = 2176

def load(path):
    if sha256(path.read_bytes()).hexdigest() != SOURCE:
        raise ValueError("source")
    spec = importlib.util.spec_from_file_location("original_arithmetic",path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def multiplied_logs(source):
    low = [0]*(LIMIT+1)
    high = low.copy()
    lower_two,upper_two = source.atanh_log_bounds(1,3,INTERNAL)
    for n in range(1,LIMIT+1):
        exponent = n.bit_length()-1
        power = 1<<exponent
        lo,hi = source.atanh_log_bounds(n-power,n+power,INTERNAL)
        low[n] = n*(lo+exponent*lower_two)
        high[n] = n*(hi+exponent*upper_two)
    return low,high

@lru_cache(maxsize=LIMIT+1)
def self_power(n):
    return n**n

def find(source,p,low,high):
    screened = computed = 0
    no_preflight = []
    for n in range(2,LIMIT+1):
        divisor = n << (INTERNAL-p)
        margin = divisor//2048
        for k in range(1,n//2+1):
            j = n-k
            screened += 1
            lower = low[n]-high[k]-high[j]
            upper = high[n]-low[k]-low[j]
            rest = lower % divisor
            if rest > margin and rest+upper-lower < divisor-margin:
                continue
            computed += 1
            q = Fraction(self_power(n),self_power(k)*self_power(j))
            returned = source.log_interval(q,n,p)
            endpoints = [v*(1<<p) for v in returned]
            if any(v.denominator != 1 for v in endpoints):
                raise ArithmeticError("non-grid endpoints")
            if endpoints[1]-endpoints[0] != 2:
                continue
            names = ("a","b")
            rows = [{"count":str(count),"target_state":[name],"source_states":[[name]]*3}
                    for name,count in zip(names,(k,j))]
            cells,total,lengths = source.typed_rows(rows)
            source.reserve(cells,total,lengths)
            plans = list(source.projections(source.base_plans(cells,total)))
            try:
                source.preflight(plans)
            except source.ArithmeticReject as failure:
                no_preflight.append([n,k,str(failure)])
                continue
            original_q, = [source.exact_product(plan) for key,plan in plans
                            if key[:3] == ("cumulative","net","01")]
            if original_q != q or source.log_interval(original_q,total,p) != returned:
                raise ArithmeticError("selected source receiver")
            return {"p":p,"screened":screened,"computed":computed,"searched_through":n-1,
                    "unadmitted":no_preflight,"result":{"N":n,"k":k,
                    "grid":list(map(int,endpoints))}}
    return {"p":p,"screened":screened,"computed":computed,"searched_through":LIMIT,
            "unadmitted":no_preflight,"result":None}

def main():
    source = load(Path(sys.argv[1]))
    low,high = multiplied_logs(source)
    cases = []
    for p in source.SCHEDULE:
        cases.append(find(source,p,low,high))
    print(json.dumps({"precisions":source.SCHEDULE,"search":cases,
                      "reference_units_exponent":INTERNAL},indent=2,sort_keys=True))

if __name__ == "__main__":
    main()
