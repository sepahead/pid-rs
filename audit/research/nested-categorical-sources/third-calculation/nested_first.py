"""Exact finite experiments on nested categorical source partitions and the gap on failure."""
from collections import Counter,defaultdict
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations
import json

def need(value,reason):
    if not value: raise ValueError(reason)

def six_counts(n,k):
    if k==1:
        yield (n,)
        return
    for head in range(n+1):
        for tail in six_counts(n-head,k-1):
            yield (head,)+tail

def lower(a,b):
    return all(any(s&t==s for s in a) for t in b)

def indices():
    subsets=(j for j in range(1,8))
    groups=tuple(subsets);collection=[]
    for k in range(1,8):
        for row in combinations(groups,k):
            if any(s!=t and s&t==s for s in row for t in row):continue
            collection.append(row)
    return collection

def field(table):
    rows=[(k,v) for k,v in table.items() if v>0]
    N=sum(k for row,k in rows)
    a=indices()
    get=lambda row,mask:tuple(v for i,v in enumerate(row[:3]) if mask&(1<<i))
    probabilities=[]
    for alpha in a:
        plus=Q(1); minus=Q(1)
        for key,count in rows:
            z=[any(get(key,s)==get(row,s) for s in alpha) for row,c in rows]
            union=sum(c for (r,c),include in zip(rows,z) if include)
            inter=sum(c for (r,c),include in zip(rows,z) if include and r[-1]==key[-1])
            target=sum(c for r,c in rows if r[-1]==key[-1])
            plus*=Q(N,union)**count
            minus*=Q(target,inter)**count
        probabilities.append((plus,minus,plus/minus))
    reach={alpha:{beta for beta in a if lower(beta,alpha)} for alpha in a}
    need(sum(map(len,reach.values()))==129,"orientation of all 18 cumulative sums")
    atoms={}
    for alpha in sorted(a,key=lambda s:len(reach[s])):
        v=list(probabilities[a.index(alpha)])
        for l in reach[alpha]-{alpha}:
            v=[c/d for c,d in zip(v,atoms[l])]
        atoms[alpha]=tuple(v)
    return a,probabilities,atoms

def check_nested(table):
    a,c,atoms=field(table)
    lev={1:c[a.index((1,))],2:c[a.index((2,))],3:c[a.index((4,))]}
    active={1:(1,2,4),2:(2,4),3:(4,)}
    for idx,alpha in enumerate(a):
        k=min(group.bit_length() for group in alpha)
        want=lev[k];need(c[idx]==want,"all 54 cumulative values")
        pos=[j for j,q in active.items() if q==alpha]
        vals=tuple(Q(1) for i in range(3))
        if pos:
            j,=pos
            vals=tuple(v/u for v,u in zip(lev[j],lev.get(j-1,(Q(1),)*3)))
        need(atoms[alpha]==vals,"all 54 inverted atom values")
    return {str(a.index(active[k])):[str(x) for x in atoms[active[k]]] for k in active}

def gap(flat,nx,ny):
    cells=dict(((i,j),flat[ny*i+j]) for i in range(nx) for j in range(ny))
    marg=[sum(k for (s,t),k in cells.items() if s==i) for i in range(nx)]
    sub=[sum(k for (s,t),k in cells.items() if t==j) for j in range(ny)]
    bad=any(sum(cells[i,j]>0 for i in range(nx))>1 for j in range(ny))
    val=Q(1)
    for (i,j),c in cells.items():
        if c: val*=Q(marg[i]+sub[j]-c,marg[i])**c
    return val,bad

def expected(N):
    a=N//2;b=N-a
    return Q((a+1)*(b+1),a*b)

def probe():
    observations={}
    for nx,ny,last in ((2,3,9),(3,2,8),(3,3,6)):
        found={}
        for size in range(2,last+1):
            wanted=expected(size);best=None;matches=0;total=0;fail=0
            for cells in six_counts(size,nx*ny):
                value,bad=gap(cells,nx,ny);total+=1
                need((value!=1)==bad,"recognition in both directions")
                if not bad:continue
                fail+=1
                need(value>=wanted,("fixed total lower bound",size,nx,ny,cells))
                if value==wanted:matches+=1
                if best is None or value<best:best=value
            # Three fine states suffice for two unrestricted coarse marginals.
            if ny>=3 or size<=3:need(best==wanted and matches>0,"attainment on this alphabet")
            found[str(size)]={"all":total,"failed":fail,"least_in_tested_alphabet":str(best),"sharp_target":str(wanted),"equal":matches}
        observations[str((nx,ny))]=found
    for n in range(2,257):
        a=n//2;b=n-a
        val,bad=gap((1,a-1,0,1,0,b-1),2,3)
        need(bad and val==expected(n),"explicit sharpness family")
    return observations

def run():
    table={(f//4,f//2,f,t):(f+1 if t else 9-f) for f in range(8) for t in range(2)}
    output={"all_108_on_weighted_16_cells":check_nested(table),"all_108_on_one_constant":check_nested({(0,0,0,0):1}),"gap":probe()}
    return output
if __name__=="__main__":
    print(json.dumps(run(),sort_keys=True,indent=2))
