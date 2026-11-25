"""Direct power expansion and a centered integer Taylor lower bound on each interval."""
import json
from fractions import Fraction as F
from math import comb,lcm
from pathlib import Path
import sys


def need(ok,reason):
    if not ok:raise ValueError(reason)


def make(r,degree,slots):
    # Coefficient recurrences for the even cosine moments use no central binomial call.
    e=F(1,1000000)
    c=F(1)
    poly=[F()]*(2*degree+1)
    for j in range(1,degree+1):
        c*=F(2*j-1,2*j)
        k=c/F(2*j*(2*j-1))
        f=lambda w: w**(2*j-1)*(2*j-(2*j-1)*w)
        h=2*f(F(1,2))-f(F(2,3))
        b=[0]*(2*j+1)
        # Explicit expansion of x^(2i) (1-x)^(2j-2i) in ordinary powers.
        for i in range(j+1):
            weight=comb(j,i)**2
            for q in range(2*(j-i)+1):
                b[2*i+q]+=weight*((-1)**q)*comb(2*(j-i),q)
        scale=k*r**(2*j)
        for i,bi in enumerate(b):
            poly[i]+=scale*(int(j>slots)-e)*bi
        poly[2*j]+=scale*e*(1-h)
    return poly,c


def value(co,x):
    ans=F()
    for b in reversed(co):ans=ans*x+b
    return ans


def lower_at_middle(co,den):
    # The local variable t runs from 0 to 1. Write u=2t-1 in [-1,1].
    # One integer numerator per coefficient of p((1+u)/2).
    deg=len(co)-1
    mid=[sum(co[m]*comb(m,j)*(1<<(deg-m)) for m in range(j,deg+1)) for j in range(deg+1)]
    return F(mid[0]-sum(abs(x) for x in mid[1:]),den<<deg)


def two_halves(co,den):
    deg=len(co)-1
    lo=[n<<(deg-j) for j,n in enumerate(co)]
    hi=[sum(co[m]*comb(m,j)*(1<<(deg-m)) for m in range(j,deg+1)) for j in range(deg+1)]
    return lo,hi,den<<deg


def run(reg):
    M,N=reg['M'],reg['N']
    left,right,x,e=(F(reg[k]) for k in ('lower','upper','x','tolerance'))
    need(0<left<right<1 and e==F(1,1000000) and M==4 and N==24,'identities')
    low,c=make(left,N,M)
    c_next=c*F(2*N+1,2*N+2)
    knext=c_next/F((2*N+2)*(2*N+1))
    top=value(low,x)+knext*(1+2*e)*left**(2*N+2)/(1-left**2)
    need(top<0,'strict physical passing example')
    poly,_=make(right,N,M)
    den=lcm(*(x.denominator for x in poly))
    stack=[([int(v*den) for v in poly],den,0,0)];leaves=[];prev=F(0);visited=0
    while stack:
        co,q,lev,i=stack.pop();visited+=1
        lower=lower_at_middle(co,q)
        if lower>0:
            need(prev==F(i,1<<lev),'successive endpoints')
            prev=F(i+1,1<<lev);leaves.append((lev,i,lower))
        else:
            need(lev<40 and visited<20000,'incomplete coverage')
            a,b,d=two_halves(co,q)
            stack.extend([(b,d,lev+1,2*i+1),(a,d,lev+1,2*i)])
    need(prev==1,'full closed domain')
    return dict(lower_example_upper=str(top),certified_upper_minimum_lower=str(min(v for _,_,v in leaves)),leaves=[[l,i,str(v)] for l,i,v in leaves],maxdepth=max(l for l,i,v in leaves))


if __name__=='__main__':
    result=run(json.loads(Path(sys.argv[1]).read_bytes()))
    with Path(sys.argv[2]).open('x') as f:
        f.write(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(len(result['leaves']),result['maxdepth'])
