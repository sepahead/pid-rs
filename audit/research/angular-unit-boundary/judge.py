"""Fixed separate read-only check by a telescoping axial-tail enclosure."""
import argparse
import hashlib
import json
from fractions import Fraction as Q
from math import comb, isqrt
from pathlib import Path

SCALE = 10**18
TAU = Q(1, 10**6)


def require(test, reason):
    if not test:
        raise ValueError(reason)


def keys(pairs):
    record = {}
    for key, value in pairs:
        require(key not in record, 'duplicate key')
        record[key] = value
    return record


def sqrt_dyadic(value):
    denominator = 2**192
    floor = isqrt((value.numerator * denominator**2) // value.denominator)
    lo, hi = Q(floor, denominator), Q(floor + 1, denominator)
    require(lo*lo <= value < hi*hi, 'sqrt interval')
    return lo, hi


def negative_log(k):
    z = 1-k
    require(0 <= z < Q(1, 4), 'proper branch ordinary log domain')
    power = z
    total = Q(0)
    for exponent in range(1, 81):
        total += power/exponent
        power *= z
    return total, total+power/(81*(1-z))


def proper(w):
    lo, hi = sqrt_dyadic(1-w*w)
    k_lo,k_hi=(1+lo)/2,(1+hi)/2
    return -negative_log(k_lo)[1]+w/(1+hi), -negative_log(k_hi)[0]+w/(1+lo)


def atom():
    a,b = proper(Q(1,2))
    c,d = proper(Q(2,3))
    return 2*a-d,2*b-c


def g(n):
    return Q(comb(2*n,n),4**n)/(6*(n-Q(11,10)))


def tail(order):
    n=order+1
    require(n>=2,'tail domain')
    above=g(n)
    return (1-Q(2,n*n))*above,above


def signed_interval(order,h):
    lo,hi=tail(order)
    return [(SCALE*(lo-TAU*h[1])).__floor__(),(SCALE*(hi-TAU*h[0])).__ceil__()]


def check(raw,h):
    require(type(raw) is bytes and len(raw)<4096,'bounded JSON')
    rec=json.loads(raw,object_pairs_hook=keys)
    require(type(rec) is dict and set(rec)=={'schema','order','scale','previous','current'},'fields')
    require(rec['schema']=='angular-unit-order-v1' and type(rec['scale']) is int and rec['scale']==SCALE,'schema/scale')
    m=rec['order'];require(type(m) is int and 2<=m<=32768,'order')
    bounds={}
    for key,i,positive in [('previous',m-1,True),('current',m,False)]:
        interval=rec[key]
        require(type(interval) is list and len(interval)==2 and all(type(n) is int and abs(n)<10**34 for n in interval),'typed endpoints')
        left,right=interval;require(0<=right-left<=2,'ordered narrow interval')
        a,b=signed_interval(i,h);require(a<=b and max(a,left)<=min(b,right),'independent enclosures disjoint')
        require(min(a,left)>0 if positive else max(b,right)<0,'strict independent and proposed signs')
        bounds[key]=[a,b]
    return rec,bounds


def main():
    parser=argparse.ArgumentParser();parser.add_argument('proposed',type=Path);parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    for j in range(2,42):
        coeff=Q(comb(2*j,j),4**j*2*j*(2*j-1));e=Q(94*j-11,5*j*(2*j-1)*(10*j+3))
        require(coeff==(1-e)*(g(j)-g(j+1)) and 0<e<Q(2,j*j),'telescoping identities')
    h=atom();require(Q(1,8)<=h[0]<=h[1]<1,'positive denominator')
    raw=args.proposed.read_bytes();rec,bounds=check(raw,h);rejected=0
    if args.self_test:
        for field,value in [('order',True),('order',rec['order']-1),('order',rec['order']+1),('order',32769),('scale',10**17),('previous',[False,True]),('previous',list(reversed(rec['previous']))),('current',[1000000000000,1000000000001]),('previous',[1,1000]),('current',[-10**30,-10**30+1]),('other',0)]:
            changed=dict(rec);changed[field]=value
            try: check(json.dumps(changed).encode(),h)
            except ValueError: rejected+=1
            else:raise ValueError('hostile control passed '+field)
        for altered in [b'{"order":3,'+raw.lstrip()[1:],json.dumps({k:v for k,v in rec.items() if k!='previous'}).encode()]:
            try:check(altered,h)
            except ValueError:rejected+=1
            else:raise ValueError('hostile structure passed')
    print(json.dumps({'order':rec['order'],'scale':SCALE,'independent_enclosures':bounds,'proposed_sha256':hashlib.sha256(raw).hexdigest(),'rejected':rejected,'finite_algebra_cases':40},sort_keys=True))

if __name__=='__main__':main()
