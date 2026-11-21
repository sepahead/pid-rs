"""Offline readback of one exact hosted stock run. A missing or failed native observation cannot qualify."""
import argparse
import importlib.util
import json
from pathlib import Path
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("observer_support",HERE/"support.py")
S=importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
F=S.load(HERE/"frames.py")
C=S.load(HERE/"receipts.py")


def remote(run,job,artifact,history,archive,launch,conclusion):
    branch=S.REF_PREFIX+launch["registration_commit"]+"-"+launch["registration_sha256"]
    head=launch["commit"]; rid=launch["run"]
    S.require(type(launch) is dict and set(launch)=={"commit","registration_commit","registration_sha256","run","attempt","execution"} and
              type(launch["attempt"]) is int and all(type(value) is int and value>0 for value in
              (run["id"],run["repository"]["id"],run["head_repository"]["id"],run["workflow_id"],run["run_attempt"],job["run_id"],
               job["run_attempt"],artifact["workflow_run"]["id"],artifact["workflow_run"]["repository_id"],artifact["workflow_run"]["head_repository_id"],
               artifact["size_in_bytes"],history["total_count"])), "typed hosted identities")
    C.execution_roots(launch["execution"])
    S.require(all(S.V1.re.fullmatch("[0-9a-f]{40}",v) for v in (head,launch["registration_commit"])) and
              S.V1.re.fullmatch("[0-9a-f]{64}",launch["registration_sha256"]) and
              type(rid) is int and rid>0 and launch["attempt"]==1, "complete registered launch")
    S.require(history["total_count"]==1 and len(history["workflow_runs"])==1,"sole available matching reserved run")
    only=history["workflow_runs"][0]
    S.require(all(only[k]==run[k] for k in ("id","run_attempt","workflow_id","event","head_branch","head_sha","status","conclusion")) and
              only["repository"]["full_name"]==run["repository"]["full_name"]==run["head_repository"]["full_name"]=="sepahead/pid-rs" and
              run["event"]=="push" and run["run_attempt"]==job["run_attempt"]==1 and run["path"]==S.WORKFLOW and
              run["head_branch"]==job["head_branch"]==artifact["workflow_run"]["head_branch"]==branch and
              run["head_sha"]==job["head_sha"]==artifact["workflow_run"]["head_sha"]==head and
              run["id"]==job["run_id"]==artifact["workflow_run"]["id"]==rid and
              run["status"]==job["status"]=="completed" and run["conclusion"]==job["conclusion"]==conclusion and
              job["name"]==S.JOB and type(job["id"]) is int and job["id"]>0 and
              type(artifact["id"]) is int and artifact["id"]>0 and artifact["expired"] is False and
              run["repository"]["id"]==run["head_repository"]["id"]==artifact["workflow_run"]["repository_id"]==artifact["workflow_run"]["head_repository_id"] and
              artifact["name"]==f"{S.ARTIFACT_PREFIX}-{head}-{rid}-1" and
              artifact["digest"]=="sha256:"+S.digest(archive) and artifact["size_in_bytes"]==archive.stat().st_size,
              "exact terminal public job and its complete ZIP")
    return {"run":rid,"job":job["id"],"artifact":artifact["id"],"commit":head,"branch":branch,"archive":S.info(archive)}


def outcome(row,tag,wanted):
    code,style=wanted
    S.require(row["exit"]==code and row["stop"] is None and row["post_group_absent"] is True and row["residual_after_wait4"] is False and
              max(row["max_observed_group_rss_bytes"],row["direct_wait4_maxrss_bytes"])<=S.SAFE_LIMITS["group_rss_bytes"] and
              row["elapsed_seconds"]<=900 and row["retained_before_receipt_bytes"]<=1<<30 and row["stderr_bytes"]==0 and
              (row["stdout_bytes"]==0)==(style=="silent"), "expected successful operation or exact planned refusal "+tag)


def is_unit(tag):
    return tag not in ("extract-official","stock-version","stock-commit",S.POST)


