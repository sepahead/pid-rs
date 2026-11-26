"""Construct true grid cells and test the original subset decision on a finite count table."""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import runpy

READ = "9a6c3746937fa0db7ceaf1fc96a6753ce547948412133690778309781e60d1d6"
FIELDS = ((256,1444,1434),(384,1364,1170),(512,1866,998),(768,1708,1494),
          (1024,408,386),(1536,1108,1054),(2048,1706,538))

def need(test, why):
    if not test: raise ValueError(why)

def exact_log_two(terms):
    partial = Fraction(0)
    power = Fraction(1,3)
    for i in range(terms):
        partial += 2*power/(2*i+1)
        power /= 9
    return partial, partial + 2*power/((2*terms+1)*Fraction(8,9))

def synthetic_input(reader,n,m):
    rows = []
    for label in ("0","1"):
        for target,count in ((label,m//2),("x",(n-m)//2)):
            rows.append({"count":str(count),"source_states":[[label],["fixed"],["fixed"]],
                         "target_state":[target]})
    fixed = reader["IDS"]
    return reader["canonical"]({"rows":rows,"schema":fixed["input_schema"],
                                "definition_revision":fixed["definition_revision"],
                                "units":"nats","sources":3})

def cell_test(reader, lower2, upper2, p,n,m):
    doc = synthetic_input(reader,n,m)
    cells,total,plans,resources = reader["derive"](doc)
    original = reader["A"]
    q, = [original.exact_product(plan) for key,plan in original.projections(plans)
          if key[:3] == ("cumulative","net","01")]
    need(q == 1<<m and total == n and len(cells) == 4,"genuine empirical input")
    scaled = Fraction(m<<p,n)
    a,b = lower2*scaled, upper2*scaled
    k = a.numerator//a.denominator
    need(k < a < b < k+1,"independent strict singleton grid cell")
    unit = Fraction(1,1<<p)
    tight = (k*unit,(k+1)*unit)
    padded = ((k-1)*unit,(k+2)*unit)
    endpoint, encode = reader["endpoint"],reader["dyadic"]
    for pair in (tight,padded):
        need(tuple(endpoint(encode(v)) for v in pair) == pair and
             0 <= pair[1]-pair[0] <= original.MAX_WIDTH,"original width and both codecs")
    observations = []
    for field in original.SCHEDULE:
        lo,hi = original.log_interval(q,n,field)
        observations.append({"p":field,"width":int((hi-lo)*(1<<field)),
                             "tight":tight[0] <= lo <= hi <= tight[1],
                             "padded":padded[0] <= lo <= hi <= padded[1]})
    atfield = next(z for z in observations if z["p"]==p)
    need(atfield["width"]==2 and not atfield["tight"] and atfield["padded"],"stage implication")
    if p==2048:
        need(not any(a["tight"] for a in observations),"true last-stage failure")
    return {"p":p,"N":n,"m":m,"lower_cell_index":str(k),"fields":observations,
            "preflight":resources,"true_cell":list(map(encode,tight)),
            "one_unit_each_side":list(map(encode,padded))}, doc

def constructed_report(reader,raw_b):
    _,total,plans,resources=reader["derive"](raw_b)
    fixed=reader["IDS"]
    original=reader["A"]
    payload={k:fixed[k] for k in reader["WIRE"]["payload"]
             if k not in ("resources","coordinates")}
    payload["resources"]=resources
    payload["coordinates"]=[]
    for (scope,component,key,masks),plan in original.projections(plans):
        q=original.exact_product(plan)
        lo,hi=original.log_interval(q,total,256)
        row={"scope":scope,"component":component,"key":key,"coordinate":".".join((scope,component,key)),
             "masks":list(masks),"bindings":reader["bindings"](raw_b),
             "product":{"schema":fixed["product_schema"],"numerator":str(q.numerator),
                        "denominator":str(q.denominator)},
             "sign":"zero" if q==1 else ("positive" if q>1 else "negative"),
             "interval":{"schema":fixed["interval_schema"],"lower":reader["dyadic"](lo),
                         "upper":reader["dyadic"](hi)}}
        payload["coordinates"].append(row)
    return {"schema":fixed["producer_schema"],"payload":payload}

def write_file(path,raw):
    if path.exists(): need(path.read_bytes()==raw,path)
    else: path.write_bytes(raw)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("original",type=Path)
    parser.add_argument("--fixtures",type=Path)
    args=parser.parse_args()
    reader_path=args.original/"check.py"
    need(sha256(reader_path.read_bytes()).hexdigest()==READ,"reader identity")
    reader=runpy.run_path(str(reader_path))
    lo2,hi2=exact_log_two(800)
    records=[]
    for p,n,m in FIELDS:
        record,raw_b=cell_test(reader,lo2,hi2,p,n,m)
        records.append(record)
    candidate=constructed_report(reader,raw_b)
    row,=[r for r in candidate["payload"]["coordinates"] if r["coordinate"]=="cumulative.net.01"]
    firstpair=[row["interval"]["lower"],row["interval"]["upper"]]
    receipts={}
    origin={"B":raw_b}
    for name,pair in (("baseline",firstpair),("tight",record["true_cell"]),
                      ("padded",record["one_unit_each_side"])):
        row["interval"]["lower"],row["interval"]["upper"]=pair
        raw=reader["canonical"](candidate)
        need(len(raw)<=reader["REPORT_CAP"],"full report size")
        origin[name]=raw
        try:
            _,total,results,products=reader["audit"](raw_b,raw)
        except reader["Refusal"] as failure:
            need(name=="tight" and str(failure)=="independent interval containment",
                 (name,"genuine failure",str(failure)))
            outcome={"reason":str(failure)}
        else:
            chosen,=[a for a in results if a["coordinate"]=="cumulative.net.01"]
            need(name!="tight" and len(results)==len(products)==108 and total==1706
                 and chosen["precision_bits"]==(256 if name=="baseline" else 2048),
                 (name,"full original decision"))
            outcome={"accepted_coordinates":108,"selected_precision":chosen["precision_bits"]}
        receipts[name]={"bytes":len(raw),"sha256":sha256(raw).hexdigest(),**outcome}
    need(origin["baseline"]!=origin["tight"]!=origin["padded"],"constructed distinct reports")
    if args.fixtures:
        args.fixtures.mkdir(parents=True,exist_ok=True)
        for key,raw in origin.items():write_file(args.fixtures/("synthetic-"+key+".json"),raw)
    result={"original_check":READ,"independent_positive_series_terms":800,"records":records,
            "constructed_input":{"bytes":len(raw_b),"sha256":sha256(raw_b).hexdigest()},
            "three_complete_synthetic_reports":receipts,
            "scope":"Invocation of audit on a constructed four-row input and three constructed reports. The six externally pinned original case pairs and their producer identity have independent evidence."}
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":
    main()
