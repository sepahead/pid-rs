"""Exposed all-law finite checks of a separately derived coupling bound."""

from collections import Counter
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('bound_adapter',ROOT/'adapter_v3.py')
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
C=A.C


def terms(record):
    return C.factors((Fraction(a,b),e) for a,b,e in record['factors'])


def enclosure_json(pair):return [str(x) for x in pair]


def leq(left,right,n):
    x,y=C.interval(left,n),C.interval(right,n)
    if x[1]<=y[0]:return 'outward separated'
    ratio=C.exact_product(C.combine([(right,1),(left,-1)]))
    C.require(ratio>=1,'finite log inequality counterexample')
    return 'exact product equality' if ratio==1 else 'exact product order'


def main():
    C.require(len(sys.argv)==2,'expected new output directory')
    frozen=json.loads((ROOT/'POST_BOUND_INPUTS.json').read_bytes())
    for item in frozen['inputs']:
        C.require(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],'analysis input drift')
    # The published campaign index pins every law file by size and SHA-256.
    output=Path(sys.argv[1]);output.mkdir(exist_ok=False)
    source=ROOT.parent/'evidence'/'campaign';index=json.loads((source/'REPORT.json').read_bytes())
    result=[]
    for recording in index['recordings']:
        heads=tuple(tuple(t) for t in recording['metadata']['heads'])
        for pointer in recording['laws']:
            raw=(source/pointer['path']).read_bytes()
            C.require(len(raw)==pointer['bytes'] and hashlib.sha256(raw).hexdigest()==pointer['sha256'],'law identity')
            law=json.loads(raw);n=law['rows']
            counts={tuple(row[:4]):row[4] for row in law['counts']}
            C.require(len(counts)==len(law['counts']) and sum(counts.values())==n,'count transport')
            def mapped(s):return s if s[1:] in heads else (s[0],*heads[0])
            coupled=[(z[:3],mapped(z[:3]),z[3],c) for z,c in sorted(counts.items())]
            cost={};direction={}
            for mask in range(1,8):
                columns=[i for i in range(3) if mask&(1<<i)]
                joint=Counter();old=Counter();new=Counter()
                for s,u,_,weight in coupled:
                    a=tuple(s[i] for i in columns);b=tuple(u[i] for i in columns)
                    joint[a,b]+=weight;old[a]+=weight;new[b]+=weight
                forward=C.factors((Fraction(old[a],weight),weight) for (a,b),weight in joint.items())
                reverse=C.factors((Fraction(new[b],weight),weight) for (a,b),weight in joint.items())
                vi=C.combine([(forward,1),(reverse,1)])
                C.require(C.exact_product(forward)>=1 and C.exact_product(reverse)>=1,'conditional entropy sign')
                cost[mask]=vi;direction[mask]=(forward,reverse)
            node_checks=[]
            original={(tuple(x['branches']),x['component']):x for x in law['coordinates'] if x['stage']=='cumulative'}
            for node in C.carrier()[0]:
                plus=[];minus=[]
                for s,u,t,weight in coupled:
                    matches=[]
                    for v,w,target,count in coupled:
                        hit=any(all(s[i]==v[i] and u[i]==w[i] for i in range(3) if branch&(1<<i)) for branch in node)
                        if hit:
                            C.require(C.matches(s,v,node) and C.matches(u,w,node),'refinement nesting')
                            matches.append((target,count))
                    total=sum(c for _,c in matches);restricted=sum(c for target,c in matches if target==t)
                    target_total=sum(c for _,_,target,c in coupled if target==t)
                    C.require(0<restricted<=total<=n and restricted<=target_total,'paired anchor/count range')
                    plus.append((Fraction(n,total),weight));minus.append((Fraction(target_total,restricted),weight))
                join={'plus':C.factors(plus),'minus':C.factors(minus)}
                checks=[]
                for version,di in (('before',0),('after',1)):
                    budget=C.combine([(direction[branch][di],1) for branch in node])
                    for component in ('plus','minus'):
                        increment=C.combine([(join[component],1),(terms(original[node,component][version]),-1)])
                        C.require(C.exact_product(increment)>=1,'negative refinement increment')
                        checks.append(leq(increment,budget,n))
                delta=C.combine([(terms(original[node,'net']['before']),1),(terms(original[node,'net']['after']),-1)])
                sign=C.exact_product(delta)
                absolute=C.combine([(delta,1 if sign>=1 else -1)])
                budget=C.combine([(cost[branch],1) for branch in node])
                checks.append(leq(absolute,budget,n))
                node_checks.append({'branches':list(node),'joined_informative':C.record(join['plus'],n),
                                    'joined_misinformative':C.record(join['minus'],n),'five_bounds':checks})
            upper=[Fraction(0),Fraction(0)];coordinate_upper=[Fraction(0),Fraction(0)]
            for mask,f in cost.items():
                pair=C.interval(f,n);weight=1 if mask==7 else 22
                for i in (0,1):
                    upper[i]+=weight*pair[i]
                    if mask in (1,2,4):coordinate_upper[i]+=67*pair[i]
            d=tuple(Fraction(x) for x in law['allocation_interval'])
            C.require(d[1]<=upper[0],'full allocation/upper enclosure separation')
            C.require(upper[1]-upper[0]<=Fraction(1,10**12),'upper width')
            result.append({'recording':recording['metadata']['recording'],'law':law['law'],'rows':n,
                           'coalition_vi':{str(mask):C.record(f,n) for mask,f in cost.items()},
                           'upper_interval':enclosure_json(upper),'upper_display_nats':float(sum(upper)/2),
                           'coordinate_upper_interval':enclosure_json(coordinate_upper),
                           'coordinate_upper_display_nats':float(sum(coordinate_upper)/2),
                           'lower_mi_cut':law['mi_cut_lower_nats'],'actual_allocation_interval':law['allocation_interval'],
                           'actual_allocation_display_nats':law['allocation_display_nats'],
                           'old_tv_upper_interval':law['continuity_upper_interval'],'node_checks':node_checks})
    C.require(len(result)==30,'all-law analysis roster')
    for item in frozen['inputs']:
        C.require(hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],'analysis input drift after')
    raw=(json.dumps({'status':'PASS','scope':'post-study exact empirical-law checks; not universal proof or population calibration',
                     'laws':result},sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
    C.require(len(raw)<2*1024**2,'post-analysis output cap')
    with (output/'REPORT.json').open('xb') as handle:handle.write(raw)
    print(json.dumps({'status':'PASS','laws':30,'node_bound_checks':30*18*5,'report_bytes':len(raw),
                      'sha256':hashlib.sha256(raw).hexdigest()}))


if __name__=='__main__':main()
