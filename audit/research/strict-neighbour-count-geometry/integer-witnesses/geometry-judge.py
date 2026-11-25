"""Read exact arrays. All reference distances are recomputed from the original observations."""
from collections import Counter
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unique_object(pairs):
    answer = {}
    for key, val in pairs:
        require(key not in answer, "duplicate property")
        answer[key] = val
    return answer


def indices(points, rank, use_both):
    size = len(points)
    terms = []
    locations = []
    for anchor, (u, v, w) in enumerate(points):
        rows = [(min(abs(a-u), abs(b-v)) if use_both else abs(a-u), abs(c-w))
                for j,(a,b,c) in enumerate(points) if j != anchor]
        radius = sorted(max(pair) for pair in rows)[rank-1]
        require(radius > 0 and sum(max(pair) == radius for pair in rows) == 1,
                "positive single kth neighbour")
        x = 1 + sum(s < radius for s,t in rows)
        y = 1 + sum(t < radius for s,t in rows)
        corner = any(s == t == radius for s,t in rows)
        locations.append((x, y, corner))
        terms.append(H[rank-1] + H[size-1] - H[x-1] - H[y-1])
    return locations, terms


H = [sum((Fraction(1,i) for i in range(1,j+1)), Fraction(0)) for j in range(17)]


def all_pairs(n,k):
    # Enumerate the number of occupants of four mutually exclusive regions.
    return {(k+p,k+q) for p in range(n-k+1) for q in range(n-k-p+1)}


def check(doc):
    require(isinstance(doc,list), "array campaigns")
    expected = {(n,k,x,y) for n in range(2,10) for k in range(1,n)
                for x,y in all_pairs(n,k)}
    seen = set()
    observed = []
    mask = Counter()
    for case in doc:
        require(type(case) is dict and set(case)=={'n','k','x','y','kind','rows'}, "case properties")
        n,k,x,y = (case[key] for key in ('n','k','x','y'))
        require(all(type(j) is int for j in (n,k,x,y)), "integer labels")
        tag = n,k,x,y
        require(tag in expected and tag not in seen, "out of range, impossible or duplicate label")
        seen.add(tag)
        pts=case['rows']
        require(type(pts) is list and len(pts)==n and
                all(type(v) is list and len(v)==3 and
                    all(type(w) is int and abs(w).bit_length()<=200 for w in v) for v in pts), "input shape and integer coordinates")
        require(all(len(set(v))==n for v in zip(*pts)),"distinct component observations")
        category = "corner" if x==y==k else "open"
        require(case['kind']==category,"exceptional/open label")
        for name,both in (('KSG1',False),('Ehrlich',True)):
            at,terms = indices(pts,k,both)
            require(at[0] == (x,y,category=='corner'), "declared anchor and shell contact")
            for i,(xx,yy,c) in enumerate(at):
                require((xx,yy) in all_pairs(n,k), "other anchor count")
                low = H[k-1]+H[n-1]-H[(n+k)//2-1]-H[(n+k+1)//2-1]
                upper = H[n-1]-H[k-1]
                require(low<=terms[i]<=upper, "integer harmonic range")
                if (xx,yy)!=(k,k):
                    require(terms[i]<=upper-Fraction(1,k), "upper bound on noncorner count pairs")
            observed.append([*tag,name,[list(z) for z in at],str(terms[0]),str(sum(terms,Fraction(0))/n)])
        mask[category]+=1
    require(seen==expected,"exhaustive allowed count pairs")
    excluded=sum((n-k+1)**2-len(all_pairs(n,k)) for n in range(2,10) for k in range(1,n))
    raw=json.dumps(sorted(observed),separators=(',',':')).encode()
    return dict(sizes=list(range(2,10)),ranks=36,rectangle_outside=excluded,witness_arrays=len(doc),
                count_by_type=mask,mean_and_anchor_records=len(observed),all_rows_checked=sum(len(z[5]) for z in observed),
                exact_records_sha256=sha256(raw).hexdigest())


def mean_check(proposed):
    require(type(proposed) is list and len(proposed)==28,"upper case count")
    seen=set()
    results=[]
    for case in proposed:
        require(type(case) is dict and set(case)=={'n','kind','rows'}, "upper case fields")
        n,kind,pts=(case[k] for k in ('n','kind','rows'))
        require(type(n) is int and 2<=n<=15 and kind in ('open','corner') and (n,kind) not in seen,'upper identity')
        require(type(pts) is list and len(pts)==n and all(type(v) is list and len(v)==3 and all(type(i) is int for i in v) for v in pts),'upper array')
        require(all(len(set(v))==n for v in zip(*pts)),'upper distinct components')
        seen.add((n,kind))
        for k in range(1,n):
            for obj,both in (('KSG1',False),('Ehrlich',True)):
                loc,trm=indices(pts,k,both)
                if kind=='corner':
                    require(all(z==(k,k,True) for z in loc), 'all anchors at exceptional corner')
                else:
                    require(all(x+y==2*k+1 and not c for x,y,c in loc), 'all anchors at open upper')
                maximum = H[n-1]-H[k-1]-(0 if kind=='corner' else Fraction(1,k))
                require(all(t==maximum for t in trm) and sum(trm,Fraction(0))/n==maximum, 'exact mean is upper bound')
                results.append([n,k,obj,kind,str(maximum),len(trm)])
    return dict(arrays=len(proposed),means=len(results),all_rows_checked=sum(r[-1] for r in results),
                exact_records_sha256=sha256(json.dumps(sorted(results),separators=(',',':')).encode()).hexdigest())


if __name__=='__main__':
    mode,source=sys.argv[1:]
    data=json.loads(Path(source).read_bytes(),object_pairs_hook=unique_object)
    require(mode in ('triangle','upper'),'mode')
    print(json.dumps((check if mode=='triangle' else mean_check)(data),indent=2,sort_keys=True))
