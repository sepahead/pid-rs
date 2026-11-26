"""Check the original 4,000 seeded draws for the finite categorical one-Lambda bound."""
from collections import Counter
from fractions import Fraction
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, product
from math import prod
import argparse
import json
import random

LOW_ROUND = Fraction(99999965435, 10**11)
HIGH_ROUND = Fraction(99999965445, 10**11)

def need(condition, message):
    if not condition:
        raise ValueError(message)

def encoded(value):
    return (json.dumps(value, separators=(',', ':'), sort_keys=True) + '\n').encode()

def shares(rng, amount, size):
    parts = [rng.random() + 1e-6 for _ in range(size)]
    denominator = sum(parts)
    result = [int(amount * x / denominator) for x in parts]
    result[0] += amount - sum(result)
    need(sum(result) == amount and min(result) >= 0, 'nonnegative share of the moved mass')
    return result

def draws():
    """Keep the original order of random draws and original binary64 share construction."""
    rng = random.Random(1)
    for trial in range(4000):
        n = rng.choice([2, 2, 3])
        shape = [rng.choice([2, 2, 3]) for _ in range(n)] + [rng.choice([2, 3])]
        size = prod(shape)
        support = [i for i in range(size) if rng.random() < .7]
        if len(support) < 2:
            continue
        w = [0] * size
        for i in support:
            w[i] = (1 + int(rng.random() ** rng.choice([1, 3, 6]) * 10**6)) * 10**12
        minimum = min(w[i] for i in support)
        small = rng.random() < .25
        proportion = 10 ** rng.uniform(-12, -1.3) if small else rng.uniform(.05, .999)
        amount = int(proportion * minimum)
        if amount == 0:
            continue
        donors = rng.sample(support, rng.randint(1, min(3, len(support) - 1)))
        rest = [i for i in support if i not in donors]
        receivers = rng.sample(rest, rng.randint(1, min(3, len(rest))))
        v = w.copy()
        for i, units in zip(donors, shares(rng, amount, len(donors))):
            v[i] -= units
        for i, units in zip(receivers, shares(rng, amount, len(receivers))):
            v[i] += units
        yield trial, shape, w, v, amount

def admissible(w, v, move):
    need(len(w) == len(v) and bool(w), 'two nonempty equal-length tables')
    need(all(type(x) is int and x >= 0 for x in w + v), 'nonnegative integer weights')
    supp = [i for i, x in enumerate(w) if x]
    need(bool(supp) and supp == [i for i, x in enumerate(v) if x], 'the fixed occupied support')
    need(sum(w) == sum(v), 'same total mass')
    minimum = min(w[i] for i in supp)
    need(type(move) is int and 0 < move < minimum, 'strict displacement below the minimum weight')
    need(sum(abs(a-b) for a,b in zip(w,v)) == 2*move, 'the declared total variation')
    return supp, minimum

@lru_cache(maxsize=None)
def families(n):
    masks = tuple(range(1, 2**n))
    return tuple(f for i in range(1, len(masks)+1) for f in combinations(masks, i)
                 if all((a & b) not in (a,b) for a,b in combinations(f,2)))

@lru_cache(maxsize=None)
def events(shape):
    n = len(shape)-1
    cells = tuple(product(*(range(k) for k in shape)))
    result = []
    for z in cells:
        same_target = tuple(i for i,c in enumerate(cells) if c[-1] == z[-1])
        masks = [sum(1<<j for j in range(n) if c[j]==z[j]) for c in cells]
        row = []
        for family in families(n):
            sources = tuple(i for i,m in enumerate(masks) if any(m & f == f for f in family))
            joint = tuple(i for i in same_target if i in sources)
            row.append((family,sources,joint))
        result.append((z,same_target,row))
    return result

def compare(num, den, minimum, move):
    need(min(num, den) > 0 and 0 < move < minimum, 'positive factor and bound')
    high, low = max(num,den), min(num,den)
    gap = minimum * low - (minimum - move) * high
    return (gap > 0) - (gap < 0), gap, high, low

def series(s, terms):
    """Enclose ln(s) for 1 <= s <= 2 with exact rational arithmetic."""
    need(1 <= s <= 2 and terms >= 1, 'series domain')
    z=(s-1)/(s+1); power=z; square=z*z; partial=Fraction()
    for i in range(terms):
        partial += power/(2*i+1)
        power *= square
    tail = 2*power/((2*terms+1)*(1-square))
    return 2*partial, 2*partial+tail

@lru_cache(maxsize=None)
def log_two(terms):
    return series(Fraction(2),terms)

def log_interval(r, terms):
    need(r >= 1, 'a logarithm of a rational at least one')
    e = max(0,r.numerator.bit_length()-r.denominator.bit_length())
    if r < 2**e:
        e -= 1
    reduced=r/2**e
    need(1<=reduced<2,'binary range reduction')
    l,u=series(reduced,terms);a,b=log_two(terms)
    return e*a+l,e*b+u

def quotient_interval(f, bound, terms):
    lo,hi=log_interval(f,terms);blo,bhi=log_interval(bound,terms)
    need(blo>0,'positive logarithm of the bound')
    return lo/bhi,hi/blo

