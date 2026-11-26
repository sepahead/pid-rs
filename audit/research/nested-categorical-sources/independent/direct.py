"""Direct finite categorical shared-exclusion events and their full lattice inversion."""
from fractions import Fraction
from itertools import combinations
from math import prod

def demand(condition, what):
    if not condition:
        raise ValueError(what)

def carrier():
    groups=[frozenset(c) for n in range(1,4) for c in combinations(range(3),n)]
    result=[]
    for n in range(1,8):
        for family in combinations(groups,n):
            if all(not (a <= b or b <= a) for a,b in combinations(family,2)):
                result.append(family)
    return result

def key(family):
    return "+".join(f"{v:02x}" for v in sorted(sum(1 << j for j in group) for group in family))

def below(smaller,larger):
    return all(any(group <= branch for group in smaller) for branch in larger)

def products(rows,uniform_weights=False):
    weights=[1 if uniform_weights else row[4] for row in rows]
    total=sum(weights)
    families=carrier()
    demand(len(families)==len({key(f) for f in families})==18,"carrier")
    cum={}
    for f in families:
        plus=Fraction(1);minus=Fraction(1)
        for z,weight in zip(rows,weights,strict=True):
            event=[any(all(other[j]==z[j] for j in group) for group in f) for other in rows]
            same_target=[other[3]==z[3] for other in rows]
            u=sum(w for bit,w in zip(event,weights,strict=True) if bit)
            t=sum(w for bit,w in zip(same_target,weights,strict=True) if bit)
            v=sum(w for e,h,w in zip(event,same_target,weights,strict=True) if e and h)
            demand(0<weight<=v<=min(u,t)<=total,"input key lies in the event")
            plus *= Fraction(total,u) ** weight
            minus *= Fraction(t,v) ** weight
        cum[f]=(plus,minus,plus/minus)
    # The count of strict predecessors increases in every strict order step.
    predecessors={f:[b for b in families if b!=f and below(b,f)] for f in families}
    atoms={}
    for f in sorted(families,key=lambda f:len(predecessors[f])):
        atoms[f]=tuple(cum[f][u]/prod(atoms[b][u] for b in predecessors[f]) for u in range(3))
    return {key(f):{"cumulative":list(cum[f]),"atom":list(atoms[f])} for f in families}
