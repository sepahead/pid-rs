"""Native report sources and source-only readers for ordered Boolean-pair output."""

import collections
import hashlib

CODE = """namespace ArchivedTrace

def code : Option (List Bool) → Nat
  | some [p, q] => (if p then 2 else 0) + (if q then 1 else 0)
  | _ => 4

end ArchivedTrace
"""

CONTROL = """import TraceCode
#reduce ArchivedTrace.code (some [false,false])
#reduce ArchivedTrace.code (some [false,true])
#reduce ArchivedTrace.code (some [true,false])
#reduce ArchivedTrace.code (some [true,true])
#reduce ArchivedTrace.code none
#reduce ArchivedTrace.code (some [])
#reduce ArchivedTrace.code (some [true,false,true])
"""

def coordinates(case):
    if case=="W15":return [(k,r) for k in range(16) for r in range(16)]
    if case in ("W01","W03"):return [(i,) for i in range(128)]
    raise ValueError("unknown case")

def source(case):
    out=["import OriginalContract","import TraceCode","set_option maxRecDepth 65536","set_option maxHeartbeats 20000000",""]
    for point in coordinates(case):
        if len(point)==1:
            point_text=f"(⟨{point[0]}, by decide⟩ : Fin 128)"
        else:
            point_text=f"((⟨{point[0]}, by decide⟩ : Fin 16), (⟨{point[1]}, by decide⟩ : Fin 16))"
        out.append("#reduce ArchivedTrace.code (OriginalContract.observe "+point_text+")")
    return "\n".join(out)+"\n"

def read_codes(path):
    raw=path.read_bytes()
    lines=raw.splitlines(keepends=True)
    if not lines or any(x not in {b"0\n",b"1\n",b"2\n",b"3\n",b"4\n"} for x in lines):
        raise ValueError("unexpected reduction output or incomplete line")
    return [int(x) for x in lines],hashlib.sha256(raw).hexdigest()

def read_control(path):
    values,sha=read_codes(path)
    if values!=[0,1,2,3,4,4,4]:raise ValueError("artificial true/false/failure/arity trace")
    return {"codes":values,"sha256":sha}

def read_original(case,path):
    coords=coordinates(case)
    values,sha=read_codes(path)
    allowed={0,1,2} if case=="W03" else {2}
    if len(values)!=len(coords) or not set(values)<=allowed:
        raise ValueError("wrong finite cardinality, joint truth, ordered result or failed evaluation")
    return {"coordinate_order":"numeric ascending, second coordinate varies fastest",
            "projected_count":len(values),"code_histogram":dict(sorted(collections.Counter(values).items())),
            "rows":[{"projected":p,"assertions":[bool(v&2),bool(v&1)]} for p,v in zip(coords,values)],
            "stdout_sha256":sha}

