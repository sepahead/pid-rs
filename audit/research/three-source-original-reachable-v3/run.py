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
schedule=local("schedule")
LIMITS=schedule.LIMITS
STOCK_VERSION="4.34.1"
STOCK_SHA="47bf4bbd78f70c2e9670598ab7124d92b6efb7330ff33e5fbb4030f6fd72e4e4"
STOCK_GIT="5045d0056413266e57c625dcd7c365b10e377c52"
ALLOWED=["Classical.choice","Quot.sound","propext"]
PAYLOADS=[A.PAYLOAD+"/"+c+".json" for c in A.CASES]
PUSH_REF=re.compile(r"refs/heads/review/original-reachable-v3/([0-9a-f]{40})-([0-9a-f]{64})\Z")

def trigger(event, ref, commit, registration, registration_hash, event_payload):
    require(event=="push","one first reserved push only")
    if event=="push":
        match=PUSH_REF.fullmatch(ref)
        require(match is not None and match.groups()==(registration,registration_hash),
                "registration identities must equal the complete reserved remote branch suffix")
        require(event_payload.get("ref")==ref and event_payload.get("after")==commit and
                event_payload.get("deleted") is False and event_payload.get("created") is True and
                event_payload.get("before")=="0"*40,"first creation of the uniquely reserved push ref")
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
    require(os.environ.get("GITHUB_REPOSITORY")=="sepahead/pid-rs","registered hosted repository")
    event=os.environ.get("GITHUB_EVENT_NAME"); ref=os.environ.get("GITHUB_REF","")
    trigger(event,ref,args.commit,args.registration_commit,args.registration_sha256,A.read(os.environ["GITHUB_EVENT_PATH"]))
    require(HERE==repo/A.PACKAGE and A.git(repo,"rev-parse","HEAD").decode().strip()==args.commit,
            "exact checkout and package")
    require(args.commit!=args.registration_commit,"the attempt registration must precede the payload")
    require(A.git(repo,"rev-list","--parents","-n","1",args.commit).decode().strip()==
            args.commit+" "+args.registration_commit,"direct child of the candidate-free registration")
    path=A.ATTEMPT
    registration=git_bytes(repo,args.registration_commit,path)
    require(A.sha(registration)==args.registration_sha256 and (repo/path).read_bytes()==registration,"attempt registration")
    seal=json.loads(registration,object_pairs_hook=A.pairs)
    require(seal.get("schema")==1 and seal.get("kind")=="single original assertion-reachable attempt v3"
            and isinstance(seal.get("attempt_id"),str) and re.fullmatch(r"[A-Za-z0-9-]{1,80}",seal["attempt_id"])
            and seal.get("preparation_registration_sha256")==table["preparation_registration_sha256"]
            and seal.get("judge_manifest_sha256")==args.expected_manifest
            and seal.get("workflow_sha256")==A.digest(repo/A.WORKFLOW)
            and seal.get("allowed_write_files")==PAYLOADS and seal.get("cases")==list(A.CASES)
            and seal.get("limits")==LIMITS and seal.get("schedule")==schedule.SCHEDULE
            and seal.get("stock_archive_sha256")==STOCK_SHA
            and seal.get("launch_event")==event,
            "separate attempt original statement, scope, release, resource and workflow seal")
    tracked=[A.PACKAGE+"/"+s for s in members]+[A.WORKFLOW,A.ATTEMPT, A.SYNTHETIC+"/manifest.json"]
    tracked+=list(table["registered_shared"])+[v["input"]["relative_path"] for v in table["cases"].values()]
    tracked+=[A.SYNTHETIC+"/"+v for v in table["synthetic_reuse"]]
    tracked+=table["external"]
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
        spec=A.git(repo,"ls-tree",args.commit,"--",n).decode().rstrip("\n")
        require(spec.startswith("100644 blob ") and spec.endswith("\t"+n),"ordinary tracked proof mode")
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
    sysres=local("native_resources")
    affinity=schedule.bind_one_cpu()
    host["native_cpu_affinity"]=affinity
    oldread=A.module(repo/A.SYNTHETIC/"readback.py")
    proof=A.module(repo/A.OLD/"proof_interface.py")
    reader=A.module(repo/A.OLD/"observations.py")
    tracer=A.module(repo/A.OLD/"finite_trace.py")
    corroborate=local("readback")
    accepted_sources={}
    stage_dir=root/"stage-inputs";stage_dir.mkdir()
    def input_receipt(case,mod,src,objects,known,kind):
        require(A.tree_hashes(objects)==known,"inter-stage exact import objects")
        trace=corroborate.inputs(A,src,mod,known,accepted_sources[src],kind,host["anchors"])
        A.write(stage_dir/(case+"-"+kind+"-"+mod+".json"),trace)
    args.stock_root.mkdir(mode=0o700)
    home=root/"scratch";home.mkdir()
    env={"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C","TZ":"UTC","HOME":str(home),"TMPDIR":str(home)}
    evidence_root=root.parent
    require({q.name for q in evidence_root.iterdir()}=={root.name,"host.txt","registration.json"},
            "dedicated retained evidence root")
    charged=sysres.Campaign(evidence_root,begin,dict(LIMITS,campaign_seconds=schedule.SCHEDULE["shared_setup_seconds"]),env,A.digest)
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
        input_receipt(case,mod,src,objects,known,"compile")
        stream=charged.run(case+"-compile-"+mod,[lean,"-DwarningAsError=true","-R",src,"-o",obj,mod+".lean"],src,mode=mode)
        require(obj.is_file() and not obj.is_symlink() and obj.stat().st_size>0,"new compiled module")
        known[obj.name]=A.digest(obj)
        return stream
    def fresh(case,mod,src,objects,known):
        require(known.get(mod+".olean")==A.digest(objects/(mod+".olean")),"fresh object identity")
        input_receipt(case,mod,src,objects,known,"fresh")
        charged.run(case+"-fresh-"+mod,[checker,"--fresh",mod],src)
    schedule.monitor_controls(A,sysres,root,begin,env,home,affinity["during_native"][0])
    controls=root/"artificial-controls";controls.mkdir()
    s=controls/"sources";s.mkdir();plan,sources=A.materialize_controls(repo,s)
    for name,text in (("TraceCode",tracer.CODE),("ArtificialTrace",tracer.CONTROL)):
        f=s/(name+".lean"); f.write_text(text); sources[f.name]=A.digest(f)
    accepted_sources[s]=sources
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
        input_receipt("controls",n,s,objects,known,"refuse")
        out=charged.run("controls-refuse-"+n,[lean,"--json","-DwarningAsError=true","-R",s,"-o",objects/(n+".olean"),n+".lean"],
                        s,mode="diagnostic",expected=1)
        require(not (objects/(n+".olean")).exists(),"refused scientific control produced object")
        refusal[n]=oldread.verify_negative(n,out,plan["refusal_diagnostics"][n])
        A.write(controls/"refusals.json",refusal)
    require(A.tree_hashes(objects)==known and A.tree_hashes(s)==sources,"synthetic object or source membership")
    A.write(controls/"accepted.json",{"positive_fresh":pos["fresh"],"qualified_refusals":list(refusal),"objects":known})
    def isolated(case,n,src,objects,known,payload,row,where):
        dest=where/"isolated-elaborations"/n
        dest.mkdir(parents=True)
        probes={}
        for slot,expected in row["individual_lemma_templates"][n].items():
            template=where/"isolated-templates"/n/(slot+".lean.in")
            require(A.digest(template)==expected,"isolated exact registered theorem "+slot)
            scientific=src/(n+".lean")
            text=template.read_text()
            marker="@@PROOF "+slot+"@@"
            require(text.count(marker)==1,"one stand-alone proof")
            candidate=proof.script(payload[slot])
            proposition=text.split(marker)[0].splitlines()[-1]
            require(scientific.read_text().count(proposition+"\n"+candidate+"\n")==1,
                    "same frozen statement and same filled proof in its scientific owner")
            here=dest/slot
            here.mkdir()
            unit=here/"One.lean"
            unit.write_text(text.replace(marker,candidate))
            unit.chmod(0o444)
            imports={k:v for k,v in known.items() if ("import "+k[:-6]+"\n") in text}
            require(imports and A.tree_hashes(objects)==known,"isolated preceding imports")
            audit={"slot":slot,"ordinary_owner":n,"registered_template":expected,
                   "same_full_module":A.digest(scientific),"isolated_source":A.digest(unit),
                   "imports":imports,"case_objects_before":dict(known),"stock_anchors":host["anchors"]}
            A.write(here/"input.json",audit)
            stream=charged.run(case+"-isolate-"+slot,[lean,"-DwarningAsError=true","-R",here,"One.lean"],
                               here,mode="text")
            found=oldread.verify_axioms(stream,[slot],set(ALLOWED))
            require(A.tree_hashes(objects)==known and not list(here.glob("*.olean")) and A.digest(unit)==audit["isolated_source"],
                    "isolated diagnostic cannot furnish a scientific import")
            probes.update(found)
            A.write(here/"result.json",{"observed_axioms":found[slot],"stdout_sha256":A.digest(stream)})
        return probes
    require(list(cases)==list(schedule.CASES),"registered sequential case order")
    shared_end=time.monotonic()-begin
    require(shared_end<=schedule.SCHEDULE["shared_setup_seconds"],"shared setup exceeded its reserved window")
    A.write(root/"shared-setup-clock.json",{"elapsed_seconds":shared_end,"schedule":schedule.SCHEDULE,
           "native_worker_affinity":affinity})
    for case,row in cases.items():
        where=root/case
        clock=schedule.window(case,begin,time.monotonic())
        charged.plan=dict(LIMITS,campaign_seconds=clock["deadline_s_since_campaign"])
        A.write(where/"case-window.json",clock)
        scratch=where/"scratch";scratch.mkdir()
        env["HOME"]=str(scratch);env["TMPDIR"]=str(scratch)
        objects=None;known={};bound=None
        failure=None
        status["active_case"]=case;charged.stage=case
        status["cases"][case]={"status":"started, no checked case result"}
        A.write(where/"terminal.json",status["cases"][case]);A.write(root/"progress.json",status)
        src=where/"sources";tmpl=where/"templates"
        before=len(charged.commands)
        try:
            payload=A.read(repo/(A.PAYLOAD+"/"+case+".json"))
            templates={n[:-8]:(tmpl/n).read_text() for n in row["templates"]}
            ordered={n:templates[n] for n in row["template_order"]}
            built=proof.fill(ordered,payload,row["slots"])
            for n,t in built.items(): (src/(n+".lean")).write_text(t)
            bound=A.tree_hashes(src);A.write(where/"proof-source-identities.json",bound)
            accepted_sources[src]=bound
            for path in src.iterdir(): path.chmod(0o444)
            objects,known=workspace(where)
            order=row["ordinary_order"]
            early={}
            per_lemma={}
            for n in order:
                names=row["compile_checkpoints"].get(n,[])
                if names:
                    per_lemma[n]=isolated(case,n,src,objects,known,payload,row,where)
                stream=build(case,n,src,objects,known,"text" if names else "silent")
                if names:
                    early[n]=oldread.verify_axioms(stream,names,set(ALLOWED))
                    A.write(where/"local-lemma-checkpoints.json",early)
                fresh(case,n,src,objects,known)
            trace=build(case,"OriginalTrace",src,objects,known,"text")
            trace_result=tracer.read_original(case,trace)
            require(trace_result["projected_count"]==row["finite_combinations"],"all registered coordinates")
            corroborate.finite_rows(case,trace_result)
            A.write(where/"finite-ordered-output.json",trace_result)
            axes=build(case,"OriginalAxioms",src,objects,known,"text")
            terms=build(case,"OriginalTerms",src,objects,known,"text")
            observed=reader.read_records(terms,axes,row,oldread,ALLOWED)
            corroborate.checkpoints_against_final(early,observed)
            corroborate.checkpoints_against_final(per_lemma,observed)
            observed["typed_direct_uses"]=corroborate.dependency_rows(terms,row,oldread,observed)
            require(observed["checked"]==len(row["targets"]) and A.tree_hashes(src)==bound and
                    A.tree_hashes(objects)==known,"complete original source, object, and declaration inventory")
            A.write(where/"readback.json",observed);A.write(where/"object-identities.json",known)
            require(time.monotonic()-begin<clock["deadline_s_since_campaign"],"case time during scientific readback")
            res={"status":"case predicate passed awaiting final custody","observed_theorems":observed["checked"],
                 "fresh_modules":order,"finite_combinations":row["finite_combinations"]}
        except Exception as exc:
            failure=exc
            res={"status":"failed registered case","error":type(exc).__name__+": "+str(exc)}
            A.write(where/"terminal.json",res);status["cases"][case]=res
            if not isinstance(exc,(ValueError,RuntimeError)):
                raise
        # Every completed case ends with its own source, module, process and shared-supplier custody.
        # Failed output bytes stay here. Only the next clean directory can supply its next case.
        try:
            snapshot=schedule.inventory(A,src,objects,known,failure is None,bound if bound is not None else row["sources"])
            require(A.tree_hashes(tmpl)==row["templates"],"case template identity at the transition")
            require({n:A.digest(stock/n) for n in anchors}==host["anchors"] and
                    locked_checkout(args,repo,table,members)["payloads"]==host["payloads"],"case transition shared supplier or inputs")
            require(sorted(os.sched_getaffinity(0))==affinity["during_native"],"single CPU affinity at the case transition")
        except Exception as error:
            res["scientific_stage_before_incomplete_custody"]=res["status"]
            res["status"]="shared transition failed, no case acceptance"
            res["shared_error"]=type(error).__name__+": "+str(error)
            A.write(where/"terminal.json",res);status["cases"][case]=res;A.write(root/"progress.json",status)
            raise
        count=len(charged.commands)-before
        last=charged.commands[-1] if count else None
        elapsed=time.monotonic()-begin
        if failure is None and elapsed>=clock["deadline_s_since_campaign"]:
            failure=RuntimeError("case time during case custody")
            res={"status":"failed registered case","error":str(failure)}
        disposition=schedule.continuation(clock,elapsed,sysres.retained_bytes(evidence_root),failure is not None,last,count)
        custody={"case":case,"clock":clock,"end_s_since_campaign":elapsed,"commands":count,"last":last,
                 "case_result":res["status"],"disposition":disposition,"source_and_objects":snapshot,
                 "stock_anchors":host["anchors"],"payloads":host["payloads"]}
        A.write(where/"case-transition.json",custody)
        res["transition_sha256"]=A.digest(where/"case-transition.json")
        A.write(where/"terminal.json",res);status["cases"][case]=res
        A.write(root/"progress.json",status)
        if not disposition.startswith("continue "):
            raise RuntimeError(disposition)
    charged.plan=LIMITS
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
    status={"status":"started","active_case":None,"cases":{k:{"status":"not started"} for k in A.CASES},"allowed_candidate_writes":PAYLOADS}
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
        if args.native:
            for case in A.CASES:
                target=root/case/"terminal.json"
                if target.parent.is_dir() and not target.exists(): A.write(target,status["cases"][case])
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
