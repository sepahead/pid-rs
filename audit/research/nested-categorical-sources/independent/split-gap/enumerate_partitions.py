"""Enumerate pairs of empirical partitions and check the informative deficit using exact products."""
from fractions import Fraction
from itertools import product
import json

def require(condition, detail):
    if not condition:
        raise ValueError(detail)

def partitions(size):
    words=[(0,)]
    for _ in range(1,size):
        words=[w+(a,) for w in words for a in range(max(w)+2)]
    return words

def blocks(word):
    by_label={}
    for i,label in enumerate(word):
        by_label.setdefault(label,set()).add(i)
    return tuple(frozenset(by_label[label]) for label in word)

def imbalance_product(first,second):
    observed=Fraction(1)
    for left,right in zip(first,second,strict=True):
        observed*=Fraction(len(left | right),len(left))
    return observed

def relation(first,second):
    assignments={}
    for coarse,fine in zip(first,second,strict=True):
        assignments.setdefault(fine,set()).add(coarse)
    return all(len(options)==1 for options in assignments.values())

def attaining(first,second):
    coarse_blocks=set(first)
    fine_blocks=set(second)
    n=len(first)
    if len(coarse_blocks)!=2 or sorted(map(len,coarse_blocks))!=[n//2,(n+1)//2]:
        return False
    split=[fine for fine in fine_blocks if not any(fine<=coarse for coarse in coarse_blocks)]
    return len(split)==1 and len(split[0])==2

def inspect_partition_pairs():
    results=[]
    for n,bell in enumerate([1,2,5,15,52,203],1):
        keys=partitions(n)
        require(len(keys)==len(set(keys))==bell,("Bell count",n))
        partition_blocks={k:blocks(k) for k in keys}
        is_map=0
        equals=0
        witness=None
        lower=None if n==1 else Fraction(n//2+1,n//2)*Fraction((n+1)//2+1,(n+1)//2)
        for first,second in product(keys,repeat=2):
            a,b=partition_blocks[first],partition_blocks[second]
            measured=imbalance_product(a,b)
            complete=relation(first,second)
            require((measured==1)==complete,("iff",first,second))
            if complete:
                is_map+=1
                continue
            require(lower is not None and measured>=lower,("gap",first,second,measured))
            require((measured==lower)==attaining(a,b),("equality",first,second,measured))
            if measured==lower:
                equals+=1
                if witness is None:witness=[first,second]
        require(equals>0 if n>=2 else (is_map==1 and equals==0),"nonempty sharp case")
        results.append(dict(n=n,partitions=bell,ordered_pairs=bell**2,functions=is_map,
                            split_pairs=bell**2-is_map,attaining_pairs=equals,
                            minimum_product=str(lower) if lower else None,first_witness=witness))
    return results

def adversarial():
    true_coarse=(0,0,1)
    true_fine=(0,1,2)
    forward=imbalance_product(blocks(true_coarse),blocks(true_fine))
    reverse=imbalance_product(blocks(true_fine),blocks(true_coarse))
    require(forward==1 and reverse>1 and relation(true_coarse,true_fine) and not relation(true_fine,true_coarse),"directed relation")
    results={}
    for n in (4,8,16):
        m=n//2
        coarse=(0,)*m+(1,)*m
        fine=(0,)+(1,)*(m-1)+(0,)+(2,)*(m-1)
        got=imbalance_product(blocks(coarse),blocks(fine))
        expected=(1+Fraction(2,n))**2
        require(got==expected,("real mass denominator",n,got,expected))
        results[str(Fraction(1,n))]=str(got)
    return dict(directed_products=[str(forward),str(reverse)],real_weight_products=results)

def main():
    records=inspect_partition_pairs()
    print(json.dumps(dict(total_ordered_pairs=sum(r["ordered_pairs"] for r in records),
          records=records,adverse=adversarial()),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
