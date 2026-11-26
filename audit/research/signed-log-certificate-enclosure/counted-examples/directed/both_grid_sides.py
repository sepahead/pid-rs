"""Test all 999² four-row reveal/erase count pairs at each of the seven precisions.

Arguments are the original check.py and an optional new directory for eight full reports.
"""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys


READER = "9a6c3746937fa0db7ceaf1fc96a6753ce547948412133690778309781e60d1d6"
KEY = "cumulative.net.01"
GUARD = 1 << 24


def require(predicate, explanation):
    if not predicate:
        raise ValueError(explanation)


def hashed(data):
    return sha256(data).hexdigest()


def half_log(d, terms):
    """Return the transformed log via a positive rational sum and geometric tail."""
    total = Fraction()
    power = Fraction(1, d)
    square = power * power
    for i in range(terms):
        total += 2 * power / (2*i+1)
        power *= square
    return total, total + 2 * power / ((2*terms+1) * (1-square))


def log_two(terms):
    bounds = [half_log(d, terms) for d in (5,7)]
    return tuple(sum(x[j] for x in bounds) for j in (0,1))


def locate(ref, p, m, n):
    # Endpoint multiplication is exact, independently of the original fixed-grid helper.
    s = Fraction((1 << p)*m, n)
    lower, upper = (s*v for v in ref)
    a = lower.numerator // lower.denominator
    return a if a < lower < upper < a+1 else None


