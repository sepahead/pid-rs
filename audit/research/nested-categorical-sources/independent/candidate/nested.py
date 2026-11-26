"""Exact products for three categorical measurements with nested partitions."""
from fractions import Fraction

FAMILIES = (
    "01", "02", "03", "04", "05", "06", "07", "01+02", "01+04",
    "01+06", "02+04", "02+05", "03+04", "03+05", "03+06", "05+06",
    "01+02+04", "03+05+06",
)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def checked_counts(rows, order):
    require(type(order) in (list,tuple) and len(order)==3 and
            all(type(j) is int for j in order) and set(order)=={0,1,2},"source permutation")
    require(type(rows) is list and rows,"no occupied row")
    observed=set()
    maps=[{},{}]
    for row in rows:
        require(type(row) is list and len(row)==5 and all(type(x) is int for x in row),"five integer fields")
        require(row[4]>0 and all(s>=0 for s in row[:4]),"positive count and finite state identifiers")
        point=tuple(row[:4]);require(point not in observed,"duplicate complete state")
        observed.add(point)
        for step,mapping in enumerate(maps):
            coarse,fine=row[order[step]],row[order[step+1]]
            require(mapping.setdefault(fine,coarse)==coarse,"finer state has two coarse values")

def add(table,key,weight):
    table[key]=table.get(key,0)+weight

def level_products(rows, source, total, target):
    state={}
    joint={}
    for row in rows:
        u,t,w=row[source],row[3],row[4]
        add(state,u,w)
        add(joint,(u,t),w)
    plus=Fraction(1)
    for marginal in state.values():
        plus *= Fraction(total,marginal)**marginal
    minus=Fraction(1)
    for (_,t),weight in joint.items():
        minus *= Fraction(target[t],weight)**weight
    return [plus,minus,plus/minus]

def products(rows, order):
    """Return all 108 stable-key products. Each value is exp(N times a mean in nats)."""
    checked_counts(rows,order)
    target={}
    for row in rows:add(target,row[3],row[4])
    total=sum(target.values())
    unit=[Fraction(1) for _ in range(3)]
    levels=[unit]+[level_products(rows,source,total,target) for source in order]
    atoms={family:unit.copy() for family in FAMILIES}
    for j in range(1,4):
        key="+".join(sorted(f"{1 << i:02x}" for i in order[j-1:]))
        atoms[key]=[nextval/old for nextval,old in zip(levels[j],levels[j-1],strict=True)]
    result={}
    for family in FAMILIES:
        masks=[int(m,16) for m in family.split("+")]
        level=min(max(j for j,source in enumerate(order,1) if mask & (1<<source)) for mask in masks)
        result[family]={"cumulative":levels[level].copy(),"atom":atoms[family]}
    return result
