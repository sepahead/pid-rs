"""Candidate-free parser checks. All native-looking rows, outputs and objects created here are artificial."""
import copy
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
import tempfile
import zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("calibration_verifier",HERE/"verify.py")
V=importlib.util.module_from_spec(spec);spec.loader.exec_module(V)
S,F=V.S,V.F
R=S.REPOSITORY
PREFIX=b"W02_TERM "


def encoded(obj):
    return (json.dumps(obj,sort_keys=True,separators=(",",":"))+"\n").encode()


def fixture_storage_before_last(failed,tag):
    # The fixture may edit a stream or withhold an object to model a genuine failed prefix.
    # Use actual remaining logical lengths. The current receipt and terminal postdate the measured state.
    receipt=failed/"commands"/tag/"result.json"
    later={receipt,failed/"terminal.json"}
    return sum(p.stat().st_size for p in failed.parent.rglob("*") if p.is_file() and p not in later)


def modeled_rows(plan):
    result={}
    for i,(name,owner) in enumerate(plan["targets"].items()):
        transitive=["propext"] if i%5==0 else []
        constants=set(plan["edges"].get(name,[]))|set(transitive)
        if name in plan["consumer_uses"]:constants.add(plan["consumer_uses"][name])
        result[name]={"name":name,"owner":owner,"kind":"theorem","ordinary_import_trust":0,"universe_parameters":[],
                "type_constructor_representation":"Lean.Expr.const MODEL_TYPE_"+str(i),
                "value_constructor_representation":"Lean.Expr.const MODEL_VALUE_"+str(i),
                "type_constants":["Nat"],"value_constants":sorted(constants),"direct_type_axioms":[],
                "direct_value_axioms":transitive,"axioms":transitive}
    return result


