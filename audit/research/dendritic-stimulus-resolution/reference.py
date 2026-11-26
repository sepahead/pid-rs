"""Verify the three fixed choices of retained source resolution on the published control grid."""
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
import math

WIDTHS=(10,50,100)
CUT=("04","05","06","05+06","07")
def need(condition,name):
    if not condition: raise ValueError(name)
def encode(q):
    return [format(q.numerator,"x"),format(q.denominator,"x")]
def show(q):
    if q==1: return 0.0
    return (math.log(q.numerator)-math.log(q.denominator))/651

def parse(raw):
    lines=raw.decode("ascii").splitlines()
    rows=[line.split() for line in lines]
    need(len(rows)==31 and all(len(row)==21 for row in rows),"31 basal by 21 tuft")
    values=[]
    for i,row in enumerate(rows):
        for j,s in enumerate(row):
            x=Decimal(s)
            need(x in range(5),"spike value")
            values.append((10*i,10*j,0 if x==0 else 1 if x<=2 else 2))
    return values

def marginals(data,columns):
    return Counter(tuple(k[i] for i in columns) for k in data)
def conditional_product(data, a,b):
    ab=marginals(data,a+b)
    n=marginals(data,a)
    return math.prod((Fraction(n[z[:len(a)]],f)**f for z,f in ab.items()),start=Fraction(1))

def reference(readings,width,ar):
    records=[(b//width,a//width,int(b>a),y) for b,a,y in readings]
    model=Counter(records)
    vals=sorted(model)
    tab=[(z,model[z]) for z in vals]
    zeta=ar["lattice"]()[1]
    base=ar["base_plans"](tab,len(records))
    atom={}
    for (scope,channel,node,masks),plan in ar["projections"](base):
        if scope=="atom":
            atom.setdefault(channel,{})[node]=ar["exact_product"](plan)
    nodes=ar["lattice"]()[0]
    names=["+".join(format(mask,"02x") for mask in family) for family in nodes]
    def output_series(series):
        return [encode(series[n]) for n in names]
    # Minimum specific information at each target value, compared as exact products.
    ttot=Counter(z[3] for z in records)
    keys={m:tuple(j for j in range(3) if m&(1<<j)) for m in range(1,8)}
    specs={}
    for mask,which in keys.items():
        cells=marginals(records,which+(3,))
        states=marginals(records,which)
        for target,n in ttot.items():
            specs[mask,target]=math.prod((Fraction(k*len(records),states[z[:-1]]*n)**k
                   for z,k in cells.items() if z[-1]==target), start=Fraction(1))
    imin={}
    mu=ar["lattice"]()[2]
    cumulative=[math.prod((min(specs[mask,target] for mask in family) for target in ttot),start=Fraction(1)) for family in nodes]
    for i,name in enumerate(names):
        imin[name]=math.prod((v**c for v,c in zip(cumulative,mu[i]) if c),start=Fraction(1))
    A=conditional_product(records,(0,1),(2,))
    B=conditional_product(records,(0,1,3),(2,))
    J=A/B
    for ch,total in [("informative",A),("misinformative",B),("net",J)]:
        need(math.prod((atom[ch][k] for k in CUT),start=Fraction(1))==total,"five-position identity")
    need(all(v>=1 for v in imin.values()),"I_min positivity")
    need(math.prod((imin[k] for k in CUT),start=Fraction(1))==J,"five I_min atoms")
    if width==10:
        need(all(atom[c][k]==1 for c in atom for k in CUT),"determined full-resolution flag")
    groups=[]
    bypair=defaultdict(list)
    for x,a,c,y in records: bypair[x,a].append((c,y))
    for (x,a),part in sorted(bypair.items()):
        without=max(Counter(y for c,y in part).values())
        withflag=sum(max(Counter(y for c2,y in part if c2==c).values()) for c in sorted({c for c,y in part}))
        groups.append([x,a,len(part),without,withflag])
    held={}
    for axis,slot in (("basal",0),("tuft",1)):
        predictions={}
        for lev in sorted({k[slot] for k in readings}):
            training=[rec for raw,rec in zip(readings,records) if raw[slot]!=lev]
            evaluations=[(raw,rec) for raw,rec in zip(readings,records) if raw[slot]==lev]
            for raw,rec in evaluations:
                stats=[]
                for num in (2,3):
                    counts=Counter(t[-1] for t in training if t[:num]==rec[:num])
                    label=max(range(3),key=lambda t:counts[t])
                    stats.extend([label,counts[rec[3]]+1,sum(counts.values())+3])
                predictions[raw[:2]]=list(raw)+stats
        held[axis]=[predictions[raw[:2]] for raw in readings]
    table={"keys":names,"informative":output_series(atom["informative"]),"misinformative":output_series(atom["misinformative"]),
          "signed":output_series(atom["net"]),"imin":output_series(imin),"groups":groups,"withheld":held}
    neg=math.prod((1/atom["net"][k] for k in CUT if atom["net"][k]<1),start=Fraction(1))
    detailed={c:{k:show(atom[c][k]) for k in CUT} for c in atom}
    metrics={axis:{str(f):{"correct":sum(row[f]==row[2] for row in probs),
        "mean_log_loss":math.fsum(math.log(row[f+2]/row[f+1]) for row in probs)/len(probs)}
        for f in (3,6)} for axis,probs in held.items()}
    brief={"N":len(records),"support":len(model),"target_counts":dict(ttot),"A":show(A),"B":show(B),"gain_nats":show(J),
        "negative_mass_nats":show(neg),"M_nats":show(J*neg**2),"signed_five":detailed["net"],
        "informative_five":detailed["informative"],"misinformative_five":detailed["misinformative"],
        "imin_five":{k:show(imin[k]) for k in CUT},"correct_without":sum(row[3] for row in groups),
        "correct_with":sum(row[4] for row in groups),"gains_by_bin":[v for v in groups if v[4]!=v[3]],"held_levels":metrics}
    if width==10:
        ht=conditional_product(records,(),(3,))
        hx=conditional_product(records,(0,),(3,))
        hy=conditional_product(records,(1,),(3,))
        hxy=conditional_product(records,(0,1),(3,))
        brief["compare_published_bits"]=[show(v)/math.log(2) for v in (ht/hx,ht/hy,hy/hxy,hx/hxy,ht/hxy,hx*hy/(ht*hxy),ht)]
    return table,brief
