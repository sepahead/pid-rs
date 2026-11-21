"""Read a completed public calibration archive and its GitHub run/job/artifact responses."""
import argparse
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("index_common",HERE/"common.py")
C=importlib.util.module_from_spec(s)
s.loader.exec_module(C)
JOB="Check all 83 positions on one Linux CPU"
MAX=1<<30

def extract(archive, destination):
    C.require(0 < archive.stat().st_size <= MAX, "compressed archive size")
    with zipfile.ZipFile(archive) as src:
        records=src.infolist()
        C.require(1 <= len(records) <= 550 and len(records)==len({p.filename for p in records}), "ZIP member set")
        C.require(sum(r.file_size for r in records)<=MAX,"retained ZIP bytes")
        for item in records:
            literal=item.filename.rstrip("/")
            parts=PurePosixPath(literal)
            C.require(parts.parts and literal==str(parts) and all(p not in (".","..") for p in parts.parts)
                      and not parts.is_absolute() and "\\" not in literal and not (item.flag_bits&1), "ordinary member name")
            mode=(item.external_attr>>16)&0xffff
            C.require(stat.S_IFMT(mode) in (0,stat.S_IFDIR,stat.S_IFREG),"regular ZIP content")
            dest=destination/parts
            if item.is_dir():
                dest.mkdir(parents=True,exist_ok=True)
            else:
                dest.parent.mkdir(parents=True,exist_ok=True)
                with src.open(item) as a, dest.open("xb") as b:
                    shutil.copyfileobj(a,b,1<<17)
                C.require(dest.stat().st_size==item.file_size,"ZIP member readback")

def match_remote(run,job,artifact,history,terminal,archive):
    head=terminal["commit"]; parent=terminal["registration_commit"]; reg=terminal["registration_sha256"]
    branch="review/index-family-control/"+parent+"-"+reg
    C.require(all(re.fullmatch("[0-9a-f]{40}",h) for h in (head,parent)) and re.fullmatch("[0-9a-f]{64}",reg),
              "complete remote identities")
    rid=run["id"]
    C.require(history["total_count"]==1 and type(history["workflow_runs"]) is list and len(history["workflow_runs"])==1,
              "unique available hosted run for the exact reserved ref")
    only=history["workflow_runs"][0]
    C.require(all(only[k]==run[k] for k in ("id","run_attempt","workflow_id","event","head_branch","head_sha","status","conclusion"))
              and only["repository"]["full_name"]=="sepahead/pid-rs","same sole run on the reserved ref")
    C.require(type(rid) is int and rid>0 and type(job["id"]) is int and job["id"]>0 and
              type(artifact["id"]) is int and artifact["id"]>0 and
              run["event"]=="push" and run["run_attempt"]==terminal["run_attempt"]==1 and
              run["repository"]["full_name"]=="sepahead/pid-rs" and run["head_repository"]["full_name"]=="sepahead/pid-rs" and
              run["path"]==C.WORKFLOW and run["head_branch"]==job["head_branch"]==branch and
              run["head_sha"]==job["head_sha"]==artifact["workflow_run"]["head_sha"]==head and
              rid==job["run_id"]==artifact["workflow_run"]["id"]==terminal["run"] and
              run["status"]==job["status"]=="completed" and run["conclusion"]==job["conclusion"]=="success"
              and job["name"]==JOB and job["run_attempt"]==1,"successful exact first hosted job")
    C.require(artifact["workflow_run"]["head_branch"]==branch and artifact["expired"] is False and
              artifact["workflow_run"]["repository_id"]==artifact["workflow_run"]["head_repository_id"]==run["repository"]["id"]
              and artifact["name"]==f"index-family-control-{head}-{rid}-1" and
              artifact["digest"]=="sha256:"+C.digest(archive) and artifact["size_in_bytes"]==archive.stat().st_size,
              "exact hosted artifact identity and ZIP bytes")
    return {"run":rid,"job":job["id"],"artifact":artifact["id"],"archive":C.info(archive),"branch":branch,
            "commit":head,"registration_commit":parent,"registration_sha256":reg}

