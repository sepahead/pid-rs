from itertools import permutations
import json
from pathlib import Path
root=Path(__file__).resolve().parent
fine_weights=list(zip((1,2,3,5,9,11,13,17),(18,11,9,6,8,4,3,1)))
cases=[]
def table(tag, coords, weights, order=(0,1,2)):
    rows=[]
    for state,values in enumerate(weights):
        for t,count in enumerate(values):
            if count:rows.append([*coords(state),t,count])
    return {"case":tag,"coarse_to_fine":list(order),"rows":rows}
for permutation in permutations(range(3)):
    def coords(x,p=permutation):
        levels=(x//4,x//2,x)
        return tuple(levels[p.index(i)] for i in range(3))
    cases.append(table("permutation-"+"".join(map(str,permutation)),coords,fine_weights,permutation))
cases.append(table("constant-coarse",lambda x:(0,x//2,x),fine_weights))
cases.append(table("middle-equals-coarse",lambda x:(x//4,x//4,x),fine_weights))
cases.append(table("middle-equals-fine",lambda x:(x//4,x,x),fine_weights))
cases.append(table("all-equal",lambda x:(x,x,x),fine_weights))
cases.append(table("all-equal-tied-order",lambda x:(x,x,x),fine_weights,(2,1,0)))
cases.append(table("target-constant",lambda x:(x//4,x//2,x),[(j+2,0) for j in range(8)]))
cases.append(table("target-independent",lambda x:(x//4,x//2,x),[(2*(j+1),3*(j+1)) for j in range(8)]))
base=cases[0]
independent=[[a,b,a,0,1] for a in (0,1) for b in (0,1)]
neg=[
 {"case":"incomparable", "coarse_to_fine":[0,1,2],"rows":independent},
 {"case":"fine-to-coarse","coarse_to_fine":[2,1,0],"rows":base["rows"]},
 {"case":"duplicate-state","coarse_to_fine":[0,1,2],"rows":base["rows"]+[base["rows"][0]]},
 {"case":"zero-count","coarse_to_fine":[0,1,2],"rows":[[0,0,0,0,0]]},
 {"case":"negative-count","coarse_to_fine":[0,1,2],"rows":[[0,0,0,0,-1]]},
 {"case":"boolean-count","coarse_to_fine":[0,1,2],"rows":[[0,0,0,0,True]]},
 {"case":"fractional-count","coarse_to_fine":[0,1,2],"rows":[[0,0,0,0,1.5]]},
 {"case":"no-observations","coarse_to_fine":[0,1,2],"rows":[]},
]
(root/"fixtures.json").write_text(json.dumps({"accepted":cases,"refused":neg},indent=2)+"\n")
