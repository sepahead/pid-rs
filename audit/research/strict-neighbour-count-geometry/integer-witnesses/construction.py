"""Finite integer coordinates for all feasible one-anchor labels in the registered range."""
import json


def array(n,k,x,y):
    # Separate two scales. The highest offset is strictly below one unit of the coarse grid.
    unit = 1 << (7*n+16)
    p,q = x-k,y-k
    neither = n-k-p-q
    region=[(2,3)]*(k-1)
    if p:
        region.extend([(2,10)]+[(2,22)]*(p-1)+[(22,2)]*q+[(23,24)]*neither)
    elif q:
        region.extend([(10,2)]+[(22,2)]*(q-1)+[(23,24)]*neither)
    else:
        region.extend([(10,10)]+[(23,24)]*(neither-1))
    points=[[0,0,0]]
    for j,(a,b) in enumerate(region,1):
        da,db=(0,0) if a==b==10 else (1 << (6*j),1 << (6*j+3))
        points.append([a*unit+da,100*j*unit,b*unit+db])
    return points


def main():
    cases=[]
    for n in range(2,10):
        for k in range(1,n):
            for x in range(k,n+1):
                for y in range(k,n+1):
                    if x+y<=n+k:
                        cases.append(dict(n=n,k=k,x=x,y=y,kind='corner' if x==y==k else 'open',rows=array(n,k,x,y)))
    print(json.dumps(cases,separators=(',',':')))


if __name__=='__main__':
    main()
