"""Certify two fixed angular four-moment decisions by a power-basis Sturm chain."""
from fractions import Fraction as F
from functools import reduce
from hashlib import sha256
import json
from math import comb, gcd, lcm

EPS = F(1, 10**6)
LO = F(340315168725, 10**12)
HI = F(340315168726, 10**12)
X = F(21787956, 10**8)
N = 18

def need(ok, msg):
    if not ok: raise ArithmeticError(msg)

def k(j):
    return F(comb(2*j, j), 4**j * 2*j * (2*j-1))

def h(j):
    return F(2*(2*j+1), 4**j) - (j+1)*F(4,9)**j

def B(j, x):
    return sum(comb(j,i)**2 * x**(2*i) * (1-x)**(2*(j-i)) for i in range(j+1))

def evaluation(r,x,n):
    t,a=F(0),F(0)
    for j in range(1,n+1):
        factor=k(j)*r**(2*j); moment=B(j,x)
        a += factor*(moment+(h(j)-1)*x**(2*j))
        if j>4:t += factor*moment
    return t-EPS*a

def upper_tail(r,n):
    # B is a sum of squared binomial probabilities, hence at most one.
    # For j>N, h_j<0 and |h_j|<=2; k_j decreases strictly.
    return (1+2*EPS)*k(n+1)*r**(2*(n+1))/(1-r*r)

def moment_coefficients(j):
    terms=[0]*(2*j+1)
    for i in range(j+1):
        exponent=2*(j-i)
        for ell in range(exponent+1):
            terms[2*i+ell] += (-1)**ell*comb(j,i)**2*comb(exponent,ell)
    return terms

def polynomial(r,n):
    coeff=[F(0)]*(2*n+1)
    for j in range(1,n+1):
        factor=k(j)*r**(2*j)
        alpha=(1-EPS if j>4 else -EPS)*factor
        for e,be in enumerate(moment_coefficients(j)):coeff[e] += alpha*be
        coeff[2*j] += EPS*factor*(1-h(j))
    return coeff

def at(a,x):
    y=0
    for c in reversed(a):y=x*y+c
    return y

def primitive(a):
    while a and a[-1]==0:a.pop()
    if not a:return []
    d=reduce(gcd, a, 0)
    return [c//d for c in a]

def intpoly(coeff):
    denom=reduce(lcm,(q.denominator for q in coeff),1)
    return primitive([int(q*denom) for q in coeff])

def rem(a,b):
    a=list(a); lead=b[-1];sgn=1 if lead>0 else -1
    while len(a)>=len(b):
        shift=len(a)-len(b);c=a[-1]*sgn
        a=[v*abs(lead) for v in a]
        for i,bi in enumerate(b):a[shift+i]-=c*bi
        a=primitive(a)
    return a

def sturm(a):
    seq=[a, primitive([i*q for i,q in enumerate(a) if i])]
    while seq[-1]:
        new=rem(seq[-2],seq[-1])
        if not new:break
        seq.append([-q for q in new])
    return seq

def signs(seq,x):
    v=[at(a,x) for a in seq]
    return [1 if n>0 else -1 for n in v if n]

def variations(v):return sum(i!=j for i,j in zip(v,v[1:]))
def fraction_bound(lower,higher,scale):
    return [(lower*scale).__floor__(),(higher*scale).__ceil__()]

def sample_digest(seq):
    hh=sha256()
    for s in seq:
        hh.update(b"S")
        for v in s:
            z=abs(v).to_bytes((abs(v).bit_length()+7)//8 or 1,"big")
            hh.update(bytes([v<0]));hh.update(len(z).to_bytes(4,"big"));hh.update(z)
    return hh.hexdigest()

def verify():
    """Return the four-moment, one-part-per-million certificate at the two fixed radii."""
    need(LO<HI and 0<X<1 and N>=5,"original inputs")
    # Direct arithmetic and the power basis must agree on both endpoints,
    # two rational interior test points, and the stated witness.
    p=polynomial(HI,N)
    for y in [F(0),F(1,3),F(1,2),X,F(1)]:need(at(p,y)==evaluation(HI,y,N),"polynomial identity sample")
    low=evaluation(LO,X,N);e=upper_tail(LO,N)
    need(low+e<0,"lower-radius strict witness including full tail")
    high=evaluation(HI,X,N)
    need(high>0,"upper-radius polynomial at witness")
    # Independent known-root controls, including a negative-leading divisor case.
    for poly,roots in [([-1,2],1),([1,-2],1),([1,-4,4],1),([2,-9,9],2),([1,-1,1],0),([3,4,1],0)]:
        need(at(poly,1)!=0 and at(poly,0)!=0,"root-control endpoint")
        chain=sturm(poly);v0=variations(signs(chain,0));v1=variations(signs(chain,1))
        need(v0-v1==roots,"Sturm control")
    a=intpoly(p);chain=sturm(a)
    need(at(a,0)>0 and at(a,1)>0 and degree(chain[-1])==0,"strict endpoints, square-free finite minorant")
    left,right=signs(chain,0),signs(chain,1)
    need(variations(left)==variations(right),"minorant has a root in the closed direction interval")
    out={"schema":"angular-minimum-sturm-two-inputs/1","degrees":[degree(q) for q in chain],
         "interval":[str(LO),str(HI)],"direction_witness":str(X),"moment_pairs":N,
         "signed_error_at_low_times_10_pow_24":fraction_bound(low,low+e,10**24),
         "value_of_finite_minorant_at_witness_high_times_10_pow_24":fraction_bound(high,high,10**24),
         "geometric_tail_at_low_times_10_pow_24":fraction_bound(e,e,10**24),"strict_endpoints":[at(a,0)>0,at(a,1)>0],
         "sturm_signs_at_zero":left,"sturm_signs_at_one":right,"variations":[variations(left),variations(right)],
         "interior_real_zeros":0,"sturm_chain_sha256":sample_digest(chain),
         "max_coefficient_bits":max(abs(c).bit_length() for q in chain for c in q),
         "boundary":"Only the stated lower witness and the all-direction upper radius. The root count applies to the finite minorant. The analytic remainder is nonnegative. No monotonicity or uniqueness follows from these two finite signs."}
    return out

def degree(p):return len(p)-1

if __name__=="__main__":
    print(json.dumps(verify(),indent=2,sort_keys=True))