def fixture(dest,reg,src):
    root=dest/"result";root.mkdir()
    obj=root/"objects";obj.mkdir();sf=root/"sources";sf.mkdir()
    for name,b in src.items():(sf/name).write_bytes(b)
    (root/"registration.json").write_bytes((R/S.REGISTER).read_bytes())
    resources=S.load(R/S.V1.OLD/"native_resources.py")
    old=S.read(R/S.V1.PACKAGE/"plan.json")
    pairs=dict(S.groups(old)); rows=modeled_rows(old)
    parent="a"*40;head="b"*40;regsha=S.digest(R/S.REGISTER)
    launch={"commit":head,"registration_commit":parent,"registration_sha256":regsha,"run":123,"attempt":1,
            "execution":{"workspace":"/FIXTURE/checkout","runner_temp":"/FIXTURE/temp","python":"/FIXTURE/python3"}}
    S.write(dest/"launch.json",launch)
    sources=S.members(sf);prior={};stages=[];commands=S.schedule(R); numbered=0
    stockbin="/FIXTURE/temp/index-observer-v4-stock/lean-4.34.1-linux/bin/"
    result_loc="/FIXTURE/temp/index-observer-v4-evidence/result"
    intervals=[]
    for tag,(code,style) in commands.items():
        numbered+=1
        intervals.append({"tag":tag,"begin":numbered-0.65,"end":numbered+0.1})
        step=root/"commands"/tag;step.mkdir(parents=True)
        stdout=b"";stderr=b""
        if tag=="extract-official":
            argv=["/usr/bin/tar","--zstd","--no-same-owner","-xf","/FIXTURE/temp/index-observer-v4-release.tar.zst","-C","/FIXTURE/temp/index-observer-v4-stock"]
        elif tag.startswith("stock-"):
            opt="--githash" if tag=="stock-commit" else "--version"
            argv=[stockbin+"lean",opt]
            stdout=(S.STOCK_GIT if tag=="stock-commit" else S.STOCK_VERSION).encode()+b"\n"
        elif tag==S.POST:
            argv=["/FIXTURE/python3","-I","-S","-B","/FIXTURE/checkout/"+S.PACKAGE+"/frames.py","--result",result_loc]
        else:
            kind,n=tag.split("-",1)
            imports=[line.split()[1] for line in (sf/(n+".lean")).read_text().splitlines() if line.startswith("import ")]
            local={m+".olean":prior[m+".olean"] for m in imports if m+".lean" in src}
            stages.append({"kind":kind,"module":n,"source":sources[n+".lean"],"local_imports":local,"preceding":dict(prior)})
            S.write_counted(dest,root/"stages.json",stages)
            if kind=="fresh":
                argv=[stockbin+"leanchecker","--fresh",n]
            else:
                argv=[stockbin+"lean"]+(["--json"] if code else [])+["-DwarningAsError=true","-R",result_loc+"/sources","-o",result_loc+"/objects/"+n+".olean",n+".lean"]
                if kind!="refuse":
                    objfile=obj/(n+".olean");objfile.write_bytes(b"ARTIFICIAL TEST STRING, NOT A COMPILED OBJECT: "+n.encode())
                    prior[objfile.name]=S.info(objfile)
            if n=="IndexAxioms":
                stdout="".join("'"+name+"' "+("depends on axioms: [propext]" if row["axioms"] else "does not depend on any axioms")+"\n" for name,row in rows.items()).encode()
            elif n in pairs:
                stdout=b"".join(PREFIX+encoded(rows[name]) for name in pairs[n])
            elif n=="IndexTrace":
                stdout=("\n".join(S.V1.original_free_rows())+"\n").encode()
            elif kind=="refuse":
                spec=old["refusals"][n]
                stdout=encoded({"severity":"error","isSilent":False,"fileName":n+".lean","pos":{"line":spec["line"]},
                                "data":spec["prefix"]+" "+" ".join(spec["contains"])+" [MODELED DIAGNOSTIC]"})
        (step/"stdout").write_bytes(stdout);(step/"stderr").write_bytes(stderr)
        if tag==S.POST:
            F.write_evidence(root,R)
        # The fixed provider measures the files after the operation and before it creates this receipt.
        measured=resources.retained_bytes(dest)
        row={"tag":tag,"stage":S.STAGE,"argv":argv,"elapsed_seconds":0.5,"campaign_elapsed_seconds":float(numbered),
             "group_rss_sample_count":1,"max_observed_group_rss_bytes":4096*numbered,"direct_wait4_maxrss_bytes":4096,
             "retained_before_receipt_bytes":measured,"stop":None,"exit":code,"native_process_group":500+numbered,
             "post_group_absent":True,"residual_after_wait4":False,
             "stdout_sha256":S.digest_bytes(stdout),"stderr_sha256":S.digest_bytes(stderr),"stdout_bytes":len(stdout),"stderr_bytes":len(stderr)}
        S.write(step/"result.json",row)
    t={"status":S.ACCEPTED,"attempt":S.ATTEMPT,"commit":head,"registration_commit":parent,"registration_sha256":regsha,
       "run":123,"run_attempt":1,"stock":S.STOCK_GIT,"stock_version":S.STOCK_VERSION,
       "archive_sha256":S.STOCK,"stock_anchors":{k:reg["stock_source_anchors"].get(k,"f"*64) for k in S.ANCHORS},
       "limits":reg["limits"],"affinity":{"before":[0,1],"during_native":[0]},"original_evaluations":0,
       "dispatch_intervals":intervals,"elapsed_seconds":105.0,"sources":sources,"objects":prior,"command_tags":list(commands),
       "stages":S.info(root/"stages.json"),"frames":S.info(root/"term-shards.json"),"joined":S.info(root/"joined-terms.stdout"),
       "observed":S.info(root/"observed.json")}
    S.write(root/"terminal.json",t)
    return root,launch,rows,pairs


