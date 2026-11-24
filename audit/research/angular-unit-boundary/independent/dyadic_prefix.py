"""Fixed-point outward certificates for the uniformly worst, continuously extended angular population."""
import json
from fractions import Fraction as Q
from math import comb, isqrt
from pathlib import Path
from sys import stdout

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def floor(q):
    return q.numerator // q.denominator

def ceil(q):
    return -floor(-q)

def sq_enclose(q, scale):
    num = q.numerator * scale**2
    den = q.denominator
    k = isqrt(num // den)
    require(den*k*k <= num < den*(k+1)**2, "square")
    return Q(k,scale), Q(k+(den*k*k != num),scale)

def minus_log(k, scale, terms=96):
    """For a rational 0<k<=1 bound -log(k) in units of 1/scale."""
    require(Q(1,2) <= k <= 1 and 1 <= terms <= 128, "signed log domain")
    u=(1-k)/(1+k)
    square=u*u
    lower=floor(scale*u)
    upper=ceil(scale*u)
    partial_l=partial_u=0
    for i in range(terms):
        odd=2*i+1
        partial_l += lower//odd
        partial_u += -(-upper//odd)
        lower = floor(lower*square)
        upper = ceil(upper*square)
    tail=ceil(Q(upper,(2*terms+1))/(1-square))
    return 2*partial_l,2*(partial_u+tail)

def proper(w, scale):
    """Return the interval of E[(1+C)log(1+w*C)], with C the cosine of uniform phase."""
    lo,hi=sq_enclose(1-w*w,scale)
    ml_upper=minus_log((1+lo)/2,scale)[1]
    ml_lower=minus_log((1+hi)/2,scale)[0]
    return floor(scale*w/(1+hi))-ml_upper,ceil(scale*w/(1+lo))-ml_lower

def scaled(bounds,den,unit):
    a,b=bounds
    return [floor(Q(a*unit,den)),ceil(Q(b*unit,den))]

def check_bracket(prior, this):
    return prior[0]>0 and this[1]<0

def one(bits):
    scale=1<<bits
    ml=minus_log(Q(1,2),scale)
    j=scale-ml[1],scale-ml[0]
    p=proper(Q(1,2),scale)
    q=proper(Q(2,3),scale)
    h=2*p[0]-q[1],2*p[1]-q[0]
    require(h[0]>=scale//8 and h[1]<scale, "positive denominator")
    require(ml[0]>0 and j[0]>0 and j[1]<scale,"log sign")
    require(minus_log(Q(1),scale)==(0,0),"zero log")
    require(sq_enclose(Q(9,16),scale)==(Q(3,4),Q(3,4)), "exact square control")
    # Independent arithmetic of the log-halving identity at 3/4 and 2/3.
    al,au=minus_log(Q(3,4),scale)
    bl,bu=minus_log(Q(2,3),scale)
    require(al+bl<=ml[1] and au+bu>=ml[0], "product of independent log brackets")
    e=10**6
    partial_l=partial_u=0
    coeff_l=coeff_u=scale//4
    prev=None
    for m in range(1,40001):
        if m<=40:
            direct=Q(comb(2*m,m),4**m*(2*m)*(2*m-1))*scale
            require(coeff_l<=direct<=coeff_u, "exact coefficient mismatch")
        partial_l+=coeff_l
        partial_u+=coeff_u
        target=(e*(j[0]-partial_u)-h[1], e*(j[1]-partial_l)-h[0])
        require(target[0]<=target[1] and (target[0]>0 or target[1]<0), "unresolved sign")
        if target[1]<0:
            require(prev and check_bracket(prev,target), "missing adjoining failure")
            require(not check_bracket(target,prev) and not check_bracket(prev,prev) and not check_bracket(target,target), "off-by-one and reversed assertions")
            return {"minimal_even_terms":m,"first_omitted_power":2*m+2,"sqrt_precision_bits":bits,"log_terms":96,"J_times_10_to_24":scaled(j,scale,10**24),"H_times_10_to_24":scaled(h,scale,10**24),"F_previous_times_10_to_24":scaled(prev,e*scale,10**24),"F_minimal_times_10_to_24":scaled(target,e*scale,10**24),
                "prior_relative_ppm_times_10_to_12":scaled((e*(j[0]-(partial_u-coeff_u))*10**12//h[1],-(-e*(j[1]-(partial_l-coeff_l))*10**12//h[0])),1,1),
                "selected_relative_ppm_times_10_to_12":scaled((e*(j[0]-partial_u)*10**12//h[1],-(-e*(j[1]-partial_l)*10**12//h[0])),1,1)}
        prev=target
        n=(2*m)*(2*m-1)
        d=(2*m+2)**2
        coeff_l=coeff_l*n//d
        coeff_u=-(-coeff_u*n//d)
    raise ValueError("resource stop")

if __name__=="__main__":
    first=one(240)
    double=one(480)
    require({k:v for k,v in first.items() if k!="sqrt_precision_bits"}=={k:v for k,v in double.items() if k!="sqrt_precision_bits"}, "precision replay")
    print(json.dumps({"schema":"independent-angular-closed-boundary-first-order-v1","method":"fixed outward integer prefix of the one-axis absolutely convergent expansion, direct elementary integral at unit amplitude","primary":first,"doubled":double,"denominator_for_F":"F=tail - 10^-6*H(1)","control_count_exact_initial_coefficients":40},sort_keys=True,indent=2))
