"""Compare two separately constructed exact rational computations at named lattice keys."""
from fractions import Fraction
from hashlib import sha256
import importlib.util,json,sys
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name,path):
    s=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(s)
    s.loader.exec_module(module)
    return module

def need(cond,why):
    if not cond:raise ValueError(why)

def digest(data):return sha256(data).hexdigest()
def encode(x):return (json.dumps(x,sort_keys=True,indent=2)+"\n").encode()

def run(payload,output):
    pins=json.loads((HERE/"FROZEN.json").read_bytes())
    for name,h in pins.items():need(digest((HERE/name).read_bytes())==h,name)
    reference=load("finite_event_reference",HERE/"direct.py")
    specialized=load("nested_level_calculation",payload)
    fixtures=json.loads((HERE/"fixtures.json").read_bytes())
    output.mkdir(mode=0o700,exist_ok=False)
    records={};rejections=[];local_example=None
    for c in fixtures["accepted"]:
        tag,order,rows=c["case"],c["coarse_to_fine"],c["rows"]
        got=specialized.products(rows,order)
        expected=reference.products(rows)
        need(set(got)==set(expected),tag+" keys")
        for key, stages in got.items():
            need(set(stages)=={"atom","cumulative"},"stage")
            for stage,v in stages.items():
                need(type(v) is list and len(v)==3 and all(type(x) is Fraction for x in v),"three exact components")
                need(v==expected[key][stage],tag+" "+key+" "+stage)
        active={"+".join(sorted(f"{1<<a:02x}" for a in order[j:])) for j in range(3)}
        structural=sum(got[k]["atom"][j]==1 for k in got if k not in active for j in range(3))
        need(structural==45 and all(min(got[k]["atom"])>=1 for k in got),"structural zeros and average sign")
        if tag.startswith("permutation-"):
            need(all(got[k]["atom"][2]>1 for k in active),"each level adds exact positive mutual information")
        if tag in ("target-independent","target-constant"):
            need(all(got[k]["atom"][2]==1 for k in got),"all average signed atoms zero")
        if tag=="permutation-012":
            # Actual local signed increment at the finest observed source value 0, target 0.
            fine=[x for x in rows if x[2]==0];middle=[x for x in rows if x[1]==0]
            def conditional(group):
                return Fraction(sum(x[4] for x in group if x[3]==0),sum(x[4] for x in group))
            ratio=conditional(fine)/conditional(middle)
            need(ratio<1 and got["04"]["atom"][2]>1,"negative local, positive average")
            local_example=str(ratio)
            wrong=reference.products(rows,uniform_weights=True)
            need(wrong!=got,"mutant weights all positive keys equally")
        records[tag]={k:{q:[str(x) for x in vals] for q,vals in stages.items()} for k,stages in got.items()}
    need(records["all-equal"]==records["all-equal-tied-order"],"equal partition permutation")
    for case in fixtures["refused"]:
        try:specialized.products(case["rows"],case["coarse_to_fine"])
        except ValueError as e:
            rejections.append([case["case"],str(e)])
        else:raise ValueError("bad input accepted "+case["case"])
    need(len(records)==13 and len(rejections)==8 and local_example,"registered cases")
    evidence=encode(records);(output/"all-products.json").write_bytes(evidence)
    outcome=dict(accepted=len(records),named_products=len(records)*108,structural_ones=len(records)*45,
                 explicit_refusals=rejections,uniform_key_mutation_detected=True,
                 negative_local_positive_average=local_example,products_sha256=digest(evidence),
                 frozen_sha256=digest((HERE/"FROZEN.json").read_bytes()),selected_source_sha256=digest(payload.read_bytes()))
    (output/"RESULT.json").write_bytes(encode(outcome));print(json.dumps(outcome,sort_keys=True))

if __name__=="__main__":run(*map(Path,sys.argv[1:]))
