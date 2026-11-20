"""Rebuild the registered source templates or score a separately registered hosted attempt."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import sys
import time

HERE=Path(__file__).resolve().parent
def local(name):
    spec=importlib.util.spec_from_file_location(name,HERE/(name+".py"))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
A=local("assembly")
require=A.require
HEX40=re.compile(r"[0-9a-f]{40}\Z")
HEX64=re.compile(r"[0-9a-f]{64}\Z")
LIMITS={"campaign_seconds":5400,"subprocess_seconds":900,"retained_bytes":1073741824,
        "group_rss_bytes":4294967296}
STOCK_VERSION="4.34.1"
STOCK_SHA="47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4"
STOCK_GIT="5045d0056413266e57c625dcd7c365b10e377c52"
ALLOWED=["Classical.choice","Quot.sound","propext"]
PAYLOADS=[A.PAYLOAD+"/"+c+".json" for c in A.CASES]
PUSH_REF=re.compile(r"refs/heads/review/three-source-original/([0-9a-f]{40})-([0-9a-f]{64})\Z")

def trigger(event, ref, commit, registration, registration_hash, event_payload):
    if event=="push":
        match=PUSH_REF.fullmatch(ref)
        require(match is not None and match.groups()==(registration,registration_hash),
                "registration identities must equal the complete reserved remote branch suffix")
        require(event_payload.get("ref")==ref and event_payload.get("after")==commit and
                event_payload.get("deleted") is False,"push ref and event commit")
    elif event=="workflow_dispatch":
        args=event_payload.get("inputs",{})
        require(args.get("registration_commit")==registration and args.get("registration_sha256")==registration_hash,
                "dispatch event inputs differ")
    else:
        raise ValueError("unregistered hosted event")

def integrity(wanted):
    require(HEX64.fullmatch(wanted) and A.digest(HERE/"manifest.json")==wanted,"judge manifest")
    files=A.read(HERE/"manifest.json")["package_files"]
    names={p.relative_to(HERE).as_posix() for p in HERE.rglob("*") if p.is_file()}
    require(names==set(files)|{"manifest.json"},"exact judge member set")
    for n,info in files.items(): A.check_bytes(HERE/n,info)
    return list(files)+["manifest.json"]

def git_bytes(repo,revision,path):return A.git(repo,"show",revision+":"+path)

def locked_checkout(args,repo,table,members):
    require(HEX40.fullmatch(args.commit) and HEX40.fullmatch(args.registration_commit) and
            HEX64.fullmatch(args.registration_sha256),"full Git and SHA-256 identities")
    require(args.commit==os.environ.get("GITHUB_SHA") and os.environ.get("GITHUB_ACTIONS")=="true"
            and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and str(os.environ.get("GITHUB_RUN_ID") or "").isdigit(),
            "first hosted invocation")
    event=os.environ.get("GITHUB_EVENT_NAME"); ref=os.environ.get("GITHUB_REF","")
    trigger(event,ref,args.commit,args.registration_commit,args.registration_sha256,A.read(os.environ["GITHUB_EVENT_PATH"]))
    require(HERE==repo/A.PACKAGE and A.git(repo,"rev-parse","HEAD").decode().strip()==args.commit,
            "exact checkout and package")
    require(args.commit!=args.registration_commit,"the attempt registration must precede the payload")
    A.git(repo,"merge-base","--is-ancestor",args.registration_commit,args.commit)
    path=A.ATTEMPT
    registration=git_bytes(repo,args.registration_commit,path)
    require(A.sha(registration)==args.registration_sha256 and (repo/path).read_bytes()==registration,"attempt registration")
    seal=json.loads(registration,object_pairs_hook=A.pairs)
    require(seal.get("schema")==1 and seal.get("kind")=="single original first-three stock attempt"
            and isinstance(seal.get("attempt_id"),str) and re.fullmatch(r"[A-Za-z0-9-]{1,80}",seal["attempt_id"])
            and seal.get("preparation_registration_sha256")==table["preparation_registration_sha256"]
            and seal.get("judge_manifest_sha256")==args.expected_manifest
            and seal.get("workflow_sha256")==A.digest(repo/A.WORKFLOW)
            and seal.get("allowed_write_files")==PAYLOADS and seal.get("cases")==list(A.CASES)
            and seal.get("limits")==LIMITS and seal.get("stock_archive_sha256")==STOCK_SHA
            and seal.get("launch_event")==event,
            "separate attempt original statement, scope, release, resource and workflow seal")
    tracked=[A.PACKAGE+"/"+s for s in members]+[A.WORKFLOW,A.ATTEMPT, A.SYNTHETIC+"/manifest.json"]
    tracked+=list(table["registered_shared"])+[v["input"]["relative_path"] for v in table["cases"].values()]
    tracked+=[A.SYNTHETIC+"/"+v for v in table["synthetic_reuse"]]
    unique=sorted(set(tracked))
    require(not A.git(repo,"ls-tree","-r","--name-only",args.registration_commit,"--",A.PAYLOAD),
            "registration already contains original candidate files")
    changed={s for s in A.git(repo,"diff","--name-only","-z",args.registration_commit,args.commit).decode().split("\0") if s}
    require(changed==set(PAYLOADS),"only the three registered proof files may change between registration and score")
    for n in unique:
        raw=(repo/n).read_bytes()
        require(raw==git_bytes(repo,args.commit,n)==git_bytes(repo,args.registration_commit,n),
                "immutable judge/authority/support file "+n)
    require({f.relative_to(repo).as_posix() for f in (repo/A.PAYLOAD).rglob("*") if f.is_file()}==set(PAYLOADS),
            "payload directory membership")
    identities={}
    for n in PAYLOADS:
        f=repo/n; require(f.is_file() and not f.is_symlink() and 0<f.stat().st_size<=1048576,"proof payload bytes")
        b=f.read_bytes();require(b==git_bytes(repo,args.commit,n),"tracked proof payload")
        identities[n]=A.sha(b)
    return {"science_commit":args.commit,"registration_commit":args.registration_commit,"registration_sha256":args.registration_sha256,
            "attempt_id":seal["attempt_id"],"workflow_sha256":seal["workflow_sha256"],"judge_manifest_sha256":args.expected_manifest,
            "payloads":identities,"retained_source_commit":table["source_commit"],"event":event,"ref":ref}

def run_native(args,repo,root,cases,table,members,begin,status):
    require(platform.system()=="Linux" and platform.machine()=="x86_64" and Path("/proc/self/stat").is_file(),
            "native campaign requires the registered hosted x86-64 Linux runner")
    require(args.archive and args.stock_root and args.commit and args.registration_commit and args.registration_sha256,
            "complete hosted inputs")
    host=locked_checkout(args,repo,table,members)
    require(A.digest(args.archive)==STOCK_SHA and not args.stock_root.exists()
            and not args.stock_root.is_relative_to(root) and not args.stock_root.is_relative_to(repo),
            "official archive and new external supplier root")
    require(begin<=time.monotonic()<begin+LIMITS["campaign_seconds"],"campaign clock")
    sysres=A.module(repo/A.SYNTHETIC/"resources.py")
    oldread=A.module(repo/A.SYNTHETIC/"readback.py")
    proof=local("proof_interface")
    reader=local("observations")
    tracer=local("finite_trace")
    args.stock_root.mkdir(mode=0o700)
    home=root/"scratch";home.mkdir()
    env={"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C","TZ":"UTC","HOME":str(home),"TMPDIR":str(home)}
    evidence_root=root.parent
    require({q.name for q in evidence_root.iterdir()}=={root.name,"host.txt","registration.json"},
            "dedicated retained evidence root")
    charged=sysres.Campaign(evidence_root,begin,LIMITS,env,A.digest)
    status["commands"]=charged.commands
    stock=args.stock_root/"lean-4.34.1-linux"
    anchors=["bin/lean","bin/leanchecker","src/lean/LeanChecker.lean","src/lean/Lean/Replay.lean","src/lean/Lean/Environment.lean"]
    charged.run("extract-official",["/usr/bin/tar","--zstd","--no-same-owner","-xf",args.archive,"-C",args.stock_root],home)
    lean=stock/"bin/lean";checker=stock/"bin/leanchecker"
    env["PATH"]=str(stock/"bin")+os.pathsep+os.defpath
    ver=charged.run("stock-version",[lean,"--version"],home,mode="text").read_text().strip()
    rev=charged.run("stock-source-revision",[lean,"--githash"],home,mode="text").read_text().strip()
    require(rev==STOCK_GIT and ver.startswith("Lean (version "+STOCK_VERSION+","),"stock release identity")
    host.update(stock_git=rev,version=ver,archive_sha256=STOCK_SHA,anchors={n:A.digest(stock/n) for n in anchors},
                host_release=platform.release(),run_id=os.environ["GITHUB_RUN_ID"])
    A.write(root/"inputs.json",host)
    def workspace(where):
        dest=where/"modules";dest.mkdir()
        env["LEAN_PATH"]=str(dest)
        return dest,{}
    def build(case,mod,src,objects,known,mode="silent"):
        obj=objects/(mod+".olean")
        require(not obj.exists() and (src/(mod+".lean")).is_file(),"once-only module write")
        stream=charged.run(case+"-compile-"+mod,[lean,"-DwarningAsError=true","-R",src,"-o",obj,mod+".lean"],src,mode=mode)
        require(obj.is_file() and not obj.is_symlink() and obj.stat().st_size>0,"new compiled module")
        known[obj.name]=A.digest(obj)
        return stream
    def fresh(case,mod,src,objects,known):
        require(known.get(mod+".olean")==A.digest(objects/(mod+".olean")),"fresh object identity")
        charged.run(case+"-fresh-"+mod,[checker,"--fresh",mod],src)
    controls=root/"artificial-controls";controls.mkdir()
    s=controls/"sources";s.mkdir();plan,sources=A.materialize_controls(repo,s)
    for name,text in (("TraceCode",tracer.CODE),("ArtificialTrace",tracer.CONTROL)):
        f=s/(name+".lean"); f.write_text(text); sources[f.name]=A.digest(f)
    charged.stage="artificial positive and false controls"
    objects,known=workspace(controls)
    pos=plan["stages"][0]
    for n in pos["compile"]:build("controls",n,s,objects,known)
    for n in pos["fresh"]:fresh("controls",n,s,objects,known)
    build("controls","TraceCode",s,objects,known)
    fresh("controls","TraceCode",s,objects,known)
    artificial=build("controls","ArtificialTrace",s,objects,known,"text")
    A.write(controls/"reduction-control.json",tracer.read_control(artificial))
    refusal={}
    for n in plan["stages"][1]["refuse"]:
        out=charged.run("controls-refuse-"+n,[lean,"--json","-DwarningAsError=true","-R",s,"-o",objects/(n+".olean"),n+".lean"],
                        s,mode="diagnostic",expected=1)
        require(not (objects/(n+".olean")).exists(),"refused scientific control produced object")
        refusal[n]=oldread.verify_negative(n,out,plan["refusal_diagnostics"][n])
        A.write(controls/"refusals.json",refusal)
    require(A.tree_hashes(objects)==known and A.tree_hashes(s)==sources,"synthetic object or source membership")
    A.write(controls/"accepted.json",{"positive_fresh":pos["fresh"],"qualified_refusals":list(refusal),"objects":known})
    for case,row in cases.items():
        where=root/case
        status["active_case"]=case;charged.stage=case
        src=where/"sources";tmpl=where/"templates"
        before=len(charged.commands)
        try:
            payload=A.read(repo/(A.PAYLOAD+"/"+case+".json"))
            templates={n[:-8]:(tmpl/n).read_text() for n in row["templates"]}
            ordered={n:templates[n] for n in ["OriginalStaticGroup"+format(i,"02d") for i in range(11)]
                +["OriginalStatic","OriginalDynamic","OriginalPredicates","OriginalFinite"]}
            built=proof.fill(ordered,payload,row["slots"])
            for n,t in built.items(): (src/(n+".lean")).write_text(t)
            bound=A.tree_hashes(src);A.write(where/"proof-source-identities.json",bound)
            for path in src.iterdir(): path.chmod(0o444)
            objects,known=workspace(where)
            order=["W02Semantics","ProjectionCore","ProjectionReification","TraceCode","OriginalLiteral","OriginalPrefix","OriginalContract",
                   *ordered,"OriginalConsumer"]
            for n in order:
                build(case,n,src,objects,known)
                fresh(case,n,src,objects,known)
            trace=build(case,"OriginalTrace",src,objects,known,"text")
            trace_result=tracer.read_original(case,trace)
            require(trace_result["projected_count"]==row["finite_combinations"],"all registered coordinates")
            A.write(where/"finite-ordered-output.json",trace_result)
            axes=build(case,"OriginalAxioms",src,objects,known,"text")
            terms=build(case,"OriginalTerms",src,objects,known,"text")
            observed=reader.read_records(terms,axes,row,oldread,ALLOWED)
            require(observed["checked"]==len(row["targets"]) and A.tree_hashes(src)==bound and
                    A.tree_hashes(objects)==known,"complete original source, object, and declaration inventory")
            A.write(where/"readback.json",observed);A.write(where/"object-identities.json",known)
            res={"status":"case predicate passed awaiting final custody","observed_theorems":observed["checked"],
                 "fresh_modules":order,"finite_combinations":row["finite_combinations"]}
        except (ValueError,RuntimeError) as exc:
            res={"status":"failed registered case","error":str(exc)}
            A.write(where/"terminal.json",res);status["cases"][case]=res
            if (len(charged.commands)>before and charged.commands[-1]["stop"]) or time.monotonic()-begin>=LIMITS["campaign_seconds"]:
                raise
        A.write(where/"terminal.json",res);status["cases"][case]=res
        A.write(root/"progress.json",status)
    require(host["anchors"]=={n:A.digest(stock/n) for n in anchors} and
            host["payloads"]==locked_checkout(args,repo,table,members)["payloads"],"post-run tool or checkout drift")
    require(time.monotonic()-begin<=LIMITS["campaign_seconds"] and sysres.retained_bytes(evidence_root)<LIMITS["retained_bytes"],
            "total resource envelope")
    A.write(root/"final-custody.json",{"postrun_release_anchors":host["anchors"],"postrun_payloads":host["payloads"],
            "workflow_sha256":host["workflow_sha256"],"retained_bytes_before_terminal":sysres.retained_bytes(evidence_root)})
    for case,item in status["cases"].items():
        if item["status"]=="case predicate passed awaiting final custody":
            item["status"]="accepted exact registered case"
            A.write(root/case/"terminal.json",item)
    require(all(v["status"]=="accepted exact registered case" for v in status["cases"].values()),
            "one or more registered cases failed")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    m=p.add_mutually_exclusive_group(required=True);m.add_argument("--check-sources",action="store_true");m.add_argument("--native",action="store_true")
    p.add_argument("--repository",type=Path,default=HERE.parents[2]);p.add_argument("--output",type=Path,required=True)
    p.add_argument("--expected-manifest",required=True)
    p.add_argument("--archive",type=Path);p.add_argument("--stock-root",type=Path)
    p.add_argument("--commit");p.add_argument("--registration-commit");p.add_argument("--registration-sha256")
    p.add_argument("--started",type=float)
    args=p.parse_args();repo=args.repository.resolve();root=args.output.resolve()
    require(not root.exists() and not root.is_relative_to(repo) and not root.is_relative_to(HERE),
            "receipt root must be fresh and outside the package and source repository")
    root.mkdir(mode=0o700,parents=False)
    status={"status":"started","active_case":None,"cases":{},"allowed_candidate_writes":PAYLOADS}
    begin=args.started if args.started is not None else time.monotonic()
    try:
        members=integrity(args.expected_manifest)
        table=A.read(HERE/"bindings.json")
        cases=A.collect(repo,root)
        require(A.preparation_identity(cases)==A.read(HERE/"generated.json"),"generated source, slots, targets or consumer drift")
        print(json.dumps({"allowed_candidate_writes":PAYLOADS,"template_source_bound":list(cases)}),flush=True)
        if args.native:
            require(args.started is not None,"campaign time begins before checkout and provisioning")
            run_native(args,repo,root,cases,table,members,begin,status)
            status["status"]="all three registered predicates accepted"
        else:
            status.update(status="three structural source transcriptions only",original_assertion_evaluations=0,
                          native_calls=0,original_candidate_payloads_opened=0)
        return 0
    except Exception as exc:
        status.update(status="failed",error=type(exc).__name__+": "+str(exc));return 1
    finally:
        status["elapsed_seconds"]=time.monotonic()-begin
        A.write(root/"terminal.json",status)
        if args.native and "commands" in status:
            retained=sum(os.stat(Path(d)/f,follow_symlinks=False).st_size
                         for d,_,files in os.walk(root.parent) for f in files)
            if retained>LIMITS["retained_bytes"] or status["elapsed_seconds"]>LIMITS["campaign_seconds"]:
                status.update(status="failed final campaign resource boundary")
                A.write(root/"terminal.json",status)
                raise RuntimeError("final campaign resource boundary")

if __name__=="__main__":sys.exit(main())

