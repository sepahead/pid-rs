#!/usr/bin/env python3
"""Frozen finite Python-only controls; no solver, subprocess, or file writes.

--manifest constructs payload descriptors without importing the checker.
The ordinary CHECKER_PATH mode requires that exact frozen descriptor file.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

CHECKER_SHA = "d6e23bf5d329368cf9681c4b7ee069a2a30930c368c842514253c8d6a3476d2e"
PLAN_SHA = "f9faff1fcb5ee6e3ea08e186f1d8bb39573b41815f5ea630b2ac63f1e7d42d51"
CAPTURE = Path(__file__).resolve().parent / "raw"
M01 = "M01-reverse-order"
W01 = "W01-carrier-complete"
SOLVERS = ("z3", "cvc5")
VAR = ("a", "b", "c", "q", "h", "x", "k", "r", "tau") + tuple("w"+str(i) for i in range(16))
SORT = {n: ("BV", w) for n,w in (("a",7),("b",7),("c",7),("q",3),("h",3),("x",3),("k",4),("r",4))}
SORT.update({"tau":("Bool",0)})
SORT.update((n,("Int",0)) for n in VAR if n.startswith("w"))
QUERY = ("a","b","c","q","h","x","tau","k","r","(U a k)","(V a k)","N")

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",",":"), ensure_ascii=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def defaults():
    v={n:0 for n in VAR}
    v.update(a=64,b=64,c=64,tau=False)
    return v

def source_holds(family,key,cell):
    for mask in range(1,8):
        if family & (1 << (mask-1)):
            if all(not(mask & (1<<i)) or ((key>>(3-i))&1)==((cell>>(3-i))&1) for i in range(3)):
                return True
    return False

def derived(v):
    u=sum(v["w"+str(i)] for i in range(16) if source_holds(v["a"],v["k"],i))
    z=sum(v["w"+str(i)] for i in range(16) if source_holds(v["a"],v["k"],i) and (v["k"]&1)==(i&1))
    return u,z,sum(v["w"+str(i)] for i in range(16))

def type_text(s):
    return "(_ BitVec "+str(s[1])+")" if s[0]=="BV" else s[0]

def literal(value,s,indexed=False):
    if s[0]=="Bool":
        return "true" if value else "false"
    if s[0]=="Int":
        return str(value) if value>=0 else "(- "+str(-value)+")"
    if indexed:
        return "(_ bv"+str(value)+" "+str(s[1])+")"
    return "#b"+format(value,"0"+str(s[1])+"b")

def declaration(name,s,body,args="()"):
    return "(define-fun "+name+" "+args+" "+type_text(s)+" "+body+")"

def parts(v,solver,indexed=False):
    d=[declaration(n,SORT[n],literal(v[n],SORT[n],indexed)) for n in VAR]
    if solver=="z3":
        pattern=sum((1<<i) for i in range(3) if ((v["k"]>>(3-i))&1)==((v["r"]>>(3-i))&1))
        fix=(v["x"]==pattern and v["tau"]==((v["k"]&1)==(v["r"]&1))
             and all(v["w"+str(i)]==int(i in (v["k"],v["r"])) for i in range(16)))
        d += [declaration("fixture",("Bool",0),"true" if fix else "false"),
              declaration("positive-table",("Bool",0),"true" if all(v["w"+str(i)]>=0 for i in range(16)) else "false"),
              declaration("N",("Int",0),literal(derived(v)[2],("Int",0)))]
    u,z,n=derived(v)
    values=dict(v); values.update({"(U a k)":u,"(V a k)":z,"N":n})
    p=["("+k+" "+literal(values[k],SORT[k] if k in SORT else ("Int",0),indexed)+")" for k in QUERY]
    return d,p,values

def prefix(case,solver,status="sat"):
    echo=case+" expect="+status
    if solver=="cvc5":
        echo='"'+echo+'"'
    return (echo+"\n"+status+"\n").encode("ascii")

def frames(d,p):
    return "(\n"+"\n".join(d)+"\n)\n", "("+" ".join(p)+")\n"

def output(case,solver,v,d=None,p=None,indexed=False):
    ds,ps,_=parts(v,solver,indexed)
    m,g=frames(ds if d is None else d,ps if p is None else p)
    return prefix(case,solver)+(m+g).encode("ascii")

def payloads():
    tests=[]
    def add(name,case,solver,out,accepted=True,stage=None,reason=None,err=b"",native=0):
        tests.append({"id":name,"case":case,"solver":solver,"stdout":out,"stderr":err,"native":native,
                      "expected":{"accepted":accepted,"stage":stage,"reason":reason}})
    roster=json.loads((CAPTURE.parent/"OBSERVATIONS.json").read_bytes())["cases"]
    cases={row["case"].split("-",1)[0]:row["case"] for row in roster}
    for row in roster:
        case=row["case"]
        for solver in SOLVERS:
            r=row["solvers"][solver]
            add("P-real-"+case+"-"+solver,case,solver,(CAPTURE/case/(solver+".stdout")).read_bytes(),
                err=(CAPTURE/case/(solver+".stderr")).read_bytes(),native=r["native_exit"])
    for solver in SOLVERS:
        v=defaults();v.update(a=64,b=32,c=0,w0=-1)
        add("P-negative-Int-"+solver,M01,solver,output(M01,solver,v))
        v=defaults();v.update(a=64,b=32,c=0)
        d,p,_=parts(v,solver);m,g=frames(d,p)
        add("P-whitespace-"+solver,M01,solver,prefix(M01,solver)+("\n\t"+m.replace(" ","\t")+g.replace(" ","\t")+" \t\n").encode())
        add("P-BV-indexed-"+solver,M01,solver,output(M01,solver,v,indexed=True))
    v=defaults();v.update(a=64,b=32,c=0);d,p,_=parts(v,"z3");d[25]=declaration("fixture",("Bool",0),"true")
    add("P-opaque-helper-boundary",M01,"z3",output(M01,"z3",v,d=d))
    for solver in SOLVERS:
        v=defaults();v.update(a=64,b=32,c=0);d,p,values=parts(v,solver);raw=output(M01,solver,v)
        api=[
            ("nativeFalse",M01,solver,raw,b"",False,"transport","native"),
            ("native1",M01,solver,raw,b"",1,"transport","native"),
            ("native-1",M01,solver,raw,b"",-1,"transport","native"),
            ("native-float",M01,solver,raw,b"",0.0,"transport","native"),
            ("stdout-str",M01,solver,raw.decode(),b"",0,"transport","stdout-cap-or-type"),
            ("stderr-str",M01,solver,raw,"",0,"transport","stderr"),
            ("unknown-case","unknown-case",solver,raw,b"",0,"protocol","case"),
            ("unknown-solver",M01,"unknown",raw,b"",0,"protocol","solver"),
            ("stderr-warning",M01,solver,raw,b"warning\n",0,"transport","stderr"),
            ("NUL",M01,solver,raw+b"\0",b"",0,"parse","ascii-whitespace"),
            ("nonASCII",M01,solver,raw+b"\xff",b"",0,"parse","ascii-whitespace"),
            ("UnicodeLS",M01,solver,raw+b"\xe2\x80\xa8",b"",0,"parse","ascii-whitespace")]
        for n,c,s,o,e,native,stage,reason in api:
            add("N1-"+n+"-"+solver,c,s,o,False,stage,reason,e,native)
        pre=prefix(M01,solver);m,g=frames(d,p);rest=(m+g).encode()
        echo=pre.splitlines()[0]+b"\n"
        wrongquote=(b'"'+echo[:-1]+b'"\n' if solver=="z3" else echo[1:-2]+b"\n")+b"sat\n"+rest
        changes=[
            ("wrongcase",raw.replace(M01.encode(),b"M02-transpose-zeta",1),"protocol","echo-status"),
            ("wrongexpect",raw.replace(b"expect=sat",b"expect=unsat",1),"protocol","echo-status"),
            ("missingecho",b"sat\n"+rest,"protocol","echo-status"),
            ("duplicateecho",echo+pre+rest,"protocol","echo-status"),
            ("wrongquote",wrongquote,"protocol","echo-status"),
            ("wrongstatus",echo+b"unsat\n"+rest,"protocol","echo-status"),
            ("duplicatestatus",pre+b"sat\n"+rest,"model","two-frames"),
            ("missingmodel",pre+g.encode(),"model","two-frames"),
            ("missingvalues",pre+m.encode(),"model","two-frames"),
            ("reversed",pre+(g+m).encode(),"model","nullary-define-fun"),
            ("thirdframe",raw+b"()\n","model","two-frames"),
            ("trailingerror",raw+b'(error "bad")\n',"parse","atom-grammar"),
            ("unbalanced",raw+b"(","parse","unclosed-list"),
            ("leadingblank",b"\n"+raw,"protocol","echo-status"),
            ("comment",raw+b";comment\n","parse","atom-grammar"),
            ("trailingatom",raw+b"junk\n","model","two-frames")]
        for n,o,stage,reason in changes:
            add("N2-"+n+"-"+solver,M01,solver,o,False,stage,reason)
        for i,n in enumerate(VAR):
            x=list(d);del x[i]
            add("N3-missing-"+n+"-"+solver,M01,solver,output(M01,solver,v,d=x),False,"model","complete-roster")
            x=list(d);x.append(x[i])
            add("N3-duplicate-"+n+"-"+solver,M01,solver,output(M01,solver,v,d=x),False,"model","name-roster")
            old=SORT[n]
            new=("BV",3 if old[1]==7 else 4 if old[1]==3 else 7) if old[0]=="BV" else ("Int",0) if old[0]=="Bool" else ("Bool",0)
            x=list(d);x[i]=declaration(n,new,literal(False if new[0]=="Bool" else 0,new))
            add("N3-sort-"+n+"-"+solver,M01,solver,output(M01,solver,v,d=x),False,"type","declared-sort")
        for i,k in enumerate(QUERY):
            x=list(p);del x[i]
            add("N4-missing-"+str(i)+"-"+solver,M01,solver,output(M01,solver,v,p=x),False,"values","association-count")
            x=list(p);x.append(x[i])
            add("N4-duplicate-"+str(i)+"-"+solver,M01,solver,output(M01,solver,v,p=x),False,"values","association-count")
            s=SORT[k] if k in SORT else ("Int",0);old=values[k];new=not old if s[0]=="Bool" else old^1 if s[0]=="BV" else old+1
            x=list(p);x[i]="("+k+" "+literal(new,s)+")"
            add("N4-value-"+str(i)+"-"+solver,M01,solver,output(M01,solver,v,p=x),False,"values","assignment-disagreement")
        neutral=("M01","M02","M03","M04","M05","M06","M07","M08","M09","M10","M11","M12","M14","M16")
        for code in neutral:
            x=defaults()
            if code in ("M04","M05","M06","M07","M08","M09"):
                x.update(x=7,tau=True,w0=1)
            case=cases[code]
            add("N5-neutral-"+code+"-"+solver,case,solver,output(case,solver,x),False,"semantic","no-counterexample")
        bad=[
            ("C01-invalid-c","C01",dict(a=64,b=64,c=0,k=0,r=0,x=7,tau=True,w0=1)),
            ("C01-fixture-target","C01",dict(a=64,b=64,c=64,k=0,r=0,x=7,tau=False,w0=1)),
            ("M15-invalid-comparable","M15",dict(a=5,k=0,r=0)),
            ("M04-fixture-pattern","M04",dict(a=64,k=0,r=0,x=0,tau=True,w0=1)),
            ("M05-fixture-pattern","M05",dict(a=3,k=0,r=0,x=1,tau=True,w0=1)),
            ("M06-fixture-pattern","M06",dict(a=64,k=0,r=0,x=1,tau=True,w0=1)),
            ("M07-fixture-pattern","M07",dict(a=64,k=0,r=1,x=6,tau=False,w0=1,w1=1)),
            ("M08-fixture-pattern","M08",dict(a=64,k=0,r=2,x=2,tau=True,w0=1,w2=1)),
            ("M09-fixture-target","M09",dict(a=1,k=0,r=6,x=1,tau=False,w0=1,w6=1))]
        for n,code,overrides in bad:
            x=defaults();x.update(overrides);case=cases[code]
            add("N5-premise-"+n+"-"+solver,case,solver,output(case,solver,x),False,"semantic","premise-false")
        shapes=[
            ("nonnullary","a",declaration("a",SORT["a"],literal(v["a"],SORT["a"]),args="((dummy Int))"),"model","nullary-define-fun"),
            ("symbolic","a",declaration("a",SORT["a"],"unknown"),"type","bv-literal"),
            ("BVoverflow","a",declaration("a",SORT["a"],"(_ bv128 7)"),"type","bv-decimal-range"),
            ("BVwidth","a",declaration("a",SORT["a"],"#b00000000"),"type","bv-binary-width"),
            ("BVdigit","a",declaration("a",SORT["a"],"#b0000002"),"type","bv-binary-width"),
            ("Intreal","w0",declaration("w0",SORT["w0"],"0.0"),"type","integer-literal"),
            ("Intrational","w0",declaration("w0",SORT["w0"],"(/ 1 2)"),"type","integer-literal"),
            ("Intsymbol","w0",declaration("w0",SORT["w0"],"unknown"),"type","integer-literal"),
            ("Boolinteger","tau",declaration("tau",SORT["tau"],"1"),"type","bool-literal"),
            ("Booluppercase","tau",declaration("tau",SORT["tau"],"True"),"type","bool-literal")]
        for n,var,decl,stage,reason in shapes:
            x=list(d);x[VAR.index(var)]=decl
            add("N6-"+n+"-"+solver,M01,solver,output(M01,solver,v,d=x),False,stage,reason)
        if solver=="z3":
            helpers=[
                ("unknown",d+[declaration("foreign",("Bool",0),"true")],"model","name-roster"),
                ("wrongsort",d[:25]+[declaration("fixture",("Int",0),"0")]+d[26:],"type","declared-sort"),
                ("nonnullary",d[:25]+[declaration("fixture",("Bool",0),"true",args="((dummy Int))")]+d[26:],"model","nullary-define-fun"),
                ("duplicate",d+[d[25]],"model","name-roster")]
        else:
            helpers=[("foreign",d+[declaration("fixture",("Bool",0),"true")],"model","name-roster")]
        for n,x,stage,reason in helpers:
            add("N7-"+n+"-"+solver,M01,solver,output(M01,solver,v,d=x),False,stage,reason)
        huge=list(d);huge[VAR.index("w0")]=declaration("w0",SORT["w0"],"9"*257)
        resources=[
            ("stdout",b" "*(1048576+1),"transport","stdout-cap-or-type"),
            ("tokens",pre+(b"a "*65537),"parse","token-cap"),
            ("depth",pre+b"("*65+b")"*65+b"\n","parse","depth-cap"),
            ("integerlexeme",output(M01,solver,v,d=huge),"parse","atom-grammar")]
        for n,o,stage,reason in resources:
            add("N8-"+n+"-"+solver,M01,solver,o,False,stage,reason)
        wraw=(CAPTURE/W01/(solver+".stdout")).read_bytes()
        un=[("unknown",wraw.replace(b"\nunsat\n",b"\nunknown\n",1),b"",0,"protocol","echo-status"),
            ("native",wraw,b"",1,"transport","native"),
            ("stderr",wraw,b"warning\n",0,"transport","stderr"),
            ("model",wraw+b"()\n",b"",0,"protocol","unsat-trailing"),
            ("case",wraw.replace(W01.encode(),b"W02-exactly-18-distinct",1),b"",0,"protocol","echo-status"),
            ("error",wraw+b'(error "bad")\n',b"",0,"protocol","unsat-trailing")]
        for n,o,e,native,stage,reason in un:
            add("N9-"+n+"-"+solver,W01,solver,o,False,stage,reason,e,native)
    if len(tests)!=454 or len({t["id"] for t in tests})!=454:
        raise RuntimeError("prospective count/identity mismatch")
    if sum(t["expected"]["accepted"] for t in tests)!=85:
        raise RuntimeError("prospective positive count mismatch")
    return tests

def manifest(tests):
    rows=[]
    for t in tests:
        d={k:t[k] for k in ("id","case","solver","expected")}
        for key in ("stdout","stderr"):
            x=t[key];b=x if type(x) is bytes else x.encode("utf-8")
            d[key]={"type":type(x).__name__,"bytes":len(b),"sha256":sha(b)}
        d["native"]={"type":type(t["native"]).__name__,"value":t["native"]}
        rows.append(d)
    return {"schema":"smt39-prospective-materialized-payloads-v1","count":454,"positive":85,"negative":369,
            "checker_sha256":CHECKER_SHA,"plan_v2_sha256":PLAN_SHA,"rows":rows}

def main(args):
    tests=payloads()
    encoded=(canonical(manifest(tests))+"\n").encode("ascii")
    if len(args)==1 and args[0]=="--manifest":
        sys.stdout.buffer.write(encoded)
        return 0
    if len(args)!=1:
        raise RuntimeError("usage: controls.py CHECKER_PATH; or --manifest without checker import")
    frozen=Path(__file__).with_name("PAYLOADS.json").read_bytes()
    if frozen!=encoded:
        raise RuntimeError("materialized payload manifest differs before checker import")
    path=Path(args[0]).resolve()
    if sha(path.read_bytes())!=CHECKER_SHA:
        raise RuntimeError("checker source hash changed")
    sys.dont_write_bytecode=True
    spec=importlib.util.spec_from_file_location("frozen_smt39_checker",str(path))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows=[];mismatches=[]
    for t in tests:
        wanted=t["expected"]
        try:
            d=module.validate(t["case"],t["solver"],t["stdout"],t["stderr"],t["native"])
            if type(d) is not dict:
                raise RuntimeError("checker decision is not a dict")
            actual={k:d.get(k) for k in ("accepted","stage","reason")}
            okay=(type(actual["accepted"]) is bool and actual==wanted)
            if wanted["accepted"]:
                expected_status="unsat" if t["case"].startswith("W") else "sat"
                okay=okay and d.get("status")==expected_status and d.get("unsat_certificate_checked") is False
                okay=okay and d.get("semantic_sat_model_checked") is (expected_status=="sat")
                if expected_status=="sat":
                    okay=okay and d.get("premises_checked") is True and d.get("negated_property_checked") is True
                    okay=okay and d.get("opaque_auxiliary_bodies_not_interpreted")==(["N","fixture","positive-table"] if t["solver"]=="z3" else [])
            if not okay:
                mismatches.append({"id":t["id"],"expected":wanted,"actual":actual})
        except BaseException as exc:
            actual={"unexpected_exception":type(exc).__name__,"message":str(exc)[:160]}
            mismatches.append({"id":t["id"],"expected":wanted,"actual":actual})
        rows.append({"id":t["id"],"expected":wanted,"actual":actual})
    result={"count":len(tests),"all_expected_decisions_observed":not mismatches,"mismatches":mismatches,
            "checker_sha256":CHECKER_SHA,"payload_manifest_sha256":sha(encoded),
            "positive":85,"negative":369,"controls":rows,
            "credit":"Finite Python decisions only; projected assignments, not full helper models or UNSAT certificates."}
    out=(canonical(result)+"\n").encode("ascii")
    if len(out)>1048576:
        raise RuntimeError("control result exceeds fixed1MiB")
    sys.stdout.buffer.write(out)
    return 0 if not mismatches else 1

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