def grid(q, scale, ceiling=False):
    y=q*scale
    return -(-y.numerator//y.denominator) if ceiling else y.numerator//y.denominator

def inspect(panel, records=None):
    digest=sha256(); tables=0; pairs=0
    counts=[Counter(),Counter(),Counter()]; ties=[[],[],[]]
    near={}; selected_records=[]
    for trial,shape,w,v,move in panel:
        need(prod(shape)==len(w),'alphabet and table dimensions')
        support, minimum=admissible(w,v,move)
        signature=encoded([trial,shape,move,w,v]);digest.update(signature)
        if records is not None:records.write(signature)
        tables+=1
        for zi in support:
            z,target,groupings=events(tuple(shape))[zi]
            c=sum(w[i] for i in target);cc=sum(v[i] for i in target)
            for family,src,joint in groupings:
                a=sum(w[i] for i in src);aa=sum(v[i] for i in src)
                b=sum(w[i] for i in joint);bb=sum(v[i] for i in joint)
                need(min(a,aa,b,bb,c,cc)>0,'all six source/target/intersection event weights')
                fact=((a,aa),(cc*b,bb*c),(a*bb*c,aa*cc*b))
                for mode,(num,den) in enumerate(fact):
                    code,gap,high,low=compare(num,den,minimum,move)
                    need(code>=0,('real exact violation',trial,z,family,mode,num,den))
                    counts[mode]['strict' if code else 'equal']+=1
                    if code==0:
                        if mode==0:
                            structural=a==minimum and a-aa==move
                        elif mode==1:
                            structural=b==minimum and b-bb==move and c==cc
                        else:structural=False
                        ties[mode].append([trial,zi,list(z),list(family),num>den,structural])
                    if mode==2:
                        # 1 - log(F)/log(B) >= (B-F)/(B(B-1)), F=high/low, B=minimum/(minimum-move).
                        # The integer gap above is low*minimum-high*(minimum-move).
                        threshold=1-LOW_ROUND
                        effect=(minimum-move)*gap*threshold.denominator
                        needed=low*minimum*move*threshold.numerator
                        if effect<=needed:
                            key=Fraction(high,low),Fraction(minimum,minimum-move)
                            near.setdefault(key,[]).append([trial,zi,list(z),list(family)])
                pairs+=1
    need(tables>0 and pairs>0,'nonempty finite assessment')
    need(bool(near),'no near-bound survivor to support the displayed maximum')
    candidates=[]
    for (factor,bound),locations in near.items():
        lo,hi=quotient_interval(factor,bound,24)
        need(hi<HIGH_ROUND, ('upper rounding threshold undecided',locations[0]))
        if hi>=LOW_ROUND:
            need(lo>LOW_ROUND,'lower rounding midpoint undecided')
            candidates.append((lo,hi,factor,bound,locations))
    need(bool(candidates),'attainment of the lower rounding threshold')
    lower=max(z[0] for z in candidates)
    winners=[x for x in candidates if x[1]>=lower]
    for lo,hi,factor,bound,loc in winners:
        selected_records.append({'factor':str(factor),'bound':str(bound),'locations':loc,
            'enclosing_integers_at_1e16':[grid(lo,10**16),grid(hi,10**16,True)]})
    return {'schema':'finite-categorical-local-continuity-exact-v1',
            'seed':1,'attempted':4000,'used':tables,'supported_row_family_pairs':pairs,
            'panel_sha256':digest.hexdigest(),'component_comparisons':counts,
            'exact_ties':ties,'all_ties_have_losing_minimum_fibre':[all(x[-1] for x in t) if t else None for t in ties],
            'strict_signed_maximum_certificate':{'round_to_ten_decimals':'0.9999996544',
              'strict_lower_midpoint':str(LOW_ROUND),'strict_upper_midpoint':str(HIGH_ROUND),
              'screen_surviving_locations':sum(map(len,near.values())),'distinct_surviving_factor_pairs':len(near),
              'odd_series_terms_after_reduction':24,'possible_top_factor_pairs':selected_records}}

def controls():
    # Three categories of one source and constant target. The reference row is in the first cell.
    # In the strict case 1-log(U)/log(2)=log(1+2/H)/log(2)<4/H<10^-60.
    # The last strict inequality uses H=10^70 and log(2)>1/2.
    h=10**70;move=h//2;w=[h,h,h];v=[h-move+1,h-1,h+move]
    _,m=admissible(w,v,move);strict,gap,_,_=compare(w[0],v[0],m,move)
    need(strict==1 and Fraction(4,h)<Fraction(1,10**60),'strict genuine tolerance tie')
    true=[h-move,h,h+move];_,m=admissible(w,true,move)
    need(compare(w[0],true[0],m,move)[0]==0,'genuine attaining table')
    need(compare(2*10**70+1,10**70,2,1)[0]==-1,'positive scalar strictly above bound')
    incoming={'empty':([],[],1),'other support':([1,1,0],[1,0,1],1),'wrong total':([4,4],[3,6],1),
              'zero move':([2,2],[2,2],0),'wrong change':([3,3],[2,4],2),
              'negative mass':([7,4],[12,-1],1),'floor not strict':([2,4,2],[1,3,4],2)}
    negative={}
    for label,args in incoming.items():
        try:admissible(*args)
        except ValueError as exc:negative[label]=str(exc)
        else:raise ValueError('accepted '+label)
    need(len(families(2))==4 and len(families(3))==18,'nonempty antichain sizes')
    return {'valid_near_tie':'H=10^70; w=(H,H,H); v=(H/2+1,H-1,3H/2). Exact order is strict; its ratio differs from one by less than 4/H.',
     'valid_exact_tie':'v=(H/2,H,3H/2), otherwise same.','invalid_scalar_above_bound_rejected':True,'false_premises_rejected':negative}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--records',type=argparse.FileType('wb'))
    p.add_argument('--controls-only',action='store_true');args=p.parse_args()
    result={'controls':controls()}
    if not args.controls_only:result.update(inspect(draws(),args.records))
    print(json.dumps(result,indent=2,sort_keys=True))
