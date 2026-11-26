"""Try to refute the five-slot finite attainment criterion on exact binary count tables."""
from collections import Counter
from fractions import Fraction
from functools import cache
from itertools import combinations, combinations_with_replacement, product
from math import prod
import json


def require(ok, message):
    if not ok:
        raise ValueError(message)


def lower(a,b):
    return all(any(k & h == k for k in a) for h in b)


ALL = [a for n in range(1,8) for a in combinations(range(1,8),n)
       if all(h & k not in (h,k) for h,k in combinations(a,2))]
NODES = sorted(ALL,key=lambda a:sum(lower(b,a) for b in ALL))
PREVIOUS = [[j for j,b in enumerate(NODES[:i]) if lower(b,a)] for i,a in enumerate(NODES)]
K = [i for i,a in enumerate(NODES) if not lower(a,(3,))]
S3 = NODES.index((4,)); PRED = NODES.index((3,4))
require(len(NODES)==18 and len(K)==5 and PREVIOUS[S3]==sorted([PRED,*PREVIOUS[PRED]]),'genuine single predecessor')
ROWS = list(product(range(2), repeat=4))


@cache
def links(z,other):
    flags=sum(2**j for j in range(3) if z[j]==other[j])
    return tuple(any(flags&mask==mask for mask in group) for group in NODES)


def test(table):
    n=sum(table.values());require(n>0 and all(w>0 for w in table.values()),'positive finite weights')
    p=[Fraction(1) for _ in NODES]; q=p.copy(); A=B=Fraction(1)
    for z,c in table.items():
        points=list(table.items());target=sum(w for v,w in points if z[3]==v[3]);twelve=sum(w for v,w in points if z[:2]==v[:2]);three=sum(w for v,w in points if z[:3]==v[:3]);ctwelve=sum(w for v,w in points if z[:2]==v[:2] and z[3]==v[3]); A*=Fraction(twelve,three)**c; B*=Fraction(ctwelve,c)**c
        pp=[];qq=[]
        for i,node in enumerate(NODES):
            joint=mass=0
            for other,w in points:
                if links(z,other)[i]:
                    mass+=w
                    if other[3]==z[3]:joint+=w
            lp=Fraction(n,mass)/prod(pp[j] for j in PREVIOUS[i]);lq=Fraction(target,joint)/prod(qq[j] for j in PREVIOUS[i])
            require(lp>=1 and lq>=1,'both original local unsigned products nonnegative');pp.append(lp);qq.append(lq);p[i]*=lp**c;q[i]*=lq**c
        marginal=sum(w for v,w in points if v[2]==z[2]);cond=sum(w for v,w in points if v[2:]==z[2:]);other_three=sum(w for v,w in points if v[:2]==z[:2] and v[2]!=z[2]);conflict=sum(w for v,w in points if v[:2]==z[:2] and v[2]!=z[2] and v[3]==z[3]);
        require(pp[S3]==Fraction(marginal+other_three,marginal) and qq[S3]==Fraction(cond+conflict,cond),'direct local pair-cut formula')
    require(prod(p[i] for i in K)==A and prod(q[i] for i in K)==B,'two exact entropy sums')
    mass=prod(max(p[i]/q[i],q[i]/p[i]) for i in K); gap=A*B/mass
    require(gap==prod(min(p[i],q[i])**2 for i in K),'slack identity')
    require((gap==1)==(B==1),'equality if and only if conditional entropy zero')
    if B>1:
        a=n//2;b=n-a
        require(gap>=Fraction((a+1)*(b+1),a*b)**2,'finite two-row lower bound')
    return B,gap


def main():
    by_size={}; total=positive=zero=0
    for n in range(1,5):
        amount=has=0;smallest=None;witness=None
        for panel in combinations_with_replacement(range(len(ROWS)),n):
            table=Counter(ROWS[i] for i in panel);B,gap=test(table);amount+=1
            if B>1:
                has+=1
                if smallest is None or gap<smallest:smallest=gap;witness=panel
        a=n//2;b=n-a; lower_bound=Fraction((a+1)*(b+1),a*b)**2 if n>1 else None
        by_size[n]={'total':amount,'positive_B':has,'zero_B':amount-has,'minimum_exponentiated_N_slack_observed':str(smallest) if smallest is not None else None,'lexicographic_minimizer_indices':witness,'uniform_valid_lower_bound':str(lower_bound) if lower_bound is not None else None}
        total+=amount;positive+=has;zero+=amount-has
    require(total==4844 and positive and zero,'nonvacuous four-dimensional input census')
    # Extra cases use explicit ternary labels and repeated counts.
    extras=[{(0,0,0,2):2,(0,0,1,2):3,(1,0,2,1):4},
            {(0,0,0,0):3,(0,0,1,1):2}, {(0,1,0,0):1,(0,1,1,0):1},
            {(0,0,0,0):1,(0,0,1,0):1,(1,1,2,1):4,(2,2,2,2):2}]
    cases=[tuple(map(str,test(t))) for t in extras]
    return {'schema':'arbitrary-finite-five-slot-attainment-census-v1','binary_tuple_order':ROWS,'exact_counted_tables':total,'positive_conditional_entropy':positive,'zero_conditional_entropy':zero,'by_total':by_size,'extra_B_and_slack_products':cases,'boundary':'The reported minimum is exact only on the enumerated binary tables. The uniform N bound is an inequality for arbitrary finite source/target alphabets with integer counts.'}

if __name__=='__main__':print(json.dumps(main(),sort_keys=True,indent=2))
