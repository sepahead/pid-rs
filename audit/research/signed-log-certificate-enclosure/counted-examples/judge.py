"""Independently test the incidence calculation and the selected observed intervals."""
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import importlib.util
import json
from pathlib import Path
import sys

EXPECTED = "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2"
PRECISIONS = (256, 384, 512, 768, 1024, 1536, 2048)

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def original(path):
    require(sha256(path.read_bytes()).hexdigest() == EXPECTED, "original bytes")
    spec = importlib.util.spec_from_file_location("fixed_arithmetic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def lower_covers(top, lower):
    return all(any((a & b) == a for a in lower) for b in top)

def finite_inverse(source):
    groups = tuple(range(1, 8))
    nodes = []
    for n in range(1, 8):
        for carrier in combinations(groups, n):
            if all(a & b not in (a, b) for a, b in combinations(carrier, 2)):
                nodes.append(carrier)
    zeta = [[int(lower_covers(top, lower)) for lower in nodes] for top in nodes]
    size = len(nodes)
    unit = [[int(i == j) for j in range(size)] for i in range(size)]
    extended = [[Fraction(v) for v in zeta[i] + unit[i]] for i in range(size)]
    for j in range(size):
        pivot = next(i for i in range(j, size) if extended[i][j])
        extended[j], extended[pivot] = extended[pivot], extended[j]
        scale = extended[j][j]
        extended[j] = [v / scale for v in extended[j]]
        for i, row in enumerate(extended):
            if i != j:
                coefficient = row[j]
                extended[i] = [x - coefficient*y for x, y in zip(row, extended[j])]
    require(all(r[:size] == u for r, u in zip(extended, unit)), "reduction")
    require(all(v.denominator == 1 for r in extended for v in r[size:]), "integer inverse")
    inverse = [[int(v) for v in row[size:]] for row in extended]
    keys, supplied_z, supplied_inv = source.lattice()
    require(set(keys) == set(nodes) and size == 18, "carrier")
    position = [keys.index(g) for g in nodes]
    for derived, reference in ((zeta, supplied_z), (inverse, supplied_inv)):
        require(all(derived[i][j] == reference[a][b] for i,a in enumerate(position)
                    for j,b in enumerate(position)), "permuted equality")
    for a,b in ((zeta,inverse),(inverse,zeta)):
        require(all(sum(a[i][h]*b[h][j] for h in range(size)) == unit[i][j]
                    for i in range(size) for j in range(size)), "two-sided independence")
    norms = [sum(map(abs,row)) for row in inverse]
    require(1 <= max(norms) <= 18, "candidate norm bound")
    return {"nodes":nodes, "rows":inverse,"norms":norms,"maximum":max(norms),
            "extremizers":[n for n,v in zip(nodes,norms) if v == max(norms)]}

def rows_for(counts):
    return [{"source_states":[[label],[label],[label]],"target_state":[label],
             "count":str(count)} for label,count in zip(("a","b"),counts)]

def selected(source, n, k, p):
    require(2<=n<=3000 and 1<=k<=n//2 and p in PRECISIONS,"selected field")
    rows = rows_for((k,n-k))
    table,total,lengths = source.typed_rows(rows)
    require(total == n, "total")
    reservation = source.reserve(table,total,lengths)
    entries = list(source.projections(source.base_plans(table,total)))
    preflight = source.preflight(entries)
    plans = {key[:3]:plan for key,plan in entries}
    require(len(plans) == len(entries) == 108,"unique coordinates")
    q = Fraction(n**n,k**k*(n-k)**(n-k))
    for key,plan in plans.items():
        result = source.exact_product(plan)
        if key[0] == "cumulative":
            require(result == (1 if key[1] == "misinformative" else q),"all cumulative plans")
    value = source.exact_product(plans["cumulative","net","01"])
    require(value == q, "actual product")
    pair = [endpoint*(1<<p) for endpoint in source.log_interval(value,n,p)]
    require(all(x.denominator == 1 for x in pair),"integer grid")
    require(pair[1]-pair[0] == 2,"two-grid witness")
    digest = sha256((hex(q.numerator)+"/"+hex(q.denominator)).encode()).hexdigest()
    return {"p":p,"N":n,"k":k,"rows":rows,"q_hex_digest":digest,
            "reservation":list(reservation),"preflight_108":list(preflight),
            "grid":list(map(int,pair))}

def run():
    src = original(Path(sys.argv[1]))
    search = json.loads(Path(sys.argv[2]).read_text())
    lattice = finite_inverse(src)
    require(search["precisions"] == list(PRECISIONS),"schedule")
    require(len(search["search"]) == len(PRECISIONS),"fields")
    witnesses = []
    for p,case in zip(PRECISIONS,search["search"]):
        require(case["p"] == p and case["screened"] >= case["computed"] >= 0,"records")
        record = case["result"]
        if record:
            checked = selected(src,record["N"],record["k"],p)
            require(checked["grid"] == record["grid"],"original endpoints")
            witnesses.append(checked)
        else:
            require(case["searched_through"] == 3000,"incomplete search")
    table,total,lengths = src.typed_rows(rows_for((1,1))[:1])
    src.reserve(table,total,lengths)
    entries = list(src.projections(src.base_plans(table,total)))
    src.preflight(entries)
    require(total == 1 and all(src.exact_product(pl) == 1 and
                all(src.log_interval(src.exact_product(pl),1,p) == (0,0) for p in PRECISIONS)
                for key,pl in entries),"one occupied observation")
    require(1387 < 64*22 and 1387*91 < 1<<24,"strict cut for both total sizes")
    output = {"spec":EXPECTED,"N1_zero":True,"incidence":lattice,"witnesses":witnesses}
    print(json.dumps(output,sort_keys=True,indent=2))

if __name__ == "__main__":
    run()
