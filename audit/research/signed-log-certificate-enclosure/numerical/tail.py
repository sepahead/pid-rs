"""Exact fractions for the logarithm tail at the worst admissible input."""
from fractions import Fraction as F
import json


def require(test, description):
    if not test:
        raise ValueError(description)


def odd_sum(x, count):
    return sum((2 * x**(2*i+1) / (2*i+1) for i in range(count)), F(0))


def enclose(x, first_omitted, through):
    require(0 <= x <= F(1,3) and 0 <= first_omitted <= through, 'positive domain and valid orders')
    partial = odd_sum(x, through) - odd_sum(x, first_omitted)
    tail = 2 * x**(2*through+1) / ((2*through+1)*(1-x*x))
    return partial, partial + tail


def frac(r):
    return [r.numerator, r.denominator]


def floor(x):
    return x.numerator // x.denominator


def main():
    x = F(1,3)
    scale = 2**80
    a,b = enclose(x, 1, 32)
    low,up = floor(scale*a), -floor(-scale*b)
    require(up == low+1 and F(low,scale) < a < b < F(up,scale), 'strict consecutive 80-bit endpoints')
    checked=0
    for bits in range(32):
        j = (bits+2)//3+1
        for z in (F(0),F(1,30000),F(1,10),F(1,4),x):
            lo,hi = enclose(z,j,j+24)
            lib = 2*z**(2*j+1)/(1-z*z)
            stronger = lib/(2*j+1)
            source = F(3,4)*F(1,8)**j/(2*j+1)
            require(0 <= lo <= hi <= stronger <= source < F(1,2**bits), 'exact bounds')
            require(2**bits*hi <= (F(1,12)*F(8,9)**((bits+2)//3)), 'library cap')
            if bits!=0 or z!=x:
                require(2**bits*hi<a, 'strict other entries')
            checked+=1
    require(enclose(x,0,1)[0]*2>1,'floor schedule fails at b=1')
    require(enclose(x,0,1)[0]*8>1,'two fewer terms fails at b=3')
    print(json.dumps({'max_scaled_remainder':'ln(2)-2/3 at b=0, z=1/3','dyadic_interval_numerators': [low,up],'denominator':scale,'last_admitted_term_index':31,'exact_fraction_pair':[frac(a),frac(b)],'low_bit_grid':checked,'strong_geometric_max':'1/36','unweakened_library_max':'1/12','original_comment_uniform_dyadic_max':'1/32','sharp_constant_at_closed_endpoint':True,'sample_counts':{'b_zero':1,'b_three':2,'first_caller_bits':280,'first_caller_terms':95}},sort_keys=True))
if __name__ == '__main__':
    main()
