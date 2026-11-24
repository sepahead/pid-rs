"""Enclose the elementary branch integrals directly with integer square roots."""
from fractions import Fraction as Q
from math import isqrt

def require(ok, reason):
    if not ok:raise ValueError(reason)

def sqrt_bounds(q):
    require(isinstance(q,Q) and q>=0,"nonnegative rational radicand")
    scale=10**65
    k=isqrt(scale*scale*q.numerator//q.denominator)
    lo,hi=Q(k,scale),Q(k+1,scale)
    require(lo*lo<=q<hi*hi,"square root bounds")
    return lo,hi

def negative_log(k):
    u=(1-k)/(1+k)
    require(0<=u<Q(1,4),"atanh domain used by this reader")
    odd=u
    prefix=Q(0)
    for j in range(28):
        prefix+=odd/(2*j+1)
        odd*=u*u
    return 2*prefix,2*(prefix+odd/(57*(1-u*u)))

def branch(a,w):
    c=a*w
    lo,hi=sqrt_bounds(1-c*c)
    return (-negative_log((1+lo)/2)[1]+a*c/(1+hi),
            -negative_log((1+hi)/2)[0]+a*c/(1+lo))

def axis(a):
    hl,hu=branch(a,Q(1,2))
    dl,du=branch(a,Q(2,3))
    return 2*hl-du,2*hu-dl

def threshold_interval(a):
    jl,ju=branch(a,Q(1))
    low,high=axis(a)
    polynomial=a*a/4+a**4/32+a**6/96+5*a**8/1024
    return jl-polynomial-high/10**6,ju-polynomial-low/10**6

def pair(q):
    return [q.numerator,q.denominator]

def counterexample():
    radius=Q(1,10)
    y=Q(1,100000)
    x=1-y
    a,b=radius*x,radius*y
    hl,hu=axis(a)
    rl,ru=axis(radius)
    first=x*x+y*y
    gap_low=hl-first*ru
    gap_high=hu+b*b/(4*(1-radius))-first*rl
    require(gap_high<0,"false first-factor comparison")
    return {"r":pair(radius),"a":pair(a),"b":pair(b),"B1":pair(first),
            "G_times_10_to_15":[(gap_low*10**15).__floor__(),(gap_high*10**15).__ceil__()]}
