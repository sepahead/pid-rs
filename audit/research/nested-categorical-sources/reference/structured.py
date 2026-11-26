"""Exact products for a small, typed three-source count table with nested partitions."""
from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations
import json
import re
import sys

ALPHABET = re.compile(r"[A-Za-z0-9._:-]{1,128}")
DECIMAL = re.compile(r"[1-9][0-9]{0,2}")
COMPONENTS = ("informative", "misinformative", "net")

def parse(raw):
    if type(raw) is not list or not 1 <= len(raw) <= 64:
        raise ValueError("invalid rows")
    table = []
    for record in raw:
        if type(record) is not dict or set(record) != {"count","source_states","target_state"}:
            raise ValueError("invalid rows")
        source = record["source_states"]
        count = record["count"]
        if type(source) is not list or len(source) != 3 or type(count) is not str or not DECIMAL.fullmatch(count):
            raise ValueError("invalid rows")
        n = int(count)
        if n > 16:
            raise ValueError("invalid rows")
        fields = (*source, record["target_state"])
        for state in fields:
            if type(state) is not list or not 1 <= len(state) <= 64 or any(type(w) is not str or not ALPHABET.fullmatch(w) for w in state):
                raise ValueError("invalid rows")
        key = tuple(tuple(state) for state in fields)
        if table and table[-1][0] >= key:
            raise ValueError("invalid rows")
        table.append((key,n))
    return table

def function_of(table, coarse, fine):
    mapping = {}
    for key,_ in table:
        fine_state = key[fine]
        if fine_state in mapping and mapping[fine_state] != key[coarse]:
            return False
        mapping[fine_state] = key[coarse]
    return True

def antichains():
    masks = range(1,8)
    for length in range(1,4):
        for family in combinations(masks,length):
            if all((a & b) not in (a,b) for a,b in combinations(family,2)):
                yield family

def ratio_record(value):
    return [value.numerator,value.denominator]

def calculate(raw):
    table = parse(raw)
    order = next((o for o in permutations(range(3))
                  if function_of(table,o[0],o[1]) and function_of(table,o[1],o[2])),None)
    if order is None:
        raise ValueError("not nested")
    total = sum(weight for _,weight in table)
    target = Counter()
    counts = [Counter() for _ in order]
    joints = [Counter() for _ in order]
    for key,weight in table:
        target[key[3]] += weight
        for position,source in enumerate(order):
            counts[position][key[source]] += weight
            joints[position][key[source],key[3]] += weight
    cumulative = [[Fraction(1) for _ in COMPONENTS] for _ in range(4)]
    local_negative = 0
    for key,weight in table:
        prior = Fraction(1)
        for j,source in enumerate(order,1):
            source_mass = counts[j-1][key[source]]
            joint_mass = joints[j-1][key[source],key[3]]
            informative = Fraction(total,source_mass)
            misinformative = Fraction(target[key[3]],joint_mass)
            net = informative/misinformative
            local_negative += net < prior
            prior = net
            for comp,value in enumerate((informative,misinformative,net)):
                cumulative[j][comp] *= value**weight
    positions = {source:j for j,source in enumerate(order,1)}
    levels = {tuple(sorted(1 << source for source in order[j:])):j+1 for j in range(3)}
    records = {}
    for family in antichains():
        node = "+".join(f"{mask:02x}" for mask in family)
        level = min(max(positions[i] for i in range(3) if mask & (1<<i)) for mask in family)
        for comp,name in enumerate(COMPONENTS):
            records[f"cumulative/{name}/{node}"] = ratio_record(cumulative[level][comp])
            affected = levels.get(family)
            atom = (cumulative[affected][comp] / cumulative[affected-1][comp]) if affected else Fraction(1)
            records[f"atom/{name}/{node}"] = ratio_record(atom)
    return {"records":records,"local_negative":local_negative}

def main():
    out=[]
    for table in json.load(sys.stdin):
        try:result=calculate(table)
        except ValueError as error:result={"error":str(error)}
        out.append(result)
    print(json.dumps(out,sort_keys=True,separators=(",",":")))

if __name__ == "__main__":
    main()
