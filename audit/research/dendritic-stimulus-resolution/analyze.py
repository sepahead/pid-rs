"""Analyze the published control response table with exact rational information products."""
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import combinations
import json
import sys

def read_matrix(data):
    matrix=[line.split() for line in data.decode("ascii").strip().splitlines()]
    if len(matrix)!=31 or any(len(row)!=21 for row in matrix):
        raise ValueError("expected 31 basal and 21 tuft settings")
    settings=[]
    for basal,row in enumerate(matrix):
        for tuft,field in enumerate(row):
            v=Fraction(field)
            if v.denominator!=1 or not 0<=v<=4:
                raise ValueError("expected an integer number of spikes from zero to four")
            category=0 if v==0 else 1 if v<=2 else 2
            settings.append((10*basal,10*tuft,category))
    return settings

def ordered_rules():
    def code(s): return sum(2**i for i in s)
    cols=tuple(range(3))
    groups=sorted((frozenset(g) for n in range(1,4) for g in combinations(cols,n)),key=code)
    rules=[fam for n in range(1,len(groups)+1) for fam in combinations(groups,n)
           if all(not(a<=b or b<=a) for a,b in combinations(fam,2))]
    labels=["+".join(f"{code(g):02x}" for g in fam) for fam in rules]
    below=[]
    for node in rules:
        below.append([i for i,other in enumerate(rules) if other!=node and
                      all(any(a<=b for a in other) for b in node)])
    return groups,rules,labels,below

def invert(values,below):
    result=[None]*len(values)
    for i in sorted(range(len(values)),key=lambda k:len(below[k])):
        part=values[i]
        for j in below[i]:
            part=part/result[j]
        result[i]=part
    return result

def features(b,a,width):
    return b//width,a//width,int(b>a)
def code(q): return [format(q.numerator,"x"),format(q.denominator,"x")]

def decompose(settings,width):
    groups,rules,labels,below=ordered_rules()
    data=Counter((features(b,a,width),y) for b,a,y in settings)
    source={g:Counter() for g in groups}
    with_target={g:Counter() for g in groups}
    target=Counter()
    def values_at(s,g):
        return tuple(s[i] for i in sorted(g))
    for (s,y),n in data.items():
        target[y]+=n
        for g in groups:
            v=values_at(s,g)
            source[g][v]+=n
            with_target[g][v,y]+=n
    events=[]
    for fam in rules:
        coefficients=Counter()
        for size in range(1,len(fam)+1):
            for branches in combinations(fam,size):
                coefficients[frozenset.union(*branches)] += (-1)**(size-1)
        events.append([(g,c) for g,c in coefficients.items() if c])
    products=[[Fraction(1) for _ in rules] for ch in range(3)]
    specific={y:{g:Fraction(1) for g in groups} for y in target}
    N=len(settings)
    for (s,y),weight in data.items():
        projection={g:values_at(s,g) for g in groups}
        terms=[[],[],[]]
        for coeff in events:
            n_event=sum(c*source[g][projection[g]] for g,c in coeff)
            n_joint=sum(c*with_target[g][projection[g],y] for g,c in coeff)
            info=Fraction(N,n_event)
            mis=Fraction(target[y],n_joint)
            for channel,val in zip(terms,(info,mis,info/mis)):
                channel.append(val)
        for channel,values in enumerate(terms):
            for i,v in enumerate(invert(values,below)):
                products[channel][i]*=v**weight
        for g in groups:
            v=projection[g]
            specific[y][g]*=Fraction(N*with_target[g][v,y],target[y]*source[g][v])**weight
    minima=[]
    for fam in rules:
        term=Fraction(1)
        for y in target:
            term*=min(specific[y][g] for g in fam)
        minima.append(term)
    return {"keys":labels, "informative":[code(q) for q in products[0]],
            "misinformative":[code(q) for q in products[1]],"signed":[code(q) for q in products[2]],
            "imin":[code(q) for q in invert(minima,below)]}

def decisions(settings,width):
    whole=defaultdict(Counter)
    excluded={"basal":defaultdict(Counter),"tuft":defaultdict(Counter)}
    for b,a,y in settings:
        feat=features(b,a,width)
        for key in (feat[:2],feat):
            whole[key][y]+=1
            excluded["basal"][b,key][y]+=1
            excluded["tuft"][a,key][y]+=1
    strata=[]
    for pair in sorted(k for k in whole if len(k)==2):
        count=sum(whole[pair].values())
        score=max(whole[pair].values())
        full=sum(max(hist.values()) for k,hist in whole.items() if len(k)==3 and k[:2]==pair)
        strata.append([*pair,count,score,full])
    predictions={}
    for axis in ("basal","tuft"):
        rows=[]
        for b,a,y in settings:
            feat=features(b,a,width)
            record=[b,a,y]
            for key in (feat[:2],feat):
                left=excluded[axis][b if axis=="basal" else a,key]
                counts=[whole[key][j]-left[j] for j in range(3)]
                label=counts.index(max(counts))
                record.extend([label,counts[y]+1,sum(counts)+3])
            rows.append(record)
        predictions[axis]=rows
    return {"groups":strata,"withheld":predictions}

settings=read_matrix(sys.stdin.buffer.read())
result={}
for width in (10,50,100):
    fields=decompose(settings,width)
    fields.update(decisions(settings,width))
    result[str(width)]=fields
print(json.dumps(result,separators=(",",":")))
