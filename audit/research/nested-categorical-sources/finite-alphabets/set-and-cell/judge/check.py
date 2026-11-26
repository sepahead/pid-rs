"""Compare a cell-count construction with the earlier event-union implementation."""
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
here=Path(__file__).resolve().parent
def need(ok,why):
    if not ok:raise ValueError(why)
def mod(name,path):
    obj=importlib.util.spec_from_file_location(name,path)
    data=importlib.util.module_from_spec(obj)
    obj.loader.exec_module(data)
    return data
def main():
    packet=json.loads((here/"BOUND.json").read_bytes())
    for name,value in packet.items():
        need(sha256((here/name).read_bytes()).hexdigest()==value,name)
    submitted=Path(sys.argv[1]).resolve(strict=True)
    dest=Path(sys.argv[2]);dest.mkdir(exist_ok=False)
    base=mod("earlier_partition_reference",here/"previous_partitions.py")
    proposal=mod("submitted_cell_result",submitted)
    all_rows=[]
    for n,bell in enumerate((1,2,5,15,52,203,877),1):
        keys=base.partitions(n)
        need(len(keys)==len(set(keys))==bell,n)
        fine=[s for s in keys if max(s)<=1]
        need(len(fine)==2**(n-1),"fine pool")
        groups={k:base.blocks(k) for k in keys}
        bins={}
        for k in (1,2):
            bins[k]={"pairs":0,"maps":0,"violations":0,"attaining_binary":0,"attaining_one":0,"minimum":None}
        for fine_word in fine:
            k=max(fine_word)+1
            state=bins[k]
            for coarse_word in keys:
                state["pairs"]+=1
                factor=base.imbalance_product(groups[coarse_word],groups[fine_word])
                predicted=proposal.from_cells(coarse_word,fine_word)
                need(type(predicted) is Fraction and predicted==factor,("independent direct product",n,coarse_word,fine_word,predicted,factor))
                is_map=base.relation(coarse_word,fine_word)
                need((factor==1)==is_map,"zero vs nesting")
                if is_map:
                    state["maps"]+=1
                    continue
                state["violations"]+=1
                binary=Fraction(2*n,n-1)
                one=Fraction(n**n,(n-1)**(n-1))
                sizes=sorted(coarse_word.count(x) for x in set(coarse_word))
                fs=set(groups[fine_word])
                cs=set(groups[coarse_word])
                shared=[f for f in fs if sum(not f.isdisjoint(c) for c in cs)>1]
                shape=(sizes==[1,n-1] and len(shared)==1 and len(shared[0])==2)
                need(factor>=binary and (factor==binary)==shape,("two available",n,coarse_word,fine_word))
                if k==1:
                    need(factor>=one and (factor==one)==(sizes==[1,n-1]),("one occupied",n))
                    state["attaining_one"]+=int(factor==one)
                state["attaining_binary"]+=int(factor==binary)
                state["minimum"]=factor if state["minimum"] is None else min(state["minimum"],factor)
        for k in (1,2):
            b=bins[k];need(b["maps"]+b["violations"]==b["pairs"],"pool accounting")
            need((b["violations"]>0)==(n>=2 if k==1 else n>=3),"feasible stratum")
            if b["violations"]:
                target=Fraction(n**n,(n-1)**(n-1)) if k==1 else Fraction(2*n,n-1)
                need(b["minimum"]==target,"unattained minimum")
                b["minimum"]=str(b["minimum"])
        all_rows.append(dict(n=n,coarse=bell,rows=bins))
    real=[]
    for n in (4,8,16,32,64):
        m=n//2
        c=(0,)*m+(1,)*m
        fine=(0,)*(m-1)+(1,0)+(1,)*(m-1)
        measured=base.imbalance_product(base.blocks(c),base.blocks(fine))
        expected=Fraction(m+1,m)**(n-2)*Fraction(2*m-1,m)**2
        need(measured==expected==proposal.from_cells(c,fine),"balanced near-map")
        real.append([n,str(expected)])
    c=(0,0,1,1);fine=(0,1,0,2)
    nonbinary=base.imbalance_product(base.blocks(c),base.blocks(fine))
    need(nonbinary==Fraction(9,4)<Fraction(8,3),"removed support premise")
    result=dict(rows=all_rows,total=sum(row["rows"][k]["pairs"] for row in all_rows for k in (1,2)),balanced_binary_real_weight_fixtures=real,three_fine_categories_four_rows=str(nonbinary))
    (dest/"RESULT.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["total"],"ordered partition pairs")
if __name__=="__main__":main()
