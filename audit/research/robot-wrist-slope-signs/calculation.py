"""Exact categorical shared exclusions and Shannon coordinates from finite source counts."""
from fractions import Fraction
from collections import Counter
from functools import cache
import re


def need(ok, message):
    if not ok:
        raise ValueError(message)


@cache
def factors(value):
    need(type(value) is int and value > 0, "factor of nonpositive count")
    power = Counter()
    divisor = 2
    while divisor * divisor <= value:
        while value % divisor == 0:
            power[divisor] += 1
            value //= divisor
        divisor += 1
    if value != 1:
        power[value] += 1
    return power


def add_factors(target, value, multiplicity):
    for p, e in factors(value).items():
        target[p] += multiplicity * e


def combine(*parts):
    result = Counter()
    for vector, factor in parts:
        for p, e in vector.items():
            result[p] += factor * e
    return result


def read_events(raw, labels, expected):
    events = []
    current = None
    readings = []
    for record in raw.decode("ascii").splitlines():
        record = record.strip()
        if not record:
            continue
        if record in labels:
            need(current is None, "new class within episode")
            current = labels.index(record)
            continue
        need(current is not None, "invalid or unknown class")
        tokens = record.split()
        need(len(tokens) == 6 and all(re.fullmatch(r"[+-]?[0-9]+", token) for token in tokens),
             "expected six integer readings")
        readings.append((int(tokens[2]), int(tokens[5])))
        if len(readings) == 15:
            signs = []
            for col in (0, 1):
                slope = sum((i - 7) * reading[col] for i, reading in enumerate(readings))
                signs.append((slope > 0) - (slope < 0))
            events.append((*signs, current))
            current, readings = None, []
    need(current is None and len(events) == expected and expected > 0, "task episode extent")
    return events


def calculate(raw, spec):
    labels, n = spec["labels"], spec["n"]
    events = read_events(raw, labels, n)
    return from_counts(Counter(events),spec)


def from_counts(counts,spec):
    labels,n=spec["labels"],spec["n"]
    need(n>0 and n==sum(counts.values()) and all(type(v) is int and v>0 for v in counts.values()),"positive integer occupied counts")
    need(all(f in (-1,0,1) and q in (-1,0,1) and type(y) is int and 0<=y<len(labels) for f,q,y in counts),"full cell alphabet")
    force, torque, target = Counter(), Counter(), Counter()
    fq, fy, qy = Counter(), Counter(), Counter()
    for (f, q, y), many in counts.items():
        force[f] += many
        torque[q] += many
        target[y] += many
        fq[f, q] += many
        fy[f, y] += many
        qy[q, y] += many
    base = {name:Counter() for name in ("target_entropy","h_y_given_f","h_y_given_q","h_y_given_fq",
            "mi_f","mi_q","mi_joint","cmi_q_given_f","cmi_f_given_q","redundant")}
    for (f, q, y), many in counts.items():
        src_union = force[f] + torque[q] - fq[f,q]
        class_union = fy[f,y] + qy[q,y] - many
        expressions = {
            "target_entropy": ((n,), (target[y],)),
            "h_y_given_f": ((force[f],), (fy[f,y],)),
            "h_y_given_q": ((torque[q],), (qy[q,y],)),
            "h_y_given_fq": ((fq[f,q],), (many,)),
            "mi_f": ((n, fy[f,y]), (force[f],target[y])),
            "mi_q": ((n, qy[q,y]), (torque[q],target[y])),
            "mi_joint": ((n, many), (fq[f,q],target[y])),
            "cmi_q_given_f": ((force[f],many), (fq[f,q],fy[f,y])),
            "cmi_f_given_q": ((torque[q],many), (fq[f,q],qy[q,y])),
            "redundant": ((n,class_union), (target[y],src_union)),
        }
        for name,(top,bottom) in expressions.items():
            for value in top:
                add_factors(base[name],value,many)
            for value in bottom:
                add_factors(base[name],value,-many)
    red = base["redundant"]
    base["unique_f"] = combine((base["mi_f"],1),(red,-1))
    base["unique_q"] = combine((base["mi_q"],1),(red,-1))
    base["synergy"] = combine((base["mi_joint"],1),(base["mi_f"],-1),(base["mi_q"],-1),(red,1))
    for mi,conditional in (("mi_f","h_y_given_f"),("mi_q","h_y_given_q"),("mi_joint","h_y_given_fq")):
        need(base["target_entropy"] == combine((base[mi],1),(base[conditional],1)), "entropy chain")
    for gain,unique,mag in (("cmi_q_given_f","unique_q","mi_f"),("cmi_f_given_q","unique_f","mi_q")):
        need(base[gain] == combine((base[unique],1),(base["synergy"],1)) and
             base["mi_joint"] == combine((base[gain],1),(base[mag],1)), "signed PID and Shannon chains")
    need(base["mi_joint"] == combine((red,1),(base["unique_f"],1),(base["unique_q"],1),(base["synergy"],1)),
         "four-atom reconstruction")
    packed = {name:[[p,e] for p,e in sorted(vec.items()) if e] for name,vec in base.items()}
    levels = (-1,0,1)
    classes = range(len(labels))
    correct = [max(target.values()),
               sum(max(fy[f,y] for y in classes) for f in levels),
               sum(max(qy[q,y] for y in classes) for q in levels),
               sum(max(counts[f,q,y] for y in classes) for f in levels for q in levels)]
    return {"id":spec["id"], "counts":[counts[f,q,y] for f in levels for q in levels for y in classes],
            "log_products":packed, "correct":correct}



