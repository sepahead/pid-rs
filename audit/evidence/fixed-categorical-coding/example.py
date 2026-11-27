"""Check prespecified sign labels with the installed pid-rs Python package."""
import itertools,json,math

def require(ok,why):
    if not ok:
        raise ValueError(why)

import numpy as np
import pid_core_rs as pid
design=list(itertools.product(range(2),repeat=3))
left=np.array([[10*i+j/8 for j in range(3)] for i in range(8)],dtype=np.float64)
increments=np.array([[(1+i/16+j/8)*(1 if bit else -1) for j,bit in enumerate(row)] for i,row in enumerate(design)])
increments[0,0]=0
right=left+increments
bits=(right>left).astype(np.int64)
require(bits.tolist()==[list(v) for v in design] and int((right==left).sum())==1,"complete exact known signs incl. zero")
fields=[bits[:,j:j+1].copy() for j in range(3)]
target=fields[0].copy()
def call(columns):
    res=pid.compute_categorical_sxpid3(*columns,target)
    require(len(res.entries)==18 and res.n_sources==3 and not res.pointwise_included and res.empirical_pmf.sample_count==8,"direct native fields")
    atoms={"+".join(map(str,x.antichain.sets)):[x.atom.informative_nats,x.atom.misinformative_nats,x.atom.net_nats] for x in res.entries}
    return res,atoms
direct,atoms=call(fields)
renamed,name_atoms=call([np.where(x==0,-11*(j+1),97+j).astype(np.int64) for j,x in enumerate(fields)])
merged,merged_atoms=call([np.zeros_like(fields[0]),*fields[1:]])
require(direct.empirical_pmf.observed_joint_states==8 and abs(direct.joint_mi_nats-math.log(2))<1e-12,"copied fair target")
require(set(atoms)==set(name_atoms) and max(abs(a-b) for k in atoms for a,b in zip(atoms[k],name_atoms[k]))<=1e-12,"bijection three sources")
require(abs(merged.joint_mi_nats)<1e-12 and all(abs(x[2])<1e-12 for x in merged_atoms.values()),"loss under coarsening")
try:
    pid.compute_categorical_sxpid3(increments[:,0:1],fields[1],fields[2],target)
except (TypeError,ValueError) as exc:
    refused=type(exc).__name__
else:
    raise ValueError("float input entered the direct typed route")
print(json.dumps(dict(design=[list(v) for v in design],sample_count=8,positive_vs_nonpositive=True,zero_increments=1,observed_joint_states=direct.empirical_pmf.observed_joint_states,atom_keys=sorted(atoms),copied_target_joint_nats_hex=direct.joint_mi_nats.hex(),merged_joint_nats_hex=merged.joint_mi_nats.hex(),max_bijection_difference_hex=max(abs(a-b) for k in atoms for a,b in zip(atoms[k],name_atoms[k])).hex(),raw_float_refusal=refused),indent=2,sort_keys=True))
