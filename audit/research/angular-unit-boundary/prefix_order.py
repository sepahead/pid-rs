"""Find the first passing number of terms by directed fixed-point summation."""
from fractions import Fraction as Q
from math import isqrt
import json

UNIT=10**48
REPORT=10**18
TAU=Q(1,10**6)


def ceil_ratio(x,y):
    return -((-x)//y)


def sqrt_decimal(q):
    unit=10**60
    low=isqrt(q.numerator*unit**2//q.denominator)
    bounds=Q(low,unit),Q(low+1,unit)
    if not bounds[0]**2<=q<bounds[1]**2:raise ValueError('square root enclosure')
    return bounds


def minus_log(k):
    d=(1-k)/(1+k)
    if not 0<=d<=Q(1,3):raise ValueError('logarithm argument')
    power=d
    total=Q(0)
    for i in range(56):
        total+=2*power/(2*i+1)
        power*=d*d
    return total,total+2*power/(113*(1-d*d))


def proper(w):
    slo,shi=sqrt_decimal(1-w*w)
    klo,khi=(1+slo)/2,(1+shi)/2
    return -minus_log(klo)[1]+w/(1+shi),-minus_log(khi)[0]+w/(1+slo)


def main():
    # A fixed scalar minus the partial sum is the signed tolerance residual.
    log2_lo,log2_hi=minus_log(Q(1,2));plo,phi=proper(Q(1,2));qlo,qhi=proper(Q(2,3))
    hlow,hhi=2*plo-qhi,2*phi-qlo
    if not Q(1,8)<=hlow<=hhi<1:raise ValueError('positive boundary atom')
    const_low=((1-log2_hi-TAU*hhi)*UNIT).__floor__();const_high=((1-log2_lo-TAU*hlow)*UNIT).__ceil__()
    clo=chi=UNIT
    sum_lower=sum_upper=0
    prev=None
    for j in range(1,32769):
        clo=(clo*(2*j-1))//(2*j)
        chi=ceil_ratio(chi*(2*j-1),2*j)
        d=2*j*(2*j-1)
        sum_lower+=clo//d
        sum_upper+=ceil_ratio(chi,d)
        low=const_low-sum_upper;high=const_high-sum_lower
        a=low*REPORT//UNIT;b=ceil_ratio(high*REPORT,UNIT)
        if a<=0<=b:raise ValueError('unresolved sign at '+str(j))
        if b<0:
            if prev is None or prev[0]<=0:raise ValueError('previous sign')
            print(json.dumps({'schema':'angular-unit-order-v1','order':j,'scale':REPORT,'previous':prev,'current':[a,b]},sort_keys=True))
            return
        prev=[a,b]
    raise ValueError('no crossing in declared domain')

if __name__=='__main__':main()
