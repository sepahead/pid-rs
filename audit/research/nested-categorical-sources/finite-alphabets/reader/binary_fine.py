"""Finite check of the directed informative gap with at most two occupied fine labels."""
from fractions import Fraction
from functools import lru_cache
from itertools import product
import json
def need(condition, reason):
    if not condition:
        raise ValueError(reason)
def counts(n,length):
    if length==1:
        yield (n,)
        return
    for k in range(n+1):
        for rest in counts(n-k,length-1):
            yield (k,)+rest
@lru_cache(maxsize=None)
def factor(total, overlap, margin, multiplicity):
    return Fraction(margin+total-overlap,margin)**multiplicity
def observed(table):
    occupied=[r for r in table if sum(r)]
    columns=tuple(map(sum,zip(*occupied)))
    result=Fraction(1)
    for row in occupied:
        for c,total in zip(row,columns):
            if c:result*=factor(total,c,sum(row),c)
    return result,occupied,columns
def equalizer(rows,N):
    if sorted(map(sum,rows))!=[1,N-1]:
        return False
    return any(sorted(col)==[1,1] for col in zip(*rows))
def read_case(cells,nx):
    return [tuple(cells[i:i+2]) for i in range(0,2*nx,2)]
def experiments():
    output={}
    for nx,cap in ((2,25),(3,12),(4,8)):
        sizes={}
        for n in range(1,cap+1):
            target=Fraction(2*n,n-1) if n>=2 else None
            const=Fraction(n**n,(n-1)**(n-1)) if n>=2 else None
            best={};tot={'all':0,'positive':0,'attain':0,'both_columns_split':0,'constant_fine_positive':0}
            for cells in counts(n,2*nx):
                G,rows,cols=observed(read_case(cells,nx));pairs=tuple(zip(*rows))
                splits=sum(sum(c>0 for c in col)>1 for col in pairs)
                tot['all']+=1
                if not splits:need(G==1,'map');continue
                need(n>=2 and G>=target,'sharp lower bound')
                active=sum(v>0 for v in cols)
                best[active]=min(best.get(active,G),G);tot['positive']+=1
                need((G==target)==equalizer(rows,n),'full equality class')
                tot['attain']+=G==target
                if active==1:
                    tot['constant_fine_positive']+=1
                    need(G>=const,'constant fine lower bound')
                    need((G==const)==(sorted(map(sum,rows))==[1,n-1]),'constant fine equality')
                if splits==2:
                    tot['both_columns_split']+=1
                    need(G>=4 and G>target,'two split columns')
            if n>=2:need(best.get(1)==const,'one occupied label sharpness')
            if n>=3:need(best.get(2)==target,'two occupied labels sharpness')
            if n==2:need(2 not in best,'two occupied fine labels cannot fail at N=2')
            sizes[n]={**tot,'one_label_min':str(best.get(1)),'two_label_min':str(best.get(2))}
        output[str(nx)+'x2']=sizes
    for n in range(2,513):
        rows=[(1,n-2),(1,0)]
        G,_,_=observed(rows)
        need(G==Fraction(2*n,n-1),'direct attaining family')
    G,_,_=observed([(1,2),(1,0)])
    need(G==Fraction(8,3) and G!=Fraction(9,4),'N4 binary correction')
    reverse,_,_=observed([(1,1),(2,0)])
    need(reverse!=G,'orientation test at N4')
    return {'tables':output,'attaining_for_each_N':[2,512],'G_at_N4':str(G),'G_for_transpose_at_N4':str(reverse),'predicted_limit_of_N_D':'ln(2)'}
if __name__=='__main__':
    print(json.dumps(experiments(),indent=2,sort_keys=True))
