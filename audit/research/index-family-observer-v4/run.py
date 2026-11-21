"""Execute the single externally registered, artificial Linux run. Preserve every reached native command."""
import argparse
import importlib.util
import os
from pathlib import Path
import platform
import sys
import time

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("observer_support", HERE/"support.py")
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def bind_push(args, repo):
    env=os.environ
    S.require(env.get("GITHUB_ACTIONS") == "true" and env.get("GITHUB_REPOSITORY") == "sepahead/pid-rs" and
              env.get("GITHUB_EVENT_NAME") == "push" and env.get("GITHUB_RUN_ATTEMPT") == "1" and
              env.get("GITHUB_RUN_ID","").isdigit(), "first hosted job only")
    event=S.read(Path(env["GITHUB_EVENT_PATH"]))
    ref="refs/heads/"+S.REF_PREFIX+args.parent+"-"+args.register
    S.require(env["GITHUB_REF"] == event.get("ref") == ref and env["GITHUB_SHA"] == event.get("after") == args.commit and
              event.get("created") is True and event.get("deleted") is False and event.get("before") == "0"*40 and
              S.git(repo,"rev-parse","HEAD").decode().strip() == args.commit, "first creation of the exact registered ref")
    reg,sources=S.bound_sources(repo,args.parent,args.commit,args.register,args.manifest)
    S.require((repo/S.PAYLOAD).read_bytes() == S.git(repo,"show",args.commit+":"+S.PAYLOAD), "working submission")
    return reg,sources


