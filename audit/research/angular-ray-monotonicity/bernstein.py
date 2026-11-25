"""Exact enclosure of the best-direction crossing for the fixed four-moment calculation."""
from argparse import ArgumentParser
from fractions import Fraction as F
from math import comb,lcm
from pathlib import Path
import json


def require(ok,why):
    if not ok:
        raise ValueError(why)


def K(j):
    return F(comb(2*j,j),4**j*2*j*(2*j-1))


def h(j):
    return 2*(2*j+1)*F(1,4)**j - (j+1)*F(4,9)**j


def b(j,x):
    return sum(F(comb(j,i)**2)*x**(2*i)*(1-x)**(2*j-2*i) for i in range(j+1))


def lower_test(r,x,e,M,N):
    total=F(0)
    for j in range(1,N+1):
        total+=K(j)*r**(2*j)*((int(j>M)-e)*b(j,x)+e*(1-h(j))*x**(2*j))
    err=(1+2*e)*K(N+1)*r**(2*N+2)/(1-r*r)
    require(total+err<0,'no passing direction at the proposed lower radial evidence')
    return total,total+err


def choose(n,k):
    return comb(n,k) if 0<=k<=n else 0


def coefficients(r,e,M,N):
    D=2*N
    coeff=[F(0)]*(D+1)
    for j in range(1,N+1):
        high=K(j)*r**(2*j)
        for ell in range(D+1):
            val=sum(comb(j,i)**2*choose(D-2*j,ell-2*i) for i in range(j+1))
            axis=choose(D-2*j,ell-2*j)
            coeff[ell]+=high*((int(j>M)-e)*val+e*(1-h(j))*axis)/comb(D,ell)
    den=lcm(*(v.denominator for v in coeff))
    return [int(den*v) for v in coeff],den


def split(coef,den):
    degree=len(coef)-1
    left,right=[],[]
    seq=coef
    for t in range(degree+1):
        left.append(seq[0]<<(degree-t))
        right.append(seq[-1]<<(degree-t))
        seq=[a+b for a,b in zip(seq,seq[1:])]
    return left,list(reversed(right)),den<<degree


def cover(c,den):
    leaves=[]
    stack=[(c,den,0,0)]
    visits=0
    while stack:
        co,q,depth,index=stack.pop()
        visits+=1
        if min(co)>0:
            leaves.append((depth,index,F(min(co),q)))
            continue
        require(depth<40 and visits<20000,'unresolved or too many intervals')
        a,b,d=split(co,q)
        stack.append((b,d,depth+1,2*index+1))
        stack.append((a,d,depth+1,2*index))
    return leaves


def check_cover(leaves,co,de):
    # A second walk from the root checks each supplied interval and its exact bound.
    require(isinstance(leaves,list) and leaves,'empty cover')
    cache={(0,0):(co,de)}
    start=F(0)
    for depth,index,bound in leaves:
        require(type(depth) is int and 0<=depth<=40 and type(index) is int and 0<=index<1<<depth,'dyadic interval')
        require(F(index,2**depth)==start,'gap, overlap or wrong order')
        start=F(index+1,2**depth)
        for level in range(1,depth+1):
            i=index>>(depth-level)
            key=(level,i)
            if key not in cache:
                a,b,d=split(*cache[(level-1,i//2)])
                cache[(level,2*(i//2))]=a,d
                cache[(level,2*(i//2)+1)]=b,d
        c,d=cache[(depth,index)]
        require(F(min(c),d)==bound and bound>0,'incorrect leaf lower bound')
    require(start==1,'incomplete direction domain')


def endpoints(v,scale):
    return [v.numerator*10**scale//v.denominator,-((-v.numerator*10**scale)//v.denominator)]


def solve(params):
    require(set(params)=={'M','N','x','lower','upper','tolerance'},'input fields')
    M,N=params['M'],params['N']
    left,right,x,e=map(F,[params[k] for k in ('lower','upper','x','tolerance')])
    require(type(M) is int and type(N) is int and M==4 and N==24 and 0<left<right<1 and 0<=x<=1 and e==F(1,10**6),'study domain')
    lo,hi=lower_test(left,x,e,M,N)
    coeff,den=coefficients(right,e,M,N)
    leaves=cover(coeff,den)
    check_cover(leaves,coeff,den)
    minimum=min(v for _,_,v in leaves)
    require(minimum>0 and lo<=hi<0,'strict sign')
    return dict(parameters=params,scale=24,lower_direction_infinite_value=[endpoints(lo,24)[0],endpoints(hi,24)[1]],
                upper_direction_global_lower_bound=endpoints(minimum,24),leaves=[[j,i,str(v)] for j,i,v in leaves],
                max_depth=max(j for j,i,v in leaves),direction_domain=['0','1'])


if __name__=='__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=solve(json.loads(args.input.read_bytes()))
    with args.output.open('x') as out:
        out.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(len(result['leaves']),result['max_depth'],result['lower_direction_infinite_value'],result['upper_direction_global_lower_bound'])
