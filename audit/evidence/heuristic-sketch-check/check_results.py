"""Check a complete original-stream recording against exact integer distances and harmonic sums."""
from __future__ import annotations
from fractions import Fraction
from decimal import Decimal, localcontext
from pathlib import Path
import argparse
import hashlib
import json
import math
import struct

GAMMA = Decimal("0.57721566490153286060651209008240243104215933593992")
TOLERANCE = Decimal("1e-12")
MASK = (1 << 64) - 1

def require(condition, message):
    if not condition:
        raise ValueError(message)

def from_word(word):
    require(len(word) == 16 and set(word) <= set("0123456789abcdef"), "bad binary64 word")
    value = struct.unpack(">d", bytes.fromhex(word))[0]
    require(math.isfinite(value), "nonfinite binary64 value")
    return value

def h(count):
    return sum((Fraction(1, d) for d in range(1, count + 1)), Fraction())

def rational_text(value):
    return f"{value.numerator}/{value.denominator}"

def decimal_mean(q):
    with localcontext() as ctx:
        ctx.prec = 55
        return Decimal(q.numerator) / Decimal(q.denominator) - 2 * GAMMA

def grid(n, wide):
    # Scale all source and target coordinates by the same 4 n².
    den = 4 * n * n
    t = [i * den + i * i for i in range(n)]
    p = [(3 * i + 1) % n for i in range(n)]
    x = [n*i for i in range(n)]
    y = [4*n*t[j] if wide else n*j for j in p]
    return x, y, t

def uniform(seed, n):
    pts = []
    for _ in range(n):
        seed = (seed + 0x9e3779b97f4a7c15) & MASK
        z = seed
        z = ((z ^ (z >> 30)) * 0xbf58476d1ce4e5b9) & MASK
        z = ((z ^ (z >> 27)) * 0x94d049bb133111eb) & MASK
        pts.append((z ^ (z >> 31)) >> 12)
    return pts

def explicit_counts(x,y,t,k):
    counts=[]
    for i, q in enumerate(t):
        other = [j for j in range(len(t)) if i != j]
        dt = [abs(t[j]-q) for j in other]
        radii = []
        for source in (x,y):
            distances = sorted(max(d, abs(source[j]-source[i])) for j,d in zip(other,dt))
            r = distances[k-1]
            require(r>0 and distances.count(r)==1, "ambiguous reference shell")
            radii.append(r)
        a,b,s = (sum(d<r for d in dt) for r in (*radii, min(radii)))
        require(k-1 <= min(a,b) <= max(a,b) < len(t) and s==min(a,b), "joint inclusion")
        counts.append((a,b))
    return counts

def check_score(x,y,t,k,word,endpoint=None):
    counts = explicit_counts(x,y,t,k)
    n=len(t)
    if endpoint:
        require(all(c==endpoint for c in counts), "endpoint counts")
    rational = h(k-1)+h(n-1) - sum((abs(h(a)-h(b)) for a,b in counts), Fraction()) / (2*n)
    lo=(3*h(k-1)+h(n-1))/2
    hi=h(k-1)+h(n-1)
    require(lo<=rational<=hi, "harmonic bound")
    expected = decimal_mean(rational)
    actual=from_word(word)
    error = abs(Decimal.from_float(actual)-expected)
    require(error<=TOLERANCE, f"binary64 discrepancy {n=} {k=} {error=}")
    return {"n":n,"k":k,"actual_bits":word,"score":actual,"exact_addend_above_minus_twice_gamma":rational_text(rational),"absolute_error":str(error),"target_counts":counts}

