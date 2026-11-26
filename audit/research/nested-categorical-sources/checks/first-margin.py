from fractions import Fraction
from pathlib import Path
import argparse,json,runpy
def require(x,msg):
    if not x:raise ValueError(msg)
def comps(n,parts):
    if parts==1:
        yield (n,)
        return
    for i in range(n+1):
        for tail in comps(n-i,parts-1):yield (i,)+tail
def exact(grid):
    # Rebuild each occupied cell's two events from the list of individual observations.
    obs=[(i,j) for i,row in enumerate(grid) for j,v in enumerate(row) for _ in range(v)]
    q=Fraction(1)
    maps={}
    for x,y in obs:
        single=sum(a==x for a,b in obs)
        union=sum(a==x or b==y for a,b in obs)
        q*=Fraction(union,single)
        maps.setdefault(y,set()).add(x)
    return q,all(len(rows)==1 for rows in maps.values())
def main():
    parser=argparse.ArgumentParser();parser.add_argument('candidate',type=Path);parser.add_argument('output',type=Path);a=parser.parse_args()
    agenda=runpy.run_path(str(a.candidate));rows=[];checked=0;eq=0
    for w,h,limit in ((2,3,9),(3,2,9),(3,3,5)):
        for n in range(1,limit+1):
            smallest=None;fail=0;reached=0
            bound=agenda['minimum'](n)
            for counts in comps(n,w*h):
                grid=[counts[i*h:(i+1)*h] for i in range(w)]
                q,det=exact(grid);newq,newdet=agenda['certificate'](grid)
                require((newq,newdet)==(q,det),'candidate correspondence')
                require((q==1)==det,'functional equivalence')
                checked+=1;eq+=det
                if not det:
                    require(type(bound) is Fraction and q>=bound,'minimum')
                    if smallest is None or q<smallest:smallest=q
                    fail+=1;reached+=q==bound
            if n==1:require(bound is None and smallest is None,'N=1')
            elif (w,h)==(2,3):require(smallest==bound and reached>0,'sharpness on 2x3')
            rows.append([w,h,n,fail,reached,str(smallest)])
    for n in range(2,11):
        grid=agenda['witness'](n);q,det=exact(grid)
        require(sum(map(sum,grid))==n and not det and q==agenda['minimum'](n),'constructed equality')
    for bad in ([],[[]],[[0,0],[0,0]],[[1,-1],[0,2]],[[1,0],[0]],[[True,0],[0,1]]):
        try:agenda['certificate'](bad)
        except ValueError:pass
        else:raise ValueError('bad grid admitted')
    wrong=[]
    values=[(3,[[1,0,0],[1,0,1]]),(5,[[2,0,0],[1,0,2]])]
    for n,grid in values:
        q,det=exact(grid)
        reversed_q,reversed_det=exact(list(zip(*grid)))
        missing=Fraction(1)
        for i,row in enumerate(grid):
            for j,v in enumerate(row):
                if v:missing*=Fraction(sum(row)+sum(g[j] for g in grid)-v,sum(row))
        if q!=reversed_q:wrong.append('reversed direction')
        if q!=missing:wrong.append('ignored multiplicities')
        if q==agenda['minimum'](n) and q<q+Fraction(1,10**12):wrong.append('excess margin')
    require(set(wrong)=={'reversed direction','ignored multiplicities','excess margin'},'hostile discriminators')
    summary={'tables':checked,'deterministic':eq,'ambiguous':checked-eq,'by_shape_and_total':rows,'witness_totals':list(range(2,11)),'bad_inputs':6,'detected_errors':sorted(set(wrong))}
    a.output.write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(checked,eq,checked-eq,len(rows),len(set(wrong)))
if __name__=='__main__':main()
