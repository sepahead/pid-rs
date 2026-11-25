"""Replay the two exact sign calculations and reject changes to either recorded certificate."""
import argparse
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

HERE=Path(__file__).resolve().parent
PINS={
    "bernstein-result.json": "cb75d88579871a0da4ddc39d1c526342b24aeb8b48dcf609d2e8bb545348b628",
    "bernstein.py": "2e26e129be8e2fbb4c904e28e7e717803fc125a6e24e21d1bcb737b05e1c144c",
    "parameters.json": "399ddc81bd4607f5cf511c05568d38cf979ebabe02a929a1e54705e0121ada45",
    "power-result.json": "5f7be9a1751223eed1a0d2c63cbac8042876b8496998ea55dbbc5a934df47712",
    "power.py": "50b747701e92dad7cfc2fa3158e88564b83de9dee795ab11434bf3bd9d8c8e48"
}


def require(ok, why):
    if not ok:
        raise ValueError(why)


def mapping(pairs):
    answer={}
    for key,val in pairs:
        require(key not in answer, "repeated JSON property")
        answer[key]=val
    return answer


def bad_number(value):
    raise ValueError("nonfinite JSON number")


def parse(data):
    return json.loads(data,object_pairs_hook=mapping,parse_constant=bad_number)


def strict_equal(a,b):
    if type(a) is not type(b):
        return False
    if isinstance(a,dict):
        return a.keys()==b.keys() and all(strict_equal(a[k],b[k]) for k in a)
    if isinstance(a,list):
        return len(a)==len(b) and all(strict_equal(x,y) for x,y in zip(a,b))
    return a==b


def leaf_cover(leaves):
    require(type(leaves) is list and leaves,"empty interval cover")
    ptr=Fraction(0)
    for row in leaves:
        require(type(row) is list and len(row)==3,"invalid interval row")
        depth,index,bound=row
        require(type(depth) is int and type(index) is int and 0<=depth<=40 and 0<=index<1<<depth,"dyadic coordinates")
        require(type(bound) is str and Fraction(bound)>0,"strict lower bound required")
        require(ptr==Fraction(index,1<<depth),"interval order, overlap or hole")
        ptr=Fraction(index+1,1<<depth)
    require(ptr==1,"incomplete final interval")


def check_result(got,expected):
    require(strict_equal(got,expected),"changed exact certificate")
    leaf_cover(got['leaves'])


def refused(fn):
    try:
        fn()
    except (ValueError,IndexError,KeyError):
        return
    raise ValueError("an invalid result passed")


def hostile(expected):
    bad=deepcopy(expected);bad['leaves'].pop();refused(lambda:leaf_cover(bad['leaves']))
    bad=deepcopy(expected);bad['leaves'].insert(0,bad['leaves'][0]);refused(lambda:leaf_cover(bad['leaves']))
    bad=deepcopy(expected);bad['leaves'][0][0]=True;refused(lambda:leaf_cover(bad['leaves']))
    bad=deepcopy(expected);bad['leaves'][0][2]='0';refused(lambda:leaf_cover(bad['leaves']))
    bad=deepcopy(expected);bad['leaves'][0][2]='1';refused(lambda:check_result(bad,expected))
    bad=deepcopy(expected);bad['lower_direction_infinite_value']=[1,2];refused(lambda:check_result(bad,expected))
    bad=deepcopy(expected);del bad['parameters']['N'];refused(lambda:check_result(bad,expected))
    bad=deepcopy(expected);bad['max_depth']=float(bad['max_depth']);refused(lambda:check_result(bad,expected))
    refused(lambda:parse('{"order":4,"order":3}'));refused(lambda:parse('{"order":NaN}'))
    return 10


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--self-test',action='store_true')
    opts=ap.parse_args()
    for n,h in PINS.items():
        require(sha256((HERE/n).read_bytes()).hexdigest()==h,"source or published input differs: "+n)
    params=parse((HERE/'parameters.json').read_bytes())
    require(params=={'M':4,'N':24,'lower':'340315168725/1000000000000','upper':'340315168726/1000000000000','x':'21787956/100000000','tolerance':'1/1000000'},"fixed scientific question")
    results={}
    with TemporaryDirectory(prefix='angular-rational-') as directory:
        out=Path(directory)
        for name in ('bernstein','power'):
            expected=parse((HERE/(name+'-result.json')).read_bytes())
            output=out/(name+'.json')
            flags=['-O'] if sys.flags.optimize else []
            proc=subprocess.run([sys.executable,*flags,'-I','-S','-B',HERE/(name+'.py'),HERE/'parameters.json',output],
                                capture_output=True,timeout=180,check=True)
            actual=parse(output.read_bytes())
            check_result(actual,expected)
            results[name]=actual
        more=0
        if opts.self_test:
            more=hostile(results['bernstein'])
            for tag,patch in (('swapped radii',{'lower':params['upper']}),('wrong direction',{'x':'1'}),('wrong term count',{'N':3}),('zero tolerance',{'tolerance':'0'})):
                paramfile=out/'invalid.json';paramfile.write_text(json.dumps(dict(params,**patch)))
                output=out/'invalid-result.json'
                ret=subprocess.run([sys.executable,*flags,'-I','-S','-B',HERE/'bernstein.py',paramfile,output],
                                   capture_output=True,timeout=180)
                require(ret.returncode!=0 and not output.exists(),tag)
                more+=1
    print(json.dumps(dict(bernstein_intervals=len(results['bernstein']['leaves']),power_intervals=len(results['power']['leaves']),
                          lower_scaled_nats=results['bernstein']['lower_direction_infinite_value'],
                          upper_scaled_lower_bound=results['bernstein']['upper_direction_global_lower_bound'],
                          strict_pass='F < 0',rejected=more),sort_keys=True))


if __name__=='__main__':
    main()