def check(data):
    stream=iter(data.splitlines())
    def take(prefix):
        row=next(stream,"").split("\t")
        require(row[:len(prefix)]==prefix,"wrong row identity: "+repr(prefix))
        return row[len(prefix):]
    result={"endpoints":[],"stream_prefixes":[],"configured_raw_pid2":[],"refusals":[]}
    for n in (4,8,16,32):
        for k in (1,2,n-1):
            for wide in (False,True):
                x,y,t=grid(n,wide)
                for swap in (False,True):
                    (word,) = take(["endpoint",str(n),str(k),str(wide).lower(),str(swap).lower()])
                    c=(k-1,n-1 if wide else k-1)
                    r=check_score(y if swap else x,x if swap else y,t,k,word,c[::-1] if swap else c)
                    r.update(wide=wide,swapped=swap)
                    result["endpoints"].append(r)
    for n in (8,32,128,256):
        inputs=[uniform(seed,n) for seed in (104729,1299709,15485863)]
        word, m1, m2, m12, rawword=take(["sample",str(n)])
        require(rawword==word,"raw PID2 estimate input")
        r=check_score(*inputs,3,word)
        result["stream_prefixes"].append(r)
        status,*fields=take(["pid2",str(n)])
        original={"n":n,"status":status,"mi_bits":[m1,m2,m12],"observed":fields}
        if status=="accepted":
            red,u1,u2,s=map(from_word,fields)
            a,b,c=map(from_word,(m1,m2,m12))
            require(fields[0]==word and u1==a-red and u2==b-red,"raw unique atoms")
            synergy=Fraction(c)-Fraction(a)-Fraction(b)+Fraction(red)
            require(s==float(synergy),"raw represented synergy")
        else:
            require(status=="refused" and fields==["Pid2Result::from_estimate reconstructed coordinates exceed compatibility guard"],"raw reconstruction guard")
        ctxt,message=take(["report",str(n)])
        require(ctxt=="pid2_isx_report" and "complete PID2 reports require the cited IsxMethod::EhrlichKsg" in message,"full report guard")
        result["configured_raw_pid2"].append(original)
    for name,code in [("rank_zero","InvalidK"),("rank_n","InvalidK"),("unspecified","SupportContractRequired"),("epsilon","InvalidConfig"),("dimension","SourceDimensionMismatch"),("target_duplicate","ObservedContinuousSampleIncompatibility"),("ambiguous","AmbiguousKthNeighborShell")]:
        (observed,)=take(["refusal",name])
        require(observed.startswith(code+" {"),"wrong refusal class "+name)
        result["refusals"].append({"control":name,"actual":observed})
    (tword,)=take(["target2"])
    require(tword==next(s["actual_bits"] for s in result["endpoints"] if s["n"]==4 and s["k"]==2 and not s["swapped"] and not s["wide"]),"two-component target")
    require(next(stream,None) is None,"unregistered trailing row")
    result["target_dimension_two_word"]=tword
    return result

def mutations(data):
    lines=data.splitlines()
    idx=next(i for i,l in enumerate(lines) if l.startswith("endpoint\t8\t2\ttrue\tfalse\t"))
    q=h(1)+h(7)
    d=h(7)-h(1)
    cases=[("signed count correction reversed", q+d/2),("halving omitted",q-d),("strict rank replaced by k",q-(h(7)-h(2))/2)]
    for name, real in cases:
        a=lines[:]
        a[idx]=a[idx][:a[idx].rfind("\t")+1]+struct.pack(">d",float(decimal_mean(real))).hex()
        yield name, "\n".join(a)
    yield "one of 48 endpoints missing", "\n".join(lines[:idx]+lines[idx+1:])
    fields=lines[idx].split("\t")
    for name,last in [("nonfinite scalar","7ff8000000000001"),("refusal in place of scalar","SupportContractRequired")]:
        a=lines[:];a[idx]="\t".join(fields[:-1]+[last])
        yield name,"\n".join(a)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("native_stdout",type=Path)
    args=p.parse_args()
    data=args.native_stdout.read_bytes()
    text=data.decode("ascii")
    record=check(text); negative=[]
    for label, changed in mutations(text):
        try: check(changed)
        except ValueError as ex: negative.append({"control":label,"refusal":str(ex)})
        else: raise RuntimeError("altered result passed: "+label)
    record["active_mutations"]=negative
    record["native_stdout_sha256"]=hashlib.sha256(data).hexdigest()
    record["units"]="nats, absolute tolerance 1e-12 for the four designed sizes and four pseudorandom prefixes"
    print(json.dumps(record,indent=2,sort_keys=True,allow_nan=False))
if __name__=="__main__":
    main()