def native(args):
    repo=Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    result=args.output.resolve()
    evidence=result.parent
    S.require(not result.exists() and not result.is_relative_to(repo) and not args.stock.exists() and
              not args.stock.is_relative_to(evidence) and not args.archive.is_relative_to(evidence) and
              {p.name for p in evidence.iterdir()} == {"launch.json"}, "fresh separated evidence, release and scratch")
    result.mkdir()
    tag="bind and provision"
    phase="setup"
    intervals=[]

    def dispatch(tag, argv, cwd, style="silent", expected=0):
        nonlocal phase
        phase="invoke"
        begin=time.monotonic()-args.started
        try:
            stream=charged.run(tag,argv,cwd,style,expected)
        finally:
            intervals.append({"tag":tag,"begin":begin,"end":time.monotonic()-args.started})
        phase="after-command"
        return stream

    def failed(reason):
        return {"status":S.FAILED,"attempt":S.ATTEMPT,"original_evaluations":0,
                "stage":tag,"phase":phase,"error":reason,"dispatch_intervals":intervals}

    try:
        reg,sources=bind_push(args,repo)
        expected_launch={"commit":args.commit,"registration_commit":args.parent,"registration_sha256":args.register,
                         "run":int(os.environ["GITHUB_RUN_ID"]),"attempt":1,
                         "execution":{"workspace":str(repo),"runner_temp":str(Path(os.environ["RUNNER_TEMP"]).resolve()),
                                      "python":str(Path(sys.executable).resolve())}}
        S.require(S.read(evidence/"launch.json") == expected_launch, "host launch and native binding")
        temp=Path(expected_launch["execution"]["runner_temp"])
        S.require(args.archive==temp/"index-observer-v4-release.tar.zst" and args.stock==temp/"index-observer-v4-stock" and
                  result==temp/"index-observer-v4-evidence/result","fixed workflow directories")
        (result/"registration.json").write_bytes((repo/S.REGISTER).read_bytes())
        S.require(platform.system()=="Linux" and platform.machine()=="x86_64" and args.archive.is_file() and
                  S.digest(args.archive)==S.STOCK and args.started <= time.monotonic() < args.started+2700, "stock, host and campaign clock")
        native_provider=S.load(repo/S.V1.OLD/"native_resources.py")
        old_scheduler=S.load(repo/S.V1.OLD/"schedule.py")
        affinity=old_scheduler.bind_one_cpu()
        src=result/"sources"; obj=result/"objects"; scratch=result/"scratch"
        for folder in (src,obj,scratch):folder.mkdir()
        for name,content in sources.items():
            S.require(S.tree_bytes(evidence)+len(content)<=reg["limits"]["retained_bytes"],"cumulative source bytes")
            f=src/name; f.write_bytes(content);f.chmod(0o444)
        source_info=S.members(src)
        env={"PATH":"/usr/bin:/bin","LC_ALL":"C","LANG":"C","TZ":"UTC","HOME":str(scratch),"TMPDIR":str(scratch),"LEAN_PATH":str(obj)}
        charged=native_provider.Campaign(result,args.started,reg["limits"],env,S.digest)
        # Command files stay in result/commands. The resource sampler counts the full uploaded evidence root.
        charged.root=evidence
        charged.stage=S.STAGE
        args.stock.mkdir(mode=0o700)
        tag="extract-official"
        dispatch(tag,["/usr/bin/tar","--zstd","--no-same-owner","-xf",args.archive,"-C",args.stock],scratch)
        release=args.stock/"lean-4.34.1-linux";lean=release/"bin/lean";checker=release/"bin/leanchecker"
        env["PATH"]=str(release/"bin")+os.pathsep+os.defpath
        tag="stock-version"
        version=dispatch(tag,[lean,"--version"],scratch,"text").read_text().strip()
        S.require(version==S.STOCK_VERSION,"reported stock version")
        tag="stock-commit"
        stock=dispatch(tag,[lean,"--githash"],scratch,"text").read_text().strip()
        S.require(version.startswith("Lean (version 4.34.1,") and stock==S.STOCK_GIT, "reported native version")
        anchors={k:S.digest(release/k) for k in S.ANCHORS}
        S.require(all(anchors[k]==v for k,v in reg["stock_source_anchors"].items()),"stock release source anchors")
        stages=[];known={}
        commands=S.schedule(repo)
        for tag,(code,style) in list(commands.items())[3:]:
            if tag==S.POST:
                continue
            phase="before-command"
            kind,n=tag.split("-",1)
            S.require(S.members(src)==source_info and S.members(obj)==known,"materialized input drift at "+tag)
            imports=[line.split()[1] for line in (src/(n+".lean")).read_text().splitlines() if line.startswith("import ")]
            local={m+".olean":known[m+".olean"] for m in imports if m+".lean" in sources}
            stages.append({"kind":kind,"module":n,"source":source_info[n+".lean"],"local_imports":local,"preceding":dict(known)})
            S.write_counted(evidence,result/"stages.json",stages)
            if kind=="fresh":
                dispatch(tag,[checker,"--fresh",n],src)
                continue
            out=obj/(n+".olean")
            S.require(not out.exists(),"fresh ordinary object "+n)
            args_lean=[lean]+(["--json"] if code else [])+["-DwarningAsError=true","-R",src,"-o",out,n+".lean"]
            dispatch(tag,args_lean,src,style,code)
            if code:
                S.require(not out.exists(),"no object from a refused control")
            else:
                known[out.name]=S.info(out)
        # This separately supervised process inherits the same CPU and storage/time/RSS limits.
        tag=S.POST
        dispatch(tag,[Path(sys.executable).resolve(),"-I","-S","-B",HERE/"frames.py","--result",result],scratch)
        tag="final checks";phase="final"
        S.require([x["tag"] for x in charged.commands]==list(commands) and S.members(src)==source_info and S.members(obj)==known and
                  sorted(os.sched_getaffinity(0))==affinity["during_native"] and {k:S.digest(release/k) for k in S.ANCHORS}==anchors and
                  bind_push(args,repo)[0]==reg and S.digest(args.archive)==S.STOCK,"complete native and registered sources")
        files={p.relative_to(evidence).as_posix() for p in evidence.rglob("*") if p.is_file()}
        S.require(files==S.all_files(repo,sources)-{"result/terminal.json"},"complete 508 pre-terminal files")
        status=dict(status=S.ACCEPTED,attempt=S.ATTEMPT,original_evaluations=0,dispatch_intervals=intervals,commit=args.commit,registration_commit=args.parent,registration_sha256=args.register,
                      run=int(os.environ["GITHUB_RUN_ID"]),run_attempt=1,stock=stock,stock_version=version,archive_sha256=S.STOCK,
                      stock_anchors=anchors,affinity=affinity,limits=reg["limits"],sources=source_info,objects=known,
                      command_tags=list(commands),stages=S.info(result/"stages.json"),observed=S.info(result/"observed.json"),
                      frames=S.info(result/"term-shards.json"),joined=S.info(result/"joined-terms.stdout"))
    except Exception as error:
        status=failed(type(error).__name__+": "+str(error))
    elapsed=time.monotonic()-args.started
    if elapsed>=2700 and status["status"]==S.ACCEPTED:
        status=failed("shared campaign clock")
    status["elapsed_seconds"]=elapsed
    try:
        S.write_counted(evidence,result/"terminal.json",status,transient=False)
    except ValueError as error:
        if status["status"]==S.ACCEPTED:
            status=failed(str(error))
        status["elapsed_seconds"]=time.monotonic()-args.started
        S.write(result/"terminal.json",status)
        return 1
    if time.monotonic()-args.started>=2700 or S.tree_bytes(evidence)>S.SAFE_LIMITS["retained_bytes"]:
        if status["status"]==S.ACCEPTED:
            status=failed("final campaign time or cumulative evidence bytes")
            status["elapsed_seconds"]=time.monotonic()-args.started
            S.write(result/"terminal.json",status)
        return 1
    return 0 if status["status"]==S.ACCEPTED else 1


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ("commit","parent","register","manifest"):
        parser.add_argument("--"+key,required=True)
    for key in ("archive","stock","output"):
        parser.add_argument("--"+key,required=True,type=Path)
    parser.add_argument("--started",required=True,type=float)
    sys.exit(native(parser.parse_args()))