def check_commands(root,repo,t,source,objects,execution,*,failed=False):
    schedule=S.schedule(repo)
    names=list(schedule)
    intervals=C.dispatches(t["dispatch_intervals"],names,t["elapsed_seconds"])
    invoked=list(intervals)
    cmd_root=root/"commands"
    folders={p.name for p in cmd_root.iterdir()} if cmd_root.is_dir() else set()
    reached=[tag for tag in names if tag in folders]
    phase=t.get("phase")
    cursor=t.get("stage")
    if failed:
        S.require(phase in {"setup","before-command","invoke","after-command","final"}, "failure phase")
        if phase=="setup":
            S.require(not invoked and cursor==C.SETUP,"setup cannot name a reached theorem")
        elif phase=="before-command":
            S.require(len(invoked)<len(names) and cursor==names[len(invoked)] and is_unit(cursor),"adjacent precommand stage")
        elif phase in ("invoke","after-command"):
            S.require(invoked and cursor==invoked[-1],"failed stage must equal the adjacent recorded dispatch")
        else:
            S.require(cursor==C.FINAL and invoked==names,"final check follows the full dispatch prefix")
    else:
        S.require(t["command_tags"]==invoked==names,"all 104 charged commands including the postprocessor")
    S.require(set(reached)==folders and (reached==invoked or
              (phase=="invoke" and invoked and reached==invoked[:-1])),"dispatch and native directory prefixes")
    stages=S.read(root/"stages.json") if (root/"stages.json").is_file() else []
    S.require(type(stages) is list,"typed stage list")
    prior={}; index=0; paths=C.Commands(execution); results=[]; unqualified_objects=[]
    persistent=sum(len(b) for b in source.values())+(root.parent/"launch.json").stat().st_size
    if (root/"registration.json").is_file():
        persistent+=(root/"registration.json").stat().st_size
    for tag in invoked:
        folder=cmd_root/tag
        last=(tag==invoked[-1])
        if is_unit(tag):
            C.stage(stages,index,tag,source,prior)
            index+=1
        if not folder.exists() or not (folder/"result.json").is_file():
            S.require(failed and phase=="invoke" and last,"missing receipt before another command")
            streams={p.name:S.info(p) for p in folder.iterdir()} if folder.exists() else {}
            S.require(set(streams) in (set(),{"stdout"},{"stdout","stderr"}),"incomplete command stream creation")
            results.append({"command":tag,"receipt":"absent","retained_streams":streams})
            break
        S.require({p.name for p in folder.iterdir()}=={"result.json","stdout","stderr"},"three raw command files")
        row=S.read(folder/"result.json")
        paths.verify(tag,row["argv"])
        if not failed:
            outcome(row,tag,schedule[tag])
        C.receipt(row,tag,folder,intervals[tag])
        stop_evidence=C.coherent_stop(row,intervals[tag])
        minimum=persistent+sum(v["bytes"] for v in prior.values())+row["stdout_bytes"]+row["stderr_bytes"]
        S.require(row["retained_before_receipt_bytes"]>=minimum,"retained reading below already present source, stream and object bytes")
        persistent+=row["stdout_bytes"]+row["stderr_bytes"]+(folder/"result.json").stat().st_size
        ok=True
        try:
            outcome(row,tag,schedule[tag])
        except ValueError:
            ok=False
        S.require(ok or (failed and phase=="invoke" and last),"unexpected earlier command outcome")
        S.require(not (failed and phase=="invoke" and last and ok),"successful receipt labeled as a failed invocation")
        if failed and phase=="invoke" and last and not ok:
            # The fixed provider has two explicit exits after it has written a complete result file.
            expected,style=schedule[tag]
            first=(row["stop"] or row["exit"]!=expected or row["stderr_bytes"] or (style=="silent" and row["stdout_bytes"]))
            native_error=("unexpected native outcome or diagnostics at " if first else "missing expected stdout at ")+tag
            S.require(t["error"]=="RuntimeError: "+native_error,"terminal reason and native receipt disagree")
        stock_matches=C.stock_text(tag,folder) if ok and tag in ("stock-version","stock-commit") else None
        S.require(stock_matches is not False or (failed and phase=="after-command" and last),"actual stock identity "+tag)
        if ok and tag.startswith(("compile-","inspect-")):
            unit=tag.split("-",1)[1]+".olean"
            if unit in objects and objects[unit]["bytes"]>0:
                prior[unit]=objects[unit]
            else:
                S.require(failed and phase=="after-command" and last,"missing successful object in failed prefix")
        results.append({"command":tag,"receipt":"complete","expected_code_and_resources":ok,"stock_identity_matches":stock_matches,
                        "exit":row["exit"],"stop":row["stop"],"stop_evidence":stop_evidence,"stdout_bytes":row["stdout_bytes"],"stderr_bytes":row["stderr_bytes"],
                        "observed_group_rss":row["max_observed_group_rss_bytes"],"group_samples":row["group_rss_sample_count"],
                        "post_group_absent":row["post_group_absent"],"residual_after_wait4":row["residual_after_wait4"]})
    additional=len(stages)-index
    if additional:
        S.require(failed and phase=="before-command" and additional==1,"surplus or absent prepared stage")
        C.stage(stages,index,cursor,source,prior)
    extra=set(objects)-set(prior)
    if extra:
        last_unit=cursor.split("-",1)[1]+".olean" if type(cursor) is str and cursor.startswith(("inspect-","compile-","refuse-")) else None
        S.require(failed and phase in ("invoke","after-command") and cursor in reached and extra=={last_unit},
                  "unexplained additional object")
        unqualified_objects=sorted(extra)
    if not failed:
        S.require(S.info(root/"stages.json")==t["stages"],"complete stage snapshots and objects")
    return results,prior,index,additional,unqualified_objects


