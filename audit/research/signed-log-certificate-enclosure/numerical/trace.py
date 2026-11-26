"""Compare the six-table fixed-point loop with direct rounding at its supplied source."""
from fractions import Fraction
from hashlib import sha256
from math import ceil, floor, gcd
from pathlib import Path
import json
import runpy
import sys

ARITHMETIC = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"


def check(ok, message):
    if not ok:
        raise ValueError(message)


def observe(helper, n, d, bits):
    code = helper.__code__
    captured = []
    names = ("low", "high", "total_low", "total_high")
    def traced(frame, event, arg):
        if frame.f_code is code and event == "line":
            if frame.f_lineno in (225, 231):
                fd = frame.f_locals
                i = fd["i"] if frame.f_lineno == 225 else fd["count"]
                captured.append((i, [fd[name] for name in names]))
        return traced
    before = sys.gettrace()
    sys.settrace(traced)
    try:
        pair = list(helper(n, d, bits))
    finally:
        sys.settrace(before)
    return pair, captured


def ceildiv(a, b):
    return (a + b - 1) // b


def row_value(z):
    return [z.numerator, z.denominator]


def main(path):
    check(sha256(path.read_bytes()).hexdigest() == ARITHMETIC, "original source")
    original = runpy.run_path(str(path))
    helper = original["atanh_log_bounds"]
    signed = dict((str(v),original["ceildiv"](v,3)) for v in (-4,-1,0,1,4))
    check(list(signed.values()) == [-1,0,0,1,2], "signed ceiling controls")

    records = prefixes = nonscalar = 0
    inlowestterms = 0
    distinct = {}
    for bits in range(11):
        scale = 2**bits
        count = ceildiv(bits, 3)+1
        for d in range(1,34):
            for n in range(d//3+1):
                records += 1
                inlowestterms += int(gcd(n,d)==1)
                pair, captured = observe(helper,n,d,bits)
                if n==0:
                    check(pair == [0,0] and not captured, "actual zero shortcut")
                    nonscalar += 1
                    continue
                check([i for i,_ in captured] == list(range(count+1)), "actual iteration positions")
                x = Fraction(n,d)
                exact_sum = Fraction(0)
                lo,hi = floor(scale*x),ceil(scale*x)
                sum_lo = sum_hi = 0
                step_lo,step_hi=lo*lo//scale,ceildiv(hi*hi,scale)
                direct_power_total_lo=direct_power_total_hi=0
                for i,actual in captured:
                    prefixes += 1
                    fact = scale*x**(2*i+1)
                    sumfact = scale*exact_sum
                    direct_pow = [floor(fact),ceil(fact)]
                    direct_sum = [floor(sumfact),ceil(sumfact)]
                    check(actual == [lo,hi,sum_lo,sum_hi], "integer-source recurrence")
                    check(lo <= fact <= hi and sum_lo <= sumfact <= sum_hi, "prefix bounds")
                    alternate = direct_pow+direct_sum
                    for label,parts in [("power_different",slice(0,2)),("accumulator_different",slice(2,4))]:
                        if i>=1 and actual[parts]!=alternate[parts] and label not in distinct:
                            distinct[label]={"bits":bits,"n":n,"d":d,"i":i,"stored_state":actual,"directly_rounded_state":alternate,"exact_scaled_power":row_value(fact),"exact_scaled_partial_sum":row_value(sumfact)}
                    if i==count:
                        break
                    odd=2*i+1
                    exact_sum += 2*x**odd/odd
                    direct_power_total_lo += 2*direct_pow[0]//odd
                    direct_power_total_hi += ceildiv(2*direct_pow[1],odd)
                    sum_lo += 2*lo//odd
                    sum_hi += ceildiv(2*hi,odd)
                    lo=lo*step_lo//scale
                    hi=ceildiv(hi*step_hi,scale)
                check(pair == [sum_lo,sum_hi+1], "actual terminal allowance")
                wrong = [direct_power_total_lo,direct_power_total_hi+1]
                exact_terminal=[floor(sumfact),ceil(sumfact)+1]
                for name,other in [("terminal_with_directly_rounded_powers",wrong),("terminal_with_exact_accumulator",exact_terminal)]:
                    if other != pair:
                        check(other[0] <= sumfact <= other[1]-1,"alternate still encloses")
                        if name not in distinct:
                            distinct[name]={"bits":bits,"n":n,"d":d,"count":count,"source":pair,"alternate":other,"exact_scaled_partial_sum":row_value(sumfact)}
    check(len(distinct)==4,distinct)
    check(nonscalar==11*33, "all zero-input counts")
    fields={"input_records":records,"reduced_fraction_observations":inlowestterms,"zero_early_returns":nonscalar,"positive_prefixes":prefixes,
        "bounds":"0<=b<=10, 1<=d<=33, every 0<=n<=floor(d/3), 0<=i<=ceil(b/3)+1 including final positive-input state",
        "source_sha256":ARITHMETIC,"first_sorted_witnesses":distinct,
        "zero_control":{"input":[0,3,0],"original":[0,0],"wrong_but_contains_zero":[0,1]},
        "ceil_positive_divisor_3":signed}
    print(json.dumps(fields,indent=2,sort_keys=True))


if __name__=="__main__":
    main(Path(sys.argv[1]))