def tests():
    S.verify_provider_bytes(R)
    reg=S.validate_registration(S.read(R/S.REGISTER),R)
    src=S.from_payload(R,(R/S.PRIOR/"submitted.json").read_bytes(),reg)
    labels=[]
    def refuses(label,call,fragment):
        try:call()
        except (ValueError,FileNotFoundError,KeyError) as e:
            S.require(fragment in str(e),label+" unexpected refusal: "+str(e));labels.append(label)
        else:raise ValueError("unexpected modeled acceptance: "+label)
    def temporary(f,b,call):
        byte=f.read_bytes()
        try:f.write_bytes(b);call()
        finally:f.write_bytes(byte)
    with tempfile.TemporaryDirectory(prefix="parser-only-87-no-native-") as work:
        outer=Path(work);temp=outer/"fixture";temp.mkdir()
        root,launch,rows,pairs=fixture(temp,reg,src)
        good=lambda:V.complete(root,R,launch,reg,src)
        positive=good()
        S.require(positive["terms"]==170 and positive["edges"]==254 and positive["numerical_rows"]==332 and
                  len(positive["refused"])==3 and len(positive["refused"])==len(set(positive["refused"])),"positive modeled whole roster")
        first=next(iter(pairs));only=next(name for name,terms in pairs.items() if terms==["IndexExample.inlineComplete"])
        folder=lambda m:root/"commands"/("inspect-"+m)
        def replace_stream(tag,raw,fun):
            d=root/"commands"/tag;stream=d/"stdout";rec=d/"result.json";before=rec.read_bytes()
            def call():
                v=json.loads(before);v["stdout_bytes"]=len(raw);v["stdout_sha256"]=S.digest_bytes(raw)
                temporary(rec,encoded(v),fun)
            temporary(stream,raw,call)
        def change_term(label,mutate,expected,module=first):
            lines=(folder(module)/"stdout").read_bytes().splitlines(keepends=True)
            row=json.loads(lines[0][len(PREFIX):]);mutate(row)
            lines[0]=PREFIX+encoded(row)
            # Give the altered streams internally matching transfer digests and framing. The semantic reader must still reject.
            def run():
                joined=root/"joined-terms.stdout"; frames=root/"term-shards.json"
                group_order=list(pairs.items())
                payload=b"".join((folder(m)/"stdout").read_bytes() for m,_ in group_order)
                def compare():
                    fake=F.fold(root,group_order)
                    temporary(frames,encoded(fake),lambda:F.verify_derived(root,R))
                temporary(joined,payload,compare)
            replace_stream("inspect-"+module,b"".join(lines),lambda:refuses(label,run,expected))
        d=folder(first);stream=(d/"stdout").read_bytes();raw_lines=stream.splitlines(keepends=True)
        replace_stream("inspect-"+first,b"".join(raw_lines[1:]),lambda:refuses("missing first assigned declaration",lambda:F.fold(root,list(pairs.items())),"wrong name"))
        replace_stream("inspect-"+first,raw_lines[0]+raw_lines[0],lambda:refuses("duplicate declaration in a pair",lambda:F.fold(root,list(pairs.items())),"wrong name"))
        replace_stream("inspect-"+first,stream[:-2],lambda:refuses("truncated row with matching altered checksum",lambda:F.fold(root,list(pairs.items())),"whole bounded native row"))
        replace_stream("inspect-"+first,stream+b"extra\n",lambda:refuses("trailing diagnostic in observer",lambda:F.fold(root,list(pairs.items())),"surplus raw row"))
        temporary(d/"stdout",stream.replace(b"MODEL_VALUE",b"CORRUPT_VAL",1),lambda:refuses("corrupt raw stdout",lambda:F.fold(root,list(pairs.items())),"incomplete native shard"))
        change_term("relabel an observation owner",lambda obj:obj.update(owner="OtherModule"),"theorem identity")
        change_term("missing full proof representation",lambda obj:obj.update(value_constructor_representation="..."),"incomplete/open")
        change_term("direct forbidden axiom",lambda obj:obj.update(direct_value_axioms=["sorryAx"]),"direct axiom readback")
        change_term("reported and printed transitive axioms disagree",lambda obj:obj.update(axioms=["Classical.choice"]),"theorem universe or axioms")
        named=list(pairs)[-2]
        change_term("missing required consumer dependency",lambda obj:obj.update(value_constants=[]),"consumer must directly use",named)
        change_term("single-slot borrows a named leaf",lambda obj:obj.update(value_constants=sorted(set(obj["value_constants"])|{"IndexExample.leaf01"})),"borrowed a named proof",only)
        cover=next(m for m,ns in pairs.items() if "IndexExample.cover83" in ns)
        change_term("drop required empty-tail elimination edge",lambda obj:obj.update(value_constants=[]),"missing constructive proof edge",cover)
        table=root/"term-shards.json"; original=S.read(table)
        for label,edit in [("overlapping spans",lambda v:v["frames"][1].update(begin=v["frames"][0]["begin"])),
                           ("gapped spans",lambda v:v["frames"][1].update(begin=v["frames"][1]["begin"]+1)),
                           ("swapped shard identity",lambda v:v["frames"][0].update(module=list(pairs)[1])),
                           ("missing shard frame",lambda v:v["frames"].pop()),
                           ("wrong joined digest",lambda v:v["joined"].update(sha256="0"*64))]:
            other=copy.deepcopy(original);edit(other)
            temporary(table,encoded(other),lambda:refuses(label,lambda:F.verify_derived(root,R),"byte ranges"))
        jp=root/"joined-terms.stdout"
        temporary(jp,jp.read_bytes()[:-1],lambda:refuses("truncated physical concatenation",lambda:F.verify_derived(root,R),"byte ranges"))
        def semantics(tag,value,label,error):
            replace_stream(tag,value,lambda:refuses(label,lambda:F.verify_derived(root,R),error))
        tr=root/"commands/inspect-IndexTrace/stdout";lines=tr.read_bytes().splitlines(keepends=True)
        semantics("inspect-IndexTrace",b"".join(lines[:-1]),"one missing finite comparison","complete ordered invented rows")
        semantics("inspect-IndexTrace",b"".join(lines[::-1]),"finite comparison order","complete ordered invented rows")
        for n in ("RefuseUnready","RefuseZero","RefuseLast"):
            rf=root/"commands"/("refuse-"+n)/"stdout";rn=S.read(rf);rn["data"]="accidental unrelated diagnostic"
            semantics("refuse-"+n,encoded(rn),"wrong negative diagnostic "+n,"unexpected compiler error")
        ax=root/"commands/inspect-IndexAxioms/stdout"
        semantics("inspect-IndexAxioms",ax.read_bytes().replace(b"propext",b"sorryAx",1),"independent axiom list rejected recovery placeholder","unexpected transitive axiom")
        room=original["joined"]["bytes"]
        F.fold(root,list(pairs.items()),available=room)
        refuses("one-byte-over remaining evidence",lambda:F.fold(root,list(pairs.items()),available=room-1),"whole bounded native row")
        rec=folder(only)/"result.json";v=S.read(rec);v.update(exit=-9,stop="observed process-group RSS",max_observed_group_rss_bytes=4438499328)
        temporary(rec,encoded(v),lambda:refuses("failing singleton with apparently complete stdout",good,"expected successful operation"))
        temporary(rec,encoded(v),lambda:refuses("failed singleton cannot enter join",lambda:F.fold(root,list(pairs.items())),"incomplete native shard"))
        post=root/"commands"/S.POST/"result.json";v=S.read(post);v["direct_wait4_maxrss_bytes"]=S.SAFE_LIMITS["group_rss_bytes"]+1
        temporary(post,encoded(v),lambda:refuses("separate Python readback exceeded memory",good,"expected successful operation"))
        v=S.read(post);v["retained_before_receipt_bytes"]=(1<<30)+1
        temporary(post,encoded(v),lambda:refuses("separate Python readback exceeded cumulative bytes",good,"expected successful operation"))
        v=S.read(post);v["elapsed_seconds"]=901
        temporary(post,encoded(v),lambda:refuses("separate Python readback exceeded 900 seconds",good,"expected successful operation"))
        v=S.read(root/"terminal.json");v["elapsed_seconds"]=2701
        temporary(root/"terminal.json",encoded(v),lambda:refuses("aggregate deadline exceeded",good,"stock, anchors and campaign deadline"))
        # An ordinary sparse fixture exercises the accepted and refused byte boundaries by logical size.
        # No 1 GiB buffer is filled or hashed. This file remains outside every archive fixture.
        budget=outer/"metadata-budget-fixture";budget.mkdir()
        metadata={"test":"small positive metadata"}; used=len((json.dumps(metadata,indent=2,sort_keys=True)+"\n").encode())
        with (budget/"sparse-test-data").open("wb") as sparse:sparse.truncate((1<<30)-used)
        S.write_counted(budget,budget/"last.json",metadata,transient=False)
        S.require(S.tree_bytes(budget)==1<<30,"last admissible metadata bytes")
        refuses("one additional metadata object after exact byte limit",lambda:S.write_counted(budget,budget/"excess.json",{},transient=False),"cumulative evidence metadata")
        refuses("replacement temporary counts alongside old bytes",lambda:S.write_counted(budget,budget/"last.json",metadata),"cumulative evidence metadata")
        # Package literal artificial files and reopen them through the unchanged ZIP extractor.
        archive=outer/"MODEL-PARSER-ONLY.zip"
        with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for member in sorted(temp.rglob("*")):
                if member.is_file():z.write(member,member.relative_to(temp))
        old_reader=S.load(R/S.V1.PACKAGE/"verify.py")
        target=outer/"reopened-model-only";target.mkdir();
        with zipfile.ZipFile(archive) as model_zip:V.C.copy_registered(model_zip,target)
        S.require(V.complete(target/"result",R,launch,reg,src)==positive,"complete modeled ZIP reopened and independently recomputed")
        branch=S.REF_PREFIX+launch["registration_commit"]+"-"+launch["registration_sha256"]
        hr={"id":launch["run"],"workflow_id":212,"event":"push","head_branch":branch,"head_sha":launch["commit"],"run_attempt":1,"status":"completed","conclusion":"success","path":S.WORKFLOW,"repository":{"full_name":"sepahead/pid-rs","id":237},"head_repository":{"full_name":"sepahead/pid-rs","id":237}}
        hj={"id":338,"run_id":hr["id"],"head_sha":hr["head_sha"],"head_branch":branch,"run_attempt":1,"status":"completed","conclusion":"success","name":S.JOB}
        ha={"id":423,"expired":False,"workflow_run":{"id":hr["id"],"head_sha":hr["head_sha"],"head_branch":branch,"repository_id":237,"head_repository_id":237},"name":f"{S.ARTIFACT_PREFIX}-{hr['head_sha']}-{hr['id']}-1","digest":"sha256:"+S.digest(archive),"size_in_bytes":archive.stat().st_size}
        hh={"total_count":1,"workflow_runs":[hr]}
        S.require(V.remote(hr,hj,ha,hh,archive,launch,"success")["job"]==338,"consistent artificial hosted model")
        refuses("reserved history has a second run",lambda:V.remote(hr,hj,ha,dict(hh,total_count=2),archive,launch,"success"),"sole available")
        refuses("wrong hosted archive fingerprint",lambda:V.remote(hr,hj,dict(ha,digest="sha256:"+"f"*64),hh,archive,launch,"success"),"exact terminal")
        refuses("wrong registered branch",lambda:V.remote(hr,dict(hj,head_branch="other"),ha,hh,archive,launch,"success"),"exact terminal")
        refuses("completed failure used as success",lambda:V.remote(hr,dict(hj,conclusion="failure"),ha,hh,archive,launch,"success"),"exact terminal")
        refuses("retry of the hosted job",lambda:V.remote(hr,dict(hj,run_attempt=2),ha,hh,archive,launch,"success"),"exact terminal")
        refuses("unrelated workflow",lambda:V.remote(dict(hr,path="different workflow"),hj,ha,hh,archive,launch,"success"),"exact terminal")
        # Source drift and missing ordinary replay remain separate from term-framing correctness.
        sourcefile=root/"sources/IndexConsumer.lean"
        temporary(sourcefile,sourcefile.read_bytes()+b"\n",lambda:refuses("changed source of the typed consumer",good,"97 independently derived source bytes"))
        freshrec=root/"commands/fresh-IndexConsumer/result.json";fr=S.read(freshrec);fr["argv"]=[fr["argv"][0],"IndexConsumer"]
        temporary(freshrec,encoded(fr),lambda:refuses("missing fresh replay mode",good,"pinned fresh object"))
        postrec=root/"commands"/S.POST/"result.json";pr=S.read(postrec);pr["post_group_absent"]=False
        temporary(postrec,encoded(pr),lambda:refuses("unclean Python worker group",good,"expected successful operation"))
        # Retain only the deterministic prefix through the failed inline singleton in a separate artificial fixture image.
        failed=outer/"failed"/"result";failed.mkdir(parents=True)
        tag="inspect-"+only
        shutil.copyfile(root.parent/"launch.json",failed.parent/"launch.json")
        shutil.copytree(root/"sources",failed/"sources")
        shutil.copyfile(root/"registration.json",failed/"registration.json")
        (failed/"objects").mkdir()
        cutoff=next(i for i,st in enumerate(S.read(root/"stages.json")) if st["kind"]=="inspect" and st["module"]==only)
        stages=S.read(root/"stages.json")[:cutoff+1];S.write(failed/"stages.json",stages)
        for unit in stages[-1]["preceding"]:shutil.copyfile(root/"objects"/unit,failed/"objects"/unit)
        for name in S.schedule(R):
            d2=failed/"commands"/name;d2.mkdir(parents=True)
            firstroot=root/"commands"/name
            for k in ("result.json","stdout","stderr"):(d2/k).write_bytes((firstroot/k).read_bytes())
            if name==tag:
                v=S.read(d2/"result.json");(d2/"stdout").write_bytes(b"")
                v.update(exit=-9,stop="observed process-group RSS",max_observed_group_rss_bytes=4438499328,direct_wait4_maxrss_bytes=4438499328,stdout_sha256=S.digest_bytes(b""),stdout_bytes=0)
                (d2/"result.json").write_bytes(encoded(v));break
        S.write(failed/"terminal.json",{"status":S.FAILED,"attempt":S.ATTEMPT,"original_evaluations":0,"stage":tag,"phase":"invoke","error":"RuntimeError: unexpected native outcome or diagnostics at "+tag,
              "dispatch_intervals":S.read(root/"terminal.json")["dispatch_intervals"][:list(S.schedule(R)).index(tag)+1],"elapsed_seconds":105.0})
        last_file=failed/"commands"/tag/"result.json"
        measured=S.read(last_file);measured["retained_before_receipt_bytes"]=fixture_storage_before_last(failed,tag)
        last_file.write_bytes(encoded(measured))
        loss=V.failure(failed,R,reg,src)
        S.require(loss["assigned_theorems"]==["IndexExample.inlineComplete"] and loss["observed_command_prefix"][-1]["exit"]==-9 and
                  loss["permitted_original_issues"]==0,"specific modeled failed singleton disposition")
        refuses("failed terminal cannot be accepted",lambda:V.complete(failed,R,launch,reg,src),"completed artificial terminal")
        last_group=failed/"commands"/tag/"result.json";z=S.read(last_group)
        z["residual_after_wait4"]=True;z["post_group_absent"]=False
        def admit_failure_only():
            facts=V.failure(failed,R,reg,src)
            S.require(facts["status"]==S.FAILED and facts["observed_command_prefix"][-1]["residual_after_wait4"] is True,"retain actual cleanup defect in negative evidence")
        temporary(last_group,encoded(z),admit_failure_only)
        bad_source=failed/"sources/IndexConsumer.lean"
        temporary(bad_source,bad_source.read_bytes()+b"\n",lambda:refuses("failed prefix source changed",lambda:V.failure(failed,R,reg,src),"failed prefix source changed"))
        fake_stage=copy.deepcopy(stages);fake_stage[-1]["preceding"].pop("IndexConsumer.olean")
        temporary(failed/"stages.json",encoded(fake_stage),lambda:refuses("failed singleton cites different preceding objects",lambda:V.failure(failed,R,reg,src),"failed prefix prior objects"))
        archive=R/S.PRIOR/"native-evidence.zip";old_reader=S.load(R/S.V1.PACKAGE/"verify.py")
        unzipped=outer/"historic";unzipped.mkdir();old_reader.extract(archive,unzipped)
        refuses("historic real v1 failure remains failed",lambda:old_reader.check_directory(unzipped/"result",R),"terminal native predicate")
        return {"scope":"artificial parser, framing and source qualification only","native_executions":0,"ordinary_fake_shard_processes":87,
                "modeled_whole_record":{"full_theorems":positive["terms"],"required_edges":positive["edges"],
                                         "finite_rows":positive["numerical_rows"],"false_controls":len(positive["refused"])},
                "ordinary_file_count":len(S.all_files(R,src)),"public_provider_and_old_failure_verified":True,"actual_old_native_status":"failed",
                "modeled_singleton_stage":tag,"modeled_failed_singleton_assigned":loss["assigned_theorems"],"denied_interpretations":labels}


if __name__=="__main__":
    print(json.dumps(tests(),sort_keys=True))