def complete(root,repo,launch,reg,source):
    t=S.read(root/"terminal.json")
    required=set("""status attempt original_evaluations dispatch_intervals commit registration_commit registration_sha256
                 run run_attempt stock stock_version archive_sha256 stock_anchors affinity limits sources objects command_tags
                 stages observed frames joined elapsed_seconds""".split())
    S.require(type(t) is dict and set(t)==required and type(t["run"]) is int and type(t["run_attempt"]) is int and
              t["status"]==S.ACCEPTED and t["attempt"]==S.ATTEMPT and
              type(t["original_evaluations"]) is int and t["original_evaluations"]==0 and
              t["registration_commit"]==launch["registration_commit"] and t["registration_sha256"]==launch["registration_sha256"] and
              t["commit"]==launch["commit"] and t["run"]==launch["run"] and t["run_attempt"]==launch["attempt"]==1,
              "completed artificial terminal and matching launch")
    S.require(t["stock"]==S.STOCK_GIT and t["archive_sha256"]==S.STOCK and t["stock_version"]==S.STOCK_VERSION and
              t["limits"]==reg["limits"]==S.SAFE_LIMITS and type(t["elapsed_seconds"]) in (float,int) and 0<t["elapsed_seconds"]<2700 and
              set(t["stock_anchors"])==set(S.ANCHORS) and all(S.V1.re.fullmatch("[0-9a-f]{64}",v) for v in t["stock_anchors"].values()) and
              all(t["stock_anchors"][k]==v for k,v in reg["stock_source_anchors"].items()),"stock, anchors and campaign deadline")
    before=t["affinity"]["before"];during=t["affinity"]["during_native"]
    S.require(type(before) is list and before and before==sorted(set(before)) and
              all(type(k) is int and k>=0 for k in before) and during==[before[0]],"single logical CPU")
    files={p.relative_to(root.parent).as_posix() for p in root.parent.rglob("*") if p.is_file()}
    S.require(files==S.all_files(repo,source) and S.tree_bytes(root.parent)<=1<<30, "509-file cumulative evidence closure")
    S.require((root/"registration.json").read_bytes()==(repo/S.REGISTER).read_bytes(),"registered bytes in actual archive")
    sources=S.members(root/"sources")
    S.require(sources==t["sources"]=={n:S.info_bytes(b) for n,b in source.items()} and
              all((root/"sources"/n).read_bytes()==b for n,b in source.items()),"all 97 independently derived source bytes")
    objects=S.members(root/"objects")
    S.require(objects==t["objects"] and len(objects)==93 and all(v["bytes"]>0 for v in objects.values()),"all 93 ordinary stock and observer objects")
    check_commands(root,repo,t,source,objects,launch["execution"])
    observed=F.verify_derived(root,repo)
    S.require(observed==S.read(root/"observed.json") and S.info(root/"observed.json")==t["observed"] and
              S.info(root/"term-shards.json")==t["frames"] and S.info(root/"joined-terms.stdout")==t["joined"], "full current independent readback")
    final_resource=last_storage(root,S.POST)
    return {"final_storage":final_resource,"status":S.ACCEPTED,"terms":observed["terms"]["checked"],"edges":sum(map(len,observed["edges"].values())),
            "numerical_rows":observed["finite"]["rows"],"refused":sorted(observed["refused"]),"shards":87,
            "source_units":97,"stock_and_provisioning_commands":103,"bounded_postprocessing_commands":1,
            "original_evaluations":0,"observed":S.info(root/"observed.json"),"terminal":S.info(root/"terminal.json")}


def last_storage(root,last_tag):
    """When no later stage writes, the last raw receipt and terminal are the only later files."""
    post=root/"commands"/last_tag/"result.json"
    later={post,root/"terminal.json"}
    total=sum(p.stat().st_size for p in root.parent.rglob("*") if p.is_file() and p not in later)
    reported=S.read(post)["retained_before_receipt_bytes"]
    S.require(reported==total,"last stock-provider storage reading differs from actual retained file lengths")
    return {"measured_before_receipt_bytes":reported,"recomputed_from_closed_files_bytes":total}


