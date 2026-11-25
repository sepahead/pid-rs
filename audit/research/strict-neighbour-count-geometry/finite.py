"""Enumerate entire finite coordinate panels, then judge against a separate parametric set."""
from collections import defaultdict
from fractions import Fraction
from itertools import combinations_with_replacement, product
import hashlib,json

def require(ok,label):
    if not ok:raise ValueError(label)

def patterns(dim):
    buckets=defaultdict(set)
    examples={}
    volume=0
    for n in range(2,6):
        sites=list(product((1,2,3),repeat=dim))
        for rows in combinations_with_replacement(sites,n-1):
            volume+=1
            comp=[(p[0] if dim==2 else min(p[0],p[1]),p[-1]) for p in rows]
            joint=sorted(max(s,t) for s,t in comp)
            h=sum(w<2 for w in joint)
            c=joint.count(2)
            x=1+sum(s<2 for s,t in comp);y=1+sum(t<2 for s,t in comp)
            for k,r in enumerate(joint,1):
                if r!=2:continue
                key=(n,k,h,c)
                buckets[key+(False,)].add((x,y))
                if all(not (s==t==r) for s,t in comp):
                    buckets[key+(True,)].add((x,y))
                if n==3 and k==1 and (x,y) in {(1,1),(1,3),(2,2)} and c==1:
                    examples.setdefault(str((x,y)),rows)
    return volume,buckets,examples

def expected(n,k,h,c,single):
    m=n-1
    if not (0<=h<k<=h+c<=m and c>0):return set()
    result=set()
    for x in range(1,n+1):
        for y in range(1,n+1):
            a,b,neither=x-h-1,y-h-1,n+h+1-x-y
            if min(a,b,neither)>=0 and (not single or c<=a+b):
                result.add((x,y))
    return result

def harmonics(n):
    a=[Fraction(0)]
    for i in range(1,n+1):a.append(a[-1]+Fraction(1,i))
    return a

def examine(dim):
    grids,seen,examples=patterns(dim)
    tested=0;pair_relations=0;ends=[]
    for n in range(2,6):
        H=harmonics(n)
        for k in range(1,n):
            for h in range(n):
                for c in range(n):
                    for single in (False,True):
                        got=seen.get((n,k,h,c,single),set())
                        wanted=expected(n,k,h,c,single)
                        require(got==wanted,'domain or range mismatch '+str((dim,n,k,h,c,single,got^wanted)))
                        tested+=1;pair_relations+=len(got)
            all_pairs=seen[(n,k,k-1,1,False)]
            stable=seen[(n,k,k-1,1,True)]
            require(all_pairs-stable=={(k,k)} and len(all_pairs)==(n-k+1)*(n-k+2)//2,'singleton diagonal')
            T=lambda xy:H[k-1]+H[n-1]-H[xy[0]-1]-H[xy[1]-1]
            lo=min(map(T,all_pairs));exact=max(map(T,all_pairs));generic=max(map(T,stable))
            mid=((n+k)//2,(n+k+1)//2)
            require(set(xy for xy in all_pairs if T(xy)==lo)=={mid,mid[::-1]},'sharp lower')
            require(exact==H[n-1]-H[k-1] and generic==exact-Fraction(1,k),'sharp upper')
            if k==n-1:require({T(xy) for xy in stable}=={0},'k=N-1 degeneracy')
            ends.append({'n':n,'k':k,'lower':str(lo),'upper_open':str(generic),'upper_exact':str(exact)})
    return {'dimension':dim,'complete_coordinate_multisets':grids,'compared_domain_cells_including_empty':tested,
            'pair_memberships_compared':pair_relations,'exact_small_examples':examples,'harmonic_endpoints':ends}

if __name__=='__main__':
    r=[examine(2),examine(3)]
    require(r[0]['pair_memberships_compared']==r[1]['pair_memberships_compared'] and r[0]['harmonic_endpoints']==r[1]['harmonic_endpoints'],'model equality of finite counts only')
    print(json.dumps(r,sort_keys=True,indent=2))
