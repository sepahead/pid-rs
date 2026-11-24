"""Separate four-term directional checks from the old interior power series."""
from fractions import Fraction as Q
from math import comb,factorial
from operator import add
import json

def require(q,msg):
    if not q: raise ArithmeticError(msg)
def moment(j):
    return Q(comb(2*j,j),4**j)
def coefficient(j):
    return moment(j)/(2*j*(2*j-1))
def h(j):
    def f(w):
        return w**(2*j-1)*(2*j-(2*j-1)*w)
    return 2*f(Q(1,2))-f(Q(2,3))
def interval(lower,upper,unit):
    return [(lower*unit).__floor__(),(upper*unit).__ceil__()]
def axis(r,n):
    sumj=sum(coefficient(j)*r**(2*j) for j in range(1,n+1))
    sumh=sum(coefficient(j)*h(j)*r**(2*j) for j in range(1,n+1))
    prefix=sum(coefficient(j)*r**(2*j) for j in range(1,5))
    error=coefficient(n+1)*r**(2*(n+1))/(1-r*r)
    # Positive k_j and |h_j|<=2 on the neglected terms.
    num=(sumj-prefix,sumj+error-prefix)
    hj=(sumh-2*error,sumh+2*error)
    jj=(sumj,sumj+error)
    values={}
    for name,den in (("pure-first",hj),("pure-second",jj)):
        require(0<den[0]<=den[1] and 0<num[0]<=num[1],"positive interval")
        values[name]={"F_times_10_to_24":interval(num[0]-den[1]/10**6,num[1]-den[0]/10**6,10**24),
                      "ppm_times_10_to_12":interval(10**6*num[0]/den[1],10**6*num[1]/den[0],10**12)}
    return values
m10=sum(comb(10,2*j)*moment(j)*moment(5-j) for j in range(6))/2**10
require(m10==moment(5)**2,"balanced moment identity")
require(sum(Q(7,10)**j/factorial(j) for j in range(4))>2,"elementary upper log2")
r=Q(39,100)
scale=m10/(90*Q(7,20))
bound=scale*r**8
require(bound>Q(1,10**6) and 0<r<Q(2,5),"strict all-direction margin")
res=axis(Q(3,10),16)
require(res["pure-first"]["F_times_10_to_24"][0]>0>res["pure-second"]["F_times_10_to_24"][1],"opposite axis outcomes")
res22=axis(Q(3,10),22)
for k in res:
 for field in res[k]:
    a,b=res[k][field]; c,d=res22[k][field]
    require(a<=c<=d<=b,"stronger remainder must narrow certificate")
print(json.dumps({"three_tenths_N16":res,"three_tenths_N22":res22,"balanced_moment":str(m10),"universal_coefficient_for_r_to_eight":str(scale),"lower_bound_at_39_over_100":str(bound),"lower_ppm_at_39_times_10_to_12":interval(bound,bound,10**18),"scope":"all r from 39/100 to 1 and all directions; sufficient threshold, does not optimize the minimum over directions; extends averaged atom continuously at r=1"},indent=2,sort_keys=True))