def failure(root,repo,reg,source):
    t=S.read(root/"terminal.json")
    required={"status","attempt","original_evaluations","stage","phase","error","elapsed_seconds","dispatch_intervals"}
    S.require(type(t) is dict and set(t)==required and t["status"]==S.FAILED and t["attempt"]==S.ATTEMPT and
              type(t["original_evaluations"]) is int and t["original_evaluations"]==0 and
              type(t["error"]) is str and t["error"].strip() and C.clock(t["elapsed_seconds"])>0,"disclosed failed terminal")
    archived=S.members(root/"sources") if (root/"sources").is_dir() else {}
    released={n:S.info_bytes(b) for n,b in source.items()}
    S.require(all(n in released and item==released[n] for n,item in archived.items()),"failed prefix source changed")
    regfile=root/"registration.json"
    if regfile.exists():
        S.require(regfile.read_bytes()==(repo/S.REGISTER).read_bytes() and S.read(regfile)==reg,"failed prefix registration changed")
    if t["phase"]=="setup":
        S.require(not archived or regfile.is_file(),"registration before any retained source file")
    else:
        S.require(regfile.is_file() and archived==released,"all registered sources before a command")
    objects=S.members(root/"objects") if (root/"objects").is_dir() else {}
    execution=S.read(root.parent/"launch.json")["execution"]
    results,prior,nstage,extra,unqualified=check_commands(root,repo,t,source,objects,execution,failed=True)
    stage=t["stage"]
    derived=["joined-terms.stdout","term-shards.json","observed.json"]
    present=[name for name in derived if (root/name).is_file()]
    S.require(present==derived[:len(present)] and (not present or (results and results[-1]["command"]==S.POST)),
              "postprocessor output precedes the registered dispatch")
    allowed=S.all_files(repo,source)|{"result/objects/"+name for name in unqualified}
    retained={"result/"+p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    S.require(retained<=allowed,"unregistered failed-prefix member")
    # A missing receipt leaves the executable, its exit and its outputs unverified. A label never proves a native observation.
    assigned=[]
    if t["phase"]=="invoke" and results and results[-1]["receipt"]=="complete" and stage.startswith("inspect-"):
        assigned=dict(S.groups(S.read(repo/S.V1.PACKAGE/"plan.json"))).get(stage.removeprefix("inspect-"),[])
    if results and t["phase"] in ("invoke","after-command","final") and results[-1]["receipt"]=="complete":
        reconciled=last_storage(root,results[-1]["command"])
    else:
        reconciled=None
    return {"final_storage":reconciled,"status":S.FAILED,"attempt":S.ATTEMPT,"permitted_original_issues":0,"stage":stage,"phase":t["phase"],"assigned_theorems":assigned,
            "source_files_verified":len(archived),"retained_source_files":archived,"successful_objects_linked":prior,"additional_observed_object_files":unqualified,
            "completed_stage_prefix":nstage,"additional_precommand_stages":extra,"observed_command_prefix":results,
            "partial_derived_files":{n:S.info(root/n) for n in present},"terminal":S.info(root/"terminal.json"),"reported_error":t["error"]}


def verify(repo,archive,run,job,artifact,history,report_failure):
    with tempfile.TemporaryDirectory(prefix="index-observer-v4-readback-") as tmp:
        dest=Path(tmp)
        S.require(0<archive.stat().st_size<=1<<30,"compressed archive size before opening")
        with zipfile.ZipFile(archive) as z:
            C.headers(z.infolist())
            S.require(z.getinfo("launch.json").file_size<=4096,"small fixed launch descriptor")
            launch=json.loads(z.read("launch.json"),object_pairs_hook=S.V1.pairs)
            identity=remote(run,job,artifact,history,archive,launch,"failure" if report_failure else "success")
            C.copy_registered(z,dest)
        S.require({p.name for p in dest.iterdir()}=={"launch.json","result"},"hosted archive root")
        root=dest/"result"
        terminal=S.read(root/"terminal.json")
        policy=S.read(repo/S.REGISTER)
        reg,source=S.bound_sources(repo,launch["registration_commit"],launch["commit"],launch["registration_sha256"],policy["judge_manifest"])
        if report_failure:
            outcome=failure(root,repo,reg,source)
        else:
            S.require(terminal["status"]==S.ACCEPTED,"original-free qualification is incomplete or failed")
            outcome=complete(root,repo,launch,reg,source)
        return {"schema":"stock-synthetic-87-readback-v4",**identity,**outcome}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("repository","archive","run","job","artifact","branch-runs","output"):
        parser.add_argument("--"+name,required=True,type=Path)
    parser.add_argument("--describe-failure",action="store_true",help="return only the achieved prefix and blocked failed disposition")
    args=parser.parse_args()
    S.require(not args.output.exists(),"new operator output")
    receipt=verify(args.repository.resolve(),args.archive,S.read(args.run),S.read(args.job),S.read(args.artifact),
                   S.read(args.branch_runs),args.describe_failure)
    S.write(args.output,receipt)
    print(json.dumps(receipt,sort_keys=True))
