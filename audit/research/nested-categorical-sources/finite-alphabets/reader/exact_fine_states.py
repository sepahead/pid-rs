"""Finite classification of the least positive gap by the exact fine-label count."""
from collections import Counter
from fractions import Fraction
import json
def require(v,reason):
    if not v:raise ValueError(reason)
def partitions(n):
    def make(w):
        if len(w)==n:
            yield w
        else:
            for i in range(max(w)+2):
                yield from make(w+(i,))
    yield from make((0,))
def ratio(x,y):
    a=Counter(x);b=Counter(y);both=Counter(zip(x,y))
    g=Fraction(1)
    for (i,j),c in both.items():
        g*=Fraction(a[i]+b[j]-c,a[i])**c
    return g
def target(n,l):
    if n<2 or l>=n:return None
    if l==1:return Fraction(n**n,(n-1)**(n-1))
    if l==2:return Fraction(2*n,n-1)
    u=n//2;v=n-u;return Fraction((u+1)*(v+1),u*v)
def witness(n,l):
    if l==1:return (0,)*(n-1)+(1,),(0,)*n
    if l==2:return (0,)*(n-1)+(1,),(0,)+(1,)*(n-2)+(0,)
    u=n//2;v=n-u
    pieces=[(0,u-1),(1,v-1)]
    while len(pieces)<l-1:
        i=next(i for i,(_,k) in enumerate(pieces) if k>1)
        label,k=pieces[i];pieces[i:i+1]=[(label,1),(label,k-1)]
    x,y=[0,1],[0,0]
    for j,(label,k) in enumerate(pieces,1):
        x.extend([label]*k);y.extend([j]*k)
    return tuple(x),tuple(y)
def run():
    scopes={};overall=0
    for n in range(1,7):
        part=list(partitions(n));best={k:None for k in range(1,n+1)};positive=Counter()
        for fine in part:
            l=len(set(fine))
            for coarse in part:
                g=ratio(coarse,fine);overall+=1
                if g==1:continue
                t=target(n,l);require(t is not None and g>=t,'predicted lower')
                positive[l]+=1;best[l]=g if best[l] is None else min(g,best[l])
        require(all(minimum==target(n,l) for l,minimum in best.items()),'no spurious sharpness')
        scopes[n]={l:{'smallest_positive_product':str(best[l]) if best[l] else None,'failed_maps':positive[l]} for l in best}
    for n in range(2,101):
        for l in range(1,n):
            coarse,fine=witness(n,l)
            require(len(coarse)==len(fine)==n and len(set(fine))==l and ratio(coarse,fine)==target(n,l),'every specified fine count attains')
    return {'all_original_partition_pairs_through_six':overall,'minima_by_N_L':scopes,'constructed_N_2_to_100_all_1_le_L_lt_N':sum(range(1,100))}
if __name__=='__main__':print(json.dumps(run(),indent=2,sort_keys=True))
