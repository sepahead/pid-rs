"""Read the first hosted V4 result and determine which native identities the original artifact establishes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

HERE=Path(__file__).resolve().parent
STUDY="audit/research/index-family-observer-v4"
ADDENDUM="audit/research/index-family-native-attribution-v1"
AXDIR="result/commands/inspect-IndexAxioms/"
HEX40=r"[0-9a-f]{40}"
HEX64=r"[0-9a-f]{64}"


def need(ok,msg):
    if not ok:raise ValueError(msg)


def pairs(rows):
    result=dict(rows)
    need(len(result)==len(rows),"duplicate JSON field")
    return result


def read(data):
    return json.loads(data,object_pairs_hook=pairs)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    with path.open("rb") as f:return hashlib.file_digest(f,"sha256").hexdigest()


def write_json(path,obj):
    with path.open("x",encoding="utf-8") as f:f.write(json.dumps(obj,indent=2,sort_keys=True)+"\n")


def git(repo,*args):
    return subprocess.check_output(["git","--no-optional-locks","-C",str(repo),*args])


def study_module(repo,c,issue):
    # Bind every module which V4 can load before importing that code.
    parent,child=issue["registration_commit"],issue["child"]
    need(all(type(v) is str and re.fullmatch(HEX40,v) for v in (parent,child)),"full preissue commits")
    def bound(name,expected,older=False):
        raw=(repo/name).read_bytes()
        need(sha(raw)==expected and raw==git(repo,"show",parent+":"+name)==git(repo,"show",child+":"+name),"fixed reader file "+name)
        if older:need(raw==git(repo,"show",c["base_commit"]+":"+name),"earlier source byte "+name)
        return raw
    manifest=read(bound(STUDY+"/manifest.json",c["study_manifest"]))
    bound(STUDY+"-registration.json",c["study_registration"])
    bound(".github/workflows/index-family-observer-v4.yml",c["study_workflow"])
    for n,record in manifest["files"].items():bound(STUDY+"/"+n,record["sha256"])
    providers=read((repo/STUDY/"providers.json").read_bytes())
    for n,record in providers["files"].items():bound(n,record["sha256"],True)
    spec=importlib.util.spec_from_file_location("registered_observer_v4",repo/STUDY/"verify.py")
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def strict_affinity(value):
    need(type(value) is dict and set(value)=={"before","during_native"},"affinity fields")
    old=value["before"];chosen=value["during_native"]
    need(type(old) is list and old and type(chosen) is list and len(chosen)==1 and
         all(type(c) is int and c>=0 for c in old+chosen) and old==sorted(set(old)) and chosen==[old[0]],
         "strict Linux CPU identifiers")
    return value


def exact_binaries(value,expected):
    need(type(value) is dict and all(value.get(k)==h for k,h in expected.items()),"two observed stock executable identities")
    return {k:value[k] for k in expected}


def as_sets(raw):
    out={}
    for line in raw.splitlines():
        text=line.decode("ascii").strip()
        mat=re.fullmatch(r"'([A-Za-z][A-Za-z0-9_.]*)'\s+(?:does\s+not\s+depend\s+on\s+any\s+axioms|depends\s+on\s+axioms\s*:\s*\[([^\]]*)\])",text)
        need(mat is not None,"complete stock axiom line")
        key,body=mat.groups();axioms=[part.strip() for part in body.split(",")] if body and body.strip() else []
        need(key not in out and len(axioms)==len(set(axioms)) and all(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]*",v) for v in axioms),
             "unique theorem and axiom names")
        out[key]=sorted(axioms)
    return out


def compare_terms(declarations,expected):
    need(type(declarations) is dict and set(declarations)==set(expected),"all 170 term declarations")
    for name,wanted in expected.items():
        actual=declarations[name].get("axioms") if type(declarations[name]) is dict else None
        need(type(actual) is list and all(type(x) is str for x in actual) and len(actual)==len(set(actual)) and sorted(actual)==wanted,
             "term transitive axioms for "+name)


def stock_files(directory,expected):
    actual={}
    for name in expected:
        p=directory/name
        need(p.is_file() and not p.is_symlink(),"regular supplier image "+name)
        actual[name]=file_sha(p)
    return exact_binaries(actual,expected)


def history_source(repo,c,dest=None):
    h=c["original_83"];archive=repo/h["archive_path"]
    need(file_sha(archive)==h["archive_sha256"],"registered earlier 83-index ZIP")
    with zipfile.ZipFile(archive) as z:
        raw=z.read(h["raw_member"])
        need(sha(z.read(AXDIR+"result.json"))==h["command_sha256"] and sha(z.read("result/sources/IndexAxioms.lean"))==h["source_sha256"],
             "earlier axiom source and command")
    need(sha(raw)==h["raw_sha256"] and len(raw)==h["raw_bytes"] and as_sets(raw)==h["named_sets"],"historical raw axiom lines and all named sets")
    sibling=c["stock"]["observed_sibling"];released=(repo/sibling["public_record"]).read_bytes()
    need(sha(released)==sibling["public_record_sha256"] and exact_binaries(read(released)["stock_files"],c["stock"]["executables"]),"earlier public binary record")
    if dest:(dest/"historical-IndexAxioms.stdout").write_bytes(raw)
    return raw


def binding(repo,c,contract_sha,issue,V):
    reg=issue["registration_commit"];child=issue["child"]
    need(type(issue) is dict and set(issue)=={"registration_commit","child","study_registration_sha256","addendum_sha256"} and
         type(reg) is str and re.fullmatch(HEX40,reg) and type(child) is str and re.fullmatch(HEX40,child) and
         issue["study_registration_sha256"]==c["study_registration"] and issue["addendum_sha256"]==contract_sha,
         "pre-issued separate parent/child and two registration identities")
    files={**c["attribution_files"],"contract.json":contract_sha}
    for name,h in files.items():
        path=ADDENDUM+"/"+name;b=(repo/path).read_bytes()
        need(sha(b)==h and b==git(repo,"show",reg+":"+path)==git(repo,"show",child+":"+path),"frozen attribution file "+name)
    need(HERE==(repo/ADDENDUM).resolve(),"registered operator source")
    regdata,source=V.S.bound_sources(repo,reg,child,c["study_registration"],c["study_manifest"])
    need(regdata["workflow_sha256"]==c["study_workflow"] and regdata["materialized_sources"]==c["study_sources"] and
         len(source)==97 and {n:sha(b) for n,b in source.items()}==c["study_sources"],"all 97 registered original and derived sources")
    return reg,child


def uint(x):return type(x) is int and x>0


def event(c,issue,ids,run,job,history):
    branch="review/index-family-observer-v4/"+issue["registration_commit"]+"-"+c["study_registration"]
    need(type(ids) is dict and set(ids)=={"run","job","artifact","archive_sha256"} and uint(ids["run"]) and uint(ids["job"]),"independent observed event IDs")
    for row in (run,job):
        need(type(row.get("run_attempt")) is int and row["run_attempt"]==1 and row["status"]=="completed" and
             row["head_sha"]==issue["child"] and row["head_branch"]==branch,"first completed child and branch")
    need(all(uint(k) for k in (run["id"],job["run_id"],job["id"],run["repository"]["id"],run["head_repository"]["id"])) and
         run["repository"]["id"]==run["head_repository"]["id"] and run["id"]==job["run_id"]==ids["run"] and job["id"]==ids["job"] and run["event"]=="push" and
         run["path"]==".github/workflows/index-family-observer-v4.yml" and job["name"]=="Observe 170 synthetic declarations on one Linux CPU" and
         all(run[key]["full_name"]=="sepahead/pid-rs" for key in ("repository","head_repository")) and
         uint(run["workflow_id"]) and (run["conclusion"]=="success")== (job["conclusion"]=="success"),"specific observed job")
    need(type(history["total_count"]) is int and history["total_count"]==1 and len(history["workflow_runs"])==1,"one reserved workflow execution")
    seen=history["workflow_runs"][0]
    need(all(seen[k]==run[k] for k in ("id","workflow_id","run_attempt","event","head_branch","head_sha","status","conclusion")) and
         seen["repository"]["full_name"]=="sepahead/pid-rs","same first run in independent history")
    return run["conclusion"]=="success"


def assess(fn):
    try:return {"state":"verified","value":fn()}
    except (ValueError,KeyError,TypeError) as e:return {"state":"mismatch","reason":str(e)}


def gates(c,terminal):
    checks={}
    for key,label,validate in (("affinity","affinity",strict_affinity),("stock_anchors","stock_executables",lambda a:exact_binaries(a,c["stock"]["executables"]))):
        checks[label]=assess(lambda:validate(terminal[key])) if key in terminal else {"state":"unobserved"}
    return checks


def streams(z,name,dest):
    with z.open(name) as incoming, dest.open("xb") as out:shutil.copyfileobj(incoming,out,1<<17)


def total_sources(z,names,expected):
    root="result/sources/"
    actual={}
    for member in sorted(n for n in names if n.startswith(root)):
        key=member[len(root):]
        with z.open(member) as stream:actual[key]=hashlib.file_digest(stream,"sha256").hexdigest()
    return {"matching":sorted(n for n,h in actual.items() if expected.get(n)==h),
            "missing":sorted(set(expected)-set(actual)),
            "unexpected_or_different":{n:h for n,h in actual.items() if expected.get(n)!=h}}


def audit(repo,evidence,out,c,csha,issue,ids,V):
    binding(repo,c,csha,issue,V)
    history_source(repo,c,out)
    docs={k:read((evidence/(k+".json")).read_bytes()) for k in ("run","job","branch-runs","artifacts")}
    success=event(c,issue,ids,docs["run"],docs["job"],docs["branch-runs"])
    result={"native_event_ids":ids,"external_issue":issue,"hosted_run_conclusion":docs["run"]["conclusion"],
            "hosted_job_conclusion":docs["job"]["conclusion"],"status":"no positive native attribution","native_scientific_originals":0}
    artifacts=docs["artifacts"];rows=artifacts["artifacts"]
    need(type(artifacts["total_count"]) is int and artifacts["total_count"]==len(rows),"complete artifact inventory")
    archive=evidence/"native.zip"
    if ids["artifact"] is None:
        need(ids["archive_sha256"] is None and not rows and not archive.exists() and not success,"documented absent artifact for unsuccessful hosted run")
        result["available_evidence"]="No native archive was retained.";return result
    need(uint(ids["artifact"]) and type(ids["archive_sha256"]) is str and re.fullmatch(HEX64,ids["archive_sha256"]) and
         archive.is_file() and 0<archive.stat().st_size<=1<<30 and file_sha(archive)==ids["archive_sha256"],"independently identified native ZIP")
    art=read((evidence/"artifact.json").read_bytes())
    need(len(rows)==1 and rows[0]["id"]==art["id"]==ids["artifact"] and
         rows[0]["digest"]==art["digest"]=="sha256:"+ids["archive_sha256"] and
         rows[0]["size_in_bytes"]==art["size_in_bytes"]==archive.stat().st_size and
         art["expired"] is False and art["workflow_run"]["id"]==ids["run"] and art["workflow_run"]["head_sha"]==issue["child"] and
         art["workflow_run"]["head_branch"]==docs["run"]["head_branch"] and art["workflow_run"]["repository_id"]==art["workflow_run"]["head_repository_id"]==docs["run"]["repository"]["id"] and
         art["name"]==f"{V.S.ARTIFACT_PREFIX}-{issue['child']}-{ids['run']}-1","provider archive membership and identity")
    with zipfile.ZipFile(archive) as z:
        V.C.headers(z.infolist());names=set(z.namelist())
        terminal={}
        if "result/terminal.json" in names:
            raw=z.read("result/terminal.json");(out/"terminal.original.json").write_bytes(raw)
            result["original_terminal_sha256"]=sha(raw)
            parsed=assess(lambda:read(raw))
            if parsed["state"]=="verified" and type(parsed["value"]) is dict:terminal=parsed["value"]
        result["producer_terminal_status"]=terminal.get("status")
        result["native_identity_fields"]=gates(c,terminal)
        if AXDIR+"stdout" in names:
            streams(z,AXDIR+"stdout",out/"actual-IndexAxioms.stdout")
        if "result/observed.json" in names:
            streams(z,"result/observed.json",out/"observed.original.json")
        if "launch.json" not in names:
            result["available_evidence"]="Native launch metadata is absent. Retained terminal and output are unqualified raw bytes."
            for f in result["native_identity_fields"].values():
                if f["state"]=="verified":f["state"]="matching raw field without launch binding"
            return result
        launch=read(z.read("launch.json"))
        need(launch["commit"]==issue["child"] and launch["registration_commit"]==issue["registration_commit"] and
             launch["registration_sha256"]==c["study_registration"] and launch["run"]==ids["run"],"launch versus external preissue child")
        result["materialized_sources"]=total_sources(z,names,c["study_sources"])
    # Call the unchanged original checker directly. Its return identity and mathematical outcome remain separate facts.
    try:
        v4=V.verify(repo,archive,docs["run"],docs["job"],art,docs["branch-runs"],not success)
        write_json(out/"v4.original-readback.json",v4)
        result["v4_disposition"]={"state":"verified","status":v4["status"]}
    except (ValueError,KeyError,TypeError,OSError,zipfile.BadZipFile,subprocess.CalledProcessError) as e:
        v4=None;result["v4_disposition"]={"state":"unavailable","reason":str(e)}
    if v4 is None:
        for field in result["native_identity_fields"].values():
            if field["state"]=="verified":field["state"]="matching raw terminal field; native readback unavailable"
    current=out/"actual-IndexAxioms.stdout"
    completed=bool(v4 and (success or any(r["command"]=="inspect-IndexAxioms" and r["receipt"]=="complete" and
                                           r["expected_code_and_resources"] is True for r in v4["observed_command_prefix"])))
    if current.exists():
        raw=current.read_bytes()
        ax={"raw_bytes":len(raw),"raw_sha256":sha(raw),"same_raw_bytes_as_prior":sha(raw)==c["original_83"]["raw_sha256"]}
        if completed:
            def named():
                seen=as_sets(raw);need(seen==c["original_83"]["named_sets"],"170 historical named axiom sets");return len(seen)
            ax["sets"]=assess(named)
        else:ax["sets"]={"state":"unqualified raw stream"}
    else:ax={"sets":{"state":"unobserved"}}
    result["axiom_output"]=ax
    terms={"state":"unobserved"}
    if success and v4:
        def declarations():
            d=read((out/"observed.original.json").read_bytes())["terms"]["declarations"]
            compare_terms(d,c["original_83"]["named_sets"]);return len(d)
        terms=assess(declarations)
    result["named_term_axioms"]=terms
    src=result["materialized_sources"]
    if (success and v4 and v4["status"]==V.S.ACCEPTED and not src["missing"] and not src["unexpected_or_different"] and
        all(v["state"]=="verified" for v in result["native_identity_fields"].values()) and ax["sets"]["state"]==terms["state"]=="verified"):
        result["status"]="positive native attribution for this fixed artificial V4 run"
    return result


def self_test(repo,c):
    raw=history_source(repo,c);wanted=c["original_83"]["named_sets"];stock=c["stock"]["executables"]
    denied=[]
    def refuse(label,call):
        try:call()
        except (ValueError,KeyError,TypeError):denied.append(label)
        else:raise ValueError("unexpected acceptance: "+label)
    def match(data):
        need(as_sets(data)==wanted,"all named sets")
    match(raw);match(raw.replace(b"\n",b"\r\n"))
    match(b"\n".join(reversed(raw.splitlines()))+b"\n")
    need(sha(raw.replace(b"\n",b"\r\n"))!=sha(raw),"same named sets with distinct raw bytes")
    exact_binaries(stock,stock);strict_affinity({"before":[0,1],"during_native":[0]})
    compare_terms({n:{"axioms":v} for n,v in wanted.items()},wanted)
    for field in stock:
        other={**stock,field:"f"*64}
        refuse("other executable "+field,lambda:exact_binaries(other,stock))
        refuse("missing executable "+field,lambda:exact_binaries({k:v for k,v in stock.items() if k!=field},stock))
    for value in ({"before":[0,1],"during_native":[False]},{"before":[False,1],"during_native":[0]},
                  {"before":[0,True],"during_native":[0]},{"before":[0,1],"during_native":[1]},
                  {"before":[0,0],"during_native":[0]},{"before":[-1,0],"during_native":[-1]}):
        refuse("bad affinity "+repr(value),lambda:strict_affinity(value))
    lines=raw.splitlines(keepends=True)
    refuse("absent historical theorem",lambda:match(b"".join(lines[1:])))
    refuse("duplicate historical theorem",lambda:match(raw+lines[0]))
    refuse("historical singleton changed",lambda:match(raw.replace(b"[propext]",b"[Classical.choice]",1)))
    refuse("two axioms where one was observed",lambda:match(raw.replace(b"[propext]",b"[Quot.sound, propext]",1)))
    refuse("raw nonempty set for historical empty theorem",lambda:match(raw.replace(b"does not depend on any axioms",b"depends on axioms: [propext]",1)))
    refuse("one repeated axiom",lambda:match(raw.replace(b"[propext]",b"[propext, propext]",1)))
    wrong={n:{"axioms":v} for n,v in wanted.items()};wrong["IndexExample.cover83"]={"axioms":["propext"]}
    refuse("term despite correct separate axiom list",lambda:compare_terms(wrong,wanted))
    issue={"child":"b"*40,"registration_commit":"a"*40};branch="review/index-family-observer-v4/"+issue["registration_commit"]+"-"+c["study_registration"]
    org={"id":7,"full_name":"sepahead/pid-rs"}
    run={"id":8,"run_attempt":1,"status":"completed","head_sha":issue["child"],"head_branch":branch,"workflow_id":9,"event":"push",
         "conclusion":"success","repository":org,"head_repository":org,"path":".github/workflows/index-family-observer-v4.yml"}
    job={"run_attempt":1,"status":"completed","head_sha":issue["child"],"head_branch":branch,"run_id":8,"id":10,"name":"Observe 170 synthetic declarations on one Linux CPU","conclusion":"success"}
    hist={"total_count":1,"workflow_runs":[run]};ids={"run":8,"job":10,"artifact":11,"archive_sha256":"c"*64}
    need(event(c,issue,ids,run,job,hist),"single modeled first-event envelope")
    for label,what,patch in (("incorrect expected child",issue,{"child":"c"*40}),("incorrect expected job",ids,{"job":12}),
                              ("second hosted attempt",job,{"run_attempt":2}),("incorrect workflow",run,{"path":"other.yml"}),
                              ("additional run on reserved ref",hist,{"total_count":2}),("boolean attempt",job,{"run_attempt":True})):
        earlier=what.copy();what.update(patch)
        try:refuse(label,lambda:event(c,issue,ids,run,job,hist))
        finally:what.clear();what.update(earlier)
    absent=gates(c,{})
    need(all(k["state"]=="unobserved" for k in absent.values()),"absence in a genuine unsuccessful run grants no stock identity")
    return {"scope":"offline attribution semantics and modeled identity envelope; no hosted event was attributed",
            "prior_positive_binary_observation":stock,"historical_axiom_raw":sha(raw),"historical_theorems":len(wanted),
            "empty_named_set":"IndexExample.cover83","nonempty_named_sets":sum(bool(v) for v in wanted.values()),
            "semantic_controls_refused":denied,"source_identities_bound":len(c["study_sources"]),"new_native_runs":0}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--repository",type=Path,default=HERE.parents[2])
    p.add_argument("--addendum-sha256",required=True)
    group=p.add_mutually_exclusive_group(required=True);group.add_argument("--self-test",action="store_true");group.add_argument("--issue",type=Path)
    p.add_argument("--ids",type=Path);p.add_argument("--evidence",type=Path);p.add_argument("--output",type=Path)
    p.add_argument("--supplier-directory",type=Path,help="optional already-provisioned Linux release root; read its two regular files without executing them")
    args=p.parse_args();repo=args.repository.resolve();b=(HERE/"contract.json").read_bytes()
    need(re.fullmatch(HEX64,args.addendum_sha256) and sha(b)==args.addendum_sha256,"independently supplied addendum digest")
    c=read(b)
    need(c["format"]=="index-family-native-attribution-v1" and all(file_sha(HERE/n)==h for n,h in c["attribution_files"].items()),
         "fixed attribution source")
    if args.supplier_directory:stock_files(args.supplier_directory.resolve(),c["stock"]["executables"])
    if args.self_test:
        print(json.dumps(self_test(repo,c),sort_keys=True));return 0
    need(args.ids and args.evidence and args.output and not args.output.exists(),"identified issue, observed IDs, original responses and new output")
    args.output.mkdir()
    try:
        issue=read(args.issue.read_bytes())
        r=audit(repo,args.evidence,args.output,c,args.addendum_sha256,issue,read(args.ids.read_bytes()),study_module(repo,c,issue))
    except (ValueError,KeyError,TypeError,OSError,zipfile.BadZipFile,subprocess.CalledProcessError) as error:
        r={"status":"no positive native attribution","readback_error":type(error).__name__+": "+str(error)}
    write_json(args.output/"attribution.json",r);print(json.dumps(r,sort_keys=True))
    return 0 if r["status"]=="positive native attribution for this fixed artificial V4 run" else 2


if __name__=="__main__":
    sys.exit(main())