def data(reader, n, m):
    rows = [{"count": str(count), "source_states": [[a],["fixed"],["fixed"]],"target_state":[t]}
            for a,t,count in (("0","0",m//2),("0","x",(n-m)//2),("1","1",m//2),("1","x",(n-m)//2))]
    obj = {"definition_revision":reader.IDS["definition_revision"], "rows":rows,
           "schema":reader.IDS["input_schema"], "sources":3, "units":"nats"}
    return reader.canonical(obj)


def check_counted_hit(reader, n, m, p, a):
    raw = data(reader,n,m)
    table, total, base, resources = reader.derive(raw)
    require(len(table)==4 and total==n, "admitted original four-cell source")
    plans = list(reader.A.projections(base))
    require(len(plans)==108, "original coordinate count")
    applied = {k[1]: plan for k,plan in plans if k[0]=="cumulative" and k[2]=="01" and k[3]==(1,)}
    require(applied == {"informative": {Fraction(2):n}, "misinformative": {Fraction(2):n-m},
                        "net": {Fraction(2):m}}, "original counted roles")
    q = reader.A.exact_product(applied["net"])
    require(q == Fraction(1 << m), "genuine rational product")
    low,high = reader.A.log_interval(q,n,p)
    integer_pair = (int(low * (1<<p)),int(high * (1<<p)))
    require(integer_pair in ((a-1,a+1),(a,a+2)), "actual crossing of the true p-cell")
    return {"N":n,"m":m, "revealed_each":m//2,"erased_each":(n-m)//2,
            "side":"lower" if integer_pair[0]==a-1 else "upper",
            "input_sha256":hashed(raw),"max_projected_coordinate_bits":resources["maximum_projected_coordinate_bits"],
            "aggregate_projected_product_bits":resources["aggregate_projected_product_bits"]}


def corpus(reader, p, ref):
    low,high = reader.A.log_two(p+24)
    width = high-low
    require(0<width<GUARD,"positive subgrid log-two width")
    hits, refused, extended = [], [], []
    examined=0
    for n in range(4,3997,2):
        m0,mlast=max(2,n-1998),min(n-2,1998)
        denominator=n*GUARD
        step=(2*low)%denominator
        residue=(m0*low)%denominator
        for m in range(m0,mlast+1,2):
            examined+=1
            if residue + m*width > denominator:
                a=locate(ref,p,m,n)
                if a is None:
                    extended.append([n,m])
                    a=locate(log_two(700),p,m,n)
                require(a is not None,"truth cell unresolved at both allowed orders")
                try:
                    hit=check_counted_hit(reader,n,m,p,a)
                except (reader.Refusal,reader.A.ArithmeticReject) as error:
                    refused.append({"N":n,"m":m,"reason":str(error)})
                else:
                    hits.append(hit)
            residue+=step
            if residue>=denominator:
                residue-=denominator
    require(examined==999**2,"complete 999 by 999 integer grid")
    counts={s:sum(row["side"]==s for row in hits) for s in ("lower","upper")}
    first={s:next((row for row in hits if row["side"]==s),None) for s in counts}
    return {"precision":p,"pairs_examined":examined,"counts":counts, "first_admitted":first,
            "original_input_refusals":refused,"extra_truth_order_required":extended,"all_admitted":hits}


def complete_sequence(reader, ref, n, m, side, output):
    p=2048
    scale=1 << p
    a=locate(ref,p,m,n)
    if a is None:
        a=locate(log_two(700),p,m,n)
    require(a is not None,"strict finest cell")
    raw_b=data(reader,n,m)
    _, total, base, resources=reader.derive(raw_b)
    binding=reader.bindings(raw_b)
    records=[]
    for (scope,component,key,masks),plan in reader.A.projections(base):
        identity=".".join((scope,component,key))
        q=reader.A.exact_product(plan)
        if identity==KEY:
            interval=(Fraction(a,scale),Fraction(a+1,scale))
        else:
            interval=reader.A.log_interval(q,total,256)
        records.append({"scope":scope,"component":component,"coordinate":identity,"key":key,"masks":list(masks),
                        "bindings":binding,"product":{"schema":reader.IDS["product_schema"],
                        "numerator":str(q.numerator),"denominator":str(q.denominator)},
                        "interval":{"schema":reader.IDS["interval_schema"],"lower":reader.dyadic(interval[0]),
                                    "upper":reader.dyadic(interval[1])},
                        "sign":"positive" if q>1 else "negative" if q<1 else "zero"})
    payload={k:reader.IDS[k] for k in reader.WIRE["payload"] if k not in ("resources","coordinates")}
    payload.update(resources=resources,coordinates=records)
    report={"schema":reader.IDS["producer_schema"],"payload":payload}
    statuses=[]
    material={}
    require(len(raw_b)<=reader.INPUT_CAP,"original input byte bound")
    for label,left,right in (("tight",0,0),("lower",1,0),("upper",0,1),("both",1,1)):
        candidate=deepcopy(report)
        value=next(x for x in candidate["payload"]["coordinates"] if x["coordinate"]==KEY)["interval"]
        lo,hi=Fraction(a-left,scale),Fraction(a+1+right,scale)
        value.update(lower=reader.dyadic(lo),upper=reader.dyadic(hi))
        require(reader.endpoint(value["lower"])==lo and reader.endpoint(value["upper"])==hi and
                hi-lo<=reader.A.MAX_WIDTH,"actual dyadic endpoint and width guard")
        raw_c=reader.canonical(candidate)
        if len(raw_c)>reader.REPORT_CAP:
            return None,{"N":n,"m":m,"source-admitted":True,"case":label,"bytes":len(raw_c),"reason":"report capacity"}
        try:
            _,seen_total,obs,_=reader.audit(raw_b,raw_c)
        except reader.Refusal as err:
            require(str(err)=="independent interval containment","only the target may reject")
            verdict="independent interval containment"
        else:
            observed=[x for x in obs if x["coordinate"]==KEY]
            require(len(obs)==108 and seen_total==n and len(observed)==1 and observed[0]["precision_bits"]==2048,
                    "last-field acceptance")
            require(all(x["precision_bits"]==256 for x in obs if x["coordinate"]!=KEY),"other 107")
            verdict="108 pass"
        expected=(left if side=="lower" else right)
        require((verdict=="108 pass")==bool(expected),"full one-sided reader decision")
        material["C-"+label+".json"]=raw_c
        statuses.append({"coordinate_interval":label,"verdict":verdict,"sha256":hashed(raw_c),"bytes":len(raw_c)})
    material["B.json"]=raw_b
    if output:
        folder=output/side
        folder.mkdir()
        for filename,content in material.items():
            (folder/filename).write_bytes(content)
    return {"N":n,"m":m,"side_needed":side,"input_sha256":hashed(raw_b),"true_cell_lower_numerator":str(a),
            "reports":statuses},None


def main(check, output):
    require(hashed(check.read_bytes())==READER,"original full report reader")
    spec=importlib.util.spec_from_file_location("typed_six_table_reader",check)
    reader=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    ref=log_two(500)
    if output:
        output.mkdir(parents=True,exist_ok=False)
    result=[corpus(reader,p,ref) for p in reader.A.SCHEDULE]
    require(sum(x["pairs_examined"] for x in result)==7*999**2,"schedule and total")
    chosen, failed = {},[]
    for side in ("lower","upper"):
        for hit in result[-1]["all_admitted"]:
            if hit["side"]!=side:
                continue
            actual,reject=complete_sequence(reader,ref,hit["N"],hit["m"],side,output)
            if reject:
                failed.append(reject)
            else:
                chosen[side]=actual
                break
    print(json.dumps({"source_check_sha256":READER,"source_arithmetic_sha256":reader.ARITHMETIC_SHA,
       "scope":"exact finite four-row equal-source reveal/erase family; counts per cell 1..999; full new synthetic reports only for chosen 2048 examples",
       "fields":result,"finest_complete":chosen,"finest_wire_capacity_refusals":failed},indent=2,sort_keys=True))


if __name__=="__main__":
    main(Path(sys.argv[1]),Path(sys.argv[2]) if len(sys.argv)>2 else None)