def fractional(vector):
    top=bottom=1
    for p,e in vector:
        if e>0:top*=p**e
        else:bottom*=p**(-e)
    return Fraction(top,bottom)
def coarse_log(x):
    z=(x-1)/(x+1)
    need(0<=z<=Fraction(1,3),"log range reduction")
    z2=z*z;power=z;total=Fraction()
    for i in range(32):
        total+=2*power/(2*i+1)
        power*=z2
    return total, total+2*power/(65*(1-z2))
def floor(x): return x.numerator//x.denominator
def ceil(x): return -floor(-x)
@cache
def log_units(p):
    shift=p.bit_length()-1
    lo,hi=coarse_log(Fraction(p,1<<shift));lo2,hi2=coarse_log(Fraction(2))
    return floor(10**18*(lo+shift*lo2)),ceil(10**18*(hi+shift*hi2))
def summary(task, k):
    n=sum(task["counts"])
    values={}
    for name,vector in task["log_products"].items():
        lo=hi=0
        for p,e in vector:
            l,h=log_units(p)
            lo+=min(e*l,e*h);hi+=max(e*l,e*h)
        r=fractional(vector)
        values[name]={"sign":(r>1)-(r<1),"lower_nanonats":floor(Fraction(lo,n*10**9)),
                      "upper_nanonats":ceil(Fraction(hi,n*10**9))}
    cells=task["counts"]
    grouped=[cells[i:i+k] for i in range(0,9*k,k)]
    class_counts=[sum(g[y] for g in grouped) for y in range(k)]
    fsums=[[sum(grouped[f*3+q][y] for q in range(3)) for y in range(k)] for f in range(3)]
    qsums=[[sum(grouped[f*3+q][y] for f in range(3)) for y in range(k)] for q in range(3)]
    def ties(groups):
        return sum(max(row)>0 and row.count(max(row))>1 for row in groups)
    return {"id":task["id"], "n":n,"classes":class_counts,"occupied_triples":sum(x>0 for x in cells),
            "pair_counts":[sum(row) for row in grouped],"zero_force":sum(fsums[1]),"zero_torque":sum(qsums[1]),
            "tied_occupied_predictions":[ties(g) for g in ([class_counts],fsums,qsums,grouped)],
            "modal_correct":task["correct"], "nanonat_intervals":values}