def check_directory(root, repo):
    plan=C.read(HERE/"plan.json")
    terminal=C.read(root/"terminal.json")
    C.require(terminal["status"]=="accepted invented calibration" and terminal["attempt"]==C.ATTEMPT and
              terminal["original_evaluations"]==0 and terminal["archive_sha256"]==C.STOCK and terminal["stock"]==C.STOCK_GIT
              and terminal["stock_version"].startswith("Lean (version 4.34.1,") and terminal["limits"]==plan["limits"],
              "terminal native predicate")
    before=terminal["affinity"]["before"]; during=terminal["affinity"]["during_native"]
    C.require(type(before) is list and before==sorted(set(before)) and before and during==[before[0]]
              and type(terminal["elapsed_seconds"]) in (float,int) and 0<terminal["elapsed_seconds"]<=2700,"CPU and aggregate clock")
    C.require(set(terminal["stock_anchors"])==set(C.ANCHORS)
              and all(re.fullmatch("[0-9a-f]{64}",v) for v in terminal["stock_anchors"].values()),"stock anchor membership")
    reg=C.read(root/"registration.json")
    C.require(reg["attempt"]==C.ATTEMPT and C.digest(root/"registration.json")==terminal["registration_sha256"]
              and reg["stock_archive"]==C.STOCK and reg["limits"]==plan["limits"]
              and reg["write_paths"]==[C.PAYLOAD] and reg["workflow_sha256"]==C.digest(repo/C.WORKFLOW),"archived registration")
    C.require(C.require_manifest(reg["judge_manifest"]) and C.reuse(repo),"source and reusable judges")
    for key, expected in reg["stock_source_anchors"].items():
        C.require(terminal["stock_anchors"][key]==expected,"stock source mismatch")
    source=C.member_info(root/"sources")
    C.require(source==terminal["sources"] and reg["materialized_sources"]=={k:v["sha256"] for k,v in source.items()},
              "every materialized source")
    source_at_commit=C.git(repo,"show",terminal["commit"]+":"+C.PAYLOAD)
    C.require(len(source_at_commit)==reg["submission"]["bytes"] and C.hashlib.sha256(source_at_commit).hexdigest()==reg["submission"]["sha256"]
              and C.git(repo,"rev-list","--parents","-n","1",terminal["commit"]).decode().strip()==terminal["commit"]+" "+terminal["registration_commit"]
              and C.git(repo,"show",terminal["registration_commit"]+":"+C.REGISTER)==(root/"registration.json").read_bytes(),
              "source archive agrees with retained Git objects")
    sources=C.fixed_sources(repo,json.loads(source_at_commit,object_pairs_hook=C.pairs))
    C.require(set(sources)==set(source) and all(v==(root/"sources"/k).read_bytes() for k,v in sources.items()),"assembled positive and refusal sources")
    commands=C.expected_commands()
    C.require(terminal["command_tags"]==list(commands) and {p.name for p in (root/"commands").iterdir()}==set(commands),
              "exact native command coverage")
    suffixes={k+".olean" for k in plan["ordinary"]+plan["observers"]}
    objects=C.member_info(root/"objects")
    C.require(set(objects)==suffixes and terminal["objects"]==objects,"fresh-complete successful objects only")
    stages=C.read(root/"stages.json")
    C.require(C.info(root/"stages.json")==terminal["stage_file"],"stage receipt")
    known={}; step=0; last=0
    for tag,(expected,style) in commands.items():
        folder=root/"commands"/tag
        C.require({f.name for f in folder.iterdir()}=={"stdout","stderr","result.json"},"command files")
        row=C.read(folder/"result.json")
        C.require(row["tag"]==tag and row["exit"]==expected and row["stop"] is None
                  and row["post_group_absent"] is True and row["residual_after_wait4"] is False
                  and row["stage"]=="invented finite-index qualification","native command completion "+tag)
        for key in ("max_observed_group_rss_bytes","direct_wait4_maxrss_bytes","retained_before_receipt_bytes",
                    "group_rss_sample_count","native_process_group"):
            C.require(type(row[key]) is int and row[key]>=0,"integer resource field")
        C.require(row["native_process_group"]>0 and max(row["direct_wait4_maxrss_bytes"],row["max_observed_group_rss_bytes"])<=4<<30
                  and row["retained_before_receipt_bytes"]<=MAX and 0<=row["elapsed_seconds"]<=900 and
                  last<=row["campaign_elapsed_seconds"]<=terminal["elapsed_seconds"]<=2700,"registered native resource report")
        last=row["campaign_elapsed_seconds"]
        for key in ("stdout","stderr"):
            f=folder/key
            C.require(row[key+"_sha256"]==C.digest(f) and row[key+"_bytes"]==f.stat().st_size,"raw native output "+tag)
        C.require(row["stderr_bytes"]==0 and (row["stdout_bytes"]==0)==(style=="silent"),"native stdout/stderr shape")
        argv=row["argv"]; tool=Path(argv[0]).name
        if tag=="extract-official":
            C.require(tool=="tar" and len(argv)==7 and argv[1:4]==["--zstd","--no-same-owner","-xf"] and argv[5]=="-C","archive extraction")
        elif tag.startswith("stock-"):
            option="--githash" if tag=="stock-commit" else "--version"
            value=terminal["stock"] if tag=="stock-commit" else terminal["stock_version"]
            C.require(tool=="lean" and argv[1:]==[option] and (folder/"stdout").read_text().strip()==value,"stock identity command")
        else:
            kind,n=tag.split("-",1); st=stages[step]; step+=1
            imports=[line.split()[1] for line in (root/"sources"/(n+".lean")).read_text().splitlines() if line.startswith("import ")]
            local={m+".olean":known[m+".olean"] for m in imports if m+".lean" in source}
            C.require(st=={"kind":kind,"module":n,"source":source[n+".lean"],"preceding":known,"local_imports":local},
                      "sequenced source/import identities "+tag)
            if kind=="fresh":
                C.require(tool=="leanchecker" and argv[1:]==["--fresh",n] and n+".olean" in known,"ordinary fresh replay")
            else:
                flags=(["--json"] if kind=="refuse" else [])+["-DwarningAsError=true","-R"]
                C.require(tool=="lean" and argv[1:1+len(flags)]==flags and
                          len(argv)==len(flags)+5 and argv[-3]=="-o" and Path(argv[-4]).name=="sources" and
                          Path(argv[-2]).name==n+".olean" and argv[-1]==n+".lean","exact ordinary native compile")
                if kind!="refuse":
                    known[n+".olean"]=objects[n+".olean"]
    C.require(len(stages)==step and known==objects,"complete interstage observations")
    observed=C.inspect(repo,lambda n:root/"commands"/n/"stdout")
    C.require(observed==C.read(root/"observed.json") and C.info(root/"observed.json")==terminal["observed"],
              "independent arithmetic, typed terms, axioms, branches and false controls")
    files={p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    permitted={"registration.json","terminal.json","stages.json","observed.json"}|{"sources/"+n for n in source}|{"objects/"+n for n in objects}
    permitted|={"commands/"+key+"/"+f for key in commands for f in ("result.json","stdout","stderr")}
    C.require(files==permitted,"complete, exact archive member inventory")
    return terminal,observed

def verify(repo, archive, run, job, artifact, history):
    with tempfile.TemporaryDirectory(prefix="finite-index-readback-") as tmp:
        dest=Path(tmp); extract(archive,dest)
        C.require({p.name for p in dest.iterdir()}=={"launch.json","result"}, "hosted archive root")
        launch=C.read(dest/"launch.json")
        dest=dest/"result"
        terminal,observed=check_directory(dest,repo)
        C.require(launch=={"commit":terminal["commit"],"registration_commit":terminal["registration_commit"],
                          "registration_sha256":terminal["registration_sha256"],"run":terminal["run"],"attempt":1},
                  "first hosted timestamp/identity envelope")
        identity=match_remote(run,job,artifact,history,terminal,archive)
        return {"schema":"readback-invented-83-v1","status":"accepted invented calibration",
                **identity,"stock":C.STOCK_GIT,"judge_manifest":C.digest(HERE/"manifest.json"),
                "terminal":C.info(dest/"terminal.json"),"observed":C.info(dest/"observed.json"),
                "terms":observed["terms"]["checked"],"edges":sum(map(len,observed["edges"].values())),
                "rows":observed["finite"]["rows"],"native_refusals":sorted(observed["refused"]),
                "branches":83,"eligible_positions":82,"original_evaluations":0}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ("repository","archive","run","job","artifact","branch-runs","output"):
        parser.add_argument("--"+field,required=True,type=Path)
    args=parser.parse_args()
    C.require(not args.output.exists(),"new independently retained readback")
    out=verify(args.repository.resolve(),args.archive,C.read(args.run),C.read(args.job),C.read(args.artifact),C.read(args.branch_runs))
    C.write(args.output,out)
    print(json.dumps(out,sort_keys=True))
