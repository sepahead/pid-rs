"""Score an isolated structured prediction using the unchanged public general oracle."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import argparse,json,runpy,subprocess,sys
def require(x,why):
    if not x:raise ValueError(why)
def digest(b):return sha256(b).hexdigest()
def same(got,want):
    require(type(got) is type(want),'type')
    if type(got) is dict:
        require(set(got)==set(want),'keys')
        for k in want:same(got[k],want[k])
    elif type(got) is list:
        require(len(got)==len(want),'length')
        for a,b in zip(got,want):same(a,b)
    else:require(got==want,'value')
def local_count(ar,table):
    """Invert all 18 local net event ratios from primary events, without a chain."""
    nodes,_,mu=ar['lattice']();total=sum(c for _,c in table);neg=0
    for anchor,_ in table:
        target=sum(c for key,c in table if key[3]==anchor[3])
        values=[]
        for masks in nodes:
            event=[(key,c) for key,c in table if any(all(key[i]==anchor[i] for i in range(3) if mask & (1<<i)) for mask in masks)]
            mass=sum(c for _,c in event);joint=sum(c for key,c in event if key[3]==anchor[3])
            values.append(Fraction(joint*total,mass*target))
        for row in mu:
            result=Fraction(1)
            for number,power in zip(values,row):
                if power:result *= number**power
            neg+=result<1
    return neg
def main():
    p=argparse.ArgumentParser();p.add_argument('candidate',type=Path);p.add_argument('oracle',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    root=Path(__file__).resolve().parents[1]
    raw=(root/'inputs/panel.json').read_bytes()
    require(digest(raw)=='3025ed53cc564879beeb796a63dc6747add3994790e252737077657be93719bb','panel identity')
    require(digest(a.oracle.read_bytes())=='b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2','reference source')
    ar=runpy.run_path(str(a.oracle));panel=json.loads(raw)
    payload=json.dumps([case['rows'] for case in panel],separators=(',',':')).encode()
    command=[sys.executable]+(['-O'] if sys.flags.optimize else [])+['-I','-S','-B',str(a.candidate.resolve())]
    run=subprocess.run(command,input=payload,capture_output=True,timeout=30)
    a.output.mkdir(exist_ok=False)
    (a.output/'candidate.stdout').write_bytes(run.stdout);(a.output/'candidate.stderr').write_bytes(run.stderr)
    require(run.returncode==0 and not run.stderr,'candidate process')
    outputs=json.loads(run.stdout)
    require(type(outputs) is list and len(outputs)==len(panel),'item roster')
    expected=[];count=Counter();per=[]
    for case,computed in zip(panel,outputs):
        if case['nested'] is None:
            try:ar['typed_rows'](case['rows'])
            except ar['ArithmeticReject']:pass
            else:raise ValueError('malformed not rejected by general oracle')
            want={'error':'invalid rows'};count['invalid']+=1
        elif not case['nested']:
            ar['typed_rows'](case['rows']);want={'error':'not nested'};count['crossed']+=1
        else:
            table,total,length=ar['typed_rows'](case['rows'])
            plans=list(ar['projections'](ar['base_plans'](table,total)));ar['preflight'](plans)
            records={}
            for (scope,comp,key,_),plan in plans:
                value=ar['exact_product'](plan);records['/'.join((scope,comp,key))]=[value.numerator,value.denominator]
                count['fraction comparisons']+=1
                if scope=='atom' and comp=='net':count['mean net atom relation '+str((value>1)-(value<1))]+=1
            require(len(records)==108,'original roster');n=local_count(ar,table)
            want=dict(records=records,local_negative=n);count['local negative entries']+=n;count['accepted']+=1
            per.append([case['name'],n])
        same(computed,want);expected.append(want)
    require(count['accepted']==49 and count['invalid']==5 and count['crossed']==6,'panel classes')
    require(count['local negative entries']>0 and count['mean net atom relation -1']==0 and count['mean net atom relation 1']>0,'nonvacuous signs')
    controls=[]
    for choice in ('missing-key','wrong-product','swapped-key','boolean-numerator','crossed-accept'):
        item=deepcopy(expected[0] if choice!='crossed-accept' else expected[48]);want=deepcopy(item)
        if choice=='crossed-accept':item={'records':{}}
        else:
            records=item['records'];keys=list(records)
            if choice=='missing-key':del records[keys[0]]
            if choice=='wrong-product':records[keys[0]][0]+=1
            if choice=='boolean-numerator':records[keys[0]][0]=bool(records[keys[0]][0])
            if choice=='swapped-key':
                right=next(k for k in keys[1:] if records[k]!=records[keys[0]])
                records[keys[0]],records[right]=records[right],records[keys[0]]
        try:same(item,want)
        except ValueError as e:controls.append([choice,str(e)])
        else:raise ValueError('failed mutation '+choice)
    summary={'checks':dict(sorted(count.items())),'controls':controls,'input':digest(raw),'output':digest(run.stdout),'local_negative_counts':per}
    (a.output/'result.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'checks':summary['checks'],'controls':controls,'output':summary['output']},sort_keys=True))
if __name__=='__main__':main()
