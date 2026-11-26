"""Fixed LP4 reader for the copied-force target and the original five added-source positions."""
import hashlib
import json
import re
import sys
from collections import Counter
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from zipfile import ZipFile

ARCHIVE_SHA = "cdfbe0b260f4a21c5249fe0da4b1baf4041959663a9182253885ee1f41a4568e"
DATA_SHA = "f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c"
LABELS = {"normal", "collision", "obstruction"}
FIVE = ((4,), (5,), (6,), (5, 6), (7,))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_raw(path):
    data = path.read_bytes()
    if sha(data) == ARCHIVE_SHA:
        with ZipFile(path) as archive:
            found = [k for k in archive.namelist() if Path(k).name == "lp4.data"]
            require(len(found) == 1, "one original LP4 archive member")
            data = archive.read(found[0])
    require(sha(data) == DATA_SHA and len(data) == 33619, "original LP4 data member")
    return data

def slope_sign(readings):
    numerator = sum((i - 7) * value for i, value in enumerate(readings))
    return (numerator > 0) - (numerator < 0)

def table_from_episodes(raw):
    lines = [line.strip() for line in raw.decode("ascii").splitlines() if line.strip()]
    require(len(lines) == 117 * 16, "117 distinct donor episodes of 15 moments")
    table = Counter()
    for start in range(0, len(lines), 16):
        require(lines[start] in LABELS, "one donor label opens an episode")
        data = [line.split() for line in lines[start+1:start+16]]
        require(all(len(r) == 6 and all(re.fullmatch(r"[+-]?[0-9]+",v) for v in r) for r in data), "six integer channels")
        x, w = (slope_sign([int(r[col]) for r in data]) for col in (2,5))
        table[x,w] += 1
    return table

def is_subset(a, b):
    return a & b == a

def below(a, b):
    return all(any(is_subset(u, v) for u in a) for v in b)

def antichains():
    rules = []
    for n in range(1,8):
        for a in combinations(range(1,8),n):
            if not any(is_subset(i,j) or is_subset(j,i) for i,j in combinations(a,2)):
                rules.append(a)
    require(len(rules) == 18, "eighteen nonempty proper rule antichains")
    topo = sorted(rules,key=lambda a:sum(below(b,a) for b in rules))
    require(set(FIVE) == {a for a in topo if not below(a,(3,))}, "five slots outside the 12-pair downset")
    return topo

def prod(values):
    result = Fraction(1)
    for v in values:
        result *= v
    return result

def atom_inversion(cumulative, rules):
    atoms = {}
    for a in rules:
        atoms[a] = cumulative[a] / prod(atoms[b] for b in atoms if below(b,a))
    require(all(prod(atoms[b] for b in rules if below(b,a)) == cumulative[a] for a in rules), "reconstruct every cumulative product")
    return atoms

def rule_name(a):
    return "+".join(f"{m:02x}" for m in a)

def signed_string(q, n):
    with localcontext() as ctx:
        ctx.prec = 52
        return str((Decimal(q.numerator).ln()-Decimal(q.denominator).ln())/Decimal(n))

def analyze(table):
    require(table and all(isinstance(n,int) and n>0 for n in table.values()), "positive occupied cell counts")
    n = sum(table.values()); rules = antichains()
    rs = Counter(); cs = Counter()
    for (x,w), count in table.items():
        rs[x] += count; cs[w] += count
    channels = ("informative","misinformative","signed")
    global_q = {k:{a:Fraction(1) for a in rules} for k in channels}
    local_a = {k:{a:Fraction(1) for a in rules} for k in channels}
    analytic = Fraction(1); obstruct = []; row_reference = []
    for (x,w), count in sorted(table.items()):
        q = {k:{} for k in channels}
        for rule in rules:
            u=v=0
            for (y,z),c in table.items():
                point=(y,0,z); anchor=(x,0,w)
                accepted=any(all(point[i]==anchor[i] for i in range(3) if m & (1<<i)) for m in rule)
                if accepted:
                    u += c
                    if y == x: v += c
            require(v>=count and v<=min(u,rs[x]), "positive observed query intersection")
            q["informative"][rule]=Fraction(n,u)
            q["misinformative"][rule]=Fraction(rs[x],v)
            q["signed"][rule]=Fraction(n*v,u*rs[x])
        for k in channels:
            atoms=atom_inversion(q[k],rules)
            for a in rules:
                global_q[k][a] *= q[k][a]**count
                local_a[k][a] *= atoms[a]**count
        h=Fraction(rs[x]*cs[w],count*(rs[x]+cs[w]-count))
        require(h>=1,"cell cancellation sign")
        analytic *= h**count
        if rs[x]>count and cs[w]>count: obstruct.append([x,w])
        row_reference.append({"x":x,"w":w,"count":count,"row":rs[x],"column":cs[w],"factor":str(h)})
    for k in channels:
        require(atom_inversion(global_q[k],rules)==local_a[k],"local inversion and full count-weighted inversion commute")
    require(all(local_a["signed"][a]==local_a["informative"][a]/local_a["misinformative"][a] for a in rules),"component quotient")
    five={rule_name(a):local_a["signed"][a] for a in FIVE}
    expected={"04":1/analytic,"05":analytic,"06":Fraction(1),"05+06":Fraction(1),"07":Fraction(1)}
    require(five==expected and prod(five.values())==1,"all five exact measures and zero net gain")
    magn=prod(max(v,1/v) for v in five.values())
    require(magn==analytic**2 and (magn==1)==(not obstruct),"independent analytic and support criterion")
    return {"N":n,"occupied_pairs":len(table),"cell_criteria":row_reference,"nonstar_cells":obstruct,"absolute_product":str(magn),"M_nats":signed_string(magn,n),"set_all_five_to_zero":magn==1,"five_signed_products":{a:str(v) for a,v in five.items()},"five_signed_means_nats":{a:signed_string(v,n) for a,v in five.items()},"all108":{rule_name(a):{k:{"cumulative":str(global_q[k][a]),"atom":str(local_a[k][a])} for k in channels} for a in rules}}

def controls():
    one=analyze({(0,0):1}); require(one["set_all_five_to_zero"],"constant law")
    star=analyze({(0,0):1,(0,1):1,(1,2):1}); require(star["set_all_five_to_zero"],"support star")
    path=analyze({(0,0):1,(1,1):1,(1,2):1,(2,1):1})
    require(path["absolute_product"]=="16/9" and path["five_signed_products"]["04"]=="3/4" and path["five_signed_products"]["05"]=="4/3","known four-observation counterexample")
    doubled=analyze({(0,0):2,(1,1):2,(1,2):2,(2,1):2})
    require(Fraction(doubled["absolute_product"])==Fraction(path["absolute_product"])**2,"count weights reflect duplicated observations")
    return ["constant","star","four-observation nonstar","duplicated observations"]

def main():
    c=controls()
    if sys.argv[1:]==["--self-test"]: print(json.dumps(c));return
    require(len(sys.argv)==2,"supply authentic raw lp4.data or original ZIP")
    r=analyze(table_from_episodes(read_raw(Path(sys.argv[1]))))
    print(json.dumps({"source":DATA_SHA,"controls":c,"scientific_result":r},sort_keys=True,indent=2))

if __name__=="__main__":
    main()
