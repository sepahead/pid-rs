"""Score one registered, original-free Linux calibration and retain each terminal outcome."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("index_common", HERE/"common.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)

def lock(args, repo):
    env = os.environ
    C.require(env.get("GITHUB_ACTIONS") == "true" and env.get("GITHUB_REPOSITORY") == "sepahead/pid-rs"
              and env.get("GITHUB_EVENT_NAME") == "push" and env.get("GITHUB_RUN_ATTEMPT") == "1"
              and env.get("GITHUB_RUN_ID", "").isdigit(), "first hosted run only")
    C.require(C.re.fullmatch("[0-9a-f]{40}", args.commit) and C.re.fullmatch("[0-9a-f]{40}", args.parent)
              and C.re.fullmatch("[0-9a-f]{64}", args.register), "externally bound commits and registration digest")
    ref = "refs/heads/review/index-family-control/"+args.parent+"-"+args.register
    event = C.read(Path(env["GITHUB_EVENT_PATH"]))
    C.require(env["GITHUB_REF"] == event.get("ref") == ref and env["GITHUB_SHA"] == event.get("after") == args.commit
              and event.get("created") is True and event.get("deleted") is False and event.get("before") == "0"*40,
              "first creation of the dedicated registration ref")
    C.require(C.HERE == repo/C.PACKAGE and C.git(repo,"rev-parse","HEAD").decode().strip() == args.commit and
              C.git(repo,"rev-list","--parents","-n","1",args.commit).decode().strip() == args.commit+" "+args.parent,
              "single direct child and correct checkout")
    C.git(repo,"merge-base","--is-ancestor",C.BASE,args.parent)
    manifest = C.require_manifest(args.manifest)
    common = C.reuse(repo)
    for f in [C.PACKAGE+"/"+s for s in [*manifest,"manifest.json"]]+[C.REGISTER,C.WORKFLOW,*common]:
        C.require((repo/f).read_bytes() == C.git(repo,"show",args.parent+":"+f) == C.git(repo,"show",args.commit+":"+f),
                  "frozen registration member "+f)
    delta=C.git(repo,"diff","--name-only","-z",args.parent,args.commit).split(b"\0")
    C.require(delta == [C.PAYLOAD.encode(), b""] and not C.git(repo,"ls-tree",args.parent,"--",C.PAYLOAD),
              "only the one new artificial input")
    f=repo/C.PAYLOAD
    C.require(C.git(repo,"ls-tree",args.commit,"--",C.PAYLOAD).decode().startswith("100644 blob ")
              and f.read_bytes()==C.git(repo,"show",args.commit+":"+C.PAYLOAD), "ordinary tracked artificial source")
    reg=C.read(repo/C.REGISTER)
    plan=C.read(HERE/"plan.json")
    C.require(C.digest(repo/C.REGISTER) == args.register and reg["attempt"] == C.ATTEMPT
              and reg["workflow_sha256"] == C.digest(repo/C.WORKFLOW) and reg["judge_manifest"]==args.manifest
              and reg["write_paths"]==[C.PAYLOAD] and reg["submission"]==C.info(f)
              and reg["stock_archive"]==C.STOCK and reg["limits"]==plan["limits"], "calibration registration")
    sources=C.fixed_sources(repo,C.read(f))
    C.require({n:hashlib.sha256(b).hexdigest() for n,b in sources.items()}==reg["materialized_sources"],
              "exact assembled artificial units")
    return reg,sources

def native(args):
    repo=Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    root=args.output.resolve()
    C.require(not root.exists() and not root.is_relative_to(repo) and not args.stock.exists()
              and not args.stock.is_relative_to(root), "new isolated paths")
    root.mkdir()
    status={"status":"started","attempt":C.ATTEMPT}
    try:
        reg,sources=lock(args,repo)
        (root/"registration.json").write_bytes((repo/C.REGISTER).read_bytes())
        C.require(platform.system()=="Linux" and platform.machine()=="x86_64" and args.archive.is_file()
                  and C.digest(args.archive)==C.STOCK, "stock archive and host")
        plan=C.read(HERE/"plan.json")
        C.require(args.started<=time.monotonic()<args.started+plan["limits"]["campaign_seconds"],"campaign clock")
        native_resource=C.module(repo/C.OLD/"native_resources.py")
        schedule=C.module(repo/C.OLD/"schedule.py")
        affinity=schedule.bind_one_cpu()
        src=root/"sources"; src.mkdir()
        for n,b in sources.items():
            (src/n).write_bytes(b)
            (src/n).chmod(0o444)
        expected=C.member_info(src)
        scratch=root/"scratch"; scratch.mkdir()
        obj=root/"objects"; obj.mkdir()
        env={"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C","TZ":"UTC","HOME":str(scratch),
             "TMPDIR":str(scratch),"LEAN_PATH":str(obj)}
        charged=native_resource.Campaign(root,args.started,plan["limits"],env,C.digest)
        charged.stage="invented finite-index qualification"
        args.stock.mkdir(mode=0o700)
        charged.run("extract-official",["/usr/bin/tar","--zstd","--no-same-owner","-xf",args.archive,"-C",args.stock],scratch)
        release=args.stock/"lean-4.34.1-linux"
        lean=release/"bin/lean"; checker=release/"bin/leanchecker"
        env["PATH"]=str(release/"bin")+os.pathsep+os.defpath
        version=charged.run("stock-version",[lean,"--version"],scratch,"text").read_text().strip()
        revision=charged.run("stock-commit",[lean,"--githash"],scratch,"text").read_text().strip()
        C.require(version.startswith("Lean (version 4.34.1,") and revision==C.STOCK_GIT,"stock version/commit")
        anchors={x:C.digest(release/x) for x in C.ANCHORS}
        C.require(all(anchors[k]==v for k,v in reg["stock_source_anchors"].items()),"verified stock source files")
        known={}; stages=[]
        def stage(kind,n):
            C.require(C.member_info(src)==expected and C.member_info(obj)==known,"materialized input drift at "+n)
            imports=[line.split()[1] for line in (src/(n+".lean")).read_text().splitlines() if line.startswith("import ")]
            local={d+".olean":known[d+".olean"] for d in imports if d+".lean" in sources}
            stages.append({"kind":kind,"module":n,"source":expected[n+".lean"],"local_imports":local,"preceding":dict(known)})
            C.write(root/"stages.json",stages)
        def compile_module(kind,n,mode="silent",code=0):
            stage(kind,n)
            file=obj/(n+".olean")
            C.require(not file.exists(),"new ordinary object")
            cmd=[lean]+(["--json"] if code else [])+["-DwarningAsError=true","-R",src,"-o",file,n+".lean"]
            charged.run(kind+"-"+n,cmd,src,mode,code)
            if code:
                C.require(not file.exists(),"refused source wrote an object")
            else:
                known[file.name]=C.info(file)
        for n in plan["ordinary"]:
            compile_module("compile",n)
            stage("fresh",n)
            charged.run("fresh-"+n,[checker,"--fresh",n],src)
        for n in plan["observers"]:
            compile_module("inspect",n,"text")
        for n in plan["refusals"]:
            compile_module("refuse",n,"diagnostic",1)
        C.require([row["tag"] for row in charged.commands]==list(C.expected_commands()),"complete native command sequence")
        observed=C.inspect(repo,lambda n:root/"commands"/n/"stdout")
        C.write(root/"observed.json",observed)
        C.require(C.member_info(src)==expected and C.member_info(obj)==known and
                  {x:C.digest(release/x) for x in C.ANCHORS}==anchors and sorted(os.sched_getaffinity(0))==affinity["during_native"],
                  "terminal source, object, stock or CPU drift")
        C.require(lock(args,repo)[0]==reg and C.digest(args.archive)==C.STOCK,"terminal registration and archive binding")
        status.update(status="accepted invented calibration",registration_commit=args.parent,commit=args.commit,
                      registration_sha256=args.register,run=int(os.environ["GITHUB_RUN_ID"]),run_attempt=1,
                      stock=revision,stock_version=version,archive_sha256=C.STOCK,stock_anchors=anchors,
                      limits=plan["limits"],affinity=affinity,sources=expected,objects=known,command_tags=list(C.expected_commands()),
                      observed=C.info(root/"observed.json"),stage_file=C.info(root/"stages.json"),original_evaluations=0)
    except Exception as error:
        status.update(status="failed invented calibration",error=type(error).__name__+": "+str(error))
    status["elapsed_seconds"]=time.monotonic()-args.started
    C.write(root/"terminal.json",status)
    limits=C.read(HERE/"plan.json")["limits"]
    if status["elapsed_seconds"]>limits["campaign_seconds"] or sum(p.stat().st_size for p in root.rglob("*") if p.is_file())>limits["retained_bytes"]:
        status["status"]="failed final time or retained storage"
        C.write(root/"terminal.json",status)
    return 0 if status["status"]=="accepted invented calibration" else 1

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("commit","parent","register","manifest"):
        parser.add_argument("--"+key,required=True)
    for key in ("archive","stock","output"):
        parser.add_argument("--"+key,required=True,type=Path)
    parser.add_argument("--started",type=float,required=True)
    sys.exit(native(parser.parse_args()))
